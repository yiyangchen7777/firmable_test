"""Unit tests for the reader layer (no network)."""

from pathlib import Path

from firm.readers import clean_header, read_rows


def test_clean_header_blanks_and_duplicates():
    cells = ["Name", "", "Name", None, " State "]
    assert clean_header(cells) == ["Name", "col_1", "Name_2", "col_3", "State"]


def test_clean_header_dedup_never_collides_with_a_real_column():
    # A, A, A_2: the suffix given to the duplicate A must not collide with the
    # real column already named A_2 (a collision silently drops a column)
    header = clean_header(["A", "A", "A_2"])
    assert len(set(header)) == 3, header


def test_read_delimited_with_junk_preamble_and_ragged_rows(tmp_path: Path):
    f = tmp_path / "sample.csv"
    f.write_text(
        "This file was generated on 2026-10-01\n"  # junk line above the header
        "ABN\tName\tState\n"
        "51824753556\tExample Charity Ltd\tVIC\n"
        "99999999999\tShort Row\n"  # one cell missing → padded with ""
        "12345678901\tExtra Cells\tNSW\tbonus\n"  # extra cell → dropped
    )
    cfg = {"format": "tsv", "delimiter": "\t", "header_row": 1}
    rows = read_rows(f, cfg, limit=10)
    assert len(rows) == 3
    assert rows[0] == {"ABN": "51824753556", "Name": "Example Charity Ltd", "State": "VIC"}
    assert rows[1]["State"] == ""  # padded
    assert "bonus" not in rows[2].values()  # dropped


def test_read_delimited_respects_limit(tmp_path: Path):
    f = tmp_path / "big.csv"
    lines = ["id,name"]
    for i in range(100):
        lines.append(f"{i},Business {i}")
    f.write_text("\n".join(lines))
    cfg = {"format": "csv", "delimiter": ",", "header_row": 0}
    rows = read_rows(f, cfg, limit=7)
    assert len(rows) == 7
    assert rows[6]["name"] == "Business 6"
