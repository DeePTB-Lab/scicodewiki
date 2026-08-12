import textwrap

import yaml

from scicodewiki.audit import audit

PASS_M = textwrap.dedent("""
    import numpy as np
    C = 18 * np.pi

    def sample(rng):
        return {"s": rng.random(10) + 1.0}

    def mirror(ctx):
        return C * ctx["s"]

    def target(ctx):
        return C * ctx["s"]
""")

DRIFT_M = PASS_M.replace("def target(ctx):\n    return C * ctx[\"s\"]",
                         "def target(ctx):\n    return 6 * C * ctx[\"s\"]")


def _claims(tmp_path):
    cd = tmp_path / "claims"
    cd.mkdir()
    (cd / "m_pass.py").write_text(PASS_M, encoding="utf-8")
    (cd / "m_drift.py").write_text(DRIFT_M, encoding="utf-8")
    (cd / "c1.yaml").write_text(yaml.safe_dump({
        "id": "g.c1", "binds": {"module": "m", "function": "f"},
        "sympy": "g == C*s", "taxonomy": "prefactor",
        "formula_impl": "m_pass.py"}), encoding="utf-8")
    (cd / "c2.yaml").write_text(yaml.safe_dump({
        "id": "g.c2", "binds": {"module": "m", "function": "f"},
        "sympy": "g == 6*C*s", "taxonomy": "prefactor",
        "formula_impl": "m_drift.py"}), encoding="utf-8")
    (cd / "c3.yaml").write_text(yaml.safe_dump({
        "id": "g.c3", "binds": {"module": "m", "function": "f"},
        "sympy": "prose-only", "taxonomy": "convention"}),
        encoding="utf-8")
    return cd


DET_M = textwrap.dedent("""
    def mirror():
        return 6.0

    def target():
        return 6.0
""")


def test_deterministic_contract_without_sample(tmp_path):
    cd = tmp_path / "claims"
    cd.mkdir()
    (cd / "m_det.py").write_text(DET_M, encoding="utf-8")
    (cd / "c.yaml").write_text(yaml.safe_dump({
        "id": "g.det", "binds": {"module": "m", "function": "f"},
        "sympy": "x == 6", "taxonomy": "prefactor",
        "formula_impl": "m_det.py"}), encoding="utf-8")
    s = audit(cd, seed=0)
    assert s["totals"]["pass"] == 1


def test_audit_verdicts_and_taxonomy(tmp_path):
    cd = _claims(tmp_path)
    s = audit(cd, seed=5)
    by_id = {v["id"]: v for v in s["verdicts"]}
    assert by_id["g.c1"]["result"] == "pass"
    assert by_id["g.c2"]["result"] == "fail"
    assert "3! = 6" in by_id["g.c2"]["diagnosis"]
    assert by_id["g.c3"]["result"] == "unverifiable"
    assert s["totals"] == {"claims": 3, "fail": 1, "pass": 1,
                           "unverifiable": 1}
    assert s["taxonomy"]["prefactor"]["fail"] == 1
