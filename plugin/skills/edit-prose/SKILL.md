---
name: edit-prose
description: Adversarial editor pass — critique composed narratives against the checklist, then revise. Editor ≠ author.
---

# Editor playbook (adversarial, separate from the author)

1. After compose, read each narrative against the checklist:
   - flow: does each section earn the next?
   - gaps: claims with no card/code backing?
   - undefined jargon?
   - cross-page duplication (should be cross-references)?
   - global consistency: terms vs `_map.yaml` + theory page; cross-refs resolve.
2. Write the critique to `wiki/scan/_edits/<stage>-<page>.critique.md`
   (generated internal artifact — wiped by clean, never rendered).
3. Revise the narrative until every item resolves. The editor FIXES flagged
   issues only; it does not invent new content (facts belong to compose +
   cards).
4. Gates: `scicodewiki lint` + `scicodewiki consistency` green.
