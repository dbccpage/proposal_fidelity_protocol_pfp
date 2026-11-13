import Derivation.Basic

/-!
# Finite counting laws

The termination law for the no-supply variant: the imposed-requirement
count strictly increases with every accepted separation round and is
bounded by the number of unordered pairs, so any run without supply has
length at most that bound.
-/

namespace Derivation

/-- A strictly increasing `Nat`-valued measure dominates its index. -/
theorem index_le_strict_mono (f : Nat → Nat) (L : Nat)
    (hstrict : ∀ i, i + 1 < L → f i < f (i + 1)) :
    ∀ i, i < L → i ≤ f i := by
  intro i
  induction i with
  | zero => intro _; exact Nat.zero_le _
  | succ n ih =>
      intro h
      have hn : n < L := Nat.lt_of_succ_lt h
      have h1 : f n < f (n + 1) := hstrict n h
      have h2 : n ≤ f n := ih hn
      omega

/-- Termination law: a run whose measure strictly increases every round and
never exceeds `B` has at most `B + 1` rounds. -/
theorem strict_bounded_length (f : Nat → Nat) (L B : Nat)
    (hstrict : ∀ i, i + 1 < L → f i < f (i + 1))
    (hbound : ∀ i, i < L → f i ≤ B) : L ≤ B + 1 := by
  by_cases h : L ≤ B + 1
  · exact h
  · have hlt : B + 1 < L := Nat.lt_of_not_le h
    have h1 : B + 1 ≤ f (B + 1) :=
      index_le_strict_mono f L hstrict (B + 1) hlt
    have h2 : f (B + 1) ≤ B := hbound (B + 1) hlt
    omega

/-- Instantiation shape used by the engine: with `n` admitted data the
requirement count is bounded by `n * (n - 1) / 2`, so a closed-system run
(endogenous generator only, external continuation policy disabled) has at
most `n * (n - 1) / 2 + 1` states, i.e. at most `n * (n - 1) / 2`
accepted separation rounds.

Conditional: this law assumes strict growth and boundedness of the
measure along the run.  That the engine's accepted separation rounds
satisfy both hypotheses (each accepted round imposes exactly one new
requirement over a fixed datum count) is discharged computationally for
the exported runs; a Lean theorem connecting the hypotheses to the
transition system itself is not proved here. -/
theorem no_supply_round_bound (f : Nat → Nat) (L n : Nat)
    (hstrict : ∀ i, i + 1 < L → f i < f (i + 1))
    (hbound : ∀ i, i < L → f i ≤ n * (n - 1) / 2) :
    L ≤ n * (n - 1) / 2 + 1 :=
  strict_bounded_length f L (n * (n - 1) / 2) hstrict hbound

/-- The requirement language of a regime with `n` data: the canonical
enumeration of ordered pairs `(i, j)` with `i < j < n`. -/
def allPairs : Nat → List (Nat × Nat)
  | 0 => []
  | n + 1 => allPairs n ++ (List.range n).map (fun i => (i, n))

/-- The requirement language is finite with exactly `n * (n - 1) / 2`
elements (stated multiplicatively to stay division-free): the endogenous
generator can issue at most this many distinct requirements before its
fixpoint. -/
theorem allPairs_length (n : Nat) :
    2 * (allPairs n).length = n * (n - 1) := by
  induction n with
  | zero => rfl
  | succ m ih =>
      have hexp : (allPairs (m + 1)).length = (allPairs m).length + m := by
        simp [allPairs]
      rw [hexp]
      have hsq : (m + 1) * (m + 1 - 1) = m * (m - 1) + 2 * m := by
        cases m with
        | zero => rfl
        | succ k =>
            simp only [Nat.succ_sub_one, Nat.succ_mul, Nat.mul_succ]
            generalize k * k = a
            omega
      omega

end Derivation
