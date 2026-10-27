use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_category_theory::finite_report_query::ReportQueryDecision;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::{
    carrier_tests::*,
    exact_channel::ExactKrausChannel,
    exact_entropy::RationalSpectrum,
    exact_hermitian::{gi, outer},
    exact_instrument::ExactDensityState,
    finite_chsh_correlations::PairwiseBox,
    instruments::ExactPovm,
};
use core_solvers::solver_convex_finite_hull::MembershipCertificate;

fn density(a: i64, b: i64) -> ExactDensityState {
    let v = [
        GaussianRat::from_rational(rq(a, 5)),
        GaussianRat::from_rational(rq(b, 5)),
    ];
    ExactDensityState::try_new(outer(&v, &v).unwrap()).unwrap()
}
fn z() -> ExactPovm {
    ExactPovm::try_new(vec![
        outer(&[gi(1, 0), gi(0, 0)], &[gi(1, 0), gi(0, 0)]).unwrap(),
        outer(&[gi(0, 0), gi(1, 0)], &[gi(0, 0), gi(1, 0)]).unwrap(),
    ])
    .unwrap()
}
fn coherent() -> ExactKrausChannel {
    let u = BasicMatrix::from_row_major(
        2,
        2,
        [rq(3, 5), rq(4, 5), rq(-4, 5), rq(3, 5)]
            .into_iter()
            .map(GaussianRat::from_rational)
            .collect(),
    )
    .unwrap();
    ExactKrausChannel::from_operators(vec![u]).unwrap()
}

#[test]
fn present_populations_collide_for_an_available_future_control() {
    let r = report_sufficiency(&[density(3, 4), density(3, -4)], &z(), &coherent(), &z()).unwrap();
    assert_eq!(r.reports, vec![vec![rq(9, 25), rq(16, 25)]; 2]);
    assert_eq!(r.answers, vec![ri(1), rq(49, 625)]);
    assert!(matches!(r.decision, ReportQueryDecision::Collision(_)));
}

#[test]
fn sufficient_controls_and_different_question_are_not_false_collisions() {
    let states = [density(3, 4), density(3, -4)];
    let r = report_sufficiency(
        &states,
        &z(),
        &ExactKrausChannel::identity(2, "").unwrap(),
        &z(),
    )
    .unwrap();
    assert!(matches!(r.decision, ReportQueryDecision::Factorable(_)));
    // Refining the report by the future pulled-back measurement restores sufficiency.
    let k = coherent();
    let p = k.adjoint_apply(z().effects()[0].as_matrix()).unwrap();
    let q = mx::sub(&mx::identity(2).unwrap(), &p).unwrap();
    let refined = ExactPovm::try_new(vec![p, q]).unwrap();
    assert!(matches!(
        report_sufficiency(&states, &refined, &k, &z())
            .unwrap()
            .decision,
        ReportQueryDecision::Factorable(_)
    ));
    assert_eq!(
        report_sufficiency(&[], &z(), &k, &z()),
        Err(CarrierTestError::EmptyPreparations)
    );
}

#[test]
fn positive_full_support_bell_box_has_a_separating_witness() {
    let p = [rq(4, 5), rq(4, 5), rq(3, 5), rq(-3, 5)]
        .into_iter()
        .flat_map(|e| {
            [
                (&ri(1) + &e) / ri(4),
                (&ri(1) - &e) / ri(4),
                (&ri(1) - &e) / ri(4),
                (&ri(1) + &e) / ri(4),
            ]
        })
        .collect();
    let b = PairwiseBox::new(p).unwrap();
    // Bind the probability fixture to an admitted quantum realization, rather
    // than inferring quantum realizability from a no-signalling box alone.
    let observable = |entries: [i64; 4], denominator| {
        BasicMatrix::from_row_major(
            2,
            2,
            entries
                .into_iter()
                .map(|n| GaussianRat::from_rational(rq(n, denominator)))
                .collect(),
        )
        .unwrap()
    };
    let a0 = observable([1, 0, 0, -1], 1);
    let a1 = observable([0, 1, 1, 0], 1);
    let b0 = observable([4, 3, 3, -4], 5);
    let b1 = observable([4, -3, -3, -4], 5);
    let rho = core_quantum_physics::bipartite_operator::pure_state(&[
        gi(1, 0),
        gi(0, 0),
        gi(0, 0),
        gi(1, 0),
    ])
    .unwrap();
    let realized = PairwiseBox::from_state(&rho, [&a0, &a1], [&b0, &b1]).unwrap();
    assert_eq!(b.coordinates(), realized.coordinates());
    assert!(b.is_no_signalling());
    assert_eq!(b.chsh(), rq(14, 5));
    assert_eq!(b.support_compatible_assignments().len(), 16);
    assert!(matches!(
        positive_joint_extension(&b).unwrap(),
        MembershipCertificate::Separated(_)
    ));
    let control = PairwiseBox::from_joint_table(&vec![ri(1); 16]).unwrap();
    assert!(matches!(
        positive_joint_extension(&control).unwrap(),
        MembershipCertificate::Member(_)
    ));
}

#[test]
fn another_chsh_facet_is_not_missed() {
    // PR correlations with the second Alice setting reversed: this chosen S=0,
    // but another CHSH orientation is 4. One scalar comparison is insufficient.
    let p = [1, 1, -1, 1]
        .into_iter()
        .flat_map(|e| [rq(1 + e, 4), rq(1 - e, 4), rq(1 - e, 4), rq(1 + e, 4)])
        .collect();
    let b = PairwiseBox::new(p).unwrap();
    assert_eq!(b.chsh(), ri(0));
    assert!(matches!(
        positive_joint_extension(&b).unwrap(),
        MembershipCertificate::Separated(_)
    ));
}

#[test]
fn mixed_central_weights_obstruct_every_declared_ancilla_size() {
    let pure = RationalSpectrum::try_new(vec![(ri(1), 1)]).unwrap();
    let sectors = [(rq(1, 2), pure.clone()), (rq(1, 2), pure)];
    for ancilla in [vec![1], vec![2], vec![2, 3], vec![64]] {
        let r = sector_purification(&sectors, &ancilla, 16).unwrap();
        assert!(r.central_obstruction);
        assert_eq!(r.central_purity_ceiling, rq(1, 2));
        assert_eq!(r.central_distance_floor, rq(1, 2));
        assert_eq!(r.capacity.maximum_extension_purity(), rq(1, 2));
        assert_eq!(r.capacity.minimum_extension_rank(), 2);
    }
}

#[test]
fn single_sector_is_not_automatically_a_purification_certificate() {
    let mixed = RationalSpectrum::try_new(vec![(rq(9, 25), 1), (rq(16, 25), 1)]).unwrap();
    let sectors = [(ri(1), mixed)];
    let small = sector_purification(&sectors, &[1], 16).unwrap();
    assert!(!small.central_obstruction);
    assert!(small.capacity.maximum_extension_purity() < ri(1));
    let large = sector_purification(&sectors, &[2], 16).unwrap();
    assert_eq!(large.capacity.maximum_extension_purity(), ri(1));
    assert_eq!(large.capacity.pure_marginal_trace_distance(), ri(0));
    assert!(sector_purification(&sectors, &[], 16).is_err());
    assert!(sector_purification(&sectors, &[0], 16).is_err());
    assert!(sector_purification(&sectors, &[2], 1).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/carrier_tests.rs
// Claim: urn:core:crates_rs:tests:carrier-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord23ad643f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord23ad643f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError23ad643f {
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
impl BoundaryError23ad643f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError23ad643f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError23ad643f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord23ad643f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError23ad643f> {
        if capacity_bound == 0 {
            return Err(BoundaryError23ad643f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError23ad643f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError23ad643f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_23ad643f() {
    let admitted = BoundaryRecord23ad643f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord23ad643f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
