import Derivation.Basic

/-!
# Challenge 0-2 theorems

Inertia of the initial state, supply/admission separation, total
observational collapse before any judgment form, and the non-increase
countermodel.
-/

namespace Derivation

/-- The genesis regime: nothing admitted. -/
def genesis : Regime := ⟨0, [], [], [], []⟩

/-- A bare supply changes no admitted state (supply is not admission). -/
theorem supply_no_op (r : Regime) (t : Nat) :
    stepE r (.supply t) = some r := rfl

/-- Nothing is derivable at genesis. -/
theorem genesis_underivable (i : Inst) : ¬ derivable genesis i := by
  intro h
  cases h with
  | inl h => cases h
  | inr h => cases h

/-- Nothing is derivable in any regime with no instances and no rules;
in particular no successor is generated internally: the only state
changes in the model are indexed by external events (`stepE`). -/
theorem underivable_of_empty (r : Regime) (hi : r.insts = [])
    (hr : r.rules = []) (i : Inst) : ¬ derivable r i := by
  intro h
  cases h with
  | inl h => rw [hi] at h; cases h
  | inr h => rw [hr] at h; cases h

/-- Key collapse lemma: with no admitted instances, derivability depends
only on the form, hence every pair of data is observationally collapsed
(uniform rules cannot separate). -/
theorem collapsed_of_no_insts (r : Regime) (hi : r.insts = [])
    (d d' : Nat) : collapsed r d d' := by
  intro c _
  constructor <;> intro h <;>
    cases h with
    | inl h => rw [hi] at h; cases h
    | inr h => exact Or.inr h

/-- Challenge 2 (reading L): the two admitted, externally distinct data are
observationally collapsed. -/
theorem R2L_collapsed : collapsed R2L 0 1 :=
  collapsed_of_no_insts R2L rfl 0 1

/-- Challenge 2 (reading F): all three pairs are collapsed. -/
theorem R2F_collapsed (d d' : Nat) : collapsed R2F d d' :=
  collapsed_of_no_insts R2F rfl d d'

/-- The recorded Challenge 0-3 history of reading L replays exactly to the
Challenge 3 regime (replayability of the admitted state). -/
theorem historyL_replays :
    replayE
      [.supply 0, .supply 1, .supply 1, .supply 2,
       .admitDatum, .admitDatum, .impose 0 1] genesis = some R2L := by
  decide

/-- Reading F likewise. -/
theorem historyF_replays :
    replayE
      [.supply 0, .admitDatum, .supply 1, .supply 1, .supply 2,
       .admitDatum, .admitDatum, .impose 1 2] genesis = some R2F := by
  decide

/-- Non-increase countermodel: admitting a fresh datum is a real admission
(the state changes) yet the previously collapsed pair stays collapsed —
a new external inscription does not necessarily increase internal
expressive power. -/
theorem admission_without_expressive_increase :
    ∃ s, stepE R2L .admitDatum = some s ∧ s ≠ R2L ∧ collapsed s 0 1 := by
  refine ⟨⟨3, [], [], [], [(0, 1)]⟩, by decide, by decide, ?_⟩
  exact collapsed_of_no_insts _ rfl 0 1

/-- Replay is compositional: a history extended by one event replays by
stepping the replayed prefix. -/
theorem replayE_append (h : List Event) (e : Event) (base : Regime) :
    replayE (h ++ [e]) base =
      (replayE h base).bind (fun r => stepE r e) := by
  unfold replayE
  induction h generalizing base with
  | nil =>
      cases hse : stepE base e <;> simp [List.foldlM, hse]
  | cons x xs ih =>
      simp only [List.cons_append, List.foldlM]
      cases stepE base x <;> simp [ih]

end Derivation
