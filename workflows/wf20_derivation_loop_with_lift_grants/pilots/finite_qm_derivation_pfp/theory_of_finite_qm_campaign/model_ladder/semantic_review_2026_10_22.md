# Semantic Review of Accepted MODEL Ladder Runs (`2026-10-22`)

- **AuthorityEffect:** `None` (read-only audit report; no run folder or DAG node was modified)
- **Dataset scanned:** 696 `ladder_receipt.json` files under `dag/results/<NODE>/runs/*_ladder*/`
- **Accepted runs audited:** 404 (`accepted`: 404, `accepted_partial`: 0; the remaining 292 runs are `not_accepted`: 236 and `blocked_abstained`: 56)
- **Companion per-entry & per-run JSON table:** `dag/pfp/model_ladder/semantic_review_2026_10_22.json`

---

## 1. Executive Summary & Counts by Class

Across the 404 accepted runs, the host verifier (`dag/pfp/model_ladder/verify.py`) accepted **1,144 non-numeric entries** (`generators`: 470, `relations`: 657, `compositions`: 17, `lemmas`: 0) and **460 numeric claims**. Per the audit rubric, numeric claims earn no credit toward supporting a node.

Every one of the 1,144 verified non-numeric entries was compared against:
1. the cited declaration window in the repository (`path::declaration` at its source line), and
2. the target node's statement and anchor declarations in `dag/derivation_dag.json`.

### 1.1 Entry Counts by Semantic Class

| Class | Generators | Relations | Compositions | Lemmas | Total Entries | Share of 1,144 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **`SUPPORTS`** | 367 | 511 | 13 | 0 | **891** | **77.88%** |
| **`TANGENTIAL`** | 68 | 98 | 0 | 0 | **166** | **14.51%** |
| **`IRRELEVANT`** | 27 | 38 | 4 | 0 | **69** | **6.03%** |
| **`MISLEADING`** | 8 | 10 | 0 | 0 | **18** | **1.57%** |
| **Total** | **470** | **657** | **17** | **0** | **1,144** | **100.00%** |

- **Numeric claims noted (no credit):** 460 verified numeric claims across the 404 accepted runs. Exactly **60 accepted runs** (all from Round 1, when `numeric_counts=True` was enabled in `verify_p0`) contain **zero** verified non-numeric entries and passed solely on `verified_numeric_claims`.

### 1.2 Entry Counts by Citation Provenance Bucket

| Provenance Bucket | `SUPPORTS` | `TANGENTIAL` | `IRRELEVANT` | `MISLEADING` | Total |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `1_direct_node_decl` (exact declaration in node's `lean`/`rust`/`python`) | 322 | 9 | 0 | 0 | **331** |
| `2_node_file_and_decl_in_deriv_md` (node's file + decl in derivation note) | 135 | 1 | 0 | 2 | **138** |
| `3_node_file_other_decl` (another declaration in node's anchored file) | 194 | 16 | 0 | 4 | **214** |
| `4_file_and_decl_in_deriv_md` (file & decl named in derivation note) | 26 | 3 | 2 | 2 | **33** |
| `5_file_in_deriv_md_other_decl` (file named in derivation note, other decl) | 26 | 0 | 2 | 0 | **28** |
| `6_decl_in_statement_other_file` (same decl name in a different file) | 27 | 13 | 1 | 3 | **44** |
| `7_neighbour_1hop` (declaration from a 1-hop DAG neighbour) | 16 | 13 | 0 | 2 | **31** |
| `8_known_pos_propagated_multi_hop` (`@KNOWN+` multi-hop contagion) | 4 | 36 | 7 | 3 | **50** |
| `9_fuzzy_src_match` (`@SRC` stem-overlap fallback candidate) | 128 | 75 | 53 | 2 | **258** |
| `composition` (wires two generators in the same attempt) | 13 | 0 | 4 | 0 | **17** |
| **Total** | **891** | **166** | **69** | **18** | **1,144** |

> **Key observation on provenance:** When a node already has anchored files (`buckets 1–3`, 683 entries), **95.3%** (651 / 683) of verified entries are `SUPPORTS`. When the node has no anchored code or Lean declaration (`OPEN` conjectures, continuum fences, methodological `DEFINITION` nodes, or unlinked `SOURCE_RECORD` nodes) and the model relies on `@KNOWN+` multi-hop neighbour propagation (`bucket 8`, 50 entries) or `@SRC` fuzzy file-stem matching (`bucket 9`, 258 entries), the `SUPPORTS` rate drops to **8.0%** (4 / 50) in `bucket 8` and **49.6%** (128 / 258) in `bucket 9`.

---

## 2. `HOLLOW` Rate Split by Model Tier

A run is marked **`HOLLOW`** if it has **zero `SUPPORTS` entries** (either because it has 0 non-numeric verified entries and passed on numeric claims alone, or because all of its verified non-numeric entries are `TANGENTIAL`, `IRRELEVANT`, or `MISLEADING`).

### 2.1 Run-Level `HOLLOW` Rate by Tier

| Model Tier (`attempt.model`) | Accepted Runs | `HOLLOW` (All Accepted) | `HOLLOW` Rate (All) | Numeric-Only `HOLLOW` (Round 1) | Non-Numeric Runs | Semantic `HOLLOW` (Non-Numeric) | `HOLLOW` Rate (Non-Numeric Runs) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`free` (Tier 0 total)** | **50** | **18** | **36.0%** | 5 | 45 | 13 | **28.9%** |
| — `provider_b/model-b1` | 33 | 9 | 27.3% | 4 | 29 | 5 | 17.2% |
| — `model_c/model-c1` | 10 | 5 | 50.0% | 1 | 9 | 4 | 44.4% |
| — `host_n/nemotron-3.5-lightning:free` | 7 | 4 | 57.1% | 0 | 7 | 4 | 57.1% |
| **`model-a3` (Tier 2)** | **20** | **7** | **35.0%** | 1 | 19 | 6 | **31.6%** |
| **`model-a2` (Tier 3)** | **328** | **117** | **35.7%** | 51 | 277 | 66 | **23.8%** |
| **`model-a1` (Tier 4)** | **5** | **4** | **80.0%** | 3 | 2 | 1 | **50.0%** |
| **`model-a4` (Tier 5)** | **1** | **1** | **100.0%** | 0 | 1 | 1 | **100.0%** |
| **Total Across All Tiers** | **404** | **147** | **36.4%** | **60** | **344** | **87** | **25.3%** |

### 2.2 Entry-Level Class Distribution by Tier

| Model Tier | Non-Numeric Entries | `SUPPORTS` | `TANGENTIAL` | `IRRELEVANT` | `MISLEADING` | `MISLEADING` Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **`free` (Tier 0)** | 121 | 88 (72.7%) | 12 (9.9%) | 9 (7.4%) | **12 (9.9%)** | **9.92%** |
| **`model-a3` (Tier 2)** | 44 | 32 (72.7%) | 6 (13.6%) | 3 (6.8%) | **3 (6.8%)** | **6.82%** |
| **`model-a2` (Tier 3)** | 972 | 766 (78.8%) | 146 (15.0%) | 57 (5.9%) | **3 (0.3%)** | **0.31%** |
| **`model-a1` (Tier 4)** | 6 | 5 (83.3%) | 1 (16.7%) | 0 (0.0%) | 0 (0.0%) | **0.00%** |
| **`model-a4` (Tier 5)** | 1 | 0 (0.0%) | 1 (100.0%) | 0 (0.0%) | 0 (0.0%) | **0.00%** |
| **Total** | **1,144** | **891 (77.9%)** | **166 (14.5%)** | **69 (6.0%)** | **18 (1.6%)** | **1.57%** |

- **Why `free` and `tier3` differ from `tier2`:** Although the headline `HOLLOW` rate is ~35–36% across `free`, `model-a3`, and `model-a2`, the failure mechanisms differ sharply:
  - **`free` (`model-b1`, `model-c1`, `nemotron`) and `model-a3`** account for **15 of the 18 `MISLEADING` entries (83.3%)**. They frequently pick an arbitrary declaration from `@SRC` (`check_associativity_for_pair`, `su2_level`, `hMatrix`, `test_unit_qm223_...`, `pub mod engine_bridge;`, `pub mod finite_valuation;`) and paste a sentence from the target node's statement onto it.
  - **`model-a2`** rarely fabricates what a cited declaration says (`MISLEADING` rate is only 3 / 972 = 0.31%, all three involving `FIELD_CONTINUUM_DEBT` or `AUTHORITY_EFFECT` constants). Instead, when `model-a2` is asked to mine an `OPEN` continuum fence, unproved conjecture, or methodological `DEFINITION` node that has no supporting code in the repo, it accurately describes whatever `@KNOWN+` neighbour declaration (`GenesisFspBridge.cut_endpoints_distinct`, `FiniteGraphDressing.dress`, `DerivationDagQMClosure.pg_six_operations_and_primdiff_admission_gate`) or `@SRC` fuzzy match (`HilbertLiftL2Model`, `MubIndexTransport`, `TargetA8CollarBoundary`) was injected into its prompt, producing `TANGENTIAL` (146) or `IRRELEVANT` (57) entries.
  - **`model-a1` (5 accepted runs)** was only reached when Tiers 0–3 failed on `OPEN` or `IMPORTED_ASSUMPTION` nodes without matching declarations: 3 of its 5 acceptances (`DFM-BPHZ-CONTINUUM-FENCE`, `FSP-DISCRETE-FERMION-DOUBLING`, `FSP-Ginsparg-Wilson-IMPORT`) were numeric-only Round 1 runs, and 1 (`DFM-GAUGE-SLICE-NONUNIQUENESS`) cited `@KNOWN+` `FiniteGraphDressing.dress` (`TANGENTIAL`).

---

## 3. The 20 Worst Examples

The 20 worst verified entries across the accepted runs are quoted below (with `entry_index` cross-referencing `semantic_review_2026_10_22.json`).

### 1. `[928]` `TFQ-0125` (`model-a3`, `MISLEADING`) — Bare `pub mod` cited as a theorem about Born weights and non-signalling
- **Run:** `TFQ-0125/20261021T161800Z_ladder` (`a2-1`)
- **Node statement:** *"Covers engine_bridge.rs, quantum_foundations.rs, density_matrix.rs, and born_rule.rs... born_rule.rs takes Born weight on Q(i)^d as the rational ratio |<e_k, psi>|^2 / <psi, psi>..."*
- **Entry (`relation` `r1`):** `"engine_bridge preserves rational Born weight ratios and enforces non-signalling across subsystems without minting authority"`
- **Cited declaration (`code/rust/src/qm/campaigns/mod.rs::engine_bridge`, line 22):**
  ```rust
  pub mod engine_bridge;
  ```
- **Why it passed & why it fails:** `DeclIndex` indexes `pub mod <name>;` with `kind="mod"`, and `statement_drift` allowed the numerals/tokens because none were backticked outside the target statement. A two-token module import line states nothing about Born weights or non-signalling.

### 2. `[927]` `TFQ-0125` (`model-a3`, `MISLEADING`) — Bare `pub mod` cited as an arity-1 operator
- **Run:** `TFQ-0125/20261021T161800Z_ladder` (`a2-1`)
- **Entry (`generator` `g1`):** `(BridgeInput) -> BridgeOutput [arity=1, carrier=Exact engine bridge]`
- **Cited declaration (`code/rust/src/qm/campaigns/mod.rs::engine_bridge`, line 22):** `pub mod engine_bridge;`
- **Why it passed & why it fails:** In `verify.py` (`check_arity`, line 417), Rust arity checking is guarded by `if lang == "rust" and decl["kind"] == "fn":`. Because `decl["kind"] == "mod"`, `check_arity` returned `None` (no error), allowing `pub mod engine_bridge;` to pass as a 1-argument function.

### 3. `[1066]` `TFQ-0226` (`model_c/model-c1`, `MISLEADING`) — Bare `pub mod` cited as an arity-6 function
- **Run:** `TFQ-0226/20261021T161800Z_ladder` (`a0-2`)
- **Node statement:** *"Finite valuations that accompany a quantum derivation stay on exact rationals. finite_valuation.rs uses Rational values, rejects a negative mass or a nonzero mass on the empty event..."*
- **Entry (`generator` `G1`):** `(F0, F1, F2, F3, F4, F5) -> F6 [arity=6, carrier=C]`
- **Cited declaration (`code/rust/src/finite_probability/mod.rs::finite_valuation`, line 25):**
  ```rust
  pub mod finite_valuation;
  ```
- **Why it passed & why it fails:** Same `check_arity` bypass on `kind="mod"`. The model invented 6 dummy inputs `(F0..F5) -> F6` on a module declaration.

### 4. `[1064]` `TFQ-0225` (`model-a3`, `MISLEADING`) — Parameterless `structure` cited as an arity-1 boundary-to-collar function on an unrelated governance node
- **Run:** `TFQ-0225/20261021T035611Z_ladder` (`a2-1`)
- **Node statement:** *"A certifier catalog row does not discharge the claim it indexes. mathematical_claim.rs documents one registry and stores AuthorityEffect: None on every record..."*
- **Entry (`generator` `g_collar_graph`):** `(Boundary) -> Collar [arity=1, carrier=CollarGraph]`
- **Cited declaration (`lean4/TargetA8CollarBoundary.lean::MUB6.Gluing.TargetA8.CollarGraph`, line 25):**
  ```lean
  structure CollarGraph where
    boundaryVertices : Nat
    collarVertices : Nat
    cutEdges : Nat
    ...
  ```
- **Why it passed & why it fails:** In `verify.py` (line 422), Lean arity checking runs only when `decl["kind"] in ("theorem", "lemma", "def", "abbrev")`, skipping `structure`. Worse, `TargetA8CollarBoundary.lean` is an area-law rank-bound file offered by `@SRC` fuzzy matching on `boundary`, unrelated to `mathematical_claim.rs`.

### 5. `[861]` & `[862]` `TFQ-0025` (`provider_b/model-b1`, `MISLEADING`) — Model states the opposite of the cited theorem (confusing the Wilson loop with the Creutz ratio)
- **Run:** `TFQ-0025/20261021T035611Z_ladder` (`a0-1`)
- **Entry `[861]` (`relation` `r_creutz_area`):** `"For any beta_tilde ≠ 0 and integers R,T ≥ 1, the Creutz ratio computed from area law Wilson loops equals beta_tilde ^ (R * T)."`
- **Entry `[862]` (`relation` `r_creutz_perim`):** `"For any beta_tilde ≠ 0 and integers R,T ≥ 1, the Creutz ratio computed from perimeter law Wilson loops equals beta_tilde ^ (2 * (R + T))."`
- **Cited declaration (`lean4/FiniteQM.lean::FiniteQM.wilson_creutz_ratio_area_vs_perimeter`, line 268):**
  ```lean
  theorem wilson_creutz_ratio_area_vs_perimeter (b : Rat) (hb : b ≠ 0) :
      let w_area (r t : Nat) : Rat := b ^ (r * t)
      let w_perim (r t : Nat) : Rat := b ^ (2 * (r + t))
      (w_area 2 2 * w_area 1 1) / (w_area 2 1 * w_area 1 2) = b ∧
      ...
      (w_perim 2 2 * w_perim 1 1) / (w_perim 2 1 * w_perim 1 2) = 1
  ```
- **Why it passed & why it fails:** The theorem defines the Wilson loops `w_area(r,t) = b^(r*t)` and `w_perim(r,t) = b^(2*(r+t))` and shows that the **Creutz ratios** equal `b` (area law) and `1` (perimeter law). The model misread the `let` bindings as the Creutz ratios themselves.

### 6. `[904]` `TFQ-0038` (`model_c/model-c1`, `MISLEADING`) — `theorem` with 0 parameters cited as an arity-2 generator
- **Run:** `TFQ-0038/20261021T161800Z_ladder` (`a0-2`)
- **Node statement:** *"weyl_heisenberg_finite_trace_obstruction checks on 2x2 and 3x3 rational matrices that Tr(AB - BA) is 0 while Tr(I_2) is 2 and Tr(I_3) is 3, so AB - BA cannot equal the identity..."*
- **Entry (`generator` `weyl_heisenberg_finite_trace_obstruction`):** `(Matrix, Matrix) -> Trace [arity=2, carrier=Q]`
- **Cited declaration (`lean4/FiniteQM.lean::FiniteQM.weyl_heisenberg_finite_trace_obstruction`, line 403):**
  ```lean
  theorem weyl_heisenberg_finite_trace_obstruction
      (a00 a01 a10 a11 b00 b01 b10 b11 : Rat) : ...
  ```
- **Why it passed & why it fails:** `verify_p0` does not reject `decl["kind"] == "theorem"` when `entry_kind == "generator"`, and `lean_arity` counted 0 binders on line 403 because the binder `(a00 ... : Rat)` was on line 404 (outside the single-line regex before `:=`), returning `arity=None` and bypassing `check_arity`.

### 7. `[838]` `TFQ-0013` (`model-a3`, `MISLEADING`) — Citing `check_associativity_for_pair` for a claim about `from_operation` skipping that check
- **Run:** `TFQ-0013/20261021T161800Z_ladder` (`a2-1`)
- **Entry (`relation` `r1`):** `"from_operation constructs a FiniteGroup from an associative operation without a separate associativity table check, so associativity is inherited from the supplied operation."`
- **Cited declaration (`code/rust/src/lie_theory/finite_group.rs::check_associativity_for_pair`, line 213):**
  ```rust
  fn check_associativity_for_pair(&self, a: usize, b: usize, n: usize) -> Result<(), GroupError> {
      let ab = self.at(a, b);
      for c in 0..n { if self.at(ab, c) != self.at(a, self.at(b, c)) { return Err(...); } }
      Ok(())
  }
  ```
- **Why it passed & why it fails:** `check_associativity_for_pair` is the brute-force table check itself; it says nothing about `from_operation`.

### 8. `[841]` `TFQ-0015` (`provider_b/model-b1`, `MISLEADING`) — Citing `finite_group.rs::check_associativity_for_pair` on the `su2.rs` / `lorentz.rs` Cayley node
- **Run:** `TFQ-0015/20261021T161800Z_ladder` (`a0-1`)
- **Node statement:** *"su2.rs represents SU(2) elements over Q(i) and checks unitarity and determinant 1. lorentz.rs builds rational boost matrices via the Cayley transform..."*
- **Entry (`relation` `r_assoc`):** `"For all a, b, c < n, the multiplication table satisfies at(at(a,b),c) = at(a,at(b,c))."`
- **Cited declaration (`code/rust/src/lie_theory/finite_group.rs::check_associativity_for_pair`, line 213):** Propagated via `@KNOWN+` from `TFQ-0013`; `TFQ-0015` is about `su2.rs` and `lorentz.rs`, not finite group multiplication tables.

### 9. `[829]` `TFQ-0010` (`model_c/model-c1`, `MISLEADING`) — Citing Python JSON schema validator `validate_contract` for a claim about Rust Lie-theory modules
- **Run:** `TFQ-0010/20261021T035611Z_ladder` (`a0-2`)
- **Node statement:** *"finite_group.rs, finite_groupoid.rs, su2.rs, and lorentz.rs each carry AuthorityEffect: None..."*
- **Entry (`relation` `authority_fence`):** `"The Lie-theory modules finite_group.rs, finite_groupoid.rs, su2.rs, and lorentz.rs carry AuthorityEffect: None and do not derive a continuum Lie group."`
- **Cited declaration (`code/python/src/wdp/finite_qm_contract.py::validate_contract`, line 32):** Checks dictionary keys of a Python `FiniteQMContractV1` dict; never mentions `finite_group.rs`, `su2.rs`, or `lorentz.rs`.

### 10. `[839]` `TFQ-0012` (`host_n/nemotron-3.5-lightning:free`, `MISLEADING`) — Citing `NoSignallingCore.lean::hMatrix` for a claim about `WeylHeisenberg` clock period `2d`
- **Run:** `TFQ-0012/20261021T035611Z_ladder` (`a0-3`)
- **Node statement:** *"heisenberg.rs defines WeylHeisenberg on a finite clock with tau^2 = omega, where the label period is d for odd d and 2d for even d..."*
- **Entry (`relation` `weyl_tau_squared_equals_omega`):** `"WeylHeisenberg enforces tau^2 = omega and has label period d (odd d) or 2d (even d)."`
- **Cited declaration (`lean4/NoSignallingCore.lean::QuantumMechanics.NoSignallingCore.hMatrix`, line 33):**
  ```lean
  def hMatrix : Mat2Int := ⟨1, 1, 1, -1⟩
  ```
- **Why it passed & why it fails:** `hMatrix` is a constant $2\times 2$ integer matrix in `NoSignallingCore.lean`. Because `statement_drift` pools numerals from `target_statement` (`2` is in `2d`), the relation passed with zero lexical overlap with `hMatrix`.

### 11. `[913]` `TFQ-0046` (`model_c/model-c1`, `MISLEADING`) — Citing `su2_level` for a claim about Fibonacci anyon braiding in $\mathbb{Q}(\zeta_{10})$
- **Run:** `TFQ-0046/20261021T035611Z_ladder` (`a0-2`)
- **Node statement:** *"braiding.rs computes the Fibonacci braiding matrix diag(zeta_10^-4, zeta_10^3) over Q(zeta_10)..."*
- **Entry (`relation` `fib_braid`):** `"fibonacci_anyon_braiding_matrix returns diag(zeta_10^-4, zeta_10^3) with entries in Q(zeta_10)."`
- **Cited declaration (`code/rust/src/fusion_categories/su2_level.rs::su2_level`, line 39):** Constructs $SU(2)_k$ ribbon categories using an $8(k+2)$-th root of unity; never mentions Fibonacci anyons or $\zeta_{10}$.

### 12. `[919]` `TFQ-0050` (`model_c/model-c1`, `MISLEADING`) — Citing `su2_level` for a claim that the absence of `su3_level.rs` is an open obligation
- **Run:** `TFQ-0050/20261021T035611Z_ladder` (`a0-2`)
- **Entry (`relation` `R1`):** `"The absence of su3_level.rs constitutes an open obligation, not a negative theorem about the existence of SU(3) fusion categories. For K=0, C is free of the field-too-small obstruction, and the SU(2) level-3 example is multiplicity-free."`
- **Cited declaration (`code/rust/src/fusion_categories/su2_level.rs::su2_level`, line 39):** Constructor for $SU(2)_k$; says nothing about `su3_level.rs` or $K=0$.

### 13. `[929]–[932]` `TFQ-0092`, `TFQ-0095`, `TFQ-0096`, `TFQ-0097` (`provider_b/model-b1`, `MISLEADING`) — Citing a QM-223 Slater-determinant test across four unrelated QM campaigns
- **Runs:** `TFQ-0092`, `TFQ-0095`, `TFQ-0096`, `TFQ-0097` (`20261021T035611Z_ladder`, `a0-1`)
- **Entries:** Claim identities for `QM-222` ($SU(2)/SU(3)$ Casimir), `QM-225` (Dirac $\gamma^5$ and CPT conjugation), `QM-226` (Schwinger $g-2 = \alpha/(2\pi)$), and `QM-227` (Lamb shift Bethe logarithm).
- **Cited declaration (`code/python/tests/test_e2e_pauli_spin_statistics_graph_control.py::test_unit_qm223_two_fermion_antisymmetry_pauli_exclusion_and_slater_determinant`, line 21):** Checks $2\times 2$ Slater determinant antisymmetry for `QM-223`; contains zero references to Casimir operators, Dirac matrices, Schwinger $g-2$, or the Lamb shift.

### 14. `[920]` `TFQ-0103` (`host_n/nemotron-3.5-lightning:free`, `MISLEADING`) — Electrostatics Schur-complement probe cited as Ponzano–Regge spin-foam invariance
- **Run:** `TFQ-0103/20261021T161800Z_ladder` (`a0-3`)
- **Node statement:** *"The constraint-closure ledger records a Ponzano-Regge style bound: a fixed-angle linear functional moves by at most the l1 distance of the spin labels times the sup-norm of the angles..."*
- **Entry (`relation` `r1`):** `"Exact deformation invariance holds on the pentagon-to-quad reduction"`
- **Cited declaration (`code/rust/src/mub/native/d6_exact_deformation_invariance_probe_b.rs::probe_b_pentagon_to_quad_exact_invariance`, line 179):** An electrostatics boundary-capacitance Schur-complement test in `mub/native` offered by `@SRC` because its filename shared the words `pentagon` and `invariance`.

### 15. `[971]` `TFQ-0162` (`host_n/nemotron-3.5-lightning:free`, `MISLEADING`) — Non-signalling test cited for a claim about `decoherence_functional` vs Born weight
- **Run:** `TFQ-0162/20261021T035611Z_ladder` (`a0-3`)
- **Entry (`relation` `r1`):** `"decoherence_functional produces a branch count that separates from Born weight"`
- **Cited declaration (`code/rust/src/qm/campaigns/everett.rs::test_everett_branch_non_signaling`, line 122):**
  ```rust
  fn test_everett_branch_non_signaling() {
      assert!(verify_branch_non_signaling());
  }
  ```

### 16. `[972]` `TFQ-0165` (`provider_b/model-b1`, `MISLEADING`) — Citing a 1D/2D frame test to claim that `probability_simplex` enforces Gleason's theorem in $d \ge 3$ (the exact opposite of `TFQ-0165`)
- **Run:** `TFQ-0165/20261021T035611Z_ladder` (`a0-1`)
- **Node statement:** *"probability_simplex.rs checks nonnegative rational weights that sum to 1... This is classical finite probability on a fixed outcome list, not Gleason's theorem."*
- **Entry (`relation` `gleason_uniqueness`):** `"For dimension d >= 3, any noncontextual frame function on the projection lattice is determined by a density operator, as checked by the QM-201 test."`
- **Cited declaration (`code/python/tests/test_e2e_born_rule_gleason_uniqueness_control.py::test_unit_qm201_born_rule_gleason_uniqueness_and_noncontextual_frame_function`, line 20):** Checks a finite rational identity on $d=2$; moreover, `TFQ-0165`'s point is that `probability_simplex.rs` is *not* Gleason's theorem.

### 17. `[992]` `TFQ-0177` (`provider_b/model-b1`, `MISLEADING`) — PyO3 module registration function `#[pymodule] fn tfqm_mub` cited as a mathematical relation on MUB(6)
- **Run:** `TFQ-0177/20261021T161800Z_ladder` (`a0-1`)
- **Entry (`relation` `r_mub6_open`):** `"tfqm_mub keeps dimension-6 MUB existence open and exposes only bounded finite checks to Python."`
- **Cited declaration (`code/rust/src/mub/python.rs::tfqm_mub`, line 143):**
  ```rust
  #[pymodule]
  fn tfqm_mub(m: &Bound<'_, PyModule>) -> PyResult<()> {
      m.add_function(wrap_pyfunction!(prime_power_mub_count, m)?)?; ...
  ```

### 18. `[0]–[4]` `AUTH-BLIND-DERIVATION-PROTOCOL` (`model-a2`, `IRRELEVANT` / `MISLEADING`) — `@KNOWN+` and `@SRC` contaminación on a methodological definition node
- **Run:** `AUTH-BLIND-DERIVATION-PROTOCOL/20261022T000006Z_ladder` (`a3-1`)
- **Node statement:** *"A derivation run toward computation is a proposal source: its prompt, model, tools, repository state, available context and outputs are frozen..."*
- **Verified entries (5):** Cites `GenesisFspBridge.lean::cut_endpoints_distinct` (`theorem` cited as an arity-2 generator `g_cut_endpoints` and as a relation), `GenesisFspBridge.lean::D2_irrefl`, and `HilbertLiftL2Model.lean::toL2` and `l2_model_summary` (Riesz representation on `Fin n -> Q`). None of the 5 verified entries has any connection to blind derivation protocol provenance.

### 19. `[662]–[663]` `PGW-BRANCH-TREES-AND-ROLES` (`model-a2`, `IRRELEVANT`) — MUB(6) transition-matrix separation cited on a Pre-Genesis branch-tree prose node
- **Run:** `PGW-BRANCH-TREES-AND-ROLES/20261021T203121Z_ladder` (`a3-1`)
- **Node statement:** *"With the external continuation policy enabled, isomorphism-quotiented branch DAGs were exported for both readings and both measures within the declared bounds. Under mu2 there is no guard cutoff: the ten trees B1 to B10..."*
- **Entries (`r_col_dist_id`, `r_col_dist_lower`):** Cite `lean4/MubQuadraticTransitionSeparation.lean::columnDistance_identity` (`columnDistance r i j = 72 - 12 * Re(W r 2 i j)`) and `columnDistance_lower` because `@SRC` matched stem tokens `transition`/`separation`.

### 20. `[349]–[353]` `FSP-BF-2GROUP-SIGN-CLAIM` (`model-a2`, `IRRELEVANT`) — 4-element toy carrier cited (with a composition) on an `OPEN` node stating no BF model exists in the checkout
- **Run:** `FSP-BF-2GROUP-SIGN-CLAIM/20261022T001319Z_ladder` (`a3-1`)
- **Node statement:** *"Claimed: in BF theory on finite cell complexes, the Postnikov class in H^3(G, A) governs cancellation of higher 2-group sign anomalies on knotted worldsheets; no BF model, linking computation or cancellation identity exists in this checkout."*
- **Entries (2 generators, 2 relations, 1 composition):** Cite `lean4/HigherTwoGroupCore.lean::surface_loop_holonomy` and `higher_two_double_holonomy` (a 4-element `inductive Carrier | c0 | c1 | c2 | c3` swap involution), earning an `accepted` status (`verified_total=5`) on a node whose statement explicitly records that the claimed BF/Postnikov construction does not exist in the repo.

---

## 4. Recommendations for the Verifier (`dag/pfp/model_ladder/`)

Each failure mode above traces to a specific, fixable gap in `dag/pfp/model_ladder/verify.py`, `packets.py`, or `memory.py`:

1. **Enforce declaration-kind allowlists for `generators` and `relations` (`verify.py`, `verify_p0`, lines 739–777):**
   - For `generators`, require `info["kind"] in ("def", "abbrev", "fn", "struct", "structure", "inductive")` and explicitly reject `theorem`, `lemma`, `mod`, `const`, `static`, and functions whose name starts with `test_` (which `_SYSTEM_P0_RULES` already forbids in prose, but `verify_p0` never checks).
   - For `relations` and `lemmas`, require `info["kind"] in ("theorem", "lemma", "def", "abbrev", "fn")` and explicitly reject `mod`, `const`, `static`, `struct`, `structure`, `inductive`, `class`, and `type`.

2. **Close the `check_arity` bypass on non-`fn` Rust declarations and multi-line Lean signatures (`verify.py`, lines 173–204 and 413–428):**
   - In `lean_arity` (line 173), parse binders across the full signature up to `:=` or `where` in `decl["window"]` rather than only the first line (`decl_line`), so multi-line theorem/def headers do not silently return `arity=None`.
   - In `check_arity` (line 413), if `decl["kind"] in ("mod", "const", "static")`, return `"not_an_operation"` instead of `None`. For Lean `structure`/`inductive`, either check the constructor fields/parameters or require the model to cite the constructor (`Type.mk`).

3. **Fix `statement_drift` so numerals in `target_statement` cannot excuse zero-overlap citations (`verify.py`, lines 431–454):**
   - Currently, `statement_drift(statement, decl_window, target_statement)` pools numerals from `decl_window + "\n" + target_statement`. That allows a model to copy a sentence (including its numbers) from `target_statement` and attach it to *any* declaration in the repo (`pub mod engine_bridge;`, `def hMatrix`, `fn su2_level`, `fn check_associativity_for_pair`).
   - Fix: Require every `relation` and `lemma` to share at least one non-trivial identifier or domain token (beyond stop-words and generic types `Nat`, `Int`, `Rat`, `Bool`) with **`decl_window` itself**, and check numerals against `decl_window` rather than `target_statement`.

4. **Restrict `@KNOWN+` neighbour propagation to 1 hop and block unanchored `OPEN` / `DEFINITION` nodes from passing on `@KNOWN+` alone (`packets.py` line 288, `memory.py` line 178):**
   - Currently, `positive_entries` injects verified entries from any accepted neighbour into `@KNOWN+`. Once a generic lemma (`FiniteGraphDressing.dress`, `GenesisFspBridge.cut_endpoints_distinct`, `DerivationDagQMClosure.pg_six_operations_and_primdiff_admission_gate`) is accepted on one node, it cascades across multi-hop chains of `OPEN` and `DEFINITION` nodes (`bucket 8` had an **8.0%** `SUPPORTS` rate: 4 / 50).
   - Fix: Do not count a cited declaration toward `min_verified` unless its file path is either (a) listed in the target node's own `lean`/`rust`/`python`/`source` fields or derivation markdown (`buckets 1–5`), or (b) offered by `@SRC` with a verified identifier overlap with the node's `statement`. Entries from `@KNOWN+` whose files belong only to a neighbour should be recorded as context, not credited toward `status = "accepted"`.

5. **Tighten `@SRC` fuzzy file-stem matching (`packets.py`, `source_candidates`, lines 243–257):**
   - Even with `STEM_DOC_FREQUENCY_LIMIT = 20`, single-stem or generic two-stem matches (`tensor`, `boundary`, `repair`, `index`, `c3`, `pentagon` + `invariance`) offered unrelated files from other stages (`MubIndexTransport.lean` on `PGW-RUNG4-INDEX-UP-TO-ISOMORPHISM`, `d6_exact_deformation_invariance_probe_b.rs` on `TFQ-0103`, `TargetA8CollarBoundary.lean` on `TFQ-0225`, `conj2_tensor_product_proof.py` on `CQFT-FINITE-POSET-NET-TARGET`).
   - Fix: Filter `@SRC` fallback candidates by stage/directory affinity (or require >=2 domain-specific stem tokens after excluding cross-repo structural vocabulary like `tensor`, `boundary`, `index`, `repair`, `matrix`, `carrier`, `bridge`, `contract`, `gate`).

6. **Re-verify or quarantine the 60 Round-1 numeric-only `accepted` receipts (`runner.py` / `verify_p0`):**
   - Although `verify_p0` now defaults to `numeric_counts: bool = False` (line 695), 60 run receipts on disk from Round 1 still carry `summary.status == "accepted"` with zero non-numeric entries. Re-running `verify_p0(..., numeric_counts=False)` over existing receipts will downgrade all 60 numeric-only runs to `not_accepted`.

---

## 5. Claim Hygiene Summary

1. **What this audit supports:**
   - Across all 404 accepted MODEL ladder runs (`dag/results/<NODE>/runs/*_ladder/`), 891 of the 1,144 verified non-numeric entries (77.88%) cite declarations that are genuine ingredients of their node's statement (`SUPPORTS`), while 166 (14.51%) are `TANGENTIAL`, 69 (6.03%) are `IRRELEVANT`, and 18 (1.57%) are `MISLEADING`.
   - At the run level (where numeric claims earn no credit), 147 of the 404 accepted runs (36.39%) are `HOLLOW`: 60 have only numeric claims from Round 1, and 87 have only `TANGENTIAL`, `IRRELEVANT`, or `MISLEADING` non-numeric entries.
2. **What this audit does not support:**
   - It does not show that a `SUPPORTS` classification on a P0 operad entry constitutes a proof of an `OPEN` node; on `OPEN` frontier targets (`LQG-TV-LEVEL2-PENTAGON-TARGET`, `CQFT-MYRHEIM-MEYER-ORDERING-FRACTION-TARGET`), `SUPPORTS` indicates only that the cited existing helper declaration is a real ingredient named in the target statement.
   - It does not evaluate the 292 `not_accepted` or `blocked_abstained` ladder runs.
3. **The narrowest defensible claim:**
   - In the audited 404 accepted ladder receipts, nodes with anchored files in `dag/derivation_dag.json` (`buckets 1–3`) achieve a 95.3% entry-level `SUPPORTS` rate (651 / 683), whereas unanchored nodes relying on `@KNOWN+` neighbour propagation (`bucket 8`) or `@SRC` fuzzy stem matching (`bucket 9`) exhibit high `HOLLOW` rates, and `free`/`tier3` tiers account for 15 of the 18 `MISLEADING` entries via declaration-kind and `statement_drift` loopholes in `verify.py`.
4. **The next test needed:**
   - Implement the five verifier checks in `dag/pfp/model_ladder/verify.py` and `packets.py` (declaration-kind allowlists, `check_arity` on `mod`/`const`/`structure` and multi-line Lean headers, `decl_window` lexical overlap in `statement_drift`, and target-file anchoring for `min_verified`) and replay `verify_p0(..., numeric_counts=False)` across all 696 run folders to verify that all 147 `HOLLOW` runs and all 18 `MISLEADING` entries are rejected.
