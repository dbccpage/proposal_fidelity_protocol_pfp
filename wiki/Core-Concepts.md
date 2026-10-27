# Core concepts

A short glossary. The papers are authoritative where they differ from this page.

## The protocol

**Proposal (candidate).** Anything submitted for checking: a value, a claim, a
prompt, a code patch. A proposal carries no authority by being submitted, and
none by coming from a capable source.

**Declared property.** The specific thing a check tests. A check is only
evidence for the property it declares, not for anything broader.

**Check (verifier).** A component, independent of the proposer, that tests a
declared property and records the result. The proposer never evaluates or
promotes its own proposal.

**Allowed use.** The decision about what a checked proposal may be used for.
Passing a check does not by itself license any wider use.

**Refusal.** A proposal that fails is refused, not silently dropped. Refused
proposals are retained as evidence (Paper 006 covers this).

**Authority effect.** Many documents in this repository open with
`AuthorityEffect: None.` This states that the document or tool grants no
authority on its own: it can describe, compute or check, but it cannot approve.

## The mathematics

**S(n) and MSS-N.** The finite symbol systems the introductory material is built
on. MSS-N is the minimal symbol system at level N. Paper 000 introduces both;
Paper 008 verifies the maps from MSS-0 to MSS-1.

**Packet.** A typed, content-addressed record that carries a problem, a proposed
value, its reason and scope, and any checked value. A returned packet keeps the
original problem alongside the answer so it can be replayed.

**Obstruction.** A measure of how far a set of claims is from being globally
consistent. On a graph, claims around a loop that do not sum to zero leave a
nonzero obstruction. An obstruction of zero means a consistent assignment exists.

**Retraction.** Moving a state back toward an admissible, consistent one. A
retraction step is admitted only if it does not increase the obstruction
(strict descent).

**Repair versus replacement.** Paper 005 separates a potential adjustment, which
keeps the original cycle sums, from replacing the edge claims themselves.

**Receipt.** A replayable record of each step, admitted or refused, with digests
so the record can be checked for tampering.

## Supporting systems

**Epistemic Immune System (EIS).** Screens proposals for known failure patterns
("antibodies"), such as unsupported claims or silently skipped checks, and keeps
rejected proposals so they can be mined later.

**Prompt Civilization (PCIV).** Evolves prompts with explicit lineage: every
changed prompt keeps its parent hashes and the failure evidence that motivated
the change. Fitness scores license inspection only, never promotion.

**Operads.** Typed composition of capabilities and workflows. A compatible type
graph shows that pieces fit together; it is not evidence that the composed
workflow runs correctly.

Each has its own section: [EIS](EIS.md), [PCIV](PCIV.md) and [Operads](Operads.md).
[Rewriting and packetization](Operads-Rewriting-and-Packetization.md) shows how
operads, rewriting and packets fit together.
