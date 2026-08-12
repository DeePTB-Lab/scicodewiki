---
name: compose
description: Write wiki narratives (subsystem subpages + zone-1 theory page) from assigned scan cards per templates/chapter-spec.md. Outputs wiki/narratives/. Re-reads current function bodies through card pointers before writing.
---

# Composition playbook (author role)

## 1. Read the allocation, not the repo
- manifest `cards:` per page; read the assigned card files (frontmatter).
- Per card, **re-read the CURRENT code through the pointer**: `file` +
  `functions`/`classes` names, line-targeted (locate by name, not stale
  line numbers). The card is understanding + pointer, never a cache.

## 2. Compose per chapter-spec skeleton
- `wiki/narratives/<stage>-<page>.md`; the opening blocks must address the
  page's `thesis:` (manifest).
- Mermaid diagrams from card + re-read data flow only.

## 3. Writing craft (craft layer)
- reader-question-driven: each `##` answers the question the reader has at
  that point;
- lead each section with its conclusion;
- glossary-canonical terms only (card `terms:`/`conventions:`);
- cross-reference, never duplicate: say once, link elsewhere;
- every number carries a docs/ or registry citation.

## 4. Anchor (quality reference excerpt — showcase standard)

> 谐和晶体中的声子是严格本征模，寿命无穷。真实晶体的势能面含三阶及更高阶
> 项，声子因此互相散射，谱函数从 δ 峰展宽为洛伦兹型，其半高半宽 Γ 即
> 三声子线宽，寿命 τ = 1/(4πΓ)。

Write toward this density: every sentence carries a fact, terms canonical,
no filler, no machine vocabulary.

## 5. theory.md
Canonical LaTeX from card `literature_hints`/registry references; notation
table from card conventions; cross-convention differences as ONE prose
paragraph.

## 6. Gates
`scicodewiki build` → `lint` → `coverage` (over-budget pages split
bottom-up, recursion ≤ 2).

## 7. Large repos
Fan out one subagent per page (narratives are independent files); the
coordinator runs `edit-prose` + the gate chain afterwards — global
consistency (duplication/glossary) is exactly what the coordinator-level
`consistency` check is for.

## Never
- edit `wiki/formulas/` FROM THIS ROLE — the registry only changes via
  extract-formula + promote (the gate); a badge must always mean
  "gate-passed". If you spot a wrong/stale entry while writing, STOP and
  run fix-drift, then continue;
- paste registry structures (convention_map, verdicts, badges) into reader pages;
- uncited numbers;
- restate whole source files;
- write from memory what a card pointer can ground.
