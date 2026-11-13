---
documentation_contract: symbol-game-documentation/v1
title: "Paper 005: A bounded checked-proposal session"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/005_pfp_practitioners_field_manual/paper.md
---

# Theoretical minimum: Paper 005

**AuthorityEffect:** None. Read the fictional [Apartment 50 preface](00_preface_at_apartment_50.md). The [source reading](../paper.md#4-follow-the-complete-session) supplies the definitions; the [study guide](study_guide.md) contains a separate instructor key.

Use the ordered directed edges (ab,bc,ca), rational claims c=(1,1,1), positive weights w=(1,2,3), and ordinary additive potentials unless a question explicitly changes them. The symbol `a>b>c>a` sketches edges; it declares no filled face. Give exact calculations and identify the move or obligation being checked. All implementation questions refer to this package's patched governor, not every repository surface.

The examination has eight levels, four questions each. Attempt it without the instructor key. The budget in Question 22 is a separately declared exercise policy; UNKNOWN is not a terminal status implemented by this four-move governor.

## Level 0: Declare the instance

1. List the vertices, ordered edges, coefficient system, claims, weights, units, allowed changes, and cell declarations needed to reproduce this example. Which datum would an undisclosed wraparound-clock convention change?
2. Is a weight evidence that one claim is true? What additional modeling decision is needed before replacing a measured edge claim?
3. Compute the score D_c(0) and the minimum Phi_w(c). Explain why six and three can both be correct reports about the same unchanged claims.
4. Compute df and r for f=(0,-2,-1). Contrast selecting this potential with replacing claims by c'=(-2,1,1). State each resulting cycle sum and minimum.

## Level 1: Certify the small calculation

5. Prove the lower bound three for every potential, and give a witness attaining it. Distinguish that proof from testing a few potentials.
6. Let q=(1,1,1). Show q dot df=0 and |q_e|<=w_e, then use q dot c to obtain a lower bound on the weighted discrepancy. What completes the optimality argument?
7. Replace f by f+(t,t,t), with t rational. What changes? Does the unique cheapest edge make the absolute potential unique?
8. Reverse ca into ac. Give the correctly transformed third claim and potential difference. What false conclusion could result from keeping the claim +1 after reversing its arrow?

## Level 2: Admit and refuse proposals

9. Trace ASSERT (1,1,1), replacement CUT (5,0,0), replacement CUT (-2,1,1), VERIFY ZERO_OBSTRUCTION, and RETRACT to the saved post-ASSERT snapshot. Give the minima and admission outcomes; explain where the snapshot identifier comes from.
10. After ASSERT, propose either an empty replacement map or just ab=-2, bc=1. Give the refusal and active-state outcome. Why does the initialization default for unasserted edges not authorize this CUT?
11. Propose the complete replacement (0,1,1). Compute its minimum and the verdict from the original instance. Is it an exact repair?
12. Propose the complete replacement (2,1,0). Compute its minimum and verdict. Does `IdempotentStationary` establish that the claims were unchanged or the proposer has made progress?

## Level 3: Identify the checked obligation

13. Use a section CUT to move the original all-zero potential to (0,-2,-1), with claims fixed. Which score decreases, and which minimum remains unchanged?
14. Install the consistent claims (-2,1,1) while the stored section is zero. Compare ZERO_OBSTRUCTION and ZERO_DEFECT. Then explain why EDGE_MATCH:b,c can pass at the original minimizing potential while the original ZERO_OBSTRUCTION fails.
15. Try EDGE_MATCH:d,e, EDGE_MATCH:a,c, and the malformed EDGE_MATCH:a. What should the patched verifier return, and why is default-zero comparison insufficient?
16. A CUT supplies both a section and replacement claims. Another supplies an undeclared section key d, and a third supplies a Boolean section value. Name the respective refusals and preserved active state.

## Level 4: Respect the execution route

17. The native calculator is unavailable. What can the hand argument, the printed worksheet, and the Python enumeration session each establish? Which execution claim remains unavailable?
18. A native executable is configured but refuses during projection after a replacement's score was calculated. May Python substitute a result? What must happen to the pre-CUT active claims, section, and admitted history?
19. Represent the three unit claims with supported `Edge` object keys rather than tuple keys. What minimum should result after normalization? What must happen to an additional undeclared claim (d,e)=9?
20. Does scoring a graph with a duplicate vertex or duplicate directed edge produce a defensible minimum? Identify the check boundary in this package. Distinguish duplicate directed edges from the separately declared reverse edge (b,a).

## Level 5: Bound the inference

21. Compare the harness inputs `"1/10"`, integer 1, JSON number 0.1, and JSON true. Which are accepted as exact claim values? Why is converting a float to `Fraction` insufficient?
22. Under a separate budget of two proposal attempts, both fail and candidates remain unexamined. Give the scoped terminal report. Can two refusals certify global impossibility, or authorize a third unbudgeted attempt? Is this policy already implemented by the demo?
23. Does accepting non-increase prove finite termination? Would strict descent through 1, 1/2, 1/4, ... prove it over the rationals? State an additional condition that would support termination.
24. Change the weights to (1,1,1). Give two different minimizing residuals for the original claims and potentials attaining them. Does equal optimal cost select the true event statement?

## Level 6: Keep evidence in custody

25. What does an executable SHA-256 pin establish? What source-to-binary, producer-authentication, and semantic obligations remain?
26. A saved record reports 75 passing tests against an earlier Windows executable. The current package has new patches. What can be claimed now? Explain why a skipped native test cannot be counted as a passing native run.
27. Both manifests and the deterministic ZIP verify. Does that validate the graph interpretation, all quiz answers, a live model comparison, or full RFC 8785 conformance? State the narrower finding.
28. Design a minimal reproduction record for this session. Include calculator selection, exact instance, source and file bindings, commands and tools, refusals, admitted state, snapshot restoration, and test skips. Which values must come from execution rather than reconstruction?

## Level 7: Transfer and audit

29. Translate the example into measured time offsets that are frozen observations. Which permitted potential operation remains meaningful? Can it make the original minimum zero? What extra model would be needed to justify changing observations?
30. A proposer deletes the cheapest edge or sets its weight to zero to obtain a better score. Is that a repair of the declared instance? Describe the required response or explicit new declaration.
31. The native spanning-forest search reaches its bound and refuses. What inference is justified, and may the same configured step switch to Python? Is the offline enumeration route a bounded search controller?
32. Execute the capstone: ASSERT original claims; save its actual snapshot; refuse an empty CUT; refuse (5,0,0); admit (0,1,1); admit (-2,1,1); VERIFY; RETRACT. Record the path, verdicts, score transitions, and restored claims. State the strongest supported result and one claim it does not establish.

## Local grading rubric

Award two points per question: one for the exact calculation or correct implementation outcome, and one for the declared scope or missing obligation. A level passes at seven of eight points with no unsupported acceptance. This threshold is an instructional choice, not an empirically validated measure of reasoning ability.

Do not pass the corresponding level if an answer silently changes the carrier, treats omitted replacement claims as zeros, replaces a configured native refusal with an accepted Python value, promotes an unfinished search to impossibility, or treats a checksum as semantic proof. Mark an unsupported step as an open obligation; return the implementation's actual refusal for a violated input contract. Keep mathematical obstruction, runtime refusal, and unavailable execution evidence distinct.
