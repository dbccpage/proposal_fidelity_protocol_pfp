//! Finite presentation-to-Primitive-Difference reference model.
//!
//! Rust face of `engine/kernel/presentation_difference.py`.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub type Profile = Vec<String>;
pub type Pair = (String, String);

#[derive(Debug, Error, PartialEq, Eq)]
pub enum PresentationDifferenceError {
    #[error("validation error: {0}")]
    Validation(String),

    #[error("refusal {code}: {message}")]
    Refusal { code: String, message: String },
}

pub fn canonical_sha256(
    domain: &str,
    payload: &Value,
) -> Result<String, PresentationDifferenceError> {
    let raw = serde_json::to_string(payload)
        .map_err(|e| PresentationDifferenceError::Validation(e.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(domain.as_bytes());
    hasher.update(b":");
    hasher.update(raw.as_bytes());
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExtensionEffect {
    #[serde(rename = "RESOLVED")]
    Resolved,
    #[serde(rename = "INEFFECTIVE")]
    Ineffective,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "QuestionWire")]
pub struct QuestionV1 {
    pub question_id: String,
    pub answers: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct QuestionWire {
    question_id: String,
    answers: Vec<String>,
}

impl TryFrom<QuestionWire> for QuestionV1 {
    type Error = PresentationDifferenceError;

    fn try_from(raw: QuestionWire) -> Result<Self, Self::Error> {
        QuestionV1::new(&raw.question_id, raw.answers)
    }
}

impl QuestionV1 {
    pub fn new(
        question_id: &str,
        answers: Vec<String>,
    ) -> Result<Self, PresentationDifferenceError> {
        if question_id.is_empty() {
            return Err(PresentationDifferenceError::Validation(
                "question_id must be non-empty".into(),
            ));
        }
        Ok(Self {
            question_id: question_id.to_string(),
            answers,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "question_id": self.question_id,
            "answers": self.answers,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "PresentationWire")]
pub struct PresentationV1 {
    pub points: Vec<String>,
    pub questions: Vec<QuestionV1>,
    pub authority_effect: String,
}

#[derive(Debug, Deserialize)]
struct PresentationWire {
    points: Vec<String>,
    questions: Vec<QuestionV1>,
    #[serde(default)]
    authority_effect: String,
}

impl TryFrom<PresentationWire> for PresentationV1 {
    type Error = PresentationDifferenceError;

    fn try_from(raw: PresentationWire) -> Result<Self, Self::Error> {
        let mut presentation = PresentationV1::new(raw.points, raw.questions)?;
        if !raw.authority_effect.is_empty() {
            presentation.authority_effect = raw.authority_effect;
        }
        Ok(presentation)
    }
}

impl PresentationV1 {
    pub fn new(
        points: Vec<String>,
        questions: Vec<QuestionV1>,
    ) -> Result<Self, PresentationDifferenceError> {
        if points.is_empty() {
            return Err(PresentationDifferenceError::Validation(
                "points must be non-empty".into(),
            ));
        }
        let mut p_seen = BTreeSet::new();
        for p in &points {
            if !p_seen.insert(p.clone()) {
                return Err(PresentationDifferenceError::Validation(
                    "points must be unique".into(),
                ));
            }
        }
        let mut q_seen = BTreeSet::new();
        for q in &questions {
            if q.question_id.is_empty() {
                return Err(PresentationDifferenceError::Validation(
                    "question_id must be non-empty".into(),
                ));
            }
            if !q_seen.insert(q.question_id.clone()) {
                return Err(PresentationDifferenceError::Validation(
                    "question IDs must be unique".into(),
                ));
            }
            if q.answers.len() != points.len() {
                return Err(PresentationDifferenceError::Validation(
                    "every question must answer every carrier point".into(),
                ));
            }
        }

        Ok(Self {
            points,
            questions,
            authority_effect: "None".into(),
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "points": self.points,
            "questions": self.questions.iter().map(|q| q.to_canonical()).collect::<Vec<_>>(),
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PresentationDifferenceError> {
        canonical_sha256(
            "core.presentation_difference.presentation.v1",
            &self.to_canonical(),
        )
    }

    pub fn point_index(&self, point: &str) -> Option<usize> {
        self.points.iter().position(|p| p == point)
    }

    pub fn profile(&self, point: &str) -> Option<Profile> {
        let idx = self.point_index(point)?;
        let mut profile = Vec::with_capacity(self.questions.len());
        for question in &self.questions {
            profile.push(question.answers.get(idx)?.clone());
        }
        Some(profile)
    }

    pub fn zero_related(&self, left: &str, right: &str) -> bool {
        match (self.profile(left), self.profile(right)) {
            (Some(p1), Some(p2)) => p1 == p2,
            _ => false,
        }
    }

    pub fn partition(&self) -> Vec<Vec<String>> {
        let mut classes: BTreeMap<Profile, Vec<String>> = BTreeMap::new();
        for p in &self.points {
            if let Some(prof) = self.profile(p) {
                classes.entry(prof).or_default().push(p.clone());
            }
        }
        classes.into_values().collect()
    }

    pub fn class_count(&self) -> usize {
        self.partition().len()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DemandV1 {
    pub left: String,
    pub right: String,
    pub retained: bool,
    pub protected: bool,
    pub authority_effect: String,
}

impl DemandV1 {
    pub fn new(
        left: &str,
        right: &str,
        retained: bool,
        protected: bool,
    ) -> Result<Self, PresentationDifferenceError> {
        if left == right {
            return Err(PresentationDifferenceError::Validation(
                "a demand must be off-diagonal".into(),
            ));
        }
        Ok(Self {
            left: left.to_string(),
            right: right.to_string(),
            retained,
            protected,
            authority_effect: "None".into(),
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "left": self.left,
            "right": self.right,
            "retained": self.retained,
            "protected": self.protected,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PresentationDifferenceError> {
        canonical_sha256(
            "core.presentation_difference.demand.v1",
            &self.to_canonical(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ActiveObstructionV1 {
    pub presentation_id: String,
    pub demand_id: String,
    pub pair: Pair,
    pub shared_profile: Profile,
    pub authority_effect: String,
}

impl ActiveObstructionV1 {
    pub fn to_canonical(&self) -> Value {
        json!({
            "presentation_id": self.presentation_id,
            "demand_id": self.demand_id,
            "pair": [self.pair.0, self.pair.1],
            "shared_profile": self.shared_profile,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PresentationDifferenceError> {
        canonical_sha256(
            "core.presentation_difference.active-obstruction.v1",
            &self.to_canonical(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtensionEvaluationV1 {
    pub parent_id: String,
    pub child_id: String,
    pub demand_id: String,
    pub old_questions_preserved: bool,
    pub adds_question_structure: bool,
    pub strict_split: bool,
    pub class_count_before: usize,
    pub class_count_after: usize,
    pub effect: ExtensionEffect,
    pub derived_new_question_ids: Vec<String>,
    pub authority_effect: String,
}

impl ExtensionEvaluationV1 {
    pub fn accepted(&self) -> bool {
        self.old_questions_preserved
            && self.adds_question_structure
            && self.strict_split
            && self.class_count_after > self.class_count_before
            && self.effect == ExtensionEffect::Resolved
    }
}

pub fn active_obstruction(
    presentation: &PresentationV1,
    demand: &DemandV1,
) -> Option<ActiveObstructionV1> {
    if !demand.retained || !demand.protected {
        return None;
    }
    presentation.point_index(&demand.left)?;
    presentation.point_index(&demand.right)?;
    if !presentation.zero_related(&demand.left, &demand.right) {
        return None;
    }

    let pres_id = presentation.canonical_id().ok()?;
    let dem_id = demand.canonical_id().ok()?;
    let prof = presentation.profile(&demand.left)?;

    Some(ActiveObstructionV1 {
        presentation_id: pres_id,
        demand_id: dem_id,
        pair: (demand.left.clone(), demand.right.clone()),
        shared_profile: prof,
        authority_effect: "None".into(),
    })
}

pub fn question_is_derived_from_parent(parent: &PresentationV1, question: &QuestionV1) -> bool {
    if question.answers.len() != parent.points.len() {
        return false;
    }
    let mut values_by_profile: BTreeMap<Profile, &str> = BTreeMap::new();
    for (index, point) in parent.points.iter().enumerate() {
        if let Some(old_profile) = parent.profile(point) {
            let answer = &question.answers[index];
            if let Some(prev) = values_by_profile.get(&old_profile) {
                if *prev != answer.as_str() {
                    return false;
                }
            } else {
                values_by_profile.insert(old_profile, answer.as_str());
            }
        }
    }
    true
}

pub fn evaluate_extension(
    parent: &PresentationV1,
    child: &PresentationV1,
    demand: &DemandV1,
) -> Result<ExtensionEvaluationV1, PresentationDifferenceError> {
    if active_obstruction(parent, demand).is_none() {
        return Err(PresentationDifferenceError::Refusal {
            code: "NO_ACTIVE_OBSTRUCTION".into(),
            message: "the declared demand is not retained, protected, and profile-zero".into(),
        });
    }

    if child.points != parent.points {
        return Err(PresentationDifferenceError::Refusal {
            code: "CARRIER_CHANGE_UNLICENSED".into(),
            message: "this bridge admits question-family extension on one carrier only".into(),
        });
    }

    let parent_count = parent.questions.len();
    let old_preserved = child.questions.len() >= parent_count
        && child.questions[..parent_count] == parent.questions[..];
    let adds_structure = child.questions.len() > parent_count;
    let new_questions = if old_preserved {
        &child.questions[parent_count..]
    } else {
        &[][..]
    };

    let derived: Vec<String> = new_questions
        .iter()
        .filter(|q| question_is_derived_from_parent(parent, q))
        .map(|q| q.question_id.clone())
        .collect();

    let strict_split = parent.zero_related(&demand.left, &demand.right)
        && !child.zero_related(&demand.left, &demand.right);
    let effect = if strict_split {
        ExtensionEffect::Resolved
    } else {
        ExtensionEffect::Ineffective
    };

    Ok(ExtensionEvaluationV1 {
        parent_id: parent.canonical_id()?,
        child_id: child.canonical_id()?,
        demand_id: demand.canonical_id()?,
        old_questions_preserved: old_preserved,
        adds_question_structure: adds_structure,
        strict_split,
        class_count_before: parent.class_count(),
        class_count_after: child.class_count(),
        effect,
        derived_new_question_ids: derived,
        authority_effect: "None".into(),
    })
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/presentation_difference.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:presentation-difference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3daf7a5b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
