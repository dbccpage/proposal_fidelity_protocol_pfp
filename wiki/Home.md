# Proposal Fidelity Protocol (PFP)

The Proposal Fidelity Protocol keeps three things apart that are easy to blur
together when a model, a person or a program suggests something:

1. **the proposal** itself, which is only a candidate;
2. **the check** of a declared property of that candidate, done by something
   other than the proposer; and
3. **the decision** about what the checked candidate may be used for.

A proposal that passes a check gains no authority beyond what the check covered.
A proposal that fails is refused, and the refusal is kept as evidence. PFP was
historically called **The Symbol Game**, and you will still see that name in
older papers and code.

## Where to start

| If you want to... | Go to |
| --- | --- |
| Put PFP into a workflow | [Choose WF1–WF5](workflows.md) · [Start in a few steps](workflow_start_here.md) |
| Understand the idea in plain language | [Getting started](getting_started.md) |
| Learn the vocabulary (packets, obstruction, retraction, receipts) | [Core concepts](core_concepts.md) |
| Read the research papers in order | [Papers](papers.md), with a page per paper |
| Understand the code | [pfp package](pfp_package.md), [Operads](operads.md), [Epistemic Immune System](eis.md), [Prompt Civilization](pciv.md) |
| See how proposals are rewritten, layer by layer | [Rewriting](rewriting.md): Pre-Genesis, Genesis, S(n), MSS-N, PFP and WDP |
| Try ideas in a small interactive tool | [PFP Lab](pfp_lab.md) |
| See how language models were steered, and replicate it here | [Steering examples](steering.md) |
| Find your way around the code | [Repository layout](repository_layout.md) |
| See the known gaps in PFP, PCIV, EIS and operads | [Gap report](gap_report.md) |
| Contribute, or check licensing | [Contributing](contributing.md) |

## Status

PFP is research software and work in progress. The papers mark which results
are proved, which are finite checks, and which are open. Finite test success is
not a claim about model performance, and no external peer review is claimed
unless a paper says so.

This wiki is maintained in the repository's
[`wiki/` folder](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/wiki)
and published from there, so changes go through pull requests.
