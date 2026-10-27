//! Exact tests for the interpretations movement of the finite quantum mechanics
//! programme: interpretations read as authority shadows, typed
//! non-implications, the finite-descent audit of the imported interface, and
//! Everettian relative states. One submodule per retired source paper; the
//! paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod everettian_relative_state_contact;
mod formal_possibility_promotion_error;
mod interpretations_as_authority_shadows;
mod quantum_interface_descent_audit;
mod typed_authority_boundary_suite;

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DescentError {
    Authority,
    Label,
    Rank,
    Edge,
    Decrease { from: usize, to: usize },
    Cycle { node: usize },
}

// Origin: engine/crates_rs/tests/core_quantum_physics/interpretations/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DescentError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DescentError {}

/// A finite descent: unique labels, authority None, strictly decreasing ranks, and no cycle.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteDescentAudit {
    steps: usize,
}

fn walk_descent(
    node: usize,
    adjacent: &[Vec<usize>],
    colour: &mut [u8],
) -> Result<(), DescentError> {
    let slot = colour.get_mut(node).ok_or(DescentError::Edge)?;
    if *slot == 1 {
        return Err(DescentError::Cycle { node });
    }
    if *slot == 2 {
        return Ok(());
    }
    *slot = 1;
    let children = adjacent.get(node).ok_or(DescentError::Edge)?.clone();
    for child in children {
        walk_descent(child, adjacent, colour)?;
    }
    let slot = colour.get_mut(node).ok_or(DescentError::Edge)?;
    *slot = 2;
    Ok(())
}

impl FiniteDescentAudit {
    fn validate_labels_and_ranks(labels: &[&str], ranks: &[u32], authority: &str) -> Result<(), DescentError> {
        if authority != "None" {
            return Err(DescentError::Authority);
        }
        if labels.is_empty() || labels.len() != ranks.len() {
            return Err(DescentError::Label);
        }
        let mut seen = BTreeSet::new();
        for label in labels {
            if label.is_empty() || !seen.insert(*label) {
                return Err(DescentError::Label);
            }
        }
        if ranks.contains(&0) {
            return Err(DescentError::Rank);
        }
        Ok(())
    }

    fn build_adjacency(n: usize, ranks: &[u32], edges: &[(usize, usize)]) -> Result<Vec<Vec<usize>>, DescentError> {
        let mut adjacent = vec![Vec::new(); n];
        for &(from, to) in edges {
            if from >= n || to >= n || from == to {
                return Err(DescentError::Edge);
            }
            if ranks[from] <= ranks[to] {
                return Err(DescentError::Decrease { from, to });
            }
            adjacent[from].push(to);
        }
        Ok(adjacent)
    }

    pub fn try_new(labels: &[&str], ranks: &[u32], edges: &[(usize, usize)], authority: &str) -> Result<Self, DescentError> {
        Self::validate_labels_and_ranks(labels, ranks, authority)?;
        let adjacent = Self::build_adjacency(labels.len(), ranks, edges)?;
        let mut colour = vec![0u8; labels.len()];
        for node in 0..labels.len() {
            walk_descent(node, &adjacent, &mut colour)?;
        }
        Ok(Self { steps: edges.len() })
    }

    pub fn steps(&self) -> usize { self.steps }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod descent_audit_tests {
    use super::*;

    #[test]
    fn a_decreasing_step_with_no_authority_is_admitted() {
        let audit = FiniteDescentAudit::try_new(&["alpha", "beta"], &[3, 1], &[(0, 1)], "None");
        assert!(matches!(audit, Ok(ref audit) if audit.steps() == 1));
    }

    #[test]
    fn a_two_cycle_is_refused() {
        let audit = FiniteDescentAudit::try_new(&["alpha", "beta"], &[2, 1], &[(0, 1), (1, 0)], "None");
        assert!(matches!(audit, Err(DescentError::Decrease { from: 1, to: 0 }) | Err(DescentError::Cycle { .. })));
    }
}
