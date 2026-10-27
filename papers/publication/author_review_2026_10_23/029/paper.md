::: {align="center"}
# Evidence-Bound Harness Evolution: Search, Failure Memory, and Held-Out Transfer

Jeremy H. Carroll

2026-10-23

Version 0.1.0 --- author-review methods and implementation draft
:::

## Abstract

An agent can propose changes to the software that organizes its own
attempts. Whether the changes improve research performance is an
experimental question; whether a particular submitted result passes a
declared checker is a separate verification question. We implement an
explicit experimental re-entry path over existing Engine
subsystems, inspired by mechanisms reported for AIDE2. The path retains
candidate ancestry, isolates candidate execution, reserves provider
liability against one durable budget, separates public feedback from
private grading, and requires fresh confirmation before replacing an
experimental incumbent. A frozen protocol allocates a maximum of \$40 to
three evolution trajectories, untouched transfer, ablations and an
exploratory ignition comparison. This revision contains implementation
and offline checks. Linux testing and the paid campaign were deferred by
the operator on 23 October 2026, so there are no new model trials,
measured improvements or transfer results. Missing experiments remain
explicitly unmeasured. Neither the implementation nor an eventual
favorable trajectory would establish accelerating self-improvement.

## 1. Question and source boundary

The question is whether changes to a bounded research harness improve
exact task completion, cost, or both under a fixed provider and
evaluator configuration. The experimental object is the harness: its
prompts, workflow options, search policy and context policy. The task
checker and the budget controller are parts of the measuring apparatus.
Giving the experimental object write access to that apparatus would
change the meaning of an observed improvement.

Srikanth and colleagues describe a nested optimization in which an outer
agent rewrites an inner research agent and evaluates each rewrite on
hidden grades \[1, pp. 3--4\]. They report seven accepted improvements
during an eight-day run and evaluate transfer on additional benchmarks
\[1, pp. 5--7\]. These are the authors' reported findings. They are not
observations from this repository, independent replications, or premises
of the finite PFP theorems.

The supplied source is arXiv:2609.26457v1, 28 pages, with SHA-256
`8ba79e0ad1028e43b0a47ee06162c9b3996ec90f7990b7ec35993444e505409b`. The
[source-to-claim map](docs/source_to_claim_map.md) identifies page-level
support and separates reported findings, implemented mechanisms,
measurements and hypotheses. The version and digest are fixed even if a
later revision of the external paper appears.

## 2. Mechanism inventory and ownership

  -----------------------------------------------------------------------
  Owner                   Implemented             Evidence ceiling
                          responsibility
  ----------------------- ----------------------- -----------------------
  OEOP                    Versioned experiment,   A typed connection does
                          candidate, evaluation   not prove callback
                          and decision contracts; correctness
                          existing typed workflow
                          compilation

  Adversary                  Explicit research       Experimental selection
                          orchestration, public   does not deploy a
                          search, private         capability
                          evaluation,
                          confirmation and
                          retained evidence

  PFP                     Exclusive provider      List-price accounting
                          admission, transport,   is not an invoice audit
                          reservations and
                          token-usage settlement

  OEEIS                   Scoped failure guidance Diagnostic candidates
                          with reproducers and    are not admitted or
                          benign controls         activated antibodies

  OEPCIV                  Protected host context, Ancestry does not
                          candidate genealogy,    authenticate an
                          rejected branches and   external author
                          exact Pareto comparison

  OEOS                    Rootless container      Isolation must be
                          process and resource    observed on the actual
                          control                 Linux host
  -----------------------------------------------------------------------

The command exposes `preflight`, `run`, `resume`, `replay` and `report`.
Ordinary learning retains its recursion suppression and publication
rules. The research use case can continue from confirmed candidate bytes
without opening a pull request or granting production admission. This is
an explicit experimental use case, not a new general agent framework.

Typed workflow tasks reuse the C/R/E/I/M/T repair sequence described in
Paper 028. Its host-selected check callback invokes the container
adapter and checks the downstream output. The earlier supplied-patch
example remains historical evidence of a narrower path. Working-copy
separation in that example is not retroactively described as an
operating-system sandbox.

## 3. Candidate and evidence identities

An experiment fixes source and checker manifests, all task partitions,
model IDs and configuration, the original budget identity, and analysis
choices. A candidate retains its parent, source identity, strategy
label, mutation description and complete allowed file bytes. The only
editable files are `prompt.txt`, `workflow.json`, `search_policy.py` and
`context_policy.py`. The serialized editable file set is capped at 3,600
bytes to reserve room for outer re-entry context. The outer role
receives the root, current champion, six task aggregates and two recent
decision references from its own trajectory. Private fixtures, checkers,
provider credentials, admission and accounting code are outside that
surface.

An evaluation occurrence identifies the experiment, candidate, parent,
source, checker, split, task, repetition, model and configuration. It
retains the submitted program, raw model response references, actual
execution outputs, public and private verdicts, and cost. An incumbent
decision cites the selection and confirmation receipts on which it
depends. Changed candidate bytes, a stale parent, a substituted checker
or a foreign task cannot inherit a prior acceptance merely by preserving
a favorable label.

Content-addressed objects and a chained journal detect inconsistent
local alterations. These checks do not authenticate a provider
independently of the trusted transport, protect against a trusted host
rewriting all records and anchors, or establish a reproducible compiler
build. Provider repetitions are fresh calls; replaying one response
against a checker is not another trial.

## 4. Reference search and bounded context

The reference has five strategy labels: conservative, aggressive
rewrite, ensemble, tuned specialist and robust simple. After untried
arms are sampled, UCB1 uses empirical mean public score and the
exploration term $\sqrt{2\log N/n_a}$. With probability 0.30 it instead
samples a softmax over the best score seen for each arm, at temperature
one. Every fifth step forks the champion under a different strategy. The
local seed, random draw, selected arm, parent and scheduling constants
are retained. These choices implement a specific reference policy
inspired by \[1, p. 9\]; they are not identified as the authors' exact
source code or a reproduction of their benchmark results.

The drafting and repair contexts include the root, champion, two recent
attempts and retained evidence references. Host checks refuse a
projection that drops required references. The reference compresses
attempt detail into summaries; the full-history comparator retains prior
code. Both remain subject to the same provider input bound. The host's
conservative text-byte ceiling is stricter than the nominal
8,000-input-token allowance.

Failure memory is considered only when candidate execution errors reach
15% of relevant observations. At most three deduplicated signatures are
included. Provider errors are a separate category. Each eligible
signature retains a reproducer and benign control and remains scoped to
the task kind. These thresholds are design choices from \[1, p. 9\], not
calibrated constants of a general reliability theory.

A repair must include a diagnosis when the diagnosis mechanism is
enabled. The host verifies its presence and retains it; it does not
certify the truth of a natural-language root-cause explanation. A
substantive-output gate rejects empty or nearly empty programs before
execution. Exact downstream checks still determine task success. The
ineffective median-score adjustment discussed in \[1, p. 10\] is
deliberately omitted.

## 5. Frozen tasks and comparators

Selection uses two instances from each of three families: exact-type and
stale input binding repairs, C052 max-flow/min-cut and C054
linear-system certificates, and typed workflows with checked downstream
results. Fresh confirmation cases are frozen separately; both selection
and confirmation remain optimization data. Public input projection omits
expected outputs, reference implementations and private fixture
databases. Identifiers do not encode the desired verdict.

Untouched transfer contains four new tasks from each selection family
and eight C059 SQL/NULL-semantics tasks. The SQL family is excluded from
discovery. Cases are generated afresh from the fixed local generation
seed. Private inputs and grading results are never injected into the
inner search context. Private selection feedback may inform later outer
rewrites, so it is not described as held-out evidence after
optimization.

The current-policy comparator projects the existing sequential
propose/check behavior into the common task adapter. It has no strategy
diversification, compression, failure memory or diagnosis requirement.
It is not a claim that the unchanged production learning service has run
this campaign. The second baseline is the hand-engineered reference.
Three independent trajectories start from the same reference and each
allow six outer rewrite proposals. The final incumbent of every
trajectory is retained, including a reference that never improves.

Each discovery comparison uses paired candidate/incumbent evaluations,
three fresh repetitions per task and at most six inner turns. Exact
completion fractions and cost remain separate objectives. The ordering
is correctness first, cost second, with the incumbent retained on
unresolved ties. Fresh confirmation, no task-family regression, and
invariant controls are necessary for replacement. Failed, refused,
timed-out and incomplete assignments remain in the denominator.

## 6. Budget, restart and execution isolation

  Phase                            Maximum USD
  ------------------------------ -------------
  Preflight                                  2
  Discovery and confirmation                16
  Untouched transfer                        10
  Ablations                                  6
  Exploratory ignition                       4
  Infrastructure retry reserve               2
  Total                                     40

The outer model is `claude-sonnet-5-5` and the inner model is
`claude-haiku-5-5`. Requests use explicit adaptive-thinking
configurations, no sampling parameters unsupported by those models, no
tools and no prompt caching. Inner output is capped at 2,000 tokens and
outer output at 3,000. The same SQLite budget persists across phases,
descendants and restarts. Atomic reservations enforce phase limits and
at most two in-flight requests; the initial dispatcher is sequential. An
interrupted call or missing usage retains its maximum liability and
prevents further dispatch pending reconciliation. Rejected response
content can still carry billable usage.

At the retained 2026-10-23 uncached observations, a maximally sized
inner call reserves \$0.0018 and an outer call \$0.046. The planned
discovery bound of 8,100 inner calls and 18 rewrites is \$15.408 before
retries. This is a planning calculation, not measured expenditure.
Pricing observations expire and must be refreshed before dispatch.
Infrastructure hosting is outside the API ceiling.

The prepared deployment targets a user-provisioned Ubuntu 24.04 x86-64
server with rootless Podman and cgroup v2. Candidate containers have no
network, credentials, private evaluator mounts or repository write
access. They have read-only source mounts, bounded memory, CPU, process
count, file size, output and elapsed execution time. A real isolation
probe is a prerequisite for paid discovery. This revision has not
executed that probe on the requested server.

## 7. Analysis, ablations and ignition

Transfer analysis pairs harnesses by task and averages the three fresh
model trials within each task. It reports exact completion fractions,
token usage, list-price cost, public/private disagreement, execution
errors, context size and retained strategy diversity. Confidence
intervals use 2,000 paired task-level bootstrap draws with a declared
local analysis seed. Comparative tests use a two-sided exact paired sign
test. Holm correction covers seven predeclared transfer contrasts:
reference versus current policy and each final incumbent versus both
baselines. Incomplete panels do not earn comparative claims.

A separate 12-task panel compares trajectory zero's final incumbent with
four variants removing diversification, compression, failure memory and
diagnosis separately. Choosing trajectory zero before transfer prevents
selection on the transfer outcomes. The four ablation contrasts form a
separate Holm family. These are tests of the implemented mechanisms in
this bounded setting, not universal causal explanations for the external
paper's gains.

The ignition experiment compares the original outer policy with the
evolved outer harness in three paired repetitions of three rewrite
steps. Both outer arms use Sonnet and the same initial inner reference.
To remain within \$4, ignition inner evaluations use one repetition and
one inner turn per task, with separately assigned confirmation calls.
The protocol records this lower resolution. Results are exploratory. The
external paper likewise reports its own ignition comparison as
inconclusive \[1, pp. 10--11\]. Neither experiment establishes
accelerating returns or an indefinitely improving process.

## 8. Current results and remaining execution

The machine-readable campaign report is produced by offline replay. At
this revision it records **NOT_RUN**, zero independent provider calls,
zero assigned model trials, zero settled API spend and zero held API
liability. Consequently, completion rates, transfer effects, ablation
effects and ignition effects are **NOT_MEASURED**. No synthetic trace is
presented as a live experiment.

Local verification exercises exact-type contracts, protected edit
surfaces, confirmation and family-regression gates, memory scope,
raw-byte tampering, concurrent reservations, restart holds and
malformed-answer settlement. Existing repair and ordinary-learning tests
are run separately. The [reproduction guide](docs/reproduction.md)
identifies commands and the retained verification receipt. Windows unit
checks do not certify Linux containment.

The frozen campaign must be replayed against its retained source bytes.
Subsequent main changes are not silently substituted into that
experiment. The reproduction guide supplies an archive-bound offline
command that checks package custody both before and after replay. Its
isolated Python process uses existing dependencies and refuses
networking and child processes. This follow-up improves reproduction of
the zero-call report; it supplies no additional model trial, Linux
isolation observation or fresh dependency-installation result. The
original review archive retains the earlier manuscript snapshot.

Linux testing and paid execution were initially deferred for this
delivery. The operator subsequently selected Windows verification and
removed Linux testing from scope. The Windows checks exercise offline
behavior; the frozen rootless runner remains Linux-specific. They do not
establish Windows containment for generated programs. A Windows live
campaign would require a separately reviewed containment adapter and
protocol revision. Provider compatibility, containment, live task
calibration and the entire paid campaign remain NOT_RUN. An experiment
curtailed by budget or infrastructure must retain its assigned trials
and refusal records; it must not be rewritten as a successful
trajectory.

## 9. Relation to finite PFP results

Paper 024's solution-map composition theorem requires explicit soundness
and coverage hypotheses. Experimental incumbent selection supplies
neither a new solution map nor proof of those hypotheses. Shared fuel
limits expenditure; it does not imply useful progress.

Paper 026's future-preservation result concerns a finite deterministic
quotient preserving action availability, exact cost, successor classes
and terminal labels. The heuristic context summaries here do not meet
that specification merely by being shorter. Dropping a reference can
disable a later operation; retaining a reference can still lose the
content needed to use it correctly. Measured context size and task
completion therefore remain distinct from operation-preservation claims.

The claim-scoping rule in Paper 023 applies separately to each checked
output. The compatibility theorem in Paper 025 does not turn
independently favorable task scores into a coherent global guarantee.
Paper 027 permits changing the proposal channel while holding host
obligations fixed. This study adds an implemented experimental
procedure, not a new formal theorem or Lean result.

## References

1.  Dhruv Srikanth, Bingchen Zhao, Dixing Xu, Yuxiang Wu and Zhengyao
    Jiang. *Recursive self-improvement of AI research agents*.
    arXiv:2609.26457v1, submitted 22 September 2026. [Versioned
    source](https://arxiv.org/abs/2609.26457v1).
2.  [Paper 024: recursive re-entry and shared fuel](../024/paper.pdf).
3.  [Paper 026: future-faithful compression and cost](../026/paper.pdf).
4.  [Paper 028: typed composition and bounded DDC
    repair](../028/paper.pdf).
5.  Anthropic, [Haiku 5.5 model
    overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview)
    and [Sonnet 5.5 model
    overview](https://platform.claude.com/docs/en/models/sonnet-5-5/overview),
    observed 23 October 2026.
