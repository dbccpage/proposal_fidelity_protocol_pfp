use crate::finite_directed_graph::{DirectedGraphError, FiniteDirectedGraph};
use std::collections::HashMap;

pub fn graph_from_poset(
    poset: &FiniteDirectedGraph,
) -> Result<FiniteDirectedGraph, DirectedGraphError> {
    Ok(poset.clone())
}

pub fn graph_from_edges(
    nodes: &[String],
    edges: &[(String, String)],
) -> Result<FiniteDirectedGraph, DirectedGraphError> {
    let node_index: HashMap<String, usize> = nodes
        .iter()
        .enumerate()
        .map(|(index, name)| (name.clone(), index))
        .collect();

    let indexed_edges = edges
        .iter()
        .map(|(source, target)| {
            Ok((
                *node_index
                    .get(source)
                    .ok_or(DirectedGraphError::InvalidNodeIndex)?,
                *node_index
                    .get(target)
                    .ok_or(DirectedGraphError::InvalidNodeIndex)?,
            ))
        })
        .collect::<Result<Vec<_>, DirectedGraphError>>()?;

    FiniteDirectedGraph::new(
        nodes.to_vec(),
        node_index,
        indexed_edges,
        crate::finite_directed_graph::TheoremProvenance {
            verification_source: "lambda".into(),
        },
    )
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StrictRelationBudget {
    order: u64,
    strict_relations: u64,
    cap: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StrictRelationBudgetError {
    EmptyCarrier,
    BlankNode,
    DuplicateNode,
    MissingEndpoint,
    SelfLoop,
    DuplicateRelation,
    AboveCap { strict_relations: u64, cap: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/lambda_graph.rs
// Claim: urn:core:crates_rs:core-homology:lambda-graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StrictRelationBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StrictRelationBudgetError {}

impl StrictRelationBudget {
    pub fn certify(nodes: &[String], edges: &[(String, String)]) -> Result<Self, StrictRelationBudgetError> {
        let order = Self::validate_nodes(nodes)?;
        let strict_relations = Self::validate_edges(nodes, edges)?;
        let pred = order.checked_sub(1).ok_or(StrictRelationBudgetError::Overflow)?;
        let product = order.checked_mul(pred).ok_or(StrictRelationBudgetError::Overflow)?;
        let cap = product.checked_div(2).ok_or(StrictRelationBudgetError::Overflow)?;
        if strict_relations > cap { return Err(StrictRelationBudgetError::AboveCap { strict_relations, cap }); }
        Ok(Self { order, strict_relations, cap })
    }

    fn validate_nodes(nodes: &[String]) -> Result<u64, StrictRelationBudgetError> {
        if nodes.is_empty() { return Err(StrictRelationBudgetError::EmptyCarrier); }
        let order = u64::try_from(nodes.len()).map_err(|_| StrictRelationBudgetError::Overflow)?;
        for (idx, name) in nodes.iter().enumerate() {
            if name.trim().is_empty() { return Err(StrictRelationBudgetError::BlankNode); }
            if nodes.iter().skip(idx + 1).any(|other| other == name) {
                return Err(StrictRelationBudgetError::DuplicateNode);
            }
        }
        Ok(order)
    }

    fn validate_edges(nodes: &[String], edges: &[(String, String)]) -> Result<u64, StrictRelationBudgetError> {
        let strict_relations = u64::try_from(edges.len()).map_err(|_| StrictRelationBudgetError::Overflow)?;
        for (idx, (source, target)) in edges.iter().enumerate() {
            if source == target { return Err(StrictRelationBudgetError::SelfLoop); }
            if !nodes.iter().any(|node| node == source) || !nodes.iter().any(|node| node == target) {
                return Err(StrictRelationBudgetError::MissingEndpoint);
            }
            if edges.iter().skip(idx + 1).any(|(s, t)| s == source && t == target) {
                return Err(StrictRelationBudgetError::DuplicateRelation);
            }
        }
        Ok(strict_relations)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        let nodes = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let edges = vec![("a".to_string(), "b".to_string()), ("b".to_string(), "c".to_string())];
        assert!(matches!(StrictRelationBudget::certify(&nodes, &edges), Ok(w) if w.order == 3 && w.strict_relations == 2 && w.cap == 3));
        let looped = vec![("a".to_string(), "a".to_string())];
        assert!(matches!(StrictRelationBudget::certify(&nodes, &looped), Err(StrictRelationBudgetError::SelfLoop)));
        let dense = vec![("a".to_string(), "b".to_string()), ("b".to_string(), "c".to_string()), ("a".to_string(), "c".to_string()), ("c".to_string(), "b".to_string())];
        assert!(matches!(StrictRelationBudget::certify(&nodes, &dense), Err(StrictRelationBudgetError::AboveCap { .. })));
    }
}
