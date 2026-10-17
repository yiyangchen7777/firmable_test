"""Deterministic validity checks. Transforms clean values; validators judge them.

Used by the engine after transforms (a failed check suppresses the claim and
records a quality flag) and by the agent's validate node to score a proposed
mapping on held-out rows.
"""

from datetime import datetime

ABN_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
ACN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 1]


def valid_abn(value: str) -> bool:
    """ABN checksum: subtract 1 from the first digit, weight, sum % 89 == 0."""
    if len(value) != 11 or not value.isdigit():
        return False
    digits = []
    for ch in value:
        digits.append(int(ch))
    digits[0] -= 1
    total = 0
    for weight, digit in zip(ABN_WEIGHTS, digits):
        total += weight * digit
    return total % 89 == 0


def valid_acn(value: str) -> bool:
    """ACN checksum: weight the first 8 digits, complement of sum % 10 is digit 9."""
    if len(value) != 9 or not value.isdigit():
        return False
    total = 0
    for weight, ch in zip(ACN_WEIGHTS, value[:8]):
        total += weight * int(ch)
    expected = (10 - total % 10) % 10
    return expected == int(value[8])


def valid_enum(value: str, allowed: list[str]) -> bool:
    return value in allowed


def valid_date(value: str) -> bool:
    """ISO YYYY-MM-DD and a real calendar date (catches 2021-02-31)."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False
