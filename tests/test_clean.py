from scicodewiki.cli import main


def test_clean_wipes_entire_wiki_keeps_repo_content(tmp_path):
    wiki = tmp_path / "wiki"
    for d in ("formulas", "pages", "_site", "narratives"):
        (wiki / d).mkdir(parents=True)
    (wiki / "formulas" / "e.yaml").write_text("id: x\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()                        # repo's own content
    (tmp_path / "docs" / "01.md").write_text("# d\n", encoding="utf-8")

    assert main(["clean", "--repo", str(tmp_path)]) == 0

    assert not wiki.exists()                           # ALL outputs gone
    assert (tmp_path / "docs" / "01.md").exists()      # repo content kept
