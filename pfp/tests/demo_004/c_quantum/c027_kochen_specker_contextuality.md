# C027: Kochen-Specker Sets and Contextuality Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that, for hidden sets of rays in 3 or 4 dimensions, either finds an explicit
> non-contextual colouring or proves that none exists, with a certificate, for under $1.

## 2. Why This Task

A Kochen–Specker (KS) set is a finite set of rays that admits no {0, 1} colouring in which every complete orthogonal basis drawn from the set has exactly one ray coloured 1 and no two orthogonal rays are both coloured 1. Known examples include Peres's 33 rays in dimension 3 (Peres 1991) and the 18 rays in dimension 4 of Cabello, Estebaranz and García-Alcaine (1996). The 18-ray set has a short parity proof: its 9 bases each contain exactly one ray coloured 1, giving an odd total, yet every ray lies in exactly two bases, giving an even total.

Both answers have cheap certificates: a colouring checked constraint by constraint, or an UNSAT proof or parity argument. Producing them needs exact orthogonality (no rounding) and correct context enumeration. The task stresses OEWAS (Omega Engine Workflows, Agents, Skills) composition of exact geometry with a SAT tool, and OEEIS (Omega Engine Epistemic Immune System) screening of rays that are orthogonal only to within a tolerance.

## 3. Formal Problem and Bounds

Input: dimension d ∈ {3, 4} and up to 60 nonzero vectors with coordinates in Z[√2], each coordinate given as a pair (a, b) meaning a + b√2. Parallel vectors (including v and −v) denote the same ray and must be merged. Orthogonality is exact: u · v = 0 in Q(√2).

The checker derives the constraints itself:

- **Orthogonality constraint:** for every orthogonal pair (u, v), not both coloured 1.
- **Context constraint:** for every set of d mutually orthogonal rays in the input, exactly one is coloured 1.

Decide whether a colouring exists. If not, the set contains a KS set; the solver may return a subset that is still uncolourable. Optionally it may claim the subset is critical (every one-ray deletion is colourable) and attach the colourings that prove it.

Edge cases: a set with no complete context (trivially colourable); the 18-ray set in a rotated frame; the 33-ray set with one ray removed (the second checker decides whether it is colourable, and that value is used); duplicate rays in different scalings; a pair orthogonal only up to a small nonzero element of Z[√2]; a zero vector (malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. The sandbox exposes `tools.sat_solve(cnf)` wrapping a pinned CaDiCaL binary. Input and outputs:

```json
{"case_id": "ks_07", "dimension": 4, "vectors": [[[1,0],[0,0],[0,0],[0,0]], "…"]}
{"id": "ks_07", "status": "SOLVED", "colourable": false, "subset": [0, 1, 4, "…"],
 "certificate": {"kind": "parity", "contexts": [[0, 1, 4, 9], "…"]}}
{"id": "ks_08", "status": "SOLVED", "colourable": true, "colouring": [1, 0, 0, "…"]}
{"id": "ks_09", "status": "OUT_OF_SCOPE", "witness": {"kind": "zero_vector", "index": 5}}
{"id": "ks_10", "status": "UNKNOWN", "refusal_code": "TOO_MANY_VECTORS"}
```

Certificate kinds for `colourable: false`: `parity` (a list of an odd number of contexts, each a real context of the subset, in which every ray appears an even number of times) or `lrat` (an LRAT refutation of the CNF that the checker regenerates from the subset). A colouring is complete when every orthogonality and context constraint holds. `OUT_OF_SCOPE` covers zero vectors and dimension mismatches.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the Z[√2] encoding, the rule for merging parallel vectors, and the CNF convention.
- `examples/`: 8 cases with exact outputs: the 18-ray set (parity certificate), a colourable 9-ray subset of it, the standard basis alone, a two-basis set sharing one ray, a set with no complete context, a duplicate-ray case, a zero vector and an oversized case.
- `runner.py`, `tools.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 24 sets: the 33-ray set and the 18-ray set in random frames, supersets with extra rays, random subsets (mostly colourable), unions of the two families padded to 60 rays, and sets built from random integer bases.
- **Relabel and gauge controls:** 8 controls: ray permutation; a signed coordinate permutation applied to every vector; a rational orthogonal matrix applied to every vector, with denominators then cleared; rescaling each vector by a nonzero integer. Colourability is invariant under all four.
- **Poisoned-but-schema-valid cases:** 6 cases: a near-KS set where one "orthogonal" pair has a tiny nonzero dot product in Z[√2], such as (√2 − 1)⁸ ≈ 0.0009 (so a context disappears and the set may become colourable; the second checker decides); a duplicate ray entered as 2v; a parity-looking list of contexts in which one context is not orthogonal.
- **Exact checker (Rust):** builds the orthogonality graph over Q(√2), enumerates contexts, checks colourings, parity certificates, and LRAT proofs with a pinned checker.
- **Independent second checker:** a separately written backtracking colourer with unit propagation, and, for parity certificates, the Z₂ cochain obstruction in `omega_quantum_physics::contextuality_obstruction` (contextuality over H¹ with Z₂ coefficients).
- **Mutation suite:** a colouring with two orthogonal ones, a context with no one, a parity list with a non-context, an LRAT proof for a different subset, a merged-ray error, a claimed critical set with a missing deletion colouring.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: exact orthogonality, context enumeration and a direct CaDiCaL call. E should pass; the challenge measures whether an arm assembles exact geometry correctly, and secondarily whether it finds short parity proofs where E emits long LRAT ones. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, Gemma 3 27B. CaDiCaL and the LRAT checker are pinned by SHA-256.

## 9. Pass Gates and Statistics

- **Capability gate:** 24/24 base and 8/8 controls, both checkers accepting.
- **Primary metric (pre-registered):** per-case certified-correct rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** fraction of uncolourable answers with a parity certificate, subset size, validity of critical-set claims.

## 10. Interpretation

- Failing the near-orthogonal poison means the solver used floating point; the result says nothing about contextuality reasoning.
- If only E passes, exact context enumeration is the bottleneck for the models tested.
- Finding a KS set certifies uncolourability of a finite ray set. It does not, by itself, establish anything about experiments or hidden-variable models beyond the stated combinatorial statement.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is an "uncolourable" claim; signal 2 is a certificate that relies on a context the exact checker does not find. This catches rounding-based contexts.
- **Kinetic proofreading:** merge rays, then derive contexts, then check the certificate.
- **Thymus:** reject operands that treat v and −v as different rays.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the orthogonality graph and the context list.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose rays), `I` (integrate the orthogonality graph and contexts), `R` (residual: unsatisfied constraints of the current colouring), `D` while local repair reduces them, `Λ` when the solver lifts from local repair to a global SAT or parity argument, then `T`. Logged measures: unsatisfied constraints, the size of the current uncolourable subset, and proof length.

Operands expected: (1) merge parallel rays before anything else; (2) parity proof: odd context count with every ray in an even number of contexts; (3) derive contexts exactly, never from tolerances; (4) certify criticality with one colouring per deletion.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers/src/solver_cadical_unsat_core.rs` (CaDiCaL; LRAT emission may need adding).
- `omega_engine/crates_rs/omega_quantum_physics/src/contextuality_obstruction.rs` (the Cabello 18-ray scenario in 9 contexts and its Z₂ cohomology class; reused by the second checker).
- `omega_engine/crates_rs/omega_number_theory/src/cyclotomic.rs` (`Cyc8`, which contains √2) for exact orthogonality; `gleason.rs` and `contextuality_thresholds.rs` for context.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize an exact colourability decider for finite ray sets with independently checked certificates.
- **Does not support:** claims about physical contextuality experiments, or any interpretation of quantum mechanics.
- **Narrowest defensible claim:** "Arm X decided KS colourability for k of 24 hidden ray sets in d ≤ 4, with checked colourings or refutations."
- **Next test:** a T4 variant asking for the smallest uncolourable subset with a criticality certificate.
