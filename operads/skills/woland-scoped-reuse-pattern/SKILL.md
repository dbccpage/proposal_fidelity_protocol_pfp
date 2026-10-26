---
name: woland-scoped-reuse-pattern
description: "Reuse unchanged evidence with its original scope."
metadata:
  omega-arity: "1"
  omega-contract: "omega_engine_operads/catalog/contracts/v1/lessons/woland-scoped-reuse-pattern.json"
  omega-contracts-digest: "sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f"
  omega-generated: "oewas.typed-capability.v1"
  omega-kind: "helpful_pattern"
  omega-residual: "unknown"
  omega-source-colours: "[\"Code\"]"
  omega-target-colour: "Code"
---

# woland-scoped-reuse-pattern

Generated guidance; edit the canonical typed contract and instruction resource.

# Review procedure

Separate changed dependencies from unchanged ones before scheduling checks. Retain historical evidence labels and bindings. Give the next worker the changed source, original invariants, relevant prior scope and the smallest deciding outstanding check.

## Digested lesson

Source: `_ic/nara/historical/oewas007/research/wdp_calibrated_recovery/reviews/r2_code.json` @ `32454fda2b42454792f6d49ec22e7304a4e30ba6` (sha256:fa836b342cd46d9a348e77670cf10dcf9eaa799321e737c54c8d9c031ad760fe).

Source excerpt (evidence to inspect):

```text
Unchanged algebraic sources were not recompiled or exhaustively re-enumerated merely for this parser repair.
```

**Failed Claim:** Every candidate edit either invalidates all prior evidence or permits old checks to be called fresh.

**Counterexample:** The parser repair reran changed public-entry controls while explicitly retaining the earlier algebraic/Lean evidence for unchanged sources.

**Cause:** Candidate-wide labels hid the evidence dependency boundary and execution date.

**Correction:** Identify the exact dependencies of each finding/check. Reuse only unchanged compatible evidence at its original scope and date, then check changed or still-open obligations.

**Verification:** Read Round 2 code and math reviews and their predecessor hash/scope declarations. This digest does not independently rehash the old external candidate or reissue its test results.

**Applicability:** Incremental Woland repair reviews and generated next-worker briefs.

**Exceptions:** Changes to assumptions, resources, policy, checker or toolchain may invalidate reuse even when a manuscript is unchanged. If the dependency mapping is unavailable, retain UNKNOWN.

## Guidance contract

**Conditions:** An explicit dependency map and compatible unchanged evidence bindings are available.

**Construction:** Recheck affected obligations; carry unchanged evidence with its original scope and date.

**Example:** A parser-only repair reruns malformed/valid input controls; unchanged proof evidence remains historical rather than becoming a fresh Lean run.

Ordered signature: `(candidate: Code) -> result: Code`.

Contracts: `sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
