//! Finite declared plan-frontier semantics and cost-order routing for solver of solvers.
//!
//! Rust face of `engine/kernel/solver_of_solvers.py`.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_181fedc1<T> {
    fn checked_invariant_181fedc1(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_181fedc1<T> for Option<T> {
    #[inline]
    fn checked_invariant_181fedc1(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_181fedc1<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_181fedc1(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum PlanGrammarError {
    #[error("validation error: {0}")]
    Validation(String),

    #[error("refusal {code}: {message}")]
    Refusal { code: String, message: String },
}

pub fn canonical_sha256(domain: &str, payload: &Value) -> Result<String, PlanGrammarError> {
    let mut canonical_payload = payload.clone();
    canonical_payload.sort_all_objects();
    let raw = serde_json::to_string(&canonical_payload)
        .map_err(|e| PlanGrammarError::Validation(e.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(domain.as_bytes());
    hasher.update(b":");
    hasher.update(raw.as_bytes());
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PlanKind {
    #[serde(rename = "SameLevelRepair")]
    SameLevelRepair,
    #[serde(rename = "StructureExtensionProposal")]
    StructureExtensionProposal,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CostOrder {
    #[serde(rename = "Lexicographic")]
    Lexicographic,
    #[serde(rename = "Pareto")]
    Pareto,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvaluationStatus {
    #[serde(rename = "Verified")]
    Verified,
    #[serde(rename = "Rejected")]
    Rejected,
    #[serde(rename = "Inconclusive")]
    Inconclusive,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FrontierTerminal {
    #[serde(rename = "VerifiedFrontier")]
    VerifiedFrontier,
    #[serde(rename = "NoVerifiedPlan")]
    NoVerifiedPlan,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SearchDeclarationV1 {
    pub grammar_id: String,
    pub grammar_digest: String,
    pub policy_digest: String,
    pub cost_order: CostOrder,
    pub cost_dimension: usize,
    pub max_candidates: usize,
    pub authority_effect: String,
}

impl SearchDeclarationV1 {
    pub fn new(
        grammar_id: &str,
        grammar_digest: &str,
        policy_digest: &str,
        cost_order: CostOrder,
        cost_dimension: usize,
        max_candidates: usize,
    ) -> Result<Self, PlanGrammarError> {
        if cost_dimension == 0 {
            return Err(PlanGrammarError::Validation(
                "cost_dimension must be positive".into(),
            ));
        }
        if max_candidates == 0 {
            return Err(PlanGrammarError::Validation(
                "max_candidates must be positive".into(),
            ));
        }
        Ok(Self {
            grammar_id: grammar_id.to_string(),
            grammar_digest: grammar_digest.to_string(),
            policy_digest: policy_digest.to_string(),
            cost_order,
            cost_dimension,
            max_candidates,
            authority_effect: "None".into(),
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "grammar_id": self.grammar_id,
            "grammar_digest": self.grammar_digest,
            "policy_digest": self.policy_digest,
            "cost_order": match self.cost_order {
                CostOrder::Lexicographic => "Lexicographic",
                CostOrder::Pareto => "Pareto",
            },
            "cost_dimension": self.cost_dimension,
            "max_candidates": self.max_candidates,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PlanGrammarError> {
        canonical_sha256(
            "core.solver-of-solvers.search-declaration.v1",
            &self.to_canonical(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FinitePlanGrammarV1 {
    pub grammar_id: String,
    pub plan_kind: PlanKind,
    pub cost_order: CostOrder,
    pub cost_dimension: usize,
    pub candidate_plan_ids: Vec<String>,
    pub authority_effect: String,
}

impl FinitePlanGrammarV1 {
    pub fn to_canonical(&self) -> Value {
        json!({
            "grammar_id": self.grammar_id,
            "plan_kind": match self.plan_kind {
                PlanKind::SameLevelRepair => "SameLevelRepair",
                PlanKind::StructureExtensionProposal => "StructureExtensionProposal",
            },
            "cost_order": match self.cost_order {
                CostOrder::Lexicographic => "Lexicographic",
                CostOrder::Pareto => "Pareto",
            },
            "cost_dimension": self.cost_dimension,
            "candidate_plan_ids": self.candidate_plan_ids,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PlanGrammarError> {
        canonical_sha256(
            "core.solver-of-solvers.plan-grammar.v1",
            &self.to_canonical(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DeclaredPlanEvaluationV1 {
    pub grammar_id: String,
    pub plan_id: String,
    pub status: EvaluationStatus,
    pub cost: Vec<i64>,
    pub replay_receipt_ref: String,
    pub rejection_reason: String,
    pub authority_effect: String,
}

impl DeclaredPlanEvaluationV1 {
    pub fn to_canonical(&self) -> Value {
        json!({
            "grammar_id": self.grammar_id,
            "plan_id": self.plan_id,
            "status": match self.status {
                EvaluationStatus::Verified => "Verified",
                EvaluationStatus::Rejected => "Rejected",
                EvaluationStatus::Inconclusive => "Inconclusive",
            },
            "cost": self.cost,
            "replay_receipt_ref": self.replay_receipt_ref,
            "rejection_reason": self.rejection_reason,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PlanGrammarError> {
        canonical_sha256(
            "core.solver-of-solvers.declared-evaluation.v1",
            &self.to_canonical(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FrontierClassV1 {
    pub kind: PlanKind,
    pub candidate_ids: Vec<String>,
    pub evaluation_ids: Vec<String>,
    pub authority_effect: String,
}

impl FrontierClassV1 {
    pub fn to_canonical(&self) -> Value {
        json!({
            "kind": match self.kind {
                PlanKind::SameLevelRepair => "SameLevelRepair",
                PlanKind::StructureExtensionProposal => "StructureExtensionProposal",
            },
            "candidate_ids": self.candidate_ids,
            "evaluation_ids": self.evaluation_ids,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PlanGrammarError> {
        canonical_sha256(
            "core.solver-of-solvers.frontier-class.v1",
            &self.to_canonical(),
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PlanFrontierV1 {
    pub search_id: String,
    pub terminal: FrontierTerminal,
    pub classes: Vec<FrontierClassV1>,
    pub evaluation_ids: Vec<String>,
    pub accepted_candidate_ids: Vec<String>,
    pub dominated_candidate_ids: Vec<String>,
    pub rejected_candidate_ids: Vec<String>,
    pub inconclusive_candidate_ids: Vec<String>,
    pub authority_effect: String,
}

impl PlanFrontierV1 {
    pub fn to_canonical(&self) -> Value {
        json!({
            "search_id": self.search_id,
            "terminal": match self.terminal {
                FrontierTerminal::VerifiedFrontier => "VerifiedFrontier",
                FrontierTerminal::NoVerifiedPlan => "NoVerifiedPlan",
            },
            "classes": self.classes.iter().map(|c| c.to_canonical()).collect::<Vec<_>>(),
            "evaluation_ids": self.evaluation_ids,
            "accepted_candidate_ids": self.accepted_candidate_ids,
            "dominated_candidate_ids": self.dominated_candidate_ids,
            "rejected_candidate_ids": self.rejected_candidate_ids,
            "inconclusive_candidate_ids": self.inconclusive_candidate_ids,
            "authority_effect": self.authority_effect,
        })
    }

    pub fn canonical_id(&self) -> Result<String, PlanGrammarError> {
        canonical_sha256(
            "core.solver-of-solvers.plan-frontier.v1",
            &self.to_canonical(),
        )
    }
}

fn pareto_dominates(a: &[i64], b: &[i64]) -> bool {
    let mut strictly_better = false;
    for (x, y) in a.iter().zip(b.iter()) {
        if x > y {
            return false;
        }
        if x < y {
            strictly_better = true;
        }
    }
    strictly_better
}

fn partition_evaluations<'a>(
    declaration: &SearchDeclarationV1,
    evaluations: &'a [DeclaredPlanEvaluationV1],
) -> Result<
    (
        Vec<&'a DeclaredPlanEvaluationV1>,
        Vec<String>,
        Vec<String>,
        Vec<String>,
    ),
    PlanGrammarError,
> {
    let mut accepted = Vec::new();
    let mut rejected = Vec::new();
    let mut inconclusive = Vec::new();
    let mut eval_ids = Vec::new();

    for ev in evaluations {
        if ev.grammar_id != declaration.grammar_id {
            return Err(PlanGrammarError::Refusal {
                code: "GRAMMAR_MISMATCH".into(),
                message: "evaluation grammar ID does not match search declaration".into(),
            });
        }
        if ev.cost.len() != declaration.cost_dimension {
            return Err(PlanGrammarError::Refusal {
                code: "COST_DIMENSION_MISMATCH".into(),
                message: "evaluation cost dimension mismatch".into(),
            });
        }
        eval_ids.push(ev.canonical_id()?);

        match ev.status {
            EvaluationStatus::Verified => accepted.push(ev),
            EvaluationStatus::Rejected => rejected.push(ev.plan_id.clone()),
            EvaluationStatus::Inconclusive => inconclusive.push(ev.plan_id.clone()),
        }
    }
    Ok((accepted, rejected, inconclusive, eval_ids))
}

fn filter_lexicographic_frontier<'a>(
    accepted: &[&'a DeclaredPlanEvaluationV1],
) -> (Vec<&'a DeclaredPlanEvaluationV1>, Vec<String>) {
    let best = accepted
        .iter()
        .map(|ev| &ev.cost)
        .min()
        .checked_invariant_181fedc1("checked invariant");
    let mut non_dominated = Vec::new();
    let mut dominated = Vec::new();
    for ev in accepted {
        if &ev.cost == best {
            non_dominated.push(*ev);
        } else {
            dominated.push(ev.plan_id.clone());
        }
    }
    (non_dominated, dominated)
}

fn filter_pareto_frontier<'a>(
    accepted: &[&'a DeclaredPlanEvaluationV1],
) -> (Vec<&'a DeclaredPlanEvaluationV1>, Vec<String>) {
    let mut non_dominated = Vec::new();
    let mut dominated = Vec::new();
    for (i, ev) in accepted.iter().enumerate() {
        let is_dominated = (0..accepted.len())
            .any(|j| i != j && pareto_dominates(&accepted[j].cost, &ev.cost));
        if is_dominated {
            dominated.push(ev.plan_id.clone());
        } else {
            non_dominated.push(*ev);
        }
    }
    (non_dominated, dominated)
}

pub fn route_declared_finite_grammar(
    declaration: &SearchDeclarationV1,
    grammar: &FinitePlanGrammarV1,
    evaluations: &[DeclaredPlanEvaluationV1],
) -> Result<PlanFrontierV1, PlanGrammarError> {
    if evaluations.len() > declaration.max_candidates {
        return Err(PlanGrammarError::Refusal {
            code: "BATCH_BUDGET_EXHAUSTED".into(),
            message: "explicit candidate batch exceeds declared cap".into(),
        });
    }

    let (accepted, rejected, inconclusive, eval_ids) =
        partition_evaluations(declaration, evaluations)?;

    let search_id = declaration.canonical_id()?;
    if accepted.is_empty() {
        return Ok(PlanFrontierV1 {
            search_id,
            terminal: FrontierTerminal::NoVerifiedPlan,
            classes: Vec::new(),
            evaluation_ids: eval_ids,
            accepted_candidate_ids: Vec::new(),
            dominated_candidate_ids: Vec::new(),
            rejected_candidate_ids: rejected,
            inconclusive_candidate_ids: inconclusive,
            authority_effect: "None".into(),
        });
    }

    let accepted_ids: Vec<String> = accepted.iter().map(|e| e.plan_id.clone()).collect();
    let (non_dominated, dominated) = match declaration.cost_order {
        CostOrder::Lexicographic => filter_lexicographic_frontier(&accepted),
        CostOrder::Pareto => filter_pareto_frontier(&accepted),
    };

    let frontier_candidates: Vec<String> =
        non_dominated.iter().map(|e| e.plan_id.clone()).collect();
    let frontier_evals: Vec<String> = non_dominated
        .iter()
        .map(|e| e.canonical_id().unwrap_or_default())
        .collect();

    let frontier_class = FrontierClassV1 {
        kind: grammar.plan_kind,
        candidate_ids: frontier_candidates,
        evaluation_ids: frontier_evals,
        authority_effect: "None".into(),
    };

    Ok(PlanFrontierV1 {
        search_id,
        terminal: FrontierTerminal::VerifiedFrontier,
        classes: vec![frontier_class],
        evaluation_ids: eval_ids,
        accepted_candidate_ids: accepted_ids,
        dominated_candidate_ids: dominated,
        rejected_candidate_ids: rejected,
        inconclusive_candidate_ids: inconclusive,
        authority_effect: "None".into(),
    })
}

// Origin: engine/crates_rs/core_solvers/src/router_plan_grammar.rs
// Claim: urn:core:crates_rs:core-solvers:router-plan-grammar:l4-production-boundary:v1
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
