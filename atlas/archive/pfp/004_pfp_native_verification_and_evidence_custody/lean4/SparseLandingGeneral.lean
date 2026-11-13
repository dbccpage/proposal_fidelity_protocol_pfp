/-!
# General Weighted-NSP Directional Positivity (Paper 032 §5.4, arbitrary dimension)

`SparseLanding.lean` mechanizes the unique sparse landing for the finite 3-cycle.
This module mechanizes the **dimension-general** crux of Theorem 5.3 over a
`List` carrier (any finite number of coordinates), Mathlib-free.

A repair direction `w` in the gauge is presented coordinate-wise as a list of
`Coord (weight, w, sgn, inS)`, where `weight ≥ 0` is the edge weight `ωₑ`, `sgn`
records the sign `σₑ = sign(r*ₑ)` on the optimal support `S` (`inS`), and off the
support the one-sided derivative contributes `|wₑ|`. Writing

    directional derivative   D  =  Σ_{e∈S} ωₑ σₑ wₑ + Σ_{e∉S} ωₑ |wₑ|
    NSP margin               M  =  Σ_{e∉S} ωₑ |wₑ| − Σ_{e∈S} ωₑ |wₑ|

the weighted null-space property is exactly `M > 0`. The theorems below prove,
for a list of any length:

- `term_le`            : per coordinate, `termM ≤ termD` (uses `σₑ wₑ ≥ −|wₑ|`);
- `margin_le_dirDeriv` : summing, `M ≤ D`;
- `dirDeriv_pos`       : hence `M > 0 ⟹ D > 0` — under the weighted NSP, every
                         nonzero gauge direction strictly increases the weighted
                         `L₁` norm to first order.

`dirDeriv_pos` is the general first-order fact behind Theorem 5.3 uniqueness: no
nonzero gauge direction is a descent-or-flat direction. The remaining convexity
closure (a minimizer has `D ≥ 0` in every gauge direction, and strict positivity
in every nonzero direction forces a unique minimizer) is the `[PROVED]` prose of
§5.4. Together with the finite instance of `SparseLanding.lean` this advances the
open obligation `O-040i-5`. Every theorem's axiom footprint is `{propext, Quot.sound}`.
-/

namespace SymbolGame.NSP

/-- Integer absolute value (self-contained). -/
def iabs (x : Int) : Int := if x < 0 then -x else x

/-- One coordinate of a repair direction: weight `ωₑ`, value `wₑ`, the optimal-support
sign `σₑ` (`sgn`, meaningful when `inS`), and support membership `inS`. -/
structure Coord where
  weight : Int
  w : Int
  sgn : Bool
  inS : Bool

/-- Directional-derivative contribution of a coordinate:
`ωₑ σₑ wₑ` on the support, `ωₑ |wₑ|` off it. -/
def termD (c : Coord) : Int :=
  if c.inS = true then (if c.sgn = true then c.weight * c.w else -(c.weight * c.w))
  else c.weight * iabs c.w

/-- NSP-margin contribution of a coordinate: `−ωₑ |wₑ|` on the support, `ωₑ |wₑ|` off it. -/
def termM (c : Coord) : Int :=
  if c.inS = true then -(c.weight * iabs c.w) else c.weight * iabs c.w

/-- Per-coordinate bound `termM ≤ termD`, from `σₑ wₑ ≥ −|wₑ|` and `ωₑ ≥ 0`. -/
theorem term_le (c : Coord) (hw : 0 ≤ c.weight) : termM c ≤ termD c := by
  have h1 : c.w ≤ iabs c.w := by unfold iabs; split <;> omega
  have h2 : (-(iabs c.w)) ≤ c.w := by unfold iabs; split <;> omega
  have m1 : c.weight * c.w ≤ c.weight * iabs c.w := Int.mul_le_mul_of_nonneg_left h1 hw
  have m2 : c.weight * (-(iabs c.w)) ≤ c.weight * c.w := Int.mul_le_mul_of_nonneg_left h2 hw
  have e2 : c.weight * (-(iabs c.w)) = -(c.weight * iabs c.w) := by rw [Int.mul_neg]
  unfold termD termM
  by_cases hin : c.inS = true <;> by_cases hsg : c.sgn = true <;> simp [hin, hsg] <;> omega

/-- The directional derivative `D = Σ termD` of a repair direction. -/
def dirDeriv : List Coord → Int
  | [] => 0
  | c :: cs => termD c + dirDeriv cs

/-- The NSP margin `M = Σ termM` of a repair direction. -/
def nspMargin : List Coord → Int
  | [] => 0
  | c :: cs => termM c + nspMargin cs

/-- Summing the per-coordinate bound: `M ≤ D` for a direction of any length. -/
theorem margin_le_dirDeriv (L : List Coord) (hw : ∀ c ∈ L, 0 ≤ c.weight) :
    nspMargin L ≤ dirDeriv L := by
  induction L with
  | nil => simp [dirDeriv, nspMargin]
  | cons c cs ih =>
    have hc := term_le c (hw c (by simp))
    have ih' := ih (fun x hx => hw x (by simp [hx]))
    simp only [dirDeriv, nspMargin]; omega

/-- **General weighted-NSP directional positivity.** If the NSP margin is positive
(the weighted null-space property), the directional derivative is positive: no
nonzero gauge direction is a descent-or-flat direction. This is the dimension-general
crux of Theorem 5.3. -/
theorem dirDeriv_pos (L : List Coord) (hw : ∀ c ∈ L, 0 ≤ c.weight)
    (hmargin : 0 < nspMargin L) : 0 < dirDeriv L := by
  have := margin_le_dirDeriv L hw
  omega

end SymbolGame.NSP
