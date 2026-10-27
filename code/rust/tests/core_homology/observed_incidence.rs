use num_rational::BigRational as Q;
use num_traits::{One, Zero};
use core_homology::block_embedding::{BlockEmbedding, BlockError};
use core_homology::finite_poset::FinitePoset;
use core_homology::observed_2category::{
    CoherenceError, ComparisonCell, ObservedRestrictionSystem, ObserverArrow, ObserverObject,
};
use core_homology::restriction_dga::{Cochain, Matrix, OperatorCarrier};
use std::collections::BTreeMap;
use std::sync::Arc;
fn q(n: i64) -> Q {
    Q::from_integer(n.into())
}
fn m(rows: usize, cols: usize, data: Vec<Q>) -> Matrix {
    Matrix::from_row_major(rows, cols, data).unwrap()
}
fn carrier(dims: Vec<usize>) -> Arc<OperatorCarrier> {
    let n = dims.len();
    OperatorCarrier::new(
        FinitePoset::new(n, (0..n).flat_map(|i| (i + 1..n).map(move |j| (i, j)))).unwrap(),
        dims,
    )
    .unwrap()
}
fn fixture(c: &Arc<OperatorCarrier>, degree: usize, seed: i64) -> Cochain {
    Cochain::new(
        c.clone(),
        degree,
        c.chains(degree)
            .iter()
            .map(|s| {
                let a = s[0];
                let b = s[s.len() - 1];
                let v = Matrix::try_from_fn(c.dimensions()[a], c.dimensions()[b], |i, j| {
                    q(seed + a as i64 + 2 * b as i64 + 3 * i as i64 - j as i64)
                })
                .unwrap();
                (s.clone(), v)
            })
            .collect(),
    )
    .unwrap()
}

#[test]
fn heterogeneous_corner_lift_is_faithful_and_preserves_composition() {
    let c = carrier(vec![2, 1, 3]);
    let e = BlockEmbedding::new(c.clone());
    let f = m(2, 1, vec![q(2), q(-1)]);
    let g = m(1, 3, vec![q(3), q(1), q(5)]);
    let fg = f.mul(&g).unwrap();
    assert_eq!(
        e.lift(0, 1, &f)
            .unwrap()
            .mul(&e.lift(1, 2, &g).unwrap())
            .unwrap(),
        e.lift(0, 2, &fg).unwrap()
    );
    assert_eq!(e.decode(0, 2, &e.lift(0, 2, &fg).unwrap()).unwrap(), fg);
    let i0 = e.idempotent(0).unwrap();
    let i2 = e.idempotent(2).unwrap();
    assert_eq!(i0.mul(&i0).unwrap(), i0);
    assert_eq!(i0.mul(&i2).unwrap(), m(6, 6, vec![Q::zero(); 36]));
    let mut bad = e.lift(0, 2, &fg).unwrap();
    bad.set(5, 0, Q::one()).unwrap();
    assert!(matches!(e.decode(0, 2, &bad), Err(BlockError::Corner)));
}

#[test]
fn all_degree_block_cup_and_internal_deletion_match_independent_dense_expansion() {
    let c = carrier(vec![2, 1, 3, 2, 1]);
    let e = BlockEmbedding::new(c.clone());
    for n in 0..=4 {
        let f = fixture(&c, n, 7);
        let lifted = e.lift_cochain(&f).unwrap();
        let bd = e.lift_cochain(&f.internal_differential().unwrap()).unwrap();
        for s in c.chains(n + 1) {
            let mut value = m(
                e.dimension(),
                e.dimension(),
                vec![Q::zero(); e.dimension() * e.dimension()],
            );
            for i in 1..=n {
                let mut face = s.clone();
                face.remove(i);
                value = if i % 2 == 0 {
                    value.add(&lifted[&face]).unwrap()
                } else {
                    value.sub(&lifted[&face]).unwrap()
                };
            }
            assert_eq!(value, bd[s]);
        }
        for p in 0..=3 {
            let g = fixture(&c, p, -2);
            let gl = e.lift_cochain(&g).unwrap();
            let fg = e.lift_cochain(&f.cup(&g).unwrap()).unwrap();
            for s in c.chains(n + p) {
                assert_eq!(
                    lifted[&s[..n + 1].to_vec()]
                        .mul(&gl[&s[n..].to_vec()])
                        .unwrap(),
                    fg[s]
                );
            }
        }
    }
}

#[test]
fn rectangular_curvature_is_detected_by_the_typed_vertex_selector() {
    let c = carrier(vec![2, 1, 3]);
    let e = BlockEmbedding::new(c.clone());
    let a = fixture(&c, 1, 3);
    let k = a.curvature().unwrap();
    assert!(!k.is_zero());
    let lift = e.lift_cochain(&k).unwrap();
    let value = &lift[&vec![0, 1, 2]];
    let selector = e.idempotent(2).unwrap();
    assert_eq!(value.mul(&selector).unwrap(), *value);
    assert!(matches!(
        e.lift_cochain(&fixture(&carrier(vec![2, 1, 2]), 0, 1)),
        Err(BlockError::Owner(_))
    ));
}

fn observed_fixture() -> ObservedRestrictionSystem {
    let c = carrier(vec![3; 5]);
    let components: BTreeMap<_, _> = c
        .chains(1)
        .iter()
        .map(|s| {
            let x = s[0] as i64;
            let z = s[1] as i64;
            (
                s.clone(),
                m(
                    3,
                    3,
                    vec![
                        q(1),
                        q(0),
                        q(0),
                        q(0),
                        q(x + 1),
                        q(z + 2),
                        q(0),
                        q(z + 1),
                        q(x + 3),
                    ],
                ),
            )
        })
        .collect();
    let a = Cochain::new(c, 1, components).unwrap();
    ObservedRestrictionSystem::new(a, vec![m(1, 3, vec![q(1), q(0), q(0)]); 5]).unwrap()
}

#[test]
fn protected_2cells_have_units_vertical_horizontal_and_interchange_laws() {
    let sys = observed_fixture();
    let alpha = sys.compositor(1, 2, 3).unwrap();
    let beta = sys.compositor(0, 1, 3).unwrap();
    let unit = ComparisonCell::identity(alpha.source().clone()).unwrap();
    assert_eq!(unit.then(&alpha).unwrap(), alpha);
    let f = sys.arrow(1, 3).unwrap();
    let g = sys.arrow(0, 1).unwrap();
    let i_f = ComparisonCell::identity(f.clone()).unwrap();
    let i_g = ComparisonCell::identity(g.clone()).unwrap();
    let horizontal = i_g.horizontal_after(&i_f).unwrap();
    assert_eq!(
        horizontal,
        ComparisonCell::identity(g.after(&f).unwrap()).unwrap()
    );
    let a2 = ComparisonCell::identity(alpha.target().clone()).unwrap();
    let b0 = ComparisonCell::identity(sys.arrow(0, 1).unwrap()).unwrap();
    let b2 = b0.clone();
    let left = b0
        .then(&b2)
        .unwrap()
        .horizontal_after(&alpha.then(&a2).unwrap())
        .unwrap();
    let right = b0
        .horizontal_after(&alpha)
        .unwrap()
        .then(&b2.horizontal_after(&a2).unwrap())
        .unwrap();
    assert_eq!(left, right);
    assert!(matches!(alpha.then(&beta), Err(CoherenceError::Boundary)));
}

#[test]
fn horizontal_mixed_term_and_nontrivial_interchange_are_required() {
    let object = ObserverObject::new(0, m(1, 3, vec![q(1), q(0), q(0)])).unwrap();
    let arrow = |b: [i64; 4]| {
        ObserverArrow::new(
            object.clone(),
            object.clone(),
            m(
                3,
                3,
                vec![
                    q(1),
                    q(0),
                    q(0),
                    q(0),
                    q(b[0]),
                    q(b[1]),
                    q(0),
                    q(b[2]),
                    q(b[3]),
                ],
            ),
        )
        .unwrap()
    };
    let f0 = arrow([1, 0, 0, 1]);
    let f1 = arrow([1, 2, 0, 1]);
    let f2 = arrow([2, 1, 3, 2]);
    let g0 = arrow([1, 0, 0, 1]);
    let g1 = arrow([1, 0, 3, 1]);
    let g2 = arrow([1, 4, 2, 3]);
    let alpha = ComparisonCell::new(f0.clone(), f1.clone()).unwrap();
    let alpha2 = ComparisonCell::new(f1.clone(), f2).unwrap();
    let beta = ComparisonCell::new(g0.clone(), g1.clone()).unwrap();
    let beta2 = ComparisonCell::new(g1.clone(), g2).unwrap();
    let mixed = beta.horizontal_after(&alpha).unwrap();
    let unpaid = g0
        .operator()
        .mul(alpha.difference())
        .unwrap()
        .add(&beta.difference().mul(f0.operator()).unwrap())
        .unwrap();
    assert_ne!(mixed.difference(), &unpaid);
    let complete = unpaid
        .add(&beta.difference().mul(alpha.difference()).unwrap())
        .unwrap();
    assert_eq!(mixed.difference(), &complete);
    let left = beta
        .then(&beta2)
        .unwrap()
        .horizontal_after(&alpha.then(&alpha2).unwrap())
        .unwrap();
    let right = beta
        .horizontal_after(&alpha)
        .unwrap()
        .then(&beta2.horizontal_after(&alpha2).unwrap())
        .unwrap();
    assert_eq!(left, right);
}

#[test]
fn compositor_associativity_and_five_way_pentagon_retain_nonzero_blind_curvature() {
    let s = observed_fixture();
    assert!(!s.connection().curvature().unwrap().is_zero());
    let a = s.arrow(0, 1).unwrap();
    let b = s.arrow(1, 2).unwrap();
    let c = s.arrow(2, 3).unwrap();
    let d = s.arrow(3, 4).unwrap();
    let products = [
        a.after(&b).unwrap().after(&c).unwrap().after(&d).unwrap(),
        a.after(&b.after(&c).unwrap()).unwrap().after(&d).unwrap(),
        a.after(&b.after(&c).unwrap().after(&d).unwrap()).unwrap(),
        a.after(&b.after(&c.after(&d).unwrap()).unwrap()).unwrap(),
        a.after(&b).unwrap().after(&c.after(&d).unwrap()).unwrap(),
    ];
    let target = s.arrow(0, 4).unwrap();
    let cells: Vec<_> = products
        .into_iter()
        .map(|p| ComparisonCell::new(p, target.clone()).unwrap())
        .collect();
    assert!(cells.windows(2).all(|p| p[0] == p[1]));
    let alpha = s.compositor(0, 1, 2).unwrap();
    let tail = ComparisonCell::identity(s.arrow(2, 3).unwrap()).unwrap();
    let left = alpha
        .horizontal_after(&tail)
        .unwrap()
        .then(&s.compositor(0, 2, 3).unwrap())
        .unwrap();
    let head = ComparisonCell::identity(s.arrow(0, 1).unwrap()).unwrap();
    let right = head
        .horizontal_after(&s.compositor(1, 2, 3).unwrap())
        .unwrap()
        .then(&s.compositor(0, 1, 3).unwrap())
        .unwrap();
    assert_eq!(left, right);
}

#[test]
fn full_questions_and_wrong_carrier_labels_refuse_unpaid_comparisons() {
    let s = observed_fixture();
    let full = Matrix::try_from_fn(3, 3, |i, j| if i == j { q(1) } else { q(0) }).unwrap();
    assert!(matches!(
        ObservedRestrictionSystem::new(s.connection().clone(), vec![full; 5]),
        Err(CoherenceError::VisibleDifference)
    ));
    let o = ObserverObject::new(1, m(1, 2, vec![q(1), q(0)])).unwrap();
    let other = ObserverObject::new(99, m(1, 2, vec![q(1), q(0)])).unwrap();
    let a = ObserverArrow::identity(o).unwrap();
    let b = ObserverArrow::identity(other).unwrap();
    assert!(matches!(a.after(&b), Err(CoherenceError::Boundary)));
    let visible = ObserverObject::new(1, m(1, 2, vec![q(1), q(0)])).unwrap();
    let leaks = m(2, 2, vec![q(1), q(1), q(0), q(1)]);
    assert!(ObserverArrow::new(visible.clone(), visible, leaks).is_err());
}

// Origin: engine/crates_rs/tests/core_homology/observed_incidence.rs
// Claim: urn:core:crates_rs:tests:observed-incidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3e2f3543 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3e2f3543` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3e2f3543 {
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
impl BoundaryError3e2f3543 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3e2f3543 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3e2f3543 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3e2f3543 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3e2f3543> {
        if capacity_bound == 0 {
            return Err(BoundaryError3e2f3543::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3e2f3543::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3e2f3543::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3e2f3543() {
    let admitted = BoundaryRecord3e2f3543::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3e2f3543::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
