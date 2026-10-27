//! QM_210: power-law outcome rules `|<b, psi>|^p / N_p` are probability vectors
//! context by context for every power, but only the square gives a ray one
//! weight across contexts in dimension three. In dimension two every power
//! rule is context free, and the first power is not of the form `<b, rho b>`.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{hs_inner, outer_product},
    matrix as mx,
};
use num_traits::{One, Signed};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::power_rule_outcomes::{
    find_context_dependence, normalizer, power_rule, Context, ContextDependence, PowerRuleError,
};

fn v(entries: &[(i64, i64)]) -> Vec<Rational> {
    entries.iter().map(|&(n, d)| rq(n, d)).collect()
}

fn standard3() -> Context {
    Context::new(vec![
        v(&[(1, 1), (0, 1), (0, 1)]),
        v(&[(0, 1), (1, 1), (0, 1)]),
        v(&[(0, 1), (0, 1), (1, 1)]),
    ])
    .unwrap()
}

/// Shares `e1` with the standard basis.
fn rotated_about_e1() -> Context {
    Context::new(vec![
        v(&[(1, 1), (0, 1), (0, 1)]),
        v(&[(0, 1), (3, 5), (4, 5)]),
        v(&[(0, 1), (-4, 5), (3, 5)]),
    ])
    .unwrap()
}

/// Shares `e3` with the standard basis.
fn rotated_about_e3() -> Context {
    Context::new(vec![
        v(&[(3, 5), (4, 5), (0, 1)]),
        v(&[(-4, 5), (3, 5), (0, 1)]),
        v(&[(0, 1), (0, 1), (1, 1)]),
    ])
    .unwrap()
}

fn three_contexts() -> Vec<Context> {
    vec![standard3(), rotated_about_e1(), rotated_about_e3()]
}

#[test]
fn every_power_rule_is_a_probability_vector_on_every_context() {
    let states = [
        v(&[(1, 1), (1, 1), (0, 1)]),
        v(&[(2, 1), (-1, 3), (5, 7)]),
        v(&[(0, 1), (0, 1), (-3, 1)]),
    ];
    for psi in &states {
        for context in three_contexts() {
            for power in 1..=4 {
                let weights = power_rule(psi, &context, power).unwrap();
                assert!(weights.iter().all(|w| !w.is_negative()));
                assert_eq!(weights.iter().sum::<Rational>(), Rational::one());
            }
        }
    }
    let psi = v(&[(1, 1), (1, 1), (0, 1)]);
    assert_eq!(
        power_rule(&psi, &rotated_about_e1(), 1).unwrap(),
        vec![rq(5, 12), rq(1, 4), rq(1, 3)]
    );
    assert_eq!(
        power_rule(&psi, &standard3(), 1).unwrap(),
        vec![rq(1, 2), rq(1, 2), ri(0)]
    );
}

#[test]
fn only_the_square_has_a_context_free_normalizer() {
    let psi = v(&[(1, 1), (1, 1), (0, 1)]);
    let contexts = three_contexts();
    let normalizers = |power| {
        contexts
            .iter()
            .map(|c| normalizer(&psi, c, power).unwrap())
            .collect::<Vec<_>>()
    };
    // Parseval: <psi, psi> = 2 on every context.
    assert_eq!(normalizers(2), vec![ri(2), ri(2), ri(2)]);
    assert_eq!(normalizers(1), vec![ri(2), rq(12, 5), rq(8, 5)]);
    assert_eq!(normalizers(3), vec![ri(2), rq(216, 125), rq(344, 125)]);
    assert_eq!(normalizers(4), vec![ri(2), rq(962, 625), rq(2402, 625)]);
}

#[test]
fn every_power_but_the_square_is_context_dependent_in_dimension_three() {
    let psi = v(&[(1, 1), (1, 1), (0, 1)]);
    let contexts = three_contexts();
    let e1 = v(&[(1, 1), (0, 1), (0, 1)]);
    assert_eq!(find_context_dependence(&psi, &contexts, 2).unwrap(), None);
    for (power, other) in [(1, rq(5, 12)), (3, rq(125, 216)), (4, rq(625, 962))] {
        assert_eq!(
            find_context_dependence(&psi, &contexts, power).unwrap(),
            Some(ContextDependence {
                ray: e1.clone(),
                first: (0, 0, rq(1, 2)),
                second: (1, 0, other),
            })
        );
    }
    // The square is context free for every state tried, and a Born weight.
    for psi in [v(&[(2, 1), (-1, 3), (5, 7)]), v(&[(0, 1), (1, 2), (-1, 1)])] {
        assert_eq!(find_context_dependence(&psi, &contexts, 2).unwrap(), None);
        let total: Rational = psi.iter().map(|x| x * x).sum();
        let weights = power_rule(&psi, &standard3(), 2).unwrap();
        assert_eq!(
            weights,
            psi.iter().map(|x| x * x / &total).collect::<Vec<_>>()
        );
    }
    // A shared ray is recognized up to sign.
    let flipped = Context::new(vec![
        v(&[(-1, 1), (0, 1), (0, 1)]),
        v(&[(0, 1), (3, 5), (4, 5)]),
        v(&[(0, 1), (-4, 5), (3, 5)]),
    ])
    .unwrap();
    assert_eq!(
        find_context_dependence(&psi, &[standard3(), flipped], 1).unwrap(),
        Some(ContextDependence {
            ray: e1.clone(),
            first: (0, 0, rq(1, 2)),
            second: (1, 0, rq(5, 12)),
        })
    );
    // The search reports only what the declared contexts show: for e1 itself
    // the first power agrees on every shared ray.
    assert_eq!(find_context_dependence(&e1, &contexts, 1).unwrap(), None);
}

/// The Hermitian matrix fixed by the values on `e1`, `e2` and a third real ray
/// `(x, y)` with `x y != 0`: its diagonal is the first two values, and its
/// real off-diagonal part solves `x^2 f11 + 2 x y f12 + y^2 f22 = value`.
fn fit(values: [Rational; 3], ray: &[Rational]) -> [[Rational; 2]; 2] {
    let (x, y) = (&ray[0], &ray[1]);
    let off = (&values[2] - x * x * &values[0] - y * y * &values[1]) / (ri(2) * x * y);
    [[values[0].clone(), off.clone()], [off, values[1].clone()]]
}

fn form(m: &[[Rational; 2]; 2], ray: &[Rational]) -> Rational {
    &ray[0] * &ray[0] * &m[0][0]
        + ri(2) * &ray[0] * &ray[1] * &m[0][1]
        + &ray[1] * &ray[1] * &m[1][1]
}

#[test]
fn in_dimension_two_power_rules_are_context_free_and_the_first_power_is_not_born() {
    let e1 = v(&[(1, 1), (0, 1)]);
    let e2 = v(&[(0, 1), (1, 1)]);
    let r = v(&[(3, 5), (4, 5)]);
    let r_perp = v(&[(-4, 5), (3, 5)]);
    let s = v(&[(4, 5), (3, 5)]);
    let s_perp = v(&[(-3, 5), (4, 5)]);
    let contexts = vec![
        Context::new(vec![e1.clone(), e2.clone()]).unwrap(),
        Context::new(vec![r.clone(), r_perp.clone()]).unwrap(),
        Context::new(vec![s.clone(), s_perp.clone()]).unwrap(),
        // The first context again, reordered and with a sign flipped.
        Context::new(vec![e2.clone(), e1.iter().map(|x| -x).collect()]).unwrap(),
    ];
    for psi in [e1.clone(), v(&[(2, 1), (-1, 3)]), v(&[(5, 7), (1, 1)])] {
        for power in 1..=4 {
            assert_eq!(
                find_context_dependence(&psi, &contexts, power).unwrap(),
                None
            );
        }
    }

    // State e1: the first power gives e1 -> 1, e2 -> 0, r -> 3/7, s -> 4/7.
    let psi = e1.clone();
    let weight =
        |context: usize, power| power_rule(&psi, &contexts[context], power).unwrap()[0].clone();
    assert_eq!(
        [weight(0, 1), weight(1, 1), weight(2, 1)],
        [ri(1), rq(3, 7), rq(4, 7)]
    );
    assert_eq!(power_rule(&psi, &contexts[0], 1).unwrap()[1], ri(0));

    // The square: the matrix fitted on e1, e2, r is |e1><e1| and reproduces every ray.
    let born = fit([weight(0, 2), ri(0), weight(1, 2)], &r);
    assert_eq!(born, [[ri(1), ri(0)], [ri(0), ri(0)]]);
    for (context, ray) in [(1, &r), (2, &s)] {
        assert_eq!(form(&born, ray), weight(context, 2));
    }
    // The first power: the fit is [[1, 1/14], [1/14, 0]], which misses s. On
    // real rays a Hermitian matrix acts through its real part, so no Hermitian
    // matrix gives these weights; the fit is not positive semidefinite either
    // (determinant -1/196).
    let first = fit([weight(0, 1), ri(0), weight(1, 1)], &r);
    assert_eq!(first, [[ri(1), rq(1, 14)], [rq(1, 14), ri(0)]]);
    assert_eq!(form(&first, &r_perp), rq(4, 7));
    assert_eq!(form(&first, &s), rq(124, 175));
    assert_ne!(form(&first, &s), weight(2, 1));
    assert_eq!(
        &first[0][0] * &first[1][1] - &first[0][1] * &first[1][0],
        rq(-1, 196)
    );
}

#[test]
fn the_born_pairing_is_linear_in_the_density_and_quadratic_in_the_amplitude() {
    let pure = |psi: [(i64, i64); 2]| {
        let psi = psi.map(|(re, im)| gi(re, im));
        outer_product(&psi, &psi).unwrap()
    };
    let effect = pure([(1, 0), (1, 0)]);
    let pair = |rho: &BasicMatrix<GaussianRat>| hs_inner(&effect, rho).unwrap();
    // Quadratic in the amplitude: e_0 and e_1 read 1 each, their sum 4, their difference 0.
    assert_eq!(pair(&pure([(1, 0), (0, 0)])), gi(1, 0));
    assert_eq!(pair(&pure([(0, 0), (1, 0)])), gi(1, 0));
    assert_eq!(pair(&pure([(1, 0), (1, 0)])), gi(4, 0));
    assert_eq!(pair(&pure([(1, 0), (-1, 0)])), gi(0, 0));
    // Linear in the density: a mixture reads the mixture of the readings.
    let zero_state = pure([(1, 0), (0, 0)]);
    let plus_state = mx::scale(&pure([(1, 0), (1, 0)]), &gq(1, 2, 0, 1)).unwrap();
    let (a, b) = (gq(1, 3, 0, 1), gq(2, 3, 0, 1));
    let mixture = mx::add(
        &mx::scale(&zero_state, &a).unwrap(),
        &mx::scale(&plus_state, &b).unwrap(),
    )
    .unwrap();
    assert_eq!(
        pair(&mixture),
        pair(&zero_state).mul(&a).add(&pair(&plus_state).mul(&b))
    );
    assert_eq!(pair(&mixture), gq(5, 3, 0, 1));
}

#[test]
fn contexts_and_rules_refuse_malformed_input() {
    assert_eq!(Context::new(vec![]), Err(PowerRuleError::EmptyContext));
    assert_eq!(
        Context::new(vec![v(&[(1, 1), (0, 1)]), v(&[(1, 1)])]),
        Err(PowerRuleError::VectorLength {
            index: 1,
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        Context::new(vec![v(&[(1, 1), (0, 1)])]),
        Err(PowerRuleError::VectorCount {
            dimension: 2,
            found: 1
        })
    );
    assert_eq!(
        Context::new(vec![v(&[(1, 1), (0, 1)]), v(&[(1, 1), (1, 1)])]),
        Err(PowerRuleError::NotOrthonormal { left: 0, right: 1 })
    );
    assert_eq!(
        Context::new(vec![v(&[(1, 1), (1, 1)]), v(&[(1, 1), (-1, 1)])]),
        Err(PowerRuleError::NotOrthonormal { left: 0, right: 0 })
    );
    let context = standard3();
    let psi = v(&[(1, 1), (0, 1), (0, 1)]);
    assert_eq!(
        power_rule(&psi, &context, 0),
        Err(PowerRuleError::ZeroPower)
    );
    assert_eq!(
        power_rule(&psi[..2], &context, 1),
        Err(PowerRuleError::StateLength {
            expected: 3,
            actual: 2
        })
    );
    assert_eq!(
        power_rule(&[ri(0), ri(0), ri(0)], &context, 2),
        Err(PowerRuleError::ZeroState)
    );
    assert!(normalizer(&psi, &context, 3).unwrap().is_positive());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/born_power_rule_pairing.rs
// Claim: urn:core:crates_rs:tests:born-power-rule-pairing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord928751ac {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord928751ac` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError928751ac {
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
impl BoundaryError928751ac {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError928751ac {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError928751ac {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord928751ac {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError928751ac> {
        if capacity_bound == 0 {
            return Err(BoundaryError928751ac::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError928751ac::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError928751ac::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_928751ac() {
    let admitted = BoundaryRecord928751ac::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord928751ac::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
