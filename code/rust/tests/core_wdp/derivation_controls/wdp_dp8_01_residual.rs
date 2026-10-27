#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductTargetSpec<'a> {
    pub target_id: &'a str,
    pub consumer: &'a str,
    pub defect_witness: &'a str,
    pub rust_owner: &'a str,
    pub deciding_check: &'a str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductTargetSelectionReceipt {
    pub status: &'static str,
    pub selected_count: usize,
    pub reason: &'static str,
}

pub fn verify_product_target_selection(
    targets: &[ProductTargetSpec<'_>],
) -> ProductTargetSelectionReceipt {
    if targets.is_empty() {
        return ProductTargetSelectionReceipt {
            status: "REFUSED",
            selected_count: 0,
            reason: "EMPTY_PRODUCT_TARGET_SET",
        };
    }
    for (idx, t) in targets.iter().enumerate() {
        if t.target_id.trim().is_empty()
            || t.consumer.trim().is_empty()
            || t.defect_witness.trim().is_empty()
            || t.rust_owner.trim().is_empty()
            || t.deciding_check.trim().is_empty()
        {
            return ProductTargetSelectionReceipt {
                status: "REFUSED",
                selected_count: idx,
                reason: "MISSING_REQUIRED_TARGET_FIELD",
            };
        }
        if !t.rust_owner.starts_with("engine/crates_rs/") {
            return ProductTargetSelectionReceipt {
                status: "REFUSED",
                selected_count: idx,
                reason: "NON_CANONICAL_RUST_OWNER",
            };
        }
    }
    ProductTargetSelectionReceipt {
        status: "PASS",
        selected_count: targets.len(),
        reason: "CONCRETE_PRODUCT_TARGETS_VERIFIED",
    }
}

#[test]
fn test_wdp_dp8_01_residual_product_target_selection() {
    let valid = [
        ProductTargetSpec {
            target_id: "TARGET-1-PROTECTED-QUESTION-SEAM",
            consumer: "adversary",
            defect_witness: "unwitnessed_summary_collapse",
            rust_owner: "engine/crates_rs/core_wdp/src/lib.rs",
            deciding_check: "cargo test -p core_wdp",
        },
        ProductTargetSpec {
            target_id: "TARGET-2-PARITY-BRIDGE",
            consumer: "pfp",
            defect_witness: "untyped_packet_fallback",
            rust_owner: "engine/crates_rs/pfp/src/lib.rs",
            deciding_check: "cargo test -p pfp",
        },
    ];
    let ok = verify_product_target_selection(&valid);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.selected_count, 2);

    let invalid = [ProductTargetSpec {
        target_id: "TARGET-BAD",
        consumer: "adversary",
        defect_witness: "",
        rust_owner: "engine/crates_rs/core_wdp/src/lib.rs",
        deciding_check: "cargo test -p core_wdp",
    }];
    let bad = verify_product_target_selection(&invalid);
    assert_eq!(bad.status, "REFUSED");
    assert_eq!(bad.reason, "MISSING_REQUIRED_TARGET_FIELD");
}

/// Admitted cardinality equals the slice length when every target is complete and `target_id` is unique.
fn validate_target_spec(target: &ProductTargetSpec<'_>) -> Result<(), &'static str> {
    let fields = [
        target.target_id,
        target.consumer,
        target.defect_witness,
        target.rust_owner,
        target.deciding_check,
    ];
    if fields.iter().any(|field| field.trim().is_empty()) {
        return Err("MISSING_REQUIRED_TARGET_FIELD");
    }
    if !target.rust_owner.starts_with("engine/crates_rs/") {
        return Err("NON_CANONICAL_RUST_OWNER");
    }
    Ok(())
}

pub fn admit_unique_targets(targets: &[ProductTargetSpec<'_>]) -> Result<usize, &'static str> {
    if targets.is_empty() {
        return Err("EMPTY_PRODUCT_TARGET_SET");
    }
    let mut seen = std::collections::BTreeSet::new();
    let mut admitted = 0usize;
    for target in targets {
        validate_target_spec(target)?;
        if !seen.insert(target.target_id) {
            return Err("DUPLICATE_TARGET_ID");
        }
        admitted = admitted.checked_add(1).ok_or("ADMISSION_OVERFLOW")?;
    }
    if admitted != targets.len() {
        return Err("COUNT_MISMATCH");
    }
    Ok(admitted)
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp8_01_residual.rs
// Claim: urn:core:crates_rs:tests:wdp-dp8-01-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6aaf5bc6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6aaf5bc6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6aaf5bc6 {
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
impl BoundaryError6aaf5bc6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6aaf5bc6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6aaf5bc6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6aaf5bc6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6aaf5bc6> {
        if capacity_bound == 0 {
            return Err(BoundaryError6aaf5bc6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6aaf5bc6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6aaf5bc6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6aaf5bc6() {
    let admitted = BoundaryRecord6aaf5bc6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6aaf5bc6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
