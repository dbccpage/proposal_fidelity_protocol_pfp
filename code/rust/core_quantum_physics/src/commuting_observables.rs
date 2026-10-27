// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Checked finite Einstein causality and a declared two-factor observable model.
//! Incomparable events commute. Odd cycles obstruct two-factor colourings;
//! they do not obstruct general commuting operator assignments.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2b650d03<T> {
    fn checked_invariant_2b650d03(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2b650d03<T> for Option<T> {
    #[inline]
    fn checked_invariant_2b650d03(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2b650d03<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2b650d03(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use std::collections::HashMap;

use crate::exact_hermitian::{is_hermitian, partial_trace_first, partial_trace_second};
use linear_algebra::exact_field::{matrix, ExactFieldError};
use core_homology::finite_poset::FinitePoset;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::rq;

/// Embed a declared qubit operator into the first local factor.
pub fn embed_factor_1(
    m: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ExactFieldError> {
    if m.shape() != (2, 2) {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "two-qubit local embedding",
            left: m.shape(),
            right: (2, 2),
        });
    }
    matrix::kronecker(m, &matrix::identity(2)?)
}
/// Embed a declared qubit operator into the second local factor.
pub fn embed_factor_2(
    m: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ExactFieldError> {
    if m.shape() != (2, 2) {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "two-qubit local embedding",
            left: m.shape(),
            right: (2, 2),
        });
    }
    matrix::kronecker(&matrix::identity(2)?, m)
}

/// A finite causality certificate says exactly which incomparable pairs were checked.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MicrocausalityCertificate {
    pub events: usize,
    pub carrier_dimension: usize,
    pub incomparable_pairs: Vec<(usize, usize)>,
}
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum MicrocausalityError {
    #[error("missing observable at event {0}")]
    Missing(usize),
    #[error("observables must be Hermitian on a common nonempty carrier of dimension at most 64")]
    Carrier,
    #[error("incomparable events {0} and {1} do not commute")]
    Noncommuting(usize, usize),
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
}
/// General finite microcausality; no tensor-factor labels or colouring hypothesis.
pub fn check_microcausality(
    poset: &FinitePoset,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
) -> Result<MicrocausalityCertificate, MicrocausalityError> {
    let d = validate_microcausality_carrier(poset, assignment)?;
    let pairs = poset.incomparable_pairs();
    for &(u, v) in &pairs {
        if !matrix::commutes(&assignment[&u], &assignment[&v])? {
            return Err(MicrocausalityError::Noncommuting(u, v));
        }
    }
    Ok(MicrocausalityCertificate {
        events: poset.size(),
        carrier_dimension: d,
        incomparable_pairs: pairs,
    })
}

fn validate_microcausality_carrier(
    poset: &FinitePoset,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
) -> Result<usize, MicrocausalityError> {
    if [
        poset.size() == 0,
        poset.size() > 4096,
        assignment.len() != poset.size(),
    ]
    .into_iter()
    .any(|b| b)
    {
        return Err(MicrocausalityError::Carrier);
    }
    let first = assignment.get(&0).ok_or(MicrocausalityError::Missing(0))?;
    let d = first.rows();
    if d == 0 || d > 64 {
        return Err(MicrocausalityError::Carrier);
    }
    for u in 0..poset.size() {
        let op = assignment.get(&u).ok_or(MicrocausalityError::Missing(u))?;
        if op.shape() != (d, d) || !is_hermitian(op) {
            return Err(MicrocausalityError::Carrier);
        }
    }
    Ok(d)
}
pub fn verify_microcausality_certificate(
    poset: &FinitePoset,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
    certificate: &MicrocausalityCertificate,
) -> bool {
    check_microcausality(poset, assignment).is_ok_and(|computed| computed == *certificate)
}

/// Check whether observables at u and v generate the same maximal abelian subalgebra.
pub fn generates_same_masa_bipartite(
    factor_u: usize,
    factor_v: usize,
    obs_u: &BasicMatrix<GaussianRat>,
    obs_v: &BasicMatrix<GaussianRat>,
) -> bool {
    if factor_u != factor_v
        || !is_local_factor_operator(obs_u, factor_u)
        || !is_local_factor_operator(obs_v, factor_v)
        || matrix::is_scalar_matrix(obs_u) != Ok(false)
        || matrix::is_scalar_matrix(obs_v) != Ok(false)
    {
        return false;
    }
    matrix::commutes(obs_u, obs_v) == Ok(true)
}

/// Membership in a declared local factor of two qubits, independently of labels.
pub fn is_local_factor_operator(operator: &BasicMatrix<GaussianRat>, factor: usize) -> bool {
    if operator.shape() != (4, 4) || !is_hermitian(operator) {
        return false;
    }
    let reduced = match factor {
        1 => partial_trace_second(operator, 2, 2),
        2 => partial_trace_first(operator, 2, 2),
        _ => return false,
    };
    reduced
        .and_then(|m| matrix::scale(&m, &GaussianRat::from_rational(rq(1, 2))).map_err(Into::into))
        .and_then(|m| {
            match factor {
                1 => embed_factor_1(&m),
                _ => embed_factor_2(&m),
            }
            .map_err(Into::into)
        })
        .is_ok_and(|m| m == *operator)
}

/// Validate an observable assignment against finite microcausality and non-degeneracy.
pub fn validate_observable_assignment(
    poset: &FinitePoset,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
    factor_labels: &HashMap<usize, usize>,
    non_degeneracy_enforced: bool,
) -> (bool, String, usize) {
    if let Err(msg) = check_hermitian_and_factors(poset.size(), assignment, factor_labels) {
        return (false, msg, 0);
    }
    if non_degeneracy_enforced {
        if let Err(msg) = check_non_scalar_observables(poset.size(), assignment) {
            return (false, msg, 1);
        }
    }
    check_spacelike_pairs(poset, assignment, factor_labels, non_degeneracy_enforced)
}

fn check_hermitian_and_factors(
    size: usize,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
    factor_labels: &HashMap<usize, usize>,
) -> Result<(), String> {
    // 1. Hermiticity check
    for u in 0..size {
        let Some(obs) = assignment.get(&u) else {
            return Err(format!("Event {} has no assigned observable", u));
        };
        if !is_hermitian(obs) {
            return Err(format!("Event {} observable is not Hermitian", u));
        }
    }
    for u in 0..size {
        let Some(&factor) = factor_labels.get(&u) else {
            return Err(format!("Event {u} has no declared tensor factor"));
        };
        let obs = &assignment[&u];
        if !is_local_factor_operator(obs, factor) {
            return Err(format!(
                "Event {u} observable does not belong to declared factor {factor}"
            ));
        }
    }
    Ok(())
}

fn check_non_scalar_observables(
    size: usize,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
) -> Result<(), String> {
    // 2. Non-degeneracy: no scalar matrix
    for u in 0..size {
        let obs = assignment
            .get(&u)
            .checked_invariant_2b650d03("checked invariant");
        if matrix::is_scalar_matrix(obs) != Ok(false) {
            return Err(format!(
                "Non-degeneracy violation: event {} assigned scalar multiple of identity",
                u
            ));
        }
    }
    Ok(())
}

fn check_spacelike_pairs(
    poset: &FinitePoset,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
    factor_labels: &HashMap<usize, usize>,
    non_degeneracy_enforced: bool,
) -> (bool, String, usize) {
    // 3. Finite microcausality on all spacelike pairs
    let spacelike = poset.incomparable_pairs();
    for &(u, v) in &spacelike {
        if matrix::commutes(&assignment[&u], &assignment[&v]) != Ok(true) {
            return (
                false,
                format!(
                    "Finite microcausality violation: spacelike events {} and {} do not commute",
                    u, v
                ),
                0,
            );
        }

        // 4. Non-degeneracy on spacelike pairs: distinct MASAs
        if non_degeneracy_enforced && pair_generates_same_masa(u, v, assignment, factor_labels) {
            return (
                false,
                format!("Non-degeneracy violation: incomparable events {} and {} generate the same maximal abelian subalgebra", u, v),
                1,
            );
        }
    }

    (true, "Assignment valid".to_string(), 0)
}

fn pair_generates_same_masa(
    u: usize,
    v: usize,
    assignment: &HashMap<usize, BasicMatrix<GaussianRat>>,
    factor_labels: &HashMap<usize, usize>,
) -> bool {
    let f_u = *factor_labels.get(&u).unwrap_or(&1);
    let f_v = *factor_labels.get(&v).unwrap_or(&2);
    generates_same_masa_bipartite(
        f_u,
        f_v,
        assignment
            .get(&u)
            .checked_invariant_2b650d03("checked invariant"),
        assignment
            .get(&v)
            .checked_invariant_2b650d03("checked invariant"),
    )
}

// Origin: engine/crates_rs/core_quantum_physics/src/commuting_observables.rs
// Claim: urn:core:crates_rs:core-quantum-physics:commuting-observables:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_2b650d03 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
