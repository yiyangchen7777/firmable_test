# WRITEUP raw material (working notes, not the deliverable)

Collected findings to draw on when writing WRITEUP.md. Each item is evidenced
in the repo (runs/, review/, ledger, git history).

## Agent design — what actually happened

- Fixed 9-node LangGraph; models propose (inspect/propose/spot-check/revise),
  code checks (checksums, enums, null drift, uniqueness — engine-level, so no
  config can bypass them), a human approves. Checkpoints + an LLM response
  cache make paid calls idempotent; `--decide` resumes across processes.
- The semantic spot-check caught the same trap in 4 of 6 sources: the status /
  date of a REGISTRATION (licence, business name, charity status, IP right)
  mapped onto the ENTITY's status/date. Parse rates were 100% in every case —
  only the meaning was wrong. This is the single highest-value validation step;
  we know because removing it would have let 4 wrong mappings through.
- Human review loop demonstrably worked: entity.status (credit licensee)
  rejected by the reviewer → agent moved it to unmapped with the reviewer's
  reason recorded in the emitted config. Approving a non-green status requires
  a recorded reason (ipgod duplicates case).
- Review workflow for a non-domain-expert reviewer: per-field semantic
  evidence quoting samples; system pre-chews doubts; independent debate agents
  argue both sides; deterministic verification settles factual disputes
  (an auditor's claim that url_normalize corrupted a value was DISPROVEN by
  checking the raw CSV — the double scheme `http://https://` is in the source).
  Reviewer's safe default: don't approve what you can't verify.
- Agent honesty under a no-entity table: handed the wrong resource
  (pbr-application.csv, plant breeder rights, no entity columns), the agent
  mapped NOTHING — 10/10 columns unmapped with correct reasons, status NOT
  USEFUL. Evidence: outputs/runs/ipgod2022-wrong-resource-pbr/.

## Validator calibration (threshold judgment calls, each evidenced)

- Conditional pair coverage 98%→95%: ~4% of the mixed ABN/ACN column is source
  junk ("0", 7-8 digit fragments); abstaining is correct, abstentions listed.
- record_id uniqueness zero→rate ≤0.5%: literal full-row duplicates exist in
  real sources (ipgod: 9 duplicate ids in the 1,000-row extract = 0.9%, per
  extract_log.json; the review-time "1.71%" in the approval note came from a
  since-fixed denominator bug and is kept verbatim as a historical record);
  the engine suffixes (#N) + flags them.
- Semantic-only flags route to the human (PASSING WITH FLAGS) instead of the
  revise loop: a flag the closed catalogue cannot fix (street text inside a
  locality cell) would loop the model pointlessly.

## Engine gaps found by use (the honest limitations list)

1. No envelope valid_from/valid_to mapping: BN_REG_DT/BN_CANCEL_DT (business
   names) and Income year (tax transparency) are exactly that material.
2. No row filter: ipgod party_role (agent/submitter rows) cannot be filtered
   or mapped; Part 3 must treat that source's legal_name at its 0.65
   confidence. Pseudonymised individuals (iNNNNNN) noted.
3. No multi-column concatenation: ACNC Address_Line_2/3 stay unmapped;
   address.full is line 1 only.
4. One sheet per config: corporate-transparency's PRRT details sheet was seen
   by inspect and deliberately skipped, but nothing recorded that — an
   undeclared silent drop (fixed by noting here; proper fix is a second
   onboarding for that sheet).
5. observed_at basis=proxy uses the catalogue modified date; the discount
   directory's filename carries a better timestamp the schema can't express.

## Audit outcomes (post-hoc subagent audits of completed decisions)

- asic-credit-licensee: both human decisions upheld (high confidence). Open
  question "is the checksum in the transform chain?" answered: it is enforced
  at the ENGINE level on every claim, by design — AI proposes, code gates.
- corporate-transparency: upheld (medium). record_id ['Name'] is single-year
  safe but ['Name','Income year'] is the zero-cost robust choice; reopened or
  WRITEUP-noted per reviewer's call.

## Part 1 numbers

- Pool 840, shortlist 50 (deterministic scorer, reasons logged).
- Hand-check 20: 11 verified contain business entities; 7 verified not (35%);
  2 unverifiable (dead/blocked resources). Conservative FP = 45% (9/20).
- Scorer weaknesses found: register/licence vocabulary pulls in price
  statistics and API doc pages; dead links not probed at triage time
  (improvement: a reachability HEAD check).
- One dataset (VIC school ABNs) is browser-openable but blocks scripted
  clients (TLS fingerprinting) — at 500-source scale, anti-bot infrastructure
  is one of the first things that breaks.

## Entity-resolution notes for Parts 3-5

- Charities ∩ tax transparency = 0 (charities are tax-exempt) — measured, not
  assumed. Random 1000-row samples of big files share ~0 entities with other
  sources (expected overlap <1); overlap-seeded sampling is REQUIRED and its
  bias documented (precision measured, coverage never claimed).
- Trusts are the fuzzy entity boundary: trustee-named licensees whose ACN
  belongs to the corporate trustee; "TRUSTEES OF X FAMILY TRUST" rows.
- Relationship columns (parent/subsidiary etc.): unmapped with reason;
  typed edges (same_as vs parent_of) described in write-up, only same_as used
  for clustering.

## Cost discipline

- Separate budgets: assistant (personal subscription) vs runtime API (personal
  OpenRouter key, $10-capped child key created via provisioning API).
- Ledger (outputs/ledger.jsonl) records per-call step/model/tokens/cost;
  OpenRouter usage accounting is the receipt. Runtime model:
  anthropic/claude-sonnet-5.5 for all four node types.
- Validator-calibration reruns were nearly free thanks to the response cache
  (only changed prompts re-bill).
