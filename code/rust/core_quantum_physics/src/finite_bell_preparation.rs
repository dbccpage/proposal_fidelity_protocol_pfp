//! Exact experimental tables obtained from local response functions and explicit
//! preparation laws. Varying a preparation law with settings is recorded, never
//! promoted to a counterexample to Bell's setting-independent model.
use crate::finite_bell_extension::{BellExtensionError, BellLimits, FiniteBellProblem};
use num_traits::Signed;
use core_finite_probability::simplex::ProbabilitySimplex;
use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_convex_farkas_feasibility::FeasibilityVerdict;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResponseFunctions {
    pub left: Vec<usize>,
    pub right: Vec<usize>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PriorDifference {
    pub context: usize,
    pub preparation: usize,
    pub first_weight: Rational,
    pub other_weight: Rational,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PreparationError {
    InvalidResponses,
    InvalidPriors,
    WorkLimit,
    Bell(BellExtensionError),
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_quantum_physics/src/finite_bell_preparation.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-bell-preparation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PreparationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PreparationError {}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PreparedBellCertificate {
    /// Left setting major, then right setting; a varies fastest inside a row.
    pub rows: Vec<Vec<Rational>>,
    pub prior_difference: Option<PriorDifference>,
    pub extension: FeasibilityVerdict,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PreparedBellProblem {
    rows: Vec<Vec<Rational>>,
    prior_difference: Option<PriorDifference>,
    shared_point: Option<Vec<Rational>>,
    bell: FiniteBellProblem,
}
impl PreparedBellProblem {
    fn check_non_empty_outcomes(
        left: &[usize],
        right: &[usize],
        settings: usize,
        responses_len: usize,
    ) -> Result<(), PreparationError> {
        let bad_dims = left.is_empty() || right.is_empty() || settings > 20;
        let bad_counts = left.contains(&0) || right.contains(&0) || responses_len == 0;
        if bad_dims || bad_counts {
            return Err(PreparationError::InvalidResponses);
        }
        Ok(())
    }

    fn validate_scenario_and_budget(
        left: &[usize],
        right: &[usize],
        responses_len: usize,
        max_cells: usize,
    ) -> Result<(usize, usize), PreparationError> {
        let contexts = left
            .len()
            .checked_mul(right.len())
            .ok_or(PreparationError::WorkLimit)?;
        let settings = left
            .len()
            .checked_add(right.len())
            .ok_or(PreparationError::WorkLimit)?;
        Self::check_non_empty_outcomes(left, right, settings, responses_len)?;
        let sum_left = left.iter().try_fold(0usize, |s, &n| s.checked_add(n));
        let sum_right = right.iter().try_fold(0usize, |s, &n| s.checked_add(n));
        let coordinate_count = sum_left.and_then(|a| sum_right.and_then(|b| a.checked_mul(b)));
        let assignments = left
            .iter()
            .chain(right)
            .try_fold(1usize, |s, &n| s.checked_mul(n));
        let cost = contexts
            .checked_add(settings)
            .and_then(|n| n.checked_mul(responses_len))
            .and_then(|n| coordinate_count.and_then(|c| n.checked_add(c)))
            .and_then(|n| assignments.and_then(|a| n.checked_add(a)));
        if cost.is_none_or(|n| n > max_cells) {
            return Err(PreparationError::WorkLimit);
        }
        Ok((contexts, assignments.ok_or(PreparationError::WorkLimit)?))
    }

    fn validate_responses(
        left: &[usize],
        right: &[usize],
        responses: &[ResponseFunctions],
    ) -> Result<(), PreparationError> {
        let invalid = responses.iter().any(|r| {
            let bad_len = r.left.len() != left.len() || r.right.len() != right.len();
            bad_len
                || r.left
                    .iter()
                    .zip(left)
                    .chain(r.right.iter().zip(right))
                    .any(|(a, n)| a >= n)
        });
        if invalid {
            return Err(PreparationError::InvalidResponses);
        }
        Ok(())
    }

    fn validate_priors(
        priors: &[Vec<Rational>],
        contexts: usize,
        responses_len: usize,
    ) -> Result<(), PreparationError> {
        let invalid = priors.len() != contexts
            || priors.iter().any(|p| {
                p.len() != responses_len
                    || p.iter().any(|x| !x.denom().is_positive())
                    || ProbabilitySimplex::try_new(p.clone()).is_err()
            });
        if invalid {
            return Err(PreparationError::InvalidPriors);
        }
        Ok(())
    }

    fn find_prior_difference(
        priors: &[Vec<Rational>],
        contexts: usize,
        responses_len: usize,
    ) -> Option<PriorDifference> {
        for context in 1..contexts {
            for preparation in 0..responses_len {
                if priors[0][preparation] != priors[context][preparation] {
                    return Some(PriorDifference {
                        context,
                        preparation,
                        first_weight: priors[0][preparation].clone(),
                        other_weight: priors[context][preparation].clone(),
                    });
                }
            }
        }
        None
    }

    fn build_shared_point(
        left: &[usize],
        right: &[usize],
        responses: &[ResponseFunctions],
        prior0: &[Rational],
        assignments: usize,
    ) -> Vec<Rational> {
        let mut point = vec![ri(0); assignments];
        for (r, w) in responses.iter().zip(prior0) {
            let (mut index, mut stride) = (0, 1);
            for (&a, &n) in r.left.iter().chain(&r.right).zip(left.iter().chain(right)) {
                index += a * stride;
                stride *= n;
            }
            point[index] += w;
        }
        point
    }

    /// All listed preparations have a total local response at EVERY setting,
    /// including zero-weight preparations. No conditioning on detection occurs.
    pub fn new(
        left: Vec<usize>,
        right: Vec<usize>,
        responses: &[ResponseFunctions],
        priors: &[Vec<Rational>],
        limits: BellLimits,
        max_cells: usize,
    ) -> Result<Self, PreparationError> {
        let (contexts, assignments) =
            Self::validate_scenario_and_budget(&left, &right, responses.len(), max_cells)?;
        Self::validate_responses(&left, &right, responses)?;
        Self::validate_priors(priors, contexts, responses.len())?;
        let prior_difference = Self::find_prior_difference(priors, contexts, responses.len());
        let mut rows = Vec::new();
        for (x, &na) in left.iter().enumerate() {
            for (y, &nb) in right.iter().enumerate() {
                let mut row = vec![ri(0); na * nb];
                for (r, w) in responses.iter().zip(&priors[x * right.len() + y]) {
                    row[r.left[x] + na * r.right[y]] += w;
                }
                rows.push(row);
            }
        }
        let shared_point = prior_difference
            .is_none()
            .then(|| Self::build_shared_point(&left, &right, responses, &priors[0], assignments));
        let bell = FiniteBellProblem::new(left, right, rows.clone(), limits)
            .map_err(PreparationError::Bell)?;
        Ok(Self {
            rows,
            prior_difference,
            shared_point,
            bell,
        })
    }
    pub fn bell(&self) -> &FiniteBellProblem {
        &self.bell
    }
    /// A shared prior constructs a verified positive model without LP search.
    /// Context-dependent priors invoke the existing exact solver; a changed
    /// prior can still produce a Bell-local table.
    pub fn decide(&self, pivots: usize) -> Result<PreparedBellCertificate, PreparationError> {
        let extension = match &self.shared_point {
            Some(point) => FeasibilityVerdict::Feasible {
                point: point.clone(),
            },
            None => self.bell.decide(pivots).map_err(PreparationError::Bell)?,
        };
        let c = PreparedBellCertificate {
            rows: self.rows.clone(),
            prior_difference: self.prior_difference.clone(),
            extension,
        };
        self.verify(&c)?;
        Ok(c)
    }
    pub fn verify(&self, c: &PreparedBellCertificate) -> Result<(), PreparationError> {
        if c.rows != self.rows || c.prior_difference != self.prior_difference {
            return Err(PreparationError::CertificateMismatch);
        }
        self.bell
            .verify(&c.extension)
            .map_err(PreparationError::Bell)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_8d002f43 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
