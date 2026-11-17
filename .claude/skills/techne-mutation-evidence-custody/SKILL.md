---
name: techne-mutation-evidence-custody
description: "Define what a mutation claim must ship to count. Target, change, failing tests, byte-identical restore."
operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "unknown"
families: [governance, quality, evidence, testing]
---

# Mutation Evidence Custody

**Status:** `CANDIDATE`
**AuthorityEffect:** `None` (defines a receipt; certifies nothing)

## The finding this exists for

Sprints report mutation kills as their central quality evidence -- `15/15`,
`16/16`, `17/17`. A repository-wide search for any durable record of those runs
returns **nothing**: no mutation log, no JSON, no receipt, no harness, no
`mutmut` or `cosmic-ray` config. No sprint has an `evidence/` directory, though
`techne-sprint-execution` states *"No path = No credit; do not mark DONE without
it."*

Every count is a scalar in a markdown file, written by the same pipeline that
ran the mutation, with no target list, no per-mutation failure set and no
residue proof. One sprint's retrospective describes *editing* the harness -- so
it existed on disk and was never committed.

The estate's own law already forbids this, in a file those sprints authored and
mirrored to four hosts:

> *"Mutation results quoted as evidence must be replayable. A count of killed
> mutants in prose, produced by a script that no longer exists, is the same
> declared-but-unenforced shape this law exists to prevent."*
> -- `_shared/test_quality_law.md:180-182`

A skills register now aggregates those scalars into *"53 mutations killed across
the branch"* -- an aggregate over unverifiable inputs, itself cited as evidence.

## What a mutation claim must carry

A mutation is replayable when a third party can re-apply it from the record
alone. Five fields, and a claim missing any of them is a candidate, not
evidence:

| Field | Why it is load-bearing |
| --- | --- |
| **target** | the file, so the reader knows what was weakened |
| **anchor** | the exact text replaced, quoted. An anchor that matches zero or many times is a **setup failure, never a result** |
| **applied** | the replacement, so the mutation can be reconstructed byte for byte |
| **failures** | *which* tests failed, by name -- not how many. A count cannot show whether the witness was the one the criterion names |
| **restore** | proof the tree returned to its prior state, by empty `git diff` or digest |

## The rule

> **A mutation count is a claim about work nobody can repeat. A mutation table is
> evidence. Quote the table or quote nothing.**

Three consequences worth stating, because each has already happened here:

1. **`N of N killed` says nothing about which N.** One sprint's two mutations
   both missed the two tests that could not fail; it reported `2 of 2` truthfully
   and proved nothing about the gates whose names promised the coverage.
2. **A surviving mutant is often the more informative result.** Recording only
   kills discards the diagnosis. One sprint's first run killed 6 of 15 and said
   so in four documents -- the most useful mutation record in the estate, and
   still unreplayable.
3. **An equivalent mutant must be recorded as equivalent, not chased.** A
   mutation that changes no observable behaviour is a fact about the code, and
   burying it inflates the denominator.

## Applying it

Record the table in the artefact that outlives the session -- the commit message
is durable, in git, and reviewable; a scalar in a retrospective is not. A worked
example, from the commit that repaired this estate's stale census literals:

```text
M1  planar_substitution.py, `directory.glob("*/SKILL.md")` -> `[:-1]`
    5 tests failed, including both repaired assertions:
      garden size    assert 111 == 112
      pair           (112, 3607) -> (111, 3558)   both moved, as designed
    restored byte-identical, verified by empty `git diff`

M2  coda-research-atlas-reconcile/SKILL.md, `operad_target_colour: "State"` -> `"Paper"`
    1 test failed, and only the pair test:
      pair           (112, 3607) -> (112, 3566)   second only, as designed
    restored byte-identical, verified by empty `git diff`
```

M2 is the one that matters: it is the case the assertion exists for. A table
that only records the mutations that were easy to kill is a table about the
author's confidence.

## The harness, and what running it taught

A harness now exists:
`operations/use_cases/verification/mutation_harness.py`, driving
pytest or cargo from a declarative catalogue and emitting the table above.
Building it surfaced four rules that custody alone does not imply, each found by
the harness getting them wrong first:

1. **A harness must not be a witness in its own experiment.** The catalogue's
   anchor test asserts each mutant's anchor matches -- and while that mutant is
   *applied* its anchor is gone by construction, so it failed on every run and
   "killed" every mutant. A real survivor would have been reported dead by the
   harness's own accounting. Exclusions belong in the catalogue as data.
2. **Fail closed.** It lied in the same direction twice for unrelated reasons:
   `^FAILED` never matched a line beginning `\x1b[31m`, and one batch produced a
   false survivor no re-run could reproduce. Both report *no evidence of a kill*
   as *evidence of no kill*. Anything the runner cannot establish -- unparsed
   output, an unconfirmed precondition, a build that did not compile -- is a
   **setup failure excluded from the denominator**, never a survivor. Read the
   mutation back off disk before trusting the run that follows it.
3. **`finally` does not survive a kill.** Three interrupted runs each left a
   mutation applied, the tree silently carrying code nobody wrote. Write a
   journal naming the file and its pre-edit digest *before* touching it, delete
   it only after a verified restore, and refuse to start while one exists. Add a
   pre-flight clean check: restoring onto a dirty tree proves only that the tool
   put back what it found.
4. **Establish whether a survivor CAN be killed before chasing it.** One was
   equivalent -- the check it removed is subsumed by the next one -- and a test
   written to kill it would have asserted an implementation detail while the
   table read `23/23`. Prove equivalence by exhaustive search over small cases,
   not by the informal argument, and pin the proof as a test so that weakening
   the subsuming check makes the mutant killable again and says so.

And one that is custody, restated because it was violated in the artifact meant
to enforce it: **every artifact describing one run is emitted by that run.** A
readable table assembled by hand beside a generated record drifts silently,
because nothing compares them. Ours said "18 of 18" next to a record of 23
mutants and a survivor.

## Scope, and what this does not claim

This skill defines custody. The harness above is one implementation of it, not
the definition, and it does not retroactively verify any past sprint -- roughly 200 claimed kills across 39
sprints remain **unverified**, and the honest disposition is to restate them as
such rather than to reconstruct evidence after the fact. Reconstructing a
mutation run from a prose description would produce exactly the artefact this
skill exists to distrust.

Whether to build a harness, and whether past claims should be restated, are
human decisions. Under the LLM Boundary Law an agent may generate the candidate
and may not certify it.

## Provenance

Built from the sprint 001-039 Blackrod enforcement audit, which verified the
absence of any mutation artefact across the whole repository.

`AuthorityEffect: None`.
