from test_verify import _write_formulas

from scicodewiki import mcp_server as M


def test_mcp_tools_on_fake_repo(tmp_path):
    repo = tmp_path / "demo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    _write_formulas(repo, "def mirror(ctx):\n    return 1\n")
    entries = M.list_entries(str(repo))
    assert entries and entries[0]["id"] == "demo.x"

    e = M.get_entry(str(repo), "demo.x")
    assert e["kind"] == "algebraic" and "verdicts" not in e

    assert M.verdicts(str(repo), "demo.x") == []
    assert M.find_bindings(str(repo), "pkg") == []     # impl module is "m"
    assert M.find_bindings(str(repo), "m")[0]["id"] == "demo.x"

    cov = M.coverage_summary(str(repo), "pkg")
    assert isinstance(cov["undocumented"], list)

    assert M.get_entry(str(repo), "nope") == {}
    assert M.card(str(repo), "nope") == {}
