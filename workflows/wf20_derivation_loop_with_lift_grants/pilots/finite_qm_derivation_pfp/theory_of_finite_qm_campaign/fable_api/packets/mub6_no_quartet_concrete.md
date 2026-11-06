---
node_id: MUB6-NO-QUARTET-D6
context_files:
  - lean4/SzollosiCommonRays.lean
  - lean4/SzollosiQuartetSystem.lean
---
# Problem: exclude a concrete Hadamard matrix from every MUB quartet in ℂ⁶

You are working on DAG node `MUB6-NO-QUARTET-D6` ("no four pairwise mutually unbiased bases exist in ℂ⁶", open) in a Lean 4 project. You have no tools. Everything you need is in this message, and your answer will be compiled and audited by the host.

## What the repository already proves

`MUB.SzollosiCommonRays.no_quartet_of_no_unbiased_ray_pair`, in `lean4/SzollosiCommonRays.lean` (included below) with the quartet system of `lean4/SzollosiQuartetSystem.lean` (included below), states the following.

> If no two common rays of a 6×6 complex Hadamard matrix H are unbiased, then H is in no MUB quartet containing the identity.

A **common ray** is a unit vector unbiased to both the standard basis and the columns of H/√6 (see `CommonRay` in the file). Read the exact Lean definitions below and follow them, not this paraphrase.

What is open is to **discharge that hypothesis for a concrete H**. Known external context, which you must not cite as proof:
- The Fourier matrix F₆ and the Szöllősi family are the standard candidates.
- OpenAI's `openai/math` proves N(6) ≤ 5. That is imported as an assumption here and does not decide quartets.
- Jaming–Matolcsi–Móra–Szöllősi–Weiner (2009) studied extensions of F₆ by computer-assisted means.

## The task

Pick a concrete 6×6 complex Hadamard matrix H with exact algebraic entries. **F₆, with entries ω^{jk}, ω = e^{2πi/6}, is the first choice.** Then prove in Lean 4 that no two common rays of H are unbiased, and conclude, using `no_quartet_of_no_unbiased_ray_pair`, that H lies in no MUB quartet containing the identity.

To do it you must:
- characterise or parametrise the common rays of (I, H) exactly. For F₆ the vectors unbiased to I and F₆ have a known structure, and you should derive it;
- show that any two of them have an overlap with |⟨z, w⟩|² ≠ 1/6.

If the full statement is out of reach, prove the largest honest finite piece and state exactly what is missing. Examples:
- the exact parametrisation of the common rays of F₆, as a Lean theorem;
- the exclusion of a stated sub-family;
- a reduction to a finite polynomial-system check together with that check.

Do not replace the claim by a floating-point computation. Every number must be exact: elements of ℚ(√−3), ℚ(ζ₁₂) or ℚ, or Mathlib's `ℂ` with exact algebraic witnesses.

## Deliverable format

1. **A short mathematical argument,** in plain prose, first.
2. **One or more complete Lean files.** Each goes in a fenced block whose first line is `-- FILE: lean4/<Name>.lean`. Suggested name: `lean4/MubFourierSixNoQuartet.lean`.
   - Target: Lean `4.35.0` with Mathlib `v4.35.0` (sha `56a005855ea17e0b0958f73ec801ae140b0a1679`).
   - You may `import SzollosiCommonRays` and `import SzollosiQuartetSystem`.
   - **Forbidden:** `sorry`, `admit`, `axiom`, `native_decide`, `unsafe`. The host rejects any file that contains them, and requires `#print axioms` to show only `propext`, `Classical.choice`, `Quot.sound`.
   - End each file with `#print axioms` lines for its main theorems.
3. **A final section "WHAT IS PROVED".** State exactly the theorem(s) the Lean establishes, and anything left unproved. Do not overstate. The host compares this section with the compiled statements.
