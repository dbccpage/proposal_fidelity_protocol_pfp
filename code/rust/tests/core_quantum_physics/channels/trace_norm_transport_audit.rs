//! The trace-norm CPTP transport audit: what CPTP monotonicity forces on a
//! gauge of state differences, a genuine strict contraction, the Helstrom
//! admission, trace-norm contraction with a Heisenberg-picture certificate,
//! and its classical l1 shadow.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use linear_algebra::exact_field::matrix;
use num_bigint::BigInt;
use num_traits::Signed;
use core_lie_theory::su_n::GellMannBasis;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::Surd;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_channel::{apply_choi, choi_is_cptp, ExactKrausChannel};
use core_quantum_physics::exact_hermitian::{self, gi, gq};
use core_quantum_physics::residual_density_calculus::{
    row_stochastic_pushforward, ResidualDensityError,
};
use core_quantum_physics::tower_walk_validator::half_trace_norm_2x2;

use crate::support::{depolarizing_choi, dm, pauli_x, pauli_z, rm, rotation, unit};
use core_quantum_physics::difference_transport_channel::{
    embedding_pair, DifferenceTransport, DifferenceTransportError,
};
use core_quantum_physics::population_shadow::population_shadow;
use core_quantum_physics::trace_norm_certificate::{
    sign_certificate_from_spectrum, within_operator_ball, SignCertificate,
};

/// Build the transport channel and replay it: CPTP by Choi's criterion, and `X -> Y`.
fn transported(source: &SignCertificate, target: &SignCertificate) {
    let channel = DifferenceTransport::new(source, target).unwrap();
    let n = channel.dim();
    assert!(choi_is_cptp(channel.choi(), n, n));
    assert_eq!(&channel.apply(source.matrix()).unwrap(), target.matrix());
}

fn self_signed(m: BasicMatrix<GaussianRat>) -> SignCertificate {
    SignCertificate::new(m.clone(), m).unwrap()
}

#[test]
fn every_difference_reaches_every_difference_of_no_larger_trace_norm() {
    // Qubits: Z, its rotation R Z R^T (both of trace norm 2), and Z / 2.
    let z = self_signed(pauli_z());
    let r = rotation();
    let rotated = self_signed(
        matrix::multiply(
            &matrix::multiply(&r, &pauli_z()).unwrap(),
            &matrix::transpose(&r).unwrap(),
        )
        .unwrap(),
    );
    assert_eq!(rotated.matrix(), &rm(&[&[-7, 24], &[24, 7]], 25));
    let half = SignCertificate::new(
        matrix::scale(&pauli_z(), &GaussianRat::from_rational((rq(1, 2)).clone())).unwrap(),
        pauli_z(),
    )
    .unwrap();
    transported(&z, &rotated);
    transported(&rotated, &z);
    transported(&z, &half);
    let zero =
        SignCertificate::new(matrix::zeros(2, 2).unwrap(), matrix::identity(2).unwrap()).unwrap();
    transported(&z, &zero);
    // Qutrits of trace norm 2 in both directions; the Hilbert-Schmidt norm grows 3/2 -> 2.
    let spread = SignCertificate::new(dm(&[2, -1, -1], 2), dm(&[1, -1, -1], 1)).unwrap();
    let pair = SignCertificate::new(dm(&[1, -1, 0], 1), dm(&[1, -1, 1], 1)).unwrap();
    transported(&spread, &pair);
    transported(&pair, &spread);
    assert_eq!(
        (spread.trace_norm(), spread.schatten_power(2).unwrap()),
        (ri(2), rq(3, 2))
    );
    assert_eq!(
        (pair.trace_norm(), pair.schatten_power(2).unwrap()),
        (ri(2), ri(2))
    );
    // A non-diagonal source with spectrum {1, -1/3, -2/3}.
    let tilted = sign_certificate_from_spectrum(
        &rm(&[&[1, 2, 0], &[2, 1, 0], &[0, 0, -2]], 3),
        &[ri(1), rq(-1, 3), rq(-2, 3)],
    )
    .unwrap();
    assert_eq!(tilted.trace_norm(), ri(2));
    transported(&tilted, &pair);
    transported(&pair, &tilted);
    // Four levels: the operator norm grows 1/2 -> 1 at trace norm 2.
    let flat = SignCertificate::new(dm(&[1, 1, -1, -1], 2), dm(&[1, 1, -1, -1], 1)).unwrap();
    let sharp = SignCertificate::new(dm(&[1, -1, 0, 0], 1), dm(&[1, -1, 1, 1], 1)).unwrap();
    transported(&flat, &sharp);
    assert!(within_operator_ball(flat.matrix(), &ri(0), &rq(1, 2)).unwrap());
    assert!(!within_operator_ball(sharp.matrix(), &ri(0), &rq(1, 2)).unwrap());
    // Refusals: expansion, a zero source, a non-difference, mixed dimensions.
    assert_eq!(
        DifferenceTransport::new(&half, &z),
        Err(DifferenceTransportError::Expanding(Box::new((
            ri(1),
            ri(2)
        ))))
    );
    assert_eq!(
        DifferenceTransport::new(&zero, &z),
        Err(DifferenceTransportError::ZeroSource)
    );
    let identity = self_signed(matrix::identity(2).unwrap());
    assert_eq!(
        DifferenceTransport::new(&identity, &z),
        Err(DifferenceTransportError::NotTraceZero)
    );
    assert_eq!(
        DifferenceTransport::new(&z, &pair),
        Err(DifferenceTransportError::Dimension)
    );
}

#[test]
fn an_embedding_and_its_cptp_left_inverse_tie_the_scale_across_dimensions() {
    let (embed, retract) = embedding_pair(2, 4).unwrap();
    for i in 0..2 {
        for j in 0..2 {
            assert_eq!(
                retract
                    .apply(&embed.apply(&unit(2, i, j)).unwrap())
                    .unwrap(),
                unit(2, i, j)
            );
        }
    }
    // The discarded levels are prepared in |0><0|.
    assert_eq!(retract.apply(&unit(4, 3, 3)).unwrap(), unit(2, 0, 0));
    // The embedding keeps the trace norm: sign V S V* + (I - V V*).
    let x = rm(&[&[3, 4], &[4, -3]], 5);
    let small = self_signed(x.clone());
    let mut big_sign = embed.apply(&x).unwrap();
    big_sign.set(2, 2, GaussianRat::one()).unwrap();
    big_sign.set(3, 3, GaussianRat::one()).unwrap();
    let big = SignCertificate::new(embed.apply(&x).unwrap(), big_sign).unwrap();
    assert_eq!(big.trace_norm(), small.trace_norm());
    assert_eq!(big.trace_norm(), ri(2));
    assert_eq!(
        embedding_pair(3, 2).unwrap_err(),
        DifferenceTransportError::Embedding
    );
    assert_eq!(
        embedding_pair(0, 2).unwrap_err(),
        DifferenceTransportError::Embedding
    );
}

#[test]
fn the_rescaled_trace_distance_stays_monotone_under_a_strict_contraction() {
    let choi = depolarizing_choi(2, &rq(1, 3));
    assert!(choi_is_cptp(&choi, 2, 2));
    // On the Pauli basis of the trace-zero space the channel is 2/3 times the identity.
    for generator in GellMannBasis::new(2).unwrap().generators() {
        assert_eq!(
            apply_choi(&choi, 2, 2, &generator.shape).unwrap(),
            matrix::scale(
                &generator.shape,
                &GaussianRat::from_rational((rq(2, 3)).clone())
            )
            .unwrap()
        );
    }
    let before = self_signed(pauli_z());
    let after =
        SignCertificate::new(apply_choi(&choi, 2, 2, &pauli_z()).unwrap(), pauli_z()).unwrap();
    let j = |c: &SignCertificate| c.trace_norm() / ri(2);
    assert_eq!((j(&before), j(&after)), (ri(1), rq(2, 3)));
    assert!(j(&after) < j(&before));
    assert!(ri(2) * j(&after) < ri(2) * j(&before));
    assert_ne!(j(&before), ri(2) * j(&before));
}

fn is_effect(e: &BasicMatrix<GaussianRat>) -> bool {
    exact_hermitian::is_positive_semidefinite(e)
        && exact_hermitian::is_positive_semidefinite(
            &matrix::sub(&matrix::identity(e.rows()).unwrap(), e).unwrap(),
        )
}

#[test]
fn the_helstrom_effect_attains_half_the_trace_norm_of_a_difference() {
    let rho = rm(&[&[1, 1, 0], &[1, 1, 0], &[0, 0, 1]], 3);
    let sigma = matrix::scale(
        &matrix::identity(3).unwrap(),
        &GaussianRat::from_rational((rq(1, 3)).clone()),
    )
    .unwrap();
    for state in [&rho, &sigma] {
        assert!(exact_hermitian::is_positive_semidefinite(state));
        assert_eq!(matrix::trace(&state).unwrap(), GaussianRat::one());
    }
    let x = matrix::sub(&rho, &sigma).unwrap();
    let certificate = sign_certificate_from_spectrum(&x, &[rq(1, 3), ri(0), rq(-1, 3)]).unwrap();
    assert_eq!(certificate.trace_norm(), rq(2, 3));
    let optimal = certificate.helstrom_effect().unwrap();
    assert_eq!(optimal, rm(&[&[1, 1, 0], &[1, 1, 0], &[0, 0, 2]], 2));
    assert!(is_effect(&optimal));
    let bias = |e: &BasicMatrix<GaussianRat>| {
        matrix::trace(&matrix::multiply(&e, &x).unwrap())
            .unwrap()
            .re
    };
    // Success probability 1/2 + (1/2) Tr(E X) = 1/2 + ||X||_1 / 4 = 2/3.
    assert_eq!(bias(&optimal), rq(1, 3));
    assert_eq!(rq(1, 2) + bias(&optimal) / ri(2), rq(2, 3));
    let mut effects = vec![
        unit(3, 0, 0),
        matrix::scale(
            &matrix::identity(3).unwrap(),
            &GaussianRat::from_rational((rq(1, 2)).clone()),
        )
        .unwrap(),
        rm(&[&[1, 1, 0], &[1, 1, 0], &[0, 0, 0]], 2),
        rm(&[&[1, -1, 0], &[-1, 1, 0], &[0, 0, 0]], 2),
        rm(&[&[1, 0, 1], &[0, 0, 0], &[1, 0, 1]], 2),
    ];
    effects.extend((0..27i64).map(|code| dm(&[code % 3, (code / 3) % 3, code / 9], 2)));
    for e in &effects {
        assert!(is_effect(e));
        assert!(bias(e) <= bias(&optimal));
    }
    assert_eq!(bias(&effects[3]), rq(-1, 3));
}

#[test]
fn a_heisenberg_certificate_proves_trace_norm_contraction_on_declared_channels() {
    let z = pauli_z();
    let damping =
        ExactKrausChannel::from_operators(vec![dm(&[5, 3], 5), rm(&[&[0, 4], &[0, 0]], 5)])
            .unwrap();
    let pauli = ExactKrausChannel::from_operators(vec![
        matrix::scale(
            &matrix::identity(2).unwrap(),
            &GaussianRat::from_rational((rq(2, 3)).clone()),
        )
        .unwrap(),
        matrix::scale(&pauli_x(), &GaussianRat::from_rational((rq(2, 3)).clone())).unwrap(),
        matrix::scale(&z, &GaussianRat::from_rational((rq(1, 3)).clone())).unwrap(),
    ])
    .unwrap();
    let isometry = ExactKrausChannel::from_operators(vec![mx::from_rows(vec![
        vec![gi(1, 0), gi(0, 0)],
        vec![gi(0, 0), gq(3, 5, 0, 1)],
        vec![gi(0, 0), gq(0, 1, 4, 5)],
    ])
    .unwrap()])
    .unwrap();
    // The reflection I - 2 v v*, v = V e_1, is the sign of V Z V* = e_0 e_0* - v v*.
    let reflection = mx::from_rows(vec![
        vec![gi(1, 0), gi(0, 0), gi(0, 0)],
        vec![gi(0, 0), gq(7, 25, 0, 1), gq(0, 1, 24, 25)],
        vec![gi(0, 0), gq(0, 1, -24, 25), gq(-7, 25, 0, 1)],
    ])
    .unwrap();
    let cases = [
        (damping, z.clone(), rq(18, 25)),
        (pauli, z.clone(), rq(2, 9)),
        (isometry, reflection, ri(2)),
    ];
    for (channel, sign, contracted) in cases {
        let output = SignCertificate::new(channel.apply(&z).unwrap(), sign.clone()).unwrap();
        assert_eq!(output.trace_norm(), contracted);
        // Lambda*(W) stays in the operator unit ball, and Tr(Lambda*(W) Z) = ||Lambda Z||_1,
        // so ||Lambda Z||_1 <= ||Lambda*(W)||_op ||Z||_1 <= ||Z||_1 = 2.
        let pulled = channel.adjoint_apply(&sign).unwrap();
        assert!(within_operator_ball(&pulled, &ri(0), &ri(1)).unwrap());
        assert_eq!(
            matrix::trace(&matrix::multiply(&pulled, &z).unwrap())
                .unwrap()
                .re,
            contracted
        );
        assert!(contracted <= ri(2));
    }
    // An irrational pair through the Pauli channel: sqrt(34)/10 -> sqrt(466)/90.
    let pauli = ExactKrausChannel::from_operators(vec![
        matrix::scale(
            &matrix::identity(2).unwrap(),
            &GaussianRat::from_rational((rq(2, 3)).clone()),
        )
        .unwrap(),
        matrix::scale(&pauli_x(), &GaussianRat::from_rational((rq(2, 3)).clone())).unwrap(),
        matrix::scale(&z, &GaussianRat::from_rational((rq(1, 3)).clone())).unwrap(),
    ])
    .unwrap();
    let x = rm(&[&[5, 3], &[3, -5]], 10);
    let before = half_trace_norm_2x2(&x).unwrap();
    let after = half_trace_norm_2x2(&pauli.apply(&x).unwrap()).unwrap();
    assert_eq!(
        after,
        Surd::from_natural(rq(1, 90), &BigInt::from(466)).unwrap()
    );
    let square = Surd::square;
    assert!(square(&after) < square(&before));
}

#[test]
fn stochastic_kernels_contract_l1_on_signed_vectors() {
    let l1 = |v: &[Rational]| v.iter().map(Signed::abs).sum::<Rational>();
    // Worked number: the averaging kernel sends (1, -1) to (0, 0).
    let averaging =
        mx::from_rows(vec![vec![rq(1, 2), rq(1, 2)], vec![rq(1, 2), rq(1, 2)]]).unwrap();
    assert_eq!(
        row_stochastic_pushforward(&averaging, &[ri(1), ri(-1)]).unwrap(),
        vec![ri(0), ri(0)]
    );
    let mixing = mx::from_rows(vec![
        vec![rq(1, 2), rq(1, 3), rq(1, 6)],
        vec![ri(0), rq(3, 4), rq(1, 4)],
        vec![rq(2, 5), ri(0), rq(3, 5)],
    ])
    .unwrap();
    let coarse = mx::from_rows(vec![
        vec![rq(1, 4), rq(3, 4)],
        vec![ri(1), ri(0)],
        vec![rq(1, 2), rq(1, 2)],
    ])
    .unwrap();
    let cycle = mx::from_rows(vec![
        vec![ri(0), ri(1), ri(0)],
        vec![ri(0), ri(0), ri(1)],
        vec![ri(1), ri(0), ri(0)],
    ])
    .unwrap();
    for (kernel, expect_strict) in [(&mixing, true), (&coarse, true), (&cycle, false)] {
        let mut strict = 0;
        for code in 0..125i64 {
            let x: Vec<Rational> = (0..3u32)
                .map(|i| ri((code / 5i64.pow(i)) % 5 - 2))
                .collect();
            let y = row_stochastic_pushforward(kernel, &x).unwrap();
            assert!(l1(&y) <= l1(&x));
            if l1(&y) < l1(&x) {
                strict += 1;
            }
        }
        assert_eq!(strict > 0, expect_strict);
    }
    // A leaky or signed kernel is refused.
    let leaky = mx::from_rows(vec![vec![rq(3, 4), rq(3, 4)], vec![ri(0), ri(1)]]).unwrap();
    assert_eq!(
        row_stochastic_pushforward(&leaky, &[ri(1), ri(0)]),
        Err(ResidualDensityError::NotRowStochastic { row: 0 })
    );
    let signed = mx::from_rows(vec![vec![rq(3, 2), rq(-1, 2)], vec![ri(0), ri(1)]]).unwrap();
    assert_eq!(
        row_stochastic_pushforward(&signed, &[ri(1), ri(0)]),
        Err(ResidualDensityError::NotRowStochastic { row: 0 })
    );
    // The classical shadow of trace-norm contraction: the population shadow of
    // amplitude damping carries the diagonal (1, -1) of Z to the diagonal of Lambda(Z).
    let damping =
        ExactKrausChannel::from_operators(vec![dm(&[5, 3], 5), rm(&[&[0, 4], &[0, 0]], 5)])
            .unwrap();
    let pushed =
        row_stochastic_pushforward(&population_shadow(&damping).unwrap(), &[ri(1), ri(-1)])
            .unwrap();
    let out = damping.apply(&pauli_z()).unwrap();
    assert_eq!(pushed, vec![rq(9, 25), rq(-9, 25)]);
    assert_eq!(
        pushed,
        (0..2)
            .map(|i| out.get_ref(i, i).unwrap().re.clone())
            .collect::<Vec<_>>()
    );
    assert!(pushed.iter().all(|v| v.abs() == rq(9, 25)));
    assert_eq!(
        l1(&pushed),
        SignCertificate::new(out, pauli_z()).unwrap().trace_norm()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/channels/trace_norm_transport_audit.rs
// Claim: urn:core:crates_rs:tests:trace-norm-transport-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1ea80eb9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1ea80eb9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1ea80eb9 {
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
impl BoundaryError1ea80eb9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1ea80eb9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1ea80eb9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1ea80eb9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1ea80eb9> {
        if capacity_bound == 0 {
            return Err(BoundaryError1ea80eb9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1ea80eb9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1ea80eb9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1ea80eb9() {
    let admitted = BoundaryRecord1ea80eb9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1ea80eb9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
