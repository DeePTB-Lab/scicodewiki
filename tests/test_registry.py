import pytest
import yaml

from scicodewiki.registry import (
    FormulaEntry,
    RegistryError,
    append_verdict,
    load_entries,
)

VALID = {
    "id": "demo.prefactor",
    "kind": "algebraic",
    "sympy": "gamma == 18 * pi / hbar**2 * S",
    "implements": {"module": "demo.mod", "function": "kernel"},
    "formula_impl": "demo_prefactor_formula.py",
    "test": {"type": "exact", "tol": 1e-12},
}


def test_valid_entry_parses():
    e = FormulaEntry.from_dict(dict(VALID))
    assert e.id == "demo.prefactor"
    assert e.verdicts == []


@pytest.mark.parametrize("drop", ["id", "kind", "sympy", "implements", "test"])
def test_missing_required_field_rejected(drop):
    data = {k: v for k, v in VALID.items() if k != drop}
    with pytest.raises(RegistryError, match="missing required"):
        FormulaEntry.from_dict(data)


def test_exact_without_formula_impl_rejected():
    data = {k: v for k, v in VALID.items() if k != "formula_impl"}
    with pytest.raises(RegistryError, match="formula_impl"):
        FormulaEntry.from_dict(data)


def test_oracle_needs_no_formula_impl():
    data = {k: (v if k != "test" else {"type": "oracle", "note": "phono3py oracle"})
            for k, v in VALID.items() if k != "formula_impl"}
    e = FormulaEntry.from_dict(data)
    assert e.test["type"] == "oracle"


def test_unknown_field_rejected():
    data = dict(VALID, symppy=VALID["sympy"])  # the classic typo
    with pytest.raises(RegistryError, match="unknown fields"):
        FormulaEntry.from_dict(data)


def test_bad_kind_rejected():
    with pytest.raises(RegistryError, match="kind"):
        FormulaEntry.from_dict(dict(VALID, kind="magic"))


def test_load_entries_skips_staging(tmp_path):
    (tmp_path / "staging").mkdir()
    (tmp_path / "a.yaml").write_text(yaml.safe_dump(VALID), encoding="utf-8")
    staged = dict(VALID, id="demo.staged")
    (tmp_path / "staging" / "s.yaml").write_text(yaml.safe_dump(staged), encoding="utf-8")
    entries = load_entries(tmp_path)
    assert [e.id for e in entries] == ["demo.prefactor"]


def test_append_verdict_roundtrip(tmp_path):
    p = tmp_path / "a.yaml"
    p.write_text(yaml.safe_dump(VALID), encoding="utf-8")
    append_verdict(p, {"at": "2026-08-11", "commit": "abc1234",
                       "seed": 42, "result": "pass"})
    e = load_entries(tmp_path)[0]
    assert e.verdicts[0]["result"] == "pass"
