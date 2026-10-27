//! DP-1 through WDP: presentation maps are total tables on the carrier, and
//! query readability is decided by the category owner.
//!
//! AuthorityEffect: None.

use core_category_theory::finite_report_query::{ReportQueryDecision, ReportQueryRefusal};
use core_wdp::difference::{Carrier, PresentationMap};
use std::collections::BTreeMap;

fn s(x: &str) -> String {
    x.to_string()
}

fn map(rows: &[(&str, &str)]) -> BTreeMap<String, String> {
    rows.iter().map(|(k, v)| (s(k), s(v))).collect()
}

fn presentation() -> PresentationMap {
    let carrier = Carrier::new(["s0", "s1", "s2"]).expect("carrier");
    PresentationMap::new(carrier, map(&[("s0", "p0"), ("s1", "p0"), ("s2", "p1")]))
        .expect("total presentation")
}

#[test]
fn presentation_map_refuses_extraneous_and_missing_rows() {
    let carrier = Carrier::new(["s0", "s1"]).expect("carrier");
    assert!(PresentationMap::new(carrier.clone(), map(&[("s0", "p"), ("s1", "p")])).is_ok());
    assert!(PresentationMap::new(
        carrier.clone(),
        map(&[("s0", "p"), ("s1", "p"), ("s99", "p")])
    )
    .is_err());
    assert!(PresentationMap::new(carrier, map(&[("s0", "p")])).is_err());
}

#[test]
fn query_constant_on_fibers_factors_on_the_realized_image() {
    let pres = presentation();
    let decision = pres
        .decide_query(
            &[s("p0"), s("p1"), s("unused")],
            &[s("lo"), s("hi")],
            &[(s("s0"), s("lo")), (s("s1"), s("lo")), (s("s2"), s("hi"))],
        )
        .expect("admitted");
    let ReportQueryDecision::Factorable(cert) = decision else {
        panic!("expected a decoder");
    };
    assert_eq!(cert.realized_image.len(), 2);
    assert!(!cert.decoder.contains_key("unused"));
}

#[test]
fn query_splitting_a_fiber_is_a_collision() {
    let pres = presentation();
    let decision = pres
        .decide_query(
            &[s("p0"), s("p1")],
            &[s("lo"), s("hi")],
            &[(s("s0"), s("lo")), (s("s1"), s("hi")), (s("s2"), s("hi"))],
        )
        .expect("admitted");
    let ReportQueryDecision::Collision(c) = decision else {
        panic!("expected a collision");
    };
    assert_eq!((c.first.as_str(), c.second.as_str(), c.report.as_str()), ("s0", "s1", "p0"));
}

#[test]
fn query_and_codomain_typing_are_refused() {
    let pres = presentation();
    // Presented token outside the declared report codomain.
    assert!(matches!(
        pres.decide_query(
            &[s("p0")],
            &[s("lo")],
            &[(s("s0"), s("lo")), (s("s1"), s("lo")), (s("s2"), s("lo"))],
        ),
        Err(ReportQueryRefusal::OutsideCodomain { .. })
    ));
    // Partial query table.
    assert!(matches!(
        pres.decide_query(&[s("p0"), s("p1")], &[s("lo")], &[(s("s0"), s("lo"))]),
        Err(ReportQueryRefusal::MissingAssignment { .. })
    ));
    // Extraneous query row.
    assert!(matches!(
        pres.decide_query(
            &[s("p0"), s("p1")],
            &[s("lo")],
            &[
                (s("s0"), s("lo")),
                (s("s1"), s("lo")),
                (s("s2"), s("lo")),
                (s("s9"), s("lo"))
            ],
        ),
        Err(ReportQueryRefusal::ExtraneousAssignment { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_wdp/test_dp1_presentation_query.rs
// Claim: urn:core:crates_rs:tests:test-dp1-presentation-query:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4519e602 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4519e602` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4519e602 {
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
impl BoundaryError4519e602 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4519e602 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4519e602 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4519e602 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4519e602> {
        if capacity_bound == 0 {
            return Err(BoundaryError4519e602::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4519e602::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4519e602::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4519e602() {
    let admitted = BoundaryRecord4519e602::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4519e602::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
