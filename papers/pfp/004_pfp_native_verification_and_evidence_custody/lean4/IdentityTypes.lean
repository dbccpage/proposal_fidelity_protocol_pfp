/-!
# Homotopy Type Theory Identity Types and Primitive Difference for Paper 032

Formalizes:
1. Constructive identity paths in HoTT: refl, sym, trans, and path inversion involution.
2. The nullary Primitive Difference structure (δ, Zero) satisfying equivalence axioms.
3. Residual quotient construction and canonical quotient equality.
4. Contrast with continuous cancellation: constructive identity requires a path witness,
   not an inner-product zeroing.
-/

namespace SymbolGame

universe u v

/-- Constructive identity path between two elements of type α. -/
inductive IdentityPath {α : Type u} : α → α → Type u where
  | refl (a : α) : IdentityPath a a

/-- Symmetry (path inversion): (a = b) → (b = a). -/
def symm {α : Type u} {a b : α} (p : IdentityPath a b) : IdentityPath b a :=
  match p with
  | .refl _ => .refl a

/-- Transitivity (path concatenation): (a = b) → (b = c) → (a = c). -/
def trans {α : Type u} {a b c : α} (p : IdentityPath a b) (q : IdentityPath b c) : IdentityPath a c :=
  match p, q with
  | .refl _, .refl _ => .refl a

/-- Involution of symmetry: (p⁻¹)⁻¹ = p. -/
theorem symm_symm {α : Type u} {a b : α} (p : IdentityPath a b) :
    symm (symm p) = p := by
  cases p
  rfl

/-- Action on paths: ap_f(p) : f(a) = f(b). -/
def ap {α : Type u} {β : Type v} (f : α → β) {a b : α} (p : IdentityPath a b) : IdentityPath (f a) (f b) :=
  match p with
  | .refl _ => .refl (f a)

/-- The Primitive Difference structure (δ, Zero) over carrier α valued in β. -/
structure PrimitiveDifference (α : Type u) (β : Type v) where
  δ : α → α → β
  Zero : β → Prop
  zero_refl : ∀ x : α, Zero (δ x x)
  zero_symm : ∀ x y : α, Zero (δ x y) → Zero (δ y x)
  zero_trans : ∀ x y z : α, Zero (δ x y) → Zero (δ y z) → Zero (δ x z)

namespace PrimitiveDifference

variable {α : Type u} {β : Type v}

/-- The zero-difference relation: ZeroRel x y := Zero (δ x y). -/
def ZeroRel (P : PrimitiveDifference α β) (x y : α) : Prop :=
  P.Zero (P.δ x y)

/-- Equivalence proof for ZeroRel. -/
theorem zeroRel_equivalence (P : PrimitiveDifference α β) :
    Equivalence P.ZeroRel where
  refl x := P.zero_refl x
  symm h := P.zero_symm _ _ h
  trans h1 h2 := P.zero_trans _ _ _ h1 h2

/-- Setoid structure induced by Primitive Difference. -/
def toSetoid (P : PrimitiveDifference α β) : Setoid α where
  r := P.ZeroRel
  iseqv := zeroRel_equivalence P

/-- The Residual Quotient type A / ZeroRel. -/
def ResidualQuotient (P : PrimitiveDifference α β) : Type u :=
  Quotient (toSetoid P)

/-- Canonical projection of an element into the residual quotient. -/
def classOf (P : PrimitiveDifference α β) (x : α) : ResidualQuotient P :=
  Quotient.mk (toSetoid P) x

/-- Quotient equality theorem: zero difference yields equal quotient classes. -/
theorem classOf_eq_of_zero (P : PrimitiveDifference α β) {x y : α} (h : P.ZeroRel x y) :
    classOf P x = classOf P y :=
  Quotient.sound h

end PrimitiveDifference

end SymbolGame
