"""Pipeline manifest: the physical-workflow tree that drives nav and scope.

The wiki's top-level organization follows the science workflow
(e.g. relax -> FC2 -> FC3 -> linewidth), not the import structure.
v0: handwritten; v1: agent-inferred with human confirmation (and seeded
by the preview-mode tree).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .registry import RegistryError


def load_manifest(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "repo" not in data or "stages" not in data:
        raise RegistryError(f"{path}: manifest requires 'repo' and 'stages'")
    for i, stage in enumerate(data["stages"]):
        if "id" not in stage or "title" not in stage:
            raise RegistryError(f"{path}: stage #{i} requires 'id' and 'title'")
    return data
