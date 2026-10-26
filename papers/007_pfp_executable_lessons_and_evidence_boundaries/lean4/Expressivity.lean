-- Vendored for Companion 007 from lean4/Expressivity.lean at commit
-- 52cb5457f6c485ba548cfd292f6012a941ed22cf.
-- This comment is the only change from that source file.

/-!
# Inc 4 Q1-A: `expressivityNorm` on `Q¹_n`

The Lean side of the Symbol Game expressivity norm, lined up with the Rust
`omega_symbol_game::expressivity::norm`.

## Carrier

We model a Symbol-Game expressivity problem at level `n` as a finite list of
overlap discrepancies `h : List Int`. Each entry is the integer discrepancy
on one overlap of the declared nerve. The Rust crate keeps the rational
representative; here we work over `Int` because the verdict trichotomy and
the grammar ceiling are integer-valued.

## Norm

`expressivityNorm h := Σ_e |h e|`.

This is the rational `ℓ¹` mass `‖h_n‖_1` of the C¹ defect cochain, computed on
a *chosen canonical representative*. It does NOT descend to the quotient `Q¹_n`:
it is invariant only under the kernel of `d⁰` (a constant potential, where
`d⁰ c = (c.tgt - c.src) = 0` leaves every entry fixed), NOT under a general
`δ ∈ im d⁰`, since a non-constant potential changes the per-entry `natAbs` and
hence the sum. The Rust S2 AT witnesses the constant-gauge invariance and
exhibits a non-constant potential that shifts the value.

## Firewall

This file is the *definition*. Authority is not minted here. The
companion file `GrammarCeiling.lean` proves the bound; the sealed
terminalizer in `omega_sweep_kernel` is the only authority surface.
-/

namespace OmegaCosmology.SymbolGame

/-- `expressivityNorm h := Σ |h e|` — the rational ℓ¹ mass of the C¹
    defect cochain `h_n`. -/
def expressivityNorm (h : List Int) : Nat :=
  h.foldr (fun x acc => x.natAbs + acc) 0

/-- The empty problem has zero norm. -/
theorem expressivityNorm_nil : expressivityNorm [] = 0 := rfl

/-- The norm of a cons is the head plus the tail. -/
theorem expressivityNorm_cons (x : Int) (xs : List Int) :
    expressivityNorm (x :: xs) = x.natAbs + expressivityNorm xs := rfl

/-- The norm is non-negative (it lives in `Nat`). -/
theorem expressivityNorm_nonneg (h : List Int) : 0 ≤ expressivityNorm h := by
  exact Nat.zero_le _

end OmegaCosmology.SymbolGame
