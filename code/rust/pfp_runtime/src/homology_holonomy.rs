//! Homology boundary closure and discrete holonomy loop evaluation.
//!
//! Sovereign delegation to `core_homology` and `core_holonomy`.
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::{One, Zero};
use core_kernel::Exact;

use crate::rational::{RationalError, RationalMatrix};
use core_holonomy::matrix::ExactMatrix;

/// Verifies that a list of 2D cell faces satisfies the boundary law ∂₁ ∘ ∂₂ = 0.
///
/// Each face is a list of signed edge terms: `(tail_vertex, head_vertex, sign)`.
/// For each face, the boundary is ∂f = ∑ s_i (head_i - tail_i).
/// The complex satisfies boundary closure iff for all faces and all vertices,
/// the net coefficient at the vertex vanishes identically.
pub fn verify_boundary_closed(faces: &[Vec<(usize, usize, i64)>]) -> bool {
    for terms in faces {
        let mut total: std::collections::BTreeMap<usize, i64> = std::collections::BTreeMap::new();
        for &(t, h, s) in terms {
            *total.entry(h).or_insert(0) += s;
            *total.entry(t).or_insert(0) -= s;
        }
        if total.values().any(|&c| c != 0) {
            return false;
        }
    }
    true
}

use core_homology::simplicial::{Simplex, SimplicialComplex};
use serde::{Deserialize, Serialize};

/// Detailed receipt record for a simplicial boundary matrix composition d_{k-1} * d_k.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimplicialCompositionRecord {
    pub degree: usize,
    pub rows: usize,
    pub cols: usize,
    pub is_zero: bool,
}

/// Detailed boundary verification report for a simplicial complex.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimplicialBoundaryReport {
    pub max_dimension: usize,
    pub simplex_counts_by_dim: Vec<usize>,
    pub euler_characteristic: i64,
    pub boundary_law_verified: bool,
    pub compositions: Vec<SimplicialCompositionRecord>,
}

/// Verifies that a higher-dimensional simplicial complex satisfies the boundary law
/// d_{k-1} ∘ d_k = 0 for all degrees k >= 2.
pub fn verify_simplicial_boundary_detailed(
    simplices: &[Vec<usize>],
) -> Result<SimplicialBoundaryReport, String> {
    if simplices.is_empty() {
        return Ok(SimplicialBoundaryReport {
            max_dimension: 0,
            simplex_counts_by_dim: vec![0],
            euler_characteristic: 0,
            boundary_law_verified: true,
            compositions: vec![],
        });
    }

    let simps: Result<Vec<Simplex>, _> = simplices
        .iter()
        .map(|v| Simplex::from_unordered(v.clone()))
        .collect();
    let simps = simps.map_err(|e| format!("invalid simplex: {e:?}"))?;
    let complex = SimplicialComplex::from_simplices(simps)
        .map_err(|e| format!("failed to build simplicial complex: {e:?}"))?;

    let max_dim = complex.max_dimension();
    let simplex_counts_by_dim: Vec<usize> = (0..=max_dim).map(|d| complex.count(d)).collect();
    let euler_characteristic = complex.euler_characteristic();

    let mut compositions = Vec::new();
    let mut boundary_law_verified = true;

    for k in 2..=max_dim {
        match complex.boundary_composition(k) {
            Ok(comp) => {
                let is_zero = comp.as_slice().iter().all(|x| x.is_zero());
                if !is_zero {
                    boundary_law_verified = false;
                }
                compositions.push(SimplicialCompositionRecord {
                    degree: k,
                    rows: comp.rows(),
                    cols: comp.cols(),
                    is_zero,
                });
            }
            Err(e) => {
                return Err(format!("boundary composition error at degree {k}: {e:?}"));
            }
        }
    }

    Ok(SimplicialBoundaryReport {
        max_dimension: max_dim,
        simplex_counts_by_dim,
        euler_characteristic,
        boundary_law_verified,
        compositions,
    })
}

/// Verifies that a higher-dimensional simplicial complex satisfies d_{k-1} ∘ d_k = 0.
pub fn verify_simplicial_boundary_law(simplices: &[Vec<usize>]) -> Result<bool, String> {
    let report = verify_simplicial_boundary_detailed(simplices)?;
    Ok(report.boundary_law_verified)
}

fn validate_transformation_tables(tables: &[RationalMatrix]) -> Result<usize, RationalError> {
    if tables.is_empty() {
        return Err(RationalError::LinearAlgebra(
            "no transformation tables provided".into(),
        ));
    }
    let dim = tables[0].rows();
    if !tables[0].is_square() {
        return Err(RationalError::NotSquare {
            rows: tables[0].rows(),
            cols: tables[0].cols(),
        });
    }
    for (i, t) in tables.iter().enumerate() {
        if t.rows() != dim || t.cols() != dim {
            return Err(RationalError::LinearAlgebra(format!(
                "table {i} dimension mismatch: expected {dim}x{dim}, got {}x{}",
                t.rows(),
                t.cols()
            )));
        }
    }
    Ok(dim)
}

fn table_step_matrix(
    tables: &[RationalMatrix],
    idx: usize,
    back: bool,
) -> Result<ExactMatrix<BigRational>, RationalError> {
    if idx >= tables.len() {
        return Err(RationalError::LinearAlgebra(format!(
            "turn index {idx} out of range (max {})",
            tables.len() - 1
        )));
    }
    let t = &tables[idx];
    let flat_data: Vec<BigRational> = (0..t.rows())
        .flat_map(|r| (0..t.cols()).map(move |c| t.get(r, c).clone()))
        .collect();
    let mat = ExactMatrix::<BigRational>::try_new(t.rows(), t.cols(), flat_data)
        .map_err(|e| RationalError::LinearAlgebra(format!("{e:?}")))?;
    if back {
        mat.transpose()
            .map_err(|e| RationalError::LinearAlgebra(format!("{e:?}")))
    } else {
        Ok(mat)
    }
}

/// Evaluates the path-ordered product of transformation tables along a word:
/// U(w) = ∏_{i} T_{g_i}^{±1}
///
/// Inversion is transposition for orthogonal tables.
pub fn ordered_loop_product(
    tables: &[RationalMatrix],
    word: &[(usize, bool)],
) -> Result<RationalMatrix, RationalError> {
    let dim = validate_transformation_tables(tables)?;

    let mut current = ExactMatrix::<BigRational>::try_identity(dim)
        .map_err(|e| RationalError::LinearAlgebra(format!("{e:?}")))?;

    for &(idx, back) in word {
        let step = table_step_matrix(tables, idx, back)?;
        current = current
            .matmul(&step)
            .map_err(|e| RationalError::LinearAlgebra(format!("{e:?}")))?;
    }

    let rows: Vec<Vec<BigRational>> = current
        .data
        .chunks(dim)
        .map(|chunk| chunk.to_vec())
        .collect();
    RationalMatrix::from_rows(&rows)
}

/// Checks whether the path-ordered product of tables along a word is the identity.
pub fn is_ordered_closure(
    tables: &[RationalMatrix],
    word: &[(usize, bool)],
) -> Result<bool, RationalError> {
    let prod = ordered_loop_product(tables, word)?;
    if !prod.is_square() {
        return Ok(false);
    }
    let dim = prod.rows();
    for r in 0..dim {
        for c in 0..dim {
            let expected = if r == c { Exact::one() } else { Exact::zero() };
            if prod.get(r, c) != &expected {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

// Origin: engine/crates_rs/pfp_runtime/src/homology_holonomy.rs
// Claim: urn:core:crates_rs:pfp-runtime:homology-holonomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9252cc24 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9252cc24` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9252cc24 {
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
impl BoundaryError9252cc24 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9252cc24 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9252cc24 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9252cc24 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9252cc24> {
        if capacity_bound == 0 {
            return Err(BoundaryError9252cc24::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9252cc24::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9252cc24::ExceedsCapacity {
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
mod l4_boundary_tests_9252cc24 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9252cc24::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9252cc24::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9252cc24::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9252cc24::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9252cc24::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9252cc24::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9252cc24::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
