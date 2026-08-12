"""Mechanical structural census: the decomposition ground truth.

Deterministic AST inventory of the target package (modules, functions,
LOC). bootstrap groups census units into semantic stages; coverage()
reports census units no stage documents — silent gaps become visible.
Python via stdlib ast; multi-language (Tree-Sitter) is v2.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path


def _raw_imports(tree: ast.Module, module: str, package: str) -> list[str]:
    """Import targets as dot-paths; relative imports resolved by level.
    (aider-repomap lesson: reference edges are extracted mechanically.)"""
    own = module.split(".")
    targets = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            targets += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.level == 0:
                if n.module:
                    targets.append(n.module)
            else:
                base = own[:-1]
                up = n.level - 1
                if up > len(base):
                    continue
                base = base[: len(base) - up]
                targets.append(".".join(base + ([n.module] if n.module else [])))
    return [t for t in targets if t == package or t.startswith(package + ".")]


def scan_package(repo: Path, package: str) -> dict:
    root = Path(repo) / package
    if not root.is_dir():
        raise ValueError(f"package dir not found: {root}")
    units = []
    raw = {}
    for py in sorted(root.rglob("*.py")):
        src = py.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        module = str(py.relative_to(repo).with_suffix("")).replace("/", ".")
        functions = [
            {"name": n.name, "loc": n.end_lineno - n.lineno + 1}
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        classes = [
            {"name": c.name, "loc": c.end_lineno - c.lineno + 1,
             "methods": [n.name for n in c.body
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]}
            for c in ast.walk(tree) if isinstance(c, ast.ClassDef)
        ]
        raw[module] = _raw_imports(tree, module, package)
        units.append({
            "module": module,
            "file": str(py.relative_to(repo)),
            "loc": len(src.splitlines()),
            "functions": functions,
            "classes": classes,
            "imports": [],
        })
    modules = {u["module"] for u in units}

    def exists(target: str) -> bool:
        return target in modules or any(
            m.startswith(target + ".") for m in modules)

    for u in units:
        u["imports"] = sorted({t for t in raw[u["module"]] if exists(t)})
    return {"package": package, "units": units}


def write_census(repo: Path, package: str, out: Path) -> dict:
    census = scan_package(repo, package)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(census, indent=1), encoding="utf-8")
    return census


def undocumented(census: dict, manifest: dict) -> list[dict]:
    """census units no manifest stage documents (silent coverage gaps)."""
    documented = [m for s in manifest["stages"] for m in s.get("modules", [])]

    def covered(mod: str) -> bool:
        if any(mod.startswith(m) or m.startswith(mod) for m in documented):
            return True
        if mod.endswith(".__init__"):   # package files ride on their children
            parent = mod[: -len(".__init__")]
            return any(m == parent or m.startswith(parent + ".")
                       for m in documented)
        return False

    return [u for u in census["units"] if not covered(u["module"])]


def preview_manifest(census: dict, repo_name: str) -> dict:
    """Deterministic zero-LLM manifest for preview mode: one stage per
    top-level subpackage. Funnel entry; extract/outline/compose refine
    later."""
    stages = {}
    for u in census["units"]:
        parts = u["module"].split(".")
        top = parts[1] if len(parts) > 2 else None
        if not top or top in ("tests",):
            continue
        stages.setdefault(top, set()).add(
            ".".join(parts[:3]) if len(parts) > 3 else u["module"])
    return {
        "repo": repo_name,
        "preview": True,
        "stages": [
            {"id": t, "title": t, "modules": sorted(ms)}
            for t, ms in sorted(stages.items())
        ],
    }


def over_budget(census: dict, manifest: dict, entries=None,
                budget: int = 1500) -> list[dict]:
    """Pages whose bound code exceeds the narration budget: the recursion
    trigger (chapter-spec). Gives the soft rule teeth.

    Subpages bind registry entries -> their implements.module LOC;
    page-less stages bind their module list.
    """
    entries = entries or []
    loc_of = lambda mods: sum(  # noqa: E731
        u["loc"] for u in census["units"]
        if any(u["module"].startswith(m) or m.startswith(u["module"])
               for m in mods))
    entry_mods = {e.id: e.implements.get("module", "") for e in entries}
    hot = []
    for stage in manifest["stages"]:
        pages = stage.get("pages")
        if pages:
            for sp in pages:
                mods = [entry_mods[f] for f in sp.get("formulas", [])
                        if f in entry_mods]
                total = loc_of([m for m in mods if m])
                if total > budget:
                    hot.append({"stage": stage["id"], "page": sp["id"],
                                "loc": total})
        else:
            total = loc_of(stage.get("modules", []))
            if total > budget:
                hot.append({"stage": stage["id"], "page": None,
                            "loc": total})
    return hot
