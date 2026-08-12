"""Audit: mechanically judge formula claims extracted from ANY wiki.

The C2 metric prototype. Claims are PROPOSED by the audit-extract skill
(agent reads some generator's wiki, emits claim YAMLs with a mirror when
possible); this module is the deterministic judge:

- claim with mirror  -> equivalence gate vs the REAL code (fail = the wiki
  misstates the implementation; ratio diagnosis says how);
- claim without mirror -> 'unverifiable' (needs human/LLM taxonomy labelling);
taxonomy labels (claim kind, not verdict) aggregate into the audit table.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .registry import FormulaEntry
from .verify import run_gate

TAXONOMY = ("prefactor", "symbol-identity", "convention", "coverage",
            "innovation", "other")


def load_claims(claims_dir: Path) -> list[dict]:
    claims = []
    for y in sorted(Path(claims_dir).glob("*.yaml")):
        claims.append(yaml.safe_load(y.read_text(encoding="utf-8")))
    return claims


def judge_claim(claim: dict, claims_dir: Path, seed: int) -> dict:
    if not claim.get("formula_impl"):
        return {"id": claim.get("id"), "result": "unverifiable",
                "diagnosis": None}
    entry = FormulaEntry.from_dict({
        "id": claim["id"],
        "kind": claim.get("kind", "algebraic"),
        "sympy": claim.get("sympy", ""),
        "implements": claim["binds"],
        "formula_impl": claim["formula_impl"],
        "test": {"type": "exact",
                 "tol": claim.get("tol", 1e-6)},
    })
    verdict = run_gate(entry, Path(claims_dir), seed)
    return {"id": claim["id"], "result": verdict.result,
            "diagnosis": verdict.diagnosis}


def audit(claims_dir: Path, seed: int = 0) -> dict:
    claims = load_claims(claims_dir)
    verdicts = [judge_claim(c, claims_dir, seed) for c in claims]
    by_kind = {}
    for c, v in zip(claims, verdicts):
        k = c.get("taxonomy", "other")
        if k not in TAXONOMY:
            k = "other"
        by_kind.setdefault(k, {"claims": 0, "fail": 0, "pass": 0,
                               "unverifiable": 0})
        by_kind[k]["claims"] += 1
        by_kind[k][v["result"] if v["result"] in ("pass", "fail")
                   else "unverifiable"] += 1
    return {"verdicts": verdicts, "taxonomy": by_kind,
            "totals": {"claims": len(claims),
                       "fail": sum(v["result"] == "fail" for v in verdicts),
                       "pass": sum(v["result"] == "pass" for v in verdicts),
                       "unverifiable": sum(v["result"] == "unverifiable"
                                           for v in verdicts)}}


def write_report(out: Path, summary: dict, generator: str) -> None:
    lines = [f"# audit report — generator: {generator}", "",
             f"claims: {summary['totals']['claims']}  "
             f"fail: {summary['totals']['fail']}  "
             f"pass: {summary['totals']['pass']}  "
             f"unverifiable: {summary['totals']['unverifiable']}", "",
             "| taxonomy | claims | fail | pass | unverifiable |",
             "|---|---|---|---|---|"]
    for k, v in summary["taxonomy"].items():
        lines.append(f"| {k} | {v['claims']} | {v['fail']} | {v['pass']} "
                     f"| {v['unverifiable']} |")
    lines += ["", "## verdicts", ""]
    for v in summary["verdicts"]:
        diag = f" — {v['diagnosis']}" if v.get("diagnosis") else ""
        lines.append(f"- {v['id']}: **{v['result']}**{diag}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
