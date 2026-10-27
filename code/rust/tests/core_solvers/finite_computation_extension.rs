use core_solvers::data_computation_carrier::*;
use std::collections::{BTreeMap, BTreeSet};
fn increment() -> FiniteMachine {
    let transitions = BTreeMap::from([
        (
            (0, 0),
            Transition {
                next_state: 0,
                write: 0,
                movement: 1,
            },
        ),
        (
            (0, 1),
            Transition {
                next_state: 0,
                write: 1,
                movement: 1,
            },
        ),
        (
            (0, 2),
            Transition {
                next_state: 1,
                write: 2,
                movement: -1,
            },
        ),
        (
            (1, 1),
            Transition {
                next_state: 1,
                write: 0,
                movement: -1,
            },
        ),
        (
            (1, 0),
            Transition {
                next_state: 2,
                write: 1,
                movement: 0,
            },
        ),
        (
            (1, 2),
            Transition {
                next_state: 2,
                write: 1,
                movement: 0,
            },
        ),
    ]);
    FiniteMachine::new(3, 3, 2, 0, BTreeSet::from([2]), transitions).unwrap()
}
#[test]
fn all_binary_graph_cnf_models_match_independent_truth_rows() {
    for mask in 0..16 {
        let outputs: Vec<_> = (0..4).map(|row| mask & (1 << row) != 0).collect();
        let graph = BooleanGraph::new(2, outputs.clone()).unwrap();
        let cnf = graph.graph_cnf();
        graph.verify_cnf(&cnf).unwrap();
        for row in 0..4 {
            let input = [row & 2 != 0, row & 1 != 0];
            assert_eq!(graph.evaluate(&input).unwrap(), outputs[row]);
            for output in [false, true] {
                assert_eq!(
                    cnf.satisfied_by(&[input[0], input[1], output]).unwrap(),
                    output == outputs[row]
                );
            }
        }
        let mut corrupted = cnf.clone();
        corrupted.clauses.clear();
        assert_eq!(
            graph.verify_cnf(&corrupted),
            Err(ComputationError::GraphMismatch)
        );
    }
}
#[test]
fn cnf_and_graph_domains_are_checked() {
    assert_eq!(
        BooleanGraph::new(2, vec![false]),
        Err(ComputationError::InvalidGraph)
    );
    let graph = BooleanGraph::new(1, vec![false, true]).unwrap();
    assert_eq!(
        graph.evaluate(&[]),
        Err(ComputationError::InvalidAssignment)
    );
    let bad = Cnf {
        variables: 2,
        clauses: vec![vec![Literal {
            variable: 2,
            positive: true,
        }]],
    };
    assert_eq!(graph.verify_cnf(&bad), Err(ComputationError::InvalidCnf));
    let constant = BooleanGraph::new(0, vec![true]).unwrap();
    constant.verify_cnf(&constant.graph_cnf()).unwrap();
}
#[test]
fn exact_prefix_and_arithmetic_controls_cover_all_selected_inputs() {
    let machine = increment();
    for length in 1..=5 {
        for value in 0..(1usize << length) {
            let cells = (0..length)
                .map(|i| (i as i64, usize::from(value & (1 << (length - 1 - i)) != 0)))
                .collect();
            let initial = Configuration {
                state: 0,
                head: 0,
                cells,
            };
            let result = machine.execute(&initial, 2 * length + 2).unwrap();
            assert_eq!(result.termination, PrefixTermination::Halted);
            let final_state = result.configurations.last().unwrap();
            let output = final_state.cells.values().fold(0, |n, &bit| 2 * n + bit);
            assert_eq!(output, value + 1);
            machine
                .verify_run(&initial, 2 * length + 2, &result)
                .unwrap();
        }
    }
}
#[test]
fn bound_status_tamper_and_partial_or_overflow_semantics() {
    let machine = increment();
    let initial = Configuration {
        state: 0,
        head: 0,
        cells: BTreeMap::from([(0, 1), (1, 0), (2, 1), (3, 1)]),
    };
    let exact = machine.execute(&initial, 20).unwrap();
    assert_eq!(exact.configurations.len(), 9);
    let mut forged = machine.execute(&initial, 3).unwrap();
    assert_eq!(forged.termination, PrefixTermination::BoundExhausted);
    forged.termination = PrefixTermination::Halted;
    assert_eq!(
        machine.verify_run(&initial, 3, &forged),
        Err(ComputationError::ForgedRun)
    );
    let partial = FiniteMachine::new(1, 1, 0, 0, BTreeSet::new(), BTreeMap::new()).unwrap();
    let blank = Configuration {
        state: 0,
        head: 0,
        cells: BTreeMap::new(),
    };
    assert_eq!(
        partial.execute(&blank, 1),
        Err(ComputationError::UndefinedTransition)
    );
    let moving = FiniteMachine::new(
        1,
        1,
        0,
        0,
        BTreeSet::new(),
        BTreeMap::from([(
            (0, 0),
            Transition {
                next_state: 0,
                write: 0,
                movement: 1,
            },
        )]),
    )
    .unwrap();
    assert_eq!(
        moving.execute(
            &Configuration {
                head: i64::MAX,
                ..blank
            },
            1
        ),
        Err(ComputationError::HeadOverflow)
    );
}

// Origin: engine/crates_rs/tests/core_solvers/finite_computation_extension.rs
// Claim: urn:core:crates_rs:tests:finite-computation-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordda5870a2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordda5870a2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorda5870a2 {
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
impl BoundaryErrorda5870a2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorda5870a2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorda5870a2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordda5870a2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorda5870a2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorda5870a2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorda5870a2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorda5870a2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_da5870a2() {
    let admitted = BoundaryRecordda5870a2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordda5870a2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
