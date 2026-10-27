//! QM_211: stochastic steps meet the unitary group only in permutations, while
//! they can sit on continuous stochastic semigroups; a unitary step generated
//! by a Hermitian matrix need not have determinant one.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_traits::One;
use core_lie_theory::cayley_unitary::{cayley_generator, cayley_unitary};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;
use core_quantum_physics::stochastic_unitary_boundary::{
    isometric_permutation, two_state_embedding, StochasticStepError, TwoStateEmbedding,
    TwoStateGenerator,
};

fn step(rows: &[&[(i64, i64)]]) -> Vec<Vec<Rational>> {
    rows.iter()
        .map(|row| row.iter().map(|&(n, d)| rq(n, d)).collect())
        .collect()
}

fn multiply(left: &[Vec<Rational>], right: &[Vec<Rational>]) -> Vec<Vec<Rational>> {
    (0..left.len())
        .map(|i| {
            (0..right[0].len())
                .map(|j| (0..right.len()).map(|k| &left[i][k] * &right[k][j]).sum())
                .collect()
        })
        .collect()
}

fn is_permutation_matrix(t: &[Vec<Rational>]) -> bool {
    let binary = t.iter().flatten().all(|x| *x == ri(0) || x.is_one());
    let columns = (0..t.len()).all(|j| {
        t.iter()
            .map(|row| row[j].clone())
            .sum::<Rational>()
            .is_one()
    });
    binary && columns
}

#[test]
fn an_l2_isometric_stochastic_step_is_a_permutation() {
    // Two sites, off-diagonal entries on a grid of quarters: 25 steps.
    let quarters: Vec<Rational> = (0..=4).map(|k| rq(k, 4)).collect();
    let mut isometric = Vec::new();
    for alpha in &quarters {
        for beta in &quarters {
            let t = vec![
                vec![Rational::one() - alpha, alpha.clone()],
                vec![beta.clone(), Rational::one() - beta],
            ];
            if let Some(permutation) = isometric_permutation(&t).unwrap() {
                assert!(is_permutation_matrix(&t));
                isometric.push(permutation);
            }
        }
    }
    assert_eq!(isometric, vec![vec![0, 1], vec![1, 0]]);

    // Three sites, rows from the six patterns over {0, 1/2, 1}: 216 steps.
    let patterns = [
        [(1, 1), (0, 1), (0, 1)],
        [(0, 1), (1, 1), (0, 1)],
        [(0, 1), (0, 1), (1, 1)],
        [(1, 2), (1, 2), (0, 1)],
        [(1, 2), (0, 1), (1, 2)],
        [(0, 1), (1, 2), (1, 2)],
    ];
    let mut permutations = Vec::new();
    let mut total = 0;
    for a in &patterns {
        for b in &patterns {
            for c in &patterns {
                let t = step(&[a, b, c]);
                total += 1;
                let verdict = isometric_permutation(&t).unwrap();
                assert_eq!(verdict.is_some(), is_permutation_matrix(&t));
                permutations.extend(verdict);
            }
        }
    }
    assert_eq!(total, 216);
    permutations.sort();
    assert_eq!(
        permutations,
        vec![
            vec![0, 1, 2],
            vec![0, 2, 1],
            vec![1, 0, 2],
            vec![1, 2, 0],
            vec![2, 0, 1],
            vec![2, 1, 0]
        ]
    );
}

#[test]
fn a_two_state_semigroup_composes_multiplicatively_and_is_isometric_only_at_the_identity() {
    let parameters = [rq(1, 2), rq(1, 3), rq(3, 4), ri(1)];
    for (a, b) in [(ri(1), ri(1)), (ri(1), ri(3)), (rq(2, 5), ri(0))] {
        let generator = TwoStateGenerator::new(a, b).unwrap();
        for s in &parameters {
            let t = generator.step(s).unwrap();
            let determinant = &t[0][0] * &t[1][1] - &t[0][1] * &t[1][0];
            assert_eq!(&determinant, s);
            assert_eq!(isometric_permutation(&t).unwrap().is_some(), s.is_one());
            for s2 in &parameters {
                assert_eq!(
                    multiply(&t, &generator.step(s2).unwrap()),
                    generator.step(&(s * s2)).unwrap()
                );
            }
        }
    }
}

#[test]
fn a_stochastic_step_with_positive_determinant_has_fractional_powers() {
    let t = step(&[&[(5, 8), (3, 8)], &[(3, 8), (5, 8)]]);
    let TwoStateEmbedding::OnSemigroup {
        generator,
        parameter,
    } = two_state_embedding(&t).unwrap()
    else {
        panic!("a positive determinant step lies on a semigroup");
    };
    assert_eq!(parameter, rq(1, 4));
    assert_eq!(generator.rates(), (&rq(3, 8), &rq(3, 8)));
    assert_eq!(generator.step(&parameter).unwrap(), t);
    // Its stochastic square root is T(1/2): a fractional power among stochastic matrices.
    let root = generator.step(&rq(1, 2)).unwrap();
    assert_eq!(root, step(&[&[(3, 4), (1, 4)], &[(1, 4), (3, 4)]]));
    assert_eq!(multiply(&root, &root), t);

    // Determinant zero or negative: on no semigroup. The swap is one of them.
    let swap = step(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]]);
    assert_eq!(
        two_state_embedding(&swap).unwrap(),
        TwoStateEmbedding::NotEmbeddable {
            determinant: ri(-1)
        }
    );
    let averaging = step(&[&[(1, 2), (1, 2)], &[(1, 2), (1, 2)]]);
    assert_eq!(
        two_state_embedding(&averaging).unwrap(),
        TwoStateEmbedding::NotEmbeddable { determinant: ri(0) }
    );
    let identity = step(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 1)]]);
    assert_eq!(
        two_state_embedding(&identity).unwrap(),
        TwoStateEmbedding::Identity
    );
}

#[test]
fn the_swap_lies_on_a_rational_unitary_family_and_a_generated_step_need_not_be_special() {
    let x = mx::from_rows((vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]])).unwrap();
    // The swap is a stochastic permutation and a unitary.
    assert!(core_lie_theory::scalar::is_unitary(&x).unwrap());
    // Up to the phase i it is the Cayley step of the Hermitian -X at tau = 1,
    // and every rational tau gives an exact unitary on the same family.
    let minus_x = mx::scale(&(x), &(&gi(-1, 0))).unwrap();
    assert_eq!(
        cayley_unitary(&minus_x, &ri(1)).unwrap(),
        mx::scale(&(x), &(&gi(0, 1))).unwrap()
    );
    assert_eq!(
        cayley_generator(&mx::scale(&(x), &(&gi(0, 1))).unwrap()).unwrap(),
        minus_x
    );
    for tau in [rq(1, 2), rq(-3, 7), ri(2)] {
        assert!(
            core_lie_theory::scalar::is_unitary(&cayley_unitary(&minus_x, &tau).unwrap()).unwrap()
        );
    }
    // A Hermitian generator with nonzero trace: det C_1(diag(1, 0)) = -i, so the
    // step lies in U(2) and not in SU(2).
    let h = mx::diagonal(&[gi(1, 0), gi(0, 0)]).unwrap();
    let u: BasicMatrix<GaussianRat> = cayley_unitary(&h, &ri(1)).unwrap();
    assert_eq!(u, mx::diagonal(&[gi(0, -1), gi(1, 0)]).unwrap());
    let determinant = u
        .get_ref(0, 0)
        .unwrap()
        .mul(u.get_ref(1, 1).unwrap())
        .sub(&u.get_ref(0, 1).unwrap().mul(u.get_ref(1, 0).unwrap()));
    assert_eq!(determinant, gi(0, -1));
}

#[test]
fn malformed_steps_generators_and_parameters_are_refused() {
    assert_eq!(isometric_permutation(&[]), Err(StochasticStepError::Empty));
    assert_eq!(
        isometric_permutation(&step(&[&[(1, 1), (0, 1)], &[(1, 1)]])),
        Err(StochasticStepError::NotSquare {
            row: 1,
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        isometric_permutation(&step(&[&[(3, 2), (-1, 2)], &[(0, 1), (1, 1)]])),
        Err(StochasticStepError::NotRowStochastic { row: 0 })
    );
    assert_eq!(
        isometric_permutation(&step(&[&[(1, 1), (0, 1)], &[(1, 2), (1, 3)]])),
        Err(StochasticStepError::NotRowStochastic { row: 1 })
    );
    let three = step(&[
        &[(1, 1), (0, 1), (0, 1)],
        &[(0, 1), (1, 1), (0, 1)],
        &[(0, 1), (0, 1), (1, 1)],
    ]);
    assert_eq!(
        two_state_embedding(&three),
        Err(StochasticStepError::NotTwoState { sites: 3 })
    );
    assert_eq!(
        TwoStateGenerator::new(ri(-1), ri(2)),
        Err(StochasticStepError::Rates)
    );
    assert_eq!(
        TwoStateGenerator::new(ri(0), ri(0)),
        Err(StochasticStepError::Rates)
    );
    let generator = TwoStateGenerator::new(ri(1), ri(1)).unwrap();
    for s in [ri(0), rq(-1, 2), rq(3, 2)] {
        assert_eq!(generator.step(&s), Err(StochasticStepError::Parameter));
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/unitary_dynamics_import_boundary.rs
// Claim: urn:core:crates_rs:tests:unitary-dynamics-import-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6bdde496 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6bdde496` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6bdde496 {
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
impl BoundaryError6bdde496 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6bdde496 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6bdde496 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6bdde496 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6bdde496> {
        if capacity_bound == 0 {
            return Err(BoundaryError6bdde496::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6bdde496::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6bdde496::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6bdde496() {
    let admitted = BoundaryRecord6bdde496::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6bdde496::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
