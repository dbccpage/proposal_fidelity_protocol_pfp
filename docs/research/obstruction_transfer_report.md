# Obstruction-class transfer test

AuthorityEffect: None. This report measures. It licenses no transfer, lift or admission.

- Code: [`code/rust/core_obstruction_transfer`](../../code/rust/core_obstruction_transfer) (library, `obstruction_transfer_table` binary, `tests/transfer.rs`).
- Base revision: PFP `main` at `6da88f4d`.
- Receipts: [`receipts/max_n_5`](../../code/rust/core_obstruction_transfer/receipts/max_n_5) (the result) and [`receipts/max_n_4`](../../code/rust/core_obstruction_transfer/receipts/max_n_4) (the fast replay).

## Question

When a solved case's recorded repair steps are replayed on another case, does "same obstruction class" predict exact success? How far down a ladder of sameness (L1 to L5) does that hold?

## Answer

Only for optimal potentials, and only at L1 and L2.

- **Gauge transport** of a certified optimum gives S = 1 on every SCORED pair and D_τ = D₀ on every NO_HEADROOM pair, at L1 (6,274 pairs) and L2 (356,736 pairs). Lemma 2 says it must, and the measurement agrees with no exception.
- **Structural traces** (canonical tree, E, R, CUT, E, T) do **not** transfer, even at L1. Out of 6,274 L1 pairs, 614 reach S = 1, 152 have S < 0, and 3,657 are refused. Out of 356,736 L2 pairs, 41,580 reach S = 1, 2,978 have S < 0, and 263,064 are refused. Most refusals are `CHORD_NO_IMAGE`: after a relabelling, the image of a recorded chord is a tree edge of the target's own canonical tree, so the recorded indices no longer point at anything. A trace keyed to a labelling-dependent tree is not a class invariant.
- At **L3 to L5** neither method reaches rate 1, and negative scores are common. L3 gauge transport has 22,492 pairs with S < 0 out of 29,180 scored.
- The hypothesis "same class ⇒ same steps" is therefore licensed nowhere for structural steps. "Same class ⇒ same optimal potential, up to the map and the gauge" is licensed at L1 and L2 only.

Compute: the whole n ≤ 5 family (4,760 instances, 2,351,084 pairs) took 767 s on one CPU core in release mode. That is **over the ~10 minute budget** by about 2.8 minutes. The n ≤ 4 family (460 instances, 32,908 pairs) takes 12 to 20 s. Both receipts are committed, and both results are reported. The n ≤ 5 run was not cut short.

## Definitions as implemented

- **Instance.** A connected simple graph on `0..n`, edges stored as `(u, v)` with `u < v`, weights `w_e ∈ {1, 2}`, integer claims `c_e`, and `(δφ)_uv = φ_v − φ_u`.
- **Defect and Φ1.** `D(c, φ) = Σ_e w_e |c_e − (δφ)_e|`. Φ1 is never computed by this crate. `core_solvers::solver_lp_phi1_quotient::solve_exact_phi1` (exact two-phase simplex) proposes a primal potential and a dual circulation. `core_functional::phi1::Phi1Functional::verify_exact_certificate` then checks the certificate: it compares the reported value with the weighted norm of the submitted residual and with the dual pairing, and checks `|z_e| ≤ w_e` and `z ⟂ im δ`. Every Φ1 used in a score passed that check. No second Φ1 was written.
- **Canonical spanning tree.** Breadth-first search from vertex 0, neighbours in increasing order; the discovering edge of each vertex is a tree edge. Chords are the other edges, indexed in edge order.
- **Structural trace.** `C E R D(k, j)… E T`, with these steps:
  - `C`: declare the canonical tree.
  - `E`: exact repair on the tree edges, reading claims from the current instance.
  - `R`: project the residual onto the chord coordinates of `[c]`. This is a no-op on φ.
  - `D(k, j)` (CUT): cut the edge at position `j` of the fundamental cycle of chord `k`. Position 0 is the chord itself; the rest follow the tree path from the chord's head back to its tail.
  - `E` (re-tree): exact repair on every edge that was not cut.
  - `T`: terminal.

  Arguments are chord indices and cycle positions only, and no step calls a solver.
- **Recording on A.** The certified optimum of A is read once. Its zero-residual edges are scanned with canonical-tree edges first, then by edge index (the tie-break rule), and a spanning tree is grown in that order. The cut set is the complement of that tree. Each chord `k` is matched to a cut edge on its own fundamental cycle, taking the first matching in lexicographic order, and `j` is that edge's position. Two refusals are possible: `RECORD_NOT_VERTEX` and `RECORD_NO_CHORD_MATCHING`. Every recorded trace is replayed on its own instance as a self-check, and it reaches Φ1 exactly.
- **Gauge transport.** `φ_B = π(φ*_A) + ψ`, where ψ is the potential that is exact on B's canonical tree for `c_B − π(c_A)`. ψ is integrated structurally, with no solver. It needs a vertex map, so L4 and L5 refuse with `NO_VERTEX_MAP`.
- **Score.** `D₀ = D(c_B, 0)` and `D_τ = D(c_B, φ_τ)`. The outcome is SCORED when `D₀ > Φ1`, with `S = (D₀ − D_τ)/(D₀ − Φ1)`; NO_HEADROOM when `D₀ = Φ1`, reporting `D_τ − D₀`; and REFUSED when the replay does not type-check. `D_τ < Φ1` would contradict a certificate and is collected as a defect. There were none.
- **Level ℓ(A, B)** is computed for every pair from scratch, by brute force over all `n!` vertex bijections. It is the highest level whose map exists:
  - L1: a bijection carries `(G, w, c)` onto B exactly;
  - L2: a bijection carries `(G, w)` onto B, and `c_B − π(c_A)` has zero class coordinates;
  - L3: a bijection carries `(G, w)`, and the class coordinates of `π(c_A)` and `c_B` have the same support on B's canonical tree;
  - L4: no such bijection, equal β₁, and equal class coordinates under the index match `k ↦ k` of the two contracted canonical trees;
  - L5: equal β₁ only.

  The first bijection in lexicographic order that attains the level is the comparison map. At L5 every chord bijection is replayed, and the worst (`structural_trace_min`) and best (`structural_trace_max`) are reported. In both, a refusal ranks below every typed score.

## Family (exhaustive, deterministic)

- Graphs: every connected simple graph with `n ≤ 5` and `β₁ ∈ {1, 2}`, one per isomorphism class. The algorithm keeps an edge set when it equals the lexicographically least relabelling of itself. Counts per `(n, β₁)` are 1, 2, 5 for β₁ = 1 and 0, 1, 5 for β₁ = 2 (14 graphs), as in the census below. A test checks these against the known counts.
- Weights in `{1, 2}`, one per `Aut(G)`-orbit (the orbit minimum).
- Claims: chord coordinates in `{−2..2}^β₁`, with tree edges set to 0.
- Pairs (every target is then classified honestly, so a block's intended level is not its reported level):
  - **iso**: B is A with labels reversed (`x ↦ n−1−x`);
  - **gauge**: the reversed copy plus `δψ` for every `ψ ∈ {−1, 0, 1}^V` with `ψ₀ = 0` and `ψ ≠ 0`;
  - **support**: the same `(G, w)`, every ordered pair of distinct coordinate vectors with equal support;
  - **contract**: every ordered pair of distinct `(G, w)` classes with equal β₁, with coordinates equal, negated or reversed (the last two only when they differ). This bounds L5 to about three targets per source class and coordinate vector rather than all of `{−2..2}^β₁`, and is the one place where the family is not the full product;
  - **control, shuffled claims**: the same `(G, w)` with the claim vector rotated by one edge position;
  - **control, cross-β₁**: each instance against the first instance with the same `n` and the other β₁.

| n | beta1 | graphs |
|---|---|---|
| 3 | 1 | 1 |
| 4 | 1 | 2 |
| 4 | 2 | 1 |
| 5 | 1 | 5 |
| 5 | 2 | 5 |

| n | beta1 | edges with w=2 | (G,w) classes | instances |
|---|---|---|---|---|
| 3 | 1 | 0 | 1 | 5 |
| 3 | 1 | 1 | 1 | 5 |
| 3 | 1 | 2 | 1 | 5 |
| 3 | 1 | 3 | 1 | 5 |
| 4 | 1 | 0 | 2 | 10 |
| 4 | 1 | 1 | 4 | 20 |
| 4 | 1 | 2 | 6 | 30 |
| 4 | 1 | 3 | 4 | 20 |
| 4 | 1 | 4 | 2 | 10 |
| 4 | 2 | 0 | 1 | 25 |
| 4 | 2 | 1 | 2 | 50 |
| 4 | 2 | 2 | 4 | 100 |
| 4 | 2 | 3 | 4 | 100 |
| 4 | 2 | 4 | 2 | 50 |
| 4 | 2 | 5 | 1 | 25 |
| 5 | 1 | 0 | 5 | 25 |
| 5 | 1 | 1 | 14 | 70 |
| 5 | 1 | 2 | 26 | 130 |
| 5 | 1 | 3 | 26 | 130 |
| 5 | 1 | 4 | 14 | 70 |
| 5 | 1 | 5 | 5 | 25 |
| 5 | 2 | 0 | 5 | 125 |
| 5 | 2 | 1 | 15 | 375 |
| 5 | 2 | 2 | 35 | 875 |
| 5 | 2 | 3 | 44 | 1100 |
| 5 | 2 | 4 | 35 | 875 |
| 5 | 2 | 5 | 15 | 375 |
| 5 | 2 | 6 | 5 | 125 |

## Results

Exact counts. `sum S` is an exact rational. "NH worse" counts NO_HEADROOM pairs with `D_τ > D₀`.

| cohort | level | method | pairs | SCORED | NO_HEADROOM | REFUSED | S=1 | S<0 | sum S | NH worse | NH sum(D_tau-D0) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| main | L1 | gauge_transport | 6274 | 3102 | 3172 | 0 | 3102 | 0 | 3102 | 0 | 0 |
| main | L1 | structural_trace | 6274 | 1028 | 1589 | 3657 | 614 | 152 | 1420/3 | 240 | 526 |
| main | L2 | gauge_transport | 356736 | 349596 | 7140 | 0 | 349596 | 0 | 349596 | 0 | 0 |
| main | L2 | structural_trace | 356736 | 92234 | 1438 | 263064 | 41580 | 2978 | 30497159087693/446185740 | 802 | 1652 |
| main | L3 | gauge_transport | 43046 | 29180 | 13866 | 0 | 1310 | 22492 | -369049/6 | 9664 | 38056 |
| main | L3 | structural_trace | 43046 | 29180 | 13866 | 0 | 16939 | 2717 | 15542 | 3693 | 9122 |
| main | L4 | gauge_transport | 763560 | 0 | 0 | 763560 | 0 | 0 | 0 | 0 | 0 |
| main | L4 | structural_trace | 763560 | 346837 | 312923 | 103800 | 161400 | 50411 | 1390667/12 | 93541 | 195617 |
| main | L5 | gauge_transport | 1171968 | 0 | 0 | 1171968 | 0 | 0 | 0 | 0 | 0 |
| main | L5 | structural_trace_max | 1171968 | 542070 | 465182 | 164716 | 270603 | 46362 | 1559513/6 | 78103 | 142376 |
| main | L5 | structural_trace_min | 1171968 | 522372 | 450320 | 199276 | 93386 | 116725 | -698143/12 | 171712 | 410387 |
| control_shuffled_claims | L1 | gauge_transport | 588 | 116 | 472 | 0 | 116 | 0 | 116 | 0 | 0 |
| control_shuffled_claims | L1 | structural_trace | 588 | 40 | 376 | 172 | 40 | 0 | 40 | 0 | 0 |
| control_shuffled_claims | L2 | gauge_transport | 264 | 126 | 138 | 0 | 126 | 0 | 126 | 0 | 0 |
| control_shuffled_claims | L2 | structural_trace | 264 | 104 | 84 | 76 | 104 | 0 | 104 | 0 | 0 |
| control_shuffled_claims | L3 | gauge_transport | 1344 | 898 | 446 | 0 | 18 | 752 | -3799/2 | 411 | 1810 |
| control_shuffled_claims | L3 | structural_trace | 1344 | 882 | 446 | 16 | 389 | 113 | 609/2 | 223 | 710 |
| control_shuffled_claims | L5 | gauge_transport | 2564 | 0 | 0 | 2564 | 0 | 0 | 0 | 0 | 0 |
| control_shuffled_claims | L5 | structural_trace_max | 2564 | 1864 | 700 | 0 | 1677 | 49 | 9845/6 | 83 | 183 |
| control_shuffled_claims | L5 | structural_trace_min | 2564 | 1658 | 660 | 246 | 892 | 250 | 2368/5 | 272 | 873 |
| control_cross_betti | none | gauge_transport | 4740 | 0 | 0 | 4740 | 0 | 0 | 0 | 0 | 0 |
| control_cross_betti | none | structural_trace | 4740 | 0 | 0 | 4740 | 0 | 0 | 0 | 0 | 0 |

| cohort | level | method | refusal code | count |
|---|---|---|---|---|
| main | L1 | structural_trace | CHORD_NO_IMAGE | 3569 |
| main | L1 | structural_trace | CUT_REPEATED | 88 |
| main | L2 | structural_trace | CHORD_NO_IMAGE | 256024 |
| main | L2 | structural_trace | CUT_REPEATED | 7040 |
| main | L4 | gauge_transport | NO_VERTEX_MAP | 763560 |
| main | L4 | structural_trace | CUT_POSITION_OUT_OF_RANGE | 75331 |
| main | L4 | structural_trace | CUT_REPEATED | 22476 |
| main | L4 | structural_trace | CUT_SET_NOT_COTREE | 5993 |
| main | L5 | gauge_transport | NO_VERTEX_MAP | 1171968 |
| main | L5 | structural_trace_max | CUT_POSITION_OUT_OF_RANGE | 120056 |
| main | L5 | structural_trace_max | CUT_REPEATED | 33714 |
| main | L5 | structural_trace_max | CUT_SET_NOT_COTREE | 10946 |
| main | L5 | structural_trace_min | CUT_POSITION_OUT_OF_RANGE | 154616 |
| main | L5 | structural_trace_min | CUT_REPEATED | 33714 |
| main | L5 | structural_trace_min | CUT_SET_NOT_COTREE | 10946 |
| control_shuffled_claims | L1 | structural_trace | CHORD_NO_IMAGE | 172 |
| control_shuffled_claims | L2 | structural_trace | CHORD_NO_IMAGE | 76 |
| control_shuffled_claims | L3 | structural_trace | CHORD_NO_IMAGE | 16 |
| control_shuffled_claims | L5 | gauge_transport | NO_VERTEX_MAP | 2564 |
| control_shuffled_claims | L5 | structural_trace_min | CUT_POSITION_OUT_OF_RANGE | 246 |
| control_cross_betti | none | gauge_transport | BETTI_MISMATCH | 4740 |
| control_cross_betti | none | structural_trace | BETTI_MISMATCH | 4740 |

### Acceptance

- Gauge transport, L1 and L2: S = 1 on 3,102 + 349,596 SCORED pairs, and D_τ = D₀ on 3,172 + 7,140 NO_HEADROOM pairs. No defects. **Met.**
- Structural traces, L1 and L2: reported exactly above. This is a finding, not an acceptance condition.
- Shuffled-claim controls are reported in their own cohort. Cross-β₁ pairs (4,740) are all REFUSED with `BETTI_MISMATCH`, and none is scored. **Met.**
- Every Φ1 in a score comes from a certificate that `Phi1Functional::verify_exact_certificate` accepted. No pair had `D_τ < Φ1`, and every recorded trace replays to Φ1 on its own instance. **Met.**
- Receipts: `obstruction_transfer_table --check receipts/max_n_4` and `--check receipts/max_n_5` rerun the family and compare the receipt and the table byte for byte. Both reproduced on the committed code. The test `small_family_acceptance_and_determinism` also asserts determinism at n ≤ 4.
- Floats: none. Integers and `BigRational` only, including the score and every sum.

## Lemmas

All three are written proofs, marked as such. They are not mechanised in Lean; that did not fit this session's budget. The executable checks named with each one are tests, not proofs.

**Lemma 1 (class invariance).** For every `ψ ∈ C⁰`, `Φ1(c + δψ) = Φ1(c)`, and the map `φ ↦ φ + ψ` carries minimisers to minimisers with the residual unchanged.

*Written proof.* `c + δψ − δ(φ + ψ) = c − δφ`, so `D(c + δψ, φ + ψ) = D(c, φ)` for every φ. The map `φ ↦ φ + ψ` is a bijection of `C⁰`, so the two minima agree and minimisers correspond. ∎
*Check:* `class_invariance_on_every_small_instance` (every n ≤ 4 instance, three ψ, certified values equal).

**Lemma 2 (gauge transport).** Let `π` be an isomorphism of `(G_A, w_A)` onto `(G_B, w_B)` with `c_B = π(c_A) + δψ`. Let `φ*_A` be optimal for `c_A`. Then `φ_B = π(φ*_A) + ψ` is optimal for `c_B`, and `c_B − δφ_B = π(c_A − δφ*_A)`. So the outcome is `S = 1` when `D₀ > Φ1(c_B)` and `D_τ = D₀` otherwise.

*Written proof.* An isomorphism that preserves weights preserves D: `D(π c, π φ) = D(c, φ)`, with orientation signs absorbed because a reversed edge negates both the claim and `δφ`. Hence `Φ1(π c_A) = Φ1(c_A)`, and `π φ*_A` is optimal for `π c_A`. Lemma 1 with ψ finishes it: `c_B − δ(πφ*_A + ψ) = π c_A − δπφ*_A`. When `D₀ > Φ1`, `D_τ = Φ1` gives `S = 1`. When `D₀ = Φ1`, `D_τ = Φ1 = D₀`. ∎
*Implementation note:* ψ is recovered by integrating `c_B − π(c_A)` on B's canonical tree. When that difference is a coboundary, the integral is ψ up to a constant, which does not change δψ.
*Check:* the acceptance rows below (every L1 and L2 pair), and the mutation check.

**Lemma 3 (a structural trace is not guaranteed to replay optimally, even at L2).** Take the unit triangle with edges `(0,1), (1,2), (0,2)`, `c_A = (1, −1, 1)` and `c_B = (2, −1, 2) = c_A + δψ` with `ψ = (0, 1, 1)`. The partial trace "set φ₁ = φ₀ + c₀₁" is optimal on A (D goes from 3 to 1, S = 1). On B it gives φ = (0, 2, 0), D goes from 5 to 3, and S = 1/2.

*Written proof:* direct computation; `Φ1 = 1` on both. ∎
*Check:* `score_counterexamples_from_the_definitions` certifies Φ1 = 1 and asserts S = 1 on A and S = 1/2 on B. It also asserts the two counterexamples from the definitions: S = −1 for φ = (0, −2, 0) on B, and NO_HEADROOM with excess 2 for `c = (0, 0, 1)` and φ = (0, 1, 0).

The measured table shows that Lemma 3 is not an edge case for this trace family. See the answer above.

## Mutation check (recorded injections)

Two injections, run with `obstruction_transfer_table --max-n 4` and then reverted. They exist as `Injection` variants that default to `None`, and the committed receipts were produced with no injection.

| Injection | Gauge transport L1, S = 1 / SCORED | Gauge transport L2, S = 1 / SCORED | Failures named |
|---|---|---|---|
| none | 300 / 300 | 11,182 / 11,182 | 0 |
| `--inject-flip-chord-sign` (negate the transported claim on the target's first chord) | 300 / 300 | 11,182 / 11,182 | 0 |
| `--inject-flip-tree-edge-sign` (negate it on the target's first tree edge) | 96 / 300 | 4,464 / 11,182 (5,720 with S < 0) | 7,352, for example `L2 gauge:g0.w4.c-2~rev+d[0,-1,-1] Scored(-11)` |

The chord flip suggested in the prompt is **inert** for gauge transport: ψ is integrated on tree edges only, so a chord claim never enters it. A test records that (`mutation_flip_chord_sign_is_inert_for_gauge_transport`). The tree-edge flip is the injection that bites, and `mutation_flip_tree_edge_sign_breaks_gauge_transport_and_names_the_case` checks that it does.

A separate lexical mutation campaign on `src/lib.rs` used 24 one-line mutants, with the crate tests as the oracle. It killed 23 and 1 survived (`governance/evidence/m-obstruction-transfer.mutation.json`). The survivor drops the tree-first tie-break in recording, and on n ≤ 4 that makes no observable difference. A first campaign killed only 18; the other five survivors changed the structural-trace table without failing any test, so I added `committed_n4_receipt_reproduces_byte_for_byte`, which pins the n ≤ 4 table.

## What failed, and where I stopped or guessed

- **Budget.** The n ≤ 5 run took 767 s against a ~10 minute budget, and the module is about 1,300 lines of Rust against an estimate of ~400, most of it the enumerator, the level classifier and the table. I did not cap n at 4, because the full run finished; the n ≤ 4 receipt is the fast replay.
- **New crate.** The module is the crate `core_obstruction_transfer`, beside `core_wdp`, not a module inside `core_wdp::ddc`. Adding a module to `core_wdp` means editing `core_wdp/src/lib.rs`, whose bytes are pinned in `governance/baseline.json`; the edit would make that 400-line file fail the governance floor. The crate depends only on `core_functional`, `core_solvers` and `core_operad_canon`. It uses the canonical `DdcOp`, the same type that `core_wdp::ddc` re-exports.
- **Φ1 solver.** `core_functional` and `core_certifiers` only *verify*. The optimum comes from `core_solvers::solve_exact_phi1`, and the shared verifier then re-checks it. `core_certifiers::phi1_certifier` was read but is not called: its LP max-form verifier is not the Φ1 form. No second Φ1 was written. `canonical_tree` is a small new BFS; `core_holonomy::gauge_fixing` has a spanning-forest routine for matrix connections, which I did not reuse because its domain and tree rule differ.
- **Guess: CUT.** The DDC alphabet has no CUT letter. I wrote CUT as `D` (descent / re-index). Its meaning here is "this edge of chord k's fundamental cycle will carry the residual", followed by exact repair on the uncut edges. The prompt names the steps but not their semantics, so this is my reading.
- **Guess: recording.** The trace is recorded from A's certified optimum (zero-residual edges, canonical-tree edges first, then by edge index). This reads the solver's answer for A once, at recording time. Replay on B calls no solver.
- **Guess: L3 and L4.** For L3, I took "same chord-support pattern up to Aut" to mean an isomorphism of (G, w) under which the class coordinates of the pushed claim and of c_B have equal support on B's canonical tree. For L4, I took "chords matched through canonical tree contraction" to require **equal class coordinates** under the index match `k ↦ k`. Without that condition every same-β₁ pair would be L4, and L5 would be empty.
- **Guess: L5 pairs.** L5 pairs use negated or reversed coordinates only, not all of `{−2..2}^β₁`, to keep the pair count finite in budget. This is the one place where the family is not exhaustive.
- **Guess: pair blocks.** L1 copies use one relabelling (label reversal), and L2 copies use that relabelling plus every ψ with ψ₀ = 0. Levels are then computed, not assumed, so some pairs land on a higher level than their block's name suggests.
- **Gauge transport at L3.** It still pushes the optimum and integrates `c_B − π(c_A)` on the tree. That is not a gauge, because the classes differ. Its L3 numbers measure what happens when the class is wrong. They are not a test of Lemma 2.
- **Lean.** Not attempted. All three lemmas are written proofs, marked as such.
- **Governance.** `src/lib.rs` is recorded at **L4D**: Gate 5 is D because `run` has cyclomatic complexity 24. `tests/transfer.rs` is recorded at L2C. The binary is under `bin/`, which `governance/policy.json` excludes. `checker check --changed-since origin/main` reports 2/2 governed sources meeting the floor. Rust mutation used a lexical campaign script, because `cargo-mutants` is not installed here. The metrics run stubbed `complexipy`, which is used only for `.py` files and is not installed here.
