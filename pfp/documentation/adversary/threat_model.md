# Adversary Threat Model and Incontracted Types

AuthorityEffect: None.

## The Adversary Model
The adversary is an LLM agent, or a person using one, that constructs a payload designed to pass host checks.
Every refusal is phrased strictly as an objective finding about the packet.

## Uncontracted Types Audit
The estate maintains a strict ledger in `UNCONTRACTED.md` accounting for every uncontracted Rust serde type across the Symbol Game runtime.
The current figure is **43** uncontracted Rust types, each documented with a named reason or encapsulation boundary in `UNCONTRACTED.md`.
