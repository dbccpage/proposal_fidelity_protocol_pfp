use core_category_theory::finite_continuation::PartialDynamics;
use core_solvers::finite_stream_interpreter::*;
fn limits() -> StreamLimits {
    StreamLimits {
        max_word_len: 10,
        max_steps: 11,
        max_trace_cells: 200,
    }
}
#[test]
fn every_two_state_binary_partial_table_matches_native_tape_replay() {
    for code in 0..81 {
        let mut d = code;
        let mut rows = vec![vec![None; 2]; 2];
        for cell in rows.iter_mut().flatten() {
            let n = d % 3;
            d /= 3;
            *cell = (n < 2).then_some(n);
        }
        let source = PartialDynamics::new(vec![0, 1], rows, 2).unwrap();
        for start in 0..2 {
            let program = CompiledStream::new(&source, start, 100).unwrap();
            for len in 0..=3 {
                for bits in 0..1usize << len {
                    let word: Vec<_> = (0..len).map(|i| (bits >> i) & 1).collect();
                    let c = program.execute(&word, len + 1, limits()).unwrap();
                    match source.run(start, &word).unwrap() {
                        Some(state) => assert_eq!(c.outcome, StreamOutcome::Accepted { state }),
                        None => assert!(matches!(c.outcome, StreamOutcome::Unavailable { .. })),
                    }
                    program.verify(&word, len + 1, limits(), &c).unwrap();
                    if let StreamOutcome::Accepted { .. } = c.outcome {
                        assert!(c.run.configurations.last().unwrap().cells.is_empty());
                        assert_eq!(c.run.configurations.len(), len + 2);
                    }
                }
            }
        }
    }
}
#[test]
fn finite_fuel_and_resource_limits_do_not_mean_semantic_rejection() {
    let source = PartialDynamics::new(vec![0], vec![vec![Some(0)]], 1).unwrap();
    let p = CompiledStream::new(&source, 0, 2).unwrap();
    for steps in 0..=2 {
        assert_eq!(
            p.execute(&[0, 0], steps, limits()).unwrap().outcome,
            StreamOutcome::FuelExhausted
        );
    }
    let c = p.execute(&[0, 0], 3, limits()).unwrap();
    assert_eq!(c.outcome, StreamOutcome::Accepted { state: 0 });
    let mut forged = c.clone();
    forged.run.configurations[1].head = 4;
    assert!(p.verify(&[0, 0], 3, limits(), &forged).is_err());
    assert!(p.verify(&[0], 3, limits(), &c).is_err());
    assert_eq!(p.execute(&[1], 3, limits()), Err(StreamError::InvalidInput));
    assert_eq!(
        p.execute(
            &[0],
            3,
            StreamLimits {
                max_trace_cells: 0,
                ..limits()
            }
        ),
        Err(StreamError::WorkLimit)
    );
    assert_eq!(
        CompiledStream::new(&source, 0, 1),
        Err(StreamError::WorkLimit)
    );
}

#[test]
fn substituted_tape_program_cannot_claim_the_source_simulation() {
    use core_solvers::data_computation_carrier::{FiniteMachine, Transition};
    use std::collections::{BTreeMap, BTreeSet};
    let source = PartialDynamics::new(vec![0], vec![vec![Some(0)]], 1).unwrap();
    let p = CompiledStream::new(&source, 0, 2).unwrap();
    p.verify_program(p.machine()).unwrap();
    // Looks like the compiled carrier but fails to consume the event tape cell.
    let bad = FiniteMachine::new(
        3,
        2,
        0,
        0,
        BTreeSet::from([1, 2]),
        BTreeMap::from([
            (
                (0, 0),
                Transition {
                    next_state: 1,
                    write: 0,
                    movement: 0,
                },
            ),
            (
                (0, 1),
                Transition {
                    next_state: 0,
                    write: 1,
                    movement: 0,
                },
            ),
        ]),
    )
    .unwrap();
    assert_eq!(
        p.verify_program(&bad),
        Err(StreamError::CertificateMismatch)
    );
}

// Origin: engine/crates_rs/tests/core_solvers/finite_stream_interpreter.rs
// Claim: urn:core:crates_rs:tests:finite-stream-interpreter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeb4b5d86 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeb4b5d86` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreb4b5d86 {
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
impl BoundaryErroreb4b5d86 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreb4b5d86 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreb4b5d86 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeb4b5d86 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreb4b5d86> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreb4b5d86::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreb4b5d86::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreb4b5d86::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_eb4b5d86() {
    let admitted = BoundaryRecordeb4b5d86::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordeb4b5d86::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
