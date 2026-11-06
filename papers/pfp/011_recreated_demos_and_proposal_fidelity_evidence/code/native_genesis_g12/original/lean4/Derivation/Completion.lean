import Derivation.Represented
import Derivation.RefusalFrontier

/-!
# Ultra closure, Stage II–III: the common native state and Rule 1

Stage II builds one common native state (`CommonState`) into which the
substantive content of the prior modules transports, keeping the
do-not-erase distinctions as *separate fields*:

* `carrier`      — admitted presentation (positions are occurrence
                   identities);
* `metaDistinct` — metatheoretic inequality facts (bookkeeping, never
                   observation);
* `posWitness`   — positive witnessed difference (relation instances);
* `views`        — observation columns (observer-relative difference
                   arises only through these);
* `protectedReqs`— protected fidelity demands;
* budget / license / refusals — resource, authorization, and refusal
  records.

Transport theorems map the represented-progress kernel, the reflective
chain, and the two-element difference objects into `CommonState`, and
the *failures* of transport are first-class: a positive witness is not
observer separation, and observer separation is not a positive
witness.

Stage III settles Rule 1 ("resolve the obstruction or create
structure") for the fixed kernel: an exhaustive trichotomy with an
augmentation *family* that retains both orientations, the
classification of refusal as a record outside the action algebra, and
the fidelity reduction (no protected requirement, no obstruction).
-/

namespace Completion

open Represented

/-! ## The common native state -/

structure CommonState where
  carrier : List Nat
  metaDistinct : List (Nat × Nat)
  posWitness : List (Nat × Nat)
  views : List (List Nat)
  retained : List (Nat × Nat)
  protectedReqs : List (Nat × Nat)
  budget : Nat
  licensed : Bool
  refusals : List (Nat × Nat)
deriving Repr, DecidableEq

/-- Observer-relative separation: only the view columns separate. -/
def sepC (s : CommonState) (i j : Nat) : Bool :=
  s.views.any (fun c => sepB c i j)

/-- The zero relation of the common state: the observer sees no
difference.  Positive witnesses do not enter — that is the point. -/
def zeroC (s : CommonState) (i j : Nat) : Bool := !sepC s i j

/-- Active obstruction: retained, protected, observer-zero — the
three-condition conjunction with the three conditions as independent
fields.  (The represented kernel realizes retention and protection by
one store; the common state keeps them separate, and the kernel
transport instantiates both from the same store — a stated
identification, not an erasure.) -/
def obstC (s : CommonState) (i j : Nat) : Bool :=
  (decide ((i, j) ∈ s.retained))
    && (decide ((i, j) ∈ s.protectedReqs)) && zeroC s i j

/-! ## Transport: the represented-progress kernel -/

def ofWorld (w : World) : CommonState :=
  { carrier := w.data
    metaDistinct := []
    posWitness := []
    views := w.views
    retained := w.reqs
    protectedReqs := w.reqs
    budget := w.budget
    licensed := w.augLicensed
    refusals := w.refusals }

theorem ofWorld_sep (w : World) (i j : Nat) :
    sepC (ofWorld w) i j = satB w (i, j) := rfl

theorem ofWorld_obstruction (w : World) (i j : Nat) :
    obstC (ofWorld w) i j = violB w (i, j) := by
  unfold obstC violB ofWorld zeroC sepC
  cases decide ((i, j) ∈ w.reqs) <;> rfl

/-- The three obstruction conditions are independent in the common
state: retained-without-protection, protected-without-retention, and
retained-and-protected-but-separated each fail to obstruct. -/
theorem obstC_conditions_independent :
    obstC { carrier := [0, 1], metaDistinct := [], posWitness := [],
            views := [], retained := [(0, 1)], protectedReqs := [],
            budget := 0, licensed := true, refusals := [] } 0 1
        = false ∧
      obstC { carrier := [0, 1], metaDistinct := [], posWitness := [],
              views := [], retained := [], protectedReqs := [(0, 1)],
              budget := 0, licensed := true, refusals := [] } 0 1
        = false ∧
      obstC { carrier := [0, 1], metaDistinct := [], posWitness := [],
              views := [[0]], retained := [(0, 1)],
              protectedReqs := [(0, 1)], budget := 0, licensed := true,
              refusals := [] } 0 1 = false ∧
      obstC { carrier := [0, 1], metaDistinct := [], posWitness := [],
              views := [], retained := [(0, 1)],
              protectedReqs := [(0, 1)], budget := 0, licensed := true,
              refusals := [] } 0 1 = true := by decide

/-- The kernel's whole requirement semantics transports exactly:
violations, satisfaction, and (through them) the dichotomy below. -/
theorem ofWorld_quiescent (w : World) :
    (w.reqs.all fun r => !obstC (ofWorld w) r.1 r.2) =
      (w.reqs.all fun r => !violB w r) := by
  apply bool_eq_of_iff
  simp only [List.all_eq_true]
  constructor
  · intro h r hr
    have hx := h r hr
    rw [show obstC (ofWorld w) r.1 r.2 = violB w (r.1, r.2) from
      ofWorld_obstruction w r.1 r.2] at hx
    exact hx
  · intro h r hr
    have hx := h r hr
    rw [show obstC (ofWorld w) r.1 r.2 = violB w (r.1, r.2) from
      ofWorld_obstruction w r.1 r.2]
    exact hx

/-! ## Transport: the reflective chain -/

open RefusalFrontier in
def ofPState (s : PState) : CommonState :=
  { carrier := s.data
    metaDistinct := []
    posWitness := s.rel
    views := [s.tags]
    retained := []
    protectedReqs := []
    budget := 0
    licensed := true
    refusals := [] }

open RefusalFrontier in
theorem chain_transport (n : Nat) :
    (ofPState (reflState n)).carrier = List.range (n + 1) ∧
      (ofPState (reflState n)).posWitness =
        (List.range n).map (fun k => (k, k + 1)) := by
  constructor
  · show (reflState n).data = _
    exact reflective_chain_is_initial_segment n
  · show (reflState n).rel = _
    exact reflective_chain_successor_relation n

/-! ## Transport: the two-element difference objects

The oriented and symmetric two-element objects are encoded as concrete
common states.  The index swap is the common form of the transposition;
the oriented encoding is not swap-invariant, the symmetric one is —
transporting the non-isomorphism content of the pointed two-element
classification. -/

def swapIdx (x : Nat) : Nat := if x = 0 then 1 else if x = 1 then 0 else x

def swapC (s : CommonState) : CommonState :=
  { s with
    posWitness := s.posWitness.map (fun p => (swapIdx p.1, swapIdx p.2))
    views := s.views.map (fun c => c.map swapIdx)
    retained := s.retained.map (fun p => (swapIdx p.1, swapIdx p.2))
    protectedReqs :=
      s.protectedReqs.map (fun p => (swapIdx p.1, swapIdx p.2)) }

def d2Common : CommonState :=
  { carrier := [0, 1], metaDistinct := [(0, 1)],
    posWitness := [(0, 1)], views := [], retained := [(0, 1)],
    protectedReqs := [(0, 1)], budget := 0, licensed := true,
    refusals := [] }

def s2Common : CommonState :=
  { d2Common with posWitness := [(0, 1), (1, 0)] }

theorem d2_transport_oriented : swapC d2Common ≠ d2Common := by decide

/-- S2 symmetry, scoped exactly: the *relation store* is
swap-invariant as a set of instances — that is the transported
symmetry content. -/
theorem s2_transport_symmetric :
    (swapC s2Common).posWitness.length = s2Common.posWitness.length ∧
      ((0, 1) ∈ (swapC s2Common).posWitness ↔
        (0, 1) ∈ s2Common.posWitness) ∧
      ((1, 0) ∈ (swapC s2Common).posWitness ↔
        (1, 0) ∈ s2Common.posWitness) := by decide

/-- And the whole *state* is not swap-invariant: the retained and
protected stores carry an ordered pair, so the encoded S2 is
symmetric in its relation and oriented in its protection bookkeeping.
The symmetry claim is the component claim above, nothing more. -/
theorem s2_state_not_swap_invariant : swapC s2Common ≠ s2Common := by
  decide

/-! ## Transport failures — first-class results

The do-not-erase separations, natively: a positive witness does not
transport to observer separation, and observer separation does not
transport to a positive witness.  These are the common-state forms of
the edge and tagging countermodels. -/

/-- A witnessed pair the observer cannot see: `posWitness` holds an
off-diagonal pair while every view is silent — the zero relation
holds.  Witness ≠ separation. -/
theorem witness_not_separation :
    (0, 1) ∈ d2Common.posWitness ∧ zeroC d2Common 0 1 = true := by
  decide

/-- A separated pair with no witness: one view column separates while
the positive-witness store is empty.  Separation ≠ witness. -/
def tagOnly : CommonState :=
  { carrier := [0, 1], metaDistinct := [], posWitness := [],
    views := [[0]], retained := [], protectedReqs := [], budget := 0,
    licensed := true, refusals := [] }

theorem separation_not_witness :
    sepC tagOnly 0 1 = true ∧ tagOnly.posWitness = [] := by decide

/-- Metatheoretic inequality alone moves nothing: two states differing
only in bookkeeping have identical observation and obstruction
verdicts on every pair (the common-state form of the hash
countermodel). -/
theorem meta_distinctness_inert (s : CommonState) (facts) (i j : Nat) :
    sepC { s with metaDistinct := facts } i j = sepC s i j ∧
      obstC { s with metaDistinct := facts } i j = obstC s i j :=
  ⟨rfl, rfl⟩

/-- The early collapse checkpoint transports as a bounded bridge: two
admitted carrier items with no views are observationally collapsed in
the common state — the Challenge-2 situation in common form.  (The
full early `Regime` structure transports only through the token-erased
simulation; that boundary is recorded in the map, not erased here.) -/
theorem early_collapse_transports :
    zeroC { carrier := [0, 1], metaDistinct := [], posWitness := [],
            views := [], retained := [], protectedReqs := [],
            budget := 0, licensed := true, refusals := [] } 0 1
      = true := by decide

/-! ## Stage III — Rule 1, settled for the fixed kernel

### R1-A: the operational dichotomy, with refusal parallel

Under the explicit hypotheses (replay well-formedness and a recorded
violation), the action-level alternative is binary: the same-level
repair family is non-empty, or the exhaustion certificate holds and
the extension family is non-empty — with *both* orientations of the
canonical augmentation retained (no hidden selector).  Refusal is not
a third action branch: it is a parallel, non-absorbing *record*,
available exactly under the certificate (`refusal_recordable`,
`refusal_object_inert`).  Budget/license execution remains a separate
represented gate (`progress_needs_budget`, `progress_needs_license`).
-/

/-- The extension family: both orientation-canonical singleton columns,
filtered by the acceptance check.  A family, not a choice. -/
def augFamily (w : World) (r : Req) : List View :=
  [[r.1], [r.2]].filter (fun c => augOkB w c)

theorem augFamily_sound {w : World} {r : Req} {c : View}
    (h : c ∈ augFamily w r) : augOkB w c = true :=
  (List.mem_filter.mp h).2

theorem sepB_symm (c : View) (i j : Nat) : sepB c i j = sepB c j i := by
  unfold sepB
  cases decide (i ∈ c) <;> cases decide (j ∈ c) <;> rfl

/-- Both orientations are accepted under a violation: the extension
family retains its ties.  (This strengthens the earlier single-witness
scoping: the orientation of the recorded requirement selects nothing —
both selections are in the family.) -/
theorem augFamily_retains_ties {w : World} {i j : Nat} (hwf : WF w)
    (hviol : violB w (i, j) = true) :
    [i] ∈ augFamily w (i, j) ∧ [j] ∈ augFamily w (i, j) := by
  have hmem : (i, j) ∈ w.reqs := by
    unfold violB at hviol
    simp only [Bool.and_eq_true] at hviol
    exact of_decide_eq_true hviol.1
  have hnots : satB w (i, j) = false := by
    unfold violB at hviol
    simp only [Bool.and_eq_true] at hviol
    have := hviol.2
    cases hs : satB w (i, j) with
    | false => rfl
    | true => rw [hs] at this; exact absurd this (by decide)
  obtain ⟨hne, hib, hjb⟩ := hwf (i, j) hmem
  have hsat_symm : satB w (j, i) = false := by
    cases hs : satB w (j, i) with
    | false => rfl
    | true =>
        exfalso
        have hs' : satB w (i, j) = true := by
          unfold satB at hs ⊢
          simp only [List.any_eq_true] at hs ⊢
          obtain ⟨c, hc, hsep⟩ := hs
          refine ⟨c, hc, ?_⟩
          rw [show sepB c (i, j).1 (i, j).2 = sepB c (j, i).1 (j, i).2
            from sepB_symm c i j]
          exact hsep
        rw [hs'] at hnots
        cases hnots
  have haug : ∀ a b : Nat, a ≠ b → a < w.data.length →
      b < w.data.length → satB w (a, b) = false →
      augOkB w [a] = true := by
    intro a b hab ha hb hnot
    have hsep : sepB [a] a b = true := by
      unfold sepB
      have h1 : (a ∈ [a]) := List.mem_cons_self
      have h2 : ¬ (b ∈ [a]) := by
        intro hbmem
        cases hbmem with
        | head => exact hab rfl
        | tail _ h => cases h
      rw [decide_eq_true h1, decide_eq_false h2]
      rfl
    have hfresh : ¬ ([a] ∈ w.views) := by
      intro hin
      have : satB w (a, b) = true := by
        unfold satB
        simp only [List.any_eq_true]
        exact ⟨[a], hin, hsep⟩
      rw [this] at hnot
      cases hnot
    unfold augOkB
    have hb1 : ([a].all fun p => decide (p < w.data.length)) = true := by
      simp only [List.all_cons, List.all_nil, Bool.and_true]
      exact decide_eq_true ha
    have hb2 : (!(decide ([a] ∈ w.views))) = true := by
      rw [decide_eq_false hfresh]
      rfl
    have hb3 : increaseB w [a] = true := by
      unfold increaseB
      simp only [List.any_eq_true, List.mem_range]
      refine ⟨a, ha, b, hb, ?_⟩
      rw [hsep, hnot]
      have : (a != b) = true := by rwa [bne_iff_ne]
      rw [this]
      rfl
    rw [hb1, hb2, hb3]
    rfl
  constructor
  · apply List.mem_filter.mpr
    refine ⟨List.mem_cons_self, haug i j hne hib hjb hnots⟩
  · apply List.mem_filter.mpr
    refine ⟨List.mem_cons_of_mem _ List.mem_cons_self,
      haug j i (fun h => hne h.symm) hjb hib hsat_symm⟩

/-- **Rule 1, strongest in-kernel form: repair family versus
exhaustion-plus-extension family.**  Every recorded violation admits a
non-empty same-level repair family, or a certified exhaustion together
with a non-empty tied extension family.  There is no third action
branch; refusal is a parallel, non-absorbing record available exactly
in the second case (`refusal_recordable`), and execution of either
branch is separately gated by the represented budget and license. -/
theorem rule1_repair_or_extension {w : World} {i j : Nat} (hwf : WF w)
    (hviol : violB w (i, j) = true) :
    (∃ m, m ∈ repairFamily w (i, j)) ∨
      (obstructedB w (i, j) = true ∧
        [i] ∈ augFamily w (i, j) ∧ [j] ∈ augFamily w (i, j)) := by
  cases hfam : repairFamily w (i, j) with
  | cons m t => exact Or.inl ⟨m, List.mem_cons_self⟩
  | nil =>
      right
      have hobs : obstructedB w (i, j) = true := by
        unfold obstructedB
        rw [hviol]
        have hall : (responseMenu w).all
            (fun m => !repairsB w m (i, j)) = true := by
          simp only [List.all_eq_true]
          intro m hm
          cases hb : repairsB w m (i, j) with
          | false => rfl
          | true =>
              have : m ∈ repairFamily w (i, j) :=
                repairFamily_complete hm hb
              rw [hfam] at this
              cases this
        rw [hall]
        rfl
      obtain ⟨h1, h2⟩ := augFamily_retains_ties hwf hviol
      exact ⟨hobs, h1, h2⟩

/-- Refusal is recordable exactly under the certificate: with the
certificate the pair is in the refusal record after the event
(whether newly recorded or already present). -/
theorem refusal_recordable {w : World} {i j : Nat}
    (hobs : obstructedB w (i, j) = true) :
    (i, j) ∈ (step w (.refuse i j)).refusals := by
  simp only [step]
  by_cases hmem : (i, j) ∈ w.refusals
  · rw [if_neg]
    · exact hmem
    · intro hc
      simp only [Bool.and_eq_true] at hc
      have := hc.2
      rw [decide_eq_true hmem] at this
      exact absurd this (by decide)
  · rw [if_pos]
    · simp only [List.mem_append]
      exact Or.inr List.mem_cons_self
    · rw [hobs, decide_eq_false hmem]
      rfl

/-! ### R1-B: binary compression — refusal is outside the action
algebra -/

/-- Refusal touches no object field: data, views, requirements,
budget, and license are all fixed.  It is a record, not an action. -/
theorem refusal_object_inert (w : World) (i j : Nat) :
    (step w (.refuse i j)).data = w.data ∧
      (step w (.refuse i j)).views = w.views ∧
      (step w (.refuse i j)).reqs = w.reqs ∧
      (step w (.refuse i j)).budget = w.budget ∧
      (step w (.refuse i j)).augLicensed = w.augLicensed := by
  simp only [step]
  split <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩

/-- Refusal is non-absorbing: recording one changes no acceptance
verdict, so later events fire exactly as before (satisfaction,
violations, menus, and acceptance read no refusal data). -/
theorem refusal_non_absorbing (w : World) (i j : Nat) (r : Req)
    (v : View) (p : Nat) (c : View) :
    satB (step w (.refuse i j)) r = satB w r ∧
      violB (step w (.refuse i j)) r = violB w r ∧
      markOkB (step w (.refuse i j)) v p = markOkB w v p ∧
      augOkB (step w (.refuse i j)) c = augOkB w c := by
  simp only [step]
  split <;> exact ⟨rfl, rfl, rfl, rfl⟩

/-- The structural dichotomy behind R1-B: every state-changing event
either preserves the presentation signature (carrier length and view
count both fixed: same-level work, records, and policy) or strictly
grows it (expressive change: a new carrier element or a new view).
Measured on the represented signature, the action algebra is binary;
refusal lives in the first class as a pure record. -/
def sigOf (w : World) : Nat × Nat := (w.data.length, w.views.length)

theorem action_dichotomy (w : World) (e : Event) :
    sigOf (step w e) = sigOf w ∨
      (sigOf w).1 < (sigOf (step w e)).1 ∨
      (sigOf w).2 < (sigOf (step w e)).2 := by
  cases e with
  | admitTok t =>
      simp only [step]
      split
      · exact Or.inl rfl
      · right; left
        show w.data.length < (w.data ++ [t]).length
        simp only [List.length_append, List.length_cons,
          List.length_nil]
        omega
  | require i j =>
      simp only [step]
      split <;> exact Or.inl rfl
  | mark v p =>
      simp only [step]
      split
      · left
        show ((markApply w v p).data.length,
          (markApply w v p).views.length) = _
        unfold markApply sigOf
        simp only [List.length_map]
      · exact Or.inl rfl
  | addView c =>
      simp only [step]
      split
      · right; right
        show w.views.length < (augApply w c).views.length
        unfold augApply
        simp only [List.length_append, List.length_cons,
          List.length_nil]
        omega
      · exact Or.inl rfl
  | refuse i j =>
      simp only [step]
      split <;> exact Or.inl rfl
  | note n => exact Or.inl rfl
  | setBudget n => exact Or.inl rfl
  | setAugLicense b => exact Or.inl rfl

/-! ### R1-C: the fidelity reduction

Rule 1 is one preservation law plus a prior fidelity commitment: with
no protected requirement there is no violation, no obstruction, and
the trichotomy is vacuous.  Obstruction is not absolute — it is
protection-relative, in the kernel as in the two-element theory
(`PrimDiff.collapse_unobstructed_without_fidelity`). -/

theorem rule1_needs_fidelity (w : World) (h : w.reqs = [])
    (r : Req) : violB w r = false ∧ obstructedB w r = false := by
  constructor
  · unfold violB
    have : ¬ (r ∈ w.reqs) := by rw [h]; intro hc; cases hc
    rw [decide_eq_false this]
    rfl
  · unfold obstructedB violB
    have : ¬ (r ∈ w.reqs) := by rw [h]; intro hc; cases hc
    rw [decide_eq_false this]
    rfl

/-- The monotone-restriction caveat, as a countermodel: a *retraction*
semantics (removing a mark) is same-level by the signature measure yet
breaks a previously satisfied requirement — so the preservation law is
not free for arbitrary same-level operations; it is exactly what the
kernel's acceptance guard buys.  (Same shape as the destructive
overwrite countermodel; stated here for the retracting case.) -/
def retractFirstMark (w : World) : World :=
  { w with views :=
      match w.views with
      | [] => []
      | c :: rest => c.drop 1 :: rest }

theorem retraction_breaks_preservation :
    satB { data := [10, 20], views := [[0]], reqs := [(0, 1)],
           refusals := [], budget := 9, augLicensed := true,
           notes := [] } (0, 1) = true ∧
      satB (retractFirstMark
        { data := [10, 20], views := [[0]], reqs := [(0, 1)],
          refusals := [], budget := 9, augLicensed := true,
          notes := [] }) (0, 1) = false := by decide

end Completion
