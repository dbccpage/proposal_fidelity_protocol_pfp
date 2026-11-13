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

end ResearchPaper011G02
