import Derivation.Basic
import Derivation.Inertia

/-!
# Response existence and pruning theorems

* `mark_progress`: in any well-formed regime whose imposed requirements
  are all separated, the fresh-mark response (one fresh unary form, one
  instance on the second target datum) is a valid response to any
  *supplied* separation demand.  Response existence only: this proves
  neither autonomous demand generation nor anything about the length of
  the process.
* `separable_of_subrules`: a separation witness never uses a uniformly
  ruled form, so shrinking the final rule set preserves every separation
  (the delta-level pruning corollary is certified computationally; see
  the theorem docstring).
-/

namespace Derivation

/-- Old instances never mention the fresh form (well-formedness). -/
theorem old_inst_form_lt {r : Regime} (hwf : r.wf) {p : Inst}
    (hp : p ∈ r.insts) : p.1 < r.forms.length :=
  (hwf.1 p hp).1

/-- Appending one element and reading at the old length yields it. -/
theorem getD_concat_self (l : List Nat) (a : Nat) :
    (l ++ [a]).getD l.length 0 = a := by
  induction l with
  | nil => rfl
  | cons x xs ih => simpa using ih

/-- Reading below the old length is unaffected by an append. -/
theorem getD_append_lt (l l' : List Nat) (i : Nat) (h : i < l.length) :
    (l ++ l').getD i 0 = l.getD i 0 := by
  induction l generalizing i with
  | nil => cases h
  | cons x xs ih =>
      cases i with
      | zero => rfl
      | succ n => simpa using ih n (Nat.lt_of_succ_lt_succ h)

/-- Derivability transfers between a regime and its fresh-mark extension
for every instance whose form is not the fresh one. -/
theorem derivable_extend {r : Regime} (hwf : r.wf) (j : Nat) (x : Inst)
    (hx : x.1 ≠ r.forms.length) :
    derivable
      ⟨r.data, r.forms ++ [1], r.insts ++ [(r.forms.length, [j])],
       r.rules, r.reqs⟩ x ↔ derivable r x := by
  unfold derivable
  constructor
  · intro h
    cases h with
    | inl h =>
        cases List.mem_append.mp h with
        | inl h => exact Or.inl h
        | inr h =>
            exfalso
            have : x = (r.forms.length, [j]) := by
              cases h with
              | head => rfl
              | tail _ h => cases h
            exact hx (by rw [this])
    | inr h => exact Or.inr h
  · intro h
    cases h with
    | inl h => exact Or.inl (List.mem_append.mpr (Or.inl h))
    | inr h => exact Or.inr h

/-- The fresh-mark response is always available: it applies, separates the
target, and keeps every imposed requirement separated.  What is proved is
that ONE concrete two-item delta is a valid response under the stated
hypotheses; the statement does not quantify over the candidate grammar,
and no claim about that grammar is made here. -/
theorem mark_progress (r : Regime) (hwf : r.wf) (i j : Nat)
    (hi : i < r.data) (hj : j < r.data) (hij : i ≠ j)
    (hreqs : ∀ q ∈ r.reqs, separable r q.1 q.2) :
    validResponse r i j [.newForm 1, .newInst r.forms.length [j]] := by
  have hfresh : ((r.forms.length, [j]) : Inst) ∉ r.insts := by
    intro hmem
    exact Nat.lt_irrefl _ ((hwf.1 _ hmem).1)
  have happ : applyDelta r [.newForm 1, .newInst r.forms.length [j]] =
      some ⟨r.data, r.forms ++ [1],
            r.insts ++ [(r.forms.length, [j])], r.rules, r.reqs⟩ := by
    have h1 : applyItem r (.newForm 1) =
        some { r with forms := r.forms ++ [1] } := by
      simp only [applyItem]
      rw [if_pos (by omega)]
    have hcond : r.forms.length < (r.forms ++ [1]).length ∧
        ([j] : List Nat).length = (r.forms ++ [1]).getD r.forms.length 0 ∧
        ∀ x ∈ ([j] : List Nat), x < r.data := by
      refine ⟨by simp, ?_, ?_⟩
      · rw [getD_concat_self]
        rfl
      · intro x hx
        have : x = j := by
          cases hx with
          | head => rfl
          | tail _ h => cases h
        subst this
        exact hj
    have h2 : applyItem { r with forms := r.forms ++ [1] }
        (.newInst r.forms.length [j]) =
        some ⟨r.data, r.forms ++ [1],
              r.insts ++ [(r.forms.length, [j])], r.rules, r.reqs⟩ := by
      simp only [applyItem]
      rw [if_pos hcond]
      simp [insertNew_of_not_mem hfresh]
    calc applyDelta r [.newForm 1, .newInst r.forms.length [j]]
        = (applyItem r (.newForm 1)).bind
            (fun r1 => applyItem r1 (.newInst r.forms.length [j])) := by
          unfold applyDelta
          cases hh : applyItem r (.newForm 1) with
          | none => simp [List.foldlM, hh]
          | some r1 =>
              cases hh2 : applyItem r1 (.newInst r.forms.length [j]) <;>
                simp [List.foldlM, hh, hh2]
      _ = _ := by rw [h1]; exact h2
  refine ⟨_, happ, ?_, ?_⟩
  · -- the fresh context separates i from j
    refine ⟨⟨r.forms.length, [none]⟩, ⟨by simp, ?_, by simp, ?_⟩, ?_⟩
    · show ([none] : List (Option Nat)).length =
        (r.forms ++ [1]).getD r.forms.length 0
      rw [getD_concat_self]
      rfl
    · intro sl hsl
      have : sl = none := by
        cases hsl with
        | head => rfl
        | tail _ h => cases h
      rw [this]; trivial
    · intro hiff
      have hderj : derivable
          ⟨r.data, r.forms ++ [1], r.insts ++ [(r.forms.length, [j])],
           r.rules, r.reqs⟩
          (plug ⟨r.forms.length, [none]⟩ j) := by
        show derivable _ (r.forms.length, [j])
        exact Or.inl (List.mem_append.mpr (Or.inr (by simp)))
      have hderi := hiff.mpr hderj
      show False
      have hne : (r.forms.length, [i]) ≠ (r.forms.length, [j]) := by
        intro h
        have := congrArg (fun p => p.2) h
        simp at this
        exact hij this
      cases hderi with
      | inl h =>
          cases List.mem_append.mp h with
          | inl h =>
              have := (hwf.1 _ h).1
              exact absurd this (Nat.lt_irrefl _)
          | inr h =>
              have : ((r.forms.length, [i]) : Inst) =
                  (r.forms.length, [j]) := by
                cases h with
                | head => rfl
                | tail _ h => cases h
              exact hne this
      | inr h =>
          have := hwf.2.1 _ h
          exact absurd this (Nat.lt_irrefl _)
  · -- every imposed requirement stays separated
    intro q hq
    have hsep := hreqs q hq
    cases hsep with
    | intro c hc =>
      have hwfc := hc.1
      have hne := hc.2
      -- the witness form is admitted in `r`, hence not the fresh form
      have hform : c.form ≠ r.forms.length := by
        intro hbad
        exact Nat.lt_irrefl _ (hbad ▸ hwfc.1)
      have hplug : ∀ d, (plug c d).1 ≠ r.forms.length := by
        intro d
        show c.form ≠ r.forms.length
        exact hform
      refine ⟨c, ⟨?_, ?_, hwfc.2.2.1, hwfc.2.2.2⟩, ?_⟩
      · show c.form < (r.forms ++ [1]).length
        have := hwfc.1
        simp
        omega
      · show c.slots.length = (r.forms ++ [1]).getD c.form 0
        rw [getD_append_lt _ _ _ hwfc.1]
        exact hwfc.2.1
      · intro hiff
        apply hne
        constructor
        · intro h
          exact (derivable_extend hwf j _ (hplug q.2)).mp
            (hiff.mp ((derivable_extend hwf j _ (hplug q.1)).mpr h))
        · intro h
          exact (derivable_extend hwf j _ (hplug q.1)).mp
            (hiff.mpr ((derivable_extend hwf j _ (hplug q.2)).mpr h))

/-- A separation witness never inhabits a uniformly ruled form, so
shrinking the final rule set preserves separability.  Precisely this and
no more: the delta-level pruning corollary ("dropping a rule item from a
delta yields a shorter valid delta") additionally needs the fact that
rule items commute out of a delta leaving the same regime with a smaller
rule set; that bridge is certified computationally
(`test_rule_never_appears_in_minimum_responses`), not proved here. -/
theorem separable_of_subrules (s : Regime) (rs' : List Nat)
    (hsub : ∀ g ∈ rs', g ∈ s.rules) (d d' : Nat)
    (h : separable s d d') :
    separable ⟨s.data, s.forms, s.insts, rs', s.reqs⟩ d d' := by
  cases h with
  | intro c hc =>
    have hwfc := hc.1
    have hne := hc.2
    -- the witness form is not ruled: otherwise both sides are derivable
    have hnr : c.form ∉ s.rules := by
      intro hr
      exact hne ⟨fun _ => Or.inr hr, fun _ => Or.inr hr⟩
    have htrans : ∀ x : Inst, x.1 = c.form →
        (derivable ⟨s.data, s.forms, s.insts, rs', s.reqs⟩ x ↔
          derivable s x) := by
      intro x hx
      unfold derivable
      constructor
      · intro h
        cases h with
        | inl h => exact Or.inl h
        | inr h => exact absurd (hsub _ h) (hx ▸ hnr)
      · intro h
        cases h with
        | inl h => exact Or.inl h
        | inr h => exact absurd h (hx ▸ hnr)
    refine ⟨c, hwfc, ?_⟩
    intro hiff
    apply hne
    constructor
    · intro h
      exact (htrans _ rfl).mp (hiff.mp ((htrans _ rfl).mpr h))
    · intro h
      exact (htrans _ rfl).mp (hiff.mpr ((htrans _ rfl).mpr h))

end Derivation
