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


def scan_package(repo: Path, package: str) -> dict:
    root = Path(repo) / package
    if not root.is_dir():
        raise ValueError(f"package dir not found: {root}")
    units = []
    for py in sorted(root.rglob("*.py")):
        src = py.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        functions = [
            {"name": n.name, "loc": n.end_lineno - n.lineno + 1}
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        units.append({
            "module": str(py.relative_to(repo).with_suffix("")).replace("/", "."),
            "file": str(py.relative_to(repo)),
            "loc": len(src.splitlines()),
            "functions": functions,
        })
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
