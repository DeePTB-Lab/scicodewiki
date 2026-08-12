import subprocess
import textwrap

import pytest
import yaml

from scicodewiki import drift
from scicodewiki.registry import load_entries
from scicodewiki.verify import run_gate, verify_repo

PASS_IMPL = textwrap.dedent("""
    import numpy as np
    C = 18 * np.pi

    def sample(rng):
        return {"s": rng.random(50) + 1.0}

    def mirror(ctx):
        return C * ctx["s"]

    def target(ctx):
        return C * ctx["s"]
""")

DRIFT_IMPL = PASS_IMPL.replace("def target(ctx):\n    return C * ctx[\"s\"]",
                                "def target(ctx):\n    return 6 * C * ctx[\"s\"]")

STRUCT_IMPL = PASS_IMPL.replace("def target(ctx):\n    return C * ctx[\"s\"]",
                                "def target(ctx):\n    return C * ctx[\"s\"] ** 2")

# SI-scale magnitudes: a vacuous atol must not hide a factor-6 drift
TINY_IMPL = textwrap.dedent("""
    import numpy as np
    C = 1e-127

    def sample(rng):
        return {"s": rng.random(50) + 1.0}

    def mirror(ctx):
        return C * ctx["s"]

    def target(ctx):
        return 6 * C * ctx["s"]
""")


def _write_formulas(tmp_path, impl_src, entry_id="demo.x"):
    formulas = tmp_path / "wiki" / "formulas"
    formulas.mkdir(parents=True, exist_ok=True)
    (formulas / "impl.py").write_text(impl_src, encoding="utf-8")
    entry = {
        "id": entry_id, "kind": "algebraic", "sympy": "gamma == C * s",
        "implements": {"module": "m", "function": "f", "file": "src/m.py"},
        "formula_impl": "impl.py",
        "test": {"type": "exact", "tol": 1e-12},
    }
    (formulas / "e.yaml").write_text(yaml.safe_dump(entry), encoding="utf-8")
    return formulas


def test_exact_pass(tmp_path):
    formulas = _write_formulas(tmp_path, PASS_IMPL)
    entry = load_entries(formulas)[0]
    v = run_gate(entry, formulas, seed=1)
    assert v.result == "pass"


def test_constant_ratio_diagnosed_as_missing_factor(tmp_path):
    formulas = _write_formulas(tmp_path, DRIFT_IMPL)
    entry = load_entries(formulas)[0]
    v = run_gate(entry, formulas, seed=1)
    assert v.result == "fail"
    assert "constant at 6" in v.diagnosis
    assert "3! = 6" in v.diagnosis


def test_si_scale_drift_not_hidden_by_atol(tmp_path):
    formulas = _write_formulas(tmp_path, TINY_IMPL)
    entry = load_entries(formulas)[0]
    v = run_gate(entry, formulas, seed=1)
    assert v.result == "fail"
    assert "constant at 6" in v.diagnosis


def test_structural_difference_diagnosed(tmp_path):
    formulas = _write_formulas(tmp_path, STRUCT_IMPL)
    entry = load_entries(formulas)[0]
    v = run_gate(entry, formulas, seed=1)
    assert v.result == "fail"
    assert "structural difference" in v.diagnosis


def test_verify_repo_records_verdicts(tmp_path):
    formulas = _write_formulas(tmp_path, PASS_IMPL)
    results = verify_repo(formulas, commit="abc1234", seed=7)
    assert results[0][1].result == "pass"
    entry = load_entries(formulas)[0]
    assert entry.verdicts[-1] == {
        "at": entry.verdicts[-1]["at"], "commit": "abc1234",
        "seed": 7, "result": "pass",
    }


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, env={"HOME": str(repo),
                                             "GIT_AUTHOR_NAME": "t",
                                             "GIT_AUTHOR_EMAIL": "t@t",
                                             "GIT_COMMITTER_NAME": "t",
                                             "GIT_COMMITTER_EMAIL": "t@t"})


COMPLEX_IMPL = textwrap.dedent("""
    import numpy as np

    def sample(rng):
        a = rng.normal(3) + 1j * rng.normal(3)
        return {"e": a}

    def mirror(ctx):
        return np.abs(ctx["e"]) ** 2          # V*conj(V), complex-native

    def target(ctx):
        return (ctx["e"] * np.conj(ctx["e"])).real
""")


def test_gate_handles_complex_fields(tmp_path):
    formulas = _write_formulas(tmp_path, COMPLEX_IMPL)
    entry = load_entries(formulas)[0]
    v = run_gate(entry, formulas, seed=3)
    assert v.result == "pass"


def test_promote_gate_driven(tmp_path):
    from scicodewiki.cli import main

    formulas = tmp_path / "wiki" / "formulas"
    staging = formulas / "staging"
    staging.mkdir(parents=True)
    (staging / "impl.py").write_text(PASS_IMPL, encoding="utf-8")
    entry = {
        "id": "demo.x", "kind": "algebraic", "sympy": "g == C * s",
        "implements": {"module": "m", "function": "f"},
        "formula_impl": "impl.py",
        "test": {"type": "exact", "tol": 1e-12},
    }
    (staging / "demo.x.yaml").write_text(yaml.safe_dump(entry),
                                         encoding="utf-8")
    assert main(["promote", "--repo", str(tmp_path),
                 "--entry", "demo.x", "--seed", "1"]) == 0
    assert (formulas / "demo.x.yaml").exists()
    assert not (staging / "demo.x.yaml").exists()

    (staging / "impl2.py").write_text(DRIFT_IMPL, encoding="utf-8")
    (staging / "demo.y.yaml").write_text(
        yaml.safe_dump(dict(entry, id="demo.y", formula_impl="impl2.py")),
        encoding="utf-8")
    assert main(["promote", "--repo", str(tmp_path),
                 "--entry", "demo.y", "--seed", "1"]) == 1
    assert not (formulas / "demo.y.yaml").exists()   # fail stays staged

    # D: fresh-random default seed must not NameError
    (staging / "impl.py").write_text(PASS_IMPL, encoding="utf-8")
    (staging / "demo.z.yaml").write_text(
        yaml.safe_dump(dict(entry, id="demo.z", formula_impl="impl.py")),
        encoding="utf-8")
    assert main(["promote", "--repo", str(tmp_path),
                 "--entry", "demo.z"]) == 0


def test_badge_states_lifecycle(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    formulas = repo / "wiki" / "formulas"
    _write_formulas(repo, PASS_IMPL)
    (repo / "src" / "m.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c1")
    c1 = drift.head_commit(repo)

    verify_repo(formulas, commit=c1, seed=1)
    entry = load_entries(formulas)[0]
    assert drift.badge_state(entry, repo) == "verified"

    # bound file changes -> stale
    (repo / "src" / "m.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "commit", "-aqm", "c2")
    entry = load_entries(formulas)[0]
    assert drift.badge_state(entry, repo) == "stale"

    # re-verify at c2, then unrelated file changes -> still verified
    verify_repo(formulas, commit=drift.head_commit(repo), seed=2)
    (repo / "README").write_text("hi\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c3")
    entry = load_entries(formulas)[0]
    assert drift.badge_state(entry, repo) == "verified"
