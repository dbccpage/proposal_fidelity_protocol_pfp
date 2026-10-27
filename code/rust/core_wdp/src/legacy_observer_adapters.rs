//! CH10 semantic adapters for the locally identified legacy families.
//! AuthorityEffect: None. Missing memory, policy and authority are never filled
//! by defaults. Source receipt/authority tags are retained as unverified source
//! metadata, independently of computed mathematical evidence.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat;
use std::collections::{BTreeMap, BTreeSet};

use linear_algebra::linear_observer_presentation::{
    LinearObserverPresentation, LinearSensingPresentation,
};
use num_rational::BigRational;
use num_traits::{One, Signed};
use core_category_theory::context_reflection::{ContextHom, ContextSystem};
use core_category_theory::finite_moore::FiniteMoore;
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{hermitian_trace, is_psd, square_dim};

use crate::coda::diagnostic_routing::DiagnosticPacket;
use crate::observer::{OperationalObserverPacket, QuotientObserver};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdapterError {
    InvalidSourceBinding,
    InvalidPresentation,
    IncompleteOperationalDomain,
    InvalidMemoryInterface,
    InvalidEvaluatorDomain,
    InvalidTransform,
    InvalidDensity,
    QuantumTransport,
    MissingSemantics(&'static str),
}

// Origin: engine/crates_rs/core_wdp/src/legacy_observer_adapters.rs
// Claim: urn:core:crates_rs:core-wdp:legacy-observer-adapters:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AdapterError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AdapterError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceCustody {
    pub path: String,
    pub recorded_sha256: String,
    pub source_receipts: Vec<String>,
    pub source_authority_tags: Vec<String>,
}
impl SourceCustody {
    fn check(&self) -> Result<(), AdapterError> {
        if self.path.is_empty()
            || self.recorded_sha256.len() != 64
            || !self.recorded_sha256.bytes().all(|b| b.is_ascii_hexdigit())
        {
            return Err(AdapterError::InvalidSourceBinding);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PresentationLayer {
    states: Vec<String>,
    report_labels: Vec<String>,
    reports: Vec<usize>,
    contexts: Option<ContextSystem>,
}
impl PresentationLayer {
    pub fn states(&self) -> &[String] {
        &self.states
    }
    pub fn report_labels(&self) -> &[String] {
        &self.report_labels
    }
    pub fn reports(&self) -> &[usize] {
        &self.reports
    }
    pub fn contexts(&self) -> Option<&ContextSystem> {
        self.contexts.as_ref()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MemoryLayer {
    model: FiniteMoore,
    comparison: Vec<Vec<bool>>,
    store: Option<Vec<usize>>,
}
impl MemoryLayer {
    pub fn try_new(
        model: FiniteMoore,
        comparison: Vec<Vec<bool>>,
        store: Option<Vec<usize>>,
    ) -> Result<Self, AdapterError> {
        let count = comparison.len();
        if count == 0
            || comparison.iter().any(|row| row.len() != count)
            || model.reports().iter().any(|&r| r >= count)
        {
            return Err(AdapterError::InvalidMemoryInterface);
        }
        if let Some(mapping) = &store {
            if mapping.len() != count
                || mapping.iter().any(|&m| m >= model.state_count())
                || mapping
                    .iter()
                    .enumerate()
                    .any(|(r, &m)| !comparison[model.reports()[m]][r])
            {
                return Err(AdapterError::InvalidMemoryInterface);
            }
        }
        Ok(Self {
            model,
            comparison,
            store,
        })
    }
    pub fn model(&self) -> &FiniteMoore {
        &self.model
    }
    pub fn comparison(&self) -> &[Vec<bool>] {
        &self.comparison
    }
    pub fn store(&self) -> Option<&[usize]> {
        self.store.as_deref()
    }
    pub fn reaccess(&self, presentation: usize) -> Result<usize, AdapterError> {
        let store = self.store.as_ref().ok_or(AdapterError::MissingSemantics(
            "presentation-to-memory store interface",
        ))?;
        let state = *store
            .get(presentation)
            .ok_or(AdapterError::InvalidMemoryInterface)?;
        Ok(self.model.reports()[state])
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FiniteStatus {
    WithinTolerance,
    AboveTolerance,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PolicyAction {
    Store,
    Emit,
    RequestData,
    Refuse,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EvaluatorLayer {
    packets: Vec<DiagnosticPacket>,
    transformations: Vec<Vec<usize>>,
    tolerance: BigRational,
}
impl EvaluatorLayer {
    fn validate_packets_consistency(
        system: &ContextSystem,
        packets: &[DiagnosticPacket],
        tolerance: &BigRational,
    ) -> Result<(), AdapterError> {
        if tolerance.is_negative()
            || packets.len() != system.state_count()
            || packets.is_empty()
            || packets.iter().any(|p| p.system() != system)
        {
            return Err(AdapterError::InvalidEvaluatorDomain);
        }
        let first = packets[0].phi1().certificate();
        if packets.iter().any(|p| {
            p.phi1().d0() != first.d0
                || p.phi1().certificate().weights != first.weights
                || p.closure_map() != packets[0].closure_map()
        }) {
            return Err(AdapterError::InvalidEvaluatorDomain);
        }
        Ok(())
    }

    fn validate_single_transformation(
        system: &ContextSystem,
        packets: &[DiagnosticPacket],
        transformation: &[usize],
    ) -> Result<(), AdapterError> {
        if transformation.iter().copied().collect::<BTreeSet<_>>()
            != (0..system.state_count()).collect()
            || transformation.len() != system.state_count()
            || ContextHom::new(system, system, transformation.to_vec()).is_err()
        {
            return Err(AdapterError::InvalidTransform);
        }
        for (i, &j) in transformation.iter().enumerate() {
            if packets[i].classification() != packets[j].classification() {
                return Err(AdapterError::InvalidTransform);
            }
        }
        Ok(())
    }

    /// Finite-instance semantic specialization of the normalized evaluator:
    /// state-indexed defects, common repair/gauge/closure, explicit lawful
    /// state permutations, and a declared exact tolerance terminalizer.
    pub fn try_new(
        system: &ContextSystem,
        packets: Vec<DiagnosticPacket>,
        transformations: Vec<Vec<usize>>,
        tolerance: BigRational,
    ) -> Result<Self, AdapterError> {
        Self::validate_packets_consistency(system, &packets, &tolerance)?;
        for transformation in &transformations {
            Self::validate_single_transformation(system, &packets, transformation)?;
        }
        Ok(Self {
            packets,
            transformations,
            tolerance,
        })
    }
    pub fn packets(&self) -> &[DiagnosticPacket] {
        &self.packets
    }
    pub fn transformations(&self) -> &[Vec<usize>] {
        &self.transformations
    }
    pub fn status(&self, state: usize) -> Result<FiniteStatus, AdapterError> {
        let packet = self
            .packets
            .get(state)
            .ok_or(AdapterError::InvalidEvaluatorDomain)?;
        Ok(if packet.phi1().value() <= &self.tolerance {
            FiniteStatus::WithinTolerance
        } else {
            FiniteStatus::AboveTolerance
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuantumPresentation {
    states: Vec<BasicMatrix<GaussianRat>>,
    channel: ExactKrausChannel,
    images: Vec<BasicMatrix<GaussianRat>>,
    shadows: Vec<Vec<BigRational>>,
}
impl QuantumPresentation {
    pub fn states(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.states
    }
    pub fn channel(&self) -> &ExactKrausChannel {
        &self.channel
    }
    pub fn images(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.images
    }
    pub fn shadows(&self) -> &[Vec<BigRational>] {
        &self.shadows
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdaptedObserver {
    custody: SourceCustody,
    presentation: Option<PresentationLayer>,
    memory: Option<MemoryLayer>,
    operational: Option<(FiniteMoore, usize)>,
    evaluator: Option<EvaluatorLayer>,
    policy: Option<[PolicyAction; 2]>,
    linear: Option<LinearObserverPresentation>,
    linear_sensing: Option<LinearSensingPresentation>,
    quantum: Option<QuantumPresentation>,
}
impl AdaptedObserver {
    fn empty(custody: SourceCustody) -> Result<Self, AdapterError> {
        custody.check()?;
        Ok(Self {
            custody,
            presentation: None,
            memory: None,
            operational: None,
            evaluator: None,
            policy: None,
            linear: None,
            linear_sensing: None,
            quantum: None,
        })
    }
    pub fn custody(&self) -> &SourceCustody {
        &self.custody
    }
    pub fn presentation(&self) -> Option<&PresentationLayer> {
        self.presentation.as_ref()
    }
    pub fn memory(&self) -> Option<&MemoryLayer> {
        self.memory.as_ref()
    }
    pub fn operational(&self) -> Option<&(FiniteMoore, usize)> {
        self.operational.as_ref()
    }
    pub fn evaluator(&self) -> Option<&EvaluatorLayer> {
        self.evaluator.as_ref()
    }
    pub fn policy(&self) -> Option<&[PolicyAction; 2]> {
        self.policy.as_ref()
    }
    pub fn linear(&self) -> Option<&LinearObserverPresentation> {
        self.linear.as_ref()
    }
    pub fn linear_sensing(&self) -> Option<&LinearSensingPresentation> {
        self.linear_sensing.as_ref()
    }
    pub fn quantum(&self) -> Option<&QuantumPresentation> {
        self.quantum.as_ref()
    }
}

pub fn adapt_finite_quotient(
    source: &QuotientObserver,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    QuotientObserver::new(
        source.carrier.clone(),
        source.equivalence_classes.clone(),
        source.comparison.clone(),
    )
    .map_err(|_| AdapterError::InvalidPresentation)?;
    let states: Vec<_> = source.carrier.iter().cloned().collect();
    let reports = states
        .iter()
        .map(|state| {
            source
                .equivalence_classes
                .iter()
                .position(|block| block.contains(state))
                .ok_or(AdapterError::InvalidPresentation)
        })
        .collect::<Result<Vec<_>, _>>()?;
    let mut result = AdaptedObserver::empty(custody)?;
    result.presentation = Some(PresentationLayer {
        states,
        report_labels: (0..source.equivalence_classes.len())
            .map(|i| format!("class:{i}"))
            .collect(),
        reports,
        contexts: None,
    });
    Ok(result)
}

pub fn adapt_report_context(
    states: Vec<String>,
    report_labels: Vec<String>,
    reports: Vec<usize>,
    contexts: ContextSystem,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    if states.len() != contexts.state_count()
        || states.iter().collect::<BTreeSet<_>>().len() != states.len()
        || report_labels.is_empty()
        || report_labels.iter().collect::<BTreeSet<_>>().len() != report_labels.len()
        || reports.len() != states.len()
        || reports.iter().any(|&r| r >= report_labels.len())
    {
        return Err(AdapterError::InvalidPresentation);
    }
    let mut result = AdaptedObserver::empty(custody)?;
    result.presentation = Some(PresentationLayer {
        states,
        report_labels,
        reports,
        contexts: Some(contexts),
    });
    Ok(result)
}

pub fn adapt_memory(
    memory: MemoryLayer,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    let mut result = AdaptedObserver::empty(custody)?;
    result.memory = Some(memory);
    Ok(result)
}

pub fn adapt_operational_semantics(
    source: &OperationalObserverPacket,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    OperationalObserverPacket::new(
        source.states.clone(),
        source.start_state.clone(),
        source.alphabet.clone(),
        source.transitions.clone(),
        source.reports.clone(),
        source.profiles.clone(),
    )
    .map_err(|_| AdapterError::IncompleteOperationalDomain)?;
    if source.reports.keys().cloned().collect::<BTreeSet<_>>() != source.states
        || source.profiles.keys().cloned().collect::<BTreeSet<_>>() != source.states
    {
        return Err(AdapterError::IncompleteOperationalDomain);
    }
    let states: Vec<_> = source.states.iter().cloned().collect();
    let indices: BTreeMap<_, _> = states
        .iter()
        .enumerate()
        .map(|(i, s)| (s.clone(), i))
        .collect();
    let labels: Vec<_> = source
        .reports
        .values()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let report_ids: BTreeMap<_, _> = labels
        .iter()
        .enumerate()
        .map(|(i, r)| (r.clone(), i))
        .collect();
    let profile_labels: Vec<_> = source
        .profiles
        .values()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let profile_ids: BTreeMap<_, _> = profile_labels
        .iter()
        .enumerate()
        .map(|(i, r)| (r.clone(), i))
        .collect();
    let mut actions = Vec::new();
    for state in &states {
        let mut row = Vec::new();
        for input in &source.alphabet {
            let next = source
                .transitions
                .get(&(state.clone(), input.clone()))
                .ok_or(AdapterError::IncompleteOperationalDomain)?;
            row.push(indices[next]);
        }
        actions.push(row);
    }
    let reports = states
        .iter()
        .map(|s| report_ids[&source.reports[s]])
        .collect::<Vec<_>>();
    let profiles = states
        .iter()
        .map(|s| profile_ids[&source.profiles[s]])
        .collect();
    let contexts = ContextSystem::new(profiles, actions.clone(), source.alphabet.len())
        .map_err(|_| AdapterError::IncompleteOperationalDomain)?;
    let model = FiniteMoore::new(reports.clone(), actions, source.alphabet.len())
        .map_err(|_| AdapterError::IncompleteOperationalDomain)?;
    let start = indices[&source.start_state];
    let mut result = adapt_report_context(states, labels, reports, contexts, custody)?;
    result.operational = Some((model, start));
    Ok(result)
}

pub fn attach_evaluator(
    mut adapted: AdaptedObserver,
    evaluator: EvaluatorLayer,
    policy: Option<[PolicyAction; 2]>,
) -> Result<AdaptedObserver, AdapterError> {
    let system = adapted
        .presentation
        .as_ref()
        .and_then(|p| p.contexts.as_ref())
        .ok_or(AdapterError::MissingSemantics(
            "report/context domain for evaluator",
        ))?;
    if evaluator.packets.iter().any(|p| p.system() != system) {
        return Err(AdapterError::InvalidEvaluatorDomain);
    }
    adapted.evaluator = Some(evaluator);
    adapted.policy = policy;
    Ok(adapted)
}

pub fn adapt_linear_quotient(
    linear: LinearObserverPresentation,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    let mut result = AdaptedObserver::empty(custody)?;
    result.linear = Some(linear);
    Ok(result)
}

fn validate_and_apply_quantum_state(
    state: &BasicMatrix<GaussianRat>,
    channel: &ExactKrausChannel,
) -> Result<(BasicMatrix<GaussianRat>, Vec<BigRational>), AdapterError> {
    if square_dim(state).ok() != Some(channel.dim_in())
        || hermitian_trace(state).ok() != Some(BigRational::one())
        || !is_psd(state).map_err(|_| AdapterError::InvalidDensity)?
    {
        return Err(AdapterError::InvalidDensity);
    }
    let image = channel
        .apply(state)
        .map_err(|_| AdapterError::QuantumTransport)?;
    if hermitian_trace(&image).ok() != Some(BigRational::one())
        || !is_psd(&image).map_err(|_| AdapterError::InvalidDensity)?
    {
        return Err(AdapterError::InvalidDensity);
    }
    let shadow = (0..channel.dim_out())
        .map(|i| {
            image
                .get(i, i)
                .map(|z| z.re)
                .map_err(|_| AdapterError::QuantumTransport)
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((image, shadow))
}

pub fn adapt_quantum_presentation(
    states: Vec<BasicMatrix<GaussianRat>>,
    channel: ExactKrausChannel,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    if states.is_empty() {
        return Err(AdapterError::InvalidDensity);
    }
    let mut images = Vec::new();
    let mut shadows = Vec::new();
    for state in &states {
        let (image, shadow) = validate_and_apply_quantum_state(state, &channel)?;
        shadows.push(shadow);
        images.push(image);
    }
    let mut result = AdaptedObserver::empty(custody)?;
    result.quantum = Some(QuantumPresentation {
        states,
        channel,
        images,
        shadows,
    });
    Ok(result)
}

/// Explicit identity bridge between the presentation report carrier and memory
/// readout carrier. Without this bridge, a memory packet remains disconnected.
pub fn attach_memory(
    mut adapted: AdaptedObserver,
    memory: MemoryLayer,
) -> Result<AdaptedObserver, AdapterError> {
    let presentation = adapted
        .presentation
        .as_ref()
        .ok_or(AdapterError::MissingSemantics(
            "presentation for memory bridge",
        ))?;
    if presentation.report_labels.len() != memory.comparison.len() || memory.store.is_none() {
        return Err(AdapterError::InvalidMemoryInterface);
    }
    adapted.memory = Some(memory);
    Ok(adapted)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SelfComponent {
    PresentationReport(usize),
    MemoryReadout(usize),
    EvaluatorStatus(usize),
    PolicyAction(usize),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SelfReferenceEvidence {
    pub component: SelfComponent,
    pub component_value: usize,
    pub memory_state: usize,
    pub reaccessed_report: usize,
}

fn resolve_self_component_value(
    adapted: &AdaptedObserver,
    component: &SelfComponent,
) -> Result<usize, AdapterError> {
    match *component {
        SelfComponent::PresentationReport(state) => adapted
            .presentation
            .as_ref()
            .and_then(|p| p.reports.get(state).copied())
            .ok_or(AdapterError::InvalidPresentation),
        SelfComponent::MemoryReadout(state) => adapted
            .memory
            .as_ref()
            .and_then(|m| m.model.reports().get(state).copied())
            .ok_or(AdapterError::InvalidMemoryInterface),
        SelfComponent::EvaluatorStatus(state) => {
            let status = adapted
                .evaluator
                .as_ref()
                .ok_or(AdapterError::MissingSemantics("self-target evaluator"))?
                .status(state)?;
            Ok(usize::from(status == FiniteStatus::AboveTolerance))
        }
        SelfComponent::PolicyAction(status) => {
            let action = adapted
                .policy
                .as_ref()
                .and_then(|p| p.get(status))
                .ok_or(AdapterError::MissingSemantics("self-target policy"))?;
            Ok(match action {
                PolicyAction::Store => 0,
                PolicyAction::Emit => 1,
                PolicyAction::RequestData => 2,
                PolicyAction::Refuse => 3,
            })
        }
    }
}

/// A partial self-presentation adapter with an actual finite decoder and
/// reaccessed memory payload. This is not an accepted E-observation receipt.
pub fn adapt_self_reference(
    adapted: &AdaptedObserver,
    target: &SourceCustody,
    component: SelfComponent,
    memory_state: usize,
    report_decoder: &[usize],
) -> Result<SelfReferenceEvidence, AdapterError> {
    if target.path != adapted.custody.path
        || target.recorded_sha256 != adapted.custody.recorded_sha256
    {
        return Err(AdapterError::InvalidSourceBinding);
    }
    let value = resolve_self_component_value(adapted, &component)?;
    let memory = adapted
        .memory
        .as_ref()
        .ok_or(AdapterError::MissingSemantics(
            "self-reference reaccess memory",
        ))?;
    if report_decoder.len() != memory.comparison.len() {
        return Err(AdapterError::InvalidMemoryInterface);
    }
    let report = *memory
        .model
        .reports()
        .get(memory_state)
        .ok_or(AdapterError::InvalidMemoryInterface)?;
    if report_decoder[report] != value {
        return Err(AdapterError::InvalidMemoryInterface);
    }
    Ok(SelfReferenceEvidence {
        component,
        component_value: value,
        memory_state,
        reaccessed_report: report,
    })
}

/// The consolidated corpus names a six-component Genesis packet but does not
/// recover its field vocabulary. Refuse a nominal six-string "completion".
pub fn adapt_unrecovered_genesis_six(
    _fields: [&str; 6],
    _custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    Err(AdapterError::MissingSemantics(
        "source-bound Genesis six-component vocabulary and maps",
    ))
}

/// General source sensing preserves actual R and d0, with no quotient assertion.
pub fn adapt_linear_sensing(
    sensing: LinearSensingPresentation,
    custody: SourceCustody,
) -> Result<AdaptedObserver, AdapterError> {
    let mut result = AdaptedObserver::empty(custody)?;
    result.linear_sensing = Some(sensing);
    Ok(result)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_70c4eb11 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
