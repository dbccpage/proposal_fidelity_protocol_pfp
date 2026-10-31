# Workflow glossary

Use this as a lookup page. You do not need to memorize it before WF1.

| Term | Plain meaning |
| --- | --- |
| Seed | The original task text. |
| P* | A host-prepared prompt combining the task with an explicit policy/response contract. |
| Typed response | An answer required to match declared fields and value types. |
| Envelope | The outer fields binding a reply to its task, attempt and input. |
| Host | The code/operator preparing the task and checking the model's actual reply. |
| Independent checker | A check that does not simply accept the proposer's own verdict. |
| Digest | A hash used to detect changed data relative to a recorded binding. It is not a signature or permission. |
| Receipt | A retained account of inputs, actions and checked outcomes under a stated contract. |
| Replay | Rechecking saved data without buying another response. What is replayed depends on the receipt format. |
| Slot | A named place for a piece of structural information or an explicit unresolved disposition. |
| Operad candidate | A proposed typed operation with ordered input ports, output type and references. Metadata alone does not prove its laws or execution. |
| Arity | Number of typed input ports. One list is one port even when it contains many values. |
| DDC move | A proposed operation from the declared eight-letter transition vocabulary. A written log is not an execution receipt. |
| Pre-mining | Preparing candidate operations/guidance before asking the solver for its answer. |
| Frozen attachment | Guidance whose bytes and lineage are fixed before the next stage. |
| L2 guidance | Concrete task-level bindings: which actual data, arguments and preservation obligations to use. |
| Local green | The named local checks passed. |
| Global red | The independent overall requirement failed despite local results. |
| LGGR | The local/global boundary check; zero defect alone is not a general soundness certificate. |
| Grammar | A declared language of legal representations, with an explicit start production. |
| Decoder | The rule that gives a representation its declared meaning. |
| Preservation | Checks that a rewrite keeps the protected task query, constraints and data. |
| Protected query | The property or task meaning that must survive transformation. |
| Source span | A recorded part of the original text, with offsets and a declared role. |
| Baseline | A retained comparison result, such as the original plain-seed response. |
| Shared allowance | One resource budget covering every miner, rewrite, solver and continuation in its scope. |
| Reference profile | A compact pointer to frozen host-owned metadata. It is not newly authored model evidence. |

[Choose a workflow](Workflows.md) · [Full contracts](Workflow-Contracts.md)
