"""Global consistency checks: the forest-level mechanical gate.

Card coverage (no silent gaps), phantom refs (trust nothing), thesis
response (IA teeth), glossary (term canonicality), duplication
(say-once-then-cross-ref), link integrity. Problem-string style, like lint.
"""
from __future__ import annotations

import re
from pathlib import Path

from .manifest import load_manifest
from .scan import load_cards

_LINK = re.compile(r"\]\(([^)h][^)]*)\)")


def _allocations(manifest: dict):
    alloc = set()
    theses = []                       # (stage_id, page_id|None, thesis)
    for stage in manifest["stages"]:
        for t in stage.get("cards", []):
            alloc.add(t)
        if stage.get("thesis"):
            theses.append((stage["id"], None, stage["thesis"]))
        for sp in stage.get("pages", []):
            for t in sp.get("cards", []):
                alloc.add(t)
            if sp.get("thesis"):
                theses.append((stage["id"], sp["id"], sp["thesis"]))
    return alloc, theses


def card_coverage(cards: list[dict], manifest: dict) -> list[str]:
    alloc, _ = _allocations(manifest)
    return [f"unallocated kernel card: {c['card']}"
            for c in cards
            if c.get("kind") == "scientific-kernel"
            and c["card"] not in alloc]


def phantom_card_refs(manifest: dict, card_ids: set) -> list[str]:
    alloc, _ = _allocations(manifest)
    return [f"phantom card ref (not in wiki/scan): {t}"
            for t in sorted(alloc - set(card_ids))]


def _narrative_path(narratives_dir: Path, stage: str, page):
    name = f"{stage}.md" if page is None else f"{stage}-{page}.md"
    return narratives_dir / name


def thesis_problems(manifest: dict, narratives_dir: Path) -> list[str]:
    _, theses = _allocations(manifest)
    problems = []
    for stage, page, thesis in theses:
        path = _narrative_path(narratives_dir, stage, page)
        if not path.exists():
            problems.append(f"thesis without narrative: {path.name}")
            continue
        head = "\n\n".join(path.read_text(encoding="utf-8").split("\n\n")[:2])
        if thesis not in head:
            problems.append(f"{path.name}: opening does not address "
                            f"thesis '{thesis[:40]}...'")
    return problems


def glossary_problems(cards: list[dict], narratives_dir: Path) -> list[str]:
    problems = []
    aliases = []
    for c in cards:
        for canon, names in (c.get("terms") or {}).items():
            # E: tolerate str or list[str] values
            for a in (names if isinstance(names, list) else [names]):
                aliases.append((a, canon))
    if not aliases or not narratives_dir.is_dir():
        return problems
    for md in sorted(narratives_dir.glob("*.md")):
        for lineno, line in enumerate(
                md.read_text(encoding="utf-8").splitlines(), 1):
            for a, canon in aliases:
                if a and a in line and canon not in line:
                    problems.append(f"{md.name}:{lineno}: alias '{a}' "
                                    f"(canonical: '{canon}')")
    return problems


def _para_blocks(text: str) -> list[str]:
    out = []
    for b in text.split("\n\n"):
        b = "\n".join(l for l in b.strip().splitlines())
        if len(b) < 200 or b.startswith("```") or b.startswith("#") \
                or all(l.startswith("|") for l in b.splitlines() if l):
            continue
        out.append(" ".join(b.split()))
    return out


def duplication_problems(narratives_dir: Path, min_chars: int = 200) -> list[str]:
    seen: dict[str, str] = {}
    problems = []
    if not narratives_dir.is_dir():
        return problems
    for md in sorted(narratives_dir.glob("*.md")):
        for block in _para_blocks(md.read_text(encoding="utf-8")):
            if len(block) < min_chars:
                continue
            if block in seen and seen[block] != md.name:
                problems.append(f"{md.name}: paragraph duplicated from "
                                f"{seen[block]}: '{block[:40]}...'")
            else:
                seen.setdefault(block, md.name)
    return problems


def link_problems(narratives_dir: Path, repo: Path) -> list[str]:
    problems = []
    if not narratives_dir.is_dir():
        return problems
    for md in sorted(narratives_dir.glob("*.md")):
        for m in _LINK.finditer(md.read_text(encoding="utf-8")):
            target = m.group(1).split("#")[0]
            if not target:
                continue
            if target.startswith("../../"):
                dest = Path(repo) / target[6:]
            else:
                dest = narratives_dir / target
            if not dest.exists():
                problems.append(f"{md.name}: broken link {target}")
    return problems


def excluded_problems(manifest: dict, cards_by_id: dict) -> list[str]:
    """F7: explicit exclusions have a mechanical home; kernels may not be
    silently excluded."""
    problems = []
    for stage in manifest["stages"]:
        for ex in stage.get("excluded_cards", []):
            cid = ex["card"] if isinstance(ex, dict) else ex
            card = cards_by_id.get(cid)
            if card is None:
                problems.append(f"excluded card not in wiki/scan: {cid}")
            elif card.get("kind") == "scientific-kernel":
                problems.append(
                    f"scientific-kernel card cannot be excluded: {cid}")
    return problems


def check_repo(repo: Path, cards_only: bool = False) -> list[str]:
    scan_dir = repo / "wiki" / "scan"
    narratives = repo / "wiki" / "narratives"
    manifest_path = repo / "wiki" / "formulas" / "manifest.yaml"
    if not scan_dir.is_dir():
        return ["wiki/scan missing: run `scicodewiki scan` first"]
    cards = load_cards(scan_dir)
    card_ids = {c["card"] for c in cards}
    problems = []
    if manifest_path.exists():
        manifest = load_manifest(manifest_path)
        alloc, _ = _allocations(manifest)
        kernels = [c for c in cards
                   if c.get("kind") == "scientific-kernel"]
        if kernels and not alloc:
            problems.append("manifest has no cards: allocation — "
                            "run the outline step")
        problems += card_coverage(cards, manifest)
        problems += phantom_card_refs(manifest, card_ids)
        problems += excluded_problems(manifest, {c["card"]: c for c in cards})
        if not cards_only:          # F5: thesis needs narratives (compose)
            problems += thesis_problems(manifest, narratives)
    if not cards_only:
        from .lint import density_problems, theory_coverage_problems

        problems += glossary_problems(cards, narratives)
        problems += duplication_problems(narratives)
        problems += link_problems(narratives, repo)
        problems += density_problems(narratives, manifest)
        problems += theory_coverage_problems(narratives, manifest, cards)
    return problems
