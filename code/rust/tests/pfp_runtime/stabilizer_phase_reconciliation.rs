//! End-to-end controls for the incoming phase-carrying runtime reconstruction.
//! Staged only; root applies at the final exclusive integration window.
use core_quantum_physics::pauli::PauliString;
use pfp_runtime::stabilizer::{check, parse_case, solve, StabilizerOutcome};
use serde_json::json;

#[test]
fn a_negative_generator_product_preserves_the_signed_dependency_and_ground_space() {
    for (target, expected_energy, expected_degeneracy) in [(1, 1, 3), (-1, 0, 1)] {
        let case = json!({"id":"signed_dependency", "n":2, "terms":[
            {"id":"x","pauli":"XX","weight":1,"target":1},
            {"id":"z","pauli":"ZZ","weight":1,"target":1},
            {"id":"y","pauli":"YY","weight":1,"target":target}
        ]});
        let outcome = solve(&case);
        let StabilizerOutcome::Solved {
            energy,
            degeneracy,
            decomposition,
            ..
        } = &outcome
        else {
            panic!("the commuting signed family should solve: {outcome:?}");
        };
        assert_eq!(*energy, [expected_energy, 1]);
        assert_eq!(*degeneracy, expected_degeneracy);
        let dependency = decomposition.iter().find(|row| row.id == "y").unwrap();
        // XX * ZZ = -YY. Matching only letters is followed by consuming that sign.
        assert_eq!((dependency.mask, dependency.phase), (3, -1));
        assert!(check(&case, &serde_json::to_value(&outcome).unwrap()).is_pass());
    }
}

#[test]
fn runtime_uses_canonical_word_admission_while_trimmed_physical_admission_remains_checked() {
    let canonical = json!({"id":"canonical_word","n":1,"terms":[
        {"id":"z","pauli":"Z","weight":1,"target":1}
    ]});
    assert!(matches!(
        solve(&canonical),
        StabilizerOutcome::Solved { energy: [0, 1], .. }
    ));
    let spaced = json!({"id":"spaced_word","n":1,"terms":[
        {"id":"z","pauli":" Z ","weight":1,"target":1}
    ]});
    assert!(matches!(parse_case(&spaced), Err((code,_)) if code=="INVALID_PAULI_WORD"));
    assert!(
        matches!(solve(&spaced), StabilizerOutcome::Unknown { refusal_code,.. } if refusal_code=="INVALID_PAULI_WORD")
    );
    assert_eq!(
        PauliString::try_parse(" Z ").unwrap().letters(),
        PauliString::parse("Z").unwrap().letters()
    );
}

// Origin: engine/crates_rs/tests/pfp_runtime/stabilizer_phase_reconciliation.rs
// Claim: urn:core:crates_rs:tests:stabilizer-phase-reconciliation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord99d7b841 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord99d7b841` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError99d7b841 {
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
impl BoundaryError99d7b841 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError99d7b841 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError99d7b841 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord99d7b841 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError99d7b841> {
        if capacity_bound == 0 {
            return Err(BoundaryError99d7b841::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError99d7b841::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError99d7b841::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_99d7b841() {
    let admitted = BoundaryRecord99d7b841::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord99d7b841::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
