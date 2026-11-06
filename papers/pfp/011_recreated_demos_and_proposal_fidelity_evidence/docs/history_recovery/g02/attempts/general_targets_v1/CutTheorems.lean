import CutDefinitions

namespace ResearchPaper011G02
open HigherStructure

def includeCount (xs : List Nat) (a : Nat) : Nat :=
  ((subsetsOf xs).filter (fun s => decide (a ∈ s))).length

def excludeCount (xs : List Nat) (a : Nat) : Nat :=
  ((subsetsOf xs).filter (fun s => !(decide (a ∈ s)))).length

def pairCount (xs : List Nat) (a b : Nat) : Nat :=
  ((subsetsOf xs).filter (fun s => (decide (a ∈ s)) && !(decide (b ∈ s)))).length

theorem subsets_length (xs : List Nat) : (subsetsOf xs).length = 2 ^ xs.length := by
  induction xs with
  | nil => simp [subsetsOf]
  | cons x xs ih => simp [subsetsOf, ih, Nat.pow_succ, Nat.mul_two]

theorem subset_member {x : Nat} {xs s : List Nat}
    (hs : s ∈ subsetsOf xs) (hx : x ∈ s) : x ∈ xs := by
  induction xs generalizing s with
  | nil => simp [subsetsOf] at hs; subst s; simp at hx
  | cons y ys ih =>
    simp only [subsetsOf, List.mem_append, List.mem_map] at hs
    rcases hs with hs | ⟨t, ht, rfl⟩
    · exact List.mem_cons_of_mem y (ih hs hx)
    · rcases List.mem_cons.mp hx with hx | hx
      · subst x; simp
      · exact List.mem_cons_of_mem y (ih ht hx)

theorem include_absent {xs : List Nat} {a : Nat} (ha : a ∉ xs) :
    includeCount xs a = 0 := by
  unfold includeCount
  have empty : (subsetsOf xs).filter (fun s => decide (a ∈ s)) = [] := by
    apply List.filter_eq_nil_iff.mpr
    intro s hs
    have absent : a ∉ s := fun h => ha (subset_member hs h)
    simp [absent]
  rw [empty]
  rfl

theorem exclude_absent {xs : List Nat} {a : Nat} (ha : a ∉ xs) :
    excludeCount xs a = 2 ^ xs.length := by
  unfold excludeCount
  have full : (subsetsOf xs).filter (fun s => !(decide (a ∈ s))) = subsetsOf xs := by
    apply List.filter_eq_self.mpr
    intro s hs
    have absent : a ∉ s := fun h => ha (subset_member hs h)
    simp [absent]
  rw [full, subsets_length]

theorem include_cons_head (x : Nat) (xs : List Nat) :
    includeCount (x :: xs) x = includeCount xs x + (subsetsOf xs).length := by
  simp [includeCount, subsetsOf, List.filter_map, Function.comp_def]

theorem include_cons_other {a x : Nat} (xs : List Nat) (ha : a ≠ x) :
    includeCount (x :: xs) a = includeCount xs a + includeCount xs a := by
  simp [includeCount, subsetsOf, List.filter_map, Function.comp_def, ha]

theorem exclude_cons_head (x : Nat) (xs : List Nat) :
    excludeCount (x :: xs) x = excludeCount xs x := by
  simp [excludeCount, subsetsOf, List.filter_map, Function.comp_def]

theorem exclude_cons_other {a x : Nat} (xs : List Nat) (ha : a ≠ x) :
    excludeCount (x :: xs) a = excludeCount xs a + excludeCount xs a := by
  simp [excludeCount, subsetsOf, List.filter_map, Function.comp_def, ha]

theorem include_present {xs : List Nat} {a : Nat} (hn : xs.Nodup) (ha : a ∈ xs) :
    includeCount xs a = 2 ^ (xs.length - 1) := by
  induction xs with
  | nil => simp at ha
  | cons x xs ih =>
    obtain ⟨hx, htail⟩ := List.nodup_cons.mp hn
    by_cases hax : a = x
    · subst a
      rw [include_cons_head, include_absent hx, subsets_length]
      simp
    · have hat : a ∈ xs := by simpa [hax] using ha
      rw [include_cons_other xs hax, ih htail hat, ← Nat.mul_two, ← Nat.pow_succ]
      congr 1
      have positive := List.length_pos_of_mem hat
      simp only [List.length_cons]
      omega

theorem exclude_present {xs : List Nat} {a : Nat} (hn : xs.Nodup) (ha : a ∈ xs) :
    excludeCount xs a = 2 ^ (xs.length - 1) := by
  induction xs with
  | nil => simp at ha
  | cons x xs ih =>
    obtain ⟨hx, htail⟩ := List.nodup_cons.mp hn
    by_cases hax : a = x
    · subst a
      rw [exclude_cons_head, exclude_absent hx]
      simp
    · have hat : a ∈ xs := by simpa [hax] using ha
      rw [exclude_cons_other xs hax, ih htail hat, ← Nat.mul_two, ← Nat.pow_succ]
      congr 1
      have positive := List.length_pos_of_mem hat
      simp only [List.length_cons]
      omega

theorem pair_absent {xs : List Nat} {a b : Nat} (ha : a ∉ xs) :
    pairCount xs a b = 0 := by
  unfold pairCount
  have empty : (subsetsOf xs).filter
      (fun s => (decide (a ∈ s)) && !(decide (b ∈ s))) = [] := by
    apply List.filter_eq_nil_iff.mpr
    intro s hs
    have absent : a ∉ s := fun h => ha (subset_member hs h)
    simp [absent]
  rw [empty]
  rfl

theorem pair_excluded_absent {xs : List Nat} {a b : Nat} (hb : b ∉ xs) :
    pairCount xs a b = includeCount xs a := by
  unfold pairCount includeCount
  congr 1
  apply List.filter_congr
  intro s hs
  have absent : b ∉ s := fun h => hb (subset_member hs h)
  simp [absent]

theorem pair_cons_first {a b : Nat} (xs : List Nat) (hb : b ≠ a) :
    pairCount (a :: xs) a b = pairCount xs a b + excludeCount xs b := by
  simp [pairCount, excludeCount, subsetsOf, List.filter_map, Function.comp_def, hb]

theorem pair_cons_second {a b : Nat} (xs : List Nat) (ha : a ≠ b) :
    pairCount (b :: xs) a b = pairCount xs a b := by
  simp [pairCount, subsetsOf, List.filter_map, Function.comp_def, ha]

theorem pair_cons_other {a b x : Nat} (xs : List Nat) (ha : a ≠ x) (hb : b ≠ x) :
    pairCount (x :: xs) a b = pairCount xs a b + pairCount xs a b := by
  simp [pairCount, subsetsOf, List.filter_map, Function.comp_def, ha, hb]

theorem pair_present {xs : List Nat} {a b : Nat}
    (hn : xs.Nodup) (ha : a ∈ xs) (hb : b ∈ xs) (hab : a ≠ b) :
    pairCount xs a b = 2 ^ (xs.length - 2) := by
  induction xs with
  | nil => simp at ha
  | cons x xs ih =>
    obtain ⟨hx, htail⟩ := List.nodup_cons.mp hn
    by_cases hax : a = x
    · subst a
      have hbx : b ≠ x := Ne.symm hab
      have hbt : b ∈ xs := by simpa [hbx] using hb
      rw [pair_cons_first xs hbx, pair_absent hx, exclude_present htail hbt]
      simp
    · have hat : a ∈ xs := by simpa [hax] using ha
      by_cases hbx : b = x
      · subst b
        rw [pair_cons_second xs hax, pair_excluded_absent hx, include_present htail hat]
        simp
      · have hbt : b ∈ xs := by simpa [hbx] using hb
        have two : 2 ≤ xs.length := by
          by_cases h : 2 ≤ xs.length
          · exact h
          · have positive := List.length_pos_of_mem hat
            have singleton : xs.length = 1 := by omega
            obtain ⟨c, rfl⟩ := List.length_eq_one.mp singleton
            simp only [List.mem_singleton] at hat hbt
            exact (hab (hat.trans hbt.symm)).elim
        rw [pair_cons_other xs hax hbx, ih htail hat hbt, ← Nat.mul_two, ← Nat.pow_succ]
        congr 1
        simp only [List.length_cons]
        omega

theorem C3 (n a b : Nat) (ha : a < n) (hb : b < n) (hab : a ≠ b) :
    cutCensus n a b = 2 ^ (n - 2) := by
  exact pair_present List.nodup_range (List.mem_range.mpr ha) (List.mem_range.mpr hb) hab

theorem C2 (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := by
  apply C3 <;> omega

theorem C1 : cutCensus 5 0 1 = 8 ∧ cutCensus 6 0 1 = 16 ∧
    cutCensus 7 0 1 = 32 ∧ cutCensus 8 0 1 = 64 := by decide

theorem equal_pair (n a : Nat) : cutCensus n a a = 0 := by
  simp [cutCensus]

theorem first_outside (n a b : Nat) (ha : n ≤ a) : cutCensus n a b = 0 := by
  apply pair_absent
  simp only [List.mem_range]
  omega

theorem second_outside (n a b : Nat) (ha : a < n) (hb : n ≤ b) :
    cutCensus n a b = 2 ^ (n - 1) := by
  change pairCount (List.range n) a b = _
  rw [pair_excluded_absent (by simp only [List.mem_range]; omega)]
  exact include_present List.nodup_range (List.mem_range.mpr ha)

theorem zero_carrier (a b : Nat) : cutCensus 0 a b = 0 := by
  apply first_outside
  omega

theorem one_carrier : cutCensus 1 0 0 = 0 ∧ cutCensus 1 0 1 = 1 ∧
    cutCensus 1 1 0 = 0 := by decide

theorem C3_at_nine : cutCensus 9 0 1 = 128 := by
  have h := C3 9 0 1 (by decide) (by decide) (by decide)
  exact h

theorem C3_at_ten : cutCensus 10 0 1 = 256 := by
  have h := C3 10 0 1 (by decide) (by decide) (by decide)
  exact h

theorem relabel_pair : cutCensus 9 3 1 = 128 := by
  exact C3 9 3 1 (by decide) (by decide) (by decide)

theorem poison_equal_pair : cutCensus 3 0 0 ≠ 2 ^ (3 - 2) := by decide

theorem poison_no_lower_bound : cutCensus 0 0 1 ≠ 2 ^ (0 - 2) := by decide

end ResearchPaper011G02
