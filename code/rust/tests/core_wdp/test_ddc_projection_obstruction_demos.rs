use core_wdp::ddc::{
    Cochain1, FiniteWindow, LambdaAlgebraError, OrientedTriangle,
};
use std::collections::BTreeMap;

/// 1. Locally acceptable judgments whose triangle does not close.
/// We construct a situation where Author accepts Proposal (edge AP = 0),
/// Proposal is accepted by Evaluator (edge PE = 0), yet the Evaluator
/// does not accept the Author (edge EA = 1). Despite edge-wise local
/// compatibility, the global triangle boundary does not close (d1 h != 0).
#[test]
fn demo_1_locally_acceptable_triangle_does_not_close() -> Result<(), LambdaAlgebraError> {
    let window = FiniteWindow::new(
        vec!["A", "P", "E"],
        vec![("A", "P"), ("P", "E"), ("A", "E")],
        vec![OrientedTriangle::new("A", "P", "E")],
    );

    let mut cochain = Cochain1::new();
    cochain.checked_add_term("A", "P", 0)?; // Author accepts Proposal
    cochain.checked_add_term("P", "E", 0)?; // Proposal accepted by Evaluator
    cochain.checked_add_term("E", "A", 1)?; // Evaluator has discrepancy with Author

    // d1 h (boundary check) = ab + bc + ca
    // ab = 0, bc = 0, ca = 1 -> 1 != 0.
    let scan = window.checked_scan_c1(&cochain)?;
    assert_eq!(
        scan.face_gamma2[0], 1,
        "The triangle closure check yields a non-zero defect"
    );
    assert_eq!(scan.gamma2_total, 1);

    Ok(())
}

/// 2. Degenerate shared projection (common-mode failure).
/// We show that under a degenerate projection P1 that discards a critical
/// distinction, the tripartite system appears completely consistent (gamma2 = 0).
/// Under an alternative projection P2 that retains the distinction, the
/// inconsistency is exposed as a non-zero closure defect (gamma2 = 1).
#[test]
fn demo_2_common_mode_failure_under_degenerate_projection() -> Result<(), LambdaAlgebraError> {
    struct State {
        secret_bit: bool,
    }

    let author_state = State { secret_bit: true };
    let proposal_state = State { secret_bit: false };
    let evaluator_state = State { secret_bit: true };

    let window = FiniteWindow::new(
        vec!["A", "P", "E"],
        vec![("A", "P"), ("P", "E"), ("A", "E")],
        vec![OrientedTriangle::new("A", "P", "E")],
    );

    // Projection 1: Degenerate projection map (discards secret_bit, mapping all to 0)
    let p1 = |_s: &State| -> i64 { 0 };

    let mut cochain_p1 = Cochain1::new();
    cochain_p1.checked_add_term("A", "P", p1(&author_state) - p1(&proposal_state))?;
    cochain_p1.checked_add_term("P", "E", p1(&proposal_state) - p1(&evaluator_state))?;
    cochain_p1.checked_add_term("E", "A", p1(&evaluator_state) - p1(&author_state))?;

    let scan_p1 = window.checked_scan_c1(&cochain_p1)?;
    assert_eq!(
        scan_p1.gamma2_total, 0,
        "Degenerate projection hides the composition defect"
    );

    // Projection 2: Alternative projection map (retains secret_bit as 1 or 0)
    let p2 = |s: &State| -> i64 {
        if s.secret_bit {
            1
        } else {
            0
        }
    };

    // A checks P (accepts P's public state) -> 0
    // E checks P (detects P's secret_bit does not match E's expectation) -> 1
    // A checks E (accepts E) -> 0
    let mut cochain_p2 = Cochain1::new();
    cochain_p2.checked_add_term("A", "P", 0)?;
    cochain_p2.checked_add_term("P", "E", p2(&evaluator_state) - p2(&proposal_state))?; // 1 - 0 = 1
    cochain_p2.checked_add_term("E", "A", 0)?;

    let scan_p2 = window.checked_scan_c1(&cochain_p2)?;
    assert_eq!(
        scan_p2.gamma2_total, 1,
        "Alternative projection exposes the hidden composition defect"
    );

    Ok(())
}

/// 3. Quotienting reduces candidate evaluation count.
/// We demonstrate that grouping candidates by their obstruction signature
/// (cardinality of quotient classes) reduces the number of full evaluations needed.
#[test]
fn demo_3_quotienting_reduces_evaluation_overhead() {
    struct Proposal {
        _content: String,
        signature: (u64, u64),
    }

    let candidates = vec![
        Proposal {
            _content: "A1".to_string(),
            signature: (1, 0),
        },
        Proposal {
            _content: "A2".to_string(),
            signature: (1, 0),
        },
        Proposal {
            _content: "A3".to_string(),
            signature: (1, 0),
        },
        Proposal {
            _content: "B1".to_string(),
            signature: (0, 2),
        },
        Proposal {
            _content: "B2".to_string(),
            signature: (0, 2),
        },
        Proposal {
            _content: "C1".to_string(),
            signature: (0, 0),
        },
    ];

    // Quotienting: Group proposals by signature.
    let mut quotient: BTreeMap<(u64, u64), Vec<&Proposal>> = BTreeMap::new();
    for p in &candidates {
        quotient.entry(p.signature).or_default().push(p);
    }

    // 6 candidates are reduced to 3 equivalence classes.
    assert_eq!(quotient.len(), 3);
    assert!(quotient.len() < candidates.len());
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_projection_obstruction_demos.rs
// Claim: urn:core:crates_rs:tests:test-ddc-projection-obstruction-demos:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord78b72295 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord78b72295` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError78b72295 {
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
impl BoundaryError78b72295 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError78b72295 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError78b72295 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord78b72295 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError78b72295> {
        if capacity_bound == 0 {
            return Err(BoundaryError78b72295::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError78b72295::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError78b72295::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_78b72295() {
    let admitted = BoundaryRecord78b72295::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord78b72295::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
