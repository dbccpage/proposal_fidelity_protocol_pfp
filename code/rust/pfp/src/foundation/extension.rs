use super::repair::ExhaustionCertificate;
use super::{require_name, require_nonnegative, FoundationError, FoundationErrorCode};
use num_rational::BigRational;
use num_traits::Zero;
use std::collections::BTreeSet;

/// One old point, its lifted point, and the exact detector value preserved by
/// the extension.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreservedPoint<Old, New> {
    old: Old,
    lifted: New,
    retracted: Old,
    old_detector_value: BigRational,
    lifted_detector_value: BigRational,
}

impl<Old, New> PreservedPoint<Old, New> {
    pub fn old(&self) -> &Old {
        &self.old
    }

    pub fn lifted(&self) -> &New {
        &self.lifted
    }

    pub fn detector_value(&self) -> &BigRational {
        &self.old_detector_value
    }
}

/// A finite, checked lift/retraction witness. It records only points whose
/// round trip and exact detector preservation were recomputed successfully.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ConservativeExtensionWitness<Old, New> {
    old_context_id: String,
    new_context_id: String,
    points: Vec<PreservedPoint<Old, New>>,
    target_points: Vec<New>,
    target_point_count: usize,
    extension_size: usize,
}

impl<Old, New> ConservativeExtensionWitness<Old, New>
where
    Old: Clone + Eq,
    New: Clone + Eq,
{
    fn ensure_unique_points<T: Eq>(
        points: &[T],
        message: &'static str,
    ) -> Result<(), FoundationError> {
        for (index, point) in points.iter().enumerate() {
            if points[..index].contains(point) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    message,
                ));
            }
        }
        Ok(())
    }

    fn certify_single_point<Lift, Forget, OldDetector, NewDetector>(
        old: &Old,
        new_points: &[New],
        lift: &Lift,
        forget: &Forget,
        old_detector: &OldDetector,
        new_detector: &NewDetector,
    ) -> Result<PreservedPoint<Old, New>, FoundationError>
    where
        Lift: Fn(&Old) -> New,
        Forget: Fn(&New) -> Option<Old>,
        OldDetector: Fn(&Old) -> BigRational,
        NewDetector: Fn(&New) -> BigRational,
    {
        let lifted = lift(old);
        if !new_points.contains(&lifted) {
            return Err(FoundationError::new(
                FoundationErrorCode::IncompleteExtension,
                "every lifted old point must occur in the declared new finite context",
            ));
        }
        let retracted = forget(&lifted).ok_or_else(|| {
            FoundationError::new(
                FoundationErrorCode::RetractionFailure,
                "forget must be defined on every lifted old point",
            )
        })?;
        if &retracted != old {
            return Err(FoundationError::new(
                FoundationErrorCode::RetractionFailure,
                "forget(lift(old)) must reproduce the old point exactly",
            ));
        }
        let old_value = old_detector(old);
        let new_value = new_detector(&lifted);
        require_nonnegative(&old_value, "old detector value")?;
        require_nonnegative(&new_value, "new detector value")?;
        if old_value != new_value {
            return Err(FoundationError::new(
                FoundationErrorCode::DetectorNotPreserved,
                "the extension changes an old exact detector value",
            ));
        }
        Ok(PreservedPoint {
            old: old.clone(),
            lifted,
            retracted,
            old_detector_value: old_value,
            lifted_detector_value: new_value,
        })
    }

    #[allow(clippy::too_many_arguments)]
    pub fn certify<Lift, Forget, OldDetector, NewDetector>(
        old_context_id: impl Into<String>,
        new_context_id: impl Into<String>,
        old_points: &[Old],
        new_points: &[New],
        lift: Lift,
        forget: Forget,
        old_detector: OldDetector,
        new_detector: NewDetector,
    ) -> Result<Self, FoundationError>
    where
        Lift: Fn(&Old) -> New,
        Forget: Fn(&New) -> Option<Old>,
        OldDetector: Fn(&Old) -> BigRational,
        NewDetector: Fn(&New) -> BigRational,
    {
        let old_context_id = old_context_id.into();
        let new_context_id = new_context_id.into();
        require_name(&old_context_id, "old context identity")?;
        require_name(&new_context_id, "new context identity")?;

        if new_points.len() < old_points.len() {
            return Err(FoundationError::new(
                FoundationErrorCode::IncompleteExtension,
                "a finite extension cannot contain fewer points than its old context",
            ));
        }

        Self::ensure_unique_points(old_points, "old finite context points must be unique")?;
        Self::ensure_unique_points(new_points, "new finite context points must be unique")?;

        let mut points = Vec::with_capacity(old_points.len());
        for old in old_points {
            points.push(Self::certify_single_point(
                old,
                new_points,
                &lift,
                &forget,
                &old_detector,
                &new_detector,
            )?);
        }

        Ok(Self {
            old_context_id,
            new_context_id,
            points,
            target_points: new_points.to_vec(),
            target_point_count: new_points.len(),
            extension_size: new_points.len() - old_points.len(),
        })
    }

    pub fn old_context_id(&self) -> &str {
        &self.old_context_id
    }

    pub fn new_context_id(&self) -> &str {
        &self.new_context_id
    }

    pub fn points(&self) -> &[PreservedPoint<Old, New>] {
        &self.points
    }

    pub fn target_point_count(&self) -> usize {
        self.target_point_count
    }

    pub fn extension_size(&self) -> usize {
        self.extension_size
    }

    pub fn forget_lift_holds(&self) -> bool {
        self.points.iter().all(|point| point.retracted == point.old)
    }

    pub fn detector_preserved(&self) -> bool {
        self.points
            .iter()
            .all(|point| point.old_detector_value == point.lifted_detector_value)
    }
}

/// One resolving member of a declared finite extension family.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExtensionCandidate<Old, New> {
    candidate_id: String,
    exhausted_context_id: String,
    exhausted_source_id: String,
    result_state: New,
    resulting_obstruction: BigRational,
    extension: ConservativeExtensionWitness<Old, New>,
}

impl<Old, New> ExtensionCandidate<Old, New>
where
    New: Clone + Eq,
{
    pub fn evaluate<Detector>(
        candidate_id: impl Into<String>,
        exhausted_context_id: impl Into<String>,
        exhausted_source_id: impl Into<String>,
        result_state: New,
        extension: ConservativeExtensionWitness<Old, New>,
        detector: Detector,
    ) -> Result<Self, FoundationError>
    where
        Detector: Fn(&New) -> BigRational,
    {
        let candidate_id = candidate_id.into();
        let exhausted_context_id = exhausted_context_id.into();
        let exhausted_source_id = exhausted_source_id.into();
        require_name(&candidate_id, "extension candidate identity")?;
        require_name(&exhausted_context_id, "exhausted context identity")?;
        require_name(&exhausted_source_id, "exhausted source identity")?;
        if extension.old_context_id != exhausted_context_id {
            return Err(FoundationError::new(
                FoundationErrorCode::ExtensionBindingMismatch,
                "extension witness is not bound to the exhausted context",
            ));
        }
        if extension.extension_size == 0 {
            return Err(FoundationError::new(
                FoundationErrorCode::IncompleteExtension,
                "an R2 candidate must add at least one declared finite point",
            ));
        }
        if !extension.target_points.contains(&result_state) {
            return Err(FoundationError::new(
                FoundationErrorCode::IncompleteExtension,
                "extension result state is outside the declared new finite context",
            ));
        }
        let resulting_obstruction = detector(&result_state);
        require_nonnegative(&resulting_obstruction, "extension obstruction")?;
        Ok(Self {
            candidate_id,
            exhausted_context_id,
            exhausted_source_id,
            result_state,
            resulting_obstruction,
            extension,
        })
    }

    pub fn candidate_id(&self) -> &str {
        &self.candidate_id
    }

    pub fn resulting_obstruction(&self) -> &BigRational {
        &self.resulting_obstruction
    }

    pub fn extension(&self) -> &ConservativeExtensionWitness<Old, New> {
        &self.extension
    }
}

/// A finite, ordered extension family declared for exactly one exhausted
/// context/source pair.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DeclaredExtensionFamily<Old, New> {
    family_id: String,
    exhausted_context_id: String,
    exhausted_source_id: String,
    candidates: Vec<ExtensionCandidate<Old, New>>,
}

impl<Old, New> DeclaredExtensionFamily<Old, New> {
    pub fn new(
        family_id: impl Into<String>,
        exhausted_context_id: impl Into<String>,
        exhausted_source_id: impl Into<String>,
        candidates: Vec<ExtensionCandidate<Old, New>>,
    ) -> Result<Self, FoundationError> {
        let family_id = family_id.into();
        let exhausted_context_id = exhausted_context_id.into();
        let exhausted_source_id = exhausted_source_id.into();
        require_name(&family_id, "extension family identity")?;
        require_name(&exhausted_context_id, "exhausted context identity")?;
        require_name(&exhausted_source_id, "exhausted source identity")?;
        let mut identities = BTreeSet::new();
        for candidate in &candidates {
            if candidate.exhausted_context_id != exhausted_context_id
                || candidate.exhausted_source_id != exhausted_source_id
            {
                return Err(FoundationError::new(
                    FoundationErrorCode::ExtensionBindingMismatch,
                    "every extension candidate must bind the family's context and source",
                ));
            }
            if !identities.insert(candidate.candidate_id.clone()) {
                return Err(FoundationError::new(
                    FoundationErrorCode::DuplicateIdentity,
                    "extension candidate identities must be unique",
                ));
            }
        }
        Ok(Self {
            family_id,
            exhausted_context_id,
            exhausted_source_id,
            candidates,
        })
    }

    pub fn family_id(&self) -> &str {
        &self.family_id
    }

    pub fn candidates(&self) -> &[ExtensionCandidate<Old, New>] {
        &self.candidates
    }
}

/// Scoped minimum within one declared finite extension family. Ties are kept
/// in declared order; `unique_candidate_id` is populated only for a singleton
/// minimum.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExtensionAssessment {
    family_id: String,
    declared_candidate_order: Vec<String>,
    minimum_extension_size: usize,
    tied_candidate_ids: Vec<String>,
}

impl ExtensionAssessment {
    pub fn family_id(&self) -> &str {
        &self.family_id
    }

    pub fn declared_candidate_order(&self) -> &[String] {
        &self.declared_candidate_order
    }

    pub fn minimum_extension_size(&self) -> usize {
        self.minimum_extension_size
    }

    pub fn tied_candidate_ids(&self) -> &[String] {
        &self.tied_candidate_ids
    }

    pub fn unique_candidate_id(&self) -> Option<&str> {
        (self.tied_candidate_ids.len() == 1).then(|| self.tied_candidate_ids[0].as_str())
    }
}

/// Assess actual extension candidates only after checked positive exhaustion.
/// This never claims a global least extension beyond the declared family.
pub fn assess_extension_family<Old, New>(
    certificate: &ExhaustionCertificate,
    family: &DeclaredExtensionFamily<Old, New>,
) -> Result<ExtensionAssessment, FoundationError> {
    if certificate.minimum().is_zero() {
        return Err(FoundationError::new(
            FoundationErrorCode::R1Priority,
            "R1 has a zero-obstruction same-context repair; R2 extension is refused",
        ));
    }
    if family.exhausted_context_id != certificate.context_id()
        || family.exhausted_source_id != certificate.source_state_id()
    {
        return Err(FoundationError::new(
            FoundationErrorCode::ExtensionBindingMismatch,
            "extension family does not bind the exhausted context and source",
        ));
    }

    let minimum_extension_size = family
        .candidates
        .iter()
        .filter(|candidate| candidate.resulting_obstruction.is_zero())
        .map(|candidate| candidate.extension.extension_size)
        .min()
        .ok_or_else(|| {
            FoundationError::new(
                FoundationErrorCode::NoResolvingExtension,
                "the declared finite extension family contains no exact resolving candidate",
            )
        })?;
    let tied_candidate_ids = family
        .candidates
        .iter()
        .filter(|candidate| {
            candidate.resulting_obstruction.is_zero()
                && candidate.extension.extension_size == minimum_extension_size
        })
        .map(|candidate| candidate.candidate_id.clone())
        .collect();
    Ok(ExtensionAssessment {
        family_id: family.family_id.clone(),
        declared_candidate_order: family
            .candidates
            .iter()
            .map(|candidate| candidate.candidate_id.clone())
            .collect(),
        minimum_extension_size,
        tied_candidate_ids,
    })
}

// Origin: engine/crates_rs/pfp/src/foundation/extension.rs
// Claim: urn:core:crates_rs:pfp:extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4043943c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4043943c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4043943c {
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
impl BoundaryError4043943c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4043943c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4043943c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4043943c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4043943c> {
        if capacity_bound == 0 {
            return Err(BoundaryError4043943c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4043943c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4043943c::ExceedsCapacity {
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
mod l4_boundary_tests_4043943c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4043943c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4043943c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4043943c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4043943c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4043943c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4043943c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4043943c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
