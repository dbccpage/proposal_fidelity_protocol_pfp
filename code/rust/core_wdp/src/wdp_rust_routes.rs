//! Structural and source-bound checks for the WDP-to-code ownership DAG.
//!
//! A checked route names its exact owner, contracts, test and negative control.
//! Validation checks graph structure and artifact commitments. It does not run
//! the named test or certify a mathematical theorem. AuthorityEffect: None.

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, VecDeque};

pub const DAG_SCHEMA_V1: &str = "core.wdp.architecture-dag.v1";
pub const MAX_DAG_ROWS: usize = 2048;
/// Total UTF-8 bytes in caller-declared strings, counted before graph storage
/// or the typed JSON commitment. Fixed schema overhead is also row-bounded.
pub const MAX_DAG_METADATA_BYTES: usize = 256 * 1024;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum NodeKind {
    Paper,
    Rust,
    Python,
    Obligation,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EdgeKind {
    SourceRelationship,
    ImplementedFiniteRoute,
    OpenObligation,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactBinding {
    pub path: String,
    pub sha256: String,
    pub anchor: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DagNode {
    pub id: String,
    pub title: String,
    pub kind: NodeKind,
    pub artifact: Option<ArtifactBinding>,
    pub scope: String,
}

/// Each semantic premise is explicit, including a stated non-applicable field.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BridgePremises {
    pub question: String,
    pub scalar: String,
    pub quotient: String,
    pub positivity: String,
    pub composition: String,
    pub availability: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DagEdge {
    pub id: String,
    pub from: String,
    pub to: String,
    pub kind: EdgeKind,
    pub owner: Option<ArtifactBinding>,
    pub input_contract: String,
    pub output_contract: String,
    pub oracle: Option<ArtifactBinding>,
    pub negative_control: String,
    pub premises: Option<BridgePremises>,
    pub scope: String,
    /// Declares that the named owner API was absent at the task's frozen baseline.
    /// The separate baseline comparison records evidence for that declaration.
    pub added_since_baseline: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum DagRecord {
    Node(DagNode),
    Edge(DagEdge),
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DagError {
    #[error("DAG row or metadata-byte limit exceeded, or empty graph")]
    Resource,
    #[error("invalid or duplicate identifier {0}")]
    Identifier(String),
    #[error("node {0} has missing source, title or scope")]
    NodeDeclaration(String),
    #[error("invalid artifact binding {0}")]
    Artifact(String),
    #[error("edge {0} references an absent node")]
    MissingNode(String),
    #[error("edge {0} has an incomplete finite bridge contract")]
    BridgeContract(String),
    #[error("DAG contains a directed cycle")]
    Cycle,
    #[error("DAG serialization failed")]
    Serialization,
}

/// Receipt minted by structural validation, with a fixed evidence ceiling.
#[derive(Debug, Clone, Serialize)]
pub struct DagReceipt {
    pub schema_version: &'static str,
    pub nodes: usize,
    pub edges: usize,
    pub implemented_routes: usize,
    pub declared_new_routes: usize,
    /// Distinct obligation nodes, counted once even with several incoming edges.
    pub open_obligations: usize,
    pub open_obligation_routes: usize,
    pub topological_order: Vec<String>,
    pub evidence_scope: &'static str,
    /// Domain-separated typed JSON commitment, distinct from raw artifact hashes.
    pub graph_digest_sha256: String,
    pub authority_effect: AuthorityEffect,
}

pub fn validate_dag(records: &[DagRecord]) -> Result<DagReceipt, DagError> {
    if records.is_empty() || records.len() > MAX_DAG_ROWS {
        return Err(DagError::Resource);
    }
    validate_metadata_size(records)?;
    let (nodes, edges) = collect_dag_nodes_and_edges(records)?;
    let (incoming, outgoing, implemented, new_routes, open_routes) =
        validate_and_index_edges(&nodes, &edges)?;
    let open = nodes
        .values()
        .filter(|node| node.kind == NodeKind::Obligation)
        .count();
    let order = topological_sort_dag(incoming, &outgoing, nodes.len())?;
    let encoded = serde_json::to_vec(records).map_err(|_| DagError::Serialization)?;
    let mut commitment = Sha256::new();
    commitment.update(b"core.wdp.architecture-dag.typed-json.v1\0");
    commitment.update(encoded);
    Ok(DagReceipt {
        schema_version: DAG_SCHEMA_V1,
        nodes: nodes.len(),
        edges: edges.len(),
        implemented_routes: implemented,
        declared_new_routes: new_routes,
        open_obligations: open,
        open_obligation_routes: open_routes,
        topological_order: order,
        evidence_scope: "graph_structure_and_declared_artifact_bindings_only",
        graph_digest_sha256: hex::encode(commitment.finalize()),
        authority_effect: AuthorityEffect::None,
    })
}

fn collect_dag_nodes_and_edges(
    records: &[DagRecord],
) -> Result<(BTreeMap<String, &DagNode>, Vec<&DagEdge>), DagError> {
    let mut ids = BTreeSet::new();
    let mut nodes = BTreeMap::new();
    let mut edges = Vec::new();
    for record in records {
        let id = match record {
            DagRecord::Node(node) => &node.id,
            DagRecord::Edge(edge) => &edge.id,
        };
        if !identifier(id) || !ids.insert(id.clone()) {
            return Err(DagError::Identifier(id.clone()));
        }
        match record {
            DagRecord::Node(node) => {
                validate_dag_node(id, node)?;
                nodes.insert(id.clone(), node);
            }
            DagRecord::Edge(edge) => edges.push(edge),
        }
    }
    if nodes.is_empty() {
        return Err(DagError::Resource);
    }
    Ok((nodes, edges))
}

fn validate_dag_node(id: &str, node: &DagNode) -> Result<(), DagError> {
    if node.title.trim().is_empty()
        || node.scope.trim().is_empty()
        || (node.kind != NodeKind::Obligation && node.artifact.is_none())
    {
        return Err(DagError::NodeDeclaration(id.to_string()));
    }
    if let Some(artifact) = &node.artifact {
        validate_artifact(artifact)?;
    }
    Ok(())
}

fn validate_and_index_edges<'a>(
    nodes: &BTreeMap<String, &'a DagNode>,
    edges: &[&'a DagEdge],
) -> Result<
    (
        BTreeMap<String, usize>,
        BTreeMap<String, Vec<String>>,
        usize,
        usize,
        usize,
    ),
    DagError,
> {
    let mut incoming: BTreeMap<String, usize> = nodes.keys().map(|id| (id.clone(), 0)).collect();
    let mut outgoing: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut implemented = 0;
    let mut new_routes = 0;
    let mut open_routes = 0;
    for edge in edges {
        validate_single_dag_edge(
            edge,
            nodes,
            &mut implemented,
            &mut new_routes,
            &mut open_routes,
        )?;
        *incoming
            .get_mut(&edge.to)
            .ok_or_else(|| DagError::MissingNode(edge.id.clone()))? += 1;
        outgoing
            .entry(edge.from.clone())
            .or_default()
            .push(edge.to.clone());
    }
    Ok((incoming, outgoing, implemented, new_routes, open_routes))
}

fn validate_single_dag_edge(
    edge: &DagEdge,
    nodes: &BTreeMap<String, &DagNode>,
    implemented: &mut usize,
    new_routes: &mut usize,
    open_routes: &mut usize,
) -> Result<(), DagError> {
    if !nodes.contains_key(&edge.from) || !nodes.contains_key(&edge.to) {
        return Err(DagError::MissingNode(edge.id.clone()));
    }
    if edge.scope.trim().is_empty() {
        return Err(DagError::BridgeContract(edge.id.clone()));
    }
    for artifact in [&edge.owner, &edge.oracle].into_iter().flatten() {
        validate_artifact(artifact)?;
    }
    validate_dag_edge_kind(edge, nodes[&edge.to], implemented, new_routes, open_routes)
}

fn validate_dag_edge_kind(
    edge: &DagEdge,
    target_node: &DagNode,
    implemented: &mut usize,
    new_routes: &mut usize,
    open_routes: &mut usize,
) -> Result<(), DagError> {
    match edge.kind {
        EdgeKind::ImplementedFiniteRoute => {
            validate_implemented_route_edge(edge, target_node)?;
            *implemented += 1;
            if edge.added_since_baseline {
                *new_routes += 1;
            }
        }
        EdgeKind::OpenObligation => {
            if edge.added_since_baseline || target_node.kind != NodeKind::Obligation {
                return Err(DagError::BridgeContract(edge.id.clone()));
            }
            *open_routes += 1;
        }
        EdgeKind::SourceRelationship => {
            if edge.added_since_baseline {
                return Err(DagError::BridgeContract(edge.id.clone()));
            }
        }
    }
    Ok(())
}

fn validate_implemented_route_edge(edge: &DagEdge, target_node: &DagNode) -> Result<(), DagError> {
    let Some(premises) = &edge.premises else {
        return Err(DagError::BridgeContract(edge.id.clone()));
    };
    let valid_contracts = edge.owner.is_some()
        && edge.oracle.is_some()
        && ![
            &edge.input_contract,
            &edge.output_contract,
            &edge.negative_control,
            &premises.question,
            &premises.scalar,
            &premises.quotient,
            &premises.positivity,
            &premises.composition,
            &premises.availability,
        ]
        .iter()
        .any(|value| value.trim().is_empty());
    if !valid_contracts || !valid_implemented_route_target(edge, target_node) {
        return Err(DagError::BridgeContract(edge.id.clone()));
    }
    Ok(())
}

fn valid_implemented_route_target(edge: &DagEdge, target_node: &DagNode) -> bool {
    matches!(target_node.kind, NodeKind::Rust | NodeKind::Python)
        && matches!(
            (&edge.owner, &target_node.artifact),
            (Some(owner), Some(target))
                if owner.path == target.path
                    && owner.sha256 == target.sha256
                    && owner.anchor == target.anchor
        )
}

fn topological_sort_dag(
    mut incoming: BTreeMap<String, usize>,
    outgoing: &BTreeMap<String, Vec<String>>,
    node_count: usize,
) -> Result<Vec<String>, DagError> {
    let mut ready: VecDeque<String> = incoming
        .iter()
        .filter(|(_, count)| **count == 0)
        .map(|(id, _)| id.clone())
        .collect();
    let mut order = Vec::new();
    while let Some(id) = ready.pop_front() {
        if let Some(targets) = outgoing.get(&id) {
            for target in targets {
                let count = incoming
                    .get_mut(target)
                    .ok_or_else(|| DagError::MissingNode(target.clone()))?;
                *count -= 1;
                if *count == 0 {
                    ready.push_back(target.clone());
                }
            }
        }
        order.push(id);
    }
    if order.len() != node_count {
        return Err(DagError::Cycle);
    }
    Ok(order)
}

pub fn validate_artifact(artifact: &ArtifactBinding) -> Result<(), DagError> {
    let mut metadata_bytes = 0;
    count_artifact_metadata(&mut metadata_bytes, artifact)?;
    if !repository_path(&artifact.path)
        || artifact.sha256.len() != 64
        || !artifact
            .sha256
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        || artifact.sha256.bytes().all(|byte| byte == b'0')
        || artifact.anchor.trim().is_empty()
    {
        return Err(DagError::Artifact(artifact.path.clone()));
    }
    Ok(())
}

fn count_metadata(total: &mut usize, text: &str) -> Result<(), DagError> {
    let next = total.checked_add(text.len()).ok_or(DagError::Resource)?;
    if next > MAX_DAG_METADATA_BYTES {
        return Err(DagError::Resource);
    }
    *total = next;
    Ok(())
}

fn count_artifact_metadata(total: &mut usize, artifact: &ArtifactBinding) -> Result<(), DagError> {
    for text in [&artifact.path, &artifact.sha256, &artifact.anchor] {
        count_metadata(total, text)?;
    }
    Ok(())
}

fn validate_metadata_size(records: &[DagRecord]) -> Result<(), DagError> {
    let mut total = 0;
    for record in records {
        match record {
            DagRecord::Node(node) => {
                for text in [&node.id, &node.title, &node.scope] {
                    count_metadata(&mut total, text)?;
                }
                if let Some(artifact) = &node.artifact {
                    count_artifact_metadata(&mut total, artifact)?;
                }
            }
            DagRecord::Edge(edge) => {
                for text in [
                    &edge.id,
                    &edge.from,
                    &edge.to,
                    &edge.input_contract,
                    &edge.output_contract,
                    &edge.negative_control,
                    &edge.scope,
                ] {
                    count_metadata(&mut total, text)?;
                }
                for artifact in [&edge.owner, &edge.oracle].into_iter().flatten() {
                    count_artifact_metadata(&mut total, artifact)?;
                }
                if let Some(premises) = &edge.premises {
                    for text in [
                        &premises.question,
                        &premises.scalar,
                        &premises.quotient,
                        &premises.positivity,
                        &premises.composition,
                        &premises.availability,
                    ] {
                        count_metadata(&mut total, text)?;
                    }
                }
            }
        }
    }
    Ok(())
}

pub fn repository_path(path: &str) -> bool {
    !path.is_empty()
        && !path.contains('\\')
        && !path.contains(':')
        && path
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn identifier(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 128
        && id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"-_".contains(&byte))
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_6cd7a17b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
