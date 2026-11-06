import Derivation.PrimitivePassage

/-!
# Trace stability of separation: what protection buys, and what it does not

**Audit repair.**  The review draft claimed "stable content is exactly
protected separation".  That claim was an overclaim: only the
SUFFICIENCY direction was proved, and the converse is FALSE.  This
module states the actual trace-stability predicate, proves the true
direction, and records the converse's countermodels.

1. **Trace stability, defined** (`TraceStableSep`): the pair stays
   separated by the declared observation after EVERY replay of the
   declared event grammar.  `RestrictedStableSep` is the same over an
   explicitly restricted fragment omitting occurrence admission,
   budget setting, and license setting.  This is a syntactic fragment,
   not an ownership boundary.
2. **Protected separation is SUFFICIENT** (`protSep_trace_stable`):
   protected ∧ separated ⟹ trace stable.  Supply events do not touch
   observation, new columns only add separators, and same-level
   refinement is guarded by exactly the monotone preservation of
   protected separations.
3. **The full converse is FALSE; restricted stability is weaker.**
   `halted_stable_not_protected`: on an absorbed (halted) state every
   replay is inert, so an UNPROTECTED separation is trace stable.
   `unfunded_restricted_stable_not_protected`: on a live but unfunded
   state (`budget = 0`) no event in the restricted fragment can change
   the observation, so an UNPROTECTED separation is restricted-stable.
   The latter is not a second countermodel to full trace stability.
4. **Instability needs a witness** (`separation_breakable`): an
   unprotected separation is destroyed only when a concrete breaking
   witness exists — a fundable accepted refinement through the one
   column that separates it.  `unprotected_separation_unstable` is the
   concrete instance.

**What is proved and what is OPEN.**  Sufficiency is a theorem;
instability-given-a-witness is a theorem; the two together sandwich
the truth but do not meet.  The exact characterization of trace
stability over all declared live, funded states is
**OPEN** — see `openExactStabilityCharacterization`.  Nothing in this
module claims that trace stability implies protection, and no
reachability restriction is built into the open proposition.

5. **Quiescence** (`quiescent_iff_protected_separated`,
   `quiescence_is_protected_separation`): on a declared state, no pair
   is actively obstructed exactly when every retained protected pair
   is separated.  That is an honest iff about `protSep`, and it is NOT
   a claim about trace stability.

Scope: every theorem quantifies over the declared event grammar of
`PrimitivePassage.step` only; pre-observational states have no
separations to stabilize.
-/

namespace StableContent

open PrimitivePassage

/-! ## 1. Protected separation, and the two stability predicates -/

/-- Protected separation: the pair is protected AND the declared
observation separates it.  This is a property of the state, not yet a
stability claim. -/
def protSep (s : PState) (i j : Nat) : Bool :=
  (decide ((i, j) ∈ s.prot))
    && (match s.obs with
        | none => false
        | some cols => sepP cols i j)

/-- The pair is separated by the state's declared observation. -/
def SepHere (s : PState) (i j : Nat) : Prop :=
  ∃ cols, s.obs = some cols ∧ sepP cols i j = true

/-- **Trace stability**: the pair remains separated after EVERY replay
of the declared grammar.  This is the predicate the review draft was
missing. -/
def TraceStableSep (s : PState) (i j : Nat) : Prop :=
  ∀ h : List PEvent, SepHere (replayP h s) i j

/-- The event forms omitted by the restricted trace fragment below.
This is a syntactic classification only: it makes no claim about who
owns or emits these events.  In particular generated repair blocks may
contain `setBudget`. -/
def IsTraceExcludedEvent : PEvent → Bool
  | .admitOcc _ => true
  | .setBudget _ => true
  | .setLicense _ => true
  | _ => false

/-- A restricted trace contains no occurrence-admission, budget-setting,
or license-setting event. -/
def RestrictedTrace (h : List PEvent) : Prop :=
  ∀ e ∈ h, IsTraceExcludedEvent e = false

/-- **Restricted stability**: the pair remains separated after every
replay in the explicitly restricted fragment.  This is weaker than
`TraceStableSep`; it is not a claim about an ownership boundary. -/
def RestrictedStableSep (s : PState) (i j : Nat) : Prop :=
  ∀ h : List PEvent, RestrictedTrace h → SepHere (replayP h s) i j

/-! ## 2. Sufficiency: protected separation is trace stable -/

theorem sepP_append (cols : List (List Nat)) (c : List Nat)
    (i j : Nat) (h : sepP cols i j = true) :
    sepP (cols ++ [c]) i j = true := by
  unfold sepP at h ⊢
  rw [List.any_append, h]
  rfl

/-- The refinement guard hands back exactly what stability needs:
an accepted refinement preserves every protected separation. -/
theorem sepP_refine (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (i j : Nat)
    (hobs : s.obs = some cols) (hro : refineOk s v p = true)
    (hp : (i, j) ∈ s.prot) (hsep : sepP cols i j = true) :
    sepP (cols.map (fun c => if c = v then p :: c else c)) i j
      = true := by
  unfold refineOk at hro
  rw [hobs] at hro
  simp only [Bool.and_eq_true] at hro
  have hall := hro.2
  rw [List.all_eq_true] at hall
  have hthis := hall (i, j) hp
  rw [hsep] at hthis
  simp only [Bool.not_true, Bool.false_or] at hthis
  exact hthis

/-- Protection is never lost: every event's result keeps every
protected pair protected. -/
theorem prot_mono (s : PState) (e : PEvent) (i j : Nat)
    (h : (i, j) ∈ s.prot) : (i, j) ∈ (step s e).prot := by
  cases e <;> unfold step <;> (repeat' split) <;>
    first
      | exact h
      | exact List.mem_append.mpr (Or.inl h)

/-- Separation of a protected pair survives every event. -/
theorem sep_preserved (s : PState) (e : PEvent) (i j : Nat)
    (cols : List (List Nat)) (hobs : s.obs = some cols)
    (hp : (i, j) ∈ s.prot) (hsep : sepP cols i j = true) :
    ∃ cols', (step s e).obs = some cols'
      ∧ sepP cols' i j = true := by
  cases e with
  | admitOcc t =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨cols, hobs, hsep⟩
  | assertWit a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨cols, hobs, hsep⟩
  | admitWit a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨cols, hobs, hsep⟩
  | protect a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨cols, hobs, hsep⟩
  | declareObs =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
              hobs]
          exact ⟨cols, hobs, hsep⟩
  | refineCol v p =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          by_cases hg : (refineOk s v p && decide (0 < s.budget))
              = true
          · have hg2 := hg
            simp only [Bool.and_eq_true] at hg2
            rw [if_pos hg, hobs]
            refine ⟨_, rfl, ?_⟩
            exact sepP_refine s cols v p i j hobs hg2.1 hp hsep
          · rw [if_neg hg]
            exact ⟨cols, hobs, hsep⟩
  | addCol c =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          by_cases hg : (colOk s c && s.licensed
              && decide (0 < s.budget)) = true
          · rw [if_pos hg, hobs]
            exact ⟨cols ++ [c], rfl, sepP_append cols c i j hsep⟩
          · rw [if_neg hg]
            exact ⟨cols, hobs, hsep⟩
  | refuse a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨cols, hobs, hsep⟩
  | setBudget n =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          exact ⟨cols, hobs, hsep⟩
  | setLicense b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨cols, hobs, hsep⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          exact ⟨cols, hobs, hsep⟩
  | halt => exact ⟨cols, hobs, hsep⟩

/-- Protected separation persists at every step. -/
theorem protSep_persists (s : PState) (e : PEvent)
    (i j : Nat) (h : protSep s i j = true) :
    protSep (step s e) i j = true := by
  unfold protSep at h
  simp only [Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨hp, hsep⟩ := h
  cases hobs : s.obs with
  | none => rw [hobs] at hsep; cases hsep
  | some cols =>
      rw [hobs] at hsep
      obtain ⟨cols', hobs', hsep'⟩ :=
        sep_preserved s e i j cols hobs hp hsep
      unfold protSep
      rw [hobs', decide_eq_true (prot_mono s e i j hp)]
      show (true && sepP cols' i j) = true
      rw [hsep']
      exact rfl

/-- Protected separation persists along every replay. -/
theorem protSep_replays (h : List PEvent) :
    ∀ (s : PState) (i j : Nat), protSep s i j = true →
      protSep (replayP h s) i j = true := by
  induction h with
  | nil =>
      intro s i j hs
      exact hs
  | cons e t ih =>
      intro s i j hs
      show protSep (replayP t (step s e)) i j = true
      exact ih (step s e) i j (protSep_persists s e i j hs)

/-- **Sufficiency (the true direction)**: protected separation implies
trace stability.  This is everything the review draft actually
proved. -/
theorem protSep_trace_stable (s : PState) (i j : Nat)
    (h : protSep s i j = true) : TraceStableSep s i j := by
  intro tr
  have hrep := protSep_replays tr s i j h
  unfold protSep at hrep
  simp only [Bool.and_eq_true] at hrep
  cases hobs : (replayP tr s).obs with
  | none =>
      exfalso
      have := hrep.2
      rw [hobs] at this
      exact Bool.noConfusion this
  | some cols =>
      refine ⟨cols, hobs, ?_⟩
      have := hrep.2
      rw [hobs] at this
      exact this

/-- Trace stability is stronger than restricted stability. -/
theorem trace_stable_restricted_stable (s : PState) (i j : Nat)
    (h : TraceStableSep s i j) : RestrictedStableSep s i j :=
  fun tr _ => h tr

/-! ## 3. The converse is FALSE — countermodel 1: absorption -/

/-- On a halted state every replay is inert: the terminal absorbs the
whole grammar. -/
theorem replay_halted (h : List PEvent) :
    ∀ s : PState, s.halted = true → replayP h s = s := by
  induction h with
  | nil => intro s _; rfl
  | cons e t ih =>
      intro s hs
      show replayP t (step s e) = s
      rw [step_halted s e hs]
      exact ih s hs

/-- An absorbed state carrying an UNPROTECTED separation. -/
def sHalt : PState :=
  { occ := [0, 1], asserted := [], wit := [], prot := [],
    obs := some [[0]], budget := 0, licensed := true,
    refusals := [], halted := true }

/-- **Countermodel 1 to the converse (absorption)**: on the halted
state every replay is inert, so the pair `(0, 1)` is TRACE STABLE —
yet it is not protected, and `protSep` is false.  Trace stability
therefore does NOT imply protected separation. -/
theorem halted_stable_not_protected :
    TraceStableSep sHalt 0 1 ∧ protSep sHalt 0 1 = false := by
  constructor
  · intro tr
    rw [replay_halted tr sHalt rfl]
    exact ⟨[[0]], rfl, by decide⟩
  · decide

/-! ## 4. Countermodel 2: resource blocking on a restricted fragment -/

/-- On an unfunded declared state no event in the restricted fragment
changes the observation or the budget: the two structure-creating
moves are budget-gated, while all three event forms capable of changing
the selected resource/control fields are outside this fragment. -/
theorem restricted_step_inert_unfunded (s : PState) (e : PEvent)
    (cols : List (List Nat)) (henv : IsTraceExcludedEvent e = false)
    (hobs : s.obs = some cols) (hb : s.budget = 0) :
    (step s e).obs = some cols ∧ (step s e).budget = 0 := by
  cases e with
  | admitOcc t => exact absurd henv (by simp [IsTraceExcludedEvent])
  | setBudget n => exact absurd henv (by simp [IsTraceExcludedEvent])
  | setLicense b => exact absurd henv (by simp [IsTraceExcludedEvent])
  | assertWit a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨hobs, hb⟩
  | admitWit a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨hobs, hb⟩
  | protect a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨hobs, hb⟩
  | refuse a b =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          repeat' split
          all_goals exact ⟨hobs, hb⟩
  | declareObs =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
              hobs]
          exact ⟨hobs, hb⟩
  | refineCol v p =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          rw [if_neg (by
            intro hc
            simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
            have := hc.2
            omega)]
          exact ⟨hobs, hb⟩
  | addCol c =>
      cases hhb : s.halted with
      | true => rw [step_halted s _ hhb]; exact ⟨hobs, hb⟩
      | false =>
          simp only [step, hhb]
          rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]
          rw [if_neg (by
            intro hc
            simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
            have := hc.2
            omega)]
          exact ⟨hobs, hb⟩
  | halt =>
      show ({ s with halted := true } : PState).obs = some cols
        ∧ ({ s with halted := true } : PState).budget = 0
      exact ⟨hobs, hb⟩

theorem restricted_replay_inert_unfunded (h : List PEvent) :
    ∀ (s : PState) (cols : List (List Nat)), RestrictedTrace h →
      s.obs = some cols → s.budget = 0 →
      (replayP h s).obs = some cols ∧ (replayP h s).budget = 0 := by
  induction h with
  | nil => intro s cols _ hobs hb; exact ⟨hobs, hb⟩
  | cons e t ih =>
      intro s cols hint hobs hb
      have henv : IsTraceExcludedEvent e = false :=
        hint e List.mem_cons_self
      obtain ⟨ho, hbb⟩ :=
        restricted_step_inert_unfunded s e cols henv hobs hb
      show (replayP t (step s e)).obs = some cols
        ∧ (replayP t (step s e)).budget = 0
      exact ih (step s e) cols
        (fun x hx => hint x (List.mem_cons_of_mem e hx)) ho hbb

/-- A live, declared, but UNFUNDED state carrying an unprotected
separation. -/
def sUnfunded : PState :=
  { occ := [0, 1], asserted := [], wit := [], prot := [],
    obs := some [[0]], budget := 0, licensed := true,
    refusals := [], halted := false }

/-- **Countermodel 2 (resource blocking, restricted scope)**: this
declared state is live but unfunded.  No event in `RestrictedTrace`
changes its observation, so `(0, 1)` is restricted-stable yet is not
protected.  This is not a countermodel to full trace stability and
makes no event-ownership claim; a `setBudget` event leaves the fragment
and can enable later observation change. -/
theorem unfunded_restricted_stable_not_protected :
    RestrictedStableSep sUnfunded 0 1 ∧ protSep sUnfunded 0 1 = false
      ∧ sUnfunded.halted = false := by
  refine ⟨?_, by decide, rfl⟩
  intro tr hint
  obtain ⟨ho, _⟩ :=
    restricted_replay_inert_unfunded tr sUnfunded [[0]] hint rfl rfl
  exact ⟨[[0]], ho, by decide⟩

/-! ## 5. Instability requires a breaking witness -/

/-- **Instability is witness-borne**: an unprotected separation is
destroyed exactly when a concrete accepted refinement exists that
routes through the separating column.  The hypotheses ARE the witness;
no existence claim is smuggled. -/
theorem separation_breakable (s : PState) (cols : List (List Nat))
    (v : List Nat) (p : Nat) (i j : Nat)
    (hh : s.halted = false) (hobs : s.obs = some cols)
    (hro : refineOk s v p = true) (hfund : 0 < s.budget)
    (hbroken :
      sepP (cols.map (fun c => if c = v then p :: c else c)) i j
        = false) :
    ¬ SepHere (step s (.refineCol v p)) i j := by
  intro hsep
  obtain ⟨cols', hobs', hsep'⟩ := hsep
  have hstep : (step s (.refineCol v p)).obs
      = some (cols.map (fun c => if c = v then p :: c else c)) := by
    simp only [step, hh]
    rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
        if_pos (by
          rw [hro, decide_eq_true hfund]
          rfl),
        hobs]
  rw [hstep] at hobs'
  have : cols' = cols.map (fun c => if c = v then p :: c else c) :=
    Option.some.inj hobs'.symm
  rw [this, hbroken] at hsep'
  exact Bool.noConfusion hsep'

/-- The concrete breaking instance: at `sUnprot` the pair `(1, 2)` is
protected and obstructed, the refinement discharging it is accepted
and funded, and it DESTROYS the unprotected separation of `(0, 1)`
while keeping the protected content intact.  Protection is
load-bearing. -/
def sUnprot : PState :=
  { occ := [0, 1, 2], asserted := [(1, 2)], wit := [(1, 2)],
    prot := [(1, 2)], obs := some [[0]], budget := 1,
    licensed := true, refusals := [], halted := false }

theorem unprotected_separation_unstable :
    (sepP [[0]] 0 1 = true) ∧
    ((step sUnprot (.refineCol [0] 1)).obs = some [[1, 0]]) ∧
    (sepP [[1, 0]] 0 1 = false) ∧
    ((1, 2) ∈ sUnprot.prot) ∧
    (sepP [[1, 0]] 1 2 = true) ∧
    (protSep sUnprot 0 1 = false) := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;> decide

/-- **The remaining gap, stated as a proposition and NOT proved.**
Sufficiency (`protSep_trace_stable`) and witness-borne instability
(`separation_breakable`) sandwich the truth without meeting: between
them lie the unprotected separations at live funded states that carry
no breaking witness.  Whether every such separation is breakable —
equivalently whether trace stability coincides with protected
separation on the live, funded class — is OPEN.  It is recorded here
as a statement, never as a theorem. -/
def openExactStabilityCharacterization : Prop :=
  ∀ (s : PState) (i j : Nat), s.halted = false → 0 < s.budget →
    SepHere s i j → TraceStableSep s i j → protSep s i j = true

/-! ## 6. Quiescence -/

/-- Quiescence: no pair is actively obstructed. -/
def quiescentP (s : PState) : Prop := ∀ i j, obstP s i j = false

/-- **Quiescence ⟺ every retained protected pair is separated**, on
a declared state. -/
theorem quiescent_iff_protected_separated (s : PState)
    (cols : List (List Nat)) (hobs : s.obs = some cols) :
    quiescentP s ↔
      (∀ pr, pr ∈ s.prot → pr ∈ s.wit →
        sepP cols pr.1 pr.2 = true) := by
  constructor
  · intro hq pr hp hw
    obtain ⟨a, b⟩ := pr
    have h := hq a b
    rw [obst_agrees_when_declared s cols hobs] at h
    rw [decide_eq_true hw, decide_eq_true hp] at h
    simp only [Bool.true_and] at h
    cases hb : sepP cols a b with
    | true => rfl
    | false =>
        exfalso
        unfold zeroP at h
        rw [hb] at h
        exact Bool.noConfusion h
  · intro hs i j
    rw [obst_agrees_when_declared s cols hobs]
    by_cases hw : (i, j) ∈ s.wit
    · by_cases hp : (i, j) ∈ s.prot
      · have hsep := hs (i, j) hp hw
        unfold zeroP
        rw [decide_eq_true hw, decide_eq_true hp, hsep]
        rfl
      · rw [decide_eq_false hp]
        simp
    · rw [decide_eq_false hw]
      simp

/-- **Quiescence is protected separation of every retained protected
pair**: on a declared state, no pair obstructs exactly when every
retained protected pair is protected-separated.  This is a statement
about `protSep`, NOT about trace stability. -/
theorem quiescence_is_protected_separation (s : PState)
    (cols : List (List Nat)) (hobs : s.obs = some cols) :
    quiescentP s ↔
      (∀ pr, pr ∈ s.prot → pr ∈ s.wit →
        protSep s pr.1 pr.2 = true) := by
  rw [quiescent_iff_protected_separated s cols hobs]
  constructor
  · intro hs pr hp hw
    unfold protSep
    rw [hobs, decide_eq_true (show (pr.1, pr.2) ∈ s.prot from hp)]
    show (true && sepP cols pr.1 pr.2) = true
    rw [hs pr hp hw]
    exact rfl
  · intro hs pr hp hw
    have h := hs pr hp hw
    unfold protSep at h
    rw [hobs] at h
    simp only [Bool.and_eq_true] at h
    exact h.2

/-- Quiescent declared states have every retained protected pair
TRACE STABLE — the corollary that does hold, by sufficiency. -/
theorem quiescent_retained_protected_trace_stable (s : PState)
    (cols : List (List Nat)) (hobs : s.obs = some cols)
    (hq : quiescentP s) :
    ∀ pr, pr ∈ s.prot → pr ∈ s.wit →
      TraceStableSep s pr.1 pr.2 := by
  intro pr hp hw
  exact protSep_trace_stable s pr.1 pr.2
    ((quiescence_is_protected_separation s cols hobs).mp hq pr hp hw)

end StableContent
