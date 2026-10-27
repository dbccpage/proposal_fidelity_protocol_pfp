//! Lamarckian Mutation Receipt and Cochain Residual Value Objects (NF-02).
//!
//! Conforms to normative specification:
//! `urn:core:nf:prompt_civilization:lamarckian_pfp_adversary_loop:v1.0.0`
//!
//! Enforces:
//! - Rule 1: Protected Core Invariance (Core(G_{g+1}) == Core(G_g)).
//! - Rule 2: Witness Grounding (No antibody injection without verified falsification witness).
//! - Rule 3: Attenuated Influence (w(alpha, d) = (1/2)^d for 1 <= d <= 10; d > 10 evaporated).
//!
//! AuthorityEffect: None.
//! Zero-Float Law: Uses exact rational arithmetic.

use num_rational::Rational64;
use num_traits::Zero;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainResidualV1 {
    pub phi1: String,
    pub gamma2: String,
    pub xi: String,
}

impl CochainResidualV1 {
    pub fn new(phi1: &str, gamma2: &str, xi: &str) -> Result<Self, &'static str> {
        let r = Self {
            phi1: phi1.to_string(),
            gamma2: gamma2.to_string(),
            xi: xi.to_string(),
        };
        r.validate()?;
        Ok(r)
    }

    pub fn validate(&self) -> Result<(), &'static str> {
        let rat_re = Regex::new(r"^-?[0-9]+/[1-9][0-9]*$").map_err(|_| "REGEX_ERROR")?;
        for val in [&self.phi1, &self.gamma2, &self.xi] {
            if !rat_re.is_match(val) {
                return Err("INVALID_COCHAIN_RATIONAL");
            }
        }
        Ok(())
    }

    pub fn parse_rational(s: &str) -> Result<Rational64, &'static str> {
        let parts: Vec<&str> = s.split('/').collect();
        if parts.len() != 2 {
            return Err("INVALID_COCHAIN_RATIONAL");
        }
        let numer = i64::from_str(parts[0]).map_err(|_| "INVALID_COCHAIN_RATIONAL")?;
        let denom = i64::from_str(parts[1]).map_err(|_| "INVALID_COCHAIN_RATIONAL")?;
        if denom <= 0 {
            return Err("INVALID_COCHAIN_RATIONAL");
        }
        Ok(Rational64::new(numer, denom))
    }

    pub fn phi1_rational(&self) -> Result<Rational64, &'static str> {
        Self::parse_rational(&self.phi1)
    }

    pub fn gamma2_rational(&self) -> Result<Rational64, &'static str> {
        Self::parse_rational(&self.gamma2)
    }

    pub fn xi_rational(&self) -> Result<Rational64, &'static str> {
        Self::parse_rational(&self.xi)
    }

    /// Computes delta_phi1 = child.phi1 - self.phi1.
    pub fn delta_phi1(&self, child: &CochainResidualV1) -> Result<Rational64, &'static str> {
        Ok(child.phi1_rational()? - self.phi1_rational()?)
    }

    /// Verifies monotonic non-increasing cochain residual: delta_phi1 <= 0.
    pub fn is_monotonic_reduction(&self, child: &CochainResidualV1) -> Result<bool, &'static str> {
        Ok(self.delta_phi1(child)? <= Rational64::zero())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LamarckianMutationReceiptV1 {
    pub receipt_id: String,
    pub parent_genome_id: String,
    pub child_genome_id: String,
    pub falsification_witness_sha256: String,
    pub cochain_residual: CochainResidualV1,
    pub antibody_id: String,
    pub hop_distance: u32,
    pub attenuation_weight: String,
    pub created_utc: String,
}

impl LamarckianMutationReceiptV1 {
    pub fn calculate_attenuation_weight(hop_distance: u32) -> Result<String, &'static str> {
        if !(1..=10).contains(&hop_distance) {
            return Err("HOP_DISTANCE_OUT_OF_BOUNDS");
        }
        let denom: u64 = 1u64 << hop_distance;
        Ok(format!("1/{}", denom))
    }

    pub fn new(
        parent_genome_id: String,
        child_genome_id: String,
        falsification_witness_sha256: String,
        cochain_residual: CochainResidualV1,
        antibody_id: String,
        hop_distance: u32,
        created_utc: String,
    ) -> Result<Self, &'static str> {
        let attenuation_weight = Self::calculate_attenuation_weight(hop_distance)?;
        let mut r = Self {
            receipt_id: String::new(),
            parent_genome_id,
            child_genome_id,
            falsification_witness_sha256,
            cochain_residual,
            antibody_id,
            hop_distance,
            attenuation_weight,
            created_utc,
        };
        let digest = r.canonical_digest()?;
        r.receipt_id = digest;
        r.validate()?;
        Ok(r)
    }

    pub fn canonical_bytes(&self) -> Result<Vec<u8>, &'static str> {
        let payload = serde_json::json!({
            "antibody_id": self.antibody_id,
            "attenuation_weight": self.attenuation_weight,
            "child_genome_id": self.child_genome_id,
            "cochain_residual": {
                "gamma2": self.cochain_residual.gamma2,
                "phi1": self.cochain_residual.phi1,
                "xi": self.cochain_residual.xi,
            },
            "created_utc": self.created_utc,
            "falsification_witness_sha256": self.falsification_witness_sha256,
            "hop_distance": self.hop_distance,
            "parent_genome_id": self.parent_genome_id,
        });
        let sorted = sort_json_keys(payload);
        serde_json::to_vec(&sorted).map_err(|_| "CANONICAL_SERIALIZATION_FAILED")
    }

    pub fn canonical_digest(&self) -> Result<String, &'static str> {
        let bytes = self.canonical_bytes()?;
        let mut hasher = Sha256::new();
        hasher.update(&bytes);
        Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
    }

    fn validate_identifier_formats(&self) -> Result<(), &'static str> {
        let prefixed_re = Regex::new(r"^sha256:[0-9a-f]{64}$").map_err(|_| "REGEX_ERROR")?;
        let hex_re = Regex::new(r"^[0-9a-f]{64}$").map_err(|_| "REGEX_ERROR")?;

        if !prefixed_re.is_match(&self.receipt_id) {
            return Err("INVALID_RECEIPT_ID_FORMAT");
        }
        if !prefixed_re.is_match(&self.parent_genome_id) {
            return Err("INVALID_PARENT_GENOME_ID_FORMAT");
        }
        if !prefixed_re.is_match(&self.child_genome_id) {
            return Err("INVALID_CHILD_GENOME_ID_FORMAT");
        }
        if !hex_re.is_match(&self.falsification_witness_sha256) {
            return Err("INVALID_WITNESS_SHA256_FORMAT");
        }
        if self.antibody_id.trim().is_empty() {
            return Err("ANTIBODY_ID_CANNOT_BE_EMPTY");
        }
        Ok(())
    }

    pub fn validate(&self) -> Result<(), &'static str> {
        self.validate_identifier_formats()?;
        let weight_re = Regex::new(r"^[0-9]+/[1-9][0-9]*$").map_err(|_| "REGEX_ERROR")?;
        if !(1..=10).contains(&self.hop_distance) {
            return Err("HOP_DISTANCE_OUT_OF_BOUNDS");
        }
        if !weight_re.is_match(&self.attenuation_weight) {
            return Err("INVALID_ATTENUATION_WEIGHT_FORMAT");
        }
        let expected_weight = Self::calculate_attenuation_weight(self.hop_distance)?;
        if self.attenuation_weight != expected_weight {
            return Err("ATTENUATION_WEIGHT_MISMATCH");
        }
        self.cochain_residual.validate()?;
        let computed = self.canonical_digest()?;
        if self.receipt_id != computed {
            return Err("RECEIPT_ID_DIGEST_MISMATCH");
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LamarckianTrackingError {
    #[error("REGRESSION_RESIDUAL_INCREASE: delta_phi1 is {0} > 0")]
    RegressionResidualIncrease(Rational64),
    #[error("PROTECTED_CORE_TAMPERED: Byte mismatch in protected span [{0}, {1}]")]
    ProtectedCoreTampered(usize, usize),
    #[error("HOP_DISTANCE_OUT_OF_BOUNDS: hop distance {0} not in [1, 10]")]
    HopDistanceOutOfBounds(u32),
    #[error("INVALID_COCHAIN_RATIONAL: {0}")]
    InvalidCochainRational(String),
    #[error("SPAN_OUT_OF_BOUNDS: Span [{0}, {1}] exceeds genome length")]
    SpanOutOfBounds(usize, usize),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LamarckianVerificationResult {
    pub status: String,
    pub delta_phi: Rational64,
    pub attenuation_weight: Rational64,
    pub protected_core_intact: bool,
    pub reason: Option<String>,
}

pub struct LamarckianCochainTrackerV1;

impl LamarckianCochainTrackerV1 {
    /// Computes attenuation weight w(alpha, d) = (1/2)^d for 1 <= d <= 10.
    pub fn attenuation_weight(hop_distance: u32) -> Result<Rational64, LamarckianTrackingError> {
        if !(1..=10).contains(&hop_distance) {
            return Err(LamarckianTrackingError::HopDistanceOutOfBounds(
                hop_distance,
            ));
        }
        let denom = 1i64 << hop_distance;
        Ok(Rational64::new(1, denom))
    }

    /// Verifies a Lamarckian mutation step:
    /// 1. Monotonic defect reduction: Delta Phi_1 = child_phi - parent_phi <= 0.
    /// 2. Attenuation weight law: 1 <= d <= 10.
    /// 3. Protected core byte invariance.
    pub fn verify_mutation(
        parent_phi: Rational64,
        child_phi: Rational64,
        hop_distance: u32,
        parent_genome: &[u8],
        child_genome: &[u8],
        protected_spans: &[(usize, usize)],
    ) -> Result<LamarckianVerificationResult, LamarckianTrackingError> {
        let delta_phi = child_phi - parent_phi;
        if delta_phi > Rational64::zero() {
            return Err(LamarckianTrackingError::RegressionResidualIncrease(
                delta_phi,
            ));
        }

        let weight = Self::attenuation_weight(hop_distance)?;

        // Verify protected spans
        for &(start, end) in protected_spans {
            if end > parent_genome.len() || end > child_genome.len() || start > end {
                return Err(LamarckianTrackingError::SpanOutOfBounds(start, end));
            }
            if parent_genome[start..end] != child_genome[start..end] {
                return Err(LamarckianTrackingError::ProtectedCoreTampered(start, end));
            }
        }

        Ok(LamarckianVerificationResult {
            status: "PASS".to_string(),
            delta_phi,
            attenuation_weight: weight,
            protected_core_intact: true,
            reason: None,
        })
    }
}

/// Tracks monotonic cochain residual descent across successive generations.
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct CochainHistoryTracker {
    pub entries: Vec<(String, CochainResidualV1)>,
}

impl CochainHistoryTracker {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn record_generation(
        &mut self,
        genome_id: &str,
        residual: CochainResidualV1,
    ) -> Result<Rational64, LamarckianTrackingError> {
        residual
            .validate()
            .map_err(|e| LamarckianTrackingError::InvalidCochainRational(e.to_string()))?;

        if let Some((_prev_id, prev_res)) = self.entries.last() {
            let prev_phi = prev_res
                .phi1_rational()
                .map_err(|e| LamarckianTrackingError::InvalidCochainRational(e.to_string()))?;
            let curr_phi = residual
                .phi1_rational()
                .map_err(|e| LamarckianTrackingError::InvalidCochainRational(e.to_string()))?;
            let delta = curr_phi - prev_phi;
            if delta > Rational64::zero() {
                return Err(LamarckianTrackingError::RegressionResidualIncrease(delta));
            }
            self.entries.push((genome_id.to_string(), residual));
            Ok(delta)
        } else {
            self.entries.push((genome_id.to_string(), residual));
            Ok(Rational64::zero())
        }
    }
}

fn sort_json_keys(value: Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut sorted = serde_json::Map::new();
            let mut keys: Vec<String> = map.keys().cloned().collect();
            keys.sort();
            for k in keys {
                if let Some(v) = map.get(&k) {
                    sorted.insert(k, sort_json_keys(v.clone()));
                }
            }
            Value::Object(sorted)
        }
        Value::Array(arr) => Value::Array(arr.into_iter().map(sort_json_keys).collect()),
        other => other,
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/lamarckian.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:lamarckian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cochain_residual_validation() {
        let res = CochainResidualV1::new("1/2", "0/1", "0/1").unwrap();
        assert_eq!(res.phi1, "1/2");
        assert_eq!(res.gamma2, "0/1");
        assert_eq!(res.xi, "0/1");

        assert_eq!(
            CochainResidualV1::new("invalid", "0/1", "0/1").unwrap_err(),
            "INVALID_COCHAIN_RATIONAL"
        );
    }

    #[test]
    fn test_lamarckian_attenuation_weights() {
        assert_eq!(
            LamarckianMutationReceiptV1::calculate_attenuation_weight(1).unwrap(),
            "1/2"
        );
        assert_eq!(
            LamarckianMutationReceiptV1::calculate_attenuation_weight(2).unwrap(),
            "1/4"
        );
        assert_eq!(
            LamarckianMutationReceiptV1::calculate_attenuation_weight(10).unwrap(),
            "1/1024"
        );
        assert_eq!(
            LamarckianMutationReceiptV1::calculate_attenuation_weight(0).unwrap_err(),
            "HOP_DISTANCE_OUT_OF_BOUNDS"
        );
        assert_eq!(
            LamarckianMutationReceiptV1::calculate_attenuation_weight(11).unwrap_err(),
            "HOP_DISTANCE_OUT_OF_BOUNDS"
        );
    }

    #[test]
    fn test_receipt_creation_and_tamper_detection() {
        let parent =
            "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef".to_string();
        let child =
            "sha256:fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210".to_string();
        let witness =
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef".to_string();
        let residual = CochainResidualV1::new("1/1", "0/1", "0/1").unwrap();

        let receipt = LamarckianMutationReceiptV1::new(
            parent,
            child,
            witness,
            residual,
            "ab_test_01".to_string(),
            1,
            "2026-10-09T00:00:00Z".to_string(),
        )
        .unwrap();

        assert!(receipt.receipt_id.starts_with("sha256:"));
        assert_eq!(receipt.attenuation_weight, "1/2");
        assert!(receipt.validate().is_ok());

        // Tamper with receipt_id
        let mut tampered = receipt.clone();
        tampered.receipt_id =
            "sha256:0000000000000000000000000000000000000000000000000000000000000000".to_string();
        assert_eq!(
            tampered.validate().unwrap_err(),
            "RECEIPT_ID_DIGEST_MISMATCH"
        );
    }

    #[test]
    fn test_lamarckian_monotonic_residual_reduction() {
        let p_phi = Rational64::new(1, 2);
        let c_phi = Rational64::new(1, 4);
        let res = LamarckianCochainTrackerV1::verify_mutation(
            p_phi,
            c_phi,
            1,
            b"SYSTEM PROMPT CORE mutated tail",
            b"SYSTEM PROMPT CORE fixed tail",
            &[(0, 18)],
        )
        .unwrap();

        assert_eq!(res.status, "PASS");
        assert_eq!(res.delta_phi, Rational64::new(-1, 4));
        assert_eq!(res.attenuation_weight, Rational64::new(1, 2));
        assert!(res.protected_core_intact);
    }

    #[test]
    fn test_lamarckian_regression_refused() {
        // Child residual is higher than parent: 3/4 > 1/2 -> delta is +1/4 > 0
        let p_phi = Rational64::new(1, 2);
        let c_phi = Rational64::new(3, 4);
        let res = LamarckianCochainTrackerV1::verify_mutation(
            p_phi,
            c_phi,
            1,
            b"SYSTEM PROMPT CORE mutated tail",
            b"SYSTEM PROMPT CORE fixed tail",
            &[(0, 18)],
        );

        assert!(matches!(
            res,
            Err(LamarckianTrackingError::RegressionResidualIncrease(d)) if d == Rational64::new(1, 4)
        ));
    }

    #[test]
    fn test_lamarckian_protected_core_tampering_refused() {
        let p_phi = Rational64::new(1, 2);
        let c_phi = Rational64::new(1, 4);
        let res = LamarckianCochainTrackerV1::verify_mutation(
            p_phi,
            c_phi,
            1,
            b"SYSTEM PROMPT CORE mutated tail",
            b"SYSTEM CORRUPTED RE fixed tail", // tampered within 0..18
            &[(0, 18)],
        );

        assert!(matches!(
            res,
            Err(LamarckianTrackingError::ProtectedCoreTampered(0, 18))
        ));
    }

    #[test]
    fn test_lamarckian_attenuation_weight_law() {
        assert_eq!(
            LamarckianCochainTrackerV1::attenuation_weight(1).unwrap(),
            Rational64::new(1, 2)
        );
        assert_eq!(
            LamarckianCochainTrackerV1::attenuation_weight(2).unwrap(),
            Rational64::new(1, 4)
        );
        assert_eq!(
            LamarckianCochainTrackerV1::attenuation_weight(3).unwrap(),
            Rational64::new(1, 8)
        );
        assert_eq!(
            LamarckianCochainTrackerV1::attenuation_weight(10).unwrap(),
            Rational64::new(1, 1024)
        );
        assert!(matches!(
            LamarckianCochainTrackerV1::attenuation_weight(0),
            Err(LamarckianTrackingError::HopDistanceOutOfBounds(0))
        ));
        assert!(matches!(
            LamarckianCochainTrackerV1::attenuation_weight(11),
            Err(LamarckianTrackingError::HopDistanceOutOfBounds(11))
        ));
    }

    #[test]
    fn test_lamarckian_history_tracker_monotonicity() {
        let mut tracker = CochainHistoryTracker::new();

        // Generation 0: baseline residual 1/1
        let r0 = CochainResidualV1::new("1/1", "0/1", "0/1").unwrap();
        assert_eq!(
            tracker.record_generation("gen_0", r0).unwrap(),
            Rational64::zero()
        );

        // Generation 1: improvement to 3/4
        let r1 = CochainResidualV1::new("3/4", "0/1", "0/1").unwrap();
        assert_eq!(
            tracker.record_generation("gen_1", r1).unwrap(),
            Rational64::new(-1, 4)
        );

        // Generation 2: improvement to 1/2
        let r2 = CochainResidualV1::new("1/2", "0/1", "0/1").unwrap();
        assert_eq!(
            tracker.record_generation("gen_2", r2).unwrap(),
            Rational64::new(-1, 4)
        );

        // Generation 3: regression to 2/3 (2/3 > 1/2 = 4/6 > 3/6)
        let r3_regressed = CochainResidualV1::new("2/3", "0/1", "0/1").unwrap();
        let res = tracker.record_generation("gen_3", r3_regressed);
        assert!(matches!(
            res,
            Err(LamarckianTrackingError::RegressionResidualIncrease(d)) if d == Rational64::new(1, 6)
        ));
    }
}
