//! Stored model turns, read and judged by the host: failures from runs, trials from fair pairs.
//!
//! AuthorityEffect: None.

use pfp_operads::ledger::{Ledger, Record, Status, GENESIS};
use pfp_operads::loading::load;
use pfp_operads::turns::{trial_turns, witness_turn, CASE_DIGITS};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const SEED: &str = "Add every integer in input.values.";

fn sha256(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// A turn folder's two files, with the extra fields a real run keeps.
fn turn(values: Value, answer: Value, seed: &str) -> Value {
    json!({
        "task": {
            "task_id": "sum-1", "checker": "integer_sum_v1", "seed_prompt": seed,
            "input": {"values": values}, "answer_schema": {"type": "object"}
        },
        "receipt": {
            "workflow_id": "WF2", "status": "PROVIDER_COMPLETED", "version": "0.2.0",
            "check": {"answer": answer, "schema_valid": true, "status": "PROVIDER_COMPLETED"}
        }
    })
}

fn total(n: i64) -> Value {
    json!({"total": n})
}

fn witnessed(turn: &Value) -> Result<Value, &'static str> {
    witness_turn(&json!({"run": "run-7/agent-2", "turn": turn}).to_string())
        .map(|found| serde_json::to_value(found.record).expect("encodes"))
        .map_err(|refusal| refusal.code)
}

fn case_name(values: &str) -> String {
    let digest = sha256(&format!("pfp.operads.case.v1\ninteger_sum_v1\n{values}"));
    format!("c{}", &digest[..CASE_DIGITS])
}

#[test]
fn a_stored_turn_the_judge_rejects_becomes_a_failure_named_after_its_case() {
    let record = witnessed(&turn(json!([17, 25, -4]), total(46), SEED)).expect("a failure");
    let evidence = sha256(
        "pfp.operads.failure-evidence.v1\ninteger_sum_v1\n{\"values\":[17,25,-4]}\n{\"total\":46}\n",
    );
    assert_eq!(
        record,
        json!({
            "kind": "failure",
            "id": format!("{}@run-7/agent-2", case_name("17,25,-4,")),
            "workflow": "WF2",
            "run": "run-7/agent-2",
            "failure_class": "CounterfeitExactness",
            "ddc_trace": "M",
            "evidence_sha256": evidence
        })
    );
    assert_eq!(CASE_DIGITS, 16);
    Ledger::new()
        .append(serde_json::from_value(record).expect("typed"))
        .expect("the ledger takes the record");
}

#[test]
fn a_case_is_named_by_its_checker_and_integers_not_by_how_they_are_written() {
    let id = |text: &str| {
        let request = format!(
            r#"{{"run":"r","turn":{{"task":{{"checker":"integer_sum_v1","seed_prompt":"s","input":{text}}},"receipt":{{"workflow_id":"WF1","check":{{"answer":{{"total":99}}}}}}}}}}"#
        );
        let record = serde_json::to_value(witness_turn(&request).expect("a failure").record);
        record.unwrap()["id"].as_str().unwrap().to_owned()
    };
    let base = id(r#"{"values":[1,2]}"#);
    assert_eq!(base, format!("{}@r", case_name("1,2,")));
    assert_eq!(base, id(r#"{ "values" : [ 1 , 2 ] }"#));
    assert_ne!(base, id(r#"{"values":[2,1]}"#));
    assert_ne!(base, id(r#"{"values":[12]}"#));
    assert_ne!(base, id(r#"{"values":[1,2,0]}"#));
}

#[test]
fn a_full_slot_reply_is_judged_on_its_task_result_and_keeps_its_ddc_word() {
    let envelope = |result: Value| {
        json!({
            "task_result": result,
            "slot_report": [],
            "ddc_moves": [{"id": "t1", "op": "C"}, {"id": "t2", "op": "T", "refusal": null}]
        })
    };
    let record =
        witnessed(&turn(json!([17, 25, -4]), envelope(total(39)), SEED)).expect("a failure");
    assert_eq!(record["ddc_trace"], "CTM");
    let stored = envelope(total(39)).to_string();
    assert_eq!(
        record["evidence_sha256"],
        sha256(&format!(
            "pfp.operads.failure-evidence.v1\ninteger_sum_v1\n{{\"values\":[17,25,-4]}}\n{stored}\n"
        ))
    );
    // A right task result is not a failure, whatever else the envelope holds.
    assert_eq!(
        witnessed(&turn(json!([17, 25, -4]), envelope(total(38)), SEED)),
        Err("NOT_A_FAILURE")
    );
    // An envelope without a task result is judged as written, and has no total.
    let bare = json!({"ddc_moves": [{"op": "R"}], "note": "no result"});
    assert_eq!(
        witnessed(&turn(json!([1]), bare, SEED)).unwrap()["ddc_trace"],
        "RM"
    );
    // The ledger, not the reader, decides whether the word is lawful.
    let unlawful = json!({"task_result": total(0), "ddc_moves": [{"op": "X"}]});
    let record = witnessed(&turn(json!([1]), unlawful, SEED)).unwrap();
    assert_eq!(record["ddc_trace"], "XM");
    assert_eq!(
        Ledger::new()
            .append(serde_json::from_value(record).unwrap())
            .unwrap_err()
            .code,
        "BAD_DDC_TRACE"
    );
}

#[test]
fn an_answer_that_is_not_an_object_is_judged_as_written() {
    for answer in [json!(38), json!("38"), json!([38])] {
        let record = witnessed(&turn(json!([17, 25, -4]), answer, SEED)).expect("a failure");
        assert_eq!(record["ddc_trace"], "M");
    }
}

#[test]
fn a_turn_the_host_cannot_judge_is_refused() {
    let good = turn(json!([1, 2]), total(4), SEED);
    assert_eq!(
        witnessed(&turn(json!([1, 2]), total(3), SEED)),
        Err("NOT_A_FAILURE")
    );
    let mut silent = good.clone();
    silent["receipt"]["check"] = json!({"schema_valid": false});
    assert_eq!(witnessed(&silent), Err("NO_ANSWER"));
    silent["receipt"]["check"] = json!({"answer": null});
    assert_eq!(witnessed(&silent), Err("NO_ANSWER"));
    silent["receipt"].as_object_mut().unwrap().remove("check");
    assert_eq!(witnessed(&silent), Err("NO_ANSWER"));
    let mut mining = good.clone();
    mining["task"]["checker"] = json!("schema_only");
    assert_eq!(witnessed(&mining), Err("UNKNOWN_CHECKER"));
    let mut broken = good.clone();
    broken["task"]["input"] = json!({"values": [1, 2.5]});
    assert_eq!(witnessed(&broken), Err("BAD_CASE"));
    let moves = json!({"task_result": total(4), "ddc_moves": "CT"});
    assert_eq!(
        witnessed(&turn(json!([1, 2]), moves, SEED)),
        Err("BAD_TURN")
    );
    let mut open = good.clone();
    open["verdict"] = json!("wrong");
    assert_eq!(witnessed(&open), Err("BAD_REQUEST"));
    let mut anonymous = good.clone();
    anonymous["receipt"]
        .as_object_mut()
        .unwrap()
        .remove("workflow_id");
    assert_eq!(witnessed(&anonymous), Err("BAD_REQUEST"));
    let code = |request: Value| witness_turn(&request.to_string()).unwrap_err().code;
    assert_eq!(code(json!({"turn": good})), "BAD_REQUEST");
    assert_eq!(
        code(json!({"run": "r", "turn": good, "failure_class": "ToyPromotion"})),
        "BAD_REQUEST"
    );
}

fn record(value: Value) -> Record {
    serde_json::from_value(value).expect("a ledger record")
}

/// A ledger with one witnessed failure on `[9, -2]` and the rule `sign` proposed from it.
fn proposed() -> Ledger {
    let mut ledger = Ledger::new();
    let failure = witnessed(&turn(json!([9, -2]), total(11), SEED)).expect("a failure");
    let id = failure["id"].clone();
    ledger.append(record(failure)).expect("a failure");
    ledger
        .append(record(json!({
            "kind": "candidate", "id": "sign", "capability_kind": "antibody",
            "constraint": "Keep the sign of every value.", "derived_from": [id]
        })))
        .expect("a candidate");
    ledger
}

fn text(ledger: &Ledger) -> String {
    ledger.to_lines().expect("lines")
}

fn seed(ledger: &Ledger, on_trial: Option<&str>) -> String {
    let request = match on_trial {
        Some(id) => json!({"seed_prompt": SEED, "on_trial": id}),
        None => json!({"seed_prompt": SEED}),
    };
    load(&text(ledger), &request.to_string())
        .expect("loaded")
        .seed_prompt
}

/// One held-out pair, loaded from the ledger as it stands: the baseline, then the rule on trial.
fn pair(ledger: &Ledger, values: Value, baseline: Value, treated: Value) -> Value {
    json!({
        "baseline": turn(values.clone(), baseline, &seed(ledger, None)),
        "treated": turn(values, treated, &seed(ledger, Some("sign"))),
        "base_seed_prompt": SEED,
        "ledger_head": ledger.head()
    })
}

fn scored(ledger: &Ledger, cases: Value) -> Result<Value, &'static str> {
    trial_turns(
        &text(ledger),
        &json!({"candidate": "sign", "cases": cases}).to_string(),
    )
    .map(|scored| serde_json::to_value(scored).expect("encodes"))
    .map_err(|refusal| refusal.code)
}

#[test]
fn a_rule_is_admitted_on_a_trial_the_host_scored_from_fair_pairs() {
    let mut ledger = proposed();
    let report = scored(
        &ledger,
        json!([
            pair(&ledger, json!([8, -3]), total(11), total(5)),
            pair(&ledger, json!([-7, 2, -1]), total(10), total(-6)),
            pair(&ledger, json!([3, 8]), total(11), total(11))
        ]),
    )
    .expect("scored");
    assert_eq!(
        report["record"],
        json!({
            "kind": "trial",
            "candidate": "sign",
            "held_out": [case_name("8,-3,"), case_name("-7,2,-1,"), case_name("3,8,")],
            "baseline_correct": 1,
            "treated_correct": 3,
            "clean_panel_hits": 0
        })
    );
    assert_eq!(
        report["cases"][0],
        json!({"id": case_name("8,-3,"), "baseline": false, "treated": true})
    );
    let seq = ledger
        .append(record(report["record"].clone()))
        .expect("a trial")
        .seq;
    ledger
        .append(record(
            json!({"kind": "admission", "candidate": "sign", "trial": seq}),
        ))
        .expect("earned");
    assert_eq!(ledger.status("sign"), Some(Status::Admitted));
    assert!(seed(&ledger, None).ends_with("- [sign] Keep the sign of every value.\n"));
}

#[test]
fn a_turn_without_an_answer_is_wrong_and_a_broken_clean_case_is_counted() {
    let ledger = proposed();
    let mut silent = pair(&ledger, json!([8, -3]), total(5), total(5));
    silent["treated"]["receipt"]["check"] = json!({});
    let report = scored(
        &ledger,
        json!([
            silent,
            pair(&ledger, json!([3, 8]), total(11), total(12)),
            pair(
                &ledger,
                json!([1, 1]),
                json!({"task_result": total(2)}),
                total(2)
            )
        ]),
    )
    .expect("scored");
    assert_eq!(report["record"]["baseline_correct"], 3);
    assert_eq!(report["record"]["treated_correct"], 1);
    assert_eq!(report["record"]["clean_panel_hits"], 2);
}

#[test]
fn a_trial_on_the_case_the_rule_came_from_is_refused_by_the_ledger() {
    let mut ledger = proposed();
    // Same integers under another run and another task id: still the same case.
    let report = scored(
        &ledger,
        json!([pair(&ledger, json!([9, -2]), total(11), total(7))]),
    )
    .expect("scored");
    assert_eq!(report["record"]["held_out"], json!([case_name("9,-2,")]));
    assert_eq!(
        ledger
            .append(record(report["record"].clone()))
            .unwrap_err()
            .code,
        "SPLIT_OVERLAP"
    );
    // The same held-out case twice is one case.
    let twice = scored(
        &ledger,
        json!([
            pair(&ledger, json!([8, -3]), total(11), total(5)),
            pair(&ledger, json!([8, -3]), total(11), total(5))
        ]),
    )
    .expect("scored");
    assert_eq!(
        ledger
            .append(record(twice["record"].clone()))
            .unwrap_err()
            .code,
        "BAD_ID_LIST"
    );
}

#[test]
fn a_pair_that_is_not_fair_is_refused() {
    let ledger = proposed();
    let fair = pair(&ledger, json!([8, -3]), total(11), total(5));
    let one = |case: Value| scored(&ledger, json!([case]));
    let mut other_case = fair.clone();
    other_case["treated"]["task"]["input"] = json!({"values": [8, 3]});
    assert_eq!(one(other_case), Err("PAIR_MISMATCH"));
    // Both arms with the rule, or both without it, are not a trial of the rule.
    let mut both = fair.clone();
    both["baseline"]["task"]["seed_prompt"] = fair["treated"]["task"]["seed_prompt"].clone();
    assert_eq!(one(both), Err("BASELINE_SEED_MISMATCH"));
    let mut neither = fair.clone();
    neither["treated"]["task"]["seed_prompt"] = json!(SEED);
    assert_eq!(one(neither), Err("TREATED_SEED_MISMATCH"));
    let mut reworded = fair.clone();
    reworded["treated"]["task"]["seed_prompt"] = json!(format!(
        "{} Answer 5.",
        fair["treated"]["task"]["seed_prompt"].as_str().unwrap()
    ));
    assert_eq!(one(reworded), Err("TREATED_SEED_MISMATCH"));
    let mut other_base = fair.clone();
    other_base["base_seed_prompt"] = json!("Another task.");
    assert_eq!(one(other_base), Err("BASELINE_SEED_MISMATCH"));
    let mut nowhere = fair.clone();
    nowhere["ledger_head"] = json!(sha256("nowhere"));
    assert_eq!(one(nowhere), Err("UNKNOWN_LEDGER_HEAD"));
    // Before the rule was proposed there was nothing to try.
    let mut early = fair.clone();
    early["ledger_head"] = json!(GENESIS);
    assert_eq!(one(early), Err("UNKNOWN_CANDIDATE"));
    let mut mining = fair.clone();
    mining["baseline"]["task"]["checker"] = json!("schema_only");
    assert_eq!(one(mining), Err("UNKNOWN_CHECKER"));
    let mut other_checker = fair.clone();
    other_checker["treated"]["task"]["checker"] = json!("schema_only");
    assert_eq!(one(other_checker), Err("UNKNOWN_CHECKER"));
    let mut open = fair.clone();
    open["treated_correct"] = json!(true);
    assert_eq!(one(open), Err("BAD_REQUEST"));
    assert_eq!(
        one(fair),
        scored(
            &ledger,
            json!([pair(&ledger, json!([8, -3]), total(11), total(5))])
        )
    );
}

#[test]
fn the_baseline_carries_the_admitted_rules_and_an_admitted_rule_is_not_retried() {
    let mut ledger = proposed();
    let report = scored(
        &ledger,
        json!([pair(&ledger, json!([8, -3]), total(11), total(5))]),
    )
    .unwrap();
    let seq = ledger.append(record(report["record"].clone())).unwrap().seq;
    let stale = pair(&ledger, json!([4, -4]), total(8), total(0));
    ledger
        .append(record(
            json!({"kind": "admission", "candidate": "sign", "trial": seq}),
        ))
        .unwrap();
    // Loaded before the admission, the pair still stands at that ledger state.
    assert!(scored(&ledger, json!([stale.clone()])).is_ok());
    // At the new state the old baseline lacks the admitted rule, and the rule cannot be on trial.
    let mut moved = stale.clone();
    moved["ledger_head"] = json!(ledger.head());
    assert_eq!(
        scored(&ledger, json!([moved.clone()])),
        Err("BASELINE_SEED_MISMATCH")
    );
    moved["baseline"]["task"]["seed_prompt"] = json!(seed(&ledger, None));
    assert_eq!(scored(&ledger, json!([moved])), Err("NOT_ON_TRIAL"));
    // A second rule is tried against a baseline that already carries the first.
    let failure = ledger.entries()[0].record.clone();
    let Record::Failure { id, .. } = failure else {
        panic!("the first entry is the failure");
    };
    ledger
        .append(record(json!({
            "kind": "candidate", "id": "order", "capability_kind": "antibody",
            "constraint": "Add left to right.", "derived_from": [id]
        })))
        .unwrap();
    let request = |baseline_seed: String| {
        json!({"candidate": "order", "cases": [{
            "baseline": turn(json!([4, -4]), total(0), &baseline_seed),
            "treated": turn(json!([4, -4]), total(0), &load(
                &text(&ledger),
                &json!({"seed_prompt": SEED, "on_trial": "order"}).to_string()
            ).unwrap().seed_prompt),
            "base_seed_prompt": SEED,
            "ledger_head": ledger.head()
        }]})
        .to_string()
    };
    assert!(trial_turns(&text(&ledger), &request(seed(&ledger, None))).is_ok());
    assert_eq!(
        trial_turns(&text(&ledger), &request(SEED.to_owned()))
            .unwrap_err()
            .code,
        "BASELINE_SEED_MISMATCH"
    );
}

#[test]
fn an_edited_ledger_or_an_open_request_is_refused() {
    let ledger = proposed();
    let case = pair(&ledger, json!([8, -3]), total(11), total(5));
    let request = json!({"candidate": "sign", "cases": [case]});
    assert_eq!(
        trial_turns(
            &text(&ledger).replace("Keep the sign", "Drop the sign"),
            &request.to_string()
        )
        .unwrap_err()
        .code,
        "CHAIN_BROKEN"
    );
    let mut counted = request.clone();
    counted["treated_correct"] = json!(1);
    assert_eq!(
        trial_turns(&text(&ledger), &counted.to_string())
            .unwrap_err()
            .code,
        "BAD_REQUEST"
    );
    assert_eq!(
        scored(&ledger, json!([])).map(|report| report["record"]["held_out"].clone()),
        Ok(json!([]))
    );
}
