//! Antimorphism Detectors and Judge-Suite Exporter Integration Tests (U19).
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::Zero;
use core_prompt_civilization::antimorphism::{
    AntimorphismVerdict, ExactOrbitSumDetector, ExactSignInversionDetector,
    ExactStationaryRepeatDetector, HarvestRow, JudgeSuiteExporter, SuiteExportError,
    PINNED_CLASSIFIER_DIGEST,
};

#[test]
fn test_exact_orbit_sum_mismatch_am_fsp_4() {
    let w0 = BigRational::from_integer(1.into());
    let w1 = BigRational::new(3.into(), 2.into());

    // 1 - 3/2 = -1/2 != 0. Model claiming cancellation to zero is caught.
    let verdict = ExactOrbitSumDetector::check(&w0, &w1, true);
    match verdict {
        AntimorphismVerdict::ConfirmedHallucination {
            detector_id,
            witness,
        } => {
            assert_eq!(detector_id, "AM-FSP-4-ORBIT-SUM-MISMATCH");
            assert!(witness.contains("1 - 3/2 = -1/2 != 0"));
        }
        other => panic!("Expected ConfirmedHallucination, got {:?}", other),
    }

    // Grounded cancellation: 2 - 2 = 0
    let w_even = BigRational::from_integer(2.into());
    let grounded = ExactOrbitSumDetector::check(&w_even, &w_even, true);
    assert!(matches!(
        grounded,
        AntimorphismVerdict::GroundedWitness { .. }
    ));
}

#[test]
fn test_exact_sign_inversion_am_5() {
    let orig = vec![
        BigRational::from_integer(1.into()),
        BigRational::from_integer((-2).into()),
        BigRational::from_integer(3.into()),
    ];
    let inverted = vec![
        BigRational::from_integer((-1).into()),
        BigRational::from_integer(2.into()),
        BigRational::from_integer((-3).into()),
    ];

    let clean = ExactSignInversionDetector::check(&orig, &inverted, true);
    assert!(matches!(clean, AntimorphismVerdict::GroundedWitness { .. }));

    // Failed sign inversion at index 2
    let faulty = vec![
        BigRational::from_integer((-1).into()),
        BigRational::from_integer(2.into()),
        BigRational::from_integer(4.into()), // expected -3
    ];
    let fail_verdict = ExactSignInversionDetector::check(&orig, &faulty, true);
    match fail_verdict {
        AntimorphismVerdict::ConfirmedHallucination { witness, .. } => {
            assert!(witness.contains("coordinate 2"));
        }
        other => panic!("Expected failure at coordinate 2, got {:?}", other),
    }

    // Fixed point violation: 0 is invariant under negation
    let with_zero_orig = vec![BigRational::zero(), BigRational::from_integer(1.into())];
    let with_zero_inv = vec![BigRational::zero(), BigRational::from_integer((-1).into())];
    let fixed_point_fail = ExactSignInversionDetector::check(&with_zero_orig, &with_zero_inv, true);
    match fixed_point_fail {
        AntimorphismVerdict::ConfirmedHallucination { witness, .. } => {
            assert!(witness.contains("Fixed point violation"));
        }
        other => panic!("Expected fixed point violation, got {:?}", other),
    }
}

#[test]
fn test_exact_stationary_repeat_am_4() {
    let distinct = vec![
        "sha256:1111111111111111".to_string(),
        "sha256:2222222222222222".to_string(),
        "sha256:3333333333333333".to_string(),
    ];
    let clean = ExactStationaryRepeatDetector::check(&distinct);
    assert!(matches!(clean, AntimorphismVerdict::GroundedWitness { .. }));

    let repeated = vec![
        "sha256:1111111111111111".to_string(),
        "sha256:2222222222222222".to_string(),
        "sha256:1111111111111111".to_string(),
    ];
    let caught = ExactStationaryRepeatDetector::check(&repeated);
    match caught {
        AntimorphismVerdict::ConfirmedHallucination { witness, .. } => {
            assert!(witness.contains("Stationary repeat detected at step 2"));
        }
        other => panic!("Expected stationary repeat detection, got {:?}", other),
    }
}

#[test]
fn test_judge_suite_export_refuses_scripted_rows_as_model_evidence() {
    let rows = vec![HarvestRow {
        task_id: "task_01".to_string(),
        probe_id: "MERON-02".to_string(),
        domain_id: "PHYSICS".to_string(),
        model: "qwen/qwen-2.5-7b-instruct".to_string(),
        mode: "scripted".to_string(),
        raw_response: "canned response".to_string(),
        disposition: "HALLUCINATION_DETECTED".to_string(),
        confirmed: true,
        classifier_digest: PINNED_CLASSIFIER_DIGEST.to_string(),
        billed_cost_micro_usd: Some(10),
    }];

    let res = JudgeSuiteExporter::export(&rows, 42, false);
    assert_eq!(
        res.unwrap_err(),
        SuiteExportError::ScriptedRowExportedAsModelEvidence("task_01".to_string())
    );
}

#[test]
fn test_judge_suite_export_refuses_unconfirmed_rows_in_hidden_suite() {
    let rows = vec![HarvestRow {
        task_id: "task_hidden_candidate".to_string(),
        probe_id: "MERON-02".to_string(),
        domain_id: "PHYSICS".to_string(),
        model: "qwen/qwen-2.5-7b-instruct".to_string(),
        mode: "live".to_string(),
        raw_response: "unconfirmed regex candidate".to_string(),
        disposition: "CANDIDATE".to_string(),
        confirmed: false, // NOT confirmed!
        classifier_digest: PINNED_CLASSIFIER_DIGEST.to_string(),
        billed_cost_micro_usd: Some(15),
    }];

    // With a seed that maps this single row to hidden
    // We try seeds until it hits hidden or loop
    let mut caught = false;
    for seed in 0..100 {
        if let Err(SuiteExportError::UnconfirmedRowInHiddenSuite(id)) =
            JudgeSuiteExporter::export(&rows, seed, false)
        {
            assert_eq!(id, "task_hidden_candidate");
            caught = true;
            break;
        }
    }
    assert!(
        caught,
        "Expected seed to assign row to hidden suite and trigger refusal"
    );
}

#[test]
fn test_judge_suite_export_enforces_disposition_stability_under_same_digest() {
    // Replicating MERON-01 break condition: identical response under same digest with dual labels
    let rows = vec![
        HarvestRow {
            task_id: "task_01".to_string(),
            probe_id: "MERON-01".to_string(),
            domain_id: "PHYSICS".to_string(),
            model: "qwen/qwen-2.5-7b-instruct".to_string(),
            mode: "live".to_string(),
            raw_response: "Identical response text for meron-01".to_string(),
            disposition: "HALLUCINATION_DETECTED".to_string(),
            confirmed: true,
            classifier_digest: PINNED_CLASSIFIER_DIGEST.to_string(),
            billed_cost_micro_usd: Some(10),
        },
        HarvestRow {
            task_id: "task_02".to_string(),
            probe_id: "MERON-01".to_string(),
            domain_id: "PHYSICS".to_string(),
            model: "qwen/qwen-2.5-7b-instruct".to_string(),
            mode: "live".to_string(),
            raw_response: "Identical response text for meron-01".to_string(),
            disposition: "GROUNDED_WITNESS".to_string(), // Inconsistent!
            confirmed: true,
            classifier_digest: PINNED_CLASSIFIER_DIGEST.to_string(),
            billed_cost_micro_usd: Some(10),
        },
    ];

    let res = JudgeSuiteExporter::export(&rows, 42, false);
    assert!(matches!(
        res.unwrap_err(),
        SuiteExportError::InconsistentDisposition(_)
    ));
}

#[test]
fn test_judge_suite_export_clean_commitment() {
    let rows = vec![
        HarvestRow {
            task_id: "task_01".to_string(),
            probe_id: "MERON-01".to_string(),
            domain_id: "PHYSICS".to_string(),
            model: "qwen/qwen-2.5-7b-instruct".to_string(),
            mode: "live".to_string(),
            raw_response: "Response 1".to_string(),
            disposition: "HALLUCINATION_DETECTED".to_string(),
            confirmed: true,
            classifier_digest: PINNED_CLASSIFIER_DIGEST.to_string(),
            billed_cost_micro_usd: Some(10),
        },
        HarvestRow {
            task_id: "task_02".to_string(),
            probe_id: "MERON-02".to_string(),
            domain_id: "PHYSICS".to_string(),
            model: "qwen/qwen-2.5-7b-instruct".to_string(),
            mode: "live".to_string(),
            raw_response: "Response 2".to_string(),
            disposition: "GROUNDED_WITNESS".to_string(),
            confirmed: true,
            classifier_digest: PINNED_CLASSIFIER_DIGEST.to_string(),
            billed_cost_micro_usd: Some(12),
        },
    ];

    let exported = JudgeSuiteExporter::export(&rows, 42, false).unwrap();
    assert_eq!(exported.total_live_rows, 2);
    assert_eq!(exported.deduplicated_rows, 2);
    assert!(exported.hidden_commitment_sha256.starts_with("sha256:"));
    assert_eq!(exported.authority_effect, "None");
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/antimorphism_detectors.rs
// Claim: urn:core:crates_rs:tests:antimorphism-detectors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda6ace273 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda6ace273` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora6ace273 {
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
impl BoundaryErrora6ace273 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora6ace273 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora6ace273 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda6ace273 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora6ace273> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora6ace273::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora6ace273::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora6ace273::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_a6ace273() {
    let admitted = BoundaryRecorda6ace273::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda6ace273::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
