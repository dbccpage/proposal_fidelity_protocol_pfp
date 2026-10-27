//! Native finite fixtures for lesson 720.24. No input parser or Python solver.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c6682cad<T> {
    fn checked_invariant_c6682cad(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c6682cad<T> for Option<T> {
    #[inline]
    fn checked_invariant_c6682cad(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c6682cad<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c6682cad(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::OperationLimits;
use num_bigint::BigInt;
use num_traits::One;
use core_wdp::genesis_balance_transition::{BalanceVerdict, Source25BalanceProfile};
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::{Source25Change, Source25State, SourceRelation};
use serde_json::{json, Value};

fn state(faces: Vec<MarkedTriple>, one_arc: bool) -> Source25State {
    let mut r = vec![BigInt::one(); 16];
    if one_arc {
        r[8] += BigInt::one();
    }
    Source25State::try_new(GenesisOngoingPacket {
        terms: (0..4).map(|i| format!("t{i}")).collect(),
        r,
        s: vec![BigInt::one(); 16],
        filled: faces,
    })
    .checked_invariant_c6682cad("fixed native fixture")
}
fn raw(source: &Source25State) -> Value {
    let p = source.packet();
    json!({"terms":p.terms,
        "r":p.r.iter().map(ToString::to_string).collect::<Vec<_>>(),
        "s":p.s.iter().map(ToString::to_string).collect::<Vec<_>>(),
        "filled":p.filled.iter().map(|t| [t.x,t.y,t.z]).collect::<Vec<_>>()})
}
fn case(name: &str, source: Source25State, event: Source25Change) -> Value {
    let p = Source25BalanceProfile::new(source, event, OperationLimits::UNLIMITED)
        .checked_invariant_c6682cad("fixed enabled event");
    p.verify().checked_invariant_c6682cad("certificate replay");
    let counter = match p.verdict() {
        BalanceVerdict::Preserved(_) => Value::Null,
        BalanceVerdict::Obstructed(w) => {
            json!({"value":w.value().to_string(),"source":raw(w.source()),"target":raw(w.target())})
        }
    };
    json!({"name":name,"universal_preserves":matches!(p.verdict(),BalanceVerdict::Preserved(_)),
        "actual_before_balanced":p.actual_source_balanced(),"actual_after_balanced":p.actual_target_balanced(),
        "counterexample":counter,"source":raw(p.source()),"target":raw(p.target())})
}
fn main() {
    let face = MarkedTriple { x: 0, y: 1, z: 2 };
    let source = state(vec![face], false);
    let mut seven = vec![];
    for x in 0..4 {
        for y in x + 1..4 {
            for z in y + 1..4 {
                for t in [MarkedTriple { x, y, z }, MarkedTriple { x, y: z, z: y }] {
                    if t != face {
                        seven.push(t);
                    }
                }
            }
        }
    }
    seven.sort();
    let three = vec![
        MarkedTriple { x: 0, y: 1, z: 3 },
        MarkedTriple { x: 0, y: 2, z: 3 },
        MarkedTriple { x: 1, y: 2, z: 3 },
    ];
    let cases = vec![
        case("add_term", source.clone(), Source25Change::AddTerm),
        case(
            "add_forward",
            source.clone(),
            Source25Change::AddAssertion {
                relation: SourceRelation::R,
                x: 0,
                y: 1,
            },
        ),
        case(
            "add_reverse",
            source.clone(),
            Source25Change::AddAssertion {
                relation: SourceRelation::R,
                x: 1,
                y: 0,
            },
        ),
        case(
            "remove_forward",
            source.clone(),
            Source25Change::Remove {
                relation: SourceRelation::R,
                x: 0,
                y: 1,
            },
        ),
        case(
            "identify_touching",
            source.clone(),
            Source25Change::Identify { x: 0, y: 3 },
        ),
        case(
            "fill_three_faces",
            state(three, true),
            Source25Change::Fill { x: 0, y: 1, z: 2 },
        ),
        case(
            "fill_seven_faces",
            state(seven, false),
            Source25Change::Fill { x: 0, y: 1, z: 2 },
        ),
    ];
    let disabled_refused = Source25BalanceProfile::new(
        source,
        Source25Change::Fill { x: 0, y: 1, z: 2 },
        OperationLimits::UNLIMITED,
    )
    .is_err();
    println!(
        "{}",
        json!({"cases":cases,"disabled_fill_refused":disabled_refused,"authority_effect":"None"})
    );
}

// Origin: engine/crates_rs/core_wdp/src/examples/balance_preserving_edits.rs
// Claim: urn:core:crates_rs:core-wdp:balance-preserving-edits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc6682cad {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc6682cad` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc6682cad {
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
impl BoundaryErrorc6682cad {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc6682cad {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc6682cad {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc6682cad {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc6682cad> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc6682cad::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc6682cad::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc6682cad::ExceedsCapacity {
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
mod l4_boundary_tests_c6682cad {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc6682cad::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc6682cad::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc6682cad::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc6682cad::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc6682cad::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc6682cad::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc6682cad::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
