# Video Storyboard: Lesson 200.10 — Holonomy on Directed Graphs: Non-Abelian Link Transports and Multi-Simplex Hinge Loops

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | Visual schematic contrasting 1D scalar graph circulation with 4D non-abelian hinge loops in $SO(4)$. | "In 1D graphs, circulation is commutative scalar addition. But in higher-dimensional gauge theories and 4D Regge complexes, link transports are non-abelian group elements." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor evaluating $SO(4)$ quarter-turn rotations $R_{yz}$ and $R_{xz}$ and calculating the ordered commutator product $U = R_{yz} R_{xz} R_{yz}^T R_{xz}^T$. | "Path-ordered matrix multiplication is strictly sensitive to traversal sequence. We evaluate two orthogonal quarter-turns in four dimensions over exact integer coordinates." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output displaying Lean 4 countermodel verification: scalar angle sum is zero, but $U$ transforms $e_0 \mapsto -e_1 \ne e_0$. | "Notice the trap: the scalar sum of rotation exponents is zero, yet the ordered matrix product deviates from the identity. Lean 4 theorem scalar_sum_does_not_certify_closure formalizes this defect." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary checklist contrasting non-abelian commutator with genuinely closed abelian sub-loops ($R_{yz} R_{yz}^T = I_4$). | "To certify zero curvature around a codimension-2 triangular hinge, the governor must evaluate path-ordered matrix holonomy, not scalar projections." | `[Pinned]` |

---

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
