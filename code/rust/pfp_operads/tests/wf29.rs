//! WF29, checker synthesis scored by mutation kill rate: what each declared predicate says of a
//! case, how a tree joins them, and the two bars a checker must clear.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf29-tests:v1

use pfp_operads::families::wf29::{FAMILY, MAX_DEPTH, PREDICATES};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Write a checker from the declared predicates.";

fn request(task: &Value, sealed: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF29", "task": task, "sealed": sealed, "replies": replies}).to_string()
}

/// The report of a run with one reply, and whether the host passed it.
fn run(task: &Value, sealed: &Value, reply: Value) -> (bool, Value) {
    match judge(&request(task, sealed, &[Some(reply)])) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn bad_task(task: Value, sealed: Value) -> String {
    match next(&request(&task, &sealed, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

/// The reason of a run refused because a reply could not be read.
fn malformed(reply: Value) -> String {
    let (passed, report) = run(&task(), &sealed(), reply);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    assert_eq!(report["predicates"], json!([]));
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

fn case(c: Value, phi: Value) -> Value {
    json!({"c": c, "phi": phi})
}

/// A potential on the triangle and its coboundary.
fn sound() -> Value {
    case(json!([1, 2, 3]), json!({"a": 0, "b": 1, "c": 3}))
}

/// The same coboundary from a potential that is not zero at the first vertex.
fn shifted() -> Value {
    case(json!([1, 2, 3]), json!({"a": 5, "b": 6, "c": 8}))
}

/// A value on the edges that is the coboundary of no potential.
fn inexact() -> Value {
    case(json!([1, 2, 4]), json!({"a": 0, "b": 1, "c": 3}))
}

/// A coboundary, with a potential that is not its potential.
fn wrong_potential() -> Value {
    case(json!([1, 2, 3]), json!({"a": 0, "b": 1, "c": 7}))
}

/// One edge value too few.
fn short() -> Value {
    case(json!([1, 2]), json!({"a": 0, "b": 1, "c": 3}))
}

/// A potential that leaves out a vertex.
fn partial() -> Value {
    case(json!([1, 2, 3]), json!({"a": 0, "b": 1}))
}

/// A triangle a, b, c, two valid cases, and a bar of four mutants in five.
fn task() -> Value {
    json!({
        "statement": STATEMENT,
        "edges": [["a", "b"], ["b", "c"], ["a", "c"]],
        "predicates": [
            "c_length_matches", "coboundary_matches", "cycle_sums_zero",
            "phi_covers_vertices", "phi_root_zero"
        ],
        "min_kill_rate": "4/5",
        "valid": [sound(), case(json!([2, -2, 0]), json!({"a": 0, "b": 2, "c": 0}))],
    })
}

fn with(key: &str, value: Value) -> Value {
    let mut task = task();
    task[key] = value;
    task
}

/// Five mutants. Only `phi_root_zero` tells the last from a valid case.
fn sealed() -> Value {
    json!({"mutants": [inexact(), wrong_potential(), short(), partial(), shifted()]})
}

fn prompt() -> String {
    format!(
        "WF29 Checker synthesis scored by mutation kill rate. {STATEMENT}\n{}",
        concat!(
            r#"{"edges":[["a","b"],["b","c"],["a","c"]],"min_kill_rate":"4/5","#,
            r#""predicates":["c_length_matches","coboundary_matches","cycle_sums_zero","#,
            r#""phi_covers_vertices","phi_root_zero"],"#,
            r#""valid":[{"c":[1,2,3],"phi":{"a":0,"b":1,"c":3}},"#,
            r#"{"c":[2,-2,0],"phi":{"a":0,"b":2,"c":0}}]}"#
        )
    )
}

fn checker(tree: Value) -> Value {
    json!({ "checker": tree })
}

/// The checker that states the definition of a valid case.
fn definition() -> Value {
    json!([
        "and",
        "c_length_matches",
        "phi_covers_vertices",
        "coboundary_matches"
    ])
}

/// Whether a checker accepts one case on a graph: the case is the only mutant, and it
/// survives.
fn accepts_on(edges: Value, tree: &Value, case: Value) -> bool {
    let task = json!({"edges": edges, "valid": [], "min_kill_rate": 0});
    let (passed, report) = run(&task, &json!({"mutants": [case]}), checker(tree.clone()));
    assert!(passed, "{report}");
    let killed = &report["detail"]["kill_rate"];
    assert!(*killed == json!(0) || *killed == json!(1), "{killed}");
    *killed == json!(0)
}

fn accepts(tree: &Value, case: Value) -> bool {
    accepts_on(task()["edges"].clone(), tree, case)
}

/// What a predicate and its negation say of a case: `Some` when the predicate can read the
/// case, and nothing when both reject it.
fn reads(predicate: &str, case: Value) -> Option<bool> {
    let plain = accepts(&json!(predicate), case.clone());
    let negated = accepts(&json!(["not", predicate]), case);
    assert!(!(plain && negated));
    (plain || negated).then_some(plain)
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF29",
            "Checker synthesis scored by mutation kill rate",
            "mutation_kill_rate_with_valid_panel"
        )
    );
}

#[test]
fn the_declared_predicates_are_the_five_a_checker_may_name() {
    assert_eq!(
        PREDICATES,
        [
            "c_length_matches",
            "phi_covers_vertices",
            "coboundary_matches",
            "cycle_sums_zero",
            "phi_root_zero"
        ]
    );
    for name in PREDICATES {
        assert!(accepts(&json!(name), sound()), "{name}");
    }
}

#[test]
fn the_one_question_shows_the_valid_cases_and_never_the_mutants() {
    let outcome = next(&request(&task(), &sealed(), &[]));
    let Outcome::Pass { result } = outcome else {
        panic!("expected a turn, got {outcome:?}");
    };
    assert_eq!(result["ask"]["stage"], "solve");
    assert_eq!(result["ask"]["prompt"], prompt());
    assert_eq!(result["ask"]["prompt_sha256"], sha(&prompt()));
    let done = next(&request(&task(), &sealed(), &[Some(checker(definition()))]));
    let Outcome::Pass { result } = done else {
        panic!("expected the end of the run, got {done:?}");
    };
    assert_eq!(result["ask"], Value::Null);
}

#[test]
fn a_checker_that_rejects_no_valid_case_and_enough_mutants_is_certified() {
    let (passed, report) = run(&task(), &sealed(), checker(definition()));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CHECKER_ACCEPTED");
    assert_eq!(
        report["detail"],
        json!({"kill_rate": "4/5", "false_rejections": 0, "mutants": 5})
    );
    assert_eq!(
        outcomes(&report),
        [("no_false_rejection", true), ("kill_rate_meets_bar", true)]
    );
    assert_eq!(evidence(&report, "no_false_rejection"), &json!(sha("0")));
    assert_eq!(
        evidence(&report, "kill_rate_meets_bar"),
        &json!(sha("\"4/5\""))
    );
}

#[test]
fn a_kill_rate_below_the_bar_is_refused() {
    let (passed, report) = run(
        &with("min_kill_rate", json!(1)),
        &sealed(),
        checker(definition()),
    );
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "KILL_RATE_MEETS_BAR");
    assert_eq!(
        report["detail"],
        json!({
            "failed": ["kill_rate_meets_bar"],
            "kill_rate": "4/5",
            "false_rejections": 0,
            "mutants": 5,
        })
    );
    // The bar is read as an exact rational, in any of its spellings.
    for bar in [json!("8/10"), json!("3/4"), json!(0), json!("-1/2")] {
        assert!(
            run(
                &with("min_kill_rate", bar),
                &sealed(),
                checker(definition())
            )
            .0
        );
    }
    for bar in [json!("5/6"), json!("81/100"), json!(2)] {
        assert!(
            !run(
                &with("min_kill_rate", bar),
                &sealed(),
                checker(definition())
            )
            .0
        );
    }
}

#[test]
fn a_kill_rate_is_written_as_an_integer_or_in_lowest_terms() {
    let rate = |tree: Value, mutants: Value| {
        let task = with("min_kill_rate", json!(0));
        let (_, report) = run(&task, &json!({ "mutants": mutants }), checker(tree));
        report["detail"].clone()
    };
    let four = json!([inexact(), sound(), short(), sound()]);
    assert_eq!(
        rate(definition(), four.clone()),
        json!({"kill_rate": "1/2", "false_rejections": 0, "mutants": 4})
    );
    assert_eq!(
        rate(definition(), json!([inexact(), short()]))["kill_rate"],
        1
    );
    assert_eq!(
        rate(definition(), json!([sound(), sound()]))["kill_rate"],
        0
    );
    assert_eq!(rate(json!("cycle_sums_zero"), four)["kill_rate"], "1/2");
}

#[test]
fn with_no_mutants_the_kill_rate_is_zero() {
    for sealed in [json!({}), json!({"mutants": []})] {
        let (passed, report) = run(&task(), &sealed, checker(definition()));
        assert!(!passed);
        assert_eq!(report["code"], "KILL_RATE_MEETS_BAR");
        assert_eq!(report["detail"]["kill_rate"], 0);
        assert_eq!(report["detail"]["mutants"], 0);
        assert_eq!(evidence(&report, "kill_rate_meets_bar"), &json!(sha("0")));
        let free = with("min_kill_rate", json!(0));
        assert!(run(&free, &sealed, checker(definition())).0);
    }
}

#[test]
fn a_checker_that_rejects_a_valid_case_is_refused() {
    let mut task = task();
    task["valid"]
        .as_array_mut()
        .expect("a list")
        .push(shifted());
    let (passed, report) = run(&task, &sealed(), checker(json!("phi_root_zero")));
    assert!(!passed);
    assert_eq!(report["code"], "NO_FALSE_REJECTION");
    assert_eq!(
        outcomes(&report),
        [
            ("no_false_rejection", false),
            ("kill_rate_meets_bar", false)
        ]
    );
    assert_eq!(
        report["detail"],
        json!({
            "failed": ["no_false_rejection", "kill_rate_meets_bar"],
            "kill_rate": "1/5",
            "false_rejections": 1,
            "mutants": 5,
        })
    );
    assert_eq!(evidence(&report, "no_false_rejection"), &json!(sha("1")));
    // Rejecting every valid case is counted case by case.
    let none = json!(["not", "c_length_matches"]);
    let (_, report) = run(&task, &sealed(), checker(none));
    assert_eq!(report["detail"]["false_rejections"], 3);
    assert_eq!(report["detail"]["kill_rate"], "4/5");
    assert_eq!(
        outcomes(&report),
        [("no_false_rejection", false), ("kill_rate_meets_bar", true)]
    );
}

#[test]
fn a_valid_case_the_checker_cannot_read_counts_as_rejected() {
    let task = with("valid", json!([sound(), "junk", {"c": [1, 2, 3]}]));
    let (_, report) = run(&task, &sealed(), checker(definition()));
    assert_eq!(report["code"], "NO_FALSE_REJECTION");
    assert_eq!(report["detail"]["false_rejections"], 2);
}

#[test]
fn the_length_predicate_counts_the_entries_of_a_list() {
    let name = "c_length_matches";
    assert_eq!(reads(name, sound()), Some(true));
    assert_eq!(reads(name, short()), Some(false));
    assert_eq!(
        reads(name, case(json!([1, 2, 3, 4]), json!({}))),
        Some(false)
    );
    // The entries are not read, and neither is phi.
    assert_eq!(reads(name, json!({"c": ["x", null, 0.5]})), Some(true));
    for unreadable in [
        json!({"phi": {"a": 0, "b": 1, "c": 3}}),
        case(json!("abc"), json!({})),
        case(json!({"0": 1, "1": 2, "2": 3}), json!({})),
        case(json!(3), json!({})),
        json!("abc"),
        json!([1, 2, 3]),
        json!(null),
    ] {
        assert_eq!(reads(name, unreadable.clone()), None, "{unreadable}");
    }
}

#[test]
fn the_cover_predicate_wants_exactly_the_vertex_names_as_keys() {
    let name = "phi_covers_vertices";
    assert_eq!(reads(name, sound()), Some(true));
    assert_eq!(reads(name, partial()), Some(false));
    let extra = json!({"a": 0, "b": 1, "c": 3, "d": 0});
    assert_eq!(reads(name, case(json!([1, 2, 3]), extra)), Some(false));
    // The values are not read, and neither is c.
    assert_eq!(
        reads(name, json!({"phi": {"a": "x", "b": null, "c": 0.5}})),
        Some(true)
    );
    for unreadable in [
        json!({"c": [1, 2, 3]}),
        case(json!([1, 2, 3]), json!(["a", "b", "c"])),
        case(json!([1, 2, 3]), json!("abc")),
        case(json!([1, 2, 3]), json!(null)),
    ] {
        assert_eq!(reads(name, unreadable.clone()), None, "{unreadable}");
    }
}

#[test]
fn the_coboundary_predicate_compares_c_with_the_coboundary_of_phi() {
    let name = "coboundary_matches";
    assert_eq!(reads(name, sound()), Some(true));
    assert_eq!(reads(name, shifted()), Some(true));
    assert_eq!(reads(name, inexact()), Some(false));
    assert_eq!(reads(name, wrong_potential()), Some(false));
    assert_eq!(reads(name, short()), Some(false));
    let spelled = case(
        json!(["2/2", 2, "6/2"]),
        json!({"a": "1/2", "b": "3/2", "c": "7/2"}),
    );
    assert_eq!(reads(name, spelled), Some(true));
    // A value under a name that is not a vertex is not read.
    let extra = json!({"a": 0, "b": 1, "c": 3, "d": "x"});
    assert_eq!(reads(name, case(json!([1, 2, 3]), extra)), Some(true));
    for unreadable in [
        partial(),
        case(json!([1, 2, 3]), json!({"a": 0, "b": 1, "c": "x"})),
        case(json!([1, 2, 3]), json!({"a": 0, "b": 1, "c": 1.5})),
        case(json!([1, 2, 3]), json!([0, 1, 3])),
        case(json!([1, 2, "x"]), json!({"a": 0, "b": 1, "c": 3})),
        case(json!([1, 2, 0.5]), json!({"a": 0, "b": 1, "c": 3})),
        case(json!("123"), json!({"a": 0, "b": 1, "c": 3})),
        json!({"phi": {"a": 0, "b": 1, "c": 3}}),
        json!({"c": [1, 2, 3]}),
    ] {
        assert_eq!(reads(name, unreadable.clone()), None, "{unreadable}");
    }
}

#[test]
fn the_cycle_predicate_asks_whether_c_is_a_coboundary_at_all() {
    let name = "cycle_sums_zero";
    assert_eq!(reads(name, sound()), Some(true));
    assert_eq!(reads(name, wrong_potential()), Some(true));
    assert_eq!(reads(name, inexact()), Some(false));
    // phi is not read.
    assert_eq!(reads(name, json!({"c": [1, 2, 3]})), Some(true));
    assert_eq!(reads(name, json!({"c": ["1/2", "1/2", 1]})), Some(true));
    for unreadable in [
        short(),
        case(json!([1, 2, 3, 0]), json!({})),
        case(json!([1, 2, "x"]), json!({})),
        case(json!([1, 2, 3.5]), json!({})),
        case(json!(null), json!({})),
        json!({"phi": {"a": 0, "b": 1, "c": 3}}),
    ] {
        assert_eq!(reads(name, unreadable.clone()), None, "{unreadable}");
    }
}

#[test]
fn the_root_predicate_reads_phi_at_the_first_vertex_the_edges_name() {
    let name = "phi_root_zero";
    assert_eq!(reads(name, sound()), Some(true));
    assert_eq!(reads(name, shifted()), Some(false));
    // Only the entry of the root is read.
    assert_eq!(
        reads(name, json!({"phi": {"a": "0/5", "b": "x"}})),
        Some(true)
    );
    assert_eq!(reads(name, json!({"phi": {"a": "1/5"}})), Some(false));
    for unreadable in [
        json!({"phi": {"b": 0, "c": 0}}),
        json!({"phi": {"a": "x"}}),
        json!({"phi": {"a": null}}),
        json!({"phi": [0, 0, 0]}),
        json!({"c": [1, 2, 3]}),
    ] {
        assert_eq!(reads(name, unreadable.clone()), None, "{unreadable}");
    }
    // With the edge written the other way round, the root is b.
    let turned = json!([["b", "a"]]);
    let at = |a: i64, b: i64| json!({"phi": {"a": a, "b": b}});
    assert!(accepts_on(turned.clone(), &json!(name), at(1, 0)));
    assert!(!accepts_on(turned, &json!(name), at(0, 1)));
}

#[test]
fn a_graph_with_no_edges_has_no_root_to_read() {
    let none = json!([]);
    let empty = case(json!([]), json!({}));
    assert!(accepts_on(
        none.clone(),
        &json!("c_length_matches"),
        empty.clone()
    ));
    assert!(accepts_on(
        none.clone(),
        &json!("phi_covers_vertices"),
        empty.clone()
    ));
    assert!(accepts_on(
        none.clone(),
        &json!("coboundary_matches"),
        empty.clone()
    ));
    assert!(accepts_on(
        none.clone(),
        &json!("cycle_sums_zero"),
        empty.clone()
    ));
    assert!(!accepts_on(
        none.clone(),
        &json!("phi_root_zero"),
        empty.clone()
    ));
    assert!(!accepts_on(none, &json!(["not", "phi_root_zero"]), empty));
}

#[test]
fn and_wants_every_part_and_or_wants_one() {
    let exact = "cycle_sums_zero";
    let rooted = "phi_root_zero";
    let both = json!(["and", exact, rooted]);
    let either = json!(["or", exact, rooted]);
    // sound: both hold. shifted: exact only. inexact: rooted only.
    let neither = case(json!([1, 2, 4]), json!({"a": 1, "b": 1, "c": 3}));
    assert!(accepts(&both, sound()));
    assert!(!accepts(&both, shifted()));
    assert!(!accepts(&both, inexact()));
    assert!(!accepts(&both, neither.clone()));
    assert!(accepts(&either, sound()));
    assert!(accepts(&either, shifted()));
    assert!(accepts(&either, inexact()));
    assert!(!accepts(&either, neither.clone()));
    // One part alone, and three parts.
    assert!(accepts(&json!(["and", rooted]), sound()));
    assert!(!accepts(&json!(["and", rooted]), shifted()));
    assert!(accepts(&json!(["or", rooted]), sound()));
    assert!(!accepts(&json!(["or", rooted]), shifted()));
    let three = json!(["or", rooted, exact, "c_length_matches"]);
    assert!(accepts(&three, neither.clone()));
    assert!(!accepts(
        &json!(["and", "c_length_matches", exact, rooted]),
        shifted()
    ));
    // Negations nest.
    assert!(accepts(&json!(["not", ["not", rooted]]), sound()));
    assert!(accepts(&json!(["not", both]), neither.clone()));
    assert!(!accepts(&json!(["not", either]), shifted()));
    assert!(accepts(&json!(["not", either]), neither));
}

#[test]
fn the_parts_are_read_in_order_and_an_unreadable_one_rejects_the_case() {
    let length = "c_length_matches";
    let exact = "cycle_sums_zero";
    // On a short c the length is wrong, and the cycle sums cannot be read.
    assert!(accepts(&json!(["not", ["and", length, exact]]), short()));
    assert!(!accepts(&json!(["not", ["and", exact, length]]), short()));
    assert!(!accepts(&json!(["and", exact, length]), short()));
    // Three entries, one of them not a number: the length is right.
    let odd = case(json!([1, 2, "x"]), json!({"a": 0, "b": 1, "c": 3}));
    assert!(accepts(&json!(["or", length, exact]), odd.clone()));
    assert!(!accepts(&json!(["or", exact, length]), odd.clone()));
    assert!(!accepts(
        &json!(["not", ["or", exact, length]]),
        odd.clone()
    ));
    // An unreadable part rejects from any depth.
    assert!(!accepts(
        &json!(["or", ["not", ["and", exact]], length]),
        odd
    ));
}

fn unreadable(tree: Value) -> String {
    malformed(checker(tree))
}

#[test]
fn a_reply_without_a_checker_is_malformed() {
    for reply in [
        json!({}),
        json!({"check": "cycle_sums_zero"}),
        json!("cycle_sums_zero"),
        json!(null),
    ] {
        assert_eq!(malformed(reply), "checker required");
    }
}

#[test]
fn a_name_that_is_not_declared_is_malformed_and_nothing_is_executed() {
    assert_eq!(
        unreadable(json!("lambda case: True")),
        r#"unknown predicate "lambda case: True""#
    );
    assert_eq!(unreadable(json!("")), r#"unknown predicate """#);
    assert_eq!(unreadable(json!("and")), r#"unknown predicate "and""#);
    assert_eq!(
        unreadable(json!(["and", "cycle_sums_zero", "Cycle_Sums_Zero"])),
        r#"unknown predicate "Cycle_Sums_Zero""#
    );
}

#[test]
fn a_tree_that_is_not_an_operator_over_parts_is_malformed() {
    assert_eq!(unreadable(json!(5)), "bad checker 5");
    assert_eq!(unreadable(json!(null)), "bad checker null");
    assert_eq!(unreadable(json!([])), "bad checker []");
    assert_eq!(unreadable(json!(["and"])), r#"bad checker ["and"]"#);
    assert_eq!(unreadable(json!(["not"])), r#"bad checker ["not"]"#);
    assert_eq!(
        unreadable(json!(["xor", "cycle_sums_zero"])),
        r#"bad checker ["xor","cycle_sums_zero"]"#
    );
    assert_eq!(
        unreadable(json!([5, "cycle_sums_zero"])),
        r#"bad checker [5,"cycle_sums_zero"]"#
    );
    assert_eq!(
        unreadable(json!({"and": ["cycle_sums_zero"]})),
        r#"bad checker {"and":["cycle_sums_zero"]}"#
    );
    assert_eq!(
        unreadable(json!(["or", "cycle_sums_zero", ["nor", "phi_root_zero"]])),
        r#"bad checker ["nor","phi_root_zero"]"#
    );
}

#[test]
fn not_takes_exactly_one_part() {
    assert_eq!(
        unreadable(json!(["not", "cycle_sums_zero", "phi_root_zero"])),
        "not takes one checker"
    );
    // The parts are read first.
    assert_eq!(
        unreadable(json!(["not", "cycle_sums_zero", "bogus"])),
        r#"unknown predicate "bogus""#
    );
}

#[test]
fn a_checker_nests_at_most_six_deep() {
    assert_eq!(MAX_DEPTH, 6);
    let nested = |operator: &str, times: usize| {
        (0..times).fold(json!("cycle_sums_zero"), |inner, _| {
            json!([operator, inner])
        })
    };
    for operator in ["not", "and", "or"] {
        let (passed, report) = run(&task(), &sealed(), checker(nested(operator, 6)));
        assert_ne!(report["code"], "MALFORMED_CANDIDATE", "{operator}");
        assert!(!passed);
        assert_eq!(unreadable(nested(operator, 7)), "checker too deep");
    }
    // Six negations cancel out.
    assert!(accepts(&nested("not", 6), sound()));
    assert!(!accepts(&nested("not", 5), sound()));
}

#[test]
fn a_task_is_read_in_a_fixed_order_and_refused_at_the_first_part_that_does_not_fit() {
    let mut task = task();
    for key in ["edges", "valid", "min_kill_rate"] {
        task[key] = json!(null);
    }
    let unsealed = json!({"mutants": "none"});
    assert_eq!(
        bad_task(task.clone(), unsealed.clone()),
        "edges must be a list of pairs of text"
    );
    task["edges"] = json!([["a", "b"]]);
    assert_eq!(
        bad_task(task.clone(), unsealed.clone()),
        "valid must be a list of cases"
    );
    task["valid"] = json!([]);
    assert_eq!(
        bad_task(task.clone(), unsealed.clone()),
        "min_kill_rate must be an exact rational"
    );
    task["min_kill_rate"] = json!("1/2");
    assert_eq!(bad_task(task, unsealed), "sealed mutants must be a list");
}

#[test]
fn each_part_of_a_task_has_one_shape() {
    for edges in [json!([[0, 1]]), json!([["a", "b", "c"]]), json!({"a": "b"})] {
        assert_eq!(
            bad_task(with("edges", edges), sealed()),
            "edges must be a list of pairs of text"
        );
    }
    for valid in [json!({"c": [], "phi": {}}), json!("none"), json!(3)] {
        assert_eq!(
            bad_task(with("valid", valid), sealed()),
            "valid must be a list of cases"
        );
    }
    for bar in [json!("most"), json!(0.8), json!([4, 5]), json!("4/0")] {
        assert_eq!(
            bad_task(with("min_kill_rate", bar), sealed()),
            "min_kill_rate must be an exact rational"
        );
    }
    for mutants in [json!("none"), json!({"0": {}}), json!(null), json!(5)] {
        assert_eq!(
            bad_task(task(), json!({ "mutants": mutants })),
            "sealed mutants must be a list"
        );
    }
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&task(), &sealed(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}
