"""Wiki rendering: registry + manifest -> markdown (mkdocs-ready).

v0 renders the subsystem page skeleton from DESIGN §7:
overview -> formula cards (badged) -> conventions -> bindings/walkthrough
-> verification status (verdict history) -> references.
Badge states come from drift.badge_state (verdict records + git freshness).
v0 renders bindings as machine-readable text refs; clickable bidirectional
source links land in v1 (needs source serving).
"""
from __future__ import annotations

from pathlib import Path

from .drift import badge_state
from .manifest import load_manifest
from .registry import FormulaEntry, load_entries

BADGES = {"verified": "✅", "stale": "🕐", "failing": "❌", "unverified": "⚪"}


def _badge(state: str) -> str:
    return f"{BADGES[state]} `{state}`"


def formula_card_md(entry: FormulaEntry, state: str) -> str:
    lines = [f"### `{entry.id}` {_badge(state)}", ""]
    if entry.latex:
        lines += ["**公式（规范形式）**", "", f"$${entry.latex.strip()}$$", ""]
    lines += ["**SymPy 机读形式**", "", "```", entry.sympy.strip(), "```", ""]
    if entry.symbol_identity:
        lines += ["**符号身份（人审层）**", ""]
        lines += [f"- {s}" for s in entry.symbol_identity]
        lines += [""]
    if entry.convention_map:
        lines += ["**约定映射**", "", "| 本仓库 | 文献/外部约定 | 背书 |",
                  "|---|---|---|"]
        for c in entry.convention_map:
            lines.append(f"| {c.get('ours', '')} | {c.get('theirs', '')} "
                         f"| {c.get('verified_by', '—')} |")
        lines += [""]
    imp = entry.implements
    binds = "".join(f"\n- `{k}`: {v}" for k, v in imp.get("binds", {}).items())
    lines += ["**代码绑定**", "",
              f"- `{imp.get('module')}::{imp.get('function')}`",
              f"- 源：`{imp.get('file', '?')}`{binds}", ""]
    if entry.references:
        lines += ["**文献**", ""]
        lines += [f"- {r.get('paper')} — {r.get('where')}"
                  + (f", eq. {r['eq']}" if r.get("eq") else "")
                  for r in entry.references]
        lines += [""]
    lines += ["**验证状态**", ""]
    if entry.verdicts:
        for v in entry.verdicts[-5:]:
            diag = f" — {v['diagnosis']}" if v.get("diagnosis") else ""
            lines.append(f"- {v.get('at')} @{v.get('commit')} "
                         f"seed={v.get('seed')}: **{v.get('result')}**{diag}")
    else:
        lines.append("- （尚无判决记录）")
    lines += [""]
    return "\n".join(lines)


def subsystem_page_md(stage: dict, entries: list[FormulaEntry],
                      repo: Path, narrative: str = "") -> str:
    lines = [f"# {stage['title']}", "",
             f"管线阶段 `{stage['id']}`。", ""]
    mods = stage.get("modules", [])
    if mods:
        lines += ["**模块**", ""]
        for m in mods:
            src = m.replace(".", "/")
            lines.append(f"- `{m}` → [`{src}.py`](../../{src}.py)")
        lines += [""]
    docs = stage.get("docs", [])
    if docs:
        lines += ["**相关文档（仓库现有 docs/）**", ""]
        lines += [f"- [{d}](../../{d})" for d in docs]
        lines += [""]
    if narrative:
        lines += [narrative.strip(), ""]
    if not entries:
        lines += ["（本阶段暂无注册表条目；知识与叙事见上方链接。）", ""]
    for entry in entries:
        lines.append(formula_card_md(entry, badge_state(entry, repo)))
    return "\n".join(lines)


def registry_index_md(entries: list[FormulaEntry], repo: Path) -> str:
    """审计面：全部公式断言 + 徽章。"""
    lines = ["# 公式注册表与验证状态", "",
             "| 条目 | kind | 徽章 | 最近判决 |", "|---|---|---|---|"]
    for e in entries:
        last = e.verdicts[-1] if e.verdicts else {}
        lines.append(
            f"| `{e.id}` | {e.kind} | {_badge(badge_state(e, repo))} "
            f"| {last.get('result', '—')} @{last.get('commit', '—')} |")
    lines += [""]
    return "\n".join(lines)


def build(repo: Path, formulas: Path, out: Path) -> list[Path]:
    repo = Path(repo)
    manifest = load_manifest(formulas / "manifest.yaml")
    entries = load_entries(formulas)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    pages = out / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    narratives = out / "narratives"
    written = []
    stage_nav = []
    for stage in manifest["stages"]:
        mods = stage.get("modules", [])
        stage_entries = [e for e in entries
                         if any(e.implements.get("module", "")
                                .startswith(m) for m in mods)]
        npath = narratives / f"{stage['id']}.md"
        narrative = npath.read_text(encoding="utf-8") if npath.exists() else ""
        page = subsystem_page_md(stage, stage_entries, repo, narrative)
        fname = f"stage-{stage['id']}.md"
        (pages / fname).write_text(page, encoding="utf-8")
        written.append(pages / fname)
        stage_nav.append({stage["title"]: fname})

    (pages / "registry-index.md").write_text(
        registry_index_md(entries, repo), encoding="utf-8")
    written.append(pages / "registry-index.md")

    (pages / "index.md").write_text(
        index_md(manifest, entries, repo), encoding="utf-8")
    written.append(pages / "index.md")

    import yaml
    nav = yaml.safe_dump(
        [{"概述": "index.md"}, {"子系统": stage_nav},
         {"开发与参考": [{"公式注册表与验证状态": "registry-index.md"}]}],
        allow_unicode=True, sort_keys=False)
    (out / "mkdocs.yml").write_text(
        f"site_name: {manifest['repo']} wiki\n"
        f"docs_dir: pages\n"
        f"theme: material\n"
        f"markdown_extensions:\n"
        f"  - pymdownx.arithmatex:\n"
        f"      generic: true\n"
        f"  - pymdownx.superfences:\n"
        f"      custom_fences:\n"
        f"        - name: mermaid\n"
        f"          class: mermaid\n"
        f"          format: !!python/name:pymdownx.superfences.fence_code_format\n"
        f"nav:\n{nav}",
        encoding="utf-8")
    written.append(out / "mkdocs.yml")
    return written


def index_md(manifest: dict, entries: list[FormulaEntry], repo: Path) -> str:
    """覆盖率概览：wiki 的入口 = 每阶段的条目/徽章/链接，不再是空 stub。"""
    lines = [f"# {manifest['repo']} 科学文档", "",
             "由 scicodewiki 渲染。公式断言带信任徽章：",
             "✅ verified / 🕐 stale /  failing / ⚪ unverified", "",
             "| 阶段 | 条目 | 徽章 | 现有 docs/ |", "|---|---|---|---|"]
    for stage in manifest["stages"]:
        mods = stage.get("modules", [])
        es = [e for e in entries
              if any(e.implements.get("module", "").startswith(m)
                     for m in mods)]
        states = [badge_state(e, repo) for e in es]
        badges = " ".join(f"{BADGES[s]}×{states.count(s)}"
                          for s in dict.fromkeys(states)) if states else "—"
        docs = "、".join(d.split("/")[-1] for d in stage.get("docs", [])) or "—"
        lines.append(f"| [{stage['title']}](stage-{stage['id']}.md) "
                     f"| {len(es)} | {badges} | {docs} |")
    lines += ["", "审计面：[公式注册表与验证状态](registry-index.md)", ""]
    return "\n".join(lines)
