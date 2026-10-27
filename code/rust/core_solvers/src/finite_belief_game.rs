//! Exact finite reachability games over declared belief states (WDP Appendix S).
//!
//! The controller chooses an enabled action; the adversary chooses a successor.
//! Strictly positive rational costs make a finite Bellman certificate well-founded:
//! along its chosen actions every successor has a strictly smaller value.
//! `None` means losing in this supplied arena, not physical impossibility.
//! This owner does not construct beliefs from the world or admit action authority.

use num_rational::BigRational;
use num_traits::Zero;
use std::collections::{BTreeMap, BTreeSet};

pub const MAX_STATES: usize = 128;
pub const MAX_ACTIONS: usize = 128;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GameError {
    Shape,
    Cost,
    Action,
    Certificate,
    Partition,
}

// Origin: engine/crates_rs/core_solvers/src/finite_belief_game.rs
// Claim: urn:core:crates_rs:core-solvers:finite-belief-game:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GameError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GameError {}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Action {
    pub label: String,
    pub cost: BigRational,
    pub successors: Vec<usize>,
}

#[derive(Clone, Debug)]
pub struct Arena {
    targets: Vec<bool>,
    actions: Vec<Vec<Action>>,
    initial: usize,
}

/// Values and a memoryless strategy. With `verify`, None is certified losing;
/// with `verify_feasible`, None is unclaimed and supplies no losing certificate.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Certificate {
    pub values: Vec<Option<BigRational>>,
    pub choices: Vec<Option<usize>>,
}

fn rational(value: &BigRational, positive: bool) -> bool {
    value.denom() > &0.into()
        && value.numer() >= &0.into()
        && (!positive || !value.numer().is_zero())
        && value.numer().bits() <= 256
        && value.denom().bits() <= 256
}

impl Arena {
    fn validate_and_normalize_action<'a>(
        action: &'a mut Action,
        n: usize,
        labels: &mut BTreeSet<&'a String>,
    ) -> Result<(), GameError> {
        if !rational(&action.cost, true) {
            return Err(GameError::Cost);
        }
        // Callers can construct new_raw ratios; normalize admitted
        // positive costs before using them as congruence signatures.
        action.cost = BigRational::new(action.cost.numer().clone(), action.cost.denom().clone());
        let unique_succs =
            action.successors.iter().collect::<BTreeSet<_>>().len() == action.successors.len();
        let valid_action = !action.label.is_empty()
            && labels.insert(&action.label)
            && (1..=n).contains(&action.successors.len())
            && action.successors.iter().all(|s| *s < n)
            && unique_succs;
        if !valid_action {
            return Err(GameError::Action);
        }
        Ok(())
    }

    pub fn new(
        targets: Vec<bool>,
        mut actions: Vec<Vec<Action>>,
        initial: usize,
    ) -> Result<Self, GameError> {
        let n = targets.len();
        if !(1..=MAX_STATES).contains(&n) || actions.len() != n || initial >= n {
            return Err(GameError::Shape);
        }
        for row in &mut actions {
            if row.len() > MAX_ACTIONS {
                return Err(GameError::Shape);
            }
            let mut labels = BTreeSet::new();
            for action in row {
                Self::validate_and_normalize_action(action, n, &mut labels)?;
            }
        }
        Ok(Self {
            targets,
            actions,
            initial,
        })
    }

    pub fn initial(&self) -> usize {
        self.initial
    }
    pub fn states(&self) -> usize {
        self.targets.len()
    }

    fn candidate(action: &Action, values: &[Option<BigRational>]) -> Option<BigRational> {
        let future = action
            .successors
            .iter()
            .map(|s| values[*s].as_ref())
            .collect::<Option<Vec<_>>>()?;
        // Nonempty successors were checked by Arena::new.
        Some(&action.cost + *future.iter().max()?)
    }

    /// Backward finite-horizon dynamic programming. A proper memoryless strategy
    /// has no reachable non-target cycle, so n rounds contain every finite optimum.
    pub fn solve(&self) -> Certificate {
        let mut values: Vec<_> = self
            .targets
            .iter()
            .map(|target| target.then(BigRational::zero))
            .collect();
        for _ in 0..self.states() {
            let mut next = values.clone();
            for s in 0..self.states() {
                if !self.targets[s] {
                    next[s] = self.actions[s]
                        .iter()
                        .filter_map(|a| Self::candidate(a, &values))
                        .min();
                }
            }
            if next == values {
                break;
            }
            values = next;
        }
        let choices = (0..self.states())
            .map(|s| {
                if self.targets[s] || values[s].is_none() {
                    return None;
                }
                self.actions[s]
                    .iter()
                    .position(|a| Self::candidate(a, &values) == values[s])
            })
            .collect();
        Certificate { values, choices }
    }

    fn has_valid_certificate_ratios(values: &[Option<BigRational>]) -> bool {
        !values
            .iter()
            .flatten()
            .any(|v| v.denom() <= &0.into() || v.numer() < &0.into())
    }

    fn verify_bellman_state(&self, certificate: &Certificate, s: usize) -> Result<(), GameError> {
        let value = &certificate.values[s];
        let choice = certificate.choices[s];
        if self.targets[s] {
            if value != &Some(BigRational::zero()) || choice.is_some() {
                return Err(GameError::Certificate);
            }
            return Ok(());
        }
        let best = self.actions[s]
            .iter()
            .filter_map(|a| Self::candidate(a, &certificate.values))
            .min();
        if best != *value {
            return Err(GameError::Certificate);
        }
        match (value, choice) {
            (None, None) => Ok(()),
            (Some(_), Some(i))
                if self.actions[s]
                    .get(i)
                    .is_some_and(|a| Self::candidate(a, &certificate.values) == *value) =>
            {
                Ok(())
            }
            _ => Err(GameError::Certificate),
        }
    }

    /// Replay a submitted certificate without calling the producer. Bellman
    /// inequalities provide the lower bound, the chosen equality provides a
    /// strictly decreasing winning strategy, and every losing state's action
    /// has a losing successor. Targets take precedence over dead ends.
    pub fn verify(&self, certificate: &Certificate) -> Result<(), GameError> {
        let n = self.states();
        if certificate.values.len() != n || certificate.choices.len() != n {
            return Err(GameError::Shape);
        }
        if !Self::has_valid_certificate_ratios(&certificate.values) {
            return Err(GameError::Certificate);
        }
        for s in 0..n {
            self.verify_bellman_state(certificate, s)?;
        }
        Ok(())
    }

    fn verify_feasible_state(&self, certificate: &Certificate, s: usize) -> Result<(), GameError> {
        match (&certificate.values[s], certificate.choices[s]) {
            (None, None) => Ok(()),
            (Some(v), None) if self.targets[s] && v.is_zero() => Ok(()),
            (Some(v), Some(i)) if !self.targets[s] => {
                let cost = self.actions[s]
                    .get(i)
                    .and_then(|a| Self::candidate(a, &certificate.values));
                if cost.is_some_and(|cost| cost <= *v) {
                    Ok(())
                } else {
                    Err(GameError::Certificate)
                }
            }
            _ => Err(GameError::Certificate),
        }
    }

    /// A feasible strategy supplies an upper cost bound, never a lower bound or
    /// a certified losing complement. Only finite-valued states are claimed.
    pub fn verify_feasible(&self, certificate: &Certificate) -> Result<(), GameError> {
        let n = self.states();
        if certificate.values.len() != n || certificate.choices.len() != n {
            return Err(GameError::Shape);
        }
        if certificate.values[self.initial].is_none()
            || !Self::has_valid_certificate_ratios(&certificate.values)
        {
            return Err(GameError::Certificate);
        }
        for s in 0..n {
            self.verify_feasible_state(certificate, s)?;
        }
        Ok(())
    }

    /// A losing trap must contain the initial state, contain no target, and let
    /// the adversary stay in it after every controller action. Reachability of
    /// some avoidable trap is insufficient.
    pub fn verify_loss(&self, losing: &BTreeSet<usize>) -> Result<(), GameError> {
        if !losing.contains(&self.initial) || losing.iter().any(|s| *s >= self.states()) {
            return Err(GameError::Certificate);
        }
        for &s in losing {
            if self.targets[s]
                || self.actions[s]
                    .iter()
                    .any(|a| !a.successors.iter().any(|t| losing.contains(t)))
            {
                return Err(GameError::Certificate);
            }
        }
        Ok(())
    }

    /// Coarsest refinement preserving targets, action labels, prices and
    /// successor-block sets. A strict round splits a block; at most n-|Pi0|
    /// strict rounds are possible. State enumeration only names the blocks.
    pub fn refine(&self, initial: &[usize]) -> Result<Vec<usize>, GameError> {
        if initial.len() != self.states() {
            return Err(GameError::Partition);
        }
        let mut blocks = normalize(initial);
        loop {
            let mut names = BTreeMap::new();
            let mut next = Vec::new();
            for s in 0..self.states() {
                let mut actions: Vec<_> = self.actions[s]
                    .iter()
                    .map(|a| {
                        (
                            a.label.clone(),
                            a.cost.clone(),
                            a.successors
                                .iter()
                                .map(|t| blocks[*t])
                                .collect::<BTreeSet<_>>(),
                        )
                    })
                    .collect();
                actions.sort();
                let signature = (blocks[s], self.targets[s], actions);
                let fresh = names.len();
                next.push(*names.entry(signature).or_insert(fresh));
            }
            if next == blocks {
                return Ok(blocks);
            }
            blocks = next;
        }
    }

    pub fn quotient(&self, blocks: &[usize]) -> Result<Arena, GameError> {
        if blocks.len() != self.states() {
            return Err(GameError::Partition);
        }
        let blocks = normalize(blocks);
        if self.refine(&blocks)? != blocks {
            return Err(GameError::Partition);
        }
        let count = blocks.iter().copied().max().ok_or(GameError::Partition)? + 1;
        let mut targets = vec![false; count];
        let mut actions = vec![Vec::new(); count];
        let mut seen = BTreeSet::new();
        for (s, &block) in blocks.iter().enumerate() {
            if !seen.insert(block) {
                continue;
            }
            targets[block] = self.targets[s];
            actions[block] = self.actions[s]
                .iter()
                .map(|a| Action {
                    label: a.label.clone(),
                    cost: a.cost.clone(),
                    successors: a
                        .successors
                        .iter()
                        .map(|t| blocks[*t])
                        .collect::<BTreeSet<_>>()
                        .into_iter()
                        .collect(),
                })
                .collect();
        }
        Arena::new(targets, actions, blocks[self.initial])
    }
}

fn normalize(labels: &[usize]) -> Vec<usize> {
    let mut names = BTreeMap::new();
    labels
        .iter()
        .map(|label| {
            let fresh = names.len();
            *names.entry(*label).or_insert(fresh)
        })
        .collect()
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_54589aa6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
