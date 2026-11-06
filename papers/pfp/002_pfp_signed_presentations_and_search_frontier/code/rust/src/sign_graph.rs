//! Exact finite sign holonomy for declared presentation rewrites.
//!
//! This is a host checker for a supplied signed graph. It
//! does not derive exchange, a Hamiltonian path integral, or a physical FSP claim.

use num_rational::Rational64;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum SignGraphError {
    #[error("Validation error: {0}")]
    Validation(String),
    #[error("Internal algorithm error: {0}")]
    Internal(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SignedRewrite {
    pub source: String,
    pub target: String,
    pub odd: u8,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GaugeWitness {
    pub vertices: Vec<String>,
    pub bits: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OddCycleWitness {
    /// Each step is (edge index, departure vertex, arrival vertex).
    pub steps: Vec<(usize, String, String)>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum SignResult {
    #[serde(rename = "gauge")]
    Gauge(GaugeWitness),
    #[serde(rename = "odd_cycle")]
    OddCycle(OddCycleWitness),
}

pub fn validate(
    vertices: &[String],
    edges: &[SignedRewrite],
) -> Result<(), SignGraphError> {
    let mut names = HashSet::new();
    for v in vertices {
        if !names.insert(v.clone()) {
            return Err(SignGraphError::Validation("vertices must be distinct strings".to_string()));
        }
    }
    for edge in edges {
        if !names.contains(&edge.source) || !names.contains(&edge.target) {
            return Err(SignGraphError::Validation("rewrite endpoint outside declared carrier".to_string()));
        }
        if edge.odd > 1 {
            return Err(SignGraphError::Validation("rewrite parity must be exactly 0 or 1".to_string()));
        }
    }
    Ok(())
}

/// Check every equation alpha(source) XOR alpha(target) = odd.
pub fn verify_gauge(
    vertices: &[String],
    edges: &[SignedRewrite],
    witness: &GaugeWitness,
) -> bool {
    if validate(vertices, edges).is_err() {
        return false;
    }
    if witness.vertices != vertices || witness.bits.len() != vertices.len() {
        return false;
    }
    if witness.bits.iter().any(|&b| b > 1) {
        return false;
    }
    let alpha: HashMap<&str, u8> = vertices
        .iter()
        .map(|s| s.as_str())
        .zip(witness.bits.iter().copied())
        .collect();

    edges.iter().all(|e| {
        let bit_u = alpha[e.source.as_str()];
        let bit_v = alpha[e.target.as_str()];
        (bit_u ^ bit_v) == e.odd
    })
}

/// Check a closed edge walk with odd parity, independent of the solver.
pub fn verify_odd_cycle(
    vertices: &[String],
    edges: &[SignedRewrite],
    witness: &OddCycleWitness,
) -> bool {
    if validate(vertices, edges).is_err() {
        return false;
    }
    if witness.steps.is_empty() {
        return false;
    }
    let mut parity: u8 = 0;
    let first = &witness.steps[0].1;
    let mut previous = first;

    for (edge_id, departure, arrival) in &witness.steps {
        if *edge_id >= edges.len() {
            return false;
        }
        let edge = &edges[*edge_id];
        if departure != previous {
            return false;
        }
        let valid_endpoints = (departure == &edge.source && arrival == &edge.target)
            || (departure == &edge.target && arrival == &edge.source);
        if !valid_endpoints {
            return false;
        }
        parity ^= edge.odd;
        previous = arrival;
    }

    previous == first && parity == 1
}

/// Return an exact gauge or a checkable odd closed walk.
pub fn classify_sign_graph(
    vertices: &[String],
    edges: &[SignedRewrite],
) -> Result<SignResult, SignGraphError> {
    validate(vertices, edges)?;

    let mut adjacency: HashMap<&str, Vec<(&str, usize, u8)>> = HashMap::new();
    for v in vertices {
        adjacency.insert(v.as_str(), Vec::new());
    }
    for (edge_id, edge) in edges.iter().enumerate() {
        adjacency
            .get_mut(edge.source.as_str())
            .unwrap()
            .push((edge.target.as_str(), edge_id, edge.odd));
        if edge.target != edge.source {
            adjacency
                .get_mut(edge.target.as_str())
                .unwrap()
                .push((edge.source.as_str(), edge_id, edge.odd));
        }
    }

    let mut alpha: HashMap<&str, u8> = HashMap::new();
    let mut parent: HashMap<&str, Option<(&str, usize)>> = HashMap::new();

    for root in vertices {
        let root_str = root.as_str();
        if alpha.contains_key(root_str) {
            continue;
        }
        alpha.insert(root_str, 0);
        parent.insert(root_str, None);
        let mut queue = VecDeque::new();
        queue.push_back(root_str);

        while let Some(source) = queue.pop_front() {
            let src_alpha = alpha[source];
            for &(target, edge_id, odd) in &adjacency[source] {
                let required = src_alpha ^ odd;
                if let Some(&existing) = alpha.get(target) {
                    if existing != required {
                        let cycle = conflict_cycle(source, target, edge_id, &parent)?;
                        let witness = OddCycleWitness { steps: cycle };
                        if !verify_odd_cycle(vertices, edges, &witness) {
                            return Err(SignGraphError::Internal(
                                "internal odd-cycle construction failed verification".to_string(),
                            ));
                        }
                        return Ok(SignResult::OddCycle(witness));
                    }
                } else {
                    alpha.insert(target, required);
                    parent.insert(target, Some((source, edge_id)));
                    queue.push_back(target);
                }
            }
        }
    }

    let bits: Vec<u8> = vertices.iter().map(|v| alpha[v.as_str()]).collect();
    let witness = GaugeWitness {
        vertices: vertices.to_vec(),
        bits,
    };
    if !verify_gauge(vertices, edges, &witness) {
        return Err(SignGraphError::Internal(
            "internal gauge construction failed verification".to_string(),
        ));
    }
    Ok(SignResult::Gauge(witness))
}

fn conflict_cycle(
    source: &str,
    target: &str,
    chord_id: usize,
    parent: &HashMap<&str, Option<(&str, usize)>>,
) -> Result<Vec<(usize, String, String)>, SignGraphError> {
    let mut ancestors: HashMap<&str, usize> = HashMap::new();
    let mut up_source: Vec<(usize, String, String)> = Vec::new();
    let mut current = source;
    ancestors.insert(current, 0);

    while let Some(&Some((ancestor, edge_id))) = parent.get(current) {
        up_source.push((edge_id, current.to_string(), ancestor.to_string()));
        current = ancestor;
        ancestors.insert(current, up_source.len());
    }

    let mut up_target: Vec<(usize, String, String)> = Vec::new();
    current = target;
    while !ancestors.contains_key(current) {
        match parent.get(current) {
            Some(&Some((ancestor, edge_id))) => {
                up_target.push((edge_id, current.to_string(), ancestor.to_string()));
                current = ancestor;
            }
            _ => {
                return Err(SignGraphError::Internal(
                    "conflict endpoints must share a tree root".to_string(),
                ));
            }
        }
    }

    let lca_depth = ancestors[current];
    let tree_to_lca = &up_source[..lca_depth];
    let mut lca_to_target = Vec::new();
    for (i, a, b) in up_target.iter().rev() {
        lca_to_target.push((*i, b.clone(), a.clone()));
    }

    let mut cycle = Vec::new();
    cycle.extend_from_slice(tree_to_lca);
    cycle.extend(lca_to_target);
    cycle.push((chord_id, target.to_string(), source.to_string()));
    Ok(cycle)
}

/// Adapt a pinned real symmetric matrix to the diagonal sign-gauge graph.
pub fn matrix_sign_graph(
    matrix: &[Vec<Rational64>],
) -> Result<(Vec<String>, Vec<SignedRewrite>), SignGraphError> {
    let size = matrix.len();
    for row in matrix {
        if row.len() != size {
            return Err(SignGraphError::Validation("matrix must be square".to_string()));
        }
    }
    for i in 0..size {
        for j in 0..i {
            if matrix[i][j] != matrix[j][i] {
                return Err(SignGraphError::Validation("matrix must be symmetric".to_string()));
            }
        }
    }
    let vertices: Vec<String> = (0..size).map(|i| i.to_string()).collect();
    let mut edges = Vec::new();
    for i in 0..size {
        for j in (i + 1)..size {
            let val = matrix[i][j];
            if val != Rational64::from_integer(0) {
                let odd = if val > Rational64::from_integer(0) { 1 } else { 0 };
                edges.push(SignedRewrite {
                    source: i.to_string(),
                    target: j.to_string(),
                    odd,
                });
            }
        }
    }
    Ok((vertices, edges))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tree_gauge() {
        let vertices = vec!["0".to_string(), "1".to_string(), "2".to_string()];
        let edges = vec![
            SignedRewrite { source: "0".to_string(), target: "1".to_string(), odd: 1 },
            SignedRewrite { source: "1".to_string(), target: "2".to_string(), odd: 0 },
        ];
        match classify_sign_graph(&vertices, &edges).expect("classification should succeed") {
            SignResult::Gauge(witness) => {
                assert!(verify_gauge(&vertices, &edges, &witness));
                assert_eq!(witness.bits, vec![0, 1, 1]);
            }
            SignResult::OddCycle(_) => panic!("expected gauge"),
        }
    }

    #[test]
    fn test_odd_triangle() {
        let vertices = vec!["0".to_string(), "1".to_string(), "2".to_string()];
        let edges = vec![
            SignedRewrite { source: "0".to_string(), target: "1".to_string(), odd: 1 },
            SignedRewrite { source: "1".to_string(), target: "2".to_string(), odd: 0 },
            SignedRewrite { source: "2".to_string(), target: "0".to_string(), odd: 0 },
        ];
        match classify_sign_graph(&vertices, &edges).expect("classification should succeed") {
            SignResult::OddCycle(witness) => {
                assert!(verify_odd_cycle(&vertices, &edges, &witness));
            }
            SignResult::Gauge(_) => panic!("expected odd cycle"),
        }
    }

    #[test]
    fn test_matrix_gauge() {
        let matrix = vec![
            vec![Rational64::from_integer(0), Rational64::from_integer(-1)],
            vec![Rational64::from_integer(-1), Rational64::from_integer(0)],
        ];
        let (vertices, edges) = matrix_sign_graph(&matrix).unwrap();
        match classify_sign_graph(&vertices, &edges).expect("gauge") {
            SignResult::Gauge(g) => {
                assert!(verify_gauge(&vertices, &edges, &g));
                assert_eq!(g.bits, vec![0, 0]);
            }
            SignResult::OddCycle(_) => panic!("expected gauge"),
        }
    }
}
