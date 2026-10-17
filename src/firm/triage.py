"""Part 1 — deterministic triage of data.gov.au datasets.

Deliberately not agentic: the assignment allows cheap deterministic filtering
ahead of any model call at this stage, and with ~600 catalogue records the
signals below (identifier vocabulary, publisher, format, register-vs-statistics
wording) separate the pool well without spending tokens. The agentic
requirement applies to Part 2.
"""

import csv
import json
import random
import re

from .ckan import package_search
from .config import OUTPUTS, ROOT

QUERIES = [
    "abn",
    "business register",
    "business names",
    "licensee",
    "licence holders",
    "registered charities",
    "company register",
    "building approvals company",
    "trade licence",
    "procurement contracts supplier",
]

# Signals: (points, label, regex) applied to title+notes lowercase.
POSITIVE = [
    (3.0, "mentions ABN/ACN", re.compile(r"\babn\b|\bacn\b|australian business number|australian company number")),
    (2.0, "register/licence vocabulary", re.compile(r"\bregister(ed)?\b|\blicen[cs]e[esd]?\b|\blicensee|\bpermit|\baccredit")),
    (1.5, "business/company/charity vocabulary", re.compile(r"\bbusiness(es)?\b|\bcompan(y|ies)\b|\bcharit(y|ies)\b|\bsupplier|\bcontractor")),
]
NEGATIVE = [
    (-3.0, "aggregate statistics wording", re.compile(r"\bstatistics\b|\bstatistical\b|\baggregate|\bsummary\b|\bcensus\b|\bsurvey\b|\bcounts?\b|\btrends?\b|number of business")),
    (-1.5, "spatial/boundary data", re.compile(r"\bboundar(y|ies)\b|\bzoning\b|\bgeospatial\b|\bshapefile\b")),
]
REGULATOR = re.compile(r"\basic\b|taxation|\bato\b|\bacnc\b|fair trading|consumer|business.?licen|attorney|treasury|regulator", re.I)
MACHINE_FORMATS = {"CSV", "TSV", "XLSX", "XLS", "JSON", "ZIP"}


def score_package(pkg: dict) -> tuple[float, str]:
    text = f"{pkg.get('title', '')} {pkg.get('notes', '')}".lower()
    org = (pkg.get("organization") or {}).get("title", "")
    formats = {(r.get("format") or "").upper().replace("EXCEL (.XLSX)", "XLSX") for r in pkg.get("resources", [])}

    score, reasons = 0.0, []
    for points, label, rx in POSITIVE + NEGATIVE:
        if rx.search(text):
            score += points
            reasons.append(label)
    if REGULATOR.search(org):
        score += 2.0
        reasons.append(f"regulator publisher ({org})")
    if formats & MACHINE_FORMATS:
        score += 1.0
        reasons.append("machine-readable format")
    else:
        score -= 2.0
        reasons.append("no machine-readable resource")
    return score, "; ".join(reasons) or "no signals"


def confidence(score: float) -> float:
    """Map score (observed range roughly [-5, 9.5]) to [0, 1]. Linear, clipped."""
    return round(min(1.0, max(0.0, (score + 5) / 14.5)), 2)


def run_triage(sample_seed: int = 42) -> None:
    pool: dict[str, dict] = {}
    for q in QUERIES:
        for pkg in package_search(q, rows=100):
            pool[pkg["id"]] = pkg
    print(f"pool: {len(pool)} unique datasets from {len(QUERIES)} queries")
    assert len(pool) >= 200, "assignment requires a pool of at least 200 records"

    scored = []
    for pkg in pool.values():
        s, reason = score_package(pkg)
        formats = sorted({(r.get("format") or "?").upper() for r in pkg.get("resources", [])})
        scored.append(
            {
                "dataset_id": pkg["name"],
                "title": pkg.get("title", ""),
                "organisation": (pkg.get("organization") or {}).get("title", ""),
                "formats": "|".join(formats),
                "licence": pkg.get("license_id") or "unknown",
                "score": round(s, 1),
                "confidence": confidence(s),
                "reason": reason,
            }
        )
    scored.sort(key=lambda r: (-r["score"], r["dataset_id"]))
    top50 = scored[:50]

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUTS / "shortlist.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(top50[0].keys()))
        writer.writeheader()
        writer.writerows(top50)
    (OUTPUTS / "triage_pool.jsonl").write_text(
        "\n".join(json.dumps(r) for r in scored) + "\n"
    )

    # Random 20 of the 50 for the human false-positive check.
    review_dir = ROOT / "review"
    review_dir.mkdir(exist_ok=True)
    sample = random.Random(sample_seed).sample(top50, 20)
    with (review_dir / "part1_handcheck.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["dataset_id", "title", "organisation", "confidence", "reason", "contains_business_entities", "note"]
        )
        writer.writeheader()
        for row in sample:
            writer.writerow({k: row[k] for k in ("dataset_id", "title", "organisation", "confidence", "reason")} | {"contains_business_entities": "", "note": ""})

    print(f"shortlist: {out_csv} (50 rows); hand-check sheet: review/part1_handcheck.csv (20 rows, seed={sample_seed})")
