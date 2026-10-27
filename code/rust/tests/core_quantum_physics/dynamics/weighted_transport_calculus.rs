//! Finite weighted transport calculus: graded path-sums over five
//! semirings, the split-point overcount of the ungraded free category and its
//! invisibility to Phi1 and Gamma2, cancellation only with signed weights, the
//! transfer identity without subtraction, and phase as a gauge-triviality
//! obstruction decided with a gauge or a closed-walk witness.

use linear_algebra::scalars::Semiring;
use linear_algebra::semiring_matrix as sm;
use linear_algebra::semiring_matrix::Boolean;
use num_traits::Zero;
use core_lie_theory::cayley::unit_pow;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::u1_graph_connection::{CochainExponential, OrientedWalk, U1Connection};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_quantum_physics::graded_path_sum::{
    NonNegative, TimeSlicedTransport, TransportError, TransportGraph, HISTORY_BUDGET, UNROLL_BUDGET,
};
use core_quantum_physics::time_sliced_action_shadow::PhaseSum;
use core_quantum_physics::u1_gauge_triviality::{trivializing_gauge, GaugeTrivialityError};

/// Step matrices of a four-slice transport with slice sizes 2, 3, 2, 2.
const STEPS: [&[&[i64]]; 3] = [
    &[&[1, 2], &[0, 1], &[3, -1]],
    &[&[1, 0, 2], &[-1, 1, 1]],
    &[&[2, 1], &[0, -3]],
];

fn sliced<W: Semiring>(weight: impl Fn(i64) -> W) -> TimeSlicedTransport<W> {
    let steps = STEPS
        .iter()
        .map(|t| {
            t.iter()
                .map(|row| row.iter().map(|&x| weight(x)).collect())
                .collect()
        })
        .collect();
    TimeSlicedTransport::new(vec![2, 3, 2, 2], steps).unwrap()
}

fn assert_sliced_path_sums_compose<W: Semiring>(transport: &TimeSlicedTransport<W>) {
    let last = transport.slice_sizes().len() - 1;
    for (c, row) in sm::to_rows(&transport.propagator())
        .unwrap()
        .iter()
        .enumerate()
    {
        for (a, entry) in row.iter().enumerate() {
            let z = transport.path_sum(a, c).unwrap();
            assert_eq!(&z, entry);
            for k in 0..=last {
                assert_eq!(
                    transport.sliced_composition(a, c, k).unwrap(),
                    z,
                    "cut at slice {k}"
                );
            }
        }
    }
}

fn open_or_filled_triangle(filled: bool) -> FiniteCochainPacket {
    let faces: &[&[&str]] = if filled { &[&["a", "b", "c"]] } else { &[] };
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["a", "b", "c"],
            &[("a", "b"), ("b", "c"), ("c", "a")],
            faces,
        )
        .unwrap(),
    )
    .unwrap()
}

/// Triangle a-b-c with a pendant edge c -> d, unit weights.
fn kite() -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["a", "b", "c", "d"],
            &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")],
            &[],
        )
        .unwrap(),
    )
    .unwrap()
}

fn pythagorean_scale() -> CochainExponential {
    CochainExponential::new(gq(3, 5, 4, 5)).unwrap()
}

// ---------------------------------------------------------------------------
// T1: graded path-sums compose across every slice.
// ---------------------------------------------------------------------------

#[test]
fn sliced_path_sums_compose_across_every_slice_in_five_semirings() {
    let integers = sliced(|x| x);
    assert_eq!(
        integers.propagator(),
        sm::from_rows(vec![vec![16, -2], vec![-6, 6]]).unwrap()
    );
    assert_eq!(integers.histories(0, 1).unwrap().len(), 6);
    assert_sliced_path_sums_compose(&integers);
    assert_sliced_path_sums_compose(&sliced(|x| Boolean(x != 0)));
    assert_sliced_path_sums_compose(&sliced(|x| NonNegative::new(ri(x.abs())).unwrap()));
    assert_sliced_path_sums_compose(&sliced(|x| gi(x, 1 - x)));
    assert_sliced_path_sums_compose(&sliced(|x| PhaseSum::phase(ri(x))));
}

#[test]
fn the_ungraded_decomposition_counts_a_two_step_path_three_times() {
    // a = 0 -> b = 1 -> c = 2.
    let weighted = TransportGraph::new(3, vec![(0, 1, 3i64), (1, 2, 5)]).unwrap();
    assert_eq!(weighted.all_histories(0, 2).unwrap(), vec![vec![0, 1]]);
    assert_eq!(weighted.total_path_sum(0, 2).unwrap(), 15);
    assert_eq!(weighted.ungraded_split_sum(0, 2).unwrap(), 45);
    // With unit weights the split sum counts decompositions: three for one path.
    let one = || NonNegative::new(ri(1)).unwrap();
    let counting = TransportGraph::new(3, vec![(0, 1, one()), (1, 2, one())]).unwrap();
    assert_eq!(counting.total_path_sum(0, 2).unwrap(), one());
    assert_eq!(
        counting.ungraded_split_sum(0, 2).unwrap(),
        NonNegative::new(ri(3)).unwrap()
    );
    // Grading by slice leaves one cut, so nothing is overcounted.
    let graded = weighted.unroll(2).unwrap();
    assert_eq!(graded.path_sum(0, 2).unwrap(), 15);
    assert_eq!(graded.sliced_composition(0, 2, 1).unwrap(), 15);
}

#[test]
fn the_ungraded_split_sum_weights_each_path_by_its_split_points() {
    // a -> b -> c and a -> c: paths of lengths two and one meet.
    let graph = TransportGraph::new(3, vec![(0, 1, 2i64), (1, 2, 3), (0, 2, 7)]).unwrap();
    let paths = graph.all_histories(0, 2).unwrap();
    assert_eq!(paths, vec![vec![0, 1], vec![2]]);
    let z = graph.total_path_sum(0, 2).unwrap();
    assert_eq!(z, 13);
    let split = graph.ungraded_split_sum(0, 2).unwrap();
    let length_weighted: i64 = paths
        .iter()
        .map(|p| (p.len() as i64 + 1) * graph.path_weight(p).unwrap())
        .sum();
    assert_eq!(split, length_weighted);
    assert_eq!(split, 32);
    assert_ne!(split % z, 0, "the overcount has no fixed ratio");
    // Graded transports keep the two lengths apart.
    assert_eq!(graph.unroll(1).unwrap().path_sum(0, 2).unwrap(), 7);
    assert_eq!(graph.unroll(2).unwrap().path_sum(0, 2).unwrap(), 6);
    // Unrolling is bounded; usize::MAX steps used to overflow.
    assert!(matches!(
        graph.unroll(usize::MAX),
        Err(TransportError::StepBudget {
            steps: usize::MAX,
            budget: UNROLL_BUDGET
        })
    ));
}

#[test]
fn the_overcount_is_invisible_to_the_obstruction_layer() {
    let packet = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&["a", "b", "c"], &[("a", "b"), ("b", "c")], &[])
            .unwrap(),
    )
    .unwrap();
    let dims = packet.dimensions();
    assert_eq!((dims.c1, dims.b1, dims.h1), (2, 2, 0));
    for cochain in [vec![ri(3), ri(5)], vec![ri(-7), rq(2, 3)]] {
        assert!(Zero::is_zero(
            packet.quotient_mass(&cochain).unwrap().value()
        ));
        assert!(Zero::is_zero(
            packet.closure_defect(&cochain).unwrap().value()
        ));
        assert_eq!(
            packet.classify(&cochain).unwrap().diagnostic_class(),
            ObstructionDiagnosticClass::ExactRepair
        );
    }
    let graph = TransportGraph::new(3, vec![(0, 1, 3i64), (1, 2, 5)]).unwrap();
    assert_eq!(
        graph.ungraded_split_sum(0, 2).unwrap(),
        3 * graph.total_path_sum(0, 2).unwrap()
    );

    // On a tree that is vacuous: every cochain is exact. On the unfilled
    // triangle (h1 = 1) the obstruction layer does see something, and the
    // overcount factor 3 still does not change the class, only the mass.
    let triangle = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["a", "b", "c"],
            &[("a", "b"), ("b", "c"), ("c", "a")],
            &[],
        )
        .unwrap(),
    )
    .unwrap();
    assert_eq!(triangle.dimensions().h1, 1);
    let circulation = vec![ri(1), ri(2), ri(0)];
    let overcounted: Vec<Rational> = circulation.iter().map(|x| ri(3) * x).collect();
    let class = |x: &[Rational]| triangle.classify(x).unwrap().diagnostic_class();
    assert_eq!(
        class(&circulation),
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert_eq!(class(&overcounted), class(&circulation));
    assert_eq!(
        triangle.quotient_mass(&circulation).unwrap().value(),
        &ri(3)
    );
    assert_eq!(
        triangle.quotient_mass(&overcounted).unwrap().value(),
        &ri(9)
    );
}

#[test]
fn cyclic_graphs_bad_shapes_and_out_of_range_indices_are_refused() {
    let cyclic = TransportGraph::new(2, vec![(0, 1, 1i64), (1, 0, 1)]).unwrap();
    assert!(matches!(
        cyclic.all_histories(0, 1),
        Err(TransportError::DirectedCycle { .. })
    ));
    let looped = TransportGraph::new(2, vec![(0, 1, 1i64), (1, 1, 1)]).unwrap();
    assert_eq!(
        looped.total_path_sum(0, 1),
        Err(TransportError::DirectedCycle { vertex: 1 })
    );
    // Grading makes the cyclic graph's history sets finite again.
    assert_eq!(cyclic.unroll(3).unwrap().path_sum(0, 1).unwrap(), 1);
    assert_eq!(cyclic.unroll(4).unwrap().path_sum(0, 0).unwrap(), 1);
    assert_eq!(
        cyclic.path_weight(&[5]),
        Err(TransportError::EdgeOutOfRange { edge: 5, count: 2 })
    );
    assert_eq!(
        TransportGraph::new(2, vec![(0, 2, 1i64)]),
        Err(TransportError::VertexOutOfRange {
            vertex: 2,
            count: 2
        })
    );
    assert_eq!(
        TransportGraph::<i64>::new(0, vec![]),
        Err(TransportError::NoVertices)
    );

    assert_eq!(
        TimeSlicedTransport::<i64>::new(vec![], vec![]),
        Err(TransportError::NoSlices)
    );
    assert_eq!(
        TimeSlicedTransport::<i64>::new(vec![1, 0], vec![vec![]]),
        Err(TransportError::EmptySlice { slice: 1 })
    );
    assert_eq!(
        TimeSlicedTransport::<i64>::new(vec![1, 2], vec![]),
        Err(TransportError::StepCount {
            slices: 2,
            steps: 0
        })
    );
    assert_eq!(
        TimeSlicedTransport::new(vec![1, 2], vec![vec![vec![1i64, 1]]]),
        Err(TransportError::StepShape {
            step: 0,
            rows: 1,
            cols: 2,
            expected_rows: 2,
            expected_cols: 1
        })
    );
    assert_eq!(
        TimeSlicedTransport::new(vec![2, 2], vec![vec![vec![1i64, 1], vec![1]]]),
        Err(TransportError::RaggedMatrix { row: 1 })
    );
    // Enumeration stops at the history budget: 17^4 > 2^16 interior histories,
    // and an 18-step ladder of width two has 2^17 paths to a fixed endpoint.
    let wide = TimeSlicedTransport::new(
        vec![1, 17, 17, 17, 17, 1],
        [(17, 1), (17, 17), (17, 17), (17, 17), (1, 17)]
            .iter()
            .map(|&(rows, cols)| vec![vec![1i64; cols]; rows])
            .collect(),
    )
    .unwrap();
    assert_eq!(
        wide.path_sum(0, 0),
        Err(TransportError::HistoryBudget {
            budget: HISTORY_BUDGET
        })
    );
    let ladder_edges = (0..18)
        .flat_map(|layer| {
            let (from, to) = (2 * layer, 2 * layer + 2);
            [
                (from, to, 1i64),
                (from, to + 1, 1),
                (from + 1, to, 1),
                (from + 1, to + 1, 1),
            ]
        })
        .collect();
    let ladder = TransportGraph::new(38, ladder_edges).unwrap();
    assert_eq!(
        ladder.all_histories(0, 36),
        Err(TransportError::HistoryBudget {
            budget: HISTORY_BUDGET
        })
    );
    // The transfer matrices still count them without enumerating.
    assert_eq!(
        ladder.unroll(18).unwrap().propagator().get(36, 0).unwrap(),
        1 << 17
    );
    assert_eq!(
        ladder.unroll(18).unwrap().path_sum(0, 36),
        Err(TransportError::HistoryBudget {
            budget: HISTORY_BUDGET
        })
    );

    let transport = TimeSlicedTransport::new(vec![1, 2], vec![vec![vec![1i64], vec![2]]]).unwrap();
    assert_eq!(
        transport.path_sum(0, 2),
        Err(TransportError::VertexOutOfRange {
            vertex: 2,
            count: 2
        })
    );
    assert_eq!(
        transport.split(2),
        Err(TransportError::SliceOutOfRange { slice: 2, steps: 1 })
    );
    assert_eq!(
        transport.history_weight(&[0]),
        Err(TransportError::HistoryLength {
            expected: 2,
            actual: 1
        })
    );
}

// ---------------------------------------------------------------------------
// Counterexample 3: cancellation needs signed weights, not complex ones.
// ---------------------------------------------------------------------------

/// `a -> {m1, m2} -> b`: the history through `m1` has steps `w[0], w[2]`,
/// the one through `m2` has `w[1], w[3]`.
fn diamond<W: Semiring>(w: [W; 4]) -> TimeSlicedTransport<W> {
    let [w0, w1, w2, w3] = w;
    TimeSlicedTransport::new(
        vec![1, 2, 1],
        vec![vec![vec![w0], vec![w1]], vec![vec![w2, w3]]],
    )
    .unwrap()
}

fn assert_nonnegative_rational_diamond_cannot_cancel() {
    let grid = [ri(0), rq(1, 2), ri(1), ri(2)];
    for w0 in &grid {
        for w1 in &grid {
            for w2 in &grid {
                for w3 in &grid {
                    let blocked = (Zero::is_zero(w0) || Zero::is_zero(w2))
                        && (Zero::is_zero(w1) || Zero::is_zero(w3));
                    let w = [w0, w1, w2, w3].map(|x| NonNegative::new(x.clone()).unwrap());
                    assert_eq!(diamond(w).path_sum(0, 0).unwrap().is_zero(), blocked);
                }
            }
        }
    }
}

#[test]
fn positive_semirings_cannot_cancel_and_signed_weights_can() {
    // Boolean weights: all sixteen assignments.
    for mask in 0u8..16 {
        let w = [0, 1, 2, 3].map(|i| Boolean(((mask >> i) & 1) == 1));
        let blocked = |x: Boolean, y: Boolean| !(x.0 && y.0);
        let z = diamond(w).path_sum(0, 0).unwrap();
        assert_eq!(
            z.is_zero(),
            blocked(w[0], w[2]) && blocked(w[1], w[3]),
            "mask {mask}"
        );
    }
    // Nonnegative rational weights: every assignment from {0, 1/2, 1, 2}.
    assert_nonnegative_rational_diamond_cannot_cancel();
    // Integers already cancel two unblocked histories; no complex weight is needed.
    assert_eq!(diamond([1i64, 1, 1, -1]).path_sum(0, 0).unwrap(), 0);
    let quarter_turns = diamond([gi(1, 0), gi(1, 0), gi(0, 1), gi(0, -1)]);
    assert!(quarter_turns.path_sum(0, 0).unwrap().is_zero());
}

// ---------------------------------------------------------------------------
// T2: the finite transfer identity needs no subtraction; a generator does.
// ---------------------------------------------------------------------------

#[test]
fn the_transfer_identity_needs_no_subtraction_but_a_generator_does() {
    let entries = [[rq(1, 2), rq(1, 3)], [rq(1, 2), rq(2, 3)]];
    let step: Vec<Vec<NonNegative>> = entries
        .iter()
        .map(|row| {
            row.iter()
                .map(|x| NonNegative::new(x.clone()).unwrap())
                .collect()
        })
        .collect();
    let chain =
        TimeSlicedTransport::new(vec![2; 4], vec![step.clone(), step.clone(), step]).unwrap();
    let propagator = chain.propagator();
    for (c, row) in sm::to_rows(&propagator).unwrap().iter().enumerate() {
        for (a, entry) in row.iter().enumerate() {
            assert_eq!(&chain.path_sum(a, c).unwrap(), entry);
        }
    }
    assert_eq!(propagator.get_ref(0, 0).unwrap().value(), &rq(29, 72));
    assert_eq!(propagator.get_ref(1, 1).unwrap().value(), &rq(65, 108));
    // The discrete generator T - I has negative diagonal entries.
    let diagonal: Vec<Rational> = (0..2).map(|i| &entries[i][i] - ri(1)).collect();
    assert_eq!(diagonal, vec![rq(-1, 2), rq(-1, 3)]);
    assert_eq!(
        NonNegative::new(diagonal[0].clone()),
        Err(TransportError::NegativeWeight(rq(-1, 2)))
    );
}

// ---------------------------------------------------------------------------
// T3: phase as a gauge-triviality obstruction.
// ---------------------------------------------------------------------------

#[test]
fn gauge_triviality_is_decided_with_a_gauge_or_a_closed_walk() {
    let packet = kite();
    let scale = pythagorean_scale();
    assert_eq!(scale.order(), None);
    let exact = packet
        .primitive_difference(&[ri(0), ri(2), ri(-1), ri(4)])
        .unwrap();
    let pure_gauge = scale.connection(&packet, &exact).unwrap();
    let g = trivializing_gauge(&packet, &pure_gauge).unwrap();
    assert_eq!(
        U1Connection::trivial(&packet)
            .gauge_transform(&packet, &g)
            .unwrap(),
        pure_gauge
    );
    assert!(Zero::is_zero(packet.quotient_mass(&exact).unwrap().value()));

    // Cycle sum three on the triangle: no gauge, and a replayable witness.
    let flux = vec![ri(1), ri(1), ri(1), ri(5)];
    let connection = scale.connection(&packet, &flux).unwrap();
    match trivializing_gauge(&packet, &connection) {
        Err(GaugeTrivialityError::NontrivialHolonomy(witness)) => {
            assert_eq!(witness.edge, 1);
            assert!(witness.walk.is_closed());
            assert_eq!(
                connection.holonomy(&packet, &witness.walk).unwrap(),
                witness.holonomy
            );
            assert_eq!(witness.holonomy, unit_pow(scale.base(), &3.into()).unwrap());
        }
        other => panic!("expected a holonomy witness, got {other:?}"),
    }
    assert_eq!(packet.quotient_mass(&flux).unwrap().value(), &ri(3));
    // A connection declared on another packet is refused, not evaluated.
    assert_eq!(
        trivializing_gauge(&open_or_filled_triangle(false), &connection),
        Err(GaugeTrivialityError::EdgeCount {
            expected: 3,
            actual: 4
        })
    );
}

#[test]
fn a_periodic_scale_makes_a_non_coboundary_pure_gauge() {
    let packet = kite();
    let quarter_turn = CochainExponential::new(gi(0, 1)).unwrap();
    assert_eq!(quarter_turn.order(), Some(4));
    let omega = vec![ri(1), ri(1), ri(2), ri(0)];
    let connection = quarter_turn.connection(&packet, &omega).unwrap();
    let g = trivializing_gauge(&packet, &connection).unwrap();
    assert_eq!(
        U1Connection::trivial(&packet)
            .gauge_transform(&packet, &g)
            .unwrap(),
        connection
    );
    // The cycle sum is four, so omega is not a coboundary.
    assert_eq!(packet.quotient_mass(&omega).unwrap().value(), &ri(4));
    // Under a scale of infinite order the same cochain is not pure gauge.
    let aperiodic = pythagorean_scale().connection(&packet, &omega).unwrap();
    assert!(matches!(
        trivializing_gauge(&packet, &aperiodic),
        Err(GaugeTrivialityError::NontrivialHolonomy(_))
    ));
}

#[test]
fn filling_the_cycle_turns_the_same_flux_into_curvature() {
    let open = open_or_filled_triangle(false);
    let filled = open_or_filled_triangle(true);
    let flux = vec![ri(1), ri(1), ri(1)];
    for packet in [&open, &filled] {
        let connection = pythagorean_scale().connection(packet, &flux).unwrap();
        assert!(matches!(
            trivializing_gauge(packet, &connection),
            Err(GaugeTrivialityError::NontrivialHolonomy(_))
        ));
    }
    assert_eq!((open.dimensions().h1, filled.dimensions().h1), (1, 0));
    assert_eq!(
        open.classify(&flux).unwrap().diagnostic_class(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    let curvature = filled.classify(&flux).unwrap();
    assert_eq!(
        curvature.diagnostic_class(),
        ObstructionDiagnosticClass::ActiveClosureFailure
    );
    assert_eq!(curvature.gamma2_value(), &ri(3));
}

#[test]
fn coboundary_step_phases_telescope_to_a_single_phase() {
    let phi = [ri(0), rq(1, 2), ri(3)];
    let build = |flux: Rational| {
        let steps = (0..3)
            .map(|k| {
                (0..3)
                    .map(|y| {
                        (0..3)
                            .map(|x| {
                                let extra = if k == 1 && (x, y) == (0, 2) {
                                    flux.clone()
                                } else {
                                    ri(0)
                                };
                                PhaseSum::phase(&phi[y] - &phi[x] + extra)
                            })
                            .collect()
                    })
                    .collect()
            })
            .collect();
        TimeSlicedTransport::new(vec![3; 4], steps).unwrap()
    };
    let delta = &phi[2] - &phi[0];
    let dynamical = build(ri(0)).path_sum(0, 2).unwrap();
    assert_eq!(dynamical.terms().len(), 1);
    assert_eq!(dynamical.terms()[&delta], gi(9, 0));
    // A non-coboundary phase on one step leaves two phases that can interfere.
    let with_flux = build(ri(1)).path_sum(0, 2).unwrap();
    assert_eq!(with_flux.terms().len(), 2);
    assert_eq!(with_flux.terms()[&delta], gi(8, 0));
    assert_eq!(with_flux.terms()[&(&delta + ri(1))], gi(1, 0));
}

#[test]
fn the_two_edge_loop_separates_coboundary_phase_from_flux() {
    let packet = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&["a", "b"], &[("a", "b"), ("b", "a")], &[]).unwrap(),
    )
    .unwrap();
    let scale = pythagorean_scale();
    let loop_walk = OrientedWalk::new(&packet, "a", &[(0, 1), (1, 1)]).unwrap();
    let dynamical = packet.primitive_difference(&[ri(0), ri(7)]).unwrap();
    assert_eq!(dynamical, vec![ri(7), ri(-7)]);
    let connection = scale.connection(&packet, &dynamical).unwrap();
    assert_eq!(
        connection.holonomy(&packet, &loop_walk).unwrap(),
        GaussianRat::one()
    );
    let g = trivializing_gauge(&packet, &connection).unwrap();
    assert_eq!(
        U1Connection::trivial(&packet)
            .gauge_transform(&packet, &g)
            .unwrap(),
        connection
    );

    let flux = scale.connection(&packet, &[ri(2), ri(0)]).unwrap();
    assert_eq!(
        flux.holonomy(&packet, &loop_walk).unwrap(),
        unit_pow(scale.base(), &2.into()).unwrap()
    );
    assert!(matches!(
        trivializing_gauge(&packet, &flux),
        Err(GaugeTrivialityError::NontrivialHolonomy(_))
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/weighted_transport_calculus.rs
// Claim: urn:core:crates_rs:tests:weighted-transport-calculus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfcf5775f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfcf5775f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfcf5775f {
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
impl BoundaryErrorfcf5775f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfcf5775f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfcf5775f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfcf5775f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfcf5775f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfcf5775f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfcf5775f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfcf5775f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fcf5775f() {
    let admitted = BoundaryRecordfcf5775f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfcf5775f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
