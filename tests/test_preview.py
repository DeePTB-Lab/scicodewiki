from scicodewiki.cli import main


def _repo(tmp_path):
    pkg = tmp_path / "demo" / "pkg"
    (pkg / "alpha").mkdir(parents=True)
    (pkg / "beta").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "alpha" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "alpha" / "core.py").write_text("def f():\n    return 1\n",
                                           encoding="utf-8")
    (pkg / "beta" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "beta" / "solvers.py").write_text("def g():\n    return 2\n",
                                             encoding="utf-8")
    return tmp_path / "demo"


def test_preview_generates_code_layer_wiki(tmp_path):
    repo = _repo(tmp_path)
    assert main(["preview", "--repo", str(repo), "--package", "pkg"]) == 0
    index = (repo / "wiki" / "pages" / "index.md").read_text(encoding="utf-8")
    assert "预览" in index
    stages = [p.name for p in (repo / "wiki" / "pages").glob("stage-*.md")]
    assert {"stage-alpha.md", "stage-beta.md"} <= set(stages)
    alpha = (repo / "wiki" / "pages" / "stage-alpha.md").read_text(
        encoding="utf-8")
    assert "pkg.alpha.core" in alpha        # module inventory as content


def test_preview_refuses_over_registry(tmp_path):
    repo = _repo(tmp_path)
    (repo / "wiki" / "formulas").mkdir(parents=True)
    (repo / "wiki" / "formulas" / "manifest.yaml").write_text(
        "repo: demo\nstages: []\n", encoding="utf-8")
    assert main(["preview", "--repo", str(repo), "--package", "pkg"]) == 2
