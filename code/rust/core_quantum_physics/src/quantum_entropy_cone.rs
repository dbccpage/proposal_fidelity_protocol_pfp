//! Exact entropy vectors and necessary quantum entropy inequalities. Monogamy
//! is an optional holographic constraint, not a universal quantum entropy law.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::stabilizer_code_distance::{StabilizerCode, StabilizerCodeError};
use num_traits::Zero;
use core_number_theory::rational::{rq, Rational};
use std::collections::BTreeSet;
pub const AUTHORITY_FENCE: &str = "AuthorityEffect None; not PROVED; not GlobalGreen; exact entropy vectors and finite inequality checks.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum EntropyConeError {
    #[error("entropy vectors require one through eight parties and all subset entries, with empty entropy zero")]
    Shape,
    #[error("regions overlap or contain repeated or out of range qubits")]
    Regions,
    #[error(transparent)]
    Stabilizer(#[from] StabilizerCodeError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EntropyVector {
    parties: usize,
    entropies: Vec<Rational>,
}
impl EntropyVector {
    pub fn new(parties: usize, entropies: Vec<Rational>) -> Result<Self, EntropyConeError> {
        if !(1..=8).contains(&parties)
            || entropies.len() != 1usize << parties
            || !entropies[0].is_zero()
        {
            return Err(EntropyConeError::Shape);
        }
        Ok(Self { parties, entropies })
    }
    pub fn parties(&self) -> usize {
        self.parties
    }
    pub fn entropies(&self) -> &[Rational] {
        &self.entropies
    }
    pub fn entropy(&self, subset: usize) -> Result<&Rational, EntropyConeError> {
        self.entropies.get(subset).ok_or(EntropyConeError::Shape)
    }
    pub fn from_stabilizer_state(code: &StabilizerCode) -> Result<Self, EntropyConeError> {
        if code.n() > 8 {
            return Err(EntropyConeError::Shape);
        }
        let regions: Vec<Vec<usize>> = (0..code.n()).map(|q| vec![q]).collect();
        Self::from_regions(code, &regions)
    }
    /// Parties may be multi-qubit disjoint regions, so toric states need only
    /// eight entropy computations for three regions, irrespective of lattice size.
    pub fn from_regions(
        code: &StabilizerCode,
        regions: &[Vec<usize>],
    ) -> Result<Self, EntropyConeError> {
        let parties = regions.len();
        if !(1..=8).contains(&parties) {
            return Err(EntropyConeError::Shape);
        }
        let mut seen = BTreeSet::new();
        for region in regions {
            for &q in region {
                if q >= code.n() || !seen.insert(q) {
                    return Err(EntropyConeError::Regions);
                }
            }
        }
        let mut entropies = Vec::with_capacity(1 << parties);
        for mask in 0..1usize << parties {
            let selected: Vec<usize> = regions
                .iter()
                .enumerate()
                .filter(|(i, _)| mask & (1usize << i) != 0)
                .flat_map(|(_, r)| r.iter().copied())
                .collect();
            entropies.push(Rational::from_integer(code.entropy(&selected)?.into()));
        }
        Self::new(parties, entropies)
    }
    fn sum_entropies(&self, masks: &[usize]) -> Result<Rational, EntropyConeError> {
        let mut total = Rational::from_integer(0.into());
        for &m in masks {
            total += self.entropy(m)?;
        }
        Ok(total)
    }

    pub fn tripartite_information(
        &self,
        a: usize,
        b: usize,
        c: usize,
    ) -> Result<Rational, EntropyConeError> {
        if ((a & b) | (a & c) | (b & c)) != 0 || [a, b, c].contains(&0) {
            return Err(EntropyConeError::Regions);
        }
        let positives = self.sum_entropies(&[a, b, c, a | b | c])?;
        let negatives = self.sum_entropies(&[a | b, a | c, b | c])?;
        Ok(positives - negatives)
    }
    pub fn purification_symmetry(&self) -> bool {
        let full = self.entropies.len() - 1;
        (0..=full).all(|a| self.entropies[a] == self.entropies[full ^ a])
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum EntropyLaw {
    Nonnegativity,
    Subadditivity,
    ArakiLieb,
    StrongSubadditivity,
    WeakMonotonicity,
    Monogamy,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EntropyInequality {
    pub law: EntropyLaw,
    pub coefficients: Vec<i64>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EntropyViolation {
    pub inequality: EntropyInequality,
    pub value: Rational,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuantumEntropyCone {
    parties: usize,
    inequalities: Vec<EntropyInequality>,
}
impl QuantumEntropyCone {
    pub fn necessary_quantum_inequalities(
        parties: usize,
        include_monogamy: bool,
    ) -> Result<Self, EntropyConeError> {
        if !(1..=6).contains(&parties) {
            return Err(EntropyConeError::Shape);
        }
        let count = 1usize << parties;
        let mut laws = BTreeSet::<(EntropyLaw, Vec<i64>)>::new();
        let mut add = |law, terms: &[(usize, i64)]| {
            let mut coefficients = vec![0; count];
            for &(mask, c) in terms {
                coefficients[mask] += c;
            }
            coefficients[0] = 0;
            laws.insert((law, coefficients));
        };
        for a in 1..count {
            add(EntropyLaw::Nonnegativity, &[(a, 1)]);
            for b in 1..count {
                if a & b != 0 {
                    continue;
                }
                add(EntropyLaw::Subadditivity, &[(a, 1), (b, 1), (a | b, -1)]);
                add(EntropyLaw::ArakiLieb, &[(a | b, 1), (a, -1), (b, 1)]);
                for c in 1..count {
                    if a & c != 0 || b & c != 0 {
                        continue;
                    }
                    add(
                        EntropyLaw::StrongSubadditivity,
                        &[(a | b, 1), (b | c, 1), (b, -1), (a | b | c, -1)],
                    );
                    add(
                        EntropyLaw::WeakMonotonicity,
                        &[(a | b, 1), (a | c, 1), (b, -1), (c, -1)],
                    );
                    if include_monogamy {
                        add(
                            EntropyLaw::Monogamy,
                            &[
                                (a | b, 1),
                                (a | c, 1),
                                (b | c, 1),
                                (a, -1),
                                (b, -1),
                                (c, -1),
                                (a | b | c, -1),
                            ],
                        );
                    }
                }
            }
        }
        Ok(Self {
            parties,
            inequalities: laws
                .into_iter()
                .map(|(law, coefficients)| EntropyInequality { law, coefficients })
                .collect(),
        })
    }
    pub fn inequalities(&self) -> &[EntropyInequality] {
        &self.inequalities
    }
    pub fn violations(
        &self,
        entropy: &EntropyVector,
    ) -> Result<Vec<EntropyViolation>, EntropyConeError> {
        if entropy.parties() != self.parties {
            return Err(EntropyConeError::Shape);
        }
        let mut violations = Vec::new();
        for inequality in &self.inequalities {
            let value = inequality
                .coefficients
                .iter()
                .zip(entropy.entropies())
                .map(|(&c, h)| Rational::from_integer(c.into()) * h)
                .sum::<Rational>();
            if value < rq(0, 1) {
                violations.push(EntropyViolation {
                    inequality: inequality.clone(),
                    value,
                });
            }
        }
        Ok(violations)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/quantum_entropy_cone.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quantum-entropy-cone:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::stabilizer_code_distance::pauli_string;
    #[test]
    fn ghz_four_obeys_quantum_inequalities_but_violates_monogamy() {
        let ghz = StabilizerCode::try_new(
            ["XXXX", "ZZII", "IZZI", "IIZZ"]
                .map(|w| pauli_string(w).unwrap())
                .to_vec(),
        )
        .unwrap();
        let h = EntropyVector::from_stabilizer_state(&ghz).unwrap();
        assert!(h.purification_symmetry());
        assert_eq!(h.tripartite_information(1, 2, 4).unwrap(), rq(1, 1));
        assert!(QuantumEntropyCone::necessary_quantum_inequalities(4, false)
            .unwrap()
            .violations(&h)
            .unwrap()
            .is_empty());
        let violations = QuantumEntropyCone::necessary_quantum_inequalities(4, true)
            .unwrap()
            .violations(&h)
            .unwrap();
        assert!(!violations.is_empty());
        assert!(violations
            .iter()
            .all(|v| v.inequality.law == EntropyLaw::Monogamy && v.value == rq(-1, 1)));
    }
    #[test]
    fn six_qubit_perfect_tensor_has_maximal_entropy_through_three_parties() {
        // Purify the [[5,1,3]] perfect code with one reference qubit.
        let state = StabilizerCode::try_new(
            ["XZZXII", "IXZZXI", "XIXZZI", "ZXIXZI", "XXXXXX", "ZZZZZZ"]
                .map(|w| pauli_string(w).unwrap())
                .to_vec(),
        )
        .unwrap();
        let h = EntropyVector::from_stabilizer_state(&state).unwrap();
        for mask in 0..64usize {
            let size = mask.count_ones() as usize;
            assert_eq!(
                h.entropy(mask).unwrap(),
                &Rational::from_integer(size.min(6 - size).into())
            );
        }
        assert_eq!(h.tripartite_information(1, 2, 4).unwrap(), rq(0, 1));
        assert!(h.purification_symmetry());
        assert!(QuantumEntropyCone::necessary_quantum_inequalities(6, false)
            .unwrap()
            .violations(&h)
            .unwrap()
            .is_empty());
    }
    #[test]
    fn bell_and_product_entropy_vectors_are_exact() {
        let bell = StabilizerCode::try_new(["XX", "ZZ"].map(|w| pauli_string(w).unwrap()).to_vec())
            .unwrap();
        assert_eq!(
            EntropyVector::from_stabilizer_state(&bell)
                .unwrap()
                .entropies(),
            &[rq(0, 1), rq(1, 1), rq(1, 1), rq(0, 1)]
        );
        let product =
            StabilizerCode::try_new(["ZI", "IZ"].map(|w| pauli_string(w).unwrap()).to_vec())
                .unwrap();
        assert!(EntropyVector::from_stabilizer_state(&product)
            .unwrap()
            .entropies()
            .iter()
            .all(Zero::is_zero));
    }
}
