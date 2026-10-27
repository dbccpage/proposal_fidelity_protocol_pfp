# Mutation and inheritance

Part of [Prompt Civilization](PCIV.md). Previous: [Genomes and lineage](PCIV-Genomes-and-Lineage.md) · Next: [Selection and retrieval](PCIV-Selection-and-Retrieval.md)

This page covers Levels 02 and 03: how prompts are changed, and how what one
prompt learned from a failure reaches its relatives.

## The forge

`use_cases/forge.py` applies mutations. A mutation is a list of byte-span edits
(`offset`, `length`, `replacement`) proposed by a mutation operator.

**Protected spans are untouchable (`F-BIO-03`).** A genome's protected spans
(system framing, types, claim hygiene) are fixed. Any edit whose range overlaps
a protected span, including a zero-width insertion inside one, is refused with
`PROTECTED_SPAN_MUTATION_REFUSED`. Mutation works only on the plastic scaffold.

**Children are born wild (`F-PROMPT-03`).** Every child starts with custody tier
`Wild`. A mutation operator has no field or permission to set `Candidate`,
`Reviewed` or `Admitted`. A mutation cannot admit itself.

**Rule changes wait for the next epoch (`F-META-01`).** A proposal to change how
evidence is counted, which checker runs or what quorum applies is a
meta-operator proposal. It never takes effect in the epoch in which it is made,
it cannot change the checker or test bank evaluating its own lineage, and it
takes effect only when an external decision ratifies it for a later epoch.

The forge's possible actions are deliberately few: continue, propose a mutation,
change a prompt's retrieval eligibility, or propose a review.

## The Lamarckian loop

Biological evolution does not pass on acquired traits. Prompt evolution can,
and PCIV does so on purpose, under strict conditions. `lamarckian_loop.py`
describes the cycle:

```text
(seed prompt, generation g)
   ──▶ adversarial dialectic ──▶ artifact
   ──▶ PFP measurement        ──▶ defect witness
   ──▶ thymus screen          ──▶ antibody
   ──▶ forge                  ──▶ generation g + 1
```

Three rules apply at every turn:

1. **Protected core invariance.** The protected core of generation `g + 1`
   equals that of generation `g`.
2. **Witness grounding.** No antibody is injected without a verified
   falsification witness.
3. **Attenuated influence.** A lesson's weight falls with distance (below).

The low-level mutation helper does not authenticate a witness or admit an
antibody by itself. The composition root must run and bind the checker first.
A well-formed witness digest and a mutation receipt alone establish no failure.

## How far a lesson travels

When a prompt acquires an antibody, its relatives may inherit it, with weight

```text
w(d) = (1/2)^d     for 1 <= d <= 10
w(d) = 0           for d > 10
```

where `d` is the distance in inheritance edges.

| Distance | 1 | 2 | 3 | 5 | 10 | 11 |
| --- | --- | --- | --- | --- | --- | --- |
| Weight | 1/2 | 1/4 | 1/8 | 1/32 | 1/1024 | 0 |

**Distance is the shortest path** in the inheritance graph (`F-IMMUNE-10`), not
the difference in generation numbers, which would overstate distance where
branches converge. Where several paths reach the same ancestor, the
highest-weight path governs.

**No relaying (`F-IMMUNE-09`).** Inheriting an antibody is not acquiring it.
The acquisition id, the origin prompt and the generation of acquisition are
preserved on every propagation record, so a prompt that received an antibody
cannot re-emit it as a fresh origin to get around the 10-hop ceiling.

**Scope is kept (`F-SCOPE-01`).** Inherited immunity arms detectors only inside
the target prompt's declared scope. Carrying it across a domain, carrier or
grammar boundary without an explicit transport and loss record is refused with
`REFUSE_SCOPE_ESCALATION`.

**The armed repertoire is derived (`F-IMMUNE-11`).** What a prompt is guarded by
is computed from the current ledger. If an antibody is suspended or revoked,
every cached repertoire is invalidated at once, with no graph walk. This is the
same "global invalidation" described in [Safety and persistence](PCIV-Safety-and-Persistence.md).

## Worked example

A prompt `P` at generation 4 acquires antibody `α` from a verified failure.
`P` has a child `C` (distance 1) and a grandchild `G` (distance 2), and `G` also
descends from `P` through a second, longer path of length 4.

- `C` inherits `α` with weight 1/2.
- `G` inherits `α` with weight 1/4: the shortest path governs, not the longer
  one (1/16).
- If `G` "relays" `α` to its own children, their records still name `P` as the
  origin and generation 4 as the acquisition, so the distance keeps counting
  from `P`.
- If `G` works in a different domain from `P`, `α` does not arm there unless a
  transport record exists.

## Related reading

[Paper 024](Paper-024.md) shows why inheritance needs these bindings: a
rejection rule that is sound for its source task can become unsound after a
task change, so a returned rule is re-used only when its task, evidence,
transport and resource bindings survive.
