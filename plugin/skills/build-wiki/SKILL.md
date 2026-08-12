---
name: build-wiki
description: Render the scicodewiki site (subsystem pages, formula cards, registry index, dependency graph) from the target repo's registry + narratives.
---

# Wiki build playbook

1. `scicodewiki build --repo .` → markdown + mkdocs.yml under `wiki/`.
2. Three-zone skeleton: 概述（含机械依赖图）/ 子系统（管线阶段页）/
   开发与参考（注册表索引 = 审计面）.
3. Reader pages are pure documentation: zero badges/verdicts. The audit
   face (registry index) carries badges + verdict history.
4. Narrative must not restate registry-owned math: prose links formula
   cards; theory pages show the literature canonical form + notation table.
5. Gate chain: `build` → `verify` → `lint` → `coverage` → `consistency`.
