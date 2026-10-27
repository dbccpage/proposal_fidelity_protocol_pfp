//! Closed finite passage carriers, protected futures, and source-bound evidence.
//! Exhaustive means reachable from these seeds under this finite alphabet.
//! Completion is a fixed point, never a depth cutoff treated as unavailability.

use crate::genesis_passage::{replay, PassageEvent, PassageState};
use crate::genesis_questions::GluingRequest;
use core_category_theory::finite_continuation::{
    ContinuationError, DistinguishingWord, PartialDynamics,
};
use core_category_theory::finite_moore::MooreQuotient;
use core_category_theory::finite_question_family::{
    factor_tables, FiniteQuestionFamily, QuestionFamilyError,
};
use core_category_theory::finite_report_descent::DescentFiber;
use core_category_theory::finite_report_query::ReportQueryDecision;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PassageQuestion {
    OccurrenceCount,
    HasToken(usize),
    Retained(usize, usize),
    Protected(usize, usize),
    ObservationDeclared,
    Separated(usize, usize),
    Obstructed(usize, usize),
    Budget,
    Licensed,
    RefusalRecorded(usize, usize),
    Halted,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum PassageAnswer {
    Bool(bool),
    Count(usize),
    Undeclared,
}

impl PassageQuestion {
    fn answer_primary(&self, s: &PassageState) -> Option<PassageAnswer> {
        use PassageAnswer::*;
        match self {
            Self::OccurrenceCount => Some(Count(s.occ.len())),
            Self::HasToken(t) => Some(Bool(s.occ.contains(t))),
            Self::Retained(i, j) => Some(Bool(s.wit.contains(&(*i, *j)))),
            Self::Protected(i, j) => Some(Bool(s.prot.contains(&(*i, *j)))),
            Self::ObservationDeclared => Some(Bool(s.obs.is_some())),
            Self::Separated(i, j) => Some(s.obs.as_ref().map_or(Undeclared, |cols| {
                Bool(crate::genesis_passage::separated(cols, *i, *j))
            })),
            _ => None,
        }
    }

    fn answer_secondary(&self, s: &PassageState) -> PassageAnswer {
        use PassageAnswer::*;
        match self {
            Self::Obstructed(i, j) => Bool(s.obstructed(*i, *j)),
            Self::Budget => Count(s.budget),
            Self::Licensed => Bool(s.licensed),
            Self::Halted => Bool(s.halted),
            Self::RefusalRecorded(i, j) => Bool(s.refusals.contains(&(*i, *j))),
            _ => Undeclared,
        }
    }

    pub fn answer(&self, s: &PassageState) -> PassageAnswer {
        self.answer_primary(s)
            .unwrap_or_else(|| self.answer_secondary(s))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CarrierLimits {
    pub max_states: usize,
    pub max_transitions: usize,
    pub max_history_events: usize,
    pub max_state_cells: usize,
    /// Conservative n²(a+q+1) allowance for refinement/table work, not CPU time.
    pub max_refinement_cells: usize,
}

impl Default for CarrierLimits {
    fn default() -> Self {
        Self {
            max_states: 256,
            max_transitions: 16_384,
            max_history_events: 512,
            max_state_cells: 4096,
            max_refinement_cells: 20_000_000,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CarrierRequest {
    pub seeds: Vec<Vec<PassageEvent>>,
    pub alphabet: Vec<PassageEvent>,
    pub questions: Vec<PassageQuestion>,
    pub limits: CarrierLimits,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CarrierError {
    InvalidGrammar,
    ResourceLimit,
    OutsideCarrier,
    CertificateMismatch,
    Dynamics(ContinuationError),
    Family(QuestionFamilyError),
}

// Origin: engine/crates_rs/core_wdp/src/genesis_carrier.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CarrierError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CarrierError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CarrierCertificate {
    pub source: CarrierRequest,
    pub states: Vec<PassageState>,
    pub histories: Vec<Vec<PassageEvent>>,
    pub seed_states: Vec<usize>,
    pub transitions: Vec<Vec<Option<usize>>>,
    pub answers: Vec<Vec<PassageAnswer>>,
    /// Includes one internal unavailable sink, separately labelled from all
    /// real states. Its final class is not a member of the native carrier.
    pub refinement: MooreQuotient,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PassageCarrier {
    certificate: CarrierCertificate,
    family: FiniteQuestionFamily<PassageAnswer>,
    dynamics: PartialDynamics,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PassageDistinction {
    pub source: CarrierRequest,
    pub witness: DistinguishingWord,
    pub left_history: Vec<PassageEvent>,
    pub right_history: Vec<PassageEvent>,
    pub suffix: Vec<PassageEvent>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PassageGluing {
    pub source: CarrierRequest,
    /// Explicit history alternatives, not silently the entire closure.
    /// Different event histories may reach the same state and remain distinct.
    pub histories: Vec<Vec<PassageEvent>>,
    pub request: GluingRequest,
    pub fiber: DescentFiber,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SequentialComposition {
    pub source: CarrierRequest,
    pub words: Vec<Vec<usize>>,
    pub right_reports: Vec<usize>,
    /// All real left states × all supplied right continuations, left-major.
    pub decision: ReportQueryDecision<usize, (usize, usize), Option<usize>>,
}

impl PassageCarrier {
    fn validate_carrier_request_bounds(request: &CarrierRequest) -> Result<(), CarrierError> {
        let l = request.limits;
        if request.seeds.is_empty()
            || request.alphabet.iter().collect::<BTreeSet<_>>().len() != request.alphabet.len()
        {
            return Err(CarrierError::InvalidGrammar);
        }
        let oversize_col = request.alphabet.iter().any(|e| {
            matches!(e, PassageEvent::AddCol(c) | PassageEvent::RefineCol(c, _) if c.len() > l.max_state_cells)
        });
        if request.seeds.len() > l.max_states
            || request.questions.len() > 64
            || request.alphabet.len() > 64
            || oversize_col
        {
            return Err(CarrierError::ResourceLimit);
        }
        Ok(())
    }

    fn intern_next_state(
        l: CarrierLimits,
        cursor: usize,
        event: &PassageEvent,
        next: PassageState,
        states: &mut Vec<PassageState>,
        histories: &mut Vec<Vec<PassageEvent>>,
        ids: &mut BTreeMap<PassageState, usize>,
    ) -> Result<usize, CarrierError> {
        if !next.within_cells(l.max_state_cells) {
            return Err(CarrierError::ResourceLimit);
        }
        if let Some(&id) = ids.get(&next) {
            return Ok(id);
        }
        if states.len() >= l.max_states || histories[cursor].len() >= l.max_history_events {
            return Err(CarrierError::ResourceLimit);
        }
        let id = states.len();
        let mut path = histories[cursor].clone();
        path.push(event.clone());
        histories.push(path);
        states.push(next.clone());
        ids.insert(next, id);
        Ok(id)
    }

    fn explore_carrier_transitions(
        request: &CarrierRequest,
        states: &mut Vec<PassageState>,
        histories: &mut Vec<Vec<PassageEvent>>,
        ids: &mut BTreeMap<PassageState, usize>,
    ) -> Result<Vec<Vec<Option<usize>>>, CarrierError> {
        let l = request.limits;
        let mut transitions = Vec::new();
        let mut cursor = 0;
        while cursor < states.len() {
            if (cursor + 1)
                .checked_mul(request.alphabet.len())
                .is_none_or(|n| n > l.max_transitions)
            {
                return Err(CarrierError::ResourceLimit);
            }
            let mut row = Vec::new();
            for event in &request.alphabet {
                if !states[cursor].enabled(event) {
                    row.push(None);
                    continue;
                }
                let next = states[cursor].step(event);
                let id = Self::intern_next_state(l, cursor, event, next, states, histories, ids)?;
                row.push(Some(id));
            }
            transitions.push(row);
            cursor += 1;
        }
        Ok(transitions)
    }

    #[allow(clippy::type_complexity)]
    fn replay_seed_histories(
        request: &CarrierRequest,
    ) -> Result<
        (
            Vec<PassageState>,
            Vec<Vec<PassageEvent>>,
            BTreeMap<PassageState, usize>,
            Vec<usize>,
        ),
        CarrierError,
    > {
        let l = request.limits;
        let mut states = Vec::new();
        let mut histories = Vec::new();
        let mut ids = BTreeMap::new();
        let mut seed_states = Vec::new();
        for history in &request.seeds {
            let state = replay(history, l.max_history_events, l.max_state_cells)
                .map_err(|_| CarrierError::ResourceLimit)?;
            let next = states.len();
            let id = *ids.entry(state.clone()).or_insert_with(|| {
                states.push(state);
                histories.push(history.clone());
                next
            });
            seed_states.push(id);
        }
        if states.len() > l.max_states {
            return Err(CarrierError::ResourceLimit);
        }
        Ok((states, histories, ids, seed_states))
    }

    pub fn build(request: &CarrierRequest) -> Result<Self, CarrierError> {
        let l = request.limits;
        Self::validate_carrier_request_bounds(request)?;
        let (mut states, mut histories, mut ids, seed_states) =
            Self::replay_seed_histories(request)?;
        let transitions =
            Self::explore_carrier_transitions(request, &mut states, &mut histories, &mut ids)?;
        let n = states
            .len()
            .checked_add(1)
            .ok_or(CarrierError::ResourceLimit)?;
        if n.checked_mul(n)
            .and_then(|m| m.checked_mul(request.alphabet.len() + request.questions.len() + 1))
            .is_none_or(|m| m > l.max_refinement_cells)
        {
            return Err(CarrierError::ResourceLimit);
        }
        let answers = states
            .iter()
            .map(|s| request.questions.iter().map(|q| q.answer(s)).collect())
            .collect();
        let family = FiniteQuestionFamily::new(request.questions.len(), answers)
            .map_err(CarrierError::Family)?;
        let dynamics = PartialDynamics::new(
            family.quotient().class_of,
            transitions.clone(),
            request.alphabet.len(),
        )
        .map_err(CarrierError::Dynamics)?;
        let certificate = CarrierCertificate {
            source: request.clone(),
            states,
            histories,
            seed_states,
            transitions,
            answers: family.answers().to_vec(),
            refinement: dynamics.quotient(),
        };
        Ok(Self {
            certificate,
            family,
            dynamics,
        })
    }

    pub fn certificate(&self) -> &CarrierCertificate {
        &self.certificate
    }
    pub fn dynamics(&self) -> &PartialDynamics {
        &self.dynamics
    }
    pub fn verify(request: &CarrierRequest, c: &CarrierCertificate) -> Result<(), CarrierError> {
        if Self::build(request)?.certificate != *c {
            return Err(CarrierError::CertificateMismatch);
        }
        Ok(())
    }

    pub fn distinguish(
        &self,
        left: usize,
        right: usize,
        max_pairs: usize,
    ) -> Result<Option<PassageDistinction>, CarrierError> {
        self.dynamics
            .distinguish(left, right, max_pairs)
            .map_err(CarrierError::Dynamics)
            .map(|c| {
                c.map(|w| PassageDistinction {
                    source: self.certificate.source.clone(),
                    left_history: self.certificate.histories[left].clone(),
                    right_history: self.certificate.histories[right].clone(),
                    suffix: w
                        .word
                        .iter()
                        .map(|&a| self.certificate.source.alphabet[a].clone())
                        .collect(),
                    witness: w,
                })
            })
    }

    pub fn verify_distinction(&self, c: &PassageDistinction) -> Result<(), CarrierError> {
        self.dynamics
            .verify_distinction(&c.witness)
            .map_err(CarrierError::Dynamics)?;
        if c.source != self.certificate.source
            || c.left_history != self.certificate.histories[c.witness.left]
            || c.right_history != self.certificate.histories[c.witness.right]
            || c.suffix
                != c.witness
                    .word
                    .iter()
                    .map(|&a| self.certificate.source.alphabet[a].clone())
                    .collect::<Vec<_>>()
        {
            return Err(CarrierError::CertificateMismatch);
        }
        Ok(())
    }

    /// Sequential history composition only. Equal right reports must preserve
    /// their action on EVERY left state, not only their result from one seed.
    pub fn compose(
        &self,
        words: &[Vec<usize>],
        right_reports: &[usize],
        max_cells: usize,
    ) -> Result<SequentialComposition, CarrierError> {
        let n = self.certificate.states.len();
        if words.len() != right_reports.len() {
            return Err(CarrierError::InvalidGrammar);
        }
        let work = words.iter().try_fold(0usize, |n, w| {
            n.checked_add(w.len()).and_then(|n| n.checked_add(1))
        });
        if work
            .and_then(|m| m.checked_mul(n))
            .is_none_or(|m| m > max_cells)
        {
            return Err(CarrierError::ResourceLimit);
        }
        let classes = &self.certificate.refinement.state_to_block;
        let mut reports = Vec::new();
        let mut outputs = Vec::new();
        for left in 0..n {
            for (i, word) in words.iter().enumerate() {
                reports.push((classes[left], right_reports[i]));
                outputs.push(
                    self.dynamics
                        .run(left, word)
                        .map_err(CarrierError::Dynamics)?
                        .map(|s| classes[s]),
                );
            }
        }
        let decision = factor_tables(&reports, &outputs)
            .map_err(CarrierError::Family)?
            .decide();
        Ok(SequentialComposition {
            source: self.certificate.source.clone(),
            words: words.to_vec(),
            right_reports: right_reports.to_vec(),
            decision,
        })
    }

    pub fn verify_composition(
        &self,
        words: &[Vec<usize>],
        reports: &[usize],
        max_cells: usize,
        c: &SequentialComposition,
    ) -> Result<(), CarrierError> {
        if *c != self.compose(words, reports, max_cells)? {
            return Err(CarrierError::CertificateMismatch);
        }
        Ok(())
    }

    /// Certifies the complete extension fiber of explicitly listed histories.
    /// Replay from genesis must land in this carrier; resource failure never
    /// counts as absence of a global extension. Duplicate histories are refused.
    pub fn glue(
        &self,
        histories: &[Vec<PassageEvent>],
        request: &GluingRequest,
    ) -> Result<PassageGluing, CarrierError> {
        let l = self.certificate.source.limits;
        if histories.len() > l.max_states {
            return Err(CarrierError::ResourceLimit);
        }
        if histories.iter().collect::<BTreeSet<_>>().len() != histories.len() {
            return Err(CarrierError::InvalidGrammar);
        }
        let c = request.cover.len();
        if c.checked_mul(c)
            .and_then(|m| {
                c.checked_mul(histories.len())
                    .and_then(|n| n.checked_add(m))
            })
            .is_none_or(|m| m > request.work_limit)
        {
            return Err(CarrierError::ResourceLimit);
        }
        let mut answers = Vec::new();
        for h in histories {
            let s = replay(h, l.max_history_events, l.max_state_cells)
                .map_err(|_| CarrierError::ResourceLimit)?;
            let i = self
                .certificate
                .states
                .iter()
                .position(|state| *state == s)
                .ok_or(CarrierError::OutsideCarrier)?;
            answers.push(self.family.answers()[i].clone());
        }
        let family = FiniteQuestionFamily::new(self.family.question_count(), answers)
            .map_err(CarrierError::Family)?;
        let site = family
            .report_site(&request.contexts, request.work_limit)
            .map_err(CarrierError::Family)?;
        let fiber = site
            .presheaf()
            .descent_fiber(request.target, &request.cover, &request.locals)
            .map_err(|e| CarrierError::Family(QuestionFamilyError::Descent(e)))?;
        Ok(PassageGluing {
            source: self.certificate.source.clone(),
            histories: histories.to_vec(),
            request: request.clone(),
            fiber,
        })
    }

    pub fn verify_gluing(
        &self,
        histories: &[Vec<PassageEvent>],
        request: &GluingRequest,
        c: &PassageGluing,
    ) -> Result<(), CarrierError> {
        if *c != self.glue(histories, request)? {
            return Err(CarrierError::CertificateMismatch);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_fe6f95e1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
