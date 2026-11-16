//! WF44, exact certificate presets: the float gate, the type gate, and the equations of the
//! three registered schemas.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf44-tests:v1

use pfp_operads::families::wf44::{FAMILY, SCHEMAS};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Certify the answer under the named schema.";

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF44", "task": task, "replies": replies}).to_string()
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

/// A square a, b, c, d with the diagonal a-c, and the coboundary of (0, 1, 3, 2).
fn potential_task() -> Value {
    json!({
        "schema": "coboundary_potential",
        "statement": STATEMENT,
        "edges": [["a", "b"], ["b", "c"], ["c", "d"], ["d", "a"], ["a", "c"]],
        "c": [1, 2, -1, -2, 3],
    })
}

/// A triangle with weights (3, 1, 0). Its one cycle runs along the first two edges and back
/// along the third, so the l1 distance of `w` to the coboundaries is 4 under unit caps.
fn dual_task() -> Value {
    json!({
        "schema": "l1_dual_circulation",
        "statement": STATEMENT,
        "edges": [["a", "b"], ["b", "c"], ["a", "c"]],
        "w": [3, 1, 0],
    })
}

/// The triangle with the middle edge at half price: the distance is 2.
fn capped_task() -> Value {
    let mut task = dual_task();
    task["cap"] = json!([1, "1/2", 1]);
    task
}

/// 2x = 1 and 3y = 1.
fn linear_task() -> Value {
    json!({"schema": "canonical_rational", "statement": STATEMENT, "A": [[2, 0], [0, 3]], "b": [1, 1]})
}

fn prompt() -> String {
    format!(
        "WF44 Exact certificate presets. {STATEMENT}\n{}",
        concat!(
            r#"{"c":[1,2,-1,-2,3],"#,
            r#""edges":[["a","b"],["b","c"],["c","d"],["d","a"],["a","c"]],"#,
            r#""schema":"coboundary_potential"}"#
        )
    )
}

/// A reply that names the schema of the task it answers.
fn reply(task: &Value, certificate: Value) -> Value {
    json!({"schema": task["schema"], "certificate": certificate})
}

fn certify(task: &Value, certificate: Value) -> (bool, Value) {
    run(task, vec![reply(task, certificate)])
}

fn phi() -> Value {
    json!({"phi": {"a": 0, "b": 1, "c": 3, "d": 2}})
}

/// All of the residual on the middle edge, and one unit round the cycle.
fn dual() -> Value {
    json!({"f": {"a": 0, "b": -3, "c": 0}, "r": [0, 4, 0], "z": [1, 1, -1]})
}

fn dual_with(key: &str, value: Value) -> Value {
    let mut certificate = dual();
    certificate[key] = value;
    certificate
}

const GATES: [(&str, bool); 2] = [("no_float", true), ("well_typed", true)];

/// The two gates passed, then these equations with these outcomes.
fn gated<const N: usize>(equations: [(&'static str, bool); N]) -> Vec<(&'static str, bool)> {
    GATES.into_iter().chain(equations).collect()
}

const DUAL: [&str; 4] = [
    "residual_is_w_plus_Bf",
    "dual_is_circulation",
    "dual_within_caps",
    "duality_gap_zero",
];

fn dual_outcomes(passed: [bool; 4]) -> Vec<(&'static str, bool)> {
    GATES
        .into_iter()
        .chain(DUAL.into_iter().zip(passed))
        .collect()
}

const LINEAR: [&str; 3] = ["unique_solution", "values_equal_solution", "canonical_form"];

fn linear_outcomes(passed: [bool; 3]) -> Vec<(&'static str, bool)> {
    GATES
        .into_iter()
        .chain(LINEAR.into_iter().zip(passed))
        .collect()
}

/// A run refused at the type gate, before any equation.
fn ill_typed(task: &Value, reply: Value) {
    let (passed, report) = run(task, vec![reply.clone()]);
    assert!(!passed, "{reply}");
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ILL_TYPED", "{reply}");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(
        outcomes(&report),
        [("no_float", true), ("well_typed", false)]
    );
}

/// A run refused at the float gate, before the types are read.
fn float(task: &Value, certificate: Value) {
    let (passed, report) = certify(task, certificate.clone());
    assert!(!passed, "{certificate}");
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "FLOAT_IN_CERTIFICATE", "{certificate}");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(outcomes(&report), [("no_float", false)]);
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF44",
            "Exact certificate presets",
            "exact_certificate_presets"
        )
    );
    assert_eq!(
        SCHEMAS,
        [
            "coboundary_potential",
            "l1_dual_circulation",
            "canonical_rational"
        ]
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&potential_task(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt());
    assert_eq!(first["prompt_sha256"], sha(&prompt()));
    let done = ask(&potential_task(), vec![reply(&potential_task(), phi())]);
    assert_eq!(done, Value::Null);
}

#[test]
fn a_potential_whose_coboundary_is_c_is_certified() {
    let (passed, report) = certify(&potential_task(), phi());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CERTIFICATE_VALID");
    assert_eq!(report["detail"], json!({"schema": "coboundary_potential"}));
    assert_eq!(outcomes(&report), gated([("coboundary_matches", true)]));
    assert_eq!(evidence(&report, "no_float"), &json!(sha("null")));
    let certificate = r#"{"phi":{"a":0,"b":1,"c":3,"d":2}}"#;
    assert_eq!(
        evidence(&report, "well_typed"),
        &json!(sha(&format!(
            r#"{{"certificate":{certificate},"schema":"coboundary_potential"}}"#
        )))
    );
    assert_eq!(
        evidence(&report, "coboundary_matches"),
        &json!(sha(certificate))
    );
    // Any shift of the potential, in integers or in text p/q, is as good.
    let shifted = json!({"phi": {"a": "1/2", "b": "3/2", "c": "7/2", "d": "5/2"}});
    assert!(certify(&potential_task(), shifted).0);
}

#[test]
fn a_potential_that_misses_an_edge_is_refused() {
    let off = json!({"phi": {"a": 0, "b": 1, "c": 3, "d": 5}});
    let (passed, report) = certify(&potential_task(), off);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "COBOUNDARY_MATCHES");
    assert_eq!(
        report["detail"],
        json!({"failed": ["coboundary_matches"], "schema": "coboundary_potential"})
    );
    assert_eq!(outcomes(&report), gated([("coboundary_matches", false)]));
}

#[test]
fn a_primal_and_dual_pair_with_no_gap_is_certified() {
    let (passed, report) = certify(&dual_task(), dual());
    assert!(passed);
    assert_eq!(report["code"], "CERTIFICATE_VALID");
    assert_eq!(report["detail"], json!({"schema": "l1_dual_circulation"}));
    assert_eq!(outcomes(&report), dual_outcomes([true; 4]));
    // Leaving the residual where the weights are is another optimum.
    let plain = json!({"f": {"a": 0, "b": 0, "c": 0}, "r": [3, 1, 0], "z": [1, 1, -1]});
    assert!(certify(&dual_task(), plain).0);
    // With the middle edge at half price the circulation is half as large.
    let halved = dual_with("z", json!(["1/2", "1/2", "-1/2"]));
    let (passed, report) = certify(&capped_task(), halved);
    assert!(passed);
    assert_eq!(outcomes(&report), dual_outcomes([true; 4]));
}

#[test]
fn negative_residuals_and_flows_count_by_their_size() {
    let mut task = dual_task();
    task["w"] = json!([-3, -1, 0]);
    let certificate = json!({"f": {"a": 0, "b": 0, "c": 0}, "r": [-3, -1, 0], "z": [-1, -1, 1]});
    let (passed, report) = certify(&task, certificate);
    assert!(passed);
    assert_eq!(outcomes(&report), dual_outcomes([true; 4]));
}

#[test]
fn a_residual_that_is_not_w_plus_the_coboundary_of_f_is_refused() {
    let (passed, report) = certify(&dual_task(), dual_with("r", json!([0, 4, 1])));
    assert!(!passed);
    assert_eq!(report["code"], "RESIDUAL_IS_W_PLUS_BF");
    assert_eq!(outcomes(&report), dual_outcomes([false, true, true, false]));
    // The coboundary is added, head less tail: the opposite potential does not fit.
    let opposite = dual_with("f", json!({"a": 0, "b": 3, "c": 0}));
    let (_, report) = certify(&dual_task(), opposite);
    assert_eq!(outcomes(&report), dual_outcomes([false, true, true, true]));
}

#[test]
fn a_flow_with_net_flow_at_a_vertex_is_refused() {
    let (passed, report) = certify(&dual_task(), dual_with("z", json!([1, 1, 1])));
    assert!(!passed);
    assert_eq!(report["code"], "DUAL_IS_CIRCULATION");
    assert_eq!(outcomes(&report), dual_outcomes([true, false, true, true]));
}

#[test]
fn a_flow_beyond_a_cap_is_refused() {
    // Seven eighths round the cycle closes the gap against the residual (3, 1, 0), but the
    // middle edge carries at most a half.
    let over = json!({
        "f": {"a": 0, "b": 0, "c": 0},
        "r": [3, 1, 0],
        "z": ["7/8", "7/8", "-7/8"],
    });
    let (passed, report) = certify(&capped_task(), over);
    assert!(!passed);
    assert_eq!(report["code"], "DUAL_WITHIN_CAPS");
    assert_eq!(outcomes(&report), dual_outcomes([true, true, false, true]));
    // A cap bounds the size of the flow in either direction, and may be met exactly.
    let (_, report) = certify(&dual_task(), dual_with("z", json!([-2, -2, 2])));
    assert_eq!(outcomes(&report), dual_outcomes([true, true, false, false]));
    let (_, report) = certify(&dual_task(), dual_with("z", json!([-1, -1, 1])));
    assert_eq!(outcomes(&report), dual_outcomes([true, true, true, false]));
}

#[test]
fn a_gap_between_the_primal_and_the_dual_is_refused() {
    let (passed, report) = certify(&dual_task(), dual_with("z", json!([0, 0, 0])));
    assert!(!passed);
    assert_eq!(report["code"], "DUALITY_GAP_ZERO");
    assert_eq!(outcomes(&report), dual_outcomes([true, true, true, false]));
    // The caps weigh the residual: what was optimal at unit caps leaves a gap here.
    let (_, report) = certify(&capped_task(), dual());
    assert_eq!(outcomes(&report), dual_outcomes([true, true, false, false]));
}

#[test]
fn the_one_solution_in_canonical_form_is_certified() {
    let (passed, report) = certify(&linear_task(), json!({"x": ["1/2", "1/3"]}));
    assert!(passed);
    assert_eq!(report["code"], "CERTIFICATE_VALID");
    assert_eq!(report["detail"], json!({"schema": "canonical_rational"}));
    assert_eq!(outcomes(&report), linear_outcomes([true; 3]));
    // An integer is canonical as a number or as its digits.
    let whole = json!({"schema": "canonical_rational", "A": [[1, 0], [0, 1]], "b": [2, -3]});
    for x in [json!([2, -3]), json!(["2", "-3"]), json!([2, "-3"])] {
        let (passed, report) = certify(&whole, json!({ "x": x }));
        assert!(passed, "{report}");
    }
}

#[test]
fn a_solution_that_is_right_but_not_in_lowest_terms_is_refused() {
    let (passed, report) = certify(&linear_task(), json!({"x": ["2/4", "1/3"]}));
    assert!(!passed);
    assert_eq!(report["code"], "CANONICAL_FORM");
    assert_eq!(outcomes(&report), linear_outcomes([true, true, false]));
    let whole = json!({"schema": "canonical_rational", "A": [[1, 0], [0, 1]], "b": [2, -3]});
    for x in [
        json!(["4/2", -3]),
        json!(["2/1", -3]),
        json!(["02", -3]),
        json!([2, "-6/2"]),
        json!([2, "-03"]),
    ] {
        let (_, report) = certify(&whole, json!({ "x": x }));
        assert_eq!(
            outcomes(&report),
            linear_outcomes([true, true, false]),
            "{x}"
        );
    }
    let zero = json!({"schema": "canonical_rational", "A": [[1]], "b": [0]});
    assert!(certify(&zero, json!({"x": ["0"]})).0);
    let (_, report) = certify(&zero, json!({"x": ["-0"]}));
    assert_eq!(outcomes(&report), linear_outcomes([true, true, false]));
}

#[test]
fn a_canonical_vector_that_is_not_the_solution_is_refused() {
    let (passed, report) = certify(&linear_task(), json!({"x": ["1/2", "1/4"]}));
    assert!(!passed);
    assert_eq!(report["code"], "VALUES_EQUAL_SOLUTION");
    assert_eq!(outcomes(&report), linear_outcomes([true, false, true]));
}

#[test]
fn a_system_without_exactly_one_solution_has_no_canonical_certificate() {
    let many = json!({"schema": "canonical_rational", "A": [[1, 1], [2, 2]], "b": [1, 2]});
    let (passed, report) = certify(&many, json!({"x": [1, 0]}));
    assert!(!passed);
    assert_eq!(report["code"], "UNIQUE_SOLUTION");
    assert_eq!(outcomes(&report), linear_outcomes([false, false, true]));
    assert_eq!(
        report["detail"]["failed"],
        json!(["unique_solution", "values_equal_solution"])
    );
    let none = json!({"schema": "canonical_rational", "A": [[1, 1], [1, 1]], "b": [1, 2]});
    let (_, report) = certify(&none, json!({"x": [1, 0]}));
    assert_eq!(outcomes(&report), linear_outcomes([false, false, true]));
}

#[test]
fn a_decimal_anywhere_in_the_certificate_is_refused_before_the_types_are_read() {
    for spoiled in [
        json!({"phi": {"a": 0, "b": 1, "c": 3, "d": 2.0}}),
        json!({"phi": {"a": 0, "b": 1, "c": 3, "d": "2.0"}}),
        json!({"phi": {"a": 0, "b": 1, "c": 3, "d": 2}, "note": [{"k": [0.5]}]}),
        json!({"anything": 1e-3}),
    ] {
        float(&potential_task(), spoiled);
    }
    float(&dual_task(), dual_with("z", json!([1, 1, -1.5])));
    float(&linear_task(), json!({"x": ["1/2", 0.25]}));
    // A decimal outside the certificate is not the certificate's.
    let mut aside = reply(&potential_task(), phi());
    aside["confidence"] = json!(0.9);
    assert!(run(&potential_task(), vec![aside]).0);
}

#[test]
fn text_written_like_a_decimal_counts_as_one() {
    for text in [
        "1.5",
        "-1.5",
        "+1.5",
        ".5",
        "5.",
        ".",
        "-.",
        "+.5",
        "0.0",
        "1e3",
        "1E3",
        "1e+3",
        "1E-3",
        "-1e3",
        "+1e3",
        "1.5e3",
        "1.e3",
        "12.25E-10",
        "007e1",
    ] {
        float(&linear_task(), json!({"x": ["1/2", text]}));
    }
}

#[test]
fn text_that_only_resembles_a_decimal_is_left_to_the_type_gate() {
    for text in [
        "e5", "1e", "1e+", "1e-", ".e5", ".5e3", "1.5.2", "1e5e5", "1e5.0", "--1.5", "+-1.5",
        "1 .5", "1.5 ", "a.5", "1.b", "1x3", "1e3x", "1,5", "abc", "", "-", "+", "1/2.0x",
    ] {
        ill_typed(
            &linear_task(),
            reply(&linear_task(), json!({"x": ["1/2", text]})),
        );
    }
}

#[test]
fn a_reply_must_name_the_schema_of_the_task() {
    for named in [
        json!("l1_dual_circulation"),
        json!("canonical_rational"),
        json!("Coboundary_Potential"),
        json!(null),
        json!(["coboundary_potential"]),
    ] {
        let mut answer = reply(&potential_task(), phi());
        answer["schema"] = named;
        ill_typed(&potential_task(), answer);
    }
    ill_typed(&potential_task(), json!({"certificate": phi()}));
}

#[test]
fn a_certificate_has_exactly_the_fields_of_its_schema() {
    let typed = |task: &Value, certificate: Value| ill_typed(task, reply(task, certificate));
    typed(&potential_task(), json!({}));
    typed(
        &potential_task(),
        json!({"potential": {"a": 0, "b": 1, "c": 3, "d": 2}}),
    );
    let mut extra = phi();
    extra["note"] = json!("exact");
    typed(&potential_task(), extra);
    typed(&potential_task(), dual());
    for key in ["f", "r", "z"] {
        let mut short = dual();
        short.as_object_mut().expect("an object").remove(key);
        typed(&dual_task(), short.clone());
        short["phi"] = json!({});
        typed(&dual_task(), short);
    }
    typed(&dual_task(), dual_with("phi", json!({})));
    typed(&linear_task(), json!({"x": ["1/2", "1/3"], "y": []}));
    typed(&linear_task(), json!({"y": ["1/2", "1/3"]}));
}

#[test]
fn a_value_on_the_vertices_is_an_object_with_one_entry_per_vertex() {
    for written in [
        json!([0, 1, 3, 2]),
        json!({"a": 0, "b": 1, "c": 3}),
        json!({"a": 0, "b": 1, "c": 3, "d": 2, "e": 0}),
        json!({"a": 0, "b": 1, "c": 3, "e": 2}),
        json!("0132"),
        json!(null),
    ] {
        ill_typed(
            &potential_task(),
            reply(&potential_task(), json!({ "phi": written })),
        );
    }
    let off = dual_with("f", json!({"a": 0, "b": -3}));
    ill_typed(&dual_task(), reply(&dual_task(), off));
}

#[test]
fn a_value_on_the_edges_or_the_unknowns_is_a_list_of_the_right_length() {
    for written in [
        json!([0, 4]),
        json!([0, 4, 0, 0]),
        json!({"0": 0, "1": 4, "2": 0}),
        json!("040"),
    ] {
        for key in ["r", "z"] {
            let off = dual_with(key, written.clone());
            ill_typed(&dual_task(), reply(&dual_task(), off));
        }
    }
    for written in [
        json!(["1/2"]),
        json!(["1/2", "1/3", 0]),
        json!({"0": "1/2", "1": "1/3"}),
        json!([]),
    ] {
        ill_typed(
            &linear_task(),
            reply(&linear_task(), json!({ "x": written })),
        );
    }
}

#[test]
fn an_entry_is_an_integer_or_text_p_over_q() {
    for entry in [
        json!("x"),
        json!(null),
        json!(true),
        json!([1]),
        json!({"p": 1, "q": 2}),
        json!("1/0"),
        json!("1/02"),
        json!("1/00"),
        json!(" 1"),
        json!("+1"),
        json!("1/-2"),
        json!("1/2/3"),
        json!("/2"),
        json!("1/"),
    ] {
        let mut on_vertices = phi();
        on_vertices["phi"]["d"] = entry.clone();
        ill_typed(&potential_task(), reply(&potential_task(), on_vertices));
        let on_edges = dual_with("r", json!([0, entry, 0]));
        ill_typed(&dual_task(), reply(&dual_task(), on_edges));
        ill_typed(
            &linear_task(),
            reply(&linear_task(), json!({"x": ["1/2", entry]})),
        );
    }
    // A denominator may have a zero after its first digit, and a numerator may start with one.
    let tenth = json!({"schema": "canonical_rational", "A": [[10]], "b": [1]});
    assert!(certify(&tenth, json!({"x": ["1/10"]})).0);
    let (_, report) = certify(&tenth, json!({"x": ["01/10"]}));
    assert_eq!(outcomes(&report), linear_outcomes([true, true, false]));
}

#[test]
fn a_reply_without_a_certificate_object_is_malformed() {
    for answer in [
        json!({"schema": "coboundary_potential"}),
        json!({"schema": "coboundary_potential", "certificate": [0, 1, 3, 2]}),
        json!({"schema": "coboundary_potential", "certificate": "phi"}),
        json!({"schema": "coboundary_potential", "certificate": null}),
        json!([phi()]),
        json!("certificate"),
    ] {
        assert_eq!(malformed(&potential_task(), vec![answer]), "certificate");
    }
}

#[test]
fn a_task_must_name_a_registered_schema() {
    for schema in [
        json!("other"),
        json!(null),
        json!(5),
        json!(["coboundary_potential"]),
    ] {
        let mut task = potential_task();
        task["schema"] = schema;
        assert_eq!(bad_task(task), "unknown certificate schema");
    }
    assert_eq!(
        bad_task(json!({"edges": [], "c": []})),
        "unknown certificate schema"
    );
}

#[test]
fn a_graph_task_needs_text_edges_and_one_value_per_edge() {
    for mut task in [potential_task(), dual_task()] {
        let key = if task["schema"] == "coboundary_potential" {
            "c"
        } else {
            "w"
        };
        let reason = format!("{key} must be one exact rational per edge");
        for values in [
            json!([1]),
            json!([1, 2, 3, 4, 5, 6]),
            json!(null),
            json!("12"),
        ] {
            let mut off = task.clone();
            off[key] = values;
            assert_eq!(bad_task(off), reason);
        }
        let mut decimal = task.clone();
        decimal[key][0] = json!(0.5);
        assert_eq!(bad_task(decimal), reason);
        task["edges"] = json!([[0, 1], [1, 2], [0, 2]]);
        assert_eq!(bad_task(task), "edges must be a list of pairs of text");
    }
}

#[test]
fn caps_when_given_are_one_per_edge() {
    for caps in [
        json!([1]),
        json!([1, 1, 1, 1]),
        json!([1, 1, 0.5]),
        json!(null),
        json!("111"),
    ] {
        let mut task = dual_task();
        task["cap"] = caps;
        assert_eq!(bad_task(task), "cap must be one exact rational per edge");
    }
}

#[test]
fn a_linear_task_is_read_as_wf7_reads_it() {
    let with = |key: &str, value: Value| {
        let mut task = linear_task();
        task[key] = value;
        bad_task(task)
    };
    assert_eq!(with("A", json!([])), "A must be a nonempty list of rows");
    assert_eq!(
        with("A", json!([[2, 0.5], [0, 3]])),
        "every row of A must be a list of exact rationals"
    );
    assert_eq!(
        with("b", json!("11")),
        "b must be a list of exact rationals"
    );
    assert_eq!(
        with("b", json!([1])),
        "A must be rectangular, with a column, and match b"
    );
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&potential_task(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}
