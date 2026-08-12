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

# material does not auto-load MathJax; official recipe = arithmatex generic
# output (\( \) / \[ \]) + these two extra_javascript entries
MATHJAX_JS = """window.MathJax = {
  tex: {
    inlineMath: [["\\\\(", "\\\\)"]],
    displayMath: [["\\\\[", "\\\\]"]]
  }
};

document$.subscribe(() => {
  MathJax.typesetClear();
  MathJax.typeset();
});
"""

# reader-facing typography: CJK stack, reading measure, quiet tables,
# centered diagrams. design tokens stay in the theme palette (mkdocs.yml).
EXTRA_CSS = """
:root {
  --md-text-font: -apple-system, "PingFang SC", "Hiragino Sans GB",
    "Noto Sans SC", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
  --md-code-font: "SF Mono", "JetBrains Mono", "Fira Code", Consolas,
    monospace;
}
.md-typeset {
  font-size: .78rem;
  line-height: 1.85;
}
.md-typeset h1, .md-typeset h2, .md-typeset h3 {
  letter-spacing: .01em;
  font-weight: 700;
}
.md-content { max-width: 46rem; margin-inline: auto; }
.md-typeset table:not([class]) {
  font-size: .72rem;
  border-radius: .3rem;
}
.md-typeset table:not([class]) th {
  background: var(--md-default-fg-color--lightest);
  color: var(--md-default-bg-color);
}
.md-typeset .mermaid, .md-typeset pre.mermaid {
  display: block;
  text-align: center;
}
.md-typeset code { font-size: .72rem; }
.md-typeset .admonition, .md-typeset details {
  border-radius: .35rem;
  font-size: .74rem;
}
"""


def _badge(state: str) -> str:
    return f"{BADGES[state]} `{state}`"


def formula_card_md(entry: FormulaEntry) -> str:
    # reader pages are pure documentation: no badges, no verdict wording.
    # verification lives in the audit face (registry index / CLI / CI) only.
    lines = [f"### `{entry.id}`", ""]
    if entry.latex:
        lines += ["**公式（规范形式）**", "", f"$${entry.latex.strip()}$$", ""]
    lines += ["**SymPy 机读形式**", "", "```", entry.sympy.strip(), "```", ""]
    if entry.symbol_identity:
        lines += ["**符号说明**", ""]
        lines += [f"- {s}" for s in entry.symbol_identity]
        lines += [""]
    # convention_map (ours/theirs/verified_by) is registry machinery for the
    # gate and audit face; reader pages get symbol explanations instead.
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
    # reader pages carry only the badge glyph (in the heading); the verdict
    # LOG is dev-process record — it lives in the registry index (audit face)
    return "\n".join(lines)


def subsystem_page_md(stage: dict, entries: list[FormulaEntry],
                      repo: Path, narrative: str = "",
                      title: str | None = None, crumb: str = "") -> str:
    heading = title or stage["title"]
    lines = [f"# {heading}", ""]
    if crumb:
        lines += [crumb, ""]
    lines += [f"管线阶段 `{stage['id']}`。", ""]
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
        lines.append(formula_card_md(entry))
    return "\n".join(lines)


def registry_index_md(entries: list[FormulaEntry], repo: Path) -> str:
    """审计面：全部公式断言 + 徽章。"""
    lines = ["# 公式注册表与验证状态", "",
             "| 条目 | kind | 徽章 | 最近判决 |", "|---|---|---|---|"]
    for e in entries:
        last = e.verdicts[-1] if e.verdicts else {}
        diag = last.get("diagnosis")
        diag_cell = f"<br>{diag}" if diag else ""
        lines.append(
            f"| `{e.id}` | {e.kind} | {_badge(badge_state(e, repo))} "
            f"| {last.get('result', '—')} @{last.get('commit', '—')}"
            f"{diag_cell} |")
    lines += ["", "完整判决历史见各条目 YAML 的 `verdicts` 字段"
                 "（开发过程记录，不面向 wiki 读者）。", ""]
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
    landing = {}                       # stage id -> reader landing file
    for stage in manifest["stages"]:
        mods = stage.get("modules", [])
        stage_entries = [e for e in entries
                         if any(e.implements.get("module", "")
                                .startswith(m) for m in mods)]
        subpages = stage.get("pages")
        if not subpages:
            npath = narratives / f"{stage['id']}.md"
            narrative = npath.read_text(encoding="utf-8") \
                if npath.exists() else ""
            page = subsystem_page_md(stage, stage_entries, repo, narrative)
            fname = f"stage-{stage['id']}.md"
            (pages / fname).write_text(page, encoding="utf-8")
            written.append(pages / fname)
            stage_nav.append({stage["title"]: fname})
            landing[stage["id"]] = fname
            continue
        # 3-level nav: stage node expands into topic subpages
        assigned = set()
        for sp in subpages:
            assigned.update(sp.get("formulas", []))
        children = []
        for i, sp in enumerate(subpages):
            fname = f"stage-{stage['id']}-{sp['id']}.md"
            npath = narratives / f"{stage['id']}-{sp['id']}.md"
            narrative = npath.read_text(encoding="utf-8") \
                if npath.exists() else ""
            cards = [e for e in stage_entries
                     if e.id in sp.get("formulas", [])]
            if i == 0:   # unassigned cards fall to the first subpage
                cards += [e for e in stage_entries
                          if e.id not in assigned]
            page = subsystem_page_md(
                stage, cards, repo, narrative, title=sp["title"],
                crumb=f"*{stage['title']} › {sp['title']}*")
            (pages / fname).write_text(page, encoding="utf-8")
            written.append(pages / fname)
            children.append({sp["title"]: fname})
            landing.setdefault(stage["id"], fname)
        stage_nav.append({stage["title"]: children})

    (pages / "registry-index.md").write_text(
        registry_index_md(entries, repo), encoding="utf-8")
    written.append(pages / "registry-index.md")

    (pages / "index.md").write_text(
        index_md(manifest, entries, repo, landing), encoding="utf-8")
    written.append(pages / "index.md")

    # zone-1 unified theory page (canonical forms + convention boxes live
    # here, not inside subsystem pages)
    theory_src = narratives / "theory.md"
    zone1 = [{"概述": "index.md"}]
    if theory_src.exists():
        (pages / "theory.md").write_text(
            "# 核心概念与理论基础\n\n"
            + theory_src.read_text(encoding="utf-8"), encoding="utf-8")
        written.append(pages / "theory.md")
        zone1.append({"核心概念与理论基础": "theory.md"})

    jsdir = pages / "javascripts"
    jsdir.mkdir(exist_ok=True)
    (jsdir / "mathjax.js").write_text(MATHJAX_JS, encoding="utf-8")
    cssdir = pages / "stylesheets"
    cssdir.mkdir(exist_ok=True)
    (cssdir / "extra.css").write_text(EXTRA_CSS, encoding="utf-8")

    import yaml
    nav = yaml.safe_dump(
        zone1 + [{"子系统": stage_nav},
                 {"开发与参考": [{"公式注册表与验证状态": "registry-index.md"}]}],
        allow_unicode=True, sort_keys=False)
    (out / "mkdocs.yml").write_text(
        f"site_name: {manifest['repo']} wiki\n"
        f"docs_dir: pages\n"
        f"markdown_extensions:\n"
        f"  - pymdownx.arithmatex:\n"
        f"      generic: true\n"
        f"  - pymdownx.superfences:\n"
        f"      custom_fences:\n"
        f"        - name: mermaid\n"
        f"          class: mermaid\n"
        f"          format: !!python/name:pymdownx.superfences.fence_code_format\n"
        f"extra_javascript:\n"
        f"  - javascripts/mathjax.js\n"
        f"  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js\n"
        f"extra_css:\n"
        f"  - stylesheets/extra.css\n"
        f"theme:\n"
        f"  name: material\n"
        f"  features:\n"
        f"    - navigation.instant\n"
        f"    - navigation.top\n"
        f"    - content.code.copy\n"
        f"    - toc.follow\n"
        f"  palette:\n"
        f"    - media: '(prefers-color-scheme: light)'\n"
        f"      scheme: default\n"
        f"      primary: indigo\n"
        f"      accent: teal\n"
        f"      toggle:\n"
        f"        icon: material/weather-night\n"
        f"        name: 切换暗色\n"
        f"    - media: '(prefers-color-scheme: dark)'\n"
        f"      scheme: slate\n"
        f"      primary: indigo\n"
        f"      accent: teal\n"
        f"      toggle:\n"
        f"        icon: material/weather-sunny\n"
        f"        name: 切换亮色\n"
        f"nav:\n{nav}",
        encoding="utf-8")
    written.append(out / "mkdocs.yml")
    return written


def index_md(manifest: dict, entries: list[FormulaEntry], repo: Path,
             landing: dict | None = None) -> str:
    """Landing page: what the code does, pipeline at a glance, reading map.
    Pure documentation — no verification plumbing on reader surfaces."""
    stages = manifest["stages"]
    lines = [f"# {manifest['repo']}", "",
             "科学计算文档：按物理工作流组织，公式与代码绑定一一对应，",
             "理论取文献规范形式，约定差异显式换算。", "",
             "```mermaid", "flowchart LR"]
    lines.append("  " + " --> ".join(
        f'{s["id"]}["{s["title"]}"]' for s in stages))
    lines += ["```", "", "## 阅读地图", ""]
    lines.append("- [核心概念与理论基础](theory.md) — 规范形式与约定换算框")
    for s in stages:
        mods = s.get("modules", [])
        n = len([e for e in entries
                 if any(e.implements.get("module", "").startswith(m)
                        for m in mods)])
        extra = f"（{n} 条机读公式）" if n else ""
        target = (landing or {}).get(s["id"], f"stage-{s['id']}.md")
        lines.append(f"- [{s['title']}]({target}){extra}")
    lines += ["", "开发与维护入口见左侧「开发与参考」。", ""]
    return "\n".join(lines)
