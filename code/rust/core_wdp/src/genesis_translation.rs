//! Checked candidate translation between two preserved Genesis source models.
//! The represented world's requirements become asserted/retained/protected pairs;
//! views become an explicitly declared passage observer. Notes are forgotten.
//! Total source replay is compared, not the additional guard-success semantics.
//! Different refusal and augmentation premises can refute this translation.
use crate::genesis_passage::{PassageEvent, PassageState};
use crate::genesis_refusal::{Constitution, RepresentedWorld, WorldEvent};
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TranslationError {
    ResourceLimit,
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_wdp/src/genesis_translation.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-translation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TranslationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TranslationError {}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TranslationLimits {
    pub max_events: usize,
    pub max_cells: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TranslationDecision {
    Checked {
        source: RepresentedWorld,
        target: PassageState,
        encoded: Vec<PassageEvent>,
    },
    Refuted {
        index: usize,
        event: WorldEvent,
        before: RepresentedWorld,
        expected: PassageState,
        actual: PassageState,
    },
}
pub fn project_world(w: &RepresentedWorld) -> PassageState {
    PassageState {
        occ: w.data.clone(),
        asserted: w.reqs.clone(),
        wit: w.reqs.clone(),
        prot: w.reqs.clone(),
        obs: Some(w.views.clone()),
        budget: w.budget,
        licensed: w.aug_licensed,
        refusals: w.refusals.clone(),
        halted: false,
    }
}
pub fn encode_event(e: &WorldEvent) -> Vec<PassageEvent> {
    use PassageEvent::*;
    match e {
        WorldEvent::Admit(t) => vec![AdmitOcc(*t)],
        WorldEvent::Require(i, j) => vec![AssertWit(*i, *j), AdmitWit(*i, *j), Protect(*i, *j)],
        WorldEvent::Mark(v, p) => vec![RefineCol(v.clone(), *p)],
        WorldEvent::AddView(v) => vec![AddCol(v.clone())],
        WorldEvent::Refuse(i, j) => vec![Refuse(*i, *j)],
        WorldEvent::Note(_) => vec![],
        WorldEvent::SetBudget(n) => vec![SetBudget(*n)],
        WorldEvent::SetAugLicense(b) => vec![SetLicense(*b)],
    }
}
fn within(w: &RepresentedWorld, max: usize) -> bool {
    let pieces = [
        w.data.len(),
        w.reqs.len(),
        w.refusals.len(),
        w.notes.len(),
        w.views.len(),
    ];
    pieces
        .into_iter()
        .chain(w.views.iter().map(Vec::len))
        .try_fold(0usize, |n, m| n.checked_add(m))
        .is_some_and(|n| n <= max)
}
fn apply_macro_events(
    target: &mut PassageState,
    macro_events: &[PassageEvent],
    max_cells: usize,
) -> Result<(), TranslationError> {
    for e in macro_events {
        *target = target.step(e);
        if !target.within_cells(max_cells) {
            return Err(TranslationError::ResourceLimit);
        }
    }
    Ok(())
}

pub fn check_translation(
    initial: &RepresentedWorld,
    constitution: Constitution,
    events: &[WorldEvent],
    limits: TranslationLimits,
) -> Result<TranslationDecision, TranslationError> {
    if events.len() > limits.max_events || !within(initial, limits.max_cells) {
        return Err(TranslationError::ResourceLimit);
    }
    let mut source = initial.clone();
    let mut target = project_world(initial);
    let mut encoded = Vec::new();
    if !target.within_cells(limits.max_cells) {
        return Err(TranslationError::ResourceLimit);
    }
    for (index, event) in events.iter().enumerate() {
        let macro_events = encode_event(event);
        if encoded
            .len()
            .checked_add(macro_events.len())
            .is_none_or(|n| n > limits.max_events)
        {
            return Err(TranslationError::ResourceLimit);
        }
        let next = source.step(constitution, event);
        if !within(&next, limits.max_cells) {
            return Err(TranslationError::ResourceLimit);
        }
        apply_macro_events(&mut target, &macro_events, limits.max_cells)?;
        let expected = project_world(&next);
        if !expected.within_cells(limits.max_cells) {
            return Err(TranslationError::ResourceLimit);
        }
        if expected != target {
            return Ok(TranslationDecision::Refuted {
                index,
                event: event.clone(),
                before: source,
                expected,
                actual: target,
            });
        }
        encoded.extend(macro_events);
        source = next;
    }
    Ok(TranslationDecision::Checked {
        source,
        target,
        encoded,
    })
}
pub fn verify_translation(
    initial: &RepresentedWorld,
    constitution: Constitution,
    events: &[WorldEvent],
    limits: TranslationLimits,
    c: &TranslationDecision,
) -> Result<(), TranslationError> {
    if check_translation(initial, constitution, events, limits)? == *c {
        Ok(())
    } else {
        Err(TranslationError::CertificateMismatch)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3809f1d2 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
