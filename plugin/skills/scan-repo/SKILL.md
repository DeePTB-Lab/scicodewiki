---
name: scan-repo
description: Fill semantic fields on wiki/scan/ skeleton cards (tiered read depth by kind_hint, centrality order) until lint_scan is green.
---

# Scan playbook (understanding as artifact)

1. `scicodewiki scan --repo <repo> --package <pkg>` → skeletons +
   `_map.yaml` + pending list.
2. Fill cards **in centrality order** (most-referenced first),
   scientific-kernel first. Tiered read depth:
   - kernel tier: read the unit's full source file;
   - plumbing/io/cli tier: docstrings + signatures only — use
     `scicodewiki signatures --repo <repo> --package <pkg>` for the dump
     (provenance.depth = mechanical-docstring).

   Heuristic caveats (B/C):
   - `kind_hint` is a hint (source marks + module name); the FINAL kind call
     is yours — record every override in the card `notes:`;
   - centrality = import-graph in-degree; in re-export-heavy codebases
     (package `__init__` re-exports) it misattributes — override with
     physical judgment and record the override in `notes:`.
3. Fields: `purpose` ≤120 chars; `depends_on` ONLY imports actually present
   in the file; `doc_anchors` from docs/; `literature_hints` grounded via
   web search (capability leg, same rule as extract-formula §2); `terms:`
   canonical→aliases for the glossary.
4. Over-budget units: fill the child cards; the module card `notes:`
   summarizes children.
5. Loop `scicodewiki scan` until 0 problems and 0 skeleton pending
   (`lint_scan` is the gate; a rejected card is a rewrite).

## Never
- read the whole repo into context to fill one card;
- exceed purpose/body caps;
- invent imports, edges or literature.
