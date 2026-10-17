"""The generic extraction engine: one mapping config + one raw file → observations.

This module knows NOTHING about any specific source. Everything source-specific
(format, columns, transforms, ids, timestamps) comes from the agent-written
config. If source-specific knowledge ever appears in this file, the
"one engine + six configs" claim is broken.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import ontology, readers, validators
from .config import CONFIGS, OUTPUTS, RUNS
from .mapping_config import MappingConfig, load_config
from .transforms import TransformError, apply_transforms

ENGINE_VERSION = "engine-0.1"


def config_version(config_path: Path) -> str:
    """Hash the raw config bytes (never re-serialized YAML — that is unstable)."""
    digest = hashlib.sha256(config_path.read_bytes()).hexdigest()[:12]
    return f"cfg-{digest}+{ENGINE_VERSION}"


def make_record_id(row: dict, cfg: MappingConfig, flags: list) -> str:
    """Build the source_record_id for one row, per the config's strategy."""
    strategy = cfg.record_id.strategy
    if strategy in ("column", "composite"):
        parts = []
        for column in cfg.record_id.columns:
            part = row.get(column, "").strip()
            if part == "":
                flags.append(
                    {"field": "source_record_id", "flag": "record_id_component_empty", "raw": column}
                )
            parts.append(part)  # keep the empty slot — never silently switch strategy
        return "|".join(parts)
    # row_hash: deterministic hash of the whole raw row, in header order
    joined = "\x1f".join(f"{k}={v}" for k, v in row.items())
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def make_observed_at(row: dict, cfg: MappingConfig, flags: list) -> str:
    """The observation timestamp for one row (a real column, or the frozen proxy)."""
    oa = cfg.observed_at
    if oa.strategy == "dataset_modified":
        return oa.value
    raw = row.get(oa.column, "")
    try:
        parsed = apply_transforms(raw, [{"parse_date": oa.format}])
    except TransformError:
        parsed = None
    if parsed is None:
        flags.append({"field": "observed_at", "flag": "observed_at_fallback", "raw": raw})
        return oa.value if oa.value is not None else ""
    return parsed


def check_claim_value(canonical: str, value) -> str | None:
    """Post-transform validity judgement. Returns a flag name, or None if fine."""
    if canonical == "entity.abn":
        if not validators.valid_abn(str(value)):
            return "abn_checksum_failed"
        return None
    if canonical == "entity.acn":
        if not validators.valid_acn(str(value)):
            return "acn_checksum_failed"
        return None
    allowed = ontology.enum_values(canonical)
    if allowed is not None:
        if not validators.valid_enum(str(value), allowed):
            return "enum_value_invalid"
        return None
    if canonical in ontology.date_fields():
        if not validators.valid_date(str(value)):
            return "date_invalid"
        return None
    return None


def extract_rows(rows: list[dict], cfg: MappingConfig, extractor_version: str, ingested_at: str) -> list[dict]:
    """Turn raw rows into canonical observations. Pure: no I/O, fully deterministic."""
    # structural check once, not per row: every referenced column must exist
    if rows:
        header = set(rows[0].keys())
        missing = []
        for entry in cfg.fields:
            if entry.source not in header:
                missing.append(entry.source)
        if missing:
            raise RuntimeError(f"config references missing columns: {missing}")

    observations = []
    id_counts: dict[str, int] = {}
    for row in rows:
        flags: list[dict] = []
        record_id = make_record_id(row, cfg, flags)

        # duplicate ids get a deterministic suffix; rows are never dropped
        seen = id_counts.get(record_id, 0) + 1
        id_counts[record_id] = seen
        if seen > 1:
            flags.append({"field": "source_record_id", "flag": "duplicate_record_id", "raw": record_id})
            record_id = f"{record_id}#{seen}"

        observed_at = make_observed_at(row, cfg, flags)

        claims = []
        for entry in cfg.fields:
            raw = row.get(entry.source, "")
            try:
                value = apply_transforms(raw, entry.transforms)
            except TransformError as err:
                flags.append({"field": entry.canonical, "flag": str(err), "raw": raw})
                continue
            if value is None:
                continue  # absence: no claim, no flag

            if entry.transforms:
                level = "L1"  # computed deterministically from what the source said
            else:
                level = "L0"  # the source said it directly

            # multi-valued fields (e.g. split trading names) emit one claim each
            if isinstance(value, list):
                values = value
            else:
                values = [value]
            for one_value in values:
                problem = check_claim_value(entry.canonical, one_value)
                if problem is not None:
                    flags.append({"field": entry.canonical, "flag": problem, "raw": raw})
                    continue  # an invalid value is never emitted as a claim
                claims.append(
                    {
                        "field": entry.canonical,
                        "value": one_value,
                        "raw": raw,  # always the full original cell
                        "field_confidence": entry.confidence,
                        "derivation_level": level,
                    }
                )

        observations.append(
            {
                "source_id": cfg.source_id,
                "source_record_id": record_id,
                "observed_at": observed_at,
                "observed_at_basis": cfg.observed_at.basis,
                "ingested_at": ingested_at,
                "licence": cfg.licence,
                "extractor_version": extractor_version,
                "claims": claims,
                "quality_flags": flags,
            }
        )
    return observations


def collect_seed_abns(exclude_source: str) -> set[str]:
    """All ABN values already observed from OTHER sources (for seeded sampling)."""
    seeds: set[str] = set()
    obs_dir = OUTPUTS / "observations"
    if not obs_dir.exists():
        return seeds
    for path in obs_dir.glob("*.jsonl"):
        if path.stem == exclude_source:
            continue
        for line in path.read_text().splitlines():
            obs = json.loads(line)
            for claim in obs["claims"]:
                if claim["field"] == "entity.abn":
                    seeds.add(claim["value"])
    return seeds


def collect_seed_names(exclude_source: str) -> set[str]:
    """Normalised names from sources that have NO ABN claims at all.

    A source without identifiers (the discount directory) can only ever be
    linked by name, so its names — and only its — also seed the big-file scan.
    Sources that carry ABNs don't need name seeding and would flood the sample.
    """
    from .names import name_key

    seeds: set[str] = set()
    obs_dir = OUTPUTS / "observations"
    if not obs_dir.exists():
        return seeds
    for path in obs_dir.glob("*.jsonl"):
        if path.stem == exclude_source:
            continue
        names: set[str] = set()
        has_abn = False
        for line in path.read_text().splitlines():
            obs = json.loads(line)
            for claim in obs["claims"]:
                if claim["field"] == "entity.abn":
                    has_abn = True
                elif claim["field"] in ("entity.legal_name", "entity.trading_name"):
                    key = name_key(str(claim["value"]))
                    if len(key) >= 6:  # too-short keys match everything
                        names.add(key)
        if not has_abn:
            seeds.update(names)
    return seeds


def seeded_rows(
    data_path: Path, cfg: MappingConfig, limit: int,
    abn_seeds: set[str], name_seeds: set[str],
) -> list[dict]:
    """Sample a big file so cross-source overlap actually lands in the sample.

    Random 1000-row samples of a 3.4M-row file would share ~0 businesses with
    the other sources (measured during source selection), so: keep the first
    limit/2 rows as an unbiased fill, then scan the whole file keeping rows
    whose ABN appears in another source — or whose name matches a source that
    has no ABNs to match on — until the sample is full. The bias is deliberate
    and documented: precision is measured either way; coverage is never claimed.
    """
    from .names import name_key

    abn_entries = []
    name_columns = []
    for entry in cfg.fields:
        if entry.canonical == "entity.abn":
            abn_entries.append(entry)
        if entry.canonical in ("entity.legal_name", "entity.trading_name"):
            name_columns.append(entry.source)

    fill_target = limit // 2
    sample: list[dict] = []
    abn_matches = 0
    name_matches = 0
    for row in readers.iter_rows(data_path, cfg.reader.model_dump()):
        if len(sample) < fill_target:
            sample.append(row)
            continue

        matched = False
        for entry in abn_entries:
            # normalise with the exact transforms the config declares for this
            # column (e.g. strip_float_suffix for "34291651910.0") — the
            # sampler must not invent its own cleaning rules
            try:
                value = apply_transforms(row.get(entry.source, ""), entry.transforms)
            except TransformError:
                continue
            if value is not None and str(value) in abn_seeds:
                matched = True
                abn_matches += 1
                break
        if not matched:
            for column in name_columns:
                if name_key(row.get(column, "")) in name_seeds:
                    matched = True
                    name_matches += 1
                    break

        if matched:
            sample.append(row)
            if len(sample) >= limit:
                break
    print(
        f"seeded sampling: {fill_target} head rows + {abn_matches} ABN matches "
        f"+ {name_matches} name matches (name seeds from no-ABN sources only)"
    )
    return sample


def run_extract(source_id: str, limit: int = 1000, seeded: bool = False) -> Path:
    """CLI entry: load config, read the source, write observations + a run log."""
    config_path = CONFIGS / f"{source_id}.yaml"
    cfg = load_config(config_path)
    version = config_version(config_path)

    raw_path = readers.download(cfg.resource_url, cfg.source_id)
    data_path = readers.unzip_if_needed(raw_path)
    if seeded:
        rows = seeded_rows(
            data_path, cfg, limit,
            collect_seed_abns(source_id), collect_seed_names(source_id),
        )
    else:
        rows = readers.read_rows(data_path, cfg.reader.model_dump(), limit)

    # one timestamp for the whole run keeps the output deterministic
    ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    observations = extract_rows(rows, cfg, version, ingested_at)

    out_dir = OUTPUTS / "observations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{source_id}.jsonl"
    with out_path.open("w") as fh:
        for obs in observations:
            fh.write(json.dumps(obs, sort_keys=True, ensure_ascii=True) + "\n")

    # run log: the numbers Part 5 needs, plus enough to debug any record
    claim_counts: dict[str, int] = {}
    flag_counts: dict[str, int] = {}
    for obs in observations:
        for claim in obs["claims"]:
            claim_counts[claim["field"]] = claim_counts.get(claim["field"], 0) + 1
        for flag in obs["quality_flags"]:
            flag_counts[flag["flag"]] = flag_counts.get(flag["flag"], 0) + 1
    log = {
        "source_id": source_id,
        "config_path": str(config_path),
        "extractor_version": version,
        "input_path": str(data_path),
        "input_bytes": data_path.stat().st_size,
        "row_limit": limit,
        "seeded_sampling": seeded,
        "rows_read": len(rows),
        "observations_written": len(observations),
        "claim_counts": claim_counts,
        "flag_counts": flag_counts,
        "output_path": str(out_path),
        "ingested_at": ingested_at,
        "api_cost_usd": 0.0,  # the engine never calls a model
    }
    run_dir = RUNS / source_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "extract_log.json").write_text(json.dumps(log, indent=2))

    print(f"{source_id}: {len(observations)} observations → {out_path}")
    return out_path
