"""Paths and environment. No secrets in code; OPENROUTER_API_KEY comes from .env or the env."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"
CONFIGS = ROOT / "configs"
RUNS = OUTPUTS / "runs"
RAW = ROOT / "data" / "raw"
ONTOLOGY_PATH = ROOT / "ontology" / "firmable_ontology.yaml"
LEDGER_PATH = OUTPUTS / "ledger.jsonl"

DEFAULT_MODEL = os.environ.get("FIRM_MODEL", "anthropic/claude-sonnet-5.5")
USER_AGENT = "firmable-takehome/0.1"


def load_env() -> None:
    """Load KEY=value lines from .env if present. Existing env vars win."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def openrouter_key() -> str:
    load_env()
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set (put it in .env)")
    return key
