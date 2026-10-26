# C021: Q40-R: The ChatGPT Stabilizer Challenge Run as Specified

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce an
> exact, certificate-generating stabilizer ground-state solver that passes a hidden judge
> packet you have never seen, for under $0.50 per arm.

## 2. Why This Task

This is ChatGPT's Q40 challenge, rerun as it was written. The first attempt did not test it: the solver was written by a coding agent, the 40 cases were generated locally and sat in public view, and the two synthesis attempts were single three-turn trajectories (the first stateless, the second stateful and sandboxed after PR #158), neither of which converged ([00_q40_review.md](../00_q40_review.md), §2–§4). End-to-end synthesis by a model of at most 70B parameters is therefore untested, not refuted.

Generation is hard because the solver must get phase tracking right (Y = iXZ), extract an independent commuting basis over F2, and enumerate the full ground space. Verification is cheap: every claim in a `SOLVED` answer can be checked by exact symplectic and rational arithmetic in well under a second for n ≤ 8.

The task stresses the engine turn driver, stateful retraction, the sandbox and the matched-arms harness in OEWAS (Omega Engine Workflows, Agents, Skills). It also exercises OEEIS (Omega Engine Epistemic Immune System) screening of schema-valid but wrong certificates. The commuting-Pauli stabilizer formalism is textbook (Gottesman 1997, quant-ph/9705052), so a pass is real but modest evidence of capability. A pass in arm A alone is not evidence that the game adds capability; that needs the arm comparison in §9.

## 3. Formal Problem and Bounds

Input: n qubits with 1 ≤ n ≤ 8 and M ≤ 24 terms. The Hamiltonian is

H = Σᵢ wᵢ (I − sᵢ Pᵢ) / 2,

where Pᵢ ∈ {I, X, Y, Z}^⊗n is a Pauli string, sᵢ ∈ {−1, +1} is the target eigenvalue and wᵢ ∈ Q, wᵢ > 0. Identity terms, repeated words, opposing target signs on the same word and unused qubits are all permitted.

- If every pair (Pᵢ, Pⱼ) commutes, return `SOLVED`: the exact ground energy E₀ ∈ Q, the full ground-space dimension, and a certificate.
- If any pair anticommutes, return `OUT_OF_SCOPE` with a genuinely anticommuting pair as witness.
- If the case is malformed or outside the bounds (n > 8, M > 24, a non-positive weight, a weight that is not a `[num, den]` pair, a word of the wrong length, a missing, non-string or duplicate term `id`), return `UNKNOWN` with a refusal code.

With an independent generator set G₁…G_k (k ≤ n) and exact decompositions Pᵢ = σᵢ ∏ⱼ Gⱼ^{eᵢⱼ}, σᵢ ∈ {±1}, the energy of an assignment b ∈ {±1}^k is Σᵢ wᵢ (1 − sᵢ σᵢ ∏ⱼ bⱼ^{eᵢⱼ}) / 2. The ground-space dimension is |argmin| · 2^{n−k}. Identity terms contribute wᵢ(1 − sᵢ)/2 to every assignment. A term equal to −I (for example from a repeated word with a sign) must be handled through σᵢ.

Edge cases the hidden set must contain: a single identity term; all terms identity; repeated words with opposing signs (irreducible frustration); Y-heavy words where a phase error flips σᵢ; k = 0 and k = n; unused qubits; a term that is a product of others with sign −1; n = 8, M = 24 at the bound; and one-past-the-bound cases (n = 9, M = 25).

## 4. Deliverable and Output Contract

A frozen Python module exposing `def solve(case: dict) -> dict`, with no network, no file writes and no imports beyond the standard library.

**Input schema: the original challenge interface.** Every arm is shown this as JSON, not described in prose:

- `id`: a case identifier string;
- `n`: the number of qubits;
- `terms`: a list of terms, each with
  - `id`: a string, unique within the case;
  - `P`: the Pauli word;
  - `w`: the weight as a rational pair `[num, den]` with `num > 0` and `den > 0`;
  - `target`: +1 or −1.

The local demo's `generate_benchmark.py` uses different field names (`case_id`, `num_qubits`, `pauli`, `weight` as a string, `target_sign`, integer term positions). That is not this interface, and no arm is shown it.

```json
{"id": "h_07", "n": 3,
 "terms": [{"id": "t_a", "P": "XYZ", "w": [3, 2], "target": 1},
           {"id": "t_b", "P": "ZZI", "w": [1, 1], "target": -1}]}
```

Output, one of:

```json
{"id": "h_07", "status": "SOLVED", "energy": [0, 1], "degeneracy": 2,
 "basis": ["t_a", "t_b"], "decomposition": [{"id": "t_a", "mask": 1, "phase": 1},
 {"id": "t_b", "mask": 2, "phase": 1}], "minimizers": [2]}
{"id": "h_08", "status": "OUT_OF_SCOPE", "witness": ["t_a", "t_c"]}
{"id": "h_09", "status": "UNKNOWN", "refusal_code": "NUM_QUBITS_OUT_OF_BOUNDS"}
```

In the `h_07` example, XYZ and ZZI differ on two qubits, so they commute and are independent (k = 2). The energy is (3/2)(1 − b₁)/2 + (1 + b₂)/2, which is minimized only at b₁ = +1, b₂ = −1 (mask 2). So E₀ = 0 and the degeneracy is 1 · 2^{3−2} = 2.

`energy` is a reduced `[num, den]` with `den > 0`. `basis` lists the string term IDs used as generators. Every term reference in the output uses the input's string `id`, never a list position. A witness lists its two IDs in lexicographic order. `decomposition` gives, for every term, the generator bitmask and the sign σᵢ ∈ {1, −1}. `minimizers` lists every assignment bitmask achieving E₀ (bit j = 1 means bⱼ = −1). A `SOLVED` certificate is complete only if the checker can recompute, from the input alone: that `basis` is independent and commuting, that every decomposition holds with the stated sign, that every listed minimizer has energy E₀, that no other assignment has lower energy, and that `degeneracy` = |minimizers| · 2^{n−k}. An `OUT_OF_SCOPE` witness is complete only if the two terms anticommute. Refusal codes come from a closed list published in `TASK.md`.

## 5. Participant Packet

- `TASK.md`: §3 and §4 above, the closed refusal-code list, and the input and output JSON schemas.
- `examples/`: 12 public cases, each with exact input JSON in the §4 interface and exact expected output JSON:
  - 5 `SOLVED`, including one Y-heavy phase case and one opposing-sign case;
  - 3 `OUT_OF_SCOPE`;
  - 2 `UNKNOWN`, one of them a duplicate term `id`;
  - 2 relabel pairs.

  Every example uses string term IDs that are not positional, such as `"t_a"` or `"zz_left"`, so a solver that echoes list indices fails visibly. The examples are built fresh for this interface; none are copied from the demo's `cases/`.
- `runner.py`: imports the frozen module inside the sandbox and writes `answers.jsonl`.
- `accounting.json`: per-call provider, model ID, generation ID, tokens and billed cost.

## 6. Judge Packet

**Origin and reporting mode.** Two modes, never mixed.

- **Mode 1: Q40 as specified.** ChatGPT's own judge packet (`sg_q40_judge.zip`) is used unchanged, obtained directly from ChatGPT: its cases, its case mix and its checker. Only this mode may be reported as a run of ChatGPT's challenge.
- **Mode 2: Q40-R follow-on benchmark.** If that packet cannot be obtained, an operator who did not build or tune any arm generates a fresh hidden set from this spec, in the same §4 interface.
  - Its case mix differs from ChatGPT's, so results are reported as a follow-on benchmark, never as an unchanged run of ChatGPT's judge.
  - The receipt records `judge_origin: "chatgpt_packet"` or `"independent_follow_on"`, and every README or summary must repeat it.

In either mode, `generate_benchmark.py` and the 40 cases in the demo folder are public and may not be reused as hidden cases.

**Hidden set (mode 2).** Every case is in the §4 interface: string `id`, integer `n`, and terms with unique string `id`, `P`, a rational-pair `w` and `target`.

- **32 base cases:** at least 20 `SOLVED`, at least 6 `OUT_OF_SCOPE`, at least 3 `UNKNOWN`.
- **8 relabel controls.** Energy and degeneracy stay fixed unless noted.
  - qubit permutation;
  - term reordering;
  - renaming of every term `id`;
  - rescaling every weight by a common positive rational (the energy scales with it);
  - a local Clifford change of basis applied to every term, with any sign it introduces absorbed into `target`, so the new H is unitarily equivalent.
- **6 poisoned-but-schema-valid cases,** scored separately:
  - an anticommuting pair hidden among 23 commuting terms;
  - a word whose Y count makes a naive phase rule give the wrong σᵢ;
  - an unreduced weight pair such as `[6, 4]` that must reduce to 3/2;
  - a term equal to a signed product of others;
  - term IDs that sort differently as strings than as positions;
  - a duplicate term `id`, which must return `UNKNOWN`.

**Checkers.** The exact checker is the Rust port of the Q40 certificate checker (U14): F2 symplectic rank, phase-tracked Pauli products, exhaustive 2^k enumeration, rational energies, with every model-supplied integer parsed through a guarded path that rejects rather than crashes. The independent second checker builds the 2^n × 2^n Hermitian matrix over Q(i), confirms that H − E₀I is positive semidefinite by an exact LDLᴴ factorization, and confirms that its kernel dimension equals `degeneracy` by exact rank. It never uses the claimed basis, so it shares no logic with the first checker, and it runs on every case, not only n ≤ 6. The numpy float checker in `omega_engine_symbol_game/infrastructure/quantum/dense_checker.py` may appear only as labelled secondary evidence.

**Mutation suite.** At least 30 corrupted outputs the checker must reject: sign-flipped σᵢ, energy off by one term weight, unreduced fraction, missing minimizer, extra non-minimizer, degeneracy without the 2^{n−k} factor, a dependent basis, a commuting pair offered as witness, a string exponent where an integer is required. A mutation that crashes the checker counts as a checker defect and pauses scoring.

## 7. Arms and Baselines

Arms A–E per the protocol, each synthesizing a solver.

- **A:** real engine turn driver (U05) with stateful, decomposed synthesis (U10).
- **B:** ordinary propose, test, repair with full history.
- **C:** arm A's controller, host checks and search, with glyph packets replaced by plain text. The ablation keeps the controller.
- **D:** best-of-N sampling filtered on public examples, same budget.
- **E:** the existing reference solver (`solver.py`). Arm E is expected to pass; it is the ceiling, not a competitor.

Arm F does not apply. Every arm sees the same JSON schema, the same public examples, the same completion cap (at least 8,192 tokens) and full history of its own turns.

## 8. Budget, Models and Provenance

$0.50 per arm, enforced before each call by `BudgetController`. This is tighter than ChatGPT's $1.00; a pass here is a pass under the original ceiling. At the blended rates in the review ($0.17–$0.35 per million tokens), $0.50 buys roughly 1.4 to 2.9 million tokens, enough for several hundred decomposed attempts. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`, Qwen3 32B. Admission is by the pinned registry (U06), never by name matching. No `load_dotenv`. No human edits to the solver after the run starts.

## 9. Pass Gates and Statistics

- **Capability gate:** for a seed, 40/40 (32 base + 8 controls) and every certificate accepted by both checkers.
- **Primary metric (pre-registered):** number of seeds whose frozen solver meets the capability gate, arm A vs arm B, paired by seed index, exact McNemar. Six paired seeds are the minimum for a differentiation claim at α = 0.05: with five, the smallest attainable two-sided p is 0.0625.
- **Secondary:** per-case correctness on base cases within matched seeds (McNemar), poisoned-case accuracy, and cost per verified success.
- At least 3 seeds per arm are required to report anything; 6 are required to claim differentiation. Controls are reported separately.

## 10. Interpretation

- A passes on most seeds and B does not: evidence that the engine path adds capability for this synthesis task.
- A, C and D all pass: decomposition, host checks and sampling suffice; the glyph representation adds nothing measurable here.
- Only E passes: the task is still beyond the harness and models tested; this does not refute the game.
- Refusal-only successes (`OUT_OF_SCOPE`, `UNKNOWN`) are reported separately and never count toward a capability claim, because finding one anticommuting pair is the easiest part of the task.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. The run should still exercise:

- **Danger gate** (`TwoSignalDangerGate`): signal 1 is a candidate whose public outputs are schema-valid; signal 2 is a global sign inversion (antimorphism AM-5), detected when every σᵢ or every energy is mirrored. Both signals are needed before quarantine.
- **Kinetic proofreading** (`HopfieldNinioProofreader`): a candidate solver is admitted only after passing the public examples, the relabel pairs and a sandboxed self-check in sequence.
- **Thymus** (`ThymusGate`): repair operands that reject the reference solver's correct outputs are discarded.

Layer 1 and Layer 2 controls do not apply (no arm F). Host scratch space (U12) should hold the single-qubit phase table (XY = iZ, YZ = iX, ZX = iY) and the running σᵢ ledger, so repair turns see them without regenerating them.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle to `_intelligence/symbol_game/runs/<run_id>/` (U01). Expected DDC pattern per seed: `C` (expose spec, schema, examples), `I` (integrate a module skeleton), then repeated `R D` (score public residual, descend) with `M` on failed candidates, `E` when all public examples pass, and `T` at freeze. Logged measures per step: failing public examples, checker rejections by class (energy, degeneracy, σ, witness, parse), and sandbox faults.

Operands expected: (1) phase-tracked product of two Pauli words with an explicit i-power counter; (2) F2 elimination that carries signs through row operations; (3) degeneracy as |argmin| · 2^{n−k}; (4) lexicographic anticommuting-pair search that stops at the first witness.

## 13. Estate Reuse and Prerequisites

- Q40 demo: `omega_engine_projects/mssn_sn_symgam/demos/demo_q40_quantum_solver/` (`TASK.md`, `solver.py` as arm E).
- Python reference: `omega_engine_symbol_game/domain/quantum/` (`pauli.py`, `stabilizer_solver.py`, `certificate_checker.py`), to be ported to Rust.
- Rust: `omega_engine/crates_rs/omega_quantum_physics/src/pauli.rs` and `binary_field.rs` give commutation and the symplectic product, but no phase-tracked string products. The checker must be written in Rust under U14.
- Upgrades: base [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md); plus [U10](../../upgrades/u10_synthesis_loop_v2.md) and [U14](../../upgrades/u14_rust_quantum_stabilizer_port.md). Recommended: [U18](../../upgrades/u18_demo_registry_unification.md) so `symbol-game demo run` can reach Q40.

## 14. Claim Hygiene

- **Supports:** whether a model of at most 70B parameters, driven by each arm under a pre-call budget, can synthesize an exact stabilizer solver that passes an unseen judge packet.
- **Does not support:** any claim about quantum hardware, about non-commuting Hamiltonians, or that the game is novel. A pass shows capability on a textbook formalism.
- **Narrowest defensible claim:** "On C021 (mode 1: ChatGPT's judge packet, or mode 2: independent follow-on benchmark), arm X produced frozen solvers passing 40/40 hidden cases on s of S seeds at cost c per verified success." A mode-2 result is never described as passing ChatGPT's challenge.
- **Next test:** C022 (code distance) and C023 (tableau synthesis), where the model is less likely to have seen reference code.
