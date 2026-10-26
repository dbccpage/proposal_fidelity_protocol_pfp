# Video Storyboard: Lab SN.01: S(n) Core Derivation, Ground State & Descent

AuthorityEffect: None.

**Target Duration:** `150s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | Show S(n) Tower diagram highlighting s00 Ground to s06 Descent. | "The S(n) Tower constructs discrete manifold retractions. Here we examine how state filtration and lattice collapse preserve mathematical invariants." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code cell showing core_collapse order-independence across multiple permutations. | "Lattice core collapse is confluent: whether you reduce outer brackets first or inner brackets first, the resulting minimal normal form is identical." | `[Tested]` |
| **03** | `1:00 - 1:35` | Pseudometric collision demo: distance=0 with distinct points A and B. | "Crucially, distance zero does not prove point equality without an explicit metric separation axiom. We fence this gap to avoid false convergence claims." | `[Pinned]` |
| **04** | `1:35 - 2:30` | Boxed Descent Law animation: retract(lift(x)) == x. | "Every accepted lift into S(n) carries a retraction down-rule that recovers the predecessor state exactly." | `[Pinned]` |

---

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (150s target).
