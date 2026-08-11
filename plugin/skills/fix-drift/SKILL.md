---
name: fix-drift
description: Repair registry entries whose equivalence gate fails or went stale after code changes.
---

# Drift repair playbook

1. `scicodewiki drift --repo .` → list failing / stale entries.
2. Read the verdict diagnosis:
   - constant ratio → prefactor / combinatorial drift; the diagnosis enumerates conventional suspects (2, 1/2, 3!, 2π, …);
   - non-constant ratio → structural change; inspect the printed max-deviation input.
3. Decide which side is right. The code may be right (update the mirror) or the code may have drifted (fix the code — the registry is the spec-level claim, and the wiki shows ❌ until someone acts).
4. Re-run the gate. A badge returns to ✅ only via a fresh pass verdict — never by editing verdict history.
