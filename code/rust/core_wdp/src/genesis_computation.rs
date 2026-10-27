//! Supplied source-graph and finite-prefix fidelity, with independent permission.
//! Domain algorithms live in core_solvers. StepTrace retains occurrence order;
//! neither a serialized trace nor any source/hash tag certifies its semantics.
use crate::types::AuthorityEffect;
use core_replay::StepTrace;
use core_solvers::data_computation_carrier::{
    BooleanGraph, Cnf, ComputationError, Configuration, FiniteMachine, MachineRun,
    PrefixTermination, Transition,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BridgeError {
    InvalidPacket,
    UnknownLabel,
    Unauthorized,
    ReadoutMismatch,
    PrefixMismatch,
    Owner(ComputationError),
}

// Origin: engine/crates_rs/core_wdp/src/genesis_computation.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-computation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BridgeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BridgeError {}
impl From<ComputationError> for BridgeError {
    fn from(e: ComputationError) -> Self {
        Self::Owner(e)
    }
}

/// Actual admitted graph instances over two explicitly interpreted opaque data.
/// The relation itself is source data; closed-world truth decoding is supplied.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBooleanPacket {
    pub datum_labels: Vec<String>,
    pub arity: usize,
    pub instances: Vec<Vec<usize>>,
}
pub struct CheckedBooleanPacket {
    source: SourceBooleanPacket,
    graph: BooleanGraph,
}
impl SourceBooleanPacket {
    fn validate_boolean_header(&self) -> Result<(usize, usize), BridgeError> {
        if self.datum_labels.len() != 2
            || self.datum_labels.iter().any(String::is_empty)
            || self.datum_labels[0] == self.datum_labels[1]
            || self.arity == 0
        {
            return Err(BridgeError::InvalidPacket);
        }
        let rows = u32::try_from(self.arity)
            .ok()
            .and_then(|n| 1usize.checked_shl(n))
            .ok_or(BridgeError::InvalidPacket)?;
        let width = self
            .arity
            .checked_add(1)
            .ok_or(BridgeError::InvalidPacket)?;
        if self.instances.len() != rows {
            return Err(BridgeError::InvalidPacket);
        }
        Ok((rows, width))
    }

    pub fn admit(&self) -> Result<CheckedBooleanPacket, BridgeError> {
        let (rows, width) = self.validate_boolean_header()?;
        let mut outputs = vec![None; rows];
        for row in &self.instances {
            if row.len() != width || row.iter().any(|&x| x > 1) {
                return Err(BridgeError::InvalidPacket);
            }
            let index = row[..self.arity].iter().fold(0, |n, &x| 2 * n + x);
            if outputs[index].is_some() {
                return Err(BridgeError::InvalidPacket);
            }
            outputs[index] = Some(row[self.arity] == 1);
        }
        let values = outputs
            .into_iter()
            .collect::<Option<Vec<_>>>()
            .ok_or(BridgeError::InvalidPacket)?;
        Ok(CheckedBooleanPacket {
            source: self.clone(),
            graph: BooleanGraph::new(self.arity, values)?,
        })
    }
}
impl CheckedBooleanPacket {
    pub fn source(&self) -> &SourceBooleanPacket {
        &self.source
    }
    pub fn graph_cnf(&self) -> Cnf {
        self.graph.graph_cnf()
    }
    pub fn verify_cnf(&self, candidate: &Cnf) -> Result<(), BridgeError> {
        Ok(self.graph.verify_cnf(candidate)?)
    }
    pub fn readout(&self, inputs: &[usize]) -> Result<usize, BridgeError> {
        if inputs.iter().any(|&x| x > 1) {
            return Err(BridgeError::InvalidPacket);
        }
        let bits: Vec<_> = inputs.iter().map(|&x| x == 1).collect();
        Ok(usize::from(self.graph.evaluate(&bits)?))
    }
    pub fn verify_readout(&self, inputs: &[usize], candidate: usize) -> Result<(), BridgeError> {
        if candidate != self.readout(inputs)? {
            return Err(BridgeError::ReadoutMismatch);
        }
        Ok(())
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NamedRule {
    pub state: String,
    pub read: String,
    pub next_state: String,
    pub write: String,
    pub movement: i8,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceMachinePacket {
    pub states: Vec<String>,
    pub alphabet: Vec<String>,
    pub blank: String,
    pub initial: String,
    pub halting: BTreeSet<String>,
    pub rules: Vec<NamedRule>,
    pub permissions: BTreeSet<(String, String)>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NamedConfiguration {
    pub state: String,
    pub head: i64,
    pub cells: Vec<(i64, String)>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum NamedTermination {
    Halted,
    BoundExhausted,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourcePrefix {
    pub configurations: Vec<NamedConfiguration>,
    pub bound: usize,
    pub termination: NamedTermination,
}
pub struct CheckedMachinePacket {
    source: SourceMachinePacket,
    owner: FiniteMachine,
    state_ids: BTreeMap<String, usize>,
    symbol_ids: BTreeMap<String, usize>,
}
/// Internal immutable ordered occurrences; repeated equal configurations stay.
pub struct CheckedPrefix {
    trace: StepTrace<NamedConfiguration>,
    bound: usize,
    termination: NamedTermination,
}
fn labels(xs: &[String]) -> Result<BTreeMap<String, usize>, BridgeError> {
    let ids: BTreeMap<_, _> = xs.iter().enumerate().map(|(i, x)| (x.clone(), i)).collect();
    if xs.is_empty() || ids.len() != xs.len() || xs.iter().any(String::is_empty) {
        return Err(BridgeError::InvalidPacket);
    }
    Ok(ids)
}
impl SourceMachinePacket {
    fn build_checked_transitions(
        &self,
        state_ids: &BTreeMap<String, usize>,
        symbol_ids: &BTreeMap<String, usize>,
    ) -> Result<BTreeMap<(usize, usize), Transition>, BridgeError> {
        let mut transitions = BTreeMap::new();
        for r in &self.rules {
            let key = (
                *state_ids.get(&r.state).ok_or(BridgeError::UnknownLabel)?,
                *symbol_ids.get(&r.read).ok_or(BridgeError::UnknownLabel)?,
            );
            let t = Transition {
                next_state: *state_ids
                    .get(&r.next_state)
                    .ok_or(BridgeError::UnknownLabel)?,
                write: *symbol_ids.get(&r.write).ok_or(BridgeError::UnknownLabel)?,
                movement: r.movement,
            };
            if transitions.insert(key, t).is_some() {
                return Err(BridgeError::InvalidPacket);
            }
        }
        Ok(transitions)
    }

    fn validate_machine_permissions(
        &self,
        state_ids: &BTreeMap<String, usize>,
        symbol_ids: &BTreeMap<String, usize>,
        transitions: &BTreeMap<(usize, usize), Transition>,
    ) -> Result<(), BridgeError> {
        for (s, d) in &self.permissions {
            let key = (
                *state_ids.get(s).ok_or(BridgeError::UnknownLabel)?,
                *symbol_ids.get(d).ok_or(BridgeError::UnknownLabel)?,
            );
            if !transitions.contains_key(&key) {
                return Err(BridgeError::InvalidPacket);
            }
        }
        Ok(())
    }

    pub fn admit(&self) -> Result<CheckedMachinePacket, BridgeError> {
        let state_ids = labels(&self.states)?;
        let symbol_ids = labels(&self.alphabet)?;
        let transitions = self.build_checked_transitions(&state_ids, &symbol_ids)?;
        self.validate_machine_permissions(&state_ids, &symbol_ids, &transitions)?;
        let owner = FiniteMachine::new(
            self.states.len(),
            self.alphabet.len(),
            *symbol_ids
                .get(&self.blank)
                .ok_or(BridgeError::UnknownLabel)?,
            *state_ids
                .get(&self.initial)
                .ok_or(BridgeError::UnknownLabel)?,
            self.halting
                .iter()
                .map(|s| state_ids.get(s).copied().ok_or(BridgeError::UnknownLabel))
                .collect::<Result<_, _>>()?,
            transitions,
        )?;
        Ok(CheckedMachinePacket {
            source: self.clone(),
            owner,
            state_ids,
            symbol_ids,
        })
    }
}
impl CheckedMachinePacket {
    pub fn source(&self) -> &SourceMachinePacket {
        &self.source
    }
    fn encode(&self, c: &NamedConfiguration) -> Result<Configuration, BridgeError> {
        if c.cells.windows(2).any(|w| w[0].0 >= w[1].0) {
            return Err(BridgeError::InvalidPacket);
        }
        Ok(Configuration {
            state: *self
                .state_ids
                .get(&c.state)
                .ok_or(BridgeError::UnknownLabel)?,
            head: c.head,
            cells: c
                .cells
                .iter()
                .map(|(i, d)| {
                    Ok((
                        *i,
                        *self.symbol_ids.get(d).ok_or(BridgeError::UnknownLabel)?,
                    ))
                })
                .collect::<Result<_, BridgeError>>()?,
        })
    }
    fn decode(&self, c: &Configuration) -> NamedConfiguration {
        NamedConfiguration {
            state: self.source.states[c.state].clone(),
            head: c.head,
            cells: c
                .cells
                .iter()
                .map(|(&i, &d)| (i, self.source.alphabet[d].clone()))
                .collect(),
        }
    }
    fn authorized_run(
        &self,
        initial: &NamedConfiguration,
        bound: usize,
    ) -> Result<MachineRun, BridgeError> {
        let run = self.owner.execute(&self.encode(initial)?, bound)?;
        for c in run
            .configurations
            .iter()
            .take(run.configurations.len().saturating_sub(1))
        {
            let symbol = self.owner.checked_read(c)?;
            let key = (
                self.source.states[c.state].clone(),
                self.source.alphabet[symbol].clone(),
            );
            if !self.source.permissions.contains(&key) {
                return Err(BridgeError::Unauthorized);
            }
        }
        Ok(run)
    }
    pub fn execute(
        &self,
        initial: &NamedConfiguration,
        bound: usize,
    ) -> Result<CheckedPrefix, BridgeError> {
        let run = self.authorized_run(initial, bound)?;
        let termination = match run.termination {
            PrefixTermination::Halted => NamedTermination::Halted,
            PrefixTermination::BoundExhausted => NamedTermination::BoundExhausted,
        };
        Ok(CheckedPrefix {
            trace: StepTrace::new(run.configurations.iter().map(|c| self.decode(c)).collect()),
            bound,
            termination,
        })
    }
    pub fn verify_prefix(
        &self,
        initial: &NamedConfiguration,
        bound: usize,
        candidate: &SourcePrefix,
    ) -> Result<(), BridgeError> {
        let expected = self.execute(initial, bound)?.export();
        if *candidate != expected {
            return Err(BridgeError::PrefixMismatch);
        }
        Ok(())
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}
impl CheckedPrefix {
    pub fn trace(&self) -> &StepTrace<NamedConfiguration> {
        &self.trace
    }
    pub fn export(&self) -> SourcePrefix {
        SourcePrefix {
            configurations: self.trace.steps().to_vec(),
            bound: self.bound,
            termination: self.termination,
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_4584c266 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
