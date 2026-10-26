# Persistence, Provenance, Security, and Receipts

## SQLite unit of work

The SQLite adapter uses transactions, WAL for file databases, full synchronous
mode, idempotency storage, an event journal, and an outbox. These are useful
mechanisms. The serialized catalog is nevertheless materially lossy: save/load
drops leaves, operands, compositions, residuals, the proven root, capability slices,
and related metadata. Journal payloads retain only an event type rather than the
full domain-event data.

Concurrency checks are conditional on an expected version that normal handlers do
not consistently supply. There is no strong stream-version contract or uniqueness
constraint for an estate/epoch pair.

## Outbox behavior

The dispatcher marks an item delivered when no subscriber exists. With multiple
subscribers, a late failure can cause already-completed effects to repeat on retry.
There is no claim/lease protocol for concurrent dispatchers.

The current evidence supports a transactional outbox table, not exactly-once or
even complete at-least-once delivery to every subscriber. A repair should define
subscriber identities, per-subscriber acknowledgements, leases, retry policy, and
dead-letter evidence.

## HMAC envelope

The provider uses HMAC-SHA256 with a shared secret and colon-separated fields. HMAC
is a message-authentication construction standardized by
[RFC 2104](https://www.rfc-editor.org/info/rfc2104/). In this implementation,
`manifest_id` and `signature_algorithm` are not bound by the MAC, and key/signer
policy is not fully checked.

HMAC can prove possession of a shared secret to another holder of that secret. It
does not provide independent, asymmetric signer attribution. The code and docs
should call this an HMAC envelope, reserve “signature” for a deliberately specified
asymmetric scheme, and MAC a canonical, domain-separated payload containing every
security-relevant field.

## Provenance model

The [W3C PROV-O recommendation](https://www.w3.org/TR/prov-o/) distinguishes
entities, activities, and agents and relates generation, use, derivation, and
attribution. A bounded OEWAS mapping is:

| PROV idea | OEWAS record |
| --- | --- |
| Entity | source bytes, schema, manifest, catalog, receipt |
| Activity | parse, compile, validate, migrate, dispatch, admit |
| Agent | human reviewer, process identity, tool/runtime identity |
| Generation/use | exact input and output digest edges |
| Attribution | independently verifiable identity evidence |

This would improve replay and diagnosis. Merely naming a field `provenance` does not
make the graph complete.

Recent work on [provenance for AI agents](https://arxiv.org/abs/2508.02866) proposes
recording agent decisions and tool interactions. The relevant OEWAS experiment is a
minimal prompt/tool/evidence trace with privacy and redaction rules, never the claim
that all reasoning has been captured.

## Supply-chain attestations

The [in-toto framework](https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias)
and [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) provide models for
binding build steps, materials, subjects, and authenticated attestations. If OEWAS
needs cross-party attribution, adopt an attestation envelope such as DSSE plus a
specified identity/key policy. Keep the current HMAC path for local integrity only
if that is the actual threat model.

## Receipt checklist

A receipt is only as strong as its covered fields. A replay-grade receipt should
name:

- schema and domain-separation tag;
- exact source, configuration, and dependency digests;
- Git commit and dirty-state disposition;
- command/runtime identity;
- deterministic versus wall-clock fields;
- complete result and refusal payload;
- signer/authenticator algorithm and key identity;
- parent receipts and externally held custody anchor.

No receipt should assert authority beyond the producing operation’s ceiling.
