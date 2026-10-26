---
pattern_id: AP_RS_002
name: domain_enum_missing_ord
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "unknown"
dual_pattern: HP_RS_002_deterministic_key_trait_derive
language: rust
authority_effect: None
---

# Anti-Pattern: Missing Total Order on an Ordered Key (`AP_RS_002`)

## Failure and applicability

A key intended for `BTreeMap` or `BTreeSet` has a meaningful total order but lacks
`Eq`, `PartialOrd` or `Ord`. Falling back to hash iteration at a serialized report
or receipt boundary can then lose byte replayability. A missing derive alone
neither forces that fallback nor proves nondeterminism.

## Witness and deciding check

The compiler reports `E0277` when an actual key fails the required trait bound.
A scanner must compare complete derive identifiers: `PartialOrd` contains the
text `Ord` but does not implement `Ord`. Use this harmful scanner control:

```rust
#[derive(Debug, PartialEq, PartialOrd)]
pub enum Key { First, Second }
```

A benign control derives `PartialEq, Eq, PartialOrd, Ord` on the same key. An
unordered floating-point/error/JSON payload carrier is a different benign case:
it must not be told to derive a fictitious total order merely because it is an
enum. Inspect actual usage and payload semantics before declaring a defect.

## Related witnessed failures

Missing derives are only one review lead. The ordering triage also reproduced
three distinct failures at consumers:

- A name-bearing AutoP tape sorted allocated symbol IDs; reversed interning
  history changed tape bytes. Sort semantic names before allocation/traversal.
- Canonical JSON digests changed with nested insertion order when the additive
  `serde_json/preserve_order` feature replaced the default sorted map. Explicitly
  sort object keys at the promised identity boundary and preserve array order.
- Retained RowValue manual traits disagreed for NaNs, signed zeros and mixed
  variants. Repeated BTreeSet insertion collapsed distinct typed values; bulk
  collection masked this control. Its extracted harness is source-only evidence.

An enum in a map value or a `Result` error position has no ordered-key obligation
from that position. A manual equality that ignores a display name also forbids
blind structural `Ord` derivation. Scanner rows remain unverified, derive-only
leads until an actual trait requirement or observable failure is established.

## Repair and limits

Derive or implement coherent total order only for intended ordered keys. At a
report boundary, ordered maps or explicit canonicalization both preserve key
iteration order. Internal hash lookup is permitted when the consuming boundary
sorts its results. Deterministic keys alone do not canonicalize timestamps,
random IDs, floating-point representations or unordered nested collections.

See [the supported alternative](../../helpful/rust/HP_RS_002_deterministic_key_trait_derive.md)
and `RULE_RUST_ORDERED_KEY_DERIVE_001` in the Rust engineering rule.
