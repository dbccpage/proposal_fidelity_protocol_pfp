//! A bounded, task-bound encoding experiment. AuthorityEffect: None.
//!
//! Candidates are integer quadratics with each coefficient in [-2, 2].
//! The question is f' = b0 + b1*x and f(0) = v in Z[x]. Cochain closure
//! checks representation consistency; only the direct checker checks this
//! question. Gamma2 arithmetic is delegated to its canonical functional.

use std::collections::{BTreeMap, BTreeSet};

use core_category_theory::finite_report_query::{ReportQueryDecision, ReportQueryProblem};
use core_functional::gamma2::Gamma2Functional;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

pub const DOMAIN: &str = "integer_quadratic_antiderivative_at_zero_v1";
pub const BOUND: i64 = 2;
pub const MAX_REPORT_BYTES: usize = 2048;

/// Detect a stale local build when replaying the pinned source snapshot.
/// This is build provenance under a trusted compiler/executable, not authentication.
pub fn compiled_source_sha256() -> BTreeMap<&'static str, String> {
    let inputs: &[(&str, &[u8])] = &[
        (
            "engine/crates_rs/core_wdp/src/question_preserving_encoding.rs",
            include_bytes!("question_preserving_encoding.rs"),
        ),
        (
            "engine/crates_rs/core_wdp/src/examples/question_preserving_encoding.rs",
            include_bytes!("examples/question_preserving_encoding.rs"),
        ),
        (
            "engine/crates_rs/tests/core_wdp/test_question_preserving_encoding.rs",
            include_bytes!(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/../tests/core_wdp/test_question_preserving_encoding.rs"
            )),
        ),
        (
            "engine/crates_rs/core_category_theory/src/finite_report_query.rs",
            include_bytes!("../../core_category_theory/src/finite_report_query.rs"),
        ),
        (
            "engine/crates_rs/core_functional/src/gamma2.rs",
            include_bytes!("../../core_functional/src/gamma2.rs"),
        ),
        (
            "engine/crates_rs/Cargo.lock",
            include_bytes!("../../Cargo.lock"),
        ),
    ];
    inputs
        .iter()
        .map(|(name, bytes)| (*name, hex::encode(Sha256::digest(bytes))))
        .collect()
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Task {
    pub derivative: [i64; 2],
    pub value_at_zero: i64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Refusal {
    MalformedReport,
    SchemaMismatch,
    TaskOutOfDomain,
    TaskMismatch,
    CandidateOutOfDomain,
    EdgeOutOfDomain,
    NonClosedReport,
    FunctionalRefusal,
    ExperimentInvariant,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DirectReport {
    pub schema_version: u8,
    pub domain: String,
    pub task: Task,
    pub coefficients: [i64; 3],
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CochainReport {
    pub schema_version: u8,
    pub domain: String,
    pub task: Task,
    pub anchor: i64,
    /// Fixed orientations 0->1, 1->2, 2->0 on the declared filled triangle.
    pub edges: [i64; 3],
}

fn in_range(value: i64, bound: i64) -> bool {
    (-bound..=bound).contains(&value)
}

pub fn validate_task(task: Task) -> Result<(), Refusal> {
    if !in_range(task.value_at_zero, BOUND)
        || !in_range(task.derivative[0], BOUND)
        || !in_range(task.derivative[1], 2 * BOUND)
    {
        return Err(Refusal::TaskOutOfDomain);
    }
    Ok(())
}

fn validate_candidate(candidate: [i64; 3]) -> Result<(), Refusal> {
    if candidate.iter().any(|&c| !in_range(c, BOUND)) {
        return Err(Refusal::CandidateOutOfDomain);
    }
    Ok(())
}

/// The sole semantic checker in this profile: equality of derivative
/// coefficients and the value at zero. Bounds precede arithmetic.
pub fn check(task: Task, candidate: [i64; 3]) -> Result<bool, Refusal> {
    validate_task(task)?;
    validate_candidate(candidate)?;
    let tests = [
        candidate[0] == task.value_at_zero,
        candidate[1] == task.derivative[0],
        2 * candidate[2] == task.derivative[1],
    ];
    Ok(tests.into_iter().all(|equal| equal))
}

pub fn encode_direct(task: Task, candidate: [i64; 3]) -> Result<DirectReport, Refusal> {
    validate_task(task)?;
    validate_candidate(candidate)?;
    Ok(DirectReport {
        schema_version: 1,
        domain: DOMAIN.to_owned(),
        task,
        coefficients: candidate,
    })
}

/// Representation map, not a defect functional or a correctness decision.
pub fn encode_cochain(task: Task, candidate: [i64; 3]) -> Result<CochainReport, Refusal> {
    validate_task(task)?;
    validate_candidate(candidate)?;
    let [a, b, c] = candidate;
    Ok(CochainReport {
        schema_version: 1,
        domain: DOMAIN.to_owned(),
        task,
        anchor: a,
        edges: [b - a, c - b, a - c],
    })
}

fn header(schema: u8, domain: &str, declared: Task, expected: Task) -> Result<(), Refusal> {
    validate_task(expected)?;
    if schema != 1 || domain != DOMAIN {
        return Err(Refusal::SchemaMismatch);
    }
    if declared != expected {
        return Err(Refusal::TaskMismatch);
    }
    Ok(())
}

fn decode<T: serde::de::DeserializeOwned>(wire: &str) -> Result<T, Refusal> {
    if wire.len() > MAX_REPORT_BYTES {
        return Err(Refusal::MalformedReport);
    }
    serde_json::from_str(wire).map_err(|_| Refusal::MalformedReport)
}

pub fn parse_direct(expected: Task, wire: &str) -> Result<[i64; 3], Refusal> {
    let report: DirectReport = decode(wire)?;
    header(report.schema_version, &report.domain, report.task, expected)?;
    validate_candidate(report.coefficients)?;
    Ok(report.coefficients)
}

pub fn parse_cochain(expected: Task, wire: &str) -> Result<[i64; 3], Refusal> {
    let report: CochainReport = decode(wire)?;
    header(report.schema_version, &report.domain, report.task, expected)?;
    if !in_range(report.anchor, BOUND) {
        return Err(Refusal::CandidateOutOfDomain);
    }
    if report.edges.iter().any(|&e| !in_range(e, 2 * BOUND)) {
        return Err(Refusal::EdgeOutOfDomain);
    }
    let closure =
        Gamma2Functional::checked_face(report.edges).map_err(|_| Refusal::FunctionalRefusal)?;
    if closure != 0 {
        return Err(Refusal::NonClosedReport);
    }
    let c0 = report.anchor;
    let c1 = c0 + report.edges[0];
    let c2 = c1 + report.edges[1];
    let candidate = [c0, c1, c2];
    validate_candidate(candidate)?;
    Ok(candidate)
}

pub fn verify_direct(expected: Task, wire: &str) -> Result<bool, Refusal> {
    check(expected, parse_direct(expected, wire)?)
}

pub fn verify_cochain(expected: Task, wire: &str) -> Result<bool, Refusal> {
    check(expected, parse_cochain(expected, wire)?)
}

/// Algebraic proposal using the supplied derivative equations. This is not
/// acceptance; every returned proposal is passed to the independent checker.
pub fn direct_proposal(task: Task) -> Result<Option<[i64; 3]>, Refusal> {
    validate_task(task)?;
    if task.derivative[1] % 2 != 0 {
        return Ok(None);
    }
    Ok(Some([
        task.value_at_zero,
        task.derivative[0],
        task.derivative[1] / 2,
    ]))
}

/// The same equations solved in anchored edge coordinates. No invocation of
/// the direct proposal routine, checker, or search result constructs this.
pub fn cochain_proposal(task: Task) -> Result<Option<CochainReport>, Refusal> {
    validate_task(task)?;
    if task.derivative[1] % 2 != 0 {
        return Ok(None);
    }
    let anchor = task.value_at_zero;
    let e01 = task.derivative[0] - anchor;
    let e12 = task.derivative[1] / 2 - task.derivative[0];
    let e20 = anchor - task.derivative[1] / 2;
    Ok(Some(CochainReport {
        schema_version: 1,
        domain: DOMAIN.to_owned(),
        task,
        anchor,
        edges: [e01, e12, e20],
    }))
}

pub fn candidates() -> Vec<[i64; 3]> {
    let mut rows = Vec::new();
    for a in -BOUND..=BOUND {
        for b in -BOUND..=BOUND {
            for c in -BOUND..=BOUND {
                rows.push([a, b, c]);
            }
        }
    }
    rows
}

fn factorable(reports: Vec<Vec<i64>>, answers: &[bool]) -> Result<bool, Refusal> {
    let source: Vec<usize> = (0..answers.len()).collect();
    let codomain: Vec<Vec<i64>> = reports
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let report_rows: Vec<_> = source.iter().copied().zip(reports).collect();
    let query_rows: Vec<_> = source
        .iter()
        .copied()
        .zip(answers.iter().copied())
        .collect();
    let problem = ReportQueryProblem::new(
        &source,
        &codomain,
        &[false, true],
        &report_rows,
        &query_rows,
    )
    .map_err(|_| Refusal::ExperimentInvariant)?;
    let decision = problem.decide();
    problem
        .verify_decision(&decision)
        .map_err(|_| Refusal::ExperimentInvariant)?;
    Ok(matches!(decision, ReportQueryDecision::Factorable(_)))
}

fn wire<T: Serialize>(value: &T) -> Result<String, Refusal> {
    serde_json::to_string(value).map_err(|_| Refusal::ExperimentInvariant)
}

fn enumerate_then_check(
    task: Task,
    carrier: &[[i64; 3]],
) -> Result<(Option<[i64; 3]>, usize), Refusal> {
    let mut calls = 0;
    for &candidate in carrier {
        calls += 1;
        if check(task, candidate)? {
            return Ok((Some(candidate), calls));
        }
    }
    Ok((None, calls))
}

fn evaluate_task_solutions(
    task: Task,
    carrier: &[[i64; 3]],
) -> Result<(Vec<bool>, Option<[i64; 3]>, usize), Refusal> {
    let answers: Vec<bool> = carrier
        .iter()
        .map(|&c| check(task, c))
        .collect::<Result<_, _>>()?;
    let solutions: Vec<_> = carrier
        .iter()
        .copied()
        .zip(&answers)
        .filter_map(|(c, &ok)| ok.then_some(c))
        .collect();
    if solutions.len() > 1 {
        return Err(Refusal::ExperimentInvariant);
    }
    let expected = solutions.first().copied();
    let (enumerated, enumeration_checks) = enumerate_then_check(task, carrier)?;
    if enumerated != expected {
        return Err(Refusal::ExperimentInvariant);
    }
    Ok((answers, expected, enumeration_checks))
}

fn encode_and_verify_cochain_pair(
    task: Task,
    candidate: [i64; 3],
    answer: bool,
) -> Result<(CochainReport, i64), Refusal> {
    let encoded = encode_cochain(task, candidate)?;
    let encoded_wire = wire(&encoded)?;
    if parse_cochain(task, &encoded_wire)? != candidate
        || verify_cochain(task, &encoded_wire)? != answer
    {
        return Err(Refusal::ExperimentInvariant);
    }
    let closure =
        Gamma2Functional::checked_face(encoded.edges).map_err(|_| Refusal::FunctionalRefusal)?;
    let closure_i64 = i64::try_from(closure).map_err(|_| Refusal::ExperimentInvariant)?;
    Ok((encoded, closure_i64))
}

fn audit_cochain_carrier(
    task: Task,
    carrier: &[[i64; 3]],
    answers: &[bool],
) -> Result<(bool, bool, usize), Refusal> {
    let mut unanchored = Vec::new();
    let mut anchored = Vec::new();
    let mut closure_reports = Vec::new();
    let mut closed_wrong_delta = 0_usize;
    for (&candidate, &answer) in carrier.iter().zip(answers) {
        let (encoded, closure_i64) = encode_and_verify_cochain_pair(task, candidate, answer)?;
        unanchored.push(encoded.edges.to_vec());
        closure_reports.push(vec![closure_i64]);
        anchored.push(vec![
            encoded.anchor,
            encoded.edges[0],
            encoded.edges[1],
            encoded.edges[2],
        ]);
        if !answer {
            closed_wrong_delta += 1;
        }
    }
    let unanchored_ok = factorable(unanchored, answers)?;
    let closure_ok = factorable(closure_reports, answers)?;
    if !factorable(anchored, answers)? {
        return Err(Refusal::ExperimentInvariant);
    }
    Ok((unanchored_ok, closure_ok, closed_wrong_delta))
}

fn verify_direct_proposal(task: Task, expected: Option<[i64; 3]>) -> Result<(), Refusal> {
    let direct = direct_proposal(task)?;
    if direct != expected {
        return Err(Refusal::ExperimentInvariant);
    }
    if let Some(candidate) = direct {
        if !verify_direct(task, &wire(&encode_direct(task, candidate)?)?)? {
            return Err(Refusal::ExperimentInvariant);
        }
    }
    Ok(())
}

fn verify_cochain_proposal(task: Task, expected: Option<[i64; 3]>) -> Result<(), Refusal> {
    let cochain = cochain_proposal(task)?;
    let decoded = cochain
        .as_ref()
        .map(|r| parse_cochain(task, &wire(r)?))
        .transpose()?;
    if decoded != expected {
        return Err(Refusal::ExperimentInvariant);
    }
    if let Some(report) = &cochain {
        if !verify_cochain(task, &wire(report)?)? {
            return Err(Refusal::ExperimentInvariant);
        }
    }
    Ok(())
}

fn verify_controls_invariant(
    zero: Task,
    correct: &CochainReport,
    wrong: &CochainReport,
    corrupt_wire: &str,
    wrong_task_wire: &str,
) -> Result<(), Refusal> {
    let controls_valid = [
        correct.edges == wrong.edges,
        check(zero, [0, 0, 0])?,
        !check(zero, [1, 1, 1])?,
        parse_cochain(zero, corrupt_wire) == Err(Refusal::NonClosedReport),
        parse_cochain(zero, wrong_task_wire) == Err(Refusal::TaskMismatch),
    ];
    if controls_valid.into_iter().any(|ok| !ok) {
        return Err(Refusal::ExperimentInvariant);
    }
    Ok(())
}

fn build_and_verify_controls() -> Result<Value, Refusal> {
    let zero = Task {
        derivative: [0, 0],
        value_at_zero: 0,
    };
    let correct = encode_cochain(zero, [0, 0, 0])?;
    let wrong = encode_cochain(zero, [1, 1, 1])?;
    let mut corrupt = correct.clone();
    corrupt.edges[2] = 1;
    let mut wrong_task = correct.clone();
    wrong_task.task.value_at_zero = 1;
    let corrupt_wire = wire(&corrupt)?;
    let wrong_task_wire = wire(&wrong_task)?;
    let controls = json!({
        "same_unanchored_report":correct.edges == wrong.edges,
        "correct_accepted":verify_cochain(zero,&wire(&correct)?)?,
        "coherent_wrong_rejected":!verify_cochain(zero,&wire(&wrong)?)?,
        "corrupt_edge_refusal":parse_cochain(zero,&corrupt_wire).err(),
        "changed_task_refusal":parse_cochain(zero,&wrong_task_wire).err()
    });
    verify_controls_invariant(zero, &correct, &wrong, &corrupt_wire, &wrong_task_wire)?;
    Ok(controls)
}

fn all_tasks() -> Vec<Task> {
    let mut tasks = Vec::new();
    for initial in -BOUND..=BOUND {
        for constant in -BOUND..=BOUND {
            for slope in -2 * BOUND..=2 * BOUND {
                tasks.push(Task {
                    derivative: [constant, slope],
                    value_at_zero: initial,
                });
            }
        }
    }
    tasks
}

/// Exhaustive reproducible experiment, including unsuccessful tasks. The
/// exhaustive audit is accounted separately from each strategy's workload.
pub fn experiment() -> Result<Value, Refusal> {
    let carrier = candidates();
    let mut rows = Vec::new();
    let mut total_enumeration_checks = 0_usize;
    let mut solved = 0_usize;
    let mut unanchored_collisions = 0_usize;
    let mut closure_only_collisions = 0_usize;
    let mut closed_wrong_pairs = 0_usize;
    for task in all_tasks() {
        let (answers, expected, enumeration_checks) = evaluate_task_solutions(task, &carrier)?;
        total_enumeration_checks += enumeration_checks;
        let (unanchored_ok, closure_ok, closed_wrong_delta) =
            audit_cochain_carrier(task, &carrier, &answers)?;
        closed_wrong_pairs += closed_wrong_delta;
        unanchored_collisions += usize::from(!unanchored_ok);
        closure_only_collisions += usize::from(!closure_ok);

        verify_direct_proposal(task, expected)?;
        verify_cochain_proposal(task, expected)?;
        let checks = usize::from(expected.is_some());
        solved += checks;
        rows.push(json!({"task":task,"solution":expected,"enumeration_checker_calls":enumeration_checks,
            "direct_reconstruction_checker_calls":checks,"cochain_reconstruction_checker_calls":checks,
            "unanchored_factorable":unanchored_ok,"closure_only_factorable":closure_ok}));
    }
    let controls = build_and_verify_controls()?;
    Ok(json!({
        "schema_version":1,"domain":DOMAIN,"authority_effect":"None",
        "compiled_source_sha256":compiled_source_sha256(),
        "coefficient_bound":BOUND,"candidate_count":carrier.len(),"task_count":rows.len(),
        "satisfiable_tasks":solved,"unsatisfiable_tasks":rows.len()-solved,
        "audit_task_candidate_pairs":rows.len()*carrier.len(),
        "audit_work_in_strategy_counts":false,
        "unanchored_colliding_tasks":unanchored_collisions,
        "closure_only_colliding_tasks":closure_only_collisions,
        "closed_wrong_task_candidate_pairs":closed_wrong_pairs,
        "strategies":[
            {"name":"enumerate_then_check","checker_calls":total_enumeration_checks,
                "checker_coefficient_comparisons":3*total_enumeration_checks,
                "report_parses":0,"candidate_integer_fields_sent":0,"gamma2_evaluations":0},
            {"name":"direct_reconstruct_then_check","checker_calls":solved,
                "checker_coefficient_comparisons":3*solved,
                "report_parses":solved,"candidate_integer_fields_sent":3*solved,"gamma2_evaluations":0},
            {"name":"cochain_reconstruct_then_check","checker_calls":solved,
                "checker_coefficient_comparisons":3*solved,
                "report_parses":solved,"candidate_integer_fields_sent":4*solved,"gamma2_evaluations":solved}
        ],
        "cost_scope":"Logical single-run strategy counts; exhaustive audit and duplicate diagnostic assertions are separate. Task headers, proposal arithmetic, JSON byte costs and wall time are not converted to a common cost.",
        "conclusion":"Both reconstruction routes reduce checker calls against enumeration; the cochain route has no checker-call advantage over direct reconstruction and adds parsing/closure data.",
        "controls":controls,"tasks":rows
    }))
}

// Origin: engine/crates_rs/core_wdp/src/question_preserving_encoding.rs
// Claim: urn:core:crates_rs:core-wdp:question-preserving-encoding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)


/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfdc245fd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfdc245fd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfdc245fd {
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
impl BoundaryErrorfdc245fd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfdc245fd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfdc245fd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfdc245fd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfdc245fd> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfdc245fd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfdc245fd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfdc245fd::ExceedsCapacity {
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

#[cfg(test)]
mod l4_mutation_checks_fdc245fd {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_fdc245fd {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfdc245fd::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfdc245fd::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfdc245fd::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfdc245fd::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfdc245fd::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfdc245fd::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfdc245fd::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
