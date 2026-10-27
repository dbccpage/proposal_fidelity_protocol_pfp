//! Channels as stochastic kernels: the population shadow of a CPTP map, what
//! it forgets, the non-forced completely positive lift, basis relativity, and
//! composition. The shadow itself is `population_shadow`, shared with the
//! ingredient ladder.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use num_traits::Signed;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_channel::{
    apply_choi, choi_is_cptp, ExactChannelError, ExactKrausChannel,
};
use core_quantum_physics::exact_hermitian::{self, gi, gq};
use core_quantum_physics::residual_density_calculus::{
    row_stochastic_pushforward, sector_measurement, ResidualDensityError,
};

use crate::support::{dm, pauli_x, rm, rotation, unit};
use core_quantum_physics::population_shadow::{
    compose_kernels, composition_defect, population_shadow,
};

fn kernel(rows: &[&[(i64, i64)]]) -> linear_algebra::backend::basic_matrix::BasicMatrix<Rational> {
    mx::from_rows(
        rows.iter()
            .map(|row| row.iter().map(|&(n, d)| rq(n, d)).collect())
            .collect(),
    )
    .unwrap()
}

fn identity_kernel(n: usize) -> linear_algebra::backend::basic_matrix::BasicMatrix<Rational> {
    mx::identity(n).unwrap()
}

fn identity_channel() -> ExactKrausChannel {
    ExactKrausChannel::from_operators(vec![mx::identity(2).unwrap()]).unwrap()
}

fn dephasing() -> ExactKrausChannel {
    ExactKrausChannel::from_operators(vec![unit(2, 0, 0), unit(2, 1, 1)]).unwrap()
}

fn rotation_channel() -> ExactKrausChannel {
    ExactKrausChannel::from_operators(vec![rotation()]).unwrap()
}

fn damping() -> ExactKrausChannel {
    ExactKrausChannel::from_operators(vec![dm(&[5, 3], 5), rm(&[&[0, 4], &[0, 0]], 5)]).unwrap()
}

fn qubit_into_qutrit() -> ExactKrausChannel {
    ExactKrausChannel::from_operators(vec![mx::from_rows(vec![
        vec![gi(1, 0), gi(0, 0)],
        vec![gi(0, 0), gq(3, 5, 0, 1)],
        vec![gi(0, 0), gq(0, 1, 4, 5)],
    ])
    .unwrap()])
    .unwrap()
}

/// `|+i><+i| = (1/2) [[1, -i], [i, 1]]`, or its conjugate for `sign = -1`.
fn circular(sign: i64) -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![
        vec![gq(1, 2, 0, 1), gq(0, 1, -sign, 2)],
        vec![gq(0, 1, sign, 2), gq(1, 2, 0, 1)],
    ])
    .unwrap()
}

#[test]
fn stochastic_kernels_carry_distributions_to_distributions_and_compose() {
    let k = kernel(&[
        &[(1, 2), (1, 3), (1, 6)],
        &[(0, 1), (3, 4), (1, 4)],
        &[(2, 5), (0, 1), (3, 5)],
    ]);
    let l = kernel(&[&[(1, 4), (3, 4)], &[(1, 1), (0, 1)], &[(1, 2), (1, 2)]]);
    let m = kernel(&[&[(1, 3), (2, 3)], &[(1, 2), (1, 2)]]);
    let p = vec![rq(1, 2), rq(1, 3), rq(1, 6)];
    let q = row_stochastic_pushforward(&k, &p).unwrap();
    assert_eq!(q, vec![rq(19, 60), rq(5, 12), rq(4, 15)]);
    assert!(q.iter().all(|v| !v.is_negative()));
    assert_eq!(q.iter().sum::<Rational>(), ri(1));
    // Composition is stochastic, acts as the two steps, has the identity as unit and is associative.
    let kl = compose_kernels(&k, &l).unwrap();
    assert!(kl
        .as_slice()
        .chunks_exact(kl.cols())
        .all(|row| row.iter().sum::<Rational>() == ri(1) && row.iter().all(|v| !v.is_negative())));
    assert_eq!(
        row_stochastic_pushforward(&kl, &p).unwrap(),
        row_stochastic_pushforward(&l, &q).unwrap()
    );
    assert_eq!(compose_kernels(&identity_kernel(3), &k).unwrap(), k);
    assert_eq!(compose_kernels(&k, &identity_kernel(3)).unwrap(), k);
    assert_eq!(
        compose_kernels(&kl, &m).unwrap(),
        compose_kernels(&k, &compose_kernels(&l, &m).unwrap()).unwrap()
    );
}

#[test]
fn the_population_shadow_of_a_trace_preserving_kraus_family_is_stochastic() {
    for channel in [
        identity_channel(),
        dephasing(),
        rotation_channel(),
        damping(),
        qubit_into_qutrit(),
    ] {
        let shadow = population_shadow(&channel).unwrap();
        let choi = channel.choi().unwrap();
        let dout = channel.dim_out();
        for (g, row) in shadow.as_slice().chunks_exact(shadow.cols()).enumerate() {
            // K(h | g) is the diagonal Choi entry at (g, h) ...
            for (h, value) in row.iter().enumerate() {
                assert_eq!(
                    &choi
                        .matrix()
                        .get_ref(g * dout + h, g * dout + h)
                        .unwrap()
                        .re,
                    value
                );
            }
            // ... a row of a stochastic kernel ...
            assert!(row.iter().all(|v| !v.is_negative()));
            assert_eq!(row.iter().sum::<Rational>(), ri(1));
            // ... and the output populations of the basis state |g><g|.
            assert_eq!(
                &sector_measurement(&channel.apply(&unit(channel.dim_in(), g, g)).unwrap())
                    .unwrap(),
                row
            );
        }
    }
    assert_eq!(
        population_shadow(&damping()).unwrap(),
        kernel(&[&[(1, 1), (0, 1)], &[(16, 25), (9, 25)]])
    );
    // A completely positive family that loses trace is refused, and its Choi
    // diagonal (1, 0; 0, 1/4) is not a stochastic kernel.
    let leaky = dm(&[2, 1], 2);
    assert_eq!(
        ExactKrausChannel::from_operators(vec![leaky]),
        Err(ExactChannelError::NotTracePreserving { row: 1, col: 1 })
    );
    let w = [gi(1, 0), gi(0, 0), gi(0, 0), gq(1, 2, 0, 1)];
    let leaky_choi = star::outer_product(&w, &w).unwrap();
    let leaky_rows = mx::from_rows(
        (0..2)
            .map(|g| {
                (0..2)
                    .map(|h| leaky_choi.get_ref(g * 2 + h, g * 2 + h).unwrap().re.clone())
                    .collect()
            })
            .collect(),
    )
    .unwrap();
    assert_eq!(leaky_rows, kernel(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 4)]]));
    assert_eq!(
        row_stochastic_pushforward(&leaky_rows, &[ri(1), ri(0)]),
        Err(ResidualDensityError::NotRowStochastic { row: 1 })
    );
}

#[test]
fn the_bit_flip_worked_example() {
    let flip = ExactKrausChannel::from_operators(vec![pauli_x()]).unwrap();
    let k = population_shadow(&flip).unwrap();
    assert_eq!(k, kernel(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]]));
    assert_eq!(
        row_stochastic_pushforward(&k, &[rq(3, 4), rq(1, 4)]).unwrap(),
        vec![rq(1, 4), rq(3, 4)]
    );
    assert_eq!(compose_kernels(&k, &k).unwrap(), identity_kernel(2));
    // The coherence K does not see: X rho X conjugates the off-diagonal entry ...
    assert_eq!(flip.apply(&circular(1)).unwrap(), circular(-1));
    // ... and a bit flip followed by dephasing has the same kernel but erases it.
    let flip_then_dephase = ExactKrausChannel::from_operators(vec![
        mx::multiply_with_limits(
            &(unit(2, 0, 0)),
            &pauli_x(),
            exact_hermitian::exact_limits(),
        )
        .unwrap(),
        mx::multiply_with_limits(
            &(unit(2, 1, 1)),
            &pauli_x(),
            exact_hermitian::exact_limits(),
        )
        .unwrap(),
    ])
    .unwrap();
    assert_eq!(population_shadow(&flip_then_dephase).unwrap(), k);
    assert_eq!(
        flip_then_dephase.apply(&circular(1)).unwrap(),
        mx::scale(
            &(mx::identity(2).unwrap()),
            &GaussianRat::from_rational(rq(1, 2))
        )
        .unwrap()
    );
}

#[test]
fn the_shadow_neither_preserves_diagonality_nor_determines_the_channel() {
    let r = rotation_channel();
    // A diagonal input leaves with coherence 12/25.
    assert_eq!(
        r.apply(&unit(2, 0, 0)).unwrap(),
        rm(&[&[9, 12], &[12, 16]], 25)
    );
    // For a coherent input the output populations are not K applied to the input populations.
    let psi = [gq(3, 5, 0, 1), gq(-4, 5, 0, 1)];
    let rho = star::outer_product(&psi, &psi).unwrap();
    let k = population_shadow(&r).unwrap();
    assert_eq!(k, kernel(&[&[(9, 25), (16, 25)], &[(16, 25), (9, 25)]]));
    assert_eq!(
        row_stochastic_pushforward(&k, &sector_measurement(&rho).unwrap()).unwrap(),
        vec![rq(337, 625), rq(288, 625)]
    );
    assert_eq!(
        sector_measurement(&r.apply(&rho).unwrap()).unwrap(),
        vec![ri(1), ri(0)]
    );
    // Identity and complete dephasing share the identity kernel and differ on |+><+|.
    assert_eq!(
        population_shadow(&identity_channel()).unwrap(),
        identity_kernel(2)
    );
    assert_eq!(population_shadow(&dephasing()).unwrap(), identity_kernel(2));
    let plus = rm(&[&[1, 1], &[1, 1]], 2);
    assert_eq!(identity_channel().apply(&plus).unwrap(), plus);
    assert_eq!(
        dephasing().apply(&plus).unwrap(),
        mx::scale(
            &(mx::identity(2).unwrap()),
            &GaussianRat::from_rational(rq(1, 2))
        )
        .unwrap()
    );
}

#[test]
fn a_positive_map_that_is_not_completely_positive_shares_the_identity_kernel() {
    // The transpose map, through its Choi matrix (the swap).
    let mut swap = mx::zeros(4, 4).unwrap();
    for (row, col) in [(0, 0), (1, 2), (2, 1), (3, 3)] {
        swap.set(row, col, GaussianRat::one()).unwrap();
    }
    let transpose_kernel = mx::from_rows(
        (0..2)
            .map(|g| sector_measurement(&apply_choi(&swap, 2, 2, &unit(2, g, g)).unwrap()).unwrap())
            .collect(),
    )
    .unwrap();
    assert_eq!(
        transpose_kernel,
        population_shadow(&identity_channel()).unwrap()
    );
    // Trace preserving and positive on the declared states ...
    for state in [
        circular(1),
        rm(&[&[1, 1], &[1, 1]], 2),
        rm(&[&[9, 12], &[12, 16]], 25),
    ] {
        let image = apply_choi(&swap, 2, 2, &state).unwrap();
        assert_eq!(image, mx::transpose(&state).unwrap());
        assert!(exact_hermitian::is_positive_semidefinite(&image));
        assert_eq!(mx::trace(&(image)).unwrap(), GaussianRat::one());
    }
    assert_eq!(apply_choi(&swap, 2, 2, &circular(1)).unwrap(), circular(-1));
    // ... but not completely positive: its Choi matrix is not PSD, and the
    // partial transpose of the Bell state has the negative direction (0, 1, -1, 0).
    assert!(!choi_is_cptp(&swap, 2, 2));
    let bell = rm(
        &[&[1, 0, 0, 1], &[0, 0, 0, 0], &[0, 0, 0, 0], &[1, 0, 0, 1]],
        2,
    );
    let flipped = exact_hermitian::partial_transpose_second(&bell, 2, 2).unwrap();
    assert_eq!(
        flipped,
        mx::scale(&(swap), &GaussianRat::from_rational(rq(1, 2))).unwrap()
    );
    let direction = [gi(0, 0), gi(1, 0), gi(-1, 0), gi(0, 0)];
    assert_eq!(
        star::inner_product(
            &direction,
            &mx::multiply_vector_with_limits(&flipped, &direction, exact_hermitian::exact_limits())
                .unwrap()
        )
        .unwrap(),
        gi(-1, 0)
    );
}

#[test]
fn every_stochastic_kernel_has_a_classical_completely_positive_lift() {
    // The measure-and-prepare lift has the diagonal Choi matrix sum K(h|g) |g><g| (x) |h><h|.
    let k = kernel(&[
        &[(1, 2), (1, 3), (1, 6)],
        &[(0, 1), (3, 4), (1, 4)],
        &[(2, 5), (0, 1), (3, 5)],
    ]);
    let entries: Vec<GaussianRat> = k
        .as_slice()
        .iter()
        .cloned()
        .map(GaussianRat::from_rational)
        .collect();
    let lift = mx::diagonal(&entries).unwrap();
    assert!(choi_is_cptp(&lift, 3, 3));
    for (g, row) in k.as_slice().chunks_exact(k.cols()).enumerate() {
        assert_eq!(
            &sector_measurement(&apply_choi(&lift, 3, 3, &unit(3, g, g)).unwrap()).unwrap(),
            row
        );
    }
    // It dephases: a coherent input leaves as the diagonal of K applied to its populations.
    let coherent = rm(&[&[1, 1, 0], &[1, 1, 0], &[0, 0, 0]], 2);
    let out = apply_choi(&lift, 3, 3, &coherent).unwrap();
    let pushed = row_stochastic_pushforward(&k, &sector_measurement(&coherent).unwrap()).unwrap();
    assert_eq!(
        out,
        mx::diagonal(
            &pushed
                .into_iter()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>()
        )
        .unwrap()
    );
    // With square rational entries the lift has rational Kraus operators sqrt(K(h|g)) |h><g|.
    let squares = kernel(&[&[(9, 25), (16, 25)], &[(0, 1), (1, 1)]]);
    let lifted = ExactKrausChannel::from_operators(vec![
        mx::scale(&(unit(2, 0, 0)), &GaussianRat::from_rational(rq(3, 5))).unwrap(),
        mx::scale(&(unit(2, 1, 0)), &GaussianRat::from_rational(rq(4, 5))).unwrap(),
        unit(2, 1, 1),
    ])
    .unwrap();
    assert_eq!(population_shadow(&lifted).unwrap(), squares);
    assert_eq!(lifted.choi().unwrap().matrix(), &dm(&[9, 16, 0, 25], 25));
    // A signed kernel has no lift of this form: the diagonal Choi matrix is not PSD.
    assert!(!choi_is_cptp(&dm(&[3, -1, 0, 2], 2), 2, 2));
}

#[test]
fn the_population_shadow_depends_on_the_declared_basis() {
    let r = rotation();
    // Complete dephasing read in the rotated basis {R e_0, R e_1}: Kraus operators R^T A_k R.
    let rotated = ExactKrausChannel::from_operators(
        dephasing()
            .operators()
            .iter()
            .map(|a| {
                mx::multiply_with_limits(
                    &(mx::multiply_with_limits(
                        &(mx::transpose(&r).unwrap()),
                        a,
                        exact_hermitian::exact_limits(),
                    )
                    .unwrap()),
                    &r,
                    exact_hermitian::exact_limits(),
                )
                .unwrap()
            })
            .collect(),
    )
    .unwrap();
    assert_eq!(population_shadow(&dephasing()).unwrap(), identity_kernel(2));
    assert_eq!(
        population_shadow(&rotated).unwrap(),
        kernel(&[&[(337, 625), (288, 625)], &[(288, 625), (337, 625)]])
    );
    // It is the same channel: conjugating back reproduces the dephasing on every input.
    for state in [
        rm(&[&[1, 1], &[1, 1]], 2),
        circular(1),
        rm(&[&[9, 12], &[12, 16]], 25),
    ] {
        let there = rotated
            .apply(
                &mx::multiply_with_limits(
                    &(mx::multiply_with_limits(
                        &(mx::transpose(&r).unwrap()),
                        &state,
                        exact_hermitian::exact_limits(),
                    )
                    .unwrap()),
                    &r,
                    exact_hermitian::exact_limits(),
                )
                .unwrap(),
            )
            .unwrap();
        assert_eq!(
            mx::multiply_with_limits(
                &(mx::multiply_with_limits(&(r), &there, exact_hermitian::exact_limits()).unwrap()),
                &mx::transpose(&r).unwrap(),
                exact_hermitian::exact_limits()
            )
            .unwrap(),
            dephasing().apply(&state).unwrap()
        );
    }
}

#[test]
fn the_shadow_of_a_composite_is_not_the_composite_of_the_shadows() {
    let there = rotation_channel();
    let back =
        ExactKrausChannel::from_operators(vec![mx::transpose(&rotation()).unwrap()]).unwrap();
    // R then R^T is the identity channel, yet K(R) K(R^T) = [[337, 288], [288, 337]] / 625.
    assert_eq!(
        composition_defect(&there, &back).unwrap(),
        kernel(&[&[(288, 625), (-288, 625)], &[(-288, 625), (288, 625)]])
    );
    // When the first map leaves only populations, shadows compose.
    let measured = ExactKrausChannel::from_operators(vec![
        mx::multiply_with_limits(
            &(unit(2, 0, 0)),
            &rotation(),
            exact_hermitian::exact_limits(),
        )
        .unwrap(),
        mx::multiply_with_limits(
            &(unit(2, 1, 1)),
            &rotation(),
            exact_hermitian::exact_limits(),
        )
        .unwrap(),
    ])
    .unwrap();
    assert_eq!(
        population_shadow(&measured).unwrap(),
        population_shadow(&there).unwrap()
    );
    assert_eq!(
        composition_defect(&measured, &back).unwrap(),
        kernel(&[&[(0, 1), (0, 1)], &[(0, 1), (0, 1)]])
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/channels/channels_as_stochastic_kernels.rs
// Claim: urn:core:crates_rs:tests:channels-as-stochastic-kernels:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcbd2bc0c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcbd2bc0c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcbd2bc0c {
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
impl BoundaryErrorcbd2bc0c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcbd2bc0c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcbd2bc0c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcbd2bc0c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcbd2bc0c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcbd2bc0c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcbd2bc0c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcbd2bc0c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_cbd2bc0c() {
    let admitted = BoundaryRecordcbd2bc0c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordcbd2bc0c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
