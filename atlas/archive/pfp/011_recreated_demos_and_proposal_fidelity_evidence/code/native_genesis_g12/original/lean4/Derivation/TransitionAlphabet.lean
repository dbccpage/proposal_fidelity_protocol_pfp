import Derivation.PrimitivePassage

/-!
# A declared one-step codebook for the passage dynamics

This file classifies accepted one-step transitions through a declared
finite signature.  It does **not** construct a quotient of histories:
the signature is not a right congruence for sequential composition, as
the countermodels near `declared_codebook_size` prove.  Raw events and
states therefore remain necessary for replay.

The layers, in dependency order:

0. **Attempted vs accepted.**  A `PEvent` is an attempt; a transition
   is *accepted* at `s` when `step s e ≠ s`.  The exact acceptance
   condition of every constructor is computed by `guardHolds` and the
   agreement `accepted_eq_guardHolds` is a theorem, so "inert" is
   never a judgement call.
1. **Effect profile.**  For an accepted transition we record: the
   nine field-change flags, the discharged guard, what happened to the
   set of actively obstructed pairs (created / preserved / removed /
   untouched, computed by comparing the two obstructed-pair lists),
   the budget delta, continuation vs absorption, and whether the
   constructor is environment-owned or internally proposable.
2. **Class signature.**  Two of the seven profile components are
   *not* invariants of the transition — they are properties of the
   pre-state or of the event's numeric parameter, and both facts are
   proved with witnesses (`preserved_untouched_not_invariant`,
   `budgetDelta_not_invariant`).  The class signature is therefore the
   declared one-step projection, and the split it drops is characterized
   exactly (`obstEffect_split_of_inert`).
3. **Partition.**  Every accepted transition of a well-formed state
   realizes exactly one class signature: existence
   (`sig_eq_classSig`) and uniqueness (`classSig_inj`).
4. **Distinctness.**  One concrete minimum witness per declared code
   plus pairwise distinctness of the thirteen signatures.

Two derived results are worth naming here because they contradict
plausible expectations:

* the internal response generator `nextFamilyP` **does** emit a
  constructor placed in the externally provisioned policy class —
  every extension block begins with
  `setBudget 1` (`internal_family_emits_budget_write`).  The
  classification "no externally classified constructor is internally
  generated" is therefore FALSE as stated; what is true is the exact
  repaired form `internal_family_env_only_unit_funding`, together
  with the two constructors that genuinely never appear
  (`internal_family_no_occurrence_supply`,
  `internal_family_no_license_write`);
* with the discharged guard erased from the signature the code image
  has twelve values, not thirteen: `refineCol` and `addCol` have the
  same accepted effect on every well-formed state
  (`refine_addCol_effect_merge`).  Their difference is a difference of
  *acceptance domain* (the license), not of effect, and the license
  countermodel is recorded.

Scope discipline: every statement below is either universally
quantified over the declared well-formed class `WFClass`, or is a
concrete witness closed by `decide`.  Minimality of the witnesses is
minimality within a declared finite battery; the exhaustive search is
the Python mirror's, and is reported as computation, not as theorem.
No renaming invariance, contextual congruence, DDA correspondence, or
presentation-independent cardinality is claimed.
-/

namespace TransitionAlphabet

open PrimitivePassage

/-! ## 0. Attempted events and accepted transitions -/

/-- A transition is accepted at `s` when it moves the represented
state.  Everything else is an attempt that the guards refuse. -/
def Accepted (s : PState) (e : PEvent) : Bool := decide (step s e ≠ s)

theorem accepted_true_iff (s : PState) (e : PEvent) :
    Accepted s e = true ↔ step s e ≠ s := by
  unfold Accepted; simp

theorem accepted_false_iff (s : PState) (e : PEvent) :
    Accepted s e = false ↔ step s e = s := by
  unfold Accepted; simp

/-- **A halted state accepts nothing at all — `halt` included.**  The
terminal is not a state at which the terminal declaration is still
available: it is inert there like every other event. -/
theorem halted_accepts_nothing (s : PState) (h : s.halted = true)
    (e : PEvent) : Accepted s e = false :=
  (accepted_false_iff s e).mpr (step_halted s e h)

/-- The `halt` half of the previous theorem, stated on its own
because it is the case one expects to be an exception and is not. -/
theorem halt_inert_on_halted (s : PState) (h : s.halted = true) :
    step s .halt = s ∧ Accepted s .halt = false :=
  ⟨step_halted s .halt h, halted_accepts_nothing s h .halt⟩

/-! ## 0.1 The named post-states -/

def occS (s : PState) (t : Nat) : PState := { s with occ := s.occ ++ [t] }

def assS (s : PState) (i j : Nat) : PState :=
  { s with asserted := s.asserted ++ [(i, j)] }

def witS (s : PState) (i j : Nat) : PState :=
  { s with wit := s.wit ++ [(i, j)] }

def protS (s : PState) (i j : Nat) : PState :=
  { s with prot := s.prot ++ [(i, j)] }

def obsS (s : PState) : PState := { s with obs := some [] }

def refineS (s : PState) (cols : List (List Nat)) (v : List Nat)
    (p : Nat) : PState :=
  { s with obs := some (cols.map (fun c => if c = v then p :: c else c)),
           budget := s.budget - 1 }

def colS (s : PState) (cols : List (List Nat)) (c : List Nat) : PState :=
  { s with obs := some (cols ++ [c]), budget := s.budget - 1 }

def refuseS (s : PState) (i j : Nat) : PState :=
  { s with refusals := s.refusals ++ [(i, j)] }

def budS (s : PState) (n : Nat) : PState := { s with budget := n }

def licS (s : PState) (b : Bool) : PState := { s with licensed := b }

def haltS (s : PState) : PState := { s with halted := true }

theorem append_ne {α : Type} (l : List α) (a : α) : l ++ [a] ≠ l := by
  intro h
  have hl := congrArg List.length h
  simp only [List.length_append, List.length_cons, List.length_nil] at hl
  omega

theorem occS_ne (s : PState) (t : Nat) : occS s t ≠ s := fun h =>
  append_ne s.occ t (congrArg PState.occ h)

theorem assS_ne (s : PState) (i j : Nat) : assS s i j ≠ s := fun h =>
  append_ne s.asserted (i, j) (congrArg PState.asserted h)

theorem witS_ne (s : PState) (i j : Nat) : witS s i j ≠ s := fun h =>
  append_ne s.wit (i, j) (congrArg PState.wit h)

theorem protS_ne (s : PState) (i j : Nat) : protS s i j ≠ s := fun h =>
  append_ne s.prot (i, j) (congrArg PState.prot h)

theorem refuseS_ne (s : PState) (i j : Nat) : refuseS s i j ≠ s := fun h =>
  append_ne s.refusals (i, j) (congrArg PState.refusals h)

theorem obsS_ne (s : PState) (h : s.obs = none) : obsS s ≠ s := by
  intro hc
  have h2 : some ([] : List (List Nat)) = s.obs := congrArg PState.obs hc
  rw [h] at h2
  simp at h2

theorem budS_ne (s : PState) (n : Nat) (h : n ≠ s.budget) :
    budS s n ≠ s := fun hc => h (congrArg PState.budget hc)

theorem licS_ne (s : PState) (b : Bool) (h : b ≠ s.licensed) :
    licS s b ≠ s := fun hc => h (congrArg PState.licensed hc)

theorem haltS_ne (s : PState) (h : s.halted = false) : haltS s ≠ s := by
  intro hc
  have h2 : (haltS s).halted = s.halted := congrArg PState.halted hc
  rw [h] at h2
  exact Bool.noConfusion h2

theorem refineS_ne (s : PState) (cols : List (List Nat)) (v : List Nat)
    (p : Nat) (hb : 0 < s.budget) : refineS s cols v p ≠ s := by
  intro hc
  have h2 : (refineS s cols v p).budget = s.budget :=
    congrArg PState.budget hc
  have h3 : s.budget - 1 = s.budget := h2
  omega

theorem colS_ne (s : PState) (cols : List (List Nat)) (c : List Nat)
    (hb : 0 < s.budget) : colS s cols c ≠ s := by
  intro hc
  have h2 : (colS s cols c).budget = s.budget := congrArg PState.budget hc
  have h3 : s.budget - 1 = s.budget := h2
  omega

/-! ## 0.2 The exact acceptance condition of every constructor -/

/-- The computed acceptance condition, constructor by constructor.
This is the *exact* inertness law: `e` is inert at `s` precisely when
`guardHolds s e = false` (`accepted_eq_guardHolds`). -/
def guardHolds (s : PState) : PEvent → Bool
  | .admitOcc t => !s.halted && !(decide (t ∈ s.occ))
  | .assertWit i j =>
      !s.halted && wfPair s i j && !(decide ((i, j) ∈ s.asserted))
  | .admitWit i j =>
      !s.halted && wfPair s i j && (decide ((i, j) ∈ s.asserted))
        && !(decide ((i, j) ∈ s.wit))
  | .protect i j =>
      !s.halted && (decide ((i, j) ∈ s.wit))
        && !(decide ((i, j) ∈ s.prot))
  | .declareObs => !s.halted && decide (s.obs = none)
  | .refineCol v p =>
      !s.halted && refineOk s v p && decide (0 < s.budget)
  | .addCol c =>
      !s.halted && colOk s c && s.licensed && decide (0 < s.budget)
  | .refuse i j =>
      !s.halted && obstP s i j && !(decide ((i, j) ∈ s.refusals))
  | .setBudget n => !s.halted && !(decide (n = s.budget))
  | .setLicense b => !s.halted && !(decide (b = s.licensed))
  | .halt => !s.halted

theorem refineOk_declared (s : PState) (v : List Nat) (p : Nat)
    (h : refineOk s v p = true) : ∃ cols, s.obs = some cols := by
  cases hobs : s.obs with
  | none => rw [refineOk, hobs] at h; exact absurd h (by simp)
  | some cols => exact ⟨cols, rfl⟩

theorem colOk_declared (s : PState) (c : List Nat)
    (h : colOk s c = true) : ∃ cols, s.obs = some cols := by
  cases hobs : s.obs with
  | none => rw [colOk, hobs] at h; exact absurd h (by simp)
  | some cols => exact ⟨cols, rfl⟩

private theorem hfalse : ¬ (false = true) := fun hc => Bool.noConfusion hc

private theorem hlive {s : PState} (hh : s.halted = false) :
    ¬ (s.halted = true) := by rw [hh]; exact hfalse

theorem step_admitOcc_acc (s : PState) (t : Nat) (hh : s.halted = false)
    (hm : t ∉ s.occ) : step s (.admitOcc t) = occS s t := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg hm]
  rfl

theorem step_admitOcc_inert (s : PState) (t : Nat) (hh : s.halted = false)
    (hm : t ∈ s.occ) : step s (.admitOcc t) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_pos hm]

theorem step_assertWit_acc (s : PState) (i j : Nat) (hh : s.halted = false)
    (hg : (wfPair s i j && !(decide ((i, j) ∈ s.asserted))) = true) :
    step s (.assertWit i j) = assS s i j := by
  simp only [step]
  rw [if_neg (hlive hh), if_pos hg]
  rfl

theorem step_assertWit_inert (s : PState) (i j : Nat)
    (hh : s.halted = false)
    (hg : (wfPair s i j && !(decide ((i, j) ∈ s.asserted))) = false) :
    step s (.assertWit i j) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg (by rw [hg]; exact hfalse)]

theorem step_admitWit_acc (s : PState) (i j : Nat) (hh : s.halted = false)
    (hg : (wfPair s i j && (decide ((i, j) ∈ s.asserted))
      && !(decide ((i, j) ∈ s.wit))) = true) :
    step s (.admitWit i j) = witS s i j := by
  simp only [step]
  rw [if_neg (hlive hh), if_pos hg]
  rfl

theorem step_admitWit_inert (s : PState) (i j : Nat)
    (hh : s.halted = false)
    (hg : (wfPair s i j && (decide ((i, j) ∈ s.asserted))
      && !(decide ((i, j) ∈ s.wit))) = false) :
    step s (.admitWit i j) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg (by rw [hg]; exact hfalse)]

theorem step_protect_acc (s : PState) (i j : Nat) (hh : s.halted = false)
    (hg : ((decide ((i, j) ∈ s.wit))
      && !(decide ((i, j) ∈ s.prot))) = true) :
    step s (.protect i j) = protS s i j := by
  simp only [step]
  rw [if_neg (hlive hh), if_pos hg]
  rfl

theorem step_protect_inert (s : PState) (i j : Nat) (hh : s.halted = false)
    (hg : ((decide ((i, j) ∈ s.wit))
      && !(decide ((i, j) ∈ s.prot))) = false) :
    step s (.protect i j) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg (by rw [hg]; exact hfalse)]

theorem step_declareObs_acc (s : PState) (hh : s.halted = false)
    (ho : s.obs = none) : step s .declareObs = obsS s := by
  simp only [step]
  rw [if_neg (hlive hh), ho]
  rfl

theorem step_declareObs_inert (s : PState) (cols : List (List Nat))
    (hh : s.halted = false) (ho : s.obs = some cols) :
    step s .declareObs = s := by
  simp only [step]
  rw [if_neg (hlive hh), ho]

theorem step_refineCol_acc (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (hh : s.halted = false)
    (ho : s.obs = some cols) (hok : refineOk s v p = true)
    (hb : 0 < s.budget) :
    step s (.refineCol v p) = refineS s cols v p := by
  simp only [step]
  rw [if_neg (hlive hh),
      if_pos (by rw [hok, decide_eq_true hb]; rfl), ho]
  rfl

theorem step_refineCol_inert (s : PState) (v : List Nat) (p : Nat)
    (hh : s.halted = false)
    (hg : (refineOk s v p && decide (0 < s.budget)) = false) :
    step s (.refineCol v p) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg (by rw [hg]; exact hfalse)]

theorem step_addCol_acc (s : PState) (cols : List (List Nat))
    (c : List Nat) (hh : s.halted = false) (ho : s.obs = some cols)
    (hok : colOk s c = true) (hl : s.licensed = true) (hb : 0 < s.budget) :
    step s (.addCol c) = colS s cols c := by
  simp only [step]
  rw [if_neg (hlive hh),
      if_pos (by rw [hok, hl, decide_eq_true hb]; rfl), ho]
  rfl

theorem step_addCol_inert (s : PState) (c : List Nat)
    (hh : s.halted = false)
    (hg : (colOk s c && s.licensed && decide (0 < s.budget)) = false) :
    step s (.addCol c) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg (by rw [hg]; exact hfalse)]

theorem step_refuse_acc (s : PState) (i j : Nat) (hh : s.halted = false)
    (hg : (obstP s i j && !(decide ((i, j) ∈ s.refusals))) = true) :
    step s (.refuse i j) = refuseS s i j := by
  simp only [step]
  rw [if_neg (hlive hh), if_pos hg]
  rfl

theorem step_refuse_inert (s : PState) (i j : Nat) (hh : s.halted = false)
    (hg : (obstP s i j && !(decide ((i, j) ∈ s.refusals))) = false) :
    step s (.refuse i j) = s := by
  simp only [step]
  rw [if_neg (hlive hh), if_neg (by rw [hg]; exact hfalse)]

theorem step_setBudget_live (s : PState) (n : Nat) (hh : s.halted = false) :
    step s (.setBudget n) = budS s n := by
  simp only [step]
  rw [if_neg (hlive hh)]
  rfl

theorem step_setLicense_live (s : PState) (b : Bool)
    (hh : s.halted = false) : step s (.setLicense b) = licS s b := by
  simp only [step]
  rw [if_neg (hlive hh)]
  rfl

theorem step_halt_eq (s : PState) : step s .halt = haltS s := rfl

/-- **The exact inertness law.**  Acceptance is decided by
`guardHolds`, constructor by constructor: no event is inert for a
reason not listed there, and none is accepted without discharging the
listed guard. -/
theorem accepted_eq_guardHolds (s : PState) (e : PEvent) :
    Accepted s e = guardHolds s e := by
  cases e with
  | admitOcc t =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          by_cases hm : t ∈ s.occ
          · rw [(accepted_false_iff s _).mpr
                (step_admitOcc_inert s t hh hm)]
            simp [guardHolds, hh, hm]
          · have hne : step s (.admitOcc t) ≠ s := by
              rw [step_admitOcc_acc s t hh hm]; exact occS_ne s t
            rw [(accepted_true_iff s _).mpr hne]
            simp [guardHolds, hh, hm]
  | assertWit i j =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases hg : (wfPair s i j && !(decide ((i, j) ∈ s.asserted))) with
          | false =>
              rw [(accepted_false_iff s _).mpr
                (step_assertWit_inert s i j hh hg)]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
          | true =>
              have hne : step s (.assertWit i j) ≠ s := by
                rw [step_assertWit_acc s i j hh hg]; exact assS_ne s i j
              rw [(accepted_true_iff s _).mpr hne]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
  | admitWit i j =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases hg : (wfPair s i j && (decide ((i, j) ∈ s.asserted))
              && !(decide ((i, j) ∈ s.wit))) with
          | false =>
              rw [(accepted_false_iff s _).mpr
                (step_admitWit_inert s i j hh hg)]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
          | true =>
              have hne : step s (.admitWit i j) ≠ s := by
                rw [step_admitWit_acc s i j hh hg]; exact witS_ne s i j
              rw [(accepted_true_iff s _).mpr hne]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
  | protect i j =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases hg : ((decide ((i, j) ∈ s.wit))
              && !(decide ((i, j) ∈ s.prot))) with
          | false =>
              rw [(accepted_false_iff s _).mpr
                (step_protect_inert s i j hh hg)]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
          | true =>
              have hne : step s (.protect i j) ≠ s := by
                rw [step_protect_acc s i j hh hg]; exact protS_ne s i j
              rw [(accepted_true_iff s _).mpr hne]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
  | declareObs =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases ho : s.obs with
          | none =>
              have hne : step s .declareObs ≠ s := by
                rw [step_declareObs_acc s hh ho]; exact obsS_ne s ho
              rw [(accepted_true_iff s _).mpr hne]
              simp [guardHolds, hh, ho]
          | some cols =>
              rw [(accepted_false_iff s _).mpr
                (step_declareObs_inert s cols hh ho)]
              simp [guardHolds, hh, ho]
  | refineCol v p =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases hg : (refineOk s v p && decide (0 < s.budget)) with
          | false =>
              rw [(accepted_false_iff s _).mpr
                (step_refineCol_inert s v p hh hg)]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
          | true =>
              have hok : refineOk s v p = true := by
                simp only [Bool.and_eq_true] at hg; exact hg.1
              have hb : 0 < s.budget := by
                simp only [Bool.and_eq_true, decide_eq_true_eq] at hg
                exact hg.2
              obtain ⟨cols, ho⟩ := refineOk_declared s v p hok
              have hne : step s (.refineCol v p) ≠ s := by
                rw [step_refineCol_acc s cols v p hh ho hok hb]
                exact refineS_ne s cols v p hb
              rw [(accepted_true_iff s _).mpr hne]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
  | addCol c =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases hg : (colOk s c && s.licensed && decide (0 < s.budget)) with
          | false =>
              rw [(accepted_false_iff s _).mpr
                (step_addCol_inert s c hh hg)]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
          | true =>
              have hok : colOk s c = true := by
                simp only [Bool.and_eq_true] at hg; exact hg.1.1
              have hl : s.licensed = true := by
                simp only [Bool.and_eq_true] at hg; exact hg.1.2
              have hb : 0 < s.budget := by
                simp only [Bool.and_eq_true, decide_eq_true_eq] at hg
                exact hg.2
              obtain ⟨cols, ho⟩ := colOk_declared s c hok
              have hne : step s (.addCol c) ≠ s := by
                rw [step_addCol_acc s cols c hh ho hok hl hb]
                exact colS_ne s cols c hb
              rw [(accepted_true_iff s _).mpr hne]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
  | refuse i j =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          cases hg : (obstP s i j && !(decide ((i, j) ∈ s.refusals))) with
          | false =>
              rw [(accepted_false_iff s _).mpr
                (step_refuse_inert s i j hh hg)]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
          | true =>
              have hne : step s (.refuse i j) ≠ s := by
                rw [step_refuse_acc s i j hh hg]; exact refuseS_ne s i j
              rw [(accepted_true_iff s _).mpr hne]
              simp only [guardHolds, hh, Bool.not_false, Bool.true_and]
              exact hg.symm
  | setBudget n =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          by_cases hn : n = s.budget
          · have heq : step s (.setBudget n) = s := by
              rw [step_setBudget_live s n hh, hn]; rfl
            rw [(accepted_false_iff s _).mpr heq]
            simp [guardHolds, hh, hn]
          · have hne : step s (.setBudget n) ≠ s := by
              rw [step_setBudget_live s n hh]; exact budS_ne s n hn
            rw [(accepted_true_iff s _).mpr hne]
            simp [guardHolds, hh, hn]
  | setLicense b =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          by_cases hn : b = s.licensed
          · have heq : step s (.setLicense b) = s := by
              rw [step_setLicense_live s b hh, hn]; rfl
            rw [(accepted_false_iff s _).mpr heq]
            simp [guardHolds, hh, hn]
          · have hne : step s (.setLicense b) ≠ s := by
              rw [step_setLicense_live s b hh]; exact licS_ne s b hn
            rw [(accepted_true_iff s _).mpr hne]
            simp [guardHolds, hh, hn]
  | halt =>
      cases hh : s.halted with
      | true => rw [halted_accepts_nothing s hh]; simp [guardHolds, hh]
      | false =>
          have hne : step s .halt ≠ s := by
            rw [step_halt_eq s]; exact haltS_ne s hh
          rw [(accepted_true_iff s _).mpr hne]
          simp [guardHolds, hh]

/-! ## 1. List apparatus (metatheory, no object-language content) -/

theorem filter_notmem_eq_nil (l m : List (Nat × Nat))
    (h : ∀ x ∈ l, x ∈ m) :
    l.filter (fun r => !(decide (r ∈ m))) = [] := by
  induction l with
  | nil => rfl
  | cons a rest ih =>
      rw [List.filter_cons, decide_eq_true (h a List.mem_cons_self),
        Bool.not_true, if_neg hfalse]
      exact ih (fun x hx => h x (List.mem_cons_of_mem a hx))

theorem filter_congr_mem (l : List (Nat × Nat))
    (f g : (Nat × Nat) → Bool) (h : ∀ x ∈ l, f x = g x) :
    l.filter f = l.filter g := by
  induction l with
  | nil => rfl
  | cons a rest ih =>
      rw [List.filter_cons, List.filter_cons, h a List.mem_cons_self,
        ih (fun x hx => h x (List.mem_cons_of_mem a hx))]

theorem filter_all_true (l : List (Nat × Nat)) (f : (Nat × Nat) → Bool)
    (h : ∀ x ∈ l, f x = true) : l.filter f = l := by
  induction l with
  | nil => rfl
  | cons a rest ih =>
      rw [List.filter_cons, h a List.mem_cons_self, if_pos rfl,
        ih (fun x hx => h x (List.mem_cons_of_mem a hx))]

theorem filter_all_false (l : List (Nat × Nat)) (f : (Nat × Nat) → Bool)
    (h : ∀ x ∈ l, f x = false) : l.filter f = [] := by
  induction l with
  | nil => rfl
  | cons a rest ih =>
      rw [List.filter_cons, h a List.mem_cons_self, if_neg hfalse]
      exact ih (fun x hx => h x (List.mem_cons_of_mem a hx))

theorem list_ne_nil_of_mem {α : Type} {a : α} {l : List α} (h : a ∈ l) :
    l ≠ [] := by
  cases l with
  | nil => cases h
  | cons b t => exact List.cons_ne_nil b t

theorem isEmpty_not_of_ne (l : List (Nat × Nat)) (h : l ≠ []) :
    (!l.isEmpty) = true := by
  cases l with
  | nil => exact absurd rfl h
  | cons a t => rfl

/-! ## 2. What an accepted transition does to the active obstructions

`obstructedPairs` is the represented list of actively obstructed
protected pairs.  Comparing it before and after gives the four
outcomes.  The classifier is *ordered*: a step that both loses and
gains obstructed pairs is reported as `removed`.  No accepted step of
the declared class exercises that order — each constructor lemma
below proves one of the two difference lists empty. -/

inductive ObstEffect where
  | created
  | preserved
  | removed
  | untouched
deriving Repr, DecidableEq

/-- The invariant coarsening: the `preserved`/`untouched` split is a
property of the pre-state, not of the transition
(`preserved_untouched_not_invariant`). -/
inductive ObstMove where
  | creates
  | removes
  | inert
deriving Repr, DecidableEq

def coarse : ObstEffect → ObstMove
  | .created => .creates
  | .removed => .removes
  | .preserved => .inert
  | .untouched => .inert

def gainedPairs (s t : PState) : List (Nat × Nat) :=
  (obstructedPairs t).filter (fun r => !(decide (r ∈ obstructedPairs s)))

def lostPairs (s t : PState) : List (Nat × Nat) :=
  (obstructedPairs s).filter (fun r => !(decide (r ∈ obstructedPairs t)))

def obstEffect (s t : PState) : ObstEffect :=
  if !(lostPairs s t).isEmpty then .removed
  else if !(gainedPairs s t).isEmpty then .created
  else if (obstructedPairs s).isEmpty then .untouched
  else .preserved

theorem obstructedPairs_sub (s : PState) :
    ∀ r ∈ obstructedPairs s, r ∈ s.prot :=
  fun _ hr => (List.mem_filter.mp hr).1

theorem obst_of_mem_obstructedPairs (s : PState) (r : Nat × Nat)
    (h : r ∈ obstructedPairs s) : obstP s r.1 r.2 = true :=
  (List.mem_filter.mp h).2

theorem mem_obstructedPairs (s : PState) (r : Nat × Nat)
    (h1 : r ∈ s.prot) (h2 : obstP s r.1 r.2 = true) :
    r ∈ obstructedPairs s :=
  List.mem_filter.mpr ⟨h1, h2⟩

theorem lost_nil_of_eq (s t : PState)
    (h : obstructedPairs t = obstructedPairs s) : lostPairs s t = [] := by
  unfold lostPairs
  rw [h]
  exact filter_notmem_eq_nil _ _ (fun x hx => hx)

theorem gained_nil_of_eq (s t : PState)
    (h : obstructedPairs t = obstructedPairs s) : gainedPairs s t = [] := by
  unfold gainedPairs
  rw [h]
  exact filter_notmem_eq_nil _ _ (fun x hx => hx)

theorem obstMove_inert_of_eq (s t : PState)
    (h : obstructedPairs t = obstructedPairs s) :
    coarse (obstEffect s t) = .inert := by
  unfold obstEffect
  rw [lost_nil_of_eq s t h, gained_nil_of_eq s t h]
  simp only [List.isEmpty_nil, Bool.not_true, if_neg hfalse]
  split <;> rfl

/-- **The dropped split, characterized exactly.**  When the
obstruction set is untouched, the four-valued outcome is decided by
the pre-state alone: `untouched` on a clear state, `preserved` on an
obstructed one. -/
theorem obstEffect_split_of_inert (s t : PState)
    (h : obstructedPairs t = obstructedPairs s) :
    (obstructedPairs s = [] → obstEffect s t = .untouched) ∧
    (obstructedPairs s ≠ [] → obstEffect s t = .preserved) := by
  unfold obstEffect
  rw [lost_nil_of_eq s t h, gained_nil_of_eq s t h]
  simp only [List.isEmpty_nil, Bool.not_true, if_neg hfalse]
  constructor
  · intro he
    rw [he]
    rfl
  · intro he
    rw [if_neg (by
      cases hc : obstructedPairs s with
      | nil => exact absurd hc he
      | cons a t => exact hfalse)]

/-- Stores untouched: the obstruction set cannot move. -/
theorem obstructedPairs_eq_of_stores (s t : PState) (hw : t.wit = s.wit)
    (hp : t.prot = s.prot) (ho : t.obs = s.obs) :
    obstructedPairs t = obstructedPairs s := by
  unfold obstructedPairs
  rw [hp]
  exact filter_congr_mem s.prot _ _ (fun r _ => by
    unfold obstP
    rw [hw, hp, ho])

/-! ### The obstruction effect of every constructor -/

theorem obstructedPairs_occS (s : PState) (t : Nat) :
    obstructedPairs (occS s t) = obstructedPairs s :=
  obstructedPairs_eq_of_stores _ _ rfl rfl rfl

theorem obstructedPairs_assS (s : PState) (i j : Nat) :
    obstructedPairs (assS s i j) = obstructedPairs s :=
  obstructedPairs_eq_of_stores _ _ rfl rfl rfl

theorem obstructedPairs_refuseS (s : PState) (i j : Nat) :
    obstructedPairs (refuseS s i j) = obstructedPairs s :=
  obstructedPairs_eq_of_stores _ _ rfl rfl rfl

theorem obstructedPairs_budS (s : PState) (n : Nat) :
    obstructedPairs (budS s n) = obstructedPairs s :=
  obstructedPairs_eq_of_stores _ _ rfl rfl rfl

theorem obstructedPairs_licS (s : PState) (b : Bool) :
    obstructedPairs (licS s b) = obstructedPairs s :=
  obstructedPairs_eq_of_stores _ _ rfl rfl rfl

theorem obstructedPairs_haltS (s : PState) :
    obstructedPairs (haltS s) = obstructedPairs s :=
  obstructedPairs_eq_of_stores _ _ rfl rfl rfl

/-- Retention cannot create an obstruction **on the declared class**:
protection is contained in retention there, so a newly retained pair
is not yet protected.  Outside the class the statement fails
(`retention_creates_outside_class`). -/
theorem obstructedPairs_witS (s : PState) (i j : Nat)
    (hsub : ∀ p ∈ s.prot, p ∈ s.wit) :
    obstructedPairs (witS s i j) = obstructedPairs s := by
  unfold obstructedPairs
  show (s.prot).filter _ = (s.prot).filter _
  refine filter_congr_mem s.prot _ _ (fun r hr => ?_)
  have hm : (r.1, r.2) ∈ s.wit := hsub r hr
  have hm2 : (r.1, r.2) ∈ s.wit ++ [(i, j)] :=
    List.mem_append.mpr (Or.inl hm)
  show obstP (witS s i j) r.1 r.2 = obstP s r.1 r.2
  unfold obstP witS
  simp only []
  rw [decide_eq_true hm, decide_eq_true hm2]

theorem obstructedPairs_protS (s : PState) (i j : Nat) :
    obstructedPairs (protS s i j)
      = obstructedPairs s
        ++ (if obstP (protS s i j) i j = true then [(i, j)] else []) := by
  have hag : ∀ r ∈ s.prot,
      obstP (protS s i j) r.1 r.2 = obstP s r.1 r.2 := by
    intro r hr
    have hm : (r.1, r.2) ∈ s.prot := hr
    have hm2 : (r.1, r.2) ∈ s.prot ++ [(i, j)] :=
      List.mem_append.mpr (Or.inl hm)
    unfold obstP protS
    simp only []
    rw [decide_eq_true hm, decide_eq_true hm2]
  unfold obstructedPairs
  show (s.prot ++ [(i, j)]).filter _ = _
  rw [List.filter_append, filter_congr_mem s.prot _ _ hag]
  congr 1
  rw [List.filter_cons, List.filter_nil]

/-- Declaring the observation makes every protected pair of a
well-formed pre-observational state actively obstructed at once. -/
theorem obstructedPairs_obsS (s : PState) (ho : s.obs = none)
    (hsub : ∀ p ∈ s.prot, p ∈ s.wit) :
    obstructedPairs (obsS s) = s.prot ∧ obstructedPairs s = [] := by
  constructor
  · unfold obstructedPairs
    show (s.prot).filter _ = s.prot
    refine filter_all_true s.prot _ (fun r hr => ?_)
    have hm : (r.1, r.2) ∈ s.wit := hsub r hr
    have hp : (r.1, r.2) ∈ s.prot := hr
    show obstP (obsS s) r.1 r.2 = true
    unfold obstP obsS
    simp only []
    rw [decide_eq_true hm, decide_eq_true hp]
    rfl
  · unfold obstructedPairs
    exact filter_all_false s.prot _ (fun r _ =>
      obst_requires_observation s r.1 r.2 ho)

/-! ### Structure-creating and same-level responses remove -/

theorem sepP_append (cols : List (List Nat)) (c : List Nat) (i j : Nat) :
    sepP (cols ++ [c]) i j = (sepP cols i j || sepCol c i j) := by
  unfold sepP
  rw [List.any_append]
  simp

theorem zeroP_append_mono (cols : List (List Nat)) (c : List Nat)
    (i j : Nat) (h : zeroP (cols ++ [c]) i j = true) :
    zeroP cols i j = true := by
  unfold zeroP at *
  rw [sepP_append] at h
  cases hc : sepP cols i j with
  | false => rfl
  | true => rw [hc] at h; exact absurd h (by simp)

theorem obstructedPairs_colS_sub (s : PState) (cols : List (List Nat))
    (c : List Nat) (ho : s.obs = some cols) :
    ∀ r ∈ obstructedPairs (colS s cols c), r ∈ obstructedPairs s := by
  intro r hr
  have h1 : r ∈ (colS s cols c).prot := (List.mem_filter.mp hr).1
  have h2 : obstP (colS s cols c) r.1 r.2 = true := (List.mem_filter.mp hr).2
  have hprot : r ∈ s.prot := h1
  refine mem_obstructedPairs s r hprot ?_
  rw [obst_agrees_when_declared (colS s cols c) (cols ++ [c]) rfl r.1 r.2]
    at h2
  rw [obst_agrees_when_declared s cols ho r.1 r.2]
  simp only [Bool.and_eq_true] at h2 ⊢
  exact ⟨h2.1, zeroP_append_mono cols c r.1 r.2 h2.2⟩

theorem colS_lost_ne_nil (s : PState) (cols : List (List Nat))
    (c : List Nat) (ho : s.obs = some cols) (hok : colOk s c = true) :
    lostPairs s (colS s cols c) ≠ [] := by
  have hany : (s.prot.any
      (fun r => obstP s r.1 r.2 && sepCol c r.1 r.2)) = true := by
    unfold colOk at hok
    rw [ho] at hok
    simp only [Bool.and_eq_true] at hok
    exact hok.2
  obtain ⟨r, hrmem, hr⟩ := List.any_eq_true.mp hany
  simp only [Bool.and_eq_true] at hr
  have hin : r ∈ obstructedPairs s := mem_obstructedPairs s r hrmem hr.1
  have hout : r ∉ obstructedPairs (colS s cols c) := by
    intro hc
    have h2 : obstP (colS s cols c) r.1 r.2 = true :=
      (List.mem_filter.mp hc).2
    rw [obst_agrees_when_declared (colS s cols c) (cols ++ [c]) rfl r.1 r.2]
      at h2
    simp only [Bool.and_eq_true] at h2
    have hz : zeroP (cols ++ [c]) r.1 r.2 = true := h2.2
    unfold zeroP at hz
    rw [sepP_append, hr.2] at hz
    simp at hz
  exact list_ne_nil_of_mem (List.mem_filter.mpr ⟨hin, by
    rw [decide_eq_false hout]; rfl⟩)

theorem obstEffect_colS (s : PState) (cols : List (List Nat))
    (c : List Nat) (ho : s.obs = some cols) (hok : colOk s c = true) :
    obstEffect s (colS s cols c) = .removed := by
  unfold obstEffect
  rw [if_pos (isEmpty_not_of_ne _ (colS_lost_ne_nil s cols c ho hok))]

/-- The refined observation contains the refined column. -/
theorem mem_map_refine (cols : List (List Nat)) (v : List Nat) (p : Nat)
    (hv : v ∈ cols) :
    (p :: v) ∈ cols.map (fun c => if c = v then p :: c else c) := by
  refine List.mem_map.mpr ⟨v, hv, ?_⟩
  rw [if_pos rfl]

theorem obstructedPairs_refineS_sub (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (ho : s.obs = some cols)
    (hok : refineOk s v p = true) :
    ∀ r ∈ obstructedPairs (refineS s cols v p), r ∈ obstructedPairs s := by
  have hmono : (s.prot.all (fun r =>
      !sepP cols r.1 r.2 || sepP (cols.map
        (fun c => if c = v then p :: c else c)) r.1 r.2)) = true := by
    unfold refineOk at hok
    rw [ho] at hok
    simp only [Bool.and_eq_true] at hok
    exact hok.2
  intro r hr
  have hprot : r ∈ s.prot := (List.mem_filter.mp hr).1
  have h2 : obstP (refineS s cols v p) r.1 r.2 = true :=
    (List.mem_filter.mp hr).2
  refine mem_obstructedPairs s r hprot ?_
  rw [obst_agrees_when_declared (refineS s cols v p)
    (cols.map (fun c => if c = v then p :: c else c)) rfl r.1 r.2] at h2
  rw [obst_agrees_when_declared s cols ho r.1 r.2]
  simp only [Bool.and_eq_true] at h2 ⊢
  refine ⟨h2.1, ?_⟩
  have hm := List.all_eq_true.mp hmono r hprot
  simp only [Bool.or_eq_true, Bool.not_eq_true'] at hm
  rcases hm with hm | hm
  · unfold zeroP
    rw [hm]
    rfl
  · exfalso
    have hz : zeroP (cols.map (fun c => if c = v then p :: c else c))
        r.1 r.2 = true := h2.2
    unfold zeroP at hz
    rw [hm] at hz
    exact absurd hz (by simp)

theorem refineS_lost_ne_nil (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (ho : s.obs = some cols)
    (hok : refineOk s v p = true) :
    lostPairs s (refineS s cols v p) ≠ [] := by
  have hv : v ∈ cols := by
    unfold refineOk at hok
    rw [ho] at hok
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hok
    exact hok.1.1.1.1
  have hany : (s.prot.any (fun r =>
      obstP s r.1 r.2 && sepCol (p :: v) r.1 r.2)) = true := by
    unfold refineOk at hok
    rw [ho] at hok
    simp only [Bool.and_eq_true] at hok
    exact hok.1.2
  obtain ⟨r, hrmem, hr⟩ := List.any_eq_true.mp hany
  simp only [Bool.and_eq_true] at hr
  have hin : r ∈ obstructedPairs s := mem_obstructedPairs s r hrmem hr.1
  have hout : r ∉ obstructedPairs (refineS s cols v p) := by
    intro hc
    have h2 : obstP (refineS s cols v p) r.1 r.2 = true :=
      (List.mem_filter.mp hc).2
    rw [obst_agrees_when_declared (refineS s cols v p)
      (cols.map (fun c => if c = v then p :: c else c)) rfl r.1 r.2] at h2
    simp only [Bool.and_eq_true] at h2
    have hz : zeroP (cols.map (fun c => if c = v then p :: c else c))
        r.1 r.2 = true := h2.2
    unfold zeroP sepP at hz
    have hsep : ((cols.map (fun c => if c = v then p :: c else c)).any
        (fun d => sepCol d r.1 r.2)) = true :=
      List.any_eq_true.mpr ⟨p :: v, mem_map_refine cols v p hv, hr.2⟩
    rw [hsep] at hz
    exact absurd hz (by simp)
  exact list_ne_nil_of_mem (List.mem_filter.mpr ⟨hin, by
    rw [decide_eq_false hout]; rfl⟩)

theorem obstEffect_refineS (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (ho : s.obs = some cols)
    (hok : refineOk s v p = true) :
    obstEffect s (refineS s cols v p) = .removed := by
  unfold obstEffect
  rw [if_pos (isEmpty_not_of_ne _ (refineS_lost_ne_nil s cols v p ho hok))]

/-! ## 3. The remaining profile components -/

structure FieldDelta where
  occ : Bool
  asserted : Bool
  wit : Bool
  prot : Bool
  obs : Bool
  budget : Bool
  licensed : Bool
  refusals : Bool
  halted : Bool
deriving Repr, DecidableEq

def fieldDelta (s t : PState) : FieldDelta :=
  { occ := t.occ != s.occ,
    asserted := t.asserted != s.asserted,
    wit := t.wit != s.wit,
    prot := t.prot != s.prot,
    obs := t.obs != s.obs,
    budget := t.budget != s.budget,
    licensed := t.licensed != s.licensed,
    refusals := t.refusals != s.refusals,
    halted := t.halted != s.halted }

def fdOcc : FieldDelta :=
  ⟨true, false, false, false, false, false, false, false, false⟩
def fdAsserted : FieldDelta :=
  ⟨false, true, false, false, false, false, false, false, false⟩
def fdWit : FieldDelta :=
  ⟨false, false, true, false, false, false, false, false, false⟩
def fdProt : FieldDelta :=
  ⟨false, false, false, true, false, false, false, false, false⟩
def fdObs : FieldDelta :=
  ⟨false, false, false, false, true, false, false, false, false⟩
def fdObsBudget : FieldDelta :=
  ⟨false, false, false, false, true, true, false, false, false⟩
def fdBudget : FieldDelta :=
  ⟨false, false, false, false, false, true, false, false, false⟩
def fdLicensed : FieldDelta :=
  ⟨false, false, false, false, false, false, true, false, false⟩
def fdRefusals : FieldDelta :=
  ⟨false, false, false, false, false, false, false, true, false⟩
def fdHalted : FieldDelta :=
  ⟨false, false, false, false, false, false, false, false, true⟩

theorem bne_true_of_ne {α : Type} [DecidableEq α] {a b : α} (h : a ≠ b) :
    (a != b) = true := by simp [h]

/-- Refining a declared column really changes the declared
observation: the refined column is one point longer. -/
theorem map_replace_ne (cols : List (List Nat)) (v : List Nat) (p : Nat)
    (hv : v ∈ cols) :
    cols.map (fun c => if c = v then p :: c else c) ≠ cols := by
  induction cols with
  | nil => cases hv
  | cons c rest ih =>
      intro h
      simp only [List.map_cons, List.cons.injEq] at h
      by_cases hc : c = v
      · rw [if_pos hc] at h
        have hl := congrArg List.length h.1
        simp only [List.length_cons] at hl
        omega
      · rw [if_neg hc] at h
        exact ih (List.mem_of_ne_of_mem (fun hvc => hc hvc.symm) hv) h.2

theorem fieldDelta_occS (s : PState) (t : Nat) :
    fieldDelta s (occS s t) = fdOcc := by
  simp [fieldDelta, fdOcc, occS]

theorem fieldDelta_assS (s : PState) (i j : Nat) :
    fieldDelta s (assS s i j) = fdAsserted := by
  simp [fieldDelta, fdAsserted, assS]

theorem fieldDelta_witS (s : PState) (i j : Nat) :
    fieldDelta s (witS s i j) = fdWit := by
  simp [fieldDelta, fdWit, witS]

theorem fieldDelta_protS (s : PState) (i j : Nat) :
    fieldDelta s (protS s i j) = fdProt := by
  simp [fieldDelta, fdProt, protS]

theorem fieldDelta_refuseS (s : PState) (i j : Nat) :
    fieldDelta s (refuseS s i j) = fdRefusals := by
  simp [fieldDelta, fdRefusals, refuseS]

theorem fieldDelta_obsS (s : PState) (ho : s.obs = none) :
    fieldDelta s (obsS s) = fdObs := by
  have h : (some ([] : List (List Nat)) != s.obs) = true := by
    rw [ho]; rfl
  simp [fieldDelta, fdObs, obsS, h]

theorem fieldDelta_budS (s : PState) (n : Nat) (h : n ≠ s.budget) :
    fieldDelta s (budS s n) = fdBudget := by
  simp [fieldDelta, fdBudget, budS, bne_true_of_ne h]

theorem fieldDelta_licS (s : PState) (b : Bool) (h : b ≠ s.licensed) :
    fieldDelta s (licS s b) = fdLicensed := by
  simp [fieldDelta, fdLicensed, licS, bne_true_of_ne h]

theorem fieldDelta_haltS (s : PState) (h : s.halted = false) :
    fieldDelta s (haltS s) = fdHalted := by
  have h2 : (true != s.halted) = true := by rw [h]; rfl
  simp [fieldDelta, fdHalted, haltS, h2]

theorem fieldDelta_refineS (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (ho : s.obs = some cols) (hv : v ∈ cols)
    (hb : 0 < s.budget) :
    fieldDelta s (refineS s cols v p) = fdObsBudget := by
  have h1 : (some (cols.map (fun c => if c = v then p :: c else c))
      != s.obs) = true := by
    rw [ho]
    have hne : ¬ (some (cols.map (fun c => if c = v then p :: c else c))
        = some cols) := fun hc =>
      map_replace_ne cols v p hv (Option.some.inj hc)
    simp [hne]
  have h2 : (s.budget - 1 != s.budget) = true :=
    bne_true_of_ne (by omega)
  simp [fieldDelta, fdObsBudget, refineS, h1, h2]

theorem fieldDelta_colS (s : PState) (cols : List (List Nat))
    (c : List Nat) (ho : s.obs = some cols) (hb : 0 < s.budget) :
    fieldDelta s (colS s cols c) = fdObsBudget := by
  have h1 : (some (cols ++ [c]) != s.obs) = true := by
    rw [ho]
    have hne : ¬ (some (cols ++ [c]) = some cols) := fun hc =>
      append_ne cols c (Option.some.inj hc)
    simp [hne]
  have h2 : (s.budget - 1 != s.budget) = true :=
    bne_true_of_ne (by omega)
  simp [fieldDelta, fdObsBudget, colS, h1, h2]

/-- The discharged guard, as a name.  A guard is a *declared*
component of the profile: it records which condition the dynamics
checked, not what changed. -/
inductive GuardKind where
  | occurrenceFresh
  | assertionWellFormed
  | retentionOfAssertion
  | protectionOfRetained
  | preObservational
  | refinementAccepted
  | columnAccepted
  | obstructionCertified
  | budgetWrite
  | licenseWrite
  | terminalDeclaration
deriving Repr, DecidableEq

def guardOf : PEvent → GuardKind
  | .admitOcc _ => .occurrenceFresh
  | .assertWit _ _ => .assertionWellFormed
  | .admitWit _ _ => .retentionOfAssertion
  | .protect _ _ => .protectionOfRetained
  | .declareObs => .preObservational
  | .refineCol _ _ => .refinementAccepted
  | .addCol _ => .columnAccepted
  | .refuse _ _ => .obstructionCertified
  | .setBudget _ => .budgetWrite
  | .setLicense _ => .licenseWrite
  | .halt => .terminalDeclaration

inductive BudgetDelta where
  | unchanged
  | spentOne
  | rewritten
deriving Repr, DecidableEq

def budgetDeltaOf (s t : PState) : BudgetDelta :=
  if t.budget = s.budget then .unchanged
  else if t.budget + 1 = s.budget then .spentOne
  else .rewritten

inductive Continuity where
  | continuation
  | absorption
deriving Repr, DecidableEq

def continuityOf (t : PState) : Continuity :=
  if t.halted then .absorption else .continuation

theorem continuityOf_live (t : PState) (h : t.halted = false) :
    continuityOf t = .continuation := by
  unfold continuityOf; rw [h]; rfl

theorem continuityOf_halted (t : PState) (h : t.halted = true) :
    continuityOf t = .absorption := by
  unfold continuityOf; rw [h]; rfl

/-- A declared policy class attached to each constructor.  The legacy
name `Origin` is retained for compatibility, but this field is not an
issuer, capability, or causal-provenance record.  In particular,
`nextFamilyP` emits `setBudget 1` even though `setBudget` is classified
as `environment`.  The negative claim is discharged for
occurrence supply, license writing and the terminal declaration
(`internal_family_no_occurrence_supply`,
`internal_family_no_license_write`, `internal_family_no_terminal`)
and REFUTED for budget writing
(`internal_family_emits_budget_write`). -/
inductive Origin where
  | environment
  | internal
deriving Repr, DecidableEq

def originOf : PEvent → Origin
  | .admitOcc _ => .environment
  | .setBudget _ => .environment
  | .setLicense _ => .environment
  | .halt => .environment
  | _ => .internal

def isEnvOwned : PEvent → Bool
  | .admitOcc _ => true
  | .setBudget _ => true
  | .setLicense _ => true
  | .halt => true
  | _ => false

theorem isEnvOwned_iff_origin (e : PEvent) :
    isEnvOwned e = true ↔ originOf e = .environment := by
  cases e <;> simp [isEnvOwned, originOf]

/-- The full effect profile of an attempted transition. -/
structure Profile where
  fields : FieldDelta
  guard : GuardKind
  obst : ObstEffect
  budget : BudgetDelta
  cont : Continuity
  origin : Origin
  accepted : Bool
deriving Repr, DecidableEq

def profileOf (s : PState) (e : PEvent) : Profile :=
  { fields := fieldDelta s (step s e),
    guard := guardOf e,
    obst := obstEffect s (step s e),
    budget := budgetDeltaOf s (step s e),
    cont := continuityOf (step s e),
    origin := originOf e,
    accepted := Accepted s e }

/-- A declared one-step projection of the profile.  The two components
dropped here vary within a constructor family.  This projection is not
a contextual congruence: equal signatures can be separated by a common
suffix (`classSig_not_right_congruent_occurrence` and
`classSig_not_right_congruent_budget`). -/
structure ClassSig where
  fields : FieldDelta
  guard : GuardKind
  move : ObstMove
  cont : Continuity
  origin : Origin
deriving Repr, DecidableEq

def sigOf (s : PState) (e : PEvent) : ClassSig :=
  { fields := fieldDelta s (step s e),
    guard := guardOf e,
    move := coarse (obstEffect s (step s e)),
    cont := continuityOf (step s e),
    origin := originOf e }

/-- The same signature with the declared guard label erased: the
purely semantic part of an accepted transition. -/
structure EffectSig where
  fields : FieldDelta
  move : ObstMove
  cont : Continuity
  origin : Origin
deriving Repr, DecidableEq

def eraseGuard (g : ClassSig) : EffectSig :=
  ⟨g.fields, g.move, g.cont, g.origin⟩

def effectSigOf (s : PState) (e : PEvent) : EffectSig :=
  eraseGuard (sigOf s e)

/-! ## 4. The declared well-formed state class

Two conditions only: the state is live, and protection is contained
in retention.  Both are invariants of replay from genesis
(`wf_of_replay`), so the class contains every live reachable state;
and the second condition is load-bearing
(`retention_creates_outside_class`). -/

structure WFClass (s : PState) : Prop where
  live : s.halted = false
  protSubWit : ∀ p ∈ s.prot, p ∈ s.wit

def wfB (s : PState) : Bool :=
  !s.halted && s.prot.all (fun p => decide (p ∈ s.wit))

theorem wf_of_wfB (s : PState) (h : wfB s = true) : WFClass s := by
  unfold wfB at h
  simp only [Bool.and_eq_true, Bool.not_eq_true'] at h
  exact ⟨h.1, fun p hp => of_decide_eq_true (List.all_eq_true.mp h.2 p hp)⟩

theorem protSubWit_step (s : PState)
    (hinv : ∀ p ∈ s.prot, p ∈ s.wit) (e : PEvent) :
    ∀ p ∈ (step s e).prot, p ∈ (step s e).wit := by
  cases e <;> simp only [step] <;> repeat' split
  all_goals
    first
      | exact hinv
      | (intro p hp
         simp only [List.mem_append]
         exact Or.inl (hinv p hp))
      | (rename_i i j hh hg
         intro p hp
         rcases List.mem_append.mp hp with hp' | hp'
         · exact hinv p hp'
         · have hmem : (i, j) ∈ s.wit := by
             simp only [Bool.and_eq_true, decide_eq_true_eq] at hg
             exact hg.1
           cases List.mem_singleton.mp hp'
           exact hmem)

theorem protSubWit_replay (h : List PEvent) :
    ∀ p ∈ (replayP h genesisP).prot, p ∈ (replayP h genesisP).wit := by
  suffices hgen : ∀ (s : PState),
      (∀ p ∈ s.prot, p ∈ s.wit) →
        ∀ p ∈ (replayP h s).prot, p ∈ (replayP h s).wit by
    exact hgen genesisP (by intro p hp; cases hp)
  induction h with
  | nil => intro s hs; exact hs
  | cons e rest ih =>
      intro s hs
      exact ih (step s e) (protSubWit_step s hs e)

/-- Every live replayed state is in the declared class. -/
theorem wf_of_replay (h : List PEvent)
    (hlive : (replayP h genesisP).halted = false) :
    WFClass (replayP h genesisP) :=
  ⟨hlive, protSubWit_replay h⟩

/-! ### The witness states

Nine small concrete states, each written out in full so that every
`decide` below runs on a closed term. -/

def wAssert : PState :=
  { occ := [0, 1], asserted := [], wit := [], prot := [], obs := none,
    budget := 0, licensed := true, refusals := [], halted := false }

def wRetain : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [], prot := [],
    obs := none, budget := 0, licensed := true, refusals := [],
    halted := false }

def wProtectQuiet : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [],
    obs := none, budget := 0, licensed := true, refusals := [],
    halted := false }

def wProtectObstructing : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [],
    obs := some [], budget := 0, licensed := true, refusals := [],
    halted := false }

def wDeclareObstructing : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [(0, 1)],
    obs := none, budget := 0, licensed := true, refusals := [],
    halted := false }

def wObstructed : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [(0, 1)],
    obs := some [], budget := 0, licensed := true, refusals := [],
    halted := false }

def wFunded : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [(0, 1)],
    obs := some [], budget := 1, licensed := true, refusals := [],
    halted := false }

def wRefine : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [(0, 1)],
    obs := some [[]], budget := 1, licensed := true, refusals := [],
    halted := false }

def wFundedUnlicensed : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [(0, 1)],
    obs := some [], budget := 1, licensed := false, refusals := [],
    halted := false }

def wRefineUnlicensed : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)], prot := [(0, 1)],
    obs := some [[]], budget := 1, licensed := false, refusals := [],
    halted := false }

/-- A state OUTSIDE the declared class: a pair protected without ever
having been retained.  No replay from genesis reaches it
(`protSubWit_replay`), and it is the exact countermodel to the
retention lemma (`retention_creates_outside_class`). -/
def outsideClass : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [], prot := [(0, 1)],
    obs := some [], budget := 0, licensed := true, refusals := [],
    halted := false }

/-! ## 5. The declared one-step codes

`EffectClass` and `classOf` are declared together, then the theorem
below proves that this table covers every accepted well-formed step.
Ten of the eleven event constructors contribute one code each;
`protect` and `declareObs` contribute two each.  Thus this declared
projection has thirteen distinct signatures.  The count is relative
to this exact event grammar and projection, not a native cardinality
of the dynamics under arbitrary presentations. -/

inductive EffectClass where
  | supplyOccurrence
  | assertDifference
  | retainDifference
  | protectQuiet
  | protectObstructing
  | declareQuiet
  | declareObstructing
  | refineObservation
  | extendObservation
  | recordRefusal
  | writeBudget
  | writeLicense
  | absorbTerminal
deriving Repr, DecidableEq

def classSig : EffectClass → ClassSig
  | .supplyOccurrence =>
      ⟨fdOcc, .occurrenceFresh, .inert, .continuation, .environment⟩
  | .assertDifference =>
      ⟨fdAsserted, .assertionWellFormed, .inert, .continuation, .internal⟩
  | .retainDifference =>
      ⟨fdWit, .retentionOfAssertion, .inert, .continuation, .internal⟩
  | .protectQuiet =>
      ⟨fdProt, .protectionOfRetained, .inert, .continuation, .internal⟩
  | .protectObstructing =>
      ⟨fdProt, .protectionOfRetained, .creates, .continuation, .internal⟩
  | .declareQuiet =>
      ⟨fdObs, .preObservational, .inert, .continuation, .internal⟩
  | .declareObstructing =>
      ⟨fdObs, .preObservational, .creates, .continuation, .internal⟩
  | .refineObservation =>
      ⟨fdObsBudget, .refinementAccepted, .removes, .continuation, .internal⟩
  | .extendObservation =>
      ⟨fdObsBudget, .columnAccepted, .removes, .continuation, .internal⟩
  | .recordRefusal =>
      ⟨fdRefusals, .obstructionCertified, .inert, .continuation, .internal⟩
  | .writeBudget =>
      ⟨fdBudget, .budgetWrite, .inert, .continuation, .environment⟩
  | .writeLicense =>
      ⟨fdLicensed, .licenseWrite, .inert, .continuation, .environment⟩
  | .absorbTerminal =>
      ⟨fdHalted, .terminalDeclaration, .inert, .absorption, .environment⟩

def classOf (s : PState) : PEvent → EffectClass
  | .admitOcc _ => .supplyOccurrence
  | .assertWit _ _ => .assertDifference
  | .admitWit _ _ => .retainDifference
  | .protect i j =>
      match obstP (protS s i j) i j with
      | true => .protectObstructing
      | false => .protectQuiet
  | .declareObs =>
      match s.prot with
      | [] => .declareQuiet
      | _ :: _ => .declareObstructing
  | .refineCol _ _ => .refineObservation
  | .addCol _ => .extendObservation
  | .refuse _ _ => .recordRefusal
  | .setBudget _ => .writeBudget
  | .setLicense _ => .writeLicense
  | .halt => .absorbTerminal

/-- **Existence.**  Every accepted transition of a well-formed state
has the signature of its class. -/
theorem sig_eq_classSig (s : PState) (hwf : WFClass s) (e : PEvent)
    (hacc : Accepted s e = true) : sigOf s e = classSig (classOf s e) := by
  have hg : guardHolds s e = true := by
    rw [← accepted_eq_guardHolds]; exact hacc
  cases e with
  | admitOcc t =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and,
        Bool.not_eq_true', decide_eq_false_iff_not] at hg
      have hstep : step s (.admitOcc t) = occS s t :=
        step_admitOcc_acc s t hwf.live hg
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_occS,
        obstMove_inert_of_eq s (occS s t) (obstructedPairs_occS s t),
        continuityOf_live (occS s t)
          (show (occS s t).halted = false from hwf.live)]
  | assertWit i j =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hstep : step s (.assertWit i j) = assS s i j :=
        step_assertWit_acc s i j hwf.live hg
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_assS,
        obstMove_inert_of_eq s (assS s i j) (obstructedPairs_assS s i j),
        continuityOf_live (assS s i j)
          (show (assS s i j).halted = false from hwf.live)]
  | admitWit i j =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hstep : step s (.admitWit i j) = witS s i j :=
        step_admitWit_acc s i j hwf.live hg
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_witS,
        obstMove_inert_of_eq s (witS s i j)
          (obstructedPairs_witS s i j hwf.protSubWit),
        continuityOf_live (witS s i j)
          (show (witS s i j).halted = false from hwf.live)]
  | protect i j =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hstep : step s (.protect i j) = protS s i j :=
        step_protect_acc s i j hwf.live hg
      have hnew : (i, j) ∉ s.prot := by
        simp only [Bool.and_eq_true, Bool.not_eq_true',
          decide_eq_false_iff_not] at hg
        exact hg.2
      cases hob : obstP (protS s i j) i j with
      | false =>
          have heq : obstructedPairs (protS s i j) = obstructedPairs s := by
            rw [obstructedPairs_protS s i j, hob, if_neg hfalse,
              List.append_nil]
          simp only [sigOf, classOf, classSig, guardOf, originOf, hstep, hob,
            fieldDelta_protS, obstMove_inert_of_eq s (protS s i j) heq,
            continuityOf_live (protS s i j)
              (show (protS s i j).halted = false from hwf.live)]
      | true =>
          have hset : obstructedPairs (protS s i j)
              = obstructedPairs s ++ [(i, j)] := by
            rw [obstructedPairs_protS s i j, hob, if_pos rfl]
          have hlost : lostPairs s (protS s i j) = [] := by
            unfold lostPairs
            rw [hset]
            exact filter_notmem_eq_nil _ _
              (fun x hx => List.mem_append.mpr (Or.inl hx))
          have hgain : gainedPairs s (protS s i j) ≠ [] := by
            refine list_ne_nil_of_mem (a := (i, j)) ?_
            unfold gainedPairs
            rw [hset]
            refine List.mem_filter.mpr
              ⟨List.mem_append.mpr (Or.inr List.mem_cons_self), ?_⟩
            rw [decide_eq_false (fun hc =>
              hnew (obstructedPairs_sub s (i, j) hc))]
            rfl
          have hcr : obstEffect s (protS s i j) = .created := by
            unfold obstEffect
            rw [hlost]
            simp only [List.isEmpty_nil, Bool.not_true, if_neg hfalse]
            rw [if_pos (isEmpty_not_of_ne _ hgain)]
          simp only [sigOf, classOf, classSig, guardOf, originOf, hstep, hob,
            fieldDelta_protS, hcr, coarse,
            continuityOf_live (protS s i j)
              (show (protS s i j).halted = false from hwf.live)]
  | declareObs =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and,
        decide_eq_true_eq] at hg
      have hstep : step s .declareObs = obsS s :=
        step_declareObs_acc s hwf.live hg
      obtain ⟨h1, h2⟩ := obstructedPairs_obsS s hg hwf.protSubWit
      cases hp : s.prot with
      | nil =>
          have heq : obstructedPairs (obsS s) = obstructedPairs s := by
            rw [h1, h2, hp]
          simp only [sigOf, classOf, classSig, guardOf, originOf, hstep, hp,
            fieldDelta_obsS s hg, obstMove_inert_of_eq s (obsS s) heq,
            continuityOf_live (obsS s)
              (show (obsS s).halted = false from hwf.live)]
      | cons a rest =>
          have hlost : lostPairs s (obsS s) = [] := by
            unfold lostPairs
            rw [h2]
            rfl
          have hgain : gainedPairs s (obsS s) ≠ [] := by
            refine list_ne_nil_of_mem (a := a) ?_
            unfold gainedPairs
            rw [h1, h2, hp]
            exact List.mem_filter.mpr ⟨List.mem_cons_self, rfl⟩
          have hcr : obstEffect s (obsS s) = .created := by
            unfold obstEffect
            rw [hlost]
            simp only [List.isEmpty_nil, Bool.not_true, if_neg hfalse]
            rw [if_pos (isEmpty_not_of_ne _ hgain)]
          simp only [sigOf, classOf, classSig, guardOf, originOf, hstep, hp,
            fieldDelta_obsS s hg, hcr, coarse,
            continuityOf_live (obsS s)
              (show (obsS s).halted = false from hwf.live)]
  | refineCol v p =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hok : refineOk s v p = true := by
        simp only [Bool.and_eq_true] at hg; exact hg.1
      have hb : 0 < s.budget := by
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hg; exact hg.2
      obtain ⟨cols, ho⟩ := refineOk_declared s v p hok
      have hv : v ∈ cols := by
        unfold refineOk at hok
        rw [ho] at hok
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hok
        exact hok.1.1.1.1
      have hstep : step s (.refineCol v p) = refineS s cols v p :=
        step_refineCol_acc s cols v p hwf.live ho hok hb
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_refineS s cols v p ho hv hb,
        obstEffect_refineS s cols v p ho hok, coarse,
        continuityOf_live (refineS s cols v p)
          (show (refineS s cols v p).halted = false from hwf.live)]
  | addCol c =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hok : colOk s c = true := by
        simp only [Bool.and_eq_true] at hg; exact hg.1.1
      have hl : s.licensed = true := by
        simp only [Bool.and_eq_true] at hg; exact hg.1.2
      have hb : 0 < s.budget := by
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hg; exact hg.2
      obtain ⟨cols, ho⟩ := colOk_declared s c hok
      have hstep : step s (.addCol c) = colS s cols c :=
        step_addCol_acc s cols c hwf.live ho hok hl hb
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_colS s cols c ho hb,
        obstEffect_colS s cols c ho hok, coarse,
        continuityOf_live (colS s cols c)
          (show (colS s cols c).halted = false from hwf.live)]
  | refuse i j =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hstep : step s (.refuse i j) = refuseS s i j :=
        step_refuse_acc s i j hwf.live hg
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_refuseS,
        obstMove_inert_of_eq s (refuseS s i j) (obstructedPairs_refuseS s i j),
        continuityOf_live (refuseS s i j)
          (show (refuseS s i j).halted = false from hwf.live)]
  | setBudget n =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and,
        Bool.not_eq_true', decide_eq_false_iff_not] at hg
      have hstep : step s (.setBudget n) = budS s n :=
        step_setBudget_live s n hwf.live
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_budS s n hg,
        obstMove_inert_of_eq s (budS s n) (obstructedPairs_budS s n),
        continuityOf_live (budS s n)
          (show (budS s n).halted = false from hwf.live)]
  | setLicense b =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and,
        Bool.not_eq_true', decide_eq_false_iff_not] at hg
      have hstep : step s (.setLicense b) = licS s b :=
        step_setLicense_live s b hwf.live
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_licS s b hg,
        obstMove_inert_of_eq s (licS s b) (obstructedPairs_licS s b),
        continuityOf_live (licS s b)
          (show (licS s b).halted = false from hwf.live)]
  | halt =>
      have hstep : step s .halt = haltS s := step_halt_eq s
      simp only [sigOf, classOf, classSig, guardOf, originOf, hstep,
        fieldDelta_haltS s hwf.live,
        obstMove_inert_of_eq s (haltS s) (obstructedPairs_haltS s),
        continuityOf_halted (haltS s) rfl]

/-- **Uniqueness.**  Distinct classes have distinct signatures. -/
theorem classSig_inj (k₁ k₂ : EffectClass) (h : classSig k₁ = classSig k₂) :
    k₁ = k₂ := by
  cases k₁ <;> cases k₂ <;> first | rfl | exact absurd h (by decide)

theorem classSig_pairwise_distinct (k₁ k₂ : EffectClass) (h : k₁ ≠ k₂) :
    classSig k₁ ≠ classSig k₂ := fun hc => h (classSig_inj k₁ k₂ hc)

/-- **The partition theorem**: every accepted transition of a
well-formed state belongs to exactly one effect class. -/
theorem exists_unique_class (s : PState) (hwf : WFClass s) (e : PEvent)
    (hacc : Accepted s e = true) :
    ∃ k : EffectClass, sigOf s e = classSig k ∧
      ∀ k' : EffectClass, sigOf s e = classSig k' → k' = k :=
  ⟨classOf s e, sig_eq_classSig s hwf e hacc, fun k hk =>
    classSig_inj k (classOf s e)
      (hk.symm.trans (sig_eq_classSig s hwf e hacc))⟩

/-! ## 6. Size of the declared code image, and its limit -/

def dedup {α : Type} [DecidableEq α] : List α → List α
  | [] => []
  | a :: t => if a ∈ dedup t then dedup t else a :: dedup t

def allClasses : List EffectClass :=
  [.supplyOccurrence, .assertDifference, .retainDifference,
   .protectQuiet, .protectObstructing, .declareQuiet,
   .declareObstructing, .refineObservation, .extendObservation,
   .recordRefusal, .writeBudget, .writeLicense, .absorbTerminal]

theorem allClasses_complete (k : EffectClass) : k ∈ allClasses := by
  cases k <;> decide

/-- The declared table has thirteen distinct signatures. -/
theorem declared_codebook_size :
    (dedup (allClasses.map classSig)).length = 13 := by
  decide

/-- The declared table has twelve values once the guard label is erased: the
same-level refinement and the structure-creating extension have the
same accepted effect. -/
theorem guard_erased_codebook_size :
    (dedup (allClasses.map (fun k => eraseGuard (classSig k)))).length = 12 := by
  decide

/-- Equal signatures at one start state are not preserved by a common
suffix.  The two occurrence admissions have the same one-step code at
genesis, but a second admission of `0` is inert after the first and
accepted after the second. -/
theorem classSig_not_right_congruent_occurrence :
    Accepted genesisP (.admitOcc 0) = true ∧
    Accepted genesisP (.admitOcc 2) = true ∧
    sigOf genesisP (.admitOcc 0) = sigOf genesisP (.admitOcc 2) ∧
    step (step genesisP (.admitOcc 0)) (.admitOcc 0) ≠
      step (step genesisP (.admitOcc 2)) (.admitOcc 0) := by
  decide

/-- The coarser thirteen-code projection also forgets the amount of a
budget write.  From the same obstructed funded state, writes to zero
and one receive the same code, but a following extension is refused in
the first case and accepted in the second. -/
theorem classSig_not_right_congruent_budget :
    let s := budS wObstructed 2
    Accepted s (.setBudget 0) = true ∧
    Accepted s (.setBudget 1) = true ∧
    sigOf s (.setBudget 0) = sigOf s (.setBudget 1) ∧
    step (step s (.setBudget 0)) (.addCol [0]) ≠
      step (step s (.setBudget 1)) (.addCol [0]) := by
  decide

/-- The merge, stated on transitions rather than on the class table:
any accepted refinement and any accepted extension, at any two
well-formed states, have literally the same guard-erased effect
signature. -/
theorem refine_addCol_effect_merge (s₁ s₂ : PState) (hw₁ : WFClass s₁)
    (hw₂ : WFClass s₂) (v : List Nat) (p : Nat) (c : List Nat)
    (h₁ : Accepted s₁ (.refineCol v p) = true)
    (h₂ : Accepted s₂ (.addCol c) = true) :
    effectSigOf s₁ (.refineCol v p) = effectSigOf s₂ (.addCol c) := by
  unfold effectSigOf
  rw [sig_eq_classSig s₁ hw₁ _ h₁, sig_eq_classSig s₂ hw₂ _ h₂]
  simp only [classOf, classSig, eraseGuard]

/-- …and the merge is not a defect of the profile: the two
constructors genuinely differ, but in their ACCEPTANCE DOMAIN, not in
their effect.  On an unlicensed obstructed state the refinement is
available and the extension is not. -/
theorem refine_addCol_domain_countermodel :
    Accepted wRefineUnlicensed (.refineCol [] 0) = true ∧
    Accepted wFundedUnlicensed (.addCol [0]) = false ∧
    Accepted wFunded (.addCol [0]) = true := by decide

/-! ## 7. The two components that are not invariants -/

/-- The `preserved`/`untouched` split is a property of the pre-state:
one and the same constructor realizes both. -/
theorem preserved_untouched_not_invariant :
    obstEffect genesisP (step genesisP (.admitOcc 0)) = .untouched ∧
    obstEffect wObstructed (step wObstructed (.admitOcc 5)) = .preserved ∧
    Accepted genesisP (.admitOcc 0) = true ∧
    Accepted wObstructed (.admitOcc 5) = true := by decide

/-- The budget delta is a property of the event's parameter: an
environment budget write can imitate a funded spend on the budget
field alone.  What separates them is the observation field and the
guard, not the arithmetic. -/
theorem budgetDelta_not_invariant :
    budgetDeltaOf genesisP (step genesisP (.setBudget 3)) = .rewritten ∧
    budgetDeltaOf (budS genesisP 2) (step (budS genesisP 2) (.setBudget 1))
      = .spentOne := by decide

/-- What the class DOES determine about resources: the two funded
guards always spend exactly one unit. -/
theorem budgetDelta_of_funded_guard (s : PState) (hwf : WFClass s)
    (e : PEvent) (hacc : Accepted s e = true)
    (hgk : guardOf e = .refinementAccepted ∨ guardOf e = .columnAccepted) :
    budgetDeltaOf s (step s e) = .spentOne := by
  have hg : guardHolds s e = true := by
    rw [← accepted_eq_guardHolds]; exact hacc
  cases e with
  | refineCol v p =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hok : refineOk s v p = true := by
        simp only [Bool.and_eq_true] at hg; exact hg.1
      have hb : 0 < s.budget := by
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hg; exact hg.2
      obtain ⟨cols, ho⟩ := refineOk_declared s v p hok
      rw [step_refineCol_acc s cols v p hwf.live ho hok hb]
      unfold budgetDeltaOf refineS
      rw [if_neg (by simp only []; omega), if_pos (by simp only []; omega)]
  | addCol c =>
      simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
      have hok : colOk s c = true := by
        simp only [Bool.and_eq_true] at hg; exact hg.1.1
      have hl : s.licensed = true := by
        simp only [Bool.and_eq_true] at hg; exact hg.1.2
      have hb : 0 < s.budget := by
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hg; exact hg.2
      obtain ⟨cols, ho⟩ := colOk_declared s c hok
      rw [step_addCol_acc s cols c hwf.live ho hok hl hb]
      unfold budgetDeltaOf colS
      rw [if_neg (by simp only []; omega), if_pos (by simp only []; omega)]
  | admitOcc t => exact absurd hgk (by simp [guardOf])
  | assertWit i j => exact absurd hgk (by simp [guardOf])
  | admitWit i j => exact absurd hgk (by simp [guardOf])
  | protect i j => exact absurd hgk (by simp [guardOf])
  | declareObs => exact absurd hgk (by simp [guardOf])
  | refuse i j => exact absurd hgk (by simp [guardOf])
  | setBudget n => exact absurd hgk (by simp [guardOf])
  | setLicense b => exact absurd hgk (by simp [guardOf])
  | halt => exact absurd hgk (by simp [guardOf])

/-- And the refusal record always meets the finer value `preserved`:
its guard certifies that an obstruction is active, so the obstruction
set is nonempty and unchanged. -/
theorem refuse_preserves (s : PState) (hwf : WFClass s) (i j : Nat)
    (hacc : Accepted s (.refuse i j) = true) :
    obstEffect s (step s (.refuse i j)) = .preserved := by
  have hg : guardHolds s (.refuse i j) = true := by
    rw [← accepted_eq_guardHolds]; exact hacc
  simp only [guardHolds, hwf.live, Bool.not_false, Bool.true_and] at hg
  have hobst : obstP s i j = true := by
    simp only [Bool.and_eq_true] at hg; exact hg.1
  have hprot : (i, j) ∈ s.prot := by
    unfold obstP at hobst
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hobst
    exact hobst.1.2
  have hne : obstructedPairs s ≠ [] :=
    list_ne_nil_of_mem (mem_obstructedPairs s (i, j) hprot hobst)
  rw [step_refuse_acc s i j hwf.live hg]
  exact (obstEffect_split_of_inert s (refuseS s i j)
    (obstructedPairs_refuseS s i j)).2 hne

/-- The declared class is load-bearing.  Outside it — a pair
protected without being retained — retention itself creates an active
obstruction, which no accepted retention inside the class can do. -/
theorem retention_creates_outside_class :
    wfB outsideClass = false ∧
    Accepted outsideClass (.admitWit 0 1) = true ∧
    coarse (obstEffect outsideClass (step outsideClass (.admitWit 0 1)))
      = .creates := by decide

/-! ## 8. The external-policy constructor class, and its exact limit -/

theorem nextFamily_block_shape (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) :
    (∃ m : List Nat × Nat, b = [PEvent.refineCol m.1 m.2]) ∨
    (∃ c : List Nat, b = [PEvent.setBudget 1, PEvent.addCol c]) := by
  unfold nextFamilyP at hb
  obtain ⟨r, _, hb2⟩ := List.mem_flatMap.mp hb
  rcases List.mem_append.mp hb2 with h | h
  · obtain ⟨m, _, he⟩ := List.mem_map.mp h
    exact Or.inl ⟨m, he.symm⟩
  · obtain ⟨c, _, he⟩ := List.mem_map.mp h
    exact Or.inr ⟨c, he.symm⟩

theorem internal_family_no_occurrence_supply (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) (t : Nat) : PEvent.admitOcc t ∉ b := by
  rcases nextFamily_block_shape s b hb with ⟨m, he⟩ | ⟨c, he⟩ <;> subst he <;>
    simp

theorem internal_family_no_license_write (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) (x : Bool) : PEvent.setLicense x ∉ b := by
  rcases nextFamily_block_shape s b hb with ⟨m, he⟩ | ⟨c, he⟩ <;> subst he <;>
    simp

theorem internal_family_no_terminal (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) : PEvent.halt ∉ b := by
  rcases nextFamily_block_shape s b hb with ⟨m, he⟩ | ⟨c, he⟩ <;> subst he <;>
    simp

/-- **REFUTATION.**  The classification "no externally classified
constructor is ever generated by the internal response family" is
false as stated: every extension block the generator produces begins
with a budget write.  This shows why the class label is not provenance. -/
theorem internal_family_emits_budget_write :
    [PEvent.setBudget 1, PEvent.addCol [0]] ∈ nextFamilyP wObstructed := by
  decide

theorem env_ownership_claim_refuted :
    ∃ (s : PState) (b : List PEvent) (e : PEvent),
      b ∈ nextFamilyP s ∧ e ∈ b ∧ isEnvOwned e = true :=
  ⟨wObstructed, [PEvent.setBudget 1, PEvent.addCol [0]], PEvent.setBudget 1,
    internal_family_emits_budget_write, by simp, rfl⟩

/-- **The exact repaired statement.**  The only externally classified
constructor the generator ever emits is the unit funding write; every
other externally classified constructor is absent from these blocks. -/
theorem internal_family_env_only_unit_funding (s : PState) (b : List PEvent)
    (hb : b ∈ nextFamilyP s) (e : PEvent) (he : e ∈ b)
    (hen : isEnvOwned e = true) : e = PEvent.setBudget 1 := by
  rcases nextFamily_block_shape s b hb with ⟨m, hb2⟩ | ⟨c, hb2⟩ <;> subst hb2
  · rw [List.mem_singleton] at he
    subst he
    exact absurd hen (by simp [isEnvOwned])
  · rcases List.mem_cons.mp he with h | h
    · exact h
    · rw [List.mem_singleton] at h
      subst h
      exact absurd hen (by simp [isEnvOwned])

/-- Non-environment events never touch the two fields the environment
owns outright. -/
theorem nonEnv_preserves_occ_licensed (s : PState) (e : PEvent)
    (h : isEnvOwned e = false) :
    (step s e).occ = s.occ ∧ (step s e).licensed = s.licensed := by
  cases e with
  | admitOcc t => exact absurd h (by simp [isEnvOwned])
  | setBudget n => exact absurd h (by simp [isEnvOwned])
  | setLicense b => exact absurd h (by simp [isEnvOwned])
  | halt => exact absurd h (by simp [isEnvOwned])
  | assertWit i j => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩
  | admitWit i j => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩
  | protect i j => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩
  | declareObs => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩
  | refineCol v p => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩
  | addCol c => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩
  | refuse i j => (simp only [step]; repeat' split) <;> exact ⟨rfl, rfl⟩

/-! ## 9. One minimum witness per class

Each witness is checked for membership in the declared class, for
acceptance, and for its signature, by `decide`, and its size is
recorded.  These witnesses are additionally store-coherent (retention
of an assertion, protection of a retention, in-bounds positions), so
they are NOT in general the smallest states of the declared class that
realize their letter: `WFClass` asks only for liveness and protection
inside retention.  The exhaustive minimum over the declared class
inside a declared finite state space is the Python mirror's
computation, and is reported there as computation, not as theorem. -/

def sizeP (s : PState) : Nat :=
  s.occ.length + s.asserted.length + s.wit.length + s.prot.length
    + s.refusals.length + s.budget
    + (match s.obs with | none => 0 | some cols => 1 + cols.length)

theorem class_witnesses :
    (wfB genesisP = true ∧ Accepted genesisP (.admitOcc 0) = true ∧
      sigOf genesisP (.admitOcc 0) = classSig .supplyOccurrence) ∧
    (wfB wAssert = true ∧ Accepted wAssert (.assertWit 0 1) = true ∧
      sigOf wAssert (.assertWit 0 1) = classSig .assertDifference) ∧
    (wfB wRetain = true ∧ Accepted wRetain (.admitWit 0 1) = true ∧
      sigOf wRetain (.admitWit 0 1) = classSig .retainDifference) ∧
    (wfB wProtectQuiet = true ∧ Accepted wProtectQuiet (.protect 0 1) = true ∧
      sigOf wProtectQuiet (.protect 0 1) = classSig .protectQuiet) ∧
    (wfB wProtectObstructing = true ∧
      Accepted wProtectObstructing (.protect 0 1) = true ∧
      sigOf wProtectObstructing (.protect 0 1)
        = classSig .protectObstructing) ∧
    (wfB genesisP = true ∧ Accepted genesisP .declareObs = true ∧
      sigOf genesisP .declareObs = classSig .declareQuiet) ∧
    (wfB wDeclareObstructing = true ∧
      Accepted wDeclareObstructing .declareObs = true ∧
      sigOf wDeclareObstructing .declareObs
        = classSig .declareObstructing) ∧
    (wfB wRefine = true ∧ Accepted wRefine (.refineCol [] 0) = true ∧
      sigOf wRefine (.refineCol [] 0) = classSig .refineObservation) ∧
    (wfB wFunded = true ∧ Accepted wFunded (.addCol [0]) = true ∧
      sigOf wFunded (.addCol [0]) = classSig .extendObservation) ∧
    (wfB wObstructed = true ∧ Accepted wObstructed (.refuse 0 1) = true ∧
      sigOf wObstructed (.refuse 0 1) = classSig .recordRefusal) ∧
    (wfB genesisP = true ∧ Accepted genesisP (.setBudget 1) = true ∧
      sigOf genesisP (.setBudget 1) = classSig .writeBudget) ∧
    (wfB genesisP = true ∧ Accepted genesisP (.setLicense false) = true ∧
      sigOf genesisP (.setLicense false) = classSig .writeLicense) ∧
    (wfB genesisP = true ∧ Accepted genesisP .halt = true ∧
      sigOf genesisP .halt = classSig .absorbTerminal) := by decide

theorem class_witness_sizes :
    sizeP genesisP = 0 ∧ sizeP wAssert = 2 ∧ sizeP wRetain = 3 ∧
    sizeP wProtectQuiet = 4 ∧ sizeP wProtectObstructing = 5 ∧
    sizeP wDeclareObstructing = 5 ∧ sizeP wRefine = 8 ∧
    sizeP wFunded = 7 ∧ sizeP wObstructed = 6 := by decide

end TransitionAlphabet
