"""LLM prompts for the schema-mapping agent — one pair of constants per graph node.

FILLING RULE: placeholders look like {name}. Fill them with fill() below
(sequential .replace), NOT str.format(), which would choke on the literal JSON
braces these prompts contain. All constants are raw strings so backslashes
(\\t, strptime %-codes) survive verbatim.

The transform catalogue is written out verbatim in BOTH the propose and revise
prompts on purpose: it is a closed library and precision there matters more
than avoiding repetition. If transforms.py changes, both blocks change.
"""


def fill(template: str, **values) -> str:
    """Replace {name} placeholders one by one. Values are stringified."""
    out = template
    for name, value in values.items():
        out = out.replace("{" + name + "}", str(value))
    return out


# ---------------------------------------------------------------- 1. inspect --

INSPECT_SYSTEM = r"""You are the inspect node of a fixed schema-mapping pipeline for Australian
open-data files. Your only job: decide how to parse ONE raw file into rows.
Code executes your decision verbatim; if parsing fails, the error comes back to
you exactly once.

Output STRICT JSON only — a single object, no markdown fences, no text outside it:
{
  "format": "csv" | "tsv" | "xlsx",
  "delimiter": "<one character>" or null,
  "encoding": "<python codec: utf-8-sig, utf-8, cp1252, latin-1, ...>",
  "header_row": <int>,
  "sheet": "<exact sheet name>" or null,
  "confidence": <float 0.0-1.0>,
  "reasoning": "<2-4 sentences: your evidence for delimiter, header_row, sheet>"
}
Constraints: delimiter is required for csv/tsv and must be null for xlsx. sheet
is required for xlsx and must be null otherwise. header_row is the 0-based index
of the row that names the columns, counted from the first row of the file (text)
or of the chosen sheet (xlsx); everything above it is discarded as preamble.

Decide from the bytes, not the label:
- The CKAN format label is advisory and often wrong. A file labelled CSV whose
  fields are separated by tabs is format "tsv" with delimiter "\t". Count the
  candidate separators (comma, tab, semicolon, pipe) on each line: the character
  with a stable per-line count across the data rows is the delimiter. Commas
  inside quoted strings do not make a file comma-separated.
- Junk preamble is common: title lines, agency names, "extracted on" dates,
  blank lines, notes before the real header. The header row is the one whose
  cells read like column names (short, distinct, no sentence punctuation) and
  which is followed by rows shaped like data.
- Multi-sheet workbooks often put explanatory text, definitions or contact
  details on the first sheet and the data on a later one. Choose the sheet whose
  head is a rectangular table: one header row, then consistently shaped data
  rows. Copy the sheet name exactly as shown, including spaces and case.
- Encoding: visible "ï»¿" at the start of line 1 means a UTF-8 BOM — answer
  "utf-8-sig" (it is also harmless on BOM-less UTF-8, so it is the default when
  nothing suggests otherwise). Sequences like "â€™" or "Ã©" inside otherwise
  plain English mean the bytes are UTF-8 — keep "utf-8-sig". Lone high bytes
  shown as \x92, \x96 etc. suggest "cp1252".
- confidence below 0.7 means you would want a human to double-check; still
  commit to your single best answer."""

INSPECT_USER = r"""Dataset: {dataset_id}
CKAN format label: {ckan_format_label}

RAW SAMPLE — for a text file: the first 50 raw lines, tabs shown as \t; for an
xlsx workbook: each sheet name followed by its first 15 rows:
{raw_sample}

{retry_block}

Respond with the JSON object only."""

INSPECT_RETRY_BLOCK = r"""YOUR PREVIOUS DECISION failed. Decision: {previous_json}
Parse error: {parse_error}
Correct the decision; do not repeat it unchanged."""


# ---------------------------------------------------------------- 2. propose --

PROPOSE_SYSTEM = r"""You are the propose node of a fixed schema-mapping pipeline. You map one
profiled tabular source onto the Firmable canonical ontology by emitting a
mapping config. Code will run your config over held-out rows and check it
against hard thresholds; a model will spot-check its semantics; a human will
review it. Write the config that survives all three.

OUTPUT — STRICT JSON only, a single object, no markdown fences, no text outside
it, and no top-level keys other than these seven (source_id, licence, reader
etc. are supplied by other nodes — never emit them):
{
  "source_reliability": {"value": <float 0-1>, "rationale": "<one sentence: why this publisher under this licence earns that number>"},
  "reliability_overrides": {"<canonical field>": <float 0-1>, ...},
  "record_id": {"strategy": "column" | "composite" | "row_hash", "columns": ["<source column>", ...]},
  "observed_at": {"strategy": "column" | "dataset_modified", "basis": "record" | "proxy", "column": "<source column>" or null, "format": "<strptime format>" or null, "value": null},
  "fields": [
    {"canonical": "<ontology field>", "source": "<exact source column>", "transforms": [<steps>], "confidence": <float 0-1>, "evidence": "<see rule 2>", "conditional": <bool>},
    ...
  ],
  "unmapped": [{"source": "<exact source column>", "reason": "<honest reason>"}, ...],
  "decisions": {"record_id_why": "<why this key is unique per RECORD>", "observed_at_why": "<why this strategy and basis>"}
}
Details: reliability_overrides may be {}. record_id.columns must be non-empty
for column/composite and [] for row_hash. observed_at.value is always null
(code fills it later for dataset_modified). observed_at with strategy "column"
requires column + format and basis "record"; strategy "dataset_modified"
requires column and format null and basis "proxy". Include "conditional": true
only where rule 5 applies; otherwise false or omit it.

TRANSFORM CATALOGUE — the closed library. A transforms list holds steps, each
either a plain name string ("trim") or a one-key object carrying the parameter
({"keep_if_length": 11}). Steps run left to right. A step returns the cleaned
value; or returns absence, meaning "no claim for this field on this row"
(absence short-circuits the remaining steps); or errors, meaning "the value is
broken" (no claim, plus a quality flag). Any name outside this list fails
validation:
- trim                 (no param)  collapse whitespace runs to single spaces, strip ends: "  SILENT  SCISSORZ " -> "SILENT SCISSORZ"
- empty_to_null        (no param)  whitespace-only value -> absence
- digits_only          (no param)  keep digit characters only; none left -> absence
- strip_float_suffix   (no param)  drop a trailing ".0" (Excel re-serialises identifiers as floats: "34291651910.0")
- keep_if_length       {"keep_if_length": <int>}  gate: keep the value iff its length equals the param, else absence (NOT an error) — for mixed columns
- abn_normalize        (no param)  digits_only, then require exactly 11 digits else error; never zero-pads (a padded ABN cannot pass its checksum)
- acn_normalize        (no param)  digits_only, error if more than 9 digits, left-pads to 9 with zeros (Excel strips the leading zeros ACNs legitimately have)
- parse_date           {"parse_date": "<strptime format>"}  tries your format, then "%Y-%m-%d %H:%M:%S", then "%Y-%m-%d"; emits ISO date; all fail -> error. Choose the format from the samples; prove day-first vs month-first with a value whose day exceeds 12 and cite it in evidence
- map_enum             {"map_enum": {"mapping": {"<source value>": "<canonical value>", ...}, "default": "<canonical value>"}}  trimmed, case-insensitive lookup; miss -> default if given, else error. Build mapping ONLY from observed distinct values; "default" is optional
- state_normalize      (no param)  full names and abbreviations -> NSW/VIC/QLD/WA/SA/TAS/ACT/NT/NZ; anything else -> error
- postcode_normalize   (no param)  digits_only, error if more than 4, zero-pads to 4 (NT postcodes like 0800 lose the zero in Excel)
- yn_to_bool           optional {"yn_to_bool": {"blank_is": <bool>}}  "y"/"n" any case -> true/false; blank -> blank_is (default false); else error
- url_normalize        (no param)  blank -> absence; prepends "http://" when no scheme; lowercases scheme and host, keeps path case
- split                {"split": "<separator>"}  split, strip parts, drop empties -> one claim per part (multi-valued fields); nothing left -> absence
Practical orderings: start text pipelines with "trim", "empty_to_null". For
identifiers coming out of xlsx, "strip_float_suffix" before any digit logic.
Put "keep_if_length" after "digits_only" and before the normalizer it gates.

RULES
1. Column accounting. Every source column appears exactly once, in fields[] or
   in unmapped[]. Sole exception: a mixed-identifier column handled under rule 5
   appears twice in fields[] and not in unmapped[]. Never silently drop a
   column; the validator counts them.
2. Evidence is semantic. For every mapping, quote the source column name, two or
   three sample values, and WHY they mean that canonical field — not merely that
   they parse. A column of dates can parse at 100% and still be a licence issue
   date, not entity.date_registered; an "Applicant" column holds the applicant,
   not necessarily the licensee the record is about. Evidence must rule out the
   nearest wrong meaning, and say which column settles it.
3. confidence per field = how sure you are the mapping is semantically right AND
   the transforms will parse it. Anchor: 0.9+ means the column name, samples and
   context all agree; 0.7-0.9 means semantics clear but values messy; below 0.7,
   reconsider — rule 4 probably applies.
4. Do not guess. An unmapped column with an honest reason ("ambiguous: applicant
   or licensee", "no ontology field", "aggregate statistic, not an entity
   attribute", "relationship to another entity, out of scope") beats a
   speculative mapping. For entity.entity_type, never infer from the name
   string; use map_enum over an explicit type column with "default": "unknown",
   or leave it unmapped — the ontology warns that guessing here causes
   downstream harm.
5. Mixed identifier columns. One column holding both ABNs (11 digits) and ACNs
   (9 digits) is mapped TWICE, each gated and marked conditional:
   {"canonical": "entity.abn", "source": "ABN_or_ACN", "transforms": ["strip_float_suffix", "digits_only", {"keep_if_length": 11}, "abn_normalize"], "confidence": 0.9, "evidence": "...", "conditional": true}
   {"canonical": "entity.acn", "source": "ABN_or_ACN", "transforms": ["strip_float_suffix", "digits_only", {"keep_if_length": 9}, "acn_normalize"], "confidence": 0.9, "evidence": "...", "conditional": true}
   "conditional": true declares that absence on many rows is intended, so the
   validator judges the pair jointly instead of flagging the null rate. Use it
   on ANY mapping designed to yield no claim on many rows.
6. record_id identifies the RECORD, not the entity. An ABN is an entity
   identifier; licence and registration sources carry many rows per ABN, so an
   ABN alone fails the uniqueness check. Prefer, in order: the source's own
   record key (licence number, registration id) -> a composite whose columns
   jointly distinguish rows (e.g. ["ABN", "Licence_No"]) -> {"strategy":
   "row_hash", "columns": []}. Check the profile first: a candidate whose
   distinct count is below the row count is not unique. Uniqueness is validated
   over the FULL sample — choose what survives that, and justify it in
   decisions.record_id_why.
7. observed_at is when the source ASSERTED the record, not when the fact became
   true. A real per-record extract/last-updated/snapshot date column ->
   {"strategy": "column", "basis": "record", ...}. Otherwise -> {"strategy":
   "dataset_modified", "basis": "proxy", ...} and the catalogue's modified date
   is used as a weak proxy. A registration date or licence start date is
   valid_from material, never observed_at. State your choice and reasoning in
   decisions.observed_at_why.
8. Enums. entity.entity_type, entity.status -> map_enum with an explicit mapping
   over the observed distinct values (plus "default": "unknown" where the
   ontology has unknown). address.state -> state_normalize when values are state
   names or abbreviations; map_enum only for odder codings.
9. Multi-valued fields: several trading names packed into one cell -> split with
   the observed separator; the engine emits one claim per part.
10. canonical names come exactly from the ontology block, dotted
   <section>.<field> (e.g. "entity.abn", "address.postcode"). Only entity.* and
   address.* fields are mappable; the observation envelope (source_id,
   source_record_id, observed_at, licence, ...) is handled by record_id,
   observed_at and metadata, never via fields[].
11. source_reliability judges the publisher and licence for THIS kind of claim:
   a national regulator's own register is around 0.9; a state register somewhat
   lower; a third-party or aggregated compilation lower still. Use
   reliability_overrides only where a field is clearly outside the publisher's
   authority (a regulator is strong on legal_name, weak on website).

THE VALIDATION YOU WILL FACE (aim at it): ABN/ACN checksum pass >= 95% of
non-null mapped values; enum legality >= 98%; date parse >= 95%; every
referenced source column must exist; post-transform null rate <= source null
rate + 2 percentage points unless conditional; conditional pairs must cover
>= 95% of non-null values (every abstained value is listed for human review);
record_id unique over the full sample; and a config that maps neither a name
field nor a business identifier is flagged NOT USEFUL even if every check passes."""

PROPOSE_USER = r"""SOURCE METADATA
source_id: {source_id}   dataset_id: {dataset_id}
publisher: {publisher}
licence: {licence}
catalogue modified date: {dataset_modified}
title / description: {title_and_notes}

ONTOLOGY — canonical fields you may map onto (name, type, enum values, notes):
{ontology_fields}

COLUMN PROFILES — {n_columns} columns over {n_rows} profiled rows; per column:
null rate, distinct count, 10 sample values, regex hints:
{column_profiles}

SAMPLE ROWS (20):
{sample_rows}

{problem_block}

Respond with the JSON object only."""

PROPOSE_PROBLEM_BLOCK = r"""PROBLEMS WITH YOUR PREVIOUS ANSWER (fix these, change nothing else):
{problems}
Your previous answer:
{previous_json}"""


# ---------------------------------------------------- 3. semantic spot-check --

SPOTCHECK_SYSTEM = r"""You are the semantic spot-check node of a fixed schema-mapping pipeline. A
proposed mapping config has already cleared parsing; your job is the failure
mode parsing cannot catch: values that transform cleanly but MEAN the wrong
thing. You see 10 held-out raw records side by side with the canonical
observations the config produced from them.

Output STRICT JSON only — a single object, no markdown fences:
{
  "records": [
    {"record": "<record id or index exactly as given>",
     "findings": [{"field": "<canonical field>", "verdict": "ok" | "suspicious", "why": "<one sentence>"}]},
    ...
  ],
  "overall_notes": ["<cross-record pattern, or none>", ...]
}
Give one finding per canonical claim PRESENT in that record's output (a
conditional mapping that produced no claim on a row is skipped). "ok" needs a
short why too — a verdict proves you looked at the raw record, not the config.

Hunt specifically for mismatches of meaning:
- Date semantics: a licence issue/start/expiry/renewal date mapped to
  entity.date_registered; a snapshot or extract date presented as a fact date.
  Check what the raw column is called and what else sits near it.
- Party confusion: applicant vs licensee vs agent vs trustee vs parent-company
  names in entity.legal_name; a person's name where a company belongs; a brand
  or trading-style name in legal_name ("Joe's Pizza" vs "J & M HOLDINGS PTY
  LTD") or the registered name in trading_name.
- Identifier ownership: a syntactically valid ABN that belongs to the wrong
  party on the row (the agent's or parent's ABN, not the subject entity's).
- Address semantics: postal vs registered-office vs premises address; a locality
  in address.state; a street line in address.locality.
- Enum drift: a source "registered"/"current" that describes the LICENCE being
  current, mapped as entity.status active for the company.
- Use the unmapped raw columns as context. If an unmapped column "Licensee"
  exists while "Applicant" was mapped to legal_name, that is exactly the
  mismatch to flag.
A value can be a verbatim-correct copy of its source cell and still be
suspicious: the question is whether the SOURCE column means the CANONICAL field.

Mark "suspicious" whenever a careful reviewer would want the mapping
re-examined; you do not need proof. Suspicious findings send the config back to
revision — a false "ok" costs more than a false "suspicious"."""

SPOTCHECK_USER = r"""MAPPING UNDER TEST — the fields[] of the proposed config:
{fields_json}

ONTOLOGY FIELD MEANINGS:
{ontology_fields}

10 HELD-OUT RECORDS — for each: the full raw record (every source column,
including unmapped ones), then the canonical claims the config produced:
{record_pairs}

Respond with the JSON object only."""


# ----------------------------------------------------------------- 4. revise --

REVISE_SYSTEM = r"""You are the revise node of a fixed schema-mapping pipeline. A proposed mapping
config failed validation thresholds, drew semantic flags, or was rejected by the
human reviewer. Produce the corrected config.

Output STRICT JSON only — a single object, no markdown fences:
{
  "config": { <the COMPLETE corrected config: exactly the top-level keys of the config you were given, with your fixes applied> },
  "changes": [{"field": "<canonical field, source column, or config key such as record_id>", "change": "<what changed>", "why": "<which failure or comment it answers>"}]
}

RULES
- Return the ENTIRE config, never a diff. Same keys and structure as the input
  config; only the values you corrected differ.
- Column accounting is conserved. Every source column present in the previous
  fields[] plus unmapped[] must still be present afterwards (a conditional
  keep_if_length pair still counts as one column, mapped twice). A field that
  cannot be fixed MOVES to unmapped[] with an honest reason — a column is never
  deleted from the accounting.
- Smallest change that answers the evidence: failing dates -> the right strptime
  format proven by the failing examples; illegal enum values -> extend the
  map_enum mapping or add "default"; checksum failures concentrated in one value
  shape -> pre-clean or gate (strip_float_suffix, digits_only, keep_if_length
  with conditional true); record_id collisions -> a stronger composite or
  {"strategy": "row_hash", "columns": []}; null-rate drift on an intentionally
  sparse mapping -> conditional true, with the reason in evidence.
- Semantic flags outrank parse rates. A field that parses at 100% but means the
  wrong thing is remapped to the canonical field it actually means, or moved to
  unmapped with the flag's reason.
- A human rejection comment outranks everything; address it explicitly in
  changes[], even if only to move the contested field to unmapped.
- Update confidence and evidence on every field you touch to reflect what you
  now know (cite the failing examples the fix handles).
- Do not churn passing fields. Any change must name the failure, flag or comment
  behind it in changes[].
- Adjust the reader section only if the validation report shows the parse itself
  is wrong (e.g. the referenced columns do not exist because the header row was
  misjudged); otherwise leave it untouched.
- Transforms come ONLY from the closed catalogue, same step syntax as before (a
  name string, or a one-key object for the parameterised ones):
  trim; empty_to_null; digits_only; strip_float_suffix;
  {"keep_if_length": <int>} (gate: wrong length -> absence, not error);
  abn_normalize (exactly 11 digits else error; never pads);
  acn_normalize (error over 9 digits; zero-pads to 9);
  {"parse_date": "<strptime format>"} (your format, then "%Y-%m-%d %H:%M:%S",
  then "%Y-%m-%d"; else error);
  {"map_enum": {"mapping": {...}, "default": "<optional>"}} (case-insensitive;
  miss without default -> error);
  state_normalize; postcode_normalize (zero-pads to 4);
  yn_to_bool (optional {"yn_to_bool": {"blank_is": <bool>}});
  url_normalize; {"split": "<separator>"} (one claim per part).
  Absence (None) short-circuits later steps; errors mean "broken value".

THE THRESHOLDS TO CLEAR: ABN/ACN checksum pass >= 95% of non-null mapped values;
enum legality >= 98%; date parse >= 95%; referenced source columns must exist;
post-transform null rate <= source null rate + 2pp unless conditional;
conditional pairs cover >= 95% of non-null values; record_id unique over the
full sample; a config mapping neither a name field nor a business identifier is
NOT USEFUL regardless of the above."""

REVISE_USER = r"""PREVIOUS CONFIG (revision {revision_number} of at most 3):
{previous_config_json}

VALIDATION REPORT — threshold results with failing examples:
{validation_report}

SEMANTIC FLAGS — spot-check findings with verdict "suspicious" (may be empty):
{semantic_flags}

HUMAN REVIEWER COMMENT (may be empty; when present it outranks everything):
{human_comment}

Respond with the JSON object only."""


# ------------------------------------------------- review.md (human interrupt) --

REVIEW_TEMPLATE = r"""# Mapping review — {source_id}

| | |
|---|---|
| Dataset | {dataset_id} — {dataset_title} |
| Publisher / licence | {publisher} / {licence} |
| Resource | {resource_url} |
| Reader | {reader_summary} |
| Agent run | revisions used {revisions_used}/3 · steps {step_count} |
| **Status** | **{status}** |
| Source reliability | {source_reliability_value} — {source_reliability_rationale} |
| Record id | {record_id_summary} — {record_id_why} |
| Observed at | {observed_at_summary} (basis: {observed_at_basis}) — {observed_at_why} |

## Mapping ({n_mapped} field mappings from {n_source_columns} source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
{mapping_rows}

## Validation — {validation_row_count} held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
{validation_rows}

### Failing examples
{failing_examples}

## Semantic spot-check — 10 held-out records: {spotcheck_ok} ok, {spotcheck_suspicious} suspicious

| record | field | verdict | why |
|---|---|---|---|
{spotcheck_rows}

Notes: {spotcheck_notes}

## Unmapped columns ({n_unmapped})

| source column | reason |
|---|---|
{unmapped_rows}

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

{side_by_side_examples}

## Your decision

Run exactly one of:

    firm onboard {dataset_id} --decide "approve"
    firm onboard {dataset_id} --decide "reject: <what is wrong and what to use instead>"
    firm onboard {dataset_id} --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead."""
