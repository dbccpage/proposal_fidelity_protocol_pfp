::: {align="center"}
# PFP: Recursive re-entry with evidence scope and shared fuel

Jeremy H. Carroll

2026-10-23

Version 0.2.0 --- author-review extension
:::

## Abstract

A returned answer, rejection rule, or operator can become the next
proposal. This recursion is useful only when its task, evidence,
transport, and resource bindings survive. We state a finite composition
theorem, separate soundness from solution coverage, and exhibit a
source-sound rejection rule that is unsound after a task change.
Positive charged costs bound execution without establishing that the
original problem has been solved.

## Mechanism inventory

  -----------------------------------------------------------------------
  Mechanism                           Evidence
  ----------------------------------- -----------------------------------
  Mathematical statement              Written proof under declared
                                      hypotheses

  Finite example                      Standard-library replay of
                                      submitted inputs and rejection
                                      controls

  Model inference                     Not executed

  Lean verification                   No new formalization claimed

  Authorization                       None supplied
  -----------------------------------------------------------------------

## 1. The re-entry contract

Fix the original task $P_0$ and representations $P_1,\ldots,P_n$. Each
admitted edge supplies a backward solution map
$b_i:\operatorname{Sol}(P_{i+1})\to
\operatorname{Sol}(P_i)$ and, separately, a forward coverage map $f_i$
in the opposite direction. A certificate binds the source and target
task data, checker versions, parent receipt, and operation charge.
Assumptions cannot change silently. A changed assumption set produces a
changed or conditional task result. An authorization requirement is
supplied independently.

## 2. Finite composition theorem

**Theorem.** Under the declared edge obligations, a checked solution at
$P_n$ decodes to a solution at $P_0$ by $b_0\circ\cdots\circ b_{n-1}$.
Forward maps compose in the opposite order and retain the stated
coverage. If original witness recovery is required, additionally assume
$b_i\circ f_i=\mathrm{id}$; that law then composes. If every operation
costs at least $\delta>0$ and all prefixes charge one original budget
$B$, at most $\lfloor B/\delta\rfloor$ operations execute.

**Proof.** Induct on history length. Apply the last backward map to the
terminal solution, then the induction hypothesis. The forward argument
is the same induction with arrows reversed. Cancel each adjacent
$b_i f_i$ for the recovery law. For the cost bound,
$n\delta\le\sum_i c_i\le B$. These are conditional composition laws:
they do not construct missing adapters, prove checker soundness, or
validate the legitimacy of a grant.

## 3. Soundness does not imply coverage

Let the original solution set be $\{0\}$ and the target solution set
empty. The empty backward map is sound, but no forward coverage map
exists. A target search can therefore fail despite an original solution.
Conversely, an adapter preserving existence can still lose original
witness identity unless the recovery law is supplied. These are
different requirements.

## 4. Antibody transfer counterexample

An antibody is a rejection predicate $r$. Its validity for a task is
$r(w)\Rightarrow w\notin\operatorname{Sol}(P)$. On the domain $\{0,1\}$,
let $\operatorname{Sol}(P)=\{0\}$ and let $r$ reject $1$. It is
source-sound. For a changed task $P'$ with solution set $\{1\}$, the
same predicate destroys the only valid answer. Transferring it requires
a checked target validity condition or a transport theorem whose
hypotheses apply to the target. Unchanged syntax and a familiar task
name are insufficient.

Truth-sound rejection also need not preserve the reachability or cost of
a controller strategy: a proposal channel may rely on intermediate
candidates that are not terminal solutions. Appendix S supplies the
additional game conditions for a declared finite execution. Task
soundness, solution coverage, and protected operating budgets must be
checked separately.

## 5. Re-entry example and replay

The [companion](code/replay.py) checks a two-operation history with unit
costs and total budget two. It rejects a stale parent, a changed task,
and a child claiming to reset consumed fuel. It also checks the
vacuous-soundness example and the antibody counterexample using complete
finite sets. This is a reference contract example, not a claim that
every engine adapter has these bindings. Model requests, installation,
and external work require separately declared charges; omitting them
weakens the resource statement.

## 6. Evidence boundary and contribution

Function composition and the cost inequality are standard mathematics.
The PFP/WDP contribution is their placement in a retained re-entry
contract with explicit task, parent, checker, and cost scope. The
example is executable; the general statement is written. Constructing
and independently checking the actual native re-entry adapter remains an
open WDP target. Recursion alone does not guarantee resolution,
intelligence, or authorization.

The [two-level teaching packet](prompts/example.yaml) includes shared
system rules, this typed user instance, a different worked example and a
required candidate response schema. It keeps provider system/user roles
separate. It is a saved example, not a schema-admission or model-run
receipt; the local replay checks the mathematical or protocol
obligations stated above.

## Research extension: explicit incumbent re-entry

The implemented research entrypoint makes a confirmed harness the parent
used by the next outer proposal. Its state includes the original
experiment and budget, current candidate bytes, parent identity, frozen
checker and split identities, model configuration, and selection and
confirmation receipts. A replay validates these bindings before
reconstructing an incumbent chain. Ordinary learning hooks retain their
recursion suppression; this explicit experimental path does not silently
turn a successful completion notification into another provider call.

Candidate and incumbent are evaluated in paired assignments, followed by
fresh confirmation. Exact completion fractions and recorded cost remain
separate objectives. Correctness has priority, cost breaks resolved
correctness ties, and an unresolved tie retains the incumbent. No task
family may regress. Passing invariant controls is necessary but does not
establish semantic correctness of all permitted future programs.

The shared-fuel argument above concerns positive charged costs under a
fixed resource identity. The implemented ledger reserves maximum
liability before transport and retains ambiguous charges across restart.
A proposed child cannot reset the budget. This bounds authorized
dispatch under the declared pricing and transport assumptions; it does
not prove that a successor solves the original task or makes research
more effective.

An empirical improvement receipt is not a backward solution map, a
coverage map, or a proof of compositional soundness. Those objects still
require the theorem's hypotheses. The three short paired ignition
repetitions in Paper 029 are explicitly exploratory and cannot establish
accelerating self-improvement. Current model performance is unmeasured;
the new implementation extends the operational example without adding a
formal theorem or altering the finite proof above.

The source and page references for this extension are collected in
[Paper 029](../029/paper.pdf) and its [source-to-claim
map](../029/docs/source_to_claim_map.md). The author-review rendering
does not replace a historical deposit or archive.

## Sources and relation to the programme

This draft builds on the [WDP
manuscript](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/witnessed_difference_programme.md),
[Paper 021's source-and-execution
distinctions](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/omega_engine_atlas/coda_atlas/F004_papers/015_pfp/021_recreated_demos_and_proposal_fidelity_evidence/paper.md),
and the [corrected findings
notices](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/omega_engine_atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/README.md).
[Paper
022](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/omega_engine_atlas/coda_atlas/F004_papers/015_pfp/022_pfp_frontier_research/paper.md)
supplies a research design whose live-model and offline-strategy claims
require their own source-bound scrutiny. These drafts do not adopt its
empirical tables as new measurements. The [PFP collection
guide](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/omega_engine_atlas/coda_atlas/F004_papers/015_pfp/README.md)
provides the shared-system/typed-instance protocol. Genesis and MSS-N
presentation stages do not license a new mathematical or physical
carrier.
