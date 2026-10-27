# Detailed definition: Fail-Closed Epistemic Verification (1)

**AuthorityEffect:** None.

Parent: [Fail-Closed Epistemic Verification](../../../../../rules/engineering/rl_fail_closed_epistemic_oracle_verification.md). Load for the matching predicate, not every task.

# Engineering Rule: Fail-Closed Epistemic Oracle Verification (`RL_ENG_ORACLE_001`)

**AuthorityEffect:** None.

## Mandate

External test oracles (such as `DiffTestOracle`) evaluating candidate diffs, mutations, and pull requests must enforce rigorous fail-closed execution semantics before returning an `ACCEPTED` verdict.

## Invariants

1. **Subprocess Environment Isolation:** Oracle subprocesses must strip sensitive host credentials, tokens, and secret environment variables while preserving minimal OS runtime variables (`PATH`, `SYSTEMROOT`, `TEMP`).
2. **Explicit Positive Test Execution Count:** An oracle must parse test runner stdout/stderr for positive passed counts (`passed > 0`) and assert zero failures (`failed == 0`) and zero collection/runtime errors (`errors == 0`).
3. **Rejection of Zero-Execution Suites:** A test suite terminating with exit code 0 but running zero tests (e.g. via `os._exit(0)` during test collection) must be classified as `ORACLE_TESTS_FAILED` with refusal code `NO_TESTS_EXECUTED`.
4. **Deterministic Receipt Binding:** The oracle receipt must record the SHA-256 digest of the evaluated patch, the executed test list, and the exact subprocess exit status.
5. **Hermetic Task Scope (Zero Cross-Task Evidence Borrowing):** An oracle or task runner must never borrow, inherit, or reuse test digests, validation receipts, or pass markers from a prior or foreign task; every candidate must execute the verification suite freshly against its own frozen candidate bytes (`TASK_EVIDENCE_BORROWING_LEAK`).
6. **Strict Input Schema Enforcement and Typed Refusal:** Evaluators and boundary ingress parsers must reject malformed, scalar, or ambiguous payload structures with an immediate typed refusal record, never silently coercing malformed types or dropping mismatched elements (`SILENT_INPUT_SCHEMA_COERCION`).
7. **Constructive Kernel Discharge (Zero Smuggled Axioms):** Mechanization verifiers must assert that proof dependencies resolve strictly to standard foundational axioms (`propext`, `Classical.choice`, `Quot.sound`); synthetic custom axioms introduced to bypass proof obligations must immediately refuse (`SMUGGLED_AXIOM_DECLARATION`).
8. **Fail-Closed Formal Verification Toolchain Gate (`RULE_FAIL_CLOSED_FORMAL_TOOLCHAIN_001`):**
   - **No Synthetic Success on Missing Toolchains:** When formal verification compilers or theorem auditors (e.g. Lean 4 Lake) are not installed, not found on system PATH, or experience process timeouts, runners must strictly return fail-closed outcomes (`False` or typed receipt status `UNAVAILABLE_TOOLCHAIN`).
   - **Prohibition of Non-Falsifiable Text Fallbacks:** A formal verification method must never fall back to scanning file text for `"sorry"` to return verification success. Text scanning is strictly an advisory static lint and must be segregated into explicit lint methods labeled with `AuthorityEffect: None`.
   - **Theorem Existence Pre-condition:** Querying axiom dependencies of a theorem must first verify the theorem's existence in the compiled or parsed module; querying a nonexistent theorem must return `THEOREM_NOT_FOUND` and never return synthetic standard axioms (`propext`, `Quot.sound`).
9. **CI/CD Auditor Census & Standby Gate Invariant (`RULE_CICD_AUDITOR_CENSUS_AND_STANDBY_GATE_001`):**
   - **Advisory Default Execution:** Any evaluation gate, auditor, or verifier declared as optional, experimental, or "left off for now" must execute by default in `STANDBY_OFF` mode, returning exit code 0 with advisory reporting so existing commit and CI workflows are not blocked unless `--enforce` is explicitly passed.
   - **Auditor Census Parity:** Any script created under `operations/use_cases/` or `domain/` containing an auditor marker in its name (`gate`, `audit`, `verify`, `census`, `evaluator`) and an executable `main()` entrypoint must be explicitly registered in `operations.use_cases.verification.stopping_point.AUDITORS`.
   - **Honest Register Status:** The auditor's registered status must strictly match CI reality:
     - `UNWIRED`: The module is not executed in active CI workflows (must state a clear rationale string).
     - `ADVISORY`: The module runs in CI under `continue-on-error: true`.
     - `WIRED`: The module runs blocking in CI and is observed to exit 0.
   - **Reconciliation Parity:** Running `py -3.12 -m operations.use_cases.verification.stopping_point --reconcile` must exit 0 with zero register drift findings before landing any gate change.
10. **Cross-Language Static Quality & Complexity Parity (`RULE_CROSS_LANGUAGE_COMPLEXITY_AND_INTEGRITY_001`):**
    - **Language-Specific Quality Metrics:** Code evaluation rubrics must evaluate each language using its sovereign native verification primitives rather than forcing imperative heuristics onto declarative or functional code:
      - *Python:* Evaluated via AST token analysis, `mypy` strictness, and `lizard`/`radon` cyclomatic complexity ($\text{CCN} \le 10$).
      - *Rust:* Evaluated via `clippy` restriction flags (`clippy::float_arithmetic`, `clippy::arithmetic_side_effects`, `clippy::unwrap_used`, `clippy::panic`), `rust-code-analysis`, and `cargo-geiger` unsafe audits.
      - *Lean 4:* Evaluated via kernel `#print axioms` (asserting zero `sorryAx` and tracking classical oracles), elaboration heartbeat ceilings (`maxHeartbeats`), tactic step length, and `lake exe shake` import hygiene.
