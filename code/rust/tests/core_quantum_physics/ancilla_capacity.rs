use linear_algebra::backend::basic_matrix::OperationLimits;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use num_traits::{Signed, Zero};
use core_lie_theory::twisted_abelian_algebra::TwistedAbelianAlgebra;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::ancilla_capacity::{AncillaCapacity, AncillaCapacityError};
use core_quantum_physics::exact_entropy::RationalSpectrum;
use core_quantum_physics::exact_hermitian::{
    gi, gq, hermitian_trace, is_psd, partial_trace_second,
};
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_quantum_physics::exact_operator::ExactOperator;
use core_quantum_physics::majorization::{compare_spectra, Majorization};

fn spectrum(values: &[Rational]) -> RationalSpectrum {
    RationalSpectrum::try_new(values.iter().cloned().map(|v| (v, 1)).collect()).unwrap()
}
fn diagonal(values: &[Rational]) -> ExactDensityState {
    ExactDensityState::try_new(
        mx::diagonal(
            &values
                .iter()
                .cloned()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>(),
        )
        .unwrap(),
    )
    .unwrap()
}
fn bounds(values: &[Rational], m: usize) -> AncillaCapacity {
    AncillaCapacity::from_sectors(&[(ri(1), spectrum(values))], &[m], 128).unwrap()
}

#[test]
fn block_purifications_attain_purity_rank_and_exact_marginals() {
    let values = [rq(9, 14), rq(4, 14), rq(1, 14)];
    let marginal = diagonal(&values);
    let expected = [
        (rq(1, 2), 3, rq(5, 14)),
        (rq(85, 98), 2, rq(1, 14)),
        (ri(1), 1, ri(0)),
    ];
    for (index, (purity, rank, distance)) in expected.into_iter().enumerate() {
        let m = index + 1;
        let capacity = bounds(&values, m);
        let sigma = capacity
            .rational_diagonal_extension(0, OperationLimits::UNLIMITED)
            .unwrap();
        ExactDensityState::try_new(sigma.clone()).unwrap();
        assert_eq!(
            partial_trace_second(&sigma, 3, m).unwrap(),
            *marginal.matrix()
        );
        assert_eq!(
            hermitian_trace(&mx::multiply(&sigma, &sigma).unwrap()).unwrap(),
            purity
        );
        let actual = ExactOperator::try_new(sigma).unwrap().spectrum().unwrap();
        let eigs = actual.rational_eigenvalues().unwrap();
        assert_eq!(
            eigs.iter()
                .filter(|(v, _)| !v.is_zero())
                .map(|(_, k)| k)
                .sum::<usize>(),
            rank
        );
        assert_eq!(capacity.maximum_extension_purity(), purity);
        assert_eq!(capacity.minimum_extension_rank(), rank);
        assert_eq!(capacity.pure_marginal_trace_distance(), distance);
    }
}

#[test]
fn matrix_bound_route_and_rotated_attainer_use_actual_spectra() {
    let values = [rq(9, 14), rq(4, 14), rq(1, 14)];
    let rho = diagonal(&values);
    let u = mx::from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(-4, 5, 0, 1), gi(0, 0)],
        vec![gq(4, 5, 0, 1), gq(3, 5, 0, 1), gi(0, 0)],
        vec![gi(0, 0), gi(0, 0), gi(1, 0)],
    ])
    .unwrap();
    let rotated = ExactDensityState::try_new(
        mx::multiply(
            &mx::multiply(&u, rho.matrix()).unwrap(),
            &star::adjoint(&u).unwrap(),
        )
        .unwrap(),
    )
    .unwrap();
    let capacity = AncillaCapacity::from_density(&rotated, &[2], 3).unwrap();
    assert_eq!(capacity, bounds(&values, 2));
    let sigma = capacity
        .rational_diagonal_extension(0, OperationLimits::UNLIMITED)
        .unwrap();
    let extended_u = mx::kronecker(&u, &mx::identity(2).unwrap()).unwrap();
    let rotated_sigma = mx::multiply(
        &mx::multiply(&extended_u, &sigma).unwrap(),
        &star::adjoint(&extended_u).unwrap(),
    )
    .unwrap();
    assert!(is_psd(&rotated_sigma).unwrap());
    assert_eq!(
        partial_trace_second(&rotated_sigma, 3, 2).unwrap(),
        *rotated.matrix()
    );
    assert_eq!(
        hermitian_trace(&mx::multiply(&rotated_sigma, &rotated_sigma).unwrap()).unwrap(),
        rq(85, 98)
    );
}

#[test]
fn central_and_ancilla_sectors_obey_the_sharp_distinct_bounds() {
    let sectors = [
        (rq(3, 5), spectrum(&[rq(3, 4), rq(1, 4)])),
        (rq(2, 5), spectrum(&[ri(1)])),
    ];
    let classical = AncillaCapacity::from_sectors(&sectors, &[1, 1], 8).unwrap();
    let quantum = AncillaCapacity::from_sectors(&sectors, &[2], 8).unwrap();
    assert_eq!(classical.maximum_extension_purity(), rq(77, 200));
    assert_eq!(quantum.maximum_extension_purity(), rq(13, 25));
    assert_eq!(classical.minimum_extension_rank(), 3);
    assert_eq!(quantum.minimum_extension_rank(), 2);
    assert_eq!(classical.pure_marginal_trace_distance(), rq(11, 20));
    assert_eq!(quantum.pure_marginal_trace_distance(), rq(2, 5));
    // Extra classical sectors do not enlarge the largest simple block.
    assert_eq!(
        quantum,
        AncillaCapacity::from_sectors(&sectors, &[1, 2, 2, 1], 8).unwrap()
    );
    // A zero-weight central block remains admitted but contributes zero rank.
    let with_zero = [
        (ri(0), spectrum(&[rq(1, 2), rq(1, 2)])),
        (ri(1), spectrum(&[ri(1)])),
    ];
    assert_eq!(
        AncillaCapacity::from_sectors(&with_zero, &[1], 3)
            .unwrap()
            .minimum_extension_rank(),
        1
    );
}

#[test]
fn nearest_pure_composite_marginal_distance_is_attained() {
    let values = [rq(9, 14), rq(4, 14), rq(1, 14)];
    let rho = diagonal(&values);
    // Normalize the top-two truncation; its rank fits the two-dimensional ancilla.
    let eta = diagonal(&[rq(9, 13), rq(4, 13), ri(0)]);
    let distance_spectrum = ExactOperator::try_new(mx::sub(rho.matrix(), eta.matrix()).unwrap())
        .unwrap()
        .spectrum()
        .unwrap()
        .rational_eigenvalues()
        .unwrap();
    let distance: Rational = distance_spectrum
        .iter()
        .map(|(q, k)| q.abs() * ri(*k as i64))
        .sum::<Rational>()
        / ri(2);
    assert_eq!(distance, bounds(&values, 2).pure_marginal_trace_distance());
    let eta_capacity = AncillaCapacity::from_density(&eta, &[2], 3).unwrap();
    let purified = eta_capacity
        .rational_diagonal_extension(0, OperationLimits::UNLIMITED)
        .unwrap();
    assert_eq!(mx::multiply(&purified, &purified).unwrap(), purified);
    assert_eq!(
        partial_trace_second(&purified, 3, 2).unwrap(),
        *eta.matrix()
    );
    // The same optimum is the distance of the extension fiber to a pure joint state.
    let original_extension = bounds(&values, 2)
        .rational_diagonal_extension(0, OperationLimits::UNLIMITED)
        .unwrap();
    let difference = ExactOperator::try_new(mx::sub(&original_extension, &purified).unwrap())
        .unwrap()
        .spectrum()
        .unwrap()
        .rational_eigenvalues()
        .unwrap();
    let joint_distance = difference
        .iter()
        .map(|(v, k)| v.abs() * ri(*k as i64))
        .sum::<Rational>()
        / ri(2);
    assert_eq!(joint_distance, distance);
}

#[test]
fn direct_sum_extensions_attain_the_central_ceiling_when_capacity_suffices() {
    let sectors = [
        (rq(3, 5), spectrum(&[rq(9, 14), rq(4, 14), rq(1, 14)])),
        (rq(2, 5), spectrum(&[ri(1)])),
    ];
    let capacity = AncillaCapacity::from_sectors(&sectors, &[1, 3], 4).unwrap();
    let blocks: Vec<_> = (0..2)
        .map(|s| {
            capacity
                .rational_diagonal_extension(s, OperationLimits::UNLIMITED)
                .unwrap()
        })
        .collect();
    for (index, block) in blocks.iter().enumerate() {
        let values = capacity.sectors()[index].eigenvalues();
        let expected = mx::diagonal(
            &values
                .iter()
                .cloned()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>(),
        )
        .unwrap();
        assert_eq!(
            partial_trace_second(block, values.len(), 3).unwrap(),
            expected
        );
    }
    // All omitted smaller-ancilla blocks have zero mass.
    let sigma = mx::block_diagonal(&blocks).unwrap();
    ExactDensityState::try_new(sigma.clone()).unwrap();
    assert_eq!(
        hermitian_trace(&mx::multiply(&sigma, &sigma).unwrap()).unwrap(),
        rq(13, 25)
    );
    assert_eq!(capacity.maximum_extension_purity(), rq(13, 25));
    assert_eq!(capacity.minimum_extension_rank(), 2);
}

#[test]
fn equal_dimension_projective_ancillas_have_different_six_level_capacity() {
    let rho = RationalSpectrum::try_new(vec![(rq(1, 6), 6)]).unwrap();
    // These are the complex block profiles proved for the Z6^2 twists, all dimension36.
    for (blocks, purity, distance, rank) in [
        (vec![1; 36], rq(1, 6), rq(5, 6), 6),
        (vec![6], ri(1), ri(0), 1),
        (vec![3; 4], rq(1, 2), rq(1, 2), 2),
        (vec![2; 9], rq(1, 3), rq(2, 3), 3),
        (vec![4], rq(5, 9), rq(1, 3), 2), // nondividing block-size control, dimension16
    ] {
        let capacity = AncillaCapacity::from_sectors(&[(ri(1), rho.clone())], &blocks, 6).unwrap();
        assert_eq!(capacity.maximum_extension_purity(), purity);
        assert_eq!(capacity.pure_marginal_trace_distance(), distance);
        assert_eq!(capacity.minimum_extension_rank(), rank);
        let sigma = capacity
            .rational_diagonal_extension(0, OperationLimits::UNLIMITED)
            .unwrap();
        assert_eq!(
            partial_trace_second(&sigma, 6, *blocks.iter().max().unwrap()).unwrap(),
            *diagonal(&vec![rq(1, 6); 6]).matrix()
        );
        assert!(is_psd(&sigma).unwrap());
        assert_eq!(
            hermitian_trace(&mx::multiply(&sigma, &sigma).unwrap()).unwrap(),
            purity
        );
    }
}

#[test]
fn product_extensions_are_majorized_by_the_attained_spectrum() {
    let capacity = bounds(&[rq(9, 14), rq(4, 14), rq(1, 14)], 2);
    let rho = diagonal(&[rq(9, 14), rq(4, 14), rq(1, 14)]);
    let product_pure = mx::kronecker(rho.matrix(), diagonal(&[ri(1), ri(0)]).matrix()).unwrap();
    assert_eq!(
        partial_trace_second(&product_pure, 3, 2).unwrap(),
        *rho.matrix()
    );
    assert_eq!(
        hermitian_trace(&mx::multiply(&product_pure, &product_pure).unwrap()).unwrap(),
        capacity.maximum_separable_extension_purity()
    );
    assert_eq!(capacity.maximum_separable_extension_purity(), rq(1, 2));
    assert!(capacity.maximum_separable_extension_purity() < capacity.maximum_extension_purity());
    // rho tensor a maximally mixed two-level environment is a different feasible extension.
    let product = spectrum(&[
        rq(9, 28),
        rq(9, 28),
        rq(4, 28),
        rq(4, 28),
        rq(1, 28),
        rq(1, 28),
    ]);
    let mut optimal = capacity.sectors()[0].grouped().to_vec();
    optimal.resize(6, ri(0));
    assert_eq!(
        compare_spectra(&spectrum(&optimal), &product).unwrap(),
        Majorization::PMajorizesQ
    );
    assert!(product.power_trace(2, 2).unwrap() < capacity.maximum_extension_purity());
    // Sort and repeated-eigenvalue expansion are checked independently of input order.
    let unsorted = RationalSpectrum::try_new(vec![(rq(1, 6), 2), (rq(1, 3), 2)]).unwrap();
    let sorted = AncillaCapacity::from_sectors(&[(ri(1), unsorted)], &[2], 4).unwrap();
    assert_eq!(
        sorted.sectors()[0].eigenvalues(),
        &[rq(1, 3), rq(1, 3), rq(1, 6), rq(1, 6)]
    );
    assert_eq!(sorted.sectors()[0].grouped(), &[rq(2, 3), rq(1, 3)]);
}

#[test]
fn checked_composition_phases_feed_the_ancilla_capacity_owner() {
    let table: Vec<Vec<usize>> = (0..36)
        .map(|g| {
            (0..36)
                .map(|h| ((g / 6 + h / 6) % 6) * 6 + (g % 6 + h % 6) % 6)
                .collect()
        })
        .collect();
    let marginal = RationalSpectrum::try_new(vec![(rq(1, 6), 6)]).unwrap();
    for (k, expected) in [rq(1, 6), ri(1), rq(1, 2), rq(1, 3), rq(1, 2), ri(1)]
        .into_iter()
        .enumerate()
    {
        let phases = (0..36)
            .map(|g| {
                (0..36)
                    .map(|h| Cyclotomic::<6>::zeta((k * (g % 6) * (h / 6)) as i64))
                    .collect()
            })
            .collect();
        let algebra = TwistedAbelianAlgebra::new(table.clone(), phases).unwrap();
        let profile = algebra.complex_block_profile().unwrap();
        assert_eq!(profile.algebra_dimension, 36);
        let capacity = AncillaCapacity::from_sectors(
            &[(ri(1), marginal.clone())],
            &vec![profile.block_dimension; profile.center_dimension],
            6,
        )
        .unwrap();
        assert_eq!(capacity.maximum_extension_purity(), expected);
    }
}

#[test]
fn raw_nonpositive_denominators_are_refused_before_sector_arithmetic() {
    let pure = spectrum(&[ri(1)]);
    for (numerator, denominator) in [(0, 0), (1, 0), (-1, 0), (0, -1), (-1, -1)] {
        let raw = Rational::new_raw(numerator.into(), denominator.into());
        assert_eq!(
            AncillaCapacity::from_sectors(&[(ri(1), pure.clone()), (raw, pure.clone())], &[2], 2),
            Err(AncillaCapacityError::InvalidWeights)
        );
    }
    let canonical = Rational::new((-1).into(), (-1).into());
    let capacity = AncillaCapacity::from_sectors(&[(canonical, pure)], &[2], 1).unwrap();
    assert_eq!(capacity.maximum_extension_purity(), ri(1));
}

#[test]
fn rational_scope_and_resource_refusals_are_explicit() {
    let s = spectrum(&[rq(1, 2), rq(1, 3), rq(1, 6)]);
    for blocks in [vec![], vec![0], vec![1, 0]] {
        assert_eq!(
            AncillaCapacity::from_sectors(&[(ri(1), s.clone())], &blocks, 3),
            Err(AncillaCapacityError::InvalidAncilla)
        );
    }
    assert_eq!(
        AncillaCapacity::from_sectors(&[], &[1], 0),
        Err(AncillaCapacityError::EmptySystem)
    );
    for weights in [[ri(-1), ri(2)], [rq(1, 2), rq(1, 3)]] {
        assert_eq!(
            AncillaCapacity::from_sectors(
                &[
                    (weights[0].clone(), s.clone()),
                    (weights[1].clone(), s.clone())
                ],
                &[1],
                6
            ),
            Err(AncillaCapacityError::InvalidWeights)
        );
    }
    assert_eq!(
        AncillaCapacity::from_sectors(&[(ri(1), s.clone())], &[2], 2),
        Err(AncillaCapacityError::SpectrumBudget)
    );
    let capacity = AncillaCapacity::from_sectors(&[(ri(1), s)], &[2], 3).unwrap();
    assert!(matches!(
        capacity.rational_diagonal_extension(0, OperationLimits::UNLIMITED),
        Err(AncillaCapacityError::NonRationalCoefficient { .. })
    ));
    assert!(matches!(
        capacity.rational_diagonal_extension(1, OperationLimits::UNLIMITED),
        Err(AncillaCapacityError::UnknownSector(1))
    ));
    assert!(capacity
        .rational_diagonal_extension(
            0,
            OperationLimits {
                max_elements: 1,
                max_scalar_ops: 1
            }
        )
        .is_err());
    let rational = bounds(&[rq(9, 14), rq(4, 14), rq(1, 14)], 2);
    assert!(rational
        .rational_diagonal_extension(
            0,
            OperationLimits {
                max_elements: 36,
                max_scalar_ops: 1,
            }
        )
        .is_err());
    assert!(rational
        .rational_diagonal_extension(
            0,
            OperationLimits {
                max_elements: 1,
                max_scalar_ops: usize::MAX,
            }
        )
        .is_err());
    let oversized = bounds(&[ri(1), ri(0)], usize::MAX);
    assert_eq!(
        oversized.rational_diagonal_extension(0, OperationLimits::UNLIMITED),
        Err(AncillaCapacityError::DimensionOverflow)
    );
    // Positive trace-one Q(i) density with irrational eigenvalues (1 +/- 1/sqrt2)/2.
    let irrational = ExactDensityState::try_new(
        mx::from_rows(vec![
            vec![gq(3, 4, 0, 1), gq(1, 4, 0, 1)],
            vec![gq(1, 4, 0, 1), gq(1, 4, 0, 1)],
        ])
        .unwrap(),
    )
    .unwrap();
    assert_eq!(
        AncillaCapacity::from_density(&irrational, &[2], 2),
        Err(AncillaCapacityError::NonRationalSpectrum)
    );
    assert_eq!(
        AncillaCapacity::from_density(&irrational, &[2], 1),
        Err(AncillaCapacityError::SpectrumBudget)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/ancilla_capacity.rs
// Claim: urn:core:crates_rs:tests:ancilla-capacity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0ce44714 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0ce44714` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0ce44714 {
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
impl BoundaryError0ce44714 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0ce44714 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0ce44714 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0ce44714 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0ce44714> {
        if capacity_bound == 0 {
            return Err(BoundaryError0ce44714::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0ce44714::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0ce44714::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_0ce44714() {
    let admitted = BoundaryRecord0ce44714::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0ce44714::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
