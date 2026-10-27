# Genomes and lineage

Part of [Prompt Civilization](PCIV.md). Next: [Mutation and inheritance](PCIV-Mutation-and-Inheritance.md)

This page covers Levels 00 and 01 of the
[PCIV levels](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv/documentation/levels).

## Material versus occurrence

A naive prompt-evolution system treats every model turn as a new prompt string.
Identities multiply and the causal record is lost. PCIV separates two things:

| Thing | What it is | How many |
| --- | --- | --- |
| **Prompt genome** (`PromptGenomeV1`) | The governed material: canonical text, schemas, boundary directives, parent links and birth custody | One per distinct prompt |
| **Execution occurrence** (`ExecutionOccurrenceV1`) | One run of a genome against an input: occurrence id, prompt id, session, input packet, output packet | One per run |

Running an unchanged prompt 1,000 times gives 1,000 occurrences and **one**
genome.

The genome's id is the SHA-256 of a canonical, sorted, float-free JSON encoding
of its source packet references, domain model, parents and birth custody. It
**excludes** timestamps, occurrences and runtime metrics, so a genome's identity
does not drift when it is used.

## The three-packet turn

A model turn is organised as packets, in the sense of
[Rewriting and packetization](Operads-Rewriting-and-Packetization.md):

```text
Stage 0  PacketEnvelope   protected boundary names, session, nonce
Stage 1  Prompt artifact  canonical instructions and scaffolds
Stage 3  Turn output      raw response and execution evidence
```

Stages 0 and 1 feed the genome. Stage 3 feeds an occurrence. Because the
packets are content-addressed, an occurrence points at exact input and output
bytes, and re-executing an unchanged genome produces a new occurrence without
touching the genome.

The forge later splits a genome's text into **protected spans** (system framing,
types, claim hygiene) and a **plastic scaffold** that mutation may change; see
[Mutation and inheritance](PCIV-Mutation-and-Inheritance.md).

## Two kinds of edge

Prompts are joined by two kinds of edge, and they are never confused.

**Inheritance edges** record that one prompt was physically generated from
another. An edge `(parent, child, relationship, receipt)` is admitted only with
a host-sealed witness receipt. The relationship is one of:

| Relationship | Carries |
| --- | --- |
| `DirectMutation` | The mutation operator id |
| `Repair` | The hash of the defect it repairs |
| `Retry` | The bout id |

**Reference edges** record that one prompt used another as a precedent. They
carry a match receipt and a ledger epoch.

| | Inheritance | Reference |
| --- | --- | --- |
| Counts toward generation number | yes | no |
| Carries inherited immunity | yes | no |
| Counts as offspring in lineage rank | yes | no |
| Created by matching topics or objectives | **never** | — |

Matching objectives, topic similarity or shared domain tags **never** create an
inheritance edge (`F-LINEAGE-01`). Lineage is a record of what happened, not of
what looks related.

## The graph stays acyclic

The inheritance graph is a directed acyclic graph. An edge that would close a
cycle is refused with `INHERITANCE_CYCLE_DETECTED` before it is inserted.
Several parents are allowed, for an explicit crossover or a joint repair.

## Witnesses must be sealed

`domain/causal_witness.py` makes the rule concrete. A `SealedCausalWitness`
holds a canonical JSON body and its digest, and construction refuses when:

- the digest is not `sha256:` followed by 64 lowercase hex digits;
- the digest is the placeholder `sha256:causal_witness_ok`;
- the digest does not match the body.

A plain dictionary supplied by a caller is not a witness, and an unverified
receipt is refused by the genealogy service.

## Check your understanding

1. A prompt is run on 50 inputs and then edited once. How many genomes and
   occurrences exist? *Two genomes (the original and the edit, joined by one
   inheritance edge) and 50 occurrences, plus any runs of the edited prompt.*
2. Two prompts address the same task and share half their text. Is there an
   edge between them? *Not unless one was generated from the other with a
   sealed witness. Similarity creates no edge.*
