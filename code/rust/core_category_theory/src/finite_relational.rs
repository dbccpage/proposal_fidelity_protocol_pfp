//! Finite labelled relational systems: strong report-respecting bisimulation.
//!
//! Labels index declared successor sets, which may be empty or branching.
//! This is exact set-level coalgebra, not trace equivalence, a clock, HoTT
//! equivalence, or Kan fibrancy. Reports are caller-interned equality classes.
//! Finite labelled relational systems: strong report-respecting bisimulation.
//!
//! Labels index declared successor sets, which may be empty or branching.
//! This is exact set-level coalgebra, not trace equivalence, a clock, HoTT
//! equivalence, or Kan fibrancy. Reports are caller-interned equality classes.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_420195cc<T> {
    fn checked_invariant_420195cc(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_420195cc<T> for Option<T> {
    #[inline]
    fn checked_invariant_420195cc(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_420195cc<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_420195cc(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RelationalError {
    EmptyCarrier,
    TransitionShape,
    TransitionOutsideCarrier,
    DuplicateSuccessor,
    InvalidPartition,
    InvalidBoundedMap,
    RelationOutsideCarrier,
    StateOutsideCarrier,
}

impl std::fmt::Display for RelationalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for RelationalError {}

/// Least reflexive, transitive relation containing the supplied finite edges.
/// Empty carriers are allowed. Cycles identify preorder-equivalent states;
/// they do not establish antisymmetry on the original carrier.
/// Least reflexive, transitive relation containing the supplied finite edges.
/// Empty carriers are allowed. Cycles identify preorder-equivalent states;
/// they do not establish antisymmetry on the original carrier.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FinitePreorder {
    relation: Vec<Vec<bool>>,
}

fn close_transitively(relation: &mut [Vec<bool>]) {
    let n = relation.len();
    for via in 0..n {
        for x in 0..n {
            for y in 0..n {
                relation[x][y] |= relation[x][via] && relation[via][y];
            }
        }
    }
}

impl FinitePreorder {
    pub fn from_edges(size: usize, edges: &[(usize, usize)]) -> Result<Self, RelationalError> {
        if edges.iter().any(|&(x, y)| x >= size || y >= size) {
            return Err(RelationalError::RelationOutsideCarrier);
        }
        let mut relation = vec![vec![false; size]; size];
        for (i, row) in relation.iter_mut().enumerate() {
            row[i] = true;
        }
        for &(x, y) in edges {
            relation[x][y] = true;
        }
        close_transitively(&mut relation);
        Ok(Self { relation })
    }

    pub fn relation(&self) -> &[Vec<bool>] {
        &self.relation
    }

    pub fn leq(&self, x: usize, y: usize) -> Result<bool, RelationalError> {
        self.relation
            .get(x)
            .and_then(|row| row.get(y))
            .copied()
            .ok_or(RelationalError::StateOutsideCarrier)
    }

    pub fn is_partial_order(&self) -> bool {
        (0..self.relation.len())
            .all(|x| (0..x).all(|y| !(self.relation[x][y] && self.relation[y][x])))
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteRelational {
    reports: Vec<usize>,
    successors: Vec<Vec<Vec<usize>>>,
    label_count: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RelationalQuotient {
    pub partitions: Vec<Vec<usize>>,
    pub state_to_block: Vec<usize>,
    pub quotient: FiniteRelational,
}

/// Nonempty reachability classifies raw succession. Cycles forbid a strict
/// order on the original carrier. SCC condensation supplies a strict order
/// on a *different* carrier; internal transitions do not become strict edges.
/// Nonempty reachability classifies raw succession. Cycles forbid a strict
/// order on the original carrier. SCC condensation supplies a strict order
/// on a *different* carrier; internal transitions do not become strict edges.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SuccessionClassification {
    pub nonempty_reachability: Vec<Vec<bool>>,
    pub acyclic: bool,
    pub state_to_component: Vec<usize>,
    pub component_strict_order: Vec<Vec<bool>>,
}

fn normalize<T: Ord>(values: impl IntoIterator<Item = T>) -> Vec<usize> {
    let mut classes = BTreeMap::new();
    values
        .into_iter()
        .map(|value| {
            let fresh = classes.len();
            *classes.entry(value).or_insert(fresh)
        })
        .collect()
}

type BlockSignature = (usize, Vec<Vec<usize>>);

fn fill_blocks(next: &[usize], partition: &[usize], blocks: &mut Vec<usize>) {
    blocks.clear();
    blocks.extend(next.iter().map(|&state| partition[state]));
    blocks.sort_unstable();
    blocks.dedup();
}

fn intern_blocks(ids: &mut BTreeMap<BlockSignature, usize>, signature: &BlockSignature) -> usize {
    if let Some(&existing) = ids.get(signature) {
        return existing;
    }
    let fresh = ids.len();
    ids.insert(signature.clone(), fresh);
    fresh
}

fn factor_blocks(
    map: &[usize],
    stable: &[usize],
    target_size: usize,
) -> Result<Vec<usize>, RelationalError> {
    let mut factor = vec![None; target_size];
    for state in 0..map.len() {
        match factor[map[state]] {
            Some(block) if block != stable[state] => {
                return Err(RelationalError::InvalidBoundedMap)
            }
            _ => factor[map[state]] = Some(stable[state]),
        }
    }
    Ok(factor
        .into_iter()
        .map(|block| block.checked_invariant_420195cc("surjective map"))
        .collect())
}

impl FiniteRelational {
    pub fn new(
        reports: Vec<usize>,
        mut successors: Vec<Vec<Vec<usize>>>,
        label_count: usize,
    ) -> Result<Self, RelationalError> {
        let n = reports.len();
        if n == 0 {
            return Err(RelationalError::EmptyCarrier);
        }
        if successors.len() != n || successors.iter().any(|row| row.len() != label_count) {
            return Err(RelationalError::TransitionShape);
        }
        for next in successors.iter_mut().flatten() {
            if next.iter().any(|&state| state >= n) {
                return Err(RelationalError::TransitionOutsideCarrier);
            }
            next.sort_unstable();
            if next.windows(2).any(|pair| pair[0] == pair[1]) {
                return Err(RelationalError::DuplicateSuccessor);
            }
        }
        Ok(Self {
            reports,
            successors,
            label_count,
        })
    }

    pub fn reports(&self) -> &[usize] {
        &self.reports
    }
    pub fn successors(&self) -> &[Vec<Vec<usize>>] {
        &self.successors
    }
    pub fn label_count(&self) -> usize {
        self.label_count
    }
    pub fn state_count(&self) -> usize {
        self.reports.len()
    }

    fn block_successors(&self, state: usize, label: usize, partition: &[usize]) -> Vec<usize> {
        let mut blocks = Vec::new();
        fill_blocks(&self.successors[state][label], partition, &mut blocks);
        blocks
    }

    fn fill_signature(&self, state: usize, partition: &[usize], signature: &mut BlockSignature) {
        signature.0 = partition[state];
        for (label, blocks) in signature.1.iter_mut().enumerate() {
            fill_blocks(&self.successors[state][label], partition, blocks);
        }
    }

    fn refine(&self, partition: &[usize]) -> Vec<usize> {
        let mut signatures = BTreeMap::new();
        let mut scratch = (0, vec![Vec::new(); self.label_count]);
        (0..self.state_count())
            .map(|state| {
                self.fill_signature(state, partition, &mut scratch);
                intern_blocks(&mut signatures, &scratch)
            })
            .collect()
    }

    /// Equality partitions are bisimulations exactly when related states have
    /// equal reports and identical sets of successor blocks for every label.
    /// Equality partitions are bisimulations exactly when related states have
    /// equal reports and identical sets of successor blocks for every label.
    pub fn is_report_bisimulation_partition(&self, partition: &[usize]) -> bool {
        if partition.len() != self.state_count() {
            return false;
        }
        let refined = self.refine(partition);
        for x in 0..self.state_count() {
            for y in 0..x {
                if !self.pair_compatible(x, y, partition, &refined) {
                    return false;
                }
            }
        }
        true
    }

    fn pair_compatible(&self, x: usize, y: usize, partition: &[usize], refined: &[usize]) -> bool {
        partition[x] != partition[y]
            || (self.reports[x] == self.reports[y] && refined[x] == refined[y])
    }

    /// Every strict round splits at least one block. At most n-1 strict
    /// rounds occur; the repeated stable partition is not stored twice.
    /// Every strict round splits at least one block. At most n-1 strict
    /// rounds occur; the repeated stable partition is not stored twice.
    pub fn bisimulation_quotient(&self) -> RelationalQuotient {
        let mut partition = normalize(self.reports.iter().copied());
        let mut partitions = vec![partition.clone()];
        loop {
            let next = self.refine(&partition);
            if next == partition {
                break;
            }
            partition = next;
            partitions.push(partition.clone());
        }
        let blocks = 1 + partition.iter().copied().max().checked_invariant_420195cc("checked invariant");
        let mut representatives = vec![0; blocks];
        for state in (0..self.state_count()).rev() {
            representatives[partition[state]] = state;
        }
        let reports = representatives
            .iter()
            .map(|&state| self.reports[state])
            .collect();
        let successors = representatives
            .iter()
            .map(|&state| {
                (0..self.label_count)
                    .map(|label| self.block_successors(state, label, &partition))
                    .collect()
            })
            .collect();
        let quotient = FiniteRelational::new(reports, successors, self.label_count)
            .checked_invariant_420195cc("refinement constructs a nonempty well-typed quotient");
        RelationalQuotient {
            partitions,
            state_to_block: partition,
            quotient,
        }
    }

    /// Receipts are replayed from the actual system, including maximality:
    /// a merely stable but unnecessarily fine partition is rejected.
    /// Receipts are replayed from the actual system, including maximality:
    /// a merely stable but unnecessarily fine partition is rejected.
    pub fn verify_quotient(&self, receipt: &RelationalQuotient) -> bool {
        &self.bisimulation_quotient() == receipt
    }

    /// Unpointed behavioral classification. Report IDs and label positions
    /// must have the same interpretation in both inputs. Equality of the
    /// represented bisimulation classes is equivalent to isomorphism of
    /// their minimal quotients, without choosing an initial state.
    /// Unpointed behavioral classification. Report IDs and label positions
    /// must have the same interpretation in both inputs. Equality of the
    /// represented bisimulation classes is equivalent to isomorphism of
    /// their minimal quotients, without choosing an initial state.
    pub fn same_behavior_set(&self, other: &Self) -> bool {
        if self.label_count != other.label_count {
            return false;
        }
        let offset = self.state_count();
        let mut reports = self.reports.clone();
        reports.extend_from_slice(&other.reports);
        let mut successors = self.successors.clone();
        successors.extend(other.successors.iter().map(|row| {
            row.iter()
                .map(|next| next.iter().map(|state| state + offset).collect())
                .collect()
        }));
        let combined = Self::new(reports, successors, self.label_count)
            .checked_invariant_420195cc("disjoint union of validated finite relational systems");
        let classes = combined.bisimulation_quotient().state_to_block;
        classes[..offset].iter().copied().collect::<BTreeSet<_>>()
            == classes[offset..].iter().copied().collect::<BTreeSet<_>>()
    }

    /// A surjective bounded morphism has equal reports and exactly the
    /// target successor set as the image of each source successor set.
    /// Forward edge preservation alone does not suffice.
    /// A surjective bounded morphism has equal reports and exactly the
    /// target successor set as the image of each source successor set.
    /// Forward edge preservation alone does not suffice.
    pub fn factor_through_bounded_quotient(
        &self,
        target: &Self,
        map: &[usize],
    ) -> Result<Vec<usize>, RelationalError> {
        if map.len() != self.state_count()
            || target.label_count != self.label_count
            || map.iter().any(|&state| state >= target.state_count())
            || map.iter().copied().collect::<BTreeSet<_>>().len() != target.state_count()
        {
            return Err(RelationalError::InvalidBoundedMap);
        }
        let mut image = Vec::new();
        for state in 0..self.state_count() {
            if !self.bounded_state(target, map, state, &mut image) {
                return Err(RelationalError::InvalidBoundedMap);
            }
        }
        let stable = self.bisimulation_quotient().state_to_block;
        factor_blocks(map, &stable, target.state_count())
    }

    fn bounded_state(
        &self,
        target: &Self,
        map: &[usize],
        state: usize,
        image: &mut Vec<usize>,
    ) -> bool {
        if self.reports[state] != target.reports[map[state]] {
            return false;
        }
        for label in 0..self.label_count {
            fill_blocks(&self.successors[state][label], map, image);
            if *image != target.successors[map[state]][label] {
                return false;
            }
        }
        true
    }

    /// Classify the union of *declared* labelled transitions without selecting
    /// or orienting new transitions from reports. Index enumeration affects
    /// only identifiers, not reachability, SCCs, or the component strict order.
    /// Classify the union of *declared* labelled transitions without selecting
    /// or orienting new transitions from reports. Index enumeration affects
    /// only identifiers, not reachability, SCCs, or the component strict order.
    pub fn succession_classification(&self) -> SuccessionClassification {
        let n = self.state_count();
        let mut reach = vec![vec![false; n]; n];
        for (state, row) in self.successors.iter().enumerate() {
            for &next in row.iter().flatten() {
                reach[state][next] = true;
            }
        }
        close_transitively(&mut reach);
        let acyclic = (0..n).all(|state| !reach[state][state]);
        let mut component = vec![usize::MAX; n];
        let mut representatives = Vec::new();
        for x in 0..n {
            if component[x] != usize::MAX {
                continue;
            }
            let block = representatives.len();
            representatives.push(x);
            for y in x..n {
                if x == y || (reach[x][y] && reach[y][x]) {
                    component[y] = block;
                }
            }
        }
        let order = representatives
            .iter()
            .enumerate()
            .map(|(i, &x)| {
                representatives
                    .iter()
                    .enumerate()
                    .map(|(j, &y)| i != j && reach[x][y])
                    .collect()
            })
            .collect();
        SuccessionClassification {
            nonempty_reachability: reach,
            acyclic,
            state_to_component: component,
            component_strict_order: order,
        }
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_relational.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-relational:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn branching_deadlock_and_replay_boundaries() {
        let machine = FiniteRelational::new(
            vec![0, 0, 1],
            vec![vec![vec![1, 2]], vec![vec![2]], vec![vec![]]],
            1,
        )
        .unwrap();
        let quotient = machine.bisimulation_quotient();
        assert_eq!(quotient.state_to_block, vec![0, 1, 2]);
        assert!(machine.verify_quotient(&quotient));
        let mut forged = quotient.clone();
        forged.partitions.clear();
        assert!(!machine.verify_quotient(&forged));
        let blind =
            FiniteRelational::new(vec![0, 0], vec![vec![vec![]], vec![vec![1]]], 1).unwrap();
        assert_eq!(blind.bisimulation_quotient().state_to_block, vec![0, 1]);
        assert!(FiniteRelational::new(vec![0], vec![vec![vec![0, 0]]], 1).is_err());
    }

    #[test]
    fn bounded_maps_require_back_condition() {
        let source =
            FiniteRelational::new(vec![0, 0], vec![vec![vec![]], vec![vec![1]]], 1).unwrap();
        let target = FiniteRelational::new(vec![0], vec![vec![vec![0]]], 1).unwrap();
        assert!(source
            .factor_through_bounded_quotient(&target, &[0, 0])
            .is_err());
        let q = source.bisimulation_quotient();
        let factor = source
            .factor_through_bounded_quotient(&q.quotient, &q.state_to_block)
            .unwrap();
        assert_eq!(factor, vec![0, 1]);
    }

    #[test]
    fn fork_cycle_and_condensation() {
        let fork = FiniteRelational::new(
            vec![0; 3],
            vec![vec![vec![1, 2]], vec![vec![]], vec![vec![]]],
            1,
        )
        .unwrap();
        let s = fork.succession_classification();
        assert!(s.acyclic);
        assert!(!s.nonempty_reachability[1][2]);
        assert!(!s.nonempty_reachability[2][1]);
        let cycle = FiniteRelational::new(
            vec![0; 3],
            vec![vec![vec![1]], vec![vec![0, 2]], vec![vec![]]],
            1,
        )
        .unwrap();
        let s = cycle.succession_classification();
        assert!(!s.acyclic);
        assert_eq!(s.state_to_component, vec![0, 0, 1]);
        assert_eq!(
            s.component_strict_order,
            vec![vec![false, true], vec![false, false]]
        );
    }

    #[test]
    fn relabelling_changes_identifiers_but_not_classification() {
        let source = FiniteRelational::new(
            vec![0, 1, 1],
            vec![vec![vec![1, 2]], vec![vec![]], vec![vec![]]],
            1,
        )
        .unwrap();
        let renamed = FiniteRelational::new(
            vec![1, 0, 1],
            vec![vec![vec![]], vec![vec![0, 2]], vec![vec![]]],
            1,
        )
        .unwrap();
        assert!(source.same_behavior_set(&renamed));
        assert!(source.same_behavior_set(&source.bisimulation_quotient().quotient));
        let different = FiniteRelational::new(vec![0], vec![vec![vec![]]], 1).unwrap();
        assert!(!source.same_behavior_set(&different));
    }

    fn assert_greatest_bisimulation(
        machine: &FiniteRelational,
        state_to_block: &[usize],
        partitions: &[Vec<usize>],
    ) {
        for candidate in partitions {
            if !machine.is_report_bisimulation_partition(candidate) {
                continue;
            }
            for x in 0..3 {
                for y in 0..3 {
                    if candidate[x] == candidate[y] {
                        assert_eq!(state_to_block[x], state_to_block[y]);
                    }
                }
            }
        }
    }

    fn assert_strict_order(order: &[Vec<bool>]) {
        for x in 0..order.len() {
            assert!(!order[x][x]);
            for y in 0..order.len() {
                for z in 0..order.len() {
                    if order[x][y] && order[y][z] {
                        assert!(order[x][z]);
                    }
                }
            }
        }
    }

    #[test]
    fn exhaustive_three_state_relations_greatest_bisimulation() {
        let partitions = [
            vec![0, 0, 0],
            vec![0, 0, 1],
            vec![0, 1, 0],
            vec![0, 1, 1],
            vec![0, 1, 2],
        ];
        for reports in 0..8 {
            for edges in 0..512 {
                let machine = FiniteRelational::new(
                    (0..3).map(|x| (reports >> x) & 1).collect(),
                    (0..3)
                        .map(|x| vec![(0..3).filter(|y| edges & (1 << (3 * x + y)) != 0).collect()])
                        .collect(),
                    1,
                )
                .unwrap();
                let q = machine.bisimulation_quotient();
                assert!(q.partitions.len() <= 3);
                assert!(machine.is_report_bisimulation_partition(&q.state_to_block));
                assert!(machine.verify_quotient(&q));
                assert_greatest_bisimulation(&machine, &q.state_to_block, &partitions);
                let succession = machine.succession_classification();
                assert_eq!(
                    succession.acyclic,
                    q.quotient.succession_classification().acyclic
                );
                assert_strict_order(&succession.component_strict_order);
            }
        }
    }
}
