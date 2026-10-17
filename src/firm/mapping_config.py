"""The mapping-config contract: what the agent writes, what the engine reads.

Flat pydantic models (no clever validators) plus one load function that does
the cross-checks in plain code, so every rule is a readable if-statement.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

from . import ontology, validators
from .transforms import ALLOWED_TRANSFORMS


class SourceReliability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: float
    rationale: str


class ReaderCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")
    format: Literal["csv", "tsv", "xlsx"]
    encoding: str = "utf-8-sig"
    delimiter: str | None = None
    header_row: int = 0
    sheet: str | None = None


class RecordIdCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: Literal["column", "composite", "row_hash"]
    columns: list[str] = []


class ObservedAtCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: Literal["column", "dataset_modified"]
    basis: Literal["record", "proxy"]
    column: str | None = None
    format: str | None = None
    # For strategy=dataset_modified the emit step freezes the catalogue's
    # modified date in here, because the engine itself never touches the network.
    value: str | None = None


class FieldMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canonical: str
    source: str
    transforms: list[str | dict] = []
    confidence: float
    evidence: str = ""
    # True when this mapping intentionally yields no claim on many rows
    # (e.g. a mixed ABN/ACN column gated by keep_if_length). The validate
    # node then checks the pair jointly instead of flagging the null rate.
    conditional: bool = False


class UnmappedEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    reason: str


class MappingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    dataset_id: str
    resource_url: str
    licence: str
    source_reliability: SourceReliability
    reliability_overrides: dict[str, float] = {}
    reader: ReaderCfg
    record_id: RecordIdCfg
    observed_at: ObservedAtCfg
    fields: list[FieldMap]
    unmapped: list[UnmappedEntry] = []


def check_config(cfg: MappingConfig) -> list[str]:
    """Cross-checks pydantic can't express as plain types. Returns problems."""
    problems = []
    known_fields = ontology.canonical_fields()

    # every number the model wrote is a probability — enforced here, not asked
    # for in the prompt
    if not 0.0 <= cfg.source_reliability.value <= 1.0:
        problems.append(f"source_reliability.value must be 0..1, got {cfg.source_reliability.value}")
    for field, value in cfg.reliability_overrides.items():
        if not 0.0 <= value <= 1.0:
            problems.append(f"reliability_overrides[{field}] must be 0..1, got {value}")

    for entry in cfg.fields:
        if entry.canonical not in known_fields:
            problems.append(f"unknown canonical field: {entry.canonical}")
        if not 0.0 <= entry.confidence <= 1.0:
            problems.append(f"confidence must be 0..1, got {entry.confidence} (field {entry.canonical})")
        for step in entry.transforms:
            if isinstance(step, str):
                name = step
            else:
                name = list(step.keys())[0]
            if name not in ALLOWED_TRANSFORMS:
                problems.append(f"unknown transform: {name} (field {entry.canonical})")

    if cfg.reader.format in ("csv", "tsv") and cfg.reader.delimiter is None:
        problems.append("reader.delimiter is required for csv/tsv")
    if cfg.reader.format == "xlsx" and cfg.reader.sheet is None:
        problems.append("reader.sheet is required for xlsx")

    if cfg.record_id.strategy in ("column", "composite") and not cfg.record_id.columns:
        problems.append("record_id.columns required for column/composite strategy")

    if cfg.observed_at.strategy == "dataset_modified" and cfg.observed_at.value is None:
        problems.append("observed_at.value required when strategy=dataset_modified")
    if cfg.observed_at.value is not None and not validators.valid_date(cfg.observed_at.value):
        problems.append(f"observed_at.value must be an ISO date (YYYY-MM-DD), got {cfg.observed_at.value!r}")
    if cfg.observed_at.strategy == "column" and cfg.observed_at.column is None:
        problems.append("observed_at.column required when strategy=column")

    return problems


def load_config(path: Path) -> MappingConfig:
    """Load and fully check a mapping config; raise with every problem listed."""
    cfg = MappingConfig(**yaml.safe_load(path.read_text()))
    problems = check_config(cfg)
    if problems:
        raise ValueError(f"invalid mapping config {path.name}: " + "; ".join(problems))
    return cfg
