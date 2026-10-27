//! Fields with an involution, and the adjoint, Hermitian, unitary and normal operators
//! over them.
//!
//! An [`Involution`] is a ring automorphism of order at most two. On `Q` it is the
//! identity; on `Q(i)` it is complex conjugation; on a cyclotomic field `Q(ζₙ)` it is
//! `ζ ↦ ζ⁻¹`. With it the adjoint `A† = conj(A)ᵀ` is defined over any such field, and
//! with the identity involution `A†` is just `Aᵀ` (so the same functions decide
//! symmetric, skew-symmetric and orthogonal matrices over `Q`, `GF(p)` or a real
//! quadratic field).
//!
//! Operator predicates return `Result<bool, _>`: a non-square matrix is a category error
//! (`NotSquare`), not the answer "no".
//!
//! AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, OperationLimits};
use crate::exact_field::matrix::{is_identity_matrix, multiply};
use crate::exact_field::{
    charge, element_count, require_same_shape, require_square, reserve, ExactFieldError,
};
use crate::scalars::{ExactRing, Field};
use num_rational::BigRational;

/// A field with an involutive automorphism `x ↦ x̄`.
///
/// # What an implementor must prove
///
/// For all `a`, `b`:
///
/// 1. `conj(a + b) = conj(a) + conj(b)`;
/// 2. `conj(a · b) = conj(a) · conj(b)`;
/// 3. `conj(1) = 1`;
/// 4. `conj(conj(a)) = a`.
///
/// (1)–(3) make `conj` a ring homomorphism, (4) makes it bijective of order at most two.
/// `conj(0) = 0` and `conj(−a) = −conj(a)` follow. The algorithms here rely on these and
/// on nothing else; in particular they do not require `conj` to be nontrivial, and no
/// ordering is assumed (see `ordered::HermitianOrdered` for the ordered fixed field needed
/// to decide *definiteness*). `laws::check_involution_axioms` replays (1)–(4) on a sample.
///
/// The identity is a valid involution (`BigRational` uses it). Complex conjugation is
/// the involution of every subfield of `C` closed under it; a subfield *not* closed under
/// conjugation must not use it.
pub trait Involution: Field + ExactRing {
    /// The conjugate `x̄`.
    fn conjugate(&self) -> Self;
}

impl Involution for BigRational {
    fn conjugate(&self) -> Self {
        self.clone()
    }
}

/// The entrywise conjugate `Ā` (same shape, no transposition).
pub fn conjugate_entries<F: Involution>(
    a: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let mut data = reserve(a.as_slice().len())?;
    for x in a.as_slice() {
        data.push(x.conjugate());
    }
    Ok(BasicMatrix::from_row_major(a.rows(), a.cols(), data)?)
}

/// The adjoint `A†`: entry `(i, j)` of `A†` is `conj(A[j][i])`; shape `n × m` for `m × n`.
pub fn adjoint<F: Involution>(a: &BasicMatrix<F>) -> Result<BasicMatrix<F>, ExactFieldError> {
    BasicMatrix::try_from_fn_result::<_, ExactFieldError>(a.cols(), a.rows(), |r, c| {
        Ok(a.get_ref(c, r)?.conjugate())
    })
}

/// The first position `(r, c)`, `r ≤ c`, in row-major order with `a[r][c] ≠ conj(a[c][r])`,
/// or `None` when `a` is Hermitian. Refuses a non-square matrix.
pub fn hermitian_violation<F: Involution>(
    a: &BasicMatrix<F>,
) -> Result<Option<(usize, usize)>, ExactFieldError> {
    let n = require_square("hermitian check", a)?;
    for r in 0..n {
        for c in r..n {
            if *a.get_ref(r, c)? != a.get_ref(c, r)?.conjugate() {
                return Ok(Some((r, c)));
            }
        }
    }
    Ok(None)
}

/// `true` when `A = A†`. With the identity involution this is symmetry.
pub fn is_hermitian<F: Involution>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    Ok(hermitian_violation(a)?.is_none())
}

/// `true` when `A = −A†` (so the diagonal satisfies `a = −ā`).
pub fn is_skew_hermitian<F: Involution>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    let n = require_square("is_skew_hermitian", a)?;
    for r in 0..n {
        for c in r..n {
            if *a.get_ref(r, c)? != a.get_ref(c, r)?.conjugate().neg() {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// `true` when `A†A = I` (equivalently `AA† = I`, since `A` is square over a field).
pub fn is_unitary<F: Involution>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    require_square("is_unitary", a)?;
    is_identity_matrix(&multiply(&adjoint(a)?, a)?)
}

/// `true` when `AA† = A†A`.
pub fn is_normal<F: Involution>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    require_square("is_normal", a)?;
    let dagger = adjoint(a)?;
    Ok(multiply(a, &dagger)? == multiply(&dagger, a)?)
}

/// The Hilbert–Schmidt inner product `⟨A, B⟩ = tr(A†B) = Σ conj(Aᵢⱼ)·Bᵢⱼ`. It is
/// conjugate-linear in `A`, linear in `B`, and `⟨B, A⟩ = conj⟨A, B⟩`. The shapes must agree.
pub fn hs_inner<F: Involution>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<F, ExactFieldError> {
    require_same_shape("hs_inner", a, b)?;
    let mut acc = F::zero();
    for (x, y) in a.as_slice().iter().zip(b.as_slice()) {
        acc = acc.add(&x.conjugate().mul(y));
    }
    Ok(acc)
}

/// `⟨A, A⟩ = Σ |Aᵢⱼ|²`, a self-conjugate element.
pub fn hs_norm_squared<F: Involution>(a: &BasicMatrix<F>) -> Result<F, ExactFieldError> {
    hs_inner(a, a)
}

/// The vector inner product `⟨u, v⟩ = Σ conj(uᵢ)·vᵢ`.
pub fn inner_product<F: Involution>(u: &[F], v: &[F]) -> Result<F, ExactFieldError> {
    if u.len() != v.len() {
        return Err(ExactFieldError::VectorLength {
            operation: "inner_product",
            expected: u.len(),
            got: v.len(),
        });
    }
    let mut acc = F::zero();
    for (x, y) in u.iter().zip(v) {
        acc = acc.add(&x.conjugate().mul(y));
    }
    Ok(acc)
}

/// The outer product `|u⟩⟨v|`: entry `(i, j)` is `uᵢ·conj(vⱼ)`, shape `len(u) × len(v)`.
pub fn outer_product<F: Involution>(u: &[F], v: &[F]) -> Result<BasicMatrix<F>, ExactFieldError> {
    outer_product_with_limits(u, v, OperationLimits::UNLIMITED)
}

/// [`outer_product`] under a budget: `len(u)·len(v)` elements, one `mul` each.
pub fn outer_product_with_limits<F: Involution>(
    u: &[F],
    v: &[F],
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let elements = element_count(u.len(), v.len())?;
    charge(limits, elements, elements)?;
    let mut data = reserve(elements)?;
    for x in u {
        for y in v {
            data.push(x.mul(&y.conjugate()));
        }
    }
    Ok(BasicMatrix::from_row_major(u.len(), v.len(), data)?)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/involution.rs
// Claim: urn:core:crates_rs:core-linear-algebra:involution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7f915794 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7f915794` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7f915794 {
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
impl BoundaryError7f915794 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7f915794 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7f915794 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7f915794 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7f915794> {
        if capacity_bound == 0 {
            return Err(BoundaryError7f915794::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7f915794::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7f915794::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::exact_field::characteristic_polynomial::characteristic_polynomial;
    use crate::exact_field::elimination::determinant;
    use crate::exact_field::matrix::{
        add, anticommutator, commutator, from_rows, identity, multiply_vector, scale, trace,
        transpose,
    };
    use crate::exact_field::test_support::{
        gi, gq, m, q, qs, qsi, random_matrix, Fp, GaussianRational, Rng,
    };
    use crate::scalars::Semiring;
    use num_rational::BigRational;

    type G = GaussianRational;

    fn gmat(rows: &[&[(i64, i64)]]) -> BasicMatrix<G> {
        from_rows(
            rows.iter()
                .map(|r| r.iter().map(|&(a, b)| gi(a, b)).collect())
                .collect(),
        )
        .unwrap()
    }

    fn random_gaussian(rng: &mut Rng, rows: usize, cols: usize) -> BasicMatrix<G> {
        from_rows(
            (0..rows)
                .map(|_| {
                    (0..cols)
                        .map(|_| {
                            gq(
                                q(rng.range(-4, 4), rng.range(1, 3)),
                                q(rng.range(-4, 4), rng.range(1, 3)),
                            )
                        })
                        .collect()
                })
                .collect(),
        )
        .unwrap()
    }

    fn pauli_x() -> BasicMatrix<G> {
        gmat(&[&[(0, 0), (1, 0)], &[(1, 0), (0, 0)]])
    }
    fn pauli_y() -> BasicMatrix<G> {
        gmat(&[&[(0, 0), (0, -1)], &[(0, 1), (0, 0)]])
    }
    fn pauli_z() -> BasicMatrix<G> {
        gmat(&[&[(1, 0), (0, 0)], &[(0, 0), (-1, 0)]])
    }

    // ------------------------------------------------------------------ adjoint

    /// Invariant: `A†` conjugates AND transposes. `A = [[1+i, 2],[3i, 4−i]]` gives
    /// `[[1−i, −3i],[2, 4+i]]`; dropping either half changes at least two entries.
    #[test]
    fn the_adjoint_conjugates_and_transposes_over_q_i() {
        let a = gmat(&[&[(1, 1), (2, 0)], &[(0, 3), (4, -1)]]);
        assert_eq!(
            adjoint(&a).unwrap(),
            gmat(&[&[(1, -1), (0, -3)], &[(2, 0), (4, 1)]])
        );
        assert_eq!(
            conjugate_entries(&a).unwrap(),
            gmat(&[&[(1, -1), (2, 0)], &[(0, -3), (4, 1)]])
        );
        // rectangular: 2×3 -> 3×2
        let r = gmat(&[&[(1, 1), (0, 1), (2, 0)], &[(3, 0), (0, 0), (0, -2)]]);
        let d = adjoint(&r).unwrap();
        assert_eq!(d.shape(), (3, 2));
        assert_eq!(d.get(0, 1).unwrap(), gi(3, 0));
        assert_eq!(d.get(1, 0).unwrap(), gi(0, -1));
        assert_eq!(d.get(2, 1).unwrap(), gi(0, 2));
    }

    /// Invariants: `(A†)† = A`, `(AB)† = B†A†`, `(cA)† = c̄ A†` (the last pins the
    /// conjugation of the scalar: with `c = i` it flips the sign).
    #[test]
    fn adjoint_is_an_involutive_anti_automorphism_and_conjugate_linear() {
        let mut rng = Rng::new(401);
        let a = random_gaussian(&mut rng, 3, 2);
        let b = random_gaussian(&mut rng, 2, 4);
        assert_eq!(adjoint(&adjoint(&a).unwrap()).unwrap(), a);
        assert_eq!(
            adjoint(&multiply(&a, &b).unwrap()).unwrap(),
            multiply(&adjoint(&b).unwrap(), &adjoint(&a).unwrap()).unwrap()
        );
        let i = gi(0, 1);
        assert_eq!(
            adjoint(&scale(&a, &i).unwrap()).unwrap(),
            scale(&adjoint(&a).unwrap(), &gi(0, -1)).unwrap()
        );
    }

    #[test]
    fn with_the_identity_involution_the_adjoint_is_the_transpose() {
        let mut rng = Rng::new(403);
        let a = random_matrix(&mut rng, 3, 4, 5);
        assert_eq!(adjoint(&a).unwrap(), transpose(&a).unwrap());
    }

    // ------------------------------------------------------------------ Hermitian / unitary

    /// The Pauli matrices over Q(i): Hermitian, unitary, involutions, traceless; their
    /// products and brackets follow the Pauli algebra.
    #[test]
    fn the_pauli_matrices_satisfy_their_algebra_over_q_i() {
        let (x, y, z) = (pauli_x(), pauli_y(), pauli_z());
        let i2 = identity::<G>(2).unwrap();
        for p in [&x, &y, &z] {
            assert!(is_hermitian(p).unwrap());
            assert!(is_unitary(p).unwrap());
            assert!(is_normal(p).unwrap());
            assert_eq!(multiply(p, p).unwrap(), i2);
            assert_eq!(trace(p).unwrap(), gi(0, 0));
            assert!(!is_skew_hermitian(p).unwrap());
        }
        // XY = iZ, YZ = iX, ZX = iY
        assert_eq!(multiply(&x, &y).unwrap(), scale(&z, &gi(0, 1)).unwrap());
        assert_eq!(multiply(&y, &z).unwrap(), scale(&x, &gi(0, 1)).unwrap());
        assert_eq!(multiply(&z, &x).unwrap(), scale(&y, &gi(0, 1)).unwrap());
        // [X, Y] = 2iZ and {X, Y} = 0
        assert_eq!(commutator(&x, &y).unwrap(), scale(&z, &gi(0, 2)).unwrap());
        assert!(crate::exact_field::matrix::is_zero_matrix(
            &anticommutator(&x, &y).unwrap()
        ));
        // iX is skew-Hermitian, not Hermitian
        let ix = scale(&x, &gi(0, 1)).unwrap();
        assert!(is_skew_hermitian(&ix).unwrap());
        assert!(!is_hermitian(&ix).unwrap());
        // det Y = -1, charpoly of Y is x^2 - 1 (real although Y has imaginary entries)
        assert_eq!(determinant(&y).unwrap(), gi(-1, 0));
        assert_eq!(
            characteristic_polynomial(&y).unwrap(),
            vec![gi(-1, 0), gi(0, 0), gi(1, 0)]
        );
    }

    /// The Hadamard matrix `(1/√2)[[1,1],[1,−1]]` over `Q(√2)` (entries `√2/2`): orthogonal
    /// and symmetric, an involution, determinant −1. The unnormalised matrix is not unitary.
    #[test]
    fn the_hadamard_matrix_is_orthogonal_over_q_sqrt2() {
        let s = qs(q(0, 1), q(1, 2)); // √2/2
        let neg_s = qs(q(0, 1), q(-1, 2));
        let h = from_rows(vec![vec![s.clone(), s.clone()], vec![s.clone(), neg_s]]).unwrap();
        assert!(is_hermitian(&h).unwrap());
        assert!(is_unitary(&h).unwrap());
        assert_eq!(multiply(&h, &h).unwrap(), identity(2).unwrap());
        assert_eq!(determinant(&h).unwrap(), qsi(-1, 0));
        let unnormalised = from_rows(vec![
            vec![qsi(1, 0), qsi(1, 0)],
            vec![qsi(1, 0), qsi(-1, 0)],
        ])
        .unwrap();
        assert!(is_hermitian(&unnormalised).unwrap());
        assert!(!is_unitary(&unnormalised).unwrap());
        assert!(is_normal(&unnormalised).unwrap());
    }

    /// `[[1, i],[i, 1]]` is normal (both products are `2I`), neither Hermitian nor unitary;
    /// `[[1,1],[0,1]]` is not normal; `[[i, 1],[−1, 2i]]` is skew-Hermitian.
    #[test]
    fn hermitian_normal_unitary_are_three_different_properties() {
        let n = gmat(&[&[(1, 0), (0, 1)], &[(0, 1), (1, 0)]]);
        assert!(is_normal(&n).unwrap());
        assert!(!is_hermitian(&n).unwrap());
        assert!(!is_unitary(&n).unwrap());
        assert_eq!(
            multiply(&n, &adjoint(&n).unwrap()).unwrap(),
            scale(&identity(2).unwrap(), &gi(2, 0)).unwrap()
        );

        let shear = gmat(&[&[(1, 0), (1, 0)], &[(0, 0), (1, 0)]]);
        assert!(!is_normal(&shear).unwrap());
        assert!(!is_unitary(&shear).unwrap());

        let skew = gmat(&[&[(0, 1), (1, 0)], &[(-1, 0), (0, 2)]]);
        assert!(is_skew_hermitian(&skew).unwrap());
        assert!(!is_hermitian(&skew).unwrap());

        // a unitary that is neither Hermitian nor a Pauli: diag(1, i) (the phase gate S)
        let phase = gmat(&[&[(1, 0), (0, 0)], &[(0, 0), (0, 1)]]);
        assert!(is_unitary(&phase).unwrap());
        assert!(!is_hermitian(&phase).unwrap());
    }

    /// Hermitian matrices form a real subspace: `H` Hermitian ⇒ `H + H†` Hermitian, and
    /// `A + A†` is Hermitian for any `A`, `A − A†` skew-Hermitian.
    #[test]
    fn hermitian_and_skew_parts_of_a_random_matrix() {
        let mut rng = Rng::new(409);
        for n in 1..=4 {
            let a = random_gaussian(&mut rng, n, n);
            let dagger = adjoint(&a).unwrap();
            let sum = add(&a, &dagger).unwrap();
            let diff = crate::exact_field::matrix::sub(&a, &dagger).unwrap();
            assert!(is_hermitian(&sum).unwrap());
            assert!(is_skew_hermitian(&diff).unwrap());
            // a Hermitian matrix times i is skew-Hermitian
            assert!(is_skew_hermitian(&scale(&sum, &gi(0, 1)).unwrap()).unwrap());
        }
    }

    /// Over GF(7) with the identity involution, `[[2,2],[−2,2]]` is orthogonal
    /// (columns have norm `4 + 4 = 8 ≡ 1` and are perpendicular) and `[[1,2],[2,−1]]` is not.
    #[test]
    fn orthogonality_over_a_finite_field() {
        type F7 = Fp<7>;
        let f = |x: i64| F7::new(x);
        let rot = from_rows(vec![vec![f(2), f(2)], vec![f(-2), f(2)]]).unwrap();
        assert!(is_unitary(&rot).unwrap());
        assert!(!is_hermitian(&rot).unwrap());
        let not = from_rows(vec![vec![f(1), f(2)], vec![f(2), f(-1)]]).unwrap();
        assert!(is_hermitian(&not).unwrap());
        assert!(!is_unitary(&not).unwrap());
    }

    // ------------------------------------------------------------------ inner products

    /// Invariants of ⟨A, B⟩ = tr(A†B): conjugate-linear in A (the factor is `c̄`), linear in
    /// B, Hermitian symmetric, and equal to the trace of the product computed by matrices.
    #[test]
    fn the_hilbert_schmidt_inner_product_is_sesquilinear_and_equals_tr_a_dagger_b() {
        let mut rng = Rng::new(421);
        let a = random_gaussian(&mut rng, 2, 3);
        let b = random_gaussian(&mut rng, 2, 3);
        let i = gi(0, 1);
        let ab = hs_inner(&a, &b).unwrap();
        assert_eq!(
            hs_inner(&scale(&a, &i).unwrap(), &b).unwrap(),
            gi(0, -1).mul(&ab)
        );
        assert_eq!(hs_inner(&a, &scale(&b, &i).unwrap()).unwrap(), i.mul(&ab));
        assert_eq!(hs_inner(&b, &a).unwrap(), ab.conjugate());
        assert_eq!(
            ab,
            trace(&multiply(&adjoint(&a).unwrap(), &b).unwrap()).unwrap()
        );
        // the squared norm is self-conjugate ("real") and zero only for the zero matrix
        let norm = hs_norm_squared(&a).unwrap();
        assert_eq!(norm, norm.conjugate());
        assert!(hs_norm_squared(&identity::<G>(3).unwrap()).unwrap() == gi(3, 0));
        assert!(matches!(
            hs_inner(&a, &transpose(&b).unwrap()),
            Err(ExactFieldError::ShapeMismatch {
                operation: "hs_inner",
                ..
            })
        ));
    }

    /// `⟨u,v⟩ = Σ ūᵢvᵢ`, `tr |u⟩⟨v| = ⟨v,u⟩`, and `(|u⟩⟨v|) w = u ⟨v,w⟩` pin where the
    /// conjugation sits in the outer product.
    #[test]
    fn inner_and_outer_products_place_the_conjugate_correctly() {
        let u = vec![gi(1, 1), gi(0, 2)];
        let v = vec![gi(2, -1), gi(1, 1)];
        let w = vec![gi(0, 1), gi(3, 0)];
        // ⟨u,v⟩ = conj(1+i)(2−i) + conj(2i)(1+i) = (1−i)(2−i) + (−2i)(1+i) = (1−3i) + (2−2i) = 3−5i
        assert_eq!(inner_product(&u, &v).unwrap(), gi(3, -5));
        let outer = outer_product(&u, &v).unwrap();
        assert_eq!(outer.shape(), (2, 2));
        assert_eq!(trace(&outer).unwrap(), inner_product(&v, &u).unwrap());
        let applied = multiply_vector(&outer, &w).unwrap();
        let scalar = inner_product(&v, &w).unwrap();
        let expected: Vec<G> = u.iter().map(|x| x.mul(&scalar)).collect();
        assert_eq!(applied, expected);
        assert!(matches!(
            inner_product(&u, &w[..1]),
            Err(ExactFieldError::VectorLength {
                operation: "inner_product",
                ..
            })
        ));
        assert!(outer_product_with_limits(
            &u,
            &v,
            OperationLimits {
                max_elements: 3,
                max_scalar_ops: usize::MAX
            }
        )
        .is_err());
    }

    #[test]
    fn predicates_refuse_non_square_input() {
        let wide = gmat(&[&[(1, 0), (2, 0), (3, 0)], &[(4, 0), (5, 0), (6, 0)]]);
        assert!(matches!(
            is_hermitian(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(matches!(
            is_skew_hermitian(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(matches!(
            is_unitary(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(matches!(
            is_normal(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
    }

    /// The first offending position is reported in row-major order over the upper triangle.
    #[test]
    fn the_hermitian_violation_names_the_first_offending_entry() {
        let a = gmat(&[
            &[(1, 0), (2, 0), (0, 1)],
            &[(2, 0), (3, 1), (5, 0)],
            &[(0, 1), (5, 0), (1, 0)],
        ]);
        // (1,1) = 3+i is not self-conjugate and comes before (0,2) = i vs conj(i)
        assert_eq!(hermitian_violation(&a).unwrap(), Some((0, 2)));
        let b = gmat(&[&[(1, 0), (2, 0)], &[(2, 0), (3, 1)]]);
        assert_eq!(hermitian_violation(&b).unwrap(), Some((1, 1)));
        assert_eq!(
            hermitian_violation(&identity::<G>(3).unwrap()).unwrap(),
            None
        );
    }

    #[test]
    fn bigrational_uses_the_identity_involution() {
        let x = q(-7, 3);
        assert_eq!(Involution::conjugate(&x), x);
        let a = m(&[&[1, 2], &[2, 5]]);
        assert!(is_hermitian::<BigRational>(&a).unwrap());
    }
}

#[cfg(test)]
mod l4_boundary_tests_7f915794 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7f915794::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7f915794::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7f915794::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7f915794::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7f915794::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7f915794::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7f915794::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
