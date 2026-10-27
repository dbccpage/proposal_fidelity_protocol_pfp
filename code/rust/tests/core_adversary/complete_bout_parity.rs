use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    Clock, DdcSink, EmitterSuite, GenealogySink, IntelligenceEvent, UnsSink, UtsSink,
};
use core_adversary::stage::genealogy::GenealogyEntry;
use core_adversary::stage::packets::{AgentResult, WorkPacket};
use core_adversary::stage::ports::{Refusal, SchedulerPort, SeatPort, SeatTurnReply, SeatTurnRequest};
use core_adversary::stage::run::{ProgressMeasure, SwarmRunState};
use core_adversary::stage::synthetic_diagnostic::NativeSbeDiagnostic;
use core_adversary::authorization::AuthorizationTime;
use core_adversary::bout_boundary::{
    execute_captured_bout_boundary, BoutAbort, BoutRunSpec, RefusalBundlePort,
};
use core_adversary::checker_ports::{CandidateCheckRequest, CandidateCheckerPort};
use core_adversary::complete_bout::{
    execute_complete_bout, CompleteBoutInput, CompleteBoutPorts, GovernancePort, GovernanceRequest,
};
use core_adversary::custody::RecordingSeatPort;
use core_adversary::evidence::{
    sha256_ref, CandidateCheck, CandidateCheckInput, CheckerVerdict, ObstructionMeasurement,
};
use core_adversary::journal::{EntryKind, JournalPort};
use core_adversary::journal_store::JsonlJournal;
use core_adversary::render_record::{JsonStyle, RenderRecord};
use core_adversary::run_folder_store::{recompute_receipt_id, RunFolderStore};
use core_adversary::scoring_ports::{CochainScoringPort, CochainScoringRequest};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::cell::RefCell;
use std::rc::Rc;

#[derive(Default)]
struct Bundles {
    turns: Vec<serde_json::Map<String, Value>>,
}
impl RefusalBundlePort for Bundles {
    fn persist(
        &mut self,
        _: &BoutRunSpec,
        _: &Refusal,
        _: &str,
        turns: &[serde_json::Map<String, Value>],
    ) -> Result<String, Refusal> {
        self.turns = turns.to_vec();
        Ok("fixture-bundle".into())
    }
}

type Calls = Rc<RefCell<Vec<Value>>>;
fn refusal(code: &str, message: &str) -> Refusal {
    let mut r = Refusal::new(code, message);
    r.locus = "fixture".into();
    r
}
struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-04T12:00:00Z".into()
    }
}
struct Scheduler {
    state: SwarmRunState,
    failed: bool,
    calls: Calls,
}
impl SchedulerPort for Scheduler {
    fn start(&mut self, key: &str, packet: &WorkPacket) -> Result<SwarmRunState, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"scheduler","run_key":key,"packet":packet}));
        if self.failed {
            Err(refusal(
                "FIXTURE_SCHEDULER_REFUSED",
                "scheduler unavailable",
            ))
        } else {
            Ok(self.state.clone())
        }
    }
    fn advance(
        &mut self,
        state: &SwarmRunState,
        _: &AgentResult,
        _: &ProgressMeasure,
    ) -> Result<SwarmRunState, Refusal> {
        if state.terminal_status() == "COMPLETED" {
            panic!("status COMPLETED written before advance");
        }
        Ok(state
            .with_terminal_status("COMPLETED")
            .expect("scheduler result"))
    }
}
struct Seats {
    responses: Value,
    fail_at: usize,
    count: usize,
    calls: Calls,
}
impl SeatPort for Seats {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.calls.borrow_mut().push(json!({"sink":"seat","request":request,"request_digest":request.request_digest().unwrap()}));
        self.count += 1;
        if self.count == self.fail_at {
            return Err(refusal("FIXTURE_SEAT_REFUSED", "seat unavailable"));
        }
        Ok(serde_json::from_value(self.responses[&request.seat_id].clone()).unwrap())
    }
}
struct Sink {
    name: &'static str,
    failed: String,
    steps: Vec<DdcStep>,
    calls: Calls,
}
impl Sink {
    fn result(&self) -> Result<String, Refusal> {
        if self.name == self.failed {
            Err(refusal(
                "FIXTURE_SINK_REFUSED",
                &format!("{} refused", self.name),
            ))
        } else {
            Ok("recorded".into())
        }
    }
}
impl UtsSink for Sink {
    fn record_event(
        &mut self,
        event: &IntelligenceEvent,
        payload: &[u8],
    ) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":self.name,"event":event,"raw_bytes":payload}));
        self.result()
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, session: &str, text: &str) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":self.name,"session":session,"text":text}));
        self.result()
    }
}
impl DdcSink for Sink {
    fn record_step(&mut self, step: &DdcStep) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":self.name,"step":step}));
        let result = self.result();
        if result.is_ok() {
            self.steps.push(step.clone());
        }
        result
    }
    fn recorded_steps(&self) -> Option<&[DdcStep]> {
        Some(&self.steps)
    }
}
struct Scorer {
    measurements: Vec<ObstructionMeasurement>,
    index: usize,
    calls: Calls,
}
impl CochainScoringPort for Scorer {
    fn identify_obstructions(
        &mut self,
        request: &CochainScoringRequest<'_>,
    ) -> Result<ObstructionMeasurement, Refusal> {
        self.calls.borrow_mut().push(json!({"sink":"scorer","network":request.network.to_dict().unwrap(),"cochain":request.initial_cochain.to_dict(),"ablation_flags":request.ablation_flags}));
        let result = self.measurements[self.index.min(self.measurements.len() - 1)].clone();
        self.index += 1;
        Ok(result)
    }
}
struct Checker {
    mode: String,
    calls: Calls,
}
impl CandidateCheckerPort for Checker {
    fn check_candidate(
        &mut self,
        r: &CandidateCheckRequest<'_>,
    ) -> Result<CandidateCheck, Refusal> {
        self.calls.borrow_mut().push(json!({"port":"checker","run_key":r.run_key,"objective":r.objective,"candidate_id":r.candidate_id,"candidate_hex":hex::encode(r.candidate_bytes),"carrier_context":r.carrier_context}));
        if self.mode == "error" {
            return Err(refusal("FIXTURE_CHECK_REFUSED", "checker unavailable"));
        }
        let verdict = if self.mode == "rejected" {
            CheckerVerdict::Rejected
        } else {
            CheckerVerdict::Accepted
        };
        let digest = sha256_ref(r.candidate_bytes);
        let receipt = RenderRecord::from_json(
            &json!({"content":digest,"checker":"exact.e\u{301}"}).to_string(),
        )
        .unwrap()
        .json(JsonStyle::SpacedSortedAscii)
        .unwrap()
        .into_bytes();
        CandidateCheck::new(CandidateCheckInput {
            verdict,
            candidate_id: r.candidate_id.into(),
            candidate_content_sha256: digest,
            checker_id: "exact.e\u{301}".into(),
            checker_receipt_sha256: Some(sha256_ref(&receipt)),
            checker_receipt_bytes: receipt,
            reason: "checked e\u{301}".into(),
        })
    }
}
struct Governance(Value);
impl GovernancePort for Governance {
    fn resolve_and_verify(&mut self, _: &GovernanceRequest<'_>) -> Result<Value, Refusal> {
        Ok(self.0.clone())
    }
}

#[test]
fn ddc_preflight_refuses_before_scheduler_seat_or_artifact_calls(
) -> Result<(), Box<dyn std::error::Error>> {
    struct UnreadableDdc;
    impl DdcSink for UnreadableDdc {
        fn record_step(&mut self, _: &DdcStep) -> Result<String, Refusal> {
            panic!("an unreadable tape must be refused before emission")
        }
    }
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_complete_bout_v1.json"))?;
    let case = &fixture["vectors"][0];
    for (configured, offset, expected) in [
        (true, 0, "ADVERSARY_DDC_TAPE_UNAVAILABLE"),
        (false, 1, "ADVERSARY_DDC_OFFSET_MISMATCH"),
    ] {
        let calls: Calls = Rc::default();
        let root = tempfile::tempdir()?;
        let packet: WorkPacket = serde_json::from_value(case["packet"].clone())?;
        let mut scheduler = Scheduler {
            state: serde_json::from_value(case["start_state"].clone())?,
            failed: true,
            calls: calls.clone(),
        };
        let mut seats = Seats {
            responses: Value::Null,
            fail_at: 1,
            count: 0,
            calls: calls.clone(),
        };
        let mut recorder =
            RecordingSeatPort::new(&mut seats, None, "preflight", packet.task_key(), "", None);
        let mut governance = Governance(Value::Null);
        let mut store = RunFolderStore::new(root.path().into());
        let mut diagnostic = NativeSbeDiagnostic;
        let mut sink = UnreadableDdc;
        let mut progress = String::new();
        let error = execute_complete_bout(
            &CompleteBoutInput {
                packet: &packet,
                carrier_json: None,
                carrier_context: None,
                ablation_flags: None,
                fixture_seats: &Value::Bool(true),
                request_external_admission: &Value::Bool(false),
                max_candidate_budget: 0,
                max_critique_rounds: 0,
                ddc_step_offset: offset,
                now_utc: "2026-10-05 12:00:00 UTC",
                instruction_plan: None,
                panel: None,
                initial_state: None,
            },
            CompleteBoutPorts {
                scheduler: &mut scheduler,
                diagnostic: &mut diagnostic,
                scorer: None,
                regge: None,
                checker: None,
                host: None,
                governance: &mut governance,
                artifacts: &mut store,
                emitters: Some(EmitterSuite {
                    ddc: configured.then_some(&mut sink as &mut dyn DdcSink),
                    ..EmitterSuite::default()
                }),
            },
            &mut recorder,
            &mut progress,
            &AuthorizationTime {
                event_clock: &FrozenClock,
                dda_timestamp: "2026-10-05 12:00:00 UTC",
            },
        )
        .expect_err("DDC custody must be checked before collaborators execute");
        assert_eq!(error.code, expected);
        assert_eq!(progress, "DDC_PREFLIGHT");
        assert!(calls.borrow().is_empty());
        assert!(recorder.turns.is_empty());
        assert_eq!(std::fs::read_dir(root.path())?.count(), 0);
    }
    Ok(())
}

#[test]
fn immutable_v1_inputs_preserve_candidate_checker_and_custody_contracts() {
    let frozen = include_bytes!("fixtures/python_complete_bout_v1.json");
    assert_eq!(
        independent_digest(frozen),
        "34daee98cddb90f78518107741ccc2c554cea14e1f263029dac60e59450e11bf"
    );
    let fixture: Value = serde_json::from_slice(frozen).unwrap();
    assert_eq!(fixture["freeze"], "before-native-composition");
    for (index, case) in fixture["vectors"].as_array().unwrap().iter().enumerate() {
        let calls: Calls = Rc::default();
        let root = tempfile::tempdir().unwrap();
        let packet: WorkPacket = serde_json::from_value(case["packet"].clone()).unwrap();
        let mut scheduler = Scheduler {
            state: serde_json::from_value(case["start_state"].clone()).unwrap(),
            failed: case["scheduler_failed"] == true,
            calls: calls.clone(),
        };
        let mut seats = Seats {
            responses: case["responses"].clone(),
            fail_at: case["fail_at"].as_u64().unwrap() as usize,
            count: 0,
            calls: calls.clone(),
        };
        let mut scorer = Scorer {
            measurements: case["measurements"]
                .as_array()
                .unwrap()
                .iter()
                .map(|m| ObstructionMeasurement::from_json(m).unwrap())
                .collect(),
            index: 0,
            calls: calls.clone(),
        };
        let mut checker = Checker {
            mode: case["checker"].as_str().unwrap().into(),
            calls: calls.clone(),
        };
        let mut governance = Governance(case["governance"].clone());
        let mut store = RunFolderStore::new(root.path().into());
        let sink = |name| Sink {
            name,
            failed: case["failed"].as_str().unwrap().into(),
            steps: vec![],
            calls: calls.clone(),
        };
        let mut uts = sink("uts");
        let mut ddc = sink("ddc");
        let mut uns = sink("uns");
        let emitters = (case["emission"] == true).then_some(EmitterSuite {
            uts: Some(&mut uts),
            ddc: Some(&mut ddc),
            uns: Some(&mut uns),
            ..Default::default()
        });
        let carrier = case["carrier"].to_string();
        let mut diagnostic = NativeSbeDiagnostic;
        let mut act = String::new();
        // Later native acceptance joins the previously tested journal boundary.
        let spec = BoutRunSpec {
            bout_id: format!("bout-{index}"),
            task_key: packet.task_key().clone(),
            objective: packet.objective().clone(),
            fixture_seats: false,
            learning_guidance: String::new(),
            instruction_plan: None,
        };
        let mut journal = JsonlJournal::new(root.path().join("journal.jsonl"));
        let mut bundles = Bundles::default();
        let boundary = execute_captured_bout_boundary(
            &spec,
            &mut seats,
            Some(&mut journal),
            &mut bundles,
            |recorder, progress| {
                let result = execute_complete_bout(
                    &CompleteBoutInput {
                        packet: &packet,
                        carrier_json: (case["carrier"] != Value::Null).then_some(carrier.as_str()),
                        carrier_context: case["carrier"].as_object(),
                        ablation_flags: case["flags"].as_object(),
                        fixture_seats: &Value::Bool(false),
                        request_external_admission: &case["external"],
                        max_candidate_budget: case["budget"].as_i64().unwrap(),
                        max_critique_rounds: case["rounds"].as_i64().unwrap(),
                        ddc_step_offset: 0,
                        now_utc: "2026-10-04 12:00:00 UTC",
                        instruction_plan: None,
                        panel: None,
                        initial_state: None,
                    },
                    CompleteBoutPorts {
                        scheduler: &mut scheduler,
                        diagnostic: &mut diagnostic,
                        scorer: Some(&mut scorer),
                        regge: None,
                        checker: (case["checker"] != "null")
                            .then_some(&mut checker as &mut dyn CandidateCheckerPort),
                        host: None,
                        governance: &mut governance,
                        artifacts: &mut store,
                        emitters,
                    },
                    recorder,
                    progress,
                    &AuthorizationTime {
                        event_clock: &FrozenClock,
                        dda_timestamp: "2026-10-04 12:00:00 UTC",
                    },
                );
                act = progress.clone();
                result.map_err(BoutAbort::from)
            },
        );
        let entries = journal.read_all().unwrap();
        assert_eq!(
            entries
                .iter()
                .filter(|e| e.kind == EntryKind::BoutTerminal)
                .count(),
            1
        );
        assert_eq!(
            entries
                .iter()
                .filter(|e| e.kind == EntryKind::SeatTurnStarted)
                .count(),
            boundary.turns.len()
        );
        assert_eq!(
            entries
                .iter()
                .filter(|e| e.kind == EntryKind::SeatTurnCompleted)
                .count(),
            boundary.turns.len()
        );
        let result = boundary.result.map_err(|abort| match abort {
            BoutAbort::Refused(mut r) => {
                if !boundary.turns.is_empty() {
                    assert_eq!(bundles.turns, boundary.turns);
                    assert_eq!(
                        r.details.remove("refusal_bundle"),
                        Some("fixture-bundle".into())
                    );
                }
                r
            }
            other => panic!("unexpected abort {other:?}"),
        });
        if case["expected"].get("error").is_some() && case["act"] == "NOVELLA" {
            let outcome = result.expect("reporting failure preserves the completed task");
            assert!(outcome.run_directory.is_none());
            assert!(outcome.receipt.get("receipt_id").is_none());
            assert_eq!(outcome.summary["reporting"]["status"], "REPORTING_FAILED");
            assert_eq!(outcome.summary["terminal_status"], "COMPLETED");
            assert!(outcome.summary["candidate_checks"].is_object());
            assert_eq!(outcome.summary["reporting"]["task_outcome_changed"], false);
        } else if case["expected"].get("error").is_some() {
            assert_eq!(
                json!(result.unwrap_err()),
                case["expected"]["error"],
                "case {index}"
            );
        } else {
            let outcome = result.unwrap();
            assert_eq!(
                json!(outcome.final_state),
                case["expected"]["state"],
                "state case {index}"
            );
            let (_, summary) =
                read_verified_bundle(outcome.run_directory.as_deref().unwrap(), &outcome.receipt);
            assert_stable_v1_contract(case, &outcome.receipt, &summary);
            let folder = std::path::Path::new(outcome.run_directory.as_deref().unwrap());
            let dda = std::fs::read(folder.join("ddc.jsonl")).unwrap();
            assert_eq!(
                dda,
                hex::decode(
                    case["expected"]["files"]["dda_actions.jsonl"]
                        .as_str()
                        .unwrap()
                )
                .unwrap()
            );
            assert_eq!(std::fs::read(folder.join("ddc.jsonl")).unwrap(), dda);
        }
        assert_eq!(act, case["act"].as_str().unwrap(), "case {index}");
        let checker_calls = |rows: &[Value]| {
            rows.iter()
                .filter(|row| row["port"] == "checker")
                .cloned()
                .collect::<Vec<_>>()
        };
        assert_eq!(
            checker_calls(calls.borrow().as_slice()),
            checker_calls(case["calls"].as_array().unwrap()),
            "checker port case {index}"
        );
    }
}

// Post-live v2 semantics deliberately differ from the frozen Python v1
// artifact hashes above. Reuse only its immutable input declarations; these
// assertions state the new public-port contract rather than regenerating goldens.
struct PostLiveBout {
    receipt: Value,
    summary: Value,
    calls: Vec<Value>,
}
struct PostLiveGenealogy(Calls);
impl GenealogySink for PostLiveGenealogy {
    fn record_lineage(&mut self, entry: &GenealogyEntry) -> Result<String, Refusal> {
        self.0
            .borrow_mut()
            .push(json!({"sink":"genealogy","entry":entry.to_dict()}));
        Ok("postlive-lineage".into())
    }
}
fn postlive_bout(
    input_index: usize,
    fixture_seats: bool,
    external: bool,
    flags: Option<Value>,
    checker_mode: Option<&str>,
) -> PostLiveBout {
    postlive_bout_with_reporting_failure(
        input_index,
        fixture_seats,
        external,
        flags,
        checker_mode,
        false,
    )
}
fn postlive_bout_with_reporting_failure(
    input_index: usize,
    fixture_seats: bool,
    external: bool,
    flags: Option<Value>,
    checker_mode: Option<&str>,
    reporting_failure: bool,
) -> PostLiveBout {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_complete_bout_v1.json")).unwrap();
    let case = &fixture["vectors"][input_index];
    let calls: Calls = Rc::default();
    let root = tempfile::tempdir().unwrap();
    let packet: WorkPacket = serde_json::from_value(case["packet"].clone()).unwrap();
    if reporting_failure {
        std::fs::create_dir_all(root.path().join("runs").join(packet.task_key())).unwrap();
    }
    let mut scheduler = Scheduler {
        state: serde_json::from_value(case["start_state"].clone()).unwrap(),
        failed: false,
        calls: calls.clone(),
    };
    let mut seats = Seats {
        responses: case["responses"].clone(),
        fail_at: 0,
        count: 0,
        calls: calls.clone(),
    };
    let mut scorer = Scorer {
        measurements: case["measurements"]
            .as_array()
            .unwrap()
            .iter()
            .map(|value| ObstructionMeasurement::from_json(value).unwrap())
            .collect(),
        index: 0,
        calls: calls.clone(),
    };
    let mode = checker_mode.unwrap_or(case["checker"].as_str().unwrap());
    let mut checker = Checker {
        mode: mode.into(),
        calls: calls.clone(),
    };
    let mut governance = Governance(case["governance"].clone());
    let mut store = RunFolderStore::new(root.path().into());
    let sink = |name| Sink {
        name,
        failed: String::new(),
        steps: vec![],
        calls: calls.clone(),
    };
    let mut uts = sink("uts");
    let mut ddc = sink("ddc");
    let mut uns = sink("uns");
    let mut genealogy = PostLiveGenealogy(calls.clone());
    let mut diagnostic = NativeSbeDiagnostic;
    let carrier = case["carrier"].to_string();
    let fixture_flag = json!(fixture_seats);
    let external_flag = json!(external);
    let mut recorder = RecordingSeatPort::new(
        &mut seats,
        None,
        "postlive-bout",
        packet.task_key(),
        "",
        None,
    );
    let mut progress = String::new();
    let outcome = execute_complete_bout(
        &CompleteBoutInput {
            packet: &packet,
            carrier_json: (!case["carrier"].is_null()).then_some(carrier.as_str()),
            carrier_context: case["carrier"].as_object(),
            ablation_flags: flags.as_ref().and_then(Value::as_object),
            fixture_seats: &fixture_flag,
            request_external_admission: &external_flag,
            max_candidate_budget: case["budget"].as_i64().unwrap(),
            max_critique_rounds: case["rounds"].as_i64().unwrap(),
            ddc_step_offset: 0,
            now_utc: "2026-10-04 12:00:00 UTC",
            instruction_plan: None,
            panel: None,
            initial_state: None,
        },
        CompleteBoutPorts {
            scheduler: &mut scheduler,
            diagnostic: &mut diagnostic,
            scorer: Some(&mut scorer),
            regge: None,
            checker: (mode != "null").then_some(&mut checker as &mut dyn CandidateCheckerPort),
            host: None,
            governance: &mut governance,
            artifacts: &mut store,
            emitters: Some(EmitterSuite {
                uts: Some(&mut uts),
                ddc: Some(&mut ddc),
                uns: Some(&mut uns),
                genealogy: Some(&mut genealogy),
                ..Default::default()
            }),
        },
        &mut recorder,
        &mut progress,
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-04 12:00:00 UTC",
        },
    )
    .expect("controlled input must complete through the real seven-act controller");
    assert_eq!(progress, "PERSIST");
    let (receipt, summary) = if let Some(path) = &outcome.run_directory {
        assert!(!reporting_failure);
        read_verified_bundle(path, &outcome.receipt)
    } else {
        assert!(reporting_failure);
        assert!(recorder
            .journal_residuals
            .iter()
            .any(|error| error.code == "RUN_FOLDER_EXISTS"));
        assert_eq!(
            std::fs::read_dir(root.path().join("runs").join(packet.task_key()))
                .unwrap()
                .count(),
            0
        );
        (outcome.receipt, outcome.summary)
    };
    let observed = calls.borrow().clone();
    PostLiveBout {
        receipt,
        summary,
        calls: observed,
    }
}
fn assert_postlive_no_lineage(bout: &PostLiveBout) {
    assert!(
        !bout.calls.iter().any(|call| call["sink"] == "genealogy"),
        "an accepted capture must not invent a no-survivor re-entry instruction"
    );
}

#[test]
fn postlive_authorized_without_carrier_is_checker_accepted_without_reentry() {
    let bout = postlive_bout(0, false, false, None, None);
    assert_eq!(bout.receipt["status"], "AUTHORIZED");
    assert_eq!(bout.summary["disposition"], "SELECT");
    assert_eq!(bout.summary["checker_verdict"], "ACCEPTED");
    assert_eq!(bout.summary["terminal_verdict"], "PASS_TO_MASTER");
    assert_eq!(bout.summary["consecration_state"], "CHECKER_ACCEPTED");
    assert_eq!(
        bout.summary["authorization_evidence"],
        "CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED"
    );
    assert_eq!(bout.summary["measurement_status"], "NOT_MEASURED");
    assert_eq!(bout.summary["phi1"], Value::Null);
    assert_eq!(bout.summary["gamma2"], Value::Null);
    assert_eq!(bout.summary["authorization_blockers"], json!([]));
    assert_postlive_no_lineage(&bout);
}

#[test]
fn postlive_declared_zero_retains_combined_evidence_and_checker_completion() {
    let bout = postlive_bout(2, false, false, None, None);
    assert_eq!(bout.receipt["status"], "AUTHORIZED");
    assert_eq!(bout.summary["terminal_verdict"], "PASS_TO_MASTER");
    assert_eq!(bout.summary["consecration_state"], "CHECKER_ACCEPTED");
    assert_eq!(
        bout.summary["authorization_evidence"],
        "CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER"
    );
    assert_eq!(
        bout.summary["lggr_joint_kernel_status"],
        "ZERO_ON_DECLARED_CARRIER"
    );
    assert_postlive_no_lineage(&bout);
}

#[test]
fn postlive_external_admission_is_only_a_proposal_after_authorized_completion() {
    let bout = postlive_bout(0, false, true, None, None);
    assert_eq!(bout.receipt["status"], "AUTHORIZED");
    assert_eq!(
        bout.summary["terminal_verdict"],
        "PROPOSED_FOR_EXTERNAL_ADMISSION"
    );
    assert_eq!(
        bout.summary["consecration_state"],
        "PROPOSED_FOR_EXTERNAL_ADMISSION"
    );
    assert_eq!(bout.summary["authority_effect"], "None");
    assert_postlive_no_lineage(&bout);
}

#[test]
fn postlive_fixture_and_ablation_are_not_promoted_even_on_external_request() {
    for external in [false, true] {
        for (fixture, flags, expected_status) in [
            (true, None, "FIXTURE_ONLY"),
            (
                false,
                Some(json!({"no_authorization_boundary":true})),
                "ABLATED_WOULD_AUTHORIZE",
            ),
        ] {
            let bout = postlive_bout(0, fixture, external, flags, None);
            assert_eq!(bout.receipt["status"], expected_status);
            assert_eq!(bout.summary["is_authorized"], false);
            assert_eq!(bout.summary["terminal_verdict"], "COMPOSTED");
            assert_eq!(
                bout.summary["consecration_state"],
                "COMPOSTED_WITH_REENTRY_GUIDANCE"
            );
            assert_eq!(bout.summary["authorization_evidence"], Value::Null);
        }
    }
}

#[test]
fn postlive_rejection_and_missing_checker_never_become_a_pass_or_external_proposal() {
    for (mode, expected) in [("rejected", "REFUSED"), ("null", "NOT_MEASURED")] {
        for external in [false, true] {
            let bout = postlive_bout(0, false, external, None, Some(mode));
            assert_eq!(bout.receipt["status"], expected);
            assert_eq!(bout.summary["is_authorized"], false);
            assert_eq!(bout.summary["terminal_verdict"], "COMPOSTED");
            assert_eq!(bout.summary["authorization_evidence"], Value::Null);
            assert!(!bout.summary["authorization_blockers"]
                .as_array()
                .unwrap()
                .is_empty());
        }
    }
}

#[test]
fn postlive_open_or_unmeasured_declared_carrier_is_not_promoted_by_accepted_checker() {
    for (index, expected, blocker) in [
        (4, "BOUNDED_RESIDUAL", "OPEN_OBSTRUCTION"),
        (5, "NOT_MEASURED", "CARRIER_NOT_MEASURED"),
    ] {
        let bout = postlive_bout(index, false, true, None, None);
        assert_eq!(bout.receipt["status"], expected);
        assert_eq!(bout.summary["checker_verdict"], "ACCEPTED");
        assert_eq!(bout.summary["terminal_verdict"], "COMPOSTED");
        assert_eq!(bout.summary["is_authorized"], false);
        assert!(bout.summary["authorization_blockers"]
            .as_array()
            .unwrap()
            .contains(&json!(blocker)));
    }
}

#[test]
fn postlive_sandbox_receives_the_current_exact_candidate_bytes_and_objective() {
    let bout = postlive_bout(0, false, false, None, None);
    let sandbox: Vec<_> = bout
        .calls
        .iter()
        .filter(|call| call["sink"] == "seat" && call["request"]["scene_id"] == "act4_sandbox")
        .collect();
    assert_eq!(sandbox.len(), 1);
    let raw: Vec<u8> =
        serde_json::from_value(sandbox[0]["request"]["context_bytes"].clone()).unwrap();
    let context: Value = serde_json::from_slice(&raw).unwrap();
    assert_eq!(context["objective"], bout.summary["objective"]);
    let artifacts = bout.summary["candidate_artifacts"].as_array().unwrap();
    assert!(!artifacts.is_empty());
    let expected: Vec<_> = artifacts
        .iter()
        .map(|row| json!({"candidate_id":row["candidate_id"],"content":row["content"]}))
        .collect();
    assert_eq!(context["candidates"], json!(expected));
    for row in artifacts {
        let content = row["content"].as_str().unwrap().as_bytes();
        assert!(content
            .windows("e\u{301}".len())
            .any(|bytes| bytes == "e\u{301}".as_bytes()));
        assert!(bout.calls.iter().any(|call| call["port"] == "checker"
            && call["candidate_id"] == row["candidate_id"]
            && call["candidate_hex"] == hex::encode(content)));
    }
}

// The immutable v1 inputs retain candidate/checker semantics. Presentation,
// terminal labels and exact request context belong to the postlive tests above.
fn independent_digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn read_verified_bundle(directory: &str, declaration: &Value) -> (Value, Value) {
    let folder = std::path::Path::new(directory);
    // Five bound files plus the `mam/` story folder.
    assert_eq!(std::fs::read_dir(folder).unwrap().count(), 6);
    assert!(folder.join("mam").is_dir());
    let read = |name| std::fs::read(folder.join(name)).unwrap();
    let receipt: Value = serde_json::from_slice(&read("receipt.json")).unwrap();
    let summary: Value = serde_json::from_slice(&read("summary.json")).unwrap();
    for (name, key) in [
        ("uns.md", "uns_sha256"),
        ("summary.json", "summary_sha256"),
        ("ddc.jsonl", "ddc_sha256"),
        ("uts.jsonl", "uts_sha256"),
    ] {
        assert_eq!(
            receipt[key],
            independent_digest(&read(name)),
            "{name} byte custody"
        );
    }
    assert_eq!(receipt["receipt_id"], recompute_receipt_id(folder).unwrap());
    assert_eq!(
        receipt["receipt_id"],
        core_adversary::run_folder_store::verify_reported_bundle(folder).unwrap()
    );
    for key in [
        "receipt_id",
        "status",
        "selected_candidate_id",
        "checker_receipt_sha256",
        "checker_verdict",
        "authority_effect",
    ] {
        assert_eq!(receipt[key], declaration[key], "application/disk {key}");
        assert_eq!(receipt[key], summary[key], "receipt/summary {key}");
    }
    assert!(!folder.join("dda_actions.jsonl").exists());
    assert!(!folder.join("novella.md").exists());
    assert_eq!(summary["bundle_schema"], "core.adversary.run-bundle.v3");
    assert_eq!(summary["terminal_status"], "COMPLETED");
    assert_eq!(receipt["authority_effect"], "None");
    (receipt, summary)
}
fn assert_stable_v1_contract(case: &Value, receipt: &Value, summary: &Value) {
    let raw = hex::decode(case["expected"]["files"]["summary.json"].as_str().unwrap()).unwrap();
    let old: Value = serde_json::from_slice(&raw).unwrap();
    for key in [
        "status",
        "selected_candidate_id",
        "checker_receipt_sha256",
        "checker_verdict",
        "authority_effect",
    ] {
        assert_eq!(
            receipt[key], case["expected"]["ok"][key],
            "stable receipt {key}"
        );
        assert_eq!(summary[key], old[key], "stable summary {key}");
    }
    assert_eq!(summary["candidate_checks"], old["candidate_checks"]);
    let artifacts = summary["candidate_artifacts"].as_array().unwrap();
    assert_eq!(artifacts.len(), case["budget"].as_u64().unwrap() as usize);
    // Repair rounds may replace generation IDs. Final checker IDs/receipts
    // above remain frozen; these new artifact rows retain the generation bytes.
    let ids = artifacts
        .iter()
        .map(|row| row["candidate_id"].as_str().unwrap())
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(ids.len(), artifacts.len());
    for row in artifacts {
        let content = row["content"].as_str().unwrap();
        assert_eq!(
            content,
            case["responses"]["seat_gauge_breaker"]["reply_text"]
                .as_str()
                .unwrap()
        );
        let digest = format!("sha256:{}", independent_digest(content.as_bytes()));
        assert_eq!(row["content_sha256"], digest);
        assert_eq!(
            row["selected"],
            row["candidate_id"] == old["selected_candidate_id"]
        );
    }
}

#[test]
fn report_persistence_failure_retains_checker_outcome_and_retry_source() {
    let bout = postlive_bout_with_reporting_failure(0, false, false, None, None, true);
    assert_eq!(bout.receipt["status"], "AUTHORIZED");
    assert_eq!(bout.summary["checker_verdict"], "ACCEPTED");
    assert_eq!(bout.summary["terminal_status"], "COMPLETED");
    assert_eq!(bout.summary["reporting"]["status"], "REPORTING_FAILED");
    assert_eq!(
        bout.summary["reporting"]["failure_code"],
        "RUN_FOLDER_EXISTS"
    );
    assert!(bout.receipt.get("receipt_id").is_none());
    assert!(bout.summary.get("receipt_id").is_none());
    assert!(!bout.summary["seat_turns"].as_array().unwrap().is_empty());
    assert!(bout.summary["candidate_checks"].is_object());
    assert!(bout.summary["report_retry_dda_actions_hex"].is_string());
}

// Origin: engine/crates_rs/tests/core_adversary/complete_bout_parity.rs
// Claim: urn:core:crates_rs:tests:complete-bout-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
