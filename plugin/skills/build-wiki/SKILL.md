---
name: build-wiki
description: Render the scicodewiki site (subsystem pages, formula cards with badges, registry index) from the target repo's registry.
---

# Wiki build playbook

1. `scicodewiki build --repo .` → markdown + mkdocs.yml under `wiki/`.
2. Pages follow the three-zone skeleton: 概述 / 子系统（管线阶段页）/ 开发与参考（注册表索引=审计面）.
3. Badges on the page are verdict records + git freshness, rendered at build time. A 🕐 stale badge means the bound file changed after the last verdict — offer to run `scicodewiki verify` to refresh.
4. Narrative must not restate registry-owned math: prose links formula cards, theory pages show the literature canonical form + convention box only.
