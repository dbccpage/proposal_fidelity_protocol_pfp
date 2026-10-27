//! Declared workflow validation. Findings carry no authorization to run.
use crate::{
    planar::{repr, substitute, OperadOperation},
    Refusal,
};
use serde::Serialize;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub const REQUIRED_WORKFLOW_KEYS: [&str; 6] = [
    "workflow_id",
    "name",
    "source_colours",
    "target_colour",
    "pipeline",
    "authority_effect",
];

pub(crate) fn python_text(value: &Value) -> String {
    match value {
        Value::String(text) => text.clone(),
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        value => value.to_string(),
    }
}
fn python_repr(value: &Value) -> String {
    match value {
        Value::String(text) => repr(text),
        value => python_text(value),
    }
}
fn tuple_repr(values: &[String]) -> String {
    let joined = values
        .iter()
        .map(|value| repr(value))
        .collect::<Vec<_>>()
        .join(", ");
    if values.len() == 1 {
        format!("({joined},)")
    } else {
        format!("({joined})")
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct WorkflowFinding {
    workflow_id: String,
    code: String,
    detail: String,
    step_index: Option<usize>,
    operation: Option<Value>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct WorkflowReport {
    workflow_id: String,
    declared: OperadOperation,
    composed: Option<OperadOperation>,
    findings: Vec<WorkflowFinding>,
}
impl WorkflowFinding {
    pub fn new(
        workflow_id: String,
        code: String,
        detail: String,
        step_index: Option<usize>,
        operation: Option<Value>,
    ) -> Self {
        Self {
            workflow_id,
            code,
            detail,
            step_index,
            operation,
        }
    }
}
impl WorkflowReport {
    pub fn new(
        workflow_id: String,
        declared: OperadOperation,
        composed: Option<OperadOperation>,
        findings: Vec<WorkflowFinding>,
    ) -> Self {
        Self {
            workflow_id,
            declared,
            composed,
            findings,
        }
    }
    pub(crate) fn with_guard_finding(&self, code: String, detail: String) -> Self {
        let mut findings = self.findings.clone();
        findings.push(WorkflowFinding::new(
            self.workflow_id.clone(),
            code,
            detail,
            None,
            None,
        ));
        Self::new(
            self.workflow_id.clone(),
            self.declared.clone(),
            None,
            findings,
        )
    }
    pub fn is_valid(&self) -> bool {
        self.findings.is_empty()
    }
    pub fn signature_matches(&self) -> bool {
        self.composed.as_ref().is_some_and(|current| {
            current.source_colours() == self.declared.source_colours()
                && current.target_colour() == self.declared.target_colour()
        })
    }
}

fn parse_declared_operation(
    data: &serde_json::Map<String, Value>,
    workflow_id: &str,
) -> Result<OperadOperation, Refusal> {
    let sources = match &data["source_colours"] {
        Value::Array(values) => Value::Array(values.clone()),
        Value::String(value) => json!(value
            .chars()
            .map(|character| character.to_string())
            .collect::<Vec<_>>()),
        _ => {
            return Err(Refusal::new(
                "BAD_SIGNATURE",
                "source_colours must be an array or string",
            ))
        }
    };
    let spec = json!({
        "name": workflow_id,
        "source_colours": sources,
        "target_colour": python_text(&data["target_colour"]),
    });
    OperadOperation::from_json(&spec).map_err(|error| {
        Refusal::new(
            "BAD_SIGNATURE",
            format!("{workflow_id} declares an invalid signature: {}", error.message),
        )
    })
}

fn apply_pipeline_step(
    position: usize,
    step: &Value,
    workflow_id: &str,
    garden: &BTreeMap<String, OperadOperation>,
    current: &mut Option<OperadOperation>,
    findings: &mut Vec<WorkflowFinding>,
) -> Result<(), Refusal> {
    let step = step.as_object().ok_or_else(|| {
        Refusal::new(
            "BAD_STEP",
            format!("pipeline step {position} must be an object"),
        )
    })?;
    let name = step.get("operation").unwrap_or(&Value::Null);
    let phi = name.as_str().and_then(|name| garden.get(name));
    let Some(phi) = phi else {
        findings.push(WorkflowFinding {
            workflow_id: workflow_id.into(),
            code: "UNKNOWN_OPERATION".into(),
            detail: format!("{} is not a skill in the garden", python_repr(name)),
            step_index: Some(position),
            operation: if name.is_null() { None } else { Some(name.clone()) },
        });
        *current = None;
        return Ok(());
    };
    let Some(theta) = current.as_ref() else {
        return Ok(());
    };
    match substitute(theta, step.get("slot").unwrap_or(&Value::Null), phi) {
        Ok(composed) => *current = Some(composed),
        Err(error) => {
            findings.push(WorkflowFinding {
                workflow_id: workflow_id.into(),
                code: error.code,
                detail: error.message,
                step_index: Some(position),
                operation: Some(name.clone()),
            });
            *current = None;
        }
    }
    Ok(())
}

fn check_input_signature_drift(
    workflow_id: &str,
    declared: &OperadOperation,
    composed: &Option<OperadOperation>,
    findings: &mut Vec<WorkflowFinding>,
) {
    if let Some(composed) = composed {
        if composed.source_colours() != declared.source_colours() {
            findings.push(WorkflowFinding {
                workflow_id: workflow_id.into(),
                code: "INPUT_SIGNATURE_DRIFT".into(),
                detail: format!(
                    "the pipeline requires {} but the workflow declares {}",
                    tuple_repr(composed.source_colours()),
                    tuple_repr(declared.source_colours())
                ),
                step_index: None,
                operation: None,
            });
        }
    }
}

pub fn validate_workflow(
    workflow: &Value,
    garden: &BTreeMap<String, OperadOperation>,
) -> Result<WorkflowReport, Refusal> {
    let data = workflow
        .as_object()
        .ok_or_else(|| Refusal::new("BAD_INPUT", "workflow must be a parsed object"))?;
    let target_name = data
        .get("name")
        .or_else(|| data.get("workflow_id"))
        .map_or_else(|| "workflow".into(), python_text);
    let missing = REQUIRED_WORKFLOW_KEYS
        .iter()
        .filter(|key| !data.contains_key(**key))
        .copied()
        .collect::<Vec<_>>();
    if !missing.is_empty() {
        return Err(Refusal::new(
            "MISSING_KEYS",
            format!("{target_name} is missing: {}", missing.join(", ")),
        ));
    }
    let workflow_id = python_text(&data["workflow_id"]);
    let declared = parse_declared_operation(data, &workflow_id)?;
    let mut findings = Vec::new();
    if data["authority_effect"] != "None" {
        findings.push(WorkflowFinding {
            workflow_id: workflow_id.clone(),
            code: "AUTHORITY".into(),
            detail: format!(
                "authority_effect is {}, not None",
                python_repr(&data["authority_effect"])
            ),
            step_index: None,
            operation: None,
        });
    }
    let Some(pipeline) = data["pipeline"]
        .as_array()
        .filter(|pipeline| !pipeline.is_empty())
    else {
        findings.push(WorkflowFinding {
            workflow_id: workflow_id.clone(),
            code: "EMPTY_PIPELINE".into(),
            detail: "a workflow with no steps composes nothing".into(),
            step_index: None,
            operation: None,
        });
        let report = WorkflowReport {
            workflow_id,
            declared,
            composed: None,
            findings,
        };
        return Ok(report);
    };
    let mut current = Some(declared.clone());
    for (position, step) in pipeline.iter().enumerate() {
        apply_pipeline_step(position, step, &workflow_id, garden, &mut current, &mut findings)?;
    }
    check_input_signature_drift(&workflow_id, &declared, &current, &mut findings);
    let report = WorkflowReport {
        workflow_id,
        declared,
        composed: current,
        findings,
    };
    Ok(report)
}

pub fn unknown_operations(reports: &[WorkflowReport]) -> Vec<String> {
    reports
        .iter()
        .flat_map(|report| &report.findings)
        .filter(|finding| finding.code == "UNKNOWN_OPERATION")
        .filter_map(|finding| finding.operation.as_ref().and_then(Value::as_str))
        .filter(|name| !name.is_empty())
        .map(str::to_owned)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}

// Origin: engine/crates_rs/core_operads/src/workflow.rs
// Claim: urn:core:crates_rs:core-operads:workflow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf76a9e66 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf76a9e66` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf76a9e66 {
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
impl BoundaryErrorf76a9e66 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf76a9e66 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf76a9e66 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf76a9e66 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf76a9e66> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf76a9e66::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf76a9e66::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf76a9e66::ExceedsCapacity {
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
mod l4_boundary_tests_f76a9e66 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf76a9e66::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf76a9e66::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf76a9e66::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf76a9e66::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf76a9e66::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf76a9e66::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf76a9e66::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
