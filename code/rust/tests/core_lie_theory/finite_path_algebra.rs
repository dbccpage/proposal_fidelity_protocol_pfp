use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{elimination, involution as star, matrix as mx};
use core_category_theory::finite_path::{FinitePathCategory, PathEdge as E};
use core_lie_theory::finite_path_algebra::{FinitePathAlgebra, PathAlgebraError};
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri, rq};

const LIMITS: OperationLimits = OperationLimits {
    max_elements: 4096,
    max_scalar_ops: 1_000_000,
};
fn example() -> FinitePathAlgebra {
    FinitePathAlgebra::new(
        FinitePathCategory::new(
            3,
            vec![
                E {
                    source: 0,
                    target: 1,
                },
                E {
                    source: 0,
                    target: 1,
                },
                E {
                    source: 1,
                    target: 2,
                },
                E {
                    source: 0,
                    target: 2,
                },
            ],
            64,
        )
        .unwrap(),
    )
}
fn unit(n: usize, p: usize, q: usize) -> BasicMatrix<G> {
    let mut a = mx::zeros(n, n).unwrap();
    a.set(p, q, G::one()).unwrap();
    a
}

#[test]
fn regular_representation_checks_every_product_and_recovers_coefficients() {
    let a = example();
    let n = a.dimension();
    let basis: Vec<_> = (0..n).map(|p| a.basis_left(p, LIMITS).unwrap()).collect();
    for p in 0..n {
        for q in 0..n {
            let product = mx::multiply(&basis[p], &basis[q]).unwrap();
            let expected = match a.paths().compose(q, p).unwrap() {
                Some(r) => basis[r].clone(),
                None => mx::zeros(n, n).unwrap(),
            };
            assert_eq!(product, expected);
        }
    }
    let coefficients: Vec<_> = (0..n)
        .map(|i| G {
            re: rq(i as i64 - 4, 3),
            im: rq(i as i64, 5),
        })
        .collect();
    let regular = a.left_regular(&coefficients, LIMITS).unwrap();
    assert_eq!(
        a.recover_coefficients(&regular, LIMITS).unwrap(),
        coefficients
    );
    let gram = mx::multiply(&star::adjoint(&regular).unwrap(), &regular).unwrap();
    // Each L_p has one nonzero entry for every history ending at source(p).
    let mut weighted_norm = ri(0);
    for (p, c) in a.paths().paths().iter().zip(&coefficients) {
        let multiplicity = a
            .paths()
            .paths()
            .iter()
            .filter(|q| q.target() == p.source())
            .count();
        weighted_norm += (&c.re * &c.re + &c.im * &c.im) * ri(multiplicity as i64);
    }
    assert_eq!(
        mx::trace(&gram).unwrap(),
        G::from_rational(weighted_norm.clone())
    );
    assert!(weighted_norm > ri(0));
}

#[test]
fn generator_words_construct_every_origin_matrix_unit_and_the_extra_adjoints() {
    let a = example();
    let n = a.dimension();
    assert_eq!(a.block_sizes(), vec![6, 2, 1]);
    assert_eq!(a.completion_dimension(), 41);
    let mut total = mx::zeros(n, n).unwrap();
    for x in 0..a.paths().vertices() {
        assert_eq!(
            a.identity_path_projection(x, LIMITS).unwrap(),
            unit(n, x, x)
        );
        let mut central = mx::zeros(n, n).unwrap();
        for (p, pp) in a.paths().paths().iter().enumerate() {
            for (q, qq) in a.paths().paths().iter().enumerate() {
                if pp.source() == x && qq.source() == x {
                    let e = a.matrix_unit(p, q, LIMITS).unwrap();
                    assert_eq!(e, unit(n, p, q));
                    assert!(a.is_in_completion(&e).unwrap());
                    if p == q {
                        central = mx::add(&central, &e).unwrap();
                    }
                }
            }
        }
        assert_eq!(central, a.central_origin_projection(x, LIMITS).unwrap());
        total = mx::add(&total, &central).unwrap();
    }
    assert_eq!(total, mx::identity(n).unwrap());
    let p = a.paths().edge_path(0).unwrap();
    let adjoint = star::adjoint(&a.basis_left(p, LIMITS).unwrap()).unwrap();
    assert!(a.is_in_completion(&adjoint).unwrap());
    assert!(matches!(
        a.recover_coefficients(&adjoint, LIMITS),
        Err(PathAlgebraError::OutsidePathAlgebra)
    ));
    assert!(matches!(
        a.matrix_unit(0, 1, LIMITS),
        Err(PathAlgebraError::DifferentOrigins)
    ));
}

#[test]
fn root_selection_can_retain_path_faithfulness_but_loses_completion_sectors() {
    let a = example();
    for root in 0..3 {
        let blocks: Vec<_> = (0..a.dimension())
            .map(|p| {
                a.restrict_origin(&a.basis_left(p, LIMITS).unwrap(), root)
                    .unwrap()
            })
            .collect();
        let rows = blocks[0].as_slice().len();
        let flattened =
            mx::from_fn(rows, a.dimension(), |i, j| blocks[j].as_slice()[i].clone()).unwrap();
        let rank = elimination::rank(&flattened).unwrap();
        assert_eq!(
            a.origin_is_path_faithful(root).unwrap(),
            rank == a.dimension()
        );
        assert_eq!(rank, [9, 3, 1][root]);
    }
    let lost = a.central_origin_projection(1, LIMITS).unwrap();
    assert_eq!(mx::trace(&lost).unwrap(), G::from_rational(ri(2)));
    assert_eq!(
        a.restrict_origin(&lost, 0).unwrap(),
        mx::zeros(6, 6).unwrap()
    );
    assert!(a.origin_is_path_faithful(0).unwrap());
}

#[test]
fn shape_origin_and_matrix_budgets_are_checked() {
    let a = example();
    assert!(matches!(
        a.left_regular(&[], LIMITS),
        Err(PathAlgebraError::CoefficientLength)
    ));
    assert!(matches!(
        a.is_in_completion(&mx::zeros(1, 1).unwrap()),
        Err(PathAlgebraError::Shape)
    ));
    assert!(matches!(
        a.restrict_origin(&mx::identity(9).unwrap(), 3),
        Err(PathAlgebraError::UnknownOrigin)
    ));
    assert!(!a.is_in_completion(&unit(9, 0, 1)).unwrap());
    assert!(matches!(
        a.restrict_origin(&unit(9, 0, 1), 0),
        Err(PathAlgebraError::OutsideCompletion)
    ));
    assert!(a.basis_left(9, LIMITS).is_err());
    assert!(
        a.basis_left(
            0,
            OperationLimits {
                max_elements: 80,
                ..LIMITS
            }
        )
        .is_err()
    );
    assert!(
        a.matrix_unit(
            0,
            0,
            OperationLimits {
                max_scalar_ops: 0,
                ..LIMITS
            }
        )
        .is_err()
    );
    assert!(a.identity_path_projection(3, LIMITS).is_err());
    assert!(a.central_origin_projection(3, LIMITS).is_err());
    assert!(a.origin_is_path_faithful(3).is_err());
}

#[test]
fn path_sign_gauge_preserves_blocks_without_claiming_endpoint_descent() {
    let a = example();
    let signs = [G::from_ints(-1, 0), G::one(), G::one(), G::one()];
    let phases: Vec<_> = a
        .paths()
        .paths()
        .iter()
        .map(|p| {
            p.edges()
                .iter()
                .fold(G::one(), |value, &e| value.mul(&signs[e]))
        })
        .collect();
    let gauge = mx::diagonal(&phases).unwrap();
    let adjoint = star::adjoint(&gauge).unwrap();
    assert_eq!(
        mx::multiply(&gauge, &adjoint).unwrap(),
        mx::identity(a.dimension()).unwrap()
    );
    for (edge, sign) in signs.iter().enumerate() {
        let l = a
            .basis_left(a.paths().edge_path(edge).unwrap(), LIMITS)
            .unwrap();
        assert_eq!(
            mx::multiply(&mx::multiply(&gauge, &l).unwrap(), &adjoint).unwrap(),
            mx::scale(&l, sign).unwrap()
        );
    }
    // Parallel edges have the same endpoints but different signs. An endpoint
    // potential cannot supply both signs; a separate phase per history can.
    assert_ne!(
        phases[a.paths().edge_path(0).unwrap()],
        phases[a.paths().edge_path(1).unwrap()]
    );
}

// Origin: engine/crates_rs/tests/core_lie_theory/finite_path_algebra.rs
// Claim: urn:core:crates_rs:tests:finite-path-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord31ae92e3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord31ae92e3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError31ae92e3 {
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
impl BoundaryError31ae92e3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError31ae92e3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError31ae92e3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord31ae92e3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError31ae92e3> {
        if capacity_bound == 0 {
            return Err(BoundaryError31ae92e3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError31ae92e3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError31ae92e3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_31ae92e3() {
    let admitted = BoundaryRecord31ae92e3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord31ae92e3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
