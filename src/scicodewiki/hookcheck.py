"""Edit-hook core: if an edited file is bound to a registry entry, run the
gate and report. Shared by the plugin PostToolUse hook and `on-edit` CLI.
Drift closes in the very session that caused it. Non-blocking."""
import json
import sys
from pathlib import Path

from .registry import RegistryError, load_entries
from .verify import run_gate


def check_edit(data: dict) -> int:
    edited = (data.get("tool_input") or {}).get("file_path", "")
    if not edited:
        return 0
    repo = Path(data.get("cwd") or ".").resolve()
    formulas = repo / "formulas"
    if not formulas.is_dir():
        return 0
    try:
        entries = load_entries(formulas)
    except RegistryError:
        return 0
    for entry in entries:
        bound = entry.implements.get("file")
        if not bound or not edited.endswith(bound):
            continue
        if not entry.formula_impl or entry.test.get("type") == "oracle":
            print(f"scicodewiki: {entry.id} binds this file "
                  f"(oracle-endorsed; run verify to refresh badge)")
            continue
        verdict = run_gate(entry, formulas, seed=0)
        if verdict.result == "fail":
            print(f"scicodewiki: your edit breaks {entry.id} -- "
                  f"{verdict.diagnosis}")
        else:
            print(f"scicodewiki: {entry.id} still equivalent after your edit")
    return 0


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    return check_edit(data)
