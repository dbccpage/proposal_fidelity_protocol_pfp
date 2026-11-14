//! The failure ledger: a rule is loaded by a later run only after it earned it, and the chain cannot be edited.
//!
//! AuthorityEffect: None.

use pfp_operads::ledger::{Ledger, Record, Status, GENESIS};
use sha2::{Digest, Sha256};

type Edit = fn(&mut Record);

const HASH: &str = "9f86d081884c7d659a2feabfb4d6f2d0d7e2e6f2a4b5c6d7e8f9a0b1c2d3e4f5";

fn failure(id: &str) -> Record {
    Record::Failure {
        id: id.to_owned(),
        workflow: "WF2".to_owned(),
        run: "run-1".to_owned(),
        failure_class: "CounterfeitExactness".to_owned(),
        ddc_trace: "CRΛM".to_owned(),
        evidence_sha256: HASH.to_owned(),
    }
}

fn candidate(id: &str, from: &[&str]) -> Record {
    Record::Candidate {
        id: id.to_owned(),
        capability_kind: "antibody".to_owned(),
        constraint: "State the sign convention before integrating.".to_owned(),
        derived_from: from.iter().map(|s| (*s).to_owned()).collect(),
    }
}

fn trial(id: &str, held_out: &[&str], baseline: u32, treated: u32, hits: u32) -> Record {
    Record::Trial {
        candidate: id.to_owned(),
        held_out: held_out.iter().map(|s| (*s).to_owned()).collect(),
        baseline_correct: baseline,
        treated_correct: treated,
        clean_panel_hits: hits,
    }
}

fn admission(id: &str, trial: u64) -> Record {
    Record::Admission {
        candidate: id.to_owned(),
        trial,
    }
}

fn retirement(id: &str) -> Record {
    Record::Retirement {
        candidate: id.to_owned(),
        reason: "fired on clean work in WF9".to_owned(),
    }
}

/// f1, f2, candidate a1 from f1: three entries, seq 0..=2.
fn seeded() -> Ledger {
    let mut ledger = Ledger::new();
    ledger.append(failure("f1")).unwrap();
    ledger.append(failure("f2")).unwrap();
    ledger.append(candidate("a1", &["f1"])).unwrap();
    ledger
}

fn refused(ledger: &mut Ledger, record: Record) -> &'static str {
    let before = ledger.entries().len();
    let code = ledger.append(record).unwrap_err().code;
    assert_eq!(
        ledger.entries().len(),
        before,
        "a refused record must change nothing"
    );
    code
}

#[test]
fn statuses_are_the_canon_names() {
    let names: Vec<&str> = Status::ALL.iter().map(|status| status.as_str()).collect();
    let canon = core_operad_canon::type_by_id("antibody_pharmacy_status")
        .unwrap()
        .values;
    assert_eq!(names, canon);
}

#[test]
fn a_rule_is_loaded_only_after_it_wins_a_held_out_trial() {
    let mut ledger = seeded();
    assert_eq!(ledger.status("a1"), Some(Status::Candidate));
    assert!(ledger.admitted().is_empty());
    assert_eq!(refused(&mut ledger, admission("a1", 2)), "NOT_EARNED");
    let seq = ledger
        .append(trial("a1", &["h1", "h2", "h3"], 1, 3, 0))
        .unwrap()
        .seq;
    assert_eq!(seq, 3);
    assert_eq!(ledger.status("a1"), Some(Status::Candidate));
    assert_eq!(refused(&mut ledger, admission("a1", 2)), "NOT_EARNED");
    ledger.append(admission("a1", seq)).unwrap();
    assert_eq!(ledger.status("a1"), Some(Status::Admitted));
    let loaded = ledger.admitted();
    assert_eq!(loaded.len(), 1);
    assert_eq!(
        (loaded[0].id.as_str(), loaded[0].capability_kind.as_str()),
        ("a1", "antibody")
    );
    assert!(loaded[0].constraint.starts_with("State the sign"));
    assert_eq!(refused(&mut ledger, admission("a1", seq)), "NOT_EARNED");
    assert_eq!(ledger.status("nobody"), None);
}

#[test]
fn no_gain_or_a_hit_on_clean_work_rejects_and_a_retest_can_recover() {
    for (baseline, treated, hits) in [(2, 2, 0), (2, 1, 0), (1, 3, 1)] {
        let mut ledger = seeded();
        ledger
            .append(trial("a1", &["h1", "h2", "h3"], baseline, treated, hits))
            .unwrap();
        assert_eq!(ledger.status("a1"), Some(Status::Rejected));
        assert_eq!(refused(&mut ledger, admission("a1", 3)), "NOT_EARNED");
        ledger.append(trial("a1", &["h4", "h5"], 0, 1, 0)).unwrap();
        assert_eq!(ledger.status("a1"), Some(Status::Candidate));
        assert_eq!(refused(&mut ledger, admission("a1", 3)), "NOT_EARNED");
        ledger.append(admission("a1", 4)).unwrap();
        assert_eq!(ledger.admitted().len(), 1);
    }
}

#[test]
fn a_later_failed_trial_blocks_an_earlier_pass_and_leaves_an_admitted_rule_in_place() {
    let mut ledger = seeded();
    ledger.append(trial("a1", &["h1"], 0, 1, 0)).unwrap();
    ledger.append(trial("a1", &["h2"], 1, 1, 0)).unwrap();
    assert_eq!(refused(&mut ledger, admission("a1", 3)), "NOT_EARNED");
    assert_eq!(refused(&mut ledger, admission("a1", 4)), "NOT_EARNED");
    ledger.append(trial("a1", &["h3"], 0, 1, 0)).unwrap();
    ledger.append(admission("a1", 5)).unwrap();
    ledger.append(trial("a1", &["h4"], 1, 0, 2)).unwrap();
    assert_eq!(ledger.status("a1"), Some(Status::Admitted));
}

#[test]
fn retirement_unloads_a_rule_for_good() {
    let mut ledger = seeded();
    ledger.append(trial("a1", &["h1"], 0, 1, 0)).unwrap();
    ledger.append(admission("a1", 3)).unwrap();
    ledger.append(retirement("a1")).unwrap();
    assert_eq!(ledger.status("a1"), Some(Status::Retired));
    assert!(ledger.admitted().is_empty());
    assert_eq!(
        refused(&mut ledger, trial("a1", &["h2"], 0, 1, 0)),
        "RULE_RETIRED"
    );
    assert_eq!(refused(&mut ledger, admission("a1", 3)), "RULE_RETIRED");
    assert_eq!(refused(&mut ledger, retirement("a1")), "RULE_RETIRED");
    assert_eq!(
        refused(&mut ledger, retirement("ghost")),
        "UNKNOWN_CANDIDATE"
    );
    let blank = Record::Retirement {
        candidate: "a1".to_owned(),
        reason: " ".to_owned(),
    };
    assert_eq!(refused(&mut seeded(), blank), "EMPTY_FIELD");
}

#[test]
fn a_failure_must_be_typed_by_the_canon() {
    let mut ledger = seeded();
    assert_eq!(refused(&mut ledger, failure("f1")), "DUPLICATE_ID");
    let with = |edit: Edit| {
        let mut record = failure("f9");
        edit(&mut record);
        record
    };
    let cases: [(Edit, &str); 9] = [
        (
            |r| {
                if let Record::Failure { failure_class, .. } = r {
                    *failure_class = "Oops".into()
                }
            },
            "UNKNOWN_FAILURE_CLASS",
        ),
        (
            |r| {
                if let Record::Failure { ddc_trace, .. } = r {
                    *ddc_trace = "CXT".into()
                }
            },
            "BAD_DDC_TRACE",
        ),
        (
            |r| {
                if let Record::Failure { ddc_trace, .. } = r {
                    ddc_trace.clear()
                }
            },
            "BAD_DDC_TRACE",
        ),
        (
            |r| {
                if let Record::Failure {
                    evidence_sha256, ..
                } = r
                {
                    evidence_sha256.pop();
                }
            },
            "BAD_EVIDENCE_HASH",
        ),
        (
            |r| {
                if let Record::Failure {
                    evidence_sha256, ..
                } = r
                {
                    *evidence_sha256 = evidence_sha256.to_uppercase()
                }
            },
            "BAD_EVIDENCE_HASH",
        ),
        (
            |r| {
                if let Record::Failure {
                    evidence_sha256, ..
                } = r
                {
                    evidence_sha256.replace_range(0..1, "g")
                }
            },
            "BAD_EVIDENCE_HASH",
        ),
        (
            |r| {
                if let Record::Failure { id, .. } = r {
                    id.clear()
                }
            },
            "EMPTY_FIELD",
        ),
        (
            |r| {
                if let Record::Failure { workflow, .. } = r {
                    *workflow = "  ".into()
                }
            },
            "EMPTY_FIELD",
        ),
        (
            |r| {
                if let Record::Failure { run, .. } = r {
                    run.clear()
                }
            },
            "EMPTY_FIELD",
        ),
    ];
    for (edit, code) in cases {
        assert_eq!(refused(&mut ledger, with(edit)), code);
    }
    let pharmacy = with(|r| {
        if let Record::Failure { failure_class, .. } = r {
            *failure_class = "FAKE_RECEIPT".into()
        }
    });
    ledger.append(pharmacy).unwrap();
}

#[test]
fn a_candidate_must_come_from_recorded_failures() {
    let mut ledger = seeded();
    assert_eq!(
        refused(&mut ledger, candidate("a1", &["f2"])),
        "DUPLICATE_ID"
    );
    assert_eq!(
        refused(&mut ledger, candidate("a2", &["f3"])),
        "UNKNOWN_FAILURE"
    );
    assert_eq!(refused(&mut ledger, candidate("a2", &[])), "BAD_ID_LIST");
    assert_eq!(
        refused(&mut ledger, candidate("a2", &["f1", "f1"])),
        "BAD_ID_LIST"
    );
    assert_eq!(refused(&mut ledger, candidate("", &["f1"])), "EMPTY_FIELD");
    let mut odd = candidate("a2", &["f1"]);
    if let Record::Candidate {
        capability_kind, ..
    } = &mut odd
    {
        *capability_kind = "spell".to_owned();
    }
    assert_eq!(refused(&mut ledger, odd), "UNKNOWN_CAPABILITY_KIND");
    let mut blank = candidate("a2", &["f1"]);
    if let Record::Candidate { constraint, .. } = &mut blank {
        constraint.clear();
    }
    assert_eq!(refused(&mut ledger, blank), "EMPTY_FIELD");
    ledger.append(candidate("a2", &["f1", "f2"])).unwrap();
}

#[test]
fn a_trial_must_be_held_out_and_countable() {
    let mut ledger = seeded();
    assert_eq!(
        refused(&mut ledger, trial("a1", &["h1", "f1"], 0, 1, 0)),
        "SPLIT_OVERLAP"
    );
    assert_eq!(
        refused(&mut ledger, trial("a1", &[], 0, 0, 0)),
        "BAD_ID_LIST"
    );
    assert_eq!(
        refused(&mut ledger, trial("a1", &["h1", "h1"], 0, 1, 0)),
        "BAD_ID_LIST"
    );
    assert_eq!(
        refused(&mut ledger, trial("a1", &["h1"], 0, 2, 0)),
        "BAD_COUNT"
    );
    assert_eq!(
        refused(&mut ledger, trial("a1", &["h1"], 2, 0, 0)),
        "BAD_COUNT"
    );
    assert_eq!(
        refused(&mut ledger, trial("a9", &["h1"], 0, 1, 0)),
        "UNKNOWN_CANDIDATE"
    );
    ledger.append(trial("a1", &["f2", "h1"], 2, 2, 0)).unwrap();
}

#[test]
fn the_chain_replays_and_any_edit_breaks_it() {
    let mut ledger = seeded();
    ledger.append(trial("a1", &["h1"], 0, 1, 0)).unwrap();
    ledger.append(admission("a1", 3)).unwrap();
    assert_eq!(ledger.entries()[0].prev, GENESIS);
    assert_eq!(ledger.entries()[1].prev, ledger.entries()[0].hash);
    assert_ne!(ledger.entries()[1].hash, ledger.entries()[0].hash);
    let text = ledger.to_lines().unwrap();
    assert_eq!(text.lines().count(), 5);
    let replayed = Ledger::from_lines(&format!("\n{text}\n")).unwrap();
    assert_eq!(replayed.entries(), ledger.entries());
    assert_eq!(replayed.admitted(), ledger.admitted());
    assert!(Ledger::from_lines("").unwrap().entries().is_empty());

    let edited = text.replace("State the sign", "Ignore the sign");
    assert_eq!(
        Ledger::from_lines(&edited).unwrap_err().code,
        "CHAIN_BROKEN"
    );
    let renumbered = text.replacen("\"seq\":1", "\"seq\":7", 1);
    assert_eq!(
        Ledger::from_lines(&renumbered).unwrap_err().code,
        "CHAIN_BROKEN"
    );
    let relinked = text.replacen(GENESIS, HASH, 1);
    assert_eq!(
        Ledger::from_lines(&relinked).unwrap_err().code,
        "CHAIN_BROKEN"
    );
    let lines: Vec<&str> = text.lines().collect();
    let dropped = [lines[0], lines[2], lines[3], lines[4]].join("\n");
    assert!(Ledger::from_lines(&dropped).is_err());
    let swapped = [lines[1], lines[0]].join("\n");
    assert_eq!(
        Ledger::from_lines(&swapped).unwrap_err().code,
        "CHAIN_BROKEN"
    );
    assert_eq!(
        Ledger::from_lines("{\"seq\":0}").unwrap_err().code,
        "BAD_ENTRY"
    );
    let extra = lines[0].replacen("{\"seq\"", "{\"note\":1,\"seq\"", 1);
    assert_eq!(Ledger::from_lines(&extra).unwrap_err().code, "BAD_ENTRY");
}

#[test]
fn the_same_records_always_hash_the_same() {
    let first = seeded().to_lines().unwrap();
    assert_eq!(first, seeded().to_lines().unwrap());
    let mut other = Ledger::new();
    other.append(failure("f2")).unwrap();
    assert_ne!(other.entries()[0].hash, seeded().entries()[0].hash);
    assert_eq!(seeded().entries()[0].hash.len(), 64);
}

#[test]
fn the_hash_covers_the_domain_line_seq_prev_and_record() {
    let record = format!(
        "{{\"kind\":\"failure\",\"id\":\"f1\",\"workflow\":\"WF2\",\"run\":\"run-1\",\
         \"failure_class\":\"CounterfeitExactness\",\"ddc_trace\":\"CRΛM\",\"evidence_sha256\":\"{HASH}\"}}"
    );
    let body = format!("pfp.operads.ledger.v1\n[0,\"{GENESIS}\",{record}]");
    let by_hand = hex::encode(Sha256::digest(body.as_bytes()));
    assert_eq!(seeded().entries()[0].hash, by_hand);
}
