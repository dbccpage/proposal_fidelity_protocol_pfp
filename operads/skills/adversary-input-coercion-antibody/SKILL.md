---
name: adversary-input-coercion-antibody
description: "Use a prompt-attached candidate to review silent structured-input coercion with a benign control."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-input-coercion-antibody.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "antibody"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-input-coercion-antibody

Generated guidance; edit the canonical typed contract and instruction resource.

# Candidate input-coercion review attachment

Use the bound Typed input review prompt with the supplied code and declared schema. Reuse ab_silent_input_schema_coercion and AP_PY_013. Compare the actual scalar-wrapping branch with the explicit BAD_STEP refusal control. Report a concrete witness or no finding; schema-authorized normalization remains allowed.

This is candidate instructional guidance. It installs no detector, imports no callable and grants no admission or activation. The existing OEEIS admission and two-signal gate retain ownership of any later enforcement. Historical source fixtures were read, not newly executed.

## Attached review prompt

# Typed input review

Review the supplied code against its declared input schema. Locate unsupported scalar wrapping, silent filtering or invented defaults that change a structured workflow request. Return the exact offending branch/value or state that no such witness was found. Preserve explicitly licensed normalization and the existing public API. Recommend the existing typed refusal and retain an item index where already supported.

Compare the harmful and benign examples in the attached candidate guidance. The antibody is a candidate instruction, not an admitted detector. Do not infer activation, executed checks or semantic correctness from this review.

## Digested lesson

Source: `eis/antibodies/anti_silent_input_schema_coercion.yaml` @ `827d3b47743393a96441751de40e1b4be2b33d9e` (sha256:7117daab59775eebc4378feb6c400b37a5279da10c9f8c2a365fb6004885b399).

Source excerpt (evidence to inspect):

```text
  Refuses parsers and workflow runners that silently coerce malformed input types
  (e.g. wrapping a bare scalar into a nullary operation) or silently filter out
  invalid items rather than emitting a typed refusal.
```

**Failed Claim:** An antibody name or a newly generated instruction automatically establishes an admitted executable detector.

**Counterexample:** The existing silent-input-coercion spec is explicitly candidate and carries separate harmful and repaired code fixtures.

**Cause:** Conflating a source-backed review instruction with admission would bypass existing OEEIS activation requirements.

**Correction:** Bind the existing candidate antibody to a tangible named review prompt and both controls; leave admission and the two-signal gate with their existing owners.

**Verification:** Source bytes and the quoted owner guidance were read during this extension. Historical fixtures were inspected; no historical execution or detector effectiveness is newly claimed. Source ownership relocated without changing the bound source bytes, quoted evidence, applicability, or admission; this is not new historical execution.

**Applicability:** On-demand review of code implementing a declared structured workflow/input boundary.

**Exceptions:** An epitope sighting alone is not a defect or admission. Schema-authorized normalization is benign; no prompt instruction supplies an independent host danger signal.

## Guidance contract

**Antibody Id:** ab_silent_input_schema_coercion

**Prompt Uri:** prompt://adversary/digestion/input/review/TYPED_INPUT

**Signal1 Epitope:** str(raw_step)

**Signal2 Required Danger:** STRICT_INPUT_VIOLATION

**Harmful Example:** if not isinstance(raw_step, dict):
    raw_step = {"op": str(raw_step), "args": []}


**Benign Example:** if not isinstance(raw_step, dict):
    return Err(RefusalRecord(code="BAD_STEP", reason="Step must be a mapping"))


Prompt resource: `operads/catalog/contracts/v1/prompts/typed_input_review.md` (sha256:e005ee8484efef8b98faefae64ad54729db566fba40b6d5689de8e935bfd432a).

Use the bound prompt when reviewing this failure class. Candidate only; the existing OEEIS admission and two-signal gate decide activation.

Ordered signature: `(code: Code) -> findings: Audit`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
