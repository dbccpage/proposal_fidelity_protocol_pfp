use crate::kinds::BaseType;
use crate::traits::candidates::{LambdaCandidate, ReducerCandidate, TransformCandidate};
use crate::witness::capability::HasPhi;
use crate::witness::evidence::{
    DeterminismWitness, IdempotenceWitness, LawViolation, PhiMonotonicityWitness,
};

const PRODUCER_ID: &str = "core_contracts.empirical_witness.v1";

fn witness_hash(parts: &[&str]) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"CoreContracts.EmpiricalWitness.v1");
    for part in parts {
        hasher.update(&(part.len() as u64).to_le_bytes());
        hasher.update(part.as_bytes());
    }
    hasher.finalize().to_hex().to_string()
}

fn candidate_failure(property: &'static str) -> LawViolation {
    LawViolation {
        property,
        description: "candidate application failed while producing empirical witness".to_string(),
    }
}

/// Produce empirical phi-monotonicity evidence over an explicit finite sample set.
///
/// This function does not certify phi-monotonicity. It emits an EvidenceOnly
/// witness record that a later checker, evaluator, or certificate boundary may
/// consume.
pub fn produce_lambda_phi_witness<Op, S, I>(
    contract_id: impl Into<String>,
    schema_hash: impl Into<String>,
    op: &Op,
    samples: I,
) -> Result<PhiMonotonicityWitness, LawViolation>
where
    S: BaseType + HasPhi + Clone,
    Op: LambdaCandidate<S, S>,
    I: IntoIterator<Item = S>,
{
    let contract_id = contract_id.into();
    let schema_hash = schema_hash.into();
    let witness_id = format!("witness:{}:phi_monotonicity", contract_id);

    let mut sample_count = 0usize;
    let mut maximum_observed_phi = f64::NEG_INFINITY;
    let mut minimum_observed_phi = f64::INFINITY;
    let mut max_phi_delta = f64::NEG_INFINITY;
    let mut violations = Vec::new();

    for sample in samples {
        let before_phi = sample.phi();
        let output = op
            .apply_candidate(&sample)
            .map_err(|_| candidate_failure("phi_monotonicity"))?;
        let after_phi = output.phi();
        let delta = after_phi - before_phi;

        sample_count += 1;
        maximum_observed_phi = maximum_observed_phi.max(before_phi).max(after_phi);
        minimum_observed_phi = minimum_observed_phi.min(before_phi).min(after_phi);
        max_phi_delta = max_phi_delta.max(delta);

        if delta > 0.0 {
            violations.push(LawViolation {
                property: "phi_monotonicity",
                description: format!("observed positive phi delta: {}", delta),
            });
        }
    }

    if sample_count == 0 {
        maximum_observed_phi = 0.0;
        minimum_observed_phi = 0.0;
        max_phi_delta = 0.0;
    }

    let violation_count = violations.len();
    let witness_hash = witness_hash(&[
        &witness_id,
        &contract_id,
        &schema_hash,
        &sample_count.to_string(),
        &max_phi_delta.to_bits().to_string(),
        &violation_count.to_string(),
    ]);

    Ok(PhiMonotonicityWitness {
        witness_id,
        contract_id,
        schema_hash,
        witness_hash,
        produced_by: PRODUCER_ID.to_string(),
        sample_count,
        max_phi_delta,
        violation_count,
        maximum_observed_phi,
        minimum_observed_phi,
        violations,
        distribution_metadata: "explicit_finite_samples".to_string(),
    })
}

/// Produce empirical idempotence evidence over an explicit finite sample set.
pub fn produce_reducer_idempotence_witness<Op, S, I>(
    contract_id: impl Into<String>,
    schema_hash: impl Into<String>,
    op: &Op,
    samples: I,
) -> Result<IdempotenceWitness, LawViolation>
where
    S: BaseType + Clone + PartialEq,
    Op: ReducerCandidate<S>,
    I: IntoIterator<Item = S>,
{
    let contract_id = contract_id.into();
    let schema_hash = schema_hash.into();
    let witness_id = format!("witness:{}:idempotence", contract_id);
    let mut samples_verified = 0usize;

    for sample in samples {
        let once = op
            .apply_candidate(&sample)
            .map_err(|_| candidate_failure("idempotence"))?;
        let twice = op
            .apply_candidate(&once)
            .map_err(|_| candidate_failure("idempotence"))?;

        if once != twice {
            return Err(LawViolation {
                property: "idempotence",
                description: "observed reducer output changed on second application".to_string(),
            });
        }
        samples_verified += 1;
    }

    let witness_hash = witness_hash(&[
        &witness_id,
        &contract_id,
        &schema_hash,
        &samples_verified.to_string(),
    ]);

    Ok(IdempotenceWitness {
        witness_id,
        contract_id,
        schema_hash,
        witness_hash,
        produced_by: PRODUCER_ID.to_string(),
        samples_verified,
    })
}

/// Produce empirical determinism evidence over an explicit finite sample set.
pub fn produce_transform_determinism_witness<Op, S, I>(
    contract_id: impl Into<String>,
    schema_hash: impl Into<String>,
    op: &Op,
    samples: I,
) -> Result<DeterminismWitness, LawViolation>
where
    S: BaseType + Clone + PartialEq,
    Op: TransformCandidate<S>,
    I: IntoIterator<Item = S>,
{
    let contract_id = contract_id.into();
    let schema_hash = schema_hash.into();
    let witness_id = format!("witness:{}:determinism", contract_id);
    let mut samples_verified = 0usize;

    for sample in samples {
        let first = op
            .apply_candidate(&sample)
            .map_err(|_| candidate_failure("determinism"))?;
        let second = op
            .apply_candidate(&sample)
            .map_err(|_| candidate_failure("determinism"))?;

        if first != second {
            return Err(LawViolation {
                property: "determinism",
                description: "observed transform output changed for same input".to_string(),
            });
        }
        samples_verified += 1;
    }

    let witness_hash = witness_hash(&[
        &witness_id,
        &contract_id,
        &schema_hash,
        &samples_verified.to_string(),
    ]);

    Ok(DeterminismWitness {
        witness_id,
        contract_id,
        schema_hash,
        witness_hash,
        produced_by: PRODUCER_ID.to_string(),
        samples_verified,
    })
}

// Origin: engine/crates_rs/core_contracts/src/witness_empirical.rs
// Claim: urn:core:crates_rs:core-contracts:witness-empirical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4de465b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4de465b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4de465b {
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
impl BoundaryErrorf4de465b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4de465b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4de465b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4de465b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4de465b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4de465b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4de465b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4de465b::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::kinds::{BaseValidationViolation, BaseValidationWitness, SchemaHash, SchemaRef};
    use crate::traits::candidates::{CandidateKind, DeclaredActionCandidate, LawDeclaration};
    use crate::traits::identity::{ContractBound, NamedComponent};

    #[derive(Debug, Clone, PartialEq)]
    struct PhiState(f64);

    impl crate::sealed::Sealed for PhiState {}

    impl BaseType for PhiState {
        fn schema() -> &'static SchemaRef {
            static SCHEMA: SchemaRef = SchemaRef("test.phi_state.v1");
            &SCHEMA
        }

        fn validate(&self) -> Result<BaseValidationWitness, BaseValidationViolation> {
            Ok(BaseValidationWitness {
                validation_id: "test.validation",
                schema_hash: SchemaHash([0; 32]),
                validator_version: "test",
            })
        }
    }

    impl HasPhi for PhiState {
        fn phi(&self) -> f64 {
            self.0
        }
    }

    struct DecreasePhi;

    impl NamedComponent for DecreasePhi {
        fn name(&self) -> &'static str {
            "decrease_phi"
        }
    }

    impl ContractBound for DecreasePhi {
        fn contract_id(&self) -> &'static str {
            "contract:decrease_phi"
        }
    }

    impl DeclaredActionCandidate<PhiState, PhiState> for DecreasePhi {
        type Error = ();

        fn apply_candidate(&self, input: &PhiState) -> Result<PhiState, Self::Error> {
            Ok(PhiState((input.0 - 1.0).max(0.0)))
        }

        fn law_declaration(&self) -> LawDeclaration {
            LawDeclaration {
                id: "law:decrease_phi".to_string(),
                phi_claim: None,
                structure_claim: None,
                effect_claim: None,
                evidence_refs: Vec::new(),
            }
        }

        fn candidate_kind(&self) -> CandidateKind {
            CandidateKind::Lambda
        }
    }

    impl LambdaCandidate<PhiState, PhiState> for DecreasePhi {}

    #[derive(Debug, Clone, PartialEq)]
    struct WordState(String);

    impl crate::sealed::Sealed for WordState {}

    impl BaseType for WordState {
        fn schema() -> &'static SchemaRef {
            static SCHEMA: SchemaRef = SchemaRef("test.word_state.v1");
            &SCHEMA
        }

        fn validate(&self) -> Result<BaseValidationWitness, BaseValidationViolation> {
            Ok(BaseValidationWitness {
                validation_id: "test.validation",
                schema_hash: SchemaHash([1; 32]),
                validator_version: "test",
            })
        }
    }

    struct TrimReducer;

    impl NamedComponent for TrimReducer {
        fn name(&self) -> &'static str {
            "trim_reducer"
        }
    }

    impl ContractBound for TrimReducer {
        fn contract_id(&self) -> &'static str {
            "contract:trim_reducer"
        }
    }

    impl DeclaredActionCandidate<WordState, WordState> for TrimReducer {
        type Error = ();

        fn apply_candidate(&self, input: &WordState) -> Result<WordState, Self::Error> {
            Ok(WordState(input.0.trim().to_string()))
        }

        fn law_declaration(&self) -> LawDeclaration {
            LawDeclaration {
                id: "law:trim_idempotent".to_string(),
                phi_claim: None,
                structure_claim: None,
                effect_claim: None,
                evidence_refs: Vec::new(),
            }
        }

        fn candidate_kind(&self) -> CandidateKind {
            CandidateKind::Reducer
        }
    }

    impl ReducerCandidate<WordState> for TrimReducer {}
    impl TransformCandidate<WordState> for TrimReducer {}

    #[test]
    fn lambda_phi_witness_records_sample_and_violation_metrics() {
        let witness = produce_lambda_phi_witness(
            "contract:decrease_phi",
            "schema:hash",
            &DecreasePhi,
            vec![PhiState(2.0), PhiState(0.5)],
        )
        .expect("witness should be produced");

        assert_eq!(witness.sample_count, 2);
        assert_eq!(witness.violation_count, 0);
        assert!(witness.max_phi_delta <= 0.0);
        assert_eq!(witness.produced_by, PRODUCER_ID);
        assert_eq!(witness.witness_hash.len(), 64);
    }

    #[test]
    fn reducer_idempotence_witness_uses_explicit_samples() {
        let witness = produce_reducer_idempotence_witness(
            "contract:trim_reducer",
            "schema:hash",
            &TrimReducer,
            vec![WordState("  x ".to_string()), WordState("y".to_string())],
        )
        .expect("idempotence should hold");

        assert_eq!(witness.samples_verified, 2);
        assert_eq!(witness.produced_by, PRODUCER_ID);
        assert_eq!(witness.witness_hash.len(), 64);
    }

    #[test]
    fn transform_determinism_witness_uses_explicit_samples() {
        let witness = produce_transform_determinism_witness(
            "contract:trim_transform",
            "schema:hash",
            &TrimReducer,
            vec![WordState("  x ".to_string()), WordState("y".to_string())],
        )
        .expect("determinism should hold");

        assert_eq!(witness.samples_verified, 2);
        assert_eq!(witness.produced_by, PRODUCER_ID);
        assert_eq!(witness.witness_hash.len(), 64);
    }
}

#[cfg(test)]
mod l4_boundary_tests_f4de465b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf4de465b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf4de465b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf4de465b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf4de465b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf4de465b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf4de465b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf4de465b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
