/-!
Primitive difference quotient kernel for PO-001.

This file records the minimum data needed for the zero-difference relation,
the quotient by that relation, and the condition under which `δ` and invariant
observations descend to the quotient.

AuthorityEffect: None.
-/

namespace OmegaCore

universe u v w z

structure PrimitiveDifference (α : Type u) (β : Type v) where
  δ : α → α → β
  Zero : β → Prop
  zero_refl : ∀ x : α, Zero (δ x x)
  zero_symm : ∀ x y : α, Zero (δ x y) → Zero (δ y x)
  zero_trans : ∀ x y z : α, Zero (δ x y) → Zero (δ y z) → Zero (δ x z)

abbrev DifferenceKernel := PrimitiveDifference

namespace PrimitiveDifference

variable {α : Type u} {β : Type v} {γ η : Type w} {κ : Type z}

def ZeroRel (P : PrimitiveDifference α β) (x y : α) : Prop :=
  P.Zero (P.δ x y)

theorem zeroRel_refl (P : PrimitiveDifference α β) :
    ∀ x : α, P.ZeroRel x x :=
  P.zero_refl

theorem zeroRel_symm (P : PrimitiveDifference α β) :
    ∀ {x y : α}, P.ZeroRel x y → P.ZeroRel y x :=
  fun {x y} => P.zero_symm x y

theorem zeroRel_trans (P : PrimitiveDifference α β) :
    ∀ {x y z : α}, P.ZeroRel x y → P.ZeroRel y z → P.ZeroRel x z :=
  fun {x y z} => P.zero_trans x y z

theorem zeroRel_equivalence (P : PrimitiveDifference α β) :
    Equivalence P.ZeroRel where
  refl := zeroRel_refl P
  symm := zeroRel_symm P
  trans := zeroRel_trans P

def zeroSetoid (P : PrimitiveDifference α β) : Setoid α where
  r := P.ZeroRel
  iseqv := zeroRel_equivalence P

def ResidualQuotient (P : PrimitiveDifference α β) : Type u :=
  Quotient (zeroSetoid P)

def classOf (P : PrimitiveDifference α β) (x : α) : P.ResidualQuotient :=
  Quotient.mk (zeroSetoid P) x

theorem classOf_eq_of_zero
    (P : PrimitiveDifference α β) {x y : α} (hxy : P.ZeroRel x y) :
    P.classOf x = P.classOf y :=
  Quotient.sound hxy

theorem classOf_eq_iff_zeroRel
    (P : PrimitiveDifference α β) {x y : α} :
    P.classOf x = P.classOf y ↔ P.ZeroRel x y := by
  constructor
  · exact Quotient.exact
  · exact classOf_eq_of_zero P

def InvariantCongruent (P : PrimitiveDifference α β) (φ : α → γ) : Prop :=
  ∀ x y : α, P.ZeroRel x y → φ x = φ y

def invariantFactor
    (P : PrimitiveDifference α β) (φ : α → γ)
    (hcongr : P.InvariantCongruent φ) :
    P.ResidualQuotient → γ :=
  Quotient.lift
    (s := zeroSetoid P)
    φ
    (by
      intro x y hxy
      exact hcongr x y hxy)

theorem invariantFactor_classOf
    (P : PrimitiveDifference α β) (φ : α → γ)
    (hcongr : P.InvariantCongruent φ) (x : α) :
    P.invariantFactor φ hcongr (P.classOf x) = φ x :=
  rfl

theorem invariantFactor_requires_congruence
    (P : PrimitiveDifference α β) (φ : α → γ)
    (F : P.ResidualQuotient → γ)
    (hF : ∀ x : α, F (P.classOf x) = φ x) :
    P.InvariantCongruent φ := by
  intro x y hxy
  calc
    φ x = F (P.classOf x) := (hF x).symm
    _ = F (P.classOf y) := by
      rw [classOf_eq_of_zero P hxy]
    _ = φ y := hF y

theorem invariantFactor_exists_iff_invariantCongruent
    (P : PrimitiveDifference α β) (φ : α → γ) :
    (∃ F : P.ResidualQuotient → γ,
        ∀ x : α, F (P.classOf x) = φ x)
      ↔ P.InvariantCongruent φ := by
  constructor
  · intro h
    rcases h with ⟨F, hF⟩
    exact invariantFactor_requires_congruence P φ F hF
  · intro hcongr
    exact ⟨P.invariantFactor φ hcongr, invariantFactor_classOf P φ hcongr⟩

theorem invariantFactor_no_factor_of_not_invariant
    (P : PrimitiveDifference α β) (φ : α → γ)
    (hφ : ¬ P.InvariantCongruent φ) :
    ¬ (∃ F : P.ResidualQuotient → γ,
        ∀ x : α, F (P.classOf x) = φ x) := by
  intro h
  exact hφ ((invariantFactor_exists_iff_invariantCongruent P φ).mp h)

end PrimitiveDifference

end OmegaCore
