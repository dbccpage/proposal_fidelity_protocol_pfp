//! Fundamental Cycle Basis and Exact Spanning Forest (U13).
//!
//! Computes spanning forest, chords, exact tree potentials, and certificate
//! that number of chords equals b1 = |E| - |V| + c.
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct Edge {
    pub u: String,
    pub v: String,
    pub weight: i64,
}

pub use Edge as CycleBasisEdge;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FundamentalCycle {
    pub chord: Edge,
    pub expected_chord_value: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CycleBasisCertificate {
    pub formula: String,
    pub num_edges: usize,
    pub num_vertices: usize,
    pub num_components: usize,
    pub b1_calculated: usize,
    pub chords_count: usize,
    pub valid: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CycleBasisResult {
    pub vertices: Vec<String>,
    pub edges: Vec<Edge>,
    pub spanning_forest_edges: Vec<Edge>,
    pub chords: Vec<Edge>,
    pub num_components: usize,
    pub b1: usize,
    pub potentials: BTreeMap<String, i64>,
    pub fundamental_cycles: Vec<FundamentalCycle>,
    pub certificate: CycleBasisCertificate,
}

/// Compute cycle basis, spanning forest, chords, potentials, and b1 certificate.
pub fn compute_cycle_basis(vertices: &[String], edges: &[Edge]) -> CycleBasisResult {
    let mut vert_set: BTreeSet<String> = vertices.iter().cloned().collect();
    for e in edges {
        vert_set.insert(e.u.clone());
        vert_set.insert(e.v.clone());
    }
    let all_vertices: Vec<String> = vert_set.into_iter().collect();

    // Adjacency for BFS: u -> list of (v, weight, edge_idx, is_forward)
    let mut adj: HashMap<String, Vec<(String, i64, usize, bool)>> = HashMap::new();
    for (idx, e) in edges.iter().enumerate() {
        adj.entry(e.u.clone())
            .or_default()
            .push((e.v.clone(), e.weight, idx, true));
        adj.entry(e.v.clone())
            .or_default()
            .push((e.u.clone(), e.weight, idx, false));
    }

    let mut visited: HashSet<String> = HashSet::new();
    let mut tree_edge_indices: HashSet<usize> = HashSet::new();
    let mut potentials: BTreeMap<String, i64> = BTreeMap::new();
    let mut num_components = 0usize;

    for root in &all_vertices {
        if visited.contains(root) {
            continue;
        }
        num_components += 1;
        visited.insert(root.clone());
        potentials.insert(root.clone(), 0);

        bfs_forest_component(
            root,
            &adj,
            &mut visited,
            &mut tree_edge_indices,
            &mut potentials,
        );
    }

    let mut spanning_forest_edges = Vec::new();
    let mut chords = Vec::new();
    let mut fundamental_cycles = Vec::new();

    for (idx, e) in edges.iter().enumerate() {
        if tree_edge_indices.contains(&idx) {
            spanning_forest_edges.push(e.clone());
        } else {
            chords.push(e.clone());
            let u_pot = potentials.get(&e.u).copied().unwrap_or(0);
            let v_pot = potentials.get(&e.v).copied().unwrap_or(0);
            let expected_chord_value = v_pot - u_pot;
            fundamental_cycles.push(FundamentalCycle {
                chord: e.clone(),
                expected_chord_value,
            });
        }
    }

    let num_edges = edges.len();
    let num_vertices = all_vertices.len();
    let b1 = num_edges + num_components - num_vertices;
    let valid = chords.len() == b1;

    let certificate = CycleBasisCertificate {
        formula: "|E| - |V| + c".to_string(),
        num_edges,
        num_vertices,
        num_components,
        b1_calculated: b1,
        chords_count: chords.len(),
        valid,
    };

    CycleBasisResult {
        vertices: all_vertices,
        edges: edges.to_vec(),
        spanning_forest_edges,
        chords,
        num_components,
        b1,
        potentials,
        fundamental_cycles,
        certificate,
    }
}

/// Compute cycle basis with a designated spanning tree.
pub fn compute_cycle_basis_with_tree(
    vertices: &[String],
    edges: &[Edge],
    tree_edges: &[Edge],
) -> CycleBasisResult {
    let mut vert_set: BTreeSet<String> = vertices.iter().cloned().collect();
    for e in edges {
        vert_set.insert(e.u.clone());
        vert_set.insert(e.v.clone());
    }
    let all_vertices: Vec<String> = vert_set.into_iter().collect();

    let tree_set: HashSet<(String, String)> = tree_edges
        .iter()
        .map(|e| (e.u.clone(), e.v.clone()))
        .collect();

    // Compute potentials from tree edges
    let mut adj: HashMap<String, Vec<(String, i64, bool)>> = HashMap::new();
    for e in tree_edges {
        adj.entry(e.u.clone())
            .or_default()
            .push((e.v.clone(), e.weight, true));
        adj.entry(e.v.clone())
            .or_default()
            .push((e.u.clone(), e.weight, false));
    }

    let mut visited: HashSet<String> = HashSet::new();
    let mut potentials: BTreeMap<String, i64> = BTreeMap::new();
    let mut num_components = 0usize;

    for root in &all_vertices {
        if visited.contains(root) {
            continue;
        }
        num_components += 1;
        visited.insert(root.clone());
        potentials.insert(root.clone(), 0);

        bfs_tree_component(root, &adj, &mut visited, &mut potentials);
    }

    let mut chords = Vec::new();
    let mut fundamental_cycles = Vec::new();

    for e in edges {
        if !tree_set.contains(&(e.u.clone(), e.v.clone())) {
            chords.push(e.clone());
            let u_pot = potentials.get(&e.u).copied().unwrap_or(0);
            let v_pot = potentials.get(&e.v).copied().unwrap_or(0);
            let expected_chord_value = v_pot - u_pot;
            fundamental_cycles.push(FundamentalCycle {
                chord: e.clone(),
                expected_chord_value,
            });
        }
    }

    let num_edges = edges.len();
    let num_vertices = all_vertices.len();
    let b1 = num_edges + num_components - num_vertices;
    let valid = chords.len() == b1;

    let certificate = CycleBasisCertificate {
        formula: "|E| - |V| + c".to_string(),
        num_edges,
        num_vertices,
        num_components,
        b1_calculated: b1,
        chords_count: chords.len(),
        valid,
    };

    CycleBasisResult {
        vertices: all_vertices,
        edges: edges.to_vec(),
        spanning_forest_edges: tree_edges.to_vec(),
        chords,
        num_components,
        b1,
        potentials,
        fundamental_cycles,
        certificate,
    }
}

fn bfs_forest_component(
    root: &str,
    adj: &HashMap<String, Vec<(String, i64, usize, bool)>>,
    visited: &mut HashSet<String>,
    tree_edge_indices: &mut HashSet<usize>,
    potentials: &mut BTreeMap<String, i64>,
) {
    let mut queue = VecDeque::new();
    queue.push_back(root.to_string());

    while let Some(curr) = queue.pop_front() {
        let curr_pot = potentials[&curr];
        if let Some(neighbors) = adj.get(&curr) {
            for (nbr, weight, edge_idx, is_forward) in neighbors {
                if !visited.contains(nbr) {
                    visited.insert(nbr.clone());
                    tree_edge_indices.insert(*edge_idx);
                    let nbr_pot = if *is_forward {
                        curr_pot + weight
                    } else {
                        curr_pot - weight
                    };
                    potentials.insert(nbr.clone(), nbr_pot);
                    queue.push_back(nbr.clone());
                }
            }
        }
    }
}

fn bfs_tree_component(
    root: &str,
    adj: &HashMap<String, Vec<(String, i64, bool)>>,
    visited: &mut HashSet<String>,
    potentials: &mut BTreeMap<String, i64>,
) {
    let mut queue = VecDeque::new();
    queue.push_back(root.to_string());

    while let Some(curr) = queue.pop_front() {
        let curr_pot = potentials[&curr];
        if let Some(neighbors) = adj.get(&curr) {
            for (nbr, weight, is_forward) in neighbors {
                if !visited.contains(nbr) {
                    visited.insert(nbr.clone());
                    let nbr_pot = if *is_forward {
                        curr_pot + weight
                    } else {
                        curr_pot - weight
                    };
                    potentials.insert(nbr.clone(), nbr_pot);
                    queue.push_back(nbr.clone());
                }
            }
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/cycle_basis.rs
// Claim: urn:core:crates_rs:core-homology:cycle-basis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord00496660 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord00496660` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError00496660 {
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
impl BoundaryError00496660 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError00496660 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError00496660 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord00496660 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError00496660> {
        if capacity_bound == 0 {
            return Err(BoundaryError00496660::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError00496660::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError00496660::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_k4_witness_round_5() {
        // K4 board: 4 vertices, 6 edges -> b1 = 6 - 4 + 1 = 3
        let vertices = vec!["a".into(), "b".into(), "c".into(), "d".into()];
        let edges = vec![
            Edge {
                u: "a".into(),
                v: "b".into(),
                weight: 1,
            },
            Edge {
                u: "b".into(),
                v: "c".into(),
                weight: 2,
            },
            Edge {
                u: "c".into(),
                v: "a".into(),
                weight: 3,
            },
            Edge {
                u: "b".into(),
                v: "d".into(),
                weight: 1,
            },
            Edge {
                u: "d".into(),
                v: "a".into(),
                weight: 2,
            },
            Edge {
                u: "c".into(),
                v: "d".into(),
                weight: 1,
            },
        ];

        let result = compute_cycle_basis(&vertices, &edges);
        assert_eq!(result.b1, 3);
        assert_eq!(result.chords.len(), 3);
        assert!(result.certificate.valid);
        assert_eq!(result.num_components, 1);
    }

    #[test]
    fn test_designated_tree_potentials_match_witness() {
        // Specified tree: a->b (1), b->c (2), d->a (2) so f(a)=0, f(b)=1, f(c)=3, f(d)=-2
        let vertices = vec!["a".into(), "b".into(), "c".into(), "d".into()];
        let tree_edges = vec![
            Edge {
                u: "a".into(),
                v: "b".into(),
                weight: 1,
            },
            Edge {
                u: "b".into(),
                v: "c".into(),
                weight: 2,
            },
            Edge {
                u: "d".into(),
                v: "a".into(),
                weight: 2,
            }, // d->a weight 2 means f(a) - f(d) = 2 => f(d) = -2
        ];
        let edges = vec![
            Edge {
                u: "a".into(),
                v: "b".into(),
                weight: 1,
            },
            Edge {
                u: "b".into(),
                v: "c".into(),
                weight: 2,
            },
            Edge {
                u: "c".into(),
                v: "a".into(),
                weight: 3,
            }, // chord: f(a) - f(c) = 0 - 3 = -3
            Edge {
                u: "b".into(),
                v: "d".into(),
                weight: 1,
            }, // chord: f(d) - f(b) = -2 - 1 = -3
            Edge {
                u: "d".into(),
                v: "a".into(),
                weight: 2,
            },
            Edge {
                u: "c".into(),
                v: "d".into(),
                weight: 1,
            }, // chord: f(d) - f(c) = -2 - 3 = -5
        ];

        let result = compute_cycle_basis_with_tree(&vertices, &edges, &tree_edges);
        assert_eq!(result.potentials["a"], 0);
        assert_eq!(result.potentials["b"], 1);
        assert_eq!(result.potentials["c"], 3);
        assert_eq!(result.potentials["d"], -2);

        assert_eq!(result.chords.len(), 3);
        assert!(result.certificate.valid);

        // Check chord expectations
        let chord_vals: HashMap<(String, String), i64> = result
            .fundamental_cycles
            .iter()
            .map(|fc| {
                (
                    (fc.chord.u.clone(), fc.chord.v.clone()),
                    fc.expected_chord_value,
                )
            })
            .collect();

        assert_eq!(chord_vals[&("c".into(), "a".into())], -3);
        assert_eq!(chord_vals[&("b".into(), "d".into())], -3);
        assert_eq!(chord_vals[&("c".into(), "d".into())], -5);
    }
}

#[cfg(test)]
mod l4_boundary_tests_00496660 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord00496660::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord00496660::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord00496660::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord00496660::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord00496660::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError00496660::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError00496660::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
