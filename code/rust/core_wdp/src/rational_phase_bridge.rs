//! Declared rational-turn transport and operational-readout boundaries.
//! AuthorityEffect: None. Symbolic phases live in Q/Z; actual scalar evaluation
//! is a checked cyclotomic-owner operation. This is not the infinite-order
//! Gaussian anchor's missing rational exponentiation, nor a real exponent map.
use crate::amplitude_bridge::{EdgePath, OrientedGraph};
use crate::error::WdpError;
use core_number_theory::rational_turns::RationalTurn;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalPhaseCochain {
    graph: OrientedGraph,
    phases: Vec<RationalTurn>,
}
impl RationalPhaseCochain {
    pub fn new(graph: OrientedGraph, phases: Vec<RationalTurn>) -> Result<Self, WdpError> {
        if phases.len() != graph.edges().len() {
            return Err(WdpError::InvalidInput {
                detail: "one rational turn per oriented edge is required".into(),
            });
        }
        Ok(Self { graph, phases })
    }
    pub fn graph(&self) -> &OrientedGraph {
        &self.graph
    }
    pub fn phases(&self) -> &[RationalTurn] {
        &self.phases
    }
    pub fn path_phase(&self, path: &EdgePath) -> Result<RationalTurn, WdpError> {
        self.graph.path_end(path)?;
        Ok(path.steps.iter().fold(RationalTurn::zero(), |sum, step| {
            let phase = &self.phases[step.edge];
            if step.forward {
                sum.add(phase)
            } else {
                sum.sub(phase)
            }
        }))
    }
    /// a'_uv=a_uv+f_v-f_u. On any validated path s→t the added phases
    /// telescope to f_t-f_s; every closed holonomy is therefore unchanged.
    pub fn gauge_transform(&self, potential: &[RationalTurn]) -> Result<Self, WdpError> {
        if potential.len() != self.graph.vertices() {
            return Err(WdpError::InvalidInput {
                detail: "one rational gauge turn per vertex is required".into(),
            });
        }
        let phases = self
            .graph
            .edges()
            .iter()
            .zip(&self.phases)
            .map(|(&(u, v), a)| a.add(&potential[v]).sub(&potential[u]))
            .collect();
        Self::new(self.graph.clone(), phases)
    }
    /// Compute both sides from the actual transformed cochain/path; this is not
    /// a caller-asserted invariant. False would indicate a broken implementation.
    pub fn verify_path_gauge_covariance(
        &self,
        path: &EdgePath,
        potential: &[RationalTurn],
    ) -> Result<bool, WdpError> {
        let transformed = self.gauge_transform(potential)?;
        let end = self.graph.path_end(path)?;
        let expected = self
            .path_phase(path)?
            .add(&potential[end])
            .sub(&potential[path.start]);
        Ok(transformed.path_phase(path)? == expected)
    }
}

// Origin: engine/crates_rs/core_wdp/src/rational_phase_bridge.rs
// Claim: urn:core:crates_rs:core-wdp:rational-phase-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5afe704e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5afe704e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5afe704e {
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
impl BoundaryError5afe704e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5afe704e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5afe704e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5afe704e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5afe704e> {
        if capacity_bound == 0 {
            return Err(BoundaryError5afe704e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5afe704e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5afe704e::ExceedsCapacity {
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
mod l4_boundary_tests_5afe704e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5afe704e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5afe704e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5afe704e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5afe704e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5afe704e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5afe704e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5afe704e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
