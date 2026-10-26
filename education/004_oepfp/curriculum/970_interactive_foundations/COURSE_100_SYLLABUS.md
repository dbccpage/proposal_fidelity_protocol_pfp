# The Symbol Game — A 100-Lesson Course (Course I)

`AuthorityEffect: None.`

> **Status: DRAFT FOR REVIEW · v0.1 · 2026-09-18 · owner: Jeremy Carroll**
> This is a single self-contained planning document, circulated to multiple review teams
> **before any lesson is built**. Nothing here is committed as final; the arc, boundaries,
> anchors, and honesty framing are all open to revision. See **§ For reviewers** below for
> what we need from you and how to leave revisions, and the **Revision log** at the end.

---

## For reviewers

Please review against the lens closest to your team, and record findings in the
**Revision log**. We specifically want:

- **Grounding accuracy.** Does every lesson's *anchor* resolve to a real notebook, code
  module, claim ID, or receipt? Flag any anchor that is wrong, missing, or overstated.
- **Pedagogical sequencing.** Does each lesson depend only on earlier ones? Flag jumps,
  gaps, or lessons that belong in a different tier/module.
- **Honesty & claim-typing.** Is anything asserted that should be `[Declared]` or `[Open]`
  rather than `[Pinned]/[Proved]`? Flag any guarded word (*forced, minimal, canonical,
  universal, complete*) used without a proof or declared scope. This matters most.
- **Scope & boundaries.** Are the three tier boundaries right? Is anything in scope for
  "Course I = only the Symbol Game" that actually belongs to a later course?
- **The open questions** (see *Build order & next steps*): granularity, copy-vs-reference
  of the LGGR/quantum modules, and per-lesson live-model cost budget.

Leave revisions as inline comments/suggestions on this file, or as a dated row in the
**Revision log**. Conflicting recommendations across teams are expected — the owner
reconciles before the Tier-I build begins.

---

**What this is.** A complete, buildable curriculum that takes a learner from a naked
prompt to the advanced mathematics of the Symbol Game — the discrete-L1, fail-closed
contract for driving untrusted language models — and out to open-weight internals,
governance of agentic swarms, and the physics (fermion sign / spin) where the same
obstruction algebra genuinely applies. It is **Course I** of a planned series; Course I
is *only* the Symbol Game.

**How it is built.** The course does not start from scratch. It sequences and expands
the lesson folders named from the former notebooks 00 through 11 (see [`NOTEBOOK_PLAN.md`](NOTEBOOK_PLAN.md)),
the `N0`–`N15` genesis/obstruction/Regge/Gödel series, `notebook_lib`, the paper `code/`
verifiers (PO-032/033), the `bench/` mechanism + matrix + packets suites, and the Omega
engine's `lggr_prime_seam` and `quantum` modules. Every lesson **anchors** to one of these;
lessons are the teaching layer, the papers and code are the authoritative layer.

**House disciplines (non-negotiable, from `NOTEBOOK_PLAN.md` §2).** Every lesson:
carries the claim-typing legend and tags each result **[Pinned] / [Proved] / [Declared] /
[Open]**; uses the guarded words *forced, minimal, canonical, universal, complete* only
beside a proof or a declared scope; carries a **CAN-show / CANNOT-show** scope box; binds
to pinned verifiers rather than re-implementing; uses **exact rational arithmetic** (never
floats) for discrete decisions; supports **dual-mode** LLM (live API + offline mock/receipt);
ends with an **Anchors** table (paper §, claim ID, verifier, Lean theorem, receipt) and
**Student Exercises** with hidden solutions.

**Delivery.** Primary vehicle = Jupyter notebooks (extends the existing series). Key
conceptual moments get a **Manim** animation (the cochain complex, the manifold collapse,
the meron cancellation) — flagged per-lesson with 🎬. The published interactive demo
([`the Symbol Game`](https://claude.ai/artifact/MqksZxUBEuWEQuFPDJ4Rve)) is the course's
30-second on-ramp. Three cross-cutting threads run the whole way and converge in Tier 3:
**🧩 typed packets (YAML + glyphs)**, **🛡 LGGR governance (the epistemic immune system)**,
and **⚛ the density/obstruction bridge (spin & sign problems)**.

**Per-lesson format.** `title` · one-line **objective** · **anchor** (notebook / code /
claim / receipt) · CAN/CANNOT frame · one exercise · (🎬 if it earns an animation).

---

## Tier I — Foundations (Lessons 1–25): *from a prompt to a proof*

The arc the newcomer asked for: start at a plain prompt, watch it fail, then build the
game one stage at a time — the carrier, the glyphs, the YAML packet, the eight stages —
and *measure what each one does to the result*.

### Module A — The problem with plain prompting (1–5)
1. **The naked prompt.** Ask a strong model "is this set of relations consistent?" and watch it launder a contradiction. — *anchor:* `bench/head_to_head`, Phase-1. 🎬
2. **The Wager.** Trust the model, or verify it? The one-sentence thesis and why "verify" wins. — *anchor:* `lesson_970_01_1_wager_why_llms_hallucinate_overclaim`, PO-033 §1.
3. **Cancellation laundering.** Why an averaged/L2 score hides an integer defect an L1 obstruction cannot. — *anchor:* `lesson_700_12_1_anatomy_conversational_fluff_bullshit_llms`, Plan 05.
4. **Three sovereignties.** Train / decode / verify — where a user actually has leverage over a model. — *anchor:* `lesson_950_02_1_three_layers_sovereignty`.
5. **Your first host verdict.** Compute Φ₁ on a 3-cycle by hand; CONSISTENT vs CONTRADICTION, live. — *anchor:* `lesson_700_06_1_simplicial_cochains_coboundary_operators`, `l1_symbol_game_governor.py`. 🎬

### Module B — The carrier and the glyphs / "hieroglyphics" (6–10)
6. **What is a carrier?** A finite alphabet the host pins — the game's ground set. — *anchor:* `lesson_800_02_1_historical_roots_mss_0_genesis_distinction`, `glyph_calculus.py`.
7. **Why exotic glyphs.** Carrier marks are *declared codepoints*, not words — a symbol earns meaning only by declaration. — *anchor:* `glyph_calculus.Carrier`.
8. **The homoglyph attack.** APL α (U+237A) vs Greek α vs Cyrillic а — why NFKC normalization fails and an allowlist wins. — *anchor:* `glyph_calculus` docstring.
9. **The codepoint pin as a firewall.** Any character off the allowlist is `FW-CARRIER-CODEPOINT`, refused. — *anchor:* `glyph_calculus.check_term`.
10. **Measuring the carrier's grip.** Attention concentrates on declared carriers (≈3.14× [Pinned, receipt]). — *anchor:* `lesson_950_05_1_what_happens_inside_transformer`, `bench/mechanism`. 🎬

### Module C — YAML packets and typed structure 🧩 (11–15)
11. **Why YAML / MD+YAML.** A prompt as a *typed packet*, not prose — every field a known type. — *anchor:* `bench/packets/TYPED_PACKETS.md`, `packet_codec.py`.
12. **Sealing a packet.** The 4-field kernel: RFC-8785 canonical JSON → SHA-256; the digest is a bytes↔type bijection. — *anchor:* `lesson_900_01_1_4_field_packet_envelope`, `PacketCodec.seal/verify`.
13. **Strict parse.** Duplicate keys and unknown fields are refusals, not last-one-wins. — *anchor:* `glyph_calculus.check_no_duplicate_keys / check_no_unknown_fields`.
14. **The closed op set.** Nine ops, exactly one per ledger row — the op *is* the evidence class. — *anchor:* `glyph_calculus.CLOSED_OPS`.
15. **Forbidden fields.** No `passed/verified/trusted` on the wire; a claim is a `claimed_*` on a candidate, a verdict only on a receipt. — *anchor:* `prompt_artifact_v1.schema.json`.

### Module D — The stages of the game 🧩 (16–20)
16. **Stage 0–1.** The sealed envelope and the host-authored prompt artifact = the admissible region A. — *anchor:* `stage_0`, `stage_1` schemas.
17. **Stage 2–3.** Candidate + LLM turn: the model *proposes* (claims, not facts). — *anchor:* `stage_2`, `stage_3`.
18. **Stage 4.** The coboundary score: how far did Φ₁ move, at what structural cost. — *anchor:* `coboundary_score_v1`.
19. **Stage 6–7.** Evaluation + elimination receipts: replayable verdicts, one obstruction discharged. — *anchor:* `stage_6`, `stage_7`.
20. **A full turn, end to end.** Walk one packet through all stages against a real model. — *anchor:* `lesson_970_19_isolated_symbol_game_host`, `governor_end_to_end.py`.

### Module E — Playing the game (21–25)
21. **Dual mode.** Live API vs offline mock / receipt replay — the same lesson runs with no key. — *anchor:* `notebook_lib/llm_client.py`, `NOTEBOOK_PLAN` §2.6.
22. **Reading a receipt.** Anchors, claim IDs, verifiers — trace any number to the code that made it. — *anchor:* `NOTEBOOK_PLAN` §2.7.
23. **The honesty discipline.** The CAN/CANNOT frame and claim-typing as a feature, not a hedge. — *anchor:* `NOTEBOOK_PLAN` §2.3.
24. **Your first governed run.** Wrap a plain LLM call in the Layer-3 governor on a toy problem. — *anchor:* `lesson_970_11_1_architecture_governed_agent`, `symbol_game_toolkit.py`.
25. **Tier-I capstone.** Gate a real prompt, catch a planted contradiction, show the fail-closed refusal + receipt. — *anchor:* `bench/head_to_head`.

---

## Tier II — The Mechanism (Lessons 26–50): *the mathematics of the referee*

Now open the host and show why the verdict is exact and replayable — cochains, the
obstruction, exact certificates, the anti-morphism collapse, and building an agent.

### Module F — Relational foundations (26–30)
26. **One refused self-loop.** Grammar 0 irreflexivity on one edge. The level-0 wire `<>` is lesson 800.01. — *anchor:* `lesson_800_02_1_historical_roots_mss_0_genesis_distinction`.
27. **Arity filtration & the ARS.** Redex matching, substitution modulo group action, termination. — *anchor:* `lesson_800_04_1_abstract_reduction_systems_ars`.
28. **The S(n) expressivity obstruction.** o_n ∈ H¹ — why some structure cannot be expressed below an arity. — *anchor:* PO-032 §3.7, `SnTower.lean`.
29. **Primitive Difference.** The difference setoid the whole game measures against. — *anchor:* `lesson_950_04_hott_identity_paths`, `hott_symbol_game.py`.
30. **HoTT identity paths.** Identity types and the symmetry involution, constructively. — *anchor:* `lesson_950_04_hott_identity_paths`, `IdentityTypes.lean`.

### Module G — Cochains and the obstruction (31–35)
31. **C⁰ → C¹.** The coboundary δ⁰ and the space of gauge-explainable claims B¹. — *anchor:* `lesson_700_06_1_simplicial_cochains_coboundary_operators`. 🎬
32. **Φ₁, exactly.** The weighted L1 obstruction; {Φ₁=0} = B¹ = the admissible sub-manifold. — *anchor:* `lesson_700_06_1_simplicial_cochains_coboundary_operators`, `l1_symbol_game_governor.compute_phi1`.
33. **The holonomy cycle.** A directed k-cycle worked to the last integer. — *anchor:* `lesson_700_06_1_simplicial_cochains_coboundary_operators`, `bench/packets/meron_collapse` (Part A analogue).
34. **Monotone descent, fail-closed.** Why a move that raises Φ₁ is refused (DefectIncrease). — *anchor:* `governor.step_cut`, PO-033.
35. **The projection.** P_S² = P_S and the nearest-coboundary landing (the exact repair). — *anchor:* `lesson_700_06_1_simplicial_cochains_coboundary_operators`, `exact_repair`.

### Module H — Exact certificates (36–40)
36. **Incidence & total unimodularity.** ∂₁, TUM, integrality for free. — *anchor:* `lesson_700_10_1_total_unimodularity_tum_incidence_matrix`, `TotalUnimodularity.lean`.
37. **Exact rational LP duality.** Dual circulation certificates; zero duality gap over ℚ. — *anchor:* `lesson_700_10_1_total_unimodularity_tum_incidence_matrix`.
38. **Weighted NSP & unique sparse landing.** Weights break the tie — one L1-optimal answer. — *anchor:* PO-032 §5, `l1_sparse_landing.py`, `SparseLanding.lean`.
39. **Why never floats.** Discrete decisions on exact arithmetic; a float comparison is a bug. — *anchor:* `NOTEBOOK_PLAN` §2.5.
40. **Replay.** A second machine reproduces the verdict from the numbers alone. — *anchor:* `PacketCodec.verify`.

### Module I — Steering by collapse: the anti-morphisms 🧩 (41–45)
41. **Anti-morphisms.** Interior operators on the admissible lattice — the dual of generation. — *anchor:* `bench/packets/antimorphism.py`.
42. **The five injectable ops.** PIN / SHAPE / DEMAND / REFUSE / LAND as decreasing set maps. — *anchor:* `antimorphism.py`.
43. **The collapse theorem.** Order-independent core; the three verdicts LANDED / RESIDUAL / REFUSED_EMPTY. — *anchor:* `antimorphism.py`, `test_antimorphism.py` [Pinned]. 🎬
44. **Grammar vs token carrier.** Structure ≠ alphabet: k separated integers needs a *grammar*. — *anchor:* `bench/matrix/run_repair_matrix.py` (grammar arm) [Pinned].
45. **Multi-pass collapse.** Residual-derived demands hone the region across passes. — *anchor:* `antimorphism.collapse_adaptive`.

### Module J — Sparsity, excision, and your own agent (46–50)
46. **L1 sparsity vs dense CoT.** The 50-task benchmark — sparse answers, fewer unpriced rewrites. — *anchor:* `lesson_700_12_1_anatomy_conversational_fluff_bullshit_llms`, `l1_sparsity_bullshit_benchmark.py` [Pinned, receipt].
47. **Bullshit excision.** Fluff excision and the unpriced-rewrite-density = 0 axiom. — *anchor:* `lesson_700_12_1_anatomy_conversational_fluff_bullshit_llms` (Woland Swarm axiom).
48. **The head-to-head result.** Host 100% vs a capable model collapsing; failure = over-flagging. — *anchor:* `bench/matrix`, Phase-1 [Pinned]. 🎬
49. **Governed theorem proving.** Topology-50 receipt fields `governed_solved` 50 and `ungoverned_solved` 0. That count is not a proof. — *anchor:* `lesson_950_06_topology50_proof_search`, `Topology50.lean`.
50. **Tier-II capstone.** Build a full Symbol Game agent wrapping a real model via the governor adapter. — *anchor:* `lesson_970_11_1_architecture_governed_agent`, `governor_adapter.py`, TAU_SG_V1.

---

## Tier III — Internals, Governance & Physics (Lessons 51–100): *reach into the model, and out to the swarm*

The advanced tier: manipulate open-weight internals, build the density-matrix bridge to
spin/sign-problem physics, install LGGR as the epistemic immune system, govern agentic
swarms, and finish with Manim + the path to publication.

### Module K — Manipulating open-weight internals (51–58)
51. **Three-layer reachability.** What you can touch on open weights vs a hosted API. — *anchor:* `lesson_950_02_1_three_layers_sovereignty`, `bench/mechanism`.
52. **Logits & logprobs.** The decode-time simplex you can read. — *anchor:* `mechanism/local_carrier_control.py`.
53. **Carrier projection at decode.** Mask off-carrier logits to −∞: 0.04% → 100% carrier mass. — *anchor:* `CarrierProjection` [Pinned]. 🎬
54. **logit_bias on hosted models.** Overriding a token even without weights (7→5). — *anchor:* `bench/mechanism`.
55. **Reading attention.** `output_attentions`, carrier vs fluff heads. — *anchor:* `lesson_950_05_1_what_happens_inside_transformer`, `mechanism`.
56. **Steering attention.** The 4D additive carrier mask moves last-layer attention 0.058 → 1.0. — *anchor:* `local_attention_steering.py` [Pinned]. 🎬
57. **KV-norm mechanics.** Frobenius-norm invariance; the 71% memory drop. — *anchor:* `lesson_950_05_1_what_happens_inside_transformer` [Pinned, receipt].
58. **Attention entropy as diagnostic.** Entropy and its change-rate as reasoning phase signals. — *anchor:* `lesson_950_05_1_what_happens_inside_transformer`, `reasoning_density.rs`.

### Module L — The density-matrix bridge ⚛ (59–66)
59. **Distributions → density matrices.** The diagnostic vocabulary (explicitly *not* physical QM). — *anchor:* `QUANTUM_ENGINES.md` §5.
60. **Purity, entropy, coherence.** Trace-diagnostics of a token distribution. — *anchor:* `density_matrix.rs`.
61. **The H1 → density bridge.** The Φ₁ residual as a density carrier ρ(h)=|h⟩⟨h|/⟨h,h⟩. — *anchor:* `density_from_h1.rs` [Pinned, 18 tests].
62. **Harmonic density.** Hodge Laplacian Δ₁ nullspace; dimension = β₁ (the first Betti number). — *anchor:* `harmonic_density.rs`. 🎬
63. **Phase witnesses.** Oriented cycle transport, path-groupoid, unitary representations. — *anchor:* `density_from_h1.rs`.
64. **Channels.** Depolarizing / amplitude-damping as noise and confidence-decay models. — *anchor:* `quantum_channel.rs`.
65. **Trajectories.** ρ(t) over a reasoning trace; convergence detection. — *anchor:* `reasoning_density.rs`.
66. **The honest fence.** These are diagnostics over probability distributions, not claims that LLMs are quantum. — *anchor:* `QUANTUM_ENGINES.md` §7 [Open where unproven].

### Module M — The fermion sign problem: spin QM that genuinely applies ⚛ (67–74)
67. **What a sign problem is.** ⟨sign⟩ → 0 exponentially in volume·β; the signal drowns. — *anchor:* `bench/packets/MERON_COLLAPSE.md`.
68. **Merons as obstructions.** A cluster whose flip flips the global sign = a nonzero sign-cochain obstruction. — *anchor:* `meron_collapse.py` (Part A). 🎬
69. **Exact cancellation.** Any configuration with a meron cancels to exactly zero. — *anchor:* `meron_collapse.meron_flip_sum` [Pinned].
70. **Zero-meron = {Φ=0}.** The surviving positive sector is the admissible manifold; restricting is LAND. — *anchor:* `meron_collapse.py`.
71. **Honing a model onto it.** Soft prompting launders; host-governed enforcement lands "meron-cluster" in 6–7 hints. — *anchor:* `meron_live.py` [Pinned].
72. **The NP-hardness fence.** The general sign problem is NP-hard — the host correctly stays RESIDUAL. — *anchor:* `MERON_COLLAPSE.md` (Troyer–Wiese 2005) [Open].
73. **GOMC diagnostics.** Composing residual density + observer quotient + branch proposals into one report. — *anchor:* `gomc_diagnostics` (`QUANTUM_ENGINES` §3.10).
74. **Spin systems: scope.** Where the obstruction mapping holds and where it breaks — stated plainly. — *anchor:* `QUANTUM_ENGINES.md`.

### Module N — LGGR governance: the epistemic immune system 🛡 (75–82)
75. **Local Green, Global Red.** Why a clean *local* reading is unsound as a certificate. — *anchor:* `lggr_prime_seam/overview.md`, papers 019/020/021.
76. **Detector adequacy.** Green stays `OracleNeeded` until collapsing detectors are excluded. — *anchor:* `adequacy.py/rs`.
77. **The asymmetric verdict.** RED-sound / GREEN-unsound; `certifies_closure()` = false for every variant. — *anchor:* `verdict.rs` [Pinned, tested].
78. **Closure eligibility.** The Closure Lemma is necessity, not sufficiency. — *anchor:* `lggr_overlay`.
79. **The LGGR flag in GOMC.** `LocalGreenGlobalRedDiagnostic`: local near-pure, global mass still positive. — *anchor:* `gomc_diagnostics`.
80. **Evidence ceilings.** No bare `Green`; the strongest label is `GreenNumericallySupported`, capped at `BoundaryChecked`. — *anchor:* `prime_seam`.
81. **Anti-skills as an immune system.** When *not* to apply an operator — domain- and problem-typed wrappers. — *anchor:* the anti-morphism library; user framing.
82. **Continuation ≠ authorization.** A predicate a host consults; `PrimeContinuation` carries no authority token. — *anchor:* `prime_seam`, `AuthorityEffect: None`.

### Module O — Agentic swarms & governance 🛡 (83–90)
83. **The Woland Swarm axiom.** Unpriced rewrite density = 0 across a swarm of agents. — *anchor:* `lesson_700_12_1_anatomy_conversational_fluff_bullshit_llms`.
84. **Governing a swarm with the host.** Every inter-agent move receipted through the governor. — *anchor:* `governor_adapter.py`, TAU_SG_V1.
85. **Typed inter-agent packets.** The sealed envelope as the swarm's lingua franca. — *anchor:* `packet_codec.py`, `TYPED_PACKETS.md`.
86. **Fail-closed at swarm scale.** One bad move → DefectIncrease refused, no cascade. — *anchor:* `governor_end_to_end.py`.
87. **LGGR across a swarm.** No agent's local green certifies global closure. — *anchor:* `lggr_prime_seam`.
88. **Anti-morphism libraries by domain.** The wrapper, categorized — a multi-category of operands. — *anchor:* `antimorphism.py`, user framing.
89. **The audit of audits.** Replayable, nested swarm audits. — *anchor:* `N9_audit_of_audits`.
90. **Policy about policies.** Governing the governance itself. — *anchor:* `N8_policy_about_policies`.

### Module P — Frontiers, Manim & publication (91–100)
91. **The S(n) tower.** Forced lifts on nonzero H¹ — the deep structural engine. — *anchor:* PO-032 §3.3, `SnTower.lean`.
92. **Gödel-capable, non-Turing-complete.** What kind of system this is. — *anchor:* `N10`, `N11`, `N12`.
93. **Regge cells & Bianchi.** The geometric face of the obstruction. — *anchor:* `N13_regge_cells_and_bianchi`.
94. **Detection vs exactifying lift.** The two operating modes and when each is honest. — *anchor:* `N14_detection_vs_exactifying_lift`.
95. **Where it is open.** The internal-concentration conjecture, stated as a conjecture. — *anchor:* PO-032, Plan 01 [Open].
96. **Manim I.** Animate the cochain complex C⁰ → C¹ → Q¹ and the obstruction quotient. 🎬 — *anchor:* Plan 05 visualizations.
97. **Manim II.** Animate the manifold collapse 125 → 19 → 1 (LANDED / RESIDUAL / REFUSED_EMPTY). 🎬 — *anchor:* `antimorphism.py`.
98. **Manim III.** Animate meron cancellation and the zero-meron positive sector. 🎬 — *anchor:* `meron_collapse.py`.
99. **From course to paper.** Turning this narrative into PO-034 positioning and a publishable result. — *anchor:* Plan 01.
100. **Capstone.** Govern your own frontier task end-to-end — receipted, fail-closed, recorded on video. — *anchor:* everything.

---

## Build order & next steps

1. **Scaffold** `notebooks/COURSE_100/` with a shared lesson template (claim legend,
   CAN/CANNOT box, anchors table, exercise cell) and a `_lesson_lib` that re-exports the
   pinned verifiers — so no lesson re-implements math.
2. **Build Tier I first** (Lessons 1–25), because it is the on-ramp that converts a
   stranger into a player; each lesson is a runnable notebook that emits a receipt.
3. **Add the three Manim scenes** (Lessons 96–98) early as reusable assets — the cochain
   complex, the collapse, the meron — because they also serve the demo and the paper.
4. **Tier II and III** reuse the paper `code/`, `bench/`, and Omega-engine modules already
   in the repo; the work is sequencing and honest exposition, not new mathematics.

**Open questions for the author (adjust before Tier-I build):** lesson granularity
(one notebook per lesson vs per module); whether the LGGR/quantum modules get *copied*
into `the_symbol_game` for self-containment or *referenced* in place; and how much live-model
cost to budget per lesson (all lessons run offline by default).

**Positioning stays honest.** This course teaches the defensible claim — exact, replayable,
fail-closed governance of a live model, with a cohomological obstruction as the referee —
and marks every conjecture as one. That honesty is what makes it credible to the readers who
matter.

---

## Revision log

Reviewers: add a dated row. Keep the newest at the top. `Scope` = Tier/Module/Lesson(s) or
"global". `Type` = grounding · sequencing · honesty · scope · other.

| Date | Reviewer / team | Scope | Type | Finding / proposed revision | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-09-18 | course architect (Grok) | global | sequencing | **Do not build 100 notebooks. Do not scaffold `notebooks/COURSE_100/`.** Three curricula collide (COURSE_100 / NOTEBOOK_PLAN notebooks 00 through 11 / Plan 05 `docs/learn/`). Track A = 8×90s videos + one offline capstone cell (KPI: first receipted governed run under 90 minutes). Videos 9–15 reuse `lesson_700_06_1_simplicial_cochains_coboundary_operators`/`lesson_700_10_1_total_unimodularity_tum_incidence_matrix`/`lesson_950_04_hott_identity_paths`/`lesson_700_12_1_anatomy_conversational_fluff_bullshit_llms`/`lesson_970_11_1_architecture_governed_agent` and benches. Keep the 100-row list as a catalog only. | open |
| 2026-09-18 | course architect (Grok) | Module D / 16–20 | grounding | Restore Stage 5 (`stage_5_code_change_proposal.schema.json`). Merge 16–20 into one 8-stage mock walk. Reanchor L20 to `play_demo.py` / `symbol_game_toolkit.py`. `lesson_970_19_isolated_symbol_game_host` is a two-cell native `symgam` host, not a provider walk. | open |
| 2026-09-18 | course architect (Grok) | 5, 18, 31–32 | sequencing | Φ₁ is used before cochains. Merge 5+31+32 into one 3-cycle video/cell: teach `C⁰→C¹` immediately before Φ₁. Track A numbers = `play_demo` `(1,1,1)` Φ₁=3; keep notebook 05’s chorded `(1,2,0)` cell on Track B. Bind module-level `compute_phi1`. | open |
| 2026-09-18 | course architect (Grok) | 21–23 | sequencing | Dual-mode, receipt replay, and CAN/CANNOT move to Track A video 2, before any live call. Default mock (`llm_client.py` already does). | open |
| 2026-09-18 | course architect (Grok) | 51–100 | scope | Course I is only the host/governor. Move L–P (density, fermion/GOMC, LGGR v1 `REJECTED_UNSOUND`, swarms, Gödel/Regge, Manim-as-lessons, publication) to Course II+. Delete “genuinely applies” and unscoped “complete.” | open |
| 2026-09-18 | course architect (Grok) | 96–98 | other | Delete 96–98 as lessons. Manim is a video asset. Pull coboundary and collapse (and optional sparse-landing) forward; meron only if Track C. | open |
| 2026-09-18 | course architect (Grok) | 28, 91 | honesty | Retype L28 as PO032-C82 `[CONJECTURE]`. `SnTower.lean` is §3.3 rigidity (`C20`–`C23`) only. Unguard/drop L91 *forced* lifts. | open |
| 2026-09-18 | course architect (Grok) | 1, 9, 12, 42, 48 | honesty | L1 is `head_to_head`, not matrix Phase-1. L12 is `json.dumps(..., sort_keys=True)`, not RFC 8785 JCS. L48 is `gpt-4o-mini` vs exact host; host 100% by construction; README says N=12 while `phase1_summary.json` is n=30. L9 is `Carrier.check_term`. L42 SHAPE/DEMAND are REDUCE/DECIDE nicknames; LAND is `LAND_ON_ZERO`. | open |
| 2026-09-18 | course architect (Grok) | 10, 53, 56, 57 | honesty | ≈3.14× is `0.0066/0.0021` on Qwen2.5-0.5B (absolute carrier mass 0.66%, `PO032-C71`). Receipt `kv_cache_energy_reduction_percentage` is **-37.53**, not 71% (`PO032-C73` is an extrapolated generation row). Membership `0.04%→100%` and steering `0.058→1.0` do not yield a correct digit. `CarrierProjection` is a class in `local_carrier_control.py`. | open |
| 2026-09-18 | (author) | global | — | v0.1 drafted and circulated for review | open |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## Sign-off

The Tier-I build begins only after the owner reconciles the review findings above and
marks this document **APPROVED**. Until then it is a draft.

| Team | Reviewer | Date | Verdict (approve / revise) |
| :--- | :--- | :--- | :--- |
| Course architect (workflow `course-100-pedagog-review`) | Grok | 2026-09-18 | **revise** |
|  |  |  |  |
