---
documentation_contract: symbol-game-documentation/v1
title: "Paper 010: Theoretical minimum quiz"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/010_pfp_holonomy_checks_and_model_pilots/paper.md
---

# Theoretical minimum: Paper 010

**AuthorityEffect:** None. Read the fictional [preface](00_preface_at_apartment_50.md)
and [study guide](study_guide.md). Keep the [instructor key](answer_key.md) closed
while answering. Use the manuscript's vertex order and group convention.
In the Q8 code, `e` means 1 and `-e` means −1.

Each of 24 questions earns 3 points: result, calculation/evidence, and condition/limit.
The capstone adds 8 points, for 80 total. These are practice criteria; no learner
outcomes were measured.

## Level 1: Group data before a verdict

1. A Q8 square has ordered links i, j, −i, −j. Compute its product and give a
   permutation of these factors that changes the product.
2. Why check associativity before using a supplied table? How many triples occur
   for S3 and Q8? State the asymptotic validation cost.
3. A table has all the right row labels, but one product is a list rather than an
   element name. May the host issue a verdict? Name the refusal type.

## Level 2: Orientation, basepoint and gauge

4. Derive the effects of reversing a closed path and rotating its basepoint from
   v0 to v1. Why does question 1's Q8 example hide some orientation mistakes?
5. The canonical witness of C017 `pois_01` has product `r2`. Its reversed witness
   states `r`. Must the package accept it? What additional checks are required?
6. Show cancellation in a gauge-transformed path product. Which aspects of a closed
   holonomy persist, and which can change?

## Level 3: Local and global flatness

7. Every plaquette of a valid open 2×3 lattice is flat. Explain why a spanning-tree
   gauge trivializes every edge. State the host's minimum open dimensions.
8. A flat Q8 torus has A=−1 and B=1. Give its verdict and explain why local
   flatness does not supply a globally trivial gauge.
9. A 3×4 Q8 torus has column seams a=i, row seams b=j and identity links elsewhere.
   Compute b a b⁻¹ a⁻¹ at the seam corner. Is it flat?

## Level 4: Optimization and formal scope

10. A trivial 4×5 torus has 20 skippable plaquettes. After a gauge differing at
    neighbouring vertices, none is skippable. What changes and what persists?
11. Separate group-table validation cost from lattice checking. How does verifying
    a supplied loop depend on its length?
12. What does the named Lean lemma establish? Distinguish its one-declaration census
    from the historical full-module census of 26 declarations and from the Python host.

## Level 5: Certificates and malformed inputs

13. A reply states `FLAT_TRIVIAL` without a gauge. Its label matches the host.
    Should the certificate verifier accept it? State the obligation.
14. A mapping contains `0,0->0,1` and `00,0->0,1`; a gauge contains `0,0` and
    `00,0`. Why must later entries not overwrite earlier ones? What should
    happen to unknown or non-string link values?
15. Give a positive certificate and a near miss for each verdict. Why is an
    arbitrary four-cycle insufficient as a `NOT_FLAT` plaquette witness?

## Level 6: Reading C017

16. Five runs of five responses are recorded. How many solution records can be
    checked afresh? Separate parsed certificates from parser-error wrappers. Reconcile accepted/rejected counts with ten missing payloads.
17. Arm 1 has four labels equal to the host and zero accepted certificates. What
    do its orientation refusals establish? What cannot be reconstructed?
18. One torus response is unfinished at 8,000 tokens; another arm's response is
    accepted at 2,810. What conclusion fits this case? What confounds prevent a
    general causal claim about token savings?

## Level 7: Reading the formal pilots

19. Distinguish C049 panels A/B from C050 runs 1/2. Why do these rows not establish
    a ranking of the three models?
20. Recount the six author-annotated identifier rows: how many of 60 name a verdict
    or answer? Does this show that models relied on the names?
21. A constant refusal passes 10/10 under both original C045 and C046 checkers.
    What does this imply for interpreting acceptance and the second checker?

## Level 8: Reproduction and evidence boundaries

22. Distinguish fresh C017 host replay, Table 3 recount, Table 4 prior replay record,
    a fresh Lean build and a new hosted-model trial.
23. A ZIP matches its manifest. Which obligations are established, and which still
    require checks? How should an unexecuted pinned toolchain be recorded?
24. Propose a pilot assessing unaided performance and a prompt change. Address
    leakage, checker defects, matched budgets, provider metadata, sampling and
    retained artifacts. Do not infer that the proposed pilot has been run.

## Capstone: An offline evidence packet

From the package root:

```text
python tools/study_capstone.py --output /tmp/paper010-capstone.json
python code/replay_c017.py
python code/recount_pilots.py
```

On Windows, choose a writable output path. Inspect the JSON and write an eight-point
audit: Q8 order; S3 reversal; seam verdicts; gauge-dependent skipping; certificate
controls; malformed-input refusals; denominators and historical Table 3/4 counts;
and the exact execution scope. A green exit alone is not an answer.
