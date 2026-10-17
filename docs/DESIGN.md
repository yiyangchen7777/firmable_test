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
| 3 | profile | code | per-column null rate, distinct count, 10 samples, regex hints (ABN-like, postcode-like, date-like). Rows split three ways: 200 visible to the model, 350 held out for the validate/revise loop, 150 reserved as a final acceptance set used exactly once after approval (the loop sees its failures, so loop pass-rates are debugging numbers; reported numbers come from the untouched set) |
| 4 | propose | model | input: ontology + profile + 20 sample rows + transform catalogue. Output: config JSON (pydantic-checked). Every column must be dispositioned: mapped, or unmapped with a reason. Each mapping must carry semantic evidence: the source column name, sample values, and why they mean that canonical field — not just that they parse. Missing columns → a delta request for just those columns |
| 5 | validate | code+model | (a) code: run the engine with the proposed config over the 350 held-out rows; produce a validation report with failing examples. (b) model (cheap semantic spot-check): 10 random held-out raw records shown side-by-side with their canonical output; flag mappings that parse but mean the wrong thing (licence issue date mapped to date_registered, applicant name mapped to legal_name). Semantic flags feed revise like any other failure |
| 6 | (edge) | code | pass → review; fail and revisions < 3 → revise; else → review flagged NOT PASSING |
| 7 | revise | model | input: previous config + validation report + failing examples. Output: new config + per-field change notes. Unfixable fields move to unmapped with a reason |
| 8 | review | human | `interrupt()`. Human sees runs/<src>/review.md: mapping table with per-field semantic evidence, validation numbers, unmapped list, and 5 raw records side-by-side with their canonical output (so a human can catch semantic mismatches, not just read pass rates). Actions: approve / reject-with-comment (comment goes back to revise) / abandon. The human never edits the config directly — that would make it hand-authored |
| 9 | emit | code | write configs/<src>.yaml + config hash, agent version, approver, timestamp |

**Validation thresholds (constants in code):** ABN/ACN checksum pass ≥ 95% of non-null
mapped values; enum legality ≥ 98%; date parse ≥ 95%; referenced source columns must
exist; post-transform null rate ≤ source null rate + 2pp; conditional pairs (mixed
identifier columns) cover ≥ 95% of non-null values, with every abstained value listed
for review — real sources carry junk identifiers and abstaining on them is correct;
`source_record_id` unique over the full sample. Hard-check failures loop back to revise
(≤3 rounds); semantic-only flags yield status PASSING WITH FLAGS and go straight to the
human, since a flag the closed catalogue cannot fix would loop the model pointlessly.
**Minimum-useful rule:** a config that maps neither a name field nor a
business identifier passes nothing — it is flagged NOT USEFUL even if every check above
passes. "Validates" and "is worth having" are different claims.

**Paid calls are idempotent:** besides graph checkpoints, every LLM response is cached
on disk keyed by a hash of (step, prompt). A crash between an API response and the next
checkpoint re-reads the cache instead of paying again.

**Why fixed graph, not free-tool-calling ReAct:** deterministic step count and cost
(reportable per the brief), self-correction visible as a graph edge (validate→revise),
checkpointable structured state, a fixed approval point, and explainable line by line.

**Proof of agency:** after the six sources, run the untouched pipeline over a seventh
dataset not used during development; ship its config and run log as `unseen demo`.

**Source selection includes an overlap probe.** Format/publisher diversity alone can
yield six sources whose businesses never co-occur, starving Parts 3–4 (50 linked
entities are needed). Before committing to the six: sample each candidate's identifier
columns, intersect pairwise, and keep a set with enough expected cross-source entities.
If organic overlap in 1,000-row samples is too thin, seed the sampling by shared ABNs —
and, for sources that carry no identifiers at all, by their normalised names, since
names are the only way such a source can ever link — and say so in the README:
precision is measured either way; coverage is never claimed.
If a source is swapped out for resisting, its failed run stays in outputs/runs/ and is
discussed in the write-up — the boundary of the system's generality is a finding.

## Config schema (agent-emitted)

```yaml
source_id: acnc-charity-register
licence: cc-by-4.0
source_reliability: {value: 0.9, rationale: "national regulator's own register"}
reader: {format: csv, encoding: utf-8, delimiter: ",", header_row: 0}
# An entity identifier is NOT automatically a record identifier: licence/contract
# sources can have many rows per ABN. Prefer the source's own key, else a composite,
# else a deterministic row hash. Uniqueness is validated over the full sample.
record_id: {strategy: composite, columns: [ABN, Registration_Date]}
# observed_at_basis records whether the timestamp is a real per-record date or a
# proxy (catalogue snapshot date). Proxy timestamps are treated as weak downstream.
observed_at: {strategy: dataset_modified, basis: proxy}
# Optional per-field reliability adjustments (a regulator is strong on legal_name,
# weaker on website); omitted fields inherit source_reliability.
reliability_overrides: {entity.website: 0.6}
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
evidence, matcher_version, run_id, threshold_used, created_at}, append-only. A link is
never physically deleted: withdrawing one means appending a retraction record (run_id,
reason). The **active link set** = links of the accepted run minus retractions. Every
resolve run records a run_id, the matcher version, thresholds, and a hash of its input
observations, so any cluster can be reproduced. Entities are derived: union-find over
the active links; cluster snapshots go to `clusters.jsonl` stamped with the run they
derive from (a cache, not truth). Entity ids (min record id in cluster) are labels valid
for that run only; recomputation emits an old-id → new-id crosswalk that supports
one-to-many (splits) and many-to-one (merges).

**Why:** a bad link is one appendable retraction, and a model upgrade is: new run
appended alongside the old, pairwise diff, re-derive clusters, crosswalk, switch the
accepted run (or roll back to it) — which is the design answer to "millions of existing
links and a better matching model". Storing entity ids directly destroys the evidence
needed to answer that.

**Matchers (in order):** (1) ABN equality, both checksums valid → ~0.98;
(2) ACN equality, only when both sides are true ACN fields → high. An ABN tail matching
an ACN is corroborating evidence only, never sufficient for a link on its own — the
ontology warns the last 9 digits of an ABN are not always the ACN;
(3) normalised exact name + same state → medium;
(4) rapidfuzz name similarity in a grey band → **unlinked queue** with reason, never
auto-linked. All confidence values are heuristic scores, not calibrated probabilities;
what calibrates them is the measured precision from the 50-link hand-check at the chosen
threshold (plus the looser-threshold curve if time allows).

**Hairball defence** (transitive closure amplifying one bad link):
ABN-equality links propagate freely (same valid ABN is the same entity by definition).
Name-based links — exact *or* fuzzy — may attach records to a cluster but may not
*bridge* two clusters that each contain distinct conflicting identifiers; such links go
to a conflict queue. No fuzzy-to-fuzzy chaining. Clusters larger than 10 records are
flagged for review.

**Relationships (parent/subsidiary):** out of scope for linking. Columns that state a
relationship are listed as unmapped with reason "relationship, out of scope"; the
write-up describes how the link table would carry typed edges (`same_as` vs `parent_of`)
later. They are not stuffed into canonical entity fields.

## Part 4 — profiles

For 50 linked entities, group claims by canonical field. Winner per field:
higher source reliability (per-field overrides considered) → newer observed_at →
majority. Losing values are kept and shown (value, source, why it lost). When recency
decided a winner but either timestamp is a proxy (catalogue date, not a per-record
date), the conflict entry is marked "weak recency" — catalogue metadata updating does
not mean the source re-asserted every record. Field confidence = field_confidence ×
source_reliability, both factors shown separately; this is a heuristic quality score,
not a calibrated probability, and it is conditional on the records being linked
correctly — so each profile also carries `cluster_support`, the weakest link confidence
in its cluster. Absent fields are absent keys.
`--drop-source <id>` re-runs resolve *and* assembly without one source and reports both
effects: field-level changes, and entities that split because the dropped source was the
bridge between their records (the source-fragility question).

## Cost model

Agent calls per source: 1 inspect + 1 propose + 1 semantic spot-check + ≤3 revise,
≈ 15–45k tokens →
estimated $0.20–0.40/source, ≈ $1.50–3 for 7 sources (estimate; actuals come from
`outputs/ledger.jsonl`, which records tokens and cost per step). Everything outside
Part 2 is deterministic and free. OpenRouter key is personal, budget-capped.

## Risks and fallbacks

- A source fights the reader → swap it for another shortlist entry (we have 50).
- Revise loop can't pass thresholds → ship flagged NOT PASSING with the validation
  report; honesty over coverage.
- Time pressure → Part 2 may steal budget from Part 4, never the reverse (assessment
  order: agentic > generalises > mapping > resolution > profiles).
