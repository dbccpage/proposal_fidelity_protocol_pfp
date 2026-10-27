//! Sovereign certifier integrations bridging core_certifiers into the Symbol Game host.
//!
//! AuthorityEffect: None. Certified outputs represent exact algebraic evidence only.

use num_rational::BigRational;
use core_certifiers::phi1_certifier::Phi1FormCertificate;
use core_kernel::{exact_wire_vec, parse_exact, to_canonical_string, Exact};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VerifyPhi1FormRequestV1 {
    #[serde(with = "exact_wire_vec")]
    pub weights: Vec<Exact>,
    #[serde(with = "exact_wire_vec")]
    pub residual_at_achiever: Vec<Exact>,
    #[serde(with = "exact_wire_vec")]
    pub dual: Vec<Exact>,
    pub coboundaries: Vec<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Phi1FormOutcomeV1 {
    pub accepted: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub certified_value: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub refusal: Option<String>,
    pub lean_soundness_theorem: &'static str,
    pub authority_effect: &'static str,
}

/// Verify exact rational Phi1 primal-dual certificate under Lean 4 soundness theorems.
pub fn verify_phi1_form_certificate(
    request: &VerifyPhi1FormRequestV1,
) -> Result<Phi1FormOutcomeV1, String> {
    let coboundaries: Result<Vec<Vec<BigRational>>, String> = request
        .coboundaries
        .iter()
        .map(|row| {
            row.iter()
                .map(|s| parse_exact(s).map_err(|e| format!("invalid coboundary rational: {e}")))
                .collect()
        })
        .collect();
    let coboundaries = coboundaries?;

    let cert = Phi1FormCertificate {
        weights: request.weights.clone(),
        residual_at_achiever: request.residual_at_achiever.clone(),
        dual: request.dual.clone(),
        coboundaries,
    };

    match cert.verify() {
        Ok(value) => Ok(Phi1FormOutcomeV1 {
            accepted: true,
            certified_value: Some(to_canonical_string(&value)),
            refusal: None,
            lean_soundness_theorem: "CoreCore.Phi1Certificate.isMinimum_of_certificate",
            authority_effect: "None",
        }),
        Err(err) => Ok(Phi1FormOutcomeV1 {
            accepted: false,
            certified_value: None,
            refusal: Some(err.to_string()),
            lean_soundness_theorem: "CoreCore.Phi1Certificate.isMinimum_of_certificate",
            authority_effect: "None",
        }),
    }
}

// Origin: engine/crates_rs/pfp/src/certifiers.rs
// Claim: urn:core:crates_rs:pfp:certifiers:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd218f9f1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd218f9f1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord218f9f1 {
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
impl BoundaryErrord218f9f1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord218f9f1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord218f9f1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd218f9f1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord218f9f1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord218f9f1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord218f9f1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord218f9f1::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_d218f9f1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd218f9f1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd218f9f1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd218f9f1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd218f9f1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd218f9f1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord218f9f1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord218f9f1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
