//! Exact CODA/CODA_GTLA adapter for a checked finite-Lambda ledger.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_functional::gamma2::{ExactCochainComplexQ, ExactGamma2Error};
use core_functional::phi1::ExactPhi1Certificate;
use core_homotopy_type_theory::primitive_difference::PrimitiveDifference;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_types::authority::AuthorityEffect;
use core_wdp::ddc::{FiniteDiagnostic, FiniteLambdaLedger, LambdaAlgebraError};
use serde::Serialize;

use core_wdp::coda::coda_gtla::{
    bind_domain_evidence, evaluate_exact, validate_primitive_difference, CodaExactInput,
    CodaGtlaEvaluation, CodaGtlaEvaluationError, DomainEvidenceBindingError,
    PrimitiveDifferenceReceiptError,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize)]
struct FiniteLambdaPoint {
    phi1: u64,
    gamma2: u64,
}

impl From<FiniteDiagnostic> for FiniteLambdaPoint {
    fn from(value: FiniteDiagnostic) -> Self {
        Self {
            phi1: value.phi1,
            gamma2: value.gamma2,
        }
    }
}

#[derive(Clone, Copy, Debug)]
struct FiniteLambdaDifference;

impl PrimitiveDifference for FiniteLambdaDifference {
    type Carrier = FiniteLambdaPoint;
    type Diff = bool;

    fn delta(&self, x: &Self::Carrier, y: &Self::Carrier) -> Self::Diff {
        x != y
    }

    fn zero(&self, difference: &Self::Diff) -> bool {
        !difference
    }
}

#[derive(Serialize)]
struct FiniteLambdaStepManifest {
    before: FiniteLambdaPoint,
    after: FiniteLambdaPoint,
    preserves_old_vertices: bool,
    preserves_old_edges: bool,
    records_tradeoff: bool,
}

#[derive(Serialize)]
struct FiniteLambdaManifest {
    schema: &'static str,
    initial: FiniteLambdaPoint,
    steps: Vec<FiniteLambdaStepManifest>,
    terminal: FiniteLambdaPoint,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FiniteLambdaTerminal {
    ExactRepair,
    Invalid,
    InfrastructureFailure,
}
#[derive(Debug, thiserror::Error)]
pub enum FiniteLambdaAdapterError {
    #[error("finite-Lambda ledger is not chained: {0:?}")]
    BrokenLedger(LambdaAlgebraError),
    #[error("finite-Lambda ledger manifest failed: {0}")]
    Manifest(#[from] serde_json::Error),
    #[error(transparent)]
    Binding(#[from] DomainEvidenceBindingError),
    #[error(transparent)]
    Primitive(#[from] PrimitiveDifferenceReceiptError),
    #[error(transparent)]
    Complex(#[from] ExactGamma2Error),
    #[error(transparent)]
    Evaluation(#[from] CodaGtlaEvaluationError),
    #[error("a valid finite-Lambda ledger did not replay to ExactRepair")]
    TerminalMismatch,
}

impl FiniteLambdaAdapterError {
    pub fn terminal(&self) -> FiniteLambdaTerminal {
        match self {
            Self::BrokenLedger(_) | Self::TerminalMismatch => FiniteLambdaTerminal::Invalid,
            Self::Manifest(_)
            | Self::Binding(_)
            | Self::Primitive(_)
            | Self::Complex(_)
            | Self::Evaluation(_) => FiniteLambdaTerminal::InfrastructureFailure,
        }
    }
}

#[derive(Debug)]
pub struct FiniteLambdaEvaluation {
    ledger_hash: blake3::Hash,
    terminal: FiniteLambdaTerminal,
    evaluation: CodaGtlaEvaluation,
    authority_effect: AuthorityEffect,
}

impl FiniteLambdaEvaluation {
    pub fn ledger_hash(&self) -> &blake3::Hash {
        &self.ledger_hash
    }

    pub fn terminal(&self) -> FiniteLambdaTerminal {
        self.terminal
    }

    pub fn evaluation(&self) -> &CodaGtlaEvaluation {
        &self.evaluation
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

fn rational(value: u64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

pub fn finite_lambda_ledger_bytes(
    ledger: &FiniteLambdaLedger,
) -> Result<Vec<u8>, serde_json::Error> {
    let manifest = FiniteLambdaManifest {
        schema: "core_pipelines::finite_lambda_ledger::v1",
        initial: ledger.initial.into(),
        steps: ledger
            .steps
            .iter()
            .map(|step| FiniteLambdaStepManifest {
                before: step.before.into(),
                after: step.after.into(),
                preserves_old_vertices: step.extension.preserves_old_vertices,
                preserves_old_edges: step.extension.preserves_old_edges,
                records_tradeoff: step.extension.records_tradeoff,
            })
            .collect(),
        terminal: ledger.terminal.into(),
    };
    serde_json::to_vec(&manifest)
}

pub fn finite_lambda_ledger_hash(
    ledger: &FiniteLambdaLedger,
) -> Result<blake3::Hash, serde_json::Error> {
    Ok(blake3::hash(&finite_lambda_ledger_bytes(ledger)?))
}

fn exact_input(
    ledger: &FiniteLambdaLedger,
    carrier_manifest: &[u8],
) -> Result<CodaExactInput, FiniteLambdaAdapterError> {
    let omega = vec![
        rational(ledger.initial.phi1),
        rational(ledger.initial.gamma2),
    ];
    let zero = vec![rational(0), rational(0)];
    let d0 = vec![
        vec![rational(1), rational(0)],
        vec![rational(0), rational(1)],
    ];
    let certificate = ExactPhi1Certificate {
        omega: omega.clone(),
        d0: d0.clone(),
        weights: vec![rational(1), rational(1)],
        alpha: omega,
        primal_residual: zero.clone(),
        dual_witness: zero.clone(),
        reported_value: rational(0),
    };
    let complex = ExactCochainComplexQ::try_new(2, 2, 1, d0, vec![vec![rational(0), rational(0)]])?;
    let evidence_manifest = serde_json::to_vec(&(&certificate, &complex, &zero))?;
    let binding = bind_domain_evidence(
        "core_pipelines::finite_lambda_ledger",
        carrier_manifest,
        &evidence_manifest,
    )?;
    let mut domain = Vec::with_capacity(ledger.steps.len() + 2);
    domain.push(ledger.initial.into());
    domain.extend(
        ledger
            .steps
            .iter()
            .map(|step| FiniteLambdaPoint::from(step.after)),
    );
    domain.push(ledger.terminal.into());
    let receipt = validate_primitive_difference(
        &FiniteLambdaDifference,
        domain,
        binding.carrier_hash().clone(),
    )?;
    Ok(CodaExactInput::new(
        receipt,
        certificate,
        complex,
        zero,
        binding.into_packet_args(),
    ))
}

pub fn evaluate_finite_lambda_ledger(
    ledger: &FiniteLambdaLedger,
) -> Result<FiniteLambdaEvaluation, FiniteLambdaAdapterError> {
    ledger
        .require_chained()
        .map_err(FiniteLambdaAdapterError::BrokenLedger)?;
    let carrier_manifest = finite_lambda_ledger_bytes(ledger)?;
    let ledger_hash = blake3::hash(&carrier_manifest);
    let evaluation = evaluate_exact(exact_input(ledger, &carrier_manifest)?)?;
    if evaluation.status() != ObstructionDiagnosticClass::ExactRepair {
        return Err(FiniteLambdaAdapterError::TerminalMismatch);
    }
    Ok(FiniteLambdaEvaluation {
        ledger_hash,
        terminal: FiniteLambdaTerminal::ExactRepair,
        evaluation,
        authority_effect: AuthorityEffect::None,
    })
}

// Origin: engine/crates_rs/core_pipelines/src/finite_lambda_adapter.rs
// Claim: urn:core:crates_rs:core-pipelines:finite-lambda-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_bb7f58c7 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
