---
name: adversary-parser-work-antibody
description: "Review exact parser work bounds."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-parser-work-antibody.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "antibody"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-parser-work-antibody

Generated guidance; edit the canonical typed contract and instruction resource.

# Review procedure

Use the attached prompt to inspect exact-parser work ordering. Return a candidate finding with the declared grammar, source location and actual control evidence. Never promote a sighting to an activated detector.

## Attached review prompt

# Exact parser review

Read the actual candidate parser and its declared grammar. Trace each public entry to the arithmetic constructor. Check type, lexical and work limits before construction; inspect the retained malformed-input control and an admitted large-cost control. Do not run an unbounded exponent payload in this IDE. Report the exact source path and the deciding checker evidence or unavailable check. Decimal/exponent support may be intentional under another resource contract. This prompt is candidate review guidance: it supplies neither independent danger evidence nor OEEIS admission.

## Digested lesson

Source: `_ic/nara/historical/oewas007/research/wdp_calibrated_recovery/reviews/r2_code.json` @ `32454fda2b42454792f6d49ec22e7304a4e30ba6` (sha256:fa836b342cd46d9a348e77670cf10dcf9eaa799321e737c54c8d9c031ad760fe).

Source excerpt (evidence to inspect):

```text
Exact string type, input-length and ASCII integer-or-ratio syntax checks precede Fraction construction.
```

**Failed Claim:** A parser constructor call or a prompt warning alone proves the parser safe or activates an antibody.

**Counterexample:** The historical repair adds pre-construction grammar checks and a legitimate large-cost control; the original exponent failure and the valid ratio case need different dispositions.

**Cause:** A literal constructor sighting is insufficient without the declared input contract and independent deciding check.

**Correction:** Attach the concrete exact-parser review prompt, inspect the harmful and benign cases, and request an independent bounded checker when defect admission is needed. Keep this candidate inert.

**Verification:** Read the complete Round 2 code repair review and retained resource-probe outputs. Compilation checks only source/prompt custody and literal example separation, not semantic detector accuracy or historical replay.

**Applicability:** On-demand review of strict canonical integer/ratio input boundaries.

**Exceptions:** Constructor text alone is not a defect. Explicitly bounded alternative grammars and prior lexical admission are benign; a prompt never supplies the independent danger signal.

## Guidance contract

**Antibody Id:** ab_preconstruction_exact_parser_work

**Prompt Uri:** prompt://adversary/digestion/parser/review/EXACT_WORK

**Signal1 Epitope:** Fraction(value)

**Signal2 Required Danger:** PRECONSTRUCTION_WORK_VIOLATION

**Harmful Example:** value = '1e1000000000'
parsed = Fraction(value)  # before lexical admission


**Benign Example:** admitted = require_bounded_integer_or_ratio(text)
parsed = Fraction(admitted)


Prompt resource: `operads/catalog/contracts/v1/prompts/exact_parser_review.md` (sha256:e6fb1e44c1e5e684d8bf820b2745168ee5f638b29ea964b6d3c94e2ed97fb1d0).

Use the bound prompt when reviewing this failure class. Candidate only; the existing OEEIS admission and two-signal gate decide activation.

Ordered signature: `(candidate: Code) -> result: Audit`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
