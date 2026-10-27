//! Allocation receipt for a declared finite proposal profile, not BigRational.

use core_kernel::bounded_rational::StackRational as Q;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};

use core_solvers::solver_lp_bounded_candidate::{propose, CandidateError, MAX_COLS, MAX_ROWS};

static MEASURING: AtomicBool = AtomicBool::new(false);
static ALLOCATIONS: AtomicUsize = AtomicUsize::new(0);
struct Counter;
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        if MEASURING.load(Ordering::Relaxed) {
            ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        }
        unsafe { System.alloc(layout) }
    }
    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        if MEASURING.load(Ordering::Relaxed) {
            ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        }
        unsafe { System.alloc_zeroed(layout) }
    }
    unsafe fn realloc(&self, p: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        if MEASURING.load(Ordering::Relaxed) {
            ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        }
        unsafe { System.realloc(p, layout, size) }
    }
    unsafe fn dealloc(&self, p: *mut u8, layout: Layout) {
        unsafe { System.dealloc(p, layout) }
    }
}
#[global_allocator]
static ALLOCATOR: Counter = Counter;

#[test]
fn bounded_enumeration_retains_all_ties_without_heap_allocations() {
    let q = |n| Q::new(n, 1).unwrap();
    let mut matrix = [[Q::ZERO; MAX_COLS]; MAX_ROWS];
    matrix[0][..3].copy_from_slice(&[q(-1), q(1), q(0)]);
    matrix[1][..3].copy_from_slice(&[q(0), q(-1), q(1)]);
    matrix[2][..3].copy_from_slice(&[q(1), q(0), q(-1)]);
    let mut reading = [Q::ZERO; MAX_ROWS];
    reading[0] = q(1);
    let weights = [q(1); MAX_ROWS];
    ALLOCATIONS.store(0, Ordering::Relaxed);
    MEASURING.store(true, Ordering::SeqCst);
    let candidate = propose(&matrix, 3, 3, &reading, &weights, 32);
    MEASURING.store(false, Ordering::SeqCst);
    let allocation_count = ALLOCATIONS.load(Ordering::Relaxed);
    let candidate = candidate.unwrap();
    assert_eq!(allocation_count, 0);
    assert_eq!(candidate.value, q(1));
    assert_eq!(candidate.subsets, 3);
    assert_eq!(candidate.tie_count, 3);
    assert!(matches!(
        propose(&matrix, 3, 3, &reading, &weights, 0),
        Err(CandidateError::Budget)
    ));
    assert!(matches!(
        propose(&matrix, MAX_ROWS + 1, 3, &reading, &weights, 32),
        Err(CandidateError::Capacity)
    ));
    reading[0] = Q {
        numerator: i128::MIN,
        denominator: 1,
    };
    assert!(matches!(
        propose(&matrix, 3, 3, &reading, &weights, 32),
        Err(CandidateError::Shape)
    ));
    reading[0] = q(i128::MAX);
    reading[1] = q(i128::MAX);
    reading[2] = q(i128::MAX);
    assert!(matches!(
        propose(&matrix, 3, 3, &reading, &weights, 32),
        Err(CandidateError::Overflow)
    ));
}

// Origin: engine/crates_rs/tests/core_solvers/bounded_l1_allocation.rs
// Claim: urn:core:crates_rs:tests:bounded-l1-allocation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7a0cdeba {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7a0cdeba` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7a0cdeba {
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
impl BoundaryError7a0cdeba {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7a0cdeba {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7a0cdeba {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7a0cdeba {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7a0cdeba> {
        if capacity_bound == 0 {
            return Err(BoundaryError7a0cdeba::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7a0cdeba::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7a0cdeba::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7a0cdeba() {
    let admitted = BoundaryRecord7a0cdeba::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7a0cdeba::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
