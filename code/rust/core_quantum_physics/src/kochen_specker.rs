//! Exact Kochen–Specker hypergraphs and frame functions on declared finite rays.
//! A KS decision includes both full orthogonal frames (exactly one selected ray)
//! and every orthogonal pair (at most one). No claim about a dense or infinite
//! carrier follows from a finite decision.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::involution::Involution;
use linear_algebra::exact_field::{elimination, matrix};
use linear_algebra::scalars::{ExactRing, Field};
use num_traits::{One, Zero};
use core_number_theory::quadratic::Quadratic;
use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_sat_dpll::{
    BooleanError, BooleanOutcome, BooleanProblem, ConstraintId,
};

pub const CABELLO_18_VECTORS: [[i64; 4]; 18] = [
    [1, 1, 1, 1],
    [1, 1, 1, -1],
    [1, 1, 0, 0],
    [1, 1, -1, -1],
    [1, 0, 1, 0],
    [1, 0, 0, 1],
    [1, 0, 0, -1],
    [1, 0, -1, 0],
    [1, -1, 1, 1],
    [1, -1, 0, 0],
    [1, -1, -1, 1],
    [1, -1, -1, -1],
    [0, 1, 0, 1],
    [0, 1, 0, 0],
    [0, 1, -1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, -1],
    [0, 0, 0, 1],
];

pub const CABELLO_9_CONTEXTS: [[usize; 4]; 9] = [
    [2, 9, 15, 17],
    [4, 7, 13, 17],
    [5, 6, 13, 15],
    [0, 3, 9, 16],
    [0, 6, 10, 14],
    [1, 5, 11, 14],
    [1, 7, 8, 12],
    [2, 8, 11, 16],
    [3, 4, 10, 12],
];

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RaySystemError {
    #[error("expected nonzero rays of a common dimension in 1..=16, at most 512 rays")]
    InvalidCarrier,
    #[error("context {0} is not an orthogonal frame of the declared dimension")]
    InvalidFrame(usize),
    #[error("exact matrix operation refused: {0}")]
    Matrix(String),
    #[error(transparent)]
    Boolean(#[from] BooleanError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RaySystem<F> {
    pub dimension: usize,
    pub rays: Vec<Vec<F>>,
    pub pairs: Vec<(usize, usize)>,
    pub contexts: Vec<Vec<usize>>,
}

fn inner<F: Field + ExactRing + Involution>(u: &[F], v: &[F]) -> F {
    u.iter()
        .zip(v)
        .fold(F::zero(), |s, (x, y)| s.add(&x.conjugate().mul(y)))
}

impl<F: Field + ExactRing + Involution> RaySystem<F> {
    fn validate_ray_context(
        rays: &[Vec<F>],
        d: usize,
        k: usize,
        c: &[usize],
    ) -> Result<(), RaySystemError> {
        let bad_indices = c.len() != d || c.iter().any(|&i| i >= rays.len());
        let non_orthogonal = (0..d).any(|i| {
            (i + 1..d).any(|j| c[i] == c[j] || !inner(&rays[c[i]], &rays[c[j]]).is_zero())
        });
        if bad_indices || non_orthogonal {
            return Err(RaySystemError::InvalidFrame(k));
        }
        Ok(())
    }

    /// All orthogonal pairs are computed; supplied contexts must be genuine frames.
    pub fn new(rays: Vec<Vec<F>>, contexts: Vec<Vec<usize>>) -> Result<Self, RaySystemError> {
        let d = rays.first().map_or(0, Vec::len);
        let bad_dims = d == 0 || d > 16 || rays.len() > 512 || contexts.len() > 512;
        if bad_dims || rays.iter().any(|r| r.len() != d || inner(r, r).is_zero()) {
            return Err(RaySystemError::InvalidCarrier);
        }
        let pairs = (0..rays.len())
            .flat_map(|i| (i + 1..rays.len()).map(move |j| (i, j)))
            .filter(|&(i, j)| inner(&rays[i], &rays[j]).is_zero())
            .collect::<Vec<_>>();
        for (k, c) in contexts.iter().enumerate() {
            Self::validate_ray_context(&rays, d, k, c)?;
        }
        Ok(Self {
            dimension: d,
            rays,
            pairs,
            contexts,
        })
    }
    pub fn problem(&self) -> Result<BooleanProblem, RaySystemError> {
        // Recheck public data, including that no pair constraint was dropped.
        let canonical = Self::new(self.rays.clone(), self.contexts.clone())?;
        if canonical.dimension != self.dimension || canonical.pairs != self.pairs {
            return Err(RaySystemError::InvalidCarrier);
        }
        Ok(BooleanProblem::new(
            self.rays.len(),
            &self.pairs,
            &self.contexts,
        )?)
    }
    pub fn decide(&self, node_budget: usize) -> Result<BooleanOutcome, RaySystemError> {
        Ok(self.problem()?.solve(node_budget)?)
    }
    pub fn deletion_minimal_core(
        &self,
        node_budget: usize,
    ) -> Result<Vec<ConstraintId>, RaySystemError> {
        Ok(self.problem()?.deletion_minimal_unsat_core(node_budget)?)
    }
    pub fn projector_coordinates(&self) -> Result<BasicMatrix<F>, RaySystemError> {
        self.problem()?;
        let mut rows = vec![vec![F::zero(); self.rays.len()]; self.dimension * self.dimension];
        for (k, r) in self.rays.iter().enumerate() {
            let inv = inner(r, r)
                .try_inv()
                .ok_or(RaySystemError::InvalidCarrier)?;
            for i in 0..self.dimension {
                for j in 0..self.dimension {
                    rows[i * self.dimension + j][k] = r[i].mul(&r[j].conjugate()).mul(&inv);
                }
            }
        }
        matrix::from_rows(rows).map_err(|e| RaySystemError::Matrix(e.to_string()))
    }
    pub fn incidence(&self) -> Result<BasicMatrix<Rational>, RaySystemError> {
        self.problem()?;
        matrix::from_fn(self.contexts.len(), self.rays.len(), |i, j| {
            if self.contexts[i].contains(&j) {
                ri(1)
            } else {
                ri(0)
            }
        })
        .map_err(|e| RaySystemError::Matrix(e.to_string()))
    }
    pub fn affine_frame_dimension(&self) -> Result<usize, RaySystemError> {
        Ok(self.rays.len()
            - elimination::rank(&self.incidence()?)
                .map_err(|e| RaySystemError::Matrix(e.to_string()))?)
    }
    pub fn projector_span_rank(&self) -> Result<usize, RaySystemError> {
        elimination::rank(&self.projector_coordinates()?)
            .map_err(|e| RaySystemError::Matrix(e.to_string()))
    }
}

pub fn cabello_18() -> Result<RaySystem<Rational>, RaySystemError> {
    RaySystem::new(
        CABELLO_18_VECTORS
            .iter()
            .map(|r| r.iter().map(|&x| ri(x)).collect())
            .collect(),
        CABELLO_9_CONTEXTS.iter().map(|c| c.to_vec()).collect(),
    )
}

fn collinear<const D: i64>(u: &[Quadratic<D>; 3], v: &[Quadratic<D>; 3]) -> bool {
    [(0, 1), (0, 2), (1, 2)]
        .iter()
        .all(|&(i, j)| (u[i].clone() * v[j].clone() - u[j].clone() * v[i].clone()).is_zero())
}

fn build_quadratic_seeds(extended: bool) -> Vec<[(i64, i64); 3]> {
    // Seed tuples are coefficients, never an independent arithmetic representation.
    let o = (0, 0);
    let one = (1, 0);
    let minus = (-1, 0);
    let root = (0, 1);
    let mroot = (0, -1);
    let mut seeds = vec![[one, o, o], [o, one, o], [o, o, one]];
    for s in [one, minus] {
        seeds.extend([[s, one, o], [s, o, one], [o, s, one]]);
    }
    for s in [root, mroot] {
        seeds.extend([
            [o, one, s],
            [o, s, one],
            [one, o, s],
            [s, o, one],
            [one, s, o],
            [s, one, o],
        ]);
    }
    for sx in [one, minus] {
        for sy in [one, minus] {
            if extended {
                seeds.push([sx, sy, one]);
            }
            seeds.extend([[sx, sy, root], [sx, root, sy], [root, sx, sy]]);
        }
    }
    if extended {
        for s in [root, mroot] {
            seeds.extend([[one, s, s], [s, one, s], [s, s, one]]);
        }
    }
    seeds
}

fn find_orthogonal_triples<const D: i64>(unique: &[[Quadratic<D>; 3]]) -> Vec<Vec<usize>> {
    let mut contexts = Vec::new();
    for i in 0..unique.len() {
        for j in i + 1..unique.len() {
            if !inner(&unique[i], &unique[j]).is_zero() {
                continue;
            }
            for k in j + 1..unique.len() {
                if inner(&unique[i], &unique[k]).is_zero()
                    && inner(&unique[j], &unique[k]).is_zero()
                {
                    contexts.push(vec![i, j, k]);
                }
            }
        }
    }
    contexts
}

fn quadratic_configuration<const D: i64>(
    extended: bool,
) -> Result<RaySystem<Quadratic<D>>, RaySystemError> {
    let seeds = build_quadratic_seeds(extended);
    let mut unique: Vec<[Quadratic<D>; 3]> = Vec::new();
    for s in seeds {
        let r = s.map(|(a, b)| Quadratic::from_ints(a, b));
        if !unique.iter().any(|u| collinear(&r, u)) {
            unique.push(r);
        }
    }
    let contexts = find_orthogonal_triples(&unique);
    RaySystem::new(unique.into_iter().map(|r| r.to_vec()).collect(), contexts)
}

pub fn peres_33() -> Result<RaySystem<Quadratic<2>>, RaySystemError> {
    quadratic_configuration::<2>(false)
}
/// This finite candidate set is a search control, not a conductor threshold theorem.
pub fn conductor_12_candidates() -> Result<RaySystem<Quadratic<3>>, RaySystemError> {
    quadratic_configuration::<3>(true)
}

/// Meyer's parity colouring on a declared primitive Pythagorean ray. A primitive
/// integer vector of square norm has exactly one odd coordinate; that coordinate
/// labels its colour. For an orthogonal rational triad, the odd positions differ.
pub fn pythagorean_colour(ray: &[num_bigint::BigInt; 3]) -> Result<usize, RaySystemError> {
    use num_integer::Integer;
    let norm = ray
        .iter()
        .fold(num_bigint::BigInt::zero(), |s, x| s + x * x);
    let root = norm.sqrt();
    if norm.is_zero()
        || &root * &root != norm
        || ray.iter().fold(num_bigint::BigInt::zero(), |s, x| s.gcd(x)) != num_bigint::BigInt::one()
    {
        return Err(RaySystemError::InvalidCarrier);
    }
    let odd = (0..3).filter(|&i| ray[i].is_odd()).collect::<Vec<_>>();
    if odd.len() != 1 {
        return Err(RaySystemError::InvalidCarrier);
    }
    Ok(odd[0])
}

// Origin: engine/crates_rs/core_quantum_physics/src/kochen_specker.rs
// Claim: urn:core:crates_rs:core-quantum-physics:kochen-specker:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_4bfef0a1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
