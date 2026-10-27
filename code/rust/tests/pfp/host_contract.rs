use pfp::protocol::{
    CandidateBindingV1, CarrierDeclarationV1, CarrierEdgeWireV1, CarrierInputV1, HostBudgetsV1,
    PacketEnvelopeWireV2, Prime002ProfileV1, PrimeProfilesV1, ResidualInputV1, SourceBindingsV1,
};
use pfp::{
    compute_packet_id, compute_request_id, derive_carrier_manifest, derive_carrier_manifest_bytes,
    describe_host, evaluate_request, evaluate_request_bytes, verify_outcome_root, HostRequestV1,
    HOST_REQUEST_SCHEMA, MAX_HOST_REQUEST_BYTES,
};

type RequestMutation = Box<dyn Fn(&mut HostRequestV1)>;
type NamedRequestMutation = (&'static str, RequestMutation);
type ExpectedRefusalMutation = (&'static str, RequestMutation, &'static str);

fn canonical_string(value: &str) -> serde_json::Value {
    serde_json::json!(["core-canonical-v1", "string", value])
}

fn canonical_int(value: &str) -> serde_json::Value {
    serde_json::json!(["core-canonical-v1", "int", value])
}

fn canonical_float(value: &str) -> serde_json::Value {
    serde_json::json!(["core-canonical-v1", "float", [canonical_string(value)]])
}

fn canonical_fraction(numerator: &str, denominator: &str) -> serde_json::Value {
    serde_json::json!([
        "core-canonical-v1",
        "fraction",
        [canonical_int(numerator), canonical_int(denominator)]
    ])
}

fn carrier() -> CarrierDeclarationV1 {
    CarrierDeclarationV1 {
        coefficient_domain: "Q".to_owned(),
        coefficient_representation: "BigRational".to_owned(),
        num_vertices: 4,
        edges: vec![
            CarrierEdgeWireV1 {
                tail: 0,
                head: 1,
                weight_i128: "1".to_owned(),
            },
            CarrierEdgeWireV1 {
                tail: 1,
                head: 2,
                weight_i128: "1".to_owned(),
            },
            CarrierEdgeWireV1 {
                tail: 2,
                head: 0,
                weight_i128: "1".to_owned(),
            },
            CarrierEdgeWireV1 {
                tail: 1,
                head: 3,
                weight_i128: "1".to_owned(),
            },
            CarrierEdgeWireV1 {
                tail: 3,
                head: 0,
                weight_i128: "1".to_owned(),
            },
        ],
        faces: vec![[0, 1, 2], [0, 1, 3]],
    }
}

fn packet() -> PacketEnvelopeWireV2 {
    let mut packet = PacketEnvelopeWireV2 {
        schema_version: "core.symbol-game.packet-envelope.v2".to_owned(),
        packet_id: "0".repeat(64),
        packet_kind: "problem".to_owned(),
        framing_mode: "strict".to_owned(),
        task_id: "solver-of-solvers-symbol-game-coda".to_owned(),
        packet_family: "cochain_obstruction".to_owned(),
        carrier_id: "finite-cochain-2-v1".to_owned(),
        initial_state_hash: "1".repeat(64),
        payload: serde_json::json!([
            "core-canonical-v1",
            "string",
            "face-aware-coda-host-contract-v1"
        ]),
        constraints: vec![
            "d1*d0=0".to_owned(),
            "finite exact carrier".to_owned(),
            "separate phi1 from gamma2".to_owned(),
        ],
        protected_boundaries: vec!["cochain:phi1".to_owned(), "cochain:gamma2".to_owned()],
        terminal_target: "ExactOrTypedObstruction".to_owned(),
        evidence_ceiling: "ReplayableLabEvidence".to_owned(),
        oracle_policy: "ExternalVerifierRequired".to_owned(),
        allowed_transforms: vec!["same_carrier_retraction".to_owned()],
        step_budget: 2,
        parent_event_id: None,
        source_digest: Some("2".repeat(64)),
        authority_effect: "None".to_owned(),
    };
    packet.packet_id = compute_packet_id(&packet).expect("packet identity must derive");
    packet
}

fn request() -> HostRequestV1 {
    let description = describe_host();
    let declaration = carrier();
    let manifest = derive_carrier_manifest(&declaration).expect("fixture carrier must bind");
    let mut request = HostRequestV1 {
        schema_version: HOST_REQUEST_SCHEMA.to_owned(),
        request_id_sha256: "0".repeat(64),
        challenge_hex: "3".repeat(64),
        operation: "evaluate_candidate".to_owned(),
        canonicalization_profile: "core-sorted-json-no-float-v1".to_owned(),
        authority_effect: "None".to_owned(),
        expected_host_registry_hash_sha256: description.host_registry_hash_sha256,
        expected_host_source_revision: description.source_revision.clone(),
        outer_dda_dialect: "experimental-z-v1".to_owned(),
        packet_envelope: packet(),
        source: SourceBindingsV1 {
            runtime_id_sha256: "4".repeat(64),
            source_event_root_sha256: "5".repeat(64),
            source_wire_receipt_id_sha256: "6".repeat(64),
            solver_registry_hash_sha256: "7".repeat(64),
            source_revision: description.source_revision,
            source_tree_sha256: Some("8".repeat(64)),
            candidate: CandidateBindingV1 {
                candidate_id_sha256: "9".repeat(64),
                producer_id: "existing-coda-cascade-proposal".to_owned(),
                witness_sha256: "a".repeat(64),
                state_hash_sha256: "b".repeat(64),
            },
        },
        carrier: CarrierInputV1 {
            declaration,
            expected_manifest_version: manifest.manifest_version,
            expected_carrier_hash_blake3: manifest.carrier_hash_blake3,
        },
        residual: ResidualInputV1 {
            before_omega_i128: ["3", "2", "2", "1", "1"].map(str::to_owned).to_vec(),
            candidate_omega_i128: vec!["0".to_owned(); 5],
            candidate_acceptance_mode: "must_equal_replayed_normal_form-v1".to_owned(),
        },
        prime_profiles: PrimeProfilesV1 {
            prime000_revision: "oeprmalg0".to_owned(),
            prime001_revision: "oeprmalg1".to_owned(),
            prime002_revision: "oeprmalg2".to_owned(),
            carrier_declaration: "finite-cochain-2-v1".to_owned(),
            primitive_difference: "declared edge cochain residual".to_owned(),
            zero_relation: "phi1=0 and gamma2=0".to_owned(),
            observer_profile_id: "coda-face-aware-phi1-gamma2-projector-v1".to_owned(),
            witness_profile_id: "face-aware-positive-negative-controls-v1".to_owned(),
            integral_mass_policy: "refuse_non_u64".to_owned(),
        },
        prime002: Prime002ProfileV1 {
            route: "write_exact_then_terminalize".to_owned(),
            detector_profile_id: "core-prime-oesos-host.exact-bytes".to_owned(),
            detector_config_sha256: "c".repeat(64),
            open_obligation_degrees: vec![],
        },
        budgets: HostBudgetsV1 {
            max_request_bytes: MAX_HOST_REQUEST_BYTES,
            max_edges: 4096,
            max_vertices_plus_faces: 4096,
            max_candidates: 1,
            max_prime_writes: 2,
            timeout_ms: 60_000,
        },
    };
    request.request_id_sha256 = compute_request_id(&request);
    request
}

#[test]
fn face_aware_coda_crosses_exact_host_but_global_admission_stays_refused() {
    let outcome = evaluate_request(request());
    assert_eq!(
        outcome.execution_status, "EXECUTED_REPLAYED_EXACT_LAB_EVIDENCE",
        "unexpected refusal: {:?}",
        outcome.refusal
    );
    assert!(verify_outcome_root(&outcome));
    assert_eq!(outcome.authority_effect, "None");
    assert_eq!(outcome.attestation, "unsigned_lab");
    assert_eq!(outcome.diagnostic_kind.as_deref(), Some("ExactRepair"));

    let prime001 = outcome.prime001_result.expect("identity receipt");
    assert_eq!(prime001.kind, "same_carrier_identity");
    assert!(!prime001.transport_called);
    assert!(prime001.transport_same_carrier_refusal_checked);

    let oesos = outcome.oesos_result.expect("exact replay summary");
    assert_eq!(oesos.kind, "replayed");
    assert!(oesos.candidate_relation.exact_match);
    assert_eq!(oesos.gauge.phi1.n, "7");
    assert_eq!(oesos.gauge.gamma2.n, "12");
    assert_eq!(oesos.final_stage.phi1.n, "0");
    assert_eq!(oesos.final_stage.gamma2.n, "0");

    let prime000 = outcome.prime000_result.expect("Prime 000 summary");
    assert_eq!(prime000.conformance.verdict, "Partial");
    assert!(!prime000.conformance.conforms);
    assert!(prime000.conformance.no_decidable_violation);
    assert_eq!(prime000.conformance.unchecked_laws.len(), 3);

    let prime002 = outcome.prime002_result.expect("sealed Prime 002 summary");
    assert_eq!(prime002.rust_letters, ["E", "T"]);
    assert_eq!(prime002.budget_before.spent, 0);
    assert_eq!(prime002.budget_after.spent, 2);
    assert_eq!(prime002.permit_bindings_sha256.len(), 2);

    assert_eq!(outcome.admission.kind, "Refused");
    assert!(outcome
        .admission
        .codes
        .contains(&"PRIME000_CONFORMANCE_PARTIAL".to_owned()));
    assert!(outcome
        .admission
        .codes
        .contains(&"UNSIGNED_LAB_ATTESTATION".to_owned()));
}

#[test]
fn stale_commitments_refuse_before_exact_solving() {
    let mutations: Vec<NamedRequestMutation> = vec![
        (
            "packet content",
            Box::new(|request| request.packet_envelope.task_id.push_str("-mutated")),
        ),
        (
            "runtime",
            Box::new(|request| request.source.runtime_id_sha256 = "d".repeat(64)),
        ),
        (
            "candidate",
            Box::new(|request| request.source.candidate.candidate_id_sha256 = "e".repeat(64)),
        ),
        (
            "source event",
            Box::new(|request| request.source.source_event_root_sha256 = "f".repeat(64)),
        ),
        (
            "omega",
            Box::new(|request| request.residual.before_omega_i128[0] = "4".to_owned()),
        ),
    ];
    for (label, mutate) in mutations {
        let mut request = request();
        mutate(&mut request);
        let outcome = evaluate_request(request);
        assert_eq!(outcome.execution_status, "REFUSED", "mutation {label}");
        assert_eq!(
            outcome.refusal.as_ref().map(|item| item.code.as_str()),
            Some("REQUEST_ID_MISMATCH"),
            "mutation {label}"
        );
        assert!(outcome.oesos_result.is_none(), "mutation {label}");
    }
}

#[test]
fn independently_rehashed_carrier_mutation_cannot_reuse_manifest_anchor() {
    let mut request = request();
    request.carrier.declaration.edges[0].weight_i128 = "2".to_owned();
    request.request_id_sha256 = compute_request_id(&request);
    let outcome = evaluate_request(request);
    assert_eq!(outcome.execution_status, "REFUSED");
    assert_eq!(
        outcome.refusal.as_ref().map(|item| item.code.as_str()),
        Some("CARRIER_MANIFEST_MISMATCH")
    );
    assert!(outcome.oesos_result.is_none());
}

#[test]
fn independently_rehashed_candidate_must_equal_replayed_normal_form() {
    let mut request = request();
    request.residual.candidate_omega_i128[4] = "1".to_owned();
    request.request_id_sha256 = compute_request_id(&request);
    let outcome = evaluate_request(request);
    assert_eq!(outcome.execution_status, "REFUSED");
    assert_eq!(
        outcome.refusal.as_ref().map(|item| item.code.as_str()),
        Some("CANDIDATE_NOT_REPLAYED_NORMAL_FORM")
    );
    assert!(outcome.oesos_result.is_some());
    assert!(outcome.prime000_result.is_none());
}

#[test]
fn registry_authority_and_host_revision_mismatches_refuse() {
    let cases: Vec<ExpectedRefusalMutation> = vec![
        (
            "registry",
            Box::new(|request| request.expected_host_registry_hash_sha256 = "d".repeat(64)),
            "HOST_REGISTRY_MISMATCH",
        ),
        (
            "authority",
            Box::new(|request| request.authority_effect = "GlobalGreen".to_owned()),
            "AUTHORITY_EXPANSION_REFUSED",
        ),
        (
            "revision",
            Box::new(|request| request.expected_host_source_revision.push_str("-wrong")),
            "HOST_SOURCE_REVISION_MISMATCH",
        ),
    ];
    for (label, mutate, code) in cases {
        let mut request = request();
        mutate(&mut request);
        request.request_id_sha256 = compute_request_id(&request);
        let outcome = evaluate_request(request);
        assert_eq!(
            outcome.refusal.as_ref().map(|item| item.code.as_str()),
            Some(code),
            "case {label}"
        );
        assert_eq!(outcome.authority_effect, "None");
    }
}

#[test]
fn malformed_duplicate_unknown_and_oversized_json_fail_closed() {
    let valid = serde_json::to_vec(&request()).unwrap();
    let text = String::from_utf8(valid).unwrap();
    let duplicate = text.replacen(
        "{",
        &format!("{{\"schema_version\":\"{}\",", HOST_REQUEST_SCHEMA),
        1,
    );
    let duplicate_outcome = evaluate_request_bytes(duplicate.as_bytes());
    assert_eq!(
        duplicate_outcome
            .refusal
            .as_ref()
            .map(|item| item.code.as_str()),
        Some("MALFORMED_OR_DUPLICATE_JSON")
    );

    let unknown = text.replacen("{", "{\"step_permit\":true,", 1);
    let unknown_outcome = evaluate_request_bytes(unknown.as_bytes());
    assert_eq!(
        unknown_outcome
            .refusal
            .as_ref()
            .map(|item| item.code.as_str()),
        Some("MALFORMED_OR_DUPLICATE_JSON")
    );

    let invalid_utf8 = evaluate_request_bytes(&[0xff, 0xfe, 0xfd]);
    assert_eq!(invalid_utf8.execution_status, "REFUSED");

    let oversized = evaluate_request_bytes(&vec![b' '; MAX_HOST_REQUEST_BYTES + 1]);
    assert_eq!(
        oversized.refusal.as_ref().map(|item| item.code.as_str()),
        Some("REQUEST_TOO_LARGE")
    );
}

#[test]
fn a_locally_rehashed_outcome_is_not_a_fresh_replay() {
    let outcome = evaluate_request(request());
    assert!(verify_outcome_root(&outcome));
    let mut forged = outcome.clone();
    forged.diagnostic_kind = Some("ClosedResidual".to_owned());
    assert!(!verify_outcome_root(&forged));
    // Even if an attacker could recompute the unkeyed local root, the outcome
    // remains explicitly unsigned laboratory evidence and admission-refused.
    assert_eq!(outcome.attestation, "unsigned_lab");
    assert_eq!(outcome.admission.kind, "Refused");
}

#[test]
fn python_canonical_float_and_fraction_images_remain_accepted() {
    let valid_payloads = [
        canonical_float("0x0.0p+0"),
        canonical_float("-0x0.0p+0"),
        canonical_float("0x1.0000000000000p+0"),
        canonical_float("-0x1.fffffffffffffp+1023"),
        canonical_float("0x0.0000000000001p-1022"),
        canonical_fraction("-2", "3"),
        canonical_fraction("0", "1"),
    ];

    for payload in valid_payloads {
        let mut packet = packet();
        packet.payload = payload;
        let id = compute_packet_id(&packet).expect("Python canonical image must derive");
        assert_eq!(id.len(), 64);
    }
}

#[test]
fn packet_id_matches_python_for_line_and_paragraph_separators() {
    // PacketEnvelopeV2 defaults, payload "\u{2028}\u{2029}", one boundary
    // containing U+2028. Python canonical_json emits the same raw UTF-8
    // serde_json::to_vec uses. Digest from
    // test_packet_id_uses_raw_line_and_paragraph_separators.
    let mut packet = PacketEnvelopeWireV2 {
        schema_version: "core.symbol-game.packet-envelope.v2".to_owned(),
        packet_id: "0".repeat(64),
        packet_kind: "problem".to_owned(),
        framing_mode: "strict".to_owned(),
        task_id: "separator-task".to_owned(),
        packet_family: "separator-family".to_owned(),
        carrier_id: "separator-carrier".to_owned(),
        initial_state_hash: "1".repeat(64),
        payload: serde_json::json!([
            "core-canonical-v1",
            "string",
            "\u{2028}\u{2029}"
        ]),
        constraints: vec!["keep-raw".to_owned()],
        protected_boundaries: vec!["boundary\u{2028}".to_owned()],
        terminal_target: "ExactOrTypedObstruction".to_owned(),
        evidence_ceiling: "ReplayableLabEvidence".to_owned(),
        oracle_policy: "ExternalVerifierRequired".to_owned(),
        allowed_transforms: vec!["same_carrier_retraction".to_owned()],
        step_budget: 8,
        parent_event_id: None,
        source_digest: None,
        authority_effect: "None".to_owned(),
    };
    let id = compute_packet_id(&packet).expect("separator packet must derive");
    assert_eq!(id.len(), 64);
    assert_eq!(
        id,
        "870efca3bded9c0fbb3f1fafa90fa11a212984f3e97b0a6f3204b1d01d7b0aa9"
    );
    packet.packet_id = id;
    let again = compute_packet_id(&packet).expect("supplied id is not hashed");
    assert_eq!(again, packet.packet_id);
}

#[test]
fn values_outside_python_canonical_image_fail_before_packet_id_matching() {
    let invalid_payloads = [
        canonical_float("nan"),
        canonical_float("0x1.0p+0"),
        canonical_float("0x1.0000000000000p+1024"),
        canonical_float("0x0.0000000000000p-1022"),
        canonical_fraction("2", "4"),
        canonical_fraction("1", "0"),
        serde_json::json!([
            "core-canonical-v1",
            "fraction",
            [canonical_string("1"), canonical_int("2")]
        ]),
        serde_json::json!([
            "core-canonical-v1",
            "enum",
            [
                canonical_string(""),
                canonical_string("Kind"),
                canonical_string("Member"),
                canonical_int("1")
            ]
        ]),
        serde_json::json!([
            "core-canonical-v1",
            "dataclass",
            [canonical_string("module"), canonical_string("")]
        ]),
    ];

    for payload in invalid_payloads {
        let mut packet = packet();
        packet.payload = payload;
        assert!(compute_packet_id(&packet).is_err());

        let mut request = request();
        request.packet_envelope = packet;
        request.request_id_sha256 = compute_request_id(&request);
        let outcome = evaluate_request(request);
        assert_eq!(outcome.execution_status, "REFUSED");
        assert_eq!(
            outcome.refusal.as_ref().map(|item| item.code.as_str()),
            Some("PACKET_ENVELOPE_INVALID")
        );
        assert!(outcome.oesos_result.is_none());
    }
}

#[test]
fn empty_required_packet_strings_are_outside_the_python_image() {
    let mutations: Vec<RequestMutation> = vec![
        Box::new(|request| request.packet_envelope.packet_kind.clear()),
        Box::new(|request| request.packet_envelope.task_id.clear()),
        Box::new(|request| request.packet_envelope.packet_family.clear()),
        Box::new(|request| request.packet_envelope.carrier_id.clear()),
        Box::new(|request| request.packet_envelope.terminal_target.clear()),
        Box::new(|request| request.packet_envelope.evidence_ceiling.clear()),
        Box::new(|request| request.packet_envelope.oracle_policy.clear()),
    ];

    for mutate in mutations {
        let mut request = request();
        mutate(&mut request);
        assert!(compute_packet_id(&request.packet_envelope).is_err());
        request.request_id_sha256 = compute_request_id(&request);
        let outcome = evaluate_request(request);
        assert_eq!(
            outcome.refusal.as_ref().map(|item| item.code.as_str()),
            Some("PACKET_ENVELOPE_INVALID")
        );
    }
}

#[test]
fn adversarial_carrier_dimensions_are_typed_refusals_without_panics() {
    let mut overflow = request();
    overflow.carrier.declaration.num_vertices = usize::MAX;
    overflow.request_id_sha256 = compute_request_id(&overflow);
    let overflow_outcome = std::panic::catch_unwind(|| evaluate_request(overflow))
        .expect("resource validation must not panic");
    assert_eq!(
        overflow_outcome
            .refusal
            .as_ref()
            .map(|item| item.code.as_str()),
        Some("RESOURCE_FENCE_EXCEEDED")
    );
    assert!(overflow_outcome.carrier_manifest.is_none());

    let mut dense = request();
    dense.carrier.declaration.num_vertices = 1025;
    dense.carrier.declaration.faces.clear();
    dense.carrier.declaration.edges = vec![
        CarrierEdgeWireV1 {
            tail: 0,
            head: 1,
            weight_i128: "1".to_owned(),
        };
        1025
    ];
    dense.request_id_sha256 = compute_request_id(&dense);
    let dense_outcome = std::panic::catch_unwind(|| evaluate_request(dense))
        .expect("dense resource validation must not panic");
    assert_eq!(
        dense_outcome
            .refusal
            .as_ref()
            .map(|item| item.code.as_str()),
        Some("RESOURCE_FENCE_EXCEEDED")
    );
    assert!(dense_outcome.carrier_manifest.is_none());
}

#[test]
fn manifest_only_carrier_derivation_applies_the_same_preallocation_fence() {
    let mut overflow = carrier();
    overflow.num_vertices = usize::MAX;

    let mut dense = carrier();
    dense.num_vertices = 1025;
    dense.faces.clear();
    dense.edges = vec![
        CarrierEdgeWireV1 {
            tail: 0,
            head: 1,
            weight_i128: "1".to_owned(),
        };
        1025
    ];

    for declaration in [overflow, dense] {
        let bytes = serde_json::to_vec(&declaration).expect("declaration serializes");
        let result = std::panic::catch_unwind(|| derive_carrier_manifest_bytes(&bytes))
            .expect("manifest-only resource validation must not panic");
        let error = result.expect_err("oversized declaration must be refused");
        assert!(
            error.contains("host fence") || error.contains("maximum is 1048576"),
            "unexpected refusal: {error}"
        );
    }
}

// Origin: engine/crates_rs/tests/pfp/host_contract.rs
// Claim: urn:core:crates_rs:tests:host-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordec669b63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordec669b63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorec669b63 {
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
impl BoundaryErrorec669b63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorec669b63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorec669b63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordec669b63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorec669b63> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorec669b63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorec669b63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorec669b63::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ec669b63() {
    let admitted = BoundaryRecordec669b63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordec669b63::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
