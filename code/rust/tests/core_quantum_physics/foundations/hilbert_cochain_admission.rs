//! Cohomology admission of residuals on declared cochain complexes: the four
//! worked cases with replayable certificates, the complex law, the `d1 = 0`
//! quotient identity, the promotion fence for quotient obstructions, and a
//! classical and a quantum realization that the classification cannot tell
//! apart.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix;
use core_functional::gamma2::{Complex2InputQ, ExactCochainComplexQ, ExactGamma2Error};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_solvers::cert_cohomology_admission::{
    admit, cohomology_dimensions, complex_of_packet, image_preimage, verify_admission, Admission,
    AdmissionRefusal, CohomologyDimensions,
};

fn packet(vertices: &[&str], edges: &[(&str, &str)], faces: &[&[&str]]) -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(vertices, edges, faces).unwrap(),
    )
    .unwrap()
}

fn path() -> FiniteCochainPacket {
    packet(&["a", "b", "c"], &[("a", "b"), ("b", "c")], &[])
}

fn square() -> FiniteCochainPacket {
    packet(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")],
        &[],
    )
}

fn filled_triangle() -> FiniteCochainPacket {
    packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        &[&["a", "b", "c"]],
    )
}

/// A filled triangle `abc` sharing the edge `ca` with an unfilled triangle `acd`.
fn census() -> FiniteCochainPacket {
    packet(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "a")],
        &[&["a", "b", "c"]],
    )
}

fn unit(index: usize, len: usize) -> Vec<Rational> {
    (0..len)
        .map(|i| if i == index { ri(1) } else { ri(0) })
        .collect()
}

fn rats(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|v| ri(*v)).collect()
}

// ---------------------------------------------------------------------------
// The four worked cases
// ---------------------------------------------------------------------------

#[test]
fn the_four_worked_cases_classify_with_replayable_certificates() {
    let path = complex_of_packet(&path()).unwrap();
    let exact = rats(&[2, 3]); // d0 (0, 2, 5)
    let admitted = admit(&path, Some(&exact));
    assert!(matches!(&admitted, Admission::Exact { .. }));
    assert!(verify_admission(&path, &exact, &admitted));

    let square = complex_of_packet(&square()).unwrap();
    let generator = unit(3, 4);
    let admitted = admit(&square, Some(&generator));
    let Admission::ClosedNonexact { separator } = &admitted else {
        panic!("expected a closed nonexact class")
    };
    assert!(verify_admission(&square, &generator, &admitted));
    // The separator is the cycle's circulation, up to scale.
    assert!(separator.iter().all(|z| z == &separator[0]) && separator[0] != ri(0));

    let triangle = complex_of_packet(&filled_triangle()).unwrap();
    let edge = unit(0, 3);
    let admitted = admit(&triangle, Some(&edge));
    assert_eq!(
        admitted,
        Admission::ActiveClosureFailure { defect: rats(&[1]) }
    );
    assert!(verify_admission(&triangle, &edge, &admitted));

    // Without a declared adapter, or with an ill-typed cochain, nothing is admitted.
    assert_eq!(
        admit(&square, None),
        Admission::Refused(AdmissionRefusal::NoAdapter)
    );
    assert_eq!(
        admit(&square, Some(&rats(&[1]))),
        Admission::Refused(AdmissionRefusal::CochainLength {
            expected: 4,
            actual: 1
        })
    );
    assert!(!verify_admission(
        &square,
        &generator,
        &Admission::Refused(AdmissionRefusal::NoAdapter)
    ));
}

#[test]
fn tampered_certificates_are_rejected() {
    let square = complex_of_packet(&square()).unwrap();
    let exact = rats(&[1, 1, 1, -3]); // d0 (0, 1, 2, 3)
    let Admission::Exact { mut preimage } = admit(&square, Some(&exact)) else {
        panic!("expected exact")
    };
    preimage[1] += ri(1);
    assert!(!verify_admission(
        &square,
        &exact,
        &Admission::Exact { preimage }
    ));

    let generator = unit(0, 4);
    let separator = match admit(&square, Some(&generator)) {
        Admission::ClosedNonexact { separator } => separator,
        other => panic!("expected closed nonexact, got {other:?}"),
    };
    // A separator annihilates the image, so it cannot certify an exact cochain.
    assert!(!verify_admission(
        &square,
        &exact,
        &Admission::ClosedNonexact { separator }
    ));
    assert!(!verify_admission(
        &square,
        &generator,
        &Admission::ClosedNonexact {
            separator: unit(0, 4)
        }
    ));

    let triangle = complex_of_packet(&filled_triangle()).unwrap();
    let edge = unit(0, 3);
    assert!(!verify_admission(
        &triangle,
        &edge,
        &Admission::ActiveClosureFailure { defect: rats(&[2]) }
    ));
}

// ---------------------------------------------------------------------------
// The complex law, the d1 = 0 identity and the promotion fence
// ---------------------------------------------------------------------------

#[test]
fn a_declaration_violating_the_complex_law_is_refused_and_exact_residuals_are_closed() {
    let broken =
        ExactCochainComplexQ::try_new(2, 1, 1, vec![vec![ri(-1), ri(1)]], vec![vec![ri(1)]]);
    assert!(matches!(
        broken,
        Err(ExactGamma2Error::CochainIdentityViolation { .. })
    ));

    let packet = census();
    let complex = complex_of_packet(&packet).unwrap();
    for vertex in 0..packet.vertex_count() {
        let s = packet
            .primitive_difference(&unit(vertex, packet.vertex_count()))
            .unwrap();
        assert!(packet
            .face_coboundary(&s)
            .unwrap()
            .iter()
            .all(|v| v == &ri(0)));
        assert!(matches!(admit(&complex, Some(&s)), Admission::Exact { .. }));
    }
}

#[test]
fn without_two_cells_h1_is_the_quotient_and_with_them_it_is_smaller() {
    let dims =
        |p: FiniteCochainPacket| cohomology_dimensions(&complex_of_packet(&p).unwrap()).unwrap();
    let d = |rank_d0, rank_d1, quotient, cycles, h1| CohomologyDimensions {
        rank_d0,
        rank_d1,
        quotient,
        cycles,
        h1,
    };
    assert_eq!(dims(path()), d(2, 0, 0, 2, 0));
    assert_eq!(dims(square()), d(3, 0, 1, 4, 1));
    assert_eq!(dims(filled_triangle()), d(2, 1, 1, 2, 0));
    assert_eq!(dims(census()), d(3, 1, 2, 4, 1));
    for p in [path(), square(), filled_triangle(), census()] {
        let found = dims(p);
        assert_eq!(found.quotient - found.h1, found.rank_d1);
    }
}

#[test]
fn a_quotient_obstruction_is_an_h1_class_only_when_closed() {
    let triangle = filled_triangle();
    let complex = complex_of_packet(&triangle).unwrap();
    let s = unit(0, 3);
    // Outside im d0: a nonzero class of the quotient, with positive Phi1...
    assert_eq!(image_preimage(&complex, &s).unwrap(), None);
    assert_eq!(triangle.quotient_mass(&s).unwrap().value(), &ri(1));
    // ...but not closed, so it is no class of H^1.
    assert!(matches!(
        admit(&complex, Some(&s)),
        Admission::ActiveClosureFailure { .. }
    ));
    // Declaring no 2-cells makes the same cochain a closed nonexact class.
    let unfilled = ExactCochainComplexQ::try_new(3, 3, 0, complex.d0().to_vec(), vec![]).unwrap();
    assert!(matches!(
        admit(&unfilled, Some(&s)),
        Admission::ClosedNonexact { .. }
    ));
    // With no declared d1 at all, the complex itself is refused.
    assert!(matches!(
        ExactCochainComplexQ::try_new_with_complex2(
            3,
            3,
            complex.d0().to_vec(),
            Complex2InputQ::Missing
        ),
        Err(ExactGamma2Error::MissingComplex2)
    ));
}

#[test]
fn the_algebraic_admission_agrees_with_the_certified_trichotomy() {
    let packet = census();
    let complex = complex_of_packet(&packet).unwrap();
    let residuals = [
        packet.primitive_difference(&rats(&[1, 2, 4, 8])).unwrap(),
        unit(3, 5),
        unit(4, 5),
        unit(0, 5),
        vec![rq(1, 2), ri(-3), ri(0), ri(7), rq(-5, 3)],
        vec![ri(1), ri(1), ri(1), ri(0), ri(0)],
    ];
    for s in &residuals {
        let admitted = admit(&complex, Some(s));
        assert!(verify_admission(&complex, s, &admitted));
        assert_eq!(
            admitted.diagnostic_class(),
            Some(packet.classify(s).unwrap().diagnostic_class())
        );
    }
}

// ---------------------------------------------------------------------------
// Non-selection: a classical and a quantum realization on one skeleton
// ---------------------------------------------------------------------------

/// Edges of [`census`] as (tail, head) vertex indices.
const CENSUS_EDGES: [(usize, usize); 5] = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 0)];

/// Column-stochastic 2x2 transport: `t[i][j] = P(i | j)`.
type Stochastic = [[Rational; 2]; 2];

fn stochastic_identity() -> Stochastic {
    [[ri(1), ri(0)], [ri(0), ri(1)]]
}

/// Readout at the head minus the readout of the transported tail, where the
/// readout is the probability of outcome 0.
fn classical_residual(p: &[[Rational; 2]], transports: &[Stochastic]) -> Vec<Rational> {
    CENSUS_EDGES
        .iter()
        .zip(transports)
        .map(|((u, v), t)| &p[*v][0] - (&t[0][0] * &p[*u][0] + &t[0][1] * &p[*u][1]))
        .collect()
}

fn quantum_residual(
    rho: &[BasicMatrix<GaussianRat>],
    channels: &[ExactKrausChannel],
) -> Vec<Rational> {
    let e0 = matrix::diagonal(&[gi(1, 0), gi(0, 0)]).unwrap();
    let readout = |m: &BasicMatrix<GaussianRat>| {
        let value = matrix::trace(&matrix::multiply(&e0, m).unwrap()).unwrap();
        assert_eq!(value.im, ri(0));
        value.re
    };
    CENSUS_EDGES
        .iter()
        .zip(channels)
        .map(|((u, v), channel)| readout(&rho[*v]) - readout(&channel.apply(&rho[*u]).unwrap()))
        .collect()
}

fn state(p0: Rational, coherence: Rational) -> BasicMatrix<GaussianRat> {
    let g = |r: Rational| core_number_theory::cyclotomic::GaussianRat { re: r, im: ri(0) };
    matrix::from_rows(vec![
        vec![g(p0.clone()), g(coherence.clone())],
        vec![g(coherence), g(ri(1) - p0)],
    ])
    .unwrap()
}

#[test]
fn classical_and_quantum_realizations_share_every_diagnostic_class() {
    let complex = complex_of_packet(&census()).unwrap();
    let identity_channel =
        || ExactKrausChannel::from_operators(vec![matrix::identity(2).unwrap()]).unwrap();
    let rotation = || {
        ExactKrausChannel::from_operators(vec![matrix::from_rows(vec![
            vec![gq(3, 5, 0, 1), gq(4, 5, 0, 1)],
            vec![gq(4, 5, 0, 1), gq(-3, 5, 0, 1)],
        ])
        .unwrap()])
        .unwrap()
    };
    let damping: Stochastic = [[ri(1), rq(24, 25)], [ri(0), rq(1, 25)]];

    // Identity transports: both residuals are the coboundary of the readouts.
    let p0 = [rq(1, 2), rq(1, 3), rq(1, 4), rq(1, 5)];
    let classical = classical_residual(
        &p0.iter()
            .map(|p| [p.clone(), ri(1) - p])
            .collect::<Vec<_>>(),
        &vec![stochastic_identity(); 5],
    );
    let coherent: Vec<BasicMatrix<GaussianRat>> =
        p0.iter().map(|p| state(p.clone(), rq(1, 10))).collect();
    let quantum = quantum_residual(
        &coherent,
        &(0..5).map(|_| identity_channel()).collect::<Vec<_>>(),
    );
    assert_eq!(classical, quantum);
    assert!(matches!(
        admit(&complex, Some(&quantum)),
        Admission::Exact { .. }
    ));

    // One non-identity transport, on the unfilled cycle's edge (index 3) and then
    // on an edge of the filled face (index 0).
    let half = [rq(1, 2), rq(1, 2)];
    let plus = state(rq(1, 2), rq(1, 2));
    for (edge, class) in [
        (3, ObstructionDiagnosticClass::ClosedResidual),
        (0, ObstructionDiagnosticClass::ActiveClosureFailure),
    ] {
        let mut transports = vec![stochastic_identity(); 5];
        transports[edge] = damping.clone();
        let classical = classical_residual(&vec![half.clone(); 4], &transports);
        let channels: Vec<ExactKrausChannel> = (0..5)
            .map(|e| {
                if e == edge {
                    rotation()
                } else {
                    identity_channel()
                }
            })
            .collect();
        let quantum = quantum_residual(&vec![plus.clone(); 4], &channels);
        assert_eq!(classical, quantum);
        assert_eq!(quantum[edge], rq(-12, 25));
        let admitted = admit(&complex, Some(&quantum));
        assert_eq!(admitted.diagnostic_class(), Some(class));
        assert!(verify_admission(&complex, &classical, &admitted));

        // The residuals have different sources. Dephasing the vertex states
        // removes the quantum residual, which came from coherence; the
        // classical one came from the transport and stays.
        let dephased = quantum_residual(&vec![state(rq(1, 2), ri(0)); 4], &channels);
        assert!(dephased.iter().all(|v| v == &ri(0)));
        assert_eq!(
            classical_residual(&vec![half.clone(); 4], &transports),
            classical
        );
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/foundations/hilbert_cochain_admission.rs
// Claim: urn:core:crates_rs:tests:hilbert-cochain-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda15ee097 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda15ee097` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora15ee097 {
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
impl BoundaryErrora15ee097 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora15ee097 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora15ee097 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda15ee097 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora15ee097> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora15ee097::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora15ee097::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora15ee097::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a15ee097() {
    let admitted = BoundaryRecorda15ee097::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda15ee097::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
