"""Formula registry: load, validate and append verdicts to entries.

An entry is self-verifiable: it carries the SymPy expression (for rendering
and citation), the code binding, and the executable mirror (``formula_impl``)
the equivalence gate runs. The check is derived from the entry, so the check
cannot drift from the formula.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

KINDS = {"algebraic", "quadrature", "novel", "convention-map"}
TEST_TYPES = {"exact", "convergent", "oracle"}
REQUIRED = ("id", "kind", "sympy", "implements", "test")


class RegistryError(ValueError):
    """Raised on malformed registry entries; message is user-facing."""


@dataclass
class FormulaEntry:
    id: str
    kind: str
    sympy: str
    implements: dict
    test: dict
    latex: str | None = None
    formula_impl: str | None = None
    symbol_identity: list = field(default_factory=list)
    convention_map: list = field(default_factory=list)
    references: list = field(default_factory=list)
    provenance: dict = field(default_factory=dict)
    verdicts: list = field(default_factory=list)
    path: Path | None = field(default=None, compare=False)

    @classmethod
    def from_dict(cls, data: dict, path: Path | None = None) -> "FormulaEntry":
        if not isinstance(data, dict):
            raise RegistryError(f"{path or '<dict>'}: entry must be a mapping")
        missing = [k for k in REQUIRED if k not in data]
        if missing:
            raise RegistryError(
                f"{path or '<dict>'}: missing required fields: {missing}"
            )
        known = set(cls.__dataclass_fields__) - {"path"}
        unknown = set(data) - known
        if unknown:
            raise RegistryError(
                f"{path or '<dict>'}: unknown fields {sorted(unknown)} "
                f"(typo? schema is {sorted(known)})"
            )
        if data["kind"] not in KINDS:
            raise RegistryError(
                f"{path or '<dict>'}: kind {data['kind']!r} not in {sorted(KINDS)}"
            )
        ttype = data["test"].get("type")
        if ttype not in TEST_TYPES:
            raise RegistryError(
                f"{path or '<dict>'}: test.type {ttype!r} not in {sorted(TEST_TYPES)}"
            )
        # executable mirror is what the gate runs; exact/convergent need one
        if ttype in {"exact", "convergent"} and not data.get("formula_impl"):
            raise RegistryError(
                f"{path or '<dict>'}: test.type {ttype!r} requires formula_impl "
                f"(the executable SymPy mirror the gate runs)"
            )
        return cls(**{k: v for k, v in data.items() if k in known}, path=path)


def load_entry(path: Path) -> FormulaEntry:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return FormulaEntry.from_dict(data, path=path)


def load_entries(formulas_dir: Path) -> list[FormulaEntry]:
    """Load all entries; ``staging/`` (agent scratch) is never loaded."""
    formulas_dir = Path(formulas_dir)
    if not formulas_dir.is_dir():
        raise RegistryError(f"no formulas dir at {formulas_dir}")
    entries = []
    for path in sorted(formulas_dir.glob("*.yaml")):
        if path.name == "manifest.yaml":   # pipeline tree, not an entry
            continue
        entries.append(load_entry(path))
    return entries


def append_verdict(path: Path, verdict: dict) -> None:
    """Append one verdict record (the audit corpus + badge source)."""
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    data.setdefault("verdicts", []).append(verdict)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
