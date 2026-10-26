# Claim Tag Legend and Proof Discipline

AuthorityEffect: None.

This reference specifies the four-tag claim legend, proof truth boundaries, and audience floor separation for all `omega_engine_education` notebooks and prose.

## The Four-Tag Claim Legend

Every lesson notebook and curriculum document within the Symbol Game series must observe the standardized four-tag legend:

| Tag | Canonical Definition | Valid Verification Substrate | Inadmissible Substitutions |
| :--- | :--- | :--- | :--- |
| `[Pinned]` | An immutable repository invariant, contract, or pinned native binary digest. | Pinned executable SHA-256 in `native_functional.py` or immutable contract YAML. | Dynamic recomputation or arbitrary mock values. |
| `[Proved]` | A mechanically verified mathematical proposition. | Machine-checked Lean 4 proof kernel (`lake build NormalFormsCore` or Lean proof term). When used in introductory notebooks, must be explicitly glossed as "deterministic finite code execution in Python". | Equating a passed Python `assert` with a universal mathematical proof. |
| `[Declared]` | An axiomatic premise, boundary definition, or problem assumption. | Schema boundary, input relation, or declared functional dependency set. | Promoting an assumption into a verified property without a verifier receipt. |
| `[Open]` | An unresolved obligation, conjecture, or unproved inductive step. | Typed obligation record or open research problem. | Silent omission of unverified steps. |

---

## The Non-Learning and Non-Authority Invariants

1. **Code Execution $\ne$ Cognitive Acquisition:**
   - A headless or interactive execution of a notebook confirms solely that the Python interpreter executed the cells without unhandled exceptions on that host.
   - An `assert` statement confirms that the specific finite example satisfied the declared condition.
   - Passing an assert is **NOT evidence that a human learner acquired the concept**, and does not constitute a measured educational trial.
2. **Execution $\ne$ Mathematical Proof:**
   - Passing tests on a finite set of tuples or graphs does not constitute a mathematical proof of a universal theorem.
   - Claims must remain strictly disciplined: "demonstrated on this finite fixture" rather than "proves universally".
3. **Age Floors Stay Separate:**
   - The player manual (`how_to_play/readme.md`) states **ages 11 to 500**.
   - Track `000_beginners` (`lesson_000_01_the_empty_slate.md`) states **ages 5 to 500**.
   - These audience floors reflect distinct developmental stages and cognitive load boundaries; they must remain separate and never be merged into a single homogenized floor.
4. **Media Slot Integrity:**
   - An empty `videos/` folder or a folder containing only `.gitkeep` is an empty slot reserved for future recordings.
   - It is strictly forbidden to describe or market an empty `videos/` directory as completed video curriculum.
