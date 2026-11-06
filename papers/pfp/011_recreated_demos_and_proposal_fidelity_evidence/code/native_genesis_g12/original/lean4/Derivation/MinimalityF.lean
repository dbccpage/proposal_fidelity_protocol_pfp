import Derivation.Minimality
import Derivation.Mention

/-!
# Uniqueness up to isomorphism under `mu2`, reading F (R5)

Residual R5 in `paper.md` section 12 is kind (c): `mu2_unique` is
proved grammar-wide for reading L, and reading F carried only a
bounded result from engine enumeration.  This module supplies the
grammar-wide F analogue.

The L case tree transfers because it never uses anything about `R2L`
beyond three structural facts, and `R2F` shares the first two verbatim:
both are form-less and instance-less with a singleton requirement list.
Only the third fact — the datum bound on the final match — changes,
from `x < 2` to `x < 3`, giving three terminal cases instead of two.

The new case is the mark on the genesis datum `0`, which sits OUTSIDE
the requirement pair `(1, 2)`.  It is a dead branch, not an
obstruction: the resulting regime's single instance mentions neither
required datum, so the pair stays collapsed — by
`collapsed_of_no_insts` on the instance-less base, transported by
`collapsed_append_unmentioning` (the R3 mention lemma) — and
separability then contradicts the validity hypothesis.  Marking the
genesis datum is simply not a valid response, and the theorem never
has to count it.

Together with `cost1_insufficient_F` (the cost floor) and
`deltaU0F_valid` (existence), this completes the F-side package
matching the L-side claim shape of `CL-3-UNIQUE-MU2-L`.
-/

namespace Derivation

/-- The F-side unary mark on the first required datum: the target of
the uniqueness statement, and the regime `deltaU0F_valid` builds. -/
def U0F : Regime := ⟨3, [1], [(0, [1])], [], [(1, 2)]⟩

/-- The F-side unary mark on the second required datum. -/
def U2F : Regime := ⟨3, [1], [(0, [2])], [], [(1, 2)]⟩

/-- The swap of the two required data, fixing the genesis datum. -/
def swap12 (d : Nat) : Nat :=
  if d = 1 then 2 else if d = 2 then 1 else d

/-- The two required-datum marks are one isomorphism class. -/
def isoU2F_U0F : Iso U2F U0F where
  dmap := swap12
  dinv := swap12
  fmap := id
  finv := id
  dmap_lt := by decide
  dinv_lt := by decide
  dinv_dmap := by decide
  dmap_dinv := by decide
  fmap_lt := by decide
  finv_lt := by decide
  finv_fmap := by decide
  fmap_finv := by decide
  arity := by decide
  insts_fwd := by decide
  insts_bwd := by decide
  rules_fwd := by decide
  rules_bwd := by decide
  reqs_fwd := by decide
  reqs_bwd := by decide

/-- The genesis-datum mark separates nothing the requirement asks
about: its single instance mentions neither datum `1` nor datum `2`,
so the required pair stays collapsed.  This is the R3 mention lemma
doing exactly the work it was proved for. -/
theorem genesis_mark_not_separable :
    ¬ separable (⟨3, [1], [(0, [0])], [], [(1, 2)]⟩ : Regime) 1 2 := by
  intro hsep
  have base : collapsed (⟨3, [1], [], [], [(1, 2)]⟩ : Regime) 1 2 :=
    collapsed_of_no_insts _ rfl 1 2
  have hcol : collapsed (⟨3, [1], [(0, [0])], [], [(1, 2)]⟩ : Regime) 1 2 :=
    (collapsed_append_unmentioning ⟨3, [1], [], [], [(1, 2)]⟩
      [(0, [0])] 1 2 (by decide) (by decide)).mpr base
  exact separable_not_collapsed hsep hcol

/-- **R5.**  Under the refined measure (two items, new-form arity sum
at most one), every valid response to Challenge 3 in reading F
produces a regime isomorphic to the unary mark `U0F` — the exact
analogue of `mu2_unique`, grammar-wide, no engine bound. -/
theorem mu2_unique_F (a b : Item) (hval : validResponse R2F 1 2 [a, b])
    (har : aritySum [a, b] ≤ 1) :
    ∃ s, applyDelta R2F [a, b] = some s ∧ Nonempty (Iso s U0F) := by
  cases hval with
  | intro s hs =>
    have happ := hs.1
    have hsep := hs.2.1
    refine ⟨s, happ, ?_⟩
    rw [applyDelta_pair] at happ
    cases ha : applyItem R2F a with
    | none => rw [ha] at happ; cases happ
    | some r1 =>
      rw [ha] at happ
      have happ2 : applyItem r1 b = some s := happ
      cases a with
      | newInst f args =>
          simp only [applyItem] at ha
          rw [if_neg (by simp [R2F])] at ha
          cases ha
      | newRuleAll f =>
          simp only [applyItem] at ha
          rw [if_neg (by simp [R2F])] at ha
          cases ha
      | newDatum =>
          have hr1 : r1 = ⟨4, [], [], [], [(1, 2)]⟩ :=
            (Option.some.inj ha).symm
          subst hr1
          cases b with
          | newInst f args =>
              simp only [applyItem] at happ2
              rw [if_neg (by simp)] at happ2
              cases happ2
          | newRuleAll f =>
              simp only [applyItem] at happ2
              rw [if_neg (by simp)] at happ2
              cases happ2
          | newDatum =>
              have hz := Option.some.inj happ2
              subst hz
              exact absurd (no_insts_no_separation rfl hsep) id
          | newForm c =>
              simp only [applyItem] at happ2
              split at happ2
              · have hz := Option.some.inj happ2
                subst hz
                exact absurd (no_insts_no_separation rfl hsep) id
              · cases happ2
      | newForm c =>
          have hc1 : 1 ≤ c := by
            cases Nat.lt_or_ge c 1 with
            | inr hge => exact hge
            | inl hlt =>
                exfalso
                simp only [applyItem] at ha
                rw [if_neg (by omega)] at ha
                cases ha
          have hr1 : r1 = ⟨3, [c], [], [], [(1, 2)]⟩ := by
            simp only [applyItem] at ha
            rw [if_pos hc1] at ha
            exact (Option.some.inj ha).symm
          subst hr1
          cases b with
          | newDatum =>
              have hz := Option.some.inj happ2
              subst hz
              exact absurd (no_insts_no_separation rfl hsep) id
          | newForm c' =>
              simp only [applyItem] at happ2
              split at happ2
              · have hz := Option.some.inj happ2
                subst hz
                exact absurd (no_insts_no_separation rfl hsep) id
              · cases happ2
          | newRuleAll f =>
              simp only [applyItem] at happ2
              split at happ2
              · have hz := Option.some.inj happ2
                subst hz
                exact absurd (no_insts_no_separation rfl hsep) id
              · cases happ2
          | newInst f args =>
              have hcsum : c ≤ 1 := by
                have : aritySum [Item.newForm c, Item.newInst f args] = c := by
                  simp [aritySum]
                omega
              have hc : c = 1 := by omega
              subst hc
              simp only [applyItem] at happ2
              split at happ2
              next hcond =>
                have hz := Option.some.inj happ2
                have hf : f = 0 := by
                  have := hcond.1
                  simp at this
                  omega
                subst hf
                have hargs1 : args.length = 1 := by
                  have := hcond.2.1
                  simpa using this
                match args, hargs1 with
                | [x], _ =>
                  have hx3 : x < 3 := by
                    have := hcond.2.2 x (by simp)
                    simpa using this
                  subst hz
                  match x, hx3 with
                  | 0, _ => exact absurd hsep genesis_mark_not_separable
                  | 1, _ => exact ⟨isoRefl U0F (by decide)⟩
                  | 2, _ => exact ⟨isoU2F_U0F⟩
              next => cases happ2

end Derivation
