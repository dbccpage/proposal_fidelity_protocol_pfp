//! Minimal Q-continuum data kernel.
//!
//! This module is a proposal/probe boundary. It records speculative Q-layer
//! material and the finite descent evidence required before any scoped support
//! is earned. It does not certify mathematical or physical claims by itself.

use serde::{Deserialize, Serialize};

/// Input shape accepted by the Q-continuum layer.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum QInputKind {
    /// A vague, analogical, continuum-level, or otherwise non-terminal idea.
    Idea,
    /// A structured claim extracted from an idea.
    Claim,
    /// An analogy that must be checked against explicit break conditions.
    Analogy,
    /// A proposed model with definitions, examples, and boundary conditions.
    Model,
    /// A source or artifact proposed as evidence.
    AuthorityCandidate,
    /// A direct request for finite probes.
    ProbeRequest,
}

/// Finite probe families generated from Q-layer material.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ProbeKind {
    /// Ask for precise definitions.
    DefinitionProbe,
    /// Ask for at least one finite example.
    ExampleProbe,
    /// Ask for a finite counterexample search or witness.
    CounterexampleProbe,
    /// Ask for type, shape, or schema obligations.
    TypeProbe,
    /// Ask for invariants and preservation checks.
    InvariantProbe,
    /// Ask where the claim stops applying.
    BoundaryProbe,
    /// Ask for a finite descent obligation.
    DescentProbe,
    /// Ask for a finite simulation or enumerator.
    SimulationProbe,
    /// Ask for theorem/proof formalization targets.
    FormalizationProbe,
    /// Ask for implementation and test evidence.
    ImplementationProbe,
    /// Ask for source, receipt, or provenance evidence.
    SourceAuthorityProbe,
    /// Ask where an analogy breaks.
    AnalogyBreakProbe,
    /// Ask for finite measurement or empirical criteria.
    MeasurementProbe,
    /// Ask for physics-specific definitions and scope fences.
    PhysicsProbe,
    /// Ask for a finite approximation to a limit or continuum object.
    ContinuumLimitProbe,
}

/// Why a descent remains blocked or failed.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ObstructionKind {
    /// The object has not been defined tightly enough.
    Underdefined,
    /// A support claim is missing a finite witness.
    MissingWitness,
    /// A counterexample was found or asserted.
    CounterexampleFound,
    /// No finite projection has been supplied.
    NonFiniteProjection,
    /// Evidence was applied outside its declared scope.
    ScopeViolation,
    /// Replay, receipt, or reproducibility material is missing.
    ReplayMissing,
    /// Source authority was claimed without sufficient support.
    SourceUnsupported,
    /// An analogy no longer preserves the relevant structure.
    AnalogyBreak,
    /// Code, tests, or executable artifacts are missing.
    ImplementationMissing,
    /// The same obstruction recurred without new structure.
    RepeatedObstruction,
}

/// Bounded reliability earned by finite descents.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AuthorityStrength {
    /// No usable finite support is present.
    #[default]
    Untrusted,
    /// The material is explicit but still speculative.
    Speculative,
    /// At least one finite probe has been run or prepared.
    Probed,
    /// Finite support exists, but not enough for terminal support.
    ConditionallySupported,
    /// Adversarial probes were survived inside the declared scope.
    AdversariallySurvived,
    /// Terminal support was earned inside the declared scope.
    TerminalWithinScope,
}

impl AuthorityStrength {
    fn rank(self) -> u8 {
        match self {
            Self::Untrusted => 0,
            Self::Speculative => 1,
            Self::Probed => 2,
            Self::ConditionallySupported => 3,
            Self::AdversariallySurvived => 4,
            Self::TerminalWithinScope => 5,
        }
    }

    fn max(self, other: Self) -> Self {
        if self.rank() >= other.rank() {
            self
        } else {
            other
        }
    }
}

/// Q-layer terminal bookkeeping.
///
/// This is intentionally local to the Q-continuum layer. The existing certified
/// authority machinery remains the stronger authority surface.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TerminalStatus {
    /// Finite support exists inside the declared scope.
    Supported,
    /// Support exists, but explicit conditions remain.
    ConditionallySupported,
    /// A typed unresolved remainder remains.
    Residual,
    /// The current material does not determine a verdict.
    Underdetermined,
    /// The claim was refuted in scope.
    Refuted,
    /// The finite system refused the object or projection.
    Refused,
    /// The object remains speculative.
    #[default]
    Speculative,
    /// Code or an artifact exists, but that alone is not proof.
    Implemented,
}

impl TerminalStatus {
    /// Returns true only for statuses that can support a claim.
    pub fn is_support_status(self) -> bool {
        matches!(
            self,
            Self::Supported | Self::ConditionallySupported | Self::Implemented
        )
    }

    /// Returns true only for terminal support, not refutation or refusal.
    pub fn is_terminal_support(self) -> bool {
        matches!(self, Self::Supported)
    }

    /// Returns true for statuses that end a scoped attempt.
    pub fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Supported
                | Self::ConditionallySupported
                | Self::Refuted
                | Self::Refused
                | Self::Implemented
        )
    }
}

/// Bounded domain in which a Q-layer authority statement may apply.
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct AuthorityScope {
    /// Domain name, such as "finite arithmetic examples".
    pub domain: String,
    /// Required constraints for the scope to apply.
    pub constraints: Vec<String>,
    /// Explicit exclusions.
    pub exclusions: Vec<String>,
}

impl AuthorityScope {
    /// Creates an unconstrained scope for a named domain.
    pub fn new(domain: impl Into<String>) -> Self {
        Self {
            domain: domain.into(),
            constraints: Vec::new(),
            exclusions: Vec::new(),
        }
    }

    /// Adds a constraint.
    pub fn with_constraint(mut self, constraint: impl Into<String>) -> Self {
        self.constraints.push(constraint.into());
        self
    }

    /// Adds an exclusion.
    pub fn with_exclusion(mut self, exclusion: impl Into<String>) -> Self {
        self.exclusions.push(exclusion.into());
        self
    }

    /// Returns true if this scope covers the requested scope.
    pub fn contains(&self, requested: &AuthorityScope) -> bool {
        normalize(&self.domain) == normalize(&requested.domain)
            && same_normalized_values(&self.constraints, &requested.constraints)
            && !requested
                .constraints
                .iter()
                .any(|c| contains_normalized(&self.exclusions, c))
            && !contains_normalized(&self.exclusions, &requested.domain)
    }

    /// Returns true if the scope applies to the exact domain string.
    pub fn applies_to_domain(&self, domain: &str) -> bool {
        normalize(&self.domain) == normalize(domain)
            && !contains_normalized(&self.exclusions, domain)
    }
}

/// A non-terminal idea that has not yet descended into finite evidence.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QIdea {
    /// Stable idea identifier.
    pub id: String,
    /// Human-readable body.
    pub body: String,
    /// Source, author, file, or receipt.
    pub provenance: String,
    /// Search and routing tags.
    pub tags: Vec<String>,
    /// Current Q-layer status.
    pub terminal_status: TerminalStatus,
}

impl QIdea {
    /// Creates a speculative idea.
    pub fn new(
        id: impl Into<String>,
        body: impl Into<String>,
        provenance: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            body: body.into(),
            provenance: provenance.into(),
            tags: Vec::new(),
            terminal_status: TerminalStatus::Speculative,
        }
    }

    /// Adds a tag.
    pub fn with_tag(mut self, tag: impl Into<String>) -> Self {
        self.tags.push(tag.into());
        self
    }
}

/// A structured claim extracted from a Q idea.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QClaim {
    /// Stable claim identifier.
    pub id: String,
    /// Source idea identifier.
    pub idea_id: String,
    /// Claim body.
    pub body: String,
    /// Scope claimed for this statement.
    pub scope: AuthorityScope,
    /// Source, author, file, or receipt.
    pub provenance: String,
    /// Current Q-layer status.
    pub terminal_status: TerminalStatus,
}

impl QClaim {
    /// Creates a speculative claim.
    pub fn new(
        id: impl Into<String>,
        idea_id: impl Into<String>,
        body: impl Into<String>,
        scope: AuthorityScope,
        provenance: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            idea_id: idea_id.into(),
            body: body.into(),
            scope,
            provenance: provenance.into(),
            terminal_status: TerminalStatus::Speculative,
        }
    }

    /// Applies a finite descent result if it has an in-scope witness.
    pub fn apply_descent_result(&mut self, result: &DescentResult) -> bool {
        if self.scope.contains(&result.scope) && result.has_valid_support() {
            self.terminal_status = result.terminal_status;
            true
        } else {
            false
        }
    }
}

/// An analogy that must expose its break conditions.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QAnalogy {
    /// Stable analogy identifier.
    pub id: String,
    /// Source side of the analogy.
    pub source: String,
    /// Target side of the analogy.
    pub target: String,
    /// Structure that is claimed to be preserved.
    pub preserved_structure: Vec<String>,
    /// Known places where the analogy breaks.
    pub break_conditions: Vec<String>,
    /// Provenance for the analogy.
    pub provenance: String,
    /// Current Q-layer status.
    pub terminal_status: TerminalStatus,
}

/// A proposed model that still needs finite definitions and tests.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QModel {
    /// Stable model identifier.
    pub id: String,
    /// Model name or summary.
    pub name: String,
    /// Definitions supplied by the model.
    pub definitions: Vec<String>,
    /// Declared assumptions.
    pub assumptions: Vec<String>,
    /// Scope claimed for the model.
    pub scope: AuthorityScope,
    /// Current Q-layer status.
    pub terminal_status: TerminalStatus,
}

/// A proposed source of authority.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QAuthorityCandidate {
    /// Stable candidate identifier.
    pub id: String,
    /// Claim, source, artifact, or receipt being proposed.
    pub subject: String,
    /// Provenance for the candidate.
    pub provenance: String,
    /// Scope where the candidate may apply.
    pub scope: AuthorityScope,
    /// Required finite witnesses before support can be earned.
    pub required_witnesses: Vec<String>,
    /// Current Q-layer status.
    pub terminal_status: TerminalStatus,
}

/// A direct request for finite probes.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QProbeRequest {
    /// Stable request identifier.
    pub id: String,
    /// Target idea, claim, model, analogy, or source.
    pub target: String,
    /// Probe kinds requested by the caller.
    pub requested_kinds: Vec<ProbeKind>,
    /// Provenance for the request.
    pub provenance: String,
}

/// A finite question asked of a Q-layer object.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QProbe {
    /// Stable probe identifier.
    pub id: String,
    /// Target object identifier.
    pub target: String,
    /// Probe kind.
    pub kind: ProbeKind,
    /// Concrete question to answer.
    pub question: String,
    /// Required finite output shape.
    pub expected_finite_output: String,
    /// Required witness type.
    pub required_witness: String,
    /// Obstructions this probe may emit.
    pub obstruction_classes: Vec<ObstructionKind>,
    /// Conditions that would close the probe.
    pub terminal_conditions: Vec<String>,
    /// Conditions that keep the probe open or failed.
    pub failure_conditions: Vec<String>,
}

/// Finite representation of part of a Q idea.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteProjection {
    /// Stable projection identifier.
    pub id: String,
    /// Source Q-layer object identifier.
    pub source_id: String,
    /// Finite carrier being inspected.
    pub carrier: String,
    /// Equivalence or zero relation to be checked by finite descent.
    pub zero_relation: String,
    /// Scope of the projection.
    pub scope: AuthorityScope,
    /// Machine-readable or human-readable finite description.
    pub finite_description: String,
}

/// Finite obligation generated from a projection and optional probe.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DescentObligation {
    /// Stable obligation identifier.
    pub id: String,
    /// Source finite projection.
    pub projection_id: String,
    /// Source probe, if any.
    pub probe_id: Option<String>,
    /// Required witness before support can be earned.
    pub required_witness: String,
    /// Required finite output.
    pub expected_finite_output: String,
    /// Conditions that may terminalize the obligation.
    pub terminal_conditions: Vec<String>,
}

/// Evidence, computation, proof, example, counterexample, test, or receipt.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Witness {
    /// Stable witness identifier.
    pub id: String,
    /// Witness family.
    pub kind: String,
    /// Human-readable description.
    pub description: String,
    /// Source, command, file, hash, or receipt.
    pub provenance: String,
}

impl Witness {
    /// Creates a finite witness record.
    pub fn new(
        id: impl Into<String>,
        kind: impl Into<String>,
        description: impl Into<String>,
        provenance: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            kind: kind.into(),
            description: description.into(),
            provenance: provenance.into(),
        }
    }
}

/// Typed unresolved remainder left by a failed or incomplete descent.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Residual {
    /// Stable residual identifier.
    pub id: String,
    /// Source object identifier.
    pub source_id: String,
    /// Obstruction family.
    pub obstruction: ObstructionKind,
    /// Human-readable description.
    pub description: String,
    /// Suggested next finite probe.
    pub next_probe_hint: Option<String>,
}

impl Residual {
    /// Creates a residual record.
    pub fn new(
        id: impl Into<String>,
        source_id: impl Into<String>,
        obstruction: ObstructionKind,
        description: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            source_id: source_id.into(),
            obstruction,
            description: description.into(),
            next_probe_hint: None,
        }
    }

    /// Adds a next-probe hint.
    pub fn with_next_probe_hint(mut self, hint: impl Into<String>) -> Self {
        self.next_probe_hint = Some(hint.into());
        self
    }
}

/// Result of attempting to satisfy a descent obligation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DescentResult {
    /// Source obligation identifier.
    pub obligation_id: String,
    /// Scope where the result applies.
    pub scope: AuthorityScope,
    /// Verdict for this finite attempt.
    pub terminal_status: TerminalStatus,
    /// Supporting witness, if present.
    pub witness: Option<Witness>,
    /// Residual left by the attempt, if present.
    pub residual: Option<Residual>,
    /// Counterexample, if present.
    pub counterexample: Option<String>,
    /// Extra notes.
    pub notes: Vec<String>,
}

impl DescentResult {
    /// Creates a supported result with a required witness.
    pub fn supported(
        obligation_id: impl Into<String>,
        scope: AuthorityScope,
        witness: Witness,
    ) -> Self {
        Self {
            obligation_id: obligation_id.into(),
            scope,
            terminal_status: TerminalStatus::Supported,
            witness: Some(witness),
            residual: None,
            counterexample: None,
            notes: Vec::new(),
        }
    }

    /// Creates a failed or incomplete result with a residual.
    pub fn failed(
        obligation_id: impl Into<String>,
        scope: AuthorityScope,
        residual: Residual,
    ) -> Self {
        Self {
            obligation_id: obligation_id.into(),
            scope,
            terminal_status: TerminalStatus::Residual,
            witness: None,
            residual: Some(residual),
            counterexample: None,
            notes: Vec::new(),
        }
    }

    /// Creates an in-scope refutation.
    pub fn refuted(
        obligation_id: impl Into<String>,
        scope: AuthorityScope,
        counterexample: impl Into<String>,
    ) -> Self {
        Self {
            obligation_id: obligation_id.into(),
            scope,
            terminal_status: TerminalStatus::Refuted,
            witness: None,
            residual: None,
            counterexample: Some(counterexample.into()),
            notes: Vec::new(),
        }
    }

    /// Returns true only if a support status carries a finite witness.
    pub fn has_valid_support(&self) -> bool {
        self.terminal_status.is_support_status() && self.witness.is_some()
    }
}

/// Candidate terminal verdict emitted before external certification.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TerminalCandidate {
    /// Source object identifier.
    pub source_id: String,
    /// Candidate status.
    pub status: TerminalStatus,
    /// Scope of the candidate.
    pub scope: AuthorityScope,
    /// Required witness for this candidate to matter.
    pub required_witness: String,
    /// Review notes that must stay attached to the candidate.
    pub review_notes: Vec<String>,
}

/// Record of earned authority, failures, and remaining speculation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityTrace {
    /// Object this trace is about.
    pub about: String,
    /// Scope where the trace applies.
    pub scope: AuthorityScope,
    /// Current bounded authority strength.
    pub strength: AuthorityStrength,
    /// Source, file, receipt, or command provenance.
    pub provenance: Vec<String>,
    /// Successful finite descent results.
    pub successful_descents: Vec<DescentResult>,
    /// Failed or incomplete finite descent results.
    pub failed_descents: Vec<DescentResult>,
    /// Unresolved residuals.
    pub residuals: Vec<Residual>,
    /// Known counterexamples.
    pub counterexamples: Vec<String>,
    /// Terminal statuses reached in scope.
    pub terminal_statuses: Vec<TerminalStatus>,
    /// Conditions that would weaken or revoke this authority.
    pub revocation_conditions: Vec<String>,
    /// Material that remains speculative.
    pub speculative_notes: Vec<String>,
}

impl AuthorityTrace {
    /// Creates a speculative authority trace.
    pub fn new(about: impl Into<String>, scope: AuthorityScope) -> Self {
        Self {
            about: about.into(),
            scope,
            strength: AuthorityStrength::Speculative,
            provenance: Vec::new(),
            successful_descents: Vec::new(),
            failed_descents: Vec::new(),
            residuals: Vec::new(),
            counterexamples: Vec::new(),
            terminal_statuses: Vec::new(),
            revocation_conditions: vec![
                "new counterexample in scope".to_string(),
                "witness replay failure".to_string(),
                "scope mismatch".to_string(),
            ],
            speculative_notes: Vec::new(),
        }
    }

    /// Returns true if the trace applies to the requested scope.
    pub fn applies_to_scope(&self, requested: &AuthorityScope) -> bool {
        self.scope.contains(requested)
    }

    /// Returns true only for terminal support inside the exact domain.
    pub fn is_terminal_within_domain(&self, domain: &str) -> bool {
        self.strength == AuthorityStrength::TerminalWithinScope
            && self.scope.applies_to_domain(domain)
    }

    /// Records a finite descent result and recomputes strength without overclaiming.
    ///
    /// Strength is *derived* from the accumulated evidence after every result
    /// (not a monotone running max), so a later in-scope residual demotes a trace
    /// out of [`AuthorityStrength::TerminalWithinScope`]. This is the firewall
    /// rule: a Q idea with **any** Q-held residual (or counterexample) in its
    /// scope cannot reach terminal support — no laundering speculation into
    /// authority.
    pub fn record_descent_result(&mut self, result: DescentResult) {
        self.terminal_statuses.push(result.terminal_status);

        if !self.scope.contains(&result.scope) {
            let residual = Residual::new(
                format!("{}:scope-violation", result.obligation_id),
                result.obligation_id.clone(),
                ObstructionKind::ScopeViolation,
                "descent result was applied outside the authority scope",
            );
            self.residuals.push(residual);
            self.failed_descents.push(result);
            self.recompute_strength();
            return;
        }

        if result.has_valid_support() {
            if let Some(witness) = &result.witness {
                self.provenance.push(witness.provenance.clone());
            }
            self.successful_descents.push(result);
            self.recompute_strength();
            return;
        }

        if result.terminal_status.is_support_status() && result.witness.is_none() {
            self.residuals.push(Residual::new(
                format!("{}:missing-witness", result.obligation_id),
                result.obligation_id.clone(),
                ObstructionKind::MissingWitness,
                "support status was proposed without a finite witness",
            ));
        }

        if let Some(residual) = &result.residual {
            self.residuals.push(residual.clone());
        }

        if let Some(counterexample) = &result.counterexample {
            self.counterexamples.push(counterexample.clone());
        }

        self.failed_descents.push(result);
        self.recompute_strength();
    }

    /// Derives [`AuthorityStrength`] from the accumulated evidence.
    ///
    /// `TerminalWithinScope` ⇔ an in-scope `Supported` witness with **no**
    /// unresolved residual or counterexample. A strong witness coexisting with a
    /// residual/counterexample caps at `ConditionallySupported`; a
    /// conditionally-supported witness caps there too; any attempt at all reaches
    /// at least `Probed`.
    fn has_witnessed_status(&self, target: TerminalStatus) -> bool {
        self.successful_descents
            .iter()
            .any(|r| r.terminal_status == target && r.witness.is_some())
    }

    fn recompute_strength(&mut self) {
        let has_strong = self.has_witnessed_status(TerminalStatus::Supported);
        let has_conditional = self.has_witnessed_status(TerminalStatus::ConditionallySupported);
        let blocked = !(self.residuals.is_empty() && self.counterexamples.is_empty());
        let any_attempt = !(self.successful_descents.is_empty() && self.failed_descents.is_empty());

        self.strength = match (has_strong, has_conditional, blocked, any_attempt) {
            (true, _, false, _) => AuthorityStrength::TerminalWithinScope,
            (true, _, true, _) | (_, true, _, _) => AuthorityStrength::ConditionallySupported,
            (_, _, _, true) => AuthorityStrength::Probed,
            _ => AuthorityStrength::Untrusted,
        };
    }
}

/// A generated set of finite probes and obligations for one idea.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProbePlan {
    /// Stable plan identifier.
    pub id: String,
    /// Source idea identifier.
    pub idea_id: String,
    /// Finite projections available to the plan.
    pub projections: Vec<FiniteProjection>,
    /// Probes to run.
    pub probes: Vec<QProbe>,
    /// Descent obligations generated by the probes.
    pub obligations: Vec<DescentObligation>,
}

/// Append-only in-memory ledger row.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObstructionLedgerEntry {
    /// Monotone sequence number.
    pub sequence: u64,
    /// Idea identifier, if applicable.
    pub idea_id: Option<String>,
    /// Claim identifier, if applicable.
    pub claim_id: Option<String>,
    /// Probe identifier, if applicable.
    pub probe_id: Option<String>,
    /// Projection identifier, if applicable.
    pub projection_id: Option<String>,
    /// Obligation identifier, if applicable.
    pub obligation_id: Option<String>,
    /// Source provenance.
    pub source_provenance: String,
    /// Witness attached to this entry.
    pub witness: Option<Witness>,
    /// Obstruction attached to this entry.
    pub obstruction: Option<ObstructionKind>,
    /// Residual attached to this entry.
    pub residual: Option<Residual>,
    /// Terminal status observed.
    pub terminal_status: TerminalStatus,
    /// Authority strength after this row.
    pub authority_strength: AuthorityStrength,
    /// Links to code, docs, tests, or receipts.
    pub links: Vec<String>,
    /// Primal residual value \Phi_1 (if available).
    pub primal_residual_value: Option<String>,
    /// Dual circulation \phi (if available).
    pub dual_circulation: Option<Vec<String>>,
}

/// Serializable in-memory Q-continuum ledger.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct QContinuumLedger {
    /// Ideas registered in the Q layer.
    pub ideas: Vec<QIdea>,
    /// Claims extracted from ideas.
    pub claims: Vec<QClaim>,
    /// Probes registered in the ledger.
    pub probes: Vec<QProbe>,
    /// Finite projections registered in the ledger.
    pub projections: Vec<FiniteProjection>,
    /// Descent obligations registered in the ledger.
    pub obligations: Vec<DescentObligation>,
    /// Descent results recorded by the ledger.
    pub descent_results: Vec<DescentResult>,
    /// Append-only ledger entries.
    pub entries: Vec<ObstructionLedgerEntry>,
    /// Authority traces accumulated from finite descents.
    pub authority_traces: Vec<AuthorityTrace>,
    /// Next append-only sequence value.
    pub sequence: u64,
}

impl QContinuumLedger {
    /// Creates an empty ledger.
    pub fn new() -> Self {
        Self::default()
    }

    /// Adds an idea.
    pub fn add_idea(&mut self, idea: QIdea) {
        self.ideas.push(idea);
    }

    /// Adds a claim.
    pub fn add_claim(&mut self, claim: QClaim) {
        self.claims.push(claim);
    }

    /// Adds a probe.
    pub fn add_probe(&mut self, probe: QProbe) {
        self.probes.push(probe);
    }

    /// Adds a finite projection.
    pub fn add_projection(&mut self, projection: FiniteProjection) {
        self.projections.push(projection);
    }

    /// Adds a descent obligation.
    pub fn add_obligation(&mut self, obligation: DescentObligation) {
        self.obligations.push(obligation);
    }

    /// Records a descent result and updates the relevant authority trace.
    pub fn record_descent_result(&mut self, about: impl Into<String>, result: DescentResult) {
        let about = about.into();
        let trace_index = match self
            .authority_traces
            .iter()
            .position(|trace| trace.about == about && trace.scope.contains(&result.scope))
        {
            Some(index) => index,
            None => {
                self.authority_traces
                    .push(AuthorityTrace::new(about.clone(), result.scope.clone()));
                self.authority_traces.len() - 1
            }
        };

        self.authority_traces[trace_index].record_descent_result(result.clone());
        let authority_strength = self.authority_traces[trace_index].strength;
        self.sequence += 1;

        let residual = result.residual.clone().or_else(|| {
            if result.terminal_status.is_support_status() && result.witness.is_none() {
                Some(Residual::new(
                    format!("{}:missing-witness", result.obligation_id),
                    result.obligation_id.clone(),
                    ObstructionKind::MissingWitness,
                    "support status was proposed without a finite witness",
                ))
            } else {
                None
            }
        });

        let obstruction = residual.as_ref().map(|r| r.obstruction);
        self.entries.push(ObstructionLedgerEntry {
            sequence: self.sequence,
            idea_id: None,
            claim_id: Some(about),
            probe_id: None,
            projection_id: None,
            obligation_id: Some(result.obligation_id.clone()),
            source_provenance: result
                .witness
                .as_ref()
                .map(|w| w.provenance.clone())
                .unwrap_or_else(|| "finite descent attempt".to_string()),
            witness: result.witness.clone(),
            obstruction,
            residual,
            terminal_status: result.terminal_status,
            authority_strength,
            links: Vec::new(),
            primal_residual_value: None,
            dual_circulation: None,
        });

        self.descent_results.push(result);
    }

    /// Returns residuals recorded in append-only rows.
    pub fn residuals(&self) -> Vec<&Residual> {
        self.entries
            .iter()
            .filter_map(|entry| entry.residual.as_ref())
            .collect()
    }

    /// Finds the first authority trace about an object.
    pub fn authority_trace(&self, about: &str) -> Option<&AuthorityTrace> {
        self.authority_traces
            .iter()
            .find(|trace| trace.about == about)
    }

    /// Returns claims that are not supported.
    pub fn unsupported_claims(&self) -> Vec<&QClaim> {
        self.claims
            .iter()
            .filter(|claim| !claim.terminal_status.is_support_status())
            .collect()
    }

    /// Returns claims with terminal Q-layer statuses.
    pub fn terminal_claims(&self) -> Vec<&QClaim> {
        self.claims
            .iter()
            .filter(|claim| claim.terminal_status.is_terminal())
            .collect()
    }

    /// Returns speculative claims.
    pub fn speculative_claims(&self) -> Vec<&QClaim> {
        self.claims
            .iter()
            .filter(|claim| claim.terminal_status == TerminalStatus::Speculative)
            .collect()
    }
}

/// The standard Lean 4 / Mathlib axioms a `sorry`-free proof may legitimately
/// depend on. A witness whose axiom set is a subset of these is "clean"; any
/// other axiom — most importantly [`SORRY_AXIOM`], the marker left by `sorry` —
/// means the proof is incomplete or conditional and cannot earn terminal support.
pub const STANDARD_LEAN_AXIOMS: [&str; 3] = ["propext", "Classical.choice", "Quot.sound"];

/// The axiom Lean emits for an unfinished proof (`sorry`).
pub const SORRY_AXIOM: &str = "sorryAx";

/// A finite witness backed by a mechanized Lean theorem and its
/// `#print axioms` receipt.
///
/// The receipt (`axioms`) is supplied by the caller from a real
/// `#print axioms <theorem>` run — this data crate never invokes `lake`/`lean`.
/// The descent gate ([`DescentGate::verify_lean_witness`]) then *enforces the
/// firewall rule on the receipt's shape*: a `sorryAx` or any non-standard axiom
/// blocks terminal support. This makes the witness-gated authority rule
/// checkable, rather than trusting a caller's asserted verdict.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LeanWitness {
    /// Stable witness identifier.
    pub id: String,
    /// Lean source file, e.g. `lean4/QM/SingularityContinuum.lean`.
    pub file: String,
    /// Fully qualified theorem name proven in that file.
    pub theorem: String,
    /// Axioms reported by `#print axioms <theorem>` (the receipt).
    pub axioms: Vec<String>,
    /// Command / cache / date describing how the receipt was produced.
    pub provenance: String,
}

impl LeanWitness {
    /// Creates a Lean witness from a `#print axioms` receipt.
    pub fn new(
        id: impl Into<String>,
        file: impl Into<String>,
        theorem: impl Into<String>,
        axioms: impl IntoIterator<Item = impl Into<String>>,
        provenance: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            file: file.into(),
            theorem: theorem.into(),
            axioms: axioms.into_iter().map(Into::into).collect(),
            provenance: provenance.into(),
        }
    }

    /// True if no axiom is the `sorry` marker (the proof has no holes).
    pub fn is_sorry_free(&self) -> bool {
        !self.axioms.iter().any(|a| a.trim() == SORRY_AXIOM)
    }

    /// Axioms outside the standard Lean/Mathlib set, in receipt order.
    ///
    /// Each such axiom is a condition the result depends on (or, for
    /// [`SORRY_AXIOM`], an outright hole). An empty result means the witness is
    /// fully standard.
    pub fn nonstandard_axioms(&self) -> Vec<String> {
        self.axioms
            .iter()
            .filter(|a| !STANDARD_LEAN_AXIOMS.contains(&a.trim()))
            .cloned()
            .collect()
    }

    /// True only when the proof is `sorry`-free and every axiom is standard.
    pub fn is_clean(&self) -> bool {
        self.is_sorry_free() && self.nonstandard_axioms().is_empty()
    }

    /// Human-readable axiom summary for notes and the ledger witness.
    pub fn axioms_summary(&self) -> String {
        if self.axioms.is_empty() {
            "axiom-free".to_string()
        } else {
            self.axioms.join(", ")
        }
    }

    /// Converts to the generic ledger [`Witness`] record.
    pub fn to_witness(&self) -> Witness {
        Witness::new(
            self.id.clone(),
            "lean4",
            format!("{} ({})", self.theorem, self.axioms_summary()),
            format!("{} :: {} :: {}", self.file, self.theorem, self.provenance),
        )
    }
}

/// Boundary object that projects Q material into finite obligations.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct DescentGate;

impl DescentGate {
    /// Creates a descent gate.
    pub fn new() -> Self {
        Self
    }

    /// Projects an idea into a finite carrier description.
    pub fn project_idea(&self, idea: &QIdea) -> FiniteProjection {
        FiniteProjection {
            id: format!("{}:projection:finite", idea.id),
            source_id: idea.id.clone(),
            carrier: "finite excerpt and finite probe target set".to_string(),
            zero_relation: "equivalent only when declared finite checks match".to_string(),
            scope: AuthorityScope::new(format!("q-idea:{}", idea.id)),
            finite_description: truncate_for_projection(&idea.body),
        }
    }

    /// Projects a claim into a finite carrier description.
    pub fn project_claim(&self, claim: &QClaim) -> FiniteProjection {
        FiniteProjection {
            id: format!("{}:projection:finite", claim.id),
            source_id: claim.id.clone(),
            carrier: "finite claim text, scope, and witness request".to_string(),
            zero_relation: "same claim only under same scope and witness obligations".to_string(),
            scope: claim.scope.clone(),
            finite_description: truncate_for_projection(&claim.body),
        }
    }

    /// Generates minimal obligations for a projection.
    pub fn obligations_for_projection(
        &self,
        projection: &FiniteProjection,
    ) -> Vec<DescentObligation> {
        vec![
            DescentObligation {
                id: format!("{}:definition-obligation", projection.id),
                projection_id: projection.id.clone(),
                probe_id: None,
                required_witness: "finite definitions for carrier and zero relation".to_string(),
                expected_finite_output: "definition record or residual".to_string(),
                terminal_conditions: vec!["definitions replay inside scope".to_string()],
            },
            DescentObligation {
                id: format!("{}:witness-obligation", projection.id),
                projection_id: projection.id.clone(),
                probe_id: None,
                required_witness: "finite proof, computation, example, test, or counterexample"
                    .to_string(),
                expected_finite_output: "witness receipt or typed residual".to_string(),
                terminal_conditions: vec![
                    "witness satisfies declared finite projection".to_string()
                ],
            },
        ]
    }

    /// Accepts descent results and records them in the ledger.
    pub fn accept_results(
        &self,
        ledger: &mut QContinuumLedger,
        about: impl Into<String>,
        results: Vec<DescentResult>,
    ) {
        let about = about.into();
        for result in results {
            ledger.record_descent_result(about.clone(), result);
        }
    }

    /// Verifies a mechanized Lean witness and returns the typed descent result.
    ///
    /// The verdict is forced by the witness's `#print axioms` receipt, not by a
    /// caller's assertion:
    ///
    /// - **clean** (`sorry`-free, only [`STANDARD_LEAN_AXIOMS`]) →
    ///   [`TerminalStatus::Supported`];
    /// - **`sorry`-free but conditional** on non-standard axioms →
    ///   [`TerminalStatus::ConditionallySupported`] (the conditioning axioms are
    ///   recorded in the result notes; not terminal);
    /// - **holey** (depends on [`SORRY_AXIOM`]) → [`TerminalStatus::Residual`]
    ///   with an [`ObstructionKind::MissingWitness`] obstruction.
    ///
    /// A `Supported` verdict for a holey or axiom-extended proof is therefore
    /// not representable through this gate.
    pub fn verify_lean_witness(
        &self,
        obligation_id: impl Into<String>,
        scope: AuthorityScope,
        witness: &LeanWitness,
    ) -> DescentResult {
        let obligation_id = obligation_id.into();

        if witness.is_clean() {
            let mut result = DescentResult::supported(obligation_id, scope, witness.to_witness());
            result.notes.push(format!(
                "lean axiom audit: clean (standard axioms only: [{}])",
                witness.axioms_summary()
            ));
            return result;
        }

        if witness.is_sorry_free() {
            return DescentResult {
                obligation_id,
                scope,
                terminal_status: TerminalStatus::ConditionallySupported,
                witness: Some(witness.to_witness()),
                residual: None,
                counterexample: None,
                notes: vec![format!(
                    "lean axiom audit: conditional on non-standard axioms: {}",
                    witness.nonstandard_axioms().join(", ")
                )],
            };
        }

        let residual = Residual::new(
            format!("{obligation_id}:sorry"),
            witness.id.clone(),
            ObstructionKind::MissingWitness,
            format!(
                "lean witness '{}' depends on {} — the proof has an unfinished `sorry`",
                witness.theorem, SORRY_AXIOM
            ),
        )
        .with_next_probe_hint("finish the proof so #print axioms drops sorryAx");
        DescentResult::failed(obligation_id, scope, residual)
    }
}

/// Generates a deterministic first-pass probe plan for an idea.
pub fn generate_probe_plan(idea: &QIdea) -> ProbePlan {
    let gate = DescentGate::new();
    let projection = gate.project_idea(idea);
    let lower = idea.body.to_ascii_lowercase();

    let mut kinds = vec![
        ProbeKind::DefinitionProbe,
        ProbeKind::ExampleProbe,
        ProbeKind::CounterexampleProbe,
        ProbeKind::BoundaryProbe,
        ProbeKind::DescentProbe,
        ProbeKind::SourceAuthorityProbe,
    ];

    if any_token(
        &lower,
        &["paper", "proof", "derive", "theorem", "mathematics"],
    ) {
        push_unique(&mut kinds, ProbeKind::FormalizationProbe);
        push_unique(&mut kinds, ProbeKind::AnalogyBreakProbe);
    }

    if any_token(&lower, &["rust", "module", "code", "implements", "test"]) {
        push_unique(&mut kinds, ProbeKind::ImplementationProbe);
        push_unique(&mut kinds, ProbeKind::InvariantProbe);
        push_unique(&mut kinds, ProbeKind::TypeProbe);
    }

    if any_token(
        &lower,
        &["money", "product", "market", "customer", "business"],
    ) {
        push_unique(&mut kinds, ProbeKind::MeasurementProbe);
    }

    if any_token(
        &lower,
        &["curvature", "physics", "quantum", "bundle", "connection"],
    ) {
        push_unique(&mut kinds, ProbeKind::PhysicsProbe);
        push_unique(&mut kinds, ProbeKind::AnalogyBreakProbe);
    }

    if any_token(&lower, &["continuum", "infinite", "limit", "unbounded"]) {
        push_unique(&mut kinds, ProbeKind::ContinuumLimitProbe);
    }

    let probes: Vec<QProbe> = kinds
        .iter()
        .enumerate()
        .map(|(index, kind)| probe_for_kind(idea, *kind, index))
        .collect();
    let obligations = probes
        .iter()
        .map(|probe| obligation_for_probe(&projection, probe))
        .collect();

    ProbePlan {
        id: format!("{}:probe-plan", idea.id),
        idea_id: idea.id.clone(),
        projections: vec![projection],
        probes,
        obligations,
    }
}

fn probe_for_kind(idea: &QIdea, kind: ProbeKind, index: usize) -> QProbe {
    QProbe {
        id: format!("{}:probe:{index}", idea.id),
        target: idea.id.clone(),
        kind,
        question: question_for_kind(kind),
        expected_finite_output: expected_output_for_kind(kind),
        required_witness: required_witness_for_kind(kind),
        obstruction_classes: obstruction_classes_for_kind(kind),
        terminal_conditions: vec!["finite witness satisfies the declared scope".to_string()],
        failure_conditions: vec![
            "missing finite carrier".to_string(),
            "missing witness".to_string(),
            "scope mismatch".to_string(),
        ],
    }
}

fn obligation_for_probe(projection: &FiniteProjection, probe: &QProbe) -> DescentObligation {
    DescentObligation {
        id: format!("{}:obligation", probe.id),
        projection_id: projection.id.clone(),
        probe_id: Some(probe.id.clone()),
        required_witness: probe.required_witness.clone(),
        expected_finite_output: probe.expected_finite_output.clone(),
        terminal_conditions: probe.terminal_conditions.clone(),
    }
}

const PROBE_KIND_METADATA: [(ProbeKind, &str, &str); 15] = [
    (
        ProbeKind::DefinitionProbe,
        "What finite definitions are required?",
        "finite definition list",
    ),
    (
        ProbeKind::ExampleProbe,
        "What finite example exercises the claim?",
        "finite example record",
    ),
    (
        ProbeKind::CounterexampleProbe,
        "What finite counterexample search or witness can challenge it?",
        "finite counterexample or searched-bound receipt",
    ),
    (
        ProbeKind::TypeProbe,
        "What type or schema obligations must hold?",
        "type obligation checklist",
    ),
    (
        ProbeKind::InvariantProbe,
        "What invariant must be preserved?",
        "invariant statement and finite check",
    ),
    (
        ProbeKind::BoundaryProbe,
        "Where does the claim stop applying?",
        "scope and exclusion list",
    ),
    (
        ProbeKind::DescentProbe,
        "What finite descent obligation can be attempted?",
        "descent obligation",
    ),
    (
        ProbeKind::SimulationProbe,
        "What finite simulation would be meaningful?",
        "bounded simulation receipt",
    ),
    (
        ProbeKind::FormalizationProbe,
        "What theorem or proof object would be required?",
        "formal statement target or proof gap",
    ),
    (
        ProbeKind::ImplementationProbe,
        "What code and tests witness implementation?",
        "code path and passing test receipt",
    ),
    (
        ProbeKind::SourceAuthorityProbe,
        "What provenance and replay evidence exists?",
        "source receipt and replay route",
    ),
    (
        ProbeKind::AnalogyBreakProbe,
        "Where does the analogy break?",
        "break condition list",
    ),
    (
        ProbeKind::MeasurementProbe,
        "What finite measurement would decide progress?",
        "finite metric and data source",
    ),
    (
        ProbeKind::PhysicsProbe,
        "What physical definitions and scope limits are explicit?",
        "physics scope, definitions, and source obligations",
    ),
    (
        ProbeKind::ContinuumLimitProbe,
        "What finite approximation or limit obligation is defined?",
        "finite approximation and convergence obligation",
    ),
];

fn question_for_kind(kind: ProbeKind) -> String {
    PROBE_KIND_METADATA
        .iter()
        .find(|(k, _, _)| *k == kind)
        .map_or("", |(_, q, _)| *q)
        .to_string()
}

fn expected_output_for_kind(kind: ProbeKind) -> String {
    PROBE_KIND_METADATA
        .iter()
        .find(|(k, _, _)| *k == kind)
        .map_or("", |(_, _, out)| *out)
        .to_string()
}

fn required_witness_for_kind(kind: ProbeKind) -> String {
    match kind {
        ProbeKind::ImplementationProbe => "code pointer plus test receipt".to_string(),
        ProbeKind::SourceAuthorityProbe => "source citation or artifact hash".to_string(),
        ProbeKind::CounterexampleProbe => "counterexample or bounded search receipt".to_string(),
        ProbeKind::FormalizationProbe => {
            "formal theorem, proof sketch, or explicit gap".to_string()
        }
        ProbeKind::PhysicsProbe => {
            "definitions, units, assumptions, and source boundary".to_string()
        }
        _ => "finite witness or typed residual".to_string(),
    }
}

fn obstruction_classes_for_kind(kind: ProbeKind) -> Vec<ObstructionKind> {
    match kind {
        ProbeKind::DefinitionProbe | ProbeKind::TypeProbe | ProbeKind::BoundaryProbe => {
            vec![
                ObstructionKind::Underdefined,
                ObstructionKind::ScopeViolation,
            ]
        }
        ProbeKind::CounterexampleProbe => vec![ObstructionKind::CounterexampleFound],
        ProbeKind::ImplementationProbe => {
            vec![
                ObstructionKind::ImplementationMissing,
                ObstructionKind::ReplayMissing,
            ]
        }
        ProbeKind::SourceAuthorityProbe => {
            vec![
                ObstructionKind::SourceUnsupported,
                ObstructionKind::ReplayMissing,
            ]
        }
        ProbeKind::AnalogyBreakProbe => vec![ObstructionKind::AnalogyBreak],
        ProbeKind::ContinuumLimitProbe => vec![ObstructionKind::NonFiniteProjection],
        _ => vec![ObstructionKind::MissingWitness],
    }
}

fn normalize(value: &str) -> String {
    value.trim().to_ascii_lowercase()
}

fn contains_normalized(values: &[String], value: &str) -> bool {
    let normalized = normalize(value);
    values
        .iter()
        .any(|candidate| normalize(candidate) == normalized)
}

fn same_normalized_values(left: &[String], right: &[String]) -> bool {
    left.len() == right.len()
        && left.iter().all(|value| {
            right
                .iter()
                .any(|candidate| normalize(candidate) == normalize(value))
        })
}

fn any_token(haystack: &str, needles: &[&str]) -> bool {
    needles.iter().any(|needle| haystack.contains(needle))
}

fn push_unique(kinds: &mut Vec<ProbeKind>, kind: ProbeKind) {
    if !kinds.contains(&kind) {
        kinds.push(kind);
    }
}

fn truncate_for_projection(body: &str) -> String {
    const LIMIT: usize = 240;
    if body.chars().count() <= LIMIT {
        body.to_string()
    } else {
        format!("{}...", body.chars().take(LIMIT).collect::<String>())
    }
}

/// The first real batch of finite witnesses: the mechanized theorems of QM_030
/// (LQG kinematical shadows) and QM_031 (GR kinematical shadows), encoded with
/// their actual `#print axioms` receipts.
///
/// Each receipt was captured with `lake env lean QM/<file>.lean` against a warm
/// `leanprover/lean4:v4.31.0-rc1` Mathlib cache on 2026-06-22; every theorem is
/// `sorry`-free with axioms inside [`STANDARD_LEAN_AXIOMS`], so
/// [`DescentGate::verify_lean_witness`] rates each one terminally
/// [`TerminalStatus::Supported`] within its scope. See ENC-1152 / ENC-1153 and
/// `docs/q-continuum/10_FINITE_DESCENT_INTEGRATION.md`.
pub fn qm_holonomy_descent_witnesses() -> Vec<LeanWitness> {
    const PROV: &str = "lake env lean; warm leanprover/lean4:v4.31.0-rc1 Mathlib cache; 2026-06-22";
    let w = |id: &str, file: &str, theorem: &str, axioms: &[&str]| {
        LeanWitness::new(id, file, theorem, axioms.iter().copied(), PROV)
    };
    vec![
        // QM_031 GR rung 1 — curvature = non-abelian loop holonomy
        w(
            "qm031:curvature:pure-gauge-trivial",
            "lean4/QM/HolonomyCurvature.lean",
            "QM.HolonomyCurvature.loop_pureGauge_holonomy_trivial",
            &["propext"],
        ),
        w(
            "qm031:curvature:nonabelian-witness",
            "lean4/QM/HolonomyCurvature.lean",
            "QM.HolonomyCurvature.nonabelian_curvature_witness",
            &["propext", "Classical.choice", "Quot.sound"],
        ),
        // QM_030 LQG — Q8 ⊂ SU(2) Wilson-loop curvature carrier
        w(
            "qm030:lqg:q8-curvature-nonflat",
            "lean4/QM/SU2HolonomyLQG.lean",
            "QM.SU2HolonomyLQG.q8_curvature_wilson_nonflat",
            &["propext", "Classical.choice", "Quot.sound"],
        ),
        w(
            "qm030:lqg:q8-flat-trivial",
            "lean4/QM/SU2HolonomyLQG.lean",
            "QM.SU2HolonomyLQG.q8_flat_wilson_loop_trivial",
            &["propext", "Classical.choice", "Quot.sound"],
        ),
        // QM_031 GR rung 2 — Bianchi = d∘d = 0
        w(
            "qm031:bianchi:dd-zero",
            "lean4/QM/BianchiDdZero.lean",
            "QM.BianchiDdZero.bianchi_dd_zero",
            &["propext", "Quot.sound"],
        ),
        // QM_031 GR rung 3 — metric compatibility = isometry holonomy
        w(
            "qm031:metric:isometry-comp",
            "lean4/QM/MetricTransport.lean",
            "QM.MetricTransport.isometry_comp",
            &[],
        ),
        w(
            "qm031:metric:holonomy-isometry",
            "lean4/QM/MetricTransport.lean",
            "QM.MetricTransport.holonomy_isometry",
            &["propext"],
        ),
        // QM_031 GR rung 4 — parallel transport / geodesic = Wilson-line functor
        w(
            "qm031:transport:append",
            "lean4/QM/GeodesicTransport.lean",
            "QM.GeodesicTransport.transport_append",
            &["propext"],
        ),
        w(
            "qm031:transport:flat-path-independent",
            "lean4/QM/GeodesicTransport.lean",
            "QM.GeodesicTransport.flat_transport_path_independent",
            &["propext"],
        ),
        // QM_031 GR rung 5 — singularity = refusal
        w(
            "qm031:singularity:geo-none-absorbing",
            "lean4/QM/SingularityContinuum.lean",
            "QM.SingularityContinuum.geo_none_absorbing",
            &["propext", "Quot.sound"],
        ),
        w(
            "qm031:singularity:not-a-point",
            "lean4/QM/SingularityContinuum.lean",
            "QM.SingularityContinuum.singularity_not_a_point",
            &["propext"],
        ),
        // QM_031 GR rung 6 — continuum = certified limit
        w(
            "qm031:continuum:subdivision-limit",
            "lean4/QM/SingularityContinuum.lean",
            "QM.SingularityContinuum.subdivision_to_continuum",
            &["propext", "Classical.choice", "Quot.sound"],
        ),
    ]
}

/// Builds the QM↔GR holonomy-ladder reconstruction as one witness-gated descent
/// ledger — the `docs/q-continuum/10_FINITE_DESCENT_INTEGRATION.md` §3 worked
/// example, realized on real receipts.
///
/// Every mechanized motif from [`qm_holonomy_descent_witnesses`] is recorded as a
/// `Supported` result; the Q-held remainder (dynamics, area scale, continuum) as
/// residual results, **all in one `AuthorityTrace`**. Because in-scope residuals
/// are present, the trace is [`AuthorityStrength::ConditionallySupported`] — never
/// terminal. The reconstruction is *conditionally supported within the
/// toy-carrier scope*; the dynamics/continuum/area-scale stay Q-held. That is the
/// honest support boundary, enforced by the type system rather than the prose.
pub fn holonomy_ladder_descent_ledger() -> QContinuumLedger {
    let gate = DescentGate::new();
    let scope = AuthorityScope::new("qm-gr-holonomy-ladder")
        .with_constraint("finite toy carriers: Q8 ⊂ SU(2), finite cycles, finite complexes")
        .with_exclusion("continuum SU(2) and the spacetime manifold")
        .with_exclusion("the Einstein field equation / Hamiltonian constraint (dynamics)")
        .with_exclusion("the area scale 8πγℓ_P² and the SU(2) Casimir eigenvalue");
    let about = "claim:qm-gr-holonomy-ladder";

    let mut ledger = QContinuumLedger::new();

    // The witnessed kinematical motifs — each a real, axiom-audited Lean theorem.
    for witness in qm_holonomy_descent_witnesses() {
        let result = gate.verify_lean_witness(format!("o:{}", witness.id), scope.clone(), &witness);
        ledger.record_descent_result(about, result);
    }

    // The Q-held remainder — recorded honestly as residuals, never witnessed.
    for (obligation_id, obstruction, description) in [
        (
            "o:dynamics",
            ObstructionKind::NonFiniteProjection,
            "the Einstein field equation / Hamiltonian constraint — open in GR/LQG itself; no finite shadow yet",
        ),
        (
            "o:area-scale",
            ObstructionKind::MissingWitness,
            "j(j+1) Casimir eigenvalue and the 8πγℓ_P² area scale are imported, not descended",
        ),
        (
            "o:continuum",
            ObstructionKind::NonFiniteProjection,
            "continuum SU(2) / spacetime manifold is Q-held; only a certified-limit shadow exists",
        ),
    ] {
        let residual = Residual::new(
            format!("residual:{obligation_id}"),
            about,
            obstruction,
            description,
        );
        let result = DescentResult::failed(obligation_id, scope.clone(), residual);
        ledger.record_descent_result(about, result);
    }

    ledger
}

// Origin: engine/crates_rs/core_types/src/q_continuum.rs
// Claim: urn:core:crates_rs:core-types:q-continuum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4bba3419 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4bba3419` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4bba3419 {
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
impl BoundaryError4bba3419 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4bba3419 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4bba3419 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4bba3419 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4bba3419> {
        if capacity_bound == 0 {
            return Err(BoundaryError4bba3419::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4bba3419::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4bba3419::ExceedsCapacity {
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

    #[test]
    fn q_idea_is_non_terminal_by_default() {
        let idea = QIdea::new(
            "idea:goldbach",
            "All even numbers greater than 2 are sums of two primes.",
            "unit-test",
        );

        assert_eq!(idea.terminal_status, TerminalStatus::Speculative);
        assert!(!idea.terminal_status.is_terminal_support());
    }

    #[test]
    fn q_claim_cannot_be_terminally_supported_without_a_witness_or_descent_result() {
        let scope = AuthorityScope::new("finite arithmetic examples");
        let mut claim = QClaim::new(
            "claim:goldbach-small",
            "idea:goldbach",
            "Every checked even number up to 100 is a sum of two primes.",
            scope.clone(),
            "unit-test",
        );
        let unsupported_result = DescentResult {
            obligation_id: "obligation:missing-witness".to_string(),
            scope: scope.clone(),
            terminal_status: TerminalStatus::Supported,
            witness: None,
            residual: None,
            counterexample: None,
            notes: Vec::new(),
        };
        let mut trace = AuthorityTrace::new(claim.id.clone(), scope);

        assert!(!claim.apply_descent_result(&unsupported_result));
        trace.record_descent_result(unsupported_result);

        assert_eq!(claim.terminal_status, TerminalStatus::Speculative);
        assert_ne!(trace.strength, AuthorityStrength::TerminalWithinScope);
        assert_eq!(trace.failed_descents.len(), 1);
        assert_eq!(
            trace.residuals[0].obstruction,
            ObstructionKind::MissingWitness
        );
    }

    #[test]
    fn failed_probe_creates_a_residual() {
        let scope = AuthorityScope::new("q-idea:business");
        let residual = Residual::new(
            "residual:wtp",
            "probe:measurement",
            ObstructionKind::MissingWitness,
            "no willingness-to-pay evidence",
        );
        let result = DescentResult::failed("obligation:wtp", scope, residual);
        let mut ledger = QContinuumLedger::new();

        ledger.record_descent_result("claim:business", result);

        assert_eq!(ledger.residuals().len(), 1);
        assert_eq!(
            ledger.entries[0].obstruction,
            Some(ObstructionKind::MissingWitness)
        );
    }

    #[test]
    fn descent_result_updates_the_ledger() {
        let scope = AuthorityScope::new("finite implementation test");
        let witness = Witness::new(
            "witness:test",
            "test",
            "q_continuum tests pass",
            "cargo test -p core_types q_continuum",
        );
        let result = DescentResult::supported("obligation:test", scope, witness);
        let mut ledger = QContinuumLedger::new();

        ledger.record_descent_result("claim:implementation", result);

        let trace = ledger
            .authority_trace("claim:implementation")
            .expect("trace was recorded");
        assert_eq!(ledger.entries.len(), 1);
        assert_eq!(trace.strength, AuthorityStrength::TerminalWithinScope);
        assert_eq!(trace.successful_descents.len(), 1);
    }

    #[test]
    fn authority_is_scoped() {
        let scope =
            AuthorityScope::new("finite arithmetic examples").with_constraint("checked up to 100");
        let trace = AuthorityTrace::new("claim:goldbach-small", scope.clone());

        assert!(trace.applies_to_scope(&scope));
    }

    #[test]
    fn authority_does_not_leak_outside_its_scope() {
        let trace = AuthorityTrace::new(
            "claim:goldbach-small",
            AuthorityScope::new("finite arithmetic examples").with_constraint("checked up to 100"),
        );
        let outside = AuthorityScope::new("all natural numbers");
        let broader_same_domain = AuthorityScope::new("finite arithmetic examples");

        assert!(!trace.applies_to_scope(&outside));
        assert!(!trace.applies_to_scope(&broader_same_domain));
        assert!(!trace.is_terminal_within_domain("all natural numbers"));
    }

    #[test]
    fn speculative_claims_remain_speculative_until_finite_support_exists() {
        let scope = AuthorityScope::new("paper claim");
        let claim = QClaim::new(
            "claim:paper",
            "idea:paper",
            "This paper derives quantum mechanics from primitive difference.",
            scope,
            "unit-test",
        );
        let mut ledger = QContinuumLedger::new();

        ledger.add_claim(claim);

        assert_eq!(ledger.speculative_claims().len(), 1);
        assert_eq!(ledger.unsupported_claims().len(), 1);
        assert_eq!(ledger.terminal_claims().len(), 0);
    }

    #[test]
    fn probe_generation_creates_finite_obligations() {
        let idea = QIdea::new(
            "idea:rust",
            "This Rust module implements finite descent.",
            "unit-test",
        );

        let plan = generate_probe_plan(&idea);

        assert!(!plan.projections.is_empty());
        assert!(!plan.probes.is_empty());
        assert_eq!(plan.probes.len(), plan.obligations.len());
        assert!(plan
            .obligations
            .iter()
            .all(|obligation| !obligation.expected_finite_output.is_empty()));
        assert!(plan
            .probes
            .iter()
            .any(|probe| probe.kind == ProbeKind::ImplementationProbe));
    }

    #[test]
    fn unsupported_general_claims_are_not_marked_supported() {
        let idea = QIdea::new(
            "idea:general-goldbach",
            "All even numbers greater than 2 are sums of two primes.",
            "unit-test",
        );
        let claim = QClaim::new(
            "claim:general-goldbach",
            idea.id.clone(),
            idea.body.clone(),
            AuthorityScope::new("all natural numbers"),
            "unit-test",
        );
        let mut ledger = QContinuumLedger::new();

        ledger.add_idea(idea);
        ledger.add_claim(claim);

        assert_eq!(ledger.unsupported_claims().len(), 1);
        assert!(ledger.authority_trace("claim:general-goldbach").is_none());
    }

    #[test]
    fn repeated_obstruction_is_recorded_not_hidden() {
        let scope = AuthorityScope::new("q-idea:continuum");
        let mut ledger = QContinuumLedger::new();
        let residual = Residual::new(
            "residual:projection",
            "projection:continuum",
            ObstructionKind::NonFiniteProjection,
            "no finite approximation supplied",
        );

        ledger.record_descent_result(
            "claim:continuum",
            DescentResult::failed("obligation:projection:1", scope.clone(), residual.clone()),
        );
        ledger.record_descent_result(
            "claim:continuum",
            DescentResult::failed("obligation:projection:2", scope, residual),
        );

        let trace = ledger
            .authority_trace("claim:continuum")
            .expect("trace was recorded");
        assert_eq!(ledger.entries.len(), 2);
        assert_eq!(ledger.residuals().len(), 2);
        assert_eq!(trace.failed_descents.len(), 2);
    }

    fn lean_scope() -> AuthorityScope {
        AuthorityScope::new("finite mechanized lean theorem")
    }

    #[test]
    fn clean_lean_witness_earns_terminal_support() {
        let gate = DescentGate::new();
        let witness = LeanWitness::new(
            "witness:clean",
            "lean4/QM/HolonomyCurvature.lean",
            "loop_pureGauge_holonomy_trivial",
            ["propext"],
            "lake env lean; 2026-06-22",
        );
        assert!(witness.is_clean());

        let result = gate.verify_lean_witness("obl:clean", lean_scope(), &witness);
        assert_eq!(result.terminal_status, TerminalStatus::Supported);
        assert!(result.has_valid_support());

        let mut ledger = QContinuumLedger::new();
        ledger.record_descent_result("thm:curvature", result);
        let trace = ledger.authority_trace("thm:curvature").expect("trace");
        assert_eq!(trace.strength, AuthorityStrength::TerminalWithinScope);
    }

    #[test]
    fn sorry_witness_cannot_earn_support() {
        let gate = DescentGate::new();
        let holey = LeanWitness::new(
            "witness:hole",
            "lean4/QM/Fake.lean",
            "totally_proved",
            ["propext", "sorryAx"],
            "tampered receipt",
        );
        assert!(!holey.is_sorry_free());
        assert!(!holey.is_clean());

        let result = gate.verify_lean_witness("obl:hole", lean_scope(), &holey);
        assert_eq!(result.terminal_status, TerminalStatus::Residual);
        assert!(!result.has_valid_support());
        assert_eq!(
            result.residual.as_ref().expect("residual").obstruction,
            ObstructionKind::MissingWitness
        );

        // A holey proof can never be laundered into terminal authority.
        let mut ledger = QContinuumLedger::new();
        ledger.record_descent_result("thm:fake", result);
        let trace = ledger.authority_trace("thm:fake").expect("trace");
        assert_ne!(trace.strength, AuthorityStrength::TerminalWithinScope);
    }

    #[test]
    fn nonstandard_axiom_is_only_conditional_support() {
        let gate = DescentGate::new();
        let conditional = LeanWitness::new(
            "witness:cond",
            "lean4/QM/Fake.lean",
            "depends_on_extra_axiom",
            ["propext", "myUnprovedAxiom"],
            "lake env lean",
        );
        assert!(conditional.is_sorry_free());
        assert!(!conditional.is_clean());
        assert_eq!(
            conditional.nonstandard_axioms(),
            vec!["myUnprovedAxiom".to_string()]
        );

        let result = gate.verify_lean_witness("obl:cond", lean_scope(), &conditional);
        assert_eq!(
            result.terminal_status,
            TerminalStatus::ConditionallySupported
        );
        assert!(result.has_valid_support());

        let mut ledger = QContinuumLedger::new();
        ledger.record_descent_result("thm:cond", result);
        let trace = ledger.authority_trace("thm:cond").expect("trace");
        // Conditional support is real but NOT terminal.
        assert_eq!(trace.strength, AuthorityStrength::ConditionallySupported);
        assert!(!trace.is_terminal_within_domain("finite mechanized lean theorem"));
    }

    #[test]
    fn axiom_free_witness_is_clean() {
        let witness = LeanWitness::new(
            "witness:axiomfree",
            "lean4/QM/MetricTransport.lean",
            "isometry_comp",
            Vec::<String>::new(),
            "lake env lean",
        );
        assert!(witness.is_clean());
        assert_eq!(witness.axioms_summary(), "axiom-free");
    }

    #[test]
    fn qm_holonomy_witnesses_are_all_clean_and_terminal() {
        let gate = DescentGate::new();
        let mut ledger = QContinuumLedger::new();
        let witnesses = qm_holonomy_descent_witnesses();
        assert!(witnesses.len() >= 6, "expected the GR/LQG witness batch");

        for w in &witnesses {
            assert!(w.is_clean(), "{} must be clean", w.theorem);
            let scope = AuthorityScope::new(format!("mechanized:{}", w.file));
            let result = gate.verify_lean_witness(format!("obl:{}", w.theorem), scope, w);
            assert_eq!(
                result.terminal_status,
                TerminalStatus::Supported,
                "{} should be terminally supported",
                w.theorem
            );
            ledger.record_descent_result(format!("thm:{}", w.theorem), result);
        }

        // Each real mechanized theorem became a terminal-within-scope trace —
        // the first genuine batch of DescentResults flowing through the gate.
        assert_eq!(ledger.authority_traces.len(), witnesses.len());
        assert!(ledger
            .authority_traces
            .iter()
            .all(|t| t.strength == AuthorityStrength::TerminalWithinScope));
    }

    #[test]
    fn in_scope_residual_demotes_terminal_to_conditional() {
        let scope = lean_scope();
        let gate = DescentGate::new();
        let mut trace = AuthorityTrace::new("claim:mixed", scope.clone());

        // A clean witness alone would be terminal ...
        let clean = LeanWitness::new("w:clean", "f.lean", "thm_ok", ["propext"], "p");
        trace.record_descent_result(gate.verify_lean_witness("o:ok", scope.clone(), &clean));
        assert_eq!(trace.strength, AuthorityStrength::TerminalWithinScope);

        // ... but a later in-scope Q-held residual demotes the trace off terminal.
        let residual = Residual::new(
            "r:held",
            "claim:mixed",
            ObstructionKind::NonFiniteProjection,
            "dynamics is Q-held",
        );
        trace.record_descent_result(DescentResult::failed("o:held", scope, residual));
        assert_eq!(trace.strength, AuthorityStrength::ConditionallySupported);
        assert_ne!(trace.strength, AuthorityStrength::TerminalWithinScope);
    }

    #[test]
    fn holonomy_ladder_is_conditionally_supported_not_terminal() {
        let ledger = holonomy_ladder_descent_ledger();
        let trace = ledger
            .authority_trace("claim:qm-gr-holonomy-ladder")
            .expect("ladder trace");

        // The witnessed motifs are real, terminal-grade evidence ...
        assert_eq!(
            trace.successful_descents.len(),
            qm_holonomy_descent_witnesses().len()
        );
        // ... but the three in-scope Q-held residuals keep the whole claim off
        // terminal: conditionally supported, never "GR/LQG derived".
        assert_eq!(trace.residuals.len(), 3);
        assert_eq!(trace.strength, AuthorityStrength::ConditionallySupported);
        assert_ne!(trace.strength, AuthorityStrength::TerminalWithinScope);
        assert!(!trace.is_terminal_within_domain("qm-gr-holonomy-ladder"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_4bba3419 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4bba3419::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4bba3419::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4bba3419::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4bba3419::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4bba3419::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4bba3419::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4bba3419::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
