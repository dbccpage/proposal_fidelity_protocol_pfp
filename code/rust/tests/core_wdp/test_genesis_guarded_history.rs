//! Guarded Source-25 histories: admission parity with the Python reference,
//! the P.18 family, a guarded kind-compatible family with replayed coherence
//! witnesses, a within-component H1 counterexample, and negative controls.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::homology_basis::homology_basis;
use linear_algebra::proof::{ReplayHash, TheoremId, TheoremProvenance};
use num_rational::{BigRational, Rational64};
use num_traits::{One, Zero};
use core_wdp::genesis_guarded_history::{
    analyze_legal_set, descriptors, evaluate_problem, guarded_certificate, kind_compatible,
    kind_sorted_extension, kind_sorted_order, legal_extensions, native_refusal, parse_problem,
    replacement_kind, schedules, AdmissionRefusal, GuardedHistoryError, Json, Replacement,
    ReplacementKind, ReplayRefusal, StarCoherence, SwapComplex,
};
use core_wdp::genesis_source_execution::{Source25Change, SourceRelation};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::path::PathBuf;

fn fixture(name: &str) -> Vec<u8> {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_wdp/fixtures/causal_certificates");
    std::fs::read(path.join(name)).expect("checked-in causal fixture")
}

fn change_json(change: &Source25Change) -> Json {
    let relation = |r: &SourceRelation| match r {
        SourceRelation::R => Json::text("r"),
        SourceRelation::S => Json::text("s"),
    };
    match change {
        Source25Change::AddTerm => Json::object([("kind", Json::text("add_term"))]),
        Source25Change::Identify { x, y } => Json::object([
            ("kind", Json::text("identify")),
            ("x", Json::natural(*x)),
            ("y", Json::natural(*y)),
        ]),
        Source25Change::Fill { x, y, z } => Json::object([
            ("kind", Json::text("fill")),
            ("x", Json::natural(*x)),
            ("y", Json::natural(*y)),
            ("z", Json::natural(*z)),
        ]),
        Source25Change::Remove { relation: r, x, y } => Json::object([
            ("kind", Json::text("remove")),
            ("relation", relation(r)),
            ("x", Json::natural(*x)),
            ("y", Json::natural(*y)),
        ]),
        Source25Change::AddAssertion { relation: r, x, y } => Json::object([
            ("kind", Json::text("add_assertion")),
            ("relation", relation(r)),
            ("x", Json::natural(*x)),
            ("y", Json::natural(*y)),
        ]),
    }
}

/// SHA-256 of `json.dumps([[order, descriptors(order)] ...], sort_keys=True,
/// separators=(",", ":"))` over all schedules, as `check_causal_execution.py`
/// computes them (Python 3.12, recorded 2026-10-06).
fn descriptor_digest(bytes: &[u8]) -> (usize, String) {
    let problem = parse_problem(bytes).unwrap();
    let orders = schedules(problem.before()).unwrap();
    let rows: Vec<Json> = orders
        .iter()
        .map(|order| {
            Json::Arr(vec![
                Json::naturals(order),
                Json::Arr(
                    descriptors(&problem, order)
                        .unwrap()
                        .iter()
                        .map(change_json)
                        .collect(),
                ),
            ])
        })
        .collect();
    let text = Json::Arr(rows).to_canonical();
    (orders.len(), hex::encode(Sha256::digest(text.as_bytes())))
}

#[test]
fn token_translation_matches_python_on_retained_problems() {
    let five = fixture("five_edit_problem.json");
    let (count, digest) = descriptor_digest(&five);
    assert_eq!(count, 24);
    assert_eq!(
        digest,
        "392e2c5a91afb561d41a97a61a79e0ce566a5efc8778c805178f81cb579d2449"
    );
    let problem = parse_problem(&five).unwrap();
    assert_eq!(problem.before(), &[0, 0, 0, 3, 7, 11, 63]);
    // The relabelled order of the Python listing's last schedule.
    let last = descriptors(&problem, &[2, 1, 0, 4, 3, 5, 6]).unwrap();
    assert_eq!(last[3], Source25Change::Fill { x: 1, y: 3, z: 2 });
    assert_eq!(last[6], Source25Change::Identify { x: 2, y: 3 });
    let (count, digest) = descriptor_digest(&fixture("antichain_problem.json"));
    assert_eq!(count, 24);
    assert_eq!(
        digest,
        "a93ca037077fa9b5116ebbf93e68ee5d2c501fe870910a0b833cf81cd7ffbe11"
    );
}

#[test]
fn retained_all_order_problems_are_all_legal_and_star_shaped() {
    for name in ["five_edit_problem.json", "antichain_problem.json"] {
        let problem = parse_problem(&fixture(name)).unwrap();
        let orders = schedules(problem.before()).unwrap();
        for order in &orders {
            assert_eq!(
                native_refusal(&problem, order).unwrap(),
                None,
                "{name} {order:?}"
            );
        }
        let legal = legal_extensions(&problem).unwrap();
        assert_eq!(legal, orders.iter().cloned().collect::<BTreeSet<_>>());
        let evaluation = evaluate_problem(problem).unwrap();
        assert!(evaluation.refused.is_empty());
        assert_eq!(evaluation.analysis.h1_ranks, vec![0]);
        assert!(evaluation.analysis.star_base.is_some());
    }
}

fn problem_bytes(initial_r: &str, events: &str) -> Vec<u8> {
    format!(
        r#"{{"schema":"wdp-causal-problem-v1","initial":{{"terms":["t0"],"r":["{initial_r}"],"s":["0"],"filled":[]}},"initial_tokens":["u"],"events":[{events}],"protected_prices":["term_additions","assertion_additions"]}}"#
    )
    .into_bytes()
}

fn edit(tag: &str, kind: &str, relation: &str, preds: &[&str]) -> String {
    let preds: Vec<String> = preds.iter().map(|p| format!("\"{p}\"")).collect();
    format!(
        r#"{{"tag":"{tag}","kind":"{kind}","relation":"{relation}","tokens":["u","u"],"predecessors":[{}]}}"#,
        preds.join(",")
    )
}

fn p18() -> Vec<u8> {
    let events = [
        edit("p", "add_assertion", "r", &[]),
        edit("x", "remove", "r", &[]),
        edit("a", "add_assertion", "r", &["x"]),
        edit("y", "remove", "r", &[]),
        edit("b", "add_assertion", "r", &["y"]),
    ];
    problem_bytes("0", &events.join(","))
}

#[test]
fn p18_family_has_two_isolated_legal_histories() {
    let certificate = guarded_certificate(&p18(), 3).unwrap();
    let legal = certificate.get("legal_orders").unwrap();
    assert_eq!(
        *legal,
        Json::Arr(vec![
            Json::naturals(&[0, 1, 2, 3, 4]),
            Json::naturals(&[0, 3, 4, 1, 2])
        ])
    );
    assert_eq!(
        certificate.get("linear_extensions"),
        Some(&Json::natural(30))
    );
    assert_eq!(certificate.get("edges"), Some(&Json::natural(0)));
    let Some(Json::Arr(components)) = certificate.get("components") else {
        panic!("components missing");
    };
    assert_eq!(components.len(), 2);
    assert_eq!(certificate.get("kind_compatible"), Some(&Json::Bool(false)));
    assert_eq!(certificate.get("star_base"), Some(&Json::Null));
    assert_eq!(
        certificate.get("coherence_witnesses"),
        Some(&Json::Arr(vec![]))
    );
    assert_eq!(certificate.get("separating_cocycle"), Some(&Json::Null));
    let Some(Json::Arr(refused)) = certificate.get("refused_orders") else {
        panic!("refusals missing");
    };
    assert_eq!(refused.len(), 28);
    assert!(certificate.to_canonical().is_ascii());
}

fn guarded_compatible() -> Vec<u8> {
    let events = [
        edit("x", "remove", "r", &[]),
        edit("y", "remove", "r", &[]),
        edit("a", "add_assertion", "r", &[]),
        edit("s", "add_assertion", "s", &[]),
    ];
    problem_bytes("1", &events.join(","))
}

fn replacements(witness: &Json) -> Vec<Replacement> {
    let Some(Json::Arr(items)) = witness.get("replacements") else {
        panic!("replacements missing");
    };
    let naturals = |v: &Json| -> Vec<usize> {
        let Json::Arr(xs) = v else { panic!("array") };
        xs.iter()
            .map(|x| match x {
                Json::Int(n) => usize::try_from(*n).unwrap(),
                _ => panic!("natural"),
            })
            .collect()
    };
    items
        .iter()
        .map(|r| {
            let before = naturals(r.get("before").unwrap());
            let after = naturals(r.get("after").unwrap());
            let kind = replacement_kind(&before, &after).unwrap();
            assert_eq!(r.get("kind"), Some(&Json::text(kind.wire())));
            let Some(Json::Int(offset)) = r.get("offset") else {
                panic!("offset");
            };
            Replacement {
                kind,
                offset: usize::try_from(*offset).unwrap(),
                before,
                after,
            }
        })
        .collect()
}

fn naturals_of(v: Option<&Json>) -> Vec<usize> {
    let Some(Json::Arr(xs)) = v else {
        panic!("array")
    };
    xs.iter()
        .map(|x| match x {
            Json::Int(n) => usize::try_from(*n).unwrap(),
            _ => panic!("natural"),
        })
        .collect()
}

#[test]
fn guarded_kind_compatible_family_is_coherent_from_its_kind_sorted_base() {
    let bytes = guarded_compatible();
    let problem = parse_problem(&bytes).unwrap();
    assert!(kind_compatible(&problem));
    let orders = schedules(problem.before()).unwrap();
    assert_eq!(kind_sorted_order(&problem), Some(vec![2, 3, 0, 1]));
    assert_eq!(
        kind_sorted_extension(&problem, &orders),
        Some(vec![2, 3, 0, 1])
    );
    // Equal-rank precedence (Remove before Remove) stays compatible.
    let chained = guarded_compatible()
        .iter()
        .map(|&b| b as char)
        .collect::<String>()
        .replacen(
            r#""tag":"y","kind":"remove","relation":"r","tokens":["u","u"],"predecessors":[]"#,
            r#""tag":"y","kind":"remove","relation":"r","tokens":["u","u"],"predecessors":["x"]"#,
            1,
        );
    let chained = parse_problem(chained.as_bytes()).unwrap();
    assert_eq!(chained.before()[1], 1);
    assert!(kind_compatible(&chained));
    assert_eq!(kind_sorted_order(&chained), Some(vec![2, 3, 0, 1]));
    let reversed = parse_problem(&problem_bytes(
        "1",
        &[
            edit("x", "remove", "r", &[]),
            edit("a", "add_assertion", "r", &["x"]),
        ]
        .join(","),
    ))
    .unwrap();
    assert!(!kind_compatible(&reversed));
    assert_eq!(kind_sorted_order(&reversed), None);
    let certificate = guarded_certificate(&bytes, 3).unwrap();
    assert_eq!(
        certificate.get("star_base"),
        Some(&Json::naturals(&[2, 3, 0, 1]))
    );
    let Some(Json::Arr(refused)) = certificate.get("refused_orders") else {
        panic!("refusals missing");
    };
    assert_eq!(refused.len(), 8);
    let Some(Json::Arr(components)) = certificate.get("components") else {
        panic!("components missing");
    };
    assert_eq!(components.len(), 1);
    assert_eq!(components[0].get("h1_rank"), Some(&Json::natural(0)));
    let Some(Json::Arr(witnesses)) = certificate.get("coherence_witnesses") else {
        panic!("witnesses missing");
    };
    assert_eq!(witnesses.len(), 3);

    let legal: BTreeSet<Vec<usize>> = legal_extensions(&problem).unwrap();
    assert_eq!(legal.len(), 16);
    let complex = SwapComplex::new(4, &legal).unwrap();
    for witness in witnesses {
        let source = naturals_of(witness.get("source_order"));
        let target = naturals_of(witness.get("target_order"));
        let first = naturals_of(witness.get("source_word"));
        let second = naturals_of(witness.get("target_word"));
        assert_ne!(first, second);
        let moves = replacements(witness);
        assert!(moves.iter().any(|m| m.kind != ReplacementKind::Backtrack));
        complex
            .replay_replacements(&source, &target, &first, &second, &moves)
            .unwrap();
        // Mutating one offset must be refused.
        let mut shifted = moves.clone();
        let k = shifted
            .iter()
            .position(|m| m.kind != ReplacementKind::Backtrack)
            .unwrap();
        shifted[k].offset += 1;
        assert!(complex
            .replay_replacements(&source, &target, &first, &second, &shifted)
            .is_err());
        // Swapping a braid for a square of the same letters is not local.
        let mut relabelled = moves.clone();
        relabelled[k].kind = if moves[k].kind == ReplacementKind::Square {
            ReplacementKind::Braid
        } else {
            ReplacementKind::Square
        };
        assert_eq!(
            complex.replay_replacements(&source, &target, &first, &second, &relabelled),
            Err(ReplayRefusal::KindMismatch)
        );
    }
}

#[test]
fn coherence_witness_never_leaves_the_legal_orders() {
    let problem = parse_problem(&guarded_compatible()).unwrap();
    let legal = legal_extensions(&problem).unwrap();
    let complex = SwapComplex::new(4, &legal).unwrap();
    // A refused order is not a star base; the kind-sorted one is.
    assert!(StarCoherence::new(&complex, &[0, 1, 2, 3]).is_err());
    let mut coherence = StarCoherence::new(&complex, &[2, 3, 0, 1]).unwrap();
    for pair in complex.witness_pairs(0, 50).unwrap() {
        let moves = coherence
            .witness(pair.source, &pair.first, &pair.second)
            .unwrap();
        let target = complex.replay_word(pair.source, &pair.first).unwrap();
        // Replay every intermediate word independently.
        let mut word = pair.first.clone();
        for m in &moves {
            assert_eq!(&word[m.offset..m.offset + m.before.len()], &m.before[..]);
            word.splice(m.offset..m.offset + m.before.len(), m.after.iter().copied());
            assert_eq!(complex.replay_word(pair.source, &word), Ok(target));
        }
        assert_eq!(word, pair.second);
    }
    // A word through a refused order is refused before any replacement.
    let start = complex.index_of(&[0, 2, 1, 3]).unwrap();
    assert_eq!(
        complex.replay_word(start, &[1]),
        Err(ReplayRefusal::IllegalIntermediate)
    );
}

fn three_chain() -> Vec<u8> {
    let events = [
        edit("x1", "remove", "r", &[]),
        edit("a1", "add_assertion", "r", &["x1"]),
        edit("x2", "remove", "r", &[]),
        edit("a2", "add_assertion", "r", &["x2"]),
        edit("x3", "remove", "r", &[]),
        edit("a3", "add_assertion", "r", &["x3"]),
    ];
    problem_bytes("2", &events.join(","))
}

fn rational(text: &str) -> BigRational {
    match text.split_once('/') {
        Some((p, q)) => BigRational::new(p.parse().unwrap(), q.parse().unwrap()),
        None => BigRational::from_integer(text.parse().unwrap()),
    }
}

/// Independent replay of the full boundary matrices through `homology_basis`.
fn homology_rank_by_basis(complex: &SwapComplex, c: usize) -> usize {
    let vertices = &complex.components()[c];
    let edges = complex.component_edges(c);
    let faces = complex.component_faces(c);
    let vpos: BTreeMap<usize, usize> = vertices.iter().enumerate().map(|(i, &v)| (v, i)).collect();
    let epos: BTreeMap<usize, usize> = edges.iter().enumerate().map(|(i, &e)| (e, i)).collect();
    let (nv, ne, nf) = (vertices.len(), edges.len(), faces.len());
    let mut d1 = vec![Rational64::zero(); nv * ne];
    for (j, &e) in edges.iter().enumerate() {
        d1[vpos[&complex.edges()[e].0] * ne + j] = -Rational64::one();
        d1[vpos[&complex.head(e).unwrap()] * ne + j] = Rational64::one();
    }
    let mut d2 = vec![Rational64::zero(); ne * nf];
    for (j, &f) in faces.iter().enumerate() {
        for &(e, s) in &complex.faces()[f].boundary {
            d2[epos[&e] * nf + j] += Rational64::from_integer(i64::from(s));
        }
    }
    let provenance = TheoremProvenance::DerivedFromFiniteVerification {
        theorem_id: TheoremId::new("test-guarded-h1").unwrap(),
        replay: ReplayHash::from_bytes([7; 32]),
    };
    homology_basis(
        1,
        &BasicMatrix::from_row_major(nv, ne, d1).unwrap(),
        &BasicMatrix::from_row_major(ne, nf, d2).unwrap(),
        provenance,
    )
    .unwrap()
    .homology_rank()
}

#[test]
fn three_chain_family_has_a_within_component_separating_cocycle() {
    let bytes = three_chain();
    let certificate = guarded_certificate(&bytes, 3).unwrap();
    assert_eq!(certificate.get("kind_compatible"), Some(&Json::Bool(false)));
    assert_eq!(certificate.get("star_base"), Some(&Json::Null));
    assert_eq!(
        certificate.get("linear_extensions"),
        Some(&Json::natural(90))
    );
    let Some(Json::Arr(legal_json)) = certificate.get("legal_orders") else {
        panic!("legal orders missing");
    };
    assert_eq!(legal_json.len(), 54);
    let Some(Json::Arr(components)) = certificate.get("components") else {
        panic!("components missing");
    };
    assert_eq!(components.len(), 1);
    assert_eq!(components[0].get("h1_rank"), Some(&Json::natural(1)));

    let problem = parse_problem(&bytes).unwrap();
    let legal = legal_extensions(&problem).unwrap();
    let complex = SwapComplex::new(6, &legal).unwrap();
    assert_eq!(homology_rank_by_basis(&complex, 0), 1);

    let cocycle = certificate.get("separating_cocycle").unwrap();
    let Some(Json::Arr(edge_values)) = cocycle.get("edge_values") else {
        panic!("edge values missing");
    };
    let mut values = BTreeMap::new();
    for item in edge_values {
        let tail = complex.index_of(&naturals_of(item.get("order"))).unwrap();
        let Some(Json::Int(p)) = item.get("position") else {
            panic!("position");
        };
        let p = usize::try_from(*p).unwrap();
        assert!(tail < complex.neighbor(tail, p).unwrap());
        let edge = complex
            .edges()
            .iter()
            .position(|&e| e == (tail, p))
            .unwrap();
        let Some(Json::Str(v)) = item.get("value") else {
            panic!("value");
        };
        values.insert(edge, rational(v));
    }
    // Closed on every legal face, recomputed from the emitted values.
    for face in complex.faces() {
        let sum = face
            .boundary
            .iter()
            .fold(BigRational::zero(), |acc, (e, s)| {
                let v = values.get(e).cloned().unwrap_or_default();
                if *s > 0 {
                    acc + v
                } else {
                    acc - v
                }
            });
        assert!(sum.is_zero());
    }
    let root = complex
        .index_of(&naturals_of(cocycle.get("root_order")))
        .unwrap();
    let target = complex
        .index_of(&naturals_of(cocycle.get("target_order")))
        .unwrap();
    assert_eq!(root, 0);
    let word_a = naturals_of(cocycle.get("word_a"));
    let word_b = naturals_of(cocycle.get("word_b"));
    assert_eq!(complex.replay_word(root, &word_a), Ok(target));
    assert_eq!(complex.replay_word(root, &word_b), Ok(target));
    let value_a = complex.cochain_along(&values, root, &word_a).unwrap();
    let value_b = complex.cochain_along(&values, root, &word_b).unwrap();
    assert_ne!(value_a, value_b);
    let Some(Json::Str(emitted)) = cocycle.get("value_a") else {
        panic!("value_a");
    };
    assert_eq!(rational(emitted), value_a);
    // Negative control: perturbing one value breaks closedness.
    let (&first, _) = values.iter().next().unwrap();
    let mut broken = values.clone();
    *broken.get_mut(&first).unwrap() += BigRational::one();
    assert!(!complex.cochain_closed(&broken));
    // Dropping one Remove-before-Add precedence removes the hole.
    let relaxed = {
        let events = [
            edit("x1", "remove", "r", &[]),
            edit("a1", "add_assertion", "r", &["x1"]),
            edit("x2", "remove", "r", &[]),
            edit("a2", "add_assertion", "r", &["x2"]),
            edit("x3", "remove", "r", &[]),
            edit("a3", "add_assertion", "r", &[]),
        ];
        problem_bytes("2", &events.join(","))
    };
    let relaxed = evaluate_problem(parse_problem(&relaxed).unwrap()).unwrap();
    assert_eq!(relaxed.analysis.h1_ranks, vec![0]);
}

#[test]
fn explicit_legal_set_with_two_antipodal_holes_has_one_cycle() {
    // All 24 orders of four free events except those beginning with {0,1}
    // or with {2,3}: the 2-sphere of the permutohedron minus two disjoint stars.
    let mut legal = BTreeSet::new();
    let mut order = vec![0, 1, 2, 3];
    fn permutations(order: &mut Vec<usize>, k: usize, out: &mut BTreeSet<Vec<usize>>) {
        if k == order.len() {
            out.insert(order.clone());
            return;
        }
        for i in k..order.len() {
            order.swap(k, i);
            permutations(order, k + 1, out);
            order.swap(k, i);
        }
    }
    let mut all = BTreeSet::new();
    permutations(&mut order, 0, &mut all);
    assert_eq!(all.len(), 24);
    for o in &all {
        let head: BTreeSet<usize> = o[..2].iter().copied().collect();
        if head != BTreeSet::from([0, 1]) && head != BTreeSet::from([2, 3]) {
            legal.insert(o.clone());
        }
    }
    let analysis = analyze_legal_set(4, &legal, None).unwrap();
    assert_eq!(analysis.complex.components().len(), 1);
    assert_eq!(analysis.h1_ranks, vec![1]);
    assert_eq!(homology_rank_by_basis(&analysis.complex, 0), 1);
    assert_eq!(analysis.star_base, None);
    let cocycle = analysis.complex.separating_cocycle().unwrap().unwrap();
    assert!(analysis.complex.cochain_closed(&cocycle.values));
    assert_ne!(cocycle.value_a, cocycle.value_b);
    // The full sphere is simply connected and every order is a star base.
    let full = analyze_legal_set(4, &all, None).unwrap();
    assert_eq!(full.h1_ranks, vec![0]);
    assert_eq!(full.complex.squares(), 6);
    assert_eq!(full.complex.hexagons(), 8);
    assert_eq!(full.star_base, Some(vec![0, 1, 2, 3]));
    assert_eq!(full.complex.separating_cocycle().unwrap(), None);
}

#[test]
fn malformed_problems_are_refused() {
    let cyclic = problem_bytes(
        "1",
        &[
            edit("x", "remove", "r", &["y"]),
            edit("y", "remove", "r", &["x"]),
        ]
        .join(","),
    );
    assert_eq!(
        parse_problem(&cyclic).unwrap_err(),
        AdmissionRefusal::CyclicPrecedence
    );
    let nine: Vec<String> = (0..9)
        .map(|i| edit(&format!("e{i}"), "add_assertion", "r", &[]))
        .collect();
    assert_eq!(
        parse_problem(&problem_bytes("0", &nine.join(","))).unwrap_err(),
        AdmissionRefusal::EventBound
    );
    let eight: Vec<String> = (0..8)
        .map(|i| edit(&format!("e{i}"), "add_assertion", "r", &[]))
        .collect();
    assert!(parse_problem(&problem_bytes("0", &eight.join(","))).is_ok());
    let birth = r#"{"tag":"born","kind":"add_term","birth":"b","predecessors":[]}"#;
    let unbound =
        r#"{"tag":"use","kind":"remove","relation":"r","tokens":["b","u"],"predecessors":[]}"#;
    let bound = r#"{"tag":"use","kind":"remove","relation":"r","tokens":["b","u"],"predecessors":["born"]}"#;
    assert_eq!(
        parse_problem(&problem_bytes("0", &format!("{birth},{unbound}"))).unwrap_err(),
        AdmissionRefusal::BirthBeforeUseMissing
    );
    assert!(parse_problem(&problem_bytes("0", &format!("{birth},{bound}"))).is_ok());
    let duplicate = br#"{"schema":"wdp-causal-problem-v1","schema":"x"}"#;
    assert!(matches!(
        parse_problem(duplicate),
        Err(AdmissionRefusal::Json(m)) if m.contains("duplicate key")
    ));
    let float = problem_bytes("0", &edit("e", "add_assertion", "r", &[]))
        .iter()
        .map(|&b| b as char)
        .collect::<String>()
        .replace(r#""filled":[]"#, r#""filled":[[0.5,1,2]]"#);
    assert!(matches!(
        parse_problem(float.as_bytes()),
        Err(AdmissionRefusal::Json(m)) if m.contains("nonintegral")
    ));
    assert_eq!(
        parse_problem(&problem_bytes("01", "")).unwrap_err(),
        AdmissionRefusal::NoncanonicalIntegerString
    );
    assert!(matches!(
        guarded_certificate(&cyclic, 3),
        Err(GuardedHistoryError::Admission(
            AdmissionRefusal::CyclicPrecedence
        ))
    ));
}

#[test]
fn strict_json_rejects_noninteger_encodings_without_coercion() {
    for raw in [
        "0.5",
        "1.0",
        "1e0",
        "1E+1",
        "-0.0",
        "[0.5]",
        r#"{"value":0.5}"#,
        r#"{"$serde_json::private::Number":"0.5"}"#,
        r#"{"$serde_json::private::Number":"1"}"#,
    ] {
        assert!(
            matches!(Json::parse(raw.as_bytes()), Err(AdmissionRefusal::Json(message))
                if message.contains("nonintegral")),
            "numeric encoding must be refused: {raw}"
        );
    }
    for value in [0i128, -1, i64::MIN.into(), u64::MAX.into()] {
        assert_eq!(
            Json::parse(value.to_string().as_bytes()),
            Ok(Json::Int(value))
        );
    }
    assert_eq!(Json::parse(br#""0.5""#), Ok(Json::text("0.5")));
    assert_eq!(
        Json::parse(br#"{"label":"0.5"}"#),
        Ok(Json::object([("label", Json::text("0.5"))]))
    );
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
