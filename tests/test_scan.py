import yaml

from scicodewiki.census import scan_package
from scicodewiki.scan import (
    build_map,
    lint_scan,
    locate_function,
    merge_card,
    parse_card,
    skeleton_cards,
    write_scan,
)

BIG_FUNC = "def big_%d():\n" + "    x = 1\n" * 50 + "    return x\n"


def _scan_repo(tmp_path):
    pkg = tmp_path / "demo" / "pkg"
    (pkg / "sub").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core.py").write_text(
        "from pkg.sub import extra\n\n\ndef f():\n    return 1\n",
        encoding="utf-8")
    big = "".join(BIG_FUNC % i for i in range(30))   # ~30*52 > 1500 LOC
    (pkg / "kernel.py").write_text(
        "import numpy as np\n\n\ndef einsum_thing():\n"
        "    return np.einsum('ij,j->i', 1, 1)\n\n\n" + big,
        encoding="utf-8")
    (pkg / "sub" / "extra.py").write_text(
        "from ..core import f\n\n\ndef h():\n    return f() + 2\n",
        encoding="utf-8")
    return tmp_path / "demo"


def test_skeleton_prefilled_from_census(tmp_path):
    repo = _scan_repo(tmp_path)
    census = scan_package(repo, "pkg")
    sk = skeleton_cards(census, repo=repo)
    core = sk["pkg.core"]
    assert core["status"] == "skeleton"
    assert core["unit"] == "pkg.core" and core["file"] == "pkg/core.py"
    assert core["imports"] == ["pkg.sub"]
    assert core["kind_hint"] == "plumbing"
    assert sk["pkg.kernel"]["kind_hint"] == "scientific-kernel"
    assert "purpose" not in core


def test_over_budget_unit_splits(tmp_path):
    repo = _scan_repo(tmp_path)
    census = scan_package(repo, "pkg")
    sk = skeleton_cards(census, budget=1500, repo=repo)
    kernel = sk["pkg.kernel"]
    assert kernel["loc"] > 1500
    assert "pkg.kernel.big_0" in kernel["children"]
    assert "pkg.kernel.big_0" in sk                 # child card exists
    assert "children" not in sk["pkg.core"]


def test_merge_preserves_semantics(tmp_path):
    repo = _scan_repo(tmp_path)
    census = scan_package(repo, "pkg")
    sk = skeleton_cards(census, repo=repo)["pkg.core"]
    old = dict(sk, status="scanned", kind="plumbing",
               purpose="核心入口", conventions=["x"])
    merged = merge_card(old, dict(sk, loc=999))
    assert merged["purpose"] == "核心入口" and merged["conventions"] == ["x"]
    assert merged["loc"] == 999 and merged["status"] == "scanned"


def test_write_scan_and_lint(tmp_path):
    repo = _scan_repo(tmp_path)
    scan_dir = repo / "wiki" / "scan"
    counts = write_scan(repo, "pkg", scan_dir)
    assert counts["skeleton"] == counts["total"]
    assert lint_scan(scan_dir) == []                # skeletons exempt purpose

    # scanned card without purpose -> problem; with purpose -> clean
    card = scan_dir / "pkg.core.md"
    meta, body = parse_card(card.read_text(encoding="utf-8"))
    meta["status"] = "scanned"
    card.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True) +
                    "---\n" + body, encoding="utf-8")
    assert any("missing purpose" in p for p in lint_scan(scan_dir))
    meta["purpose"] = "核心入口函数"
    card.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True) +
                    "---\n" + body, encoding="utf-8")
    assert lint_scan(scan_dir) == []

    meta["purpose"] = "x" * 200
    card.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True) +
                    "---\n" + body, encoding="utf-8")
    assert any("purpose" in p for p in lint_scan(scan_dir))


def test_merge_on_rescan(tmp_path):
    repo = _scan_repo(tmp_path)
    scan_dir = repo / "wiki" / "scan"
    write_scan(repo, "pkg", scan_dir)
    card = scan_dir / "pkg.core.md"
    meta, body = parse_card(card.read_text(encoding="utf-8"))
    meta.update(status="scanned", purpose="核心入口函数")
    card.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True) +
                    "---\n" + body, encoding="utf-8")
    counts = write_scan(repo, "pkg", scan_dir)      # rescan must not clobber
    assert counts["scanned"] == 1
    again, _ = parse_card(card.read_text(encoding="utf-8"))
    assert again["purpose"] == "核心入口函数"


def test_map_aggregation_and_centrality(tmp_path):
    repo = _scan_repo(tmp_path)
    scan_dir = repo / "wiki" / "scan"
    write_scan(repo, "pkg", scan_dir)
    m = build_map(scan_dir, "pkg")
    core_group = m["subpackages"]["pkg.core"]
    assert core_group["loc"] > 0
    assert [u["card"] for u in core_group["units"]] == ["pkg.core"]
    # mechanical edge: pkg.sub.extra imports pkg.core (relative level-2)
    sub_group = m["subpackages"]["pkg.sub"]
    assert ["pkg.sub.extra", "pkg.core"] in [list(e) for e in sub_group["cross_links"]]
    yaml.safe_load((scan_dir / "_map.yaml").read_text(encoding="utf-8"))


def test_kind_hint_generalized(tmp_path):
    pkg = tmp_path / "demo2" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "hamiltonian_builder.py").write_text(
        "def build():\n    return 1\n", encoding="utf-8")   # name mark only
    (pkg / "dataset.py").write_text(
        "import numpy as np\n\n\ndef load():\n    return np.sqrt(2)\n",
        encoding="utf-8")                                    # weak mark only
    census = scan_package(tmp_path / "demo2", "pkg")
    sk = skeleton_cards(census, repo=tmp_path / "demo2")
    assert sk["pkg.hamiltonian_builder"]["kind_hint"] == "scientific-kernel"
    assert sk["pkg.dataset"]["kind_hint"] == "plumbing"     # A: no np.sqrt FP


def test_tiny_classes_folded(tmp_path):
    pkg = tmp_path / "demo3" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    big = "".join(BIG_FUNC % i for i in range(30))
    (pkg / "core.py").write_text(
        "class Tiny:\n    def m(self):\n        return 1\n\n\n" + big,
        encoding="utf-8")
    census = scan_package(tmp_path / "demo3", "pkg")
    sk = skeleton_cards(census, budget=1500, repo=tmp_path / "demo3")
    assert "pkg.core.Tiny" not in sk                        # I: 3-LOC class folded
    assert "pkg.core.big_0" in sk


def _git(repo, *args):
    import subprocess
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, env={"HOME": str(repo),
                                             "GIT_AUTHOR_NAME": "t",
                                             "GIT_AUTHOR_EMAIL": "t@t",
                                             "GIT_COMMITTER_NAME": "t",
                                             "GIT_COMMITTER_EMAIL": "t@t"})


def test_drift_cards_reset_on_change(tmp_path):
    from scicodewiki.cli import main
    from scicodewiki.scan import parse_card

    repo = _scan_repo(tmp_path)
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c1")
    scan_dir = repo / "wiki" / "scan"
    write_scan(repo, "pkg", scan_dir)
    card = scan_dir / "pkg.core.md"
    meta, body = parse_card(card.read_text(encoding="utf-8"))
    meta["status"] = "scanned"
    meta["purpose"] = "核心"
    card.write_text("---\n" + yaml.safe_dump(meta, allow_unicode=True) +
                    "---\n" + body, encoding="utf-8")

    (repo / "pkg" / "core.py").write_text(
        (repo / "pkg" / "core.py").read_text(encoding="utf-8") +
        "\n# drift\n", encoding="utf-8")
    _git(repo, "commit", "-aqm", "c2")
    assert main(["drift-cards", "--repo", str(repo)]) == 0
    again, _ = parse_card(card.read_text(encoding="utf-8"))
    assert again["status"] == "skeleton"          # reset for rescan
    assert again["purpose"] == "核心"             # semantics kept


def test_locate_function_drift_immune(tmp_path):
    repo = _scan_repo(tmp_path)
    start, end = locate_function(repo, "pkg.core", "f")
    assert (start, end) == (4, 5)
    core = repo / "pkg" / "core.py"
    core.write_text("\n\n# header drift\n" + core.read_text(encoding="utf-8"),
                    encoding="utf-8")
    start2, end2 = locate_function(repo, "pkg.core", "f")
    assert (start2, end2) == (7, 8)                # found by name, not stale line
