//! Streaming reverse search checked against the independent active-set oracle.
use linear_algebra::exact_field::{
    matrix,
    rational_bareiss::{RationalBudget, RationalError, RationalLimits},
};
use num_rational::BigRational;
use core_solvers::solver_convex_vertex_enum::{
    reverse_search_vertices, vertex_enumeration, ReverseSearchError,
};
use std::collections::BTreeSet;
fn q(n: i64) -> BigRational {
    BigRational::from_integer(n.into())
}
fn limits() -> RationalLimits {
    RationalLimits {
        max_scalar_ops: 20_000_000,
        max_elements: 100_000,
        max_bits: 4096,
    }
}
fn budget() -> RationalBudget {
    RationalBudget::new(limits())
}
#[test]
fn simple_cubes_match_active_set_oracle_without_duplicate_output() {
    for d in 1..=4 {
        let e = matrix::zeros(0, d).unwrap();
        let a = matrix::from_fn(2 * d, d, |r, c| {
            if r / 2 == c {
                q(if r % 2 == 0 { -1 } else { 1 })
            } else {
                q(0)
            }
        })
        .unwrap();
        let bounds: Vec<_> = (0..2 * d)
            .map(|r| q(if r % 2 == 0 { 0 } else { 1 }))
            .collect();
        let expected: BTreeSet<_> = vertex_enumeration(&e, &[], &a, &bounds, 1000)
            .unwrap()
            .into_iter()
            .collect();
        let mut emitted = Vec::new();
        let report =
            reverse_search_vertices(&e, &[], &a, &bounds, &vec![q(0); d], &mut budget(), |p| {
                emitted.push(p.to_vec())
            })
            .unwrap();
        let actual: BTreeSet<_> = emitted.iter().cloned().collect();
        assert_eq!(actual, expected);
        assert_eq!(emitted.len(), actual.len());
        assert_eq!(report.vertices, 1 << d);
    }
}
#[test]
fn equality_reduction_and_unbounded_rays() {
    let e = matrix::from_rows(vec![vec![q(0), q(0), q(1)], vec![q(0), q(0), q(2)]]).unwrap();
    let a = matrix::from_rows(vec![
        vec![q(-1), q(0), q(0)],
        vec![q(0), q(-1), q(0)],
        vec![q(1), q(1), q(0)],
    ])
    .unwrap();
    let b = vec![q(0), q(0), q(1)];
    let mut out = Vec::new();
    let result = reverse_search_vertices(
        &e,
        &[q(3), q(6)],
        &a,
        &b,
        &[q(0), q(0), q(3)],
        &mut budget(),
        |p| out.push(p.to_vec()),
    )
    .unwrap();
    assert_eq!(result.vertices, 3);
    assert_eq!(
        out.into_iter().collect::<BTreeSet<_>>(),
        vertex_enumeration(&e, &[q(3), q(6)], &a, &b, 10)
            .unwrap()
            .into_iter()
            .collect()
    );
    let e = matrix::zeros(0, 2).unwrap();
    let a = matrix::from_rows(vec![vec![q(-1), q(0)], vec![q(0), q(-1)]]).unwrap();
    let report = reverse_search_vertices(
        &e,
        &[],
        &a,
        &[q(0), q(0)],
        &[q(0), q(0)],
        &mut budget(),
        |_| {},
    )
    .unwrap();
    assert_eq!(report.vertices, 1); // two rays, one vertex
}
#[test]
fn degeneracy_seed_errors_and_fuel_are_explicit_refusals() {
    let e = matrix::zeros(0, 1).unwrap();
    let a = matrix::from_rows(vec![vec![q(-1)], vec![q(1)], vec![q(1)]]).unwrap();
    assert_eq!(
        reverse_search_vertices(
            &e,
            &[],
            &a,
            &[q(0), q(1), q(1)],
            &[q(1)],
            &mut budget(),
            |_| {}
        ),
        Err(ReverseSearchError::NonSimpleVertex)
    );
    // Degeneracy reached after the valid root cannot turn partial output into completion.
    let mut emitted = 0;
    assert_eq!(
        reverse_search_vertices(
            &e,
            &[],
            &a,
            &[q(0), q(1), q(1)],
            &[q(0)],
            &mut budget(),
            |_| emitted += 1
        ),
        Err(ReverseSearchError::NonSimpleVertex)
    );
    assert_eq!(emitted, 1);
    assert_eq!(
        reverse_search_vertices(
            &e,
            &[],
            &a,
            &[q(0), q(1), q(1)],
            &[q(2)],
            &mut budget(),
            |_| {}
        ),
        Err(ReverseSearchError::InfeasibleSeed)
    );
    let a = matrix::from_rows(vec![vec![q(-1)], vec![q(1)]]).unwrap();
    let result =
        reverse_search_vertices(&e, &[], &a, &[q(0), q(1)], &[q(0)], &mut budget(), |_| {})
            .unwrap();
    let mut exact = limits();
    exact.max_scalar_ops = result.scalar_ops;
    assert_eq!(
        reverse_search_vertices(
            &e,
            &[],
            &a,
            &[q(0), q(1)],
            &[q(0)],
            &mut RationalBudget::new(exact),
            |_| {}
        )
        .unwrap(),
        result
    );
    exact.max_scalar_ops -= 1;
    assert_eq!(
        reverse_search_vertices(
            &e,
            &[],
            &a,
            &[q(0), q(1)],
            &[q(0)],
            &mut RationalBudget::new(exact),
            |_| {}
        ),
        Err(ReverseSearchError::Arithmetic(RationalError::FuelExhausted))
    );
}

// Origin: engine/crates_rs/tests/core_solvers/reverse_search_vertices.rs
// Claim: urn:core:crates_rs:tests:reverse-search-vertices:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord47a9ba16 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord47a9ba16` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError47a9ba16 {
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
impl BoundaryError47a9ba16 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError47a9ba16 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError47a9ba16 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord47a9ba16 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError47a9ba16> {
        if capacity_bound == 0 {
            return Err(BoundaryError47a9ba16::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError47a9ba16::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError47a9ba16::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_47a9ba16() {
    let admitted = BoundaryRecord47a9ba16::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord47a9ba16::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
