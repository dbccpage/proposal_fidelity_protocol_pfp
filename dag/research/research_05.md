# Research 05: independent panels without consensus authority

Status: **proposed_not_evaluated**. These are three repository adaptations, not claims of literature-wide novelty or measured gains. No paid call, seed solution, or private evaluator access occurred. Seed SHA-256 remained `9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7`.

| Idea | Mechanism and dependency DAG | Conditional whole-run reservation |
|---|---|---:|
| R05-I01 | Freeze → two isolated complete proposals → premise-aware equivalence checking → minimal represented disagreement frontier → deterministic whole-answer selection | $0.047; 2 × 2,500 output tokens |
| R05-I02 | Freeze → solver and candidate-blind challenge designer → host witness checks → annotated original answer | $0.0425; 3,000 + 1,500 output tokens |
| R05-I03 | Freeze → full answer/DAG → mask up to four seam conclusions → reconstruct seams → check equivalence and propagate residuals | $0.0475; 2,800 + 1,900 output tokens |

These amounts assume input at most $1/million tokens, all billable output/reasoning at most $5/million, zero fixed fees, and $0.01 quantified reserve. Respective total input caps are 12,000, 10,000 and 14,000 tokens, including repeated unchanged seed and framing. They are conditional admission examples, not current price quotations. All branches are included, retries/fallbacks are disabled, and unbounded billing causes refusal before dispatch. Local checking assumes zero incremental monetary cost. Separate ablations require separate run reservations; no campaign was launched.

R05-I01 extends WF4's isolated proposal pattern by locating disagreement under explicit shared premises. Two different expressions may be equivalent, and two equal expressions may both be wrong. The host therefore distinguishes checked equivalence, witnessed incompatibility and unknown. It selects a whole candidate by a frozen public-check rule; no unverified merging of prose is allowed.

R05-I02 adapts WF15's frozen sides into an answer producer and a critic who cannot see that answer. The critic proposes typed boundary tests from the public task; only the host can establish that an objection has a valid-domain witness. For a universal assertion, one checked counterexample refutes it. Passing finitely many tests does not prove it. Criticism of a sufficient condition must not confuse failure of its antecedent with a counterexample.

R05-I03 replaces WF28's many visible roles with a single masked reconstruction call. It targets up to four structurally selected dependency interfaces, withholding candidate conclusions while preserving the original seed. This is partial blinding, not independent generation: the original candidate supplies premises and graph structure. Agreement under those premises cannot establish the premises. Unknown/refuted parents remain visible in downstream status.

The literature supplies strong baselines, not correctness guarantees. [Wang et al.](https://arxiv.org/html/2203.11171v4) sample multiple reasoning paths and aggregate answers. [Du et al.](https://proceedings.mlr.press/v235/du24e.html) study proposal-and-debate rounds. [Choi, Zhu and Li](https://arxiv.org/html/2508.17536v2) compare voting with debate and analyze a particular stochastic belief-update model; its martingale conclusion is conditional on that model, not a universal impossibility theorem for verification-assisted debate.

No workflow assigns a confidence bonus merely for different roles or model names. If equal-marginal Bernoulli error indicators have rate `e` and correlation `rho` on a declared distribution, their joint error probability is `e² + rho e(1-e)`. A pair of artifacts cannot estimate those quantities. Conditional sampling independence on one task and correlated error rates across tasks are different claims. Neither is inferred from an isolation manifest.

Each proposal has a falsifiable comparison: claim-aware versus string disagreement; blind versus visible challenge generation; masked versus visible seam replay. Public synthetic controls must include shared errors, equivalent rewrites, missing premises and invalid-domain objections. Final correctness and completeness are evaluated only after candidate bytes are frozen. Repeated calls on one seed do not establish transfer to a task population, and WF31's held-out terminology cannot create such evidence here.

Recommended reusable primitive: **FrozenPanelComparisonV1**, specified in the accompanying JSON. It binds artifact visibility, premises, domains, checker versions, three-valued comparisons and unresolved obligations. Its central invariant is that agreement never upgrades correctness. All schemas and adapters remain proposals.
