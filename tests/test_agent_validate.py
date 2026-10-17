"""Agent-node tests that need no network and no model.

These cover the two deterministic paths every new source walks through before
a human sees it: the validation report (code checks over extracted rows) and
the emit gate (what may, and may not, land in configs/).
"""

from firm.agent import graph, nodes
from firm.engine import extract_rows
from firm.mapping_config import MappingConfig


def make_config() -> dict:
    return {
        "source_id": "test-agent-source",
        "dataset_id": "test-agent-source",
        "resource_url": "http://example.invalid/data.csv",
        "licence": "cc-by",
        "source_reliability": {"value": 0.9, "rationale": "test"},
        "reader": {"format": "csv", "delimiter": ",", "header_row": 0},
        "record_id": {"strategy": "column", "columns": ["ID"]},
        "observed_at": {"strategy": "dataset_modified", "basis": "proxy", "value": "2026-10-01"},
        "fields": [
            {"canonical": "entity.legal_name", "source": "NAME",
             "transforms": ["trim", "empty_to_null"], "confidence": 0.95},
            {"canonical": "entity.abn", "source": "ABN",
             "transforms": ["digits_only", "abn_normalize"], "confidence": 0.9},
        ],
        "unmapped": [],
    }


GOOD_ROWS = [
    {"ID": "1", "NAME": "Alpha Pty Ltd", "ABN": "51824753556"},
    {"ID": "2", "NAME": "Beta Ltd", "ABN": "53004085616"},
]
BAD_ABN_ROWS = [  # every ABN fails its checksum, so acceptance cannot pass
    {"ID": "1", "NAME": "Alpha Pty Ltd", "ABN": "51824753557"},
    {"ID": "2", "NAME": "Beta Ltd", "ABN": "53004085617"},
]


def report_for(rows):
    cfg = MappingConfig(**make_config())
    obs = extract_rows(rows, cfg, "cfg-test", nodes.FIXED_TS)
    return nodes.build_validation_report(obs, rows, cfg, duplicate_ids=0)


def test_validation_report_runs_on_unconditional_mappings():
    # regression: build_validation_report used apply_transforms/TransformError
    # without importing them, so any non-conditional mapping crashed the node
    report = report_for(GOOD_ROWS)
    assert report["all_pass"]
    assert any("null drift" in c["check"] for c in report["checks"])


def test_validation_report_fails_on_broken_identifiers():
    assert not report_for(BAD_ABN_ROWS)["all_pass"]


def emit_state(rows, approval_note=""):
    return {
        "config": make_config(),
        "accept": rows,
        "revisions": 0,
        "status": "PASSING",
        "approval_note": approval_note,
        "steps": ["review"],
    }


def point_dirs_at(monkeypatch, tmp_path):
    monkeypatch.setattr(nodes, "CONFIGS", tmp_path / "configs")
    monkeypatch.setattr(nodes, "RUNS", tmp_path / "runs")


def test_emit_publishes_when_acceptance_passes(monkeypatch, tmp_path):
    point_dirs_at(monkeypatch, tmp_path)
    out = nodes.emit(emit_state(GOOD_ROWS))
    assert (tmp_path / "configs" / "test-agent-source.yaml").exists()
    assert out["emitted"] != ""


def test_emit_withholds_config_when_acceptance_fails(monkeypatch, tmp_path):
    # the 150 unseen rows are the one check the reviewer never saw; failing it
    # must keep the config out of configs/, not print a warning and publish
    point_dirs_at(monkeypatch, tmp_path)
    out = nodes.emit(emit_state(BAD_ABN_ROWS))
    assert not (tmp_path / "configs" / "test-agent-source.yaml").exists()
    assert (tmp_path / "runs" / "test-agent-source" / "config.candidate.yaml").exists()
    assert out["emitted"] == ""


def test_emit_failed_acceptance_publishes_only_with_written_exception(monkeypatch, tmp_path):
    point_dirs_at(monkeypatch, tmp_path)
    nodes.emit(emit_state(BAD_ABN_ROWS, approval_note="source rows are literal duplicates"))
    path = tmp_path / "configs" / "test-agent-source.yaml"
    assert path.exists()
    assert "source rows are literal duplicates" in path.read_text()


def test_graph_routes_withheld_emit_back_to_review():
    assert graph.after_emit({"emitted": ""}) == "review"
    assert graph.after_emit({"emitted": "/somewhere/x.yaml"}) == "end"
