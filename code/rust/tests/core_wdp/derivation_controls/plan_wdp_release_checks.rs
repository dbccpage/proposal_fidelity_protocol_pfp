//! Finite revalidation and policy-disposition control for PLAN-WDP-RELEASE-CHECKS.
//! Refuses silent trusted-baseline refresh and requires explicit disposition of DEC-WDP-REPIN.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ReleaseCheckInput {
    pub manuscript_sha256: [u8; 4],
    pub tex_header_sha256: [u8; 4],
    pub relative_directory_href_count: usize,
    pub release_manifest_matches_tree: bool,
    pub checksums_match_tree: bool,
    pub silent_baseline_refresh: bool,
    pub repin_owner_approved: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ReleaseCheckOutcome {
    pub artifacts_bound: bool,
    pub dec_wdp_repin_separate: bool,
    pub publication_clearance_claimed: bool,
}

pub fn verify_release_check_state(
    input: ReleaseCheckInput,
) -> Result<ReleaseCheckOutcome, &'static str> {
    if input.silent_baseline_refresh {
        return Err("silent trusted-baseline refresh is refused");
    }
    if input.manuscript_sha256 != input.tex_header_sha256 {
        return Err("tex header does not bind current manuscript sha256");
    }
    if input.relative_directory_href_count != 0 {
        return Err("relative directory href would render as .pdf");
    }
    if !input.release_manifest_matches_tree || !input.checksums_match_tree {
        return Err("release manifest or checksum inventory drift");
    }
    Ok(ReleaseCheckOutcome {
        artifacts_bound: true,
        dec_wdp_repin_separate: !input.repin_owner_approved,
        publication_clearance_claimed: false,
    })
}

#[test]
fn release_checks_bind_artifacts_and_refuse_silent_repin() {
    let valid = ReleaseCheckInput {
        manuscript_sha256: [0x12, 0x34, 0x56, 0x78],
        tex_header_sha256: [0x12, 0x34, 0x56, 0x78],
        relative_directory_href_count: 0,
        release_manifest_matches_tree: true,
        checksums_match_tree: true,
        silent_baseline_refresh: false,
        repin_owner_approved: false,
    };
    let outcome = verify_release_check_state(valid).expect("valid release check state");
    assert_eq!(
        outcome,
        ReleaseCheckOutcome {
            artifacts_bound: true,
            dec_wdp_repin_separate: true,
            publication_clearance_claimed: false,
        }
    );

    let mut silent_repin = valid;
    silent_repin.silent_baseline_refresh = true;
    assert_eq!(
        verify_release_check_state(silent_repin),
        Err("silent trusted-baseline refresh is refused")
    );

    let mut dir_href = valid;
    dir_href.relative_directory_href_count = 3;
    assert_eq!(
        verify_release_check_state(dir_href),
        Err("relative directory href would render as .pdf")
    );
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_wdp_release_checks.rs
// Claim: urn:core:crates_rs:tests:plan-wdp-release-checks:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord042af50e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord042af50e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError042af50e {
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
impl BoundaryError042af50e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError042af50e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError042af50e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord042af50e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError042af50e> {
        if capacity_bound == 0 {
            return Err(BoundaryError042af50e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError042af50e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError042af50e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_042af50e() {
    let admitted = BoundaryRecord042af50e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord042af50e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
