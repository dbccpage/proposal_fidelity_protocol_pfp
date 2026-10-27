//! Structural Intake Rust twin (INTAKE-S6 / LIB4-005 / D-LIB-06).
//!
//! Schema-driven Rust twin for intake observatory.
//! AuthorityEffect: None on all intake operations.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_cba46fd0;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_cba46fd0<T> = std::result::Result<T, BoundaryError_cba46fd0>;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum IntakeMatchKind {
    CandidateAlignment,
    DefinitionalIdentity,
    WitnessedEquivalence,
    Refinement,
    Conflict,
    NonEquivalent,
    Incommensurable,
    MissingAdapter,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntakeCorrespondenceSpan {
    pub span_id: String,
    pub source_a: String,
    pub source_b: String,
    pub match_kind: IntakeMatchKind,
    pub merge_eligible: bool,
    pub authority_effect: String,
}

impl IntakeCorrespondenceSpan {
    pub fn new(
        span_id: String,
        source_a: String,
        source_b: String,
        match_kind: IntakeMatchKind,
    ) -> Self {
        let merge_eligible = matches!(
            match_kind,
            IntakeMatchKind::DefinitionalIdentity | IntakeMatchKind::WitnessedEquivalence
        );
        Self {
            span_id,
            source_a,
            source_b,
            match_kind,
            merge_eligible,
            authority_effect: "None".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntakeObservatoryReport {
    pub report_id: String,
    pub spans: Vec<IntakeCorrespondenceSpan>,
    pub merge_eligible_count: usize,
    pub authority_effect: String,
}

impl IntakeObservatoryReport {
    pub fn build(report_id: String, spans: Vec<IntakeCorrespondenceSpan>) -> Self {
        let merge_eligible_count = spans.iter().filter(|s| s.merge_eligible).count();
        Self {
            report_id,
            spans,
            merge_eligible_count,
            authority_effect: "None".to_string(),
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_intake_span_merge_eligibility() {
        let s1 = IntakeCorrespondenceSpan::new(
            "SPAN-1".to_string(),
            "srcA".to_string(),
            "srcB".to_string(),
            IntakeMatchKind::CandidateAlignment,
        );
        assert!(!s1.merge_eligible);

        let s2 = IntakeCorrespondenceSpan::new(
            "SPAN-2".to_string(),
            "srcA".to_string(),
            "srcB".to_string(),
            IntakeMatchKind::DefinitionalIdentity,
        );
        assert!(s2.merge_eligible);

        let report = IntakeObservatoryReport::build("REP-1".to_string(), vec![s1, s2]);
        assert_eq!(report.merge_eligible_count, 1);
        assert_eq!(report.authority_effect, "None");
    }
}

// --- exact carrier witness ---
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IntakeCertError {
    Empty,
    Authority,
    Endpoint,
    Flag,
    AlreadyJoined { left: String, right: String },
    Depth,
}

// Origin: engine/crates_rs/core_types/src/structural_intake.rs
// Claim: urn:core:crates_rs:core-types:structural-intake:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IntakeCertError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IntakeCertError {}

/// Merge-eligible spans are unions. A conflict inside one class is refused.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CertifiedIntake {
    classes: usize,
    merges: usize,
}

fn find_root(parent: &mut BTreeMap<String, String>, start: &str) -> Result<String, IntakeCertError> {
    let mut cursor = start.to_string();
    for _ in 0..32 {
        match parent.get(&cursor) {
            Some(parent_name) if parent_name != &cursor => {
                let next = parent_name.clone();
                let grand = match parent.get(&next) {
                    Some(name) => name.clone(),
                    None => next.clone(),
                };
                parent.insert(cursor, grand);
                cursor = next;
            }
            Some(_) => return Ok(cursor),
            None => {
                parent.insert(cursor.clone(), cursor.clone());
                return Ok(cursor);
            }
        }
    }
    Err(IntakeCertError::Depth)
}

impl CertifiedIntake {
    fn validate_span_header(span: &IntakeCorrespondenceSpan) -> Result<bool, IntakeCertError> {
        if span.authority_effect != "None" || span.span_id.is_empty() {
            return Err(IntakeCertError::Authority);
        }
        if span.source_a.is_empty() || span.source_b.is_empty() || span.source_a == span.source_b {
            return Err(IntakeCertError::Endpoint);
        }
        let should_merge = matches!(
            span.match_kind,
            IntakeMatchKind::DefinitionalIdentity | IntakeMatchKind::WitnessedEquivalence
        );
        if span.merge_eligible != should_merge {
            return Err(IntakeCertError::Flag);
        }
        Ok(should_merge)
    }

    fn apply_span(
        parent: &mut BTreeMap<String, String>,
        span: &IntakeCorrespondenceSpan,
    ) -> Result<usize, IntakeCertError> {
        let should_merge = Self::validate_span_header(span)?;
        let left = find_root(parent, &span.source_a)?;
        let right = find_root(parent, &span.source_b)?;
        if should_merge {
            if left != right {
                parent.insert(left, right);
            }
            return Ok(1);
        }
        if matches!(span.match_kind, IntakeMatchKind::Conflict) && left == right {
            return Err(IntakeCertError::AlreadyJoined {
                left: span.source_a.clone(),
                right: span.source_b.clone(),
            });
        }
        Ok(0)
    }

    pub fn try_certified(spans: &[IntakeCorrespondenceSpan]) -> Result<Self, IntakeCertError> {
        if spans.is_empty() {
            return Err(IntakeCertError::Empty);
        }
        let mut parent = BTreeMap::new();
        let mut merges = 0usize;
        for span in spans {
            let delta = Self::apply_span(&mut parent, span)?;
            merges = merges.checked_add(delta).ok_or(IntakeCertError::Depth)?;
        }
        let nodes: BTreeSet<String> = parent.keys().cloned().collect();
        let mut roots = BTreeSet::new();
        for node in nodes {
            roots.insert(find_root(&mut parent, &node)?);
        }
        Ok(Self { classes: roots.len(), merges })
    }

    pub fn classes(&self) -> usize { self.classes }
    pub fn merges(&self) -> usize { self.merges }
}

#[cfg(test)]
mod certified_intake_tests {
    use super::*;

    #[test]
    fn a_conflict_inside_one_class_is_refused() {
        let spans = [
            IntakeCorrespondenceSpan::new("1".to_string(), "a".to_string(), "b".to_string(), IntakeMatchKind::DefinitionalIdentity),
            IntakeCorrespondenceSpan::new("2".to_string(), "b".to_string(), "c".to_string(), IntakeMatchKind::DefinitionalIdentity),
            IntakeCorrespondenceSpan::new("3".to_string(), "a".to_string(), "c".to_string(), IntakeMatchKind::Conflict),
        ];
        let certified = CertifiedIntake::try_certified(&spans);
        assert!(matches!(certified, Err(IntakeCertError::AlreadyJoined { .. })));
    }

    #[test]
    fn two_identities_form_one_class() {
        let spans = [
            IntakeCorrespondenceSpan::new("1".to_string(), "a".to_string(), "b".to_string(), IntakeMatchKind::DefinitionalIdentity),
            IntakeCorrespondenceSpan::new("2".to_string(), "b".to_string(), "c".to_string(), IntakeMatchKind::WitnessedEquivalence),
        ];
        let certified = CertifiedIntake::try_certified(&spans);
        assert!(matches!(certified, Ok(ref certified) if certified.classes() == 1 && certified.merges() == 2));
    }
}
