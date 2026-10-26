import Derivation.MinimalityF

namespace ResearchG01
open Derivation

def state (xs : List Nat) : Regime :=
  ⟨3, [xs.length], [(0, xs)], [], [(1, 2)]⟩

def delta (xs : List Nat) : List Item :=
  [.newForm xs.length, .newInst 0 xs]

def markF (k : Nat) : Regime :=
  ⟨3, [k], [(0, List.replicate k 1)], [], [(1, 2)]⟩

def deltaF (k : Nat) : List Item :=
  [.newForm k, .newInst 0 (List.replicate k 1)]

theorem deltaF_applies (k : Nat) (hk : 1 ≤ k) :
    applyDelta R2F (deltaF k) = some (markF k) := by
  rw [show deltaF k = [Item.newForm k, Item.newInst 0 (List.replicate k 1)] from rfl]
  rw [applyDelta_pair]
  have h1 : applyItem R2F (.newForm k) = some ⟨3, [k], [], [], [(1, 2)]⟩ := by
    simp only [applyItem]
    rw [if_pos hk]
    rfl
  rw [h1]
  show applyItem ⟨3, [k], [], [], [(1, 2)]⟩
    (.newInst 0 (List.replicate k 1)) = some (markF k)
  simp only [applyItem]
  rw [if_pos]
  · rfl
  · refine ⟨by simp, by simp, ?_⟩
    intro x hx
    have hx1 : x = 1 := List.eq_of_mem_replicate hx
    subst hx1
    omega

theorem markF_separable (k : Nat) (hk : 1 ≤ k) :
    separable (markF k) 1 2 := by
  refine ⟨⟨0, List.replicate k none⟩,
    ⟨by simp [markF], by simp [markF],
     List.mem_replicate.mpr ⟨by omega, rfl⟩, ?_⟩, ?_⟩
  · intro s hs
    have : s = none := List.eq_of_mem_replicate hs
    rw [this]
    trivial
  · intro hiff
    have hone : derivable (markF k) (plug ⟨0, List.replicate k none⟩ 1) := by
      simp [derivable, plug, markF, List.map_replicate]
    have htwo := hiff.mp hone
    simp only [derivable, plug, markF, List.map_replicate] at htwo
    cases htwo with
    | inr h => cases h
    | inl h =>
      cases k with
      | zero => omega
      | succ n => simp [List.replicate] at h

theorem deltaF_valid (k : Nat) (hk : 1 ≤ k) :
    validResponse R2F 1 2 (deltaF k) := by
  refine ⟨markF k, deltaF_applies k hk, markF_separable k hk, ?_⟩
  intro q hq
  have : q = (1, 2) := by simpa [R2F] using hq
  rw [this]
  exact markF_separable k hk

theorem markF_pairwise_noniso (j k : Nat) (hjk : j ≠ k)
    (iso : Iso (markF j) (markF k)) : False := by
  have hlt := iso.fmap_lt 0 (by simp [markF])
  have ha := iso.arity 0 (by simp [markF])
  have h0 : iso.fmap 0 = 0 := by
    simp [markF] at hlt
    omega
  rw [h0] at ha
  simp [markF] at ha
  exact hjk ha.symm

theorem F_K :
    (∀ k, 1 ≤ k → validResponse R2F 1 2 (deltaF k) ∧
      (deltaF k).length = 2 ∧ applyDelta R2F (deltaF k) = some (markF k)) ∧
    (∀ j k, j ≠ k → Iso (markF j) (markF k) → False) := by
  refine ⟨?_, markF_pairwise_noniso⟩
  intro k hk
  exact ⟨deltaF_valid k hk, rfl, deltaF_applies k hk⟩

theorem F_1 :
    validResponse R2F 1 2 (deltaF 1) ∧ validResponse R2F 1 2 (deltaF 2) ∧
    (deltaF 1).length = 2 ∧ (deltaF 2).length = 2 ∧
    (∀ δ, δ.length ≤ 1 → ¬ validResponse R2F 1 2 δ) ∧
    applyDelta R2F (deltaF 1) = some (markF 1) ∧
    applyDelta R2F (deltaF 2) = some (markF 2) ∧
    (Iso (markF 1) (markF 2) → False) :=
  ⟨deltaF_valid 1 (by decide), deltaF_valid 2 (by decide), rfl, rfl,
   cost1_insufficient_F, deltaF_applies 1 (by decide), deltaF_applies 2 (by decide),
   markF_pairwise_noniso 1 2 (by decide)⟩

def boundedArgs (i : Nat) : List Nat :=
  match i with
  | 0 => [1]
  | 1 => [1, 1]
  | 2 => [1, 2]
  | 3 => [0, 1]
  | _ => [1, 0]

theorem fixed_valid (xs : List Nat) (c : Ctx)
    (happly : applyDelta R2F (delta xs) = some (state xs))
    (hctx : wfCtx (state xs) c)
    (hsep : ¬ (derivable (state xs) (plug c 1) ↔ derivable (state xs) (plug c 2))) :
    validResponse R2F 1 2 (delta xs) := by
  refine ⟨state xs, happly, ⟨c, hctx, hsep⟩, ?_⟩
  intro q hq
  have : q = (1, 2) := by simpa [R2F] using hq
  rw [this]
  exact ⟨c, hctx, hsep⟩

theorem bounded_valid (i : Nat) (hi : i < 5) :
    validResponse R2F 1 2 (delta (boundedArgs i)) := by
  have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
  rcases cases with h | h | h | h | h <;> subst i
  · exact fixed_valid [1] ⟨0, [none]⟩ (by decide) (by decide) (by decide)
  · exact fixed_valid [1, 1] ⟨0, [none, none]⟩ (by decide) (by decide) (by decide)
  · exact fixed_valid [1, 2] ⟨0, [none, some 2]⟩ (by decide) (by decide) (by decide)
  · exact fixed_valid [0, 1] ⟨0, [some 0, none]⟩ (by decide) (by decide) (by decide)
  · exact fixed_valid [1, 0] ⟨0, [none, some 0]⟩ (by decide) (by decide) (by decide)

theorem state_arity_invariant (xs ys : List Nat) (iso : Iso (state xs) (state ys)) :
    xs.length = ys.length := by
  have hlt := iso.fmap_lt 0 (by simp [state])
  have ha := iso.arity 0 (by simp [state])
  have h0 : iso.fmap 0 = 0 := by simp [state] at hlt; omega
  rw [h0] at ha
  simpa [state] using ha.symm

theorem binary_diag_noniso (a b c : Nat) (hbc : b ≠ c)
    (iso : Iso (state [a, a]) (state [b, c])) : False := by
  have h := iso.insts_fwd (0, [a, a]) (by simp [state])
  simp [state] at h
  exact hbc (h.2.1.symm.trans h.2.2)

theorem req_nonzero (xs ys : List Nat) (iso : Iso (state xs) (state ys)) :
    iso.dmap 1 ≠ 0 ∧ iso.dmap 2 ≠ 0 := by
  have h := iso.reqs_fwd (1, 2) (by simp [state])
  simp only [state, List.mem_singleton] at h
  unfold sortPair at h
  have order : iso.dmap 1 ≤ iso.dmap 2 ∨ iso.dmap 2 < iso.dmap 1 := by omega
  rcases order with hle | hlt
  · rw [if_pos hle] at h
    simp only [Prod.mk.injEq] at h
    constructor <;> intro hz <;> omega
  · rw [if_neg (by omega)] at h
    simp only [Prod.mk.injEq] at h
    constructor <;> intro hz <;> omega

theorem target_to_genout_noniso (iso : Iso (state [1, 2]) (state [0, 1])) : False := by
  have h := iso.insts_fwd (0, [1, 2]) (by simp [state])
  simp [state] at h
  exact (req_nonzero _ _ iso).1 h.2.1

theorem target_to_genin_noniso (iso : Iso (state [1, 2]) (state [1, 0])) : False := by
  have h := iso.insts_fwd (0, [1, 2]) (by simp [state])
  simp [state] at h
  exact (req_nonzero _ _ iso).2 h.2.2

theorem genout_to_genin_noniso (iso : Iso (state [0, 1]) (state [1, 0])) : False := by
  have h := iso.insts_fwd (0, [0, 1]) (by simp [state])
  simp [state] at h
  exact (req_nonzero _ _ iso).1 h.2.2

theorem bounded_pairwise (i j : Nat) (hi : i < j) (hj : j < 5)
    (iso : Iso (state (boundedArgs i)) (state (boundedArgs j))) : False := by
  have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 := by omega
  rcases cases with h | h | h | h <;> subst i
  · have ha := state_arity_invariant _ _ iso
    have js : j = 1 ∨ j = 2 ∨ j = 3 ∨ j = 4 := by omega
    rcases js with h | h | h | h <;> subst j <;> simp [boundedArgs] at ha
  · have js : j = 2 ∨ j = 3 ∨ j = 4 := by omega
    rcases js with h | h | h <;> subst j
    · exact binary_diag_noniso 1 1 2 (by decide) iso
    · exact binary_diag_noniso 1 0 1 (by decide) iso
    · exact binary_diag_noniso 1 1 0 (by decide) iso
  · have js : j = 3 ∨ j = 4 := by omega
    rcases js with h | h <;> subst j
    · exact target_to_genout_noniso iso
    · exact target_to_genin_noniso iso
  · have : j = 4 := by omega
    subst j
    exact genout_to_genin_noniso iso

theorem F_5 :
    (∀ i, i < 5 → validResponse R2F 1 2 (delta (boundedArgs i)) ∧
      (delta (boundedArgs i)).length = 2 ∧ (boundedArgs i).length ≤ 2 ∧
      applyDelta R2F (delta (boundedArgs i)) = some (state (boundedArgs i))) ∧
    (∀ i j, i < j → j < 5 → Iso (state (boundedArgs i)) (state (boundedArgs j)) → False) := by
  refine ⟨?_, bounded_pairwise⟩
  intro i hi
  refine ⟨bounded_valid i hi, rfl, ?_, ?_⟩
  · have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
    rcases cases with h | h | h | h | h <;> subst i <;> decide
  · have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
    rcases cases with h | h | h | h | h <;> subst i <;> decide

def relabelledBase : Regime := ⟨3, [], [], [], [(0, 2)]⟩
def relabelledState (xs : List Nat) : Regime :=
  ⟨3, [xs.length], [(0, xs)], [], [(0, 2)]⟩
def relabelledArgs (i : Nat) : List Nat :=
  match i with
  | 0 => [0]
  | 1 => [0, 0]
  | 2 => [0, 2]
  | 3 => [1, 0]
  | _ => [0, 1]

theorem relabelled_fixed_valid (xs : List Nat) (c : Ctx)
    (happly : applyDelta relabelledBase (delta xs) = some (relabelledState xs))
    (hctx : wfCtx (relabelledState xs) c)
    (hsep : ¬ (derivable (relabelledState xs) (plug c 0) ↔
      derivable (relabelledState xs) (plug c 2))) :
    validResponse relabelledBase 0 2 (delta xs) := by
  refine ⟨relabelledState xs, happly, ⟨c, hctx, hsep⟩, ?_⟩
  intro q hq
  have : q = (0, 2) := by simpa [relabelledBase] using hq
  rw [this]
  exact ⟨c, hctx, hsep⟩

theorem relabelled_valid (i : Nat) (hi : i < 5) :
    validResponse relabelledBase 0 2 (delta (relabelledArgs i)) := by
  have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
  rcases cases with h | h | h | h | h <;> subst i
  · exact relabelled_fixed_valid [0] ⟨0, [none]⟩ (by decide) (by decide) (by decide)
  · exact relabelled_fixed_valid [0, 0] ⟨0, [none, none]⟩ (by decide) (by decide) (by decide)
  · exact relabelled_fixed_valid [0, 2] ⟨0, [none, some 2]⟩ (by decide) (by decide) (by decide)
  · exact relabelled_fixed_valid [1, 0] ⟨0, [some 1, none]⟩ (by decide) (by decide) (by decide)
  · exact relabelled_fixed_valid [0, 1] ⟨0, [none, some 1]⟩ (by decide) (by decide) (by decide)

theorem relabelled_arity (xs ys : List Nat)
    (iso : Iso (relabelledState xs) (relabelledState ys)) : xs.length = ys.length := by
  have hlt := iso.fmap_lt 0 (by simp [relabelledState])
  have ha := iso.arity 0 (by simp [relabelledState])
  have h0 : iso.fmap 0 = 0 := by simp [relabelledState] at hlt; omega
  rw [h0] at ha
  simpa [relabelledState] using ha.symm

theorem relabelled_diag (a b c : Nat) (hbc : b ≠ c)
    (iso : Iso (relabelledState [a, a]) (relabelledState [b, c])) : False := by
  have h := iso.insts_fwd (0, [a, a]) (by simp [relabelledState])
  simp [relabelledState] at h
  exact hbc (h.2.1.symm.trans h.2.2)

theorem relabelled_req (xs ys : List Nat)
    (iso : Iso (relabelledState xs) (relabelledState ys)) :
    iso.dmap 0 ≠ 1 ∧ iso.dmap 2 ≠ 1 := by
  have h := iso.reqs_fwd (0, 2) (by simp [relabelledState])
  simp only [relabelledState, List.mem_singleton] at h
  unfold sortPair at h
  have order : iso.dmap 0 ≤ iso.dmap 2 ∨ iso.dmap 2 < iso.dmap 0 := by omega
  rcases order with hle | hlt
  · rw [if_pos hle] at h
    simp only [Prod.mk.injEq] at h
    constructor <;> intro hz <;> omega
  · rw [if_neg (by omega)] at h
    simp only [Prod.mk.injEq] at h
    constructor <;> intro hz <;> omega

theorem relabelled_pairwise (i j : Nat) (hi : i < j) (hj : j < 5)
    (iso : Iso (relabelledState (relabelledArgs i))
      (relabelledState (relabelledArgs j))) : False := by
  have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 := by omega
  rcases cases with h | h | h | h <;> subst i
  · have ha := relabelled_arity _ _ iso
    have js : j = 1 ∨ j = 2 ∨ j = 3 ∨ j = 4 := by omega
    rcases js with h | h | h | h <;> subst j <;> simp [relabelledArgs] at ha
  · have js : j = 2 ∨ j = 3 ∨ j = 4 := by omega
    rcases js with h | h | h <;> subst j
    · exact relabelled_diag 0 0 2 (by decide) iso
    · exact relabelled_diag 0 1 0 (by decide) iso
    · exact relabelled_diag 0 0 1 (by decide) iso
  · have js : j = 3 ∨ j = 4 := by omega
    rcases js with h | h <;> subst j
    · have h := iso.insts_fwd (0, [0, 2]) (by simp [relabelledState, relabelledArgs])
      simp [relabelledState, relabelledArgs] at h
      exact (relabelled_req _ _ iso).1 h.2.1
    · have h := iso.insts_fwd (0, [0, 2]) (by simp [relabelledState, relabelledArgs])
      simp [relabelledState, relabelledArgs] at h
      exact (relabelled_req _ _ iso).2 h.2.2
  · have : j = 4 := by omega
    subst j
    have h := iso.insts_fwd (0, [1, 0]) (by simp [relabelledState, relabelledArgs])
    simp [relabelledState, relabelledArgs] at h
    exact (relabelled_req _ _ iso).1 h.2.2

theorem H01_relabelled_F5 :
    (∀ i, i < 5 → validResponse relabelledBase 0 2 (delta (relabelledArgs i)) ∧
      (delta (relabelledArgs i)).length = 2 ∧ (relabelledArgs i).length ≤ 2 ∧
      applyDelta relabelledBase (delta (relabelledArgs i)) =
        some (relabelledState (relabelledArgs i))) ∧
    (∀ i j, i < j → j < 5 → Iso (relabelledState (relabelledArgs i))
      (relabelledState (relabelledArgs j)) → False) := by
  refine ⟨?_, relabelled_pairwise⟩
  intro i hi
  refine ⟨relabelled_valid i hi, rfl, ?_, ?_⟩
  · have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
    rcases cases with h | h | h | h | h <;> subst i <;> decide
  · have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
    rcases cases with h | h | h | h | h <;> subst i <;> decide

theorem relabelling_binding (i : Nat) (hi : i < 5) :
    relabelledArgs i = (boundedArgs i).map swap01 ∧
    relabelledBase.data = R2F.data ∧ relabelledBase.forms = R2F.forms ∧
    relabelledBase.insts = R2F.insts ∧ relabelledBase.rules = R2F.rules ∧
    relabelledBase.reqs = [(sortPair (swap01 1, swap01 2))] := by
  have cases : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 ∨ i = 4 := by omega
  rcases cases with h | h | h | h | h <;> subst i <;> decide

theorem family_to_link (k b c : Nat) (hbc : b ≠ c)
    (iso : Iso (markF k) (state [b, c])) : False := by
  have h := iso.insts_fwd (0, List.replicate k 1) (by simp [markF])
  simp only [state, List.map_replicate, List.mem_singleton, Prod.mk.injEq] at h
  have hlen := congrArg List.length h.2
  simp only [List.length_replicate, List.length_cons, List.length_nil] at hlen
  have : k = 2 := hlen
  subst k
  simp [List.replicate] at h
  exact hbc (h.2.1.symm.trans h.2.2)

theorem H02_family_vs_genout (k : Nat) (_hk : 1 ≤ k)
    (iso : Iso (markF k) (state [0, 1])) : False :=
  family_to_link k 0 1 (by decide) iso

theorem H03_family_vs_genin (k : Nat) (_hk : 1 ≤ k)
    (iso : Iso (markF k) (state [1, 0])) : False :=
  family_to_link k 1 0 (by decide) iso

theorem H04_fixed_k3 :
    validResponse R2F 1 2 (deltaF 3) ∧ (deltaF 3).length = 2 ∧
    applyDelta R2F (deltaF 3) = some (markF 3) := by
  exact ⟨fixed_valid [1, 1, 1] ⟨0, [none, none, none]⟩
    (by decide) (by decide) (by decide), rfl, by decide⟩

theorem H05_bounded_family_members :
    markF 1 = state (boundedArgs 0) ∧ markF 2 = state (boundedArgs 1) ∧
    Nonempty (Iso (markF 1) (state (boundedArgs 0))) ∧
    Nonempty (Iso (markF 2) (state (boundedArgs 1))) := by
  refine ⟨rfl, rfl, ⟨?_⟩, ⟨?_⟩⟩
  · exact isoRefl (markF 1) (by decide)
  · exact isoRefl (markF 2) (by decide)

theorem H06_genesis_mark_refuted : ¬ validResponse R2F 1 2 (delta [0]) := by
  intro h
  obtain ⟨s, hs, hsep, _⟩ := h
  have ha : applyDelta R2F (delta [0]) = some (state [0]) := by decide
  rw [ha] at hs
  have : s = state [0] := Option.some.inj hs |>.symm
  subst s
  exact genesis_mark_not_separable hsep

theorem H07_mu2_unique_witness (a b : Item)
    (hval : validResponse R2F 1 2 [a, b]) (har : aritySum [a, b] ≤ 1) :
    ∃ s, applyDelta R2F [a, b] = some s ∧ Nonempty (Iso s U0F) :=
  mu2_unique_F a b hval har

theorem H08_reading_identification_refuted (xs ys : List Nat)
    (iso : Iso (state xs) (⟨2, [ys.length], [(0, ys)], [], [(0, 1)]⟩ : Regime)) :
    False := by
  have h0 := iso.dmap_lt 0 (by simp [state])
  have h1 := iso.dmap_lt 1 (by simp [state])
  have h2 := iso.dmap_lt 2 (by simp [state])
  change iso.dmap 0 < 2 at h0
  change iso.dmap 1 < 2 at h1
  change iso.dmap 2 < 2 at h2
  have i0 := iso.dinv_dmap 0 (by simp [state])
  have i1 := iso.dinv_dmap 1 (by simp [state])
  have i2 := iso.dinv_dmap 2 (by simp [state])
  have h01 : iso.dmap 0 ≠ iso.dmap 1 := by intro h; rw [h] at i0; omega
  have h02 : iso.dmap 0 ≠ iso.dmap 2 := by intro h; rw [h] at i0; omega
  have h12 : iso.dmap 1 ≠ iso.dmap 2 := by intro h; rw [h] at i1; omega
  omega

theorem public_deltaK_valid (k : Nat) (hk : 1 ≤ k) :
    validResponse R2L 0 1 (deltaK k) := deltaK_valid k hk
theorem public_markK_noniso (j k : Nat) (hjk : j ≠ k)
    (iso : Iso (markK j) (markK k)) : False := markK_pairwise_noniso j k hjk iso

end ResearchG01
