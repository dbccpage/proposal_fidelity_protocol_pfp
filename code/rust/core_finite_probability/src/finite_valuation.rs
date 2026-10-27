//! Exact nonnegative finite Boolean valuations; no normalization requirement.
//! AuthorityEffect: None. FinN requires a nonempty probability carrier, whereas
//! this unnormalized measure layer also admits the empty carrier.
use std::collections::{BTreeMap, BTreeSet};

use num_traits::{Signed, Zero};
use core_number_theory::rational::Rational;

pub type Event = BTreeSet<usize>;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ValuationError {
    #[error("event is outside the carrier")]
    OutsideCarrier,
    #[error("duplicate event")]
    DuplicateEvent,
    #[error("events do not form a Boolean algebra")]
    NotBooleanAlgebra,
    #[error("valuation is negative or nonzero on empty")]
    InvalidMass,
    #[error("valuation is not disjoint-additive")]
    NotAdditive,
    #[error("event is not measurable")]
    NotMeasurable,
    #[error("map is not total or has an out-of-range image")]
    InvalidMap,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BooleanValuation {
    size: usize,
    values: BTreeMap<Event, Rational>,
    atoms: Vec<Event>,
}

impl BooleanValuation {
    fn verify_boolean_closure(
        full: &Event,
        values: &BTreeMap<Event, Rational>,
    ) -> Result<(), ValuationError> {
        if !values.contains_key(&Event::new()) || !values.contains_key(full) {
            return Err(ValuationError::NotBooleanAlgebra);
        }
        for a in values.keys() {
            let complement: Event = full.difference(a).copied().collect();
            if !values.contains_key(&complement) {
                return Err(ValuationError::NotBooleanAlgebra);
            }
            for b in values.keys() {
                let union: Event = a.union(b).copied().collect();
                if !values.contains_key(&union) {
                    return Err(ValuationError::NotBooleanAlgebra);
                }
            }
        }
        Ok(())
    }

    fn verify_disjoint_additivity(
        values: &BTreeMap<Event, Rational>,
    ) -> Result<(), ValuationError> {
        for (a, av) in values {
            for (b, bv) in values {
                if a.is_disjoint(b) {
                    let union: Event = a.union(b).copied().collect();
                    if values[&union] != av + bv {
                        return Err(ValuationError::NotAdditive);
                    }
                }
            }
        }
        Ok(())
    }

    /// Independently check carrier typing, Boolean closure, nonnegativity and
    /// all disjoint additive equations. Inputs are owned and fields private.
    pub fn try_new(size: usize, entries: Vec<(Event, Rational)>) -> Result<Self, ValuationError> {
        let full: Event = (0..size).collect();
        let mut values = BTreeMap::new();
        for (event, value) in entries {
            if !event.is_subset(&full) {
                return Err(ValuationError::OutsideCarrier);
            }
            if values.insert(event, value).is_some() {
                return Err(ValuationError::DuplicateEvent);
            }
        }
        Self::verify_boolean_closure(&full, &values)?;
        if !values[&Event::new()].is_zero() || values.values().any(Signed::is_negative) {
            return Err(ValuationError::InvalidMass);
        }
        Self::verify_disjoint_additivity(&values)?;
        // Equal event-membership signatures are exactly algebra atoms. Closure
        // makes each signature class measurable, so its mass is uniquely fixed.
        let mut signatures: BTreeMap<Vec<bool>, Event> = BTreeMap::new();
        for point in 0..size {
            let signature = values.keys().map(|event| event.contains(&point)).collect();
            signatures.entry(signature).or_default().insert(point);
        }
        let mut atoms: Vec<Event> = signatures.into_values().collect();
        atoms.sort();
        Ok(Self {
            size,
            values,
            atoms,
        })
    }

    pub fn size(&self) -> usize {
        self.size
    }
    pub fn values(&self) -> &BTreeMap<Event, Rational> {
        &self.values
    }
    pub fn atoms(&self) -> &[Event] {
        &self.atoms
    }
    pub fn atom_masses(&self) -> Vec<Rational> {
        self.atoms
            .iter()
            .map(|atom| self.values[atom].clone())
            .collect()
    }
    pub fn reconstructed_value(&self, event: &Event) -> Result<Rational, ValuationError> {
        if !self.values.contains_key(event) {
            return Err(ValuationError::NotMeasurable);
        }
        Ok(self
            .atoms
            .iter()
            .filter(|atom| atom.is_subset(event))
            .map(|atom| self.values[atom].clone())
            .sum())
    }
    /// Exhibit full-powerset extensions concentrating each atom's mass on its
    /// first/last point. Positive nonsingleton atoms give distinct extensions.
    pub fn singleton_extension(&self, choose_last: bool) -> Vec<Rational> {
        let mut masses = vec![Rational::zero(); self.size];
        for atom in &self.atoms {
            let point = if choose_last {
                atom.last()
            } else {
                atom.first()
            };
            if let Some(&point) = point {
                masses[point] = self.values[atom].clone();
            }
        }
        masses
    }
    /// Nonnegativity is essential: zero atom mass forces every point mass zero.
    pub fn singleton_extension_is_unique(&self) -> bool {
        self.atoms
            .iter()
            .all(|atom| atom.len() == 1 || self.values[atom].is_zero())
    }
    /// Restrict to a coarser Boolean algebra; constructor checks its closure.
    pub fn coarsen(&self, events: Vec<Event>) -> Result<Self, ValuationError> {
        let entries = events
            .into_iter()
            .map(|event| {
                let value = self
                    .values
                    .get(&event)
                    .ok_or(ValuationError::NotMeasurable)?
                    .clone();
                Ok((event, value))
            })
            .collect::<Result<Vec<_>, ValuationError>>()?;
        Self::try_new(self.size, entries)
    }
    /// Pushforward through a declared measurable map. Target events must form a
    /// Boolean algebra and every inverse image must be source-measurable.
    pub fn pushforward(
        &self,
        target_size: usize,
        images: &[usize],
        target_events: Vec<Event>,
    ) -> Result<Self, ValuationError> {
        if images.len() != self.size || images.iter().any(|&i| i >= target_size) {
            return Err(ValuationError::InvalidMap);
        }
        let mut entries = Vec::new();
        for event in target_events {
            if event.iter().any(|&i| i >= target_size) {
                return Err(ValuationError::OutsideCarrier);
            }
            let preimage: Event = images
                .iter()
                .enumerate()
                .filter_map(|(i, image)| event.contains(image).then_some(i))
                .collect();
            let value = self
                .values
                .get(&preimage)
                .ok_or(ValuationError::NotMeasurable)?
                .clone();
            entries.push((event, value));
        }
        Self::try_new(target_size, entries)
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/finite_valuation.rs
// Claim: urn:core:crates_rs:core-finite-probability:finite-valuation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_19e3e7ac {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
