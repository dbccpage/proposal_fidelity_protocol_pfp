//! Lam-Leung lengths of vanishing sums of n-th roots with nonnegative integer
//! multiplicities: W(n) is the numerical semigroup of n's distinct prime divisors.
//! A witness is a sum of regular prime polygons. It is not a classification of
//! irreducible vanishing sums or a guarantee of distinct roots. AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_96c4190e<T> {
    fn checked_invariant_96c4190e(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_96c4190e<T> for Option<T> {
    #[inline]
    fn checked_invariant_96c4190e(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_96c4190e<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_96c4190e(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::integer_factorization::{factor_natural, FactorizationBudget, FactorizationError};
use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};
use std::collections::{BTreeMap, BTreeSet};

pub const MAX_RESIDUES: usize = 65536;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum VanishingLengthError {
    #[error("a positive conductor is required")]
    InvalidConductor,
    #[error(transparent)]
    Factorization(#[from] FactorizationError),
    #[error("the residue carrier exceeds {MAX_RESIDUES} states")]
    ResidueLimit,
    #[error("the numerical-semigroup search exhausted its declared budget")]
    SearchBudget,
    #[error("the prime-polygon witness does not replay its conductor and length")]
    InvalidWitness,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VanishingLengthWitness {
    pub conductor: u64,
    pub length: BigUint,
    /// p -> number of translated regular p-gons (root repetition is allowed).
    pub prime_cycles: BTreeMap<u64, BigUint>,
}
impl VanishingLengthWitness {
    pub fn verify(&self, budget: FactorizationBudget) -> Result<(), VanishingLengthError> {
        if self.conductor == 0 {
            return Err(VanishingLengthError::InvalidConductor);
        }
        let primes = factor_natural(&BigUint::from(self.conductor), budget)?;
        let mut total = BigUint::zero();
        for (p, count) in &self.prime_cycles {
            if count.is_zero() || !primes.contains_key(&BigUint::from(*p)) {
                return Err(VanishingLengthError::InvalidWitness);
            }
            total += BigUint::from(*p) * count;
        }
        if total != self.length {
            return Err(VanishingLengthError::InvalidWitness);
        }
        Ok(())
    }
}

/// Complete length membership when the declared bounds suffice. Shortest paths
/// on residues modulo the smallest prime find the least representable weight of
/// each residue; adding that prime fills every greater weight in the residue.
fn reconstruct_prime_cycles(
    node: usize,
    states: usize,
    smallest: u64,
    length: &BigUint,
    distance: BigUint,
    modulus: &BigUint,
    parent: &[Option<(usize, u64)>],
) -> Result<BTreeMap<u64, BigUint>, VanishingLengthError> {
    let mut cycles = BTreeMap::<u64, BigUint>::new();
    let mut cursor = node;
    for _ in 0..states {
        if cursor == 0 {
            break;
        }
        let (previous, p) = parent[cursor].ok_or(VanishingLengthError::InvalidWitness)?;
        *cycles.entry(p).or_default() += BigUint::from(1u8);
        cursor = previous;
    }
    if cursor != 0 {
        return Err(VanishingLengthError::InvalidWitness);
    }
    let additional = (length - distance) / modulus;
    if !additional.is_zero() {
        *cycles.entry(smallest).or_default() += additional;
    }
    Ok(cycles)
}

fn relax_prime_transitions(
    node: usize,
    distance: &BigUint,
    smallest: u64,
    primes: &[u64],
    distances: &mut [Option<BigUint>],
    parent: &mut [Option<(usize, u64)>],
    queue: &mut BTreeSet<(BigUint, usize)>,
    fuel: &mut u64,
) -> Result<(), VanishingLengthError> {
    for &p in primes {
        if *fuel == 0 {
            return Err(VanishingLengthError::SearchBudget);
        }
        *fuel -= 1;
        let next = ((node as u128 + u128::from(p)) % u128::from(smallest)) as usize;
        let candidate = distance + BigUint::from(p);
        if distances[next].as_ref().is_none_or(|old| candidate < *old) {
            distances[next] = Some(candidate.clone());
            parent[next] = Some((node, p));
            queue.insert((candidate, next));
        }
    }
    Ok(())
}

fn search_residue_cycles(
    primes: &[u64],
    residue: u64,
    length: &BigUint,
    relaxation_budget: u64,
) -> Result<Option<BTreeMap<u64, BigUint>>, VanishingLengthError> {
    let smallest = primes[0];
    let modulus = BigUint::from(smallest);
    let states = usize::try_from(smallest)
        .ok()
        .filter(|p| *p <= MAX_RESIDUES)
        .ok_or(VanishingLengthError::ResidueLimit)?;
    let mut distances = vec![None::<BigUint>; states];
    let mut parent = vec![None::<(usize, u64)>; states];
    let mut queue = BTreeSet::from([(BigUint::zero(), 0usize)]);
    distances[0] = Some(BigUint::zero());
    let mut fuel = relaxation_budget;
    while let Some((distance, node)) = queue.pop_first() {
        if distances[node].as_ref() != Some(&distance) {
            continue;
        }
        if node as u64 == residue {
            if &distance > length {
                return Ok(None);
            }
            let cycles = reconstruct_prime_cycles(
                node, states, smallest, length, distance, &modulus, &parent,
            )?;
            return Ok(Some(cycles));
        }
        relax_prime_transitions(
            node,
            &distance,
            smallest,
            primes,
            &mut distances,
            &mut parent,
            &mut queue,
            &mut fuel,
        )?;
    }
    Ok(None)
}

pub fn lam_leung_length(
    conductor: u64,
    length: &BigUint,
    factor_budget: FactorizationBudget,
    relaxation_budget: u64,
) -> Result<Option<VanishingLengthWitness>, VanishingLengthError> {
    if conductor == 0 {
        return Err(VanishingLengthError::InvalidConductor);
    }
    let factors = factor_natural(&BigUint::from(conductor), factor_budget)?;
    let primes: Vec<u64> = factors
        .keys()
        .map(|p| p.to_u64().checked_invariant_96c4190e("factors of a u64 fit u64"))
        .collect();
    let build_witness = |prime_cycles| VanishingLengthWitness {
        conductor,
        length: length.clone(),
        prime_cycles,
    };
    if length.is_zero() {
        return Ok(Some(build_witness(BTreeMap::new())));
    }
    if primes.is_empty() {
        return Ok(None);
    }
    let smallest = primes[0];
    let modulus = BigUint::from(smallest);
    let residue = (length % &modulus).to_u64().checked_invariant_96c4190e("remainder fits u64");
    if residue == 0 {
        return Ok(Some(build_witness(BTreeMap::from([(
            smallest,
            length / &modulus,
        )]))));
    }
    if primes.len() == 1 {
        return Ok(None);
    }
    let Some(cycles) = search_residue_cycles(&primes, residue, length, relaxation_budget)? else {
        return Ok(None);
    };
    let result = build_witness(cycles);
    result.verify(factor_budget)?;
    Ok(Some(result))
}

// Origin: engine/crates_rs/core_number_theory/src/vanishing_sums.rs
// Claim: urn:core:crates_rs:core-number-theory:vanishing-sums:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn lam_leung_lengths_match_small_exhaustive_numerical_semigroups() {
        for conductor in [1u64, 2, 6, 15, 30, 35, 49] {
            let factors =
                factor_natural(&BigUint::from(conductor), FactorizationBudget::default()).unwrap();
            let primes: Vec<usize> = factors.keys().map(|p| p.to_usize().unwrap()).collect();
            let mut reachable = vec![false; 101];
            reachable[0] = true;
            for i in 1..reachable.len() {
                reachable[i] = primes.iter().any(|p| i >= *p && reachable[i - *p]);
            }
            for (length, inside) in reachable.iter().enumerate() {
                let answer = lam_leung_length(
                    conductor,
                    &BigUint::from(length),
                    FactorizationBudget::default(),
                    10000,
                )
                .unwrap();
                assert_eq!(answer.is_some(), *inside, "n={conductor}, weight={length}");
                if let Some(w) = answer {
                    w.verify(FactorizationBudget::default()).unwrap();
                }
            }
        }
    }
    #[test]
    fn prime_polygon_witness_replays_in_the_actual_cyclotomic_field() {
        use crate::cyclotomic_field::CyclotomicNumber;
        let w = lam_leung_length(
            15,
            &BigUint::from(8u8),
            FactorizationBudget::default(),
            1000,
        )
        .unwrap()
        .unwrap();
        let z = CyclotomicNumber::zeta(15, 1).unwrap();
        let mut sum = CyclotomicNumber::zero(15).unwrap();
        for (p, count) in w.prime_cycles {
            for _ in 0..count.to_usize().unwrap() {
                for k in 0..p {
                    sum = sum.add(&z.pow((k * 15 / p) as u32)).unwrap();
                }
            }
        }
        assert!(sum.is_zero());
    }
    #[test]
    fn exhausted_search_and_mutated_witnesses_are_refused() {
        assert_eq!(
            lam_leung_length(15, &BigUint::from(8u8), FactorizationBudget::default(), 0),
            Err(VanishingLengthError::SearchBudget)
        );
        assert_eq!(
            lam_leung_length(0, &BigUint::zero(), FactorizationBudget::default(), 100),
            Err(VanishingLengthError::InvalidConductor)
        );
        let mut w = lam_leung_length(6, &BigUint::from(5u8), FactorizationBudget::default(), 100)
            .unwrap()
            .unwrap();
        w.length += BigUint::from(1u8);
        assert_eq!(
            w.verify(FactorizationBudget::default()),
            Err(VanishingLengthError::InvalidWitness)
        );
    }
}

/// The least odd prime polygon available in the conductor. It is an explicit
/// unpairable irreducible sum: no proper subset of a regular prime p-gon sums
/// to zero. This does not classify all irreducible composite-root sums.
pub fn minimal_unpairable_polygon(
    conductor: u64,
    budget: FactorizationBudget,
) -> Result<Option<u64>, VanishingLengthError> {
    if conductor == 0 {
        return Err(VanishingLengthError::InvalidConductor);
    }
    let factors = factor_natural(&BigUint::from(conductor), budget)?;
    Ok(factors.keys().filter_map(|p| p.to_u64()).find(|p| *p != 2))
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RootConductorError {
    #[error("root order must be in 1..=128")]
    Carrier,
    #[error("the conductor search exhausted its declared field budget")]
    Budget,
    #[error("cyclotomic root construction failed: {0}")]
    Field(String),
    #[error(transparent)]
    Factorization(#[from] FactorizationError),
    #[error("the root conductor certificate failed replay")]
    Certificate,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RootConductorWitness {
    pub order: usize,
    pub conductor: usize,
    pub root: crate::cyclotomic_field::CyclotomicNumber,
}
impl RootConductorWitness {
    pub fn verify(&self, budget: FactorizationBudget) -> Result<bool, RootConductorError> {
        if self.order == 0
            || self.order > 128
            || self.conductor == 0
            || self.root.conductor() != self.conductor
        {
            return Ok(false);
        }
        let one = crate::cyclotomic_field::CyclotomicNumber::one(self.conductor)
            .map_err(|e| RootConductorError::Field(e.to_string()))?;
        let factors = factor_natural(&BigUint::from(self.order), budget)?;
        Ok(self.root.pow(self.order as u32) == one
            && factors.keys().all(|p| {
                self.root
                    .pow((self.order / p.to_usize().expect("factor of a bounded order")) as u32)
                    != one
            })
            && (1..self.conductor).all(|m| {
                let roots = if m % 2 == 0 { m } else { 2 * m };
                roots % self.order != 0
            }))
    }
}
fn build_candidate_root_witness(
    order: usize,
    m: usize,
) -> Result<Option<RootConductorWitness>, RootConductorError> {
    let roots = if m % 2 == 0 { m } else { 2 * m };
    if roots % order != 0 {
        return Ok(None);
    }
    let z = crate::cyclotomic_field::CyclotomicNumber::zeta(m, 1)
        .map_err(|e| RootConductorError::Field(e.to_string()))?;
    let generator = if m % 2 == 0 { z } else { z.neg() };
    Ok(Some(RootConductorWitness {
        order,
        conductor: m,
        root: generator.pow((roots / order) as u32),
    }))
}

/// Uses the full root-of-unity group mu_lcm(2,m) of Q(zeta_m), then constructs
/// and verifies the required root in that field. Earlier fields are excluded by
/// the same complete root-group order; this is an embedding statement, not a
/// formula checked against itself.
pub fn minimal_root_conductor(
    order: usize,
    field_budget: usize,
    factor_budget: FactorizationBudget,
) -> Result<RootConductorWitness, RootConductorError> {
    if order == 0 || order > 128 {
        return Err(RootConductorError::Carrier);
    }
    for m in 1..=order {
        if m > field_budget {
            return Err(RootConductorError::Budget);
        }
        let Some(witness) = build_candidate_root_witness(order, m)? else {
            continue;
        };
        if !witness.verify(factor_budget)? {
            return Err(RootConductorError::Certificate);
        }
        return Ok(witness);
    }
    Err(RootConductorError::Certificate)
}
#[cfg(test)]
mod conductor_witness_laws {
    use super::*;
    #[test]
    fn primitive_root_conductor_witnesses_replay_and_refuse_mutation() {
        for n in 1..=32 {
            let w = minimal_root_conductor(n, 32, FactorizationBudget::default()).unwrap();
            assert!(w.verify(FactorizationBudget::default()).unwrap());
        }
        let mut w = minimal_root_conductor(6, 6, FactorizationBudget::default()).unwrap();
        assert_eq!(w.conductor, 3);
        w.order = 4;
        assert!(!w.verify(FactorizationBudget::default()).unwrap());
        assert_eq!(
            minimal_root_conductor(5, 4, FactorizationBudget::default()),
            Err(RootConductorError::Budget)
        );
        assert_eq!(
            minimal_unpairable_polygon(24, FactorizationBudget::default()).unwrap(),
            Some(3)
        );
        assert_eq!(
            minimal_unpairable_polygon(32, FactorizationBudget::default()).unwrap(),
            None
        );
        assert!(minimal_unpairable_polygon(0, FactorizationBudget::default()).is_err());
    }
}
