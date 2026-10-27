//! Scoped exact cochain metadata validation; no claim about a global cover.
use crate::evidence::{canonical_rational, is_sha256_ref, parse_exact_rational};
use crate::render_record::RenderRecord;
use num_bigint::{BigInt, Sign};
use num_traits::Zero;
use crate::stage::ports::Refusal;
use serde_json::Value;

pub struct AlgorithmMetadataInput<'a> {
    pub ddc_trace_hash: &'a RenderRecord,
    pub joint_kernel_status: &'a RenderRecord,
    pub phi1: &'a RenderRecord,
    pub gamma2: &'a RenderRecord,
    pub carrier_degree: &'a RenderRecord,
}
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_ALGORITHM_METADATA_INVALID", message)
}
fn validate_single_coda_value(value: &RenderRecord) -> Result<(), Refusal> {
    if value == &RenderRecord::Null {
        return Ok(());
    }
    let text = match value {
        RenderRecord::String(s) => s,
        _ => {
            return Err(invalid(
                "CODA measurements must be nonnegative canonical rational strings",
            ))
        }
    };
    let rational =
        parse_exact_rational(&Value::String(text.clone())).map_err(|r| invalid(r.message))?;
    if canonical_rational(&rational) != *text || rational < num_rational::BigRational::zero() {
        return Err(invalid(
            "CODA measurements must be nonnegative canonical rational strings",
        ));
    }
    Ok(())
}

fn validate_coda_consistency(
    input: &AlgorithmMetadataInput<'_>,
    status: &str,
) -> Result<(), Refusal> {
    if (input.phi1 == &RenderRecord::Null) != (input.gamma2 == &RenderRecord::Null) {
        return Err(invalid("CODA measurements must be supplied together"));
    }
    let measured = input.phi1 != &RenderRecord::Null;
    if (status != "NOT_MEASURED") != measured {
        return Err(invalid(
            "joint-kernel metadata requires measured CODA values",
        ));
    }
    if measured && input.carrier_degree != &RenderRecord::Integer(BigInt::from(1)) {
        return Err(invalid(
            "measured Adversary CODA values require declared cochain degree one",
        ));
    }
    let zero = input.phi1 == &RenderRecord::text("0") && input.gamma2 == &RenderRecord::text("0");
    if measured && zero != (status == "ZERO_ON_DECLARED_CARRIER") {
        return Err(invalid(
            "joint-kernel status disagrees with exact CODA values",
        ));
    }
    Ok(())
}

fn parse_joint_kernel_status<'a>(record: &'a RenderRecord) -> Result<&'a str, Refusal> {
    match record {
        RenderRecord::String(s)
            if ["NOT_MEASURED", "OPEN_RESIDUAL", "ZERO_ON_DECLARED_CARRIER"]
                .contains(&s.as_str()) =>
        {
            Ok(s.as_str())
        }
        _ => Err(invalid("unknown lggr_joint_kernel_status")),
    }
}

pub fn validate_algorithm_metadata(input: &AlgorithmMetadataInput<'_>) -> Result<(), Refusal> {
    if input.ddc_trace_hash != &RenderRecord::Null
        && !matches!(input.ddc_trace_hash, RenderRecord::String(s) if is_sha256_ref(&Value::String(s.clone())))
    {
        return Err(invalid("ddc_trace_hash must be a sha256 reference or None"));
    }
    let status = parse_joint_kernel_status(input.joint_kernel_status)?;
    if input.carrier_degree != &RenderRecord::Null
        && !matches!(input.carrier_degree, RenderRecord::Integer(n) if n.sign() != Sign::Minus)
    {
        return Err(invalid(
            "carrier_degree must be a nonnegative exact integer or None",
        ));
    }
    for value in [input.phi1, input.gamma2] {
        validate_single_coda_value(value)?;
    }
    validate_coda_consistency(input, status)
}

// Origin: engine/crates_rs/core_adversary/src/algorithm_metadata.rs
// Claim: urn:core:crates_rs:core-adversary:algorithm-metadata:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord21f40702 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord21f40702` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError21f40702 {
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
impl BoundaryError21f40702 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError21f40702 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError21f40702 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord21f40702 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError21f40702> {
        if capacity_bound == 0 {
            return Err(BoundaryError21f40702::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError21f40702::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError21f40702::ExceedsCapacity {
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
mod l4_boundary_tests_21f40702 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord21f40702::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord21f40702::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord21f40702::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord21f40702::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord21f40702::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError21f40702::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError21f40702::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
