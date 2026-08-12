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
- Source hierarchy: web search / arXiv first; **offline fallback = repo-local
  authority** (module docstrings that transcribe the formula, docs/ sections
  pinning conventions) — record which leg you used in `provenance.via`.
- Record `references` with paper + equation number; paywalled classics → ask the user for a local PDF.
- Papers disagree on conventions (FWHM/HWHM, ħ/h, angular/cyclic). Do NOT silently pick one — record the mapping in `convention_map`.

## 3. Write the staging deliverables (schemas/formula-entry.schema.json)
- `formulas/staging/<id>.yaml`: id / kind / sympy / latex / implements / symbol_identity / convention_map / references / provenance / test
- `formulas/staging/<id>_formula.py` contract:
  - `sample(rng) -> ctx` — random named primitive arrays
  - `mirror(ctx) -> array` — SymPy-lambdified evaluation
  - `target(ctx) -> array` — the REAL code path, random data injected at a documented seam (patch only data-provider methods)

## 3b. Finding seams (make target() run REAL code on random data)

In order of preference:
1. **constructor injection** — the class takes arrays/providers
   (freqs, eigvecs, FC3); build it with random ctx.
2. **object.__new__ + attribute patch** — set only the attributes the
   method reads; patch *data-provider* methods (e.g. `_phi3_batch`)
   with ctx lambdas; the math path stays real.
3. **module-level pure function** — call directly with ctx arrays.
4. **tolerance/flag seams** — disable post-stages (e.g.
   `degeneracy_tolerance=0`) to isolate the stage under test.

Rules: patch ONLY data providers, never the compute being mirrored;
document the seam in the entry (`binds`/`symbol_identity`); if no seam
exists without refactoring the target, take a coarser stage or
`kind: novel` + oracle — never re-implement the compute in the mirror.

## 4. Iterate, then hand to the gate
- Scratch self-tests are free (your inputs, your iteration loop).
- **Promote via `scicodewiki promote --repo <repo> --entry <id>`**: the gate
  runs on staging and moves entry + mirror into `formulas/` ONLY on pass.
  Never copy staging files by hand. Holdout seed is fresh-random by default
  (`--seed` only for reproduction).
- "ratio constant" diagnosis → multiplicative drift (conventional factors are enumerated for you); non-constant → structural. Fix the mirror; NEVER loosen `tol`.
- If a `kind: novel` candidate turns out to admit a real equivalence mirror
  (deterministic grouping etc.), record the STRONGER `test.type: exact` and
  note the deviation in the entry — oracle is the floor, not the ceiling.

## 5. Never
- render or treat an unverified formula as fact;
- report your own scratch tests as verification — only gate verdicts count.
