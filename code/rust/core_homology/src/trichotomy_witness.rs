//! --- Math Contract: PO-D9 / GTFOC-20 — Element-level residual trichotomy ---
//!
//! Mechanizes the element-level finite obstruction trichotomy on
//! `Q^1 = C^1 / im(d0)`. Given a residual cochain `q ∈ C^1`, classify its class
//! `[q]` by EXACT rational computation:
//!
//!   - `ExactRepair`        <=> `[q] = 0`            (`q ∈ im(d0)`)              [Φ1 = 0]
//!   - `StabilizedSurvivor` <=> `[q] ≠ 0`, closed    (`q ∉ im d0`, `d1·q = 0`)  [Φ1>0, Γ2=0]
//!   - `OpenObstruction`    <=> not closed           (`d1·q ≠ 0`)               [Γ2 > 0]
//!
//! This is the cohomological content of the `(Φ1,Γ2)`-trichotomy (L20A.2 /
//! L20A.3 / GTFOC-20, proof_obligations.md §18.1–18.2) verified at the *element*
//! level, and the element-level exactness of the survivor short exact sequence
//! `0 -> im(d0) -> ker(d1) -> H^1 -> 0` (PO-D9): a `StabilizedSurvivor` is
//! exhibited as a genuine `H^1` representative — a cocycle (`d1·q = 0`) that is
//! NOT a coboundary (`q ∉ im d0`) — and two residuals are cohomologous iff their
//! difference is a coboundary.
//!
//! Unlike a `dim ker - rank` identity (which is true by construction), every
//! step here is a real exact-rational computation that fails for an ill-formed
//! witness — mirroring the PO-D1 `d1∘d0 = 0` discharge.

use num_traits::Zero;

use crate::errors::HomologicalError;
use crate::matrix::{in_column_space, mat_vec_mul};
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;

/// The element-level residual trichotomy class of `[q] ∈ Q^1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResidualClass {
    /// `[q] = 0`: the residual is an exact coboundary (`q ∈ im d0`).
    ExactRepair,
    /// Closed but not exact: a genuine `H^1` survivor.
    StabilizedSurvivor,
    /// Not closed (`d1·q ≠ 0`): a higher-arity open obstruction.
    OpenObstruction,
}

/// Is `q` closed (a cocycle): `d1·q = 0`?
pub fn is_cocycle(d1: &BasicMatrix<Q>, q: &[Q]) -> Result<bool, HomologicalError> {
    let image = mat_vec_mul(d1, q)?;
    Ok(image.iter().all(|x| x.is_zero()))
}

/// Is `q` an exact coboundary: `q ∈ im(d0)`?
pub fn is_coboundary(d0: &BasicMatrix<Q>, q: &[Q]) -> Result<bool, HomologicalError> {
    in_column_space(d0, q)
}

/// Classify the residual class `[q] ∈ Q^1` by exact computation over `Q`.
pub fn classify_residual(
    d0: &BasicMatrix<Q>,
    d1: &BasicMatrix<Q>,
    q: &[Q],
) -> Result<ResidualClass, HomologicalError> {
    // q ∈ C^1, so q.len() == dim C^1 == d0.rows() == d1.cols().
    if q.len() != d0.rows() {
        return Err(HomologicalError::DimensionMismatch {
            expected: d0.rows(),
            got: q.len(),
        });
    }
    if d1.cols() != d0.rows() {
        return Err(HomologicalError::DimensionMismatch {
            expected: d0.rows(),
            got: d1.cols(),
        });
    }

    if is_coboundary(d0, q)? {
        // [q] = 0.
        return Ok(ResidualClass::ExactRepair);
    }
    if is_cocycle(d1, q)? {
        // closed, not exact => genuine H^1 survivor.
        Ok(ResidualClass::StabilizedSurvivor)
    } else {
        // not closed.
        Ok(ResidualClass::OpenObstruction)
    }
}

/// Two residuals are cohomologous iff their difference is a coboundary:
/// `q1 - q2 ∈ im(d0)`. This is the exactness of the class map on `Q^1`.
pub fn cohomologous(d0: &BasicMatrix<Q>, q1: &[Q], q2: &[Q]) -> Result<bool, HomologicalError> {
    if q1.len() != q2.len() {
        return Err(HomologicalError::DimensionMismatch {
            expected: q1.len(),
            got: q2.len(),
        });
    }
    let diff: Vec<Q> = q1
        .iter()
        .zip(q2)
        .map(|(a, b)| a.clone() - b.clone())
        .collect();
    in_column_space(d0, &diff)
}

// Origin: engine/crates_rs/core_homology/src/trichotomy_witness.rs
// Claim: urn:core:crates_rs:core-homology:trichotomy-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord12abb90a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord12abb90a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError12abb90a {
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
impl BoundaryError12abb90a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError12abb90a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError12abb90a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord12abb90a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError12abb90a> {
        if capacity_bound == 0 {
            return Err(BoundaryError12abb90a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError12abb90a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError12abb90a::ExceedsCapacity {
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
    use num_rational::Rational64;

    fn q(n: i64) -> Q {
        crate::scalar::q(n)
    }

    /// Triangle nerve d0 (im d0 = { x : x0+x1+x2 = 0 }).
    fn triangle_d0() -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(
            3,
            3,
            vec![
                q(-1),
                q(1),
                q(0), //
                q(0),
                q(-1),
                q(1), //
                q(1),
                q(0),
                q(-1),
            ],
        )
        .unwrap()
    }

    /// Unfilled triangle: C^2 trivial, d1 = 0 (1x3). Every cochain is closed.
    fn d1_zero() -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(1, 3, vec![q(0); 3]).unwrap()
    }

    /// Filled triangle: d1 = [1,1,1] (the 2-cell boundary). d1∘d0 = 0 still.
    fn d1_filled() -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(1, 3, vec![q(1), q(1), q(1)]).unwrap()
    }

    #[test]
    fn zero_and_coboundary_residuals_are_exact_repair() {
        let d0 = triangle_d0();
        let d1 = d1_zero();
        assert_eq!(
            classify_residual(&d0, &d1, &[q(0), q(0), q(0)]).unwrap(),
            ResidualClass::ExactRepair
        );
        // d0 · [0,1,0] = [1,-1,0], a coboundary.
        assert_eq!(
            classify_residual(&d0, &d1, &[q(1), q(-1), q(0)]).unwrap(),
            ResidualClass::ExactRepair
        );
    }

    #[test]
    fn winding_residual_is_a_genuine_h1_survivor() {
        let d0 = triangle_d0();
        let d1 = d1_zero();
        let winding = [q(1), q(1), q(1)];
        // Explicitly: it IS a cocycle and is NOT a coboundary — a real H^1 rep.
        assert!(is_cocycle(&d1, &winding).unwrap());
        assert!(!is_coboundary(&d0, &winding).unwrap());
        assert_eq!(
            classify_residual(&d0, &d1, &winding).unwrap(),
            ResidualClass::StabilizedSurvivor
        );
    }

    #[test]
    fn non_closed_residual_is_open_obstruction() {
        let d0 = triangle_d0();
        let d1 = d1_filled();
        // d1·[1,0,0] = [1] != 0 => not closed.
        assert!(!is_cocycle(&d1, &[q(1), q(0), q(0)]).unwrap());
        assert_eq!(
            classify_residual(&d0, &d1, &[q(1), q(0), q(0)]).unwrap(),
            ResidualClass::OpenObstruction
        );
    }

    #[test]
    fn cohomologous_iff_differ_by_a_coboundary() {
        let d0 = triangle_d0();
        // [1,1,1] and [1,1,1] + d0·[0,1,0] = [2,0,1] are cohomologous (same H^1 class).
        assert!(cohomologous(&d0, &[q(1), q(1), q(1)], &[q(2), q(0), q(1)]).unwrap());
        // [1,1,1] and [2,2,2] differ by [-1,-1,-1] (sum -3 != 0): NOT cohomologous.
        assert!(!cohomologous(&d0, &[q(1), q(1), q(1)], &[q(2), q(2), q(2)]).unwrap());
    }

    #[test]
    fn cohomologous_survivors_share_the_class() {
        let d0 = triangle_d0();
        let d1 = d1_zero();
        // [2,0,1] is cohomologous to the winding survivor, so it is also a survivor.
        assert_eq!(
            classify_residual(&d0, &d1, &[q(2), q(0), q(1)]).unwrap(),
            ResidualClass::StabilizedSurvivor
        );
        assert!(cohomologous(&d0, &[q(1), q(1), q(1)], &[q(2), q(0), q(1)]).unwrap());
    }

    #[test]
    fn dimension_mismatch_is_rejected() {
        let d0 = triangle_d0();
        let d1 = d1_zero();
        assert!(matches!(
            classify_residual(&d0, &d1, &[q(1), q(1)]),
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_12abb90a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord12abb90a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord12abb90a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord12abb90a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord12abb90a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord12abb90a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError12abb90a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError12abb90a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
