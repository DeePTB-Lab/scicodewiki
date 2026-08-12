"""MCP server: the registry + scan cards as a structured knowledge source.

Lets any conversation (not just a skill run) query bindings, verdicts and
coverage without parsing YAML by hand. Read-only by design — the gates
stay in the CLI.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .census import over_budget, scan_package, undocumented
from .consistency import load_cards
from .drift import badge_state
from .manifest import load_manifest
from .registry import load_entries

mcp = FastMCP("scicodewiki")


def _wiki(repo: str) -> Path:
    return Path(repo).resolve() / "wiki"


@mcp.tool()
def list_entries(repo: str) -> list[dict]:
    """All registry entries: id, kind, badge state."""
    wiki = _wiki(repo)
    formulas = wiki / "formulas"
    if not formulas.is_dir():
        return []
    return [{"id": e.id, "kind": e.kind,
             "state": badge_state(e, Path(repo).resolve())}
            for e in load_entries(formulas)]


@mcp.tool()
def get_entry(repo: str, entry_id: str) -> dict:
    """Full entry (sympy, implements, symbol_identity, convention_map,
    references) minus verdict history — use verdicts() for that."""
    for e in load_entries(_wiki(repo) / "formulas"):
        if e.id == entry_id:
            d = {k: v for k, v in e.__dict__.items()
                 if k not in ("path", "verdicts")}
            return d
    return {}


@mcp.tool()
def verdicts(repo: str, entry_id: str) -> list[dict]:
    """Verdict history of one entry (the audit trail)."""
    for e in load_entries(_wiki(repo) / "formulas"):
        if e.id == entry_id:
            return e.verdicts
    return []


@mcp.tool()
def find_bindings(repo: str, module_prefix: str) -> list[dict]:
    """Registry entries whose bound implementation module starts with the
    prefix — 'which formulas live in this code?'"""
    return [{"id": e.id, "function": e.implements.get("function"),
             "state": badge_state(e, Path(repo).resolve())}
            for e in load_entries(_wiki(repo) / "formulas")
            if e.implements.get("module", "").startswith(module_prefix)]


@mcp.tool()
def card(repo: str, card_id: str) -> dict:
    """One scan card (the understanding artifact)."""
    for c in load_cards(_wiki(repo) / "scan"):
        if c.get("card") == card_id:
            return {k: v for k, v in c.items() if k != "_path"}
    return {}


@mcp.tool()
def coverage_summary(repo: str, package: str) -> dict:
    """Documentation coverage: undocumented modules + over-budget pages."""
    r = Path(repo).resolve()
    wiki = _wiki(repo)
    census = scan_package(r, package)
    manifest_path = wiki / "formulas" / "manifest.yaml"
    if not manifest_path.exists():
        return {"undocumented": [u["module"] for u in census["units"]],
                "over_budget": []}
    manifest = load_manifest(manifest_path)
    entries = load_entries(wiki / "formulas") \
        if (wiki / "formulas").is_dir() else []
    return {"undocumented": [u["module"] for u in undocumented(census, manifest)],
            "over_budget": over_budget(census, manifest, entries)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
