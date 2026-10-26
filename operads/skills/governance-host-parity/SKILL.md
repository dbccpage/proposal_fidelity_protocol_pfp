---
name: governance-host-parity
description: "Consolidated agent licensing parity, tracked host garden mirroring atomicity, and sprint governance document gate."
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [governance, host-parity]
---

# governance-host-parity

AuthorityEffect: None.

## The single rule

> Mirror artifacts atomically across the tracked roster in HOST_SKILL_ROOTS in sync_cross_host_skills.py. Do not invent host roots from local directories. Agent capability ceilings forbid unapproved expansions; sprint transitions require their implementation documents.

## Consolidated Invariants

1. **Host License Parity & Directionality**: Sub-operad license definitions must be identical across mirrors, and deployed grants exceeding canonical authority are fatal refusals (`goo-agent-license-host-parity-gate`, `goo-agent-licence-direction-check`).
2. **Tracked Roster Completeness & Atomicity**: The packaging roster is authoritative. Commits altering canonical shared artifacts must mirror to its tracked peers. Adding a host is a separate reviewed roster change, never a sync side effect.
3. **Sprint Document Hard Gate**: Sprints require all 4 implementation documents (`completion.md`, `devops_review.md`, `retrospective.md`, `vp_briefing.md`) prior to retrospective or archiving (`goo-sprint-impl-documents-hard-gate`).
4. **Garden Scope & Context Budget**: Budget gate sweeps measure the entire garden, and over-budget skills must be factorized into `references/` (`goo-budget-gate-default-scope-guard`, `goo-skill-md-factorization-sweep`).
5. **Knowledge Parity Phrasing & Banned Live Doctrine**: Live skill text must use `cross-host` or `active host roots` instead of unfenced historical numerical seat counts (such as former four-host or five-host doctrine), unless explicitly guarded by historical fence tokens (`historical`, `superseded`).
6. **Tracked-Path Git Index Parity**: Skill file renames and deletions must be synchronized atomically across all active host roots to eliminate git tracked-path case/name splits (`sync_cross_host_skills.py --check`).
7. **Governance Rule Size Ceiling & Factorization Parity**: Rule documents in `rules/` across all active host roots must strictly remain `< 12,000` bytes. Over-budget rules must be decomposed along conceptual boundaries into modular sub-rules, mirrored atomically across all active host seats, and registered in the Progressive Disclosure tables of `GEMINI.md` and `AGENTS.md`.

## Verification Requirements

Run the host parity and completeness audit:

```bash
python omega_engine_operads/skills/governance-host-parity/scripts/check_host_parity.py
```
