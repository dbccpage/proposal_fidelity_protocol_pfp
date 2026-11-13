# G11: Wiring the m114 Solver Adapter into the Search Policies

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to connect the
> m114 solver adapter to the Alpha Engine search policies, so that every prune and every funded
> key carries an independently re-verified exact certificate, with receipts, for under $0.50.

## 2. Why This Task

At HEAD `b55fc96a`, `19L57G1:research/m114_solver_adapter/README.md` names its next test: integration with the Alpha Engine search policy extensions and Driver A multi-key exploration. `research/x302_operational_reasoning/CLAIMS.md` names a neighbouring hook, belief-revision pruning, which is out of scope here.

`declared_constraint_pruned` takes a predicate or `pruned_keys`, and `declared_cost_budgeted` takes exact costs. Nothing yet certifies why a key is pruned. The adapter emits exact certificates in `Fraction`: `PrimalReceipt`, a feasible witness; `DualReceipt`, a vector of Farkas multipliers; `IntegerInfeasibilityReceipt`; the typed refusal `FUEL_EXHAUSTED`, which leaves the problem unmutated.

The glue code is modest. What matters is the refusal semantics: a refusal must never prune. The challenge stresses Symbol Game repair on typed refusals, OEWAS (Engine Workflows, Agents, Skills) code synthesis, and OEEIS (Engine Epistemic Immune System) rejection of forged certificates.

## 3. Formal Problem and Bounds

**Adapter.** At HEAD in `19L57G1:research/m114_solver_adapter/solver_adapter.py`: `SolverAdapter.solve(problem, fuel) -> StepResult`; `ProblemType` values `LINEAR_FEASIBILITY`, `BOUNDED_SMT`, `SAT_CNF` and `INTEGER_FEASIBILITY`; a `verify(problem)` method on each receipt, which raises `InvalidPrimalCertificateError` or `InvalidDualCertificateError`; `RefusalReason.FUEL_EXHAUSTED`.

`lean/SolverAdapter.lean` contains `primal_soundness`, `farkas_dual_soundness` and `refusal_preserves_state`.

**Policies.** At HEAD in `19L57G1:research/alpha_engine/search_policy.py`, every output passes `record_census`, which requires the explored, pruned and open keys to partition the retained keys.

**Wiring contract.** For each retained key `k`, the operator declares a constraint problem `P(k)` over the class features: item count, arities and new forms.

- **W-1.** `k` goes to `pruned_keys` only if `solve(P(k), fuel)` returns a `DualReceipt` or an `IntegerInfeasibilityReceipt`, and independent re-verification passes.
- **W-2.** `k` enters the `declared_cost_budgeted` pass only with a verified `PrimalReceipt`. Its cost is the declared exact `Fraction`.
- **W-3.** A refusal of `FUEL_EXHAUSTED`, `HORIZON_EXCEEDED` or `UNBOUNDED_VARIABLE` leaves `k` in `open_keys`: never pruned, never explored. The census must still partition.
- **W-4.** The policy `justification` and the receipt bind the SHA-256 of every certificate used.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new research tree. The tree consumes both source trees by import, with blob pins in `SOURCE_MANIFEST.json`, and edits neither. It holds: `wiring.py`, containing policy constructors that wrap the four existing ones; tests with live injections: a forged `DualReceipt` must raise; `fuel = 0` must leave the key open; a float coefficient must be refused by `_exact_q`; JSON receipts over the C3 folds.

An optional Lean statement would show that a refusal-preserving policy is still a partition.

`solve(case)` takes `{retained_keys, problems, fuel, budget}` and returns one of: `SOLVED`: `{explored, pruned, open, certificates}`; `OUT_OF_SCOPE`: a witness that `P(k)` lies outside the adapter's four problem classes, for example a non-linear constraint; `UNKNOWN`: `BUDGET_EXHAUSTED`.

## 5. Participant Packet

`TASK.md` gives W-1 to W-4, the pins and the schemas. Public examples, each with exact input and output:

1. The C3 L/`mu1` retained set (3 keys), with one infeasible, one feasible and one fuel-limited problem.
2. The C3 F/`mu1` set (5 keys), all feasible.
3. A poisoned certificate whose multipliers do not cancel. The expected output is a refusal.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

**Held-out cases:** Deeper nodes from the `mu1` branch trees; the L/`mu2` sole class (a License of a sole class is still an apply); held-out constraint systems, including one that is feasible over the rationals but infeasible over the integers, which needs integer infeasibility rather than Farkas; relabel controls that permute key order.

**Poisoned but schema-valid cases:** A key absent from the sealed quotient, which must raise `FabricatedClassError`; a certificate issued for another key's problem; a negative cost.

**Second checker.** Operator-written. It uses Rust `core_solvers` (exact weighted L1 LP) to re-derive feasibility, and checks Farkas multipliers with exact rationals from `core_kernel`.

**Gates.** `python ci/run_gates.py` and both trees' `verify.py`, at HEAD.

**Mutation suite.** The judge must reject a refusal mapped to pruned, a certificate used without verification, and a census that drops a key.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is the adapter at maximal declared fuel, wired by the operator's reference script. It defines the correct partition, so it serves as the oracle, not as a competitor. The challenge compares the arms' wiring code on correctness and cost. If A ties B, the typed refusal contract is easy enough for plain iteration.

## 8. Budget, Models and Provenance

The ceiling is $0.50 per arm. Candidate models: `qwen/qwen-2.5-7b-instruct`; `meta-llama/llama-3.1-8b-instruct`; Qwen3 14B; Mistral Small 24B.

Solver fuel is tool cost. Candidate code runs only in the sandbox.

## 9. Pass Gates and Statistics

**Capability gate.** All of the following must hold: every held-out partition equals the oracle's; every prune carries a verified certificate; every refusal leaves the key open; every poisoned case is refused with its named error; both trees' verifiers still pass.

**Differentiation test.** Exact McNemar across arms on the held-out cases, with 3 seeds.

**Primary metric.** Cost per verified wiring.

## 10. Interpretation

- **A pass.** The adapter can certify pruning decisions inside declared policies. The pruning is still a declaration about `P(k)`, not a fact about the keys.
- **Failure on the integer-infeasible case.** The Farkas route was over-applied.
- **Every arm agrees with the E oracle.** The challenge then measures synthesis cost only.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended:

- **Danger gate.** Signal 1 is "infeasible, so prune" with no certificate. Signal 2 is `verify()` raising, or a missing certificate digest.
- **Thymus.** The self panel is the adapter's own passing receipts, so valid Farkas certificates are not flagged.
- **Kinetic proofreading.** `HopfieldNinioProofreader` requires two independent verifications before a prune is accepted.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** Each feasible key follows `C E D T`: **C** exposes the problems; **E** is the solver certificate; **D** is the partition narrowing; **T** freezes the result.

`R M` marks a refused certificate, and `I` marks the assembled census.

**Logged.** Unverified certificates, refusal mappings and partition errors.

**Operands to mine.** A refusal maps to open, never to pruned; re-verify every certificate before use; integer infeasibility is not Farkas infeasibility.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only, at HEAD:** `19L57G1:research/m114_solver_adapter/` (`solver_adapter.py`, `lean/SolverAdapter.lean`, `README.md`, `CLAIMS.md`); `19L57G1:research/alpha_engine/` (`search_policy.py`, `driver_a.py`); `19L57G1:research/x302_operational_reasoning/CLAIMS.md`.

**the_symbol_game:** `engine/crates_rs/core_solvers`; `engine/crates_rs/core_kernel`; `pfp/domain/biochem/proofreading.py`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row extras: none.

## 14. Claim Hygiene

- **Supports:** the wired policies partition the retained keys with an exact, re-verified certificate behind every prune and every admission, and refusals leave keys open.
- **Does not support:**
  - that pruned classes are mathematically worse;
  - that a certificate is a License;
  - that uniqueness after pruning authorizes an apply;
  - any decision beyond the declared `P(k)`.
- **Narrowest defensible claim:** certified wiring of m114 into the Alpha Engine policies, checked on held-out folds.
- **Next test:** Driver A multi-key exploration under certified pruning, then the x302 belief-revision hook.
