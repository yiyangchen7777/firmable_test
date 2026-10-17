"""OpenRouter client with a cost ledger and a response cache.

Every model call goes through `complete()`:
- it appends one line to outputs/ledger.jsonl (step, model, tokens, cost as
  reported by OpenRouter, wall-clock). The WRITEUP's cost numbers come from
  this file, not from estimates.
- it caches each response on disk, keyed by a hash of the prompt. If the
  process crashes after an API call was paid for, the rerun reads the cache
  instead of paying again.
"""

import hashlib
import json
import time
from datetime import datetime, timezone

from openai import OpenAI

from .config import CACHE, DEFAULT_MODEL, LEDGER_PATH, openrouter_key

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
    """One chat completion: cache check, call with retries, ledger, cache write."""
    cache_key = hashlib.sha256(f"{model}\n{system}\n{user}".encode()).hexdigest()[:32]
    cache_file = CACHE / f"{cache_key}.json"
    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        print(f"[llm] cache hit for step={step} (no API cost)")
        return cached["content"]

    last_err: Exception | None = None
    resp = None
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
            break  # success — leave the retry loop
        except Exception as err:  # network errors, rate limits, 5xx
            last_err = err
            if attempt < retries:
                print(f"[llm] attempt {attempt + 1} failed ({err}); retrying")
                time.sleep(2 * (attempt + 1))
    if resp is None:
        raise RuntimeError(
            f"model call failed after {retries + 1} attempts: {last_err}"
        ) from last_err

    # From here on the call has succeeded and been paid for. Nothing below may
    # trigger a re-call, so logging and checks happen outside the retry loop.
    usage = resp.usage
    cost = getattr(usage, "cost", None)  # OpenRouter adds `cost` as an extra field
    if not cost:  # deliberately catches both None and 0.0
        extra = getattr(usage, "model_extra", None) or {}
        cost = extra.get("cost")

    row = {
        "step": step,
        "source": source,
        "model": resp.model or model,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "cost_usd": cost,
        "duration_s": round(time.monotonic() - t0, 2),
    }
    _log(row)

    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError(f"model returned an empty completion at step={step}")

    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"step": step, "content": content}))
    return content


def _log(row: dict) -> None:
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

        prompt_tokens = row.get("prompt_tokens")
        if prompt_tokens is None:  # the ledger stores null when usage was missing
            prompt_tokens = 0
        totals["prompt_tokens"] += prompt_tokens

        completion_tokens = row.get("completion_tokens")
        if completion_tokens is None:
            completion_tokens = 0
        totals["completion_tokens"] += completion_tokens

        cost = row.get("cost_usd")
        if cost is None:
            cost = 0.0
        totals["cost_usd"] += cost

    totals["cost_usd"] = round(totals["cost_usd"], 4)
    return totals
