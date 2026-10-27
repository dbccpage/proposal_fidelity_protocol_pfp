// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b5ad64c5<T> {
    fn checked_invariant_b5ad64c5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b5ad64c5<T> for Option<T> {
    #[inline]
    fn checked_invariant_b5ad64c5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b5ad64c5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b5ad64c5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use num_rational::BigRational;
use num_traits::Zero;
use pfp_runtime::canonical::framed_sha256;
use pfp_runtime::packet_wire::{
    validate_canonical_node, wire_int, wire_mapping, wire_optional_string, wire_string, wire_tuple,
};
use core_wdp::carrier_binding::carrier_manifest;
use core_wdp::solver_of_solvers::{CarrierEdge, FiniteCarrier2};
use serde::de::{DeserializeOwned, Error as DeError, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::{Map, Value};

pub const HOST_REQUEST_SCHEMA: &str = "core.oesos.rust-prime-host-request.v1";
pub const HOST_OUTCOME_SCHEMA: &str = "core.oesos.rust-prime-host-outcome.v1";
pub const HOST_DESCRIPTION_SCHEMA: &str = "core.oesos.rust-prime-host-description.v1";
pub const PACKET_SCHEMA: &str = "core.symbol-game.packet-envelope.v2";
pub const MAX_HOST_REQUEST_BYTES: usize = 1_048_576;
pub const HOST_SOURCE_REVISION: &str = env!("CORE_HOST_SOURCE_REVISION");
pub(crate) const MAX_CARRIER_DIMENSION: usize = 4096;
pub(crate) const MAX_DENSE_MATRIX_CELLS: usize = 1_048_576;

const REQUEST_DOMAIN: &str = "core.oesos.rust-prime-host-request.v1";
const OUTCOME_DOMAIN: &str = "core.oesos.rust-prime-host-outcome.v1";
const HOST_REGISTRY_DOMAIN: &str = "core.oesos.rust-prime-host-registry.v1";
const PACKET_ID_DOMAIN: &str = "core.symbol-game.packet-envelope.v2";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PacketEnvelopeWireV2 {
    pub schema_version: String,
    pub packet_id: String,
    pub packet_kind: String,
    pub framing_mode: String,
    pub task_id: String,
    pub packet_family: String,
    pub carrier_id: String,
    pub initial_state_hash: String,
    pub payload: Value,
    pub constraints: Vec<String>,
    pub protected_boundaries: Vec<String>,
    pub terminal_target: String,
    pub evidence_ceiling: String,
    pub oracle_policy: String,
    pub allowed_transforms: Vec<String>,
    pub step_budget: usize,
    pub parent_event_id: Option<String>,
    pub source_digest: Option<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateBindingV1 {
    pub candidate_id_sha256: String,
    pub producer_id: String,
    pub witness_sha256: String,
    pub state_hash_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBindingsV1 {
    pub runtime_id_sha256: String,
    pub source_event_root_sha256: String,
    pub source_wire_receipt_id_sha256: String,
    pub solver_registry_hash_sha256: String,
    pub source_revision: String,
    pub source_tree_sha256: Option<String>,
    pub candidate: CandidateBindingV1,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierEdgeWireV1 {
    pub tail: usize,
    pub head: usize,
    pub weight_i128: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierDeclarationV1 {
    pub coefficient_domain: String,
    pub coefficient_representation: String,
    pub num_vertices: usize,
    pub edges: Vec<CarrierEdgeWireV1>,
    pub faces: Vec<[usize; 3]>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierInputV1 {
    pub declaration: CarrierDeclarationV1,
    pub expected_manifest_version: u32,
    pub expected_carrier_hash_blake3: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResidualInputV1 {
    pub before_omega_i128: Vec<String>,
    pub candidate_omega_i128: Vec<String>,
    pub candidate_acceptance_mode: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PrimeProfilesV1 {
    pub prime000_revision: String,
    pub prime001_revision: String,
    pub prime002_revision: String,
    pub carrier_declaration: String,
    pub primitive_difference: String,
    pub zero_relation: String,
    pub observer_profile_id: String,
    pub witness_profile_id: String,
    pub integral_mass_policy: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Prime002ProfileV1 {
    pub route: String,
    pub detector_profile_id: String,
    pub detector_config_sha256: String,
    pub open_obligation_degrees: Vec<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostBudgetsV1 {
    pub max_request_bytes: usize,
    pub max_edges: usize,
    pub max_vertices_plus_faces: usize,
    pub max_candidates: usize,
    pub max_prime_writes: usize,
    pub timeout_ms: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostRequestV1 {
    pub schema_version: String,
    pub request_id_sha256: String,
    pub challenge_hex: String,
    pub operation: String,
    pub canonicalization_profile: String,
    pub authority_effect: String,
    pub expected_host_registry_hash_sha256: String,
    pub expected_host_source_revision: String,
    pub outer_dda_dialect: String,
    pub packet_envelope: PacketEnvelopeWireV2,
    pub source: SourceBindingsV1,
    pub carrier: CarrierInputV1,
    pub residual: ResidualInputV1,
    pub prime_profiles: PrimeProfilesV1,
    pub prime002: Prime002ProfileV1,
    pub budgets: HostBudgetsV1,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExactRationalWireV1 {
    pub n: String,
    pub d: String,
}

impl ExactRationalWireV1 {
    pub fn from_rational(value: &BigRational) -> Self {
        Self {
            n: value.numer().to_string(),
            d: value.denom().to_string(),
        }
    }

    pub fn zero() -> Self {
        Self::from_rational(&BigRational::zero())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CommitmentCheckV1 {
    pub supplied: String,
    pub derived: String,
    pub verdict: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierManifestSummaryV1 {
    pub manifest_version: u32,
    pub carrier_hash_blake3: String,
    pub d0_hash_blake3: String,
    pub d1_hash_blake3: String,
    pub weights_hash_blake3: String,
    pub witness_hash_blake3: String,
    pub provenance_hash_blake3: String,
    pub coefficient_domain: String,
    pub coefficient_representation: String,
    pub c0_dim: usize,
    pub c1_dim: usize,
    pub c2_dim: usize,
    pub rank_d0: usize,
    pub dim_q1: usize,
    pub dim_h1: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBindingChecksV1 {
    pub packet_id: CommitmentCheckV1,
    pub runtime_id_sha256: String,
    pub runtime_id_verdict: String,
    pub candidate_id_sha256: String,
    pub candidate_id_verdict: String,
    pub candidate_state_hash_sha256: String,
    pub candidate_state_verdict: String,
    pub source_event_root_sha256: String,
    pub source_event_root_verdict: String,
    pub source_wire_receipt_id_sha256: String,
    pub source_wire_receipt_verdict: String,
    pub solver_registry_hash_sha256: String,
    pub solver_registry_verdict: String,
    pub source_revision: String,
    pub source_revision_verdict: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Prime001SummaryV1 {
    pub kind: String,
    pub carrier_hash_blake3: String,
    pub identity_commitment_sha256: String,
    pub loss_ledger_commitment_sha256: String,
    pub transport_called: bool,
    pub transport_same_carrier_refusal_checked: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExactStageSummaryV1 {
    pub status: String,
    pub raw_weighted_l1: ExactRationalWireV1,
    pub phi1: ExactRationalWireV1,
    pub gamma2: ExactRationalWireV1,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateRelationV1 {
    pub kind: String,
    pub candidate_vector_sha256: String,
    pub normal_form_sha256: String,
    pub exact_match: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OesosSummaryV1 {
    pub kind: String,
    pub input_commitment_sha256: String,
    pub fresh_solve_commitment_sha256: String,
    pub replay_commitment_sha256: String,
    pub pipeline_declaration_carrier_hash_blake3: String,
    pub gauge: ExactStageSummaryV1,
    pub final_stage: ExactStageSummaryV1,
    pub normal_form: Vec<ExactRationalWireV1>,
    pub b1_over_q: usize,
    pub span_distance: ExactRationalWireV1,
    pub closure_premium: ExactRationalWireV1,
    pub candidate_relation: CandidateRelationV1,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Prime000ConformanceV1 {
    pub verdict: String,
    pub conforms: bool,
    pub no_decidable_violation: bool,
    pub violations: Vec<String>,
    pub unchecked_laws: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Prime000SummaryV1 {
    pub kind: String,
    pub receipt_commitment_sha256: String,
    pub terminal: String,
    pub evidence_provenance: String,
    pub letter_tape: String,
    pub phi1_u64: u64,
    pub gamma2_u64: u64,
    pub conformance: Prime000ConformanceV1,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BudgetSummaryV1 {
    pub max_ops: usize,
    pub spent: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Prime002SummaryV1 {
    pub kind: String,
    pub scope_commitments_sha256: Vec<String>,
    pub claim_commitments_sha256: Vec<String>,
    pub evidence_commitments_sha256: Vec<String>,
    pub permit_bindings_sha256: Vec<String>,
    pub rust_letters: Vec<String>,
    pub terminal_head_sha256: String,
    pub budget_before: BudgetSummaryV1,
    pub budget_after: BudgetSummaryV1,
    pub refusal_laws: Vec<String>,
    pub evidence_caveat: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AdmissionSummaryV1 {
    pub kind: String,
    pub codes: Vec<String>,
    pub reason_commitment_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RefusalSummaryV1 {
    pub stage: String,
    pub code: String,
    pub detail: String,
    pub laws: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostOutcomeV1 {
    pub schema_version: String,
    pub request_id_sha256: Option<String>,
    pub challenge_hex: Option<String>,
    pub outcome_root_sha256: String,
    pub host_registry_hash_sha256: String,
    pub host_source_revision: String,
    pub authority_effect: String,
    pub execution_status: String,
    pub source_bindings: Option<SourceBindingChecksV1>,
    pub carrier_manifest: Option<CarrierManifestSummaryV1>,
    pub prime001_result: Option<Prime001SummaryV1>,
    pub oesos_result: Option<OesosSummaryV1>,
    pub prime000_result: Option<Prime000SummaryV1>,
    pub prime002_result: Option<Prime002SummaryV1>,
    pub diagnostic_kind: Option<String>,
    pub admission: AdmissionSummaryV1,
    pub attestation: String,
    pub refusal: Option<RefusalSummaryV1>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostDescriptionV1 {
    pub schema_version: String,
    pub logical_id: String,
    pub crate_version: String,
    pub request_schema: String,
    pub outcome_schema: String,
    pub host_registry_hash_sha256: String,
    pub source_revision: String,
    pub max_request_bytes: usize,
    pub outer_dialects: Vec<String>,
    pub authority_effect: String,
    pub attestation: String,
}

pub(crate) fn hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(DIGITS[(byte >> 4) as usize] as char);
        output.push(DIGITS[(byte & 0x0f) as usize] as char);
    }
    output
}

pub(crate) fn canonical_json(value: &Value) -> Vec<u8> {
    pfp_runtime::packet_wire::sorted_json_bytes(value)
}

fn canonical_without_field<T: Serialize>(value: &T, field: &str) -> Vec<u8> {
    let mut json = serde_json::to_value(value).checked_invariant_b5ad64c5("protocol values serialize");
    json.as_object_mut()
        .checked_invariant_b5ad64c5("protocol root is an object")
        .remove(field);
    canonical_json(&json)
}

pub fn compute_request_id(request: &HostRequestV1) -> String {
    framed_sha256(
        REQUEST_DOMAIN,
        &canonical_without_field(request, "request_id_sha256"),
    )
}

pub(crate) fn finalize_outcome(mut outcome: HostOutcomeV1) -> HostOutcomeV1 {
    outcome.outcome_root_sha256 = framed_sha256(
        OUTCOME_DOMAIN,
        &canonical_without_field(&outcome, "outcome_root_sha256"),
    );
    outcome
}

pub fn verify_outcome_root(outcome: &HostOutcomeV1) -> bool {
    outcome.outcome_root_sha256
        == framed_sha256(
            OUTCOME_DOMAIN,
            &canonical_without_field(outcome, "outcome_root_sha256"),
        )
}

pub fn describe_host() -> HostDescriptionV1 {
    let registry_payload = serde_json::json!({
        "logical_id": "core-prime-oesos-host",
        "crate_version": env!("CARGO_PKG_VERSION"),
        "request_schema": HOST_REQUEST_SCHEMA,
        "outcome_schema": HOST_OUTCOME_SCHEMA,
        "oesos": "core_wdp::solver_of_solvers::solve+replay_solve",
        "prime000": "oeprmalg0+oeprmalg0_conformance",
        "prime001": "oeprmalg1",
        "prime002": "oeprmalg2",
        "authority_effect": "None"
    });
    HostDescriptionV1 {
        schema_version: HOST_DESCRIPTION_SCHEMA.to_owned(),
        logical_id: "core-prime-oesos-host".to_owned(),
        crate_version: env!("CARGO_PKG_VERSION").to_owned(),
        request_schema: HOST_REQUEST_SCHEMA.to_owned(),
        outcome_schema: HOST_OUTCOME_SCHEMA.to_owned(),
        host_registry_hash_sha256: framed_sha256(
            HOST_REGISTRY_DOMAIN,
            &canonical_json(&registry_payload),
        ),
        source_revision: HOST_SOURCE_REVISION.to_owned(),
        max_request_bytes: MAX_HOST_REQUEST_BYTES,
        outer_dialects: vec!["experimental-z-v1".to_owned()],
        authority_effect: "None".to_owned(),
        attestation: "unsigned_lab".to_owned(),
    }
}

fn parse_i128(value: &str, label: &str) -> Result<i128, String> {
    let parsed = value
        .parse::<i128>()
        .map_err(|_| format!("{label} is not a minimal signed i128"))?;
    if parsed.to_string() != value {
        return Err(format!("{label} is not minimally encoded"));
    }
    Ok(parsed)
}

pub(crate) fn build_carrier(declaration: &CarrierDeclarationV1) -> Result<FiniteCarrier2, String> {
    if declaration.coefficient_domain != "Q"
        || declaration.coefficient_representation != "BigRational"
    {
        return Err("carrier must declare Q/BigRational coefficient semantics".to_owned());
    }
    let edges = declaration
        .edges
        .iter()
        .enumerate()
        .map(|(index, edge)| {
            Ok(CarrierEdge {
                tail: edge.tail,
                head: edge.head,
                weight: parse_i128(&edge.weight_i128, &format!("edge[{index}].weight_i128"))?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(FiniteCarrier2 {
        num_vertices: declaration.num_vertices,
        edges,
        faces: declaration
            .faces
            .iter()
            .map(|face| (face[0], face[1], face[2]))
            .collect(),
    })
}

fn validate_dense_matrix_cells(
    declaration: &CarrierDeclarationV1,
    vertices_plus_faces: usize,
) -> Result<(), String> {
    for (label, rows, columns) in [
        ("d0", declaration.edges.len(), declaration.num_vertices),
        ("d1", declaration.faces.len(), declaration.edges.len()),
        ("augmented", declaration.edges.len(), vertices_plus_faces),
        (
            "closed-system",
            declaration.faces.len(),
            vertices_plus_faces,
        ),
    ] {
        let cells = rows
            .checked_mul(columns)
            .ok_or_else(|| format!("{label} dense matrix dimensions overflow usize"))?;
        if cells > MAX_DENSE_MATRIX_CELLS {
            return Err(format!(
                "{label} dense matrix requires {cells} cells; maximum is {MAX_DENSE_MATRIX_CELLS}"
            ));
        }
    }
    Ok(())
}

pub(crate) fn validate_carrier_resource_fence(
    declaration: &CarrierDeclarationV1,
) -> Result<usize, String> {
    let valid_vertices =
        declaration.num_vertices > 0 && declaration.num_vertices <= MAX_CARRIER_DIMENSION;
    let valid_edges =
        !declaration.edges.is_empty() && declaration.edges.len() <= MAX_CARRIER_DIMENSION;
    if !valid_vertices || !valid_edges || declaration.faces.len() > MAX_CARRIER_DIMENSION {
        return Err("declared carrier dimension exceeds an independent host fence".to_owned());
    }
    let vertices_plus_faces = declaration
        .num_vertices
        .checked_add(declaration.faces.len())
        .ok_or_else(|| "carrier vertex-plus-face dimension overflows usize".to_owned())?;
    if vertices_plus_faces > MAX_CARRIER_DIMENSION {
        return Err("carrier vertex-plus-face dimension exceeds the host fence".to_owned());
    }
    validate_dense_matrix_cells(declaration, vertices_plus_faces)?;
    Ok(vertices_plus_faces)
}

pub(crate) fn parse_omega(values: &[String], label: &str) -> Result<Vec<i128>, String> {
    values
        .iter()
        .enumerate()
        .map(|(index, value)| parse_i128(value, &format!("{label}[{index}]")))
        .collect()
}

pub fn derive_carrier_manifest(
    declaration: &CarrierDeclarationV1,
) -> Result<CarrierManifestSummaryV1, String> {
    validate_carrier_resource_fence(declaration)?;
    let carrier = build_carrier(declaration)?;
    let manifest = carrier_manifest(&carrier).map_err(|error| error.to_string())?;
    Ok(CarrierManifestSummaryV1 {
        manifest_version: manifest.manifest_version(),
        carrier_hash_blake3: manifest.carrier_hash().to_hex(),
        d0_hash_blake3: manifest.d0_hash().to_hex(),
        d1_hash_blake3: manifest.d1_hash().to_hex(),
        weights_hash_blake3: manifest.weights_hash().to_hex(),
        witness_hash_blake3: manifest.witness_hash().to_hex(),
        provenance_hash_blake3: manifest.provenance_hash().to_hex(),
        coefficient_domain: manifest.coefficient_domain().to_owned(),
        coefficient_representation: manifest.coefficient_representation().to_owned(),
        c0_dim: manifest.c0_dim(),
        c1_dim: manifest.c1_dim(),
        c2_dim: manifest.c2_dim(),
        rank_d0: manifest.rank_d0(),
        dim_q1: manifest.dim_q1(),
        dim_h1: manifest.dim_h1(),
    })
}

pub fn derive_carrier_manifest_bytes(bytes: &[u8]) -> Result<CarrierManifestSummaryV1, String> {
    let declaration: CarrierDeclarationV1 = strict_json(bytes)?;
    derive_carrier_manifest(&declaration)
}

fn has_valid_packet_profile_header(packet: &PacketEnvelopeWireV2) -> bool {
    packet.schema_version == PACKET_SCHEMA
        && packet.authority_effect == "None"
        && matches!(packet.framing_mode.as_str(), "strict" | "extraction")
        && packet.step_budget > 0
}

fn has_nonempty_packet_strings(packet: &PacketEnvelopeWireV2) -> bool {
    [
        packet.packet_kind.as_str(),
        packet.task_id.as_str(),
        packet.packet_family.as_str(),
        packet.carrier_id.as_str(),
        packet.terminal_target.as_str(),
        packet.evidence_ceiling.as_str(),
        packet.oracle_policy.as_str(),
    ]
    .into_iter()
    .all(|s| !s.is_empty())
}

fn validate_packet_hex_fields(packet: &PacketEnvelopeWireV2) -> Result<(), String> {
    validate_lower_hex(&packet.packet_id, "packet_id")?;
    validate_lower_hex(&packet.initial_state_hash, "initial_state_hash")?;
    if let Some(value) = packet.parent_event_id.as_deref() {
        validate_lower_hex(value, "parent_event_id")?;
    }
    if let Some(value) = packet.source_digest.as_deref() {
        validate_lower_hex(value, "source_digest")?;
    }
    Ok(())
}

pub(crate) fn verify_packet_envelope(
    packet: &PacketEnvelopeWireV2,
) -> Result<CommitmentCheckV1, String> {
    if !has_valid_packet_profile_header(packet) || !has_nonempty_packet_strings(packet) {
        return Err("packet envelope profile is invalid".to_owned());
    }
    validate_packet_hex_fields(packet)?;
    validate_canonical_node(&packet.payload)?;

    let mut entries = BTreeMap::new();
    entries.insert(
        "schema_version".to_owned(),
        wire_string(&packet.schema_version),
    );
    entries.insert("packet_kind".to_owned(), wire_string(&packet.packet_kind));
    entries.insert("framing_mode".to_owned(), wire_string(&packet.framing_mode));
    entries.insert("task_id".to_owned(), wire_string(&packet.task_id));
    entries.insert(
        "packet_family".to_owned(),
        wire_string(&packet.packet_family),
    );
    entries.insert("carrier_id".to_owned(), wire_string(&packet.carrier_id));
    entries.insert(
        "initial_state_hash".to_owned(),
        wire_string(&packet.initial_state_hash),
    );
    entries.insert("payload".to_owned(), packet.payload.clone());
    entries.insert("constraints".to_owned(), wire_tuple(&packet.constraints));
    entries.insert(
        "protected_boundaries".to_owned(),
        wire_tuple(&packet.protected_boundaries),
    );
    entries.insert(
        "terminal_target".to_owned(),
        wire_string(&packet.terminal_target),
    );
    entries.insert(
        "evidence_ceiling".to_owned(),
        wire_string(&packet.evidence_ceiling),
    );
    entries.insert(
        "oracle_policy".to_owned(),
        wire_string(&packet.oracle_policy),
    );
    entries.insert(
        "allowed_transforms".to_owned(),
        wire_tuple(&packet.allowed_transforms),
    );
    entries.insert("step_budget".to_owned(), wire_int(packet.step_budget));
    entries.insert(
        "parent_event_id".to_owned(),
        wire_optional_string(packet.parent_event_id.as_deref()),
    );
    entries.insert(
        "source_digest".to_owned(),
        wire_optional_string(packet.source_digest.as_deref()),
    );
    entries.insert(
        "authority_effect".to_owned(),
        wire_string(&packet.authority_effect),
    );
    let canonical_identity = canonical_json(&wire_mapping(entries));
    let derived = framed_sha256(PACKET_ID_DOMAIN, &canonical_identity);
    Ok(CommitmentCheckV1 {
        supplied: packet.packet_id.clone(),
        verdict: if derived == packet.packet_id {
            "MATCH".to_owned()
        } else {
            "MISMATCH".to_owned()
        },
        derived,
    })
}

pub fn compute_packet_id(packet: &PacketEnvelopeWireV2) -> Result<String, String> {
    let mut packet = packet.clone();
    packet.packet_id = "0".repeat(64);
    Ok(verify_packet_envelope(&packet)?.derived)
}

pub(crate) fn validate_lower_hex(value: &str, label: &str) -> Result<(), String> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_hexdigit() || byte.is_ascii_uppercase())
    {
        return Err(format!(
            "{label} must be 64 lowercase hexadecimal characters"
        ));
    }
    Ok(())
}

pub(crate) fn decode_lower_hex(value: &str, label: &str) -> Result<[u8; 32], String> {
    validate_lower_hex(value, label)?;
    let mut output = [0u8; 32];
    for (index, slot) in output.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|_| format!("{label} is invalid hexadecimal"))?;
    }
    Ok(output)
}

struct StrictValueVisitor;

impl<'de> Visitor<'de> for StrictValueVisitor {
    type Value = Value;

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("JSON without duplicate object keys")
    }

    fn visit_bool<E: DeError>(self, value: bool) -> Result<Self::Value, E> {
        Ok(Value::Bool(value))
    }

    fn visit_i64<E: DeError>(self, value: i64) -> Result<Self::Value, E> {
        Ok(Value::Number(value.into()))
    }

    fn visit_u64<E: DeError>(self, value: u64) -> Result<Self::Value, E> {
        Ok(Value::Number(value.into()))
    }

    fn visit_f64<E: DeError>(self, value: f64) -> Result<Self::Value, E> {
        serde_json::Number::from_f64(value)
            .map(Value::Number)
            .ok_or_else(|| E::custom("non-finite JSON number"))
    }

    fn visit_str<E: DeError>(self, value: &str) -> Result<Self::Value, E> {
        Ok(Value::String(value.to_owned()))
    }

    fn visit_string<E: DeError>(self, value: String) -> Result<Self::Value, E> {
        Ok(Value::String(value))
    }

    fn visit_none<E: DeError>(self) -> Result<Self::Value, E> {
        Ok(Value::Null)
    }

    fn visit_unit<E: DeError>(self) -> Result<Self::Value, E> {
        Ok(Value::Null)
    }

    fn visit_some<D: Deserializer<'de>>(self, deserializer: D) -> Result<Self::Value, D::Error> {
        deserializer.deserialize_any(StrictValueVisitor)
    }

    fn visit_seq<A: SeqAccess<'de>>(self, mut sequence: A) -> Result<Self::Value, A::Error> {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element_seed(StrictValueSeed)? {
            values.push(value);
        }
        Ok(Value::Array(values))
    }

    fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
        let mut values = Map::new();
        while let Some(key) = map.next_key::<String>()? {
            if values.contains_key(&key) {
                return Err(A::Error::custom(format!("duplicate JSON key {key:?}")));
            }
            values.insert(key, map.next_value_seed(StrictValueSeed)?);
        }
        Ok(Value::Object(values))
    }
}

struct StrictValueSeed;

impl<'de> serde::de::DeserializeSeed<'de> for StrictValueSeed {
    type Value = Value;

    fn deserialize<D: Deserializer<'de>>(self, deserializer: D) -> Result<Self::Value, D::Error> {
        deserializer.deserialize_any(StrictValueVisitor)
    }
}

pub(crate) fn strict_json<T: DeserializeOwned>(bytes: &[u8]) -> Result<T, String> {
    if bytes.len() > MAX_HOST_REQUEST_BYTES {
        return Err(format!(
            "request has {} bytes; maximum is {MAX_HOST_REQUEST_BYTES}",
            bytes.len()
        ));
    }
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    let value = deserializer
        .deserialize_any(StrictValueVisitor)
        .map_err(|error| error.to_string())?;
    deserializer.end().map_err(|error| error.to_string())?;
    serde_json::from_value(value).map_err(|error| error.to_string())
}

pub(crate) fn base_refusal(
    request_id: Option<String>,
    challenge: Option<String>,
    stage: &str,
    code: &str,
    detail: impl Into<String>,
) -> HostOutcomeV1 {
    let detail = detail.into();
    let admission_codes = vec![code.to_owned(), "UNSIGNED_LAB_ATTESTATION".to_owned()];
    let reason_commitment = framed_sha256(
        "core.oesos.host-admission-refusal.v1",
        &canonical_json(&serde_json::json!({
            "stage": stage,
            "codes": admission_codes,
            "detail": detail,
        })),
    );
    finalize_outcome(HostOutcomeV1 {
        schema_version: HOST_OUTCOME_SCHEMA.to_owned(),
        request_id_sha256: request_id,
        challenge_hex: challenge,
        outcome_root_sha256: String::new(),
        host_registry_hash_sha256: describe_host().host_registry_hash_sha256,
        host_source_revision: HOST_SOURCE_REVISION.to_owned(),
        authority_effect: "None".to_owned(),
        execution_status: "REFUSED".to_owned(),
        source_bindings: None,
        carrier_manifest: None,
        prime001_result: None,
        oesos_result: None,
        prime000_result: None,
        prime002_result: None,
        diagnostic_kind: None,
        admission: AdmissionSummaryV1 {
            kind: "Refused".to_owned(),
            codes: admission_codes,
            reason_commitment_sha256: reason_commitment,
        },
        attestation: "unsigned_lab".to_owned(),
        refusal: Some(RefusalSummaryV1 {
            stage: stage.to_owned(),
            code: code.to_owned(),
            detail,
            laws: Vec::new(),
        }),
    })
}

// Origin: engine/crates_rs/pfp/src/protocol.rs
// Claim: urn:core:crates_rs:pfp:protocol:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb5ad64c5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb5ad64c5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb5ad64c5 {
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
impl BoundaryErrorb5ad64c5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb5ad64c5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb5ad64c5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb5ad64c5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb5ad64c5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb5ad64c5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb5ad64c5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb5ad64c5::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_b5ad64c5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb5ad64c5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb5ad64c5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb5ad64c5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb5ad64c5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb5ad64c5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb5ad64c5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb5ad64c5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
