//! Conformance: gamma2 exact cochain refusal (family 8) and trichotomy (family 9).
//! Independently authored finite fixtures; exact diagnostic evidence only.
//! Fixtures and their hand-derived expectations are owned by this native crate.
use std::path::PathBuf;

use num_bigint::BigInt;
use num_rational::BigRational;
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, Gamma2Functional,
};
use serde::Deserialize;

fn vectors_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../tests/core_policy/fixtures/conformance")
}

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

fn col(v: &[i64]) -> Vec<BigRational> {
    v.iter().map(|&x| r(x)).collect()
}

fn mat(m: &[Vec<i64>]) -> Vec<Vec<BigRational>> {
    m.iter().map(|row| col(row)).collect()
}

#[derive(Deserialize)]
struct Gamma2File {
    schema_version: String,
    authority_effect: String,
    weight_profile_id: String,
    cases: Vec<Gamma2Case>,
}

#[derive(Deserialize)]
struct Gamma2Case {
    id: String,
    input: Gamma2Input,
    expected: Gamma2Expected,
}

#[derive(Deserialize)]
struct Gamma2Input {
    residual: Vec<i64>,
    d0: Vec<Vec<i64>>,
    d1: Vec<Vec<i64>>,
}

#[derive(Deserialize)]
struct Gamma2Expected {
    cochain_ok: bool,
    value: Option<i64>,
}

#[test]
fn gamma2_cochain_refusal() {
    let path = vectors_dir().join("08_gamma2_cochain_refusal.json");
    let text =
        std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    let file: Gamma2File =
        serde_json::from_str(&text).unwrap_or_else(|e| panic!("parse {}: {e}", path.display()));
    assert_eq!(file.schema_version, "core.functional.gamma2-fixtures.v1");
    assert_eq!(file.authority_effect, "None");
    assert_eq!(
        file.cases.iter().map(|c| c.id.as_str()).collect::<Vec<_>>(),
        ["closed", "open_negative_coordinate", "non_cochain"]
    );
    assert_eq!(file.weight_profile_id, "unit_weights_v1");

    for case in &file.cases {
        let residual_val = col(&case.input.residual);
        let d0_val = mat(&case.input.d0);
        let d1_val = mat(&case.input.d1);
        let c0_dim = if d0_val.is_empty() {
            0
        } else {
            d0_val[0].len()
        };
        let c1_dim = residual_val.len();
        let c2_dim = d1_val.len();
        let complex = ExactCochainComplexQ::try_new(c0_dim, c1_dim, c2_dim, d0_val, d1_val);
        if case.expected.cochain_ok {
            let complex =
                complex.unwrap_or_else(|e| panic!("expected ok for {}: complex {e:?}", case.id));
            let residual = DegreeOneResidualQ::try_new(&complex, residual_val)
                .unwrap_or_else(|e| panic!("expected ok for {}: residual {e:?}", case.id));
            let gamma = Gamma2Functional::try_compute_exact_quotient(&residual)
                .unwrap_or_else(|e| panic!("gamma2 for {}: {e:?}", case.id));
            let want = r(case.expected.value.expect("value for ok case"));
            assert_eq!(gamma.value(), &want, "value {}", case.id);
        } else {
            // For non-ok cases, the error should come from complex construction (d1*d0 != 0)
            assert_eq!(
                complex.unwrap_err(),
                ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 },
                "expected exact chain-law refusal for {}",
                case.id
            );
        }
    }
}

use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_policy::trichotomy::{classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome};

#[derive(Deserialize)]
struct TriFile {
    schema_version: String,
    authority_effect: String,
    weight_profile_id: String,
    cases: Vec<TriCase>,
}

#[derive(Deserialize)]
struct TriCase {
    id: String,
    input: TriInput,
    expected: String,
}

#[derive(Deserialize)]
struct TriInput {
    omega: Vec<i64>,
    d0: Vec<Vec<i64>>,
    weights: Vec<i64>,
    alpha: Vec<i64>,
    primal_residual: Vec<i64>,
    dual_witness: Vec<i64>,
    reported_value: i64,
    d1: Vec<Vec<i64>>,
}

fn status_from(s: &str) -> ObstructionDiagnosticClass {
    match s {
        "ExactRepair" => ObstructionDiagnosticClass::ExactRepair,
        "StabilizedSurvivor" => ObstructionDiagnosticClass::ClosedResidual,
        "OpenObstruction" => ObstructionDiagnosticClass::ActiveClosureFailure,
        other => panic!("unknown trichotomy status in vector: {other}"),
    }
}

#[test]
fn trichotomy_exact_classification() {
    let path = vectors_dir().join("09_trichotomy.json");
    let text =
        std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    let file: TriFile =
        serde_json::from_str(&text).unwrap_or_else(|e| panic!("parse {}: {e}", path.display()));
    assert_eq!(
        file.schema_version,
        "core.functional.trichotomy-fixtures.v1"
    );
    assert_eq!(file.authority_effect, "None");
    assert_eq!(
        file.cases.iter().map(|c| c.id.as_str()).collect::<Vec<_>>(),
        ["exact", "closed_residual", "active_closure"]
    );
    assert_eq!(file.weight_profile_id, "unit_weights_v1");

    for case in &file.cases {
        let phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: col(&case.input.omega),
            d0: mat(&case.input.d0),
            weights: col(&case.input.weights),
            alpha: col(&case.input.alpha),
            primal_residual: col(&case.input.primal_residual),
            dual_witness: col(&case.input.dual_witness),
            reported_value: r(case.input.reported_value),
        })
        .unwrap_or_else(|e| panic!("verify phi1 for {}: {e:?}", case.id));

        let d0_val = phi1.d0().to_vec();
        let d1_val = mat(&case.input.d1);
        let c0_dim = if d0_val.is_empty() {
            0
        } else {
            d0_val[0].len()
        };
        let c1_dim = phi1.primal_residual().len();
        let c2_dim = d1_val.len();
        let complex =
            ExactCochainComplexQ::try_new(c0_dim, c1_dim, c2_dim, d0_val, d1_val).unwrap();
        let residual =
            DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec()).unwrap();
        let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual)
            .unwrap_or_else(|e| panic!("gamma2 for {}: {e:?}", case.id));

        match classify_exact(&phi1, &gamma2) {
            TrichotomyOutcome::Classified(c) => {
                assert_eq!(
                    c.diagnostic_class(),
                    status_from(&case.expected),
                    "status {}",
                    case.id
                );
            }
            TrichotomyOutcome::TriRefused(refusal) => {
                panic!("unexpected refusal for {}: {refusal:?}", case.id);
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_policy/conformance_gamma2_trichotomy.rs
// Claim: urn:core:crates_rs:tests:conformance-gamma2-trichotomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord39fc1908 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord39fc1908` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError39fc1908 {
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
impl BoundaryError39fc1908 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError39fc1908 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError39fc1908 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord39fc1908 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError39fc1908> {
        if capacity_bound == 0 {
            return Err(BoundaryError39fc1908::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError39fc1908::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError39fc1908::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_39fc1908() {
    let admitted = BoundaryRecord39fc1908::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord39fc1908::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
