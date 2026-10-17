"""Fresh, entity-stratified precision sample for the shipped matcher.

Samples 30 accepted links from outputs/links.jsonl — at most one link per
derived entity, excluding every pair already labelled in the first hand-check —
pre-fetches the ABR register's testimony for each link's ABN, and renders one
verdict page. Measures matcher-0.2 on data no one has labelled before.

Usage: uv run python scripts/fresh_sample.py
"""

import csv
import html
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SAMPLE_SIZE = 30
SEED = 2026


def esc(v) -> str:
    return html.escape(str(v))


def abr_testimony(abn: str) -> dict:
    """Entity holder + registered business names from the ABR public page."""
    url = f"https://abr.business.gov.au/ABN/View?id={abn}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/130.0"})
    page = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", errors="replace")
    entity = re.search(r'itemprop="legalName">([^<]+)<', page)
    business_names = re.findall(r"searchIdType=BUSN[^>]*>\s*([^<]+?)\s*<img", page)
    return {
        "entity": entity.group(1).strip() if entity else "?",
        "business_names": [re.sub(r"\s+", " ", b).strip() for b in business_names],
    }


def main() -> None:
    already = set()
    with (ROOT / "review" / "part3_handcheck.csv").open() as fh:
        for row in csv.DictReader(fh):
            already.add(tuple(sorted([row["record_a"], row["record_b"]])))

    links = [json.loads(l) for l in (ROOT / "outputs" / "links.jsonl").read_text().splitlines()]
    clusters = json.loads((ROOT / "outputs" / "clusters.json").read_text())["clusters"]
    entity_of = {}
    for c in clusters:
        for m in c["members"]:
            entity_of[m] = c["entity_id"]

    # one candidate link per entity, excluding already-labelled pairs
    per_entity: dict[str, dict] = {}
    for link in sorted(links, key=lambda l: (l["record_a"], l["record_b"])):
        pair = tuple(sorted([link["record_a"], link["record_b"]]))
        if pair in already:
            continue
        entity = entity_of.get(link["record_a"], link["record_a"])
        per_entity.setdefault(entity, link)
    sample = random.Random(SEED).sample(
        sorted(per_entity.values(), key=lambda l: l["record_a"]),
        min(SAMPLE_SIZE, len(per_entity)),
    )

    from firm.resolve import load_records
    records = load_records()

    rows_html, csv_rows = [], []
    for i, link in enumerate(sample, 1):
        a, b = records[link["record_a"]], records[link["record_b"]]
        abn = a["abn"] or b["abn"] or ""
        testimony = {"entity": "(no ABN)", "business_names": []}
        if abn:
            try:
                testimony = abr_testimony(abn)
                time.sleep(0.8)
            except Exception as err:  # keep the page usable if ABR hiccups
                testimony = {"entity": f"ABR fetch failed: {err}", "business_names": []}

        def cell(d):
            names = "<br>".join(esc(n) for n in d["names"]) or "<em>no names</em>"
            place = " ".join(p for p in (d["state"], d["country"] or "") if p)
            return (f"<div class='rec'><span class='src'>{esc(d['source'])}</span>"
                    f"<strong>{names}</strong><span class='meta'>ABN {esc(d['abn'] or '-')}"
                    f"{(' · ' + esc(place)) if place else ''}</span></div>")

        bn_list = ", ".join(esc(n) for n in testimony["business_names"][:6]) or "—"
        rows_html.append(
            f"<tr><td class='num'>{i}</td><td>{cell(a)}</td><td>{cell(b)}</td>"
            f"<td><strong>{esc(testimony['entity'])}</strong>"
            f"<br><span class='meta'>注册商号: {bn_list}</span></td></tr>"
        )
        csv_rows.append({"record_a": link["record_a"], "record_b": link["record_b"],
                         "link_confidence": link["link_confidence"], "evidence": link["evidence"],
                         "abr_entity": testimony["entity"],
                         "abr_business_names": "|".join(testimony["business_names"]),
                         "correct": "", "note": ""})

    out_csv = ROOT / "review" / "part3_fresh_handcheck.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    page = f"""<title>新样本精确率核对</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg:#f7f7f5; --panel:#fff; --fg:#1d2129; --muted:#6b7280; --line:#e3e4e0; --accent:#1f6f54; --code-bg:#f0f0ed; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#15171b; --panel:#1d2026; --fg:#e8e8e4; --muted:#9aa1ab; --line:#31353c; --accent:#5cbf97; --code-bg:#272b31; color-scheme:dark; }} }}
:root[data-theme="dark"] {{ --bg:#15171b; --panel:#1d2026; --fg:#e8e8e4; --muted:#9aa1ab; --line:#31353c; --accent:#5cbf97; --code-bg:#272b31; color-scheme:dark; }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.55 -apple-system,"Segoe UI","PingFang SC",sans-serif;
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); padding-block:28px 64px; }}
main {{ max-width:1060px; margin:0 auto; display:grid; gap:22px; }}
h1 {{ font-size:1.35rem; margin:0; }}
section {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px 20px; }}
table {{ border-collapse:collapse; width:100%; font-size:0.87rem; }}
th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; }}
.num {{ color:var(--muted); font-variant-numeric:tabular-nums; }}
.rec {{ display:grid; gap:2px; min-width:0; }}
.src {{ font-size:0.72rem; color:var(--accent); text-transform:uppercase; letter-spacing:0.03em; }}
.meta {{ font-size:0.78rem; color:var(--muted); }}
.tablewrap {{ overflow-x:auto; }}
</style>
<main>
<h1>matcher-0.2 全新样本核对 · 30 条</h1>
<section>
<p>按实体分层的全新抽样（每个实体最多一条链接，排除所有已标注过的对）。<strong>第四列是 ABR 登记册的证词</strong>：这个 ABN 的法定持有人和它名下的注册商号。判定规则：左右两条记录的名字，能在第四列（持有人名或商号列表）里找到归属 → 同一家（y）；对不上 → n。<strong>默认全 y，只回「第 X 条 n/不确定」。</strong></p>
<div class="tablewrap"><table>
<tr><th>#</th><th>记录 A</th><th>记录 B</th><th>ABR 登记册证词</th></tr>
{"".join(rows_html)}
</table></div>
</section>
</main>
"""
    out_html = ROOT / "review" / "part3_fresh_handcheck.html"
    out_html.write_text(page)
    print(f"wrote {out_csv} and {out_html} ({len(csv_rows)} links)")


if __name__ == "__main__":
    main()
