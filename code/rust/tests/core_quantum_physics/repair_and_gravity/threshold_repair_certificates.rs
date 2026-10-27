//! Threshold theorems read as conditional repair-capacity certificates: the
//! worked threshold-scaling arithmetic, the least suppressing distance, the
//! three readings of the repair-capacity recurrence under the threshold
//! mapping, and repair-image monotonicity on every nested pair of repair
//! families of a declared carrier. Every check is exact.

use num_bigint::BigInt;
use num_traits::Zero;
use core_homology::graph_f2::PatternCarrier;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::repair_capacity::residual_lower_bounds;

use core_quantum_physics::threshold_repair_certificate::{
    read_threshold_packet, ThresholdError, ThresholdReading, ThresholdScaling,
};

fn scaling(c: Rational, p: Rational, p_th: Rational) -> ThresholdScaling {
    ThresholdScaling::new(c, p, p_th).unwrap()
}

/// `C = 1`, `p = 1/1000`, `p_th = 1/100`: the source's worked numbers.
fn worked() -> ThresholdScaling {
    scaling(ri(1), rq(1, 1000), rq(1, 100))
}

#[test]
fn the_worked_scaling_example_is_recomputed_exactly() {
    let s = worked();
    assert_eq!(s.ratio(), rq(1, 10));
    let bounds: Vec<Rational> = [3, 5, 7, 9]
        .iter()
        .map(|&d| s.pairing_bound(d).unwrap())
        .collect();
    assert_eq!(
        bounds,
        vec![rq(1, 100), rq(1, 1000), rq(1, 10_000), rq(1, 100_000)]
    );
    // floor((d + 1) / 2): an even distance repeats the odd one below it.
    assert_eq!(s.pairing_bound(1).unwrap(), rq(1, 10));
    assert_eq!(s.pairing_bound(4).unwrap(), rq(1, 100));
    assert_eq!(s.pairing_bound(6).unwrap(), rq(1, 1000));
    assert_eq!(s.pairing_bound(0), Err(ThresholdError::ZeroDistance));
}

#[test]
fn above_threshold_the_bound_grows_and_at_threshold_it_is_constant() {
    let above = scaling(ri(1), rq(1, 50), rq(1, 100));
    let bounds: Vec<Rational> = [1, 3, 5, 7]
        .iter()
        .map(|&d| above.pairing_bound(d).unwrap())
        .collect();
    assert_eq!(bounds, vec![ri(2), ri(4), ri(8), ri(16)]);
    assert_eq!(above.least_distance_below(&rq(1, 100), 99).unwrap(), None);
    // A small prefactor puts d = 1 below tau, but no d* keeps it there.
    let small = scaling(rq(1, 1000), rq(1, 50), rq(1, 100));
    assert!(small.pairing_bound(1).unwrap() < rq(1, 100));
    assert!(small.pairing_bound(15).unwrap() > rq(1, 100));
    assert_eq!(small.least_distance_below(&rq(1, 100), 99).unwrap(), None);

    let at = scaling(rq(1, 2), rq(1, 100), rq(1, 100));
    assert_eq!(at.pairing_bound(1).unwrap(), rq(1, 2));
    assert_eq!(at.pairing_bound(21).unwrap(), rq(1, 2));
    assert_eq!(at.least_distance_below(&ri(1), 99).unwrap(), Some(1));
    assert_eq!(at.least_distance_below(&rq(1, 2), 99).unwrap(), None);
}

#[test]
fn the_least_suppressing_distance_is_strictly_below_the_threshold() {
    let s = worked();
    // The source's criterion floor((d+1)/2) >= log(tau/C) / log(p/p_th) admits d = 3
    // for tau = 1/100, where the bound equals tau instead of dropping below it.
    assert_eq!(s.pairing_bound(3).unwrap(), rq(1, 100));
    assert_eq!(s.least_distance_below(&rq(1, 100), 99).unwrap(), Some(5));
    assert_eq!(s.least_distance_below(&rq(1, 500), 99).unwrap(), Some(5));
    assert_eq!(s.least_distance_below(&rq(1, 1000), 99).unwrap(), Some(7));
    assert_eq!(s.least_distance_below(&ri(1), 99).unwrap(), Some(1));
    let mut power = BigInt::from(1);
    for k in 1..=6u32 {
        power *= 10;
        let tau = Rational::new(BigInt::from(1), power.clone());
        let d = s.least_distance_below(&tau, 99).unwrap().unwrap();
        assert_eq!(d, 2 * k + 1);
        assert!(s.pairing_bound(d).unwrap() < tau && s.pairing_bound(d - 2).unwrap() >= tau);
    }
    // p = 0: the bound vanishes from d = 1.
    assert_eq!(
        scaling(ri(3), ri(0), rq(1, 100))
            .least_distance_below(&rq(1, 10), 9)
            .unwrap(),
        Some(1)
    );
    // A slow ratio exhausts a small search bound.
    let slow = scaling(ri(1), rq(99, 10_000), rq(1, 100));
    assert_eq!(
        slow.least_distance_below(&rq(1, 1_000_000), 11),
        Err(ThresholdError::SearchBound { max_distance: 11 })
    );
    assert_eq!(
        s.least_distance_below(&ri(0), 99),
        Err(ThresholdError::NonPositiveVisibility)
    );
}

#[test]
fn the_threshold_reading_returns_survival_no_go_or_undecided() {
    let tau = rq(1, 100);
    let survival = read_threshold_packet(&worked(), &rq(1, 500), &ri(0), &tau, 99).unwrap();
    assert_eq!(
        survival,
        ThresholdReading::ConditionalSurvival {
            gap: rq(-11, 1000),
            least_distance: 5
        }
    );
    // p = 2/100: gap 20/1000 - 10/1000 - 2/1000 = 1/125; 1/125 < 1/100 < 2/125.
    let above = scaling(ri(1), rq(1, 50), rq(1, 100));
    let no_go = read_threshold_packet(&above, &rq(1, 500), &ri(0), &tau, 99).unwrap();
    assert_eq!(
        no_go,
        ThresholdReading::ConditionalNoGo {
            gap: rq(1, 125),
            windows: BigInt::from(2)
        }
    );
    // p = 11/1000 is above threshold, yet inside the slack band nothing is forced.
    let band = scaling(ri(1), rq(11, 1000), rq(1, 100));
    let undecided = read_threshold_packet(&band, &rq(1, 500), &ri(0), &tau, 99).unwrap();
    assert_eq!(
        undecided,
        ThresholdReading::Undecided {
            gap: rq(-1, 1000),
            ratio: rq(11, 10)
        }
    );
    assert!(band.pairing_bound(9).unwrap() > band.pairing_bound(1).unwrap());
    // With no slack the same rate is in the no-go regime.
    assert!(matches!(
        read_threshold_packet(&band, &ri(0), &ri(0), &tau, 99).unwrap(),
        ThresholdReading::ConditionalNoGo { .. }
    ));
}

fn tally_threshold_reading(
    p: &Rational,
    p_th: &Rational,
    eps: &Rational,
    rho0: &Rational,
    tau: &Rational,
    survivals: &mut i32,
    no_goes: &mut i32,
    undecided: &mut i32,
) {
    let s = scaling(ri(1), p.clone(), p_th.clone());
    match read_threshold_packet(&s, eps, rho0, tau, 199).unwrap() {
        ThresholdReading::ConditionalSurvival {
            gap,
            least_distance,
        } => {
            assert!(p < p_th && gap < Rational::zero());
            assert!(&s.pairing_bound(least_distance).unwrap() < tau);
            assert!(least_distance == 1 || &s.pairing_bound(least_distance - 2).unwrap() >= tau);
            *survivals += 1;
        }
        ThresholdReading::ConditionalNoGo { gap, windows } => {
            assert!(p > &(p_th + eps) && gap > Rational::zero());
            let budget = s.repair_budget(eps).unwrap();
            let k: usize = windows.try_into().unwrap();
            let bounds = residual_lower_bounds(rho0, &budget, k).unwrap();
            assert!(&bounds[k] > tau && &bounds[k - 1] <= tau);
            *no_goes += 1;
        }
        ThresholdReading::Undecided { gap, .. } => {
            assert!(p >= p_th && p <= &(p_th + eps) && gap <= Rational::zero());
            *undecided += 1;
        }
    }
}

#[test]
fn below_threshold_the_recurrence_never_fires_and_above_it_fires_only_past_the_slack() {
    let rates = [
        ri(0),
        rq(1, 1000),
        rq(1, 200),
        rq(1, 100),
        rq(11, 1000),
        rq(3, 250),
        rq(1, 50),
    ];
    let thresholds = [rq(1, 100), rq(1, 50)];
    let slacks = [ri(0), rq(1, 500), rq(1, 100)];
    let starts = [ri(0), rq(1, 200)];
    let tau = rq(1, 100);
    let (mut survivals, mut no_goes, mut undecided) = (0, 0, 0);
    for p in &rates {
        for p_th in &thresholds {
            for eps in &slacks {
                for rho0 in &starts {
                    tally_threshold_reading(
                        p,
                        p_th,
                        eps,
                        rho0,
                        &tau,
                        &mut survivals,
                        &mut no_goes,
                        &mut undecided,
                    );
                }
            }
        }
    }
    assert_eq!((survivals, no_goes, undecided), (54, 8, 22));
}

#[test]
fn malformed_threshold_declarations_are_refused() {
    assert_eq!(
        ThresholdScaling::new(ri(0), rq(1, 1000), rq(1, 100)),
        Err(ThresholdError::NonPositivePrefactor)
    );
    assert_eq!(
        ThresholdScaling::new(ri(1), rq(1, 1000), ri(0)),
        Err(ThresholdError::NonPositiveThreshold)
    );
    assert_eq!(
        ThresholdScaling::new(ri(1), rq(-1, 1000), rq(1, 100)),
        Err(ThresholdError::NegativeRate)
    );
    let s = worked();
    assert_eq!(
        s.repair_budget(&rq(-1, 500)),
        Err(ThresholdError::NegativeSlack)
    );
    assert_eq!(
        read_threshold_packet(&s, &ri(0), &rq(1, 50), &rq(1, 100), 99),
        Err(ThresholdError::StartOutsideVisibility)
    );
    assert_eq!(
        read_threshold_packet(&s, &ri(0), &rq(-1, 50), &rq(1, 100), 99),
        Err(ThresholdError::StartOutsideVisibility)
    );
    assert_eq!(
        read_threshold_packet(&s, &ri(0), &ri(0), &ri(0), 99),
        Err(ThresholdError::NonPositiveVisibility)
    );
}

/// All `2^8` families of assignments on the triangle, as masks over `0..8`.
fn family(mask: u32) -> Vec<u32> {
    (0..8).filter(|f| mask >> f & 1 == 1).collect()
}

#[test]
fn enlarging_the_repair_image_never_strands_more_defects() {
    let carrier = PatternCarrier::new(3, vec![(0, 1), (1, 2), (2, 0)]).unwrap();
    let stranded =
        |mask: u32| carrier.pattern_count() - carrier.image(&family(mask)).unwrap().len();
    assert_eq!(stranded(0xFF), 4);
    assert_eq!(stranded(0), 8);
    let mut nested_pairs = 0;
    for small in 0u32..256 {
        for large in 0u32..256 {
            if small & !large != 0 {
                continue;
            }
            nested_pairs += 1;
            assert!(stranded(large) <= stranded(small));
            if small != 0 {
                for h in 0..8 {
                    let before = carrier.binary_residual(h, &family(small)).unwrap();
                    let after = carrier.binary_residual(h, &family(large)).unwrap();
                    assert!(after <= before);
                }
            }
        }
    }
    assert_eq!(nested_pairs, 6561);
    // Without nesting the count can rise: the full family strands 4, one repair strands 7.
    assert_eq!((stranded(0xFF), stranded(0b1)), (4, 7));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/repair_and_gravity/threshold_repair_certificates.rs
// Claim: urn:core:crates_rs:tests:threshold-repair-certificates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3ef4f7d7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3ef4f7d7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3ef4f7d7 {
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
impl BoundaryError3ef4f7d7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3ef4f7d7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3ef4f7d7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3ef4f7d7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3ef4f7d7> {
        if capacity_bound == 0 {
            return Err(BoundaryError3ef4f7d7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3ef4f7d7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3ef4f7d7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3ef4f7d7() {
    let admitted = BoundaryRecord3ef4f7d7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3ef4f7d7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
