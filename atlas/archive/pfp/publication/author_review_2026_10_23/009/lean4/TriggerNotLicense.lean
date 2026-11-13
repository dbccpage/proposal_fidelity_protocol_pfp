-- Copied without change from lean4/TriggerNotLicense.lean in the repository
-- at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf.
import RuntimeLimits
/-!
# Paper 043, T4: a lift trigger is not a lift licence

The concrete source below has an active, populated trigger but zero lift
budget.  The resulting theorem is a finite non-implication countermodel.  It is
not a universal authority theorem and it does not claim that triggers can
never accompany independently licensed lifts.
-/

namespace PaperER007

open SnSymbolGameAndPackets

/-- A concrete finite source at which the lift budget is exhausted. -/
def zeroBudgetTriggeredSource : SLevel :=
  { n := 3
    symbols := 2
    operators := 1
    packetFamilies := 1
    witnesses := 1
    liftBudget := 0 }

/-- A populated trigger at `zeroBudgetTriggeredSource`.  Both diagnostic flags
are active; neither flag is itself a lift licence. -/
def populatedZeroBudgetTrigger : LiftTrigger zeroBudgetTriggeredSource :=
  { missingStructure := true
    residualNonzero := true }

/-- Strict budget decrease is impossible from any zero-budget source. -/
theorem zero_budget_blocks_every_licensed_lift
    (source : SLevel) (hZero : source.liftBudget = 0) :
    ∀ target : SLevel, ¬ LicensedLift source target := by
  intro target lift
  have hDrop := lift.budget_drops
  rw [hZero] at hDrop
  exact Nat.not_lt_zero target.liftBudget hDrop

theorem concrete_zero_budget_trigger_is_populated :
    populatedZeroBudgetTrigger.missingStructure = true ∧
      populatedZeroBudgetTrigger.residualNonzero = true := by
  exact ⟨rfl, rfl⟩

/-- No target can form a `LicensedLift` from the exhibited source. -/
theorem concrete_zero_budget_trigger_has_no_licensed_target :
    ¬ ∃ target : SLevel, LicensedLift zeroBudgetTriggeredSource target := by
  intro hTarget
  rcases hTarget with ⟨target, lift⟩
  exact zero_budget_blocks_every_licensed_lift
    zeroBudgetTriggeredSource rfl target lift

/-- The complete finite countermodel packages the zero budget, populated
trigger, and absence of every licensed target in one statement. -/
theorem exists_populated_zero_budget_trigger_without_license :
    ∃ (source : SLevel) (trigger : LiftTrigger source),
      source.liftBudget = 0 ∧
        trigger.missingStructure = true ∧
        trigger.residualNonzero = true ∧
        ¬ ∃ target : SLevel, LicensedLift source target := by
  exact ⟨zeroBudgetTriggeredSource, populatedZeroBudgetTrigger,
    rfl, rfl, rfl, concrete_zero_budget_trigger_has_no_licensed_target⟩

#print axioms PaperER007.zero_budget_blocks_every_licensed_lift
#print axioms PaperER007.concrete_zero_budget_trigger_is_populated
#print axioms PaperER007.concrete_zero_budget_trigger_has_no_licensed_target
#print axioms PaperER007.exists_populated_zero_budget_trigger_without_license

end PaperER007
