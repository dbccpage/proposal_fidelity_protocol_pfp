---
name: woland-silent-coercion-antipattern
description: "Find malformed workflow inputs silently wrapped or filtered into valid-looking steps."
metadata:
  omega-arity: "1"
  omega-contract: "omega_engine_operads/catalog/contracts/v1/lessons/woland-silent-coercion-antipattern.json"
  omega-contracts-digest: "sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f"
  omega-generated: "oewas.typed-capability.v1"
  omega-kind: "anti_pattern"
  omega-residual: "unknown"
  omega-source-colours: "[\"Code\"]"
  omega-target-colour: "Audit"
---

# woland-silent-coercion-antipattern

Generated guidance; edit the canonical typed contract and instruction resource.

# Silent input schema coercion

Reuse AP_PY_013. Inspect the declared boundary before calling a conversion invalid. A scalar wrapped into an invented operation or an invalid mixed-list item silently dropped is a concrete witness when the schema requires a structured step. Report the original value/index and the code that hides it.

Repair through HP_PY_013 at the same boundary with an explicit typed refusal. Preserve all valid behavior. Schema-authorized normalization is an exception. This instruction is review guidance, not an executable detector or activated guard.

## Digested lesson

Source: `omega_engine_operads/patterns/anti/python/AP_PY_013_silent_input_schema_coercion.md` @ `827d3b47743393a96441751de40e1b4be2b33d9e` (sha256:d900ba3880a893818e56b8efce6fb1bf1eae6b8bdb33627d5cc710d1469c44eb).

Source excerpt (evidence to inspect):

```text
A parser, workflow runner, or ingress boundary silently accepts malformed input structures (e.g. converting a bare scalar into a nullary operation, discarding non-matching items from a mixed list, or defaulting invalid JSON/YAML keys) without emitting a typed refusal.
```

**Failed Claim:** A malformed scalar or mixed collection can be silently repaired into executable steps without changing caller semantics.

**Counterexample:** A scalar becomes a fabricated nullary operation, or invalid items disappear from a mixed input collection.

**Cause:** Implicit wrapping and filtering erase the original specification error instead of returning the declared refusal.

**Correction:** Keep AP_PY_013 paired with HP_PY_013: refuse unsupported structure at the existing boundary and retain the offending item or index.

**Verification:** Source bytes and the quoted owner guidance were read during this extension. Historical fixtures were inspected; no historical execution or detector effectiveness is newly claimed. Source ownership relocated without changing the bound source bytes, quoted evidence, applicability, or admission; this is not new historical execution.

**Applicability:** Parsers and workflow ingress whose declared schema requires structured operation inputs.

**Exceptions:** Explicitly licensed normalization or filtering is permitted by its own schema; this pattern does not require every parser to share one input format.

## Guidance contract

**Failure:** Unsupported scalar wrapping, silent item filtering or default repair hides malformed structured input.

**Witness:** if not isinstance(raw_step, dict): raw_step = {"op": str(raw_step), "args": []}

**Repair:** Use the existing structured-step validator and return its explicit typed refusal, with the input index where available; preserve valid inputs.

Ordered signature: `(code: Code) -> findings: Audit`.

Contracts: `sha256:eeec5a0d727eae41436369698416eabff393a33d0ea7c7eb250036af9296661f`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
