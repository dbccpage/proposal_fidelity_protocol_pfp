//! WF17, witnessed-difference programme: separating formulas, bisimulation certificates, and
//! the claims that carry neither.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf17-tests:v1

use pfp_operads::families::wf17::{FAMILY, MAX_DEPTH, MAX_TRANSITIONS};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str =
    "Claim differences with a separating formula and equivalences with a bisimulation.";

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF17", "task": task, "replies": replies}).to_string()
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

/// The report of a finished run, and whether the host passed it.
fn run(task: &Value, replies: Vec<Value>) -> (bool, Value) {
    match judge(&request(task, &all(replies))) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

/// The next question of a run that is not finished.
fn ask(task: &Value, replies: Vec<Value>) -> Value {
    match next(&request(task, &all(replies))) {
        Outcome::Pass { result } => result["ask"].clone(),
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn bad_task(task: Value) -> String {
    match next(&request(&task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

/// The reason of a run refused because a reply could not be read.
fn malformed(task: &Value, replies: Vec<Value>) -> String {
    let (passed, report) = run(task, replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

/// The predicates of a report as name and outcome, in the order they were recorded.
fn outcomes(report: &Value) -> Vec<(&str, bool)> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| {
            (
                row["name"].as_str().expect("a name"),
                row["passed"].as_bool().expect("an outcome"),
            )
        })
        .collect()
}

/// The digest of the evidence recorded under a predicate.
fn evidence<'r>(report: &'r Value, name: &str) -> &'r Value {
    let rows = report["predicates"].as_array().expect("predicates");
    let row = rows.iter().find(|row| row["name"] == name);
    &row.unwrap_or_else(|| panic!("no predicate {name}"))["evidence_sha256"]
}

/// Four small machines. From p0, `a` leads to one state that offers both `b` and `c`. From q0,
/// `a` leads either to a state that offers `b` or to one that offers `c`. r0 and s0 both do `a`
/// then `b`, and s0 has two ways of doing it.
fn task() -> Value {
    json!({
        "statement": STATEMENT,
        "transitions": [
            ["p0", "a", "p1"], ["p1", "b", "p2"], ["p1", "c", "p3"],
            ["q0", "a", "q1"], ["q0", "a", "q2"], ["q1", "b", "q3"], ["q2", "c", "q4"],
            ["r0", "a", "r1"], ["r1", "b", "r2"],
            ["s0", "a", "s1"], ["s0", "a", "s2"], ["s1", "b", "s3"], ["s2", "b", "s4"],
        ],
    })
}

fn prompt() -> String {
    format!(
        "WF17 Witnessed-difference programme. {STATEMENT}\n{}",
        concat!(
            r#"{"transitions":[["p0","a","p1"],["p1","b","p2"],["p1","c","p3"],"#,
            r#"["q0","a","q1"],["q0","a","q2"],["q1","b","q3"],["q2","c","q4"],"#,
            r#"["r0","a","r1"],["r1","b","r2"],"#,
            r#"["s0","a","s1"],["s0","a","s2"],["s1","b","s3"],["s2","b","s4"]]}"#
        )
    )
}

fn difference(left: &str, right: &str, witness: Value) -> Value {
    json!({"kind": "difference", "left": left, "right": right, "witness": witness})
}

fn equivalence(left: &str, right: &str, certificate: Value) -> Value {
    json!({"kind": "equivalence", "left": left, "right": right, "certificate": certificate})
}

/// After `a`, some state offers both `b` and `c`: true at p0 and false at q0.
fn both_offered() -> Value {
    json!(["dia", "a", ["and", ["dia", "b", "tt"], ["dia", "c", "tt"]]])
}

fn apart() -> Value {
    difference("p0", "q0", both_offered())
}

fn alike() -> Value {
    equivalence(
        "r0",
        "s0",
        json!([
            ["r0", "s0"],
            ["r1", "s1"],
            ["r1", "s2"],
            ["r2", "s3"],
            ["r2", "s4"]
        ]),
    )
}

fn claims(listed: Vec<Value>) -> Value {
    json!({ "claims": listed })
}

/// The outcome of the last predicate recorded for one claim on the four machines.
fn last(claim: Value) -> (String, bool) {
    last_on(&task(), claim)
}

fn last_on(task: &Value, claim: Value) -> (String, bool) {
    let (_, report) = run(task, vec![claims(vec![claim])]);
    let (name, passed) = *outcomes(&report).last().expect("a predicate");
    (name.to_owned(), passed)
}

/// Whether a formula is recorded as separating two states.
fn separates(left: &str, right: &str, witness: Value) -> bool {
    let (name, passed) = last(difference(left, right, witness));
    assert_eq!(name, "claim0:separates");
    passed
}

/// Whether a certificate is recorded as a bisimulation for two states of a task.
fn bisimilar(task: &Value, left: &str, right: &str, certificate: Value) -> bool {
    let (name, passed) = last_on(task, equivalence(left, right, certificate));
    assert_eq!(name, "claim0:bisimulation");
    passed
}

/// `tt` under this many `not`s.
fn negated(times: usize) -> Value {
    (0..times).fold(json!("tt"), |inner, _| json!(["not", inner]))
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF17",
            "Witnessed-difference programme",
            "hml_separator_bisimulation_check"
        )
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt());
    assert_eq!(first["prompt_sha256"], sha(&prompt()));
    assert_eq!(ask(&task(), vec![claims(vec![apart()])]), Value::Null);
}

#[test]
fn a_witnessed_difference_and_a_certified_equivalence_are_certified() {
    let (passed, report) = run(&task(), vec![claims(vec![apart(), alike()])]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CLAIMS_WITNESSED");
    assert_eq!(report["detail"], json!({"claims": 2}));
    assert_eq!(
        outcomes(&report),
        [
            ("claim0:states_declared", true),
            ("claim0:witnessed", true),
            ("claim0:separates", true),
            ("claim1:states_declared", true),
            ("claim1:witnessed", true),
            ("claim1:bisimulation", true),
        ]
    );
    let first = concat!(
        r#"{"kind":"difference","left":"p0","right":"q0","#,
        r#""witness":["dia","a",["and",["dia","b","tt"],["dia","c","tt"]]]}"#
    );
    for name in ["states_declared", "witnessed", "separates"] {
        assert_eq!(
            evidence(&report, &format!("claim0:{name}")),
            &json!(sha(first)),
            "{name}"
        );
    }
    let second = concat!(
        r#"{"certificate":[["r0","s0"],["r1","s1"],["r1","s2"],["r2","s3"],["r2","s4"]],"#,
        r#""kind":"equivalence","left":"r0","right":"s0"}"#
    );
    assert_eq!(
        evidence(&report, "claim1:bisimulation"),
        &json!(sha(second))
    );
}

#[test]
fn the_constants_hold_everywhere_and_nowhere() {
    // p0 can do `a` and p2 can do nothing.
    assert!(separates("p0", "p2", json!(["dia", "a", "tt"])));
    assert!(!separates("p0", "p2", json!(["dia", "a", "ff"])));
    assert!(separates("p0", "p2", json!(["box", "a", "ff"])));
    assert!(!separates("p0", "p2", json!(["box", "a", "tt"])));
    assert!(!separates("p0", "p2", json!("tt")));
    assert!(!separates("p0", "p2", json!("ff")));
}

#[test]
fn not_and_and_or_are_read_as_written() {
    let does_a = json!(["dia", "a", "tt"]);
    let does_b = json!(["dia", "b", "tt"]);
    assert!(separates("p0", "p2", json!(["not", does_a])));
    // A formula and its negation never hold together, and one of them always holds.
    assert!(!separates(
        "p0",
        "p2",
        json!(["and", ["not", does_a], does_a])
    ));
    assert!(!separates(
        "p0",
        "p2",
        json!(["or", ["not", does_a], does_a])
    ));
    // p0 does `a` only, p1 does `b` only, and p2 does neither.
    assert!(!separates("p0", "p2", json!(["and", does_a, does_b])));
    assert!(separates("p0", "p2", json!(["or", does_a, does_b])));
    assert!(separates("p1", "p2", json!(["or", does_a, does_b])));
    assert!(!separates("p0", "p1", json!(["or", does_a, does_b])));
    assert!(separates(
        "p0",
        "p1",
        json!(["and", does_a, ["not", does_b]])
    ));
    assert!(separates(
        "p0",
        "p1",
        json!(["and", ["not", does_b], does_a])
    ));
}

#[test]
fn dia_asks_for_some_move_and_box_for_every_move() {
    let then_b = |operator: &str| json!([operator, "a", ["dia", "b", "tt"]]);
    // Both can do `a` and then `b`, but only p0 must be able to do `b` after `a`.
    assert!(!separates("p0", "q0", then_b("dia")));
    assert!(separates("p0", "q0", then_b("box")));
    // The moves counted are the ones with the label named, out of the state asked about.
    assert!(separates("p0", "p1", json!(["dia", "b", "tt"])));
    assert!(separates("p1", "p2", json!(["dia", "b", "tt"])));
    assert!(!separates("p2", "p3", json!(["dia", "b", "tt"])));
    assert!(separates("p1", "q1", json!(["dia", "c", "tt"])));
    assert!(!separates("p1", "q1", json!(["dia", "b", "tt"])));
    assert!(separates("p1", "q1", json!(["box", "c", "ff"])));
    assert!(!separates("p1", "q1", json!(["box", "b", "ff"])));
    // A label no move carries: `dia` holds nowhere and `box` everywhere.
    assert!(!separates("p0", "p2", json!(["dia", "z", "tt"])));
    assert!(!separates("p0", "p2", json!(["box", "z", "ff"])));
}

#[test]
fn a_formula_that_holds_at_both_states_or_at_neither_is_refused() {
    let weak = difference("p0", "q0", json!(["dia", "a", ["dia", "b", "tt"]]));
    let (passed, report) = run(&task(), vec![claims(vec![weak])]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "CLAIM0:SEPARATES");
    assert_eq!(
        report["detail"],
        json!({"failed": ["claim0:separates"], "claims": 1})
    );
    assert!(!separates("p0", "p0", both_offered()));
    assert!(separates("q0", "p0", both_offered()));
}

#[test]
fn a_claim_about_a_state_no_transition_names_is_refused() {
    for (left, right) in [
        (json!("p0"), json!("zz")),
        (json!("zz"), json!("p0")),
        (json!("p0"), json!(5)),
        (json!(["p0"]), json!("q0")),
        (json!(null), json!("q0")),
    ] {
        let claim = json!({"kind": "difference", "left": left, "right": right, "witness": "tt"});
        let (passed, report) = run(&task(), vec![claims(vec![claim.clone()])]);
        assert!(!passed, "{claim}");
        assert_eq!(report["code"], "CLAIM0:STATES_DECLARED");
        assert_eq!(outcomes(&report), [("claim0:states_declared", false)]);
    }
    let bare = json!({"kind": "equivalence", "left": "p0"});
    assert_eq!(last(bare), ("claim0:states_declared".to_owned(), false));
    // A state that is only ever arrived at is declared.
    assert!(separates("p3", "p1", json!(["dia", "b", "tt"])));
}

#[test]
fn a_claim_without_its_kind_of_witness_is_refused() {
    let unwitnessed = |claim: Value| {
        let (passed, report) = run(&task(), vec![claims(vec![claim.clone()])]);
        assert!(!passed, "{claim}");
        assert_eq!(report["code"], "CLAIM0:WITNESSED", "{claim}");
        assert_eq!(
            outcomes(&report),
            [
                ("claim0:states_declared", true),
                ("claim0:witnessed", false)
            ]
        );
    };
    unwitnessed(json!({"kind": "difference", "left": "p0", "right": "q0"}));
    unwitnessed(json!({"kind": "difference", "left": "p0", "right": "q0", "certificate": []}));
    unwitnessed(json!({"kind": "equivalence", "left": "r0", "right": "s0"}));
    unwitnessed(json!({"kind": "equivalence", "left": "r0", "right": "s0", "witness": "tt"}));
    unwitnessed(equivalence("r0", "s0", json!("r0s0")));
    unwitnessed(equivalence("r0", "s0", json!({"r0": "s0"})));
    unwitnessed(equivalence("r0", "s0", json!(null)));
}

#[test]
fn a_relation_that_is_not_a_bisimulation_is_refused() {
    let fake = equivalence(
        "p0",
        "q0",
        json!([
            ["p0", "q0"],
            ["p1", "q1"],
            ["p1", "q2"],
            ["p2", "q3"],
            ["p3", "q4"]
        ]),
    );
    let (passed, report) = run(&task(), vec![claims(vec![fake])]);
    assert!(!passed);
    assert_eq!(report["code"], "CLAIM0:BISIMULATION");
    assert_eq!(
        outcomes(&report),
        [
            ("claim0:states_declared", true),
            ("claim0:witnessed", true),
            ("claim0:bisimulation", false),
        ]
    );
}

#[test]
fn a_certificate_must_hold_the_claimed_pair() {
    let rest = json!([["r1", "s1"], ["r1", "s2"], ["r2", "s3"], ["r2", "s4"]]);
    assert!(!bisimilar(&task(), "r0", "s0", rest));
    assert!(!bisimilar(&task(), "r0", "s0", json!([])));
    // The pair is ordered: the certificate for (r0, s0) is not one for (s0, r0).
    let (_, forward) = last(alike());
    assert!(forward);
    let mut turned = alike();
    turned["left"] = json!("s0");
    turned["right"] = json!("r0");
    assert_eq!(last(turned), ("claim0:bisimulation".to_owned(), false));
    // A state is bisimilar to itself by the identity on what it reaches.
    let same = json!([["r0", "r0"], ["r1", "r1"], ["r2", "r2"]]);
    assert!(bisimilar(&task(), "r0", "r0", same));
}

#[test]
fn a_certificate_must_be_distinct_pairs_of_declared_states() {
    let with = |extra: Value| {
        let mut claim = alike();
        claim["certificate"]
            .as_array_mut()
            .expect("a list")
            .push(extra);
        last(claim).1
    };
    // Two states that do nothing are bisimilar, so this pair changes nothing.
    assert!(with(json!(["p2", "p3"])));
    for extra in [
        json!(["r0", "s0"]),
        json!(["zz", "p2"]),
        json!(["p2", "zz"]),
        json!(["p2"]),
        json!(["p2", "p3", "p2"]),
        json!("p2p3"),
        json!(["p2", 5]),
        json!([null, "p3"]),
    ] {
        assert!(!with(extra.clone()), "{extra}");
    }
}

/// L does `a` and `b`, R does only `a`, and nothing happens after either.
fn lopsided() -> Value {
    json!({"transitions": [["L", "a", "l1"], ["L", "b", "l2"], ["R", "a", "r1"]]})
}

#[test]
fn every_move_of_either_state_must_be_matched_under_the_same_label() {
    // L's move `b` has no match in R, whichever side L is written on.
    let forth = json!([["L", "R"], ["l1", "r1"], ["l2", "r1"]]);
    assert!(!bisimilar(&lopsided(), "L", "R", forth));
    let back = json!([["R", "L"], ["r1", "l1"], ["r1", "l2"]]);
    assert!(!bisimilar(&lopsided(), "R", "L", back));
    // The move that matches must lead into a pair of the certificate.
    assert!(!bisimilar(&task(), "r0", "s0", json!([["r0", "s0"]])));
    assert!(!bisimilar(
        &task(),
        "r0",
        "s0",
        json!([["r0", "s0"], ["r1", "s1"], ["r2", "s3"]])
    ));
    // On the four machines p1 offers `c` and q1 does not.
    assert!(!bisimilar(
        &task(),
        "p1",
        "q1",
        json!([["p1", "q1"], ["p2", "q3"]])
    ));
    assert!(!bisimilar(
        &task(),
        "q1",
        "p1",
        json!([["q1", "p1"], ["q3", "p2"]])
    ));
    assert!(bisimilar(
        &task(),
        "r1",
        "q1",
        json!([["r1", "q1"], ["r2", "q3"]])
    ));
}

#[test]
fn a_failed_claim_is_not_checked_further_and_the_rest_still_are() {
    let listed = vec![
        difference("p0", "zz", json!("tt")),
        json!({"kind": "difference", "left": "p0", "right": "q0"}),
        difference("p0", "q0", json!("tt")),
        equivalence("p0", "q0", json!([["p0", "q0"]])),
        apart(),
    ];
    let (passed, report) = run(&task(), vec![claims(listed)]);
    assert!(!passed);
    assert_eq!(report["code"], "CLAIM0:STATES_DECLARED");
    assert_eq!(
        report["detail"],
        json!({
            "failed": [
                "claim0:states_declared",
                "claim1:witnessed",
                "claim2:separates",
                "claim3:bisimulation"
            ],
            "claims": 5,
        })
    );
    assert_eq!(
        outcomes(&report),
        [
            ("claim0:states_declared", false),
            ("claim1:states_declared", true),
            ("claim1:witnessed", false),
            ("claim2:states_declared", true),
            ("claim2:witnessed", true),
            ("claim2:separates", false),
            ("claim3:states_declared", true),
            ("claim3:witnessed", true),
            ("claim3:bisimulation", false),
            ("claim4:states_declared", true),
            ("claim4:witnessed", true),
            ("claim4:separates", true),
        ]
    );
}

#[test]
fn a_reply_without_claims_is_malformed() {
    for reply in [
        json!({}),
        json!({"claims": []}),
        json!({"claims": {"0": apart()}}),
        json!([apart()]),
        json!("p0 and q0 differ"),
    ] {
        assert_eq!(malformed(&task(), vec![reply]), "claims required");
    }
}

#[test]
fn a_claim_of_no_known_kind_is_malformed_and_keeps_what_was_recorded() {
    for claim in [
        json!({"kind": "similar", "left": "p0", "right": "q0"}),
        json!({"left": "p0", "right": "q0", "witness": "tt"}),
        json!({"kind": 5}),
        json!({"kind": ["difference"]}),
        json!("difference"),
        json!(null),
        json!(["difference", "p0", "q0"]),
    ] {
        assert_eq!(malformed(&task(), vec![claims(vec![claim])]), "claim kind");
    }
    let (_, report) = run(&task(), vec![claims(vec![apart(), json!({})])]);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    assert_eq!(
        outcomes(&report),
        [
            ("claim0:states_declared", true),
            ("claim0:witnessed", true),
            ("claim0:separates", true),
        ]
    );
}

fn unreadable(witness: Value) -> String {
    malformed(&task(), vec![claims(vec![difference("p0", "q0", witness)])])
}

#[test]
fn a_formula_that_is_not_one_of_the_seven_forms_is_malformed() {
    assert_eq!(unreadable(json!("maybe")), r#"unknown formula "maybe""#);
    assert_eq!(unreadable(json!("")), r#"unknown formula """#);
    assert_eq!(unreadable(json!(5)), "unknown formula 5");
    assert_eq!(unreadable(json!(null)), "unknown formula null");
    assert_eq!(unreadable(json!([])), "unknown formula []");
    assert_eq!(
        unreadable(json!({"op": "tt"})),
        r#"unknown formula {"op":"tt"}"#
    );
    assert_eq!(
        unreadable(json!(["xor", "tt", "ff"])),
        r#"unknown formula ["xor","tt","ff"]"#
    );
    assert_eq!(unreadable(json!([5, "tt"])), r#"unknown formula [5,"tt"]"#);
    assert_eq!(
        unreadable(json!([["not"], "tt"])),
        r#"unknown formula [["not"],"tt"]"#
    );
    assert_eq!(unreadable(json!(["tt"])), r#"unknown formula ["tt"]"#);
}

#[test]
fn an_operator_with_the_wrong_arguments_is_malformed() {
    assert_eq!(unreadable(json!(["not"])), "not takes one formula");
    assert_eq!(
        unreadable(json!(["not", "tt", "ff"])),
        "not takes one formula"
    );
    assert_eq!(unreadable(json!(["and", "tt"])), "and takes two arguments");
    assert_eq!(
        unreadable(json!(["and", "tt", "tt", "tt"])),
        "and takes two arguments"
    );
    assert_eq!(unreadable(json!(["or"])), "or takes two arguments");
    assert_eq!(unreadable(json!(["dia", "a"])), "dia takes two arguments");
    assert_eq!(
        unreadable(json!(["box", "a", "tt", "tt"])),
        "box takes two arguments"
    );
    assert_eq!(
        unreadable(json!(["dia", 5, "tt"])),
        "the label of dia must be text"
    );
    assert_eq!(
        unreadable(json!(["box", ["a"], "tt"])),
        "the label of box must be text"
    );
    assert_eq!(
        unreadable(json!(["box", null, "tt"])),
        "the label of box must be text"
    );
}

#[test]
fn every_part_of_a_formula_is_read_whether_or_not_a_state_reaches_it() {
    // No state has a move `z`, so nothing would ever be asked of the inner formula.
    assert_eq!(
        unreadable(json!(["dia", "z", ["bogus"]])),
        r#"unknown formula ["bogus"]"#
    );
    assert_eq!(
        unreadable(json!(["box", "z", "bogus"])),
        r#"unknown formula "bogus""#
    );
    assert_eq!(
        unreadable(json!(["and", "ff", ["not"]])),
        "not takes one formula"
    );
    assert_eq!(
        unreadable(json!(["or", "tt", ["dia", "a"]])),
        "dia takes two arguments"
    );
    assert_eq!(
        unreadable(json!(["not", ["and", "tt"]])),
        "and takes two arguments"
    );
    // The parts are read left to right, and a label before the formula under it.
    assert_eq!(
        unreadable(json!(["and", ["not"], ["or"]])),
        "not takes one formula"
    );
    assert_eq!(
        unreadable(json!(["or", ["or"], ["not"]])),
        "or takes two arguments"
    );
    assert_eq!(
        unreadable(json!(["dia", 5, ["not"]])),
        "the label of dia must be text"
    );
}

#[test]
fn a_formula_nests_at_most_twelve_deep() {
    assert_eq!(MAX_DEPTH, 12);
    // Twelve negations of `tt` are `tt`, which separates nothing.
    assert!(!separates("p0", "p2", negated(12)));
    assert!(separates(
        "p0",
        "p2",
        json!(["or", ["dia", "a", "tt"], negated(11)])
    ));
    assert_eq!(unreadable(negated(13)), "formula too deep");
    assert_eq!(
        unreadable(json!(["and", "tt", negated(12)])),
        "formula too deep"
    );
    assert_eq!(
        unreadable(json!(["or", negated(12), "tt"])),
        "formula too deep"
    );
    assert_eq!(
        unreadable(json!(["dia", "a", negated(12)])),
        "formula too deep"
    );
    assert_eq!(
        unreadable(json!(["box", "a", negated(12)])),
        "formula too deep"
    );
    let modal = |times: usize| (0..times).fold(json!("tt"), |inner, _| json!(["dia", "z", inner]));
    assert!(!separates("p0", "p2", modal(12)));
    assert_eq!(unreadable(modal(13)), "formula too deep");
}

#[test]
fn a_deep_formula_over_many_moves_is_answered_at_once() {
    // 256 moves from one state to itself. Following every move at every depth would take
    // 256 to the power 12 steps.
    let moves: Vec<Value> = (0..256).map(|_| json!(["s", "a", "s"])).collect();
    let task = json!({ "transitions": moves });
    let deep = (0..12).fold(json!("tt"), |inner, _| json!(["dia", "a", inner]));
    let (name, passed) = last_on(&task, difference("s", "s", deep));
    assert_eq!((name.as_str(), passed), ("claim0:separates", false));
}

#[test]
fn a_task_whose_transitions_are_not_triples_of_text_is_refused() {
    let reason = "transitions must be a list of [state, label, state] in text";
    for transitions in [
        json!(null),
        json!({"p0": "a"}),
        json!("p0 a p1"),
        json!([["p0", "a"]]),
        json!([["p0", "a", "p1", "p2"]]),
        json!([["p0", "a", "p1"], "p1 b p2"]),
        json!([["p0", 1, "p1"]]),
        json!([[0, "a", "p1"]]),
        json!([["p0", "a", ["p1"]]]),
    ] {
        assert_eq!(bad_task(json!({ "transitions": transitions })), reason);
    }
    assert_eq!(bad_task(json!({"statement": STATEMENT})), reason);
}

#[test]
fn a_task_lists_at_most_256_transitions() {
    assert_eq!(MAX_TRANSITIONS, 256);
    let moves = |count: usize| -> Vec<Value> {
        (0..count)
            .map(|at| json!(["s", "a", format!("t{at}")]))
            .collect()
    };
    assert_eq!(
        bad_task(json!({ "transitions": moves(257) })),
        "at most 256 transitions"
    );
    assert_eq!(
        ask(&json!({ "transitions": moves(256) }), vec![])["stage"],
        "solve"
    );
}

#[test]
fn a_task_with_no_transitions_declares_no_state() {
    let empty = json!({"transitions": []});
    assert_eq!(ask(&empty, vec![])["stage"], "solve");
    let claim = difference("p0", "p0", json!("tt"));
    assert_eq!(
        last_on(&empty, claim),
        ("claim0:states_declared".to_owned(), false)
    );
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&task(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}
