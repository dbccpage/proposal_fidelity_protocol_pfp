use std::collections::HashSet;
use std::hash::Hash;

#[derive(Debug, Clone)]
pub struct CausalResidue<D> {
    pub sequence: Vec<D>,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct RegionId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DistinctionNode {
    pub id: usize,
    pub parent_region: Option<RegionId>,
}

#[derive(Debug, Clone)]
pub struct CausalPoset {
    pub region_list: Vec<RegionId>,
    pub inclusions: HashSet<(RegionId, RegionId)>,
    pub residue: CausalResidue<DistinctionNode>,
}

pub struct Site<T>(pub std::marker::PhantomData<T>);
pub struct CohomologyGroup(pub usize);
pub trait PresheafMarker {}

impl CausalPoset {
    pub fn as_site(&self) -> Site<Self> {
        Site(std::marker::PhantomData)
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_types/src/finite_causal_poset.rs
// Claim: urn:core:types:causal-poset:strict-order:v1
// AuthorityEffect: None

use std::collections::BTreeMap;

const MAX_REGIONS: usize = 128;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StrictOrderWitness {
    regions: usize,
    relations: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StrictOrderError {
    Empty,
    TooManyRegions { count: usize },
    DuplicateRegion { region: String },
    UnknownRegion { region: String },
    Reflexive { region: String },
    MissingComposite { left: String, mid: String, right: String },
}

// Origin: engine/crates_rs/core_types/src/finite_causal_poset.rs
// Claim: urn:core:crates_rs:core-types:finite-causal-poset:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StrictOrderError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StrictOrderError {}

impl CausalPoset {
    fn index_regions(&self) -> Result<BTreeMap<String, usize>, StrictOrderError> {
        let count = self.region_list.len();
        if count == 0 {
            return Err(StrictOrderError::Empty);
        }
        if count > MAX_REGIONS {
            return Err(StrictOrderError::TooManyRegions { count });
        }
        let mut index = BTreeMap::new();
        for (slot, region) in self.region_list.iter().enumerate() {
            if index.insert(region.0.clone(), slot).is_some() {
                return Err(StrictOrderError::DuplicateRegion { region: region.0.clone() });
            }
        }
        Ok(index)
    }

    fn build_relation_table(
        &self,
        index: &BTreeMap<String, usize>,
        count: usize,
    ) -> Result<(Vec<bool>, u64), StrictOrderError> {
        let mut related = vec![false; count.checked_mul(count).ok_or(StrictOrderError::TooManyRegions { count })?];
        let mut pairs: Vec<(&RegionId, &RegionId)> = self.inclusions.iter().map(|(left, right)| (left, right)).collect();
        pairs.sort_by(|left, right| (&left.0.0, &left.1.0).cmp(&(&right.0.0, &right.1.0)));
        let mut relations = 0u64;
        for (source, target) in pairs {
            let source_index = *index.get(&source.0).ok_or_else(|| StrictOrderError::UnknownRegion {
                region: source.0.clone(),
            })?;
            let target_index = *index.get(&target.0).ok_or_else(|| StrictOrderError::UnknownRegion {
                region: target.0.clone(),
            })?;
            if source_index == target_index {
                return Err(StrictOrderError::Reflexive { region: source.0.clone() });
            }
            let slot = source_index * count + target_index;
            if !related[slot] {
                related[slot] = true;
                relations = relations.checked_add(1).ok_or(StrictOrderError::TooManyRegions { count })?;
            }
        }
        Ok((related, relations))
    }

    fn verify_triple_transitivity(
        &self,
        related: &[bool],
        count: usize,
        left: usize,
        mid: usize,
        right: usize,
    ) -> Result<(), StrictOrderError> {
        if related[left * count + mid] && related[mid * count + right] && !related[left * count + right] {
            return Err(StrictOrderError::MissingComposite {
                left: self.region_list[left].0.clone(),
                mid: self.region_list[mid].0.clone(),
                right: self.region_list[right].0.clone(),
            });
        }
        Ok(())
    }

    pub fn try_strict_order(&self) -> Result<StrictOrderWitness, StrictOrderError> {
        let count = self.region_list.len();
        let index = self.index_regions()?;
        let (related, relations) = self.build_relation_table(&index, count)?;
        for left in 0..count {
            for mid in 0..count {
                for right in 0..count {
                    self.verify_triple_transitivity(&related, count, left, mid, right)?;
                }
            }
        }
        Ok(StrictOrderWitness { regions: count, relations })
    }
}

impl StrictOrderWitness {
    pub fn regions(&self) -> usize {
        self.regions
    }

    pub fn relations(&self) -> u64 {
        self.relations
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod strict_order_tests {
    use super::*;

    fn region(name: &str) -> RegionId {
        RegionId(name.to_string())
    }

    fn poset(names: &[&str], pairs: &[(&str, &str)]) -> CausalPoset {
        let mut inclusions = std::collections::HashSet::new();
        for (left, right) in pairs {
            inclusions.insert((region(left), region(right)));
        }
        CausalPoset {
            region_list: names.iter().map(|name| region(name)).collect(),
            inclusions,
            residue: CausalResidue { sequence: Vec::new() },
        }
    }

    #[test]
    fn a_chain_of_three_is_transitive() {
        let carrier = poset(&["a", "b", "c"], &[("a", "b"), ("b", "c"), ("a", "c")]);
        let witness = carrier.try_strict_order();
        assert!(matches!(witness, Ok(ref order) if order.regions() == 3 && order.relations() == 3));
    }

    #[test]
    fn refuses_a_missing_composite_and_a_loop() {
        let broken = poset(&["a", "b", "c"], &[("a", "b"), ("b", "c")]);
        assert!(matches!(broken.try_strict_order(), Err(StrictOrderError::MissingComposite { .. })));
        let looped = poset(&["a"], &[("a", "a")]);
        assert!(matches!(looped.try_strict_order(), Err(StrictOrderError::Reflexive { .. })));
    }
}
