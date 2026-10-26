# Authenticated EIS custody

The operational activation use case now requires a current signed host-health
report. Signed admission decisions and observed evidence use the native
`omega_epistemic_immune_system::authenticated` verifier and the existing
SQLite `ReceiptLedger`. The legacy Formulary and four-conjunct activation
primitive retain their narrower, unauthenticated metadata interfaces.

## Trust and composition

An operator supplies `NativeAttestationVerifier` with an explicit policy and a
trusted clock. There is no built-in production key, trust discovery, signer or
automatic admission. The fixed keys in `tests/auth_support.py` are public test
data. A verified signature identifies a configured key, not a human being or
an independently correct measurement. Deployment must establish that mapping.

The policy schema is `omega.eis.trust-policy.v1`, with `trust_domain` and a
nonempty `keys` array. Each key specifies `issuer`, `key_id`, a lowercase
32-byte `public_key_hex`, permitted `purposes` and exact `scopes`, integer
`not_before`, `not_after`, `max_lifetime_seconds`, `revoked`, and optional
`observer_source_digest`. Health and observation reports must match that
observer-source digest. Duplicate issuer/key identities, duplicate roles or
scopes, malformed/weak public keys and missing trust refuse.

Purpose is one of `admission`, `health`, or `observation`. Bindings contain:

| Field | Meaning |
| --- | --- |
| `spec_id`, `scope` | Exact guard identity and operational scope. |
| `rule_digest` | SHA-256 of the actual rule bytes supplied at ledger opening. |
| `source_digest` | Operator-selected source manifest digest. |
| `subject_digest` | Rule digest for admission; payload digest for health; complete external-admission request ID for observations. |
| `context_digest` | Exact policy/profile/assumption context selected by composition. |

Digests use `sha256:` followed by 64 lowercase hexadecimal digits. Every
binding field is checked, not just candidate identity. Observation request
IDs additionally bind producer, source and positive/negative fixture digests
through the existing native request parser. A changed fixture needs a new
bound request; a previously verified view cannot be transplanted to it.

## Signed bytes and limits

`SignedEvidence` contains `attestation` and lowercase `evidence_hex`.
Attestations use `omega.eis.signed-attestation.v1`; unknown fields refuse.
Ed25519 strict verification covers UTF-8 JSON encoding of this ordered array,
with no whitespace, maps or floats:

```text
[schema_version, trust_domain, purpose, issuer, key_id, event_id,
 [spec_id, scope, rule_digest, source_digest, subject_digest, context_digest],
 issued_at, expires_at, outcome, previous_event, evidence_digest]
```

This is a versioned array encoding, not a claim to implement JSON Canonicalization
Scheme. `previous_event` is JSON null or the preceding statement's SHA-256.
The signature itself is excluded. SHA-256 binds the exact raw evidence bytes.
Tests independently encode and sign in Python and verify in Rust. Event IDs
and policy identifiers are bounded strings; booleans are not timestamps.
Evidence is nonempty and at most 1 MiB; policy size is at most 64 keys and
history size at most 4,096 events. Exceeding a budget refuses.

Validity is `issued_at <= now < expires_at`, inside the key's validity window
and maximum lifetime. Revoked keys refuse even historical authorization.
The structured health/observation evidence schema is
`omega.eis.observed-evidence.v1`, with exactly `observer_id`, `run_id`,
`subject_digest`, `source_digest`, and `outcome` in addition to the schema
field. Even a correctly signed narrative `ACCEPTED` is insufficient.

## Admission, activation and recovery

`AuthenticatedEisLedger.apply_decision` verifies current evidence before
appending. The permitted decision history is:

```text
CANDIDATE --ADMIT--> ADMITTED --SUSPEND--> SUSPENDED --REINSTATE--> ADMITTED
                         \--REVOKE--> REVOKED <--REVOKE--/
```

Every decision binds the previous statement digest, not a caller status flag.
Duplicate issuer/event pairs, missing links and decreasing times refuse.
Reinstatement must be strictly newer than suspension. Revocation is terminal.
Current lookup rechecks the latest decision's expiry and every historical
signature. Expired decisions never silently restore admission. Fresh signed
suspension and reinstatement can extend an expired history without erasing it;
there is no implicit renewal transition or key-rollover migration.

`activate_learned_guard` retains hit, independent danger, admission and
suspension checks, then calls `HostHealthPort.require_healthy`. The supplied
`SignedHostHealth` adapter reads and verifies a configured external report
for the exact subject/profile. Missing, unhealthy, expired, forged or foreign
reports refuse. An unchanged report may be reused during its explicit validity
window; this does not establish continuous health or latest-report ordering.
Host ports and their composition remain trusted application code, not a
capability sandbox against arbitrary in-process Python replacement.

`append_observation` accepts only current signed reports. Assessment verifies
retained history, excludes expired observations and counts distinct evidence
digests. Fresh reports can recover eligibility without deleting expired rows.
The observation view supplies the existing `assess_antibody` use case with
verified rows for the full request. Eligibility always remains `CANDIDATE`.
Distinct signed bytes do not prove statistical or causal independence.

## Persistence boundary

Open one `AuthenticatedEisLedger` for one rule/source/context binding using
the existing `ReceiptLedger`, the verifier, actual `rule_bytes`, and a
separately retained `pinned_tip`. New empty custody starts at `GENESIS_DIGEST`.
Each successful append returns the new pin; persist it outside the database
before treating the operation as durably anchored. On reopen, provide that
retained pin, never the current database's own tip.

The existing BLAKE3 chain and SQLite no-update/no-delete triggers are reused.
Whole-database replacement or tail truncation fails comparison with the
retained pin. A crash between database append and external-pin persistence
requires explicit reconciliation; there is no atomic cross-store commit.
Only a single writer is supported. Concurrent writers, rollback-resistant key
storage, physical tamper resistance, arbitrary history compaction and trusted
host-observer deployment remain outside this contract.

## Finite experiment and verification

The negative-selection experiment hashes the exact serialized detector rule,
executes its bound matcher on a malformed narrative receipt and a healthy
control, and uses actual signed observations through persisted custody.
Self-panel survival and external-review eligibility do not admit the rule.
This small fixture bank does not adopt a prior-art theorem or establish a
universal false-positive rate.

Run focused tests with a freshly built `omega_symbol_game` host configured by
`OMEGA_SYMBOL_GAME_HOST`. Python test signing requires the `dev` extra;
production signature verification stays in Rust. Reproduction commands and
the mutation/RED/GREEN evidence are in the
[follow-on checkpoint](../receipts/authenticated_custody_20261012/README.md).

AuthorityEffect: None.
