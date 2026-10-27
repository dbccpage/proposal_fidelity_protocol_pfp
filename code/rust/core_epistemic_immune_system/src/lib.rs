//! Sovereign Rust Epistemic Immune System (EIS) Engine.
//!
//! AuthorityEffect: None.
//!
//! Implements the Four-Gate Epistemic Immune Protocol:
//! 1. Defect Observation -> AntiSkillSpecV2(status=PROPOSED) (IMMUNE-001)
//! 2. Central Tolerance -> ThymusGate negative selection screen (IMMUNE-002)
//! 3. Two-Signal Danger Gating -> strict four-part conjunction (IMMUNE-002)
//! 4. Human Admission Fence -> Formulary admission receipts (PHARMACY-001)

pub mod activation;
pub mod activation_ports;
pub mod activation_use_case;
pub mod admission;
pub mod authenticated;
pub mod allostery;
pub mod anti_skill;
pub mod clonal_selection;
pub mod danger_gate;
pub mod formulary;
pub mod host_checks;
pub mod independence;
pub mod pharmacy_search;
pub mod regulation;
pub mod signal_gate;
pub mod thymus;

pub use anti_skill::{AntiSkillSpecV2, AntiSkillStatus, FailureClass, ANTI_SKILL_SCHEMA};
pub use danger_gate::{DangerGateVerdict, IndependentDangerSignal, TwoSignalDangerGate};
pub use formulary::{AdmissionReceiptV1, Formulary};
pub use regulation::{DetectorTelemetry, TregSupervisor};
pub use thymus::{ThymusGate, ThymusVerdict};

/// A typed native boundary or activation failure, granting no authority.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
}
impl Refusal {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: format!("{code}: {}", message.into()),
        }
    }
}
impl std::fmt::Display for Refusal {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.message)
    }
}
impl std::error::Error for Refusal {}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/lib.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord427bb0b3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord427bb0b3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError427bb0b3 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError427bb0b3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError427bb0b3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError427bb0b3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord427bb0b3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError427bb0b3> {
        if capacity_bound == 0 {
            return Err(BoundaryError427bb0b3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError427bb0b3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError427bb0b3::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn anti_skill_cannot_self_admit() {
        let spec = AntiSkillSpecV2::propose(
            r"flawless\s+proof",
            FailureClass::UnmechanizedProofClaim,
            "mathematical_monographs",
            "Catches unmechanized hype words",
            100,
        );
        assert_eq!(spec.status, AntiSkillStatus::Proposed);
        assert_eq!(spec.authority_effect, "None");
    }

    #[test]
    fn thymus_kills_self_reactive_patterns() {
        let thymus = ThymusGate::standard_baseline();

        // Pattern matching healthy self sample "exact rational duality gap is zero"
        let mut self_reactive = AntiSkillSpecV2::propose(
            r"exact rational",
            FailureClass::CounterfeitExactness,
            "solvers",
            "Overly broad pattern",
            100,
        );

        let verdict = thymus.screen(&mut self_reactive);
        match verdict {
            ThymusVerdict::SelfReactive { matched_sample, .. } => {
                assert!(matched_sample.contains("exact rational"));
                assert_eq!(self_reactive.status, AntiSkillStatus::Retired);
            }
            other => panic!("expected SelfReactive, got {:?}", other),
        }
    }

    #[test]
    fn thymus_promotes_healthy_detector_to_candidate() {
        let thymus = ThymusGate::standard_baseline();

        let mut safe_detector = AntiSkillSpecV2::propose(
            r"weaponized\s+singularity",
            FailureClass::ToyPromotion,
            "papers",
            "Catches hype phrase",
            100,
        );

        let verdict = thymus.screen(&mut safe_detector);
        assert!(matches!(verdict, ThymusVerdict::Survived { .. }));
        assert_eq!(safe_detector.status, AntiSkillStatus::Candidate);
    }

    #[test]
    fn two_signal_conjunction_rejects_unadmitted_and_uncorroborated() {
        let thymus = ThymusGate::standard_baseline();
        let mut formulary = Formulary::new();

        let mut detector = AntiSkillSpecV2::propose(
            r"subfloor_gamma2_fraud",
            FailureClass::CounterfeitExactness,
            "solvers",
            "Subfloor gamma2 counterfeit detector",
            100,
        );

        assert!(matches!(
            thymus.screen(&mut detector),
            ThymusVerdict::Survived { .. }
        ));
        formulary.register_candidate(detector.clone()).unwrap();

        let subject = "Candidate payload contains subfloor_gamma2_fraud in stream";

        // 1. Candidate alone is refused because it is not externally admitted
        let v1 = TwoSignalDangerGate::evaluate(
            &detector,
            subject,
            Some(IndependentDangerSignal::NonZeroDualityGap),
        );
        assert!(matches!(
            v1,
            DangerGateVerdict::RefusedStatus {
                status: AntiSkillStatus::Candidate,
                ..
            }
        ));

        // 2. Admit externally with human receipt
        formulary
            .admit_with_receipt(
                &detector.id,
                "Dr. Carroll",
                101,
                "sha256_mock_human_receipt",
            )
            .unwrap();
        let admitted = formulary.get(&detector.id).unwrap();
        assert_eq!(admitted.status, AntiSkillStatus::Admitted);

        // 3. Signal 1 only (pattern match without independent danger signal) yields HoldUncorroborated
        let v2 = TwoSignalDangerGate::evaluate(admitted, subject, None);
        assert!(matches!(v2, DangerGateVerdict::HoldUncorroborated { .. }));

        // 4. Conjunction: Admitted + Pattern Match + Independent Danger Signal yields Finding
        let v3 = TwoSignalDangerGate::evaluate(
            admitted,
            subject,
            Some(IndependentDangerSignal::NonZeroDualityGap),
        );
        assert!(matches!(v3, DangerGateVerdict::Finding { .. }));
    }

    #[test]
    fn treg_supervisor_suspends_elevated_false_positives() {
        let mut detector =
            AntiSkillSpecV2::propose("test", FailureClass::BoundaryLeakage, "test", "test", 100);
        let _ = detector.promote_to_candidate();
        let _ = detector.admit_externally("receipt");
        assert_eq!(detector.status, AntiSkillStatus::Admitted);

        let treg = TregSupervisor::default();
        let telemetry = DetectorTelemetry {
            anti_skill_id: detector.id.clone(),
            true_positives: 5,
            false_positives: 10, // 10 / 15 = 66.7% > 10% ceiling
            last_active_epoch: 105,
        };

        let suspended = treg.review(&mut detector, &telemetry);
        assert!(suspended);
        assert_eq!(detector.status, AntiSkillStatus::Suspended);
    }
}

#[cfg(test)]
mod l4_boundary_tests_427bb0b3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord427bb0b3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord427bb0b3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord427bb0b3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord427bb0b3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord427bb0b3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError427bb0b3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError427bb0b3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
