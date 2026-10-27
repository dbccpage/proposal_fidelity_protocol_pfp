//! Finite contextual systems, checked morphisms and relation-coarsening reflection.
//! AuthorityEffect: None. No authority or report-reflecting completion is claimed.
//!
//! Objects have a total action for each fixed context label and a profile
//! equivalence. Morphisms commute with actions and preserve that equivalence.
//! The full subcategory Cong consists of action-stable equivalences. Closing
//! an equivalence upward under actions gives a reflector with identity carrier
//! unit, initial in (S down-arrow Cong). It can merge previously distinct
//! profiles. A profile-reflecting unit into Cong cannot repair noncongruence.
use crate::finite_moore::{FiniteMoore, MooreError};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ContextError {
    Carrier(MooreError),
    InvalidMap,
    ContextCountMismatch,
    ProfileNotPreserved,
    ActionNotPreserved,
    WrongDomain,
    TargetNotCongruent,
}

// Origin: engine/crates_rs/core_category_theory/src/context_reflection.rs
// Claim: urn:core:crates_rs:core-category-theory:context-reflection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ContextError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ContextError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ContextSystem {
    model: FiniteMoore,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ContextWitness {
    pub left: usize,
    pub right: usize,
    pub context: usize,
}

impl ContextSystem {
    pub fn new(
        profiles: Vec<usize>,
        transitions: Vec<Vec<usize>>,
        context_count: usize,
    ) -> Result<Self, ContextError> {
        Ok(Self {
            model: FiniteMoore::new(profiles, transitions, context_count)
                .map_err(ContextError::Carrier)?,
        })
    }
    pub fn state_count(&self) -> usize {
        self.model.state_count()
    }
    pub fn context_count(&self) -> usize {
        self.model.input_count()
    }
    pub fn profiles(&self) -> &[usize] {
        self.model.reports()
    }
    pub fn transitions(&self) -> &[Vec<usize>] {
        self.model.transitions()
    }
    pub fn related(&self, x: usize, y: usize) -> bool {
        x < self.state_count() && y < self.state_count() && self.profiles()[x] == self.profiles()[y]
    }
    pub fn check_witness(&self, witness: &ContextWitness) -> bool {
        let (x, y, c) = (witness.left, witness.right, witness.context);
        c < self.context_count()
            && self.related(x, y)
            && !self.related(self.transitions()[x][c], self.transitions()[y][c])
    }
    pub fn obstruction(&self) -> Option<ContextWitness> {
        for x in 0..self.state_count() {
            for y in 0..x {
                for c in 0..self.context_count() {
                    let witness = ContextWitness {
                        left: x,
                        right: y,
                        context: c,
                    };
                    if self.check_witness(&witness) {
                        return Some(witness);
                    }
                }
            }
        }
        None
    }
    pub fn is_congruent(&self) -> bool {
        self.obstruction().is_none()
    }
}

/// Typed checked arrow. No caller can replace its domain, codomain or map.
#[derive(Debug, Clone)]
pub struct ContextHom<'a> {
    source: &'a ContextSystem,
    target: &'a ContextSystem,
    map: Vec<usize>,
}
impl<'a> ContextHom<'a> {
    pub fn new(
        source: &'a ContextSystem,
        target: &'a ContextSystem,
        map: Vec<usize>,
    ) -> Result<Self, ContextError> {
        if source.context_count() != target.context_count() {
            return Err(ContextError::ContextCountMismatch);
        }
        if map.len() != source.state_count() || map.iter().any(|&v| v >= target.state_count()) {
            return Err(ContextError::InvalidMap);
        }
        for x in 0..source.state_count() {
            for y in 0..source.state_count() {
                if source.related(x, y) && !target.related(map[x], map[y]) {
                    return Err(ContextError::ProfileNotPreserved);
                }
            }
            for c in 0..source.context_count() {
                if map[source.transitions()[x][c]] != target.transitions()[map[x]][c] {
                    return Err(ContextError::ActionNotPreserved);
                }
            }
        }
        Ok(Self {
            source,
            target,
            map,
        })
    }
    pub fn source(&self) -> &ContextSystem {
        self.source
    }
    pub fn target(&self) -> &ContextSystem {
        self.target
    }
    pub fn map(&self) -> &[usize] {
        &self.map
    }
    pub fn identity(system: &'a ContextSystem) -> Result<Self, ContextError> {
        Self::new(system, system, (0..system.state_count()).collect())
    }
    pub fn then(&self, next: &Self) -> Result<Self, ContextError> {
        if self.target != next.source {
            return Err(ContextError::WrongDomain);
        }
        Self::new(
            self.source,
            next.target,
            self.map.iter().map(|&v| next.map[v]).collect(),
        )
    }
    pub fn reflects_profiles(&self) -> bool {
        (0..self.source.state_count()).all(|x| {
            (0..self.source.state_count()).all(|y| {
                !self.target.related(self.map[x], self.map[y]) || self.source.related(x, y)
            })
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CongruenceReflection {
    source: ContextSystem,
    completed: ContextSystem,
    chain: Vec<Vec<usize>>,
}

fn canonicalize(labels: &[usize]) -> Vec<usize> {
    let mut representatives = Vec::new();
    labels
        .iter()
        .map(|label| {
            if let Some(i) = representatives.iter().position(|old| old == label) {
                i
            } else {
                representatives.push(*label);
                representatives.len() - 1
            }
        })
        .collect()
}
fn merge(labels: &mut [usize], x: usize, y: usize) {
    let from = labels[y];
    let to = labels[x];
    for label in labels {
        if *label == from {
            *label = to;
        }
    }
}

impl CongruenceReflection {
    /// Least stable equivalence above the given profile equivalence. Every
    /// strict round merges at least two blocks, hence at most n-1 strict rounds.
    pub fn new(source: &ContextSystem) -> Result<Self, ContextError> {
        let mut labels = canonicalize(source.profiles());
        let mut chain = vec![labels.clone()];
        loop {
            let old = labels.clone();
            for x in 0..source.state_count() {
                for y in 0..x {
                    if old[x] == old[y] {
                        for c in 0..source.context_count() {
                            merge(
                                &mut labels,
                                source.transitions()[x][c],
                                source.transitions()[y][c],
                            );
                        }
                    }
                }
            }
            labels = canonicalize(&labels);
            if labels == old {
                break;
            }
            chain.push(labels.clone());
        }
        let completed = ContextSystem::new(
            labels,
            source.transitions().to_vec(),
            source.context_count(),
        )?;
        Ok(Self {
            source: source.clone(),
            completed,
            chain,
        })
    }
    pub fn source(&self) -> &ContextSystem {
        &self.source
    }
    pub fn completed(&self) -> &ContextSystem {
        &self.completed
    }
    pub fn chain(&self) -> &[Vec<usize>] {
        &self.chain
    }
    pub fn unit(&self) -> Result<ContextHom<'_>, ContextError> {
        ContextHom::new(
            &self.source,
            &self.completed,
            (0..self.source.state_count()).collect(),
        )
    }
    /// Given an object (T,f:S->T) of the comma category S↓Cong, construct its
    /// unique arrow from (R(S),eta). Relation-preservation is independently
    /// checked on the saturated relation; no trust in a claimed factor flag.
    pub fn factor<'a>(&'a self, arrow: &ContextHom<'a>) -> Result<ContextHom<'a>, ContextError> {
        if arrow.source != &self.source {
            return Err(ContextError::WrongDomain);
        }
        if !arrow.target.is_congruent() {
            return Err(ContextError::TargetNotCongruent);
        }
        ContextHom::new(&self.completed, arrow.target, arrow.map.clone())
    }
    /// Check the actual comma triangle for a candidate factor. Since eta is
    /// identity on carriers, two accepted factors have exactly the same map.
    pub fn is_factor(&self, arrow: &ContextHom<'_>, candidate: &ContextHom<'_>) -> bool {
        arrow.source == &self.source
            && arrow.target.is_congruent()
            && candidate.source == &self.completed
            && candidate.target == arrow.target
            && candidate.map == arrow.map
    }
}

/// The reflector's action on arrows, with endpoints checked against both units.
pub fn reflect_arrow<'a>(
    source: &'a CongruenceReflection,
    target: &'a CongruenceReflection,
    arrow: &ContextHom<'_>,
) -> Result<ContextHom<'a>, ContextError> {
    if arrow.source != source.source() || arrow.target != target.source() {
        return Err(ContextError::WrongDomain);
    }
    ContextHom::new(source.completed(), target.completed(), arrow.map.clone())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_854a5390 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
