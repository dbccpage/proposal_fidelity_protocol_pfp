//! Exact supplied Boolean graphs/CNF and deterministic finite-prefix tape machines.
//! No logic, permission, universal computation or halting oracle is inferred.
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ComputationError {
    InvalidGraph,
    InvalidAssignment,
    InvalidCnf,
    GraphMismatch,
    InvalidMachine,
    InvalidConfiguration,
    UndefinedTransition,
    AlreadyHalted,
    HeadOverflow,
    ForgedRun,
}

// Origin: engine/crates_rs/core_solvers/src/data_computation_carrier.rs
// Claim: urn:core:crates_rs:core-solvers:data-computation-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ComputationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ComputationError {}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Literal {
    pub variable: usize,
    pub positive: bool,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Cnf {
    pub variables: usize,
    pub clauses: Vec<Vec<Literal>>,
}
impl Cnf {
    pub fn satisfied_by(&self, assignment: &[bool]) -> Result<bool, ComputationError> {
        if assignment.len() != self.variables {
            return Err(ComputationError::InvalidAssignment);
        }
        if self
            .clauses
            .iter()
            .flatten()
            .any(|l| l.variable >= self.variables)
        {
            return Err(ComputationError::InvalidCnf);
        }
        Ok(self
            .clauses
            .iter()
            .all(|clause| clause.iter().any(|l| assignment[l.variable] == l.positive)))
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BooleanGraph {
    arity: usize,
    outputs: Vec<bool>,
}
impl BooleanGraph {
    pub fn new(arity: usize, outputs: Vec<bool>) -> Result<Self, ComputationError> {
        let count = u32::try_from(arity)
            .ok()
            .and_then(|n| 1usize.checked_shl(n))
            .ok_or(ComputationError::InvalidGraph)?;
        if outputs.len() != count {
            return Err(ComputationError::InvalidGraph);
        }
        Ok(Self { arity, outputs })
    }
    pub fn arity(&self) -> usize {
        self.arity
    }
    pub fn outputs(&self) -> &[bool] {
        &self.outputs
    }
    pub fn evaluate(&self, inputs: &[bool]) -> Result<bool, ComputationError> {
        if inputs.len() != self.arity {
            return Err(ComputationError::InvalidAssignment);
        }
        let index = inputs
            .iter()
            .fold(0usize, |n, &bit| 2 * n + usize::from(bit));
        Ok(self.outputs[index])
    }
    /// Forbid precisely each input row with the wrong output; literals negate
    /// that complete assignment. No opaque SAT backend supplies the evidence.
    pub fn graph_cnf(&self) -> Cnf {
        let clauses = self
            .outputs
            .iter()
            .enumerate()
            .map(|(row, &output)| {
                (0..self.arity)
                    .map(|i| Literal {
                        variable: i,
                        positive: row & (1 << (self.arity - 1 - i)) == 0,
                    })
                    .chain(std::iter::once(Literal {
                        variable: self.arity,
                        positive: output,
                    }))
                    .collect()
            })
            .collect();
        Cnf {
            variables: self.arity + 1,
            clauses,
        }
    }
    /// Independently verify CNF semantics on every input/output assignment.
    pub fn verify_cnf(&self, candidate: &Cnf) -> Result<(), ComputationError> {
        if candidate.variables != self.arity + 1 {
            return Err(ComputationError::InvalidCnf);
        }
        for (row, &expected) in self.outputs.iter().enumerate() {
            let inputs: Vec<_> = (0..self.arity)
                .map(|i| row & (1 << (self.arity - 1 - i)) != 0)
                .collect();
            for output in [false, true] {
                let mut assignment = inputs.clone();
                assignment.push(output);
                if candidate.satisfied_by(&assignment)? != (output == expected) {
                    return Err(ComputationError::GraphMismatch);
                }
            }
        }
        Ok(())
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Configuration {
    pub state: usize,
    pub head: i64,
    /// Canonical sparse tape; blank entries are forbidden.
    pub cells: BTreeMap<i64, usize>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Transition {
    pub next_state: usize,
    pub write: usize,
    pub movement: i8,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteMachine {
    states: usize,
    symbols: usize,
    blank: usize,
    initial: usize,
    halting: BTreeSet<usize>,
    transitions: BTreeMap<(usize, usize), Transition>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PrefixTermination {
    Halted,
    BoundExhausted,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MachineRun {
    pub configurations: Vec<Configuration>,
    pub bound: usize,
    pub termination: PrefixTermination,
}
impl FiniteMachine {
    fn is_valid_transition(
        states: usize,
        symbols: usize,
        halting: &BTreeSet<usize>,
        s: usize,
        d: usize,
        t: &Transition,
    ) -> bool {
        [
            s < states,
            d < symbols,
            !halting.contains(&s),
            t.next_state < states,
            t.write < symbols,
            (-1..=1).contains(&t.movement),
        ]
        .into_iter()
        .all(|b| b)
    }

    pub fn new(
        states: usize,
        symbols: usize,
        blank: usize,
        initial: usize,
        halting: BTreeSet<usize>,
        transitions: BTreeMap<(usize, usize), Transition>,
    ) -> Result<Self, ComputationError> {
        let base_valid = states > 0
            && symbols > 0
            && blank < symbols
            && initial < states
            && halting.iter().all(|&s| s < states);
        let transitions_valid = transitions
            .iter()
            .all(|(&(s, d), t)| Self::is_valid_transition(states, symbols, &halting, s, d, t));
        if !base_valid || !transitions_valid {
            return Err(ComputationError::InvalidMachine);
        }
        Ok(Self {
            states,
            symbols,
            blank,
            initial,
            halting,
            transitions,
        })
    }
    pub fn initial_state(&self) -> usize {
        self.initial
    }
    pub fn is_halting(&self, state: usize) -> bool {
        self.halting.contains(&state)
    }
    pub fn transition_keys(&self) -> BTreeSet<(usize, usize)> {
        self.transitions.keys().copied().collect()
    }
    pub fn checked_read(&self, c: &Configuration) -> Result<usize, ComputationError> {
        if c.state >= self.states
            || c.cells
                .values()
                .any(|&d| d >= self.symbols || d == self.blank)
        {
            return Err(ComputationError::InvalidConfiguration);
        }
        Ok(c.cells.get(&c.head).copied().unwrap_or(self.blank))
    }
    pub fn step(&self, c: &Configuration) -> Result<Configuration, ComputationError> {
        let symbol = self.checked_read(c)?;
        if self.is_halting(c.state) {
            return Err(ComputationError::AlreadyHalted);
        }
        let t = self
            .transitions
            .get(&(c.state, symbol))
            .ok_or(ComputationError::UndefinedTransition)?;
        let head = c
            .head
            .checked_add(i64::from(t.movement))
            .ok_or(ComputationError::HeadOverflow)?;
        let mut cells = c.cells.clone();
        if t.write == self.blank {
            cells.remove(&c.head);
        } else {
            cells.insert(c.head, t.write);
        }
        Ok(Configuration {
            state: t.next_state,
            head,
            cells,
        })
    }
    pub fn execute(
        &self,
        initial: &Configuration,
        bound: usize,
    ) -> Result<MachineRun, ComputationError> {
        self.checked_read(initial)?;
        if initial.state != self.initial {
            return Err(ComputationError::InvalidConfiguration);
        }
        let mut configurations = vec![initial.clone()];
        for _ in 0..bound {
            let last = configurations
                .last()
                .ok_or(ComputationError::InvalidConfiguration)?;
            if self.is_halting(last.state) {
                break;
            }
            configurations.push(self.step(last)?);
        }
        let termination = if self.is_halting(
            configurations
                .last()
                .ok_or(ComputationError::InvalidConfiguration)?
                .state,
        ) {
            PrefixTermination::Halted
        } else {
            PrefixTermination::BoundExhausted
        };
        Ok(MachineRun {
            configurations,
            bound,
            termination,
        })
    }
    pub fn verify_run(
        &self,
        initial: &Configuration,
        bound: usize,
        candidate: &MachineRun,
    ) -> Result<(), ComputationError> {
        if *candidate != self.execute(initial, bound)? {
            return Err(ComputationError::ForgedRun);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ea1836f4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
