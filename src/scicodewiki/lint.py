"""Mechanical lint for generated narratives: chapter-spec discipline as code.

Reader-facing prose must not leak the machinery, and quantitative claims
must carry citations. Deterministic checks, same spirit as coverage().
"""
from __future__ import annotations

import re
from pathlib import Path

# machine vocabulary that must never appear in reader narratives
FORBIDDEN = [
    "✅", "🕐", "⚪",
    "verdict", "convention_map", "staging", "formula_impl",
    "scicodewiki verify", "badge",
]

# lines that look quantitative: number with unit/exponent/scientific notation
QUANT = re.compile(r"\d+(\.\d+)?\s*(%|e-?\d|THz|cm⁻¹|ps|K\b|Å)|\d+\.\d{2,}")


def lint_narratives(narratives_dir: Path) -> list[str]:
    problems = []
    nd = Path(narratives_dir)
    if not nd.is_dir():
        return [f"{nd}: no narratives dir (run compose first)"]
    for md in sorted(nd.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for word in FORBIDDEN:
                if word in line:
                    problems.append(
                        f"{md.name}:{lineno}: machine vocabulary '{word}' "
                        f"in reader narrative")
        # quantitative lines in benchmarks-style pages need a citation
        if any(k in md.name for k in ("benchmark", "algorithm", "physics")):
            blocks = text.split("\n\n")
            for block in blocks:
                if QUANT.search(block) and "docs/" not in block \
                        and "```" not in block and "|" not in block:
                    first = block.strip().splitlines()[0][:40]
                    problems.append(
                        f"{md.name}: quantitative block without docs/ "
                        f"citation: '{first}...'")
        # algorithm pages must carry a real data-flow diagram
        if "algorithm" in md.name and "mermaid" not in text:
            problems.append(f"{md.name}: algorithm page without mermaid "
                            f"data-flow diagram")
    return problems


MIN_PROSE = {"physics": 1500, "algorithm": 2500, "usage": 2000,
             "benchmarks": 2000}


def _prose_chars(text: str) -> int:
    import re
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return len(re.sub(r"\s", "", text))


def _body_after_links(text: str) -> str:
    idx = text.find("\n## ")
    return text[idx:] if idx >= 0 else text


def density_problems(narratives_dir: Path, manifest: dict) -> list[str]:
    """Code-layer density gate: thin pages, link-only modules, missing
    code-map tables. The information-density analogue of the formula gate."""
    problems = []
    for stage in manifest["stages"]:
        targets = ([(sp["id"], f"{stage['id']}-{sp['id']}.md")
                    for sp in stage.get("pages", [])]
                   or [(None, f"{stage['id']}.md")])
        for pid, fname in targets:
            path = Path(narratives_dir) / fname
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            prose = _prose_chars(text)
            need = MIN_PROSE.get(pid or "physics", 1500)
            if prose < need:
                problems.append(f"{fname}: prose {prose} chars < {need} "
                                f"(thin page — expand or split)")
            body = _body_after_links(text)
            for m in stage.get("modules", []):
                leaf = m.split(".")[-1]
                if leaf not in body:
                    problems.append(f"{fname}: module '{m}' only linked, "
                                    f"never described in body")
            if (pid or "") == "algorithm" and "|" not in text:
                problems.append(f"{fname}: algorithm page lacks a code-map "
                                f"table (function/class inventory)")
    return problems


THEORY_MIN = 2000


def theory_coverage_problems(narratives_dir: Path, manifest: dict,
                             cards: list) -> list[str]:
    """Zone-1 theory page must introduce EVERY physics capability the code
    implements (spectrum/DOS, linewidth, transport, ...), not just the
    flagship. Coverage is mechanical: each scientific-kernel stage must be
    mentioned in theory.md or carry its own dense physics page."""
    probs = []
    tpath = Path(narratives_dir) / "theory.md"
    if not tpath.exists():
        return ["theory.md missing: zone-1 theory page is required"]
    text = tpath.read_text(encoding="utf-8")
    prose = _prose_chars(text)
    if prose < THEORY_MIN:
        probs.append(f"theory.md: prose {prose} chars < {THEORY_MIN} "
                     f"(must introduce every capability, not just the flagship)")
    for s in manifest["stages"]:
        mods = s.get("modules", [])
        has_kernel = any(
            c.get("kind") == "scientific-kernel"
            and any(c.get("unit", "").startswith(m)
                    or m.startswith(c.get("unit", "")) for m in mods)
            for c in cards)
        if not has_kernel:
            continue
        tokens = [t for t in s["id"].replace("-", "_").split("_")
                  if len(t) > 3]
        phys_page = any(sp.get("id") == "physics" for sp in s.get("pages", []))
        if tokens and not any(t in text for t in tokens) and not phys_page:
            probs.append(f"theory.md: capability '{s['id']}' never "
                         f"introduced (no physics page either) — every "
                         f"capability needs a principle intro")
    return probs
