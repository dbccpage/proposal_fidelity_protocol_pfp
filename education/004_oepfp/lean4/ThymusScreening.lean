/-!
# Thymus screening soundness (Lemma C and the OEEIS self-panel gate)

AuthorityEffect: None. This file is a proposal; the status upgrade is the
author's.

Core Lean 4 only (no imports). Mechanizes:

* Lemma C, "negative selection screens what it screens", from
  `omega_engine_atlas/coda_atlas/F004_papers/015_pfp/003_pfp_host_admitted_failure_detectors/paper.md`
  Appendix A.4 (lines 727 to 760 at commit `8ac5da188`), ledger row P3-22.
  A detector rule has a screened predicate `P` and an executed predicate `E`
  over a universe `U`. The screen admits the rule for a finite panel `S`
  when no member of `S` satisfies `P`. Screening is sound for `S` when an
  admitted rule never fires on a member of `S`.

* The OEEIS Thymus gate and its Self-Panel Soundness theorem from
  `omega_engine_education/documentation/004_oepfp/math/math_epistemic_immune_system_and_negative_selection.md`
  Section 2 (lines 80 to 97): `Thymus(d) = ADMIT` exactly when every sealed
  self item `s` has `d s = 0`, and every admitted detector has zero false
  positives on the sealed panel. This is Lemma C part 1 with `E = P = d`,
  stated as a count.

Predicates are `Bool`-valued (`d : X → {0,1}` in the source), so no
classical axiom and no decidability instance is needed. Panels are `List U`; a list
is a finite subset with possible repetition, which changes nothing here
because every statement quantifies over members.
-/

namespace Oeeis.Thymus

variable {U : Type}

/-- The screen admits the rule for panel `S`: no member of `S` satisfies the
screened predicate `P`. -/
def admits (P : U → Bool) (S : List U) : Prop := ∀ x ∈ S, P x = false

/-- The rule fires on panel `S`: some member of `S` satisfies the executed
predicate `E`. -/
def fires (E : U → Bool) (S : List U) : Prop := ∃ x ∈ S, E x = true

/-- Screening is sound for `S`: an admitted rule does not fire on `S`. -/
def soundFor (P E : U → Bool) (S : List U) : Prop := admits P S → ¬ fires E S

/-- The rule is harmless for `S`: it does not fire on `S`. -/
def harmlessFor (E : U → Bool) (S : List U) : Prop := ¬ fires E S

/-- Screening never rejects a harmless rule for `S`: a rule that does not
fire on `S` is admitted for `S`. -/
def neverRejectsHarmless (P E : U → Bool) (S : List U) : Prop :=
  harmlessFor E S → admits P S

/-- Bool case analysis used by the singleton-panel steps. -/
theorem bool_false_of_not_true {b : Bool} (h : ¬ b = true) : b = false := by
  cases b with
  | false => rfl
  | true => exact absurd rfl h

/-- Membership in a singleton panel. -/
theorem mem_singleton_self (x : U) : x ∈ [x] := List.Mem.head []

/-- The only member of a singleton panel is its element. -/
theorem eq_of_mem_singleton {x y : U} (h : y ∈ [x]) : y = x := by
  cases h with
  | head => rfl
  | tail _ h' => cases h'

/-- Lemma C, part 1. Screening is sound for every panel exactly when the
executed predicate implies the screened one on the whole universe.

Forward direction: the singleton panel `[x]`. If `E x` held and `P x` did
not, `[x]` would let the rule through, and the rule then fires on `x`.
Backward direction: an admitted rule has `P x = false` on every member, so
`E x = true` on a member would give `P x = true`, a Bool contradiction. -/
theorem sound_all_iff (P E : U → Bool) :
    (∀ S : List U, soundFor P E S) ↔ (∀ x, E x = true → P x = true) := by
  constructor
  · intro h x hE
    cases hP : P x with
    | true => rfl
    | false =>
      exfalso
      apply h [x]
      · intro y hy
        have hyx : y = x := eq_of_mem_singleton hy
        rw [hyx]
        exact hP
      · exact ⟨x, mem_singleton_self x, hE⟩
  · intro h S hadm hfire
    match hfire with
    | ⟨x, hx, hE⟩ =>
      have hPx : P x = true := h x hE
      rw [hadm x hx] at hPx
      exact Bool.false_ne_true hPx

/-- Lemma C, part 2. Screening never rejects a rule that is harmless for the
panel, for every panel, exactly when the screened predicate implies the
executed one on the whole universe. The same singleton-panel argument with
`E` and `P` exchanged. -/
theorem never_rejects_all_iff (P E : U → Bool) :
    (∀ S : List U, neverRejectsHarmless P E S) ↔ (∀ x, P x = true → E x = true) := by
  constructor
  · intro h x hP
    cases hE : E x with
    | true => rfl
    | false =>
      exfalso
      have hadm : admits P [x] := h [x] (fun hfire =>
        match hfire with
        | ⟨y, hy, hEy⟩ =>
          have hyx : y = x := eq_of_mem_singleton hy
          have hEx : E x = true := by rw [hyx] at hEy; exact hEy
          Bool.false_ne_true (hE.symm.trans hEx))
      have hPx : P x = false := hadm x (mem_singleton_self x)
      exact Bool.false_ne_true (hPx.symm.trans hP)
  · intro h S hharm x hx
    cases hP : P x with
    | false => rfl
    | true =>
      exfalso
      exact hharm ⟨x, hx, h x hP⟩

/-- Lemma C, part 3. Both hold for every panel exactly when `E = P` on `U`. -/
theorem both_all_iff (P E : U → Bool) :
    ((∀ S, soundFor P E S) ∧ (∀ S, neverRejectsHarmless P E S)) ↔ (∀ x, E x = P x) := by
  constructor
  · intro hboth x
    have h1 : ∀ x, E x = true → P x = true := (sound_all_iff P E).mp hboth.1
    have h2 : ∀ x, P x = true → E x = true := (never_rejects_all_iff P E).mp hboth.2
    cases hE : E x with
    | true => exact (h1 x hE).symm
    | false =>
      cases hP : P x with
      | false => rfl
      | true =>
        have hEx : E x = true := h2 x hP
        rw [hE] at hEx
        exact absurd hEx Bool.false_ne_true
  · intro h
    exact ⟨(sound_all_iff P E).mpr (fun x hE => (h x).symm.trans hE),
           (never_rejects_all_iff P E).mpr (fun x hP => (h x).trans hP)⟩

/-! ## OEEIS instance: the Thymus gate with `E = P = d` -/

/-- `Thymus(d) = ADMIT` as a Bool: every sealed self item is not detected. -/
def thymusAdmit (d : U → Bool) (sealed : List U) : Bool := sealed.all (fun s => !d s)

/-- The numerator of `FPR_{S_sealed}(d)`: the number of sealed self items the
detector fires on. -/
def falsePositives (d : U → Bool) (sealed : List U) : Nat := (sealed.filter d).length

theorem bnot_eq_true_iff (b : Bool) : (!b) = true ↔ b = false := by
  cases b <;> decide

theorem band_eq_true_iff (a b : Bool) : (a && b) = true ↔ a = true ∧ b = true := by
  cases a <;> cases b <;> decide

/-- The Bool gate agrees with the Prop-level `admits` with `P = d`. -/
theorem thymus_admit_iff (d : U → Bool) :
    ∀ (sealed : List U), thymusAdmit d sealed = true ↔ admits d sealed
  | [] => by
    constructor
    · intro _ x hx
      cases hx
    · intro _
      rfl
  | a :: l => by
    have ih := thymus_admit_iff d l
    constructor
    · intro h x hx
      have hsplit : (!d a) = true ∧ l.all (fun s => !d s) = true :=
        (band_eq_true_iff _ _).mp h
      cases hx with
      | head => exact (bnot_eq_true_iff (d a)).mp hsplit.1
      | tail _ hx' => exact ih.mp hsplit.2 x hx'
    · intro h
      have ha : (!d a) = true := (bnot_eq_true_iff (d a)).mpr (h a (List.Mem.head l))
      have hl : l.all (fun s => !d s) = true :=
        ih.mpr (fun x hx => h x (List.Mem.tail a hx))
      exact (band_eq_true_iff _ _).mpr ⟨ha, hl⟩

/-- An admitted detector filters nothing out of the sealed panel. -/
theorem filter_eq_nil_of_admits (d : U → Bool) :
    ∀ (S : List U), admits d S → S.filter d = []
  | [], _ => rfl
  | a :: l, h => by
    have ha : d a = false := h a (List.Mem.head l)
    have ih : l.filter d = [] :=
      filter_eq_nil_of_admits d l (fun x hx => h x (List.Mem.tail a hx))
    rw [List.filter, ha]
    exact ih

/-- Self-Panel Soundness (OEEIS Section 2.2): an admitted detector has zero
false positives on the sealed panel. The source states the mean
`(1/|S|) Σ d(s) = 0`; the numerator is zero, so the mean is zero for every
nonempty panel. -/
theorem self_panel_soundness (d : U → Bool) (sealed : List U)
    (h : thymusAdmit d sealed = true) : falsePositives d sealed = 0 := by
  unfold falsePositives
  rw [filter_eq_nil_of_admits d sealed ((thymus_admit_iff d sealed).mp h)]
  rfl

/-- Self-Panel Soundness restated through Lemma C: with `E = P = d` the
executed predicate implies the screened one, so screening is sound for
every panel. -/
theorem self_panel_sound_for_every_panel (d : U → Bool) :
    ∀ S : List U, soundFor d d S :=
  (sound_all_iff d d).mpr (fun _ h => h)

/-! ## Negative control: the counterexample of Lemma C part 1

Paper A.4, `test_pattern_ignoring_matcher_is_admitted_and_fires_on_a_self_fixture`:
the screen tests a failure-class name (`MISSING_WITNESS`), which no self
record mentions; the matcher tests the structure of the record (no
`"witness"` field). The two self records are
`{"claim": "x", "witness": "w"}` and `{"claim": "y", "evidence": []}`. -/

inductive Record where
  | claimWithWitness
  | claimWithEvidenceOnly
  deriving DecidableEq, Repr

/-- Screened predicate: the record names the failure class. No self record
does. -/
def screenedByName : Record → Bool := fun _ => false

/-- Executed predicate: the record has no `"witness"` field. -/
def executedNoWitness : Record → Bool
  | .claimWithWitness => false
  | .claimWithEvidenceOnly => true

theorem control_predicates_differ : screenedByName ≠ executedNoWitness :=
  fun h => nomatch congrFun h Record.claimWithEvidenceOnly

/-- The singleton self panel admits the rule. -/
theorem control_admitted : thymusAdmit screenedByName [Record.claimWithEvidenceOnly] = true := by
  decide

/-- The admitted rule fires on the panel member: one false positive. -/
theorem control_fires_count : falsePositives executedNoWitness [Record.claimWithEvidenceOnly] = 1 := by
  decide

theorem control_fires : fires executedNoWitness [Record.claimWithEvidenceOnly] :=
  ⟨Record.claimWithEvidenceOnly, mem_singleton_self _, rfl⟩

/-- Screening is not sound for this panel. -/
theorem control_not_sound :
    ¬ soundFor screenedByName executedNoWitness [Record.claimWithEvidenceOnly] :=
  fun hs => hs (fun _ _ => rfl) control_fires

/-- The hypothesis of Lemma C part 1 fails, as it must by `sound_all_iff`. -/
theorem control_implication_fails :
    ¬ (∀ x, executedNoWitness x = true → screenedByName x = true) :=
  fun h => nomatch h Record.claimWithEvidenceOnly rfl

end Oeeis.Thymus

#print axioms Oeeis.Thymus.sound_all_iff
#print axioms Oeeis.Thymus.never_rejects_all_iff
#print axioms Oeeis.Thymus.both_all_iff
#print axioms Oeeis.Thymus.thymus_admit_iff
#print axioms Oeeis.Thymus.self_panel_soundness
#print axioms Oeeis.Thymus.self_panel_sound_for_every_panel
#print axioms Oeeis.Thymus.control_not_sound
