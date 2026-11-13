---
documentation_contract: symbol-game-documentation/v1
title: "Paper 010: Study guide"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/010_pfp_holonomy_checks_and_model_pilots/paper.md
---

# Study guide: Paper 010

**AuthorityEffect:** None. Study first, attempt the [quiz](quiz.md), then use the
separate [instructor key](answer_key.md). Definitions come from manuscript Section 2;
pilot data and limits come from Sections 3–6.

## 1. Validate the algebra

A finite table must be total and closed, have a two-sided identity and inverses,
and be associative for every triple. Names and values need their declared types.
The S3 construction uses (p q)(x)=p(q(x)); Q8 uses integer quaternions.
No floating-point tolerance enters these checks.

In Q8, i j (−i) (−j)=−1, while i(−i)j(−j)=1. The code labels 1 and −1 as
`e` and `-e`. A −1 square is non-flat even though −1 is central and self-inverse.

## 2. Keep the path convention visible

Plaquettes are (r,c), (r+1,c), (r+1,c+1), (r,c+1). The last two edges use inverses
of stored positive links. Reversal inverts the product. Moving the basepoint to the
next vertex conjugates by the inverse of the first edge. Adjacent gauge factors
cancel along a path, leaving `g(start) hol(path) inverse(g(end))`.
A closed product is conjugated at its basepoint: identity status persists, but its
exact element can change.

Use a non-central S3 product of order three to detect reversal errors. The Q8
commutator −1 alone cannot distinguish its two orientations.

## 3. Local flatness and global gauge triviality

The declared lattice includes its plaquettes. An open rectangle has trivial fundamental group,
so flatness lets a rooted spanning-tree gauge trivialize every edge. On a torus,
flatness leaves commuting cycle products A and B; both must be identity for a
trivializing gauge. A=−1, B=1 therefore gives `FLAT_NONTRIVIAL`.

The host accepts open dimensions at least 2 and torus dimensions at least 3.
Endpoint-only names cannot distinguish parallel torus edges at size 2.
For seam links a,b, only the seam corner can be non-flat, with product b a b⁻¹ a⁻¹.
Enumerating S3² and Q8² covers 36+64=100 connections in this family, not all connections.

## 4. Optimization and proof boundary

Four identity links have identity product. Skipping their multiplications preserves
the complete check; every other plaquette is still tested. The number skipped is
gauge-dependent. Group validation takes O(|G|³); after validation, the lattice pass
and tree work take O(LM). A submitted path of k edges adds O(k) work.

Lean formalizes only the four-identity-link observation. The named report lists one
axiom-free theorem. The historical full-module report lists 26 declarations: 25
axiom-free and one using `propext`, including generated structure declarations.
Neither report formalizes the parser, flatness host or pilot analysis.
Read the current receipt to distinguish static report checks from an executed build.

## 5. Require a witness

| Verdict | Checked obligation | Near miss |
| --- | --- | --- |
| NOT_FLAT | Actual plaquette with its matching nonidentity product | Correct label, wrong product or winding four-cycle |
| FLAT_TRIVIAL / PURE_GAUGE | Full gauge making every positive link identity | Missing vertex, conflicting alias or a remaining nonidentity edge |
| FLAT_NONTRIVIAL | All plaquettes flat and a closed path with matching nonidentity product | Open path, identity loop or non-flat input |

The verifier accepts valid plaquette rotations and either orientation. Parsed edge
or vertex aliases cannot overwrite entries. Unknown elements are refused before a
verdict rather than treated as identity or silently omitted.

## 6. The right C017 denominator

Twenty-five historical responses are recorded. Fifteen solution records are retained: 13 parsed certificates and two parser-error
wrappers. Fresh host checks accept 10 and reject 5 overall, including both wrappers. The other ten retain labels/reasons and zero
recorded acceptances; they cannot be freshly certificate-checked. All 25 extracted
entries can be compared with the original reports, which is a different check.

Arm 1's labels match 4/5 while certificates score 0/5 under the old harness.
Three refusals concern vertex order before products were compared; those products
are missing. The current host accepts either orientation but cannot recover absent payloads.

## 7. Audit historical tables

Table 3 reports original checker decisions out of ten per cell. C049 has two
different panels; C050 repeats one panel. Table 4 uses the author's case-by-case
classification (36 of 60 identifiers name a verdict/answer) and a prior checker replay.
Recounting does not independently assign these categories or measure model reliance
on leakage. Readers can dispute the published annotations.

Always refusing passes 10/10 in original C045 and C046. Acceptance there cannot
separate mathematical answers from that baseline. Paired checkers may share code
or permissive failure modes; inspect obligations and negative controls before treating
agreement as added assurance.

## 8. Name the execution supporting the claim

| Operation | Evidence produced | Limit |
| --- | --- | --- |
| C017 replay | Fresh verdicts and 15 solution-record checks | Ten payloads remain missing; no new responses |
| Pilot recount | Hashes, 25 extraction comparisons, Table 3/4 counts | Original flags and prior record; no fresh C045–C050 checker execution |
| Lean build/census | Result under the actual pinned compiler | Only the identity lemma; confirm the build ran |
| Deposit verification | Membership and byte custody | Does not establish mathematical truth |
| Hosted-model trial | New responses under recorded settings | Requires actual requests and suitable experimental design |

Run the capstone and explain its fields. Future performance work needs opaque IDs,
stripped answer notes, repaired checker refusal rules, negative controls, matched
conditions/budgets, provider/error metadata, predeclared samples and complete retained
responses. The package provides no new provider trial, learner study, physical
result or operational authority.
