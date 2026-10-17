"""Minimal CKAN Action API client for data.gov.au."""

import time

import httpx

from .config import USER_AGENT

BASE = "https://data.gov.au/data/api/3/action"


def api(action: str, *, retries: int = 2, **params) -> dict:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = httpx.get(
                f"{BASE}/{action}",
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=60,
            )
            resp.raise_for_status()
            body = resp.json()
            if not body.get("success"):
                raise RuntimeError(f"CKAN {action} returned success=false")
            return body["result"]
        except Exception as err:  # noqa: BLE001
            last_err = err
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"CKAN {action} failed after {retries + 1} attempts: {last_err}")


def package_search(query: str, rows: int = 100) -> list[dict]:
    return api("package_search", q=query, rows=rows)["results"]


def package_show(dataset_id: str) -> dict:
    return api("package_show", id=dataset_id)
