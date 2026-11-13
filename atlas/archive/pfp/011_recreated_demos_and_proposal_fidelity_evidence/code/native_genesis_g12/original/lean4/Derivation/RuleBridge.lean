import Derivation.Progress
import Derivation.TransitionTransport
import Derivation.Minimality

/-!
# The delta-level rule-removal bridge (R4)

Residual R4 in `paper.md` section 12 is kind (b):
`separable_of_subrules` proves witness transfer under a shrunken final
rule set, and the step from delta ITEMS to shrunken rule sets was
certified computationally (`test_rule_never_appears_in_minimum_responses`),
not proved.  This module supplies the bridge, at the item level, which
is what the pruning actually uses.

## Why the bridge is definitional rather than combinatorial

Reading `applyItem`: no guard of any item reads the `rules` field, and
only the `newRuleAll` constructor writes it.  So the evolution of
`data`, `forms`, `insts` and `reqs` under a delta is entirely
independent of the rule store: dropping every rule item from a delta
yields a delta that applies over ANY replacement rule field and
produces the identical regime except for `rules`.  The master lemma
`applyDelta_dropRules` states exactly that, parametrized by an
arbitrary replacement — the subset condition enters only at the final
`separable_of_subrules` call, through rule monotonicity, never through
the induction.

## The corollary the enumeration uses

A valid response containing a uniform-rule item is never a minimum
under either declared measure: dropping its rule items leaves a valid
response that is strictly shorter (`mu1` decreases) with unchanged
new-form arity sum (so `mu2` decreases lexicographically).  This
discharges part (ii) of `CL-PRUNE-RULE`.
-/

namespace Derivation

/-- Drop every uniform-rule item from a delta. -/
def dropRules : List Item → List Item
  | [] => []
  | .newRuleAll _ :: rest => dropRules rest
  | it :: rest => it :: dropRules rest

/-- Admission never removes a rule. -/
theorem applyItem_rules_mono {r s : Regime} {it : Item}
    (h : applyItem r it = some s) : ∀ g ∈ r.rules, g ∈ s.rules := by
  cases it with
  | newDatum =>
    injection h with h
    subst h
    exact fun g hg => hg
  | newForm a =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      exact fun g hg => hg
    · exact nomatch h
  | newInst fm args =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      exact fun g hg => hg
    · exact nomatch h
  | newRuleAll f =>
    simp only [applyItem] at h
    split at h
    · injection h with h
      subst h
      exact fun g hg => mem_insertNew.mpr (Or.inl hg)
    · exact nomatch h

theorem applyDelta_rules_mono {δ : List Item} :
    ∀ {r s : Regime}, applyDelta r δ = some s →
      ∀ g ∈ r.rules, g ∈ s.rules := by
  induction δ with
  | nil =>
    intro r s h
    injection h with h
    subst h
    exact fun g hg => hg
  | cons it rest ih =>
    intro r s h
    rw [applyDelta_cons] at h
    cases happ : applyItem r it with
    | none =>
      rw [happ] at h
      exact nomatch h
    | some r1 =>
      rw [happ] at h
      exact fun g hg => ih h g (applyItem_rules_mono happ g hg)

/-- **The bridge, master form.**  Dropping the rule items of a delta
yields a delta that applies over ANY replacement rule field and
produces the identical regime except for `rules`, which stays at the
replacement.  Parametrizing by `rs` keeps the induction invariant
fixed; the subset condition never enters here. -/
theorem applyDelta_dropRules {δ : List Item} :
    ∀ {r s : Regime} (rs : List Nat), applyDelta r δ = some s →
      applyDelta ⟨r.data, r.forms, r.insts, rs, r.reqs⟩ (dropRules δ)
        = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩ := by
  induction δ with
  | nil =>
    intro r s rs h
    injection h with h
    subst h
    rfl
  | cons it rest ih =>
    intro r s rs h
    rw [applyDelta_cons] at h
    cases it with
    | newDatum =>
      have h' : applyDelta { r with data := r.data + 1 } rest = some s := h
      show applyDelta ⟨r.data, r.forms, r.insts, rs, r.reqs⟩
          (Item.newDatum :: dropRules rest)
        = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩
      rw [applyDelta_cons]
      exact ih rs h'
    | newForm a =>
      simp only [applyItem] at h
      split at h
      next hg =>
        have h' : applyDelta { r with forms := r.forms ++ [a] } rest
            = some s := h
        show applyDelta ⟨r.data, r.forms, r.insts, rs, r.reqs⟩
            (Item.newForm a :: dropRules rest)
          = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩
        rw [applyDelta_cons]
        show (if 1 ≤ a then
            some (⟨r.data, r.forms ++ [a], r.insts, rs, r.reqs⟩ : Regime)
          else none).bind
            (fun s1 => applyDelta s1 (dropRules rest))
          = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩
        rw [if_pos hg]
        exact ih rs h'
      next =>
        have hnone : (none : Option Regime) = some s := by
          exact h
        exact nomatch hnone
    | newInst fm args =>
      simp only [applyItem] at h
      split at h
      next hg =>
        have h' : applyDelta
            { r with insts := insertNew r.insts (fm, args) } rest
            = some s := h
        show applyDelta ⟨r.data, r.forms, r.insts, rs, r.reqs⟩
            (Item.newInst fm args :: dropRules rest)
          = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩
        rw [applyDelta_cons]
        show (if fm < r.forms.length ∧ args.length = r.forms.getD fm 0 ∧
              (∀ x ∈ args, x < r.data) then
            some (⟨r.data, r.forms, insertNew r.insts (fm, args), rs,
              r.reqs⟩ : Regime)
          else none).bind
            (fun s1 => applyDelta s1 (dropRules rest))
          = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩
        rw [if_pos hg]
        exact ih rs h'
      next =>
        have hnone : (none : Option Regime) = some s := by
          exact h
        exact nomatch hnone
    | newRuleAll f =>
      simp only [applyItem] at h
      split at h
      next hg =>
        have h' : applyDelta
            { r with rules := insertNew r.rules f } rest = some s := h
        show applyDelta ⟨r.data, r.forms, r.insts, rs, r.reqs⟩
            (dropRules rest)
          = some ⟨s.data, s.forms, s.insts, rs, s.reqs⟩
        exact ih (r := { r with rules := insertNew r.rules f }) rs h'
      next =>
        have hnone : (none : Option Regime) = some s := by
          exact h
        exact nomatch hnone

/-! ## Cost accounting for the drop -/

theorem dropRules_length_le (δ : List Item) :
    (dropRules δ).length ≤ δ.length := by
  induction δ with
  | nil => exact Nat.le_refl _
  | cons it rest ih =>
    cases it with
    | newRuleAll f =>
      exact Nat.le_trans ih (Nat.le_succ _)
    | newDatum => exact Nat.succ_le_succ ih
    | newForm a => exact Nat.succ_le_succ ih
    | newInst fm args => exact Nat.succ_le_succ ih

theorem dropRules_length_lt {δ : List Item} {f : Nat}
    (h : Item.newRuleAll f ∈ δ) :
    (dropRules δ).length < δ.length := by
  induction δ with
  | nil => exact nomatch h
  | cons it rest ih =>
    cases it with
    | newRuleAll g =>
      exact Nat.lt_succ_of_le (dropRules_length_le rest)
    | newDatum =>
      have : Item.newRuleAll f ∈ rest := by
        rcases List.mem_cons.mp h with he | hm
        · exact nomatch he
        · exact hm
      exact Nat.succ_lt_succ (ih this)
    | newForm a =>
      have : Item.newRuleAll f ∈ rest := by
        rcases List.mem_cons.mp h with he | hm
        · exact nomatch he
        · exact hm
      exact Nat.succ_lt_succ (ih this)
    | newInst fm args =>
      have : Item.newRuleAll f ∈ rest := by
        rcases List.mem_cons.mp h with he | hm
        · exact nomatch he
        · exact hm
      exact Nat.succ_lt_succ (ih this)

/-- Dropping rule items never changes the new-form arity sum: `mu2`'s
second component is blind to the drop. -/
theorem aritySum_dropRules (δ : List Item) :
    aritySum (dropRules δ) = aritySum δ := by
  induction δ with
  | nil => rfl
  | cons it rest ih =>
    cases it with
    | newRuleAll f =>
      show aritySum (dropRules rest) = aritySum rest
      exact ih
    | newDatum => exact ih
    | newForm a =>
      show a + aritySum (dropRules rest) = a + aritySum rest
      rw [ih]
    | newInst fm args => exact ih

/-! ## The validity transfer, and the pruning corollary -/

/-- **R4.**  Dropping the rule items of a valid response leaves a valid
response: the bridge feeds `separable_of_subrules` with the subset
condition supplied by rule monotonicity. -/
theorem validResponse_dropRules {r : Regime} {i j : Nat} {δ : List Item}
    (h : validResponse r i j δ) : validResponse r i j (dropRules δ) := by
  obtain ⟨s, hs, hsep, hall⟩ := h
  have hbridge := applyDelta_dropRules (rs := r.rules) hs
  have hsub : ∀ g ∈ r.rules, g ∈ s.rules := applyDelta_rules_mono hs
  refine ⟨⟨s.data, s.forms, s.insts, r.rules, s.reqs⟩, hbridge, ?_, ?_⟩
  · exact separable_of_subrules s r.rules hsub i j hsep
  · intro q hq
    exact separable_of_subrules s r.rules hsub q.1 q.2 (hall q hq)

/-- **The pruning corollary discharged: a delta containing a
uniform-rule item is never a minimum valid response.**  Its rule-free
drop is valid, strictly shorter (`mu1` decreases), and has the same
new-form arity sum (`mu2` decreases lexicographically). -/
theorem rule_item_never_minimal {r : Regime} {i j : Nat} {δ : List Item}
    {f : Nat} (hf : Item.newRuleAll f ∈ δ)
    (h : validResponse r i j δ) :
    validResponse r i j (dropRules δ) ∧
    (dropRules δ).length < δ.length ∧
    aritySum (dropRules δ) = aritySum δ :=
  ⟨validResponse_dropRules h, dropRules_length_lt hf,
    aritySum_dropRules δ⟩

end Derivation
