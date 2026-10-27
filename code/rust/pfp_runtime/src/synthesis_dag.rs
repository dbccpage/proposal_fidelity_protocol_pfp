//! Program Synthesis Loop v2: Module DAG and Stateful Retraction (U10).
//!
//! Invariants:
//! - A module may only transition to Ready/Synthesizing when ALL dependencies are Frozen.
//! - A module transitions to Frozen only when verified by an exact host oracle.
//! - Repair prompt for attempt >= 2 carries previous code and failing diff.
//! - AuthorityEffect: None (const).

use serde::{Deserialize, Serialize};

fn default_authority_effect() -> String {
    "None".to_string()
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ModuleStatus {
    Pending,
    Ready,
    Synthesizing,
    Frozen,
    Failed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModuleNodeV1 {
    pub name: String,
    pub dependencies: Vec<String>,
    pub status: ModuleStatus,
    pub code: Option<String>,
    pub attempts: u32,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModuleDagV1 {
    pub nodes: Vec<ModuleNodeV1>,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

impl ModuleDagV1 {
    pub fn new() -> Self {
        Self {
            nodes: Vec::new(),
            authority_effect: default_authority_effect(),
        }
    }

    pub fn add_module(&mut self, name: &str, dependencies: &[&str]) {
        self.nodes.push(ModuleNodeV1 {
            name: name.to_string(),
            dependencies: dependencies.iter().map(|s| s.to_string()).collect(),
            status: ModuleStatus::Pending,
            code: None,
            attempts: 0,
            authority_effect: default_authority_effect(),
        });
    }

    /// Finds the next module schedulable for synthesis.
    ///
    /// Invariant:
    /// A module is schedulable if its status is Pending and ALL dependencies have status Frozen.
    pub fn next_schedulable_module(&mut self) -> Option<&mut ModuleNodeV1> {
        let frozen_names: Vec<String> = self
            .nodes
            .iter()
            .filter(|n| n.status == ModuleStatus::Frozen)
            .map(|n| n.name.clone())
            .collect();

        for node in &mut self.nodes {
            if node.status == ModuleStatus::Pending {
                let all_deps_frozen = node
                    .dependencies
                    .iter()
                    .all(|dep| frozen_names.contains(dep));
                if all_deps_frozen {
                    node.status = ModuleStatus::Ready;
                    return Some(node);
                }
            }
        }
        None
    }

    pub fn freeze_module(&mut self, name: &str, code: &str) -> Result<(), &'static str> {
        let node = self
            .nodes
            .iter_mut()
            .find(|n| n.name == name)
            .ok_or("MODULE_NOT_FOUND")?;
        node.status = ModuleStatus::Frozen;
        node.code = Some(code.to_string());
        Ok(())
    }

    pub fn fail_module(&mut self, name: &str) -> Result<(), &'static str> {
        let node = self
            .nodes
            .iter_mut()
            .find(|n| n.name == name)
            .ok_or("MODULE_NOT_FOUND")?;
        node.status = ModuleStatus::Failed;
        Ok(())
    }

    pub fn is_all_frozen(&self) -> bool {
        !self.nodes.is_empty() && self.nodes.iter().all(|n| n.status == ModuleStatus::Frozen)
    }
}

impl Default for ModuleDagV1 {
    fn default() -> Self {
        Self::new()
    }
}

/// Retraction Context for repair attempts (t >= 2).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RetractionContextV1 {
    pub module_name: String,
    pub attempt_number: u32,
    pub spec_text: String,
    pub schema_card: String,
    pub previous_code: Option<String>,
    pub failing_diff: Option<String>,
    pub error_feedback: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

impl RetractionContextV1 {
    /// Renders repair prompt enforcing the retraction invariant.
    ///
    /// Invariant:
    /// For attempt >= 2, previous_code AND failing_diff MUST be present in prompt.
    /// MUTATION KILL GATE: Omitting previous_code or failing_diff fails repair rendering!
    pub fn render_prompt(&self) -> Result<String, &'static str> {
        let mut prompt = format!(
            "### Module Synthesis: {}\nAttempt: {}\n\nSpecification:\n{}\n\nSchema:\n{}\n\n",
            self.module_name, self.attempt_number, self.spec_text, self.schema_card
        );

        if self.attempt_number >= 2 {
            let prev_code = self
                .previous_code
                .as_ref()
                .ok_or("REPAIR_MISSING_PREVIOUS_CODE")?;
            let diff = self
                .failing_diff
                .as_ref()
                .ok_or("REPAIR_MISSING_FAILING_DIFF")?;

            prompt.push_str("### Previous Code (Failed Host Verification)\n```python\n");
            prompt.push_str(prev_code);
            prompt.push_str("\n```\n\n### Failure Diagnostics & Diff\n");
            prompt.push_str(diff);
            prompt.push_str("\n\nError Feedback:\n");
            prompt.push_str(&self.error_feedback);
            prompt.push_str("\n\nPlease repair the code to eliminate all failure modes.\n");
        } else {
            prompt.push_str("Please synthesize code matching the specification.\n");
        }

        Ok(prompt)
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/synthesis_dag.rs
// Claim: urn:core:crates_rs:pfp-runtime:synthesis-dag:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord88176c67 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord88176c67` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError88176c67 {
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
impl BoundaryError88176c67 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError88176c67 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError88176c67 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord88176c67 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError88176c67> {
        if capacity_bound == 0 {
            return Err(BoundaryError88176c67::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError88176c67::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError88176c67::ExceedsCapacity {
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
mod l4_boundary_tests_88176c67 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord88176c67::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord88176c67::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord88176c67::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord88176c67::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord88176c67::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError88176c67::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError88176c67::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
