---
title: "SPK-COSMO-003 — first conversion worked packet (ODP)"
subtitle: "The modal-addressability collapse test as an Obstruction Descent Packet"
author: "Jeremy H. Carroll"
date: "2026-06-20"
status: "WORKED EXAMPLE / binding discharge for core_obstruction_packet_standard.md §7. F1 / ShapeOnly — NOT promoted (see firewall)."
---

What SPK-COSMO-003 actually is (grounded)
-----------------------------------------

SPK-COSMO-003 is **not** a published paper or crate. It is the live research task defined by candidate **F** ("modal addressability / unreified selection") from SPK-COSMO-002 — a scoped **collapse test**: *does the weakest modal/existential addressability structure (no total function, selector, source/target map, graph, path relation, or declared carrier) stay below `CarrierStructure`, or collapse into a directed-incidence `CarrierSkeleton`?* Candidate F and the collapse-test prompt are defined self-contained in the **Appendix** below (consolidated from the now-retired 2026-06-19 troika review).

Sub-task status (`proof_ledger_20260619.md`):

* **003-1** — DISCHARGED 2026-06-20 by `lean4/002_finite_obstruction_calculus/002_the_sentinel_boundary/CoreCosmology/Ontology/AddressabilityThreshold.lean`: `functional_to_skeleton` / `predicate_to_skeleton` / `modal_relation_to_skeleton` collapse **binary** relations into a `CarrierSkeleton` **without `Classical.choice`** (axiom-free, `#print axioms` lines 117–120). **Source missing (checked 2026-09-29):** `AddressabilityThreshold.lean` is in neither this repository nor its history, and no `.lean` file here declares `functional_to_skeleton`, `predicate_to_skeleton`, `modal_relation_to_skeleton` or `UnaryAddressability`. The discharge above is the 2026-06-20 record; it cannot be replayed from this tree.
* **003-2** — DISCHARGED (PaperFOC000c §2.3 patch).
* **003-3** — DEFERRED (Rust fixture `spk_cosmo_modal_addressability_fixture`), blocked on 003-4.
* **003-4** — **OPEN / GATING CONJECTURE:** does `UnaryAddressability {addressable: Mark → Prop}` (`AddressabilityThreshold.lean:47`) support *represented difference* without reintroducing an address domain / selector / binary relation / carrier skeleton?

This packet is the operator-requested **synthesis** of that task over the ODP — not a pre-existing ODP-typed artifact.

The packet
----------

| ODP field | SPK-COSMO-003 instance (binding) |
|-----------|----------------------------------|
| **Carrier** | `Address ⊎ Mark` bipartite carrier built by `*_to_skeleton` (`AddressabilityThreshold.lean`); ODP carrier via `CochainPrimitiveDifference` (`cochain_primitive_difference.rs:34`). Pre-collapse the candidate is `UnaryAddressability {addressable: Mark→Prop}` (`:47`), exposing **no** carrier. |
| **C⁰** | address/mark vertices = `Carrier` of `CarrierSkeleton` (`:29`) — `CochainComplex.c0_dim`. **For the open unary candidate C⁰ is intentionally absent — that absence IS the test.** |
| **d₀** | incidence coboundary `CochainComplex.d0:CoboundaryMap` — edges = matched address/mark witness pairs (`predicate_to_skeleton`/`modal_relation_to_skeleton`, `:65–91`). A binary `Address→Mark→Prop` relation **supplies** d₀ constructively (no `Classical.choice`). |
| **C¹** | edge set `Σ a {m // matchesRel a m}` (`:68`) — `CochainComplex.c1_dim`. |
| **ZeroRel** | `d ∈ im(d₀)` — `CochainPrimitiveDifference::zero` (exact over ℚ via `solve_in_image`); Lean `CoreCore.PrimitiveDifference.ZeroRel` (`PrimitiveDifference.lean:24`). Decides whether an address/mark difference is already a coboundary of the incidence skeleton. |
| **B¹ = im(d₀)** | the coboundary image (`rank_coboundary`, `cohomology.rs:41`). |
| **Q¹ = C¹/im(d₀)** | `QuotientSpace`/`QuotientClass` (`ModImageOfBoundary{degree:0}`, `quotient.rs:37,81`). **Q¹ vanishing ⇔ "collapsed into `CarrierSkeleton`."** |
| **d₁ / C²** | `CochainComplex.d1` enforces `d₁∘d₀ = 0` (`CochainComplexWitness`); C² (`c2_dim`) empty for the binary-collapse result. |
| **Φ₁** | `VerifiedExactPhi1` (`core_functional/src/phi1.rs`) / `TerminalBranchResult.phi1` (`residual_gate.rs:34`). **Binary case Φ₁ = 0.** |
| **Γ₂** | `ExactGamma2Result` (`core_functional/src/gamma2.rs`) / `gamma2_normalized` (`transition_scorer.rs:341`). **Binary case Γ₂ = 0** (clean collapse). |
| **observer / norm** | `Observer`/`ObserverKind` (`core_functional/observer.rs`); norm `boundary_residual_l1` (`residual_gate.rs:31`). |
| **Λ** | `FaceLambda<F>` (`core_discrete_deformation_algebra/src/lib.rs:31`) — the "derive directed incidence" deformation, witnessed by `NonDestructiveExtensionCertificate` (`lib.rs:405`) / `FiniteLambdaStepCertificate` (`lib.rs:434`). |
| **DDA ledger** | the chained collapse (functional → predicate → modal → skeleton). **Pending the `FiniteLambdaLedger` build** (standard §2.1). |
| **terminal** | `ObstructionStatus` (`trichotomy.rs:16`). **Binary (003-1, DISCHARGED):** `ExactRepair` (Φ₁=0) ⇒ candidate **REFUTED** (collapses to `CarrierSkeleton`). **Unary (003-4, OPEN):** UNDECIDED — `ExactRepair` (collapses, refuted) vs `StabilizedSurvivor`/`OpenObstruction` (genuinely below carrier). |

Firewall (honored)
------------------

* This is a **synthesis**, not a repo artifact; `CertifiedAuthority` (`authority.rs:169`) is **not** invoked.
* Per the SPK-COSMO firewall (**Appendix** below), SPK-COSMO-003 is **not promoted** past `F1 / ShapeOnly` until **003-4** has a Lean witness — an F1 prose packet mints **no** ENC entry and **no** authority.
* This is **not** a claim that modal/unary addressability *is* below carrier. It is the obstruction-typed statement of the open question.

Next (when 003-4 unblocks)
--------------------------

1. Resolve 003-4 in Lean (does `UnaryAddressability` represent difference without an address domain/selector/binary relation?). The terminal flips to `ExactRepair` (refuted) or a genuine survivor.
2. Then 003-3: name the fixture `spk_cosmo_modal_addressability_fixture`, route it through `SgSession`/`FamilyDriver`, assert the `ObstructionStatus` per case — **do not** rewrite the Symbol Game core.
3. Only after a Lean witness may the result earn an ENC entry / terminal seal.

---

Appendix — Provenance & consolidated firewall (self-contained after retiring the troika review)
-----------------------------------------------------------------------------------------------

**Provenance (2026-07-15 consolidation).** Candidate **F** and the collapse-test prompt below originated in the *SPK-COSMO Troika Review* (2026-06-19), an exploratory Symbol-Game-loop emulation over the deep-origin question. That review has been **retired** (its superseded exploratory matrix — candidates A–E, the adversarial round table, and the score tables — is preserved only in git history); its two load-bearing, still-referenced parts are consolidated **here** so this packet is self-contained. This appendix is the canonical home for "candidate F" and "the SPK-COSMO firewall"; the packet standard (`core_obstruction_packet_standard.md` §7) and this file no longer depend on the deleted review.

**Relation to the canonical foundations (cross-link).** The 003-4 question — *does modal/unary addressability stay below carrier-Structure, or reconstruct it?* — is the SPK-COSMO instance of the canonical open obligation **PL-GTOC-GB1** (the Difference/Structure independence-or-inseparability question; `999_gtoc` charter §"The two root channels" + `genesis-bias` doctrine; `research/proof_ledger_20260715.md`). The discharged **003-1** result (functional / predicate / **modal** *binary* relations each collapse into a `CarrierSkeleton`, axiom-free) is a partial finding bearing on GB1: the *binary* forms do not stay below carrier; only the *unary* `UnaryAddressability {addressable : Mark → Prop}` form (003-4, OPEN) remains a live candidate for a difference-without-antecedent-carrier structure. GB1 and SPK-COSMO-003 should be worked as one question.

### Candidate F — Modal addressability / unreified selection (consolidated from troika review §6)

* **Thesis.** After *functional* addressability collapses into directed incidence, the remaining deep-origin candidate is *modal or existential* addressability that does not provide a function graph, selector, or carrier skeleton by construction.
* **What it explains.** Why the address layer is still worth testing even after `Address → Mark` fails as a lower-layer account.
* **What it refuses.** Total functions, selectors, named addresses as root authority, and any immediate claim that ProtoSupport is below carrier.
* **What it smuggles.** Modal access may still carry identity, persistence, multiplicity, or hidden selection principles — the exact risk 003-4 tests.
* **Minimal Lean target.** Define the weakest modal/existential addressability predicate and test whether directed incidence, source/target, or a carrier skeleton follows from it under minimal assumptions (`CoreCosmology/Ontology/AddressabilityThreshold.lean`).
* **Minimal Rust target.** No core Rust change yet; only prepare later fixtures named after the Lean collapse/non-collapse cases.
* **Terminal status:** `ReadyForLean` · **Evidence:** F1 · **Authority ceiling:** ShapeOnly.

### The SPK-COSMO firewall (consolidated from troika review §11 "What Not To Do Next")

The non-promotion discipline this packet cites as "the troika/SPK-COSMO firewall":

1. Do **not** broaden this into a physical-cosmology claim.
2. Do **not** claim `PrimitiveDifference_0` is prior to Structure.
3. Do **not** claim Carrier is fundamental.
4. Do **not** use ProtoSupport as a root just because it has a name.
5. Do **not** add Rust architecture before Lean identifies a stable field set.
6. Do **not** treat `Address → Mark` as a lower-layer primitive; that form has already collapsed into directed incidence.
7. Do **not** promote `F1` review output into mechanized evidence.
8. Do **not** add an encyclopedia entry for the speculative candidate before a proof or replay witness exists.
