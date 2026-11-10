# Research 10: hybrids that preserve experimental meaning

Status: **proposed, not evaluated**. The repository baseline is `8050c66900899771766f33e8f5fdd200b7dd9120`. This report compared all 27 ideas in research_01 through research_09 with the foundation audit and composition-catalog metadata. It did **not** read the frozen seed, solve it, inspect private storage, or make any paid calls. The full structured specifications are in [research_10.json](research_10.json).

Three gaps remain after the earlier reports: preserving blindness when workflows are composed, distinguishing a present premise from a sufficient or nonvacuous premise context, and establishing whether a combination has an interaction benefit. The following proposals address those gaps rather than adding another generic draft/critic loop.

## R10-I01 — Information-flow certificates for blind composition

The proposed mechanism attaches an origin set to each typed artifact and request. Origins propagate through both data dependencies and control decisions. A blind challenger may see the unchanged seed and its frozen instructions; it may not see the solver's candidate, its hash or length, candidate-derived diagnostics, or a wrapper selected because of candidate content.

For node `v`, the host computes the union of direct, data-parent and control-parent origins in topological order. A request is admitted only when its origin set is contained in the recipient's frozen allowed set. This builds on information-flow typing rather than assuming that permission to invoke an operation controls everything the operation later reveals. The distinction is established in [Sabelfeld and Myers](https://www.cs.cornell.edu/andru/papers/jsac/sm-jsac03.pdf); the application to these workflow roles is proposed here.

The additional falsifiable check is relational. Holding public input and randomness fixed, replace a synthetic hidden artifact with another and require exactly the same blind-stage messages, tool manifest, model settings, allowance and dispatch choice. A difference exposes a leak. Synthetic probes do not prove arbitrary-code noninterference, and timing/provider-cache channels remain explicit residuals.

The DAG is:

`bind → audit_compiler → derive → blind_challenge → freeze`

The first model call produces a complete answer. The second produces bounded public challenges without seeing that answer. The host joins their artifacts only after both are frozen, annotates the original answer and stops. There is no repair call. The same two-call schedule is the baseline; the experimental intervention is the compiler/broker enforcement, not a new challenge strategy.

On a disjoint synthetic confirmation panel, the target is to block every registered leak while rejecting at most 2% of valid compositions. Compare colour-only, data-taint-only and full data/control-origin enforcement. Include candidate-conditioned wrapper choice, hashed candidate fields, exception messages, shared conversation history and benign sealed-host-packet controls.

This differs from **R05-I02**, which proposes a blind challenger, and **R08-I03**, which tests fault propagation: it tests whether blindness survives their composition. A shared serializer defect can defeat both provenance labels and probes. No result establishes statistical independence between model errors.

Relevant source boundaries:

- [PCIV taint propagation](../../pciv/use_cases/immunity.py), lines 108–131, is one pass over supplied edges; it is not arbitrary-order transitive closure and has no control-flow analysis.
- [OPERADS agent permissions](../../operads/domain/operad/operad.py), lines 126–158, restrict operation/colour access without examining materialized requests.
- [PFP feedback rules](../../pfp/use_cases/pfp_proposal.py), lines 35–45, already recognize that raw judge messages can disclose answers.

The honest external type is **(RunContext, VisibilityContract, SyntheticLeakPanel, PinnedRequestBuilder) → Outcome**. It becomes `RunContext → Outcome` only after independent external bundles are frozen by partial application or explicitly included in an extended RunContext.

## R10-I02 — Premise stress tests with finite countermodels

Dependency closure does not establish that an inference follows from its listed parents or that its premise context has any instances. This proposal gives a small number of candidate claims explicit premise ASTs and checks them in an independently supplied finite interpretation.

For finite carrier Ω, premises Γ = {a₁,…,aₖ}, and conclusion Q, compute:

- S = {w ∈ Ω : every a ∈ Γ holds}.
- W₀ = {w ∈ S : Q fails}.
- Wⱼ = {w ∈ Ω : every aᵢ except aⱼ holds, aⱼ fails, and Q fails}.

A replayed member of W₀ refutes the **encoded** implication. Empty S means only `VACUOUS_IN_SCOPE`. A member of Wⱼ shows that deleting that premise permits a failure in this finite interpretation. It does not establish globally minimal assumptions or a causal role for the premise. An empty countermodel search remains `NO_COUNTERMODEL_IN_SCOPE` unless the carrier demonstrably exhausts the declared finite domain. These distinctions follow the bounded-analysis contract in the [official Alloy reference](https://alloytools.org/download/alloy-language-reference.pdf).

Uninterpreted Boolean assignments may be mathematically unrealizable. They therefore remain dependency diagnostics unless a separate decoder verifies a concrete witness against every original domain constraint. The audit never changes the immutable seed or substitutes an audit context for the original task context.

The DAG is:

`bind → draft → stress → patch → freeze`

PFP checks and replays the declared witness relation; EIS distinguishes invalid inference, scoped vacuity and premise dependence; PCIV records one protected wrapper patch; OPERADS distinguishes original contexts from premise-deletion audit contexts. The second call receives only public, scope-labelled findings and corrects or qualifies the original answer. Unsupported analytic claims remain open.

The baseline has the same two calls but only dependency/context closure. Ablations omit antecedent satisfiability, premise-deletion views or independent witness replay. Synthetic confirmation controls include inconsistent antecedents, omitted necessary premises, redundant premises, valid implications with no sampled antecedent instances, and unrealizable abstract countermodels. Any false concrete refutation of a supported valid fixture defeats the checker claim. The seed comparison additionally requires no more than a preregistered three-point rubric loss.

This differs from **R01-I01/I02** and **R08-I02**: its target is sufficiency and nonvacuity of the encoded premise context, not merely graph closure, definedness or extractor discrimination. Independent arithmetic implementations can still share a wrong interpretation.

The external type is **(RunContext, PublicPremiseTheory, FiniteCarrier, ReferenceReplay) → Outcome**. A model's AST cannot authorize its own theory. [Exact rational arithmetic](../../pfp/domain/exact/q.py), lines 22–43, supplies only a limited replay substrate.

## R10-I03 — Factorial isolation of hybrid synergy

A hybrid beating a baseline does not show that its components interact beneficially. Fix one two-call draft/revision graph and independently toggle:

- **A:** typed premise/dependency contexts and their host validation.
- **B:** calibrated public diagnostic guidance before revision.

PCIV freezes all four wrappers and their lineage; PFP binds artifacts; EIS supplies the diagnostic intervention; OPERADS fixes the graph and visibility contract. Every assigned run executes exactly one of the four cells, preserving the same complete seed and output ceilings.

For expected fixed-seed rubric score μₐᵦ, the primary interaction is

**Δ = μ₁₁ − μ₁₀ − μ₀₁ + μ₀₀.**

Report all cell means and marginal effects. Positive individual effects do not imply positive Δ. The separation of main effects from interactions is the reason for the full design described in the [NIST experimental-design guidance](https://www.itl.nist.gov/div898/handbook/pri/section4/pri43.htm).

The assigned-run DAG is:

`bind → draft → diagnose → revise → freeze`

Assignments use a preregistered balanced schedule within model/time blocks, with fixed replication and fresh provider samples. The off arms still solve the entire task and revise it; they omit only their assigned optional mechanism. The same final measurements apply to every cell. Failures, timeouts and truncations remain in the denominator.

The stated hypothesis is Δ ≥ 3 rubric points, with the hybrid no more than two points below the best single-mechanism arm. A claim requires the preregistered uncertainty treatment to support that threshold. The JSON supplies a conservative bounded-score interval; small samples may be inconclusive. Equal output ceilings, equal money and equal wall time are distinct comparisons.

This differs from **R04-I03**'s order test and **R09-I01**'s repair-versus-rederivation allocation: it measures an interaction at fixed order and call count. A common model misconception or parser defect can affect all four arms. Private grades are terminal offline observations, never input to within-run routing or prompt updates.

The assigned-run type is **(RunContext, FactorialAssignment, FrozenFactorialProtocol, CalibratedPublicCheckerBundle) → Outcome**. The campaign analysis is separately **(FrozenOutcomes, PostFreezeTrustedScores, FactorialProtocol) → InteractionReport**. It is not a solver composition. Existing [PCIV research selection](../../pciv/use_cases/research_selection.py), lines 18–87, does not estimate this interaction.

## Budget, execution and composition limits

Each proposed run has **at most two model calls, zero retries and zero fallbacks**. One ledger includes the exact seed, all messages and artifacts, all billable reasoning/output tokens, provider fees, metered host work and any paid evaluation.

Conditional admission thresholds are input ≤ USD 0.000001/token, output ≤ USD 0.000005/token, no fixed fees, no paid judge, and USD 0.01 additional reserve:

| Idea | Total input ceiling | Total billable output ceiling | Complete-run reservation |
|---|---:|---:|---:|
| R10-I01 | 12,000 | 4,200 | USD 0.043 |
| R10-I02 | 14,000 | 4,400 | USD 0.046 |
| R10-I03, one assigned arm | 14,000 | 4,400 | USD 0.046 |

These are **conditional affordability examples**, not current provider-price claims. Actual tokenization and capped billing semantics must be verified before dispatch. Unknown charges, uncapped reasoning or additional paid calls cause refusal. Timeout/cancellation does not release uncertain reservations. Never truncate the seed to fit.

A four-cell factorial block is four runs, not one hidden eight-call run: it reserves USD 0.184 at the example thresholds, or USD 0.40 at the absolute per-run caps. Replication needs a separately authorized aggregate campaign budget. No campaign was launched.

All model stages receive the same exact seed bytes in an isolated message. Private keys, private derivations and evaluator diagnostics have no workflow edge. Native [workflow compilation](../../operads/application/typed_workflow_compiler.py), lines 327–362, is single-consumer and requires exact full port interfaces; the packet chains here are proposals requiring concrete schemas and broker implementations. No implicit fan-out, calibration-input fabrication or correctness upgrade follows from the names `RunContext` and `Outcome`.

The recommended first implementation is a **VisibilityAndContextBoundaryV1** host contract with synthetic leakage and countermodel-replay controls. Its value can be tested before any paid benchmark and without accessing the seed.
