/-!
# A choice-free finite counting lemma and pigeonhole

This module closes the residual recorded in
`contact/analysis/separation_capacity_open.md` §3: a counting lemma

    `nodup_length_le : ∀ B l, l.Nodup → (∀ x ∈ l, x < B) → l.length ≤ B`

and the guarded-binder pigeonhole derived from it, both within the
audit gate `{propext, Quot.sound}`.  Nothing here imports Mathlib; the
whole development is core `Init` plus the lemmas proved below.

## Where the `Classical.choice` dependency actually came from

The residual was recorded as "inside `nodup_length_le`, not in any
lemma it cites".  Measured on this toolchain (Lean 4.33.0), the carrier
is neither a cited lemma nor the recursion machinery.  It is the
`ReflBEq Nat` INSTANCE, which `beq_self_eq_true` requires at `Nat`:

    `LawfulBEq Nat`              → `[propext, Quot.sound]`
    `ReflBEq Nat`                → `[propext, Classical.choice, Quot.sound]`
    `(B == B) = true` at `Nat`   → `[propext, Classical.choice, Quot.sound]`
    `(b == b) = true` at `Bool`  → `[propext, Quot.sound]`

So every route through `x == B` on `Nat` carries the dependency,
however the surrounding proof is written; and the equation compiler,
the `induction` tactic, `omega`, `List.mem_filter`, `List.filter_cons`
and `Decidable.byContradiction` are all clear.  Replacing `x == B` by
`decide (x = B)` removes the `Classical.choice` dependency:
`of_decide_eq_true`, `of_decide_eq_false` and `decide_eq_false` are
choice-free in their enumerated axiom reports.

The filter-based shape of the argument is the one the residual note
proposed; the `erase`-based route is avoided, since `List.length_erase`
and `List.Nodup.mem_erase_iff` are themselves choice-dependent.
`List.nodup_range` is choice-dependent too, so §6 uses a locally
defined descending index list instead.

## Classification

Metatheory apparatus.  This is finite counting used to license an
argument about the object language; it supplies no object-language
notion, and it is stated for `List Nat` only.
-/

namespace Pigeonhole

/-! ## 1. Duplicate-freeness, destructed through the `Pairwise`
constructor rather than through `List.nodup_cons`. -/

theorem nodup_head {α : Type} {x : α} {t : List α}
    (h : List.Nodup (x :: t)) : ∀ a ∈ t, x ≠ a := by
  cases h with
  | cons h1 _ => exact h1

theorem nodup_tail {α : Type} {x : α} {t : List α}
    (h : List.Nodup (x :: t)) : List.Nodup t := by
  cases h with
  | cons _ h2 => exact h2

/-! ## 2. A list splits by any boolean test, additively in length. -/

theorem length_filter_split {α : Type} (p : α → Bool) :
    ∀ l : List α,
      (l.filter p).length + (l.filter (fun x => !p x)).length = l.length
  | [] => rfl
  | x :: t => by
      have ih := length_filter_split p t
      rw [List.filter_cons, List.filter_cons]
      cases hp : p x with
      | true =>
          show (t.filter p).length + 1 + (t.filter (fun x => !p x)).length
            = t.length + 1
          omega
      | false =>
          show (t.filter p).length + ((t.filter (fun x => !p x)).length + 1)
            = t.length + 1
          omega

/-- A test that fails everywhere filters to the empty list. -/
theorem filter_eq_nil_of_none {α : Type} (p : α → Bool) :
    ∀ l : List α, (∀ y ∈ l, p y = false) → l.filter p = []
  | [], _ => rfl
  | x :: t, h => by
      have hx : p x = false := h x (List.mem_cons_self ..)
      rw [List.filter_cons, hx]
      show t.filter p = []
      exact filter_eq_nil_of_none p t
        (fun y hy => h y (List.mem_cons_of_mem x hy))

/-- Filtering preserves duplicate-freeness. -/
theorem filter_nodup {α : Type} (p : α → Bool) :
    ∀ l : List α, List.Nodup l → List.Nodup (l.filter p)
  | [], _ => List.Pairwise.nil
  | x :: t, hnd => by
      rw [List.filter_cons]
      have iht := filter_nodup p t (nodup_tail hnd)
      cases hp : p x with
      | true =>
          show List.Nodup (x :: t.filter p)
          refine List.Pairwise.cons ?_ iht
          intro a ha
          exact nodup_head hnd a (List.mem_filter.mp ha).1
      | false =>
          show List.Nodup (t.filter p)
          exact iht

/-! ## 3. A duplicate-free list holds at most one copy of a value.

`decide (x = B)` is used in place of `x == B`; see the module header
for why the `BEq` route is not available under the audit gate. -/

theorem nodup_filter_eq_le_one (B : Nat) :
    ∀ l : List Nat, List.Nodup l →
      (l.filter (fun x => decide (x = B))).length ≤ 1
  | [], _ => Nat.zero_le 1
  | x :: t, hnd => by
      rw [List.filter_cons]
      cases hp : (decide (x = B)) with
      | true =>
          show (x :: t.filter (fun y => decide (y = B))).length ≤ 1
          have hxB : x = B := of_decide_eq_true hp
          have hnone : ∀ y ∈ t, (decide (y = B)) = false := by
            intro y hy
            refine decide_eq_false ?_
            intro hyB
            exact nodup_head hnd y hy (hxB.trans hyB.symm)
          rw [filter_eq_nil_of_none _ t hnone]
          exact Nat.le_refl 1
      | false =>
          show (t.filter (fun y => decide (y = B))).length ≤ 1
          exact nodup_filter_eq_le_one B t (nodup_tail hnd)

/-! ## 4. The counting lemma. -/

/-- **The counting lemma.**  A duplicate-free list of naturals all
below `B` has at most `B` entries.  Induction on `B`, splitting the
list at the top value: the `= B` part has length at most one because
the list is duplicate-free, and the `≠ B` part is again duplicate-free
with every entry below `B`. -/
theorem nodup_length_le :
    ∀ (B : Nat) (l : List Nat), List.Nodup l → (∀ x ∈ l, x < B) →
      l.length ≤ B
  | 0, l, _, hb => by
      cases l with
      | nil => exact Nat.le_refl 0
      | cons x t =>
          exact absurd (hb x (List.mem_cons_self ..)) (Nat.not_lt_zero x)
  | B + 1, l, hnd, hb => by
      have hsplit := length_filter_split (fun x => decide (x = B)) l
      have h1 : (l.filter (fun x => decide (x = B))).length ≤ 1 :=
        nodup_filter_eq_le_one B l hnd
      have h2 : (l.filter (fun x => !(decide (x = B)))).length ≤ B := by
        refine nodup_length_le B _ (filter_nodup _ l hnd) ?_
        intro x hx
        have hm := List.mem_filter.mp hx
        have hlt : x < B + 1 := hb x hm.1
        have hne : x ≠ B := by
          have hb2 : ((!(decide (x = B))) = true) := hm.2
          cases hd : (decide (x = B)) with
          | false => exact of_decide_eq_false hd
          | true =>
              rw [hd] at hb2
              exact Bool.noConfusion hb2
        omega
      omega

/-! ## 5. A descending index list.

`List.range` is not used, because `List.nodup_range` is
choice-dependent on this toolchain. -/

def upto : Nat → List Nat
  | 0 => []
  | n + 1 => n :: upto n

theorem upto_length : ∀ n, (upto n).length = n
  | 0 => rfl
  | n + 1 => by
      show (upto n).length + 1 = n + 1
      rw [upto_length n]

theorem upto_mem : ∀ (n x : Nat), x ∈ upto n → x < n
  | 0, x, hx => absurd hx (List.not_mem_nil)
  | n + 1, x, hx => by
      rcases List.mem_cons.mp hx with h | h
      · omega
      · have := upto_mem n x h
        omega

/-- A map that separates distinct indices below `n` produces a
duplicate-free list. -/
theorem map_nodup_of_inj (f : Nat → Nat) :
    ∀ n : Nat, (∀ p, p < n → ∀ q, q < n → p ≠ q → f p ≠ f q) →
      List.Nodup ((upto n).map f)
  | 0, _ => List.Pairwise.nil
  | n + 1, hinj => by
      show List.Nodup (f n :: (upto n).map f)
      refine List.Pairwise.cons ?_ ?_
      · intro a ha
        obtain ⟨x, hx, rfl⟩ := List.mem_map.mp ha
        have hxn : x < n := upto_mem n x hx
        exact hinj n (by omega) x (by omega) (by omega)
      · exact map_nodup_of_inj f n
          (fun p hp q hq hpq => hinj p (by omega) q (by omega) hpq)

/-! ## 6. The pigeonhole. -/

/-- **The pigeonhole.**  A map sending `B + 1` indices into `B` values
collides.  The existential is written with each binder immediately
guarded by its bound, so that the negation is decidable and
`Decidable.byContradiction` applies; the shape `∃ p q, p < B + 1 ∧ …`
does not synthesize a `Decidable` instance, because the bound on `p`
then sits inside the `q` binder. -/
theorem pigeonhole (B : Nat) (f : Nat → Nat)
    (hf : ∀ p, p < B + 1 → f p < B) :
    ∃ p, p < B + 1 ∧ ∃ q, q < B + 1 ∧ p ≠ q ∧ f p = f q := by
  refine Decidable.byContradiction ?_
  intro hcon
  have hinj : ∀ p, p < B + 1 → ∀ q, q < B + 1 → p ≠ q → f p ≠ f q :=
    fun p hp q hq hpq hfe => hcon ⟨p, hp, q, hq, hpq, hfe⟩
  have hnd : List.Nodup ((upto (B + 1)).map f) :=
    map_nodup_of_inj f (B + 1) hinj
  have hall : ∀ y ∈ (upto (B + 1)).map f, y < B := by
    intro y hy
    obtain ⟨x, hx, rfl⟩ := List.mem_map.mp hy
    exact hf x (upto_mem (B + 1) x hx)
  have hle := nodup_length_le B ((upto (B + 1)).map f) hnd hall
  rw [List.length_map, upto_length] at hle
  omega

end Pigeonhole
