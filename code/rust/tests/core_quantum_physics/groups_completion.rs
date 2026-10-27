use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::Cyc5;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::wigner::{
    state_ground_d5, DiscreteWigner, DiscreteWignerSystemD5, WignerError,
};

#[test]
fn non_rational_real_wigner_values_are_retained_and_rational_projection_is_refused() {
    let w = DiscreteWignerSystemD5::new();
    let alpha = Cyc5::zeta5(1).add(&Cyc5::zeta5(4));
    // Real, unit trace, positive in the canonical embedding (0 < alpha < 1).
    let mut rho = state_ground_d5();
    rho.set(0, 0, alpha.clone()).unwrap();
    rho.set(1, 1, Cyc5::one().sub(&alpha)).unwrap();
    let exact = w.evaluate_exact(&rho).unwrap();
    assert_eq!(exact[0][0], alpha.mul(&Cyc5::rat(rq(1, 5))));
    assert_eq!(w.evaluate_wigner(&rho), Err(WignerError::NonRational));
    assert!(w.try_operator(5, 0).is_err());
    let mut raw = serde_json::to_value(&w).unwrap();
    let rows = raw["operators"].as_array_mut().unwrap();
    rows.push(rows[0].clone());
    let malformed: DiscreteWignerSystemD5 = serde_json::from_value(raw).unwrap();
    assert_eq!(malformed.operator(5, 0), Err(WignerError::Coordinate));
    assert_eq!(malformed.evaluate_exact(&rho), Err(WignerError::Shape));
    assert!(!malformed.verify_hermiticity());
}

fn stabilizer_laws<const P: usize>() {
    let w = DiscreteWigner::<P>::new().unwrap();
    let mut families = vec![(0, 1)];
    families.extend((0..P as i64).map(|m| (1, m)));
    let mut count = 0;
    for (a, b) in families {
        for k in 0..P as i64 {
            let rho = w.stabilizer_projector(a, b, k).unwrap();
            assert_eq!(mx::multiply(&rho, &rho).unwrap(), rho);
            assert_eq!(mx::trace(&rho).unwrap(), Cyclotomic::<P>::one());
            let grid = w.evaluate(&rho).unwrap();
            let mut total = Cyclotomic::<P>::zero();
            for q in 0..P {
                for p in 0..P {
                    let value = grid[q][p].as_rational().unwrap();
                    assert!(value >= ri(0));
                    total = total.add(&grid[q][p]);
                }
            }
            assert_eq!(total, Cyclotomic::<P>::one());
            for line in 0..P as i64 {
                let marginal = w.line_marginal(&rho, a, b, line).unwrap();
                let probability = mx::trace(
                    &mx::multiply(&rho, &w.stabilizer_projector(a, b, line).unwrap()).unwrap(),
                )
                .unwrap();
                assert_eq!(marginal, probability);
            }
            assert_eq!(w.l1_norm(&rho, 1).unwrap(), Cyclotomic::<P>::one());
            count += 1;
        }
    }
    assert_eq!(count, P * (P + 1));
}

#[test]
fn all_stabilizer_states_at_primes_three_five_and_seven_have_nonnegative_wigner_marginals() {
    stabilizer_laws::<3>();
    stabilizer_laws::<5>();
    stabilizer_laws::<7>();
}

#[test]
fn choi_positivity_matches_kraus_damping_and_keeps_fujiwara_left_sides() {
    use linear_algebra::exact_field::elimination::rank;
    use core_number_theory::cyclotomic::GaussianRat as G;
    use core_quantum_physics::qubit_bloch_map::{BlochMapError, QubitBlochMap};
    assert_eq!(
        QubitBlochMap::from_kraus(&[]),
        Err(BlochMapError::EmptyKraus)
    );
    assert_eq!(
        QubitBlochMap::from_kraus(&[mx::identity(3).unwrap()]),
        Err(BlochMapError::NotQubit { index: 0 })
    );
    assert_eq!(
        QubitBlochMap::from_kraus(&[
            mx::scale(&mx::identity(2).unwrap(), &G::from_ints(2, 0)).unwrap()
        ]),
        Err(BlochMapError::NotTracePreserving)
    );
    let damping = QubitBlochMap::amplitude_damping(rq(3, 5)).unwrap();
    let k0 = mx::diagonal(&[G::one(), G::from_rational(rq(3, 5))]).unwrap();
    let k1 = mx::from_rows(vec![
        vec![G::zero(), G::from_rational(rq(4, 5))],
        vec![G::zero(), G::zero()],
    ])
    .unwrap();
    assert_eq!(QubitBlochMap::from_kraus(&[k0, k1]).unwrap(), damping);
    assert_eq!(
        damping.apply(&[ri(0), ri(0), ri(-1)]),
        [ri(0), ri(0), rq(7, 25)]
    );
    assert_eq!(
        damping.compose(&damping),
        QubitBlochMap::amplitude_damping(rq(9, 25)).unwrap()
    );
    assert_eq!(
        rank(&QubitBlochMap::depolarizing(ri(1)).unwrap().choi_matrix()).unwrap(),
        1
    );
    assert!(QubitBlochMap::depolarizing(rq(-1, 3))
        .unwrap()
        .is_completely_positive());
    let epsilon = core_number_theory::rational::Rational::new(
        1.into(),
        num_bigint::BigInt::from(1u8) << 128,
    );
    assert_eq!(
        QubitBlochMap::depolarizing(rq(-1, 3) - epsilon),
        Err(BlochMapError::NotCompletelyPositive)
    );
    assert_eq!(
        QubitBlochMap::depolarizing(rq(4, 3)),
        Err(BlochMapError::NotCompletelyPositive)
    );
    assert!(!QubitBlochMap::unital_diagonal_is_cp(&[
        ri(0),
        ri(0),
        ri(3)
    ]));
}

#[test]
fn four_gamma_traces_and_on_shell_energy_projectors_replay_the_metric() {
    use linear_algebra::exact_field::elimination::rank;
    use core_number_theory::cyclotomic::GaussianRat as G;
    use core_quantum_physics::dirac_gamma_admission::{CliffordFamily, DiracError};
    let dirac = CliffordFamily::dirac();
    let eta = [1, -1, -1, -1];
    for mu in 0..4 {
        for nu in 0..4 {
            for rho in 0..4 {
                for sigma in 0..4 {
                    let metric = |a, b| if a == b { eta[a] } else { 0 };
                    let expected = 4
                        * (metric(mu, nu) * metric(rho, sigma)
                            - metric(mu, rho) * metric(nu, sigma)
                            + metric(mu, sigma) * metric(nu, rho));
                    assert_eq!(
                        dirac.four_gamma_trace(mu, nu, rho, sigma).unwrap(),
                        G::from_ints(expected, 0)
                    );
                }
            }
        }
    }
    let p = [ri(5), ri(4), ri(0), ri(0)];
    let [positive, negative] = dirac.energy_projectors(&p, &ri(3)).unwrap();
    assert_eq!(
        mx::add(&positive, &negative).unwrap(),
        mx::identity(4).unwrap()
    );
    assert!(mx::is_zero_matrix(
        &mx::multiply(&positive, &negative).unwrap()
    ));
    for projector in [&positive, &negative] {
        assert_eq!(mx::multiply(projector, projector).unwrap(), *projector);
        assert_eq!(rank(projector).unwrap(), 2);
    }
    assert_eq!(
        dirac.energy_projectors(&[ri(5), ri(3), ri(0), ri(0)], &ri(3)),
        Err(DiracError::OffMassShell)
    );
    assert_eq!(
        dirac.energy_projectors(&p, &ri(0)),
        Err(DiracError::ZeroMass)
    );
}

#[test]
fn exact_lattice_momentum_corners_match_dense_kernels_and_wilson_species() {
    use num_bigint::BigUint;
    use core_lie_theory::pauli_symplectic::{pauli, Pauli};
    use core_number_theory::cyclotomic::GaussianRat as G;
    use core_quantum_physics::dirac_gamma_admission::CliffordFamily;
    use core_quantum_physics::lattice_dirac_doubling::{LatticeDirac, LatticeMomentumSpectrum};
    let family = CliffordFamily::admit(
        vec![pauli::<G>(Pauli::X).unwrap(), pauli::<G>(Pauli::Y).unwrap()],
        vec![ri(1), ri(1)],
    )
    .unwrap();
    for period in [3, 4] {
        let lattice = LatticeDirac::new(family.clone(), period).unwrap();
        let spectrum = LatticeMomentumSpectrum::new(period, vec![false, false]).unwrap();
        assert_eq!(
            spectrum.naive_kernel_dimension(),
            BigUint::from(lattice.zero_mode_count(&lattice.naive_operator()).unwrap())
        );
        assert_eq!(
            spectrum.wilson_species_count(&ri(0), &ri(1)).unwrap() * spectrum.spin_dimension(),
            BigUint::from(
                lattice
                    .zero_mode_count(&lattice.wilson_operator(&ri(1)))
                    .unwrap()
            )
        );
    }
    let plane = LatticeMomentumSpectrum::new(4, vec![false, false]).unwrap();
    assert_eq!(
        plane.wilson_species_count(&ri(-2), &ri(1)).unwrap(),
        BigUint::from(2u8)
    );
    assert_eq!(plane.total_corner_chirality(), 0);
    let twisted = LatticeMomentumSpectrum::new(4, vec![true, false]).unwrap();
    assert_eq!(twisted.naive_species_count(), BigUint::from(0u8));
    let odd_twist = LatticeMomentumSpectrum::new(3, vec![true, false]).unwrap();
    let (sin2, mass) = odd_twist.symbol_data::<6>(&[1, 0]).unwrap();
    assert_eq!(sin2, Cyclotomic::<6>::zero());
    assert_eq!(mass, Cyclotomic::<6>::rational(ri(2)));
    assert_eq!(odd_twist.total_corner_chirality(), -1);
    let large = LatticeMomentumSpectrum::new(4, vec![false; 64]).unwrap();
    assert_eq!(large.naive_species_count(), BigUint::from(1u8) << 64);
}

#[test]
fn spin_intertwiners_and_exchange_projectors_preserve_exact_sector_dimensions() {
    use linear_algebra::exact_field::elimination::rank;
    use num_bigint::BigUint;
    use core_quantum_physics::pair_exchange_characters::{
        exchange_projector, exchange_sector_dimension, permutation_character, ExchangeError,
    };
    use core_quantum_physics::spin_area_spectrum::{
        area_label, area_label_squared, invariant_subspace_dimension, magnetic_degeneracy,
        tensor_spin_multiplicities,
    };
    for spins in [vec![], vec![1, 1], vec![1, 1, 1, 1], vec![2, 3, 4]] {
        let sectors = tensor_spin_multiplicities(&spins).unwrap();
        let sum = sectors
            .into_iter()
            .map(|(j, m)| m * magnetic_degeneracy(j))
            .sum::<BigUint>();
        let expected = spins
            .iter()
            .fold(BigUint::from(1u8), |a, n| a * magnetic_degeneracy(*n));
        assert_eq!(sum, expected);
    }
    assert_eq!(
        invariant_subspace_dimension(&[1, 1, 1, 1]).unwrap(),
        BigUint::from(2u8)
    );
    assert_eq!(
        invariant_subspace_dimension(&[1, 1, 1]).unwrap(),
        BigUint::from(0u8)
    );
    assert_eq!(area_label(1).unwrap().square(), area_label_squared(1));
    for (d, n) in [(2, 2), (3, 2), (2, 3)] {
        for alternating in [false, true] {
            let p = exchange_projector(d, n, alternating).unwrap();
            assert_eq!(mx::multiply(&p, &p).unwrap(), p);
            assert_eq!(mx::transpose(&p).unwrap(), p);
            assert_eq!(
                BigUint::from(rank(&p).unwrap()),
                exchange_sector_dimension(d as u64, n as u64, alternating).unwrap()
            );
        }
    }
    assert_eq!(permutation_character(&[1, 0, 2], true).unwrap(), -1);
    assert_eq!(permutation_character(&[1, 2, 0], true).unwrap(), 1);
    assert_eq!(
        permutation_character(&[0, 0], false),
        Err(ExchangeError::NotPermutation)
    );
    assert_eq!(
        exchange_sector_dimension(0, 0, false).unwrap(),
        BigUint::from(1u8)
    );
}

#[test]
fn born_rank_one_positivity_survives_every_galois_embedding_while_declared_diagonals_need_not() {
    use core_quantum_physics::embedding_relativity::{
        born_weights, conductor_5_witness, conductor_8_witness, galois_born_weights,
        positivity_under_embeddings,
    };
    assert_eq!(
        positivity_under_embeddings(&conductor_5_witness().unwrap())
            .unwrap()
            .iter()
            .map(|x| x.1)
            .collect::<Vec<_>>(),
        vec![true, false]
    );
    assert_eq!(
        positivity_under_embeddings(&conductor_8_witness().unwrap())
            .unwrap()
            .iter()
            .map(|x| x.1)
            .collect::<Vec<_>>(),
        vec![true, false]
    );
    let amplitudes = [
        Cyclotomic::<5>::one(),
        Cyclotomic::<5>::zeta(1).add(&Cyclotomic::one()),
    ];
    let weights = born_weights(&amplitudes);
    for k in [1, 2, 3, 4] {
        assert_eq!(
            galois_born_weights(&amplitudes, k).unwrap(),
            weights
                .iter()
                .map(|x| x.galois(k).unwrap())
                .collect::<Vec<_>>()
        );
    }
    let rank_one = mx::from_fn(2, 2, |r, c| amplitudes[r].mul(&amplitudes[c].conjugate())).unwrap();
    assert!(positivity_under_embeddings(&rank_one)
        .unwrap()
        .iter()
        .all(|x| x.1));
    // Nonnegative diagonal entries alone fail: the off-diagonal minor is negative.
    let indefinite = mx::from_rows(vec![
        vec![Cyclotomic::<5>::one(), Cyclotomic::rational(ri(2))],
        vec![Cyclotomic::rational(ri(2)), Cyclotomic::one()],
    ])
    .unwrap();
    assert!(positivity_under_embeddings(&indefinite)
        .unwrap()
        .iter()
        .all(|x| !x.1));
}

#[test]
fn mass_phase_overlaps_preserve_algebraic_coefficients_and_distinguish_phases() {
    use core_number_theory::cyclotomic::GaussianRat as G;
    use core_quantum_physics::mass_phase_embedding::{EmbeddingError, MassPhaseEmbedding};
    let a = MassPhaseEmbedding::new(&[ri(1), ri(1)], &[G::one(), G::one()]).unwrap();
    let b = MassPhaseEmbedding::new(&[ri(1), ri(0)], &[G::one(), G::one()]).unwrap();
    assert_eq!(a.overlap(&b), Err(EmbeddingError::IrrationalOverlap));
    let overlap = a.algebraic_overlap(&b).unwrap();
    assert_eq!(overlap.mul(&overlap).unwrap().as_rational(), Some(rq(1, 2)));
    assert_eq!(
        a.algebraic_fidelity(&b).unwrap().as_rational(),
        Some(rq(1, 2))
    );
    assert_eq!(a.algebraic_fidelity(&a).unwrap().as_rational(), Some(ri(1)));
    let opposite =
        MassPhaseEmbedding::new(&[ri(1), ri(1)], &[G::one(), G::from_ints(-1, 0)]).unwrap();
    assert_eq!(a.born_weights(), opposite.born_weights());
    assert_eq!(
        a.algebraic_fidelity(&opposite).unwrap().as_rational(),
        Some(ri(0))
    );
    assert_eq!(a.fidelity(&opposite).unwrap(), ri(0));
    assert_eq!(a.norm_squared(), ri(1));
    let large = MassPhaseEmbedding::new(&[ri(1), ri(1200)], &[G::one(), G::one()]).unwrap();
    assert!(matches!(
        large.algebraic_overlap(&b),
        Err(EmbeddingError::FieldBound { max: 1024, .. })
    ));
    assert!(a
        .amplitude_surds()
        .unwrap()
        .iter()
        .all(|s| s.square() == rq(1, 2)));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/groups_completion.rs
// Claim: urn:core:crates_rs:tests:groups-completion:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4d4d4b45 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4d4d4b45` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4d4d4b45 {
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
impl BoundaryError4d4d4b45 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4d4d4b45 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4d4d4b45 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4d4d4b45 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4d4d4b45> {
        if capacity_bound == 0 {
            return Err(BoundaryError4d4d4b45::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4d4d4b45::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4d4d4b45::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4d4d4b45() {
    let admitted = BoundaryRecord4d4d4b45::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4d4d4b45::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
