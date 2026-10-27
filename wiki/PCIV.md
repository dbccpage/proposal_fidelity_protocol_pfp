# Prompt Civilization (PCIV)

[`pciv/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv)
owns **prompt evolution and lineage**. Prompts are treated as genomes that can
be mutated and selected, but every change keeps a full record of where it came
from and why, and no score ever becomes permission.

## The idea in one picture

```text
 parent genome ──mutate (protected spans fixed, birth custody Wild)──▶ child genome
      ▲                                                                   │
      │ inherited lessons, attenuated by distance                         │ run many times
      │                                                                   ▼
 failure witness ◀── host check ◀── execution occurrence (packets in, packets out)
                                                                          │
                                                                          ▼
                             exact Pareto fitness ──▶ inspection budget only
```

## Pages in this section

| Page | Read it to... |
| --- | --- |
| [Genomes and lineage](PCIV-Genomes-and-Lineage.md) | Tell a prompt genome from its execution occurrences, and see which edges may join two prompts (Levels 00–01) |
| [Mutation and inheritance](PCIV-Mutation-and-Inheritance.md) | See how the forge edits prompts, and how lessons from failures are inherited with attenuation (Levels 02–03) |
| [Selection and retrieval](PCIV-Selection-and-Retrieval.md) | Follow exact Pareto selection, inverse lineage PageRank, precedent matching and population reserves (Levels 04–07) |
| [Safety and persistence](PCIV-Safety-and-Persistence.md) | See how taint and invalidation work, how events are logged durably, and how experimental incumbents are chosen (Levels 08–10) |

## Invariants

1. **Explicit ancestry.** Every changed prompt keeps its parent hashes, the
   mutation applied and the delta. Nothing is edited in place without a record.
2. **Learning from typed failures.** Lessons taken from counterexamples and
   obstruction receipts are written into child prompts. This is the
   "Lamarckian" part: acquired fixes are inherited.
3. **Separated populations.** Task prompts, mutation prompts, evaluation prompts
   and the orchestrator live in separate populations. A prompt never evaluates
   or promotes itself.
4. **Canaries and held-out panels.** Each generation is tested on held-out
   panels and canary prompts that detect drift, flattery and unsupported
   claims.
5. **No automatic authority.** A fitness score licenses inspection only. It is
   not a proof, a promotion or a model verification.
6. **Exact arithmetic.** Fitness, weights and ranks are exact rationals; floats
   are barred.

## Main modules

| Module | What it does |
| --- | --- |
| `use_cases/forge.py` | Prompt mutation and population policy |
| `use_cases/genealogy.py` | Lineage graph of prompt genomes |
| `use_cases/fitness.py` | Fitness, Pareto selection and obligation checks |
| `use_cases/lamarckian_loop.py` | Feeds failure receipts back into offspring |
| `use_cases/immunity.py` | Propagates immunity and taint along lineages |
| `use_cases/rank.py` | Adapter for native inverse lineage rank and its certificates |
| `infrastructure/matching.py` | Precedent matching and usage evaporation |
| `infrastructure/event_log.py`, `cas.py` | Durable event log and content-addressed storage |
| `use_cases/custody.py`, `operator_custody.py` | Append-only prompt custody, external review and independent operator admission |
| `use_cases/research_selection.py` | Exact paired selection of experimental incumbents, with no deployment authority |
| `use_cases/ablation.py` | Report-only barrier ablations |
| `domain/elenchus.py` | Socratic questioning that refuses flattery and urgency used to waive checks |
| `domain/causal_witness.py` | Sealed causal witnesses: a plain dictionary from a caller is not a witness |
| `intelligence_metabolism/` | Segments obstruction episodes and mines recurring motifs into a daily digest |

The executable core of several of these is native code; the Python modules are
adapters and reference implementations.

## How PCIV connects to the rest

- **Packetization.** A model turn is a set of packets, and a genome is bound to
  its source packets. See [Rewriting and packetization](Operads-Rewriting-and-Packetization.md).
- **EIS.** Antibodies are what a lineage inherits; the thymus screens what a
  failure produces. See [Epistemic Immune System](EIS.md).
- **Bounded repair.** The repair workflow submits its observations to the
  genealogy service. See [Bounded repair](Operads-Bounded-Repair.md).

## Further reading

The [levels](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv/documentation/levels)
(00 to 10) and the [curriculum](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv/documentation/curriculum)
(tracks 400, 410 and 420, with notebooks) teach the material in stages, as does
[education/010](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/education/010_oepciv).
The level documents are specifications marked as drafts; read each claim at its
stated evidence grade.

Related papers: [024](Paper-024.md) (recursive re-entry with evidence scope)
and [029](Paper-029.md) (evidence-bound harness evolution).
