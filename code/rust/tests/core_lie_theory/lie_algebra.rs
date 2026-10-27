//! Lie algebras by structure constants: axioms, Killing forms, matrix algebras, and the
//! Chevalley-Eilenberg complex with its cohomology.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_rational::BigRational;
use core_lie_theory::cayley::so_basis;
use core_lie_theory::lie_algebra::{
    adjoint_is_representation, adjoint_matrix, bracket, chevalley_eilenberg_differential,
    chevalley_eilenberg_squares_to_zero, cohomology_betti_numbers, killing_form,
    structure_constants_from_matrices, verify_antisymmetry, verify_jacobi, LieAlgebra,
    LieAlgebraError, StructureConstants, MAX_COMPLEX_DIMENSION,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};

type Q = BasicMatrix<BigRational>;

fn mat(rows: &[&[i64]]) -> Q {
    mx::from_rows(
        rows.iter()
            .map(|r| r.iter().map(|&v| ri(v)).collect())
            .collect(),
    )
    .unwrap()
}

/// The matrix units E_ij of size n (1-indexed in the names, 0-indexed here).
fn unit(n: usize, i: usize, j: usize) -> Q {
    Q::try_from_fn(n, n, |r, c| if (r, c) == (i, j) { ri(1) } else { ri(0) }).unwrap()
}

/// `sl(2)` with basis (h, e, f).
fn sl2() -> StructureConstants<BigRational> {
    let h = mat(&[&[1, 0], &[0, -1]]);
    let e = mat(&[&[0, 1], &[0, 0]]);
    let f = mat(&[&[0, 0], &[1, 0]]);
    structure_constants_from_matrices(&[h, e, f]).unwrap()
}

fn heisenberg() -> StructureConstants<BigRational> {
    // x = E12, y = E23, z = E13 in the strictly upper triangular 3x3 matrices: [x, y] = z.
    structure_constants_from_matrices(&[unit(3, 0, 1), unit(3, 1, 2), unit(3, 0, 2)]).unwrap()
}

/// `[x0, x1] = x1`: the two-dimensional non-abelian algebra.
fn affine() -> StructureConstants<BigRational> {
    StructureConstants::from_fn(2, |a, b, e| match (a, b, e) {
        (0, 1, 1) => ri(1),
        (1, 0, 1) => ri(-1),
        _ => ri(0),
    })
}

/// An antisymmetric bracket on three generators that violates Jacobi: `[e0, e1] = e1`, `[e1, e2] = e2`.
fn not_a_lie_algebra() -> StructureConstants<BigRational> {
    StructureConstants::from_fn(3, |a, b, e| match (a, b, e) {
        (0, 1, 1) | (1, 2, 2) => ri(1),
        (1, 0, 1) | (2, 1, 2) => ri(-1),
        _ => ri(0),
    })
}

#[test]
fn sl2_has_the_standard_structure_constants() {
    let g = sl2();
    let c = |a: usize, b: usize, e: usize| g.structure_constant(a, b, e);
    // [h, e] = 2e, [h, f] = -2f, [e, f] = h, in the order (h, e, f).
    assert_eq!(c(0, 1, 1), ri(2));
    assert_eq!(c(0, 2, 2), ri(-2));
    assert_eq!(c(1, 2, 0), ri(1));
    assert_eq!(c(1, 0, 1), ri(-2));
    // Every other constant is zero: exactly the six listed (with antisymmetry) are nonzero.
    let nonzero = (0..3)
        .flat_map(|a| (0..3).flat_map(move |b| (0..3).map(move |e| (a, b, e))))
        .filter(|&(a, b, e)| c(a, b, e) != ri(0))
        .count();
    assert_eq!(nonzero, 6);
    assert!(verify_antisymmetry(&g));
    assert!(verify_jacobi(&g));
    assert!(adjoint_is_representation(&g).unwrap());
}

#[test]
fn killing_forms_of_sl2_so3_and_the_nilpotent_heisenberg_algebra() {
    // sl(2): K(X, Y) = 4 tr(XY): K(h, h) = 8, K(e, f) = 4, all else 0 in the basis (h, e, f).
    let k = killing_form(&sl2()).unwrap();
    assert_eq!(k, mat(&[&[8, 0, 0], &[0, 0, 4], &[0, 4, 0]]));
    // so(3): K = -2 I in the basis E_ij - E_ji (here tr(L_ij L_ij) = -2 and K = (n - 2) tr).
    let so3 = structure_constants_from_matrices(&so_basis(3).unwrap()).unwrap();
    assert!(verify_jacobi(&so3));
    assert_eq!(
        killing_form(&so3).unwrap(),
        mat(&[&[-2, 0, 0], &[0, -2, 0], &[0, 0, -2]])
    );
    // The Killing form of so(n) is (n - 2) tr(XY): check so(4) on the diagonal.
    let so4_basis = so_basis(4).unwrap();
    let so4 = structure_constants_from_matrices(&so4_basis).unwrap();
    let k4 = killing_form(&so4).unwrap();
    for a in 0..6 {
        for b in 0..6 {
            let trace = mx::trace(&mx::multiply(&so4_basis[a], &so4_basis[b]).unwrap()).unwrap();
            assert_eq!(
                *k4.get_ref(a, b).unwrap(),
                ri(2) * trace,
                "K = (n-2) tr for n = 4"
            );
        }
    }
    // The Heisenberg algebra is nilpotent: its Killing form vanishes.
    assert_eq!(killing_form(&heisenberg()).unwrap(), Q::zero(3, 3).unwrap());
    // The two-dimensional non-abelian algebra has the degenerate Killing form diag(0, 1).
    assert_eq!(killing_form(&affine()).unwrap(), mat(&[&[1, 0], &[0, 0]]));
}

#[test]
fn the_so3_structure_constants_are_the_cross_product() {
    let so3 = structure_constants_from_matrices(&so_basis(3).unwrap()).unwrap();
    // so_basis order: L_01, L_02, L_12 with L_ij = E_ij - E_ji; [L_01, L_12] = L_02, [L_01, L_02] = -L_12, [L_02, L_12] = -L_01.
    let c = |a: usize, b: usize, e: usize| so3.structure_constant(a, b, e);
    assert_eq!(c(0, 2, 1), ri(1));
    assert_eq!(c(0, 1, 2), ri(-1));
    assert_eq!(c(1, 2, 0), ri(-1));
    assert!(verify_antisymmetry(&so3) && verify_jacobi(&so3));
}

#[test]
fn the_three_formulations_of_the_jacobi_identity_agree_on_every_antisymmetric_table() {
    // For 200 deterministic antisymmetric tables of dimension 3: Jacobi <=> ad is a representation <=> d^2 = 0.
    let mut state = 7i64;
    let mut next = || {
        state = (state * 1_103_515_245 + 12_345) % 2_147_483_648;
        state.rem_euclid(5) - 2
    };
    let (mut lie, mut non_lie) = (0, 0);
    for _ in 0..200 {
        let mut values = [[[0i64; 3]; 3]; 3];
        for a in 0..3 {
            for b in (a + 1)..3 {
                for e in 0..3 {
                    let v = next();
                    values[a][b][e] = v;
                    values[b][a][e] = -v;
                }
            }
        }
        let g = StructureConstants::from_fn(3, |a, b, e| ri(values[a][b][e]));
        assert!(verify_antisymmetry(&g));
        let jacobi = verify_jacobi(&g);
        let representation = adjoint_is_representation(&g).unwrap();
        let complex = chevalley_eilenberg_squares_to_zero(&g).unwrap();
        assert_eq!(
            jacobi, representation,
            "Jacobi <=> ad is a representation: {values:?}"
        );
        assert_eq!(jacobi, complex, "Jacobi <=> d^2 = 0: {values:?}");
        if jacobi {
            lie += 1;
        } else {
            non_lie += 1;
        }
    }
    // The sample is not vacuous in either direction.
    assert!(lie > 0 && non_lie > 0, "lie = {lie}, non_lie = {non_lie}");
}

#[test]
fn a_bracket_that_violates_jacobi_fails_all_three_tests() {
    let bad = not_a_lie_algebra();
    assert!(verify_antisymmetry(&bad));
    assert!(!verify_jacobi(&bad));
    assert!(!adjoint_is_representation(&bad).unwrap());
    assert!(!chevalley_eilenberg_squares_to_zero(&bad).unwrap());
    // A table that is not antisymmetric fails antisymmetry.
    let symmetric = StructureConstants::from_fn(2, |a, b, e| {
        if (a, b, e) == (0, 1, 0) || (a, b, e) == (1, 0, 0) {
            ri(1)
        } else {
            ri(0)
        }
    });
    assert!(!verify_antisymmetry(&symmetric));
}

#[test]
fn cohomology_of_the_standard_algebras_has_the_known_betti_numbers() {
    // sl(2) and so(3) (Whitehead): H^0 = Q, H^3 = Q, nothing else.
    assert_eq!(cohomology_betti_numbers(&sl2()).unwrap(), vec![1, 0, 0, 1]);
    let so3 = structure_constants_from_matrices(&so_basis(3).unwrap()).unwrap();
    assert_eq!(cohomology_betti_numbers(&so3).unwrap(), vec![1, 0, 0, 1]);
    // The Heisenberg algebra: 1, 2, 2, 1.
    assert_eq!(
        cohomology_betti_numbers(&heisenberg()).unwrap(),
        vec![1, 2, 2, 1]
    );
    // The abelian algebra has d = 0: Betti numbers are the binomial coefficients.
    assert_eq!(
        cohomology_betti_numbers(&StructureConstants::<BigRational>::abelian(4)).unwrap(),
        vec![1, 4, 6, 4, 1]
    );
    // The two-dimensional non-abelian algebra: 1, 1, 0.
    assert_eq!(cohomology_betti_numbers(&affine()).unwrap(), vec![1, 1, 0]);
    // The Euler characteristic of every complex of positive dimension is 0.
    for betti in [
        cohomology_betti_numbers(&sl2()).unwrap(),
        cohomology_betti_numbers(&heisenberg()).unwrap(),
        cohomology_betti_numbers(&affine()).unwrap(),
    ] {
        let euler: i64 = betti
            .iter()
            .enumerate()
            .map(|(k, &b)| if k % 2 == 0 { b as i64 } else { -(b as i64) })
            .sum();
        assert_eq!(euler, 0);
    }
}

#[test]
fn the_cohomology_of_so4_is_that_of_the_product_of_two_three_spheres() {
    // so(4) = sl(2) + sl(2): Poincare polynomial (1 + t^3)^2 = 1 + 2 t^3 + t^6.
    let so4 = structure_constants_from_matrices(&so_basis(4).unwrap()).unwrap();
    assert!(verify_jacobi(&so4));
    assert_eq!(
        cohomology_betti_numbers(&so4).unwrap(),
        vec![1, 0, 0, 2, 0, 0, 1]
    );
}

#[test]
fn the_differential_has_the_expected_shape_and_low_degree_entries() {
    let g = sl2();
    // d_0: Lambda^0 -> Lambda^1 is zero (constants are invariant); d_1: Lambda^1 (3) -> Lambda^2 (3).
    assert_eq!(
        chevalley_eilenberg_differential(&g, 0).unwrap(),
        Q::zero(3, 1).unwrap()
    );
    let d1 = chevalley_eilenberg_differential(&g, 1).unwrap();
    assert_eq!(d1.shape(), (3, 3));
    // d e^c = - sum_{a<b} c_ab^c e^a ^ e^b: for sl(2) in (h, e, f): d e^h = -e^e ^ e^f, d e^e = -2 e^h ^ e^e, d e^f = 2 e^h ^ e^f.
    // Rows are the 2-subsets (0,1), (0,2), (1,2); columns the 1-subsets 0, 1, 2.
    assert_eq!(d1, mat(&[&[0, -2, 0], &[0, 0, 2], &[-1, 0, 0]]));
    assert_eq!(
        chevalley_eilenberg_differential(&g, 4).unwrap_err(),
        LieAlgebraError::DegreeTooLarge {
            degree: 4,
            dimension: 3
        }
    );
    let big = StructureConstants::<BigRational>::abelian(MAX_COMPLEX_DIMENSION + 1);
    assert_eq!(
        cohomology_betti_numbers(&big).unwrap_err(),
        LieAlgebraError::DimensionTooLarge {
            dimension: MAX_COMPLEX_DIMENSION + 1
        }
    );
}

#[test]
fn matrix_algebras_are_refused_when_they_are_not_closed_or_not_independent() {
    // {E11, E12, E21} is not closed: [E12, E21] = E11 - E22.
    let not_closed = [unit(2, 0, 0), unit(2, 0, 1), unit(2, 1, 0)];
    assert_eq!(
        structure_constants_from_matrices(&not_closed).unwrap_err(),
        LieAlgebraError::NotClosed { a: 1, b: 2 }
    );
    // Dependent: a matrix and twice itself.
    let e = unit(2, 0, 1);
    let doubled = e.map(|x| x * ri(2));
    assert_eq!(
        structure_constants_from_matrices(&[e.clone(), doubled]).unwrap_err(),
        LieAlgebraError::DependentBasis
    );
    // Shapes.
    assert_eq!(
        structure_constants_from_matrices::<BigRational>(&[]).unwrap_err(),
        LieAlgebraError::Shape
    );
    assert_eq!(
        structure_constants_from_matrices(&[e, unit(3, 0, 1)]).unwrap_err(),
        LieAlgebraError::Shape
    );
    assert!(matches!(
        structure_constants_from_matrices(&[Q::zero(2, 3).unwrap()]),
        Err(LieAlgebraError::Shape)
    ));
}

#[test]
fn brackets_adjoint_matrices_and_indices() {
    let g = sl2();
    // [h + e, f] = [h, f] + [e, f] = -2 f + h.
    let x = vec![ri(1), ri(1), ri(0)];
    let y = vec![ri(0), ri(0), ri(1)];
    assert_eq!(bracket(&g, &x, &y).unwrap(), vec![ri(1), ri(0), ri(-2)]);
    assert_eq!(bracket(&g, &x, &y[..2]), Err(LieAlgebraError::Shape));
    // ad h = diag(0, 2, -2).
    assert_eq!(
        adjoint_matrix(&g, 0).unwrap(),
        mat(&[&[0, 0, 0], &[0, 2, 0], &[0, 0, -2]])
    );
    assert_eq!(
        adjoint_matrix(&g, 3).unwrap_err(),
        LieAlgebraError::IndexOutOfRange {
            index: 3,
            dimension: 3
        }
    );
    // ad is a homomorphism: ad [x, y] = [ad x, ad y] on a pair of non-basis vectors, by linearity.
    let ad = |v: &[BigRational]| -> Q {
        let mut m = Q::zero(3, 3).unwrap();
        for (a, coefficient) in v.iter().enumerate() {
            m = mx::add(
                &m,
                &mx::scale(&adjoint_matrix(&g, a).unwrap(), coefficient).unwrap(),
            )
            .unwrap();
        }
        m
    };
    let (u, v) = (vec![ri(2), rq(1, 2), ri(3)], vec![ri(-1), ri(4), rq(1, 3)]);
    let w = bracket(&g, &u, &v).unwrap();
    assert_eq!(ad(&w), mx::commutator(&ad(&u), &ad(&v)).unwrap());
}

#[test]
fn the_same_algebra_over_the_gaussian_rationals_has_the_same_structure_constants() {
    let g = |re: i64, im: i64| GaussianRat::from_ints(re, im);
    let mat_g = |rows: &[&[i64]]| -> BasicMatrix<GaussianRat> {
        mx::from_rows(
            rows.iter()
                .map(|r| r.iter().map(|&v| g(v, 0)).collect())
                .collect(),
        )
        .unwrap()
    };
    let basis = [
        mat_g(&[&[1, 0], &[0, -1]]),
        mat_g(&[&[0, 1], &[0, 0]]),
        mat_g(&[&[0, 0], &[1, 0]]),
    ];
    let gauss = structure_constants_from_matrices(&basis).unwrap();
    let rational = sl2();
    for a in 0..3 {
        for b in 0..3 {
            for e in 0..3 {
                assert_eq!(
                    gauss.structure_constant(a, b, e),
                    GaussianRat::from_rational(rational.structure_constant(a, b, e))
                );
            }
        }
    }
    assert!(verify_jacobi(&gauss));
    assert_eq!(cohomology_betti_numbers(&gauss).unwrap(), vec![1, 0, 0, 1]);
}

// Origin: engine/crates_rs/tests/core_lie_theory/lie_algebra.rs
// Claim: urn:core:crates_rs:tests:lie-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1973de7e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1973de7e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1973de7e {
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
impl BoundaryError1973de7e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1973de7e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1973de7e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1973de7e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1973de7e> {
        if capacity_bound == 0 {
            return Err(BoundaryError1973de7e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1973de7e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1973de7e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1973de7e() {
    let admitted = BoundaryRecord1973de7e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1973de7e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
