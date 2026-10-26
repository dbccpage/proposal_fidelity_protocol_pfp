---
pattern_id: AP_MD_037
name: prefix_string_returned_admitted
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_037_admission_binds_key_action_and_subject
language: markdown
authority_effect: None
---

# Anti-Pattern: A Prefix String Returned Admitted (`AP_MD_037`)

## Description

An admission interface treats a signature-shaped prefix as authorization. The string is not a checked signature, and the call still returns admitted.

## Detection Signature

- The recorded input is a prefix-shaped string such as `SIG_HUMAN_OPERATOR_forged`, or a value that only starts with `sig:ed25519:` or `SIG_HUMAN_OPERATOR_`.
- The recorded result is `ADMITTED`, or the controller's ephemeral state changes on that call.
- The same record does not show key resolution, a verified signature, or bindings for action, subject digest, scope, issuer, policy, nonce, and expiry.
- A plan sentence that already separates evaluation from admission does not turn the prefix check into that gate.
- Updating Candidate to Reviewed inside the same admission call, without a review record, is this defect.

## Witness

Historical integration note, not a fresh admission run. This digest did not run `integration_repro.py`, `integration_domain_repro.ps1`, `replay.ps1`, or `lake`, and it did not rebuild the native binary.

`_ic/darpa/research/inputs/pfp_second_pass_20261008/integration_evidence.md`, finding D3, 2026-10-08:

> Executed `authorize_admission(...,"SIG_HUMAN_OPERATOR_forged")` returned ADMITTED and updated the controller's ephemeral state. This demonstrates that this named admission interface is not a cryptographic authorization gate, not that an external production service has been breached.

The same cell says Rust `civilization.rs:121-147` accepts string prefixes and emits `AdmittedFormulary`, and that lines 214-226 move Candidate to Reviewed during admission. Python legacy `domain/models.py:186-221` does the same prefix check. The executed assertions include the exact words "Python legacy prefix admission true; native controller prefix admission true."

`report.md` in that folder states that `civilization.rs:121` accepts `sig:ed25519:` or `SIG_HUMAN_OPERATOR_` prefixes, and that `SIG_HUMAN_OPERATOR_forged` was admitted in an ephemeral controller.

The note pins the existing native executable SHA-256 `afeb70a4fda041b5d102a702a5c5e383b5ea6e547b2ed0e2b6ed4559d82e3363` and says that binary was not rebuilt. Python 3.12.10 exited 0. An earlier sandboxed interpreter launch exited 1 before code ran; the same command then succeeded. That launch outage is not this admission result.

## Hazard & Failure Mode

- A later note cites `ADMITTED` as a cryptographic authorization.
- Candidate is described as reviewed because admission ran.
- The same folder's unsigned research receipt is cited as if this interface had been repaired.
- An evaluation signature is treated as population admission.

## Dual Healthy Pattern

See [HP_MD_037_admission_binds_key_action_and_subject](../../helpful/markdown/HP_MD_037_admission_binds_key_action_and_subject.md).
