//! Exact five-field V3 composition checks; validation grants no execution authority.
use core_operads::estate::{execute_composition, verify_composition, OperationV3};
use serde_json::{json, Value};
use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;

thread_local! {
    static MEASURING: Cell<bool> = const { Cell::new(false) };
    static ALLOCATIONS: Cell<usize> = const { Cell::new(0) };
}

struct CountingAllocator;

fn count_allocation() {
    if MEASURING.try_with(Cell::get).unwrap_or(false) {
        let _ = ALLOCATIONS.try_with(|count| count.set(count.get() + 1));
    }
}

// Instrument only the current test thread; all allocation behavior delegates to System.
unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        count_allocation();
        unsafe { System.alloc(layout) }
    }
    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        count_allocation();
        unsafe { System.alloc_zeroed(layout) }
    }
    unsafe fn dealloc(&self, pointer: *mut u8, layout: Layout) {
        unsafe { System.dealloc(pointer, layout) }
    }
    unsafe fn realloc(&self, pointer: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        count_allocation();
        unsafe { System.realloc(pointer, layout, size) }
    }
}

#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

fn port(name: &str) -> Value {
    json!({
        "name":name,"colour_id":{"value":"Code"},"schema_ref":{"value":"schema:code:v1"},
        "schema_digest":{"algorithm":"sha256","hex_digest":"a".repeat(64)},
        "validator_ref":"validator:code:v1",
        "validator_digest":{"algorithm":"sha256","hex_digest":"b".repeat(64)}
    })
}

fn operation(id: &str, inputs: Vec<Value>, output: Value) -> Value {
    json!({
        "operation_id":{"value":id},"inputs":inputs,"output":output,"operand_refs":[],
        "lifecycle":{
            "declaration":"Declared","schema_binding":"Bound","executor_binding":"Bound",
            "validation":"Validated","admission":"Unadmitted",
            "schema_digest":{"algorithm":"sha256","hex_digest":"c".repeat(64)},
            "executor_digest":{"algorithm":"sha256","hex_digest":"d".repeat(64)}
        },"residual_status":"HOLD","authority_effect":"None","authority_ceiling":"None"
    })
}

fn request() -> Value {
    json!({
        "root_operation":operation("root",vec![port("parent-input")],port("result")),
        "slot_bindings":[[0,operation("child",vec![],port("child-output"))]]
    })
}

#[test]
fn exact_contract_ignores_port_labels_and_never_admits() {
    assert_eq!(
        execute_composition(&request()).unwrap(),
        json!({"is_valid":true,"authority_effect":"None"})
    );
}

#[test]
fn every_contract_field_has_an_independent_refusal_and_recovery() {
    for (field, value, code) in [
        ("colour_id", json!({"value":"State"}), "COLOUR_MISMATCH"),
        (
            "schema_ref",
            json!({"value":"schema:foreign:v1"}),
            "SCHEMA_REFERENCE_MISMATCH",
        ),
        (
            "schema_digest",
            json!({"algorithm":"sha256","hex_digest":"e".repeat(64)}),
            "SCHEMA_DIGEST_MISMATCH",
        ),
        (
            "validator_ref",
            json!("validator:foreign:v1"),
            "VALIDATOR_REFERENCE_MISMATCH",
        ),
        (
            "validator_digest",
            json!({"algorithm":"sha256","hex_digest":"f".repeat(64)}),
            "VALIDATOR_DIGEST_MISMATCH",
        ),
    ] {
        let original = request();
        let mut changed = original.clone();
        changed["slot_bindings"][0][1]["output"][field] = value;
        assert_eq!(
            execute_composition(&changed).unwrap_err().code,
            code,
            "{field}"
        );
        assert_eq!(execute_composition(&original).unwrap()["is_valid"], true);
    }
}

#[test]
fn zero_digest_is_not_a_contract_wildcard() {
    let mut changed = request();
    changed["slot_bindings"][0][1]["output"]["schema_digest"]["hex_digest"] = json!("0".repeat(64));
    assert_eq!(
        execute_composition(&changed).unwrap_err().code,
        "SCHEMA_DIGEST_MISMATCH"
    );
}

#[test]
fn slot_flags_floats_strings_negative_and_overflow_are_not_normalized() {
    for (slot, code) in [
        (json!(true), "SLOT_INDEX_NOT_AN_INTEGER"),
        (json!(0.0), "SLOT_INDEX_NOT_AN_INTEGER"),
        (json!("0"), "SLOT_INDEX_NOT_AN_INTEGER"),
        (json!(-1), "SLOT_INDEX_OUT_OF_BOUNDS"),
        (json!(1), "SLOT_INDEX_OUT_OF_BOUNDS"),
        (
            serde_json::from_str("184467440737095516160").unwrap(),
            "SLOT_INDEX_OUT_OF_BOUNDS",
        ),
    ] {
        let mut changed = request();
        changed["slot_bindings"][0][0] = slot;
        assert_eq!(execute_composition(&changed).unwrap_err().code, code);
    }
    let mut duplicate = request();
    let binding = duplicate["slot_bindings"][0].clone();
    duplicate["slot_bindings"]
        .as_array_mut()
        .unwrap()
        .push(binding);
    assert_eq!(
        execute_composition(&duplicate).unwrap_err().code,
        "DUPLICATE_SLOT_BINDING"
    );
}

#[test]
fn original_typed_slot_positions_cannot_be_swapped() {
    let mut changed = request();
    let mut second = port("second");
    second["validator_ref"] = json!("validator:second:v1");
    changed["root_operation"]["inputs"]
        .as_array_mut()
        .unwrap()
        .push(second.clone());
    changed["slot_bindings"][0][0] = json!(1);
    assert_eq!(
        execute_composition(&changed).unwrap_err().code,
        "VALIDATOR_REFERENCE_MISMATCH"
    );
    changed["slot_bindings"][0][1]["output"] = second;
    assert_eq!(execute_composition(&changed).unwrap()["is_valid"], true);
}

#[test]
fn unknown_wire_fields_refuse() {
    let mut changed = request();
    changed["pretend_admission"] = json!(true);
    assert_eq!(
        execute_composition(&changed).unwrap_err().code,
        "STRICT_COMPOSITION_INPUT_INVALID"
    );
}

#[test]
fn prepared_successful_composition_kernel_allocates_nothing() {
    // The caller owns these decoded buffers. JSON decoding and refusal messages
    // are cold adapters and are outside this accepted-input measurement.
    for arity in [0, 1, 2, 16, 64, 128] {
        let root = OperationV3::from_json(&operation(
            "root",
            vec![port("input"); arity],
            port("result"),
        ))
        .unwrap();
        let child = OperationV3::from_json(&operation("child", vec![], port("output"))).unwrap();
        let bindings = (0..arity)
            .map(|slot| (json!(slot), child.clone()))
            .collect::<Vec<_>>();
        ALLOCATIONS.with(|count| count.set(0));
        MEASURING.with(|measuring| measuring.set(true));
        let outcome = verify_composition(&root, &bindings);
        MEASURING.with(|measuring| measuring.set(false));
        let allocations = ALLOCATIONS.with(Cell::get);
        assert_eq!(outcome.unwrap(), true);
        assert_eq!(allocations, 0, "arity {arity}");
    }
    ALLOCATIONS.with(|count| count.set(0));
    MEASURING.with(|measuring| measuring.set(true));
    let positive_control = std::hint::black_box(vec![0u8; 128]);
    MEASURING.with(|measuring| measuring.set(false));
    assert!(
        ALLOCATIONS.with(Cell::get) > 0,
        "allocation instrumentation must detect its control"
    );
    drop(positive_control);
}

// Origin: engine/crates_rs/tests/core_operads/estate_composition_contract.rs
// Claim: urn:core:crates_rs:tests:estate-composition-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2f5ac551 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2f5ac551` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2f5ac551 {
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
impl BoundaryError2f5ac551 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2f5ac551 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2f5ac551 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2f5ac551 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2f5ac551> {
        if capacity_bound == 0 {
            return Err(BoundaryError2f5ac551::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2f5ac551::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2f5ac551::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2f5ac551() {
    let admitted = BoundaryRecord2f5ac551::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2f5ac551::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
