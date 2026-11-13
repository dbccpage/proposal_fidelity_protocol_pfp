import Derivation.Initiality

/-!
# Horizon: every-stage lawfulness and the budget saturation pin

PR #12 Stage I correction module.  Two audit findings are settled
here, without rewriting the sealed PR #11 modules:

**C6 (horizon lawfulness).**  PR #11 proved quiescence of the
generated run only at the concrete stage 3
(`Represented.worldAt_three_quiescent`), while the claim ledger's
autonomy entry spoke of lawfulness "across extension" citing a
theorem with no lawfulness conjunct.  This module closes the gap
upward: `worldAt_spec` characterizes the complete record of the
generated world at *every* stage by induction, and from it
`worldAt_quiescent`, `worldAt_wf`, and `block_all_accepted` prove
quiescence, well-formedness, and per-event acceptance at every
horizon.  `gen_quiescent` and `gen_wf` lift the results to the
driver's generated run through
`Constitution.driver_reproduces_tower`.

**C10 (cross-language budget exactness).**  The Python mirror of the
family interpreter computed `budget - 1` with unsaturated integer
subtraction, so a `gateBudget`-off descriptor at budget 0 produced a
state (budget `-1`) unrepresentable in the Lean carrier, while Lean
`Nat` subtraction saturates at 0.  The mirror now saturates
(`max(0, budget - 1)`).  The exact shared semantics is pinned here:
`interp_budget_bound` proves that for *every* descriptor and *every*
event the budget field either is unchanged, or is the saturating
decrement `w.budget - 1` (Lean `Nat` subtraction — equal to
`max(0, b - 1)` over the integers), or is set by an explicit
`setBudget n`.  `budget_saturation_noop` pins the audit's exact
countermodel, and `mark_saturation_all_descs` decides it exhaustively
over all 64 descriptors; the Python suite asserts the identical facts
on the same declared basis.
-/

namespace Horizon

open Represented Constitution

/-! ## The generated run, characterized at every stage -/

/-- The view columns of the generated world at stage `k`. -/
def specViews (k : Nat) : List View :=
  (List.range k).map (fun i => [i + 1])

/-- The recorded requirements of the generated world at stage `k`. -/
def specReqs (k : Nat) : List (Nat × Nat) :=
  (List.range k).map (fun i => (0, i + 1))

/-- The complete record of the generated world at stage `k`. -/
def specWorld (k : Nat) : World :=
  { data := List.range (k + 1), views := specViews k,
    reqs := specReqs k, refusals := [], budget := 0,
    augLicensed := true, notes := [] }

/-- Intermediate state 1 of block `k+1`: budget replenished. -/
def w1 (m : Nat) : World :=
  { data := List.range (m + 1), views := specViews m,
    reqs := specReqs m, refusals := [], budget := 1,
    augLicensed := true, notes := [] }

/-- Intermediate state 2: fresh token admitted. -/
def w2 (m : Nat) : World :=
  { data := List.range (m + 1) ++ [m + 1], views := specViews m,
    reqs := specReqs m, refusals := [], budget := 1,
    augLicensed := true, notes := [] }

/-- Intermediate state 3: requirement recorded. -/
def w3 (m : Nat) : World :=
  { data := List.range (m + 1) ++ [m + 1], views := specViews m,
    reqs := specReqs m ++ [(0, m + 1)], refusals := [], budget := 1,
    augLicensed := true, notes := [] }

theorem specViews_succ (m : Nat) :
    specViews (m + 1) = specViews m ++ [[m + 1]] := by
  unfold specViews
  rw [List.range_succ, List.map_append]
  rfl

theorem specReqs_succ (m : Nat) :
    specReqs (m + 1) = specReqs m ++ [(0, m + 1)] := by
  unfold specReqs
  rw [List.range_succ, List.map_append]
  rfl

/-! ### Guard facts on the characterized record -/

theorem fresh_not_mem (m : Nat) :
    ¬ (m + 1 ∈ List.range (m + 1)) := by
  intro h
  exact absurd (List.mem_range.mp h) (by omega)

theorem req_not_mem (m : Nat) :
    ¬ ((0, m + 1) ∈ specReqs m) := by
  intro h
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp h
  have h2 : i + 1 = m + 1 := congrArg Prod.snd heq
  have h3 : i < m := List.mem_range.mp hi
  omega

theorem view_not_mem (m : Nat) :
    ¬ (([m + 1] : View) ∈ specViews m) := by
  intro h
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp h
  have h2 : i + 1 = m + 1 := by
    have := congrArg (fun l : List Nat => l.headD 0) heq
    simpa using this
  have h3 : i < m := List.mem_range.mp hi
  omega

theorem data_len (m : Nat) :
    (List.range (m + 1) ++ [m + 1]).length = m + 2 := by
  simp [List.length_append, List.length_range]

/-- The new column separates the new requirement's endpoints. -/
theorem sep_new_col (m : Nat) : sepB [m + 1] 0 (m + 1) = true := by
  unfold sepB
  rw [decide_eq_false (by
        intro h
        cases List.mem_singleton.mp h),
      decide_eq_true (List.mem_singleton.mpr rfl)]
  rfl

/-- Older columns do not separate the new requirement. -/
theorem old_cols_blind (m : Nat) {c : View} (hc : c ∈ specViews m) :
    sepB c 0 (m + 1) = false := by
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp hc
  have h3 : i < m := List.mem_range.mp hi
  subst heq
  unfold sepB
  rw [decide_eq_false (by
        intro h
        cases List.mem_singleton.mp h),
      decide_eq_false (by
        intro h
        have := List.mem_singleton.mp h
        omega)]
  rfl

/-! ### Step lemmas on explicit guards -/

theorem step_admit_fresh {w : World} {t : Nat} (h : ¬ t ∈ w.data) :
    step w (.admitTok t) = { w with data := w.data ++ [t] } := by
  simp only [step]
  rw [if_neg h]

theorem step_require_ok {w : World} {i j : Nat}
    (h : reqOkB w i j = true) :
    step w (.require i j) = { w with reqs := w.reqs ++ [(i, j)] } := by
  simp only [step]
  rw [if_pos h]

theorem step_addView_ok {w : World} {c : View}
    (h : (augOkB w c && w.augLicensed && decide (0 < w.budget))
      = true) :
    step w (.addView c) =
      { augApply w c with budget := w.budget - 1 } := by
  simp only [step]
  rw [if_pos h]

/-! ### The four guards of block `m + 1` hold at every stage -/

theorem req_guard (m : Nat) : reqOkB (w2 m) 0 (m + 1) = true := by
  show ((0 != m + 1)
      && decide (0 < (List.range (m + 1) ++ [m + 1]).length)
      && decide (m + 1 < (List.range (m + 1) ++ [m + 1]).length)
      && !(decide ((0, m + 1) ∈ specReqs m))) = true
  rw [data_len]
  rw [decide_eq_true (show 0 < m + 2 by omega),
      decide_eq_true (show m + 1 < m + 2 by omega),
      decide_eq_false (req_not_mem m)]
  rfl

theorem satB_w3_false (m : Nat) : satB (w3 m) (0, m + 1) = false := by
  show (specViews m).any (fun c => sepB c 0 (m + 1)) = false
  cases h : (specViews m).any (fun c => sepB c 0 (m + 1)) with
  | false => rfl
  | true =>
      obtain ⟨c, hc, hp⟩ := List.any_eq_true.mp h
      rw [old_cols_blind m hc] at hp
      cases hp

theorem increase_guard (m : Nat) :
    increaseB (w3 m) [m + 1] = true := by
  show (List.range (List.range (m + 1) ++ [m + 1]).length).any
      (fun i => (List.range (List.range (m + 1) ++ [m + 1]).length).any
        fun j => (i != j) && sepB [m + 1] i j && !satB (w3 m) (i, j))
    = true
  rw [data_len]
  apply List.any_eq_true.mpr
  refine ⟨0, List.mem_range.mpr (by omega), ?_⟩
  apply List.any_eq_true.mpr
  refine ⟨m + 1, List.mem_range.mpr (by omega), ?_⟩
  show ((0 != m + 1) && sepB [m + 1] 0 (m + 1)
    && !satB (w3 m) (0, m + 1)) = true
  rw [sep_new_col m, satB_w3_false m]
  rfl

theorem aug_guard (m : Nat) :
    (augOkB (w3 m) [m + 1] && (w3 m).augLicensed
      && decide (0 < (w3 m).budget)) = true := by
  have haug : augOkB (w3 m) [m + 1] = true := by
    show (([m + 1] : View).all
        (fun p => decide (p < (List.range (m + 1) ++ [m + 1]).length))
      && !(decide (([m + 1] : View) ∈ specViews m))
      && increaseB (w3 m) [m + 1]) = true
    have hall : (([m + 1] : View).all
        (fun p => decide (p < (List.range (m + 1) ++ [m + 1]).length)))
        = true := by
      show (decide (m + 1 < (List.range (m + 1) ++ [m + 1]).length)
        && true) = true
      rw [data_len, decide_eq_true (show m + 1 < m + 2 by omega)]
      rfl
    rw [hall, decide_eq_false (view_not_mem m), increase_guard m]
    rfl
  rw [haug]
  rfl

/-- Assembly of the final addView application into the next spec. -/
theorem final_assembly (m : Nat) :
    ({ augApply (w3 m) [m + 1] with budget := (w3 m).budget - 1 })
      = specWorld (m + 1) := by
  show ({ data := List.range (m + 1) ++ [m + 1],
          views := specViews m ++ [[m + 1]],
          reqs := specReqs m ++ [(0, m + 1)], refusals := [],
          budget := 0, augLicensed := true, notes := [] } : World)
    = specWorld (m + 1)
  unfold specWorld
  rw [← List.range_succ, ← specViews_succ, ← specReqs_succ]

/-- **The complete record characterization of the generated run, at
every stage**: carrier `0..k`, one view column and one requirement
per prior stage, empty refusals, budget spent to zero, licensed. -/
theorem worldAt_spec (k : Nat) : worldAt k = specWorld k := by
  induction k with
  | zero => decide
  | succ m ih =>
      have h0 : worldAt (m + 1)
          = replay (blockEvents (m + 1)) (worldAt m) := by
        show replay (histUpTo m ++ blockEvents (m + 1)) genesis = _
        rw [replay_append]
        rfl
      rw [h0, ih]
      show step (step (step (step (specWorld m) (.setBudget 1))
        (.admitTok (m + 1))) (.require 0 (m + 1))) (.addView [m + 1])
        = specWorld (m + 1)
      rw [show step (specWorld m) (.setBudget 1) = w1 m from rfl]
      rw [show step (w1 m) (.admitTok (m + 1)) = w2 m from by
        rw [step_admit_fresh (fresh_not_mem m)]; rfl]
      rw [show step (w2 m) (.require 0 (m + 1)) = w3 m from by
        rw [step_require_ok (req_guard m)]; rfl]
      rw [step_addView_ok (aug_guard m), final_assembly m]

/-! ## C6 closed upward: lawfulness at every horizon -/

/-- **Quiescence at every stage** (previously proved only at stage
3): every recorded requirement of the generated world is satisfied,
at every horizon. -/
theorem worldAt_quiescent (k : Nat) :
    quiescentB (worldAt k) = true := by
  rw [worldAt_spec]
  show (specReqs k).all (fun r => satB (specWorld k) r) = true
  apply List.all_eq_true.mpr
  intro r hr
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp hr
  subst heq
  show (specViews k).any (fun c => sepB c 0 (i + 1)) = true
  apply List.any_eq_true.mpr
  exact ⟨[i + 1], List.mem_map.mpr ⟨i, hi, rfl⟩, sep_new_col i⟩

/-- **Well-formedness at every stage**: recorded requirements are
off-diagonal and in-bounds at every horizon. -/
theorem worldAt_wf (k : Nat) : WF (worldAt k) := by
  rw [worldAt_spec]
  intro r hr
  have hr' : r ∈ specReqs k := hr
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp hr'
  have hik : i < k := List.mem_range.mp hi
  subst heq
  refine ⟨by omega, ?_, ?_⟩
  · show 0 < (List.range (k + 1)).length
    rw [List.length_range]
    omega
  · show i + 1 < (List.range (k + 1)).length
    rw [List.length_range]
    omega

/-- **Per-event acceptance at every stage**: each of the four events
of block `k + 1`, applied in order from the generated world at stage
`k`, changes the state — no emitted event is ever silently rejected —
and the block lands exactly on the next generated world. -/
theorem block_all_accepted (k : Nat) :
    step (worldAt k) (.setBudget 1) ≠ worldAt k ∧
    step (w1 k) (.admitTok (k + 1)) ≠ w1 k ∧
    step (w2 k) (.require 0 (k + 1)) ≠ w2 k ∧
    step (w3 k) (.addView [k + 1]) ≠ w3 k ∧
    step (w3 k) (.addView [k + 1]) = worldAt (k + 1) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [worldAt_spec]
    intro h
    have hb : (1 : Nat) = 0 := congrArg World.budget h
    cases hb
  · rw [show step (w1 k) (.admitTok (k + 1)) = w2 k from by
      rw [step_admit_fresh (fresh_not_mem k)]; rfl]
    have hlen2 : (w2 k).data.length = k + 2 := by
      show (List.range (k + 1) ++ [k + 1]).length = k + 2
      exact data_len k
    have hlen1 : (w1 k).data.length = k + 1 := by
      show (List.range (k + 1)).length = k + 1
      exact List.length_range
    intro h
    rw [h, hlen1] at hlen2
    omega
  · rw [show step (w2 k) (.require 0 (k + 1)) = w3 k from by
      rw [step_require_ok (req_guard k)]; rfl]
    have hlen3 : (w3 k).reqs.length = k + 1 := by
      show (specReqs k ++ [(0, k + 1)]).length = k + 1
      simp [specReqs, List.length_append, List.length_map,
        List.length_range]
    have hlen2 : (w2 k).reqs.length = k := by
      show (specReqs k).length = k
      simp [specReqs, List.length_map, List.length_range]
    intro h
    rw [h, hlen2] at hlen3
    omega
  · rw [step_addView_ok (aug_guard k), final_assembly k]
    have hlen4 : (specWorld (k + 1)).views.length = k + 1 := by
      show (specViews (k + 1)).length = k + 1
      simp [specViews, List.length_map, List.length_range]
    have hlen3 : (w3 k).views.length = k := by
      show (specViews k).length = k
      simp [specViews, List.length_map, List.length_range]
    intro h
    rw [h, hlen3] at hlen4
    omega
  · rw [step_addView_ok (aug_guard k), final_assembly k,
      worldAt_spec (k + 1)]

/-- The genesis event is accepted too: the run is lawful from the
first event. -/
theorem genesis_accepted : step genesis (.admitTok 0) ≠ genesis := by
  decide

/-! ## Lift to the driver's generated run -/

/-- **Lawfulness of the generated run at every horizon** — the C6
gap, closed: the driver-generated world is quiescent at every stage,
not only at stage 3 (`Constitution.gen_three_quiescent`). -/
theorem gen_quiescent (k : Nat) :
    quiescentB (genWorld k).w = true := by
  show quiescentB (replay (towerGen k) genesis) = true
  rw [driver_reproduces_tower]
  exact worldAt_quiescent k

/-- Well-formedness of the generated run at every horizon. -/
theorem gen_wf (k : Nat) : WF (genWorld k).w := by
  show WF (replay (towerGen k) genesis)
  rw [driver_reproduces_tower]
  exact worldAt_wf k

/-! ## C10 pinned: budget semantics across the descriptor family -/

/-- **The budget trichotomy, for every descriptor and every event**:
the family interpreter leaves the budget unchanged, applies the
saturating decrement (`Nat` subtraction, `max(0, b - 1)` over the
integers), or sets it by an explicit `setBudget`.  This is the exact
semantics the Python mirror now implements; no descriptor can drive
the budget below zero in either language. -/
theorem interp_budget_bound (d : ConstitutionDesc) (w : World)
    (e : Event) :
    (interpStep d w e).budget = w.budget ∨
      (interpStep d w e).budget = w.budget - 1 ∨
      ∃ n, e = .setBudget n ∧ (interpStep d w e).budget = n := by
  cases e with
  | admitTok t =>
      simp only [interpStep]
      split <;> exact Or.inl rfl
  | require i j =>
      simp only [interpStep]
      split <;> exact Or.inl rfl
  | mark v p =>
      simp only [interpStep]
      split
      · exact Or.inr (Or.inl rfl)
      · exact Or.inl rfl
  | addView c =>
      simp only [interpStep]
      split
      · exact Or.inr (Or.inl rfl)
      · exact Or.inl rfl
  | refuse i j =>
      simp only [interpStep]
      split <;> exact Or.inl rfl
  | note n => exact Or.inl rfl
  | setBudget n => exact Or.inr (Or.inr ⟨n, rfl, rfl⟩)
  | setAugLicense b => exact Or.inl rfl

/-- The audit countermodel world: satisfied requirement, budget
exhausted. -/
def satNoopWorld : World :=
  { data := [10, 20], views := [[0]], reqs := [(0, 1)],
    refusals := [], budget := 0, augLicensed := true, notes := [] }

/-- **The audit countermodel, pinned**: with the acceptance guard and
budget gate both off, `mark [1] 0` at budget zero is a no-op — the
`Nat` decrement saturates and `markApply` is the identity off the
view store, so the state is unchanged.  (Before the correction the
Python mirror produced budget `-1` here.) -/
theorem budget_saturation_noop :
    interpStep
      { kernelDesc with guardAccept := false, gateBudget := false }
      satNoopWorld (.mark [1] 0) = satNoopWorld := by decide

/-- Exhaustive over the family: all 64 descriptors agree that the
audit countermodel event is a no-op — the exact fact the Python
mirror asserts on the same basis. -/
theorem mark_saturation_all_descs :
    allDescs.all
      (fun d => interpStep d satNoopWorld (.mark [1] 0)
        == satNoopWorld) = true := by decide

end Horizon
