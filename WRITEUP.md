# WRITEUP

## Cost — actuals from `outputs/ledger.jsonl`, not estimates

- Runtime API total: **USD $2.83** (59 calls, 519k prompt / 180k completion tokens,
  `anthropic/claude-sonnet-5.5` via a personal OpenRouter key). Every call logged with
  step, source, tokens and the billed cost.
- **One-time inference per source**: steady state **$0.13–0.55** (per-source table
  under Agent design). The first source cost $0.83 because validator calibration
  changed prompts and re-billed; a disk response cache makes unchanged steps free.
- **Per-record cost: $0** — extraction is the deterministic engine. Two oversized
  sources seeded-sampled at 1,000 rows, one 66k-row source head-sampled at 1,000, the
  rest in full → 19,542 observations.
- Not counted, on purpose: the coding assistant that *built* the system (personal
  subscription). The $10 budget governs runtime spend.

## Agent design

- Fixed 9-node LangGraph: fetch → inspect(model) → profile(code) → propose(model) →
  validate(code + model semantic spot-check) → revise(model, ≤3) → review(human) →
  emit. State carried between nodes (and checkpointed to sqlite after each): the
  reader decision, the 200/350/150 row split, column profiles, the config draft, the
  validation report with failing examples, the revision count, the human's comment.
- **Onboarding one source, measured** (steps = graph nodes executed incl. the human
  gate; wall-clock = model time from the ledger; downloads and the deterministic
  engine excluded):

  | source | steps | revisions | LLM calls | tokens | model time | cost |
  |---|---|---|---|---|---|---|
  | credit-licensee (first, incl. calibration) | 10 | 1 | 14 | 199k | 5.2 min | $0.83 |
  | corporate-transparency (xlsx) | 10 | 1 | 5 | 29k | 0.9 min | $0.13 |
  | acnc-register (69 cols) | 10 | 1 | 6 | 147k | 3.1 min | $0.55 |
  | business-names (mislabelled tsv) | 10 | 1 | 6 | 47k | 1.3 min | $0.20 |
  | discount-directory (no ids) | 10 | 1 | 9 | 95k | 3.0 min | $0.43 |
  | ipgod2022 (hard source) | 13 | 3 | 15 | 119k | 3.6 min | $0.51 |
  | **afs-licensee (unseen demo)** | **7** | **0** | **3** | **59k** | **0.7 min** | **$0.18** |

- **Where a run fails without losing the job**, in layers: transport retries inside
  each call; one JSON-repair retry per model step; one inspect retry fed the parse
  error; ≤3 validate→revise rounds fed the failing examples; a crash resumes from the
  last checkpointed node; and a disk cache keyed on the prompt means a resumed run
  never re-pays a completed call.
- **Models propose, code gates, a human approves.** ABN/ACN checksums, enums, dates,
  null drift (per column entry) and record-id uniqueness run engine-side — no config
  bypasses them. Rows split 200 model-visible / 350 revise-loop / 150 acceptance (run
  once after approval; only those numbers are reported).
- The human sees, per source: every mapping with semantic evidence (column name +
  samples + why it means that field), validation vs thresholds, spot-check verdicts,
  unmapped columns with reasons, five raw-vs-canonical record pairs. Actions:
  approve / reject-with-comment / abandon — comments go verbatim to the revise node;
  **the human never edits a config**. Five of seven onboarding runs were rejected once;
  the verbatim decision trail is in `outputs/runs/<source>/decisions.json`. Approving a
  non-green status requires a written justification (used once: literal duplicate rows).
- **One worked round-trip of five:** the first credit-licensee proposal mapped
  `CRED_LIC_STATUS` (`APPR`) to `entity.status`. Reviewer: *"APPR describes the licence
  approval, not the company's existence — unmap it with that reason."* The revise node
  obeyed; nobody touched the YAML.
- **Weakest step, and how we know:** propose's semantic layer. Four of six first
  proposals mapped a *registration's* status or date onto the *entity* (licence,
  business name, charity registration, IP right) — parse rates ~100% every time; only
  the spot-check plus the reviewer caught them. Format errors are code's job; meaning
  errors need the second model pass and the human.
- Honesty under failure: handed a wrong resource (plant-breeder rights, no entities),
  the agent mapped **nothing** — 10/10 columns unmapped with correct reasons, status
  NOT USEFUL (`outputs/runs/ipgod2022-wrong-resource-pbr/`).

## The hard one

**ipgod2022 (design-party table).** One row = one party-role; the role column has no
ontology field; and the source asserts a local subsidiary's ABN on rows whose party is a
*foreign parent* (`country_code` us/ch). No mapping change fixes either — row filtering
is deliberately outside the closed catalogue. Our rule for "when is custom code
correct": when the fix generalises across sources. So we upgraded the matcher (below)
instead of writing a parser. Runner-up: the discount directory (no identifiers) produced
**zero accepted links** at our evidence bar — its name matches all sit in the refused
queue with reasons. The queue is the deliverable, not a failure.

## Scale: 6 → 500

1. **Human review throughput** breaks first — minutes/source × 500. Queue by validation
   status, risk-based sampling, batch-approve green runs; don't remove the human.
2. **Reachability/anti-bot** (one shortlisted source rejects every scripted client);
   triage needs liveness probes.
3. **Resolution blocking and storage** — name buckets grow superlinearly; JSONL gives
   way to a store with incremental runs and record-level diffs; row_hash record ids are
   snapshot-scoped, so source refreshes need their own versioning.
4. **Licence review** becomes a workflow (all six here are CC-BY family, recorded per
   observation).

## Change — the model-upgrade question, performed live

Every link records `matcher_version`, `run_id`, thresholds, evidence, timestamps;
observations are immutable; clusters are derived, versioned snapshots. Hand-checking 50
links measured **62% precision at matcher-0.1** — all 19 false positives one pattern
(foreign parents carrying a local ABN), *predicted in the reviewer's recorded approval
note for that source*. matcher-0.2 adds a country gate using country claims the
observations already carried. Procedure: archive v1 → re-run → crosswalk (341 entities
intact, 0 split, 13 shrunk or dissolved — 10 fully, 3 partly: the foreign-parent
clusters) → re-measure on the **same** labels: **19/19 FPs removed, 31/31 true links
kept**. That check is in-sample, so we also drew a **fresh, entity-stratified sample of
30 shipped links** (one per entity, no previously labelled pairs): **30/30 correct —
fresh-sample precision 100%, Wilson 95% lower bound 88.7%** (`review/
part3_fresh_handcheck.csv`, with the ABR testimony used to adjudicate).
Honesty notes: the link table is append-only within a run, but across runs this build
regenerates files and keeps versions as archives (`outputs/history/`) — true retraction
records are designed, not exercised; and ABN-seeded sampling enriches exactly the
foreign-parent region, so 62% describes the seeded overlap, not the corpus. Recorded in
advance, which made all this possible: per-link version + evidence + thresholds,
immutable observations including fields we didn't know we needed (country), versioned
snapshots, a labelled sample. Rollback = derive from the archived v1 links.

## Profile assembly (Part 4)

50 profiles from randomly sampled multi-source entities (seed in code). Per field:
winner + support count, both confidence factors shown separately (heuristics, bounded
by the measured precision), provenance, every losing value with the rule that beat it;
majority counts distinct sources before rows; `trading_name` is multi-valued; absent
fields are absent keys; each profile carries `cluster_support` (weakest link under it). **Drop-one-source:** removing the
tax-transparency anchor splits or dissolves **31/50** entities, 19 survive, 1 changes a
field value — a single point of failure, with the caveat that seeded sampling made it
the hub of the sampled graph.

## Entity relationships

Pairwise **same_as** link table as stored truth; entities derived by union-find; name
links may attach records but never bridge clusters holding different ABNs; fuzzy never
links — it queues. `parent_of` deliberately untouched: such columns are unmapped with
that reason; the extension is typed edges (`same_as` clustered, `parent_of` stored,
never merged). Structural admission: every shipped link is identifier-tier — the name
tier never fired, because 498 of its 509 candidate pairs involve sources that map no
state at all. What this build demonstrates is identifier-join plus refusal discipline;
the name tier's value is its queue. We chose links-as-truth because conclusions
(cluster ids) are cheap to recompute; evidence is not.

## Next, with three weeks

1. Regression harness: golden configs, replay per agent/prompt version, mapping
   accuracy over time — the evaluation layer this build lacks.
2. Engine gaps measured in use: envelope `valid_from`/`valid_to`, row filters,
   multi-column concat, country-aware postcode validation, refresh-stable record ids.
3. Review UI with batch queues; calibrate confidences against accumulated labels.
4. ABR as a link-time verification oracle (it settled every hand-check dispute).
5. Observations/links into a database; incremental refresh; licence tracking.

---

*Honesty appendix.* Hand-check protocol, a finding in itself: in both rounds the
reviewer's initial flags (driven by name dissimilarity) were largely overturned by
register evidence — Australia's business-name system makes "the names look unrelated" a
misleading signal for identifier links in *both* directions — so every verdict was
adjudicated against the ABR / primary registers before being recorded. Part 1 FP rate:
35% verified (7/20), 45% counting two unverifiable resources against ourselves. Looser-threshold linking (exact name, no state), 16
non-duplicate refused pairs: 6 confirmed same, 3 unsure, 7 distinct — refusing cost at
most 9 true links, avoided at least 7 wrong ones. Seeded sampling disclosed in README:
precision is measured, coverage never claimed.
