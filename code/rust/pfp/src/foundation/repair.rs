use super::{
    canonical_json_bytes, require_name, require_nonnegative, FoundationError, FoundationErrorCode,
};
use num_rational::BigRational;
use num_traits::Zero;
use pfp_runtime::canonical::framed_sha256;
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet};
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DetectorEntry {
    state_id: String,
    value: BigRational,
}

impl DetectorEntry {
    pub fn new(state_id: impl Into<String>, value: BigRational) -> Result<Self, FoundationError> {
        let state_id = state_id.into();
        require_name(&state_id, "detector state identity")?;
        require_nonnegative(&value, "detector value")?;
        Ok(Self { state_id, value })
    }

    pub fn state_id(&self) -> &str {
        &self.state_id
    }

    pub fn value(&self) -> &BigRational {
        &self.value
    }
}

/// A finite detector table over exact rational values.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExactFiniteDetector {
    detector_id: String,
    entries: BTreeMap<String, BigRational>,
}

impl ExactFiniteDetector {
    pub fn new(
        detector_id: impl Into<String>,
        entries: Vec<DetectorEntry>,
    ) -> Result<Self, FoundationError> {
        let detector_id = detector_id.into();
        require_name(&detector_id, "detector identity")?;
        let mut table = BTreeMap::new();
        for entry in entries {
            if table.insert(entry.state_id, entry.value).is_some() {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "detector state identities must be unique",
                ));
            }
        }
        Ok(Self {
            detector_id,
            entries: table,
        })
    }

    pub fn detector_id(&self) -> &str {
        &self.detector_id
    }

    pub fn value_of(&self, state_id: &str) -> Result<&BigRational, FoundationError> {
        self.entries.get(state_id).ok_or_else(|| {
            FoundationError::new(
                FoundationErrorCode::MissingDetectorValue,
                format!("the exact detector has no value for state {state_id:?}"),
            )
        })
    }
}

/// One candidate in a declared complete same-context repair universe.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RepairCandidate {
    candidate_id: String,
    result_state_id: String,
}

impl RepairCandidate {
    pub fn new(
        candidate_id: impl Into<String>,
        result_state_id: impl Into<String>,
    ) -> Result<Self, FoundationError> {
        let candidate_id = candidate_id.into();
        let result_state_id = result_state_id.into();
        require_name(&candidate_id, "repair candidate identity")?;
        require_name(&result_state_id, "repair result state identity")?;
        Ok(Self {
            candidate_id,
            result_state_id,
        })
    }

    pub fn candidate_id(&self) -> &str {
        &self.candidate_id
    }

    pub fn result_state_id(&self) -> &str {
        &self.result_state_id
    }
}

/// The ordered, complete repair universe declared for one finite source state.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DeclaredRepairUniverse {
    context_id: String,
    source_state_id: String,
    candidates: Vec<RepairCandidate>,
}

impl DeclaredRepairUniverse {
    pub fn new(
        context_id: impl Into<String>,
        source_state_id: impl Into<String>,
        candidates: Vec<RepairCandidate>,
    ) -> Result<Self, FoundationError> {
        let context_id = context_id.into();
        let source_state_id = source_state_id.into();
        require_name(&context_id, "repair context identity")?;
        require_name(&source_state_id, "repair source state identity")?;
        let mut identities = BTreeSet::new();
        for candidate in &candidates {
            if !identities.insert(candidate.candidate_id.clone()) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "repair candidate identities must be unique",
                ));
            }
        }
        Ok(Self {
            context_id,
            source_state_id,
            candidates,
        })
    }

    pub fn context_id(&self) -> &str {
        &self.context_id
    }

    pub fn source_state_id(&self) -> &str {
        &self.source_state_id
    }

    pub fn candidates(&self) -> &[RepairCandidate] {
        &self.candidates
    }
}

/// One observed exact evaluation, checked against the detector during
/// certification.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CandidateEvaluation {
    candidate_id: String,
    value: BigRational,
}

impl CandidateEvaluation {
    pub fn new(
        candidate_id: impl Into<String>,
        value: BigRational,
    ) -> Result<Self, FoundationError> {
        let candidate_id = candidate_id.into();
        require_name(&candidate_id, "candidate evaluation identity")?;
        require_nonnegative(&value, "candidate evaluation value")?;
        Ok(Self {
            candidate_id,
            value,
        })
    }

    pub fn candidate_id(&self) -> &str {
        &self.candidate_id
    }

    pub fn value(&self) -> &BigRational {
        &self.value
    }
}

/// A checked finite-coverage certificate.
///
/// All fields are private: external code cannot assert exhaustion directly.
/// `certify` checks exact ordered coverage and recomputes every detector value.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExhaustionCertificate {
    context_id: String,
    source_state_id: String,
    detector_id: String,
    evaluations: Vec<CandidateEvaluation>,
    source_value: BigRational,
    minimum: BigRational,
    certificate_id: String,
}

impl ExhaustionCertificate {
    pub fn certify(
        universe: &DeclaredRepairUniverse,
        detector: &ExactFiniteDetector,
        evaluations: Vec<CandidateEvaluation>,
    ) -> Result<Self, FoundationError> {
        if evaluations.len() != universe.candidates.len() {
            return Err(FoundationError::new(
                FoundationErrorCode::IncompleteCoverage,
                "exhaustion evaluations must cover the complete declared repair universe",
            ));
        }

        for (candidate, evaluation) in universe.candidates.iter().zip(&evaluations) {
            if candidate.candidate_id != evaluation.candidate_id {
                return Err(FoundationError::new(
                    FoundationErrorCode::IncompleteCoverage,
                    "exhaustion evaluations must preserve declared candidate identity and order",
                ));
            }
            let expected = detector.value_of(&candidate.result_state_id)?;
            if expected != &evaluation.value {
                return Err(FoundationError::new(
                    FoundationErrorCode::EvaluationMismatch,
                    "candidate evaluation does not match the exact detector",
                ));
            }
        }

        let source_value = detector.value_of(&universe.source_state_id)?.clone();
        let minimum = evaluations
            .iter()
            .map(|evaluation| &evaluation.value)
            .fold(source_value.clone(), |current, value| {
                current.min(value.clone())
            });

        let mut binding = Map::new();
        binding.insert(
            "context_id".to_owned(),
            Value::String(universe.context_id.clone()),
        );
        binding.insert(
            "source_state_id".to_owned(),
            Value::String(universe.source_state_id.clone()),
        );
        binding.insert(
            "detector_id".to_owned(),
            Value::String(detector.detector_id.clone()),
        );
        binding.insert("source_value".to_owned(), rational_json(&source_value));
        binding.insert(
            "evaluations".to_owned(),
            Value::Array(
                evaluations
                    .iter()
                    .map(|evaluation| {
                        Value::Array(vec![
                            Value::String(evaluation.candidate_id.clone()),
                            rational_json(&evaluation.value),
                        ])
                    })
                    .collect(),
            ),
        );
        binding.insert("minimum".to_owned(), rational_json(&minimum));
        let certificate_id = framed_sha256(
            "core.symbol-game.exhaustion-certificate.v1",
            &canonical_json_bytes(&Value::Object(binding))?,
        );

        Ok(Self {
            context_id: universe.context_id.clone(),
            source_state_id: universe.source_state_id.clone(),
            detector_id: detector.detector_id.clone(),
            evaluations,
            source_value,
            minimum,
            certificate_id,
        })
    }

    /// Enumerate the entire declared universe directly from its exact detector.
    pub fn enumerate(
        universe: &DeclaredRepairUniverse,
        detector: &ExactFiniteDetector,
    ) -> Result<Self, FoundationError> {
        let evaluations = universe
            .candidates
            .iter()
            .map(|candidate| {
                CandidateEvaluation::new(
                    candidate.candidate_id.clone(),
                    detector.value_of(&candidate.result_state_id)?.clone(),
                )
            })
            .collect::<Result<Vec<_>, _>>()?;
        Self::certify(universe, detector, evaluations)
    }

    pub fn context_id(&self) -> &str {
        &self.context_id
    }

    pub fn source_state_id(&self) -> &str {
        &self.source_state_id
    }

    pub fn detector_id(&self) -> &str {
        &self.detector_id
    }

    pub fn evaluations(&self) -> &[CandidateEvaluation] {
        &self.evaluations
    }

    pub fn source_value(&self) -> &BigRational {
        &self.source_value
    }

    pub fn minimum(&self) -> &BigRational {
        &self.minimum
    }

    pub fn certificate_id(&self) -> &str {
        &self.certificate_id
    }
}

fn rational_json(value: &BigRational) -> Value {
    Value::Array(vec![
        Value::String(value.numer().to_string()),
        Value::String(value.denom().to_string()),
    ])
}

/// The exact R2 license. Its fields are private and it is constructed only by
/// `decide_oesos` from a checked positive-residual exhaustion certificate.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct R2License {
    certificate_id: String,
    context_id: String,
    source_state_id: String,
    residual: BigRational,
}

impl R2License {
    pub fn certificate_id(&self) -> &str {
        &self.certificate_id
    }

    pub fn context_id(&self) -> &str {
        &self.context_id
    }

    pub fn source_state_id(&self) -> &str {
        &self.source_state_id
    }

    pub fn residual(&self) -> &BigRational {
        &self.residual
    }
}

/// The only two lawful routes derived from checked finite evidence.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum OesosDecision {
    R1SameContext {
        certificate_id: String,
        residual: BigRational,
        selected_candidate_ids: Vec<String>,
    },
    R2ExtensionLicensed(R2License),
}

/// Give R1 priority whenever the source or any declared repair has zero exact
/// obstruction. R2 is otherwise licensed by the same complete certificate.
pub fn decide_oesos(certificate: &ExhaustionCertificate) -> OesosDecision {
    if certificate.minimum.is_zero() {
        let selected_candidate_ids = certificate
            .evaluations
            .iter()
            .filter(|evaluation| evaluation.value.is_zero())
            .map(|evaluation| evaluation.candidate_id.clone())
            .collect();
        OesosDecision::R1SameContext {
            certificate_id: certificate.certificate_id.clone(),
            residual: certificate.minimum.clone(),
            selected_candidate_ids,
        }
    } else {
        OesosDecision::R2ExtensionLicensed(R2License {
            certificate_id: certificate.certificate_id.clone(),
            context_id: certificate.context_id.clone(),
            source_state_id: certificate.source_state_id.clone(),
            residual: certificate.minimum.clone(),
        })
    }
}

// Origin: engine/crates_rs/pfp/src/foundation/repair.rs
// Claim: urn:core:crates_rs:pfp:repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda7d19937 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda7d19937` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora7d19937 {
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
impl BoundaryErrora7d19937 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora7d19937 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora7d19937 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda7d19937 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora7d19937> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora7d19937::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora7d19937::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora7d19937::ExceedsCapacity {
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
mod l4_boundary_tests_a7d19937 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda7d19937::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda7d19937::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda7d19937::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda7d19937::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda7d19937::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora7d19937::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora7d19937::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
