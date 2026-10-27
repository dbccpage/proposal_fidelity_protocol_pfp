//! Proposal-only presentation extension after declared finite exhaustion.
//!
//! Rust face of `engine/kernel/structure_extension.py`.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use thiserror::Error;

use core_homotopy_type_theory::presentation_difference::{
    DemandV1, ExtensionEvaluationV1, PresentationV1,
};

use super::router_plan_grammar::{
    DeclaredPlanEvaluationV1, FinitePlanGrammarV1, FrontierTerminal, PlanFrontierV1,
    SearchDeclarationV1,
};

#[derive(Debug, Error, PartialEq, Eq)]
pub enum StructureExtensionError {
    #[error("validation error: {0}")]
    Validation(String),

    #[error("refusal {code}: {message}")]
    Refusal { code: String, message: String },
}

pub fn canonical_sha256(domain: &str, payload: &Value) -> Result<String, StructureExtensionError> {
    let mut canonical_payload = payload.clone();
    canonical_payload.sort_all_objects();
    let raw = serde_json::to_string(&canonical_payload)
        .map_err(|e| StructureExtensionError::Validation(e.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(domain.as_bytes());
    hasher.update(b":");
    hasher.update(raw.as_bytes());
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtensionProposalReceiptV1 {
    pub parent_id: String,
    pub child_id: String,
    pub demand_id: String,
    pub search_id: String,
    pub grammar_id: String,
    pub grammar_digest: String,
    pub frontier_id: String,
    pub new_question_ids: Vec<String>,
    pub class_count_before: usize,
    pub class_count_after: usize,
    pub authority_effect: String,
}

impl ExtensionProposalReceiptV1 {
    pub fn to_canonical(&self) -> Value {
        json!({
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "demand_id": self.demand_id,
            "search_id": self.search_id,
            "grammar_id": self.grammar_id,
            "grammar_digest": self.grammar_digest,
            "frontier_id": self.frontier_id,
            "new_question_ids": self.new_question_ids,
            "class_count_before": self.class_count_before,
            "class_count_after": self.class_count_after,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, StructureExtensionError> {
        canonical_sha256("core.structure-extension.receipt.v1", &self.to_canonical())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckedQuestionExtensionV1 {
    pub parent: PresentationV1,
    pub child: PresentationV1,
    pub demand: DemandV1,
    pub search: SearchDeclarationV1,
    pub same_level_grammar: FinitePlanGrammarV1,
    pub same_level_evaluations: Vec<DeclaredPlanEvaluationV1>,
    pub evaluation: ExtensionEvaluationV1,
    pub frontier: PlanFrontierV1,
}

fn validate_extension_preconditions(
    checked: &CheckedQuestionExtensionV1,
) -> Result<Vec<String>, StructureExtensionError> {
    if checked.frontier.terminal != FrontierTerminal::NoVerifiedPlan {
        return Err(StructureExtensionError::Refusal {
            code: "SAME_LEVEL_REPAIRS_REMAIN".into(),
            message: "structure extension is refused while same-level repairs remain unexhausted"
                .into(),
        });
    }
    if !checked.evaluation.accepted() {
        return Err(StructureExtensionError::Refusal {
            code: "EXTENSION_EVALUATION_NOT_ACCEPTED".into(),
            message: "extension evaluation did not strictly split the obstruction".into(),
        });
    }
    if checked.child.class_count() <= checked.parent.class_count() {
        return Err(StructureExtensionError::Refusal {
            code: "NO_PARTITION_REFINEMENT".into(),
            message: "an accepted extension must strictly refine the finite partition".into(),
        });
    }
    let parent_count = checked.parent.questions.len();
    let new_questions: Vec<String> = checked
        .child
        .questions
        .iter()
        .skip(parent_count)
        .map(|q| q.question_id.clone())
        .collect();
    if new_questions.is_empty() {
        return Err(StructureExtensionError::Refusal {
            code: "NO_NEW_QUESTIONS".into(),
            message: "extension receipt requires new question IDs".into(),
        });
    }
    let mut seen = BTreeSet::new();
    for q in &new_questions {
        if !seen.insert(q.clone()) {
            return Err(StructureExtensionError::Validation(
                "new_question_ids must be unique".into(),
            ));
        }
    }
    Ok(new_questions)
}

pub fn propose_question_family_extension(
    checked: &CheckedQuestionExtensionV1,
) -> Result<ExtensionProposalReceiptV1, StructureExtensionError> {
    let new_questions = validate_extension_preconditions(checked)?;
    fn map_val_err(error: impl std::fmt::Display) -> StructureExtensionError {
        StructureExtensionError::Validation(error.to_string())
    }
    Ok(ExtensionProposalReceiptV1 {
        parent_id: checked.parent.canonical_id().map_err(map_val_err)?,
        child_id: checked.child.canonical_id().map_err(map_val_err)?,
        demand_id: checked.demand.canonical_id().map_err(map_val_err)?,
        search_id: checked.search.canonical_id().map_err(map_val_err)?,
        grammar_id: checked.same_level_grammar.grammar_id.clone(),
        grammar_digest: checked
            .same_level_grammar
            .canonical_id()
            .map_err(map_val_err)?,
        frontier_id: checked.frontier.canonical_id().map_err(map_val_err)?,
        new_question_ids: new_questions,
        class_count_before: checked.parent.class_count(),
        class_count_after: checked.child.class_count(),
        authority_effect: "None".into(),
    })
}

// Origin: engine/crates_rs/core_solvers/src/router_structure_extension.rs
// Claim: urn:core:crates_rs:core-solvers:router-structure-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod canonical_hash_tests {
    use super::canonical_sha256;
    use serde_json::{json, Map, Value};

    #[test]
    fn canonical_sha256_sorts_nested_maps_without_reordering_arrays() {
        fn payload(reverse: bool) -> Value {
            let mut nested = Map::new();
            let pairs = if reverse {
                [("z", 1), ("a", 2)]
            } else {
                [("a", 2), ("z", 1)]
            };
            for (key, value) in pairs {
                nested.insert(key.into(), json!(value));
            }
            let array = Value::Array(vec![Value::Object(nested), json!(9)]);
            let mut outer = Map::new();
            if reverse {
                outer.insert("z".into(), json!(0));
                outer.insert("a".into(), array);
            } else {
                outer.insert("a".into(), array);
                outer.insert("z".into(), json!(0));
            }
            Value::Object(outer)
        }

        let first = payload(true);
        let second = payload(false);
        let original_bytes = serde_json::to_vec(&first).unwrap();
        assert_eq!(first, second);
        let digest = canonical_sha256("core.test", &first).unwrap();
        assert_eq!(digest, canonical_sha256("core.test", &second).unwrap());
        // SHA-256 of core.test:{"a":[{"a":2,"z":1},9],"z":0}.
        assert_eq!(
            digest,
            "sha256:313091eac13c51f1d7324dd237ffc4d68c1f72c87e258533feeced122b8c9d05"
        );
        assert_eq!(original_bytes, serde_json::to_vec(&first).unwrap());
        assert_ne!(
            canonical_sha256("core.test", &json!([1, 2])).unwrap(),
            canonical_sha256("core.test", &json!([2, 1])).unwrap()
        );
        assert_ne!(digest, canonical_sha256("core.other", &second).unwrap());
    }
}
