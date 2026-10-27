# Test Suite Readiness: Symbol Game M-Theory Physics Challenge Swarm (C031)

**Status**: READY FOR VERIFICATION  
**Scope**: Comprehensive Scoped Test Suite for C031 (Anomaly-Free Chiral $U(1)$ Charge Assignments)  
**AuthorityEffect**: None  

---

## 1. Test Suite Summary

The comprehensive, opaque-box, requirement-driven E2E and unit test suite for C031 (Anomaly-Free Chiral $U(1)$ Charge Assignments) has been authored and verified against `c031_anomaly_free_u1_charges.md`, architecture designs, and SG-CP v1. All tests adhere strictly to the Examiner falsification methodology (verifying Invariant, Break, Witness, and Mutation) and strict claim hygiene (narrow, bounded, defensible claims with zero hype verbs).

| Test Module | Focus Area | Tests | Status | Execution Time |
|:---|:---|:---:|:---:|:---:|
| `tests/test_participant_packet.py` | Participant packet schema, 12 public worked examples, runner CLI, canonical RFC 8785 JSON formatting | 4 | PASS | 0.47s |
| `tests/test_reference_solver.py` | Reference solver mathematical invariants, $n \le 4$ non-existence identity, exact counts for $n=5,6$, $O(1)$ solve_pair resolvent, spectator pair completions, DDC 8-letter hash chain | 9 | PASS | 0.38s |
| `tests/test_dual_checkers.py` | Dual independent checkers, 46 judge cases (32 base, 8 controls, 6 poisoned), manifest UTF-8 ordinal sorting, 100% dual evaluator agreement | 5 | PASS | 1.40s |
| `judge_packet/mutation_suite/test_c031_checker_mutations.py` | Mutation testing suite across 36 corrupted certificates verifying 100% kill rate (Checker 1 & Checker 2) | 37 | PASS | 0.63s |
| `tests/test_governance_and_commit_reveal.py` | Tier T3 budget controller ($1.00 ceiling, $0.05 target, 70B ceiling, no fallbacks), Adversary 7-Act reality gate, 3-Phase Commit-Reveal runner | 4 | PASS | 2.54s |
| `tests/test_e2e_challenge.py` | Comprehensive 4-Tier E2E test suite (Features, boundaries $n \in [3, 12], Q \le 2\cdot 10^6$, cross-seam integration, full bout) | 12 | PASS | 3.38s |
| **Total** | **Complete C031 Challenge Verification** | **71** | **PASS** | **8.80s** |

---

## 2. Test File Inventory

### 1. `tests/test_participant_packet.py` (4 tests)
- `test_task_markdown_exists_and_contains_formal_invariants`: Verifies existence and structure of `TASK.md`, confirming linear and cubic Diophantine anomaly equations, $n \le 4$ identity theorem, primitivity, chirality, canonical form, and closed refusal catalog.
- `test_accounting_template_fields`: Validates `accounting.json`, confirming Tier T3, budget ceiling $1.00, target $0.05, model parameter ceiling 70B, and `allow_fallbacks: false`.
- `test_public_examples_inventory_and_schema`: Validates all 12 public worked examples against the reference solver, confirming exact outputs, completion lengths ($n - m$), witness structures, and statuses (9 `SOLVED`, 3 `OUT_OF_SCOPE`).
- `test_runner_execution_on_examples`: Verifies `runner.py` CLI execution against `examples/`, validating output answers in RFC 8785 canonical JSON-L.

### 2. `tests/test_reference_solver.py` (9 tests)
- `test_n3_n4_non_existence_identity`: Validates that for $n=3$ and $n=4$, no chiral anomaly-free spectra exist for any bound, confirming $(a+b+c)^3 - a^3 - b^3 - c^3 = 3(a+b)(b+c)(c+a) = 0$.
- `test_n5_enumeration_exact_counts`: Validates analytical enumeration counts and canonical representatives for $n=5$ ($B=9 \to 1$, $B=10 \to 2$, $B=12 \to 2$).
- `test_n6_enumeration_exact_counts`: Validates analytical enumeration counts and canonical representatives for $n=6$ ($B=5 \to 1$, $B=6 \to 2$, $B=10 \to 2$).
- `test_solve_pair_quadratic_resolvent`: Validates $O(1)$ quadratic resolvent `solve_pair` across solvable, zero-sum, and incompatible sum/cubic-sum pairs.
- `test_complete_chiral_u1_solvable_cases`: Validates completion of partial fixed charges into full chiral spectra, including spectator pair completion for $n=12, Q=10^5$.
- `test_complete_chiral_u1_no_completion_refusal`: Validates certified non-existence of completions on vector-like traps.
- `test_out_of_scope_witnesses`: Validates structured `OUT_OF_SCOPE` parameter domain violation witnesses (`fixed_charge_exceeds_bound`, `fixed_charge_zero`, `too_many_fixed_charges`).
- `test_closed_refusal_codes`: Validates closed `UNKNOWN` refusal codes (`N_OUT_OF_BOUNDS`, `BOUND_OUT_OF_BOUNDS`, `MALFORMED_QUERY_TYPE`, `MALFORMED_CASE_STRUCTURE`).
- `test_ddc_tracer_hash_chaining`: Validates DDC 8-letter operational tracer ($\mathcal{A}_{\mathrm{DDC}} = \{E, R, C, I, \Lambda, D, M, T\}$) with unbroken SHA-256 step hashes.

### 3. `tests/test_dual_checkers.py` (5 tests)
- `test_base_cases_dual_evaluation_agreement`: Validates dual checker evaluation across all 32 base cases covering $n \in [5, 12]$, bounds up to $2\cdot 10^6$, enumerations, and completions.
- `test_control_cases_physical_invariance`: Validates that physical invariance controls (permutation of fixed charges, charge conjugation negation, different partitions) pass dual checkers and preserve `NO_COMPLETION` refusals.
- `test_poisoned_cases_dual_evaluation_agreement`: Validates that poisoned cases (vector-like traps, factor 2/3 traps, $Q=10^6, 2\cdot 10^6$ bounds) achieve dual agreement with 0 defects.
- `test_checker_disagreement_error_tripping`: Validates that `evaluate_dual` flags corrupted inputs and raises `CheckerDisagreementError` when checkers conflict.
- `test_manifest_cryptographic_integrity_and_ordinal_sorting`: Validates `manifest.json` against all 87 files on disk, ensuring SHA-256 byte-level agreement and strict ordinal UTF-8 sorting.

### 4. `judge_packet/mutation_suite/test_c031_checker_mutations.py` (37 tests)
- Evaluates 36 corrupted certificate mutations (`mut_01` through `mut_36`):
  - Linear anomaly violation ($\sum q_i \neq 0$).
  - Cubic anomaly violation ($\sum q_i^3 \neq 0$).
  - Zero charge injection ($q_i = 0$).
  - Non-primitive common factor scaling ($k \cdot q$, $\gcd > 1$).
  - Vector-like trivial pair injection ($q, -q$).
  - Inverted or non-canonical signs ($s_n > -s_1$).
  - Solution count spoofing and duplicate solutions.
  - False `NO_COMPLETION` claim when a valid completion exists.
- Verifies 100% kill rate (36/36 killed independently by Checker 1 and Checker 2).

### 5. `tests/test_governance_and_commit_reveal.py` (4 tests)
- `test_budget_gate_configuration_and_limits`: Validates BudgetController initialization, $1,000,000\,\mu\text{USD}$ hard ceiling, $50,000\,\mu\text{USD}$ target, and fail-closed halting on over-budget quotes.
- `test_budget_gate_fallback_and_model_admittance`: Validates rejection of `allow_fallbacks=True`, admission of $\le 70\text{B}$ open-weights models, and rejection of $> 70\text{B}$ models.
- `test_adversary_gate_verdict_and_bundle_persistence`: Validates the novelistian 7-Act dialectic novella generation, StructureBench reverse write order 4-file bundle (`novella.md` $\to$ `dda_actions.jsonl` $\to$ `summary.json` $\to$ `receipt.json`), atomic renaming, dual-sink persistence, and `RunFolderExistsError` collision protection.
- `test_commit_reveal_runner_three_phases_and_tamper`: Validates the complete 3-phase Commit-Reveal state machine: Phase 1 commitment, Phase 2 freeze, Phase 3 reveal and scoring, and cryptographic tamper detection on manifest modification.

### 6. `tests/test_e2e_challenge.py` (12 tests across 4 Tiers)
- **Tier 1 (Feature Coverage)**:
  - `test_tier1_n5_enumeration_exact_solution`: Validates exact enumeration and dual verification on $n=5, B=9$.
  - `test_tier1_complete_solvable_case`: Validates completion of fixed charges on $n=5, B=10$.
  - `test_tier1_spectator_pair_completion`: Validates completion with spectator pairs on higher fermion counts.
  - `test_tier1_non_existence_refusal`: Validates certified refusal on vector-like traps.
- **Tier 2 (Boundary Values & Limits)**:
  - `test_tier2_extreme_charge_bound_2e6`: Validates arbitrary-precision integer arithmetic on large bounds ($Q=2\cdot 10^6$).
  - `test_tier2_fermion_count_extremes`: Validates behavior at boundaries $n=3$ (empty) and $n=12$ (solvable).
  - `test_tier2_closed_refusal_codes`: Validates all closed refusal codes at boundary conditions.
  - `test_tier2_out_of_scope_witnesses`: Validates all 3 `OUT_OF_SCOPE` witness kinds.
- **Tier 3 (Cross-Seam Integration)**:
  - `test_tier3_commit_reveal_runner_and_governance`: Validates end-to-end integration of CommitRevealRunner, BudgetGate, and AdversaryGate.
  - `test_tier3_ddc_tracer_receipt_chain`: Validates DDC tracer step chaining and hash verification on end-to-end solve.
- **Tier 4 (Real-World Scenarios & Falsification)**:
  - `test_tier4_all_46_judge_cases_pass_with_100_percent_agreement`: Evaluates all 46 hidden cases (32 base, 8 controls, 6 poisoned) with dual evaluator, asserting 100% agreement and 0 defects.
  - `test_tier4_100_percent_mutation_kill_rate`: Verifies that all 36 mutations in `mutation_suite/mutations/` produce `verdict == "FAIL"` in `evaluate_dual`.

---

## 3. Examiner Falsification Matrix

| Invariant | Break Attempt | Witness | Mutation Test | Result |
|:---|:---|:---|:---|:---|
| Linear Anomaly $\sum q_i = 0$ | Inject perturbation $\pm 1$ into single charge | Residual $\sum q_i \neq 0$ | `mut_01`–`mut_04` | KILLED (Checker 1 & 2 reject) |
| Cubic Anomaly $\sum q_i^3 = 0$ | Swap charges preserving linear sum but changing cubes | Cubic sum $\sum q_i^3 \neq 0$ | `mut_05`–`mut_08` | KILLED (Checker 1 & 2 reject) |
| Primitivity $\gcd(|q|) = 1$ | Rescale valid spectrum by factor of 2 or 3 | $\gcd(|q|) > 1$ | `mut_09`–`mut_12` | KILLED (Checker 1 & 2 reject) |
| Chirality $\operatorname{Counter}(q) \neq \operatorname{Counter}(-q)$ | Insert vector-like cancellation pair $(p, -p)$ | Multiset equality under negation | `mut_13`–`mut_16` | KILLED (Checker 1 & 2 reject) |
| Canonical Representative | Negate spectrum or alter lexicographical order | $s_n > -s_1$ or non-minimal sort | `mut_17`–`mut_20` | KILLED (Checker 1 & 2 reject) |
| Non-Zero Charges $q_i \neq 0$ | Insert trivial zero charge $q_i = 0$ | $0 \in q$ | `mut_21`–`mut_24` | KILLED (Checker 1 & 2 reject) |
| Bound Compliance $|q_i| \le Q$ | Exceed declared charge bound $Q$ | $\max(|q_i|) > Q$ | `mut_25`–`mut_28` | KILLED (Checker 1 & 2 reject) |
| Set Equality in Enumeration | Add duplicate or omit valid solution | Missing/spurious solution | `mut_29`–`mut_32` | KILLED (Checker 1 & 2 reject) |
| Completion Claim Honesty | Claim `NO_COMPLETION` when solution exists | Refuter finds valid completion | `mut_33`–`mut_36` | KILLED (Checker 1 & 2 reject) |

---

## 4. How to Run the Tests

In compliance with repository governance rules, **never execute whole-suite sweeps (`pytest .`)**. Tests must be run locally via targeted commands:

```bash
# 1. Participant packet tests (4 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_participant_packet.py -v

# 2. Reference solver & Diophantine engine tests (9 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_reference_solver.py -v

# 3. Dual independent checkers & cases tests (5 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_dual_checkers.py -v

# 4. Hostile mutation kill suite (37 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/judge_packet/mutation_suite/test_c031_checker_mutations.py -v

# 5. Governance, Tier T3 budget gate, Adversary gate, and Commit-Reveal runner (4 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_governance_and_commit_reveal.py -v

# 6. Comprehensive 4-Tier E2E integration test suite (12 tests)
python -m pytest demos/certified_challenges/c031_anomaly_free_u1_charges/tests/test_e2e_challenge.py -v
```

---

## 5. Claim Hygiene Summary (AuthorityEffect: None)

1. **What this evaluates:** Whether a solver can systematically enumerate and complete integer solutions to the Diophantine system $\sum q_i = 0, \sum q_i^3 = 0$ under primitivity, chirality, and canonical sorting within declared bounds.
2. **What this does not evaluate:** Real-world particle physics phenomenology, string vacuum selection, dark sector $U(1)$ gauge groups, or continuum field theories.
3. **Narrowest defensible claim:** "The algorithm satisfies linear and cubic Diophantine constraints under primitivity and chirality on all 46 evaluated queries within declared bounds."
4. **Next test needed:** Evaluate C032 (six-dimensional supergravity anomaly cancellation with tensor and Yang-Mills multiplets).
