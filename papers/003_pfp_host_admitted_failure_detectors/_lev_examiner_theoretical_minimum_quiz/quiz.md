---
documentation_contract: symbol-game-documentation/v1
title: "Paper 003: Detector admission, exact checks, and evidence limits"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/003_pfp_host_admitted_failure_detectors/paper.md
---

# Examiner theoretical minimum: Paper 003

Version 0.1.0, 2026-10-02. **AuthorityEffect:** None.

The [Apartment 50 preface](00_preface_at_apartment_50.md) is fictional staging.
These eight teaching levels are an original curriculum, not a historical
Examiner examination. Use the [study guide](study_guide.md) before attempting the
problems; keep the separate [instructor key](instructor_key.md) closed.

For every answer, identify the declared input, calculation or counterexample,
and the scope of the conclusion. Use integers and rational fractions for exact
work. Decimal approximations are permitted only for the confidence-bound
interpretation in Q23. Missing verification is an explicit open obligation.

## Level 0: Know what has been decided

**Q01.** A phrase detector flags a proposal; a policy holds it; a route checker
later accepts its witness. Explain the three decisions and identify whether
there was false suppression if the hold permanently blocked submission.

**Q02.** The AM-FSP-2 list includes `particle-hole symmetry on triangle`.
Compare its findings on "There is particle-hole symmetry on triangle
plaquettes" and "There is no particle-hole symmetry on triangle plaquettes."
What can the phrase comparison establish about the truth of either sentence?

**Q03.** Declare a directed-graph carrier with vertices `a,b`. Route I requires
irreflexivity; route L permits loops. The same proposal adds edge `(a,a)`.
Give its defect and valid near-miss status under these two contracts. List what
a loop-refusal detector must bind before admission, and explain why a near miss
from route L alone cannot qualify the detector for route I.

## Level 1: Compute the policy you actually have

**Q04.** Reconstruct the baseline/Appendix A gate for all six cases: no signals;
Signal 1 alone; Signal 2 alone with LOW/MEDIUM severity; Signal 2 alone with
HIGH/CRITICAL severity; both with LOW/MEDIUM; both with HIGH/CRITICAL.
Give the exact decision label and whether it refuses.

**Q05.** Compare that gate with `code/danger_gate.py`. Evaluate (a) one pattern
match plus a MEDIUM Signal 2 record of defect count zero, and (b) one pattern
match plus a MEDIUM record of defect count one. Identify both implementation
differences. Is either table the strict Boolean conjunction of two signals?

**Q06.** Let `m` be the match count and set Signal 2 to absent when `m=0`,
otherwise to `("HIGH",m)`. Compute the reachable decisions. Then change the
derivation so Signal 2 is absent for every `m`. What changes? Explain why
separately named inputs or four reachable test outcomes do not prove independent
derivation in a deployed pipeline.

## Level 2: Trace the host without inventing acceptance

**Q07.** At the canonical baseline, start with fuel 12, phase INTAKE, empty
coverage, and no witness. Submit one batch: cover `elem_all`; propose
`vertex_bits=[0,1,0]`; VERIFY. Give the decision, final semantic state,
remaining fuel, and whether the witness has been proved wrong.

**Q08.** Start again and append COVER_ELEMENT after VERIFY. Give the decision
and fuel. Compare an empty batch and the moment of exhaustion at the canonical
baseline with the package host. State which implementation each result belongs to.

**Q09.** After reaching TERMINAL, the baseline host still records a receipt for
each further attempted batch. Does fuel 12 bound all receipt count, retained
bytes, or wall-clock time? State the bound fuel does establish and the additional
limits a caller would need.

## Level 3: Read evidence with its source attached

**Q10.** An editor changes a package receipt's fuel field and recomputes its
unkeyed digest chain. Explain why the package verifier may accept it, what the
canonical verifier additionally checks, and what neither verifier authenticates.
Distinguish a digest edit without recomputation from a fully recomputed receipt.

**Q11.** A stored historical pilot reports terminal certificates, while the
audited host returns NO_NATIVE_PORT. May the two records be pooled into an
effectiveness estimate? Specify what would be needed to reproduce the historical
certificates and to claim a current randomized treatment effect.

**Q12.** Prepare a source table for the deposit reviewed at
`e11c07ce90318309f058c8097ffd1c440a8ffb84`, the canonical host baseline
`52cb5457f6c485ba548cfd292f6012a941ed22cf`, the Appendix A audit
`30609de2c3928238715375a9bac608256fa381d8`, and the historical correction
`fdc0035a81c45e10b900fc917b8b0710df81391f`. Does any of those pins alone
establish the behavior of today's default branch? Explain what a fresh test
receipt must add.

## Level 4: A sum is not a count of witnesses

**Q13.** For `n=2,K=2,t=1/2`, compute the Hill ratio for signal lists
`[1,1/2,-7]` and `[2]`. Show the exact activation threshold and explain
why negative entries do not cancel positive entries in this definition.

**Q14.** Keep `K=2,t=1/2` and cap each positive signal at `3/4`.
Find the least possible number of contributing entries. Does that prove as many
independent agents agreed? Also assess two unit entries copied from one source.

**Q15.** Derive the threshold for `n>0,K>0,0<t<1` by clearing the denominator.
Handle `t=0` and `t=1` separately. Would `n=True` or `n=3/2` be a
legal exponent for the package's exact integer-exponent helper, even though the
mathematical lemma permits positive real exponents?

## Level 5: Screen the predicate that will run

**Q16.** Let `U={a,b,c}`, screened predicate `P={b}`, executed predicate
`E={a,b}`, and valid self panel `S={a}`. Is the detector admitted by the
screen? Does it fire on the panel? Supply the smallest counterexample.

**Q17.** Prove that screening is sound for every finite self panel if and only
if `E(x) implies P(x)` for every input. Use a singleton panel for necessity.
Is equality required for this one property?

**Q18.** Derive the additional implication needed to avoid rejecting a rule
that would not fire on a panel. Then let `E=P={b}` and `S={a}`: if a
new independent checker establishes that `b` is valid, what has admission
failed to guarantee? Distinguish predicate agreement from panel coverage.

## Level 6: Repair the physics claim's scope

**Q19.** For the manuscript's matrix
`H=[[0,1,-1],[1,0,1],[-1,1,0]]`, compute `SHS` with
`S=diag(1,-1,1)` and the cycle product of `sgn(-H_ij)`.
Repeat the cycle-product test when all three off-diagonal bonds are positive.
What separates the two triangles? Why does the standard local particle-hole
sign assignment still fail on an odd cycle?

**Q20.** For the attractive onsite Hubbard model with real, spin-independent
hopping, equal spin chemical potentials, and a real charge-channel
decoupling, explain why equal spin-sector determinants give nonnegative
configuration weights on a non-bipartite lattice. Does this establish the local
particle-hole symmetry of Q19? What assumption is missing from "equal
populations alone imply sign freedom"?

**Q21.** Classify three claims: a restricted model has a checked sign-free
formulation; every instance in the NP-hard sign-problem class has a generic
polynomial-time exact solution without complexity consequences; changing to a
Majorana basis alone ensures positive weights. State the missing obligations,
including why the hardness result is conditional on the complexity assumptions
and why a phrase match cannot verify the Majorana or meron conditions.

## Level 7: Design a study that can answer its question

**Q22.** Ten allocated runs yield three verified witnesses, two refusals, one
timeout, and four unavailable/unknown outcomes. Compute the primary success
fraction. Separately, of 20 independently valid eligible proposals, two were
blocked; 100 invalid proposals were also blocked. Compute false suppression
and explain why the invalid proposals cannot enlarge its denominator.

**Q23.** With zero false suppressions in `n` independent opportunities,
derive the one-sided exact upper 95% bound. Evaluate `n=8`.
Show using `(99/100)^n` why 298 opportunities miss the strict 1% gate and
299 meet it. Can 1,000 tagged rows generated from 40 base strings be substituted
for 1,000 independent opportunities? Does a separate 95% bound on each of three
routes automatically give a simultaneous 95% guarantee?

**Q24.** Draft the smallest confirmatory protocol that identifies the D-minus-R
contrast. Include allocation/dependence unit, disjoint discovery and held-out
instances, frozen source/detector/checker versions, common budgets and feedback
opportunity, shadow checks, success and safety gates, missing outcomes, and
stopping rules. Explain the ceiling if the route adapters remain unavailable
or the assisted arm A supplies solutions.

## Grading and advancement

Score each question from 0 to 4: 0, absent or wrong; 1, a label without support;
2, a partly correct calculation or argument; 3, correct result with its contract
and evidence limit; 4, complete reasoning plus the requested counterexample or
source binding. Maximum: 96.

Mastery requires at least 3 on every question and correction of every unsupported
promotion of a finding, receipt, refusal, finite panel, or historical run.
A high total cannot compensate for claiming a certificate from NO_NATIVE_PORT.
This rubric evaluates the declared exercises; it grants no research or
operational authority.
