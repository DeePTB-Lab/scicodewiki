---
name: narrate
description: Generate wiki narratives (subsystem subpages + zone-1 theory page) from the target repo's source and docs, per templates/chapter-spec.md. Outputs wiki/narratives/.
---

# Narrative generation playbook

You are the generation-side author. Everything you write must be
re-derivable from the repo's source; the wiki is wiped and regenerated
on every tool test, so hand-memory content is a defect.

## Procedure

1. Read `wiki/formulas/manifest.yaml` (stages, `pages:`, docs mapping)
   and the registry entries (`symbol_identity`, `references`).
2. For each narrative file: read the bound module's **code** and the
   mapped `docs/*.md`. Extract facts; cite as you go.
3. Write `wiki/narratives/<stage>-<page>.md` following the page skeleton
   in `templates/chapter-spec.md` (physics / algorithm / usage /
   benchmarks). Mermaid diagrams from the code's real data flow.
4. Write `wiki/narratives/theory.md`: canonical forms (LaTeX) from
   `references`; notation table reshaped from `symbol_identity`;
   cross-literature convention differences as ONE prose paragraph.
5. Run `scicodewiki build --repo <repo>` then `scicodewiki verify
   --repo <repo>`; fix structural errors.
6. Self-check the spec's 写作纪律 list. Machine-flavored wording or an
   uncited number = defect; rewrite.

## Never

- edit `wiki/formulas/` (inputs; data changes go through extract-formula
  and the equivalence gate);
- paste registry structures (convention_map, verdicts, badges) into
  reader pages;
- write a number without a docs/source citation.
