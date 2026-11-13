import Derivation.Basic

/-!
# Token-erasure simulation

The Python model keeps presentation tokens and dedups datum admission on
token identity; the Lean `Regime` erases tokens to a count.  This module
makes the bridge exact: a token-aware state `TRegime` with deduplicating
admission (`stepT`), the erasure map, and a simulation theorem — one
token-aware step corresponds to one erased step, where a duplicate
admission erases to a bare supply (a provable no-op).  Consequently the
Lean development is a sound abstraction of the token-aware model, not a
claim of literal mirroring.
-/

namespace Derivation

/-- Token-aware admitted state: data are a list of presentation tokens
(as opaque numbers) in admission order. -/
structure TRegime where
  tokens : List Nat
  forms  : List Nat
  insts  : List Inst
  rules  : List Nat
  reqs   : List (Nat × Nat)
deriving Repr, DecidableEq

/-- Token-aware events: datum admission carries its token. -/
inductive TEvent where
  | supply       (token : Nat)
  | admitDatum   (token : Nat)
  | admitForm    (arity : Nat)
  | admitInst    (form : Nat) (args : List Nat)
  | admitRuleAll (form : Nat)
  | impose       (i j : Nat)
deriving Repr, DecidableEq

/-- Token-aware step with deduplicating admission (the Python semantics):
re-admitting a present token designates the existing datum. -/
def stepT (t : TRegime) : TEvent → Option TRegime
  | .supply _ => some t
  | .admitDatum tok =>
      if tok ∈ t.tokens then some t
      else some { t with tokens := t.tokens ++ [tok] }
  | .admitForm a =>
      if 1 ≤ a then some { t with forms := t.forms ++ [a] } else none
  | .admitInst f args =>
      if f < t.forms.length ∧ args.length = t.forms.getD f 0 ∧
          (∀ x ∈ args, x < t.tokens.length) then
        some { t with insts := insertNew t.insts (f, args) }
      else none
  | .admitRuleAll f =>
      if f < t.forms.length then
        some { t with rules := insertNew t.rules f }
      else none
  | .impose i j =>
      if i < j ∧ j < t.tokens.length then
        some { t with reqs := insertNew t.reqs (i, j) }
      else none

/-- Erasure: forget tokens, keep the count. -/
def TRegime.erase (t : TRegime) : Regime :=
  ⟨t.tokens.length, t.forms, t.insts, t.rules, t.reqs⟩

/-- Event erasure, relative to the current token-aware state: a duplicate
admission erases to a bare supply (which `supply_no_op` shows is a no-op);
everything else erases structurally. -/
def eraseEvent (t : TRegime) : TEvent → Event
  | .supply tok => .supply tok
  | .admitDatum tok =>
      if tok ∈ t.tokens then .supply tok else .admitDatum
  | .admitForm a => .admitForm a
  | .admitInst f args => .admitInst f args
  | .admitRuleAll f => .admitRuleAll f
  | .impose i j => .impose i j

/-- One-step simulation: token-aware stepping followed by erasure equals
erased stepping of the erased event. -/
theorem erase_step (t : TRegime) (e : TEvent) :
    (stepT t e).map TRegime.erase =
      stepE t.erase (eraseEvent t e) := by
  cases e with
  | supply tok => rfl
  | admitDatum tok =>
      by_cases h : tok ∈ t.tokens
      · simp [stepT, eraseEvent, h, stepE]
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
  | admitForm a =>
      by_cases h : 1 ≤ a
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
      · simp [stepT, eraseEvent, h, stepE]
  | admitInst f args =>
      by_cases h : f < t.forms.length ∧ args.length = t.forms.getD f 0 ∧
          (∀ x ∈ args, x < t.tokens.length)
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
  | admitRuleAll f =>
      by_cases h : f < t.forms.length
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
  | impose i j =>
      by_cases h : i < j ∧ j < t.tokens.length
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]
      · simp [stepT, eraseEvent, h, stepE, TRegime.erase]

/-- Token-aware replay. -/
def replayT (h : List TEvent) (base : TRegime) : Option TRegime :=
  h.foldlM stepT base

/-- Erase a whole token-aware history, threading the state so each
duplicate admission becomes a supply.  On an ill-formed step the
continuation is irrelevant (both replays are poisoned), so it is cut. -/
def eraseHistory (t : TRegime) : List TEvent → List Event
  | [] => []
  | e :: rest =>
      eraseEvent t e ::
        (match stepT t e with
         | some t1 => eraseHistory t1 rest
         | none => [])

theorem replayT_cons (e : TEvent) (rest : List TEvent) (base : TRegime) :
    replayT (e :: rest) base =
      (stepT base e).bind (fun t1 => replayT rest t1) := by
  unfold replayT
  cases hs : stepT base e <;> simp [List.foldlM, hs]

theorem replayE_cons (e : Event) (rest : List Event) (base : Regime) :
    replayE (e :: rest) base =
      (stepE base e).bind (fun r1 => replayE rest r1) := by
  unfold replayE
  cases hs : stepE base e <;> simp [List.foldlM, hs]

/-- History-level simulation: replaying a token-aware history with
deduplicating admission and then erasing tokens equals replaying the
erased history in the token-erased model.  The Lean development is
therefore a sound abstraction of the token-aware (Python) admission
semantics. -/
theorem erase_replay (h : List TEvent) (base : TRegime) :
    (replayT h base).map TRegime.erase =
      replayE (eraseHistory base h) base.erase := by
  induction h generalizing base with
  | nil => rfl
  | cons e rest ih =>
      have hstep := erase_step base e
      rw [replayT_cons]
      cases hs : stepT base e with
      | none =>
          rw [hs] at hstep
          have hE : eraseHistory base (e :: rest) = [eraseEvent base e] := by
            simp [eraseHistory, hs]
          rw [hE, replayE_cons, ← hstep]
          simp
      | some t1 =>
          rw [hs] at hstep
          have hE : eraseHistory base (e :: rest) =
              eraseEvent base e :: eraseHistory t1 rest := by
            simp [eraseHistory, hs]
          rw [hE, replayE_cons, ← hstep]
          simpa using ih t1

end Derivation
