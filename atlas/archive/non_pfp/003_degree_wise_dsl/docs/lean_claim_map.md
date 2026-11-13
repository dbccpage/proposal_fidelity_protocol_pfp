# Lean Claim Map: Paper 009 — Degree-Wise Obstruction Calculus and Symbolic DSL

**Paper Target:** `001_finite_obstruction_calculus/004_degree_wise_dsl` (FOC-006)
**Version:** v2.0.8
**Mechanization Level:** Explicitly bounded partial mechanization (`[MECHANIZED-PARTIAL]`). Formal Lean proofs cover discrete integer-valued cochains and declared contracts in `PaperFOC006`, including the integer $C_3$ distance in `PaperFOC006.c3_degree_separation_instance`. Real-valued $\ell^1$ minimization and general-$k$ theorems are outside this deposit.

---

## Claim Mechanization Status

| Claim ID | Claim Description | Declared Status | Lean 4 Status | Lake Module / Target | Notes |
|---|---|---|---|---|---|
| `C1` | Graded complex $C^0 \to C^1 \to C^2$, $d_1 d_0 = 0$ | `[STANDARD / DEFINITION]` | `MECHANIZED` | `PaperFOC006.c3_d1_d0_zero` | Mechanized on discrete $C_3$ instance. |
| `C2` | Degree Separation Theorem | `[PROVEN (integer C3) / SCHEMATIC (k)]` | `MECHANIZED` | `PaperFOC006.c3_degree_separation_instance` | Integer $C_3$ distance and readout. General $k$ and real minimization stay outside. |
| `C3` | Declared-projection $\pi_Z$ invariants | `[DEFINITION]` | `N/A` | None | Specification in prose. |
| `C4` | DSL Rewrite Rules | `[PROVEN / CONTRACT]` | `MECHANIZED` | `PaperFOC006.declaredProjection_*` | Verified as declared projection contract. |
| `C5` | Coarse-graining information-loss asymmetry | `[STANDARD / PROVEN]` | `PROSE` | None | Triangle inequality in prose. |
| `C6` | DSL Grammar and Static Typing | `[SPECIFICATION]` | `N/A` | None | Language specification in prose. |
| `C7` | Guarded descent law | `[OPERATIONAL RULE]` | `N/A` | None | Policy / operational rule. |
| `C8` | Worked Replay on $C_3$ | `[WORKED EXAMPLE]` | `MECHANIZED-PARTIAL` | `PaperFOC006.c3_degree_separation_instance` | Integer $C_3$ minimum mechanized. Real potentials and a real ratio stay outside. |
| `C9` | Lean finite support artifact | `[MECHANIZED-PARTIAL]` | `MECHANIZED-PARTIAL` | `PaperFOC006.DegreeSeparation` | Integer-valued cochains, including the $C_3$ distance. Real $R_{cl}$ stays outside. |
| `C10` | Diagnostic constructibility $\not\implies$ acceptance | `[PROVEN / MECHANIZED]` | `MECHANIZED` | `PaperFOC006.diagnostic_local_green...` | Local/global LGGR separation witness. |
| `C11` | Context metadata does not change the fingerprint or the gated readout | `[PROVEN for context replacement]` | `MECHANIZED` | `PaperFOC006.contextual_local_fingerprint_ignores_context_replacement` | `QM.PaperFOC006DegreeBridge` is not in this package. Q admission is not a theorem here. |
| `C12` | Rust DSL typing/safety conformance | `[MECHANICAL / DISCHARGED]` | `N/A` (Rust) | `omega_functional` | Rust test suite, not Lean theorem. |
| `C13` | Composite local fingerprint / global gate obstruction | `[PROVEN / MECHANIZED]` | `MECHANIZED` | `PaperFOC006.degreeDsl_local_green...` | Composite LGGR non-factorization. |
| `C14` | Context extension does not repair boundary | `[PROVEN / MECHANIZED]` | `MECHANIZED` | `PaperFOC006.contextual_local_green...` | Context-stability theorem. |
| `C15` | General PrimitiveDifference context-fingerprint theorem | `[PROVEN / MECHANIZED]` | `MECHANIZED` | `PaperFOC006.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness` | Elaborated in this package. The `OmegaCore` name is not a module here. |
| `C16` | `Density`, `trace_norm`, `rho`, `xi` DSL slots | `[SCOPE FENCE]` | `N/A` | None | Import scope fence; not constructed here. |
| `C17` | Non-minting of authority | `[POLICY RULE]` | `N/A` | None | Policy boundary; AuthorityEffect None. |
| `C18` | Adequacy of detector profile | `[OPEN]` | `N/A` | None | Open obligation PL-012-2. |
| `C19` | Diagnostic inspection routing rule | `[POLICY RULE]` | `N/A` | None | Diagnostic routing flag, not inconsistency proof. |
| `C20` | Genesis-Bias Fence (No Prior State-Space) | `[SCOPE FENCE]` | `N/A` | None | Admitted antecedent fence. |
| `C21` | Implementation code pointers | `[CONTRACT]` | `N/A` | None | Historical/transient implementation references. |

---

## Falsifier Check: `LEAN_TOY`-as-`MECHANIZED`

- **Mechanized claims count:** 8 (C1, C2, C4, C10, C11, C13, C14, C15)
- **`[MECHANIZED-PARTIAL]` claims count:** 2 (C8, C9)
- **Prose / Specification / Scope Fence claims count:** 12
- **Result:** PASS. The `[MECHANIZED-PARTIAL]` status is explicitly fenced in the manuscript, ledger, and this map; integer cochains are honestly reported as shadows of the real calculus.
