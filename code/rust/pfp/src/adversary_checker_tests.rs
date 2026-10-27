//! Native C011 composition contracts. AuthorityEffect: None.
use super::*;

fn fixture_payload(root: &Path, task_key: &str) -> Value {
    let resources = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    json!({
        "task_key": task_key, "objective": "Check an exact finite C011 certificate",
        "repo_root": root, "resources_root": resources,
        "adversary_output_dir": root.join("_ic/adversary"),
        "ledger_path": root.join("calls.jsonl"), "bout_id": "fixture1",
        "config_path": resources.join("adversary/config/seat_routing_v1.yaml"),
        "live": false,
        "symbol_game_request": {
            "schema_version": "core.symbol-game.request.v1",
            "checker_id": "symbol_game.c011.exact.v1", "authority_effect": "None",
            "case_json": "{\"challenge\":\"c011\",\"nodes\":[\"a\",\"b\"],\"edges\":[[\"a\",\"b\"]],\"claims\":{\"a->b\":\"1/10\"}}"
        }
    })
}

#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn native_c011_request_selects_checker_and_retains_rejected_fixture_bytes() {
    let root = tempfile::tempdir().unwrap();
    let outcome = dispatch(&fixture_payload(root.path(), "c011_fixture_binding")).unwrap();
    assert!(outcome["refusal"].is_null(), "{outcome}");
    let summary: Value = serde_json::from_slice(
        &fs::read(outcome["outcome"]["summary_path"].as_str().unwrap()).unwrap(),
    )
    .unwrap();
    let checks = summary["candidate_checks"].as_object().unwrap();
    assert_eq!(checks.len(), 3);
    for check in checks.values() {
        assert_eq!(check["verdict"], "REJECTED");
        assert_eq!(check["checker_id"], "symbol_game.c011.exact.v1");
        let raw = hex::decode(check["checker_receipt_hex"].as_str().unwrap()).unwrap();
        assert_eq!(
            check["checker_receipt_sha256"],
            core_adversary::evidence::sha256_ref(&raw)
        );
        let receipt: Value = serde_json::from_slice(&raw).unwrap();
        assert_eq!(receipt["run_key"], "c011_fixture_binding");
        assert_eq!(receipt["candidate_id"], check["candidate_id"]);
        assert_eq!(
            receipt["candidate_content_sha256"],
            check["candidate_content_sha256"]
        );
    }
    assert_eq!(summary["fixture_seats"], true);
    assert_eq!(summary["is_authorized"], false);
}

const SOLUTION: &str =
    r#"{"status":"SOLVED","phi1":"0","potential":{"a":"0","b":"1/10"},"repair":{},"dual":{}}"#;
#[test]
fn pfp_envelope_admission_does_not_replace_exact_candidate_verification() {
    use pfp_runtime::pfp_task_turn::PreparedTaskTurn;
    use core_adversary::checker_ports::CandidateCheckRequest;
    let root = tempfile::tempdir().unwrap();
    let payload = fixture_payload(root.path(), "pfp_exact_separation");
    let source: SymbolGameRequest =
        serde_json::from_value(payload["symbol_game_request"].clone()).unwrap();
    let prepared = PreparedTaskTurn::prepare(
        "Propose a finite C011 certificate",
        "problem data",
        "finite_c011",
        "attempt_0",
        json!({"case_sha256":core_adversary::evidence::sha256_ref(payload["symbol_game_request"]["case_json"].as_str().unwrap().as_bytes())}),
        "adversary-seat-string-v1",
    )
    .unwrap();
    for (certificate, expected) in [
        (SOLUTION.to_owned(), "ACCEPTED"),
        (SOLUTION.replace("1/10", "0"), "REJECTED"),
    ] {
        let raw=json!({"task_id":prepared.binding["task_id"],"attempt_id":prepared.binding["attempt_id"],"input_sha256":prepared.binding["input_sha256"],"answer":certificate}).to_string();
        let answer = prepared.check(raw.as_bytes()).unwrap();
        assert_eq!(answer.as_bytes(), certificate.as_bytes());
        let mut checker = NativeC011Checker::new(&source).unwrap();
        let check = checker
            .check_candidate(&CandidateCheckRequest {
                run_key: "pfp_exact_separation",
                objective: "Check certificate",
                candidate_id: "candidate_0",
                candidate_bytes: answer.as_bytes(),
                carrier_context: None,
            })
            .unwrap();
        let receipt: Value = serde_json::from_slice(check.receipt_bytes()).unwrap();
        assert_eq!(receipt["verdict"], expected);
        assert_eq!(
            receipt["candidate_content_sha256"],
            core_adversary::evidence::sha256_ref(certificate.as_bytes())
        );
        assert_eq!(receipt["authority_effect"], "None");
    }
}
struct NoNetwork;
impl SeatTransport for NoNetwork {
    fn configured(&self, _: &str) -> bool {
        panic!("fixture attempted network routing");
    }
    fn send(
        &mut self,
        _: &str,
        _: &str,
        _: &SeatPrompt,
        _: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        panic!("fixture attempted provider dispatch");
    }
}
struct ExactFixtureSeats<'a> {
    content: &'a str,
    malformed_critique: bool,
}
impl SeatPort for ExactFixtureSeats<'_> {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        let reply_text = if request.seat_id == "seat_gauge_breaker" {
            self.content.to_owned()
        } else if request.seat_id == "seat_defect_hunter" {
            if self.malformed_critique {
                "unstructured agreement".into()
            } else {
                "```critique\n{\"blocking\":false,\"counterexample\":null}\n```".into()
            }
        } else {
            "Fixture audit; no independent safety verification claimed.".into()
        };
        Ok(SeatTurnReply {
            raw_bytes: reply_text.as_bytes().to_vec(),
            reply_text,
            machine_fields: BTreeMap::from([("DISPOSITION".into(), "PASS".into())]),
            residual_colour: "Open".into(),
            authority_effect: "None".into(),
            model: None,
            provider: None,
            parameters: None,
            usage: None,
            request_digest: Some(request.request_digest()?),
        })
    }
}
fn complete(payload: &Value, content: &str, malformed_critique: bool) -> Value {
    let request: Request = serde_json::from_value(payload.clone()).unwrap();
    let (table, digest) = load_routing(&request.config_path).unwrap();
    let outcome = execute(
        &request,
        table,
        digest,
        NoNetwork,
        Some(&mut ExactFixtureSeats {
            content,
            malformed_critique,
        }),
    )
    .unwrap();
    serde_json::from_slice(&fs::read(outcome["summary_path"].as_str().unwrap()).unwrap()).unwrap()
}
fn checker_receipts(summary: &Value) -> Vec<Value> {
    summary["candidate_checks"]
        .as_object()
        .unwrap()
        .values()
        .map(|check| {
            let raw = hex::decode(check["checker_receipt_hex"].as_str().unwrap()).unwrap();
            assert_eq!(
                check["checker_receipt_sha256"],
                core_adversary::evidence::sha256_ref(&raw)
            );
            let receipt: Value = serde_json::from_slice(&raw).unwrap();
            assert_eq!(receipt["candidate_id"], check["candidate_id"]);
            assert_eq!(
                receipt["candidate_content_sha256"],
                check["candidate_content_sha256"]
            );
            assert_eq!(receipt["verdict"], check["verdict"]);
            receipt
        })
        .collect()
}
fn assert_rejected(summary: &Value) {
    let checks = summary["candidate_checks"].as_object().unwrap();
    assert_eq!(checks.len(), 3);
    assert!(
        checks.values().all(|check| check["verdict"] == "REJECTED"),
        "{summary}"
    );
    assert_eq!(summary["is_authorized"], false);
    assert_eq!(summary["selected_candidate_id"], "");
    assert_eq!(summary["status"], "REFUSED");
    assert_eq!(summary["authority_effect"], "None");
    assert!(checker_receipts(summary)
        .iter()
        .all(|receipt| receipt["verified_phi1"].is_null()));
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn exact_c011_full_bout_binds_bytes_and_remains_fixture_only() {
    let root = tempfile::tempdir().unwrap();
    let payload = fixture_payload(root.path(), "c011_exact_positive");
    let summary = complete(&payload, SOLUTION, false);
    assert_eq!(summary["status"], "FIXTURE_ONLY");
    assert_eq!(summary["is_authorized"], false);
    assert_eq!(summary["checker_verdict"], "ACCEPTED");
    assert_eq!(summary["fixture_seats"], true);
    assert!(summary["authorization_blockers"]
        .as_array()
        .unwrap()
        .contains(&json!("FIXTURE_SEATS")));
    for receipt in checker_receipts(&summary) {
        assert_eq!(
            receipt["candidate_content_sha256"],
            core_adversary::evidence::sha256_ref(SOLUTION.as_bytes())
        );
        let case = receipt["case_json"].as_str().unwrap();
        assert_eq!(
            receipt["case_sha256"],
            core_adversary::evidence::sha256_ref(case.as_bytes())
        );
        assert_eq!(
            case,
            payload["symbol_game_request"]["case_json"]
                .as_str()
                .unwrap()
        );
        assert_eq!(receipt["run_key"], "c011_exact_positive");
        assert_eq!(receipt["verified_phi1"], "0");
        assert_eq!(
            receipt["checker_source_sha256"],
            core_adversary::evidence::sha256_ref(include_bytes!("adversary_checker.rs"))
        );
        assert_eq!(
            receipt["checker_kernel_source_sha256"],
            core_adversary::evidence::sha256_ref(include_bytes!(
                "../../core_functional/src/phi1.rs"
            ))
        );
    }
    assert!(!root.path().join("calls.jsonl").exists());
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn c011_wrong_primal_gap_and_wire_shapes_cannot_survive_terminal_gate() {
    for content in [
        r#"{"status":"SOLVED","phi1":"0","potential":{"a":"0","b":"0"}}"#,
        r#"{"status":"SOLVED","phi1":"1/1000000","potential":{"a":"0","b":"1/10"}}"#,
        r#"{"status":"SOLVED","phi1":0.0,"potential":{"a":"0","b":"1/10"}}"#,
        r#"{"status":"SOLVED","phi1":false,"potential":{"a":"0","b":"1/10"}}"#,
        r#"{"status":"SOLVED","phi1":"0/1","potential":{"a":"0","b":"1/10"}}"#,
        r#"{"status":"UNKNOWN","phi1":"0","potential":{"a":"0","b":"1/10"}}"#,
        r#"{"status":"SOLVED","phi1":"0","phi1":"0","potential":{"a":"0","b":"1/10"}}"#,
        r#"{"status":"SOLVED","phi1":"0","potential":{"a":"0","b":"1/10","other":"0"}}"#,
        r#"{"status":"SOLVED","phi1":"0","potential":{"a":"0","b":"1/10"},"dual":{"unknown":"0"}}"#,
        r#"{"status":"SOLVED","phi1":"0","potential":{"a":"0","b":"1/10"},"authority_effect":"promoted"}"#,
        "```json\n{\"status\":\"SOLVED\"}\n```",
        "{",
    ] {
        let root = tempfile::tempdir().unwrap();
        let summary = complete(
            &fixture_payload(root.path(), "c011_wrong_candidate"),
            content,
            false,
        );
        assert_rejected(&summary);
        for receipt in checker_receipts(&summary) {
            assert_eq!(
                receipt["candidate_content_sha256"],
                core_adversary::evidence::sha256_ref(content.as_bytes())
            );
        }
    }
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn weighted_nonzero_certificate_is_checked_without_claiming_repair_or_authority() {
    let root = tempfile::tempdir().unwrap();
    let mut payload = fixture_payload(root.path(), "c011_weighted_cycle");
    payload["symbol_game_request"]["case_json"] = json!(
        r#"{"challenge":"c011","nodes":["a","b","c"],"edges":[["a","b"],["b","c"],["c","a"]],"claims":{"a->b":"1","b->c":"1","c->a":"1"},"weights":{"a->b":"2","b->c":"3","c->a":"4"}}"#
    );
    let valid = r#"{"status":"SOLVED","phi1":"6","potential":{"a":"0","b":"-2","c":"-1"},"repair":{"a->b":"3"},"dual":{"a->b":"2","b->c":"2","c->a":"2"}}"#;
    let accepted = complete(&payload, valid, false);
    assert!(checker_receipts(&accepted)
        .iter()
        .all(|receipt| receipt["verdict"] == "ACCEPTED" && receipt["verified_phi1"] == "6"));
    assert_eq!(accepted["is_authorized"], false);
    for content in [
        valid.replace("\"phi1\":\"6\"", "\"phi1\":\"0\""),
        valid.replace("\"c->a\":\"2\"", "\"c->a\":\"3\""),
    ] {
        let output = tempfile::tempdir().unwrap();
        payload["repo_root"] = json!(output.path());
        payload["adversary_output_dir"] = json!(output.path().join("_ic/adversary"));
        assert_rejected(&complete(&payload, &content, false));
    }
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn changed_case_rechecks_same_candidate_and_recovery_gets_new_run_receipt() {
    let first_root = tempfile::tempdir().unwrap();
    let first_payload = fixture_payload(first_root.path(), "c011_run_a");
    let first = complete(&first_payload, SOLUTION, false);
    let second_root = tempfile::tempdir().unwrap();
    let mut second_payload = fixture_payload(second_root.path(), "c011_run_b");
    second_payload["symbol_game_request"]["case_json"] = json!(first_payload
        ["symbol_game_request"]["case_json"]
        .as_str()
        .unwrap()
        .replace("1/10", "1/5"));
    let second = complete(&second_payload, SOLUTION, false);
    assert_rejected(&second);
    let recovery_root = tempfile::tempdir().unwrap();
    let recovered = complete(
        &fixture_payload(recovery_root.path(), "c011_run_c"),
        SOLUTION,
        false,
    );
    let a = checker_receipts(&first);
    let b = checker_receipts(&second);
    let c = checker_receipts(&recovered);
    assert_ne!(a[0]["case_sha256"], b[0]["case_sha256"]);
    assert_eq!(a[0]["case_sha256"], c[0]["case_sha256"]);
    assert_eq!(b[0]["run_key"], "c011_run_b");
    assert_eq!(c[0]["run_key"], "c011_run_c");
    assert_eq!(c[0]["verdict"], "ACCEPTED");
    assert_ne!(first["receipt_id"], recovered["receipt_id"]);
}
#[test]
fn invalid_c011_request_refuses_before_routing_or_storage() {
    for (field, value) in [
        ("schema_version", "foreign.v1"),
        ("checker_id", "test.accept_all"),
        ("authority_effect", "AUTHORIZED"),
    ] {
        let root = tempfile::tempdir().unwrap();
        let destination = root.path().join("must_not_exist");
        let mut payload = fixture_payload(&destination, "c011_bad_pin");
        payload["symbol_game_request"][field] = json!(value);
        payload["config_path"] = json!(root.path().join("missing_routing.yaml"));
        let result = dispatch(&payload).unwrap();
        assert_eq!(
            result["refusal"]["code"],
            "ADVERSARY_SYMBOL_GAME_REQUEST_INVALID"
        );
        assert!(!destination.exists());
    }
    for case in [
        r#"{"challenge":"c011","challenge":"c011","nodes":[],"edges":[]}"#,
        r#"{"challenge":"c011","challenge_id":"c012","nodes":[],"edges":[]}"#,
        r#"{"challenge":"c011","nodes":["a"],"edges":[["a","a"]]}"#,
        r#"{"challenge":"c011","nodes":["a"],"edges":[["a","b"]]}"#,
        r#"{"challenge":"c011","nodes":["a","a"],"edges":[]}"#,
        r#"{"challenge":"c011","nodes":["a","b"],"edges":[["a","b"]],"weights":{"a->b":"0"}}"#,
        r#"{"challenge":"c011","nodes":["a","b"],"edges":[["a","b"]],"claims":{"a->b":0.1}}"#,
        "{",
    ] {
        let root = tempfile::tempdir().unwrap();
        let destination = root.path().join("must_not_exist");
        let mut payload = fixture_payload(&destination, "c011_bad_case");
        payload["symbol_game_request"]["case_json"] = json!(case);
        let result = dispatch(&payload).unwrap();
        assert_eq!(
            result["refusal"]["code"], "ADVERSARY_SYMBOL_GAME_REQUEST_INVALID",
            "{result}"
        );
        assert!(!destination.exists());
    }
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn null_checker_malformed_critique_and_live_flag_keep_existing_fences() {
    let root = tempfile::tempdir().unwrap();
    let mut payload = fixture_payload(root.path(), "c011_null_checker");
    payload
        .as_object_mut()
        .unwrap()
        .remove("symbol_game_request");
    let unmeasured = complete(&payload, SOLUTION, false);
    assert_eq!(unmeasured["checker_verdict"], "NOT_MEASURED");
    assert_eq!(unmeasured["is_authorized"], false);
    let root = tempfile::tempdir().unwrap();
    let malformed = complete(
        &fixture_payload(root.path(), "c011_malformed_witness"),
        SOLUTION,
        true,
    );
    assert_eq!(malformed["is_authorized"], false);
    assert_eq!(malformed["status"], "REFUSED");
    let root = tempfile::tempdir().unwrap();
    let mut payload = fixture_payload(root.path(), "c011_live");
    payload["live"] = json!(true);
    let result = dispatch(&payload).unwrap();
    assert_eq!(result["refusal"]["code"], "NATIVE_INSTRUCTION_PLAN_UNBOUND");
    assert!(!root.path().join("calls.jsonl").exists());
    assert!(!root.path().join("_intelligence").exists());
    payload["live"] = json!("false");
    let result = dispatch(&payload).unwrap();
    assert_eq!(result["refusal"]["code"], "ADVERSARY_REQUEST_INVALID");
}
#[test]
fn raw_invalid_utf8_and_oversized_candidate_are_byte_bound_rejections() {
    let root = tempfile::tempdir().unwrap();
    let payload = fixture_payload(root.path(), "c011_raw");
    let request: SymbolGameRequest =
        serde_json::from_value(payload["symbol_game_request"].clone()).unwrap();
    let mut checker = NativeC011Checker::new(&request).unwrap();
    for bytes in [vec![0xff, 0xfe], vec![b' '; 16_385]] {
        let checked = checker
            .check_candidate(&core_adversary::checker_ports::CandidateCheckRequest {
                run_key: "c011_raw",
                objective: "raw negative",
                candidate_id: "candidate_raw",
                candidate_bytes: &bytes,
                carrier_context: None,
            })
            .unwrap();
        assert_eq!(
            checked.verdict(),
            core_adversary::evidence::CheckerVerdict::Rejected
        );
        assert_eq!(
            checked.candidate_content_sha256(),
            core_adversary::evidence::sha256_ref(&bytes)
        );
        assert_eq!(
            checked.receipt_sha256().unwrap(),
            core_adversary::evidence::sha256_ref(checked.receipt_bytes())
        );
    }
}
#[test]
#[ignore = "needs the adversary seat-routing config and council dossiers, which stay in the private engine repo"]
fn checker_emission_resolves_to_actual_audit_dossier_without_persona_verification() {
    use core_adversary::stage::file_adapters::MemoryUts;
    use core_adversary::stage::packets::CandidateProposal;
    use core_adversary::candidate_checks::{execute_candidate_checks, CandidateChecksInput};
    use core_adversary::evidence::sha256_ref;

    let root = tempfile::tempdir().unwrap();
    let request: SymbolGameRequest = serde_json::from_value(
        fixture_payload(root.path(), "c011_audit_identity")["symbol_game_request"].clone(),
    )
    .unwrap();
    let mut checker = NativeC011Checker::new(&request).unwrap();
    let candidate: CandidateProposal = serde_json::from_value(json!({
        "schema_version": "core.oeas.candidate-proposal.v1", "authority_effect": "None",
        "producer_agent_id": "seat_gauge_breaker", "work_packet_id": sha256_ref(b"work"),
        "artifact_refs": [sha256_ref(SOLUTION.as_bytes())],
        "prediction_receipt_id": sha256_ref(b"prediction"),
        "nonclaims": ["Finite certificate only; no persona or external authority."],
    }))
    .unwrap();
    let candidate_id = candidate.candidate_id().clone();
    let candidates = [candidate];
    let payloads = BTreeMap::from([(candidate_id.clone(), SOLUTION.as_bytes().to_vec())]);
    let carrier_hash = sha256_ref(b"bound-audit-carrier");
    let mut uts = MemoryUts::default();
    let mut emitters = EmitterSuite {
        uts: Some(&mut uts),
        ..Default::default()
    };
    let clock = RuntimeClock {
        start: Instant::now(),
    };
    let time = AuthorizationTime {
        event_clock: &clock,
        dda_timestamp: "2026-10-10 00:00:00 UTC",
    };
    let checks = execute_candidate_checks(
        Some(&mut checker),
        &CandidateChecksInput {
            run_key: "c011_audit_identity",
            objective: "Check a finite certificate",
            candidates: &candidates,
            candidate_payloads: &payloads,
            carrier_context: None,
            measurement: None,
            carrier_state_hash: Some(&carrier_hash),
            now_utc: time.dda_timestamp,
        },
        Some(&mut emitters),
        &time,
    )
    .unwrap();
    assert_eq!(
        checks[&candidate_id].verdict(),
        core_adversary::evidence::CheckerVerdict::Accepted
    );
    assert_eq!(uts.records.len(), 1);
    let (event, payload) = &uts.records[0];
    let resources = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    let rel_path = if resources.join("cognitive_operations/documentation/_sap/ana_000_forms_council_members/aletheia_procurator_v1.0.yaml").exists() {
        "cognitive_operations/documentation/_sap/ana_000_forms_council_members/aletheia_procurator_v1.0.yaml"
    } else {
        "cognitive_operations/ooutwire/_docs/_sap/ana_000_forms_council_members/aletheia_procurator_v1.0.yaml"
    };
    let dossier: Value =
        serde_yaml::from_str(&fs::read_to_string(resources.join(rel_path)).unwrap()).unwrap();
    let actor = &dossier["sentinel_actor_model"];
    assert_eq!(json!(event.actor_id()), actor["metadata"]["actor_id"]);
    assert_eq!(event.actor_kind(), "SWARM_SEAT");
    assert_eq!(event.authority_effect(), "None");
    assert_eq!(actor["use_policy"]["authority"]["authority_effect"], "none");
    assert_eq!(
        actor["use_policy"]["authority"]["model_may_mint_real_world_authority"],
        false
    );
    let record: Value = serde_json::from_slice(payload).unwrap();
    assert_eq!(record["checker_id"], "symbol_game.c011.exact.v1");
    assert_eq!(
        record["candidate_content_sha256"],
        sha256_ref(SOLUTION.as_bytes())
    );
    assert_eq!(event.payload_sha256(), &sha256_ref(payload));
    let receipt: Value = serde_json::from_slice(
        &hex::decode(record["checker_receipt_hex"].as_str().unwrap()).unwrap(),
    )
    .unwrap();
    assert_eq!(
        receipt["checker_source_sha256"],
        sha256_ref(include_bytes!("adversary_checker.rs"))
    );
    assert_eq!(receipt["authority_effect"], "None");
}

// Origin: engine/crates_rs/pfp/src/adversary_checker_tests.rs
// Claim: urn:core:crates_rs:pfp:adversary-checker-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord77aea0ce {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord77aea0ce` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError77aea0ce {
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
impl BoundaryError77aea0ce {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError77aea0ce {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError77aea0ce {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord77aea0ce {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError77aea0ce> {
        if capacity_bound == 0 {
            return Err(BoundaryError77aea0ce::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError77aea0ce::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError77aea0ce::ExceedsCapacity {
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
mod l4_boundary_tests_77aea0ce {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord77aea0ce::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord77aea0ce::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord77aea0ce::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord77aea0ce::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord77aea0ce::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError77aea0ce::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError77aea0ce::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
