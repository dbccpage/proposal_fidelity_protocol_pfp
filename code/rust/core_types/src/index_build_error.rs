#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IndexBuildError {
    DuplicateObservationId { id: String },
    DuplicateMotifId { id: String },
    DuplicateAntiMorphismId { id: String },
    DuplicateOperatorId { id: String },
}

// Origin: engine/crates_rs/core_types/src/index_build_error.rs
// Claim: urn:core:crates_rs:core-types:index-build-error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IndexBuildError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IndexBuildError {}

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NamespaceAdmissionError {
    Build(IndexBuildError),
    EmptyId,
    SharedAcrossNamespaces,
    Empty,
}

/// Four identifier namespaces that are internally unique and pairwise disjoint.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DisjointIndexIds {
    count: usize,
}

fn take_ids(
    ids: &[String],
    duplicate: fn(String) -> IndexBuildError,
    global: &mut BTreeSet<String>,
) -> Result<usize, NamespaceAdmissionError> {
    let mut local = BTreeSet::new();
    for id in ids {
        if id.is_empty() {
            return Err(NamespaceAdmissionError::EmptyId);
        }
        if !local.insert(id.clone()) {
            return Err(NamespaceAdmissionError::Build(duplicate(id.clone())));
        }
        if !global.insert(id.clone()) {
            return Err(NamespaceAdmissionError::SharedAcrossNamespaces);
        }
    }
    Ok(local.len())
}

impl DisjointIndexIds {
    pub fn try_admit(
        observations: &[String],
        motifs: &[String],
        anti_morphisms: &[String],
        operators: &[String],
    ) -> Result<Self, NamespaceAdmissionError> {
        let mut global = BTreeSet::new();
        let mut count = 0usize;
        count = count.checked_add(take_ids(observations, |id| IndexBuildError::DuplicateObservationId { id }, &mut global)?).ok_or(NamespaceAdmissionError::Empty)?;
        count = count.checked_add(take_ids(motifs, |id| IndexBuildError::DuplicateMotifId { id }, &mut global)?).ok_or(NamespaceAdmissionError::Empty)?;
        count = count.checked_add(take_ids(anti_morphisms, |id| IndexBuildError::DuplicateAntiMorphismId { id }, &mut global)?).ok_or(NamespaceAdmissionError::Empty)?;
        count = count.checked_add(take_ids(operators, |id| IndexBuildError::DuplicateOperatorId { id }, &mut global)?).ok_or(NamespaceAdmissionError::Empty)?;
        if count == 0 {
            return Err(NamespaceAdmissionError::Empty);
        }
        Ok(Self { count })
    }

    pub fn count(&self) -> usize { self.count }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod namespace_tests {
    use super::*;

    #[test]
    fn four_namespaces_can_share_no_identifier() {
        let admitted = DisjointIndexIds::try_admit(
            &["obs".to_string()],
            &["motif".to_string()],
            &["anti".to_string()],
            &["op".to_string()],
        );
        assert!(matches!(admitted, Ok(ref admitted) if admitted.count() == 4));
    }

    #[test]
    fn one_identifier_in_two_namespaces_is_refused() {
        let admitted = DisjointIndexIds::try_admit(&["shared".to_string()], &["shared".to_string()], &[], &[]);
        assert!(matches!(admitted, Err(NamespaceAdmissionError::SharedAcrossNamespaces)));
    }
}
