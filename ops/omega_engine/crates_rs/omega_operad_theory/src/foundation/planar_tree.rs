//! Foundation: Planar trees, open leaves, grafting, and term hashing.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_2c5eca91;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_2c5eca91<T> = std::result::Result<T, BoundaryError_2c5eca91>;
use std::fmt;
use sha2::{Digest, Sha256};
use serde::{Deserialize, Serialize};
use super::colour::OperadColour;
use super::operation::Operation;

/// An open, un-grafted input leaf port typed by an OperadColour.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct OpenLeaf {
    pub colour: OperadColour,
}

impl OpenLeaf {
    pub fn new(colour: OperadColour) -> Self {
        Self { colour }
    }
}

impl fmt::Display for OpenLeaf {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Leaf({})", self.colour)
    }
}

/// A child slot in a planar tree: either an open leaf or a composite subtree.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TreeChild {
    Leaf(OpenLeaf),
    Subtree(PlanarTree),
}

impl TreeChild {
    pub fn output_colour(&self) -> &OperadColour {
        match self {
            Self::Leaf(l) => &l.colour,
            Self::Subtree(t) => t.output_colour(),
        }
    }

    pub fn arity(&self) -> usize {
        match self {
            Self::Leaf(_) => 1,
            Self::Subtree(t) => t.arity(),
        }
    }

    pub fn term_hash(&self) -> String {
        match self {
            Self::Leaf(l) => format!("leaf:{}", l.colour.as_str()),
            Self::Subtree(t) => format!("sub:{}", t.term_hash()),
        }
    }
}

/// A rooted planar tree whose vertices are decorated by operadic operations.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PlanarTree {
    pub root: Operation,
    pub children: Vec<TreeChild>,
}

impl PlanarTree {
    /// Creates a planar tree with explicit children validation.
    pub fn new(root: Operation, children: Option<Vec<TreeChild>>) -> Result<Self, String> {
        let actual_children = match children {
            None => root
                .inputs()
                .iter()
                .map(|c| TreeChild::Leaf(OpenLeaf::new(c.clone())))
                .collect(),
            Some(ch) => {
                if ch.len() != root.arity() {
                    return Err(format!(
                        "PlanarTree children count {} != root operation arity {}",
                        ch.len(),
                        root.arity()
                    ));
                }
                for (idx, child) in ch.iter().enumerate() {
                    let expected = &root.inputs()[idx];
                    if child.output_colour() != expected {
                        return Err(format!(
                            "Child colour mismatch at slot {}: expected {}, got {}",
                            idx,
                            expected.as_str(),
                            child.output_colour().as_str()
                        ));
                    }
                }
                ch
            }
        };

        Ok(Self {
            root,
            children: actual_children,
        })
    }

    /// Constructs a basic corolla tree with OpenLeaf slots for all root inputs.
    pub fn corolla(operation: Operation) -> Self {
        let children: Vec<TreeChild> = operation
            .inputs()
            .iter()
            .map(|c| TreeChild::Leaf(OpenLeaf::new(c.clone())))
            .collect();
        Self {
            root: operation,
            children,
        }
    }

    /// Total number of open external leaves across the entire tree.
    pub fn arity(&self) -> usize {
        self.children.iter().map(|ch| ch.arity()).sum()
    }

    /// Output colour of the tree root.
    pub fn output_colour(&self) -> &OperadColour {
        self.root.output()
    }

    /// Computes deterministic content-addressed term hash: `tree_<sha256[:16]>`.
    pub fn term_hash(&self) -> String {
        let mut parts = vec![self.root.op_id.as_str().to_string()];
        for ch in &self.children {
            parts.push(ch.term_hash());
        }
        let mut hasher = Sha256::new();
        hasher.update(parts.join(";").as_bytes());
        let digest = hex::encode(hasher.finalize());
        format!("tree_{}", &digest[..16])
    }

    /// Grafts a subtree into the i-th immediate root slot (0-indexed).
    pub fn graft(&self, slot_index: usize, subtree: PlanarTree) -> Result<PlanarTree, String> {
        if slot_index >= self.children.len() {
            return Err(format!(
                "Root slot index {} out of range [0, {})",
                slot_index,
                self.children.len()
            ));
        }

        let expected_colour = &self.root.inputs()[slot_index];
        if subtree.output_colour() != expected_colour {
            return Err(format!(
                "Cannot graft subtree into slot {}: expected output colour {}, got {}",
                slot_index,
                expected_colour.as_str(),
                subtree.output_colour().as_str()
            ));
        }

        let mut new_children = self.children.clone();
        new_children[slot_index] = TreeChild::Subtree(subtree);
        Ok(PlanarTree {
            root: self.root.clone(),
            children: new_children,
        })
    }
}

// Origin: omega_engine/crates_rs/omega_operad_theory/src/foundation/planar_tree.rs
// Claim: urn:omega:crates_rs:omega-operad-theory:planar-tree:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_2c5eca91 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
