# Cognitive Scaffolding and Expertise Reversal Discipline

AuthorityEffect: None.

This reference formalizes the educational literature findings on novice-to-expert scaffolding across `education` tracks, grounded in the deterministic findings of `teaching_and_learning_findings.md`.

## Literature Foundations

1. **Worked Examples for Novice Skill Acquisition ([S1] Barbieri et al. 2023):**
   - In mathematics and introductory computing, studying worked examples produces medium-to-large performance improvements over unguided problem solving.
   - Early skill acquisition requires a fully worked, step-by-step canonical case before learners attempt generative coding.
2. **Completion Problems ([S3] van Merriënboer et al. 1992):**
   - For introductory programming, completing partially finished programs produces superior high-transfer outcomes compared to blank-slate design and implementation.
3. **Expertise Reversal Effect ([S2] Kalyuga 2007):**
   - Heavy scaffolding (worked examples) that aids novices becomes redundant or cognitively obstructive as learner competence increases.
   - Advanced and frontier tracks must deliberately fade step-by-step guidance into completion tasks, productive failure problems, and open challenge investigations.
4. **Spacing vs. Massed Practice ([S4] Meta-Analytic Review):**
   - Spacing practice across separate sittings produces robust small-to-medium learning gains over massed practice.
   - Retrieval practice alone does not show a robust transfer advantage in mathematics; curriculum structure should prioritize spaced revisits to core invariants over retrieval quiz drills.
5. **Productive Failure ([S5] Sinha & Kapur 2021):**
   - Problem solving before instruction improves conceptual transfer (when supported by post-problem consolidation), but does not improve procedural fluency.
   - Productive failure does not apply to younger children (grades 2–5, ages 5–11) or initial procedural syntax; it is reserved for conceptual challenges in intermediate and advanced tracks.

---

## Pedagogical Scaffolding Matrix by Track Tier

| Curriculum Tier | Target Audience / Tracks | Primary Scaffolding Stage | Required Lab Structure | Literature Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0: Beginners** | Ages 5–500 (`000_beginners`, `how_to_play`) | **Worked Example + Completion** | 1 fully worked step $\to$ 1 completion with 1 blank step $\to$ 1 guided test | [S1], [S3]: Novices require heavy guidance and atomic steps. |
| **Tier 1: Novices** | Ages 11–500 (`100_novices`) | **Completion + Faded Practice** | Setup cell $\to$ partially completed pipeline $\to$ fill-in assertions | [S3]: Program completion fosters reflective problem solving. |
| **Tier 2: Intermediates** | Engineering (`200_intermediates`, `300_advanced`) | **Faded Guidance + Productive Failure** | Conceptual challenge first $\to$ verifier execution $\to$ synthesis | [S2], [S5]: Fading guidance avoids cognitive overload from redundancy. |
| **Tier 3: Researchers & Frontier** | Advanced (`400_researchers`) | **Open Challenge & Verification** | Minimal setup $\to$ adversarial hypothesis testing $\to$ exact proof audit | [S2]: High expertise reverses the benefit of worked examples. |

---

## Authoring Invariants

1. **Prediction Gate Precondition:** Every notebook with an adversarial or diagnostic check must require the learner to commit a prediction (e.g. `prediction = "..."`) prior to running the evaluating cell.
2. **Illustrative Models vs. Pinned Verifiers:** Any simplified toy model created for pedagogical clarity must:
   - Be explicitly labeled `# ILLUSTRATIVE MODEL ONLY: NOT AUTHORITATIVE`.
   - Be asserted strictly equal to the pinned repository verifier or native engine result on the declared test domain.
3. **Exact Rational Purity:** All discrete L1 calculations, cochains, and eigenvalues in lesson notebooks must use exact rational arithmetic (`fractions.Fraction`). Floating-point literals in discrete decision logic are forbidden (`FLOAT_FORBIDDEN`).
