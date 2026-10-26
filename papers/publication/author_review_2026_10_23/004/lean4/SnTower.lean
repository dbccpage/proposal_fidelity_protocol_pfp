/-!
# The S(n) Tower: Distinction, Rigidity, and Symmetry (Paper 032 §3.3)

Self-contained (Mathlib-free) mechanization of the four carrier-admissibility and
rigidity theorems of Paper 032 §3.3, previously cited only against the sealed
derivation (`sealed-derivation-v1:lean4/Derivation/PrimDiff.lean`). Bringing them
into the package's own Lean makes claims `PO032-C20`..`PO032-C23` machine-checked
here as well.

- Theorem 3.1 (`irrefl_witness_ne`): an irreflexive relation forces witnessed
  endpoint inequality.
- Theorem 3.2 (`no_witness_on_subsingleton`): a subsingleton carrier hosts no
  witnessed irreflexive relation.
- Theorem 3.3 (`oriented_rigid`): the directed cut `D₂` on `Bool` is rigid —
  every endomap preserving and reflecting it is the identity (`Aut(D₂) = {id}`).
- Theorem 3.4 (`swap_is_S2_automorphism`, `symmetric_no_equivariant_classifier`):
  Boolean negation is an `S₂` automorphism, and every classifier invariant under
  it is constant.
-/

namespace SymbolGame

/-- Theorem 3.1. If `r` is irreflexive and `r a b` is witnessed, then `a ≠ b`. -/
theorem irrefl_witness_ne {α : Type} (r : α → α → Prop) (hirr : ∀ x, ¬ r x x)
    {a b : α} (hab : r a b) : a ≠ b := by
  intro h
  subst h
  exact hirr a hab

/-- Theorem 3.2. A subsingleton carrier admits no witnessed irreflexive relation:
`Bool` is therefore the minimal non-empty carrier that can host one. -/
theorem no_witness_on_subsingleton {α : Type} (r : α → α → Prop) (hirr : ∀ x, ¬ r x x)
    (hsub : ∀ x y : α, x = y) (a b : α) : ¬ r a b := by
  intro hab
  have h : a = b := hsub a b
  subst h
  exact hirr a hab

/-- The directed cut `D₂` on `Bool`: the single oriented, irreflexive arc `false → true`. -/
def D2 (x y : Bool) : Prop := x = false ∧ y = true

/-- Theorem 3.3 (`oriented_rigid`). Every endomap of `Bool` preserving and reflecting
`D₂` is the identity: the directed irreflexive cut breaks all permutation symmetry. -/
theorem oriented_rigid (g : Bool → Bool)
    (h : ∀ x y, D2 x y ↔ D2 (g x) (g y)) : ∀ x, g x = x := by
  have hft : D2 (g false) (g true) := (h false true).mp ⟨rfl, rfl⟩
  intro x
  cases x with
  | false => exact hft.1
  | true => exact hft.2

/-- The symmetric link `S₂` on `Bool`: the transposition-invariant distinction `x ≠ y`. -/
def S2 (x y : Bool) : Prop := x ≠ y

/-- Theorem 3.4a. Boolean negation is an automorphism of the symmetric link `S₂`. -/
theorem swap_is_S2_automorphism : ∀ x y, S2 x y ↔ S2 (!x) (!y) := by
  intro x y
  cases x <;> cases y <;> simp [S2]

/-- Theorem 3.4b. Any Boolean classifier invariant under the `S₂` transposition
(`f (!x) = f x`) is constant. -/
theorem symmetric_no_equivariant_classifier (f : Bool → Bool)
    (hinv : ∀ x, f (!x) = f x) : f false = f true := by
  simpa using (hinv false).symm

end SymbolGame
