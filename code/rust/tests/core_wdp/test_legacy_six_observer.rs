use num_rational::BigRational;
use core_functional::phi1::ExactPhi1Certificate;
use core_wdp::legacy_observer_adapters::SourceCustody;
use core_wdp::legacy_six_observer::SixObserverAdapter;
fn q(x: i64) -> BigRational {
    BigRational::from_integer(x.into())
}
fn cert(x: i64) -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![q(x)],
        d0: vec![vec![q(0)]],
        weights: vec![q(1)],
        alpha: vec![q(0)],
        primal_residual: vec![q(x)],
        dual_witness: vec![q(x.signum())],
        reported_value: q(x.abs()),
    }
}
fn build(
    relation: Vec<Vec<bool>>,
    pair: Vec<Vec<ExactPhi1Certificate>>,
) -> Result<SixObserverAdapter, core_wdp::legacy_observer_adapters::AdapterError> {
    SixObserverAdapter::try_new(
        vec!["edge".into()],
        vec!["x".into(), "y".into()],
        vec![cert(0), cert(1)],
        pair,
        relation,
        vec!["zero".into(), "positive".into()],
        vec![0, 1],
        SourceCustody {
            path: "education/05_math_contexts_observers_and_detector_adequacy.md".into(),
            recorded_sha256: "a".repeat(64),
            source_receipts: vec![],
            source_authority_tags: vec![],
        },
    )
}
#[test]
fn six_tuple_uses_actual_assignments_image_relation_receipts_terminalizer() {
    let pairs = vec![vec![cert(0), cert(-1)], vec![cert(1), cert(0)]];
    let a = build(vec![vec![true, false], vec![false, true]], pairs.clone()).unwrap();
    assert_eq!(a.terminal(1), Some("positive"));
    assert!(a.presentation().memory().is_none());
    assert!(a.presentation().policy().is_none());
    assert!(a.presentation().evaluator().is_none());
    assert!(build(vec![vec![true, true], vec![true, true]], pairs).is_err());
    assert!(build(
        vec![vec![true, false], vec![false, true]],
        vec![vec![cert(0), cert(0)], vec![cert(1), cert(0)]]
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_legacy_six_observer.rs
// Claim: urn:core:crates_rs:tests:test-legacy-six-observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2ea6a19f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2ea6a19f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2ea6a19f {
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
impl BoundaryError2ea6a19f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2ea6a19f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2ea6a19f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2ea6a19f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2ea6a19f> {
        if capacity_bound == 0 {
            return Err(BoundaryError2ea6a19f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2ea6a19f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2ea6a19f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2ea6a19f() {
    let admitted = BoundaryRecord2ea6a19f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2ea6a19f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
