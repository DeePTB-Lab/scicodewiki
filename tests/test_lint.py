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


def test_over_budget_function_granular():
    census = {"units": [{"module": "pkg.big", "file": "f", "loc": 3954,
                         "functions": [{"name": "tiny", "loc": 50}],
                         "classes": [], "imports": []}]}
    manifest = {"stages": [{"id": "s", "title": "t", "modules": ["pkg.big"],
                           "pages": [{"id": "algorithm", "title": "a",
                                      "formulas": ["demo.x"]}]}]}
    small = FormulaEntry.from_dict(dict(
        ENTRY, implements={"module": "pkg.big", "function": "tiny"}))
    assert over_budget(census, manifest, [small]) == []      # F6
    whole = FormulaEntry.from_dict(ENTRY)                    # no function
    assert over_budget(census, manifest, [whole])[0]["loc"] == 3954


def test_over_budget_flags_hot_subpage():
    census = {"units": [{"module": "pkg.big", "file": "f", "loc": 3800,
                        "functions": []}]}
    manifest = {"stages": [{"id": "s", "title": "t", "modules": ["pkg.big"],
                           "pages": [{"id": "algorithm", "title": "a",
                                      "formulas": ["demo.x"]}]}]}
    hot = over_budget(census, manifest, [FormulaEntry.from_dict(ENTRY)])
    assert hot == [{"stage": "s", "page": "algorithm", "loc": 3800}]


def test_density_gate(tmp_path):
    from scicodewiki.lint import density_problems

    nd = tmp_path / "narratives"
    nd.mkdir()
    manifest = {"stages": [{"id": "s", "title": "t",
                           "modules": ["pkg.alpha", "pkg.beta"],
                           "pages": [{"id": "algorithm", "title": "a"}]}]}
    (nd / "s-algorithm.md").write_text("# t\n\n## x\n\nshort.\n",
                                       encoding="utf-8")
    probs = density_problems(nd, manifest)
    assert any("thin page" in p for p in probs)
    assert any("pkg.alpha" in p for p in probs)
    assert any("code-map" in p for p in probs)

    dense = ("## code map\n\n| f | role |\n|---|---|\n| x | y |\n\n"
             + "alpha " * 800 + "beta " * 800)
    (nd / "s-algorithm.md").write_text("# t\n\n" + dense, encoding="utf-8")
    assert density_problems(nd, manifest) == []
