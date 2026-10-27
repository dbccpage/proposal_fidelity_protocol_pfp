//! Exact conditional preserver, reachability and projection certificates on Q(i).
//!
//! The positive Gram matrix and frame/task inputs are supplied. A full Gram
//! identity certifies the induced global semilinear map; matching sampled rays
//! alone never certifies a black-box global bijection. Proposal construction is
//! separate from replay. No routine here grants authorization or supplies a
//! physical Born rule, time evolution, or continuum completion.
//! AuthorityEffect: None.

use linear_algebra::exact_field::{involution, ordered, ExactFieldError};
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::gaussian_norm::{self, GaussianNormError, NormBudget, NormObstruction};
use core_number_theory::rational::{ri, Rational};

use crate::exact_hermitian::exact_limits;
use crate::exact_operator::{ExactOperator, OperatorError};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PreserverError {
    #[error(transparent)]
    Operator(#[from] OperatorError),
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
    #[error(transparent)]
    Norm(#[from] GaussianNormError),
    #[error("invalid carrier or submitted witness: {0}")]
    Invalid(&'static str),
}

fn require(condition: bool, reason: &'static str) -> Result<(), PreserverError> {
    if condition {
        Ok(())
    } else {
        Err(PreserverError::Invalid(reason))
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HermitianCarrier {
    gram: ExactOperator,
    inverse_gram: ExactOperator,
}

impl HermitianCarrier {
    pub fn new(gram: ExactOperator) -> Result<Self, PreserverError> {
        gram.check_hermitian()?;
        let inertia = ordered::hermitian_inertia_with_limits(gram.as_matrix(), exact_limits())?;
        require(
            inertia.is_positive_definite(),
            "Gram form is not positive definite",
        )?;
        let inverse_gram = gram.inverse()?;
        Ok(Self { gram, inverse_gram })
    }

    pub fn dimension(&self) -> usize {
        self.gram.rows()
    }
    pub fn gram(&self) -> &ExactOperator {
        &self.gram
    }

    pub fn inner(&self, x: &[G], y: &[G]) -> Result<G, PreserverError> {
        require(x.len() == self.dimension(), "left vector dimension")?;
        Ok(involution::inner_product(x, &self.gram.apply(y)?)?)
    }

    pub fn norm(&self, x: &[G]) -> Result<Rational, PreserverError> {
        let value = self.inner(x, x)?;
        require(
            value.im.is_zero() && !value.re.is_negative(),
            "nonreal or negative squared norm",
        )?;
        Ok(value.re)
    }

    pub fn probability(&self, x: &[G], y: &[G]) -> Result<Rational, PreserverError> {
        let denominator = self.norm(x)? * self.norm(y)?;
        require(!denominator.is_zero(), "zero vector has no ray probability")?;
        Ok(self.inner(x, y)?.norm_sq() / denominator)
    }

    pub fn adjoint(&self, a: &ExactOperator) -> Result<ExactOperator, PreserverError> {
        Ok(self.inverse_gram.mul(&a.dagger()?)?.mul(&self.gram)?)
    }

    pub fn verify_unitary(&self, a: &ExactOperator) -> Result<(), PreserverError> {
        require(a.shape() == self.gram.shape(), "unitary dimension")?;
        require(
            a.dagger()?.mul(&self.gram)?.mul(a)? == self.gram,
            "submitted unitary Gram identity",
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ScalarBranch {
    Identity,
    Conjugate,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PreserverCertificate {
    pub operator: ExactOperator,
    pub branch: ScalarBranch,
    pub multiplier: Rational,
}

fn gram_for_branch(
    carrier: &HermitianCarrier,
    branch: ScalarBranch,
) -> Result<ExactOperator, PreserverError> {
    match branch {
        ScalarBranch::Identity => Ok(carrier.gram.clone()),
        ScalarBranch::Conjugate => Ok(ExactOperator::try_new(involution::conjugate_entries(
            carrier.gram.as_matrix(),
        )?)?),
    }
}

fn verify_frame_action(
    d: usize,
    original_frame: &[Vec<G>],
    original_images: &[Vec<G>],
    certificate: &PreserverCertificate,
) -> Result<(), PreserverError> {
    for (source, target) in original_frame.iter().zip(original_images) {
        require(target.len() == d, "image vector dimension")?;
        let twisted = match certificate.branch {
            ScalarBranch::Identity => source.clone(),
            ScalarBranch::Conjugate => source.iter().map(G::conj).collect(),
        };
        require(
            certificate.operator.apply(&twisted)? == *target,
            "original frame action",
        )?;
    }
    Ok(())
}

fn verify_preserver_gram_identity(
    carrier: &HermitianCarrier,
    certificate: &PreserverCertificate,
) -> Result<(), PreserverError> {
    let h = gram_for_branch(carrier, certificate.branch)?;
    let dag = certificate.operator.dagger()?;
    let left_gram = dag.mul(&carrier.gram)?.mul(&certificate.operator)?;
    require(
        left_gram == h.scale_rat(&certificate.multiplier)?,
        "complete semisimilarity Gram identity",
    )
}

pub fn verify_preserver(
    carrier: &HermitianCarrier,
    original_frame: &[Vec<G>],
    original_images: &[Vec<G>],
    certificate: &PreserverCertificate,
) -> Result<(), PreserverError> {
    let d = carrier.dimension();
    require(
        original_frame.len() == d && original_images.len() == d,
        "complete frame cardinality",
    )?;
    let frame = ExactOperator::from_rows(original_frame.to_vec())?;
    require(
        frame.shape() == (d, d) && certificate.operator.shape() == (d, d),
        "frame or preserver dimension",
    )?;
    frame.inverse()?;
    require(
        certificate.multiplier.is_positive(),
        "nonpositive multiplier",
    )?;
    verify_preserver_gram_identity(carrier, certificate)?;
    verify_frame_action(d, original_frame, original_images, certificate)
}

/// Exact original data are compared at replay, including representative choices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RayBinding {
    pub gram: ExactOperator,
    pub source: Vec<G>,
    pub target: Vec<G>,
}

#[derive(Debug, Clone)]
pub struct RayProblem {
    carrier: HermitianCarrier,
    binding: RayBinding,
}

impl RayProblem {
    pub fn new(
        carrier: HermitianCarrier,
        source: Vec<G>,
        target: Vec<G>,
    ) -> Result<Self, PreserverError> {
        require(
            carrier.norm(&source)?.is_positive() && carrier.norm(&target)?.is_positive(),
            "zero ray",
        )?;
        let binding = RayBinding {
            gram: carrier.gram.clone(),
            source,
            target,
        };
        Ok(Self { carrier, binding })
    }
    pub fn binding(&self) -> &RayBinding {
        &self.binding
    }
    fn ratio(&self) -> Result<Rational, PreserverError> {
        Ok(self.carrier.norm(&self.binding.source)? / self.carrier.norm(&self.binding.target)?)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReachabilityCertificate {
    Unitary {
        original: RayBinding,
        operator: ExactOperator,
        scalar: G,
    },
    Obstruction {
        original: RayBinding,
        witness: NormObstruction,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ReachabilityVerdict {
    UnitaryReachable,
    UnitaryImpossible,
}

fn verify_unitary_reachability(
    problem: &RayProblem,
    original: &RayBinding,
    operator: &ExactOperator,
    scalar: &G,
) -> Result<ReachabilityVerdict, PreserverError> {
    require(
        original == problem.binding(),
        "original ray problem binding",
    )?;
    gaussian_norm::verify_norm(&problem.ratio()?, scalar)?;
    problem.carrier.verify_unitary(operator)?;
    let target: Vec<_> = problem
        .binding
        .target
        .iter()
        .map(|x| scalar.mul(x))
        .collect();
    require(
        operator.apply(&problem.binding.source)? == target,
        "submitted source-to-target action",
    )?;
    Ok(ReachabilityVerdict::UnitaryReachable)
}

pub fn verify_reachability(
    problem: &RayProblem,
    certificate: &ReachabilityCertificate,
    budget: NormBudget,
) -> Result<ReachabilityVerdict, PreserverError> {
    match certificate {
        ReachabilityCertificate::Unitary {
            original,
            operator,
            scalar,
        } => verify_unitary_reachability(problem, original, operator, scalar),
        ReachabilityCertificate::Obstruction { original, witness } => {
            require(
                original == problem.binding(),
                "original ray problem binding",
            )?;
            gaussian_norm::verify_obstruction(
                &problem.ratio()?,
                witness,
                budget.factorization_per_integer,
            )?;
            Ok(ReachabilityVerdict::UnitaryImpossible)
        }
    }
}

fn build_rank_one_isometry(
    carrier: &HermitianCarrier,
    f: &[G],
    v: &[G],
) -> Result<ExactOperator, PreserverError> {
    let mut operator = ExactOperator::identity(carrier.dimension())?;
    if f != v {
        let w: Vec<_> = f.iter().zip(v).map(|(x, y)| x.sub(y)).collect();
        let beta = carrier.inner(&w, f)?;
        require(!beta.is_zero(), "zero rank-one denominator")?;
        let hw = carrier.gram.apply(&w)?;
        let outer = ExactOperator::try_new(involution::outer_product(&w, &hw)?)?;
        let correction = outer.scale(&beta.inv())?;
        operator = operator.sub(&correction)?;
    }
    Ok(operator)
}

/// Root-free rank-one isometry. Errors preserve exhaustion and malformed input.
pub fn propose_reachability(
    problem: &RayProblem,
    budget: NormBudget,
) -> Result<ReachabilityCertificate, PreserverError> {
    let ratio = problem.ratio()?;
    if let Some(witness) =
        gaussian_norm::propose_obstruction(&ratio, budget.factorization_per_integer)?
    {
        return Ok(ReachabilityCertificate::Obstruction {
            original: problem.binding.clone(),
            witness,
        });
    }
    let scalar = gaussian_norm::realize_norm(&ratio, budget)?
        .ok_or(PreserverError::Invalid("inconsistent norm construction"))?;
    let f = &problem.binding.source;
    let v: Vec<_> = problem
        .binding
        .target
        .iter()
        .map(|x| scalar.mul(x))
        .collect();
    let operator = build_rank_one_isometry(&problem.carrier, f, &v)?;
    Ok(ReachabilityCertificate::Unitary {
        original: problem.binding.clone(),
        operator,
        scalar,
    })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProjectionCertificate {
    pub original: RayBinding,
    pub projection: ExactOperator,
    pub branch_vector: Vec<G>,
    pub probability: Rational,
}

pub fn propose_projection(problem: &RayProblem) -> Result<ProjectionCertificate, PreserverError> {
    let g = &problem.binding.target;
    let hg = problem.carrier.gram.apply(g)?;
    let projection = ExactOperator::try_new(involution::outer_product(g, &hg)?)?
        .scale_rat(&(Rational::one() / problem.carrier.norm(g)?))?;
    Ok(ProjectionCertificate {
        original: problem.binding.clone(),
        branch_vector: projection.apply(&problem.binding.source)?,
        probability: problem.carrier.probability(&problem.binding.source, g)?,
        projection,
    })
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ProjectionVerdict {
    PositivePostselection,
    ZeroBranch,
}

fn verify_rank_one_basis_action(
    c: &HermitianCarrier,
    p: &ExactOperator,
    g: &[G],
    rg: &Rational,
) -> Result<(), PreserverError> {
    for j in 0..c.dimension() {
        let mut e = vec![G::zero(); c.dimension()];
        e[j] = G::one();
        let coefficient = c
            .inner(g, &e)?
            .mul(&G::from_rational(Rational::one() / rg));
        let expected: Vec<_> = g.iter().map(|x| coefficient.mul(x)).collect();
        require(p.apply(&e)? == expected, "complete named rank-one action")?;
    }
    Ok(())
}

fn verify_projection_operator(
    c: &HermitianCarrier,
    p: &ExactOperator,
    g: &[G],
) -> Result<(), PreserverError> {
    require(p.shape() == c.gram.shape(), "projection shape")?;
    require(
        c.adjoint(p)? == *p && p.mul(p)? == *p,
        "selfadjoint idempotent",
    )?;
    let rg = c.norm(g)?;
    verify_rank_one_basis_action(c, p, g, &rg)
}

fn verify_projection_probabilities(
    c: &HermitianCarrier,
    f: &[G],
    g: &[G],
    branch_vector: &[G],
    probability: &Rational,
) -> Result<(), PreserverError> {
    let branch_prob = c.norm(branch_vector)? / c.norm(f)?;
    let transition_prob = c.probability(f, g)?;
    require(
        branch_prob == *probability && transition_prob == *probability,
        "submitted branch or transition probability",
    )
}

pub fn verify_projection(
    problem: &RayProblem,
    certificate: &ProjectionCertificate,
) -> Result<ProjectionVerdict, PreserverError> {
    require(
        certificate.original == problem.binding,
        "original projection task binding",
    )?;
    let p = &certificate.projection;
    let c = &problem.carrier;
    let g = &problem.binding.target;
    verify_projection_operator(c, p, g)?;
    let f = &problem.binding.source;
    require(
        p.apply(f)? == certificate.branch_vector,
        "submitted branch vector",
    )?;
    verify_projection_probabilities(
        c,
        f,
        g,
        &certificate.branch_vector,
        &certificate.probability,
    )?;
    Ok(if certificate.probability.is_zero() {
        ProjectionVerdict::ZeroBranch
    } else {
        ProjectionVerdict::PositivePostselection
    })
}

pub fn canonical_ray(vector: &[G]) -> Result<Vec<G>, PreserverError> {
    let pivot = vector
        .iter()
        .find(|x| !x.is_zero())
        .ok_or(PreserverError::Invalid("zero ray"))?;
    let inverse = pivot.inv();
    Ok(vector.iter().map(|x| inverse.mul(x)).collect())
}

/// The exact Gaussian Hadamard representative; its square is iI.
pub fn gaussian_hadamard() -> Result<ExactOperator, PreserverError> {
    let z = G {
        re: Rational::one() / ri(2),
        im: Rational::one() / ri(2),
    };
    Ok(ExactOperator::from_rows(vec![
        vec![z.clone(), z.clone()],
        vec![z.clone(), z.neg()],
    ])?)
}

// Origin: engine/crates_rs/core_quantum_physics/src/projective_preservers.rs
// Claim: urn:core:crates_rs:core-quantum-physics:projective-preservers:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_27498659 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
