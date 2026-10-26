/-
Copyright 2026 Jeremy H. Carroll.
Released under the PolyForm Noncommercial License 1.0.0; see LICENSE-CODE.
Author: Jeremy H. Carroll
-/

import Lean

set_option linter.unusedSectionVars false

namespace SymbolGame.Topology

/-!
# Point-Set and General Topology: 50 Benchmark Theorems
Self-contained Lean 4 formalization of general topology without external Mathlib dependencies.
Used as the held-out benchmark for multi-step interactive proof generation with the Symbol Game host governor.
-/

def Set (α : Type) := α → Prop

namespace Set

variable {α β : Type}

def mem (x : α) (s : Set α) : Prop := s x
infix:50 " ∈ " => Set.mem

def subset (s t : Set α) : Prop := ∀ ⦃x : α⦄, x ∈ s → x ∈ t
infix:50 " ⊆ " => Set.subset

def univ : Set α := fun _ => True
def empty : Set α := fun _ => False

def inter (s t : Set α) : Set α := fun x => x ∈ s ∧ x ∈ t
infixl:70 " ∩ " => Set.inter

def union (s t : Set α) : Set α := fun x => x ∈ s ∨ x ∈ t
infixl:65 " ∪ " => Set.union

def compl (s : Set α) : Set α := fun x => ¬(x ∈ s)
postfix:100 "ᶜ" => Set.compl

def diff (s t : Set α) : Set α := fun x => x ∈ s ∧ ¬(x ∈ t)
infixl:70 " \\ " => Set.diff

def preimage (f : α → β) (t : Set β) : Set α := fun x => t (f x)

def sUnion (S : Set (Set α)) : Set α := fun x => ∃ s, S s ∧ s x
def sInter (S : Set (Set α)) : Set α := fun x => ∀ s, S s → s x

@[ext]
theorem ext {s t : Set α} (h : ∀ x, x ∈ s ↔ x ∈ t) : s = t := funext fun x => propext (h x)

theorem subset_refl (s : Set α) : s ⊆ s := fun _ h => h

theorem subset_trans {s t u : Set α} (h1 : s ⊆ t) (h2 : t ⊆ u) : s ⊆ u :=
  fun _ hx => h2 (h1 hx)

theorem inter_subset_left (s t : Set α) : s ∩ t ⊆ s := fun _ h => h.1
theorem inter_subset_right (s t : Set α) : s ∩ t ⊆ t := fun _ h => h.2

theorem subset_union_left (s t : Set α) : s ⊆ s ∪ t := fun _ h => Or.inl h
theorem subset_union_right (s t : Set α) : t ⊆ s ∪ t := fun _ h => Or.inr h

theorem compl_compl (s : Set α) : (sᶜ)ᶜ = s := by
  ext x; constructor
  · intro h; by_cases hx : x ∈ s; exact hx; exact False.elim (h hx)
  · intro hx h; exact h hx

theorem compl_empty : (empty : Set α)ᶜ = univ := by
  ext x; constructor
  · intro _; trivial
  · intro _ h; contradiction

theorem compl_univ : (univ : Set α)ᶜ = empty := by
  ext x; constructor
  · intro h; exact h trivial
  · intro h; contradiction

end Set

open Set

class TopologicalSpace (α : Type) where
  isOpen : Set α → Prop
  isOpen_univ : isOpen univ
  isOpen_empty : isOpen empty
  isOpen_inter : ∀ s t, isOpen s → isOpen t → isOpen (s ∩ t)
  isOpen_sUnion : ∀ S : Set (Set α), (∀ s, S s → isOpen s) → isOpen (sUnion S)

variable {α β γ : Type} [tα : TopologicalSpace α] [tβ : TopologicalSpace β] [tγ : TopologicalSpace γ]

def isOpen (s : Set α) : Prop := tα.isOpen s
def isClosed (s : Set α) : Prop := isOpen (sᶜ)

def interior (s : Set α) : Set α := sUnion (fun t => isOpen t ∧ t ⊆ s)
def closure (s : Set α) : Set α := sInter (fun t => isClosed t ∧ s ⊆ t)
def frontier (s : Set α) : Set α := closure s \ interior s

def Continuous (f : α → β) : Prop := ∀ s, isOpen s → isOpen (preimage f s)

structure Homeomorphism (α β : Type) [TopologicalSpace α] [TopologicalSpace β] where
  toFun : α → β
  invFun : β → α
  left_inv : ∀ x, invFun (toFun x) = x
  right_inv : ∀ y, toFun (invFun y) = y
  continuous_toFun : Continuous toFun
  continuous_invFun : Continuous invFun

def IsHomeomorphic (α β : Type) [TopologicalSpace α] [TopologicalSpace β] : Prop :=
  Nonempty (Homeomorphism α β)

def IsHausdorff (α : Type) [TopologicalSpace α] : Prop :=
  ∀ x y : α, x ≠ y → ∃ u v : Set α, isOpen u ∧ isOpen v ∧ x ∈ u ∧ y ∈ v ∧ u ∩ v = empty

def IsDense (s : Set α) : Prop := ∀ x, x ∈ closure s

def IsConnected (α : Type) [TopologicalSpace α] : Prop :=
  ∀ u v : Set α, isOpen u → isOpen v → u ∪ v = univ → u ∩ v = empty → (u = univ ∨ v = univ)

-- ==============================================================================
-- THE 50 BENCHMARK THEOREMS
-- ==============================================================================

-- Theorem 1: univ is open
theorem thm_01_isOpen_univ : isOpen (univ : Set α) := tα.isOpen_univ

-- Theorem 2: empty is open
theorem thm_02_isOpen_empty : isOpen (empty : Set α) := tα.isOpen_empty

-- Theorem 3: empty is closed
theorem thm_03_isClosed_empty : isClosed (empty : Set α) := by
  dsimp [isClosed]; rw [compl_empty]; exact tα.isOpen_univ

-- Theorem 4: univ is closed
theorem thm_04_isClosed_univ : isClosed (univ : Set α) := by
  dsimp [isClosed]; rw [compl_univ]; exact tα.isOpen_empty

-- Theorem 5: Union of closed sets is closed (finite)
theorem thm_05_isClosed_union (s t : Set α) (hs : isClosed s) (ht : isClosed t) : isClosed (s ∪ t) := by
  dsimp [isClosed] at *
  have h : (s ∪ t)ᶜ = sᶜ ∩ tᶜ := by
    ext x; constructor
    · intro hx; constructor; intro hsx; exact hx (Or.inl hsx); intro htx; exact hx (Or.inr htx)
    · intro hx hst; cases hst with
      | inl hsx => exact hx.1 hsx
      | inr htx => exact hx.2 htx
  rw [h]; exact tα.isOpen_inter (sᶜ) (tᶜ) hs ht

-- Theorem 6: Union of open sets is open
theorem thm_06_isOpen_union (s t : Set α) (hs : isOpen s) (ht : isOpen t) : isOpen (s ∪ t) := by
  have h : s ∪ t = sUnion (fun u => u = s ∨ u = t) := by
    ext x; constructor
    · intro hx; cases hx with
      | inl hsx => exact ⟨s, Or.inl rfl, hsx⟩
      | inr htx => exact ⟨t, Or.inr rfl, htx⟩
    · intro ⟨u, hu, hx⟩; cases hu with
      | inl hus => rw [hus] at hx; exact Or.inl hx
      | inr hut => rw [hut] at hx; exact Or.inr hx
  rw [h]; apply tα.isOpen_sUnion; intro u hu; cases hu with
  | inl hus => rw [hus]; exact hs
  | inr hut => rw [hut]; exact ht

-- Theorem 7: interior is a subset
theorem thm_07_interior_subset (s : Set α) : interior s ⊆ s := by
  intro x hx; dsimp [interior, sUnion] at hx
  rcases hx with ⟨t, ⟨_, hts⟩, hxt⟩
  exact hts hxt

-- Theorem 8: subset of closure
theorem thm_08_subset_closure (s : Set α) : s ⊆ closure s := by
  intro x hx; dsimp [closure, sInter]
  intro t ⟨_, hst⟩; exact hst hx

-- Theorem 9: interior of open set is itself
theorem thm_09_interior_of_isOpen {s : Set α} (h : isOpen s) : interior s = s := by
  ext x; constructor
  · exact fun hx => thm_07_interior_subset s hx
  · intro hx; dsimp [interior, sUnion]; exact ⟨s, ⟨h, Set.subset_refl s⟩, hx⟩

-- Theorem 10: closure of closed set is itself
theorem thm_10_closure_of_isClosed {s : Set α} (h : isClosed s) : closure s = s := by
  ext x; constructor
  · intro hx; dsimp [closure, sInter] at hx; exact hx s ⟨h, Set.subset_refl s⟩
  · exact fun hx => thm_08_subset_closure s hx

-- Theorem 11: interior is maximal open subset
theorem thm_11_interior_maximal {s t : Set α} (ht : isOpen t) (hts : t ⊆ s) : t ⊆ interior s := by
  intro x hx; dsimp [interior, sUnion]; exact ⟨t, ⟨ht, hts⟩, hx⟩

-- Theorem 12: closure is minimal closed superset
theorem thm_12_closure_minimal {s t : Set α} (ht : isClosed t) (hst : s ⊆ t) : closure s ⊆ t := by
  intro x hx; dsimp [closure, sInter] at hx; exact hx t ⟨ht, hst⟩

-- Theorem 13: interior idempotence
theorem thm_13_interior_interior (s : Set α) : interior (interior s) = interior s := by
  ext x; constructor
  · intro hx; exact thm_07_interior_subset (interior s) hx
  · intro hx; dsimp [interior, sUnion] at hx; rcases hx with ⟨t, ⟨ht, hts⟩, hxt⟩
    have ht_int : t ⊆ interior s := thm_11_interior_maximal ht hts
    exact thm_11_interior_maximal ht ht_int hxt

-- Theorem 14: closure idempotence
theorem thm_14_closure_closure (s : Set α) : closure (closure s) = closure s := by
  ext x; constructor
  · intro hx; dsimp [closure, sInter] at hx
    intro t ⟨ht, hst⟩
    have hcl : closure s ⊆ t := thm_12_closure_minimal ht hst
    exact hx t ⟨ht, hcl⟩
  · intro hx; exact thm_08_subset_closure (closure s) hx

-- Theorem 15: interior monotonicity
theorem thm_15_interior_mono {s t : Set α} (h : s ⊆ t) : interior s ⊆ interior t := by
  intro x hx; dsimp [interior, sUnion] at *; rcases hx with ⟨u, ⟨hu, hus⟩, hxu⟩
  exact ⟨u, ⟨hu, Set.subset_trans hus h⟩, hxu⟩

-- Theorem 16: closure monotonicity
theorem thm_16_closure_mono {s t : Set α} (h : s ⊆ t) : closure s ⊆ closure t := by
  intro x hx; dsimp [closure, sInter] at *; intro u ⟨hu, htu⟩
  exact hx u ⟨hu, Set.subset_trans h htu⟩

-- Theorem 17: frontier definition equivalence
theorem thm_17_frontier_eq_diff (s : Set α) : frontier s = closure s \ interior s := rfl

-- Theorem 18: frontier subset of closure
theorem thm_18_frontier_subset_closure (s : Set α) : frontier s ⊆ closure s := by
  intro _ hx; exact hx.1

-- Theorem 19: frontier disjoint from interior
theorem thm_19_frontier_inter_interior_empty (s : Set α) : frontier s ∩ interior s = empty := by
  ext x; constructor
  · intro ⟨h1, h2⟩; exact h1.2 h2
  · intro h; contradiction

-- Theorem 20: open set disjoint from its boundary
theorem thm_20_isOpen_frontier_disjoint (s : Set α) (h : isOpen s) : s ∩ frontier s = empty := by
  ext x; constructor
  · intro ⟨hsx, hfront⟩
    have hint : x ∈ interior s := by rw [thm_09_interior_of_isOpen h]; exact hsx
    exact hfront.2 hint
  · intro h; contradiction

-- Theorem 21: closed set contains its frontier
theorem thm_21_isClosed_frontier_subset (s : Set α) (h : isClosed s) : frontier s ⊆ s := by
  intro x hx
  have hcl : x ∈ closure s := hx.1
  rw [thm_10_closure_of_isClosed h] at hcl
  exact hcl

-- Theorem 22: identity map is continuous
theorem thm_22_continuous_id : Continuous (@id α) := by
  intro s hs; exact hs

-- Theorem 23: composition of continuous maps is continuous
theorem thm_23_continuous_comp {f : α → β} {g : β → γ}
    (hf : Continuous f) (hg : Continuous g) : Continuous (g ∘ f) := by
  intro s hs; exact hf (preimage g s) (hg s hs)

-- Theorem 24: constant function is continuous
theorem thm_24_continuous_const (b : β) : Continuous (fun _ : α => b) := by
  intro s hs
  by_cases hb : b ∈ s
  · have h : preimage (fun _ : α => b) s = univ := by
      ext x; constructor
      · intro _; trivial
      · intro _; exact hb
    rw [h]; exact tα.isOpen_univ
  · have h : preimage (fun _ : α => b) s = empty := by
      ext x; constructor
      · intro hx; exact hb hx
      · intro hx; contradiction
    rw [h]; exact tα.isOpen_empty

-- Theorem 25: continuous map preserves closed preimages
theorem thm_25_continuous_closed_preimage (f : α → β) (hf : Continuous f) (s : Set β) (hs : isClosed s) :
    isClosed (preimage f s) := by
  dsimp [isClosed] at *
  have h : (preimage f s)ᶜ = preimage f (sᶜ) := rfl
  rw [h]; exact hf (sᶜ) hs

-- Theorem 26: closure of union contains union of closures
theorem thm_26_closure_union_left (s t : Set α) : closure s ⊆ closure (s ∪ t) :=
  thm_16_closure_mono (Set.subset_union_left s t)

-- Theorem 27: closure of union right
theorem thm_27_closure_union_right (s t : Set α) : closure t ⊆ closure (s ∪ t) :=
  thm_16_closure_mono (Set.subset_union_right s t)

-- Theorem 28: interior of intersection subset left
theorem thm_28_interior_inter_left (s t : Set α) : interior (s ∩ t) ⊆ interior s :=
  thm_15_interior_mono (Set.inter_subset_left s t)

-- Theorem 29: interior of intersection subset right
theorem thm_29_interior_inter_right (s t : Set α) : interior (s ∩ t) ⊆ interior t :=
  thm_15_interior_mono (Set.inter_subset_right s t)

-- Theorem 30: dense set closure is univ
theorem thm_30_dense_closure_univ {s : Set α} (h : IsDense s) : closure s = univ := by
  ext x; constructor
  · intro _; trivial
  · intro _; exact h x

-- Theorem 31: univ is dense
theorem thm_31_univ_isDense : IsDense (univ : Set α) := by
  intro x; exact thm_08_subset_closure univ trivial

-- Theorem 32: empty set closure is empty
theorem thm_32_closure_empty : closure (empty : Set α) = empty :=
  thm_10_closure_of_isClosed thm_03_isClosed_empty

-- Theorem 33: empty set interior is empty
theorem thm_33_interior_empty : interior (empty : Set α) = empty :=
  thm_09_interior_of_isOpen thm_02_isOpen_empty

-- Theorem 34: univ interior is univ
theorem thm_34_interior_univ : interior (univ : Set α) = univ :=
  thm_09_interior_of_isOpen thm_01_isOpen_univ

-- Theorem 35: univ closure is univ
theorem thm_35_closure_univ : closure (univ : Set α) = univ :=
  thm_10_closure_of_isClosed thm_04_isClosed_univ

-- Theorem 36: frontier of empty is empty
theorem thm_36_frontier_empty : frontier (empty : Set α) = empty := by
  dsimp [frontier]; rw [thm_32_closure_empty]
  ext x; constructor; intro h; exact h.1; intro h; contradiction

-- Theorem 37: frontier of univ is empty
theorem thm_37_frontier_univ : frontier (univ : Set α) = empty := by
  dsimp [frontier]; rw [thm_35_closure_univ, thm_34_interior_univ]
  ext x; constructor
  · intro h; exact h.2 trivial
  · intro h; contradiction

-- Theorem 38: Homeomorphism reflexivity
theorem thm_38_isHomeo_refl (α : Type) [TopologicalSpace α] : IsHomeomorphic α α :=
  ⟨⟨id, id, fun _ => rfl, fun _ => rfl, thm_22_continuous_id, thm_22_continuous_id⟩⟩

-- Theorem 39: Homeomorphism symmetry
theorem thm_39_isHomeo_symm (h : IsHomeomorphic α β) : IsHomeomorphic β α := by
  rcases h with ⟨⟨toFun, invFun, left_inv, right_inv, c_to, c_inv⟩⟩
  exact ⟨⟨invFun, toFun, right_inv, left_inv, c_inv, c_to⟩⟩

-- Theorem 40: Homeomorphism transitivity
theorem thm_40_isHomeo_trans (h1 : IsHomeomorphic α β) (h2 : IsHomeomorphic β γ) :
    IsHomeomorphic α γ := by
  rcases h1 with ⟨⟨f1, g1, l1, r1, cf1, cg1⟩⟩
  rcases h2 with ⟨⟨f2, g2, l2, r2, cf2, cg2⟩⟩
  refine ⟨⟨f2 ∘ f1, g1 ∘ g2, ?_, ?_, ?_, ?_⟩⟩
  · intro x; dsimp; rw [l2, l1]
  · intro z; dsimp; rw [r1, r2]
  · exact thm_23_continuous_comp cf1 cf2
  · exact thm_23_continuous_comp cg2 cg1

-- Theorem 41: Preimage under identity is identity
theorem thm_41_preimage_id (s : Set α) : preimage (@id α) s = s := rfl

-- Theorem 42: Preimage under composition
theorem thm_42_preimage_comp (f : α → β) (g : β → γ) (s : Set γ) :
    preimage (g ∘ f) s = preimage f (preimage g s) := rfl

-- Theorem 43: Hausdorff points are distinct has disjoint neighborhoods
theorem thm_43_hausdorff_disjoint_nbds (hH : IsHausdorff α) {x y : α} (hne : x ≠ y) :
    ∃ u v : Set α, isOpen u ∧ isOpen v ∧ x ∈ u ∧ y ∈ v ∧ u ∩ v = empty :=
  hH x y hne

-- Theorem 44: Connected space clopen set either empty or univ
theorem thm_44_connected_clopen (hC : IsConnected α) (s : Set α) (ho : isOpen s) (hc : isClosed s) :
    s = empty ∨ s = univ := by
  have huniv : s ∪ sᶜ = univ := by ext x; constructor; intro _; trivial; intro _; by_cases hx : x ∈ s; exact Or.inl hx; exact Or.inr hx
  have hinter : s ∩ sᶜ = empty := by ext x; constructor; intro ⟨h1, h2⟩; exact h2 h1; intro h; contradiction
  have hor := hC s (sᶜ) ho hc huniv hinter
  cases hor with
  | inl hs => exact Or.inr hs
  | inr hsc =>
    have hsempty : s = empty := by
      ext x; constructor
      · intro hx; have hxsc : x ∈ sᶜ := by rw [hsc]; trivial
        exact False.elim (hxsc hx)
      · intro h; contradiction
    exact Or.inl hsempty

-- Theorem 45: Subset boundary inclusion into union of closures
theorem thm_45_closure_subset_union (s t : Set α) : closure s ∪ closure t ⊆ closure (s ∪ t) := by
  intro x hx; cases hx with
  | inl hs => exact thm_26_closure_union_left s t hs
  | inr ht => exact thm_27_closure_union_right s t ht

-- Theorem 46: Interior of intersection subset of intersection of interiors
theorem thm_46_interior_inter_subset (s t : Set α) :
    interior (s ∩ t) ⊆ interior s ∩ interior t := by
  intro x hx; constructor
  · exact thm_28_interior_inter_left s t hx
  · exact thm_29_interior_inter_right s t hx

-- Theorem 47: Preimage of intersection is intersection of preimages
theorem thm_47_preimage_inter (f : α → β) (s t : Set β) :
    preimage f (s ∩ t) = preimage f s ∩ preimage f t := rfl

-- Theorem 48: Preimage of union is union of preimages
theorem thm_48_preimage_union (f : α → β) (s t : Set β) :
    preimage f (s ∪ t) = preimage f s ∪ preimage f t := rfl

-- Theorem 49: Preimage of complement is complement of preimage
theorem thm_49_preimage_compl (f : α → β) (s : Set β) :
    preimage f (sᶜ) = (preimage f s)ᶜ := rfl

-- Theorem 50: Frontier of closed set is contained in the set
theorem thm_50_frontier_closed_subset (s : Set α) (h : isClosed s) : frontier s ⊆ s :=
  thm_21_isClosed_frontier_subset s h

end SymbolGame.Topology
