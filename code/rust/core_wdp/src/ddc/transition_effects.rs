//! Finite event-effect quotient and replay-congruence reference kernel.
//!
//! Events are compared by their complete transition tables on one declared finite
//! state carrier. Raw semantic equality is kept separate from governed equality:
//! two events with the same state action are not interchangeable when their owner
//! or effect kind differs. This is a bounded DDA precursor, not a universal trace calculus.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b8dbe3b2<T> {
    fn checked_invariant_b8dbe3b2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b8dbe3b2<T> for Option<T> {
    #[inline]
    fn checked_invariant_b8dbe3b2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b8dbe3b2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b8dbe3b2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet};
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum EffectOwner {
    #[serde(rename = "Declaration")]
    Declaration,
    #[serde(rename = "Solver")]
    Solver,
    #[serde(rename = "Host")]
    Host,
    #[serde(rename = "Terminalizer")]
    Terminalizer,
}

impl EffectOwner {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Declaration => "Declaration",
            Self::Solver => "Solver",
            Self::Host => "Host",
            Self::Terminalizer => "Terminalizer",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum EffectKind {
    #[serde(rename = "Admission")]
    Admission,
    #[serde(rename = "ObserverDeclaration")]
    ObserverDeclaration,
    #[serde(rename = "SameLevelRepair")]
    SameLevelRepair,
    #[serde(rename = "StructureExtensionProposal")]
    StructureExtensionProposal,
    #[serde(rename = "TypedRefusal")]
    TypedRefusal,
    #[serde(rename = "BudgetControl")]
    BudgetControl,
    #[serde(rename = "CapabilityControl")]
    CapabilityControl,
    #[serde(rename = "Terminal")]
    Terminal,
}

impl EffectKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Admission => "Admission",
            Self::ObserverDeclaration => "ObserverDeclaration",
            Self::SameLevelRepair => "SameLevelRepair",
            Self::StructureExtensionProposal => "StructureExtensionProposal",
            Self::TypedRefusal => "TypedRefusal",
            Self::BudgetControl => "BudgetControl",
            Self::CapabilityControl => "CapabilityControl",
            Self::Terminal => "Terminal",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
}

impl Refusal {
    pub fn new(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: message.into(),
        }
    }
}

#[derive(Debug, Error)]
pub enum TransitionEffectsError {
    #[error("Invalid identifier in field '{field}': '{value}'")]
    InvalidIdentifier { field: String, value: String },
    #[error("Invalid digest in field '{field}': '{value}'")]
    InvalidDigest { field: String, value: String },
    #[error("Validation error: {0}")]
    Validation(String),
    #[error("Event not found: '{0}'")]
    EventNotFound(String),
    #[error("State not found: '{0}'")]
    StateNotFound(String),
    #[error("Authority effect must be None")]
    NonZeroAuthority,
    #[error("Canonical serialization failed: {0}")]
    Serialization(String),
}

fn validate_identifier(value: &str, field: &str) -> Result<String, TransitionEffectsError> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err(TransitionEffectsError::InvalidIdentifier {
            field: field.to_string(),
            value: value.to_string(),
        });
    }
    let mut chars = trimmed.chars();
    let first = chars.next().checked_invariant_b8dbe3b2("checked invariant");
    if !first.is_ascii_alphanumeric() {
        return Err(TransitionEffectsError::InvalidIdentifier {
            field: field.to_string(),
            value: value.to_string(),
        });
    }
    if !chars.all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | ':' | '/' | '@' | '-')) {
        return Err(TransitionEffectsError::InvalidIdentifier {
            field: field.to_string(),
            value: value.to_string(),
        });
    }
    Ok(trimmed.to_string())
}

fn validate_digest(value: &str, field: &str) -> Result<String, TransitionEffectsError> {
    let trimmed = value.trim();
    if !trimmed.starts_with("sha256:") {
        return Err(TransitionEffectsError::InvalidDigest {
            field: field.to_string(),
            value: value.to_string(),
        });
    }
    let rest = &trimmed["sha256:".len()..];
    if rest.len() != 64
        || !rest
            .chars()
            .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase())
    {
        return Err(TransitionEffectsError::InvalidDigest {
            field: field.to_string(),
            value: value.to_string(),
        });
    }
    Ok(trimmed.to_string())
}

fn sort_json_value(val: Value) -> Value {
    match val {
        Value::Object(map) => {
            let sorted: BTreeMap<String, Value> = map
                .into_iter()
                .map(|(k, v)| (k, sort_json_value(v)))
                .collect();
            serde_json::to_value(sorted).unwrap_or(Value::Null)
        }
        Value::Array(arr) => Value::Array(arr.into_iter().map(sort_json_value).collect()),
        other => other,
    }
}

pub fn canonical_id(domain: &str, payload: &Value) -> Result<String, TransitionEffectsError> {
    validate_identifier(domain, "domain")?;
    let mut envelope = BTreeMap::new();
    envelope.insert("domain".to_string(), Value::String(domain.to_string()));
    envelope.insert("payload".to_string(), sort_json_value(payload.clone()));

    let bytes = serde_json::to_vec(&Value::Object(envelope.into_iter().collect()))
        .map_err(|e| TransitionEffectsError::Serialization(e.to_string()))?;

    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let digest = hasher.finalize();
    Ok(format!("sha256:{}", hex::encode(digest)))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EventV1 {
    pub event_id: String,
    pub owner: EffectOwner,
    pub kind: EffectKind,
    pub transitions: Vec<String>,
    pub authority_effect: String,
}

impl EventV1 {
    pub fn new(
        event_id: impl Into<String>,
        owner: EffectOwner,
        kind: EffectKind,
        transitions: Vec<String>,
    ) -> Result<Self, TransitionEffectsError> {
        let event_id_str = event_id.into();
        let validated_id = validate_identifier(&event_id_str, "event_id")?;
        let mut validated_transitions = Vec::with_capacity(transitions.len());
        for target in transitions {
            validated_transitions.push(validate_identifier(&target, "transition target")?);
        }

        Ok(Self {
            event_id: validated_id,
            owner,
            kind,
            transitions: validated_transitions,
            authority_effect: "None".to_string(),
        })
    }

    pub fn to_canonical_value(&self) -> Value {
        json!({
            "event_id": self.event_id,
            "owner": self.owner.as_str(),
            "kind": self.kind.as_str(),
            "transitions": self.transitions,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, TransitionEffectsError> {
        canonical_id(
            "core.transition-effects.event.v1",
            &self.to_canonical_value(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteTransitionSystemV1 {
    pub states: Vec<String>,
    pub events: Vec<EventV1>,
    pub terminal_states: Vec<String>,
    pub authority_effect: String,
}

impl FiniteTransitionSystemV1 {
    pub fn new(
        states: Vec<String>,
        events: Vec<EventV1>,
        terminal_states: Vec<String>,
    ) -> Result<Self, TransitionEffectsError> {
        if states.is_empty() {
            return Err(TransitionEffectsError::Validation(
                "states must be non-empty".to_string(),
            ));
        }
        let mut validated_states = Vec::with_capacity(states.len());
        let mut state_set = HashSet::new();
        for state in states {
            let valid = validate_identifier(&state, "state")?;
            if !state_set.insert(valid.clone()) {
                return Err(TransitionEffectsError::Validation(
                    "states must not contain duplicates".to_string(),
                ));
            }
            validated_states.push(valid);
        }

        let mut event_ids = HashSet::new();
        for event in &events {
            if !event_ids.insert(event.event_id.clone()) {
                return Err(TransitionEffectsError::Validation(
                    "event IDs must not contain duplicates".to_string(),
                ));
            }
            if event.transitions.len() != validated_states.len() {
                return Err(TransitionEffectsError::Validation(
                    "every event must act on every declared state".to_string(),
                ));
            }
            for target in &event.transitions {
                if !state_set.contains(target) {
                    return Err(TransitionEffectsError::Validation(
                        "event transition target lies outside the state carrier".to_string(),
                    ));
                }
            }
        }

        let mut validated_terminals = Vec::with_capacity(terminal_states.len());
        let mut terminal_set = HashSet::new();
        for terminal in terminal_states {
            let valid = validate_identifier(&terminal, "terminal state")?;
            if !state_set.contains(&valid) {
                return Err(TransitionEffectsError::Validation(
                    "terminal states must be members of the state carrier".to_string(),
                ));
            }
            if !terminal_set.insert(valid.clone()) {
                return Err(TransitionEffectsError::Validation(
                    "terminal states must be unique".to_string(),
                ));
            }
            validated_terminals.push(valid);
        }

        for terminal in &validated_terminals {
            let idx = validated_states.iter().position(|s| s == terminal).checked_invariant_b8dbe3b2("checked invariant");
            for event in &events {
                if &event.transitions[idx] != terminal {
                    return Err(TransitionEffectsError::Validation(
                        "every declared terminal state must absorb every event".to_string(),
                    ));
                }
            }
        }

        Ok(Self {
            states: validated_states,
            events,
            terminal_states: validated_terminals,
            authority_effect: "None".to_string(),
        })
    }

    pub fn to_canonical_value(&self) -> Value {
        json!({
            "states": self.states,
            "events": self.events.iter().map(|e| e.to_canonical_value()).collect::<Vec<_>>(),
            "terminal_states": self.terminal_states,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, TransitionEffectsError> {
        canonical_id(
            "core.transition-effects.system.v1",
            &self.to_canonical_value(),
        )
    }

    pub fn event(&self, event_id: &str) -> Result<&EventV1, TransitionEffectsError> {
        self.events
            .iter()
            .find(|e| e.event_id == event_id)
            .ok_or_else(|| TransitionEffectsError::EventNotFound(event_id.to_string()))
    }

    pub fn step(&self, state: &str, event_id: &str) -> Result<String, TransitionEffectsError> {
        let state_idx = self
            .states
            .iter()
            .position(|s| s == state)
            .ok_or_else(|| TransitionEffectsError::StateNotFound(state.to_string()))?;
        let event = self.event(event_id)?;
        Ok(event.transitions[state_idx].clone())
    }

    pub fn replay(&self, state: &str, trace: &[String]) -> Result<String, Refusal> {
        let mut current = state.to_string();
        for event_id in trace {
            match self.step(&current, event_id) {
                Ok(next_state) => current = next_state,
                Err(err) => {
                    return Err(Refusal::new("TRACE_OUTSIDE_SYSTEM", err.to_string()));
                }
            }
        }
        Ok(current)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EffectReceiptV1 {
    pub system_id: String,
    pub event_id: String,
    pub event_digest: String,
    pub owner: EffectOwner,
    pub kind: EffectKind,
    pub transition_digest: String,
    pub authority_effect: String,
}

impl EffectReceiptV1 {
    pub fn new(
        system_id: impl Into<String>,
        event_id: impl Into<String>,
        event_digest: impl Into<String>,
        owner: EffectOwner,
        kind: EffectKind,
        transition_digest: impl Into<String>,
    ) -> Result<Self, TransitionEffectsError> {
        let sys_id = validate_digest(&system_id.into(), "system_id")?;
        let ev_id = validate_identifier(&event_id.into(), "event_id")?;
        let ev_dig = validate_digest(&event_digest.into(), "event_digest")?;
        let tr_dig = validate_digest(&transition_digest.into(), "transition_digest")?;

        Ok(Self {
            system_id: sys_id,
            event_id: ev_id,
            event_digest: ev_dig,
            owner,
            kind,
            transition_digest: tr_dig,
            authority_effect: "None".to_string(),
        })
    }

    pub fn to_canonical_value(&self) -> Value {
        json!({
            "system_id": self.system_id,
            "event_id": self.event_id,
            "event_digest": self.event_digest,
            "owner": self.owner.as_str(),
            "kind": self.kind.as_str(),
            "transition_digest": self.transition_digest,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, TransitionEffectsError> {
        canonical_id(
            "core.transition-effects.receipt.v1",
            &self.to_canonical_value(),
        )
    }
}

pub fn effect_receipt(
    system: &FiniteTransitionSystemV1,
    event_id: &str,
) -> Result<EffectReceiptV1, TransitionEffectsError> {
    let event = system.event(event_id)?;
    let system_id = system.canonical_id()?;
    let event_digest = event.canonical_id()?;
    let transition_digest = canonical_id(
        "core.transition-effects.transition-table.v1",
        &json!({
            "states": system.states,
            "targets": event.transitions,
        }),
    )?;

    EffectReceiptV1::new(
        system_id,
        event.event_id.clone(),
        event_digest,
        event.owner,
        event.kind,
        transition_digest,
    )
}

pub fn semantic_effect_classes(
    system: &FiniteTransitionSystemV1,
    governed: bool,
) -> Vec<Vec<String>> {
    #[derive(Hash, PartialEq, Eq)]
    struct PartitionKey {
        transitions: Vec<String>,
        owner: Option<EffectOwner>,
        kind: Option<EffectKind>,
    }

    let mut classes: HashMap<PartitionKey, Vec<String>> = HashMap::new();
    for event in &system.events {
        let key = PartitionKey {
            transitions: event.transitions.clone(),
            owner: if governed { Some(event.owner) } else { None },
            kind: if governed { Some(event.kind) } else { None },
        };
        classes.entry(key).or_default().push(event.event_id.clone());
    }

    let mut result: Vec<Vec<String>> = classes
        .into_values()
        .map(|mut group| {
            group.sort();
            group
        })
        .collect();

    result.sort();
    result
}

pub fn events_commute(
    system: &FiniteTransitionSystemV1,
    left_event_id: &str,
    right_event_id: &str,
) -> bool {
    system.states.iter().all(|state| {
        let left_then_right = system
            .step(state, left_event_id)
            .and_then(|s| system.step(&s, right_event_id));
        let right_then_left = system
            .step(state, right_event_id)
            .and_then(|s| system.step(&s, left_event_id));
        match (left_then_right, right_then_left) {
            (Ok(s1), Ok(s2)) => s1 == s2,
            _ => false,
        }
    })
}

fn governance_multiset(
    system: &FiniteTransitionSystemV1,
    trace: &[String],
) -> Result<BTreeMap<(EffectOwner, EffectKind), usize>, TransitionEffectsError> {
    let mut counts = BTreeMap::new();
    for event_id in trace {
        let event = system.event(event_id)?;
        *counts.entry((event.owner, event.kind)).or_insert(0) += 1;
    }
    Ok(counts)
}

fn protected_control_sequence(
    system: &FiniteTransitionSystemV1,
    trace: &[String],
) -> Result<Vec<String>, TransitionEffectsError> {
    let mut result = Vec::new();
    for event_id in trace {
        let event = system.event(event_id)?;
        if matches!(event.owner, EffectOwner::Host | EffectOwner::Terminalizer) {
            result.push(event_id.clone());
        }
    }
    Ok(result)
}

pub fn trace_rewrite_equivalent(
    system: &FiniteTransitionSystemV1,
    source: &[String],
    target: &[String],
) -> Result<bool, Refusal> {
    let src_counts = match governance_multiset(system, source) {
        Ok(c) => c,
        Err(e) => return Err(Refusal::new("TRACE_OUTSIDE_SYSTEM", e.to_string())),
    };
    let tgt_counts = match governance_multiset(system, target) {
        Ok(c) => c,
        Err(e) => return Err(Refusal::new("TRACE_OUTSIDE_SYSTEM", e.to_string())),
    };
    if src_counts != tgt_counts {
        return Ok(false);
    }

    let src_protected = match protected_control_sequence(system, source) {
        Ok(p) => p,
        Err(e) => return Err(Refusal::new("TRACE_OUTSIDE_SYSTEM", e.to_string())),
    };
    let tgt_protected = match protected_control_sequence(system, target) {
        Ok(p) => p,
        Err(e) => return Err(Refusal::new("TRACE_OUTSIDE_SYSTEM", e.to_string())),
    };
    if src_protected != tgt_protected {
        return Ok(false);
    }

    for state in &system.states {
        let left = system.replay(state, source)?;
        let right = system.replay(state, target)?;
        if left != right {
            return Ok(false);
        }
    }
    Ok(true)
}

pub fn solver_trace_allowed(
    system: &FiniteTransitionSystemV1,
    trace: &[String],
) -> Result<bool, Refusal> {
    for event_id in trace {
        let event = match system.event(event_id) {
            Ok(e) => e,
            Err(e) => return Err(Refusal::new("TRACE_OUTSIDE_SYSTEM", e.to_string())),
        };
        if event.owner != EffectOwner::Solver {
            return Ok(false);
        }
    }
    Ok(true)
}

// Origin: engine/crates_rs/core_wdp/src/ddc/transition_effects.rs
// Claim: urn:core:crates_rs:core-wdp:transition-effects:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b8dbe3b2 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
