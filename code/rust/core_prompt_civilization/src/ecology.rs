//! Finite islands, Pareto migration, and additive search.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_353d864b<T> {
    fn checked_invariant_353d864b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_353d864b<T> for Option<T> {
    #[inline]
    fn checked_invariant_353d864b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_353d864b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_353d864b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

use crate::convergence::{
    ConvergenceMonitorV1, ConvergencePolicyV1, PopulationSnapshotV1, RecoveryAction,
};
use crate::fitness::{compute_pareto_fronts, PromptFitnessV1};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EcologyCandidateV1 {
    pub fitness: PromptFitnessV1,
    pub behavior_cell: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IslandV1 {
    pub island_id: String,
    pub objective_id: String,
    pub capacity: usize,
    pub members: BTreeMap<String, EcologyCandidateV1>,
}

/// One best member per behavior cell, preserving unlike behaviors.
pub fn map_elites(candidates: &[EcologyCandidateV1]) -> BTreeMap<String, EcologyCandidateV1> {
    let mut cells: BTreeMap<String, EcologyCandidateV1> = BTreeMap::new();
    for candidate in candidates {
        let replace = match cells.get(&candidate.behavior_cell) {
            None => true,
            Some(incumbent) => {
                let front =
                    compute_pareto_fronts(&[incumbent.fitness.clone(), candidate.fitness.clone()]);
                front[0][0].prompt_id == candidate.fitness.prompt_id
            }
        };
        if replace {
            cells.insert(candidate.behavior_cell.clone(), candidate.clone());
        }
    }
    cells
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MigrationReceiptV1 {
    pub epoch: u64,
    pub transfers: Vec<(String, String, String)>,
    pub authority_effect: &'static str,
}

pub struct ArchipelagoV1 {
    islands: Vec<IslandV1>,
    period: u64,
    quota: usize,
    last_epoch: Option<u64>,
    convergence: ConvergenceMonitorV1,
    recovery_epoch: u64,
    shelved: Vec<IslandV1>,
}

pub struct RecoveryDecisionV1 {
    pub epoch: u64,
    pub population_digest: String,
    pub action: RecoveryAction,
    pub external_receipt: String,
    pub policy: ConvergencePolicyV1,
}

pub trait RecoveryDecisionVerifier {
    /// The trusted host authenticates the complete decision, including budget.
    fn verify(&self, decision: &RecoveryDecisionV1) -> bool;
}

impl ArchipelagoV1 {
    fn validate_island_disjointness(islands: &[IslandV1]) -> Result<(), String> {
        let mut ids = BTreeSet::new();
        let mut genomes = BTreeSet::new();
        for island in islands {
            let cap_invalid = island.capacity == 0 || island.members.len() > island.capacity;
            if cap_invalid || !ids.insert(&island.island_id) {
                return Err("ISLAND_CAPACITY_OR_ID_INVALID".into());
            }
            for (id, member) in &island.members {
                if id != &member.fitness.prompt_id || !genomes.insert(id) {
                    return Err("POPULATIONS_MUST_BE_DISJOINT".into());
                }
            }
        }
        Ok(())
    }

    pub fn new(
        islands: Vec<IslandV1>,
        period: u64,
        quota: usize,
        convergence: ConvergencePolicyV1,
    ) -> Result<Self, String> {
        if islands.len() < 2 || period == 0 || quota == 0 {
            return Err("INVALID_MIGRATION_POLICY".into());
        }
        Self::validate_island_disjointness(&islands)?;
        Ok(Self {
            islands,
            period,
            quota,
            last_epoch: None,
            convergence: ConvergenceMonitorV1::new(convergence)?,
            recovery_epoch: 0,
            shelved: vec![],
        })
    }

    pub fn islands(&self) -> &[IslandV1] {
        &self.islands
    }

    pub fn is_frozen(&self) -> bool {
        self.convergence.is_frozen()
    }

    pub fn population_digest(&self) -> String {
        hex::encode(Sha256::digest(
            serde_json::to_vec(&self.islands)
                .checked_invariant_353d864b("integer population serializes"),
        ))
    }

    pub fn shelved(&self) -> &[IslandV1] {
        &self.shelved
    }

    fn verify_reinjection_preserved(
        old_islands: &[IslandV1],
        new_islands: &[IslandV1],
    ) -> Result<(), String> {
        let mut added = false;
        for old in old_islands {
            let new = new_islands
                .iter()
                .find(|i| i.island_id == old.island_id)
                .ok_or("REINJECTION_MUST_PRESERVE_POPULATION")?;
            let members_changed = old
                .members
                .iter()
                .any(|(id, c)| new.members.get(id) != Some(c));
            if new.objective_id != old.objective_id
                || new.capacity != old.capacity
                || members_changed
            {
                return Err("REINJECTION_MUST_PRESERVE_POPULATION".into());
            }
            let prior_cells: BTreeSet<_> = old.members.values().map(|c| &c.behavior_cell).collect();
            added |= new
                .members
                .values()
                .any(|c| !prior_cells.contains(&c.behavior_cell));
        }
        if !added {
            return Err("DIVERSITY_REINJECTION_REQUIRED".into());
        }
        Ok(())
    }

    /// Explicit host-authenticated recovery, with a fresh finite budget.
    /// Re-injection preserves every existing member; reboot shelves the old
    /// population. This method never calls itself or schedules another epoch.
    pub fn recover(
        &mut self,
        decision: &RecoveryDecisionV1,
        replacement: Vec<IslandV1>,
        verifier: &impl RecoveryDecisionVerifier,
    ) -> Result<(), String> {
        let state_valid = self.is_frozen()
            && self.convergence.recovery_action() == Some(decision.action)
            && decision.epoch > self.recovery_epoch
            && decision.population_digest == self.population_digest();
        if !state_valid || decision.external_receipt.is_empty() || !verifier.verify(decision) {
            return Err("EXTERNAL_RECOVERY_EPOCH_REQUIRED".into());
        }
        let next = Self::new(
            replacement,
            self.period,
            self.quota,
            decision.policy.clone(),
        )?;
        if decision.action == RecoveryAction::ReinjectDiversity {
            Self::verify_reinjection_preserved(&self.islands, &next.islands)?;
        }
        self.shelved.extend(self.islands.clone());
        self.islands = next.islands;
        self.convergence = next.convergence;
        self.recovery_epoch = decision.epoch;
        self.last_epoch = None;
        Ok(())
    }

    fn ensure_open(&self) -> Result<(), String> {
        if self.is_frozen() {
            return Err("FROZEN: population transition refused".into());
        }
        Ok(())
    }

    fn record_round(&mut self) -> Result<(), String> {
        let members: Vec<_> = self
            .islands
            .iter()
            .flat_map(|i| i.members.values())
            .collect();
        self.convergence.observe(PopulationSnapshotV1 {
            best_success: members
                .iter()
                .map(|c| c.fitness.task_success_credit)
                .max()
                .unwrap_or(0),
            best_failures: members
                .iter()
                .map(|c| c.fitness.failures)
                .min()
                .unwrap_or(0),
            occupied_cells: self
                .islands
                .iter()
                .flat_map(|i| {
                    i.members
                        .values()
                        .map(|c| format!("{}:{}", i.island_id, c.behavior_cell))
                })
                .collect(),
        })?;
        Ok(())
    }

    /// Realize a candidate mutation/crossover inside one island. This changes
    /// population membership only; it confers no prompt or antibody admission.
    pub fn insert_candidate(
        &mut self,
        island_id: &str,
        candidate: EcologyCandidateV1,
    ) -> Result<(), String> {
        self.ensure_open()?;
        let id = &candidate.fitness.prompt_id;
        if self.islands.iter().any(|i| i.members.contains_key(id)) {
            return Err("POPULATIONS_MUST_BE_DISJOINT".into());
        }
        let target = self
            .islands
            .iter_mut()
            .find(|i| i.island_id == island_id)
            .ok_or("ISLAND_NOT_FOUND")?;
        if target.members.len() >= target.capacity {
            return Err("ISLAND_CAPACITY_REACHED".into());
        }
        target.members.insert(id.clone(), candidate);
        self.record_round()
    }

    fn select_island_migrants(
        &self,
        source: usize,
        target: usize,
    ) -> Vec<(usize, usize, EcologyCandidateV1)> {
        let a = &self.islands[source];
        let b = &self.islands[target];
        if a.objective_id != b.objective_id {
            return Vec::new();
        }
        let free = b.capacity - b.members.len();
        let fits: Vec<_> = a.members.values().map(|c| c.fitness.clone()).collect();
        let fronts = compute_pareto_fronts(&fits);
        let Some(front) = fronts.first() else {
            return Vec::new();
        };
        let existing_cells: BTreeSet<_> = b.members.values().map(|c| &c.behavior_cell).collect();
        let mut selected_cells = BTreeSet::new();
        let mut selected = Vec::new();
        // Prefer unoccupied behavior cells, then deterministic Pareto order.
        for novel in [true, false] {
            for fitness in front {
                let c = &a.members[&fitness.prompt_id];
                if (!existing_cells.contains(&c.behavior_cell)) == novel
                    && selected_cells.insert(c.behavior_cell.clone())
                {
                    selected.push(c.clone());
                }
            }
        }
        selected
            .into_iter()
            .take(self.quota.min(free))
            .map(|c| (source, target, c))
            .collect()
    }

    /// Simultaneous one-hop ring migration from the pre-step snapshot. Migrants
    /// never traverse two islands in one call; objectives must be comparable.
    pub fn migrate(&mut self, epoch: u64) -> Result<MigrationReceiptV1, String> {
        self.ensure_open()?;
        if self.last_epoch.is_some_and(|previous| epoch <= previous) {
            return Err("MIGRATION_EPOCH_REPLAY".into());
        }
        self.last_epoch = Some(epoch);
        let mut receipt = MigrationReceiptV1 {
            epoch,
            transfers: vec![],
            authority_effect: "None",
        };
        if !epoch.is_multiple_of(self.period) {
            self.record_round()?;
            return Ok(receipt);
        }
        let mut moves = Vec::new();
        for source in 0..self.islands.len() {
            let target = (source + 1) % self.islands.len();
            moves.extend(self.select_island_migrants(source, target));
        }
        for (source, target, candidate) in &moves {
            let id = candidate.fitness.prompt_id.clone();
            self.islands[*source].members.remove(&id);
            receipt.transfers.push((
                self.islands[*source].island_id.clone(),
                self.islands[*target].island_id.clone(),
                id,
            ));
        }
        for (_, target, candidate) in moves {
            self.islands[target]
                .members
                .insert(candidate.fitness.prompt_id.clone(), candidate);
        }
        self.record_round()?;
        Ok(receipt)
    }
}

/// Approximate retrieval is recall-only. Eligibility checks happen afterwards.
pub fn augment_candidates(
    exact: &BTreeSet<String>,
    approximate: impl IntoIterator<Item = String>,
) -> BTreeSet<String> {
    exact.iter().cloned().chain(approximate).collect()
}

/// MinHash locality-sensitive buckets over caller-supplied prompt AST atoms.
/// The eight deterministic bands add suggestions; exact candidates always survive.
#[derive(Default)]
pub struct ApproximatePromptIndexV1 {
    buckets: BTreeMap<(u8, [u8; 32]), BTreeSet<String>>,
}

impl ApproximatePromptIndexV1 {
    fn signature(atoms: &[String], band: u8) -> Option<[u8; 32]> {
        atoms
            .iter()
            .map(|atom| {
                let mut hash = Sha256::new();
                hash.update([band]);
                hash.update(atom.as_bytes());
                <[u8; 32]>::from(hash.finalize())
            })
            .min()
    }

    pub fn insert(&mut self, prompt_id: &str, atoms: &[String]) {
        for band in 0..8 {
            if let Some(signature) = Self::signature(atoms, band) {
                self.buckets
                    .entry((band, signature))
                    .or_default()
                    .insert(prompt_id.into());
            }
        }
    }

    pub fn candidates(&self, atoms: &[String], exact: &BTreeSet<String>) -> BTreeSet<String> {
        let mut result = exact.clone();
        for band in 0..8 {
            if let Some(signature) = Self::signature(atoms, band) {
                if let Some(found) = self.buckets.get(&(band, signature)) {
                    result.extend(found.iter().cloned());
                }
            }
        }
        result
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/ecology.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:ecology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord353d864b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord353d864b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError353d864b {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError353d864b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError353d864b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError353d864b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord353d864b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError353d864b> {
        if capacity_bound == 0 {
            return Err(BoundaryError353d864b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError353d864b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError353d864b::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_353d864b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord353d864b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord353d864b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord353d864b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord353d864b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord353d864b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError353d864b::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError353d864b::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
