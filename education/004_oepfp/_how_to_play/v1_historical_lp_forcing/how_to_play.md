# How to Play the Symbol Game

**Version:** v1 historical LP-forcing (circa 2026-05/06)
**Audience:** a human who will type a packet
**AuthorityEffect:** None
**Status:** Player guide recovered from the 2026-05/06 LP-forcing era. Not a theorem. Not an imprimatur. Not the 2026-09 packet-iteration guide.

> **Historical banner.** This is the 2026-05/06 play recipe: finite-symbol forcing, an `lp<...>` packet you can type by hand, a local check, a global check, and named terminals. Cargo paths printed in the archive (`omega_engine/products/symbol_game`, `run_proof_pipeline`, `symsys-pipeline`) **may be stale** and are **not** a live play recipe. **AuthorityEffect is None.** A completed run is **not** a proof. Certificate-shaped output is host routing evidence, not world-truth.

> This folder is **not** `v2_modern_2026-09_packet_iteration`. v2 is five public Symbol Packet Iteration stages plus internal eight-stage YAML modes. This v1 guide is one ad-hoc LP packet. Do not merge the two.

---

## 1. What you are playing

The Symbol Game is an audit-grade reasoning workflow. It is not an entertainment game.

Its job is to force a candidate claim through a **finite symbolic container** before anyone is allowed to trust prose, code, or a self-awarded QED.

The archive how-to-play stated the core idea as:

> The Symbol Game is a finite-symbol forcing system: it compresses vague intent into declared symbols, rules, obstructions, operators, and terminal conditions before allowing prose or code generation.

You play by **typing a packet**. A model may fill holes in that packet. A **host** parses the packet, replays the arithmetic, and emits a terminal. The model is not the referee.

### 1.1 The one loop

1. Declare a finite alphabet and a packet family.
2. Write the problem as a terse `tag<...>` payload (in this version, `lp<...>`).
3. The model proposes a candidate: matrices, a primal point, a dual combination, a `hit`, a `qed`.
4. The host independently checks the claim over rational numbers (Q).
5. The host emits exactly one honest terminal. You do not promote the evidence yourself.

If step 4 is skipped, you are not playing the Symbol Game. You are reading an LLM.

### 1.2 Authority warning

A completed run is not automatically a proof. The pipeline produces artifacts, validator results, evidence levels, and oracle targets. Evidence upgrades are owned by validators, mechanical evaluators, or external proof/empirical oracles.

A model may propose. It may emit structured material. It may even emit certificate-shaped material. **It is not the certifier.**

This recovery guide does not mint Omega authority. AuthorityEffect stays None.

---

## 2. Finite-symbol forcing (the original move)

The game works by replacing a vague natural-language request with a finite symbolic regime.

**Bad request:**

```text
Build me a primal-dual solver in Rust.
```

**Symbol Game request:**

```text
Use symbols a-z, 0-9, <, >, =.
Declare the carrier.
Declare allowed terms.
Declare allowed rewrites.
Declare the obstruction.
Declare the terminal condition.
Then derive the operator structure needed for a solver.
```

The point is to force a reasoning state **before** anyone writes code. Code generation, if it happens at all, comes after symbolic compression, obstruction detection, operator selection, and validation.

The failure mode of the era was asking a model to synthesize an optimizer in ordinary language. The better test is to force the problem through a tiny symbolic instruction system so that failure is measurable.

### 2.1 Historical substrate (not this version's play alphabet)

An older MSS-N grammar note (`mss_n_grammar_000.md`) takes genesis to be the empty distinction `<>` and a later up-lift `op<<0><><0><1>>`. That substrate is **historical**. This v1 guide does **not** treat alphabet cardinality as live MSS-0 law. The play alphabet below is the LP packet alphabet of 2026-05/06, not a tower theorem.

---

## 3. What you type versus what the host sees

JSON packets are implementation envelopes. Symbol payloads are the constrained interface the model is allowed to write. Every terse payload must compile into a typed internal packet before validation.

The design split of the era:

| Layer | Who uses it | What it looks like |
|---|---|---|
| Human / spec | You, docs, validators | JSON, markdown, Rust traits, schemas |
| LLM packet | The model | Tiny symbolic grammar (`lp<...>`) |
| Internal | The host | Parsed AST / typed packet / validation structs |

Pipeline flow:

```text
prose -> envelope -> symbol payload -> AST -> validation -> terminal
```

The model operates at the **symbol payload** layer. The host handles the envelope, validation, and terminalization.

For each packet family the era asked for five declarations: alphabet, grammar, local rules, global boundary, terminal symbols.

---

## 4. Worked example: type this LP packet

This is the original Core Idea example. Type it. Do not paraphrase it into prose and then trust the answer.

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

Now the model is not writing an optimizer from vibes. It is generating a trace in a constrained algebra.

### 4.1 Same packet, JSON envelope (host/spec layer)

The spec-side envelope for the same problem looks like this (from the terse-payload note):

```json
{
  "kind": "lp_primal_dual",
  "sense": "max",
  "objective": "3x+2y",
  "constraints": ["x+y<=4", "x<=2", "y<=3", "x>=0", "y>=0"],
  "candidate": {"x": 2, "y": 2}
}
```

You do **not** ask the model to be the JSON schema. The host owns the envelope. The model is asked for the `lp<...>` payload (and, in some host scripts, the primal/dual numbers that the host will recompute).

### 4.2 Even tighter payload

```text
lp<max<3x+2y>;ub<x+y<=4,x<=2,y<=3>;nn<x,y>;try<2,2>;use<2u1+u2>;hit<10>;qed>
```

Same game, fewer tokens. Still not a proof until the host replays it.

### 4.3 Hand arithmetic you should be able to check

Declared program (maximize):

- objective `Phi = 3x + 2y`
- `x + y <= 4`, `x <= 2`, `y <= 3`, `x >= 0`, `y >= 0`

Candidate `try<x=2,y=2>`:

- feasibility: `2+2 = 4 <= 4`, `2 <= 2`, `2 <= 3`, both nonnegative
- objective: `3*2 + 2*2 = 10`, which matches `hit<10>`

Local derivation `use<2*ub1+ub2>`:

- `2(x+y <= 4) + 1(x <= 2)` gives `3x + 2y <= 8 + 2 = 10`
- that is exactly `derive<3x+2y<=10>`
- nonnegative combination of declared constraints; no undeclared inequality

If the host recomputes over Q and finds primal value = derived upper bound = 10, the duality gap is 0. Gap zero is **evidence for this packet**, not a theorem about linear programming in general, and not a license to skip the global check.

---

## 5. Local check versus global check

In this LP example:

```text
use<2*ub1+ub2>
derive<3x+2y<=10>
```

**The local check asks:**

```text
Does the linear combination follow?
```

**The global check asks:**

```text
Does this derived inequality bound the actual declared objective?
Does the candidate satisfy all original constraints?
Does the final QED claim match the declared problem?
```

Only when **both** are true do you get `OptimalityCertified`. Without the global check, the model could produce a valid-looking algebraic fragment that does not solve the declared problem.

> The Symbol Game is not satisfied by local validity. A trace must remain green at the global packet boundary: same problem, same protected skeleton, same terminal target, same evidence ceiling.

That is the whole skill of playing: **local green is not global green.**

Host-side LP checks of the same era (packet-family spec) say the same thing in validator language:

**Local:** dimension of `A`, `b`, `c`, `x`, and `y`; primal feasibility; dual feasibility; primal and dual objective values; duality gap within declared tolerance.

**Global / boundary:** rational or decimal precision policy; reject a tolerance looser than the packet budget; reject unsupported constraint orientation; bound matrix size; no problem mutation; no protected-skeleton mutation; no evidence-promotion attempt.

---

## 6. The host verifies over Q

Folded from the plain-English host-verifies guide of the same era.

The model writes down the matrices, vectors, and primal/dual values. The host script **independently** calculates the math. If the model claims a solution value `Phi = 2`, it must supply a dual witness `y*` such that `<y*, omega> = 2`. If the numbers do not balance, the host rejects the claim. The model does not get a vote.

In the worked packet above the same rule is: claimed `hit<10>` plus `qed<try=opt>` is acceptable only if the host's own Q arithmetic sees a feasible candidate and a zero gap against a legal dual combination of the **declared** constraints.

Some host scripts of the era emitted a `HOST_VERDICT.md` with exact pass/fail checks labeled G2 through G7 and a remaining-error list (`remaining_delta`). That file is a **host artifact**. It is not a proof ledger and not a GTLA seal. This guide does not invent the G2–G7 definitions; it only records that the host, not the model, wrote the verdict.

**What this supports:** host–model separation and falsifiable checks on declared finite complexes over Q.

**What this does not support:** unverified model self-trust, continuum mathematics, or the slide from a green run to an undeclared theorem.

**Narrowest defensible claim of this version:** the Symbol Game replaces prose trust with host-owned Q-arithmetic checks on a declared finite packet. It does not make the model smarter. It makes the model's failures enumerable, replayable, and terminalizable **relative to that packet's verifier**.

---

## 7. Terminal and failure vocabulary

Two vocabularies sat next to each other in 2026-05/06. Keep them distinct. Neither is minted by the model.

### 7.1 Packet-level LP gates (from the original how-to-play)

Terminal classifications and boundary gates for the LP example:

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

You want `LocalStepValid` **and** `GlobalBoundaryValid` before `OptimalityCertified` is even discussable. `AdmissibleStep` in the era's wording meant local-green **and** global-green relative to the declared verifier, not that the model felt done.

### 7.2 Failure / violation names (from the original how-to-play)

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

May 2026 validator-catalog names that match the same LP family include `QedContradiction` (gap 0 but the packet refused to say Certificate / said `qed<try=subopt>`), `TerminalStatusMismatch_LP` (positive gap but the packet claimed Certificate), `CandidateInfeasible`, `DimensionMismatch`, `InvalidLinearCombination`, `ObjectiveMismatch`, and `UpperBoundGap`. A catalog name is a **host error code**. It is not an extra packet family.

### 7.3 LP alphabet and payload terminals

```text
LP alphabet:
  lp max min var ub lb eq nn try use derive hit qed fail

LP terminals:
  qed<opt>
  fail<infeasible>
  fail<gap>
  fail<bad_bound>
  oracle<lp_solver>
```

`qed<...>` in the payload is a **claim**. The host may override it.

### 7.4 Host terminalizer (four statuses; validator is authority)

Contemporaneous May 2026 host policy: the terminalizer returns **exactly one** of four statuses. The model is a candidate generator. It may emit a terminal claim. The host verifier is the authority and may override.

| Status | Player meaning |
|---|---|
| `Certificate` | Host replayed the packet and the declared checks passed, **scoped to that verifier**, not to external semantic truth. |
| `Refusal` | Grammar, type, law, budget, or boundary is broken in a way the host will not repair. |
| `Repair` | Close enough for a structured repair payload; bounded iterations (era default: 2), then Refusal or OracleNeeded. |
| `OracleNeeded` | Host cannot verify locally; pause and name the oracle. Not an excuse to skip a check the host already has. |

Hard rules of that registry:

- LLM terminal claim is advisory.
- Evidence promotion by the model is forbidden.
- No conversational padding in the packet response.
- Validator is authority, not the LLM.
- An LLM-emitted `Certificate` that has not passed host validation is an unverified claim, not a certificate.

Empirical anti-patterns already named in that era: Certificate with positive gap; Certificate for a suboptimal point; `qed<try=subopt>` when the gap is already zero (repair the **terminal**, keep the math).

---

## 8. How a turn actually goes

Play this version as a human typing a packet, not as a cargo tutorial.

1. **Pick the family.** This guide's family is `lp_primal_dual`. Other families existed (code-rewrite, operator classification, cochain, and more). They are not this version's play recipe.
2. **Write the payload** in the `lp<...>` alphabet. Declare objective, variables, constraints, candidate, proof combination, hit, and qed.
3. **Do not** attach a fluent explanation and call it evidence.
4. **Hand the payload to a host** that owns the JSON/schema envelope. The host parses, hashes the raw text, replays local steps, checks the global boundary, and terminalizes.
5. **Read the host terminal**, not the model's mood. If the host says Repair, fix the named error. If it says Refusal, stop. If it says OracleNeeded, you need a solver or prover the host does not have. If it says Certificate, you have **packet-scoped** host evidence. You still do not have a proof of an undeclared theorem.
6. **Never** let the model raise its own evidence ceiling.

A sibling payload (not the LP game, shown only so the three-tier split is visible):

```text
rewrite<
target<UserId>
skeleton<
  preserve_pub_sig: true
  preserve_error: true
  preserve_vis: true
  no_unsafe: true
  no_deps: true
  no_panic: true
>
license<PartialityLicense, EncapsulationLicense>
lhs<...>
rhs<...>
qed<compiles, api_preserved>
>
```

That is a different family with a protected skeleton and a license lattice. Do not mix its terminals into the LP example.

---

## 9. What this version is not

### 9.1 Not the original eight-stage YAML cargo pipeline

The archive how-to-play **appended** an eight-stage industrial pipeline after the LP Core Idea:

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

plus `cargo` commands against `omega_engine/products/symbol_game` (`run_proof_pipeline`, `run_operator_tower`, `symsys-pipeline`).

**Those eight stages are not the original playable game.** The playable unit in this version is the tiny checked `lp<...>` object: packet, local check, global check, terminal. The eight-stage YAML overlay is a later crate-and-contract machine. It is recorded here so you can recognize it in the dump. It is **not** how you play v1. It is **not** a claim that those cargo paths still exist. v2 (2026-09) is the place for live YAML stage counts, and even there the **public** mode is five-stage Symbol Packet Iteration, not public stages 1–8.

### 9.2 Do not conflate three artifacts

A 2026-06-15 product-readiness note warned that three different objects shared the name Symbol Game:

1. A Rust vertical slice that parses `lp<...>` (one family).
2. A Python eight-stage MVP / testbed that did **not** call that crate.
3. A research spine and paper series.

Conflating them was the readiness failure mode. This v1 guide is the **player-facing LP-forcing recipe**. It is not a claim that the Python eight-stage service is the game, and it is not a claim that the research spine is a CLI.

### 9.3 Historical crate paths (archaeology only)

Recorded, not recommended as live commands:

- Archive how-to-play: `cd omega_engine/products/symbol_game` then `cargo build --all-targets --all-features`.
- 2026-07-24 archive-mined wrapper: those product-CLI paths may be stale; then-described prod was `crates/omega_symbol_game` and a Python orchestrator under `omega_engine_py/omega_symbol_game/`.
- File-backend fixtures `runs/test_fixtures/stage_1.yaml` through `stage_8.yaml` belong to the overlay, not to the LP packet.

If those paths are missing on the tree you are holding, that is expected. Absence of a binary does not refute the LP packet rules.

### 9.4 Not a live theory-spine upgrade

This version's **era pointer** is `symbol_game_math_spine.md` (the archive how-to-play called it canonical and called `symbol_game_proof_ledger.md` archival). A 2026-07-24 provenance banner on a hashed wrapper later said that spine-canonicality reading was **superseded for programme navigation** by Paper 043 / the 007 monograph and proof ledger, research terminal OpenObstruction, AuthorityEffect none. **v2** is where that later pointer belongs. This v1 file keeps the 2026-05/06 pointer on purpose so the two how-to-play versions disagree.

Quoted archive box (historical wording, not a seal this guide mints):

> Finite packet grammar + total verifier + packet fidelity + family soundness implies failure is mechanically enumerable, repairable, and terminalizable.

Read it as a **programme slogan of the era**, scoped to a declared finite family and a host verifier. It is not a proof that every future family is sound, and it is not Omega authority.

---

## 10. Player checklist

Before you call a turn done:

- [ ] The problem is a declared `lp<...>` packet, not a paragraph.
- [ ] Alphabet is the LP alphabet, not unrestricted natural language.
- [ ] Local combination replays (no `InvalidLinearCombination`).
- [ ] Candidate meets **original** constraints (no `CandidateInfeasible`, no `ProblemMutation`).
- [ ] Derived bound actually bounds the declared objective (no `UpperBoundGap`).
- [ ] `hit` matches the host's Q objective (no `ObjectiveMismatch`).
- [ ] `qed` matches the host gap (no `QEDRejected` / `QedContradiction` / `TerminalStatusMismatch_LP`).
- [ ] Host, not model, emitted the terminal.
- [ ] You did not promote evidence.
- [ ] You did not treat the run as a proof.

---

## 11. Sources

Walked paths and merge rules live in `SOURCES.md` in this folder. Primary dump stem: `symbol_game_docs/how_to_play_the_symbol_game.md`. Hashed wrappers are sources, not dest filenames.
