---
name: adversary-strict-input-pattern
description: "Repair structured ingress with explicit typed refusals while preserving valid normalization."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-strict-input-pattern.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "helpful_pattern"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Code"
---

# adversary-strict-input-pattern

Generated guidance; edit the canonical typed contract and instruction resource.

# Strict input typed refusal

Reuse HP_PY_013 and its AP_PY_013 witness. Read the declared schema and existing refusal types. At that boundary, reject unsupported structure explicitly; do not fabricate an operation from a scalar or discard invalid collection members. Keep the offending index when the API already exposes one.

Preserve valid inputs and explicitly documented normalization. Carry the original API and invariants into the repair brief. Inspect the whole change against those invariants and report only checks actually observed. The existing Markdown owner keeps its healthy_pattern category; this typed entry uses helpful_pattern.

## Digested lesson

Source: `operads/patterns/helpful/python/HP_PY_013_strict_input_typed_refusal.md` @ `827d3b47743393a96441751de40e1b4be2b33d9e` (sha256:360fc3efbbe26c3c7fe1175eb1251419197343814bd18931ada41e795c641d70).

Source excerpt (evidence to inspect):

```text
Any malformed structure (such as unexpected scalars, malformed step dictionaries, or unrecognized elements) triggers an immediate, typed refusal record without silent transformation or data dropping.
```

**Failed Claim:** Silently converting or discarding malformed inputs preserves a structured workflow request.

**Counterexample:** AP_PY_013 documents a scalar converted into a nullary operation and mixed-list items discarded without refusal.

**Cause:** The parser substitutes its own request for the caller request and loses the failure witness.

**Correction:** Apply the existing structured-input validator and return the named typed refusal for unsupported values.

**Verification:** Source bytes and the quoted owner guidance were read during this extension. Historical fixtures were inspected; no historical execution or detector effectiveness is newly claimed. Source ownership relocated without changing the bound source bytes, quoted evidence, applicability, or admission; this is not new historical execution.

**Applicability:** A declared structured-step or ingress contract rejects scalars, malformed mappings or invalid collection members.

**Exceptions:** Preserve documented valid normalization, supported optional fields and existing refusal vocabulary. Do not tighten unrelated schemas.

## Guidance contract

**Conditions:** The declared input schema requires a structured step and already has typed refusal semantics.

**Construction:** Validate the original value before construction, return the existing typed refusal for unsupported shape and preserve valid input behavior.

**Example:** if not isinstance(raw_step, dict): return Err(RefusalRecord(code="BAD_STEP", reason="Step must be a mapping"))

Ordered signature: `(code: Code) -> code: Code`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
