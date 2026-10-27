//! Finite Wick contractions and vacuum multigraph symmetry factors.
//! Half-edges, loops and parallel edges are retained, with explicit work limits.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use num_bigint::BigUint;
use num_traits::One;
use core_combinatorics::enumeration::{factorial, permutations};
use core_number_theory::rational::Rational;
use std::collections::BTreeMap;
pub const AUTHORITY_FENCE: &str = "AuthorityEffect None; not PROVED; not GlobalGreen; bounded exact Wick and diagram combinatorics.";
/// Bound materialized contractions independently of a caller's work budget.
/// Counting remains available for the full declared twenty-leg carrier.
pub const MAX_WICK_PAIRINGS: usize = 1 << 16;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DiagramError {
    #[error("a Wick pairing requires an even number of legs at most 20")]
    Legs,
    #[error("diagram contraction or permutation count exceeds budget {limit}")]
    Budget { limit: usize },
    #[error("every half-edge must occur exactly once and vertex valences must be positive")]
    Pairing,
    #[error(transparent)]
    Combinatorics(#[from] core_combinatorics::enumeration::CombinatoricsError),
}
pub fn wick_pairing_count(legs: usize) -> Result<BigUint, DiagramError> {
    if legs % 2 != 0 || legs > 20 {
        return Err(DiagramError::Legs);
    }
    Ok((1..legs)
        .step_by(2)
        .fold(BigUint::one(), |v, i| v * BigUint::from(i)))
}
pub fn wick_pairings(legs: usize, budget: usize) -> Result<Vec<Vec<(usize, usize)>>, DiagramError> {
    let limit = budget.min(MAX_WICK_PAIRINGS);
    if wick_pairing_count(legs)? > BigUint::from(limit) {
        return Err(DiagramError::Budget { limit });
    }
    fn enumerate(
        remaining: &[usize],
        pairs: &mut Vec<(usize, usize)>,
        out: &mut Vec<Vec<(usize, usize)>>,
    ) {
        if remaining.is_empty() {
            out.push(pairs.clone());
            return;
        }
        let a = remaining[0];
        for j in 1..remaining.len() {
            pairs.push((a, remaining[j]));
            let rest: Vec<usize> = remaining
                .iter()
                .enumerate()
                .filter_map(|(i, &k)| (i != 0 && i != j).then_some(k))
                .collect();
            enumerate(&rest, pairs, out);
            pairs.pop();
        }
    }
    let mut result = Vec::new();
    enumerate(&(0..legs).collect::<Vec<_>>(), &mut Vec::new(), &mut result);
    Ok(result)
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FeynmanDiagram {
    valences: Vec<usize>,
    pairing: Vec<(usize, usize)>,
    adjacency: Vec<usize>,
}
impl FeynmanDiagram {
    fn validate_valences(valences: &[usize], pairing_len: usize) -> Result<usize, DiagramError> {
        if valences.is_empty() || valences.len() > 8 || valences.contains(&0) {
            return Err(DiagramError::Pairing);
        }
        let legs = valences
            .iter()
            .try_fold(0usize, |a, &b| a.checked_add(b))
            .ok_or(DiagramError::Legs)?;
        if legs > 20 || pairing_len.checked_mul(2) != Some(legs) {
            return Err(DiagramError::Pairing);
        }
        Ok(legs)
    }

    pub fn new(valences: Vec<usize>, pairing: Vec<(usize, usize)>) -> Result<Self, DiagramError> {
        let legs = Self::validate_valences(&valences, pairing.len())?;
        let mut seen = vec![false; legs];
        let vertices: Vec<usize> = valences
            .iter()
            .enumerate()
            .flat_map(|(v, &n)| std::iter::repeat_n(v, n))
            .collect();
        let n = valences.len();
        let mut adjacency = vec![0; n * n];
        for &(a, b) in &pairing {
            let invalid_pair = a >= legs || b >= legs || a == b;
            if invalid_pair || seen[a] || seen[b] {
                return Err(DiagramError::Pairing);
            }
            seen[a] = true;
            seen[b] = true;
            let (u, v) = (vertices[a], vertices[b]);
            adjacency[u * n + v] += 1;
            if u != v {
                adjacency[v * n + u] += 1;
            }
        }
        Ok(Self {
            valences,
            pairing,
            adjacency,
        })
    }
    pub fn pairing(&self) -> &[(usize, usize)] {
        &self.pairing
    }
    pub fn components(&self) -> usize {
        let n = self.valences.len();
        let mut seen = vec![false; n];
        let mut count = 0;
        for start in 0..n {
            if seen[start] {
                continue;
            }
            count += 1;
            let mut stack = vec![start];
            seen[start] = true;
            while let Some(v) = stack.pop() {
                for (w, marked) in seen.iter_mut().enumerate() {
                    if self.adjacency[v * n + w] != 0 && !*marked {
                        *marked = true;
                        stack.push(w);
                    }
                }
            }
        }
        count
    }
    pub fn is_connected(&self) -> bool {
        self.components() == 1
    }
    pub fn loops(&self) -> usize {
        self.pairing.len() + self.components() - self.valences.len()
    }
    pub fn canonical_form(&self, budget: usize) -> Result<Vec<usize>, DiagramError> {
        let n = self.valences.len();
        let mut best = self.adjacency.clone();
        for p in permutations(n, budget)? {
            let candidate: Vec<usize> = (0..n)
                .flat_map(|i| {
                    let p = &p;
                    (0..n).map(move |j| self.adjacency[p[i] * n + p[j]])
                })
                .collect();
            if candidate < best {
                best = candidate;
            }
        }
        Ok(best)
    }
    /// Vertex automorphisms times parallel-edge permutations times loop reversals.
    pub fn automorphism_count(&self, budget: usize) -> Result<BigUint, DiagramError> {
        let n = self.valences.len();
        let vertex_count = permutations(n, budget)?
            .iter()
            .filter(|p| {
                (0..n).all(|i| {
                    (0..n).all(|j| self.adjacency[i * n + j] == self.adjacency[p[i] * n + p[j]])
                })
            })
            .count();
        let mut count = BigUint::from(vertex_count);
        for i in 0..n {
            let loops = self.adjacency[i * n + i];
            count *= factorial(loops)? * (BigUint::one() << loops);
            for j in i + 1..n {
                count *= factorial(self.adjacency[i * n + j])?;
            }
        }
        Ok(count)
    }
    pub fn symmetry_factor(&self, budget: usize) -> Result<Rational, DiagramError> {
        Ok(Rational::new(
            1.into(),
            self.automorphism_count(budget)?.into(),
        ))
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
/// Canonical phi-four vacuum multigraphs through three vertices. Each pairing
/// is classified by its graph, and the returned symmetry factor is computed.
pub fn phi4_vacuum_diagrams(
    vertices: usize,
    budget: usize,
) -> Result<Vec<FeynmanDiagram>, DiagramError> {
    if vertices == 0 || vertices > 3 {
        return Err(DiagramError::Legs);
    }
    let mut diagrams = BTreeMap::new();
    for pairing in wick_pairings(4 * vertices, budget)? {
        let d = FeynmanDiagram::new(vec![4; vertices], pairing)?;
        let key = d.canonical_form(budget)?;
        diagrams.entry(key).or_insert(d);
    }
    Ok(diagrams.into_values().collect())
}
// Origin: engine/crates_rs/core_quantum_physics/src/feynman_diagram.rs
// Claim: urn:core:crates_rs:core-quantum-physics:feynman-diagram:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;
    #[test]
    fn wick_pairings_count_is_the_double_factorial() {
        for n in [0, 2, 4, 6, 8] {
            assert_eq!(
                BigUint::from(wick_pairings(n, 200).unwrap().len()),
                wick_pairing_count(n).unwrap()
            );
        }
        assert!(wick_pairings(20, 100).is_err());
        assert!(matches!(
            wick_pairings(20, usize::MAX),
            Err(DiagramError::Budget {
                limit: MAX_WICK_PAIRINGS
            })
        ));
        assert!(FeynmanDiagram::new(vec![4], vec![(0, 1), (1, 2)]).is_err());
    }
    #[test]
    fn vacuum_symmetry_factors_and_connected_sums_match_phi4_coefficients() {
        let one = phi4_vacuum_diagrams(1, 20000).unwrap();
        assert_eq!(one.len(), 1);
        assert_eq!(one[0].symmetry_factor(8).unwrap(), rq(1, 8));
        assert_eq!(one[0].loops(), 2);
        for (n, total, connected) in [(2, rq(35, 384), rq(1, 12)), (3, rq(385, 3072), rq(11, 96))] {
            let diagrams = phi4_vacuum_diagrams(n, 20000).unwrap();
            assert_eq!(
                diagrams
                    .iter()
                    .map(|d| d.symmetry_factor(8).unwrap())
                    .sum::<Rational>(),
                total
            );
            assert_eq!(
                diagrams
                    .iter()
                    .filter(|d| d.is_connected())
                    .map(|d| d.symmetry_factor(8).unwrap())
                    .sum::<Rational>(),
                connected
            );
        }
    }
}
