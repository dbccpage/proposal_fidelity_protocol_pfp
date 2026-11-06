# C059: One Certificate-Solver Skeleton, Three Families

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize one frozen certificate-solver skeleton that transfers, by adding only a small family adapter each time, to exact LP, max-flow and commuting-Pauli stabilizer problems within a small incremental budget, for under $1.00 in total.

## 2. Why This Task

C051, C052 and the Q40 rerun C021 each ask for a certificate-emitting solver. Most of each module is the same:

- exact parsing;
- a status taxonomy;
- never raising on bad input;
- a self-check before emitting;
- canonical output.

Only the mathematical core differs. The Symbol Game claims to learn from its own runs through operands (U04). This challenge measures whether it does: whether what was learned on one family lowers the cost of the next one.

Verification stays cheap and exact per family, with duals and Farkas vectors, cuts, and stabilizer ground-space certificates. The experiment is transfer, measured against from-scratch controls at equal incremental budget. It stresses the U04 operand registry and composition, the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that sequences stages, and the OEEIS (Omega Engine Epistemic Immune System) admission of operands. A positive result supports reuse on these three families only.

## 3. Formal Problem and Bounds

The families and their certificate contracts are exactly those of their source specs:

- **LP:** [C051](c051_exact_lp_solver_with_duals.md), inequality form with `m, n ≤ 30`.
- **FLOW:** [C052](c052_maxflow_mincut_certificates.md), `N ≤ 200`.
- **STAB:** the Q40 commuting-Pauli ground-space contract as rerun in [C021](../c_quantum/c021_q40_r_synthesis_as_intended.md). It returns a solved ground space with its certificate, or an anticommuting-pair `OUT_OF_SCOPE` witness.

The skeleton is a module `skeleton.py` exposing `run(case, adapter) -> dict`. It owns the status envelope, exact rational and integer parsing, canonical serialization and limits. It maps any exception to a typed `UNKNOWN` and calls `adapter.self_check` before emitting. An adapter implements `parse`, `solve`, `certify` and `self_check` for one family.

Protocol per seed:

1. **Stage 1:** synthesize the skeleton plus the first family's adapter (at most $0.40), then freeze the skeleton's SHA-256.
2. **Stages 2 and 3:** synthesize only an adapter for each next family (at most $0.15 each). The judge verifies that the skeleton hash is unchanged.
3. **Controls:** from-scratch controls for the stage-2 and stage-3 families (at most $0.15 each), in a fresh context with no skeleton and no operands.

Seeds rotate the family order so that each family appears once in each position: LP→FLOW→STAB, FLOW→STAB→LP, STAB→LP→FLOW.

## 4. Deliverable and Output Contract

**Mode: frozen modules.** Per seed the deliverables are the frozen skeleton, three adapters and two scratch modules, all hashed before reveal, with no model calls at scoring. Outputs use each family's own schema. The skeleton adds one envelope field, recording the adapter and skeleton hashes.

```json
{"case_id": "mf_h_07", "family": "FLOW", "n": 3, "s": 0, "t": 2, "arcs": [[0,1,"4"],[1,2,"3"]]}
{"case_id": "mf_h_07", "status": "SOLVED", "value": "3", "flow": ["3","3"], "cut_S": [0, 1], "provenance": {"skeleton_sha256": "<64 hex>", "adapter_sha256": "<64 hex>"}}
{"case_id": "lp_h_11", "status": "UNKNOWN", "code": "ADAPTER_EXCEPTION", "provenance": {"skeleton_sha256": "<64 hex>", "adapter_sha256": "<64 hex>"}}
```

A certificate is complete by the source spec's definition. An adapter that edits the skeleton's file, or that monkeypatches the skeleton at import, voids the transfer condition for that seed. The judge checks imports and hashes.

## 5. Participant Packet

- `TASK.md` with the skeleton interface, stage budgets, the rotation, and the three family contracts with their JSON Schemas.
- The public examples of C051 (14), C052 (10) and C021, each with verbatim JSON.
- `runner.py`, which runs `skeleton.run` with each adapter in the sandbox and enforces the hash freeze.
- `accounting.json`, with one row per stage and control.

## 6. Judge Packet

- **Hidden base:** a fresh set per family, disjoint from the C051, C052 and C021 hidden sets: 20 LP, 20 FLOW and 20 STAB base cases.
- **Relabel and gauge controls:** 8 per family, of the kinds defined in each source spec (variable and constraint permutations; node relabelling and arc reversal; qubit permutation and Pauli relabelling).
- **Poisoned but schema-valid:** 4 per family, including a case with one family's schema but another family's `note`.
- **Exact checkers:** C051's Rust LP checker and C052's Rust flow checker. For STAB, the U14 Rust checker if available; otherwise the Q40 Python checker is used only after its unguarded `int(...)` conversions are fixed and its mutation suite passes; the review documents a scoring crash there.
- **Independent second checkers:** as in each source spec.
- **Mutation suites:** the union of the source suites, plus two transfer-specific corruptions: a skeleton envelope with the wrong family schema, and an adapter that raises (the skeleton must map it to `UNKNOWN`, never crash the runner).

## 7. Arms and Baselines

- **A:** the Symbol Game. Operands mined from stage-1 runs (U02) are admitted and composed into later-stage prompts (U04).
- **B:** ordinary, with the model's own plain-text notes carried forward.
- **C:** A's controller and operands rendered as plain text.
- **D:** best-of-N per stage, with the skeleton available but no operands.
- **E:** the three reference solvers wrapped in a hand-written skeleton: a pinned exact LP solver, the `omega_solvers` network simplex, and the Q40 reference `omega_engine_symbol_game/domain/quantum/stabilizer_solver.py`, or its U14 Rust port.

E makes no transfer claim. It shows that each hidden set is solvable and that the contracts are consistent, so "matching E" here means only reaching reference capability. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$1.00 per arm in total: $0.40 for stage 1, $0.15 each for stages 2 and 3, and $0.15 for each scratch control. That is about 2.8 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `deepseek/deepseek-r1-distill-llama-70b`. The same model is used across all stages and arms. The receipt records operand IDs and admission receipts per stage.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module (skeleton and adapter), the failing case and the typed rejection; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController` for each stage's sub-ceiling; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, each family's frozen adapter plus skeleton passes all base, control and poisoned cases, in every position.
- **Primary metric (pre-registered):** transfer gain, defined as the stage-2 and stage-3 pass rate with the skeleton minus the pass rate of the from-scratch control at equal budget. It is tested by an exact McNemar test on paired (seed, family, case) rows within each arm.
- **Secondary:** A vs B on the transfer condition, by McNemar with Holm correction across A–B, A–C and A–D at α = 0.05; the incremental cost to the first all-public pass.
- **Seeds:** 3, one per rotation. With 6 transfer episodes per arm, power is low, and the distribution is reported.

## 10. Interpretation

If transfer gain is positive in A and absent in B, operands compose usefully. If it is positive in both, the frozen skeleton does the work, not the operand machinery. If it is positive in D, the skeleton alone explains it. If it is gone in C, the representation matters for operand uptake. If STAB transfer fails everywhere, the skeleton's abstractions do not reach GF(2) phase-tracked algebra, and that is a useful negative result.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Operands still pass U04's immune admission:

- a thymus-style check against a self panel of known-good public outputs;
- danger gating on operands whose use raised failures;
- decay of unused operands.

Expected antimorphisms:

- AM-4 (re-synthesizing the skeleton inside an adapter);
- AM-FSP-2 (a certificate of the wrong family);
- AM-3 (the self-check bypassed).

Layer 2: grammar-masked JSON per family schema, via `carrier_gbnf` (unwired, and dependent on U06). Layer 1 is not applicable. Scratch space: the host keeps the skeleton interface and the admitted operands as the persistent scratch state carried across stages.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern:

- **Stage 1:** `C`, `Λ` (skeleton/adapter split), `I`, `R`, `D` steps, `E`, `T`.
- **Transfer stages:** `C` (operands and skeleton), `I` (adapter), `R`, a few `D` steps, `E`, `T`. A transfer stage that needs a skeleton change emits `M` with `SKELETON_INSUFFICIENT` and names the missing hook.

The `ObstructionScore` sets Φ₁ to the certificate violation mass defined in each source spec, and `active_count` to failing public cases. Γ₂ is unused (0).

Operands to mine:

- a never-raise envelope that maps exceptions to typed `UNKNOWN`;
- exact canonical rational parsing;
- a self-check before emitting;
- the list of skeleton hooks that the stabilizer family needed but the first family did not.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers` (network simplex, and the LP checker home).
- `omega_engine_symbol_game/domain/quantum/` (the Q40 reference solver and checker, both Python and flagged by the review) and `omega_engine_projects/mssn_sn_symgam/demos/demo_q40_quantum_solver/`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extras [U04](../../upgrades/u04_operand_registry_and_composition.md) and [U10](../../upgrades/u10_synthesis_loop_v2.md). [U14](../../upgrades/u14_rust_quantum_stabilizer_port.md) is recommended for the STAB checker.

## 14. Claim Hygiene

- **Supports:** with a frozen skeleton, adapters for later families reached certified passes at the recorded incremental cost, compared with from-scratch controls at equal budget, per arm and per rotation.
- **Does not support:** general transfer learning, transfer to families outside these three, or the claim that operands caused a gain unless A differs from D.
- **Narrowest defensible claim:** on LP, FLOW and STAB with these budgets, the measured transfer gain in arm A was X (interval Y), against Z in arm B.
- **Next test:** a fourth unseen family (assignment, [C053](c053_assignment_with_potentials.md)) added with no new skeleton budget.
