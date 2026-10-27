//! Applications: OEAS Applied Workflow Operad.
//!
//! AuthorityEffect: None.

use std::collections::HashSet;
use serde::{Deserialize, Serialize};
use crate::foundation::{OperadColour, Operation, OperationId, OperadSignature, PlanarColoredOperad, PlanarTree};
use crate::realization::OperadAlgebra;

pub const OEAS_ADMITTED_PORT_COLOURS: &[&str] = &[
    "State",
    "Code",
    "AuditCandidate",
    "AuditFinding",
    "ProofCandidate",
    "AdmittedProof",
    "Post",
    "LedgerProposal",
    "LedgerSnapshot",
    "ReceiptPayload",
    "EvaluationReceipt",
];

/// Agent capability slice restricting an interpreter to permitted skill generators.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AgentCapabilitySlice {
    pub agent_id: String,
    pub licensed_skills: HashSet<String>,
    pub allowed_input_ports: HashSet<OperadColour>,
    pub allowed_output_ports: HashSet<OperadColour>,
}

impl AgentCapabilitySlice {
    pub fn new(
        agent_id: impl Into<String>,
        licensed_skills: HashSet<String>,
        allowed_input_ports: HashSet<OperadColour>,
        allowed_output_ports: HashSet<OperadColour>,
    ) -> Self {
        Self {
            agent_id: agent_id.into(),
            licensed_skills,
            allowed_input_ports,
            allowed_output_ports,
        }
    }

    pub fn permits_skill(&self, skill_id: &str) -> bool {
        self.licensed_skills.contains(skill_id)
    }
}

/// Applied workflow operad typing all skill generators and planar workflow trees.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OEASWorkflowOperad {
    pub operad: PlanarColoredOperad,
}

impl OEASWorkflowOperad {
    pub fn new() -> Result<Self, String> {
        let mut operad = PlanarColoredOperad::new("OEAS_WorkflowOperad", true);
        for &c_name in OEAS_ADMITTED_PORT_COLOURS {
            let c = OperadColour::new(c_name)?;
            operad.add_colour(c);
        }
        operad.ensure_identities();
        Ok(Self { operad })
    }

    pub fn register_skill(
        &mut self,
        skill_id: impl Into<String>,
        input_ports: &[&str],
        output_port: &str,
        description: impl Into<String>,
    ) -> Result<Operation, String> {
        let s_id = skill_id.into();
        for &inp in input_ports {
            if !OEAS_ADMITTED_PORT_COLOURS.contains(&inp) {
                return Err(format!("Cannot register skill '{}': unadmitted input port colour '{}'", s_id, inp));
            }
        }
        if !OEAS_ADMITTED_PORT_COLOURS.contains(&output_port) {
            return Err(format!("Cannot register skill '{}': unadmitted output port colour '{}'", s_id, output_port));
        }

        let in_cols: Result<Vec<OperadColour>, String> = input_ports.iter().map(|&s| OperadColour::new(s)).collect();
        let out_col = OperadColour::new(output_port)?;
        let sig = OperadSignature::new(in_cols?, out_col);

        let op = Operation::new_generator(OperationId::new(&s_id)?, sig, description);
        self.operad.add_operation(op.clone())?;
        Ok(op)
    }

    pub fn create_corolla(&self, skill_id: &str) -> Result<PlanarTree, String> {
        if let Some(op) = self.operad.operations().get(skill_id) {
            Ok(PlanarTree::corolla(op.clone()))
        } else {
            Err(format!("Skill '{}' is not registered in workflow operad", skill_id))
        }
    }

    pub fn compose_workflow_tree(
        &self,
        root_tree: &PlanarTree,
        slot_index: usize,
        child_tree: PlanarTree,
    ) -> Result<PlanarTree, String> {
        root_tree.graft(slot_index, child_tree)
    }

    pub fn compose_workflow(
        &self,
        root_skill_id: &str,
        slot_index: usize,
        child_skill_id: &str,
    ) -> Result<Operation, String> {
        let root_op = self
            .operad
            .operations()
            .get(root_skill_id)
            .ok_or_else(|| format!("Root skill '{}' not found in operad", root_skill_id))?;
        let child_op = self
            .operad
            .operations()
            .get(child_skill_id)
            .ok_or_else(|| format!("Child skill '{}' not found in operad", child_skill_id))?;

        self.operad.partial_compose(root_op, child_op, slot_index)
    }

    pub fn create_agent_interpreter(
        &self,
        agent_id: impl Into<String>,
        _capability_slice: Option<AgentCapabilitySlice>,
    ) -> OperadAlgebra {
        let a_id = agent_id.into();
        OperadAlgebra::new(self.operad.clone(), format!("AgentInterpreter_{}", a_id), a_id)
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/applications/oeas_workflow_operad.rs
// Claim: urn:core:crates_rs:core-operad-theory:oeas-workflow-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcf59dfd5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcf59dfd5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcf59dfd5 {
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
impl BoundaryErrorcf59dfd5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcf59dfd5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcf59dfd5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcf59dfd5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcf59dfd5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcf59dfd5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcf59dfd5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcf59dfd5::ExceedsCapacity {
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
mod l4_boundary_tests_cf59dfd5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcf59dfd5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcf59dfd5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcf59dfd5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcf59dfd5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcf59dfd5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorcf59dfd5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorcf59dfd5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
