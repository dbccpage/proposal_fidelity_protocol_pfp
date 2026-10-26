# How to Play the Symbol Game

> [!IMPORTANT]
> **Canonical Symbol Game Theory Spine**
>
> The Symbol Game is the finite packet boundary between untrusted generation and Omega authority.
> A model may propose. It may emit structured material. It may even emit certificate-shaped material. It is not the certifier.
>
> \[
> \boxed{
> \mathsf{Finite\ packet\ grammar} + \mathsf{total\ verifier} + \mathsf{packet\ fidelity} + \mathsf{family\ soundness} \Rightarrow \mathsf{failure\ is\ mechanically\ enumerable,\ repairable,\ and\ terminalizable.}
> }
> \]
>
> **Authority Boundary:** Symbol Game emits verifier evidence and terminal statuses. It does not directly mint Omega authority.
>
> **Governance Rule:** symbol_game_math_spine.md is canonical. symbol_game_proof_ledger.md is archival only and non-admissible. Theory is closeable; implementation authority remains gated until conformance passes.

The Symbol Game is an audit-grade reasoning workflow. It is not an entertainment game. Its job is to force candidate claims through finite symbolic containers, typed outputs, mechanical checks, and explicit authority ceilings.

## Authority Warning

A completed run is not automatically a proof. The pipeline produces staged artifacts, validator results, evidence levels, and oracle targets. Evidence upgrades are owned by validators, mechanical evaluators, or external proof/empirical oracles.

## Core Idea

> **The Symbol Game is a finite-symbol forcing system: it compresses vague intent into declared symbols, rules, obstructions, operators, and terminal conditions before allowing prose or code generation.**

The Symbol Game works by replacing vague natural-language requests with finite symbolic regimes.

Bad request:

```text
Build me a primal-dual solver in Rust.
```

Symbol Game request:

```text
Use symbols a-z, 0-9, <, >, =.
Declare the carrier.
Declare allowed terms.
Declare allowed rewrites.
Declare the obstruction.
Declare the terminal condition.
Then derive the operator structure needed for a solver.
```

The point is to force the model into a reasoning state before it writes code. Code generation comes after symbolic compression, obstruction detection, operator selection, and validation.

The failure mode is asking an AI model to synthesize an optimizer in ordinary language. A better test is to force the problem through a tiny symbolic instruction system.

Example:

```text
lp<
max<3x+2y>
var<x,y>
ub1<x+y<=4>
ub2<x<=2>
ub3<y<=3>
nn<x>=0,y>=0>
try<x=2,y=2>
hit<10>
proof<
use<2*ub1+ub2>
derive<3x+2y<=10>
>
qed<try=opt>
>
```

Now the model is not “writing an optimizer from vibes.” It is generating a trace in a constrained algebra. That makes the failure measurable.

In this LP example:

```text
use<2*ub1+ub2>
derive<3x+2y<=10>
```

The local check asks:

```text
Does the linear combination follow?
```

The global check asks:

```text
Does this derived inequality bound the actual declared objective?
Does the candidate satisfy all original constraints?
Does the final QED claim match the declared problem?
```

Only when both are true do you get `OptimalityCertified`. Without the global check, the model could produce a valid-looking algebraic fragment that does not solve the declared problem.

> The Symbol Game is not satisfied by local validity. A trace must remain green at the global packet boundary: same problem, same protected skeleton, same terminal target, same evidence ceiling.

Terminal classifications and boundary gates for this LP example:

```text
SyntaxValid
CandidateFeasible
ObjectiveHitValid
UpperBoundCertified
OptimalityCertified
LocalStepValid
GlobalBoundaryValid
AdmissibleStep
```

Failure / violation examples:

```text
MalformedPacket
InvalidConstraintReference
InvalidLinearCombination
CandidateInfeasible
ObjectiveMismatch
UpperBoundGap
QEDRejected
BoundaryViolation
ProblemMutation
ConstraintScopeLeak
ProtectedSkeletonMutation
EvidencePromotionAttempt
```

> The Symbol Game does not ask the model to solve from prose. It forces the model to emit symbolic traces that can be parsed, replayed, and mechanically checked.

## Build

```bash
cd omega_engine/products/symbol_game
cargo build --all-targets --all-features
```

## The Pipeline

Every current mode uses these public stages:

```text
Stage 1  Compression Gate
Stage 2  Ideation
Stage 3  Audit
Stage 4  L2 Extraction
Stage 5  MSS-mu Evaluator
Stage 6  Adversarial Search
Stage 7  Countermodel Refinement
Stage 8  Evidence Plan
```

The same number appears in the CLI stage argument, YAML filename, run artifact filename, and manifest `stage_index`.

## Run Proof Mode

```bash
cargo run -j 1 --bin run_proof_pipeline -- \
  --seed "Prove LP duality for bounded polyhedra" \
  --encoding full \
  --backend http \
  --yaml-dir yaml/mode_2_proofer
```

For deterministic local testing:

```bash
cargo run -j 1 --bin run_proof_pipeline -- \
  --seed "Test seed" \
  --backend file \
  --responses-dir runs/test_fixtures \
  --yaml-dir yaml/mode_2_proofer
```

The file backend expects:

```text
runs/test_fixtures/
  stage_1.yaml
  stage_2.yaml
  stage_3.yaml
  stage_4.yaml
  stage_5.yaml
  stage_6.yaml
  stage_7.yaml
  stage_8.yaml
```

## Run Operator Mode

Operator mode proposes and tests candidate operators. An operator is not admitted merely because the LLM proposes it; admission requires contract validation, mechanical checks, and operator-lattice validation.

```bash
cargo run -j 1 --bin run_operator_tower -- \
  --domain "linear_algebra" \
  --gap "projection operator" \
  --max-iterations 3
```

## Use the Legacy Prompt CLI

The `symsys-pipeline` binary is still the manual prompt/report path.

```bash
cargo run -j 1 --bin symsys-pipeline --features legacy-pipeline -- \
  generate-prompt \
  --stage 3 \
  --input stage_2_response.yaml \
  --stage2-output stage_2_response.yaml \
  --yaml-dir yaml/mode_1_candidate_ideas_proposer
```

```bash
cargo run -j 1 --bin symsys-pipeline --features legacy-pipeline -- \
  parse-response \
  --stage 3 \
  --input stage_3_response.yaml \
  --output stage_3_report.md
```

## Output Layout

An autonomous run writes:

```text
runs/{run_id}/
  manifest.yaml
  stage_1.yaml
  stage_2.yaml
  stage_3.yaml
  stage_4.yaml
  stage_5.yaml
  stage_6.yaml
  stage_7.yaml
  stage_8.yaml
```

The manifest records the frozen seed hash, stage input/output hashes, backend name, one-based stage index, terminal status, and evidence level.

## Troubleshooting

`SYMGAME_LLM_ENDPOINT not set`: use `--backend file` or set the HTTP backend variables.

`canned response not found`: create the missing `stage_N.yaml` file for the one-based stage being requested.

`Invalid stage id`: use a stage number from `1` through `8`.

`CODE_OR_SCHEMA_FAILURE`: the YAML did not parse or a validator blocked the transition. Treat this as an engineering artifact, not evidence about the seed.
