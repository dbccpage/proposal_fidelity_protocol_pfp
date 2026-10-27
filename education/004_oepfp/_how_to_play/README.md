# How to Play The Symbol Game: Master Educational Syllabus & Player Manual

Current execution (2026-10-12): [practical PFP and discovery](13_practical_pfp_and_discovery.md). Use the consolidated `pfp` commands there; historical profiles below do not imply current runtime support. The fixed pilot grid is retired; each new run should answer a concrete use or discovery question.


> **Lead Council:** `L3_nous_panepistimion` & `L3_logos_techne`  
> **Audience:** How-to-play manual only (ages 11 to 500): students,
> evaluators, engineers, and researchers. The beginner lesson track
> [`000_beginners`](../curriculum/000_beginners/) states ages 5 to 500. This line is not that track.
> **AuthorityEffect:** `None`. Host execution receipts certify local protocol state, not universal truth.  
> **Location:** `education/documentation/004_oepfp/_how_to_play/` (companion to [`education/curriculum/004_oepfp/`](../curriculum/))

---

## 1. Start with a first game

The Symbol Game separates a proposal from its check. Declare your marks,
goal, and checking rule; submit a packet; inspect a scoped receipt.
Read [Paper 000](../papers/symbol_game/000_pfp_introduction/README.md)
for an introduction using S(n), MSS-N, and basic packets.

Choose from [ten useful ways to play](06_ten_useful_ways_to_play.md) or explore the master matrix in [the modalities atlas](07_all_ways_to_play_the_symbol_game.md).
For recent bounded LLM experiments, see [numbered prompt roles and PO035 play](../docs/16_numbered_prompt_roles_and_po035_play.md): short public workpads, calculation/carrier matching, measured failures and explicit experimental variants.
These are practical learning and research routes across all published monographs and demonstrations. New players can start with mark distinction, packet
repair, and prediction before attempting advanced mathematics.

The notebooks below model a **declared directed triangle**. Their runtime
is [educational_governor.py](educational_governor.py), an exact local teaching
model, separate from the native Symbol Game host. Its circulation check does
not compute the native Phi1, Gamma2, or Xi functionals. ASSERT records an
annotation; it does not prove that annotation. VERIFY certifies only zero
circulation on the declared triangle. Historical editions, native interfaces,
and mathematical extensions have additional contracts.

---

## 2. Core Curriculum, Interactive Notebooks & Visual Player Guides

This directory contains the canonical educational breakdown of the game mechanics, system architecture, and operational guidelines:

### Interactive Jupyter Notebooks (Browser Sessions)

Begin with [ten executable local exercises](02_ten_ways_to_play.ipynb),
which accompanies the [ten-route guide](06_ten_useful_ways_to_play.md).

| Notebook | Focus | Key Topics |
| :--- | :--- | :--- |
| **[`00. Interactive Walkthrough`](00_interactive_how_to_play_walkthrough.ipynb)** | Live Visual Walkthrough | Step-by-step interactive walkthrough of all 4 moves, 7 scenarios, reactive `ipywidgets` workbench, and live defect gauge. |
| **[`01. Interactive Scenarios Lab`](01_interactive_scenarios_lab.ipynb)** | Diagnostic Refusal Lab | Adversarial lab probing the boundary conditions: carrier smuggling, non-monotonic rollbacks, and post-terminal state locks. |

### Visual Diagrams & Infographics (`assets/`)

| Asset | Format | Preview / Topic |
| :--- | :--- | :--- |
| **[`01. Dual-Space Architecture`](assets/01_dual_space_governor_loop.svg)** | SVG | Proposer space $\to$ Bit-level firewall $\to$ Discrete host governor loop. |
| **[`02. 3-Cycle Triangle Repair`](assets/02_triangle_constraint_cycle.svg)** | SVG | $K_3$ directed graph showing holonomy circulation $\Phi_1 = 6$ and chord repair. |
| **[`03. The Four Legal Moves`](assets/03_four_legal_moves.svg)** | SVG | Complete state-transition infographic for `ASSERT`, `CUT`, `VERIFY`, `RETRACT`. |
| **[`04. Strict Lyapunov Descent`](assets/04_strict_lyapunov_descent.svg)** | SVG | Trajectory staircase demonstrating atomic rollbacks on non-monotonic attempts. |

### Prose Guides & Handbooks

| Document | Focus | Key Topics |
| :--- | :--- | :--- |
| **[00. Quickstart Guide](00_quickstart_how_to_play.md)** | 5-Minute Onboarding | The dual-space loop, the 4 moves, and your first playable triangle repair game. |
| **[01. The Three Editions](01_the_three_game_editions_and_evolution.md)** | Historical Evolution | How the game evolved from v1 LP-forcing to v2 SPK-002 YAML, to modern v3 L1 Oracle Governor. |
| **[02. Rules of the Board](02_the_rules_of_the_board.md)** | Mathematical Governance | The 5-tuple state $S$, bit-level carrier firewall, move preconditions, and Lyapunov descent invariants. |
| **[03. Developer Handbook](03_developer_and_player_handbook.md)** | Practical Integration | Prompting models, defeating the AM-4 stationary loop with chord decoupling, and local Python integration. |
| **[04. Visual Cheat Sheet](04_visual_reference_and_cheat_sheet.md)** | Quick Reference | Master system flowcharts, refusal code dictionary, graph topologies ($K_3, K_4$), and 4-file receipts. |
| **[05. Examiner's Theoretical Minimum](05_examiner_theoretical_minimum_exam.md)** | Comprehensive Qualification Exam | The 3-tier, 13-problem qualification exam testing novice intuition, intermediate cochains, and professional researcher defense before the Apartment 50 tribunal. |
| **[06. Ten Useful Ways to Play](06_ten_useful_ways_to_play.md)** | Pedagogical Onboarding | 10 accessible, code-accompanied learning paths for students and engineers. |
| **[07. The Complete Modalities Atlas](07_all_ways_to_play_the_symbol_game.md)** | Master Research & Play Spectrum | Complete taxonomy of canonical ways to play PFP across papers 000–011, live demos, and multi-agent swarms. |
| **[08. Theory Spine & Authority Boundary](08_theory_spine_and_authority_boundary.md)** | Protocol Spine | Boxed canonical spine, total verifier, packet fidelity, and explicit authority ceilings. |
| **[09. LP Forcing Trace: Worked Example](09_lp_forcing_trace_worked_example.md)** | Concrete Trace | Finite-symbol intent compression, dual bound derivation, local vs global check, and status taxonomy. |
| **[10. The Eight-Stage Pipeline](10_eight_stage_pipeline.md)** | Architecture Lifecycle | 8 public operational stages, host evaluation boundary, and stages/controller correspondence. |
| **[11. Run Modes & Legacy CLI](11_run_modes_and_legacy_cli.md)** | Historical References | Proof pipeline, operator tower, and historical symsys-pipeline CLI reference. |
| **[12. Output Layout & Troubleshooting](12_output_layout_and_troubleshooting.md)** | Operations & P* | Run artifact layout, manifest fields, diagnostic triage, and deterministic seed-to-P* assembly. |
| **[Examiner Exam Test Suite](test_examiner_theoretical_minimum.py)** | Automated Exam Verifier | 15 programmatic tests executing exact rational solutions, zero duality gap certificates, Regge Cayley-Menger determinants, and 48-mutation rejection. |
| **[Python Test Suite](test_how_to_play_scenarios.py)** | Executable Scenarios | 7 automated unit test scenarios verifying move rules, rollback on defect increase, and receipt issuance. |
| **[Interactive Board Engine](interactive_board.py)** | Visual UI Module | Reactive HTML board cards, dynamic SVG triangle graphs, and `ipywidgets` player workbench. |

---

## 3. The Dual-Space Arena Architecture

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                     PROPOSER SPACE                          │
 │       (Language Model / Continuous Latent Vectors)          │
 │  • Emits structured move candidate: ASSERT, CUT, VERIFY     │
 │  • Explores combinatorial tree heuristic                    │
 │  • Has ZERO verification authority                          │
 └──────────────────────────────┬──────────────────────────────┘
                                │ Candidate Proposal Payload
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                BIT-LEVEL CARRIER FIREWALL                   │
 │  • Rejects unpinned unicode codepoints (fail-closed)        │
 │  • Enforces RFC 8785 canonical JSON formatting              │
 └──────────────────────────────┬──────────────────────────────┘
                                │ Pinned Byte Stream
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                 DISCRETE HOST GOVERNOR                      │
 │              (Deterministic Ground Truth)                   │
 │  • Recomputes integer L1 defect: Phi_1 = ||delta^1 c||_1    │
 │  • Enforces Strict Descent: Phi_1(S') < Phi_1(S)            │
 │  • Emits 4-File Receipt: receipt.json, novella.md,          │
 │    dda_actions.jsonl, summary.json                          │
 └─────────────────────────────────────────────────────────────┘
```

---

## 4. Archival Editions & Declarative Machine Contracts

For deep research and historical reproducibility, this folder preserves the original specifications and machine contracts:

- [`contracts/`](contracts/): Declarative YAML contracts governing gameplay modes:
  - `symbol_game.contract.yaml`: Master operational game contract.
  - `symbol_game_integrity_contract.yaml`: Tamper detection, hash chain integrity, and process obstruction rules.
  - `mode_1_symbol_packet_iteration/`: SPK-002 5-stage YAML schemas.
  - `mode_2_proofer/`: Internal 8-stage proofer pipeline.
  - `mode_5_operator/`: Internal 8-stage operator tower.
- [`v1_historical_lp_forcing/`](v1_historical_lp_forcing/): Historical 2026-05 documentation for the rational linear programming duality gap edition.
- [`v2_modern_packet_iteration/`](v2_modern_packet_iteration/): The SPK-002 5-stage symbol packet iteration guide and architecture monograph.
- [`v3_l1_oracle_governor/`](v3_l1_oracle_governor/): The L1 Oracle Governor blueprint and cochain routing architecture.

---

## 5. Running the Interactive Verification Tests

You can verify the gameplay rules, host referee engine, and interactive Jupyter walkthrough notebooks directly in your terminal:

```bash
# 1. Run the discrete host governor unit test scenarios (7 scenarios)
py -3.12 -m pytest education/documentation/004_oepfp/_how_to_play/test_how_to_play_scenarios.py -v

# 2. Run Examiner's Theoretical Minimum qualification exam fixture (15 tests across 3 tiers)
py -3.12 -m pytest education/documentation/004_oepfp/_how_to_play/test_examiner_theoretical_minimum.py -v

# 3. Run the complete curriculum and exam E2E verification battery (61 tests)
py -3.12 -m pytest education/education_app/tests/test_e2e_curriculum_and_exam.py -v
```

Historical expected output (not a fresh execution receipt):
```text
test_how_to_play_scenarios.py: 7 passed in 0.65s
test_examiner_theoretical_minimum.py: 15 passed in 0.82s
test_e2e_curriculum_and_exam.py: 61 passed in 1.40s
```

- [Where PFP code lives and how to replay it](../docs/17_runtime_ownership_and_replay.md)
