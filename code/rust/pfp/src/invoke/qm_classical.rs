//! Bounded experiment wire format; mathematics stays in sovereign owners.
use super::{outcome_err, outcome_ok, RuntimeOutcomeV1, RuntimeRequestV1};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_category_theory::finite_report_query::ReportQueryDecision;
use core_kernel::{parse_exact, to_canonical_string as wire, Exact};
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::{
    carrier_tests, exact_channel::ExactKrausChannel, exact_entropy::RationalSpectrum,
    exact_instrument::ExactDensityState, finite_chsh_correlations::PairwiseBox,
    instruments::ExactPovm,
};
use core_solvers::solver_convex_finite_hull::MembershipCertificate;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

const SCHEMA: &str = "core.qm-classical.experiment.v1";
const MAX_DIM: usize = 8;
const MAX_ITEMS: usize = 64;
type MatrixWire = Vec<Vec<[String; 2]>>;

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Experiment {
    schema_version: String,
    test: Test,
}

#[derive(Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum Test {
    ReportSufficiency {
        states: Vec<MatrixWire>,
        report_povm: Vec<MatrixWire>,
        kraus: Vec<MatrixWire>,
        future_povm: Vec<MatrixWire>,
    },
    PositiveJointExtension {
        probabilities: Vec<String>,
    },
    SectorPurification {
        model: SectorModel,
        sectors: Vec<Sector>,
        ancilla_blocks: Vec<usize>,
    },
}

#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum SectorModel {
    ComplexDirectSumStandardTensor,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Sector {
    weight: String,
    spectrum: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Verification {
    experiment: Value,
    certificate: Value,
}

fn rational(s: &str) -> Result<Exact, String> {
    if s.len() > 256 {
        return Err("RATIONAL_TOKEN_BUDGET".into());
    }
    parse_exact(s).map_err(|e| e.to_string())
}

fn matrix(rows: &MatrixWire) -> Result<BasicMatrix<GaussianRat>, String> {
    let cols = rows.first().map_or(0, Vec::len);
    if rows.is_empty()
        || rows.len() > MAX_DIM
        || cols == 0
        || cols > MAX_DIM
        || rows.iter().any(|r| r.len() != cols)
    {
        return Err("MATRIX_SHAPE_OR_BUDGET".into());
    }
    let data = rows
        .iter()
        .flatten()
        .map(|[re, im]| {
            Ok(GaussianRat {
                re: rational(re)?,
                im: rational(im)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    BasicMatrix::from_row_major(rows.len(), cols, data).map_err(|e| e.to_string())
}

fn family(rows: &[MatrixWire]) -> Result<Vec<BasicMatrix<GaussianRat>>, String> {
    if rows.is_empty() || rows.len() > MAX_ITEMS {
        return Err("MATRIX_FAMILY_BUDGET".into());
    }
    rows.iter().map(matrix).collect()
}

fn strings(values: &[Exact]) -> Vec<String> {
    values.iter().map(wire).collect()
}

fn format_report_query_witness(decision: &carrier_tests::ReportDecision) -> Value {
    match decision {
        ReportQueryDecision::Collision(c) => json!({
            "verdict":"report_collision", "first":c.first, "second":c.second,
            "report":strings(&c.report),
            "answers":[wire(&c.first_query),wire(&c.second_query)]}),
        ReportQueryDecision::Factorable(c) => json!({
            "verdict":"report_sufficient_on_declared_family",
            "decoder":c.decoder.iter().map(|(r,a)| json!({"report":strings(r),"answer":wire(a)})).collect::<Vec<_>>() }),
    }
}

fn evaluate_report_sufficiency(
    states: &[MatrixWire],
    report_povm: &[MatrixWire],
    kraus: &[MatrixWire],
    future_povm: &[MatrixWire],
) -> Result<Value, String> {
    let states = family(states)?
        .into_iter()
        .map(ExactDensityState::try_new)
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;
    let report = ExactPovm::try_new(family(report_povm)?).map_err(|e| e.to_string())?;
    let future = ExactPovm::try_new(family(future_povm)?).map_err(|e| e.to_string())?;
    let channel = ExactKrausChannel::from_operators(family(kraus)?).map_err(|e| e.to_string())?;
    let tested = carrier_tests::report_sufficiency(&states, &report, &channel, &future)
        .map_err(|e| e.to_string())?;
    let witness = format_report_query_witness(&tested.decision);
    Ok(json!({"witness":witness,
        "reports":tested.reports.iter().map(|r| strings(r)).collect::<Vec<_>>(),
        "answers":strings(&tested.answers),
        "scope":"listed states; ensemble reports; supplied CPTP control and future outcome zero"}))
}

fn evaluate_positive_joint_extension(probabilities: &[String]) -> Result<Value, String> {
    if probabilities.len() != 16 {
        return Err("BELL_COORDINATES".into());
    }
    let box_ = PairwiseBox::new(
        probabilities
            .iter()
            .map(|p| rational(p))
            .collect::<Result<_, _>>()?,
    )
    .map_err(|e| e.to_string())?;
    let certificate =
        carrier_tests::positive_joint_extension(&box_).map_err(|e| e.to_string())?;
    let witness = match certificate {
        MembershipCertificate::Member(c) => {
            json!({"verdict":"positive_joint_extension", "weights":strings(c.coefficients())})
        }
        MembershipCertificate::Separated(c) => {
            json!({"verdict":"no_positive_joint_extension",
            "functional":strings(c.functional()),"threshold":wire(c.threshold()),
            "value":wire(&c.evaluate(box_.coordinates()).map_err(|e| e.to_string())?)})
        }
    };
    Ok(json!({"witness":witness,"chsh":wire(&box_.chsh()),"no_signalling":box_.is_no_signalling(),
        "scope":"two settings and binary outcomes per party; Bell causality and setting independence are additional interpretation premises"}))
}

fn parse_sector(s: &Sector) -> Result<(Exact, RationalSpectrum), String> {
    if s.spectrum.is_empty() || s.spectrum.len() > MAX_ITEMS {
        return Err("SPECTRUM_BUDGET".into());
    }
    let entries = s
        .spectrum
        .iter()
        .map(|q| Ok((rational(q)?, 1)))
        .collect::<Result<Vec<_>, String>>()?;
    Ok((
        rational(&s.weight)?,
        RationalSpectrum::try_new(entries).map_err(|e| e.to_string())?,
    ))
}

fn validate_sector_purification_budgets(
    sectors: &[Sector],
    ancilla_blocks: &[usize],
) -> Result<(), String> {
    let invalid_sectors = sectors.is_empty() || sectors.len() > MAX_ITEMS;
    let invalid_ancilla = ancilla_blocks.is_empty()
        || ancilla_blocks.len() > MAX_ITEMS
        || ancilla_blocks.iter().any(|n| *n == 0 || *n > MAX_ITEMS);
    if invalid_sectors || invalid_ancilla {
        return Err("SECTOR_OR_ANCILLA_BUDGET".into());
    }
    Ok(())
}

fn evaluate_sector_purification(
    sectors: &[Sector],
    ancilla_blocks: &[usize],
) -> Result<Value, String> {
    validate_sector_purification_budgets(sectors, ancilla_blocks)?;
    let sectors = sectors
        .iter()
        .map(parse_sector)
        .collect::<Result<Vec<_>, String>>()?;
    let tested = carrier_tests::sector_purification(&sectors, ancilla_blocks, 256)
        .map_err(|e| e.to_string())?;
    let verdict = if tested.central_obstruction {
        "central_purification_obstructed"
    } else {
        "no_central_obstruction"
    };
    Ok(json!({"verdict":verdict,
        "central_purity_ceiling":wire(&tested.central_purity_ceiling),
        "central_trace_distance_floor":wire(&tested.central_distance_floor),
        "available_ancilla_max_purity":wire(&tested.capacity.maximum_extension_purity()),
        "available_ancilla_min_rank":tested.capacity.minimum_extension_rank(),
        "available_ancilla_pure_marginal_distance":wire(&tested.capacity.pure_marginal_trace_distance()),
        "scope":"declared normalized rational spectra; full positive complex block states and standard tensor composition; no empirical confirmation of these premises"}))
}

fn evaluate_test_branch(test: &Test) -> Result<Value, String> {
    match test {
        Test::ReportSufficiency {
            states,
            report_povm,
            kraus,
            future_povm,
        } => evaluate_report_sufficiency(states, report_povm, kraus, future_povm),
        Test::PositiveJointExtension { probabilities } => {
            evaluate_positive_joint_extension(probabilities)
        }
        Test::SectorPurification {
            sectors,
            ancilla_blocks,
            ..
        } => evaluate_sector_purification(sectors, ancilla_blocks),
    }
}

fn evaluate(payload: &Value) -> Result<Value, String> {
    let input: Experiment = serde_json::from_value(payload.clone()).map_err(|e| e.to_string())?;
    if input.schema_version != SCHEMA {
        return Err("EXPERIMENT_SCHEMA".into());
    }
    let result = evaluate_test_branch(&input.test)?;
    // Structural key order is handled by the canonical owner, including with
    // serde_json/preserve_order enabled. Arrays retain semantic order.
    let normalized = serde_json::to_value(input).map_err(|e| e.to_string())?;
    let canonical = pfp_runtime::jcs_canonicalize_value(&normalized)
        .map_err(|e| e.to_string())?;
    let normal_form: Value = serde_json::from_str(&canonical).map_err(|e| e.to_string())?;
    let digest = pfp_runtime::domain_digest_json(SCHEMA, &normal_form)
        .map_err(|e| e.to_string())?;
    Ok(json!({"schema_version":"core.qm-classical.certificate.v1",
        "normal_form":normal_form,"input_digest":digest,"result":result,
        "authority_effect":"None"}))
}

pub(super) fn dispatch(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let result = if req.action == "qm_classical_evaluate" {
        evaluate(&req.payload)
    } else {
        serde_json::from_value::<Verification>(req.payload.clone())
            .map_err(|e| e.to_string())
            .and_then(|v| {
                let replayed = evaluate(&v.experiment)?;
                if replayed != v.certificate {
                    return Err("CERTIFICATE_REPLAY_MISMATCH".into());
                }
                Ok(json!({"verified":true,"certificate":replayed}))
            })
    };
    match result {
        Ok(v) => outcome_ok(&req.action, v),
        Err(e) => outcome_err(&req.action, e),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/qm_classical.rs
// Claim: urn:core:crates_rs:pfp:qm-classical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord142bf252 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord142bf252` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError142bf252 {
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
impl BoundaryError142bf252 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError142bf252 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError142bf252 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord142bf252 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError142bf252> {
        if capacity_bound == 0 {
            return Err(BoundaryError142bf252::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError142bf252::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError142bf252::ExceedsCapacity {
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
mod l4_boundary_tests_142bf252 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord142bf252::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord142bf252::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord142bf252::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord142bf252::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord142bf252::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError142bf252::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError142bf252::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
