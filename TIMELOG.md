# Time log

Time box: 6h total (360 min). Received 2026-10-16, due 2026-10-23.
Clock started: 2026-10-17 18:15 AEDT. Clock pauses on breaks; every segment is logged below.

## Plan (T+ = elapsed working time, not wall-clock)

| Node | T+ start → end | Budget | Done when | If over budget |
|---|---|---|---|---|
| 0 Design | 0:00 → 0:40 | 40m | Design approved, plan written | Freeze open questions as README assumptions |
| 1a Repo skeleton + token ledger | 0:40 → 0:50 | 10m | `uv run` works, every LLM call logged to ledger | — |
| 1b Part 1 fetch + score + shortlist | 0:50 → 1:10 | 20m | ≥200 records pulled, 50-row shortlist CSV | Drop state portals, data.gov.au only |
| 1c Part 1 hand-check 20 | 1:10 → 1:20 | 10m | FP rate recorded | — |
| 2a Readers (csv/tsv/xlsx/zip) + pick 6 sources | 1:20 → 1:40 | 20m | 6 sources downloaded, sampled | Swap any source that fights the reader |
| 2b Generic engine + transforms | 1:40 → 2:15 | 35m | Config → canonical observations w/ envelope | — |
| 2c Agent steps + approval CLI | 2:15 → 3:05 | 50m | Unseen source → config with no human edits | Cap revise loop, ship fewer steps |
| 2d Run 6 sources, approve, 1000 rows each | 3:05 → 3:30 | 25m | 6 configs + observations on disk | Ship ≥5, document the 6th |
| 3a Linking + unlinked queue | 3:30 → 4:05 | 35m | links.jsonl + unlinked.jsonl | ABN-exact only, name-match as "next" |
| 3b Hand-check 50 links | 4:05 → 4:25 | 20m | Precision @ threshold recorded | — |
| 4 Profiles (50) + drop-one-source | 4:25 → 5:00 | 35m | 50 profiles, per-field conf + provenance + conflicts | Skip ablation, describe it |
| 5a WRITEUP | 5:00 → 5:30 | 30m | ≤2 pages | — |
| 5b README + clean-checkout test | 5:30 → 5:45 | 15m | Fresh clone runs in <10 min | Document what's broken |
| Buffer | 5:45 → 6:00 | 15m | Only for fixing a broken README run | — |

Priority if squeezed: Part 2 (agentic + generalises) steals from Part 4, never the other way round.

## Segments

| # | Start (AEDT) | End | Minutes | Node | Notes |
|---|---|---|---|---|---|
| 1 | 2026-10-17 18:15 | 18:55 | 40 | 0 Design | Design discussion + DESIGN.md, with AI assistant (Claude Code). Includes a 2-subagent debate on the Part 3 link model |
| 2 | 2026-10-17 18:55 | 18:58 | 3 | 1a Skeleton | uv project, CLI stubs, OpenRouter client + cost ledger, smoke call |
| 3 | 2026-10-17 18:58 | 19:02 | 4 | 1b Triage | 840-dataset pool, shortlist of 50, hand-check sheet generated |
| 4 | 2026-10-17 19:02 | 19:09 | 7 | Design rev + 2a | External review feedback folded into DESIGN.md; readers.py (2 design proposals reconciled); source picks verified incl. overlap probe; readability refactor |
| 5 | 2026-10-17 19:09 | 19:18 | 9 | 2b Engine | transforms (14), validators (checksums verified independently), config schema, engine; 27 tests passing |
| 6 | 2026-10-17 19:18 | 19:29 | 11 | 1c Hand-check | data-level evidence for 20 datasets via script; verdicts reviewed by hand; FP 35% verified / 45% conservative |
| 7 | 2026-10-17 19:29 | 19:48 | 19 | 2c Agent | prompts (subagent draft), 9-node LangGraph, checkpoint resume, cross-process review gate; first real run caught a licence-status≠entity-status semantic trap; validator calibrated (pair coverage 95%, PASSING WITH FLAGS路由) |
| 8 | 2026-10-17 19:48 | 20:50 | 62 | 2d Reviews | 6 sources through the human gate: Monica rejected 4 mappings with comments (status/date semantics ×3, outlet names), approved 2 red-flag cases with recorded reasons; debate subagents per decision; post-hoc audits of 2 completed decisions; review pages as artifacts; review-gate hardening (--resource, --fresh, approve-with-reason) |
| 9 | 2026-10-17 20:50 | 21:20 | 30 | 3+4 Execute | extracts (ABN+name seeded sampling, sampler bug fixed to reuse config transforms), resolve (1,090 links, 354 multi-source entities, 0 conflicts), 50-link+20-queue hand-check page, 50 profiles with support counts, drop-source experiment (31/50 entities split without the anchor source) |
| 10 | 2026-10-17 21:20 | 21:35 | 15 | 3 Hand-check + matcher-0.2 | Three-way link verification (reviewer flags + independent judge + ABR register & raw country_code): matcher-0.1 precision 62% (19 FPs, all foreign parents carrying a local ABN — the pattern the ipgod approval note predicted). Reviewer-approved matcher upgrade: country gate + queue dedupe; all 19 labeled FPs removed, 31/31 true links kept, crosswalk 341 intact / 13 dissolved. Unseen 7th dataset approved (PASSING, 0 revisions) |
