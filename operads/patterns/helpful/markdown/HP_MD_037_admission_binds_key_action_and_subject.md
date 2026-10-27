---
pattern_id: HP_MD_037
name: admission_binds_key_action_and_subject
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_037_prefix_string_returned_admitted
language: markdown
authority_effect: None
---

# Healthy Pattern: Admission Binds Key, Action, And Subject (`HP_MD_037`)

## Description

An admission record names the string it was given and refuses that string when the only check is a prefix. A real admission binds a verified key to an action and a subject. An evaluation signature does not perform that act.

## Construction

- Put the exact string and the admission result in the same sentence.
- Treat `startswith("sig:ed25519:")` and `startswith("SIG_HUMAN_OPERATOR_")` as prefix shape, not signature verification.
- Refuse `SIG_HUMAN_OPERATOR_forged` and any other prefix-only string at the consumer that returns admission.
- Require a distinct authorization payload: action, subject digest, scope, issuer, policy version, nonce, and expiry, checked against a resolved key.
- Do not move Candidate to Reviewed unless a separate review record is present.
- Keep an evaluation signature at AuthorityEffect None. It does not admit a population member.
- When citing the 2026-10-08 observation, name native binary SHA-256 `afeb70a4fda041b5d102a702a5c5e383b5ea6e547b2ed0e2b6ed4559d82e3363` and label that run historical.

## Limit

The witness in [AP_MD_037_prefix_string_returned_admitted](../../anti/markdown/AP_MD_037_prefix_string_returned_admitted.md) is the historical folder `_ic/darpa/research/inputs/pfp_second_pass_20261008`, finding D3, dated 2026-10-08. No admission repro, domain harness, replay script, Lean command, or native rebuild was rerun. The note already says this is not a deployed-service compromise. Python and native prefix results are one policy shape, not two independent trials. Plan text that already separates evaluation from admission is not evidence that this interface performed that separation.

`/adversary-assigned-outcome-rule` still owns finding D2 in this same folder: one solved task and 99 allowed-task valid refusals are 100% conditional success and 1% assigned success. `/adversary-check-sensitivity-pattern` still owns a component check that misses a property-changing mutation. The historical fixture `missed_semantics` has `screen_pass` true and `oracle_pass` false for edge (2,2,4). The quoted-cost row has `screen_pass` false and `oracle_pass` true. Those rows are not this pattern.

`AP_MD_005` still owns a quotient or a non-closed cochain named as cohomology. `AP_MD_031` still owns an efficiency sentence that credits a cochain encoding with a gain the direct baseline already has. The historical screen-to-verifier CPU ratio 2.107, with fewer verifier calls, is not this pattern. `AP_MD_022` still owns axiom lines standing in for a failed `.olean`. This folder's positive log follows exit 0 and names `propext`, `Classical.choice`, and `Quot.sound`. `AP_MD_028` still owns a runner outage scored as a package fail. The negative Lean log is the expected unsolved goal `⊢ False`, and the earlier interpreter exit 1 was not the admission result. `AP_MD_049` still owns `certificate_verified` true beside a checker that was not run. `local_receipt.json` says `independent_reproduction` `NOT_RUN` and `signature` `UNSIGNED`.

`AP_PY_005` and `/adversarial-receipt-audit` still own a digest string treated as verified evidence. The historical helper credit for `sealed_receipt_digest="not-a-digest"` with `VERIFIED_EXACT` is not this prefix. `/declared-vs-actual-gate` still owns a missing stage binary or a host-mirror mismatch, not this admission string. `/human-promotion-firewall` still owns an agent promoting itself. `/adversary-proof-scope-rule` still owns a narrow identity, including a mean `4/delta` or a zero coboundary, promoted to a tail bound, a stopping theorem, or a semantic certificate. `/adversary-scoped-reuse-pattern` still owns cached imports labeled as a fresh rebuild. This receipt already says dependencies were not rebuilt.

A verified signature that fails a later policy check is not this defect. A prefix refused at the same consumer is not this defect. Python false and Rust true on one cross-assignment query is a different witness. It is not this pattern.

## Dual Anti-Pattern

See [AP_MD_037_prefix_string_returned_admitted](../../anti/markdown/AP_MD_037_prefix_string_returned_admitted.md).
