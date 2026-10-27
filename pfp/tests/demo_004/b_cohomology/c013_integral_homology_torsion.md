# C013: Integral Homology with Torsion and Smith Normal Form Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that returns the integral homology of hidden simplicial complexes, Betti
> numbers and torsion, each certified by a unimodular Smith normal form, for under $0.50.

## 2. Why This Task

Homology over Q forgets torsion. The real projective plane has rational Betti numbers (1, 0, 0), like a point, yet H_1(RP²; Z) = Z/2. Over F₂ the same space has Betti numbers (1, 1, 1). A solver that eliminates over the wrong ring gets a confident, wrong answer. The honest certificate is a Smith normal form: unimodular integer matrices U and V with U·∂·V = D diagonal and d₁ | d₂ | … | d_r. It is cheap to check (multiply and compare) and hard to produce without integer blow-up. `engine/crates_rs/core_homology/src/smith_normal_form.rs` states the same point: rank over Q discards torsion.

The challenge stresses the Symbol Game's exact host, OEWAS (Engine Workflows, Agents, Skills) synthesis, and no OEEIS (Engine Epistemic Immune System) mechanism beyond the refusal path. A pass shows the game can produce a certified integral-homology solver. It says nothing about which spaces the complexes "are" beyond their homology.

## 3. Formal Problem and Bounds

Input: a finite abstract simplicial complex K, given by its maximal simplices over integer vertex labels, of dimension at most 3. Orient each simplex by increasing vertex label; ∂_n: C_n → C_{n−1} is the usual alternating-sign boundary. Output for each degree n ≤ dim K:

H_n(K; Z) ≅ Z^{β_n} ⊕ Z/t₁ ⊕ … ⊕ Z/t_s, with t_i > 1 and t₁ | t₂ | ….

Here β_n = dim C_n − rank ∂_n − rank ∂_{n+1}, and the t_i are the invariant factors greater than 1 of ∂_{n+1}.

Reference values (Hatcher 2002, Chapter 2):

| Space | H_0 | H_1 | H_2 | H_3 |
| --- | --- | --- | --- | --- |
| RP² (for example the 6-vertex triangulation) | Z | Z/2 | 0 | |
| Klein bottle | Z | Z ⊕ Z/2 | 0 | |
| Torus (for example the 7-vertex triangulation) | Z | Z² | Z | |
| S² | Z | 0 | Z | |
| Mod-p Moore space S¹ ∪_p D², triangulated | Z | Z/p | 0 | |
| Lens space L(p, q), triangulated | Z | Z/p | 0 | Z |

Triangulations of Moore spaces and lens spaces are built and verified by the second checker at packet-build time; this spec asserts only their homology.

Bounds: at most 1,000 simplices in total, dimension ≤ 3, p ≤ 7 for Moore and lens spaces. The hidden set must contain all six families, cones and suspensions (contractible and shifted homology), disconnected complexes (β₀ > 1), and complexes whose F₂ Betti numbers differ from their rational ones.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "homology": [{"n": "0", "betti": "1", "torsion": []}, {"n": "1", "betti": "0", "torsion": ["2"]}, {"n": "2", "betti": "0", "torsion": []}], "snf": [{"boundary": "2", "U": [["1", "0"], ["0", "1"]], "U_inv": [["1", "0"], ["0", "1"]], "V": [["1"]], "V_inv": [["1"]], "D": ["2"]}]}
{"status": "OUT_OF_SCOPE", "witness": {"missing_face": ["3", "5"], "of_simplex": ["1", "3", "5"]}}
{"status": "UNKNOWN", "refusal": "CERTIFICATE_TOO_LARGE"}
```

For each boundary map ∂_n the certificate gives integer matrices U, U⁻¹, V, V⁻¹ (with U·U⁻¹ = I and V·V⁻¹ = I, which proves unimodularity without a determinant) and the diagonal D, with U·∂_n·V = D and the divisibility chain. A replayable log of elementary row and column operations may replace the four matrices. The certificate is complete when every boundary map is covered and the stated β_n and torsion follow from the D's. `OUT_OF_SCOPE` covers inputs that are not closed under faces, with the missing face as witness. (The example SNF entry is schematic; real boundary matrices are larger.)

## 5. Participant Packet

- `TASK.md` with orientation conventions, the certificate format and the log alternative.
- `examples/`: 20 public cases with exact input and output JSON: a point, a circle, S², the 7-vertex torus, the 6-vertex RP², a Klein bottle, a mod-3 Moore space, a cone, a disjoint union, and two not-closed inputs.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 40, covering every family above, several p values, and dimension 3.
- **Relabel controls:** 16. Vertex relabelling (changes orientations and signs; homology unchanged) and one barycentric subdivision per family (much larger complex; homology unchanged).
- **Poisoned but schema-valid:** 12. RP² and Klein-bottle triangulations, where F₂ elimination gives wrong answers; a Moore space with p = 6 (torsion Z/6, which a solver might split as Z/2 ⊕ Z/3; both describe the same group, so the checker compares the invariant-factor form); a complex with a maximal simplex listed twice.
- **Exact checker:** `core_linear_algebra::smith_normal_form_checked` recomputes each D, and a direct BigInt product checks U·∂·V = D and the inverse identities. `core_homology::smith_normal_form::torsion_coefficients` covers only degrees 0 to 2 of three-term complexes; lens spaces need the per-matrix route, which works in any degree.
- **Independent second checker:** a separately written Python integer elimination, cross-checked against `core_homology::exact_betti` for the 2-dimensional cases.
- **Checker mutation suite:** a U that is not unimodular (U·U⁻¹ ≠ I in one entry); a correct D with a wrong divisibility order; D with a torsion 2 replaced by 1; an off-by-one sign in ∂; torsion reported for the top degree of a 2-complex.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis of the complex builder, boundary maps and SNF.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** `smith_normal_form_checked` applied per boundary map and wrapped as `solve`. Expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, Qwen3-32B, `deepseek/deepseek-r1-distill-llama-70b` (route pinned in U06). $0.50 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only, so solvers cannot import a computer-algebra package; any setup help is logged. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 40/40 hidden base cases with complete certificates, all relabel and subdivision controls consistent, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Error taxonomy:** per arm, counts of torsion lost (Q elimination), torsion invented (F₂ elimination) and non-unimodular certificates.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified integral homology at this budget.
- **All arms get Betti numbers right and lose torsion:** the models defaulted to field elimination; the certificate format caught it.
- **A ties D:** sampling whole solvers explains the result.
- **E matches A:** useful automation with no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the checker's refusal is the only immune analogue.
- **Antimorphisms expected:** field substitution (Q or F₂ in place of Z), AM-5-style orientation sign errors, and claimed certificates that do not multiply out (AM-FSP-2).
- **Layer 2:** grammar-constrained certificate JSON allowed equally. **Layer 1, scratch space:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, then `D` steps as candidate solvers pass more public cases (for a single SNF run, `D` also describes each elimination step lowering the count of nonzero off-diagonal entries), `M` for rejected certificates, `E` when all public certificates replay, `T`. Logged measures: public cases failed, off-diagonal nonzeros remaining, largest intermediate entry size.

Operands this challenge should yield:

```text
operand field_vs_integer_trap.v1 | kind: guard | when: F2 and Q Betti numbers disagree | do: compute invariant factors over Z; report factors > 1 as torsion | check: U d V = D replays
operand euler_crosscheck.v1 | kind: guard | when: homology is reported | do: compare sum (-1)^n dim C_n with sum (-1)^n beta_n | check: equal
operand unit_pivot_first.v1 | kind: move | when: reducing an integer matrix | do: eliminate on entries of absolute value 1 first to limit growth | check: largest entry stays below the declared cap
```

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_linear_algebra` (`smith_normal_form.rs`, `smith_normal_form_checked` with U, V).
- `engine/crates_rs/core_homology` (`smith_normal_form.rs`, `exact_betti.rs`, `simplicial.rs`, `chain_complex.rs`).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: none in the catalog. Checker work: a small driver that applies `smith_normal_form_checked` to every boundary map of a 3-complex.

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose integral homology and SNF certificates replay exactly on hidden complexes up to dimension 3.
- **Does not support:** that complexes with equal homology are homeomorphic or homotopy equivalent; any cohomology-ring statement (that is [C016](c016_cohomology_ring_cup_products.md)); anything about physical spaces.
- **Narrowest defensible claim:** the frozen solver returned replayable unimodular SNF certificates and correct integral homology on the measured number of hidden complexes.
- **Next test:** cohomology rings in C016 and persistent homology in [C015](c015_persistent_homology_barcodes.md).
