---
name: outline
description: Decide the page tree and content allocation (manifest cards:/thesis:) from wiki/scan/_map.yaml only — the forest-level information architecture step.
---

# Outline playbook (information architecture)

1. Read ONLY `wiki/scan/_map.yaml` + the current manifest. Not code, not
   card bodies. This is the bounded global view.
2. Consult individual cards only where a `kind` or `purpose` is ambiguous
   for allocation.
3. Decide/refresh stages (domain-semantic units, never module names) and
   pages (default 4-type split). Write per page:
   - `cards:` — every scientific-kernel card lands on exactly one page;
     plumbing/io/cli cards go to dev/API pages or are explicitly excluded
     with a note (no silent gaps, same rule as coverage);
   - `thesis:` — the single reader question the page answers;
   - page priority follows centrality.
4. Gates: `scicodewiki scan --strict` then `scicodewiki consistency`
   (card-coverage + phantom-ref checks green).

## Never
- allocate a card that is not in `wiki/scan/` (mechanically caught anyway);
- structure pages around a single module name.
