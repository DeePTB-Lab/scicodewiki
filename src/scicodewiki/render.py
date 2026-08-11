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
                      repo: Path) -> str:
    lines = [f"# {stage['title']}", "",
             f"管线阶段 `{stage['id']}`。模块：{', '.join(stage.get('modules', []))}",
             ""]
    if not entries:
        lines += ["（本阶段暂无注册表条目）", ""]
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

    written = []
    nav = [{"首页": "index.md"}]
    stage_nav = []
    for stage in manifest["stages"]:
        mods = stage.get("modules", [])
        stage_entries = [e for e in entries
                         if any(e.implements.get("module", "")
                                .startswith(m) for m in mods)]
        page = subsystem_page_md(stage, stage_entries, repo)
        fname = f"stage-{stage['id']}.md"
        (out / fname).write_text(page, encoding="utf-8")
        written.append(out / fname)
        stage_nav.append({stage["title"]: fname})

    (out / "registry-index.md").write_text(
        registry_index_md(entries, repo), encoding="utf-8")
    written.append(out / "registry-index.md")

    (out / "index.md").write_text(
        f"# {manifest['repo']} 科学文档\n\n"
        "由 scicodewiki 渲染。公式断言带信任徽章：\n"
        "✅ verified / 🕐 stale / ❌ failing /  unverified\n",
        encoding="utf-8")
    written.append(out / "index.md")

    import yaml
    mkdocs = {
        "site_name": f"{manifest['repo']} wiki",
        "theme": "material",
        "markdown_extensions": [
            {"pymdownx.arithmatex": {"generic": True}},
            "pymdownx.superfences",
        ],
        "nav": [{"概述": "index.md"}, {"子系统": stage_nav},
                {"开发与参考": [{"公式注册表与验证状态": "registry-index.md"}]}],
    }
    (out / "mkdocs.yml").write_text(
        yaml.safe_dump(mkdocs, allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    written.append(out / "mkdocs.yml")
    return written
