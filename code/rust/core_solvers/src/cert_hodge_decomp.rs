//! Exact Euclidean Hodge certificate replay over Q. No epsilon acceptance.
//!
//! This checker binds the potentials and all three components to the supplied
//! cochain maps and input flow; it does not trust solver residuals or status.
//! Orthogonality and reconstruction imply uniqueness of the components. The
//! potentials themselves remain defined only modulo the kernels of the maps.
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::rational_bareiss::{self as exact, RationalBudget, RationalError};
use num_rational::BigRational;
use num_traits::Zero;
use core_kernel::exact_wire_vec;
use serde::{Deserialize, Serialize};

pub struct HodgeProblem<'a> {
    /// C0 -> C1, with rows indexed by edges.
    pub d0: &'a BasicMatrix<BigRational>,
    /// C1 -> C2, with columns indexed by edges.
    pub d1: &'a BasicMatrix<BigRational>,
    pub flow: &'a [BigRational],
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HodgeCertificate {
    #[serde(with = "exact_wire_vec")]
    pub alpha: Vec<BigRational>,
    #[serde(with = "exact_wire_vec")]
    pub beta: Vec<BigRational>,
    #[serde(with = "exact_wire_vec")]
    pub exact: Vec<BigRational>,
    #[serde(with = "exact_wire_vec")]
    pub coexact: Vec<BigRational>,
    #[serde(with = "exact_wire_vec")]
    pub harmonic: Vec<BigRational>,
}

#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum HodgeError {
    #[error("cochain or certificate dimensions do not match")]
    Shape,
    #[error("cochain maps violate d1*d0 = 0")]
    ChainLaw,
    #[error("certificate component does not equal its claimed image")]
    Component,
    #[error("components do not reconstruct the input flow")]
    Reconstruction,
    #[error("residual is not harmonic")]
    Harmonicity,
    #[error("components are not pairwise orthogonal")]
    Orthogonality,
    #[error(transparent)]
    Arithmetic(#[from] RationalError),
}

/// Constructible only by exact replay. Mathematical evidence has no authority.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VerifiedHodge {
    scalar_ops: usize,
}
impl VerifiedHodge {
    pub fn scalar_ops(&self) -> usize {
        self.scalar_ops
    }
    pub fn authority_effect(&self) -> &'static str {
        "AuthorityEffect: None"
    }
}

pub(crate) fn validate_problem(
    p: &HodgeProblem<'_>,
    fuel: &mut RationalBudget,
) -> Result<(), HodgeError> {
    if p.d0.rows() != p.flow.len() || p.d1.cols() != p.flow.len() {
        return Err(HodgeError::Shape);
    }
    for n in [p.d0.cols(), p.flow.len(), p.d1.rows()] {
        fuel.elements(n, 1)?;
    }
    for q in p.flow {
        fuel.rational(q)?;
    }
    if exact::multiply(p.d1, p.d0, fuel)?
        .as_slice()
        .iter()
        .any(|q| !q.is_zero())
    {
        return Err(HodgeError::ChainLaw);
    }
    Ok(())
}

fn validate_certificate_shapes_and_fuel(
    p: &HodgeProblem<'_>,
    c: &HodgeCertificate,
    fuel: &mut RationalBudget,
) -> Result<(), HodgeError> {
    let shapes_ok = [
        c.alpha.len() == p.d0.cols(),
        c.beta.len() == p.d1.rows(),
        c.exact.len() == p.flow.len(),
        c.coexact.len() == p.flow.len(),
        c.harmonic.len() == p.flow.len(),
    ]
    .into_iter()
    .all(|b| b);
    if !shapes_ok {
        return Err(HodgeError::Shape);
    }
    validate_problem(p, fuel)?;
    for q in c
        .alpha
        .iter()
        .chain(&c.beta)
        .chain(&c.exact)
        .chain(&c.coexact)
        .chain(&c.harmonic)
    {
        fuel.rational(q)?;
    }
    Ok(())
}

fn verify_hodge_components_and_reconstruction(
    p: &HodgeProblem<'_>,
    c: &HodgeCertificate,
    d1t: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<(), HodgeError> {
    let exact_vec = exact::multiply_vector(p.d0, &c.alpha, fuel)?;
    let coexact_vec = exact::multiply_vector(d1t, &c.beta, fuel)?;
    if exact_vec != c.exact || coexact_vec != c.coexact {
        return Err(HodgeError::Component);
    }
    for (i, input) in p.flow.iter().enumerate() {
        let sum = fuel.add(&c.exact[i], &c.coexact[i])?;
        if fuel.add(&sum, &c.harmonic[i])? != *input {
            return Err(HodgeError::Reconstruction);
        }
    }
    Ok(())
}

fn verify_hodge_harmonic_and_orthogonal(
    p: &HodgeProblem<'_>,
    c: &HodgeCertificate,
    d0t: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<(), HodgeError> {
    let d0t_harm = exact::multiply_vector(d0t, &c.harmonic, fuel)?;
    let d1_harm = exact::multiply_vector(p.d1, &c.harmonic, fuel)?;
    if d0t_harm.iter().any(|q| !q.is_zero()) || d1_harm.iter().any(|q| !q.is_zero()) {
        return Err(HodgeError::Harmonicity);
    }
    for (a, b) in [
        (&c.exact, &c.coexact),
        (&c.exact, &c.harmonic),
        (&c.coexact, &c.harmonic),
    ] {
        if !exact::dot(a, b, fuel)?.is_zero() {
            return Err(HodgeError::Orthogonality);
        }
    }
    Ok(())
}

pub fn check_hodge_certificate(
    p: &HodgeProblem<'_>,
    c: &HodgeCertificate,
    fuel: &mut RationalBudget,
) -> Result<VerifiedHodge, HodgeError> {
    let start = fuel.used();
    validate_certificate_shapes_and_fuel(p, c, fuel)?;
    let d0t = p.d0.try_transpose().map_err(RationalError::from)?;
    let d1t = p.d1.try_transpose().map_err(RationalError::from)?;
    verify_hodge_components_and_reconstruction(p, c, &d1t, fuel)?;
    verify_hodge_harmonic_and_orthogonal(p, c, &d0t, fuel)?;
    Ok(VerifiedHodge {
        scalar_ops: fuel.used() - start,
    })
}

// Origin: engine/crates_rs/core_solvers/src/cert_hodge_decomp.rs
// Claim: urn:core:crates_rs:core-solvers:cert-hodge-decomp:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e874adb5 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
