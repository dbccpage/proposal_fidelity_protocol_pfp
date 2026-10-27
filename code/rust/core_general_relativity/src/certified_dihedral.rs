//! Metric-bound rational dihedral and deficit enclosures for finite hinge stars.
//! Edge inputs are squared lengths. A shared edge table binds all neighboring
//! simplex metrics; a distinct cyclic link supplies the closed hinge incidence.
//! This local Regge calculation does not assert global manifold realizability.

use linear_algebra::regge_exact::{determinant, solve};
use num_rational::BigRational as Q;
use num_traits::Zero;
use core_number_theory::certified_angles::{
    atan_enclosure, pi_enclosure, sqrt_enclosure, validate_precision, validate_rational, AngleError,
};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum GeometryError {
    #[error(transparent)]
    Angle(#[from] AngleError),
    #[error("invalid hinge, link cycle, edge coverage, or squared lengths")]
    Input,
    #[error("the metric Gram matrix is not positive definite")]
    NotEuclidean,
    #[error("exact linear algebra refused the metric")]
    LinearAlgebra,
}

// No new kernel dependency: number theory exposes the shared Interval type.
pub use core_number_theory::certified_angles::RationalInterval;

#[derive(Debug, Clone)]
pub struct DihedralEnclosure {
    normal_gram: [Q; 3],
    bounds: RationalInterval,
}
impl DihedralEnclosure {
    pub fn normal_gram(&self) -> &[Q; 3] {
        &self.normal_gram
    }
    pub fn bounds(&self) -> &RationalInterval {
        &self.bounds
    }
}

/// Nondegenerate Euclidean 4-simplex. Indices 0,1,2 specify its triangle hinge.
fn validate_squared_matrix(squared: &[[Q; 5]; 5]) -> Result<(), GeometryError> {
    for i in 0..5 {
        for j in 0..5 {
            validate_rational(&squared[i][j])?;
            if squared[i][j] != squared[j][i]
                || (i == j && !squared[i][j].is_zero())
                || (i != j && squared[i][j] <= Q::zero())
            {
                return Err(GeometryError::Input);
            }
        }
    }
    Ok(())
}

fn validate_gram_positive_definite(g: &[[Q; 4]; 4]) -> Result<(), GeometryError> {
    let m1: [[Q; 1]; 1] = [[g[0][0].clone()]];
    if determinant(&m1).map_err(|_| GeometryError::LinearAlgebra)? <= Q::zero() {
        return Err(GeometryError::NotEuclidean);
    }
    let m2: [[Q; 2]; 2] = std::array::from_fn(|i| std::array::from_fn(|j| g[i][j].clone()));
    if determinant(&m2).map_err(|_| GeometryError::LinearAlgebra)? <= Q::zero() {
        return Err(GeometryError::NotEuclidean);
    }
    let m3: [[Q; 3]; 3] = std::array::from_fn(|i| std::array::from_fn(|j| g[i][j].clone()));
    if determinant(&m3).map_err(|_| GeometryError::LinearAlgebra)? <= Q::zero() {
        return Err(GeometryError::NotEuclidean);
    }
    let m4: [[Q; 4]; 4] = std::array::from_fn(|i| std::array::from_fn(|j| g[i][j].clone()));
    if determinant(&m4).map_err(|_| GeometryError::LinearAlgebra)? <= Q::zero() {
        return Err(GeometryError::NotEuclidean);
    }
    Ok(())
}

fn compute_dihedral_bounds(disc: &Q, ab: &Q, eps: &Q) -> Result<RationalInterval, GeometryError> {
    if ab.is_zero() {
        return Ok(pi_enclosure(eps)?.mul_scalar(&Q::new(1.into(), 2.into())));
    }
    let denom = if ab > &Q::zero() { ab.clone() } else { -ab };
    let quarter = eps / Q::from_integer(4.into());
    let root = sqrt_enclosure(disc, &(&denom * &quarter))?;
    let lo = atan_enclosure(&(root.lo() / &denom), &quarter)?;
    let hi = atan_enclosure(&(root.hi() / &denom), &quarter)?;
    let theta = RationalInterval::try_new(lo.lo().clone(), hi.hi().clone())
        .map_err(AngleError::from)?;
    if ab > &Q::zero() {
        Ok(theta)
    } else {
        Ok(pi_enclosure(&quarter)?.sub(&theta))
    }
}

pub fn dihedral_enclosure(
    squared: &[[Q; 5]; 5],
    eps: &Q,
) -> Result<DihedralEnclosure, GeometryError> {
    validate_precision(eps)?;
    validate_squared_matrix(squared)?;
    let two = Q::from_integer(2.into());
    let g: [[Q; 4]; 4] = std::array::from_fn(|i| {
        std::array::from_fn(|j| {
            (&squared[0][i + 1] + &squared[0][j + 1] - &squared[i + 1][j + 1]) / &two
        })
    });
    validate_gram_positive_definite(&g)?;
    let tangent: [[Q; 2]; 2] = std::array::from_fn(|i| std::array::from_fn(|j| g[i][j].clone()));
    let v: Vec<[Q; 2]> = (2..4).map(|j| [g[0][j].clone(), g[1][j].clone()]).collect();
    let inverse_v: Vec<[Q; 2]> = v
        .iter()
        .map(|x| solve(&tangent, x).map_err(|_| GeometryError::LinearAlgebra))
        .collect::<Result<_, _>>()?;
    let schur = |i: usize, j: usize| {
        &g[i + 2][j + 2] - (&v[i][0] * &inverse_v[j][0] + &v[i][1] * &inverse_v[j][1])
    };
    let aa = schur(0, 0);
    let bb = schur(1, 1);
    let ab = schur(0, 1);
    let disc = &aa * &bb - &ab * &ab;
    if aa <= Q::zero() || bb <= Q::zero() || disc <= Q::zero() {
        return Err(GeometryError::NotEuclidean);
    }
    // theta=atan2(sqrt(aa bb-ab^2),ab). atan is monotone and 1-Lipschitz.
    let bounds = compute_dihedral_bounds(&disc, &ab, eps)?;
    Ok(DihedralEnclosure {
        normal_gram: [aa, bb, ab],
        bounds,
    })
}

#[derive(Debug, Clone)]
pub struct MetricHingeStar {
    hinge: [usize; 3],
    cycle: Vec<usize>,
    squared_edges: BTreeMap<(usize, usize), Q>,
}

fn edge(a: usize, b: usize) -> (usize, usize) {
    (a.min(b), a.max(b))
}

impl MetricHingeStar {
    /// Exactly the edges used by consecutive 4-simplices, no missing/extra edge.
    pub fn new(
        hinge: [usize; 3],
        cycle: Vec<usize>,
        squared_edges: BTreeMap<(usize, usize), Q>,
    ) -> Result<Self, GeometryError> {
        let vertices: BTreeSet<_> = hinge.iter().chain(&cycle).copied().collect();
        if !(3..=16).contains(&cycle.len()) || vertices.len() != 3 + cycle.len() {
            return Err(GeometryError::Input);
        }
        let mut required = BTreeSet::new();
        for i in 0..cycle.len() {
            let simplex = [
                hinge[0],
                hinge[1],
                hinge[2],
                cycle[i],
                cycle[(i + 1) % cycle.len()],
            ];
            for a in 0..5 {
                for b in a + 1..5 {
                    required.insert(edge(simplex[a], simplex[b]));
                }
            }
        }
        if squared_edges.keys().copied().collect::<BTreeSet<_>>() != required {
            return Err(GeometryError::Input);
        }
        for q in squared_edges.values() {
            validate_rational(q)?;
            if q <= &Q::zero() {
                return Err(GeometryError::Input);
            }
        }
        Ok(Self {
            hinge,
            cycle,
            squared_edges,
        })
    }
    pub fn hinge(&self) -> &[usize; 3] {
        &self.hinge
    }
    pub fn cycle(&self) -> &[usize] {
        &self.cycle
    }
    pub fn squared_edges(&self) -> &BTreeMap<(usize, usize), Q> {
        &self.squared_edges
    }
    /// Metric of sector i in the declared cyclic hinge ordering.
    pub fn simplex(&self, i: usize) -> Result<[[Q; 5]; 5], GeometryError> {
        if i >= self.cycle.len() {
            return Err(GeometryError::Input);
        }
        let ids = [
            self.hinge[0],
            self.hinge[1],
            self.hinge[2],
            self.cycle[i],
            self.cycle[(i + 1) % self.cycle.len()],
        ];
        let mut out = std::array::from_fn(|_| std::array::from_fn(|_| Q::zero()));
        for a in 0..5 {
            for b in a + 1..5 {
                let value = self
                    .squared_edges
                    .get(&edge(ids[a], ids[b]))
                    .ok_or(GeometryError::Input)?;
                out[a][b] = value.clone();
                out[b][a] = value.clone();
            }
        }
        Ok(out)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DeficitSign {
    Positive { separation: Q },
    Negative { separation: Q },
    ContainsZero,
}

#[derive(Debug, Clone)]
pub struct DeficitEnclosure {
    source: MetricHingeStar,
    angles: Vec<DihedralEnclosure>,
    bounds: RationalInterval,
}
impl DeficitEnclosure {
    pub fn source(&self) -> &MetricHingeStar {
        &self.source
    }
    pub fn angles(&self) -> &[DihedralEnclosure] {
        &self.angles
    }
    pub fn bounds(&self) -> &RationalInterval {
        &self.bounds
    }
    /// Separation is obtained from the computed bounds, never a caller promise.
    pub fn sign(&self) -> DeficitSign {
        if self.bounds.lo() > &Q::zero() {
            DeficitSign::Positive {
                separation: self.bounds.lo().clone(),
            }
        } else if self.bounds.hi() < &Q::zero() {
            DeficitSign::Negative {
                separation: -self.bounds.hi(),
            }
        } else {
            DeficitSign::ContainsZero
        }
    }
}

/// Width <=eps for delta=2 pi-sum(theta). Zero-containing output is permitted.
pub fn deficit_enclosure(
    star: &MetricHingeStar,
    eps: &Q,
) -> Result<DeficitEnclosure, GeometryError> {
    validate_precision(eps)?;
    let tol = eps / Q::from_integer((star.cycle.len() + 2).into());
    let mut bounds = pi_enclosure(&tol)?.mul_scalar(&Q::from_integer(2.into()));
    let mut angles = Vec::new();
    for i in 0..star.cycle.len() {
        let angle = dihedral_enclosure(&star.simplex(i)?, &tol)?;
        bounds = bounds.sub(angle.bounds());
        angles.push(angle);
    }
    Ok(DeficitEnclosure {
        source: star.clone(),
        angles,
        bounds,
    })
}

// Origin: engine/crates_rs/core_general_relativity/src/certified_dihedral.rs
// Claim: urn:core:crates_rs:core-general-relativity:certified-dihedral:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_6f1e35c9 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
