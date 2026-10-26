---
documentation_contract: symbol-game-documentation/v1
title: "Paper 010: Instructor key"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/010_pfp_holonomy_checks_and_model_pilots/paper.md
---

# Instructor key: Paper 010

**AuthorityEffect:** None. Use after the [quiz](quiz.md). A plausible label alone
earns at most one of each question's three points.

## Levels 1–2

1. i j (−i) (−j)=k(−i)(−j)=(−j)(−j)=−1. Reordering to i(−i)j(−j) gives 1.
2. Associativity supports group/path reasoning and is not implied by totality.
   S3 has 6³=216 triples, Q8 has 8³=512; validation costs O(|G|³).
3. `GroupTableError`: a list is not a declared element and may be unhashable. No verdict.
4. Reversal gives hol⁻¹; rotation gives U01⁻¹ hol U01. Central self-inverse −1
   stays unchanged under either operation.
5. Accept if it is an actual plaquette, its listed-order product is `r`, and it
   is nonidentity. The old harness accepted only one convention.
6. Adjacent g(v)⁻¹g(v) cancel, leaving endpoint factors. Identity status and
   conjugacy class persist for a closed path; the exact element may change.

## Levels 3–4

7. Set g(root)=e and g(v)=g(u)Uuv along the tree. Flatness permits plaquette path
   substitutions, so path independence on the rectangle extends this relation to
   all edges. Each open dimension must be at least 2.
8. `FLAT_NONTRIVIAL`: nonidentity A cannot be conjugated to identity.
9. j i (−j)(−i)=−1, so the corner and connection are `NOT_FLAT`.
10. Skipping changes 20→0; flatness, gauge triviality and verdict persist.
11. Validation O(|G|³); lattice/tree/gauge work O(LM); a k-edge certificate path O(k).
12. Four identity links give identity. The named theorem has no axioms; the full
    historical report has 26 declarations, 25 axiom-free and one `propext`.
    The complete checker and empirical analysis are outside the proof.

## Levels 5–6

13. Reject: `gauge missing`. A matching label does not meet the witness obligation.
14. These spellings parse to one edge/vertex. Reject duplicates, even equal ones.
    Unknown/non-string links receive `LatticeError` before inverse lookup.
15. Accept an actual non-flat plaquette/product; reject a wrong product. Accept a
    full trivializing gauge; reject a missing vertex. Accept a flat torus with a
    matching closed nonidentity loop; reject an open or identity loop. A four-cycle
    can wind on a torus without bounding a plaquette.
16. 25 recorded responses; 15 retained solution records, 10 accepted and 5 rejected afresh.
    Thirteen records are parsed certificates, two are parser-error wrappers.
    Ten missing payloads retain historical failures; their fresh checks are not run.
17. The messages establish convention-based rejection before product comparison,
    not a wrong product. Absent payloads cannot be reconstructed.
18. This shorter prompt produced an accepted response within its limit on this
    case. Several prompt changes, budgets, provider/sampling conditions and one
    reply per arm prevent a general savings or causal estimate.

## Levels 7–8

19. C049 changes cases (stealth 5→9), so it is not a matched repeat. C050 repeats
    ten cases (7→6); five outcomes change, two involving API errors. Tasks, small
    authored panels, leakage and absent statistical design preclude model ranking.
20. 7+5+4+10+5+5=36/60. This is the author's identifier classification, not a measured
    dependence of model replies on leaked answers.
21. Model counts do not exceed the refusal baseline. The second checker accepts
    vacuous/unsupported outputs in the cited controls; agreement alone supplies
    no general independent assurance.
22. C017 replay executes algebra/certificate checks. Table 3 recount reads old
    flags; Table 4 recount reads annotations/prior checker outcomes. A fresh Lean
    build invokes the pin. A new trial obtains new provider responses.
23. Membership and byte identity are checked. Correctness, proof scope, design
    and rendering need separate evidence. Record actual failed/not-run toolchain
    status and retain earlier successful receipts as historical.
24. Use held-out cases with opaque IDs and stripped notes; repair/check refusal
    rules and both checkers; match conditions/budgets; record providers, errors
    and repeated samples; predeclare comparisons and retain complete outputs.
    This proposes work rather than reporting its execution.

## Capstone rubric: eight points

One point for each audit item named in the quiz, supported by a calculation,
output field or source. S3 has 18 commuting seam pairs and Q8 has 40: 58 flat of
100, comprising 2 `FLAT_TRIVIAL`, 56 `FLAT_NONTRIVIAL`, and 42 `NOT_FLAT`.
Gauge skipping is 20→0. C017 counts stay 15/10/5 with ten missing payloads.
Historical table recounts preserve Tables 3/4 and do not execute the formal checkers.
The capstone runs neither Lean nor a provider. An 80-point practice score or
receipt grants no further authority.
