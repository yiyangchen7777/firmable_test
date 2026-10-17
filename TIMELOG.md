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
