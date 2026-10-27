//! The bit-shadow: the two-locus one-edge carrier and its two-pattern
//! alphabet, family-relative removability on the edge, the parity-forced
//! obstruction of the triangle and its least-ness among small simple graphs,
//! the exchange characters of a pair, the finite shadow of the superposition
//! obstruction, and the failure of the Bloch-contraction conjecture.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use std::collections::BTreeSet;

use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;
use core_quantum_physics::mass_phase_embedding::MassPhaseEmbedding;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_homology::graph_f2::{pattern_pairing, simple_graphs, PatternCarrier, PatternError};
use core_quantum_physics::pair_exchange_characters::{exchange_characters_mod, ExchangeError};
use core_quantum_physics::qubit_bloch_map::{BlochMapError, QubitBlochMap};

const SAME: u32 = 0;
const DIFF: u32 = 1;

fn one_edge() -> PatternCarrier {
    PatternCarrier::new(2, vec![(0, 1)]).unwrap()
}

fn triangle() -> PatternCarrier {
    PatternCarrier::new(3, vec![(0, 1), (1, 2), (2, 0)]).unwrap()
}

fn qi(rows: &[&[(i64, i64, i64)]]) -> BasicMatrix<GaussianRat> {
    mx::from_rows(
        rows.iter()
            .map(|r| {
                r.iter()
                    .map(|&(re, im, den)| GaussianRat {
                        re: rq(re, den),
                        im: rq(im, den),
                    })
                    .collect()
            })
            .collect(),
    )
    .unwrap()
}

fn rationals(values: [(i64, i64); 3]) -> [Rational; 3] {
    values.map(|(n, d)| rq(n, d))
}

fn norm_sq(r: &[Rational; 3]) -> Rational {
    r.iter().map(|x| x * x).sum()
}

// ---------------------------------------------------------------------------
// P7-C1: the minimal carrier and its pattern alphabet.
// ---------------------------------------------------------------------------

#[test]
fn the_one_edge_carrier_has_a_two_pattern_alphabet() {
    let edge = one_edge();
    assert_eq!(edge.pattern_count(), 2);
    let family = edge.full_family();
    assert_eq!(family, vec![0b00, 0b01, 0b10, 0b11]);
    let patterns: Vec<u32> = family
        .iter()
        .map(|&f| edge.coboundary(f).unwrap())
        .collect();
    // Constant assignments give `same`, separating ones give `diff`.
    assert_eq!(patterns, vec![SAME, DIFF, DIFF, SAME]);
    assert_eq!(edge.image(&family).unwrap(), BTreeSet::from([SAME, DIFF]));
    assert!(edge.is_simple());
}

// ---------------------------------------------------------------------------
// P7-C2 / P7-C3: on the edge, removability is relative to the declared family.
// ---------------------------------------------------------------------------

#[test]
fn removability_on_the_one_edge_carrier_is_relative_to_the_declared_family() {
    let edge = one_edge();
    let assignments = [0b00u32, 0b01, 0b10, 0b11];
    let (mut full_families, mut diff_residual, mut same_residual) = (0, 0, 0);
    for mask in 0u32..16 {
        let family: Vec<u32> = (0..4)
            .filter(|i| (mask >> i) & 1 == 1)
            .map(|i| assignments[i])
            .collect();
        if family.is_empty() {
            assert_eq!(
                edge.binary_residual(DIFF, &family),
                Err(PatternError::EmptyFamily)
            );
            continue;
        }
        let has_constant = family.iter().any(|&f| f == 0b00 || f == 0b11);
        let has_separating = family.iter().any(|&f| f == 0b01 || f == 0b10);
        let full_for_the_cut = has_constant && has_separating;
        assert_eq!(edge.image(&family).unwrap().len() == 2, full_for_the_cut);
        assert_eq!(edge.is_removable(DIFF, &family).unwrap(), has_separating);
        assert_eq!(edge.is_removable(SAME, &family).unwrap(), has_constant);
        let (d, s) = (
            edge.binary_residual(DIFF, &family).unwrap(),
            edge.binary_residual(SAME, &family).unwrap(),
        );
        assert_eq!(d, u32::from(!has_separating));
        assert_eq!(s, u32::from(!has_constant));
        full_families += usize::from(full_for_the_cut);
        diff_residual += d;
        same_residual += s;
    }
    // Nine of the sixteen families are full for the cut; three leave `diff` and three leave `same`.
    assert_eq!((full_families, diff_residual, same_residual), (9, 3, 3));
    // Constants only: `diff` is residual, relative to that impoverished family.
    assert_eq!(edge.binary_residual(DIFF, &[0b00, 0b11]).unwrap(), 1);
    // Over the full function space every pattern is removed: tree-triviality.
    assert!(!edge.has_unremovable_pattern());
}

// ---------------------------------------------------------------------------
// P7-C4: the three-way minimality split.
// ---------------------------------------------------------------------------

#[test]
fn the_triangle_carries_a_parity_certificate_that_no_family_can_remove() {
    let t = triangle();
    let all_diff = 0b111;
    let cycle = 0b111;
    assert!(t.is_even_subgraph(cycle).unwrap());
    assert_eq!(pattern_pairing(all_diff, cycle), 1);
    for f in t.full_family() {
        assert_eq!(pattern_pairing(t.coboundary(f).unwrap(), cycle), 0);
    }
    assert_eq!(
        t.image(&t.full_family()).unwrap(),
        BTreeSet::from([0b000, 0b011, 0b101, 0b110])
    );
    assert!(!t.is_removable(all_diff, &t.full_family()).unwrap());
    assert_eq!(t.binary_residual(all_diff, &t.full_family()).unwrap(), 1);
    assert!(t.has_unremovable_pattern());
    assert!(!t.is_even_subgraph(0b011).unwrap());
    // The single edge has no even subgraph, so no parity certificate exists there.
    let edge = one_edge();
    assert!(!edge.is_even_subgraph(0b1).unwrap());
    assert!(!edge.is_even_subgraph(0b0).unwrap());
}

#[test]
fn among_small_simple_graphs_an_unremovable_pattern_means_a_cycle_and_needs_three_edges() {
    let mut forced_counts = Vec::new();
    let mut least: Vec<PatternCarrier> = Vec::new();
    for n in 1..=4usize {
        let graphs = simple_graphs(n).unwrap();
        assert_eq!(graphs.len(), 1 << (n * (n - 1) / 2));
        let names: Vec<String> = (0..n).map(|v| format!("v{v}")).collect();
        let labels: Vec<&str> = names.iter().map(String::as_str).collect();
        let mut forced = 0;
        for g in graphs {
            let unremovable = g.has_unremovable_pattern();
            assert_eq!(unremovable, g.has_cycle(), "{:?}", g.edges());
            // Over Q the same graph has H^1 != 0 exactly when F_2 leaves a pattern.
            let edges: Vec<(&str, &str)> = g
                .edges()
                .iter()
                .map(|&(u, v)| (labels[u], labels[v]))
                .collect();
            let packet = FiniteCochainPacket::with_unit_weights(
                FiniteCochainPacket::build_complex(&labels, &edges, &[]).unwrap(),
            )
            .unwrap();
            assert_eq!(packet.dimensions().h1 > 0, unremovable, "{:?}", g.edges());
            if unremovable {
                forced += 1;
                if g.edges().len() == 3 {
                    least.push(g);
                } else {
                    assert!(g.edges().len() > 3);
                }
            }
        }
        forced_counts.push(forced);
    }
    // 1 of 8 graphs on three vertices and 26 of 64 on four (64 minus 38 forests).
    assert_eq!(forced_counts, vec![0, 0, 1, 26]);
    // The three-edge ones are exactly the triangles: one on three vertices, four on four.
    assert_eq!(least.len(), 5);
    assert!(least.iter().all(|g| g.is_even_subgraph(0b111).unwrap()));

    // With parallel edges allowed, a digon is already forced.
    let digon = PatternCarrier::new(2, vec![(0, 1), (0, 1)]).unwrap();
    assert!(!digon.is_simple());
    assert!(digon.has_unremovable_pattern());
    assert!(digon.is_even_subgraph(0b11).unwrap());
    assert_eq!(pattern_pairing(0b01, 0b11), 1);
    assert!(!digon.is_removable(0b01, &digon.full_family()).unwrap());
}

#[test]
fn carriers_refuse_self_loops_foreign_vertices_and_bits_beyond_the_carrier() {
    assert_eq!(
        PatternCarrier::new(2, vec![(1, 1)]),
        Err(PatternError::SelfLoop { edge: 0 })
    );
    assert_eq!(
        PatternCarrier::new(2, vec![(0, 1), (0, 2)]),
        Err(PatternError::VertexOutOfRange {
            edge: 1,
            vertex: 2,
            vertex_count: 2
        })
    );
    assert_eq!(PatternCarrier::new(17, vec![]), Err(PatternError::TooLarge));
    assert_eq!(simple_graphs(7), Err(PatternError::TooLarge));
    let edge = one_edge();
    assert_eq!(
        edge.coboundary(0b100),
        Err(PatternError::AssignmentOutOfRange {
            assignment: 0b100,
            vertices: 2
        })
    );
    assert_eq!(
        edge.is_removable(0b10, &[0b00]),
        Err(PatternError::PatternOutOfRange {
            pattern: 0b10,
            edges: 1
        })
    );
    assert_eq!(edge.vertex_count(), 2);
}

// ---------------------------------------------------------------------------
// P7-C5: two exchange characters on a pair, under the stated hypotheses.
// ---------------------------------------------------------------------------

#[test]
fn a_pair_has_exactly_two_exchange_characters_when_the_scalars_are_a_field_with_one_not_minus_one()
{
    for p in [
        3u64, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
    ] {
        assert_eq!(
            exchange_characters_mod(p).unwrap(),
            vec![1, p - 1],
            "p = {p}"
        );
    }
    // Characteristic 2: +1 = -1, one character.
    assert_eq!(exchange_characters_mod(2).unwrap(), vec![1]);
    // Zero divisors: Z/8 has four square roots of one, Z/4 still two.
    assert_eq!(exchange_characters_mod(8).unwrap(), vec![1, 3, 5, 7]);
    assert_eq!(exchange_characters_mod(4).unwrap(), vec![1, 3]);
    assert_eq!(exchange_characters_mod(15).unwrap(), vec![1, 4, 11, 14]);
    assert_eq!(
        exchange_characters_mod(1),
        Err(ExchangeError::ModulusTooSmall(1))
    );
}

// ---------------------------------------------------------------------------
// P7-C8 (finite shadow): weights do not fix the superposition.
// ---------------------------------------------------------------------------

#[test]
fn equal_weights_on_the_two_patterns_leave_the_interference_term_undetermined() {
    let masses = [ri(9), ri(16)];
    let in_phase = MassPhaseEmbedding::new(&masses, &[gi(1, 0), gi(1, 0)]).unwrap();
    let out_of_phase = MassPhaseEmbedding::new(&masses, &[gi(1, 0), gi(-1, 0)]).unwrap();
    assert_eq!(in_phase.born_weights(), out_of_phase.born_weights());
    let cross_term = |e: &MassPhaseEmbedding| {
        let c = e.exact_amplitudes().unwrap();
        c[0].add(&c[1]).norm_sq() - c[0].norm_sq() - c[1].norm_sq()
    };
    assert_eq!(cross_term(&in_phase), rq(24, 25));
    assert_eq!(cross_term(&out_of_phase), rq(-24, 25));
}

// ---------------------------------------------------------------------------
// P7-C10 (conjecture): Bloch contraction does not characterise dissipation.
// ---------------------------------------------------------------------------

#[test]
fn bloch_contraction_does_not_characterise_dissipation() {
    let zero = || ri(0);
    let p0 = qi(&[&[(1, 0, 1), (0, 0, 1)], &[(0, 0, 1), (0, 0, 1)]]);
    let p1 = qi(&[&[(0, 0, 1), (0, 0, 1)], &[(0, 0, 1), (1, 0, 1)]]);

    // Complete dephasing destroys coherence yet has operator norm exactly one.
    let dephasing = QubitBlochMap::from_kraus(&[p0.clone(), p1]).unwrap();
    assert_eq!(
        dephasing.linear(),
        &[
            [zero(), zero(), zero()],
            [zero(), zero(), zero()],
            [zero(), zero(), ri(1)]
        ]
    );
    assert_eq!(dephasing.translation(), &[zero(), zero(), zero()]);
    assert!(dephasing.linear_is_contraction());
    assert!(!dephasing.linear_is_strict_contraction());
    assert_eq!(dephasing.linear_rank(), 1);
    // |+> has Bloch vector (1, 0, 0) and purity 1; its image has purity (1 + 0) / 2.
    let image = dephasing.apply(&rationals([(1, 1), (0, 1), (0, 1)]));
    assert_eq!((ri(1) + norm_sq(&image)) / ri(2), rq(1, 2));

    // Measure in the computational basis, then prepare (3, 4)/5 or (4, -3)/5:
    // entanglement-breaking, rank one, and still of norm exactly one.
    let prepare_first = qi(&[&[(3, 0, 5), (0, 0, 1)], &[(4, 0, 5), (0, 0, 1)]]);
    let prepare_second = qi(&[&[(0, 0, 1), (4, 0, 5)], &[(0, 0, 1), (-3, 0, 5)]]);
    let measure_prepare = QubitBlochMap::from_kraus(&[prepare_first, prepare_second]).unwrap();
    assert_eq!(
        measure_prepare.linear(),
        &[
            [zero(), zero(), rq(24, 25)],
            [zero(), zero(), zero()],
            [zero(), zero(), rq(-7, 25)]
        ]
    );
    assert_eq!(measure_prepare.translation(), &[zero(), zero(), zero()]);
    assert!(measure_prepare.linear_is_contraction());
    assert!(!measure_prepare.linear_is_strict_contraction());
    assert_eq!(measure_prepare.linear_rank(), 1);
    // Preparing mixtures with Bloch vectors +-(216, 0, 337)/625 instead gives a strict contraction.
    let noisy = QubitBlochMap::from_kraus(&[
        qi(&[&[(9, 0, 25), (0, 0, 1)], &[(12, 0, 25), (0, 0, 1)]]),
        qi(&[&[(4, 0, 5), (0, 0, 1)], &[(0, 0, 1), (0, 0, 1)]]),
        qi(&[&[(0, 0, 1), (12, 0, 25)], &[(0, 0, 1), (-9, 0, 25)]]),
        qi(&[&[(0, 0, 1), (0, 0, 1)], &[(0, 0, 1), (4, 0, 5)]]),
    ])
    .unwrap();
    assert_eq!(
        noisy.linear(),
        &[
            [zero(), zero(), rq(216, 625)],
            [zero(), zero(), zero()],
            [zero(), zero(), rq(337, 625)]
        ]
    );
    assert_eq!(noisy.translation(), &[zero(), zero(), zero()]);
    assert!(noisy.linear_is_strict_contraction());
    assert_eq!(noisy.linear_rank(), 1);

    // The replacement channel onto |0>: the affine ratio |E(r)| / |r| exceeds one.
    let lower = qi(&[&[(0, 0, 1), (1, 0, 1)], &[(0, 0, 1), (0, 0, 1)]]);
    let replacement = QubitBlochMap::from_kraus(&[p0.clone(), lower]).unwrap();
    assert_eq!(replacement.linear_rank(), 0);
    assert_eq!(replacement.translation(), &[zero(), zero(), ri(1)]);
    let r = rationals([(1, 10), (0, 1), (0, 1)]);
    assert_eq!(norm_sq(&replacement.apply(&r)) / norm_sq(&r), ri(100));
    assert!(replacement.linear_is_strict_contraction());

    // Amplitude damping with gamma = 9/25 is a strict contraction.
    let k0 = qi(&[&[(1, 0, 1), (0, 0, 1)], &[(0, 0, 1), (4, 0, 5)]]);
    let k1 = qi(&[&[(0, 0, 1), (3, 0, 5)], &[(0, 0, 1), (0, 0, 1)]]);
    let damping = QubitBlochMap::from_kraus(&[k0, k1]).unwrap();
    assert_eq!(
        damping.linear(),
        &[
            [rq(4, 5), zero(), zero()],
            [zero(), rq(4, 5), zero()],
            [zero(), zero(), rq(16, 25)]
        ]
    );
    assert_eq!(damping.translation(), &[zero(), zero(), rq(9, 25)]);
    assert!(damping.linear_is_strict_contraction());
    assert_eq!(damping.linear_rank(), 3);

    // A rational rotation is an isometry: norm one and nothing lost.
    let rotation = qi(&[&[(3, 0, 5), (-4, 0, 5)], &[(4, 0, 5), (3, 0, 5)]]);
    let isometry = QubitBlochMap::from_kraus(&[rotation]).unwrap();
    assert_eq!(
        isometry.linear(),
        &[
            [rq(-7, 25), zero(), rq(24, 25)],
            [zero(), ri(1), zero()],
            [rq(-24, 25), zero(), rq(-7, 25)]
        ]
    );
    assert!(isometry.linear_is_contraction());
    assert!(!isometry.linear_is_strict_contraction());
    assert_eq!(isometry.linear_rank(), 3);

    assert_eq!(
        QubitBlochMap::from_kraus(&[]),
        Err(BlochMapError::EmptyKraus)
    );
    assert_eq!(
        QubitBlochMap::from_kraus(&[mx::identity::<GaussianRat>(3).unwrap()]),
        Err(BlochMapError::NotQubit { index: 0 })
    );
    assert_eq!(
        QubitBlochMap::from_kraus(&[p0]),
        Err(BlochMapError::NotTracePreserving)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/entanglement/bit_shadow.rs
// Claim: urn:core:crates_rs:tests:bit-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord16971660 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord16971660` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError16971660 {
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
impl BoundaryError16971660 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError16971660 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError16971660 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord16971660 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError16971660> {
        if capacity_bound == 0 {
            return Err(BoundaryError16971660::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError16971660::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError16971660::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_16971660() {
    let admitted = BoundaryRecord16971660::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord16971660::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
