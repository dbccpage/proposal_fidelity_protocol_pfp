---
pattern_id: HP_RS_002
name: deterministic_key_trait_derive
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "unknown"
dual_pattern: AP_RS_002_domain_enum_missing_ord
language: rust
authority_effect: None
---

# Helpful Pattern: Meaningful Ordered Keys (`HP_RS_002`)

## Conditions

Use when an identifier/status type is an actual ordered collection key and its
payloads admit a coherent total order, or when a report requires stable key
iteration. Do not impose total order on every Rust value or result carrier.

## Construction

```rust
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum NodeStatus { Pending, Active, Terminated }

let counts: BTreeMap<NodeStatus, usize> = BTreeMap::new();
```

Ensure `Eq` and `Ord` agree. If wire output uses names, establish the intended
lexical/key ordering rather than assume an enum's declaration order is the wire
order. Sorting a console projection does not canonicalize serialized struct
fields. Test the final serialized report from different map insertion orders.

## Replay and trait-law controls

Compare name-bearing tapes after reversing both symbol interning history and
graph/neighbor insertion. Canonicalize semantic names rather than allocation IDs;
preserve dependency/refusal behavior. Internal ID lookup may remain unchanged.

For documented canonical JSON/hash/identity functions, compare opposite nested
object insertion under `serde_json/preserve_order` as well as the default profile.
Explicit recursive object sorting must preserve existing golden bytes and make
array reordering observable. Do not apply this to source-ordered display output.

For manual ordering, check Eq reflexivity, `cmp == Equal` iff Eq, equal hashes,
transitivity and repeated ordered-set insertion/lookup. Include NaNs, signed
zeros, mixed variants and large integers. Decide and document typed identity
versus numerical coercion; a numerical predicate can have a separate contract.

## Deciding controls and limits

An actual ordered-key compile check distinguishes `Ord` from `PartialOrd`.
Use a complete ordered key as the benign scanner control and a `PartialOrd`-only
key as the harmful control. Retain a benign unordered payload type so the
scanner cannot turn broad enum counts into a bulk derive instruction.

`BTreeMap` stabilizes map iteration, not the whole artifact: timestamps, random
values and nested unordered collections retain their own contracts. Internal
hash lookup followed by explicit canonicalization is another valid construction.
See [AP_RS_002](../../anti/rust/AP_RS_002_domain_enum_missing_ord.md).
