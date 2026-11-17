# Goo Micro-Skills Consolidation Manifest

**AuthorityEffect:** None.  
**Governing Standard:** 30-day archive rule under OEWAS Clean Architecture and Coloured Operad consolidation.

This manifest records the consolidation of all 87 legacy `goo-*` micro-skills into their canonical domain suites and councils. On 2026-09-18, the deletion and renaming sweep was fully executed:

- **85 absorbed documentation stubs** were permanently deleted across all 6 repository host seats.
- **2 executable gates** were renamed to strictly refuse the `goo-` prefix and assigned to their governing councils under `councils_combined.yaml`:
  1. `declared-vs-actual-gate` (Council: `L3_logos_sadc` / `L4_logos_sadc_metronomos`)
  2. `paper-header-lexicon-gate` (Council: `L3_nous_glossa` / `L4_nous_panepistimion_kanon`)

---

## Goo Prefix Refusal Law (`RULE_REFUSE_GOO_PREFIX_001`)

When consolidating `goo-*` micro-skills into their canonical domain suites, agents MUST:

1. **Delete** the legacy `goo-*` skill directory once its devolved invariants, fitness functions, and test contracts are fully incorporated into the target host suite.
2. **Rename** the skill to explicitly refuse and strip the `goo-` prefix if the capability is retained as an atomic operand or standalone gate (e.g. `declared-vs-actual-gate` instead of `goo-declared-vs-actual-gate`).

Under no circumstances may a consolidated skill retain the `goo-` prefix. All 6 host seats maintain zero directories starting with `goo-`.

---

## 1. Clean Architecture & AST Fence Suite

**Target Host:** `techne-code-principal-architect`  
**Automated Fitness Function:** `python .agents/skills/governance-clean-arch/scripts/check_clean_arch.py`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-clean-arch-operations-layer-auditor` | Inward dependency rule (`domain <- use_cases <- infrastructure`) |
| `goo-clean-arch-single-root-auditor` | Single-root layer directory layout per bounded context |
| `goo-zero-applications-clean-arch-devolution-gate` | Devolution of nested `applications/` paths |
| `goo-bounded-context-clean-architecture-fence` | Strict boundary isolation across bounded contexts |
| `goo-no-shim-dual-home-collapse` | Prohibition of backward-compatibility re-export shims |
| `goo-monolith-clean-arch-modularizer` | AST decomposition of monolithic scripts into Clean Arch sub-services |
| `goo-oeos-base-object-contract-guard` | Purity of domain base objects (zero host I/O in kernels) |
| `goo-oeos-eight-stage-waist-contract-validator` | Validation of 8-stage waist pipeline contracts |
| `goo-reserved-word-module-name-guard` | Prevention of Python standard library naming collisions |
| `goo-repo-escaping-path-resolver-ban` | Ban on path traversal escaping repository boundaries |
| `goo-root-relative-path-exclusion-guard` | Repository-root evaluation of path exclusions |
| `goo-po000-package-root-resolution` | Deterministic root-depth resolution across tool depths |

---

## 2. Exact Rational Arithmetic & Solvers Suite

**Target Host:** `coda-degree-k-dual-certified-solver` & `techne-code-math-search-solver-implementer`  
**Automated Fitness Function:** `python .agents/skills/governance-exact-solvers/scripts/check_exact_solvers.py`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-exact-rational-fold-gate` | Stepwise GCD-reduced rational folding (no float coercion) |
| `goo-exact-rational-hamiltonian-solver-gate` | Rational sum preservation in discrete Hamiltonian solvers |
| `goo-exact-gaussian-rational-arithmetic-guard` | Exact algebraic decision paths and precision controls |
| `goo-finite-operational-closure-gate` | Finite operational closure at declared system class |
| `goo-five-way-finiteness-taxonomy-guard` | Separation of the five meanings of finiteness in quantum foundations |
| `goo-quotient-residual-cycle-closure-gate` | Total variation preservation and cycle boundary bounds |
| `goo-residual-projection-obstruction-solver-suite` | Oblique projection solvers and dual witness certificates |
| `goo-pea-representation-transport-pricing-gate` | Round-trip isomorphism laws and polynomial size bounds |
| `goo-nine-dot-gauge-break-transgression-operator` | Transgression operator boundaries and gauge breaks |
| `goo-simplex-normal-forms-contracts-consolidation` | Simplex normal form contract consolidation |

---

## 3. ROP Monad & Runtime Defect Firewall Suite

**Target Host:** `techne-code-inspector`  
**Automated Fitness Function:** `python .agents/skills/governance-rop-runtime/scripts/check_rop_runtime.py`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-operad-rop-result-monad-gate` | Elimination of naked exceptions; propagation of `Result[T, E]` monads |
| `goo-adversary-rop-monad-strictness` | Strict ROP container return enforcement across agent runtimes |
| `goo-probe-defect-firewall` | Separation of apparatus probe errors from computational defects |
| `goo-simulation-probe-error-defect-firewall` | Explicit exception raising on malformed simulation probes |
| `goo-atomic-trace-ledger-concurrency-guard` | Thread locking and atomic staging replacement for evidence traces |
| `goo-polymorphic-value-object-equality-guard` | Symmetric `__eq__` and `__hash__` rejecting string coercion |
| `goo-callback-immutable-family-snapshot-guard` | Immutable tuple snapshotting of test families at entry points |
| `goo-adversary-predictive-framing-bout-evaluator` | Separation of narrative dialogue rendering from raw JSONL traces |

---

## 4. Paper & Atlas Format Linter Suite

**Target Host:** `governance-paper-deposit` & `paper-package-techne`  
**Automated Fitness Function:** `python .agents/skills/governance-paper-deposit/scripts/check_paper_deposit.py`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-book-chapter-six-section-linter` | Mandatory 6-section chapter invariant under `coda_atlas/**/book/` |
| `paper-header-lexicon-gate` | 6-field Center-Justified header block and house lexicon firewall (renamed from `goo-paper-header-lexicon-gate`; Council: `L3_nous_glossa` / `L4_kanon`) |
| `goo-paper-companion-notebook-canonical-naming-gate` | Canonical `<paper_num>_<slug>.ipynb` notebook naming |
| `goo-paper-package-self-containment-gate` | Self-contained paper directories with zero monorepo path escapes |
| `goo-eadc-coordinate-integrity-guard` | `EA:FFF.SSS.BBB` decimal classification integrity |
| `goo-spine-batch-catalog-synchronizer` | Bijection between YAML spines, master index, and FTS5 indices |
| `goo-arxiv-resilient-stream-ingestion-gate` | Versioned arXiv fallback ingestion and raw PDF deletion |
| `goo-fastmcp-cross-encoder-hybrid-retrieval-gate` | SQLite FTS5 BM25 + dense vector hybrid search contracts |
| `goo-prompts-university-library-custody` | Domain goal prompts management with non-claim fences |
| `goo-cognitive-expectancy-envelope-harness` | Cognitive expectancy envelopes and prompt audit gates |
| `goo-novelist-dramatic-cochain-synthesizer` | Separation of dramatic dialogue rendering from JSONL envelopes |
| `goo-master-planning-office-reorg-guard` | Single-level master planning document layout |
| `goo-skill-md-factorization-sweep` | Extraction of subtopic modules into `references/` |
| `goo-gate-executability-requirement` | Executable check script requirement for packages labeled as gates |

---

## 5. Lean 4 Estate Verification Suite

**Target Host:** `paper-proof-signoff` & `governance-lean4-estate`  
**Automated Fitness Function:** `lake build` + `#print axioms` whitelist verification

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-lean4-estate-lake-elaboration-gate` | Continuous lake build compilation and axiom whitelist checks |
| `goo-lean4-evidence-gate` | Direct binding between claim ledger rows and Lean 4 declarations |
| `goo-lean4-strict-mechanization-guard` | Anti-toy mechanization firewall (mapping to domain invariants) |
| `goo-research-lean4-canonical-locus-guard` | Canonical root path verification for research programs |

---

## 6. Release, CAS & Integrity Gate Suite

**Target Host:** `paper-release` & `github`  
**Automated Fitness Function:** `python .agents/skills/governance-git-release/scripts/check_git_release.py`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-git-explicit-staging-safety-gate` | Prohibition of blind `git add .` or `git add -A` |
| `goo-changeset-shape-preflight` | Preflight inspection of git diff shapes prior to commit |
| `goo-cas-atomic-writes-integrity-gate` | Content-addressed storage atomic replacement integrity |
| `goo-standalone-release-archive-isolation-gate` | Extraction isolation, SHA-256 manifest matching, clean venv tests |
| `goo-producer-hash-provenance-gate` | Comparison of on-disk producer script hashes against generated provenance |
| `goo-receipt-replayability-gate` | Replayable execution trace audit for evidence receipts |
| `goo-sha256-content-hash-honesty-gate` | Prohibition of 64-zero SHA-256 placeholder hashes |
| `goo-source-disposition-sha256-witness-gate` | Witness verification for source dispositions |
| `goo-research-pre-deletion-blob-preservation-gate` | Pre-deletion ZIP snapshotting and SQLite blob ingestion |
| `declared-vs-actual-gate` | Parity between declared release manifests and on-disk assets (renamed from `goo-declared-vs-actual-gate`; Council: `L3_logos_sadc` / `L4_metronomos`) |
| `goo-operad-cli-ascii-output-coverage` | ASCII-safe console stdout output on Windows environments |

---

## 7. Host Parity & Sprint Governance Suite

**Target Host:** `governance-host-parity` & `sprint-devops-review`  
**Automated Fitness Function:** `python .agents/skills/governance-host-parity/scripts/check_host_parity.py`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-host-mirror-set-completeness-gate` | Derivation of host root set and complete mirror parity |
| `goo-agent-license-host-parity-gate` | Identical sub-operad licence sets across all 6 host mirrors |
| `goo-agent-licence-direction-check` | Directionality and capability ceilings of agent licences |
| `goo-canon-mirror-atomicity-hook` | Atomic multi-mirror write synchronization |
| `goo-sprint-impl-documents-hard-gate` | Mandatory presence of 4 sprint implementation documents |
| `goo-yaml-contract-dual-home-sync` | Dual-home synchronization across contract directories |
| `goo-computed-status-work-program` | Status work program validation |
| `goo-pr-relocation-bijection-guard` | Pull request file relocation tracking |
| `goo-budget-gate-default-scope-guard` | Default whole-garden scope verification for budget gates |

---

## 8. Strict Testing & Falsification Suite

**Target Host:** `techne-code-builder` & `rip-testing`  
**Automated Fitness Function:** `python -m pytest <path> --basetemp=scratch/pytest_tmp`

| Legacy Skill | Devolved Invariant |
| :--- | :--- |
| `goo-strict-test-execution-discipline-enforcer` | Targeted single-file or small-batch pytest sweeps |
| `goo-test-hygiene-four-rules-gate` | The 4-rule test hygiene gate (invariant, break, witness, mutation) |
| `goo-scoped-test-harness-synchronizer` | Scoped test harness alignment with bounded contexts |
| `goo-pytest-windows-basetemp-isolation-enforcer` | Mandatory `--basetemp` temp isolation on Windows |
| `goo-python-replay-admission-boundary-adversary` | Admission boundary replay tests |
| `goo-package-local-pythonpath-isolation-gate` | Package-local PYTHONPATH isolation (no monorepo escapes) |
| `goo-universe-sentinelica-playpen-math-conventions` | Math convention adherence in playpen test modules |
| `goo-symbol-game-shared-kernel-ddd-synchronizer` | Shared domain value object synchronization |
| `goo-bqnf-delta-conformance-oracle` | Conformance delta evaluation |
| `goo-operational-pipeline-attestation-gate` | Sealed pipeline execution trace verification |
