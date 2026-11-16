/-!
# Remaining finite claim closure for ATL-P012 through ATL-P021

AuthorityEffect: None.

Core Lean `v4.35.0` text (zero Mathlib, zero declared axioms, zero `sorryAx`)
for the finite statements whose proposed derivations are discharged below.
Each theorem is the statement named in its section. A later section does not
extend an earlier one to a larger class of graphs, languages, or tasks.

What this file supports: the kernel-checked statements printed at the bottom.
What it does not support: stochastic model behaviour, a live campaign, a
physical or fault-tolerance reading, or any archive row left out of this file.
Narrowest claim: each named theorem holds for the types written in it.
Negative control: `no_forward_cover`, `unchecked_extension`,
`false_green_not_coboundary`, and `no_decreasing_cycle` are refusals.
-/

namespace PFP.RemainingClaimClosure

/-! ## ATL-P014-002. A sound backward map with no forward map -/

def backwardCover : Empty → Fin 1 := fun e => nomatch e

theorem no_forward_cover (f : Fin 1 → Empty) : False := nomatch (f 0)

theorem soundness_without_coverage :
    (∃ backward : Empty → Fin 1, ∀ e, backward e = backwardCover e) ∧
      ((Fin 1 → Empty) → False) :=
  ⟨⟨backwardCover, fun e => nomatch e⟩, no_forward_cover⟩

/-! ## ATL-P012-010. Partial maps that preserve an observation, composed -/

def agrees {α β : Type} (qPrev qNext : α → β) (f : α → Option α) : Prop :=
  ∀ x y, f x = some y → qNext y = qPrev x

structure Step (α β : Type) where
  map : α → Option α
  before : α → β
  after : α → β
  agree : agrees before after map

def glued {α β : Type} : List (Step α β) → Prop
  | [] => True
  | [_] => True
  | s1 :: s2 :: rest => s1.after = s2.before ∧ glued (s2 :: rest)

def execSteps {α β : Type} : List (Step α β) → α → Option α
  | [], x => some x
  | s :: ss, x =>
    match s.map x with
    | none => none
    | some y => execSteps ss y

theorem composite_preserves
    {α β : Type} (s : Step α β) (ss : List (Step α β))
    (hglue : glued (s :: ss)) {x y : α}
    (hx : execSteps (s :: ss) x = some y) :
    ((s :: ss).getLast (by simp)).after y = s.before x := by
  induction ss generalizing s x with
  | nil =>
    simp [execSteps] at hx
    cases hm : s.map x with
    | none => simp [hm] at hx
    | some z =>
      simp [hm] at hx
      have hagree : s.after z = s.before x := s.agree x z hm
      cases hx
      simpa [List.getLast_singleton] using hagree
  | cons s2 rest ih =>
    simp [execSteps] at hx
    cases hm : s.map x with
    | none => simp [hm] at hx
    | some z =>
      simp [hm] at hx
      have hagree : s.after z = s.before x := s.agree x z hm
      have hjoin : s.after = s2.before := by
        simp [glued] at hglue
        exact hglue.1
      have hglue2 : glued (s2 :: rest) := by
        simp [glued] at hglue
        exact hglue.2
      have ih' := ih s2 hglue2 hx
      simp [List.getLast_cons_cons] at ih' ⊢
      rw [ih']
      rw [← hjoin]
      exact hagree

/-! ## ATL-P012-011. Terminal status under the four stated hypotheses -/

structure TerminalHyp where
  boundTask : Prop
  checkerAccept : Prop
  validReply : Prop
  checkerSound : checkerAccept → validReply
  prerequisitesDone : Prop
  authorityState : Prop

theorem terminal_sound (h : TerminalHyp)
    (hb : h.boundTask) (hc : h.checkerAccept)
    (hp : h.prerequisitesDone) (ha : h.authorityState) :
    h.boundTask ∧ h.checkerAccept ∧ h.validReply ∧ h.prerequisitesDone ∧ h.authorityState :=
  ⟨hb, hc, h.checkerSound hc, hp, ha⟩

/-! ## ATL-P013-001. An admitted receipt yields the conjunction -/

theorem receipt_conjunction
    {ι : Type} (J : List ι) (accept : ι → Bool) (R : ι → Prop)
    (hsound : ∀ j, accept j = true → R j)
    (hadmit : ∀ j ∈ J, accept j = true) :
    ∀ j ∈ J, R j :=
  fun j hj => hsound j (hadmit j hj)

/-! ## ATL-P013-002. A receipt for J does not yield an outside predicate -/

theorem unchecked_extension :
    ∃ R : Fin 2 → Prop, ∃ J : List (Fin 2), ∃ k : Fin 2,
      (∀ j ∈ J, R j) ∧ k ∉ J ∧ ¬ R k := by
  refine ⟨fun i => i = 0, [0], 1, ?_, ?_, ?_⟩
  · intro j hj
    simp at hj
    subst hj
    rfl
  · simp
  · simp

/-! ## ATL-P013-003. The same witness bytes and two different sources -/

def spanIn (src span : List Nat) : Bool := src == span

theorem unbound_quotation :
    ∃ witness srcA srcB span : List Nat,
      witness = span ∧ spanIn srcA span = true ∧ spanIn srcB span = false := by
  refine ⟨[1], [1], [2], [1], rfl, ?_⟩
  decide

/-! ## ATL-P014-001. Sections compose, and a positive cost bounds the count -/

def compAll {α : Type} : List (α → α) → α → α
  | [] => id
  | g :: gs => g ∘ compAll gs

theorem compAll_snoc {α : Type} (gs : List (α → α)) (g : α → α) :
    ∀ x, compAll (gs ++ [g]) x = compAll gs (g x) := by
  induction gs with
  | nil => intro x; rfl
  | cons h t ih =>
    intro x
    simp [compAll, ih]

theorem sections_compose
    {α : Type} (pairs : List ((α → α) × (α → α)))
    (hsec : ∀ p ∈ pairs, ∀ x, p.1 (p.2 x) = x) :
    ∀ x, compAll (pairs.map Prod.fst) (compAll (pairs.map Prod.snd).reverse x) = x := by
  induction pairs with
  | nil => intro x; rfl
  | cons p ps ih =>
    intro x
    have hp : ∀ x, p.1 (p.2 x) = x := hsec p (by simp)
    have hps : ∀ q ∈ ps, ∀ x, q.1 (q.2 x) = x := by
      intro q hq x
      exact hsec q (by simp [hq]) x
    have ihx := ih hps (p.2 x)
    simp [compAll, List.reverse_cons, compAll_snoc, ihx, hp]

theorem op_budget (k δ B : Nat) (hδ : 0 < δ) (hk : k * δ ≤ B) : k ≤ B / δ :=
  (Nat.le_div_iff_mul_le hδ).2 hk

/-! ## ATL-P017-001. Acceptance does not mention the channel -/

theorem channel_independent
    {P W C : Type} (accept : P → W → Bool) (valid : P → W → Prop)
    (_channel : C)
    (hsound : ∀ p w, accept p w = true → valid p w) :
    ∀ p w, accept p w = true → valid p w :=
  hsound

/-! ## ATL-P017-003. Non-faithful leaf lists are a two-sided ideal -/

structure Leaf where
  stored : List Nat
  slice : List Nat
deriving DecidableEq

def leafOk (leaf : Leaf) : Bool := leaf.stored == leaf.slice

def faithful (tree : List Leaf) : Bool := tree.all leafOk

theorem faithful_append (a b : List Leaf) :
    faithful (a ++ b) = (faithful a && faithful b) := by
  simp [faithful, List.all_append]

theorem nonfaithful_left (a b : List Leaf) (h : faithful a = false) :
    faithful (a ++ b) = false := by
  simp [faithful_append, h]

theorem nonfaithful_right (a b : List Leaf) (h : faithful b = false) :
    faithful (a ++ b) = false := by
  simp [faithful_append, h]

def quotientTree (tree : List Leaf) : Option (List Leaf) :=
  if faithful tree then some tree else none

theorem quotient_nonzero_iff (tree : List Leaf) :
    (quotientTree tree).isSome = faithful tree := by
  cases h : faithful tree <;> simp [quotientTree, h]

/-! ## ATL-P017-004. Exact viable-prefix frontier -/

def viable {α : Type} (L : List α → Prop) (p : List α) : Prop :=
  ∃ s, L (p ++ s)

theorem frontier_nonempty
    {α : Type} {L : List α → Prop} {p : List α}
    (h : viable L p) (hnot : ¬ L p) :
    ∃ t : α, viable L (p ++ [t]) := by
  rcases h with ⟨s, hs⟩
  cases s with
  | nil =>
    exact False.elim (hnot (by simpa using hs))
  | cons t rest =>
    exact ⟨t, rest, by simpa using hs⟩

inductive Masked {α : Type} (L : List α → Prop) : List α → Prop where
  | nil : viable L [] → Masked L []
  | cons : Masked L p → viable L (p ++ [t]) → Masked L (p ++ [t])

theorem masked_prefixes_viable
    {α : Type} {L : List α → Prop} {p : List α}
    (h : Masked L p) : viable L p := by
  induction h with
  | nil hv => exact hv
  | cons _ hv _ => exact hv

/-! ## ATL-P017-002. Directed-cycle L1 lower bound and a dual witness -/

def cycleSum : List Int → Int
  | [] => 0
  | z :: zs => z + cycleSum zs

def l1 : List Int → Nat
  | [] => 0
  | z :: zs => z.natAbs + l1 zs

theorem natAbs_sum_le_l1 (r : List Int) : (cycleSum r).natAbs ≤ l1 r := by
  induction r with
  | nil => simp [cycleSum, l1]
  | cons z zs ih =>
    simp only [cycleSum, l1]
    exact Nat.le_trans (Int.natAbs_add_le z (cycleSum zs)) (Nat.add_le_add_left ih _)

theorem l1_attained (s : Int) :
    ∃ r : List Int, cycleSum r = s ∧ l1 r = s.natAbs := by
  refine ⟨[s], ?_, ?_⟩
  · simp [cycleSum]
  · simp [l1]

def signOf (s : Int) : Int := if s < 0 then -1 else 1

theorem dual_pair (s : Int) : signOf s * s = ↑s.natAbs := by
  unfold signOf
  by_cases h : s < 0
  · simp [h, Int.neg_mul, Int.one_mul]
    exact (Int.ofNat_natAbs_of_nonpos (Int.le_of_lt h)).symm
  · simp [h, Int.one_mul]
    exact (Int.natAbs_of_nonneg ((Int.not_lt).mp h)).symm

/-! ## ATL-P017-005. Exact rational identity behind 1-(1-p)^n -/

theorem pow_sub_le (a b n : Nat) (h : a ≤ b) : (b - a) ^ n ≤ b ^ n := by
  have _kept : a ≤ b := h
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Nat.pow_succ, Nat.pow_succ]
    exact Nat.mul_le_mul ih (Nat.sub_le b a)

theorem admit_split (a b n : Nat) (h : a ≤ b) :
    (b ^ n - (b - a) ^ n) + (b - a) ^ n = b ^ n :=
  Nat.sub_add_cancel (pow_sub_le a b n h)

/-! ## ATL-P017-006. Omitting the cycle sum leaves s ≠ 0 -/

def isCoboundary (c : List Int) : Prop := cycleSum c = 0

theorem false_green_not_coboundary (c : List Int) (h : cycleSum c ≠ 0) :
    ¬ isCoboundary c :=
  h

theorem family_indexed_by_sum (s : Int) :
    ∃ c : List Int, cycleSum c = s ∧ (isCoboundary c ↔ s = 0) := by
  refine ⟨[s], by simp [cycleSum], by simp [isCoboundary, cycleSum]⟩

/-! ## ATL-P017-008. Staged arity arithmetic on the five named graphs -/

theorem max_le_staged (tree chords : Nat) : max tree chords ≤ tree + 2 * chords := by
  refine (Nat.max_le).2 ⟨Nat.le_add_right _ _, ?_⟩
  calc
    chords = chords * 1 := by rw [Nat.mul_one]
    _ ≤ chords * 2 := Nat.mul_le_mul_left _ (by decide : 1 ≤ 2)
    _ = 2 * chords := by rw [Nat.mul_comm]
    _ ≤ tree + 2 * chords := Nat.le_add_left _ _

theorem arity_examples :
    (5 + 8 = 13 ∧ max 5 4 = 5) ∧
    (7 + 10 = 17 ∧ max 7 5 = 7) ∧
    (4 + 12 = 16 ∧ max 4 6 = 6) ∧
    (9 + 12 = 21 ∧ max 9 6 = 9) ∧
    (7 + 14 = 21 ∧ max 7 7 = 7) := by
  decide

theorem two_stage_zero (t c : Nat) : (t + c) - t - c = 0 := by
  omega

/-! ## ATL-P017-007. Chord order makes the support matrix the identity -/

def chordEntry (cycle chord : Fin b1) : Nat :=
  if cycle = chord then 1 else 0

theorem chord_entry_diag (i : Fin b1) : chordEntry i i = 1 := by
  simp [chordEntry]

theorem chord_entry_off (i j : Fin b1) (h : i ≠ j) : chordEntry i j = 0 := by
  simp [chordEntry, h]

/-! ## ATL-P021-006. Strictly earlier targets admit no return walk -/

def linked : List (Nat × Nat) → Prop
  | [] => True
  | [_] => True
  | a :: b :: rest => a.2 = b.1 ∧ linked (b :: rest)

theorem chain_decreases
    (edges : List (Nat × Nat))
    (hdec : ∀ e ∈ edges, e.2 < e.1)
    (chain : List (Nat × Nat))
    (hc : ∀ e ∈ chain, e ∈ edges)
    (hlink : linked chain) :
    ∀ hne : chain ≠ [], (chain.getLast hne).2 < (chain.head hne).1 := by
  induction chain with
  | nil =>
    intro hne
    exact (hne rfl).elim
  | cons a rest ih =>
    intro hne
    cases rest with
    | nil =>
      have ha : a.2 < a.1 := hdec a (hc a (by simp))
      simpa [List.getLast_singleton, List.head_cons] using ha
    | cons b rest2 =>
      have ha : a.2 < a.1 := hdec a (hc a (by simp))
      have hjoin : a.2 = b.1 := by
        simp [linked] at hlink
        exact hlink.1
      have hlink2 : linked (b :: rest2) := by
        simp [linked] at hlink
        exact hlink.2
      have hc2 : ∀ e ∈ b :: rest2, e ∈ edges := by
        intro e he
        exact hc e (by simp [he])
      have ih' := ih hc2 hlink2 (by simp)
      simp [List.getLast_cons_cons, List.head_cons] at ih' ⊢
      omega

theorem no_decreasing_cycle
    (edges : List (Nat × Nat))
    (hdec : ∀ e ∈ edges, e.2 < e.1)
    (chain : List (Nat × Nat))
    (hc : ∀ e ∈ chain, e ∈ edges)
    (hlink : linked chain)
    (hne : chain ≠ [])
    (hback : (chain.getLast hne).2 = (chain.head hne).1) :
    False := by
  have hlt := chain_decreases edges hdec chain hc hlink hne
  omega

/-! ## ATL-P017-009. Path spanning tree, then chord values -/

theorem cycleSum_append (a b : List Int) : cycleSum (a ++ b) = cycleSum a + cycleSum b := by
  induction a with
  | nil => simp [cycleSum]
  | cons z zs ih =>
    simp [cycleSum, ih, Int.add_assoc]

/-- Potential at vertex `i` on a path: the sum of the first `i` tree-edge values. -/
def pot (cs : List Int) (i : Nat) : Int := cycleSum (cs.take i)

theorem pot_step (cs : List Int) (i : Nat) (hi : i < cs.length) :
    pot cs (i + 1) - pot cs i = cs.get ⟨i, hi⟩ := by
  unfold pot
  rw [List.take_succ_eq_append_getElem hi]
  rw [cycleSum_append]
  simp [cycleSum]
  omega

def holonomy (tree : List Int) (i j : Nat) (chord : Int) : Int :=
  chord - (pot tree j - pot tree i)

theorem holonomy_zero_iff (tree : List Int) (i j : Nat) (chord : Int) :
    holonomy tree i j chord = 0 ↔ chord = pot tree j - pot tree i := by
  simp [holonomy]
  constructor <;> intro h <;> omega

#print axioms soundness_without_coverage
#print axioms composite_preserves
#print axioms terminal_sound
#print axioms receipt_conjunction
#print axioms unchecked_extension
#print axioms unbound_quotation
#print axioms sections_compose
#print axioms op_budget
#print axioms channel_independent
#print axioms faithful_append
#print axioms nonfaithful_left
#print axioms nonfaithful_right
#print axioms quotient_nonzero_iff
#print axioms frontier_nonempty
#print axioms masked_prefixes_viable
#print axioms natAbs_sum_le_l1
#print axioms l1_attained
#print axioms dual_pair
#print axioms admit_split
#print axioms false_green_not_coboundary
#print axioms family_indexed_by_sum
#print axioms max_le_staged
#print axioms arity_examples
#print axioms two_stage_zero
#print axioms chord_entry_diag
#print axioms chord_entry_off
#print axioms chain_decreases
#print axioms no_decreasing_cycle
#print axioms pot_step
#print axioms holonomy_zero_iff

end PFP.RemainingClaimClosure
