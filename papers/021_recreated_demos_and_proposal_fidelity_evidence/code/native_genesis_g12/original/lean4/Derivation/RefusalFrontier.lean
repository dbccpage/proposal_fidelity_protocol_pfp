import Derivation.Refusal
import Derivation.Bridge
import Derivation.PrimDiff

/-!
# Frontier Run 006: refusal, reflection, and the remaining bridge

Theorem cores T1-T8 of the frontier run.  This module deliberately
imports the refusal disciplines, the bridge, and the primitive-difference
layer: the run studies their intersection.

Distinctions maintained throughout (never conflated): token, occurrence,
presentation event, admission attempt, admission *result*, state
transition, unchanged state, object-language datum, object-language
judgment, retained receipt, metatheoretic trace, carrier element, sort,
relation instance, relation law, classifier.
-/

namespace RefusalFrontier

open Refusal Derivation

/-! ## T1 — Silent-refusal inertia, horizon-free

Under silent deduplication, any history of presentations of
already-present tokens (with supplies and markers) leaves the state
exactly fixed.  No horizon: arbitrary repetition. -/

theorem silent_repetition_inert (h : List REvent) :
    ∀ s : RState,
      (∀ e ∈ h, ∀ tok, e = REvent.admitTok tok → tok ∈ s.data) →
      h.foldl (stepR .silent) s = s := by
  induction h with
  | nil => intro s _; rfl
  | cons e rest ih =>
      intro s hall
      have hstep : stepR .silent s e = s := by
        cases e with
        | supply tok => rfl
        | marker tok => rfl
        | admitTok tok =>
            have hmem := hall _ List.mem_cons_self tok rfl
            simp only [stepR]
            rw [if_pos hmem]
      simp only [List.foldl]
      rw [hstep]
      exact ih s (fun e' he' => hall e' (List.mem_cons_of_mem _ he'))

/-! ## T2 — Trace/object separation

An admission attempt has a host-visible *result* (new admission versus
existing designation).  The traced runner returns results; the state
evolution provably never consumes them, so metatheoretically distinct
traces erase to one object state. -/

inductive AdmResult where
  | isNew | existing
deriving Repr, DecidableEq

def stepTraced (s : RState) : REvent → AdmResult × RState
  | .supply _ => (.existing, s)
  | .marker _ => (.existing, s)
  | .admitTok tok =>
      if tok ∈ s.data then (.existing, s)
      else (.isNew, { s with data := s.data ++ [tok] })

/-- The traced runner's state projection is exactly the silent replay:
results are host data, never object data. -/
theorem trace_erasure (e : REvent) (s : RState) :
    (stepTraced s e).2 = stepR .silent s e := by
  cases e with
  | supply tok => rfl
  | marker tok => rfl
  | admitTok tok =>
      by_cases hmem : tok ∈ s.data
      · simp [stepTraced, stepR, hmem]
      · simp [stepTraced, stepR, hmem]

/-- Two metatheoretically distinct histories (one and two presentations;
different lengths, different result streams) erase to one object
state. -/
theorem histories_collapse :
    replayR .silent [.admitTok 0, .admitTok 0] =
      replayR .silent [.admitTok 0] := by decide

/-! ## T3 — Result-constructor accounting

A retained two-receipt store is modeled by its pair of constructor
codes.  Distinction in the store is *exactly* code inequality: under a
singleton result algebra every retained pair is monochrome, swap-
invariant, and (by the refusal translation) object-collapsed.  The
two-ness of a distinguishing result was imported by the result type. -/

def storeSwap (p : Nat × Nat) : Nat × Nat := (p.2, p.1)

theorem mono_code_swap_invariant (c : Nat) :
    storeSwap (c, c) = (c, c) := rfl

theorem distinct_code_not_swap_invariant {c0 c1 : Nat} (h : c0 ≠ c1) :
    storeSwap (c0, c1) ≠ (c0, c1) := by
  intro he
  exact h (congrArg Prod.snd he)

/-- Singleton algebra forces a monochrome store. -/
theorem singleton_algebra_monochrome (c : Nat) (p : Nat × Nat)
    (h1 : p.1 = c) (h2 : p.2 = c) : p = (c, c) := by
  cases p
  simp_all

/-- The dependency theorem (finite core): a distinguishable retained
pair yields two distinct constructor codes occurring in the store — the
distinction was purchased with the result algebra. -/
theorem distinction_needs_two_constructors (p : Nat × Nat)
    (hsep : p.1 ≠ p.2) :
    ∃ a b, a ≠ b ∧ (a = p.1 ∨ a = p.2) ∧ (b = p.1 ∨ b = p.2) :=
  ⟨p.1, p.2, hsep, Or.inl rfl, Or.inr rfl⟩

/-! ## T4 — Refusal-to-carrier, judgment variant

The R2 protocol admits the refusal as a *judgment*: the carrier provably
never grows; the judgment store does.  A second judgment is not a second
carrier element. -/

structure JState where
  data : List Nat
  judgments : List Nat
deriving Repr, DecidableEq

def stepJ (s : JState) (tok : Nat) : JState :=
  if tok ∈ s.data then { s with judgments := s.judgments ++ [tok] }
  else { s with data := s.data ++ [tok] }

theorem judgment_variant_second_judgment_not_datum :
    let s := stepJ (stepJ (stepJ ⟨[], []⟩ 0) 0) 0
    s.data = [0] ∧ s.judgments = [0, 0] := by decide

/-- Horizon-free carrier bound for the judgment variant. -/
theorem judgment_carrier_bound (h : List Nat) :
    ∀ s : JState, (s.data = [] ∨ s.data = [0]) →
      (∀ tok ∈ h, tok = 0) →
      ((h.foldl stepJ s).data = [] ∨ (h.foldl stepJ s).data = [0]) := by
  induction h with
  | nil => intro s hs _; exact hs
  | cons tok rest ih =>
      intro s hs hall
      have htok : tok = 0 := hall tok List.mem_cons_self
      subst htok
      simp only [List.foldl]
      refine ih _ ?_ (fun t ht => hall t (List.mem_cons_of_mem _ ht))
      by_cases hmem : 0 ∈ s.data
      · simp only [stepJ]
        rw [if_pos hmem]
        exact hs
      · simp only [stepJ]
        rw [if_neg hmem]
        cases hs with
        | inl h0 =>
            right
            show s.data ++ [0] = [0]
            rw [h0]
            rfl
        | inr h1 => exact absurd (by rw [h1]; simp) hmem

/-! ## T5 — priced constructive bridges: a sufficient route and the
unique minimum route

`stepP` is a *sufficient, non-minimum* construction: occurrence-style
reification (the token itself is re-appended) + a tag + an automatic
relation rule.  Its `if` is host-level control flow, not a stored
result constructor — `PState` has no result store, so no binary result
algebra is used or claimed.  Two presentations of one token yield a
witnessed, irreflexive-as-fact, oriented datum.  The irreflexivity
*law* remains a separate declaration (T6).

The *minimum* witnessed route computed by the search — unique under
both declared cost orders — uses strictly less and is verified
separately below (`stepM`). -/

structure PState where
  data : List Nat
  tags : List Nat
  rel : List (Nat × Nat)
deriving Repr, DecidableEq

def stepP (s : PState) (tok : Nat) : PState :=
  if tok ∈ s.data then
    { data := s.data ++ [tok],
      tags := s.tags ++ [s.data.length],
      rel := s.rel ++ [(0, s.data.length)] }
  else { s with data := s.data ++ [tok] }

def bridgeState : PState := stepP (stepP ⟨[], [], []⟩ 0) 0

theorem priced_bridge_closes :
    bridgeState.data.length = 2 ∧
    bridgeState.rel = [(0, 1)] ∧
    (∀ p ∈ bridgeState.rel, p.1 ≠ p.2) ∧
    bridgeState.tags = [1] := by decide

/-- Orientation for free at the act level: the bridge state is not
swap-invariant (the tag and the relation both break the symmetry).  The
choice was made once, in the protocol declaration. -/
def swapP (s : PState) : PState :=
  ⟨s.data,
   s.tags.map (fun i => if i = 0 then 1 else if i = 1 then 0 else i),
   s.rel.map (fun p =>
     ((if p.1 = 0 then 1 else if p.1 = 1 then 0 else p.1),
      (if p.2 = 0 then 1 else if p.2 = 1 then 0 else p.2)))⟩

theorem priced_bridge_oriented : swapP bridgeState ≠ bridgeState := by
  decide

/-! ### The unique minimum witnessed route

The search's minimum protocol for `witnessed_relation` and
`witnessed_irreflexive` is *unique under both declared cost orders*:
datum retention (receipt reification — a coproduct into the carrier)
plus the automatic relation rule, with no tag, no binary result
algebra, no reflection, and one token.  `MItem` is literally that
coproduct (token ⊕ receipt); `MState` has no tag store and no result
store, so this construction cannot use either of the other channels. -/

inductive MItem where
  | tok (n : Nat)
  | receipt (n : Nat)
deriving Repr, DecidableEq

structure MState where
  data : List MItem
  rel : List (Nat × Nat)
deriving Repr, DecidableEq

/-- One-token minimum protocol: a repeated presentation reifies a fresh
receipt and asserts the relation instance from the refused subject
(index 0, the sole token) to the receipt. -/
def stepM (s : MState) (t : Nat) : MState :=
  if MItem.tok t ∈ s.data then
    { data := s.data ++ [MItem.receipt s.data.length],
      rel := s.rel ++ [(0, s.data.length)] }
  else { s with data := s.data ++ [MItem.tok t] }

def minState : MState := stepM (stepM ⟨[], []⟩ 0) 0

/-- The minimum route closes: two presentations of one token yield a
two-element carrier (token and receipt — the coproduct is the second
element's provenance), the witnessed relation `[(0, 1)]`, and only
off-diagonal (irreflexive-as-fact) links — with no tag and no result
store even present in the state. -/
theorem min_witnessed_route_closes :
    minState.data = [MItem.tok 0, MItem.receipt 1] ∧
    minState.rel = [(0, 1)] ∧
    (∀ p ∈ minState.rel, p.1 ≠ p.2) := by decide

/-! ## T6 — Irreflexivity provenance (boundary preserved)

The bridge state has irreflexive *facts* (`priced_bridge_closes`); the
irreflexivity *law* is still never entailed: the fact/law boundary of
the earlier developments carries over verbatim
(`Bridge.irrefl_law_not_entailed`). -/

theorem bridge_facts_not_law :
    ∃ r' : Nat → Nat → Prop,
      (∀ x y, (x, y) ∈ bridgeState.rel → r' x y) ∧
      ¬ PrimDiff.Irrefl r' :=
  ⟨fun _ _ => True, fun _ _ _ => trivial, fun hi => hi 0 trivial⟩

/-! ## T7 — The invariance ceiling, general form

Choice-free (equivariant) constructions land in the invariant
substructure: fully general, one line.  The structural content of each
instance lies in identifying the invariant substructure (done for the
two-element case by `Bridge.equivariant_witness_is_S2`); the bypass used
by tagged refusal is that its states are never fixed points of the
symmetry (`priced_bridge_oriented`). -/

theorem equivariant_output_invariant {S R : Type} (actS : S → S)
    (actR : R → R) (F : S → R)
    (hequiv : ∀ s, F (actS s) = actR (F s)) :
    ∀ s, actS s = s → actR (F s) = F s := by
  intro s hfix
  calc actR (F s) = F (actS s) := (hequiv s).symm
    _ = F s := by rw [hfix]

/-! ## T8 — Reflective dynamics, classified

Three declared reflective semantics realize three of the possible
dynamics; none is inferred from finite depth — the growth statement is
universally quantified. -/

/-- Untyped reflection (a single undifferentiated receipt flag) is
idempotent: a fixed point at depth one. -/
def stepU : Bool → Bool := fun _ => true

theorem untyped_reflect_fixpoint : ∀ s, stepU (stepU s) = stepU s := by
  decide

/-- Replacing retention with a binary toggle realizes a two-cycle. -/
theorem toggle_two_cycle :
    ∀ s : Bool, (!(!s)) = s ∧ (!s) ≠ s := by decide

/-- Subject-typed reflection: presenting the newest receipt refuses and
reifies a new tagged receipt linked to its subject.  One token generates
a chain. -/
def stepRefl (s : PState) : PState :=
  ⟨s.data ++ [s.data.length],
   s.tags ++ [s.data.length],
   s.rel ++ [(s.data.length - 1, s.data.length)]⟩

def reflState : Nat → PState
  | 0 => ⟨[0], [], []⟩
  | n + 1 => stepRefl (reflState n)

/-- Horizon-free growth: after `n` reflections the carrier has exactly
`n + 1` elements.  Growth under an explicitly supplied constructor —
stated for every `n`, not inferred from a finite run. -/
theorem reflective_chain_growth :
    ∀ n, (reflState n).data.length = n + 1 := by
  intro n
  induction n with
  | zero => rfl
  | succ m ih =>
      show (stepRefl (reflState m)).data.length = m + 2
      simp only [stepRefl, List.length_append]
      rw [ih]
      rfl

/-- The carrier of the chain is literally the initial segment of the
numerals: the *declared* reflective semantics realizes a successor
structure.  Realization, not derivation — `stepRefl` itself appends the
current length and inserts the predecessor edge, so the successor shape
is the declaration's content; what the theorem adds is that this holds
horizon-free, for every `n`. -/
theorem reflective_chain_is_initial_segment :
    ∀ n, (reflState n).data = List.range (n + 1) := by
  intro n
  induction n with
  | zero => rfl
  | succ m ih =>
      show (stepRefl (reflState m)).data = List.range (m + 2)
      have hr : List.range (m + 2) = List.range (m + 1) ++ [m + 1] :=
        List.range_succ
      simp only [stepRefl]
      rw [reflective_chain_growth m, ih, hr]

/-- The chain's relation is the successor relation on its carrier: each
reflection links predecessor to successor. -/
theorem reflective_chain_successor_relation :
    ∀ n, (reflState n).rel =
      (List.range n).map (fun k => (k, k + 1)) := by
  intro n
  induction n with
  | zero => rfl
  | succ m ih =>
      show (stepRefl (reflState m)).rel = _
      have hr : List.range (m + 1) = List.range m ++ [m] :=
        List.range_succ
      simp only [stepRefl]
      rw [reflective_chain_growth m, ih, hr, List.map_append]
      simp

/-- Every chain link is off-diagonal: the successor facts are
irreflexive facts (the law, as always, is separate). -/
theorem reflective_chain_irreflexive_facts :
    ∀ n, ∀ p ∈ (reflState n).rel, p.1 ≠ p.2 := by
  intro n p hp
  rw [reflective_chain_successor_relation] at hp
  have ⟨k, _, hk⟩ := List.mem_map.mp hp
  rw [← hk]
  omega

end RefusalFrontier
