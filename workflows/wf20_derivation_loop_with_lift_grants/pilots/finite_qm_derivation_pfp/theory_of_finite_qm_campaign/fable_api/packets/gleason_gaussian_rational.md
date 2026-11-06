---
node_id: FQ-GAP-BORN-UNIQUENESS-GLEASON
context_files:
  - lean4/BornRationalSphereObstruction.lean
  - lean4/GleasonRationalPlane.lean
  - lean4/BornGaussRat.lean
---
# Problem: frame functions on Gaussian-rational rays in dimension 3

You are working on the open part of DAG node `FQ-GAP-BORN-UNIQUENESS-GLEASON` in a Lean 4 project that builds finite quantum mechanics from exact arithmetic. You have no tools. Everything you need is in this message, and your answer will be compiled and audited by the host.

## Setting

Let K = ℚ(i), the Gaussian rationals, and V = K³ with the Hermitian form ⟨u, v⟩ = Σₖ conj(uₖ) vₖ.
- A **ray** is a line K·v with v ≠ 0.
- An **orthogonal frame** is a triple of pairwise orthogonal rays.
- A **frame function** is a map f from rays to ℚ such that f(a) + f(b) + f(c) = 1 for every orthogonal frame (a, b, c).
- f is **quadratic** (Born) if there is a Hermitian 3×3 matrix ρ over K, of trace 1, with f(K·v) = ⟨v, ρ v⟩ / ⟨v, v⟩ for every v ≠ 0.

## What the repository already proves

- `BornFable.RationalSphere.parity_frame_function` and `parity_not_quadratic`, in `lean4/BornRationalSphereObstruction.lean` (included below). On primitive integer rays of ℤ³ whose squared norm is a perfect square, exactly one coordinate is odd. The 0/1 "last coordinate odd" function is additive on orthogonal frames, and no rational symmetric form represents it. So over the **real** rational sphere the frame-function route to Gleason is obstructed.
- `lean4/GleasonRationalPlane.lean` (included below): in dimension 2 there is a binary non-quadratic frame function on ℚ².
- The Gaussian-rational field is available as `BornFable.GaussRat` (`lean4/BornGaussRat.lean`, included below), together with its star ring structure.
- With **effect additivity** assumed, the repository already kernel-checks the Born rule over Gaussian-rational Hermitian matrices. This problem is about the **projection-only (frame-function) route**, without effect additivity.

## The question

Over K = ℚ(i) in dimension 3, is every frame function on rays quadratic?

Decide it, and prove your answer in Lean 4. Either outcome is a result for this project.
- **(A) Obstruction.** Construct an explicit frame function on Gaussian-rational rays of K³, and prove (1) frame additivity over every orthogonal frame and (2) that no Hermitian trace-one ρ over K represents it. A natural route is to adapt the parity argument to primitive Gaussian-integer vectors, for example using norms and congruences modulo (1+i) powers. Check carefully which rays exist, because non-real frames are allowed here.
- **(B) Uniqueness.** If no such function exists, prove that every frame function on K³ rays is quadratic. This would contradict the expectation set by the ℚ³ case, so double-check before claiming it.

If neither (A) nor (B) can be completed, prove the largest honest finite piece. Examples: additivity on a stated infinite family of frames, or a non-representability lemma. State exactly what is missing.

## Deliverable format

1. **A short mathematical argument,** in plain prose, first.
2. **One or more complete Lean files.** Each goes in a fenced block whose first line is `-- FILE: lean4/<Name>.lean`. Suggested name: `lean4/BornGaussianRationalFrameObstruction.lean`.
   - Target: Lean `4.35.0` with Mathlib `v4.35.0` (sha `56a005855ea17e0b0958f73ec801ae140b0a1679`).
   - You may `import` the included repository files by module name, e.g. `import BornRationalSphereObstruction`.
   - **Forbidden:** `sorry`, `admit`, `axiom`, `native_decide`, `unsafe`. The host rejects any file that contains them, and requires `#print axioms` to show only `propext`, `Classical.choice`, `Quot.sound`.
   - End each file with `#print axioms` lines for its main theorems.
3. **A final section "WHAT IS PROVED".** State exactly the theorem(s) the Lean establishes, in one or two sentences each, and anything left unproved. Do not overstate. The host compares this section with the compiled statements.
