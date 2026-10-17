# WRITEUP

## Cost — actuals from `outputs/ledger.jsonl`, not estimates

- Runtime API total: **USD $2.83** (59 calls, 519k prompt / 180k completion tokens,
  `anthropic/claude-sonnet-5.5` via a personal OpenRouter key). Every call is logged
  with step, source, tokens, and the cost OpenRouter reported.
- **One-time inference per source** (onboarding): steady state **$0.13–0.55**. The
  unseen seventh dataset cost **$0.18** (3 calls, 0 revisions). The first source cost
  $0.83 because validator-calibration re-runs re-billed changed prompts; an on-disk
  response cache makes unchanged steps free on re-runs, so a crash never pays twice.
- **Per-record cost: $0.** Extraction is the deterministic engine; model cost does not
  scale with row count. The two oversized sources were seeded-sampled at 1,000 rows,
  one 66k-row source head-sampled at 1,000, the rest taken in full → 19,542 canonical
  observations.
- Not counted, on purpose: the coding assistant used to *build* the system (personal
  subscription). The $10 budget governs what the *system* spends at runtime.

## Agent design

- Fixed 9-node LangGraph: fetch → inspect(model) → profile(code) → propose(model) →
  validate(code + model spot-check) → revise(model, ≤3) → review(human) → emit.
  State is checkpointed to sqlite after every node; a crash resumes at the last node.
- Division of labour: **models propose, code gates, a human approves.** ABN/ACN
  checksums, enum legality, date parsing, null drift and record-id uniqueness are
  enforced at the engine level — no config can bypass them. Rows are split 200
  (model-visible) / 350 (revise loop) / 150 (acceptance, run once after approval, the
  only numbers we report).
- Self-correction: the validate→revise edge carries threshold failures *with failing
  examples* and semantic flags. The human sees a review document per source: every
  mapping with semantic evidence (column name + samples + why it means that field),
  validation vs thresholds, spot-check verdicts, unmapped columns with reasons, and
  five raw-vs-canonical record pairs. Actions: approve / reject-with-comment /
  abandon. A rejection comment goes verbatim to the revise node — **the human never
  edits a config**. Five of seven onboarding runs were rejected once by the reviewer;
  every review event, with the verbatim rejection comment or approval note, is
  exported to `outputs/runs/<source>/decisions.json`. Approving a non-green status
  requires a recorded justification (used once, for literal duplicate rows).
- **Weakest step, and how we know:** propose's semantic layer. Four of six first
  proposals mapped a *registration's* status or date onto the *entity* (credit-licence
  status, business-name status, charity registration date, IP-right dates). Parse
  validation passed at ~100% in every case; the model spot-check plus the human
  reviewer caught all four. Deterministic checks catch format errors; meaning errors
  need the second model pass and the human — that is where the review step earns its
  existence.
- Honest agent behaviour under failure: handed a wrong resource (a plant-breeder-rights
  table with no entities), the agent mapped **nothing** — all 10 columns unmapped with
  correct reasons, status NOT USEFUL (`outputs/runs/ipgod2022-wrong-resource-pbr/`).

## The hard one

**ipgod2022 (IP Australia design-party table).** One row = one party playing one role
(applicant, owner, *agent*, submitter) on one design right; the role column has no
ontology field; and the source asserts a *local subsidiary's* ABN on rows whose party
is a *foreign parent* (`country_code` us/ch in the raw rows). No mapping change can fix
either — row filtering is deliberately not expressible in the closed transform
catalogue. Our rule for "when is custom code the correct answer": when the fix
generalises across sources rather than patching one. So instead of a per-source parser
we upgraded the *matcher* (see Change below), which applies to every source. The
runner-up was the discount directory (no identifiers at all): at our evidence bar it
produced **zero accepted links** — all its name matches sit in the refused queue with
reasons. That is where we drew the line; the queue is the deliverable, not a failure.

## Scale: 6 → 500 sources

1. **Human review throughput breaks first.** Minutes per source × 500 is weeks of one
   reviewer; the fix is queueing by validation status, risk-based sampling, and batch
   approval of green runs — not removing the human.
2. **Reachability/anti-bot.** One of our six picks was browser-openable but rejected
   every scripted client; triage needs reachability probes before scoring.
3. **Resolution blocking and storage.** Name buckets grow superlinearly; JSONL files
   give way to a store with incremental runs and record-level diffs.
4. **Licence review** becomes a workflow of its own (we were lucky: everything here is
   CC-BY family, recorded per observation).

## Change — the model-upgrade question, performed live in this assignment

Every link records `matcher_version`, `run_id`, thresholds, evidence and timestamps;
observations are immutable; clusters are derived, versioned snapshots. That let us do
the upgrade for real: hand-checking 50 links measured **62% precision at
matcher-0.1** — all 19 false positives were one pattern (foreign parents carrying a
local ABN), *predicted in the reviewer's recorded approval note for that source*.
matcher-0.2 adds a country gate using country claims the observations already carried.
Procedure: archive v1 links → re-run → crosswalk (341 entities intact, 0 split, 13
shrunk or dissolved: 10 fully dissolved, 3 shrunk — the foreign-parent clusters) →
re-measure on the **same** labelled sample:
**19/19 false positives removed, 31/31 true links kept.** Rollback = pointing the
derivation at the archived v1 links. What you must have recorded in advance: per-link
matcher version + evidence + thresholds, immutable observations including fields you
did not think you needed (country), versioned cluster snapshots, and a labelled sample.

## Profile assembly (Part 4) in numbers

50 profiles from randomly sampled multi-source entities (no cherry-picking; seed in
code). Per field: winner + support count, two confidence factors shown separately,
provenance, and every losing value with the rule that beat it; `trading_name` is
multi-valued per the ontology; absent fields are absent keys. Each profile carries
`cluster_support` — the weakest link under it — because field confidence is
conditional on the linking being right. **Source-fragility experiment** (delete one of
six sources, re-resolve, rebuild): dropping the tax-transparency anchor splits or
dissolves **31 of 50** profiled entities, 19 survive, 1 of those changes a field value
(`outputs/drop-source-corporate-transparency.json`). The anchor source is a single
point of failure, which feeds the scale answer above.

## Entity relationships (Part 3 modelling)

Stored truth is a pairwise **same_as link table** (append-only; retraction records
rather than deletes). Entities are derived by union-find; name links may attach records
but never bridge two clusters holding different ABNs; fuzzy similarity never links —
it queues. `parent_of`-style relations are deliberately out of scope: columns stating
them are unmapped with that reason, and the extension is a typed-edge link table
(`same_as` clustered, `parent_of` stored but never merged). We chose links-as-truth
precisely because of the Change question above: conclusions (cluster ids) are cheap to
recompute; evidence is not.

## Next, with three weeks

1. A regression harness: golden configs, replay of onboarded sources per agent/prompt
   version, mapping-accuracy tracking — the evaluation layer this build lacks.
2. Engine gaps measured during use: envelope `valid_from`/`valid_to` (business-name
   registration dates, tax years), a row-filter config feature (ipgod roles),
   multi-column concatenation (ACNC address lines).
3. Review UI with batch queues; calibrate confidences against accumulated hand-check
   labels (today they are declared heuristics, and labelled as such).
4. ABR as a verification oracle at link time — it settled every dispute in our
   hand-check within seconds.
5. Storage and incremental refresh: observations/links to a database, per-source
   record diffs, licence tracking.

---

*Honesty appendix.* Part 1 false-positive rate: 35% verified (7/20), 45% counting two
unverifiable resources against ourselves. Looser-threshold linking (exact name without
state corroboration), 16 non-duplicate refused pairs hand-checked: 6 confirmed the
same business, 3 unsure, 7 distinct — refusing cost us at most 9 true links and
avoided at least 7 wrong ones. Sampling for the two large files was deliberately overlap-seeded
and is disclosed in the README; precision is measured, coverage is never claimed.
