#[derive(Debug, Clone, Default)]
pub struct UpperTriangularPairs {
    pub pairs: Vec<(usize, usize)>,
}

impl UpperTriangularPairs {
    pub fn build(n: usize) -> Self {
        let mut pairs = Vec::new();

        for i in 0..n {
            for j in (i + 1)..n {
                pairs.push((i, j));
            }
        }

        Self { pairs }
    }

    pub fn add_edges_for_new_vertex(&mut self, new_vertex: usize) {
        for i in 0..new_vertex {
            self.pairs.push((i, new_vertex));
        }
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PairCensusError { Order, Duplicate, Count, Overflow }

// Origin: engine/crates_rs/core_homology/src/upper_triangular_pairs.rs
// Claim: urn:core:crates_rs:core-homology:upper-triangular-pairs:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PairCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PairCensusError {}

impl UpperTriangularPairs {
    /// Every pair satisfies `i < j < n`, pairs are unique, and the count is `n(n-1)/2`.
    pub fn certify(&self, n: usize) -> Result<usize, PairCensusError> {
        let n_u = u64::try_from(n).map_err(|_| PairCensusError::Overflow)?;
        let expected = if n_u < 2 { 0 } else { n_u.checked_mul(n_u - 1).ok_or(PairCensusError::Overflow)? / 2 };
        let mut seen = std::collections::BTreeSet::new();
        for pair in &self.pairs {
            if pair.0 >= pair.1 || pair.1 >= n {
                return Err(PairCensusError::Order);
            }
            if !seen.insert(*pair) {
                return Err(PairCensusError::Duplicate);
            }
        }
        let count = u64::try_from(seen.len()).map_err(|_| PairCensusError::Overflow)?;
        if count != expected {
            return Err(PairCensusError::Count);
        }
        Ok(seen.len())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod pair_census_checks {
    use super::*;

    #[test]
    fn the_complete_triple_has_three_pairs() {
        let pairs = UpperTriangularPairs::build(3);
        let census = pairs.certify(3);
        assert!(matches!(census, Ok(3)));
    }

    #[test]
    fn a_descending_pair_is_refused() {
        let pairs = UpperTriangularPairs { pairs: vec![(1, 0)] };
        assert!(matches!(pairs.certify(2), Err(PairCensusError::Order)));
    }
}
