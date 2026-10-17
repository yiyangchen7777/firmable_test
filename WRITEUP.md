# WRITEUP

## Cost — actuals from `outputs/ledger.jsonl`, not estimates

- Runtime API total: **USD $2.91** (62 calls, 533k prompt / 184k completion tokens,
  `anthropic/claude-sonnet-5.5` via a personal OpenRouter key; every call logged with
  step, source, tokens, billed cost).
- **One-time inference per source**: steady state **$0.13–0.55** (table below). The
  first source cost $0.83 because validator calibration changed prompts and re-billed;
  a disk response cache makes unchanged steps free.
- **Per-record cost: $0** — extraction is deterministic. Two oversized sources
  seeded-sampled at 1,000 rows, one 66k-row source head-sampled at 1,000, the rest in
  full → 19,542 observations.
- Not counted, on purpose: the coding assistant that *built* the system (personal
  subscription). The $10 budget governs runtime spend.

## Agent design

- Fixed 9-node LangGraph: fetch → inspect(model) → profile(code) → propose(model) →
  validate(code + model semantic spot-check) → revise(model, ≤3) → review(human) →
  emit. State carried between nodes and checkpointed after each: reader decision,
  200/350/150 row split, column profiles, config draft, validation report with failing
  examples, revision count, the human's comment.
- **Models propose, code gates, a human approves.** Checksums, enums, dates, per-entry
  null drift and record-id uniqueness run engine-side — no config bypasses them. The
  150 acceptance rows run once after approval; a failure withholds the config and
  returns the run to review unless the approval carried a written exception.
- **Onboarding one source, measured** (steps = graph nodes incl. the human gate;
  model time from the ledger; downloads and the engine excluded):

  | source | steps | revisions | LLM calls | tokens | model time | cost |
  |---|---|---|---|---|---|---|
  | credit-licensee (first, incl. calibration) | 10 | 1 | 14 | 199k | 5.2 min | $0.83 |
  | corporate-transparency (xlsx) | 10 | 1 | 5 | 29k | 0.9 min | $0.13 |
  | acnc-register (69 cols) | 10 | 1 | 6 | 147k | 3.1 min | $0.55 |
  | business-names (mislabelled tsv) | 10 | 1 | 6 | 47k | 1.3 min | $0.20 |
  | discount-directory (no ids) | 10 | 1 | 9 | 95k | 3.0 min | $0.43 |
  | ipgod2022 (hard source) | 13 | 3 | 15 | 119k | 3.6 min | $0.51 |
  | afs-licensee (unseen; same-publisher sibling, weak evidence) | 7 | 0 | 3 | 59k | 0.7 min | $0.18 |
  | **r&d-tax-incentive (unseen, non-ASIC, final code)** | **7** | **0** | **3** | **18k** | **0.5 min** | **$0.07** |

- **A run fails without losing the job** in layers: transport retries per call; one
  JSON-repair retry per model step; inspect retried once with its parse error; ≤3
  validate→revise rounds fed the failing examples; crashes resume from the last
  checkpoint; a prompt-keyed cache means a resume never re-pays a completed call.
- The human sees, per source: each mapping with semantic evidence (column name +
  samples + why it means that field), validation vs thresholds, spot-check verdicts,
  unmapped columns with reasons, five raw-vs-canonical record pairs. Actions:
  approve / reject-with-comment / abandon — comments go verbatim to revise; **the
  human never edits a config**. Five of seven runs were rejected once; the verbatim
  trail is in `outputs/runs/<source>/decisions.json`. **One round-trip of five:** the
  first proposal mapped `CRED_LIC_STATUS` (`APPR`) to `entity.status`; reviewer:
  *"APPR describes the licence approval, not the company's existence — unmap it with
  that reason."* The revise node obeyed; nobody touched the YAML.
- **Weakest step, how we know:** propose's semantic layer — four of six first
  proposals mapped a *registration's* status/date onto the *entity*, at ~100% parse
  rates; only the spot-check plus the reviewer caught them. Handed a no-entity table
  (wrong resource), the agent honestly mapped nothing — NOT USEFUL, 10/10 columns
  unmapped with reasons (`outputs/runs/ipgod2022-wrong-resource-pbr/`).

## The hard one

**ipgod2022** (one row = one party-role on a design right): the role column has no
ontology field, and the source asserts a local subsidiary's ABN on *foreign parents'*
rows (`country_code` us/ch). No mapping change fixes either — row filtering is
deliberately outside the closed catalogue. Our rule for when custom code is correct:
when the fix generalises across sources — so we upgraded the matcher (below), not a
parser. Runner-up: the discount directory (no identifiers) produced **zero accepted
links** at our evidence bar; its name matches sit in the refused queue with reasons.
The queue is the deliverable, not a failure.

## Scale: 6 → 500

1. **Human review throughput** breaks first; queue by validation status, risk-sample,
   batch-approve green runs — don't remove the human.
2. **Reachability/anti-bot** (one shortlisted source rejects every scripted client).
3. **Blocking and storage**: name buckets grow superlinearly; JSONL → a store with
   incremental runs; row_hash record ids are snapshot-scoped, so refreshes need their
   own versioning.
4. **Licence review** becomes a workflow (all six here CC-BY family, recorded per
   observation).

## Change — the model-upgrade question, performed live

Every link records `matcher_version`, `run_id`, threshold, evidence, timestamps, and
the `canonical_entity_key` it currently derives to; observations are immutable;
clusters are versioned snapshots. **Thresholds used:** ABN equality (both checksums
valid) 0.98; ACN equality 0.95; exact normalised name + same state 0.75; fuzzy
similarity 85–100 is queued, never linked. Hand-checking 50 links measured **62%
precision at matcher-0.1** — all 19 false positives one pattern: foreign parents
carrying a local ABN. The reviewer's approval note for that source had flagged its
identity columns as weak (legal_name capped at 0.65; agent-row ABNs noted) but
**neither agent nor reviewer anticipated the foreign-parent mechanism — the hand-check
caught it**. Earlier commit messages say "predicted"; this sentence is the correction.
matcher-0.2 adds a country gate from country claims the observations already carried. Procedure: archive v1 → re-run → crosswalk (341 entities intact, 0 split, 13
shrunk or dissolved) → re-measure on the same labels: **19/19 FPs removed, 31/31 true
links kept** (in-sample), then a **fresh entity-stratified sample of 30 shipped links:
30/30 correct — Wilson 95% lower bound 88.7%** (one link drawn per entity, so this is
per-entity precision; a large cluster contributes one draw, not its 45 links). Honesty notes: across runs this build
regenerates files and keeps versions as archives (`outputs/history/`) — retraction
records are designed, not exercised; version labels (`matcher-0.2`, `engine-0.1`) were
hand-bumped during the exercise and lag some code changes — production would stamp the
code SHA and prompt hash instead; ABN-seeded sampling enriches exactly the
foreign-parent region, so 62% describes the seeded overlap, not the corpus. Recorded
in advance, which made this possible: per-link version + evidence + thresholds,
immutable observations including fields we didn't know we needed (country), versioned
snapshots, a labelled sample. Rollback = derive from the archived v1 links.

## Profile assembly (Part 4)

50 profiles from randomly sampled multi-source entities (seed in code). Per field:
winner + support count, both confidence factors shown separately (heuristics, bounded
by the measured precision), provenance, every losing value with the rule that beat it;
majority counts distinct sources before rows; `trading_name` is multi-valued; absent
fields are absent keys; each profile carries `cluster_support`. **Drop-one-source:**
removing the tax-transparency anchor splits or dissolves **31/50** entities, 19
survive, 1 changes a field value — a single point of failure, with the caveat that
seeded sampling made it the hub of the sampled graph.

## Entity relationships

Pairwise **same_as** link table as stored truth; entities derived by union-find; no
link of any tier may bridge two clusters holding different ABNs; fuzzy never links —
it queues. `parent_of` deliberately untouched: such columns are unmapped with that
reason; the extension is typed edges (`same_as` clustered, `parent_of` stored, never
merged). Structural admission: every shipped link is identifier-tier — the name tier
never fired, since 498 of its 509 candidate pairs involve sources that map no state at
all. This build demonstrates identifier-join plus refusal discipline; the name tier's
value is its queue. Links-as-truth because conclusions (cluster ids) are cheap to
recompute; evidence is not.

## Next, with three weeks

1. Regression harness: golden configs, replay per agent/prompt version, mapping
   accuracy over time.
2. Engine gaps measured in use: envelope `valid_from`/`valid_to`, row filters,
   multi-column concat, country-aware postcode validation, refresh-stable record ids.
3. Review UI with batch queues; calibrate confidences against accumulated labels.
4. ABR as a link-time verification oracle (it settled every hand-check dispute).
5. Observations/links into a database; incremental refresh; licence tracking.

---

*Honesty appendix.* Hand-check protocol, a finding in itself: in both rounds the
reviewer's name-dissimilarity flags were largely overturned by register evidence —
Australia's business-name system makes "the names look unrelated" misleading in *both*
directions — so every verdict was adjudicated against the ABR / primary registers.
Part 1 FP rate: 35% verified (7/20), 45% counting two unverifiable resources against
ourselves. Looser-threshold linking, 16 non-duplicate refused pairs: 6 same, 3 unsure,
7 distinct — refusing cost at most 9 true links, avoided at least 7 wrong ones. Seeded
sampling disclosed in the README; precision is measured, coverage never claimed.
