import SLevel
/-!
Constructive count-shadow semantics for a PaperER007 lift patch.

The construction derives the three fields of the existing `LicensedLift` from
positive patch cost, source-budget applicability, and a nonempty declared
structural addition.  It is not a proof of full GTOC licensing, preservation of
arbitrary semantics, or non-destruction outside these declared counters.
-/

namespace PaperER007

open SnSymbolGameAndPackets

structure LiftPatch where
  addedSymbols : Nat
  addedOperators : Nat
  addedPacketFamilies : Nat
  addedWitnesses : Nat
  cost : Nat
  cost_positive : 0 < cost
  nonempty_structural_addition :
    0 < addedSymbols + addedOperators + addedPacketFamilies + addedWitnesses

def LiftPatch.Applicable (patch : LiftPatch) (source : SLevel) : Prop :=
  patch.cost ≤ source.liftBudget

def applyLift (source : SLevel) (patch : LiftPatch)
    (_hApplicable : patch.Applicable source) : SLevel :=
  { n := source.n + 1
    symbols := source.symbols + patch.addedSymbols
    operators := source.operators + patch.addedOperators
    packetFamilies := source.packetFamilies + patch.addedPacketFamilies
    witnesses := source.witnesses + patch.addedWitnesses
    liftBudget := source.liftBudget - patch.cost }

theorem applyLift_advances_level (source : SLevel) (patch : LiftPatch)
    (hApplicable : patch.Applicable source) :
    (applyLift source patch hApplicable).n = source.n + 1 :=
  rfl

theorem applyLift_strictly_decreases_budget
    (source : SLevel) (patch : LiftPatch)
    (hApplicable : patch.Applicable source) :
    (applyLift source patch hApplicable).liftBudget < source.liftBudget := by
  change source.liftBudget - patch.cost < source.liftBudget
  unfold LiftPatch.Applicable at hApplicable
  have hCost := patch.cost_positive
  omega

theorem applyLift_increases_declared_mass
    (source : SLevel) (patch : LiftPatch)
    (hApplicable : patch.Applicable source) :
    source.declaredMass < (applyLift source patch hApplicable).declaredMass := by
  simp only [SLevel.declaredMass, applyLift]
  have hAddition := patch.nonempty_structural_addition
  omega

theorem applyLift_is_licensed (source : SLevel) (patch : LiftPatch)
    (hApplicable : patch.Applicable source) :
    LicensedLift source (applyLift source patch hApplicable) := by
  exact
    { level_step := applyLift_advances_level source patch hApplicable
      budget_drops := applyLift_strictly_decreases_budget source patch hApplicable
      declares_new_structure :=
        applyLift_increases_declared_mass source patch hApplicable }

#print axioms PaperER007.applyLift_advances_level
#print axioms PaperER007.applyLift_strictly_decreases_budget
#print axioms PaperER007.applyLift_increases_declared_mass
#print axioms PaperER007.applyLift_is_licensed

end PaperER007
