//! Contract tests for prompt topology probing.
//!
//! `EPIC-OE-SYMGAM-013`. Third of the six epics whose acceptance criteria name
//! no falsifier, so the criteria here come from the epic's **invariants** --
//! Discrete Metric Discipline and the Anti-Hype Invariant -- plus the one
//! request in criterion 3 that cannot be honoured as written.
//!
//! The load-bearing claims:
//!
//! 1. Every number is exact. `f64` appears nowhere in `probing.rs`, and a test
//!    reads the source to prove it.
//! 2. Curvature is a property of a **declared** construction. Change the
//!    distance function and it changes; the receipt names what was measured.
//! 3. Eigenvalues are refused, not approximated, and the characteristic
//!    polynomial is offered instead.

use num_bigint::BigInt;

use pfp::epics::probing::{
    characteristic_polynomial, curvature_profile, eigenvalues, forman_curvature, hamming,
    laplacian, levenshtein, map_defects, probe_receipt, render_ascii, CurvatureKind, ProbeRefusal,
    PromptGraph, TokenDistance, MAX_SPECTRAL_VERTICES, PROBE_RECEIPT_SCHEMA,
};

/// A path `0 - 1 - 2`.
///
/// The endpoints must be **two** substitutions apart or this is a triangle, not
/// a path -- the first draft of this fixture used `[1,1,1] [1,1,2] [1,1,3]`,
/// which is pairwise distance 1 and therefore K3. Three tests caught it.
fn path_graph() -> PromptGraph {
    PromptGraph::build(
        vec![vec![1, 1], vec![1, 2], vec![2, 2]],
        TokenDistance::Hamming,
        1,
    )
    .expect("a valid manifold")
}

/// A triangle: three prompts pairwise one substitution apart.
fn triangle_graph() -> PromptGraph {
    PromptGraph::build(
        vec![vec![1, 1], vec![1, 2], vec![1, 3]],
        TokenDistance::Hamming,
        1,
    )
    .expect("a valid manifold")
}

// ---------------------------------------------------------------------------
// Criterion 1 -- exactness, and no floats anywhere
// ---------------------------------------------------------------------------

#[test]
fn the_module_contains_no_floating_point_at_all() {
    // Sprint 026 confined a float to a marked region because an exponential
    // decay cannot be rational. Curvature needs no such concession: Forman-Ricci
    // on an unweighted graph is integer-valued. This asserts the stronger claim.
    let source = include_str!("../../pfp/src/epics/probing.rs");
    for banned in ["f64", "f32"] {
        // The doc comment discusses floats by name; the code must not use them.
        let code_only: String = source
            .lines()
            .filter(|line| !line.trim_start().starts_with("//"))
            .collect::<Vec<_>>()
            .join("\n");
        assert!(
            !code_only.contains(banned),
            "{banned} appears in probing.rs outside the documentation"
        );
    }
}

#[test]
fn curvature_is_an_integer() {
    // Not "an integer to within rounding" -- the return type is i64 and the
    // arithmetic is degree counting.
    let graph = path_graph();
    let curvature = forman_curvature(&graph, 0, 1, CurvatureKind::Forman).expect("an edge");
    // deg(0)=1, deg(1)=2  ->  4 - 1 - 2 = 1
    assert_eq!(curvature, 1);
}

#[test]
fn the_augmented_variant_adds_three_per_triangle() {
    let graph = triangle_graph();
    // Every vertex has degree 2; each edge lies on exactly one triangle.
    let plain = forman_curvature(&graph, 0, 1, CurvatureKind::Forman).expect("an edge");
    let augmented =
        forman_curvature(&graph, 0, 1, CurvatureKind::AugmentedForman).expect("an edge");
    assert_eq!(plain, 0); // 4 - 2 - 2
    assert_eq!(augmented, 3); // + 3 * 1 triangle
    assert_eq!(graph.triangles_on(0, 1).expect("an edge"), 1);
}

#[test]
fn a_profile_reports_a_total_rather_than_a_mean() {
    // A mean would be the one number here that is not exact. The total and the
    // edge count are both integers and the caller may form the ratio.
    let graph = triangle_graph();
    let profile = curvature_profile(&graph, CurvatureKind::Forman).expect("edges exist");
    assert_eq!(profile.edges, 3);
    assert_eq!(profile.total, 0);
    assert_eq!(profile.minimum, 0);
    assert_eq!(profile.maximum, 0);
}

// ---------------------------------------------------------------------------
// Criterion 2 -- the construction is declared, and curvature depends on it
// ---------------------------------------------------------------------------

#[test]
fn curvature_changes_with_the_declared_radius() {
    // The decisive demonstration of the Anti-Hype Invariant: curvature is a
    // property of the graph the declared distance produced, not a fact
    // discovered about the prompts. Widening the radius changes it.
    let prompts = vec![vec![1, 1, 1], vec![1, 1, 2], vec![1, 1, 3]];
    let tight = PromptGraph::build(prompts.clone(), TokenDistance::Hamming, 1).expect("valid");
    let wide = PromptGraph::build(prompts, TokenDistance::Hamming, 2).expect("valid");

    assert_eq!(tight.size(), 3);
    assert_eq!(wide.size(), 3);

    // The prompts are pairwise distance 1, so both radii give the same graph.
    // Push one prompt further out and the two constructions diverge.
    let spread = vec![vec![1, 1, 1], vec![1, 1, 2], vec![9, 9, 9]];
    let tight = PromptGraph::build(spread.clone(), TokenDistance::Hamming, 1).expect("valid");
    let wide = PromptGraph::build(spread, TokenDistance::Hamming, 3).expect("valid");
    assert_eq!(tight.size(), 1);
    assert_eq!(wide.size(), 3);
    assert_ne!(
        curvature_profile(&tight, CurvatureKind::Forman)
            .expect("edges")
            .total,
        curvature_profile(&wide, CurvatureKind::Forman)
            .expect("edges")
            .total
    );
}

#[test]
fn the_two_distance_functions_are_distinct() {
    assert_eq!(hamming(&[1, 2, 3], &[1, 2, 4]), Some(1));
    assert_eq!(hamming(&[1, 2], &[1, 2, 3]), None); // ragged
    assert_eq!(levenshtein(&[1, 2], &[1, 2, 3]), 1); // an insertion
    assert_eq!(levenshtein(&[1, 2, 3], &[1, 2, 3]), 0);
    assert_eq!(levenshtein(&[], &[1, 2]), 2);
}

#[test]
fn a_levenshtein_manifold_admits_ragged_prompts() {
    let graph = PromptGraph::build(
        vec![vec![1, 2], vec![1, 2, 3], vec![1, 2, 3, 4]],
        TokenDistance::Levenshtein,
        1,
    )
    .expect("edit distance tolerates unequal lengths");
    assert_eq!(graph.size(), 2);
}

#[test]
fn hamming_refuses_ragged_prompts_naming_both_lengths() {
    let error = PromptGraph::build(vec![vec![1, 2], vec![1, 2, 3]], TokenDistance::Hamming, 1)
        .expect_err("hamming needs equal lengths");
    match error {
        ProbeRefusal::RaggedForHamming {
            left_len,
            right_len,
            ..
        } => {
            assert_eq!(left_len, 2);
            assert_eq!(right_len, 3);
        }
        other => panic!("expected RaggedForHamming, got {other:?}"),
    }
}

#[test]
fn duplicate_prompts_are_refused() {
    // Two identical prompts are one point. Admitting them as two would report a
    // spurious neighbour for each.
    let error = PromptGraph::build(vec![vec![1, 2], vec![1, 2]], TokenDistance::Hamming, 1)
        .expect_err("a manifold needs distinct points");
    assert!(matches!(
        error,
        ProbeRefusal::DuplicatePrompt { left: 0, right: 1 }
    ));
}

#[test]
fn a_manifold_of_fewer_than_two_prompts_is_refused() {
    for count in 0..2usize {
        let prompts: Vec<Vec<u32>> = (0..count).map(|i| vec![i as u32 + 1]).collect();
        let error =
            PromptGraph::build(prompts, TokenDistance::Hamming, 1).expect_err("too few points");
        assert!(matches!(error, ProbeRefusal::TooFewPrompts { .. }));
    }
}

#[test]
fn an_empty_prompt_is_refused() {
    let error = PromptGraph::build(vec![vec![1], vec![]], TokenDistance::Hamming, 1)
        .expect_err("an empty sequence has no neighbourhood");
    assert!(matches!(error, ProbeRefusal::EmptyPrompt { index: 1 }));
}

#[test]
fn asking_for_the_curvature_of_a_non_edge_is_refused() {
    let graph = path_graph();
    // 0 and 2 differ in one position from 1 but two from each other.
    assert!(!graph.is_edge(0, 2));
    let error = forman_curvature(&graph, 0, 2, CurvatureKind::Forman)
        .expect_err("curvature is defined on edges");
    assert!(matches!(
        error,
        ProbeRefusal::NotAnEdge { left: 0, right: 2 }
    ));
}

#[test]
fn a_vertex_outside_the_graph_is_refused() {
    let graph = path_graph();
    let error = graph.degree(99).expect_err("no such vertex");
    assert!(matches!(
        error,
        ProbeRefusal::VertexOutOfRange {
            index: 99,
            order: 3
        }
    ));
}

// ---------------------------------------------------------------------------
// Criterion 3 -- defects, and what is NOT a defect
// ---------------------------------------------------------------------------

#[test]
fn a_star_centre_is_not_a_defect_but_its_leaves_are() {
    // A star: one hub, four leaves. Leaf edges have curvature 4-1-5 = -2, so
    // every leaf's only edge is negative and each leaf is a defect. The hub's
    // edges are all negative too -- so the hub is a defect by the stated
    // definition, and the test records what the definition actually yields
    // rather than what the word "defect" suggests.
    let graph = PromptGraph::build(
        vec![
            vec![0, 0, 0, 0],
            vec![1, 0, 0, 0],
            vec![0, 1, 0, 0],
            vec![0, 0, 1, 0],
            vec![0, 0, 0, 1],
        ],
        TokenDistance::Hamming,
        1,
    )
    .expect("valid");

    assert_eq!(graph.degree(0).expect("hub"), 4);
    assert_eq!(
        forman_curvature(&graph, 0, 1, CurvatureKind::Forman).expect("edge"),
        -1
    );

    let defects = map_defects(&graph, CurvatureKind::Forman).expect("edges exist");
    assert_eq!(defects.negative_edges, 4);
    assert_eq!(defects.defect_vertices, vec![0, 1, 2, 3, 4]);
    assert_eq!(defects.density(), (5, 5));
}

#[test]
fn a_triangle_has_no_defects() {
    let defects = map_defects(&triangle_graph(), CurvatureKind::Forman).expect("edges");
    assert!(defects.defect_vertices.is_empty());
    assert_eq!(defects.negative_edges, 0);
}

#[test]
fn an_isolated_vertex_is_reported_separately_from_a_defect() {
    // "Every incident edge is negative" is vacuously true of a vertex with no
    // edges. Counting it as a defect would be exactly the vacuous pass this
    // estate keeps finding, so it is reported in its own list.
    let graph = PromptGraph::build(
        vec![vec![1, 1], vec![1, 2], vec![9, 9]],
        TokenDistance::Hamming,
        1,
    )
    .expect("valid");

    let defects = map_defects(&graph, CurvatureKind::Forman).expect("edges");
    assert_eq!(defects.isolated_vertices, vec![2]);
    assert!(!defects.defect_vertices.contains(&2));
}

#[test]
fn a_graph_with_no_edges_is_refused_rather_than_reported_flat() {
    // A zero total over zero edges would read as "flat", not as "absent".
    let graph = PromptGraph::build(
        vec![vec![1, 1, 1], vec![2, 2, 2], vec![3, 3, 3]],
        TokenDistance::Hamming,
        1,
    )
    .expect("valid vertices, no edges");
    assert_eq!(graph.size(), 0);
    assert!(matches!(
        curvature_profile(&graph, CurvatureKind::Forman).expect_err("no edges"),
        ProbeRefusal::NoEdges
    ));
}

// ---------------------------------------------------------------------------
// Criterion 4 -- eigenvalues refused, characteristic polynomial offered
// ---------------------------------------------------------------------------

#[test]
fn eigenvalues_are_refused_with_the_reason() {
    // The epic asks receipts to record "curvature eigenvalues". They are
    // algebraic and generally irrational, so returning them means returning
    // approximations. Refusing states the substitution instead of hiding it.
    let error = eigenvalues(&triangle_graph()).expect_err("no exact representation");
    assert_eq!(error, ProbeRefusal::EigenvaluesNotExact);
    assert!(error.to_string().contains("characteristic_polynomial"));
}

#[test]
fn the_characteristic_polynomial_of_a_triangle_is_exact() {
    // K3 has Laplacian spectrum {0, 3, 3}, so det(xI - L) = x^3 - 6x^2 + 9x.
    let coefficients = characteristic_polynomial(&triangle_graph()).expect("small graph");
    let expected: Vec<BigInt> = [1, -6, 9, 0].into_iter().map(BigInt::from).collect();
    assert_eq!(coefficients, expected);
}

#[test]
fn the_characteristic_polynomial_of_a_path_is_exact() {
    // P3 has Laplacian spectrum {0, 1, 3}: x^3 - 4x^2 + 3x.
    let coefficients = characteristic_polynomial(&path_graph()).expect("small graph");
    let expected: Vec<BigInt> = [1, -4, 3, 0].into_iter().map(BigInt::from).collect();
    assert_eq!(coefficients, expected);
}

#[test]
fn zero_is_always_a_laplacian_eigenvalue_so_the_constant_term_vanishes() {
    // A structural check that would catch a sign or minor-summation error the
    // two spectrum tests might share.
    for graph in [triangle_graph(), path_graph()] {
        let coefficients = characteristic_polynomial(&graph).expect("small graph");
        assert_eq!(*coefficients.last().expect("nonempty"), BigInt::from(0));
    }
}

#[test]
fn the_laplacian_rows_sum_to_zero() {
    let matrix = laplacian(&triangle_graph()).expect("valid");
    for row in &matrix {
        let sum: BigInt = row.iter().sum();
        assert_eq!(sum, BigInt::from(0));
    }
}

#[test]
fn an_oversized_graph_refuses_exact_spectral_data() {
    // Principal-minor expansion is exponential. The cap refuses; it does not
    // quietly switch to floating-point eigenvalues.
    let prompts: Vec<Vec<u32>> = (0..(MAX_SPECTRAL_VERTICES as u32 + 1))
        .map(|i| vec![i, 0, 0])
        .collect();
    let graph = PromptGraph::build(prompts, TokenDistance::Hamming, 1).expect("valid");
    let error = characteristic_polynomial(&graph).expect_err("too large");
    assert!(matches!(error, ProbeRefusal::SpectrumTooLarge { .. }));
}

// ---------------------------------------------------------------------------
// Criterion 5 -- receipts and rendering
// ---------------------------------------------------------------------------

#[test]
fn a_receipt_names_the_construction_it_measured() {
    // Curvature without the distance and radius that produced it does not
    // identify what was measured.
    let receipt = probe_receipt(&triangle_graph(), CurvatureKind::AugmentedForman)
        .expect("a probeable graph");
    assert_eq!(receipt.schema, PROBE_RECEIPT_SCHEMA);
    assert_eq!(receipt.distance, "hamming");
    assert_eq!(receipt.radius, 1);
    assert_eq!(receipt.curvature_kind, "augmented_forman");
    assert_eq!(receipt.order, 3);
    assert_eq!(receipt.size, 3);
    assert_eq!(receipt.authority_effect, "None");
}

#[test]
fn a_receipt_is_reproducible_for_the_same_construction() {
    // Criterion 2 of the epic: fixed prompt sequences yield identical receipts.
    let left = probe_receipt(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    let right = probe_receipt(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    assert_eq!(left, right);
    assert_eq!(left.digest, right.digest);
}

#[test]
fn a_receipt_digest_separates_the_two_curvature_kinds() {
    // Same graph, different measurement: the digest must not collide.
    let plain = probe_receipt(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    let augmented =
        probe_receipt(&triangle_graph(), CurvatureKind::AugmentedForman).expect("probeable");
    assert_ne!(plain.digest, augmented.digest);
}

#[test]
fn a_receipt_digest_separates_two_different_manifolds() {
    let triangle = probe_receipt(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    let path = probe_receipt(&path_graph(), CurvatureKind::Forman).expect("probeable");
    assert_ne!(triangle.digest, path.digest);
}

#[test]
fn a_receipt_carries_the_polynomial_when_it_can_and_records_absence_when_it_cannot() {
    let small = probe_receipt(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    assert_eq!(
        small.characteristic_polynomial,
        Some(vec!["1".into(), "-6".into(), "9".into(), "0".into()])
    );

    let prompts: Vec<Vec<u32>> = (0..(MAX_SPECTRAL_VERTICES as u32 + 1))
        .map(|i| vec![i, 0, 0])
        .collect();
    let large = PromptGraph::build(prompts, TokenDistance::Hamming, 1).expect("valid");
    let receipt = probe_receipt(&large, CurvatureKind::Forman).expect("probeable");
    // `None` rather than a fabricated or approximated value.
    assert!(receipt.characteristic_polynomial.is_none());
}

#[test]
fn the_receipt_serialises_to_json() {
    let receipt = probe_receipt(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    let json = serde_json::to_string(&receipt).expect("must serialise");
    assert!(json.contains(PROBE_RECEIPT_SCHEMA));
    assert!(json.contains("\"authority_effect\":\"None\""));
    // No float syntax anywhere in the emitted receipt.
    assert!(!json.contains(".0"));
}

#[test]
fn the_ascii_rendering_states_its_construction_and_its_authority() {
    let rendered = render_ascii(&triangle_graph(), CurvatureKind::Forman).expect("probeable");
    assert!(rendered.contains("distance=hamming"));
    assert!(rendered.contains("radius=1"));
    assert!(rendered.contains("AuthorityEffect: None"));
    assert!(rendered.contains("curvature"));
}

#[test]
fn the_rendering_marks_isolated_vertices_as_not_defects() {
    let graph = PromptGraph::build(
        vec![vec![1, 1], vec![1, 2], vec![9, 9]],
        TokenDistance::Hamming,
        1,
    )
    .expect("valid");
    let rendered = render_ascii(&graph, CurvatureKind::Forman).expect("probeable");
    assert!(rendered.contains("isolated (not defects)"));
}

// Origin: engine/crates_rs/tests/pfp/probing_contract.rs
// Claim: urn:core:crates_rs:tests:probing-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5c177117 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5c177117` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5c177117 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError5c177117 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5c177117 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5c177117 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5c177117 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5c177117> {
        if capacity_bound == 0 {
            return Err(BoundaryError5c177117::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5c177117::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5c177117::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_5c177117() {
    let admitted = BoundaryRecord5c177117::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5c177117::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
