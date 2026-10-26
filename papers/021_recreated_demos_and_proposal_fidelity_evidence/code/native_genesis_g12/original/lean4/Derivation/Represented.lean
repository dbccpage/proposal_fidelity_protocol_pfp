/-!
# Represented progress without an outside

Externally imposed challenge (caller assignment, 2026-08-12).  The
decisive question: can all load-bearing causes of represented progress
themselves be represented, without leaving a hidden evaluator,
selector, or source outside the replay semantics?

This module is native and self-contained (core Lean only).  It builds
one kernel in which every input that can change a transition —
evaluator, requirement, scheduler, tie-break, fresh-name source, fuel,
authorization, stopping condition — occurs in the represented state or
the represented history, proves the eight target theorems for that
kernel, and exhibits the eight required countermodels as minimal
non-kernel semantics, each consuming exactly one unrepresented input.

Required native definitions and where they live:

* representation           — `World` (data store, view columns, records)
* admitted transformation  — `Event` + the acceptance-guarded `step`
* represented history      — `List Event`; replay — `replay`
* recorded requirement     — `World.reqs`
* obstruction              — `obstructedB` (recorded requirement plus
                             exhaustive failure of the declared finite
                             response menu — never mere lookalikeness)
* same-structure repair    — `Event.mark` (guarded by `markOkB`)
* structure-creating
  augmentation             — `Event.addView` (guarded by `augOkB`)
* represented support      — `supp`
* internally determined
  successor family         — `repairFamily` (all tied responses kept)
* replay-equivalence       — `WEquiv` / `SameElems`

The kernel constitution — fixed metatheory, not represented runtime
input: the event grammar (`Event`), the separation and satisfaction
laws (`sepB`, `satB`), the declared response menu (`responseMenu`),
the acceptance predicates (`reqOkB`, `markOkB`, `augOkB`,
`obstructedB`), and the history producer that supplies event streams.
The theorems say: *relative to this fixed constitution*, no hidden
runtime input reaches a transition.  They do not say the constitution
derives itself.

No-hidden-choice is scoped to `repairFamily` (same-structure
responses, all ties retained).  The progress theorem's structural
branch exhibits the canonical augmentation `[i]`, whose orientation is
supplied by the *ordered, recorded* requirement `(i, j)` — a
represented datum, and a stated scoping, not a hidden selector.

Evidence classes: every statement below is a theorem or a decidable
instance; policies (budget, augmentation license) are state fields;
conjectures are confined to the paper.
-/

namespace Represented

/-! ## Small Bool bridges -/

theorem bool_eq_of_iff {a b : Bool} (h : a = true ↔ b = true) :
    a = b := by
  cases a <;> cases b <;> simp_all

theorem or_not_eq_true {a b : Bool} :
    (!a || b) = true ↔ (a = true → b = true) := by
  cases a <;> cases b <;> simp

/-! ## Representation -/

/-- A view column: the marked data positions.  Views are set-like;
membership is their whole content. -/
abbrev View := List Nat

/-- A recorded requirement: separate the data positions `i` and `j`. -/
abbrev Req := Nat × Nat

/-- The represented state.  Every load-bearing input lives here:
`budget` is the fuel, `augLicensed` the structure-creation
authorization, `refusals` the represented unresolved obstructions,
`notes` a represented but transition-inert commentary field (used by
the support theorem). -/
structure World where
  data : List Nat
  views : List View
  reqs : List Req
  refusals : List Req
  budget : Nat
  augLicensed : Bool
  notes : List Nat
deriving Repr, DecidableEq

def genesis : World := ⟨[], [], [], [], 0, true, []⟩

/-! ## Observation semantics (decidable throughout) -/

def sepB (c : View) (i j : Nat) : Bool :=
  (decide (i ∈ c)) != (decide (j ∈ c))

def satB (w : World) (r : Req) : Bool :=
  w.views.any (fun c => sepB c r.1 r.2)

def violB (w : World) (r : Req) : Bool :=
  (decide (r ∈ w.reqs)) && !satB w r

def quiescentB (w : World) : Bool :=
  w.reqs.all (fun r => satB w r)

/-! ## Same-structure repair: acceptance and application -/

def markApply (w : World) (v : View) (p : Nat) : World :=
  { w with views := w.views.map (fun c => if c = v then p :: c else c) }

def preservesB (w w' : World) : Bool :=
  w.reqs.all (fun r => !satB w r || satB w' r)

def dischargesSomeB (w w' : World) : Bool :=
  w.reqs.any (fun r => violB w r && satB w' r)

def markOkB (w : World) (v : View) (p : Nat) : Bool :=
  (decide (v ∈ w.views)) && (decide (p < w.data.length))
    && !(decide (p ∈ v))
    && dischargesSomeB w (markApply w v p)
    && preservesB w (markApply w v p)

/-! ## Structure-creating augmentation: acceptance and application -/

def augApply (w : World) (c : View) : World :=
  { w with views := w.views ++ [c] }

def increaseB (w : World) (c : View) : Bool :=
  (List.range w.data.length).any fun i =>
    (List.range w.data.length).any fun j =>
      (i != j) && sepB c i j && !satB w (i, j)

def augOkB (w : World) (c : View) : Bool :=
  c.all (fun p => decide (p < w.data.length))
    && !(decide (c ∈ w.views))
    && increaseB w c

/-! ## The declared finite response menu and the obstruction predicate

An obstruction is never "two items look alike": it is a recorded,
currently violated requirement together with the exhaustive failure of
the declared finite response menu. -/

def responseMenu (w : World) : List (View × Nat) :=
  w.views.flatMap fun v =>
    (List.range w.data.length).map fun p => (v, p)

def repairsB (w : World) (m : View × Nat) (r : Req) : Bool :=
  markOkB w m.1 m.2 && satB (markApply w m.1 m.2) r

def repairFamily (w : World) (r : Req) : List (View × Nat) :=
  (responseMenu w).filter (fun m => repairsB w m r)

def obstructedB (w : World) (r : Req) : Bool :=
  violB w r && (responseMenu w).all (fun m => !repairsB w m r)

/-! ## Events and the step function

Every event carries its own content; the step consumes nothing else.
Fresh names arrive in `admitTok` events (history-represented), fuel by
`setBudget`, authorization by `setAugLicense`, refusal by `refuse`
(recordable only with a verified obstruction certificate). -/

inductive Event where
  | admitTok (tok : Nat)
  | require (i j : Nat)
  | mark (v : View) (p : Nat)
  | addView (c : View)
  | refuse (i j : Nat)
  | note (n : Nat)
  | setBudget (n : Nat)
  | setAugLicense (b : Bool)
deriving Repr, DecidableEq

def reqOkB (w : World) (i j : Nat) : Bool :=
  (i != j) && (decide (i < w.data.length))
    && (decide (j < w.data.length)) && !(decide ((i, j) ∈ w.reqs))

def step (w : World) : Event → World
  | .admitTok t =>
      if t ∈ w.data then w else { w with data := w.data ++ [t] }
  | .require i j =>
      if reqOkB w i j then { w with reqs := w.reqs ++ [(i, j)] } else w
  | .mark v p =>
      if markOkB w v p && decide (0 < w.budget) then
        { markApply w v p with budget := w.budget - 1 }
      else w
  | .addView c =>
      if augOkB w c && w.augLicensed && decide (0 < w.budget) then
        { augApply w c with budget := w.budget - 1 }
      else w
  | .refuse i j =>
      if obstructedB w (i, j) && !(decide ((i, j) ∈ w.refusals)) then
        { w with refusals := w.refusals ++ [(i, j)] }
      else w
  | .note n => { w with notes := w.notes ++ [n] }
  | .setBudget n => { w with budget := n }
  | .setAugLicense b => { w with augLicensed := b }

def replay (h : List Event) (w : World) : World := h.foldl step w

/-! ## Target 1 — replay determinism and composition -/

/-- Replay is a function of represented history and start state alone;
two runs with identical represented inputs agree.  (For the kernel
this is definitional — that is the design point; the countermodels
below show semantics with unrepresented inputs failing it.) -/
theorem replay_deterministic (h : List Event) {w w' : World}
    (hw : w = w') : replay h w = replay h w' := by rw [hw]

theorem replay_nil (w : World) : replay [] w = w := rfl

theorem replay_append (h1 h2 : List Event) (w : World) :
    replay (h1 ++ h2) w = replay h2 (replay h1 w) :=
  List.foldl_append

/-! ## Target 2 — the represented support of a transition -/

structure Supp where
  data : List Nat
  views : List View
  reqs : List Req
  refusals : List Req
  budget : Nat
  augLicensed : Bool
deriving Repr, DecidableEq

def supp (w : World) : Supp :=
  ⟨w.data, w.views, w.reqs, w.refusals, w.budget, w.augLicensed⟩

/-- Operational-support factorization: the step factors through the
`supp` projection — agreement on the represented support forces
agreement of successor supports, for every event. -/
theorem support_determines (w w' : World) (h : supp w = supp w')
    (e : Event) : supp (step w e) = supp (step w' e) := by
  cases w with
  | mk d v r f b a nt =>
    cases w' with
    | mk d' v' r' f' b' a' nt' =>
      simp only [supp, Supp.mk.injEq] at h
      obtain ⟨h1, h2, h3, h4, h5, h6⟩ := h
      subst h1; subst h2; subst h3; subst h4; subst h5; subst h6
      cases e with
      | admitTok t =>
          simp only [step]
          split <;> rfl
      | require i j =>
          have hc : reqOkB (World.mk d v r f b a nt) i j
              = reqOkB (World.mk d v r f b a nt') i j := rfl
          simp only [step]
          rw [hc]
          split <;> rfl
      | mark vv p =>
          have hc : (markOkB (World.mk d v r f b a nt) vv p
                && decide (0 < (World.mk d v r f b a nt).budget))
              = (markOkB (World.mk d v r f b a nt') vv p
                && decide
                  (0 < (World.mk d v r f b a nt').budget)) := rfl
          simp only [step]
          rw [hc]
          split <;> rfl
      | addView c =>
          have hc : (augOkB (World.mk d v r f b a nt) c
                && (World.mk d v r f b a nt).augLicensed
                && decide (0 < (World.mk d v r f b a nt).budget))
              = (augOkB (World.mk d v r f b a nt') c
                && (World.mk d v r f b a nt').augLicensed
                && decide
                  (0 < (World.mk d v r f b a nt').budget)) := rfl
          simp only [step]
          rw [hc]
          split <;> rfl
      | refuse i j =>
          have hc : (obstructedB (World.mk d v r f b a nt) (i, j)
                && !(decide
                  ((i, j) ∈ (World.mk d v r f b a nt).refusals)))
              = (obstructedB (World.mk d v r f b a nt') (i, j)
                && !(decide
                  ((i, j) ∈
                    (World.mk d v r f b a nt').refusals))) := rfl
          simp only [step]
          rw [hc]
          split <;> rfl
      | note n => rfl
      | setBudget n => rfl
      | setAugLicense bb => rfl

/-- Internal-support corollary (factorization form): two runs whose
successor supports differ already differ in their represented
supports.  This is operational-support factorization, not a claim of
per-datum causation. -/
theorem internal_support (w w' : World) (e : Event)
    (hres : supp (step w e) ≠ supp (step w' e)) : supp w ≠ supp w' :=
  fun h => hres (support_determines w w' h e)

/-- The transition-inert field really is inert: worlds differing only
in `notes` have support-equal successors (concrete instance). -/
theorem notes_inert :
    supp (step { genesis with notes := [7] } (.admitTok 3)) =
      supp (step genesis (.admitTok 3)) := by decide

/-! ## Target 3 — no hidden choice: complete successor families and
replay-equivalence invariance -/

theorem repairFamily_sound {w : World} {r : Req} {m : View × Nat}
    (h : m ∈ repairFamily w r) :
    m ∈ responseMenu w ∧ repairsB w m r = true :=
  List.mem_filter.mp h

theorem repairFamily_complete {w : World} {r : Req} {m : View × Nat}
    (hm : m ∈ responseMenu w) (hr : repairsB w m r = true) :
    m ∈ repairFamily w r :=
  List.mem_filter.mpr ⟨hm, hr⟩

/-- Ties are retained: the family is a filter of the declared menu; no
minimum, no representative, no selector occurs anywhere in it. -/
theorem repairFamily_retains_ties {w : World} {r : Req}
    {m m' : View × Nat}
    (hm : m ∈ responseMenu w) (hm' : m' ∈ responseMenu w)
    (h1 : repairsB w m r = true) (h2 : repairsB w m' r = true) :
    m ∈ repairFamily w r ∧ m' ∈ repairFamily w r :=
  ⟨repairFamily_complete hm h1, repairFamily_complete hm' h2⟩

/-! Replay-equivalence between results.  Data is the ordered admission
record (positions are load-bearing occurrence identities), so it is
compared literally; views, requirements, and refusals are set-like and
compared by membership. -/

def SameElems {α : Type} (l l' : List α) : Prop :=
  ∀ x, x ∈ l ↔ x ∈ l'

def WEquiv (w w' : World) : Prop :=
  w.data = w'.data ∧ SameElems w.views w'.views ∧
    SameElems w.reqs w'.reqs ∧ SameElems w.refusals w'.refusals ∧
    w.budget = w'.budget ∧ w.augLicensed = w'.augLicensed

theorem sameElems_refl {α : Type} (l : List α) : SameElems l l :=
  fun _ => Iff.rfl

theorem sameElems_append {α : Type} {l l' : List α}
    (h : SameElems l l') (x : α) :
    SameElems (l ++ [x]) (l' ++ [x]) := by
  intro y
  simp only [List.mem_append]
  constructor
  · rintro (hy | hy)
    · exact Or.inl ((h y).mp hy)
    · exact Or.inr hy
  · rintro (hy | hy)
    · exact Or.inl ((h y).mpr hy)
    · exact Or.inr hy

theorem sameElems_map {α β : Type} {l l' : List α}
    (h : SameElems l l') (f : α → β) :
    SameElems (l.map f) (l'.map f) := by
  intro y
  simp only [List.mem_map]
  constructor
  · rintro ⟨x, hx, rfl⟩
    exact ⟨x, (h x).mp hx, rfl⟩
  · rintro ⟨x, hx, rfl⟩
    exact ⟨x, (h x).mpr hx, rfl⟩

theorem any_congr {α : Type} {l l' : List α}
    (h : SameElems l l') (f : α → Bool) : l.any f = l'.any f := by
  apply bool_eq_of_iff
  simp only [List.any_eq_true]
  constructor
  · rintro ⟨x, hx, hf⟩
    exact ⟨x, (h x).mp hx, hf⟩
  · rintro ⟨x, hx, hf⟩
    exact ⟨x, (h x).mpr hx, hf⟩

theorem all_congr {α : Type} {l l' : List α}
    (h : SameElems l l') (f : α → Bool) : l.all f = l'.all f := by
  apply bool_eq_of_iff
  simp only [List.all_eq_true]
  constructor
  · intro ha x hx
    exact ha x ((h x).mpr hx)
  · intro ha x hx
    exact ha x ((h x).mp hx)

theorem satB_congr {w w' : World} (h : WEquiv w w') (r : Req) :
    satB w r = satB w' r :=
  any_congr h.2.1 _

theorem violB_congr {w w' : World} (h : WEquiv w w') (r : Req) :
    violB w r = violB w' r := by
  unfold violB
  have hdec : (decide (r ∈ w.reqs)) = (decide (r ∈ w'.reqs)) := by
    apply bool_eq_of_iff
    simp only [decide_eq_true_eq]
    exact h.2.2.1 r
  rw [satB_congr h, hdec]

theorem sameElems_flatMap_menu {w w' : World} (h : WEquiv w w') :
    SameElems (responseMenu w) (responseMenu w') := by
  intro m
  unfold responseMenu
  simp only [List.mem_flatMap, List.mem_map, List.mem_range]
  rw [show w'.data.length = w.data.length from by rw [h.1]]
  constructor
  · rintro ⟨v, hv, p, hp, rfl⟩
    exact ⟨v, (h.2.1 v).mp hv, p, hp, rfl⟩
  · rintro ⟨v, hv, p, hp, rfl⟩
    exact ⟨v, (h.2.1 v).mpr hv, p, hp, rfl⟩

theorem markApply_equiv {w w' : World} (h : WEquiv w w')
    (v : View) (p : Nat) :
    WEquiv (markApply w v p) (markApply w' v p) := by
  refine ⟨h.1, sameElems_map h.2.1 _, h.2.2.1, h.2.2.2.1,
    h.2.2.2.2.1, h.2.2.2.2.2⟩

theorem preservesB_congr {w w' : World} (h : WEquiv w w')
    {u u' : World} (hu : WEquiv u u') :
    preservesB w u = preservesB w' u' := by
  unfold preservesB
  have hall : ∀ r : Req,
      (!satB w r || satB u r) = (!satB w' r || satB u' r) := by
    intro r
    rw [satB_congr h, satB_congr hu]
  calc w.reqs.all (fun r => !satB w r || satB u r)
      = w.reqs.all (fun r => !satB w' r || satB u' r) := by
        apply bool_eq_of_iff
        simp only [List.all_eq_true]
        constructor
        · intro ha x hx; rw [← hall x]; exact ha x hx
        · intro ha x hx; rw [hall x]; exact ha x hx
    _ = w'.reqs.all (fun r => !satB w' r || satB u' r) :=
        all_congr h.2.2.1 _

theorem dischargesSomeB_congr {w w' : World} (h : WEquiv w w')
    {u u' : World} (hu : WEquiv u u') :
    dischargesSomeB w u = dischargesSomeB w' u' := by
  unfold dischargesSomeB
  have hone : ∀ r : Req,
      (violB w r && satB u r) = (violB w' r && satB u' r) := by
    intro r
    rw [violB_congr h, satB_congr hu]
  calc w.reqs.any (fun r => violB w r && satB u r)
      = w.reqs.any (fun r => violB w' r && satB u' r) := by
        apply bool_eq_of_iff
        simp only [List.any_eq_true]
        constructor
        · rintro ⟨x, hx, hf⟩; exact ⟨x, hx, by rw [← hone x]; exact hf⟩
        · rintro ⟨x, hx, hf⟩; exact ⟨x, hx, by rw [hone x]; exact hf⟩
    _ = w'.reqs.any (fun r => violB w' r && satB u' r) :=
        any_congr h.2.2.1 _

theorem markOkB_congr {w w' : World} (h : WEquiv w w')
    (v : View) (p : Nat) : markOkB w v p = markOkB w' v p := by
  unfold markOkB
  have hdec : (decide (v ∈ w.views)) = (decide (v ∈ w'.views)) := by
    apply bool_eq_of_iff
    simp only [decide_eq_true_eq]
    exact h.2.1 v
  rw [hdec,
      show w.data.length = w'.data.length from by rw [h.1],
      dischargesSomeB_congr h (markApply_equiv h v p),
      preservesB_congr h (markApply_equiv h v p)]

theorem increaseB_congr {w w' : World} (h : WEquiv w w') (c : View) :
    increaseB w c = increaseB w' c := by
  unfold increaseB
  rw [show w.data.length = w'.data.length from by rw [h.1]]
  apply bool_eq_of_iff
  simp only [List.any_eq_true]
  constructor
  · rintro ⟨i, hi, j, hj, hf⟩
    refine ⟨i, hi, j, hj, ?_⟩
    rw [← satB_congr h (i, j)]
    exact hf
  · rintro ⟨i, hi, j, hj, hf⟩
    refine ⟨i, hi, j, hj, ?_⟩
    rw [satB_congr h (i, j)]
    exact hf

theorem augOkB_congr {w w' : World} (h : WEquiv w w') (c : View) :
    augOkB w c = augOkB w' c := by
  unfold augOkB
  have hdec : (decide (c ∈ w.views)) = (decide (c ∈ w'.views)) := by
    apply bool_eq_of_iff
    simp only [decide_eq_true_eq]
    exact h.2.1 c
  rw [show w.data.length = w'.data.length from by rw [h.1],
      hdec, increaseB_congr h c]

theorem repairsB_congr {w w' : World} (h : WEquiv w w')
    (m : View × Nat) (r : Req) : repairsB w m r = repairsB w' m r := by
  unfold repairsB
  rw [markOkB_congr h, satB_congr (markApply_equiv h m.1 m.2)]

theorem obstructedB_congr {w w' : World} (h : WEquiv w w') (r : Req) :
    obstructedB w r = obstructedB w' r := by
  unfold obstructedB
  rw [violB_congr h]
  have hmenu := sameElems_flatMap_menu h
  have : (responseMenu w).all (fun m => !repairsB w m r) =
      (responseMenu w').all (fun m => !repairsB w' m r) := by
    calc (responseMenu w).all (fun m => !repairsB w m r)
        = (responseMenu w).all (fun m => !repairsB w' m r) := by
          apply bool_eq_of_iff
          simp only [List.all_eq_true]
          constructor
          · intro ha x hx; rw [← repairsB_congr h x r]; exact ha x hx
          · intro ha x hx; rw [repairsB_congr h x r]; exact ha x hx
      _ = (responseMenu w').all (fun m => !repairsB w' m r) :=
          all_congr hmenu _
  rw [this]

theorem reqOkB_congr {w w' : World} (h : WEquiv w w') (i j : Nat) :
    reqOkB w i j = reqOkB w' i j := by
  unfold reqOkB
  have hdec : (decide ((i, j) ∈ w.reqs))
      = (decide ((i, j) ∈ w'.reqs)) := by
    apply bool_eq_of_iff
    simp only [decide_eq_true_eq]
    exact h.2.2.1 (i, j)
  rw [show w.data.length = w'.data.length from by rw [h.1], hdec]

/-- No hidden choice, invariance half: replay-equivalent worlds step to
replay-equivalent worlds.  (The countermodel `stepHead` below breaks
exactly this by consulting list order — an unrecorded tie-break.) -/
theorem equiv_step {w w' : World} (h : WEquiv w w') (e : Event) :
    WEquiv (step w e) (step w' e) := by
  obtain ⟨hd, hv, hr, hf, hb, ha⟩ := h
  cases e with
  | admitTok t =>
      simp only [step]
      by_cases hmem : t ∈ w.data
      · rw [if_pos hmem, if_pos (show t ∈ w'.data from hd ▸ hmem)]
        exact ⟨hd, hv, hr, hf, hb, ha⟩
      · rw [if_neg hmem,
            if_neg (show ¬ t ∈ w'.data from fun hx =>
              hmem (hd ▸ hx))]
        exact ⟨by rw [hd], hv, hr, hf, hb, ha⟩
  | require i j =>
      simp only [step]
      rw [reqOkB_congr ⟨hd, hv, hr, hf, hb, ha⟩ i j]
      split
      · exact ⟨hd, hv, sameElems_append hr _, hf, hb, ha⟩
      · exact ⟨hd, hv, hr, hf, hb, ha⟩
  | mark v p =>
      simp only [step]
      rw [markOkB_congr ⟨hd, hv, hr, hf, hb, ha⟩ v p, hb]
      split
      · exact ⟨hd, sameElems_map hv _, hr, hf, rfl, ha⟩
      · exact ⟨hd, hv, hr, hf, hb, ha⟩
  | addView c =>
      simp only [step]
      rw [augOkB_congr ⟨hd, hv, hr, hf, hb, ha⟩ c, hb, ha]
      split
      · exact ⟨hd, sameElems_append hv _, hr, hf, rfl, ha⟩
      · exact ⟨hd, hv, hr, hf, hb, ha⟩
  | refuse i j =>
      simp only [step]
      have hdec : (decide ((i, j) ∈ w.refusals))
          = (decide ((i, j) ∈ w'.refusals)) := by
        apply bool_eq_of_iff
        simp only [decide_eq_true_eq]
        exact hf (i, j)
      rw [obstructedB_congr ⟨hd, hv, hr, hf, hb, ha⟩ (i, j), hdec]
      split
      · exact ⟨hd, hv, hr, sameElems_append hf _, hb, ha⟩
      · exact ⟨hd, hv, hr, hf, hb, ha⟩
  | note n => exact ⟨hd, hv, hr, hf, hb, ha⟩
  | setBudget n => exact ⟨hd, hv, hr, hf, rfl, ha⟩
  | setAugLicense b => exact ⟨hd, hv, hr, hf, hb, rfl⟩

theorem equiv_replay {w w' : World} (h : WEquiv w w')
    (hist : List Event) : WEquiv (replay hist w) (replay hist w') := by
  induction hist generalizing w w' with
  | nil => exact h
  | cons e rest ih => exact ih (equiv_step h e)

/-- Equivalent representations receive the same complete successor
family (membership-identical menus of accepted responses). -/
theorem equiv_repairFamily {w w' : World} (h : WEquiv w w') (r : Req) :
    SameElems (repairFamily w r) (repairFamily w' r) := by
  intro m
  unfold repairFamily
  simp only [List.mem_filter]
  constructor
  · rintro ⟨hm, hp⟩
    exact ⟨(sameElems_flatMap_menu h m).mp hm,
      by rw [← repairsB_congr h m r]; exact hp⟩
  · rintro ⟨hm, hp⟩
    exact ⟨(sameElems_flatMap_menu h m).mpr hm,
      by rw [repairsB_congr h m r]; exact hp⟩

/-! ## Target 4 — repair soundness -/

theorem mark_discharges {w : World} {v : View} {p : Nat}
    (h : markOkB w v p = true) :
    ∃ r ∈ w.reqs, violB w r = true ∧
      satB (markApply w v p) r = true := by
  unfold markOkB at h
  simp only [Bool.and_eq_true] at h
  have hd := h.1.2
  unfold dischargesSomeB at hd
  simp only [List.any_eq_true, Bool.and_eq_true] at hd
  obtain ⟨r, hr, hviol, hsat⟩ := hd
  exact ⟨r, hr, hviol, hsat⟩

theorem mark_preserves {w : World} {v : View} {p : Nat}
    (h : markOkB w v p = true) :
    ∀ r ∈ w.reqs, satB w r = true →
      satB (markApply w v p) r = true := by
  unfold markOkB at h
  simp only [Bool.and_eq_true] at h
  have hp := h.2
  unfold preservesB at hp
  simp only [List.all_eq_true] at hp
  intro r hr hs
  exact (or_not_eq_true.mp (hp r hr)) hs

/-- An accepted repair discharges a recorded violation and preserves
every previously satisfied recorded requirement — at the step level. -/
theorem step_mark_sound {w : World} {v : View} {p : Nat}
    (hok : markOkB w v p = true) (hbud : 0 < w.budget) :
    (∃ r ∈ w.reqs, violB w r = true ∧
        satB (step w (.mark v p)) r = true) ∧
      (∀ r ∈ w.reqs, satB w r = true →
        satB (step w (.mark v p)) r = true) := by
  have hcond : (markOkB w v p && decide (0 < w.budget)) = true := by
    rw [hok, decide_eq_true hbud]
    rfl
  have hstep : step w (.mark v p) =
      { markApply w v p with budget := w.budget - 1 } := by
    simp only [step]
    rw [if_pos hcond]
  have hsat : ∀ r, satB (step w (.mark v p)) r =
      satB (markApply w v p) r := by
    intro r
    rw [hstep]
    rfl
  constructor
  · obtain ⟨r, hr, h1, h2⟩ := mark_discharges hok
    exact ⟨r, hr, h1, by rw [hsat]; exact h2⟩
  · intro r hr hs
    rw [hsat]
    exact mark_preserves hok r hr hs

/-! ## Target 5 — augmentation soundness -/

/-- Exact positive-satisfaction delta equation: after augmentation,
satisfaction is the old verdict or the new column's.  Satisfied
positive requirements are therefore preserved; old *non-separation*
judgments are not preserved — changing them is exactly the licensed
content of an expressive increase. -/
theorem satB_aug (w : World) (c : View) (r : Req) :
    satB (augApply w c) r = (satB w r || sepB c r.1 r.2) := by
  unfold satB augApply
  simp only [List.any_append, List.any_cons, List.any_nil,
    Bool.or_false]

theorem aug_preserves_satisfied {w : World} {c : View} {r : Req}
    (h : satB w r = true) : satB (augApply w c) r = true := by
  rw [satB_aug, h]
  rfl

/-- An accepted augmentation genuinely adds expressive capacity: some
bounded pair is separated by the new column and by no old view. -/
theorem aug_increases {w : World} {c : View}
    (h : augOkB w c = true) :
    ∃ i j, i ≠ j ∧ i < w.data.length ∧ j < w.data.length ∧
      sepB c i j = true ∧ satB w (i, j) = false := by
  unfold augOkB at h
  simp only [Bool.and_eq_true] at h
  have hi := h.2
  unfold increaseB at hi
  simp only [List.any_eq_true, List.mem_range, Bool.and_eq_true] at hi
  obtain ⟨i, hi', j, hj', hprod⟩ := hi
  obtain ⟨⟨hne, hsep⟩, hnot⟩ := hprod
  rw [bne_iff_ne] at hne
  refine ⟨i, j, hne, hi', hj', hsep, ?_⟩
  cases hs : satB w (i, j) with
  | false => rfl
  | true =>
      rw [hs] at hnot
      exact absurd hnot (by decide)

/-! ## Target 6 — represented progress -/

/-- Recorded requirements are well-formed: off-diagonal and in-bounds.
An invariant of the kernel, established at `genesis` and preserved by
every step. -/
def WF (w : World) : Prop :=
  ∀ r ∈ w.reqs, r.1 ≠ r.2 ∧ r.1 < w.data.length ∧
    r.2 < w.data.length

theorem wf_genesis : WF genesis := by
  intro r hr
  cases hr

theorem wf_step {w : World} (hwf : WF w) (e : Event) :
    WF (step w e) := by
  cases e with
  | admitTok t =>
      intro r hr
      simp only [step] at hr ⊢
      by_cases hmem : t ∈ w.data
      · rw [if_pos hmem] at hr ⊢
        exact hwf r hr
      · rw [if_neg hmem] at hr ⊢
        obtain ⟨h1, h2, h3⟩ := hwf r hr
        refine ⟨h1, ?_, ?_⟩ <;>
          · simp only [List.length_append, List.length_cons,
              List.length_nil]
            omega
  | require i j =>
      intro r hr
      simp only [step] at hr ⊢
      by_cases hok : reqOkB w i j = true
      · rw [if_pos hok] at hr ⊢
        rcases List.mem_append.mp hr with hold | hnew
        · exact hwf r hold
        · have hrij : r = (i, j) := by
            cases hnew with
            | head => rfl
            | tail _ h => cases h
          subst hrij
          unfold reqOkB at hok
          simp only [Bool.and_eq_true] at hok
          refine ⟨?_, of_decide_eq_true hok.1.1.2,
            of_decide_eq_true hok.1.2⟩
          have := hok.1.1.1
          rwa [bne_iff_ne] at this
      · rw [if_neg hok] at hr ⊢
        exact hwf r hr
  | mark v p =>
      intro r hr
      simp only [step] at hr ⊢
      by_cases hc : (markOkB w v p && decide (0 < w.budget)) = true
      · rw [if_pos hc] at hr ⊢
        exact hwf r hr
      · rw [if_neg hc] at hr ⊢
        exact hwf r hr
  | addView c =>
      intro r hr
      simp only [step] at hr ⊢
      by_cases hc : (augOkB w c && w.augLicensed
          && decide (0 < w.budget)) = true
      · rw [if_pos hc] at hr ⊢
        exact hwf r hr
      · rw [if_neg hc] at hr ⊢
        exact hwf r hr
  | refuse i j =>
      intro r hr
      simp only [step] at hr ⊢
      by_cases hc : (obstructedB w (i, j)
          && !(decide ((i, j) ∈ w.refusals))) = true
      · rw [if_pos hc] at hr ⊢
        exact hwf r hr
      · rw [if_neg hc] at hr ⊢
        exact hwf r hr
  | note n => exact hwf
  | setBudget n => exact hwf
  | setAugLicense b => exact hwf

theorem wf_replay (h : List Event) : WF (replay h genesis) := by
  have : ∀ w, WF w → WF (replay h w) := by
    induction h with
    | nil => intro w hw; exact hw
    | cons e rest ih =>
        intro w hw
        exact ih _ (wf_step hw e)
  exact this genesis wf_genesis

/-- The represented-progress theorem.  Hypotheses, all explicit and
all represented: well-formedness (an invariant of replay), and the
violation itself.  Conclusion: the internally determined repair family
is non-empty, or the violation is a certified obstruction *and* the
canonical singleton augmentation is accepted and discharges it.  The
budget and license needed to *apply* either response are state fields
(`progress_needs_budget`, `progress_needs_license`). -/
theorem represented_progress {w : World} {i j : Nat} (hwf : WF w)
    (hviol : violB w (i, j) = true) :
    (∃ m, m ∈ repairFamily w (i, j)) ∨
      (obstructedB w (i, j) = true ∧ augOkB w [i] = true ∧
        satB (augApply w [i]) (i, j) = true) := by
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
  have hsep : sepB [i] i j = true := by
    unfold sepB
    have h1 : (i ∈ [i]) := List.mem_cons_self
    have h2 : ¬ (j ∈ [i]) := by
      intro hj
      cases hj with
      | head => exact hne rfl
      | tail _ h => cases h
    rw [decide_eq_true h1, decide_eq_false h2]
    rfl
  cases hfam : repairFamily w (i, j) with
  | cons m t => exact Or.inl ⟨m, List.mem_cons_self⟩
  | nil =>
      right
      have hallfail : ∀ m ∈ responseMenu w,
          repairsB w m (i, j) = false := by
        intro m hm
        cases hb : repairsB w m (i, j) with
        | false => rfl
        | true =>
            have : m ∈ repairFamily w (i, j) :=
              repairFamily_complete hm hb
            rw [hfam] at this
            cases this
      have hobs : obstructedB w (i, j) = true := by
        unfold obstructedB
        rw [hviol]
        have : (responseMenu w).all
            (fun m => !repairsB w m (i, j)) = true := by
          simp only [List.all_eq_true]
          intro m hm
          rw [hallfail m hm]
          rfl
        rw [this]
        rfl
      have hfresh : ¬ ([i] ∈ w.views) := by
        intro hin
        have : satB w (i, j) = true := by
          unfold satB
          simp only [List.any_eq_true]
          exact ⟨[i], hin, hsep⟩
        rw [this] at hnots
        cases hnots
      have haug : augOkB w [i] = true := by
        unfold augOkB
        have hb1 : ([i].all fun p => decide (p < w.data.length))
            = true := by
          simp only [List.all_cons, List.all_nil, Bool.and_true]
          exact decide_eq_true hib
        have hb2 : (!(decide ([i] ∈ w.views))) = true := by
          rw [decide_eq_false hfresh]
          rfl
        have hb3 : increaseB w [i] = true := by
          unfold increaseB
          simp only [List.any_eq_true, List.mem_range]
          refine ⟨i, hib, j, hjb, ?_⟩
          rw [hsep, hnots]
          have : (i != j) = true := by rwa [bne_iff_ne]
          rw [this]
          rfl
        rw [hb1, hb2, hb3]
        rfl
      refine ⟨hobs, haug, ?_⟩
      rw [satB_aug, hsep]
      simp


/-- The isolated hypotheses: the represented budget and the represented
license are load-bearing.  With either absent, the accepting steps are
no-ops, and the same-level exhaustion is recordable as a represented,
certificate-bearing refusal.  Refusal is non-absorbing — it records
exhaustion and terminates nothing; ending a bounded run belongs to the
history producer, which is fixed metatheory (see the module header). -/
theorem progress_needs_budget (w : World) (v : View) (p : Nat)
    (h : w.budget = 0) : step w (.mark v p) = w := by
  simp only [step]
  rw [if_neg]
  intro hc
  have : decide (0 < w.budget) = true := by
    have := hc
    simp only [Bool.and_eq_true] at this
    exact this.2
  rw [h] at this
  exact absurd (of_decide_eq_true this) (by omega)

theorem progress_needs_license (w : World) (c : View)
    (h : w.augLicensed = false) : step w (.addView c) = w := by
  simp only [step]
  rw [if_neg]
  intro hc
  simp only [Bool.and_eq_true] at hc
  rw [h] at hc
  exact absurd hc.1.2 (by decide)

/-! ## Target 7 — closure -/

/-- New violations arise only from represented `require` events: every
other step can only shrink the violation set (marks by the
preservation guard, augmentations by monotonicity, the rest by leaving
requirements and views unchanged). -/
theorem violation_only_from_require {w : World} {e : Event} {r : Req}
    (h : violB (step w e) r = true) :
    violB w r = true ∨ ∃ i j, e = .require i j := by
  cases e with
  | admitTok t =>
      left
      simp only [step] at h
      split at h
      · exact h
      · unfold violB satB at h ⊢
        exact h
  | require i j => exact Or.inr ⟨i, j, rfl⟩
  | mark v p =>
      left
      simp only [step] at h
      split at h
      · rename_i hc
        simp only [Bool.and_eq_true] at hc
        have hok := hc.1
        unfold violB at h ⊢
        simp only [Bool.and_eq_true] at h
        have hmem : r ∈ w.reqs := of_decide_eq_true h.1
        rw [decide_eq_true hmem]
        cases hs : satB w r with
        | false => rfl
        | true =>
            exfalso
            have hpres := mark_preserves hok r hmem hs
            have : satB { markApply w v p with
                budget := w.budget - 1 } r =
                satB (markApply w v p) r := rfl
            rw [this, hpres] at h
            exact absurd h.2 (by decide)
      · exact h
  | addView c =>
      left
      simp only [step] at h
      split at h
      · unfold violB at h ⊢
        simp only [Bool.and_eq_true] at h
        have hmem : r ∈ w.reqs := of_decide_eq_true h.1
        rw [decide_eq_true hmem]
        cases hs : satB w r with
        | false => rfl
        | true =>
            exfalso
            have : satB { augApply w c with
                budget := w.budget - 1 } r =
                satB (augApply w c) r := rfl
            rw [this, aug_preserves_satisfied hs] at h
            exact absurd h.2 (by decide)
      · exact h
  | refuse i j =>
      left
      simp only [step] at h
      split at h <;> (unfold violB satB at h ⊢; exact h)
  | note n =>
      left
      unfold violB satB at h ⊢
      exact h
  | setBudget n =>
      left
      unfold violB satB at h ⊢
      exact h
  | setAugLicense b =>
      left
      unfold violB satB at h ⊢
      exact h

/-- Quiescence: with every recorded requirement satisfied, no event
except a represented `require` can create a violation. -/
theorem quiescent_stable {w : World} (hq : quiescentB w = true)
    {e : Event} (hnotreq : ∀ i j, e ≠ .require i j) :
    quiescentB (step w e) = true := by
  unfold quiescentB at hq ⊢
  simp only [List.all_eq_true] at hq ⊢
  intro r hr
  cases hs : satB (step w e) r with
  | true => rfl
  | false =>
      exfalso
      have hmem : r ∈ w.reqs := by
        cases e with
        | require i j => exact absurd rfl (hnotreq i j)
        | admitTok t =>
            simp only [step] at hr
            split at hr <;> exact hr
        | mark v p =>
            simp only [step] at hr
            split at hr <;> exact hr
        | addView c =>
            simp only [step] at hr
            split at hr <;> exact hr
        | refuse i j =>
            simp only [step] at hr
            split at hr <;> exact hr
        | note n => exact hr
        | setBudget n => exact hr
        | setAugLicense b => exact hr
      have hviol : violB (step w e) r = true := by
        unfold violB
        rw [decide_eq_true hr, hs]
        rfl
      rcases violation_only_from_require hviol with hold | ⟨i, j, he⟩
      · unfold violB at hold
        simp only [Bool.and_eq_true] at hold
        have := hq r hmem
        rw [this] at hold
        exact absurd hold.2 (by decide)
      · exact hnotreq i j he

/-! ## Target 8 — productivity: one prefix-compatible unbounded run
under an *explicitly supplied* event stream

`histUpTo` is a metatheoretic history producer — supplied, not
endogenous.  What the kernel contributes is that every state on the
stream is reached through the acceptance-guarded `step` alone. -/

def blockEvents (k : Nat) : List Event :=
  [.setBudget 1, .admitTok k, .require 0 k, .addView [k]]

def histUpTo : Nat → List Event
  | 0 => [.admitTok 0]
  | k + 1 => histUpTo k ++ blockEvents (k + 1)

def worldAt (k : Nat) : World := replay (histUpTo k) genesis

theorem admit_data_fresh (u : World) (t : Nat) (h : ¬ t ∈ u.data) :
    (step u (.admitTok t)).data = u.data ++ [t] := by
  simp only [step]
  rw [if_neg h]

/-- Prefix compatibility: each history extends the previous one — a
single unbounded run, not unrelated finite witnesses. -/
theorem histUpTo_prefix (k : Nat) :
    histUpTo k <+: histUpTo (k + 1) :=
  ⟨blockEvents (k + 1), rfl⟩

/-- The carrier of the unbounded run is the initial segment of the
numerals, derived through the acceptance-guarded kernel itself. -/
theorem worldAt_data (k : Nat) :
    (worldAt k).data = List.range (k + 1) := by
  induction k with
  | zero => decide
  | succ m ih =>
      show (replay (histUpTo m ++ blockEvents (m + 1)) genesis).data
        = List.range (m + 2)
      rw [replay_append]
      show (replay (blockEvents (m + 1)) (worldAt m)).data = _
      unfold blockEvents replay
      simp only [List.foldl]
      have hb : (step (worldAt m) (.setBudget 1)).data =
          (worldAt m).data := rfl
      have hnm : ¬ (m + 1 ∈ (step (worldAt m) (.setBudget 1)).data) := by
        rw [hb, ih]
        intro hmem
        have := List.mem_range.mp hmem
        omega
      have hrange : List.range (m + 1) ++ [m + 1] =
          List.range (m + 2) := (List.range_succ).symm
      have hreq : ∀ u : World, (step u (.require 0 (m + 1))).data =
          u.data := by
        intro u
        simp only [step]
        split <;> rfl
      have haug : ∀ u : World, (step u (.addView [m + 1])).data =
          u.data := by
        intro u
        simp only [step]
        split <;> rfl
      rw [haug, hreq, admit_data_fresh _ _ hnm, hb, ih, hrange]

theorem worldAt_growth (k : Nat) :
    (worldAt k).data.length = k + 1 := by
  rw [worldAt_data]
  exact List.length_range

/-- Productivity, assembled: histories of strictly increasing length,
each a prefix of the next, with strictly growing replayed carriers. -/
theorem productive_run (k : Nat) :
    histUpTo k <+: histUpTo (k + 1) ∧
      (worldAt k).data.length < (worldAt (k + 1)).data.length := by
  refine ⟨histUpTo_prefix k, ?_⟩
  rw [worldAt_growth, worldAt_growth]
  omega

/-- The full pipeline runs through the kernel: at the concrete third
stage the recorded requirement is discharged and the world is
quiescent — every acceptance made by the represented checks alone. -/
theorem worldAt_three_quiescent : quiescentB (worldAt 3) = true := by
  decide

/-! ## Countermodel 8 — finite witnesses at every length with no
compatible infinite history (a represented König failure) -/

def witValid (l : List Nat) : Bool :=
  l.all (fun x => decide (l.length ≤ x))

theorem wit_all_lengths (n : Nat) :
    witValid (List.replicate n n) = true := by
  unfold witValid
  simp only [List.all_eq_true, List.length_replicate]
  intro x hx
  have hxn := List.eq_of_mem_replicate hx
  rw [hxn]
  exact decide_eq_true (Nat.le_refl n)

def prefixList (g : Nat → Nat) (n : Nat) : List Nat :=
  (List.range n).map g

/-- No single infinite source is compatible: some prefix is invalid —
the witnesses of every length do not assemble into one history. -/
theorem wit_no_infinite (g : Nat → Nat) :
    witValid (prefixList g (g 0 + 1)) = false := by
  unfold witValid
  cases hall : (prefixList g (g 0 + 1)).all
      (fun x => decide ((prefixList g (g 0 + 1)).length ≤ x)) with
  | false => rfl
  | true =>
      exfalso
      simp only [List.all_eq_true] at hall
      have hmem : g 0 ∈ prefixList g (g 0 + 1) := by
        unfold prefixList
        exact List.mem_map.mpr ⟨0, List.mem_range.mpr (by omega), rfl⟩
      have hlen : (prefixList g (g 0 + 1)).length = g 0 + 1 := by
        unfold prefixList
        rw [List.length_map, List.length_range]
      have := of_decide_eq_true (hall _ hmem)
      rw [hlen] at this
      omega

/-! ## The internal candidate for truth: certification by represented
evaluators -/

/-- An evaluator is represented data: the view columns it can use. -/
abbrev Evaluator := List View

def verdictB (E : Evaluator) (i j : Nat) : Bool :=
  E.any (fun c => sepB c i j)

/-- The panel closes positively: every represented evaluator, run by
the represented procedure, returns `separated`. -/
def certPosB (panel : List Evaluator) (i j : Nat) : Bool :=
  !panel.isEmpty && panel.all (fun E => verdictB E i j)

def certNegB (panel : List Evaluator) (i j : Nat) : Bool :=
  !panel.isEmpty && panel.all (fun E => !verdictB E i j)

/-- Exactly what certification gives: closure of the panel on
`separated` is precisely joint separation by every evaluator's own
columns — no more. -/
theorem cert_scope (panel : List Evaluator) (i j : Nat) :
    certPosB panel i j = true ↔
      panel ≠ [] ∧ ∀ E ∈ panel, ∃ c ∈ E, sepB c i j = true := by
  unfold certPosB
  simp only [Bool.and_eq_true, List.all_eq_true]
  constructor
  · rintro ⟨hne, hall⟩
    refine ⟨?_, ?_⟩
    · intro hnil
      rw [hnil] at hne
      exact absurd hne (by decide)
    · intro E hE
      have := hall E hE
      unfold verdictB at this
      simp only [List.any_eq_true] at this
      exact this
  · rintro ⟨hne, hall⟩
    refine ⟨?_, ?_⟩
    · cases panel with
      | nil => exact absurd rfl hne
      | cons E rest => rfl
    · intro E hE
      unfold verdictB
      simp only [List.any_eq_true]
      exact hall E hE

/-- Certification is panel-relative, never correspondence: a unanimous
panel certifies "equivalent" while a column outside the panel
separates.  Agreement among represented evaluators reaches exactly the
panel's joint quotient and nothing beyond it. -/
theorem cert_not_correspondence :
    certNegB [[[0, 1]], [[0, 1]]] 0 1 = true ∧
      sepB [0] 0 1 = true := by decide

/-- Panel-extension can break closure: certification is a fact about a
represented panel, not a monotone approach to an outside. -/
theorem cert_panel_relative :
    certPosB [[[0]]] 0 1 = true ∧
      certPosB [[[0]], [[0, 1]]] 0 1 = false := by decide

/-! ## Countermodels 1–3: unrepresented scheduler, fresh-name source,
and hidden evaluator

Each is a *semantics* that consumes one input found in neither the
represented state nor the represented history.  In each, two runs with
identical represented state and history produce different results —
exactly what the kernel's type makes impossible. -/

def stepSched (ext : Bool) (w : World) (e : Event) : World :=
  match e with
  | .mark v p => if ext then step w (.mark v p) else w
  | _ => step w e

def schedWorld : World :=
  replay [.setBudget 9, .admitTok 10, .admitTok 20, .require 0 1,
    .addView [0]] genesis

/-- Wait — the view `[0]` already separates the recorded pair, so use a
world with a live repair instead: two data, requirement, an empty-ish
view landscape where a mark is the accepted response. -/
def schedWorld2 : World :=
  { data := [10, 20], views := [[]], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

theorem scheduler_hidden :
    stepSched true schedWorld2 (.mark [] 0) ≠
      stepSched false schedWorld2 (.mark [] 0) := by decide

def stepGensym (seed : Nat) (w : World) (e : Event) : World :=
  match e with
  | .admitTok _ => step w (.admitTok seed)
  | _ => step w e

theorem gensym_hidden :
    (stepGensym 0 (worldAt 1) (.admitTok 99)).data ≠
      (stepGensym 99 (worldAt 1) (.admitTok 99)).data := by decide

def stepOracle (oracle : Bool) (w : World) (e : Event) : World :=
  match e with
  | .mark v p =>
      if (markOkB w v p || oracle) && decide (0 < w.budget) then
        { markApply w v p with budget := w.budget - 1 }
      else w
  | _ => step w e

/-- A world whose recorded requirement is already satisfied: the
kernel rejects a mark that discharges nothing; only the hidden oracle
can push it through. -/
def oracleWorld : World :=
  { data := [10, 20], views := [[0]], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

theorem oracle_hidden :
    stepOracle true oracleWorld (.mark [0] 1) ≠
      stepOracle false oracleWorld (.mark [0] 1) := by decide

/-! ## Countermodel 4 — incomplete search falsely declares an
obstruction -/

def obstructedTruncB (k : Nat) (w : World) (r : Req) : Bool :=
  violB w r && ((responseMenu w).take k).all (fun m => !repairsB w m r)

def truncWorld : World :=
  { data := [10, 20, 30], views := [[0]], reqs := [(1, 2)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

/-- The truncated check declares an obstruction that the exhaustive
check refutes: a working repair sits past the truncation point.
Obstruction requires *exhaustive* failure — by definition. -/
theorem incomplete_search_false_alarm :
    obstructedTruncB 1 truncWorld (1, 2) = true ∧
      obstructedB truncWorld (1, 2) = false ∧
      repairFamily truncWorld (1, 2) ≠ [] := by decide

/-! ## Countermodel 5 — a destructive rewrite is not an augmentation -/

def overwriteFirst (w : World) (c : View) : World :=
  { w with views := c :: w.views.drop 1 }

def owWorld : World :=
  { data := [10, 20], views := [[0]], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

/-- Overwriting destroys a previously satisfied requirement; the
kernel's augmentation is append-only and provably conservative
(`satB_aug`), so this transition is not expressible as an accepted
`addView`. -/
theorem augmentation_destroys_old_replay :
    satB owWorld (0, 1) = true ∧
      satB (overwriteFirst owWorld []) (0, 1) = false := by decide

/-! ## Countermodel 6 — repetition mislabeled as progress -/

/-- Three admissions of one token replay to the state of one; history
length grows while the represented state — and with it every recorded
requirement verdict — is unchanged.  Event count is not a progress
measure; the represented violation set is. -/
theorem repetition_not_progress :
    replay [.admitTok 5, .admitTok 5, .admitTok 5] genesis =
        replay [.admitTok 5] genesis ∧
      ([Event.admitTok 5, .admitTok 5, .admitTok 5].length ≠
        [Event.admitTok 5].length) := by decide

/-! ## Countermodel 7 — an order-sensitive semantics splits equivalent
representations -/

def stepHead (w : World) (e : Event) : World :=
  match e with
  | .mark _ p =>
      { w with views :=
          match w.views with
          | [] => []
          | c :: rest => (p :: c) :: rest }
  | _ => step w e

def headWorldA : World :=
  { data := [10, 20], views := [[], [0]], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

def headWorldB : World :=
  { data := [10, 20], views := [[0], []], reqs := [(0, 1)],
    refusals := [], budget := 9, augLicensed := true, notes := [] }

/-- The two worlds are replay-equivalent (same views as sets), yet the
head-picking semantics gives them observationally different
successors: the tie-break "first in the list" is an unrecorded
selector.  The kernel identifies repairs by value (`markApply` matches
the column itself), and `equiv_step` is exactly the theorem this
variant fails. -/
theorem order_sensitivity_splits_equivalents :
    WEquiv headWorldA headWorldB ∧
      satB (stepHead headWorldA (.mark [] 1)) (0, 1) ≠
        satB (stepHead headWorldB (.mark [] 1)) (0, 1) := by
  constructor
  · refine ⟨rfl, ?_, sameElems_refl _, sameElems_refl _, rfl, rfl⟩
    intro c
    constructor <;> intro h <;>
      (rcases List.mem_cons.mp h with rfl | h' <;>
        first
          | exact List.mem_cons_of_mem _ List.mem_cons_self
          | (rcases List.mem_cons.mp h' with rfl | h'' <;>
              first
                | exact List.mem_cons_self
                | cases h''))
  · decide

/-! ## The kernel's refusal discipline

Refusal records verified same-level exhaustion; it is non-absorbing
(later events may still fire).  It certifies, it does not
terminalize. -/

theorem refusal_needs_certificate {w : World} {i j : Nat}
    (h : step w (.refuse i j) ≠ w) :
    obstructedB w (i, j) = true := by
  by_cases hc : obstructedB w (i, j) = true
  · exact hc
  · exfalso
    apply h
    simp only [step]
    rw [if_neg]
    intro hcond
    simp only [Bool.and_eq_true] at hcond
    exact hc hcond.1

theorem refusals_are_represented {w : World} {i j : Nat} :
    ((i, j) ∈ (step w (.refuse i j)).refusals) ∨
      step w (.refuse i j) = w := by
  simp only [step]
  split
  · left
    simp only [List.mem_append]
    right
    exact List.mem_cons_self
  · right
    rfl

end Represented
