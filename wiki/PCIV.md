# Prompt Civilization (PCIV)

[`pciv/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv)
owns **prompt evolution and lineage**. Prompts are treated as genomes that can
be mutated and selected, but every change keeps a full record of where it came
from and why.

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

## Main use cases

| Module | What it does |
| --- | --- |
| `forge.py` | Prompt mutation and population policy |
| `genealogy.py` | Lineage graph of prompt genomes |
| `fitness.py` | Fitness, Pareto selection and obligation checks |
| `lamarckian_loop.py` | Feeds failure receipts back into offspring |
| `immunity.py` | Propagates immunity and taint along lineages |
| `custody.py`, `operator_custody.py` | Append-only prompt custody, external review and independent operator admission |
| `research_selection.py` | Exact paired selection of experimental incumbents, with no deployment authority |
| `ablation.py` | Report-only barrier ablations |
| `intelligence_metabolism/` | Segments obstruction episodes and mines recurring motifs into a daily digest |

The domain also includes an **elenchus** module (Socratic questioning that
extracts contradictions and resists flattery) and sealed **causal witnesses**: a
plain dictionary from a caller is not accepted as a witness.

## Further reading

The [curriculum and levels](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv/documentation)
and [education/010](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/education/010_oepciv)
teach the material in stages.

Related papers: [024](Paper-024.md), [029](Paper-029.md).
