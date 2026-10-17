"""Part 4 — company profiles: one record per linked entity, conflicts shown.

Winner per field: higher source reliability (per-field overrides considered)
→ newer observed_at (marked weak when either timestamp is a catalogue proxy)
→ majority. Losing values are kept and shown. trading_name is multi-valued by
the ontology, so it collects all distinct values instead of picking a winner.
Field confidence = field_confidence × source_reliability, both shown — a
heuristic quality score, not a calibrated probability, and conditional on the
cluster being linked correctly (hence cluster_support on every profile).
"""

import json
import random
from pathlib import Path

import yaml

from .config import CONFIGS, OUTPUTS

PROFILE_COUNT = 50
SAMPLE_SEED = 7

SINGLE_VALUED = [
    "entity.legal_name", "entity.abn", "entity.acn", "entity.nzbn",
    "entity.entity_type", "entity.status", "entity.website",
    "entity.industry_code", "entity.date_registered",
    "address.full", "address.locality", "address.state",
    "address.postcode", "address.country",
]
MULTI_VALUED = ["entity.trading_name"]


def load_reliabilities() -> dict[str, dict]:
    """source_id → {'base': float, 'overrides': {field: float}} from the configs."""
    table: dict[str, dict] = {}
    for path in CONFIGS.glob("*.yaml"):
        cfg = yaml.safe_load(path.read_text())
        table[cfg["source_id"]] = {
            "base": cfg["source_reliability"]["value"],
            "overrides": cfg.get("reliability_overrides", {}) or {},
        }
    return table


def reliability_for(source: str, field: str, table: dict[str, dict]) -> float:
    entry = table.get(source)
    if entry is None:
        return 0.5  # unknown source: trust it less than any configured one
    return entry["overrides"].get(field, entry["base"])


def load_claims_by_record(suffix: str = "") -> dict[str, dict]:
    """record key → {'claims': [...], 'observed_at': ..., 'basis': ...}."""
    records: dict[str, dict] = {}
    for path in sorted((OUTPUTS / "observations").glob("*.jsonl")):
        for line in path.read_text().splitlines():
            obs = json.loads(line)
            key = f"{obs['source_id']}::{obs['source_record_id']}"
            records[key] = {
                "source": obs["source_id"],
                "observed_at": obs["observed_at"],
                "basis": obs.get("observed_at_basis", "proxy"),
                "claims": obs["claims"],
            }
    return records


def gather_candidates(members: list[str], records: dict, field: str, reliab: dict) -> list[dict]:
    """Every claim for one canonical field across the cluster's records."""
    candidates = []
    for key in members:
        rec = records.get(key)
        if rec is None:
            continue
        for claim in rec["claims"]:
            if claim["field"] == field:
                source = rec["source"]
                candidates.append(
                    {
                        "value": claim["value"],
                        "provenance": key,
                        "source": source,
                        "observed_at": rec["observed_at"],
                        "observed_at_basis": rec["basis"],
                        "field_confidence": claim["field_confidence"],
                        "source_reliability": reliability_for(source, field, reliab),
                    }
                )
    return candidates


def value_key(value) -> str:
    """Case/whitespace-insensitive grouping key: 'NEUMANN STEEL PTY LTD' and its
    lower-case twin are the same value, not a conflict."""
    return " ".join(str(value).split()).casefold()


def pick_winner(candidates: list[dict]) -> tuple[dict, list[dict], str]:
    """Returns (winner, distinct losing values with why, the deciding rule)."""
    # rows and sources behind each distinct (normalised) value
    rows_per_value: dict[str, int] = {}
    sources_per_value: dict[str, set] = {}
    for c in candidates:
        key = value_key(c["value"])
        rows_per_value[key] = rows_per_value.get(key, 0) + 1
        sources_per_value.setdefault(key, set()).add(c["source"])

    if len(rows_per_value) == 1:
        winner = dict(candidates[0])
        winner["support"] = len(candidates)
        return winner, [], "no conflict"

    # 1) reliability
    best_rel = max(c["source_reliability"] for c in candidates)
    top = [c for c in candidates if c["source_reliability"] == best_rel]
    decided_by = "reliability"
    if len({value_key(c["value"]) for c in top}) > 1:
        # 2) recency (weak when any contender's timestamp is a catalogue proxy)
        newest = max(c["observed_at"] for c in top)
        weak = any(c["observed_at_basis"] == "proxy" for c in top)
        top = [c for c in top if c["observed_at"] == newest]
        decided_by = "recency (weak: catalogue dates)" if weak else "recency"
        if len({value_key(c["value"]) for c in top}) > 1:
            # 3) majority: count DISTINCT SOURCES per value first (ten rows from
            # one source are one voice), rows only break source ties
            top.sort(key=lambda c: (
                -len(sources_per_value[value_key(c["value"])]),
                -rows_per_value[value_key(c["value"])],
                c["provenance"],
            ))
            decided_by = "majority of sources"

    winner = dict(top[0])
    winner_key = value_key(winner["value"])
    winner["support"] = rows_per_value[winner_key]

    losers = []
    seen: set[str] = set()
    for c in candidates:
        key = value_key(c["value"])
        if key != winner_key and key not in seen:
            seen.add(key)
            losers.append(
                {
                    "value": c["value"], "source": c["source"], "provenance": c["provenance"],
                    "support": rows_per_value[key],
                    "sources": sorted(sources_per_value[key]),
                    "why_lost": f"lost on {decided_by}",
                }
            )
    return winner, losers, decided_by


def build_profile(cluster: dict, records: dict, reliab: dict) -> dict:
    members = cluster["members"]
    fields: dict[str, dict] = {}

    for field in SINGLE_VALUED:
        candidates = gather_candidates(members, records, field, reliab)
        if not candidates:
            continue  # absent fields are absent keys, never blanks
        winner, losers, note = pick_winner(candidates)
        entry = {
            "value": winner["value"],
            "support": winner["support"],
            "confidence": {
                "field_confidence": winner["field_confidence"],
                "source_reliability": winner["source_reliability"],
                "combined": round(winner["field_confidence"] * winner["source_reliability"], 3),
            },
            "provenance": winner["provenance"],
        }
        if losers:
            entry["decided_by"] = note
            entry["conflicts"] = losers
        fields[field] = entry

    for field in MULTI_VALUED:
        candidates = gather_candidates(members, records, field, reliab)
        if not candidates:
            continue
        seen: dict[str, dict] = {}
        for c in sorted(candidates, key=lambda c: (-c["source_reliability"], c["provenance"])):
            if c["value"] not in seen:
                seen[c["value"]] = {
                    "value": c["value"],
                    "provenance": c["provenance"],
                    "confidence": {
                        "field_confidence": c["field_confidence"],
                        "source_reliability": c["source_reliability"],
                        "combined": round(c["field_confidence"] * c["source_reliability"], 3),
                    },
                }
        fields[field] = {"values": list(seen.values()), "note": "multi-valued by ontology"}

    return {
        "entity_id": cluster["entity_id"],
        "sources": cluster["sources"],
        "member_records": members,
        "cluster_support": cluster["cluster_support"],
        "fields": fields,
    }


def pick_entities(clusters: list[dict]) -> list[dict]:
    multi = [c for c in clusters if len(c["sources"]) > 1]
    if len(multi) <= PROFILE_COUNT:
        return multi
    return random.Random(SAMPLE_SEED).sample(multi, PROFILE_COUNT)  # no cherry-picking


def run_profile(drop_source: str | None = None) -> None:
    records = load_claims_by_record()
    reliab = load_reliabilities()
    clusters = json.loads((OUTPUTS / "clusters.json").read_text())["clusters"]
    chosen = pick_entities(clusters)
    profiles = [build_profile(c, records, reliab) for c in chosen]

    out = OUTPUTS / "profiles.jsonl"
    with out.open("w") as fh:
        for profile in profiles:
            fh.write(json.dumps(profile, sort_keys=True) + "\n")
    print(f"{len(profiles)} profiles → {out}")

    if drop_source is not None:
        # the fragility experiment: re-resolve without one source, rebuild the
        # SAME 50 entities, and report both field-level and cluster-level damage
        from .resolve import run_resolve

        run_resolve(drop_source=drop_source)
        dropped_clusters = json.loads(
            (OUTPUTS / f"clusters.without-{drop_source}.json").read_text()
        )["clusters"]
        by_members: dict[frozenset, dict] = {}
        for c in dropped_clusters:
            by_members[frozenset(c["members"])] = c

        survived, split_or_gone, fields_changed = 0, 0, 0
        for profile in profiles:
            original = frozenset(m for m in profile["member_records"]
                                 if not m.startswith(f"{drop_source}::"))
            match = None
            for members, cluster in by_members.items():
                if original and original.issubset(members):
                    match = cluster
                    break
            if match is None or len(original) < 2:
                split_or_gone += 1
                continue
            survived += 1
            rebuilt = build_profile(match, records, reliab)
            if rebuilt["fields"] != profile["fields"]:
                fields_changed += 1

        report = {
            "dropped_source": drop_source,
            "profiles_total": len(profiles),
            "entities_split_or_gone": split_or_gone,
            "entities_survived": survived,
            "profiles_with_field_changes": fields_changed,
        }
        (OUTPUTS / f"drop-source-{drop_source}.json").write_text(json.dumps(report, indent=2))
        print(f"drop-source report: {report}")
