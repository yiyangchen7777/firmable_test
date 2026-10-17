"""The closed catalogue of transforms a mapping config may reference.

Configs refer to these by NAME only — a config can never contain code.
A transform does one of three things:
- returns the cleaned value,
- returns None, meaning "no claim for this field on this row" (absence),
- raises TransformError, meaning "the value is broken" (no claim + quality flag).

A step in a config is either a plain name ("trim") or a one-key dict carrying
a parameter ({"keep_if_length": 11}, {"parse_date": "%d/%m/%Y"}).
None short-circuits: once a value becomes None, later steps are skipped.
"""

from datetime import datetime


class TransformError(Exception):
    """A value that should have been transformable was not."""


ALLOWED_TRANSFORMS = (
    "trim",
    "empty_to_null",
    "digits_only",
    "strip_float_suffix",
    "keep_if_length",
    "abn_normalize",
    "acn_normalize",
    "parse_date",
    "map_enum",
    "state_normalize",
    "postcode_normalize",
    "yn_to_bool",
    "url_normalize",
    "split",
)

STATE_ALIASES = {
    "nsw": "NSW", "new south wales": "NSW",
    "vic": "VIC", "victoria": "VIC",
    "qld": "QLD", "queensland": "QLD",
    "wa": "WA", "western australia": "WA",
    "sa": "SA", "south australia": "SA",
    "tas": "TAS", "tasmania": "TAS",
    "act": "ACT", "australian capital territory": "ACT",
    "nt": "NT", "northern territory": "NT",
    "nz": "NZ", "new zealand": "NZ",
}


def apply_transforms(value, steps):
    """Run a config's transform pipeline over one cell value, left to right."""
    for step in steps:
        if value is None:
            return None  # absence short-circuits the rest of the pipeline
        if isinstance(step, str):
            name = step
            param = None
        else:  # one-key dict like {"keep_if_length": 11}
            name = list(step.keys())[0]
            param = step[name]
        value = _apply_one(value, name, param)
    return value


def _apply_one(value, name: str, param):
    """One transform step. A plain if/elif chain — no dynamic dispatch."""
    if name == "trim":
        # split on any whitespace run, join with single spaces:
        # "   SILENT  SCISSORZ " -> "SILENT SCISSORZ"
        return " ".join(value.split())

    if name == "empty_to_null":
        if value.strip() == "":
            return None
        return value

    if name == "digits_only":
        digits = ""
        for ch in value:
            if ch.isdigit():
                digits += ch
        if digits == "":
            return None
        return digits

    if name == "strip_float_suffix":
        # IP Australia serialises ABNs as "34291651910.0"
        if value.endswith(".0"):
            return value[:-2]
        return value

    if name == "keep_if_length":
        # gate for mixed columns: wrong length means "not this field", not an error
        if len(value) == int(param):
            return value
        return None

    if name == "abn_normalize":
        digits = _apply_one(value, "digits_only", None)
        if digits is None or len(digits) != 11:
            raise TransformError(f"abn_wrong_length: {value!r}")
        # no zero-padding: a leading-zero ABN cannot pass the checksum,
        # so padding would manufacture garbage
        return digits

    if name == "acn_normalize":
        digits = _apply_one(value, "digits_only", None)
        if digits is None or len(digits) > 9:
            raise TransformError(f"acn_wrong_length: {value!r}")
        # Excel strips leading zeros and ACNs legitimately start with 0
        return digits.zfill(9)

    if name == "parse_date":
        # explicit format first (an agent decision, reviewable), then the two
        # shapes openpyxl/ISO produce. Tried in a fixed order — no guessing.
        formats = [param, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        for fmt in formats:
            if fmt is None:
                continue
            try:
                return datetime.strptime(value.strip(), fmt).date().isoformat()
            except ValueError:
                continue
        raise TransformError(f"date_parse_failed: {value!r}")

    if name == "map_enum":
        mapping = param["mapping"]
        lookup = {}
        for key, mapped in mapping.items():
            lookup[key.strip().lower()] = mapped
        found = lookup.get(value.strip().lower())
        if found is not None:
            return found
        if "default" in param:
            return param["default"]
        raise TransformError(f"enum_value_unmapped: {value!r}")

    if name == "state_normalize":
        found = STATE_ALIASES.get(value.strip().lower())
        if found is None:
            raise TransformError(f"state_unknown: {value!r}")
        return found

    if name == "postcode_normalize":
        digits = _apply_one(value, "digits_only", None)
        if digits is None or len(digits) > 4:
            raise TransformError(f"postcode_invalid: {value!r}")
        return digits.zfill(4)  # NT postcodes like 0800 lose their zero in Excel

    if name == "yn_to_bool":
        blank_is = False
        if isinstance(param, dict) and "blank_is" in param:
            blank_is = param["blank_is"]
        cleaned = value.strip().lower()
        if cleaned == "y":
            return True
        if cleaned == "":
            return blank_is
        if cleaned == "n":
            return False
        raise TransformError(f"yn_unexpected: {value!r}")

    if name == "url_normalize":
        cleaned = value.strip()
        if cleaned == "":
            return None
        if "://" not in cleaned:
            cleaned = "http://" + cleaned
        scheme, rest = cleaned.split("://", 1)
        if "/" in rest:
            host, path = rest.split("/", 1)
            return f"{scheme.lower()}://{host.lower()}/{path}"
        return f"{scheme.lower()}://{rest.lower()}"

    if name == "split":
        parts = []
        for piece in value.split(param):
            piece = piece.strip()
            if piece != "":
                parts.append(piece)
        if not parts:
            return None
        return parts  # the engine emits one claim per element

    raise TransformError(f"unknown_transform: {name}")
