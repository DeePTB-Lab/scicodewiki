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
        return [f"{nd}: no narratives dir (run narrate first)"]
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
