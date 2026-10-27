// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Canonical Layer IDs for the nine runtime stages of CODA.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[allow(non_camel_case_types)]
#[repr(u8)]
pub enum LayerId {
    FOC = 1,
    MUR = 2,
    CS = 3,
    CS_Q = 4,
    Q = 5,
    A = 6,
    OR = 7,
    FDA = 8,
    #[serde(rename = "GTLA")]
    CODA_GTLA = 9,
}

impl LayerId {
    pub fn name(&self) -> &'static str {
        match self {
            LayerId::FOC => "FOC",
            LayerId::MUR => "MUR",
            LayerId::CS => "CS",
            LayerId::CS_Q => "CS_Q",
            LayerId::Q => "Q",
            LayerId::A => "A",
            LayerId::OR => "OR",
            LayerId::FDA => "FDA",
            LayerId::CODA_GTLA => "GTLA",
        }
    }
}

/// Audit record emitted by each CODA layer evaluation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LayerExecutionRecord {
    pub layer_id: LayerId,
    pub succeeded: bool,
    pub diagnostic_message: String,
    pub defect_mass: BigRational,
    pub metadata: BTreeMap<String, serde_json::Value>,
}

impl LayerExecutionRecord {
    pub fn new(
        layer_id: LayerId,
        succeeded: bool,
        diagnostic_message: impl Into<String>,
        defect_mass: BigRational,
    ) -> Self {
        Self {
            layer_id,
            succeeded,
            diagnostic_message: diagnostic_message.into(),
            defect_mass,
            metadata: BTreeMap::new(),
        }
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: serde_json::Value) -> Self {
        self.metadata.insert(key.into(), value);
        self
    }
}

/// Machine-verifiable dual witness functional certifying an exact quotient obstruction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DualWitness {
    pub vector: Vec<BigRational>,
    pub linfty_norm: BigRational,
    pub pairing_value: BigRational,
}

impl DualWitness {
    pub fn new(vector: Vec<BigRational>, pairing_value: BigRational) -> Self {
        let mut max_abs = BigRational::from_integer(0.into());
        for v in &vector {
            let abs_v = if v < &BigRational::from_integer(0.into()) {
                -v.clone()
            } else {
                v.clone()
            };
            if abs_v > max_abs {
                max_abs = abs_v;
            }
        }
        Self {
            vector,
            linfty_norm: max_abs,
            pairing_value,
        }
    }
}

/// Machine-verifiable curved constrained dual witness functional certifying a closure-constrained repair obstruction.
///
/// Satisfies the coupled annihilator condition:
/// ```text
/// d0^T y + K^T z = 0,   where K = d1 * d0
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CurvedDualWitness {
    pub dual_y: Vec<BigRational>,
    pub dual_z: Vec<BigRational>,
    pub dual_lambda: BigRational,
    pub tau: BigRational,
    pub objective: BigRational,
    pub linfty_norm_y: BigRational,
}

impl CurvedDualWitness {
    pub fn new(
        dual_y: Vec<BigRational>,
        dual_z: Vec<BigRational>,
        dual_lambda: BigRational,
        tau: BigRational,
        objective: BigRational,
    ) -> Self {
        let mut max_abs = BigRational::from_integer(0.into());
        for v in &dual_y {
            let abs_v = if v < &BigRational::from_integer(0.into()) {
                -v.clone()
            } else {
                v.clone()
            };
            if abs_v > max_abs {
                max_abs = abs_v;
            }
        }
        Self {
            dual_y,
            dual_z,
            dual_lambda,
            tau,
            objective,
            linfty_norm_y: max_abs,
        }
    }

    /// Checks the coupled annihilator condition: d0^T y + K^T z = 0 in Q^n.
    ///
    /// d0 is m x n, y is m, so d0^T y is n.
    /// K is p x n, z is p, so K^T z is n.
    pub fn verify_coupled_annihilator(
        &self,
        d0: &[Vec<BigRational>],
        k: &[Vec<BigRational>],
    ) -> bool {
        let m = d0.len();
        if self.dual_y.len() != m {
            return false;
        }
        let n = if m > 0 { d0[0].len() } else { 0 };
        let p = k.len();
        if self.dual_z.len() != p {
            return false;
        }
        for row in k {
            if row.len() != n {
                return false;
            }
        }

        for j in 0..n {
            let mut sum = BigRational::zero();
            // (d0^T y)_j = sum_{i=0}^{m-1} d0[i][j] * y[i]
            for i in 0..m {
                sum += &d0[i][j] * &self.dual_y[i];
            }
            // (K^T z)_j = sum_{r=0}^{p-1} K[r][j] * z[r]
            for r in 0..p {
                sum += &k[r][j] * &self.dual_z[r];
            }
            if !sum.is_zero() {
                return false;
            }
        }
        true
    }
}

/// Distinct proof-carrying certificate payload variants for flat vs curved quotient/obstruction verification.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "variant", content = "certificate")]
pub enum ObstructionWitnessPayload {
    /// Exact quotient obstruction witness certifying d0^T y = 0, ||y||_infty <= 1, <y, x> = phi1 > 0.
    FlatQuotient(DualWitness),
    /// Coupled curved constrained witness certifying d0^T y + K^T z = 0 with dual multiplier lambda.
    CurvedConstrained(CurvedDualWitness),
}

impl ObstructionWitnessPayload {
    pub fn flat(witness: DualWitness) -> Self {
        Self::FlatQuotient(witness)
    }

    pub fn curved(witness: CurvedDualWitness) -> Self {
        Self::CurvedConstrained(witness)
    }

    pub fn dual_y(&self) -> &[BigRational] {
        match self {
            Self::FlatQuotient(w) => &w.vector,
            Self::CurvedConstrained(w) => &w.dual_y,
        }
    }

    pub fn objective(&self) -> &BigRational {
        match self {
            Self::FlatQuotient(w) => &w.pairing_value,
            Self::CurvedConstrained(w) => &w.objective,
        }
    }

    pub fn is_curved(&self) -> bool {
        matches!(self, Self::CurvedConstrained(_))
    }

    pub fn is_flat(&self) -> bool {
        matches!(self, Self::FlatQuotient(_))
    }

    pub fn as_flat(&self) -> Option<&DualWitness> {
        match self {
            Self::FlatQuotient(w) => Some(w),
            _ => None,
        }
    }

    pub fn as_curved(&self) -> Option<&CurvedDualWitness> {
        match self {
            Self::CurvedConstrained(w) => Some(w),
            _ => None,
        }
    }
}

/// Firewall routing decision for Layer 8 FDA.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum FirewallDecision {
    PermitAuthorized,
    RouteClosedResidual,
    RouteRefused,
}

/// Definitive 3-way disjoint coproduct partition for Master Normal Form.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum TerminalKind {
    Authorized,
    ClosedResidual,
    Refused,
}

/// Legacy authority-token metadata; no verification is provided by this crate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityToken {
    pub token_id: String,
    pub granted_externally: bool,
    pub grantee: String,
    pub evidence_digest: String,
    pub timestamp_iso: String,
}

/// Evaluated residual pair (Phi_1, Gamma_2).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResidualPair {
    pub phi1: BigRational,
    pub gamma2: BigRational,
}

impl ResidualPair {
    pub fn new(phi1: BigRational, gamma2: BigRational) -> Self {
        Self { phi1, gamma2 }
    }

    pub fn is_exact_zero(&self) -> bool {
        self.phi1 == BigRational::from_integer(0.into())
            && self.gamma2 == BigRational::from_integer(0.into())
    }

    pub fn is_coherent(&self) -> bool {
        self.gamma2 == BigRational::from_integer(0.into())
    }
}

/// Untrusted grant request; strings do not verify a signer, scope, or freshness.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalAuthorityGrant {
    pub grant_id: String,
    pub signature_hex: String,
    pub grantee: String,
}

/// Canonical problem instance containing finite cochains, profiles, and sections.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProblemInstance {
    pub problem_id: String,
    pub raw_data: String,
    pub candidate_sieve: Vec<String>,
    pub coarse_profile: Vec<i64>,
    pub fine_profile: Vec<i64>,
    pub projection_map: BTreeMap<i64, i64>,
    pub local_sections: BTreeMap<String, Vec<BigRational>>,
    pub overlaps: BTreeMap<(String, String), bool>,
    pub d0: Vec<Vec<BigRational>>,
    pub d1: Vec<Vec<BigRational>>,
    pub defect_cochain: Vec<BigRational>,
    pub fda_license_granted: bool,
    pub enclosure_interval: (BigRational, BigRational),
}

impl ProblemInstance {
    pub fn new(problem_id: impl Into<String>) -> Self {
        Self {
            problem_id: problem_id.into(),
            raw_data: String::new(),
            candidate_sieve: Vec::new(),
            coarse_profile: Vec::new(),
            fine_profile: Vec::new(),
            projection_map: BTreeMap::new(),
            local_sections: BTreeMap::new(),
            overlaps: BTreeMap::new(),
            d0: Vec::new(),
            d1: Vec::new(),
            defect_cochain: Vec::new(),
            fda_license_granted: false,
            enclosure_interval: (
                BigRational::from_integer(0.into()),
                BigRational::from_integer(1.into()),
            ),
        }
    }
}

/// Definitive outcome of the 9-stage Master Normal Form pipeline.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MasterNormalFormOutcome {
    pub problem_id: String,
    pub terminal_kind: TerminalKind,
    pub residual_pair: Option<ResidualPair>,
    pub dual_witness: Option<DualWitness>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub witness_payload: Option<ObstructionWitnessPayload>,
    pub authority_token: Option<AuthorityToken>,
    pub layer_records: Vec<LayerExecutionRecord>,
    pub firewall_decision: FirewallDecision,
    pub reason: String,
    pub primal_repair: Option<Vec<BigRational>>,
    pub evidence_digest: String,
}

impl MasterNormalFormOutcome {
    pub fn is_authorized(&self) -> bool {
        self.terminal_kind == TerminalKind::Authorized
    }

    pub fn is_closed_residual(&self) -> bool {
        self.terminal_kind == TerminalKind::ClosedResidual
    }

    pub fn is_refused(&self) -> bool {
        self.terminal_kind == TerminalKind::Refused
    }

    pub fn witness_payload(&self) -> Option<&ObstructionWitnessPayload> {
        self.witness_payload.as_ref()
    }

    pub fn is_curved_obstruction(&self) -> bool {
        self.witness_payload
            .as_ref()
            .map_or(false, |p| p.is_curved())
    }

    pub fn is_flat_obstruction(&self) -> bool {
        self.witness_payload
            .as_ref()
            .map_or(false, |p| p.is_flat())
    }

    pub fn curved_witness(&self) -> Option<&CurvedDualWitness> {
        self.witness_payload.as_ref().and_then(|p| p.as_curved())
    }

    pub fn flat_witness(&self) -> Option<&DualWitness> {
        self.witness_payload.as_ref().and_then(|p| p.as_flat())
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/types.rs
// Claim: urn:core:crates_rs:core-wdp:types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9eae1064 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9eae1064` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9eae1064 {
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
impl BoundaryError9eae1064 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9eae1064 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9eae1064 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9eae1064 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9eae1064> {
        if capacity_bound == 0 {
            return Err(BoundaryError9eae1064::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9eae1064::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9eae1064::ExceedsCapacity {
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
mod l4_boundary_tests_9eae1064 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9eae1064::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9eae1064::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9eae1064::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9eae1064::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9eae1064::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9eae1064::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9eae1064::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
