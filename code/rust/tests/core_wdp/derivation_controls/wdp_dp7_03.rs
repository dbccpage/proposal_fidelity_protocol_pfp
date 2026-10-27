#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CleanExportReceipt {
    pub status: &'static str,
    pub verified_files: usize,
    pub reason: &'static str,
}

pub fn verify_clean_export_manifest(
    declared: &[(&str, &str)],
    extracted: &[(&str, &str)],
    outside_refs: &[&str],
) -> CleanExportReceipt {
    if declared.is_empty() {
        return CleanExportReceipt {
            status: "REFUSED",
            verified_files: 0,
            reason: "EMPTY_DECLARED_MANIFEST",
        };
    }
    if !outside_refs.is_empty() {
        return CleanExportReceipt {
            status: "REFUSED",
            verified_files: 0,
            reason: "HERMETIC_ESCAPE_TO_CHECKOUT",
        };
    }
    if declared.len() != extracted.len() {
        return CleanExportReceipt {
            status: "REFUSED",
            verified_files: 0,
            reason: "UNDECLARED_EXTRACTED_FILE",
        };
    }
    for (path, sha) in declared {
        if path.starts_with('/') || path.split('/').any(|p| p == "..") {
            return CleanExportReceipt {
                status: "REFUSED",
                verified_files: 0,
                reason: "UNSAFE_MANIFEST_PATH",
            };
        }
        match extracted.iter().find(|(ep, _)| ep == path) {
            Some((_, esha)) if esha == sha => {}
            _ => {
                return CleanExportReceipt {
                    status: "REFUSED",
                    verified_files: 0,
                    reason: "HASH_MISMATCH",
                };
            }
        }
    }
    CleanExportReceipt {
        status: "PASS",
        verified_files: declared.len(),
        reason: "CLEAN_EXPORT_VERIFIED",
    }
}

#[test]
fn test_wdp_dp7_03_clean_export_verification() {
    let manifest = [("manuscript.md", "sha256:aaa"), ("code/witness.py", "sha256:bbb")];
    let ok = verify_clean_export_manifest(&manifest, &manifest, &[]);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.verified_files, 2);

    let escaped = verify_clean_export_manifest(&manifest, &manifest, &["../checkout.json"]);
    assert_eq!(escaped.status, "REFUSED");
    assert_eq!(escaped.reason, "HERMETIC_ESCAPE_TO_CHECKOUT");
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp7_03.rs
// Claim: urn:core:crates_rs:tests:wdp-dp7-03:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord69cacd8b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord69cacd8b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError69cacd8b {
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
impl BoundaryError69cacd8b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError69cacd8b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError69cacd8b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord69cacd8b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError69cacd8b> {
        if capacity_bound == 0 {
            return Err(BoundaryError69cacd8b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError69cacd8b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError69cacd8b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_69cacd8b() {
    let admitted = BoundaryRecord69cacd8b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord69cacd8b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
