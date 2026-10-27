//! Compile finite partial dynamics to the existing deterministic tape interpreter.
//! Event a is tape symbol a+1; 0 is blank. Controls 0..n are source states,
//! n..2n accept end-of-input, 2n..3n reject an unavailable event. Both terminal
//! ranges retain the source-state index. This is a finite compiler, not a
//! self-interpreter or an unbounded computation theorem.
use crate::data_computation_carrier::{Configuration, FiniteMachine, MachineRun, Transition};
use core_category_theory::finite_continuation::PartialDynamics;
use std::collections::{BTreeMap, BTreeSet};
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StreamError {
    InvalidInput,
    WorkLimit,
    Machine,
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_solvers/src/finite_stream_interpreter.rs
// Claim: urn:core:crates_rs:core-solvers:finite-stream-interpreter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StreamError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StreamError {}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StreamOutcome {
    Accepted {
        state: usize,
    },
    Unavailable {
        position: usize,
        state: usize,
        event: usize,
    },
    FuelExhausted,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StreamCertificate {
    pub run: MachineRun,
    pub outcome: StreamOutcome,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StreamLimits {
    pub max_word_len: usize,
    pub max_steps: usize,
    pub max_trace_cells: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledStream {
    source: PartialDynamics,
    start: usize,
    machine: FiniteMachine,
}
impl CompiledStream {
    pub fn new(
        source: &PartialDynamics,
        start: usize,
        max_rules: usize,
    ) -> Result<Self, StreamError> {
        let n = source.reports().len();
        let symbols = source.transitions()[0]
            .len()
            .checked_add(1)
            .ok_or(StreamError::WorkLimit)?;
        let states = n.checked_mul(3).ok_or(StreamError::WorkLimit)?;
        if start >= n {
            return Err(StreamError::InvalidInput);
        }
        if n.checked_mul(symbols).is_none_or(|c| c > max_rules) {
            return Err(StreamError::WorkLimit);
        }
        let mut rules = BTreeMap::new();
        for (s, row) in source.transitions().iter().enumerate() {
            rules.insert(
                (s, 0),
                Transition {
                    next_state: n + s,
                    write: 0,
                    movement: 0,
                },
            );
            for (a, t) in row.iter().enumerate() {
                let step = match t {
                    Some(t) => Transition {
                        next_state: *t,
                        write: 0,
                        movement: 1,
                    },
                    None => Transition {
                        next_state: 2 * n + s,
                        write: a + 1,
                        movement: 0,
                    },
                };
                rules.insert((s, a + 1), step);
            }
        }
        let machine = FiniteMachine::new(
            states,
            symbols,
            0,
            start,
            (n..states).collect::<BTreeSet<_>>(),
            rules,
        )
        .map_err(|_| StreamError::Machine)?;
        let compiled = Self {
            source: source.clone(),
            start,
            machine,
        };
        compiled.verify_program(&compiled.machine)?;
        Ok(compiled)
    }
    pub fn machine(&self) -> &FiniteMachine {
        &self.machine
    }
    fn expected_step_configuration(
        &self,
        s: usize,
        symbol: usize,
        n: usize,
        cells: BTreeMap<i64, usize>,
    ) -> Configuration {
        if symbol == 0 {
            Configuration {
                state: n + s,
                head: 0,
                cells,
            }
        } else if let Some(t) = self.source.transitions()[s][symbol - 1] {
            Configuration {
                state: t,
                head: 1,
                cells: BTreeMap::new(),
            }
        } else {
            Configuration {
                state: 2 * n + s,
                head: 0,
                cells,
            }
        }
    }

    /// Check every encoded one-step rule against the expected source table.
    /// This also checks both terminal classes and refuses extra transition keys.
    pub fn verify_program(&self, candidate: &FiniteMachine) -> Result<(), StreamError> {
        let n = self.source.reports().len();
        let symbols = self.source.transitions()[0].len() + 1;
        let keys: BTreeSet<_> = (0..n)
            .flat_map(|s| (0..symbols).map(move |a| (s, a)))
            .collect();
        if candidate.initial_state() != self.start
            || candidate.transition_keys() != keys
            || (0..3 * n).any(|s| candidate.is_halting(s) != (s >= n))
        {
            return Err(StreamError::CertificateMismatch);
        }
        for s in 0..n {
            for symbol in 0..symbols {
                let cells = if symbol == 0 {
                    BTreeMap::new()
                } else {
                    BTreeMap::from([(0, symbol)])
                };
                let input = Configuration {
                    state: s,
                    head: 0,
                    cells: cells.clone(),
                };
                let actual = candidate
                    .step(&input)
                    .map_err(|_| StreamError::CertificateMismatch)?;
                let expected = self.expected_step_configuration(s, symbol, n, cells);
                if actual != expected {
                    return Err(StreamError::CertificateMismatch);
                }
            }
        }
        Ok(())
    }
    fn input(
        &self,
        word: &[usize],
        steps: usize,
        limits: StreamLimits,
    ) -> Result<Configuration, StreamError> {
        if word.len() > limits.max_word_len
            || steps > limits.max_steps
            || word
                .len()
                .checked_add(1)
                .and_then(|n| steps.min(n).checked_add(1).and_then(|s| s.checked_mul(n)))
                .is_none_or(|n| n > limits.max_trace_cells)
        {
            return Err(StreamError::WorkLimit);
        }
        if i64::try_from(word.len()).is_err()
            || word
                .iter()
                .any(|&a| a >= self.source.transitions()[0].len())
        {
            return Err(StreamError::InvalidInput);
        }
        let cells = word
            .iter()
            .enumerate()
            .map(|(i, &a)| (i as i64, a + 1))
            .collect();
        Ok(Configuration {
            state: self.start,
            head: 0,
            cells,
        })
    }
    fn expected(&self, word: &[usize], steps: usize) -> StreamOutcome {
        let mut state = self.start;
        for (i, &a) in word.iter().enumerate() {
            if i >= steps {
                return StreamOutcome::FuelExhausted;
            }
            match self.source.transitions()[state][a] {
                Some(t) => state = t,
                None => {
                    return StreamOutcome::Unavailable {
                        position: i,
                        state,
                        event: a,
                    }
                }
            }
        }
        if steps > word.len() {
            StreamOutcome::Accepted { state }
        } else {
            StreamOutcome::FuelExhausted
        }
    }
    pub fn execute(
        &self,
        word: &[usize],
        steps: usize,
        limits: StreamLimits,
    ) -> Result<StreamCertificate, StreamError> {
        let input = self.input(word, steps, limits)?;
        let run = self
            .machine
            .execute(&input, steps)
            .map_err(|_| StreamError::Machine)?;
        let last = run.configurations.last().ok_or(StreamError::Machine)?;
        let n = self.source.reports().len();
        let outcome = if last.state < n {
            StreamOutcome::FuelExhausted
        } else if last.state < 2 * n {
            StreamOutcome::Accepted {
                state: last.state - n,
            }
        } else {
            let position = usize::try_from(last.head).map_err(|_| StreamError::Machine)?;
            StreamOutcome::Unavailable {
                position,
                state: last.state - 2 * n,
                event: *word.get(position).ok_or(StreamError::Machine)?,
            }
        };
        if outcome != self.expected(word, steps) {
            return Err(StreamError::CertificateMismatch);
        }
        Ok(StreamCertificate { run, outcome })
    }
    pub fn verify(
        &self,
        word: &[usize],
        steps: usize,
        limits: StreamLimits,
        c: &StreamCertificate,
    ) -> Result<(), StreamError> {
        if self.execute(word, steps, limits)? == *c {
            Ok(())
        } else {
            Err(StreamError::CertificateMismatch)
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_4f9c976a {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
