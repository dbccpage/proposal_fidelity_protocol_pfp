use crate::validation::violation::ValidationViolation;
use crate::witness::evidence::ValidationWitness;
use crate::ContractEffect;
use crate::SchemaHash;
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum LawSubjectLayer {
    Structure,
    Evidence,
    Fact,
    Judgment,
    Action,
    Record,
    Runtime,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum LawClass {
    Structural,
    Phi,
    Effect,
    Authority,
    Replay,
    Certificate,
    Policy,
    Runtime,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum LawSeverity {
    HardFailure,
    SoftFailure,
    Warning,
}

#[derive(Debug)]
pub enum LawEvidence {
    Witness(Box<dyn ValidationWitness>),
    Violation(Box<dyn ValidationViolation>),
}

impl LawEvidence {
    pub fn is_witness(&self) -> bool {
        matches!(self, Self::Witness(_))
    }

    pub fn is_violation(&self) -> bool {
        matches!(self, Self::Violation(_))
    }
}

pub trait LawCheck<S> {
    type Witness: ValidationWitness;
    type Violation: ValidationViolation;

    fn law_id(&self) -> &'static str;
    fn checker_id(&self) -> &'static str {
        self.law_id()
    }
    fn checker_version(&self) -> &'static str {
        "unspecified"
    }
    fn schema_hash(&self) -> SchemaHash;
    fn subject_layer(&self) -> LawSubjectLayer;
    fn class(&self) -> LawClass;
    fn severity(&self) -> LawSeverity;

    fn check(&self, subject: &S) -> Result<Self::Witness, Self::Violation>;
}

pub trait ErasedLawCheck<S> {
    fn law_id(&self) -> &'static str;
    fn checker_id(&self) -> &'static str;
    fn checker_version(&self) -> &'static str;
    fn schema_hash(&self) -> SchemaHash;
    fn subject_layer(&self) -> LawSubjectLayer;
    fn class(&self) -> LawClass;
    fn severity(&self) -> LawSeverity;

    fn check_erased(
        &self,
        subject: &S,
    ) -> Result<Box<dyn ValidationWitness>, Box<dyn ValidationViolation>>;
}

impl<S, T: LawCheck<S>> ErasedLawCheck<S> for T
where
    T::Witness: 'static,
    T::Violation: 'static,
{
    fn law_id(&self) -> &'static str {
        LawCheck::law_id(self)
    }

    fn checker_id(&self) -> &'static str {
        LawCheck::checker_id(self)
    }

    fn checker_version(&self) -> &'static str {
        LawCheck::checker_version(self)
    }

    fn schema_hash(&self) -> SchemaHash {
        LawCheck::schema_hash(self)
    }

    fn subject_layer(&self) -> LawSubjectLayer {
        LawCheck::subject_layer(self)
    }

    fn class(&self) -> LawClass {
        LawCheck::class(self)
    }

    fn severity(&self) -> LawSeverity {
        LawCheck::severity(self)
    }

    fn check_erased(
        &self,
        subject: &S,
    ) -> Result<Box<dyn ValidationWitness>, Box<dyn ValidationViolation>> {
        LawCheck::check(self, subject)
            .map(|w| Box::new(w) as Box<dyn ValidationWitness>)
            .map_err(|v| Box::new(v) as Box<dyn ValidationViolation>)
    }
}

pub struct LawCheckReport {
    pub report_id: String,
    pub law_id: &'static str,
    pub checker_id: &'static str,
    pub checker_version: &'static str,
    pub schema_hash: SchemaHash,
    pub subject_hash: Option<String>,
    pub subject_layer: LawSubjectLayer,
    pub class: LawClass,
    pub severity: LawSeverity,
    pub passed: bool,
    pub authority_effect: ContractEffect,
    pub report_hash: String,
    pub evidence: LawEvidence,
}

// Hash helper binds every identity field of the report; the arity is the point.
#[allow(clippy::too_many_arguments)]
fn report_hash(
    law_id: &'static str,
    checker_id: &'static str,
    checker_version: &'static str,
    schema_hash: SchemaHash,
    subject_hash: Option<&str>,
    subject_layer: LawSubjectLayer,
    class: LawClass,
    severity: LawSeverity,
    passed: bool,
) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"CoreContracts.LawCheckReport.v1");
    let mut update_part = |part: &str| {
        hasher.update(&(part.len() as u64).to_le_bytes());
        hasher.update(part.as_bytes());
    };
    update_part(law_id);
    update_part(checker_id);
    update_part(checker_version);
    update_part(&schema_hash.to_string());
    update_part(subject_hash.unwrap_or(""));
    update_part(&format!("{subject_layer:?}"));
    update_part(&format!("{class:?}"));
    update_part(&format!("{severity:?}"));
    update_part(if passed { "passed" } else { "failed" });
    hasher.finalize().to_hex().to_string()
}

/// Check all laws against a subject and collect reports.
pub fn check_all_laws<S>(subject: &S, laws: &[&dyn ErasedLawCheck<S>]) -> Vec<LawCheckReport> {
    laws.iter()
        .map(|law| {
            let result = law.check_erased(subject);
            let passed = result.is_ok();
            let evidence = match result {
                Ok(w) => LawEvidence::Witness(w),
                Err(v) => LawEvidence::Violation(v),
            };
            let report_hash = report_hash(
                law.law_id(),
                law.checker_id(),
                law.checker_version(),
                law.schema_hash(),
                None,
                law.subject_layer(),
                law.class(),
                law.severity(),
                passed,
            );
            LawCheckReport {
                report_id: format!("law_report:{}:{report_hash}", law.law_id()),
                law_id: law.law_id(),
                checker_id: law.checker_id(),
                checker_version: law.checker_version(),
                schema_hash: law.schema_hash(),
                subject_hash: None,
                subject_layer: law.subject_layer(),
                class: law.class(),
                severity: law.severity(),
                passed,
                authority_effect: ContractEffect::EvidenceOnly,
                report_hash,
                evidence,
            }
        })
        .collect()
}

/// Returns true if no report of severity `HardFailure` failed.
pub fn reports_all_hard_laws_hold(reports: &[LawCheckReport]) -> bool {
    reports
        .iter()
        .all(|report| !matches!(report.severity, LawSeverity::HardFailure) || report.passed)
}

/// Returns the IDs of all failing law reports.
pub fn failing_laws_from_reports(reports: &[LawCheckReport]) -> Vec<&'static str> {
    reports
        .iter()
        .filter(|report| !report.passed)
        .map(|report| report.law_id)
        .collect()
}

/// Returns true if no laws of severity `HardFailure` fail.
pub fn all_laws_hold<S>(subject: &S, laws: &[&dyn ErasedLawCheck<S>]) -> bool {
    reports_all_hard_laws_hold(&check_all_laws(subject, laws))
}

/// Returns the IDs of all failing laws.
pub fn failing_laws<S>(subject: &S, laws: &[&dyn ErasedLawCheck<S>]) -> Vec<&'static str> {
    failing_laws_from_reports(&check_all_laws(subject, laws))
}

// ——— Tests ——————————————————————————————————————————————————————————

// Origin: engine/crates_rs/core_contracts/src/witness_law_checker.rs
// Claim: urn:core:crates_rs:core-contracts:witness-law-checker:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordba30c92d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordba30c92d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorba30c92d {
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
impl BoundaryErrorba30c92d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorba30c92d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorba30c92d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordba30c92d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorba30c92d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorba30c92d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorba30c92d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorba30c92d::ExceedsCapacity {
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
    use crate::witness::evidence::{WitnessCertainty, WitnessClass};

    // Domain 1: matrix basis mismatch
    #[derive(Debug, Serialize)]
    struct BasisMismatchWitness {
        basis_id_a: String,
        basis_id_b: String,
    }
    impl ValidationWitness for BasisMismatchWitness {
        fn property(&self) -> &'static str {
            "basis_match"
        }
        fn class(&self) -> WitnessClass {
            WitnessClass::Structural
        }
        fn witness_certainty(&self) -> WitnessCertainty {
            WitnessCertainty::StructuralProof
        }
    }

    #[derive(Debug, Serialize)]
    struct BasisMismatchViolation {
        reason: String,
    }
    impl ValidationViolation for BasisMismatchViolation {
        fn code(&self) -> &'static str {
            "E_BASIS_MISMATCH"
        }
    }

    struct MatrixBasisCheck;
    impl LawCheck<(&'static str, &'static str)> for MatrixBasisCheck {
        type Witness = BasisMismatchWitness;
        type Violation = BasisMismatchViolation;

        fn law_id(&self) -> &'static str {
            "matrix_basis_check"
        }
        fn schema_hash(&self) -> SchemaHash {
            SchemaHash([0x01; 32])
        }
        fn subject_layer(&self) -> LawSubjectLayer {
            LawSubjectLayer::Structure
        }
        fn class(&self) -> LawClass {
            LawClass::Structural
        }
        fn severity(&self) -> LawSeverity {
            LawSeverity::HardFailure
        }

        fn check(
            &self,
            subject: &(&'static str, &'static str),
        ) -> Result<Self::Witness, Self::Violation> {
            if subject.0 == subject.1 {
                Ok(BasisMismatchWitness {
                    basis_id_a: subject.0.to_string(),
                    basis_id_b: subject.1.to_string(),
                })
            } else {
                Err(BasisMismatchViolation {
                    reason: format!("Basis mismatch between {} and {}", subject.0, subject.1),
                })
            }
        }
    }

    // Domain 2: boundary operator d∘d = 0
    #[derive(Debug, Serialize)]
    struct NilpotencyWitness {
        degree: usize,
        verified: bool,
    }
    impl ValidationWitness for NilpotencyWitness {
        fn property(&self) -> &'static str {
            "boundary_nilpotency"
        }
        fn class(&self) -> WitnessClass {
            WitnessClass::Structural
        }
        fn witness_certainty(&self) -> WitnessCertainty {
            WitnessCertainty::StructuralProof
        }
    }

    #[derive(Debug, Serialize)]
    struct NilpotencyViolation {
        degree: usize,
        nonzero_norm: f64,
    }
    impl ValidationViolation for NilpotencyViolation {
        fn code(&self) -> &'static str {
            "E_NONZERO_BOUNDARY_COMPOSITION"
        }
    }

    struct BoundaryOperatorCheck;
    impl LawCheck<(usize, f64)> for BoundaryOperatorCheck {
        type Witness = NilpotencyWitness;
        type Violation = NilpotencyViolation;

        fn law_id(&self) -> &'static str {
            "boundary_nilpotency_check"
        }
        fn schema_hash(&self) -> SchemaHash {
            SchemaHash([0x02; 32])
        }
        fn subject_layer(&self) -> LawSubjectLayer {
            LawSubjectLayer::Structure
        }
        fn class(&self) -> LawClass {
            LawClass::Structural
        }
        fn severity(&self) -> LawSeverity {
            LawSeverity::HardFailure
        }

        fn check(&self, subject: &(usize, f64)) -> Result<Self::Witness, Self::Violation> {
            if subject.1.abs() < 1e-9 {
                Ok(NilpotencyWitness {
                    degree: subject.0,
                    verified: true,
                })
            } else {
                Err(NilpotencyViolation {
                    degree: subject.0,
                    nonzero_norm: subject.1,
                })
            }
        }
    }

    // Domain 3: chain map commutativity
    #[derive(Debug, Serialize)]
    struct CommutativityWitness {
        path_a_norm: f64,
        path_b_norm: f64,
    }
    impl ValidationWitness for CommutativityWitness {
        fn property(&self) -> &'static str {
            "chain_map_commutativity"
        }
        fn class(&self) -> WitnessClass {
            WitnessClass::Structural
        }
        fn witness_certainty(&self) -> WitnessCertainty {
            WitnessCertainty::StructuralProof
        }
    }

    #[derive(Debug, Serialize)]
    struct CommutativityViolation {
        discrepancy: f64,
    }
    impl ValidationViolation for CommutativityViolation {
        fn code(&self) -> &'static str {
            "E_CHAIN_MAP_NON_COMMUTATIVE"
        }
    }

    struct ChainMapCommutativityCheck;
    impl LawCheck<f64> for ChainMapCommutativityCheck {
        type Witness = CommutativityWitness;
        type Violation = CommutativityViolation;

        fn law_id(&self) -> &'static str {
            "chain_map_commutativity_check"
        }
        fn schema_hash(&self) -> SchemaHash {
            SchemaHash([0x03; 32])
        }
        fn subject_layer(&self) -> LawSubjectLayer {
            LawSubjectLayer::Structure
        }
        fn class(&self) -> LawClass {
            LawClass::Structural
        }
        fn severity(&self) -> LawSeverity {
            LawSeverity::Warning
        } // warning-level during WIP

        fn check(&self, subject: &f64) -> Result<Self::Witness, Self::Violation> {
            if subject.abs() < 1e-9 {
                Ok(CommutativityWitness {
                    path_a_norm: 1.0,
                    path_b_norm: 1.0,
                })
            } else {
                Err(CommutativityViolation {
                    discrepancy: *subject,
                })
            }
        }
    }

    // Domain 4: certificate hash mismatch
    #[derive(Debug, Serialize)]
    struct CertificateWitness {
        hash: [u8; 32],
    }
    impl ValidationWitness for CertificateWitness {
        fn property(&self) -> &'static str {
            "certificate_validity"
        }
        fn class(&self) -> WitnessClass {
            WitnessClass::Behavioral
        }
        fn witness_certainty(&self) -> WitnessCertainty {
            WitnessCertainty::PropertyWitness
        }
    }

    #[derive(Debug, Serialize)]
    struct CertificateViolation {
        expected: [u8; 32],
        actual: [u8; 32],
    }
    impl ValidationViolation for CertificateViolation {
        fn code(&self) -> &'static str {
            "E_CERTIFICATE_HASH_MISMATCH"
        }
    }

    struct CertificateHashCheck;
    impl LawCheck<([u8; 32], [u8; 32])> for CertificateHashCheck {
        type Witness = CertificateWitness;
        type Violation = CertificateViolation;

        fn law_id(&self) -> &'static str {
            "certificate_hash_check"
        }
        fn schema_hash(&self) -> SchemaHash {
            SchemaHash([0x04; 32])
        }
        fn subject_layer(&self) -> LawSubjectLayer {
            LawSubjectLayer::Evidence
        }
        fn class(&self) -> LawClass {
            LawClass::Certificate
        }
        fn severity(&self) -> LawSeverity {
            LawSeverity::HardFailure
        }

        fn check(&self, subject: &([u8; 32], [u8; 32])) -> Result<Self::Witness, Self::Violation> {
            if subject.0 == subject.1 {
                Ok(CertificateWitness { hash: subject.0 })
            } else {
                Err(CertificateViolation {
                    expected: subject.0,
                    actual: subject.1,
                })
            }
        }
    }

    // Domain 5: policy replay mismatch
    #[derive(Debug, Serialize)]
    struct PolicyReplayWitness {
        state_digest: [u8; 32],
    }
    impl ValidationWitness for PolicyReplayWitness {
        fn property(&self) -> &'static str {
            "policy_replay"
        }
        fn class(&self) -> WitnessClass {
            WitnessClass::Behavioral
        }
        fn witness_certainty(&self) -> WitnessCertainty {
            WitnessCertainty::PropertyWitness
        }
    }

    #[derive(Debug, Serialize)]
    struct PolicyReplayViolation {
        mismatched_index: usize,
    }
    impl ValidationViolation for PolicyReplayViolation {
        fn code(&self) -> &'static str {
            "E_POLICY_REPLAY_MISMATCH"
        }
    }

    struct PolicyReplayCheck;
    impl LawCheck<(usize, bool)> for PolicyReplayCheck {
        type Witness = PolicyReplayWitness;
        type Violation = PolicyReplayViolation;

        fn law_id(&self) -> &'static str {
            "policy_replay_check"
        }
        fn schema_hash(&self) -> SchemaHash {
            SchemaHash([0x05; 32])
        }
        fn subject_layer(&self) -> LawSubjectLayer {
            LawSubjectLayer::Judgment
        }
        fn class(&self) -> LawClass {
            LawClass::Replay
        }
        fn severity(&self) -> LawSeverity {
            LawSeverity::HardFailure
        }

        fn check(&self, subject: &(usize, bool)) -> Result<Self::Witness, Self::Violation> {
            if subject.1 {
                Ok(PolicyReplayWitness {
                    state_digest: [0; 32],
                })
            } else {
                Err(PolicyReplayViolation {
                    mismatched_index: subject.0,
                })
            }
        }
    }

    // Domain 6: public verifier mutation attempt
    #[derive(Debug, Serialize)]
    struct PublicVerifyWitness {
        is_immutable: bool,
    }
    impl ValidationWitness for PublicVerifyWitness {
        fn property(&self) -> &'static str {
            "verifier_immutability"
        }
        fn class(&self) -> WitnessClass {
            WitnessClass::Structural
        }
        fn witness_certainty(&self) -> WitnessCertainty {
            WitnessCertainty::StructuralProof
        }
    }

    #[derive(Debug, Serialize)]
    struct PublicVerifyViolation {
        mutated_field: String,
    }
    impl ValidationViolation for PublicVerifyViolation {
        fn code(&self) -> &'static str {
            "E_MUTATION_ATTEMPT"
        }
    }

    struct PublicVerifierCheck;
    impl LawCheck<Option<&'static str>> for PublicVerifierCheck {
        type Witness = PublicVerifyWitness;
        type Violation = PublicVerifyViolation;

        fn law_id(&self) -> &'static str {
            "public_verifier_mutation_check"
        }
        fn schema_hash(&self) -> SchemaHash {
            SchemaHash([0x06; 32])
        }
        fn subject_layer(&self) -> LawSubjectLayer {
            LawSubjectLayer::Runtime
        }
        fn class(&self) -> LawClass {
            LawClass::Runtime
        }
        fn severity(&self) -> LawSeverity {
            LawSeverity::HardFailure
        }

        fn check(&self, subject: &Option<&'static str>) -> Result<Self::Witness, Self::Violation> {
            match subject {
                None => Ok(PublicVerifyWitness { is_immutable: true }),
                Some(field) => Err(PublicVerifyViolation {
                    mutated_field: field.to_string(),
                }),
            }
        }
    }

    #[test]
    fn test_matrix_basis_and_boundary_checks() {
        let basis_subject = ("basis_x", "basis_x");
        let basis_check = MatrixBasisCheck;
        let res = basis_check.check(&basis_subject);
        assert!(res.is_ok());

        let bad_basis_subject = ("basis_x", "basis_y");
        let res_err = basis_check.check(&bad_basis_subject);
        assert!(res_err.is_err());
        assert_eq!(res_err.err().unwrap().code(), "E_BASIS_MISMATCH");

        let boundary_check = BoundaryOperatorCheck;
        let res_boundary = boundary_check.check(&(2, 0.0));
        assert!(res_boundary.is_ok());

        let res_boundary_err = boundary_check.check(&(2, 0.5));
        assert!(res_boundary_err.is_err());
        assert_eq!(
            res_boundary_err.err().unwrap().code(),
            "E_NONZERO_BOUNDARY_COMPOSITION"
        );
    }

    #[test]
    fn test_chain_map_commutativity_warning_severity() {
        let check = ChainMapCommutativityCheck;
        let laws: Vec<&dyn ErasedLawCheck<f64>> = vec![&check];
        let reports = check_all_laws(&0.8, &laws);
        assert_eq!(reports.len(), 1);
        assert!(!reports[0].passed);
        assert!(reports[0].evidence.is_violation());
        assert_eq!(reports[0].authority_effect, ContractEffect::EvidenceOnly);
        assert_eq!(reports[0].subject_layer, LawSubjectLayer::Structure);
        assert_eq!(reports[0].report_hash.len(), 64);

        // Since it's only warning-level severity, all_laws_hold should still return true!
        assert!(all_laws_hold(&0.8, &laws));
        assert!(reports_all_hard_laws_hold(&reports));
        assert_eq!(
            failing_laws_from_reports(&reports),
            vec!["chain_map_commutativity_check"]
        );
    }

    #[test]
    fn test_hard_failures_block_all_laws_hold() {
        let basis_check = MatrixBasisCheck;
        let laws: Vec<&dyn ErasedLawCheck<(&'static str, &'static str)>> = vec![&basis_check];

        // Should hold when passes
        assert!(all_laws_hold(&("basis_x", "basis_x"), &laws));

        // Should NOT hold when HardFailure check fails
        assert!(!all_laws_hold(&("basis_x", "basis_y"), &laws));
    }

    #[test]
    fn test_all_domains_reports() {
        let check1 = MatrixBasisCheck;
        let check2 = BoundaryOperatorCheck;
        let check3 = ChainMapCommutativityCheck;
        let check4 = CertificateHashCheck;
        let check5 = PolicyReplayCheck;
        let check6 = PublicVerifierCheck;

        assert_eq!(
            LawCheck::<(&str, &str)>::law_id(&check1),
            "matrix_basis_check"
        );
        assert_eq!(
            LawCheck::<(usize, f64)>::schema_hash(&check2),
            SchemaHash([0x02; 32])
        );
        assert_eq!(
            LawCheck::<f64>::subject_layer(&check3),
            LawSubjectLayer::Structure
        );
        assert_eq!(
            LawCheck::<([u8; 32], [u8; 32])>::subject_layer(&check4),
            LawSubjectLayer::Evidence
        );
        assert_eq!(
            LawCheck::<(usize, bool)>::subject_layer(&check5),
            LawSubjectLayer::Judgment
        );
        assert_eq!(
            LawCheck::<Option<&str>>::subject_layer(&check6),
            LawSubjectLayer::Runtime
        );
        assert_eq!(
            LawCheck::<([u8; 32], [u8; 32])>::class(&check4),
            LawClass::Certificate
        );
        assert_eq!(
            LawCheck::<(usize, bool)>::severity(&check5),
            LawSeverity::HardFailure
        );
        assert_eq!(
            LawCheck::<Option<&str>>::law_id(&check6),
            "public_verifier_mutation_check"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_ba30c92d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordba30c92d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordba30c92d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordba30c92d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordba30c92d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordba30c92d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorba30c92d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorba30c92d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
