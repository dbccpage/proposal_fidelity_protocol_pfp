//! Explicit, stateless dispatch of checked finite functional measurements.
//!
//! This layer emits no workload verdict, terminal status, or actor license.
//! It supports the named Phi1 and Gamma2 kernels only; it does not reinterpret
//! a raw norm as Phi1 or alias Xi to Wigner-Yanase. Hashes bind typed serialized
//! data, not original HTTP bytes, a native binary, or an authenticated carrier.

use std::collections::BTreeMap;

use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, ExactGamma2Result, Gamma2Functional,
};
use crate::l1_seminorm::{L1Seminorm, L1SeminormError};
use crate::phi1::{ExactPhi1Certificate, VerifiedExactPhi1};

pub type FunctionalContentHash = [u8; 32];
const RECORD_SCHEMA: &str = "core.functional.measurement.v1";
const FUNCTIONAL_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(
    tag = "kind",
    content = "state",
    rename_all = "snake_case",
    deny_unknown_fields
)]
pub enum FunctionalInput {
    Phi1(ExactPhi1Certificate),
    Gamma2(Vec<BigRational>),
}

/// This is a mathematical range declaration, not a resource budget.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum FunctionalRange {
    UnboundedAllowed,
}

/// Functional evidence cannot authorize or promote itself.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum FunctionalAuthorityEffect {
    None,
}

/// Shape-only transport record. Deserialize does not validate its claims.
/// Use replay_functional_record against the independently selected configuration
/// and original typed input before relying on its arithmetic or bindings.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UntrustedFunctionalRecord {
    pub schema: String,
    pub functional_id: String,
    pub functional_version: u32,
    pub input_hash: FunctionalContentHash,
    pub config_hash: FunctionalContentHash,
    pub output_hash: FunctionalContentHash,
    pub values: Vec<BigRational>,
    pub witness_refs: Vec<FunctionalContentHash>,
    pub certificate_refs: Vec<FunctionalContentHash>,
    pub solver_refs: Vec<FunctionalContentHash>,
    pub observable_refs: Vec<FunctionalContentHash>,
    pub range_behavior: FunctionalRange,
    pub authority_effect: FunctionalAuthorityEffect,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FunctionalEvidence {
    Phi1(VerifiedExactPhi1),
    Gamma2(ExactGamma2Result),
}

impl FunctionalEvidence {
    pub fn value(&self) -> &BigRational {
        match self {
            Self::Phi1(result) => result.value(),
            Self::Gamma2(result) => result.value(),
        }
    }
}

/// Only actual checked computation or replay can construct this result.
///
/// No deserializer, public field setter, terminal conversion, or promotion API.
///
/// ~~~compile_fail
/// use core_functional::factory::FunctionalOutput;
/// let forged: FunctionalOutput = serde_json::from_str("{}").unwrap();
/// ~~~
///
/// ~~~compile_fail
/// use core_functional::factory::{FunctionalOutput, UntrustedFunctionalRecord, FunctionalEvidence};
/// fn forge(record: UntrustedFunctionalRecord, evidence: FunctionalEvidence) -> FunctionalOutput {
///     FunctionalOutput { record, evidence }
/// }
/// ~~~
#[derive(Debug, Clone)]
pub struct FunctionalOutput {
    record: UntrustedFunctionalRecord,
    evidence: FunctionalEvidence,
}

impl FunctionalOutput {
    pub fn record(&self) -> &UntrustedFunctionalRecord {
        &self.record
    }

    pub fn evidence(&self) -> &FunctionalEvidence {
        &self.evidence
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FunctionalError {
    #[error("FUNCTIONAL_UNKNOWN_KERNEL")]
    UnknownKernel,
    #[error("FUNCTIONAL_CONFIGURATION_MISMATCH")]
    ConfigurationMismatch,
    #[error("FUNCTIONAL_INPUT_KIND_MISMATCH")]
    InputKindMismatch,
    #[error("FUNCTIONAL_INVALID_PHI1: {0}")]
    Phi1(#[from] L1SeminormError),
    #[error("FUNCTIONAL_INVALID_GAMMA2: {0}")]
    Gamma2(#[from] ExactGamma2Error),
    #[error("FUNCTIONAL_SERIALIZATION_FAILED")]
    SerializationFailed,
    #[error("FUNCTIONAL_RECORD_MISMATCH")]
    RecordMismatch,
}

mod sealed {
    pub trait Kernel {}
}

/// Inward computational port, not a plugin or an authority-creation interface.
/// The supported implementations are sealed; adding a kernel requires an
/// explicit in-crate implementation, contract binding, and executable witnesses.
///
/// ~~~compile_fail
/// use core_functional::factory::{BaseFunctionalKernel, FunctionalInput, FunctionalOutput, FunctionalError};
/// struct OutsideKernel;
/// impl BaseFunctionalKernel for OutsideKernel {
///     fn functional_id(&self) -> &'static str { "forged" }
///     fn functional_version(&self) -> u32 { 1 }
///     fn compute(&self, _: &FunctionalInput) -> Result<FunctionalOutput, FunctionalError> {
///         Err(FunctionalError::UnknownKernel)
///     }
/// }
/// ~~~
pub trait BaseFunctionalKernel: sealed::Kernel {
    fn functional_id(&self) -> &'static str;
    fn functional_version(&self) -> u32;
    fn compute(&self, state: &FunctionalInput) -> Result<FunctionalOutput, FunctionalError>;
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum KernelConfiguration {
    Phi1(L1Seminorm),
    Gamma2(ExactCochainComplexQ),
}

/// Immutable selected presentation. Configuration never changes during compute.
/// No mutable global registry, inference, fallback, cache, or candidate ranking.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConfiguredFunctional {
    configuration: KernelConfiguration,
}

impl ConfiguredFunctional {
    pub fn phi1(
        boundary: Vec<Vec<BigRational>>,
        weights: Vec<BigRational>,
    ) -> Result<Self, FunctionalError> {
        Ok(Self {
            configuration: KernelConfiguration::Phi1(L1Seminorm::new(boundary, weights)?),
        })
    }

    pub fn gamma2(complex: ExactCochainComplexQ) -> Self {
        Self {
            configuration: KernelConfiguration::Gamma2(complex),
        }
    }

    fn config_hash(&self) -> Result<FunctionalContentHash, FunctionalError> {
        match &self.configuration {
            KernelConfiguration::Phi1(space) => hash_typed(
                "phi1-config",
                &(FUNCTIONAL_VERSION, space.boundary(), space.weights()),
            ),
            KernelConfiguration::Gamma2(complex) => {
                hash_typed("gamma2-config", &(FUNCTIONAL_VERSION, complex))
            }
        }
    }
    fn evaluate_evidence(
        &self,
        state: &FunctionalInput,
    ) -> Result<FunctionalEvidence, FunctionalError> {
        match (&self.configuration, state) {
            (KernelConfiguration::Phi1(space), FunctionalInput::Phi1(certificate)) => Ok(
                FunctionalEvidence::Phi1(space.evaluate(certificate.clone())?),
            ),
            (KernelConfiguration::Gamma2(complex), FunctionalInput::Gamma2(h)) => {
                let residual = DegreeOneResidualQ::try_new(complex, h.clone())?;
                Ok(FunctionalEvidence::Gamma2(
                    Gamma2Functional::try_compute_exact_quotient(&residual)?,
                ))
            }
            _ => Err(FunctionalError::InputKindMismatch),
        }
    }

    fn populate_evidence_refs(
        record: &mut UntrustedFunctionalRecord,
        evidence: &FunctionalEvidence,
    ) -> Result<(), FunctionalError> {
        match evidence {
            FunctionalEvidence::Phi1(checked) => {
                record
                    .certificate_refs
                    .push(hash_typed("phi1-certificate", checked.certificate())?);
                record.witness_refs.push(hash_typed(
                    "phi1-primal",
                    &(checked.alpha(), checked.primal_residual()),
                )?);
                record
                    .witness_refs
                    .push(hash_typed("phi1-dual", checked.dual_witness())?);
            }
            FunctionalEvidence::Gamma2(checked) => {
                record
                    .witness_refs
                    .push(hash_typed("gamma2-complex", checked.complex())?);
                record
                    .witness_refs
                    .push(hash_typed("gamma2-residual", checked.residual())?);
                record
                    .witness_refs
                    .push(hash_typed("gamma2-coboundary", checked.coboundary())?);
            }
        }
        Ok(())
    }
}

impl sealed::Kernel for ConfiguredFunctional {}

impl BaseFunctionalKernel for ConfiguredFunctional {
    fn functional_id(&self) -> &'static str {
        match self.configuration {
            KernelConfiguration::Phi1(_) => "phi1",
            KernelConfiguration::Gamma2(_) => "gamma2",
        }
    }

    fn functional_version(&self) -> u32 {
        FUNCTIONAL_VERSION
    }

    fn compute(&self, state: &FunctionalInput) -> Result<FunctionalOutput, FunctionalError> {
        // Admission precedes hashing. These typed algebraic boundaries are not
        // substitutes for ingress byte/bit limits in the host/controller.
        let evidence = self.evaluate_evidence(state)?;
        let mut record = UntrustedFunctionalRecord {
            schema: RECORD_SCHEMA.to_owned(),
            functional_id: self.functional_id().to_owned(),
            functional_version: self.functional_version(),
            input_hash: hash_typed("input", state)?,
            config_hash: self.config_hash()?,
            output_hash: [0; 32],
            values: vec![BigRational::new(
                evidence.value().numer().clone(),
                evidence.value().denom().clone(),
            )],
            witness_refs: vec![],
            certificate_refs: vec![],
            solver_refs: vec![],
            observable_refs: vec![],
            range_behavior: FunctionalRange::UnboundedAllowed,
            authority_effect: FunctionalAuthorityEffect::None,
        };
        Self::populate_evidence_refs(&mut record, &evidence)?;
        record.output_hash = output_commitment(&record)?;
        Ok(FunctionalOutput { record, evidence })
    }
}

/// Dispatch only the explicitly requested, configured kernel. Known-but-different
/// configuration is not an alias; unknown names never trigger a default kernel.
pub fn evaluate_functional(
    name: &str,
    kernel: &ConfiguredFunctional,
    state: &FunctionalInput,
) -> Result<FunctionalOutput, FunctionalError> {
    if !matches!(name, "phi1" | "gamma2") {
        return Err(FunctionalError::UnknownKernel);
    }
    if name != kernel.functional_id() {
        return Err(FunctionalError::ConfigurationMismatch);
    }
    kernel.compute(state)
}

/// Recompute against independent inputs and compare the complete record.
/// Comparing serialized data avoids arithmetic on potentially invalid in-process
/// new_raw rationals supplied in an untrusted record.
pub fn replay_functional_record(
    name: &str,
    kernel: &ConfiguredFunctional,
    state: &FunctionalInput,
    claim: &UntrustedFunctionalRecord,
) -> Result<FunctionalOutput, FunctionalError> {
    let checked = evaluate_functional(name, kernel, state)?;
    if encode(&checked.record)? != encode(claim)? {
        return Err(FunctionalError::RecordMismatch);
    }
    Ok(checked)
}

fn encode<T: Serialize + ?Sized>(value: &T) -> Result<Vec<u8>, FunctionalError> {
    serde_json::to_vec(value).map_err(|_| FunctionalError::SerializationFailed)
}

fn hash_typed<T: Serialize + ?Sized>(
    domain: &str,
    value: &T,
) -> Result<FunctionalContentHash, FunctionalError> {
    let bytes = encode(value)?;
    let mut hash = Sha256::new();
    hash.update(b"core.functional.v1\0");
    hash.update((domain.len() as u64).to_le_bytes());
    hash.update(domain.as_bytes());
    hash.update((bytes.len() as u64).to_le_bytes());
    hash.update(bytes);
    Ok(hash.finalize().into())
}

fn output_commitment(
    record: &UntrustedFunctionalRecord,
) -> Result<FunctionalContentHash, FunctionalError> {
    let value = serde_json::to_value(record).map_err(|_| FunctionalError::SerializationFailed)?;
    // Bind every record field except the hash itself. Explicit BTreeMap sorting
    // makes key order independent of serde_json's optional preserve_order feature.
    let mut fields: BTreeMap<String, serde_json::Value> = value
        .as_object()
        .ok_or(FunctionalError::SerializationFailed)?
        .iter()
        .map(|(key, value)| (key.clone(), value.clone()))
        .collect();
    fields.remove("output_hash");
    hash_typed("output", &fields)
}

// Origin: engine/crates_rs/core_functional/src/factory.rs
// Claim: urn:core:crates_rs:core-functional:factory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::phi1::ExactPhi1CertificateError;

    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }

    fn phi1() -> ConfiguredFunctional {
        ConfiguredFunctional::phi1(vec![vec![q(1)], vec![q(0)]], vec![q(2), q(3)]).unwrap()
    }

    fn certificate() -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: vec![q(3), q(-4)],
            d0: vec![vec![q(1)], vec![q(0)]],
            weights: vec![q(2), q(3)],
            alpha: vec![q(3)],
            primal_residual: vec![q(0), q(-4)],
            dual_witness: vec![q(0), q(-3)],
            reported_value: q(12),
        }
    }

    fn complex(scale: i64) -> ExactCochainComplexQ {
        let half = BigRational::new(scale.into(), 2.into());
        ExactCochainComplexQ::try_new(
            1,
            2,
            1,
            vec![vec![q(1)], vec![q(-1)]],
            vec![vec![half.clone(), half]],
        )
        .unwrap()
    }

    fn gamma2() -> ConfiguredFunctional {
        ConfiguredFunctional::gamma2(complex(1))
    }

    fn state() -> FunctionalInput {
        FunctionalInput::Gamma2(vec![q(3), q(-1)])
    }

    #[test]
    fn names_configuration_and_input_kinds_have_distinct_refusals() {
        for name in ["", "PHI1", "Phi1", "xi", "wy", "gamma2 ", "unknown"] {
            assert_eq!(
                evaluate_functional(name, &gamma2(), &state()).unwrap_err(),
                FunctionalError::UnknownKernel,
                "{name}"
            );
        }
        assert_eq!(
            evaluate_functional("phi1", &gamma2(), &state()).unwrap_err(),
            FunctionalError::ConfigurationMismatch
        );
        assert_eq!(
            evaluate_functional("gamma2", &phi1(), &state()).unwrap_err(),
            FunctionalError::ConfigurationMismatch
        );
        assert_eq!(
            evaluate_functional("phi1", &phi1(), &state()).unwrap_err(),
            FunctionalError::InputKindMismatch
        );
        assert_eq!(
            evaluate_functional("gamma2", &gamma2(), &FunctionalInput::Phi1(certificate()))
                .unwrap_err(),
            FunctionalError::InputKindMismatch
        );
    }

    #[test]
    fn stateless_dispatch_is_immutable_and_uses_real_finite_arithmetic() {
        let kernel = gamma2();
        let before = kernel.clone();
        let input = state();
        let input_before = encode(&input).unwrap();
        let port: &dyn BaseFunctionalKernel = &kernel;
        assert_eq!(port.functional_id(), "gamma2");
        assert_eq!(port.functional_version(), 1);
        let first = port.compute(&input).unwrap();
        let shifted = port
            .compute(&FunctionalInput::Gamma2(vec![q(7), q(-5)]))
            .unwrap();
        let again = evaluate_functional("gamma2", &kernel, &input).unwrap();
        // (3 - 1)/2 = (7 - 5)/2 = 1, not the raw representative norm 4 or 12.
        assert_eq!(first.evidence().value(), &q(1));
        assert_eq!(shifted.evidence().value(), &q(1));
        assert_eq!(
            encode(first.record()).unwrap(),
            encode(again.record()).unwrap()
        );
        assert_ne!(first.record().input_hash, shifted.record().input_hash);
        assert_eq!(kernel, before);
        assert_eq!(encode(&input).unwrap(), input_before);
    }

    #[test]
    fn phi1_dispatch_verifies_an_optimum_instead_of_raw_representative_mass() {
        let output =
            evaluate_functional("phi1", &phi1(), &FunctionalInput::Phi1(certificate())).unwrap();
        // min_a 2|3-a| + 3|-4| = 12, whereas the raw mass is 18.
        assert_eq!(output.evidence().value(), &q(12));
        assert_eq!(output.record().values, vec![q(12)]);
        assert!(matches!(output.evidence(), FunctionalEvidence::Phi1(_)));
        let mut bad = certificate();
        bad.reported_value = q(18);
        assert_eq!(
            evaluate_functional("phi1", &phi1(), &FunctionalInput::Phi1(bad)).unwrap_err(),
            FunctionalError::Phi1(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::PrimalValueMismatch
            ))
        );
    }

    #[test]
    fn phi1_presentation_and_admission_failures_are_not_erased_by_dispatch() {
        let mut other = certificate();
        other.weights = vec![q(1), q(1)];
        other.dual_witness = vec![q(0), q(-1)];
        other.reported_value = q(4);
        assert_eq!(
            evaluate_functional("phi1", &phi1(), &FunctionalInput::Phi1(other)).unwrap_err(),
            FunctionalError::Phi1(L1SeminormError::WeightBindingMismatch)
        );
        assert_eq!(
            ConfiguredFunctional::phi1(vec![vec![]], vec![q(0)]).unwrap_err(),
            FunctionalError::Phi1(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::NonPositiveWeight { index: 0 }
            ))
        );
        let mut invalid = certificate();
        invalid.omega[0] = BigRational::new_raw(1.into(), 0.into());
        assert_eq!(
            evaluate_functional("phi1", &phi1(), &FunctionalInput::Phi1(invalid)).unwrap_err(),
            FunctionalError::Phi1(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::ZeroRationalDenominator
            ))
        );
    }

    #[test]
    fn gamma2_admission_refuses_length_and_zero_denominators_before_hashing() {
        assert_eq!(
            evaluate_functional("gamma2", &gamma2(), &FunctionalInput::Gamma2(vec![q(1)]))
                .unwrap_err(),
            FunctionalError::Gamma2(ExactGamma2Error::ResidualLengthMismatch {
                expected: 2,
                actual: 1
            })
        );
        let bad = FunctionalInput::Gamma2(vec![q(1), BigRational::new_raw(1.into(), 0.into())]);
        assert_eq!(
            evaluate_functional("gamma2", &gamma2(), &bad).unwrap_err(),
            FunctionalError::Gamma2(ExactGamma2Error::ZeroDenominator {
                field: "residual",
                row: None,
                column: 1
            })
        );
    }

    #[test]
    fn full_configuration_binds_even_when_distinct_maps_have_the_same_zero_value() {
        let input = FunctionalInput::Gamma2(vec![q(3), q(-3)]);
        let first = evaluate_functional("gamma2", &gamma2(), &input).unwrap();
        let other = ConfiguredFunctional::gamma2(complex(2));
        let second = evaluate_functional("gamma2", &other, &input).unwrap();
        assert_eq!(first.record().values, vec![q(0)]);
        assert_eq!(first.record().values, second.record().values);
        assert_eq!(first.record().input_hash, second.record().input_hash);
        assert_ne!(first.record().config_hash, second.record().config_hash);
        assert_ne!(
            first.record().witness_refs[0],
            second.record().witness_refs[0]
        );
        assert_ne!(first.record().output_hash, second.record().output_hash);
        assert_eq!(
            replay_functional_record("gamma2", &other, &input, first.record()).unwrap_err(),
            FunctionalError::RecordMismatch
        );
    }

    #[test]
    fn hashes_bind_typed_input_encoding_while_valid_configuration_is_canonical() {
        let raw = |n: i64, d: i64| BigRational::new_raw(n.into(), d.into());
        let equivalent = ExactCochainComplexQ::try_new(
            1,
            2,
            1,
            vec![vec![raw(-2, -2)], vec![raw(2, -2)]],
            vec![vec![raw(-2, -4), raw(3, 6)]],
        )
        .unwrap();
        let kernel = ConfiguredFunctional::gamma2(equivalent);
        assert_eq!(kernel, gamma2());
        let canonical = evaluate_functional("gamma2", &gamma2(), &state()).unwrap();
        let noncanonical = FunctionalInput::Gamma2(vec![raw(-6, -2), raw(3, -3)]);
        let output = evaluate_functional("gamma2", &kernel, &noncanonical).unwrap();
        assert_eq!(output.record().values, canonical.record().values);
        assert_eq!(output.record().config_hash, canonical.record().config_hash);
        assert_eq!(
            output.record().witness_refs,
            canonical.record().witness_refs
        );
        assert_ne!(output.record().input_hash, canonical.record().input_hash);
        assert_eq!(
            encode(
                replay_functional_record("gamma2", &kernel, &noncanonical, output.record())
                    .unwrap()
                    .record()
            )
            .unwrap(),
            encode(output.record()).unwrap()
        );
        assert_eq!(
            replay_functional_record("gamma2", &kernel, &state(), output.record()).unwrap_err(),
            FunctionalError::RecordMismatch
        );
    }

    #[test]
    fn emitted_references_are_actual_evidence_not_fabricated_solver_or_authority() {
        for (name, kernel, input) in [
            ("phi1", phi1(), FunctionalInput::Phi1(certificate())),
            ("gamma2", gamma2(), state()),
        ] {
            let output = evaluate_functional(name, &kernel, &input).unwrap();
            let record = output.record();
            assert_eq!(record.schema, "core.functional.measurement.v1");
            assert_eq!(record.authority_effect, FunctionalAuthorityEffect::None);
            assert_eq!(record.range_behavior, FunctionalRange::UnboundedAllowed);
            assert!(record.solver_refs.is_empty() && record.observable_refs.is_empty());
            let json = serde_json::to_value(record).unwrap();
            assert_eq!(json["authority_effect"], "None");
            for forbidden in [
                "is_closed",
                "verdict",
                "terminal",
                "license",
                "rank",
                "accepted",
            ] {
                assert!(json.get(forbidden).is_none(), "{forbidden}");
            }
            match output.evidence() {
                FunctionalEvidence::Phi1(checked) => {
                    assert_eq!(
                        record.certificate_refs,
                        vec![hash_typed("phi1-certificate", checked.certificate()).unwrap()]
                    );
                    assert_eq!(
                        record.witness_refs,
                        vec![
                            hash_typed(
                                "phi1-primal",
                                &(checked.alpha(), checked.primal_residual())
                            )
                            .unwrap(),
                            hash_typed("phi1-dual", checked.dual_witness()).unwrap(),
                        ]
                    );
                }
                FunctionalEvidence::Gamma2(checked) => {
                    assert!(record.certificate_refs.is_empty());
                    assert_eq!(
                        record.witness_refs,
                        vec![
                            hash_typed("gamma2-complex", checked.complex()).unwrap(),
                            hash_typed("gamma2-residual", checked.residual()).unwrap(),
                            hash_typed("gamma2-coboundary", checked.coboundary()).unwrap(),
                        ]
                    );
                }
            }
        }
    }

    fn mutate_claim_field_low(claim: &mut UntrustedFunctionalRecord, field: usize) -> bool {
        match field {
            0 => claim.schema.push_str(".forged"),
            1 => claim.functional_id = "phi1".to_owned(),
            2 => claim.functional_version += 1,
            3 => claim.input_hash[0] ^= 1,
            4 => claim.config_hash[0] ^= 1,
            5 => claim.values[0] = q(0),
            _ => return false,
        }
        true
    }

    fn mutate_claim_field_high(claim: &mut UntrustedFunctionalRecord, field: usize) {
        match field {
            6 => claim.witness_refs[0][0] ^= 1,
            7 => claim.certificate_refs.push([1; 32]),
            8 => claim.solver_refs.push([1; 32]),
            9 => claim.observable_refs.push([1; 32]),
            10 => claim.witness_refs.swap(0, 1),
            _ => claim.values.push(q(1)),
        }
    }

    #[test]
    fn every_record_field_is_checked_on_replay_even_with_a_rehashed_claim() {
        let original = evaluate_functional("gamma2", &gamma2(), &state()).unwrap();
        for field in 0..12 {
            let mut claim = original.record().clone();
            if !mutate_claim_field_low(&mut claim, field) {
                mutate_claim_field_high(&mut claim, field);
            }
            claim.output_hash = output_commitment(&claim).unwrap();
            assert_ne!(
                claim.output_hash,
                original.record().output_hash,
                "field {field}"
            );
            assert_eq!(
                replay_functional_record("gamma2", &gamma2(), &state(), &claim).unwrap_err(),
                FunctionalError::RecordMismatch,
                "field {field}"
            );
        }
        let mut bad_hash = original.record().clone();
        bad_hash.output_hash[0] ^= 1;
        assert_eq!(
            replay_functional_record("gamma2", &gamma2(), &state(), &bad_hash).unwrap_err(),
            FunctionalError::RecordMismatch
        );
        let restored: UntrustedFunctionalRecord =
            serde_json::from_slice(&encode(original.record()).unwrap()).unwrap();
        assert_eq!(
            encode(
                replay_functional_record("gamma2", &gamma2(), &state(), &restored)
                    .unwrap()
                    .record()
            )
            .unwrap(),
            encode(original.record()).unwrap()
        );
    }

    #[test]
    fn untrusted_record_zero_denominator_is_refused_without_rational_comparison() {
        let original = evaluate_functional("gamma2", &gamma2(), &state()).unwrap();
        let mut claim = original.record().clone();
        claim.values[0] = BigRational::new_raw(1.into(), 0.into());
        assert_eq!(
            replay_functional_record("gamma2", &gamma2(), &state(), &claim).unwrap_err(),
            FunctionalError::RecordMismatch
        );
    }

    #[test]
    fn wire_shape_rejects_unknown_duplicate_and_forged_authority_fields() {
        let output = evaluate_functional("gamma2", &gamma2(), &state()).unwrap();
        let mut json = serde_json::to_value(output.record()).unwrap();
        json["authority_effect"] = serde_json::json!("FactOnly");
        assert!(serde_json::from_value::<UntrustedFunctionalRecord>(json).is_err());
        let mut json = serde_json::to_value(output.record()).unwrap();
        json["range_behavior"] = serde_json::json!("Clamped");
        assert!(serde_json::from_value::<UntrustedFunctionalRecord>(json).is_err());
        let mut json = serde_json::to_value(output.record()).unwrap();
        json["accepted"] = serde_json::json!(true);
        assert!(serde_json::from_value::<UntrustedFunctionalRecord>(json).is_err());
        let bytes = String::from_utf8(encode(output.record()).unwrap()).unwrap();
        let duplicate = bytes.replacen('{', "{\"functional_version\":99,", 1);
        assert!(serde_json::from_str::<UntrustedFunctionalRecord>(&duplicate).is_err());
        let mut input = serde_json::to_value(state()).unwrap();
        input["provider_passed"] = serde_json::json!(true);
        assert!(serde_json::from_value::<FunctionalInput>(input).is_err());
        let input = String::from_utf8(encode(&state()).unwrap()).unwrap();
        let duplicate = input.replacen('{', "{\"kind\":\"phi1\",", 1);
        assert!(serde_json::from_str::<FunctionalInput>(&duplicate).is_err());
    }

    #[test]
    fn domain_separation_and_self_hash_exclusion_are_explicit() {
        assert_ne!(
            hash_typed("input", &[1, 2]).unwrap(),
            hash_typed("output", &[1, 2]).unwrap()
        );
        assert_ne!(
            hash_typed("ab", &"c").unwrap(),
            hash_typed("a", &"bc").unwrap()
        );
        let output = evaluate_functional("gamma2", &gamma2(), &state()).unwrap();
        let mut claim = output.record().clone();
        let expected = output_commitment(&claim).unwrap();
        claim.output_hash = [255; 32];
        assert_eq!(output_commitment(&claim).unwrap(), expected);
        assert_eq!(output.record().output_hash, expected);
    }

    #[test]
    fn independent_python_vectors_bind_every_serialized_record_field() {
        let vectors: serde_json::Value = serde_json::from_str(include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../tests/core_functional/fixtures/functional_factory_vectors.json"
        )))
        .unwrap();
        assert_eq!(vectors["AuthorityEffect"], "None");
        let cases = vectors["cases"].as_array().unwrap();
        assert_eq!(cases.len(), 2);
        for case in cases {
            let name = case["name"].as_str().unwrap();
            let (kernel, input) = match name {
                "phi1" => (phi1(), FunctionalInput::Phi1(certificate())),
                "gamma2" => (gamma2(), state()),
                _ => panic!("undeclared independent fixture"),
            };
            assert_eq!(serde_json::to_value(&input).unwrap(), case["input"]);
            let output = evaluate_functional(name, &kernel, &input).unwrap();
            assert_eq!(
                serde_json::to_value(output.record()).unwrap(),
                case["expected_record"],
                "{name}"
            );
            let wire: UntrustedFunctionalRecord =
                serde_json::from_value(case["expected_record"].clone()).unwrap();
            assert_eq!(
                encode(
                    replay_functional_record(name, &kernel, &input, &wire)
                        .unwrap()
                        .record()
                )
                .unwrap(),
                encode(output.record()).unwrap()
            );
        }
    }
}
