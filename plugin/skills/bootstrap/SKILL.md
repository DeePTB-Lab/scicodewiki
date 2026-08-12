---
name: bootstrap
description: Infer the pipeline manifest from the target repo's README/docs/code structure and write wiki/formulas/manifest.yaml. First step of a from-scratch generation.
---

# Manifest inference playbook

The manifest is generated output, not a hand input. Derive it from the
repo's own content; never invent stages the docs/code do not support.

## Procedure

0. Run `scicodewiki census --repo <repo>` first — the AST inventory is
   your ground truth; group ONLY census units, never inferred phantoms.
1. Read README, the docs/ listing, and the package layout
   (`scicodewiki`-agnostic: any scientific repo).
2. Identify the **physical workflow order** (dependency chain, e.g.
   relax → FC2 → FC3 → linewidth). Sources: workflow docs, CLI target
   lists, runner code.
3. Stages = domain-semantic units ("三声子线宽与寿命"), NOT python module
   names. Each stage: `id`, `title`, `modules` (real import paths),
   `docs` (existing docs mapped to the stage).
4. `pages:` per stage: default 4-type split from
   `templates/chapter-spec.md` (physics/algorithm/usage/benchmarks);
   adjust titles/omit types the stage cannot support. `formulas:` lists
   stay empty here — extract fills the registry; render attaches cards
   after extraction.
5. Write `wiki/formulas/manifest.yaml`.
6. Run `scicodewiki coverage`; every reported gap either joins a stage or
   is explicitly excluded (pure plumbing -> zone-3 API/dev pages note).
   Silent gaps are defects.

## Never

- create a stage without a docs/code anchor;
- copy module file names as titles;
- touch anything outside `wiki/`.
