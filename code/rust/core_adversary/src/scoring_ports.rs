//! Adversary-owned carrier scoring port; concrete certifiers are injected.
use crate::carrier::{ExactCochain, Network};
use crate::evidence::ObstructionMeasurement;
use crate::stage::ports::Refusal;
use serde_json::{Map, Value};

pub struct CochainScoringRequest<'a> {
    pub network: &'a Network,
    pub initial_cochain: &'a ExactCochain,
    pub ablation_flags: Option<&'a Map<String, Value>>,
}
pub trait CochainScoringPort {
    fn identify_obstructions(
        &mut self,
        request: &CochainScoringRequest<'_>,
    ) -> Result<ObstructionMeasurement, Refusal>;
}
/// A missing scorer supplies no numerical values or verified certificate.
pub struct NullCochainScorer;
impl CochainScoringPort for NullCochainScorer {
    fn identify_obstructions(
        &mut self,
        _request: &CochainScoringRequest<'_>,
    ) -> Result<ObstructionMeasurement, Refusal> {
        ObstructionMeasurement::not_measured(
            "No cochain scorer is bound to this bout.".into(),
            "null_scorer".into(),
        )
    }
}


/// Exact Euler characteristic of the network 2-skeleton: `V - E + F`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NetworkEulerWitness {
    nodes: u64,
    edges: u64,
    faces: u64,
    euler: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NetworkEulerError {
    EdgesWithoutNodes { edges: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_adversary/src/scoring_ports.rs
// Claim: urn:core:crates_rs:core-adversary:scoring-ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for NetworkEulerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for NetworkEulerError {}

pub fn admit_network_euler(network: &Network) -> Result<NetworkEulerWitness, NetworkEulerError> {
    if network.nodes().is_empty() && !network.edges().is_empty() {
        return Err(NetworkEulerError::EdgesWithoutNodes {
            edges: network.edges().len(),
        });
    }
    let nodes_u64 = u64::try_from(network.nodes().len()).map_err(|_| NetworkEulerError::Overflow)?;
    let edges_u64 = u64::try_from(network.edges().len()).map_err(|_| NetworkEulerError::Overflow)?;
    let faces_u64 = u64::try_from(network.faces().len()).map_err(|_| NetworkEulerError::Overflow)?;
    let nodes_i64 = i64::try_from(nodes_u64).map_err(|_| NetworkEulerError::Overflow)?;
    let edges_i64 = i64::try_from(edges_u64).map_err(|_| NetworkEulerError::Overflow)?;
    let faces_i64 = i64::try_from(faces_u64).map_err(|_| NetworkEulerError::Overflow)?;
    let euler = nodes_i64
        .checked_sub(edges_i64)
        .and_then(|value| value.checked_add(faces_i64))
        .ok_or(NetworkEulerError::Overflow)?;
    Ok(NetworkEulerWitness {
        nodes: nodes_u64,
        edges: edges_u64,
        faces: faces_u64,
        euler,
    })
}

impl NetworkEulerWitness {
    pub fn euler(&self) -> i64 {
        self.euler
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::carrier::NodeLabel;

    #[test]
    fn a_triangle_has_euler_characteristic_one() {
        let a = NodeLabel::Text("a".into());
        let b = NodeLabel::Text("b".into());
        let c = NodeLabel::Text("c".into());
        let built = Network::new(
            vec![a.clone(), b.clone(), c.clone()],
            vec![[a.clone(), b.clone()], [b.clone(), c.clone()], [c.clone(), a.clone()]],
            vec![[a, b, c]],
            vec![],
            vec![],
        );
        assert!(built.is_ok());
        let admitted = built.ok().and_then(|network| admit_network_euler(&network).ok());
        assert_eq!(admitted.map(|witness| witness.euler()), Some(1));
    }
}
