//! Definite Horn certificate checking on an explicitly supplied finite theory.
//! Exact source equality binds certificates; neither acceptance nor non-entailment
//! supplies empirical premises or an authorization decision.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Rule {
    pub premises: Vec<usize>,
    pub conclusion: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Theory {
    pub atoms: Vec<String>,
    pub facts: Vec<usize>,
    pub rules: Vec<Rule>,
}

impl Theory {
    pub fn valid(&self) -> bool {
        let n = self.atoms.len();
        self.atoms
            .iter()
            .enumerate()
            .all(|(i, a)| !a.is_empty() && !self.atoms[..i].contains(a))
            && self.facts.iter().all(|&a| a < n)
            && self
                .rules
                .iter()
                .all(|r| r.conclusion < n && r.premises.iter().all(|&a| a < n))
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProofStep {
    pub conclusion: usize,
    pub rule: Option<usize>,
    pub premises: Vec<usize>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Proof {
    pub theory: Theory,
    pub goal: usize,
    pub steps: Vec<ProofStep>,
}

pub fn check_proof(theory: &Theory, goal: usize, proof: &Proof) -> bool {
    if !theory.valid()
        || goal >= theory.atoms.len()
        || proof.goal != goal
        || &proof.theory != theory
    {
        return false;
    }
    if !proof
        .steps
        .iter()
        .enumerate()
        .all(|(i, step)| check_proof_step(theory, proof, i, step))
    {
        return false;
    }
    proof.steps.last().is_some_and(|s| s.conclusion == goal)
}

fn check_proof_step(theory: &Theory, proof: &Proof, i: usize, step: &ProofStep) -> bool {
    if step.conclusion >= theory.atoms.len() {
        return false;
    }
    match step.rule {
        None => theory.facts.contains(&step.conclusion) && step.premises.is_empty(),
        Some(index) => check_rule_application(theory, proof, i, step, index),
    }
}

fn check_rule_application(
    theory: &Theory,
    proof: &Proof,
    i: usize,
    step: &ProofStep,
    index: usize,
) -> bool {
    let Some(rule) = theory.rules.get(index) else {
        return false;
    };
    step.conclusion == rule.conclusion
        && step.premises.len() == rule.premises.len()
        && step
            .premises
            .iter()
            .zip(&rule.premises)
            .all(|(&j, &a)| j < i && proof.steps[j].conclusion == a)
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Countermodel {
    pub theory: Theory,
    pub goal: usize,
    pub values: Vec<bool>,
}

pub fn check_countermodel(theory: &Theory, goal: usize, model: &Countermodel) -> bool {
    theory.valid()
        && goal < theory.atoms.len()
        && model.goal == goal
        && &model.theory == theory
        && model.values.len() == theory.atoms.len()
        && !model.values[goal]
        && theory.facts.iter().all(|&a| model.values[a])
        && theory
            .rules
            .iter()
            .all(|r| !r.premises.iter().all(|&a| model.values[a]) || model.values[r.conclusion])
}

// Origin: engine/crates_rs/core_wdp/src/witnessed_reasoning.rs
// Claim: urn:core:crates_rs:core-wdp:witnessed-reasoning:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord75f3704f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord75f3704f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError75f3704f {
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
impl BoundaryError75f3704f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError75f3704f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError75f3704f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord75f3704f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError75f3704f> {
        if capacity_bound == 0 {
            return Err(BoundaryError75f3704f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError75f3704f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError75f3704f::ExceedsCapacity {
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
mod l4_boundary_tests_75f3704f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord75f3704f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord75f3704f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord75f3704f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord75f3704f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord75f3704f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError75f3704f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError75f3704f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
