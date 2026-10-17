"""Engine tests: a fixture config over a tiny in-memory table, no network."""

from firm.engine import extract_rows
from firm.mapping_config import MappingConfig

FIXTURE_CONFIG = {
    "source_id": "test-source",
    "dataset_id": "test-dataset",
    "resource_url": "http://example.invalid/data.csv",
    "licence": "cc-by",
    "source_reliability": {"value": 0.9, "rationale": "test"},
    "reader": {"format": "csv", "delimiter": ",", "header_row": 0},
    "record_id": {"strategy": "composite", "columns": ["LIC_NUM", "START_DT"]},
    "observed_at": {"strategy": "dataset_modified", "basis": "proxy", "value": "2026-10-01"},
    "fields": [
        {
            "canonical": "entity.legal_name",
            "source": "NAME",
            "transforms": ["trim", "empty_to_null"],
            "confidence": 0.95,
        },
        {
            "canonical": "entity.abn",
            "source": "ABN_ACN",
            "transforms": ["digits_only", {"keep_if_length": 11}, "abn_normalize"],
            "confidence": 0.9,
            "conditional": True,
        },
        {
            "canonical": "entity.acn",
            "source": "ABN_ACN",
            "transforms": ["digits_only", {"keep_if_length": 9}, "acn_normalize"],
            "confidence": 0.9,
            "conditional": True,
        },
        {
            "canonical": "address.state",
            "source": "STATE",
            "transforms": ["empty_to_null", "state_normalize"],
            "confidence": 0.95,
        },
    ],
    "unmapped": [{"source": "FEE", "reason": "no ontology field"}],
}

ROWS = [
    # valid ABN in the mixed column
    {"LIC_NUM": "L1", "START_DT": "2020-01-01", "NAME": " Alpha Pty Ltd ", "ABN_ACN": "51 824 753 556", "STATE": "Vic", "FEE": "10"},
    # valid ACN in the mixed column
    {"LIC_NUM": "L2", "START_DT": "2020-01-02", "NAME": "Beta Ltd", "ABN_ACN": "004085616", "STATE": "NSW", "FEE": "20"},
    # ABN fails its checksum: claim suppressed, flag recorded
    {"LIC_NUM": "L3", "START_DT": "2020-01-03", "NAME": "Gamma", "ABN_ACN": "51824753557", "STATE": "", "FEE": "30"},
    # duplicate composite key with L1
    {"LIC_NUM": "L1", "START_DT": "2020-01-01", "NAME": "Alpha Pty Ltd", "ABN_ACN": "", "STATE": "Vic", "FEE": "40"},
    # empty id component
    {"LIC_NUM": "", "START_DT": "2020-01-05", "NAME": "Delta", "ABN_ACN": "", "STATE": "Queensland", "FEE": "50"},
]


def run():
    cfg = MappingConfig(**FIXTURE_CONFIG)
    return extract_rows(ROWS, cfg, "cfg-test+engine-0.1", "2026-10-17T12:00:00+00:00")


def claims_of(obs, field):
    return [c for c in obs["claims"] if c["field"] == field]


def flags_of(obs, flag_name):
    return [f for f in obs["quality_flags"] if f["flag"] == flag_name]


def test_mixed_column_yields_at_most_one_identifier():
    obs = run()
    assert claims_of(obs[0], "entity.abn")[0]["value"] == "51824753556"
    assert claims_of(obs[0], "entity.acn") == []
    assert claims_of(obs[1], "entity.acn")[0]["value"] == "004085616"
    assert claims_of(obs[1], "entity.abn") == []


def test_bad_checksum_suppressed_and_flagged():
    obs = run()
    assert claims_of(obs[2], "entity.abn") == []
    assert len(flags_of(obs[2], "abn_checksum_failed")) == 1
    # the raw value is preserved in the flag for debugging
    assert flags_of(obs[2], "abn_checksum_failed")[0]["raw"] == "51824753557"


def test_duplicate_record_id_gets_suffix():
    obs = run()
    assert obs[0]["source_record_id"] == "L1|2020-01-01"
    assert obs[3]["source_record_id"] == "L1|2020-01-01#2"
    assert len(flags_of(obs[3], "duplicate_record_id")) == 1


def test_empty_id_component_kept_and_flagged():
    obs = run()
    assert obs[4]["source_record_id"] == "|2020-01-05"
    assert len(flags_of(obs[4], "record_id_component_empty")) == 1


def test_envelope_and_raw():
    obs = run()
    assert obs[0]["observed_at"] == "2026-10-01"
    assert obs[0]["observed_at_basis"] == "proxy"
    assert obs[0]["licence"] == "cc-by"
    # raw keeps the original cell before transforms
    assert claims_of(obs[0], "entity.abn")[0]["raw"] == "51 824 753 556"
    assert claims_of(obs[0], "entity.legal_name")[0]["value"] == "Alpha Pty Ltd"


def test_state_normalised_and_empty_absent():
    obs = run()
    assert claims_of(obs[0], "address.state")[0]["value"] == "VIC"
    assert claims_of(obs[4], "address.state")[0]["value"] == "QLD"
    # empty state on row 3: no claim and no flag (absence is not an error)
    assert claims_of(obs[2], "address.state") == []


def test_determinism():
    assert run() == run()


def test_record_id_suffix_never_collides_with_a_real_id():
    # raw ids K, K, K#2: the suffix given to the second K must not collide
    # with the row whose real id is already K#2
    cfg = MappingConfig(**{**FIXTURE_CONFIG, "record_id": {"strategy": "column", "columns": ["LIC_NUM"]}})
    rows = [
        {"LIC_NUM": "K", "START_DT": "", "NAME": "One", "ABN_ACN": "", "STATE": "", "FEE": ""},
        {"LIC_NUM": "K", "START_DT": "", "NAME": "Two", "ABN_ACN": "", "STATE": "", "FEE": ""},
        {"LIC_NUM": "K#2", "START_DT": "", "NAME": "Three", "ABN_ACN": "", "STATE": "", "FEE": ""},
    ]
    obs = extract_rows(rows, cfg, "cfg-test", "1970-01-01T00:00:00+00:00")
    ids = [o["source_record_id"] for o in obs]
    assert len(set(ids)) == 3, ids


def test_non_text_cell_is_flagged_never_claimed():
    # the readers stringify every cell, but extract_rows is a public function:
    # a non-string cell (here a bool) must become a flag, not a claim
    cfg = MappingConfig(**FIXTURE_CONFIG)
    rows = [{"LIC_NUM": "L9", "START_DT": "2020-01-01", "NAME": True,
             "ABN_ACN": "", "STATE": "", "FEE": ""}]
    obs = extract_rows(rows, cfg, "cfg-test", "1970-01-01T00:00:00+00:00")
    assert claims_of(obs[0], "entity.legal_name") == []
    assert any(f["flag"] == "cell_not_text" for f in obs[0]["quality_flags"])
