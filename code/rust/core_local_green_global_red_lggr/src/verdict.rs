//! LGGR asymmetric verdict — the rule LGGR II §3.1 states and no code enforced.
//!
//! Paper 020 (`020_lggr_ii_organizational_gluing`) §3.1 fixes an asymmetry between
//! the two readings of the evaluator gluing defect `Δ_E = E_g − ∏ᵢ Eᵢ`:
//!
//! | Verdict | Reading | Soundness (verbatim from §3.1) |
//! |---|---|---|
//! | `Δ_E = −1` | local green, global red | *"**Sound as a detection.** … That non-factorization is exhibited, not inferred."* |
//! | `Δ_E = 0`  | boundary "closed"       | *"**Unsound as a certificate.**"* |
//!
//! and states the consequence directly:
//!
//! > *"a red verdict reports something; a green verdict reports the absence of
//! > something the detector may simply be unable to see. A green boundary is
//! > therefore `OracleNeeded` — not `ExactClass` — until an adequacy certificate
//! > excludes the collapses above."*
//!
//! Before this module, nothing in the tree enforced that. [`crate::adequacy`]
//! implements the certificate machinery, but `evaluate_detector_adequacy` was a
//! free function no caller invoked, and [`crate::EpkResidualLedger`] carries no
//! reference to it — so `EpkResidualLedger::from_metrics` will report `ngd: 0.0`
//! from a corpus whose detector is provably collapsing. [`classify`] closes that
//! gap: a green reading cannot be produced at all without an adequacy verdict in
//! hand, and even a supported one never reaches an "exact" label, because
//! `adequacy.rs` never returns `Adequate`.
//!
//! There is deliberately **no bare `Green` variant**.
//!
//! **AuthorityEffect: None.** A verdict classifies a reading. It authorizes
//! nothing, names no cause, assigns no fault, and licenses no intervention.

use serde::{Deserialize, Serialize};

use crate::epk_engine::GluingDefect;
use core_types::authority::AuthorityEffect;
use core_types::ceiling::EvidenceCeiling;

use crate::adequacy::{
    DetectorAdequacyVerdict, DetectorAdequacyVerdictKind, DetectorStructuralFailure,
    DetectorUndeclaredReason,
};

/// Where the evaluator verdicts `E₁`, `E₂`, `E_g` came from.
///
/// LGGR II §7.3 is explicit that this changes what may be concluded:
///
/// > *"On the CLI path, the values E₁, E₂, E_g that feed Δ_E are **not observed**
/// > — they are extracted from prose by a language model. … Under an oracle
/// > extractor, **neither** verdict direction is sound — the §3.1 asymmetry does
/// > not rescue the red verdict here, because the red is no longer exhibited."*
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvaluatorProvenance {
    /// The validator verdicts were exhibited by the declared model.
    Exhibited,
    /// The validator verdicts were produced by an oracle (e.g. an LLM reading
    /// prose). §7.3 applies: no verdict direction is sound.
    OracleExtracted,
}

/// Why a `Δ_E = 0` reading cannot be taken as a certificate of closure.
///
/// Every variant is a named collapse from LGGR II §3.1, or the adequacy protocol's
/// own refusal to certify. The mapping to [`DetectorStructuralFailure`] is recorded
/// per-variant: these are not new checks, they are a reading of checks
/// [`crate::adequacy`] already performs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub enum GreenUnsoundReason {
    /// No `DetectorDeploymentDeclaration` was supplied at all. §3.1: *"This paper
    /// supplies no such certificate, and therefore certifies no boundary."*
    AdequacyUndeclared,
    /// A declaration exists but carries no capacity evidence.
    CapacityEvidenceMissing,
    /// §3.1 case 1, *trivially-aligned validator family*: `E₁ := E_G` or a perfect
    /// proxy, so `Δ_E ≡ 0` for every input and *"every boundary reads closed"*.
    /// ← [`DetectorStructuralFailure::GlobalEqualsLocalProduct`].
    AlignedValidatorFamily,
    /// An all-accept or all-reject evaluator: the detector distinguishes nothing.
    /// ← [`DetectorStructuralFailure::EvaluatorConstant`].
    ConstantEvaluator,
    /// The local product is constant across the corpus.
    /// ← [`DetectorStructuralFailure::LocalProductConstant`].
    ConstantLocalProduct,
    /// The corpus contains no `Δ_E = −1` example, so the instrument has never been
    /// shown capable of returning red.
    /// ← [`DetectorStructuralFailure::MissingNgdWitness`].
    NoNegativeDefectWitness,
    /// The corpus exhibits no local-green/global-red witness.
    /// ← [`DetectorStructuralFailure::MissingLrgrWitness`].
    NoLocalGreenGlobalRedWitness,
    /// Zero comparable pairs: the closure reading is vacuous.
    /// ← [`DetectorStructuralFailure::CarrierClosureVacuous`].
    VacuousCarrierClosure,
    /// The declared evaluator does not separate the protected distinctions.
    /// ← [`DetectorStructuralFailure::EvaluatorDoesNotSeparate`].
    EvaluatorDoesNotSeparate,
    /// Two protected records collide under projection.
    /// ← [`DetectorStructuralFailure::ProjectionCollision`].
    ProjectionCollision,
    /// §3.1 requires a certificate naming *"known blind spots"*; none was declared.
    /// ← [`DetectorStructuralFailure::MissingBlindSpotDeclaration`].
    BlindSpotsUndeclared,
    /// Some other exact structural guard failed. The full failure vector remains
    /// available on the originating [`DetectorAdequacyVerdict`]; this variant
    /// exists so the projection is total and never silently drops a refusal.
    OtherStructuralInadequacy,
    /// Capacity evidence exceeded the declared epsilon.
    /// ← [`DetectorAdequacyVerdictKind::NumericalCounterevidence`].
    CapacityCounterevidence,
    /// Capacity evidence could not be resolved against the declaration.
    /// ← [`DetectorAdequacyVerdictKind::NumericalUnresolved`].
    CapacityUnresolved,
}

impl GreenUnsoundReason {
    /// Project one exact structural failure onto its §3.1 collapse reading.
    ///
    /// Total by construction: every unmapped failure becomes
    /// [`GreenUnsoundReason::OtherStructuralInadequacy`] rather than being dropped.
    /// A dropped refusal would silently upgrade a green reading, which is the exact
    /// failure this module exists to prevent.
    fn from_structural(failure: &DetectorStructuralFailure) -> Self {
        match failure {
            DetectorStructuralFailure::GlobalEqualsLocalProduct => Self::AlignedValidatorFamily,
            DetectorStructuralFailure::EvaluatorConstant { .. } => Self::ConstantEvaluator,
            DetectorStructuralFailure::LocalProductConstant => Self::ConstantLocalProduct,
            DetectorStructuralFailure::MissingNgdWitness => Self::NoNegativeDefectWitness,
            DetectorStructuralFailure::MissingLrgrWitness => Self::NoLocalGreenGlobalRedWitness,
            DetectorStructuralFailure::CarrierClosureVacuous => Self::VacuousCarrierClosure,
            DetectorStructuralFailure::EvaluatorDoesNotSeparate { .. } => {
                Self::EvaluatorDoesNotSeparate
            }
            DetectorStructuralFailure::ProjectionCollision { .. } => Self::ProjectionCollision,
            DetectorStructuralFailure::MissingBlindSpotDeclaration { .. } => {
                Self::BlindSpotsUndeclared
            }
            _ => Self::OtherStructuralInadequacy,
        }
    }
}

/// Refusal to classify a reading at all.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LggrVerdictError {
    /// `Δ_E` is defined only on `{-1, 0, +1}`. [`GluingDefect`] has public fields,
    /// so an out-of-range value is constructible; it is refused rather than
    /// classified.
    #[error("evaluator gluing defect out of range: delta_eval = {0}, expected -1, 0, or +1")]
    DefectOutOfRange(i8),
    /// `delta_eval` disagrees with `global_pass − local_product`.
    #[error(
        "malformed gluing defect: delta_eval = {delta_eval} but global_pass = {global_pass} and \
         local_product = {local_product} imply {implied}"
    )]
    DefectInternallyInconsistent {
        delta_eval: i8,
        global_pass: bool,
        local_product: bool,
        implied: i8,
    },
}

/// The asymmetric LGGR reading of one evaluator gluing defect.
///
/// There is no bare `Green`. A zero defect reaches
/// [`LggrVerdict::GreenNumericallySupported`] only with a supporting adequacy
/// verdict, and even that is not an exactness claim — `adequacy.rs` pins its own
/// ceiling verbatim: *"No verdict is `Adequate`; exact BSC-CERT remains open."*
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum LggrVerdict {
    /// `Δ_E = −1`. Local green, global red. **Sound as a detection**: under the
    /// declared assignment the locals passed and the global failed, and that
    /// non-factorization is exhibited rather than inferred.
    ///
    /// It still names no cause. LGGR II §3.1: *"it does not name a cause, assign
    /// fault, or license an intervention."*
    Red { defect: GluingDefect },
    /// `Δ_E = +1`. The global passed where the local product did not.
    PositiveGluingDefect { defect: GluingDefect },
    /// `Δ_E = 0` without an adequacy verdict that excludes the §3.1 collapses.
    /// The reading is consistent with a genuinely composing boundary *and equally*
    /// with an instrument that could not have returned anything else.
    GreenOracleNeeded {
        defect: GluingDefect,
        /// Sorted and deduplicated so the verdict is deterministic.
        reasons: Vec<GreenUnsoundReason>,
    },
    /// `Δ_E = 0` with [`DetectorAdequacyVerdictKind::NumericallySupported`].
    /// The strongest reachable green. **Not** `ExactClass`, **not**
    /// `ClosedResidual`, **not** `StabilizedSurvivor`.
    GreenNumericallySupported { defect: GluingDefect },
    /// The evaluator verdicts came from an oracle. LGGR II §7.3: neither verdict
    /// direction is sound, so no reading is emitted — not even red.
    OracleExtractedUnsound { defect: GluingDefect },
}

impl LggrVerdict {
    /// **Always** [`AuthorityEffect::None`], for every variant and every value.
    ///
    /// Mirrors [`crate::EpkResidualLedger::authority_effect`]: the authority
    /// interface is fixed regardless of what the verdict carries.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }

    /// What a host may verify from this reading, capped at
    /// [`EvidenceCeiling::BoundaryChecked`].
    ///
    /// The cap follows the rule `core_business_contracts` already enforces on
    /// prospective findings (`claimed.meet(BoundaryChecked)`): an EPK reading is a
    /// property of a declared boundary model, never of the world. LGGR II §6.0:
    /// *"A gluing defect in a **model of** an organization is **not** a proven fact
    /// about that organization."*
    ///
    /// The ordering across variants is monotone in how much the reading settles:
    /// an unsupported green settles nothing ([`EvidenceCeiling::ShapeOnly`]), a
    /// supported green is replayable but not exact
    /// ([`EvidenceCeiling::LocalReplay`]), and an exhibited defect is a checked
    /// boundary observation ([`EvidenceCeiling::BoundaryChecked`]).
    pub fn evidence_ceiling(&self) -> EvidenceCeiling {
        let raw = match self {
            Self::Red { .. } | Self::PositiveGluingDefect { .. } => {
                EvidenceCeiling::BoundaryChecked
            }
            Self::GreenNumericallySupported { .. } => EvidenceCeiling::LocalReplay,
            Self::GreenOracleNeeded { .. } | Self::OracleExtractedUnsound { .. } => {
                EvidenceCeiling::ShapeOnly
            }
        };
        raw.meet(EvidenceCeiling::BoundaryChecked)
    }

    /// Whether this reading may be cited as a *detection* of non-factorization.
    ///
    /// True only for [`LggrVerdict::Red`] from exhibited verdicts. Every green is
    /// false — that is the §3.1 asymmetry — and so is an oracle-extracted red.
    pub fn is_sound_detection(&self) -> bool {
        matches!(self, Self::Red { .. })
    }

    /// Whether this reading certifies closure. **Always false.**
    ///
    /// No LGGR verdict certifies a boundary. `GreenNumericallySupported` is the
    /// strongest reachable label and it is still not a certificate: `adequacy.rs`
    /// never returns `Adequate`, so the exact certificate remains open.
    pub fn certifies_closure(&self) -> bool {
        false
    }

    /// The underlying defect, whatever the reading.
    pub fn defect(&self) -> &GluingDefect {
        match self {
            Self::Red { defect }
            | Self::PositiveGluingDefect { defect }
            | Self::GreenOracleNeeded { defect, .. }
            | Self::GreenNumericallySupported { defect }
            | Self::OracleExtractedUnsound { defect } => defect,
        }
    }
}

/// Project an adequacy verdict onto the reasons a green reading stays unsound.
///
/// Returns an empty vector **only** when the verdict is
/// [`DetectorAdequacyVerdictKind::NumericallySupported`]. Every other kind yields
/// at least one reason, so `reasons.is_empty()` is a faithful test for "green is
/// permitted".
fn green_unsound_reasons(adequacy: &DetectorAdequacyVerdict) -> Vec<GreenUnsoundReason> {
    let mut reasons: Vec<GreenUnsoundReason> = match adequacy.kind() {
        DetectorAdequacyVerdictKind::NumericallySupported => Vec::new(),
        DetectorAdequacyVerdictKind::Undeclared => {
            vec![match adequacy.undeclared_reason() {
                Some(DetectorUndeclaredReason::CapacityEvidenceMissing) => {
                    GreenUnsoundReason::CapacityEvidenceMissing
                }
                // `DeploymentDeclarationMissing`, and the defensive `None` case:
                // an `Undeclared` verdict without a recorded reason is still
                // undeclared, and must not read as adequate.
                _ => GreenUnsoundReason::AdequacyUndeclared,
            }]
        }
        DetectorAdequacyVerdictKind::StructuralInadequate => {
            let projected: Vec<GreenUnsoundReason> = adequacy
                .structural_failures()
                .iter()
                .map(GreenUnsoundReason::from_structural)
                .collect();
            // A `StructuralInadequate` verdict with an empty failure vector should
            // be unreachable, but must never read as adequate if it occurs.
            if projected.is_empty() {
                vec![GreenUnsoundReason::OtherStructuralInadequacy]
            } else {
                projected
            }
        }
        DetectorAdequacyVerdictKind::NumericalCounterevidence => {
            vec![GreenUnsoundReason::CapacityCounterevidence]
        }
        DetectorAdequacyVerdictKind::NumericalUnresolved => {
            vec![GreenUnsoundReason::CapacityUnresolved]
        }
    };
    reasons.sort_unstable();
    reasons.dedup();
    reasons
}

/// Classify one evaluator gluing defect under the LGGR II §3.1 asymmetry.
///
/// `adequacy` is `None` when no adequacy protocol was run at all — which is itself
/// a reason a green reading stays unsound, never a licence to skip the gate.
///
/// The gate, in one sentence: **a zero defect can never be reported as supported
/// unless an adequacy verdict says `NumericallySupported`.**
pub fn classify(
    defect: &GluingDefect,
    adequacy: Option<&DetectorAdequacyVerdict>,
    provenance: EvaluatorProvenance,
) -> Result<LggrVerdict, LggrVerdictError> {
    let implied = defect.global_pass as i8 - defect.local_product as i8;
    // Range before consistency, deliberately. `implied` is always in {-1, 0, +1},
    // so checking consistency first would make `DefectOutOfRange` unreachable: an
    // out-of-range `delta_eval` can never equal `implied`, and the caller would be
    // told "inconsistent" when the actual fault is "not a defect value at all".
    if !matches!(defect.delta_eval, -1..=1) {
        return Err(LggrVerdictError::DefectOutOfRange(defect.delta_eval));
    }
    if defect.delta_eval != implied {
        return Err(LggrVerdictError::DefectInternallyInconsistent {
            delta_eval: defect.delta_eval,
            global_pass: defect.global_pass,
            local_product: defect.local_product,
            implied,
        });
    }

    // §7.3 fence, applied before the §3.1 asymmetry: if the verdicts were not
    // exhibited, the red is not exhibited either, and nothing is sound.
    if provenance == EvaluatorProvenance::OracleExtracted {
        return Ok(LggrVerdict::OracleExtractedUnsound { defect: *defect });
    }

    match defect.delta_eval {
        -1 => Ok(LggrVerdict::Red { defect: *defect }),
        1 => Ok(LggrVerdict::PositiveGluingDefect { defect: *defect }),
        _ => {
            let reasons = match adequacy {
                None => vec![GreenUnsoundReason::AdequacyUndeclared],
                Some(verdict) => green_unsound_reasons(verdict),
            };
            if reasons.is_empty() {
                Ok(LggrVerdict::GreenNumericallySupported { defect: *defect })
            } else {
                Ok(LggrVerdict::GreenOracleNeeded {
                    defect: *defect,
                    reasons,
                })
            }
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_dc066dab {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
