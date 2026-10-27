packet_type: implementation
authority_effect: None
carrier: dimension-6 MUB wall problem, cyclotomic-extension field K, PSD certificate Q (C⁰)
primary_residual: missing Lean 4 shadow for d=6 MUB wall upper bound (Q¹)
in_scope_repairs: Lean upper-bound shadow statement, import wiring, print axioms audit hook (d₀)
deferred_residuals: axiom-free PSD proof (core_mub_axiom_free_psd_packet.md), symbol game recording, lower-bound Lean attainment shadow (core_mub_attainment_packet.md)
seal_condition: lake build PaperER006 green and print axioms golden comparison success

core_mub: d=6 Wall Upper-Bound Lean Shadow (Obstruction Packet)
================================================================

**App:** `engine/crates/mub`
**Date:** 2026-06-20
**Bundle status (A2):** load-bearing, no sibling lemma-packets. This packet carries the load-bearing Rust-to-Lean descent for the d=6 MUB wall upper bound. The three explicitly deferred successor packets named in section 13 (`core_mub_axiom_free_psd_packet.md`, `core_mub_symbol_game_packet.md`, `core_mub_attainment_packet.md`) are out-of-window successors, not sibling context-exposure (DDA C) lemma-packets in the current bundle.
**Driving obstruction:** The d=6 MUB wall theorem `max_{|v|=1} f(v) = W = (88 + 3*sqrt6)/100` is proved on the Rust rail (lower bound by `mub::wall::attainment`, upper bound by `mub::wall::certificate` over the loaded PSD certificate `Q`), but the upper-bound half has no Lean 4 shadow. Per the GTOC firewall, markdown and Rust tests do not mint authority; the Lean target is the descent that licenses calling the upper bound a Lean upper-bound shadow rather than a verified Rust computation.

**Defects in this window (per A1).** Four distinct defects ride this single 2-window; sections 8 (Gamma_2), 9 (Phi_1), 10 (Classification), and 13 (Terminal / Seal) are reported as per-defect tables below. The defect IDs used throughout are:

| ID | Defect (from section 4) |
|----|--------------------------|
| D1 | No Lean statement of the upper bound (`PaperER006.MUB6Wall` does not exist). |
| D2 | PSD-certificate-as-data is unbudgeted (axiom-free vs typed-axiom-budget branch). |
| D3 | No `#print axioms mub6_wall_upper` audit hook / golden. |
| D4 | No `PaperER006.lean` wiring of `PaperER006.MUB6Wall`. |

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The dimension-6 MUB wall problem over the cyclotomic-extension field `K = Q(zeta_24)(sqrt5)` (degree 16), with the canonical triple `{Z2xZ3, X2xQ0, Y2xQ1}` fixed and the global PSD certificate `Q` (size `N_LIFT = 441`, see `engine/crates/mub/src/wall/certificate.rs`) loaded as an artifact. The 2-window inspects the local cochain primitive differences between (a) the Rust upper-bound certificate (`mub::wall::certificate`) and (b) a Lean 4 statement+proof of the same upper bound, then the `C^0 -> C^1 -> C^2` closure between that Lean statement and the rest of the descended math spine (`PaperER006`, `PrimitiveAxiomatics`, `MUB`).

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Existing assignments on the Rust rail are concrete:

* `mub::wall::attainment::*` — exact proof that `f(v*) = W` over `K`, giving `max f >= W` (the lower-bound half).
* `mub::wall::certificate::{N_LIFT, build_triple, ...}` — independent verifier of `max f <= W` via the bidegree-(p,p) form algebra against the loaded PSD certificate `Q`.
* `mub::exact::cyclotomic` and `mub::exact::f4` — exact algebraic carriers `Cyc`, `L1`, `Cf4`, `F4`.
* `mub::apache_verifier` / `mub::artifact_manifest` — gated loader for the upstream Apache-2.0 `Q` artifact (gitignored, read from `research/published` per the operator ruling).

On the Lean rail, the existing assignments under `engine/lean4/`:

* `012_mutually_unbiased_bases/MUB.lean` and its `MUB/` library (Hilbert MUB family, basis-extension obstructions, terminalizer contracts, etc.) — descended math spine that the upper-bound theorem will sit on.
* `PaperER006.lean` and `PaperER006/PaperER006b.lean` — the existing Paper 040 / 040b chapter (tower zeta), the natural neighbour for a `MUB6Wall` module.
* No `PaperER006.MUB6Wall` target exists yet; no Lean statement of the form `max f <= W` exists on the Lean rail.

These are the cochains in `core_homology::CochainPrimitiveDifference` terms: each is a primitive difference row carrying its source (`mub` Rust crate vs `lean4/MUB`).

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** The permitted primitive operator at this stage is the Rust-to-Lean cochain transport that introduces a Lean 4 statement+proof shadow without changing the Rust rail's external invariants. Concretely:

* Add a new Lean library target `PaperER006.MUB6Wall` (file `engine/lean4/008_engine_runtime/PaperER006/MUB6Wall.lean`, plus updates to `engine/lean4/008_engine_runtime/PaperER006.lean` and `engine/lean4/lakefile.lean` if needed) declaring the wall constant `W = (88 + 3*sqrt6)/100` and the upper-bound theorem `mub6_wall_upper : max_{v in S^{n-1}} f v <= W` against the same canonical triple.
* Encode the bidegree-(p,p) form algebra and the loaded PSD certificate `Q` as a Lean data structure with an explicit axiom budget when the artifact-load step is irreducible.
* Mirror — not re-derive — the Rust witnesses; primitive-difference rows are emitted whenever a Lean step diverges from its Rust counterpart.

Formally, `d_0` is the lambda generator (in the DDA sense — operators are lambdas) that maps Rust assignments to Lean assignments preserving the underlying field-arithmetic invariants; see `core_homology::CochainComplex.d0`.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** The defects against the canonical descent are:

1. **No Lean statement of the upper bound.** `PaperER006.MUB6Wall` does not exist. The Rust function `mub::wall::certificate` returns success on the loaded `Q` but emits no Lean obligation, so the theorem is currently Rust-only.
2. **PSD-certificate-as-data is unbudgeted.** The Lean shadow either (a) mechanizes the PSD check axiom-free over the cyclotomic field `K` (the goal) or (b) carries the `Q` matrix as a typed axiom with an explicit `axioms` budget; neither has been authored. Without a budget the descent is silent on what authority Lean is taking on faith.
3. **No `#print axioms` audit hook for `mub6_wall_upper`.** Even if the file compiles, there is no acceptance test that pins the axiom list and fails on drift.
4. **No PaperER006 wiring.** `PaperER006.lean` does not yet import `PaperER006.MUB6Wall`, so the chapter view does not see the upper bound.

These are emitted as `core_homology::CochainPrimitiveDifference` rows under `core_homology::CochainComplex.d1` of the Rust assignments. The Symbol Game adapter (`pfp`) records each row as a candidate `lp<...>` term.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Differences that are zero modulo gauge:

* Whitespace / module-name aliasing inside `PaperER006.MUB6Wall` (e.g. swapping `wall_constant` for `W`).
* Rewriting `(88 + 3 * Real.sqrt 6) / 100` as `(1 / 100) * (88 + 3 * Real.sqrt 6)` etc.
* Reordering imports inside the Lean file.
* Reformatting Rust comments or Cargo metadata in the `mub` crate.

These collapse to interval / algebraic zero in the `core_homology::QuotientSpace` projection and never survive to `Q^1`.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** Modulo ZeroRel, the surviving residuals are exactly:

* **Primary residual.** A Lean target `PaperER006.MUB6Wall` that mechanizes the upper-bound certificate **either** axiom-free **or** with a typed, listed axiom budget (the PSD-as-data axioms for the loaded `Q`), and is wired into `PaperER006.lean` so that `lake build PaperER006` exercises it.
* **Secondary residual.** A `#print axioms mub6_wall_upper` acceptance check and a `cargo test -j 1 -p mub --test wall_lean_axiom_budget` (or `pytest`-driven equivalent) that diffs the printed axiom list against a checked-in golden, blocking drift.

`Q^1` is computed by the projection `core_homology::QuotientSpace` over the rows emitted in section 4. Verification of `Phi_1 = 0` after descent is the responsibility of `core_functional::VerifiedExactPhi1`.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** The closure operator is the triple-overlap check across the three carriers that must agree on the upper bound:

* The Rust certificate verifier (`mub::wall::certificate`),
* The Lean theorem (`PaperER006.MUB6Wall.mub6_wall_upper`),
* The descended math spine (`PrimitiveAxiomatics` plus the `MUB` library at `lean4/012_mutually_unbiased_bases/`, especially `HilbertMubFamily.lean` and `BasisExtensionObstruction.lean`).

`d_1` requires that any change to the Rust certificate, the Lean theorem statement, or the supporting spine is reflected coherently in the other two; otherwise a cocycle defect is emitted under `core_homology::CochainComplex.d1`. The matching observer is `core_functional::Observer` with the GTOC two-window context.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass) — per defect (A1):** `Gamma_2` is computed by `core_functional::ExactGamma2Result` on the closure cochain produced under `d_1`, evaluated per defect over the (Rust, Lean, spine) triple-overlap of section 7.

| Defect | $\Gamma_2$ | Witness |
|--------|------------|---------|
| D1 | $> 0$ | Rust upper-bound theorem has no Lean shadow at all on the (Rust, Lean, spine) overlap; the Lean leg of the triple is empty so the cocycle cannot close. |
| D2 | $> 0$ | The loaded PSD certificate `Q` is referenced on the Rust rail (`mub::wall::certificate`) and only via `mub::apache_verifier` / `mub::artifact_manifest` for the gitignored copy; it is not referenced on the Lean rail at all, so the Lean-side authority over `Q` is undefined — the closure cochain across the rails carries an unbudgeted import edge. |
| D3 | $> 0$ | No `#print axioms mub6_wall_upper` acceptance gate exists; any future Lean drift in `mub6_wall_upper`'s axiom set would not be caught by `d_1`, so the closure is silent on regression. |
| D4 | $> 0$ | `lake build PaperER006` does not import `PaperER006.MUB6Wall`; the `PaperER006.lean` chapter view does not see the upper bound, so a regression on the new module would not propagate to the chapter-level closure check. |

Sprint S-core_mub-001 drives D1, D3, and D4 to $\Gamma_2 = 0$ via the Meta in section 11; the artifact gating for D2 is handled by an explicit typed axiom budget rather than a hidden import (see also section 11, "Oracles required").

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass) — per defect (A1):** `Phi_1` is measured by `core_functional::VerifiedExactPhi1` against the `Q^1` rows of section 6, evaluated per defect.

| Defect | $\Phi_1$ (current) | Witness |
|--------|---------------------|---------|
| D1 | $> 0$ | The missing Lean target `PaperER006.MUB6Wall` and the missing statement `mub6_wall_upper` are gauge-irreducible against ZeroRel of section 5 (whitespace/module-name aliasing collapses to zero; an absent theorem does not). |
| D2 | $> 0$ | The axiom-budget branch (axiom-free vs typed-axiom-budget) is unauthored: there is neither a Mathlib-PSD mechanization nor a typed `axiom Q_is_psd_certificate` with a checked-in golden axiom list. Neither outcome is in `im(d_0)`. |
| D3 | $> 0$ | No `#print axioms` acceptance test exists; the gauge-irreducible residual is the missing test + golden file. |
| D4 | $> 0$ | No `import PaperER006.MUB6Wall` in `PaperER006.lean`; the gauge-irreducible residual is the missing import edge. |

**Target after sprint S-core_mub-001.** Drive each row to $\Phi_1 = 0$, gated by the seal condition in section 13 (per A4). The acceptance test in S-core_mub-001 is the gate that licenses moving on; markdown does not.

10. Classify System State — per defect (A1)
-------------------------------------------

| Defect | Class |
|--------|-------|
| D1 | ActiveClosureFailure -> LiftNeeded. The closure across the (Rust, Lean, spine) triple is broken because the Lean leg is empty. The Meta in section 11 (`PaperER006.MUB6Wall.mub6_wall_upper`) is the licensed lift; on landing, the defect re-classifies to ExactRepair. |
| D2 | Two sub-paths conditioned on the seal in section 13 (per A4). (a) Axiom-free branch -> ExactRepair (Phi_1 = 0, no oracle). (b) Typed-axiom-budget branch -> OracleNeeded (an imported representation of `Q.PosSemidef` per A3; see section 11 "Oracles required"). Choice between (a) and (b) is recorded on the Rust rail as a `CochainPrimitiveDifference` row, never minted by markdown. |
| D3 | ActiveClosureFailure -> ExactRepair after a `cargo test`-driven `#print axioms mub6_wall_upper` golden gate lands. Local repair via a checked-in golden file; no lift required. |
| D4 | ActiveClosureFailure -> ExactRepair after `import PaperER006.MUB6Wall` is added to `PaperER006.lean`. Local repair via a one-line import edit; no lift required. |

The Rust rail proves the theorem; the Lean rail does not even state it. The repair path for D1 is the Meta in section 11. For D2, if the PSD-check encoding cannot be discharged axiom-free against the standard library available to `lean4/012_mutually_unbiased_bases/MUB`, the residual is moved to a typed-axiom-budget plus an explicit A3 oracle declaration in section 11 — the budget IS the preservation witness for that branch.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift / Structural Extension):** Propose a Lean-shadow Meta that descends the Rust upper-bound certificate into a typed Lean theorem with an auditable axiom budget. Concretely:

* **Meta carrier (lambda).** A `FaceLambda` (see `core_discrete_deformation_algebra`, `pub struct FaceLambda`) instance whose source face is the Rust assignment `mub::wall::certificate::*` and whose target face is the Lean assignment `PaperER006.MUB6Wall.mub6_wall_upper`. The face lambda's data is the cyclotomic-field bridge (Rust `Cyc`/`L1`/`Cf4` to Lean's `Mathlib.NumberTheory.Cyclotomic` / `Polynomial.IsRoot` setup) and the bidegree-(p,p) form algebra over that bridge. Construction is via `FaceLambda::new(face, capacity)`; the FaceLambda is then validated by composing with the two certificates below.
* **Non-destruction certificate.** A `NonDestructiveExtensionCertificate` (`core_discrete_deformation_algebra`) constructed via `NonDestructiveExtensionCertificate::new(preserves_old_vertices: true, preserves_old_edges: true, records_tradeoff: true)` and then `require_non_destructive()`. The three booleans MUST be witnessed by a runnable test in the SAME PR that introduces the Meta: (a) `preserves_old_vertices` is witnessed by running `lake build` of every prior `PaperER006` / `PrimitiveAxiomatics` / `MUB` target named in the lakefile and asserting exit 0; (b) `preserves_old_edges` is witnessed by checking that no existing Lean symbol in those targets was redefined (grep for the symbols introduced by the new file against the prior namespace); (c) `records_tradeoff` is witnessed by emitting a Rust-rail `CochainPrimitiveDifference` row recording the axiom-budget branch taken (axiom-free vs typed-axiom). GTOC-3: the certificate MUST travel with the Meta in the same PR — a Meta that lands without all three witnesses on the Rust rail is unlicensed.
* **Finite-step certificate.** A `FiniteLambdaStepCertificate` bounding the Meta's elaboration: the file resolves in a finite number of `d_0` / `d_1` steps (one cochain map for the wall constant; one for the bidegree-(p,p) form; one for the PSD positivity check or its axiomatization; one for the triple-overlap with `PaperER006.lean`). Constructed via `FiniteLambdaStepCertificate::new(before, after, extension)` where `before` is the `FiniteDiagnostic{phi1, gamma2}` measured before the Meta lands and `after` is the diagnostic measured after; `require_valid()` enforces (i) before has obstruction (`phi1 > 0` or `gamma2 > 0`), (ii) after is resolved (`phi1 == 0 && gamma2 == 0`), and (iii) the extension is non-destructive (all three NDE booleans true). The certificate is constructed and validated in the SAME PR that lands the Meta.
* **Preservation witness.** $\Meta$ preserves the upper-bound semantics: every model of the Rust certificate is a model of the Lean theorem and vice versa, modulo the axiom budget. The witness is the matching `f` definitions on both rails over `K = Q(zeta_24)(sqrt5)`; mechanically, a Rust-side test asserts that the Lean-rail wall constant value `(88 + 3 * Real.sqrt 6) / 100` is byte-equal (over the documented printed form) to the Rust constant computed by `mub::wall::certificate`. If the axiom-budget branch is taken, the preservation witness also includes a Rust-side check that the axiom's documented PSD-shape statement matches the shape `mub::wall::certificate` actually verifies over `K`.
* **Obstruction witness.** Listed in section 4; primary obstruction is the missing Lean target. The Rust-side enumerator `emit_primitive_differences()` (S2) is the load-bearing witness: it MUST emit at least one row of kind "missing-Lean-statement" before the Meta lands, and the same enumerator MUST return zero such rows after the Meta lands (verified in the same PR as the Meta). A scaffold story that introduces a temporary `sorry` MUST emit a paired `sorry_pending` obstruction row in the same PR — a sorry that lands without a paired Rust-rail obstruction row is itself an unlicensed Meta.
* **Terminalizer route.** $\Meta$ does NOT mint terminal authority. The terminal seal is reserved for `core_sweep_kernel::terminalize_row` (`fn terminalize_row(row: &serde_yaml::Value, author_model: &str, gate_model: &str) -> TerminalRecord`, success variant `Decision::Certified`, `host_terminal_status == "Certificate"`) or `core_certifiers::certify_checked_packet`, called by the sprint's CI gate once `lake build PaperER006` is green and the `#print axioms` golden matches. EPK diagnostics (`core_epk::EpkResidualLedger`) may attach diagnostic-only annotations but mint no authority; per the firewall contract, `EpkResidualLedger::authority_effect()` ALWAYS returns `AuthorityEffect::None` and `as_outcome()` ALWAYS returns `Outcome::Refused(RefusalSource::Residual)`. EPK does not classify rows as "Repaired"; the terminal-status vocabulary on the Rust sweep rail is `{Certificate, OracleNeeded, Refusal}` and the `Decision` enum is `{Certified, Killed, Obligation, DeferredToValidator, RefusedHostAuthority, NotGated}` — there is no `Decision::Repaired`. LLMs may propose `lp<...>` candidate Meta shapes via `pfp` but are not judges; the `lp<...>` recording itself is **deferred to a successor packet** (see §13) and is not load-bearing for this sprint's closure.

Trigger: active closure failure $\Gamma_2 > 0$ on the Rust-Lean overlap. Licensed by the published-paper descent policy (Paper 040 is already in the spine; mechanizing its central numerical theorem is a sanctioned extension).

**Oracles required (A3 — imported witnesses, not DDA operations).** A licensing transformation that comes from OUTSIDE the declared finite 2-window is an import/oracle and is recorded here, NOT under section 12 as a DDA letter.

* **Axiom-free branch (D2.a).** Oracles required: **none.** The PSD positivity step is mechanized inside the 2-window via `Mathlib.LinearAlgebra.Matrix.PosDef` over the cyclotomic field `K`. D2 terminalizes to ExactRepair via the seal in section 13. Section 12's DDA log records only in-window letters.
* **Typed-axiom-budget branch (D2.b).** Oracles required: ONE imported representation theorem, recorded as `axiom Q_is_psd_certificate : Q.PosSemidef` in `PaperER006.MUB6Wall`, with the bidegree-(p,p) form algebra positivity over the loaded `Q` of size `N_LIFT = 441` as its statement. The oracle's documented shape MUST match the shape `mub::wall::certificate` actually verifies over `K`. Under this branch, the D2 sub-claim's terminal is `OracleNeeded` (per A3) — NOT `Certificate` and NOT `ExactRepair` — and the corresponding seal in section 13 is the Lean `#print axioms` golden listing this axiom. The axiom is an imported witness in this packet; its discharge is the deferred successor packet `core_mub_axiom_free_psd_packet.md` (section 13). The oracle's evaluation is NOT logged in section 12 as a DDA letter.

  > [!IMPORTANT]
  > The typed-axiom branch proves the Lean wrapper conditional on imported PSD certificate data. It does not prove the PSD certificate internally.

All other sub-claims (D1, D3, D4 and the D2.a branch) require zero oracles.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** Per A5, every step below is one of the canonical letters `{E, R, C, I, Meta/Lambda, D, M, T}`. No new letters are introduced. The PSD-as-import step under D2.b is NOT in this log — per A3 it is an oracle in section 11, not a DDA operation.

| # | DDA op (A5) | Action |
|---|-------------|--------|
| 1 | `I` (Integration / DDA-log append) | Run `cargo test -j 1 -p mub --test wall_upper_bound` (or whichever test exercises `mub::wall::certificate` end-to-end) to anchor the source assignment, then emit `core_homology::CochainPrimitiveDifference` rows for each defect D1–D4 from section 4 into the DDA log. (Previously labeled `R`; corrected — emission to the log is `I`, not residual projection.) |
| 2 | `Meta` / `Lambda` (Lift / structural extension) | Author `engine/lean4/008_engine_runtime/PaperER006/MUB6Wall.lean`: declare `W`, define the canonical triple, declare the bidegree-(p,p) form, state `mub6_wall_upper`, and prove it via the in-window route (Mathlib `PosDef` mechanization, D2.a branch). The D2.b branch uses an A3 oracle declared in section 11; the oracle itself is NOT a DDA step. This step targets defect D1 (and D2 under the D2.a branch). |
| 3 | `D` (Descent / re-index) | Wire `import PaperER006.MUB6Wall` into `engine/lean4/008_engine_runtime/PaperER006.lean` so the chapter view re-indexes onto the new module; this discharges defect D4. |
| 4 | `E` (Exact repair) | Land the `#print axioms mub6_wall_upper` acceptance test + checked-in golden file (e.g. `engine/lean4/008_engine_runtime/PaperER006/AxiomGolden.txt`) and the `cargo test -j 1 -p mub --test wall_lean_axiom_budget` (or `lake env`-driven equivalent) that diffs the printed axioms against the golden. This is a local repair against ZeroRel for defect D3 — no lift required. |
| 5 | `R` (Residual projection) | Run `core_homology::QuotientSpace` over the resulting cochain; confirm `Q^1` is empty on the Rust-Lean overlap (mod ZeroRel of section 5). (Previously labeled `R'`; restored to canonical `R`.) |
| 6 | `C` (Context exposure) | Run `core_functional::Observer` on the closure cochain; confirm `core_functional::ExactGamma2Result` shows `Gamma_2 = 0` across the (Rust, Lean, spine) triple, exposing whether any contextuality between rails survives. |
| 7 | `R` (Residual projection) | Run `core_functional::VerifiedExactPhi1` against the per-defect `Q^1` rows; require `Phi_1 = 0` per the per-defect table in section 9. (Previously labeled `V`; `V` is not in the A5 alphabet — replaced with `R` because this is the final residual-projection measurement.) |
| 8 | `T` (Terminalization) | Only after (7), call `core_sweep_kernel::terminalize_row` or `core_certifiers::certify_checked_packet` for the row, per the seal condition in section 13. This is the sole authority-minting step in the pipeline. The packet itself never mints authority. |

DDA crates bound: `core_homology` (carriers and cochains), `core_functional` (`VerifiedExactPhi1`, `ExactGamma2Result`, `Observer`), `core_discrete_deformation_algebra` (`FaceLambda`, `NonDestructiveExtensionCertificate`, `FiniteLambdaStepCertificate`), `pfp` (candidate `lp<...>` generation, deferred per section 13), `core_sweep_kernel` / `core_certifiers` (terminal seal), `core_epk` (diagnostic-only).

13. Terminal Status — per defect (A1) with Current / Target / Seal Condition (A4)
---------------------------------------------------------------------------------

Per A4, every row separates Current terminal, Target terminal, and the concrete Seal Condition that flips Current to Target. Per the firewall, every Seal Condition names ONE of the two authority-minting paths: `core_sweep_kernel::terminalize_row` returning `Decision::Certified` on a named row, or `core_certifiers::certify_checked_packet` (7 IsAuth guards), composed where needed with `lake build <target>` clean and `#print axioms` empty on a named Lean theorem. Markdown DOES NOT mint authority.

| Defect | Current | Target | Seal Condition |
|--------|---------|--------|----------------|
| D1 | LiftNeeded | Repaired | `cd engine/lean4 && lake build PaperER006` exits 0 with `PaperER006.MUB6Wall.mub6_wall_upper` resolved; AND `core_sweep_kernel::terminalize_row` returns `Decision::Certified` (`host_terminal_status == "Certificate"`) for the `core_mub:d1:mub6_wall_upper_lean_shadow` row in the sprint S-core_mub-001 CI gate. |
| D2.a (axiom-free branch) | LiftNeeded | ExactRepair | `lake build PaperER006` exits 0 AND `#print axioms mub6_wall_upper` (executed via `lake env lean` against `engine/lean4/008_engine_runtime/PaperER006/MUB6Wall.lean`) lists ONLY Lean/Mathlib standard axioms (no `Q_is_psd_certificate`, no `sorry`, no project-local axiom); AND `core_certifiers::certify_checked_packet` returns success (all 7 IsAuth guards) on the `core_mub:d2a:psd_axiom_free` row. |
| D2.b (typed-axiom-budget branch) | LiftNeeded | OracleNeeded | `lake build PaperER006` exits 0 AND `#print axioms mub6_wall_upper` matches the checked-in golden file `engine/lean4/008_engine_runtime/PaperER006/AxiomGolden.txt` listing EXACTLY the imported axiom `Q_is_psd_certificate` (plus standard axioms); AND `core_sweep_kernel::terminalize_row` returns `Decision::Certified` with `host_terminal_status == "OracleNeeded"` on the `core_mub:d2b:psd_imported_axiom` row, recording the oracle (per A3 — the PSD positivity is an imported representation theorem; see section 11 "Oracles required"). The terminal is sealed as OracleNeeded, not ExactRepair; the axiom-free discharge is the successor packet below. |
| D3 | ActiveClosureFailure | ExactRepair | `cargo test -j 1 -p mub --test wall_lean_axiom_budget` exits 0 (the test invokes `lake env lean` to print axioms and diffs against the checked-in golden); AND `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the `core_mub:d3:axiom_print_golden` row. |
| D4 | ActiveClosureFailure | ExactRepair | `cd engine/lean4 && lake build PaperER006` exits 0 with `PaperER006.lean` importing `PaperER006.MUB6Wall` (so the chapter view exercises the new theorem); AND `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the `core_mub:d4:paper040_wiring` row. |

**Firewall reminder.** No EPK annotation, no LLM judgment, no markdown line below this table can flip a Current to a Target. Only `core_sweep_kernel::terminalize_row` and `core_certifiers::certify_checked_packet` mint authority; this packet documents the gate, it does not pass it.

**Deferred residuals (explicit, no silent backlog).** Per the GTOC firewall and the no-silent-residual rule:

* `defer: axiom-free-PSD -> successor packet core_mub_axiom_free_psd_packet.md` — if sprint S-core_mub-001 takes the typed-axiom-budget branch D2.b in section 11 (declaring `axiom Q_is_psd_certificate : Q.PosSemidef`), the axiom-free mechanization of the PSD check over `K` is moved to a successor packet (proposed name `core_mub_axiom_free_psd_packet.md`, not yet written). The current sprint's `AxiomGolden.txt` documents the budget; the successor packet's residual is to discharge the listed axiom and flip D2 from OracleNeeded to Certificate.
* `defer: lp<...>-symbol-game-recording -> successor packet core_mub_symbol_game_packet.md` — the `pfp` candidate `lp<...>` recording named in §4 and §11 is a candidate-residual-generator stream, not load-bearing for the Rust-Lean overlap closure. Recording the Meta as an `lp<...>` term and replaying it through the Symbol Game adapter is moved to a successor packet (proposed name `core_mub_symbol_game_packet.md`, not yet written). LLMs remain candidate generators, never judges, in either packet.
* `defer: lower-bound-Lean-shadow -> successor packet core_mub_attainment_packet.md` — mechanizing `max f >= W` via `mub::wall::attainment` on the Lean rail is out of scope for this sprint and moved to a successor packet (proposed name `core_mub_attainment_packet.md`, not yet written).

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, both `mub` and `core_mub` contain substantial mathematical and certificate surfaces, but no admitted single semantic owner and no `GtocExactInput` adapter into `core_pipeline::gtoc_gtla::evaluate_exact` exists. `PaperER006/MUB6Wall.lean` is also absent at this base. Ownership selection, exact adaptation, and the honest Lean/certificate boundary remain owned by `S16-003`. This lane remains `OpenObstruction`, with survivor route `OperatorNeeded`, `AuthorityEffect::None`, and no human promotion. The S16-001 census records the current packet hash and source manifest and does not infer convergence from either crate's file presence.

15. S16-003 current-base runtime disposition
--------------------------------------------

At frozen base `d295aa86692467eb17c85551ff55629c1c0df14c`, packet `29cade7d0bcc807e226abfa20aef805042a3b969cf40f7e97b0bfba64adfad60` selects `core_mub` as the sole Core-native MUB domain/runtime owner. The Apache-derived `mub` crate remains an evidence-only comparison provider and is not imported by the production adapter. Ownership of the wall functional, exact evaluator, terminal enum, and authority boundary remains with `core_functional`, `core_pipeline`, `core_state`, and `core_certifiers` respectively.

`core_mub::runtime_adapter` replays the committed exact fixed-`T0` carrier and vector-cover witness, constructs the shared `core_pipeline::gtoc_gtla::GtocExactInput`, and recomputes primitive-difference validity, Phi1, Gamma2, and trichotomy. The exact cover fixture routes to `ExactRepair`; the uncovered fixed triple routes to `StabilizedSurvivor`; the hostile exact closure fixture routes to `OpenObstruction`; malformed JSON and floating diagnostics route to `Refused`. Every successful projection has `AuthorityEffect::None`.

`PaperER006.MUB6Wall.mub6_wall_upper` is intentionally conditional on `ExactUpperCertificate`. The module neither constructs that certificate nor reflects the 441-by-441 PSD artifact. Its `#print axioms` output contains only the standard Lean/Mathlib axioms `propext`, `Classical.choice`, and `Quot.sound`; the three terminal-projection theorems are axiom-free. This is an honest finite statement boundary, not the axiom-free PSD branch or a proof of complete MUB(6) existence/nonexistence.

The S16-003 aggregate terminal is `StabilizedSurvivor`, with `AuthorityStatus: None`, `AuthorityEffect::None`, no gate activation, and no human promotion. The unreflected PSD artifact, full dimension-six MUB classification, and production convergence remain explicit residuals. Earlier target/seal language in this packet is historical planning evidence and does not override this dated current-base receipt.
