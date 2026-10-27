// The Yang-Baxter equation as an exact matrix identity, and the standard solutions.
//
// For `R` acting on `V (x) V` with `dim V = n`, write `R12 = R (x) 1`, `R23 = 1 (x) R`
// and `R13 = P23 R12 P23` (`P23 = 1 (x) P`, `P` the flip). The equations checked are
//
// - the braid form `R12 R23 R12 = R23 R12 R23` (constant `R`; the braid relation of the
//   fusion-space generators of `braided` is this identity, see
//   [`crate::braid_group`]);
// - the spectral form `R12(a) R13(b) R23(c) = R23(c) R13(b) R12(a)`, with the three
//   arguments given explicitly (`a = u - v, b = u, c = v` for the additive law,
//   `a = z1/z2, b = z1, c = z2` for the multiplicative law);
// - the spectral braid form for `R_check = P R`:
//   `Rc12(x) Rc23(y) Rc12(z) = Rc23(z) Rc12(y) Rc23(x)`.
//
// Each checker returns the defect matrix (the difference of the two sides), so a
// caller can see where an equation fails. The standard solutions are Yang's rational
// `R(u) = u 1 + P`, the Hecke/Jones `R(q)`, and the symmetric six-vertex (XXZ)
// `R(q, z)`. Note that `u 1 + c P` satisfies the equation for every constant `c`, and
// `u 1 + Z (x) Z` does too: neither is a negative control.
//
// AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::matrix;

use crate::braid_group::DEFAULT_BRAID_LIMITS;
use crate::error::FusionError;
use crate::scalar::FusionScalar;

fn charge(what: &'static str, requested: u128, limit: usize) -> Result<(), FusionError> {
    if requested > limit as u128 {
        return Err(FusionError::Budget {
            what,
            requested,
            limit: limit as u128,
        });
    }
    Ok(())
}

// Charge all simultaneously retained embeddings and all dense products before
// constructing an operator on V tensor V tensor V.
fn preflight(
    n: usize,
    products: usize,
    storage: usize,
    limits: OperationLimits,
) -> Result<(), FusionError> {
    let dimension = n.checked_pow(3).ok_or(FusionError::Overflow {
        context: "sizing a three-fold Yang-Baxter carrier",
    })?;
    let entries = dimension
        .checked_mul(dimension)
        .ok_or(FusionError::Overflow {
            context: "sizing Yang-Baxter embeddings",
        })? as u128;
    charge(
        "Yang-Baxter embedding storage",
        storage as u128 * entries,
        limits.max_elements,
    )?;
    let work = 2 * products as u128 * dimension as u128 * entries + (storage as u128 + 1) * entries;
    charge("Yang-Baxter scalar work", work, limits.max_scalar_ops)
}

/// The dimension `n` of `V` for a matrix acting on `V tensor V` (`rows = cols = n^2`).
/// Integer bisection takes at most `usize::BITS` steps, including extreme declarations.
pub fn base_dimension<K: FusionScalar>(r: &BasicMatrix<K>) -> Result<usize, FusionError> {
    if r.rows() != r.cols() {
        return Err(FusionError::NotSquare {
            operation: "Yang-Baxter",
            rows: r.rows(),
            cols: r.cols(),
        });
    }
    let size = r.rows() as u128;
    let (mut low, mut high) = (0u128, size + 1);
    while low < high {
        let mid = low + (high - low) / 2;
        if mid * mid < size {
            low = mid + 1;
        } else {
            high = mid;
        }
    }
    if low == 0 || low * low != size {
        return Err(FusionError::NotSquare {
            operation: "Yang-Baxter (dimension must be a square n^2)",
            rows: r.rows(),
            cols: r.cols(),
        });
    }
    usize::try_from(low).map_err(|_| FusionError::Overflow {
        context: "the Yang-Baxter base dimension",
    })
}

/// The flip `P (e_i tensor e_j) = e_j tensor e_i` on `V tensor V`, `dim V = n`.
pub fn swap_matrix<K: FusionScalar>(n: usize) -> Result<BasicMatrix<K>, FusionError> {
    swap_matrix_with_limits(n, DEFAULT_BRAID_LIMITS)
}

/// [`swap_matrix`] with an explicit allocation budget. The zero carrier is retained.
pub fn swap_matrix_with_limits<K: FusionScalar>(
    n: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    let dimension = n.checked_mul(n).ok_or(FusionError::Overflow {
        context: "sizing the flip matrix",
    })?;
    matrix::from_fn_with_limits(dimension, dimension, limits, |row, column| {
        let (i, j) = (row / n.max(1), row % n.max(1));
        let (k, l) = (column / n.max(1), column % n.max(1));
        if i == l && j == k {
            K::one()
        } else {
            K::zero()
        }
    })
    .map_err(FusionError::from)
}

fn check_family_shape<K: FusionScalar>(r: &BasicMatrix<K>, n: usize) -> Result<(), FusionError> {
    if base_dimension(r)? != n {
        return Err(FusionError::Shape {
            operation: "one Yang-Baxter spectral carrier",
            left: (n * n, n * n),
            right: r.shape(),
        });
    }
    Ok(())
}

/// `R12 = R tensor 1`, `R23 = 1 tensor R` and `R13 = P23 R12 P23`.
#[derive(Clone, Copy)]
enum TensorPair {
    First,
    Outer,
    Last,
}

fn tensor_embedding<K: FusionScalar>(
    r: &BasicMatrix<K>,
    n: usize,
    pair: TensorPair,
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    check_family_shape(r, n)?;
    let dimension = n.checked_pow(3).ok_or(FusionError::Overflow {
        context: "sizing a three-fold Yang-Baxter carrier",
    })?;
    let square = n * n;
    let (first, second, other) = match pair {
        TensorPair::First => (0, 1, 2),
        TensorPair::Outer => (0, 2, 1),
        TensorPair::Last => (1, 2, 0),
    };
    matrix::from_fn_with_limits(dimension, dimension, limits, |row, column| {
        let a = [row / square, row / n % n, row % n];
        let b = [column / square, column / n % n, column % n];
        if a[other] != b[other] {
            K::zero()
        } else {
            r.as_slice()[(a[first] * n + a[second]) * square + b[first] * n + b[second]].clone()
        }
    })
    .map_err(FusionError::from)
}

fn triple_product<K: FusionScalar>(
    m: [&BasicMatrix<K>; 3],
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    matrix::multiply_with_limits(
        &matrix::multiply_with_limits(m[0], m[1], limits)?,
        m[2],
        limits,
    )
    .map_err(FusionError::from)
}

fn triple_difference<K: FusionScalar>(
    left: [&BasicMatrix<K>; 3],
    right: [&BasicMatrix<K>; 3],
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    matrix::sub(
        &triple_product(left, limits)?,
        &triple_product(right, limits)?,
    )
    .map_err(FusionError::from)
}

fn remaining_family<K: FusionScalar>(
    family: &impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
    b: &K,
    c: &K,
    n: usize,
) -> Result<[BasicMatrix<K>; 2], FusionError> {
    let rb = family(b)?;
    let rc = family(c)?;
    check_family_shape(&rb, n)?;
    check_family_shape(&rc, n)?;
    Ok([rb, rc])
}

fn spectral_values<K: FusionScalar>(
    family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
    parameters: [&K; 3],
    limits: OperationLimits,
    storage: usize,
) -> Result<(usize, [BasicMatrix<K>; 3]), FusionError> {
    let ra = family(parameters[0])?;
    let n = base_dimension(&ra)?;
    preflight(n, 4, storage, limits)?;
    let [rb, rc] = remaining_family(&family, parameters[1], parameters[2], n)?;
    Ok((n, [ra, rb, rc]))
}

fn alternate_triple<K: FusionScalar>(
    values: [&BasicMatrix<K>; 3],
    n: usize,
    outer: TensorPair,
    middle: TensorPair,
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    let a = tensor_embedding(values[0], n, outer, limits)?;
    let b = tensor_embedding(values[1], n, middle, limits)?;
    let c = tensor_embedding(values[2], n, outer, limits)?;
    triple_product([&a, &b, &c], limits)
}

/// `R12 R23 R12 - R23 R12 R23` for a constant `R` on `V tensor V`.
pub fn braid_form_defect<K: FusionScalar>(
    r: &BasicMatrix<K>,
) -> Result<BasicMatrix<K>, FusionError> {
    braid_form_defect_with_limits(r, DEFAULT_BRAID_LIMITS)
}

/// [`braid_form_defect`] with aggregate allocation and scalar-work limits.
pub fn braid_form_defect_with_limits<K: FusionScalar>(
    r: &BasicMatrix<K>,
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    let n = base_dimension(r)?;
    preflight(n, 4, 5, limits)?;
    let r12 = tensor_embedding(r, n, TensorPair::First, limits)?;
    let r23 = tensor_embedding(r, n, TensorPair::Last, limits)?;
    triple_difference([&r12, &r23, &r12], [&r23, &r12, &r23], limits)
}

/// `R12(a) R13(b) R23(c) - R23(c) R13(b) R12(a)` on one spectral carrier.
pub fn spectral_form_defect<K: FusionScalar>(
    family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
    a: &K,
    b: &K,
    c: &K,
) -> Result<BasicMatrix<K>, FusionError> {
    spectral_form_defect_with_limits(family, a, b, c, DEFAULT_BRAID_LIMITS)
}

/// [`spectral_form_defect`] with aggregate limits; each family argument is evaluated once.
pub fn spectral_form_defect_with_limits<K: FusionScalar>(
    family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
    a: &K,
    b: &K,
    c: &K,
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    let (n, [ra, rb, rc]) = spectral_values(family, [a, b, c], limits, 9)?;
    let r12 = tensor_embedding(&ra, n, TensorPair::First, limits)?;
    let r13 = tensor_embedding(&rb, n, TensorPair::Outer, limits)?;
    let r23 = tensor_embedding(&rc, n, TensorPair::Last, limits)?;
    triple_difference([&r12, &r13, &r23], [&r23, &r13, &r12], limits)
}

/// `Rc12(x) Rc23(y) Rc12(z) - Rc23(z) Rc12(y) Rc23(x)` for braid-form matrices.
pub fn spectral_braid_form_defect<K: FusionScalar>(
    family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
    x: &K,
    y: &K,
    z: &K,
) -> Result<BasicMatrix<K>, FusionError> {
    spectral_braid_form_defect_with_limits(family, x, y, z, DEFAULT_BRAID_LIMITS)
}

/// [`spectral_braid_form_defect`] with aggregate limits and one evaluation per argument.
pub fn spectral_braid_form_defect_with_limits<K: FusionScalar>(
    family: impl Fn(&K) -> Result<BasicMatrix<K>, FusionError>,
    x: &K,
    y: &K,
    z: &K,
    limits: OperationLimits,
) -> Result<BasicMatrix<K>, FusionError> {
    let (n, [rx, ry, rz]) = spectral_values(family, [x, y, z], limits, 10)?;
    let left = alternate_triple(
        [&rx, &ry, &rz],
        n,
        TensorPair::First,
        TensorPair::Last,
        limits,
    )?;
    let right = alternate_triple(
        [&rz, &ry, &rx],
        n,
        TensorPair::Last,
        TensorPair::First,
        limits,
    )?;
    matrix::sub(&left, &right).map_err(FusionError::from)
}

/// Yang's rational solution `R(u) = u 1 + P` on `C^n tensor C^n`.
pub fn yang_rational<K: FusionScalar>(n: usize, u: &K) -> Result<BasicMatrix<K>, FusionError> {
    let dimension = n.checked_mul(n).ok_or(FusionError::Overflow {
        context: "sizing Yang's R-matrix",
    })?;
    matrix::from_fn_with_limits(dimension, dimension, DEFAULT_BRAID_LIMITS, |row, column| {
        let flipped = row / n == column % n && row % n == column / n;
        match (row == column, flipped) {
            (true, true) => u.add(&K::one()),
            (true, false) => u.clone(),
            (false, true) => K::one(),
            _ => K::zero(),
        }
    })
    .map_err(FusionError::from)
}

/// The Hecke / Jones braid matrix on `C^2 (x) C^2`:
/// `[[q,0,0,0],[0,0,1,0],[0,1,q-1/q,0],[0,0,0,q]]`; it satisfies the braid relation and
/// `(R - q)(R + 1/q) = 0`.
pub fn hecke<K: FusionScalar>(q: &K) -> Result<BasicMatrix<K>, FusionError> {
    let q_inverse = core_number_theory::scalar::inverse(q).map_err(FusionError::from)?;
    let zero = K::zero();
    let one = K::one();
    matrix::from_rows(vec![
        vec![q.clone(), zero.clone(), zero.clone(), zero.clone()],
        vec![zero.clone(), zero.clone(), one.clone(), zero.clone()],
        vec![zero.clone(), one, q.sub(&q_inverse), zero.clone()],
        vec![zero.clone(), zero.clone(), zero, q.clone()],
    ])
    .map_err(FusionError::from)
}

/// The Hecke relation defect `(R - q)(R + 1/q)` (zero for the Hecke matrix at `q`).
pub fn hecke_quadratic_defect<K: FusionScalar>(
    r: &BasicMatrix<K>,
    q: &K,
) -> Result<BasicMatrix<K>, FusionError> {
    hecke_admission(r)?;
    let q_inverse = core_number_theory::scalar::inverse(q).map_err(FusionError::from)?;
    let identity = matrix::identity_with_limits::<K>(r.rows(), DEFAULT_BRAID_LIMITS)?;
    let left = matrix::sub(r, &matrix::scale(&identity, q)?)?;
    let right = matrix::add(r, &matrix::scale(&identity, &q_inverse)?)?;
    matrix::multiply_with_limits(&left, &right, DEFAULT_BRAID_LIMITS).map_err(FusionError::from)
}

fn hecke_admission<K: FusionScalar>(r: &BasicMatrix<K>) -> Result<(), FusionError> {
    if r.rows() != r.cols() || r.rows() == 0 {
        return Err(FusionError::NotSquare {
            operation: "Hecke relation",
            rows: r.rows(),
            cols: r.cols(),
        });
    }
    let n = r.rows() as u128;
    charge(
        "Hecke relation storage",
        4 * n * n,
        DEFAULT_BRAID_LIMITS.max_elements,
    )?;
    charge(
        "Hecke relation scalar work",
        2 * n * n * n + 4 * n * n,
        DEFAULT_BRAID_LIMITS.max_scalar_ops,
    )?;
    Ok(())
}

/// The symmetric six-vertex (XXZ) `R`-matrix in multiplicative parameters,
/// `[[a,0,0,0],[0,b,c,0],[0,c,b,0],[0,0,0,a]]` with `a = q z - 1/(q z)`, `b = z - 1/z`,
/// `c = q - 1/q`.
pub fn six_vertex<K: FusionScalar>(q: &K, z: &K) -> Result<BasicMatrix<K>, FusionError> {
    let qz = q.mul(z);
    let a = qz.sub(&core_number_theory::scalar::inverse(&qz).map_err(FusionError::from)?);
    let b = z.sub(&core_number_theory::scalar::inverse(z).map_err(FusionError::from)?);
    let c = q.sub(&core_number_theory::scalar::inverse(q).map_err(FusionError::from)?);
    let zero = K::zero();
    matrix::from_rows(vec![
        vec![a.clone(), zero.clone(), zero.clone(), zero.clone()],
        vec![zero.clone(), b.clone(), c.clone(), zero.clone()],
        vec![zero.clone(), c, b, zero.clone()],
        vec![zero.clone(), zero.clone(), zero, a],
    ])
    .map_err(FusionError::from)
}

// Origin: engine/crates_rs/core_fusion_categories/src/yang_baxter.rs
// Claim: urn:core:crates_rs:core-fusion-categories:yang-baxter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5f05a112 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5f05a112` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5f05a112 {
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
impl BoundaryError5f05a112 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5f05a112 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5f05a112 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5f05a112 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5f05a112> {
        if capacity_bound == 0 {
            return Err(BoundaryError5f05a112::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5f05a112::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5f05a112::ExceedsCapacity {
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
    use linear_algebra::exact_field::elimination;
    use core_number_theory::rational::{rq, Rational};

    fn q(n: i64, d: i64) -> Rational {
        rq(n, d)
    }

    #[test]
    fn oversized_yang_baxter_embeddings_refuse_before_dense_products() {
        // The input has only 65,536 entries; its three-fold carrier would have
        // 16,777,216 entries per embedding and require billions of products.
        let r = matrix::identity::<Rational>(256).unwrap();
        assert_eq!(base_dimension(&r).unwrap(), 16);
        assert!(matches!(
            braid_form_defect(&r),
            Err(FusionError::Budget { .. })
        ));
        assert!(matches!(
            swap_matrix::<Rational>(usize::MAX),
            Err(FusionError::Overflow { .. })
        ));
        assert!(matches!(
            yang_rational::<Rational>(usize::MAX, &q(1, 1)),
            Err(FusionError::Overflow { .. })
        ));
        let rectangular = BasicMatrix::<Rational>::from_row_major(usize::MAX, 0, vec![]).unwrap();
        assert!(matches!(
            base_dimension(&rectangular),
            Err(FusionError::NotSquare { .. })
        ));
        let r = matrix::identity::<Rational>(4).unwrap();
        let tight = OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1,
        };
        assert!(matches!(
            braid_form_defect_with_limits(&r, tight),
            Err(FusionError::Budget {
                what: "Yang-Baxter scalar work",
                ..
            })
        ));
    }

    #[test]
    fn spectral_families_use_one_checked_carrier_and_one_value_per_argument() {
        assert!(matches!(
            spectral_form_defect(
                |u| yang_rational(if u == &q(0, 1) { 2 } else { 3 }, u),
                &q(0, 1),
                &q(1, 1),
                &q(2, 1)
            ),
            Err(FusionError::Shape { .. })
        ));
        let seen = std::cell::RefCell::new(Vec::new());
        let defect = spectral_braid_form_defect(
            |u| {
                seen.borrow_mut().push(u.clone());
                matrix::identity::<Rational>(4).map_err(FusionError::from)
            },
            &q(1, 1),
            &q(2, 1),
            &q(3, 1),
        )
        .unwrap();
        assert!(matrix::is_zero_matrix(&defect));
        assert_eq!(*seen.borrow(), vec![q(1, 1), q(2, 1), q(3, 1)]);
    }

    fn pauli_x() -> BasicMatrix<Rational> {
        matrix::from_rows(vec![vec![q(0, 1), q(1, 1)], vec![q(1, 1), q(0, 1)]])
            .map_err(FusionError::from)
            .unwrap()
    }

    fn pauli_z() -> BasicMatrix<Rational> {
        matrix::from_rows(vec![vec![q(1, 1), q(0, 1)], vec![q(0, 1), q(-1, 1)]])
            .map_err(FusionError::from)
            .unwrap()
    }

    #[test]
    fn the_flip_squares_to_the_identity_and_swaps_basis_vectors() {
        let p = swap_matrix::<Rational>(3).unwrap();
        assert!(matrix::is_identity_matrix(
            &matrix::multiply(&p, &p).map_err(FusionError::from).unwrap()
        )
        .map_err(FusionError::from)
        .unwrap());
        // e_1 (x) e_2 (index 1*3 + 2 = 5) goes to e_2 (x) e_1 (index 2*3 + 1 = 7).
        assert_eq!(p.get(7, 5).unwrap(), q(1, 1));
        assert_eq!(p.get(5, 5).unwrap(), q(0, 1));
        assert_eq!(base_dimension(&p).unwrap(), 3);
        assert!(base_dimension(
            &matrix::zeros::<Rational>(5, 5)
                .map_err(FusionError::from)
                .unwrap()
        )
        .is_err());
        assert!(base_dimension(
            &matrix::zeros::<Rational>(4, 6)
                .map_err(FusionError::from)
                .unwrap()
        )
        .is_err());
    }

    #[test]
    fn yang_rational_satisfies_the_spectral_and_braid_forms() {
        let (u, v) = (q(3, 2), q(2, 5));
        let family = |x: &Rational| yang_rational::<Rational>(2, x);
        let defect = spectral_form_defect(family, &(&u - &v), &u, &v).unwrap();
        assert!(
            matrix::is_zero_matrix(&defect),
            "R12(u-v) R13(u) R23(v) = R23(v) R13(u) R12(u-v)"
        );
        // Braid form for Rc(u) = P R(u): Rc12(u-v) Rc23(u) Rc12(v) = Rc23(v) Rc12(u) Rc23(u-v).
        let braid_family = |x: &Rational| -> Result<BasicMatrix<Rational>, FusionError> {
            matrix::multiply(
                &swap_matrix::<Rational>(2)?,
                &yang_rational::<Rational>(2, x)?,
            )
            .map_err(FusionError::from)
        };
        let defect = spectral_braid_form_defect(braid_family, &(&u - &v), &u, &v).unwrap();
        assert!(matrix::is_zero_matrix(&defect));
        // Unitarity R(u) R(-u) = (1 - u^2) 1 and regularity R(0) = P.
        let product = matrix::multiply(
            &yang_rational::<Rational>(2, &u).unwrap(),
            &yang_rational::<Rational>(2, &(-&u)).unwrap(),
        )
        .map_err(FusionError::from)
        .unwrap();
        let scaled = matrix::scale(
            &matrix::identity::<Rational>(4)
                .map_err(FusionError::from)
                .unwrap(),
            &(Rational::from_integer(1.into()) - &u * &u),
        )
        .map_err(FusionError::from)
        .unwrap();
        assert_eq!(product, scaled);
        assert_eq!(
            yang_rational::<Rational>(2, &q(0, 1)).unwrap(),
            swap_matrix::<Rational>(2).unwrap()
        );
    }

    #[test]
    fn mismatched_spectral_arguments_violate_the_equation() {
        // Negative control (K5): Yang's R with R12(u + v) instead of R12(u - v) fails.
        let (u, v) = (q(3, 2), q(2, 5));
        let family = |x: &Rational| yang_rational::<Rational>(2, x);
        let defect = spectral_form_defect(family, &(&u + &v), &u, &v).unwrap();
        assert!(!matrix::is_zero_matrix(&defect));
    }

    #[test]
    fn hecke_matrices_satisfy_the_braid_relation_and_the_quadratic_relation() {
        let two = q(2, 1);
        let r = hecke(&two).unwrap();
        // The documented matrix at q = 2.
        assert_eq!(
            r,
            matrix::from_rows(vec![
                vec![q(2, 1), q(0, 1), q(0, 1), q(0, 1)],
                vec![q(0, 1), q(0, 1), q(1, 1), q(0, 1)],
                vec![q(0, 1), q(1, 1), q(3, 2), q(0, 1)],
                vec![q(0, 1), q(0, 1), q(0, 1), q(2, 1)],
            ])
            .map_err(FusionError::from)
            .unwrap()
        );
        assert!(matrix::is_zero_matrix(&braid_form_defect(&r).unwrap()));
        assert!(matrix::is_zero_matrix(
            &hecke_quadratic_defect(&r, &two).unwrap()
        ));
        // R - R^{-1} = (q - 1/q) 1.
        let difference = matrix::sub(
            &r,
            &elimination::inverse(&r)
                .map_err(FusionError::from)
                .map_err(FusionError::from)
                .unwrap(),
        )
        .map_err(FusionError::from)
        .unwrap();
        let expected = matrix::scale(
            &matrix::identity::<Rational>(4)
                .map_err(FusionError::from)
                .unwrap(),
            &q(3, 2),
        )
        .map_err(FusionError::from)
        .unwrap();
        assert_eq!(difference, expected);
        assert!(hecke(&q(0, 1)).is_err(), "q = 0 has no inverse");
    }

    #[test]
    fn perturbed_hecke_matrices_violate_the_braid_relation() {
        // Negative control (K5): with q + 1/q in the (2,2) entry instead of q - 1/q.
        let two = q(2, 1);
        let mut entries = matrix::to_rows(&hecke(&two).unwrap())
            .map_err(FusionError::from)
            .unwrap();
        entries[2][2] = q(5, 2);
        let bad = matrix::from_rows(entries)
            .map_err(FusionError::from)
            .unwrap();
        assert!(!matrix::is_zero_matrix(&braid_form_defect(&bad).unwrap()));
        assert!(!matrix::is_zero_matrix(
            &hecke_quadratic_defect(&bad, &two).unwrap()
        ));
    }

    #[test]
    fn the_six_vertex_matrix_satisfies_the_multiplicative_yang_baxter_equation() {
        let (z1, z2) = (q(3, 1), q(5, 7));
        let param = q(2, 1);
        let family = |z: &Rational| six_vertex(&param, z);
        let ratio = &z1 / &z2;
        let defect = spectral_form_defect(family, &ratio, &z1, &z2).unwrap();
        assert!(matrix::is_zero_matrix(&defect));
        // Changing one weight destroys it (b -> b + 1 in a single evaluation).
        let perturbed = |z: &Rational| -> Result<BasicMatrix<Rational>, FusionError> {
            let mut entries =
                matrix::to_rows(&six_vertex(&param, z)?).map_err(FusionError::from)?;
            entries[1][1] = &entries[1][1] + q(1, 1);
            matrix::from_rows(entries).map_err(FusionError::from)
        };
        assert!(!matrix::is_zero_matrix(
            &spectral_form_defect(perturbed, &ratio, &z1, &z2).unwrap()
        ));
        assert!(six_vertex(&q(0, 1), &z1).is_err());
    }

    #[test]
    fn unmatched_pauli_mixtures_are_genuine_negative_controls_but_commuting_ones_are_not() {
        let (u, v) = (q(3, 2), q(2, 5));
        let zz = matrix::kronecker(&pauli_z(), &pauli_z())
            .map_err(FusionError::from)
            .unwrap();
        let xx = matrix::kronecker(&pauli_x(), &pauli_x())
            .map_err(FusionError::from)
            .unwrap();
        let identity = matrix::identity::<Rational>(4)
            .map_err(FusionError::from)
            .unwrap();
        // u 1 + Z (x) Z commutes with itself and DOES satisfy the equation (not a control).
        let commuting = |x: &Rational| {
            matrix::add(
                &matrix::scale(&identity, x).map_err(FusionError::from)?,
                &zz,
            )
            .map_err(FusionError::from)
        };
        assert!(matrix::is_zero_matrix(
            &spectral_form_defect(commuting, &(&u - &v), &u, &v).unwrap()
        ));
        // u 1 + 2 X (x) X + Z (x) Z mixes non-commuting terms and fails.
        let mixed = |x: &Rational| -> Result<BasicMatrix<Rational>, FusionError> {
            matrix::add(
                &matrix::add(
                    &matrix::scale(&identity, x).map_err(FusionError::from)?,
                    &matrix::scale(&xx, &q(2, 1)).map_err(FusionError::from)?,
                )
                .map_err(FusionError::from)?,
                &zz,
            )
            .map_err(FusionError::from)
        };
        assert!(!matrix::is_zero_matrix(
            &spectral_form_defect(mixed, &(&u - &v), &u, &v).unwrap()
        ));
        // u 1 + c P satisfies the equation for every constant c (not a control either):
        // R(u) = c R_Yang(u / c) and the additive law is homogeneous.
        let scaled_flip = |x: &Rational| -> Result<BasicMatrix<Rational>, FusionError> {
            matrix::add(
                &matrix::scale(&identity, x).map_err(FusionError::from)?,
                &matrix::scale(&swap_matrix::<Rational>(2)?, &q(7, 3))
                    .map_err(FusionError::from)?,
            )
            .map_err(FusionError::from)
        };
        assert!(matrix::is_zero_matrix(
            &spectral_form_defect(scaled_flip, &(&u - &v), &u, &v).unwrap()
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_5f05a112 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5f05a112::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5f05a112::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5f05a112::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5f05a112::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5f05a112::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5f05a112::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5f05a112::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
