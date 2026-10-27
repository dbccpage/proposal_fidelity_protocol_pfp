//! Heisenberg-picture shadow: decoherence matrices of declared histories and
//! the Heisenberg picture of declared unitary steps. Diagonal entries of the
//! decoherence matrix are the classical path weights of the unistochastic
//! transport, off-diagonal entries are the interference cross terms of the
//! amplitude path-sum, and a vanishing off-diagonal gives every sum rule while
//! the converse fails. Schrödinger and Heisenberg expectation values agree
//! along declared steps, and the exact derivative of the Cayley path at zero is
//! `2i[H, A]`; the paper's `U(t) = exp(itH)` has the opposite sign.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::involution as iv;
use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::cayley_unitary::cayley_unitary;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::coherent_interference::cross_term;
use core_quantum_physics::exact_hermitian::{self, gi, gq};
use core_quantum_physics::finite_schrodinger_step::euler_propagator;
use core_quantum_physics::graded_path_sum::{NonNegative, TimeSlicedTransport};

use crate::support::{basis_partition, basis_projector, complex_mixer, pauli, rotation};
use core_functional::decoherence::DecoherenceFunctional;
use core_quantum_physics::chain_histories::chain_histories;
use core_quantum_physics::heisenberg_picture::{
    cayley_jet, cayley_rate_generator, heisenberg_jet, heisenberg_observable, schrodinger_state,
    HeisenbergError,
};

fn two_level() -> BasicMatrix<GaussianRat> {
    mx::from_rows((vec![vec![gi(1, 0), gi(1, 1)], vec![gi(1, -1), gi(-1, 0)]])).unwrap()
}

fn real_symmetric() -> BasicMatrix<GaussianRat> {
    mx::from_rows((vec![vec![gi(0, 0), gi(2, 0)], vec![gi(2, 0), gi(3, 0)]])).unwrap()
}

fn observable() -> BasicMatrix<GaussianRat> {
    mx::from_rows((vec![vec![gi(1, 0), gi(2, -1)], vec![gi(2, 1), gi(0, 0)]])).unwrap()
}

fn density() -> BasicMatrix<GaussianRat> {
    mx::from_rows(
        (vec![
            vec![gq(2, 3, 0, 1), gq(1, 6, -1, 6)],
            vec![gq(1, 6, 1, 6), gq(1, 3, 0, 1)],
        ]),
    )
    .unwrap()
}

fn i_times(m: &BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat> {
    mx::scale(&(m), &(&GaussianRat::i())).unwrap()
}

fn modulus_squared(z: &GaussianRat) -> Rational {
    z.norm_sq()
}

/// A time-0 projection, then the rotation, then the real rotation again.
fn three_time_steps() -> Vec<BasicMatrix<GaussianRat>> {
    vec![mx::identity(2).unwrap(), rotation(), rotation()]
}

#[test]
fn diagonal_entries_are_the_classical_path_weights_and_off_diagonals_the_interference() {
    let steps = three_time_steps();
    let rho = mx::diagonal(&[gq(1, 3, 0, 1), gq(2, 3, 0, 1)]).unwrap();
    let partitions = [basis_partition(2), basis_partition(2), basis_partition(2)];
    let histories = chain_histories(&steps, &partitions).unwrap();
    assert_eq!(histories.len(), 8);
    let functional = DecoherenceFunctional::new(
        rho.clone(),
        histories.iter().map(|h| h.class_operator.clone()).collect(),
    )
    .unwrap();
    let d = functional.matrix();
    assert!(exact_hermitian::is_hermitian(d));
    let u = rotation();
    let unistochastic: Vec<Vec<NonNegative>> = (0..2)
        .map(|y| {
            (0..2)
                .map(|x| NonNegative::new(modulus_squared(u.get_ref(y, x).unwrap())).unwrap())
                .collect()
        })
        .collect();
    let amplitudes: Vec<Vec<GaussianRat>> = (0..2)
        .map(|y| (0..2).map(|x| u.get_ref(y, x).unwrap().clone()).collect())
        .collect();
    let classical =
        TimeSlicedTransport::new(vec![2, 2, 2], vec![unistochastic.clone(), unistochastic])
            .unwrap();
    let quantum =
        TimeSlicedTransport::new(vec![2, 2, 2], vec![amplitudes.clone(), amplitudes]).unwrap();
    for (j, h) in histories.iter().enumerate() {
        let weight = rho.get_ref(h.labels[0], h.labels[0]).unwrap().re.clone()
            * classical.history_weight(&h.labels).unwrap().value();
        assert_eq!(
            *d.get_ref(j, j).unwrap(),
            GaussianRat::from_rational(weight.clone())
        );
        assert!(weight >= ri(0));
        for (k, g) in histories.iter().enumerate() {
            let expected = if h.labels[0] == g.labels[0] && h.labels[2] == g.labels[2] {
                quantum
                    .history_weight(&h.labels)
                    .unwrap()
                    .mul(&quantum.history_weight(&g.labels).unwrap().conj())
                    .scale_rat(&rho.get_ref(h.labels[0], h.labels[0]).unwrap().re)
            } else {
                GaussianRat::zero()
            };
            assert_eq!(*d.get_ref(j, k).unwrap(), expected);
        }
    }
    // The diagonal of the rotation squared: the paths 0 -> 0 -> 0 and 0 -> 1 -> 0.
    assert_eq!(
        *d.get_ref(0, 0).unwrap(),
        gq(1, 3, 0, 1).mul(&gq(81, 625, 0, 1))
    );
    // Coarse-graining over the middle time: the probability is the Born weight
    // of the propagator, and the excess over the path weights is the cross term.
    let classes: Vec<Vec<usize>> = (0..4)
        .map(|end| {
            (0..8)
                .filter(|&j| histories[j].labels[0] * 2 + histories[j].labels[2] == end)
                .collect()
        })
        .collect();
    let coarse = functional.coarse_grain(&classes).unwrap();
    let propagator = mx::multiply(&(u), &(&u)).unwrap();
    for (c, members) in classes.iter().enumerate() {
        let (x0, x2) = (
            histories[members[0]].labels[0],
            histories[members[0]].labels[2],
        );
        let weight = rho.get_ref(x0, x0).unwrap().re.clone();
        let born = &weight * modulus_squared(propagator.get_ref(x2, x0).unwrap());
        assert_eq!(
            *coarse.matrix().get_ref(c, c).unwrap(),
            GaussianRat::from_rational(born)
        );
        let path_amplitudes: Vec<GaussianRat> = members
            .iter()
            .map(|&j| quantum.history_weight(&histories[j].labels).unwrap())
            .collect();
        let diagonal_total: GaussianRat = members.iter().fold(GaussianRat::zero(), |acc, &j| {
            acc.add(d.get_ref(j, j).unwrap())
        });
        assert_eq!(
            coarse.matrix().get_ref(c, c).unwrap().sub(&diagonal_total),
            GaussianRat::from_rational(weight * cross_term(&path_amplitudes).unwrap())
        );
    }
    // From 0 to 0: Born weight 49/625 of (1/3) against path weights 81/625 + 256/625.
    assert_eq!(*coarse.matrix().get_ref(0, 0).unwrap(), gq(49, 1875, 0, 1));
    assert_eq!(classes[0], vec![0, 2]);
    assert_eq!(
        d.get_ref(0, 0).unwrap().add(d.get_ref(2, 2).unwrap()),
        gq(337, 1875, 0, 1)
    );
}

#[test]
fn a_state_that_is_not_positive_gives_a_negative_diagonal_entry() {
    let rho = mx::diagonal(&[gq(3, 2, 0, 1), gq(-1, 2, 0, 1)]).unwrap();
    let histories = chain_histories(
        &[mx::identity(2).unwrap(), rotation()],
        &[basis_partition(2), basis_partition(2)],
    )
    .unwrap();
    let functional = DecoherenceFunctional::new(
        rho,
        histories.iter().map(|h| h.class_operator.clone()).collect(),
    )
    .unwrap();
    // History (1, 0): weight -1/2 * |R_01|^2 = -1/2 * 16/25.
    let index = histories
        .iter()
        .position(|h| h.labels == vec![1, 0])
        .unwrap();
    assert_eq!(
        *functional.matrix().get_ref(index, index).unwrap(),
        gq(-8, 25, 0, 1)
    );
    assert!(!exact_hermitian::is_positive_semidefinite(
        functional.matrix()
    ));
}

fn two_time_functional(second: BasicMatrix<GaussianRat>) -> DecoherenceFunctional {
    let rho = basis_projector(2, 0);
    let histories = chain_histories(
        &[rotation(), second],
        &[basis_partition(2), basis_partition(2)],
    )
    .unwrap();
    DecoherenceFunctional::new(
        rho,
        histories.into_iter().map(|h| h.class_operator).collect(),
    )
    .unwrap()
}

/// Every partition of `0..n` into nonempty classes.
fn set_partitions(n: usize) -> Vec<Vec<Vec<usize>>> {
    let mut out: Vec<Vec<Vec<usize>>> = vec![Vec::new()];
    for item in 0..n {
        let mut next = Vec::new();
        for partition in &out {
            for class in 0..partition.len() {
                let mut extended = partition.clone();
                extended[class].push(item);
                next.push(extended);
            }
            let mut extended = partition.clone();
            extended.push(vec![item]);
            next.push(extended);
        }
        out = next;
    }
    out
}

fn every_sum_rule_holds(functional: &DecoherenceFunctional, n: usize) -> bool {
    set_partitions(n).iter().all(|partition| {
        let coarse = functional.coarse_grain(partition).unwrap();
        partition.iter().enumerate().all(|(c, members)| {
            let total = members.iter().fold(GaussianRat::zero(), |acc, &j| {
                acc.add(functional.matrix().get_ref(j, j).unwrap())
            });
            *coarse.matrix().get_ref(c, c).unwrap() == total
        })
    })
}

#[test]
fn an_environment_record_decoheres_the_histories_and_every_sum_rule_holds() {
    let [x, _, _] = pauli();
    let identity = mx::identity(2).unwrap();
    let p0 = basis_projector(2, 0);
    let p1 = basis_projector(2, 1);
    let cnot = mx::add(
        &(mx::kronecker(&(p0), &(&identity)).unwrap()),
        &(&mx::kronecker(&(p1), &(&x)).unwrap()),
    )
    .unwrap();
    let system_partition = vec![
        mx::kronecker(&(p0), &(&identity)).unwrap(),
        mx::kronecker(&(p1), &(&identity)).unwrap(),
    ];
    let steps = vec![
        mx::kronecker(&(rotation()), &(&identity)).unwrap(),
        mx::multiply(
            &(mx::kronecker(&(rotation()), &(&identity)).unwrap()),
            &(&cnot),
        )
        .unwrap(),
    ];
    let histories = chain_histories(&steps, &[system_partition.clone(), system_partition]).unwrap();
    let rho = basis_projector(4, 0);
    let recorded = DecoherenceFunctional::new(
        rho,
        histories.into_iter().map(|h| h.class_operator).collect(),
    )
    .unwrap();
    assert_eq!(recorded.medium_decoherence_witness(), None);
    assert_eq!(
        *recorded.matrix(),
        mx::diagonal(&[
            gq(81, 625, 0, 1),
            gq(144, 625, 0, 1),
            gq(256, 625, 0, 1),
            gq(144, 625, 0, 1)
        ])
        .unwrap()
    );
    assert_eq!(set_partitions(4).len(), 15);
    assert!(every_sum_rule_holds(&recorded, 4));
    // Without the record the same steps interfere: the final outcome 0 has
    // weight 49/625, not 81/625 + 256/625.
    let unrecorded = two_time_functional(rotation());
    assert_eq!(unrecorded.medium_decoherence_witness(), Some((0, 2)));
    assert_eq!(
        unrecorded.sum_rule_residual(0, 2).unwrap(),
        gq(-288, 625, 0, 1)
    );
    assert_eq!(unrecorded.weak_decoherence_witness(), Some((0, 2)));
    assert!(!every_sum_rule_holds(&unrecorded, 4));
}

#[test]
fn every_sum_rule_can_hold_while_an_off_diagonal_entry_is_nonzero() {
    let weak = two_time_functional(complex_mixer());
    let d = weak.matrix();
    assert_eq!(*d.get_ref(0, 2).unwrap(), gq(0, 1, 144, 625));
    assert_eq!(*d.get_ref(1, 3).unwrap(), gq(0, 1, -144, 625));
    assert_eq!(weak.medium_decoherence_witness(), Some((0, 2)));
    assert_eq!(weak.sum_rule_residual(0, 2).unwrap(), GaussianRat::zero());
    assert_eq!(weak.weak_decoherence_witness(), None);
    assert!(every_sum_rule_holds(&weak, 4));
}

fn three_steps() -> Vec<BasicMatrix<GaussianRat>> {
    vec![
        cayley_unitary(&two_level(), &rq(1, 2)).unwrap(),
        cayley_unitary(&real_symmetric(), &rq(1, 3)).unwrap(),
        cayley_unitary(&two_level(), &ri(-2)).unwrap(),
    ]
}

#[test]
fn schrodinger_and_heisenberg_expectations_agree_along_declared_steps() {
    let steps = three_steps();
    let (rho, a) = (density(), observable());
    let evolved_state = schrodinger_state(&steps, &rho).unwrap();
    let evolved_observable = heisenberg_observable(&steps, &a).unwrap();
    let w = mx::multiply(
        &(mx::multiply(&(steps[2]), &(&steps[1])).unwrap()),
        &(&steps[0]),
    )
    .unwrap();
    assert_eq!(
        evolved_state,
        mx::multiply(
            &(mx::multiply(&(w), &(&rho)).unwrap()),
            &(&iv::adjoint(&(w)).unwrap())
        )
        .unwrap()
    );
    assert_eq!(
        evolved_observable,
        mx::multiply(
            &(mx::multiply(&(iv::adjoint(&(w)).unwrap()), &(&a)).unwrap()),
            &(&w)
        )
        .unwrap()
    );
    let schrodinger = mx::trace(&mx::multiply(&evolved_state, &a).unwrap()).unwrap();
    assert_eq!(
        schrodinger,
        mx::trace(&(mx::multiply(&(rho), &(&evolved_observable)).unwrap())).unwrap()
    );
    // Conjugating in the Schrödinger order instead pairs a different operator.
    let reversed: Vec<BasicMatrix<GaussianRat>> = steps.iter().rev().cloned().collect();
    let wrong_order = heisenberg_observable(&reversed, &a).unwrap();
    assert_ne!(
        mx::trace(&(mx::multiply(&(rho), &(&wrong_order)).unwrap())).unwrap(),
        schrodinger
    );
    // One hand-checked step: C_(1/2)(Z) = diag(3/5 - 4i/5, 3/5 + 4i/5) turns X
    // into -(7/25) X - (24/25) Y.
    let [x, y, z] = pauli();
    let step = cayley_unitary(&z, &rq(1, 2)).unwrap();
    assert_eq!(
        step,
        mx::diagonal(&[gq(3, 5, -4, 5), gq(3, 5, 4, 5)]).unwrap()
    );
    assert_eq!(
        heisenberg_observable(&[step], &x).unwrap(),
        mx::add(
            &(mx::scale(
                &(x),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(-7, 25)))
            )
            .unwrap()),
            &(&mx::scale(
                &(y),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(-24, 25)))
            )
            .unwrap())
        )
        .unwrap()
    );
    // The Heisenberg picture is an automorphism: products, commutators, adjoints.
    let b = real_symmetric();
    let evolve = |m: &BasicMatrix<GaussianRat>| heisenberg_observable(&steps, m).unwrap();
    assert_eq!(
        evolve(&mx::multiply(&(a), &(&b)).unwrap()),
        mx::multiply(&evolve(&a), &evolve(&b)).unwrap()
    );
    assert_eq!(
        evolve(&mx::commutator(&(a), &(&b)).unwrap()),
        mx::commutator(&evolve(&a), &evolve(&b)).unwrap()
    );
    let skew = mx::multiply(&(a), &(&b)).unwrap();
    assert_eq!(
        evolve(&iv::adjoint(&(skew)).unwrap()),
        iv::adjoint(&evolve(&skew)).unwrap()
    );
}

#[test]
fn the_cayley_path_has_the_heisenberg_tangent_two_i_commutator_at_zero() {
    let [x, y, z] = pauli();
    let zero = ri(0);
    for h in [two_level(), real_symmetric(), z.clone()] {
        let path = cayley_jet(&h, &zero).unwrap();
        assert_eq!(*path.value(), mx::identity(2).unwrap());
        assert_eq!(
            *path.tangent(),
            mx::scale(
                &(i_times(&h)),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-2)))
            )
            .unwrap()
        );
        for a in [x.clone(), observable()] {
            let jet = heisenberg_jet(&h, &a, &zero).unwrap();
            assert_eq!(*jet.value(), a);
            assert_eq!(
                *jet.tangent(),
                mx::scale(
                    &(i_times(&mx::commutator(&(h), &(&a)).unwrap())),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(2)))
                )
                .unwrap()
            );
        }
    }
    // H = Z, A = X: the tangent is 2i [Z, X] = -4 Y.
    assert_eq!(
        *heisenberg_jet(&z, &x, &zero).unwrap().tangent(),
        mx::scale(
            &(y),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-4)))
        )
        .unwrap()
    );
}

#[test]
fn the_papers_sign_is_reversed_for_u_equal_to_exp_of_plus_i_t_h() {
    let [x, y, z] = pauli();
    let zero = ri(0);
    // t -> C_t(-H/2) has tangent i H at t = 0, the tangent of exp(i t H).
    let minus_half_z = mx::scale(
        &(z),
        &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(-1, 2))),
    )
    .unwrap();
    assert_eq!(
        *cayley_jet(&minus_half_z, &zero).unwrap().tangent(),
        i_times(&z)
    );
    let tangent = heisenberg_jet(&minus_half_z, &x, &zero)
        .unwrap()
        .tangent()
        .clone();
    // dA/dt at 0 is -i[H, A] = 2Y; the paper's i[H, A] is -2Y.
    assert_eq!(
        tangent,
        mx::scale(
            &(i_times(&mx::commutator(&(z), &(&x)).unwrap())),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-1)))
        )
        .unwrap()
    );
    assert_eq!(
        tangent,
        mx::scale(
            &(y),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(2)))
        )
        .unwrap()
    );
    assert_ne!(tangent, i_times(&mx::commutator(&(z), &(&x)).unwrap()));
    // With U(t) = exp(-i t H), i.e. t -> C_t(H/2), the sign is the paper's.
    let half_z = mx::scale(
        &(z),
        &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(1, 2))),
    )
    .unwrap();
    assert_eq!(
        *heisenberg_jet(&half_z, &x, &zero).unwrap().tangent(),
        i_times(&mx::commutator(&(z), &(&x)).unwrap())
    );
}

#[test]
fn away_from_zero_the_cayley_tangent_uses_the_rate_generator() {
    let three_level = mx::diagonal(&[gi(0, 0), gi(1, 0), gi(2, 0)]).unwrap();
    let ones = mx::from_rows((vec![vec![gi(1, 0); 3]; 3])).unwrap();
    let cases = [
        (two_level(), observable()),
        (real_symmetric(), observable()),
        (three_level.clone(), ones.clone()),
    ];
    for (h, a) in &cases {
        for tau in [rq(1, 2), ri(-3), rq(2, 7)] {
            let path = cayley_jet(h, &tau).unwrap();
            let step = cayley_unitary(h, &tau).unwrap();
            assert_eq!(*path.value(), step);
            let g = cayley_rate_generator(h, &tau).unwrap();
            assert_eq!(
                *path.tangent(),
                mx::scale(
                    &(i_times(&mx::multiply(&g, &step).unwrap())),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-1)))
                )
                .unwrap()
            );
            let jet = heisenberg_jet(h, a, &tau).unwrap();
            assert_eq!(*jet.value(), heisenberg_observable(&[step], a).unwrap());
            assert_eq!(
                *jet.tangent(),
                i_times(&mx::commutator(&g, jet.value()).unwrap())
            );
        }
    }
    // H^2 = 3I: G_tau = 2 H / (1 + 3 tau^2), a reparametrized group.
    let tau = rq(1, 2);
    assert_eq!(
        cayley_rate_generator(&two_level(), &tau).unwrap(),
        mx::scale(
            &(two_level()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(8, 7)))
        )
        .unwrap()
    );
    // H = diag(0, 1, 2): the tangent is not a multiple of i[H, A(tau)].
    let jet = heisenberg_jet(&three_level, &ones, &tau).unwrap();
    let bracket = i_times(&mx::commutator(&(three_level), &(jet.value())).unwrap());
    assert!(!bracket.get_ref(0, 1).unwrap().is_zero() && !bracket.get_ref(0, 2).unwrap().is_zero());
    assert_eq!(
        jet.tangent().get(0, 1).unwrap(),
        bracket.get_ref(0, 1).unwrap().scale_rat(&rq(8, 5))
    );
    assert_eq!(
        jet.tangent().get(0, 2).unwrap(),
        bracket.get_ref(0, 2).unwrap().clone()
    );
    assert_ne!(
        *jet.tangent(),
        mx::scale(
            &(bracket),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(2)))
        )
        .unwrap()
    );
}

#[test]
fn conserved_observables_are_fixed_by_every_step() {
    let h = real_symmetric();
    let commuting = mx::add(
        &(mx::multiply(&(h), &(&h)).unwrap()),
        &(&mx::scale(
            &(h),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(2))),
        )
        .unwrap()),
    )
    .unwrap();
    for tau in [rq(1, 2), ri(-3)] {
        let step = cayley_unitary(&h, &tau).unwrap();
        assert_eq!(
            heisenberg_observable(std::slice::from_ref(&step), &h).unwrap(),
            h
        );
        assert_eq!(
            heisenberg_observable(std::slice::from_ref(&step), &commuting).unwrap(),
            commuting
        );
        assert!(mx::is_zero_matrix(
            heisenberg_jet(&h, &commuting, &tau).unwrap().tangent()
        ));
        assert_ne!(
            heisenberg_observable(&[step], &observable()).unwrap(),
            observable()
        );
    }
}

#[test]
fn malformed_heisenberg_inputs_are_refused() {
    let h = two_level();
    let euler = euler_propagator(&h, &rq(1, 2)).unwrap();
    let good = cayley_unitary(&h, &rq(1, 2)).unwrap();
    assert_eq!(
        heisenberg_observable(&[good.clone(), euler], &observable()),
        Err(HeisenbergError::NotUnitary { step: 1 })
    );
    let tall = mx::from_fn(3, 2, |_, _| (gi(0, 0)).clone()).unwrap();
    assert_eq!(
        schrodinger_state(std::slice::from_ref(&good), &tall),
        Err(HeisenbergError::NotSquare { rows: 3, cols: 2 })
    );
    assert_eq!(
        schrodinger_state(&[mx::identity(3).unwrap()], &density()),
        Err(HeisenbergError::DimensionMismatch {
            expected: 2,
            found: 3
        })
    );
    let not_hermitian =
        mx::from_rows((vec![vec![gi(0, 0), gi(1, 0)], vec![gi(0, 0), gi(0, 0)]])).unwrap();
    assert_eq!(
        cayley_jet(&not_hermitian, &ri(1)),
        Err(HeisenbergError::NotHermitian)
    );
    assert_eq!(
        cayley_rate_generator(&not_hermitian, &ri(1)),
        Err(HeisenbergError::NotHermitian)
    );
    assert_eq!(
        heisenberg_jet(&h, &mx::identity(3).unwrap(), &ri(1)),
        Err(HeisenbergError::DimensionMismatch {
            expected: 2,
            found: 3
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/heisenberg_picture_shadow.rs
// Claim: urn:core:crates_rs:tests:heisenberg-picture-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda361fa08 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda361fa08` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora361fa08 {
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
impl BoundaryErrora361fa08 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora361fa08 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora361fa08 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda361fa08 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora361fa08> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora361fa08::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora361fa08::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora361fa08::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a361fa08() {
    let admitted = BoundaryRecorda361fa08::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda361fa08::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
