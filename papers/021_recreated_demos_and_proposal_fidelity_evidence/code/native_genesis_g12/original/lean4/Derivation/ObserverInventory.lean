import Derivation.PrimDiff

/-!
# Nine-slot inventory of existing objects

A declared classification of objects this development already has.
It is not a dynamics, not a next challenge, and not a necessity
claim about any slot.

Nine slots, each named for what it hosts.  On the two-element
fragment they bind as follows:

* `carrier` — the carrier `Bool`
* `localState` — a local pair-state: empty, `D2`, `D2rev`, or `S2`
* `support` — that same relation, read as support
* `defect` — two defect readings, kept distinct: collision of a
  collapse map, versus obstruction relative to `Irrefl`
* `reversal` — two reversal maps that agree on `D2` and are not the
  same operation: relation `Transpose`, and pushforward along
  `Bool.not`
* `closure` — optional operation-family closure (`Clos`); the empty
  family is the identity
* `residual` — more than one residual on the local state (edge
  count versus the both-orientations bit)
* `maps` — maps; the transposition is an automorphism of `S2` and
  not of `D2`
* `terminal` — irreflexivity does not determine the local state:
  empty and `D2` are both irreflexive local states

Witness assignments occupy extra data on pairs.  They are present
when supplied.  They are not derived as the unique inhabitant:
the zero assignment and the one-oriented assignment both exist, and
the one-oriented assignment is the model already named
`PrimDiff.single_oriented_witness_consistent`.
-/

namespace ObserverInventory

open PrimDiff

/-! ## Slot names -/

inductive Slot where
  | carrier | localState | support | defect | reversal
  | closure | residual | maps | terminal
deriving DecidableEq, Repr

def slotList : List Slot :=
  [.carrier, .localState, .support, .defect, .reversal,
   .closure, .residual, .maps, .terminal]

theorem slot_count : slotList.length = 9 := rfl

theorem slots_nodup : slotList.Nodup := by decide

/-! ## Carrier, local state, and support on the two-element carrier -/

def EmptyRel : Bool → Bool → Prop := fun _ _ => False

instance (x y : Bool) : Decidable (EmptyRel x y) :=
  isFalse fun h => h

theorem empty_irrefl : Irrefl EmptyRel :=
  fun _ h => h

theorem empty_ne_D2 : EmptyRel ≠ D2 := by
  intro h
  have : EmptyRel false true := h ▸ D2_witness
  exact this

/-- Every irreflexive relation on `Bool` is empty, `D2`, `D2rev`, or
`S2`.  The nonempty fragment is `bool_irrefl_nonempty_classification`;
this includes the empty relation. -/
theorem bool_irrefl_full_classification (r : Bool → Bool → Prop)
    [inst : ∀ x y, Decidable (r x y)] (hi : Irrefl r) :
    r = EmptyRel ∨ r = D2 ∨ r = D2rev ∨ r = S2 := by
  by_cases hft : r false true
  · by_cases htf : r true false
    · right; right; right
      funext x y
      apply propext
      cases x <;> cases y
      · exact ⟨fun h => absurd h (hi false), fun h => absurd h (by decide)⟩
      · exact ⟨fun _ => Or.inl (by decide), fun _ => hft⟩
      · exact ⟨fun _ => Or.inr (by decide), fun _ => htf⟩
      · exact ⟨fun h => absurd h (hi true), fun h => absurd h (by decide)⟩
    · right; left
      funext x y
      apply propext
      cases x <;> cases y
      · exact ⟨fun h => absurd h (hi false), fun h => absurd h (by decide)⟩
      · exact ⟨fun _ => by decide, fun _ => hft⟩
      · exact ⟨fun h => absurd h htf, fun h => absurd h (by decide)⟩
      · exact ⟨fun h => absurd h (hi true), fun h => absurd h (by decide)⟩
  · by_cases htf : r true false
    · right; right; left
      funext x y
      apply propext
      cases x <;> cases y
      · exact ⟨fun h => absurd h (hi false), fun h => absurd h (by decide)⟩
      · exact ⟨fun h => absurd h hft, fun h => absurd h (by decide)⟩
      · exact ⟨fun _ => by decide, fun _ => htf⟩
      · exact ⟨fun h => absurd h (hi true), fun h => absurd h (by decide)⟩
    · left
      funext x y
      apply propext
      cases x <;> cases y
      · exact ⟨fun h => absurd h (hi false), fun h => absurd h (by decide)⟩
      · exact ⟨fun h => absurd h hft, fun h => absurd h (by decide)⟩
      · exact ⟨fun h => absurd h htf, fun h => absurd h (by decide)⟩
      · exact ⟨fun h => absurd h (hi true), fun h => absurd h (by decide)⟩

/-! ## Witnesses: present as data, not derived as necessary -/

def zeroW : Bool → Bool → Nat := fun _ _ => 0

def oneW : Bool → Bool → Nat
  | false, true => 1
  | _, _ => 0

/-- Two witness assignments exist as data.  Neither is derived as
the unique inhabitant.  The one-oriented assignment is the model of
`single_oriented_witness_consistent`; its presence relation is `D2`. -/
theorem witnesses_are_data :
    zeroW ≠ oneW ∧
      oneW false true = 1 ∧
      oneW true false = 0 ∧
      (∀ x y, ¬ (0 < zeroW x y)) ∧
      (∀ x y, (0 < oneW x y) ↔ D2 x y) := by
  refine ⟨?ne, rfl, rfl, ?z, ?p⟩
  · intro h
    have : zeroW false true = oneW false true :=
      congrFun (congrFun h false) true
    simp [zeroW, oneW] at this
  · intro x y h
    simp [zeroW] at h
  · intro x y
    cases x <;> cases y <;> simp [oneW, D2]

/-! ## Defect: two readings, not fused -/

/-- Collision of a collapse exists on the one-point self-difference,
which is not irreflexive.  Collision of a map is therefore not the
same reading as obstruction relative to `Irrefl`. -/
theorem collision_is_not_obstruction :
    ∃ r : Unit → Unit → Prop, r () () ∧ ¬ Irrefl r :=
  ⟨fun _ _ => True, trivial, fun hi => hi () trivial⟩

/-! ## Reversal: relation transpose and carrier swap -/

def pushNot (r : Bool → Bool → Prop) : Bool → Bool → Prop :=
  fun x y => r (Bool.not x) (Bool.not y)

theorem transpose_involutive {α : Type} (r : α → α → Prop) :
    Transpose (Transpose r) = r := rfl

theorem transpose_D2_eq_D2rev : Transpose D2 = D2rev := by
  funext x y
  apply propext
  constructor
  · intro h
    exact ⟨h.2, h.1⟩
  · intro h
    exact ⟨h.2, h.1⟩

theorem transpose_D2rev_eq_D2 : Transpose D2rev = D2 := by
  funext x y
  apply propext
  constructor
  · intro h
    exact ⟨h.2, h.1⟩
  · intro h
    exact ⟨h.2, h.1⟩

theorem pushNot_D2_eq_D2rev : pushNot D2 = D2rev := by
  funext x y
  apply propext
  cases x <;> cases y <;> simp [pushNot, D2, D2rev]

theorem transpose_eq_pushNot_on_D2 : Transpose D2 = pushNot D2 := by
  rw [transpose_D2_eq_D2rev, pushNot_D2_eq_D2rev]

/-- Relation transpose and pushforward along `Bool.not` are distinct
operations: they agree on `D2` and disagree on a self-loop. -/
theorem transpose_ne_pushNot :
    ∃ r : Bool → Bool → Prop, Transpose r ≠ pushNot r := by
  let r : Bool → Bool → Prop := fun x y => x = false ∧ y = false
  refine ⟨r, ?_⟩
  intro h
  have ht : Transpose r false false := ⟨rfl, rfl⟩
  have eqp : Transpose r false false = pushNot r false false :=
    congrFun (congrFun h false) false
  have hp : pushNot r false false := eqp ▸ ht
  exact Bool.noConfusion hp.1

/-! ## Closure: optional operation-family closure -/

theorem closure_empty_family_is_identity :
    ∀ f : Bool → Bool, Clos (fun _ => False) f → ∀ x, f x = x :=
  clos_empty_id

/-! ## Residuals: more than one -/

def edgeCount (r : Bool → Bool → Prop)
    [∀ x y, Decidable (r x y)] : Nat :=
  (if r false true then 1 else 0) + (if r true false then 1 else 0)

def isSymBit (r : Bool → Bool → Prop)
    [∀ x y, Decidable (r x y)] : Nat :=
  if r false true then (if r true false then 1 else 0) else 0

theorem residuals_not_unique :
    edgeCount D2 = 1 ∧ edgeCount S2 = 2 ∧
      isSymBit D2 = 0 ∧ isSymBit S2 = 1 ∧
      edgeCount D2 ≠ isSymBit D2 := by
  decide

/-! ## Maps and terminal: automorphisms, and no state determined -/

theorem swap_not_auto_of_D2 :
    ¬ (∀ x y, D2 x y ↔ D2 (Bool.not x) (Bool.not y)) :=
  (swap_auto_of_S2_not_of_D2).2

/-- The carrier swap is not an automorphism of the reverse
orientation either: it carries `D2rev` back to `D2`.  Companion to
the negative half of `swap_auto_of_S2_not_of_D2`. -/
theorem swap_not_auto_of_D2rev :
    ¬ (∀ x y, D2rev x y ↔ D2rev (Bool.not x) (Bool.not y)) := by
  decide

end ObserverInventory
