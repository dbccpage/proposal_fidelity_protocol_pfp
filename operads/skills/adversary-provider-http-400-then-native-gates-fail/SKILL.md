---
name: adversary-provider-http-400-then-native-gates-fail
description: "A seat blocked by PROVIDER_HTTP_400 is followed by native gates that do not all pass."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-provider-http-400-then-native-gates-fail.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "anti_pattern"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-provider-http-400-then-native-gates-fail

Generated guidance; edit the canonical typed contract and instruction resource.

# A seat blocked by PROVIDER_HTTP_400 is followed by native gates that do not all pass.

After PROVIDER_HTTP_400, treat that seat's output as absent and do not cite it as a basis. Native gates will likely fail, so report the residual failure code and keep the task open instead of claiming verification.

Seats: scope_guard, scar_chronicler, adversary. Admitted by host replay of recorded runs; guidance only, not a gate.

## Digested lesson

Source: `_ic/darpa/adversary/self_digestion/witnesses/adversary-provider-http-400-then-native-gates-fail.json` @ `corpus-sha256:76258a14132224dfe2e1b3d5bf0f641dc333def62f75d93bb4dc792f98467c89` (sha256:12282a83811e340950e44497942fb2cb5ed3e30d9d981439cd23e408e6e2591c).

Source excerpt (evidence to inspect):

```text
detector {'blocked': true, 'failure_code': 'PROVIDER_HTTP_400'} then {'kind': 'NATIVE_GATES_NOT_ALL_PASS'} in 2 runs
```

**Failed Claim:** A provider HTTP 400 on one seat is a transient hiccup that later seats will recover from.

**Counterexample:** Witness runs: 392ba665681646f8b983b3bf394c15f7, 94e1b4c1702d454290e1791bc6d078d3.

**Cause:** The provider rejected the request itself, so that seat produced no output and the downstream seats had nothing to build on. The native gates then failed on the missing artifact.

**Correction:** On PROVIDER_HTTP_400, treat the seat's output as missing. Do not rely on it, do not assume a retry will succeed, and report the residual failure code instead of a solved state.

**Verification:** Host replay of recorded host facts over 48 runs: the detector fired in 2 and the outcome followed every time. Proposed by claude-sonnet-5-5. This does not rerun the old checks or show that the guidance helps later runs.

**Applicability:** Any seat observation with blocked=true and failure_code PROVIDER_HTTP_400.

**Exceptions:** Does not cover other provider errors or blocks caused by malformed replies.

## Guidance contract

**Failure:** The provider rejected the request itself, so that seat produced no output and the downstream seats had nothing to build on. The native gates then failed on the missing artifact.

**Witness:** detector {'blocked': true, 'failure_code': 'PROVIDER_HTTP_400'} then {'kind': 'NATIVE_GATES_NOT_ALL_PASS'} in 2 runs

**Repair:** On PROVIDER_HTTP_400, treat the seat's output as missing. Do not rely on it, do not assume a retry will succeed, and report the residual failure code instead of a solved state.

Ordered signature: `(candidate: Code) -> result: Audit`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
