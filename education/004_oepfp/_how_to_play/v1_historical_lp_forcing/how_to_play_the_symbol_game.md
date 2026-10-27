# how to play the symbol game

> **provenance (2026-07-24):** mined from the official archive snapshot
> `engine/.official_archive/the_symbol_game.zip`
> (`the symbol game/how_to_play_the_symbol_game.md`). historical product cli paths
> (`products/symbol_game`, legacy binaries) may be stale; live prod is
> `crates/core_symbol_game` and python orchestrator under `engine_py/core_symbol_game/`.
>
> **live theory navigation:** `007_the_symbol_game_monograph.md` +
> `007_the_symbol_game_proof_ledger.md` (paper 043 / er007). research terminal
> `openobstruction`. **authorityeffect: none.** certificate / terminal statuses are
> host routing evidence, not gtla seals and not world-truth.
>
> archive banner claimed `symbol_game_math_spine.md` as canonical — that reading is
> **superseded** for programme navigation by the 007 monograph/proof ledger pair.

---

> [!important]
> **canonical symbol game theory spine**
>
> the symbol game is the finite packet boundary between untrusted generation and omega authority.
> a model may propose. it may emit structured material. it may even emit certificate-shaped material. it is not the certifier.
>
> [
> \boxed{
> \mathsf{finite\ packet\ grammar} + \mathsf{total\ verifier} + \mathsf{packet\ fidelity} + \mathsf{family\ soundness} \Rightarrow \mathsf{failure\ is\ mechanically\ enumerable,\ repairable,\ and\ terminalizable.}
> }
> ]
>
> **authority boundary:** symbol game emits verifier evidence and terminal statuses. it does not directly mint omega authority.
>
> **governance rule:** symbol_game_math_spine.md is canonical. symbol_game_proof_ledger.md is archival only and non-admissible. theory is closeable; implementation authority remains gated until conformance passes.

the symbol game is an audit-grade reasoning workflow. it is not an entertainment game. its job is to force candidate claims through finite symbolic containers, typed outputs, mechanical checks, and explicit authority ceilings.

## authority warning

a completed run is not automatically a proof. the pipeline produces staged artifacts, validator results, evidence levels, and oracle targets. evidence upgrades are owned by validators, mechanical evaluators, or external proof/empirical oracles.

## core idea

> **the symbol game is a finite-symbol forcing system: it compresses vague intent into declared symbols, rules, obstructions, operators, and terminal conditions before allowing prose or code generation.**

the symbol game works by replacing vague natural-language requests with finite symbolic regimes.

bad request:

```text
build me a primal-dual solver in rust.
```

symbol game request:

```text
use symbols a-z, 0-9, <, >, =.
declare the carrier.
declare allowed terms.
declare allowed rewrites.
declare the obstruction.
declare the terminal condition.
then derive the operator structure needed for a solver.
```

the point is to force the model into a reasoning state before it writes code. code generation comes after symbolic compression, obstruction detection, operator selection, and validation.

the failure mode is asking an ai model to synthesize an optimizer in ordinary language. a better test is to force the problem through a tiny symbolic instruction system.

example:

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

now the model is not “writing an optimizer from vibes.” it is generating a trace in a constrained algebra. that makes the failure measurable.

in this lp example:

```text
use<2*ub1+ub2>
derive<3x+2y<=10>
```

the local check asks:

```text
does the linear combination follow?
```

the global check asks:

```text
does this derived inequality bound the actual declared objective?
does the candidate satisfy all original constraints?
does the final qed claim match the declared problem?
```

only when both are true do you get `optimalitycertified`. without the global check, the model could produce a valid-looking algebraic fragment that does not solve the declared problem.

> the symbol game is not satisfied by local validity. a trace must remain green at the global packet boundary: same problem, same protected skeleton, same terminal target, same evidence ceiling.

terminal classifications and boundary gates for this lp example:

```text
syntaxvalid
candidatefeasible
objectivehitvalid
upperboundcertified
optimalitycertified
localstepvalid
globalboundaryvalid
admissiblestep
```

failure / violation examples:

```text
malformedpacket
invalidconstraintreference
invalidlinearcombination
candidateinfeasible
objectivemismatch
upperboundgap
qedrejected
boundaryviolation
problemmutation
constraintscopeleak
protectedskeletonmutation
evidencepromotionattempt
```

> the symbol game does not ask the model to solve from prose. it forces the model to emit symbolic traces that can be parsed, replayed, and mechanically checked.

## build

```bash
cd engine/products/symbol_game
cargo build --all-targets --all-features
```

## the pipeline

every current mode uses these public stages:

```text
stage 1  compression gate
stage 2  ideation
stage 3  audit
stage 4  l2 extraction
stage 5  mss-mu evaluator
stage 6  adversarial search
stage 7  countermodel refinement
stage 8  evidence plan
```

the same number appears in the cli stage argument, yaml filename, run artifact filename, and manifest `stage_index`.

## run proof mode

```bash
cargo run -j 1 --bin run_proof_pipeline -- \
  --seed "prove lp duality for bounded polyhedra" \
  --encoding full \
  --backend http \
  --yaml-dir yaml/mode_2_proofer
```

for deterministic local testing:

```bash
cargo run -j 1 --bin run_proof_pipeline -- \
  --seed "test seed" \
  --backend file \
  --responses-dir runs/test_fixtures \
  --yaml-dir yaml/mode_2_proofer
```

the file backend expects:

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

## run operator mode

operator mode proposes and tests candidate operators. an operator is not admitted merely because the llm proposes it; admission requires contract validation, mechanical checks, and operator-lattice validation.

```bash
cargo run -j 1 --bin run_operator_tower -- \
  --domain "linear_algebra" \
  --gap "projection operator" \
  --max-iterations 3
```

## use the legacy prompt cli

the `symsys-pipeline` binary is still the manual prompt/report path.

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

## output layout

an autonomous run writes:

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

the manifest records the frozen seed hash, stage input/output hashes, backend name, one-based stage index, terminal status, and evidence level.

## troubleshooting

`symgame_llm_endpoint not set`: use `--backend file` or set the http backend variables.

`canned response not found`: create the missing `stage_n.yaml` file for the one-based stage being requested.

`invalid stage id`: use a stage number from `1` through `8`.

`code_or_schema_failure`: the yaml did not parse or a validator blocked the transition. treat this as an engineering artifact, not evidence about the seed.
