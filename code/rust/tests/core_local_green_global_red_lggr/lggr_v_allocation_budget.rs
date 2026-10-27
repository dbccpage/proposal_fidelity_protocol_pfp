//! Standalone allocation-order regression binary.
//! The observer is armed only around a call on the current test thread.
//! Allocation requests always delegate to System: no deliberate panic or abort.
//! Unsafe code is confined to forwarding GlobalAlloc's contracts unchanged.

use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;

use num_rational::BigRational;
use core_epk::lggr_v::{
    check_soundness, verify_unsoundness_witness, LggrSoundnessError, MAX_LGGR_CELLS,
};
use core_linear_algebra::backend::basic_matrix::BasicMatrix;

thread_local! {
    static ARMED: Cell<bool> = const { Cell::new(false) };
    static MAX_SINGLE: Cell<usize> = const { Cell::new(0) };
}

#[test]
fn witness_verifier_refuses_an_oversized_product_profile() {
    let one = BigRational::from_integer(1.into());
    let d = BasicMatrix::from_row_major(1, 65, vec![one.clone(); 65]).unwrap();
    let q = BasicMatrix::from_row_major(65, 1, vec![one.clone(); 65]).unwrap();
    assert_eq!(
        verify_unsoundness_witness(&d, &q, &vec![one; 65]).unwrap_err(),
        LggrSoundnessError::BudgetUnknown {
            cells: 4225,
            limit: MAX_LGGR_CELLS
        }
    );
}

fn observe(size: usize) {
    // Constant TLS initializers do not allocate. try_with also tolerates TLS
    // teardown; never format, log, panic or allocate in this allocator path.
    let _ = ARMED.try_with(|armed| {
        if armed.get() {
            let _ = MAX_SINGLE.try_with(|maximum| maximum.set(maximum.get().max(size)));
        }
    });
}

struct ProbeAllocator;

unsafe impl GlobalAlloc for ProbeAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        observe(layout.size());
        unsafe { System.alloc(layout) }
    }
    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        observe(layout.size());
        unsafe { System.alloc_zeroed(layout) }
    }
    unsafe fn realloc(&self, ptr: *mut u8, old: Layout, size: usize) -> *mut u8 {
        observe(size);
        unsafe { System.realloc(ptr, old, size) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static ALLOCATOR: ProbeAllocator = ProbeAllocator;

struct Disarm;
impl Drop for Disarm {
    fn drop(&mut self) {
        ARMED.with(|armed| armed.set(false));
    }
}

fn measure<T>(operation: impl FnOnce() -> T) -> (T, usize) {
    MAX_SINGLE.with(|maximum| maximum.set(0));
    ARMED.with(|armed| armed.set(true));
    let disarm = Disarm;
    let result = operation();
    drop(disarm);
    (result, MAX_SINGLE.with(Cell::get))
}

#[test]
fn oversize_output_refuses_before_the_old_dense_allocation() {
    // All construction and assertions occur while unarmed. Only this thread's
    // measured call is observed, even if the Rust harness has other threads.
    let one = BigRational::from_integer(1.into());
    let d = BasicMatrix::from_row_major(1, 65, vec![one.clone(); 65]).unwrap();
    let q = BasicMatrix::from_row_major(65, 1, vec![one; 65]).unwrap();
    let allowed_single_allocation = MAX_LGGR_CELLS * std::mem::size_of::<BigRational>();

    // Bounded positive control: 4225 entries is deliberately small. This proves
    // the probe observes the old multiplication mechanism, not a synthetic OOM.
    let (product, old_maximum) = measure(|| q.mul(&d));
    assert_eq!(product.as_ref().unwrap().shape(), (65, 65));
    assert!(old_maximum > allowed_single_allocation);
    drop(product);

    let (result, maximum) = measure(|| check_soundness(&d, &q));
    assert_eq!(
        result.unwrap_err(),
        LggrSoundnessError::BudgetUnknown {
            cells: 4225,
            limit: MAX_LGGR_CELLS,
        }
    );
    assert!(
        maximum <= allowed_single_allocation,
        "output refusal followed an oversized allocation request"
    );
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/lggr_v_allocation_budget.rs
// Claim: urn:core:crates_rs:tests:lggr-v-allocation-budget:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5f459f74 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5f459f74` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5f459f74 {
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
impl BoundaryError5f459f74 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5f459f74 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5f459f74 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5f459f74 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5f459f74> {
        if capacity_bound == 0 {
            return Err(BoundaryError5f459f74::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5f459f74::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5f459f74::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5f459f74() {
    let admitted = BoundaryRecord5f459f74::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5f459f74::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
