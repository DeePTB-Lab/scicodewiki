from scicodewiki.census import over_budget
from scicodewiki.lint import lint_narratives
from scicodewiki.registry import FormulaEntry

ENTRY = {
    "id": "demo.x", "kind": "algebraic", "sympy": "g == 1",
    "implements": {"module": "pkg.big", "function": "f"},
    "test": {"type": "oracle", "note": "n"},
}


def test_forbidden_machine_vocabulary(tmp_path):
    nd = tmp_path / "narratives"
    nd.mkdir()
    (nd / "x-physics.md").write_text(
        "# t\n\n本节 ✅ verified，verdict 见注册表。\n", encoding="utf-8")
    probs = lint_narratives(nd)
    assert any("verified" in p or "verdict" in p for p in probs)
    assert any("✅" in p for p in probs)


def test_algorithm_requires_mermaid(tmp_path):
    nd = tmp_path / "narratives"
    nd.mkdir()
    (nd / "x-algorithm.md").write_text("# t\n\n散文。\n", encoding="utf-8")
    assert any("mermaid" in p for p in lint_narratives(nd))


def test_quant_block_needs_citation(tmp_path):
    nd = tmp_path / "narratives"
    nd.mkdir()
    (nd / "x-benchmarks.md").write_text(
        "# t\n\n相对差 0.0031，很好。\n", encoding="utf-8")
    assert any("citation" in p for p in lint_narratives(nd))
    (nd / "x-benchmarks.md").write_text(
        "# t\n\n相对差 0.0031（docs/10 §4）。\n", encoding="utf-8")
    assert not lint_narratives(nd)


def test_clean_narrative_passes(tmp_path):
    nd = tmp_path / "narratives"
    nd.mkdir()
    (nd / "x-algorithm.md").write_text(
        "# t\n\n```mermaid\nflowchart TD\n  A-->B\n```\n", encoding="utf-8")
    assert lint_narratives(nd) == []


def test_over_budget_flags_hot_subpage():
    census = {"units": [{"module": "pkg.big", "file": "f", "loc": 3800,
                        "functions": []}]}
    manifest = {"stages": [{"id": "s", "title": "t", "modules": ["pkg.big"],
                           "pages": [{"id": "algorithm", "title": "a",
                                      "formulas": ["demo.x"]}]}]}
    hot = over_budget(census, manifest, [FormulaEntry.from_dict(ENTRY)])
    assert hot == [{"stage": "s", "page": "algorithm", "loc": 3800}]
