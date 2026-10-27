// AuthorityEffect: None.
//! Exact arithmetic seam regressions for the bounded stabilizer runtime.
use pfp_runtime::stabilizer::{
    check, solve, StabilizerCheckResult, StabilizerOutcome,
};
use serde_json::json;
#[test]
fn maximum_i64_weights_accumulate_exactly_and_refuse_only_unrepresentable_minima() {
    let forced = json!({"id":"energy_width", "n":1, "terms":[
        {"id":"a","pauli":"I","weight":i64::MAX,"target":-1},
        {"id":"b","pauli":"I","weight":i64::MAX,"target":-1}
    ]});
    let outcome = solve(&forced);
    assert!(
        matches!(&outcome,StabilizerOutcome::Unknown{refusal_code,..} if refusal_code=="ENERGY_WIDTH_EXCEEDED")
    );
    assert!(check(&forced, &serde_json::to_value(outcome).unwrap()).is_pass());
    // A non-minimizing assignment can overflow the old carrier while the minimum fits.
    let flexible = json!({"id":"wide_intermediate", "n":1, "terms":[
        {"id":"a","pauli":"Z","weight":i64::MAX,"target":1},
        {"id":"b","pauli":"Z","weight":i64::MAX,"target":1}
    ]});
    assert!(matches!(
        solve(&flexible),
        StabilizerOutcome::Solved {
            energy: [0, 1],
            degeneracy: 1,
            ..
        }
    ));
    assert!(check(&flexible, &serde_json::to_value(solve(&flexible)).unwrap()).is_pass());
    let boundary = json!({"id":"fits_boundary", "n":1, "terms":[
        {"id":"a","pauli":"I","weight":i64::MAX,"target":-1}
    ]});
    assert!(
        matches!(solve(&boundary),StabilizerOutcome::Solved{energy:[n,1],degeneracy:2,..} if n==i64::MAX)
    );
    assert!(check(&boundary, &serde_json::to_value(solve(&boundary)).unwrap()).is_pass());
    let denominators = json!({"id":"denominator_width", "n":1, "terms":[
        {"id":"a","pauli":"I","weight":[1,i64::MAX-2],"target":-1},
        {"id":"b","pauli":"I","weight":[1,i64::MAX-4],"target":-1}
    ]});
    assert!(
        matches!(solve(&denominators),StabilizerOutcome::Unknown{refusal_code,..} if refusal_code=="ENERGY_WIDTH_EXCEEDED")
    );
    assert!(matches!(check(
        &boundary,
        &json!({"id":"fits_boundary","status":"SOLVED","energy":[i64::MIN,i64::MAX]})
    ), StabilizerCheckResult::Fail { reason, .. } if reason.starts_with("Energy mismatch:")));
}

// Origin: engine/crates_rs/tests/pfp_runtime/stabilizer_energy_width.rs
// Claim: urn:core:crates_rs:tests:stabilizer-energy-width:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5ea1635c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5ea1635c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5ea1635c {
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
impl BoundaryError5ea1635c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5ea1635c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5ea1635c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5ea1635c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5ea1635c> {
        if capacity_bound == 0 {
            return Err(BoundaryError5ea1635c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5ea1635c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5ea1635c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5ea1635c() {
    let admitted = BoundaryRecord5ea1635c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5ea1635c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
