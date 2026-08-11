"""Drift maintenance: badge states from verdict records + git freshness.

Honesty without CI: a verdict is trusted for exactly the code it was run
against. If the bound file changed after the last verdict, the entry is
stale — the wiki says so instead of silently showing an old badge.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .registry import FormulaEntry

STATES = ("verified", "stale", "failing", "unverified")


def head_commit(repo: Path) -> str | None:
    r = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def badge_state(entry: FormulaEntry, repo: Path) -> str:
    if not entry.verdicts:
        return "unverified"
    last = entry.verdicts[-1]
    if last.get("result") != "pass":
        return "failing"
    commit = last.get("commit")
    bound = entry.implements.get("file")
    head = head_commit(repo)
    if not commit or not head or not bound or commit == head:
        return "verified"
    r = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", commit, "HEAD", "--", bound],
        capture_output=True, text=True,
    )
    if r.returncode == 0 and r.stdout.strip():
        return "stale"
    return "verified"
