---
name: kybernesis-yaml-contract-dual-home-sync
description: "Check contract prompt YAML stays in sync between core_contracts and universe_sentinelica copies."
status: Kybernesis
archive_prefix: kybernesis
authority_effect: None
date: 2026-08-07
operad_source_colours: ["Contract", "State"]
operad_target_colour: "Contract"
operad_arity: 2
operad_residual: "unknown"
---

# kybernesis-yaml-contract-dual-home-sync

**AuthorityEffect:** `None`

## Purpose

Guards YAML contract definitions, ensuring exact 1-to-1 byte parity between Rust crate contract definitions and universe_sentinelica contracts documentation.

## Protocol

1. When modifying or creating a `.yaml` contract in `engine/crates/core_contracts/src/contracts_prompts/`, immediately copy to `engine/research/ooutwire_docs/universe_sentinelica/engine/contracts/contracts_prompts/`.
2. Verify SHA-256 agreement across both homes.
