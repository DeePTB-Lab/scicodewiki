# scicodewiki

Verified scientific documentation layer for scientific computing repositories.

Code-wiki generators treat code as the specification; in scientific software the
physics is the specification. scicodewiki adds the layers they structurally miss —
formulas, conventions, literature — as a machine-readable registry whose claims
are checked against the implementation by numerical equivalence gates.

- Atomic product: a verified formula claim. Site, badges and drift reports are projections of it.
- Repo-native: the registry lives in the documented repository; verification is a docs capability, not a dev gate.
- Agent-harness: coding-agent CLIs (Claude Code, codex) propose; mechanical gates decide.

See [DESIGN.md](DESIGN.md) for the full design.

## Status

v0 under construction (see DESIGN.md §10).
