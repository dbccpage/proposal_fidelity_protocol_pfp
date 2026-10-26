# Detailed definition: Intelligence Digestion & Archiving Discipline (1)

**AuthorityEffect:** None.

Parent: [Intelligence Digestion & Archiving Discipline](../../../../../rules/architecture/rl_intelligence_digestion_and_archiving_discipline.md). Load for the matching predicate, not every task.

# Intelligence Digestion, Transmutation & Archiving Invariants

**AuthorityEffect:** None.
**Domain Topic:** Canonical Intelligence Estate Lifecycle, Transmutation Pipeline, and Archival Fences
**Canonical Rule Path:** `.agents/rules/architecture/rl_intelligence_digestion_and_archiving_discipline.md`

---

## 1. The Intelligence Ingestion & Digestion Lifecycle

All artifacts residing under `_ic/` represent ingested telemetry, error traces, test coverage matrices, benchmark outputs, or swarm deliberation receipts. They are epistemic intermediate representations, **not permanent shelf documents**.

```
[Raw Telemetry / Execution Runs]
               │
               ▼
   [_ic/ Active Queue]
               │
               ▼  (Obstruction Mining & Structural Extraction)
┌─────────────────────────────────────────────────────────────┐
│ Transmutation into Permanent Repository Assets:             │
│ • Epistemic Antibodies (OEEIS -> .agents/antibodies/)       │
│ • Sovereign Parent Skills (.agents/skills/)                 │
│ • Passive Ambient Rules (.agents/rules/)                    │
│ • 2-Morphism Execution Workflows (.agents/workflows/)       │
│ • Hardened Relational Contracts & Sovereign Code            │
└─────────────────────────────────────────────────────────────┘
               │
               ▼  (Digestion Condition Satisfied: ||Obstruction|| = 0)
    [Terminal State Gate]
         ├── Historical Provenance Needed  ──> Archive (_ic/nara/_archive/ or sealed zip)
         └── Ephemeral / Reproducible      ──> Deletion (git rm)
```

---

## 2. Mandatory Digestion & Archival Invariants

### Invariant 1: Obstruction Exhaustion Predicate (Terminal Digestion)
An intelligence file is **Terminally Digested** if and only if:
1. Every defect witness $\Omega^-$ has been extracted into a typed antibody (`ab_*.json`) or closed in code/contracts/tests.
2. Every architectural finding or pattern has been codified into a permanent skill, rule, workflow, or clean architecture domain.
3. Every referenced conflict or failure has been fully resolved or marked `Terminal Refusal`.

### Invariant 2: Active vs. Terminal Demarcation (`RULE_INTELLIGENCE_TERMINAL_PRUNING_001`)

> **Active Queue Terminal Removal & Branch Pruning Directive:**
>
> Once an intelligence file is Terminally Digested, **it is no longer relevant as an active document** and must not remain in the active `_ic/` root tree:
> - **Archive Boundary:** If the artifact carries non-reproducible historical evidence, cryptographic custody hashes, or formal publication receipts, it must be relocated to sealed CAS storage or an explicit immutable archive.
> - **Deletion Boundary & Branch Pruning:** Once digestion has extracted all actionable failure modes, antibodies, or rules, fully processed files must be removed immediately using `git rm`, and any now-empty parent directory branches must be pruned. No completed source file may linger in active queues to be repeatedly re-digested across sessions.
> - **Post-Harvest Archive Pruning:** Once defect patterns are harvested into `.agents/antibodies/` and operational anti-patterns are closed, intermediate manifests (`corpora_archive_manifest.json`, `teamwork_archive_index.json`, `anti_patterns_registry.json`) and raw run snapshots in `_ic/nara/_archive/` must be pruned cleanly to prevent ghost references and dangling diffs.

### Invariant 3: Producing and Consuming Code Ownership
Every directory and file in `_ic/` must possess an identified Producing Application Service (e.g., `woland_bout_use_case.py`, `symbol_game_emitter.py`, `repo_wide_coda_lggr_auditor.py`) and an identified Consuming Application Service (e.g., `IntelligenceMiner`, `pharmacy_catalog.json`, `DailyDigestGenerator`). Any intelligence file lacking both a live producer and a live consumer is an unowned orphan and must be audited for immediate digestion or deletion.

### Invariant 4: Read-Only Mining Integrity
Mining processes (such as `IntelligenceMiner`) must operate strictly read-only on active sources; in-place mutations of active intelligence files are forbidden. Modification occurs exclusively via atomic creation of downstream antibodies, skills, or archive transitions.

### Invariant 5: Scratch-to-Skill Diagnostic Digestion Invariant (`RULE_SCRATCH_TO_SKILL_DIGESTION_001`)

> **Diagnostic Script Transmutation into Canonical Skills:**
>
> 1. **No Orphaned Scratch Tools:** Diagnostic AST parsers, report inspectors, and defect query scripts created in `scratch/` during codebase audits, reviews, or error investigations must not remain as unowned throwaway files once their immediate objective is validated.
> 2. **Canonical Skill Absorption:** When a diagnostic operation provides reusable utility for recurring audits (e.g., derive trait inspection, anti-pattern detection, or certificate collection validation), the script must be refactored into the corresponding skill's `scripts/` directory with clean CLI parameter parsing, unit test or linter compliance, and documentation in the skill's `SKILL.md`.
> 3. **Scratch Cleanup:** Following integration and verification, the temporary scratch script must be removed or moved to terminal digestion.

### Invariant 6: Permanent Records Custody & Hash-Chain Integration (`RULE_PERMANENT_RECORDS_CUSTODY_001`)

> **Permanent Records Custody & Hash-Chain Invariant:**
>
> 1. **Protected Permanent Records Custody:** `_ic/nara/permanent_records/` is protected cold-storage custody alongside `_ic/nara/historical/` and `_ic/odni/migrations/`. Digestion, pruning, and cleanup routines must never modify or delete these byte-bound records.
> 2. **Multi-Run Linear Hash-Chain Preservation:** When integrating successive runs into a linear hash-chained stream (such as `prompt_genealogy.jsonl`), alternate sequence branches must not be naively appended to the main stream, as doing so breaks SHA-256 parent-child continuity (`seq == next_sequence` and `parent == head_sha256`). The authoritative continuous sequence must be recorded at the root of `permanent_records/`, while run-specific branches are preserved verbatim in dedicated provenance subtrees (`permanent_records/<run_class>/<agency>/<subsystem>/`).
> 3. **Bout Journal Interleaving & Terminal Totality:** Multi-act bout journals (`bout_journal.jsonl`) integrated into permanent records must preserve all terminal records and contain zero unreadable entries or unfinished bouts across all constituent runs.


Historical custody exception: `_ic/nara/permanent_records/`, `_ic/nara/historical/`, `_ic/odni/migrations/`, and checkout-local `_ic/odni/migration/` are protected migration custody. Digestion, pruning, and cleanup must never modify or delete these byte-bound records. Active queues exclude these directories.
