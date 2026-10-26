---
documentation_contract: symbol-game-documentation/v1
title: "Paper 000: Worked Landau examination key"
kind: educational-companion
status: proposed
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
---

# Worked Landau examination key

**Paper 000, version 0.1.0. AuthorityEffect: None.** Attempt the [quiz](quiz.md)
before reading this key. Accept other correct constructions with the same
declared scope. Grade the result, justification, and limits separately; an
honest correction should retain the original failed prediction.

## First room

**1.** Presentation count 1; carrier count 0; printed-character count 2.
The requested answer is `{"presentation_count": 1, "carrier_count": 0}`.
The two printed delimiters do not admit two marks. No relation or physical
vacuum follows from the token's spelling.

**2.** S(2) is a Genesis derivation stage, MSS-2 an atlas specification, and the
second refusal a session event. Their numerals have different indexing roles.
A teaching receipt licenses neither a Genesis successor nor an MSS lift.

**3.** Supply alone does not admit c. The carrier stays a,b until admission is
declared or checked under the relevant regime. S(4) closes the declared finite
separation task, not every possible task. Earlier checks and refusals remain
in the history. S(5) introduces an external continuation demand rather than
automatic progress. These are the paper's orienting descriptions, not a new
derivation of the native stages.

**4.** A basic candidate packet is:

```json
{
  "schema": "symbol-game-basic-packet/v1",
  "carrier": ["a", "b"],
  "relation_label": "separates",
  "goal": ["a", "b"],
  "candidate": ["a", "separates", "b"]
}
```

Share the finite checker and its schema interpretation. The basic checker
enforces membership, a non-self relation, the label, and the exact directed
goal. Budget and exhaustion behavior belong to the session; they are not
extra keys in this strict basic schema. A two-attempt session without a
passing answer stops UNKNOWN.

**5.** The actual basic checker returns:

| Candidate | Status | Reason or property |
| --- | --- | --- |
| a separates b | CHECKED | declared-directed-separation |
| a separates a | REFUSED | SELF_RELATION |
| a separates c | REFUSED | OUTSIDE_CARRIER |
| b separates a | REFUSED | GOAL_UNMET |
| a joins b | REFUSED | RELATION_LABEL |
| Two-element candidate | REFUSED | SCHEMA |

The reversed triple is irreflexive. A first-failure checker need not report
every violated rule: for example, a wrong label on a self-pair still produces
SELF_RELATION because that check occurs first. A passing receipt certifies
only this teaching predicate.

## Second room

**6.** BLOCKED / NO_DECLARED_SEPARATOR. The supplied table contains no row
with unequal observations for a,b. That is not a proof about every observation
that could be supplied. Changing a name alone changes no observation value.

**7.** On the expanded table: index 0 gives REFUSED / NOT_A_SEPARATOR; index 1
gives CHECKED / DECLARED_OBSERVATION_SEPARATES, checked value 1; True gives
REFUSED / ANSWER_TYPE. The checker uses `type(value) is int`, so Python's
Boolean subclassing does not admit True as index 1. The expanded problem has
a different identity; reusing the old candidate produces PROBLEM_BINDING.
Supplying a row does not itself license a native Genesis transition.

**8.** Under the explicit convention, `<ba>` reverses the directed pair,
`<aa>` depicts a self-pair, and `<<ab><>>` attaches an obstruction marker to
the declared pair. Removing the convention removes those semantic readings.
Examples of balanced displays are `<edge<a><b>>` and `<refuse<selfloop>>`.
Their balancing supplies neither a universal parser nor execution or evidence
of the claimed predicate.

**9.** The three reasons are ANSWER_TYPE, SCHEMA, and GOAL_UNMET, respectively.
In the second case the candidate declares the expected answer type, but the
string value fails the basic checker's triple-shape guard. In the third case
the triple has an admissible shape and label but fails direction. Do not
confuse an answer-type label with validation of its value.

**10.** With a newly constructed binding, the self-pair is REFUSED /
SELF_RELATION. The English text is never executed. An original candidate has
the old problem identity, so it gives PROBLEM_BINDING first. This demonstrates
the behavior of this deterministic teaching checker. It makes no general
prompt-injection or tool-authorization guarantee for a future model adapter.

## Third room

**11.** Carrier u,v; goal u to v; candidate u separates v. Direction, membership,
and the declared predicate are preserved under the bijection. The literal
packet content changes, so its digest changes. Renaming only the candidate
while leaving the original board gives OUTSIDE_CARRIER. Mapping both marks to
u loses injectivity and is refused by the renaming helper. Structural
correspondence is different from exact-content identity.

**12.** Dictionary-key reordering does not change the identity under the declared
sorted-key profile. Reversing the carrier list or editing the text does change
it. The digest helps compare exact packet content against a retained expected
identity, assuming the intended hash-comparison use. It authenticates no
producer and proves no natural-language semantics. The profile is not claimed
to conform to RFC 8785.

**13.** Status-only tampering does not replay. A wholly substituted but internally
consistent checked return can replay. Before accepting it, compare:

```python
identity(returned["problem"]) == independently_retained_expected_id
```

Use that comparison together with replay and the required status and scope.
The expected ID must not come from the untrusted return itself. This binds the
consumer to its intended exact question; producer authentication remains a
separate requirement.

**14.** The usable checked values are the exact count dictionary, a separating
observation index, and a relation triple. REFUSED directs inspection and
repair; BLOCKED calls for an additional supplied requirement; UNKNOWN records
an unresolved stop. A valid relation triple says nothing by itself about the
correctness of a scientific model or a medical treatment. Returned data are
the payload; evidence value is what the check establishes; practical value
depends on whether that predicate matters to the task.

**15.**

| Fuel | Status | Attempts | Retained receipt statuses | Values requested |
| --- | --- | --- | --- | --- |
| 0 | UNKNOWN | 0 | none | none |
| 1 | UNKNOWN | 1 | REFUSED | first |
| 2 | CHECKED | 2 | REFUSED, CHECKED | first and second |

No third value is requested after success or exhaustion. A proposer ending
immediately at fuel 2 gives UNKNOWN with zero attempts; it has not consumed
two attempts. The controller does not expose a separate stop reason. Neither
event proves impossibility. The fuel bound controls candidate attempts, not
all resource costs of constructing the proposer or checking its inputs.

## Fourth room

**16.** Extracting the Old payload gives a from d(u(a)) and b from d(u(b)).
On z, d gives the distinct NON_DESCENT constructor, to which u does not apply.
Thus u after d is not a total identity on B. This is an old-image round-trip
fixture. A real extension still needs its source and target regimes, maps,
preservation properties, relevant obstruction evidence, and a licensing record.
It is not a conservativity theorem or an assertion of two involutions.

**17.** Replacing the self-pair by the goal triple repairs the answer under the
same prompt. Admitting c, reversing the goal, or adding an observation row
changes the problem and requires a new binding. Earlier returns describe their
original inputs; retaining them prevents a changed question from being passed
off as a solved original question.

**18.** b separates a is irreflexive and misses the goal. A strategy proposing
a separates a twice fails at fuel 2, even though a passing answer exists.
The first counterexample refutes irreflexivity implying the directed goal;
the second refutes the claimed success of every strategy within two attempts.
Neither refutes scoped checking or establishes universal failure.

**19.** On the shipped collapsed problem, a candidate whose value is True gives
BLOCKED / NO_DECLARED_SEPARATOR. The branch finds no separator before it tests
`type(value) is int`. This disagrees with a uniform validate-value-types-first
reading of the teaching contract. Move that exact integer guard before
computing/returning the no-separator outcome. A useful regression supplies True
to the collapsed table and requires REFUSED / ANSWER_TYPE, while integer 0
still gives BLOCKED / NO_DECLARED_SEPARATOR. The repair notes include this
patch and controls for other malformed values. The result is not a general
security audit of the checker.

**20.** Many tasks qualify. One finite example: input list `[2,4,6]`, answer
type exact integer, goal sum of the admitted inputs, budget two, scope
integer-list-sum-only. A complete checker rejects non-integer input members,
rejects non-integer answers including Booleans, and compares the answer with
the computed sum. Candidate 12 passes; 10 is well-shaped and fails; `"12"`
is malformed. A second person can recompute the sum from the retained list.
The receipt certifies this sum, not the correctness of a model that chose
these inputs. Give full credit to other fully declared replayable examples.

## Final challenges

**21. Every tied minimum.** With no rows all signatures coincide. Each single
binary row distinguishes at most two profiles and fails to separate four marks.
Each two-row subset succeeds:

| Rows | a | b | c | d |
| --- | --- | --- | --- | --- |
| {0,1} | 00 | 01 | 10 | 11 |
| {0,2} | 00 | 01 | 11 | 10 |
| {1,2} | 00 | 11 | 01 | 10 |

The three-row subset also succeeds but is not minimum. Of the eight subsets,
the empty set and three singletons fail; three pairs and the full set pass.
Minimum size is two, with all three pairs retained as ties.

A binary signature of length k has two choices per coordinate, hence 2^k
possible signatures. By the pigeonhole principle, more marks cannot all have
distinct signatures. A fifth mark cannot have a new two-bit profile. Additional
observations or a declared change of the observation-value alphabet would be
needed. This does not decide what native Genesis must do next.

**22. Exact primal and dual witnesses.** For the unit example, take
f(a)=0, f(b)=-2, f(c)=-1. In edge order ab,bc,ca:

\[
df=(-2,1,1),\qquad r=(3,0,0),\qquad C(f)=3.
\]

The circulation lambda=(1,1,1) has zero divergence and meets the unit capacities.
Its dot product with reports is 3, proving a matching lower bound.

For reports (1/2,-1/3,5/6), weights (2,3,1), choose
f(a)=0, f(b)=1/2, f(c)=1/6. Then

\[
df=(1/2,-1/3,-1/6),\quad r=(0,0,1),\quad C(f)=1.
\]

The same lambda=(1,1,1) is feasible for capacities (2,3,1), and
lambda dot c=1/2-1/3+5/6=1. This proves the exact minimum 1.

For any feasible circulation, zero divergence gives lambda dot df=0 by
collecting the coefficient of each vertex potential. Then

\[
\lambda\cdot c=\sum_e\lambda_e r_e
\leq\sum_e|\lambda_e||r_e|
\leq\sum_e w_e|r_e|=C(f).
\]

For a single oriented cycle let H=sum_e c_e and m=min_e w_e. Differences
telescope, so sum_e r_e=H. Therefore every potential obeys

\[
C(f)\geq m\sum_e|r_e|\geq m|H|.
\]

Choose a least-weight edge e*. Put residual H on e* and zero residual on the
other edges. The desired differences c-r sum to zero, so assigning one vertex
potential 0 and integrating these rational differences around the cycle gives
a consistent rational potential. Its cost is m|H|. A constant circulation
lambda_e=m sign(H) gives the same dual value and satisfies every capacity.
For H=0, take lambda=0 and integrate c directly; cost is zero. For H<0 the
constant circulation is -m and its dot product with c is m|H|. No sign case
needs floating-point arithmetic.

This proves the stated single-cycle problem. It does not give an algorithm or
classification for every graph, and its graph has no admitted filled face.

**23. Declared cells and boundaries.** In target [a,b,c], the omitted face
opposite vertex 1 is ac. Edges ab and bc are the other faces of the inner
2-horn. A filling supplies the missing edge ac and the 2-simplex, consistently
with the declared lower faces and ambient structure; a composability claim
alone should not be mistaken for an already admitted cell.

For target [a,b,c,d], Lambda^3_1 retains bcd, abd, abc and their lower faces;
the omitted face is acd. A three-edge path contains no triangular faces and
cannot supply this horn. The oriented tetrahedron boundary is

\[
\partial[a,b,c,d]=[b,c,d]-[a,c,d]+[a,b,d]-[a,b,c].
\]

Applying the triangular boundary rule gives

\[
([c,d]-[b,d]+[b,c])-([c,d]-[a,d]+[a,c])
+([b,d]-[a,d]+[a,b])-([b,c]-[a,c]+[a,b])=0.
\]

Every edge cancels. For a triangle the further boundary cancels vertices by
the same rule. The connected K4 graph has m-n+1=6-4+1=3 independent graph
cycles, but no faces or solid cell are supplied by this count. Set every report
and every potential to zero to obtain zero defect on every edge. The boundary
identity is a mathematical fact under the declared chain convention, not a
physical emergence result or a licensed Genesis transition.

**24. A scoped consumer.** One acceptable implementation is:

```python
from lesson_packets import identity, replay_return

def consume(result, expected_problem_id):
    try:
        if not replay_return(result):
            return None
        if identity(result["problem"]) != expected_problem_id:
            return None
        receipt = result["receipt"]
        if (receipt["status"] != "CHECKED"
                or receipt["scope"] != "finite-teaching-contract-only"
                or result["problem"]["prompt"]["task_type"] != "directed_relation"):
            return None
        return receipt["checked_value"]
    except (KeyError, TypeError, ValueError):
        return None
```

Compute `expected_problem_id=identity(problem)` from the caller's own intended
problem before receiving the return. Accept the valid goal triple; reject a
status-only forgery, a checked return for a changed question, and a genuine
refusal. Rejection here is a consumer decision, not a new native receipt schema.

For candidate endpoints from a,b and the fixed label, the complete Cartesian
product has 2 times 2 = 4 triples. Their reasons are:

| Candidate | Lesson outcome |
| --- | --- |
| a separates a | REFUSED / SELF_RELATION |
| a separates b | CHECKED / DECLARED_GOAL_MET |
| b separates a | REFUSED / GOAL_UNMET |
| b separates b | REFUSED / SELF_RELATION |

This exhausts exactly the fixed-label endpoint class, not arbitrary schemas,
carriers, prompts, or strategies. The lazy-proposer results are those in
Question 15. The consumer checks internal consistency, the intended problem
binding, the selected task, and receipt scope. It trusts the local checker and
its own expected identity. It does not authenticate a remote producer or
authorize an external action. The review bundle's verification script runs
these controls against the supplied teaching checker.

## Use the score to decide what to revisit

Record the four room subtotals out of 25 and capstones separately. Revisit the
specific failed concept before using the overall core score as encouragement
to proceed. A high score is performance on this examination; no validated
learning-transfer metric or Landau historical grading standard is claimed.
