# Research Translation and Improvement Program

## Method

The sources below were selected for a concrete OEWAS design or falsification
question. Each translation is `PROPOSED`. Citation is evidence that a technique or
problem exists in the literature, not evidence that OEWAS implements it or inherits
its results.

## Typed composition and workflow semantics

| Source | OEWAS translation | Required nonclaim |
| --- | --- | --- |
| [Spivak: wiring-diagram operad](https://arxiv.org/abs/1305.0297) | Specify the exact generators and equations claimed by the planar composition layer. | The paper does not validate OEWAS operations. |
| [Yau: Operads of Wiring Diagrams](https://arxiv.org/abs/1512.01602) | Separate coloured profiles, substitution laws, and optional symmetric structure. | Shared vocabulary is not conformance. |
| [Patterson, Spivak, and Vagner: normal forms](https://arxiv.org/abs/2101.12046) | Explore canonical forms for replayable structural-equivalence tests. | A normal form is not behavioral equivalence. |
| [Workflow-net soundness complexity](https://arxiv.org/abs/2201.05588) | Add completion, reachability, and dead-task analyses beyond DAG checks. | OEWAS is not presently a workflow-net verifier. |

## Agent workflows and memory

| Source | OEWAS translation | Required nonclaim |
| --- | --- | --- |
| [ReAct](https://arxiv.org/abs/2210.03629) | Record typed action/observation transitions and explicit refusals. | A trace is not faithful access to private reasoning. |
| [Reflexion](https://arxiv.org/abs/2303.11366) | Store critiques as non-authoritative episodes linked to failed fixtures. | Reflection does not certify the repair. |
| [Voyager](https://arxiv.org/abs/2305.16291) | Treat generated skills as candidates with retrieval metadata and regression tests. | Skill-library growth is not admission or authority. |
| [AutoGen](https://arxiv.org/abs/2308.08155) | Model multi-agent exchanges as explicit state transitions with bounded roles. | Conversation structure is not correct coordination. |
| [StateFlow](https://arxiv.org/abs/2403.11322) | Separate state, transition guards, actions, and terminal conditions from prose. | A declared state machine is not workflow soundness. |
| [Agent Workflow Memory](https://arxiv.org/abs/2409.07429) | Retrieve prior workflows as candidates, then revalidate against current schemas and tools. | Retrieved precedent is never current evidence by itself. |
| [AutoFlow](https://arxiv.org/abs/2407.12821) and [AFlow](https://arxiv.org/abs/2410.10762) | Experiment with workflow search behind an evaluation bank and human admission gate. | Automated search must not write authority or production state. |

## Tools, interfaces, and evaluation

| Source | OEWAS translation | Required nonclaim |
| --- | --- | --- |
| [Toolformer](https://arxiv.org/abs/2302.04761) | Represent tool calls as typed operations with explicit input/output schemas. | Tool-selection ability does not prove safe effects. |
| [AgentBench](https://arxiv.org/abs/2308.03688) | Build environment-backed scenario fixtures and report per-capability results. | Aggregate score is not universal agent quality. |
| [SWE-agent](https://arxiv.org/abs/2405.15793) | Treat the agent-computer interface as a versioned contract with bounded observations. | Repository-task performance does not transfer automatically. |

## Structured generation

| Source | OEWAS translation | Required nonclaim |
| --- | --- | --- |
| [PICARD](https://arxiv.org/abs/2109.05093) | Reject inadmissible declaration tokens during constrained generation. | Syntactic validity is not schema, type, evidence, or authority validity. |
| [Grammar-Constrained Decoding](https://arxiv.org/abs/2305.13971) | Generate only the accepted fenced-declaration grammar and fuzz it against the parser. | Grammar acceptance is not semantic correctness. |
| [Decode-Time Grammars](https://arxiv.org/abs/2607.18357) | Measure grammar expressiveness, latency, and parser/decoder agreement before adoption. | Newer decoding research is not a reason to weaken validation. |

The parser should still validate in layers after generation: syntax, schema,
references/types, evidence, then admission.

## Provenance and supply-chain custody

| Source | OEWAS translation | Required nonclaim |
| --- | --- | --- |
| [W3C PROV-O](https://www.w3.org/TR/prov-o/) | Record entities, activities, agents, generation, use, and derivation edges. | A partial graph is not complete lineage. |
| [PROV-AGENT](https://arxiv.org/abs/2508.02866) | Prototype prompt/tool/evidence lineage with privacy and redaction rules. | Stored traces need not reveal or reproduce cognition. |
| [in-toto](https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias) | Bind steps, materials, products, and authorized functionaries. | Naming in-toto concepts is not supply-chain compliance. |
| [SLSA v1.2 provenance](https://slsa.dev/spec/v1.2/provenance) | Define verifiable origin fields and threat-model-specific verification. | A provenance JSON object alone is not a SLSA level. |
| [DSSE protocol](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md) | Authenticate payload type plus serialized body and specify key policy. | DSSE is an envelope, not signer authorization policy. |

## Prioritized research-to-code experiments

### R1: Grammar/parser agreement

Create a small formal declaration grammar, generate valid and invalid corpora, and
compare constrained decoder acceptance with parser/schema acceptance. Success means
zero unexplained disagreement on a hash-pinned corpus.

### R2: Semantic integrity mutations

Define canonical catalog content, then mutate every field. Success means each
semantically relevant mutation changes the digest or produces a typed refusal.

### R3: Provenance graph minimum

Record one compile run as source entities, parse/compile activities, process/human
agents, and output entities. Success means every catalog field can be traced to an
input or explicit default, with redaction behavior tested.

### R4: Workflow soundness ladder

Progress from current DAG checks to catalog resolution, reachability/completion,
dead-task detection, and effect conflict analysis. Keep each rung separately named.

### R5: Candidate workflow memory

Retrieve a prior workflow only as an inert candidate; rebind schemas and tools,
execute an evaluation bank, and require human admission. Compare against a no-memory
baseline. Never auto-promote based on score alone.

### R6: Attestation threat model

Write the local-shared-secret and cross-party-attribution threat models. Retain HMAC
for the former if sufficient; prototype DSSE plus asymmetric verification for the
latter. Test field tampering, key rotation, replay, and revocation.
