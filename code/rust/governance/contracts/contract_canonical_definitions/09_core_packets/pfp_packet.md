packet_type: theory
authority_effect: None
carrier: finite Symbol Game tower {S(n)}, expressivity norm, Cech expressivity-obstruction o_n (C⁰)
primary_residual: historical Inc-4 representative norm, upper-bound, and tightness residual; runtime-discharged 2026-07-17 (no quotient-descent claim)
in_scope_repairs: Lean expressivityNorm definition, expressivity_norm_le_grammar_ceiling proof, grammar_ceiling_saturation Rust test (d₀)
deferred_residuals: residual-family consumer wiring, recursive tower refinement, lower-bound Lean shadow
seal_condition: shared GTOC/GTLA ExactRepair plus clean Lean build/axiom audit; authority requires packet-bound descent and decided IsAuth

Core Symbol Game — Inc 4 Theory Half (Obstruction Packet)
==========================================================

**Packet date:** 2026-06-20
**Runtime convergence update:** 2026-07-17
**App:** `pfp` (crate at `engine/crates/pfp`)
**Status carrier:** Increments 1–3 shipped (PRs #761, #769, #772, #776). Inc 4 = **theory half** of the computable expressivity-obstruction `o_n` introduced in Inc 3.
**Bundle status (A2):** this packet is **load-bearing**. The two-rail descent (Rust↔Lean numeric agreement on `‖o_n‖ ≤ S(n)`) is a single $d_0 \to d_1$ flow over one finite 2-window; no sibling context-exposure (DDA `C`) lemma-packets are split out. The historical labels Q¹-A/B/C are retained as packet identifiers, but the numeric norm and bound are proved only on a chosen finite representative. They do not define a function on the full cochain quotient.

Runtime convergence receipt (2026-07-17)
----------------------------------------

The historical Inc-4 residual is discharged on the production runtime path:

* `pfp::gtoc_adapter` validates the finite primitive-difference carrier `{Obstructed, Discharged}` and binds canonical carrier/evidence manifests.
* Both states reuse the existing nondegenerate exact carrier `d⁰ = [[1],[1]]` with `d¹ = [[0,0]]`; no app-local Phi1/Gamma2 or trichotomy algorithm was added.
* `evaluate_symbol_expressivity_repair` requires the DDA `FiniteLambdaStepCertificate`, replays the before and after states through `core_pipeline::gtoc_gtla`, and rejects any disagreement between the DDA and shared exact values.
* The verified transition is `StabilizedSurvivor (Phi1=1,Gamma2=0) -> ExactRepair (0,0)`. Both states produce `CheckedPacket`; neither produces authority implicitly.
* `certify_checked_symbol_expressivity` is the only Symbol authority wrapper. It delegates to the canonical checked-packet bridge and requires a packet-bound `DescentWitness` plus decided `IsAuth`.
* `SgOutcome` is explicitly projected to `SgWorkflowProjection`; names such as `Certified` and `Repaired` are product fidelity states, not a second obstruction classifier.
* `core_sweep_kernel::terminalize_row` remains a test-only product-lane compatibility receipt. Its `"Certificate"` string is not `CertifiedAuthority`.
* `lake build CoreSymbolGame QM007Transport` is green, and the Rust-driven `#print axioms` audit passes against the declared `SemiringTransportAxiomAudit` allow-list.

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The finite Symbol Game tower `{S(n)}` with the executable Čech expressivity-obstruction represented by a chosen finite discrepancy list `h_n`. The underlying cochain may be projected to `[h_n] ∈ H¹`, but the implemented `ℓ¹` norm is evaluated on the chosen representative and is not a function of the quotient class. The 2-window inspects, for each level `n`:

* **C⁰-window:** the patches (local namings) of an `ExpressivityProblem` at level `n`, exposed as the cochain `C⁰_n` over `Q = Rational64` consumed by `core_homology::cech_gate::run_cech_gate` (the finite Čech instance of CODA-FOC-CHECK-01).
* **C¹-window:** the pairwise overlaps with rational discrepancy `h_n`, paired with the *grammar-ceiling* index `S(n)` declared by the family driver (`pfp::family::SymbolPacketIterationStageDriver`, `StageConfig`).

The pinned binding is: domain carrier and candidate construction in `pfp`; finite primitive-difference validation, exact Phi1/Gamma2 replay, and the canonical trichotomy in `core_pipeline::gtoc_gtla`; checked evidence and authority gating in `core_certifiers`; and product packet realization in `core_representation`. `lp_to_routed_seed` remains the product adapter, while `gtoc_adapter` is the obstruction-runtime adapter.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Current code-side assignments at level `n`:

* The executable `ExpressivityProblem { patches, overlaps: Vec<Overlap{src,tgt,discrepancy}> }` and the verdict trichotomy `ExpressivityVerdict ∈ {Complete, Obstructed, Malformed}` (`crates/pfp/src/expressivity.rs`).
* The family drivers `LpDriver`, `CodeRewriteDriver`, `SymbolPacketIterationStageDriver` and the runtime `SymbolPacketIterationRunner` (`crates/pfp/src/family.rs`, `src/session.rs`).
* The `core_homology::cech_gate::run_cech_gate` finite Čech gate already mapping verdicts to `CechTerminal` (the inherited CODA-FOC-CHECK-01 carrier reused by `expressivity::Verdict`).
* On the Lean side, the cochain owner is `lean4/original_lean_20260809/finite_cochain_complex.lean` (`CoreCore.FiniteCochainComplex`, `cochainDifference`, `IsPhi1`, `cochainClassifier`). It is not a root of any Lake package here and its imports do not resolve in this tree; a 2026-09-29 scratch replay with those imports rewritten elaborates it. The two other owners this line used to name, `Cochain012.lean` (under `002_the_sentinel_boundary/CoreCosmology/FOC/`) and `ProjectionObstructionQuotient.lean` (under `003_quantum_foundations/qm_015_qm_typed_authority_boundary_suite/CoreCosmology/Primitives/`), exist nowhere in this repository or its history (checked 2026-09-29); no replacement is claimed for them. The deleted `Cochain`, `Cocycle`, and `Quotient` aliases are not evidence surfaces.
* **Historical baseline (2026-06-20):** the Lean grammar-ceiling statement and Rust saturation fixture were absent. Both artifacts now exist and are verified; this line records the trigger, not current state.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** The finite Čech differential still defines the underlying cochain quotient. The numeric norm rail is narrower: it permits representative-preserving refactors and the constant-potential action for which `d⁰ c = 0`. A general non-constant potential adds an element of `im d⁰` and can change `Σ |h_e|`; therefore `expressivityNorm` is not invariant under the full gauge relation.

This scope boundary is executable: the Rust S2 acceptance test witnesses constant-gauge invariance and a non-constant counterexample. No step in this packet may replace that finite representative statement with a quotient-invariance claim.

4. Emit $C^1$
-------------

**$C^1$ (historical Inc-4 trigger):** At packet issuance the repository lacked (1) a typed representative norm, (2) its level-`n` upper bound, and (3) a saturating Rust fixture. All three now exist. The repair is a finite representative-level result; it does not add the still-absent theorem that the norm descends through `C¹ / im d⁰`.

5. Declare ZeroRel
------------------

**ZeroRel (scope split):** The canonical cochain modules define zero-related cochains by a difference in `im d⁰`, and `ProjectionObstructionQuotient` owns that quotient. Separately, `expressivityNorm : List Int → Nat` is congruent only for transformations that leave the chosen discrepancy list's absolute values unchanged (in particular the constant-potential kernel action).

Consequently, two cochains can be ZeroRel-equivalent while carrying different representative `ℓ¹` masses. This packet must not cite the norm or grammar-ceiling bound as a well-defined observable on `Q¹` without an additional gauge selector or an independently proved congruence theorem.

6. Compute the finite representative residual
---------------------------------------------

The historical identifiers Q¹-A/B/C now have the following exact, narrower meanings:

* **Q¹-A (identifier only):** `CoreCosmology.SymbolGame.expressivityNorm : List Int → Nat`, the `ℓ¹` mass of a chosen canonical representative, implemented at `engine/lean4/008_engine_runtime/007_the_symbol_game/pfp/src/expressivity.lean`.
* **Q¹-B (identifier only):** `expressivity_norm_le_grammar_ceiling (n) (h)` proves `expressivityNorm h ≤ grammarCeiling n` from `h.length ≤ n` and `∀ x ∈ h, x.natAbs ≤ n - 1`; there is no quotient constructor in its statement.
* **Q¹-C:** the Rust saturation fixture exhibits a representative family attaining the same finite ceiling.

These results are useful capacity evidence. They are not cohomology-class invariants, do not prove that general gauge shifts preserve the norm, and do not license an authority or quotient-level physical claim.

7. Declare $d_1$
----------------

**$d_1$ (cross-rail closure):** Rust and Lean must agree on the numeric norm and `grammarCeiling` for the same chosen finite representative and level constraints. The separate cochain rail retains `d¹ ∘ d⁰ = 0`, but that closure theorem does not imply norm congruence under `im d⁰`.

The executable closure obligations are therefore the Rust/Lean representative agreement test, the grammar-ceiling saturation test, the Lean bound, and its axiom audit. No monotonicity under a general `d⁰` shift and no descent of `expressivityNorm` to `Q¹` is asserted.

8. Compute $\Gamma_2$
---------------------

**Current exact closure mass:** the production adapter uses the existing `d¹ = [[0,0]]` no-two-face carrier. Both before and after replay to `Gamma2 = 0`; the historical cross-window documentation residual is discharged by the Lean build, axiom audit, saturation fixture, and Rust/Lean agreement tests.

| State | $\Gamma_2$ | Executable witness |
|---|---:|---|
| Before Meta | 0 | `evaluate_symbol_expressivity(Obstructed)` through shared `Gamma2Functional` |
| After Meta | 0 | `evaluate_symbol_expressivity(Discharged)` through the same complex and residual binding |

The old aggregate `Gamma2 = 3` was a planning count over three absent artifacts, not a value computed by the exact runtime. It is retained only in repository history and must not be used as a current diagnostic.

9. Compute $\Phi_1$
-------------------

**Current exact quotient mass:** the adapter reuses the existing primal/dual certificates on the same nondegenerate `d0 = [[1],[1]]` carrier.

| State | $\Phi_1$ | Exact witness |
|---|---:|---|
| Before Meta | 1 | `omega=[1,0]`, `alpha=[0]`, residual `[1,0]`, dual `[1,-1]` |
| After Meta | 0 | `omega=[3,3]=d0*[3]`, residual `[0,0]`, zero dual |

`evaluate_symbol_expressivity_repair` also checks these values against the DDA `FiniteLambdaStepCertificate`. Any disagreement fails before a checked packet is returned. The values remain diagnostic and imply no authority.

10. Classify System State
-------------------------

Classification is no longer performed by packet prose or `SgOutcome`. The shared exact trichotomy returns:

| Domain state | Canonical `ObstructionStatus` | Authority effect |
|---|---|---|
| `Obstructed` | `StabilizedSurvivor` | None; the checked bridge refuses it |
| `Discharged` | `ExactRepair` | None until packet-bound descent and `IsAuth` are supplied |

Q1-A, Q1-B, and Q1-C are therefore closed Inc-4 evidence obligations. Product workflow outcomes remain separate projections and cannot override this classification.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift / Structural Extension):** The finite, non-destructive Meta is implemented and routed through the DDA crate:

* **$\Meta$ shape:** a `FaceLambda` from `core_discrete_deformation_algebra` whose source face is the current Inc 3 cochain complex `(C⁰_n →d⁰ C¹_n →d¹ C²_n)` and whose target face is the same complex augmented with the representative map `expressivityNorm : List Int → Nat` and its finite level bound. No map out of `Q¹_n` is added. The Meta does **not** alter `d⁰`, `d¹`, or the verdict trichotomy — it adds structure, it does not replace.
* **Obstruction witness:** the historical three-artifact trigger is represented at runtime by the exact before-state `Phi1=1`; the DDA capacity count `3` is not substituted for that exact value.
* **Preservation witness:** a `NonDestructiveExtensionCertificate` showing (i) every existing `ExpressivityVerdict` value is preserved (the new norm refines, it does not relabel), (ii) `d¹ ∘ d⁰ = 0` remains a Lean theorem after the extension (the FOC.Cochain012 proof is unchanged), and (iii) ENC-0891's firewall `faithful_comparison = false` is preserved, and (iv) the source explicitly refuses general quotient invariance for the representative norm.
* **Non-destruction check:** `evaluate_symbol_expressivity_repair` calls `FiniteLambdaStepCertificate::require_valid` and binds its diagnostics to the shared exact replay.
* **Runtime route:** `symbol_gtoc_exact_input -> core_pipeline::gtoc_gtla::evaluate_exact -> CheckedPacket`. The only authority route is `certify_checked_symbol_expressivity`, which delegates to `certify_checked_packet`.
* **Oracles required (A3): none.** Every transformation in this packet's $d_0 \to d_1$ flow is licensed *inside* the declared finite 2-window: `core_homology`'s finite Čech `d⁰`/`d¹` (mechanized in `FOC/Cochain012.lean`), the separately owned cochain quotient, the representative-level grammar calculation, and the finite-rational `Rational64` arithmetic. The quotient is context only; it is not used to infer norm invariance. No imported representation theorem (no Gleason, no Hilbert space, no Born ontology, no Mathlib-side classical analysis import) is invoked. The `#print axioms` audit is a Lean kernel verifier check — it is a DDA `T` (terminalization) step *over* the Lean kernel, not an A3 oracle. (Were an external representation theorem to be required in some future increment, it would be listed here and the corresponding sub-claim's terminal would become `OracleNeeded`; that is not the case for Inc 4.)
* **Product vocabulary:** `terminalize_row` returning `Decision::Certified` and `"Certificate"` is only a sweep-lane receipt. It is not interchangeable with `CertifiedAuthority`.
* **GTOC-3 sequencing:** the Lean, Rust, axiom, DDA, and shared-runtime gates now all pass; the lift trigger has been discharged without an implicit license or silent promotion.

The Meta is currently **Repaired** at the evidence/classification layer. This does not change `authority_effect: None` for the packet.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** the executable sequence has landed:

1. **$R$:** the underlying cochain quotient remains owned by `ProjectionObstructionQuotient`; the representative norm is deliberately not projected through it.
2. **$C$:** Rust `norm` and Lean `expressivityNorm` are present and agreement-tested.
3. **$\Meta$:** `FaceLambda`, NDEC, and the finite step certificate are implemented.
4. **$E$:** `expressivity_norm_le_grammar_ceiling` elaborates in `CoreSymbolGame` at representative scope.
5. **$C$:** `grammar_ceiling_saturation` exhibits the pinned family.
6. **$I$:** `gtoc_adapter` converts the domain states to validated shared exact inputs.
7. **$T$:** the Lean axiom audit and checked-packet construction pass.
8. **$D$:** DDA before/after diagnostics agree with shared `(Phi1,Gamma2)` values and descend from `(1,0)` to `(0,0)`.

Verification commands:

```
cargo test -j 1 -p pfp --test gtoc_adapter
cargo test -j 1 -p pfp --test grammar_ceiling_saturation
cargo test -j 1 -p pfp --test expressivity_axiom_audit -- --nocapture
cargo test -j 1 -p pfp
cd lean4 && lake build CoreSymbolGame QM007Transport
```

13. Terminal Status
-------------------

| Defect | Current evidence state | Receipt |
|---|---|---|
| Q1-A (`expressivityNorm`, representative scope) | Repaired | `lake build CoreSymbolGame`; Rust/Lean agreement suite |
| Q1-B (upper-bound theorem) | Repaired | Rust-driven `#print axioms` allow-list audit |
| Q1-C (saturation fixture) | Repaired | `grammar_ceiling_saturation` |
| Runtime composition | ExactRepair | `gtoc_adapter` shared replay `(1,0) -> (0,0)` |

The release gates for the Inc-4 upper bound and sharpness evidence are closed. No current Q1-A/B/C residual is deferred.

**Authority boundary:**

* The packet remains `authority_effect: None`.
* The post-repair `CheckedPacket` is eligible for, but does not itself create, `CertifiedAuthority`.
* A packet-bound `DescentWitness` and decided seven-guard `IsAuth` are mandatory at `certify_checked_symbol_expressivity`.
* The negative control proves `StabilizedSurvivor` is refused by that bridge.
* The positive bridge test proves the route is reachable for a correctly bound exact fixture; it is not a standing authority grant for arbitrary Symbol outputs.
* The sweep-lane `Decision::Certified` / `"Certificate"` receipt remains product-local and has no authority effect.

Future recursive-tower refinement, lower-bound formalization, and residual-family consumer wiring belong to successor work; they do not reopen this finite Inc-4 repair.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `pfp::gtoc_adapter::evaluate_symbol_expressivity` constructs `GtocExactInput` and calls `core_pipeline::gtoc_gtla::evaluate_exact`; focused adapter and rewrite tests are present. Existing Lean modules bound the expressivity ceiling but do not promote the runtime lane. Production convergence and separate promotion remain owned by `S16-005`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census records the current packet hash and source manifest.
