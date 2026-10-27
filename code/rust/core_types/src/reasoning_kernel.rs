#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReasoningProblem {
    pub givens: Vec<String>,
    pub goal: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReasoningFrame {
    pub givens: Vec<String>,
    pub goal: String,
    pub tokens: Vec<String>,
    pub entities: Vec<String>,
    pub quantities: Vec<i64>,
    pub domains: Vec<ReasoningDomain>,
    pub subgoals: Vec<String>,
    pub operator_plan: Vec<ReasoningOperatorCall>,
    pub lemmas: Vec<String>,
    pub cases: Vec<String>,
    pub contradictions: Vec<String>,
    pub analogies: Vec<String>,
    pub trace: Vec<String>,
}

impl ReasoningFrame {
    pub fn from_problem(problem: &ReasoningProblem) -> Self {
        Self {
            givens: problem.givens.clone(),
            goal: problem.goal.clone(),
            tokens: Vec::new(),
            entities: Vec::new(),
            quantities: Vec::new(),
            domains: Vec::new(),
            subgoals: Vec::new(),
            operator_plan: Vec::new(),
            lemmas: Vec::new(),
            cases: Vec::new(),
            contradictions: Vec::new(),
            analogies: Vec::new(),
            trace: vec!["frame_initialized".to_string()],
        }
    }

    /// Admit a quantity ledger whose given integers sum to the goal quantity.
    pub fn admit_quantities(
        &mut self,
        quantities: &[i64],
        goal_quantity: i64,
    ) -> Result<i64, QuantityError> {
        let total = conserve(quantities, goal_quantity)?;
        self.quantities = quantities.to_vec();
        self.trace.push("quantities_conserved".to_string());
        Ok(total)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum QuantityError {
    Overflow,
    NotConserved { total: i64, goal: i64 },
}

impl std::fmt::Display for QuantityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Overflow => write!(formatter, "quantity sum overflowed i64"),
            Self::NotConserved { total, goal } => {
                write!(formatter, "quantity sum {total} is not the goal {goal}")
            }
        }
    }
}

impl std::error::Error for QuantityError {}

/// Sum of the given quantities equals the goal quantity.
pub fn conserve(quantities: &[i64], goal: i64) -> Result<i64, QuantityError> {
    let mut total = 0i64;
    for quantity in quantities {
        total = total.checked_add(*quantity).ok_or(QuantityError::Overflow)?;
    }
    if total != goal {
        return Err(QuantityError::NotConserved { total, goal });
    }
    Ok(total)
}

// Origin: engine/crates_rs/core_types/src/reasoning_kernel.rs
// Claim: urn:core:crates_rs:core-types:reasoning-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod quantity_tests {
    use super::*;

    fn taken(result: Result<i64, QuantityError>) -> i64 {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn givens_that_sum_to_the_goal_are_admitted() {
        let mut frame = ReasoningFrame::from_problem(&ReasoningProblem {
            givens: vec!["2".to_owned(), "3".to_owned()],
            goal: "5".to_owned(),
        });
        let total = taken(frame.admit_quantities(&[2, 3], 5));
        assert_eq!(total, 5);
        assert_eq!(frame.quantities, vec![2, 3]);
    }

    #[test]
    fn a_broken_sum_is_refused() {
        assert!(matches!(
            conserve(&[2, 2], 5),
            Err(QuantityError::NotConserved { total: 4, goal: 5 })
        ));
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum ReasoningDomain {
    Algebra,
    Geometry,
    Calculus,
    Probability,
    Logic,
    Algorithms,
    Physics,
    Language,
    Planning,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReasoningOperatorCall {
    pub lambda_id: u16,
    pub name: &'static str,
    pub role: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReasoningAnswer {
    pub conclusion: String,
    pub support: Vec<String>,
    pub unresolved: Vec<String>,
    pub trace: Vec<String>,
}
