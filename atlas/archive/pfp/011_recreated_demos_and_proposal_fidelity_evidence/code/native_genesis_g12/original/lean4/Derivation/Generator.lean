import Derivation.RefusalFrontier

/-!
# F5: the composite generator — reflective growth + pair-separation closure

The question (F5 of the frontier run): is the composite of the declared
reflective refusal semantics (`RefusalFrontier.stepRefl`) and the
pair-separation closure policy a *self-sustaining* challenge generator —
and is the full obstruction-*repair* cycle self-sustaining, or does
every repair strategy in a declared class either import per repair, act
vacuously, or end generation?

This module proves the horizon-free halves.  The observation regime is
the depth-1 profile used by the frontier search (tag bit + incident
edge patterns), reproduced here structurally; deeper regimes and the
bounded trajectories live in `code/derivation/generator.py`.

Distinctions maintained: carrier element vs. its index (the index is
metatheoretic bookkeeping; observation sees only tags and incident
edges); presence of an observable vs. its *value*; a declared rule
(one-time import) vs. its per-round outputs; obstruction (a pair the
regime cannot separate) vs. collision.
-/

namespace Generator

open RefusalFrontier

/-! ## The chain's tag store

Companion to `reflective_chain_is_initial_segment` and
`reflective_chain_successor_relation`: the tag store is exactly the
non-zero initial segment — every receipt is tagged, the seed is not. -/

theorem reflective_chain_tags :
    ∀ n, (reflState n).tags = (List.range n).map (· + 1) := by
  intro n
  induction n with
  | zero => rfl
  | succ m ih =>
      show (stepRefl (reflState m)).tags = _
      have hr : List.range (m + 1) = List.range m ++ [m] :=
        List.range_succ
      simp only [stepRefl]
      rw [reflective_chain_growth m, ih, hr, List.map_append]
      simp

/-! ## The depth-1 observation regime

`profile1 s i` is what depth-1 observation sees of carrier element `i`:
its tag bit, whether some relation instance points at it, and whether
some relation instance leaves it.  This mirrors the frontier search's
per-element profile; element indices themselves are *not* observable. -/

def profile1 (s : PState) (i : Nat) : Bool × Bool × Bool :=
  (decide (i ∈ s.tags),
   decide (∃ p ∈ s.rel, p.2 = i),
   decide (∃ p ∈ s.rel, p.1 = i))

theorem chain_tagged_iff (n i : Nat) :
    i ∈ (reflState n).tags ↔ (1 ≤ i ∧ i ≤ n) := by
  rw [reflective_chain_tags]
  simp only [List.mem_map, List.mem_range]
  constructor
  · rintro ⟨k, hk, rfl⟩
    exact ⟨by omega, by omega⟩
  · intro ⟨h1, h2⟩
    exact ⟨i - 1, by omega, by omega⟩

theorem chain_hasIn_iff (n i : Nat) :
    (∃ p ∈ (reflState n).rel, p.2 = i) ↔ (1 ≤ i ∧ i ≤ n) := by
  rw [reflective_chain_successor_relation]
  simp only [List.mem_map, List.mem_range]
  constructor
  · rintro ⟨p, ⟨k, hk, rfl⟩, h2⟩
    have hki : k + 1 = i := h2
    exact ⟨by omega, by omega⟩
  · intro ⟨h1, h2⟩
    refine ⟨(i - 1, i), ⟨i - 1, by omega, ?_⟩, rfl⟩
    rw [Nat.sub_add_cancel h1]

theorem chain_hasOut_iff (n i : Nat) :
    (∃ p ∈ (reflState n).rel, p.1 = i) ↔ i < n := by
  rw [reflective_chain_successor_relation]
  simp only [List.mem_map, List.mem_range]
  constructor
  · rintro ⟨p, ⟨k, hk, rfl⟩, h1⟩
    have hki : k = i := h1
    omega
  · intro h
    exact ⟨(i, i + 1), ⟨i, h, rfl⟩, rfl⟩

/-! ## The three profile classes of the chain -/

/-- Every interior element looks the same to depth-1 observation:
tagged, entered, left. -/
theorem middle_profile (n i : Nat) (h1 : 1 ≤ i) (h2 : i < n) :
    profile1 (reflState n) i = (true, true, true) := by
  have ht := (chain_tagged_iff n i).mpr ⟨h1, by omega⟩
  have hin := (chain_hasIn_iff n i).mpr ⟨h1, by omega⟩
  have hout := (chain_hasOut_iff n i).mpr h2
  simp only [profile1, decide_eq_true ht, decide_eq_true hin,
             decide_eq_true hout]

theorem endpoint0_profile (n : Nat) (h : 1 ≤ n) :
    profile1 (reflState n) 0 = (false, false, true) := by
  have ht : ¬ (0 ∈ (reflState n).tags) := by
    rw [chain_tagged_iff]; omega
  have hin : ¬ (∃ p ∈ (reflState n).rel, p.2 = 0) := by
    rw [chain_hasIn_iff]; omega
  have hout := (chain_hasOut_iff n 0).mpr (by omega)
  simp only [profile1, decide_eq_false ht, decide_eq_false hin,
             decide_eq_true hout]

theorem endpointN_profile (n : Nat) (h : 1 ≤ n) :
    profile1 (reflState n) n = (true, true, false) := by
  have ht := (chain_tagged_iff n n).mpr ⟨h, Nat.le_refl n⟩
  have hin := (chain_hasIn_iff n n).mpr ⟨h, Nat.le_refl n⟩
  have hout : ¬ (∃ p ∈ (reflState n).rel, p.1 = n) := fun hex =>
    absurd ((chain_hasOut_iff n n).mp hex) (Nat.lt_irrefl n)
  simp only [profile1, decide_eq_true ht, decide_eq_true hin,
             decide_eq_false hout]

/-! ## The obstruction set, identified exactly

Under the pair-separation closure policy an *obstruction* is an
unordered pair of distinct carrier elements the observation regime
cannot separate.  At depth 1 the chain's obstructions are exactly the
interior pairs — no judgment call, an iff. -/

theorem depth1_obstructions_are_exactly_middle_pairs
    (n i j : Nat) (hn : 1 ≤ n) (hi : i ≤ n) (hj : j ≤ n) (hne : i ≠ j) :
    (profile1 (reflState n) i = profile1 (reflState n) j) ↔
      (1 ≤ i ∧ i < n ∧ 1 ≤ j ∧ j < n) := by
  constructor
  · intro heq
    have tri : ∀ m : Nat, m ≤ n → m = 0 ∨ m = n ∨ (1 ≤ m ∧ m < n) := by
      intro m hm
      rcases Nat.eq_zero_or_pos m with h0 | h1
      · exact Or.inl h0
      · rcases Nat.lt_or_ge m n with hlt | hge
        · exact Or.inr (Or.inr ⟨h1, hlt⟩)
        · exact Or.inr (Or.inl (Nat.le_antisymm hm hge))
    have hI := tri i hi
    have hJ := tri j hj
    rcases hI with hi0 | hiN | hiM
    · rcases hJ with hj0 | hjN | hjM
      · exact absurd (by omega) hne
      · rw [hi0, hjN, endpoint0_profile n hn,
            endpointN_profile n hn] at heq
        exact absurd heq (by decide)
      · rw [hi0, endpoint0_profile n hn,
            middle_profile n j hjM.1 hjM.2] at heq
        exact absurd heq (by decide)
    · rcases hJ with hj0 | hjN | hjM
      · rw [hiN, hj0, endpointN_profile n hn,
            endpoint0_profile n hn] at heq
        exact absurd heq (by decide)
      · exact absurd (by omega) hne
      · rw [hiN, endpointN_profile n hn,
            middle_profile n j hjM.1 hjM.2] at heq
        exact absurd heq (by decide)
    · rcases hJ with hj0 | hjN | hjM
      · rw [hj0, middle_profile n i hiM.1 hiM.2,
            endpoint0_profile n hn] at heq
        exact absurd heq (by decide)
      · rw [hjN, middle_profile n i hiM.1 hiM.2,
            endpointN_profile n hn] at heq
        exact absurd heq (by decide)
      · exact ⟨hiM.1, hiM.2, hjM.1, hjM.2⟩
  · intro ⟨h1, h2, h3, h4⟩
    rw [middle_profile n i h1 h2, middle_profile n j h3 h4]

/-! ## Endogenous generation, horizon-free

The composite fires at every round from the third on: elements 1 and 2
are distinct carrier elements with identical depth-1 profiles, and the
only event consumed is the internally enabled reflection.  This is the
*generation* half of F5, proved — the first horizon-free challenge
generator exhibited in the development, with no per-round external
act.  No minimality or uniqueness claim is made. -/

theorem generation_never_dries (n : Nat) (h : 3 ≤ n) :
    (1 : Nat) ≠ 2 ∧
      profile1 (reflState n) 1 = profile1 (reflState n) 2 := by
  refine ⟨by omega, ?_⟩
  rw [middle_profile n 1 (by omega) (by omega),
      middle_profile n 2 (by omega) (by omega)]

/-! ## Repair strategies, horizon-free halves

The bounded trajectories over the declared strategy class live in
Python; here are the statements that no finite horizon could carry. -/

/-- Presence marking is vacuous as a repair.  The chain *already*
implements automark-as-presence — every reflective admission tags its
receipt — and the interior still collapses observationally. -/
theorem automark_presence_vacuous (n : Nat) (h : 3 ≤ n) :
    (∀ i, 1 ≤ i → i ≤ n → i ∈ (reflState n).tags) ∧
      profile1 (reflState n) 1 = profile1 (reflState n) 2 :=
  ⟨fun i h1 h2 => (chain_tagged_iff n i).mpr ⟨h1, h2⟩,
   (generation_never_dries n h).2⟩

theorem le_foldr_max (marks : List Nat) :
    ∀ x ∈ marks, x ≤ marks.foldr max 0 := by
  induction marks with
  | nil => intro x hx; cases hx
  | cons a rest ih =>
      intro x hx
      rcases List.mem_cons.mp hx with rfl | hmem
      · simp only [List.foldr]
        omega
      · have := ih x hmem
        simp only [List.foldr]
        omega

/-- Any finite marking is outrun: beyond the largest marked index the
chain grows fresh interior pairs with equal profiles, so a per-pair
repair strategy is called again — and again, each call consuming a
fresh import.  Repair by per-pair marking never becomes endogenous. -/
theorem finite_marks_outrun (marks : List Nat) :
    ∃ n i j, 1 ≤ i ∧ i < n ∧ 1 ≤ j ∧ j < n ∧ i ≠ j ∧
      i ∉ marks ∧ j ∉ marks ∧
      profile1 (reflState n) i = profile1 (reflState n) j := by
  refine ⟨marks.foldr max 0 + 3, marks.foldr max 0 + 1,
          marks.foldr max 0 + 2,
          by omega, by omega, by omega, by omega, by omega, ?_, ?_, ?_⟩
  · intro hmem
    have := le_foldr_max marks _ hmem
    omega
  · intro hmem
    have := le_foldr_max marks _ hmem
    omega
  · rw [middle_profile _ _ (by omega) (by omega),
        middle_profile _ _ (by omega) (by omega)]

/-- Valued marks collapse generation.  If the observation regime reads
the mark *value* — here the element's own index, i.e. presentation
identity made observable — every pair separates and no obstruction ever
arises: the generator dies of success.  The price is an unbounded
observable alphabet (one distinguishable value per element),
identity-grade observation rather than a finite declaration. -/
def profileV (s : PState) (i : Nat) : (Bool × Bool × Bool) × Nat :=
  (profile1 s i, i)

theorem valued_marks_collapse_generation (n i j : Nat) (h : i ≠ j) :
    profileV (reflState n) i ≠ profileV (reflState n) j := by
  intro he
  exact h (congrArg Prod.snd he)

/-! ## The ceiling at work is expressiveness, not symmetry

The direct transposition of interior elements 1 and 2 does not preserve
the successor relation: it sends the edge (0, 1) to (0, 2), which is not
an edge.  This theorem separates the present example from the earlier
swap-symmetric witness, but it does not quantify over all automorphisms
or prove full rigidity of the directed chain. -/

def swap12 (k : Nat) : Nat := if k = 1 then 2 else if k = 2 then 1 else k

theorem middle_swap_not_relation_preserving (n : Nat) (h : 2 ≤ n) :
    (0, 1) ∈ (reflState n).rel ∧
      ((swap12 0, swap12 1) ∉ (reflState n).rel) := by
  constructor
  · rw [reflective_chain_successor_relation]
    exact List.mem_map.mpr ⟨0, List.mem_range.mpr (by omega), rfl⟩
  · rw [reflective_chain_successor_relation]
    intro hmem
    have ⟨k, _, hk⟩ := List.mem_map.mp hmem
    simp [swap12, Prod.mk.injEq] at hk
    omega

/-! ## Depth-2 observation: repairs near the ends, outrun in the deep
interior (decidable instances; the general depth-d statement is a
declared open conjecture) -/

def profile2 (s : PState) (i : Nat) :
    (Bool × Bool × Bool) × List (Bool × Bool × Bool) ×
      List (Bool × Bool × Bool) :=
  (profile1 s i,
   (s.rel.filter (fun p => decide (p.2 = i))).map (fun p => profile1 s p.1),
   (s.rel.filter (fun p => decide (p.1 = i))).map (fun p => profile1 s p.2))

/-- Depth 2 separates the pair (1, 3) that depth 1 could not: their
neighbours' profiles differ.  Raising the regime is a genuine local
repair. -/
theorem depth2_separates_near_ends_n4 :
    profile2 (reflState 4) 1 ≠ profile2 (reflState 4) 3 := by decide

/-- Depth 2 is outrun at length 5: the deep-interior pair (2, 3) has
equal depth-2 profiles.  The all-depth generalization remains open. -/
theorem depth2_obstruction_n5 :
    profile2 (reflState 5) 2 = profile2 (reflState 5) 3 ∧
      (2 : Nat) ≠ 3 := by decide

end Generator
