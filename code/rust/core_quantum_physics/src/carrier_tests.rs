//! Three distinct finite quantum/classical questions. AuthorityEffect: None.
//! Report sufficiency concerns a supplied finite state family and future test;
//! Bell extension concerns positive joint assignments, not signed solutions;
//! purification bounds use the declared complex direct-sum tensor model.

use crate::ancilla_capacity::{AncillaCapacity, AncillaCapacityError};
use crate::exact_channel::ExactKrausChannel;
use crate::exact_entropy::RationalSpectrum;
use crate::exact_instrument::ExactDensityState;
use crate::finite_chsh_correlations::{deterministic_family, PairwiseBox};
use crate::instruments::ExactPovm;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::involution::hs_inner;
use core_category_theory::finite_report_query::{ReportQueryDecision, ReportQueryProblem};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_convex_finite_hull::MembershipCertificate;
use std::collections::BTreeSet;

pub type ReportDecision = ReportQueryDecision<usize, Vec<Rational>, Rational>;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CarrierTestError {
    #[error("the finite preparation family must be nonempty")]
    EmptyPreparations,
    #[error("state, report, channel or future measurement dimensions differ")]
    Dimension,
    #[error("exact owner refused: {0}")]
    Owner(String),
    #[error("probability trace was nonreal")]
    NonReal,
    #[error(transparent)]
    Capacity(#[from] AncillaCapacityError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReportTest {
    pub reports: Vec<Vec<Rational>>,
    pub answers: Vec<Rational>,
    pub decision: ReportDecision,
}

/// Does the present POVM probability profile determine the probability of
/// outcome zero of the supplied future POVM after the supplied CPTP channel?
/// These are ensemble probability reports, not single-shot outcome labels.
pub fn report_sufficiency(
    states: &[ExactDensityState],
    report: &ExactPovm,
    channel: &ExactKrausChannel,
    future: &ExactPovm,
) -> Result<ReportTest, CarrierTestError> {
    validate_sufficiency_inputs(states, report, channel, future)?;
    let (reports, answers) = evaluate_reports_and_answers(states, report, channel, future)?;
    let decision = decide_report_query(states.len(), &reports, &answers)?;
    Ok(ReportTest {
        reports,
        answers,
        decision,
    })
}

fn validate_sufficiency_inputs(
    states: &[ExactDensityState],
    report: &ExactPovm,
    channel: &ExactKrausChannel,
    future: &ExactPovm,
) -> Result<(), CarrierTestError> {
    if states.is_empty() {
        return Err(CarrierTestError::EmptyPreparations);
    }
    if [
        report.dim() != channel.dim_in(),
        future.dim() != channel.dim_out(),
        states.iter().any(|s| s.dimension() != report.dim()),
    ]
    .into_iter()
    .any(|b| b)
    {
        return Err(CarrierTestError::Dimension);
    }
    Ok(())
}

fn hs_real_pair(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> Result<Rational, CarrierTestError> {
    let z = hs_inner(a, b).map_err(|e| CarrierTestError::Owner(e.to_string()))?;
    if !z.is_real() {
        return Err(CarrierTestError::NonReal);
    }
    Ok(z.re)
}

fn evaluate_reports_and_answers(
    states: &[ExactDensityState],
    report: &ExactPovm,
    channel: &ExactKrausChannel,
    future: &ExactPovm,
) -> Result<(Vec<Vec<Rational>>, Vec<Rational>), CarrierTestError> {
    let mut reports = Vec::new();
    let mut answers = Vec::new();
    let target = future
        .effects()
        .first()
        .ok_or(CarrierTestError::Dimension)?;
    for state in states {
        reports.push(
            report
                .effects()
                .iter()
                .map(|e| hs_real_pair(e.as_matrix(), state.matrix()))
                .collect::<Result<Vec<_>, _>>()?,
        );
        let image = channel
            .apply(state.matrix())
            .map_err(|e| CarrierTestError::Owner(e.to_string()))?;
        answers.push(hs_real_pair(target.as_matrix(), &image)?);
    }
    Ok((reports, answers))
}

fn decide_report_query(
    num_states: usize,
    reports: &[Vec<Rational>],
    answers: &[Rational],
) -> Result<ReportDecision, CarrierTestError> {
    let sources: Vec<_> = (0..num_states).collect();
    let report_values: Vec<_> = reports
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let answer_values: Vec<_> = answers
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let report_rows: Vec<_> = reports.iter().cloned().enumerate().collect();
    let answer_rows: Vec<_> = answers.iter().cloned().enumerate().collect();
    let problem = ReportQueryProblem::new(
        &sources,
        &report_values,
        &answer_values,
        &report_rows,
        &answer_rows,
    )
    .map_err(|e| CarrierTestError::Owner(e.to_string()))?;
    let decision = problem.decide();
    problem
        .verify_decision(&decision)
        .map_err(|e| CarrierTestError::Owner(format!("{e:?}")))?;
    Ok(decision)
}

/// Replays a full convex-hull certificate. Neither a single CHSH orientation
/// nor a support-only parity check decides all positive joint extensions.
pub fn positive_joint_extension(
    box_: &PairwiseBox,
) -> Result<MembershipCertificate, CarrierTestError> {
    let certificate = box_
        .joint_extension()
        .map_err(|e| CarrierTestError::Owner(e.to_string()))?;
    let family = deterministic_family();
    match &certificate {
        MembershipCertificate::Member(c) => c.verify(&family, box_.coordinates()),
        MembershipCertificate::Separated(c) => c.verify(&family, box_.coordinates()).map(|_| ()),
    }
    .map_err(|e| CarrierTestError::Owner(e.to_string()))?;
    Ok(certificate)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PurificationTest {
    pub capacity: AncillaCapacity,
    pub central_purity_ceiling: Rational,
    pub central_distance_floor: Rational,
    pub central_obstruction: bool,
}

/// Rational spectral packets are declarations, not certificates for separately
/// supplied matrices. The central bounds apply to every available ancilla in
/// the standard block tensor model; the capacity additionally uses the listed
/// ancilla block sizes. A zero central obstruction does not prove purification.
pub fn sector_purification(
    sectors: &[(Rational, RationalSpectrum)],
    ancilla_blocks: &[usize],
    max_dimension: usize,
) -> Result<PurificationTest, CarrierTestError> {
    // AncillaCapacity validates ordinary weights; raw BigRational::new_raw can
    // bypass normalization, so reject malformed representations before arithmetic.
    if sectors.iter().any(|(p, _)| p.denom() <= &0.into()) {
        return Err(CarrierTestError::Owner("invalid weight denominator".into()));
    }
    let capacity = AncillaCapacity::from_sectors(sectors, ancilla_blocks, max_dimension)?;
    let central_purity_ceiling = sectors.iter().map(|(p, _)| p * p).sum();
    let maximum = sectors
        .iter()
        .map(|(p, _)| p)
        .max()
        .ok_or(AncillaCapacityError::EmptySystem)?;
    let central_distance_floor = ri(1) - maximum;
    let central_obstruction = central_distance_floor > ri(0);
    Ok(PurificationTest {
        capacity,
        central_purity_ceiling,
        central_distance_floor,
        central_obstruction,
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/carrier_tests.rs
// Claim: urn:core:crates_rs:core-quantum-physics:carrier-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
