"""Render the Part 3 hand-check as one HTML page.

Two tables: the 50 sampled ACCEPTED links (measures precision at our
thresholds) and 20 sampled REFUSED exact-name pairs from the queue (measures
what precision would be at a looser threshold — the assignment explicitly
invites this number). Verdicts are recorded back into the CSVs by hand.

Usage: uv run python scripts/part3_handcheck_page.py
"""

import csv
import html
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

QUEUE_SAMPLE_SIZE = 20
QUEUE_SEED = 123


def esc(value) -> str:
    return html.escape(str(value))


def load_record_details() -> dict[str, dict]:
    """key → readable summary built straight from the observations."""
    details: dict[str, dict] = {}
    for path in sorted((ROOT / "outputs" / "observations").glob("*.jsonl")):
        for line in path.read_text().splitlines():
            obs = json.loads(line)
            key = f"{obs['source_id']}::{obs['source_record_id']}"
            d = {"source": obs["source_id"], "names": [], "abn": "", "acn": "",
                 "state": "", "locality": "", "postcode": ""}
            for claim in obs["claims"]:
                field = claim["field"]
                if field in ("entity.legal_name", "entity.trading_name"):
                    if claim["value"] not in d["names"]:
                        d["names"].append(claim["value"])
                elif field == "entity.abn":
                    d["abn"] = claim["value"]
                elif field == "entity.acn":
                    d["acn"] = claim["value"]
                elif field == "address.state":
                    d["state"] = claim["value"]
                elif field == "address.locality":
                    d["locality"] = claim["value"]
                elif field == "address.postcode":
                    d["postcode"] = claim["value"]
            details[key] = d
    return details


def record_cell(key: str, details: dict) -> str:
    d = details.get(key)
    if d is None:
        return f"<em>{esc(key)} (record not found)</em>"
    names = "<br>".join(esc(n) for n in d["names"]) or "<em>no name claims</em>"
    ids = []
    if d["abn"]:
        ids.append(f"ABN {d['abn']}")
    if d["acn"]:
        ids.append(f"ACN {d['acn']}")
    place = " ".join(p for p in (d["locality"], d["state"], d["postcode"]) if p)
    return (
        f"<div class='rec'><span class='src'>{esc(d['source'])}</span>"
        f"<strong>{names}</strong>"
        f"<span class='meta'>{esc(' · '.join(ids) if ids else 'no identifier')}"
        f"{(' · ' + esc(place)) if place else ''}</span></div>"
    )


def sample_queue() -> list[dict]:
    """20 refused exact-name pairs (the looser-threshold candidates)."""
    candidates = []
    for line in (ROOT / "outputs" / "unlinked.jsonl").read_text().splitlines():
        item = json.loads(line)
        if item["reason"].startswith("name matches"):
            candidates.append(item)
    return random.Random(QUEUE_SEED).sample(candidates, min(QUEUE_SAMPLE_SIZE, len(candidates)))


def main() -> None:
    details = load_record_details()
    with (ROOT / "review" / "part3_handcheck.csv").open() as fh:
        accepted = list(csv.DictReader(fh))
    queue_sample = sample_queue()

    # persist the queue sample so verdicts have a place to live
    queue_csv = ROOT / "review" / "part3_queue_sample.csv"
    with queue_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["record_a", "record_b", "reason", "evidence", "same_business", "note"])
        writer.writeheader()
        for item in queue_sample:
            writer.writerow({"record_a": item["record_a"], "record_b": item["record_b"],
                             "reason": item["reason"], "evidence": item["evidence"],
                             "same_business": "", "note": ""})

    accepted_rows = []
    for i, link in enumerate(accepted, 1):
        accepted_rows.append(
            f"<tr><td class='num'>{i}</td>"
            f"<td>{record_cell(link['record_a'], details)}</td>"
            f"<td>{record_cell(link['record_b'], details)}</td>"
            f"<td><code class='small'>{esc(link['evidence'])}</code><br>"
            f"<span class='meta'>conf {esc(link['link_confidence'])} · {esc(link['tier'])}</span></td></tr>"
        )
    queue_rows = []
    for i, item in enumerate(queue_sample, 1):
        queue_rows.append(
            f"<tr><td class='num'>Q{i}</td>"
            f"<td>{record_cell(item['record_a'], details)}</td>"
            f"<td>{record_cell(item['record_b'], details)}</td>"
            f"<td><span class='meta'>{esc(item['reason'])}</span></td></tr>"
        )

    page = f"""<title>链接人工核对 · Part 3</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* layout: two long verdict tables, pair-per-row, judged left vs right */
:root {{
  --bg: #f7f7f5; --panel: #ffffff; --fg: #1d2129; --muted: #6b7280;
  --line: #e3e4e0; --accent: #1f6f54; --code-bg: #f0f0ed; --warn-bg: #fdf0d7; --warn-fg: #8a5a0a;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #15171b; --panel: #1d2026; --fg: #e8e8e4; --muted: #9aa1ab;
  --line: #31353c; --accent: #5cbf97; --code-bg: #272b31; --warn-bg: #3a2d10; --warn-fg: #ecbf63; color-scheme: dark;
}} }}
:root[data-theme="dark"] {{
  --bg: #15171b; --panel: #1d2026; --fg: #e8e8e4; --muted: #9aa1ab;
  --line: #31353c; --accent: #5cbf97; --code-bg: #272b31; --warn-bg: #3a2d10; --warn-fg: #ecbf63; color-scheme: dark;
}}
body {{ background: var(--bg); color: var(--fg);
  font: 15px/1.55 -apple-system, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 28px 64px; }}
main {{ max-width: 1040px; margin: 0 auto; display: grid; gap: 26px; }}
h1 {{ font-size: 1.4rem; margin: 0; }}
h2 {{ font-size: 1.05rem; margin: 0 0 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }}
section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px 20px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ color: var(--muted); font-weight: 600; }}
.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; color: var(--muted); }}
code {{ background: var(--code-bg); border-radius: 4px; padding: 1px 5px; font-size: 0.82em; overflow-wrap: anywhere; }}
.rec {{ display: grid; gap: 2px; min-width: 0; }}
.src {{ font-size: 0.74rem; color: var(--accent); letter-spacing: 0.03em; text-transform: uppercase; }}
.meta {{ font-size: 0.8rem; color: var(--muted); }}
.tablewrap {{ overflow-x: auto; }}
.guide ul {{ margin: 0; padding-left: 1.2em; display: grid; gap: 6px; }}
.tip {{ background: var(--warn-bg); color: var(--warn-fg); border-radius: 6px; padding: 8px 12px; font-size: 0.88rem; }}
</style>
<main>
<header>
  <h1>链接人工核对 · Part 3</h1>
  <p class="muted meta">接受的链接共 1,090 条（全部为标识符层）· 拒绝队列 1,217 条 · 跨源实体 354 个</p>
</header>

<section class="guide">
  <h2>怎么核（两张表，总共约 20 分钟）</h2>
  <ul>
    <li><strong>表一（50 条已接受）</strong>：每行左右两条记录，问自己「这是同一家企业吗？」名字吻合或一方是另一方的商号/门店名 → y；明显不是一家 → n。<strong>默认全 y，只报出你认为错的编号</strong>（比如「12、37 是 n」）。</li>
    <li><strong>表二（20 条被拒的同名对）</strong>：这些是名字完全一致但我们因缺少佐证（州缺失/不同）而拒绝的。请判断每条「其实是不是同一家」——这个比例就是「放宽阈值后的精确率」，题目明确说对这个数感兴趣。格式如「Q3、Q7 是 y，其余 n」或相反。</li>
    <li>拿不准的标「不确定」，我们按保守口径（算错）统计。</li>
  </ul>
  <p class="tip">提示：表一全是 ABN/ACN 相同的链接，错误只可能来自「同一个 ABN 被两家不同企业使用」（源数据录入错误）——所以重点看两边名字是否风马牛不相及。</p>
</section>

<section>
  <h2>表一 · 50 条已接受的链接（测我们阈值下的精确率）</h2>
  <div class="tablewrap"><table>
    <tr><th>#</th><th>记录 A</th><th>记录 B</th><th>证据</th></tr>
    {"".join(accepted_rows)}
  </table></div>
</section>

<section>
  <h2>表二 · 20 条被拒的同名对（测放宽阈值后的精确率）</h2>
  <div class="tablewrap"><table>
    <tr><th>#</th><th>记录 A</th><th>记录 B</th><th>拒绝原因</th></tr>
    {"".join(queue_rows)}
  </table></div>
</section>
</main>
"""
    out = ROOT / "review" / "part3_handcheck.html"
    out.write_text(page)
    print(f"wrote {out} and {queue_csv}")


if __name__ == "__main__":
    main()
