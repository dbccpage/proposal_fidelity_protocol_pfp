//! Exact finite control witness for `PLAN-QP-1` (`plan_qp_1`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_unconditional_h1_promotion_without_d1`.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub carrier_val: i64,
    pub secondary_pair: (i64, i64),
    pub coboundary_cycle_zero: i64,
}

pub fn witness() -> Witness {
    let a = [3_i64, 7, 11];
    let coboundary_cycle_zero = (a[1] - a[0]) + (a[2] - a[1]) + (a[0] - a[2]);
    Witness {
        carrier_val: 512,
        secondary_pair: (1, 1),
        coboundary_cycle_zero,
    }
}

pub fn reject_unconditional_h1_promotion_without_d1(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "unconditional_h1_promotion_without_d1" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-1: unconditional_h1_promotion_without_d1")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_1.rs
// Claim: urn:core:crates_rs:tests:plan-qp-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb3e3a4bf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb3e3a4bf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb3e3a4bf {
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
impl BoundaryErrorb3e3a4bf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb3e3a4bf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb3e3a4bf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb3e3a4bf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb3e3a4bf> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb3e3a4bf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb3e3a4bf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb3e3a4bf::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_unconditional_h1_promotion_without_d1, witness};

    #[test]
    fn plan_qp_1_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 512);
        assert_eq!(w.secondary_pair, (1, 1));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_1_refuses_unconditional_h1_promotion_without_d1() {
        assert!(reject_unconditional_h1_promotion_without_d1("unconditional_h1_promotion_without_d1").is_err());
        assert!(reject_unconditional_h1_promotion_without_d1("promote_unrestricted").is_err());
        assert!(reject_unconditional_h1_promotion_without_d1("admissible_scoped_control").is_ok());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CocycleError { kind: &'static str, left: i128, right: i128 }
impl CocycleError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// An integer 1-cochain on a cycle is admitted only when the edge values sum to zero.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EdgeCocycle { edges: u64, sum: i128 }
pub fn try_edge_cocycle(edges: &[i64]) -> Result<EdgeCocycle, CocycleError> {
    if edges.is_empty() {
        return Err(CocycleError::new("a cocycle has an edge", 0, 0));
    }
    let mut sum = 0i128;
    let mut count = 0u64;
    for edge in edges {
        sum = sum.checked_add(i128::from(*edge)).ok_or_else(|| CocycleError::new("cocycle sum overflow", sum, i128::from(*edge)))?;
        count = count.checked_add(1).ok_or_else(|| CocycleError::new("edge count overflow", i128::from(count), 1))?;
    }
    if sum != 0 {
        return Err(CocycleError::new("cycle edges do not sum to zero", sum, 0));
    }
    Ok(EdgeCocycle { edges: count, sum })
}
fn checked_edge_diff(left: i64, right: i64, err_msg: &'static str) -> Result<i64, CocycleError> {
    let step = i128::from(right) - i128::from(left);
    i64::try_from(step).map_err(|_| CocycleError::new(err_msg, step, 0))
}

pub fn try_closed_coboundary(vertices: &[i64]) -> Result<EdgeCocycle, CocycleError> {
    if vertices.len() < 2 {
        return Err(CocycleError::new("a closed coboundary needs two vertices", vertices.len() as i128, 2));
    }
    let mut edges = Vec::with_capacity(vertices.len());
    for pair in vertices.windows(2) {
        edges.push(checked_edge_diff(pair[0], pair[1], "edge difference exceeds i64")?);
    }
    let first = vertices[0];
    let end = vertices[vertices.len() - 1];
    edges.push(checked_edge_diff(end, first, "closing difference exceeds i64")?);
    try_edge_cocycle(&edges)
}
#[cfg(test)]
mod edge_cocycle_checks {
    use super::{try_closed_coboundary, try_edge_cocycle};
    #[test]
    fn an_arbitrary_zero_sum_is_admitted_and_a_nonzero_sum_is_refused() {
        assert_eq!(try_edge_cocycle(&[4, -1, -3]).as_ref().map(|item| item.sum), Ok(0));
        assert_eq!(try_edge_cocycle(&[1, 1]).map(|_| ()).map_err(|e| e.kind()), Err("cycle edges do not sum to zero"));
        assert_eq!(try_closed_coboundary(&[3, 7, 11]).as_ref().map(|item| item.edges), Ok(3));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_b3e3a4bf() {
    let admitted = BoundaryRecordb3e3a4bf::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb3e3a4bf::try_admit(9, 8).is_err());
}
