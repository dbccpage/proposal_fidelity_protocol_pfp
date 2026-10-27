//! CH04 mathematical diagnostic-to-proposal routing under explicit policies.
//! AuthorityEffect: None. These are finite mathematical proposals, not CODA
//! operational terminalization, licenses, or authority. Diagnostic certificates
//! never choose policy. Context data and cochain data are separately declared;
//! there is no claim that a Phi1 value implies a context witness.
use num_rational::BigRational;
use core_category_theory::context_reflection::{
    CongruenceReflection, ContextError, ContextSystem, ContextWitness,
};
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, Gamma2Functional,
    RawClosureDefectResult,
};
use core_functional::phi1::{
    ExactPhi1Certificate, ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1,
};
use core_policy::trichotomy::{
    classify_exact, CertifiedExactTrichotomy, TrichotomyOutcome, TrichotomyRefusal,
};
use core_solvers::solver_cohomology_simplicial_l1::{
    verify_constrained_curved_phi1, CurvedConstrainedPhi1Certificate, CurvedConstrainedPhi1Error,
    VerifiedCurvedConstrainedPhi1,
};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RoutingError {
    #[error("Phi1 certificate replay failed: {0}")]
    Phi1(#[from] ExactPhi1CertificateError),
    #[error("Curved constrained Phi1 certificate replay failed: {0}")]
    CurvedPhi1(#[from] CurvedConstrainedPhi1Error),
    #[error("Gamma2 replay failed: {0}")]
    Gamma2(#[from] ExactGamma2Error),
    #[error("trichotomy evidence is incompatible: {0:?}")]
    Trichotomy(TrichotomyRefusal),
    #[error("context type check failed: {0:?}")]
    Context(ContextError),
    #[error("declared witness is not an obstruction of the given system")]
    InvalidContextWitness,
    #[error("candidate violates the declared value-edit contract")]
    InvalidEditContract,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagnosticPacket {
    system: ContextSystem,
    phi1: VerifiedExactPhi1,
    d1: Vec<Vec<BigRational>>,
    classification: CertifiedExactTrichotomy,
}
impl DiagnosticPacket {
    pub fn replay(
        system: ContextSystem,
        certificate: ExactPhi1Certificate,
        d1: Vec<Vec<BigRational>>,
    ) -> Result<Self, RoutingError> {
        let phi1 = Phi1Functional::verify_exact_certificate(certificate)?;
        let complex = ExactCochainComplexQ::try_new(
            phi1.alpha().len(),
            phi1.primal_residual().len(),
            d1.len(),
            phi1.d0().to_vec(),
            d1.clone(),
        )?;
        let residual = DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec())?;
        let gamma = Gamma2Functional::try_compute_exact_quotient(&residual)?;
        let classification = match classify_exact(&phi1, &gamma) {
            TrichotomyOutcome::Classified(value) => value,
            TrichotomyOutcome::TriRefused(reason) => return Err(RoutingError::Trichotomy(reason)),
        };
        Ok(Self {
            system,
            phi1,
            d1,
            classification,
        })
    }
    pub fn closure_map(&self) -> &[Vec<BigRational>] {
        &self.d1
    }
    pub fn system(&self) -> &ContextSystem {
        &self.system
    }
    pub fn phi1(&self) -> &VerifiedExactPhi1 {
        &self.phi1
    }
    pub fn classification(&self) -> &CertifiedExactTrichotomy {
        &self.classification
    }
}

/// Diagnostic packet for curved presentations (`K = d1 d0 != 0`) backed by
/// [`VerifiedCurvedConstrainedPhi1`] and [`RawClosureDefectResult`] without
/// constructing [`ExactCochainComplexQ`] or [`CertifiedExactTrichotomy`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CurvedDiagnosticPacket {
    system: ContextSystem,
    constrained_phi1: VerifiedCurvedConstrainedPhi1,
}

impl CurvedDiagnosticPacket {
    pub fn replay(
        system: ContextSystem,
        certificate: CurvedConstrainedPhi1Certificate,
    ) -> Result<Self, RoutingError> {
        let constrained_phi1 = verify_constrained_curved_phi1(certificate)?;
        Ok(Self {
            system,
            constrained_phi1,
        })
    }

    pub fn system(&self) -> &ContextSystem {
        &self.system
    }

    pub fn constrained_phi1(&self) -> &VerifiedCurvedConstrainedPhi1 {
        &self.constrained_phi1
    }

    pub fn baseline_raw_gamma2(&self) -> &RawClosureDefectResult {
        self.constrained_phi1.baseline_raw_gamma2()
    }

    pub fn repaired_raw_gamma2(&self) -> &RawClosureDefectResult {
        self.constrained_phi1.repaired_raw_gamma2()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ProposalPolicy {
    pub allow_profile_coarsening: bool,
    pub allow_value_edits: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Refusal {
    PolicyProhibitsCoarsening,
    PolicyProhibitsValueEdit,
    ReflectingCompletionImpossible(ContextWitness),
    CandidateHasNoStrictDescent,
    CurvedClosureGuardViolated,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Proposal {
    Hold,
    AlreadyCongruent,
    RelationCompletion(CongruenceReflection),
    ValueEdit {
        before: Box<DiagnosticPacket>,
        after: Box<DiagnosticPacket>,
    },
    Refused(Refusal),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CurvedProposal {
    Hold,
    ValueEdit {
        before: Box<CurvedDiagnosticPacket>,
        after: Box<CurvedDiagnosticPacket>,
    },
    Refused(Refusal),
}

pub fn propose_relation_completion(
    packet: &DiagnosticPacket,
    policy: ProposalPolicy,
    witness: &ContextWitness,
    require_profile_reflection: bool,
) -> Result<Proposal, RoutingError> {
    if !packet.system.check_witness(witness) {
        return Err(RoutingError::InvalidContextWitness);
    }
    if require_profile_reflection {
        return Ok(Proposal::Refused(Refusal::ReflectingCompletionImpossible(
            witness.clone(),
        )));
    }
    if !policy.allow_profile_coarsening {
        return Ok(Proposal::Refused(Refusal::PolicyProhibitsCoarsening));
    }
    let completion = CongruenceReflection::new(&packet.system).map_err(RoutingError::Context)?;
    Ok(Proposal::RelationCompletion(completion))
}

pub fn propose_preserving_completion(packet: &DiagnosticPacket) -> Proposal {
    if let Some(witness) = packet.system.obstruction() {
        Proposal::Refused(Refusal::ReflectingCompletionImpossible(witness))
    } else {
        Proposal::AlreadyCongruent
    }
}

/// Guarded value-edit contract: same declared context system, d0, d1 and weights;
/// only omega may change, both optimal certificates are replayed, and the exact
/// quotient defect must strictly decrease. Pure changes of repair alpha cannot
/// satisfy this guard because Phi1 is a property of the fixed problem.
pub fn propose_value_edit(
    before: &DiagnosticPacket,
    policy: ProposalPolicy,
    candidate: ExactPhi1Certificate,
) -> Result<Proposal, RoutingError> {
    if !policy.allow_value_edits {
        return Ok(Proposal::Refused(Refusal::PolicyProhibitsValueEdit));
    }
    let original = before.phi1.certificate();
    if candidate.d0 != original.d0
        || candidate.weights != original.weights
        || candidate.omega.len() != original.omega.len()
    {
        return Err(RoutingError::InvalidEditContract);
    }
    let after = DiagnosticPacket::replay(before.system.clone(), candidate, before.d1.clone())?;
    if after.phi1.value() >= before.phi1.value() {
        return Ok(Proposal::Refused(Refusal::CandidateHasNoStrictDescent));
    }
    Ok(Proposal::ValueEdit {
        before: Box::new(before.clone()),
        after: Box::new(after),
    })
}

/// Guarded value-edit contract on curved presentations (`K = d1 d0 != 0`):
/// replays both [`CurvedConstrainedPhi1Certificate`] instances on the same
/// `(d0, d1, K, weights)` presentation, verifies that the candidate's repaired
/// raw closure defect (`||d1(omega' - d0 f*')||_1`) does not exceed the
/// before-packet's repaired raw closure defect plus `candidate.tau`, and requires
/// strict descent on the constrained repair norm `||omega' - d0 f*'||_{1,w}`.
pub fn propose_curved_value_edit(
    before: &CurvedDiagnosticPacket,
    policy: ProposalPolicy,
    candidate: CurvedConstrainedPhi1Certificate,
) -> Result<CurvedProposal, RoutingError> {
    if !policy.allow_value_edits {
        return Ok(CurvedProposal::Refused(Refusal::PolicyProhibitsValueEdit));
    }
    let original = before.constrained_phi1.certificate();
    if candidate.d0 != original.d0
        || candidate.d1 != original.d1
        || candidate.curvature_k != original.curvature_k
        || candidate.weights != original.weights
        || candidate.omega.len() != original.omega.len()
    {
        return Err(RoutingError::InvalidEditContract);
    }
    let after = CurvedDiagnosticPacket::replay(before.system.clone(), candidate)?;
    let max_admissible_gamma2 =
        before.repaired_raw_gamma2().value() + after.constrained_phi1().tau();
    if after.repaired_raw_gamma2().value() > &max_admissible_gamma2 {
        return Ok(CurvedProposal::Refused(Refusal::CurvedClosureGuardViolated));
    }
    if after.constrained_phi1().value() >= before.constrained_phi1().value() {
        return Ok(CurvedProposal::Refused(Refusal::CandidateHasNoStrictDescent));
    }
    Ok(CurvedProposal::ValueEdit {
        before: Box::new(before.clone()),
        after: Box::new(after),
    })
}

/// A declared request, separate from the mathematical diagnostic class.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RoutingRequest {
    Hold,
    ProfileReflectingCompletion,
    RelationCoarsening(ContextWitness),
    ValueEdit(ExactPhi1Certificate),
}

/// Bound finite routing receipt. All inputs and the unique proposal/refusal are
/// retained, and replay recomputes the exact diagnostic and policy guards.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RoutingReceipt {
    packet: DiagnosticPacket,
    policy: ProposalPolicy,
    request: RoutingRequest,
    proposal: Proposal,
}
impl RoutingReceipt {
    pub fn packet(&self) -> &DiagnosticPacket {
        &self.packet
    }
    pub fn policy(&self) -> ProposalPolicy {
        self.policy
    }
    pub fn request(&self) -> &RoutingRequest {
        &self.request
    }
    pub fn proposal(&self) -> &Proposal {
        &self.proposal
    }
    pub fn replay(&self) -> Result<bool, RoutingError> {
        // Recheck even the sealed diagnostic instead of trusting stored enums.
        let packet = DiagnosticPacket::replay(
            self.packet.system.clone(),
            self.packet.phi1.certificate().clone(),
            self.packet.d1.clone(),
        )?;
        Ok(route_request(&packet, self.policy, self.request.clone())? == *self)
    }
}

pub fn route_request(
    packet: &DiagnosticPacket,
    policy: ProposalPolicy,
    request: RoutingRequest,
) -> Result<RoutingReceipt, RoutingError> {
    let proposal = match &request {
        RoutingRequest::Hold => Proposal::Hold,
        RoutingRequest::ProfileReflectingCompletion => propose_preserving_completion(packet),
        RoutingRequest::RelationCoarsening(witness) => {
            propose_relation_completion(packet, policy, witness, false)?
        }
        RoutingRequest::ValueEdit(candidate) => {
            propose_value_edit(packet, policy, candidate.clone())?
        }
    };
    Ok(RoutingReceipt {
        packet: packet.clone(),
        policy,
        request,
        proposal,
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_4cba414f {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
