packet_type: implementation
authority_effect: None
carrier: shape-addressed PromptPacketCore / PromptPacketRecord carrier (C⁰)
primary_residual: raw-text persistence, shape-typed carrier integration into EPK, content-address conflation (Q¹)
in_scope_repairs: private bucket vector, opaque-id mappings, try_from_wire validation (d₀)
deferred_residuals: consumer-side PromptGeometry migration, EPK row shape packet_id extension (core_prompt_packets_v2_packet.md)
seal_condition: terminalize_row returning Decision::Certified on prompt packet candidate rows

core_prompt_packets (Obstruction Descent Packet)
=================================================

**Date:** 2026-06-20
**App:** `core_prompt_packets` (greenfield Rust crate; SAGA-01 backbone)
**Parent spec:** `docs/superpowers/specs/2026-06-19-core-prompt-packets-design.md`
**Adapter:** `sprints/epic_omega_platform/sprint_planning_adapter_001.md`
**Firewall:** markdown does not mint authority; LLMs are candidate residual generators, not judges; HCT/HoTT/homology only

**Bundle status:** load-bearing, no sibling lemma-packets. (A2)

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The shape-addressed `PromptPacketCore` / `PromptPacketRecord` carrier emitted by the greenfield `core_prompt_packets` crate (pure, no-I/O, `forbid(unsafe_code)`), modelled as a `CochainPrimitiveDifference` row in `core_homology` whose payload is the canonical-byte encoding of a coarse `PromptShape` (byte/token/line buckets, 5-class byte histogram, entropy bucket, class-only trigram `structure_sig`).

The 2-window inspects the local boundary between three sites:

* **C0 site:** the borrowed `&str` raw input inside `PromptPacketCore::from_raw(raw, kind)` (raw text is hashed, dropped, and never moved into any struct).
* **C1 site:** the serialized JSONL row appended by the app layer, plus every `Debug`, `Display`, and `PacketError` rendering path.
* **C2 site:** the downstream `core_epk::EpkResidualLedger` consumer, where the packet must classify residual risk without ever lifting raw text or unkeyed raw-content identity into the seam.

The window is bounded by the SAGA-01 build-order step 1 (backbone), the SHAPE-address claim (`shape_id = H("...v1.shape" || canonical_bytes_v1(shape))`), and the `RefusalSource::Residual` boundary on the EPK side.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):** Current local assignments at packet construction time, lifted to a finite cochain in `core_homology::CochainComplex`:

* `CarrierKind` token (`UserPrompt | SystemPrompt | LlmResponse | OpaqueText`, with `BusinessPlan | PaperClaim | CodeDiff` forward-declared under `#[non_exhaustive]`).
* `PromptShape` private bucket vector: `shape_version=1`, `byte_len_bucket`, `token_count_bucket`, `line_count_bucket` (fixed ladder `[0, 16, 64, 256, 1024, 4096, 16384, 50000]`), `byte_class_histogram: [u8;5]` over `{alpha, digit, punct, space, other}`, `entropy_bucket: u8` over the 5-class distribution, `structure_sig: Hash32` over class-only trigrams.
* Opaque-id assignments: `ShapeId(Hash32)`, `PromptPacketId(Hash32)`, optional `ResidualFamilyId(Hash32)`, optional `OriginRef(Hash32)` (app-supplied keyed hash).
* `ProducerMeta`: `crate_name`, `crate_version`, `shape_algorithm = "core.prompt_shape.v1"`, `canonical_encoding = "core.canonical_shape_bytes.v1"` (build version is NOT hashed into `shape_id`).
* The pre-existing stubs that this carrier supersedes: `prompt_intake_engine::PromptGeometry` (left untouched at v1) and any ad-hoc raw-string fields surfacing through `core_epk::ledger::EpkResidualLedger { ngd, nrke, obstruction_status }`.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** The permitted cochain map at the C0 boundary, realized in `core_homology::CochainComplex::d0`. Admissible $d_0$ moves preserve the SHAPE-address claim and the privacy invariant:

* Reorder, rename, or re-bucket private fields **without** changing `canonical_bytes_v1` output (e.g. encapsulation refactors that leave the canonical byte stream identical).
* Add downstream annotations via the builder lambdas `PromptPacketRecord::with_family` and `PromptPacketRecord::with_origin`, where the annotations are typed `Hash32` newtypes (a free-form `String` family id is a $d_0$-forbidden move — it is a raw-text leak path).
* Re-derive `shape_id` / `packet_id` from `canonical_bytes_v1(shape)` and `carrier_kind` byte tag using blake3-256 with distinct domain tags (`...v1.shape`, `...v1.packet`, `...v1.structure`, `...v1.origin`).
* Tamper-evident rehydration through `try_from_wire(PromptPacketWire)`: recompute the ids and reject any mismatch as `PacketError::MalformedCarrier`.

Forbidden under $d_0$ (these moves break the canonical hash and force a `shape_version` bump, i.e. a $\Meta$ — see section 11): widening `PromptShape` with lexical features, hashing raw byte n-grams, deriving `serde::Deserialize` on `PromptPacketCore`, persisting raw text, mutating canonical field order, or introducing fs/net/log dependencies (denied by crate hygiene).

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** The active primitive differences observed across the 2-window, emitted as `CochainPrimitiveDifference` rows:

1. **PD-PP-001 (raw-text persistence):** raw prompt text is currently being persisted in shared stores upstream of the seam — directly violates §0 of the spec ("cannot persist, log, or expose raw prompt text").
2. **PD-PP-002 (no shape-typed carrier into EPK):** the EPK residual seam (`EpkResidualLedger::from_metrics`) consumes ad-hoc input with no shape-addressed carrier; the `Δ_E` channel has nowhere to attach a `PromptPacketId` and downstream telemetry can leak raw substrings through `Debug`/error rendering.
3. **PD-PP-003 (content-address conflation):** the umbrella architecture and analyzer (face b) treat the packet id as content-addressed, while the operator-corrected v2 spec demands SHAPE-address semantics (`distinct raw inputs may collide by design`).
4. **PD-PP-004 (free-form residual family ids):** downstream code paths assume `family_id: String`; this is a typed-leak path (e.g. `"user-asked-about-layoffs"`) and must be closed at the type level via `ResidualFamilyId(Hash32)`.
5. **PD-PP-005 (unkeyed origin hashes):** existing origin references are unkeyed hashes of low-entropy strings (`"user-1"`) — vulnerable to dictionary attack on common prompts.
6. **PD-PP-006 (no serde-tamper revalidation):** wire input is deserialized directly into the core type without recomputing `shape_id`, so a tampered JSON row can lie about its shape.
7. **PD-PP-007 (PromptGeometry stub):** the `prompt_intake_engine::PromptGeometry` stub is the de-facto carrier and ships nothing of the privacy invariant.

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two carrier states $x, y$ are gauge-equivalent when they agree under the canonical-byte encoding and the SHAPE-address claim:

$$
x \sim_{0} y \iff \mathrm{canonical\_bytes\_v1}(\mathrm{shape}(x)) = \mathrm{canonical\_bytes\_v1}(\mathrm{shape}(y)) \;\wedge\; \mathrm{carrier\_kind}(x) = \mathrm{carrier\_kind}(y).
$$

Concretely, the following differences are zero under ZeroRel and do **not** survive into $Q^1$:

* Private-field reorderings, doc-comment edits, internal renames that preserve `canonical_bytes_v1`.
* Distinct raw inputs that map to identical bucket vectors and identical class-only `structure_sig` (this is the operator-blessed by-design collision — §2 of the spec).
* Round-trip through `serde::Serialize` → `PromptPacketWire` → `try_from_wire` (the rehydration is a gauge transformation when no tampering occurred).
* Reordering of `with_family` / `with_origin` builder calls on `PromptPacketRecord` (annotations commute and are not part of core identity).

Implementation: the equivalence is decided by `core_homology::QuotientSpace` with the canonical-bytes key, and is observed externally via `core_functional::Observer` so the gauge action is auditable.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** $C^1 / \mathrm{im}(d_0)$ retains exactly the defects that no canonical-bytes-preserving $d_0$ move can erase. The irreducible residual is:

> **A shape-addressed `PromptPacketCore` carrier in a new crate `core_prompt_packets` that proves, by construction and by path-specific test, no raw-text leakage across the serialize / `try_from_wire` rehydration / EPK `Δ_E` seam.**

Concretely this residual class contains:

* The new crate itself (`engine/crates/core_prompt_packets/`) with private-field `PromptShape`, `PromptPacketCore`, `PromptPacketRecord`, opaque `Hash32` newtypes, `canonical_bytes_v1`, and lowercase-hex serde for `Hash32`.
* The seam fixture wiring one `PromptPacketRecord` into `core_epk::EpkResidualLedger` while the EPK ledger continues to return `AuthorityEffect::None` / `Outcome::Refused(RefusalSource::Residual)` — i.e. the packet does not change EPK's authority interface.
* The canary-grep gate: no fixture sentinel (`CANARY-7Q...`) and no raw token of length $\ge N$ may appear in serialized JSONL, `Debug`, `Display`, `PacketError` text, or any panic snapshot.

PD-PP-001 / PD-PP-002 / PD-PP-003 / PD-PP-004 / PD-PP-006 / PD-PP-007 survive $d_0$ and live in $Q^1$. PD-PP-005 is *almost* gauge-removable (the pure crate cannot own secrets), but the format-validation discipline on `OriginRef` survives as part of the residual contract.

**Residual deferrals** (no silent backlog — operator ruling 2026-06-20):

* `defer: PD-PP-007.consumer_side` → successor packet `core_prompt_packets_v2_packet.md`. The closure in this sprint is the *additive* preservation witness: a `NonDestructiveExtensionCertificate` over the unchanged `prompt_intake_engine::PromptGeometry` stub. A measurable "the new crate is now the de-facto carrier on the consumer side" requires migrating each consumer call site (analyzer face b, flagship API face d, self-reconstruction loop face f) and is out of this sprint's scope.
* `defer: epk_row_carries_packet_id` → successor packet `core_prompt_packets_v2_packet.md`. The current EPK row `EpkResidualLedger { ngd, nrke, obstruction_status }` (core_epk::ledger) has no `PromptPacketId` field. Adding one is a *separate* Meta against `core_epk` (a structural extension of EPK's row shape) and is fenced as out-of-scope by §13 ("Any change to `core_epk` authority semantics… lives in its own packet"). The S10 seam test in the sprint instead asserts the diagnostic-only firewall (`AuthorityEffect::None`, `RefusalSource::Residual`) over the *unchanged* EPK row shape; the prompt-side carrier is observed at the seam input, not from inside the ledger struct.

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** The triple-overlap closure across the three seams:

* **Round-trip overlap:** `from_raw` → `serde::Serialize` → `try_from_wire` must commute (same `shape_id` / `packet_id`).
* **Seam overlap (EPK):** `PromptPacketRecord` consumed by an `EpkResidualLedger`-bearing pipeline leaves `EpkResidualLedger::authority_effect() == AuthorityEffect::None` and `as_outcome() == Outcome::Refused(RefusalSource::Residual)` for every ledger state (the firewall already proven in `core_types`).
* **Annotation overlap:** `PromptPacketRecord::with_family(f).with_origin(o)` and `with_origin(o).with_family(f)` produce serializations that agree byte-for-byte (annotations commute and are not part of core identity).
* **Schema overlap:** `schema_version == PACKET_SCHEMA_VERSION` everywhere a record is rehydrated; mismatch closes as `PacketError::UnsupportedSchemaVersion`, not as an ad-hoc panic.

$d_1$ is the closure operator above. The crate's after-state closure check audits it on the **real** `core_functional::ExactGamma2Result` rail over a non-degenerate exact complex (a $d_1 d_0 = 0$ complex with a coboundary residual), confirming $\Gamma_2 = 0$ on the overlap cells; the carrier's own `PromptShape` bytes are not themselves projected into that complex (see the §8/§9 [ASSERTED] notes).

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass):** Per defect (A1). Each row reports the closure-failure mass at $t = 0$ on the overlap that defect lives on, plus the witness that will drive it to zero after section 12. Defects D1..D7 correspond one-to-one to PD-PP-001..007 of section 4.

> **[ASSERTED / by-construction]** As with $\Phi_1$ (§9), the per-defect "$> 0$" before-state entries below are an architectural census, not a `BigRational`-rail computation on a `PromptShape`-derived complex. The recomputed **after-state** $\Gamma_2 = 0$ on the three overlaps IS witnessed on the real `core_functional::ExactGamma2Result` rail over a non-degenerate exact complex (`tests/phi1_gamma2_closure.rs::phi1_gamma2_closure_gamma2_is_zero_on_three_overlap_cells`, with a coboundary residual on a $d_1 d_0 = 0$ complex). The "$> 0$" is the design-level claim that no admissible $d_0$ move closes the overlap before the Meta.

| Defect | $\Gamma_2$ at $t=0$ | Witness (overlap + driver to $\Gamma_2 = 0$) |
|---|---|---|
| D1 (PD-PP-001 raw-text persistence) | $> 0$ | EPK seam overlap: raw text persisted upstream of the carrier; driven to $0$ by introducing the shape-addressed `PromptPacketCore` so no raw text reaches the seam (see section 6, $\Meta$ in §11). |
| D2 (PD-PP-002 no shape-typed carrier into EPK) | $> 0$ | EPK seam overlap: no `PromptPacketId` is reachable from `EpkResidualLedger { ngd, nrke, obstruction_status }`; driven to $0$ at the seam-input observation (S10 offline post-LLM seam fixture, adapter AT-11) while EPK row shape is left unchanged. |
| D3 (PD-PP-003 content-address conflation) | $> 0$ | Round-trip overlap: content-vs-shape conflation makes `from_raw` $\to$ serialize $\to$ `try_from_wire` non-commuting on by-design shape-collisions; driven to $0$ by SHAPE-address derivation of `shape_id` / `packet_id` via `canonical_bytes_v1`. |
| D4 (PD-PP-004 free-form residual family ids) | $> 0$ | Annotation overlap: `String` `family_id` lets raw text smuggle through; driven to $0$ by the typed `ResidualFamilyId(Hash32)` newtype. |
| D5 (PD-PP-005 unkeyed origin hashes) | $> 0$ | Annotation overlap: unkeyed origin hash of low-entropy strings; driven to $0$ by requiring app-supplied keyed `OriginRef(Hash32)` (pure crate cannot own the key; format-validation discipline survives in $Q^1$). |
| D6 (PD-PP-006 no serde-tamper revalidation) | $> 0$ | Wire boundary overlap: tampered `shape_id` silently accepted; driven to $0$ by `try_from_wire(PromptPacketWire)` recomputing the ids and rejecting mismatch as `PacketError::MalformedCarrier`. |
| D7 (PD-PP-007 PromptGeometry stub) | $> 0$ | EPK seam overlap (additive): stub has no privacy invariant; driven to $0$ on the new-carrier side by the new crate; consumer-side migration is `defer:` to a successor packet (see section 6). |

Target after the DDA executes (section 12): $\Gamma_2 = 0$ on D1..D7, witnessed by the `wire_roundtrip_and_tamper`, `family_origin_no_leak`, and offline post-LLM seam integration test (adapter AT-11).

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass):** Per defect (A1). Each row is the non-removable component of that defect in $Q^1 = C^1 / \mathrm{im}(d_0)$ at $t = 0$. A row contributes $1$ when the defect survives every admissible $d_0$ move; it contributes $0$ when it is gauge-removable inside the existing carrier set.

> **[ASSERTED / by-construction]** The per-defect $\Phi_1$ values in the table below are an **architectural census**, not a numeric quantity read off a runtime `core_homology::CochainComplex` built from `PromptShape` data. These defects (PD-PP-001..007) are design-level primitive differences — "raw text is persisted upstream", "no shape-typed carrier reaches the EPK seam", etc. — and there is no natural finite cochain complex whose $\ker d_1 / \operatorname{im} d_0$ numerically equals such a statement. Constructing a complex engineered to total $\Phi_1 = 6$ would be fitting a carrier to a predetermined number. The crate's `tests/phi1_gamma2_closure.rs` instead exercises the **real** `core_functional::VerifiedExactPhi1` / `ExactGamma2Result` verifier on the **after-state** exact certificate ($\Phi_1 = 0$, $\Gamma_2 = 0$): it proves the upstream verifier accepts the by-construction resolved certificate, which is the load-bearing DoD claim. The before-state mass $\Phi_1(t=0) = 6$ is asserted from the census below; it is NOT computed on the `BigRational` rail (see also §11).

| Defect | $\Phi_1$ at $t=0$ | Witness |
|---|---|---|
| D1 (PD-PP-001 raw-text persistence) | $1$ | No $d_0$ move on the existing stub carriers eliminates raw-text persistence; requires the structural extension of §11 ($\Meta$). |
| D2 (PD-PP-002 no shape-typed carrier into EPK) | $1$ | The existing $C^0$ cannot express a shape-addressed carrier reachable from the EPK seam; survives quotient. |
| D3 (PD-PP-003 content-address conflation) | $1$ | SHAPE-address semantics are not derivable from a content-address carrier by any $d_0$ refactor; survives quotient. |
| D4 (PD-PP-004 free-form residual family ids) | $1$ | A `String` family id is a typed-leak path; no canonical-bytes-preserving $d_0$ move closes it; survives quotient. |
| D5 (PD-PP-005 unkeyed origin hashes) | $0$ (gauge-removable component) | Almost gauge-removable: the pure crate cannot own secrets; the format-validation discipline on `OriginRef` survives as part of the residual contract, but no $\Phi_1$ generator is contributed at the carrier level. |
| D6 (PD-PP-006 no serde-tamper revalidation) | $1$ | `try_from_wire` revalidation is structurally absent in the existing carriers; survives quotient. |
| D7 (PD-PP-007 PromptGeometry stub) | $1$ | The stub ships nothing of the privacy invariant; survives quotient. (Consumer-side migration is `defer:` per section 6 and is not double-counted here.) |

$$
\Phi_1(t = 0) = 6, \text{ architectural census.}
$$
$$
\Phi_1(t_{\mathrm{final}}) = 0, \text{ verifier-checked on exact witness.}
$$

The DoD for the corresponding sprint (see the sprint plan companion) is $\Phi_1(t_{\mathrm{final}}) = 0$ on D1..D7, OR any uncleared residual is moved into a successor packet via an explicit `defer` annotation. Until then $\Phi_1 > 0$ and the carrier sits in an active-closure-failure regime.

10. Classify System State
-------------------------

Per defect (A1). Classes drawn from the section-5 trichotomy of the standard: `ExactRepair`, `ClosedSurvivor`, `ActiveClosureFailure`, `NoRule` (plus `LiftNeeded` for defects whose closure requires the §11 $\Meta$).

| Defect | Class | Justification |
|---|---|---|
| D1 (PD-PP-001 raw-text persistence) | `LiftNeeded` (Active closure failure pre-lift) | $\Gamma_2 > 0$ on the EPK seam; not removable by any $d_0$ move; the §11 $\Meta$ introducing `core_prompt_packets` licenses closure. |
| D2 (PD-PP-002 no shape-typed carrier into EPK) | `LiftNeeded` (Active closure failure pre-lift) | $\Gamma_2 > 0$ on EPK seam; requires the new shape-addressed carrier (§11 $\Meta$). |
| D3 (PD-PP-003 content-address conflation) | `LiftNeeded` (Active closure failure pre-lift) | $\Gamma_2 > 0$ on round-trip overlap; SHAPE-address semantics require the new carrier type (§11 $\Meta$). |
| D4 (PD-PP-004 free-form residual family ids) | `LiftNeeded` (Active closure failure pre-lift) | $\Gamma_2 > 0$ on annotation overlap; closed by the typed `ResidualFamilyId(Hash32)` introduced by the $\Meta$. |
| D5 (PD-PP-005 unkeyed origin hashes) | `ClosedSurvivor` | Gauge-removable component at the carrier level ($\Phi_1$ contribution $0$); residual-contract format-validation discipline is stabilized as a survivor under declared scope; pure crate cannot own the key. |
| D6 (PD-PP-006 no serde-tamper revalidation) | `LiftNeeded` (Active closure failure pre-lift) | $\Gamma_2 > 0$ on wire boundary; `try_from_wire` revalidation is added by the $\Meta$. |
| D7 (PD-PP-007 PromptGeometry stub) | `LiftNeeded` (Active closure failure pre-lift) on the new-carrier side; consumer-side closure is `defer:` to a successor packet | Stub ships nothing of the privacy invariant; the new crate plus a `NonDestructiveExtensionCertificate` preserves the v1 stub; consumer migration is out of scope (§6 `defer`). |

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**Oracles required (A3):** none. No imported representation theorem is invoked; every transformation in §12 stays inside the declared finite 2-window. No sub-claim takes an `OracleNeeded` terminal status.

**$\Meta$ (Lift / Structural Extension):** Introduce the structural extension as a `FaceLambda` from `core_discrete_deformation_algebra`, packaged as a `NonDestructiveExtensionCertificate` and witnessed by a `FiniteLambdaStepCertificate`.

The proposed $\Meta$, written formally:

$$
\Meta : C^0_{\mathrm{stub}} \;\longrightarrow\; C^0_{\mathrm{packets}} \qquad
\Meta \;=\; \mathtt{FaceLambda::new("shape\_addressed\_carrier\_introduction",\ capacity)}
$$

(In code: `core_discrete_deformation_algebra::FaceLambda<&'static str>` — the face id is the literal string `"shape_addressed_carrier_introduction"`; the `kind` keyword in earlier drafts was prose only — `FaceLambda<F>` is generic over an opaque face id `F` and has no separate `kind` parameter.)

with the following witnesses, all required by the DDA contract before $\Meta$ may execute:

* **Obstruction witness:** the $Q^1$ residual of section 6 (the SHAPE-address carrier the existing $C^0$ cannot express).
* **Preservation witness (`NonDestructiveExtensionCertificate`):** `prompt_intake_engine::PromptGeometry` is **left untouched at v1** (spec §13); the umbrella build order step 1 is additive; downstream consumers (analyzer face b, flagship API face d, self-reconstruction loop face f) depend on the new crate but no existing public API is broken. The non-destruction check is satisfied because $\Meta$ adds a crate and adds a `CarrierKind` variant under `#[non_exhaustive]` (forward-declared carriers `BusinessPlan | PaperClaim | CodeDiff` are zero-impl-cost).
* **Coherence witness (`FiniteLambdaStepCertificate`):** the certificate carries `{ before: FiniteDiagnostic, after: FiniteDiagnostic, extension: NonDestructiveExtensionCertificate }` and is verified by `require_valid()`, which enforces (i) `before.require_lambda_license()` (the pre-Meta diagnostic must be obstructed: $\Phi_1 > 0$ or $\Gamma_2 > 0$), (ii) `after.is_resolved()` (the post-Meta diagnostic has $\Phi_1 = 0$ and $\Gamma_2 = 0$), (iii) the extension is non-destructive (all three NDEC bools true). The constants pinned in this packet — `PACKET_SCHEMA_VERSION = 1`, `shape_version = 1`, the fixed bucket ladder `[0, 16, 64, 256, 1024, 4096, 16384, 50000]`, the 5-class byte alphabet, and the four domain tags (`...v1.shape | ...v1.packet | ...v1.structure | ...v1.origin`) — are the *coherence boundary conditions* the certificate is asserted under; v2 (`shape_version` 2+) is fenced as a future $\Meta$, not part of this one.
* **Terminalizer route:** the seal is minted by `core_sweep_kernel::terminalize_row` (sole authority) or `core_certifiers::certify_checked_packet`; this markdown does not mint authority. The candidate row reaching the terminalizer carries the `PromptPacketId` and the offline-seam fixture digest.

$\Meta$ is licensed by: SAGA-01 backbone scope, operator review (2026-06-20), and the cross-boundary failure $\Gamma_2 > 0$ that no $d_0$ refactor can clear.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** The executable sequence, backed by the pinned bindings in the frontmatter:

1. **Gauge cleanup ($E$):** consolidate the existing pre-crate stubs, remove dead raw-text paths, run `core_homology::QuotientSpace` over the carrier complex to factor out gauge-equivalent differences (e.g. doc-only edits to `prompt_intake_engine`). No semantics change.
2. **Quotient projection ($R$):** enumerate the seven design-level primitive differences PD-PP-001..007 and assert the before-state $\Phi_1 > 0$ as an architectural census (the [ASSERTED] note in §9 — this step does NOT run `VerifiedExactPhi1` on a `PromptShape`-derived complex; the verifier is run only on the after-state resolved certificate in step 5).
3. **Structural lift ($\Meta$):** apply the `FaceLambda` of section 11. Create `engine/crates/core_prompt_packets/` with the type set from spec §3, `canonical_bytes_v1`, lowercase-hex serde for `Hash32`, `PromptPacketWire` + `try_from_wire` revalidation, and the `PacketError` enum from spec §9. Add `forbid(unsafe_code)` and the crate-hygiene denylist (no `tokio | reqwest | ureq | hyper | axum | tracing | log`; grep-deny `std::fs | std::net | println! | eprintln! | dbg!`). Allowed deps: `blake3`, `serde`, `thiserror`.
4. **Descent ($D$):** wire one `PromptPacketRecord` into the offline post-LLM seam fixture so that `core_epk::EpkResidualLedger::from_metrics` is reachable from a shape-addressed source, while `authority_effect() == AuthorityEffect::None` and `as_outcome() == Outcome::Refused(RefusalSource::Residual)` are preserved for every ledger state.
5. **Closure recompute ($C$ — context exposure):** run `core_functional::ExactGamma2Result` on a non-degenerate exact complex ($d_1 d_0 = 0$, a coboundary residual) and confirm the recomputed after-state $\Gamma_2 = 0$ (`tests/phi1_gamma2_closure.rs`); together with the $\Phi_1 = 0$ after-state certificate this is the load-bearing closure witness. The complex is a faithful exact-calculus instance but is NOT projected from the carrier's own `PromptShape` bytes (no natural such complex exists — see the §8/§9 [ASSERTED] notes). (Letter normalized to canonical `C` per A5: this step re-exposes the closure overlaps under the new carrier; the earlier draft labelled it with the symbol $\Gamma_2$, which is the *measurement*, not a DDA operation class.)
6. **Symbol Game adapter ($I$):** route the packet through `pfp` for downstream identification (no new authority surface; the Symbol Game is a candidate residual generator, not a judge).
7. **Terminalize ($T$):** send the resulting row to `core_sweep_kernel::terminalize_row` (or `core_certifiers::certify_checked_packet`); ONLY these mint authority. EPK and this packet remain diagnostic-only.

**A5 alphabet check.** DDA letters used in this section: $E, R, \Meta, D, C, I, T$. All drawn from the canonical set $\{E, R, C, I, \Meta/\Lambda, D, M, T\}$; no letter is invented.

Acceptance tests (runnable, real invocations — no "verify manually"):

```bash
cargo test -j 1 -p core_prompt_packets
cargo test -j 1 -p core_prompt_packets --test offline_post_llm_seam
cargo test -j 1 -p core_epk --lib ledger
```

plus the canary-grep test `canary_never_in_json` / `_debug` / `_display` / `_error` and the determinism / wire-tamper / hex32 / no-IO-hygiene tests from spec §12.

13. Terminal Status
-------------------

Per defect (A1) with Current / Target / Seal Condition split (A4). Markdown does not mint authority; every Seal Condition below names a real authority-minting call: `core_sweep_kernel::terminalize_row` returning `Decision::Certified`, or `core_certifiers::certify_checked_packet` (seven `IsAuth` guards).

| Defect | Current terminal | Target terminal | Seal Condition (the mechanical check that flips Current to Target) |
|---|---|---|---|
| D1 (PD-PP-001 raw-text persistence) | `ActiveClosureFailure` / `LiftNeeded` | `ExactRepair` | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the `core_prompt_packets` candidate row whose JSONL serialization passes the canary-grep test `canary_never_in_json` (and `_debug` / `_display` / `_error`) under `cargo test -j 1 -p core_prompt_packets`. |
| D2 (PD-PP-002 no shape-typed carrier into EPK) | `ActiveClosureFailure` / `LiftNeeded` | `ExactRepair` | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the seam-fixture row whose acceptance gate is `cargo test -j 1 -p core_prompt_packets --test offline_post_llm_seam` green and `EpkResidualLedger::authority_effect() == AuthorityEffect::None` / `as_outcome() == Outcome::Refused(RefusalSource::Residual)` on every ledger state. |
| D3 (PD-PP-003 content-address conflation) | `ActiveClosureFailure` / `LiftNeeded` | `ExactRepair` | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` after the wire-roundtrip / determinism / hex32 acceptance tests of section 12 are green under `cargo test -j 1 -p core_prompt_packets` (SHAPE-address `shape_id` / `packet_id` derived only from `canonical_bytes_v1`). |
| D4 (PD-PP-004 free-form residual family ids) | `ActiveClosureFailure` / `LiftNeeded` | `ExactRepair` | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` after `family_origin_no_leak` is green under `cargo test -j 1 -p core_prompt_packets` (typed `ResidualFamilyId(Hash32)` newtype enforced). |
| D5 (PD-PP-005 unkeyed origin hashes) | `ClosedSurvivor` | `ClosedSurvivor` | `core_certifiers::certify_checked_packet` (seven `IsAuth` guards) accepts the residual contract that requires app-supplied keyed `OriginRef(Hash32)`; `Decision::Certified` is minted on the residual-contract row; the pure crate carries no secret. |
| D6 (PD-PP-006 no serde-tamper revalidation) | `ActiveClosureFailure` / `LiftNeeded` | `ExactRepair` | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` after `wire_roundtrip_and_tamper` is green under `cargo test -j 1 -p core_prompt_packets` (`try_from_wire(PromptPacketWire)` rejects any `shape_id` / `packet_id` mismatch as `PacketError::MalformedCarrier`). |
| D7 (PD-PP-007 PromptGeometry stub) | `LiftNeeded` on the new-carrier side; `OpenResidual` / `defer` on the consumer side | `ExactRepair` on the new-carrier side; consumer-side carried via `defer:` to a successor packet | `core_sweep_kernel::terminalize_row` returns `Decision::Certified` on the new-carrier row carrying the `NonDestructiveExtensionCertificate` that leaves `prompt_intake_engine::PromptGeometry` untouched at v1; consumer-side migration is fenced to `core_prompt_packets_v2_packet.md`. |

Aggregate seal across D1..D7: the packet's overall Current is `ActiveClosureFailure` (one or more defects in `LiftNeeded`); its Target is `ExactRepair` (with D5 as a sealed `ClosedSurvivor` and D7's consumer-side carried via `defer:`) per row above; its aggregate Seal Condition is the conjunction of all rows' Seal Conditions, mediated by `core_sweep_kernel::terminalize_row` (returning `Decision::Certified`) or `core_certifiers::certify_checked_packet`. If any row fails its Seal Condition the corresponding defect regresses to `LiftNeeded` (mapped to `Decision::Obligation` or `Decision::RefusedHostAuthority` on the kernel side, depending on the failure mode) and a successor packet is opened with the residual carried via `defer`. LLM verdicts are candidate residual generators only; the Claude adversary gate in the companion sprint plan must report `blocks_promotion = false` before any row is sealed.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `core_prompt_packets::gtoc_adapter::evaluate_prompt_packets` constructs `GtocExactInput` and delegates classification to `core_pipeline::gtoc_gtla::evaluate_exact`. The adapter and focused Rust test are present; consumer completion and packet-id carriage remain owned by `S16-004`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The current packet hash and source manifest are recorded in `docs/status/core_conductor_s16_001_current_base_census_2026-07-19.json`; earlier future-tense implementation text is historical evidence only.

15. S16-004 protected-consumer disposition
------------------------------------------

At frozen base `46d91fb4165e6cb83fbb8c41168ed56739db478e`, S16-004 packet `01bd1e82e29810bf940ae962ebf3b50c87b54ba79dfd42a1d9dedfedc8f55e7b` registers five prompt-consumer dispositions. The API live lane, `engines` intake, and `core_business_plan_analyzer` boundary consume the v2 protected packet and shared exact evaluator. JSONL, CSV, and CoT intake retain hashes and typed metadata but drop raw prompt, answer, and chain-of-thought text before protected output. Focused tests pass for the registry (1), prompt exact adapter (2), and intake (5).

The EPK row-shape extension and absent self-reconstruction host remain explicit `LiftLicenseNeeded` survivors. This packet therefore terminalizes as `StabilizedSurvivor`, not global consumer completion. It does not judge prompt content or model output. `AuthorityEffect::None`, no gate activation, and no promotion are preserved.
