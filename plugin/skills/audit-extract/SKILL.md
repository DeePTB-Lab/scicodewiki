---
name: audit-extract
description: Extract formula-level claims from ANY generator's wiki into claim YAMLs for `scicodewiki audit`. Proposer only — the gate decides truth.
---

# Audit extraction playbook

Input: a wiki directory produced by SOME generator (naked LLM, CodeWiki,
deepwiki-open, Qoder, …) + the target repo. Output: `<claims>/*.yaml`.

## Per claim (one YAML each)

```yaml
id: <generator>.<page>.<n>
source: <page file>:<line-ish>
binds: {module: <dotted module>, function: <function name>}
sympy: "<the formula the wiki states, SymPy text>"
taxonomy: prefactor | symbol-identity | convention | coverage | innovation | other
formula_impl: <mirror file in claims dir>   # when a mirror is feasible
tol: 1e-6
notes: "<verbatim quote of the wiki's claim>"
```

## Rules
- Extract EVERY quantitative/formula statement (prefactors, normalization,
  units/conventions, δ-forms, lifetimes) — coverage matters as much as errors.
- `taxonomy` labels the CLAIM KIND, never the verdict; you do NOT judge
  correctness — `scicodewiki audit` does, mechanically.
- Attach a mirror whenever the claim binds to runnable code (reuse
  extract-formula §3b seam patterns); prose-only claims stay mirror-less
  and become 'unverifiable' (human/LLM labelling later).
- Quote the wiki verbatim in `notes` so every verdict is traceable.
