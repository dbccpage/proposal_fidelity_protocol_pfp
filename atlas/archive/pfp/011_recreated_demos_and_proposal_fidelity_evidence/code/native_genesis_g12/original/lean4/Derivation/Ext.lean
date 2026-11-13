import Derivation.Basic

/-!
# Membership extensionality

The Python model's admitted instance/rule/requirement collections are
sets; the Lean model uses deduplicated lists.  This module proves that the
gap is semantically empty: under the membership-extensional relation
`RegimeExt`, every observable of the development — derivability, context
well-formedness, collapse, separability, stepping, delta application, and
response validity — transports.  Two list representations of the same
admitted sets are `RegimeExt`, so no exported claim depends on list order
or representation.  The bridge claim is therefore: erasure simulation
(`Derivation/Erasure.lean`) **plus** membership extensionality — never
exactness of a particular list representation.
-/

namespace Derivation

/-- Membership-extensional equality of list-represented sets. -/
def SetEq {α : Type} (l1 l2 : List α) : Prop := ∀ x, x ∈ l1 ↔ x ∈ l2

theorem SetEq.rfl' {α : Type} (l : List α) : SetEq l l :=
  fun _ => Iff.rfl

theorem SetEq.symm' {α : Type} {l1 l2 : List α} (h : SetEq l1 l2) :
    SetEq l2 l1 := fun x => (h x).symm

theorem SetEq.insertNew' {α : Type} [DecidableEq α] {l1 l2 : List α}
    (h : SetEq l1 l2) (a : α) :
    SetEq (insertNew l1 a) (insertNew l2 a) := by
  intro x
  rw [mem_insertNew, mem_insertNew, h x]

/-- Regimes with equal data counts and form tables whose admitted
instance, rule, and requirement collections agree as sets. -/
def RegimeExt (r s : Regime) : Prop :=
  r.data = s.data ∧ r.forms = s.forms ∧ SetEq r.insts s.insts ∧
  SetEq r.rules s.rules ∧ SetEq r.reqs s.reqs

theorem RegimeExt.refl' (r : Regime) : RegimeExt r r :=
  ⟨rfl, rfl, SetEq.rfl' _, SetEq.rfl' _, SetEq.rfl' _⟩

theorem RegimeExt.symm' {r s : Regime} (h : RegimeExt r s) :
    RegimeExt s r :=
  ⟨h.1.symm, h.2.1.symm, SetEq.symm' h.2.2.1, SetEq.symm' h.2.2.2.1,
   SetEq.symm' h.2.2.2.2⟩

/-- Derivability is membership-extensional. -/
theorem derivable_ext {r s : Regime} (h : RegimeExt r s) (i : Inst) :
    derivable r i ↔ derivable s i :=
  or_congr (h.2.2.1 i) (h.2.2.2.1 i.1)

/-- Context well-formedness is membership-extensional (it reads only the
data count and the form table). -/
theorem wfCtx_ext {r s : Regime} (h : RegimeExt r s) (c : Ctx) :
    wfCtx r c ↔ wfCtx s c := by
  unfold wfCtx
  rw [h.1, h.2.1]

/-- Collapse is membership-extensional. -/
theorem collapsed_ext {r s : Regime} (h : RegimeExt r s) (d d' : Nat) :
    collapsed r d d' ↔ collapsed s d d' := by
  constructor
  · intro hc c hwf
    have h1 := hc c ((wfCtx_ext h c).mpr hwf)
    exact ((derivable_ext h _).symm.trans h1).trans (derivable_ext h _)
  · intro hc c hwf
    have h1 := hc c ((wfCtx_ext h c).mp hwf)
    exact ((derivable_ext h _).trans h1).trans
      (derivable_ext h _).symm

/-- Separability is membership-extensional. -/
theorem separable_ext {r s : Regime} (h : RegimeExt r s) (d d' : Nat) :
    separable r d d' ↔ separable s d d' := by
  constructor
  · intro ⟨c, hwf, hne⟩
    refine ⟨c, (wfCtx_ext h c).mp hwf, fun hiff => hne ?_⟩
    exact ((derivable_ext h _).trans hiff).trans
      (derivable_ext h _).symm
  · intro ⟨c, hwf, hne⟩
    refine ⟨c, (wfCtx_ext h c).mpr hwf, fun hiff => hne ?_⟩
    exact ((derivable_ext h _).symm.trans hiff).trans (derivable_ext h _)

/-- Extensional relation on optional regimes. -/
def OptExt : Option Regime → Option Regime → Prop
  | some a, some b => RegimeExt a b
  | none, none => True
  | _, _ => False

/-- Delta application is membership-extensional, item by item. -/
theorem applyItem_ext {r s : Regime} (h : RegimeExt r s) (it : Item) :
    OptExt (applyItem r it) (applyItem s it) := by
  cases it with
  | newDatum =>
      exact ⟨by simp [h.1], h.2.1, h.2.2.1, h.2.2.2.1, h.2.2.2.2⟩
  | newForm a =>
      by_cases h1 : 1 ≤ a
      · simp only [applyItem, if_pos h1]
        exact ⟨h.1, by rw [h.2.1], h.2.2.1, h.2.2.2.1, h.2.2.2.2⟩
      · simp only [applyItem, if_neg h1]
        trivial
  | newInst f args =>
      have hcond : (f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
          (∀ x ∈ args, x < r.data)) ↔
          (f < s.forms.length ∧ args.length = s.forms.getD f 0 ∧
          (∀ x ∈ args, x < s.data)) := by
        rw [h.1, h.2.1]
      by_cases h1 : f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
          (∀ x ∈ args, x < r.data)
      · simp only [applyItem, if_pos h1, if_pos (hcond.mp h1)]
        exact ⟨h.1, h.2.1, SetEq.insertNew' h.2.2.1 _, h.2.2.2.1,
          h.2.2.2.2⟩
      · simp only [applyItem, if_neg h1,
          if_neg (fun hc => h1 (hcond.mpr hc))]
        trivial
  | newRuleAll f =>
      have hcond : f < r.forms.length ↔ f < s.forms.length := by
        rw [h.2.1]
      by_cases h1 : f < r.forms.length
      · simp only [applyItem, if_pos h1, if_pos (hcond.mp h1)]
        exact ⟨h.1, h.2.1, h.2.2.1, SetEq.insertNew' h.2.2.2.1 _,
          h.2.2.2.2⟩
      · simp only [applyItem, if_neg h1,
          if_neg (fun hc => h1 (hcond.mpr hc))]
        trivial

/-- Delta application is membership-extensional. -/
theorem applyDelta_ext {r s : Regime} (h : RegimeExt r s)
    (δ : List Item) : OptExt (applyDelta r δ) (applyDelta s δ) := by
  induction δ generalizing r s with
  | nil => exact h
  | cons it rest ih =>
      have hstep := applyItem_ext h it
      unfold applyDelta
      cases hr : applyItem r it with
      | none =>
          cases hs : applyItem s it with
          | none => simp [List.foldlM, hr, hs]; trivial
          | some s1 => rw [hr, hs] at hstep; exact absurd hstep id
      | some r1 =>
          cases hs : applyItem s it with
          | none => rw [hr, hs] at hstep; exact absurd hstep id
          | some s1 =>
              rw [hr, hs] at hstep
              simp only [List.foldlM, hr, hs]
              exact ih hstep

/-- Response validity is membership-extensional: the bridge-relevant
corollary.  Any two list representations of the same admitted sets accept
exactly the same responses. -/
theorem validResponse_ext {r s : Regime} (h : RegimeExt r s)
    (i j : Nat) (δ : List Item) :
    validResponse r i j δ ↔ validResponse s i j δ := by
  constructor
  · intro ⟨t, happ, hsep, hreqs⟩
    have hd := applyDelta_ext h δ
    rw [happ] at hd
    cases hs : applyDelta s δ with
    | none => rw [hs] at hd; exact absurd hd id
    | some t' =>
        rw [hs] at hd
        refine ⟨t', hs, (separable_ext hd i j).mp hsep, ?_⟩
        intro q hq
        exact (separable_ext hd q.1 q.2).mp
          (hreqs q ((h.2.2.2.2 q).mpr hq))
  · intro ⟨t, happ, hsep, hreqs⟩
    have hd := applyDelta_ext (RegimeExt.symm' h) δ
    rw [happ] at hd
    cases hr : applyDelta r δ with
    | none => rw [hr] at hd; exact absurd hd id
    | some t' =>
        rw [hr] at hd
        refine ⟨t', hr, (separable_ext hd i j).mp hsep, ?_⟩
        intro q hq
        exact (separable_ext hd q.1 q.2).mp
          (hreqs q ((h.2.2.2.2 q).mp hq))

end Derivation
