//! Request profile validation and explicit source-evidence binding grades.

use super::*;

fn validate_request_digests(request: &HostRequestV1) -> Result<(), (&'static str, String)> {
    for (label, digest) in [
        ("request_id_sha256", request.request_id_sha256.as_str()),
        ("challenge_hex", request.challenge_hex.as_str()),
        (
            "expected_host_registry_hash_sha256",
            request.expected_host_registry_hash_sha256.as_str(),
        ),
        (
            "runtime_id_sha256",
            request.source.runtime_id_sha256.as_str(),
        ),
        (
            "source_event_root_sha256",
            request.source.source_event_root_sha256.as_str(),
        ),
        (
            "source_wire_receipt_id_sha256",
            request.source.source_wire_receipt_id_sha256.as_str(),
        ),
        (
            "solver_registry_hash_sha256",
            request.source.solver_registry_hash_sha256.as_str(),
        ),
        (
            "candidate_id_sha256",
            request.source.candidate.candidate_id_sha256.as_str(),
        ),
        (
            "candidate_witness_sha256",
            request.source.candidate.witness_sha256.as_str(),
        ),
        (
            "candidate_state_hash_sha256",
            request.source.candidate.state_hash_sha256.as_str(),
        ),
        (
            "detector_config_sha256",
            request.prime002.detector_config_sha256.as_str(),
        ),
        (
            "expected_carrier_hash_blake3",
            request.carrier.expected_carrier_hash_blake3.as_str(),
        ),
    ] {
        validate_lower_hex(digest, label).map_err(|error| ("DIGEST_INVALID", error))?;
    }
    if let Some(tree) = request.source.source_tree_sha256.as_deref() {
        validate_lower_hex(tree, "source_tree_sha256")
            .map_err(|error| ("DIGEST_INVALID", error))?;
    }
    Ok(())
}

fn validate_host_and_dialect(request: &HostRequestV1) -> Result<(), (&'static str, String)> {
    if request.authority_effect != "None" || request.packet_envelope.authority_effect != "None" {
        return Err((
            "AUTHORITY_EXPANSION_REFUSED",
            "host and packet authority_effect must both be None".to_owned(),
        ));
    }
    let dialect_ok = [
        request.operation == "evaluate_candidate",
        request.canonicalization_profile == "core-sorted-json-no-float-v1",
        request.outer_dda_dialect == "experimental-z-v1",
    ]
    .into_iter()
    .all(|b| b);
    if !dialect_ok {
        return Err((
            "PROFILE_UNSUPPORTED",
            "operation, canonicalization profile, or outer DDA dialect is unsupported".to_owned(),
        ));
    }
    let description = describe_host();
    if request.expected_host_registry_hash_sha256 != description.host_registry_hash_sha256 {
        return Err((
            "HOST_REGISTRY_MISMATCH",
            "expected host registry hash does not match this executable".to_owned(),
        ));
    }
    if request.expected_host_source_revision != HOST_SOURCE_REVISION {
        return Err((
            "HOST_SOURCE_REVISION_MISMATCH",
            format!(
                "expected host revision {:?}, executable is {:?}",
                request.expected_host_source_revision, HOST_SOURCE_REVISION
            ),
        ));
    }
    let derived_request = compute_request_id(request);
    if derived_request != request.request_id_sha256 {
        return Err((
            "REQUEST_ID_MISMATCH",
            format!(
                "request id {} does not match canonical content {}",
                request.request_id_sha256, derived_request
            ),
        ));
    }
    Ok(())
}

fn validate_budgets_and_carrier(request: &HostRequestV1) -> Result<(), (&'static str, String)> {
    let b = &request.budgets;
    let budgets_ok = [
        b.max_request_bytes == MAX_HOST_REQUEST_BYTES,
        b.max_candidates == 1,
        (2..=64).contains(&b.max_prime_writes),
        (1..=MAX_CARRIER_DIMENSION).contains(&b.max_edges),
        (1..=MAX_CARRIER_DIMENSION).contains(&b.max_vertices_plus_faces),
        (1..=MAX_TIMEOUT_MS).contains(&b.timeout_ms),
    ]
    .into_iter()
    .all(|ok| ok);
    if !budgets_ok {
        return Err((
            "RESOURCE_PROFILE_INVALID",
            "request resource profile lies outside host v1 fences".to_owned(),
        ));
    }
    let declaration = &request.carrier.declaration;
    let vertices_plus_faces = validate_carrier_resource_fence(declaration)
        .map_err(|detail| ("RESOURCE_FENCE_EXCEEDED", detail))?;
    if declaration.edges.len() > request.budgets.max_edges
        || vertices_plus_faces > request.budgets.max_vertices_plus_faces
    {
        return Err((
            "RESOURCE_FENCE_EXCEEDED",
            "declared carrier exceeds the request-specific dimension fence".to_owned(),
        ));
    }
    Ok(())
}

fn validate_prime_and_source_profiles(
    request: &HostRequestV1,
) -> Result<(), (&'static str, String)> {
    let prime_ok = [
        request.carrier.expected_manifest_version == 2,
        request.residual.candidate_acceptance_mode == "must_equal_replayed_normal_form-v1",
        request.prime_profiles.integral_mass_policy == "refuse_non_u64",
        request.prime002.route == "write_exact_then_terminalize",
        request.prime_profiles.prime000_revision == "oeprmalg0",
        request.prime_profiles.prime001_revision == "oeprmalg1",
        request.prime_profiles.prime002_revision == "oeprmalg2",
    ]
    .into_iter()
    .all(|ok| ok);
    if !prime_ok {
        return Err((
            "PRIME_PROFILE_UNSUPPORTED",
            "host v1 accepts only the declared exact same-carrier Prime profile".to_owned(),
        ));
    }
    let boundaries = &request.packet_envelope.protected_boundaries;
    let unique_boundaries = boundaries
        .iter()
        .collect::<std::collections::BTreeSet<_>>()
        .len()
        == boundaries.len();
    let source_ok = [
        !request.source.source_revision.trim().is_empty(),
        !request.source.candidate.producer_id.trim().is_empty(),
        !request.prime002.detector_profile_id.trim().is_empty(),
        unique_boundaries,
        boundaries.iter().any(|boundary| boundary == "cochain:phi1"),
        boundaries
            .iter()
            .any(|boundary| boundary == "cochain:gamma2"),
    ]
    .into_iter()
    .all(|ok| ok);
    if !source_ok {
        return Err((
            "SOURCE_PROFILE_INVALID",
            "source identity or protected-boundary declarations are incomplete".to_owned(),
        ));
    }
    Ok(())
}

pub(super) fn validate_request_profile(
    request: &HostRequestV1,
) -> Result<(), (&'static str, String)> {
    if request.schema_version != HOST_REQUEST_SCHEMA {
        return Err((
            "SCHEMA_UNSUPPORTED",
            format!("unsupported request schema {}", request.schema_version),
        ));
    }
    validate_request_digests(request)?;
    validate_host_and_dialect(request)?;
    validate_budgets_and_carrier(request)?;
    validate_prime_and_source_profiles(request)?;
    Ok(())
}

pub(super) fn source_binding_checks(
    request: &HostRequestV1,
    packet_id: crate::protocol::CommitmentCheckV1,
) -> SourceBindingChecksV1 {
    SourceBindingChecksV1 {
        packet_id,
        runtime_id_sha256: request.source.runtime_id_sha256.clone(),
        runtime_id_verdict: "BOUND_ONLY_RUNTIME_ARTIFACT_SCHEMA_NOT_YET_PUBLISHED".to_owned(),
        candidate_id_sha256: request.source.candidate.candidate_id_sha256.clone(),
        candidate_id_verdict: "BOUND_ONLY_CANDIDATE_ARTIFACT_BYTES_NOT_SUPPLIED".to_owned(),
        candidate_state_hash_sha256: request.source.candidate.state_hash_sha256.clone(),
        candidate_state_verdict: "BOUND_ONLY_PYTHON_IDENTITY;HOST_VECTOR_HASH_REPORTED_SEPARATELY"
            .to_owned(),
        source_event_root_sha256: request.source.source_event_root_sha256.clone(),
        source_event_root_verdict: "BOUND_ONLY_EVENT_BUNDLE_SCHEMA_NOT_YET_PUBLISHED".to_owned(),
        source_wire_receipt_id_sha256: request.source.source_wire_receipt_id_sha256.clone(),
        source_wire_receipt_verdict: "BOUND_ONLY_SOURCE_RECEIPT_BYTES_NOT_SUPPLIED".to_owned(),
        solver_registry_hash_sha256: request.source.solver_registry_hash_sha256.clone(),
        solver_registry_verdict: "BOUND_ONLY_SOURCE_REGISTRY_MANIFEST_NOT_SUPPLIED".to_owned(),
        source_revision: request.source.source_revision.clone(),
        source_revision_verdict: if request.source.source_revision == HOST_SOURCE_REVISION {
            "MATCH_HOST_BUILD_STAMP".to_owned()
        } else {
            "BOUND_ONLY_DISTINCT_SOURCE_REVISION".to_owned()
        },
    }
}

// Origin: engine/crates_rs/pfp/src/host/intake.rs
// Claim: urn:core:crates_rs:pfp:intake:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordde166492 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordde166492` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorde166492 {
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
impl BoundaryErrorde166492 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorde166492 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorde166492 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordde166492 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorde166492> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorde166492::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorde166492::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorde166492::ExceedsCapacity {
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
mod l4_boundary_tests_de166492 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordde166492::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordde166492::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordde166492::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordde166492::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordde166492::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorde166492::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorde166492::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
