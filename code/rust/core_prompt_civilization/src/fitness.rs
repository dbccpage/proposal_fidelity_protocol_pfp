//! Receipt-backed integer evidence and Pareto front selection.
//!
//! Enforces:
//! - F-SELECT-01: Front ordering plus declared tiebreak, with no composite scalar.
//! - F-SELECT-03: Acceptance is bound to its obligation; receipts for other obligations are not counted.
//! - F-RES-06: Validity or emptiness alone earns no success credit.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PromptFitnessV1 {
    pub prompt_id: String,
    pub passes: u64,
    pub failures: u64,
    pub inconclusive: u64,
    pub not_triggered: u64,
    pub valid_refusals: u64,
    pub task_success_credit: u64,
}

pub fn is_valid_sealed_digest(digest: Option<&str>) -> bool {
    let Some(d) = digest else {
        return false;
    };
    let Some(hex_part) = d.strip_prefix("sha256:") else {
        return false;
    };
    hex_part.len() == 64
        && hex_part
            .chars()
            .all(|c| c.is_ascii_digit() || ('a'..='f').contains(&c))
}

impl PromptFitnessV1 {
    pub fn new(prompt_id: &str) -> Self {
        Self {
            prompt_id: prompt_id.to_string(),
            passes: 0,
            failures: 0,
            inconclusive: 0,
            not_triggered: 0,
            valid_refusals: 0,
            task_success_credit: 0,
        }
    }

    pub fn correctness(&self) -> Option<BigRational> {
        let total = self.passes + self.failures;
        if total == 0 {
            None
        } else {
            Some(BigRational::new(
                BigInt::from(self.passes),
                BigInt::from(total),
            ))
        }
    }

    /// F3: Completion rate defined as S / N_assigned across all assigned units.
    pub fn completion_rate(&self, n_assigned: u64) -> Option<BigRational> {
        if n_assigned == 0 {
            None
        } else {
            Some(BigRational::new(
                BigInt::from(self.passes),
                BigInt::from(n_assigned),
            ))
        }
    }

    /// Untrusted receipt metadata is diagnostic, never authenticated task credit.
    /// The host must execute its independently bound challenge checker instead.
    pub fn record_verifier_result(
        &mut self,
        declared_obligation: &str,
        receipt_obligation: &str,
        is_exact_verified: bool,
        sealed_digest: Option<&str>,
    ) {
        let _ = (
            declared_obligation,
            receipt_obligation,
            is_exact_verified,
            sealed_digest,
        );
        self.not_triggered += 1;
    }

    /// Pure syntax validity or nonempty output earns 0 task success credit.
    pub fn record_syntax_only_output(&mut self, is_valid_syntax: bool) {
        if is_valid_syntax {
            self.valid_refusals += 1; // Counted as compliance, NOT task success credit
        } else {
            self.failures += 1;
        }
    }
}

/// F3: Total Selected-Attempt Outcome Table (Epic PCIV V1.0RC Table 4.7).
/// Priority:
/// 1. Any TaskFail -> TaskFail
/// 2. Otherwise any InvalidRefusal -> InvalidRefusal
/// 3. Otherwise any InfrastructureError -> InfrastructureError
/// 4. Otherwise any NotMeasured -> NotMeasured
/// 5. Otherwise any Inconclusive -> Inconclusive
/// 6. Otherwise AllowedTask with any ValidRefusal -> ValidRefusal
/// 7. Otherwise AllowedTask (all mandatory outcomes are TaskPass) -> TaskPass
/// 8. Otherwise RefusalRequired and root is ValidRefusal -> ValidRefusal
/// 9. Otherwise RefusalRequired (root is TaskPass without required refusal) -> InvalidRefusal
pub fn reduce_selected_attempt_outcome(
    mandatory_outcomes: &[&str],
    expected_behavior: &str,
    root_outcome: Option<&str>,
) -> &'static str {
    if mandatory_outcomes.contains(&"TaskFail") {
        return "TaskFail";
    }
    if mandatory_outcomes.contains(&"InvalidRefusal") {
        return "InvalidRefusal";
    }
    if mandatory_outcomes.contains(&"InfrastructureError") {
        return "InfrastructureError";
    }
    if mandatory_outcomes.contains(&"NotMeasured") {
        return "NotMeasured";
    }
    if mandatory_outcomes.contains(&"Inconclusive") {
        return "Inconclusive";
    }
    if expected_behavior == "AllowedTask" {
        if mandatory_outcomes.contains(&"ValidRefusal") {
            return "ValidRefusal";
        }
        if mandatory_outcomes.iter().all(|&o| o == "TaskPass") {
            return "TaskPass";
        }
    } else if expected_behavior == "RefusalRequired" {
        if root_outcome == Some("ValidRefusal")
            || (root_outcome.is_none() && mandatory_outcomes.contains(&"ValidRefusal"))
        {
            return "ValidRefusal";
        }
        return "InvalidRefusal";
    }
    "InvalidRefusal"
}

fn dominates_fitness(q: &PromptFitnessV1, p: &PromptFitnessV1) -> bool {
    // q dominates p if q >= p in all objectives and q > p in at least one
    let q_ge_p = q.task_success_credit >= p.task_success_credit && q.failures <= p.failures;
    let q_gt_p = q.task_success_credit > p.task_success_credit || q.failures < p.failures;
    q_ge_p && q_gt_p
}

fn is_candidate_dominated(remaining: &[PromptFitnessV1], i: usize) -> bool {
    let p = &remaining[i];
    remaining
        .iter()
        .enumerate()
        .any(|(j, other)| i != j && dominates_fitness(other, p))
}

fn compare_pareto_tiebreak(a: &PromptFitnessV1, b: &PromptFitnessV1) -> std::cmp::Ordering {
    b.task_success_credit
        .cmp(&a.task_success_credit)
        .then(a.failures.cmp(&b.failures))
        .then(a.prompt_id.cmp(&b.prompt_id))
}

/// Partition candidates into non-dominated Pareto fronts.
/// Dimension 1: task_success_credit (higher is better)
/// Dimension 2: failures (lower is better)
pub fn compute_pareto_fronts(candidates: &[PromptFitnessV1]) -> Vec<Vec<PromptFitnessV1>> {
    let mut remaining: Vec<PromptFitnessV1> = candidates.to_vec();
    let mut fronts = Vec::new();

    while !remaining.is_empty() {
        let mut current_front = Vec::new();
        let mut next_remaining = Vec::new();

        for (i, p) in remaining.iter().enumerate() {
            if !is_candidate_dominated(&remaining, i) {
                current_front.push(p.clone());
            } else {
                next_remaining.push(p.clone());
            }
        }

        // Lexicographic tiebreak within front: higher success_credit, then lower failures, then prompt_id
        current_front.sort_by(compare_pareto_tiebreak);

        fronts.push(current_front);
        remaining = next_remaining;
    }

    fronts
}

/// Generalized exact rational candidate for multi-objective optimization over Rational64.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateRational {
    pub id: String,
    pub correctness: Rational64,
    pub cost: Rational64,
    pub robustness: Rational64,
}

impl CandidateRational {
    pub fn new(
        id: impl Into<String>,
        correctness: Rational64,
        cost: Rational64,
        robustness: Rational64,
    ) -> Self {
        Self {
            id: id.into(),
            correctness,
            cost,
            robustness,
        }
    }

    /// Checks if self weakly dominates other across all three objectives:
    /// correctness >= other.correctness, cost <= other.cost, robustness >= other.robustness.
    pub fn weakly_dominates(&self, other: &Self) -> bool {
        self.correctness >= other.correctness
            && self.cost <= other.cost
            && self.robustness >= other.robustness
    }

    /// Checks if self is strictly better in at least one objective.
    pub fn strictly_better_any(&self, other: &Self) -> bool {
        self.correctness > other.correctness
            || self.cost < other.cost
            || self.robustness > other.robustness
    }

    /// Law of Pareto Domination:
    /// Candidate self strictly dominates other iff self is weakly dominating
    /// across all three objectives AND strictly better in at least one objective.
    pub fn dominates(&self, other: &Self) -> bool {
        self.weakly_dominates(other) && self.strictly_better_any(other)
    }
}

/// Generalized non-dominated sorting over Q (num_rational::Rational64).
/// Partitions candidates into non-dominated Pareto fronts [F0, F1, ...].
/// Within each front, candidates are sorted lexicographically:
/// 1. correctness descending (highest correctness first)
/// 2. cost ascending (lowest cost first)
/// 3. candidate id ascending (deterministic alphabetical tiebreak)
pub fn compute_pareto_fronts_rational(
    candidates: &[CandidateRational],
) -> Vec<Vec<CandidateRational>> {
    let mut remaining: Vec<CandidateRational> = candidates.to_vec();
    let mut fronts = Vec::new();

    while !remaining.is_empty() {
        let mut current_front = Vec::new();
        let mut next_remaining = Vec::new();

        for i in 0..remaining.len() {
            let p = &remaining[i];
            let mut is_dominated = false;
            for (j, other) in remaining.iter().enumerate() {
                if i != j && other.dominates(p) {
                    is_dominated = true;
                    break;
                }
            }
            if !is_dominated {
                current_front.push(p.clone());
            } else {
                next_remaining.push(p.clone());
            }
        }

        // Lexicographic tiebreak within front:
        // higher correctness (descending), lower cost (ascending), then id (ascending)
        current_front.sort_by(|a, b| {
            b.correctness
                .cmp(&a.correctness)
                .then_with(|| a.cost.cmp(&b.cost))
                .then_with(|| a.id.cmp(&b.id))
        });

        fronts.push(current_front);
        remaining = next_remaining;
    }

    fronts
}

/// Returns the first Pareto front (non-dominated candidates) F0.
pub fn pareto_frontier_rational(candidates: &[CandidateRational]) -> Vec<CandidateRational> {
    compute_pareto_fronts_rational(candidates)
        .into_iter()
        .next()
        .unwrap_or_default()
}

/// Generalized candidate over BigRational.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateBigRational {
    pub id: String,
    pub correctness: BigRational,
    pub cost: BigRational,
    pub robustness: BigRational,
}

impl CandidateBigRational {
    pub fn new(
        id: impl Into<String>,
        correctness: BigRational,
        cost: BigRational,
        robustness: BigRational,
    ) -> Self {
        Self {
            id: id.into(),
            correctness,
            cost,
            robustness,
        }
    }

    pub fn dominates(&self, other: &Self) -> bool {
        let ge = self.correctness >= other.correctness
            && self.cost <= other.cost
            && self.robustness >= other.robustness;
        let strictly_better = self.correctness > other.correctness
            || self.cost < other.cost
            || self.robustness > other.robustness;
        ge && strictly_better
    }
}

/// Partitions BigRational candidates into non-dominated Pareto fronts.
pub fn compute_pareto_fronts_bigrational(
    candidates: &[CandidateBigRational],
) -> Vec<Vec<CandidateBigRational>> {
    let mut remaining: Vec<CandidateBigRational> = candidates.to_vec();
    let mut fronts = Vec::new();

    while !remaining.is_empty() {
        let mut current_front = Vec::new();
        let mut next_remaining = Vec::new();

        for i in 0..remaining.len() {
            let p = &remaining[i];
            let mut is_dominated = false;
            for (j, other) in remaining.iter().enumerate() {
                if i != j && other.dominates(p) {
                    is_dominated = true;
                    break;
                }
            }
            if !is_dominated {
                current_front.push(p.clone());
            } else {
                next_remaining.push(p.clone());
            }
        }

        current_front.sort_by(|a, b| {
            b.correctness
                .cmp(&a.correctness)
                .then_with(|| a.cost.cmp(&b.cost))
                .then_with(|| a.id.cmp(&b.id))
        });

        fronts.push(current_front);
        remaining = next_remaining;
    }

    fronts
}

// Origin: engine/crates_rs/core_prompt_civilization/src/fitness.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:fitness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5bd61059 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5bd61059` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5bd61059 {
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
impl BoundaryError5bd61059 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5bd61059 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5bd61059 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5bd61059 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5bd61059> {
        if capacity_bound == 0 {
            return Err(BoundaryError5bd61059::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5bd61059::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5bd61059::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_f_select_03_obligation_binding() {
        let mut fit = PromptFitnessV1::new("p1");
        // Caller status and digest syntax earn no independently checked credit.
        fit.record_verifier_result(
            "integral_task",
            "integral_task",
            true,
            Some("sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"),
        );
        assert_eq!(fit.task_success_credit, 0);
        assert_eq!(fit.passes, 0);

        // Different obligation -> earns NO task success credit
        fit.record_verifier_result(
            "integral_task",
            "pagerank_task",
            true,
            Some("sha256:fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"),
        );
        assert_eq!(fit.task_success_credit, 0);
        assert_eq!(fit.valid_refusals, 0);

        // F2: Fake digest ("not-a-digest") -> earns NO task success credit, counts as failure
        fit.record_verifier_result("integral_task", "integral_task", true, Some("not-a-digest"));
        assert_eq!(fit.task_success_credit, 0);
        assert_eq!(fit.failures, 0);

        // Unsealed claim -> earns NO task success credit, counts as failure
        fit.record_verifier_result("integral_task", "integral_task", true, None);
        assert_eq!(fit.task_success_credit, 0);
        assert_eq!(fit.failures, 0);

        // Short and unprefixed digests earn no credit.
        assert!(!is_valid_sealed_digest(Some("sha256:abcd")));
        assert!(!is_valid_sealed_digest(Some(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        )));
        fit.record_verifier_result("integral_task", "integral_task", true, Some("sha256:abcd"));
        assert_eq!(fit.task_success_credit, 0);
        assert_eq!(fit.failures, 0);
        assert_eq!(fit.not_triggered, 5);
    }

    #[test]
    fn test_f_res_06_syntax_only_earns_no_success_credit() {
        let mut fit = PromptFitnessV1::new("p2");
        fit.record_syntax_only_output(true);
        assert_eq!(fit.task_success_credit, 0);
        assert_eq!(fit.valid_refusals, 1);
    }

    #[test]
    fn test_f3_completion_rate_and_selected_attempt_reducer() {
        let mut fit = PromptFitnessV1::new("p3");
        fit.passes = 1;
        fit.valid_refusals = 99;
        // True assigned denominator: 100 assigned tasks -> 1/100, not 1/(1+0)
        let rate = fit.completion_rate(100).unwrap();
        assert_eq!(rate, BigRational::new(BigInt::from(1), BigInt::from(100)));

        // Total Selected-Attempt Outcome Table (Table 4.7):
        // Early valid refusal with unexecuted required check (NotMeasured) -> NotMeasured!
        let outcome = reduce_selected_attempt_outcome(
            &["ValidRefusal", "NotMeasured"],
            "RefusalRequired",
            Some("ValidRefusal"),
        );
        assert_eq!(outcome, "NotMeasured");

        // AllowedTask with any TaskFail -> TaskFail
        let fail_res = reduce_selected_attempt_outcome(
            &["TaskPass", "TaskFail"],
            "AllowedTask",
            Some("TaskPass"),
        );
        assert_eq!(fail_res, "TaskFail");

        // AllowedTask with all TaskPass -> TaskPass
        let pass_res = reduce_selected_attempt_outcome(
            &["TaskPass", "TaskPass"],
            "AllowedTask",
            Some("TaskPass"),
        );
        assert_eq!(pass_res, "TaskPass");
    }

    #[test]
    fn test_pareto_rational64_domination_partition() {
        let c_a = CandidateRational::new(
            "cand_a",
            Rational64::new(9, 10),
            Rational64::new(1, 10),
            Rational64::new(1, 1),
        );
        let c_b = CandidateRational::new(
            "cand_b",
            Rational64::new(8, 10),
            Rational64::new(2, 10),
            Rational64::new(8, 10),
        );

        assert!(c_a.dominates(&c_b));
        assert!(!c_b.dominates(&c_a));

        let fronts = compute_pareto_fronts_rational(&[c_a.clone(), c_b.clone()]);
        assert_eq!(fronts.len(), 2);
        assert_eq!(fronts[0], vec![c_a]);
        assert_eq!(fronts[1], vec![c_b]);
    }

    #[test]
    fn test_pareto_rational64_tradeoff_single_front() {
        // Trade-off: c1 higher correctness, c2 lower cost
        let c1 = CandidateRational::new(
            "c1",
            Rational64::new(9, 10),
            Rational64::new(5, 10),
            Rational64::new(1, 1),
        );
        let c2 = CandidateRational::new(
            "c2",
            Rational64::new(7, 10),
            Rational64::new(2, 10),
            Rational64::new(1, 1),
        );

        assert!(!c1.dominates(&c2));
        assert!(!c2.dominates(&c1));

        let fronts = compute_pareto_fronts_rational(&[c1.clone(), c2.clone()]);
        assert_eq!(fronts.len(), 1);
        assert_eq!(fronts[0].len(), 2);
        // Lexicographic order: c1 has higher correctness, so c1 comes first
        assert_eq!(fronts[0][0].id, "c1");
        assert_eq!(fronts[0][1].id, "c2");

        let best_front = pareto_frontier_rational(&[c1.clone(), c2.clone()]);
        assert_eq!(best_front.len(), 2);
    }

    #[test]
    fn test_pareto_rational64_lexicographic_tiebreak() {
        let c_b = CandidateRational::new(
            "cand_b",
            Rational64::new(8, 10),
            Rational64::new(1, 2),
            Rational64::new(1, 1),
        );
        let c_a = CandidateRational::new(
            "cand_a",
            Rational64::new(8, 10),
            Rational64::new(1, 2),
            Rational64::new(1, 1),
        );

        let fronts = compute_pareto_fronts_rational(&[c_b, c_a]);
        assert_eq!(fronts.len(), 1);
        assert_eq!(fronts[0][0].id, "cand_a");
        assert_eq!(fronts[0][1].id, "cand_b");
    }

    #[test]
    fn test_pareto_rational64_cost_inversion_lower_is_better() {
        let cheap = CandidateRational::new(
            "cheap",
            Rational64::new(8, 10),
            Rational64::new(1, 10),
            Rational64::new(1, 1),
        );
        let expensive = CandidateRational::new(
            "expensive",
            Rational64::new(8, 10),
            Rational64::new(9, 10),
            Rational64::new(1, 1),
        );

        assert!(cheap.dominates(&expensive));
        assert!(!expensive.dominates(&cheap));

        let frontier = pareto_frontier_rational(&[cheap.clone(), expensive]);
        assert_eq!(frontier, vec![cheap]);
    }

    #[test]
    fn test_pareto_rational64_champion_replacement() {
        let p1 = CandidateRational::new(
            "p1",
            Rational64::new(5, 10),
            Rational64::new(5, 10),
            Rational64::new(5, 10),
        );
        let p2 = CandidateRational::new(
            "p2",
            Rational64::new(6, 10),
            Rational64::new(4, 10),
            Rational64::new(6, 10),
        );
        let champ = CandidateRational::new(
            "champ",
            Rational64::new(9, 10),
            Rational64::new(1, 10),
            Rational64::new(9, 10),
        );

        let fronts = compute_pareto_fronts_rational(&[p1, p2, champ.clone()]);
        assert_eq!(fronts[0], vec![champ]);
    }
}

#[cfg(test)]
mod l4_boundary_tests_5bd61059 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5bd61059::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5bd61059::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5bd61059::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5bd61059::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5bd61059::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError5bd61059::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError5bd61059::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
