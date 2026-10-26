# C024: Local-Clifford Equivalence of Graph States

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that decides whether two hidden graph states are local-Clifford equivalent, with a
> local-complementation sequence when they are and a checkable separating certificate when they
> are not, for under $1.

## 2. Why This Task

Two graph states |G⟩ and |G′⟩ on the same labelled vertices are equivalent under local Clifford operations exactly when G′ can be reached from G by a sequence of local complementations (Van den Nest, Dehaene, De Moor 2004). Bouchet gave a polynomial-time algorithm for deciding local equivalence of graphs (Bouchet 1991). Both directions have cheap certificates: a vertex sequence to replay, or an invariant that differs.

The task is a decision problem with two certificate types, so a solver that only ever says "equivalent" or only ever says "not equivalent" fails half the set. It stresses OEWAS (Omega Engine Workflows, Agents, Skills) search over orbits and OEEIS (Omega Engine Epistemic Immune System) screening of answers that confuse labelled equivalence with graph isomorphism.

## 3. Formal Problem and Bounds

Input: two simple undirected graphs G and G′ on the vertex set {0, …, n − 1}, 2 ≤ n ≤ 16, as adjacency lists. Local complementation at v, written G *v, complements the induced subgraph on the neighbourhood N(v) and leaves every other edge unchanged. It is an involution: (G* v) * v = G.

Decide whether G′ = G *v₁* v₂ *⋯* v_m for some sequence. Vertex labels are fixed; no relabelling is allowed.

Separating invariant: for A ⊆ V, the cut-rank ρ_G(A) is the F2 rank of the adjacency submatrix Γ[A, V \ A]. It is invariant under local complementation, so ρ_G(A) ≠ ρ_{G′}(A) for any A proves non-equivalence. Equal cut-rank functions do not by themselves prove equivalence. For such pairs, the fallback certificate is Bouchet's F2 linear system: its solution space, given by a basis, together with an exhaustive check that no element of that space satisfies the non-degeneracy constraints. The second checker searches for pairs within the bounds whose cut-rank functions agree but which are not equivalent. If it finds any, they go into the hidden set; if it finds none, the judge packet records that.

Edge cases: G = G′ (empty sequence); G′ an isomorphic but differently labelled copy of G that is not LC-equivalent; disconnected graphs where components must be handled separately; n = 16 at the bound; pairs one edge apart.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input:

```json
{"case_id": "lc_09", "num_vertices": 4,
 "g": [[0, 1], [1, 2], [2, 3]], "g_prime": [[0, 1], [0, 2], [1, 2], [2, 3]]}
```

Outputs:

```json
{"id": "lc_09", "status": "SOLVED", "equivalent": true, "sequence": [1]}
{"id": "lc_10", "status": "SOLVED", "equivalent": false,
 "witness": {"kind": "cut_rank", "subset": [0, 3], "rank_g": 2, "rank_g_prime": 1}}
{"id": "lc_11", "status": "OUT_OF_SCOPE", "witness": {"kind": "self_loop", "edge": [2, 2]}}
{"id": "lc_12", "status": "UNKNOWN", "refusal_code": "NUM_VERTICES_OUT_OF_BOUNDS"}
```

A certificate is complete when the checker replays the sequence and obtains exactly G′, or recomputes both cut-ranks and finds them different, or verifies the linear-system basis and enumerates its solutions. `OUT_OF_SCOPE` covers inputs that are not simple graphs on the same vertex set (self-loops, repeated edges, mismatched vertex sets).

## 5. Participant Packet

- `TASK.md` with §3 and §4, the definition of local complementation with a worked 4-vertex example, and the cut-rank definition.
- `examples/`: 10 pairs with exact outputs: equal graphs, the path P4 and its complementation at an inner vertex, the star and complete graph on 5 vertices (equivalent; they give the GHZ state), a relabelled non-equivalent pair, two cut-rank separations, and two malformed pairs.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 30 pairs with n from 4 to 16: 15 equivalent (G′ built by a random sequence of length up to 3n, and the sequence discarded), 15 non-equivalent, of which at least 5 differ by a single edge.
- **Relabel and gauge controls:** 10 controls: the same vertex permutation applied to both graphs; G replaced by G * u for a random u (the answer is unchanged); and the pair swapped (a valid sequence reverses).
- **Poisoned-but-schema-valid cases:** 6 pairs where G′ is isomorphic to G, or to an LC-equivalent of G, under a non-identity permutation but not equivalent under the fixed labelling.
- **Exact checker (Rust):** replays local complementations on F2 adjacency matrices and computes cut-ranks by exact F2 rank.
- **Independent second checker:** a separate implementation of Bouchet's algorithm through the Van den Nest, Dehaene and De Moor linear system over F2, plus exhaustive orbit enumeration for n ≤ 8.
- **Mutation suite:** a sequence off by one vertex, a sequence in reverse order where order matters, a cut-rank witness with swapped ranks, a subset where the ranks are actually equal, "equivalent" asserted with an empty sequence on unequal graphs.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: a direct implementation of Bouchet's algorithm that also emits certificates. If A only matches E, the result is automation without a model advantage. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, Gemma 3 27B. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 30/30 base and 10/10 controls, both checkers accepting every certificate.
- **Primary metric (pre-registered):** per-case certified-correct rate on base cases, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** accuracy on the isomorphism-trap cases, and the fraction of non-equivalent answers needing the linear-system certificate.

## 10. Interpretation

- Failing mainly the isomorphism traps means the solver decides the wrong problem; the representation is not the cause.
- If every arm finds sequences and none produces separating certificates, the lower-bound half of the task is the bottleneck, as in C022.
- A matching E shows useful automation of a known polynomial algorithm.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is an "equivalent" answer; signal 2 is a replay that yields a graph isomorphic to G′ but not equal to it. This is the relabelling antimorphism.
- **Thymus:** discard repair operands that break the involution law (G *v* v = G) on the self-panel.
- **Kinetic proofreading:** a sequence is replayed twice, once in each checker, before admission.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the current adjacency matrix during search.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern for equivalent pairs: `C` (expose both graphs), then repeated `D` (each local complementation reduces the symmetric difference between the current graph and G′) with `M` on moves that increase it, and `T`. For non-equivalent pairs: `C`, `I` (integrate the cut-rank table), `R` (the residual is the first differing subset), `T`. Logged measures: size of the edge symmetric difference, and the number of subsets whose cut-ranks differ.

Operands expected: (1) local complementation is an involution, so reverse the sequence to swap the pair; (2) the cut-rank of singletons is the non-isolation indicator; (3) star and complete graph are one complementation apart; (4) test labelled equality, never isomorphism.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_linear_algebra` for F2 rank; `omega_engine/crates_rs/omega_number_theory/src/binary_field.rs`.
- `omega_engine/crates_rs/omega_quantum_physics/src/clifford.rs` (the single-qubit Clifford quotient Sp(2, F2), order 6), for the local Clifford framing.
- `omega_engine/crates_rs/omega_quantum_physics/src/ghz_state.rs` is a scaffold marked best-effort and is not used for checking.
- No graph-state or local-complementation module exists in Rust; the checker is new work.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize a solver that decides labelled LC equivalence with certificates in both directions.
- **Does not support:** claims about local-unitary equivalence beyond the Clifford group, entanglement classification in general, or hardware.
- **Narrowest defensible claim:** "Arm X decided k of 30 hidden graph-state pairs (n ≤ 16) with independently checked certificates."
- **Next test:** C023 with graph-state preparation circuits as targets.
