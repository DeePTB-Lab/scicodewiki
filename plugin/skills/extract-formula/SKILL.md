---
name: extract-formula
description: Extract a machine-verifiable registry entry (SymPy mirror + code binding + conventions + references) for a scientific-computing function. Use when documenting a formula/kernel in a science repo.
---

# Formula extraction playbook

You are the proposer. The mechanical gate decides. Your prose is never authority.

## 1. Read the code, not your memory
- Read the target function and its docstring; trace prefactors to constant definitions.
- Check `formulas/` first — the registry may already own this stage.

## 2. Ground in literature (capability leg, not authority)
- web search / arXiv for the canonical form; mature theory is pinned in literature.
- Record `references` with paper + equation number; paywalled classics → ask the user for a local PDF.
- Papers disagree on conventions (FWHM/HWHM, ħ/h, angular/cyclic). Do NOT silently pick one — record the mapping in `convention_map`.

## 3. Write the staging deliverables (schemas/formula-entry.schema.json)
- `formulas/staging/<id>.yaml`: id / kind / sympy / latex / implements / symbol_identity / convention_map / references / provenance / test
- `formulas/staging/<id>_formula.py` contract:
  - `sample(rng) -> ctx` — random named primitive arrays
  - `mirror(ctx) -> array` — SymPy-lambdified evaluation
  - `target(ctx) -> array` — the REAL code path, random data injected at a documented seam (patch only data-provider methods)

## 4. Iterate, then hand to the gate
- Scratch self-tests are free (your inputs, your iteration loop).
- Promote staging → `formulas/` only via the gate: `scicodewiki verify --repo <repo> --entry <id>`. The gate draws fresh holdout seeds you never see.
- "ratio constant" diagnosis → multiplicative drift (conventional factors are enumerated for you); non-constant → structural. Fix the mirror; NEVER loosen `tol`.

## 5. Never
- render or treat an unverified formula as fact;
- report your own scratch tests as verification — only gate verdicts count.
