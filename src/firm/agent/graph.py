"""The agent graph: fixed pipeline, checkpointed, with a human approval gate.

fetch_meta → inspect → profile → propose → validate ─┬─ review ─┬─ emit
                                          ▲          │          ├─ revise (reject)
                                          └─ revise ◄┘          └─ abandon
(validate → revise when checks fail or semantics look wrong, max 3 rounds)

Every node's completion is checkpointed to sqlite: a crash resumes from the
last finished node, and paid model calls are additionally cached on disk.
The human gate works across processes:

    firm onboard <dataset-id>                      # runs until review, then exits
    firm onboard <dataset-id> --decide "approve"   # resumes from the checkpoint
"""

import sqlite3
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from ..config import OUTPUTS
from . import nodes

CHECKPOINT_DB = OUTPUTS / "agent_checkpoints.sqlite"


class AgentState(TypedDict, total=False):
    """One channel per key; a node updates only the keys it returns."""

    dataset_id: str
    resource_hint: str | None
    meta: dict
    data_path: str
    reader: dict
    inspect_reasoning: str
    rows: list
    visible: list
    loop: list
    accept: list
    profiles: list
    config: dict
    decisions: dict
    revisions: int
    validation: dict
    spotcheck: dict
    suspicious: list
    status: str
    decision: str
    approval_note: str
    human_comment: str
    changes: list
    emitted: str
    steps: list


def after_validate(state: dict) -> str:
    # Hard-check failures loop back to the model (max 3 rounds). Semantic-only
    # flags (PASSING WITH FLAGS) go straight to the human, who can reject with
    # a comment if they agree with the flag.
    if state["status"] in ("PASSING", "PASSING WITH FLAGS"):
        return "review"
    if state["revisions"] >= nodes.MAX_REVISIONS:
        return "review"  # flagged NOT PASSING / NOT USEFUL; the human decides
    return "revise"


def after_review(state: dict) -> str:
    return state["decision"]  # "approve" → emit, "reject" → revise, "abandon"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("fetch_meta", nodes.fetch_meta)
    graph.add_node("inspect", nodes.inspect)
    graph.add_node("profile", nodes.profile)
    graph.add_node("propose", nodes.propose)
    graph.add_node("validate", nodes.validate)
    graph.add_node("revise", nodes.revise)
    graph.add_node("review", nodes.review)
    graph.add_node("emit", nodes.emit)
    graph.add_node("abandon", nodes.abandon)

    graph.add_edge(START, "fetch_meta")
    graph.add_edge("fetch_meta", "inspect")
    graph.add_edge("inspect", "profile")
    graph.add_edge("profile", "propose")
    graph.add_edge("propose", "validate")
    graph.add_conditional_edges("validate", after_validate, {"review": "review", "revise": "revise"})
    graph.add_edge("revise", "validate")
    graph.add_conditional_edges("review", after_review, {"approve": "emit", "reject": "revise", "abandon": "abandon"})
    graph.add_edge("emit", END)
    graph.add_edge("abandon", END)
    return graph


def run_onboard(
    dataset_id: str,
    decide: str | None = None,
    resource: str | None = None,
    fresh: bool = False,
) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    if fresh:  # throw away this dataset's previous run and start over
        for table in ("checkpoints", "writes"):
            try:
                conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (dataset_id,))
            except sqlite3.OperationalError:
                pass  # table does not exist yet
        conn.commit()
    saver = SqliteSaver(conn)
    app = build_graph().compile(checkpointer=saver)
    config = {"configurable": {"thread_id": dataset_id}}

    if decide is not None:
        graph_input = Command(resume=decide)
    else:
        snapshot = app.get_state(config)
        if snapshot is not None and snapshot.next:
            graph_input = None  # crashed mid-run: resume from the last checkpoint
            print(f"resuming {dataset_id} from checkpoint (next: {snapshot.next})")
        else:
            graph_input = {
                "dataset_id": dataset_id, "steps": [], "revisions": 0,
                "human_comment": "", "resource_hint": resource,
            }

    result = app.invoke(graph_input, config)

    if "__interrupt__" in result:
        info = result["__interrupt__"][0].value
        print()
        print(f"REVIEW NEEDED — status: {info['status']}")
        print(f"read: {info['review_path']}")
        print()
        print(f'then:  firm onboard {dataset_id} --decide "approve"')
        print(f'  or:  firm onboard {dataset_id} --decide "reject: <comment>"')
        print(f'  or:  firm onboard {dataset_id} --decide "abandon"')
    conn.close()
