# Detailed definition: Subsystem Relocation & Estate Purity (2)

**AuthorityEffect:** None.

Parent: [Subsystem Relocation & Estate Purity](../../../../../rules/architecture/rl_subsystem_relocation_and_estate_purity.md). Load for the matching predicate, not every task.

## Legacy Kernel Eradication & Canonical ROP Placement Invariant (`RULE_ROP_CANONICAL_PLACEMENT_AND_LEGACY_KERNEL_RETIREMENT_001`)

> **Eradication of Zombie Shims and Canonical ROP Domain Home:**
>
> 1. **Zero Zombie Shims:** Following sovereign Rust migration to `engine/crates_rs/`, the legacy Python packages `engine/kernel/` and `engine/crates/` are permanently eradicated. No agent may recreate compatibility facades, re-export stubs, or placeholder `__init__.py` files under `engine/kernel/` or `engine/crates/`.
> 2. **Canonical Python ROP Home:** The pure-Python Railway-Oriented Programming (ROP) result monad and typed refusal records (`Ok`, `Err`, `Refusal`, `Result`, `sequence`, `traverse`) reside exclusively in `operations/domain/rop/result.py` with domain re-exports in `operations/domain/rop/__init__.py`. All call sites, tests, and adapters must import directly from `operations.domain.rop.result` or `operations.domain.rop`.
> 3. **Host Root Cleanliness (No Eval Banks or Quarantines):** Agent host roots (`.agents/`, `.claude/`, `.codex/`, `.grok/`) are strictly reserved for live agent configurations, governance rules, and skills. Test eval banks belong in domain packages (e.g., `operads/skill_operad/skill_compiler/eval_bank/`), and obsolete quarantined prototypes must be purged from the repository rather than accumulated in host roots.

## Canon-Only Estate & Host Mirror Exclusion Invariant (`RULE_CANON_ONLY_HOST_MIRROR_EXCLUSION_001`)

> **External Host Context & Mirror Exclusion Discipline:**
>
> 1. **Canon-Only Roots in `.agents/`:** Directories containing internal intelligence, mined candidates, raw definitions, or operad graphs (`.agents/antiskills/`, `.agents/antibodies/`, `.agents/oeeis/`, `.agents/locks/`, `.agents/skill_operads/`) are strictly canon-only (`CANON_ONLY_ROOTS`). They must NEVER be mirrored to `.claude/`, `.codex/`, or `.grok/`.
> 2. **Claude Code Rules Subdirectory Pruning:** Claude Code automatically ingests all markdown files found in `.claude/rules/` recursively. To avoid severe context exhaustion, `.claude/rules/` must remain pruned of all subdirectories, containing only top-level markers or `.gitkeep`.
> 3. **Local Host Parity Verification:** `operations/use_cases/packaging/host_root_parity.py` enforces this invariant via `CANON_ONLY_ROOTS` and `INTENTIONAL_HOST_ROOT_EXCLUSIONS`.

---

## Code Audit & Anti-Pattern Review Engine Placement (`RULE_CODE_AUDIT_OEWAS_PLACEMENT_001`)

> **OEWAS Placement Invariant for Audit & Review Engines:**
>
> 1. **Canonical Home in OEWAS:** All static code analysis engines, anti-pattern checkers, and comment-slop hunter-killer pipelines MUST reside under `operads` (OEWAS) within `domain/` and `application/`, exposed via `frontend/cli/main.py` (`review-anti-patterns`, `review-comment-slop`).
> 2. **Prohibition of Operations & .agents Engines:** Autonomous agents must NOT place or invoke executable Python review logic from `operations` or `.agents/`.
> 3. **Skill Script Forwarding:** Skill runners under `.agents/skills/*/scripts/` must serve strictly as lightweight CLI forwarding adapters delegating directly to OEWAS controllers.
