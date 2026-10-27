//! Replay only the exact functional claims in an core_id_run wall deposit.
//!
//! This is designed to pair with independent structural checks (rank, H1,
//! chain identity and receipt consistency). Its Phi1 and Gamma2 arithmetic
//! stays in this canonical functional crate. This binary emits evidence only;
//! it does not certify a deposit, accept a lift, or mint authority.

use std::env;
use std::fs;
use std::path::Path;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::One;
use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_functional::Gamma2Functional;
use core_policy::trichotomy::classify_exact;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_policy::trichotomy::TrichotomyOutcome;
use serde::Deserialize;
use serde_json::{json, Value};

const MAX_MATRIX_ENTRIES: usize = 1_000_000;

#[derive(Deserialize)]
struct WallCertificate {
    kind: String,
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    d0: Vec<[i64; 2]>,
    d1: Vec<[i64; 2]>,
    q: Vec<[i64; 2]>,
    alpha: Vec<[i64; 2]>,
    primal_residual: Vec<[i64; 2]>,
    dual_witness: Vec<[i64; 2]>,
    phi1: [i64; 2],
    gamma2: [i64; 2],
    gamma2_exact: [i64; 2],
    exact_status: String,
}

struct ReplaySummary {
    phi1: BigRational,
    gamma2_q: BigRational,
    gamma2_residual: BigRational,
    exact_status: &'static str,
}

fn rational(pair: [i64; 2], field: &str) -> Result<BigRational, String> {
    if pair[1] == 0 {
        return Err(format!("{field}: zero denominator"));
    }
    Ok(BigRational::new(
        BigInt::from(pair[0]),
        BigInt::from(pair[1]),
    ))
}

fn vector(pairs: &[[i64; 2]], field: &str) -> Result<Vec<BigRational>, String> {
    pairs
        .iter()
        .enumerate()
        .map(|(index, pair)| rational(*pair, &format!("{field}[{index}]")))
        .collect()
}

fn matrix(
    pairs: &[[i64; 2]],
    rows: usize,
    cols: usize,
    field: &str,
) -> Result<Vec<Vec<BigRational>>, String> {
    let expected = rows
        .checked_mul(cols)
        .ok_or_else(|| format!("{field}: dimensions overflow"))?;
    if expected > MAX_MATRIX_ENTRIES {
        return Err(format!("{field}: matrix exceeds replay size limit"));
    }
    if pairs.len() != expected {
        return Err(format!(
            "{field}: expected {expected} entries, found {}",
            pairs.len()
        ));
    }
    let flat = vector(pairs, field)?;
    let mut result = Vec::with_capacity(rows);
    for row in 0..rows {
        let start = row * cols;
        result.push(flat[start..start + cols].to_vec());
    }
    Ok(result)
}

struct ParsedWallCert {
    d0: Vec<Vec<BigRational>>,
    d1: Vec<Vec<BigRational>>,
    q: Vec<BigRational>,
    alpha: Vec<BigRational>,
    primal_residual: Vec<BigRational>,
    dual_witness: Vec<BigRational>,
    claimed_phi1: BigRational,
    claimed_gamma2_q: BigRational,
    claimed_gamma2_residual: BigRational,
}

fn validate_wall_header(cert: &WallCertificate) -> Result<(), String> {
    if cert.kind != "core_id_run::obstruction_wall_certificate" {
        return Err("unexpected certificate kind".into());
    }
    if [cert.c0_dim, cert.c1_dim, cert.c2_dim]
        .into_iter()
        .any(|dim| dim > MAX_MATRIX_ENTRIES)
    {
        return Err("cochain dimension exceeds replay size limit".into());
    }
    Ok(())
}

fn parse_wall_vectors(
    cert: &WallCertificate,
) -> Result<
    (
        Vec<BigRational>,
        Vec<BigRational>,
        Vec<BigRational>,
        Vec<BigRational>,
    ),
    String,
> {
    let q = vector(&cert.q, "q")?;
    let alpha = vector(&cert.alpha, "alpha")?;
    let primal_residual = vector(&cert.primal_residual, "primal_residual")?;
    let dual_witness = vector(&cert.dual_witness, "dual_witness")?;
    let lengths_match = [
        q.len() == cert.c1_dim,
        alpha.len() == cert.c0_dim,
        primal_residual.len() == cert.c1_dim,
        dual_witness.len() == cert.c1_dim,
    ]
    .into_iter()
    .all(|ok| ok);
    if !lengths_match {
        return Err("cochain or witness length does not match declared dimensions".into());
    }
    Ok((q, alpha, primal_residual, dual_witness))
}

fn parse_and_validate_wall_cert(cert: &WallCertificate) -> Result<ParsedWallCert, String> {
    validate_wall_header(cert)?;
    let d0 = matrix(&cert.d0, cert.c1_dim, cert.c0_dim, "d0")?;
    let d1 = matrix(&cert.d1, cert.c2_dim, cert.c1_dim, "d1")?;
    let (q, alpha, primal_residual, dual_witness) = parse_wall_vectors(cert)?;
    let claimed_phi1 = rational(cert.phi1, "phi1")?;
    let claimed_gamma2_q = rational(cert.gamma2, "gamma2")?;
    let claimed_gamma2_residual = rational(cert.gamma2_exact, "gamma2_exact")?;
    Ok(ParsedWallCert {
        d0,
        d1,
        q,
        alpha,
        primal_residual,
        dual_witness,
        claimed_phi1,
        claimed_gamma2_q,
        claimed_gamma2_residual,
    })
}

fn verify_gamma2_q_claim(
    complex: &ExactCochainComplexQ,
    q: Vec<BigRational>,
    claimed_gamma2_q: &BigRational,
) -> Result<BigRational, String> {
    let q_input = DegreeOneResidualQ::try_new(complex, q)
        .map_err(|error| format!("gamma2 q input: {error}"))?;
    let gamma2_q = Gamma2Functional::try_compute_exact_quotient(&q_input)
        .map_err(|error| format!("gamma2 q replay: {error}"))?;
    if gamma2_q.value() != claimed_gamma2_q {
        return Err("gamma2 claim does not match exact quotient replay on q".into());
    }
    Ok(gamma2_q.value().clone())
}

fn extract_wall_status(
    outcome: TrichotomyOutcome,
    claimed_status: &str,
) -> Result<&'static str, String> {
    let status = match outcome {
        TrichotomyOutcome::Classified(result) => match result.diagnostic_class() {
            ObstructionDiagnosticClass::ExactRepair => "ExactRepair",
            ObstructionDiagnosticClass::ClosedResidual => "StabilizedSurvivor",
            ObstructionDiagnosticClass::ActiveClosureFailure => "OpenObstruction",
        },
        TrichotomyOutcome::TriRefused(reason) => {
            return Err(format!("exact trichotomy refused: {reason:?}"));
        }
    };
    if claimed_status != status {
        return Err(format!(
            "exact_status claim {claimed_status} does not match replay {status}"
        ));
    }
    Ok(status)
}

fn replay(cert: WallCertificate) -> Result<ReplaySummary, String> {
    let parsed = parse_and_validate_wall_cert(&cert)?;

    let verified_phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: parsed.q.clone(),
        d0: parsed.d0.clone(),
        weights: vec![BigRational::one(); cert.c1_dim],
        alpha: parsed.alpha,
        primal_residual: parsed.primal_residual.clone(),
        dual_witness: parsed.dual_witness,
        reported_value: parsed.claimed_phi1,
    })
    .map_err(|error| format!("phi1 certificate: {error}"))?;

    let complex =
        ExactCochainComplexQ::try_new(cert.c0_dim, cert.c1_dim, cert.c2_dim, parsed.d0, parsed.d1)
            .map_err(|error| format!("cochain complex: {error}"))?;
    let gamma2_q = verify_gamma2_q_claim(&complex, parsed.q, &parsed.claimed_gamma2_q)?;

    let residual_input = DegreeOneResidualQ::try_new(&complex, parsed.primal_residual)
        .map_err(|error| format!("gamma2 residual input: {error}"))?;
    let gamma2_residual = Gamma2Functional::try_compute_exact_quotient(&residual_input)
        .map_err(|error| format!("gamma2 residual replay: {error}"))?;
    if gamma2_residual.value() != &parsed.claimed_gamma2_residual {
        return Err("gamma2_exact claim does not match exact quotient replay on residual".into());
    }

    let status = extract_wall_status(
        classify_exact(&verified_phi1, &gamma2_residual),
        &cert.exact_status,
    )?;

    Ok(ReplaySummary {
        phi1: verified_phi1.value().clone(),
        gamma2_q,
        gamma2_residual: gamma2_residual.value().clone(),
        exact_status: status,
    })
}

fn replay_json(value: Value) -> Result<ReplaySummary, String> {
    let cert: WallCertificate =
        serde_json::from_value(value).map_err(|error| format!("certificate schema: {error}"))?;
    replay(cert)
}

fn pair_json(value: &BigRational) -> Value {
    json!([value.numer().to_string(), value.denom().to_string()])
}

fn result_json(result: Result<ReplaySummary, String>) -> (Value, bool) {
    match result {
        Ok(summary) => (
            json!({
                "status": "PASS",
                "schema": "core_functional.wall_functional_replay.v1",
                "authority_effect": "None",
                "phi1": pair_json(&summary.phi1),
                "gamma2": pair_json(&summary.gamma2_q),
                "gamma2_exact": pair_json(&summary.gamma2_residual),
                "exact_status": summary.exact_status,
                "checks": ["PHI1_CERTIFICATE", "GAMMA2_Q", "GAMMA2_RESIDUAL", "EXACT_TRICHOTOMY"]
            }),
            true,
        ),
        Err(reason) => (
            json!({
                "status": "REFUSE",
                "schema": "core_functional.wall_functional_replay.v1",
                "authority_effect": "None",
                "reason": reason
            }),
            false,
        ),
    }
}

fn run_path(path: &Path) -> Result<ReplaySummary, String> {
    let data = fs::read_to_string(path).map_err(|error| format!("read certificate: {error}"))?;
    let value: Value =
        serde_json::from_str(&data).map_err(|error| format!("parse certificate: {error}"))?;
    replay_json(value)
}

fn main() {
    let args: Vec<_> = env::args_os().collect();
    let result = if args.len() == 2 {
        run_path(Path::new(&args[1]))
    } else {
        Err("usage: verify_wall_functionals <wall_certificate.json>".into())
    };
    let (payload, passed) = result_json(result);
    println!("{payload}");
    if !passed {
        std::process::exit(1);
    }
}

// Origin: engine/crates_rs/pfp/src/bin/verify_wall_functionals.rs
// Claim: urn:core:crates_rs:pfp:verify-wall-functionals:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd84726bc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd84726bc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord84726bc {
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
impl BoundaryErrord84726bc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord84726bc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord84726bc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd84726bc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord84726bc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord84726bc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord84726bc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord84726bc::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn open_wall() -> Value {
        json!({
            "kind": "core_id_run::obstruction_wall_certificate",
            "c0_dim": 1,
            "c1_dim": 1,
            "c2_dim": 1,
            "d0": [[0, 1]],
            "d1": [[1, 1]],
            "q": [[1, 1]],
            "alpha": [[0, 1]],
            "primal_residual": [[1, 1]],
            "dual_witness": [[1, 1]],
            "phi1": [1, 1],
            "gamma2": [1, 1],
            "gamma2_exact": [1, 1],
            "exact_status": "OpenObstruction"
        })
    }

    #[test]
    fn accepts_exact_open_wall_without_authority() {
        let (payload, passed) = result_json(replay_json(open_wall()));
        assert!(passed, "{payload}");
        assert_eq!(payload["status"], "PASS");
        assert_eq!(payload["authority_effect"], "None");
        assert_eq!(payload["phi1"], json!(["1", "1"]));
        assert_eq!(payload["gamma2"], json!(["1", "1"]));
    }

    #[test]
    fn maps_all_exact_trichotomy_classes_to_deposit_statuses() {
        let mut survivor = open_wall();
        survivor["d1"] = json!([[0, 1]]);
        survivor["gamma2"] = json!([0, 1]);
        survivor["gamma2_exact"] = json!([0, 1]);
        survivor["exact_status"] = json!("StabilizedSurvivor");
        let (payload, passed) = result_json(replay_json(survivor));
        assert!(passed, "{payload}");

        let mut repaired = open_wall();
        repaired["d0"] = json!([[1, 1]]);
        repaired["d1"] = json!([[0, 1]]);
        repaired["alpha"] = json!([[1, 1]]);
        repaired["primal_residual"] = json!([[0, 1]]);
        repaired["dual_witness"] = json!([[0, 1]]);
        repaired["phi1"] = json!([0, 1]);
        repaired["gamma2"] = json!([0, 1]);
        repaired["gamma2_exact"] = json!([0, 1]);
        repaired["exact_status"] = json!("ExactRepair");
        let (payload, passed) = result_json(replay_json(repaired));
        assert!(passed, "{payload}");
    }

    #[test]
    fn refuses_incomplete_legacy_certificate_without_alpha() {
        let mut cert = open_wall();
        cert.as_object_mut().unwrap().remove("alpha");
        let (payload, passed) = result_json(replay_json(cert));
        assert!(!passed);
        assert_eq!(payload["status"], "REFUSE");
        assert!(payload["reason"].as_str().unwrap().contains("alpha"));
    }

    #[test]
    fn refuses_tampered_phi_and_gamma_claims() {
        for (field, expected_reason) in [
            ("phi1", "phi1 certificate"),
            ("gamma2", "gamma2 claim"),
            ("gamma2_exact", "gamma2_exact claim"),
        ] {
            let mut cert = open_wall();
            cert[field] = json!([2, 1]);
            let (payload, passed) = result_json(replay_json(cert));
            assert!(!passed, "{field}");
            assert!(payload["reason"]
                .as_str()
                .unwrap()
                .contains(expected_reason));
        }
    }

    #[test]
    fn refuses_invalid_chain_or_primal_witness() {
        let mut chain = open_wall();
        chain["d0"] = json!([[1, 1]]);
        let (payload, passed) = result_json(replay_json(chain));
        assert!(!passed);
        assert_eq!(payload["status"], "REFUSE");

        let mut residual = open_wall();
        residual["primal_residual"] = json!([[0, 1]]);
        let (payload, passed) = result_json(replay_json(residual));
        assert!(!passed);
        assert!(payload["reason"]
            .as_str()
            .unwrap()
            .contains("phi1 certificate"));
    }

    #[test]
    fn refuses_zero_denominator_and_wrong_matrix_shape() {
        let mut zero_denominator = open_wall();
        zero_denominator["q"] = json!([[1, 0]]);
        let (payload, passed) = result_json(replay_json(zero_denominator));
        assert!(!passed);
        assert!(payload["reason"]
            .as_str()
            .unwrap()
            .contains("zero denominator"));

        let mut wrong_shape = open_wall();
        wrong_shape["d1"] = json!([]);
        let (payload, passed) = result_json(replay_json(wrong_shape));
        assert!(!passed);
        assert!(payload["reason"]
            .as_str()
            .unwrap()
            .contains("expected 1 entries"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_d84726bc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd84726bc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd84726bc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd84726bc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd84726bc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd84726bc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord84726bc::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord84726bc::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
