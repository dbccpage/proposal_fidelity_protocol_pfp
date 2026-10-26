# Detailed definition: Woland Base Swarm Specialization & Estate Connections (2)

**AuthorityEffect:** None.

Parent: [Woland Base Swarm Specialization & Estate Connections](../../../../../rules/swarms/rl_woland_base_swarm_specialization.md). Load for the matching predicate, not every task.

## 6. Legacy Swarm Consolidation & RIP Retirement Protocol (`RULE_WOLAND_LEGACY_SWARM_RETIREMENT_001`)

1. **Purge of Legacy Standalone Agent Manifests:**
   All 8 legacy `rip-*.md` agent manifests (`rip-code.md`, `rip-lawyers.md`, `rip-master.md`, `rip-papers.md`, `rip-product.md`, `rip-sprints.md`, `rip-testing.md`, `rip-thanatos.md`) are permanently deleted across all four host roots (`.agents/agents/`, `.claude/agents/`, `.codex/agents/`, `.grok/agents/`). No standalone `rip-*` agent persona may be instantiated.
2. **Legacy Swarm Skill Deprecation & Retinue Redirection:**
   The 12 legacy `rip-*` skills in `.agents/skills/` (`rip-code`, `rip-rust`, `rip-python`, `rip-testing`, `rip-lawyers`, `rip-math-contracts`, `rip-papers`, `rip-product`, `rip-sprints`, `rip-thanatos`, `rip-councils-meeting-hash-validator`, `rip-oeags`) and autonomous swarm router skills (`techne-operad-swarm-router`) are retired. Any retained legacy skill must declare `STATUS: NOT_SUPPORTED` in its `SKILL.md` frontmatter and instruct callers to invoke `/woland --specialization <profile>`.
3. **Unified Child Swarm Specializations:**
   External workloads (`software_dev`, `research`, `deep_research`, `teamwork`) operate strictly as `SwarmSpecializationV1` profiles on the canonical `OmegaEngineWolandSwarm` base (`build_woland_swarm`). They narrow ports, terminals, and budgets without widening, and evaluate through Woland's 10 intergates.
4. **Atomic Four-Host Deprecation Parity:**
   Any modification to agent manifests, skill status markers, or swarm family registries (`family_registry.md`) must be replicated identically across all four host roots (`.agents/`, `.claude/`, `.codex/`, `.grok/`) with passing `test_sync_cross_host_skills.py` verification.
5. **Compiler & Resolver Alias Preservation for Retired Swarms:**
   Whenever standalone swarms (`omega-cognitive-operations-swarm`, `omega-engine-governing-councils-swarm`, `omega-engine-project-management-swarm`, `omega-engine-research-swarm`, `omega-engine-software-development-swarm`, `omega-paper-review-swarm`, `omega-swarm-developer`) are retired from `.agents/skills/`, compiler resolution mechanisms (`resolve.py`, `eval_runner.py`) MUST maintain explicit alias mappings (`RETIRED_STANDALONE_SWARMS`). Inbound references in locus, signals, or review receipts must resolve to `EXISTING_OP` pointing to the unified Woland Single Point of Entry (`.agents/skills/woland/SKILL.md`), preventing false fall-through to generic skill prose.

---

## Cross-References

- Clean Architecture and swarm decoupling: [`../architecture/rl_clean_architecture_and_subsystem_governance.md`](../../../../../rules/architecture/rl_clean_architecture_and_subsystem_governance.md).
- Antibody admission and activation: [`../architecture/rl_immune_antibody_and_verification_hygiene.md`](../../../../../rules/architecture/rl_immune_antibody_and_verification_hygiene.md).
- Routing and authority axes: [`../authority/rl_gtla_rules_rubric.md`](../../../../../rules/authority/rl_gtla_rules_rubric.md).
