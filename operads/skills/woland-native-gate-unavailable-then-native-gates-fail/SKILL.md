---
name: woland-native-gate-unavailable-then-native-gates-fail
description: "Native gate unavailable (blocked) predicts native gates still not all pass on later re-execution"
metadata:
  omega-arity: "1"
  omega-contract: "omega_engine_operads/catalog/contracts/v1/lessons/woland-native-gate-unavailable-then-native-gates-fail.json"
  omega-contracts-digest: "sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f"
  omega-generated: "oewas.typed-capability.v1"
  omega-kind: "anti_pattern"
  omega-residual: "unknown"
  omega-source-colours: "[\"Code\"]"
  omega-target-colour: "Audit"
---

# woland-native-gate-unavailable-then-native-gates-fail

Generated guidance; edit the canonical typed contract and instruction resource.

# Native gate unavailable (blocked) predicts native gates still not all pass on later re-execution

If host_native_gates shows blocked NATIVE_GATE_UNAVAILABLE, do not assume a rerun will pass. Fix the native host binding or runtime artifact access first. Otherwise report native gate coverage as incomplete and never claim all-pass.

Seats: woland, hella, bezdomny. Admitted by host replay of recorded runs; guidance only, not a gate.

## Digested lesson

Source: `_ic/darpa/woland/self_digestion/witnesses/woland-native-gate-unavailable-then-native-gates-fail.json` @ `corpus-sha256:76258a14132224dfe2e1b3d5bf0f641dc333def62f75d93bb4dc792f98467c89` (sha256:4ffedb17253c3e029f231e3e81cd10e8d69bd7410e40b8fbf3c991efc87444af).

Source excerpt (evidence to inspect):

```text
detector {'blocked': true, 'failure_code': 'NATIVE_GATE_UNAVAILABLE', 'role': 'host_native_gates'} then {'kind': 'NATIVE_GATES_NOT_ALL_PASS'} in 3 runs
```

**Failed Claim:** Native gate unavailability was transient or incidental, and re-executing the gates later in the run would produce a full pass.

**Counterexample:** Witness runs: e0e7c4eed7fe48b990fa2a8a8063a425, ide-pfp-b3367b1ddb63, original-7a5445d19cd1.

**Cause:** The environment cause persists: no native host intake bound (OMEGA_SYMBOL_GAME_HOST or an explicit native binding), or a sandbox runtime artifact access denied. Rerunning gates without changing that environment leaves native_all_pass false.

**Correction:** Fix the native binding or artifact access before the gates are rerun. If it cannot be fixed, record native coverage as incomplete and do not assert that gates pass.

**Verification:** Host replay of recorded host facts over 48 runs: the detector fired in 3 and the outcome followed every time. Proposed by claude-sonnet-5-5. This does not rerun the old checks or show that the guidance helps later runs.

**Applicability:** Runs where host_native_gates reports blocked with failure_code NATIVE_GATE_UNAVAILABLE, such as NATIVE_HOST_INTAKE_UNAVAILABLE or RUNTIME_ARTIFACT_UNAVAILABLE.

**Exceptions:** Does not apply if the native host binding or artifact permission is changed between the blocked observation and the next gate execution.

## Guidance contract

**Failure:** The environment cause persists: no native host intake bound (OMEGA_SYMBOL_GAME_HOST or an explicit native binding), or a sandbox runtime artifact access denied. Rerunning gates without changing that environment leaves native_all_pass false.

**Witness:** detector {'blocked': true, 'failure_code': 'NATIVE_GATE_UNAVAILABLE', 'role': 'host_native_gates'} then {'kind': 'NATIVE_GATES_NOT_ALL_PASS'} in 3 runs

**Repair:** Fix the native binding or artifact access before the gates are rerun. If it cannot be fixed, record native coverage as incomplete and do not assert that gates pass.

Ordered signature: `(candidate: Code) -> result: Audit`.

Contracts: `sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
