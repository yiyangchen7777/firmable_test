"""Business-name normalisation, shared by the resolver and seeded sampling."""

# trailing legal-form tokens stripped when normalising a name for matching
SUFFIX_TOKENS = {
    "PTY", "LTD", "LIMITED", "PROPRIETARY", "P/L", "PTY.", "LTD.",
    "INC", "INC.", "INCORPORATED", "PLC", "NL", "CO", "CO.",
}


def name_key(name: str) -> str:
    """Normalise a business name for matching: upper-case, strip punctuation,
    collapse spaces, drop trailing legal-form tokens (PTY LTD etc.)."""
    cleaned = []
    for ch in name.upper():
        if ch.isalnum() or ch == " ":
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    tokens = "".join(cleaned).split()
    while tokens and tokens[-1] in SUFFIX_TOKENS:
        tokens.pop()
    return " ".join(tokens)
