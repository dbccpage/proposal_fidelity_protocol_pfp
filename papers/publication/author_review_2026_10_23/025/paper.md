::: {align="center"}
# PFP: Local witnesses and global compatibility in agent composition

Jeremy H. Carroll

2026-10-23

Version 0.3.0
:::

## Abstract

Independently checked local answers can disagree on shared variables. We
give a finite gluing theorem for explicit assignment tables, retain the
overlap disagreements as obstruction evidence, and exhibit a three-agent
cycle in which every local task is satisfiable but the joint task is
not. The result explains a concrete role for LGGR in PFP agent
composition without claiming a general sheaf theorem or automatic
multi-agent reliability.

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

  Authorization                       None supplied by this paper or its
                                      replay
  -----------------------------------------------------------------------

## 1. Local tasks and the global question

Let $V$ be a finite variable set with finite declared domains. Each
agent's local task has a scope $S_i\subseteq V$ and an explicitly
supplied allowed relation $R_i\subseteq\prod_{v\in S_i}D_v$. A candidate
family selects $a_i\in R_i$ for each scope. Local satisfaction and
pairwise overlap compatibility are separate checks. Add full-domain
unary relations for any uncovered variable when a global-assignment
correspondence is required.

## 2. Finite compatibility theorem

**Theorem.** A locally permitted family glues to a unique assignment on
$\bigcup_i S_i$ precisely when every pair agrees on its intersection. If
the scopes cover $V$, compatible permitted families correspond
bijectively to global solutions of all local constraints.

**Proof.** If a global assignment exists, its restrictions agree.
Conversely, for each covered variable choose its value from any
containing scope. Pairwise agreement makes that choice independent of
the scope. The resulting assignment restricts to each selected row, so
it satisfies every relation. Every global assignment with those
restrictions has those same values, proving uniqueness. Restriction and
gluing are inverse maps when all variables are covered. An uncovered
variable with multiple values defeats uniqueness unless its value is
supplied separately; an empty uncovered domain makes global existence
fail. The full-domain unary relations retain these cases.

## 3. Three local successes and one global obstruction

Take Boolean variables $x,y,z$. The first agent checks $x=y$, the second
$y=z$, and the third $z\ne x$. Every relation has two rows, so every
local existence query succeeds. A global assignment would imply $x=z$
and $x\ne z$, a contradiction. In the selected family $(x,y)=(0,0)$,
$(y,z)=(0,0)$, $(z,x)=(0,1)$, the overlap value of $x$ disagrees.
Replacing the final relation by equality gives the two global solutions
$(0,0,0)$ and $(1,1,1)$ and compatible local restrictions for each.

This is the finite LGGR distinction: local green results need not
produce a global green result. A disagreement is an obstruction to the
declared gluing requirement, not an assertion that all differences are
inherently bad.

## 4. Agent packets and the integration check

The shared prompt explains row selection and the possibility of overlap
failure. The typed instance supplies domains, scopes, tables, and the
joint question. Each agent returns its actual row and local certificate.
The integrator replays local membership and checks common-variable
values before admitting a global witness. A loss ledger or a narrative
agreement cannot replace these values. Renaming variables requires
explicit bijections applied to the task and every witness; dropping an
overlap changes the problem.

## 5. Executable falsifiers

The [reference replay](code/replay.py) independently enumerates all
eight original global assignments and checks submitted local rows. It
verifies local nonemptiness of the incompatible cycle, refuses its
disagreeing family, and accepts the compatible equality family. A global
solution is decoded only from a family passing the overlap checks. There
are no model calls, observed swarm improvements, or new claims about
physical contextuality.

## 6. Scope and relation to WDP

The assignment gluing fact is standard. Its PFP use is a task-bound
composition contract that preserves local evidence while exposing
missing global compatibility. WDP §20.7 supplies the broader finite
constraint construction and zero-disagreement encoding. More general
agent composition additionally requires contracts for effects,
authority, timing, and representation change. Those cannot be
established from this static Boolean example alone.

The [two-level teaching packet](prompts/example.yaml) includes shared
system rules, this typed user instance, a different worked example and a
required candidate response schema. It keeps provider system/user roles
separate. It is a saved example, not a schema-admission or model-run
receipt; the local replay checks the mathematical or protocol
obligations stated above.

## 7. Typed operation composition is a different obligation

The current OEOP compiler checks ordered input and output slots,
declared effects and source-bound operation identities. This is not the
assignment gluing theorem: two callbacks with compatible types can still
disagree on task identity, candidate bytes or shared state. The
execution boundary must retain those bindings and observe the actual
operations. The finite theorem cannot supply an unimplemented callback,
undo a side effect or resolve a missing native host.

In the [bounded DDC repair study](../028/paper.pdf), the operation order
is C, R, E, I, M, T. Every stage carries the same run key, request
digest and candidate identity. Compilation uses the existing typed
workflow and operation-inventory boundaries; Adversary owns the working
copy and fixed checks. OEEIS screening and Prompt Civilization lineage
are injected services, not responsibilities absorbed into the capability
catalog.

A complete six-step execution is a concrete integration observation, not
a general gluing theorem for effectful agents. The example's original
source is unchanged, activation remains on hold, and no mathematical
residual is measured. The assignment proof and Boolean falsifiers above
are unchanged; they remain independent from this implementation study.

## Research extension: compatible evidence across a campaign

The harness campaign requires common experiment, source, checker,
partition, model configuration and original budget identities before
comparing evaluations. This is an evidence compatibility obligation. It
is distinct from the finite assignment-gluing theorem above: task
completion fractions are not assignments on a shared variable carrier,
and agreement among several task scores is not a proof of global
correctness.

A candidate that improves one family while degrading another is retained
as a rejected branch. Independent confirmation is still required when
all family scores appear favorable. The existing typed workflow compiler
checks declared connections; actual container execution and downstream
checks provide separate observations. A locally typed plan can still
produce a wrong answer or fail to execute. The current author-review
extension reports implementation, with the live campaign and its
transfer comparisons unmeasured.

The source and page references for this extension are collected in
[Paper 029](../029/paper.pdf) and its [source-to-claim
map](../029/docs/source_to_claim_map.md). The author-review rendering
does not replace a historical deposit or archive.

## Sources and relation to the programme

This draft builds on the [WDP
manuscript](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/witnessed_difference_programme.md),
[Paper 021's source-and-execution
distinctions](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/atlas/coda_atlas/F004_papers/015_pfp/021_recreated_demos_and_proposal_fidelity_evidence/paper.md),
and the [corrected findings
notices](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/atlas/coda_atlas/F004_papers/015_pfp/symbol_game_challenge_and_demos_findings/README.md).
[Paper
022](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/atlas/coda_atlas/F004_papers/015_pfp/022_pfp_frontier_research/paper.md)
supplies a research design whose live-model and offline-strategy claims
require their own source-bound scrutiny. These drafts do not adopt its
empirical tables as new measurements. The [PFP
collection](https://github.com/dbccpage/the_symbol_game/blob/59dde95a7860063c25d75db37f40af556e9f28ee/atlas/coda_atlas/F004_papers/015_pfp/README.md)
provides the shared-system/typed-instance protocol. Genesis and MSS-N
presentation stages do not license a new mathematical or physical
carrier.
