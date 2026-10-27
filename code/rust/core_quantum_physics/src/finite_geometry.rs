//! Exact finite configurations from QM_122. Enumerations have explicit finite bounds.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ddf6403f<T> {
    fn checked_invariant_ddf6403f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ddf6403f<T> for Option<T> {
    #[inline]
    fn checked_invariant_ddf6403f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ddf6403f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ddf6403f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{elimination, matrix as mx};
use num_bigint::BigInt;
use num_traits::Zero;
use core_homology::finite_cliques::{cliques, maximum_clique, validate_graph, CliqueError};
use core_number_theory::rational::{ri, Rational as Q};
use core_solvers::solver_sat_dpll::{BooleanError, BooleanOutcome, BooleanProblem};
use serde::Serialize;
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GeometryError {
    #[error("ray carrier requires1..128 nonzero vectors of the same dimension1..64")]
    Rays,
    #[error("Sorkin power {power} is outside1..=8")]
    Power { power: u32 },
    #[error("a context must contain distinct indexed mutually orthogonal rays")]
    Context,
    #[error("finite coloring or incidence computation exceeds its work budget")]
    Budget,
    #[error(transparent)]
    Graph(#[from] CliqueError),
    #[error(transparent)]
    Solver(#[from] BooleanError),
    #[error(transparent)]
    Matrix(#[from] linear_algebra::exact_field::ExactFieldError),
}
/// Exact ray orthogonality, including inputs whose integer dot product exceeds i64.
pub fn adjacent(v: &[Vec<i64>]) -> Result<Vec<u128>, GeometryError> {
    let d = v.first().map_or(0, Vec::len);
    if v.is_empty()
        || v.len() > 128
        || d == 0
        || d > 64
        || v.iter().any(|r| r.len() != d || r.iter().all(|x| *x == 0))
    {
        return Err(GeometryError::Rays);
    }
    Ok((0..v.len())
        .map(|i| {
            (0..v.len())
                .filter(|&j| {
                    i != j
                        && v[i]
                            .iter()
                            .zip(&v[j])
                            .map(|(&a, &b)| BigInt::from(a) * BigInt::from(b))
                            .sum::<BigInt>()
                            .is_zero()
                })
                .fold(0, |a, j| a | (1u128 << j))
        })
        .collect())
}
fn validate_coloring_frame(adj: &[u128], frame: &[usize]) -> Result<(), GeometryError> {
    if frame.is_empty() || frame.len() > adj.len() || frame.iter().any(|v| *v >= adj.len()) {
        return Err(GeometryError::Context);
    }
    let members = frame.iter().copied().collect::<BTreeSet<_>>();
    let non_clique = members
        .iter()
        .any(|a| members.iter().any(|b| a != b && adj[*a] & (1 << b) == 0));
    if members.len() != frame.len() || non_clique {
        return Err(GeometryError::Context);
    }
    Ok(())
}

fn coloring_problem(adj: &[u128], frames: &[Vec<usize>]) -> Result<BooleanProblem, GeometryError> {
    validate_graph(adj)?;
    if frames.len() > 4096 {
        return Err(GeometryError::Budget);
    }
    for frame in frames {
        validate_coloring_frame(adj, frame)?;
    }
    let pairs = (0..adj.len())
        .flat_map(|a| {
            (a + 1..adj.len())
                .filter(move |b| adj[a] & (1 << b) != 0)
                .map(move |b| (a, b))
        })
        .collect::<Vec<_>>();
    Ok(BooleanProblem::new(adj.len(), &pairs, frames)?)
}
fn colorable(adj: &[u128], frames: &[Vec<usize>]) -> Result<bool, GeometryError> {
    Ok(matches!(
        coloring_problem(adj, frames)?.solve(1 << 20)?,
        BooleanOutcome::Sat(_)
    ))
}
/// Complete finite valuation count, with at most24 rays and2^28 literal checks.
pub fn coloring_count_small(adj: &[u128], frames: &[Vec<usize>]) -> Result<usize, GeometryError> {
    if adj.len() > 24 {
        return Err(GeometryError::Budget);
    }
    let problem = coloring_problem(adj, frames)?;
    let clause_work =
        adj.len() * adj.len() + frames.iter().map(|f| f.len() * f.len()).sum::<usize>();
    let assignments = 1usize << adj.len();
    if assignments
        .checked_mul(clause_work)
        .is_none_or(|n| n > 1 << 28)
    {
        return Err(GeometryError::Budget);
    }
    Ok((0..assignments)
        .filter(|mask| {
            problem.verify_assignment(
                &(0..adj.len())
                    .map(|v| mask & (1 << v) != 0)
                    .collect::<Vec<_>>(),
            )
        })
        .count())
}

fn expand_sorkin_mask_term(mask: u32, p: u32) -> std::collections::BTreeMap<[u32; 3], Q> {
    let sign = if mask.count_ones() % 2 == 1 {
        ri(1)
    } else {
        ri(-1)
    };
    let mut term = std::collections::BTreeMap::from([([0, 0, 0], sign)]);
    for _ in 0..p {
        let mut next = std::collections::BTreeMap::new();
        for (power, c) in term {
            for i in 0..3 {
                if mask & (1 << i) != 0 {
                    let mut power = power;
                    power[i] += 1;
                    *next.entry(power).or_insert_with(|| ri(0)) += &c;
                }
            }
        }
        term = next;
    }
    term
}

/// Coefficients of the Sorkin polynomial, obtained by expanding all seven terms.
pub fn sorkin_coefficients(
    p: u32,
) -> Result<std::collections::BTreeMap<[u32; 3], Q>, GeometryError> {
    if p == 0 || p > 8 {
        return Err(GeometryError::Power { power: p });
    }
    let mut out = std::collections::BTreeMap::new();
    for mask in 1u32..8 {
        for (power, c) in expand_sorkin_mask_term(mask, p) {
            *out.entry(power).or_insert_with(|| ri(0)) += c;
        }
    }
    Ok(out)
}
fn incidence_rank(frames: &[Vec<usize>], n: usize) -> Result<usize, GeometryError> {
    let matrix = mx::from_fn(frames.len(), n, |r, c| {
        ri(i64::from(frames[r].contains(&c)))
    })?;
    Ok(elimination::rank_with_limits(
        &matrix,
        OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 28,
        },
    )?)
}
#[derive(Debug, Clone, Serialize)]
pub struct Configuration {
    pub rays: usize,
    pub orthogonal_pairs: usize,
    pub frames: usize,
    pub incidence_rank: usize,
    pub affine_nullity: usize,
    pub has_classical_coloring: bool,
    pub ray_frame_degrees: Vec<usize>,
}
pub fn config(adj: &[u128], frames: &[Vec<usize>]) -> Result<Configuration, GeometryError> {
    let n = adj.len();
    let has_classical_coloring = colorable(adj, frames)?;
    let r = incidence_rank(frames, n)?;
    Ok(Configuration {
        rays: n,
        orthogonal_pairs: adj.iter().map(|v| v.count_ones() as usize).sum::<usize>() / 2,
        frames: frames.len(),
        incidence_rank: r,
        affine_nullity: n - r,
        has_classical_coloring,
        ray_frame_degrees: (0..n)
            .map(|i| frames.iter().filter(|f| f.contains(&i)).count())
            .collect(),
    })
}

// Coordinates a+b*sqrt(2), reduced using sqrt(2)^2=2; all source coordinates are small integers.
pub fn peres() -> Configuration {
    type S = (i64, i64);
    let z = (0, 0);
    let o = (1, 0);
    let m = (-1, 0);
    let s = (0, 1);
    let ms = (0, -1);
    let mut v = vec![[o, z, z], [z, o, z], [z, z, o]];
    for a in [o, m] {
        v.extend([[a, o, z], [a, z, o], [z, a, o]])
    }
    for a in [s, ms] {
        v.extend([
            [z, o, a],
            [z, a, o],
            [o, z, a],
            [a, z, o],
            [o, a, z],
            [a, o, z],
        ])
    }
    for a in [o, m] {
        for b in [o, m] {
            v.extend([[a, b, s], [a, s, b], [s, a, b]])
        }
    }
    fn dot(a: &[S; 3], b: &[S; 3]) -> S {
        a.iter().zip(b).fold((0, 0), |(r, s), (&(a, b), &(c, d))| {
            (r + a * c + 2 * b * d, s + a * d + b * c)
        })
    }
    let adj: Vec<u128> = (0..v.len())
        .map(|i| {
            (0..v.len())
                .filter(|&j| i != j && dot(&v[i], &v[j]) == (0, 0))
                .fold(0, |a, j| a | (1 << j))
        })
        .collect();
    config(&adj, &cliques(&adj, 3).checked_invariant_ddf6403f("fixed Peres context budget"))
        .checked_invariant_ddf6403f("fixed admitted Peres configuration")
}
pub fn cabello_rays() -> Vec<Vec<i64>> {
    vec![
        vec![1, 1, 1, 1],
        vec![1, 1, 1, -1],
        vec![1, 1, 0, 0],
        vec![1, 1, -1, -1],
        vec![1, 0, 1, 0],
        vec![1, 0, 0, 1],
        vec![1, 0, 0, -1],
        vec![1, 0, -1, 0],
        vec![1, -1, 1, 1],
        vec![1, -1, 0, 0],
        vec![1, -1, -1, 1],
        vec![1, -1, -1, -1],
        vec![0, 1, 0, 1],
        vec![0, 1, 0, 0],
        vec![0, 1, -1, 0],
        vec![0, 0, 1, 0],
        vec![0, 0, 1, -1],
        vec![0, 0, 0, 1],
    ]
}
pub fn cabello() -> Configuration {
    let a = adjacent(&cabello_rays()).checked_invariant_ddf6403f("fixed admitted rays");
    config(&a, &cliques(&a, 4).checked_invariant_ddf6403f("fixed context budget"))
        .checked_invariant_ddf6403f("fixed admitted Cabello configuration")
}
fn canonical(v: Vec<i64>) -> Vec<i64> {
    let sign = v.iter().find(|&&x| x != 0).copied().unwrap_or(1).signum();
    v.into_iter().map(|x| x * sign).collect()
}
pub fn d4_rays() -> Vec<Vec<i64>> {
    let mut v = BTreeSet::new();
    for i in 0..4 {
        for j in i + 1..4 {
            for s in [-1, 1] {
                let mut x = vec![0; 4];
                x[i] = 1;
                x[j] = s;
                v.insert(x);
            }
        }
    }
    v.into_iter().collect()
}
pub fn e8_rays() -> Vec<Vec<i64>> {
    let mut rays = BTreeSet::new();
    for i in 0..8 {
        for j in i + 1..8 {
            for s in [-1, 1] {
                let mut v = vec![0; 8];
                v[i] = 1;
                v[j] = s;
                rays.insert(v);
            }
        }
    }
    for b in 0u32..256 {
        if b.count_ones() % 2 == 0 {
            rays.insert(canonical(
                (0..8)
                    .map(|i| if b & (1 << i) == 0 { 1 } else { -1 })
                    .collect(),
            ));
        }
    }
    rays.into_iter().collect()
}
#[derive(Debug, Clone, Serialize)]
pub struct E8Result {
    pub configuration: Configuration,
    pub roots: usize,
    pub max_nonorthogonal: usize,
    pub required_ones: usize,
}
pub fn e8() -> E8Result {
    let rays = e8_rays();
    let adj = adjacent(&rays).checked_invariant_ddf6403f("fixed admitted rays");
    let frames = cliques(&adj, 8).checked_invariant_ddf6403f("fixed E8 context budget");
    let mask = (1u128 << rays.len()) - 1;
    let non: Vec<_> = adj
        .iter()
        .enumerate()
        .map(|(i, a)| mask & !a & !(1 << i))
        .collect();
    let alpha = maximum_clique(&non).checked_invariant_ddf6403f("fixed E8 clique budget");
    let degrees: Vec<_> = (0..rays.len())
        .map(|i| frames.iter().filter(|f| f.contains(&i)).count())
        .collect();
    let required = frames.len() / degrees[0];
    let rank = incidence_rank(&frames, rays.len()).checked_invariant_ddf6403f("fixed E8 elimination budget");
    E8Result {
        roots: rays.len() * 2,
        max_nonorthogonal: alpha,
        required_ones: required,
        configuration: Configuration {
            rays: rays.len(),
            orthogonal_pairs: adj.iter().map(|v| v.count_ones() as usize).sum::<usize>() / 2,
            frames: frames.len(),
            incidence_rank: rank,
            affine_nullity: rays.len() - rank,
            has_classical_coloring: required <= alpha,
            ray_frame_degrees: degrees,
        },
    }
}
pub fn sorkin(a: &Q, b: &Q, c: &Q, p: u32) -> Result<Q, GeometryError> {
    if p == 0 || p > 8 {
        return Err(GeometryError::Power { power: p });
    }
    Ok((a + b + c).pow(p as i32)
        - (a + b).pow(p as i32)
        - (a + c).pow(p as i32)
        - (b + c).pow(p as i32)
        + a.pow(p as i32)
        + b.pow(p as i32)
        + c.pow(p as i32))
}
/// Negative part of the declared normal's quadratic form. This diagnostic is
/// zero for positive-semidefinite matrices; it is not a complete PSD test.
pub fn interface_defect(
    m: &BasicMatrix<Q>,
    normal: &[Q],
) -> Result<Q, linear_algebra::exact_field::ExactFieldError> {
    let image = mx::multiply_vector(m, normal)?;
    let value = mx::dot(normal, &image)?;
    Ok((-value).max(ri(0)))
}

// Origin: engine/crates_rs/core_quantum_physics/src/finite_geometry.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-geometry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finite_configurations() {
        let p = peres();
        assert_eq!((p.rays, p.orthogonal_pairs, p.frames), (33, 72, 16));
        assert!(!p.has_classical_coloring);
        let c = cabello();
        assert_eq!((c.rays, c.orthogonal_pairs, c.frames), (18, 63, 9));
        assert!(!c.has_classical_coloring);
        let d = adjacent(&d4_rays()).unwrap();
        assert_eq!(
            coloring_count_small(&d, &cliques(&d, 4).unwrap()).unwrap(),
            64
        );
        assert!(sorkin_coefficients(2).unwrap().values().all(Q::is_zero));
        assert_eq!(sorkin_coefficients(3).unwrap()[&[1, 1, 1]], ri(6));
    }
    #[test]
    fn full_e8_enumeration() {
        let r = e8();
        assert_eq!(
            (
                r.roots,
                r.configuration.frames,
                r.configuration.incidence_rank,
                r.max_nonorthogonal
            ),
            (240, 2025, 85, 8)
        );
        assert!(!r.configuration.has_classical_coloring);
        assert!(r.configuration.ray_frame_degrees.iter().all(|&d| d == 135));
    }
}
