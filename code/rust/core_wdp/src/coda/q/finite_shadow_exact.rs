//! Exact-arithmetic finite shadow system dual (Target 10 — reusable PROD path).
//!
//! --- Math Contract:
//! - Purpose: carry **exact** Fin-`n` residual masses and a CODA-CS-Q style
//!   finite-shadow system through a diagnostic terminalization that mirrors the
//!   Python TEST_ONLY dual (`FiniteShadowSystem.terminalize`) without floating
//!   point and without minting authority.
//! - Inputs: finite support size `n`, non-negative integer masses, named shadow
//!   family / refinement edges, topology label, cofinality flag, exact
//!   non-negative rational error budget, optional convergence witness.
//! - Outputs: [`TerminalizationDiagnostic`] with status/terminal labels only;
//!   exact product / marginals for Fin-`n` distributions.
//! - Invariants: no `f64` arithmetic; masses and budgets are exact integers /
//!   rationals; AuthorityEffect is always [`AUTHORITY_EFFECT_NONE`]; continuum
//!   requests without a convergence witness never upgrade past
//!   `OracleNeeded(Convergence)`.
//! - Failure: empty support, zero denominator, mass/support length mismatch.
//! - Numerical status: exact integer / rational only.
//! - Authority: diagnostic dual only. **Not** a continuum theorem. **Not**
//!   GlobalGreen. Python duals remain TEST_ONLY prototypes.
//!
//! Cross-ref: field-name constants align with `FiniteQMContractV1`
//! (`urn:core:math:finite_qm:v1.0.0`) for fixture/schema glue. This module does
//! **not** implement the full schema shell (that is `finite_qm_types` / Target 3).

use serde::{Deserialize, Serialize};
use thiserror::Error;

// ---------------------------------------------------------------------------
// FiniteQMContractV1 field-name cross-ref (string constants only)
// ---------------------------------------------------------------------------

/// JSON schema tag for FiniteQMContractV1 (`json_schema.schema_version`).
pub const FINITE_QM_CONTRACT_SCHEMA_VERSION: &str = "FiniteQMContractV1";

/// Contract URN alias for FiniteQMContractV1.
pub const FINITE_QM_CONTRACT_URN: &str = "urn:core:math:finite_qm:v1.0.0";

/// `json_schema.fields.schema_version`
pub const FIELD_SCHEMA_VERSION: &str = "schema_version";
/// `json_schema.fields.contract_urn`
pub const FIELD_CONTRACT_URN: &str = "contract_urn";
/// `json_schema.fields.authority_effect`
pub const FIELD_AUTHORITY_EFFECT: &str = "authority_effect";
/// `json_schema.fields.carrier` (FiniteCarrier fence)
pub const FIELD_CARRIER: &str = "carrier";
/// Nested: `carrier.carrier_id`
pub const FIELD_CARRIER_ID: &str = "carrier_id";
/// Nested: `carrier.support_cardinality`
pub const FIELD_SUPPORT_CARDINALITY: &str = "support_cardinality";
/// `json_schema.fields.dimension` (FiniteDimension fence)
pub const FIELD_DIMENSION: &str = "dimension";
/// Nested: `dimension.dimension_id`
pub const FIELD_DIMENSION_ID: &str = "dimension_id";
/// Nested: `dimension.rank`
pub const FIELD_RANK: &str = "rank";
/// `json_schema.fields.certificate` (FiniteCertificate fence)
pub const FIELD_CERTIFICATE: &str = "certificate";
/// Nested: `certificate.certificate_id`
pub const FIELD_CERTIFICATE_ID: &str = "certificate_id";
/// Nested: `certificate.kind`
pub const FIELD_CERTIFICATE_KIND: &str = "kind";
/// Nested: `certificate.payload_digest_sha256`
pub const FIELD_PAYLOAD_DIGEST_SHA256: &str = "payload_digest_sha256";
/// `json_schema.fields.continuum_debt` (Finite-QM sense, not core_q admission)
pub const FIELD_CONTINUUM_DEBT: &str = "continuum_debt";
/// Nested: `continuum_debt.scalars`
pub const FIELD_SCALARS: &str = "scalars";
/// Nested: `continuum_debt.notes`
pub const FIELD_NOTES: &str = "notes";
/// `json_schema.fields.import_ledger`
pub const FIELD_IMPORT_LEDGER: &str = "import_ledger";
/// Nested: `import_ledger.slots`
pub const FIELD_SLOTS: &str = "slots";

/// Standing authority declaration for this dual. Never rewritten.
pub const AUTHORITY_EFFECT_NONE: &str = "None";

/// Layer label shared with the Python CODA-CS-Q dual.
pub const LAYER_CODA_CS_Q: &str = "CODA-CS-Q";

// ---------------------------------------------------------------------------
// Exact non-negative rational (error budget)
// ---------------------------------------------------------------------------

/// Exact non-negative rational `numer / denom` in lowest terms (denom > 0).
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ExactNonNegRational {
    numer: u64,
    denom: u64,
}

impl ExactNonNegRational {
    /// Constructs `numer / denom` with `denom > 0`, reduced by gcd.
    pub fn new(numer: u64, denom: u64) -> Result<Self, FiniteShadowExactError> {
        if denom == 0 {
            return Err(FiniteShadowExactError::ZeroDenominator);
        }
        let g = gcd_u64(numer, denom);
        Ok(Self {
            numer: numer / g,
            denom: denom / g,
        })
    }

    /// Exact zero budget.
    pub fn zero() -> Self {
        Self { numer: 0, denom: 1 }
    }

    pub fn numer(&self) -> u64 {
        self.numer
    }

    pub fn denom(&self) -> u64 {
        self.denom
    }

    /// True iff this rational is strictly negative — impossible for this type.
    pub fn is_negative(&self) -> bool {
        false
    }

    /// Cross-multiply compare: self < other.
    pub fn lt(&self, other: &Self) -> bool {
        // a/b < c/d ⇔ a*d < c*b  (all non-negative; use u128 to avoid overflow)
        (self.numer as u128) * (other.denom as u128) < (other.numer as u128) * (self.denom as u128)
    }
}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a.max(1)
}

// ---------------------------------------------------------------------------
// Fin n distribution (exact integer masses)
// ---------------------------------------------------------------------------

/// Exact non-negative integer mass distribution on `Fin n = {0, …, n-1}`.
///
/// Masses are absolute residual weights (not required to sum to 1). Normalization
/// is an optional exact rational projection; never performed with floats.
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct FinDistribution {
    /// Support cardinality `n` (FiniteCarrier.support_cardinality sense).
    n: usize,
    /// Exact non-negative integer mass on each point of Fin n.
    masses: Vec<u64>,
}

impl FinDistribution {
    /// Builds a distribution; `masses.len()` must equal `n`, and `n ≥ 1`.
    pub fn new(n: usize, masses: Vec<u64>) -> Result<Self, FiniteShadowExactError> {
        if n == 0 {
            return Err(FiniteShadowExactError::EmptySupport);
        }
        if masses.len() != n {
            return Err(FiniteShadowExactError::MassLengthMismatch {
                expected: n,
                got: masses.len(),
            });
        }
        Ok(Self { n, masses })
    }

    /// Fin-2 bit residual weight `(w0, w1)`.
    pub fn bit(w0: u64, w1: u64) -> Self {
        Self {
            n: 2,
            masses: vec![w0, w1],
        }
    }

    pub fn n(&self) -> usize {
        self.n
    }

    pub fn masses(&self) -> &[u64] {
        &self.masses
    }

    pub fn total_mass(&self) -> u64 {
        self.masses.iter().copied().sum()
    }

    /// Pure iff exactly one positive mass cell.
    pub fn is_pure(&self) -> bool {
        self.masses.iter().filter(|&&m| m > 0).count() == 1
    }

    /// Mixed iff at least two positive mass cells.
    pub fn is_mixed(&self) -> bool {
        self.masses.iter().filter(|&&m| m > 0).count() >= 2
    }

    /// Independent classical product on Fin (n_a * n_b).
    ///
    /// Cell index is row-major: `i * n_b + j` holds `mass_a[i] * mass_b[j]`.
    pub fn product(&self, other: &Self) -> Result<Self, FiniteShadowExactError> {
        let n = self
            .n
            .checked_mul(other.n)
            .ok_or(FiniteShadowExactError::SupportOverflow)?;
        let mut masses = Vec::with_capacity(n);
        for &a in &self.masses {
            for &b in &other.masses {
                masses.push(
                    a.checked_mul(b)
                        .ok_or(FiniteShadowExactError::MassOverflow)?,
                );
            }
        }
        Self::new(n, masses)
    }

    /// A-marginal of a Fin(n_a * n_b) joint under the product indexing of
    /// [`Self::product`], with sector size `n_b`.
    pub fn marginal_a(&self, n_b: usize) -> Result<Self, FiniteShadowExactError> {
        if n_b == 0 || self.n % n_b != 0 {
            return Err(FiniteShadowExactError::InvalidMarginalShape {
                joint_n: self.n,
                n_b,
            });
        }
        let n_a = self.n / n_b;
        let mut masses = vec![0u64; n_a];
        for i in 0..n_a {
            let mut sum = 0u64;
            for j in 0..n_b {
                sum = sum
                    .checked_add(self.masses[i * n_b + j])
                    .ok_or(FiniteShadowExactError::MassOverflow)?;
            }
            masses[i] = sum;
        }
        Self::new(n_a, masses)
    }

    /// B-marginal under the same product indexing.
    pub fn marginal_b(&self, n_b: usize) -> Result<Self, FiniteShadowExactError> {
        if n_b == 0 || self.n % n_b != 0 {
            return Err(FiniteShadowExactError::InvalidMarginalShape {
                joint_n: self.n,
                n_b,
            });
        }
        let n_a = self.n / n_b;
        let mut masses = vec![0u64; n_b];
        for j in 0..n_b {
            let mut sum = 0u64;
            for i in 0..n_a {
                sum = sum
                    .checked_add(self.masses[i * n_b + j])
                    .ok_or(FiniteShadowExactError::MassOverflow)?;
            }
            masses[j] = sum;
        }
        Self::new(n_b, masses)
    }

    /// Exact probability of cell `i` as a reduced rational, if total mass > 0.
    pub fn probability(&self, i: usize) -> Result<ExactNonNegRational, FiniteShadowExactError> {
        if i >= self.n {
            return Err(FiniteShadowExactError::IndexOutOfRange {
                index: i,
                n: self.n,
            });
        }
        let total = self.total_mass();
        if total == 0 {
            return Err(FiniteShadowExactError::ZeroTotalMass);
        }
        ExactNonNegRational::new(self.masses[i], total)
    }
}

// ---------------------------------------------------------------------------
// Finite shadow system (exact dual of Python FiniteShadowSystem)
// ---------------------------------------------------------------------------

/// Diagnostic terminal labels for finite-shadow terminalization.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ShadowTerminalLabel {
    /// Missing shadow/refinement/topology or non-cofinal / negative budget.
    ShadowRefusal,
    /// Continuum requested without a convergence witness.
    OracleNeededConvergence,
    /// Finite query replay admitted (not continuum authority).
    FiniteShadowReplay,
}

impl ShadowTerminalLabel {
    /// Wire label matching the Python dual terminal strings.
    pub fn as_python_dual_str(self) -> &'static str {
        match self {
            Self::ShadowRefusal => "ShadowRefusal",
            Self::OracleNeededConvergence => "OracleNeeded(Convergence)",
            Self::FiniteShadowReplay => "FiniteShadowReplay",
        }
    }
}

/// Status label aligned with the Python dual (`pass` / `refused` / `conditional`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ShadowStatus {
    Pass,
    Refused,
    Conditional,
}

impl ShadowStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Pass => "pass",
            Self::Refused => "refused",
            Self::Conditional => "conditional",
        }
    }
}

/// Exact CODA-CS-Q finite shadow system (PROD-path dual of the Python prototype).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteShadowSystemExact {
    shadows: Vec<String>,
    refinements: Vec<(String, String)>,
    topology: Option<String>,
    cofinal_for_query: bool,
    error_budget: ExactNonNegRational,
    convergence_witness: Option<String>,
}

impl FiniteShadowSystemExact {
    /// Constructs a system. Empty strings in shadow/refinement names are kept
    /// as data; emptiness of the *collections* drives refusal.
    pub fn new(
        shadows: Vec<String>,
        refinements: Vec<(String, String)>,
        topology: Option<String>,
        cofinal_for_query: bool,
        error_budget: ExactNonNegRational,
        convergence_witness: Option<String>,
    ) -> Self {
        Self {
            shadows,
            refinements,
            topology,
            cofinal_for_query,
            error_budget,
            convergence_witness,
        }
    }

    pub fn shadows(&self) -> &[String] {
        &self.shadows
    }

    pub fn refinements(&self) -> &[(String, String)] {
        &self.refinements
    }

    pub fn topology(&self) -> Option<&str> {
        self.topology.as_deref()
    }

    pub fn cofinal_for_query(&self) -> bool {
        self.cofinal_for_query
    }

    pub fn error_budget(&self) -> &ExactNonNegRational {
        &self.error_budget
    }

    pub fn convergence_witness(&self) -> Option<&str> {
        self.convergence_witness.as_deref()
    }

    /// Attach or replace the named convergence witness route (diagnostic only).
    pub fn with_convergence_witness(mut self, witness: impl Into<String>) -> Self {
        self.convergence_witness = Some(witness.into());
        self
    }

    fn has_nonempty_convergence_witness(&self) -> bool {
        match &self.convergence_witness {
            Some(w) => !w.trim().is_empty(),
            None => false,
        }
    }

    /// Terminalization diagnostic dual of Python `FiniteShadowSystem.terminalize`.
    ///
    /// Rules (exact; AuthorityEffect None):
    /// 1. Empty shadows, empty refinements, or missing topology → ShadowRefusal.
    /// 2. Not cofinal for the declared query, or negative error budget → ShadowRefusal
    ///    (negative budget is uninhabited for [`ExactNonNegRational`]).
    /// 3. Continuum required and no convergence witness → OracleNeeded(Convergence).
    /// 4. Otherwise → FiniteShadowReplay (finite scope only).
    pub fn terminalize(&self, require_continuum: bool) -> TerminalizationDiagnostic {
        let topology_ok = match &self.topology {
            Some(t) => !t.trim().is_empty(),
            None => false,
        };
        let (status, terminal) =
            if self.shadows.is_empty() || self.refinements.is_empty() || !topology_ok {
                (ShadowStatus::Refused, ShadowTerminalLabel::ShadowRefusal)
            } else if !self.cofinal_for_query || self.error_budget.is_negative() {
                (ShadowStatus::Refused, ShadowTerminalLabel::ShadowRefusal)
            } else if require_continuum && !self.has_nonempty_convergence_witness() {
                (
                    ShadowStatus::Conditional,
                    ShadowTerminalLabel::OracleNeededConvergence,
                )
            } else {
                (ShadowStatus::Pass, ShadowTerminalLabel::FiniteShadowReplay)
            };

        TerminalizationDiagnostic {
            layer: LAYER_CODA_CS_Q.to_string(),
            status,
            terminal,
            shadows: self.shadows.clone(),
            refinements: self.refinements.clone(),
            topology: self.topology.clone(),
            cofinal_for_declared_query: self.cofinal_for_query,
            error_budget: self.error_budget.clone(),
            continuum_requested: require_continuum,
            convergence_witness: self.convergence_witness.clone(),
            authority_effect: AUTHORITY_EFFECT_NONE.to_string(),
            finite_qm_schema_version: FINITE_QM_CONTRACT_SCHEMA_VERSION.to_string(),
            finite_qm_contract_urn: FINITE_QM_CONTRACT_URN.to_string(),
        }
    }
}

/// Diagnostic result of [`FiniteShadowSystemExact::terminalize`].
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TerminalizationDiagnostic {
    pub layer: String,
    pub status: ShadowStatus,
    pub terminal: ShadowTerminalLabel,
    pub shadows: Vec<String>,
    pub refinements: Vec<(String, String)>,
    pub topology: Option<String>,
    pub cofinal_for_declared_query: bool,
    pub error_budget: ExactNonNegRational,
    pub continuum_requested: bool,
    pub convergence_witness: Option<String>,
    /// Always `"None"`.
    pub authority_effect: String,
    /// Cross-ref to FiniteQMContractV1 schema tag (fixture glue only).
    pub finite_qm_schema_version: String,
    /// Cross-ref to FiniteQMContractV1 URN (fixture glue only).
    pub finite_qm_contract_urn: String,
}

impl TerminalizationDiagnostic {
    /// Python-dual wire string for the terminal field.
    pub fn terminal_wire(&self) -> &'static str {
        self.terminal.as_python_dual_str()
    }
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

#[derive(Clone, Debug, PartialEq, Eq, Error)]
pub enum FiniteShadowExactError {
    #[error("exact rational denominator must be non-zero")]
    ZeroDenominator,
    #[error("Fin n support must be non-empty (n ≥ 1)")]
    EmptySupport,
    #[error("mass vector length {got} does not match Fin n = {expected}")]
    MassLengthMismatch { expected: usize, got: usize },
    #[error("support cardinality overflow under product")]
    SupportOverflow,
    #[error("mass product overflow")]
    MassOverflow,
    #[error("invalid marginal shape: joint_n={joint_n}, n_b={n_b}")]
    InvalidMarginalShape { joint_n: usize, n_b: usize },
    #[error("index {index} out of range for Fin {n}")]
    IndexOutOfRange { index: usize, n: usize },
    #[error("cannot form probability with zero total mass")]
    ZeroTotalMass,
}

// ---------------------------------------------------------------------------
// Fixture DTO (shared JSON under fixtures/finite_shadow/)
// ---------------------------------------------------------------------------

/// Shared fixture schema for exact finite-shadow cases.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteShadowFixture {
    pub fixture_id: String,
    pub kind: String,
    pub authority_effect: String,
    pub global_green: bool,
    /// FiniteQMContractV1 field-name cross-ref block (optional glue).
    #[serde(default)]
    pub finite_qm_contract_field_refs: FiniteQmFieldRefs,
    pub system: FixtureSystem,
    pub cases: Vec<FixtureCase>,
    #[serde(default)]
    pub distributions: Vec<FixtureDistributionCase>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteQmFieldRefs {
    #[serde(default)]
    pub schema_version: Option<String>,
    #[serde(default)]
    pub contract_urn: Option<String>,
    #[serde(default)]
    pub field_names: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FixtureSystem {
    pub shadows: Vec<String>,
    pub refinements: Vec<[String; 2]>,
    pub topology: Option<String>,
    pub cofinal_for_query: bool,
    pub error_budget: FixtureRational,
    #[serde(default)]
    pub convergence_witness: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FixtureRational {
    pub numer: u64,
    pub denom: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FixtureCase {
    pub case_id: String,
    pub require_continuum: bool,
    pub expected_status: String,
    pub expected_terminal: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FixtureDistributionCase {
    pub case_id: String,
    pub a: FixtureDist,
    pub b: FixtureDist,
    pub expected_product_masses: Vec<u64>,
    pub expected_marg_a: Vec<u64>,
    pub expected_marg_b: Vec<u64>,
    pub expected_a_pure: bool,
    pub expected_a_mixed: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FixtureDist {
    pub n: usize,
    pub masses: Vec<u64>,
}

impl FiniteShadowFixture {
    /// Materialize the exact system from fixture data.
    pub fn system_exact(&self) -> Result<FiniteShadowSystemExact, FiniteShadowExactError> {
        let budget = ExactNonNegRational::new(
            self.system.error_budget.numer,
            self.system.error_budget.denom,
        )?;
        let refinements = self
            .system
            .refinements
            .iter()
            .map(|pair| (pair[0].clone(), pair[1].clone()))
            .collect();
        Ok(FiniteShadowSystemExact::new(
            self.system.shadows.clone(),
            refinements,
            self.system.topology.clone(),
            self.system.cofinal_for_query,
            budget,
            self.system.convergence_witness.clone(),
        ))
    }

    /// Replay all terminalization cases; returns the first mismatch description.
    pub fn replay_terminalization(&self) -> Result<(), String> {
        if self.authority_effect != AUTHORITY_EFFECT_NONE {
            return Err(format!(
                "fixture {} authority_effect must be None, got {}",
                self.fixture_id, self.authority_effect
            ));
        }
        if self.global_green {
            return Err(format!(
                "fixture {} must not claim global_green",
                self.fixture_id
            ));
        }
        let system = self
            .system_exact()
            .map_err(|e| format!("fixture {} system: {e}", self.fixture_id))?;
        for case in &self.cases {
            let diag = system.terminalize(case.require_continuum);
            if diag.status.as_str() != case.expected_status {
                return Err(format!(
                    "fixture {} case {}: status got {} want {}",
                    self.fixture_id,
                    case.case_id,
                    diag.status.as_str(),
                    case.expected_status
                ));
            }
            if diag.terminal_wire() != case.expected_terminal {
                return Err(format!(
                    "fixture {} case {}: terminal got {} want {}",
                    self.fixture_id,
                    case.case_id,
                    diag.terminal_wire(),
                    case.expected_terminal
                ));
            }
            if diag.authority_effect != AUTHORITY_EFFECT_NONE {
                return Err(format!(
                    "fixture {} case {}: authority_effect not None",
                    self.fixture_id, case.case_id
                ));
            }
        }
        Ok(())
    }

    fn verify_product_and_marginals(
        case_id: &str,
        a: &FinDistribution,
        b: &FinDistribution,
        expected_product: &[u64],
        expected_marg_a: &[u64],
        expected_marg_b: &[u64],
    ) -> Result<(), String> {
        let product = a
            .product(b)
            .map_err(|e| format!("{case_id}: product: {e}"))?;
        if product.masses() != expected_product {
            return Err(format!(
                "{case_id}: product masses got {:?} want {:?}",
                product.masses(),
                expected_product
            ));
        }
        let marg_a = product
            .marginal_a(b.n())
            .map_err(|e| format!("{case_id}: marg_a: {e}"))?;
        if marg_a.masses() != expected_marg_a {
            return Err(format!(
                "{case_id}: marg_a got {:?} want {:?}",
                marg_a.masses(),
                expected_marg_a
            ));
        }
        let marg_b = product
            .marginal_b(b.n())
            .map_err(|e| format!("{case_id}: marg_b: {e}"))?;
        if marg_b.masses() != expected_marg_b {
            return Err(format!(
                "{case_id}: marg_b got {:?} want {:?}",
                marg_b.masses(),
                expected_marg_b
            ));
        }
        Ok(())
    }

    /// Replay distribution product / marginal cases.
    pub fn replay_distributions(&self) -> Result<(), String> {
        for case in &self.distributions {
            let a = FinDistribution::new(case.a.n, case.a.masses.clone())
                .map_err(|e| format!("{}: a: {e}", case.case_id))?;
            let b = FinDistribution::new(case.b.n, case.b.masses.clone())
                .map_err(|e| format!("{}: b: {e}", case.case_id))?;
            if a.is_pure() != case.expected_a_pure {
                return Err(format!(
                    "{}: a.is_pure got {} want {}",
                    case.case_id,
                    a.is_pure(),
                    case.expected_a_pure
                ));
            }
            if a.is_mixed() != case.expected_a_mixed {
                return Err(format!(
                    "{}: a.is_mixed got {} want {}",
                    case.case_id,
                    a.is_mixed(),
                    case.expected_a_mixed
                ));
            }
            Self::verify_product_and_marginals(
                &case.case_id,
                &a,
                &b,
                &case.expected_product_masses,
                &case.expected_marg_a,
                &case.expected_marg_b,
            )?;
        }
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/core_wdp/src/coda/q/finite_shadow_exact.rs
// Claim: urn:core:crates_rs:core-wdp:finite-shadow-exact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn complete_system() -> FiniteShadowSystemExact {
        FiniteShadowSystemExact::new(
            vec!["declared_M1_projection".into(), "declared_M2_packet".into()],
            vec![("declared_M1_projection".into(), "declared_M2_packet".into())],
            Some("finite_matrix_norm_topology".into()),
            true,
            ExactNonNegRational::zero(),
            None,
        )
    }

    #[test]
    fn finite_query_replays_without_continuum() {
        let diag = complete_system().terminalize(false);
        assert_eq!(diag.status, ShadowStatus::Pass);
        assert_eq!(diag.terminal, ShadowTerminalLabel::FiniteShadowReplay);
        assert_eq!(diag.terminal_wire(), "FiniteShadowReplay");
        assert_eq!(diag.authority_effect, AUTHORITY_EFFECT_NONE);
        assert_eq!(
            diag.finite_qm_schema_version,
            FINITE_QM_CONTRACT_SCHEMA_VERSION
        );
    }

    #[test]
    fn continuum_without_witness_is_oracle_needed() {
        let diag = complete_system().terminalize(true);
        assert_eq!(diag.status, ShadowStatus::Conditional);
        assert_eq!(diag.terminal, ShadowTerminalLabel::OracleNeededConvergence);
        assert_eq!(diag.terminal_wire(), "OracleNeeded(Convergence)");
    }

    #[test]
    fn continuum_with_witness_is_finite_replay_only() {
        let sys = complete_system().with_convergence_witness("route=named-not-proved");
        let diag = sys.terminalize(true);
        assert_eq!(diag.status, ShadowStatus::Pass);
        assert_eq!(diag.terminal, ShadowTerminalLabel::FiniteShadowReplay);
    }

    #[test]
    fn empty_shadows_refuse() {
        let sys = FiniteShadowSystemExact::new(
            vec![],
            vec![("a".into(), "b".into())],
            Some("top".into()),
            true,
            ExactNonNegRational::zero(),
            None,
        );
        let diag = sys.terminalize(false);
        assert_eq!(diag.status, ShadowStatus::Refused);
        assert_eq!(diag.terminal, ShadowTerminalLabel::ShadowRefusal);
    }

    #[test]
    fn missing_topology_refuses() {
        let sys = FiniteShadowSystemExact::new(
            vec!["s".into()],
            vec![("s".into(), "s".into())],
            None,
            true,
            ExactNonNegRational::zero(),
            None,
        );
        assert_eq!(
            sys.terminalize(false).terminal,
            ShadowTerminalLabel::ShadowRefusal
        );
    }

    #[test]
    fn non_cofinal_refuses() {
        let sys = FiniteShadowSystemExact::new(
            vec!["s".into()],
            vec![("s".into(), "t".into())],
            Some("top".into()),
            false,
            ExactNonNegRational::zero(),
            None,
        );
        assert_eq!(
            sys.terminalize(false).terminal,
            ShadowTerminalLabel::ShadowRefusal
        );
    }

    #[test]
    fn fin_bit_product_and_marginals_exact() {
        let a = FinDistribution::bit(2, 3);
        let b = FinDistribution::bit(1, 0);
        assert!(a.is_mixed());
        assert!(b.is_pure());
        let j = a.product(&b).expect("product");
        assert_eq!(j.masses(), &[2, 0, 3, 0]);
        let marg_a = j.marginal_a(2).expect("marg_a");
        // marg_a scaled by total_b = 1 → (2, 3)
        assert_eq!(marg_a.masses(), &[2, 3]);
        let marg_b = j.marginal_b(2).expect("marg_b");
        assert_eq!(marg_b.masses(), &[5, 0]);
    }

    #[test]
    fn pure_joint_implies_pure_marginals() {
        let j = FinDistribution::new(4, vec![5, 0, 0, 0]).unwrap();
        assert!(j.is_pure());
        let ma = j.marginal_a(2).unwrap();
        let mb = j.marginal_b(2).unwrap();
        assert!(ma.is_pure());
        assert!(mb.is_pure());
    }

    #[test]
    fn mixed_bit_has_no_pure_classical_purification() {
        let fair = FinDistribution::bit(1, 1);
        assert!(fair.is_mixed());
        for mass in 1u64..5 {
            for pure in [
                FinDistribution::new(4, vec![mass, 0, 0, 0]).unwrap(),
                FinDistribution::new(4, vec![0, mass, 0, 0]).unwrap(),
                FinDistribution::new(4, vec![0, 0, mass, 0]).unwrap(),
                FinDistribution::new(4, vec![0, 0, 0, mass]).unwrap(),
            ] {
                assert!(pure.is_pure());
                let marg = pure.marginal_a(2).unwrap();
                assert_ne!(marg.masses(), fair.masses());
            }
        }
    }

    #[test]
    fn exact_probability_is_reduced() {
        let d = FinDistribution::bit(2, 2);
        let p0 = d.probability(0).unwrap();
        assert_eq!((p0.numer(), p0.denom()), (1, 2));
    }

    #[test]
    fn finite_qm_field_name_constants_match_contract() {
        assert_eq!(FINITE_QM_CONTRACT_SCHEMA_VERSION, "FiniteQMContractV1");
        assert_eq!(FINITE_QM_CONTRACT_URN, "urn:core:math:finite_qm:v1.0.0");
        assert_eq!(FIELD_CARRIER, "carrier");
        assert_eq!(FIELD_DIMENSION, "dimension");
        assert_eq!(FIELD_CERTIFICATE, "certificate");
        assert_eq!(FIELD_CONTINUUM_DEBT, "continuum_debt");
        assert_eq!(FIELD_IMPORT_LEDGER, "import_ledger");
        assert_eq!(FIELD_AUTHORITY_EFFECT, "authority_effect");
        assert_eq!(AUTHORITY_EFFECT_NONE, "None");
    }

    #[test]
    fn zero_denominator_refused() {
        assert_eq!(
            ExactNonNegRational::new(1, 0),
            Err(FiniteShadowExactError::ZeroDenominator)
        );
    }
}
