---
name: adversary-parser-work-antipattern
description: "Reject syntax before costly parsing."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-parser-work-antipattern.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "anti_pattern"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-parser-work-antipattern

Generated guidance; edit the canonical typed contract and instruction resource.

# Review procedure

Review every public parsing entry and helper. Reject out-of-grammar text before costly arithmetic. Check both malformed exponent input and an admitted large aggregate cost; an over-tight cap is also a defect.

## Digested lesson

Source: `_ic/nara/historical/oewas007/research/wdp_calibrated_recovery/reviews/r1_code.json` @ `32454fda2b42454792f6d49ec22e7304a4e30ba6` (sha256:32f2b965aa32c08af29a76b202e98e2104d3e787d52d7edfaf7ab74ef8e1d27f).

Source excerpt (evidence to inspect):

```text
Both parsers call Fraction(value) before checking canonical rational syntax.
```

**Failed Claim:** A short text-length bound and a post-construction bit-size check bound exact-parser work.

**Counterexample:** The short exponent payload 1e1000000000 reached Fraction before lexical rejection; historical bounded child probes were killed at both public verifier entries.

**Cause:** Arithmetic construction preceded the declared integer-or-ratio lexical admission.

**Correction:** Check exact type, bounded length and the declared ASCII integer-or-ratio grammar before Fraction. Preserve reduced form and exact-size checks afterward, and allow every legitimate aggregate cost.

**Verification:** Read CAL-CODE-001, the Round 2 repair review and r2_resource_probe.json: the retained successor rejects both entries and retains a legitimate large-cost positive control. No dangerous exponent payload was executed in this digest.

**Applicability:** Strict canonical integer/ratio parsers and verifier certificate inputs.

**Exceptions:** An intentionally supported decimal/exponent grammar needs its own work bound. Do not copy the historical 160/4096 limits into unrelated schemas, or use timeout as a mathematical counterexample.

## Guidance contract

**Failure:** Constructing exact arithmetic values before lexical/resource admission.

**Witness:** Fraction(value) receives a short exponent payload before canonical syntax validation.

**Repair:** Admit the declared lexical form first; then construct and verify exact canonical values, preserving legitimate aggregate costs.

Ordered signature: `(candidate: Code) -> result: Audit`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
