---
title: "Core Obstruction Packet (ODP) — The Universal Standard"
subtitle: "Cohomology as the operating system, not a domain object"
author: "Jeremy H. Carroll"
date: "2026-06-20"
status: "DOCTRINE / OPERATING STANDARD. Every Core artifact is an obstruction-descent problem; no artifact is promoted without its packet."
---

0. The core sentence
--------------------

> **Engine does not choose proposals. It computes, estimates, or refuses obstruction descent.**

Cohomology is not a thing the engine studies. It is the form in which the engine does *everything*. A proof, a Rust patch, a governance decision, a sprint item, a paper, a product feature, an ENC entry — each is **the same cochain problem** over a different carrier.

Conventions (packet algebra)
----------------------------

**A1 — Per-defect within the window.** A single 2-window may carry more than one defect.
Steps 8–10 and 13 ($\Gamma_2$, $\Phi_1$, classification, terminal status) are computed **per
defect**, not once for the whole packet: the same window can be *exact repair* for one defect
($\Phi_1 = 0$) and *no rule* for another ($\Phi_1 > 0$). When more than one defect is in play,
report $\Gamma_2$, $\Phi_1$, the classification, and the terminal as a small table keyed by
defect; a single value is just the one-defect special case.

**A2 — Packets come in bundles.** A multi-result artifact (a multi-theorem paper, a feature
with several invariants) maps to a **bundle**, not one packet: one *load-bearing descent
packet* carrying the window's $d_0 \to d_1$ flow, plus supporting *context-exposure
lemma-packets* (DDA `C`) that establish the carrier / norm / gauge the descent packet relies
on but are not themselves steps in its flow. Declare the bundle and mark which packet is
load-bearing; do not force a many-result artifact into a single packet.

*(Both conventions were surfaced by the pub-010 → GTOC migration — see
`../migrations/paper010_born_normalization_obstruction_packet.md`.)*

**A3 — Oracles are not operations.** Imported representation theorems (e.g., Gleason, Hilbert space, Born ontology) are not DDA operations. A transformation licensed from outside the declared finite 2-window is an **import/oracle**, and triggers the `OracleNeeded` terminal status.

**A4 — Current vs target terminal status.** Every packet with proposed implementation must separate: Current terminal, target terminal, and seal condition.

**A5 — DDA alphabet registry.** Packets may not invent DDA operation letters unless the alphabet is extended here. The official DDA operation classes are: `E` (Exact repair), `R` (Residual projection), `C` (Context exposure), `I` (Integration / DDA-log append), `Λ / Meta` (Lift / structural extension), `D` (Descent), `M` (Mutation/refusal), and `T` (Terminalization).

**A6 — Q is a debt, not a terminal.** `Q-held` is not a final status; it is an *obligation to descend*. Admission to Q requires, declared up front: (1) a **named finite shadow**, (2) a **convergence / refinement-certificate route** that would promote the shadow, and (3) a **descent trigger** (when the debt comes due). A candidate that cannot name all three does **not** enter Q — it is **typed Refusal** (`No rule`). An un-discharged Q debt past its trigger is downgraded by GTLA to `Refused`: *"held in Q" without a live descent obligation is bullshit, and the framework says so.* This is exactly what keeps Q from becoming a god-of-the-gaps attic — God, Zeus, consciousness, or "the continuum as ontology" have no finite shadow and no certificate route, so they are **refused, never held**. The continuum is welcome in Q *only* as the certified limit of finite shadows (e.g. the `Zₙ → U(1)` refinement of §9–10), never as an un-descended deposit. GTOC/GTLA require descent — you terminalize (`Repaired` / `Lifted` / `Refused`, or `Q-held` with a *live, dated* descent debt) or you are bullshitting.

The defect this standard repairs: the workflow has been
`prompt → proposals → adversarial review → judgment by another LLM → prose plan`
— a governance wrapper around LLM arbitration. The correct spine is
`Primitive Difference → cochains → quotient → obstruction → lift → terminalization`.
Adversarial review is **not** abandoned; it becomes **one operator** inside the cochain pipeline (an attempted `d₁` / `Γ₂` exposure).

1. The packet
-------------

An **Obstruction Descent Packet (ODP)** is the canonical typed carrier for any task. Minimum required fields:

| Field | Meaning |
|-------|---------|
| **Carrier** | the support window: the finite object the task lives over (dimension/index set, file/crate set, epic/role set, claim set, …) |
| **C⁰** | local assignments (definitions/hypotheses; structs/contracts; capabilities; mark/address assignments) |
| **d₀** | the **primitive-difference** operator: the permitted move from C⁰ that should leave "no difference" (derivation; refactor; gauge/rephasing; process) |
| **C¹** | the difference / **defect** layer: where d₀ fails to cancel (proof gaps; failing tests; blockers; unbiasedness defects) |
| **ZeroRel** | the gauge / equivalence relation that declares what counts as "zero difference" (exact equality, certified-interval zero, algebraic zero) |
| **B¹ = im(d₀)** | defects **removable** by the allowed move (closable by existing lemmas / local refactor / gauge) |
| **Q¹ = C¹ / im(d₀)** | the **irreducible** residual after all allowed repairs (genuine proof obligations / non-local failures / non-removable obstruction class) |
| **d₁** | the closure / compatibility operator (cocycle closure across overlaps; cross-crate integration coherence; cross-epic consistency) |
| **C²** | the closure / compatibility layer that `d₁` lands in |
| **Φ₁** | the **quotient obstruction mass** (per defect, A1): the size of `Q¹` under the observer norm |
| **Γ₂** | the **closure-failure mass** (per defect, A1): the size of `d₁`-failure (non-commuting square; failure to glue local certificates globally) |
| **observer / norm / terminalizer** | the declared lens that *measures* Φ₁/Γ₂ and the gate that *seals* a terminal status (no measurement without a declared observer; no seal outside the terminalizer) |
| **Λ** | lift candidates — admissible structure-adding moves, proposed **only if the obstruction licenses a lift** (`h ∉ im(d₀)`): new definition/lemma/witness; new trait/carrier/validator; field extension/cover refinement |
| **DDA operation ledger** | the recorded class of every transformation applied (discrete deformation calculus) — what was done, and what it preserved |
| **terminal status** | the sealed outcome: ExactRepair / ClosedSurvivor / ActiveClosureFailure / NoRule / LiftNeeded / Refusal / OracleNeeded / OpenResidual |

**Partial-packet rule:** no research question, proof task, governance question, sprint item, or product feature is *entered into the engine* until it has at least a **partial** version of this packet (carrier + C⁰ + d₀ + a first C¹ is the floor).

2. The crate binding (this is the OS, not prose)
------------------------------------------------

Each field binds to the Rust machinery that computes it. **Pinned 2026-06-20** against real source (binding-pin pass): **All 14 fields bind to a live type**. This standard is wired, not prose.

| Field | Rust binding (`type` — `file:line`) | Status |
|-------|--------------------------------------|--------|
| Carrier | `CochainPrimitiveDifference::Carrier = Vec<Q>` — `core_homology/src/cochain_primitive_difference.rs:34` | pinned |
| C⁰ / C¹ / C² | `CochainComplex.{c0_dim,c1_dim,c2_dim}` — `core_homology/src/cochain_complex.rs:56–60` | partial (dims, not first-class groups) |
| d₀ / d₁ | `CochainComplex.{d0,d1}: CoboundaryMap` — `cochain_complex.rs:62,64` (`coboundary.rs:12`) | pinned |
| ZeroRel / primitive difference | `CochainPrimitiveDifference::zero` — `cochain_primitive_difference.rs:45`; Lean `CoreCore.PrimitiveDifference.ZeroRel` — `lean4/PrimitiveDifference.lean:24` | pinned |
| B¹ = im(d₀) | `rank_coboundary(complex,0)` — `core_homology/src/cohomology.rs:41` (column space of `d0.matrix`; no reified type) | partial |
| Q¹ = C¹/im(d₀) | `QuotientSpace<K>` / `QuotientClass<K>` (`ModImageOfBoundary`) — `core_homology/src/quotient.rs:37,81,11` | pinned |
| Φ₁ (quotient mass) | `TerminalBranchResult.phi1` — `core_homology/src/residual_gate.rs:34`; exact `VerifiedExactPhi1` — `core_functional/src/phi1.rs` | pinned |
| Γ₂ (closure mass) | `gamma2_normalized` — `core_homology/src/transition_scorer.rs:341`; exact `ExactGamma2Result` — `core_functional/src/gamma2.rs` | pinned |
| observer / norm | `Observer` / `ObserverKind` — `core_functional/src/observer.rs:53,15`; norm `boundary_residual_l1` — `core_homology/src/residual_gate.rs:31` | pinned |
| Λ lift candidates | `FaceLambda<F>` / `FiniteLambdaStepCertificate` — `core_discrete_deformation_algebra/src/lib.rs:31,434`; lifting problems — `core_lifts` | pinned |
| **DDA operation ledger** | `FiniteLambdaLedger` — `core_discrete_deformation_algebra/src/lib.rs` | pinned |
| terminalizer / terminal status | `ObstructionStatus` — `core_functional/src/trichotomy.rs:16`; sealed `Decision` — `core_sweep_kernel/src/terminalize.rs:32`; `AuthorityTerminal` — `core_types/src/authority.rs:46`; `certify_checked_packet` (7 IsAuth guards) — `core_certifiers` | pinned |
| evaluator defect Δ_E (a C¹ instance) | `Delta_E ∈ {−1,0,+1}`, G1–G4, `EpkResidualLedger` — `core_epk` | pinned |
| diagnostic-only firewall | `authority_effect = None` everywhere; only `terminalize_row`/`certify_checked_packet` mints | pinned |

### 2.1 Build backlog (optional reifications)

| Field | Missing | Build action |
|-------|---------|--------------|
| C⁰/C¹/C² group | groups are only `usize` dims on `CochainComplex` | *optional* `CochainGroup { degree, dim }` — low priority (dim+matrix is sound) |
| B¹ = im(d₀) | image has no standalone type | *optional* `BoundarySubspace { degree, basis, rank }` — not blocking |
| unified PreservationWitness | split across `NonDestructiveExtensionCertificate` / `LiftForgetFixedPoint` / `ObserverPassivityCertificate` | *optional* `enum PreservationWitness` over the three — **do not collapse semantics** |

3. The mandatory workflow spine
-------------------------------

Replace `ask three models and compare answers` with: *force each answer into C¹, then test whether it is exact, surviving, actively broken, or lift-requiring.*

1. Declare **carrier**.
2. Declare **C⁰**.
3. Declare **d₀**.
4. Emit **C¹** defects.
5. Declare **ZeroRel / gauge**.
6. Compute or estimate **Q¹** (= C¹ / im(d₀)).
7. Declare **d₁**.
8. Compute **Γ₂**.
9. Compute or estimate **Φ₁**.
10. **Classify** the residual: `ExactRepair` · `ClosedSurvivor` · `ActiveClosureFailure` · `NoRule`.
11. Propose **Λ** *only if* the obstruction licenses a lift (`h ∉ im(d₀)`), and state **what the lift preserves**.
12. Record the **DDA operation**.
13. **Terminalize** (seal the terminal status through the terminalizer).

4. The role of LLMs (candidate generators, never judges)
--------------------------------------------------------

LLMs may not evaluate authority. They emit candidate cochains:

| LLM act | ODP meaning |
|---------|-------------|
| proposal | candidate `h ∈ C¹` |
| adversarial review | attempted `d₁` / `Γ₂` exposure (does this expose a non-removable residual or a closure failure?) |
| repair suggestion | candidate `α` with `h − d₀α` smaller |
| lift suggestion | candidate `Λ` when `h ∉ im(d₀)` |

Stop asking *"which proposal is best?"* — ask *"which residual survives quotient and closure?"* Stop asking *"which critique is strongest?"* — ask *"which critique exposes nonzero Γ₂ or nonzero Q¹?"* Stop asking *"should we add structure?"* — ask *"which obstruction licenses Λ, and what does the lift preserve?"*

5. Terminal classification
--------------------------

(Classify per defect — A1. A window with several defects gets one row each.)

| Terminal | Condition |
|----------|-----------|
| **ExactRepair** | `h ∈ im(d₀)` under ZeroRel — closed by an allowed move; `Φ₁ = 0`, `Γ₂ = 0` |
| **ClosedSurvivor** | `Q¹` nonempty but compatible (`Γ₂ = 0`); a stabilized residual held within declared scope |
| **ActiveClosureFailure** | `Γ₂ ≠ 0` — local repairs do not glue; a non-commuting square / contextuality obstruction |
| **NoRule** | no admissible `d₀`/`Λ` applies; the carrier is under-specified |
| **LiftNeeded** | `h ∉ im(d₀)` and a licensed `Λ` exists — descent continues after the lift |
| **Refusal** | the obstruction is real and no lift is licensed; honest stop (not a failure to route around) |
| **OracleNeeded** | resolution requires evidence/computation outside the declared carrier (undecidable in-scope) |
| **OpenResidual** | a declared, replayable residual carried forward with routed work |

Terminal status is **sealed only by the terminalizer** (`core_sweep_kernel`/`core_certifiers`); an LLM, a council vote, or a score never seals it.

6. The promotion gate (governance)
----------------------------------

> **No Core artifact may be promoted unless it declares its obstruction packet.**

**Promotion** = paper release · Lean theorem claim · Rust module claim · sprint epic · product feature · public post · ENC entry.

**Required promotion checklist** (each item present or explicitly out-of-scope-with-reason):

* [ ] carrier declared?
* [ ] C⁰ declared?
* [ ] C¹ declared?
* [ ] d₀ declared?
* [ ] ZeroRel declared?
* [ ] Q¹ declared or refused?
* [ ] d₁ / C² declared or explicitly out of scope?
* [ ] Φ₁ / Γ₂ declared or marked unavailable?
* [ ] lift candidate declared only if licensed?
* [ ] terminal status assigned?
* [ ] DDA operation recorded?

If not, the artifact is still **representation-layer prose** and is not promoted. This checklist supersedes "ask three models and compare." It should be referenced from `CLAUDE.md` and wired into the paper-release, Lean-signoff, sprint-planning, and ENC-entry gates.

7. First conversion test (the binding discharge)
------------------------------------------------

The standard is not done until one active task is forced into a real packet and the bindings are pinned. **This is done.** The first test — **SPK-COSMO-003** — was converted; the full worked packet is in [`spk_cosmo_003_packet.md`](spk_cosmo_003_packet.md), grounded in the live Lean artifact.

SPK-COSMO-003 is **not** a paper — it is the live collapse test of candidate F ("modal addressability / unreified selection"), defined self-contained in [`spk_cosmo_003_packet.md`](spk_cosmo_003_packet.md) (Appendix; consolidated from the retired 2026-06-19 troika review): does the weakest modal/existential addressability structure stay *below* a carrier, or collapse into a directed-incidence `CarrierSkeleton`? The complete 15-field packet, all bound to real types:

```
Carrier    : Address ⊎ Mark bipartite carrier (AddressabilityThreshold.lean) — CochainPrimitiveDifference;
             pre-collapse the candidate is UnaryAddressability {addressable: Mark→Prop} (line 47), exposing NO carrier — that absence IS the test
C⁰         : address/mark vertices = Carrier of CarrierSkeleton (AddressabilityThreshold.lean:29) — CochainComplex.c0_dim
d₀         : incidence coboundary CochainComplex.d0:CoboundaryMap — edges = matched address/mark witness pairs
             (predicate_to_skeleton/modal_relation_to_skeleton, lines 65–91); a binary Address→Mark→Prop relation SUPPLIES d₀ (no Classical.choice)
C¹         : edge set Σa {m // matchesRel a m} (line 68) — CochainComplex.c1_dim
ZeroRel    : d ∈ im(d₀) — CochainPrimitiveDifference::zero (exact over ℚ via solve_in_image); Lean CoreCore.PrimitiveDifference.ZeroRel
B¹ / Q¹    : Q¹ = C¹/im(d₀) — QuotientSpace/QuotientClass (ModImageOfBoundary{degree:0}); Q¹ vanishing decides "collapsed into CarrierSkeleton"
d₁ / C²    : CochainComplex.d1 enforces d₁∘d₀=0 (CochainComplexWitness); C² (c2_dim) empty for the binary-collapse result
Φ₁ / Γ₂    : binary case Φ₁=0 (VerifiedExactPhi1), Γ₂=0 (clean collapse over the skeleton)
observer   : Observer/ObserverKind (core_functional/observer.rs); norm = boundary_residual_l1
Λ          : FaceLambda<F> — the "derive directed incidence" deformation, witnessed by NonDestructiveExtensionCertificate (lib.rs:405)
DDA ledger : the chained collapse (functional/predicate/modal → skeleton) — pending the FiniteLambdaLedger build (§2.1)
terminal   : ObstructionStatus. Binary case (PL-SPK-COSMO-003-1, DISCHARGED 2026-06-20, AddressabilityThreshold.lean, axiom-free):
             ExactRepair (Φ₁=0) ⇒ candidate REFUTED. Unary case (003-4, OPEN/GATING): UNDECIDED — ExactRepair (collapses, refuted)
             vs StabilizedSurvivor/OpenObstruction (genuinely below carrier)
```

**Firewall (honored):** this is a *synthesis*, not a new repo artifact; `CertifiedAuthority` is **not** invoked. Per the SPK-COSMO firewall (`spk_cosmo_003_packet.md` Appendix), SPK-COSMO-003 is **not promoted** past `F1 / ShapeOnly` until 003-4 has a Lean witness — an F1 prose packet mints no ENC entry and no authority. Each model proposal is just a candidate `h ∈ C¹`, tested for survival under quotient (`Q¹`) and closure (`Γ₂`).

8. Functorial views (the GT* tower)
-----------------------------------

The GT* names are **not** labels over prose; each is a functorial view of the *same* ODP:

| View | What it is over the ODP |
|------|--------------------------|
| **CODA-FOC** | the finite `C⁰ → C¹ → C²` obstruction calculus (the packet's core) |
| **GTLA** | authority = a **terminalized descent** over the packet (nothing else mints authority) |
| **CODA-MUR** | transport / representation / observer mismatch as a cochain **transport-square** obstruction |
| **CODA-OR** | the operator registry over admissible obstruction-reducing moves (the legal `d₀`/`Λ` set) |
| **CODA-A** | trace / terminal-authority accounting over **replayable residual histories** |
| **GTC** | closure / contextuality / gluing discipline (`d₁`/`Γ₂`) |

A paper that uses one of these names **without declaring the carrier, cochains, maps, observer, and terminalizer is marked incomplete.**

9. How this reframes the platform (session continuity)
------------------------------------------------------

* The umbrella's *"packetize a difference into a typed carrier"* — that carrier **is** the ODP.
* `core_prompt_packets`' `PromptShape` is a **degenerate ODP** (C⁰ only, no obstruction layer). Its deferred "v2 homological signature" is exactly this packet's `Φ₁`/`Γ₂`/`Q¹` fields — they are the same object.
* EPK / LGGR is the **evaluator-defect** instance of C¹ (`Δ_E`), with G1–G4 as the closure conditions.
* A **sprint item** is a governance ODP: it exists only because it kills or routes a named residual.
* The platform's "O(1) dream" is content-addressed retrieval over **matched ODPs** in the DDA composition library — earned per-class, not asserted.

10. Adapters
------------

This universal standard is specialized by three domain adapters (same packet, domain-specific C⁰/d₀/Λ/terminal):

* `proof_obstruction_packet.md` — a proof is obstruction removal; a Lean file is a residual-killing ledger.
* `rust_obstruction_packet.md` — a feature is obstruction management over executable carriers; a PR reports `Φ₁`/`Γ₂` before/after + lift used + preservation witness.
* `governance_obstruction_packet.md` — governance is obstruction routing; a sprint item kills or routes a named residual.

11. Bad packet examples (anti-patterns)
---------------------------------------

Every packet must be checked against the following anti-patterns. An illegal packet is immediately rejected at the promotion gate:

### Example 1: No carrier
```text
C⁰: my Rust functions
d₀: refactoring
...
```
*Why it is illegal:* It fails to specify the support window. There is no finite object (such as a crate, file range, or set of types) over which the cochains are defined.

### Example 2: No $d_0$
```text
carrier: core_api crate
C⁰: Axum router and handlers
C¹: no type-safety on body
...
```
*Why it is illegal:* It declares defects ($C^1$) but no primitive-difference operator $d_0$. Without $d_0$, there is no gauge relation, no boundary $\operatorname{im}(d_0)$, and no quotient space projection. A defect cannot be resolved or identified without its allowed gauge moves.

### Example 3: No per-defect table
```text
C¹: D_packetize, D_route
Φ₁: 2
Γ₂: 1
terminal: Repaired
```
*Why it is illegal:* Violates **A1**. Aggregate values mask individual defect state. A single 2-window must report $\Phi_1$, $\Gamma_2$, classification, and terminal status in a table keyed by each individual defect class. One defect can be resolved while another is deferred or active closure failure.

### Example 4: Oracle logged as DDA op
```text
DDA operation:

  1. import representation theorem (Gleason's theorem)
  2. apply Gleason's theorem to select U(1)
```
*Why it is illegal:* Violates **A3**. Representation theorems or external mathematical frameworks are not DDA operations. They are oracle imports, which must be declared in the oracle/import section and trigger the `OracleNeeded` terminal status, not masqueraded as local DDA steps.

### Example 5: Q-held with no descent trigger
```text
terminal: Q-held
note: held in Q until we figure out the continuum limit
```
*Why it is illegal:* Violates **A6**. `Q-held` is debt, not a terminal. Every admission to Q must declare a named finite shadow, a convergence/refinement-certificate route, and a live, dated descent trigger. Lacking these, the packet must be classified as a `Refusal` (`No rule`).

### Example 6: Terminal claimed without seal
```text
terminal: Repaired
```
*Why it is illegal:* Violates **A4** and the firewall. The packet text/markdown itself does not mint authority or seal status. The terminal section must separate Current terminal, target terminal, and the explicit authority-minting seal condition (e.g. `terminalize_row` or `certify_checked_packet`). The status becomes "Repaired" only after the seal condition actually executes and passes.

---

*This standard is the operating system. If we follow it, the system becomes itself; if we do not, we are using obstruction language around ordinary prompt engineering.*

