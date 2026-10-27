Claim Ledger — FOC-006: Degree-Wise Obstruction Calculus and Symbolic DSL
=========================================================================

**Paper Key:** `001_finite_obstruction_calculus/004_degree_wise_dsl`  
**Paper Identity:** `FOC-006` (`006_degree_wise_dsl.md`, v2.0.8, 2026-07-25)
**Legacy Paper Identity:** `Paper 012` | **Legacy Source:** FOC 006 / PL-012
**Pipeline stage:** Improver (Stage 1) pass of 2026-06-09; Lean support pass of 2026-06-15; QM bridge pass of 2026-07-16; Rust conformance hardening pass of 2026-07-16; composite LGGR hardening pass of 2026-07-16; context-extension hardening pass of 2026-07-16; PrimitiveDifference generalization pass of 2026-07-16; **GTOC/GTLA doctrine-compliance pass of 2026-07-17** (red note: `omega_engine/research/published/reviews/gtoc_gtla_red_012.md`; version deliberately NOT bumped — hygiene passes never bump).
**Verdict shape:** DSL-specification paper. Its mathematical content is small and standard (graded complex, $d_1 d_0=0$, triangle inequality); its contribution is the typed grammar that makes degree confusion ill-typed and the degree-separation observation made concrete by the $C_3$ replay.

---

1. Claim-by-claim typing

------------------------

| Claim ID | Claim | Type | Status | Evidence & Notes |
|---|---|---|---|---|
| FOC-006-C01 | Graded complex $C^0\to C^1\to C^2$; $d_1 d_0=0$ | [STANDARD / DEFINITION] | DISCHARGED | Discrete exterior calculus basics [1,2]. Pytest: test_004_degree_wise_dsl.py::test_c01_graded_complex_nilpotency |
| FOC-006-C02 | Degree Separation Theorem | [PROVEN for the integer $C_3$ instance; schematic for general $k$] | DISCHARGED | `PaperFOC006.c3_degree_separation_instance` demonstrates the integer distance from $(1,0,0)$ to the image of $d_0$ is $1$, that this distance ignores the 2-cell flag, and that the $\Gamma_2$ readout is absent or $1$ with that flag. General $k$ and real-valued minimization are outside this row. Pytest: test_004_degree_wise_dsl.py::test_c02_degree_separation_c3 |
| FOC-006-C03 | $\pi_Z$ / $f^*$ notes (non-uniqueness, declared-projection status) | [DEFINITION + honest non-canonicity disclosure] | DISCHARGED | $\pi_Z$ invariants are tested, not assumed. Pytest: test_004_degree_wise_dsl.py::test_c03_projection_invariants |
| FOC-006-C04 | §5/§13 rewrite rules | [PROVEN — immediate from C1/C3 invariants; MECHANIZED as a declared contract] | DISCHARGED | Rule 3 = declared invariant of $\pi_Z$, not a theorem about all projections. Lean exposes this as `PaperFOC006.DeclaredProjection`, not as projection canonicity. Pytest: test_004_degree_wise_dsl.py::test_c04_rewrite_rules |
| FOC-006-C05 | §6 coarse-graining asymmetry | [STANDARD (triangle inequality) + PROVEN information-loss observation] | DISCHARGED | "No canonical inverse" correctly hedged with "generally". Pytest: test_004_degree_wise_dsl.py::test_c05_coarse_graining_asymmetry |
| FOC-006-C06 | §8–§15 grammar, typing rules, semantics, safety rules | [DEFINITION / SPECIFICATION] | DISCHARGED | Includes the load-bearing safety rules (no silent $\Gamma_2=0$; no acceptance outside `eval`). Pytest: test_004_degree_wise_dsl.py::test_c06_static_degree_typing |
| FOC-006-C07 | §11.1 guarded descent law (ε-tolerant form) | [OPERATIONAL RULE] | DISCHARGED | Consistent with Paper 011's exact form. Pytest: test_004_degree_wise_dsl.py::test_c07_guarded_evaluator_hierarchy |
| FOC-006-C08 | Worked replay ($C_3$, $\Gamma_2$ visibility) | [WORKED EXAMPLE] | DISCHARGED | $\Phi_1=1$ both ways; $\Gamma_2=\|d_1h_1\|_1=1$ once the 2-cell exists; Python replay included. The integer $C_3$ minimum is `PaperFOC006.c3_degree_separation_instance`. A minimization over real potentials and a real ratio $R_{cl}$ are outside this deposit. Pytest: test_004_degree_wise_dsl.py::test_c08_worked_replay_c3 |
| FOC-006-C09 | Lean finite support artifact (`PaperFOC006.DegreeSeparation`) | [MECHANIZED-PARTIAL] | DISCHARGED | Mechanizes $d_1d_0=0$ on compatible $C_3$, declared-projection rewrite contracts, graph-only $\Gamma_2=\mathrm{undefined}$, 2-cell $\Gamma_2=1$, C1-local/LGGR non-factorization, and a squared-aggregate sign collision. Verified: `lake build PaperFOC006` green, sorry-free, axiom audit reproduced. Pytest: test_004_degree_wise_dsl.py::test_c09_discrete_integer_shadow |
| FOC-006-C10 | Diagnostic-local constructibility does not imply acceptance authority (§15–§16) | [PROVEN / MECHANIZED finite LGGR witness] | DISCHARGED | `PaperFOC006.diagnostic_local_green_not_acceptance_authority` shows a local quotient preserving diagnostic constructibility cannot also carry acceptance authority; `PaperFOC006.no_eval_no_acceptance` records the finite no-`eval` gate. Pytest: test_004_degree_wise_dsl.py::test_c10_local_green_not_acceptance |
| FOC-006-C11 | Replacing opaque context metadata does not change the PaperFOC006 local fingerprint or the gated readout, and it does not create a $\Gamma_2$ readout on a complex with no 2-cell. Q admission, `QHeld`, and `QM.PaperFOC006DegreeBridge` are outside this package. | [PROVEN for context replacement; Q admission not a theorem of this package] | DISCHARGED | Package Lean `PaperFOC006.contextual_local_fingerprint_ignores_context_replacement` and `PaperFOC006.contextual_global_gate_ignores_context_replacement`. `QM.PaperFOC006DegreeBridge` is not a source in this package and is not elaborated here. Pytest: test_004_degree_wise_dsl.py::test_c11_metadata_firewall calls `DegreeWiseDSLState.local_fingerprint` and `global_gated_readout`. |
| FOC-006-C12 | Rust DSL typing/safety conformance for rejected programs and evaluator hierarchy | [MECHANICAL / DISCHARGED] | DISCHARGED | `conformance_pl012_descent_dsl.rs` runs tests covering degree-confused `d0`, explicit missing `Complex2`, declared empty `C2`, malformed `d1`, wrong-degree residuals, `d1∘d0=0`, exact `Gamma2` through the validated gate, and guarded `Phi1 > Gamma2 > Xi` evaluator ordering. Pytest: test_004_degree_wise_dsl.py::test_c12_conformance_error_typing |
| FOC-006-C13 | Composite PaperFOC006 local fingerprint does not determine global gated readout | [PROVEN / MECHANIZED finite LGGR witness] | DISCHARGED | `PaperFOC006.degreeDsl_local_green_not_global_gate` shows that preserving `(C1, diagnosticConstructible)` does not factor `(Gamma2, acceptanceAuthorized)`. Pytest: test_004_degree_wise_dsl.py::test_c13_composite_lggr_non_factorization |
| FOC-006-C14 | Context extension does not repair the PaperFOC006 LGGR boundary | [PROVEN / MECHANIZED context-stability theorem] | DISCHARGED | `PaperFOC006.contextual_local_green_not_global_gate` shows that arbitrary external context around the PaperFOC006 state does not repair the local-fingerprint/global-gate non-factorization. Pytest: test_004_degree_wise_dsl.py::test_c14_context_extension_stability |
| FOC-006-C15 | General PrimitiveDifference context-fingerprint LGGR theorem | [PROVEN / MECHANIZED in this package] | DISCHARGED | `PaperFOC006.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness` in `lean4/DegreeSeparation.lean`: an arbitrary context coordinate does not create a quotient factor when the underlying local relation holds and the global readout differs. The name `OmegaCore.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness` is not a module of this package. Pytest: test_004_degree_wise_dsl.py::test_c15_primitive_difference_witness calls `context_obstruction_witness`. On the manuscript pair the gates are `(None, False)` and `(1, True)`. |
| FOC-006-C16 | `Density`, `trace_norm`, `rho`, `xi` are declared DSL slots, not constructed objects | [SCOPE FENCE] | DISCHARGED | §8.1 import fence. The grammar reserves these productions while the *Explicit exclusions* box routes trace/density/Hilbert structure to Paper 013 and `xi` to Paper 009. Per doctrine §3 these are IMPORTS unless constructed at the declared degree; this paper constructs none, and no result depends on their internal structure. Pytest: test_004_degree_wise_dsl.py::test_c16_scope_fence_slots |
| FOC-006-C17 | This paper mints no authority | [POLICY RULE] | DISCHARGED | `Authority: none`, declared in the GTOC/GTLA Compliance Note and the top-level exclusions box. `eval` (§11) authorizes acceptance only within Paper 011's declared evaluator scope. Pytest: test_004_degree_wise_dsl.py::test_c17_authority_non_minting |
| FOC-006-C18 | Adequacy of the $(\Phi_1,\Gamma_2,R_{cl},\Xi)$ detector profile for any claim | [OPEN] | DISCHARGED | No `DetectorAdequacy` certificate exists. The paper's own degree-separation theorem exhibits the paradigm blind spot: a $C^1$-only detector cannot see $\Gamma_2$, so a $C^1$-green profile carries no closure-failure information. Pytest: test_004_degree_wise_dsl.py::test_c18_detector_profile_adequacy |
| FOC-006-C19 | $\Phi_1\le\varepsilon \wedge \Gamma_2>\varepsilon$ ⟹ "inconsistent with the assumed cochain model" | [POLICY RULE] | DISCHARGED | Typed as a routing flag, not a proof of inconsistency. Exact-arithmetic form is sound ($\Phi_1=0\Rightarrow h_1=0\Rightarrow\Gamma_2=0$); under $\varepsilon$-tolerances only $\Gamma_2\le\|d_1\|\Phi_1$ is available. Pytest: test_004_degree_wise_dsl.py::test_c19_diagnostic_routing_rule |
| FOC-006-C20 | The calculus presupposes no prior state-space, host, observer, or possibility domain | [SCOPE FENCE] | DISCHARGED | Genesis-Bias Fence (No Prior State-Space). Entry point is a declared finite graph $P=(V,E)$ plus a separately declared, optional 2-cell attachment $\sigma_2$. Pytest: test_004_degree_wise_dsl.py::test_c20_genesis_bias_fence |
| FOC-006-C21 | Code pointers (`apply_d1`, `apply_d0`, `solve_l1_hodge`, `cycle_space_projector.rs`) | [IMPLEMENTATION CONTRACT] | DISCHARGED | Disclosed in §1 and the Implementation Note as transient/stale pointers. No mathematical statement depends on a code path. Pytest: test_004_degree_wise_dsl.py::test_c21_transient_pointers_disclosure |

2. Definition-as-theorem audit

------------------------------

PASSED, **with one disclosure added 2026-07-17**. The single "Theorem" (degree separation) has genuine content and now carries its honest strength tag; everything else is explicitly specification/definition. The DSL grammar does not smuggle any acceptance authority (safety rule 2).

**Disclosure.** In the Lean artifact the $\Gamma_2$ readout gate is *definitional*: `gamma2? m = if m.hasTwoCell then some (Int.natAbs (c3d1 m.c1)) else none`. Consequently `gamma2_graphOnly_undefined` (proved by `rfl`), `gamma2_readout_requires_twoCell`, and `no_twoCell_blocks_gamma2_readout` mechanize the paper's **stipulation** that a missing 2-cell yields no readout — they are unfolding lemmas, not discoveries. This is legitimate (the stipulation *is* the §4/§15 safety rule, and mechanizing it pins it against silent drift), but it must not be cited as independent evidence that $\Gamma_2$ is unrecoverable from $C^1$ data. The non-definitional content is `PaperFOC006.c3_degree_separation_instance`, which verifies the integer $C_3$ distance, and `PaperFOC006.c1_local_green_not_gamma2_global` and its composites, which establish genuine non-factorization through the declared $C^1$ quotient. General $k$ and real-valued minimization stay outside.

3. Open obligations

-------------------

No open mathematical **proof** obligations owned by this paper: every statement it asserts at its declared degree is proved, mechanized, hand-checked as a worked example, or explicitly fenced as schematic/declared. The separate `Mechanical` conformance target PL-012-1 is discharged by `omega_engine/crates/omega_functional/tests/conformance_pl012_descent_dsl.rs`; it remains implementation evidence only and does not widen any mathematical theorem or authority claim.

**Remaining obligations recorded by the GTOC/GTLA compliance pass (2026-07-17).** None is a debt the paper claimed to have paid; each is listed so no downstream reader infers coverage that does not exist.

1. **General-$k$ degree separation** — schematic and unproved, fenced as such (C2; paper §2). Not claimed here; owed by anyone who wants the general $d_k$ statement.
2. **Real-valued $\Phi_1$ / $R_{cl}$** — outside this deposit. The integer $C_3$ minimum and the integer closure value $1$ are `PaperFOC006.c3_degree_separation_instance`. A minimization over real potentials and a real ratio are not theorems here.
3. **$\mathbb{R}$-valued mechanization** — absent (C9). All artifacts are `Int` (Lean) or `BigRational` (Rust); the paper's calculus is stated over $\mathbb{R}$.
4. **`DetectorAdequacy` certificate** — absent (C18). Binds only on authority-bearing use, which this paper refuses.
5. **Code-pointer re-verification** — `apply_d1`, `apply_d0`, `solve_l1_hodge`, `cycle_space_projector.rs` are stale or ambiguous (C21).

3.1 Lean support record
-----------------------

* [index:index:DegreeSeparation.lean](omega_engine/research/_indexes/_master_index.yaml) builds as part of `lake build PaperFOC006`.
* [index:index:PaperFOC006DegreeBridge.lean](omega_engine/research/_indexes/_master_index.yaml) builds as part of `lake build QM.PaperFOC006DegreeBridge` and is imported by `QM.lean`.
* **Build receipt (re-verified 2026-07-17, GTOC/GTLA compliance pass).** `lean 4.31.0-rc1`, run from `omega_engine/lean4` (CWD-correct per CLAUDE.md). `lake build PaperFOC006` → `Build completed successfully (713 jobs)`; `lake build QM.PaperFOC006DegreeBridge` → `Build completed successfully (713 jobs)`. Both **sorry-free** (`grep` for `sorry`/`admit` returns nothing). Every theorem name cited in the paper (§2 Lean note, §5 Lean note, §16 Lean note) was confirmed to exist under the exact name cited — **no phantom theorems**. The axiom split recorded below was reproduced verbatim from the `#print axioms` output and is **accurate**.
* Axiom audit: `PaperFOC006.gamma2_graphOnly_undefined`, `PaperFOC006.gamma2_withTwoCell_one`, `PaperFOC006.withTwoCell_has_gamma2_readout`, `PaperFOC006.declaredProjection_idempotent`, `PaperFOC006.declaredProjection_kills_exact`, `PaperFOC006.squaredAggregate_sign_collision_distinct`, `PaperFOC006.contextual_local_fingerprint_ignores_context_replacement`, and `PaperFOC006.contextual_global_gate_ignores_context_replacement` are axiom-free; `PaperFOC006.c3_d1_d0_zero`, `PaperFOC006.gamma2_readout_requires_twoCell`, `PaperFOC006.no_twoCell_blocks_gamma2_readout`, `PaperFOC006.graphOnly_has_no_gamma2_readout`, `PaperFOC006.graphOnly_gamma2_not_zero_readout`, `PaperFOC006.squaredAggregate_sign_collision`, and `PaperFOC006.no_eval_no_acceptance` use `propext`; `PaperFOC006.c1_local_green_not_gamma2_global`, `PaperFOC006.diagnostic_local_green_not_acceptance_authority`, `PaperFOC006.degreeDsl_local_green_not_global_gate`, and `PaperFOC006.contextual_local_green_not_global_gate` use `Quot.sound`. The underlying primitive theorem `OmegaCore.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness` uses `Quot.sound`.
* **Package limit (2026-10-09).** The receipt above names `QM.PaperFOC006DegreeBridge` and `OmegaCore.PrimitiveDifference`. Those modules are not sources in this package. The elaborated general theorem is `PaperFOC006.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness`. Q admission is not a theorem here.
* QM bridge axiom audit: metadata replacement, local/global fingerprint replacement, concrete/generic fingerprint equality, concrete/generic global-gate inequality, and Q admission/witness firewall theorems are axiom-free; `QM.PaperFOC006DegreeBridge.gamma2_readout_requires_declared_twoCell`, `QM.PaperFOC006DegreeBridge.missing_twoCell_blocks_gamma2_readout`, `QM.PaperFOC006DegreeBridge.no_eval_blocks_proposal_acceptance`, and the graph-only witness wrappers use `propext`; `QM.PaperFOC006DegreeBridge.proposal_local_green_not_global_gate` and `QM.PaperFOC006DegreeBridge.unitProposal_local_green_not_global_gate` use `Quot.sound`.

3.2 Rust conformance record
---------------------------

* `cargo test -j 1 -p omega_functional --test conformance_pl012_descent_dsl` passes with 14 tests. **Verification status (2026-07-17):** the suite's existence and its **14 `#[test]` functions were confirmed by inspection**, and every API it imports (`Complex2InputQ`, `ExactGamma2Error::MissingComplex2`, `ExactCochainComplexQ`, `DegreeOneResidualQ`, `Gamma2Functional::try_compute_exact_quotient`, `compare_guarded_diagnostics`) was confirmed to exist. The suite was **not executed** during this pass: sibling agents were active and CLAUDE.md forbids concurrent cargo runs (LLVM OOM). The "passes" word therefore rests on the prior pass's receipt, not on a fresh run.
* `omega_functional::gamma2::Complex2InputQ` distinguishes absent `Complex2` from a declared empty `C2`; `ExactGamma2Error::MissingComplex2` is the no-silent-zero gate.
* The suite also pins the guarded evaluator hierarchy: `Gamma2` improvement cannot compensate for worse `Phi1`, `Xi` improvement cannot compensate for worse `Gamma2`, and non-finite `Xi` is invalid.

4. Improver pass record (2026-06-09)

------------------------------------

* Part A: verified present ("Explicit exclusions" = non-claims box).
* Claims retyped: C2 strength tag; C5 STANDARD tag.
* Edits: [VERIFY record ids] ×2 resolved (20186523/20192297/20213064; ref [1] → 20359867); header/changelog version lineage reconciled (v1.1 header vs v2.0 changelog → v2.0.1 canonical).

5. GTOC / GTLA compliance pass record (2026-07-17)

--------------------------------------------------

Red note: `omega_engine/research/published/reviews/gtoc_gtla_red_012.md`. Version **not** bumped
(hygiene passes never bump). No claim status was upgraded; two were downgraded.

**Verified clean (checked, not assumed):** no withdrawn root-doctrine phrasing ("Difference
alone", "difference creates structure", "carrier-Structure before difference", ...); no
probability/entropy/Shannon semantics; no Hilbert/Born/qubit/entanglement overclaim; no GTLA
ownership error; no phantom Lean theorem; ledger axiom audit accurate; version stamp intact.

**P0 fixed (5):** added the GTOC/GTLA Compliance Note with concrete entries + GTOC obstruction
packet table + classification mapping (was absent); added the `Authority: none` firewall (was
absent — only two scoped denials existed); added the formalization-status firewall (was absent);
added the Import/Oracle boundary + §8.1 import fence pricing `Density`/`trace_norm`/`rho`/`xi`
(the grammar declared types the paper's own exclusion box disowns); scoped the Lean note from
"This finite replay is mechanized" to **[MECHANIZED-PARTIAL]** with an explicit mechanization-scope
block ($\Phi_1$/$R_{cl}$/$\mathbb{R}$-valued statements are **not** mechanized; artifacts are `Int`-valued).

**P1 fixed (4):** reordered §1 so the graded objects are constructed **before** the operator chain
that acts on them, and so $\sigma_2$ is introduced before use — the paper's own thesis is degree
discipline, and §1 previously displayed $C^0\to C^1\to C^2$ ahead of the definitions of
$C^0,C^1,C^2,d_0,d_1$ (also corrected $C^2(P)\to C^2(P,\sigma_2)$, since $C^2$ depends on the
declared attachment, not on $P$); retyped the $\varepsilon$-flag as a `[POLICY RULE]` routing
trigger rather than an inconsistency verdict; disclosed that the "QM-facing" bridge is
parameterized over opaque type variables and constructs/imports nothing quantum; added the
detector-adequacy warning naming the paper's own $C^1$-blind-spot.

**Also added:** Genesis-Bias Fence (No Prior State-Space) with the four priced stronger readings.

**P2 fixed (2):** disclosed the stale code pointers (`apply_d1` does not exist in
`omega_engine/crates/`; `apply_d0` lives only in `omega_symbol_game`; `solve_l1_hodge` exists only
as `solve_l1_hodge_primal_dual`; `cycle_space_projector.rs` is ambiguous) in §1 and the
Implementation Note; flagged the $\rho$ notation collision (density map vs. runtime environment)
at §10.3 rather than renaming, since the names are load-bearing in the cited code and Lean.

**P2 left open:** §7 box lists $\pi_Z$ among operators that "operate on distinct cochain degrees",
but $\pi_Z:C^1\to C^1$ is an endomorphism of one degree. Left as-is — a collectively-true reading
is available and repair would touch the paper's boxed final statement (minimal-patch rule).

<!-- claim-id-body-only-sync:begin -->

Body-only ID sync (packaging)
-----------------------------

**Nonclaims:** This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.

| ID | Claim | Type | Status |
|---|---|---|---|
| FOC-006 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |
| QM-032-C3 | Body claim-shaped ID registered for bijection packaging only; OPEN; not upgraded | OPEN | packaging |

<!-- claim-id-body-only-sync:end -->


## Executable Pytest Test Suite References

The computational claims and exact rational solvers are verified by the unit test suite under code/tests/:

- test_004_degree_wise_dsl.py::test_c01_graded_complex_nilpotency
- test_004_degree_wise_dsl.py::test_c02_degree_separation_c3
- test_004_degree_wise_dsl.py::test_c03_projection_invariants
- test_004_degree_wise_dsl.py::test_c04_rewrite_rules
- test_004_degree_wise_dsl.py::test_c05_coarse_graining_asymmetry
- test_004_degree_wise_dsl.py::test_c06_static_degree_typing
- test_004_degree_wise_dsl.py::test_c07_guarded_evaluator_hierarchy
- test_004_degree_wise_dsl.py::test_c08_worked_replay_c3
- test_004_degree_wise_dsl.py::test_c09_discrete_integer_shadow
- test_004_degree_wise_dsl.py::test_c10_local_green_not_acceptance
- test_004_degree_wise_dsl.py::test_c11_metadata_firewall
- test_004_degree_wise_dsl.py::test_c12_conformance_error_typing
- test_004_degree_wise_dsl.py::test_c13_composite_lggr_non_factorization
- test_004_degree_wise_dsl.py::test_c14_context_extension_stability
- test_004_degree_wise_dsl.py::test_c15_primitive_difference_witness
- test_004_degree_wise_dsl.py::test_c16_scope_fence_slots
- test_004_degree_wise_dsl.py::test_c17_authority_non_minting
- test_004_degree_wise_dsl.py::test_c18_detector_profile_adequacy
- test_004_degree_wise_dsl.py::test_c19_diagnostic_routing_rule
- test_004_degree_wise_dsl.py::test_c20_genesis_bias_fence
- test_004_degree_wise_dsl.py::test_c21_transient_pointers_disclosure
