packet_type: implementation
authority_effect: None
carrier: CochainPrimitiveDifference / CochainComplex shape signatures (C⁰)
primary_residual: missing durable shape-keyed registry (Q¹)
in_scope_repairs: ShapeSignature newtype, ResidualClassRecord lookup FamilyRegistry (d₀)
deferred_residuals: consumer-side lookup wiring into solver/EPK/Symbol Game (core_residual_families_wiring_packet.md)
seal_condition: terminalize_row returning Decision::Certified on registry crate rows

Core Residual Families Registry (Obstruction Packet)
=====================================================

**Date:** 2026-06-20
**App:** `core_residual_families` (greenfield crate under `engine/crates/`)
**Role:** Hashed-shape registry of recognized residual classes; lookup by signature returns prior $Q^1$/$\Gamma_2$ class hits without minting authority.

**Bundle status (A2):** load-bearing, no sibling lemma-packets.

**Defect roster:** This packet carries a single defect:

* `D1` (RF-NO-REGISTRY): Solver / EPK / Symbol Game call sites rediscover the same shape-keyed residual classes every run because no durable shape-keyed registry exists.

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The diagnostic carrier formed by the cochain shape signature of
`core_homology::cochain_primitive_difference::CochainPrimitiveDifference`
instances emitted by `core_homology::cochain_complex::CochainComplex::d0`
and `::d1`. The 2-window inspects the local pair
$(\sigma(Q^1), \sigma(\Gamma_2))$ where $\sigma$ is a `blake3`-derived
shape-only signature over the primitive-difference structure (face indices,
arity, coefficient-domain tag, quotient-class id from
`core_homology::quotient::QuotientSpace`), and where the right-hand window
slot is the diagnostic mass pair
$(\Phi_1, \Gamma_2)$ produced by
`core_functional::phi1::VerifiedExactPhi1` and
`core_functional::gamma2::ExactGamma2Result` under a fixed
`core_functional::observer::Observer`. The carrier deliberately discards
raw cochain payload bytes: the signature key is the only persisted shape
fingerprint.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** No crate yet exists. The local assignments are
(a) the existing in-tree types
`CochainPrimitiveDifference`, `QuotientSpace`,
`core_functional::phi1::VerifiedExactPhi1`,
`core_functional::gamma2::ExactGamma2Result`,
`core_functional::observer::Observer`,
and (b) the empty crate skeleton `engine/crates/core_residual_families/`
to be added as a workspace member with a `ShapeSignature` newtype, a
`ResidualClassRecord { signature, q1_class_id, gamma2_class_id, hits: u64 }`
struct, and a `FamilyRegistry` lookup table keyed by `ShapeSignature`.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** Permitted shape-preserving rewrites of the
signature computation: re-ordering of internal serialization fields under a
deterministic canonicalization that preserves the `blake3` digest, renaming
of internal field accessors, and any refactor of `FamilyRegistry` storage
that preserves the lookup contract
`fn lookup(&self, sig: &ShapeSignature) -> Option<&ResidualClassRecord>`
and the contract
`fn record(&mut self, sig: ShapeSignature, q1: Q1ClassId, g2: Gamma2ClassId) -> RegistryWrite`.
This is the gauge lambda for the crate; no public-API drift, no payload
widening.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** Every solver loop, EPK diagnostic
pass, and Symbol Game candidate-generation pass rediscovers the same
$Q^1$/$\Gamma_2$ class fingerprints from scratch. There is no durable place
to store recognized residual classes; the carrier emits the same
`CochainPrimitiveDifference` shape signature repeatedly without recall.
Concretely: `core_functional::phi1::VerifiedExactPhi1` and
`core_functional::gamma2::ExactGamma2Result` compute classes that have
been seen, but the system has no map from shape signature to a prior class
record, so cross-session learning is impossible and the same residual
families are re-derived every run.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two `CochainPrimitiveDifference` instances are
identified iff their canonicalized shape signature
$\sigma : \text{CochainPrimitiveDifference} \to \text{blake3 digest}$
agrees. Equivalently: differences that vary only by
`core_homology::cochain::Cochain` coefficient values, internal field
ordering, or `core_functional::observer::Observer`-local naming, but that
share the same face-index pattern, arity, coefficient-domain tag, and
`QuotientSpace`-id, are gauge-equivalent for registry purposes. ZeroRel is
exactly the kernel of $\sigma$.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** $C^1 / \mathrm{im}(d_0)$ is the
shape-only residual class: the equivalence class of cochain-primitive-
difference signatures that survives shape-preserving rewrites. The primary
$Q^1$ that this crate must materialize is a hashed-shape-only registry
table mapping `ShapeSignature` to a `ResidualClassRecord` carrying the
prior `Q1ClassId` and `Gamma2ClassId` hit, plus a hit counter. The raw
cochain text or coefficient payload is NOT part of $Q^1$ here; the
registry deliberately stores only the shape digest.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** Cross-call coherence of registry hits.
For every pair of lookups that return `Some(record)` on the same
`ShapeSignature` within and across sessions, the returned
`(q1_class_id, gamma2_class_id)` pair MUST be stable. $d_1$ is the
requirement that `FamilyRegistry::lookup` is a function (single-valued)
of the signature key and that round-tripping the same input
`CochainPrimitiveDifference` through $\sigma$ twice yields byte-identical
keys.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass) — per defect (A1):**

| Defect | $\Gamma_2$ | Witness |
|---|---|---|
| D1 (RF-NO-REGISTRY) | count of registry lookups that return inconsistent `Q1ClassId` / `Gamma2ClassId` values on the same `ShapeSignature` (shape-key collision with disagreeing class hits), plus the count of round-trip failures where the same input shape produces different signatures across calls, plus the count of cross-instance / cross-observer disagreements (two `VerifiedExactPhi1` instances built from gauge-equivalent `ExactPhi1Certificate`s on the same shape differing only by `alpha` / `primal_residual` choices, or two distinct `Observer` values — `Projection` vs `Precision` kinds — on the same shape, that yield different local `Q1ClassId`). | Target: $\Gamma_2 = 0$ under three known shape-collision tests AND the cross-instance / cross-observer stability test (S7b). |

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass) — per defect (A1):**

| Defect | $\Phi_1$ | Witness |
|---|---|---|
| D1 (RF-NO-REGISTRY) | `core_functional::phi1::VerifiedExactPhi1` mass attributable to the absence of the registry: every solver run that re-derives a residual class already seen contributes one unit. System-wide $\Phi_1 = 0$ requires BOTH (i) the crate shipping with its lookup surface AND (ii) the lookup being wired into the existing residual-emitting call sites in `core_solvers`, `core_epk`, `pfp`. (ii) is explicitly out of scope; tracked as `defer: PD-RF-PHI1-WIRING` -> successor packet `core_residual_families_wiring_packet.md` (not yet authored). | This packet ships only the lookup surface and the in-crate $\Gamma_2 = 0$ collision-stability proof. The in-crate measure shipped is `registry_hit_recurrence` (count of shape keys with `hits >= 2`); it quantifies registry exercise and is explicitly NOT a $\Phi_1$ measurement. Any sprint or downstream artifact that conflates the two must be rejected by the adversary gate. |

10. Classify System State
-------------------------

**Classification — per defect (A1):**

| Defect | Class |
|---|---|
| D1 (RF-NO-REGISTRY) | `LiftNeeded` (Closed survivor requiring structural Meta) |

The defect is the absence of a durable shape-keyed registry. The resolution requires a structural lift ($\Meta$) to introduce the new crate `core_residual_families` into the workspace, as a new crate is a structural extension rather than a local refactor ($d_0$ move). The repair preserves all existing contracts and adds a new diagnostic-only lookup surface.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**$\Meta$ (Lift/Structural Extension):** Introduce the greenfield diagnostic crate `core_residual_families` as a structural extension to the workspace.

$$\Meta \;=\; \mathtt{FaceLambda::new("residual\_families\_registry\_introduction",\ capacity)}$$

The lift candidate is licensed because adding a new greenfield diagnostic crate is a structural extension, not a local refactor. The `NonDestructiveExtensionCertificate` verifies:

* `preserves_old_vertices: true` (all existing workspace crates build unchanged)
* `preserves_old_edges: true` (no existing crate's public API is mutated or broken)
* `records_tradeoff: true` (the lookup is strictly diagnostic and does not alter the authority interfaces)

**Oracles required (A3):** none. The packet relies on no imported representation theorem. Every transformation lives inside the declared finite 2-window.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus) — canonical alphabet (A5) {E, R, C, I, Meta/Lambda, D, M, T}:**

* `Meta` / `Lambda` (Lift / structural extension): Apply the `FaceLambda` to introduce the new `core_residual_families` crate as a workspace member.
* `E` (Exact repair): gauge repair over the `ShapeSignature` canonicalization, ensuring deterministic byte-identical digests under $d_0$.
* `R` (Residual projection): quotient projection realizing `CochainPrimitiveDifference -> ShapeSignature`.
* `C` (Context exposure): lookup application realizing `FamilyRegistry::lookup`, which exposes prior shape-keyed class hits to the caller without minting authority.
* `I` (Integration / DDA-log append): record append realizing `FamilyRegistry::record`, which appends a new shape-keyed record (or increments `hits`) into the registry.

Wiring binding: the crate lives at `engine/crates/core_residual_families/`, depends on `core_homology` and `core_functional`, and is consumed (in a successor packet) by `core_epk` as a diagnostic-only lookup. The crate mints no authority; only `core_sweep_kernel::terminalize_row` and `core_certifiers::certify_checked_packet` ever seal a terminal, and this crate is not on that path.

13. Terminal Status
-------------------

**Terminal status — per defect (A1) with A4 split (Current / Target / Seal Condition):**

| Defect | Current | Target | Seal Condition |
|---|---|---|---|
| D1 (RF-NO-REGISTRY) | Open: no crate exists; every solver / EPK / Symbol Game pass re-derives shape-keyed residual classes from scratch. | Repaired (in-crate $\Gamma_2 = 0$). | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the row that asserts (a) the `core_residual_families` crate is a workspace member that builds under `cargo build -j 1`, (b) a canary-grep test proves no raw cochain payload is persisted (signature-only storage), (c) three round-trip tests on known shape collisions return $\Gamma_2 = 0$ and witness $d_1$ single-valuedness, and (d) the cross-instance / cross-observer stability test (S7b) returns $\Gamma_2 = 0$, proving the local `Q1ClassId` derivation depends only on shape-relevant accessors of `VerifiedExactPhi1` / `ExactGamma2Result`. |

**Deferred residuals (declared, not silent):**

* `defer: PD-RF-PHI1-WIRING` -> successor packet
  `core_residual_families_wiring_packet.md` (not yet authored). System-
  wide $\Phi_1 = 0$ for the registry's $Q^1$ requires consumer-side
  wiring of `FamilyRegistry::lookup` into `core_solvers`, `core_epk`,
  and `pfp`; that wiring is explicitly out of scope here
  (packet section 9). The in-crate measure that this packet does ship is
  `registry_hit_recurrence` (count of shape keys with `hits >= 2`),
  which is NOT a $\Phi_1$ measurement.

Authority is NOT minted by this packet or by the crate; the markdown and
the crate are diagnostic-only. Only `core_sweep_kernel::terminalize_row`
and `core_certifiers::certify_checked_packet` ever seal a terminal.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, the registry remains the canonical family owner and `core_solvers::phi1::gtoc_adapter::solve_phi1_gtoc` constructs a shared exact input and calls `core_pipeline::gtoc_gtla::evaluate_exact`; solver and EPK wiring tests are present. Completion of all declared consumers and a current packet terminal remain owned by `S16-004`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census records the current packet hash and source manifest.

15. S16-004 all-declared-consumer disposition
---------------------------------------------

At frozen base `46d91fb4165e6cb83fbb8c41168ed56739db478e`, S16-004 packet `01bd1e82e29810bf940ae962ebf3b50c87b54ba79dfd42a1d9dedfedc8f55e7b` verifies that solvers, EPK, and Symbol Game consult `core_residual_families` only after their shared exact classification. Symbol Game now derives the canonical shape signature, admits only closed residuals, and performs lookup-only resolution. An unknown family id is not inserted and routes to `LiftLicenseNeeded`.

Focused wiring receipts pass for solvers (3), EPK (1), and Symbol Game (2). Registered admitted fixtures reach `ExactRepair`, all outputs retain `AuthorityEffect::None`, and no consumer mints authority. This closes the named three-consumer wiring residual, not completeness of the family registry or arbitrary future consumers.
