# How to Play the Symbol Game (v2 — Modern Packet Iteration, 2026-09)

**AuthorityEffect:** None  
**Policy:** SPK-002 (`symbol_packet_iteration.v0.2`)  
**Audience:** a human (or model) who will emit YAML packets into a host loop  
**Machine contracts:** `2_how_to_play/how_to_play_yaml/` (not this file)  
**Theory pointer:** Paper 043 — *The Symbol Game: Finite Packetization, LGGR, and the Authority Firewall*  
**Live crate:** `omega_symbol_game`

This is a player guide. It is not a proof, not a certificate, and not Omega authority. A finished run is staged YAML plus host terminals. Treat a completed run as a proof and you have already lost the game.

YAML stays YAML. Do not paste the stage templates into a chat and call that the contract. Play *over* the hashed files under `how_to_play_yaml/`.

---

## 0. What this version is

The modern public game is **Symbol Packet Iteration** under policy **SPK-002**.

You do not type a free-form essay and hope. You do not type an `lp<…>` trace and call it the whole game (that family still exists on the crate; it is not the public loop). You emit **one YAML artifact per stage**. The host parses it, checks the schema, checks local/global boundary fields, and either injects it into the next stage or stops with a typed refusal.

The loop is recursive on purpose. Stage 5 must synthesize a `next_prompt`. The public engine is built to produce the *next packet*, not a final answer you can frame on a wall.

**Authority warning.** A model may propose. It may emit certificate-shaped YAML. It is not the certifier. Evidence upgrades and terminal statuses are owned by the host (parser, evaluators, oracles). `AuthorityEffect` on this guide, on the SPK-002 controller, and on the dest crate bins is **None**.

---

## 1. Three disagreements with v1 (required)

v1 (historical LP-forcing, May 2026) and this file must not be paraphrases of each other. They disagree on the load-bearing knobs:

| Knob | v1 (historical) | v2 (this file) |
| --- | --- | --- |
| Public stage count | Eight public stages: Compression Gate through Evidence Plan | **Five** public stages under SPK-002: Seed Packet → Symbol Expansion → Descent Audit → Adversarial Rounds → Terminal Prompt Synthesis. Eight stages remain **internal** for Mode 2 (proofer) and Mode 5 (operator) |
| Theory-spine pointer | `symbol_game_math_spine.md` is canonical; the proof ledger is archival | **Paper 043** is the theory pointer (finite packetization, LGGR, authority firewall). math_spine is *not* canon for this version. dest papers/032 (PO-032) is a different dest monograph and is not this pointer |
| Live crate / CLI | `cd omega_engine/products/symbol_game` then `run_proof_pipeline` / `run_operator_tower` / `symsys-pipeline` | Dest crate **`omega_symbol_game`** (`code/rust/`). Current bins: `run_sg`, `omega_symbol_admit`. The v1 cargo paths are not this crate's current bins |

If a document still says the public convention is Stage 1 Compression Gate through Stage 8 Evidence Plan, it is describing the **internal** 8-stage YAML (or the v1 architecture banner). It is not describing SPK-002 public play.

The historical 8-stage binaries (`run_proof_pipeline`, `run_operator_tower`, `symsys-pipeline`) and the path `omega_engine/products/symbol_game` are the v1 architecture story. Do not treat them as live commands in this recovery tree.

---

## 2. Roles (who may do what)

| Role | May | May not |
| --- | --- | --- |
| You / the model | Propose YAML matching the stage schema; name ambiguities, attacks, next tests | Upgrade `evidence_level`; mint `Certificate`; edit templates after the seed is frozen; wrap YAML in markdown fences |
| Host (`omega_symbol_game`) | Parse, refuse, replay, inject Stage N into Stage N+1, emit terminals | Treat producer `verified: true` as a certificate |
| YAML contracts | Define schemas, enums, stop conditions, preamble | Change mid-run (SGI-001: hash mismatch is `PROCESS_OBSTRUCTION`) |
| Paper 043 | State the finite-packet / LGGR / firewall claims this loop is playing under | Be replaced by a math_spine banner or by dest PO-032 inside a player guide |

Division of labor from the 2026-09 host contract (`symgam_new_intructions.md`, status **DRAFT DESIGN NOTE**, not doctrine):

- Outside parties may supply a challenge, adversarial attacks, and (if the host contract is complete) an outside bet.
- The run must not silently import an outside vocabulary, carrier, or calculus.
- Producer prose is testimony. A positive terminal is licensed only by host-side validation and replay.

Useful design rule, quoted as a play constraint not as metaphysics:

> An unpriced rewrite is a smuggled axiom.

---

## 3. The public board: five stages (SPK-002)

**Mode id:** `symbol_packet_iteration`  
**Controller:** `how_to_play_yaml/mode_1_symbol_packet_iteration/controller.yaml`  
**Config:** `how_to_play_yaml/symsys_config.yaml` (`mode: symbol_packet_iteration`, `max_round_count: 5`)  
**Backend runtime (from the controller):** `rust_crate: omega_symbol_game`, `public_stage_count: 5`, `internal_stage_count: 8`

Every public artifact must carry:

- `derived_under_policy: SPK-002`
- `schema_version: symbol_packet_iteration.v0.2`
- YAML only — **markdown code blocks forbidden**
- a `boundary_check` with `local_valid`, `global_valid`, `boundary_violation`, and a `preserved` list
- iteration metadata (`run_id`, packet ids, `depth`, `max_depth: 5`)

Hard laws (controller; these are play rules, not slogans):

1. Packet shape forgets semantic truth. Packetization preserves declared fidelity and emits no authority.
2. Local green does not imply global green.
3. The model may propose but never certifies.
4. No stage self-promotes evidence.
5. Depth does not raise the expressive ceiling. Five recursive rounds are still the same grammar.

Stop conditions: `malformed_yaml`, `missing_required_field`, `forbidden_language_unscoped`, `terminal_prompt_missing`, `no_adversarial_rounds`.

Quality gates: schema valid; adversarial rounds complete; `next_prompt` present; forbidden language scoped. Failures are typed refusal or repair-required, not a prose apology.

`S(n)` is **symbolic context level**, not a pipeline stage number, not an evidence level, and not a proof status. Completing stages 1–5 does not lift `S(n)`.

The 38-token wire that the controller preamble still recites (a–z, 0–9, `<`, `>`, `<>`) is a **prompt-contract clause**. It is not live MSS-0 law. Alphabet-count minimality was withdrawn. Winning is not “I used 38 symbols.”

### Stage 1 — Seed Packet

**Files:** `stage_1_seed_packet.yaml`  
**Input:** raw user seed  
**Output:** `seed_packet`  
**Absorbs (internal names):** compression_gate  
**Families:** prompt_obstruction, claim_decomposition, json_schema

Your job: strip filler, name the question, type every seed claim with an evidence label, map vocabulary onto the allowed layers, and run a local/global boundary check *without mutating* the seed question or the policy boundary.

Allowed layers: `root_occurrence`, `representability`, `authority`, `repeatable_engagement`, `representation_layer`, `derived_structure`, `unknown`.

Seed evidence labels (stage schema): `F0`, `F1`, `DESIGN`, `CONJECTURE`, `OPEN`, `INTERPRETIVE`, `PROVEN_UNDER_ASSUMPTIONS`. Labeling a claim `PROVEN_UNDER_ASSUMPTIONS` does not make it proved. It records a claim type. The host still owns promotion.

Forbidden unscoped words include: supports, enforces, mathematically verifies, structurally, true intelligence, impossible, domain-wide, exact, perfectly, explicitly, by direct inspection, simply, merely, adversarial.

Packet id shape: `SPK-SEED-…`. Parent is null. Next is `SPK-EXP-…`. Depth 1 / 5.

If the seed is poetry with no mechanical equality test, you are not in public Mode 1 anymore — that refusal lives on the **internal** compression gate (Mode 2/5 Stage 1: `WORD_PROBLEM_UNDECIDABLE`). Public Stage 1 still discards narrative filler and must not smuggle a solved word-problem.

### Stage 2 — Symbol Expansion

**Files:** `stage_2_symbol_expansion.yaml`  
**Input:** seed packet  
**Output:** `symbol_expansion_packet`  
**Absorbs:** ideation, L2_extraction  
**Families:** typed_ast, operator_classification, cochain_obstruction, json_schema

Expand the seed into candidate **models** and **primitives**. Name hidden assumptions (target/source, codomain, observer, equality). Score `model_bias_risk`. List `missing_models`. Do not praise models. Do not claim completeness.

Each model carries feasibility (`High|Medium|Low`), an unresolved assumption, a hygiene audit, declared primitives, and hidden assumptions.

Depth 2 / 5. Next packet `SPK-AUD-…`.

### Stage 3 — Descent Audit

**Files:** `stage_3_descent_audit.yaml`  
**Input:** expansion packet  
**Output:** `descent_audit_packet`  
**Absorbs:** audit, MSS_mu_evaluator  
**Families:** evidence_routing, response_obstruction, cochain_obstruction

Audit against the three-layer ontology in the controller preamble:

- Layer 1: root occurrence (the obstruction itself, if admitted)
- Layer 2: representability (carrier, support, addressability)
- Layer 3: authority (witnessability, repeatability, terminals, preservation laws)

Do **not** use binary true/false as primitive status. Use exactly one of: `derived`, `presupposed_by_current_formalism`, `candidate_primitive`, `co_arising`, `representation_layer_only`, `authority_layer_condition`, `repeatable_engagement_condition`, `unknown`.

Emit `narrowest_defensible_thesis`, `evidence_scope.supports` / `does_not_support`, per-primitive descent paths, and a confidence block (`low|medium|high` plus reason and failure_mode). Confidence is not evidence.

Depth 3 / 5. Next packet `SPK-ADV-…`.

### Stage 4 — Adversarial Rounds

**Files:** `stage_4_adversarial_rounds.yaml`  
**Input:** descent audit  
**Output:** `adversarial_rounds_packet`  
**Absorbs:** adversarial, countermodel_refinement  
**Families:** claim_decomposition, response_obstruction, response_repair

Six **mandatory** rounds. Missing Round F is a host refusal (`symbol_packet_iteration_e2e` names `round_f_depth_expressivity`).

| Round | Attack |
| --- | --- |
| A Formalism | Smuggled carrier, type, witness, codomain, equality, observer |
| B Authority | Terminal/proved talk without a descent path |
| C Prompt-bias | Framing, over-description, emotional tilt |
| D Product | Does this help someone write Lean or Rust? |
| E Next-prompt | Strategic pivot; required next test |
| F Depth/expressivity | New structure, or more wrapping at the same `S(n)`? What lift, if any, is *required* (not licensed)? |

Every round: `attack`, `severity` (`P0|P1|P2|P3`), `survives_attack` (`true|false|partial`), plus the round's extra fields (obligations, unverified claims, biases, user_value, required_next_test, required_lift).

A required lift in Round F is a **trigger**, not a license. Writing `S(n)→S(n+1)` in YAML does not lift anything.

Depth 4 / 5.

### Stage 5 — Terminal Prompt Synthesis

**Files:** `stage_5_terminal_prompt_synthesis.yaml`  
**Input:** seed + audit + adversarial packets  
**Output:** `terminal_symbol_packet`  
**Absorbs:** evidence_plan  
**Families:** prompt_rewrite, evidence_routing, json_schema

Assemble one machine-consumable packet. Keep rounds A–F nested (do not flatten). Carry `self_critique` (strongest objection, strongest repair, remaining open problem, false-authority risks). Emit `next_prompt` and `next_tests`.

Stage-5 schema ceilings the **model** may fill:

- `evidence_level: F0|F1` only
- `authority_ceiling: ShapeOnly|LocalReplay|BoundaryChecked` only
- `terminal_status` from the *synthesis* enum: `continue`, `refined`, `blocked`, `refused`, `no_rule`, `budget_unknown`, `ready_for_mechanization`, `ready_for_paper_patch`

The dest e2e runner **refuses**:

- `derived_under_policy: SPK-001` (must be SPK-002)
- missing Round F
- `evidence_level: F2` (self-promotion)
- `authority_ceiling: EmpiricalOracleRequired` (self-promotion)

So: F2 and F3 exist on the public ladder as *host* grades. You do not type them in Stage 5. `EmpiricalOracleRequired` exists on the controller ceiling list as a *named later need*. You do not assign it to yourself. If you need an external checker, the honest packet move is a host `OracleNeeded` / synthesis `ready_for_mechanization`, not a self-written empirical ceiling.

Depth 5 / 5. `next_prompt` is the next seed if the host continues (`max_round_count: 5`).

---

## 4. How to play one public round

1. **Freeze.** Hash the seed and every template you will use (`controller.yaml`, five stage files, `symsys_config.yaml`, integrity contract). After this point, editing a template is `PROCESS_OBSTRUCTION` (SGI-001). Humans do not inject candidates after the seed.
2. **Pick the public mode.** `symbol_packet_iteration` / SPK-002. Do not start in `mode_1_candidate_ideas_proposer` and call it v2 Mode 1 — that directory is **SPK-001** eight-stage.
3. **Host prepends** `controller.yaml` to Stage 1.
4. **You emit YAML only** matching `response_schema`. No markdown fences. No second YAML document. No unknown fields (`symsys_config.yaml` validation flags).
5. **Host validates** before Stage 2. Malformed output stops the run (`CODE_OR_SCHEMA_FAILURE` if the parser itself breaks; realization refusal if policy/schema fails).
6. Repeat through Stage 5. Stage N+1 input = Stage N output + frozen templates + frozen controller. Nothing else.
7. Read `next_prompt`. Either halt on a host terminal or feed it back as the next seed, incrementing depth, until `max_depth` / `max_round_count`.
8. **Do not** upgrade evidence in prose, by multi-model agreement, or by “the five stages completed.”

Replay rule: Stage transitions must be reproducible from the frozen inputs. Side-channel paste from a chat window is contamination.

---

## 5. Evidence levels (public F0–F3)

Public SPK-002 controller lists `F0`–`F3`. Internal 8-stage controllers also mention `F4` (independently reproduced). F4 is an **evaluator-scope cap** on the internal evidence planner, not a public SPK-002 self-grade.

| Level | Meaning (8-stage controller wording) | Who may assign it |
| --- | --- | --- |
| F0 | Unverified idea | Default on ideation / seed |
| F1 | Internally consistent | Audit-shaped host acceptance of packet consistency; Stage 5 may *claim* F0 or F1 only |
| F2 | Structurally validated | Mechanical evaluator / host — **not** Stage 5 YAML |
| F3 | Mechanically verified within verification scope | Formal/runtime oracle named by an evidence plan — **not** the LLM |
| F4 (internal only) | Independently reproduced | Independent reproduction oracle (O5). Not a public SPK-002 field |

Evaluator scope (internal controllers; still the right play discipline):

- `cargo test` promotes implementation behavior, not mathematical truth.
- A computer-algebra check promotes symbolic computation, not empirical reality.
- Lean/Coq/Isabelle promote theorem validity relative to stated axioms.
- Reference checks support provenance, not proof.
- Confidence scores are not evidence.

Internal Stage 8 evaluator kinds and caps:

| Kind | Role | Cap |
| --- | --- | --- |
| O0 | No evaluator | F0 only |
| O1 | Reference / provenance | at most F1 |
| O2 | Runtime implementation test | implementation evidence only |
| O3 | Symbolic computation | symbolic-computation evidence only |
| O4 | Formal proof | formal-theorem evidence relative to stated axioms |
| O5 | Independent reproduction | reproduction evidence (the F4 slot on the internal ladder) |

An evidence plan **names** an evaluator. It does not run the oracle and it does not license a lift.

Authority ceilings (controller enum): `ShapeOnly`, `LocalReplay`, `BoundaryChecked`, `ExternalOracleRequired`, `EmpiricalOracleRequired`.

`omega_symbol_admit` admits only `cochain_obstruction` and `code_rewrite` onto a **ShapeOnly** receipt with `authority_effect: None`, and refuses trailing prose / self-certification. That bin is not the five-stage loop; it is a ShapeOnly admission gate.

---

## 6. Terminals (do not mix the enums)

There are several terminal vocabularies. Mixing them is how players launder a Continue into a Certificate.

### 6.1 Host packet terminals (SPK-002 controller)

These are the public play terminals this guide must teach:

| Terminal | Meaning |
| --- | --- |
| **Certificate** | Host checks passed **within declared scope**. Not Omega authority. Not a theorem of Paper 043 merely because the YAML parsed |
| **Refusal** | Grammar, type, law, budget, or boundary violation |
| **Repair** | Close enough for a deterministic repair; not a silent success |
| **OracleNeeded** | An external prover/solver/oracle is required; the model does not become that oracle |
| **Continue** | Loop: consume `next_prompt`; depth remaining |
| BudgetUnknown | Finite search ended before exhaustion |
| NoRule | No admitted rule covers the move |

`omega_symbol_admit` requested-terminal subset is Certificate / Refusal / Repair / OracleNeeded (no Continue). Continue belongs to the SPK-002 iteration loop.

### 6.2 Stage-5 synthesis field

The YAML key `terminal_status` in Stage 5 is a **synthesis label** (`continue|refined|blocked|refused|…`). Filling `ready_for_paper_patch` does not patch the paper. Filling `continue` does not force the host to Continue.

### 6.3 Process-integrity terminals (SGI-001)

`symbol_game_integrity_contract.yaml` (`contract_id: SGI-001`) is about whether the *run* is evidence at all:

- `CANDIDATES_GENERATED` — F0 candidates for downstream audit
- `THEORY_STRAIN_DETECTED` — tension, not refutation
- `THEORY_REFUTATION_CANDIDATE` — a specific testable “the theory is wrong” claim (the schema must allow this; suppressing it is itself obstruction)
- `PROCESS_OBSTRUCTION` — mid-run patch, human candidate injection, prompt/schema bias; **debugging artifact only**
- `CODE_OR_SCHEMA_FAILURE` — CLI/parser/template failure
- `LIFT_REQUIRED` — missing certified structure; specifies what is missing
- `BUDGET_UNKNOWN` / `REFUSED` — valid process outputs with reasons

SGI-001 valid clean outcomes are only: (1) theory strain or refutation candidate, (2) candidate idea with required tests (F0, named evaluator, named falsifier), (3) typed process/code/schema failure. Anything else is noise. Discard it.

Anti-rabbit rule: no physics-group / cosmology / consciousness / speculative-bridge realization targets in the core spec. Those belong in a separate realization ledger, not in a winning packet.

### 6.4 Host-enforced FW-* (2026-09 overlay)

From `symgam_new_intructions.md` (draft; host must actually parse and replay or this is theatre):

| Code | Meaning |
| --- | --- |
| FW-MOVE | Unlisted rewrite, missing soundness basis, or out-of-scope application |
| FW-CARRIER | Undeclared member, codepoint mismatch, digest mismatch |
| FW-OP | Undeclared operation verb |
| FW-REPLAY | Positive terminal depends on a row the host did not re-derive |
| FW-SCOPE | Bounded result promoted beyond declared carrier or bound |
| FW-LEAD | Pre-registration leaks the expected result into the run |
| FW-CHAIN | A prior receipt treated as stronger than its own scope |

A producer-authored `verified: true` is not a certificate. Receipts are dual-column: `producer_claimed_valid` versus `host_rederived`.

Closed op set in that draft glyph calculus: `PROVE`, `SHOW`, `DECIDE`, `EXHAUST`, `REDUCE`, `LAND`, `PIN`, `REFUSE`, `OPEN`. Every ledger row begins with exactly one declared op. A declared instance does not license a general rewrite theorem.

Required prompt surfaces in that draft (textual compliance is not enforcement): `[SYSTEM]`, `[K: CARRIER]`, `[VOCABULARY]`, `[GLYPH CALCULUS]`, `[LAWS / AXIOMS]`, `[REFUSALS]`, `[D: ACTIVE DEMAND]`, `[TAU]`.

This overlay does **not** make a language model deterministic, alter attention, or turn tokens into a physical object. If a packet claims that, refuse it.

---

## 7. Packet families (public registry)

`packet_family_registry.yaml` (sources tagged 040c; terminals Certificate / Refusal / Repair / OracleNeeded, json_schema Certificate / Refusal):

| Family | Stages |
| --- | --- |
| prompt_obstruction | 1, 4 |
| claim_decomposition | 1, 3, 4 |
| evidence_routing | 3, 5 |
| prompt_rewrite | 5 |
| response_obstruction | 3, 4 |
| json_schema | 1–5 |

A family name in the registry does not make a future family sound. Finite grammar is not automatic soundness.

The dest crate still knows an `lp<…>` grammar (`run_sg parse` / `run_sg solve`) and a code-rewrite family. Those are **family drivers**, not the public five-stage SPK-002 board. v1 taught LP-forcing as the core idea. v2 does not.

---

## 8. Internal eight-stage modes (not public SPK-002)

`internal_stage_count: 8` on the SPK-002 controller is real. It is **not** the public numbering.

Live dest YAML:

| Mode | Directory | Public? | What you are doing |
| --- | --- | --- | --- |
| Symbol packet iteration | `how_to_play_yaml/mode_1_symbol_packet_iteration/` | **Yes — 5 stages, SPK-002** | Recursive YAML packet loop |
| Proofer | `how_to_play_yaml/mode_2_proofer/` | No — internal 8 | Finite-grammar theorem *attempts*; external proof oracle owns theorem status |
| Operator | `how_to_play_yaml/mode_5_operator/` | No — internal 8 | Fill an operator lattice; admission only after contract + mechanical checks |
| Candidate-ideas proposer | `2_how_to_play/mode_1_candidate_ideas_proposer/` | No — **SPK-001** 8-stage leftover | Do not call this v2 Mode 1 |
| Nemotron/genesis | `symsys_config.yaml` lists `nemotron_templates` | Dest tree has **support/** overlays only, no `mode_3_nemotron/` stage YAML | Not a playable public mode in this dest |

Controller preambles are prepended to every internal stage. Mode 2 includes OP-semantics and MSS-μ kernel text. Mode 5's main controller is shorter; the MSS-μ kernel also lives at `support/mode_5_operator/mss_mu_controller.yaml`.

OP is a Layer-1 **syntactic** binary operator. Mapping it to arithmetic, tensor, boundary, causality, optimization, or physics requires an explicit interpretation license. Unlicensed mapping is operator overloading — kill it at audit.

### Internal stages 1–8 (how to play them)

Think DAG, not chat. Packetization exists to force claims through finite grammar, typed extraction, witness-bearing trichotomy, and oracle-scoped promotion. LLMs propose. They do not green-light.

**Stage 1 — Compression gate.** No quotient until the word problem is finite and equality is mechanically testable. Poetic or unbounded input: `gate_status: REFUSED`, reason `WORD_PROBLEM_UNDECIDABLE`. Mode 2 frames this as axioms for a proof attempt. Mode 5 frames it as an operator-trait contract (hidden carrier growth, side effects → refuse).

**Stage 2 — Ideation.** Mode 2: 5–7 candidates, all F0, at least two surprising, at least two implementable without an LLM, at least one that weakens the seed. Mode 5: **exactly three** operator implementation candidates (`d_0` conservative baseline, then two more), aimed at deterministic trait impls — still F0.

**Stage 3 — Audit.** Route each candidate: `ESCALATE_TO_LEVEL2` / `HOLD_AS_IDEA` / `KILL`. Hunt imported priors, semantic drift, scalarization, OP overloading, cycle/face smuggling, numeric-label smuggling, evidence smuggling (agreement, elegance, compression, analogy, confidence). **Cannot raise evidence level.**

**Stage 4 — L2 extraction.** Prose → typed finite objects (`T`, `~`, `ρ`, `d0`, `d1`, licenses) or refuse. Extraction cannot produce F2/F3/F4 by itself. Classify imported assumptions (`DECLARED`, `REQUIRED_FOR_TEST`, `AMBIGUOUS`, `HALLUCINATED_PRIOR`, and the `*_PRIOR` tags in the YAML). Name the narrowest evaluator O0–O5.

**Stage 5 — MSS-μ evaluator.** Classify each class in `Q = T / ~`:

| Label | Meaning | Required witness |
| --- | --- | --- |
| Ex (exact) | `e_t` in im(d0) | C0 linear combination; `d1_image` empty |
| Surv (survivor) | closed and not exact | empty `d1_image`; not in im(d0) |
| Open | `d1(e_t) ≠ 0` | nonempty `d1_image` |

A context witness `w = (x, y, c)` with `x ~ y` but `ρ(c,x) ≁ ρ(c,y)` is a **lift trigger**, not a licensed lift. A survivor without that witness stays `StabilizedSurvivor`, not `LiftCandidate`.

Chain lock: if `d0` exists, `d1 ∘ d0 = 0` (F2 in the original kernel text; weighted forms appear in Mode 2 Stage 5). Failure: `RefusalCertificate` reason `CHAIN_FAIL`. Also `SEPARABILITY_FAIL`, `OBSERVER_FAIL` as written in the evaluator template.

Declare gauges `phi_value` (distance to repair) and `gamma_value` (closure mass). Declaring them is not computing them; the host must re-derive if a stronger terminal depends on them.

**Stage 6 — Adversarial / separating context.** Search for `w = (x,y,c)` against all declared `ρ`. Verdicts: `SURVIVES` / `DRIFT_DOWNGRADE` / `REPAIR_PROPOSED` / `KILLED`. A proposed repair edge is not authorized by being written down. Quotient-separability justification is required to *propose* it; licensing is still later.

**Stage 7 — Countermodel refinement.** Non-promotional. Preserve, downgrade, or kill. `NO_COUNTERMODEL_FOUND` is not evidence of truth. Do not invent a countermodel to look busy.

**Stage 8 — Evidence plan.** Name O0–O5 evaluators, rank by **implementation usefulness not truth**, emit `CANDIDATE_RANK_MATRIX`. A lift may be *proposed* here (`lift_contract` fields `w, E, m, F, U, iota, pi`). It is licensed only after evaluator/checker validation. Stage 8 does not license lifts alone.

Support files (`paper_refinement.yaml`, `poison_corpus.yaml`) are not extra public stages. Paper refinement is a compression/evidence-extraction overlay: do not upgrade status; do not treat compression as correctness.

Mode 3 templates in `symsys_config.yaml` point at `yaml/mode_3_nemotron/…`, which is **not** present as stage YAML in dest `how_to_play_yaml/` (only `support/mode_3_nemotron/`). Do not invent a playable Mode 3 from the config keys.

---

## 9. Local green is not global green

Every public stage carries:

```
boundary_check:
  local_valid: true|false
  global_valid: true|false
  boundary_violation: true|false
  preserved:
    - seed_question
    - policy_boundary
    - evidence_ceiling
    - terminal_target
    - allowed_transforms
```

Play meaning:

- Local: this step follows an admitted local rule.
- Global: the declared problem, protected skeleton, terminal target, evidence ceiling, and policy boundary did not mutate.

LocalGreen and not GlobalGreen is a **boundary violation**, not a Certificate with a footnote. Fluent YAML that changes the question is a fail, same as a pivot that walks off the feasible set in the old LP family.

Packetization is a partial map. Two worlds can share a packet shape and disagree on unencoded semantic truth. Do not decode “the YAML looks right” as “the claim is true.”

---

## 10. What you actually run in this dest tree

Live crate: `code/rust/` package **`omega_symbol_game`**.

Current bins (read from dest sources; these replace v1's `cd omega_engine/products/symbol_game` story):

**Parse / solve an LP or code-rewrite family (not the five-stage loop):**

```
cargo run -p omega_symbol_game --bin run_sg -- parse
cargo run -p omega_symbol_game --bin run_sg -- solve --fixture <path> --budget 2
```

`run_sg solve` is a budgeted propose/validate/repair loop over a declared `lp<…>` or code-rewrite seed. The host decides each candidate. Default repair budget 2. `--live` needs the crate `live` feature. Firewall: prints evidence and a typed terminal; mints no authority.

**ShapeOnly admission of one cochain_obstruction packet and one code_rewrite packet:**

```
cargo run -p omega_symbol_game --bin omega_symbol_admit -- --proposal PATH [--receipt PATH]
```

Refuses self-certification, trailing prose, and missing families. Receipt `authority_effect` is `None`. Ceiling is ShapeOnly.

**Public five-stage SPK-002 loop (what this guide is for):** dest tests pin `SymbolPacketIterationRunner` over inlined SPK-002 YAML:

```
cargo test -p omega_symbol_game --test symbol_packet_iteration_e2e
```

That test is the dest proof that the public loop is five stages, that SPK-001 is refused, that Round F is required, and that F2 / EmpiricalOracleRequired self-promotion is refused. It is not a theorem of the seed you typed.

Do **not** run the v1 commands as if they were dest-current:

```
cd omega_engine/products/symbol_game
cargo run -j 1 --bin run_proof_pipeline …
cargo run -j 1 --bin run_operator_tower …
cargo run -j 1 --bin symsys-pipeline --features legacy-pipeline …
```

Those lines are how v1 taught the eight-stage crate layout. This crate's `Cargo.toml` does not ship those bins. Internal 8-stage **YAML** is still dest-present for Mode 2/5; the historical orchestrator binaries are not what `omega_symbol_game` currently exports.

`symsys_config.yaml` still names models and template paths. Treat it as the contract map (`templates` = five public stages; `proofer_templates` / `operator_templates` = internal eight). It does not authorize mid-run model shopping as evidence promotion (`forbid_status_upgrade_by_llm: true`).

---

## 11. Worked miniature (public Stage 1 skeleton)

This is a shape to play into, not a Certificate. Copy the real schema from `stage_1_seed_packet.yaml`. Values here are illustrative F0 testimony.

```
derived_under_policy: SPK-002
schema_version: symbol_packet_iteration.v0.2
stage_id: stage_1_seed_packet
packet_id: SPK-SEED-example
parent_packet_id: null
seed_question: Does local YAML validity preserve the declared seed question across one SPK-002 round?
policy_boundary: SPK-002
boundary_check:
  local_valid: true
  global_valid: true
  boundary_violation: false
  preserved:
    - seed_question
    - policy_boundary
    - evidence_ceiling
    - terminal_target
    - allowed_transforms
raw_input_summary: Player asked whether a locally valid packet can still violate the seed.
discarded_prose:
  - Please prove my engine is generally intelligent.
ambiguities:
  - globally valid is a host field; the model filling true does not make it true.
seed_claims:
  - claim: Packet shape does not preserve unencoded semantic truth.
    apparent_evidence_level: F0
vocabulary:
  - term: local_valid
    definition: Step follows an admitted local rule under the stage schema.
    level: representability
  - term: Certificate
    definition: Host terminal after replay; not model-authored success.
    level: authority
iteration:
  run_id: example
  parent_packet_id: null
  current_packet_id: SPK-SEED-example
  next_packet_id: SPK-EXP-example
  depth: 1
  max_depth: 5
```

A later Stage 5 that sets `evidence_level: F2` on this claim is an automatic loss: the dest runner treats that as self-promotion.

The 2026-09 draft also shows a *different* miniature: a five-element carrier cycle, `successor^17(alpha)`, host-rederived `17 mod 5 = 2`, land on `gamma`, terminal `evidence_only`. That is a glyph-calculus receipt example. It is not an SPK-002 five-stage artifact, and it does not speak to how the model represented the arithmetic internally.

---

## 12. How you lose (and how you do not win)

**Losses (host should stop you):**

- Markdown fences around the YAML
- `derived_under_policy` not `SPK-002`
- Missing required adversarial round, especially F
- Missing `next_prompt` at Stage 5
- Self-assigned F2/F3 or EmpiricalOracleRequired
- Mid-run template edit or human candidate injection (SGI-001)
- Treating `|Σ|=38` as a theorem or a Certificate reason
- Treating `NO_COUNTERMODEL_FOUND` or five completed stages as proof
- Treating Stage 8 `lift_contract.licensed: true` as a licensed lift
- Importing continuum physics / Lie / geometry without a mapping license from declared primitives (and SGI-001 still wants those realizations out of the core spec)
- Producer-only `verified: true`
- Calling the internal 8-stage DAG the public game
- Running v1 cargo paths and reporting dest-green

**Non-wins (the run may be clean and still not a proof):**

- `Certificate` inside declared scope (ShapeOnly / LocalReplay / BoundaryChecked)
- `Continue` with a tighter `next_prompt`
- `OracleNeeded` with a named O4/O5 evaluator
- `THEORY_REFUTATION_CANDIDATE` that is specific and testable
- `REFUSED` / `CHAIN_FAIL` with a witness — honest terminals are the point

Paper 043 (and the LGGR firewall it carries) is why a locally pretty packet still cannot hide a collapsed representation. This guide does not restate that monograph. It tells you not to play as if math_spine were still the canon pointer and not to play as if eight public YAML stages were the modern board. It does not point at dest Paper 032 / PO-032.

---

## 13. Pointers (read these; do not flatten them)

| Need | Where |
| --- | --- |
| Public 5-stage schemas | `2_how_to_play/how_to_play_yaml/mode_1_symbol_packet_iteration/` |
| Internal 8-stage proofer | `…/mode_2_proofer/` |
| Internal 8-stage operator | `…/mode_5_operator/` |
| Integrity / run manifest | `…/symbol_game_integrity_contract.yaml` |
| Template map / max rounds | `…/symsys_config.yaml` |
| Host overlay (draft) | dump `symgam_new_intructions.md`; dest synthesis in historical Doc 05 and brief 20 |
| Theory spine for v2 | Paper 043, not math_spine, not dest PO-032 |
| v1 player guide | `2_how_to_play/v1_historical_2026-05_lp_forcing/how_to_play.md` (separate version; do not merge) |

`AuthorityEffect: None.`
