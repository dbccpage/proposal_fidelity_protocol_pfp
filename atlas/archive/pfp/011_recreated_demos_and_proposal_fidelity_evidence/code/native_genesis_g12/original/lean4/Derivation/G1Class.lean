import Derivation.LocalStrategy

/-!
# G1 inside the declared local finite-alphabet class

This module names the class-relative exclusion separately from the class
definition.  The proof uses `finite_local_not_clears`, whose collision is
obtained from `CapacityBound.capacity_bound` at the derived threshold
`k ^ (2 * d + 1) + 2 * d + 2`.

The conclusion is not unrestricted G1 and does not change the inherited
closure-policy obligation.
-/

namespace G1Class

open LocalFiniteAlphabet

/-- The strongest target form supported by the definitions.  The
identity-grade premise from the draft is unnecessary: finite locality
already prevents clearing every inherited obstruction. -/
theorem local_strategy_cycle_impossible {d : Nat} (S : LocalStrategy d)
    (k : Nat) (hfinite : FiniteDeclaration k S) :
    ¬ (Fires S ∧ Clears S ∧ ¬ RecurringImport S) := by
  intro hcycle
  exact (finite_local_not_clears S k hfinite) hcycle.2.1

/-- Named G1 class terminal: the inherited challenge fires, while every
fixed finite-alphabet local response fails to clear all chain lengths. -/
theorem g1_class_exclusion {d : Nat} (S : LocalStrategy d) (k : Nat)
    (hfinite : FiniteDeclaration k S) :
    Fires S ∧ ¬ Clears S ∧
      ¬ (Fires S ∧ Clears S ∧ ¬ RecurringImport S) :=
  g1_local_finite_alphabet_class S k hfinite

/-- G3 does not follow from the post-repair `Clears` predicate: the
one-time valued rule clears every inherited pair while the pre-repair
reflective family still fires.  A theorem relating repair power to the
absence of future challenges needs an additional state-transition
hypothesis not present in this class. -/
theorem clears_does_not_imply_not_fires :
    ∃ S : LocalStrategy 0, Clears S ∧ Fires S :=
  ⟨valued, valued_clears, fires_every_strategy valued⟩

end G1Class
