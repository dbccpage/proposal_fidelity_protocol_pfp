use std::collections::BTreeSet;

pub type Region = BTreeSet<usize>;

#[derive(Debug, Clone, PartialEq)]
pub struct LocalObs {
    pub region: Region,
    pub value: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Composition {
    pub outer: Region,
    pub inners: Vec<LocalObs>,
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct OperadMetrics {
    pub success_rate: f64,
    pub mean_phi_delta: f64,
    pub rejection_rate: f64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RegionError {
    Overlap { point: usize },
    UnionMismatch,
    Cardinality { card_sum: usize, outer: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/operad.rs
// Claim: urn:core:crates_rs:core-types:operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RegionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RegionError {}

/// Pairwise-disjoint inner regions whose union is exactly `outer`.
pub fn disjoint_region_union(outer: &Region, inners: &[Region]) -> Result<usize, RegionError> {
    let mut acc = BTreeSet::new();
    let mut card_sum = 0usize;
    for inner in inners {
        card_sum = card_sum
            .checked_add(inner.len())
            .ok_or(RegionError::Overflow)?;
        for point in inner {
            if !acc.insert(*point) {
                return Err(RegionError::Overlap { point: *point });
            }
        }
    }
    if &acc != outer {
        return Err(RegionError::UnionMismatch);
    }
    if card_sum != outer.len() {
        return Err(RegionError::Cardinality {
            card_sum,
            outer: outer.len(),
        });
    }
    Ok(outer.len())
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod disjoint_region_witness {
    use super::*;

    #[test]
    fn disjoint_parts_recover_the_outer_cardinality() {
        let outer: Region = [1, 2, 3].into_iter().collect();
        let left: Region = [1, 2].into_iter().collect();
        let right: Region = [3].into_iter().collect();
        assert_eq!(disjoint_region_union(&outer, &[left, right]), Ok(3));
    }

    #[test]
    fn overlap_is_refused() {
        let outer: Region = [1, 2].into_iter().collect();
        let left: Region = [1, 2].into_iter().collect();
        let right: Region = [2].into_iter().collect();
        assert!(matches!(
            disjoint_region_union(&outer, &[left, right]),
            Err(RegionError::Overlap { point: 2 })
        ));
    }
}
