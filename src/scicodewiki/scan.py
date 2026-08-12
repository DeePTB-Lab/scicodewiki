"""Scan phase: compact intermediate cards + deterministic repo map.

Cards (skill-header style: YAML frontmatter + capped body) pin
*understanding* as auditable artifacts between raw code and writing.
_map.yaml is their deterministic projection = the bounded global view
outline/compose read, so the forest never costs raw-code context.

Deterministic fields (unit/file/loc/functions/classes/imports/centrality)
refresh from census on every scan; agent-filled semantics persist (merge).
"""
from __future__ import annotations

import ast
from pathlib import Path

import yaml

from .census import scan_package

CARD_KINDS = {"scientific-kernel", "plumbing", "io", "cli"}
CARD_STATUSES = {"skeleton", "scanned"}
PURPOSE_CAP = 120          # chars
BODY_CAP_LINES = 60        # card body cap
MIN_CHILD_LOC = 40         # split threshold for functions/classes

# mechanical kind hint: dense numeric marks -> kernel candidate (controls
# read depth only; the scan-repo agent makes the final kind call)
_KERNEL_MARKS = ("einsum", "linalg", "fft", "hbar", "HBAR", "integrate",
                 "tetrahedra", "np.sqrt", "occupation", "linewidth")

_SEMANTIC = ("purpose", "key_symbols", "inputs", "outputs", "depends_on",
             "doc_anchors", "literature_hints", "conventions",
             "formula_candidates", "terms", "notes", "provenance")
_KNOWN = ("card", "kind", "kind_hint", "status", "unit", "function", "file",
          "loc", "functions", "classes", "children", "imports",
          "centrality") + _SEMANTIC


class ScanError(ValueError):
    pass


def parse_card(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ScanError("missing frontmatter opener '---'")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ScanError("missing frontmatter closer '---'")
    try:
        meta = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        raise ScanError(f"frontmatter YAML error: {exc}") from exc
    if not isinstance(meta, dict):
        raise ScanError("frontmatter is not a mapping")
    return meta, text[end + 5:]


def _card_text(meta: dict, body: str) -> str:
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True,
                                   sort_keys=False) + "---\n" + body


def _kind_hint(module: str, src: str) -> str:
    low = module.lower()
    if any(m in src for m in _KERNEL_MARKS):
        return "scientific-kernel"
    if ".cli" in low or low.endswith("cli"):
        return "cli"
    if ".io" in low or "providers" in low:
        return "io"
    return "plumbing"


def _centralities(census: dict) -> dict[str, int]:
    """in-degree over mechanical import edges, normalized to card ids."""
    ids = {u["module"] for u in census["units"]}

    def norm(target: str) -> str | None:
        if target in ids:
            return target
        init = target + ".__init__"
        return init if init in ids else None

    cent = {i: 0 for i in ids}
    for u in census["units"]:
        for t in u["imports"]:
            n = norm(t)
            if n and n != u["module"]:
                cent[n] += 1
    return cent


def skeleton_cards(census: dict, budget: int = 1500,
                   repo: Path | None = None) -> dict[str, dict]:
    """Deterministic prefill: one card per census unit; over-budget units
    additionally split into per-function/per-class child cards."""
    cent = _centralities(census)
    out = {}
    for u in census["units"]:
        src = ""
        if repo is not None:
            p = Path(repo) / u["file"]
            if p.exists():
                src = p.read_text(encoding="utf-8")
        hint = _kind_hint(u["module"], src)
        meta = {
            "card": u["module"], "kind": hint, "kind_hint": hint,
            "status": "skeleton", "unit": u["module"], "file": u["file"],
            "loc": u["loc"], "functions": u["functions"],
            "classes": u["classes"], "imports": u["imports"],
            "centrality": cent[u["module"]],
        }
        if u["loc"] > budget:
            children = []
            for f in u["functions"]:
                if f["loc"] >= MIN_CHILD_LOC:
                    cid = f"{u['module']}.{f['name']}"
                    children.append(cid)
                    out[cid] = {
                        "card": cid, "kind": hint, "kind_hint": hint,
                        "status": "skeleton", "unit": u["module"],
                        "function": f["name"], "file": u["file"],
                        "loc": f["loc"], "imports": [],
                        "centrality": cent[u["module"]],
                    }
            for c in u["classes"]:
                cid = f"{u['module']}.{c['name']}"
                children.append(cid)
                out[cid] = {
                    "card": cid, "kind": hint, "kind_hint": hint,
                    "status": "skeleton", "unit": u["module"],
                    "function": c["name"], "file": u["file"],
                    "loc": c["loc"], "imports": [],
                    "centrality": cent[u["module"]],
                }
            meta["children"] = children
        out[u["module"]] = meta
    return out


def merge_card(old: dict, skeleton: dict) -> dict:
    """Deterministic fields from skeleton; agent semantics persist.
    Final kind kept from a scanned old card, else the hint."""
    merged = dict(skeleton)
    for field in _SEMANTIC:
        if field in old:
            merged[field] = old[field]
    if old.get("status") == "scanned":
        merged["status"] = "scanned"
        merged["kind"] = old.get("kind", skeleton["kind_hint"])
    else:
        merged["status"] = "skeleton"
        merged["kind"] = old.get("kind", skeleton["kind_hint"])
    return merged


def load_cards(scan_dir: Path) -> list[dict]:
    cards = []
    for md in sorted(Path(scan_dir).glob("*.md")):
        meta, _ = parse_card(md.read_text(encoding="utf-8"))
        meta["_path"] = md
        cards.append(meta)
    return cards


def write_scan(repo: Path, package: str, out_dir: Path,
               budget: int = 1500, force: bool = False) -> dict:
    census = scan_package(repo, package)
    skeletons = skeleton_cards(census, budget, repo)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {"total": 0, "scanned": 0, "skeleton": 0}
    for cid, sk in skeletons.items():
        path = out_dir / f"{cid}.md"
        body = ""
        if path.exists() and not force:
            old, body = parse_card(path.read_text(encoding="utf-8"))
            meta = merge_card(old, sk)
        else:
            meta = dict(sk)
        counts["total"] += 1
        counts["scanned" if meta["status"] == "scanned" else "skeleton"] += 1
        path.write_text(_card_text(meta, body), encoding="utf-8")
    build_map(scan_dir=out_dir, repo_name=package,
              out_path=out_dir / "_map.yaml")
    return counts


def lint_scan(scan_dir: Path) -> list[str]:
    problems = []
    ids = set()
    parsed = []
    for md in sorted(Path(scan_dir).glob("*.md")):
        try:
            meta, body = parse_card(md.read_text(encoding="utf-8"))
        except ScanError as exc:
            problems.append(f"{md.name}: {exc}")
            continue
        parsed.append((md, meta, body))
        ids.add(meta.get("card"))
    for md, meta, body in parsed:
        name = md.name
        unknown = set(meta) - set(_KNOWN)
        if unknown:
            problems.append(f"{name}: unknown fields {sorted(unknown)}")
        if meta.get("status") not in CARD_STATUSES:
            problems.append(f"{name}: bad status {meta.get('status')!r}")
        if meta.get("kind") not in CARD_KINDS:
            problems.append(f"{name}: bad kind {meta.get('kind')!r}")
        purpose = meta.get("purpose")
        if meta.get("status") == "scanned":
            if not purpose:
                problems.append(f"{name}: scanned card missing purpose")
            elif len(purpose) > PURPOSE_CAP:
                problems.append(f"{name}: purpose > {PURPOSE_CAP} chars")
        elif purpose and len(purpose) > PURPOSE_CAP:
            problems.append(f"{name}: purpose > {PURPOSE_CAP} chars")
        if body and len(body.strip().splitlines()) > BODY_CAP_LINES:
            problems.append(f"{name}: body > {BODY_CAP_LINES} lines")
        for dep in meta.get("depends_on", []):
            if dep not in ids:
                problems.append(f"{name}: depends_on '{dep}' is not a card")
    return problems


def build_map(scan_dir: Path, repo_name: str,
              out_path: Path | None = None) -> dict:
    """Deterministic projection of the cards = bounded global view."""
    cards = load_cards(scan_dir)
    subs = {}
    for c in cards:
        parts = c["unit"].split(".")
        top = parts[1] if len(parts) > 2 else (parts[-1] if parts else "_")
        subs.setdefault(top, []).append(c)
    subpackages = {}
    for top, cs in sorted(subs.items()):
        kinds = {}
        for c in cs:
            kinds[c.get("kind", "?")] = kinds.get(c.get("kind", "?"), 0) + 1
        edges = set()
        literature, docs = set(), set()
        for c in cs:
            for t in c.get("imports", []):
                edges.add((c["card"], t))
            for t in c.get("depends_on", []):
                edges.add((c["card"], t))
            literature.update(c.get("literature_hints", []))
            docs.update(c.get("doc_anchors", []))
        units = sorted(cs, key=lambda c: (-c.get("centrality", 0), c["card"]))
        subpackages[f"{_pkg_of(cs)}.{top}"] = {
            "kinds": kinds,
            "loc": sum(c.get("loc", 0) for c in cs),
            "units": [
                {"card": c["card"], "kind": c.get("kind"),
                 "loc": c.get("loc"), "status": c.get("status"),
                 "centrality": c.get("centrality", 0),
                 "purpose": c.get("purpose", "")}
                for c in units],
            "cross_links": sorted(edges),
            "literature": sorted(literature),
            "docs": sorted(docs),
        }
    depth = {"agent-read": 0, "mechanical-docstring": 0}
    for c in cards:
        d = (c.get("provenance") or {}).get("depth")
        if d in depth:
            depth[d] += 1
    mapping = {
        "repo": repo_name,
        "generated_by": "scicodewiki scan",
        "cards": {"total": len(cards),
                  "scanned": sum(c.get("status") == "scanned" for c in cards),
                  "skeleton": sum(c.get("status") == "skeleton" for c in cards)},
        "depth_counts": depth,
        "subpackages": subpackages,
    }
    if out_path is not None:
        out_path.write_text(yaml.safe_dump(mapping, allow_unicode=True,
                                           sort_keys=False), encoding="utf-8")
    return mapping


def _pkg_of(cs: list[dict]) -> str:
    return cs[0]["unit"].split(".")[0]


def locate_function(repo: Path, module: str, name: str) -> tuple[int, int]:
    """Current line span of a function/class — line-drift immune pointer
    for compose's on-demand re-reads."""
    path = Path(repo) / (module.replace(".", "/") + ".py")
    if not path.exists():
        path = Path(repo) / (module.replace(".", "/")[:-len("__init__")]
                             if module.endswith("__init__")
                             else module.replace(".", "/"))
    if not path.exists():
        raise ScanError(f"module file not found: {module}")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and n.name == name:
            return n.lineno, n.end_lineno
    raise ScanError(f"{name} not found in {module}")
