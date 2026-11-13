import Derivation.LadderGeneral

/-!
# General boundary cancellation: the composite boundary vanishes at
every dimension, coefficientwise

This module replaces the dimension-2-to-4 computation
`LadderGeneral.d2_zero_dims_2_3_4` by a general theorem: for EVERY
cell `σ : List Nat` and EVERY `τ : List Nat`,

    `coeffN τ (pushN (bdN σ)) = 0`.

The proof is the deletion-order pairing, not a brute-force decision
procedure.  The double sum runs over ordered position pairs
`(i, j)` with `i < σ.length` and `j < σ.length - 1`: delete position
`i` from `σ`, then position `j` from the result.  Every unordered pair
of deleted POSITIONS has exactly two orders — delete `b` then `a`, or
delete `a` then the shifted position `b - 1` (`eraseIdx_swap`) — and
the two signs are `sgn b * sgn a` and `sgn a * sgn (b - 1)`, which
cancel because `b = (b - 1) + 1` (`sgn_cancel`).  The reindexing of the
rectangle into unordered pairs is carried out exactly, by splitting each
row at the diagonal and transposing the resulting triangle
(`tri_transpose`).

## Scope note (declared inputs, not derived)

The alternating sign convention `sgn i = (-1)^i` and the INTEGER
coefficients of the chain calculus are DECLARED inputs of this
development, exactly as in `LadderGeneral`.  They are not derived from
anything: the filler rule `LadderGeneral.uniform_guarded_filler` fixes
only which cells the guarded step accepts and that the step strictly
extends the complex; it says nothing about coefficients, signs, or
chains.  `signless_countermodel` below exhibits an ascending cell on
which the SAME composite with all signs replaced by `1` is NONZERO,
so the vanishing theorem is a theorem about the declared sign
convention and cannot be attributed to the filler rule.  This is an
integer-coefficient countermodel; it is not a universal claim about
all coefficient systems (for example, characteristic two changes the
signless calculation).

## What strict ascent does and does not do here

The task specification expected strict ascent (`ascB`) to be
load-bearing for the coefficientwise vanishing.  It is not, and this
module does not pretend otherwise: `d2_zero_unrestricted` proves the
vanishing for EVERY list, including repeated-vertex pseudo-cells, and
`illformed_countermodel` confirms by decision that the composite of the
pseudo-cell `[0, 0, 1]` still vanishes at every face.  The pairing
argument never needs distinct faces, because the two members of a pair
cancel whether or not a third term lands in the same coefficient slot.

Strict ascent IS load-bearing for the DISTINCTNESS statements, which are
proved here and are genuinely false without it:

* `eraseIdx_inj_of_asc` — distinct deleted positions give distinct
  facets;
* `codim2_distinct` — distinct unordered position pairs give distinct
  codimension-two faces, so for an ascending cell the deletion-order
  pairing is injective on faces;
* both fail for `[0, 0, 1]` (`illformed_countermodel`), where two
  distinct positions give the SAME facet and the composite's
  coefficient slot for `[0]` collects four terms instead of two.

NOT proved here, and therefore not claimed: the quantitative form of
the last point — that for EVERY ascending cell each codimension-two
face collects exactly two of the `n * (n - 1)` ordered deletion pairs.
That is a consequence of `codim2_distinct` by counting, but the count
is not formalized; it is recorded only as a decided computation on the
exhibits of `illformed_countermodel` (slot sizes 2 and 4) and checked
exhaustively over the declared finite bounds in the Python mirror
(`perfect_matching` in `code/derivation/boundary_cancellation.py`).

`d2_zero_general` is stated with the requested hypotheses
(`ascB σ = true`, `2 ≤ σ.length`); they are recorded in the statement
and discharged by the stronger unrestricted theorem.  Claiming that
they are necessary would be false.

## Classification

Proved theorem (`d2_zero_general`, `d2_zero_unrestricted`,
`d2_zero_replayed`, `d2_zero_renamed`, `eraseIdx_inj_of_asc`,
`codim2_distinct`, `ascB_map`); countermodel (`signless_countermodel`,
`illformed_countermodel`); declared inputs (integer coefficients, the
alternating sign convention, the ascending-list cell encoding, all
imported from `LadderGeneral`).
-/

namespace BoundaryCancellation

open LadderGeneral

/-! ## 1. Finite integer sums (metatheory apparatus) -/

/-- `sumTo f m = f 0 + ⋯ + f (m - 1)`. -/
def sumTo (f : Nat → Int) : Nat → Int
  | 0 => 0
  | m + 1 => sumTo f m + f m

/-- `sumFrom f a m = f a + ⋯ + f (a + m - 1)`. -/
def sumFrom (f : Nat → Int) (a : Nat) : Nat → Int
  | 0 => 0
  | m + 1 => sumFrom f a m + f (a + m)

theorem sumTo_const_zero (m : Nat) : sumTo (fun _ => (0 : Int)) m = 0 := by
  induction m with
  | zero => rfl
  | succ m ih =>
      show sumTo (fun _ => (0 : Int)) m + 0 = 0
      omega

theorem sumTo_congr (f g : Nat → Int) (m : Nat)
    (h : ∀ t, t < m → f t = g t) : sumTo f m = sumTo g m := by
  induction m with
  | zero => rfl
  | succ m ih =>
      show sumTo f m + f m = sumTo g m + g m
      rw [ih (fun t ht => h t (by omega)), h m (by omega)]

theorem sumTo_add (f g : Nat → Int) (m : Nat) :
    sumTo (fun t => f t + g t) m = sumTo f m + sumTo g m := by
  induction m with
  | zero => rfl
  | succ m ih =>
      show sumTo (fun t => f t + g t) m + (f m + g m)
        = sumTo f m + f m + (sumTo g m + g m)
      rw [ih]
      omega

theorem sumTo_split (f : Nat → Int) (a m : Nat) :
    sumTo f (a + m) = sumTo f a + sumFrom f a m := by
  induction m with
  | zero => show sumTo f a = sumTo f a + 0; omega
  | succ m ih =>
      show sumTo f (a + m) + f (a + m)
        = sumTo f a + (sumFrom f a m + f (a + m))
      rw [ih]
      omega

theorem sumFrom_shift (f : Nat → Int) (a m : Nat) :
    sumFrom f a m = sumFrom (fun b => f (b - 1)) (a + 1) m := by
  induction m with
  | zero => rfl
  | succ m ih =>
      show sumFrom f a m + f (a + m)
        = sumFrom (fun b => f (b - 1)) (a + 1) m + f (a + 1 + m - 1)
      rw [ih, show a + 1 + m - 1 = a + m from by omega]

/-! ## 2. Transposing a triangular double sum -/

/-- Row-major upper triangle: `Σ_{a < n} Σ_{a < b < n} F a b`. -/
def rowTri (F : Nat → Nat → Int) (n : Nat) : Int :=
  sumTo (fun a => sumFrom (F a) (a + 1) (n - (a + 1))) n

/-- Column-major upper triangle: `Σ_{b < n} Σ_{a < b} F a b`. -/
def colTri (F : Nat → Nat → Int) (n : Nat) : Int :=
  sumTo (fun b => sumTo (fun a => F a b) b) n

/-- The two enumerations of the strict upper triangle agree. -/
theorem tri_transpose (F : Nat → Nat → Int) (n : Nat) :
    rowTri F n = colTri F n := by
  induction n with
  | zero => rfl
  | succ n ih =>
      have hstep : ∀ a, a < n →
          sumFrom (F a) (a + 1) (n + 1 - (a + 1))
            = sumFrom (F a) (a + 1) (n - (a + 1)) + F a n := by
        intro a ha
        rw [show n + 1 - (a + 1) = (n - (a + 1)) + 1 from by omega]
        show sumFrom (F a) (a + 1) (n - (a + 1))
            + F a (a + 1 + (n - (a + 1))) = _
        rw [show a + 1 + (n - (a + 1)) = n from by omega]
      have e1 : rowTri F (n + 1)
          = sumTo (fun a => sumFrom (F a) (a + 1) (n + 1 - (a + 1))) n
            + sumFrom (F n) (n + 1) (n + 1 - (n + 1)) := rfl
      have e2 : sumFrom (F n) (n + 1) (n + 1 - (n + 1)) = 0 := by
        rw [show n + 1 - (n + 1) = 0 from by omega]
        rfl
      have e3 : sumTo (fun a => sumFrom (F a) (a + 1) (n + 1 - (a + 1))) n
          = sumTo (fun a => sumFrom (F a) (a + 1) (n - (a + 1))) n
            + sumTo (fun a => F a n) n := by
        rw [sumTo_congr _ _ _ hstep, sumTo_add]
      have e4 : colTri F (n + 1)
          = colTri F n + sumTo (fun a => F a n) n := rfl
      have e5 : rowTri F n
          = sumTo (fun a => sumFrom (F a) (a + 1) (n - (a + 1))) n := rfl
      rw [e1, e2, e3, e4, ← e5, ih]
      omega

/-! ## 3. The two deletion orders (declared cell encoding) -/

/-- Deleting position `c + 1` and then position `a ≤ c` is deleting
position `a` and then the shifted position `c`. -/
theorem eraseIdx_eraseIdx_succ :
    ∀ (l : List Nat) (a c : Nat), a ≤ c →
      (l.eraseIdx (c + 1)).eraseIdx a = (l.eraseIdx a).eraseIdx c
  | [], _, _, _ => rfl
  | _ :: _, 0, _, _ => rfl
  | x :: t, a + 1, c, h => by
      obtain ⟨c', rfl⟩ : ∃ c', c = c' + 1 := ⟨c - 1, by omega⟩
      show x :: (t.eraseIdx (c' + 1)).eraseIdx a
        = x :: (t.eraseIdx a).eraseIdx c'
      rw [eraseIdx_eraseIdx_succ t a c' (by omega)]

/-- **The pairing identity.** For `a < b` the two deletion orders on
the codimension-two face agree: deleting `b` then `a` equals deleting
`a` then `b - 1`. -/
theorem eraseIdx_swap (l : List Nat) (a b : Nat) (h : a < b) :
    (l.eraseIdx b).eraseIdx a = (l.eraseIdx a).eraseIdx (b - 1) := by
  obtain ⟨c, rfl⟩ : ∃ c, b = c + 1 := ⟨b - 1, by omega⟩
  rw [show c + 1 - 1 = c from by omega]
  exact eraseIdx_eraseIdx_succ l a c (by omega)

/-! ## 4. The declared alternating sign -/

theorem sgn_succ (c : Nat) : sgn (c + 1) = -sgn c := by
  unfold sgn
  have h : c % 2 = 0 ∨ c % 2 = 1 := by omega
  rcases h with h | h <;> simp [h, Nat.add_mod] <;> omega

/-- **The sign cancellation.** For `a < b` the two deletion orders
carry opposite signs. -/
theorem sgn_cancel (a b : Nat) (h : 0 < b) :
    sgn b * sgn a + sgn a * sgn (b - 1) = 0 := by
  obtain ⟨c, rfl⟩ : ∃ c, b = c + 1 := ⟨b - 1, by omega⟩
  rw [show c + 1 - 1 = c from by omega, sgn_succ]
  have h1 : sgn a * sgn c = -(-sgn c * sgn a) := by
    rw [Int.neg_mul, Int.neg_neg, Int.mul_comm]
  rw [h1]
  omega

/-! ## 5. Coefficient collection is additive -/

theorem coeffN_nil (τ : List Nat) : coeffN τ [] = 0 := rfl

theorem foldl_acc (l : List (Int × List Nat)) (z : Int) :
    l.foldl (fun acc p => acc + p.1) z
      = z + l.foldl (fun acc p => acc + p.1) 0 := by
  induction l generalizing z with
  | nil => show z = z + 0; omega
  | cons p t ih =>
      show t.foldl _ (z + p.1) = z + t.foldl _ (0 + p.1)
      rw [ih (z + p.1), ih (0 + p.1)]
      omega

theorem coeffN_append (τ : List Nat) (a b : List (Int × List Nat)) :
    coeffN τ (a ++ b) = coeffN τ a + coeffN τ b := by
  unfold coeffN
  rw [List.filter_append, List.foldl_append, foldl_acc]

/-- The coefficient test is the one `coeffN` itself uses — the boolean
`BEq` test on presentations.  Keeping the whole development in that
form avoids any appeal to a decidability bridge. -/
theorem coeffN_singleton (τ : List Nat) (p : Int × List Nat) :
    coeffN τ [p] = if (p.2 == τ) = true then p.1 else 0 := by
  unfold coeffN
  rw [List.filter_cons]
  split
  · show (0 : Int) + p.1 = p.1
    omega
  · rfl

theorem coeffN_map_range (τ : List Nat) (f : Nat → Int × List Nat)
    (m : Nat) :
    coeffN τ ((List.range m).map f)
      = sumTo (fun j => if ((f j).2 == τ) = true then (f j).1 else 0) m := by
  induction m with
  | zero => rfl
  | succ m ih =>
      have hs : coeffN τ [f m]
          = if ((f m).2 == τ) = true then (f m).1 else 0 :=
        coeffN_singleton τ (f m)
      rw [List.range_succ, List.map_append]
      simp only [List.map_cons, List.map_nil]
      rw [coeffN_append, ih, hs]
      rfl

theorem coeffN_flatMap_range (τ : List Nat)
    (h : Nat → List (Int × List Nat)) (n : Nat) :
    coeffN τ ((List.range n).flatMap h)
      = sumTo (fun i => coeffN τ (h i)) n := by
  induction n with
  | zero => rfl
  | succ n ih =>
      rw [List.range_succ, List.flatMap_append]
      simp only [List.flatMap_cons, List.flatMap_nil, List.append_nil]
      rw [coeffN_append, ih]
      rfl

/-! ## 6. The composite boundary as a rectangle of signed terms -/

/-- The signed contribution of the ordered deletion pair `(i, j)`:
delete position `i` of `σ`, then position `j` of the result. -/
def dterm (σ τ : List Nat) (i j : Nat) : Int :=
  if ((σ.eraseIdx i).eraseIdx j == τ) = true then sgn i * sgn j else 0

theorem coeff_push_bd (σ τ : List Nat) :
    coeffN τ (pushN (bdN σ))
      = sumTo (fun i => sumTo (dterm σ τ i) (σ.eraseIdx i).length)
          σ.length := by
  have h1 : pushN (bdN σ)
      = (List.range σ.length).flatMap (fun i =>
          (List.range (σ.eraseIdx i).length).map (fun j =>
            (sgn i * sgn j, (σ.eraseIdx i).eraseIdx j))) := by
    simp only [pushN, bdN, List.flatMap_map, List.map_map,
      Function.comp_def]
  rw [h1, coeffN_flatMap_range]
  refine sumTo_congr _ _ _ (fun i _ => ?_)
  rw [coeffN_map_range]
  rfl

/-- The composite boundary is the rectangle sum over ordered deletion
pairs `(i, j)`, `i < σ.length`, `j < σ.length - 1`. -/
theorem coeff_rect (σ τ : List Nat) :
    coeffN τ (pushN (bdN σ))
      = sumTo (fun i => sumTo (dterm σ τ i) (σ.length - 1)) σ.length := by
  rw [coeff_push_bd]
  refine sumTo_congr _ _ _ (fun i hi => ?_)
  rw [List.length_eraseIdx_of_lt hi]

/-- **The paired terms cancel.**  For `a < b` the ordered pairs
`(b, a)` and `(a, b - 1)` name the same codimension-two face with
opposite signs. -/
theorem ite_pair_cancel (c : Bool) (u v : Int) (h : u + v = 0) :
    (if c = true then u else 0) + (if c = true then v else 0) = 0 := by
  cases c with
  | false =>
      show (0 : Int) + 0 = 0
      omega
  | true =>
      show u + v = 0
      exact h

theorem dterm_cancel (σ τ : List Nat) (a b : Nat) (h : a < b) :
    dterm σ τ b a + dterm σ τ a (b - 1) = 0 := by
  unfold dterm
  rw [eraseIdx_swap σ a b h]
  exact ite_pair_cancel _ _ _ (sgn_cancel a b (by omega))

theorem rect_zero (σ τ : List Nat) :
    sumTo (fun i => sumTo (dterm σ τ i) (σ.length - 1)) σ.length = 0 := by
  have hsplit : ∀ i, i < σ.length →
      sumTo (dterm σ τ i) (σ.length - 1)
        = sumTo (dterm σ τ i) i
          + sumFrom (dterm σ τ i) i (σ.length - 1 - i) := by
    intro i _
    have hs := sumTo_split (dterm σ τ i) i (σ.length - 1 - i)
    rw [show i + (σ.length - 1 - i) = σ.length - 1 from by omega] at hs
    exact hs
  rw [sumTo_congr _ _ _ hsplit, sumTo_add]
  have hupper :
      sumTo (fun i => sumFrom (dterm σ τ i) i (σ.length - 1 - i))
          σ.length
        = rowTri (fun a b => dterm σ τ a (b - 1)) σ.length := by
    refine sumTo_congr _ _ _ (fun i _ => ?_)
    rw [sumFrom_shift,
      show σ.length - 1 - i = σ.length - (i + 1) from by omega]
  rw [hupper, tri_transpose]
  unfold colTri
  rw [← sumTo_add]
  have hzero : ∀ b, b < σ.length →
      sumTo (dterm σ τ b) b + sumTo (fun a => dterm σ τ a (b - 1)) b
        = 0 := by
    intro b _
    rw [← sumTo_add,
      sumTo_congr _ (fun _ => (0 : Int)) b
        (fun a ha => dterm_cancel σ τ a b ha)]
    exact sumTo_const_zero b
  rw [sumTo_congr _ (fun _ => (0 : Int)) _ hzero]
  exact sumTo_const_zero _

/-! ## 7. The general vanishing theorem -/

/-- **General boundary cancellation, unrestricted.**  For every list
`σ` and every `τ`, the composite boundary has coefficient zero at `τ`.
No well-formedness hypothesis is used: the deletion-order pairing
cancels term by term. -/
theorem d2_zero_unrestricted (σ τ : List Nat) :
    coeffN τ (pushN (bdN σ)) = 0 := by
  rw [coeff_rect]
  exact rect_zero σ τ

/-- **General boundary cancellation (the requested statement).**  For
every strictly ascending cell of dimension at least one and every `τ`,
the composite boundary vanishes at `τ`.  The hypotheses are recorded
because the statement was posed with them; the proof does not need
them (`d2_zero_unrestricted`). -/
theorem d2_zero_general (σ : List Nat) (_hasc : ascB σ = true)
    (_hlen : 2 ≤ σ.length) (τ : List Nat) :
    coeffN τ (pushN (bdN σ)) = 0 :=
  d2_zero_unrestricted σ τ

/-- The dimension-2-to-4 computation `LadderGeneral.d2_zero_dims_2_3_4`
is now a corollary at every dimension: every facet of every ascending
cell over any vertex set collects coefficient zero. -/
theorem d2_zero_facets (σ : List Nat) (_hasc : ascB σ = true)
    (_hlen : 2 ≤ σ.length) :
    ∀ τ ∈ facets σ, coeffN τ (pushN (bdN σ)) = 0 :=
  fun τ _ => d2_zero_unrestricted σ τ

/-! ## 8. Connection to replayed complexes -/

/-- **Every replayed cell of dimension at least one has vanishing
composite boundary.**  Well-formedness (exact arity and strict ascent)
is supplied by the replayed invariant `LadderGeneral.wf_nreplay`; the
vanishing is `d2_zero_general`. -/
theorem d2_zero_replayed (h : List NEvent) (k : Nat) (σ : List Nat)
    (hk : 1 ≤ k) (hmem : σ ∈ (nreplay h emptyN).cells k) (τ : List Nat) :
    coeffN τ (pushN (bdN σ)) = 0 := by
  have hwf := wf_nreplay h emptyN wf_empty k σ hmem
  have hlen : σ.length = k + 1 := hwf.1
  exact d2_zero_general σ hwf.2 (by omega) τ

/-- The same, for the dimension-4 demonstration complex of
`LadderGeneral`. -/
theorem d2_zero_d4 (k : Nat) (σ : List Nat) (hk : 1 ≤ k)
    (hmem : σ ∈ d4Complex.cells k) (τ : List Nat) :
    coeffN τ (pushN (bdN σ)) = 0 := by
  have hd : d4Complex = nreplay d4Events emptyN := rfl
  exact d2_zero_replayed d4Events k σ hk (hd ▸ hmem) τ

/-! ## 9. Strict ascent: what it really buys (distinctness) -/

theorem ascB_tail (x y : Nat) (t : List Nat)
    (h : ascB (x :: y :: t) = true) : ascB (y :: t) = true := by
  simp only [ascB, Bool.and_eq_true] at h
  exact h.2

theorem ascB_head_lt (x : Nat) :
    ∀ (l : List Nat), ascB (x :: l) = true → ∀ z ∈ l, x < z
  | [], _, _, hz => absurd hz (by simp)
  | y :: t, h, z, hz => by
      have h' : ascB (x :: y :: t) = true := h
      simp only [ascB, Bool.and_eq_true, decide_eq_true_eq] at h'
      rcases List.mem_cons.mp hz with hzy | hz'
      · exact hzy ▸ h'.1
      · exact Nat.lt_trans h'.1
          (ascB_head_lt y t (ascB_tail x y t h) z hz')

/-- **Distinct positions, distinct facets — for ascending cells.**
This is where strict ascent is load-bearing; it fails for
`[0, 0, 1]` (`illformed_countermodel`). -/
theorem eraseIdx_inj_of_asc :
    ∀ (l : List Nat), ascB l = true → ∀ i j, i < l.length →
      j < l.length → l.eraseIdx i = l.eraseIdx j → i = j
  | [], _, _, _, hi, _, _ => absurd hi (by simp)
  | [_], _, i, j, hi, hj, _ => by
      simp only [List.length_cons, List.length_nil] at hi hj
      omega
  | x :: y :: t, h, i, j, hi, hj, he => by
      have hasc : ascB (x :: y :: t) = true := h
      simp only [ascB, Bool.and_eq_true, decide_eq_true_eq] at hasc
      have hxy : x < y := hasc.1
      simp only [List.length_cons] at hi hj
      match i, j with
      | 0, 0 => rfl
      | 0, j + 1 =>
          exfalso
          have he' : y :: t = x :: (y :: t).eraseIdx j := he
          injection he' with hyx _
          omega
      | i + 1, 0 =>
          exfalso
          have he' : x :: (y :: t).eraseIdx i = y :: t := he
          injection he' with hxy2 _
          omega
      | i + 1, j + 1 =>
          have he' : x :: (y :: t).eraseIdx i
              = x :: (y :: t).eraseIdx j := he
          injection he' with _ hij
          have hi' : i < (y :: t).length := by
            simp only [List.length_cons]; omega
          have hj' : j < (y :: t).length := by
            simp only [List.length_cons]; omega
          have := eraseIdx_inj_of_asc (y :: t)
            (ascB_tail x y t h) i j hi' hj' hij
          omega

/-- **Distinct unordered position pairs, distinct codimension-two
faces — for ascending cells.**  With `eraseIdx_swap` this says the
deletion-order pairing is INJECTIVE on the codimension-two faces of an
ascending cell.  Load-bearing use of strict ascent; false for
`[0, 0, 1]`.  The quantitative consequence — every such face collects
exactly two of the ordered deletion pairs — is NOT proved here; see the
module docstring for its exact status. -/
theorem codim2_distinct :
    ∀ (l : List Nat), ascB l = true → ∀ a b c d, a < b → c < d →
      b < l.length → d < l.length →
      (l.eraseIdx b).eraseIdx a = (l.eraseIdx d).eraseIdx c →
      a = c ∧ b = d
  | [], _, _, _, _, _, _, _, hb, _, _ => absurd hb (by simp)
  | [_], _, a, b, _, _, hab, _, hb, _, _ => by
      simp only [List.length_cons, List.length_nil] at hb
      exact absurd hab (by omega)
  | x :: y :: t, h, a, b, c, d, hab, hcd, hb, hd, he => by
      obtain ⟨b', rfl⟩ : ∃ b', b = b' + 1 := ⟨b - 1, by omega⟩
      obtain ⟨d', rfl⟩ : ∃ d', d = d' + 1 := ⟨d - 1, by omega⟩
      have htail : ascB (y :: t) = true := ascB_tail x y t h
      simp only [List.length_cons] at hb hd
      have hb' : b' < (y :: t).length := by
        simp only [List.length_cons]; omega
      have hd' : d' < (y :: t).length := by
        simp only [List.length_cons]; omega
      match a, c with
      | 0, 0 =>
          have he' : (y :: t).eraseIdx b' = (y :: t).eraseIdx d' := he
          have := eraseIdx_inj_of_asc (y :: t) htail b' d' hb' hd' he'
          exact ⟨rfl, by omega⟩
      | 0, c + 1 =>
          exfalso
          have he' : (y :: t).eraseIdx b'
              = x :: ((y :: t).eraseIdx d').eraseIdx c := he
          have hx : x ∈ (y :: t).eraseIdx b' := by
            rw [he']; exact List.mem_cons_self
          exact Nat.lt_irrefl x
            (ascB_head_lt x (y :: t) h x (List.mem_of_mem_eraseIdx hx))
      | a + 1, 0 =>
          exfalso
          have he' : x :: ((y :: t).eraseIdx b').eraseIdx a
              = (y :: t).eraseIdx d' := he
          have hx : x ∈ (y :: t).eraseIdx d' := by
            rw [← he']; exact List.mem_cons_self
          exact Nat.lt_irrefl x
            (ascB_head_lt x (y :: t) h x (List.mem_of_mem_eraseIdx hx))
      | a + 1, c + 1 =>
          have he' : x :: ((y :: t).eraseIdx b').eraseIdx a
              = x :: ((y :: t).eraseIdx d').eraseIdx c := he
          injection he' with _ hin
          have := codim2_distinct (y :: t) htail a b' c d'
            (by omega) (by omega) hb' hd' hin
          exact ⟨by omega, by omega⟩

/-! ## 10. Renaming independence -/

theorem eraseIdx_map (r : Nat → Nat) :
    ∀ (l : List Nat) (i : Nat),
      (l.map r).eraseIdx i = (l.eraseIdx i).map r
  | [], _ => rfl
  | _ :: _, 0 => rfl
  | _ :: t, i + 1 => by
      simp only [List.map_cons, List.eraseIdx_cons_succ,
        eraseIdx_map r t i]

/-- A strictly monotone renaming of vertices preserves strict
ascent. -/
theorem ascB_map (r : Nat → Nat) (hr : ∀ x y, x < y → r x < r y) :
    ∀ σ : List Nat, ascB σ = true → ascB (σ.map r) = true
  | [], _ => rfl
  | [_], _ => rfl
  | x :: y :: t, h => by
      have hasc : ascB (x :: y :: t) = true := h
      simp only [ascB, Bool.and_eq_true, decide_eq_true_eq] at hasc
      have hrec : ascB ((y :: t).map r) = true :=
        ascB_map r hr (y :: t) (ascB_tail x y t h)
      simp only [List.map_cons] at hrec ⊢
      simp only [ascB, Bool.and_eq_true, decide_eq_true_eq]
      exact ⟨hr x y hasc.1, hrec⟩

/-- **Renaming independence, exact scope.**  Let `r : Nat → Nat` be
strictly monotone (hence injective).  Then the renamed cell is again
strictly ascending, its length is unchanged, its facets are the renamed
facets, and its composite boundary vanishes at every `τ`.  The
vanishing itself needs no hypothesis on `r` at all — it is
`d2_zero_unrestricted` applied to `σ.map r`; what the monotonicity buys
is that the WELL-FORMEDNESS hypotheses transport, so the renamed cell is
again an admissible cell of the guarded calculus.  Nothing is claimed
for renamings that are injective but not monotone: those can destroy
`ascB` (they permute vertex order), though the vanishing still holds. -/
theorem d2_zero_renamed (r : Nat → Nat) (hr : ∀ x y, x < y → r x < r y)
    (σ : List Nat) (hasc : ascB σ = true) (hlen : 2 ≤ σ.length) :
    ascB (σ.map r) = true ∧ (σ.map r).length = σ.length ∧
    (∀ i, (σ.map r).eraseIdx i = (σ.eraseIdx i).map r) ∧
    (∀ τ : List Nat, coeffN τ (pushN (bdN (σ.map r))) = 0) := by
  refine ⟨ascB_map r hr σ hasc, List.length_map .., ?_, ?_⟩
  · exact fun i => eraseIdx_map r σ i
  · exact fun τ => d2_zero_general (σ.map r) (ascB_map r hr σ hasc)
      (by rw [List.length_map]; exact hlen) τ

/-- The canonical shift `x ↦ x + 1` is such a renaming; the scope note
above applies to it verbatim. -/
theorem d2_zero_shift (σ : List Nat) (hasc : ascB σ = true)
    (hlen : 2 ≤ σ.length) :
    ascB (σ.map (fun x => x + 1)) = true ∧
    (∀ τ : List Nat,
      coeffN τ (pushN (bdN (σ.map (fun x => x + 1)))) = 0) := by
  have h := d2_zero_renamed (fun x => x + 1) (fun _ _ hxy => by omega)
    σ hasc hlen
  exact ⟨h.1, h.2.2.2⟩

/-! ## 11. Countermodel: the signs are load-bearing -/

/-- The signless boundary: the same facets, every coefficient `1`. -/
def bdNoSign (σ : List Nat) : List (Int × List Nat) :=
  (List.range σ.length).map (fun i => ((1 : Int), σ.eraseIdx i))

/-- The signless pushforward. -/
def pushNoSign (ch : List (Int × List Nat)) : List (Int × List Nat) :=
  ch.flatMap (fun p => (bdNoSign p.2).map (fun q => (p.1 * q.1, q.2)))

/-- **Countermodel (required): without the declared alternating sign
there is no cancellation.**  On the strictly ascending 2-cell
`[0, 1, 2]` the signless composite has coefficient `2` at the vertex
`[0]` (and at every vertex), while the signed composite has
coefficient `0`.  Hence `d2_zero_general` is a theorem about the
DECLARED sign convention: the filler rule
`LadderGeneral.uniform_guarded_filler` does not force it, and this
signless INTEGER coefficient calculus does not satisfy it. -/
theorem signless_countermodel :
    ascB [0, 1, 2] = true ∧
    coeffN [0] (pushNoSign (bdNoSign [0, 1, 2])) = 2 ∧
    coeffN [1] (pushNoSign (bdNoSign [0, 1, 2])) = 2 ∧
    coeffN [2] (pushNoSign (bdNoSign [0, 1, 2])) = 2 ∧
    coeffN [0] (pushN (bdN [0, 1, 2])) = 0 ∧
    coeffN [1] (pushN (bdN [0, 1, 2])) = 0 ∧
    coeffN [2] (pushN (bdN [0, 1, 2])) = 0 := by
  refine ⟨by decide, by decide, by decide, by decide, by decide,
    by decide, by decide⟩

set_option maxRecDepth 8192 in
/-- The signless failure is not an artefact of dimension two: it
persists on the ascending 3-cell `[0, 1, 2, 3]`, where the signless
composite has coefficient `2` at the edge `[0, 1]`. -/
theorem signless_countermodel_dim3 :
    ascB [0, 1, 2, 3] = true ∧
    coeffN [0, 1] (pushNoSign (bdNoSign [0, 1, 2, 3])) = 2 ∧
    coeffN [0, 1] (pushN (bdN [0, 1, 2, 3])) = 0 := by
  refine ⟨by decide, by decide, by decide⟩

/-! ## 12. Countermodel: the ill-formed cell -/

/-- **Countermodel (required): the repeated-vertex list `[0, 0, 1]`.**
Stated exactly, because the expected failure does NOT occur.

* What fails: DISTINCTNESS.  Positions `0` and `1` give the same facet,
  so `eraseIdx_inj_of_asc` is false without `ascB`; the codimension-two
  slot of `[0]` collects FOUR ordered pairs instead of the two of an
  ascending cell (`[0, 1, 2]`, shown alongside), so the pairing is no
  longer a perfect matching on faces.  The boundary chain is degenerate
  as well: `[0, 1]` is a facet, yet its coefficient in the boundary is
  `0`, so the boundary of the pseudo-cell forgets a face.
* What does NOT fail: the coefficientwise composite still vanishes at
  every face — the four terms cancel in two pairs.  The pairing
  argument never required distinctness.  This is why
  `d2_zero_unrestricted` is provable, and why the `ascB` hypothesis of
  `d2_zero_general` is recorded rather than used.

The guarded calculus refuses this pseudo-cell for the separate reason
proved in `LadderGeneral.pseudo_cell_countermodel`. -/
theorem illformed_countermodel :
    ascB [0, 0, 1] = false ∧
    ([0, 0, 1] : List Nat).eraseIdx 0
      = ([0, 0, 1] : List Nat).eraseIdx 1 ∧
    [0, 1] ∈ facets [0, 0, 1] ∧
    coeffN [0, 1] (bdN [0, 0, 1]) = 0 ∧
    ((pushN (bdN [0, 0, 1])).filter (fun p => p.2 == [0])).length = 4 ∧
    ((pushN (bdN [0, 1, 2])).filter (fun p => p.2 == [0])).length = 2 ∧
    coeffN [0] (pushN (bdN [0, 0, 1])) = 0 ∧
    coeffN [1] (pushN (bdN [0, 0, 1])) = 0 := by
  refine ⟨by decide, by decide, by decide, by decide, by decide,
    by decide, by decide, by decide⟩

end BoundaryCancellation
