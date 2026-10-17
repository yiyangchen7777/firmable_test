"""Render an agent run's review as an HTML page (easier to read than review.md).

Usage: uv run python scripts/review_page.py <dataset_id>
Writes outputs/runs/<dataset_id>/review.html from the agent's checkpoint state.
Tooling for the human reviewer; the canonical artefact remains review.md.
"""

import html
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402

from firm.agent.graph import CHECKPOINT_DB, build_graph  # noqa: E402
from firm.agent.nodes import FIXED_TS  # noqa: E402
from firm.engine import extract_rows  # noqa: E402
from firm.mapping_config import MappingConfig  # noqa: E402

STATUS_CLASS = {
    "PASSING": "ok",
    "PASSING WITH FLAGS": "warn",
    "NOT PASSING": "bad",
    "NOT USEFUL": "bad",
}


def esc(value) -> str:
    return html.escape(str(value))


def load_state(dataset_id: str) -> dict:
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    app = build_graph().compile(checkpointer=SqliteSaver(conn))
    snapshot = app.get_state({"configurable": {"thread_id": dataset_id}})
    conn.close()
    if snapshot is None or not snapshot.values:
        raise SystemExit(f"no checkpoint state for {dataset_id}")
    return snapshot.values


def mapping_rows(cfg: dict) -> str:
    rows = []
    for f in cfg["fields"]:
        cond = '<span class="chip">conditional</span>' if f.get("conditional") else ""
        rows.append(
            "<tr>"
            f"<td><code>{esc(f['canonical'])}</code></td>"
            f"<td><code>{esc(f['source'])}</code></td>"
            f"<td><code class='small'>{esc(json.dumps(f['transforms']))}</code></td>"
            f"<td class='num'>{esc(f['confidence'])}</td>"
            f"<td>{cond}</td>"
            f"<td class='evidence'>{esc(f.get('evidence', ''))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def validation_rows(report: dict) -> str:
    rows = []
    for c in report["checks"]:
        mark = '<span class="pill ok">通过</span>' if c["pass"] else '<span class="pill bad">不过</span>'
        rows.append(
            "<tr>"
            f"<td>{esc(c['check'])}</td><td class='num'>{esc(c['threshold'])}</td>"
            f"<td class='num'>{esc(c['result'])}</td><td>{mark}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def failing_rows(report: dict) -> str:
    if not report["failing_examples"]:
        return "<p class='muted'>无</p>"
    items = []
    for f in report["failing_examples"]:
        items.append(
            f"<li><code>{esc(f['field'])}</code> — {esc(f['flag'])}"
            f"（原始值 <code>{esc(f['raw'][:60])}</code>）</li>"
        )
    return "<ul>" + "\n".join(items) + "</ul>"


def spotcheck_sections(spotcheck: dict) -> tuple[str, str, int, int]:
    suspicious_rows, ok_rows = [], []
    seen = set()
    for record in spotcheck.get("records", []):
        for finding in record.get("findings", []):
            key = (record.get("record"), finding.get("field"), finding.get("why"))
            if key in seen:  # the model occasionally repeats a finding
                continue
            seen.add(key)
            row = (
                "<tr>"
                f"<td><code>{esc(record.get('record'))}</code></td>"
                f"<td><code>{esc(finding.get('field'))}</code></td>"
                f"<td>{esc(finding.get('why', ''))}</td>"
                "</tr>"
            )
            if finding.get("verdict") == "suspicious":
                suspicious_rows.append(row)
            else:
                ok_rows.append(row)
    return "\n".join(suspicious_rows), "\n".join(ok_rows), len(ok_rows), len(suspicious_rows)


def unmapped_rows(cfg: dict) -> str:
    rows = []
    for u in cfg.get("unmapped", []):
        rows.append(f"<tr><td><code>{esc(u['source'])}</code></td><td>{esc(u['reason'])}</td></tr>")
    return "\n".join(rows) or "<tr><td colspan='2' class='muted'>无</td></tr>"


def side_by_side(state: dict) -> str:
    cfg_obj = MappingConfig(**state["config"])
    sample_rows = state["loop"][:5]
    sample_obs = extract_rows(sample_rows, cfg_obj, "cfg-proposal", FIXED_TS)
    cards = []
    for i, (row, one) in enumerate(zip(sample_rows, sample_obs), 1):
        raw_lines = "\n".join(f"{esc(k)}: {esc(v[:70])}" for k, v in row.items())
        canon_lines = "\n".join(
            f"{esc(c['field'])} = {esc(json.dumps(c['value']))}   (conf {esc(c['field_confidence'])})"
            for c in one["claims"]
        ) or "(无 claims)"
        cards.append(
            f"<div class='example'><h4>样例 {i} · record <code>{esc(one['source_record_id'])}</code></h4>"
            "<div class='pair'>"
            f"<div><h5>原始行（全部列）</h5><pre>{raw_lines}</pre></div>"
            f"<div><h5>标准化输出</h5><pre>{canon_lines}</pre></div>"
            "</div></div>"
        )
    return "\n".join(cards)


def render(dataset_id: str) -> Path:
    state = load_state(dataset_id)
    cfg = state["config"]
    meta = state["meta"]
    report = state["validation"]
    status = state["status"]
    status_class = STATUS_CLASS.get(status, "warn")
    sus_html, ok_html, ok_n, sus_n = spotcheck_sections(state["spotcheck"])
    decisions = state.get("decisions", {})
    observed = cfg["observed_at"]

    page = f"""<title>映射审核 · {esc(dataset_id)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* layout: single reading column, status-led; data tables full width */
:root {{
  --bg: #f7f7f5; --panel: #ffffff; --fg: #1d2129; --muted: #6b7280;
  --line: #e3e4e0; --accent: #1f6f54;
  --ok-bg: #e4f2ea; --ok-fg: #19613f; --warn-bg: #fdf0d7; --warn-fg: #8a5a0a;
  --bad-bg: #fbe5e3; --bad-fg: #a02c21; --code-bg: #f0f0ed;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #15171b; --panel: #1d2026; --fg: #e8e8e4; --muted: #9aa1ab;
  --line: #31353c; --accent: #5cbf97;
  --ok-bg: #173527; --ok-fg: #7fd7ab; --warn-bg: #3a2d10; --warn-fg: #ecbf63;
  --bad-bg: #40201d; --bad-fg: #f1988e; --code-bg: #272b31; color-scheme: dark;
}} }}
:root[data-theme="dark"] {{
  --bg: #15171b; --panel: #1d2026; --fg: #e8e8e4; --muted: #9aa1ab;
  --line: #31353c; --accent: #5cbf97;
  --ok-bg: #173527; --ok-fg: #7fd7ab; --warn-bg: #3a2d10; --warn-fg: #ecbf63;
  --bad-bg: #40201d; --bad-fg: #f1988e; --code-bg: #272b31; color-scheme: dark;
}}
body {{
  background: var(--bg); color: var(--fg);
  font: 15px/1.6 -apple-system, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 28px 64px;
}}
main {{ max-width: 980px; margin: 0 auto; display: grid; gap: 28px; }}
h1 {{ font-size: 1.45rem; margin: 0; text-wrap: balance; }}
h2 {{ font-size: 1.05rem; margin: 0 0 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }}
h4, h5 {{ margin: 0 0 6px; }}
section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px 20px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{ color: var(--muted); font-weight: 600; letter-spacing: 0.02em; }}
.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tablewrap {{ overflow-x: auto; }}
code {{ background: var(--code-bg); border-radius: 4px; padding: 1px 5px; font-size: 0.85em; }}
pre {{ background: var(--code-bg); border-radius: 6px; padding: 10px 12px; overflow-x: auto; font-size: 0.8rem; line-height: 1.5; margin: 0; }}
.pill {{ border-radius: 99px; padding: 2px 10px; font-size: 0.78rem; font-weight: 600; white-space: nowrap; }}
.pill.ok, .ok {{ background: var(--ok-bg); color: var(--ok-fg); }}
.pill.warn, .warn {{ background: var(--warn-bg); color: var(--warn-fg); }}
.pill.bad, .bad {{ background: var(--bad-bg); color: var(--bad-fg); }}
.status {{ display: inline-block; border-radius: 6px; padding: 4px 14px; font-weight: 700; }}
.chip {{ background: var(--code-bg); border-radius: 99px; padding: 1px 8px; font-size: 0.75rem; }}
.muted {{ color: var(--muted); }}
.evidence {{ min-width: 260px; }}
.metagrid {{ display: grid; grid-template-columns: 9em 1fr; gap: 4px 14px; font-size: 0.9rem; }}
.metagrid dt {{ color: var(--muted); }} .metagrid dd {{ margin: 0; min-width: 0; overflow-wrap: anywhere; }}
.guide ol {{ margin: 0; padding-left: 1.3em; display: grid; gap: 8px; }}
.pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.pair > div {{ min-width: 0; }}
@media (max-width: 720px) {{ .pair {{ grid-template-columns: 1fr; }} }}
.example {{ border-top: 1px solid var(--line); padding-top: 12px; margin-top: 12px; }}
.example:first-of-type {{ border-top: none; margin-top: 0; padding-top: 0; }}
.decision pre {{ user-select: all; }}
details summary {{ cursor: pointer; color: var(--muted); margin: 8px 0; }}
</style>
<main>
<header>
  <h1>映射审核 · {esc(dataset_id)}</h1>
  <p><span class="status {status_class}">{esc(status)}</span>
     <span class="muted">修订 {esc(state['revisions'])}/3 · 流程步数 {len(state['steps'])} · 审核材料同步存于 review.md</span></p>
</header>

<section class="guide">
  <h2>怎么审（约 5 分钟）</h2>
  <ol>
    <li><strong>看硬指标</strong>（<a href="#checks">校验结果</a>）：有没有 ❌。校验位、枚举、唯一性是代码算的，不会说谎。</li>
    <li><strong>看语义疑点</strong>（<a href="#flags">语义抽检</a>）：这是最需要人的部分——模型挑出「解析没错但含义可能错」的字段，你判断同不同意。</li>
    <li><strong>抽看对照样例</strong>（<a href="#examples">原始 vs 输出</a>）：随手挑两条，问自己「左边这列的意思，真的是右边那个字段吗？」</li>
    <li><strong>扫一眼未映射清单</strong>（<a href="#unmapped">unmapped</a>）：理由是否诚实，有没有本该映射却被偷懒放弃的列。</li>
  </ol>
  <p class="muted">你只有三个动作：approve / reject + 意见 / abandon。你不能直接改配置文件——人一改，配置就成了「手写的」，作业的核心主张（agent 独立完成映射）就不成立了。</p>
</section>

<section>
  <h2>来源与关键决定</h2>
  <dl class="metagrid">
    <dt>数据集</dt><dd>{esc(meta['title'])}（{esc(cfg['dataset_id'])}）</dd>
    <dt>发布方 / 许可</dt><dd>{esc(meta['publisher'])} / {esc(cfg['licence'])}</dd>
    <dt>读取方式</dt><dd><code>{esc(json.dumps(state['reader']))}</code></dd>
    <dt>source_reliability</dt><dd>{esc(cfg['source_reliability']['value'])} — {esc(cfg['source_reliability']['rationale'])}</dd>
    <dt>record_id</dt><dd><code>{esc(cfg['record_id']['strategy'])} {esc(cfg['record_id'].get('columns', []))}</code> — {esc(decisions.get('record_id_why', ''))}</dd>
    <dt>observed_at</dt><dd><code>{esc(observed['strategy'])}</code>（basis: {esc(observed['basis'])}，值 {esc(observed.get('value') or observed.get('column'))}）— {esc(decisions.get('observed_at_why', ''))}</dd>
  </dl>
</section>

<section id="checks">
  <h2>校验结果 · {len(state['loop'])} 行留存数据（循环集；最终验收在批准后跑一次）</h2>
  <div class="tablewrap"><table>
    <tr><th>检查</th><th>阈值</th><th>结果</th><th></th></tr>
    {validation_rows(report)}
  </table></div>
  <h4 style="margin-top:14px">未通过/弃权的例子</h4>
  {failing_rows(report)}
</section>

<section id="flags">
  <h2>语义抽检 · 10 条留存记录：{ok_n} ok / {sus_n} suspicious</h2>
  <div class="tablewrap"><table>
    <tr><th>record</th><th>字段</th><th>为什么可疑</th></tr>
    {sus_html or "<tr><td colspan='3' class='muted'>无疑点</td></tr>"}
  </table></div>
  <details><summary>展开 {ok_n} 条「ok」判定</summary>
  <div class="tablewrap"><table>
    <tr><th>record</th><th>字段</th><th>理由</th></tr>
    {ok_html}
  </table></div></details>
</section>

<section id="mapping">
  <h2>字段映射 · {len(cfg['fields'])} 条（共 {len(state['rows'][0])} 个源列）</h2>
  <div class="tablewrap"><table>
    <tr><th>canonical</th><th>← 源列</th><th>transforms</th><th>conf.</th><th></th><th>语义证据</th></tr>
    {mapping_rows(cfg)}
  </table></div>
</section>

<section id="unmapped">
  <h2>未映射的列 · {len(cfg.get('unmapped', []))}</h2>
  <div class="tablewrap"><table>
    <tr><th>源列</th><th>理由</th></tr>
    {unmapped_rows(cfg)}
  </table></div>
</section>

<section id="examples">
  <h2>对照样例 · 5 条原始行 vs 标准化输出</h2>
  <p class="muted">读含义，别读通过率：日期是注册日还是牌照日？名字是本人还是代理人？ABN 是这一行主体自己的吗？</p>
  {side_by_side(state)}
</section>

<section class="decision">
  <h2>你的决定（在终端运行其一）</h2>
  <pre>uv run firm onboard {esc(dataset_id)} --decide "approve"</pre>
  <pre>uv run firm onboard {esc(dataset_id)} --decide "reject: &lt;哪里不对、应该用哪个列/含义&gt;"</pre>
  <pre>uv run firm onboard {esc(dataset_id)} --decide "abandon"</pre>
  <p class="muted">reject 的意见会原文交给 agent 的 revise 节点，它自己改完会再生成一份新的审核材料。</p>
</section>
</main>
"""
    out = ROOT / "outputs" / "runs" / dataset_id / "review.html"
    out.write_text(page)
    print(f"wrote {out}")
    return out


if __name__ == "__main__":
    render(sys.argv[1])
