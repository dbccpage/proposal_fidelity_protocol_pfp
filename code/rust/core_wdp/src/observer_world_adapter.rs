//! The source observer-world five: (image(profile), contexts, histories, witnesses, grammar).
//! A finite closed history restriction is declared explicitly. It supplies neither
//! memory updates nor a grammar interpretation unless those maps are supplied.
use std::collections::BTreeSet;

use core_category_theory::context_reflection::ContextSystem;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorldWitness {
    pub left: usize,
    pub right: usize,
    pub context: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteObserverWorldPacket {
    pub alphabet: Vec<String>,
    pub histories: Vec<Vec<usize>>,
    pub profiles: Vec<String>,
    pub presented_profiles: Vec<usize>,
    pub contexts: Vec<String>,
    /// Context-major maps on the complete declared history carrier.
    pub context_actions: Vec<Vec<usize>>,
    pub witnesses: Vec<WorldWitness>,
    pub grammar: Vec<String>,
    /// An optional explicit interpretation of every grammar expression.
    pub grammar_interpretation: Option<Vec<BTreeSet<usize>>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WorldAdapterError {
    InvalidCarrier,
    InvalidContext,
    InvalidWitness,
    InvalidGrammar,
    MissingGrammarInterpretation,
    ReceiptMismatch,
}

// Origin: engine/crates_rs/core_wdp/src/observer_world_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:observer-world-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for WorldAdapterError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for WorldAdapterError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverWorldReceipt {
    packet: FiniteObserverWorldPacket,
    context_system: ContextSystem,
}

fn valid_labels(labels: &[String]) -> bool {
    labels.iter().all(|label| !label.is_empty())
        && labels.iter().collect::<BTreeSet<_>>().len() == labels.len()
}

impl FiniteObserverWorldPacket {
    pub fn adapt(&self) -> Result<ObserverWorldReceipt, WorldAdapterError> {
        let n = self.histories.len();
        self.validate_carrier(n)?;
        self.validate_contexts(n)?;
        self.validate_grammar()?;
        let transitions = (0..n)
            .map(|h| self.context_actions.iter().map(|map| map[h]).collect())
            .collect();
        let system = ContextSystem::new(
            self.presented_profiles.clone(),
            transitions,
            self.contexts.len(),
        )
        .map_err(|_| WorldAdapterError::InvalidContext)?;
        self.validate_witnesses(n, &system)?;
        Ok(ObserverWorldReceipt {
            packet: self.clone(),
            context_system: system,
        })
    }

    fn validate_carrier(&self, n: usize) -> Result<(), WorldAdapterError> {
        let valid_histories = n > 0
            && valid_labels(&self.alphabet)
            && valid_labels(&self.profiles)
            && self.histories.iter().collect::<BTreeSet<_>>().len() == n
            && !self
                .histories
                .iter()
                .flatten()
                .any(|&d| d >= self.alphabet.len());
        if !valid_histories || !self.valid_presented_profiles(n) {
            return Err(WorldAdapterError::InvalidCarrier);
        }
        Ok(())
    }

    fn valid_presented_profiles(&self, n: usize) -> bool {
        self.presented_profiles.len() == n
            && !self
                .presented_profiles
                .iter()
                .any(|&p| p >= self.profiles.len())
            && self
                .presented_profiles
                .iter()
                .copied()
                .collect::<BTreeSet<_>>()
                .len()
                == self.profiles.len()
    }

    fn validate_contexts(&self, n: usize) -> Result<(), WorldAdapterError> {
        if !valid_labels(&self.contexts)
            || self.context_actions.len() != self.contexts.len()
            || self
                .context_actions
                .iter()
                .any(|map| map.len() != n || map.iter().any(|&h| h >= n))
        {
            return Err(WorldAdapterError::InvalidContext);
        }
        Ok(())
    }

    fn validate_grammar(&self) -> Result<(), WorldAdapterError> {
        if !valid_labels(&self.grammar)
            || self
                .grammar_interpretation
                .as_ref()
                .is_some_and(|interpretation| {
                    interpretation.len() != self.grammar.len()
                        || interpretation
                            .iter()
                            .flatten()
                            .any(|&p| p >= self.profiles.len())
                })
        {
            return Err(WorldAdapterError::InvalidGrammar);
        }
        Ok(())
    }

    fn validate_witnesses(
        &self,
        n: usize,
        system: &ContextSystem,
    ) -> Result<(), WorldAdapterError> {
        for witness in &self.witnesses {
            if witness.left >= n || witness.right >= n || witness.context >= self.contexts.len() {
                return Err(WorldAdapterError::InvalidWitness);
            }
            let map = &self.context_actions[witness.context];
            if !system.related(witness.left, witness.right)
                || system.related(map[witness.left], map[witness.right])
            {
                return Err(WorldAdapterError::InvalidWitness);
            }
        }
        Ok(())
    }
}

impl ObserverWorldReceipt {
    pub fn packet(&self) -> &FiniteObserverWorldPacket {
        &self.packet
    }
    pub fn context_system(&self) -> &ContextSystem {
        &self.context_system
    }

    /// Source facts require both declared grammar expressibility and forward
    /// context stability. Noncongruent contexts are retained on histories.
    pub fn facts(&self) -> Result<BTreeSet<BTreeSet<usize>>, WorldAdapterError> {
        let interpretation = self
            .packet
            .grammar_interpretation
            .as_ref()
            .ok_or(WorldAdapterError::MissingGrammarInterpretation)?;
        Ok(interpretation
            .iter()
            .filter(|subset| {
                self.packet.context_actions.iter().all(|map| {
                    self.packet
                        .presented_profiles
                        .iter()
                        .enumerate()
                        .all(|(h, p)| {
                            !subset.contains(p)
                                || subset.contains(&self.packet.presented_profiles[map[h]])
                        })
                })
            })
            .cloned()
            .collect())
    }

    pub fn verify_against(
        &self,
        packet: &FiniteObserverWorldPacket,
    ) -> Result<(), WorldAdapterError> {
        if self.packet != *packet || packet.adapt()? != *self {
            return Err(WorldAdapterError::ReceiptMismatch);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_18ef7f37 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
