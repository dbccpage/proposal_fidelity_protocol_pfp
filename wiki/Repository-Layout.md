# Repository layout

| Folder | What is in it |
| --- | --- |
| [`papers/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers) | The paper collection; see [Papers](Papers.md) |
| [`education/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/education) | Teaching material: `004` PFP and the Symbol Game, `008` operads, `009` epistemic immune system, `010` prompt civilization |
| [`pfp/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp) ([page](PFP-Package.md)) | The core Python package: packets, evaluators, retraction, receipts, replay. `CONTEXT.md` is its engineering glossary |
| [`eis/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/eis) ([page](EIS.md)) | Epistemic Immune System: antibodies, screening and custody of rejected proposals |
| [`pciv/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pciv) ([page](PCIV.md)) | Prompt Civilization: prompt lineage and evolution with recorded ancestry |
| [`operads/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/operads) ([page](Operads.md)) | Typed composition of capabilities, workflows and skills |
| [`pfp_lab/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_lab) | [PFP Lab](PFP-Lab.md) and its scenario packs |
| [`ops/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/ops) | Operations, governance and supporting infrastructure |
| [`demos/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos) ([page](Demos-Pilots-And-Tests.md)) | Offline demos and the fifty certified challenges; no model calls |
| [`pilots/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pilots) ([page](Demos-Pilots-And-Tests.md)) | Experiments that ran language models; they need the private runtime |
| `wiki/` | The source for this wiki |

## Code layout

The Python packages follow a layered layout: `domain/` for pure rules and value
types, `use_cases/` for application logic, `infrastructure/` for adapters and
storage, `controllers/` and `entrypoints/` for the outside world, and `tests/`.

## A note on names

These components were brought over from an earlier repository, and some imports,
paths and document links still use their older names. They are being renamed
gradually; until then, a link inside an imported document may point to a path
that does not exist here.
