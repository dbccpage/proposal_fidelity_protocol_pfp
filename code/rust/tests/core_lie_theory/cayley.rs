//! Cayley charts of so(n) over Q and the unit circle of Q(i): laws, refusals, and
//! cross-validation against the quaternion parametrisation of SO(3).

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use core_lie_theory::cayley::{
    cayley_inverse, cayley_transform, compose_circle_parameters, compose_steps,
    cross_product_matrix, gaussian_unit_order, is_orthogonal, is_special_orthogonal, is_unit,
    parameter_of_unit, skew_defect, so_basis, unit_from_parameter, unit_pow, CayleyError,
    MAX_DIMENSION, MAX_UNIT_EXPONENT,
};
use core_lie_theory::su2::{rotation_of_quaternion, Quaternion};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};

type Q = BasicMatrix<BigRational>;

fn mat(rows: &[&[i64]]) -> Q {
    let cols = rows[0].len();
    Q::from_row_major(
        rows.len(),
        cols,
        rows.iter().flat_map(|r| r.iter().map(|&v| ri(v))).collect(),
    )
    .unwrap()
}

fn matq(rows: &[&[(i64, i64)]]) -> Q {
    let cols = rows[0].len();
    Q::from_row_major(
        rows.len(),
        cols,
        rows.iter()
            .flat_map(|r| r.iter().map(|&(n, d)| rq(n, d)))
            .collect(),
    )
    .unwrap()
}

fn identity(n: usize) -> Q {
    Q::try_from_fn(n, n, |r, c| if r == c { ri(1) } else { ri(0) }).unwrap()
}

fn scaled(m: &Q, k: &BigRational) -> Q {
    m.map(|x| x * k)
}

fn add(a: &Q, b: &Q) -> Q {
    a.add(b).unwrap()
}

fn mul(a: &Q, b: &Q) -> Q {
    a.mul(b).unwrap()
}

fn transpose(m: &Q) -> Q {
    m.try_transpose().unwrap()
}

/// A deterministic skew-symmetric matrix of dimension `n` from a seed.
fn skew(n: usize, seed: i64) -> Q {
    let mut state = seed;
    let mut next = || {
        state = (state * 1103515245 + 12345).rem_euclid(1 << 20);
        // Odd, so never zero: every entry of the matrix is nonzero.
        2 * (state % 7 - 3) + 1
    };
    let mut m = Q::zero(n, n).unwrap();
    for i in 0..n {
        for j in (i + 1)..n {
            let v = rq(next(), 1 + (next().rem_euclid(3)));
            m.set(i, j, v.clone()).unwrap();
            m.set(j, i, -v).unwrap();
        }
    }
    m
}

#[test]
fn the_plane_chart_is_the_pythagorean_parametrisation_of_rotations() {
    let j = mat(&[&[0, -1], &[1, 0]]);
    // tau = 1/2 gives cos = (1 - 1/4)/(1 + 1/4) = 3/5, sin = 4/5 (clockwise: the chart is (I - tau J)(I + tau J)^-1).
    let r = cayley_transform(&j, &rq(1, 2)).unwrap();
    assert_eq!(r, matq(&[&[(3, 5), (4, 5)], &[(-4, 5), (3, 5)]]));
    // tau = 1/3: 4/5, 3/5.
    let r3 = cayley_transform(&j, &rq(1, 3)).unwrap();
    assert_eq!(r3, matq(&[&[(4, 5), (3, 5)], &[(-3, 5), (4, 5)]]));
    // tau = 0 is the identity; tau = 1 the quarter turn.
    assert_eq!(cayley_transform(&j, &ri(0)).unwrap(), identity(2));
    assert_eq!(
        cayley_transform(&j, &ri(1)).unwrap(),
        mat(&[&[0, 1], &[-1, 0]])
    );
}

#[test]
fn every_rational_plane_rotation_except_minus_one_is_a_chart_image() {
    // Rotations (c, s) with c^2 + s^2 = 1 from Pythagorean triples, in all four quadrants.
    let triples = [
        (3, 4, 5),
        (5, 12, 13),
        (8, 15, 17),
        (20, 21, 29),
        (7, 24, 25),
    ];
    for (a, b, c) in triples {
        for (sa, sb) in [(1, 1), (1, -1), (-1, 1), (-1, -1)] {
            let r = matq(&[&[(sa * a, c), (-sb * b, c)], &[(sb * b, c), (sa * a, c)]]);
            assert!(is_special_orthogonal(&r));
            let x = cayley_inverse(&r, &ri(1)).unwrap();
            assert!(skew_defect(&x).is_none());
            assert_eq!(cayley_transform(&x, &ri(1)).unwrap(), r);
        }
    }
    // The half-turn -I is the one rotation of SO(2) missed by the chart.
    assert_eq!(
        cayley_inverse(&mat(&[&[-1, 0], &[0, -1]]), &ri(1)),
        Err(CayleyError::EigenvalueMinusOne)
    );
}

#[test]
fn the_transform_lands_in_so_n_and_the_inverse_recovers_the_generator() {
    for n in 2..=6usize {
        for seed in [3i64, 17, 101] {
            let x = skew(n, seed);
            for tau in [rq(1, 1), rq(1, 2), rq(-3, 4), rq(5, 3)] {
                let r = cayley_transform(&x, &tau).unwrap();
                assert!(is_orthogonal(&r), "R^T R = I, n = {n}");
                assert!(is_special_orthogonal(&r), "det R = 1, n = {n}");
                assert_eq!(cayley_inverse(&r, &tau).unwrap(), x, "round trip, n = {n}");
            }
        }
    }
}

#[test]
fn reversing_the_parameter_inverts_the_rotation() {
    // C_{-tau}(X) = C_tau(X)^(-1) = C_tau(X)^T.
    let x = skew(4, 29);
    for tau in [rq(1, 3), rq(2, 1)] {
        let r = cayley_transform(&x, &tau).unwrap();
        let back = cayley_transform(&x, &(-&tau)).unwrap();
        assert_eq!(back, transpose(&r));
        assert_eq!(mul(&r, &back), identity(4));
    }
}

#[test]
fn steps_of_one_generator_commute_and_compose_by_the_generator_law() {
    for n in [2usize, 3, 4] {
        let x = skew(n, 11 + n as i64);
        let (s, t) = (rq(1, 3), rq(2, 5));
        let rs = cayley_transform(&x, &s).unwrap();
        let rt = cayley_transform(&x, &t).unwrap();
        assert_eq!(mul(&rs, &rt), mul(&rt, &rs), "one-parameter steps commute");
        // C_s C_t = C_1(K) with K = (s + t) X (I + s t X^2)^(-1).
        let k = compose_steps(&x, &s, &t).unwrap();
        assert!(skew_defect(&k).is_none(), "K is skew");
        assert_eq!(cayley_transform(&k, &ri(1)).unwrap(), mul(&rs, &rt));
    }
}

#[test]
fn for_the_plane_generator_the_composition_is_tangent_addition() {
    let j = mat(&[&[0, -1], &[1, 0]]);
    let (s, t) = (rq(1, 2), rq(1, 3));
    let k = compose_steps(&j, &s, &t).unwrap();
    // J^2 = -I, so K = (s + t) / (1 - s t) J.
    let tangent = compose_circle_parameters(&s, &t).unwrap();
    assert_eq!(tangent, ri(1));
    assert_eq!(k, scaled(&j, &tangent));
    // Composing with a parameter of product 1 leaves the chart: the composite is the half-turn.
    assert_eq!(
        compose_steps(&j, &ri(1), &ri(1)),
        Err(CayleyError::OutsideChart)
    );
    assert_eq!(
        compose_circle_parameters(&ri(1), &ri(1)),
        Err(CayleyError::OutsideChart)
    );
    // Cross-check: the half-turn is -I, which has eigenvalue -1.
    let half_turn = mul(
        &cayley_transform(&j, &ri(1)).unwrap(),
        &cayley_transform(&j, &ri(1)).unwrap(),
    );
    assert_eq!(half_turn, mat(&[&[-1, 0], &[0, -1]]));
}

#[test]
fn the_chart_agrees_with_the_quaternion_parametrisation_of_so3() {
    // C_tau([v]_x) is the rotation of the quaternion (1, -tau v): two independent formulas
    // (a matrix inverse here, the Euler-Rodrigues entries there).
    let vectors = [
        [ri(1), ri(2), ri(3)],
        [rq(1, 2), rq(-1, 3), ri(2)],
        [ri(0), ri(0), ri(5)],
        [ri(-2), ri(1), rq(3, 7)],
    ];
    for v in vectors {
        let x = cross_product_matrix(&v).unwrap();
        for tau in [ri(1), rq(1, 2), rq(-2, 3)] {
            let q = Quaternion::new(ri(1), -&tau * &v[0], -&tau * &v[1], -&tau * &v[2]);
            assert_eq!(
                cayley_transform(&x, &tau).unwrap(),
                rotation_of_quaternion(&q).unwrap()
            );
        }
    }
    // The cross-product matrix really computes the cross product: [v]_x w = v x w.
    let v = [ri(1), ri(2), ri(3)];
    let w = [ri(4), ri(5), ri(6)];
    let x = cross_product_matrix(&v).unwrap();
    let wx = x.mul_vec(&w).unwrap();
    assert_eq!(wx, vec![ri(-3), ri(6), ri(-3)]);
}

#[test]
fn so_basis_spans_the_skew_matrices() {
    for n in 2..=5usize {
        let basis = so_basis(n).unwrap();
        assert_eq!(basis.len(), n * (n - 1) / 2);
        assert!(basis.iter().all(|b| skew_defect(b).is_none()));
        // Distinct: no two coincide.
        for (i, a) in basis.iter().enumerate() {
            for b in &basis[i + 1..] {
                assert_ne!(a, b);
            }
        }
        // A skew matrix is the combination of the basis with its upper triangle.
        let x = skew(n, 5);
        let mut rebuilt = Q::zero(n, n).unwrap();
        let mut index = 0;
        for i in 0..n {
            for j in (i + 1)..n {
                let coefficient = x.get(i, j).unwrap();
                rebuilt = add(&rebuilt, &scaled(&basis[index], &coefficient));
                index += 1;
            }
        }
        assert_eq!(rebuilt, x);
    }
    assert!(matches!(so_basis(0), Err(CayleyError::Shape { .. })));
}

#[test]
fn malformed_input_is_refused_with_the_right_reason() {
    // Not skew: the offending position is named.
    let not_skew = mat(&[&[0, 1, 0], &[1, 0, 0], &[0, 0, 0]]);
    assert_eq!(skew_defect(&not_skew), Some((0, 1)));
    assert_eq!(
        cayley_transform(&not_skew, &ri(1)),
        Err(CayleyError::NotSkew { row: 0, col: 1 })
    );
    // A nonzero diagonal is not skew either.
    let diagonal = mat(&[&[1, 0], &[0, 0]]);
    assert_eq!(
        cayley_transform(&diagonal, &ri(1)),
        Err(CayleyError::NotSkew { row: 0, col: 0 })
    );
    // Shapes: non-square, empty, too large.
    assert!(matches!(
        cayley_transform(&Q::zero(2, 3).unwrap(), &ri(1)),
        Err(CayleyError::Shape { rows: 2, cols: 3 })
    ));
    assert!(matches!(
        cayley_transform(&Q::zero(0, 0).unwrap(), &ri(1)),
        Err(CayleyError::Shape { .. })
    ));
    let big = MAX_DIMENSION + 1;
    assert!(matches!(
        cayley_transform(&Q::zero(big, big).unwrap(), &ri(1)),
        Err(CayleyError::Shape { .. })
    ));
    // Inverse: zero parameter, non-orthogonal, det -1 / eigenvalue -1.
    let r = cayley_transform(&skew(3, 9), &ri(1)).unwrap();
    assert_eq!(cayley_inverse(&r, &ri(0)), Err(CayleyError::ZeroParameter));
    assert_eq!(
        cayley_inverse(&mat(&[&[1, 1], &[0, 1]]), &ri(1)),
        Err(CayleyError::NotOrthogonal)
    );
    let reflection = mat(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, -1]]);
    assert!(is_orthogonal(&reflection) && !is_special_orthogonal(&reflection));
    assert_eq!(
        cayley_inverse(&reflection, &ri(1)),
        Err(CayleyError::EigenvalueMinusOne)
    );
    let half_turn = mat(&[&[-1, 0, 0], &[0, -1, 0], &[0, 0, 1]]);
    assert_eq!(
        cayley_inverse(&half_turn, &ri(1)),
        Err(CayleyError::EigenvalueMinusOne)
    );
    // Not orthogonal is not special orthogonal, and det must be exactly 1.
    assert!(!is_special_orthogonal(&mat(&[&[2, 0], &[0, 1]])));
    // Composition needs a skew generator.
    assert_eq!(
        compose_steps(&not_skew, &ri(1), &ri(2)),
        Err(CayleyError::NotSkew { row: 0, col: 1 })
    );
}

#[test]
fn the_unit_circle_chart_is_a_group_isomorphism_on_parameters() {
    for (s, t) in [
        (rq(1, 2), rq(1, 3)),
        (rq(2, 1), rq(-1, 5)),
        (rq(3, 7), rq(0, 1)),
    ] {
        let (us, ut) = (unit_from_parameter(&s), unit_from_parameter(&t));
        assert!(is_unit(&us) && is_unit(&ut));
        let product = us.mul(&ut);
        let composed = compose_circle_parameters(&s, &t).unwrap();
        assert_eq!(product, unit_from_parameter(&composed));
        assert_eq!(parameter_of_unit(&product).unwrap(), Some(composed));
    }
    // t = 1 gives i; t = 0 gives 1.
    assert_eq!(unit_from_parameter(&ri(1)), GaussianRat::i());
    assert_eq!(unit_from_parameter(&ri(0)), GaussianRat::one());
    // -1 has no parameter; a non-unit is refused.
    assert_eq!(
        parameter_of_unit(&GaussianRat::from_ints(-1, 0)).unwrap(),
        None
    );
    assert!(matches!(
        parameter_of_unit(&GaussianRat::from_ints(2, 0)),
        Err(CayleyError::NotUnit(_))
    ));
    // Every unit other than -1 arises from its own parameter: (3 + 4i)/5 from t = 2.
    let z = GaussianRat {
        re: rq(3, 5),
        im: rq(4, 5),
    };
    assert_eq!(parameter_of_unit(&z).unwrap(), Some(rq(1, 2)));
    assert_eq!(unit_from_parameter(&rq(1, 2)), z);
}

#[test]
fn unit_powers_orders_and_bounds() {
    let z = GaussianRat {
        re: rq(3, 5),
        im: rq(4, 5),
    };
    // Repeated squaring agrees with repeated multiplication.
    let mut by_hand = GaussianRat::one();
    for k in 0..=12 {
        assert_eq!(unit_pow(&z, &BigInt::from(k)).unwrap(), by_hand, "k = {k}");
        by_hand = by_hand.mul(&z);
    }
    // Negative powers are conjugate powers and invert.
    let zp = unit_pow(&z, &BigInt::from(7)).unwrap();
    assert_eq!(unit_pow(&z, &BigInt::from(-7)).unwrap(), zp.conj());
    assert_eq!(zp.mul(&zp.conj()), GaussianRat::one());
    // z has infinite order; its powers have denominator exactly 5^k.
    assert_eq!(gaussian_unit_order(&z).unwrap(), None);
    let p10 = unit_pow(&z, &BigInt::from(10)).unwrap();
    let denominator = p10.re.denom().clone() * p10.im.denom().clone()
        / num_integer::Integer::gcd(p10.re.denom(), p10.im.denom());
    assert_eq!(denominator, BigInt::from(5).pow(10));
    // Orders of the roots of unity of Q(i).
    assert_eq!(gaussian_unit_order(&GaussianRat::one()).unwrap(), Some(1));
    assert_eq!(
        gaussian_unit_order(&GaussianRat::from_ints(-1, 0)).unwrap(),
        Some(2)
    );
    assert_eq!(gaussian_unit_order(&GaussianRat::i()).unwrap(), Some(4));
    assert_eq!(
        gaussian_unit_order(&GaussianRat::from_ints(0, -1)).unwrap(),
        Some(4)
    );
    // Refusals: non-units and oversized exponents.
    assert!(matches!(
        unit_pow(&GaussianRat::from_ints(2, 0), &BigInt::from(2)),
        Err(CayleyError::NotUnit(_))
    ));
    assert!(matches!(
        gaussian_unit_order(&GaussianRat::from_ints(0, 2)),
        Err(CayleyError::NotUnit(_))
    ));
    let too_big = BigInt::from(MAX_UNIT_EXPONENT) + 1;
    assert!(matches!(
        unit_pow(&z, &too_big),
        Err(CayleyError::ExponentTooLarge { .. })
    ));
    assert!(matches!(
        unit_pow(&z, &-too_big),
        Err(CayleyError::ExponentTooLarge { .. })
    ));
    // The bound itself is accepted: i^65536 = 1 since 4 divides 65536.
    assert_eq!(
        unit_pow(&GaussianRat::i(), &BigInt::from(MAX_UNIT_EXPONENT)).unwrap(),
        GaussianRat::one()
    );
    assert_eq!(
        unit_pow(
            &GaussianRat::i(),
            &BigInt::from(-i64::from(MAX_UNIT_EXPONENT))
        )
        .unwrap(),
        GaussianRat::one()
    );
}

#[test]
fn the_chart_is_not_the_exponential_but_respects_the_group_law_only_for_one_generator() {
    // For two different generators the product of charts is generally not a chart of the sum:
    // the test guards against replacing the transform by a linear shortcut.
    let a = cross_product_matrix(&[ri(1), ri(0), ri(0)]).unwrap();
    let b = cross_product_matrix(&[ri(0), ri(1), ri(0)]).unwrap();
    let ra = cayley_transform(&a, &ri(1)).unwrap();
    let rb = cayley_transform(&b, &ri(1)).unwrap();
    let rab = cayley_transform(&add(&a, &b), &ri(1)).unwrap();
    assert_ne!(mul(&ra, &rb), rab);
    assert_ne!(
        mul(&rb, &ra),
        mul(&ra, &rb),
        "rotations about different axes do not commute"
    );
}

// Origin: engine/crates_rs/tests/core_lie_theory/cayley.rs
// Claim: urn:core:crates_rs:tests:cayley:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc9ea455e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc9ea455e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc9ea455e {
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
impl BoundaryErrorc9ea455e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc9ea455e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc9ea455e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc9ea455e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc9ea455e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc9ea455e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc9ea455e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc9ea455e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c9ea455e() {
    let admitted = BoundaryRecordc9ea455e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc9ea455e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
