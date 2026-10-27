# ACSets, DPO and optional backend experiments

AuthorityEffect: None. These are bounded offline controls for V1.0RC.
The default application keeps its existing Python/Rust runtime and PFP envelope.
Julia and DSPy are optional demonstrations, not production dependencies.

> **Source check (2026-10-20, pin `c419cc6beb`).** The three linked pilot directories exist under `adversary/tests/pilots/`. The counts below match the test files: `test_acset_prompt_rewriting.py` and `test_acset_cochain_rewriting.py` each define 25 test functions, and `optional_rewrite_backends/dspy/test_demo.py` defines 11 test functions, one parametrized over 4 malformations, giving 10 + 4 = 14 controls. These tests were not run in this check.

An attributed C-set gives a typed relational carrier. This pilot uses one fixed
attributed directed-graph schema: parts, links, source/target incidence, kinds and
exact string attributes. It does not implement arbitrary categorical schemas.
A DPO rule specifies a left pattern, an unchanged interface and a replacement.
The host accepts only registered rules and explicit injective matches. It checks
attribute/incidence preservation, dangling edges, protected objects and fuel
before returning a new immutable state. It performs no automatic match search.

## Two questions, two pilots

| Pilot | Question | Independent deciding check |
| --- | --- | --- |
| [Prompt rewriting](../../../../adversary/tests/pilots/acset_prompt_rewriting/README.md) | Can permitted structural rewrites preserve a nontrivial prompt's protected content and complete bindings? | Ordered task/constraint/output query and original UTF-8 text agreement |
| [Cochain rewriting](../../../../adversary/tests/pilots/acset_cochain_rewriting/README.md) | Can a registered rewrite repair declared edge values while preserving topology and potentials? | Exact rational value minus endpoint potential difference on every directed edge |

Each has 25 separately collected deterministic cases. Benign operations are
paired with malformed matches, unauthorized changes and other hostile controls.
Offline candidate replies are explicitly fixtures. They are never labelled as
actual model replies, provider trials or evidence of improved LLM reasoning.
Prepared prompts and strict typed replies use the existing PFP task boundary.

Structural acceptance alone does not establish prompt meaning or cochain
correctness. The pilot judges run after the rewrite. A sum of signed edge errors
can vanish while individual errors remain; the cochain judge checks the vector.
Its residual is not a minimized quotient obstruction or an optimality certificate.
This experiment supplies no new physical bridge for Meron.

## Registration, replay and names

Rule names select an immutable host registry. Receipts bind the complete rule,
labelled input/output graph digests, explicit match and remaining fuel. Identical
names with different rule bodies cannot be treated as identical evidence.
Graph identity here includes stable labels; graph isomorphism is a separate claim.
Replay recomputes the actual operation and deciding checks, not a stored PASS flag.

The existing polygraph validator now requires each supplied ground rewrite step
to belong to its registered rule set. A known name with changed location, source
or result also fails. Continuous paths and a shared endpoint remain separately
checked. These checks establish the supplied finite paths; global confluence and
automatic critical-pair completeness remain open.

Prompt/adapter identifiers carry a role and explicit version in each pilot's
specification. The shared PFP envelope remains the transport contract. The
optional graph layer controls permitted changes behind that interface; users do
not need to write categorical diagrams or learn another packet format.

## One optional demo per backend

The [optional backend guide](../../../../adversary/tests/pilots/optional_rewrite_backends/README.md)
contains one Julia ACSets/DPO demo and one DSPy demo. Install their dependencies
only in the guide's isolated environment. Neither is imported by the default
application or added to its dependency list.

Julia is a reference experiment for declarative graph rewriting and exact
attributes. Its result must be checked against independently calculated edge
residuals and invalid deletion controls. Version pinning and actual execution
availability belong to that demo's retained result, not a general parity claim.

DSPy is an experiment in typed signature/module composition. Its model boundary
still passes through PFP preparation and strict reply checking; an SDK must not
bypass Adversary's provider accounting, native gates or continuing limits. The
offline proposal preserves the seed exactly and selects one registered template
ID; the host resolves its fixed instruction. Contract v002 replaces the earlier
prose-output fixture, whose original sources and replies remain retained. Its
14 focused controls and socket-blocked execution passed. The demo has no outgoing
model calls and grants no live provider route.
Optimizer searches and model-quality comparisons are deferred beyond V1.0RC.

## What would justify adoption

Keep the shared mechanism only if it removes bespoke code or catches actual
failure modes while preserving a simple input and reliable replay. Optional
runtime adoption additionally needs measured dependency/startup cost, semantic
parity and operational maintenance benefits. The offline controls cannot establish
better single-shot answers, lower model token usage or general PFP efficacy.
Any later metered comparison keeps the existing $0.05 total per-run cap, frozen
tasks and an independent judge; reaching a cap does not authorize a larger run.
