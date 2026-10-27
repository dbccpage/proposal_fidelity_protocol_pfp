# C023: Clifford Circuit Synthesis from Tableaux

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that turns hidden Clifford tableaux on up to 12 qubits into H, S and CNOT circuits
> that implement them exactly, within a gate budget, for under $0.50.

## 2. Why This Task

A Clifford unitary is fixed, up to global phase, by its tableau: the images of X₁…Xₙ and Z₁…Zₙ under conjugation, with signs. Checking a circuit against a tableau is a linear-time F2 simulation with sign bits. Producing the circuit requires a correct elimination order and, above all, correct sign handling; the sign row is where plausible circuits fail.

The task is the reverse of C021. There the solver reads Pauli words; here it must produce a gate sequence whose conjugation action matches exactly. It stresses host checks in OEWAS (Engine Workflows, Agents, Skills) that report which tableau entries are still wrong, and OEEIS (Engine Epistemic Immune System) screening of circuits correct on the F2 part and wrong on signs. Canonical-form synthesis is known (Aaronson and Gottesman 2004), so a pass shows competent assembly, not a new method.

## 3. Formal Problem and Bounds

Input: n with 1 ≤ n ≤ 12, and a target tableau T: for each j, the Pauli words T(Xⱼ) and T(Zⱼ) with signs ±1. Validity requires that the 2n images satisfy the symplectic relations: T(Xᵢ) and T(Zⱼ) anticommute iff i = j, and all other pairs commute. The F2 part is then an element of Sp(2n, F2), whose order is 2^{n²} ∏_{j=1}^{n} (2^{2j} − 1).

Gate set: H(q), S(q), CNOT(c, t). Pauli corrections are expressed in this set (Z = S², X = H S² H). Each case carries a gate budget B, set by the judge as the gate count of a pinned reference synthesis on that case. The circuit must have at most B gates.

Edge cases the hidden set must contain: the identity tableau (empty circuit is correct); a pure sign change (a Pauli); a single SWAP; a tableau whose F2 part is identity but every sign is flipped; T(Xⱼ) containing Y; n = 12 at the bound; a non-symplectic tableau (malformed); n = 13 (out of bounds).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input:

```json
{"case_id": "cl_04", "num_qubits": 2, "gate_budget": 6,
 "images": {"X0": "+XX", "X1": "+IX", "Z0": "+ZI", "Z1": "+ZZ"}}
```

Outputs:

```json
{"id": "cl_04", "status": "SOLVED", "circuit": [["CNOT", 0, 1]]}
{"id": "cl_05", "status": "OUT_OF_SCOPE", "witness": {"pair": ["X0", "Z1"], "expected": "commute"}}
{"id": "cl_06", "status": "UNKNOWN", "refusal_code": "GATE_BUDGET_NOT_MET", "best_gate_count": 41}
```

The circuit is applied left to right. `SOLVED` is correct only if conjugating each Xⱼ and Zⱼ through the circuit reproduces every target image including its sign, and the gate count is at most `gate_budget`. The circuit is the whole certificate. `OUT_OF_SCOPE` requires a pair of images whose commutation contradicts the symplectic relations.

## 5. Participant Packet

- `TASK.md` with §3, §4, the conjugation rules for H, S and CNOT on X and Z including signs (H: X ↔ Z, Y → −Y; S: X → Y, Y → −X, Z → Z; CNOT: X_c → X_c X_t, Z_t → Z_c Z_t), and the left-to-right convention.
- `examples/`: 10 cases with exact outputs: identity, one Pauli, SWAP, CNOT, a 3-qubit GHZ encoder, a sign-only case, two random 4-qubit Cliffords and two malformed cases.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 30 tableaux, uniformly random over the Clifford group modulo phase for n ∈ {2, 3, 4, 6, 8, 12}, plus structured ones (encoders for the codes in C022).
- **Relabel and gauge controls:** 10 controls: qubit permutation of a base case (circuit relabels, count unchanged), and a base case composed with a Pauli (signs change, F2 part fixed; budget raised by 6n, enough for a Pauli on every qubit).
- **Poisoned-but-schema-valid cases:** 6 cases: the F2 part of a base case with every sign flipped; a tableau that differs from a valid one in a single sign; a valid tableau whose images are listed in a shuffled key order.
- **Exact checker (Rust):** row-wise F2 tableau simulation with sign tracking.
- **Independent second checker:** a separately written Rust simulator that propagates each image column-wise, plus, for n ≤ 5, an exact dense unitary over Q(ζ₈) compared with the target's conjugation action up to global phase.
- **Mutation suite:** drop one S, swap control and target, reverse gate order, append a Z (sign-only error), exceed the budget by one, a non-symplectic witness that actually commutes as required.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the pinned reference synthesis that sets the budget, so E passes by construction on base cases. Tight-budget cases separate synthesis quality from reproducing the baseline: the judge builds them from a random circuit of known length L, sets B = L, and keeps only instances where the reference synthesis needs more than L gates. Such budgets are feasible by construction. Arm F does not apply.

## 8. Budget, Models and Provenance

$0.50 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 14B, Mistral Small 24B. The reference synthesis used to set budgets is pinned by SHA-256 in the judge packet and is not visible to any arm.

## 9. Pass Gates and Statistics

- **Capability gate:** 30/30 base and 10/10 controls, each accepted by both checkers.
- **Primary metric (pre-registered):** per-case exact-and-within-budget rate on base cases, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** tight-budget pass rate, sign-only error rate (F2 part right, sign wrong), cost per verified success.

## 10. Interpretation

- A high sign-only error rate in every arm means the shared weakness is phase bookkeeping; this points to host scratch space, not to the representation.
- If A passes tight-budget cases and E does not, the model found shorter circuits than the pinned reference; that is an efficiency result, not a lower bound on gate count.
- A and C tying means the controller and checks carry the result.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a circuit whose F2 action matches; signal 2 is a sign mismatch. This is a sign-flip antimorphism (AM-5 family) and must be quarantined, not averaged away.
- **Kinetic proofreading:** F2 match, then sign match, then budget, in that order.
- **Clonal maturation** (`ClonalSelectionEngine`) may refine repair operands for sign fixes across cases.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the current partial tableau after each gate so the model never recomputes conjugations in text.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose tableau), `I` (integrate an elimination plan), repeated `D` per column (the residual tableau moves toward identity), `R` for the sign residual, `E` when the sign residual is fixed by Pauli corrections, `M` on any gate that increases the residual, `T` at freeze. Logged measure: the number of tableau entries (F2 bits plus sign bits) that differ from the identity after applying the inverse of the partial circuit.

Operands expected: (1) clear a column to a single X with CNOTs; (2) turn Y into X with S, then X into Z with H; (3) fix signs last with Z = S² and X = H S² H; (4) check symplecticity before synthesis.

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_quantum_physics/src/clifford.rs`: exact H and S in Q(ζ₂₄), Sp(2, F2) and Sp(4, F2) enumeration, and `symplectic_order`.
- `engine/crates_rs/core_quantum_physics/src/pauli.rs` and `cyclotomic.rs` (`Cyc8`) for the dense second check.
- No n-qubit tableau type with signs exists in Rust; it is part of [U14](../../upgrades/u14_rust_quantum_stabilizer_port.md).
- Upgrades: base [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus U14. [U12](../../upgrades/u12_host_scratch_space_working_memory.md) is recommended.

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize a solver producing exact Clifford circuits, signs included, within a declared budget.
- **Does not support:** optimal gate counts, depth optimality, or anything about hardware compilation or noise.
- **Narrowest defensible claim:** "Arm X produced exact H/S/CNOT circuits within budget for k of 30 hidden tableaux (n ≤ 12)."
- **Next test:** C024, where the same local Clifford group acts on graph states and the task becomes a decision problem with a separating invariant.
