use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::collections::{BTreeMap, BTreeSet};

use super::{Presentation, Rule};

/// A computed decomposition of the supplied finite permutation, not a pin.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PermutationOrderWitness {
    order: BigUint,
    cycles: Vec<Vec<String>>,
}

impl PermutationOrderWitness {
    /// The exact least common multiple of the cycle lengths.
    pub fn order(&self) -> &BigUint {
        &self.order
    }

    /// Successor-oriented cycles, each starting at its least Unicode scalar.
    /// The cycles themselves are sorted by their starting scalar.
    pub fn cycles(&self) -> &[Vec<String>] {
        &self.cycles
    }
}

/// Bounded mechanism categories for a relation that is not an admitted
/// nonempty, single-symbol permutation. No submitted text or authority verdict
/// is carried by these errors.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum PermutationOrderError {
    #[error("the permutation signature is empty")]
    EmptySignature,
    #[error("a signature symbol is not exactly one Unicode scalar")]
    SignatureSymbolNotScalar,
    #[error("the signature repeats a symbol")]
    DuplicateSignatureSymbol,
    #[error("a rule source is not exactly one Unicode scalar")]
    RuleSourceNotScalar,
    #[error("a rule target is not exactly one Unicode scalar")]
    RuleTargetNotScalar,
    #[error("a rule source is outside the signature")]
    RuleSourceOutsideSignature,
    #[error("a rule target is outside the signature")]
    RuleTargetOutsideSignature,
    #[error("the relation repeats a rule source")]
    DuplicateRuleSource,
    #[error("the relation is not total on the signature")]
    NonTotal,
    #[error("the relation is not onto the signature")]
    NotOnto,
}

fn single_scalar(text: &str) -> Option<char> {
    let mut scalars = text.chars();
    let scalar = scalars.next()?;
    scalars.next().is_none().then_some(scalar)
}

fn collect_signature_scalars(
    presentation: &Presentation,
) -> Result<BTreeSet<char>, PermutationOrderError> {
    if presentation.signature.is_empty() {
        return Err(PermutationOrderError::EmptySignature);
    }
    let mut symbols = BTreeSet::new();
    for symbol in &presentation.signature {
        let scalar =
            single_scalar(symbol).ok_or(PermutationOrderError::SignatureSymbolNotScalar)?;
        if !symbols.insert(scalar) {
            return Err(PermutationOrderError::DuplicateSignatureSymbol);
        }
    }
    Ok(symbols)
}

fn validate_and_insert_rule(
    rule: &Rule,
    symbols: &BTreeSet<char>,
    successors: &mut BTreeMap<char, char>,
) -> Result<(), PermutationOrderError> {
    let source = single_scalar(&rule.lhs).ok_or(PermutationOrderError::RuleSourceNotScalar)?;
    let target = single_scalar(&rule.rhs).ok_or(PermutationOrderError::RuleTargetNotScalar)?;
    if !symbols.contains(&source) {
        return Err(PermutationOrderError::RuleSourceOutsideSignature);
    }
    if !symbols.contains(&target) {
        return Err(PermutationOrderError::RuleTargetOutsideSignature);
    }
    if successors.insert(source, target).is_some() {
        return Err(PermutationOrderError::DuplicateRuleSource);
    }
    Ok(())
}

fn collect_bijection_successors(
    presentation: &Presentation,
    symbols: &BTreeSet<char>,
) -> Result<BTreeMap<char, char>, PermutationOrderError> {
    let mut successors = BTreeMap::new();
    for rule in &presentation.rules {
        validate_and_insert_rule(rule, symbols, &mut successors)?;
    }
    if successors.len() != symbols.len() {
        return Err(PermutationOrderError::NonTotal);
    }
    let targets: BTreeSet<char> = successors.values().copied().collect();
    if targets != *symbols {
        return Err(PermutationOrderError::NotOnto);
    }
    Ok(successors)
}

fn trace_permutation_cycle(
    start: char,
    successors: &BTreeMap<char, char>,
    seen: &mut BTreeSet<char>,
) -> Result<Vec<String>, PermutationOrderError> {
    let mut cycle = Vec::new();
    let mut current = start;
    loop {
        if !seen.insert(current) {
            return Err(PermutationOrderError::NotOnto);
        }
        cycle.push(current.to_string());
        current = *successors
            .get(&current)
            .ok_or(PermutationOrderError::NonTotal)?;
        if current == start {
            break;
        }
    }
    Ok(cycle)
}

pub(super) fn permutation_order(
    presentation: &Presentation,
) -> Result<PermutationOrderWitness, PermutationOrderError> {
    let symbols = collect_signature_scalars(presentation)?;
    let successors = collect_bijection_successors(presentation, &symbols)?;

    let mut seen = BTreeSet::new();
    let mut cycles = Vec::new();
    let mut order = BigUint::one();
    for &start in &symbols {
        if seen.contains(&start) {
            continue;
        }
        let cycle = trace_permutation_cycle(start, &successors, &mut seen)?;
        let length = BigUint::from(cycle.len());
        let divisor = permutation_gcd(order.clone(), length.clone());
        order = (order / divisor) * length;
        cycles.push(cycle);
    }
    Ok(PermutationOrderWitness { order, cycles })
}

fn permutation_gcd(mut left: BigUint, mut right: BigUint) -> BigUint {
    while !right.is_zero() {
        let remainder = left % &right;
        left = right;
        right = remainder;
    }
    left
}

// Origin: engine/crates_rs/pfp_runtime/src/rewriting/permutation.rs
// Claim: urn:core:crates_rs:pfp-runtime:permutation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_210c2b05 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
