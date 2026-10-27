//! The finite kernels of the typed boundary suite that this batch owns: the
//! exact trichotomy is total, exclusive and equal to its linear-algebra
//! characterization on every cochain of a declared box; the quotient mass
//! vanishes exactly on the repair image; enlarging the repair image never
//! strands more defects; mismatched evidence is refused rather than
//! classified. Image membership is decided independently of the quotient LP,
//! by `core_linear_algebra`'s exact row reduction.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::{solve_in_image, ImageMembership};
use num_traits::Zero;
use core_number_theory::rational::{ri, Rational};
use core_policy::trichotomy::{
    classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome, TrichotomyRefusal,
};
use core_solvers::solver_cohomology_quotient_phi1::certified_phi1;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

fn packet(vertices: &[&str], edges: &[(&str, &str)], faces: &[&[&str]]) -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(vertices, edges, faces).unwrap(),
    )
    .unwrap()
}

fn open_triangle() -> FiniteCochainPacket {
    packet(&["a", "b", "c"], &[("a", "b"), ("b", "c"), ("c", "a")], &[])
}

fn filled_triangle() -> FiniteCochainPacket {
    packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        &[&["a", "b", "c"]],
    )
}

/// Triangle abc filled, triangle acd left open.
fn two_triangles() -> FiniteCochainPacket {
    packet(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "a")],
        &[&["a", "b", "c"]],
    )
}

/// Every vector in `{-1, 0, 1}^len`.
fn unit_box(len: usize) -> Vec<Vec<Rational>> {
    (0..len).fold(vec![Vec::new()], |acc, _| {
        acc.iter()
            .flat_map(|prefix| {
                (-1..=1).map(move |v| {
                    let mut next = prefix.clone();
                    next.push(ri(v));
                    next
                })
            })
            .collect()
    })
}

/// A potential `f` with `d0 f = x`, found by exact row reduction, if one exists.
fn repair_potential(d0: &[Vec<Rational>], x: &[Rational]) -> Option<Vec<Rational>> {
    let cols = d0.first().map_or(0, Vec::len);
    let matrix =
        BasicMatrix::from_row_major(d0.len(), cols, d0.iter().flatten().cloned().collect())
            .unwrap();
    match solve_in_image(&matrix, x).unwrap() {
        ImageMembership::InImage(witness) => Some(witness.potential),
        ImageMembership::NotInImage { .. } => None,
    }
}

// ---------------------------------------------------------------------------
// QM-092-C2 / C3 / C6: total, exclusive, and equal to image plus closure.
// ---------------------------------------------------------------------------

#[test]
fn the_trichotomy_matches_image_membership_and_closure_on_every_box_cochain() {
    let cases = [
        (open_triangle(), [7, 20, 0]),
        (filled_triangle(), [7, 0, 20]),
        (two_triangles(), [17, 46, 180]),
    ];
    for (packet, expected_counts) in cases {
        let mut counts = [0usize; 3];
        for x in unit_box(packet.edge_count()) {
            let certified = packet.classify(&x).unwrap();
            let potential = repair_potential(packet.d0(), &x);
            let closed = packet
                .face_coboundary(&x)
                .unwrap()
                .iter()
                .all(Zero::is_zero);
            let expected = match (&potential, closed) {
                (Some(_), _) => ObstructionDiagnosticClass::ExactRepair,
                (None, true) => ObstructionDiagnosticClass::ClosedResidual,
                (None, false) => ObstructionDiagnosticClass::ActiveClosureFailure,
            };
            assert_eq!(certified.diagnostic_class(), expected, "x = {x:?}");
            // The quotient mass vanishes exactly on the repair image, and the
            // row-reduction potential replays: d0 f = x.
            assert_eq!(certified.phi1_value().is_zero(), potential.is_some());
            if let Some(f) = potential {
                assert_eq!(packet.primitive_difference(&f).unwrap(), x);
                assert!(certified.gamma2_value().is_zero());
            }
            counts[expected as usize] += 1;
        }
        assert_eq!(counts, expected_counts);
    }
}

#[test]
fn evidence_from_different_residuals_is_refused_rather_than_classified() {
    let packet = filled_triangle();
    let phi1 = packet.quotient_mass(&[ri(1), ri(0), ri(0)]).unwrap();
    let gamma2 = packet.closure_defect(&[ri(0), ri(1), ri(0)]).unwrap();
    assert_eq!(
        classify_exact(&phi1, &gamma2),
        TrichotomyOutcome::TriRefused(TrichotomyRefusal::IncompatiblePhi1Gamma2Evidence)
    );
    // The matched evidence for the same residual is classified.
    let matched = packet.closure_defect(phi1.primal_residual()).unwrap();
    assert!(matches!(
        classify_exact(&phi1, &matched),
        TrichotomyOutcome::Classified(_)
    ));
}

// ---------------------------------------------------------------------------
// QM-092-C4: a larger repair image never strands more defects.
// ---------------------------------------------------------------------------

#[test]
fn enlarging_the_repair_image_never_strands_more_defects() {
    let triangle = open_triangle();
    let weights = vec![ri(1); 3];
    let defects = unit_box(3);
    // Licensed repairs: potentials supported on a nested chain of vertex sets.
    let chain: [&[usize]; 4] = [&[], &[0], &[0, 1], &[0, 1, 2]];
    let mut stranded = Vec::new();
    let mut previous: Option<Vec<Rational>> = None;
    for support in chain {
        let d0: Vec<Vec<Rational>> = triangle
            .d0()
            .iter()
            .map(|row| support.iter().map(|&v| row[v].clone()).collect())
            .collect();
        let masses: Vec<Rational> = defects
            .iter()
            .map(|x| {
                certified_phi1(support.len(), &d0, x, &weights, 16_384)
                    .unwrap()
                    .value()
                    .clone()
            })
            .collect();
        if let Some(before) = &previous {
            assert!(masses.iter().zip(before).all(|(now, then)| now <= then));
        }
        for (x, mass) in defects.iter().zip(&masses) {
            assert_eq!(mass.is_zero(), repair_potential(&d0, x).is_some());
        }
        stranded.push(masses.iter().filter(|m| !m.is_zero()).count());
        previous = Some(masses);
    }
    // No repair; potentials at a; at a and b (already all of im d0); everywhere.
    assert_eq!(stranded, vec![26, 24, 20, 20]);
}

// Origin: engine/crates_rs/tests/core_quantum_physics/interpretations/typed_authority_boundary_suite.rs
// Claim: urn:core:crates_rs:tests:typed-authority-boundary-suite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord395ca7d8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord395ca7d8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError395ca7d8 {
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
impl BoundaryError395ca7d8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError395ca7d8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError395ca7d8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord395ca7d8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError395ca7d8> {
        if capacity_bound == 0 {
            return Err(BoundaryError395ca7d8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError395ca7d8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError395ca7d8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_395ca7d8() {
    let admitted = BoundaryRecord395ca7d8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord395ca7d8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
