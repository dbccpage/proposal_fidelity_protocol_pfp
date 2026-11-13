import Derivation.Basic
import Derivation.Erasure
import Derivation.PrimDiff

/-!
# The bridge: provenance of the Primitive Difference ingredients

Question: can the opaque inscription be elaborated into a witnessed
irreflexive datum, or which components must be externally admitted?

This module deliberately imports *both* prior developments — the
admission model (histories, token-aware states) and the primitive
difference layer — because the question is exactly the bridge between
them.  Each ingredient of the target object

  carrier · two designated occurrences · relation · witness ·
  irreflexivity · orientation

gets a provenance theorem or countermodel.  No gap is filled silently:
where the metatheory *could* supply an ingredient (positions, supply
order, token identity), that import is stated as a theorem about the
metatheory and flagged as invisible to the object language.
-/

namespace Bridge

open Derivation

/-! ## Carrier and two-ness -/

/-- Histories whose every datum admission carries the same token. -/
def SingleTok (t0 : Nat) (e : TEvent) : Prop :=
  ∀ tok, e = TEvent.admitDatum tok → tok = t0

/-- Invariant: under single-token admission, the token store is empty or
exactly the singleton. -/
def AtMostTok (t0 : Nat) (t : TRegime) : Prop :=
  t.tokens = [] ∨ t.tokens = [t0]

theorem stepT_preserves_atMostTok {t0 : Nat} {t : TRegime}
    (ht : AtMostTok t0 t) {e : TEvent} (he : SingleTok t0 e)
    {t' : TRegime} (hs : stepT t e = some t') : AtMostTok t0 t' := by
  cases e with
  | supply tok =>
      cases Option.some.inj hs
      exact ht
  | admitDatum tok =>
      have htok : tok = t0 := he tok rfl
      rw [htok] at hs
      by_cases hmem : t0 ∈ t.tokens
      · simp only [stepT] at hs
        rw [if_pos hmem] at hs
        cases Option.some.inj hs
        exact ht
      · simp only [stepT] at hs
        rw [if_neg hmem] at hs
        cases Option.some.inj hs
        cases ht with
        | inl h =>
            right
            show t.tokens ++ [t0] = [t0]
            rw [h]
            rfl
        | inr h =>
            exact absurd (by rw [h]; simp) hmem
  | admitForm a =>
      simp only [stepT] at hs
      split at hs
      · cases Option.some.inj hs; exact ht
      · cases hs
  | admitInst f args =>
      simp only [stepT] at hs
      split at hs
      · cases Option.some.inj hs; exact ht
      · cases hs
  | admitRuleAll f =>
      simp only [stepT] at hs
      split at hs
      · cases Option.some.inj hs; exact ht
      · cases hs
  | impose i j =>
      simp only [stepT] at hs
      split at hs
      · cases Option.some.inj hs; exact ht
      · cases hs

/-- **Carrier bound.**  One opaque inscription never yields a carrier of
size two: any history whose datum admissions all carry the same token
leaves at most one admitted datum, no matter how often the inscription is
re-supplied or re-admitted. -/
theorem single_token_carrier_bound (t0 : Nat) (h : List TEvent)
    (hall : ∀ e ∈ h, SingleTok t0 e) {t : TRegime}
    (ht : AtMostTok t0 t) {res : TRegime}
    (hr : replayT h t = some res) : res.tokens.length ≤ 1 := by
  induction h generalizing t with
  | nil =>
      have : t = res := Option.some.inj hr
      subst this
      cases ht with
      | inl h0 => rw [h0]; exact Nat.zero_le 1
      | inr h1 => rw [h1]; exact Nat.le_refl 1
  | cons e rest ih =>
      rw [replayT_cons] at hr
      cases hs : stepT t e with
      | none => rw [hs] at hr; cases hr
      | some t1 =>
          rw [hs] at hr
          exact ih
            (fun e' he' => hall e' (List.mem_cons_of_mem _ he'))
            (stepT_preserves_atMostTok ht
              (hall e (List.mem_cons_self)) hs)
            hr

instance (t0 : Nat) (e : TEvent) : Decidable (SingleTok t0 e) :=
  match e with
  | .supply _ => isTrue (fun _ h => nomatch h)
  | .admitForm _ => isTrue (fun _ h => nomatch h)
  | .admitInst _ _ => isTrue (fun _ h => nomatch h)
  | .admitRuleAll _ => isTrue (fun _ h => nomatch h)
  | .impose _ _ => isTrue (fun _ h => nomatch h)
  | .admitDatum tok =>
      if htok : tok = t0 then
        isTrue (fun tok' h => by cases h; exact htok)
      else
        isFalse (fun hall => htok (hall tok rfl))

/-- A decidably refuted bounded universal yields an explicit witness. -/
theorem exists_not_of_not_ball {α : Type} (l : List α) (P : α → Prop)
    [DecidablePred P] (h : ¬ ∀ x ∈ l, P x) : ∃ x ∈ l, ¬ P x := by
  induction l with
  | nil => exact absurd (fun x hx => nomatch hx) h
  | cons a rest ih =>
      cases hd : decide (P a) with
      | true =>
          have ha : P a := of_decide_eq_true hd
          have hrest : ¬ ∀ x ∈ rest, P x := fun hr =>
            h (fun x hx => by
              cases hx with
              | head => exact ha
              | tail _ hx => exact hr x hx)
          have ⟨x, hx, hnp⟩ := ih hrest
          exact ⟨x, List.mem_cons_of_mem _ hx, hnp⟩
      | false =>
          exact ⟨a, List.mem_cons_self, of_decide_eq_false hd⟩

/-- **Two-ness needs a second external token** (contrapositive form):
a state with two admitted data comes only from a history admitting some
token different from the first. -/
theorem second_token_required (t0 : Nat) (h : List TEvent)
    {res : TRegime}
    (hr : replayT h ⟨[], [], [], [], []⟩ = some res)
    (htwo : 2 ≤ res.tokens.length) :
    ∃ e ∈ h, ∃ tok, e = TEvent.admitDatum tok ∧ tok ≠ t0 := by
  cases hd : decide (∀ e ∈ h, SingleTok t0 e) with
  | true =>
      have hall : ∀ e ∈ h, SingleTok t0 e := of_decide_eq_true hd
      have hle := single_token_carrier_bound t0 h hall (Or.inl rfl) hr
      exact absurd htwo (by omega)
  | false =>
      have hall : ¬ ∀ e ∈ h, SingleTok t0 e := of_decide_eq_false hd
      have ⟨e, he, hnot⟩ := exists_not_of_not_ball h (SingleTok t0) hall
      refine ⟨e, he, ?_⟩
      cases e with
      | admitDatum tok =>
          refine ⟨tok, rfl, fun htok => ?_⟩
          exact hnot (fun tok' hh => by cases hh; exact htok)
      | supply tok => exact absurd (fun _ hh => nomatch hh) hnot
      | admitForm a => exact absurd (fun _ hh => nomatch hh) hnot
      | admitInst f args => exact absurd (fun _ hh => nomatch hh) hnot
      | admitRuleAll f => exact absurd (fun _ hh => nomatch hh) hnot
      | impose i j => exact absurd (fun _ hh => nomatch hh) hnot

/-! ## Relation and witness -/

/-- Histories with no form admission leave the form table empty (the
inertia of the signature: nothing derives a relation symbol). -/
theorem no_admitForm_no_forms (h : List TEvent)
    (hall : ∀ e ∈ h, ∀ a, e ≠ TEvent.admitForm a) {t : TRegime}
    (hf : t.forms = []) {res : TRegime}
    (hr : replayT h t = some res) : res.forms = [] := by
  induction h generalizing t with
  | nil =>
      have : t = res := Option.some.inj hr
      subst this; exact hf
  | cons e rest ih =>
      rw [replayT_cons] at hr
      cases hs : stepT t e with
      | none => rw [hs] at hr; cases hr
      | some t1 =>
          rw [hs] at hr
          refine ih (fun e' he' => hall e' (List.mem_cons_of_mem _ he'))
            ?_ hr
          cases e with
          | supply tok => cases Option.some.inj hs; exact hf
          | admitDatum tok =>
              simp only [stepT] at hs
              split at hs <;>
                (cases Option.some.inj hs; exact hf)
          | admitForm a =>
              exact absurd rfl (hall _ (List.mem_cons_self) a)
          | admitInst f args =>
              simp only [stepT] at hs
              split at hs
              · cases Option.some.inj hs; exact hf
              · cases hs
          | admitRuleAll f =>
              simp only [stepT] at hs
              split at hs
              · cases Option.some.inj hs; exact hf
              · cases hs
          | impose i j =>
              simp only [stepT] at hs
              split at hs
              · cases Option.some.inj hs; exact hf
              · cases hs

/-- With an empty form table no instance is admissible, so no witness
ever exists: the relation and its witness are external admissions, never
derivations. -/
theorem no_forms_no_witness (t : TRegime) (hf : t.forms = [])
    (f : Nat) (args : List Nat) :
    stepT t (TEvent.admitInst f args) = none := by
  simp [stepT, hf]

/-! ## Irreflexivity: fact versus law -/

/-- Any irreflexive fact set has a bare-signature extension with a
self-edge: finite facts never entail the irreflexivity *law*.  The law is
a declared protected property, not a consequence. -/
theorem irrefl_law_not_entailed {α : Type} (r : α → α → Prop)
    (a : α) :
    ∃ r' : α → α → Prop,
      (∀ x y, r x y → r' x y) ∧ ¬ PrimDiff.Irrefl r' :=
  ⟨fun x y => r x y ∨ (x = a ∧ y = a),
   fun _ _ h => Or.inl h,
   fun hi => hi a (Or.inr ⟨rfl, rfl⟩)⟩

/-! ## Orientation and designation: the equivariance obstruction -/

/-- Any swap-invariant, irreflexive-as-fact, inhabited relation on the
two-element carrier is exactly `S2`: an equivariant (choice-free)
introduction rule can reach the symmetric difference but never the
oriented one. -/
theorem equivariant_witness_is_S2 (S : Bool → Bool → Prop)
    (hinv : ∀ x y, S x y ↔ S (Bool.not x) (Bool.not y))
    (hi : PrimDiff.Irrefl S)
    (hne : S false true ∨ S true false) : ∀ x y, S x y ↔ PrimDiff.S2 x y := by
  have hft : S false true := by
    cases hne with
    | inl h => exact h
    | inr h =>
        have := (hinv true false).mp h
        simpa using this
  have htf : S true false := by
    have := (hinv false true).mp hft
    simpa using this
  intro x y
  cases x <;> cases y
  · exact ⟨fun h => absurd h (hi false), fun h => absurd h (by decide)⟩
  · exact ⟨fun _ => by decide, fun _ => hft⟩
  · exact ⟨fun _ => by decide, fun _ => htf⟩
  · exact ⟨fun h => absurd h (hi true), fun h => absurd h (by decide)⟩

/-- In particular no equivariant introduction yields the oriented datum:
`D2` asserts (false, true) but not (true, false), and equivariance forces
both or neither. -/
theorem equivariant_not_D2 (S : Bool → Bool → Prop)
    (hinv : ∀ x y, S x y ↔ S (Bool.not x) (Bool.not y))
    (hi : PrimDiff.Irrefl S)
    (hne : S false true ∨ S true false) :
    ¬ (∀ x y, S x y ↔ PrimDiff.D2 x y) := by
  intro hD2
  have hS2 := equivariant_witness_is_S2 S hinv hi hne
  have h1 : PrimDiff.D2 true false := by
    exact (hD2 true false).mp ((hS2 true false).mpr (by decide))
  exact absurd h1 (by decide)

/-- No ordered off-diagonal pair on the two-element carrier is fixed by
the swap: an equivariant *designation* of an ordered pair does not exist.
Unordered two-ness is swap-invariant; orientation is not. -/
theorem no_swap_fixed_offdiag_pair :
    ∀ x y : Bool, x ≠ y → (Bool.not x, Bool.not y) ≠ (x, y) := by
  decide

/-! ## Admission order: metatheoretic orientation, erased at object
level -/

/-- The two-token admission history in one order... -/
def hist01 : List TEvent :=
  [.supply 0, .admitDatum 0, .supply 1, .admitDatum 1]

/-- ...and in the other order. -/
def hist10 : List TEvent :=
  [.supply 1, .admitDatum 1, .supply 0, .admitDatum 0]

/-- Admission order is present in the token-aware state: the two
admission orders produce different token lists (`Supply` itself is a
proved no-op; the asymmetry comes from the `admitDatum` append order).
A metatheoretic orientation (first-admitted versus second-admitted)
exists for free. -/
theorem order_visible_to_metatheory :
    replayT hist01 ⟨[], [], [], [], []⟩ ≠
      replayT hist10 ⟨[], [], [], [], []⟩ := by
  decide

/-- Yet that orientation is erased at the object level: the two orders
have identical token-erased states.  Internalizing the order as an
object-level asymmetry requires an admitted asymmetric fact — which is
the oriented witness itself, hence external (by
`equivariant_not_D2`). -/
theorem order_erased_at_object_level :
    (replayT hist01 ⟨[], [], [], [], []⟩).map TRegime.erase =
      (replayT hist10 ⟨[], [], [], [], []⟩).map TRegime.erase := by
  decide

end Bridge
