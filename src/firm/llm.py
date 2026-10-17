"""OpenRouter client with a cost ledger.

Every model call goes through `complete()`, which appends one line to
outputs/ledger.jsonl: step, model, tokens, cost (as reported by OpenRouter),
wall-clock duration. The WRITEUP's cost numbers are produced from this file,
not estimated after the fact.
"""

import json
import time
from datetime import datetime, timezone

from openai import OpenAI

from .config import DEFAULT_MODEL, LEDGER_PATH, openrouter_key

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key(),
        )
    return _client


def complete(
    step: str,
    system: str,
    user: str,
    *,
    source: str = "-",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8000,
    retries: int = 2,
) -> str:
    """One chat completion. Logs to the ledger; retries transient failures."""
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        t0 = time.monotonic()
        try:
            resp = client().chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                extra_body={"usage": {"include": True}},
            )
            usage = resp.usage
            cost = None
            if usage is not None:
                # OpenRouter returns the actual charge when usage accounting is on.
                cost = getattr(usage, "cost", None) or (
                    getattr(usage, "model_extra", None) or {}
                ).get("cost")
            _log(
                step=step,
                source=source,
                model=resp.model or model,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                cost_usd=cost,
                duration_s=round(time.monotonic() - t0, 2),
                attempt=attempt,
            )
            content = resp.choices[0].message.content
            if not content:
                raise RuntimeError("empty completion")
            return content
        except Exception as err:  # noqa: BLE001 - retry anything transient, then surface
            last_err = err
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"model call failed after {retries + 1} attempts: {last_err}")


def _log(**row) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    row["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LEDGER_PATH.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def ledger_totals() -> dict:
    """Sum tokens and cost across the ledger (for the WRITEUP)."""
    totals = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
    if not LEDGER_PATH.exists():
        return totals
    for line in LEDGER_PATH.read_text().splitlines():
        row = json.loads(line)
        totals["calls"] += 1
        totals["prompt_tokens"] += row.get("prompt_tokens") or 0
        totals["completion_tokens"] += row.get("completion_tokens") or 0
        totals["cost_usd"] += row.get("cost_usd") or 0.0
    totals["cost_usd"] = round(totals["cost_usd"], 4)
    return totals
