# Design — Schema Inference and Entity Identification at Scale

Target: the Firmable take-home. Time box 6h; API budget < USD $10. This document was
written before implementation and records the design decisions and their reasoning.

## Goals and non-goals

**Goal.** A pipeline that (1) triages data.gov.au datasets for Australian business
content, (2) onboards an unseen tabular source via a multi-step agent that emits a
mapping config, (3) runs one generic engine over config + raw data to produce canonical
observations, (4) links records across sources with measured precision, and (5) merges
linked records into per-field-confidence company profiles.

**Non-goals (6h cut lines).** No database (JSONL files throughout). No web UI (CLI
approval). No regression/eval harness for the agent (runtime self-validation plus human
spot-checks instead; a golden-config regression harness is the three-week answer). No
NZBN sources.

## Stack

Python 3.12 via uv. Dependencies: `langgraph` + `langgraph-checkpoint-sqlite` (agent
graph, resume, human interrupt), `openai` SDK pointed at OpenRouter (no LangChain model
wrappers), `httpx`, `pandas`, `openpyxl`, `pyyaml`, `pydantic`, `rapidfuzz`.
Default model `anthropic/claude-sonnet-5.5`, overridable via `FIRM_MODEL`.

## Pipeline and CLI

```
firm triage    →  outputs/shortlist.csv            (Part 1, deterministic)
firm onboard <dataset-id>  →  configs/<src>.yaml    (Part 2, agent + human approval)
firm extract <src>  →  outputs/observations/<src>.jsonl   (Part 2, generic engine)
firm resolve   →  outputs/links.jsonl, unlinked.jsonl, clusters.jsonl  (Part 3)
firm profile   →  outputs/profiles.jsonl            (Part 4; supports --drop-source)
```

Layout:

```
src/firm/
  llm.py         OpenRouter client + ledger: every call logs step, model, tokens, cost
  ckan.py        CKAN Action API client
  readers.py     csv/tsv/xlsx/zip → rows; which reader + params comes from config
  validators.py  ABN/ACN checksums, enums, dates
  transforms.py  closed library of named transforms; configs reference by name only
  engine.py      config + raw rows → canonical observations
  agent/         graph.py (StateGraph) + nodes.py
  triage.py, resolve.py, profiles.py
outputs/         shortlist, configs, observations, links, unlinked, clusters, profiles,
                 ledger.jsonl, runs/<src>/ (per-step state + review material)
review/          hand-check sheets (Part 1: 20 datasets; Part 3: 50 links)
docs/            this file
TIMELOG.md       how the 6h budget was actually spent
```

**Core boundary:** the engine knows nothing about any specific source. Everything
source-specific lives in the agent-emitted YAML config. Configs cannot contain code —
only names of transforms from the closed library. This keeps "one engine + six configs"
honest: a config with embedded code is a parser wearing a trench coat.

## Part 1 — deterministic triage

Pull 400–600 unique package records via `package_search` over a fixed keyword set
(business, charity, licence, abn, register, company, …). Score each record with weighted
signals: ABN/ACN/ABR mentions in title/description (strong +), machine-readable resource
format CSV/XLSX/JSON (+), regulator publisher ASIC/ATO/ACNC/state regulators (+),
register/licensee/approval vocabulary (+), aggregate-statistics vocabulary (strong −:
aggregated tables contain counts, not entities). Top 50 → shortlist with dataset id,
title, organisation, formats, confidence, one-line reason. Hand-check a random 20 and
report the false-positive rate. Deterministic by design — the assignment explicitly
allows it at this stage; the agentic requirement applies to Part 2.

## Part 2 — the agent

LangGraph `StateGraph`, one thread per source, SqliteSaver checkpoints after every node
(a crash resumes from the last completed step; paid model calls are not repeated).

| # | node | actor | role |
|---|---|---|---|
| 1 | fetch_meta | code | package_show → licence, publisher, modified date; download preferred resource |
| 2 | inspect | model+code | model sees raw first ~50 lines (or per-sheet heads) and decides reader, delimiter, header row, sheet; code executes that decision; on parse failure the error goes back to the model, one retry |
| 3 | profile | code | per-column null rate, distinct count, 10 samples, regex hints (ABN-like, postcode-like, date-like). Rows split: 200 visible to the model, 500 held out for validation |
| 4 | propose | model | input: ontology + profile + 20 sample rows + transform catalogue. Output: config JSON (pydantic-checked). Every column must be dispositioned: mapped, or unmapped with a reason. Missing columns → a delta request for just those columns |
| 5 | validate | code | run the engine with the proposed config over the 500 held-out rows; produce a validation report with failing examples |
| 6 | (edge) | code | pass → review; fail and revisions < 3 → revise; else → review flagged NOT PASSING |
| 7 | revise | model | input: previous config + validation report + failing examples. Output: new config + per-field change notes. Unfixable fields move to unmapped with a reason |
| 8 | review | human | `interrupt()`. Human sees runs/<src>/review.md (mapping table, confidences, validation numbers, unmapped list). Actions: approve / reject-with-comment (comment goes back to revise) / abandon. The human never edits the config directly — that would make it hand-authored |
| 9 | emit | code | write configs/<src>.yaml + config hash, agent version, approver, timestamp |

**Validation thresholds (constants in code):** ABN/ACN checksum pass ≥ 95% of non-null
mapped values; enum legality ≥ 98%; date parse ≥ 95%; referenced source columns must
exist; post-transform null rate ≤ source null rate + 2pp; `source_record_id` unique.

**Why fixed graph, not free-tool-calling ReAct:** deterministic step count and cost
(reportable per the brief), self-correction visible as a graph edge (validate→revise),
checkpointable structured state, a fixed approval point, and explainable line by line.

**Proof of agency:** after the six sources, run the untouched pipeline over a seventh
dataset not used during development; ship its config and run log as `unseen demo`.

## Config schema (agent-emitted)

```yaml
source_id: acnc-charity-register
licence: cc-by-4.0
source_reliability: {value: 0.9, rationale: "national regulator's own register"}
reader: {format: csv, encoding: utf-8, delimiter: ",", header_row: 0}
record_id: {strategy: column, columns: [ABN]}      # fallback: row_hash (documented)
observed_at: {strategy: dataset_modified}           # or a source column
fields:
  - {canonical: entity.abn, source: ABN, transforms: [abn_normalize],
     confidence: 0.97, evidence: "99.6% checksum pass on 500 unseen rows"}
unmapped:
  - {source: Charity_Size, reason: "no ontology field"}
```

## Engine output

One JSON object per source record: the observation envelope (source_id,
source_record_id, observed_at, ingested_at, licence, extractor_version = config hash +
engine version) plus a `claims` list: {field, value, raw, field_confidence,
derivation_level}. Multi-valued fields (trading names) emit one claim each. An ABN that
fails its checksum is not emitted as a value; it is recorded under `quality_flags`.
No reconciliation at ingest — five sources disagreeing produce five observations.

## Part 3 — entity identification

**Stored truth is a pairwise link table** (JSONL): {record_a, record_b, link_confidence,
evidence, matcher_version, threshold_used, created_at}, append-only. Entities are
derived: union-find over accepted links; cluster snapshots go to `clusters.jsonl` with a
header noting the link set + threshold they derive from (a cache, not truth).
Deterministic entity ids (min record id in cluster); recomputation emits an
old-id → new-id crosswalk.

**Why:** a bad link is one deletable row, and a model upgrade is an append + pairwise
diff + re-derive + crosswalk — which is the design answer to "millions of existing links
and a better matching model". Storing entity ids directly destroys the evidence needed
to answer that.

**Matchers (in order):** (1) ABN equality, checksums valid → confidence ~0.98;
(2) ACN/ABN-tail equality → high; (3) normalised exact name + same state → medium;
(4) rapidfuzz name similarity in a grey band → **unlinked queue** with reason, never
auto-linked. Thresholds are constants; report precision at the chosen threshold via a
50-link hand-check, plus the looser-threshold curve if time allows.

**Hairball defence** (transitive closure amplifying one bad fuzzy link):
ABN-equality links propagate freely (same valid ABN is the same entity by definition).
Fuzzy-name links may attach records to a cluster but may not *bridge* two clusters that
each contain distinct conflicting ABNs — such links go to a conflict queue. No
fuzzy-to-fuzzy chaining. Clusters larger than 10 records are flagged for review.

**Relationships (parent/subsidiary):** out of scope for linking; where a source states a
relationship we record it as an observation claim and note in the write-up how the link
table would carry typed edges (`same_as` vs `parent_of`) later.

## Part 4 — profiles

For 50 linked entities, group claims by canonical field. Winner per field:
higher source_reliability → newer observed_at → majority. Losing values are kept and
shown (value, source, why it lost). Field confidence = field_confidence ×
source_reliability, both factors shown separately. Absent fields are absent keys.
`--drop-source <id>` re-runs assembly without one source and reports how many profiles
changed and how badly (the source-fragility question).

## Cost model

Agent calls per source: 1 inspect + 1 propose + ≤3 revise, ≈ 15–40k tokens →
estimated $0.20–0.40/source, ≈ $1.50–3 for 7 sources (estimate; actuals come from
`outputs/ledger.jsonl`, which records tokens and cost per step). Everything outside
Part 2 is deterministic and free. OpenRouter key is personal, budget-capped.

## Risks and fallbacks

- A source fights the reader → swap it for another shortlist entry (we have 50).
- Revise loop can't pass thresholds → ship flagged NOT PASSING with the validation
  report; honesty over coverage.
- Time pressure → Part 2 may steal budget from Part 4, never the reverse (assessment
  order: agentic > generalises > mapping > resolution > profiles).
