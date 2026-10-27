
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e914e36b<T> {
    fn checked_invariant_e914e36b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e914e36b<T> for Option<T> {
    #[inline]
    fn checked_invariant_e914e36b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e914e36b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e914e36b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::{
    canonical_json_bytes, require_name, require_nonnegative, FoundationError, FoundationErrorCode,
};
use num_rational::BigRational;
use serde_json::Value;
use std::collections::BTreeSet;
/// The explicit structural difference carried by one DDA event.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct StructureDelta {
    added: BTreeSet<String>,
    removed: BTreeSet<String>,
}

impl StructureDelta {
    pub fn new(added: Vec<String>, removed: Vec<String>) -> Result<Self, FoundationError> {
        let mut added_set = BTreeSet::new();
        for item in added {
            require_name(&item, "added structure identity")?;
            if !added_set.insert(item) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "added structure identities must be unique",
                ));
            }
        }
        let mut removed_set = BTreeSet::new();
        for item in removed {
            require_name(&item, "removed structure identity")?;
            if !removed_set.insert(item) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "removed structure identities must be unique",
                ));
            }
        }
        if added_set.iter().any(|item| removed_set.contains(item)) {
            return Err(FoundationError::new(
                FoundationErrorCode::DuplicateIdentity,
                "a structure identity cannot be both added and removed",
            ));
        }
        Ok(Self {
            added: added_set,
            removed: removed_set,
        })
    }

    pub fn same_context() -> Self {
        Self::default()
    }

    pub fn added(&self) -> &BTreeSet<String> {
        &self.added
    }

    pub fn removed(&self) -> &BTreeSet<String> {
        &self.removed
    }

    pub fn is_same_context(&self) -> bool {
        self.added.is_empty() && self.removed.is_empty()
    }
}

/// An explicitly declared information loss.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LossRecord {
    field: String,
    reason: String,
}

impl LossRecord {
    pub fn new(
        field: impl Into<String>,
        reason: impl Into<String>,
    ) -> Result<Self, FoundationError> {
        let field = field.into();
        let reason = reason.into();
        require_name(&field, "loss field")?;
        require_name(&reason, "loss reason")?;
        Ok(Self { field, reason })
    }

    pub fn field(&self) -> &str {
        &self.field
    }

    pub fn reason(&self) -> &str {
        &self.reason
    }
}

type ProjectionFunction<S> = dyn Fn(&S) -> Result<Value, String> + Send + Sync;

/// A named state projection used to recompute an invariant on both endpoints.
pub struct InvariantProjection<S> {
    name: String,
    project: Box<ProjectionFunction<S>>,
}

impl<S> InvariantProjection<S> {
    pub fn new<F>(name: impl Into<String>, project: F) -> Result<Self, FoundationError>
    where
        F: Fn(&S) -> Result<Value, String> + Send + Sync + 'static,
    {
        let name = name.into();
        require_name(&name, "protected invariant identity")?;
        Ok(Self {
            name,
            project: Box::new(project),
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct ProtectedInvariantWitness {
    name: String,
    canonical_value: Vec<u8>,
}

/// Complete input required to record one generic exact DDA event.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DdaEventDraft<S> {
    pub event_id: String,
    pub contract_id: String,
    pub task_id: String,
    pub source_id: String,
    pub before: S,
    pub operation_id: String,
    pub parameters: Value,
    pub after: S,
    pub obstruction_before: BigRational,
    pub obstruction_after: BigRational,
    pub structure_delta: StructureDelta,
    pub losses: Vec<LossRecord>,
    pub parent_event_id: Option<String>,
}

/// One checked DDA event over an exact state type. `S: Eq` deliberately
/// excludes standard floating-point states.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DdaEvent<S> {
    event_id: String,
    contract_id: String,
    task_id: String,
    source_id: String,
    before: S,
    operation_id: String,
    parameters: Value,
    after: S,
    obstruction_before: BigRational,
    obstruction_after: BigRational,
    structure_delta: StructureDelta,
    protected_invariants: Vec<ProtectedInvariantWitness>,
    losses: Vec<LossRecord>,
    parent_event_id: Option<String>,
}

impl<S> DdaEvent<S>
where
    S: Clone + Eq,
{
    fn validate_draft_identities(draft: &DdaEventDraft<S>) -> Result<(), FoundationError> {
        for (value, label) in [
            (&draft.event_id, "DDA event identity"),
            (&draft.contract_id, "DDA contract identity"),
            (&draft.task_id, "DDA task identity"),
            (&draft.source_id, "DDA source boundary"),
            (&draft.operation_id, "DDA operation identity"),
        ] {
            require_name(value, label)?;
        }
        if let Some(parent) = &draft.parent_event_id {
            require_name(parent, "DDA parent event identity")?;
        }
        canonical_json_bytes(&draft.parameters)?;
        require_nonnegative(&draft.obstruction_before, "obstruction before")?;
        require_nonnegative(&draft.obstruction_after, "obstruction after")?;
        Ok(())
    }

    fn evaluate_protected_projection(
        projection: &InvariantProjection<S>,
        before: &S,
        after: &S,
    ) -> Result<ProtectedInvariantWitness, FoundationError> {
        let before_value = (projection.project)(before).map_err(|message| {
            FoundationError::new(
                FoundationErrorCode::ProjectionFailed,
                format!(
                    "protected projection {:?} failed: {message}",
                    projection.name
                ),
            )
        })?;
        let after_value = (projection.project)(after).map_err(|message| {
            FoundationError::new(
                FoundationErrorCode::ProjectionFailed,
                format!(
                    "protected projection {:?} failed: {message}",
                    projection.name
                ),
            )
        })?;
        let before_bytes = canonical_json_bytes(&before_value)?;
        let after_bytes = canonical_json_bytes(&after_value)?;
        if before_bytes != after_bytes {
            return Err(FoundationError::new(
                FoundationErrorCode::ProtectedInvariantChanged,
                format!("protected invariant {:?} changed", projection.name),
            ));
        }
        Ok(ProtectedInvariantWitness {
            name: projection.name.clone(),
            canonical_value: before_bytes,
        })
    }

    fn verify_losses_and_removals(
        losses: &[LossRecord],
        removed: &BTreeSet<String>,
        protected_names: &BTreeSet<String>,
    ) -> Result<(), FoundationError> {
        let mut lost_fields = BTreeSet::new();
        for loss in losses {
            if !lost_fields.insert(loss.field.clone()) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "loss fields must be unique",
                ));
            }
            if protected_names.contains(&loss.field) {
                return Err(FoundationError::new(
                    FoundationErrorCode::ProtectedLoss,
                    format!("protected invariant {:?} cannot be lost", loss.field),
                ));
            }
        }
        if let Some(removed_item) = removed.iter().find(|item| protected_names.contains(*item)) {
            return Err(FoundationError::new(
                FoundationErrorCode::ProtectedLoss,
                format!("protected invariant {removed_item:?} cannot be removed"),
            ));
        }
        Ok(())
    }

    pub fn record(
        draft: DdaEventDraft<S>,
        projections: &[InvariantProjection<S>],
    ) -> Result<Self, FoundationError> {
        Self::validate_draft_identities(&draft)?;

        let mut protected_names = BTreeSet::new();
        let mut protected_invariants = Vec::with_capacity(projections.len());
        for projection in projections {
            if !protected_names.insert(projection.name.clone()) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "protected invariant identities must be unique",
                ));
            }
            protected_invariants.push(Self::evaluate_protected_projection(
                projection,
                &draft.before,
                &draft.after,
            )?);
        }

        Self::verify_losses_and_removals(
            &draft.losses,
            &draft.structure_delta.removed,
            &protected_names,
        )?;

        Ok(Self {
            event_id: draft.event_id,
            contract_id: draft.contract_id,
            task_id: draft.task_id,
            source_id: draft.source_id,
            before: draft.before,
            operation_id: draft.operation_id,
            parameters: draft.parameters,
            after: draft.after,
            obstruction_before: draft.obstruction_before,
            obstruction_after: draft.obstruction_after,
            structure_delta: draft.structure_delta,
            protected_invariants,
            losses: draft.losses,
            parent_event_id: draft.parent_event_id,
        })
    }

    pub fn event_id(&self) -> &str {
        &self.event_id
    }

    pub fn contract_id(&self) -> &str {
        &self.contract_id
    }

    pub fn task_id(&self) -> &str {
        &self.task_id
    }

    pub fn source_id(&self) -> &str {
        &self.source_id
    }

    pub fn before(&self) -> &S {
        &self.before
    }

    pub fn operation_id(&self) -> &str {
        &self.operation_id
    }

    pub fn parameters(&self) -> &Value {
        &self.parameters
    }

    pub fn after(&self) -> &S {
        &self.after
    }

    pub fn obstruction_before(&self) -> &BigRational {
        &self.obstruction_before
    }

    pub fn obstruction_after(&self) -> &BigRational {
        &self.obstruction_after
    }

    pub fn structure_delta(&self) -> &StructureDelta {
        &self.structure_delta
    }

    pub fn protected_invariant_names(&self) -> impl Iterator<Item = &str> {
        self.protected_invariants
            .iter()
            .map(|witness| witness.name.as_str())
    }

    pub fn losses(&self) -> &[LossRecord] {
        &self.losses
    }

    pub fn parent_event_id(&self) -> Option<&str> {
        self.parent_event_id.as_deref()
    }
}

/// A finite DDA path. Empty paths are identities; nonempty paths retain their
/// event sequence without a fixed stage alphabet or length.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DdaPath<S> {
    start: S,
    events: Vec<DdaEvent<S>>,
}

impl<S> DdaPath<S>
where
    S: Clone + Eq,
{
    pub fn identity(state: S) -> Self {
        Self {
            start: state,
            events: Vec::new(),
        }
    }

    pub fn from_events(start: S, events: Vec<DdaEvent<S>>) -> Result<Self, FoundationError> {
        let mut current = &start;
        let mut previous: Option<&DdaEvent<S>> = None;
        let mut seen = BTreeSet::new();
        let boundary = events.first().map(|event| {
            (
                event.contract_id.as_str(),
                event.task_id.as_str(),
                event.source_id.as_str(),
            )
        });

        for event in &events {
            if !seen.insert(event.event_id.as_str()) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateEvent,
                    "DDA path event identities must be unique",
                ));
            }
            if event.before != *current {
                return Err(FoundationError::new(
                    FoundationErrorCode::IntermediateStateMismatch,
                    "DDA event before-state does not match the current path state",
                ));
            }
            if let Some((contract_id, task_id, source_id)) = boundary {
                if event.contract_id != contract_id
                    || event.task_id != task_id
                    || event.source_id != source_id
                {
                    return Err(FoundationError::new(
                        FoundationErrorCode::BoundaryMismatch,
                        "DDA path changed its contract, task, or source boundary",
                    ));
                }
            }
            if let Some(prior) = previous {
                if event.parent_event_id.as_deref() != Some(prior.event_id.as_str()) {
                    return Err(FoundationError::new(
                        FoundationErrorCode::ParentMismatch,
                        "DDA event parent does not name the preceding event",
                    ));
                }
            }
            current = &event.after;
            previous = Some(event);
        }

        Ok(Self { start, events })
    }

    pub fn start(&self) -> &S {
        &self.start
    }

    pub fn end(&self) -> &S {
        self.events.last().map_or(&self.start, |event| &event.after)
    }

    pub fn events(&self) -> &[DdaEvent<S>] {
        &self.events
    }

    pub fn compose(&self, next: &Self) -> Result<Self, FoundationError> {
        if self.end() != next.start() {
            return Err(FoundationError::new(
                FoundationErrorCode::IntermediateStateMismatch,
                "DDA paths do not share the same intermediate state",
            ));
        }
        if self.events.is_empty() {
            return Ok(next.clone());
        }
        if next.events.is_empty() {
            return Ok(self.clone());
        }

        let left_last = self.events.last().checked_invariant_e914e36b("the left path is nonempty");
        let right_first = next.events.first().checked_invariant_e914e36b("the right path is nonempty");
        if left_last.contract_id != right_first.contract_id
            || left_last.task_id != right_first.task_id
            || left_last.source_id != right_first.source_id
        {
            return Err(FoundationError::new(
                FoundationErrorCode::BoundaryMismatch,
                "DDA composition changed its contract, task, or source boundary",
            ));
        }
        if right_first.parent_event_id.as_deref() != Some(left_last.event_id.as_str()) {
            return Err(FoundationError::new(
                FoundationErrorCode::ParentMismatch,
                "the first right event is not a child of the last left event",
            ));
        }

        let mut events = self.events.clone();
        events.extend(next.events.iter().cloned());
        Self::from_events(self.start.clone(), events)
    }
}

/// Replay outcomes are explicit and do not promote authority.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DdaReplayCode {
    Accepted,
    OperatorUnavailable,
    AfterStateMismatch,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DdaReplayReceipt<S> {
    code: DdaReplayCode,
    after: Option<S>,
    event_id: Option<String>,
}

impl<S> DdaReplayReceipt<S> {
    pub fn code(&self) -> DdaReplayCode {
        self.code
    }

    pub fn accepted(&self) -> bool {
        self.code == DdaReplayCode::Accepted
    }

    pub fn after(&self) -> Option<&S> {
        self.after.as_ref()
    }

    pub fn event_id(&self) -> Option<&str> {
        self.event_id.as_deref()
    }
}

/// Replay a path through a caller-supplied exact operation resolver. Returning
/// `None` means the named operation is unavailable.
pub fn replay_dda_path<S, Resolve>(path: &DdaPath<S>, mut resolve: Resolve) -> DdaReplayReceipt<S>
where
    S: Clone + Eq,
    Resolve: FnMut(&str, &S, &Value) -> Option<S>,
{
    let mut current = path.start.clone();
    for event in &path.events {
        let Some(reproduced) = resolve(&event.operation_id, &current, &event.parameters) else {
            return DdaReplayReceipt {
                code: DdaReplayCode::OperatorUnavailable,
                after: None,
                event_id: Some(event.event_id.clone()),
            };
        };
        if reproduced != event.after {
            return DdaReplayReceipt {
                code: DdaReplayCode::AfterStateMismatch,
                after: Some(reproduced),
                event_id: Some(event.event_id.clone()),
            };
        }
        current = reproduced;
    }
    DdaReplayReceipt {
        code: DdaReplayCode::Accepted,
        after: Some(current),
        event_id: path.events.last().map(|event| event.event_id.clone()),
    }
}

// Origin: engine/crates_rs/pfp/src/foundation/dda.rs
// Claim: urn:core:crates_rs:pfp:dda:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde914e36b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde914e36b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore914e36b {
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
impl BoundaryErrore914e36b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore914e36b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore914e36b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde914e36b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore914e36b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore914e36b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore914e36b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore914e36b::ExceedsCapacity {
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
mod l4_boundary_tests_e914e36b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde914e36b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde914e36b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde914e36b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde914e36b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde914e36b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore914e36b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore914e36b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
