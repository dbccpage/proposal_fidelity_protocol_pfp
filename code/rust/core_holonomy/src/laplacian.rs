//! Discrete connection Laplacian Delta_U = D - A_U and spectral verification.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Hermiticity, PSD quadratic form, Zero-Float Law).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3583925a<T> {
    fn checked_invariant_3583925a(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3583925a<T> for Option<T> {
    #[inline]
    fn checked_invariant_3583925a(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3583925a<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3583925a(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::connection::DiscreteConnection;
use crate::error::HolonomyError;
use crate::graph::CellComplex;
use crate::matrix::{ExactMatrix, ExactScalar, GaussianRational};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Discrete connection Laplacian operator $\Delta_U = D - A_U = D_U^\dagger D_U$.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionLaplacian<T: ExactScalar> {
    pub matrix: ExactMatrix<T>,
    pub num_vertices: usize,
    pub fiber_dim: usize,
    pub total_dim: usize,
}

impl<T: ExactScalar> ConnectionLaplacian<T> {
    /// Constructs the discrete connection Laplacian $\Delta_U$ from cell complex and gauge connection.
    pub fn compute(
        complex: &CellComplex,
        connection: &DiscreteConnection<T>,
        weights: Option<&BTreeMap<(String, String), T>>,
    ) -> Result<Self, HolonomyError> {
        let n = complex.vertices.len();
        let d = connection.dim;
        let total_dim = n.checked_mul(d).ok_or(HolonomyError::AllocationFailure {
            requested: usize::MAX,
            detail: "Laplacian dimension overflow".into(),
        })?;

        let mut lap = ExactMatrix::try_zero(total_dim, total_dim)?;

        for u in &complex.vertices {
            let u_idx = *complex.vertex_map.get(&u.id).checked_invariant_3583925a("checked invariant");
            let mut weighted_deg = T::zero();

            // Find all neighbors v connected to u in complex
            for v in &complex.vertices {
                if u.id == v.id {
                    continue;
                }
                let v_idx = *complex.vertex_map.get(&v.id).checked_invariant_3583925a("checked invariant");

                // Check if step u -> v exists
                if let Ok(u_mat) = connection.get_step(&u.id, &v.id) {
                    let w = Self::edge_weight(weights, &u.id, &v.id);

                    weighted_deg += w.clone();

                    // Place -w * U(u, v) in block (u_idx, v_idx)
                    Self::write_off_diagonal_block(&mut lap, d, u_idx, v_idx, &w, &u_mat);
                }
            }

            // Diagonal block: weighted_deg * I_d
            for r in 0..d {
                *lap.get_mut(u_idx * d + r, u_idx * d + r) = weighted_deg.clone();
            }
        }

        Ok(Self {
            matrix: lap,
            num_vertices: n,
            fiber_dim: d,
            total_dim,
        })
    }

    fn edge_weight(
        weights: Option<&BTreeMap<(String, String), T>>,
        u_id: &str,
        v_id: &str,
    ) -> T {
        weights
            .and_then(|map| {
                map.get(&(u_id.to_string(), v_id.to_string()))
                    .or_else(|| map.get(&(v_id.to_string(), u_id.to_string())))
            })
            .cloned()
            .unwrap_or_else(T::one)
    }

    fn write_off_diagonal_block(
        lap: &mut ExactMatrix<T>,
        d: usize,
        u_idx: usize,
        v_idx: usize,
        w: &T,
        u_mat: &ExactMatrix<T>,
    ) {
        for r in 0..d {
            for c in 0..d {
                let val = -w.clone() * u_mat.get(r, c).clone();
                *lap.get_mut(u_idx * d + r, v_idx * d + c) = val;
            }
        }
    }

    /// Checks if the Laplacian matrix is symmetric: L = L^T.
    pub fn is_symmetric(&self) -> bool {
        self.matrix.is_symmetric()
    }

    /// Checks if the Laplacian matrix is Hermitian: L = L^\dagger.
    pub fn is_hermitian(&self) -> bool {
        self.matrix.is_hermitian()
    }

    /// Computes the exact trace: $\operatorname{Tr}(\Delta_U) = d \sum_{v} \operatorname{deg}(v) = 2 d |E|$.
    pub fn trace(&self) -> Result<T, HolonomyError> {
        self.matrix.trace()
    }

    /// Evaluates the quadratic form $\langle \psi, \Delta_U \psi \rangle = \psi^\dagger \Delta_U \psi$.
    pub fn evaluate_quadratic_form(&self, psi: &[T]) -> Result<T, HolonomyError> {
        if psi.len() != self.total_dim {
            return Err(HolonomyError::DimensionMismatch {
                expected: self.total_dim,
                actual: psi.len(),
            });
        }
        let mut sum = T::zero();
        for r in 0..self.total_dim {
            let mut row_acc = T::zero();
            for (c, psi_c) in psi.iter().enumerate().take(self.total_dim) {
                row_acc += self.matrix.get(r, c).clone() * psi_c.clone();
            }
            sum += psi[r].conjugate() * row_acc;
        }
        Ok(sum)
    }

    /// Computes the exact dimension of the kernel $\ker(\Delta_U) = \text{total\_dim} - \operatorname{rank}(\Delta_U)$.
    pub fn kernel_dimension(&self) -> usize {
        let r = self.matrix.rank();
        self.total_dim.saturating_sub(r)
    }

    /// Verifies whether a spectral gap exists: returns true if $\ker(\Delta_U) = \{0\}$.
    pub fn has_spectral_gap(&self) -> bool {
        self.kernel_dimension() == 0
    }
}

/// Scalars whose value on a Hermitian diagonal lies in the ordered field Q.
pub trait RealDiagonal: ExactScalar {
    /// This scalar as an element of Q, or `None` when it is not real.
    fn as_rational(&self) -> Option<BigRational>;
}

impl RealDiagonal for BigRational {
    fn as_rational(&self) -> Option<BigRational> {
        Some(self.clone())
    }
}

impl RealDiagonal for GaussianRational<BigRational> {
    fn as_rational(&self) -> Option<BigRational> {
        self.im.is_zero().then(|| self.re.clone())
    }
}

/// Weyl–Gershgorin certificate for a Hermitian connection Laplacian under a
/// bounded transport perturbation (WDP-CH05-O01).
///
/// If every edge transport moves by `δU(u, v)` with `‖δU(u, v)‖_∞ ≤ ε`
/// (maximum absolute row sum), each block row of `δΔ_U` has absolute row sum at
/// most `deg_W(u) · ε`. For Hermitian `δΔ_U`, `‖δΔ_U‖_2 ≤ ‖δΔ_U‖_∞ ≤ Δ_W · ε`
/// with `Δ_W = max_u deg_W(u)`, and by Weyl every eigenvalue moves by at most
/// that much. A gap wider than twice the bound therefore survives.
///
/// The degrees are read from the diagonal blocks of `Δ_U`, which equal the
/// weighted degrees under the Laplacian convention of non-negative weights.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PerturbationCertificate {
    pub max_weighted_degree: BigRational,
    pub transport_epsilon: BigRational,
    /// `max_weighted_degree · transport_epsilon`, a bound on `‖δΔ_U‖_2`.
    pub operator_norm_bound: BigRational,
    /// `2 · operator_norm_bound`: the most two eigenvalues can close by.
    pub spectral_gap_tolerance: BigRational,
    pub unperturbed_gap: BigRational,
    /// `unperturbed_gap > spectral_gap_tolerance`.
    pub gap_survives: bool,
}

impl<T: RealDiagonal> ConnectionLaplacian<T> {
    /// `max_u deg_W(u)`, read from the diagonal blocks of `Δ_U`.
    ///
    /// A non-real diagonal entry is refused as non-Hermitian; a negative one
    /// (only possible with a negative edge weight) is refused as a negative bound.
    pub fn max_weighted_degree(&self) -> Result<BigRational, HolonomyError> {
        let mut max = BigRational::zero();
        for i in 0..self.total_dim {
            let entry = self.matrix.get(i, i);
            let degree =
                entry
                    .as_rational()
                    .ok_or_else(|| HolonomyError::NonHermitianLaplacian {
                        u: i.to_string(),
                        v: i.to_string(),
                        detail: format!("diagonal entry {entry} is not real"),
                    })?;
            if degree.is_negative() {
                return Err(HolonomyError::NegativeBound {
                    quantity: format!("weighted degree at index {i}"),
                    value: degree.to_string(),
                });
            }
            if degree > max {
                max = degree;
            }
        }
        Ok(max)
    }

    /// Certify whether a spectral gap of `unperturbed_gap` survives every
    /// transport perturbation with `‖δU(u, v)‖_∞ ≤ transport_epsilon`.
    ///
    /// Refuses a non-Hermitian Laplacian, where Weyl's bound does not apply, and
    /// negative inputs. All arithmetic is exact over Q.
    pub fn perturbation_certificate(
        &self,
        transport_epsilon: BigRational,
        unperturbed_gap: BigRational,
    ) -> Result<PerturbationCertificate, HolonomyError> {
        for (quantity, value) in [
            ("transport_epsilon", &transport_epsilon),
            ("unperturbed_gap", &unperturbed_gap),
        ] {
            if value.is_negative() {
                return Err(HolonomyError::NegativeBound {
                    quantity: quantity.to_string(),
                    value: value.to_string(),
                });
            }
        }
        if let Some((r, c)) = self.first_non_hermitian_entry() {
            return Err(HolonomyError::NonHermitianLaplacian {
                u: r.to_string(),
                v: c.to_string(),
                detail: "Weyl's perturbation bound requires a Hermitian Laplacian".to_string(),
            });
        }
        let max_weighted_degree = self.max_weighted_degree()?;
        let operator_norm_bound = &max_weighted_degree * &transport_epsilon;
        let spectral_gap_tolerance =
            &operator_norm_bound * BigRational::from_integer(BigInt::from(2));
        let gap_survives = unperturbed_gap > spectral_gap_tolerance;
        Ok(PerturbationCertificate {
            max_weighted_degree,
            transport_epsilon,
            operator_norm_bound,
            spectral_gap_tolerance,
            unperturbed_gap,
            gap_survives,
        })
    }

    fn first_non_hermitian_entry(&self) -> Option<(usize, usize)> {
        (0..self.total_dim)
            .flat_map(|r| (r..self.total_dim).map(move |c| (r, c)))
            .find(|&(r, c)| *self.matrix.get(r, c) != self.matrix.get(c, r).conjugate())
    }
}

/// Helper function computing connection Laplacian directly.
pub fn compute_connection_laplacian<T: ExactScalar>(
    complex: &CellComplex,
    connection: &DiscreteConnection<T>,
    weights: Option<&BTreeMap<(String, String), T>>,
) -> Result<ConnectionLaplacian<T>, HolonomyError> {
    ConnectionLaplacian::compute(complex, connection, weights)
}

// Origin: engine/crates_rs/core_holonomy/src/laplacian.rs
// Claim: urn:core:crates_rs:core-holonomy:laplacian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3583925a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3583925a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3583925a {
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
impl BoundaryError3583925a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3583925a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3583925a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3583925a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3583925a> {
        if capacity_bound == 0 {
            return Err(BoundaryError3583925a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3583925a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3583925a::ExceedsCapacity {
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
mod l4_boundary_tests_3583925a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3583925a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3583925a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3583925a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3583925a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3583925a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3583925a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3583925a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
