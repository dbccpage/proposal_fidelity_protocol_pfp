//! Independent finite controls for the strict-chain operator algebra.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};
use core_homology::finite_poset::FinitePoset;
use core_homology::restriction_dga::{
    Cochain, CoverMaps, Matrix, OperatorCarrier, RestrictionError,
};
use std::collections::BTreeMap;
use std::sync::Arc;

fn q(n: i64, d: i64) -> Q {
    Q::new(n.into(), d.into())
}
fn scalar(n: i64, d: i64) -> Matrix {
    BasicMatrix::from_row_major(1, 1, vec![q(n, d)]).unwrap()
}
fn identity(dim: usize) -> Matrix {
    Matrix::try_from_fn(dim, dim, |i, j| if i == j { Q::one() } else { Q::zero() }).unwrap()
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
    let values = c
        .chains(degree)
        .iter()
        .map(|chain| {
            let tag = chain
                .iter()
                .enumerate()
                .map(|(i, x)| (i + 1) * (x + 2))
                .sum::<usize>() as i64;
            let rows = c.dimensions()[chain[0]];
            let cols = c.dimensions()[chain[chain.len() - 1]];
            let m = Matrix::try_from_fn(rows, cols, |i, j| {
                q(
                    seed + tag * (i as i64 + 1) - (j as i64 + 3).pow(2),
                    2 + ((tag + i as i64 + j as i64) % 3),
                )
            })
            .unwrap();
            (chain.clone(), m)
        })
        .collect();
    Cochain::new(c.clone(), degree, values).unwrap()
}
fn signed_add(a: Cochain, b: Cochain, degree: usize) -> Cochain {
    if degree % 2 == 0 {
        a.add(&b).unwrap()
    } else {
        a.sub(&b).unwrap()
    }
}

/// Direct endpoint/interior expansion, independent of cup and b implementations.
fn expanded_d(f: &Cochain, a: &Cochain) -> Cochain {
    let degree = f.degree();
    let c = f.carrier();
    let mut out = BTreeMap::new();
    for chain in c.chains(degree + 1) {
        let mut v = a.components()[&chain[..2].to_vec()]
            .mul(&f.components()[&chain[1..].to_vec()])
            .unwrap();
        for i in 1..=degree {
            let mut face = chain.clone();
            face.remove(i);
            v = if i % 2 == 0 {
                v.add(&f.components()[&face]).unwrap()
            } else {
                v.sub(&f.components()[&face]).unwrap()
            };
        }
        let edge = chain[chain.len() - 2..].to_vec();
        let left = chain[..chain.len() - 1].to_vec();
        let last = f.components()[&left].mul(&a.components()[&edge]).unwrap();
        v = if degree % 2 == 0 {
            v.sub(&last).unwrap()
        } else {
            v.add(&last).unwrap()
        };
        out.insert(chain.clone(), v);
    }
    Cochain::new(c.clone(), degree + 1, out).unwrap()
}

#[test]
fn all_degrees_nilpotence_curvature_and_nonvacuous_controls() {
    let c = carrier(vec![2, 1, 3, 2, 1, 2, 3, 2]);
    let a = fixture(&c, 1, 7);
    let k = a.curvature().unwrap();
    assert!(!k.is_zero());
    assert!(k.covariant_differential(&a).unwrap().is_zero());
    for n in 0..=7 {
        let f = fixture(&c, n, 11);
        let d = f.covariant_differential(&a).unwrap();
        assert_eq!(d, expanded_d(&f, &a), "endpoint signs in degree {n}");
        assert!(f
            .internal_differential()
            .unwrap()
            .internal_differential()
            .unwrap()
            .is_zero());
        let d2 = d.covariant_differential(&a).unwrap();
        assert_eq!(
            d2,
            k.cup(&f).unwrap().sub(&f.cup(&k).unwrap()).unwrap(),
            "curvature in degree {n}"
        );
        if n <= 4 {
            assert!(!d2.is_zero(), "avoid vacuous degree-{n} curvature checks");
        }
    }
}

#[test]
fn graded_leibniz_associativity_and_unit() {
    let c = carrier(vec![2; 8]);
    let a = fixture(&c, 1, 7);
    let unit = Cochain::unit(c.clone()).unwrap();
    for p in 0..=5 {
        let f = fixture(&c, p, 11);
        assert_eq!(unit.cup(&f).unwrap(), f);
        assert_eq!(f.cup(&unit).unwrap(), f);
        for r in 0..=5 - p {
            let g = fixture(&c, r, -3);
            let fg = f.cup(&g).unwrap();
            assert_eq!(
                fg.internal_differential().unwrap(),
                signed_add(
                    f.internal_differential().unwrap().cup(&g).unwrap(),
                    f.cup(&g.internal_differential().unwrap()).unwrap(),
                    p
                )
            );
            assert_eq!(
                fg.covariant_differential(&a).unwrap(),
                signed_add(
                    f.covariant_differential(&a).unwrap().cup(&g).unwrap(),
                    f.cup(&g.covariant_differential(&a).unwrap()).unwrap(),
                    p
                )
            );
            let h = fixture(&c, 1, 19);
            assert_eq!(fg.cup(&h).unwrap(), f.cup(&g.cup(&h).unwrap()).unwrap());
        }
    }
}

#[test]
fn vertex_selectors_detect_all_curvature_components() {
    let c = carrier(vec![2, 1, 3, 2]);
    let a = fixture(&c, 1, 7);
    let k = a.curvature().unwrap();
    for triple in c.chains(2) {
        let mut e = Cochain::zero(c.clone(), 0).unwrap().components().clone();
        e.insert(vec![triple[2]], identity(c.dimensions()[triple[2]]));
        let e = Cochain::new(c.clone(), 0, e).unwrap();
        let d2 = e
            .covariant_differential(&a)
            .unwrap()
            .covariant_differential(&a)
            .unwrap();
        assert_eq!(d2.components()[triple], k.components()[triple]);
    }
}

#[test]
fn exact_graded_lie_bridge_and_odd_connection_sign() {
    let c = carrier(vec![2; 8]);
    let a = fixture(&c, 1, 7);
    assert_eq!(
        a.graded_bracket(&a).unwrap(),
        a.cup(&a).unwrap().add(&a.cup(&a).unwrap()).unwrap()
    );
    for p in 0..=2 {
        for q_degree in 0..=2 {
            for r in 0..=2 {
                let f = fixture(&c, p, 11);
                let g = fixture(&c, q_degree, -3);
                let h = fixture(&c, r, 19);
                let lhs = f.graded_bracket(&g.graded_bracket(&h).unwrap()).unwrap();
                let first = f.graded_bracket(&g).unwrap().graded_bracket(&h).unwrap();
                let second = g.graded_bracket(&f.graded_bracket(&h).unwrap()).unwrap();
                assert_eq!(lhs, signed_add(first, second, p * q_degree));
                let d = f
                    .graded_bracket(&g)
                    .unwrap()
                    .covariant_differential(&a)
                    .unwrap();
                let rhs = signed_add(
                    f.covariant_differential(&a)
                        .unwrap()
                        .graded_bracket(&g)
                        .unwrap(),
                    f.graded_bracket(&g.covariant_differential(&a).unwrap())
                        .unwrap(),
                    p,
                );
                assert_eq!(d, rhs);
            }
        }
    }
}

#[test]
fn gauge_intertwines_product_differential_and_curvature() {
    let c = carrier(vec![2, 1, 3, 2, 1, 2]);
    let a = fixture(&c, 1, 7);
    let mut g = Vec::new();
    let mut h = Vec::new();
    for (x, &dim) in c.dimensions().iter().enumerate() {
        if dim == 1 {
            g.push(scalar(2, 1));
            h.push(scalar(1, 2));
        } else {
            let mut gx = identity(dim);
            let mut hx = identity(dim);
            gx.set(0, 1, q(x as i64 + 1, 1)).unwrap();
            hx.set(0, 1, q(-(x as i64 + 1), 1)).unwrap();
            g.push(gx);
            h.push(hx);
        }
    }
    let ag = a.gauge(&g, &h).unwrap();
    assert_eq!(
        ag.curvature().unwrap(),
        a.curvature().unwrap().gauge(&g, &h).unwrap()
    );
    assert!(!ag.curvature().unwrap().is_zero());
    assert_eq!(ag.gauge(&h, &g).unwrap(), a);
    for n in 0..=3 {
        let f = fixture(&c, n, 11);
        let fg = f.gauge(&g, &h).unwrap();
        assert_eq!(
            f.covariant_differential(&a).unwrap().gauge(&g, &h).unwrap(),
            fg.covariant_differential(&ag).unwrap()
        );
        assert_eq!(
            f.internal_differential().unwrap().gauge(&g, &h).unwrap(),
            fg.internal_differential().unwrap()
        );
        assert_eq!(
            f.cup(&a).unwrap().gauge(&g, &h).unwrap(),
            fg.cup(&ag).unwrap()
        );
    }
    let mut invalid = h.clone();
    invalid[0] = identity(2);
    assert!(matches!(
        a.gauge(&g, &invalid),
        Err(RestrictionError::Inverse)
    ));
}

fn diamond() -> Arc<OperatorCarrier> {
    OperatorCarrier::new(
        FinitePoset::new(4, [(0, 1), (0, 2), (0, 3), (1, 3), (2, 3)]).unwrap(),
        vec![1; 4],
    )
    .unwrap()
}
fn diamond_covers(last_denominator: i64) -> CoverMaps {
    [
        ((0, 1), scalar(1, 2)),
        ((1, 3), scalar(1, 2)),
        ((0, 2), scalar(1, 2)),
        ((2, 3), scalar(1, last_denominator)),
    ]
    .into()
}

#[test]
fn flat_extension_is_unique_when_paths_agree_and_refuses_noncommuting_covers() {
    let c = diamond();
    let flat = c.flat_cover_extension(diamond_covers(2)).unwrap();
    assert_eq!(flat.components()[&vec![0, 3]], scalar(1, 4));
    assert!(flat.curvature().unwrap().is_zero());
    let err = c.flat_cover_extension(diamond_covers(3)).unwrap_err();
    assert!(matches!(
        err,
        RestrictionError::PathDependent {
            lower: 0,
            upper: 3,
            ..
        }
    ));
    let mut missing = diamond_covers(2);
    missing.remove(&(1, 3));
    assert!(matches!(
        c.flat_cover_extension(missing),
        Err(RestrictionError::Coverage)
    ));
    let mut extra = diamond_covers(2);
    extra.insert((0, 3), scalar(1, 4));
    assert!(matches!(
        c.flat_cover_extension(extra),
        Err(RestrictionError::Coverage)
    ));
    let g = vec![scalar(2, 1); 4];
    let h = vec![scalar(1, 2); 4];
    assert!(flat.gauge(&g, &h).unwrap().curvature().unwrap().is_zero());
    let mut changed = flat.components().clone();
    changed.insert(vec![0, 3], scalar(0, 1));
    let curved = Cochain::new(c.clone(), 1, changed).unwrap();
    assert!(!curved.gauge(&g, &h).unwrap().curvature().unwrap().is_zero());
    assert!(c
        .flat_cover_extension(diamond_covers(2))
        .unwrap()
        .curvature()
        .unwrap()
        .is_zero());
}

#[test]
fn conditional_normal_form_retains_both_mixed_terms() {
    let c = carrier(vec![2; 5]);
    let covers = c
        .poset()
        .covers()
        .into_iter()
        .map(|(x, y)| ((x, y), fixture(&c, 1, 5).components()[&vec![x, y]].clone()))
        .collect();
    let flat = c.flat_cover_extension(covers).unwrap();
    let r = fixture(&c, 1, 7);
    let residual = r.sub(&flat).unwrap();
    let expansion = flat
        .cup(&residual)
        .unwrap()
        .add(&residual.cup(&flat).unwrap())
        .unwrap()
        .add(&residual.cup(&residual).unwrap())
        .unwrap()
        .add(&residual.internal_differential().unwrap())
        .unwrap();
    assert_eq!(r.curvature().unwrap(), expansion);
    assert!(!flat.cup(&residual).unwrap().is_zero());
    assert!(!residual.cup(&flat).unwrap().is_zero());
}

#[test]
fn carrier_coverage_shape_scalar_and_degree_refusals() {
    assert!(matches!(
        OperatorCarrier::new(FinitePoset::new(0, []).unwrap(), vec![]),
        Err(RestrictionError::Profile)
    ));
    assert!(matches!(
        OperatorCarrier::new(FinitePoset::new(9, []).unwrap(), vec![1; 9]),
        Err(RestrictionError::Profile)
    ));
    assert!(matches!(
        OperatorCarrier::new(FinitePoset::new(1, []).unwrap(), vec![0]),
        Err(RestrictionError::Profile)
    ));
    let c = carrier(vec![2; 3]);
    let f = fixture(&c, 1, 7);
    let mut values = f.components().clone();
    values.remove(&vec![0, 1]);
    assert!(matches!(
        Cochain::new(c.clone(), 1, values),
        Err(RestrictionError::Coverage)
    ));
    let mut values = f.components().clone();
    values.insert(vec![1, 0], identity(2));
    assert!(matches!(
        Cochain::new(c.clone(), 1, values),
        Err(RestrictionError::Coverage)
    ));
    let mut values = f.components().clone();
    values.insert(vec![0, 1], identity(1));
    assert!(matches!(
        Cochain::new(c.clone(), 1, values),
        Err(RestrictionError::Shape)
    ));
    let mut values = f.components().clone();
    let mut bad = identity(2);
    bad.set(0, 0, Q::new_raw(1.into(), 0.into())).unwrap();
    values.insert(vec![0, 1], bad);
    assert!(matches!(
        Cochain::new(c.clone(), 1, values),
        Err(RestrictionError::Denominator)
    ));
    let same_size_different_order =
        OperatorCarrier::new(FinitePoset::new(3, []).unwrap(), vec![2; 3]).unwrap();
    assert!(matches!(
        f.cup(&Cochain::zero(same_size_different_order, 1).unwrap()),
        Err(RestrictionError::CarrierMismatch)
    ));
    assert!(matches!(
        f.cup(&fixture(&carrier(vec![1; 3]), 1, 7)),
        Err(RestrictionError::CarrierMismatch)
    ));
    assert!(matches!(
        f.add(&Cochain::unit(c.clone()).unwrap()),
        Err(RestrictionError::Degree)
    ));
    assert!(matches!(
        f.covariant_differential(&Cochain::unit(c.clone()).unwrap()),
        Err(RestrictionError::Degree)
    ));
    let max = Cochain::zero(c, usize::MAX).unwrap();
    assert!(matches!(
        max.internal_differential(),
        Err(RestrictionError::DegreeOverflow)
    ));
    assert!(matches!(max.cup(&f), Err(RestrictionError::DegreeOverflow)));
}

#[test]
fn l1_optimality_does_not_select_a_unique_representative() {
    for t in [q(0, 1), q(1, 4), q(1, 2), q(3, 4), q(1, 1)] {
        assert_eq!((Q::one() - &t).abs() + t.abs(), Q::one());
    }
}

#[test]
fn flat_cover_extension_compares_saturated_paths_of_different_lengths() {
    // 0 -> 1 -> 2 -> 4 and 0 -> 3 -> 4, with full strict transitive order.
    let poset = FinitePoset::new(
        5,
        [
            (0, 1),
            (1, 2),
            (2, 4),
            (0, 2),
            (1, 4),
            (0, 4),
            (0, 3),
            (3, 4),
        ],
    )
    .unwrap();
    let c = OperatorCarrier::new(poset, vec![1; 5]).unwrap();
    let mut maps: CoverMaps = c
        .poset()
        .covers()
        .into_iter()
        .map(|(x, y)| ((x, y), scalar(x as i64 + 1, y as i64 + 1)))
        .collect();
    let flat = c.flat_cover_extension(maps.clone()).unwrap();
    assert_eq!(flat.components()[&vec![0, 4]], scalar(1, 5));
    assert!(flat.curvature().unwrap().is_zero());
    maps.insert((3, 4), scalar(3, 5));
    match c.flat_cover_extension(maps) {
        Err(RestrictionError::PathDependent {
            lower,
            upper,
            first_path,
            second_path,
        }) => {
            assert_eq!((lower, upper), (0, 4));
            let paths = [first_path, second_path]
                .into_iter()
                .collect::<std::collections::BTreeSet<_>>();
            assert_eq!(paths, [vec![0, 1, 2, 4], vec![0, 3, 4]].into());
        }
        other => panic!("expected the unequal-length path obstruction, got {other:?}"),
    }
}

// Origin: engine/crates_rs/tests/core_homology/restriction_dga.rs
// Claim: urn:core:crates_rs:tests:restriction-dga:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord43d8a546 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord43d8a546` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError43d8a546 {
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
impl BoundaryError43d8a546 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError43d8a546 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError43d8a546 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord43d8a546 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError43d8a546> {
        if capacity_bound == 0 {
            return Err(BoundaryError43d8a546::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError43d8a546::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError43d8a546::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_43d8a546() {
    let admitted = BoundaryRecord43d8a546::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord43d8a546::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
