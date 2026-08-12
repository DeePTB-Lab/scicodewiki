---
name: naked-wiki
description: Baseline generator — write plain LLM documentation for a repo with NO scicodewiki machinery (no registry, no gates, no cards). Emulates an unassisted LLM wiki for audit contrasts.
---

# Naked wiki playbook (baseline only)

Write the documentation an ordinary LLM assistant would write:

- read the target repo's code/docs freely;
- produce markdown pages (overview, per-subsystem, theory, usage) with
  formulas in LaTeX/prose as you see fit;
- NO registry, NO equivalence checks, NO cards, NO badges;
- do NOT read any existing `wiki/` produced by scicodewiki, and do NOT
  consult its registry — the baseline must be uncontaminated;
- write to `<out-dir>/` (never the repo's own wiki/).

Honesty rule: write what you believe from the code and your knowledge —
do not deliberately err; the audit measures natural error rates.
