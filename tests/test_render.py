from pathlib import Path

import pytest
import yaml

from scicodewiki.registry import FormulaEntry
from scicodewiki.render import (
    BADGES,
    build,
    formula_card_md,
    registry_index_md,
)

ENTRY = {
    "id": "demo.x", "kind": "algebraic", "sympy": "g == 18*pi/hbar**2 * S",
    "implements": {"module": "m", "function": "f", "file": "src/m.py"},
    "test": {"type": "oracle", "note": "oracle"},
    "symbol_identity": ["S 为 |V|^2", "Γ 为半线宽（HWHM），cyclic THz"],
    "convention_map": [{"ours": "HWHM", "theirs": "Togo2015 HWHM",
                        "verified_by": "tests/oracles/x.py"}],
    "references": [{"paper": "Togo2015", "where": "PRB 91, 094306"}],
}


def _entry(verdicts=None):
    data = dict(ENTRY)
    if verdicts is not None:
        data = dict(data, verdicts=verdicts)
    return FormulaEntry.from_dict(data)


def test_card_is_pure_documentation():
    card = formula_card_md(_entry())
    assert "`demo.x`" in card
    assert "Togo2015" in card
    assert "HWHM" in card
    assert not any(b in card for b in BADGES.values())  # no badges on reader pages


@pytest.mark.parametrize("state", list(BADGES))
def test_audit_face_keeps_badges(state):
    idx = registry_index_md([_entry()], Path("."))
    assert "⚪" in idx  # unverified for a verdict-less entry


def test_verdict_log_in_audit_face_not_reader_pages():
    from pathlib import Path
    e = _entry([{"at": "2026-08-11", "commit": "abc", "seed": 1,
                 "result": "fail", "diagnosis": "ratio constant at 6"}])
    card = formula_card_md(e)
    assert "ratio constant at 6" not in card      # reader page: no dev log
    idx = registry_index_md([e], Path("."))
    assert "ratio constant at 6" in idx           # audit face keeps diagnosis


def test_index_lists_states(tmp_path):
    e1 = _entry()                                   # unverified
    e2 = _entry([{"at": "a", "commit": "c", "seed": 0, "result": "pass"}])
    idx = registry_index_md([e1, e2], tmp_path)     # no .git -> verified
    assert "⚪" in idx and "✅" in idx


def test_landing_dependency_graph_from_map(tmp_path):
    from scicodewiki.render import dep_mermaid_from_map
    mapping = {"subpackages": {"phonons": {
        "units": [
            {"card": "p.linewidth", "centrality": 3},
            {"card": "p.dynamical", "centrality": 2},
            {"card": "p.mesh", "centrality": 0}],
        "cross_links": [["p.linewidth", "p.dynamical"],
                        ["p.linewidth", "p.mesh"]]}}}
    mer = dep_mermaid_from_map(mapping, top_n=2)
    assert "p.linewidth" in mer and "p.dynamical" in mer
    assert "p.mesh" not in mer                      # below top-N
    assert "flowchart TD" in mer
    assert dep_mermaid_from_map({"subpackages": {}}, 2) == ""


def test_three_level_nav(tmp_path):
    formulas = tmp_path / "wiki" / "formulas"
    formulas.mkdir(parents=True)
    (formulas / "manifest.yaml").write_text(yaml.safe_dump(
        {"repo": "demo", "stages": [
            {"id": "s1", "title": "阶段一", "modules": ["m"],
             "pages": [{"id": "a", "title": "主题甲"},
                       {"id": "b", "title": "主题乙",
                        "formulas": ["demo.x"]}]}]}),
        encoding="utf-8")
    (formulas / "e.yaml").write_text(yaml.safe_dump(ENTRY), encoding="utf-8")
    out = tmp_path / "wiki"
    written = [p.name for p in build(tmp_path, formulas, out)]
    assert {"stage-s1-a.md", "stage-s1-b.md"} <= set(written)
    b = (out / "pages" / "stage-s1-b.md").read_text(encoding="utf-8")
    assert "demo.x" in b and "主题乙" in b
    a = (out / "pages" / "stage-s1-a.md").read_text(encoding="utf-8")
    assert "demo.x" not in a                      # cards only where assigned
    nav_txt = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert "主题甲" in nav_txt and "主题乙" in nav_txt


def test_build_writes_pages(tmp_path):
    formulas = tmp_path / "formulas"
    formulas.mkdir()
    (formulas / "manifest.yaml").write_text(yaml.safe_dump(
        {"repo": "demo", "stages": [
            {"id": "s1", "title": "阶段一", "modules": ["m"]}]}),
        encoding="utf-8")
    (formulas / "e.yaml").write_text(yaml.safe_dump(ENTRY), encoding="utf-8")
    out = tmp_path / "wiki"
    written = [p.name for p in build(tmp_path, formulas, out)]
    assert {"index.md", "stage-s1.md", "registry-index.md", "mkdocs.yml"} \
        <= set(written)
    page = (out / "pages" / "stage-s1.md").read_text(encoding="utf-8")
    assert "阶段一" in page and "demo.x" in page
    # mkdocs.yml carries a !!python/name tag (mermaid fence) -> text asserts
    cfg_txt = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert "docs_dir: pages" in cfg_txt and "mermaid" in cfg_txt
