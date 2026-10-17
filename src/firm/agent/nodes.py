"""The agent's graph nodes. Each function takes the state dict, does one job,
and returns the keys it updates. Models propose; code checks; a human approves.

State keys:
  dataset_id, meta, data_path, reader, rows, visible, loop, accept, profiles,
  config, decisions, revisions, validation, spotcheck, suspicious, status,
  human_comment, changes, steps
"""

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from .. import ontology, readers
from ..ckan import package_show
from ..config import CONFIGS, RUNS
from ..engine import check_claim_value, extract_rows
from ..llm import complete
from ..mapping_config import MappingConfig, check_config
from ..transforms import TransformError, apply_transforms
from . import prompts

MAX_REVISIONS = 3
TOTAL_ROWS = 700  # 200 visible to the model, 350 validate loop, 150 acceptance
FIXED_TS = "1970-01-01T00:00:00+00:00"  # validation runs use a fixed timestamp
RESOURCE_PREFERENCE = ["CSV", "TSV", "XLSX", "ZIP"]

NAME_OR_ID_FIELDS = {
    "entity.legal_name", "entity.trading_name",
    "entity.abn", "entity.acn", "entity.nzbn",
}


# ---------------------------------------------------------------- helpers ----

def parse_model_json(text: str) -> dict:
    """Parse the model's reply as JSON, tolerating markdown fences around it."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        cleaned = cleaned[first_newline + 1:]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    return json.loads(cleaned)


def ask_json(step: str, system: str, user: str, source: str) -> dict:
    """One model call that must return JSON; one corrective retry if it does not."""
    reply = complete(step, system, user, source=source)
    try:
        return parse_model_json(reply)
    except json.JSONDecodeError as err:
        retry_user = (
            user
            + f"\n\nYOUR PREVIOUS REPLY WAS NOT VALID JSON ({err}). "
            + "Reply again with only the JSON object."
        )
        reply = complete(step + "-jsonfix", system, retry_user, source=source)
        return parse_model_json(reply)


def ontology_text() -> str:
    lines = []
    for name, spec in ontology.canonical_fields().items():
        parts = [spec.get("type", "string")]
        if spec.get("values"):
            parts.append("values: " + ", ".join(spec["values"]))
        if spec.get("pattern"):
            parts.append("pattern: " + spec["pattern"])
        note = str(spec.get("notes", "")).strip().replace("\n", " ")
        lines.append(f"- {name} ({'; '.join(parts)}): {note}")
    return "\n".join(lines)


def truncate_cells(row: dict, width: int = 80) -> dict:
    out = {}
    for key, value in row.items():
        out[key] = value[:width]
    return out


def column_hints(values: list[str]) -> list[str]:
    """Cheap regex-ish hints computed from non-empty sample values."""
    hints = []
    digits = [v for v in values if v.replace(" ", "").replace(".0", "").isdigit()]
    if digits and len(digits) >= len(values) * 0.8:
        lengths = {len(v.replace(" ", "").replace(".0", "")) for v in digits}
        if lengths == {11}:
            hints.append("all 11-digit (ABN-like)")
        elif lengths == {9}:
            hints.append("all 9-digit (ACN-like)")
        elif lengths == {4}:
            hints.append("all 4-digit (postcode-like)")
        else:
            hints.append("numeric")
    slash_dates = [v for v in values if len(v) == 10 and v[2] == "/" and v[5] == "/"]
    if slash_dates and len(slash_dates) >= len(values) * 0.8:
        hints.append("dd/mm/yyyy-like dates")
    if all(v.strip().lower() in ("y", "n", "") for v in values) and values:
        hints.append("Y/N flag")
    if sum(1 for v in values if "www." in v.lower() or "http" in v.lower()) >= len(values) * 0.5 and values:
        hints.append("URL-like")
    return hints


def build_profiles(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    profiles = []
    for column in rows[0].keys():
        values = [row.get(column, "") for row in rows]
        non_empty = [v for v in values if v.strip() != ""]
        samples = []
        for v in non_empty:
            if v not in samples:
                samples.append(v)
            if len(samples) >= 10:
                break
        profiles.append(
            {
                "column": column,
                "null_rate": round(1 - len(non_empty) / len(values), 3),
                "distinct": len(set(non_empty)),
                "samples": [s[:60] for s in samples],
                "hints": column_hints(non_empty[:100]),
            }
        )
    return profiles


def accounting_problems(cfg_dict: dict, columns: list[str]) -> list[str]:
    """Every source column must land in fields[] or unmapped[] exactly once.
    Exception: a column mapped twice where both entries are conditional (the
    mixed ABN/ACN pattern)."""
    problems = []
    field_sources = [f["source"] for f in cfg_dict.get("fields", [])]
    unmapped_sources = [u["source"] for u in cfg_dict.get("unmapped", [])]
    for column in columns:
        in_fields = field_sources.count(column)
        in_unmapped = unmapped_sources.count(column)
        total = in_fields + in_unmapped
        if total == 0:
            problems.append(f"column not accounted for: {column}")
        elif total > 1:
            entries = [f for f in cfg_dict.get("fields", []) if f["source"] == column]
            two_conditional = (
                in_unmapped == 0
                and in_fields == 2
                and all(e.get("conditional") for e in entries)
            )
            if not two_conditional:
                problems.append(f"column accounted for {total} times: {column}")
    for source in field_sources + unmapped_sources:
        if source not in columns:
            problems.append(f"config references a column the file does not have: {source}")
    return problems


def structural_problems(cfg_dict: dict, columns: list[str]) -> list[str]:
    """Pydantic shape + cross-checks + column accounting, as a list of strings."""
    try:
        cfg = MappingConfig(**cfg_dict)
    except Exception as err:
        return [f"config shape invalid: {err}"]
    problems = check_config(cfg)
    problems.extend(accounting_problems(cfg_dict, columns))
    return problems


def assemble_config(proposal: dict, state: dict) -> dict:
    """Merge the model's proposal with the parts other nodes own."""
    meta = state["meta"]
    cfg = dict(proposal)  # shallow copy; we add the non-model keys
    cfg["source_id"] = state["dataset_id"]
    cfg["dataset_id"] = state["dataset_id"]
    cfg["resource_url"] = meta["resource_url"]
    cfg["licence"] = meta["licence"]
    cfg["reader"] = state["reader"]
    observed = cfg.get("observed_at", {})
    if observed.get("strategy") == "dataset_modified":
        observed["value"] = meta["modified"]  # freeze the proxy date now
    return cfg


# ------------------------------------------------------------------ nodes ----

def fetch_meta(state: dict) -> dict:
    dataset_id = state["dataset_id"]
    pkg = package_show(dataset_id)

    chosen = None
    hint = state.get("resource_hint")
    if hint:
        # The human names WHICH file of a multi-resource dataset to onboard
        # (choosing the file is a human call, like choosing the dataset;
        # mapping it is the agent's job).
        for res in pkg.get("resources", []):
            text = f"{res.get('name', '')} {res.get('url', '')}".lower()
            if hint.lower() in text:
                chosen = res
                break
        if chosen is None:
            names = [r.get("name") or r.get("url", "")[-40:] for r in pkg.get("resources", [])]
            raise RuntimeError(f"{dataset_id}: no resource matches {hint!r}; resources: {names}")
    else:
        for wanted in RESOURCE_PREFERENCE:
            for res in pkg.get("resources", []):
                fmt = (res.get("format") or "").upper().replace("EXCEL (.XLSX)", "XLSX")
                if fmt == wanted:
                    chosen = res
                    break
            if chosen is not None:
                break
    if chosen is None:
        raise RuntimeError(f"{dataset_id}: no CSV/TSV/XLSX/ZIP resource to onboard")

    org_info = pkg.get("organization")
    if org_info is None:
        org_info = {}
    meta = {
        "publisher": org_info.get("title", ""),
        "licence": pkg.get("license_id") or "unknown",
        "modified": (pkg.get("metadata_modified") or "")[:10],
        "title": pkg.get("title", ""),
        "notes": (pkg.get("notes") or "")[:800],
        "resource_url": chosen["url"],
        "format_label": chosen.get("format", ""),
    }
    raw_path = readers.download(meta["resource_url"], dataset_id)
    data_path = readers.unzip_if_needed(raw_path)
    return {"meta": meta, "data_path": str(data_path), "steps": state.get("steps", []) + ["fetch_meta"]}


def inspect(state: dict) -> dict:
    path = Path(state["data_path"])
    if path.suffix.lower() == ".xlsx":
        sheets = readers.head_xlsx(path, n_rows=15)
        parts = []
        for name, rows in sheets.items():
            parts.append(f"SHEET {name!r}:")
            for row in rows:
                parts.append("  " + json.dumps([c[:40] for c in row[:25]]))
        raw_sample = "\n".join(parts)
    else:
        raw_sample = readers.head_text(path, n_lines=50).replace("\t", "\\t")

    user = prompts.fill(
        prompts.INSPECT_USER,
        dataset_id=state["dataset_id"],
        ckan_format_label=state["meta"]["format_label"],
        raw_sample=raw_sample,
        retry_block="",
    )
    decision = ask_json("inspect", prompts.INSPECT_SYSTEM, user, state["dataset_id"])

    def to_reader_cfg(d: dict) -> dict:
        return {
            "format": d["format"],
            "delimiter": d.get("delimiter"),
            "encoding": d.get("encoding", "utf-8-sig"),
            "header_row": int(d.get("header_row", 0)),
            "sheet": d.get("sheet"),
        }

    reader_cfg = to_reader_cfg(decision)
    try:
        rows = readers.read_rows(path, reader_cfg, limit=TOTAL_ROWS)
    except Exception as err:  # one retry: the model sees its own failure
        retry = prompts.fill(
            prompts.INSPECT_RETRY_BLOCK,
            previous_json=json.dumps(decision),
            parse_error=str(err),
        )
        user = prompts.fill(
            prompts.INSPECT_USER,
            dataset_id=state["dataset_id"],
            ckan_format_label=state["meta"]["format_label"],
            raw_sample=raw_sample,
            retry_block=retry,
        )
        decision = ask_json("inspect-retry", prompts.INSPECT_SYSTEM, user, state["dataset_id"])
        reader_cfg = to_reader_cfg(decision)
        rows = readers.read_rows(path, reader_cfg, limit=TOTAL_ROWS)

    if not rows:
        raise RuntimeError("inspect produced a reader config that yields zero rows")
    return {
        "reader": reader_cfg,
        "inspect_reasoning": decision.get("reasoning", ""),
        "rows": rows,
        "steps": state["steps"] + ["inspect"],
    }


def profile(state: dict) -> dict:
    rows = list(state["rows"])
    random.Random(42).shuffle(rows)  # file order is often sorted; shuffle first
    n = len(rows)
    if n >= TOTAL_ROWS:
        n_visible, n_loop = 200, 350
    else:  # small source: keep the same 30/50/20 proportions
        n_visible = max(1, int(n * 0.3))
        n_loop = max(1, int(n * 0.5))
    visible = rows[:n_visible]
    loop = rows[n_visible:n_visible + n_loop]
    accept = rows[n_visible + n_loop:]
    # profiles are computed from the visible slice only: the model must never
    # learn anything about the rows it will be validated on
    return {
        "visible": visible,
        "loop": loop,
        "accept": accept,
        "profiles": build_profiles(visible),
        "steps": state["steps"] + ["profile"],
    }


def propose(state: dict) -> dict:
    meta = state["meta"]
    base_user = prompts.fill(
        prompts.PROPOSE_USER,
        source_id=state["dataset_id"],
        dataset_id=state["dataset_id"],
        publisher=meta["publisher"],
        licence=meta["licence"],
        dataset_modified=meta["modified"],
        title_and_notes=f"{meta['title']} — {meta['notes']}",
        ontology_fields=ontology_text(),
        n_columns=len(state["profiles"]),
        n_rows=len(state["visible"]),
        column_profiles=json.dumps(state["profiles"], indent=1),
        sample_rows="\n".join(json.dumps(truncate_cells(r)) for r in state["visible"][:20]),
        problem_block="",
    )
    proposal = ask_json("propose", prompts.PROPOSE_SYSTEM, base_user, state["dataset_id"])
    decisions = proposal.pop("decisions", {})
    cfg_dict = assemble_config(proposal, state)

    columns = list(state["rows"][0].keys())
    problems = structural_problems(cfg_dict, columns)
    if problems:  # one corrective round-trip with the exact problem list
        problem_block = prompts.fill(
            prompts.PROPOSE_PROBLEM_BLOCK,
            problems="\n".join(f"- {p}" for p in problems),
            previous_json=json.dumps(proposal),
        )
        user = base_user.replace("Respond with the JSON object only.", "") + problem_block
        proposal = ask_json("propose-fix", prompts.PROPOSE_SYSTEM, user, state["dataset_id"])
        decisions = proposal.pop("decisions", decisions)
        cfg_dict = assemble_config(proposal, state)
        problems = structural_problems(cfg_dict, columns)
        if problems:
            raise RuntimeError(f"propose could not produce a structurally valid config: {problems}")

    return {
        "config": cfg_dict,
        "decisions": decisions,
        "revisions": 0,
        "steps": state["steps"] + ["propose"],
    }


def build_validation_report(
    obs: list[dict], rows: list[dict], cfg: MappingConfig,
    duplicate_ids: int, id_check_rows: int | None = None,
) -> dict:
    n = len(rows)
    if id_check_rows is None:
        id_check_rows = n  # duplicates may be counted over a larger row set
    # which rows produced a claim for each canonical field
    rows_with_claim: dict[str, int] = {}
    flags_per_field: dict[str, int] = {}
    failing_examples: list[dict] = []
    for one in obs:
        fields_present = set()
        for claim in one["claims"]:
            fields_present.add(claim["field"])
        for field in fields_present:
            rows_with_claim[field] = rows_with_claim.get(field, 0) + 1
        for flag in one["quality_flags"]:
            if flag["field"] in ("source_record_id", "observed_at"):
                continue
            flags_per_field[flag["field"]] = flags_per_field.get(flag["field"], 0) + 1
            if len(failing_examples) < 8:
                failing_examples.append(flag)

    checks = []

    def rate_check(canonical: str, label: str, threshold: float) -> None:
        ok = rows_with_claim.get(canonical, 0)
        bad = flags_per_field.get(canonical, 0)
        if ok + bad == 0:
            return  # field not mapped or never attempted: nothing to measure
        rate = ok / (ok + bad)
        checks.append(
            {"check": f"{label} ({canonical})", "threshold": f">= {threshold:.0%}",
             "result": f"{rate:.1%} ({ok} ok / {bad} failed)", "pass": rate >= threshold}
        )

    mapped = {f.canonical for f in cfg.fields}
    for canonical in ("entity.abn", "entity.acn", "entity.nzbn"):
        if canonical in mapped:
            rate_check(canonical, "identifier checksum", 0.95)
    for canonical in mapped:
        if ontology.enum_values(canonical) is not None:
            rate_check(canonical, "enum legality", 0.98)
        if canonical in ontology.date_fields():
            rate_check(canonical, "date parse", 0.95)

    # null drift: a mapping must not lose real values. Measured PER ENTRY (two
    # columns mapping to the same canonical field are judged separately — an
    # aggregate would let one broken column hide behind the other). Conditional
    # entries are judged jointly per source column (the mixed-identifier pattern).
    conditional_columns = set()
    for entry in cfg.fields:
        if entry.conditional:
            conditional_columns.add(entry.source)
        else:
            source_null = sum(1 for r in rows if r.get(entry.source, "").strip() == "") / n
            produced = 0
            for r in rows:
                try:
                    value = apply_transforms(r.get(entry.source, ""), entry.transforms)
                except TransformError:
                    continue
                if value is None:
                    continue
                one_value = value[0] if isinstance(value, list) else value
                if check_claim_value(entry.canonical, one_value) is None:
                    produced += 1
            drift = (1 - produced / n) - source_null
            checks.append(
                {"check": f"null drift ({entry.canonical} ← {entry.source})",
                 "threshold": "<= +2pp", "result": f"{drift:+.1%}", "pass": drift <= 0.02}
            )
    for column in conditional_columns:
        pair_fields = [f.canonical for f in cfg.fields if f.source == column]
        non_null = 0
        rows_with_any = 0
        abstained = []  # non-null values neither gate accepted: shown, not hidden
        for one, row in zip(obs, rows):
            raw = row.get(column, "").strip()
            if raw == "":
                continue
            non_null += 1
            present = {c["field"] for c in one["claims"]}
            if present.intersection(pair_fields):
                rows_with_any += 1
            elif len(abstained) < 5:
                abstained.append(raw)
        if non_null > 0:
            # 95%, not higher: real sources carry junk identifiers ("0", 7-digit
            # fragments) and abstaining on them is correct, not a mapping fault
            rate = rows_with_any / non_null
            checks.append(
                {"check": f"conditional pair coverage ({column} → {' + '.join(pair_fields)})",
                 "threshold": ">= 95% of non-null", "result": f"{rate:.1%}", "pass": rate >= 0.95}
            )
            for raw in abstained:
                failing_examples.append(
                    {"field": " / ".join(pair_fields), "flag": "identifier_unclassified (no claim emitted)", "raw": raw}
                )

    # A literally duplicated source row duplicates ANY honest record id; the
    # engine suffixes it (#2) and flags it, so a trace survives. The check
    # guards against a bad id choice (many rows per key), not against source
    # dirt — hence a rate, not zero.
    dup_rate = duplicate_ids / id_check_rows if id_check_rows else 0.0
    checks.append(
        {"check": "record_id effectively unique (full sample)", "threshold": "<= 0.5% duplicates",
         "result": f"{duplicate_ids} duplicates in {id_check_rows} rows ({dup_rate:.2%})",
         "pass": dup_rate <= 0.005}
    )
    useful = len(mapped.intersection(NAME_OR_ID_FIELDS)) > 0
    checks.append(
        {"check": "minimum useful (a name or an identifier mapped)",
         "threshold": "required", "result": "yes" if useful else "NO", "pass": useful}
    )

    return {
        "checks": checks,
        "failing_examples": failing_examples,
        "all_pass": all(c["pass"] for c in checks),
        "useful": useful,
    }


def validate(state: dict) -> dict:
    cfg = MappingConfig(**state["config"])
    loop_rows = state["loop"]
    try:
        obs_loop = extract_rows(loop_rows, cfg, "cfg-proposal", FIXED_TS)
        obs_all = extract_rows(state["visible"] + loop_rows, cfg, "cfg-proposal", FIXED_TS)
    except RuntimeError as err:  # e.g. config references missing columns
        report = {
            "checks": [{"check": "engine run", "threshold": "must run",
                        "result": str(err), "pass": False}],
            "failing_examples": [], "all_pass": False, "useful": False,
        }
        return {"validation": report, "spotcheck": {"records": [], "overall_notes": []},
                "suspicious": [], "status": "NOT PASSING",
                "steps": state["steps"] + ["validate"]}

    duplicate_ids = 0
    for one in obs_all:
        for flag in one["quality_flags"]:
            if flag["flag"] == "duplicate_record_id":
                duplicate_ids += 1
    report = build_validation_report(
        obs_loop, loop_rows, cfg, duplicate_ids,
        id_check_rows=len(state["visible"]) + len(loop_rows),
    )

    # semantic spot-check: 10 held-out records, raw vs canonical, meaning only
    picker = random.Random(7)
    indices = picker.sample(range(len(loop_rows)), min(10, len(loop_rows)))
    pair_texts = []
    for i in indices:
        claims = obs_loop[i]["claims"]
        claim_lines = [f"  {c['field']} = {json.dumps(c['value'])} (raw: {json.dumps(c['raw'][:60])})" for c in claims]
        if not claim_lines:
            claim_lines = ["  (no claims produced)"]
        pair_texts.append(
            f"RECORD {obs_loop[i]['source_record_id']}\n"
            f"RAW: {json.dumps(truncate_cells(loop_rows[i]))}\n"
            "CANONICAL:\n" + "\n".join(claim_lines)
        )
    spot_user = prompts.fill(
        prompts.SPOTCHECK_USER,
        fields_json=json.dumps(state["config"]["fields"], indent=1),
        ontology_fields=ontology_text(),
        record_pairs="\n\n".join(pair_texts),
    )
    spotcheck = ask_json("spotcheck", prompts.SPOTCHECK_SYSTEM, spot_user, state["dataset_id"])
    suspicious = []
    for record in spotcheck.get("records", []):
        for finding in record.get("findings", []):
            if finding.get("verdict") == "suspicious":
                suspicious.append({"record": record.get("record"), **finding})

    # Hard checks gate the revise loop; semantic flags go to the human. A flag
    # the catalogue cannot fix (street text inside a locality column) would
    # otherwise send the model in circles for three rounds.
    if not report["useful"]:
        status = "NOT USEFUL"
    elif not report["all_pass"]:
        status = "NOT PASSING"
    elif suspicious:
        status = "PASSING WITH FLAGS"
    else:
        status = "PASSING"
    return {
        "validation": report,
        "spotcheck": spotcheck,
        "suspicious": suspicious,
        "status": status,
        "steps": state["steps"] + ["validate"],
    }


def revise(state: dict) -> dict:
    user = prompts.fill(
        prompts.REVISE_USER,
        revision_number=state["revisions"] + 1,
        previous_config_json=json.dumps(state["config"], indent=1),
        validation_report=json.dumps(state["validation"], indent=1),
        semantic_flags=json.dumps(state["suspicious"], indent=1),
        human_comment=state.get("human_comment", ""),
    )
    answer = ask_json("revise", prompts.REVISE_SYSTEM, user, state["dataset_id"])
    new_cfg = assemble_config(answer["config"], state)  # re-pin the non-model keys

    columns = list(state["rows"][0].keys())
    problems = structural_problems(new_cfg, columns)
    if problems:
        retry_user = user + "\n\nPROBLEMS WITH YOUR PREVIOUS ANSWER (fix these):\n" + "\n".join(
            f"- {p}" for p in problems
        )
        answer = ask_json("revise-fix", prompts.REVISE_SYSTEM, retry_user, state["dataset_id"])
        new_cfg = assemble_config(answer["config"], state)
        problems = structural_problems(new_cfg, columns)
        if problems:
            raise RuntimeError(f"revise could not produce a structurally valid config: {problems}")

    return {
        "config": new_cfg,
        "changes": answer.get("changes", []),
        "revisions": state["revisions"] + 1,
        "human_comment": "",
        "steps": state["steps"] + ["revise"],
    }


# ------------------------------------------------------------ review + emit --

def render_review(state: dict) -> str:
    cfg = state["config"]
    meta = state["meta"]
    report = state["validation"]

    mapping_rows = []
    for f in cfg["fields"]:
        mapping_rows.append(
            f"| {f['canonical']} | {f['source']} | `{json.dumps(f['transforms'])}` "
            f"| {f['confidence']} | {'yes' if f.get('conditional') else ''} | {f.get('evidence', '')[:220]} |"
        )
    validation_rows = []
    for c in report["checks"]:
        validation_rows.append(
            f"| {c['check']} | {c['threshold']} | {c['result']} | {'✅' if c['pass'] else '❌'} |"
        )
    failing = "\n".join(f"- `{f['field']}`: {f['flag']} (raw: `{f['raw'][:60]}`)" for f in report["failing_examples"])
    if failing == "":
        failing = "none"

    spot_rows, ok_count, sus_count = [], 0, 0
    for record in state["spotcheck"].get("records", []):
        for finding in record.get("findings", []):
            if finding.get("verdict") == "suspicious":
                sus_count += 1
            else:
                ok_count += 1
            spot_rows.append(
                f"| {record.get('record')} | {finding.get('field')} | {finding.get('verdict')} | {finding.get('why', '')[:160]} |"
            )
    notes = "; ".join(state["spotcheck"].get("overall_notes", [])) or "none"

    unmapped_rows = [f"| {u['source']} | {u['reason']} |" for u in cfg.get("unmapped", [])]

    examples = []
    cfg_obj = MappingConfig(**cfg)
    sample_rows = state["loop"][:5]
    sample_obs = extract_rows(sample_rows, cfg_obj, "cfg-proposal", FIXED_TS)
    for i, (row, one) in enumerate(zip(sample_rows, sample_obs), 1):
        raw_lines = [f"{k}: {v[:70]}" for k, v in row.items()]
        canon_lines = [
            f"{c['field']} = {json.dumps(c['value'])}    (raw: {json.dumps(c['raw'][:40])}, field_confidence: {c['field_confidence']})"
            for c in one["claims"]
        ] or ["(no claims)"]
        examples.append(
            f"### Example {i} — source_record_id {one['source_record_id']}\n"
            "RAW\n```\n" + "\n".join(raw_lines) + "\n```\nCANONICAL\n```\n" + "\n".join(canon_lines) + "\n```"
        )

    observed = cfg["observed_at"]
    record_id = cfg["record_id"]
    return prompts.fill(
        prompts.REVIEW_TEMPLATE,
        source_id=cfg["source_id"],
        dataset_id=cfg["dataset_id"],
        dataset_title=meta["title"],
        publisher=meta["publisher"],
        licence=cfg["licence"],
        resource_url=cfg["resource_url"],
        reader_summary=json.dumps(state["reader"]),
        revisions_used=state["revisions"],
        step_count=len(state["steps"]),
        status=state["status"],
        source_reliability_value=cfg["source_reliability"]["value"],
        source_reliability_rationale=cfg["source_reliability"]["rationale"],
        record_id_summary=f"{record_id['strategy']} {record_id.get('columns', [])}",
        record_id_why=state.get("decisions", {}).get("record_id_why", ""),
        observed_at_summary=f"{observed['strategy']} → {observed.get('value') or observed.get('column')}",
        observed_at_basis=observed["basis"],
        observed_at_why=state.get("decisions", {}).get("observed_at_why", ""),
        n_mapped=len(cfg["fields"]),
        n_source_columns=len(state["rows"][0]),
        mapping_rows="\n".join(mapping_rows),
        validation_row_count=len(state["loop"]),
        validation_rows="\n".join(validation_rows),
        failing_examples=failing,
        spotcheck_ok=ok_count,
        spotcheck_suspicious=sus_count,
        spotcheck_rows="\n".join(spot_rows),
        spotcheck_notes=notes,
        n_unmapped=len(cfg.get("unmapped", [])),
        unmapped_rows="\n".join(unmapped_rows),
        side_by_side_examples="\n\n".join(examples),
    )


def review(state: dict) -> dict:
    from langgraph.types import interrupt  # imported here so tests can run nodes without a graph

    run_dir = RUNS / state["dataset_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    review_path = run_dir / "review.md"
    review_path.write_text(render_review(state))

    decision_text = interrupt({"review_path": str(review_path), "status": state["status"]})

    decision_text = str(decision_text).strip()
    if decision_text == "approve" or decision_text.startswith("approve:"):
        note = ""
        if ":" in decision_text:
            note = decision_text.split(":", 1)[1].strip()
        if state["status"] != "PASSING" and state["status"] != "PASSING WITH FLAGS" and note == "":
            raise ValueError(
                'approving a NOT PASSING / NOT USEFUL config needs a recorded reason: '
                '--decide "approve: <why this is acceptable>"'
            )
        return {"decision": "approve", "approval_note": note, "steps": state["steps"] + ["review"]}
    if decision_text == "abandon":
        return {"decision": "abandon", "steps": state["steps"] + ["review"]}
    if decision_text.startswith("reject"):
        comment = decision_text.split(":", 1)[1].strip() if ":" in decision_text else ""
        if comment == "":
            raise ValueError('reject needs a comment: --decide "reject: <what is wrong>"')
        return {"decision": "reject", "human_comment": comment, "steps": state["steps"] + ["review"]}
    raise ValueError(f'decision must be approve / reject: <comment> / abandon, got: {decision_text!r}')


def emit(state: dict) -> dict:
    import yaml

    cfg = state["config"]
    source_id = cfg["source_id"]
    run_dir = RUNS / source_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # final acceptance: the 150 rows nobody (model or loop) has seen, run once
    cfg_obj = MappingConfig(**cfg)
    accept_rows = state["accept"]
    acceptance = None
    if accept_rows:
        obs = extract_rows(accept_rows, cfg_obj, "cfg-acceptance", FIXED_TS)
        duplicate_ids = sum(
            1 for one in obs for flag in one["quality_flags"] if flag["flag"] == "duplicate_record_id"
        )
        acceptance = build_validation_report(obs, accept_rows, cfg_obj, duplicate_ids)
        (run_dir / "acceptance.json").write_text(json.dumps(acceptance, indent=2))

    header = (
        f"# Mapping config written by the schema-inference agent (not by hand).\n"
        f"# dataset: {cfg['dataset_id']} | revisions used: {state['revisions']}/3\n"
        f"# status at review: {state['status']}\n"
        f"# approved by a human reviewer at {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
    )
    if state.get("approval_note"):
        header += f"# reviewer's note: {state['approval_note']}\n"
    config_text = header + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True)

    log = {
        "dataset_id": cfg["dataset_id"],
        "steps": state["steps"] + ["emit"],
        "revisions": state["revisions"],
        "status_at_review": state["status"],
        "approval_note": state.get("approval_note", ""),
        "acceptance_all_pass": acceptance["all_pass"] if acceptance else None,
    }

    # The acceptance rows are the one check the reviewer never saw. If they
    # fail, publishing anyway would make the acceptance set decorative — so the
    # config is withheld and the run goes back to review. Publishing despite
    # the failure needs the same written exception as any non-green approval.
    if acceptance and not acceptance["all_pass"] and not state.get("approval_note"):
        candidate_path = run_dir / "config.candidate.yaml"
        candidate_path.write_text(
            "# NOT PUBLISHED: the acceptance set failed a check; awaiting a re-decision.\n"
            + config_text
        )
        log["config_path"] = str(candidate_path)
        log["withheld"] = "acceptance failed and the approval carried no written exception"
        (run_dir / "agent_log.json").write_text(json.dumps(log, indent=2))
        print(f"acceptance ({len(accept_rows)} unseen rows): all_pass=False — config NOT published")
        print(f"candidate kept at {candidate_path}; read {run_dir / 'acceptance.json'}, then")
        print('re-decide:  --decide "approve: <why this failure is acceptable>"  or  --decide "reject: <what to fix>"')
        return {"emitted": "", "steps": state["steps"] + ["emit"]}

    CONFIGS.mkdir(parents=True, exist_ok=True)
    config_path = CONFIGS / f"{source_id}.yaml"
    config_path.write_text(config_text)
    log["config_path"] = str(config_path)
    (run_dir / "agent_log.json").write_text(json.dumps(log, indent=2))
    print(f"config emitted: {config_path}")
    if acceptance:
        print(f"acceptance ({len(accept_rows)} unseen rows): all_pass={acceptance['all_pass']}")
        if not acceptance["all_pass"]:
            print("note: published despite the failed acceptance because the approval "
                  "carried a written exception — read runs/.../acceptance.json.")
    return {"emitted": str(config_path), "steps": state["steps"] + ["emit"]}


def abandon(state: dict) -> dict:
    run_dir = RUNS / state["dataset_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "abandoned.json").write_text(
        json.dumps({"status": state.get("status"), "validation": state.get("validation")}, indent=2)
    )
    print(f"abandoned: {state['dataset_id']} (run kept in {run_dir})")
    return {"steps": state["steps"] + ["abandon"]}
