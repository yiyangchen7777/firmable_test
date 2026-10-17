"""Export each source's human-decision trail from the agent checkpoints.

The rejection comments and approval notes live in the LangGraph checkpoint
history (outputs/agent_checkpoints.sqlite), which is runtime state and not
committed. This script exports the reviewable part — every review-gate event
with its verbatim comment — to outputs/runs/<source>/decisions.json so the
trail ships with the repo.

Usage: uv run python scripts/export_decisions.py
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402

from firm.agent.graph import CHECKPOINT_DB, build_graph  # noqa: E402


def main() -> None:
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    app = build_graph().compile(checkpointer=SqliteSaver(conn))
    thread_ids = [row[0] for row in conn.execute(
        "SELECT DISTINCT thread_id FROM checkpoints"
    )]

    for thread_id in sorted(thread_ids):
        config = {"configurable": {"thread_id": thread_id}}
        snapshots = list(app.get_state_history(config))
        snapshots.reverse()  # oldest first

        events = []
        previous = {}
        for snap in snapshots:
            values = snap.values or {}
            decision = values.get("decision")
            comment = values.get("human_comment", "")
            note = values.get("approval_note", "")
            marker = (decision, comment, note)
            # a reject with no comment is a state echo (the comment is cleared
            # once revise consumes it), not a decision — skip it
            if decision == "reject" and comment == "":
                continue
            if decision and marker != previous:
                events.append(
                    {
                        "decision": decision,
                        "rejection_comment": comment if decision == "reject" else "",
                        "approval_note": note if decision == "approve" else "",
                        "status_at_decision": values.get("status", ""),
                        "revisions_used": values.get("revisions", 0),
                    }
                )
                previous = marker

        if not events:
            continue
        run_dir = ROOT / "outputs" / "runs" / thread_id
        run_dir.mkdir(parents=True, exist_ok=True)
        out = run_dir / "decisions.json"
        out.write_text(json.dumps({"source": thread_id, "review_events": events}, indent=2))
        print(f"{thread_id}: {len(events)} review event(s) → {out}")
    conn.close()


if __name__ == "__main__":
    main()
