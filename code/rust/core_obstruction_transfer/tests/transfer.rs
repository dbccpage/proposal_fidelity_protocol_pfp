//! Tests for the obstruction-transfer test. AuthorityEffect: None.

use core_obstruction_transfer::*;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::One;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// Claims and weights listed for edges (0,1), (1,2), (0,2), as in the definitions;
/// the graph stores its edges sorted, (0,1), (0,2), (1,2).
fn triangle(c: [i64; 3], w: [i64; 3]) -> Instance {
    Instance {
        id: "triangle".into(),
        graph: Graph::new(3, &[(0, 1), (1, 2), (0, 2)]),
        w: vec![w[0], w[2], w[1]],
        c: vec![c[0], c[2], c[1]],
    }
}

#[test]
fn census_matches_known_graph_counts() {
    // Connected unicyclic graphs: 1, 2, 5 for n = 3, 4, 5; bicyclic: 0, 1, 5.
    let graphs = enumerate_graphs(5);
    let count = |n, b| {
        graphs
            .iter()
            .filter(|g| g.n() == n && g.betti() == b)
            .count()
    };
    assert_eq!([count(3, 1), count(4, 1), count(5, 1)], [1, 2, 5]);
    assert_eq!([count(3, 2), count(4, 2), count(5, 2)], [0, 1, 5]);
    assert_eq!(graphs.len(), 14);
}

#[test]
fn score_counterexamples_from_the_definitions() {
    // Structural trace "phi1 = phi0 + c01" on B = (2, -1, 2): S = 1/2.
    let b = triangle([2, -1, 2], [1, 1, 1]);
    let phi1 = certify_phi1(&b).unwrap().value;
    assert_eq!(phi1, q(1, 1));
    assert_eq!(
        score(&b, &phi1, &[0, 2, 0]).unwrap(),
        Outcome::Scored(q(1, 2))
    );
    // Negative score: phi = (0, -2, 0) gives D 5 -> 9, S = -1.
    assert_eq!(
        score(&b, &phi1, &[0, -2, 0]).unwrap(),
        Outcome::Scored(q(-1, 1))
    );
    // No headroom: c = (0, 0, 1), phi = (0, 1, 0): D0 = Phi1 = 1, D_tau = 3.
    let nh = triangle([0, 0, 1], [1, 1, 1]);
    let v = certify_phi1(&nh).unwrap().value;
    assert_eq!(
        score(&nh, &v, &[0, 1, 0]).unwrap(),
        Outcome::NoHeadroom(q(2, 1))
    );
    // The same trace is optimal on A = (1, -1, 1).
    let a = triangle([1, -1, 1], [1, 1, 1]);
    let va = certify_phi1(&a).unwrap().value;
    assert_eq!(
        score(&a, &va, &[0, 1, 0]).unwrap(),
        Outcome::Scored(BigRational::one())
    );
}

#[test]
fn class_invariance_on_every_small_instance() {
    let family = enumerate_family(4);
    for inst in &family.instances {
        let base = certify_phi1(inst).unwrap().value;
        for psi in [[0, 1, -1, 0], [0, -1, 1, 1], [0, 0, 0, 1]] {
            let mut c = inst.c.clone();
            for (e, &(u, v)) in inst.graph.edges().iter().enumerate() {
                c[e] += psi.get(v).copied().unwrap_or(0) - psi.get(u).copied().unwrap_or(0);
            }
            let shifted = Instance { c, ..inst.clone() };
            assert_eq!(certify_phi1(&shifted).unwrap().value, base, "{}", inst.id);
        }
    }
}

#[test]
fn weighted_triangle_trace_picks_the_light_edge() {
    // Heavy chord: the optimum cuts the light tree edge, so the trace moves the cut.
    // Edges (0,1), (1,2), (0,2); the canonical tree is (0,1), (0,2), the chord (1,2) has weight 2.
    let a = triangle([0, 1, 0], [1, 2, 1]);
    let cert = certify_phi1(&a).unwrap();
    assert_eq!(cert.value, q(1, 1));
    let trace = record_trace(&a, &cert.alpha).unwrap();
    assert!(
        trace.word().starts_with("C E R D(0,") && !trace.word().contains("D(0,0)"),
        "{}",
        trace.word()
    );
    let phi = replay(&trace, &a, &[Some(0)]).unwrap();
    assert_eq!(
        score(&a, &cert.value, &phi).unwrap(),
        Outcome::Scored(BigRational::one())
    );
}

#[test]
fn cross_betti_is_refused_and_chord_without_image_is_typed() {
    let a = triangle([1, 0, 0], [1, 1, 1]);
    let b = Instance {
        id: "diamond".into(),
        graph: Graph::new(4, &[(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]),
        w: vec![1; 5],
        c: vec![0, 0, 1, 0, 1],
    };
    assert_eq!(classify(&a, &b, &permutations(3)), None);
    let cert = certify_phi1(&a).unwrap();
    let trace = record_trace(&a, &cert.alpha).unwrap();
    assert_eq!(replay(&trace, &a, &[None]), Err(Refusal::ChordNoImage));
}

#[test]
fn small_family_acceptance_and_determinism() {
    let cfg = RunConfig {
        max_n: 4,
        injection: Injection::None,
    };
    let first = run(cfg).unwrap();
    assert!(first.defects.is_empty(), "{:?}", first.defects);
    assert!(
        first.gauge_failures.is_empty(),
        "{:?}",
        first.gauge_failures
    );
    // Cross-Betti pairs produce refusals only.
    for line in first
        .table
        .lines()
        .filter(|l| l.starts_with("| control_cross_betti | none |"))
    {
        let cols: Vec<&str> = line.split('|').map(str::trim).collect();
        if cols.len() > 8 && cols[4].parse::<u64>().is_ok() {
            assert_eq!(cols[4], cols[7], "{line}");
        }
    }
    let second = run(cfg).unwrap();
    assert_eq!(first.table, second.table);
    assert_eq!(first.output_digest, second.output_digest);
    assert_eq!(first.input_digest, second.input_digest);
}

#[test]
fn mutation_flip_tree_edge_sign_breaks_gauge_transport_and_names_the_case() {
    let cfg = RunConfig {
        max_n: 4,
        injection: Injection::FlipFirstTreeEdgeSign,
    };
    let out = run(cfg).unwrap();
    assert!(
        out.gauge_failures
            .iter()
            .any(|f| f.starts_with("L2 gauge:")),
        "{:?}",
        out.gauge_failures.first()
    );
}

#[test]
fn mutation_flip_chord_sign_is_inert_for_gauge_transport() {
    // The gauge psi is integrated on tree edges only, so a chord flip changes nothing.
    let cfg = RunConfig {
        max_n: 3,
        injection: Injection::FlipFirstChordSign,
    };
    assert!(run(cfg).unwrap().gauge_failures.is_empty());
}

#[test]
fn committed_n4_receipt_reproduces_byte_for_byte() {
    let cfg = RunConfig {
        max_n: 4,
        injection: Injection::None,
    };
    let out = run(cfg).unwrap();
    assert_eq!(
        receipt_json(&cfg, &out),
        include_str!("../receipts/max_n_4/receipt.json")
    );
    let doc = format!("## Census\n\n{}\n## Table\n\n{}", out.census, out.table);
    assert_eq!(doc, include_str!("../receipts/max_n_4/table.md"));
}
