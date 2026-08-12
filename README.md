# scicodewiki

Verified scientific documentation layer for scientific computing repositories.

Code-wiki generators treat code as the specification; in scientific software the
physics is the specification. scicodewiki adds the layers they structurally miss —
formulas, conventions, literature — as a machine-readable registry whose claims
are checked against the implementation by numerical equivalence gates.

- Atomic product: a verified formula claim. Site, badges and drift reports are projections of it.
- Repo-native: the registry lives in the documented repository; verification is a docs capability, not a dev gate.
- Agent-harness: coding-agent CLIs (Claude Code, codex) propose; mechanical gates decide.

Commercial repo-wiki tools enclose their free tiers; scientific software's
documentation infrastructure should be self-owned. scicodewiki is the open
alternative — with the verification layer they structurally lack.

See [DESIGN.md](DESIGN.md) for the full design.

## Running on codex (or any open-standard agent CLI)

The skill pack follows the shared SKILL.md standard:

```bash
scicodewiki export-skills --out <repo>/.agents/skills
scicodewiki init --repo <repo> --agents-md   # AGENTS.md conventions
```

Then drive the chain (census → scan → bootstrap → extract → outline →
compose → edit → build) from `codex exec` with the skills in
`.agents/skills/`. Claude-specific extras (PostToolUse hooks) are absent
there; run `scicodewiki drift` / `drift-cards` manually — the AGENTS.md
conventions instruct the agent to do so after touching bound code.

## Status

v0.5: mechanical chain + skills cold-validated on two repos (phonax,
DeePTB-JAX); 64 tests. v1 queue: codex smoke, complex-field gates, MCP
registry queries, per-card fan-out. Research line queued: audit study
(naked-LLM / deepwiki-open / CodeWiki baselines vs equivalence gates).
