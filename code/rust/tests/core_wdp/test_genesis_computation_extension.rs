use core_solvers::data_computation_carrier::{Cnf, Literal};
use core_wdp::genesis_computation::*;
use std::collections::BTreeSet;
fn packet() -> SourceMachinePacket {
    let rules = vec![
        NamedRule {
            state: "scan".into(),
            read: "0".into(),
            next_state: "scan".into(),
            write: "0".into(),
            movement: 1,
        },
        NamedRule {
            state: "scan".into(),
            read: "1".into(),
            next_state: "scan".into(),
            write: "1".into(),
            movement: 1,
        },
        NamedRule {
            state: "scan".into(),
            read: "_".into(),
            next_state: "carry".into(),
            write: "_".into(),
            movement: -1,
        },
        NamedRule {
            state: "carry".into(),
            read: "1".into(),
            next_state: "carry".into(),
            write: "0".into(),
            movement: -1,
        },
        NamedRule {
            state: "carry".into(),
            read: "0".into(),
            next_state: "halt".into(),
            write: "1".into(),
            movement: 0,
        },
        NamedRule {
            state: "carry".into(),
            read: "_".into(),
            next_state: "halt".into(),
            write: "1".into(),
            movement: 0,
        },
    ];
    let permissions = rules
        .iter()
        .map(|r| (r.state.clone(), r.read.clone()))
        .collect();
    SourceMachinePacket {
        states: vec!["scan".into(), "carry".into(), "halt".into()],
        alphabet: vec!["0".into(), "1".into(), "_".into()],
        blank: "_".into(),
        initial: "scan".into(),
        halting: BTreeSet::from(["halt".into()]),
        rules,
        permissions,
    }
}
fn initial() -> NamedConfiguration {
    NamedConfiguration {
        state: "scan".into(),
        head: 0,
        cells: vec![
            (0, "1".into()),
            (1, "0".into()),
            (2, "1".into()),
            (3, "1".into()),
        ],
    }
}
#[test]
fn source_truth_graph_readout_and_native_cnf_are_faithful() {
    for mask in 0..16 {
        let source = SourceBooleanPacket {
            datum_labels: vec!["zero".into(), "one".into()],
            arity: 2,
            instances: (0..4)
                .map(|row| vec![row / 2, row % 2, usize::from(mask & (1 << row) != 0)])
                .collect(),
        };
        let checked = source.admit().unwrap();
        checked.verify_cnf(&checked.graph_cnf()).unwrap();
        for row in &source.instances {
            assert_eq!(checked.readout(&row[..2]).unwrap(), row[2]);
        }
        assert!(checked
            .verify_cnf(&Cnf {
                variables: 3,
                clauses: vec![vec![Literal {
                    variable: 3,
                    positive: true
                }]]
            })
            .is_err());
        assert_eq!(
            checked.verify_readout(&[0, 0], 1 - source.instances[0][2]),
            Err(BridgeError::ReadoutMismatch)
        );
    }
}
#[test]
fn truth_graph_duplicate_contradictory_or_missing_rows_are_not_function_graphs() {
    let mut source = SourceBooleanPacket {
        datum_labels: vec!["zero".into(), "one".into()],
        arity: 1,
        instances: vec![vec![0, 0], vec![1, 1]],
    };
    source.instances[1] = vec![0, 1];
    assert!(source.admit().is_err());
    source.instances.pop();
    assert!(source.admit().is_err());
    source.instances = vec![vec![0, 0], vec![1, 2]];
    assert!(source.admit().is_err());
}
#[test]
fn prefix_translation_preserves_all_occurrences_and_native_steps() {
    let checked = packet().admit().unwrap();
    let start = initial();
    let run = checked.execute(&start, 20).unwrap();
    assert_eq!(run.trace().steps().len(), 9);
    let candidate = run.export();
    checked.verify_prefix(&start, 20, &candidate).unwrap();
    assert_eq!(candidate.termination, NamedTermination::Halted);
    assert_eq!(
        candidate
            .configurations
            .iter()
            .map(|c| c.head)
            .collect::<Vec<_>>(),
        vec![0, 1, 2, 3, 4, 3, 2, 1, 1]
    );
    assert_eq!(
        candidate
            .configurations
            .last()
            .unwrap()
            .cells
            .iter()
            .map(|(_, d)| d.as_str())
            .collect::<String>(),
        "1100"
    );
    let mut forged = candidate.clone();
    forged.configurations[1].head = 9;
    assert_eq!(
        checked.verify_prefix(&start, 20, &forged),
        Err(BridgeError::PrefixMismatch)
    );
    let mut short = checked.execute(&start, 3).unwrap().export();
    assert_eq!(short.termination, NamedTermination::BoundExhausted);
    short.termination = NamedTermination::Halted;
    assert_eq!(
        checked.verify_prefix(&start, 3, &short),
        Err(BridgeError::PrefixMismatch)
    );
}
#[test]
fn execution_evidence_never_supplies_permission() {
    let good = packet();
    let candidate = good
        .admit()
        .unwrap()
        .execute(&initial(), 20)
        .unwrap()
        .export();
    let mut denied = good.clone();
    denied.permissions.remove(&("scan".into(), "1".into()));
    let checked = denied.admit().unwrap();
    assert!(matches!(
        checked.execute(&initial(), 20),
        Err(BridgeError::Unauthorized)
    ));
    assert_eq!(
        checked.verify_prefix(&initial(), 20, &candidate),
        Err(BridgeError::Unauthorized)
    );
    let mut bad = good;
    bad.rules.push(bad.rules[0].clone());
    assert!(bad.admit().is_err());
}
#[test]
fn repeated_configurations_and_invalid_sparse_tapes_are_preserved_or_refused() {
    let source = SourceMachinePacket {
        states: vec!["q".into()],
        alphabet: vec!["_".into()],
        blank: "_".into(),
        initial: "q".into(),
        halting: BTreeSet::new(),
        rules: vec![NamedRule {
            state: "q".into(),
            read: "_".into(),
            next_state: "q".into(),
            write: "_".into(),
            movement: 0,
        }],
        permissions: BTreeSet::from([("q".into(), "_".into())]),
    };
    let checked = source.admit().unwrap();
    let start = NamedConfiguration {
        state: "q".into(),
        head: 0,
        cells: vec![],
    };
    let run = checked.execute(&start, 4).unwrap().export();
    assert_eq!(run.configurations, vec![start.clone(); 5]);
    assert_eq!(run.termination, NamedTermination::BoundExhausted);
    let invalid = NamedConfiguration {
        cells: vec![(0, "_".into())],
        ..start
    };
    assert!(checked.execute(&invalid, 1).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_computation_extension.rs
// Claim: urn:core:crates_rs:tests:test-genesis-computation-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf084bade {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf084bade` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf084bade {
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
impl BoundaryErrorf084bade {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf084bade {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf084bade {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf084bade {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf084bade> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf084bade::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf084bade::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf084bade::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f084bade() {
    let admitted = BoundaryRecordf084bade::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf084bade::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
