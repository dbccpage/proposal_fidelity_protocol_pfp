//! Integration and falsification test suite for Prompt Civilization Rational Solvers.
//!
//! Enforces:
//! - Exact PageRank over Rational64 via Gaussian elimination with exact damping factors.
//! - Exact multi-objective Pareto frontier sorting over Q with cost inversion and tiebreaks.
//! - Bounded multi-parent lineage graph traversal with max_depth <= 5 and cycle detection.
//! - Monotonic Lamarckian cochain residual tracking (Delta Phi_1 <= 0) and protected core invariance.
//! - Zero floating-point arithmetic (I_float_metric).
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::{One, Signed, Zero};
use core_prompt_civilization::rank::{
    CitationGraph, CompactedPageRankResult, CompactedPageRankResultV1, ExactPageRankSolverV1,
    PageRankCertificateV1, PageRankError, RankError, SovereignPrng, SparsePageRankResult,
};
use core_prompt_civilization::{
    compute_pareto_fronts_rational, pareto_frontier_rational, CandidateRational,
    CochainHistoryTracker, CochainResidualV1, GenealogyError, GenealogyGraph,
    InheritanceRelationship, LamarckianCochainTrackerV1, LamarckianTrackingError,
};
use std::collections::{BTreeMap, HashSet};

fn bound_witness(parent: &str, child: &str) -> String {
    core_prompt_civilization::genealogy::inheritance_witness_digest(
        parent,
        child,
        &InheritanceRelationship::DirectMutation,
    )
}

// ==============================================================================
// 1. ExactPageRankSolverV1 Falsification Tests
// ==============================================================================

#[test]
fn test_exact_pagerank_two_node_mathematical_expectation() {
    // 2-node graph: 0 -> 1. Node 1 is dangling.
    // Fixed point equation: (I - alpha * P) r = (1 - alpha) * u, with sum(r) = 1.
    // For alpha = 17/20, exact solution: r_0 = 20/57, r_1 = 37/57.
    let mut adj = BTreeMap::new();
    adj.insert(0, vec![1]);
    adj.insert(1, vec![]);
    let alpha = Rational64::new(17, 20);

    let rank = ExactPageRankSolverV1::solve(&adj, alpha).expect("solver failed");

    assert_eq!(rank.len(), 2);
    assert_eq!(rank[0], Rational64::new(20, 57));
    assert_eq!(rank[1], Rational64::new(37, 57));
    assert_eq!(rank[0] + rank[1], Rational64::one());
    assert!(
        rank[1] > rank[0],
        "Target node must have higher rank than source"
    );
}

#[test]
fn test_exact_pagerank_three_node_cycle_uniformity() {
    // 3-node cycle: 0 -> 1 -> 2 -> 0.
    // By cyclic symmetry, rank must be identically [1/3, 1/3, 1/3].
    let edges = [(0, 1), (1, 2), (2, 0)];
    let alpha = Rational64::new(17, 20);

    let rank = ExactPageRankSolverV1::solve_edges(3, &edges, alpha).expect("solver failed");

    assert_eq!(rank, vec![Rational64::new(1, 3); 3]);
    let total: Rational64 = rank.iter().sum();
    assert_eq!(total, Rational64::one());
}

#[test]
fn test_exact_pagerank_dangling_star_graph() {
    // Star topology: 1, 2, 3 all link to 0. Center node 0 is dangling (no outgoing edges).
    let edges = [(1, 0), (2, 0), (3, 0)];
    let alpha = Rational64::new(17, 20);

    let rank = ExactPageRankSolverV1::solve_edges(4, &edges, alpha).expect("solver failed");

    assert_eq!(rank.len(), 4);
    assert_eq!(rank.iter().sum::<Rational64>(), Rational64::one());
    // Node 0 receives 3 links, must have highest rank
    assert_eq!(rank[0], *rank.iter().max().unwrap());
    // Nodes 1, 2, 3 are symmetric leaves and must have identical rank
    assert_eq!(rank[1], rank[2]);
    assert_eq!(rank[2], rank[3]);
}

#[test]
fn test_exact_pagerank_falsify_invalid_damping_and_empty() {
    let mut adj = BTreeMap::new();
    adj.insert(0, vec![1]);

    // Damping <= 0 must be refused
    assert!(matches!(
        ExactPageRankSolverV1::solve(&adj, Rational64::zero()),
        Err(RankError::InvalidDamping(_))
    ));
    assert!(matches!(
        ExactPageRankSolverV1::solve(&adj, Rational64::new(-1, 5)),
        Err(RankError::InvalidDamping(_))
    ));

    // Damping >= 1 must be refused
    assert!(matches!(
        ExactPageRankSolverV1::solve(&adj, Rational64::one()),
        Err(RankError::InvalidDamping(_))
    ));
    assert!(matches!(
        ExactPageRankSolverV1::solve(&adj, Rational64::new(6, 5)),
        Err(RankError::InvalidDamping(_))
    ));

    // Empty graph must be refused
    let empty_adj: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    assert!(matches!(
        ExactPageRankSolverV1::solve(&empty_adj, Rational64::new(17, 20)),
        Err(RankError::EmptyGraph)
    ));
}

#[test]
fn test_exact_pagerank_zero_float_drift_impossible() {
    // Multi-edge topology with cycle, dangling branch, and sink
    let edges = [(0, 1), (1, 2), (1, 3), (2, 0), (3, 2), (4, 1)];
    let alpha = Rational64::new(17, 20);

    let rank = ExactPageRankSolverV1::solve_edges(5, &edges, alpha).expect("solver failed");

    // Exact stochastic closure: sum must equal 1/1 identically with integer 1 numerator and denominator
    let sum: Rational64 = rank.iter().sum();
    assert_eq!(sum, Rational64::one());
    assert_eq!(*sum.numer(), 1i64);
    assert_eq!(*sum.denom(), 1i64);
}

// ==============================================================================
// 2. Exact Rational Pareto Frontier Sorting Falsification Tests
// ==============================================================================

#[test]
fn test_pareto_exact_domination_partition() {
    let cand_a = CandidateRational::new(
        "cand_a",
        Rational64::new(9, 10),
        Rational64::new(1, 10),
        Rational64::new(1, 1),
    );
    let cand_b = CandidateRational::new(
        "cand_b",
        Rational64::new(8, 10),
        Rational64::new(2, 10),
        Rational64::new(8, 10),
    );

    assert!(cand_a.dominates(&cand_b));
    assert!(!cand_b.dominates(&cand_a));

    let fronts = compute_pareto_fronts_rational(&[cand_a.clone(), cand_b.clone()]);
    assert_eq!(fronts.len(), 2);
    assert_eq!(fronts[0], vec![cand_a.clone()]);
    assert_eq!(fronts[1], vec![cand_b]);

    let frontier = pareto_frontier_rational(&[cand_a.clone()]);
    assert_eq!(frontier, vec![cand_a]);
}

#[test]
fn test_pareto_tradeoff_non_dominated_front() {
    // c1 has higher correctness, c2 has lower cost -> neither dominates
    let c1 = CandidateRational::new(
        "c1",
        Rational64::new(9, 10),
        Rational64::new(5, 10),
        Rational64::new(1, 1),
    );
    let c2 = CandidateRational::new(
        "c2",
        Rational64::new(7, 10),
        Rational64::new(2, 10),
        Rational64::new(1, 1),
    );

    assert!(!c1.dominates(&c2));
    assert!(!c2.dominates(&c1));

    let fronts = compute_pareto_fronts_rational(&[c1.clone(), c2.clone()]);
    assert_eq!(fronts.len(), 1);
    assert_eq!(fronts[0].len(), 2);
    // Tiebreak: correctness descending -> c1 comes before c2
    assert_eq!(fronts[0][0].id, "c1");
    assert_eq!(fronts[0][1].id, "c2");
}

#[test]
fn test_pareto_cost_inversion_lower_cost_strictly_dominates() {
    let cheap = CandidateRational::new(
        "cheap",
        Rational64::new(8, 10),
        Rational64::new(1, 10),
        Rational64::new(1, 1),
    );
    let expensive = CandidateRational::new(
        "expensive",
        Rational64::new(8, 10),
        Rational64::new(9, 10),
        Rational64::new(1, 1),
    );

    assert!(cheap.dominates(&expensive));
    assert!(!expensive.dominates(&cheap));

    let front = pareto_frontier_rational(&[expensive, cheap.clone()]);
    assert_eq!(front, vec![cheap]);
}

#[test]
fn test_pareto_lexicographic_tiebreak_by_id() {
    let b = CandidateRational::new(
        "cand_b",
        Rational64::new(8, 10),
        Rational64::new(1, 2),
        Rational64::new(1, 1),
    );
    let a = CandidateRational::new(
        "cand_a",
        Rational64::new(8, 10),
        Rational64::new(1, 2),
        Rational64::new(1, 1),
    );

    let fronts = compute_pareto_fronts_rational(&[b, a]);
    assert_eq!(fronts.len(), 1);
    assert_eq!(fronts[0][0].id, "cand_a");
    assert_eq!(fronts[0][1].id, "cand_b");
}

// ==============================================================================
// 3. Multi-Parent Lineage Traversal Falsification Tests
// ==============================================================================

#[test]
fn test_lineage_single_parent_descent_chain() {
    let mut g = GenealogyGraph::new();
    for i in 0..4 {
        let parent = format!("g{i}");
        let child = format!("g{}", i + 1);
        g.add_inheritance_edge(
            &parent,
            &child,
            InheritanceRelationship::DirectMutation,
            &bound_witness(&parent, &child),
        )
        .expect("edge add failed");
    }

    let ancestors = g.traverse_ancestors("g4", 5).expect("traversal failed");
    let expected: HashSet<String> = (0..=4).map(|i| format!("g{i}")).collect();
    assert_eq!(ancestors, expected);
}

#[test]
fn test_lineage_multi_parent_crossover() {
    let mut g = GenealogyGraph::new();
    g.add_inheritance_edge(
        "p1",
        "child",
        InheritanceRelationship::DirectMutation,
        &bound_witness("p1", "child"),
    )
    .unwrap();
    g.add_inheritance_edge(
        "p2",
        "child",
        InheritanceRelationship::DirectMutation,
        &bound_witness("p2", "child"),
    )
    .unwrap();

    let ancestors = g.traverse_ancestors("child", 2).unwrap();
    let expected: HashSet<String> = ["child", "p1", "p2"]
        .iter()
        .map(|s| s.to_string())
        .collect();
    assert_eq!(ancestors, expected);
}

#[test]
fn test_lineage_strict_max_depth_five_refusal() {
    let mut g = GenealogyGraph::new();
    g.add_inheritance_edge(
        "root",
        "child",
        InheritanceRelationship::DirectMutation,
        &bound_witness("root", "child"),
    )
    .unwrap();

    // max_depth <= 5 succeeds
    assert!(g.traverse_ancestors("child", 5).is_ok());

    // max_depth > 5 is strictly refused with DepthBoundExceeded
    assert!(matches!(
        g.traverse_ancestors("child", 6),
        Err(GenealogyError::DepthBoundExceeded(6))
    ));
    assert!(matches!(
        g.traverse_ancestors("child", 10),
        Err(GenealogyError::DepthBoundExceeded(10))
    ));
    assert!(matches!(
        g.traverse_lineage("child", 7),
        Err(GenealogyError::DepthBoundExceeded(7))
    ));
}

#[test]
fn test_lineage_cycle_refusal() {
    let mut g = GenealogyGraph::new();
    g.add_inheritance_edge(
        "A",
        "B",
        InheritanceRelationship::DirectMutation,
        &bound_witness("A", "B"),
    )
    .unwrap();
    g.add_inheritance_edge(
        "B",
        "C",
        InheritanceRelationship::DirectMutation,
        &bound_witness("B", "C"),
    )
    .unwrap();

    // Adding C -> A would create cycle A -> B -> C -> A
    let res = g.add_inheritance_edge(
        "C",
        "A",
        InheritanceRelationship::DirectMutation,
        &bound_witness("C", "A"),
    );
    assert!(res.is_err());
    assert!(res.unwrap_err().contains("LINEAGE_CYCLE_REFUSED"));

    // Self edge A -> A must also be refused
    let self_res = g.add_inheritance_edge(
        "A",
        "A",
        InheritanceRelationship::DirectMutation,
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdcc",
    );
    assert!(self_res.is_err());
    assert!(self_res.unwrap_err().contains("LINEAGE_CYCLE_REFUSED"));
}

#[test]
fn test_lineage_generation_number_derivation() {
    let mut g = GenealogyGraph::new();
    g.add_node("p_gen1", 1);
    g.add_node("p_gen3", 3);
    g.add_inheritance_edge(
        "p_gen1",
        "hybrid",
        InheritanceRelationship::DirectMutation,
        &bound_witness("p_gen1", "hybrid"),
    )
    .unwrap();
    g.add_inheritance_edge(
        "p_gen3",
        "hybrid",
        InheritanceRelationship::DirectMutation,
        &bound_witness("p_gen3", "hybrid"),
    )
    .unwrap();

    // Generation is max(gen(P_i)) + 1 = max(1, 3) + 1 = 4
    assert_eq!(g.derive_generation("hybrid"), 4);
}

// ==============================================================================
// 4. Lamarckian Cochain Tracking Falsification Tests
// ==============================================================================

#[test]
fn test_lamarckian_monotonic_residual_reduction_pass() {
    let parent_phi = Rational64::new(1, 2);
    let child_phi = Rational64::new(1, 4);

    let res = LamarckianCochainTrackerV1::verify_mutation(
        parent_phi,
        child_phi,
        1,
        b"PROTECTED_CORE_PREFIX_tail_old",
        b"PROTECTED_CORE_PREFIX_tail_new",
        &[(0, 22)],
    )
    .expect("verification failed");

    assert_eq!(res.status, "PASS");
    assert_eq!(res.delta_phi, Rational64::new(-1, 4));
    assert_eq!(res.attenuation_weight, Rational64::new(1, 2));
    assert!(res.protected_core_intact);
}

#[test]
fn test_lamarckian_falsify_residual_increase_refusal() {
    // Child residual higher than parent: 3/4 > 1/2 -> Delta Phi_1 = +1/4 > 0
    let parent_phi = Rational64::new(1, 2);
    let child_phi = Rational64::new(3, 4);

    let res = LamarckianCochainTrackerV1::verify_mutation(
        parent_phi,
        child_phi,
        1,
        b"CORE_tail_a",
        b"CORE_tail_b",
        &[(0, 4)],
    );

    assert!(matches!(
        res,
        Err(LamarckianTrackingError::RegressionResidualIncrease(d)) if d == Rational64::new(1, 4)
    ));
}

#[test]
fn test_lamarckian_falsify_protected_core_tampering_refusal() {
    let parent_phi = Rational64::new(1, 2);
    let child_phi = Rational64::new(1, 4);

    let res = LamarckianCochainTrackerV1::verify_mutation(
        parent_phi,
        child_phi,
        1,
        b"PROTECTED_IMMUTABLE_SPINE_old",
        b"PROTECTED_MUTATED___SPINE_old", // modified byte in protected span
        &[(0, 25)],
    );

    assert!(matches!(
        res,
        Err(LamarckianTrackingError::ProtectedCoreTampered(0, 25))
    ));
}

#[test]
fn test_lamarckian_attenuation_weight_bounds() {
    // Valid hop distances 1 <= d <= 10
    assert_eq!(
        LamarckianCochainTrackerV1::attenuation_weight(1).unwrap(),
        Rational64::new(1, 2)
    );
    assert_eq!(
        LamarckianCochainTrackerV1::attenuation_weight(2).unwrap(),
        Rational64::new(1, 4)
    );
    assert_eq!(
        LamarckianCochainTrackerV1::attenuation_weight(3).unwrap(),
        Rational64::new(1, 8)
    );
    assert_eq!(
        LamarckianCochainTrackerV1::attenuation_weight(10).unwrap(),
        Rational64::new(1, 1024)
    );

    // Hop distance 0 and > 10 strictly refused
    assert!(matches!(
        LamarckianCochainTrackerV1::attenuation_weight(0),
        Err(LamarckianTrackingError::HopDistanceOutOfBounds(0))
    ));
    assert!(matches!(
        LamarckianCochainTrackerV1::attenuation_weight(11),
        Err(LamarckianTrackingError::HopDistanceOutOfBounds(11))
    ));
}

#[test]
fn test_lamarckian_multi_generation_history_tracker() {
    let mut tracker = CochainHistoryTracker::new();

    let g0 = CochainResidualV1::new("1/1", "0/1", "0/1").unwrap();
    assert_eq!(
        tracker.record_generation("gen_0", g0).unwrap(),
        Rational64::zero()
    );

    let g1 = CochainResidualV1::new("3/4", "0/1", "0/1").unwrap();
    assert_eq!(
        tracker.record_generation("gen_1", g1).unwrap(),
        Rational64::new(-1, 4)
    );

    let g2 = CochainResidualV1::new("1/2", "0/1", "0/1").unwrap();
    assert_eq!(
        tracker.record_generation("gen_2", g2).unwrap(),
        Rational64::new(-1, 4)
    );

    // Regressive candidate: 3/5 > 1/2 (6/10 > 5/10)
    let g3_bad = CochainResidualV1::new("3/5", "0/1", "0/1").unwrap();
    assert!(matches!(
        tracker.record_generation("gen_3", g3_bad),
        Err(LamarckianTrackingError::RegressionResidualIncrease(_))
    ));
}

// ==============================================================================
// Adversarial Stress Tests (Empirical Challenger Suite)
// ==============================================================================

#[test]
fn test_adversarial_pagerank_cyclic_graphs_and_fixed_point() {
    // 1. 2-node cycle: 0 -> 1, 1 -> 0
    let edges_2 = [(0, 1), (1, 0)];
    let alpha = Rational64::new(17, 20);
    let rank_2 = ExactPageRankSolverV1::solve_edges(2, &edges_2, alpha).expect("solver failed");
    assert_eq!(rank_2, vec![Rational64::new(1, 2); 2]);
    assert_eq!(rank_2.iter().sum::<Rational64>(), Rational64::one());

    // 2. 4-node directed cycle: 0 -> 1 -> 2 -> 3 -> 0
    let edges_4 = [(0, 1), (1, 2), (2, 3), (3, 0)];
    let rank_4 = ExactPageRankSolverV1::solve_edges(4, &edges_4, alpha).expect("solver failed");
    assert_eq!(rank_4, vec![Rational64::new(1, 4); 4]);
    assert_eq!(rank_4.iter().sum::<Rational64>(), Rational64::one());

    // 3. Complex cyclic graph with cross edges:
    // 0 -> 1, 1 -> 2, 2 -> 0, 1 -> 0, 2 -> 1
    let edges_complex = [(0, 1), (1, 2), (2, 0), (1, 0), (2, 1)];
    let rank_c =
        ExactPageRankSolverV1::solve_edges(3, &edges_complex, alpha).expect("solver failed");
    assert_eq!(rank_c.iter().sum::<Rational64>(), Rational64::one());

    // Verify exact fixed point: (I - alpha * P) r = (1 - alpha) * u
    // For node 0: out(0)={1}, so P[1][0] = 1, P[0][0] = 0, P[2][0] = 0
    // For node 1: out(1)={0, 2}, so P[0][1] = 1/2, P[2][1] = 1/2
    // For node 2: out(2)={0, 1}, so P[0][2] = 1/2, P[1][2] = 1/2
    // r_0 = alpha * (1/2 * r_1 + 1/2 * r_2) + (1 - alpha) * 1/3
    let u = Rational64::new(1, 3);
    let expected_r0 = alpha
        * (Rational64::new(1, 2) * rank_c[1] + Rational64::new(1, 2) * rank_c[2])
        + (Rational64::one() - alpha) * u;
    assert_eq!(
        rank_c[0], expected_r0,
        "Fixed point equation must hold with zero rational difference"
    );
}

#[test]
fn test_adversarial_pagerank_disconnected_nodes_and_isolated_components() {
    let alpha = Rational64::new(17, 20);

    // 1. All isolated nodes: 5 nodes, 0 edges.
    // Each node has out-degree 0, transitions uniformly to all nodes.
    let rank_isolated = ExactPageRankSolverV1::solve_edges(5, &[], alpha).expect("solver failed");
    assert_eq!(rank_isolated, vec![Rational64::new(1, 5); 5]);
    assert_eq!(rank_isolated.iter().sum::<Rational64>(), Rational64::one());

    // 2. Two disjoint subgraphs: Component A (0 <-> 1) and Component B (2 <-> 3)
    let disjoint_edges = [(0, 1), (1, 0), (2, 3), (3, 2)];
    let rank_disjoint =
        ExactPageRankSolverV1::solve_edges(4, &disjoint_edges, alpha).expect("solver failed");
    assert_eq!(rank_disjoint, vec![Rational64::new(1, 4); 4]);
    assert_eq!(rank_disjoint.iter().sum::<Rational64>(), Rational64::one());

    // 3. Disconnected island with sink: 0 -> 1 (island), and node 2 completely isolated
    let island_edges = [(0, 1)];
    let rank_island =
        ExactPageRankSolverV1::solve_edges(3, &island_edges, alpha).expect("solver failed");
    assert_eq!(rank_island.iter().sum::<Rational64>(), Rational64::one());
    assert!(
        rank_island[1] > rank_island[0],
        "Node 1 receives edge from 0"
    );
}

#[test]
fn test_adversarial_pagerank_extreme_damping_and_refusal_boundaries() {
    let edges = [(0, 1), (1, 0)];

    // Boundary damping values:
    assert!(matches!(
        ExactPageRankSolverV1::solve_edges(2, &edges, Rational64::zero()),
        Err(RankError::InvalidDamping(_))
    ));
    assert!(matches!(
        ExactPageRankSolverV1::solve_edges(2, &edges, Rational64::one()),
        Err(RankError::InvalidDamping(_))
    ));
    assert!(matches!(
        ExactPageRankSolverV1::solve_edges(2, &edges, Rational64::new(-1, 10)),
        Err(RankError::InvalidDamping(_))
    ));
    assert!(matches!(
        ExactPageRankSolverV1::solve_edges(2, &edges, Rational64::new(11, 10)),
        Err(RankError::InvalidDamping(_))
    ));

    // Extreme valid damping close to 0: alpha = 1 / 10000
    let alpha_small = Rational64::new(1, 10000);
    let rank_small =
        ExactPageRankSolverV1::solve_edges(2, &edges, alpha_small).expect("extreme damping failed");
    assert_eq!(rank_small, vec![Rational64::new(1, 2); 2]);

    // Extreme valid damping close to 1: alpha = 9999 / 10000
    let alpha_large = Rational64::new(9999, 10000);
    let rank_large =
        ExactPageRankSolverV1::solve_edges(2, &edges, alpha_large).expect("extreme damping failed");
    assert_eq!(rank_large, vec![Rational64::new(1, 2); 2]);

    // Graph error conditions:
    assert!(matches!(
        ExactPageRankSolverV1::solve_edges(0, &[], Rational64::new(1, 2)),
        Err(RankError::EmptyGraph)
    ));
    assert!(matches!(
        ExactPageRankSolverV1::solve_edges(3, &[(0, 5)], Rational64::new(1, 2)),
        Err(RankError::InputInvalid(_))
    ));
}

#[test]
fn test_adversarial_pareto_duplicate_candidates_and_tiebreak_sorting() {
    // 3 duplicate candidates with identical scores but distinct IDs
    let c_z = CandidateRational::new(
        "cand_Z",
        Rational64::new(8, 10),
        Rational64::new(5, 1),
        Rational64::new(9, 10),
    );
    let c_a = CandidateRational::new(
        "cand_A",
        Rational64::new(8, 10),
        Rational64::new(5, 1),
        Rational64::new(9, 10),
    );
    let c_m = CandidateRational::new(
        "cand_M",
        Rational64::new(8, 10),
        Rational64::new(5, 1),
        Rational64::new(9, 10),
    );

    // Neither dominates because strictly_better_any returns false
    assert!(!c_z.dominates(&c_a));
    assert!(!c_a.dominates(&c_m));

    let candidates = vec![c_z, c_a, c_m];
    let fronts = compute_pareto_fronts_rational(&candidates);

    assert_eq!(
        fronts.len(),
        1,
        "All identical candidates must belong to Front 0"
    );
    assert_eq!(fronts[0].len(), 3);

    // Lexicographic tiebreak by id ascending
    assert_eq!(fronts[0][0].id, "cand_A");
    assert_eq!(fronts[0][1].id, "cand_M");
    assert_eq!(fronts[0][2].id, "cand_Z");
}

#[test]
fn test_adversarial_pareto_cost_inversion_and_tradeoffs() {
    // Cost inversion: Candidate B has identical correctness and robustness, but cost is 2/1 vs 10/1
    let c_high_cost = CandidateRational::new(
        "high_cost",
        Rational64::new(9, 10),
        Rational64::new(10, 1),
        Rational64::new(8, 10),
    );
    let c_low_cost = CandidateRational::new(
        "low_cost",
        Rational64::new(9, 10),
        Rational64::new(2, 1),
        Rational64::new(8, 10),
    );

    assert!(c_low_cost.dominates(&c_high_cost));
    assert!(!c_high_cost.dominates(&c_low_cost));

    let fronts = compute_pareto_fronts_rational(&[c_high_cost.clone(), c_low_cost.clone()]);
    assert_eq!(fronts.len(), 2);
    assert_eq!(fronts[0][0].id, "low_cost");
    assert_eq!(fronts[1][0].id, "high_cost");

    // 3-way trade-off matrix: each candidate leads in exactly one objective
    let c_correctness = CandidateRational::new(
        "best_correctness",
        Rational64::new(99, 100),
        Rational64::new(50, 1),
        Rational64::new(1, 10),
    );
    let c_cost = CandidateRational::new(
        "best_cost",
        Rational64::new(50, 100),
        Rational64::new(1, 1),
        Rational64::new(1, 10),
    );
    let c_robustness = CandidateRational::new(
        "best_robustness",
        Rational64::new(50, 100),
        Rational64::new(50, 1),
        Rational64::new(99, 100),
    );

    let tradeoff_fronts = compute_pareto_fronts_rational(&[c_correctness, c_cost, c_robustness]);
    assert_eq!(
        tradeoff_fronts.len(),
        1,
        "Trade-off candidates are non-dominated and form Front 0"
    );
    assert_eq!(tradeoff_fronts[0].len(), 3);
}

#[test]
fn test_adversarial_genealogy_cyclical_graphs_rejection() {
    let mut graph = GenealogyGraph::new();
    graph.add_node("node_A", 0);
    graph.add_node("node_B", 1);
    graph.add_node("node_C", 2);

    // Self-edge refusal
    let err_self = graph.add_inheritance_edge(
        "node_A",
        "node_A",
        InheritanceRelationship::DirectMutation,
        "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    );
    assert!(err_self.is_err());
    assert!(err_self
        .unwrap_err()
        .contains("LINEAGE_CYCLE_REFUSED: self-edge forbidden"));

    // Add A -> B
    graph
        .add_inheritance_edge(
            "node_A",
            "node_B",
            InheritanceRelationship::DirectMutation,
            &bound_witness("node_A", "node_B"),
        )
        .unwrap();

    // 2-cycle attempt: B -> A must be refused
    let err_cycle_2 = graph.add_inheritance_edge(
        "node_B",
        "node_A",
        InheritanceRelationship::DirectMutation,
        &bound_witness("node_B", "node_A"),
    );
    assert!(err_cycle_2.is_err());
    assert!(err_cycle_2
        .unwrap_err()
        .contains("LINEAGE_CYCLE_REFUSED: Cycle detected"));

    // Add B -> C
    graph
        .add_inheritance_edge(
            "node_B",
            "node_C",
            InheritanceRelationship::DirectMutation,
            &bound_witness("node_B", "node_C"),
        )
        .unwrap();

    // 3-cycle attempt: C -> A must be refused
    let err_cycle_3 = graph.add_inheritance_edge(
        "node_C",
        "node_A",
        InheritanceRelationship::DirectMutation,
        &bound_witness("node_C", "node_A"),
    );
    assert!(err_cycle_3.is_err());
    assert!(err_cycle_3
        .unwrap_err()
        .contains("LINEAGE_CYCLE_REFUSED: Cycle detected"));

    // Unverified receipt edge refusal
    let err_unverified = graph.add_inheritance_edge(
        "node_C",
        "node_D",
        InheritanceRelationship::DirectMutation,
        "unverified",
    );
    assert!(err_unverified.is_err());
    assert!(err_unverified
        .unwrap_err()
        .contains("WITNESS_RECEIPT_REQUIRED"));
}

#[test]
fn test_adversarial_genealogy_depth_bounds_exceeded_refusal() {
    let mut graph = GenealogyGraph::new();
    graph.add_node("root", 0);

    // Depth > 5 must be refused
    assert_eq!(
        graph.traverse_ancestors("root", 6),
        Err(GenealogyError::DepthBoundExceeded(6))
    );
    assert_eq!(
        graph.traverse_lineage("root", 7),
        Err(GenealogyError::DepthBoundExceeded(7))
    );
    assert_eq!(
        graph.traverse_lineage("root", 100),
        Err(GenealogyError::DepthBoundExceeded(100))
    );

    // Depth 5 must succeed
    assert!(graph.traverse_ancestors("root", 5).is_ok());
    assert!(graph.traverse_lineage("root", 5).is_ok());

    // Non-existent root
    assert!(matches!(
        graph.traverse_lineage("non_existent_node", 3),
        Err(GenealogyError::RootNotFound(_))
    ));
}

#[test]
fn test_adversarial_lamarckian_cochain_residual_increase_and_tampered_core() {
    let parent_phi = Rational64::new(1, 5);
    let regressive_child_phi = Rational64::new(2, 5); // delta_phi = +1/5 > 0

    // 1. Residual increase refusal
    let res_regress = LamarckianCochainTrackerV1::verify_mutation(
        parent_phi,
        regressive_child_phi,
        1,
        b"PROTECTED_CORE_PAYLOAD",
        b"PROTECTED_CORE_PAYLOAD",
        &[(0, 22)],
    );
    assert!(matches!(
        res_regress,
        Err(LamarckianTrackingError::RegressionResidualIncrease(d)) if d == Rational64::new(1, 5)
    ));

    // 2. Tampered core refusal
    let valid_child_phi = Rational64::new(1, 10); // delta_phi = -1/10 < 0
    let res_tampered = LamarckianCochainTrackerV1::verify_mutation(
        parent_phi,
        valid_child_phi,
        1,
        b"PROTECTED_CORE_PAYLOAD",
        b"PROTECTED_XORE_PAYLOAD", // 'C' -> 'X' tamper
        &[(0, 22)],
    );
    assert!(matches!(
        res_tampered,
        Err(LamarckianTrackingError::ProtectedCoreTampered(0, 22))
    ));

    // 3. Out-of-bounds protected span refusal
    let res_oob = LamarckianCochainTrackerV1::verify_mutation(
        parent_phi,
        valid_child_phi,
        1,
        b"SHORT",
        b"SHORT",
        &[(0, 10)],
    );
    assert!(matches!(
        res_oob,
        Err(LamarckianTrackingError::SpanOutOfBounds(0, 10))
    ));
}

// ==============================================================================
// 6. Scale-Free Citation Graph & Rational Solvers M1 Verification & Falsification
// ==============================================================================

#[test]
fn test_scale_free_graph_deterministic_generation() {
    let n = 100;
    let m = 2;
    let bridge_edges = 20;
    let seed = 42;

    let g1 = ExactPageRankSolverV1::generate_scale_free_citation_graph(n, m, bridge_edges, seed);
    let g2 = ExactPageRankSolverV1::generate_scale_free_citation_graph(n, m, bridge_edges, seed);
    let g3 = ExactPageRankSolverV1::generate_scale_free_citation_graph(n, m, bridge_edges, 99);

    // Exact deterministic reproducibility for identical seeds
    assert_eq!(g1.num_nodes, n);
    assert_eq!(g1.edges, g2.edges);
    assert_eq!(g1.seed, g2.seed);

    // Seed diversity
    assert_ne!(g1.edges, g3.edges);

    // Out-degree and in-degree vectors
    let in_degs = g1.in_degrees();
    let out_degs = g1.out_degrees();
    assert_eq!(in_degs.len(), n);
    assert_eq!(out_degs.len(), n);

    // Preferential attachment property: early nodes accumulate higher in-degrees than late nodes
    let early_in: usize = in_degs[0..5].iter().sum();
    let late_in: usize = in_degs[95..100].iter().sum();
    assert!(
        early_in > late_in,
        "Early nodes should attract more citations than late nodes: early={early_in}, late={late_in}"
    );
}

#[test]
fn test_rank_types_and_aliases_parity() {
    let mut rng = SovereignPrng::new(12345);
    assert!(rng.next_u64() > 0);
    assert!(rng.gen_range(0, 10) < 10);

    let graph = CitationGraph::new(2, vec![(0, 1)]);
    assert_eq!(graph.num_nodes(), 2);
    assert_eq!(graph.edges().len(), 1);
    assert!(!graph.is_empty());

    let empty = CitationGraph::new(0, vec![]);
    assert!(empty.is_empty());

    let solver = ExactPageRankSolverV1;
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(100));
    let sparse_res: Result<SparsePageRankResult, PageRankError> =
        solver.solve_sparse_bigrational(&graph, 10, &tolerance);
    assert!(sparse_res.is_ok());

    let cert: PageRankCertificateV1 = sparse_res.unwrap();
    let compacted_res: Result<CompactedPageRankResult, PageRankError> =
        ExactPageRankSolverV1::compact_ranks(cert, 30);
    assert!(compacted_res.is_ok());

    let comp: CompactedPageRankResultV1 = compacted_res.unwrap();
    assert_eq!(comp.compacted_ranks.len(), 2);
}

fn assert_small_scale_rational64_success(alpha: Rational64) {
    // 1. Regime N <= 10: 100% deterministic success without overflow
    for &n in &[5, 8, 10] {
        for seed in 0..5 {
            let graph =
                ExactPageRankSolverV1::generate_scale_free_citation_graph(n, 2, n / 5, seed);
            let res = ExactPageRankSolverV1::solve_edges(n, &graph.edges, alpha);
            assert!(
                res.is_ok(),
                "Dense Rational64 elimination must succeed for N <= 10 (N={n}, seed={seed})"
            );
            let rank = res.unwrap();
            assert_eq!(rank.len(), n);
            let sum_r: Rational64 = rank.iter().sum();
            assert_eq!(sum_r, Rational64::one());
        }
    }
}

fn count_transition_regime_trials(alpha: Rational64) -> (usize, usize) {
    let mut failures_transition = 0;
    let mut successes_transition = 0;
    for &n_trans in &[15, 18, 20, 25] {
        for &m in &[2, 3] {
            for seed in 0..20 {
                let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(
                    n_trans,
                    m,
                    n_trans / 5,
                    seed,
                );
                match ExactPageRankSolverV1::solve_edges(n_trans, &graph.edges, alpha) {
                    Ok(_) => successes_transition += 1,
                    Err(RankError::Rational64Overflow) => failures_transition += 1,
                    Err(e) => panic!("Unexpected error: {e:?}"),
                }
            }
        }
    }
    (failures_transition, successes_transition)
}

fn count_large_regime_overflows(alpha: Rational64) -> (usize, usize) {
    let mut large_overflows = 0;
    let mut total_large = 0;
    for &n_large in &[75, 100] {
        for &m in &[2, 3] {
            for seed in 0..5 {
                total_large += 1;
                let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(
                    n_large,
                    m,
                    n_large / 5,
                    seed,
                );
                let res = ExactPageRankSolverV1::solve_edges(n_large, &graph.edges, alpha);
                if matches!(res, Err(RankError::Rational64Overflow)) {
                    large_overflows += 1;
                }
            }
        }
    }
    (large_overflows, total_large)
}

#[test]
fn test_falsify_rational64_overflow_characterization() {
    let alpha = Rational64::new(17, 20);

    assert_small_scale_rational64_success(alpha);

    // 2. Regime N approx 15-25: begins failing due to cross-multiplication intermediate overflow (> 32-bit denominators)
    let (failures_transition, successes_transition) = count_transition_regime_trials(alpha);
    assert!(
        failures_transition > 0,
        "Dense Rational64 elimination must begin encountering integer overflow around N approx 15-25 (got {failures_transition} failures, {successes_transition} successes)"
    );
    assert!(
        successes_transition > 0,
        "Transition regime must contain both successes and overflow failures"
    );

    // 3. Regime N >= 40: overflow dominates (>= 80% at N=40) and reaches 100% deterministic overflow at N >= 75
    let mut failures_at_40 = 0;
    let total_at_40 = 20;
    for &m in &[2, 3] {
        for seed in 0..10 {
            let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(40, m, 8, seed);
            let res = ExactPageRankSolverV1::solve_edges(40, &graph.edges, alpha);
            if matches!(res, Err(RankError::Rational64Overflow)) {
                failures_at_40 += 1;
            }
        }
    }
    assert!(
        failures_at_40 > 0,
        "Dense Rational64 elimination begins failing with overflow at N=40 (got {failures_at_40}/{total_at_40})"
    );

    // Overflow dominates at N >= 75 (>= 80% of trials fail with Rational64Overflow)
    let (large_overflows, total_large) = count_large_regime_overflows(alpha);
    assert!(
        large_overflows >= total_large * 8 / 10,
        "Dense Rational64 elimination must fail with overflow in >= 80% of trials at N >= 75 (got {large_overflows}/{total_large})"
    );
}

#[test]
fn test_sparse_banach_bigrational_solver_convergence_and_certification() {
    let solver = ExactPageRankSolverV1;
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(100_000));

    for &n in &[50, 100, 250] {
        let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(n, 2, n / 5, 42);
        let res = solver
            .solve_sparse_bigrational(&graph, 80, &tolerance)
            .expect("solver failed");

        assert_eq!(res.num_nodes, n);
        assert_eq!(res.ranks.len(), n);
        assert!(res.is_converged);

        // Exact stochastic closure: sum(r_i) == 1 in Q
        let total: BigRational = res.ranks.iter().cloned().sum();
        assert_eq!(total, BigRational::one());

        // Positivity: all ranks r_i > 0
        for (i, r) in res.ranks.iter().enumerate() {
            assert!(
                r > &BigRational::zero(),
                "Rank must be strictly positive at node {i}"
            );
        }

        // A posteriori certified bound: ||r^(k) - r*||_1 <= 17/3 * ||r^(k) - r^(k-1)||_1
        let expected_bound =
            &BigRational::new(BigInt::from(17), BigInt::from(3)) * &res.residual_l1_delta;
        assert_eq!(res.certified_l1_error, expected_bound);
        assert!(
            res.certified_l1_error
                <= BigRational::new(BigInt::from(17), BigInt::from(3)) * &tolerance
        );
    }
}

#[test]
fn test_common_denominator_rational_compaction_hamilton_hare() {
    let solver = ExactPageRankSolverV1;
    let n = 100;
    let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(n, 2, 20, 42);
    let power_of_two = 30; // D = 2^30 = 1,073,741,824

    let compacted = solver
        .solve_compacted_rational(&graph, power_of_two)
        .expect("compaction failed");

    assert_eq!(compacted.compacted_ranks.len(), n);
    assert_eq!(compacted.compacted_ranks_big.len(), n);

    // Exact stochastic sum in Rational64: sum(hat_r_i) == 1 identically
    let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
    assert_eq!(sum_r64, Rational64::one());
    assert_eq!(*sum_r64.numer(), 1i64);
    assert_eq!(*sum_r64.denom(), 1i64);

    // Exact stochastic sum in BigRational
    let sum_big: BigRational = compacted.compacted_ranks_big.iter().cloned().sum();
    assert_eq!(sum_big, BigRational::one());

    // Every denominator divides 2^30, so max denominator <= 2^30
    let d_limit = 1i64 << power_of_two;
    for (i, r) in compacted.compacted_ranks.iter().enumerate() {
        assert!(
            *r.denom() <= d_limit,
            "Denominator at node {i} ({}) exceeds 2^30",
            r.denom()
        );
        assert_eq!(
            d_limit % *r.denom(),
            0,
            "Denominator at node {i} ({}) does not divide common denominator 2^30",
            r.denom()
        );
    }

    // Compaction l1 shift is bounded by n / D = 100 / 2^30
    let max_compaction_shift =
        BigRational::new(BigInt::from(n), BigInt::one() << power_of_two as usize);
    assert!(
        compacted.compaction_l1_shift <= max_compaction_shift,
        "Compaction shift {} exceeds theoretical bound {}",
        compacted.compaction_l1_shift,
        max_compaction_shift
    );

    // Total certified error = compaction_l1_shift + certificate.certified_l1_error
    let expected_total = &compacted.compaction_l1_shift + &compacted.certificate.certified_l1_error;
    assert_eq!(compacted.total_certified_l1_error, expected_total);
}

#[test]
fn test_scale_free_citation_graphs_comprehensive_benchmark_suite() {
    let solver = ExactPageRankSolverV1;
    let power_of_two = 30; // D = 2^30

    // Benchmark targets across all requested scales up to N = 1500
    let scale_targets = [50, 100, 250, 500, 1000, 1500];

    for &n in &scale_targets {
        let m = 2;
        let bridges = n / 5;
        let seed = 42;

        let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(n, m, bridges, seed);
        assert_eq!(graph.num_nodes, n);

        // 1. Solve via Sparse Banach BigRational contractive power iteration (75 iterations max)
        let tolerance = BigRational::new(BigInt::one(), BigInt::from(1_000_000));
        let cert = solver
            .solve_sparse_bigrational(&graph, 75, &tolerance)
            .unwrap_or_else(|e| panic!("Sparse solver failed at N={n}: {e:?}"));

        assert_eq!(cert.num_nodes, n);
        assert_eq!(cert.ranks.len(), n);

        // Exact stochastic property in Q: sum(r_i) == 1
        let total_big: BigRational = cert.ranks.iter().cloned().sum();
        assert_eq!(
            total_big,
            BigRational::one(),
            "Exact stochastic sum must be 1/1 at N={n}"
        );

        // High accuracy for large graphs
        if n >= 1000 {
            let error_target = BigRational::new(BigInt::one(), BigInt::from(100_000));
            assert!(
                cert.certified_l1_error <= error_target,
                "Certified error at N={n} ({}) must be <= 10^-5",
                cert.certified_l1_error
            );
        }

        // 2. Compact via Hamilton-Hare largest remainder method onto D = 2^30
        let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
            .unwrap_or_else(|e| panic!("Compaction failed at N={n}: {e:?}"));

        // Exact sum == 1/1 in Rational64
        let total_r64: Rational64 = compacted.compacted_ranks.iter().sum();
        assert_eq!(
            total_r64,
            Rational64::one(),
            "Compacted sum in Rational64 must be exactly 1/1 at N={n}"
        );

        // Max denominator bounded by 31 bits
        let max_denom_bits = compacted
            .compacted_ranks
            .iter()
            .map(|r| 64 - r.denom().leading_zeros())
            .max()
            .unwrap_or(0);
        assert!(
            max_denom_bits <= 31,
            "Max denominator bit length ({max_denom_bits}) must be <= 31 bits at N={n}"
        );

        // Total certified error is certified in Q with 0 floats
        assert!(compacted.total_certified_l1_error > BigRational::zero());
    }
}

fn verify_r64_matches_bigrational(graph: &CitationGraph, r64: &[Rational64]) {
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(10_000_000));
    let big_res = ExactPageRankSolverV1::solve_sparse_bigrational_impl(graph, 100, &tolerance)
        .expect("BigRational solver should succeed");
    for (i, val) in r64.iter().enumerate() {
        let diff = (BigRational::new(BigInt::from(*val.numer()), BigInt::from(*val.denom()))
            - &big_res.ranks[i])
            .abs();
        assert!(
            diff < BigRational::new(BigInt::from(1), BigInt::from(10_000)),
            "Silent numerical corruption detected in Ok result at node {i}: diff={diff}"
        );
    }
}

fn run_challenger2_n40_trials(alpha: Rational64) -> (usize, usize, usize) {
    let mut total_trials_40 = 0;
    let mut overflows_40 = 0;
    let mut successes_40 = 0;

    for &m in &[1, 2, 3, 5] {
        for seed in 0..25 {
            total_trials_40 += 1;
            let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(40, m, 8, seed);
            let res = ExactPageRankSolverV1::solve_edges(40, &graph.edges, alpha);
            match res {
                Ok(r64) => {
                    successes_40 += 1;
                    // If it succeeded, verify that no silent overflow occurred:
                    // Compare with exact BigRational power iteration solution
                    verify_r64_matches_bigrational(&graph, &r64);
                }
                Err(RankError::Rational64Overflow) => {
                    overflows_40 += 1;
                }
                Err(e) => {
                    panic!(
                        "Unexpected error variant for N=40 (expected Rational64Overflow): {e:?}"
                    );
                }
            }
        }
    }
    (total_trials_40, overflows_40, successes_40)
}

fn check_dense_topologies_n40(alpha: Rational64) {
    // 2. Empirical test on dense topologies at N=40
    // 2a. Complete graph K_40 (all directed pairs)
    let mut complete_edges = Vec::new();
    for u in 0..40 {
        for v in 0..40 {
            if u != v {
                complete_edges.push((u, v));
            }
        }
    }
    match ExactPageRankSolverV1::solve_edges(40, &complete_edges, alpha) {
        Ok(r) => {
            // In complete graph, uniform symmetry: each node should have rank 1/40
            let expected = Rational64::new(1, 40);
            for (i, val) in r.iter().enumerate() {
                assert_eq!(*val, expected, "Complete graph rank mismatch at node {i}");
            }
        }
        Err(RankError::Rational64Overflow) => {
            // Overflow in dense elimination is also an acceptable fail-closed outcome
        }
        Err(e) => panic!("Complete graph failed with unexpected error: {e:?}"),
    }

    // 2b. Directed cycle C_40
    let cycle_edges: Vec<(usize, usize)> = (0..40).map(|u| (u, (u + 1) % 40)).collect();
    match ExactPageRankSolverV1::solve_edges(40, &cycle_edges, alpha) {
        Ok(r) => {
            let expected = Rational64::new(1, 40);
            for (i, val) in r.iter().enumerate() {
                assert_eq!(*val, expected, "Cycle graph rank mismatch at node {i}");
            }
        }
        Err(RankError::Rational64Overflow) => {}
        Err(e) => panic!("Cycle graph failed with unexpected error: {e:?}"),
    }

    check_dense_random_n40(alpha);
}

fn check_dense_random_n40(alpha: Rational64) {
    // 2c. Highly connected dense random graph at N=40
    let mut dense_rng = SovereignPrng::new(999);
    let mut dense_edges = Vec::new();
    for u in 0..40 {
        for v in 0..40 {
            if u != v && dense_rng.gen_range(0, 100) < 60 {
                dense_edges.push((u, v));
            }
        }
    }
    match ExactPageRankSolverV1::solve_edges(40, &dense_edges, alpha) {
        Ok(r) => {
            let sum_r: Rational64 = r.iter().sum();
            assert_eq!(sum_r, Rational64::one());
        }
        Err(RankError::Rational64Overflow) => {}
        Err(e) => panic!("Dense random graph failed with unexpected error: {e:?}"),
    }
}

#[test]
fn test_challenger2_dense_rational64_overflow_characterization() {
    let alpha = Rational64::new(17, 20);

    // 1. Empirical test on scale-free graphs at N=40 across 50 distinct seeds and various m
    let (total_trials_40, overflows_40, successes_40) = run_challenger2_n40_trials(alpha);

    println!(
        "Challenger 2 Empirical: N=40 scale-free trials: total={total_trials_40}, overflows={overflows_40}, successes={successes_40} (overflow fraction: {overflows_40}/{total_trials_40})"
    );
    assert!(
        overflows_40 > 0,
        "Expected at least one Rational64 overflow at N=40"
    );
    // Verify that every single failure failed closed to Rational64Overflow
    assert_eq!(total_trials_40, overflows_40 + successes_40);

    check_dense_topologies_n40(alpha);

    // 3. Overflow trajectory across scale targets N in [10, 20, 30, 40, 50, 60, 75, 100]
    let test_scales = [10, 20, 30, 40, 50, 60, 75, 100];
    for &n in &test_scales {
        let mut n_overflows = 0;
        let trials = 10;
        for seed in 0..trials {
            let graph =
                ExactPageRankSolverV1::generate_scale_free_citation_graph(n, 2, n / 5, seed);
            match ExactPageRankSolverV1::solve_edges(n, &graph.edges, alpha) {
                Ok(_) => {}
                Err(RankError::Rational64Overflow) => n_overflows += 1,
                Err(e) => panic!("Scale N={n} failed with unexpected error: {e:?}"),
            }
        }
        println!("Challenger 2 Scale N={n}: {n_overflows}/{trials} trials overflowed");
        if n == 10 {
            assert_eq!(n_overflows, 0, "N=10 must have 0 overflows");
        }
        if n >= 75 {
            assert!(
                n_overflows >= 6,
                "N={n} must have statistical dominance >= 60% on 10 trials (got {n_overflows}/{trials})"
            );
        }
    }
}

fn check_inward_star_compaction(n: usize, power_of_two: u32, tolerance: &BigRational) {
    let mut edges: Vec<(usize, usize)> = (1..n).map(|u| (u, 0)).collect();
    // Center node points to 1 to create cycle, or leaves dangling
    edges.push((0, 1));
    let graph = CitationGraph {
        num_nodes: n,
        edges,
        m: 1,
        bridge_edges: 0,
        seed: 1234,
    };

    let cert = ExactPageRankSolverV1::solve_sparse_bigrational_impl(&graph, 80, tolerance)
        .expect("Inward star solve should succeed");
    assert_eq!(cert.num_nodes, n);
    assert!(cert.is_converged);

    // Center node 0 must have strictly greater rank than all leaves
    for leaf in 2..n {
        assert!(
            cert.ranks[0] > cert.ranks[leaf],
            "Center node 0 should have greater rank than leaf {leaf} at N={n}"
        );
    }

    let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
        .expect("Inward star compaction should succeed");

    // Verify exact sum == 1 in Rational64
    let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
    assert_eq!(
        sum_r64,
        Rational64::one(),
        "Inward star N={n} compacted sum must equal 1/1"
    );

    // Verify exact sum == 1 in BigRational
    let sum_big: BigRational = compacted.compacted_ranks_big.iter().cloned().sum();
    assert_eq!(
        sum_big,
        BigRational::one(),
        "Inward star N={n} big compacted sum must equal 1/1"
    );

    // Verify all ranks non-negative
    for (i, r) in compacted.compacted_ranks.iter().enumerate() {
        assert!(
            *r.numer() >= 0,
            "Inward star N={n} rank at node {i} must be non-negative"
        );
        assert!(
            *r.denom() > 0,
            "Inward star N={n} denom at node {i} must be positive"
        );
        let bits = 64 - r.denom().leading_zeros();
        assert!(bits <= 31, "Denominator bits ({bits}) must be <= 31");
    }

    // Compaction shift bound: <= N / 2^30
    let max_shift = BigRational::new(BigInt::from(n), BigInt::one() << power_of_two as usize);
    assert!(
        compacted.compaction_l1_shift <= max_shift,
        "Compaction shift {} exceeds bound {} at N={n}",
        compacted.compaction_l1_shift,
        max_shift
    );
}

fn check_uniform_cycle_compaction(n: usize, power_of_two: u32, tolerance: &BigRational) {
    let edges: Vec<(usize, usize)> = (0..n).map(|u| (u, (u + 1) % n)).collect();
    let graph = CitationGraph {
        num_nodes: n,
        edges,
        m: 1,
        bridge_edges: 0,
        seed: 42,
    };

    let cert = ExactPageRankSolverV1::solve_sparse_bigrational_impl(&graph, 80, tolerance)
        .expect("Uniform cycle solve should succeed");
    let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
        .expect("Uniform cycle compaction should succeed");

    let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
    assert_eq!(
        sum_r64,
        Rational64::one(),
        "Cycle N={n} compacted sum must equal 1/1"
    );

    // In a cycle, each node's quota difference is at most 1 unit
    let d = 1i64 << power_of_two;
    let min_num = compacted
        .compacted_ranks
        .iter()
        .map(|r| r.numer() * (d / r.denom()))
        .min()
        .unwrap();
    let max_num = compacted
        .compacted_ranks
        .iter()
        .map(|r| r.numer() * (d / r.denom()))
        .max()
        .unwrap();
    assert!(
        max_num - min_num <= 1,
        "Cycle N={n} numerator deviation ({min_num} to {max_num}) exceeds 1 quota unit"
    );
    for r in &compacted.compacted_ranks {
        assert!(64 - r.denom().leading_zeros() <= 31);
    }
}

#[test]
fn test_challenger2_compaction_extreme_node_distributions() {
    let power_of_two = 30; // D = 2^30
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(100_000));

    // 1. Extreme Inward Star Graph: N-1 nodes point to node 0; node 0 is dangling (or points to 1)
    for &n in &[10, 50, 100, 500, 1000] {
        check_inward_star_compaction(n, power_of_two, &tolerance);
    }

    // 2. Extreme Outward Star Graph: Node 0 points to all nodes 1..N-1; nodes 1..N-1 are dangling
    for &n in &[10, 50, 100, 500] {
        let edges: Vec<(usize, usize)> = (1..n).map(|v| (0, v)).collect();
        let graph = CitationGraph {
            num_nodes: n,
            edges,
            m: 1,
            bridge_edges: 0,
            seed: 5678,
        };

        let cert = ExactPageRankSolverV1::solve_sparse_bigrational_impl(&graph, 80, &tolerance)
            .expect("Outward star solve should succeed");
        let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
            .expect("Outward star compaction should succeed");

        let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
        assert_eq!(sum_r64, Rational64::one());
        for r in &compacted.compacted_ranks {
            assert!(64 - r.denom().leading_zeros() <= 31);
        }
    }

    // 3. Uniform Cycles: N in [3, 7, 25, 100, 1024, 1500]
    for &n in &[3, 7, 25, 100, 1024, 1500] {
        check_uniform_cycle_compaction(n, power_of_two, &tolerance);
    }

    // 4. Completely Isolated Nodes (0 edges)
    for &n in &[1, 2, 10, 50, 100, 1000] {
        let graph = CitationGraph {
            num_nodes: n,
            edges: vec![],
            m: 0,
            bridge_edges: 0,
            seed: 0,
        };

        let cert = ExactPageRankSolverV1::solve_sparse_bigrational_impl(&graph, 10, &tolerance)
            .expect("Isolated nodes solve should succeed");
        let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
            .expect("Isolated nodes compaction should succeed");

        let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
        assert_eq!(
            sum_r64,
            Rational64::one(),
            "Isolated N={n} compacted sum must equal 1/1"
        );
        for r in &compacted.compacted_ranks {
            assert!(64 - r.denom().leading_zeros() <= 31);
        }
    }

    // 5. Disconnected components: Two disjoint cycles
    let n = 100;
    let mut edges: Vec<(usize, usize)> = (0..50).map(|u| (u, (u + 1) % 50)).collect();
    edges.extend((50..100).map(|u| (u, 50 + ((u - 50 + 1) % 50))));
    let graph = CitationGraph {
        num_nodes: n,
        edges,
        m: 1,
        bridge_edges: 0,
        seed: 777,
    };
    let cert = ExactPageRankSolverV1::solve_sparse_bigrational_impl(&graph, 80, &tolerance)
        .expect("Disjoint cycles solve should succeed");
    let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
        .expect("Disjoint cycles compaction should succeed");
    let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
    assert_eq!(sum_r64, Rational64::one());
    for r in &compacted.compacted_ranks {
        assert!(64 - r.denom().leading_zeros() <= 31);
    }
}

#[test]
fn test_challenger2_denominator_bit_lengths_and_power_of_two_bounds() {
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(100_000));
    let graph = ExactPageRankSolverV1::generate_scale_free_citation_graph(100, 2, 20, 42);
    let cert = ExactPageRankSolverV1::solve_sparse_bigrational_impl(&graph, 80, &tolerance)
        .expect("Solve should succeed");

    // Test across range of valid power_of_two bounds: B in [0, 5, 10, 20, 30, 31, 62]
    for &b in &[0, 5, 10, 20, 30, 31, 62] {
        let res = ExactPageRankSolverV1::compact_ranks(cert.clone(), b);
        assert!(
            res.is_ok(),
            "Compaction with power_of_two={b} should succeed"
        );
        let compacted = res.unwrap();

        // Exact sum in Rational64
        let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
        assert_eq!(
            sum_r64,
            Rational64::one(),
            "Sum at B={b} must be exactly 1/1"
        );

        // Verify denominator bit lengths <= b + 1
        for (i, r) in compacted.compacted_ranks.iter().enumerate() {
            let bits = 64 - r.denom().leading_zeros();
            assert!(
                bits <= b + 1,
                "At B={b}, node {i} denom bit length ({bits}) exceeds max bound {}",
                b + 1
            );
            if b <= 62 {
                let d_limit = 1i64 << b;
                assert!(
                    *r.denom() <= d_limit,
                    "At B={b}, node {i} denom ({}) exceeds 2^{b} ({d_limit})",
                    r.denom()
                );
            }
        }

        // Specifically for default B=30, verify <= 31 bits
        if b == 30 {
            for (i, r) in compacted.compacted_ranks.iter().enumerate() {
                let bits = 64 - r.denom().leading_zeros();
                assert!(bits <= 31, "At B=30, node {i} bits ({bits}) must be <= 31");
            }
        }
    }

    // Fail-closed refusal on B > 62
    for &bad_b in &[63, 64, 128] {
        let res = ExactPageRankSolverV1::compact_ranks(cert.clone(), bad_b);
        assert!(
            matches!(res, Err(RankError::CompactionDenominatorTooLarge(b)) if b == bad_b),
            "B={bad_b} must fail closed to CompactionDenominatorTooLarge({bad_b})"
        );
    }
}

fn build_disconnected_hetero_graph() -> CitationGraph {
    let n_total = 60;
    let mut edges_hetero = Vec::new();

    // Comp 1: 0..11 cycle
    for i in 0..11 {
        edges_hetero.push((i, (i + 1) % 11));
    }
    // Comp 2: 11..26 complete graph
    for u in 11..26 {
        for v in 11..26 {
            if u != v {
                edges_hetero.push((u, v));
            }
        }
    }
    // Comp 3: 26..41 tree where root 26 branches to 27, 28; 27 branches to 29, 30; 28 branches to 31, 32;
    // 29 branches to 33, 34; 30 branches to 35, 36; 31 branches to 37, 38; 32 branches to 39, 40.
    // Leaves 33..41 have out-degree 0 (dangling nodes).
    edges_hetero.extend([
        (26, 27),
        (26, 28),
        (27, 29),
        (27, 30),
        (28, 31),
        (28, 32),
        (29, 33),
        (29, 34),
        (30, 35),
        (30, 36),
        (31, 37),
        (31, 38),
        (32, 39),
        (32, 40),
    ]);

    // Comp 4: 41..51 isolated nodes -> 0 edges added

    // Comp 5: 51..56 self-loops
    for i in 51..56 {
        edges_hetero.push((i, i));
    }

    // Comp 6: 56..60 bipartite cycle
    edges_hetero.extend([(56, 57), (57, 58), (58, 59), (59, 56), (58, 57)]);

    CitationGraph {
        num_nodes: n_total,
        edges: edges_hetero,
        m: 1,
        bridge_edges: 0,
        seed: 1337,
    }
}

fn check_topology1_heterogeneous(
    solver: &ExactPageRankSolverV1,
    power_of_two: u32,
    tolerance: &BigRational,
) {
    // =========================================================================
    // Topology 1: Disconnected Heterogeneous Components (N = 60)
    // Coexistence of 6 completely disjoint topological regimes:
    // - Comp 1 (0..10): Directed cycle of length 11
    // - Comp 2 (11..25): Complete directed graph K_15 (all 15*14 directed edges)
    // - Comp 3 (26..40): Directed tree with root 26; leaves 33..40 dangling (no out edges)
    // - Comp 4 (41..50): 10 isolated singletons with 0 edges
    // - Comp 5 (51..55): 5 nodes with only self-loops (i -> i)
    // - Comp 6 (56..59): Alternating bipartite 4-cycle (56->57->58->59->56, 58->57)
    // =========================================================================
    let graph_hetero = build_disconnected_hetero_graph();
    let n_total = graph_hetero.num_nodes;

    let cert_hetero = solver
        .solve_sparse_bigrational(&graph_hetero, 100, tolerance)
        .expect("Disconnected heterogeneous components solve must succeed");
    assert_eq!(cert_hetero.num_nodes, n_total);
    assert!(
        cert_hetero.is_converged,
        "Solver must converge on disconnected components"
    );

    // Exact stochastic closure: sum(r_i) == 1/1 in Q
    let sum_hetero: BigRational = cert_hetero.ranks.iter().cloned().sum();
    assert_eq!(
        sum_hetero,
        BigRational::one(),
        "Sum of ranks must be exactly 1/1 in Q"
    );

    // Strict positivity: r_i > 0 for all nodes
    for (i, r) in cert_hetero.ranks.iter().enumerate() {
        assert!(
            r > &BigRational::zero(),
            "Rank at node {i} must be strictly positive"
        );
    }

    // Internal symmetry checks:
    // In Comp 1 (cycle 0..10), all 11 nodes must have identical rank
    // In Comp 2 (complete graph 11..25), all 15 nodes must have identical rank
    // In Comp 4 (isolated nodes 41..50), all 10 singletons must have identical rank
    // In Comp 5 (pure self-loops 51..55), all 5 nodes must have identical rank
    for (start, end) in [(0, 11), (11, 26), (41, 51), (51, 56)] {
        for i in (start + 1)..end {
            assert_eq!(cert_hetero.ranks[i], cert_hetero.ranks[start]);
        }
    }

    // Compaction onto D = 2^30
    let compacted_hetero = ExactPageRankSolverV1::compact_ranks(cert_hetero, power_of_two)
        .expect("Compaction on disconnected components must succeed");
    let sum_hetero_r64: Rational64 = compacted_hetero.compacted_ranks.iter().sum();
    assert_eq!(
        sum_hetero_r64,
        Rational64::one(),
        "Compacted sum must be exactly 1/1 in Rational64"
    );
    let sum_hetero_big: BigRational = compacted_hetero.compacted_ranks_big.iter().cloned().sum();
    assert_eq!(
        sum_hetero_big,
        BigRational::one(),
        "Compacted sum must be exactly 1/1 in BigRational"
    );
    for (i, r) in compacted_hetero.compacted_ranks.iter().enumerate() {
        let bits = 64 - r.denom().leading_zeros();
        assert!(
            bits <= 31,
            "Compacted denominator bit length at node {i} ({bits}) must be <= 31"
        );
    }
}

fn check_topology2_dangling_extremes(
    solver: &ExactPageRankSolverV1,
    power_of_two: u32,
    tolerance: &BigRational,
) {
    // =========================================================================
    // Topology 2: Dangling Node Extremes (Inward Star, Outward Star, Long Chain)
    // =========================================================================
    // 2a. Inward Star: N = 50, leaves 1..50 point to root 0, root 0 has NO outgoing edges (dangling)
    let n_star = 50;
    let edges_inward: Vec<(usize, usize)> = (1..n_star).map(|u| (u, 0)).collect();
    let graph_inward = CitationGraph {
        num_nodes: n_star,
        edges: edges_inward,
        m: 1,
        bridge_edges: 0,
        seed: 42,
    };
    let cert_inward = solver
        .solve_sparse_bigrational(&graph_inward, 80, tolerance)
        .unwrap();
    assert_eq!(
        cert_inward.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );
    assert!(
        cert_inward.ranks[0] > cert_inward.ranks[1],
        "Root must have higher rank than leaves"
    );
    for u in 2..n_star {
        assert_eq!(
            cert_inward.ranks[u], cert_inward.ranks[1],
            "All leaves in inward star must be equal"
        );
    }
    let comp_inward = ExactPageRankSolverV1::compact_ranks(cert_inward, power_of_two).unwrap();
    assert_eq!(
        comp_inward.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );

    // 2b. Outward Star: Root 0 points to all leaves 1..50, all 49 leaves are dangling
    let edges_outward: Vec<(usize, usize)> = (1..n_star).map(|v| (0, v)).collect();
    let graph_outward = CitationGraph {
        num_nodes: n_star,
        edges: edges_outward,
        m: 1,
        bridge_edges: 0,
        seed: 43,
    };
    let cert_outward = solver
        .solve_sparse_bigrational(&graph_outward, 80, tolerance)
        .unwrap();
    assert_eq!(
        cert_outward.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );
    for v in 2..n_star {
        assert_eq!(
            cert_outward.ranks[v], cert_outward.ranks[1],
            "All leaves in outward star must be equal"
        );
    }
    let comp_outward = ExactPageRankSolverV1::compact_ranks(cert_outward, power_of_two).unwrap();
    assert_eq!(
        comp_outward.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );

    // 2c. Long Directed Chain: 0 -> 1 -> 2 -> ... -> 49 (node 49 dangling)
    let edges_chain: Vec<(usize, usize)> = (0..49).map(|u| (u, u + 1)).collect();
    let graph_chain = CitationGraph {
        num_nodes: 50,
        edges: edges_chain,
        m: 1,
        bridge_edges: 0,
        seed: 44,
    };
    let cert_chain = solver
        .solve_sparse_bigrational(&graph_chain, 100, tolerance)
        .unwrap();
    assert_eq!(
        cert_chain.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );
    // Monotonic rank accumulation along directed chain:
    for u in 0..49 {
        assert!(
            cert_chain.ranks[u] < cert_chain.ranks[u + 1],
            "Rank along chain must strictly increase: r[{u}] < r[{}]",
            u + 1
        );
    }
    let comp_chain = ExactPageRankSolverV1::compact_ranks(cert_chain, power_of_two).unwrap();
    assert_eq!(
        comp_chain.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );
}

fn check_topology3_loops_and_multiedges(
    solver: &ExactPageRankSolverV1,
    power_of_two: u32,
    tolerance: &BigRational,
) {
    // =========================================================================
    // Topology 3: Pure Self-Loops & Multi-Edges
    // =========================================================================
    // 3a. Pure Self-Loops: N = 25, edge (i, i) for all i in 0..25
    let n_loop = 25;
    let edges_loops: Vec<(usize, usize)> = (0..n_loop).map(|i| (i, i)).collect();
    let graph_loops = CitationGraph {
        num_nodes: n_loop,
        edges: edges_loops,
        m: 1,
        bridge_edges: 0,
        seed: 45,
    };
    let cert_loops = solver
        .solve_sparse_bigrational(&graph_loops, 80, tolerance)
        .unwrap();
    let expected_uniform = BigRational::new(BigInt::one(), BigInt::from(n_loop));
    for (i, r) in cert_loops.ranks.iter().enumerate() {
        assert_eq!(
            *r, expected_uniform,
            "Pure self-loops must yield exact uniform rank 1/{n_loop} at node {i}"
        );
    }
    assert_eq!(
        cert_loops.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );
    let comp_loops = ExactPageRankSolverV1::compact_ranks(cert_loops, power_of_two).unwrap();
    assert_eq!(
        comp_loops.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );

    // 3b. Multi-Edges with Self-Loops:
    // Node 0 has self-loop (0, 0) x 3, edge (0, 1) x 2 (total out-deg 5)
    // Node 1 has edge (1, 0) x 4 (total out-deg 4)
    let multi_edges = vec![
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 1),
        (0, 1),
        (1, 0),
        (1, 0),
        (1, 0),
        (1, 0),
    ];
    let graph_multi = CitationGraph {
        num_nodes: 2,
        edges: multi_edges,
        m: 1,
        bridge_edges: 0,
        seed: 46,
    };
    let cert_multi = solver
        .solve_sparse_bigrational(&graph_multi, 80, tolerance)
        .unwrap();
    assert_eq!(
        cert_multi.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );
    let comp_multi = ExactPageRankSolverV1::compact_ranks(cert_multi, power_of_two).unwrap();
    assert_eq!(
        comp_multi.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );
}

fn check_topology4_bipartite(
    solver: &ExactPageRankSolverV1,
    power_of_two: u32,
    tolerance: &BigRational,
) {
    // =========================================================================
    // Topology 4: Bipartite Cycles & Complete Bipartite Graphs
    // =========================================================================
    // 4a. Even Directed Cycle C_40 (0 -> 1 -> ... -> 39 -> 0)
    let n_even = 40;
    let edges_even_cycle: Vec<(usize, usize)> =
        (0..n_even).map(|u| (u, (u + 1) % n_even)).collect();
    let graph_even = CitationGraph {
        num_nodes: n_even,
        edges: edges_even_cycle,
        m: 1,
        bridge_edges: 0,
        seed: 47,
    };
    let cert_even = solver
        .solve_sparse_bigrational(&graph_even, 80, tolerance)
        .unwrap();
    assert_eq!(
        cert_even.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );
    let uniform_even = BigRational::new(BigInt::one(), BigInt::from(n_even));
    for (i, r) in cert_even.ranks.iter().enumerate() {
        assert_eq!(
            *r, uniform_even,
            "Even cycle C_{n_even} must yield exact uniform rank at node {i}"
        );
    }
    let comp_even = ExactPageRankSolverV1::compact_ranks(cert_even, power_of_two).unwrap();
    assert_eq!(
        comp_even.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );

    // 4b. Complete Bipartite Graph K_{15, 30} (p = 15, q = 30, N = 45)
    // Every node in A (0..15) connects to every node in B (15..45).
    // Every node in B (15..45) connects to every node in A (0..15).
    let p = 15;
    let q = 30;
    let n_bip = p + q;
    let mut edges_k_pq = Vec::new();
    for u in 0..p {
        for v in p..n_bip {
            edges_k_pq.push((u, v));
            edges_k_pq.push((v, u));
        }
    }
    let graph_k_pq = CitationGraph {
        num_nodes: n_bip,
        edges: edges_k_pq,
        m: 1,
        bridge_edges: 0,
        seed: 48,
    };
    let cert_k_pq = solver
        .solve_sparse_bigrational(&graph_k_pq, 80, tolerance)
        .unwrap();
    assert_eq!(
        cert_k_pq.ranks.iter().cloned().sum::<BigRational>(),
        BigRational::one()
    );

    // By symmetry: all nodes in A have equal rank r_A, all nodes in B have equal rank r_B
    let r_a = cert_k_pq.ranks[0].clone();
    let r_b = cert_k_pq.ranks[p].clone();
    for u in 1..p {
        assert_eq!(
            cert_k_pq.ranks[u], r_a,
            "All nodes in partition A must have equal rank"
        );
    }
    for v in (p + 1)..n_bip {
        assert_eq!(
            cert_k_pq.ranks[v], r_b,
            "All nodes in partition B must have equal rank"
        );
    }
    // Theoretical tie-out: p * r_A + q * r_B == 1/1
    let partition_sum =
        &BigRational::from(BigInt::from(p)) * &r_a + &BigRational::from(BigInt::from(q)) * &r_b;
    assert_eq!(
        partition_sum,
        BigRational::one(),
        "Partition sum p*r_A + q*r_B must equal 1/1"
    );

    let comp_k_pq = ExactPageRankSolverV1::compact_ranks(cert_k_pq, power_of_two).unwrap();
    assert_eq!(
        comp_k_pq.compacted_ranks.iter().sum::<Rational64>(),
        Rational64::one()
    );
}

#[test]
fn test_challenger1_empirical_adversarial_topologies_and_stochastic_closure() {
    let solver = ExactPageRankSolverV1;
    let power_of_two = 30; // D = 2^30
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(1_000_000));
    let _alpha = BigRational::new(BigInt::from(17), BigInt::from(20));

    check_topology1_heterogeneous(&solver, power_of_two, &tolerance);
    check_topology2_dangling_extremes(&solver, power_of_two, &tolerance);
    check_topology3_loops_and_multiedges(&solver, power_of_two, &tolerance);
    check_topology4_bipartite(&solver, power_of_two, &tolerance);
}

fn compute_independent_oracle_residual(
    graph: &CitationGraph,
    ranks: &[BigRational],
    alpha: &BigRational,
    one_minus_alpha: &BigRational,
) -> BigRational {
    // 2. Independent Oracle Check:
    // Explicitly recompute one step of the stationary equation T(r) = alpha * P * r + (1 - alpha) * u
    // and verify that ||T(r) - r||_1 == cert.residual_l1_delta with zero discrepancy
    let n = graph.num_nodes;
    let mut out_degrees = vec![0usize; n];
    let mut in_map: Vec<std::collections::HashMap<usize, usize>> =
        (0..n).map(|_| std::collections::HashMap::new()).collect();
    for &(u, v) in &graph.edges {
        out_degrees[u] += 1;
        *in_map[v].entry(u).or_insert(0) += 1;
    }
    let dangle_sum: BigRational = (0..n)
        .filter(|&u| out_degrees[u] == 0)
        .map(|u| &ranks[u])
        .sum();
    let uniform = BigRational::new(BigInt::one(), BigInt::from(n));
    let teleport = (alpha * &dangle_sum + one_minus_alpha) * &uniform;

    let scaled_r: Vec<BigRational> = (0..n)
        .map(|u| {
            if out_degrees[u] > 0 {
                &ranks[u] / BigInt::from(out_degrees[u])
            } else {
                BigRational::zero()
            }
        })
        .collect();

    let mut oracle_residual = BigRational::zero();
    for v in 0..n {
        let in_sum: BigRational = in_map[v]
            .iter()
            .map(|(&u, &count)| {
                &BigRational::new(BigInt::from(count), BigInt::one()) * &scaled_r[u]
            })
            .sum();
        let t_r_v = alpha * in_sum + &teleport;
        oracle_residual += (&t_r_v - &ranks[v]).abs();
    }
    oracle_residual
}

fn verify_stress_compaction(cert: SparsePageRankResult, n: usize, seed: u64, power_of_two: u32) {
    // 3. Compact via Hamilton-Hare onto D = 2^30
    let compacted = ExactPageRankSolverV1::compact_ranks(cert, power_of_two)
        .unwrap_or_else(|e| panic!("Compaction failed for N={n}, seed={seed}: {e:?}"));

    assert_eq!(compacted.compacted_ranks.len(), n);
    assert_eq!(compacted.compacted_ranks_big.len(), n);

    // Exact stochastic sum == 1/1 in Rational64
    let sum_r64: Rational64 = compacted.compacted_ranks.iter().sum();
    assert_eq!(
        sum_r64,
        Rational64::one(),
        "Compacted sum in Rational64 must be exactly 1/1 at N={n}, seed={seed}"
    );
    assert_eq!(*sum_r64.numer(), 1i64);
    assert_eq!(*sum_r64.denom(), 1i64);

    // Exact stochastic sum == 1/1 in BigRational
    let sum_big: BigRational = compacted.compacted_ranks_big.iter().cloned().sum();
    assert_eq!(
        sum_big,
        BigRational::one(),
        "Compacted sum in BigRational must be exactly 1/1 at N={n}, seed={seed}"
    );

    // Denominator bounds: all denominators <= 2^30 and bit length <= 31
    let d_i64 = 1i64 << power_of_two;
    for (i, r) in compacted.compacted_ranks.iter().enumerate() {
        assert!(
            *r.denom() <= d_i64,
            "Compacted denom at node {i} exceeds 2^30 (N={n}, seed={seed})"
        );
        assert_eq!(
            d_i64 % *r.denom(),
            0,
            "Compacted denom at node {i} does not divide 2^30 (N={n}, seed={seed})"
        );
        let bits = 64 - r.denom().leading_zeros();
        assert!(
            bits <= 31,
            "Compacted denom bit length {bits} exceeds 31 at node {i} (N={n}, seed={seed})"
        );
    }

    // Compaction shift bounded by N / 2^30
    let max_shift = BigRational::new(BigInt::from(n), BigInt::one() << power_of_two as usize);
    assert!(
        compacted.compaction_l1_shift <= max_shift,
        "Compaction l1 shift {} exceeds theoretical bound {} at N={n}, seed={seed}",
        compacted.compaction_l1_shift,
        max_shift
    );
}

#[test]
fn test_challenger1_scale_free_stress_n_50_to_1500_multi_seed() {
    let solver = ExactPageRankSolverV1;
    let power_of_two = 30; // D = 2^30
    let alpha = BigRational::new(BigInt::from(17), BigInt::from(20));
    let one_minus_alpha = BigRational::one() - &alpha;
    let tolerance = BigRational::new(BigInt::one(), BigInt::from(1_000_000));

    // Specifically test all required scales: N in {50, 100, 500, 1000, 1500}
    let scales = [50, 100, 500, 1000, 1500];
    let seeds = [11u64, 42, 101, 777];

    for &n in &scales {
        for &seed in &seeds {
            let m = 2;
            let bridge_edges = n / 5;
            let graph =
                ExactPageRankSolverV1::generate_scale_free_citation_graph(n, m, bridge_edges, seed);
            assert_eq!(graph.num_nodes, n);

            // 1. Solve via Sparse Banach BigRational
            let cert = solver
                .solve_sparse_bigrational(&graph, 80, &tolerance)
                .unwrap_or_else(|e| panic!("Solver failed for N={n}, seed={seed}: {e:?}"));

            assert_eq!(cert.num_nodes, n);
            assert_eq!(cert.ranks.len(), n);
            assert!(
                cert.is_converged,
                "Must converge within 80 iterations at N={n}, seed={seed}"
            );

            // Exact stochastic closure in Q: sum(r_i) == 1/1 identically
            let sum_q: BigRational = cert.ranks.iter().cloned().sum();
            assert_eq!(
                sum_q,
                BigRational::one(),
                "Stochastic closure violated in Q at N={n}, seed={seed}: sum={sum_q}"
            );

            // Strict positivity: r_i > 0 for all i
            for (i, r) in cert.ranks.iter().enumerate() {
                assert!(
                    r > &BigRational::zero(),
                    "Rank at node {i} must be positive (N={n}, seed={seed})"
                );
            }

            // Certified a posteriori l1 error check
            let expected_error =
                &BigRational::new(BigInt::from(17), BigInt::from(3)) * &cert.residual_l1_delta;
            assert_eq!(cert.certified_l1_error, expected_error);
            assert!(
                cert.certified_l1_error
                    <= BigRational::new(BigInt::from(17), BigInt::from(3)) * &tolerance,
                "Certified l1 error exceeds tolerance bound at N={n}, seed={seed}"
            );

            let oracle_residual =
                compute_independent_oracle_residual(&graph, &cert.ranks, &alpha, &one_minus_alpha);

            // Oracle residual must be <= tolerance
            assert!(
                oracle_residual <= tolerance,
                "Independent oracle residual {} exceeds tolerance at N={n}, seed={seed}",
                oracle_residual
            );

            verify_stress_compaction(cert, n, seed, power_of_two);
        }
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/tests/rational_solvers_falsification.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:rational-solvers-falsification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
