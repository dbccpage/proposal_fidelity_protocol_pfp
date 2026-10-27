---
packet_type: implementation
authority_effect: None
carrier: FiniteQMContractV1 schema shell (C⁰)
primary_residual: missing distinct fence types + import ledger + versioned hashable schema (Q¹)
in_scope_repairs: FiniteCarrier/FiniteDimension/FiniteCertificate/ContinuumDebt newtypes, ImportLedger, SHA-256 canonical JSON (d₀)
deferred_residuals: full QM math (T8–T18); import slot WITNESSED bindings; Lean non-inference mirror
seal_condition: terminalize_row returns Decision::Certified on FiniteQMContractV1 schema row (not claimed by this markdown)
---

# FiniteQMContractV1 (Obstruction Packet)

**Packet date:** 2026-08-01  
**App / carrier:** `core_q::finite_qm_types`  
**Math contract:** `urn:core:math:finite_qm:v1.0.0`  
**Rust file contract:** `urn:core:rust:core_q:finite_qm_types:v1.0.0`  
**Schema tag:** `FiniteQMContractV1`  
**AuthorityEffect:** None (never GlobalGreen)

**Firewall:** Markdown does not mint authority. Only `core_sweep_kernel::terminalize_row` / `core_certifiers::certify_checked_packet` can. No motivic structures. No Langlands. HCT / HoTT / homology only.

**Related loci:**
- Finite vocabulary fence: `engine/research/published/001_coda/005_coda_cs_q_bridge/docs/finite_vocabulary_fence.md`
- Ingredient ladder: `engine/research/published/003_quantum_foundations/qm_121_the_finite_qm_ingredient_ladder/`
- Q continuum siblings: `rust/core_q_*.contract.yaml`, `09_core_packets/q_real_001_*.md`

## Thesis

Target 3 ships a **schema shell** for finite QM boundary bookkeeping: four non-collapsing fence types, an import ledger with `OPEN|DECLARED|WITNESSED` slots, a versioned JSON schema identity, and a deterministic SHA-256 of canonical JSON. It does **not** implement QM solvers, does **not** admit continuum claims, and does **not** mint authority.

## Non-inference fence (mandatory)

| Type | Fence ID | Meaning | Must not be inferred from |
|---|---|---|---|
| `FiniteCarrier` | `FINITE_CARRIER` | Finite set of states / discrete support | Finite-dim Hilbert; continuum object finite as a set |
| `FiniteDimension` | `FINITE_DIMENSION` | Finite-dim vector/Hilbert rank | Finite carrier; finite certificate |
| `FiniteCertificate` | `FINITE_CERTIFICATE` | Finite evidence/receipt/audit artifact | Finite-dim Hilbert; finite presentation |
| `ContinuumDebt` / `FiniteDimContinuumScalars` | `FINITE_DIM_CONTINUUM_SCALARS` | Finite-dim system with continuum scalars (e.g. $M_n(\mathbb{C})$) | Finite certificate; continuum object finite as a set |

**Chain (no arrows reverse):**

```text
FiniteCarrier ⇏ FiniteDimension ⇏ FiniteCertificate ⇏ ContinuumDebt
continuum scalars ⇏ finite certificate
finite certificate ⇏ finite-dim Hilbert
finite carrier ⇏ continuum object is finite
```

**Name fence:** `finite_qm_types::ContinuumDebt` is the schema continuum-debt type. It is **not** `core_q::continuum::ContinuumDebt` (Q-admission debt).

## Schema fields

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string const | `"FiniteQMContractV1"` |
| `contract_urn` | string const | `urn:core:math:finite_qm:v1.0.0` |
| `authority_effect` | string const | `"None"` |
| `carrier` | `FiniteCarrier` | `carrier_id`, `support_cardinality` |
| `dimension` | `FiniteDimension` | `dimension_id`, `rank` |
| `certificate` | `FiniteCertificate` | `certificate_id`, `kind`, `payload_digest_sha256` |
| `continuum_debt` | `ContinuumDebt` | wraps `FiniteDimContinuumScalars` + notes |
| `import_ledger` | `ImportLedger` | slots sorted by `slot_id` before hash |

## Import ledger (default OPEN slots)

| slot_id | Label | Default status |
|---|---|---|
| `born_uniqueness` | Born-quadratic uniqueness (Gleason-type) | OPEN |
| `continuum_limit` | continuum path-integral / limit authorization | OPEN |
| `interference_resource` | non-L1 interference (qm_121 rung 6) | OPEN |
| `monoidal` | monoidal / tensor composition rule | OPEN |
| `spectral` | finite spectral theorem / spectral membrane | OPEN |
| `tomography` | local tomography / state reconstruction | OPEN |
| `u1_phase_carrier` | ℂ/U(1) phase carrier | OPEN |
| `unitarity` | unitary dynamics import | OPEN |

Status enum only: `OPEN` | `DECLARED` | `WITNESSED`. Advancement is recorded, never silently discharged.

## Canonical hash

- **Algorithm:** SHA-256  
- **Encoding:** `core.canonical_json.v1` (compact JSON, object keys sorted, no floats)  
- **Digest format:** lowercase hex  
- **Fixture:** `FiniteQmContractV1::smoke_fixture()` in `engine/crates/core_q/src/finite_qm_types.rs`  
- **Pinned digest:** `6bb78de524b10eb32ae23f3b5aa277b632e0490ca888ab554340202d8a3a10f0` (`SMOKE_FIXTURE_SHA256`); asserted by `fixture_canonical_hash_is_stable`

## ODP field mapping (schema shell only)

| ODP field | Instance |
|---|---|
| Carrier | `FiniteQmContractV1` type surface in `core_q::finite_qm_types` |
| C⁰ | Missing distinct fence types + import ledger + versioned hashable schema |
| d₀ | Add newtypes, ImportLedger, canonical JSON + SHA-256, dual YAML contracts |
| C¹ | Alias-collapse risk across FINITE_* senses; undated imports |
| ZeroRel | Same canonical JSON bytes (key-sorted, ledger sorted by slot_id) |
| Q¹ | Full QM math still out of scope; WITNESSED bindings open |
| terminal | Evidence-only schema shell; AuthorityEffect None |

## Paths

| Artifact | Path |
|---|---|
| Math contract | `engine/crates/core_contracts/src/contract_canonical_definitions/math/finite_qm/finite_qm_contract_v1.contract.yaml` |
| Rust file contract | `engine/crates/core_contracts/src/contract_canonical_definitions/rust/finite_qm_contract_v1.contract.yaml` |
| This packet | `engine/crates/core_contracts/src/contract_canonical_definitions/09_core_packets/finite_qm_contract_v1_packet.md` |
| Rust types | `engine/crates/core_q/src/finite_qm_types.rs` |

## Gate impact

- **v1 corpus gate:** math contract is `core.contract.v1` with `descriptor.authority_effect: none` — additive; must load without findings.
- **rust_binding gate:** symbols listed under `core_q` / `finite_qm_types` must resolve (Target 3 realizes them).
- **file contract:** rust YAML pins required substrings/tests on `finite_qm_types.rs`.
- **packet_registry.json:** no new prefix mapping required for Target 3 (schema shell only; `crates/core_q` remains on the packet-coverage ratchet list, not forced-mapped here).
- **Does not** change Q-admission firewall behavior or existing `ContinuumDebt` admission fields.

## Non-claims

- Does not derive QM, Born uniqueness, ℂ/U(1), continuum limits, or unitarity.
- Does not promote import slots from OPEN to WITNESSED without external evidence.
- Does not mint certificates of authority or GlobalGreen.
- Does not implement T8–T18 QM math (other agents).

## Terminal status (diagnostic only)

| Defect | Current | Target | Seal condition |
|---|---|---|---|
| D_finite_qm_schema_shell | **Repaired** (types + contracts + hash fixture) | Sealed | Host `terminalize_row` Certified on the FiniteQMContractV1 row — **not executed by this packet** |

Markdown mints nothing.
