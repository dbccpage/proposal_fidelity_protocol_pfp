# NATIVE-EIS-004: Signed Custody Binding Boundary

AuthorityEffect: None.

- Archive claim: [ATL-P003-014](atl_p003_014.md) (partially covered alongside `PAPER006-CONTROLLED-REUSE-UTILITY`, `supports`)
- Audit derivation node: `NATIVE-EIS-004` (`ATL-D-NATIVE-EIS-004`)
- Review verdict: `partial` (`supports` `ATL-P003-014` in [`atlas/atlas_claim_matches.json`](../../atlas/atlas_claim_matches.json))

## 1. Statement under review

Signed custody verification in `code/rust/core_epistemic_immune_system/src/authenticated.rs` binds each attestation statement to an ordered Ed25519 signing array, a configured `TrustPolicy`, time validity bounds, SHA-256 evidence digest, and declared `Binding` fields (`spec_id`, `scope`, `rule_digest`, `source_digest`, `subject_digest`, `context_digest`).

## 2. Verified codebase evidence

- `code/rust/core_epistemic_immune_system/src/authenticated.rs:148-191`: `TrustPolicy::validate` rejects empty or `> 64` key sets, duplicate `(issuer, key_id)`, `not_before >= not_after`, zero `max_lifetime_seconds`, empty or non-unique purposes/scopes, and weak or malformed Ed25519 keys.
- `code/rust/core_epistemic_immune_system/src/authenticated.rs:196-220`: `Attestation::signing_bytes` serializes an ordered float-free JSON array containing schema, `trust_domain`, `purpose`, `issuer`, `key_id`, `event_id`, the 6 `Binding` fields, `issued_at`, `expires_at`, `outcome`, `previous_event`, and `evidence_digest`.
- `code/rust/core_epistemic_immune_system/src/authenticated.rs:285-376`: `verify` checks policy, expected binding, statement fields, key authorization, evidence length (`<= 1 MiB`) and digest, strict Ed25519 signature, and purpose payload coherence.
- `code/rust/core_epistemic_immune_system/src/authenticated.rs:378-385`: admission state transitions are gated by prior state and outcome (`CANDIDATE` + `ADMIT` -> `ADMITTED`).

## 3. Relation to `ATL-P003-014`

`ATL-P003-014` states that admission requires a reproduced defect, valid near misses, a declared scope, and frozen identities. Together with `PAPER006-CONTROLLED-REUSE-UTILITY`, `NATIVE-EIS-004` grounds the identity, scope, and rule/source/subject/context binding side natively in `authenticated.rs`.

## 4. Bounds and open obligations

- Verification authenticates statements relative to a caller-supplied `TrustPolicy` and `now` timestamp; it does not establish truth of the observation or map cryptographic keys to authorized operators (`eis/documentation/oeeis_residual_obligations.md`).
- Durable external pinning of latest chain tips remains the host/operator's responsibility.
- Package-specific wording differences in Paper 003 remain recorded on `ATL-P003-014` as an editorial/scope boundary.
