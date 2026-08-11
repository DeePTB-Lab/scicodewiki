"""Equivalence gate: executable mirror vs bound implementation on holdout inputs.

The gate generates its own random inputs at verification time (holdout):
inputs the proposer (agent or human) never chose, so a mirror cannot be
overfit to its own scratch tests. Verdicts are appended to the entry and
are the badge source, the audit corpus and the paper evidence chain.

formula_impl contract (executable mirror, lives in the target repo's formulas/):
    sample(rng) -> ctx            dict of random named primitive arrays
    mirror(ctx) -> ndarray        SymPy-lambdified evaluation over ctx
    target(ctx) -> ndarray        the REAL code path, random data injected at a
                                  documented seam (instance-method patch etc.)
  convergent entries additionally expose:
    params() -> list              refinement sequence (sigma values, mesh sizes)
    mirror(ctx, param) / target(ctx, param)
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .registry import FormulaEntry, RegistryError, append_verdict


class GateError(RegistryError):
    """Raised when a formula_impl violates the contract."""


@dataclass
class Verdict:
    result: str          # pass | fail
    seed: int
    diagnosis: str | None = None


# multiplicative drift suspects: the conventional prefactor traps
COMMON_FACTORS = {
    2.0: "factor 2 (FWHM/HWHM mixup or double counting)",
    0.5: "factor 1/2",
    6.0: "missing combinatorial factor 3! = 6",
    1 / 6: "spurious 1/3!",
    2 * np.pi: "2pi (angular vs cyclic frequency)",
    1 / (2 * np.pi): "1/(2pi)",
}


def _load_impl(path: Path):
    if not path.exists():
        raise GateError(f"formula_impl not found: {path}")
    spec = importlib.util.spec_from_file_location(
        f"scicodewiki_impl_{path.stem}", path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in ("sample", "mirror", "target"):
        if not hasattr(mod, attr):
            raise GateError(f"{path.name}: formula_impl must define {attr}()")
    return mod


def ratio_diagnosis(mirror: np.ndarray, target: np.ndarray) -> str:
    """Half an answer, not a red X: constant ratio => multiplicative drift
    (enumerate conventional factors); else => structural difference."""
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = target / np.where(mirror == 0, np.nan, mirror)
    finite = ratio[np.isfinite(ratio)]
    if finite.size and np.allclose(finite, finite[0], rtol=1e-6):
        r = float(finite[0])
        hits = [label for val, label in COMMON_FACTORS.items()
                if np.isclose(r, val, rtol=1e-6)]
        base = (f"implementation/mirror ratio constant at {r:.6g} "
                f"across random inputs")
        if hits:
            return base + " -> suspect: " + "; ".join(hits)
        return base + " -> multiplicative drift (prefactor mismatch)"
    diff = np.abs(target - mirror)
    i = int(np.nanargmax(diff))
    return (f"non-constant ratio -> structural difference; "
            f"max |target-mirror| = {diff.flat[i]:.6g} at flat index {i} "
            f"(mirror={mirror.flat[i]:.6g}, target={target.flat[i]:.6g}); "
            f"inspect inputs there")


def run_gate(entry: FormulaEntry, formulas_dir: Path, seed: int) -> Verdict:
    rng = np.random.default_rng(seed)
    impl = _load_impl(formulas_dir / entry.formula_impl) \
        if entry.formula_impl else None

    if entry.test["type"] == "oracle":
        return Verdict("pass", seed,
                       f"oracle-endorsed: {entry.test.get('note', '')}")
    if impl is None:
        raise GateError(f"{entry.id}: test.type {entry.test['type']} "
                        f"requires formula_impl")

    ctx = impl.sample(rng)

    if entry.test["type"] == "convergent":
        if not hasattr(impl, "params"):
            raise GateError(f"{entry.id}: convergent entries need params()")
        tol = float(entry.test.get("tol", 1e-3))
        errs = []
        for param in impl.params():
            a = np.asarray(impl.mirror(ctx, param), float)
            b = np.asarray(impl.target(ctx, param), float)
            errs.append(float(np.max(np.abs(a - b))))
        if errs[-1] <= tol:
            return Verdict("pass", seed,
                           f"convergent: error sequence {[f'{e:.3g}' for e in errs]}")
        return Verdict("fail", seed,
                       f"convergent: error {errs[-1]:.3g} at finest param "
                       f"exceeds tol {tol:g}; sequence {errs}")

    # exact. atol scales with the data magnitude: SI-scale physics
    # (~1e-127 for linewidths) would otherwise be vacuously "close"
    # to any small absolute tolerance.
    a = np.asarray(impl.mirror(ctx), float)
    b = np.asarray(impl.target(ctx), float)
    if a.shape != b.shape:
        return Verdict("fail", seed,
                       f"shape mismatch: mirror={a.shape} target={b.shape}")
    tol = float(entry.test.get("tol", 1e-10))
    scale = max(float(np.abs(b).max()), float(np.abs(a).max()), 1e-300)
    if np.allclose(a, b, rtol=tol, atol=tol * scale):
        return Verdict("pass", seed)
    return Verdict("fail", seed, ratio_diagnosis(a, b))


def verify_repo(formulas_dir: Path, commit: str, seed: int = 0,
                only: str | None = None, record: bool = True):
    """Run the gate over every entry; append verdicts; return (entries, verdicts)."""
    from .registry import load_entries

    out = []
    for entry in load_entries(formulas_dir):
        if only and entry.id != only:
            continue
        verdict = run_gate(entry, formulas_dir, seed)
        if record and entry.path is not None:
            append_verdict(entry.path, {
                "at": _today(), "commit": commit, "seed": seed,
                "result": verdict.result,
                **({"diagnosis": verdict.diagnosis} if verdict.diagnosis else {}),
            })
        out.append((entry, verdict))
    return out


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()
