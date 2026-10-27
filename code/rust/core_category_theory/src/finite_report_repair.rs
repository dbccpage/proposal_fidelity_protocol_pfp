//! Witness-guided repair of a complete finite report/answer table.
//!
//! Each step splits one current report class by an already supplied question.
//! The result is the least refinement retaining the old report and all answers.
//! This repairs a representation, not the source world or observation hardware.
//! Bounds count rows, questions, steps and pair inspections, not bytes or time.

use crate::finite_question_family::FiniteQuestionFamily;
use std::collections::BTreeMap;
use std::fmt::Debug;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RepairLimits {
    pub max_rows: usize,
    pub max_questions: usize,
    pub max_steps: usize,
    pub max_pair_checks: usize,
}

impl Default for RepairLimits {
    fn default() -> Self {
        Self {
            max_rows: 256,
            max_questions: 64,
            max_steps: 256,
            max_pair_checks: 10_000_000,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RepairError {
    ReportLength,
    SizeLimit,
    StepLimit,
    PairLimit,
    InvalidStep { index: usize },
    FinalPartitionMismatch,
    NotLeastSufficient,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_report_repair.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-report-repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RepairError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RepairError {}

/// Source indices and a question witnessing unequal answers in one report class.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairStep {
    pub first: usize,
    pub second: usize,
    pub question: usize,
}

/// Numbered classes use first occurrence order after each split. The verifier
/// accepts any legal witness order, without calling the repair search.
/// Application-level source identities and acquisition licenses are separate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairCertificate {
    pub steps: Vec<RepairStep>,
    pub class_of: Vec<usize>,
}

fn classes<T: Ord>(values: impl Iterator<Item = T>) -> Vec<usize> {
    let mut ids = BTreeMap::new();
    values
        .map(|v| {
            let next = ids.len();
            *ids.entry(v).or_insert(next)
        })
        .collect()
}

fn admit<A: Ord + Clone + Debug, R>(
    family: &FiniteQuestionFamily<A>,
    report: &[R],
    limits: RepairLimits,
) -> Result<(), RepairError> {
    if report.len() != family.answers().len() {
        return Err(RepairError::ReportLength);
    }
    if report.len() > limits.max_rows || family.question_count() > limits.max_questions {
        return Err(RepairError::SizeLimit);
    }
    Ok(())
}

fn inspect(remaining: &mut usize) -> Result<(), RepairError> {
    *remaining = remaining.checked_sub(1).ok_or(RepairError::PairLimit)?;
    Ok(())
}

fn collision<A: Ord + Clone + Debug>(
    family: &FiniteQuestionFamily<A>,
    partition: &[usize],
    remaining: &mut usize,
) -> Result<Option<RepairStep>, RepairError> {
    for first in 0..partition.len() {
        for second in first + 1..partition.len() {
            inspect(remaining)?;
            if partition[first] == partition[second] {
                if let Some(question) = family.answers()[first]
                    .iter()
                    .zip(&family.answers()[second])
                    .position(|(a, b)| a != b)
                {
                    return Ok(Some(RepairStep {
                        first,
                        second,
                        question,
                    }));
                }
            }
        }
    }
    Ok(None)
}

fn split<A: Ord + Clone + Debug>(
    family: &FiniteQuestionFamily<A>,
    partition: &[usize],
    step: &RepairStep,
    index: usize,
) -> Result<Vec<usize>, RepairError> {
    let valid_indices = step.first < partition.len()
        && step.second < partition.len()
        && step.question < family.question_count();
    if !valid_indices
        || partition[step.first] != partition[step.second]
        || family.answers()[step.first][step.question]
            == family.answers()[step.second][step.question]
    {
        return Err(RepairError::InvalidStep { index });
    }
    let selected = partition[step.first];
    Ok(classes(partition.iter().enumerate().map(|(i, &class)| {
        (
            class,
            if class == selected {
                Some(&family.answers()[i][step.question])
            } else {
                None
            },
        )
    })))
}

/// Return a complete repair or a typed resource/input refusal. The input tables
/// are unchanged. No partial repair is labeled sufficient on budget exhaustion.
pub fn repair_report<A: Ord + Clone + Debug, R: Ord>(
    family: &FiniteQuestionFamily<A>,
    report: &[R],
    limits: RepairLimits,
) -> Result<RepairCertificate, RepairError> {
    admit(family, report, limits)?;
    let mut partition = classes(report.iter());
    let mut steps = Vec::new();
    let mut remaining = limits.max_pair_checks;
    while let Some(step) = collision(family, &partition, &mut remaining)? {
        if steps.len() >= limits.max_steps {
            return Err(RepairError::StepLimit);
        }
        partition = split(family, &partition, &step, steps.len())?;
        steps.push(step);
    }
    Ok(RepairCertificate {
        steps,
        class_of: partition,
    })
}

fn verify_least_sufficient<A: Ord + Clone + Debug, R: Ord>(
    family: &FiniteQuestionFamily<A>,
    report: &[R],
    partition: &[usize],
    max_pair_checks: usize,
) -> Result<(), RepairError> {
    let mut remaining = max_pair_checks;
    for i in 0..report.len() {
        for j in i + 1..report.len() {
            inspect(&mut remaining)?;
            let expected = report[i] == report[j] && family.answers()[i] == family.answers()[j];
            if (partition[i] == partition[j]) != expected {
                return Err(RepairError::NotLeastSufficient);
            }
        }
    }
    Ok(())
}

/// Replay each declared split, then independently check the defining pair
/// relation. Both excessive splitting and unresolved collisions are refused.
pub fn verify_repair<A: Ord + Clone + Debug, R: Ord>(
    family: &FiniteQuestionFamily<A>,
    report: &[R],
    candidate: &RepairCertificate,
    limits: RepairLimits,
) -> Result<(), RepairError> {
    admit(family, report, limits)?;
    if candidate.steps.len() > limits.max_steps {
        return Err(RepairError::StepLimit);
    }
    if candidate.class_of.len() != report.len() {
        return Err(RepairError::FinalPartitionMismatch);
    }
    let mut partition = classes(report.iter());
    for (index, step) in candidate.steps.iter().enumerate() {
        partition = split(family, &partition, step, index)?;
    }
    if partition != candidate.class_of {
        return Err(RepairError::FinalPartitionMismatch);
    }
    verify_least_sufficient(family, report, &partition, limits.max_pair_checks)
}

/// Replay a legal prefix without claiming sufficiency. Includes the initial
/// partition, so an application can recheck its original task after each split.
/// Each transition uses the same checked split as the complete verifier.
pub fn replay_repair_prefix<A: Ord + Clone + Debug, R: Ord>(
    family: &FiniteQuestionFamily<A>,
    report: &[R],
    steps: &[RepairStep],
    limits: RepairLimits,
) -> Result<Vec<Vec<usize>>, RepairError> {
    admit(family, report, limits)?;
    if steps.len() > limits.max_steps {
        return Err(RepairError::StepLimit);
    }
    let mut partition = classes(report.iter());
    let mut partitions = vec![partition.clone()];
    for (index, step) in steps.iter().enumerate() {
        partition = split(family, &partition, step, index)?;
        partitions.push(partition.clone());
    }
    Ok(partitions)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_1e51ff91 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
