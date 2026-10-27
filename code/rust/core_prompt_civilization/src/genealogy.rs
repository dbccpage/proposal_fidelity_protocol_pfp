//! Inheritance DAG and Reference Graph.
//!
//! Enforces:
//! - F-LINEAGE-01: Edges exist only for witnessed causal relations; matching objectives alone never creates an edge.
//! - F-PHARM-04: Descent follows declared inheritance edges only.
//! - Multi-parent lineage graph traversal bounded by max_depth <= 5.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet, VecDeque};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GenealogyError {
    #[error("DEPTH_BOUND_EXCEEDED: max_depth must be <= 5 (requested: {0})")]
    DepthBoundExceeded(usize),
    #[error("ROOT_NOT_FOUND: Root node '{0}' not found in lineage graph")]
    RootNotFound(String),
    #[error("LINEAGE_CYCLE_REFUSED: Cycle detected in inheritance DAG between {0} and {1}")]
    CycleRefused(String, String),
    #[error("WITNESS_RECEIPT_REQUIRED: Unverified causal edge refused")]
    WitnessReceiptRequired,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum InheritanceRelationship {
    DirectMutation,
    Repair,
    Retry,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InheritanceEdgeV1 {
    pub parent_id: String,
    pub child_id: String,
    pub relationship: InheritanceRelationship,
    pub witness_receipt_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LineageTree {
    pub root_id: String,
    pub max_depth: usize,
    pub ancestors: Vec<String>,
    pub generation_map: HashMap<String, u64>,
    pub depth_layers: Vec<Vec<String>>,
}

#[derive(Debug, Default, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LineageGraphV1 {
    pub forward_edges: HashMap<String, Vec<InheritanceEdgeV1>>,
    pub backward_edges: HashMap<String, Vec<InheritanceEdgeV1>>,
    pub reference_edges: HashMap<String, Vec<String>>,
    pub generations: HashMap<String, u64>,
}

pub type GenealogyGraph = LineageGraphV1;

fn relationship_label(relationship: &InheritanceRelationship) -> &'static str {
    match relationship {
        InheritanceRelationship::DirectMutation => "DirectMutation",
        InheritanceRelationship::Repair => "Repair",
        InheritanceRelationship::Retry => "Retry",
    }
}

/// Digest of the named parent, child, and relationship. A constant hex string is not this digest.
pub fn inheritance_witness_digest(
    parent_id: &str,
    child_id: &str,
    relationship: &InheritanceRelationship,
) -> String {
    let body = serde_json::json!([
        "core.lineage.edge.v1",
        parent_id,
        child_id,
        relationship_label(relationship),
    ])
    .to_string();
    format!("sha256:{}", hex::encode(Sha256::digest(body.as_bytes())))
}

fn sealed_witness_digest(
    parent_id: &str,
    child_id: &str,
    relationship: &InheritanceRelationship,
    digest: &str,
) -> bool {
    const PLACEHOLDER: &str = "sha256:causal_witness_ok";
    if digest.is_empty() || digest == "unverified" || digest == PLACEHOLDER {
        return false;
    }
    let Some(hex_body) = digest.strip_prefix("sha256:") else {
        return false;
    };
    if hex_body.len() != 64
        || !hex_body
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return false;
    }
    digest == inheritance_witness_digest(parent_id, child_id, relationship)
}

impl LineageGraphV1 {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_node(&mut self, node_id: &str, generation: u64) {
        self.generations
            .entry(node_id.to_string())
            .or_insert(generation);
    }

    pub fn has_path(&self, from: &str, to: &str) -> bool {
        if from == to {
            return true;
        }
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        queue.push_back(from.to_string());
        visited.insert(from.to_string());

        while let Some(curr) = queue.pop_front() {
            if curr == to {
                return true;
            }
            if let Some(edges) = self.forward_edges.get(&curr) {
                for edge in edges {
                    if !visited.contains(&edge.child_id) {
                        visited.insert(edge.child_id.clone());
                        queue.push_back(edge.child_id.clone());
                    }
                }
            }
        }
        false
    }

    pub fn add_inheritance_edge(
        &mut self,
        parent_id: &str,
        child_id: &str,
        relationship: InheritanceRelationship,
        witness_receipt_digest: &str,
    ) -> Result<(), String> {
        if parent_id == child_id {
            return Err("LINEAGE_CYCLE_REFUSED: self-edge forbidden".to_string());
        }
        if !sealed_witness_digest(parent_id, child_id, &relationship, witness_receipt_digest) {
            return Err(
                "WITNESS_RECEIPT_REQUIRED: digest does not bind this parent and child"
                    .to_string(),
            );
        }
        // Acyclicity check: if child_id can already reach parent_id, adding parent_id -> child_id creates a cycle!
        if self.has_path(child_id, parent_id) {
            return Err(format!(
                "LINEAGE_CYCLE_REFUSED: Cycle detected in inheritance DAG between {} and {}",
                parent_id, child_id
            ));
        }

        let edge = InheritanceEdgeV1 {
            parent_id: parent_id.to_string(),
            child_id: child_id.to_string(),
            relationship,
            witness_receipt_digest: witness_receipt_digest.to_string(),
        };

        self.forward_edges
            .entry(parent_id.to_string())
            .or_default()
            .push(edge.clone());
        self.backward_edges
            .entry(child_id.to_string())
            .or_default()
            .push(edge);

        // Update child generation: g+1 = max(gen(P_i)) + 1
        let p_gen = self.derive_generation(parent_id);
        let current_c_gen = self.generations.get(child_id).copied().unwrap_or(0);
        let new_c_gen = std::cmp::max(current_c_gen, p_gen + 1);
        self.generations.insert(child_id.to_string(), new_c_gen);

        Ok(())
    }

    pub fn add_reference_edge(&mut self, from_prompt_id: &str, precedent_id: &str) {
        self.reference_edges
            .entry(from_prompt_id.to_string())
            .or_default()
            .push(precedent_id.to_string());
    }

    pub fn get_parents(&self, child_id: &str) -> Vec<String> {
        self.backward_edges
            .get(child_id)
            .map(|edges| edges.iter().map(|e| e.parent_id.clone()).collect())
            .unwrap_or_default()
    }

    pub fn get_children(&self, parent_id: &str) -> Vec<String> {
        self.forward_edges
            .get(parent_id)
            .map(|edges| edges.iter().map(|e| e.child_id.clone()).collect())
            .unwrap_or_default()
    }

    /// Derives the generation number of a node in the DAG:
    /// Base nodes (no parents) have generation equal to their declared generation or 0.
    /// Multi-parent child has generation = max(gen(P_i)) + 1.
    pub fn derive_generation(&self, node_id: &str) -> u64 {
        if let Some(&g) = self.generations.get(node_id) {
            if g > 0 {
                return g;
            }
        }
        let parents = self.get_parents(node_id);
        if parents.is_empty() {
            return *self.generations.get(node_id).unwrap_or(&0);
        }
        let max_p = parents
            .iter()
            .map(|p| self.derive_generation(p))
            .max()
            .unwrap_or(0);
        max_p + 1
    }

    /// Bounded multi-parent ancestor traversal.
    /// Strictly requires max_depth <= 5; refuses depths > 5 with DepthBoundExceeded.
    pub fn traverse_ancestors(
        &self,
        root_id: &str,
        max_depth: usize,
    ) -> Result<HashSet<String>, GenealogyError> {
        if max_depth > 5 {
            return Err(GenealogyError::DepthBoundExceeded(max_depth));
        }

        if !self.backward_edges.contains_key(root_id)
            && !self.forward_edges.contains_key(root_id)
            && !self.generations.contains_key(root_id)
        {
            return Err(GenealogyError::RootNotFound(root_id.to_string()));
        }

        let mut ancestors = HashSet::new();
        ancestors.insert(root_id.to_string());
        let mut current_layer = HashSet::new();
        current_layer.insert(root_id.to_string());

        for _ in 0..max_depth {
            let mut next_layer = HashSet::new();
            for node in &current_layer {
                for parent in self.get_parents(node) {
                    next_layer.insert(parent);
                }
            }
            if next_layer.is_empty() {
                break;
            }
            ancestors.extend(next_layer.iter().cloned());
            current_layer = next_layer;
        }

        Ok(ancestors)
    }

    fn has_node(&self, node_id: &str) -> bool {
        self.backward_edges.contains_key(node_id)
            || self.forward_edges.contains_key(node_id)
            || self.generations.contains_key(node_id)
    }

    fn expand_lineage_layer(
        &self,
        current_layer: &[String],
        visited: &mut HashSet<String>,
    ) -> Vec<String> {
        let mut next_layer = Vec::new();
        for node in current_layer {
            for parent in self.get_parents(node) {
                if visited.insert(parent.clone()) {
                    next_layer.push(parent);
                }
            }
        }
        next_layer.sort();
        next_layer
    }

    /// Complete lineage tree traversal with depth layer decomposition.
    pub fn traverse_lineage(
        &self,
        root_id: &str,
        max_depth: usize,
    ) -> Result<LineageTree, GenealogyError> {
        if max_depth > 5 {
            return Err(GenealogyError::DepthBoundExceeded(max_depth));
        }

        if !self.has_node(root_id) {
            return Err(GenealogyError::RootNotFound(root_id.to_string()));
        }

        let mut depth_layers: Vec<Vec<String>> = Vec::new();
        let mut visited = HashSet::new();
        visited.insert(root_id.to_string());
        let mut current_layer = vec![root_id.to_string()];
        depth_layers.push(current_layer.clone());

        for _ in 0..max_depth {
            let next_layer = self.expand_lineage_layer(&current_layer, &mut visited);
            if next_layer.is_empty() {
                break;
            }
            depth_layers.push(next_layer.clone());
            current_layer = next_layer;
        }

        let mut ancestors: Vec<String> = visited.into_iter().collect();
        ancestors.sort();

        let mut generation_map = HashMap::new();
        for node in &ancestors {
            let gen = self.derive_generation(node);
            generation_map.insert(node.clone(), gen);
        }

        Ok(LineageTree {
            root_id: root_id.to_string(),
            max_depth,
            ancestors,
            generation_map,
            depth_layers,
        })
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/genealogy.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:genealogy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn witness(parent: &str, child: &str) -> String {
        inheritance_witness_digest(parent, child, &InheritanceRelationship::DirectMutation)
    }

    #[test]
    fn test_f_lineage_01_witness_required() {
        let mut g = LineageGraphV1::new();
        let res = g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            "unverified",
        );
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("WITNESS_RECEIPT_REQUIRED"));
        let placeholder = g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            "sha256:causal_witness_ok",
        );
        assert!(placeholder.is_err());
        let short = g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            "sha256:w1",
        );
        assert!(short.is_err());
    }

    #[test]
    fn test_constant_digest_is_not_a_causal_edge() {
        let mut g = LineageGraphV1::new();
        let constant = format!("sha256:{}", "0".repeat(64));
        let res = g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            &constant,
        );
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("WITNESS_RECEIPT_REQUIRED"));
        assert!(g.get_children("A").is_empty());

        let bound = witness("A", "B");
        g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            &bound,
        )
        .unwrap();
        let reused = g.add_inheritance_edge(
            "C",
            "D",
            InheritanceRelationship::DirectMutation,
            &bound,
        );
        assert!(reused.is_err());
        assert!(reused.unwrap_err().contains("WITNESS_RECEIPT_REQUIRED"));
    }

    #[test]
    fn test_cycle_refused() {
        let mut g = LineageGraphV1::new();
        g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            &witness("A", "B"),
        )
        .unwrap();
        let res = g.add_inheritance_edge(
            "B",
            "A",
            InheritanceRelationship::DirectMutation,
            &witness("B", "A"),
        );
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("LINEAGE_CYCLE_REFUSED"));
    }

    #[test]
    fn test_self_edge_refused() {
        let mut g = LineageGraphV1::new();
        let res = g.add_inheritance_edge(
            "A",
            "A",
            InheritanceRelationship::DirectMutation,
            "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        );
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("LINEAGE_CYCLE_REFUSED"));
    }

    #[test]
    fn test_single_parent_descent_chain() {
        let mut g = LineageGraphV1::new();
        for i in 0..4 {
            let parent = format!("g{i}");
            let child = format!("g{}", i + 1);
            g.add_inheritance_edge(
                &parent,
                &child,
                InheritanceRelationship::DirectMutation,
                &witness(&parent, &child),
            )
            .unwrap();
        }
        let ancestors = g.traverse_ancestors("g4", 5).unwrap();
        let expected: HashSet<String> = (0..=4).map(|i| format!("g{i}")).collect();
        assert_eq!(ancestors, expected);
    }

    #[test]
    fn test_multi_parent_crossover_traversal() {
        let mut g = LineageGraphV1::new();
        g.add_inheritance_edge(
            "p1",
            "child",
            InheritanceRelationship::DirectMutation,
            &witness("p1", "child"),
        )
        .unwrap();
        g.add_inheritance_edge(
            "p2",
            "child",
            InheritanceRelationship::DirectMutation,
            &witness("p2", "child"),
        )
        .unwrap();

        let ancestors = g.traverse_ancestors("child", 2).unwrap();
        let expected: HashSet<String> = ["child", "p1", "p2"]
            .iter()
            .map(|s| s.to_string())
            .collect();
        assert_eq!(ancestors, expected);
    }

    #[test]
    fn test_depth_bounded_ancestor_collection() {
        let mut g = LineageGraphV1::new();
        for i in 0..5 {
            let parent = format!("v{i}");
            let child = format!("v{}", i + 1);
            g.add_inheritance_edge(
                &parent,
                &child,
                InheritanceRelationship::DirectMutation,
                &witness(&parent, &child),
            )
            .unwrap();
        }
        // From v5 with depth 2: collects v5, v4, v3
        let res = g.traverse_ancestors("v5", 2).unwrap();
        let expected: HashSet<String> = ["v5", "v4", "v3"].iter().map(|s| s.to_string()).collect();
        assert_eq!(res, expected);
    }

    #[test]
    fn test_depth_exceeded_refusal() {
        let mut g = LineageGraphV1::new();
        g.add_inheritance_edge(
            "A",
            "B",
            InheritanceRelationship::DirectMutation,
            &witness("A", "B"),
        )
        .unwrap();
        // max_depth > 5 must strictly return DepthBoundExceeded error
        let res = g.traverse_ancestors("B", 6);
        assert!(matches!(res, Err(GenealogyError::DepthBoundExceeded(6))));

        let tree_res = g.traverse_lineage("B", 10);
        assert!(matches!(
            tree_res,
            Err(GenealogyError::DepthBoundExceeded(10))
        ));
    }

    #[test]
    fn test_generation_number_derivation() {
        let mut g = LineageGraphV1::new();
        g.add_node("p_gen1", 1);
        g.add_node("p_gen3", 3);
        g.add_inheritance_edge(
            "p_gen1",
            "hybrid",
            InheritanceRelationship::DirectMutation,
            &witness("p_gen1", "hybrid"),
        )
        .unwrap();
        g.add_inheritance_edge(
            "p_gen3",
            "hybrid",
            InheritanceRelationship::DirectMutation,
            &witness("p_gen3", "hybrid"),
        )
        .unwrap();

        assert_eq!(g.derive_generation("hybrid"), 4);
    }
}
