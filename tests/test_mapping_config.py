"""Config-contract tests: numbers a model writes must be range-checked by code,
not trusted because the prompt asked nicely."""

from firm.mapping_config import MappingConfig, check_config


def base_config() -> dict:
    return {
        "source_id": "test-source",
        "dataset_id": "test-dataset",
        "resource_url": "http://example.invalid/data.csv",
        "licence": "cc-by",
        "source_reliability": {"value": 0.9, "rationale": "test"},
        "reader": {"format": "csv", "delimiter": ",", "header_row": 0},
        "record_id": {"strategy": "column", "columns": ["ID"]},
        "observed_at": {"strategy": "dataset_modified", "basis": "proxy", "value": "2026-10-01"},
        "fields": [
            {"canonical": "entity.legal_name", "source": "NAME",
             "transforms": ["trim"], "confidence": 0.95},
        ],
        "unmapped": [],
    }


def problems_for(**overrides) -> str:
    cfg_dict = base_config()
    cfg_dict.update(overrides)
    return "; ".join(check_config(MappingConfig(**cfg_dict)))


def test_valid_config_has_no_problems():
    assert problems_for() == ""


def test_source_reliability_must_be_a_probability():
    problems = problems_for(source_reliability={"value": 2.0, "rationale": "test"})
    assert "source_reliability" in problems


def test_field_confidence_must_be_a_probability():
    cfg_dict = base_config()
    cfg_dict["fields"][0]["confidence"] = 1.7
    problems = "; ".join(check_config(MappingConfig(**cfg_dict)))
    assert "confidence" in problems


def test_reliability_overrides_must_be_probabilities():
    problems = problems_for(reliability_overrides={"entity.legal_name": 1.5})
    assert "reliability_overrides" in problems


def test_observed_at_value_must_be_a_real_date():
    problems = problems_for(
        observed_at={"strategy": "dataset_modified", "basis": "proxy", "value": "not-a-date"}
    )
    assert "observed_at" in problems
