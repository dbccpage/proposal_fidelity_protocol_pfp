# Prompts as operad trees

Part of [Operads](Operads.md). Previous: [Operad primer](Operads-Primer.md) · Next: [Rewriting and packetization](Operads-Rewriting-and-Packetization.md)

A PFP prompt is not a free-form string. It is assembled as a tree whose leaves
are exact slices of a source document and whose internal nodes are typed
operators. The code is in
[`pfp/domain/operad/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp/domain/operad),
and the mathematics is Theorem 3 of [Paper 027](Paper-027.md).

## Prompt colours

The prompt operad has its own colours (`PromptColour` in `prompt.py`), naming
the semantic role of a piece of text:

```text
RawTextSpan  IsolatedVariable  Equation  SubstitutionStep
RationalValue  InvariantWitness  TargetResult
```

## Leaves are byte-exact spans

A leaf (`LeafTextSpan`) carries an id, a colour, its text, the offsets
`[start, end)` it was cut from, and optionally a document id and SHA-256
digest. `verify_against_document` re-slices the source and refuses if the text
differs. A prompt therefore cannot quietly paraphrase its source: either the
leaf is the declared slice, or the tree is defective.

## Operators and grafting

A `PromptOperator` has ordered source colours, one target colour and an arity
that must equal the number of source colours. `OperadTreeNode.graft(slot, child)`
is partial composition `∘_slot` on trees. It refuses an out-of-range slot or a
child whose output colour differs from the slot's colour.

```text
                SubstitutionStep
               /                \
     Equation(span 12–31)   RationalValue(span 40–43)
```

## The null tree and the congruence ideal

Some defects make a tree useless no matter what surrounds it. Paper 027 collects
them into a set `I` of defective trees:

1. a numeric value that is not exact, or is a boolean dressed up as a number;
2. a leaf whose content or digest does not match its declared slice;
3. a graft whose child colour does not match the slot, or whose slot is out of
   range;
4. a binding neutralised by an active decoy witness.

**Theorem 3** shows that `I` is a two-sided ideal: if a tree contains a defect,
so does every larger tree built from it, on either side of a graft. Collapsing
`I` to one point `0`, called `NullTree`, gives a well-defined quotient operad
in which

```text
f ∘_m 0 = 0        0 ∘_m g = 0
```

A composite is non-null exactly when every leaf is byte-identical to its
slice, every parameter is rational, every graft matches its signature, and no
decoy fires.

In the code, `CongruenceIdeal.evaluate_rational_domain` turns a boolean, a float
or a decimal string into a `NullTree` with a reason, and grafting a `NullTree`
into any node returns a `NullTree`. A `NullTree` is a typed failed term: it
keeps the ideal id and reason so the failure can be read later. It is not a
zero value and it does not mean "no answer"; it means "this answer is refused,
and here is why".

## Three polarities

`PolarizedOperadTriad` in `operad.py` keeps three disjoint families of
operations, plus the host gate:

| Polarity | Symbol | Maps | May not |
| --- | --- | --- | --- |
| Constructive | `O+` | requirements to candidate artifacts | — |
| Interrogative | `O−` | candidates to findings and unmet obligations | emit a patch (`ProhibitedRepairError`) |
| Corrective | `O_repair` | a subject and findings to a candidate patch | judge correctness (`ProhibitedEvaluationError`) |
| Gate | `A_gate` | host-side deterministic check | — |

Only constructive operations compose with `∘_i`. Registering a morphism under
the wrong polarity raises `OperadRoleViolationError`. Separating the roles is
the operad form of the PFP rule that the proposer never checks its own work:
the thing that finds a fault does not write the fix, and the thing that writes
the fix does not decide whether it worked.

## Where checks attach

`PlanarGraft` binds an interrogative check to one of three sites on a tree:

| Site | Looks at | Typical failure |
| --- | --- | --- |
| `VERTEX` | one generator | a locally defective step, before generation |
| `EDGE` | one seam `f ∘_i g` (needs a `seam_index`) | the child's type does not match what the parent expects |
| `TREE` | the whole tree | a circular dependency, or nonzero boundary leakage (`d1 ∘ d0 ≠ 0`) |

Anti-skills from the [EIS](EIS.md) bind at these sites.

## Expanding a prompt into sub-prompts

A root prompt `P` is expanded into a template-instantiated `P*`, which may be
decomposed into sub-prompts. `ExpansionNode` in
[`prompt_containment.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp/domain/rewriting/prompt_containment.py)
records each node with a declared **cardinality** and enforces the containment
law

```text
cardinality(node) = 1 + Σ cardinality(child)
```

and a maximum depth of 5. A tree whose declared count does not add up is
refused, so a decomposition cannot hide or invent sub-prompts. Every node
carries `authority_effect: "None"`.

## Why a two-stage prompt helps

Paper 027 studies a two-stage pipeline `X → Z1 → Y`: stage 1 proposes a small
tuple of invariants, the host checks it, and only then is it grafted into
stage 2. If the stage-1 guard is sound and complete, Theorem 5 shows that:

- conditioning on admission removes every corrupted stage-1 graft, because a
  rejected tuple becomes `NullTree` and `f ∘_i 0 = 0`;
- with retries, the admission probability is `1 − (1 − p1)(1 − p_retry)^(R−1)`;
- every abstention saves the cost of a stage-2 call.

Theorem 6 is the warning: a guard that checks only local slot invariants and
omits the global cycle-sum equation leaves an infinite set of false greens. A
guard is only as good as the equations it actually checks.

These are finite results under stated hypotheses. The historical model trials
in Paper 027 are reported as unverified summaries, not current evidence.
