//! Exact finite product-formula estimates and declared interaction cones.
//! Matrix estimates compute their commutators. Supplied norm bounds are explicit
//! hypotheses; graph cones with a declared velocity are not Lieb-Robinson estimates.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_homology::directed_multigraph::{DirectedMultigraph, DirectedMultigraphError};
use core_number_theory::cyclotomic::GaussianRat;

/// Imported first-order estimate evaluated without machine-integer narrowing.
pub fn trotter_first_order_error_bound(
    t: &BigRational,
    n: &BigInt,
    comm_norm: &BigRational,
) -> Result<BigRational, ProductFormulaError> {
    if n <= &BigInt::zero() || comm_norm < &BigRational::zero() {
        return Err(ProductFormulaError::Input);
    }
    Ok(t * t * comm_norm / BigRational::from_integer(BigInt::from(2) * n))
}
/// Imported symmetric-splitting estimate; the two nested norms are assumptions.
pub fn trotter_second_order_error_bound(
    t: &BigRational,
    n: &BigInt,
    a: &BigRational,
    b: &BigRational,
) -> Result<BigRational, ProductFormulaError> {
    if n <= &BigInt::zero() || a < &BigRational::zero() || b < &BigRational::zero() {
        return Err(ProductFormulaError::Input);
    }
    let time = t.abs();
    Ok(&time
        * &time
        * &time
        * (a / BigRational::from_integer(24.into()) + b / BigRational::from_integer(12.into()))
        / BigRational::from_integer(n * n))
}
/// Interaction graph distances are computed from the declared undirected bonds.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredInteractionGraph {
    graph: DirectedMultigraph,
}
impl DeclaredInteractionGraph {
    pub fn new(vertices: usize, bonds: &[(usize, usize)]) -> Result<Self, ProductFormulaError> {
        if bonds.len() > 8192 {
            return Err(ProductFormulaError::Input);
        }
        Ok(Self {
            graph: DirectedMultigraph::new(
                vertices,
                bonds.iter().flat_map(|&(u, v)| [(u, v), (v, u)]).collect(),
            )?,
        })
    }
    /// Disconnected sites are outside every finite declared cone. This is a graph
    /// distance predicate, not a bound on evolved commutators or signal amplitudes.
    pub fn outside_cone(
        &self,
        a: usize,
        b: usize,
        t: &BigRational,
        velocity: &BigRational,
    ) -> Result<bool, ProductFormulaError> {
        if velocity < &BigRational::zero() {
            return Err(ProductFormulaError::Input);
        }
        let distances = self.graph.shortest_distances(a)?;
        let distance = distances.get(b).ok_or(ProductFormulaError::Input)?;
        Ok(
            distance
                .is_none_or(|d| BigRational::from_integer(BigInt::from(d)) > velocity * t.abs()),
        )
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/continuous_time_locality_limit.rs
// Claim: urn:core:crates_rs:core-quantum-physics:continuous-time-locality-limit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};
    #[test]
    fn test_trotter_first_order_bound() {
        assert_eq!(
            trotter_first_order_error_bound(&rq(1, 2), &10.into(), &ri(4)).unwrap(),
            rq(1, 20)
        );
        assert_eq!(
            trotter_first_order_error_bound(&rq(1, 2), &20.into(), &ri(4)).unwrap(),
            rq(1, 40)
        );
    }
    #[test]
    fn test_trotter_second_order_bound() {
        let bound =
            trotter_second_order_error_bound(&rq(1, 2), &10.into(), &ri(4), &ri(4)).unwrap();
        assert_eq!(bound, rq(1, 1600));
        assert_eq!(
            trotter_second_order_error_bound(&rq(-1, 2), &10.into(), &ri(4), &ri(4)).unwrap(),
            bound
        );
        assert_eq!(
            trotter_second_order_error_bound(&rq(1, 2), &20.into(), &ri(4), &ri(4)).unwrap(),
            rq(1, 6400)
        );
    }
    #[test]
    fn negative_norm_is_rejected() {
        assert!(trotter_first_order_error_bound(&ri(1), &10.into(), &ri(-1)).is_err());
    }
    #[test]
    fn intermediate_products_do_not_overflow_i64() {
        let large = BigRational::from_integer(i64::MAX.into());
        assert_eq!(
            trotter_first_order_error_bound(&large, &1.into(), &ri(2)).unwrap(),
            &large * &large
        );
        assert!(trotter_first_order_error_bound(&large, &0.into(), &ri(2)).is_err());
    }
}

/// Bounds derived from the supplied finite Hermitian matrices. The operator
/// norm is bounded by the exact entrywise absolute-value norm; no norm is
/// declared by the caller. Product formula bounds concern exp(-i t H).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductFormulaCertificate {
    pub commutator_bound: BigRational,
    pub a_double_commutator_bound: BigRational,
    pub b_double_commutator_bound: BigRational,
    pub first_order_error: BigRational,
    pub second_order_error: BigRational,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ProductFormulaError {
    #[error("positive steps and equal Hermitian dimensions at most 64 are required")]
    Input,
    #[error(transparent)]
    Operator(#[from] crate::exact_hermitian::ExactHermitianError),
    #[error(transparent)]
    Graph(#[from] DirectedMultigraphError),
}
pub fn product_formula_bounds(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
    time: &BigRational,
    steps: usize,
) -> Result<ProductFormulaCertificate, ProductFormulaError> {
    use num_traits::Zero;
    crate::exact_hermitian::check_hermitian(a)?;
    crate::exact_hermitian::check_hermitian(b)?;
    if steps == 0 || a.rows() != b.rows() || a.rows() > 64 {
        return Err(ProductFormulaError::Input);
    }
    let comm = |x: &BasicMatrix<GaussianRat>, y: &BasicMatrix<GaussianRat>| {
        linear_algebra::exact_field::matrix::sub(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(x),
                y,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .expect("validated finite matrix shape and budget")),
            &linear_algebra::exact_field::matrix::multiply_with_limits(
                &(y),
                x,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .expect("validated finite matrix shape and budget"),
        )
        .expect("validated finite matrix shape and budget")
    };
    let norm = |x: &BasicMatrix<GaussianRat>| {
        x.as_slice()
            .iter()
            .fold(BigRational::zero(), |v, z| v + z.re.abs() + z.im.abs())
    };
    let c = comm(a, b);
    let ca = comm(a, &c);
    let cb = comm(b, &c);
    let commutator_bound = norm(&c);
    let a_double_commutator_bound = norm(&ca);
    let b_double_commutator_bound = norm(&cb);
    let t = time.abs();
    let n = BigRational::from_integer(BigInt::from(steps));
    let first_order_error =
        &t * &t * &commutator_bound / (BigRational::from_integer(2.into()) * &n);
    let second_order_error = &t
        * &t
        * &t
        * (&a_double_commutator_bound / BigRational::from_integer(24.into())
            + &b_double_commutator_bound / BigRational::from_integer(12.into()))
        / (&n * &n);
    Ok(ProductFormulaCertificate {
        commutator_bound,
        a_double_commutator_bound,
        b_double_commutator_bound,
        first_order_error,
        second_order_error,
    })
}
