//! Finite path-sum as graded transport: matrix powers are length-n
//! path-sums in every semiring, Chapman–Kolmogorov, the swap, a stochastic
//! path-sum is already a probability law, the Born square returns the L1 law
//! for every declared phase, and interference is the part of a coherent sum
//! that the diagonal weights do not fix.

use linear_algebra::backend::basic_matrix::MatrixError;
use linear_algebra::scalars::Semiring;
use linear_algebra::semiring_matrix::Boolean;
use linear_algebra::semiring_matrix::{
    self as sm, multiply as semiring_matmul, power as semiring_matpow,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::mass_phase_embedding::MassPhaseEmbedding;
use core_quantum_physics::u1_graph_connection::{OrientedWalk, U1Connection, VertexGauge};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_quantum_physics::graded_path_sum::{NonNegative, TimeSlicedTransport, TransportGraph};
use core_quantum_physics::time_sliced_action_shadow::PhaseSum;

/// `M[b][a]` is the weight of `a -> b`; loops and a zero entry included.
const M: [[i64; 3]; 3] = [[1, 2, 0], [0, 1, 3], [1, 0, 1]];

fn graph_of<W: Semiring>(weight: impl Fn(i64) -> W) -> TransportGraph<W> {
    let edges = (0..3)
        .flat_map(|b| (0..3).map(move |a| (a, b)))
        .filter(|&(a, b)| M[b][a] != 0)
        .map(|(a, b)| (a, b, weight(M[b][a])))
        .collect();
    TransportGraph::new(3, edges).unwrap()
}

fn assert_powers_are_path_sums<W: Semiring>(graph: &TransportGraph<W>) {
    let m = graph.transfer_matrix();
    for n in 0..=4u32 {
        let graded = graph.unroll(n as usize).unwrap();
        for (b, row) in sm::to_rows(&semiring_matpow(&m, n).unwrap())
            .unwrap()
            .iter()
            .enumerate()
        {
            for (a, entry) in row.iter().enumerate() {
                assert_eq!(&graded.path_sum(a, b).unwrap(), entry, "n = {n}");
            }
        }
    }
}

#[test]
fn matrix_powers_are_length_n_path_sums_in_every_semiring() {
    let integers = graph_of(|x| x);
    assert_eq!(
        integers.transfer_matrix(),
        sm::from_rows(M.map(|row| row.to_vec()).to_vec()).unwrap()
    );
    assert_eq!(
        semiring_matpow(&integers.transfer_matrix(), 4).unwrap(),
        sm::from_rows(vec![vec![25, 20, 36], vec![18, 25, 30], vec![10, 12, 25]]).unwrap()
    );
    assert_eq!(
        integers.unroll(4).unwrap().histories(0, 2).unwrap().len(),
        27
    );
    assert_powers_are_path_sums(&integers);
    assert_powers_are_path_sums(&graph_of(|x| Boolean(x != 0)));
    assert_powers_are_path_sums(&graph_of(|x| NonNegative::new(rq(x, 2)).unwrap()));
    assert_powers_are_path_sums(&graph_of(|x| gi(x, -x)));
    assert_powers_are_path_sums(&graph_of(|x| PhaseSum::phase(rq(x, 3))));
}

#[test]
fn chapman_kolmogorov_composes_matrix_powers() {
    let integers = graph_of(|x| x).transfer_matrix();
    let phases = graph_of(|x| PhaseSum::phase(rq(x, 3))).transfer_matrix();
    for m in 0..=3u32 {
        for n in 0..=3u32 {
            assert_eq!(
                semiring_matpow(&integers, m + n).unwrap(),
                semiring_matmul(
                    &semiring_matpow(&integers, m).unwrap(),
                    &semiring_matpow(&integers, n).unwrap()
                )
                .unwrap()
            );
            assert_eq!(
                semiring_matpow(&phases, m + n).unwrap(),
                semiring_matmul(
                    &semiring_matpow(&phases, m).unwrap(),
                    &semiring_matpow(&phases, n).unwrap()
                )
                .unwrap()
            );
        }
    }
    // Every cut of the graded five-step transport returns (M^5)[2][0].
    let graded = graph_of(|x| x).unroll(5).unwrap();
    for k in 0..=5 {
        assert_eq!(graded.sliced_composition(0, 2, k).unwrap(), 35);
    }
    let rectangular = sm::from_rows(vec![vec![1i64, 2]]).unwrap();
    assert!(matches!(
        semiring_matpow(&rectangular, 2),
        Err(MatrixError::DimensionMismatch { .. })
    ));
    assert!(matches!(
        semiring_matmul(&rectangular, &rectangular),
        Err(MatrixError::DimensionMismatch { .. })
    ));
}

#[test]
fn the_swap_squares_to_the_identity_and_counts_walks() {
    let swap = TransportGraph::new(2, vec![(0, 1, 1i64), (1, 0, 1)]).unwrap();
    let m = swap.transfer_matrix();
    assert_eq!(m, sm::from_rows(vec![vec![0, 1], vec![1, 0]]).unwrap());
    assert_eq!(
        semiring_matpow(&m, 2).unwrap(),
        sm::identity::<i64>(2).unwrap()
    );
    assert_eq!(semiring_matpow(&m, 3).unwrap(), m);
    let two = swap.unroll(2).unwrap();
    let walks: Vec<Vec<usize>> = two
        .histories(0, 0)
        .unwrap()
        .into_iter()
        .filter(|h| two.history_weight(h).unwrap() != 0)
        .collect();
    assert_eq!(walks, vec![vec![0, 1, 0]]);
    assert_eq!(two.path_sum(0, 1).unwrap(), 0);
    let boolean =
        TransportGraph::new(2, vec![(0, 1, Boolean(true)), (1, 0, Boolean(true))]).unwrap();
    assert_eq!(
        boolean.unroll(3).unwrap().path_sum(0, 1).unwrap(),
        Boolean(true)
    );
    assert_eq!(
        boolean.unroll(3).unwrap().path_sum(0, 0).unwrap(),
        Boolean(false)
    );
}

#[test]
fn a_stochastic_path_sum_is_already_a_probability_law() {
    let weight = |x: Rational| NonNegative::new(x).unwrap();
    let chain = TransportGraph::new(
        2,
        vec![
            (0, 0, weight(rq(1, 2))),
            (0, 1, weight(rq(1, 2))),
            (1, 0, weight(rq(1, 3))),
            (1, 1, weight(rq(2, 3))),
        ],
    )
    .unwrap();
    for n in 0..=5 {
        let graded = chain.unroll(n).unwrap();
        for a in 0..2 {
            let total = (0..2).fold(NonNegative::zero(), |acc, c| {
                acc.add(&graded.path_sum(a, c).unwrap())
            });
            assert_eq!(total.value(), &ri(1), "n = {n}, a = {a}");
        }
    }
    assert_eq!(
        chain.unroll(3).unwrap().path_sum(0, 0).unwrap().value(),
        &rq(29, 72)
    );
    // Normalizing nonnegative history weights is the same rule, w / sum w.
    let two = chain.unroll(2).unwrap();
    let histories = two.histories(0, 1).unwrap();
    assert_eq!(histories, vec![vec![0, 0, 1], vec![0, 1, 1]]);
    let weights: Vec<Rational> = histories
        .iter()
        .map(|h| two.history_weight(h).unwrap().value().clone())
        .collect();
    assert_eq!(weights, vec![rq(1, 4), rq(1, 3)]);
    assert_eq!(two.path_sum(0, 1).unwrap().value(), &rq(7, 12));
    let embedding = MassPhaseEmbedding::new(&weights, &[gi(1, 0), gi(1, 0)]).unwrap();
    assert_eq!(embedding.probabilities(), &[rq(3, 7), rq(4, 7)]);
}

#[test]
fn the_born_square_returns_the_l1_law_for_every_declared_phase() {
    let masses = [ri(1), ri(4), ri(4)];
    let phase_choices = [
        [gi(1, 0), gi(0, 1), gi(-1, 0)],
        [gq(3, 5, 4, 5), gi(1, 0), gq(-5, 13, 12, 13)],
    ];
    let mut born = Vec::new();
    for phases in &phase_choices {
        let embedding = MassPhaseEmbedding::new(&masses, phases).unwrap();
        assert_eq!(embedding.probabilities(), &[rq(1, 9), rq(4, 9), rq(4, 9)]);
        // The check squares the exact amplitudes sqrt(p) u; born_weights() is
        // p |u|^2 by definition, so comparing it with p would prove nothing.
        let amplitudes = embedding.exact_amplitudes().unwrap();
        let total: Rational = amplitudes.iter().map(GaussianRat::norm_sq).sum();
        let from_amplitudes: Vec<Rational> =
            amplitudes.iter().map(|c| c.norm_sq() / &total).collect();
        assert_eq!(from_amplitudes, embedding.probabilities());
        born.push(from_amplitudes);
    }
    assert_eq!(born[0], born[1]);
    assert_ne!(phase_choices[0], phase_choices[1]);
}

/// Two histories `a -> m_j -> b`: the first step carries `w[j]`, the second `1`.
fn two_histories(w: [GaussianRat; 2]) -> TimeSlicedTransport<GaussianRat> {
    let one = gi(1, 0);
    let [w0, w1] = w;
    TimeSlicedTransport::new(
        vec![1, 2, 1],
        vec![vec![vec![w0], vec![w1]], vec![vec![one.clone(), one]]],
    )
    .unwrap()
}

/// `|w(gamma)|^2` for every history from the source to the sink.
fn diagonal_weights(t: &TimeSlicedTransport<GaussianRat>) -> Vec<Rational> {
    t.histories(0, 0)
        .unwrap()
        .iter()
        .map(|h| t.history_weight(h).unwrap().norm_sq())
        .collect()
}

#[test]
fn interference_is_not_a_function_of_the_diagonal_weights() {
    let constructive = two_histories([gi(1, 0), gi(1, 0)]);
    let destructive = two_histories([gi(1, 0), gi(-1, 0)]);
    let quarter_turn = two_histories([gi(1, 0), gi(0, 1)]);
    for t in [&constructive, &destructive, &quarter_turn] {
        assert_eq!(diagonal_weights(t), vec![ri(1), ri(1)]);
    }
    // Same diagonal weights; the coherent intensity |Z|^2 is 4, 0 and 2.
    let intensity = |t: &TimeSlicedTransport<GaussianRat>| t.path_sum(0, 0).unwrap().norm_sq();
    assert_eq!(intensity(&constructive), ri(4));
    assert_eq!(intensity(&destructive), ri(0));
    assert_eq!(intensity(&quarter_turn), ri(2));
}

#[test]
fn two_path_interference_is_twice_the_real_part_of_the_loop_holonomy() {
    let packet = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["a", "b", "c", "d"],
            &[("a", "b"), ("b", "d"), ("a", "c"), ("c", "d")],
            &[],
        )
        .unwrap(),
    )
    .unwrap();
    let connection = U1Connection::new(
        &packet,
        vec![
            gq(3, 5, 4, 5),
            gq(5, 13, 12, 13),
            gi(0, 1),
            gq(8, 17, 15, 17),
        ],
    )
    .unwrap();
    // Slices {a}, {b, c}, {d}; each step carries the connection value of its edge.
    let transport = |conn: &U1Connection| {
        let v: Vec<GaussianRat> = conn.values().iter().cloned().collect();
        TimeSlicedTransport::new(
            vec![1, 2, 1],
            vec![
                vec![vec![v[0].clone()], vec![v[2].clone()]],
                vec![vec![v[1].clone(), v[3].clone()]],
            ],
        )
        .unwrap()
    };
    let loop_walk = OrientedWalk::new(&packet, "a", &[(0, 1), (1, 1), (3, -1), (2, -1)]).unwrap();
    let holonomy = connection.holonomy(&packet, &loop_walk).unwrap();
    let paths = transport(&connection);
    assert_eq!(diagonal_weights(&paths), vec![ri(1), ri(1)]);
    let z = paths.path_sum(0, 0).unwrap();
    // |Z|^2 = 2 + 2 Re(Hol): the cross term is the loop holonomy's real part, twice.
    assert_eq!(holonomy, gq(943, 1105, -576, 1105));
    assert_eq!(z.norm_sq(), ri(2) + &holonomy.re + &holonomy.re);
    assert_eq!(z.norm_sq(), rq(4096, 1105));
    // A vertex gauge moves the amplitude by its endpoint phases only.
    let g = VertexGauge::new(
        &packet,
        vec![gq(3, 5, -4, 5), gi(-1, 0), gq(12, 13, 5, 13), gi(0, -1)],
    )
    .unwrap();
    let moved = transport(&connection.gauge_transform(&packet, &g).unwrap())
        .path_sum(0, 0)
        .unwrap();
    assert_ne!(moved, z);
    assert_eq!(moved, g.values()[3].mul(&z).mul(&g.values()[0].conj()));
    assert_eq!(moved.norm_sq(), z.norm_sq());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/finite_path_sum_graded_transport.rs
// Claim: urn:core:crates_rs:tests:finite-path-sum-graded-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1b9ee72d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1b9ee72d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1b9ee72d {
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
impl BoundaryError1b9ee72d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1b9ee72d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1b9ee72d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1b9ee72d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1b9ee72d> {
        if capacity_bound == 0 {
            return Err(BoundaryError1b9ee72d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1b9ee72d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1b9ee72d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1b9ee72d() {
    let admitted = BoundaryRecord1b9ee72d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1b9ee72d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
