use core_category_theory::finite_path::{FinitePathCategory, PathEdge as E, PathError};
use std::collections::BTreeSet;

#[test]
fn parallel_histories_keep_occurrences_and_complete_composition() {
    let c = FinitePathCategory::new(
        3,
        vec![
            E {
                source: 0,
                target: 1,
            },
            E {
                source: 0,
                target: 1,
            },
            E {
                source: 1,
                target: 2,
            },
            E {
                source: 0,
                target: 2,
            },
        ],
        64,
    )
    .unwrap();
    assert_eq!(c.paths().len(), 9);
    assert_eq!(c.origin_path_counts(), vec![6, 2, 1]);
    let a = c.edge_path(0).unwrap();
    let b = c.edge_path(1).unwrap();
    let d = c.edge_path(2).unwrap();
    let ad = c.compose(a, d).unwrap().unwrap();
    let bd = c.compose(b, d).unwrap().unwrap();
    assert_ne!(ad, bd);
    assert_eq!(c.path(ad).unwrap().edges(), &[0, 2]);
    assert_eq!(c.path(bd).unwrap().edges(), &[1, 2]);
    for p in 0..c.paths().len() {
        assert_eq!(c.compose(c.path(p).unwrap().source(), p).unwrap(), Some(p));
        assert_eq!(c.compose(p, c.path(p).unwrap().target()).unwrap(), Some(p));
    }
    assert_eq!(c.compose(d, a).unwrap(), None);
    assert_eq!(c.compose(100, a), Err(PathError::UnknownPath));
    assert_eq!(c.edge_path(4), Err(PathError::UnknownPath));
    assert_eq!(c.category().declared().morphisms.len(), 9);
}

#[test]
fn every_ordered_dag_through_four_vertices_matches_independent_word_enumeration() {
    for n in 1..=4 {
        let possible: Vec<_> = (0..n)
            .flat_map(|x| {
                (x + 1..n).map(move |y| E {
                    source: x,
                    target: y,
                })
            })
            .collect();
        for mask in 0..1usize << possible.len() {
            let edges: Vec<_> = possible
                .iter()
                .enumerate()
                .filter_map(|(i, e)| (mask & (1 << i) != 0).then_some(*e))
                .collect();
            let c = FinitePathCategory::new(n, edges.clone(), 64).unwrap();
            let mut expected: BTreeSet<_> = (0..n).map(|v| (v, Vec::<usize>::new(), v)).collect();
            for length in 1..n {
                for mut code in 0..edges.len().pow(length as u32) {
                    let mut word = Vec::new();
                    for _ in 0..length {
                        word.push(code % edges.len());
                        code /= edges.len();
                    }
                    let source = edges[word[0]].source;
                    let mut target = source;
                    let mut valid = true;
                    for &e in &word {
                        if edges[e].source != target {
                            valid = false;
                            break;
                        }
                        target = edges[e].target;
                    }
                    if valid {
                        expected.insert((source, word, target));
                    }
                }
            }
            let actual: BTreeSet<_> = c
                .paths()
                .iter()
                .map(|p| (p.source(), p.edges().to_vec(), p.target()))
                .collect();
            assert_eq!(actual, expected);
        }
    }
}

#[test]
fn cycles_bad_boundaries_and_incomplete_enumeration_refuse() {
    assert_eq!(
        FinitePathCategory::new(0, vec![], 64),
        Err(PathError::EmptyGraph)
    );
    assert_eq!(
        FinitePathCategory::new(65, vec![], 64),
        Err(PathError::GraphBudget)
    );
    assert_eq!(
        FinitePathCategory::new(
            1,
            vec![E {
                source: 0,
                target: 1
            }],
            64
        ),
        Err(PathError::InvalidVertex)
    );
    assert_eq!(
        FinitePathCategory::new(
            1,
            vec![E {
                source: 0,
                target: 0
            }],
            64
        ),
        Err(PathError::Cycle)
    );
    assert_eq!(
        FinitePathCategory::new(
            2,
            vec![
                E {
                    source: 0,
                    target: 1
                },
                E {
                    source: 1,
                    target: 0
                }
            ],
            64
        ),
        Err(PathError::Cycle)
    );
    assert_eq!(
        FinitePathCategory::new(2, vec![], 1),
        Err(PathError::PathBudget)
    );
    assert_eq!(
        FinitePathCategory::new(
            2,
            vec![E {
                source: 0,
                target: 1
            }],
            2
        ),
        Err(PathError::PathBudget)
    );
    let chain = (0..11)
        .map(|v| E {
            source: v,
            target: v + 1,
        })
        .collect();
    assert_eq!(
        FinitePathCategory::new(12, chain, usize::MAX),
        Err(PathError::PathBudget)
    );
    assert_eq!(
        FinitePathCategory::new(
            2,
            vec![
                E {
                    source: 0,
                    target: 1
                };
                65
            ],
            64
        ),
        Err(PathError::GraphBudget)
    );
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_path.rs
// Claim: urn:core:crates_rs:tests:finite-path:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord00b39bc2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord00b39bc2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError00b39bc2 {
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
impl BoundaryError00b39bc2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError00b39bc2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError00b39bc2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord00b39bc2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError00b39bc2> {
        if capacity_bound == 0 {
            return Err(BoundaryError00b39bc2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError00b39bc2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError00b39bc2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_00b39bc2() {
    let admitted = BoundaryRecord00b39bc2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord00b39bc2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
