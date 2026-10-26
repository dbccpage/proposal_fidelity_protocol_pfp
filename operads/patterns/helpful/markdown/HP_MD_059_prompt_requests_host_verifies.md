---
pattern_id: HP_MD_059
name: prompt_requests_host_verifies
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_059_prompt_agency_and_self_authorizing_miner
language: markdown
authority_effect: None
---

# Healthy Pattern: Prompt Requests, Host Verifies (`HP_MD_059`)

## Description

Establishes clear architectural boundaries between prompt conditioning, proposal envelopes, host gate verification, prompt family membership, and checkable derivation witnesses.

## Construction

1. **Request Semantics:** State that the prompt *requests* structured candidate data or an intermediate derivation witness. State explicitly that host parsers and verifiers reject non-conforming or invalid proposals.
2. **Candidate Mining Fence:** When using models to extract patterns, skills, antiskills, or antibodies, explicitly declare: *"Mining output remains candidate material until reviewed or verified by the host."*
3. **Family Invariant Equivalence:** Restrict membership in a prompt family to dialects satisfying $P_i \sim P_j \iff \text{Both compile to the same protected task, boundaries, and acceptance tests}$. Route refusal tests and rule-withholding probes to an *associated adversarial-test family*.
4. **Wire vs. Pretty-Printed AST Separation:** Label multiline indented ASTs as pretty-printed visualizations for human legibility. Show the actual canonical one-line wire with all whitespace stripped for byte-exact hashing and cryptographic replay.
5. **External Witness Naming:** Label witness slots after the externally checkable artifact (e.g. `[DERIVATION_WITNESS]`, `"derivation_witness"`).

## Dual Anti-Pattern

See [AP_MD_059_prompt_agency_and_self_authorizing_miner](../../anti/markdown/AP_MD_059_prompt_agency_and_self_authorizing_miner.md).
