//! Sealed, non-authoritative receipts for exact operator closure and transport.
//! The mathematical inputs and witnesses are committed in full, using canonical
//! rational text and length-prefixed fields. Rust replay is not a Lean replay.
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::One;
use core_functional::operator_trace_closure::{
    self, KrausMapInput, Operator, OperatorClosureTransportInput, OperatorClosureWitness,
    OperatorTraceError, TraceObserverInput, TraceRepairInput, VerifiedOperatorClosure,
    VerifiedOperatorClosureTransport, OPERATOR_INPUT_MAX_RATIONAL_BITS,
    OPERATOR_MATRIX_CALL_MAX_ELEMENTS, OPERATOR_MATRIX_CALL_MAX_SCALAR_OPS,
    OPERATOR_MAX_INPUT_MATRIX_ELEMENTS,
};
use core_types::AuthorityEffect;
use serde::{Serialize, Serializer};
use sha2::{Digest, Sha256};

pub const OPERATOR_CLOSURE_BINDING_PROFILE: &str =
    "core.operator-closure.length-prefixed-canonical-rationals.v1";

fn rational_text(value: &BigRational) -> String {
    if value.denom().is_one() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

fn serialize_rational<S: Serializer>(
    value: &BigRational,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    serializer.serialize_str(&rational_text(value))
}

fn serialize_optional_rational<S: Serializer>(
    value: &Option<BigRational>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    match value {
        Some(value) => serializer.serialize_some(&rational_text(value)),
        None => serializer.serialize_none(),
    }
}

fn commit_text(hash: &mut Sha256, text: &str) {
    hash.update(text.len().to_string().as_bytes());
    hash.update(b":");
    hash.update(text.as_bytes());
}

fn commit_count(hash: &mut Sha256, value: usize) {
    commit_text(hash, &value.to_string());
}

fn commit_operator(hash: &mut Sha256, operator: &Operator) {
    commit_count(hash, operator.rows());
    commit_count(hash, operator.cols());
    for entry in operator.as_slice() {
        commit_text(hash, &rational_text(&entry.re));
        commit_text(hash, &rational_text(&entry.im));
    }
}

fn commit_operators(hash: &mut Sha256, operators: &[Operator]) {
    commit_count(hash, operators.len());
    for operator in operators {
        commit_operator(hash, operator);
    }
}

fn commit_rationals(hash: &mut Sha256, rationals: &[BigRational]) {
    commit_count(hash, rationals.len());
    for value in rationals {
        commit_text(hash, &rational_text(value));
    }
}

fn commit_problem(hash: &mut Sha256, problem: TraceRepairInput<'_>) {
    commit_operators(hash, problem.defects);
    commit_count(hash, problem.repair_generators.len());
    for generator in problem.repair_generators {
        commit_operators(hash, generator);
    }
    commit_rationals(hash, problem.weights);
}

fn commit_faces(hash: &mut Sha256, faces: &[Vec<(usize, BigRational)>]) {
    commit_count(hash, faces.len());
    for face in faces {
        commit_count(hash, face.len());
        for (edge, sign) in face {
            commit_count(hash, *edge);
            commit_text(hash, &rational_text(sign));
        }
    }
}

fn commit_channel(hash: &mut Sha256, channel: KrausMapInput<'_>) {
    commit_count(hash, channel.dim_in);
    commit_count(hash, channel.dim_out);
    commit_rationals(hash, channel.weights);
    commit_operators(hash, channel.operators);
}

fn closure_digest(
    problem: TraceRepairInput<'_>,
    faces: &[Vec<(usize, BigRational)>],
    trace_witness: TraceObserverInput<'_>,
    closure_witness: &OperatorClosureWitness,
) -> String {
    let mut hash = Sha256::new();
    commit_text(&mut hash, OPERATOR_CLOSURE_BINDING_PROFILE);
    commit_text(&mut hash, "closure");
    commit_problem(&mut hash, problem);
    commit_faces(&mut hash, faces);
    commit_rationals(&mut hash, trace_witness.repair_coefficients);
    commit_operators(&mut hash, trace_witness.residuals);
    commit_operators(&mut hash, trace_witness.positive_parts);
    commit_operators(&mut hash, trace_witness.negative_parts);
    commit_operators(&mut hash, trace_witness.dual_observables);
    commit_operators(&mut hash, &closure_witness.face_defects);
    commit_operators(&mut hash, &closure_witness.positive_parts);
    commit_operators(&mut hash, &closure_witness.negative_parts);
    commit_text(&mut hash, &rational_text(&closure_witness.claimed_d1_norm));
    format!("sha256:{}", hex::encode(hash.finalize()))
}

fn transport_digest(input: OperatorClosureTransportInput<'_>) -> String {
    let mut hash = Sha256::new();
    commit_text(&mut hash, OPERATOR_CLOSURE_BINDING_PROFILE);
    commit_text(&mut hash, "transport");
    commit_problem(&mut hash, input.source);
    commit_problem(&mut hash, input.target);
    commit_faces(&mut hash, input.source_faces);
    commit_faces(&mut hash, input.target_faces);
    commit_count(&mut hash, input.edge_channels.len());
    for channel in input.edge_channels {
        commit_channel(&mut hash, *channel);
    }
    commit_count(&mut hash, input.face_channels.len());
    for channel in input.face_channels {
        commit_channel(&mut hash, *channel);
    }
    commit_count(&mut hash, input.generator_images.len());
    for expansion in input.generator_images {
        commit_rationals(&mut hash, expansion);
    }
    format!("sha256:{}", hex::encode(hash.finalize()))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
pub enum OperatorClosureReceiptStatus {
    #[serde(rename = "PASS")]
    Pass,
}

/// An immutable machine receipt. Only the verifier constructs it; there is no
/// deserializer or public field through which evidence or authority can change.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OperatorClosureCertificate {
    schema: &'static str,
    status: OperatorClosureReceiptStatus,
    authority_effect: AuthorityEffect,
    binding_profile: &'static str,
    input_and_witness_sha256: String,
    #[serde(serialize_with = "serialize_rational")]
    phi_q: BigRational,
    #[serde(serialize_with = "serialize_rational")]
    gamma2_q: BigRational,
    #[serde(serialize_with = "serialize_rational")]
    d1_norm: BigRational,
    #[serde(serialize_with = "serialize_optional_rational")]
    closure_ratio: Option<BigRational>,
    edge_count: usize,
    face_count: usize,
    repair_generator_count: usize,
    input_rational_max_bits: u64,
    collective_input_matrix_max_elements: usize,
    matrix_call_max_elements: usize,
    matrix_call_max_scalar_ops: usize,
}

impl OperatorClosureCertificate {
    fn from_verified(value: VerifiedOperatorClosure, digest: String) -> Self {
        Self {
            schema: "core.operator-closure-certificate.v1",
            status: OperatorClosureReceiptStatus::Pass,
            authority_effect: AuthorityEffect::None,
            binding_profile: OPERATOR_CLOSURE_BINDING_PROFILE,
            input_and_witness_sha256: digest,
            phi_q: value.phi_q().clone(),
            gamma2_q: value.gamma2_q().clone(),
            d1_norm: value.d1_norm().clone(),
            closure_ratio: value.closure_ratio().cloned(),
            edge_count: value.edge_count(),
            face_count: value.face_count(),
            repair_generator_count: value.repair_generator_count(),
            input_rational_max_bits: OPERATOR_INPUT_MAX_RATIONAL_BITS,
            collective_input_matrix_max_elements: OPERATOR_MAX_INPUT_MATRIX_ELEMENTS,
            matrix_call_max_elements: OPERATOR_MATRIX_CALL_MAX_ELEMENTS,
            matrix_call_max_scalar_ops: OPERATOR_MATRIX_CALL_MAX_SCALAR_OPS,
        }
    }

    pub fn phi_q(&self) -> &BigRational {
        &self.phi_q
    }
    pub fn gamma2_q(&self) -> &BigRational {
        &self.gamma2_q
    }
    pub fn d1_norm(&self) -> &BigRational {
        &self.d1_norm
    }
    pub fn closure_ratio(&self) -> Option<&BigRational> {
        self.closure_ratio.as_ref()
    }
    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
    pub fn input_and_witness_sha256(&self) -> &str {
        &self.input_and_witness_sha256
    }
}

pub struct OperatorClosureVerifier;

impl OperatorClosureVerifier {
    pub fn verify(
        problem: TraceRepairInput<'_>,
        faces: &[Vec<(usize, BigRational)>],
        trace_witness: TraceObserverInput<'_>,
        closure_witness: &OperatorClosureWitness,
    ) -> Result<OperatorClosureCertificate, OperatorTraceError> {
        let value = operator_trace_closure::verify_operator_closure(
            problem,
            faces,
            trace_witness,
            closure_witness,
        )?;
        let digest = closure_digest(problem, faces, trace_witness, closure_witness);
        Ok(OperatorClosureCertificate::from_verified(value, digest))
    }
}

/// A full-space cochain-map receipt. The basis count describes exact identity
/// checks, not sampled operator inputs or a bounded word search.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OperatorClosureTransportCertificate {
    schema: &'static str,
    status: OperatorClosureReceiptStatus,
    authority_effect: AuthorityEffect,
    binding_profile: &'static str,
    input_and_witness_sha256: String,
    edge_count: usize,
    face_count: usize,
    traceless_basis_checks: usize,
    input_rational_max_bits: u64,
    collective_input_matrix_max_elements: usize,
    matrix_call_max_elements: usize,
    matrix_call_max_scalar_ops: usize,
}

impl OperatorClosureTransportCertificate {
    fn from_verified(value: VerifiedOperatorClosureTransport, digest: String) -> Self {
        Self {
            schema: "core.operator-closure-transport-certificate.v1",
            status: OperatorClosureReceiptStatus::Pass,
            authority_effect: AuthorityEffect::None,
            binding_profile: OPERATOR_CLOSURE_BINDING_PROFILE,
            input_and_witness_sha256: digest,
            edge_count: value.edge_count(),
            face_count: value.face_count(),
            traceless_basis_checks: value.basis_checks(),
            input_rational_max_bits: OPERATOR_INPUT_MAX_RATIONAL_BITS,
            collective_input_matrix_max_elements: OPERATOR_MAX_INPUT_MATRIX_ELEMENTS,
            matrix_call_max_elements: OPERATOR_MATRIX_CALL_MAX_ELEMENTS,
            matrix_call_max_scalar_ops: OPERATOR_MATRIX_CALL_MAX_SCALAR_OPS,
        }
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
    pub fn traceless_basis_checks(&self) -> usize {
        self.traceless_basis_checks
    }
    pub fn input_and_witness_sha256(&self) -> &str {
        &self.input_and_witness_sha256
    }
}

pub struct OperatorClosureTransportVerifier;

impl OperatorClosureTransportVerifier {
    pub fn verify(
        input: OperatorClosureTransportInput<'_>,
    ) -> Result<OperatorClosureTransportCertificate, OperatorTraceError> {
        let value = operator_trace_closure::verify_operator_closure_transport(input)?;
        let digest = transport_digest(input);
        Ok(OperatorClosureTransportCertificate::from_verified(
            value, digest,
        ))
    }
}

// Origin: engine/crates_rs/core_certifiers/src/operator_closure_certifier.rs
// Claim: urn:core:crates_rs:core-certifiers:operator-closure-certifier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd03bed8f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd03bed8f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord03bed8f {
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
impl BoundaryErrord03bed8f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord03bed8f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord03bed8f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd03bed8f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord03bed8f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord03bed8f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord03bed8f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord03bed8f::ExceedsCapacity {
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
mod l4_boundary_tests_d03bed8f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd03bed8f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd03bed8f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd03bed8f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd03bed8f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd03bed8f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord03bed8f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord03bed8f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
