# Detailed definition: Councils, Planning & Review Protocols (1)

**AuthorityEffect:** None.

Parent: [Councils, Planning & Review Protocols](../../../../../rules/governance/rl_councils_planning_and_operad_architecture.md). Load for the matching predicate, not every task.

# Rule: Councils, Planning, Contract Authority & Review Protocols

**AuthorityEffect:** None.

This rule codifies lead governance council prefix standardization, 12-agent review protocols, quad-agent planning specifications, master relational council schemas, and epic manifest byte custody.

---

## Lead Governance Council Prefix Standardization Invariant

> **Council Prefix Law:**
>
> 1. All skills admitted to the estate skill garden must declare their lead Greek Governance Council prefix. The admitted set is **derived from the council roster**, not hand-listed here: a prefix is admitted when it names a council that exists in `omega_engine_product_planning_office/plans/epics/oegov/source_specs/05_anomalon_councils_and_type_lexicon_sovereignty.md` §2.1 and has a current council declaration in `omega_engine_governance/anomalon_councils/` (standalone agent manifests are retired). That currently admits `aletheia-*`, `curious-*`, `dianoia-*`, `episteme-*`, `glossa-*`, `kybernesis-*`, `logos-*`, `nomos-*`, `nous-*`, `oikonomia-*`, `panepistimion-*`, `techne-*`, `thanatos-*` and `theoria-*`.
>
>    *Amended 2026-08-31.* Clause 1 previously named five prefixes -- `thanatos`, `techne`, `panepistimion`, `theoria`, `oikonomia`. Nineteen of 115 admitted skills already used prefixes outside that list, so the law described a garden that had not existed for some time. A hand-written list of a derived set goes stale silently and then reads as permission denied rather than as documentation that was never updated. Deriving it means the law cannot drift from the roster again. This widens nothing that was not already in use, and it does not admit a prefix that names no council.
> 2. Dedicated operad families (`auto-*`, `woland-*`, `meta-*`) remain reserved for autopoiesis, single-point-of-entry swarms, and colored operad quotient verifiers.
> 3. Ooutwire is not a governance council; the `ow-*` prefix is explicitly authorized by the Architect for Ooutwire psychological operations, directorates, and intelligence bureaus (`ow-directorate-*`, `ow-bureau-*`).

---

## Council Prefix & Hot-Context Factorization Invariant

> **Prefix Standardization with Factorized Modularity:**
>
> 1. When creating, renaming, or synchronizing skill packages to comply with the Lead Governance Council Prefix Standardization Invariant (e.g. `techne-*`, `panepistimion-*`), agents must strictly preserve the factorized architecture.
> 2. `SKILL.md` files must remain strictly under the **300-line / 20 KB** context budget ceiling (`budget_gate.py`).
> 3. Never copy monolithic, uncompacted legacy skill bodies into council-prefixed packages. Exhaustive checklists, rubrics, example sessions, and workflow walkthroughs must reside in `references/` subdirectories and be referenced via relative markdown links.

---

## Lexical, Vocabulary & Abbreviation Symmetry Invariant

> **Terminology & Acronym Purity:**
>
> 1. `_types/lexicon.yaml` and `_types/abbreviations.yaml` are the estate authorities for term definitions, symbols, and acronym expansions.
> 2. `/auto-symmetry-hunter` actively inspects candidate PRs, preprints, and contracts to detect misspellings, ungrounded symbol collisions, deprecated acronyms (e.g. `GTOC` -> `CODA`), and unexpanded abbreviations (e.g. `DDC` -> Discrete Deformation Calculus), logging divergences in `_types/vocabulary_deviations.md` and scaffolding valid new terms into the canonical lexicon.

---

## Master Relational Council Schema & Fibration Invariant

> **0-6NF Relational Governance:**
>
> 1. Council topology, authority matrices, and meeting lifecycle doctrine reside in `_types/councils.yaml` under strict 0-6NF, EKNF, and BCNF normalization.
> 2. The governance fibration $\pi: E \to B$ guarantees that runtime deliberation sessions ($E$) project onto the static council DAG ($B$) with evidence conservation (Invariants C1-C12) and lossless historical blob provenance.

---

## Quad-Agent Planning & Lev Landau Theoretical Minimum Invariant

> **Specification & Test Hardening Protocol:**
>
> 1. **Quad-Agent Governance Review**: All technical specifications under plans/specs/ and epics under plans/epics/ must satisfy the quad-agent governance checks:
>    - DOC_MGR: UTF-8 without BOM, ATX headings, MD031 blank lines, ordinal UTF-8 manifest synchronization.
>    - DEV_MGR: Explicit retinue specialist assignment, 4-stage assembly line routing, mandatory -j 1 cargo compilation.
>    - QA_MGR: Small-batch test execution discipline (1-3 crates max, no whole-suite sweeps), Soviet Inspector hard veto, finite auto-repair loop ( \le 3$), SoftwareQaReceiptV1.
>    - BUILDER: Lev Landau Theoretical Minimum (INVARIANT, BREAK, WITNESS, MUTATION) and Landau classification (Classes 1-5; Class 0 mock ornaments strictly forbidden).
> 2. **Theoretical Minimum Mandate**: Every technical specification MUST contain an explicit Theoretical Minimum formulation and a verified production mutation target that forces tests RED prior to GREEN certification.

---

## Product Planning Office Epic Manifest & Domain Subfolder Invariant (`RULE_PLANNING_EPIC_MANIFEST_001`)

> **Product Planning Byte Custody & Subfolder Partitioning:**
>
> 1. **Reviewed Inventory:** The 2026-10-10 user-authorized OEGOV successor review contained 61 formal epic plans. The 2026-10-11 user-requested SPEC_ONLY Woland shared-backend epic brings the reviewed inventory to 62 (`EXPECTED_EPIC_COUNT = 62`), with zero source snapshots in the epic manifest. The three added SPEC_ONLY epics have proposed acceptance work; planning status does not imply implementation completion. Supporting specifications have separate migration custody. Earlier review and retirement receipts remain historical custody for their recorded versions; they do not exclude the newly reviewed plans.
> 2. **Recursive Coverage:** Inventory every matching `epic_oe_*_plan.md` recursively under `plans/epics/`, including governance, Woland and all other system suites. READMEs, research drafts, prior-art YAML and execution receipts are separate document classes. Do not omit unrelated plans or lower the reviewed pin to make a gate pass.
> 3. **Explicit Review:** Additions, removals and supersession require review, source custody and manifest regeneration. Preserve historical receipts and held proof obligations. A content mutation to any registered plan must invalidate its recorded digest.
> 4. **Programmatic Generator:** Regenerate only through `python -m omega_engine_product_planning_office.use_cases.epic_manifest_audit --write`; do not hand-edit counts or digests.
> 5. **Encoding:** Generated manifests use UTF-8 without BOM and pure LF line endings.

---

## Product Planning Epic Hygiene

See [epic hygiene and consolidation](../../../../../rules/governance/rl_product_planning_epic_hygiene.md).

## Single Canonical Contract Source of Truth Invariant

> **Contract Authority & Zero-Drift Asset Discipline:**
>
> 1. `omega_engine_governance/contracts/` is the sole canonical source of truth for all system, mathematical, operating system, and packet contracts under `omega.contract.v2`.
> 2. Rust crates must never maintain duplicated, unverified YAML asset copies. Build scripts (`build.rs`) and code generators must read directly from the canonical governance directory and emit typed descriptors into `$OUT_DIR`.
> 3. All computational and mathematical contracts must strictly declare `descriptor.authority_effect: None`, rejecting unauthorized runtime authority minting.

---
