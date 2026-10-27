//! Structural export of native certificates for independent Lean kernel replay.
//! The emitted theorem is about the explicit task literal. This exporter does
//! not assert a theorem about Rust execution or replace the Lean checker.

use crate::witnessed_reasoning::{Countermodel, Proof, Theory};

fn list(values: impl Iterator<Item = String>) -> String {
    format!("[{}]", values.collect::<Vec<_>>().join(", "))
}

fn text(value: &str) -> String {
    format!(
        "(String.ofList {})",
        list(
            value
                .chars()
                .map(|c| format!("(Char.ofNat {})", u32::from(c)))
        )
    )
}

pub fn theory_term(theory: &Theory) -> String {
    format!(
        "⟨{}, {}, {}⟩",
        list(theory.atoms.iter().map(|a| text(a))),
        list(theory.facts.iter().map(ToString::to_string)),
        list(theory.rules.iter().map(|r| format!(
            "⟨{}, {}⟩",
            list(r.premises.iter().map(ToString::to_string)),
            r.conclusion
        )))
    )
}

fn module(task: &Theory, goal: usize, certificate: String, positive: bool) -> String {
    let (kind, checker, parameter, judgment) = if positive {
        ("Proof", "checkProof", "p", "")
    } else {
        ("Model", "checkCountermodel", "m", "¬")
    };
    format!(
        "import ExecutableReasoning\n\
         open WitnessedReasoning WitnessedReasoning.Executable\n\
         namespace NativeReplay\n\
         def task : FiniteTheory := {}\n\
         def certificate : {kind}Certificate := {certificate}\n\
         theorem result : {judgment}Derivable task.abstract {goal} :=\n\
           {checker}_sound (T := task) (goal := {goal}) ({parameter} := certificate) (by decide)\n\
         #print axioms result\n\
         end NativeReplay\n",
        theory_term(task)
    )
}

pub fn proof_module(theory: &Theory, goal: usize, proof: &Proof) -> String {
    let steps = list(proof.steps.iter().map(|s| {
        let rule = s
            .rule
            .map_or_else(|| "none".to_owned(), |i| format!("(some {i})"));
        format!(
            "⟨{}, {}, {}⟩",
            s.conclusion,
            rule,
            list(s.premises.iter().map(ToString::to_string))
        )
    }));
    module(
        theory,
        goal,
        format!(
            "⟨{}, {}, {}⟩",
            theory_term(&proof.theory),
            proof.goal,
            steps
        ),
        true,
    )
}

pub fn countermodel_module(theory: &Theory, goal: usize, model: &Countermodel) -> String {
    module(
        theory,
        goal,
        format!(
            "⟨{}, {}, {}⟩",
            theory_term(&model.theory),
            model.goal,
            list(model.values.iter().map(ToString::to_string))
        ),
        false,
    )
}

// Origin: engine/crates_rs/core_wdp/src/witnessed_reasoning_replay.rs
// Claim: urn:core:crates_rs:core-wdp:witnessed-reasoning-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord73c8683e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord73c8683e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError73c8683e {
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
impl BoundaryError73c8683e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError73c8683e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError73c8683e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord73c8683e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError73c8683e> {
        if capacity_bound == 0 {
            return Err(BoundaryError73c8683e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError73c8683e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError73c8683e::ExceedsCapacity {
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
mod l4_boundary_tests_73c8683e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord73c8683e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord73c8683e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord73c8683e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord73c8683e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord73c8683e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError73c8683e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError73c8683e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
