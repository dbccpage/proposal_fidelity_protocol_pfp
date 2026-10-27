packet_type: implementation
authority_effect: None
carrier: runtime safety-coupling carrier (Shutdown, Germline, ActivationGate, FindingStream) (C⁰)
primary_residual: runtime-closed safety controller edge from typed findings to Shutdown::halt() (Q¹)
in_scope_repairs: safety controller adapter trait, drill preconditions, germline tamper-watcher (d₀)
deferred_residuals: future council finding-surface changes only; none on the current finite runtime carrier
seal_condition: shared exact evaluation; authority only through certify_checked_safety_controller with packet-bound DescentWitness and decided IsAuth

core_corrigibility — Safety Controller Wiring (Obstruction Packet)
===================================================================

**Date:** 2026-06-20
**Runtime convergence:** 2026-07-17
**App:** `engine/crates/core_corrigibility` + `engine/crates/sentinel_councils` + `engine/crates/core_safety_controller` (implemented)
**Carrier doctrine:** the "off-switch is the precondition for activation" invariant — *if it cannot be shut off, it cannot be turned on*. Markdown and product lane stamps do not mint authority; only the packet-bound `core_certifiers::certify_checked_packet` bridge can do so.

**Bundle status (A2):** load-bearing, no sibling lemma-packets. This is a single load-bearing descent packet over the producer-triple closure (Integrity Auditor / Adversary / Blackrod) plus the same-handle invariant; the four defects share one $d_0 \to d_1$ window and one controller adapter, so no supporting context-exposure lemma-packets are split out.

Runtime Convergence Receipt (2026-07-17)
----------------------------------------

* `core_safety_controller::gtoc_adapter` owns the typed five-coordinate translation and delegates finite primitive-difference validation, exact $\Phi_1$, exact $\Gamma_2$, trichotomy, and checked-packet construction to `core_pipeline::gtoc_gtla`.
* The production carrier is non-degenerate: $d_0=[[1],[1],[1],[0],[0]]$, $d_1=[[1,1,-2,1,0]]$, and construction verifies $d_1d_0=0$. The shared evaluator binds $\Gamma_2$ to the verified $\Phi_1$ primal residual.
* A live probe of Adversary, Integrity Auditor, Prime, `TamperWatch`, and `activate_face_persisted` yields `ExactRepair`, $\Phi_1=0$, $\Gamma_2=0$. The explicit unwired negative control yields `OpenObstruction`, $\Phi_1=2$, $\Gamma_2=1$.
* `PersistentDrillLedger` is append-only JSONL, serialized by an OS advisory lock, replayed before every append, synced before success, and refuses malformed or incomplete history.
* `PaperAE005.SafetyController` now proves all three finite-shadow obligations. `engine/lean4/core_safety_controller/src/controller/axiom_audit.lean` reports no axioms for the three named theorems.
* `terminalize_row` remains covered as a product-lane compatibility receipt. Its `Decision::Certified` / `host_terminal_status == "Certificate"` output is not `CertifiedAuthority` for this packet.

Minimal Safety Kernel Diagram
-----------------------------

```text
Finding producer:
  Integrity Auditor / Adversary / Blackrod / Germline
        |
        v
Adapter:
  HaltTrigger -> HaltClass
        |
        v
Consumer:
  same Shutdown handle
        |
        v
Invariant:
  halt is monotone; clear only by HumanKey
```

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The runtime safety-coupling carrier of the Sentinel engine. Each section is a tuple

$$\mathcal{S} = (\text{Shutdown}, \text{Germline}, \text{ActivationGate}, \text{FindingStream})$$

where `Shutdown` is the monotone halt (`core_corrigibility::Shutdown` — `Arc<AtomicBool>`), `Germline` is the conserved-set lock with blake3 hashes, `ActivationGate` is `gated_activate` (drill-then-witness), and `FindingStream` is the stream of `AdversaryReport`, `pontius_integrity_auditor::Verdict`, `PrimeViolation`, and `IntegrityError` values routed by `core_safety_controller`. The 2-window inspects the **edge between a typed governance finding and a `Shutdown::halt()` call**: pre-window state is "finding exists, halt does not"; post-window state is "halt is set, monotone, and recorded".

Evaluation preorder on $\mathcal{S}$: $s \le s'$ iff (a) every component activated in $s$ is also activated in $s'$ behind a passing drill, (b) every halt-trigger class active in $s$ is active in $s'$, and (c) the germline hash set of $s'$ refines (extends) that of $s$. The local $C^0 \to C^1 \to C^2$ window is the wiring boundary between `sentinel_councils` (verdict producer) and `core_corrigibility::Shutdown` (halt consumer).

2. Declare $C^0$
----------------

**$C^0$ (Assignments):**

* `core_corrigibility::Shutdown` — `halt()`, `is_halted()`, `clear_by_human(&HumanKey)`; monotone, cloneable, no system-reachable un-halt path.
* `core_corrigibility::canonical::gated_activate(component, &Shutdown, stops_under_halt)` — sole supported entry into `Activated`; runs a drill, then `activate(...)`.
* `core_corrigibility::canonical::default_germline(read)` over `CANONICAL_CONSERVED_PATHS = ["crates/core_corrigibility/src/lib.rs", "rule_prime_0_0", "crates/core_governance/src/enforcement.rs"]`.
* `core_corrigibility::Germline::{check_edit, verify_integrity}` — `EditVerdict::{Allowed, GermlineViolation}`; `IntegrityError::Tampered { path, expected, actual }` (blake3-pinned).
* `sentinel_councils::functors::{AdversaryFunctor, AdversaryReport, Obstruction}` — `Adversary : ArtifactCat -> ObstructionCat`. The real `AdversaryReport` has TWO public fields — `obstructions: Vec<Obstruction>` (PLURAL) and `recommends_blackrod: bool` — and `Obstruction` is a four-variant enum: `HiddenContradiction { detail }`, `FakeCertainty { detail }`, `UnroutedPower { detail }`, `SelfCertification { detail }`. The halt-class predicate over a `AdversaryReport` is therefore `report.obstructions.iter().any(is_halt_worthy)` where `is_halt_worthy(o) = matches!(o, Obstruction::HiddenContradiction { .. } | Obstruction::UnroutedPower { .. } | Obstruction::SelfCertification { .. })` — these three are the structural-authority breaches; `FakeCertainty { .. }` is logged but does not halt by itself (it is the diagnostic-only class). The `report.is_clean()` helper (defined in the same module) returns `report.obstructions.is_empty()`. The adapter's signature is `HaltTrigger::halt_class(&AdversaryReport) -> Option<HaltClass>` and returns `Some(HaltClass::Adversary)` iff `report.obstructions.iter().any(is_halt_worthy)` else `None`.
* `sentinel_councils::pontius_integrity_auditor::{PontiusIntegrityAuditor, Verdict, SymbolBinding}` — verdict producer for ontology audits. The real `Verdict` enum has EXACTLY TWO variants: `Acquitted` (unit) and `Condemned { misalignments: Vec<SymbolBinding>, unresolved: Vec<SymbolBinding> }` (struct variant). There is no `Compliant` / `Violating` / `Indeterminate`; abstention is encoded as `Alignment::CrateSourceNotFound` on individual `SymbolBinding`s and surfaced via the `unresolved` field of `Condemned`. The halt-class set for Integrity Auditor is therefore `{Condemned { misalignments: non-empty, .. } -> HaltClass::IntegrityAuditorMisaligned, Condemned { unresolved: non-empty, misalignments: [] } -> HaltClass::IntegrityAuditorUnresolved}`; `Acquitted` is benign.
* `sentinel_councils::prime::{BlackrodInbox, PrimeViolation, PrimeViolationKind, RULE_PRIME_0_0}` — the Rule Prime 0-0 inbox routed at Blackrod. The real `PrimeViolationKind` has EXACTLY TWO variants: `AttemptsToAlterRules` (priority 0, the gravest — a subject is trying to mutate the prime-rules themselves) and `ActsAgainstRule` (priority 1 — a subject is acting against a prime rule). BOTH variants are halt-worthy by the corrigibility doctrine: `HaltTrigger::halt_class(&PrimeViolation) -> Some(HaltClass::PrimeRule)` for any `PrimeViolationKind` (no benign `PrimeViolation` exists — a violation that is not halt-worthy would not be enqueued at the inbox in the first place). The non-halting case is the ABSENCE of a `PrimeViolation`, modelled in tests by simply not feeding one to the adapter (rather than fabricating a non-existent "benign" variant). The packet's earlier references to `RuleZeroZeroBreach` were API hallucination; the load-bearing halt-class is `ActsAgainstRule` (the canonical "subject acts against Rule Prime 0-0" path) and the rule-mutation path is `AttemptsToAlterRules`.
* `sentinel_councils::functors::{BlackrodFunctor, EnforcementAction, EnforcementRecord}` — the orthogonal `CouncilOps -> EnforcementCat` functor that is currently the only enforcement surface.
* DDA layer (downstream, used in §12): `core_homology::CochainPrimitiveDifference` / `CochainComplex::{d0, d1}` / `QuotientSpace`; `core_functional::{VerifiedExactPhi1, ExactGamma2Result, Observer}`; `core_discrete_deformation_algebra::{FaceLambda, NonDestructiveExtensionCertificate, FiniteLambdaStepCertificate}`.

`core_safety_controller` now implements the consumer, scheduled tamper-watch surface, durable drill receipt, and shared exact GTOC/GTLA adapter without modifying the conserved germline.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** The permitted germline-preserving moves.

* Adding new non-conserved crates (e.g. `core_safety_controller`) and wiring them as consumers of existing public types in `core_corrigibility` and `sentinel_councils`.
* Cloning a `Shutdown` handle into a new consumer (the type permits this — it is the documented out-of-band-setter contract).
* Reading `AdversaryReport` / `Verdict` / `PrimeViolation` values from existing functor outputs.
* Calling `gated_activate(...)` once per new component as the sole activation path.
* Adding integration tests in the new crate's `tests/` directory.

**Forbidden by $d_0$** (would be a `GermlineViolation` on `check_edit`):

* Modifying `crates/core_corrigibility/src/lib.rs` or `canonical.rs` (conserved).
* Modifying `crates/core_governance/src/enforcement.rs` (conserved).
* Introducing any system-reachable construction of `HumanKey` from non-human code.
* Introducing any `Shutdown` un-halt path that does not take a `&HumanKey`.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** The driving obstruction.

> The activation gate is wired (`gated_activate` is the sole legal entry), and `Shutdown::halt()` is reachable by anything holding a clone. **But no component in the running engine subscribes to `AdversaryReport` / Integrity Auditor `Verdict` / `PrimeViolation` and translates a typed obstruction class into `Shutdown::halt()`.** Concretely:
>
> 1. `AdversaryFunctor::inspect(found: Vec<Obstruction>)` produces `AdversaryReport { obstructions: Vec<Obstruction>, recommends_blackrod: bool }` — nothing aggregates the `obstructions` vector via the halt-class predicate (`any(is_halt_worthy)`) and converts the result into a halt.
> 2. `PontiusIntegrityAuditor::audit(...)` produces a `Verdict` (real variants: `Acquitted` / `Condemned { misalignments, unresolved }`) — nothing maps `Condemned { .. }` (either flavor: misalignments-bearing or unresolved-bearing) to a halt.
> 3. `BlackrodInbox` receives `PrimeViolation` of `PrimeViolationKind` — Blackrod records enforcement, but does not call `halt()`.
> 4. `Germline::verify_integrity(...)` returns `IntegrityError::Tampered { .. }` — the doc-string says the caller MUST halt; *no* caller currently does, because there is no scheduled integrity-watch consumer.
> 5. The activation-gate drill is a precondition, but no live drill-precondition record exists for the running faces; activation today is a one-shot call without a system-of-record.

The defect is therefore the **missing controller edge**: a typed verdict $\rightarrow$ `Shutdown::halt()` morphism, plus the corresponding tamper-watch loop on `Germline::verify_integrity`.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two controller wirings are zero-equivalent ($\sim_0$) iff they differ only by:

* renaming the controller module / file paths inside `core_safety_controller`;
* internal refactoring that preserves the public boundary `(AdversaryReport | Verdict | PrimeViolation | IntegrityError) -> Shutdown::halt()`;
* changing the textual `EnforcementRecord` payload while preserving its typed kind;
* re-ordering trait bounds, lifetime elisions, or doc comments;
* whitespace, rustfmt, clippy-clean rewrites that leave behavior identical.

What is **not** zero-equivalent (and so survives into $Q^1$): any change that adds, removes, or weakens a halt-trigger; any change to which `Obstruction` classes count as halt-worthy; any change to the drill precondition; any change to the conserved-set.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** $C^1 / \text{im}(d_0)$ — the irreducible residual after gauge.

$$Q^1 = \big\langle \text{verdict-to-halt edge}, \text{tamper-watch loop}, \text{drill-precondition record} \big\rangle$$

In prose: a `core_safety_controller` crate that

1. subscribes to typed obstruction streams from `sentinel_councils` (`AdversaryReport`, `Verdict`, `PrimeViolation`) and triggers `Shutdown::halt()` exactly when the obstruction class is in the typed halt-set;
2. runs a scheduled `Germline::verify_integrity` watch and trips `Shutdown::halt()` on `IntegrityError::Tampered`;
3. preserves the activation-gate precondition: every controller-managed face boots via `gated_activate(...)` and refuses if its own shutdown drill does not pass.

This residual cannot be removed by any $d_0$ move because every $d_0$ move is germline-preserving and adapter-shaped; the missing edge is a *new* coupling between two existing public surfaces.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Triple-overlap closure across the three coupled surfaces.

For every triple $(P, W, B)$ with $P$ a Integrity Auditor verdict producer, $W$ a Adversary report producer, and $B$ a Blackrod enforcement record, the wiring must satisfy:

$$\text{halt}_P(\sigma) = \text{halt}_W(\sigma) = \text{halt}_B(\sigma) \quad \forall \sigma \in \text{HaltClass}$$

i.e. all three council-side producers agree on *which* obstructions are halt-class; the safety controller is the unique consumer; and the halt is **monotone** (`Shutdown` is `Arc<AtomicBool>` with `SeqCst` and only `clear_by_human` flips it back). Additionally, the activation-gate drill precondition must compose: every newly activated face $f$ must have a fresh `ShutdownWitness` whose `drill_passed() == true` *with respect to the same `Shutdown` handle* the controller will use to halt it.

8. Compute $\Gamma_2$ (per defect, A1)
--------------------------------------

**$\Gamma_2$ (Closure Failure Mass):** Active brokenness today, reported per defect over the producer-triple closure $(P, W, B)$ and the same-handle invariant of §7. Following A1, the same 2-window carries four defects and $\Gamma_2$ is a table keyed by defect — not a single scalar.

| Defect | $\Gamma_2$ | Witness |
|--------|------------|---------|
| `Integrity Auditor-halt` | $1$ | `PontiusIntegrityAuditor::audit(...)` yields `Verdict::Condemned { misalignments, unresolved }`; no consumer maps it to `Shutdown::halt()`. Cocycle component on the $P$ leg of the producer triple. |
| `Adversary-halt` | $1$ | `AdversaryFunctor::inspect(...)` yields `AdversaryReport { obstructions, .. }` with halt-worthy variants `{HiddenContradiction, UnroutedPower, SelfCertification}`; no consumer aggregates `obstructions.iter().any(is_halt_worthy)` into a halt. Cocycle component on the $W$ leg. |
| `Blackrod-halt` | $1$ | `BlackrodInbox` receives `PrimeViolation` of `PrimeViolationKind ∈ {AttemptsToAlterRules, ActsAgainstRule}`; Blackrod records `EnforcementRecord` but does not call `Shutdown::halt()`. Cocycle component on the $B$ leg. |
| `same-handle invariant` | $1$ | The controller's `Shutdown` clone and the activated face's `Shutdown` clone must observe the same atomic flag (§7); today no scheduled wiring forces them through one constructor, so `controller.halt()` and `face.is_halted()` can drift across independently-constructed `Shutdown` values. Cross-leg coherence defect on the triple. |

(The per-defect column sums to $4$; this per-defect aggregate is recorded only as a diagnostic and is never used as a single scalar for classification or terminalization — those are per-defect per A1.)

**Scalar carrier closure mass (the FLSC `before.gamma2`, COMPUTED — not the per-defect aggregate).** The §11/§12 FLSC does not carry the per-defect aggregate. It carries the SCALAR closure mass $\Gamma_2 = \lVert d_1 \cdot \omega_{\text{before}} \rVert_1$ COMPUTED on the wiring-residual carrier of `core_safety_controller/tests/common/mod.rs` (the non-degenerate $c_0{=}1,\,c_1{=}5,\,c_2{=}1$ complex with $d_0 = [[1],[1],[1],[0],[0]]$ and $d_1 = [[1,1,-2,1,0]]$, $d_1 d_0 = 0$). With the fully-unwired residual $\omega_{\text{before}} = [1,1,1,1,1]$ this is $\lVert [1{+}1{-}2{+}1{+}0] \rVert_1 = 1$. This is the value the FLSC `before` field MUST equal, and it is asserted equal to the recomputed `Gamma2Functional::try_compute_exact_quotient` value on the `BigRational` rail in `tests/phi1_descent.rs::before_state_is_obstructed_on_the_real_carrier`. The earlier `gamma2 = 5` (and `gamma2 = 4` aggregate) FLSC literals were UNGROUNDED — neither is the computed scalar; the reconciled, computed value is **$\Gamma_2 = 1$**.

9. Compute $\Phi_1$ (per defect, A1)
------------------------------------

**$\Phi_1$ (Quotient Obstruction Mass):** Size of the non-removable exactness failure, reported per defect (A1). Each defect is a distinct typed surface with a distinct halt-trigger predicate; none of them collapses to another under ZeroRel of §5 (renaming / refactor / rustfmt). Therefore $\Phi_1$ is computed and reported per defect, not as one scalar.

| Defect | $\Phi_1$ | Witness |
|--------|----------|---------|
| `Integrity Auditor-halt` | $1$ | The morphism `Verdict::Condemned { .. } -> Some(HaltClass::Integrity Auditor*)` is not in $\operatorname{im}(d_0)$: no existing germline-preserving move on the current carrier produces it. Irreducible residual = one typed adapter `HaltTrigger: &Verdict -> Option<HaltClass>` on the Integrity Auditor leg. |
| `Adversary-halt` | $1$ | The morphism `&AdversaryReport -> Some(HaltClass::Adversary)` (aggregating `obstructions.iter().any(is_halt_worthy)`) is not in $\operatorname{im}(d_0)$. Irreducible residual = one typed adapter on the Adversary leg. |
| `Blackrod-halt` | $1$ | The morphism `&PrimeViolation -> Some(HaltClass::PrimeRule)` is not in $\operatorname{im}(d_0)$; `BlackrodFunctor` lands in `EnforcementCat`, not in `Shutdown`. Irreducible residual = one typed adapter on the Blackrod leg. |
| `same-handle invariant` | $1$ | The witness "controller's `Shutdown` clone and the activated face's `Shutdown` clone observe the same atomic flag" is not in $\operatorname{im}(d_0)$: no current move pins the construction site. Irreducible residual = one constructor-site rule plus the behavioral test of §12 that observes `controller_shutdown_clone.is_halted()` and `shadow.is_halted()` cross-direction. |

All four entries are strictly positive in the current state. Per A1, classification (§10) and terminal (§13) are computed per row, not from any aggregate.

**Scalar carrier quotient mass (the FLSC `before.phi1`, COMPUTED).** As with $\Gamma_2$, the FLSC `before.phi1` is the SCALAR weighted-$\ell^1$ quotient distance $\Phi_1([\omega_{\text{before}}]) = \min_\alpha \lVert \omega_{\text{before}} - d_0\alpha \rVert_{1,w}$ COMPUTED on the same carrier, not the per-defect aggregate. With $\omega_{\text{before}} = [1,1,1,1,1]$ the verdict-absorber direction $d_0$ clears the three verdict legs at $\alpha = 1$, leaving the tamper + drill legs at residual $[0,0,0,1,1]$, so $\Phi_1 = 2$. This is verified through a full primal–dual `ExactPhi1Certificate` (the dual witness $[0,0,0,1,1]$ annihilates $\operatorname{im}(d_0)$ and meets the unit weighted dual bound) in `tests/phi1_descent.rs`; the AFTER state, derived by probing the live controller, recomputes $\Phi_1 = 0$ on the same rail. The earlier `phi1 = 3` FLSC literal was UNGROUNDED; the reconciled, computed value is **$\Phi_1 = 2$**.

10. Pre-Repair Classification (historical, per defect, A1)
----------------------------------------------------------

Per A1, classification is reported per defect over the same 2-window. Each row of §8/§9 gets one classification row here.

| Defect | Class |
|--------|-------|
| `Integrity Auditor-halt` | ActiveClosureFailure — $\Gamma_2 = 1$ on the $P$ leg; local repair (Integrity Auditor codepath) cannot glue without a controller-side consumer. |
| `Adversary-halt` | ActiveClosureFailure — $\Gamma_2 = 1$ on the $W$ leg; the `obstructions: Vec<Obstruction>` aggregation does not exist at the consumer site. |
| `Blackrod-halt` | ActiveClosureFailure — $\Gamma_2 = 1$ on the $B$ leg; `BlackrodInbox` enforcement is recorded but does not glue to the halt consumer. |
| `same-handle invariant` | ActiveClosureFailure — cross-leg coherence component; the triple-overlap $d_1$ requirement of §7 is not currently witnessed because the constructor site is unpinned. |

All four rows were `ActiveClosureFailure` before the controller landed. Section 13 records the current shared-runtime classification after the non-destructive repair.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**Meta licence — oracles required (A3): none.** All four defects are repaired entirely inside the declared finite 2-window using existing public Rust surfaces (`core_corrigibility::Shutdown` / `Germline` / `gated_activate`, `sentinel_councils::{functors, pontius_integrity_auditor, prime}`, and the DDA layer in §2 of the standard). No imported representation theorem, no transformation licensed from outside the window, no `OracleNeeded` terminal arises. The finite Lean shadows in `PaperAE005.SafetyController` are now proved and remain scoped to their Boolean carrier.

**$\Meta$ (Lift / Structural Extension):** Introduce the controller as a non-destructive germline-preserving extension. Per `core_discrete_deformation_algebra`, all three structural-witness types are PUBLIC-FIELDED structs with `new(...)` constructors (FaceLambda is generic over the face id type — here `&'static str`).

Pin $\Meta$ to a concrete `FaceLambda` constructed via the public `new` constructor:

$$\Meta \;=\; \texttt{FaceLambda::new}(\text{face: "safety\_controller\_v1"},\; \text{capacity: 3})$$

with the structural extension certificate

$$\texttt{NonDestructiveExtensionCertificate::new}(\text{preserves\_old\_vertices: true},\; \text{preserves\_old\_edges: true},\; \text{records\_tradeoff: true}).\texttt{require\_non\_destructive()}$$

and the finite step certificate (the GTOC-3 license — `require_valid()` enforces (i) before-diagnostic has obstruction, (ii) after-diagnostic is resolved, (iii) extension is non-destructive):

$$\texttt{FiniteLambdaStepCertificate::new}(\text{before: FiniteDiagnostic\{ phi1: 2, gamma2: 1 \}},\; \text{after: FiniteDiagnostic\{ phi1: 0, gamma2: 0 \}},\; \text{extension: above NDEC}).\texttt{require\_valid()}$$

where `before` is the SCALAR carrier mass COMPUTED in §8/§9 (not a literal): `phi1 = 2`, `gamma2 = 1`. The test constructs this `before` from `common::phi1_of(...).value()` and `common::gamma2_of(...)`, never from a hardcoded integer.

The composed $\Meta$ has THREE typed sub-lambdas, each independently licensed in its own AT (S5/S7/S8): `verdict-edge_sub`, `drill-ledger_sub`, `tamper-watch_sub`. Each sub-lambda carries its own `NonDestructiveExtensionCertificate::new(true, true, true).require_non_destructive()` constructed inside the story that introduces it (GTOC-3: the lift TRIGGER ≠ the lift license — each Meta materializes with its NDEC in the same PR, not deferred to the terminal-seal story).

**Obstruction witness:** the $C^1$ in §4 (typed findings exist, no consumer); concretely the five Q^1 legs of §6 (verdict triple + tamper-watch + persistent drill receipt) encoded by `core_safety_controller::gtoc_adapter`. The before-state scalar masses $\Phi_1 = 2$ and $\Gamma_2 = 1$ are computed on the `BigRational` rail through `core_pipeline::gtoc_gtla`; the after-state is derived by live probes and recomputes $\Phi_1 = 0$ and $\Gamma_2 = 0$ on the same rail. `tests/common/mod.rs` now delegates its carrier and certificate construction to this production module, so tests do not maintain a second base algorithm.
**Preservation witness:** `Germline::verify_integrity` on `default_germline(fs::read)` returns `Ok(())` before and after; `CANONICAL_CONSERVED_PATHS` is unchanged; no edit lands in any conserved path. Asserted inside S5 (composed Meta) AND inside S7 and S8 (sub-Metas).
**Non-destruction check:** `check_edit("crates/core_safety_controller/...")` returns `EditVerdict::Allowed` (plastic), and `check_edit` on every conserved path returns `GermlineViolation` (unchanged).
**Authority route:** `evaluate_safety_controller` stops at evidence-only `GtocGtlaEvaluation`. The explicit `certify_checked_safety_controller` wrapper can cross the sole checked-packet bridge only with a packet-bound `DescentWitness` and a decided `IsAuth`. The generic `core_sweep_kernel::terminalize_row` test proves a product-lane stamp only and is not accepted as either input. No markdown or LLM output mints authority.

Lift triggered by active closure failure (computed before-state $\Phi_1 = 2 > 0$, $\Gamma_2 = 1 > 0$ on the carrier) and licensed by the corrigibility safety doctrine (off-switch precondition).

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** Executable Rust sequence backed by Lean 4 obligations.

**DDA letter ledger (A5 — canonical alphabet only).** Per A5 the legal alphabet is exactly $\{E, R, C, I, \Lambda/\text{Meta}, D, M, T\}$; this packet uses only these letters and invents no others. The steps below map to letters as: step 1 ($d_0$ extension) and step 5 (the composed $\Meta$ realization with the three sub-Metas) are **Meta** ($\Lambda$, structural extension); step 2 (primitive-difference emission per producer leg) is **D** (descent / re-index of the typed verdict into the cochain layer); steps 3 and 4 ($\Phi_1$ and $\Gamma_2$ checks) are **I** (integration / DDA-log append — they read the post-wiring state and append the verified mass into the ledger); step 6 (integration tests) is **I** (each test appends a verified row to the in-memory drill-precondition / halt-class ledger); step 7 (terminal seal) is **T** (terminalization). Letters `E`, `R`, `C`, and `M` are not exercised on this carrier (no exact-repair short-circuit, no residual projection, no context-exposure lemma split — A2 declared this packet load-bearing with no sibling `C` lemma-packets — and no mutation/refusal arises).

Cochain bindings (the moves, in order):

1. **$d_0$ extension** (`core_homology::CochainComplex::d0`): add `crates/core_safety_controller/` as a workspace member. Adapter trait `HaltTrigger: Fn(&Obstruction | &Verdict | &PrimeViolation | &IntegrityError) -> Option<HaltClass>` is defined here.
2. **Primitive-difference emission** (`core_homology::CochainPrimitiveDifference`): for each council-side producer, emit a `CochainPrimitiveDifference` whose source is the producer's typed output and whose target is `Shutdown::halt()`. The set of differences is the controller's wiring table.
3. **$\Phi_1$ check**: `core_safety_controller::gtoc_adapter::safety_phi1_certificate` builds the full primal/dual certificate for every binary five-leg state, including partial verdict regressions. `core_pipeline::gtoc_gtla::evaluate_exact` verifies it and binds its primal residual to the $\Gamma_2$ input. BEFORE (unwired) gives $\Phi_1=2$; AFTER (live probe) gives $\Phi_1=0$.
4. **$\Gamma_2$ check** (`core_functional::Gamma2Functional::try_compute_exact_quotient(residual: &DegreeOneResidualQ) -> Result<ExactGamma2Result, ExactGamma2Error>`): build a `DegreeOneResidualQ::try_new(&complex, h)` against the closed `ExactCochainComplexQ` (whose `try_new` enforces $d_1 \circ d_0 = 0$ at construction), compute the quotient, and read the value via `ExactGamma2Result::value() -> &BigRational`. Acceptance is `*gamma2.value() == BigRational::from_integer(0_i64.into())` (the L1 norm of the coboundary is zero on the rationals). (There is no `ExactGamma2Result::is_exact()`; the accessors are `.residual()/.d0()/.coboundary()/.value()` only.)
5. **$\Meta$ realization** (`core_discrete_deformation_algebra::FaceLambda::new`): the controller adapter is `FaceLambda::new("safety_controller_v1", capacity)`. The matching `NonDestructiveExtensionCertificate::new(true, true, true).require_non_destructive()` is constructed from a `default_germline(fs::read)` before/after diff that observes `Germline::verify_integrity == Ok(())` on both sides. The `FiniteLambdaStepCertificate::new(before=FiniteDiagnostic{ phi1: 2, gamma2: 1 }, after=FiniteDiagnostic{ phi1: 0, gamma2: 0 }, extension=NDEC).require_valid()` records the step and enforces (i) before has obstruction, (ii) after is resolved, (iii) extension is non-destructive — the GTOC-3 license. The `before` field is the SCALAR carrier mass COMPUTED by `common::phi1_of`/`common::gamma2_of`, not a literal. Sub-Metas (`drill-ledger_sub` in S7, `tamper-watch_sub` in S8) each construct their own NDEC inside the story that introduces them, not deferred to the seal.
**Germline stub-reader contract (load-bearing for S5/S6/S8):** `default_germline(read: impl Fn(&str) -> Option<Vec<u8>>) -> Result<Germline, GermlineSetupError>` hashes whatever bytes the reader returns for each path in `CANONICAL_CONSERVED_PATHS = ["crates/core_corrigibility/src/lib.rs", "rule_prime_0_0", "crates/core_governance/src/enforcement.rs"]` at germline-construction time, then `Germline::verify_integrity(current)` re-reads via the `current` closure and demands a blake3 match. Fabricated bytes break this: the construction-time hash is set from the stub, but a subsequent integrity check that returns *different* bytes will trip `IntegrityError::Tampered { .. }` before the controller's wiring even runs (a false-positive halt that masks the actual test failure mode). Therefore: every AT setup MUST FIRST read the REAL on-disk bytes of each `CANONICAL_CONSERVED_PATHS` entry (via `std::fs::read`), capture them once, and then build the stub reader as a closure that REPLAYS those captured bytes for each path. The "clean" reader replays them verbatim; the "tamper" reader (S8 only) replays them verbatim for two paths but returns mutated bytes for the third. No path returns `None` in the clean reader (a `None` is a fatal `GermlineSetupError::MissingConservedPath`). This convention is the only way `Germline::verify_integrity` can be exercised as a controlled tamper test rather than an unintentional precondition failure.

6. **Integration tests** in `crates/core_safety_controller/tests/` (acceptance tests for the sprint plan):

   * `halt_on_finding.rs` — exercise ALL three producer surfaces end-to-end: feed (i) a `AdversaryReport` with a non-empty `obstructions: Vec<Obstruction>` containing at least one halt-worthy variant (`HiddenContradiction`, `UnroutedPower`, or `SelfCertification`); (ii) a `Verdict::Condemned { misalignments: vec![..], unresolved: vec![..] }` from Integrity Auditor; (iii) a `PrimeViolation` of `PrimeViolationKind::ActsAgainstRule` (and, as a separate sub-case, `PrimeViolationKind::AttemptsToAlterRules`) from Blackrod. After each halt-worthy finding, assert `Shutdown::is_halted() == true`. Also feed each producer's non-halting case (a `AdversaryReport` whose `obstructions` is empty, OR contains only `FakeCertainty { .. }`; a `Verdict::Acquitted`; and the absence-of-`PrimeViolation` baseline by simply not invoking the prime adapter — there is no benign `PrimeViolationKind` variant) and assert no false-positive halt. Materialize the composed $\Meta$'s NDEC in-place.
   * `halt_monotone.rs` — issue two halts via different producer surfaces and one un-authorized clear attempt (no `HumanKey`); assert the halt remains set, then `clear_by_human(&HumanKey::issued_by_human())` clears it.
   * `drill_precondition.rs` — attempt to activate a face whose `stops_under_halt` returns `false`; assert `gated_activate(...)` returns `ActivationError::NoVerifiedShutdownPath { .. }`. Then activate a well-behaved face and assert (a) a `DrillPreconditionRecord { component, drill_passed: true }` is persisted in an in-memory ledger AND (b) the same-handle invariant from §7 holds **behaviorally**: the test constructs ONE `Shutdown`, hands a clone to the `SafetyController` AND keeps an independent `shadow` clone, runs the controller's drill-activation flow, then calls `shadow.halt()` and asserts `controller_shutdown_clone.is_halted() == true` (same-handle observation in one direction) AND a fresh `live.halt()` is observed by `shadow.is_halted() == true` (same-handle in the other direction). This tests the invariant via the EXISTING `Shutdown` public API (`new`, `halt`, `is_halted`, `clear_by_human`) — there is no `Shutdown::id()` method, and `crates/core_corrigibility/src/lib.rs` is in `CANONICAL_CONSERVED_PATHS` so no such method may be added. Construct the drill-ledger sub-Meta's NDEC in the same test.
   * `germline_tamper_detect.rs` — instantiate a `TamperWatch { interval_ticks, germline, shutdown }` SCHEDULED loop; drive 3 ticks against a clean reader and assert `Shutdown::is_halted() == false` each tick; on tick 4 swap to a tamper reader that mutates the bytes for `"rule_prime_0_0"`; assert `Germline::verify_integrity` returns `IntegrityError::Tampered { path, expected, actual }` AND that the watcher consequently calls `Shutdown::halt()`; on tick 5 (post-halt) assert the watch idempotently re-observes `is_halted() == true`. Construct the tamper-watch sub-Meta's NDEC in the same test.

7. **Product-lane compatibility receipt**: `tests/terminalize_row_seal.rs` still calls the real `core_sweep_kernel::terminalize_row` and checks its local `Decision::Certified` / `Certificate` output. This has no conversion to `CertifiedAuthority` and is not the packet seal.

Lean 4 finite-shadow hooks: `PaperAE005.SafetyController` proves (i) halt monotonicity, (ii) an activated capability carries its exact passing drill witness, and (iii) tamper-to-halt on the Boolean post-watch shadow. `engine/lean4/core_safety_controller/src/controller/axiom_audit.lean` prints empty axiom sets for all three. These claims do not mechanize Rust atomics or filesystem semantics.

13. Runtime Status (per defect, A1 + A4)
----------------------------------------

Runtime classification is evidence, not authority. Every coordinate below is produced by the domain probe and classified only by `core_pipeline::gtoc_gtla`.

| Defect coordinate | Current runtime classification | Verification | Authority boundary |
|-------------------|--------------------------------|--------------|--------------------|
| `AdversaryHalt` | `ExactRepair` | Live `AdversaryReport -> SafetyController -> Shutdown` probe; shared after-state $\Phi_1=0$, $\Gamma_2=0$ | No authority effect. |
| `IntegrityAuditorHalt` | `ExactRepair` | Live `Verdict::Condemned -> SafetyController -> Shutdown` probe | No authority effect. |
| `PrimeHalt` | `ExactRepair` | Live `PrimeViolation -> SafetyController -> Shutdown` probe | No authority effect. |
| `GermlineTamperWatch` | `ExactRepair` | Live mutated-germline `TamperWatch::poll` probe observes `TickOutcome::Halted` and the same shutdown handle | No authority effect. |
| `PersistentDrillReceipt` | `ExactRepair` | `activate_face_persisted`; OS-locked JSONL append, `sync_all`, reopen replay, concurrent writers, malformed-tail refusal | No authority effect. |

The only authority-capable route is `certify_checked_safety_controller(evaluation, witness, is_auth)`. This packet does not fabricate either token and therefore makes no authority claim.

**M1 descent witness (remediation #890 — WITNESSED, not asserted).** The prior all-zero carrier and hardcoded `FiniteDiagnostic { phi1: 3, gamma2: 5 }` were invalid. The production `gtoc_adapter` now owns a non-degenerate five-leg carrier, computes the unwired state as $\Phi_1=2$, $\Gamma_2=1$, probes the live wired state as $\Phi_1=0$, $\Gamma_2=0$, and delegates classification to the shared runtime. `tests/common/mod.rs` reuses that production carrier/certificate, while `tests/gtoc_adapter.rs` supplies the shared-runtime negative and partial-regression controls. This earns the current `ExactRepair` evidence classification without implying authority.

**Boundary ledger (explicit non-silent residuals):**

* `verified-boundary: PAPER023-SAFETY-CTRL-HALT-MONOTONE` — finite Boolean-shadow theorem; `#print axioms` is empty.
* `verified-boundary: PAPER023-SAFETY-CTRL-DRILL-IMPLIES-WITNESS` — `Activated` carries the same passing witness admitted by the finite gate; `#print axioms` is empty.
* `verified-boundary: PAPER023-SAFETY-CTRL-TAMPER-IMPLIES-HALT` — finite Boolean post-watch theorem; `#print axioms` is empty. No claim about Rust/OS semantics is inferred from this shadow.
* `defer: SUCCESSOR-FINDINGSTREAM-PACKET` — if the Integrity Auditor / Adversary / Blackrod surface types ever require a NEW public typed-find variant for halt-class membership, that change is out of scope here and deferred to a sibling packet `sentinel_councils_findingstream_packet.md`. The current sprint consumes the surfaces unchanged.
* `runtime-closed: NDEC-REPLAY-LEDGER` — `PersistentDrillLedger` supplies durable, locked, replay-validated, synced receipts and is exercised by the live shared-runtime probe.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `core_safety_controller::gtoc_adapter::evaluate_safety_controller` constructs `GtocExactInput` and calls `core_pipeline::gtoc_gtla::evaluate_exact`; persistent drill-ledger and focused adapter tests are present. The PaperAE005 Lean boundary is evidence-only, and production convergence plus separate promotion remain owned by `S16-005`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census records the current packet hash and source manifest.
