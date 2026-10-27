use core_adversary::stage::diagnostics::{SbeDiagnosticPort, SbeReport};
use core_adversary::stage::emission::{EmitterSuite, GenealogySink};
use core_adversary::stage::genealogy::{CemeteryHeadstone, GenealogyEntry};
use core_adversary::stage::packets::CandidateProposal;
use core_adversary::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
use core_adversary::bout_auxiliary::{
    execute_act3_epistemic_sieve, execute_act4_sandbox_verification, execute_act7_crystallization,
    CandidateContent, CrystallizationInput, EpistemicSieveInput,
};
use serde_json::{json, Value};
use std::cell::RefCell;
use std::rc::Rc;

fn refused(code: &str, message: &str) -> Refusal {
    let mut r = Refusal::new(code, message);
    r.locus = "fixture".into();
    r
}
struct Diagnostic {
    report: Value,
    calls: Rc<RefCell<Vec<Value>>>,
}
impl SbeDiagnosticPort for Diagnostic {
    fn compute(&mut self, text: &str, dim: usize) -> Result<SbeReport, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"sbe","text":text,"dim":dim}));
        SbeReport::from_json(&self.report)
    }
}
struct Seats {
    reply: SeatTurnReply,
    failed: bool,
    calls: Rc<RefCell<Vec<Value>>>,
}
impl SeatPort for Seats {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.calls.borrow_mut().push(
            json!({"sink":"seat","request":request,"request_digest":request.request_digest()?}),
        );
        if self.failed {
            Err(refused("FIXTURE_SEAT_REFUSED", "seat unavailable"))
        } else {
            Ok(self.reply.clone())
        }
    }
}
struct Genealogy {
    failed: bool,
    calls: Rc<RefCell<Vec<Value>>>,
}
impl GenealogySink for Genealogy {
    fn record_lineage(&mut self, entry: &GenealogyEntry) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"genealogy","entry":entry.to_dict()}));
        if self.failed {
            Err(refused(
                "FIXTURE_GENEALOGY_REFUSED",
                "genealogy unavailable",
            ))
        } else {
            Ok("recorded".into())
        }
    }
}
fn fixture() -> Result<Value, serde_json::Error> {
    serde_json::from_str(include_str!("fixtures/python_bout_auxiliary_v1.json"))
}
fn verify_sieve_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let input = &row["input"];
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut diagnostic = Diagnostic {
        report: input["report"].clone(),
        calls: calls.clone(),
    };
    let candidates: Vec<CandidateProposal> = serde_json::from_value(input["candidates"].clone())?;
    let data: Vec<CandidateContent<'_>> = input["data"]
        .as_array()
        .unwrap()
        .iter()
        .map(|item| CandidateContent {
            candidate_id: item["candidate_id"].as_str().unwrap(),
            content: item["content"].as_str().unwrap(),
        })
        .collect();
    let outcome = execute_act3_epistemic_sieve(
        &EpistemicSieveInput {
            objective: input["objective"].as_str().unwrap(),
            candidates: &candidates,
            candidates_data: &data,
        },
        &mut diagnostic,
    )?;
    assert_eq!(outcome.report().to_dict(), row["expected"]["ok"]["sieve_sbe"]);
    assert_eq!(outcome.narrative(), &row["expected"]["ok"]["narrative"]);
    assert_eq!(json!({"ok":outcome.to_dict()}), row["expected"], "sieve {index}");
    assert_eq!(json!(*calls.borrow()), row["calls"], "sieve trace {index}");
    Ok(())
}

#[test]
fn frozen_python_sieve_selection_order_and_injected_synthetic_report(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture = fixture()?;
    let rows = fixture["sieve"].as_array().ok_or("rows")?;
    assert_eq!(rows.len(), 60);
    for (index, row) in rows.iter().enumerate() {
        verify_sieve_row(index, row)?;
    }
    Ok(())
}
#[test]
fn frozen_python_unverified_sandbox_request_disposition_and_unicode_excerpt(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture = fixture()?;
    let rows = fixture["sandbox"].as_array().ok_or("rows")?;
    assert_eq!(rows.len(), 36);
    for (index, row) in rows.iter().enumerate() {
        let input = &row["input"];
        let calls = Rc::new(RefCell::new(Vec::new()));
        let mut seats = Seats {
            reply: serde_json::from_value(input["reply"].clone())?,
            failed: input["failed"] == 1,
            calls: calls.clone(),
        };
        let actual = match execute_act4_sandbox_verification(if input["port"] == true {
            Some(&mut seats)
        } else {
            None
        }) {
            Ok(outcome) => {
                assert_eq!(
                    outcome.disposition(),
                    row["expected"]["ok"]["disposition"]
                        .as_str()
                        .ok_or("disposition")?
                );
                assert_eq!(outcome.narrative(), &row["expected"]["ok"]["narrative"]);
                json!({"ok":outcome.to_dict()})
            }
            Err(error) => json!({"error":error}),
        };
        assert_eq!(actual, row["expected"], "sandbox {index}");
        assert_eq!(
            json!(*calls.borrow()),
            row["calls"],
            "sandbox trace {index}"
        );
    }
    Ok(())
}
fn verify_crystallization_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let input = &row["input"];
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut sink = Genealogy {
        failed: input["failed"] == true,
        calls: calls.clone(),
    };
    let mut suite = EmitterSuite {
        genealogy: (input["port"] == true).then_some(&mut sink),
        ..EmitterSuite::default()
    };
    let dead = input["dead"]
        .as_array()
        .unwrap()
        .iter()
        .map(CemeteryHeadstone::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    // v1 preserved the old compost label even for an accepted terminal.
    // Only this named diagnostic label changes in the post-live contract;
    // no genealogy or unrelated frozen fields are rewritten.
    let mut expected = row["expected"].clone();
    if input["verdict"] == "PASS_TO_MASTER" {
        expected["ok"]["consecration_state"] = json!("CHECKER_ACCEPTED");
        if let Some(body) = expected["ok"]["narrative"]["body"].as_str() {
            expected["ok"]["narrative"]["body"] =
                json!(body.replace("`COMPOSTED_WITH_REENTRY_GUIDANCE`", "`CHECKER_ACCEPTED`"));
        }
    }
    let actual = match execute_act7_crystallization(
        &CrystallizationInput {
            run_key: "aux_fixture",
            terminal_verdict: input["verdict"].as_str().unwrap(),
            request_external_admission: &input["external_admission"],
            dead_candidates: &dead,
        },
        Some(&mut suite),
    ) {
        Ok(outcome) => {
            assert_eq!(outcome.consecration_state(), expected["ok"]["consecration_state"].as_str().unwrap());
            assert_eq!(outcome.narrative(), &expected["ok"]["narrative"]);
            json!({"ok":outcome.to_dict()})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, expected, "crystallization {index}");
    assert_eq!(json!(*calls.borrow()), row["calls"], "crystallization trace {index}");
    Ok(())
}

#[test]
fn frozen_python_crystallization_non_authority_and_ordered_reentry_genealogy(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture = fixture()?;
    let rows = fixture["crystallization"].as_array().ok_or("rows")?;
    assert_eq!(rows.len(), 192);
    for (index, row) in rows.iter().enumerate() {
        verify_crystallization_row(index, row)?;
    }
    Ok(())
}

#[test]
fn postlive_checker_accepted_capture_never_emits_compost_genealogy(
) -> Result<(), Box<dyn std::error::Error>> {
    for external in [false, true] {
        let calls = Rc::new(RefCell::new(Vec::new()));
        // A failing sink makes any accidental invocation observable as an error.
        let mut sink = Genealogy {
            failed: true,
            calls: calls.clone(),
        };
        let mut suite = EmitterSuite {
            genealogy: Some(&mut sink),
            ..Default::default()
        };
        let outcome = execute_act7_crystallization(
            &CrystallizationInput {
                run_key: "postlive_accepted",
                terminal_verdict: "PASS_TO_MASTER",
                request_external_admission: &json!(external),
                dead_candidates: &[],
            },
            Some(&mut suite),
        )?;
        assert_eq!(outcome.consecration_state(), "CHECKER_ACCEPTED");
        assert!(calls.borrow().is_empty());
        assert!(outcome.narrative()["body"]
            .as_str()
            .unwrap()
            .contains("Non-authoritative"));
    }
    Ok(())
}

#[test]
fn postlive_compost_still_records_reentry_and_external_flag_cannot_relabel_it(
) -> Result<(), Box<dyn std::error::Error>> {
    for external in [false, true] {
        let calls = Rc::new(RefCell::new(Vec::new()));
        let mut sink = Genealogy {
            failed: false,
            calls: calls.clone(),
        };
        let mut suite = EmitterSuite {
            genealogy: Some(&mut sink),
            ..Default::default()
        };
        let outcome = execute_act7_crystallization(
            &CrystallizationInput {
                run_key: "postlive_compost",
                terminal_verdict: "COMPOSTED",
                request_external_admission: &json!(external),
                dead_candidates: &[],
            },
            Some(&mut suite),
        )?;
        assert_eq!(
            outcome.consecration_state(),
            "COMPOSTED_WITH_REENTRY_GUIDANCE"
        );
        let recorded = calls.borrow();
        assert_eq!(recorded.len(), 1);
        assert_eq!(
            recorded[0]["entry"]["re_entry_reason"],
            "COMPOST_GUIDED_MUTATION"
        );
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/bout_auxiliary_parity.rs
// Claim: urn:core:crates_rs:tests:bout-auxiliary-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
