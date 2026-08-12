import yaml

from scicodewiki.cli import main
from scicodewiki.consistency import (
    card_coverage,
    check_repo,
    duplication_problems,
    glossary_problems,
    link_problems,
    phantom_card_refs,
    thesis_problems,
)

LONG = "这是一段足够长的、用于重复检测的段落文字，" * 12   # >200 chars


def _write_card(scan_dir, cid, kind="scientific-kernel", **kw):
    scan_dir.mkdir(parents=True, exist_ok=True)
    meta = {"card": cid, "kind": kind, "status": "scanned",
            "unit": cid, "file": f"{cid.split('.')[-1]}.py", "loc": 10,
            "purpose": "x", **kw}
    (scan_dir / f"{cid}.md").write_text(
        "---\n" + yaml.safe_dump(meta, allow_unicode=True) + "---\n",
        encoding="utf-8")
    return meta


def _wiki(tmp_path, cards=("a", "b"), alloc=("a",), theses=None,
          narratives=None):
    repo = tmp_path / "demo"
    scan_dir = repo / "wiki" / "scan"
    metas = [_write_card(scan_dir, f"m.{c}") for c in cards]
    _write_card(scan_dir, "m.p", kind="plumbing")
    formulas = repo / "wiki" / "formulas"
    formulas.mkdir(parents=True)
    pages = {"id": "s", "title": "t", "modules": ["m"],
             "cards": [f"m.{c}" for c in alloc]}
    if theses:
        pages["thesis"] = theses[0]
    (formulas / "manifest.yaml").write_text(yaml.safe_dump(
        {"repo": "demo", "stages": [pages]}, allow_unicode=True),
        encoding="utf-8")
    narr = repo / "wiki" / "narratives"
    narr.mkdir(parents=True)
    for name, text in (narratives or {}).items():
        (narr / name).write_text(text, encoding="utf-8")
    return repo, metas


def test_card_coverage_and_phantom(tmp_path):
    repo, metas = _wiki(tmp_path, cards=("a", "b"), alloc=("a",))
    from scicodewiki.manifest import load_manifest
    manifest = load_manifest(repo / "wiki" / "formulas" / "manifest.yaml")
    cov = card_coverage(metas, manifest)
    assert cov == ["unallocated kernel card: m.b"]
    man2 = dict(manifest, stages=[dict(manifest["stages"][0],
                                       cards=["m.a", "m.b", "m.ghost"])])
    assert phantom_card_refs(man2, {m["card"] for m in metas}) == \
        ["phantom card ref (not in wiki/scan): m.ghost"]


def test_thesis_response(tmp_path):
    repo, _ = _wiki(tmp_path, alloc=("a", "b"), theses=["本页回答：线宽从哪来？"],
                    narratives={"s.md": "# t\n\n无关开头。\n\n更多。"})
    from scicodewiki.manifest import load_manifest
    manifest = load_manifest(repo / "wiki" / "formulas" / "manifest.yaml")
    assert thesis_problems(manifest, repo / "wiki" / "narratives")
    (repo / "wiki" / "narratives" / "s.md").write_text(
        "# t\n\n本页回答：线宽从哪来？……\n", encoding="utf-8")
    assert not thesis_problems(manifest, repo / "wiki" / "narratives")


def test_glossary_and_duplication(tmp_path):
    repo, metas = _wiki(tmp_path, alloc=("a", "b"))
    metas[0]["terms"] = {"半高半宽（HWHM）": ["半峰宽"]}
    narr = repo / "wiki" / "narratives"
    (narr / "s.md").write_text(f"用半峰宽描述。\n\n{LONG}\n", encoding="utf-8")
    (narr / "x.md").write_text(f"另一页。\n\n{LONG}\n", encoding="utf-8")
    assert glossary_problems(metas, narr)
    assert duplication_problems(narr)


def test_terms_str_value_tolerated(tmp_path):
    repo, metas = _wiki(tmp_path, alloc=("a", "b"))
    metas[0]["terms"] = {"半高半宽（HWHM）": "半峰宽"}     # E: str, not list
    narr = repo / "wiki" / "narratives"
    narr.mkdir(exist_ok=True)
    (narr / "s.md").write_text("用半峰宽描述。\n", encoding="utf-8")
    assert glossary_problems(metas, narr)                # no crash, flagged


def test_links(tmp_path):
    repo, _ = _wiki(tmp_path, alloc=("a", "b"))
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "01.md").write_text("# d\n", encoding="utf-8")
    narr = repo / "wiki" / "narratives"
    (narr / "s.md").write_text(
        "[ok](../../docs/01.md) [bad](../../docs/99.md)\n", encoding="utf-8")
    probs = link_problems(narr, repo)
    assert probs == ["s.md: broken link ../../docs/99.md"]


def test_cli_consistency_exit_codes(tmp_path):
    repo, _ = _wiki(tmp_path, cards=("a",), alloc=("a",))
    assert main(["consistency", "--repo", str(repo)]) == 0
    # unallocated kernel -> exit 1
    _write_card(repo / "wiki" / "scan", "m.b")
    assert main(["consistency", "--repo", str(repo)]) == 1
    # no scan dir -> guidance, exit 1
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main(["consistency", "--repo", str(empty)]) == 1


def test_check_repo_degrades_without_manifest_cards(tmp_path):
    repo, _ = _wiki(tmp_path, alloc=())
    assert any("outline" in p for p in check_repo(repo))


def test_cards_only_skips_thesis(tmp_path):
    repo, _ = _wiki(tmp_path, alloc=("a", "b"), theses=["本页回答：Q？"],
                    narratives={})
    assert check_repo(repo)                 # thesis without narrative yet
    assert not check_repo(repo, cards_only=True)   # outline-stage gate


def test_exclusions_mechanical(tmp_path):
    repo, _ = _wiki(tmp_path, alloc=("a", "b"))
    mpath = repo / "wiki" / "formulas" / "manifest.yaml"
    m = yaml.safe_load(mpath.read_text(encoding="utf-8"))
    m["stages"][0]["excluded_cards"] = [{"card": "m.p", "note": "plumbing"}]
    mpath.write_text(yaml.safe_dump(m, allow_unicode=True), encoding="utf-8")
    assert check_repo(repo, cards_only=True) == []
    m["stages"][0]["excluded_cards"] = ["m.a"]      # kernel exclusion = defect
    mpath.write_text(yaml.safe_dump(m, allow_unicode=True), encoding="utf-8")
    assert any("cannot be excluded" in p
               for p in check_repo(repo, cards_only=True))
