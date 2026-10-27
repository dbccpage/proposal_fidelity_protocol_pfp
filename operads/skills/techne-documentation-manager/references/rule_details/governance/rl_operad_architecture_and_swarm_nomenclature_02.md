# Detailed definition: Operad Architecture & Swarm Protocols (2)

**AuthorityEffect:** None.

Parent: [Operad Architecture & Swarm Protocols](../../../../../rules/governance/rl_operad_architecture_and_swarm_nomenclature.md). Load for the matching predicate, not every task.

## Swarm Nomenclature Purity & Descriptive Script Naming (`RULE_SWARM_NOMENCLATURE_PURITY_001`)

> **Anti-Fabricated Swarm & Descriptive Script Naming:**
>
> 1. **Prohibition of Fabricated Swarms & Backronyms:** Agents are strictly forbidden from inventing fictional swarm titles, pseudo-bureaucracies, or synthetic acronyms not defined in the canonical Council roster (`governance/sentinel_councils/`). In particular, there is NO "Engine Agentic Obstruction Hunting Swarm" (OEAOHS).
> 2. **Descriptive Script Naming:** Tool scripts residing under skill `scripts/` directories must use standard, clean snake_case filenames reflecting their concrete operational behavior (e.g., `ten_level_obstruction_scanner.py`, `ast_cochain_obstruction_scanner.py`), never prepending fabricated swarm acronyms.
> 3. **Four-Parent Skill Script Directory Traversal:** Scripts residing in `.agents/skills/<skill_name>/scripts/` are exactly 4 directory levels below the repository root. Path resolution must navigate 4 parent levels (`os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")` or `Path(__file__).resolve().parents[3]`) to prevent resolving into `.agents/` as false root.
> 4. **Atomic Four-Host Script Rename Replication:** Whenever a skill script is renamed, it must be atomically updated across all four host roots (`.agents/`, `.claude/`, `.codex/`, `.grok/`), old paths deleted from git index in all seats, and entries in `capability_catalog.v1.json` synchronized with updated SHA-256 digests and byte counts.

---

## Installed MSS-N Catalog


- The canonical packet AST and structural profile live in `pfp/domain/tower/`; the new profile refuses unregistered opcode 29.
- Use `symbol-game demo list`, `symbol-game demo run <id> --output-dir <new-dir>`, and `symbol-game demo verify <receipt>`. Fixture transport is the offline release gate. Live transport requires an explicit flag and credentials.
- All 101 distinct Python checkers remain research-grade in `pfp/infrastructure/adapters/mssn_research/`, authenticated by the new registry. Keep historical reach registries and Git-object receipts unchanged.
- Named functionals require explicitly pinned Rust adapters. Missing adapters/binaries yield typed refusal. Illustrations and receipts have `AuthorityEffect: None`.
- The Epistemic Immune System (`eis`, OEEIS) owns detector, thymus, danger, selection, and quarantine behavior. OEWAS and other bounded contexts consume it only through an application-layer port, never by importing OEEIS from their domain layer. Model calls use the traced provider gateway; no implicit dotenv reads or automatic native pins.
- Migration custody and file dispositions are recorded in `research/mssn_sn_tower/migration/`; replay tools live in `tools/mssn_migration/`.
