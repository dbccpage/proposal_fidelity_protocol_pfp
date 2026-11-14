//! The exact-domain checkers: each one's true answer, and what it will not read.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-domains-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::domains::{checker, permutation, DOMAINS, MAX_POINTS};
use serde_json::{json, Value};

/// Whether the reply passed and the witness as canonical text, or the reason it was unreadable.
fn check(domain: &str, data: Value, answer: Value) -> Result<(bool, String), String> {
    let run = checker(domain).expect("a registered domain");
    let data = Datum::parse(&data.to_string()).expect("data");
    let answer = Datum::parse(&answer.to_string()).expect("answer");
    run(&data, &answer).map(|(passed, witness)| (passed, witness.canonical()))
}

fn passes(domain: &str, data: Value, answer: Value) -> bool {
    check(domain, data, answer).expect("readable").0
}

fn reason(domain: &str, data: Value, answer: Value) -> String {
    check(domain, data, answer).expect_err("unreadable")
}

#[test]
fn the_host_has_exactly_four_domains() {
    let names: Vec<&str> = DOMAINS.iter().map(|(name, _)| *name).collect();
    assert_eq!(
        names,
        [
            "group_commutator",
            "linear_refusal",
            "stabilizer_commutation",
            "u1_anomaly"
        ]
    );
    for name in names {
        assert!(checker(name).is_some());
    }
    assert!(checker("regge_deficit").is_none());
    assert!(checker("").is_none());
    assert!(checker("U1_ANOMALY").is_none());
    assert_eq!(MAX_POINTS, 8);
}

#[test]
fn each_name_runs_its_own_checker() {
    let anomaly = json!({"linear": 0, "cubic": 0, "anomaly_free": true});
    assert!(passes(
        "u1_anomaly",
        json!({"charges": [1, -1]}),
        anomaly.clone()
    ));
    assert_eq!(
        reason(
            "stabilizer_commutation",
            json!({"charges": [1, -1]}),
            anomaly.clone()
        ),
        "generators must be Pauli strings of one length"
    );
    assert_eq!(
        reason(
            "group_commutator",
            json!({"charges": [1, -1]}),
            anomaly.clone()
        ),
        "n must be an exact integer from 1 to 8"
    );
    assert_eq!(
        reason("linear_refusal", json!({"charges": [1, -1]}), anomaly),
        "A must be a nonempty list of rows"
    );
}

fn five_qubit() -> Value {
    json!({"generators": ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"]})
}

#[test]
fn commuting_stabilizers_have_no_anticommuting_pair() {
    assert_eq!(
        check(
            "stabilizer_commutation",
            five_qubit(),
            json!({"anticommuting": []})
        ),
        Ok((true, r#"{"anticommuting":[]}"#.to_owned()))
    );
    assert!(!passes(
        "stabilizer_commutation",
        five_qubit(),
        json!({"anticommuting": [[0, 1]]})
    ));
}

#[test]
fn the_anticommuting_pairs_are_found_by_the_symplectic_product() {
    let data = json!({"generators": ["XXI", "ZZI", "IXZ", "ZII"]});
    let truth = json!({"anticommuting": [[0, 3], [1, 2]]});
    assert_eq!(
        check("stabilizer_commutation", data.clone(), truth),
        Ok((true, r#"{"anticommuting":[[0,3],[1,2]]}"#.to_owned()))
    );
    for wrong in [
        json!([]),
        json!([[0, 3]]),
        json!([[1, 2]]),
        json!([[0, 3], [1, 2], [0, 1]]),
        json!([[0, 3], [1, 2], [1, 2]]),
        json!([[0, 3], [1, 3]]),
    ] {
        // The witness of a wrong reply is the true answer, not what the reply said.
        assert_eq!(
            check(
                "stabilizer_commutation",
                data.clone(),
                json!({ "anticommuting": wrong })
            ),
            Ok((false, r#"{"anticommuting":[[0,3],[1,2]]}"#.to_owned()))
        );
    }
}

#[test]
fn pairs_may_come_in_any_order_and_either_way_round() {
    let data = json!({"generators": ["XXI", "ZZI", "IXZ", "ZII"]});
    assert!(passes(
        "stabilizer_commutation",
        data.clone(),
        json!({"anticommuting": [[2, 1], [3, 0]]})
    ));
    assert!(passes(
        "stabilizer_commutation",
        data,
        json!({"anticommuting": [[1, 2], [0, 3]]})
    ));
}

#[test]
fn each_pauli_letter_pair_commutes_or_not_as_it_should() {
    let anticommuting = |a: &str, b: &str| {
        check(
            "stabilizer_commutation",
            json!({"generators": [a, b]}),
            json!({"anticommuting": [[0, 1]]}),
        )
        .expect("readable")
        .0
    };
    for (a, b) in [
        ("X", "Z"),
        ("Z", "X"),
        ("X", "Y"),
        ("Y", "X"),
        ("Y", "Z"),
        ("Z", "Y"),
    ] {
        assert!(anticommuting(a, b), "{a} {b}");
    }
    for (a, b) in [
        ("X", "X"),
        ("Y", "Y"),
        ("Z", "Z"),
        ("I", "X"),
        ("I", "Y"),
        ("Z", "I"),
        ("I", "I"),
    ] {
        assert!(!anticommuting(a, b), "{a} {b}");
    }
    assert!(!anticommuting("XX", "ZZ"));
    assert!(anticommuting("XXX", "ZZZ"));
    assert!(anticommuting("XI", "ZZ"));
}

#[test]
fn generators_must_be_pauli_strings_of_one_length() {
    let bad = "generators must be Pauli strings of one length";
    let answer = json!({"anticommuting": []});
    for data in [
        json!({}),
        json!({"generators": []}),
        json!({"generators": "XZ"}),
        json!({"generators": ["XZ", "X"]}),
        json!({"generators": ["X", "XZ"]}),
        json!({"generators": ["XA"]}),
        json!({"generators": ["xz"]}),
        json!({"generators": ["XZ", 7]}),
        json!({"generators": [["X", "Z"]]}),
    ] {
        assert_eq!(reason("stabilizer_commutation", data, answer.clone()), bad);
    }
    assert!(passes(
        "stabilizer_commutation",
        json!({"generators": ["XYZI"]}),
        answer.clone()
    ));
    assert!(passes(
        "stabilizer_commutation",
        json!({"generators": ["", ""]}),
        answer
    ));
}

#[test]
fn an_anticommuting_reply_is_a_list_of_pairs_of_exact_integers() {
    let data = json!({"generators": ["X", "Z"]});
    let reason = |answer: Value| reason("stabilizer_commutation", data.clone(), answer);
    assert_eq!(reason(json!({})), "anticommuting list required");
    assert_eq!(reason(json!([[0, 1]])), "anticommuting list required");
    assert_eq!(
        reason(json!({"anticommuting": "0,1"})),
        "anticommuting list required"
    );
    assert_eq!(reason(json!({"anticommuting": [[0]]})), "pairs are [i, j]");
    assert_eq!(
        reason(json!({"anticommuting": [[0, 1, 2]]})),
        "pairs are [i, j]"
    );
    assert_eq!(reason(json!({"anticommuting": [7]})), "pairs are [i, j]");
    assert_eq!(
        reason(json!({"anticommuting": [[0, 1.0]]})),
        "pair must be an exact int"
    );
    assert_eq!(
        reason(json!({"anticommuting": [["0", 1]]})),
        "pair must be an exact int"
    );
    assert!(!passes(
        "stabilizer_commutation",
        data.clone(),
        json!({"anticommuting": [[0, -1]]})
    ));
    assert!(passes(
        "stabilizer_commutation",
        data,
        json!({"anticommuting": [[1, 0]]})
    ));
}

#[test]
fn the_anomaly_sums_are_exact() {
    let data = json!({"charges": [1, 5, -7, -8, 9]});
    assert_eq!(
        check(
            "u1_anomaly",
            data.clone(),
            json!({"linear": 0, "cubic": 0, "anomaly_free": true})
        ),
        Ok((true, r#"{"cubic":"0","linear":"0"}"#.to_owned()))
    );
    let data = json!({"charges": [1, 2, "1/2"]});
    assert_eq!(
        check(
            "u1_anomaly",
            data.clone(),
            json!({"linear": "7/2", "cubic": "73/8", "anomaly_free": false})
        ),
        Ok((true, r#"{"cubic":"73/8","linear":"7/2"}"#.to_owned()))
    );
    for wrong in [
        json!({"linear": "7/2", "cubic": "73/8", "anomaly_free": true}),
        json!({"linear": 3, "cubic": "73/8", "anomaly_free": false}),
        json!({"linear": "7/2", "cubic": 9, "anomaly_free": false}),
        json!({"linear": "73/8", "cubic": "7/2", "anomaly_free": false}),
    ] {
        assert!(!passes("u1_anomaly", data.clone(), wrong));
    }
    assert!(passes(
        "u1_anomaly",
        data,
        json!({"linear": "14/4", "cubic": "146/16", "anomaly_free": false})
    ));
}

#[test]
fn anomaly_freedom_needs_both_sums_to_vanish() {
    let free = |charges: Value, linear: Value, cubic: Value, claim: bool| {
        passes(
            "u1_anomaly",
            json!({ "charges": charges }),
            json!({"linear": linear, "cubic": cubic, "anomaly_free": claim}),
        )
    };
    assert!(free(json!([1, -1]), json!(0), json!(0), true));
    assert!(!free(json!([1, -1]), json!(0), json!(0), false));
    assert!(free(json!([2, -1, -1]), json!(0), json!(6), false));
    assert!(!free(json!([2, -1, -1]), json!(0), json!(6), true));
    assert!(free(json!([3]), json!(3), json!(27), false));
    assert!(!free(json!([3]), json!(3), json!(27), true));
    assert!(free(json!([-2]), json!(-2), json!(-8), false));
    // 1^3 + 12^3 = 9^3 + 10^3: the cubes cancel and the charges do not.
    assert!(free(json!([1, 12, -9, -10]), json!(-6), json!(0), false));
    assert!(!free(json!([1, 12, -9, -10]), json!(-6), json!(0), true));
    assert!(free(json!([0]), json!(0), json!(0), true));
}

#[test]
fn the_anomaly_checker_reads_exact_rationals_only() {
    let answer = json!({"linear": 0, "cubic": 0, "anomaly_free": true});
    for data in [json!({}), json!({"charges": []}), json!({"charges": 3})] {
        assert_eq!(
            reason("u1_anomaly", data, answer.clone()),
            "charges required"
        );
    }
    for data in [json!({"charges": [1, 0.5]}), json!({"charges": [1, "x"]})] {
        assert_eq!(
            reason("u1_anomaly", data, answer.clone()),
            "charge must be an exact rational"
        );
    }
    let data = json!({"charges": [1, -1]});
    let reason = |answer: Value| reason("u1_anomaly", data.clone(), answer);
    assert_eq!(
        reason(json!({"linear": 0, "cubic": 0})),
        "anomaly_free bool required"
    );
    assert_eq!(
        reason(json!({"linear": 0, "cubic": 0, "anomaly_free": "true"})),
        "anomaly_free bool required"
    );
    assert_eq!(reason(json!([0, 0, true])), "anomaly_free bool required");
    assert_eq!(
        reason(json!({"cubic": 0, "anomaly_free": true})),
        "linear must be an exact rational"
    );
    assert_eq!(
        reason(json!({"linear": 0.0, "cubic": 0, "anomaly_free": true})),
        "linear must be an exact rational"
    );
    assert_eq!(
        reason(json!({"linear": 0, "anomaly_free": true})),
        "cubic must be an exact rational"
    );
    assert_eq!(
        reason(json!({"linear": 0, "cubic": [0], "anomaly_free": true})),
        "cubic must be an exact rational"
    );
}

#[test]
fn the_commutator_is_g_inverse_h_inverse_g_h_in_reading_order() {
    let data = json!({"n": 4, "g": [1, 0, 2, 3], "h": [0, 2, 1, 3]});
    assert_eq!(
        check(
            "group_commutator",
            data.clone(),
            json!({"commutator": [1, 2, 0, 3]})
        ),
        Ok((true, r#"{"commutator":[1,2,0,3]}"#.to_owned()))
    );
    assert_eq!(
        check(
            "group_commutator",
            data.clone(),
            json!({"commutator": [2, 0, 1, 3]})
        ),
        Ok((false, r#"{"commutator":[1,2,0,3]}"#.to_owned()))
    );
    assert!(!passes(
        "group_commutator",
        data,
        json!({"commutator": [0, 1, 2, 3]})
    ));
    let cycles = json!({"n": 3, "g": [1, 2, 0], "h": [1, 0, 2]});
    assert!(passes(
        "group_commutator",
        cycles,
        json!({"commutator": [1, 2, 0]})
    ));
    let commuting = json!({"n": 3, "g": [1, 2, 0], "h": [2, 0, 1]});
    assert!(passes(
        "group_commutator",
        commuting,
        json!({"commutator": [0, 1, 2]})
    ));
}

#[test]
fn a_commutator_item_permutes_one_to_eight_points() {
    let answer = json!({"commutator": [0]});
    let range = "n must be an exact integer from 1 to 8";
    for n in [
        json!(0),
        json!(9),
        json!(-1),
        json!(2.0),
        json!("2"),
        Value::Null,
    ] {
        let data = json!({"n": n, "g": [0], "h": [0]});
        assert_eq!(reason("group_commutator", data, answer.clone()), range);
    }
    assert_eq!(
        reason(
            "group_commutator",
            json!({"g": [0], "h": [0]}),
            answer.clone()
        ),
        range
    );
    assert!(passes(
        "group_commutator",
        json!({"n": 1, "g": [0], "h": [0]}),
        answer
    ));
    let eight = json!([1, 0, 2, 3, 4, 5, 6, 7]);
    assert!(passes(
        "group_commutator",
        json!({"n": 8, "g": eight, "h": eight}),
        json!({"commutator": [0, 1, 2, 3, 4, 5, 6, 7]})
    ));
}

#[test]
fn every_permutation_of_a_commutator_item_is_read_strictly() {
    let answer = json!({"commutator": [0, 1]});
    assert_eq!(
        reason(
            "group_commutator",
            json!({"n": 2, "g": [0, 0], "h": [0, 1]}),
            answer.clone()
        ),
        "g must be a permutation of 2 points"
    );
    assert_eq!(
        reason(
            "group_commutator",
            json!({"n": 2, "h": [0, 1]}),
            answer.clone()
        ),
        "g must be a permutation of 2 points"
    );
    assert_eq!(
        reason(
            "group_commutator",
            json!({"n": 2, "g": [0, 1], "h": [0, 1, 2]}),
            answer
        ),
        "h must be a permutation of 2 points"
    );
    let data = json!({"n": 2, "g": [0, 1], "h": [1, 0]});
    for answer in [
        json!({}),
        json!([0, 1]),
        json!({"commutator": [0]}),
        json!({"commutator": [1, 1]}),
        json!({"commutator": "01"}),
    ] {
        assert_eq!(
            reason("group_commutator", data.clone(), answer),
            "commutator must be a permutation of 2 points"
        );
    }
}

#[test]
fn a_named_permutation_is_read_from_its_holder() {
    let holder = Datum::parse(r#"{"p": [1, 0, 2], "q": [0, 0, 1]}"#).expect("holder");
    assert_eq!(permutation(&holder, "p", 3), Ok(vec![1, 0, 2]));
    assert_eq!(
        permutation(&holder, "q", 3),
        Err("q must be a permutation of 3 points".to_owned())
    );
    assert_eq!(
        permutation(&holder, "r", 3),
        Err("r must be a permutation of 3 points".to_owned())
    );
    assert_eq!(
        permutation(&holder, "p", 4),
        Err("p must be a permutation of 4 points".to_owned())
    );
    assert_eq!(
        permutation(&Datum::Null, "p", 0),
        Err("p must be a permutation of 0 points".to_owned())
    );
}

#[test]
fn a_linear_item_is_graded_by_the_rank_test() {
    let unique = json!({"A": [[1, 1], [1, -1]], "b": [3, 1]});
    assert_eq!(
        check("linear_refusal", unique.clone(), json!({"answer": [2, 1]})),
        Ok((
            true,
            r#"{"code":"CERTIFIED","n":2,"rank_A":2,"rank_Ab":2,"status":"unique"}"#.to_owned()
        ))
    );
    assert_eq!(
        check("linear_refusal", unique.clone(), json!({"answer": [1, 2]})),
        Ok((
            false,
            r#"{"code":"ANSWER_EQUALS_UNIQUE_SOLUTION","n":2,"rank_A":2,"rank_Ab":2,"status":"unique"}"#
                .to_owned()
        ))
    );
    assert_eq!(
        check(
            "linear_refusal",
            unique,
            json!({"refusal": "UNRESOLVED_INCONSISTENT"})
        ),
        Ok((
            false,
            r#"{"code":"FALSE_REFUSAL","n":2,"rank_A":2,"rank_Ab":2,"status":"unique"}"#.to_owned()
        ))
    );
    let inconsistent = json!({"A": [[1, 1], [2, 2]], "b": [3, 7]});
    assert_eq!(
        check(
            "linear_refusal",
            inconsistent.clone(),
            json!({"refusal": "UNRESOLVED_INCONSISTENT"})
        ),
        Ok((
            true,
            r#"{"code":"UNRESOLVED_INCONSISTENT","n":2,"rank_A":1,"rank_Ab":2,"status":"inconsistent"}"#
                .to_owned()
        ))
    );
    assert_eq!(
        check(
            "linear_refusal",
            inconsistent.clone(),
            json!({"refusal": "UNRESOLVED_UNDERDETERMINED"})
        )
        .map(|(passed, _)| passed),
        Ok(false)
    );
    assert_eq!(
        check("linear_refusal", inconsistent, json!({"answer": [1, 2]})),
        Ok((
            false,
            r#"{"code":"BLUFF","n":2,"rank_A":1,"rank_Ab":2,"status":"inconsistent"}"#.to_owned()
        ))
    );
}

#[test]
fn a_linear_item_that_cannot_be_read_gives_its_reason() {
    assert_eq!(
        reason(
            "linear_refusal",
            json!({"A": [[1, 2], [3]], "b": [1, 2]}),
            json!({"answer": [1]})
        ),
        "A must be rectangular, with a column, and match b"
    );
    let data = json!({"A": [[1]], "b": [1]});
    assert_eq!(
        reason("linear_refusal", data.clone(), json!([1])),
        "the reply must be an object"
    );
    assert_eq!(
        reason("linear_refusal", data, json!({"answer": [0.5]})),
        "answer must be a list of exact rationals"
    );
}
