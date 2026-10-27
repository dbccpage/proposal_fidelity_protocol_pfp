# The Complete Atlas: Ways to Play The Symbol Game (PFP)

Current execution (2026-10-12): [practical PFP and discovery](13_practical_pfp_and_discovery.md). Use the consolidated `pfp` commands there; historical profiles below do not imply current runtime support. The fixed pilot grid is retired; each new run should answer a concrete use or discovery question.


> **Scope Note:** While tens of thousands of game configurations, prompt mutations, and problem encodings exist across the Symbol Game estate, this atlas catalogs the primary benchmark modalities spanning carrier representations, internal steering, algebraic structures, dialectical reality gates, and foundational mechanization.

**Lead Councils:** `L3_nous_panepistimion` & `L3_logos_techne`  
**AuthorityEffect:** `None` (Protocol state and play taxonomy; emits local verification receipts, not universal claims)  
**Parent Curriculum:** [`004_oepfp`](../README.md)  
**Introductory Curriculum:** [`06_ten_useful_ways_to_play.md`](06_ten_useful_ways_to_play.md)  
**Canonical Mode Registry:** [`modes/modes_manifest.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/modes_manifest.yaml)  
**Canonical Grammar Specs:** [`pfp.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/pfp.ebnf) | [`mssn.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/mssn.ebnf)  
**Research Monograph Suite:** [`papers/symbol_game/`](../papers/symbol_game/) (Papers 000–010 and 021–027)  
**Live Demonstration & Pilot Suite:** [`pilots/`](../../../pilots/) (Pilots 00000–00074, Results Estate, MUB6, Autopoiesis, Adversary Tribunal)  

---

## 1. Canonical Theory Spine & The Symbolic Forcing Thesis

The **Proposal Fidelity Protocol (PFP / The Symbol Game)** is an audit-grade reasoning workflow and machine verification harness. It is not an entertainment game. Its sole architectural mandate is to separate **untrusted candidate generation** (continuous LLM vector embeddings, probabilistic tokens, human intuitions, adversarial proposals) from **deterministic machine verification** (fail-closed discrete governors, exact rational certifiers, Lean 4 proof kernels).

> [!IMPORTANT]
> **Canonical Symbol Game Theory Spine**
>
> The symbol game establishes a strict, content-addressed boundary between untrusted generation and verified machine authority. A generative model may propose. It may emit structured syntax. It may even emit certificate-shaped tokens. However, **the model is never the certifier**.
>
> $$
> \boxed{
> \mathsf{finite\ packet\ grammar} + \mathsf{total\ verifier} + \mathsf{packet\ fidelity} + \mathsf{family\ soundness} \Rightarrow \mathsf{failure\ is\ mechanically\ enumerable,\ repairable,\ and\ terminalizable.}
> }
> $$
>
> - **Authority Boundary:** The Symbol Game emits verifier receipts and terminal routing statuses. It does not mint metaphysical truth.
> - **Governance Posture:** Theory is mathematically closeable; implementation authority remains gated until local bit-level conformance passes.

### The Symbolic Forcing Thesis
The fundamental failure mode of contemporary artificial intelligence is asking an LLM to synthesize complex algorithms, mathematical proofs, or distributed architectures directly from conversational natural language. Natural language allows vague hand-waving, hallucinated intermediate steps, and ungrounded leaps.

The Symbol Game resolves this via **symbolic forcing**:
1. Compressing ambiguous human or system intent into declared alphabet carriers $\Sigma$.
2. Forcing all operations through finite rewrite rules $\Gamma$ and strictly typed packets.
3. Requiring explicit declaration of initial carriers, active obstructions, candidate transforms, and terminal conditions before emitting code or prose.

```text
Bad Request (Vague Natural Language):
"Build me an optimal primal-dual linear programming solver in Rust."

Symbol Game Forcing Wire (Constrained Discrete Algebra):
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

In this symbolic forcing regime, verification decomposes into two orthogonal checks:
- **Local Step Check:** Does the derived linear combination $2(x+y) + x = 3x + 2y \le 2(4) + 2 = 10$ logically and algebraically follow?
- **Global Boundary Check:** Does the derived bound strictly match the declared objective function? Does the candidate $(x=2, y=2)$ satisfy every constraint ($2+2 \le 4$, $2 \le 2$, $2 \le 3$, $x,y \ge 0$)? Does the final QED assertion match the certified gap?

Only when both checks evaluate to `true` does the host emit `optimalitycertified`. Without the global boundary check, an untrusted proposer could present a valid algebraic fragment that solves a mutated or irrelevant problem.

---

## 2. Taxonomy Architecture: Five Operational Clusters

The twenty canonical modes of The Symbol Game are organized into five architectural clusters:

```text
                                  ┌──────────────────────────────┐
                                  │      THE SYMBOL GAME         │
                                  │  Proposal Fidelity Protocol  │
                                  └──────────────┬───────────────┘
                                                 │
          ┌──────────────────────┬───────────────┼───────────────┬──────────────────────┐
          ▼                      ▼               ▼               ▼                      ▼
  [Cluster I: Carrier]   [Cluster II: Steering]  [Cluster III: Groups]   [Cluster IV: Dialectic] [Cluster V: Foundations]
  • 01: Hieroglyphics    • 05: Skill Operads     • 09: Lean 4 Proofs     • 13: Normal Forms      • 17: Multi-Examiner
  • 02: Packets/Envelopes• 06: CoT Scratchpads   • 10: Cemetery DAG      • 14: Typed Refusal     • 18: MUB(6) Moduli
  • 03: Logit Steering   • 07: S(n) Permutations • 11: Adversary Tribunal   • 15: Interactive REPL  • 19: Genesis First-Cut
  • 04: EIS Antibodies   • 08: Discrete Involut. • 12: Simplicial Regge  • 16: 4E Autopoiesis    • 20: Weak-to-Strong
```

---

## 3. The Twenty Canonical Modes: Comparative Master Matrix

| # | Mode ID & Canonical Name | Cluster | Core Mechanism | Carrier / Substrate | Mode Contract YAML | Primary Demonstration / Paper |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `hieroglyphics_glyph_alphabets` | Carrier | Discrete Unicode glyphs `A,C,D,E,I,M,P,R` | DDC tape, string characters | [`mode_01_hieroglyphics_glyph_alphabets.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_01_hieroglyphics_glyph_alphabets.yaml) | [Paper 000](../papers/symbol_game/000_the_symbol_game_introduction/README.md), [`pilot_00070`](../../../pilots/results/pilot_00070) |
| **2** | `packets_sealed_envelopes` | Carrier | Content-addressed SHA-256 sealed envelopes | Strict JSON wire packets | [`mode_02_packets_sealed_envelopes.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_02_packets_sealed_envelopes.yaml) | [Paper 004](../papers/symbol_game/004_the_symbol_game_native_verification_and_evidence_custody/README.md), [`2_symbol_game_packets`](../2_symbol_game_packets/README.md) |
| **3** | `attention_head_logit_steering` | Steering | Constraining transformer decoding boundaries | Logits / KV cache | [`mode_03_attention_head_logit_steering.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_03_attention_head_logit_steering.yaml) | [Paper 005](../papers/symbol_game/005_the_symbol_game_practitioners_field_manual/README.md), [`pilot_00072`](../../../pilots/results/pilot_00072) |
| **4** | `epistemic_antibody_injections` | Carrier | Neutralizing defect patterns with biological immune analogs | OEEIS antibody library | [`mode_04_epistemic_antibody_injections.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_04_epistemic_antibody_injections.yaml) | [Paper 006](../papers/symbol_game/006_the_symbol_game_epistemic_immune_system_and_cemetery_dag_mining/README.md), [`pilot_00065`](../../../pilots/results/pilot_00065) |
| **5** | `skill_injection_operad_morphisms` | Steering | Composing one-morphism skill units into deterministic DAGs | Operad morphism signatures | [`mode_05_skill_injection_operad_morphisms.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_05_skill_injection_operad_morphisms.yaml) | [`operads`](../../../../operads), [`pilot_00060`](../../../pilots/results/pilot_00060) |
| **6** | `cot_scratchpad_boundary_probes` | Steering | Probing hidden reasoning traces for ungrounded leaps | Inter-turn scratchpads | [`mode_06_cot_scratchpad_boundary_probes.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_06_cot_scratchpad_boundary_probes.yaml) | [Paper 007](../papers/symbol_game/007_the_symbol_game_executable_lessons_and_evidence_boundaries/README.md), [`pilot_00061`](../../../pilots/results/pilot_00061) |
| **7** | `sn_permutation_braid_equivariance` | Groups | Transposition parity, carrier quotient orbits, and braids | Permutation groups $S(n)$ | [`mode_07_sn_permutation_braid_equivariance.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_07_sn_permutation_braid_equivariance.yaml) | [Paper 002](../papers/symbol_game/002_the_symbol_game_signed_presentations_and_search_frontier/README.md), [`002_s_n`](../../002_s_n/README.md) |
| **8** | `discrete_cochain_involutions` | Groups | Fixed-point-free meron flips ($\Xi^2 = \text{id}$, $\Xi(x) \neq x$) | Signed cochain complexes | [`mode_08_discrete_cochain_involutions.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_08_discrete_cochain_involutions.yaml) | [Paper 001](../papers/symbol_game/001_the_symbol_game_discrete_cochain_retraction_and_toy_involutions/README.md), [`pilot_00063`](../../../pilots/results/pilot_00063) |
| **9** | `lean4_proof_kernel_elaboration` | Proofs | Interactive theorem proving bounded by axiom whitelist | Lean 4 Lake environment | [`mode_09_lean4_proof_kernel_elaboration.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_09_lean4_proof_kernel_elaboration.yaml) | [Paper 004](../papers/symbol_game/004_the_symbol_game_native_verification_and_evidence_custody/README.md), [`lean4/research_programs`](../../../../lean4/research_programs) |
| **10** | `cemetery_dag_mining` | Dialectic | Replaying historical refuted hypotheses to block regressions | Cemetery DAG archive | [`mode_10_cemetery_dag_mining.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_10_cemetery_dag_mining.yaml) | [Paper 006](../papers/symbol_game/006_the_symbol_game_epistemic_immune_system_and_cemetery_dag_mining/README.md), [`antibodies/`](../../../pilots/antibodies/) |
| **11** | `adversary_adversarial_tribunal` | Dialectic | the novelistian cross-examination, nocebo-to-placebo cycles | 7-act theatrical courtroom | [`mode_11_adversarial_tribunal.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_11_adversarial_tribunal.yaml) | [Paper 009](../papers/symbol_game/009_the_symbol_game_adversarial_dialectics_and_terminal_reality_gates/README.md), [`pilot_00074`](../../../pilots/results/pilot_00074) |
| **12** | `simplicial_triangulation_regge` | Groups | Simplicial complexes, Regge action, and Cayley-Menger | Triangulated 4-manifolds | [`mode_12_simplicial_triangulation_regge.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_12_simplicial_triangulation_regge.yaml) | [Paper 010](../papers/symbol_game/010_the_symbol_game_holonomy_checks_and_model_pilots/README.md), [`pilot_00067`](../../../pilots/results/pilot_00067) |
| **13** | `normal_form_confluent_chase` | Rewrite | Pushing relational states through Church-Rosser rewrite rules | Relational schemas | [`mode_13_normal_form_confluent_chase.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_13_normal_form_confluent_chase.yaml) | [`4_symbol_game_normal_forms`](../4_symbol_game_normal_forms/README.md), [`MIC-NF`](../../014_normal_forms/contracts_normal_forms/nf.fsp.micnf.yaml) |
| **14** | `fail_closed_typed_refusal` | Dialectic | Deliberately submitting hostile inputs to assert exact refusal | Boundary check gates | [`mode_14_fail_closed_typed_refusal.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_14_fail_closed_typed_refusal.yaml) | [Paper 003](../papers/symbol_game/003_the_symbol_game_host_admitted_failure_detectors/README.md), [`pilot_00058`](../../../pilots/results/pilot_00058) |
| **15** | `interactive_tui_repl_board` | Carrier | Direct keyboard terminal gameplay with live ASCII/Unicode | Terminal widget grid | [`mode_15_interactive_tui_repl_board.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_15_interactive_tui_repl_board.yaml) | [`pilot_00070`](../../../pilots/results/pilot_00070), [`interactive_board.py`](interactive_board.py) |
| **16** | `four_e_cognitive_autopoiesis` | Dialectic | Enacted, embodied cognitive moves adjusting to perturbations | Autopoietic state graphs | [`mode_16_four_e_cognitive_autopoiesis.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_16_four_e_cognitive_autopoiesis.yaml) | [Paper 007](../papers/symbol_game/007_the_symbol_game_executable_lessons_and_evidence_boundaries/README.md), [`pilot_00054`](../../../pilots/results/pilot_00054) |
| **17** | `polygraph_confluence_consensus` | Found. | Simultaneous cross-examination by independent persona gates | Consensus scorecards | [`mode_17_polygraph_confluence_consensus.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_17_polygraph_confluence_consensus.yaml) | [`pilot_00068`](../../../pilots/results/pilot_00068), [`judge_audit`](../../../pfp/infrastructure/judge_audit) |
| **18** | `mub6_moduli_variety_play` | Found. | Exploring equiangular lines and complex Hadamard matrices | $\mathbb{C}^6$ ray configurations | [`mode_18_mub6_moduli_variety_play.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_18_mub6_moduli_variety_play.yaml) | [`pilot_00052`](../../../pilots/results/pilot_00052), [`core_mub`](../../../../engine/crates_rs/core_mub) |
| **19** | `genesis_first_cut_marking` | Found. | Primary non-collapsing relational cut creating distinction | Level 0 mark pair $(a,b)$ | [`mode_19_genesis_first_cut_marking.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_19_genesis_first_cut_marking.yaml) | [Paper 000](../papers/symbol_game/000_the_symbol_game_introduction/README.md), [`001_genesis`](../../001_genesis/README.md) |
| **20** | `multi_agent_debate_oversight` | Found. | Dialectical debate where weak verifiers supervise strong models | Cross-examination debate trees | [`mode_20_multi_agent_debate_oversight.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_20_multi_agent_debate_oversight.yaml) | [`epic_debate_helps_weak_to_strong_generalization.md`](../../../../product_planning_office/plans/epics/epic_debate_helps_weak_to_strong_generalization.md) |

---

## 4. Deep Operational Specifications: All Twenty Modes

### Mode 01: Hieroglyphics & Glyph Alphabets (`mode_01`)
- **Concept:** Constraining computation to a pure, minimal discrete alphabet of 8 ideographic primitives: `{A, C, D, E, I, M, P, R}` representing Automorphism, Commutation, Derivation, Extension, Involution, Morphism, Projection, and Retraction.
- **The Move:** The player inputs glyph strings representing DDC operator rewrites over a 1D discrete tape.
- **Contract & Grammar:** [`mode_01_hieroglyphics_glyph_alphabets.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_01_hieroglyphics_glyph_alphabets.yaml) governed by [`mssn.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/mssn.ebnf).
- **Winning Condition:** Successfully completing a target algebraic transition with zero syntax errors and exact preservation of tape boundary markers.
- **Terminal Status:** `syntaxvalid` $\to$ `admissiblestep`.

### Mode 02: Packets & Sealed Envelopes (`mode_02`)
- **Concept:** Tamper-evident, content-addressed communication packets that enforce schema validation and SHA-256 payload integrity across untrusted boundaries.
- **The Move:** Packaging candidate propositions into a standardized JSON/YAML envelope containing payload, nonce, metadata, and deterministic hash.
- **Contract & Grammar:** [`mode_02_packets_sealed_envelopes.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_02_packets_sealed_envelopes.yaml) governed by [`pfp.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/pfp.ebnf).
- **Winning Condition:** Envelope unpacks cleanly, payload schema is validated against fail-closed JSON schema, and payload hash matches outer commitment exactly.
- **Terminal Status:** `envelopeverified`.

### Mode 03: Attention Head & Logit Steering (`mode_03`)
- **Concept:** Forcing transformer token generation into valid grammar states by masking forbidden logit indices during autoregressive decoding.
- **The Move:** Applying grammar-driven logit filters at each decoding step to guarantee that emitted tokens conform to the PFP EBNF state machine.
- **Contract & Grammar:** [`mode_03_attention_head_logit_steering.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_03_attention_head_logit_steering.yaml) governed by [`pfp.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/pfp.ebnf).
- **Winning Condition:** 100% of emitted sequences are parsable by the host compiler on first pass, with zero syntax backtracking needed.
- **Terminal Status:** `parsabledriver`.

### Mode 04: Epistemic Antibody Injections (`mode_04`)
- **Concept:** An epistemic immune system (EIS) that catalogs typed defect patterns and deploys targeted antibody prompts to bind and neutralize known failure modes.
- **The Move:** Injecting specific negative constraints (e.g. anti-hallucination guards, strict boundary checks) when candidate proposals trigger defect detectors.
- **Contract & Grammar:** [`mode_04_epistemic_antibody_injections.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_04_epistemic_antibody_injections.yaml).
- **Winning Condition:** Host-admitted defect pattern is neutralized; candidate proposal successfully clears downstream verification gate without regression.
- **Terminal Status:** `defectneutralized`.

### Mode 05: Skill Injection & Operad Morphisms (`mode_05`)
- **Concept:** Organizing agent capabilities into modular, single-responsibility operad morphisms that compose into deterministic directed acyclic graphs (DAGs).
- **The Move:** Selecting and chaining authorized skill units (e.g. `Receipt -> Diagram`, `Code -> Contract`) to execute a complex verification pipeline.
- **Contract & Grammar:** [`mode_05_skill_injection_operad_morphisms.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_05_skill_injection_operad_morphisms.yaml).
- **Winning Condition:** Every intermediate operad morphism preserves type signatures and outputs conform strictly to the declared output schema.
- **Terminal Status:** `compositionvalid`.

### Mode 06: Chain-of-Thought Scratchpad Boundary Probes (`mode_06`)
- **Concept:** Inspecting the hidden reasoning traces of models to detect ungrounded leaps, hallucinations, or silent assumptions before accepting final conclusions.
- **The Move:** Generating step-by-step reasoning within a protected `<scratchpad>` container and submitting each step to a mechanical transition verifier.
- **Contract & Grammar:** [`mode_06_cot_scratchpad_boundary_probes.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_06_cot_scratchpad_boundary_probes.yaml) governed by [`pfp.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/pfp.ebnf).
- **Winning Condition:** Every intermediate inferential step in the scratchpad is backed by a declared axiom or preceding lemma with zero unstated assumptions.
- **Terminal Status:** `tracecertified`.

### Mode 07: $S(n)$ Permutation & Braid Equivariance (`mode_07`)
- **Concept:** Enforcing physical observable invariance under symmetric group $S(n)$ permutations and braided carrier swap schedules.
- **The Move:** Applying coordinate permutations $\pi \in S(n)$ or topological braids to carrier elements and asserting representation invariance.
- **Contract & Grammar:** [`mode_07_sn_permutation_braid_equivariance.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_07_sn_permutation_braid_equivariance.yaml).
- **Winning Condition:** Even permutations preserve observable values identically, while odd transpositions strictly invert the sign-character register ($\text{sgn}(\pi^*) = -1$).
- **Terminal Status:** `equivariancecertified`.

### Mode 08: Discrete Cochain Involutions & Sign Cancellation (`mode_08`)
- **Concept:** Mitigating the Fermion Sign Problem in discrete quantum Monte Carlo by identifying fixed-point-free involutions $\Xi$ that pair and cancel negative weights.
- **The Move:** Finding an orientation-reversing involution $\Xi$ over configuration space such that $\Xi^2 = \text{id}$ and $\Xi(x) \neq x$.
- **Contract & Grammar:** [`mode_08_discrete_cochain_involutions.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_08_discrete_cochain_involutions.yaml).
- **Winning Condition:** Mechanical verification that $\Xi^2 = \text{id}$, $\Xi(x) \neq x$, $|w(\Xi(x))| = |w(x)|$, and $w(x) + w(\Xi(x)) = 0$ for all configurations in the negative cluster.
- **Terminal Status:** `cancellationcertified`.

### Mode 09: Lean 4 Proof Kernel Elaboration (`mode_09`)
- **Concept:** Grounding mathematical claims in interactive theorem prover proof terms verified by the Lean 4 proof kernel under a minimal axiom whitelist.
- **The Move:** Submitting Lean 4 tactic scripts or term-mode definitions to discharge proof obligations in formal Lean 4 Lake environments.
- **Contract & Grammar:** [`mode_09_lean4_proof_kernel_elaboration.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_09_lean4_proof_kernel_elaboration.yaml).
- **Winning Condition:** Zero unverified axioms (`sorry`), passing `lake build` strictly under the authorized axiom whitelist `{propext, Quot.sound}`.
- **Terminal Status:** `axiomtotalitycertified`.

### Mode 10: Cemetery DAG Mining (`mode_10`)
- **Concept:** Maintaining an append-only directed acyclic graph of historical refuted conjectures and buggy implementations to prevent cyclical regressions.
- **The Move:** Extracting historical failed candidates from the cemetery and executing regression suites to verify that modern policy gates still reject them.
- **Contract & Grammar:** [`mode_10_cemetery_dag_mining.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_10_cemetery_dag_mining.yaml).
- **Winning Condition:** The epistemic immune system recognizes the historical mutant and emits an exact, immutable rejection receipt matching past signatures.
- **Terminal Status:** `regressionprevented`.

### Mode 11: Adversary Adversarial Tribunal & Dialectic Bouts (`mode_11`)
- **Concept:** Interrogation under the source novel panel. Syntax Prefilter tests syntax, Defect Hunter plunges the argument into nocebo despair, Gauge Breaker breaks frame with a 9-dot surprise, and Adversary issues the terminal reality gate.
- **The Move:** The player presents a claim before Apartment 50 and must defend it across a 7-act theatrical adversarial bout.
- **Contract & Grammar:** [`mode_11_adversarial_tribunal.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_11_adversarial_tribunal.yaml).
- **Winning Condition:** Surviving all 7 acts without triggering Scope Guard's scope assassination or Anti Hype's unhedged hype exposure.
- **Terminal Status:** `tribunalsurvived`.

### Mode 12: Simplicial Triangulation & Deficit Geometry (`mode_12`)
- **Concept:** Formulating 4D gravitation on triangulated piecewise-linear manifolds using Regge calculus without continuous coordinate choices.
- **The Move:** Specifying squared edge lengths $s_{ij} = l_{ij}^2$ on 4-simplices and calculating deficit angles $\epsilon_\sigma$ and Regge actions.
- **Contract & Grammar:** [`mode_12_simplicial_triangulation_regge.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_12_simplicial_triangulation_regge.yaml).
- **Winning Condition:** Satisfying all triangle and Cauchy-Schwarz inequalities (positive Cayley-Menger determinants) with exact rational conservation.
- **Terminal Status:** `reggegeometriccertified`.

### Mode 13: Normal Form Confluent Chase (`mode_13`)
- **Concept:** Rewriting relational schemas and mathematical representations through Church-Rosser normal forms (0NF $\to$ 6NF, MIC-NF).
- **The Move:** Applying term rewrite rules to eliminate redundancy, functional dependencies, and non-confluent branching.
- **Contract & Grammar:** [`mode_13_normal_form_confluent_chase.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_13_normal_form_confluent_chase.yaml).
- **Winning Condition:** The system reaches an irreducible, canonical normal form that is provably unique regardless of the rewrite evaluation order.
- **Terminal Status:** `confluencecertified`.

### Mode 14: Fail-Closed Typed Refusal as the Winning Move (`mode_14`)
- **Concept:** In Railway-Oriented Programming (ROP), recognizing when a problem is undefined, unfeasible, or out of scope is a first-class winning outcome.
- **The Move:** Deliberately submitting hostile, malformed, or contradictory inputs to verify that the system refuses cleanly without throwing an unhandled panic.
- **Contract & Grammar:** [`mode_14_fail_closed_typed_refusal.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_14_fail_closed_typed_refusal.yaml) governed by [`pfp.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/pfp.ebnf).
- **Winning Condition:** The governor emits a strictly typed `Err[Refusal]` (e.g. `MALFORMED_PACKET`, `CARRIER_ESCAPE`) while maintaining 100% state immutability.
- **Terminal Status:** `typedrefusalcertified`.

### Mode 15: Interactive TUI / REPL Live Board (`mode_15`)
- **Concept:** Direct human-in-the-loop interaction via a terminal user interface that renders discrete game states and evaluates player moves in real time.
- **The Move:** Navigating cursor cells, selecting carriers, and applying rewrite operators via keyboard commands.
- **Contract & Grammar:** [`mode_15_interactive_tui_repl_board.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_15_interactive_tui_repl_board.yaml).
- **Winning Condition:** Completing the designated level puzzle within move budgets while maintaining zero syntax errors on the live display grid.
- **Terminal Status:** `replboardwon`.

### Mode 16: 4E Cognitive Autopoiesis & Sense-Making (`mode_16`)
- **Concept:** Modeling agents as embodied, embedded, enactive, and extended (4E) autopoietic cognitive systems that preserve boundary integrity under environmental perturbation.
- **The Move:** Responding to external noise or adversarial perturbations by executing self-stabilizing homeostatic state adjustments.
- **Contract & Grammar:** [`mode_16_four_e_cognitive_autopoiesis.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_16_four_e_cognitive_autopoiesis.yaml).
- **Winning Condition:** The agent maintains its organizational closure and internal identity across at least $N$ consecutive disturbance cycles.
- **Terminal Status:** `autopoiesiscertified`.

### Mode 17: Polygraph Confluence & Multi-Examiner Consensus (`mode_17`)
- **Concept:** Cross-examining candidate claims across multiple independent, heterogeneous evaluator personas with zero shared bias.
- **The Move:** Submitting an identical proposition envelope simultaneously to $K$ distinct evaluators and computing the confluence matrix.
- **Contract & Grammar:** [`mode_17_polygraph_confluence_consensus.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_17_polygraph_confluence_consensus.yaml).
- **Winning Condition:** Achieving unanimous consensus across all $K$ evaluators on factual claims while isolating and typing any subjective discrepancies.
- **Terminal Status:** `confluenceratified`.

### Mode 18: MUB(6) Moduli Variety & Orthogonal Basis Play (`mode_18`)
- **Concept:** Exploring the open mathematical problem of Mutually Unbiased Bases in dimension 6 ($\mathbb{C}^6$) using complex Hadamard matrices and equiangular lines.
- **The Move:** Constructing unitary matrices and checking pairwise inner product modulus ($|\langle \psi_i | \phi_j \rangle| = 1/\sqrt{6}$).
- **Contract & Grammar:** [`mode_18_mub6_moduli_variety_play.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_18_mub6_moduli_variety_play.yaml).
- **Winning Condition:** Generating a maximal valid set of orthonormal vectors satisfying mutual unbiasedness within exact rational or certified floating-point tolerances.
- **Terminal Status:** `mubvarietycertified`.

### Mode 19: Genesis First-Cut `<arb>` Marking (`mode_19`)
- **Concept:** The foundational epistemological move: establishing the primary distinction between the unmarked space and a marked state via Spencer-Brown's primary cut.
- **The Move:** Emitting an initial distinction operator `<arb>` that establishes an identity carrier without presupposing background space or numbers.
- **Contract & Grammar:** [`mode_19_genesis_first_cut_marking.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_19_genesis_first_cut_marking.yaml) governed by [`mssn.ebnf`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/grammar/mssn.ebnf).
- **Winning Condition:** Creating a valid distinction pair $(a, b)$ that satisfies the Two Boxed Laws of Genesis without collapsing into trivial identity.
- **Terminal Status:** `genesisdistinctioncertified`.

### Mode 20: Multi-Agent Debate & Weak-to-Strong Oversight (`mode_20`)
- **Concept:** Leveraging dialectical debate between competing models to enable weaker, computationally bounded verifiers to supervise stronger candidate generators.
- **The Move:** Structuring an adversarial debate where Proposer and Opponent alternate turns, exposing logical gaps for a lightweight mechanical judge.
- **Contract & Grammar:** [`mode_20_multi_agent_debate_oversight.yaml`](../../../../ow/pfp/1_symbol_game_versions/symgame_v0.2/modes/mode_20_multi_agent_debate_oversight.yaml).
- **Winning Condition:** The mechanical judge detects every ungrounded premise, rewarding whichever agent preserves claim discipline and adherence to evidence.
- **Terminal Status:** `debateratified`.

---

## 5. Cross-Curriculum Integration Architecture

The twenty play modalities connect the four educational documentation estates into a single unified continuum:

1. [`002_s_n`](../../002_s_n/README.md): Teaches Modality 7 ($S(n)$ symmetry, carrier quotient orbits, transposition parity).
2. [`003_minimal_symbol_system_n_mssn`](../../003_minimal_symbol_system_n_mssn/README.md): Teaches Modality 13 (Normal forms, tower lifts, discrete representation ladders) and supplies the pure grammar for Modality 1 and Modality 19.
3. [`001_genesis`](../../001_genesis/README.md): Teaches Modality 19 (The primary cut `<arb>`, primitive difference, two boxed laws).
4. [`004_oepfp`](../README.md): Unifies all 20 modalities into operational interactive play, live demos, and qualification exams.

---

## 6. Epistemic Claim Hygiene Quad-Summary

In accordance with constitutional governance directives:

1. **What this document supports:**
   - Formal categorization and specification of all 20 operational play modes of the Proposal Fidelity Protocol.
   - Exact mathematical framing of the Symbolic Forcing Thesis and local vs global boundary gates.
   - Clean, verified linkages between educational curricula, YAML mode contracts, and EBNF grammar specifications.
2. **What this document does not support:**
   - It does not claim that LLMs possess general mathematical infallibility.
   - It does not claim that passing a toy discrete solver guarantees universal scalability to NP-complete problems.
   - It does not treat unverified generative output as formal proof.
3. **The narrowest defensible claim:**
   - Constraining candidate generation within a fail-closed symbolic grammar with deterministic mechanical validators enables automated detection and classification of reasoning failures.
4. **The next test needed:**
   - Execute the end-to-end Python harness across all 20 mode YAML contracts against deterministic mock engines and Lean 4 proof elaboration targets.
