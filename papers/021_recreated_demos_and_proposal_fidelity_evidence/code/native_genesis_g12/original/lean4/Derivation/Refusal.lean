import Derivation.Basic
import Derivation.Inertia
import Derivation.PrimDiff

/-!
# Refusal as a difference source

Question (left open by the bridge investigation): can the failed
re-admission of one already admitted token, when that failure/refusal is
itself admitted as object-language data, produce a second distinguishable
state without a second token?

Five re-admission disciplines are formalized over one reduced signature
and compared without assuming that refusal, repetition, occurrence, and
state difference are equivalent:

* `silent`        — re-admission is a designation no-op (the first
                    development's semantics);
* `meta`          — re-admission is a state no-op; the runner records a
                    metatheoretic refusal marker in the history only;
* `fact`          — the refusal increments an admitted counter (a state
                    fact attached to no datum);
* `reifyUntagged` — the refusal is reified as another carrier occurrence
                    of the same token;
* `reifyTagged`   — as `reifyUntagged`, and the discipline additionally
                    tags the reified occurrence with a built-in unary
                    observable.

The comparison yields a strict hierarchy — history difference < state
difference < carrier growth < witnessed difference — with a separation
at every gap, one proved equivalence (`reifyUntagged` = occurrence
admission), and one genuinely new phenomenon: the tagged discipline
orients the difference it creates *canonically*, relocating the
symmetry-breaking choice from each act into the discipline declaration.
-/

namespace Refusal

open Derivation

/-- Reduced event signature: supplies, admissions, and the meta-mode
refusal marker (a history-only record). -/
inductive REvent where
  | supply  (tok : Nat)
  | admitTok (tok : Nat)
  | marker  (tok : Nat)
deriving Repr, DecidableEq

/-- Reduced state: admitted tokens in admission order, discipline-tagged
indices, and the refusal counter. -/
structure RState where
  data : List Nat
  tags : List Nat
  refusals : Nat
deriving Repr, DecidableEq

def emptyR : RState := ⟨[], [], 0⟩

inductive Mode where
  | silent | metaMarker | fact | reifyUntagged | reifyTagged
deriving Repr, DecidableEq

/-- One admission step of the given discipline.  Total: the reduced
signature has no ill-formed events. -/
def stepR (m : Mode) (s : RState) : REvent → RState
  | .supply _ => s
  | .marker _ => s
  | .admitTok tok =>
      if tok ∈ s.data then
        match m with
        | .silent => s
        | .metaMarker => s
        | .fact => { s with refusals := s.refusals + 1 }
        | .reifyUntagged => { s with data := s.data ++ [tok] }
        | .reifyTagged =>
            { s with data := s.data ++ [tok],
                     tags := s.tags ++ [s.data.length] }
      else { s with data := s.data ++ [tok] }

/-- Occurrence admission (the bridge investigation's declared
discipline): every admission appends. -/
def stepOcc (s : RState) : REvent → RState
  | .supply _ => s
  | .marker _ => s
  | .admitTok tok => { s with data := s.data ++ [tok] }

def replayR (m : Mode) (h : List REvent) : RState :=
  h.foldl (stepR m) emptyR

def replayOcc (h : List REvent) : RState :=
  h.foldl stepOcc emptyR

/-! ## Level 0/1: silent versus meta — history difference without state
difference -/

/-- The silent and meta disciplines have literally the same state
semantics: the meta marker exists only in the history. -/
theorem silent_eq_meta : ∀ s e, stepR .silent s e = stepR .metaMarker s e := by
  intro s e
  cases e <;> simp [stepR]

/-- Markers are state-invisible in every mode. -/
theorem marker_state_invisible (m : Mode) (s : RState) (tok : Nat) :
    stepR m s (.marker tok) = s := rfl

/-- The marker recognizer. -/
def isMarker : REvent → Bool
  | .marker _ => true
  | _ => false

theorem markers_invisible_from (m : Mode) (h : List REvent) :
    ∀ s, (h.filter fun e => !isMarker e).foldl (stepR m) s =
      h.foldl (stepR m) s := by
  induction h with
  | nil => intro _; rfl
  | cons e rest ih =>
      intro s
      cases e with
      | marker tok =>
          simp only [List.filter, isMarker, Bool.not_true, List.foldl]
          exact ih s
      | supply tok =>
          simp only [List.filter, isMarker, Bool.not_false, List.foldl]
          exact ih _
      | admitTok tok =>
          simp only [List.filter, isMarker, Bool.not_false, List.foldl]
          exact ih _

/-- Histories differing by markers replay identically: history
difference is strictly below state difference. -/
theorem markers_invisible (m : Mode) (h : List REvent) :
    replayR m (h.filter fun e => !isMarker e) = replayR m h :=
  markers_invisible_from m h emptyR

/-! ## Level 2: fact refusal — state difference without carrier growth -/

/-- Non-reifying disciplines obey the single-token carrier bound: the
data store stays within the singleton. -/
def AtMostTokR (t0 : Nat) (s : RState) : Prop :=
  s.data = [] ∨ s.data = [t0]

theorem nonreify_carrier_bound {m : Mode}
    (hm : m = .silent ∨ m = .metaMarker ∨ m = .fact) {t0 : Nat} {s : RState}
    (hs : AtMostTokR t0 s) {e : REvent}
    (he : ∀ tok, e = REvent.admitTok tok → tok = t0) :
    AtMostTokR t0 (stepR m s e) := by
  cases e with
  | supply tok => exact hs
  | marker tok => exact hs
  | admitTok tok =>
      have htok : tok = t0 := he tok rfl
      subst htok
      by_cases hmem : tok ∈ s.data
      · simp only [stepR]
        rw [if_pos hmem]
        cases hm with
        | inl h => subst h; exact hs
        | inr hm2 =>
            cases hm2 with
            | inl h => subst h; exact hs
            | inr h => subst h; exact hs
      · simp only [stepR]
        rw [if_neg hmem]
        cases hs with
        | inl h =>
            right
            show s.data ++ [tok] = [tok]
            rw [h]
            rfl
        | inr h => exact absurd (by rw [h]; simp) hmem

/-- The fact discipline changes the state on refusal... -/
theorem fact_state_changes :
    stepR .fact ⟨[0], [], 0⟩ (.admitTok 0) ≠ ⟨[0], [], 0⟩ := by decide

/-- ...while the silent discipline does not: state difference separates
the two, carrier growth separates neither (both stay at one datum). -/
theorem silent_state_fixed :
    stepR .silent ⟨[0], [], 0⟩ (.admitTok 0) = ⟨[0], [], 0⟩ := by decide

/-! ## Level 3: reification — carrier growth; and one proved equivalence -/

/-- The untagged reifying discipline *is* occurrence admission: their
steppers agree on every state and event.  An assumed non-equivalence,
refuted by proof. -/
theorem reifyUntagged_eq_occurrence :
    ∀ s e, stepR .reifyUntagged s e = stepOcc s e := by
  intro s e
  cases e with
  | supply tok => rfl
  | marker tok => rfl
  | admitTok tok =>
      by_cases hmem : tok ∈ s.data
      · simp [stepR, stepOcc, hmem]
      · simp [stepR, stepOcc, hmem]

theorem reify_occ_from (h : List REvent) :
    ∀ s, h.foldl (stepR .reifyUntagged) s = h.foldl stepOcc s := by
  induction h with
  | nil => intro _; rfl
  | cons e rest ih =>
      intro s
      simp only [List.foldl]
      rw [reifyUntagged_eq_occurrence]
      exact ih _

theorem reifyUntagged_replay_eq_occurrence (h : List REvent) :
    replayR .reifyUntagged h = replayOcc h :=
  reify_occ_from h emptyR

/-- Carrier growth from one token, untagged: two occurrences, no tags,
no counter — and no object-level distinction between the occurrences
(the state is fixed by the index swap, next section). -/
theorem reifyUntagged_two_admissions :
    replayR .reifyUntagged [.admitTok 0, .admitTok 0] = ⟨[0, 0], [], 0⟩ := by
  decide

/-! ## Level 4: the tagged discipline — witnessed, oriented difference -/

theorem reifyTagged_two_admissions :
    replayR .reifyTagged [.admitTok 0, .admitTok 0] = ⟨[0, 0], [1], 0⟩ := by
  decide

/-- The built-in tag observable separates the two occurrences: index 1
is tagged, index 0 is not.  A witnessed difference from one token and
two admissions. -/
theorem tag_separates :
    (1 ∈ (replayR .reifyTagged [.admitTok 0, .admitTok 0]).tags) ∧
    (0 ∉ (replayR .reifyTagged [.admitTok 0, .admitTok 0]).tags) := by
  decide

/-- The swap of the two occurrence indices on a two-element reduced
state. -/
def swapIdx : Nat → Nat := fun i => if i = 0 then 1 else if i = 1 then 0 else i

def swapState (s : RState) : RState :=
  ⟨s.data, s.tags.map swapIdx, s.refusals⟩

/-- The untagged (= occurrence) two-element state is swap-invariant:
the two occurrences are symmetric, so designating one is a per-act
choice (the equivariance obstruction of the bridge investigation
applies). -/
theorem occurrence_state_swap_invariant :
    swapState (replayR .reifyUntagged [.admitTok 0, .admitTok 0]) =
      replayR .reifyUntagged [.admitTok 0, .admitTok 0] := by
  decide

/-- The tagged state is *not* swap-invariant: the discipline itself
breaks the symmetry.  Orientation arrives canonically — established
versus refused — with no per-act choice.  The symmetry-breaking choice
was made once, in the discipline declaration. -/
theorem tagged_state_not_swap_invariant :
    swapState (replayR .reifyTagged [.admitTok 0, .admitTok 0]) ≠
      replayR .reifyTagged [.admitTok 0, .admitTok 0] := by
  decide

/-- Canonical designation: the tagged discipline provides a designated
occurrence (the head of the tag list); the untagged discipline provides
none.  The designation the bridge investigation proved impossible to
choose equivariantly from a symmetric state is here supplied by never
entering a symmetric state. -/
theorem canonical_designation :
    (replayR .reifyTagged [.admitTok 0, .admitTok 0]).tags.head? = some 1 ∧
    (replayR .reifyUntagged [.admitTok 0, .admitTok 0]).tags.head? = none := by
  decide

/-! ## No free lunch: the tag is a priced unary observable -/

/-- Translation of the tagged two-element state into the admission
model's signature: one unary form, one instance marking the tagged
index.  The discipline's built-in observable is exactly one form plus
one instance. -/
def taggedTranslation : Regime := ⟨2, [1], [(0, [1])], [], []⟩

/-- The translated state is separable in the admission model's sense —
the tag observable and the explicit unary mark have the same separating
content... -/
theorem tagged_translation_separable :
    Derivation.separable taggedTranslation 0 1 :=
  ⟨⟨0, [none]⟩, by decide, by decide⟩

/-- ...while the untagged translation (no form, no instance) is
collapsed: without the built-in tag the two occurrences are
object-indistinguishable, exactly as in occurrence admission. -/
theorem untagged_translation_collapsed :
    Derivation.collapsed ⟨2, [], [], [], []⟩ 0 1 :=
  collapsed_of_no_insts _ rfl 0 1

end Refusal
