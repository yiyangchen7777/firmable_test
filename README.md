# Schema Inference and Entity Identification at Scale

Take-home submission. A multi-step agent onboards unseen data.gov.au sources by
inspecting them, proposing a mapping to the canonical ontology, validating its own
proposal on held-out rows, revising, and asking a human to approve. One generic engine
reads the approved configs and emits canonical observations; a resolver links entities
across sources with measured precision; profiles merge what the sources say, conflicts
shown. **Every mapping config in `configs/` was written by the agent, not by hand** —
the headers record revisions used and the human reviewer's decisions.

## Run it (clean checkout, under 10 minutes)

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). An OpenRouter key is needed
only for `onboard` (the agent); every other command is deterministic and free.

```bash
uv sync                                   # ~1 min
echo 'OPENROUTER_API_KEY=sk-or-...' > .env   # only needed for `onboard`
uv run pytest -q                          # 50 tests, <1 s

uv run firm triage                        # Part 1: pool 840 → shortlist 50 (network: ~10 CKAN queries, ~1 min)
uv run firm extract asic-credit-licensee --limit 4400   # Part 2: engine (downloads ~7MB)
uv run firm resolve                       # Part 3: links + refusals + clusters
uv run firm profile                       # Part 4: 50 profiles
uv run firm profile --drop-source corporate-transparency  # fragility experiment
```

The committed `outputs/` are the real run's artefacts; the commands above reproduce
them. Re-running rewrites the output files under a fresh `run_id` and timestamps, so
expect a large byte-level git diff whose *numbers* match the committed ones (781 links,
839 refusals, 344 clusters, 50 profiles). (`extract` on the two big sources downloads 69–248MB; all downloads cache under
`data/raw/`.)

To watch the agent onboard a source it has never seen (costs ~$0.20, stops for your
approval):

```bash
uv run firm onboard <dataset-id-from-shortlist>
# read outputs/runs/<id>/review.md, then:
uv run firm onboard <dataset-id> --decide "approve"          # or "reject: <why>" / "abandon"
```

## What is where

| Path | What |
|---|---|
| `outputs/shortlist.csv` | Part 1: 50 ranked datasets (pool of 840) |
| `review/part1_handcheck.csv` + `part1_evidence.md` | 20-dataset hand-check: FP 35% verified / 45% conservative |
| `configs/*.yaml` | Part 2: 7 agent-written mapping configs (6 sources + unseen demo) |
| `outputs/runs/<src>/` | per-source agent runs: review.md, acceptance.json, logs — including one failed/abandoned run kept as evidence |
| `outputs/observations/*.jsonl` | canonical observations (envelope + claims), 19.5k records |
| `outputs/links.jsonl`, `outputs/unlinked.jsonl`, `outputs/clusters.json` | Part 3: 781 accepted links, 839 refusals with reasons, 344 derived multi-source entities (matcher-0.2) |
| `outputs/history/`, `outputs/crosswalk.json` | the matcher-0.1 → 0.2 upgrade: archived links, cluster crosswalk |
| `review/part3_handcheck.csv`, `part3_queue_sample.csv` | 50 links + 20 refusals hand-checked: **62% precision at matcher-0.1; the 19 FPs removed by 0.2 with all 31 true links kept** |
| `outputs/profiles.jsonl`, `outputs/drop-source-*.json` | Part 4: 50 profiles (per-field confidence, provenance, conflicts with support counts) + drop-one-source report |
| `outputs/ledger.jsonl` | every model call: step, tokens, cost. Total **$2.83** |
| `WRITEUP.md`, `docs/DESIGN.md`, `docs/WRITEUP_NOTES.md` | the write-up, the pre-implementation design, raw findings |
| `TIMELOG.md` | how the 6-hour budget was actually spent, segment by segment |

## Decisions worth knowing before reading the code

- **Proof of agency.** `asic-afs-licensee` was onboarded after development froze, as an
  unseen seventh dataset: first proposal PASSING, 0 revisions, 0 human edits, $0.18.
  The demo deliberately stops at config emission — its observations are kept out of
  Part 3 so the measured link numbers stay frozen.
- **Sampling bias, disclosed.** Random 1,000-row samples of the two large files would
  share ~0 businesses with the other sources (measured). Sampling is therefore seeded:
  half head rows, half rows whose ABN appears in another source (or whose name matches
  the one source that has no identifiers). Precision is measured on what we linked;
  coverage is never claimed.
- **Conservative numbers.** Unverifiable datasets count as false positives; refused
  name matches stay refused (≈6/16 of them were real matches — we accept that recall
  cost); confidences are labelled heuristics, calibrated only by the hand-checks.
- **The engine knows no source.** Everything source-specific lives in agent-written
  YAML; configs reference a closed catalogue of named transforms and cannot contain
  code. Checksums and enum/date/uniqueness gates run engine-side on every claim.
- **Human review is the product.** `review.md` per run is the canonical review
  document; `scripts/review_page.py` renders it as a local HTML page for the reviewer
  (not committed). Decisions are CLI resumes against sqlite checkpoints; rejecting feeds the
  comment to the agent's revise node; humans never edit configs. A failed final
  acceptance (the 150 unseen rows) withholds the config and returns the run to
  review — publishing anyway needs the same written exception as any non-green
  approval. Five of seven
  onboarding runs were rejected once; the verbatim decision trail per source is in
  `outputs/runs/<source>/decisions.json`.

## Licences of the six sources

| Source | Licence |
|---|---|
| ASIC credit licensee / business names | CC-BY 3.0 AU (`cc-by`) |
| ACNC charity register | CC-BY |
| ATO corporate tax transparency | CC-BY |
| QLD business discount directory | CC-BY 4.0 |
| IP Australia IPGOD 2022 | CC-BY 2.5 AU |

Licence is recorded on every observation's envelope; one shortlisted dataset with no
clear licence would be recorded as `unknown` and flagged (none of the six needed it).

## AI use

Built with Claude (coding assistant, personal subscription) — commits carry
co-authorship trailers. The runtime agent calls `anthropic/claude-sonnet-5.5` through a
personal OpenRouter key; `outputs/ledger.jsonl` is the receipt. Design decisions,
review verdicts and the write-up were human-approved at recorded gates; subagent
debates and audits informed several reviewer decisions and are reflected in
`docs/WRITEUP_NOTES.md`. Every line of code is explained on request.

## Known issues

- `brew`-style system deps: none; but the first `uv sync` downloads Python 3.12 if absent.
- The VIC schools dataset in the shortlist is browser-only (anti-bot); recorded as
  unverifiable in the Part 1 hand-check rather than worked around.
- Engine gaps found during use (envelope validity dates, row filters, multi-column
  concat) are documented in `WRITEUP.md` → *Next*.
