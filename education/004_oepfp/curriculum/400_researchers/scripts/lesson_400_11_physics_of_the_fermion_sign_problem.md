# Video Storyboard: Lab MSS-N.07: Continuum: Interval Arithmetic & Topological DB Cells

AuthorityEffect: None.

**Target Duration:** `140s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | MSS-66 to MSS-79: rational intervals, simplicial database complexes, and CRDTs. | "Covering continuum approximations and distributed data, this lab explores rational intervals, topological database cells, and CRDT joins." | `[Declared]` |
| **02** | `0:30 - 0:55` | Rational interval addition: [1/3, 1/2] + [1/4, 1/3] = [7/12, 5/6] in exact Fractions. | "Rational interval arithmetic tracks guaranteed lower and upper bounds without roundoff error, catching inverted bounds as bugs." | `[Executed]` |
| **03** | `0:55 - 1:25` | Topological database cell foreign key check: missing vertex triggers boundary leak error. | "Foreign key relationships form boundary maps in a simplicial complex. Missing parent records violate boundary closure." | `[Tested]` |
| **04** | `1:25 - 2:20` | State-based G-Counter CRDT: max-join is idempotent and commutative. | "Replicas merge states by computing least upper bounds across node counters, converging monotonically without central coordination." | `[Tested]` |

---

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (140s target).
