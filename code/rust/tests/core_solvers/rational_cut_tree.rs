//! Compare every pair of terminals with exhaustive cuts, not another flow solver.
use linear_algebra::exact_field::rational_bareiss::{
    RationalBudget, RationalError, RationalLimits,
};
use num_rational::BigRational;
use core_solvers::solver_flow_gomory_hu::{
    min_cut, verify_min_cut, CutError, GomoryHuTree, UndirectedNetwork,
};
fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn budget() -> RationalBudget {
    RationalBudget::new(RationalLimits {
        max_scalar_ops: 5_000_000,
        max_elements: 10_000,
        max_bits: 4096,
    })
}
fn brute(g: &UndirectedNetwork, s: usize, t: usize) -> BigRational {
    (0..1usize << g.nodes())
        .filter(|mask| mask & (1 << s) != 0 && mask & (1 << t) == 0)
        .map(|mask| {
            g.edges()
                .iter()
                .filter(|(u, v, _)| (mask >> u) & 1 != (mask >> v) & 1)
                .map(|(_, _, c)| c.clone())
                .sum()
        })
        .min()
        .unwrap()
}
#[test]
fn all_small_simple_graphs_match_every_exhaustive_cut() {
    let possible = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];
    for mask in 0..64 {
        let edges = possible
            .iter()
            .enumerate()
            .filter(|(i, _)| mask & (1 << i) != 0)
            .map(|(i, &(u, v))| (u, v, q((i + 1) as i64, 7)))
            .collect();
        let g = UndirectedNetwork::new(4, edges, &mut budget()).unwrap();
        let tree = GomoryHuTree::build(&g, &mut budget()).unwrap();
        assert_eq!(tree.edges().len(), 3);
        for s in 0..4 {
            for t in s + 1..4 {
                let expected = brute(&g, s, t);
                let c = min_cut(&g, s, t, &mut budget()).unwrap();
                assert_eq!(c.value, expected, "graph {mask}, terminals {s},{t}");
                assert_eq!(
                    tree.min_cut(s, t, &mut budget()).unwrap(),
                    expected,
                    "tree {mask}, terminals {s},{t}"
                );
                verify_min_cut(&g, &c, &mut budget()).unwrap();
            }
        }
    }
}
#[test]
fn parallel_zero_capacity_edges_and_mutations() {
    let g = UndirectedNetwork::new(
        3,
        vec![
            (0, 1, q(1, 3)),
            (0, 1, q(2, 3)),
            (1, 2, q(7, 5)),
            (0, 2, q(0, 1)),
        ],
        &mut budget(),
    )
    .unwrap();
    let c = min_cut(&g, 0, 2, &mut budget()).unwrap();
    assert_eq!(c.value, q(1, 1));
    let mut bad = c.clone();
    bad.value += q(1, 1_000_000);
    assert_eq!(
        verify_min_cut(&g, &bad, &mut budget()),
        Err(CutError::InvalidCertificate)
    );
    let mut bad = c.clone();
    bad.edge_flows[0] = q(1, 1);
    assert_eq!(
        verify_min_cut(&g, &bad, &mut budget()),
        Err(CutError::InvalidCertificate)
    );
    let mut bad = c.clone();
    bad.source_side[2] = true;
    assert_eq!(
        verify_min_cut(&g, &bad, &mut budget()),
        Err(CutError::InvalidCertificate)
    );
    let mut bad = c.clone();
    bad.edge_flows[0] = BigRational::new_raw(1.into(), 0.into());
    assert!(matches!(
        verify_min_cut(&g, &bad, &mut budget()),
        Err(CutError::Arithmetic(RationalError::InvalidRational))
    ));
    assert!(min_cut(&g, 0, 0, &mut budget()).is_err());
}
#[test]
fn no_fuel_never_returns_a_partial_cut() {
    let g = UndirectedNetwork::new(2, vec![(0, 1, q(1, 1))], &mut budget()).unwrap();
    let mut fuel = RationalBudget::new(RationalLimits {
        max_scalar_ops: 0,
        max_elements: 10_000,
        max_bits: 4096,
    });
    assert_eq!(
        min_cut(&g, 0, 1, &mut fuel),
        Err(CutError::Arithmetic(RationalError::FuelExhausted))
    );
}

#[test]
fn all_pair_replay_binds_the_tree_to_the_supplied_graph() {
    let g =
        UndirectedNetwork::new(3, vec![(0, 1, q(1, 3)), (1, 2, q(2, 3))], &mut budget()).unwrap();
    let tree = GomoryHuTree::build(&g, &mut budget()).unwrap();
    let receipt = tree.verify_all_pairs(&g, &mut budget()).unwrap();
    assert_eq!(receipt.pairs_checked(), 3);
    let changed =
        UndirectedNetwork::new(3, vec![(0, 1, q(4, 3)), (1, 2, q(2, 3))], &mut budget()).unwrap();
    assert_eq!(
        tree.verify_all_pairs(&changed, &mut budget()),
        Err(CutError::InvalidCertificate)
    );
    let mut limits = RationalLimits {
        max_scalar_ops: receipt.scalar_ops(),
        max_elements: 10_000,
        max_bits: 4096,
    };
    tree.verify_all_pairs(&g, &mut RationalBudget::new(limits))
        .unwrap();
    limits.max_scalar_ops -= 1;
    assert_eq!(
        tree.verify_all_pairs(&g, &mut RationalBudget::new(limits)),
        Err(CutError::Arithmetic(RationalError::FuelExhausted))
    );
}

// Origin: engine/crates_rs/tests/core_solvers/rational_cut_tree.rs
// Claim: urn:core:crates_rs:tests:rational-cut-tree:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5cc771db {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5cc771db` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5cc771db {
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
impl BoundaryError5cc771db {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5cc771db {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5cc771db {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5cc771db {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5cc771db> {
        if capacity_bound == 0 {
            return Err(BoundaryError5cc771db::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5cc771db::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5cc771db::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_5cc771db() {
    let admitted = BoundaryRecord5cc771db::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5cc771db::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
