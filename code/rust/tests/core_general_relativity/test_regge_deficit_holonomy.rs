//! Exact synthetic hinge turns on a declared finite complex. These fixtures
//! supply angle data and a correspondence; they do not derive Regge geometry.

use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::matrix::identity;
use linear_algebra::regge_exact::So4;
use num_bigint::BigInt;
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};
use core_general_relativity::regge_deficit_holonomy::{
    ordered_so4_boundary, DeclaredHingeStar, DeclaredReggeTurnComplex, OrientedSo4Step,
    ReggeTurnRefusal, ReggeTurnScope, So4EdgeTransport, So4Orientation,
};
use core_holonomy::gauge_quotient::{
    CommutingGaugeMap, GaugeClassification, GaugeDiagnosticAuthority, GaugeQuotientRefusal,
    GaugeSource, RationalGaugeQuotient,
};
use core_homology::declared_incidence::encode_declared;
use core_homology::simplicial::SimplicialComplex;
use core_number_theory::rational_turns::RationalTurn;

type TestResult = Result<(), Box<dyn std::error::Error>>;
const LIMITS: OperationLimits = OperationLimits {
    max_elements: 1 << 16,
    max_scalar_ops: 1 << 24,
};

fn q(n: i64, d: i64) -> Q {
    Q::new(n.into(), d.into())
}
fn source(label: &str) -> Result<GaugeSource, GaugeQuotientRefusal> {
    GaugeSource::from_bytes(label.to_owned(), label.as_bytes())
}

fn tetrahedron() -> Result<SimplicialComplex, Box<dyn std::error::Error>> {
    let cells = (1usize..16)
        .map(|mask| {
            (0usize..4)
                .filter(|&vertex| mask & (1usize << vertex) != 0)
                .collect()
        })
        .collect::<Vec<Vec<usize>>>();
    Ok(encode_declared(&cells)?)
}

fn tetra_quotient(label: &str) -> Result<RationalGaugeQuotient, Box<dyn std::error::Error>> {
    let tetrahedron = tetrahedron()?;
    Ok(RationalGaugeQuotient::try_new(
        Some(source(label)?),
        [4, 6, 4],
        Some(tetrahedron.boundary_matrix(1)?.try_transpose()?),
        Some(tetrahedron.boundary_matrix(2)?.try_transpose()?),
        LIMITS,
    )?)
}

fn turn_complex() -> Result<DeclaredReggeTurnComplex, Box<dyn std::error::Error>> {
    Ok(DeclaredReggeTurnComplex::try_new(
        Some(source("synthetic tetrahedral turns")?),
        &tetra_quotient("tetrahedral cochains")?,
        Some(tetrahedron()?.boundary_matrix(3)?.try_transpose()?),
        LIMITS,
    )?)
}

fn connection() -> Vec<Q> {
    vec![q(1, 4), q(0, 1), q(0, 1), q(0, 1), q(0, 1), q(0, 1)]
}

fn star(hinge: usize, deficit: &Q, sectors: usize) -> Result<DeclaredHingeStar, ReggeTurnRefusal> {
    let turn = (Q::one() - deficit) / Q::from_integer(sectors.into());
    let mut chamber_cycle: Vec<_> = (0..sectors).collect();
    chamber_cycle.push(0);
    DeclaredHingeStar::try_new(hinge, Some(chamber_cycle), Some(vec![turn; sectors]))
}

fn stars(curvature: &[Q]) -> Result<Vec<DeclaredHingeStar>, ReggeTurnRefusal> {
    curvature
        .iter()
        .enumerate()
        .map(|(hinge, value)| star(hinge, value, 3))
        .collect()
}

#[test]
fn dbar1_is_defined_on_the_full_quotient_and_replays_representative_shifts() -> TestResult {
    let quotient = tetra_quotient("tetra quotient")?;
    let original = connection();
    let class = quotient.project(&original, LIMITS)?;
    assert!(!class.is_zero());
    assert_eq!(quotient.quotient_dimension(), 3);
    assert_eq!(quotient.h1_dimension(), 0);
    let curvature = vec![q(1, 4), q(1, 4), q(0, 1), q(0, 1)];
    assert_eq!(quotient.dbar1(&class, LIMITS)?, curvature);
    let shift =
        quotient.shift_with_receipt(&original, &[q(1, 1), q(-2, 1), q(3, 1), q(4, 1)], LIMITS)?;
    assert_ne!(shift.original(), shift.shifted());
    assert_eq!(quotient.project(shift.shifted(), LIMITS)?, class);
    assert_eq!(shift.curvature(), curvature);
    assert_eq!(shift.authority_effect(), GaugeDiagnosticAuthority::None);
    shift.replay(&quotient, LIMITS)?;
    let diagnosis = quotient.diagnose(&original, LIMITS)?;
    assert_eq!(diagnosis.classification(), &GaugeClassification::NonClosed);
    diagnosis.replay(&quotient, LIMITS)?;
    Ok(())
}

fn build_unfilled_triangle_quotient() -> Result<RationalGaugeQuotient, Box<dyn std::error::Error>> {
    let circle = encode_declared(&[
        vec![0],
        vec![1],
        vec![2],
        vec![0, 1],
        vec![0, 2],
        vec![1, 2],
    ])?;
    assert_eq!(circle.rational_betti_numbers()?, vec![1, 1]);
    Ok(RationalGaugeQuotient::try_new(
        Some(source("unfilled triangle")?),
        [3, 3, 0],
        Some(circle.boundary_matrix(1)?.try_transpose()?),
        Some(BasicMatrix::from_row_major(0, 3, vec![])?),
        LIMITS,
    )?)
}

#[test]
fn closed_nonzero_h1_cannot_be_repaired_by_a_gauge_shift() -> TestResult {
    let quotient = build_unfilled_triangle_quotient()?;
    let residual = vec![q(1, 100_000_000), q(0, 1), q(0, 1)];
    let diagnosis = quotient.diagnose(&residual, LIMITS)?;
    assert_eq!(diagnosis.h1_dimension(), 1);
    assert!(!diagnosis.class().is_zero());
    assert!(diagnosis.curvature().is_empty());
    match diagnosis.classification() {
        GaugeClassification::ClosedNonExact { h1_coordinates } => {
            assert_eq!(h1_coordinates.len(), 1);
            assert_eq!(h1_coordinates[0].abs(), q(1, 100_000_000));
        }
        unexpected => panic!("unexpected exact classification: {unexpected:?}"),
    }
    let shifted = quotient.shift_with_receipt(&residual, &[q(7, 1), q(-8, 1), q(9, 1)], LIMITS)?;
    assert_eq!(shifted.class(), diagnosis.class());
    assert!(matches!(
        quotient.diagnose(shifted.shifted(), LIMITS)?.classification(),
        GaugeClassification::ClosedNonExact { .. }
    ));
    diagnosis.replay(&quotient, LIMITS)?;
    Ok(())
}

#[test]
fn exact_repair_is_replayed_and_zero_has_its_own_classification() -> TestResult {
    let quotient = tetra_quotient("exact repair")?;
    let potential = vec![q(1, 1), q(-2, 1), q(3, 1), q(4, 1)];
    let representative = quotient
        .d0()
        .checked_mul_vec_with_limits(&potential, LIMITS)?;
    let diagnosis = quotient.diagnose(&representative, LIMITS)?;
    assert!(diagnosis.class().is_zero());
    assert!(diagnosis.curvature().iter().all(Zero::is_zero));
    match diagnosis.classification() {
        GaugeClassification::ExactRepairable { potential } => {
            assert_eq!(
                quotient
                    .d0()
                    .checked_mul_vec_with_limits(potential, LIMITS)?,
                representative
            );
        }
        unexpected => panic!("unexpected exact classification: {unexpected:?}"),
    }
    assert_eq!(diagnosis.authority_effect(), GaugeDiagnosticAuthority::None);
    diagnosis.replay(&quotient, LIMITS)?;
    assert_eq!(
        quotient
            .diagnose(&vec![Q::zero(); 6], LIMITS)?
            .classification(),
        &GaugeClassification::Zero
    );
    Ok(())
}

fn verify_zero_and_wrong_gauge_maps(
    source: &RationalGaugeQuotient,
    target: &RationalGaugeQuotient,
    mut wrong: [BasicMatrix<Q>; 3],
) -> TestResult {
    wrong[1].set(0, 0, q(3, 1))?;
    assert!(matches!(
        CommutingGaugeMap::try_new(source, target, wrong, LIMITS),
        Err(GaugeQuotientRefusal::NonCommutingMap("d0"))
    ));
    let zero_map = CommutingGaugeMap::try_new(
        source,
        target,
        [
            BasicMatrix::try_from_fn(4, 4, |_, _| Q::zero())?,
            BasicMatrix::try_from_fn(6, 6, |_, _| Q::zero())?,
            BasicMatrix::try_from_fn(4, 4, |_, _| Q::zero())?,
        ],
        LIMITS,
    )?;
    let projected = source.project(&connection(), LIMITS)?;
    assert!(!projected.is_zero());
    assert!(zero_map.transport_class(&projected, LIMITS)?.is_zero());
    Ok(())
}

fn scaled_identity_map(n: usize) -> Result<BasicMatrix<Q>, Box<dyn std::error::Error>> {
    Ok(BasicMatrix::try_from_fn(n, n, |i, j| if i == j { q(2, 1) } else { q(0, 1) })?)
}

#[test]
fn commuting_map_transports_representatives_and_curvature_without_assuming_an_inverse() -> TestResult
{
    let source = tetra_quotient("transport source")?;
    let target = tetra_quotient("transport target")?;
    let maps = [scaled_identity_map(4)?, scaled_identity_map(6)?, scaled_identity_map(4)?];
    let map = CommutingGaugeMap::try_new(&source, &target, maps.clone(), LIMITS)?;
    let transport = map.transport_with_receipt(
        &connection(),
        &[q(1, 1), q(2, 1), q(-1, 1), q(4, 1)],
        LIMITS,
    )?;
    let expected: Vec<_> = transport
        .source_shift()
        .shifted()
        .iter()
        .map(|value| value * q(2, 1))
        .collect();
    assert_eq!(transport.target_shift().shifted(), expected);
    assert_eq!(
        map.transport_class(transport.source_shift().class(), LIMITS)?,
        *transport.target_shift().class()
    );
    assert_eq!(transport.authority_effect(), GaugeDiagnosticAuthority::None);
    transport.replay(&map, LIMITS)?;
    verify_zero_and_wrong_gauge_maps(&source, &target, maps)
}

#[test]
fn synthetic_hinge_turns_have_exact_oriented_boundary_holonomy() -> TestResult {
    let complex = turn_complex()?;
    let curvature = complex.quotient().curvature(&connection(), LIMITS)?;
    let data = stars(&curvature)?;
    let deficit = complex.evaluate(Some(&data), Some(&connection()), LIMITS)?;
    assert_eq!(deficit.deficit_turns(), curvature);
    assert_eq!(deficit.scope(), ReggeTurnScope::DeclaredRationalHingeTurns);
    assert_eq!(deficit.holonomy_turns()[0], RationalTurn::new(q(1, 4)));
    assert_eq!(deficit.authority_effect(), GaugeDiagnosticAuthority::None);
    let boundary = complex.boundary_holonomy(&deficit, Some(&[BigInt::one()]), LIMITS)?;
    assert_eq!(
        boundary.boundary_cycle(),
        &[(-1).into(), 1.into(), (-1).into(), 1.into()]
    );
    assert!(boundary.curvature_pairing().is_zero());
    assert!(boundary.deficit_pairing().is_zero());
    assert_eq!(boundary.holonomy(), &RationalTurn::zero());
    assert_eq!(boundary.authority_effect(), GaugeDiagnosticAuthority::None);
    boundary.replay(&complex, LIMITS)?;
    let shift = complex.quotient().shift_with_receipt(
        &connection(),
        &[q(3, 1), q(2, 1), q(1, 1), q(0, 1)],
        LIMITS,
    )?;
    let shifted = complex.evaluate(Some(&data), Some(shift.shifted()), LIMITS)?;
    assert_eq!(shifted.curvature(), deficit.curvature());
    assert_eq!(shifted.holonomy_turns(), deficit.holonomy_turns());
    Ok(())
}

#[test]
fn unsigned_scalar_deficit_cancellation_is_false_even_on_the_licensed_boundary() -> TestResult {
    let complex = turn_complex()?;
    let data = stars(&complex.quotient().curvature(&connection(), LIMITS)?)?;
    let deficit = complex.evaluate(Some(&data), Some(&connection()), LIMITS)?;
    let unsigned_sum: Q = deficit.deficit_turns().iter().cloned().sum();
    assert_eq!(unsigned_sum, q(1, 2));
    // In radian notation the scalar sum is pi, rather than zero modulo 2*pi.
    assert_ne!(RationalTurn::new(unsigned_sum), RationalTurn::zero());
    assert_eq!(
        complex
            .boundary_holonomy(&deficit, Some(&[1.into()]), LIMITS)?
            .holonomy(),
        &RationalTurn::zero()
    );
    Ok(())
}

#[test]
fn integer_deficit_lifts_preserve_holonomy_but_need_not_cancel_as_rational_numbers() -> TestResult {
    let complex = turn_complex()?;
    let curvature = complex.quotient().curvature(&connection(), LIMITS)?;
    let mut data = stars(&curvature)?;
    data[0] = star(0, &(&curvature[0] - Q::one()), 5)?;
    let deficit = complex.evaluate(Some(&data), Some(&connection()), LIMITS)?;
    assert_eq!(deficit.deficit_turns()[0], q(-3, 4));
    assert_eq!(deficit.curvature()[0], q(1, 4));
    assert_eq!(deficit.holonomy_turns()[0], RationalTurn::new(q(1, 4)));
    let boundary = complex.boundary_holonomy(&deficit, Some(&[1.into()]), LIMITS)?;
    assert_eq!(boundary.deficit_pairing(), &Q::one());
    assert_eq!(boundary.curvature_pairing(), &Q::zero());
    assert_eq!(boundary.holonomy(), &RationalTurn::zero());
    // The character is exact in the declared conductor, with no trig evaluation.
    assert_eq!(
        boundary.holonomy().character_in(4)?,
        RationalTurn::zero().character_in(4)?
    );
    boundary.replay(&complex, LIMITS)?;
    Ok(())
}

#[test]
fn absent_data_invalid_shapes_and_noncanonical_rationals_fail_closed() -> TestResult {
    let quotient = tetra_quotient("refusals")?;
    assert!(matches!(
        RationalGaugeQuotient::try_new(
            None,
            [4, 6, 4],
            Some(quotient.d0().clone()),
            Some(quotient.d1().clone()),
            LIMITS
        ),
        Err(GaugeQuotientRefusal::MissingSource)
    ));
    assert!(matches!(
        RationalGaugeQuotient::try_new(
            Some(source("missing d0")?),
            [4, 6, 4],
            None,
            Some(quotient.d1().clone()),
            LIMITS
        ),
        Err(GaugeQuotientRefusal::MissingDifferential("d0"))
    ));
    assert!(matches!(
        RationalGaugeQuotient::try_new(
            Some(source("missing d1")?),
            [4, 6, 4],
            Some(quotient.d0().clone()),
            None,
            LIMITS
        ),
        Err(GaugeQuotientRefusal::MissingDifferential("d1"))
    ));
    assert!(matches!(
        RationalGaugeQuotient::try_new(
            Some(source("wrong shape")?),
            [4, 5, 4],
            Some(quotient.d0().clone()),
            Some(quotient.d1().clone()),
            LIMITS
        ),
        Err(GaugeQuotientRefusal::Shape("d0"))
    ));
    assert_noncanonical_rational_refusals(&quotient)?;
    assert!(matches!(
        RationalGaugeQuotient::try_new(
            Some(source("chain law")?),
            [1, 1, 1],
            Some(identity(1)?),
            Some(identity(1)?),
            LIMITS
        ),
        Err(GaugeQuotientRefusal::ChainLaw)
    ));
    assert_regge_turn_complex_refusals(&quotient)
}

fn assert_noncanonical_rational_refusals(quotient: &RationalGaugeQuotient) -> TestResult {
    for raw in [
        Q::new_raw(1.into(), 0.into()),
        Q::new_raw(2.into(), 4.into()),
        Q::new_raw(1.into(), (-2).into()),
    ] {
        let mut value = connection();
        value[0] = raw.clone();
        assert!(matches!(
            quotient.project(&value, LIMITS),
            Err(GaugeQuotientRefusal::NonCanonicalRational("representative"))
        ));
        let mut d0 = quotient.d0().clone();
        d0.set(0, 0, raw)?;
        assert!(matches!(
            RationalGaugeQuotient::try_new(
                Some(source("raw differential")?),
                [4, 6, 4],
                Some(d0),
                Some(quotient.d1().clone()),
                LIMITS
            ),
            Err(GaugeQuotientRefusal::NonCanonicalRational("d0"))
        ));
    }
    Ok(())
}

fn assert_regge_turn_complex_refusals(quotient: &RationalGaugeQuotient) -> TestResult {
    assert!(matches!(
        DeclaredReggeTurnComplex::try_new(
            None,
            quotient,
            Some(BasicMatrix::from_row_major(0, 4, vec![])?),
            LIMITS
        ),
        Err(ReggeTurnRefusal::MissingSource)
    ));
    assert!(matches!(
        DeclaredReggeTurnComplex::try_new(Some(source("missing d2")?), quotient, None, LIMITS),
        Err(ReggeTurnRefusal::MissingData("d2"))
    ));
    let complex = turn_complex()?;
    assert!(matches!(
        complex.evaluate(None, Some(&connection()), LIMITS),
        Err(ReggeTurnRefusal::MissingData("hinge stars"))
    ));
    let data = stars(&complex.quotient().curvature(&connection(), LIMITS)?)?;
    assert!(matches!(
        complex.evaluate(Some(&data), None, LIMITS),
        Err(ReggeTurnRefusal::MissingData("connection cochain"))
    ));
    assert!(matches!(
        complex.evaluate(Some(&data[..3]), Some(&connection()), LIMITS),
        Err(ReggeTurnRefusal::MissingHinge(3))
    ));
    let mut duplicate = data.clone();
    duplicate[3] = duplicate[2].clone();
    assert!(matches!(
        complex.evaluate(Some(&duplicate), Some(&connection()), LIMITS),
        Err(ReggeTurnRefusal::DuplicateHinge(2))
    ));
    let mut incompatible = data;
    incompatible[0] = star(0, &Q::zero(), 3)?;
    assert!(matches!(
        complex.evaluate(Some(&incompatible), Some(&connection()), LIMITS),
        Err(ReggeTurnRefusal::DeficitCorrespondence(0))
    ));
    Ok(())
}

#[test]
fn excluded_incidence_and_hinge_cycle_premises_have_distinct_refusals() -> TestResult {
    let complex = turn_complex()?;
    let mut nonintegral = complex.d2().clone();
    nonintegral.set(0, 0, q(1, 2))?;
    assert!(matches!(
        DeclaredReggeTurnComplex::try_new(
            Some(source("nonintegral")?),
            complex.quotient(),
            Some(nonintegral),
            LIMITS
        ),
        Err(ReggeTurnRefusal::NonIntegralIncidence)
    ));
    let mut not_closed = complex.d2().clone();
    not_closed.set(0, 0, Q::one())?;
    assert!(matches!(
        DeclaredReggeTurnComplex::try_new(
            Some(source("not closed")?),
            complex.quotient(),
            Some(not_closed),
            LIMITS
        ),
        Err(ReggeTurnRefusal::CurvatureLaw)
    ));
    assert!(matches!(
        DeclaredHingeStar::try_new(0, None, Some(vec![q(1, 4); 3])),
        Err(ReggeTurnRefusal::MissingData("chamber cycle"))
    ));
    assert!(matches!(
        DeclaredHingeStar::try_new(0, Some(vec![0, 1, 2, 3]), Some(vec![q(1, 4); 3])),
        Err(ReggeTurnRefusal::InvalidHingeCycle)
    ));
    assert!(matches!(
        DeclaredHingeStar::try_new(0, Some(vec![0, 1, 1, 0]), Some(vec![q(1, 4); 3])),
        Err(ReggeTurnRefusal::InvalidHingeCycle)
    ));
    assert!(matches!(
        DeclaredHingeStar::try_new(0, Some(vec![0, 1, 2, 0]), Some(vec![q(1, 2); 3])),
        Err(ReggeTurnRefusal::DihedralTurnRange)
    ));
    let data = stars(&complex.quotient().curvature(&connection(), LIMITS)?)?;
    assert!(matches!(
        complex.evaluate(
            Some(&data),
            Some(&connection()),
            OperationLimits {
                max_elements: 11,
                max_scalar_ops: LIMITS.max_scalar_ops
            }
        ),
        Err(ReggeTurnRefusal::Budget)
    ));
    assert_boundary_and_carrier_refusals(&complex, &data)
}

fn assert_boundary_and_carrier_refusals(
    complex: &DeclaredReggeTurnComplex,
    data: &[DeclaredHingeStar],
) -> TestResult {
    let deficit = complex.evaluate(Some(data), Some(&connection()), LIMITS)?;
    assert!(matches!(
        complex.boundary_holonomy(&deficit, None, LIMITS),
        Err(ReggeTurnRefusal::MissingData("integral three-chain"))
    ));
    assert!(matches!(
        complex.boundary_holonomy(&deficit, Some(&[]), LIMITS),
        Err(ReggeTurnRefusal::Shape("integral three-chain"))
    ));
    assert!(matches!(
        complex.boundary_holonomy(&deficit, Some(&[0.into()]), LIMITS),
        Err(ReggeTurnRefusal::EmptyBoundaryCycle)
    ));
    let other_source = DeclaredReggeTurnComplex::try_new(
        Some(source("another source")?),
        complex.quotient(),
        Some(complex.d2().clone()),
        LIMITS,
    )?;
    assert!(matches!(
        deficit.replay(&other_source, LIMITS),
        Err(ReggeTurnRefusal::CarrierMismatch)
    ));
    assert!(matches!(
        complex.quotient().shift_with_receipt(&connection(), &[q(1, 1)], LIMITS),
        Err(GaugeQuotientRefusal::Shape("potential"))
    ));
    assert!(complex
        .quotient()
        .project(
            &connection(),
            OperationLimits {
                max_elements: 0,
                max_scalar_ops: 0
            }
        )
        .is_err());
    assert!(matches!(
        tetra_quotient("other source")?
            .dbar1(&complex.quotient().project(&connection(), LIMITS)?, LIMITS),
        Err(GaugeQuotientRefusal::CarrierMismatch)
    ));
    Ok(())
}

fn rotation(a: usize, b: usize) -> [[Q; 4]; 4] {
    let mut matrix = So4::identity().m;
    matrix[a][a] = q(3, 5);
    matrix[b][b] = q(3, 5);
    matrix[a][b] = q(-4, 5);
    matrix[b][a] = q(4, 5);
    matrix
}
fn forward(edge: usize) -> OrientedSo4Step {
    OrientedSo4Step {
        edge,
        orientation: So4Orientation::Forward,
    }
}
fn reverse(edge: usize) -> OrientedSo4Step {
    OrientedSo4Step {
        edge,
        orientation: So4Orientation::Reverse,
    }
}

fn build_so4_tetra_edges(g: &So4, h: &So4) -> Result<Vec<So4EdgeTransport>, Box<dyn std::error::Error>> {
    Ok(vec![
        So4EdgeTransport::try_new(0, 1, g.m.clone())?,
        So4EdgeTransport::try_new(0, 2, So4::identity().m)?,
        So4EdgeTransport::try_new(0, 3, So4::identity().m)?,
        So4EdgeTransport::try_new(1, 2, h.m.clone())?,
        So4EdgeTransport::try_new(1, 3, So4::identity().m)?,
        So4EdgeTransport::try_new(2, 3, So4::identity().m)?,
    ])
}

#[test]
fn noncommuting_so4_bianchi_preserves_order_common_frames_and_the_complete_word() -> TestResult {
    let g = So4::try_new(rotation(0, 1)).map_err(|error| {
        std::io::Error::new(std::io::ErrorKind::InvalidData, format!("{error:?}"))
    })?;
    let h = So4::try_new(rotation(1, 2)).map_err(|error| {
        std::io::Error::new(std::io::ErrorKind::InvalidData, format!("{error:?}"))
    })?;
    assert_ne!(g.mul(&h), h.mul(&g));
    // a=01, b=02, c=03, d=12, e=13, f=23. All loops are based at 0.
    let edges = build_so4_tetra_edges(&g, &h)?;
    let loops = vec![
        vec![forward(0), forward(3), reverse(1)],
        vec![forward(1), forward(5), reverse(2)],
        vec![forward(2), reverse(4), reverse(0)],
        vec![forward(0), forward(4), reverse(5), reverse(3), reverse(0)],
    ];
    let receipt = ordered_so4_boundary(
        Some(source("ordered tetrahedron boundary")?),
        Some(&edges),
        Some(&loops),
        0,
        LIMITS,
    )?;
    assert!(receipt.ordered_product().is_identity());
    assert_eq!(receipt.authority_effect(), GaugeDiagnosticAuthority::None);
    receipt.replay(LIMITS)?;
    assert!(matches!(
        ordered_so4_boundary(
            Some(source("bounded word")?),
            Some(&edges),
            Some(&loops),
            0,
            OperationLimits {
                max_elements: 16,
                max_scalar_ops: LIMITS.max_scalar_ops
            }
        ),
        Err(ReggeTurnRefusal::Budget)
    ));
    let mut reordered = loops.clone();
    reordered.swap(0, 2);
    assert!(matches!(
        ordered_so4_boundary(
            Some(source("reordered boundary")?),
            Some(&edges),
            Some(&reordered),
            0,
            LIMITS
        ),
        Err(ReggeTurnRefusal::UncancelledBoundaryWord)
    ));
    // The excluded order also fails numerically over exact rationals.
    let wrong_product = core_general_relativity::exact_regge::hinge_holonomy(&[
        g.transpose(),
        So4::identity(),
        g.mul(&h),
        g.mul(&h.transpose()).mul(&g.transpose()),
    ]);
    assert!(!wrong_product.is_identity());
    assert_so4_boundary_refusals(&edges, &loops)
}

fn assert_so4_boundary_refusals(
    edges: &[So4EdgeTransport],
    loops: &[Vec<OrientedSo4Step>],
) -> TestResult {
    assert!(matches!(
        ordered_so4_boundary(Some(source("wrong base")?), Some(edges), Some(loops), 1, LIMITS),
        Err(ReggeTurnRefusal::CommonBasepoint)
    ));
    let mut missing = loops.to_vec();
    missing[0][1].edge = 255;
    assert!(matches!(
        ordered_so4_boundary(Some(source("missing edge")?), Some(edges), Some(&missing), 0, LIMITS),
        Err(ReggeTurnRefusal::MissingEdge(255))
    ));
    assert!(matches!(
        ordered_so4_boundary(None, Some(edges), Some(loops), 0, LIMITS),
        Err(ReggeTurnRefusal::MissingSource)
    ));
    assert!(matches!(
        ordered_so4_boundary(Some(source("empty boundary")?), Some(edges), Some(&[]), 0, LIMITS),
        Err(ReggeTurnRefusal::MissingData("nonempty SO4 boundary word"))
    ));
    let mut malformed = So4::identity().m;
    malformed[0][0] = Q::new_raw(1.into(), 0.into());
    assert!(matches!(
        So4EdgeTransport::try_new(0, 1, malformed),
        Err(ReggeTurnRefusal::NonCanonicalRational("SO4 transition"))
    ));
    let mut reflection = So4::identity().m;
    reflection[0][0] = q(-1, 1);
    assert!(matches!(
        So4EdgeTransport::try_new(0, 1, reflection),
        Err(ReggeTurnRefusal::FrameRejected)
    ));
    Ok(())
}

// Origin: engine/crates_rs/tests/core_general_relativity/test_regge_deficit_holonomy.rs
// Claim: urn:core:crates_rs:tests:test-regge-deficit-holonomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
