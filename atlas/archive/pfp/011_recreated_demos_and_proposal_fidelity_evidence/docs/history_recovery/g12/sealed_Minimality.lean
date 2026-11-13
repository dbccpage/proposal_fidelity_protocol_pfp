import Derivation.Basic
import Derivation.Inertia

/-!
# Challenge 3: minimality, non-uniqueness, and the tie family

All statements are relative to the declared candidate space (`Item` deltas)
and the declared cost measures: `mu1` = item count, `mu2` = item count then
new-form arity sum, lexicographically.
-/

namespace Derivation

/-- New-form arity sum: the second component of `mu2`. -/
def aritySum : List Item → Nat
  | [] => 0
  | .newForm a :: rest => a + aritySum rest
  | _ :: rest => aritySum rest

/-- Single-item deltas decompose. -/
theorem applyDelta_single (r : Regime) (a : Item) :
    applyDelta r [a] = applyItem r a := by
  unfold applyDelta
  cases h : applyItem r a <;> simp [List.foldlM, h]

/-- Two-item deltas decompose. -/
theorem applyDelta_pair (r : Regime) (a b : Item) :
    applyDelta r [a, b] =
      (applyItem r a).bind (fun r1 => applyItem r1 b) := by
  unfold applyDelta
  cases h : applyItem r a with
  | none => simp [List.foldlM, h]
  | some r1 => cases h2 : applyItem r1 b <;> simp [List.foldlM, h, h2]

/-! ## The surviving Challenge 3 regimes (reading L) -/

/-- Unary mark on datum 0. -/
def U0 : Regime := ⟨2, [1], [(0, [0])], [], [(0, 1)]⟩
/-- Unary mark on datum 1. -/
def U1 : Regime := ⟨2, [1], [(0, [1])], [], [(0, 1)]⟩
/-- Binary link. -/
def BL : Regime := ⟨2, [2], [(0, [0, 1])], [], [(0, 1)]⟩
/-- Binary self-loop. -/
def BD : Regime := ⟨2, [2], [(0, [0, 0])], [], [(0, 1)]⟩

theorem U0_separable : separable U0 0 1 :=
  ⟨⟨0, [none]⟩, by decide, by decide⟩

theorem U1_separable : separable U1 0 1 :=
  ⟨⟨0, [none]⟩, by decide, by decide⟩

theorem BL_separable : separable BL 0 1 :=
  ⟨⟨0, [none, some 1]⟩, by decide, by decide⟩

theorem BD_separable : separable BD 0 1 :=
  ⟨⟨0, [none, some 0]⟩, by decide, by decide⟩

/-! ## The candidate deltas and their validity -/

def deltaU0 : List Item := [.newForm 1, .newInst 0 [0]]
def deltaU1 : List Item := [.newForm 1, .newInst 0 [1]]
def deltaBL : List Item := [.newForm 2, .newInst 0 [0, 1]]
def deltaBD : List Item := [.newForm 2, .newInst 0 [0, 0]]

/-- Helper: a response to the single requirement of `R2L` is valid as soon
as it applies and separates the target. -/
theorem validResponse_R2L (δ : List Item) (s : Regime)
    (happ : applyDelta R2L δ = some s) (hsep : separable s 0 1) :
    validResponse R2L 0 1 δ := by
  refine ⟨s, happ, hsep, ?_⟩
  intro q hq
  have : q = (0, 1) := by
    cases hq with
    | head => rfl
    | tail _ h => cases h
  rw [this]
  exact hsep

theorem deltaU0_valid : validResponse R2L 0 1 deltaU0 :=
  validResponse_R2L _ U0 (by decide) U0_separable

theorem deltaU1_valid : validResponse R2L 0 1 deltaU1 :=
  validResponse_R2L _ U1 (by decide) U1_separable

theorem deltaBL_valid : validResponse R2L 0 1 deltaBL :=
  validResponse_R2L _ BL (by decide) BL_separable

theorem deltaBD_valid : validResponse R2L 0 1 deltaBD :=
  validResponse_R2L _ BD (by decide) BD_separable

/-! ## No zero- or one-item delta suffices -/

/-- Dead-end helper: a regime with no instances cannot host a separation. -/
theorem no_insts_no_separation {s : Regime} {d d' : Nat}
    (hi : s.insts = []) (hsep : separable s d d') : False :=
  separable_not_collapsed hsep (collapsed_of_no_insts s hi d d')

/-- Impossibility below cost 2 on any form-less, instance-less regime:
every delta of at most one item either fails to apply or leaves the
admitted instance set empty, and with no instances the target pair stays
collapsed. -/
theorem cost1_insufficient_general (r : Regime) (hforms : r.forms = [])
    (hinsts : r.insts = []) (i j : Nat) (δ : List Item)
    (hlen : δ.length ≤ 1) : ¬ validResponse r i j δ := by
  intro h
  cases h with
  | intro s hs =>
    have happ := hs.1
    have hsep := hs.2.1
    cases δ with
    | nil =>
        have hz : r = s := Option.some.inj happ
        subst hz
        exact no_insts_no_separation hinsts hsep
    | cons it rest =>
      cases rest with
      | cons b r2 => simp at hlen
      | nil =>
        rw [applyDelta_single] at happ
        cases it with
        | newDatum =>
            have hz := Option.some.inj happ
            subst hz
            refine no_insts_no_separation ?_ hsep
            exact hinsts
        | newForm a =>
            simp only [applyItem] at happ
            split at happ
            · have hz := Option.some.inj happ
              subst hz
              refine no_insts_no_separation ?_ hsep
              exact hinsts
            · cases happ
        | newInst f args =>
            simp only [applyItem] at happ
            rw [if_neg (by simp [hforms])] at happ
            cases happ
        | newRuleAll f =>
            simp only [applyItem] at happ
            rw [if_neg (by simp [hforms])] at happ
            cases happ

/-- Impossibility below cost 2 at Challenge 3, reading L. -/
theorem cost1_insufficient (δ : List Item) (hlen : δ.length ≤ 1) :
    ¬ validResponse R2L 0 1 δ :=
  cost1_insufficient_general R2L rfl rfl 0 1 δ hlen

/-- Impossibility below cost 2 at Challenge 3, reading F. -/
theorem cost1_insufficient_F (δ : List Item) (hlen : δ.length ≤ 1) :
    ¬ validResponse R2F 1 2 δ :=
  cost1_insufficient_general R2F rfl rfl 1 2 δ hlen

/-- Reading F existence: the unary mark on `<a>` is a valid two-item
response, so the minimum cost in reading F is also exactly two. -/
theorem deltaU0F_valid :
    validResponse R2F 1 2 [.newForm 1, .newInst 0 [1]] := by
  refine ⟨⟨3, [1], [(0, [1])], [], [(1, 2)]⟩, by decide, ?_, ?_⟩
  · exact ⟨⟨0, [none]⟩, by decide, by decide⟩
  · intro q hq
    have : q = (1, 2) := by
      cases hq with
      | head => rfl
      | tail _ h => cases h
    rw [this]
    exact ⟨⟨0, [none]⟩, by decide, by decide⟩

/-! ## The implemented isomorphism relation -/

def sortPair (p : Nat × Nat) : Nat × Nat :=
  if p.1 ≤ p.2 then p else (p.2, p.1)

/-- Isomorphism of regimes: bijections on datum and form indices (given by
two-sided inverses on the admitted ranges) preserving arities, instances,
rules, and requirements.  Mirrors `code/derivation/iso.py`; presentation
tokens are already absent from the Lean model. -/
structure Iso (r s : Regime) where
  dmap : Nat → Nat
  dinv : Nat → Nat
  fmap : Nat → Nat
  finv : Nat → Nat
  dmap_lt : ∀ d ∈ List.range r.data, dmap d < s.data
  dinv_lt : ∀ d ∈ List.range s.data, dinv d < r.data
  dinv_dmap : ∀ d ∈ List.range r.data, dinv (dmap d) = d
  dmap_dinv : ∀ d ∈ List.range s.data, dmap (dinv d) = d
  fmap_lt : ∀ f ∈ List.range r.forms.length, fmap f < s.forms.length
  finv_lt : ∀ f ∈ List.range s.forms.length, finv f < r.forms.length
  finv_fmap : ∀ f ∈ List.range r.forms.length, finv (fmap f) = f
  fmap_finv : ∀ f ∈ List.range s.forms.length, fmap (finv f) = f
  arity : ∀ f ∈ List.range r.forms.length,
      s.forms.getD (fmap f) 0 = r.forms.getD f 0
  insts_fwd : ∀ p ∈ r.insts, (fmap p.1, p.2.map dmap) ∈ s.insts
  insts_bwd : ∀ p ∈ s.insts, (finv p.1, p.2.map dinv) ∈ r.insts
  rules_fwd : ∀ f ∈ r.rules, fmap f ∈ s.rules
  rules_bwd : ∀ f ∈ s.rules, finv f ∈ r.rules
  reqs_fwd : ∀ q ∈ r.reqs, sortPair (dmap q.1, dmap q.2) ∈ s.reqs
  reqs_bwd : ∀ q ∈ s.reqs, sortPair (dinv q.1, dinv q.2) ∈ r.reqs

/-- Every regime with sorted requirement pairs is isomorphic to itself. -/
def isoRefl (r : Regime) (hreqs : ∀ q ∈ r.reqs, q.1 ≤ q.2) : Iso r r where
  dmap := id
  dinv := id
  fmap := id
  finv := id
  dmap_lt := fun d hd => List.mem_range.mp hd
  dinv_lt := fun d hd => List.mem_range.mp hd
  dinv_dmap := fun _ _ => rfl
  dmap_dinv := fun _ _ => rfl
  fmap_lt := fun f hf => List.mem_range.mp hf
  finv_lt := fun f hf => List.mem_range.mp hf
  finv_fmap := fun _ _ => rfl
  fmap_finv := fun _ _ => rfl
  arity := fun _ _ => rfl
  insts_fwd := fun p hp => by simpa [List.map_id] using hp
  insts_bwd := fun p hp => by simpa [List.map_id] using hp
  rules_fwd := fun _ hf => hf
  rules_bwd := fun _ hf => hf
  reqs_fwd := fun q hq => by
    simpa [sortPair, hreqs q hq] using hq
  reqs_bwd := fun q hq => by
    simpa [sortPair, hreqs q hq] using hq

/-- The swap of the two data. -/
def swap01 (d : Nat) : Nat :=
  if d = 0 then 1 else if d = 1 then 0 else d

/-- The two unary marks are isomorphic: the tie class is one class. -/
def isoU1U0 : Iso U1 U0 where
  dmap := swap01
  dinv := swap01
  fmap := id
  finv := id
  dmap_lt := by decide
  dinv_lt := by decide
  dinv_dmap := by decide
  dmap_dinv := by decide
  fmap_lt := by decide
  finv_lt := by decide
  finv_fmap := by decide
  fmap_finv := by decide
  arity := by decide
  insts_fwd := by decide
  insts_bwd := by decide
  rules_fwd := by decide
  rules_bwd := by decide
  reqs_fwd := by decide
  reqs_bwd := by decide

/-- Arity is an isomorphism invariant, so the unary mark and the binary
link are non-isomorphic tied minima. -/
theorem U0_not_iso_BL (iso : Iso U0 BL) : False := by
  have hlt := iso.fmap_lt 0 (by decide)
  have ha := iso.arity 0 (by decide)
  have h0 : iso.fmap 0 = 0 := by
    have h1 : iso.fmap 0 < 1 := by simpa [BL] using hlt
    omega
  rw [h0] at ha
  simp [U0, BL] at ha

theorem U0_not_iso_BD (iso : Iso U0 BD) : False := by
  have hlt := iso.fmap_lt 0 (by decide)
  have ha := iso.arity 0 (by decide)
  have h0 : iso.fmap 0 = 0 := by
    have h1 : iso.fmap 0 < 1 := by simpa [BD] using hlt
    omega
  rw [h0] at ha
  simp [U0, BD] at ha

/-- The self-loop is not the link: instance preservation would force the
datum bijection to collapse two data. -/
theorem BL_not_iso_BD (iso : Iso BL BD) : False := by
  have h := iso.insts_fwd (0, [0, 1]) (by decide)
  have h01 : iso.dmap 0 = 0 ∧ iso.dmap 1 = 0 := by
    simp [BD] at h
    exact ⟨h.2.1, h.2.2⟩
  have i0 := iso.dinv_dmap 0 (by decide)
  have i1 := iso.dinv_dmap 1 (by decide)
  rw [h01.1] at i0
  rw [h01.2] at i1
  omega

/-- Non-uniqueness of the minimum corrective augmentation under `mu1`:
two valid two-item responses whose results are non-isomorphic, while no
response of at most one item is valid. -/
theorem mu1_minimum_not_unique :
    validResponse R2L 0 1 deltaU0 ∧ validResponse R2L 0 1 deltaBL ∧
    deltaU0.length = 2 ∧ deltaBL.length = 2 ∧
    (∀ δ, δ.length ≤ 1 → ¬ validResponse R2L 0 1 δ) ∧
    applyDelta R2L deltaU0 = some U0 ∧
    applyDelta R2L deltaBL = some BL ∧
    (Iso U0 BL → False) :=
  ⟨deltaU0_valid, deltaBL_valid, rfl, rfl, cost1_insufficient,
   by decide, by decide, U0_not_iso_BL⟩

/-! ## The infinite tie family under `mu1` -/

/-- The `k`-ary mark: one `k`-ary form and one instance marking datum 1. -/
def markK (k : Nat) : Regime :=
  ⟨2, [k], [(0, List.replicate k 1)], [], [(0, 1)]⟩

def deltaK (k : Nat) : List Item :=
  [.newForm k, .newInst 0 (List.replicate k 1)]

theorem deltaK_applies (k : Nat) (hk : 1 ≤ k) :
    applyDelta R2L (deltaK k) = some (markK k) := by
  rw [show deltaK k = [Item.newForm k, Item.newInst 0 (List.replicate k 1)]
    from rfl]
  rw [applyDelta_pair]
  have h1 : applyItem R2L (.newForm k) =
      some ⟨2, [k], [], [], [(0, 1)]⟩ := by
    simp only [applyItem]
    rw [if_pos hk]
    rfl
  rw [h1]
  show applyItem ⟨2, [k], [], [], [(0, 1)]⟩
      (.newInst 0 (List.replicate k 1)) = some (markK k)
  simp only [applyItem]
  rw [if_pos]
  · rfl
  · refine ⟨by simp, by simp, ?_⟩
    intro x hx
    have hx1 : x = 1 := List.eq_of_mem_replicate hx
    subst hx1
    omega

theorem markK_separable (k : Nat) (hk : 1 ≤ k) :
    separable (markK k) 0 1 := by
  refine ⟨⟨0, List.replicate k none⟩,
    ⟨by simp [markK], by simp [markK],
     List.mem_replicate.mpr ⟨by omega, rfl⟩, ?_⟩, ?_⟩
  · intro s hs
    have : s = none := List.eq_of_mem_replicate hs
    rw [this]; trivial
  · intro hiff
    have hone : derivable (markK k) (plug ⟨0, List.replicate k none⟩ 1) := by
      simp [derivable, plug, markK, List.map_replicate]
    have hzero := hiff.mpr hone
    simp only [derivable, plug, markK, List.map_replicate] at hzero
    cases hzero with
    | inr h => cases h
    | inl h =>
      cases k with
      | zero => omega
      | succ n =>
        simp [List.replicate] at h

theorem deltaK_valid (k : Nat) (hk : 1 ≤ k) :
    validResponse R2L 0 1 (deltaK k) :=
  validResponse_R2L _ (markK k) (deltaK_applies k hk) (markK_separable k hk)

/-- Every member of the family has exactly two items. -/
theorem deltaK_length (k : Nat) : (deltaK k).length = 2 := rfl

/-- Distinct arities give non-isomorphic results: the `mu1` tie class is
infinite (one member for every arity `k ≥ 1`). -/
theorem markK_pairwise_noniso (j k : Nat) (hjk : j ≠ k)
    (iso : Iso (markK j) (markK k)) : False := by
  have hlt := iso.fmap_lt 0 (by simp [markK])
  have ha := iso.arity 0 (by simp [markK])
  have h0 : iso.fmap 0 = 0 := by
    simp [markK] at hlt
    omega
  rw [h0] at ha
  simp [markK] at ha
  exact hjk ha.symm

/-! ## Uniqueness up to isomorphism under `mu2` -/

/-- Under the refined measure (two items, new-form arity sum at most one),
every valid response to Challenge 3 (reading L) produces a regime
isomorphic to the unary mark `U0`. -/
theorem mu2_unique (a b : Item) (hval : validResponse R2L 0 1 [a, b])
    (har : aritySum [a, b] ≤ 1) :
    ∃ s, applyDelta R2L [a, b] = some s ∧ Nonempty (Iso s U0) := by
  cases hval with
  | intro s hs =>
    have happ := hs.1
    have hsep := hs.2.1
    refine ⟨s, happ, ?_⟩
    rw [applyDelta_pair] at happ
    -- First item: only `newDatum` and `newForm` can apply on a form-less
    -- regime.
    cases ha : applyItem R2L a with
    | none => rw [ha] at happ; cases happ
    | some r1 =>
      rw [ha] at happ
      have happ2 : applyItem r1 b = some s := happ
      cases a with
      | newInst f args =>
          simp only [applyItem] at ha
          rw [if_neg (by simp [R2L])] at ha
          cases ha
      | newRuleAll f =>
          simp only [applyItem] at ha
          rw [if_neg (by simp [R2L])] at ha
          cases ha
      | newDatum =>
          -- r1 still has no forms: the second item cannot be an instance,
          -- and without an instance the target stays collapsed.
          have hr1 : r1 = ⟨3, [], [], [], [(0, 1)]⟩ :=
            (Option.some.inj ha).symm
          subst hr1
          cases b with
          | newInst f args =>
              simp only [applyItem] at happ2
              rw [if_neg (by simp)] at happ2
              cases happ2
          | newRuleAll f =>
              simp only [applyItem] at happ2
              rw [if_neg (by simp)] at happ2
              cases happ2
          | newDatum =>
              have hz := Option.some.inj happ2
              subst hz
              exact absurd (no_insts_no_separation rfl hsep) id
          | newForm c =>
              simp only [applyItem] at happ2
              split at happ2
              · have hz := Option.some.inj happ2
                subst hz
                exact absurd (no_insts_no_separation rfl hsep) id
              · cases happ2
      | newForm c =>
          have hc1 : 1 ≤ c := by
            cases Nat.lt_or_ge c 1 with
            | inr hge => exact hge
            | inl hlt =>
                exfalso
                simp only [applyItem] at ha
                rw [if_neg (by omega)] at ha
                cases ha
          have hr1 : r1 = ⟨2, [c], [], [], [(0, 1)]⟩ := by
            simp only [applyItem] at ha
            rw [if_pos hc1] at ha
            exact (Option.some.inj ha).symm
          subst hr1
          cases b with
          | newDatum =>
              have hz := Option.some.inj happ2
              subst hz
              exact absurd (no_insts_no_separation rfl hsep) id
          | newForm c' =>
              simp only [applyItem] at happ2
              split at happ2
              · have hz := Option.some.inj happ2
                subst hz
                exact absurd (no_insts_no_separation rfl hsep) id
              · cases happ2
          | newRuleAll f =>
              simp only [applyItem] at happ2
              split at happ2
              · have hz := Option.some.inj happ2
                subst hz
                exact absurd (no_insts_no_separation rfl hsep) id
              · cases happ2
          | newInst f args =>
              -- The live shape.  Arity sum forces c = 1; well-formedness
              -- forces f = 0 and args = [d] with d < 2.
              have hcsum : c ≤ 1 := by
                have : aritySum [Item.newForm c, Item.newInst f args] = c := by
                  simp [aritySum]
                omega
              have hc : c = 1 := by omega
              subst hc
              simp only [applyItem] at happ2
              split at happ2
              next hcond =>
                have hz := Option.some.inj happ2
                have hf : f = 0 := by
                  have := hcond.1
                  simp at this
                  omega
                subst hf
                have hargs1 : args.length = 1 := by
                  have := hcond.2.1
                  simpa using this
                match args, hargs1 with
                | [x], _ =>
                  have hx2 : x < 2 := by
                    have := hcond.2.2 x (by simp)
                    simpa using this
                  subst hz
                  match x, hx2 with
                  | 0, _ => exact ⟨isoRefl U0 (by decide)⟩
                  | 1, _ => exact ⟨isoU1U0⟩
              next => cases happ2

end Derivation
