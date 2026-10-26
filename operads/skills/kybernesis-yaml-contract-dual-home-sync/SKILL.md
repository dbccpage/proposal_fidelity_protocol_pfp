---
name: kybernesis-yaml-contract-dual-home-sync
description: "Check contract prompt YAML stays in sync between omega_contracts and universe_anomalonica copies."
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

Guards YAML contract definitions, ensuring exact 1-to-1 byte parity between Rust crate contract definitions and universe_anomalonica contracts documentation.

## Protocol

1. When modifying or creating a `.yaml` contract in `omega_engine/crates/omega_contracts/src/contracts_prompts/`, immediately copy to `omega_engine/research/ooutwire_docs/universe_anomalonica/omega_engine/contracts/contracts_prompts/`.
2. Verify SHA-256 agreement across both homes.
