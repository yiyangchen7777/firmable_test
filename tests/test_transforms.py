import pytest

from firm.transforms import TransformError, apply_transforms


def test_trim_collapses_inner_whitespace():
    assert apply_transforms("   SILENT  SCISSORZ ", ["trim"]) == "SILENT SCISSORZ"


def test_strip_float_suffix():
    assert apply_transforms("34291651910.0", ["strip_float_suffix"]) == "34291651910"


def test_mixed_column_gates():
    # the same cell mapped twice: 11 digits survive the ABN gate, not the ACN gate
    abn_pipe = ["trim", "digits_only", {"keep_if_length": 11}, "abn_normalize"]
    acn_pipe = ["trim", "digits_only", {"keep_if_length": 9}, "acn_normalize"]
    assert apply_transforms("80 005 443 292", abn_pipe) == "80005443292"
    assert apply_transforms("80 005 443 292", acn_pipe) is None
    assert apply_transforms("004085616", acn_pipe) == "004085616"
    assert apply_transforms("004085616", abn_pipe) is None


def test_acn_zero_pad():
    assert apply_transforms("4085616", ["acn_normalize"]) == "004085616"


def test_parse_date_explicit_then_openpyxl_shape():
    step = [{"parse_date": "%d/%m/%Y"}]
    assert apply_transforms("01/07/2010", step) == "2010-07-01"
    # openpyxl stringifies Excel dates like this; same pipeline must cope
    assert apply_transforms("2021-05-03 00:00:00", step) == "2021-05-03"
    with pytest.raises(TransformError):
        apply_transforms("not a date", step)


def test_map_enum_case_insensitive_and_default():
    step = [{"map_enum": {"mapping": {"Current": "active", "Ceased": "deregistered"}}}]
    assert apply_transforms("CURRENT", step) == "active"
    with pytest.raises(TransformError):
        apply_transforms("Mystery", step)
    with_default = [{"map_enum": {"mapping": {"Current": "active"}, "default": "unknown"}}]
    assert apply_transforms("Mystery", with_default) == "unknown"


def test_state_normalize():
    assert apply_transforms("Vic", ["state_normalize"]) == "VIC"
    assert apply_transforms("Victoria", ["state_normalize"]) == "VIC"
    with pytest.raises(TransformError):
        apply_transforms("Mars", ["state_normalize"])


def test_postcode_pad():
    assert apply_transforms("800", ["postcode_normalize"]) == "0800"


def test_yn_to_bool():
    assert apply_transforms("Y", ["yn_to_bool"]) is True
    assert apply_transforms("", ["yn_to_bool"]) is False


def test_split_emits_list():
    assert apply_transforms("A; B ;; C", [{"split": ";"}]) == ["A", "B", "C"]


def test_null_short_circuits():
    # empty_to_null makes the value None; later steps must be skipped, not crash
    assert apply_transforms("  ", ["empty_to_null", "abn_normalize"]) is None
