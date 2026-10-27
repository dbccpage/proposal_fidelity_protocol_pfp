//! Finite-dimensional Hilbert carriers `C^n` and their tensor products.
//!
//! A [`HilbertSpace`] is a carrier `C^d` with `d >= 1` and a label; it stores no basis
//! and no inner product beyond the standard one, so everything stated about it is a
//! statement about coordinates in the declared standard basis.
//!
//! [`TensorCarrier`] is a finite multipartite carrier `C^(d_1) (x) ... (x) C^(d_k)`
//! whose basis order is *declared*, not assumed: the lexicographic order, in which the
//! basis vector `|i_1 ... i_k>` has flat index `((i_1 d_2 + i_2) d_3 + i_3) ... + i_k`
//! (the order `linear_algebra::tensor::kronecker_vectors` and `kronecker_matrices`
//! produce). The laws checked by the tests are the ones every exact module relies on:
//!
//! - `dim(H_1 (x) H_2) = d_1 d_2`, with overflow refused
//!   (`linear_algebra::tensor::checked_dim_product`);
//! - `flat_index` and `unflat_index` are mutually inverse bijections between
//!   `{0..d_1} x ... x {0..d_k}` and `{0..d_1 ... d_k}`;
//! - the flat index is associative: grouping the factors `(A B) C` or `A (B C)` gives
//!   the same flat index, so a tripartite carrier cut after factor `c` is the bipartite
//!   carrier of [`TensorCarrier::bipartition`], with the index order of
//!   `linear_algebra::tensor::FiniteTensorSpace`.
//!
//! Requests beyond the declared [`OperationLimits`] (`qubits(11)` needs `2^11 > 1024`
//! amplitudes) and products that do not fit in `usize` (`qubits(64)`) are typed
//! refusals, never a shift overflow and never an allocation.
//!
//! AuthorityEffect: None.

use linear_algebra::tensor::tensor::{checked_dim_product, FiniteTensorSpace, TensorError};

use core_kernel::resource_limits::{OperationLimits, ResourceError};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite Hilbert carrier face.";

/// Refusals of the carrier constructors and index maps.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum HilbertError {
    /// A dimension must be at least 1.
    #[error("a Hilbert carrier has dimension at least 1")]
    ZeroDimension,
    /// A declared ceiling was exceeded, or a product overflowed `usize`.
    #[error("dimension limit: {0}")]
    Limit(ResourceError),
    /// A tensor carrier needs at least one factor.
    #[error("a tensor carrier needs at least one factor")]
    NoFactors,
    /// A multi-index has the wrong number of entries.
    #[error("the multi-index has {actual} entries, the carrier has {expected} factors")]
    FactorCount { expected: usize, actual: usize },
    /// An index lies outside its factor or outside the carrier.
    #[error("index {index} is out of range {bound}")]
    IndexOutOfRange { index: usize, bound: usize },
    /// A bipartition cut must satisfy `1 <= cut < number of factors`.
    #[error("cut {cut} is not between 1 and {factors} - 1")]
    CutOutOfRange { cut: usize, factors: usize },
    /// The tensor algebra of `linear_algebra` refused.
    #[error("tensor algebra refused: {0}")]
    Tensor(TensorError),
}

impl From<ResourceError> for HilbertError {
    fn from(e: ResourceError) -> Self {
        HilbertError::Limit(e)
    }
}

impl From<TensorError> for HilbertError {
    fn from(e: TensorError) -> Self {
        match e {
            TensorError::DimensionOverflow { .. } => {
                HilbertError::Limit(ResourceError::DimensionOverflow)
            }
            other => HilbertError::Tensor(other),
        }
    }
}

/// Finite-dimensional Hilbert carrier `C^n` (`n = dim`) with a label.
///
/// The fields are private: a value always has `dim >= 1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HilbertSpace {
    dim: usize,
    label: String,
}

impl HilbertSpace {
    /// Carrier of dimension `dim >= 1`.
    pub fn try_new(dim: usize, label: impl Into<String>) -> Result<Self, HilbertError> {
        if dim == 0 {
            return Err(HilbertError::ZeroDimension);
        }
        Ok(Self {
            dim,
            label: label.into(),
        })
    }

    /// Carrier of dimension `dim`, refused when it is zero or exceeds
    /// `limits.max_hilbert_dim`.
    pub fn try_new_with_limits(
        dim: usize,
        label: impl Into<String>,
        limits: &OperationLimits,
    ) -> Result<Self, HilbertError> {
        if dim == 0 {
            return Err(HilbertError::ZeroDimension);
        }
        limits.check_hilbert_dim(dim)?;
        Self::try_new(dim, label)
    }

    /// Superseded by [`HilbertSpace::try_new`], and kept only because
    /// `engine_bridge` and `tests/engine_bridge_tests.rs` still call it: it maps the
    /// dimension `0`, which has no carrier, to the dimension `1`, a silently wrong
    /// answer. New code must use `try_new`.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            dim: degree.max(1),
            label: label.into(),
        }
    }

    /// Dimension `n` of `C^n`.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// The label.
    pub fn label(&self) -> &str {
        &self.label
    }

    /// The single-qubit carrier `C^2`.
    pub fn qubit() -> Self {
        Self {
            dim: 2,
            label: "qubit".into(),
        }
    }

    /// The single-qutrit carrier `C^3`.
    pub fn qutrit() -> Self {
        Self {
            dim: 3,
            label: "qutrit".into(),
        }
    }

    /// The `n`-qubit carrier `C^(2^n)` under the default [`OperationLimits`].
    pub fn qubits(n: usize) -> Result<Self, HilbertError> {
        Self::qubits_with_limits(n, &OperationLimits::default())
    }

    /// The `n`-qubit carrier `C^(2^n)`. `n = 0` is the one-dimensional carrier `C`.
    /// A power that does not fit in `usize` is [`ResourceError::DimensionOverflow`];
    /// one beyond `limits.max_hilbert_dim` is `HilbertDimensionExceeded`.
    pub fn qubits_with_limits(n: usize, limits: &OperationLimits) -> Result<Self, HilbertError> {
        let exponent = u32::try_from(n).map_err(|_| ResourceError::DimensionOverflow)?;
        let dim = 2usize
            .checked_pow(exponent)
            .ok_or(ResourceError::DimensionOverflow)?;
        limits.check_hilbert_dim(dim)?;
        Self::try_new(dim, format!("{n}_qubits"))
    }

    /// `H_1 (x) H_2`, of dimension `d_1 d_2` (overflow is refused).
    pub fn tensor_product(&self, other: &Self) -> Result<Self, HilbertError> {
        let dim = checked_dim_product(self.dim, other.dim)?;
        Self::try_new(dim, format!("{}x{}", self.label, other.label))
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// A multipartite carrier `C^(d_1) (x) ... (x) C^(d_k)` in the declared lexicographic
/// basis order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorCarrier {
    factors: Vec<usize>,
    total: usize,
}

impl TensorCarrier {
    /// The carrier with the given factor dimensions under the default limits.
    pub fn new(factors: &[usize]) -> Result<Self, HilbertError> {
        Self::new_with_limits(factors, &OperationLimits::default())
    }

    /// The carrier with the given factor dimensions. Every factor must be at least 1,
    /// the product is computed with overflow checks, and it must not exceed
    /// `limits.max_hilbert_dim`.
    pub fn new_with_limits(
        factors: &[usize],
        limits: &OperationLimits,
    ) -> Result<Self, HilbertError> {
        if factors.is_empty() {
            return Err(HilbertError::NoFactors);
        }
        let mut total = 1usize;
        for &d in factors {
            if d == 0 {
                return Err(HilbertError::ZeroDimension);
            }
            total = checked_dim_product(total, d)?;
        }
        limits.check_hilbert_dim(total)?;
        Ok(Self {
            factors: factors.to_vec(),
            total,
        })
    }

    /// `n >= 1` qubits.
    pub fn qubits(n: usize) -> Result<Self, HilbertError> {
        if n == 0 {
            return Err(HilbertError::NoFactors);
        }
        // Check the power first: `vec![2; n]` must not be built for a huge `n`.
        HilbertSpace::qubits(n)?;
        Self::new(&vec![2; n])
    }

    /// The factor dimensions `d_1, ..., d_k`.
    pub fn factors(&self) -> &[usize] {
        &self.factors
    }

    /// The total dimension `d_1 ... d_k`.
    pub fn total_dim(&self) -> usize {
        self.total
    }

    /// The flat index of `|i_1 ... i_k>`.
    pub fn flat_index(&self, indices: &[usize]) -> Result<usize, HilbertError> {
        if indices.len() != self.factors.len() {
            return Err(HilbertError::FactorCount {
                expected: self.factors.len(),
                actual: indices.len(),
            });
        }
        let mut flat = 0usize;
        for (&i, &d) in indices.iter().zip(&self.factors) {
            if i >= d {
                return Err(HilbertError::IndexOutOfRange { index: i, bound: d });
            }
            // flat < (product of the factors so far) and i < d, so this stays below
            // `total`, which fits in usize by construction.
            flat = flat * d + i;
        }
        Ok(flat)
    }

    /// The multi-index `(i_1, ..., i_k)` of the flat index `k`.
    pub fn unflat_index(&self, k: usize) -> Result<Vec<usize>, HilbertError> {
        if k >= self.total {
            return Err(HilbertError::IndexOutOfRange {
                index: k,
                bound: self.total,
            });
        }
        let mut rest = k;
        let mut out = vec![0usize; self.factors.len()];
        for (slot, &d) in out.iter_mut().zip(&self.factors).rev() {
            *slot = rest % d;
            rest /= d;
        }
        Ok(out)
    }

    /// The bipartite space `(d_1 ... d_cut) (x) (d_(cut+1) ... d_k)` with the index
    /// order of `linear_algebra::tensor::FiniteTensorSpace`.
    pub fn bipartition(&self, cut: usize) -> Result<FiniteTensorSpace, HilbertError> {
        if cut == 0 || cut >= self.factors.len() {
            return Err(HilbertError::CutOutOfRange {
                cut,
                factors: self.factors.len(),
            });
        }
        let left: usize = self.factors[..cut].iter().product();
        let right: usize = self.factors[cut..].iter().product();
        Ok(FiniteTensorSpace::lex(left, right)?)
    }

    /// The carrier as a plain [`HilbertSpace`] of dimension `total_dim()`.
    pub fn as_space(&self, label: impl Into<String>) -> Result<HilbertSpace, HilbertError> {
        HilbertSpace::try_new(self.total, label)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/hilbert_space.rs
// Claim: urn:core:crates_rs:core-quantum-physics:hilbert-space:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_zero_dim() {
        assert_eq!(
            HilbertSpace::try_new(0, "bad"),
            Err(HilbertError::ZeroDimension)
        );
        assert_eq!(
            HilbertSpace::try_new_with_limits(0, "bad", &OperationLimits::default()),
            Err(HilbertError::ZeroDimension)
        );
        assert_eq!(
            TensorCarrier::new(&[2, 0, 3]),
            Err(HilbertError::ZeroDimension)
        );
        assert_eq!(TensorCarrier::new(&[]), Err(HilbertError::NoFactors));
    }

    #[test]
    fn accepts_qubit() {
        let h = HilbertSpace::try_new(2, "qubit").unwrap();
        assert_eq!(h.dim(), 2);
        assert_eq!(h.label(), "qubit");
        assert!(HilbertSpace::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn qubit_tensor_qutrit_has_dimension_six_and_the_declared_index_order() {
        let c = TensorCarrier::new(&[2, 3]).unwrap();
        assert_eq!(c.total_dim(), 6);
        assert_eq!(c.flat_index(&[1, 2]), Ok(5));
        assert_eq!(c.unflat_index(5), Ok(vec![1, 2]));
        let h = HilbertSpace::qubit()
            .tensor_product(&HilbertSpace::qutrit())
            .unwrap();
        assert_eq!(h.dim(), 6);
    }

    #[test]
    fn flat_and_unflat_are_mutually_inverse_on_every_index() {
        let c = TensorCarrier::new(&[2, 3, 4]).unwrap();
        for k in 0..c.total_dim() {
            let multi = c.unflat_index(k).unwrap();
            assert_eq!(c.flat_index(&multi), Ok(k));
        }
        // and the other way round: a bijection, so every multi-index is hit once.
        let mut seen = vec![false; c.total_dim()];
        for a in 0..2 {
            for b in 0..3 {
                for d in 0..4 {
                    let k = c.flat_index(&[a, b, d]).unwrap();
                    assert!(!seen[k]);
                    seen[k] = true;
                }
            }
        }
        assert!(seen.iter().all(|&s| s));
    }

    #[test]
    fn the_flat_index_is_associative_across_a_bipartition() {
        // (A B) C and A (B C) give the same flat index of |a b c>.
        let c = TensorCarrier::new(&[2, 3, 4]).unwrap();
        let ab_c = c.bipartition(2).unwrap();
        let a_bc = c.bipartition(1).unwrap();
        for a in 0..2 {
            for b in 0..3 {
                for d in 0..4 {
                    let k = c.flat_index(&[a, b, d]).unwrap();
                    assert_eq!(ab_c.flat_index(a * 3 + b, d), Ok(k));
                    assert_eq!(a_bc.flat_index(a, b * 4 + d), Ok(k));
                }
            }
        }
        assert!(ab_c.dim_product_law_holds() && a_bc.dim_product_law_holds());
    }

    #[test]
    fn oversized_and_overflowing_requests_are_typed_refusals() {
        assert_eq!(HilbertSpace::qubits(3).unwrap().dim(), 8);
        assert_eq!(HilbertSpace::qubits(10).unwrap().dim(), 1024);
        assert_eq!(
            HilbertSpace::qubits(11),
            Err(HilbertError::Limit(
                ResourceError::HilbertDimensionExceeded {
                    requested: 2048,
                    limit: 1024
                }
            ))
        );
        // 2^64 does not fit in usize: the unchecked shift 1usize << 64 overflowed.
        assert_eq!(
            HilbertSpace::qubits(64),
            Err(HilbertError::Limit(ResourceError::DimensionOverflow))
        );
        assert_eq!(
            HilbertSpace::qubits(usize::MAX),
            Err(HilbertError::Limit(ResourceError::DimensionOverflow))
        );
        let huge = HilbertSpace::try_new(usize::MAX, "huge").unwrap();
        assert_eq!(
            huge.tensor_product(&HilbertSpace::qubit()),
            Err(HilbertError::Limit(ResourceError::DimensionOverflow))
        );
        assert_eq!(
            TensorCarrier::new(&[usize::MAX, 2]),
            Err(HilbertError::Limit(ResourceError::DimensionOverflow))
        );
        assert_eq!(
            TensorCarrier::qubits(11),
            Err(HilbertError::Limit(
                ResourceError::HilbertDimensionExceeded {
                    requested: 2048,
                    limit: 1024
                }
            ))
        );
    }

    #[test]
    fn index_maps_refuse_bad_arguments() {
        let c = TensorCarrier::new(&[2, 3]).unwrap();
        assert_eq!(
            c.flat_index(&[1]),
            Err(HilbertError::FactorCount {
                expected: 2,
                actual: 1
            })
        );
        assert_eq!(
            c.flat_index(&[2, 0]),
            Err(HilbertError::IndexOutOfRange { index: 2, bound: 2 })
        );
        assert_eq!(
            c.unflat_index(6),
            Err(HilbertError::IndexOutOfRange { index: 6, bound: 6 })
        );
        assert!(matches!(
            c.bipartition(0),
            Err(HilbertError::CutOutOfRange { cut: 0, factors: 2 })
        ));
        assert!(matches!(
            c.bipartition(2),
            Err(HilbertError::CutOutOfRange { cut: 2, factors: 2 })
        ));
    }

    #[test]
    fn the_legacy_constructor_still_clamps_and_is_not_the_checked_path() {
        // Documents the superseded behaviour that `try_new` refuses.
        assert_eq!(HilbertSpace::new(0, "legacy").dim(), 1);
    }
}
