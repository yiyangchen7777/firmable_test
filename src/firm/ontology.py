"""Read the assignment's ontology file once and answer questions about it."""

import yaml

from .config import ONTOLOGY_PATH

_cache: dict | None = None


def load() -> dict:
    global _cache
    if _cache is None:
        _cache = yaml.safe_load(ONTOLOGY_PATH.read_text())
    return _cache


def canonical_fields() -> dict[str, dict]:
    """All mappable fields, keyed 'entity.abn' / 'address.state' style."""
    ontology = load()
    fields = {}
    for group in ("entity", "address"):
        for name, spec in ontology[group].items():
            fields[f"{group}.{name}"] = spec
    return fields


def enum_values(canonical: str) -> list[str] | None:
    """The allowed values for an enum field, or None if it is not an enum."""
    spec = canonical_fields().get(canonical)
    if spec is None:
        return None
    if spec.get("type") == "enum":
        return spec["values"]
    return None


def date_fields() -> set[str]:
    """Canonical fields whose ontology type is date."""
    result = set()
    for name, spec in canonical_fields().items():
        if spec.get("type") == "date":
            result.add(name)
    return result
