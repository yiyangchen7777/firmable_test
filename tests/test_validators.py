"""Checksum and validity tests. Vectors verified independently before coding."""

from firm.validators import valid_abn, valid_acn, valid_date, valid_enum


def test_valid_abns():
    assert valid_abn("51824753556")  # ATO's published example
    assert valid_abn("53004085616")  # BHP
    assert valid_abn("34291651910")


def test_invalid_abns():
    assert not valid_abn("51824753557")  # one digit off
    assert not valid_abn("12345678901")
    assert not valid_abn("5182475355")  # 10 digits
    assert not valid_abn("5182475355a")


def test_valid_acns():
    assert valid_acn("000000019")  # ASIC's published example
    assert valid_acn("004085616")
    assert valid_acn("010499966")


def test_invalid_acns():
    assert not valid_acn("000000018")
    assert not valid_acn("123456789")
    assert not valid_acn("00000001")  # 8 digits


def test_valid_date():
    assert valid_date("2010-07-01")
    assert not valid_date("2021-02-31")  # not a real day
    assert not valid_date("01/07/2010")  # not ISO


def test_valid_enum():
    assert valid_enum("VIC", ["NSW", "VIC"])
    assert not valid_enum("Vic", ["NSW", "VIC"])  # case matters after normalisation
