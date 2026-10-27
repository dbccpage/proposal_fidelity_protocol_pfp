---
name: adversary-fixture-transport-block-then-later-seat-blocked
description: "Syntax Prefilter blocked by FIXTURE_TRANSPORT_UNAVAILABLE predicts a later seat (scar_chronicler) blocked the same way"
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-fixture-transport-block-then-later-seat-blocked.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "rule"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-fixture-transport-block-then-later-seat-blocked

Generated guidance; edit the canonical typed contract and instruction resource.

# Syntax Prefilter blocked by FIXTURE_TRANSPORT_UNAVAILABLE predicts a later seat (scar_chronicler) blocked the same way

If your seat or an earlier seat was blocked with FIXTURE_TRANSPORT_UNAVAILABLE (no model was sent), expect later seats to be blocked the same way. Do not retry or reword the task. Report the transport as the residual blocker, and proceed only if the transport has been restored.

Seats: syntax_prefilter, scar_chronicler, adversary. Admitted by host replay of recorded runs; guidance only, not a gate.

## Digested lesson

Source: `_ic/darpa/adversary/self_digestion/witnesses/adversary-fixture-transport-block-then-later-seat-blocked.json` @ `corpus-sha256:76258a14132224dfe2e1b3d5bf0f641dc333def62f75d93bb4dc792f98467c89` (sha256:f976ec92c4bcba4b35d906eeaf6558766498ea64801867e5f8e8c8b0ef12f307).

Source excerpt (evidence to inspect):

```text
detector {'blocked': true, 'failure_code': 'FIXTURE_TRANSPORT_UNAVAILABLE', 'role': 'syntax_prefilter'} then {'kind': 'SEAT_BLOCKED'} in 5 runs
```

**Failed Claim:** The assumption that a later seat can still run and produce model output after the first seat was blocked by a missing fixture transport.

**Counterexample:** Witness runs: 01472d27e70849d99b2eadb24dbc1a64, 02aa75e678eb491cae4d2cf84380fcbd, 0a371ade50014b41b80817cc07afa5a0, 0c6c4cb965034d8ca3e0326122f9598d, b8cb1e0b32894e24bb36ae7dd8ee5a84.

**Cause:** FIXTURE_TRANSPORT_UNAVAILABLE is a run-level transport condition, not a seat-specific fault. No model request is sent, so every subsequent seat that needs the transport is blocked the same way.

**Correction:** Treat the first FIXTURE_TRANSPORT_UNAVAILABLE block as run-wide. Do not plan work that depends on model output from later seats. Either restore the fixture transport before dispatching further seats or record the run as blocked with that residual.

**Verification:** Host replay of recorded host facts over 48 runs: the detector fired in 5 and the outcome followed every time. Proposed by claude-sonnet-5-5. This does not rerun the old checks or show that the guidance helps later runs.

**Applicability:** Runs where an early seat observation has blocked=true and failure_code FIXTURE_TRANSPORT_UNAVAILABLE with the summary 'No model was sent'. This applies to runs with the openrouter executor.

**Exceptions:** Does not apply if the transport is restored or replaced between seat dispatches. It also does not apply to blocks with other failure codes, such as provider HTTP errors or an unavailable native gate.

## Guidance contract

**Trigger:** A Adversary seat observation matching {"blocked": true, "failure_code": "FIXTURE_TRANSPORT_UNAVAILABLE", "role": "syntax_prefilter"}

**Predicate:** The recorded outcome {"kind": "SEAT_BLOCKED"} is anticipated and handled before it occurs.

**Response:** Treat the first FIXTURE_TRANSPORT_UNAVAILABLE block as run-wide. Do not plan work that depends on model output from later seats. Either restore the fixture transport before dispatching further seats or record the run as blocked with that residual.

Ordered signature: `(candidate: Code) -> result: Audit`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
