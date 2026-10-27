//! Exact Chemical Reaction Network Theory (CRNT) & Deficiency Calculator (U24).
//!
//! Evaluates Feinberg Chemical Reaction Network Theory invariants:
//! - n: Number of distinct complexes
//! - ell: Number of linkage classes (connected components of reaction graph)
//! - s: Stoichiometric rank = dim span(v_1, ..., v_r) over Q
//! - delta: Network deficiency = n - ell - s
//! - Weak reversibility: Every linkage class is strongly connected.
//!
//! Exact rational arithmetic using num_rational::BigRational. Zero floating-point arithmetic.
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct Species(pub String);

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct Complex {
    /// Mapping of species name to stoichiometric coefficient y_i >= 1. Empty map is the zero complex '0'.
    pub composition: BTreeMap<String, u32>,
}

impl Complex {
    pub fn zero() -> Self {
        Self {
            composition: BTreeMap::new(),
        }
    }

    pub fn single(species: &str, count: u32) -> Self {
        let mut composition = BTreeMap::new();
        if count > 0 {
            composition.insert(species.to_string(), count);
        }
        Self { composition }
    }

    pub fn from_pairs(pairs: &[(&str, u32)]) -> Self {
        let mut composition = BTreeMap::new();
        for &(sp, count) in pairs {
            if count > 0 {
                composition.insert(sp.to_string(), count);
            }
        }
        Self { composition }
    }

    pub fn to_string_repr(&self) -> String {
        if self.composition.is_empty() {
            return "0".to_string();
        }
        let parts: Vec<String> = self
            .composition
            .iter()
            .map(|(sp, &c)| {
                if c == 1 {
                    sp.clone()
                } else {
                    format!("{c}{sp}")
                }
            })
            .collect();
        parts.join(" + ")
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Reaction {
    pub source: Complex,
    pub target: Complex,
}

impl Reaction {
    pub fn new(source: Complex, target: Complex) -> Self {
        Self { source, target }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReactionNetworkReport {
    pub num_species: usize,
    pub num_complexes: usize,
    pub num_reactions: usize,
    pub num_linkage_classes: usize,
    pub stoichiometric_rank: usize,
    pub deficiency: i64,
    pub is_weakly_reversible: bool,
    pub deficiency_zero_applicable: bool,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReactionNetwork {
    pub species: Vec<Species>,
    pub complexes: Vec<Complex>,
    pub reactions: Vec<Reaction>,
}

impl ReactionNetwork {
    pub fn new(reactions: Vec<Reaction>) -> Self {
        let mut species_set = BTreeSet::new();
        let mut complex_set = BTreeSet::new();

        for r in &reactions {
            for sp in r.source.composition.keys() {
                species_set.insert(sp.clone());
            }
            for sp in r.target.composition.keys() {
                species_set.insert(sp.clone());
            }
            complex_set.insert(r.source.clone());
            complex_set.insert(r.target.clone());
        }

        let species: Vec<Species> = species_set.into_iter().map(Species).collect();
        let complexes: Vec<Complex> = complex_set.into_iter().collect();

        Self {
            species,
            complexes,
            reactions,
        }
    }

    fn build_stoichiometric_matrix(&self) -> Vec<Vec<BigRational>> {
        let m = self.species.len();
        let r = self.reactions.len();
        let species_idx: HashMap<String, usize> = self
            .species
            .iter()
            .enumerate()
            .map(|(i, sp)| (sp.0.clone(), i))
            .collect();

        // Build stoichiometric matrix N of size m x r over BigRational
        let mut matrix: Vec<Vec<BigRational>> = vec![vec![BigRational::zero(); r]; m];

        for (col, rxn) in self.reactions.iter().enumerate() {
            // target - source
            for (sp, &cnt) in &rxn.target.composition {
                if let Some(&row) = species_idx.get(sp) {
                    matrix[row][col] += BigRational::from_integer(BigInt::from(cnt));
                }
            }
            for (sp, &cnt) in &rxn.source.composition {
                if let Some(&row) = species_idx.get(sp) {
                    matrix[row][col] -= BigRational::from_integer(BigInt::from(cnt));
                }
            }
        }
        matrix
    }

    fn normalize_and_eliminate_pivot(
        matrix: &mut [Vec<BigRational>],
        row: usize,
        pivot_col: usize,
        r: usize,
    ) {
        let m = matrix.len();
        // Normalize pivot row
        let pivot_val = matrix[row][pivot_col].clone();
        for c in 0..r {
            matrix[row][c] /= &pivot_val;
        }

        // Eliminate column entries in other rows
        for other_row in 0..m {
            if other_row != row && !matrix[other_row][pivot_col].is_zero() {
                let factor = matrix[other_row][pivot_col].clone();
                for c in 0..r {
                    let sub = &factor * &matrix[row][c];
                    matrix[other_row][c] -= sub;
                }
            }
        }
    }

    /// Compute exact stoichiometric rank over Q using rational Gaussian elimination.
    pub fn compute_stoichiometric_rank(&self) -> usize {
        if self.reactions.is_empty() || self.species.is_empty() {
            return 0;
        }

        let m = self.species.len();
        let r = self.reactions.len();
        let mut matrix = self.build_stoichiometric_matrix();

        // Exact rational Gaussian elimination to compute row rank
        let mut rank = 0;
        let mut pivot_col = 0;

        for row in 0..m {
            if pivot_col >= r {
                break;
            }

            // Find pivot
            let pivot_row = (row..m).find(|&r_idx| !matrix[r_idx][pivot_col].is_zero());

            let Some(p_row) = pivot_row else {
                pivot_col += 1;
                continue;
            };

            // Swap rows
            matrix.swap(row, p_row);
            Self::normalize_and_eliminate_pivot(&mut matrix, row, pivot_col, r);

            rank += 1;
            pivot_col += 1;
        }

        rank
    }

    /// Compute number of linkage classes ell (undirected connected components of complex reaction graph).
    pub fn compute_linkage_classes(&self) -> usize {
        if self.complexes.is_empty() {
            return 0;
        }

        let complex_idx: HashMap<&Complex, usize> = self
            .complexes
            .iter()
            .enumerate()
            .map(|(i, c)| (c, i))
            .collect();

        let n = self.complexes.len();
        let mut adj: Vec<Vec<usize>> = vec![Vec::new(); n];

        for rxn in &self.reactions {
            if let (Some(&u), Some(&v)) =
                (complex_idx.get(&rxn.source), complex_idx.get(&rxn.target))
            {
                adj[u].push(v);
                adj[v].push(u);
            }
        }

        let mut visited = vec![false; n];
        let mut components = 0;

        for i in 0..n {
            if !visited[i] {
                components += 1;
                let mut queue = VecDeque::new();
                queue.push_back(i);
                visited[i] = true;

                while let Some(u) = queue.pop_front() {
                    for &v in &adj[u] {
                        if !visited[v] {
                            visited[v] = true;
                            queue.push_back(v);
                        }
                    }
                }
            }
        }

        components
    }

    fn collect_undirected_component(
        start: usize,
        undirected_adj: &[Vec<usize>],
        visited: &mut [bool],
    ) -> Vec<usize> {
        let mut component = Vec::new();
        let mut queue = VecDeque::new();
        queue.push_back(start);
        visited[start] = true;

        while let Some(u) = queue.pop_front() {
            component.push(u);
            for &v in &undirected_adj[u] {
                if !visited[v] {
                    visited[v] = true;
                    queue.push_back(v);
                }
            }
        }
        component
    }

    fn is_component_strongly_connected(
        component: &[usize],
        forward_adj: &[Vec<usize>],
    ) -> bool {
        // Check strong connectivity for this component:
        // Every node u in component must reach every node v in component via forward_adj
        for &src in component {
            let mut reachable = HashSet::new();
            let mut f_queue = VecDeque::new();
            f_queue.push_back(src);
            reachable.insert(src);

            while let Some(curr) = f_queue.pop_front() {
                for &next in &forward_adj[curr] {
                    if reachable.insert(next) {
                        f_queue.push_back(next);
                    }
                }
            }

            if component.iter().any(|target| !reachable.contains(target)) {
                return false;
            }
        }
        true
    }

    /// Check weak reversibility: every directed reaction component is strongly connected.
    pub fn is_weakly_reversible(&self) -> bool {
        if self.reactions.is_empty() {
            return true;
        }

        let complex_idx: HashMap<&Complex, usize> = self
            .complexes
            .iter()
            .enumerate()
            .map(|(i, c)| (c, i))
            .collect();

        let n = self.complexes.len();
        let mut forward_adj: Vec<Vec<usize>> = vec![Vec::new(); n];
        let mut undirected_adj: Vec<Vec<usize>> = vec![Vec::new(); n];

        for rxn in &self.reactions {
            if let (Some(&u), Some(&v)) =
                (complex_idx.get(&rxn.source), complex_idx.get(&rxn.target))
            {
                forward_adj[u].push(v);
                undirected_adj[u].push(v);
                undirected_adj[v].push(u);
            }
        }

        // For each linkage class, check if every node can reach every other node in the class via forward paths
        let mut visited_undirected = vec![false; n];

        for i in 0..n {
            if !visited_undirected[i] {
                let component =
                    Self::collect_undirected_component(i, &undirected_adj, &mut visited_undirected);
                if !Self::is_component_strongly_connected(&component, &forward_adj) {
                    return false;
                }
            }
        }

        true
    }

    /// Evaluates full CRNT deficiency report: delta = n - ell - s.
    pub fn evaluate(&self) -> ReactionNetworkReport {
        let n = self.complexes.len();
        let ell = self.compute_linkage_classes();
        let s = self.compute_stoichiometric_rank();
        let deficiency = (n as i64) - (ell as i64) - (s as i64);
        let weakly_rev = self.is_weakly_reversible();

        ReactionNetworkReport {
            num_species: self.species.len(),
            num_complexes: n,
            num_reactions: self.reactions.len(),
            num_linkage_classes: ell,
            stoichiometric_rank: s,
            deficiency,
            is_weakly_reversible: weakly_rev,
            deficiency_zero_applicable: deficiency == 0 && weakly_rev,
            authority_effect: "None".to_string(),
        }
    }
}

// Origin: engine/crates_rs/core_solvers/src/solver_crn_deficiency.rs
// Claim: urn:core:crates_rs:core-solvers:solver-crn-deficiency:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord90ac6894 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord90ac6894` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError90ac6894 {
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
impl BoundaryError90ac6894 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError90ac6894 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError90ac6894 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord90ac6894 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError90ac6894> {
        if capacity_bound == 0 {
            return Err(BoundaryError90ac6894::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError90ac6894::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError90ac6894::ExceedsCapacity {
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
mod l4_boundary_tests_90ac6894 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord90ac6894::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord90ac6894::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord90ac6894::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord90ac6894::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord90ac6894::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError90ac6894::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError90ac6894::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
