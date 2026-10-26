# Council Deliberation & Planning Protocol

**AuthorityEffect:** None.  
**Domain Context:** `governance-councils`

This reference documents the procedural review pipelines, quad-agent planning protocols, 12-agent governance review gates, and the installed MSS-N catalog specifications.

---

## 1. Quad-Agent Governance Review Protocol

All technical specifications under `plans/specs/` and epics under `plans/epics/` must satisfy quad-agent governance checks:
1. **DOC_MGR:** UTF-8 without BOM, ATX headings, MD031 blank lines, ordinal UTF-8 manifest synchronization.
2. **DEV_MGR:** Explicit retinue specialist assignment, 4-stage assembly line routing, mandatory single-threaded `-j 1` Cargo compilation.
3. **QA_MGR:** Small-batch test execution discipline (1–3 crates max, no whole-suite sweeps), Soviet Inspector hard veto, finite auto-repair loop ($N \le 3$), `SoftwareQaReceiptV1`.
4. **BUILDER:** Lev Landau Theoretical Minimum (INVARIANT, BREAK, WITNESS, MUTATION) and Landau classification (Classes 1–5; Class 0 mock ornaments strictly forbidden). Every specification must contain an explicit Theoretical Minimum formulation and verified production mutation target forcing tests RED prior to GREEN certification.

---

## 2. 12-Agent Governance Review Protocol

When authoring or reviewing epics, technical specifications, and tracer-bullet tickets:
1. **Mathematical & Invariant Layer:**
   - Verify idempotent projector purity ($P(P(x)) = P(x)$ with zero $\Phi_1/\Gamma_2$ calculation in projectors).
   - Autonomous primitive difference invariants.
   - Named Lean 4 axiom profiles (e.g. `{propext, Quot.sound}` or paper-harmonic profile).
2. **Architecture & Dev Layer:**
   - Enforce Clean Architecture inward dependencies.
   - Exact-type equality on value objects (`type(self) is type(other)`).
   - Pure domain ports and single-threaded `-j 1` Cargo builds.
3. **QA & Testing Layer:**
   - Enforce Soviet Inspector hard veto on mock-only or silent-skip suites.
   - Require Landau Classes 1–5 test tables with verified mutation targets.
   - Bound auto-repair loops to $N \le 3$.
4. **Security & Epistemic Layer:**
   - Guard against Argument Exploit Patterns 1 & 8.
   - Enforce sandbox isolation and verify cryptographic receipt bindings.
   - Route raw unexpected runtime deviations to the Symbol Game JSON-L DAG and CemeterySink.

---

## 3. Installed MSS-N Catalog Specifications

- **Canonical Packet AST:** Resides in `omega_engine_pfp/domain/tower/`; the profile refuses unregistered opcode 29.
- **CLI Commands:** Use `symbol-game demo list`, `symbol-game demo run <id> --output-dir <new-dir>`, and `symbol-game demo verify <receipt>`. Fixture transport is the offline release gate. Live transport requires an explicit flag and credentials.
- **Checkers:** All 101 distinct Python checkers remain research-grade in `omega_engine_pfp/infrastructure/adapters/mssn_research/`, authenticated by the registry.
- **Epistemic Immune System (OEEIS):** Owns detector, thymus, danger, selection, and quarantine behavior. External bounded contexts consume it only through an application-layer port.
- **Migration Custody:** Recorded in `research/mssn_sn_tower/migration/`; replay tools live in `tools/mssn_migration/`.
