/-!
# Core model

A *token-erased abstraction* of `code/derivation/model.py` and
`observe.py`: presentation tokens are deliberately absent (data are
counted, not named); token-level datum deduplication is bridged by the
erasure simulation in `Derivation/Erasure.lean`.  The admitted instance,
rule, and requirement collections are sets in the Python model, so every
admission here uses deduplicating insertion (`insertNew`): repeated
admission of any event kind is idempotent, matching Python.

A regime is the admitted state: a count of admitted data (internal identity
is the index), a list of judgment-form arities, admitted judgment
instances, forms carrying the uniform all-tuples rule, and externally
imposed separation requirements.
-/

namespace Derivation

/-- Judgment instance: a form index and an argument tuple of datum indices. -/
abbrev Inst := Nat × List Nat

/-- Deduplicating insertion: the admitted collections are sets, so
re-admission is a no-op. -/
def insertNew {α : Type} [DecidableEq α] (l : List α) (a : α) : List α :=
  if a ∈ l then l else l ++ [a]

@[simp] theorem insertNew_nil {α : Type} [DecidableEq α] (a : α) :
    insertNew [] a = [a] := rfl

theorem insertNew_of_not_mem {α : Type} [DecidableEq α] {l : List α}
    {a : α} (h : a ∉ l) : insertNew l a = l ++ [a] := by
  simp [insertNew, h]

theorem insertNew_of_mem {α : Type} [DecidableEq α] {l : List α}
    {a : α} (h : a ∈ l) : insertNew l a = l := by
  simp [insertNew, h]

/-- Membership after deduplicating insertion. -/
theorem mem_insertNew {α : Type} [DecidableEq α] {l : List α} {a x : α} :
    x ∈ insertNew l a ↔ x ∈ l ∨ x = a := by
  by_cases h : a ∈ l
  · rw [insertNew_of_mem h]
    constructor
    · exact Or.inl
    · intro hx
      cases hx with
      | inl hx => exact hx
      | inr hx => exact hx ▸ h
  · rw [insertNew_of_not_mem h]
    simp [List.mem_append]

structure Regime where
  data  : Nat
  forms : List Nat
  insts : List Inst
  rules : List Nat
  reqs  : List (Nat × Nat)
deriving Repr, DecidableEq

/-- Well-formed regime: instances respect form arity and datum bounds,
rules name admitted forms, requirements are ordered pairs of admitted data,
and every form has arity at least one. -/
def Regime.wf (r : Regime) : Prop :=
  (∀ p ∈ r.insts,
      p.1 < r.forms.length ∧
      p.2.length = r.forms.getD p.1 0 ∧
      ∀ a ∈ p.2, a < r.data) ∧
  (∀ f ∈ r.rules, f < r.forms.length) ∧
  (∀ q ∈ r.reqs, q.1 < q.2 ∧ q.2 < r.data) ∧
  (∀ a ∈ r.forms, 1 ≤ a)

/-- A context: a judgment form with slots, where `none` is a hole. -/
structure Ctx where
  form  : Nat
  slots : List (Option Nat)
deriving Repr, DecidableEq

/-- Plugging fills every hole with the same datum. -/
def plug (c : Ctx) (d : Nat) : Inst :=
  (c.form, c.slots.map (fun s => s.getD d))

/-- Derivability: membership in the admitted instances, or coverage by a
uniform all-tuples rule.  No other inference is admitted. -/
def derivable (r : Regime) (i : Inst) : Prop :=
  i ∈ r.insts ∨ i.1 ∈ r.rules

instance (r : Regime) (i : Inst) : Decidable (derivable r i) := by
  unfold derivable; infer_instance

/-- A slot is admissible when it is a hole or names an admitted datum. -/
def slotOk (n : Nat) : Option Nat → Prop
  | none => True
  | some x => x < n

instance (n : Nat) (s : Option Nat) : Decidable (slotOk n s) :=
  match s with
  | none => isTrue trivial
  | some x => Nat.decLt x n

/-- Well-formed context relative to a regime: the form is admitted, the
slot count matches the form's arity, at least one slot is a hole (a
context observes; a hole-free slot tuple is an instance, not a context —
matching the Python enumeration), and every filled slot names an admitted
datum. -/
def wfCtx (r : Regime) (c : Ctx) : Prop :=
  c.form < r.forms.length ∧
  c.slots.length = r.forms.getD c.form 0 ∧
  none ∈ c.slots ∧
  ∀ s ∈ c.slots, slotOk r.data s

instance (r : Regime) (c : Ctx) : Decidable (wfCtx r c) := by
  unfold wfCtx; infer_instance

/-- Observational collapse: no well-formed context separates the two data
by positive derivability. -/
def collapsed (r : Regime) (d d' : Nat) : Prop :=
  ∀ c : Ctx, wfCtx r c → (derivable r (plug c d) ↔ derivable r (plug c d'))

/-- Internal separability (the declared sense): some well-formed context
witnesses a difference in positive derivability.  Stated existentially so
that every separability proof carries its witness. -/
def separable (r : Regime) (d d' : Nat) : Prop :=
  ∃ c : Ctx, wfCtx r c ∧
    ¬ (derivable r (plug c d) ↔ derivable r (plug c d'))

/-- Separability contradicts collapse (constructively). -/
theorem separable_not_collapsed {r : Regime} {d d' : Nat}
    (h : separable r d d') : ¬ collapsed r d d' :=
  fun hc => h.elim fun c hc' => hc'.2 (hc c hc'.1)

/-! ## Admission events and replay -/

inductive Event where
  | supply       (token : Nat)
  | admitDatum
  | admitForm    (arity : Nat)
  | admitInst    (form : Nat) (args : List Nat)
  | admitRuleAll (form : Nat)
  | impose       (i j : Nat)
deriving Repr, DecidableEq

/-- One admission step.  `none` signals an ill-formed admission.  A bare
supply provably changes nothing (`supply_no_op`). -/
def stepE (r : Regime) : Event → Option Regime
  | .supply _ => some r
  | .admitDatum => some { r with data := r.data + 1 }
  | .admitForm a =>
      if 1 ≤ a then some { r with forms := r.forms ++ [a] } else none
  | .admitInst f args =>
      if f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
          (∀ x ∈ args, x < r.data) then
        some { r with insts := insertNew r.insts (f, args) }
      else none
  | .admitRuleAll f =>
      if f < r.forms.length then
        some { r with rules := insertNew r.rules f }
      else none
  | .impose i j =>
      if i < j ∧ j < r.data then
        some { r with reqs := insertNew r.reqs (i, j) }
      else none

/-- Replay: fold the recorded history over a base regime.  All-or-nothing:
an ill-formed event poisons the whole history. -/
def replayE (h : List Event) (base : Regime) : Option Regime :=
  h.foldlM stepE base

/-! ## Candidate augmentations (deltas) -/

inductive Item where
  | newDatum
  | newForm    (arity : Nat)
  | newInst    (form : Nat) (args : List Nat)
  | newRuleAll (form : Nat)
deriving Repr, DecidableEq

def applyItem (r : Regime) : Item → Option Regime
  | .newDatum => some { r with data := r.data + 1 }
  | .newForm a =>
      if 1 ≤ a then some { r with forms := r.forms ++ [a] } else none
  | .newInst f args =>
      if f < r.forms.length ∧ args.length = r.forms.getD f 0 ∧
          (∀ x ∈ args, x < r.data) then
        some { r with insts := insertNew r.insts (f, args) }
      else none
  | .newRuleAll f =>
      if f < r.forms.length then
        some { r with rules := insertNew r.rules f }
      else none

def applyDelta (r : Regime) (δ : List Item) : Option Regime :=
  δ.foldlM applyItem r

/-- A valid response to the requirement `Separate (i, j)` on `r`: the delta
applies and the result separates the target while keeping every previously
imposed requirement separated. -/
def validResponse (r : Regime) (i j : Nat) (δ : List Item) : Prop :=
  ∃ s, applyDelta r δ = some s ∧ separable s i j ∧
    ∀ q ∈ r.reqs, separable s q.1 q.2

/-! ## The Challenge 3 regimes

Reading L: only explicit retention admits; two data, no forms, no
instances, the imposed requirement.  Reading F: the initial inscription is
admitted at genesis; three data. -/

def R2L : Regime := ⟨2, [], [], [], [(0, 1)]⟩
def R2F : Regime := ⟨3, [], [], [], [(1, 2)]⟩

theorem R2L_wf : R2L.wf := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> simp [R2L]

theorem R2F_wf : R2F.wf := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> simp [R2F]

end Derivation
