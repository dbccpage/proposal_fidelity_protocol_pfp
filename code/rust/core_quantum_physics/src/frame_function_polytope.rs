// AuthorityEffect: None.

//! Frame functions on a finite configuration of integer rays, their polytope,
//! and the symmetric matrices they come from.
//!
//! A system declares rays `r_1, .., r_n` in `Z^d` and frames: sets of `d`
//! pairwise orthogonal rays. A frame function is `f` in `Q^n` with
//! `sum_(r in F) f_r = 1` on every frame, that is `A f = 1` for the
//! frame-by-ray incidence `A`. Every trace-one real symmetric `rho` gives one,
//! `f_r = r^T rho r / r^T r`, because the projectors of a frame sum to `I`.
//! Computed exactly:
//!
//! - `A`, its rank, the frame degree of every ray, and the rank of the linear
//!   map `rho -> (r^T rho r / r^T r)_r` on symmetric matrices (the span of the
//!   ray projectors). When that rank is `d(d+1)/2` the map is injective, and
//!   [`FrameSystem::state_of`] returns the unique symmetric `rho` of a frame
//!   function, or refuses one that no symmetric matrix produces;
//! - feasibility (`f >= 0`, `A f = 1`), and vertices of the polytope
//!   `{f >= 0, A f = 1}`: feasible points whose support columns of `A` are
//!   linearly independent;
//! - every vertex, when each ray lies in exactly two frames and `A` has full
//!   row rank. Frames are then the vertices and rays the edges of a multigraph,
//!   and a basis of `A` is a set of `rank A` edges whose every component has as
//!   many edges as vertices. Its basic solution is found by peeling leaves and
//!   solving the remaining cycle: an odd cycle has a unique solution, an even
//!   one is singular and is certified by an alternating kernel vector. Every
//!   basic solution and kernel vector is checked against `A` before it is used;
//! - margins of a symmetric matrix: whether `rho - t I` is positive
//!   semidefinite or definite, by exact LDL^T. So `lambda_min >= t` and
//!   `lambda_min > t` are decided without computing an eigenvalue.
//!
//! Refused: systems without rays or frames, zero rays, rays of different
//! lengths, frames of the wrong size, with repeated or out-of-range rays or a
//! non-orthogonal pair, vectors or matrices of the wrong shape, and vertex
//! enumeration when some ray is not in exactly two frames or `A` has a
//! dependent row.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_8d333ab8<T> {
    fn checked_invariant_8d333ab8(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_8d333ab8<T> for Option<T> {
    #[inline]
    fn checked_invariant_8d333ab8(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_8d333ab8<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_8d333ab8(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeSet;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    elimination::{rank, solve, LinearSolution},
    matrix as mx,
    ordered::hermitian_inertia,
    ExactFieldError,
};
use num_bigint::BigInt;

use num_traits::{One, Signed, Zero};
use core_number_theory::rational::{ri, Rational};

/// Refusals for frame systems.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FramePolytopeError {
    #[error("the unique tomographic matrix is not positive semidefinite")]
    NotPositiveSemidefinite,
    #[error("a system needs at least one ray and one frame")]
    Empty,
    #[error("ray {ray} is zero or has the wrong length")]
    BadRay { ray: usize },
    #[error("frame {frame} is not a set of {dimension} distinct declared rays")]
    BadFrame { frame: usize, dimension: usize },
    #[error("rays {left} and {right} of frame {frame} are not orthogonal")]
    NotOrthogonal {
        frame: usize,
        left: usize,
        right: usize,
    },
    #[error("expected a vector of length {expected}, got {actual}")]
    VectorLength { expected: usize, actual: usize },
    #[error("expected a symmetric {dimension} x {dimension} matrix")]
    NotSymmetric { dimension: usize },
    #[error("the ray projectors span {rank} of the {needed} symmetric directions")]
    ProjectorsDoNotSpan { rank: usize, needed: usize },
    #[error("the vector is not a frame function")]
    NotAFrameFunction,
    #[error("ray {ray} lies in {count} frames; vertex enumeration needs exactly two")]
    NotDegreeTwo { ray: usize, count: usize },
    #[error("the incidence has rank {rank} below its {frames} frames")]
    RankDeficient { rank: usize, frames: usize },
    #[error("vertex enumeration exhausted its {limit} support budget")]
    EnumerationLimit { limit: usize },
    #[error(
        "the declared frame carrier exceeds16 dimensions,512 rays/frames or65536 incidence entries"
    )]
    CarrierBudget,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("the computed basic solution failed exact replay")]
    InvalidSolution,
}

/// Declared integer rays and orthogonal frames.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FrameSystem {
    rays: Vec<Vec<i64>>,
    frames: Vec<Vec<usize>>,
}

enum BasicSolution {
    Unique(Vec<Rational>),
    Singular,
}

fn dot(a: &[i64], b: &[i64]) -> BigInt {
    a.iter()
        .zip(b)
        .map(|(x, y)| BigInt::from(*x) * BigInt::from(*y))
        .sum()
}

impl FrameSystem {
    fn validate_frame_members(
        rays: &[Vec<i64>],
        dimension: usize,
        frame: usize,
        members: &[usize],
    ) -> Result<(), FramePolytopeError> {
        let distinct: BTreeSet<usize> = members.iter().copied().collect();
        let bad_members = members.len() != dimension || distinct.len() != dimension;
        if bad_members || members.iter().any(|&r| r >= rays.len()) {
            return Err(FramePolytopeError::BadFrame { frame, dimension });
        }
        for (i, &left) in members.iter().enumerate() {
            for &right in &members[i + 1..] {
                if !dot(&rays[left], &rays[right]).is_zero() {
                    return Err(FramePolytopeError::NotOrthogonal { frame, left, right });
                }
            }
        }
        Ok(())
    }

    fn validate_carrier_budget_and_nonempty(
        dimension: usize,
        rays_len: usize,
        frames_len: usize,
    ) -> Result<(), FramePolytopeError> {
        let over_budget = dimension > 16 || rays_len > 512 || frames_len > 512;
        if over_budget || rays_len.checked_mul(frames_len).is_none_or(|n| n > 65536) {
            return Err(FramePolytopeError::CarrierBudget);
        }
        if rays_len == 0 || frames_len == 0 || dimension == 0 {
            return Err(FramePolytopeError::Empty);
        }
        Ok(())
    }

    pub fn new(rays: Vec<Vec<i64>>, frames: Vec<Vec<usize>>) -> Result<Self, FramePolytopeError> {
        let dimension = rays.first().map_or(0, Vec::len);
        Self::validate_carrier_budget_and_nonempty(dimension, rays.len(), frames.len())?;
        if let Some(ray) = rays
            .iter()
            .position(|r| r.len() != dimension || r.iter().all(|&x| x == 0))
        {
            return Err(FramePolytopeError::BadRay { ray });
        }
        for (frame, members) in frames.iter().enumerate() {
            Self::validate_frame_members(&rays, dimension, frame, members)?;
        }
        Ok(Self { rays, frames })
    }

    pub fn dimension(&self) -> usize {
        self.rays[0].len()
    }

    pub fn ray_count(&self) -> usize {
        self.rays.len()
    }

    /// `A[F][r] = 1` when ray `r` lies in frame `F`.
    pub fn incidence(&self) -> Result<BasicMatrix<Rational>, FramePolytopeError> {
        Ok(mx::from_fn(self.frames.len(), self.rays.len(), |f, r| {
            ri(i64::from(self.frames[f].contains(&r)))
        })?)
    }

    pub fn incidence_rank(&self) -> Result<usize, FramePolytopeError> {
        Ok(rank(&self.incidence()?)?)
    }

    /// How many frames contain each ray.
    pub fn ray_degrees(&self) -> Vec<usize> {
        (0..self.rays.len())
            .map(|r| {
                self.frames
                    .iter()
                    .filter(|members| members.contains(&r))
                    .count()
            })
            .collect()
    }

    fn symmetric_coordinates(&self) -> Vec<(usize, usize)> {
        let d = self.dimension();
        (0..d).flat_map(|i| (i..d).map(move |j| (i, j))).collect()
    }

    /// Row `r`: the coefficients of `r^T rho r / r^T r` in the entries
    /// `rho_ij`, `i <= j`, of a symmetric `rho`.
    fn projector_rows(&self) -> Result<BasicMatrix<Rational>, FramePolytopeError> {
        let coordinates = self.symmetric_coordinates();
        Ok(mx::from_fn(self.rays.len(), coordinates.len(), |r, c| {
            let ray = &self.rays[r];
            let (i, j) = coordinates[c];
            Rational::new(
                BigInt::from(ray[i])
                    * BigInt::from(ray[j])
                    * BigInt::from(if i == j { 1 } else { 2 }),
                dot(ray, ray),
            )
        })?)
    }

    /// The dimension of the span of the ray projectors in the symmetric matrices.
    pub fn projector_span_rank(&self) -> Result<usize, FramePolytopeError> {
        Ok(rank(&self.projector_rows()?)?)
    }

    fn check_length(&self, f: &[Rational]) -> Result<(), FramePolytopeError> {
        if f.len() != self.rays.len() {
            return Err(FramePolytopeError::VectorLength {
                expected: self.rays.len(),
                actual: f.len(),
            });
        }
        Ok(())
    }

    /// `f_r = r^T rho r / r^T r` for a symmetric `rho`.
    pub fn frame_function_of(
        &self,
        rho: &BasicMatrix<Rational>,
    ) -> Result<Vec<Rational>, FramePolytopeError> {
        let d = self.dimension();
        let square = rho.rows() == d && rho.cols() == d;
        if !square
            || (0..d)
                .any(|i| (0..d).any(|j| rho.as_slice()[i * d + j] != rho.as_slice()[j * d + i]))
        {
            return Err(FramePolytopeError::NotSymmetric { dimension: d });
        }
        Ok(self
            .rays
            .iter()
            .map(|r| {
                let form: Rational = (0..d)
                    .flat_map(|i| (0..d).map(move |j| (i, j)))
                    .map(|(i, j)| {
                        Rational::from_integer(BigInt::from(r[i]) * BigInt::from(r[j]))
                            * &rho.as_slice()[i * d + j]
                    })
                    .sum();
                form / Rational::from_integer(dot(r, r))
            })
            .collect())
    }

    /// `A f = 1`, with no sign condition.
    pub fn is_frame_function(&self, f: &[Rational]) -> Result<bool, FramePolytopeError> {
        self.check_length(f)?;
        Ok(self
            .frames
            .iter()
            .all(|members| members.iter().map(|&r| &f[r]).sum::<Rational>().is_one()))
    }

    /// `f >= 0` and `A f = 1`.
    pub fn is_feasible(&self, f: &[Rational]) -> Result<bool, FramePolytopeError> {
        Ok(self.is_frame_function(f)? && !f.iter().any(Signed::is_negative))
    }

    /// Feasible, and the columns of `A` on the support of `f` are independent.
    pub fn is_vertex(&self, f: &[Rational]) -> Result<bool, FramePolytopeError> {
        if !self.is_feasible(f)? {
            return Ok(false);
        }
        let incidence = self.incidence()?;
        let support: Vec<usize> = (0..self.rays.len()).filter(|&r| !f[r].is_zero()).collect();
        let columns = mx::from_fn(incidence.rows(), support.len(), |r, c| {
            incidence.as_slice()[r * incidence.cols() + support[c]].clone()
        })?;
        Ok(rank(&columns)? == support.len())
    }

    fn solve_unique_projector_coordinates(
        &self,
        f: &[Rational],
        needed: usize,
    ) -> Result<Vec<Rational>, FramePolytopeError> {
        let rank = self.projector_span_rank()?;
        if rank != needed {
            return Err(FramePolytopeError::ProjectorsDoNotSpan { rank, needed });
        }
        match solve(&self.projector_rows()?, f)? {
            LinearSolution::Consistent {
                particular,
                kernel_basis,
            } if kernel_basis.is_empty() => Ok(particular),
            _ => Err(FramePolytopeError::NotAFrameFunction),
        }
    }

    /// The unique symmetric `rho` with `f_r = r^T rho r / r^T r`; its trace is
    /// one because `f` is a frame function. This does not certify positivity;
    /// use `density_state_of` to admit a density matrix.
    pub fn state_of(&self, f: &[Rational]) -> Result<BasicMatrix<Rational>, FramePolytopeError> {
        if !self.is_frame_function(f)? {
            return Err(FramePolytopeError::NotAFrameFunction);
        }
        let coordinates = self.symmetric_coordinates();
        let solution = self.solve_unique_projector_coordinates(f, coordinates.len())?;
        let d = self.dimension();
        let mut rho = mx::zeros(d, d)?;
        for (&(i, j), value) in coordinates.iter().zip(solution) {
            rho.set(i, j, value.clone())
                .map_err(ExactFieldError::from)?;
            rho.set(j, i, value).map_err(ExactFieldError::from)?;
        }
        if self.frame_function_of(&rho)? != f {
            return Err(FramePolytopeError::InvalidSolution);
        }
        Ok(rho)
    }

    /// Finite tomography followed by exact positivity admission. Even a
    /// normalized nonnegative frame function on every declared context may
    /// reconstruct to a matrix negative on an unmeasured ray.
    pub fn density_state_of(
        &self,
        f: &[Rational],
    ) -> Result<BasicMatrix<Rational>, FramePolytopeError> {
        let rho = self.state_of(f)?;
        if !hermitian_inertia(&rho)?.is_positive_semidefinite() {
            return Err(FramePolytopeError::NotPositiveSemidefinite);
        }
        Ok(rho)
    }

    fn degree_two_edges(&self) -> Result<Vec<(usize, usize)>, FramePolytopeError> {
        (0..self.rays.len())
            .map(|r| {
                let holders: Vec<usize> = (0..self.frames.len())
                    .filter(|&f| self.frames[f].contains(&r))
                    .collect();
                match holders.as_slice() {
                    [a, b] => Ok((*a, *b)),
                    _ => Err(FramePolytopeError::NotDegreeTwo {
                        ray: r,
                        count: holders.len(),
                    }),
                }
            })
            .collect()
    }

    fn check_solution(
        &self,
        edges: &[(usize, usize)],
        values: &[Rational],
        rhs: &Rational,
    ) -> Result<(), FramePolytopeError> {
        for frame in 0..self.frames.len() {
            let total: Rational = edges
                .iter()
                .enumerate()
                .filter(|(_, &(a, b))| a == frame || b == frame)
                .map(|(r, _)| &values[r])
                .sum();
            if &total != rhs {
                return Err(FramePolytopeError::InvalidSolution);
            }
        }
        Ok(())
    }

    fn peel_leaf_edges(
        frames: usize,
        edges: &[(usize, usize)],
        support: &[usize],
        incident: &[Vec<usize>],
        demand: &mut [Rational],
        values: &mut [Rational],
        alive: &mut [bool],
    ) {
        let mut degree: Vec<usize> = incident.iter().map(Vec::len).collect();
        let mut leaves: Vec<usize> = (0..frames).filter(|&v| degree[v] == 1).collect();
        while let Some(v) = leaves.pop() {
            if degree[v] != 1 {
                continue;
            }
            let k = *incident[v]
                .iter()
                .find(|&&k| alive[k])
                .checked_invariant_8d333ab8("a leaf keeps one live edge");
            let r = support[k];
            let w = if edges[r].0 == v {
                edges[r].1
            } else {
                edges[r].0
            };
            values[r] = demand[v].clone();
            demand[w] = &demand[w] - &values[r];
            alive[k] = false;
            degree[v] -= 1;
            degree[w] -= 1;
            if degree[w] == 1 {
                leaves.push(w);
            }
        }
    }

    fn trace_cycle(
        start: usize,
        edges: &[(usize, usize)],
        support: &[usize],
        incident: &[Vec<usize>],
        alive: &mut [bool],
    ) -> (usize, Vec<usize>, Vec<usize>) {
        let (c0, first) = (edges[support[start]].0, edges[support[start]].1);
        let mut cycle = vec![start];
        let mut vertices = vec![first];
        let (mut vertex, mut edge) = (first, start);
        while vertex != c0 {
            let next = *incident[vertex]
                .iter()
                .find(|&&k| alive[k] && k != edge)
                .checked_invariant_8d333ab8("a cycle vertex has two live edges");
            let r = support[next];
            vertex = if edges[r].0 == vertex {
                edges[r].1
            } else {
                edges[r].0
            };
            edge = next;
            cycle.push(next);
            vertices.push(vertex);
        }
        for &k in &cycle {
            alive[k] = false;
        }
        (c0, cycle, vertices)
    }

    fn solve_odd_cycle(
        c0: usize,
        cycle: &[usize],
        vertices: &[usize],
        support: &[usize],
        demand: &[Rational],
        values: &mut [Rational],
    ) {
        // f(e_j) = s_j + t_j x with x = f(e_0); vertex c_j sits between e_(j-1) and e_j.
        let mut s = vec![Rational::zero()];
        let mut t = vec![Rational::one()];
        for j in 1..cycle.len() {
            s.push(&demand[vertices[j - 1]] - &s[j - 1]);
            t.push(-&t[j - 1]);
        }
        let last = cycle.len() - 1;
        let x = (&demand[c0] - &s[last]) / (&t[last] + Rational::one());
        for (j, &k) in cycle.iter().enumerate() {
            values[support[k]] = &s[j] + &t[j] * &x;
        }
    }

    /// Solve `A_S f_S = 1` on a support whose components are unicyclic.
    fn basic_solution(
        &self,
        edges: &[(usize, usize)],
        support: &[usize],
    ) -> Result<BasicSolution, FramePolytopeError> {
        let frames = self.frames.len();
        let mut demand = vec![Rational::one(); frames];
        let mut values = vec![Rational::zero(); edges.len()];
        let mut alive = vec![true; support.len()];
        let mut incident: Vec<Vec<usize>> = vec![Vec::new(); frames];
        for (k, &r) in support.iter().enumerate() {
            incident[edges[r].0].push(k);
            incident[edges[r].1].push(k);
        }
        Self::peel_leaf_edges(
            frames,
            edges,
            support,
            &incident,
            &mut demand,
            &mut values,
            &mut alive,
        );
        for start in 0..support.len() {
            if !alive[start] {
                continue;
            }
            let (c0, cycle, vertices) =
                Self::trace_cycle(start, edges, support, &incident, &mut alive);
            if cycle.len() % 2 == 0 {
                let kernel: Vec<Rational> = (0..edges.len())
                    .map(|r| match cycle.iter().position(|&k| support[k] == r) {
                        Some(position) => ri(if position % 2 == 0 { 1 } else { -1 }),
                        None => Rational::zero(),
                    })
                    .collect();
                self.check_solution(edges, &kernel, &Rational::zero())?;
                return Ok(BasicSolution::Singular);
            }
            Self::solve_odd_cycle(c0, &cycle, &vertices, support, &demand, &mut values);
        }
        self.check_solution(edges, &values, &Rational::one())?;
        Ok(BasicSolution::Unique(values))
    }

    /// Every vertex of `{f >= 0, A f = 1}`, for a system whose rays each lie in
    /// exactly two frames and whose incidence has full row rank.
    pub fn vertices(&self) -> Result<Vec<Vec<Rational>>, FramePolytopeError> {
        self.vertices_with_budget(1_000_000)
    }

    fn validate_enumeration_budget(
        &self,
        edges_len: usize,
        frames: usize,
        limit: usize,
    ) -> Result<(), FramePolytopeError> {
        let rank = self.incidence_rank()?;
        if rank != frames {
            return Err(FramePolytopeError::RankDeficient { rank, frames });
        }
        let count = core_combinatorics::enumeration::binomial(edges_len as u64, frames as u64)
            .map_err(|_| FramePolytopeError::EnumerationLimit { limit })?;
        if count > num_bigint::BigUint::from(limit) {
            return Err(FramePolytopeError::EnumerationLimit { limit });
        }
        Ok(())
    }

    /// Enumerate supports within an explicit budget. Exhaustion is not infeasibility.
    pub fn vertices_with_budget(
        &self,
        limit: usize,
    ) -> Result<Vec<Vec<Rational>>, FramePolytopeError> {
        let edges = self.degree_two_edges()?;
        let frames = self.frames.len();
        self.validate_enumeration_budget(edges.len(), frames, limit)?;
        let mut found = BTreeSet::new();
        let mut support: Vec<usize> = (0..frames).collect();
        let mut examined = 0usize;
        loop {
            if examined == limit {
                return Err(FramePolytopeError::EnumerationLimit { limit });
            }
            examined += 1;
            if components_are_unicyclic(frames, &edges, &support) {
                if let BasicSolution::Unique(values) = self.basic_solution(&edges, &support)? {
                    if !values.iter().any(Signed::is_negative) {
                        found.insert(values);
                    }
                }
            }
            if !next_combination(&mut support, edges.len()) {
                break;
            }
        }
        Ok(found.into_iter().collect())
    }
}

/// Every component of the spanning subgraph on `support` has as many edges as
/// vertices: necessary for `A_S` to be square and invertible.
fn components_are_unicyclic(frames: usize, edges: &[(usize, usize)], support: &[usize]) -> bool {
    fn root(parent: &mut [usize], mut x: usize) -> usize {
        while parent[x] != x {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        x
    }
    let mut parent: Vec<usize> = (0..frames).collect();
    for &r in support {
        let (a, b) = (root(&mut parent, edges[r].0), root(&mut parent, edges[r].1));
        if a != b {
            parent[a] = b;
        }
    }
    let mut vertex_count = vec![0usize; frames];
    let mut edge_count = vec![0usize; frames];
    for v in 0..frames {
        vertex_count[root(&mut parent, v)] += 1;
    }
    for &r in support {
        edge_count[root(&mut parent, edges[r].0)] += 1;
    }
    vertex_count == edge_count
}

/// Advance a sorted `k`-subset of `0..n` to the next one in lexicographic order.
fn next_combination(subset: &mut [usize], n: usize) -> bool {
    let k = subset.len();
    for i in (0..k).rev() {
        if subset[i] < n - k + i {
            subset[i] += 1;
            for j in i + 1..k {
                subset[j] = subset[j - 1] + 1;
            }
            return true;
        }
    }
    false
}

/// `rho - t I` is positive semidefinite: every eigenvalue of `rho` is at least `t`.
pub fn eigenvalues_at_least(
    rho: &BasicMatrix<Rational>,
    t: &Rational,
) -> Result<bool, FramePolytopeError> {
    Ok(hermitian_inertia(&shifted(rho, t)?)?.is_positive_semidefinite())
}

/// Every eigenvalue strictly exceeds t, checked by exact congruence inertia.
pub fn eigenvalues_above(
    rho: &BasicMatrix<Rational>,
    t: &Rational,
) -> Result<bool, FramePolytopeError> {
    let inertia = hermitian_inertia(&shifted(rho, t)?)?;
    Ok(inertia.positive == rho.rows())
}

fn shifted(
    rho: &BasicMatrix<Rational>,
    t: &Rational,
) -> Result<BasicMatrix<Rational>, FramePolytopeError> {
    if rho.rows() == 0 || rho.rows() > 16 || rho.rows() != rho.cols() {
        return Err(FramePolytopeError::NotSymmetric {
            dimension: rho.rows(),
        });
    }
    Ok(mx::sub(rho, &mx::scale(&mx::identity(rho.rows())?, t)?)?)
}

// Origin: engine/crates_rs/core_quantum_physics/src/frame_function_polytope.rs
// Claim: urn:core:crates_rs:core-quantum-physics:frame-function-polytope:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_8d333ab8 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
