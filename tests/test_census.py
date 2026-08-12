import json

import yaml

from scicodewiki.census import scan_package, undocumented, write_census
from scicodewiki.cli import main


def _fake_repo(tmp_path):
    pkg = tmp_path / "demo" / "pkg"
    (pkg / "sub").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core.py").write_text(
        "from pkg.sub import extra\n\n\n"
        "class Widget:\n"
        "    def spin(self):\n"
        "        return 1\n\n\n"
        "def f():\n    return 1\n\n\ndef g():\n    return 2\n",
        encoding="utf-8")
    (pkg / "sub" / "extra.py").write_text(
        "from ..core import f\n\n\ndef h():\n    return f() + 2\n",
        encoding="utf-8")
    return tmp_path / "demo"


def test_scan_inventory(tmp_path):
    repo = _fake_repo(tmp_path)
    census = scan_package(repo, "pkg")
    mods = {u["module"] for u in census["units"]}
    assert {"pkg.core", "pkg.sub.extra"} <= mods
    core = next(u for u in census["units"] if u["module"] == "pkg.core")
    assert {f["name"] for f in core["functions"]} >= {"f", "g", "spin"}
    assert core["classes"] == [{"name": "Widget", "loc": 3,
                                "methods": ["spin"]}]


def test_mechanical_import_edges(tmp_path):
    repo = _fake_repo(tmp_path)
    census = scan_package(repo, "pkg")
    core = next(u for u in census["units"] if u["module"] == "pkg.core")
    extra = next(u for u in census["units"] if u["module"] == "pkg.sub.extra")
    assert core["imports"] == ["pkg.sub"]          # absolute, prefix edge
    assert extra["imports"] == ["pkg.core"]        # relative level-2 resolved


def test_undocumented_gaps(tmp_path):
    repo = _fake_repo(tmp_path)
    census = scan_package(repo, "pkg")
    manifest = {"stages": [{"id": "s", "title": "t",
                           "modules": ["pkg.core"]}]}
    gaps = undocumented(census, manifest)
    assert [u["module"] for u in gaps] == ["pkg.sub.extra"]


def test_cli_census_and_coverage(tmp_path, capsys):
    repo = _fake_repo(tmp_path)
    formulas = repo / "wiki" / "formulas"
    formulas.mkdir(parents=True)
    (formulas / "manifest.yaml").write_text(yaml.safe_dump(
        {"repo": "demo", "stages": [
            {"id": "s", "title": "t", "modules": ["pkg.core"]}]}),
        encoding="utf-8")
    assert main(["census", "--repo", str(repo), "--package", "pkg"]) == 0
    assert json.loads((repo / "wiki" / ".census.json").read_text())["units"]
    assert main(["coverage", "--repo", str(repo), "--package", "pkg"]) == 0
    out = capsys.readouterr().out
    assert "undocumented: pkg.sub.extra" in out
    assert "1 undocumented modules" in out
