"""Part 1 hand-check helper: pull real rows from each sampled dataset.

For each of the 20 datasets in review/part1_handcheck.csv this script downloads
a machine-readable resource, reads the header and a few rows, and prints the
evidence a human needs to judge: does one row describe one identifiable
business/organisation?

The script gathers evidence; the verdict is recorded by a person in the CSV.
Run: uv run python scripts/handcheck_part1.py
"""

import csv
import io
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from firm.ckan import package_show  # noqa: E402
from firm.config import USER_AGENT  # noqa: E402

MAX_XLSX_BYTES = 30 * 1024 * 1024
PREFERRED = ["CSV", "TSV", "XLSX"]

# column-name words that suggest one row = one organisation
NAME_WORDS = ["name", "organisation", "organization", "charity", "entity", "company", "contractor", "licensee"]
ID_WORDS = ["abn", "acn", "licence", "license", "lic_num"]


def pick_resource(resources: list[dict]) -> dict | None:
    for wanted in PREFERRED:
        for res in resources:
            fmt = (res.get("format") or "").upper().replace("EXCEL (.XLSX)", "XLSX")
            if fmt == wanted:
                return res
    return None


def fetch_csv_head(url: str) -> list[list[str]]:
    """First ~100KB of a delimited file → up to 4 parsed rows."""
    headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-100000"}
    resp = httpx.get(url, headers=headers, timeout=60, follow_redirects=True)
    resp.raise_for_status()
    text = resp.content.decode("utf-8-sig", errors="replace")
    # try comma first, then tab (some "CSV" files are tab-separated)
    for delimiter in [",", "\t"]:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        if rows and len(rows[0]) > 1:
            return rows[:4]
    return rows[:4]


def fetch_xlsx_head(url: str) -> list[list[str]]:
    """Download an xlsx (size-capped) → first 4 rows of its largest sheet."""
    import openpyxl

    resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True)
    resp.raise_for_status()
    if len(resp.content) > MAX_XLSX_BYTES:
        raise RuntimeError(f"xlsx too big to fetch here ({len(resp.content)} bytes)")
    wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True)
    best_rows: list[list[str]] = []
    for sheet_name in wb.sheetnames:
        rows = []
        for row in wb[sheet_name].iter_rows(values_only=True):
            cells = []
            for cell in row:
                cells.append("" if cell is None else str(cell))
            rows.append(cells)
            if len(rows) >= 4:
                break
        # prefer the sheet with the widest header (preamble sheets are narrow)
        if rows and len(rows[0]) > (len(best_rows[0]) if best_rows else 0):
            best_rows = rows
    wb.close()
    return best_rows


def signals(header: list[str]) -> str:
    found = []
    lowered = [h.lower() for h in header]
    for word in NAME_WORDS + ID_WORDS:
        for col in lowered:
            if word in col:
                found.append(f"{word}→{col}")
                break
    return ", ".join(found) if found else "none"


def main() -> None:
    out_lines = ["# Part 1 hand-check evidence", ""]
    with (ROOT / "review" / "part1_handcheck.csv").open() as fh:
        sampled = list(csv.DictReader(fh))

    for i, row in enumerate(sampled, 1):
        dataset_id = row["dataset_id"]
        out_lines.append(f"## {i}. {row['title']}")
        try:
            pkg = package_show(dataset_id)
            res = pick_resource(pkg.get("resources", []))
            if res is None:
                fmts = [r.get("format") for r in pkg.get("resources", [])]
                out_lines.append(f"- no machine-readable resource (formats: {fmts})")
                out_lines.append("")
                continue
            fmt = (res.get("format") or "").upper().replace("EXCEL (.XLSX)", "XLSX")
            if fmt == "XLSX":
                rows = fetch_xlsx_head(res["url"])
            else:
                rows = fetch_csv_head(res["url"])
            if not rows:
                out_lines.append("- resource downloaded but no rows parsed")
                out_lines.append("")
                continue
            header = rows[0]
            out_lines.append(f"- resource: {fmt}, {res['url']}")
            out_lines.append(f"- columns ({len(header)}): {header[:12]}")
            for sample in rows[1:3]:
                out_lines.append(f"- sample row: {[c[:30] for c in sample[:8]]}")
            out_lines.append(f"- entity signals: {signals(header)}")
        except Exception as err:  # keep going: an unreachable resource is a finding
            out_lines.append(f"- FETCH FAILED: {err}")
        out_lines.append("")

    out_path = ROOT / "review" / "part1_evidence.md"
    out_path.write_text("\n".join(out_lines))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
