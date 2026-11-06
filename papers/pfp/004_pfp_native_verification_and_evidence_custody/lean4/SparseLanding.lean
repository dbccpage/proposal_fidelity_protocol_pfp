/-!
# Weighted Null-Space Property and Unique Sparse Landing (Paper 032 §5.4)

Finite mechanization of the weighted null-space property (NSP) and the unique
ℓ¹ landing for the canonical directed 3-cycle. This discharges the finite
instance of Paper 032 Theorem 5.3 (equivalently, part of the open obligation
`O-040i-5` recorded in legacy Paper 040i, which asks for exactly this
mechanization over an integer/rational carrier).

Setup. On the directed 3-cycle `0 →e₀ 1 →e₁ 2 →e₂ 0`, the repair gauge is
`W = im(δ) = { w : w₀ + w₁ + w₂ = 0 }`, so a coboundary is determined by
`(w₁, w₂)` with `w₀ = -(w₁ + w₂)`. For a support `S ⊆ {e₀,e₁,e₂}` and positive
weights `ω`, the weighted NSP at `S` is
    `Σ_{e∈S} ωₑ|wₑ|  <  Σ_{e∉S} ωₑ|wₑ|`   for every nonzero `w ∈ W`.

We mechanize, at `S = {e₀}`:
  * `nsp_e0_asymmetric`  — for `ω = (1,2,2)` the NSP holds for every nonzero coboundary;
  * `nsp_e0_uniform_fails` — for `ω = (1,1,1)` the NSP fails (a tie witness exists);
and the concrete landing consequence on the coset `{r : r₀+r₁+r₂ = 1}`:
  * `landing_cost_lower_bound`  — the weighted cost is `≥ 1`;
  * `landing_unique_asymmetric` — cost `= 1` forces `r = (1,0,0)` (unique landing);
  * `landing_uniform_tie`       — under uniform weights `(1,0,0)` and `(0,1,0)` both cost `1`.

All arithmetic is over `Int`; no Mathlib dependency.
-/

namespace SymbolGame

/-- Integer absolute value (self-contained; avoids a Mathlib dependency). -/
def iabs (x : Int) : Int := if x < 0 then -x else x

theorem iabs_nonneg (x : Int) : 0 ≤ iabs x := by
  unfold iabs; split <;> omega

theorem iabs_pos {x : Int} (hx : x ≠ 0) : 0 < iabs x := by
  unfold iabs; split <;> omega

theorem iabs_neg (x : Int) : iabs (-x) = iabs x := by
  unfold iabs; split <;> split <;> omega

theorem iabs_cases (x : Int) : iabs x = x ∨ iabs x = -x := by
  unfold iabs; split
  · exact Or.inr rfl
  · exact Or.inl rfl

theorem iabs_triangle (a b : Int) : iabs (a + b) ≤ iabs a + iabs b := by
  unfold iabs; split <;> split <;> split <;> omega

/-- **NSP holds (asymmetric weights).** For `ω = (1,2,2)` and `S = {e₀}`, every nonzero
coboundary `w = (-(w₁+w₂), w₁, w₂)` satisfies `1·|w₀| < 2·|w₁| + 2·|w₂|`. This is exactly
the hypothesis (NSP_S) of Theorem 5.3, so the ℓ¹ landing is unique. -/
theorem nsp_e0_asymmetric (w1 w2 : Int) (hne : w1 ≠ 0 ∨ w2 ≠ 0) :
    1 * iabs (-(w1 + w2)) < 2 * iabs w1 + 2 * iabs w2 := by
  have hneg : iabs (-(w1 + w2)) = iabs (w1 + w2) := iabs_neg (w1 + w2)
  have htri : iabs (w1 + w2) ≤ iabs w1 + iabs w2 := iabs_triangle w1 w2
  have hpos : 0 < iabs w1 + iabs w2 := by
    rcases hne with h | h
    · have := iabs_pos h; have := iabs_nonneg w2; omega
    · have := iabs_pos h; have := iabs_nonneg w1; omega
  rw [hneg]; omega

/-- **NSP fails (uniform weights).** For `ω = (1,1,1)` the witness `w = (2,-1,-1) ∈ W`
gives `1·|w₀| = 2 = |w₁| + |w₂|`, so the strict inequality `2 < 2` is false: the landing
ties and a tie policy is load-bearing. -/
theorem nsp_e0_uniform_fails :
    ∃ w1 w2 : Int, (w1 ≠ 0 ∨ w2 ≠ 0) ∧
      ¬ (1 * iabs (-(w1 + w2)) < 1 * iabs w1 + 1 * iabs w2) := by
  refine ⟨-1, -1, Or.inl (by decide), ?_⟩
  decide

/-- The weighted cost on the coset `{r : r₀+r₁+r₂ = 1}` with weights `(1,2,2)` is `≥ 1`. -/
theorem landing_cost_lower_bound (r0 r1 r2 : Int) (hcoset : r0 + r1 + r2 = 1) :
    1 ≤ 1 * iabs r0 + 2 * iabs r1 + 2 * iabs r2 := by
  have n0 := iabs_nonneg r0
  have n1 := iabs_nonneg r1
  have n2 := iabs_nonneg r2
  rcases iabs_cases r0 with h0 | h0 <;> rcases iabs_cases r1 with h1 | h1 <;>
    rcases iabs_cases r2 with h2 | h2 <;> omega

/-- **Unique landing (asymmetric weights).** On the coset `{r : r₀+r₁+r₂ = 1}` with
weights `(1,2,2)`, the minimum weighted cost `1` is attained only at `r = (1,0,0)`. -/
theorem landing_unique_asymmetric (r0 r1 r2 : Int) (hcoset : r0 + r1 + r2 = 1)
    (hmin : 1 * iabs r0 + 2 * iabs r1 + 2 * iabs r2 = 1) :
    r0 = 1 ∧ r1 = 0 ∧ r2 = 0 := by
  have n0 := iabs_nonneg r0
  have n1 := iabs_nonneg r1
  have n2 := iabs_nonneg r2
  have e1 : iabs r1 = 0 := by omega
  have e2 : iabs r2 = 0 := by omega
  have hr1 : r1 = 0 := by rcases iabs_cases r1 with h | h <;> omega
  have hr2 : r2 = 0 := by rcases iabs_cases r2 with h | h <;> omega
  exact ⟨by omega, hr1, hr2⟩

/-- **Tie (uniform weights).** `(1,0,0)` and `(0,1,0)` are distinct residuals of equal
weighted cost `1`, so the uniform-weight landing is not unique. -/
theorem landing_uniform_tie :
    (1 * iabs 1 + 1 * iabs 0 + 1 * iabs 0 = 1) ∧
    (1 * iabs 0 + 1 * iabs 1 + 1 * iabs 0 = 1) ∧
    (((1 : Int), (0 : Int), (0 : Int)) ≠ ((0 : Int), (1 : Int), (0 : Int))) := by
  refine ⟨by decide, by decide, by decide⟩

end SymbolGame
