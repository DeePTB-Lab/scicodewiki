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
    "symbol_identity": ["S 为 |V|^2"],
    "convention_map": [{"ours": "HWHM", "theirs": "Togo2015 HWHM",
                        "verified_by": "tests/oracles/x.py"}],
    "references": [{"paper": "Togo2015", "where": "PRB 91, 094306"}],
}


def _entry(verdicts=None):
    data = dict(ENTRY)
    if verdicts is not None:
        data = dict(data, verdicts=verdicts)
    return FormulaEntry.from_dict(data)


@pytest.mark.parametrize("state", list(BADGES))
def test_card_renders_each_badge_state(state):
    card = formula_card_md(_entry(), state)
    assert BADGES[state] in card
    assert "`demo.x`" in card
    assert "Togo2015" in card
    assert "HWHM" in card


def test_verdict_log_in_audit_face_not_reader_pages():
    from pathlib import Path
    e = _entry([{"at": "2026-08-11", "commit": "abc", "seed": 1,
                 "result": "fail", "diagnosis": "ratio constant at 6"}])
    card = formula_card_md(e, "failing")
    assert "ratio constant at 6" not in card      # reader page: badge only
    idx = registry_index_md([e], Path("."))
    assert "ratio constant at 6" in idx           # audit face keeps diagnosis


def test_index_lists_states(tmp_path):
    e1 = _entry()                                   # unverified
    e2 = _entry([{"at": "a", "commit": "c", "seed": 0, "result": "pass"}])
    idx = registry_index_md([e1, e2], tmp_path)     # no .git -> verified
    assert "⚪" in idx and "✅" in idx


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
