/-
  The Symbol Game: Formal Involution Laws for Fermion Sign Cancellation.
  AuthorityEffect: None.
-/

namespace SymbolGame001

/-- A discrete sign value in {-1, +1}. -/
inductive Sign : Type
  | neg : Sign
  | pos : Sign
  deriving DecidableEq, Repr

def Sign.toInt : Sign → Int
  | Sign.neg => -1
  | Sign.pos => 1

def Sign.negate : Sign → Sign
  | Sign.neg => Sign.pos
  | Sign.pos => Sign.neg

/-- A finite signed configuration in the carrier manifold. -/
structure SignedConfig where
  id : Nat
  sign : Sign
  weight : Nat
  deriving DecidableEq, Repr

/-- 
  The 4 Involution Laws defining an ExactCancellation witness:
    1. involution_law: xi (xi x) = x
    2. fixed_point_free: xi x != x
    3. sign_reversing: (xi x).sign = x.sign.negate
    4. weight_preserving: (xi x).weight = x.weight
-/
structure InvolutionWitness (α : Type) [DecidableEq α] (sign : α → Sign) (weight : α → Nat) where
  xi : α → α
  involution_law : ∀ x, xi (xi x) = x
  fixed_point_free : ∀ x, xi x ≠ x
  sign_reversing : ∀ x, sign (xi x) = (sign x).negate
  weight_preserving : ∀ x, weight (xi x) = weight x

/-- 
  Pairwise Cancellation Lemma:
  In any paired orbit {x, xi(x)}, the signed sum of weights cancels to zero.
-/
theorem pair_cancellation (x : SignedConfig) (w : InvolutionWitness SignedConfig (fun c => c.sign) (fun c => c.weight)) :
    (x.sign.toInt * (x.weight : Int)) + ((w.xi x).sign.toInt * ((w.xi x).weight : Int)) = 0 := by
  have h_sign := w.sign_reversing x
  have h_weight := w.weight_preserving x
  cases h : x.sign with
  | neg =>
    have hs : (w.xi x).sign = Sign.pos := by
      rw [h_sign, h]
      rfl
    have hs_val : (w.xi x).sign.toInt = 1 := by rw [hs]; rfl
    have h_neg : Sign.neg.toInt = -1 := rfl
    rw [h_neg, hs_val, h_weight]
    omega
  | pos =>
    have hs : (w.xi x).sign = Sign.neg := by
      rw [h_sign, h]
      rfl
    have hs_val : (w.xi x).sign.toInt = -1 := by rw [hs]; rfl
    have h_pos : Sign.pos.toInt = 1 := rfl
    rw [h_pos, hs_val, h_weight]
    omega

end SymbolGame001
