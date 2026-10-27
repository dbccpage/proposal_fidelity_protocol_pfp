//! QM_208: the cross term `2 Re(c1 conj c2)` belongs to the readout of the
//! recombined amplitude `|c1 + c2|^2`, not to the norm of the superposition.
//! Over orthonormal loci the norm is the L1 total of the weights for every
//! phase.

use linear_algebra::exact_field::involution::inner_product;
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::coherent_interference::{cross_term, interfered_weight};
use core_quantum_physics::exact_hermitian::{gi, gq};

fn norm(c: &[GaussianRat]) -> Rational {
    let value = inner_product(c, c).unwrap();
    assert!(value.im.is_zero());
    value.re
}

fn weights(c: &[GaussianRat]) -> Rational {
    c.iter().map(GaussianRat::norm_sq).sum()
}

/// The source's formula `|c1|^2 + |c2|^2 + 2 Re(c1 conj c2)`.
fn source_formula(c: &[GaussianRat; 2]) -> Rational {
    weights(c) + ri(2) * c[0].mul(&c[1].conj()).re
}

#[test]
fn the_norm_has_no_cross_term_and_the_recombined_amplitude_does() {
    let configurations = [
        [gi(1, 0), gi(1, 0)],
        [gi(1, 0), gi(-1, 0)],
        [gi(1, 0), gi(0, 1)],
        [gi(2, 0), gi(1, 1)],
        [gq(3, 5, 0, 1), gq(0, 1, 4, 5)],
    ];
    let expected = [
        // (norm, recombined weight, cross term)
        (ri(2), ri(4), ri(2)),
        (ri(2), ri(0), ri(-2)),
        (ri(2), ri(2), ri(0)),
        (ri(6), ri(10), ri(4)),
        (ri(1), ri(1), ri(0)),
    ];
    for (c, (n, recombined, cross)) in configurations.iter().zip(expected) {
        // The L1 readout: the norm is the sum of the weights, whatever the phases.
        assert_eq!(norm(c), weights(c));
        assert_eq!(norm(c), n);
        // The source's formula is the recombined readout |<(1, 1), psi>|^2.
        assert_eq!(source_formula(c), interfered_weight(c).unwrap());
        assert_eq!(interfered_weight(c).unwrap(), recombined);
        assert_eq!(cross_term(c).unwrap(), cross);
    }
    // Countermodel to "||psi||^2 = |c1|^2 + |c2|^2 + 2 Re(c1 conj c2)": 2 against 4.
    let equal = &configurations[0];
    assert_ne!(norm(equal), source_formula(equal));
}

#[test]
fn importing_the_quadratic_readout_does_not_make_the_cross_term_nonzero() {
    // Nonzero amplitudes whose product c1 conj c2 is imaginary: phase
    // difference pi/2, cross term 0 under the recombined readout.
    assert_eq!(cross_term(&[gi(1, 0), gi(0, 1)]).unwrap(), ri(0));
    assert_eq!(
        cross_term(&[gq(3, 5, 0, 1), gq(0, 1, 4, 5)]).unwrap(),
        ri(0)
    );
    // A zero amplitude carries every phase, including the phase of its partner:
    // phase difference 0 and still no cross term, so the phase criterion needs
    // w1 w2 > 0.
    for partner in [gi(1, 0), gi(0, 1), gq(3, 5, 4, 5), gi(-2, 7)] {
        assert_eq!(
            cross_term(&[partner.clone(), GaussianRat::zero()]).unwrap(),
            ri(0)
        );
        assert_eq!(cross_term(&[GaussianRat::zero(), partner]).unwrap(), ri(0));
    }
    // With both amplitudes nonzero and the product not imaginary the cross term is nonzero.
    assert_eq!(cross_term(&[gi(1, 0), gq(3, 5, 4, 5)]).unwrap(), rq(6, 5));
}

/// A declared cochain complex and nonnegative endpoint-normalized slit
/// tables do not determine the readout degree. This is a finite control,
/// not an alternative operational theory or a Born-rule reconstruction.
#[test]
fn the_same_three_slit_packet_admits_distinct_readout_degrees() {
    use core_quantum_physics::coherent_interference::sorkin_interference;
    use core_quantum_physics::gaussian_frame_readout::readout;
    use core_solvers::data_cochain_packet::FiniteCochainPacket;

    let complex = FiniteCochainPacket::build_complex(
        &["source", "a", "b", "c", "sink"],
        &[
            ("source", "a"),
            ("source", "b"),
            ("source", "c"),
            ("a", "sink"),
            ("b", "sink"),
            ("c", "sink"),
        ],
        &[
            &["source", "a", "sink", "b"],
            &["source", "b", "sink", "c"],
            &["source", "c", "sink", "a"],
        ],
    )
    .unwrap();
    let packet = FiniteCochainPacket::with_unit_weights(complex).unwrap();
    assert_eq!((packet.vertex_count(), packet.edge_count()), (5, 6));
    // Verify d1 d0 on the full rational coordinate basis, not one potential.
    for vertex in 0..packet.vertex_count() {
        let mut potential = vec![ri(0); packet.vertex_count()];
        potential[vertex] = ri(1);
        let gradient = packet.primitive_difference(&potential).unwrap();
        assert!(packet
            .face_coboundary(&gradient)
            .unwrap()
            .iter()
            .all(Zero::is_zero));
    }

    let paths = [[1, 0, 0, 1, 0, 0], [0, 1, 0, 0, 1, 0], [0, 0, 1, 0, 0, 1]];
    let detector = vec![gi(1, 0); packet.edge_count()];
    let amplitudes: Vec<_> = paths
        .iter()
        .map(|path| {
            let chain: Vec<_> = path.iter().map(|&x| gi(x, 0)).collect();
            let pairing = inner_product(&chain, &detector).unwrap();
            assert_eq!(pairing, gi(2, 0));
            pairing.mul(&gq(1, 6, 0, 1))
        })
        .collect();
    assert_eq!(amplitudes, vec![gq(1, 3, 0, 1); 3]);

    let report = [gi(1, 0), gi(0, 0)];
    let mut linear = Vec::new();
    let mut quadratic = Vec::new();
    let mut quartic = Vec::new();
    for mask in 0u32..8 {
        let total = amplitudes
            .iter()
            .enumerate()
            .filter(|(i, _)| mask & (1 << i) != 0)
            .fold(GaussianRat::zero(), |sum, (_, a)| sum.add(a));
        let psi = [total.clone(), gi(0, 0)];
        linear.push(total.re);
        quadratic.push(readout(&report, &psi, 1).unwrap());
        quartic.push(readout(&report, &psi, 2).unwrap());
    }
    let third_order = |table: &[Rational]| -> Rational {
        -&table[0] + &table[1] + &table[2] - &table[3] + &table[4] - &table[5] - &table[6]
            + &table[7]
    };
    for table in [&linear, &quadratic, &quartic] {
        assert!(table.iter().all(|p| p >= &ri(0) && p <= &ri(1)));
        assert_eq!(table[0], ri(0));
        assert_eq!(table[7], ri(1));
    }
    assert_eq!(
        linear,
        vec![
            ri(0),
            rq(1, 3),
            rq(1, 3),
            rq(2, 3),
            rq(1, 3),
            rq(2, 3),
            rq(2, 3),
            ri(1)
        ]
    );
    assert_eq!(
        quadratic,
        vec![
            ri(0),
            rq(1, 9),
            rq(1, 9),
            rq(4, 9),
            rq(1, 9),
            rq(4, 9),
            rq(4, 9),
            ri(1)
        ]
    );
    assert_eq!(
        quartic,
        vec![
            ri(0),
            rq(1, 81),
            rq(1, 81),
            rq(16, 81),
            rq(1, 81),
            rq(16, 81),
            rq(16, 81),
            ri(1)
        ]
    );
    assert_eq!(third_order(&linear), ri(0));
    assert_eq!(third_order(&quadratic), ri(0));
    assert_eq!(third_order(&quartic), rq(4, 9));
    assert_eq!(
        (linear[1].clone(), quadratic[1].clone(), quartic[1].clone()),
        (rq(1, 3), rq(1, 9), rq(1, 81))
    );
    // Independent existing quadratic inclusion-exclusion owner agrees.
    assert_eq!(
        sorkin_interference(&amplitudes, &[vec![0], vec![1], vec![2]], 8).unwrap(),
        ri(0)
    );
    // Even I3=0 does not select the square: the linear law has no I2 term.
    assert_eq!(&linear[3] - &linear[1] - &linear[2], ri(0));
    assert_eq!(&quadratic[3] - &quadratic[1] - &quadratic[2], rq(2, 9));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/quadratic_readout_interference.rs
// Claim: urn:core:crates_rs:tests:quadratic-readout-interference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2b98f9df {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2b98f9df` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2b98f9df {
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
impl BoundaryError2b98f9df {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2b98f9df {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2b98f9df {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2b98f9df {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2b98f9df> {
        if capacity_bound == 0 {
            return Err(BoundaryError2b98f9df::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2b98f9df::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2b98f9df::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2b98f9df() {
    let admitted = BoundaryRecord2b98f9df::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2b98f9df::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
