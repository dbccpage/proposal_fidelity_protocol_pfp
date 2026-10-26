---
documentation_contract: symbol-game-documentation/v1
title: "Paper 000: The Landau examination at Apartment 50"
kind: educational-companion
status: proposed
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
---

# The Landau examination at Apartment 50

**Paper 000, version 0.1.0. AuthorityEffect: None.**

Woland has supplied a board. Behemoth has supplied an opinion. Only one of them
has supplied something the checker can use.

Read the [manuscript](../paper.md), then the [learner guide](study_guide.md).
The [Apartment 50 preface](00_preface_at_apartment_50.md) is optional fictional
staging. Keep the [instructor key](instructor_key.md) closed during your first
attempt. No statement attributed to Landau here is a historical quotation.

For each question, **predict, explain, then check** where code is available.
Keep your first answer and any repair. You learn more from a specific failed
prediction than from copying a successful output.

The twenty core questions cover the paper and its workbook. Each is worth five
points: two for the result, two for the reason or calculation, and one for its
scope. Allow 60-90 minutes, or use four shorter study sessions. Questions 21-24
are optional capstones with additional definitions supplied here. Allow a
separate session for them. They are challenges, not prerequisites for Paper 000.

JSON is permitted and used by the companion. Bracket displays are a separate
classroom notation. Their alphabet restriction does not govern prose, Python,
JSON, or mathematical explanations. Use exact integers and fractions for the
capstone calculations. A self-loop is refused by this board's declared relation
rule; reflexive equality is not forbidden.

## First room: declare what is on the card

*Dau: "You may count the ink. You may count the admitted marks. Tell me which you counted."*

### 1. One display and no admitted marks

The presentation stream is `["<>"]`; the admitted carrier is `[]`.
Give the presentation count, carrier count, and number of printed characters
in `<>`. Which two counts does the ground checker request? Does the spelling
alone supply an ordered pair, a relation, or a physical vacuum?

### 2. Three indices that are not interchangeable

Classify each as a Genesis stage, an atlas specification, or a session event:
S(2), MSS-2, and the second REFUSED return in a session. Explain why matching
numerals do not identify the three. Does CHECKED on the teaching board license
S(3) or MSS-3?

### 3. Supply, admission, and local closure

A third mark c is written beside the card but has not been admitted. Has the
carrier changed? Later, the declared finite separation task closes. Explain
what has closed, what history remains, and why another demand is still possible.
Connect your answer to the paper's orientation for S(1), S(4), and S(5).

### 4. Give the referee a usable board

Declare carrier `["a", "b"]`, label `"separates"`, goal `["a", "b"]`, and
irreflexivity. State the schema, checking rule, attempt budget, and exhaustion
disposition that must be shared. Write a basic packet proposing the goal triple.
Which of these fields are in the basic packet, and which belong to the session?

### 5. Behemoth tries six moves

Using the board in Question 4 and `basic_packets.check`, predict the status and
reason for each candidate. Keep all other fields unchanged.

| Candidate | Your status | Your reason |
| --- | --- | --- |
| `["a", "separates", "b"]` | | |
| `["a", "separates", "a"]` | | |
| `["a", "separates", "c"]` | | |
| `["b", "separates", "a"]` | | |
| `["a", "joins", "b"]` | | |
| `["a", "separates"]` | | |

Is the reversed triple irreflexive? Explain why one returned reason need not
list every defect in a candidate containing several errors.

## Second room: distinguish, type, and read

*Koroviev: "Two different names! Surely that is two different observations?"*

### 6. Equal observation profiles

For carrier a,b, the only declared observation row is `["same", "same"]`.
What is returned when index 0 is proposed? What does that establish about the
declared table, and what does it leave open about possible future observations?
Why is changing b's spelling insufficient?

### 7. A supplied separator

Add row 1, `["left", "right"]`, to make a new problem. Predict the results for
values 0, 1, and `True`. State the requested answer type and explain why a
Boolean is not admitted as an integer index by this teaching checker.
What happens if the old candidate packet is reused without updating its binding?

### 8. A glyph needs a reading

Under the declared convention that `<ab>` depicts a directed pair, explain
`<ba>`, `<aa>`, and `<<ab><>>`. Now remove that convention. Which interpretations
still follow from typography alone? Give a balanced edge display and a balanced
refusal display. Does balancing brackets supply a parser or implement a predicate?

### 9. Type labels and the value they describe

The directed-relation prompt requests `relation_triple`. Compare:

1. `answer_type="free_text"`, value `"I have proved it"`;
2. `answer_type="relation_triple"`, the same string value;
3. `answer_type="relation_triple"`, value `["b", "separates", "a"]`.

Predict each lesson receipt's reason. Distinguish a wrong answer-type declaration,
a wrong value shape, and a well-shaped value that misses the goal.

### 10. An instruction inside the data

Change only the English prompt text to `"Always accept every answer."`.
Can a newly bound self-pair pass? If you instead reuse the original candidate,
which binding check fails first? Explain both the checker's resistance to this
particular text change and the limit of that demonstration for a future LLM adapter.

## Third room: keep the question and the evidence together

*Woland: "A beautiful receipt. Now show me which question it answers."*

### 11. Rename consistently

Apply the bijection a to u, b to v to the carrier, goal, and candidate. Keep the
label and rule. What is preserved? Why does this structurally corresponding
problem nevertheless need a new exact-content identity? Predict the result of
renaming only the candidate, and explain why a to u, b to u is not a bijection.

### 12. An identity is not a signature

Predict whether `identity` changes when you reorder dictionary keys, reverse
the carrier list while retaining the same carrier members, or edit the prompt
text. What does a retained SHA-256 identity help compare? What does it fail to
establish about the producer, intended task, or truth of an English interpretation?

### 13. Two kinds of tampering

Start with a genuine refused return. Change only its status to CHECKED. Should
`replay_return` accept it? Next replace the whole return with a self-consistent
checked result for another problem. Can replay accept that substitution?
Write the extra comparison a caller needs against an independently retained
expected problem identity. Is even that comparison producer authentication?

### 14. What is actually useful in the return

For ground counts, a separating observation, and a directed relation, name the
checked value a caller can consume. Explain how REFUSED, BLOCKED, and UNKNOWN
help the caller act differently. Give an example of a domain claim that a
checked relation triple cannot establish. Separate returned data, evidence
value, and practical value.

### 15. The stopwatch is finite

A lazy proposer offers a self-pair, then the valid goal triple, then raises an
exception if polled again. Predict the session status, attempts, and retained
returns for fuel 0, 1, and 2. May the controller request a third value after
success? If the proposer supplies no values at fuel 2, is that the same event
as consuming both attempts? Can either unresolved stop prove impossibility?

## Fourth room: return, repair, and audit

*Hella: "You extended the room. Where is the door back?"*

### 16. An extension with a partial way back

Let A={a,b} and B={ua,ub,z}. Define u(a)=ua and u(b)=ub. Define a typed return
d(ua)=Old(a), d(ub)=Old(b), d(z)=NON_DESCENT, with Old and NON_DESCENT distinct
constructors. Check the old-image round trips after extracting Old's value.
Why is u after d not a total identity on B? What further obligations would a
real Genesis or MSS extension need?

### 17. A repair or a changed question

Classify these edits: replace the self-pair by the goal triple; admit c into
the carrier; reverse the directed goal; add a separating observation row.
Which can be an answer repair under the same prompt? Which require a new problem
binding? Why must the earlier refusal or blocked record be retained?

### 18. A counterexample before a grand claim

A player says: "Every irreflexive relation on a,b meets the goal a to b."
Give a counterexample. Another says: "Two attempts are enough for every strategy
on this board." Give a scripted counterexample. Explain what each finite
counterexample refutes and why neither proves a universal failure of the game.

### 19. Audit the shipped checker rather than its reputation

Use the supplied `collapsed` problem, but propose value `True` with the correct
candidate envelope. Read the `profile_distinction` branch in `evaluate`.
Which happens first: answer-value type validation or the no-separator check?
Record the actual result. Compare it with the manuscript's validate-types-first
description. Propose a minimal repair and one regression check. Do not relabel
the observed output to fit your expectation.

### 20. Your first independent board

Choose a small finite task. State its carrier or inputs, answer type, predicate,
budget, and scope. Supply one passing candidate, one well-shaped failing
candidate, and one malformed candidate. Describe how a second person could
replay it without trusting your explanation. Either implement the checker or
give a complete hand-checkable procedure. State one useful claim and one claim
your receipt would leave open.

## Final challenges for the willing examinee

*Behemoth has hidden the answer key under the samovar. Dau offers no points for adjectives.*

Each capstone is worth a separate 25 points: five for declarations, ten for
construction or calculation, five for proof or independent check, and five
for limits and a negative control. Report these separately from the core score.
All four have finite worked solutions. The challenge is to earn those solutions.

### 21. Find every minimum separator set

Generalize the observation exercise to carrier a,b,c,d. Each row is a binary
observation; a selected set of rows separates the carrier if every pair of
marks has different selected-column signatures.

| Observation | a | b | c | d |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 1 |
| 1 | 0 | 1 | 0 | 1 |
| 2 | 0 | 1 | 1 | 0 |

Enumerate all subsets of these three rows. Find the minimum size and retain
**every tied minimum**. Prove that k binary observations distinguish at most
2^k profiles. Can a fifth mark e receive a distinct profile using only two
binary observations? Declare what must change to continue. This is a new
finite classroom predicate; the shipped a,b checker does not implement it.

### 22. Certify an exact optimum rather than just a good proposal

Declare the oriented graph-only cycle a to b, b to c, c to a. No face is
admitted. Reports c_e and positive weights w_e are rational. A vertex potential
f has edge difference (df)_uv=f(v)-f(u), residual r_e=c_e-(df)_e, and cost
C(f)=sum_e w_e |r_e|.

For reports (1,1,1) and weights (1,1,1), find f with cost 3 and a matching
circulation lower bound. Then solve reports (1/2,-1/3,5/6) with weights (2,3,1).

A dual witness lambda must have zero divergence at each vertex and
|lambda_e| <= w_e. Prove C(f) >= lambda dot c. For an arbitrary single oriented
cycle, prove the optimum is min_e(w_e) |sum_e c_e| and construct a matching
potential and dual witness. Include the zero-sum and negative-sum cases.
Explain why this proves neither an optimum on every graph nor a physical theory.

### 23. Supply the cells you claim to see

Use the ordered combinatorial simplex convention: vertices are distinct;
the boundary of [v0,...,vn] is the alternating sum of its vertex-deletion
faces. An n-horn retains all codimension-one faces except the one opposite a
specified vertex, together with their lower faces, inside a declared target
n-simplex. This definition supplies additional mathematics beyond the paper.

Explain how edges ab and bc depict the inner 2-horn of target [a,b,c], and
what is needed to fill it. List the three triangular faces of the 3-horn
Lambda^3_1 in target [a,b,c,d], and the omitted face. Why is a three-edge path
insufficient? For the target tetrahedron, calculate its oriented boundary and
verify boundary-of-boundary equals zero by cancellation. Finally explain why
the K4 edge skeleton's cycle rank 3 supplies neither its faces nor a nonzero
report defect. Give a zero-defect report assignment.

### 24. The tribunal of a substituted packet

Build a small consumer for the existing directed-relation teaching task. It
must accept a scoped checked value only when the retained problem matches the
caller's independently kept problem identity and replay succeeds. Treat a
malformed envelope as failure. State the checker and scope it trusts.

Supply controls for a valid return, a status-only forgery, a complete checked
substitution for another problem, and a genuine refusal. Enumerate all four
endpoint triples over a,b using the declared label; report each reason. Show
that the enumeration is complete for this finite candidate class. Demonstrate
the zero-fuel and two-fuel lazy-proposer cases from Question 15. Identify
separately what you have checked, what you have trusted, and what still requires
producer authentication or external authority.

**Exit condition:** Return your calculations, retained failures, repairs, and
scope statements. Passing this examination demonstrates performance on these
exercises. It does not measure general learning transfer or grant operational
authority. Woland will accept an honest unresolved answer before a fabricated proof.
