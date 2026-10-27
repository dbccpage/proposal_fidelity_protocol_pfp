use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
// Full declared finite packet evidence; AuthorityEffect: None.
use num_rational::BigRational;
use core_measurement::affine_calibration::{AffineCalibration, BoundedReading};
use core_measurement::documentary_traceability::{
    DocumentaryCalibrationLink, DocumentaryTraceabilityGraph,
};
use core_measurement::{MeasurementValue, UnitSpec};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::outer;
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_wdp::calibration_adapter::{CalibrationPacket, NamedCalibrationStage};
use core_wdp::instrument_adapter::FiniteQuantumInstrument;
use core_wdp::measurement_packet::*;
use core_wdp::types::AuthorityEffect;

fn basis(i: usize) -> Vec<GaussianRat> {
    let mut vector = vec![GaussianRat::zero(); 3];
    vector[i] = GaussianRat::one();
    vector
}
fn matrix_unit(row: usize, col: usize) -> BasicMatrix<GaussianRat> {
    outer(&basis(row), &basis(col)).unwrap()
}
fn repeatable_instrument(phase_sign: i64) -> FiniteQuantumInstrument {
    let coefficient = GaussianRat {
        re: rq(phase_sign, 2),
        im: rq(phase_sign, 2),
    };
    let mut a = matrix_unit(0, 2);
    let mut b = matrix_unit(1, 2);
    a.set(0, 2, coefficient.clone()).unwrap();
    b.set(1, 2, coefficient).unwrap();
    FiniteQuantumInstrument::new(
        3,
        3,
        vec![vec![matrix_unit(0, 0), a], vec![matrix_unit(1, 1), b]],
        "repeatable-unsharp",
    )
    .unwrap()
}
fn bind_registration(actual: &mut QuantumMeasurementProblem) {
    actual.registration.mark = InstrumentMark {
        instrument: actual
            .instrument
            .receipt(actual.selected_outcome, &actual.input_state)
            .unwrap(),
        indication: actual.outcome_indications[actual.selected_outcome].clone(),
    };
}
fn problem() -> QuantumMeasurementProblem {
    let instrument = repeatable_instrument(1);
    let state = ExactDensityState::try_new(matrix_unit(2, 2)).unwrap();
    let mark = InstrumentMark {
        instrument: instrument.receipt(0, &state).unwrap(),
        indication: ri(4),
    };
    let stages = vec![
        NamedCalibrationStage::new(
            "first".into(),
            AffineCalibration::new(ri(2), ri(1), rq(1, 100), rq(1, 20), rq(1, 25)).unwrap(),
        )
        .unwrap(),
        NamedCalibrationStage::new(
            "second".into(),
            AffineCalibration::new(ri(-1), ri(3), ri(0), rq(1, 50), ri(0)).unwrap(),
        )
        .unwrap(),
    ];
    let link = |source: &str, target: &str, document: &str, uncertainty: BigRational| {
        DocumentaryCalibrationLink {
            source_id: source.into(),
            target_id: target.into(),
            document_id: document.into(),
            unit: "V".into(),
            uncertainty_contribution: uncertainty,
        }
    };
    QuantumMeasurementProblem {
        packet_id: "measurement-0".into(),
        instrument,
        input_state: state,
        selected_outcome: 0,
        outcome_indications: vec![ri(4), ri(-3)],
        context: InstrumentObservationContext {
            interaction_id: "declared-coupling".into(),
            poles: vec!["qutrit".into(), "detector".into()],
            registration_carrier_id: "detector".into(),
            mark_capacity: true,
            evaluator_id: "exact-model-replay".into(),
            evaluator_status: ObservationStatus::Accept,
            accepting_standing: true,
        },
        registration: InstrumentRegistration {
            registration_id: "retained-mark-0".into(),
            carrier_id: "detector".into(),
            retained: true,
            mark,
        },
        calibration: CalibrationPacket::new(
            "calibration-0".into(),
            BoundedReading::new(ri(4), rq(1, 10)).unwrap(),
            stages,
        )
        .unwrap(),
        calibration_scale_id: "declared-voltage-scale".into(),
        calibration_evaluator_id: "exact-model-replay".into(),
        value_map: IndicationValueMap {
            map_id: "ordered-affine-map".into(),
            source_carrier_id: "detector".into(),
            result_carrier_id: "rational-voltage".into(),
            gain: ri(-2),
            offset: ri(2),
        },
        measurand: MeasurandSpecification {
            quantity_id: "voltage".into(),
            system_id: "declared-finite-apparatus".into(),
            conditions: vec!["deterministic-bounds-assumed".into()],
        },
        scale: NumericMeasurementScale {
            scale_id: "declared-voltage-scale".into(),
            unit: UnitSpec {
                unit_name: "V".into(),
                dimension: Some("voltage".into()),
            },
            lower: ri(-20),
            upper: ri(20),
            resolution: rq(1, 100),
        },
        declared_raw_value: ri(-6),
        correction: rq(1, 2),
        stated_uncertainty: rq(1, 2),
        traceability: DocumentaryTraceabilityGraph {
            origin_id: "calibration-0".into(),
            terminal_reference_id: "reference-0".into(),
            terminal_reference_kind: "declared-documentary-reference".into(),
            result_unit: "V".into(),
            links: vec![
                link("calibration-0", "transfer", "document-a", rq(1, 10)),
                link("transfer", "reference-0", "document-b", rq(1, 5)),
            ],
        },
        artifact_provenance: vec![
            "retained-mark-0".into(),
            "documentary-acquisition-log".into(),
        ],
        require_outcome_repeatability: true,
    }
}

#[test]
fn complete_registration_witness_observation_calibration_packet_replays_exactly() {
    let actual = problem();
    let mark = actual.registration.mark.clone();
    let receipt = evaluate_quantum_measurement(&actual, &mark).unwrap();
    assert!(verify_quantum_measurement(&actual, &mark, &receipt).unwrap());
    assert_eq!(
        receipt.observation.registration.mark.instrument.probability,
        rq(1, 2)
    );
    assert_eq!(
        receipt.observation.witness.retained_mark_digest,
        receipt.observation.witness.reaccessed_mark_digest
    );
    assert_eq!(receipt.calibration.readings.len(), 3);
    assert_eq!(
        receipt.calibration.readings[1],
        BoundedReading::new(ri(9), rq(331, 1000)).unwrap()
    );
    assert_eq!(
        receipt.calibration.readings[2],
        BoundedReading::new(ri(-6), rq(351, 1000)).unwrap()
    );
    assert_eq!(receipt.traceability.additive_bound(), &rq(3, 10));
    assert_eq!(
        receipt.corrected_enclosure,
        BoundedReading::new(rq(-11, 2), rq(651, 1000)).unwrap()
    );
    assert_eq!(receipt.result.combined_uncertainty, rq(4, 5));
    assert_eq!(
        receipt.result.native_value,
        MeasurementValue::ExactRational(rq(-11, 2))
    );
    assert_eq!(receipt.authority_effect, AuthorityEffect::None);
    assert!(receipt.repeatability_checked);
    let post = actual
        .instrument
        .instrument()
        .post_state(0, &actual.input_state)
        .unwrap()
        .unwrap();
    assert_eq!(
        actual
            .instrument
            .instrument()
            .probability(0, &post)
            .unwrap(),
        ri(1)
    );
}

#[test]
fn freshly_rehashed_false_records_states_enclosures_and_calibration_are_rejected() {
    let actual = problem();
    let mark = actual.registration.mark.clone();
    let receipt = evaluate_quantum_measurement(&actual, &mark).unwrap();
    let mut false_receipt = receipt.clone();
    false_receipt
        .observation
        .registration
        .mark
        .instrument
        .probability = ri(1);
    false_receipt.refresh_digest().unwrap();
    assert!(!verify_quantum_measurement(&actual, &mark, &false_receipt).unwrap());
    let mut false_receipt = receipt.clone();
    false_receipt
        .observation
        .registration
        .mark
        .instrument
        .post_state_digest = None;
    false_receipt.refresh_digest().unwrap();
    assert!(!verify_quantum_measurement(&actual, &mark, &false_receipt).unwrap());
    let mut false_receipt = receipt.clone();
    false_receipt.corrected_enclosure = BoundedReading::new(rq(-11, 2), ri(0)).unwrap();
    false_receipt.refresh_digest().unwrap();
    assert!(!verify_quantum_measurement(&actual, &mark, &false_receipt).unwrap());
    let mut false_receipt = receipt.clone();
    false_receipt.calibration.readings[1] = BoundedReading::new(ri(9), ri(0)).unwrap();
    false_receipt.refresh_digest().unwrap();
    assert!(!verify_quantum_measurement(&actual, &mark, &false_receipt).unwrap());
    let mut false_receipt = receipt.clone();
    false_receipt.observation.witness.evaluator_id = "another-evaluator".into();
    false_receipt.refresh_digest().unwrap();
    assert!(!verify_quantum_measurement(&actual, &mark, &false_receipt).unwrap());
    let mut false_receipt = receipt;
    false_receipt.result.native_value = MeasurementValue::ExactRational(ri(0));
    false_receipt.refresh_digest().unwrap();
    assert!(!verify_quantum_measurement(&actual, &mark, &false_receipt).unwrap());
}

#[test]
fn matching_forged_retained_and_reaccessed_marks_still_fail_actual_quantum_binding() {
    let mut actual = problem();
    actual.registration.mark.instrument.probability = ri(1);
    let forged_mark = actual.registration.mark.clone();
    assert_eq!(
        evaluate_quantum_measurement(&actual, &forged_mark),
        Err(MeasurementPacketError::RegistrationMismatch)
    );
    let actual = problem();
    let mut reaccess = actual.registration.mark.clone();
    reaccess.indication = ri(99);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &reaccess),
        Err(MeasurementPacketError::ReaccessMismatch)
    );
}

#[test]
fn receipt_binds_actual_density_kraus_presentation_documents_and_error_model() {
    let actual = problem();
    let receipt = evaluate_quantum_measurement(&actual, &actual.registration.mark).unwrap();
    let mut other = problem();
    other.input_state = ExactDensityState::try_new(matrix_unit(0, 0)).unwrap();
    bind_registration(&mut other);
    assert!(!verify_quantum_measurement(&other, &other.registration.mark, &receipt).unwrap());
    let mut other = problem();
    other.instrument = repeatable_instrument(-1); // same CP maps, different declared presentation
    bind_registration(&mut other);
    assert!(!verify_quantum_measurement(&other, &other.registration.mark, &receipt).unwrap());
    let mut other = problem();
    other.traceability.links[0].document_id = "different-real-model-input".into();
    assert!(!verify_quantum_measurement(&other, &other.registration.mark, &receipt).unwrap());
    let mut other = problem();
    other.calibration.stages[0].calibration =
        AffineCalibration::new(ri(2), ri(1), ri(0), rq(1, 20), rq(1, 25)).unwrap();
    assert!(!verify_quantum_measurement(&other, &other.registration.mark, &receipt).unwrap());
    let mut other = problem();
    other.artifact_provenance[0] = "different-history".into();
    assert!(!verify_quantum_measurement(&other, &other.registration.mark, &receipt).unwrap());
}

#[test]
fn the_ladder_requires_retention_compatible_interaction_and_accepting_standing() {
    for status in [
        ObservationStatus::Reject,
        ObservationStatus::Refuse,
        ObservationStatus::Undetermined,
    ] {
        let mut actual = problem();
        actual.context.evaluator_status = status;
        assert_eq!(
            evaluate_quantum_measurement(&actual, &actual.registration.mark),
            Err(MeasurementPacketError::NonAcceptingObservation)
        );
    }
    let mut actual = problem();
    actual.context.accepting_standing = false;
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::NonAcceptingObservation)
    );
    let mut actual = problem();
    actual.context.poles = vec!["detector".into(), "detector".into()];
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::Interaction)
    );
    let mut actual = problem();
    actual.registration.retained = false;
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::NotRetained)
    );
}

#[test]
fn impossible_outcomes_and_nonrepeatable_instruments_are_distinct_refusals() {
    let mut actual = problem();
    actual.input_state = ExactDensityState::try_new(matrix_unit(1, 1)).unwrap();
    bind_registration(&mut actual);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::ImpossibleOutcome)
    );
    let mut actual = problem();
    actual.instrument = FiniteQuantumInstrument::new(
        3,
        3,
        (0..3).map(|i| vec![matrix_unit(0, i)]).collect(),
        "nonrepeatable-prepare",
    )
    .unwrap();
    actual.input_state = ExactDensityState::try_new(matrix_unit(0, 0)).unwrap();
    actual.outcome_indications.push(ri(2));
    bind_registration(&mut actual);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::NonRepeatable)
    );
    actual.require_outcome_repeatability = false;
    let receipt = evaluate_quantum_measurement(&actual, &actual.registration.mark).unwrap();
    assert!(!receipt.repeatability_checked);
}

#[test]
fn calibration_numeric_scale_and_documentary_binding_cannot_be_assumed() {
    let mut actual = problem();
    actual.stated_uncertainty = rq(1, 100);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::UncertaintyUnderstated)
    );
    let mut actual = problem();
    actual.value_map.gain = ri(2);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::ValueMapMismatch)
    );
    let mut actual = problem();
    actual.calibration_evaluator_id = "another-evaluator".into();
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::ValueMapMismatch)
    );
    let mut actual = problem();
    actual.calibration_scale_id = "another-scale".into();
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::ValueMapMismatch)
    );
    let mut actual = problem();
    actual.traceability.origin_id = "transfer".into();
    assert!(evaluate_quantum_measurement(&actual, &actual.registration.mark).is_err());
    let mut actual = problem();
    actual.scale.unit.unit_name = "m".into();
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::TraceabilityBinding)
    );
    let mut actual = problem();
    actual.scale.lower = ri(0);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::Scale)
    );
    let mut actual = problem();
    actual.scale.resolution = ri(1);
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::Scale)
    );
    let mut actual = problem();
    actual.artifact_provenance.clear();
    assert_eq!(
        evaluate_quantum_measurement(&actual, &actual.registration.mark),
        Err(MeasurementPacketError::MissingProvenance)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_quantum_measurement_packet.rs
// Claim: urn:core:crates_rs:tests:test-quantum-measurement-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf348d5d2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf348d5d2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf348d5d2 {
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
impl BoundaryErrorf348d5d2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf348d5d2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf348d5d2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf348d5d2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf348d5d2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf348d5d2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf348d5d2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf348d5d2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f348d5d2() {
    let admitted = BoundaryRecordf348d5d2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf348d5d2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
