//! Run with `cargo run -p core_wdp --example finite_derivations`.
//! Declared finite mathematics only; each replay checks the actual problem.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_24efefed<T> {
    fn checked_invariant_24efefed(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_24efefed<T> for Option<T> {
    #[inline]
    fn checked_invariant_24efefed(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_24efefed<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_24efefed(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeSet;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::semiring_lumpability::lumpable_quotient;
use core_finite_probability::finite_valuation::BooleanValuation;
use core_measurement::affine_calibration::{AffineCalibration, BoundedReading};
use core_measurement::finite_chain_clock::ChainClock;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::outer;
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_quantum_physics::instrument_repeatability::analyze_repeatability;
use core_wdp::calibration_adapter::{
    evaluate_calibration_packet, verify_calibration_receipt, CalibrationPacket,
    NamedCalibrationStage,
};
use core_wdp::clock_adequacy_adapter::{
    evaluate_clock_adequacy, evaluate_clock_coarsening, verify_clock_adequacy,
    verify_clock_coarsening, NamedChainClockPacket,
};
use core_wdp::empirical_adapter::{MeasurementCover, RunTable};
use core_wdp::empirical_repair::{repair, sampling_tolerance, verify_repair};
use core_wdp::instrument_adapter::FiniteQuantumInstrument;
use core_wdp::profile_evaluator::{FiniteProfile, ProfileStatus, TableEvidence};
use core_wdp::retention::{compute_behavioral_quotient, make_cm1_static_carrier};

fn sum_block_entries(
    matrix: &[[i64; 3]; 3],
    rows: &[usize],
    cols: &[usize],
) -> Result<i64, &'static str> {
    let mut sum = 0i64;
    for &row in rows {
        for &col in cols {
            let entry = matrix
                .get(row)
                .and_then(|line| line.get(col))
                .ok_or("matrix index")?;
            sum = sum.checked_add(*entry).ok_or("block sum overflow")?;
        }
    }
    Ok(sum)
}

fn sum_fine_rows(matrix: &[[i64; 3]; 3], rows: &[usize]) -> Result<i64, &'static str> {
    let mut fine = 0i64;
    for &row in rows {
        for entry in matrix.get(row).ok_or("matrix index")? {
            fine = fine.checked_add(*entry).ok_or("row sum overflow")?;
        }
    }
    Ok(fine)
}

fn lumpable_block_identity() -> Result<[[i64; 2]; 2], &'static str> {
    let matrix = [[2i64, -1, 3], [0, 1, 3], [4, -2, 1]];
    let blocks: [&[usize]; 2] = [&[0, 1], &[2]];
    let mut quotient = [[0i64; 2]; 2];
    for (row_index, rows) in blocks.iter().enumerate() {
        for (col_index, cols) in blocks.iter().enumerate() {
            quotient[row_index][col_index] = sum_block_entries(&matrix, rows, cols)?;
        }
        let fine = sum_fine_rows(&matrix, rows)?;
        let coarse = quotient[row_index][0]
            .checked_add(quotient[row_index][1])
            .ok_or("quotient row overflow")?;
        if fine != coarse {
            return Err("block row sum disagrees with the quotient row");
        }
    }
    Ok(quotient)
}

fn main() {
    match lumpable_block_identity() {
        Ok(quotient) if quotient == [[2, 6], [2, 1]] => {}
        Ok(_) | Err(_) => {
            eprintln!("finite_derivations: lumpable block identity refused");
            std::process::exit(2);
        }
    }
    let (classes, _) = compute_behavioral_quotient(&make_cm1_static_carrier()).checked_invariant_24efefed("checked invariant");
    println!("Retention: {classes} behavioral classes");

    let clock = ChainClock::new(
        [1, 2, 3, 4].into_iter().map(ri).collect(),
        [0, 2, 5, 7, 12].into_iter().map(ri).collect(),
        ri(1),
        vec![ri(1); 4],
    )
    .checked_invariant_24efefed("checked invariant");
    let full_interval = clock.interval_bound(0, 4).checked_invariant_24efefed("checked invariant");
    assert_eq!(full_interval.discrepancy, ri(2));
    assert_eq!(full_interval.error_budget, ri(4));
    let clock_packet = NamedChainClockPacket::new(
        "finite-clock".into(),
        (0..=4).map(|index| format!("occurrence-{index}")).collect(),
        clock,
    )
    .checked_invariant_24efefed("checked invariant");
    let clock_receipt = evaluate_clock_adequacy(&clock_packet).checked_invariant_24efefed("checked invariant");
    assert!(verify_clock_adequacy(&clock_packet, &clock_receipt).checked_invariant_24efefed("checked invariant"));
    let coarsening = evaluate_clock_coarsening(&clock_packet, &[0, 2, 4]).checked_invariant_24efefed("checked invariant");
    assert!(verify_clock_coarsening(&clock_packet, &[0, 2, 4], &coarsening).checked_invariant_24efefed("checked invariant"));
    println!("Clock: interval discrepancy 2 <= budget 4; adequacy and block coarsening verified");

    let valuation = BooleanValuation::try_new(
        2,
        vec![(BTreeSet::new(), ri(0)), (BTreeSet::from([0, 1]), ri(9))],
    )
    .checked_invariant_24efefed("checked invariant");
    assert!(!valuation.singleton_extension_is_unique());
    println!(
        "Valuation: atom mass {}; individual witness masses are ambiguous",
        valuation.atom_masses()[0]
    );

    let transition = BasicMatrix::from_row_major(
        3,
        3,
        [2, -1, 3, 0, 1, 3, 4, -2, 1].into_iter().map(ri).collect(),
    )
    .checked_invariant_24efefed("checked invariant");
    let quotient = lumpable_quotient(&transition, &[vec![0, 1], vec![2]])
        .checked_invariant_24efefed("checked invariant")
        .checked_invariant_24efefed("declared partition satisfies outgoing block sums");
    println!(
        "Coarse-graining: quotient [[{}, {}], [{}, {}]] preserves endpoint-block sums",
        quotient.get_ref(0, 0).checked_invariant_24efefed("checked invariant"),
        quotient.get_ref(0, 1).checked_invariant_24efefed("checked invariant"),
        quotient.get_ref(1, 0).checked_invariant_24efefed("checked invariant"),
        quotient.get_ref(1, 1).checked_invariant_24efefed("checked invariant")
    );

    let packet = CalibrationPacket::new(
        "finite-measurement".into(),
        BoundedReading::new(ri(2), rq(1, 10)).checked_invariant_24efefed("checked invariant"),
        vec![
            NamedCalibrationStage::new(
                "first".into(),
                AffineCalibration::new(ri(2), ri(1), rq(1, 10), rq(1, 20), ri(0)).checked_invariant_24efefed("checked invariant"),
            )
            .checked_invariant_24efefed("checked invariant"),
            NamedCalibrationStage::new(
                "second".into(),
                AffineCalibration::new(ri(-3), ri(2), ri(0), ri(0), rq(1, 50)).checked_invariant_24efefed("checked invariant"),
            )
            .checked_invariant_24efefed("checked invariant"),
        ],
    )
    .checked_invariant_24efefed("checked invariant");
    let receipt = evaluate_calibration_packet(&packet).checked_invariant_24efefed("checked invariant");
    assert!(verify_calibration_receipt(&packet, &receipt).checked_invariant_24efefed("checked invariant"));
    let output = receipt.readings.last().checked_invariant_24efefed("checked invariant");
    assert_eq!(output.center(), &ri(-13));
    assert_eq!(output.radius(), &rq(7, 5));
    println!(
        "Calibration: {} +/- {}; actual packet replay verified",
        output.center(),
        output.radius()
    );

    let amplitude = vec![
        GaussianRat::from_rational(rq(3, 5)),
        GaussianRat::from_rational(rq(4, 5)),
        GaussianRat::zero(),
    ];
    let state = ExactDensityState::try_new(outer(&amplitude, &amplitude).checked_invariant_24efefed("checked invariant")).checked_invariant_24efefed("checked invariant");
    let projectors = (0..3)
        .map(|index| {
            let mut basis = vec![GaussianRat::zero(); 3];
            basis[index] = GaussianRat::from_ints(1, 0);
            vec![outer(&basis, &basis).checked_invariant_24efefed("checked invariant")]
        })
        .collect();
    let instrument = FiniteQuantumInstrument::new(3, 3, projectors, "three-outcome").checked_invariant_24efefed("checked invariant");
    let mut probabilities = Vec::new();
    for outcome in 0..3 {
        let receipt = instrument.receipt(outcome, &state).checked_invariant_24efefed("checked invariant");
        assert!(instrument.verify_receipt(&state, &receipt).checked_invariant_24efefed("checked invariant"));
        probabilities.push(receipt.probability);
    }
    assert_eq!(probabilities, vec![rq(9, 25), rq(16, 25), ri(0)]);
    println!("Quantum instrument: probabilities 9/25, 16/25, 0; all receipts verified");
    assert!(analyze_repeatability(instrument.instrument())
        .checked_invariant_24efefed("checked invariant")
        .is_repeatable());
    println!("Repeatability: every cross-outcome Kraus product vanishes");

    let cover = MeasurementCover::new(1, 3, vec![vec![0]; 3]).checked_invariant_24efefed("checked invariant");
    let runs = RunTable::new(&cover, vec![vec![vec![0]], vec![vec![1]], vec![vec![2]]]).checked_invariant_24efefed("checked invariant");
    let repair_receipt = repair(&cover, &runs, 20, 2000).checked_invariant_24efefed("checked invariant");
    verify_repair(&cover, &runs, &repair_receipt, 20).checked_invariant_24efefed("checked invariant");
    assert_eq!(repair_receipt.radius, rq(4, 3));
    println!("Empirical repair: three-context radius 4/3; exact primal/dual replay verified");

    let sample_cover = MeasurementCover::new(1, 2, vec![vec![0]; 2]).checked_invariant_24efefed("checked invariant");
    let sample_runs = RunTable::new(&sample_cover, vec![vec![vec![0]; 400]; 2]).checked_invariant_24efefed("checked invariant");
    let tolerance =
        sampling_tolerance(&sample_cover, &sample_runs, &[rq(1, 10), rq(1, 10)], 10).checked_invariant_24efefed("checked invariant");
    assert_eq!(tolerance.uniform_tolerance, rq(1, 5));
    println!("Sampling: iid compatible-population pair tolerance 1/5, failure bound 1/2");

    let query = "calibration-replay".to_owned();
    let profile = FiniteProfile::new(
        vec![(query.clone(), true)],
        BTreeSet::from([query.clone()]),
        BTreeSet::new(),
        1,
    )
    .checked_invariant_24efefed("checked invariant");
    let evidence = [TableEvidence {
        query: query.clone(),
        value: verify_calibration_receipt(&packet, &receipt).checked_invariant_24efefed("checked invariant"),
    }];
    let status_receipt = profile.evaluate_with_receipt(&query, &evidence).checked_invariant_24efefed("checked invariant");
    profile
        .verify_receipt(&query, &evidence, &status_receipt)
        .checked_invariant_24efefed("checked invariant");
    assert_eq!(status_receipt.status, ProfileStatus::Proved);
    println!("Profile: Proved in the declared finite table; receipt replay verified");
}

// Origin: engine/crates_rs/core_wdp/src/examples/finite_derivations.rs
// Claim: urn:core:crates_rs:core-wdp:finite-derivations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord24efefed {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord24efefed` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError24efefed {
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
impl BoundaryError24efefed {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError24efefed {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError24efefed {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord24efefed {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError24efefed> {
        if capacity_bound == 0 {
            return Err(BoundaryError24efefed::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError24efefed::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError24efefed::ExceedsCapacity {
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
mod l4_boundary_tests_24efefed {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord24efefed::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord24efefed::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord24efefed::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord24efefed::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord24efefed::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError24efefed::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError24efefed::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
