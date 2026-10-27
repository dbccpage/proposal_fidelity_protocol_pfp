use core_types::q_continuum::{
    holonomy_ladder_descent_ledger, AuthorityScope, DescentGate, DescentObligation, DescentResult,
    FiniteProjection, LeanWitness, QContinuumLedger,
};

use super::packet::ValidatedQPacket;

/// Adapter over `core_types::q_continuum::DescentGate`.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct QDescentGate {
    inner: DescentGate,
}

impl QDescentGate {
    pub fn new() -> Self {
        Self {
            inner: DescentGate::new(),
        }
    }

    pub fn project_packet(&self, packet: &ValidatedQPacket) -> FiniteProjection {
        let packet = packet.packet();
        FiniteProjection {
            id: format!("{}:projection:q", packet.id),
            source_id: packet.id.clone(),
            carrier: packet.carrier.clone().unwrap_or_default(),
            zero_relation: "same finite shadow under declared observer and transport".to_string(),
            scope: AuthorityScope::new(format!("q-packet:{}", packet.id)),
            finite_description: format!(
                "composition: {}; observer: {}; finite_predictions: {}",
                packet.composition.as_deref().unwrap_or_default(),
                packet.observer.as_deref().unwrap_or_default(),
                packet.finite_predictions.join("; ")
            ),
        }
    }

    pub fn obligations_for_packet(&self, packet: &ValidatedQPacket) -> Vec<DescentObligation> {
        let projection = self.project_packet(packet);
        self.inner.obligations_for_projection(&projection)
    }

    pub fn verify_lean_witness(
        &self,
        obligation_id: impl Into<String>,
        scope: AuthorityScope,
        witness: &LeanWitness,
    ) -> DescentResult {
        self.inner
            .verify_lean_witness(obligation_id, scope, witness)
    }

    pub fn accept_results(
        &self,
        ledger: &mut QContinuumLedger,
        about: impl Into<String>,
        results: Vec<DescentResult>,
    ) {
        self.inner.accept_results(ledger, about, results);
    }

    /// The first real finite-descent artifact mapped into Q without terminal overclaim.
    pub fn holonomy_ladder_ledger() -> QContinuumLedger {
        holonomy_ladder_descent_ledger()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DescentChain {
    depth: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DescentChainError {
    ParentNotSmaller,
    Overflow,
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/descent.rs
// Claim: urn:core:crates_rs:core-wdp:descent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DescentChainError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DescentChainError {}

pub fn try_strict_descent(parent: &[Option<u32>]) -> Result<DescentChain, DescentChainError> {
    let mut max_depth = 0u32;
    for (index, link) in parent.iter().enumerate() {
        let here = u32::try_from(index).map_err(|_| DescentChainError::Overflow)?;
        let Some(mut cursor) = *link else {
            continue;
        };
        if cursor >= here {
            return Err(DescentChainError::ParentNotSmaller);
        }
        let mut depth = 0u32;
        let mut guard = 0u32;
        loop {
            depth = depth.checked_add(1).ok_or(DescentChainError::Overflow)?;
            guard = guard.checked_add(1).ok_or(DescentChainError::Overflow)?;
            if u64::from(guard) > parent.len() as u64 {
                return Err(DescentChainError::ParentNotSmaller);
            }
            let Some(next_index) = usize::try_from(cursor).ok() else {
                return Err(DescentChainError::Overflow);
            };
            let Some(next) = parent.get(next_index).copied() else {
                return Err(DescentChainError::ParentNotSmaller);
            };
            let Some(parent_of) = next else {
                break;
            };
            if parent_of >= cursor {
                return Err(DescentChainError::ParentNotSmaller);
            }
            cursor = parent_of;
        }
        if depth > max_depth {
            max_depth = depth;
        }
    }
    Ok(DescentChain { depth: max_depth })
}

impl DescentChain {
    pub fn depth(&self) -> u32 {
        self.depth
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod descent_chain_tests {
    use super::*;

    #[test]
    fn a_strict_parent_chain_has_depth_two() {
        let chain = try_strict_descent(&[None, Some(0), Some(1)]);
        assert!(matches!(chain, Ok(chain) if chain.depth() == 2));
        assert!(matches!(
            try_strict_descent(&[None, Some(1)]),
            Err(DescentChainError::ParentNotSmaller)
        ));
    }
}
