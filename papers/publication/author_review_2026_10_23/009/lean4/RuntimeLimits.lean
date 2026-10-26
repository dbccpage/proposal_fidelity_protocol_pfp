-- Copied without change from lean4/RuntimeLimits.lean in the repository
-- at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf.
import SLevel
/-!
Runtime limit kernels for the S(n) / Symbol Game / packetization paper.

These lemmas turn roadmap limits into finite contract facts:
* a lift trigger is not a lift license,
* public prompt memory must be redacted,
* ranking and refusal calibration are diagnostics, not authority.
-/

namespace SnSymbolGameAndPackets

structure LiftTrigger (source : SLevel) where
  missingStructure : Bool
  residualNonzero : Bool
  sourceLevel : Nat := source.n

def sameLevelTarget (source : SLevel) : SLevel :=
  { source with symbols := source.symbols + 1 }

theorem same_level_target_not_licensed_lift (source : SLevel) :
    ¬ LicensedLift source (sameLevelTarget source) := by
  intro lift
  have hstep := lift.level_step
  change source.n = source.n + 1 at hstep
  exact Nat.succ_ne_self source.n hstep.symm

theorem trigger_alone_does_not_license_same_level_lift
    (source : SLevel) (_trigger : LiftTrigger source) :
    ¬ LicensedLift source (sameLevelTarget source) :=
  same_level_target_not_licensed_lift source

theorem no_budget_drop_blocks_licensed_lift
    (source target : SLevel) (hBudget : target.liftBudget = source.liftBudget) :
    ¬ LicensedLift source target := by
  intro lift
  have hdrop := lift.budget_drops
  rw [hBudget] at hdrop
  exact Nat.lt_irrefl source.liftBudget hdrop

structure PromptMemoryEvent where
  rawPromptPresent : Bool
  promptHashPresent : Bool
  familyIdPresent : Bool
  boundedMetadata : Bool
  deriving Repr

def PublicMemorySafe (event : PromptMemoryEvent) : Prop :=
  event.rawPromptPresent = false ∧
    event.promptHashPresent = true ∧
    event.familyIdPresent = true ∧
    event.boundedMetadata = true

def redactForPublicMemory (_event : PromptMemoryEvent) : PromptMemoryEvent :=
  { rawPromptPresent := false,
    promptHashPresent := true,
    familyIdPresent := true,
    boundedMetadata := true }

theorem redacted_prompt_memory_is_public_safe (event : PromptMemoryEvent) :
    PublicMemorySafe (redactForPublicMemory event) := by
  exact ⟨rfl, rfl, rfl, rfl⟩

theorem raw_prompt_blocks_public_memory
    (event : PromptMemoryEvent) (hRaw : event.rawPromptPresent = true) :
    ¬ PublicMemorySafe event := by
  intro hSafe
  have hNoRaw := hSafe.1
  rw [hRaw] at hNoRaw
  cases hNoRaw

theorem missing_hash_blocks_public_memory
    (event : PromptMemoryEvent) (hHash : event.promptHashPresent = false) :
    ¬ PublicMemorySafe event := by
  intro hSafe
  have hHashPresent := hSafe.2.1
  rw [hHash] at hHashPresent
  cases hHashPresent

structure PublicPromptMemoryLedger where
  publicEvents : Nat
  rawPromptEvents : Nat
  deriving Repr

def PublicLedgerRawFree (ledger : PublicPromptMemoryLedger) : Prop :=
  ledger.rawPromptEvents = 0

def appendPublicMemoryEvent
    (ledger : PublicPromptMemoryLedger) (event : PromptMemoryEvent) :
    PublicPromptMemoryLedger :=
  { publicEvents := ledger.publicEvents + 1,
    rawPromptEvents :=
      ledger.rawPromptEvents +
        (if event.rawPromptPresent then 1 else 0) }

theorem append_public_memory_event_increments_count
    (ledger : PublicPromptMemoryLedger) (event : PromptMemoryEvent) :
    (appendPublicMemoryEvent ledger event).publicEvents =
      ledger.publicEvents + 1 := by
  rfl

theorem append_safe_prompt_memory_preserves_raw_free
    (ledger : PublicPromptMemoryLedger) (event : PromptMemoryEvent)
    (hLedger : PublicLedgerRawFree ledger) (hEvent : PublicMemorySafe event) :
    PublicLedgerRawFree (appendPublicMemoryEvent ledger event) := by
  unfold PublicLedgerRawFree appendPublicMemoryEvent
  have hNoRaw := hEvent.1
  rw [hLedger, hNoRaw]
  rfl

theorem append_redacted_prompt_memory_preserves_raw_free
    (ledger : PublicPromptMemoryLedger) (event : PromptMemoryEvent)
    (hLedger : PublicLedgerRawFree ledger) :
    PublicLedgerRawFree
      (appendPublicMemoryEvent ledger (redactForPublicMemory event)) := by
  exact append_safe_prompt_memory_preserves_raw_free
    ledger (redactForPublicMemory event) hLedger
    (redacted_prompt_memory_is_public_safe event)

theorem append_raw_prompt_memory_raw_count_positive
    (ledger : PublicPromptMemoryLedger) (event : PromptMemoryEvent)
    (hLedger : PublicLedgerRawFree ledger)
    (hRaw : event.rawPromptPresent = true) :
    0 < (appendPublicMemoryEvent ledger event).rawPromptEvents := by
  unfold PublicLedgerRawFree at hLedger
  unfold appendPublicMemoryEvent
  rw [hLedger, hRaw]
  exact Nat.zero_lt_succ 0

structure RankSuggestion where
  hasRank : Bool
  hasRepairTemplate : Bool
  authorityEffect : AuthorityEffect
  deriving Repr

def diagnosticRankSuggestion (hasRank hasRepairTemplate : Bool) : RankSuggestion :=
  { hasRank,
    hasRepairTemplate,
    authorityEffect := AuthorityEffect.none }

theorem diagnostic_rank_suggestion_non_authority
    (hasRank hasRepairTemplate : Bool) :
    (diagnosticRankSuggestion hasRank hasRepairTemplate).authorityEffect =
      AuthorityEffect.none :=
  rfl

structure RefusalStats where
  benignTotal : Nat
  falseRefusals : Nat
  falseRefusalBudget : Nat
  deriving Repr

def CalibratedRefusal (stats : RefusalStats) : Prop :=
  stats.falseRefusals ≤ stats.falseRefusalBudget

def AutoimmuneExceeded (stats : RefusalStats) : Prop :=
  stats.falseRefusalBudget < stats.falseRefusals

theorem calibrated_refusal_not_autoimmune_exceeded
    (stats : RefusalStats) :
    CalibratedRefusal stats → ¬ AutoimmuneExceeded stats := by
  intro hCal hExceeded
  exact Nat.not_lt_of_ge hCal hExceeded

theorem zero_false_refusal_budget_forces_zero_false_refusals
    (stats : RefusalStats)
    (hBudget : stats.falseRefusalBudget = 0)
    (hCal : CalibratedRefusal stats) :
    stats.falseRefusals = 0 := by
  unfold CalibratedRefusal at hCal
  rw [hBudget] at hCal
  exact Nat.eq_zero_of_le_zero hCal

#print axioms SnSymbolGameAndPackets.same_level_target_not_licensed_lift
#print axioms SnSymbolGameAndPackets.trigger_alone_does_not_license_same_level_lift
#print axioms SnSymbolGameAndPackets.no_budget_drop_blocks_licensed_lift
#print axioms SnSymbolGameAndPackets.redacted_prompt_memory_is_public_safe
#print axioms SnSymbolGameAndPackets.raw_prompt_blocks_public_memory
#print axioms SnSymbolGameAndPackets.missing_hash_blocks_public_memory
#print axioms SnSymbolGameAndPackets.append_public_memory_event_increments_count
#print axioms SnSymbolGameAndPackets.append_safe_prompt_memory_preserves_raw_free
#print axioms SnSymbolGameAndPackets.append_redacted_prompt_memory_preserves_raw_free
#print axioms SnSymbolGameAndPackets.append_raw_prompt_memory_raw_count_positive
#print axioms SnSymbolGameAndPackets.diagnostic_rank_suggestion_non_authority
#print axioms SnSymbolGameAndPackets.calibrated_refusal_not_autoimmune_exceeded
#print axioms SnSymbolGameAndPackets.zero_false_refusal_budget_forces_zero_false_refusals

end SnSymbolGameAndPackets
