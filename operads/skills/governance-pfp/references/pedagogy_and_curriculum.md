# Pedagogical Ladder & Curriculum Standards

AuthorityEffect: None.

## 1. Age-Adaptive Cognitive Ladder (Ages 5 to 500)

Symbol Game mathematical pedagogy bridges intuitive distinction and foundational research through four cognitive tiers:

| Concept | Tier 1: Age 5–10 (Tangible Play) | Tier 2: Age 11–17 (Algorithmic Logic) | Tier 3: Undergraduate (Discrete Math) | Tier 4: Age 50–500 (Foundational Research) |
| :--- | :--- | :--- | :--- | :--- |
| **The Void** | Empty slate `<>` | Empty string `""` / empty set $\emptyset$ | Initial object $\mathbf{0}$ | Unmarked state; pre-topological substrate |
| **Distinction** | Circle in the sand | Boolean delimiter `( )` | Elementary 0-simplex $\sigma_0$ | Spencer-Brown mark; primary distinction |
| **Atoms** | Named toy in a box | String variable `name = "0"` | Generator in free algebra $\mathcal{F}(\Sigma)$ | Atomic symbol in alphabet $\Sigma_{36}$ |
| **Application** | Machine with input/output | Function call `op([x, y])` | Operadic tree node | Manifold retraction term $\mathrm{App}(\tau)$ |
| **Directed Edges** | One-way bridge | Directed edge `u -> v` with weight $w$ | 1-chain element $e_{uv} \in C_1$ | Carrier cochain with orientation |
| **Defect $\Phi_1$** | Step height mismatch | Loop elevation sum mismatch | Coboundary norm $\|\delta^0 f - c\|_1$ | Curvature 1-form defect $\Phi_1$ |
| **The CUT Move** | Shifting terrace heights | Vertex potential update | Exact gauge shift $\delta^0 \phi$ | Discrete deformation gauge shift |
| **Survivor Class** | Unflattenable cycle | Frustrated loop with non-zero sum | Cohomology class $[c] \in H^1(G; \mathbb{Q})$ | Holonomy obstruction $\Gamma_2 > 0$ |

## 2. 2026 Online Micro-Attention Model

Uninterrupted attention decays exponentially online ($t_{1/2} \approx 4.0\text{ minutes}$). Lessons adhere to the **3–5 Minute Pulse Protocol**:

1. **The Hook (0:00–0:45):** A paradoxical or striking physical/geometric question.
2. **The Observation (0:45–1:45):** Direct inspection of a minimal visual diagram.
3. **The Calculation (1:45–3:15):** The student executes an exact calculation (e.g. edge sums around a 3-cycle).
4. **The Resolution (3:15–4:00):** Confronting the defect or invariant discovered by calculation.
5. **The Diagnostic Probe (4:00–5:00):** Immediate verification check before unlocking the next concept.

## 3. Quantitative Efficacy Metrics

- **Diagnostic Probe Pass Rate ($P_{\text{diag}}$):** First-try pass rate $\ge 0.90$.
- **Representation Transfer Index ($I_{\text{transfer}}$):** Translation across prose, geometry, equations, and code $\ge 0.85$.
- **Teaching Efficacy Score ($E_{\text{teach}}$):** Knowledge gain over cognitive friction.

## 4. Beginner Curriculum Structure (Lessons 01–25)

Living in `omega_engine_education/the_symbol_game/lessons/000_beginners/`:

- **Module 1 (01–05): The Mark & The Void** (Slate `<>`, Boundaries, Law of Crossing, Atoms, Self-delimiting words).
- **Module 2 (06–10): Words & First Structures** (Application `op<...>`, Binary alphabet, Tree branches, Deterministic parsing, Inactive words).
- **Module 3 (11–15): Dots, Arrows & Defects** (Directed edges, 3-cycles, Edge values, Defect $\Phi_1$, Graph carrier invariant).
- **Module 4 (16–20): Cuts, Repairs & Fair Play** (Terrace shift, Monotonic descent, Obstinate cycles, Survivor classes, Symbol Game rules & turns).
- **Module 5 (21–25): Triangles, Curvature & Packets** (2-simplex, Simplicial complexes, Deficit angles, Canonical packets, Bridge to spacetime).

## 5. Notebook Execution Standards

1. Pure Python simulation cells without external CDN dependencies.
2. Executable unit test cells (`assert ...`) enabling headless automated grading.
3. Every lesson notebook must execute from start to finish via `pytest` without human intervention.

## 6. Paper Companion Examination Architecture (Landau Theoretical Minimum)

Each research paper under `omega_engine_education/documentation/004_oepfp/papers/omega_engine_symbol_game/` (`000` to `010`) maintains a dedicated companion folder `_lev_landau_theoretical_minimum_quiz/` implementing the Landau Theoretical Minimum examination pattern.

### Two-Deliverable Publication Standard
Every paper quiz companion is composed of two independent Markdown documents compiled to separate PDFs:

1. **The Sadovaya Apartment 50 Preface (`00_preface_at_apartment_50.md` / `preface.pdf`):**
   - Dramatic narrative staging of the examinee confronting the Woland Retinue and Professor Lev Davidovich Landau ("Dau") at the city, Sadovaya 302-bis, Apartment 50.
   - The dialogue, tribunal warnings, and "Seven Mortal Sins" are tailored to the specific mathematical and architectural domain of that paper (e.g., cycle obstructions, signed presentations, failure detectors, or holonomy lattice checks).
   - Compiled and shipped as **PDF #1**.

2. **The Progressive Minimum Quiz (`quiz.md` / `quiz.pdf`):**
   - A progressive challenge sequence adhering strictly to the naked symbol alphabet $\Sigma_{\text{Landau}} = \{0-9, a-z, <, >\}$ and exact rational arithmetic $\mathbb{Q}$.
   - **Progression Gradient:** Begins at page 1 with foundational primitives (elementary marks, primitive distinction, basic incidence) and escalates monotonically to rigorous adversarial reality gates on page 3 (frustrated cycle obstructions, high-dimensional simplex rigidity, or non-trivial dual certificates).
   - Compiled and shipped as **PDF #2**.

### Central Education Hub vs. Paper Locality
- Central repository of study materials, problem banks (Exams 01–VI, prompts VII–XI), and Python verifiers live under `omega_engine_education/documentation/_lev_landau_theoretical_minimum_quiz/` (including `study_guide/` and `_study_guide/`).
- Individual paper packages under `omega_engine_symbol_game/` contain self-contained, paper-scoped instances designed for readers of that specific monograph.

