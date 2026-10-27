//! Bounded exact convex geometry over Q. Elimination belongs to linear_algebra.
//!
//! A convex-hull negative result exhausts every affinely independent support
//! of size at most d+1 (Caratheodory). Vertex enumeration exhausts full-rank
//! active sets of the H-representation; an empty vertex list does not assert
//! that an unbounded polyhedron is empty. A budget refusal is neither result.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    elimination::{rank, solve, LinearSolution},
    matrix, ExactFieldError,
};
use num_bigint::BigUint;
use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};
use core_combinatorics::enumeration::{binomial, combinations, CombinatoricsError};
use thiserror::Error;

pub const MAX_GEOMETRY_DIMENSION: usize = 64;
pub const MAX_GEOMETRY_ROWS: usize = 4096;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ConvexGeometryError {
    #[error("incompatible dimensions or ragged point coordinates")]
    Shape,
    #[error("geometry exceeds the finite dimension or row limit")]
    SizeLimit,
    #[error("convex witness fails exact replay")]
    InvalidWitness,
    #[error("a rational geometry or certificate entry has a zero denominator")]
    InvalidRational,
    #[error("packing coefficients and bounds must be nonnegative")]
    NegativePackingData,
    #[error("positive-objective column {column} has no constraint")]
    UnboundedPacking { column: usize },
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
    #[error(transparent)]
    Enumeration(#[from] CombinatoricsError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConvexWitness {
    /// Indices of distinct input points; all omitted weights are zero.
    pub support: Vec<usize>,
    pub weights: Vec<BigRational>,
}

fn validate_convex_witness_support(
    points_len: usize,
    w: &ConvexWitness,
) -> Result<(), ConvexGeometryError> {
    let valid_len = !w.support.is_empty()
        && w.support.len() == w.weights.len()
        && w.support.len() <= points_len;
    let valid_indices = w.support.iter().all(|i| *i < points_len)
        && w.support.windows(2).all(|s| s[0] < s[1]);
    if !valid_len || !valid_indices {
        return Err(ConvexGeometryError::InvalidWitness);
    }
    Ok(())
}

fn validate_convex_witness_weights(w: &ConvexWitness) -> Result<(), ConvexGeometryError> {
    validate_rationals(&w.weights)?;
    if w.weights.iter().any(Signed::is_negative)
        || w.weights.iter().cloned().sum::<BigRational>() != BigRational::one()
    {
        return Err(ConvexGeometryError::InvalidWitness);
    }
    Ok(())
}

/// Recompute the affine combination against the actual input carrier.
pub fn verify_convex_witness(
    points: &[Vec<BigRational>],
    target: &[BigRational],
    w: &ConvexWitness,
) -> Result<(), ConvexGeometryError> {
    validate_points(points, target)?;
    validate_convex_witness_support(points.len(), w)?;
    validate_convex_witness_weights(w)?;
    for (j, t) in target.iter().enumerate() {
        let value: BigRational = w
            .support
            .iter()
            .zip(&w.weights)
            .map(|(i, weight)| points[*i][j].clone() * weight)
            .sum();
        if &value != t {
            return Err(ConvexGeometryError::InvalidWitness);
        }
    }
    Ok(())
}

fn validate_points(
    points: &[Vec<BigRational>],
    target: &[BigRational],
) -> Result<(), ConvexGeometryError> {
    if target.len() > MAX_GEOMETRY_DIMENSION || points.len() > MAX_GEOMETRY_ROWS {
        return Err(ConvexGeometryError::SizeLimit);
    }
    if points.iter().any(|p| p.len() != target.len()) {
        return Err(ConvexGeometryError::Shape);
    }
    validate_rationals(points.iter().flatten().chain(target))
}

fn validate_rationals<'a>(
    values: impl IntoIterator<Item = &'a BigRational>,
) -> Result<(), ConvexGeometryError> {
    if values.into_iter().any(|q| q.denom().is_zero()) {
        Err(ConvexGeometryError::InvalidRational)
    } else {
        Ok(())
    }
}

fn check_count(
    what: &'static str,
    count: BigUint,
    budget: usize,
) -> Result<(), ConvexGeometryError> {
    if count > BigUint::from(budget) {
        return Err(CombinatoricsError::BudgetExceeded {
            what,
            requested: count,
            limit: budget,
        }
        .into());
    }
    Ok(())
}

/// Complete finite convex-hull membership; None means outside this input hull.
/// Candidate count is bounded before searching, so even an early witness never
/// disguises a caller budget that cannot support the declared complete search.
fn try_convex_support(
    points: &[Vec<BigRational>],
    target: &[BigRational],
    rhs: &[BigRational],
    support: Vec<usize>,
) -> Result<Option<ConvexWitness>, ConvexGeometryError> {
    let k = support.len();
    let affine = matrix::from_fn(target.len() + 1, k, |r, c| {
        if r == target.len() {
            BigRational::one()
        } else {
            points[support[c]][r].clone()
        }
    })?;
    if let LinearSolution::Consistent {
        particular,
        kernel_basis,
    } = solve(&affine, rhs)?
    {
        if kernel_basis.is_empty() && particular.iter().all(|q| !q.is_negative()) {
            let witness = ConvexWitness {
                support,
                weights: particular,
            };
            verify_convex_witness(points, target, &witness)?;
            return Ok(Some(witness));
        }
    }
    Ok(None)
}

pub fn convex_membership(
    points: &[Vec<BigRational>],
    target: &[BigRational],
    candidate_budget: usize,
) -> Result<Option<ConvexWitness>, ConvexGeometryError> {
    validate_points(points, target)?;
    let max_support = points.len().min(target.len() + 1);
    let count = (1..=max_support).try_fold(BigUint::zero(), |sum, k| {
        Ok::<_, CombinatoricsError>(sum + binomial(points.len() as u64, k as u64)?)
    })?;
    check_count("convex supports", count, candidate_budget)?;
    let mut rhs = target.to_vec();
    rhs.push(BigRational::one());
    for k in 1..=max_support {
        for support in combinations(points.len(), k, candidate_budget)? {
            if let Some(witness) = try_convex_support(points, target, &rhs, support)? {
                return Ok(Some(witness));
            }
        }
    }
    Ok(None)
}

fn satisfies(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
    x: &[BigRational],
    equal: bool,
) -> Result<bool, ConvexGeometryError> {
    let value = matrix::multiply_vector(a, x)?;
    Ok(value
        .iter()
        .zip(b)
        .all(|(v, b)| if equal { v == b } else { v <= b }))
}

/// Vertices of {x : E x = e, A x <= b}, sorted and deduplicated exactly.
/// Each returned point solves a full-rank active system and replays all original
/// constraints. This also works for lower-dimensional and unbounded carriers.
fn validate_vertex_enum_carrier(
    e: &BasicMatrix<BigRational>,
    erhs: &[BigRational],
    a: &BasicMatrix<BigRational>,
    bounds: &[BigRational],
) -> Result<(), ConvexGeometryError> {
    if e.cols() != a.cols() || e.rows() != erhs.len() || a.rows() != bounds.len() {
        return Err(ConvexGeometryError::Shape);
    }
    if a.cols() > MAX_GEOMETRY_DIMENSION
        || e.rows() > MAX_GEOMETRY_ROWS
        || a.rows() > MAX_GEOMETRY_ROWS
    {
        return Err(ConvexGeometryError::SizeLimit);
    }
    validate_rationals(
        e.as_slice()
            .iter()
            .chain(erhs)
            .chain(a.as_slice())
            .chain(bounds),
    )
}

fn solve_active_vertex_candidate(
    e: &BasicMatrix<BigRational>,
    erhs: &[BigRational],
    a: &BasicMatrix<BigRational>,
    bounds: &[BigRational],
    support: &[usize],
) -> Result<Option<Vec<BigRational>>, ConvexGeometryError> {
    let d = a.cols();
    let active = support.len();
    let system = matrix::from_fn(e.rows() + active, d, |r, c| {
        if r < e.rows() {
            e.as_slice()[r * d + c].clone()
        } else {
            a.as_slice()[support[r - e.rows()] * d + c].clone()
        }
    })?;
    let mut rhs = erhs.to_vec();
    rhs.extend(support.iter().map(|i| bounds[*i].clone()));
    let LinearSolution::Consistent {
        particular,
        kernel_basis,
    } = solve(&system, &rhs)?
    else {
        return Ok(None);
    };
    if kernel_basis.is_empty()
        && satisfies(e, erhs, &particular, true)?
        && satisfies(a, bounds, &particular, false)?
    {
        Ok(Some(particular))
    } else {
        Ok(None)
    }
}

fn collect_enumerated_vertices(
    e: &BasicMatrix<BigRational>,
    erhs: &[BigRational],
    a: &BasicMatrix<BigRational>,
    bounds: &[BigRational],
    active: usize,
    candidate_budget: usize,
) -> Result<Vec<Vec<BigRational>>, ConvexGeometryError> {
    let mut vertices = std::collections::BTreeSet::new();
    for support in combinations(a.rows(), active, candidate_budget)? {
        if let Some(v) = solve_active_vertex_candidate(e, erhs, a, bounds, &support)? {
            vertices.insert(v);
        }
    }
    Ok(vertices.into_iter().collect())
}

pub fn vertex_enumeration(
    e: &BasicMatrix<BigRational>,
    erhs: &[BigRational],
    a: &BasicMatrix<BigRational>,
    bounds: &[BigRational],
    candidate_budget: usize,
) -> Result<Vec<Vec<BigRational>>, ConvexGeometryError> {
    validate_vertex_enum_carrier(e, erhs, a, bounds)?;
    if !solve(e, erhs)?.is_consistent() {
        return Ok(Vec::new());
    }
    let active = a.cols() - rank(e)?;
    check_count(
        "polyhedron active sets",
        binomial(a.rows() as u64, active as u64)?,
        candidate_budget,
    )?;
    collect_enumerated_vertices(e, erhs, a, bounds, active, candidate_budget)
}

/// A certificate for max sum(x) subject to x>=0 and A x<=b.
/// The dual is min b.y subject to y>=0 and A^T y>=1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PackingWitness {
    pub primal: Vec<BigRational>,
    pub dual: Vec<BigRational>,
    pub value: BigRational,
}

fn validate_packing(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
) -> Result<(), ConvexGeometryError> {
    if a.rows() != b.len() {
        return Err(ConvexGeometryError::Shape);
    }
    // Both primal and dual carriers are explicitly finite.
    if a.cols() > MAX_GEOMETRY_DIMENSION || a.rows() > MAX_GEOMETRY_DIMENSION {
        return Err(ConvexGeometryError::SizeLimit);
    }
    validate_rationals(a.as_slice().iter().chain(b))?;
    if a.as_slice().iter().chain(b).any(Signed::is_negative) {
        return Err(ConvexGeometryError::NegativePackingData);
    }
    Ok(())
}

/// Replay primal feasibility, all dual inequalities, and equality of objectives.
/// Weak duality then certifies global optimality independently of enumeration.
fn validate_packing_witness_vectors(
    a: &BasicMatrix<BigRational>,
    w: &PackingWitness,
) -> Result<(), ConvexGeometryError> {
    if w.primal.len() != a.cols() || w.dual.len() != a.rows() {
        return Err(ConvexGeometryError::InvalidWitness);
    }
    validate_rationals(
        w.primal
            .iter()
            .chain(&w.dual)
            .chain(std::iter::once(&w.value)),
    )?;
    if w.primal.iter().chain(&w.dual).any(Signed::is_negative) {
        return Err(ConvexGeometryError::InvalidWitness);
    }
    Ok(())
}

pub fn verify_packing_witness(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
    w: &PackingWitness,
) -> Result<(), ConvexGeometryError> {
    validate_packing(a, b)?;
    validate_packing_witness_vectors(a, w)?;
    if !satisfies(a, b, &w.primal, false)? {
        return Err(ConvexGeometryError::InvalidWitness);
    }
    let dual_lhs = matrix::multiply_vector(&matrix::transpose(a)?, &w.dual)?;
    let dual_obj: BigRational = b.iter().zip(&w.dual).map(|(b_i, y)| b_i * y).sum();
    if dual_lhs.iter().any(|q| q < &BigRational::one())
        || w.primal.iter().sum::<BigRational>() != w.value
        || dual_obj != w.value
    {
        return Err(ConvexGeometryError::InvalidWitness);
    }
    Ok(())
}

/// Complete bounded packing optimum with a replayed primal/dual certificate.
/// Nonnegative data makes zero feasible. Every nonzero column is constrained,
/// so the remaining feasible primal carrier is compact. Zero-bound rows first
/// force their incident columns to zero; this also handles strongly contextual
/// support models without enumerating impossible assignments.
fn classify_packing_columns(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
) -> Result<(Vec<BigRational>, Vec<usize>), ConvexGeometryError> {
    let (m, n) = (a.rows(), a.cols());
    for j in 0..n {
        if (0..m).all(|i| a.as_slice()[i * n + j].is_zero()) {
            return Err(ConvexGeometryError::UnboundedPacking { column: j });
        }
    }
    let mut zero_dual = vec![BigRational::zero(); m];
    let mut free = Vec::new();
    for j in 0..n {
        if let Some(i) = (0..m).find(|&i| b[i].is_zero() && !a.as_slice()[i * n + j].is_zero()) {
            zero_dual[i] += BigRational::one() / &a.as_slice()[i * n + j];
        } else {
            free.push(j);
        }
    }
    Ok((zero_dual, free))
}

fn solve_packing_primal(
    reduced: &BasicMatrix<BigRational>,
    b: &[BigRational],
    candidate_budget: usize,
) -> Result<(Vec<BigRational>, usize), ConvexGeometryError> {
    let (m, k) = (reduced.rows(), reduced.cols());
    let inequalities = matrix::from_fn(m + k, k, |i, j| {
        if i < m {
            reduced.as_slice()[i * k + j].clone()
        } else if i - m == j {
            -BigRational::one()
        } else {
            BigRational::zero()
        }
    })?;
    let mut bounds = b.to_vec();
    bounds.resize(m + k, BigRational::zero());
    let primal_count = binomial((m + k) as u64, k as u64)?;
    check_count(
        "packing primal active sets",
        primal_count.clone(),
        candidate_budget,
    )?;
    let vertices = vertex_enumeration(
        &matrix::zeros(0, k)?,
        &[],
        &inequalities,
        &bounds,
        candidate_budget,
    )?;
    let x = vertices
        .into_iter()
        .max_by_key(|x| x.iter().sum::<BigRational>())
        .ok_or(ConvexGeometryError::InvalidWitness)?;
    let remaining = candidate_budget
        - primal_count
            .to_usize()
            .ok_or(ConvexGeometryError::SizeLimit)?;
    Ok((x, remaining))
}

fn solve_packing_dual(
    reduced: &BasicMatrix<BigRational>,
    b: &[BigRational],
    x: &[BigRational],
    remaining: usize,
) -> Result<(Vec<usize>, Vec<BigRational>), ConvexGeometryError> {
    let (m, k) = (reduced.rows(), reduced.cols());
    let values = matrix::multiply_vector(reduced, x)?;
    let tight: Vec<usize> = (0..m).filter(|&i| values[i] == b[i]).collect();
    let positive: Vec<usize> = (0..k).filter(|&j| !x[j].is_zero()).collect();
    // Complementarity permits setting every loose-row dual variable to zero.
    let equalities = matrix::from_fn(positive.len(), tight.len(), |r, c| {
        reduced.as_slice()[tight[c] * k + positive[r]].clone()
    })?;
    let rhs = vec![BigRational::one(); positive.len()];
    let dual_ineq = matrix::from_fn(k + tight.len(), tight.len(), |r, c| {
        if r < k {
            -reduced.as_slice()[tight[c] * k + r].clone()
        } else if r - k == c {
            -BigRational::one()
        } else {
            BigRational::zero()
        }
    })?;
    let mut dual_bounds = vec![-BigRational::one(); k];
    dual_bounds.resize(k + tight.len(), BigRational::zero());
    let dual_vertices = vertex_enumeration(&equalities, &rhs, &dual_ineq, &dual_bounds, remaining)?;
    let y = dual_vertices
        .into_iter()
        .min_by_key(|y| {
            tight
                .iter()
                .zip(y)
                .map(|(&i, y)| &b[i] * y)
                .sum::<BigRational>()
        })
        .ok_or(ConvexGeometryError::InvalidWitness)?;
    Ok((tight, y))
}

fn assemble_packing_witness(
    n: usize,
    free: &[usize],
    zero_dual: Vec<BigRational>,
    x: &[BigRational],
    tight: &[usize],
    y: Vec<BigRational>,
) -> PackingWitness {
    let mut primal = vec![BigRational::zero(); n];
    for (&j, x_j) in free.iter().zip(x) {
        primal[j] = x_j.clone();
    }
    let mut dual = zero_dual;
    for (&i, y_i) in tight.iter().zip(y) {
        dual[i] += y_i;
    }
    let value = primal.iter().sum();
    PackingWitness {
        primal,
        dual,
        value,
    }
}

pub fn packing_optimum(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
    candidate_budget: usize,
) -> Result<PackingWitness, ConvexGeometryError> {
    validate_packing(a, b)?;
    check_count("packing candidates", BigUint::one(), candidate_budget)?;
    let (m, n) = (a.rows(), a.cols());
    let (zero_dual, free) = classify_packing_columns(a, b)?;
    if free.is_empty() {
        let w = PackingWitness {
            primal: vec![BigRational::zero(); n],
            dual: zero_dual,
            value: BigRational::zero(),
        };
        verify_packing_witness(a, b, &w)?;
        return Ok(w);
    }
    let reduced = matrix::from_fn(m, free.len(), |i, j| a.as_slice()[i * n + free[j]].clone())?;
    let (x, remaining) = solve_packing_primal(&reduced, b, candidate_budget)?;
    let (tight, y) = solve_packing_dual(&reduced, b, &x, remaining)?;
    let witness = assemble_packing_witness(n, &free, zero_dual, &x, &tight, y);
    verify_packing_witness(a, b, &witness)?;
    Ok(witness)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(n))
    }
    fn rows(v: &[&[i64]]) -> BasicMatrix<BigRational> {
        matrix::from_rows(
            v.iter()
                .map(|r| r.iter().copied().map(q).collect())
                .collect(),
        )
        .unwrap()
    }
    #[test]
    fn convex_membership_replays_weights_and_kills_tampering() {
        let points = vec![
            vec![q(0), q(0)],
            vec![q(2), q(0)],
            vec![q(0), q(2)],
            vec![q(0), q(0)],
        ];
        let target = vec![q(1), q(1)];
        let w = convex_membership(&points, &target, 14).unwrap().unwrap();
        verify_convex_witness(&points, &target, &w).unwrap();
        let mut tampered = w.clone();
        tampered.weights[0] += q(1);
        assert!(verify_convex_witness(&points, &target, &tampered).is_err());
        assert_eq!(convex_membership(&points, &[q(2), q(2)], 14).unwrap(), None);
        assert!(convex_membership(&points, &target, 13).is_err());
        assert_eq!(convex_membership(&[], &[], 0).unwrap(), None);
        assert!(convex_membership(&[vec![]], &[], 1).unwrap().is_some());
    }
    #[test]
    fn active_sets_find_square_and_affine_line_vertices() {
        let e = matrix::zeros(0, 2).unwrap();
        let a = rows(&[&[1, 0], &[-1, 0], &[0, 1], &[0, -1]]);
        let b = vec![q(1), q(0), q(1), q(0)];
        assert_eq!(
            vertex_enumeration(&e, &[], &a, &b, 6).unwrap(),
            vec![
                vec![q(0), q(0)],
                vec![q(0), q(1)],
                vec![q(1), q(0)],
                vec![q(1), q(1)]
            ]
        );
        let e = rows(&[&[1, 1], &[2, 2]]);
        assert_eq!(
            vertex_enumeration(&e, &[q(1), q(2)], &a, &b, 4).unwrap(),
            vec![vec![q(0), q(1)], vec![q(1), q(0)]]
        );
        assert!(vertex_enumeration(&e, &[q(1), q(3)], &a, &b, 0)
            .unwrap()
            .is_empty());
    }
    #[test]
    fn unbounded_and_vertex_free_carriers_do_not_get_false_emptiness_claims() {
        let e = matrix::zeros(0, 2).unwrap();
        let a = rows(&[&[-1, 0], &[0, -1]]);
        assert_eq!(
            vertex_enumeration(&e, &[], &a, &[q(0), q(0)], 1).unwrap(),
            vec![vec![q(0), q(0)]]
        );
        let a = rows(&[&[-1, 0]]);
        assert!(vertex_enumeration(&e, &[], &a, &[q(0)], 0)
            .unwrap()
            .is_empty());
        assert!(vertex_enumeration(&e, &[], &a, &[], 10).is_err());
    }
    #[test]
    fn packing_optima_match_complete_small_grid_and_reject_corrupted_certificates() {
        let a = rows(&[&[1, 0], &[0, 1], &[1, 1]]);
        for bx in 0..=3 {
            for by in 0..=3 {
                for total in 0..=4 {
                    let b = vec![q(bx), q(by), q(total)];
                    let w = packing_optimum(&a, &b, 200).unwrap();
                    let grid = (0..=bx)
                        .flat_map(|x| (0..=by).map(move |y| (x, y)))
                        .filter(|(x, y)| x + y <= total)
                        .map(|(x, y)| q(x + y))
                        .max()
                        .unwrap();
                    assert_eq!(w.value, grid);
                    verify_packing_witness(&a, &b, &w).unwrap();
                    let mut bad = w.clone();
                    bad.primal[0] += q(10);
                    assert!(verify_packing_witness(&a, &b, &bad).is_err());
                    let mut bad = w.clone();
                    bad.dual.fill(q(0));
                    assert!(verify_packing_witness(&a, &b, &bad).is_err());
                }
            }
        }
        let b = vec![q(1), q(1), q(1)];
        assert!(packing_optimum(&a, &b, 0).is_err());
        assert!(matches!(
            packing_optimum(&rows(&[&[1, 0]]), &[q(1)], 10),
            Err(ConvexGeometryError::UnboundedPacking { column: 1 })
        ));
        assert!(matches!(
            packing_optimum(&rows(&[&[-1]]), &[q(1)], 10),
            Err(ConvexGeometryError::NegativePackingData)
        ));
        assert!(packing_optimum(&a, &[q(1)], 10).is_err());
        let a = rows(&[&[2, 0], &[0, 3]]);
        let w = packing_optimum(&a, &[q(0), q(0)], 1).unwrap();
        assert_eq!(w.value, q(0));
    }
}

/// Streaming reverse search for simple vertices of a rational H-polyhedron.
///
/// The caller supplies one feasible vertex. Its tight inequalities must be an
/// independent basis modulo the equality rows. Their sum defines a linear
/// objective uniquely maximized at that root. At every other vertex the first
/// improving edge is the parent. We traverse the inverse parent map without a
/// recursion stack, visited set, or list of all active sets (Avis-Fukuda reverse
/// search). Rays are skipped; they are not vertices. Duplicate/redundant tight
/// inequalities and non-simple vertices are explicitly refused. The existing
/// `vertex_enumeration` remains the general bounded active-set oracle.
///
/// Only `Ok(report)` means enumeration completed. Callback emissions before a
/// refusal are a partial stream, not an exhaustiveness certificate. Working
/// storage is polynomial in carrier size; caller-retained output is excluded.
/// Fuel is shared with all exact contractions and Bareiss solves.
pub use reverse_search::{reverse_search_vertices, ReverseSearchError, ReverseSearchReport};

mod reverse_search {
    use super::{BasicMatrix, BigRational, MAX_GEOMETRY_DIMENSION, MAX_GEOMETRY_ROWS};
    use linear_algebra::exact_field::rational_bareiss::{
        self as exact, RationalBudget, RationalError,
    };
    use num_traits::{One, Signed, Zero};

    #[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
    pub enum ReverseSearchError {
        #[error("incompatible carrier dimensions or size limit")]
        Shape,
        #[error("the supplied seed is infeasible")]
        InfeasibleSeed,
        #[error("tight inequalities are redundant or the vertex is not simple")]
        NonSimpleVertex,
        #[error("seed is not a vertex")]
        NotVertex,
        #[error("no improving parent edge exists at a non-root vertex")]
        InvalidParent,
        #[error(transparent)]
        Arithmetic(#[from] RationalError),
    }
    #[derive(Clone, Debug, PartialEq, Eq)]
    pub struct ReverseSearchReport {
        pub vertices: usize,
        pub edge_probes: usize,
        pub scalar_ops: usize,
    }
    #[derive(Clone)]
    struct Vertex {
        active: Vec<usize>,
        point: Vec<BigRational>,
    }
    struct Oracle<'a> {
        e: &'a BasicMatrix<BigRational>,
        erhs: &'a [BigRational],
        a: &'a BasicMatrix<BigRational>,
        bounds: &'a [BigRational],
        independent_equalities: Vec<usize>,
        objective: Vec<BigRational>,
        root: Vec<usize>,
        probes: usize,
    }
    impl Oracle<'_> {
        fn vertex(
            &self,
            point: Vec<BigRational>,
            fuel: &mut RationalBudget,
        ) -> Result<Vertex, ReverseSearchError> {
            if exact::multiply_vector(self.e, &point, fuel)? != self.erhs {
                return Err(ReverseSearchError::InfeasibleSeed);
            }
            let values = exact::multiply_vector(self.a, &point, fuel)?;
            if values.iter().zip(self.bounds).any(|(x, b)| x > b) {
                return Err(ReverseSearchError::InfeasibleSeed);
            }
            let active = values
                .iter()
                .zip(self.bounds)
                .enumerate()
                .filter(|(_, (x, b))| x == b)
                .map(|(i, _)| i)
                .collect::<Vec<_>>();
            let free = self.a.cols() - self.independent_equalities.len();
            if active.len() < free {
                return Err(ReverseSearchError::NotVertex);
            }
            if active.len() > free {
                return Err(ReverseSearchError::NonSimpleVertex);
            }
            Ok(Vertex { active, point })
        }
        fn basis(
            &self,
            v: &Vertex,
            fuel: &mut RationalBudget,
        ) -> Result<BasicMatrix<BigRational>, ReverseSearchError> {
            let d = self.a.cols();
            let n = fuel.elements(d, d)?;
            let mut data = Vec::new();
            data.try_reserve_exact(n)
                .map_err(|_| RationalError::Allocation)?;
            for &i in &self.independent_equalities {
                for c in 0..d {
                    data.push(self.e.get_ref(i, c).map_err(RationalError::from)?.clone());
                }
            }
            for &i in &v.active {
                for c in 0..d {
                    data.push(self.a.get_ref(i, c).map_err(RationalError::from)?.clone());
                }
            }
            Ok(BasicMatrix::from_row_major(d, d, data).map_err(RationalError::from)?)
        }
        fn min_positive_step(
            &self,
            rates: &[BigRational],
            values: &[BigRational],
            fuel: &mut RationalBudget,
        ) -> Result<Option<BigRational>, ReverseSearchError> {
            let mut step: Option<BigRational> = None;
            for (i, rate) in rates.iter().enumerate() {
                if rate.is_positive() {
                    let slack = fuel.sub(&self.bounds[i], &values[i])?;
                    let distance = fuel.div(&slack, rate)?;
                    if distance.is_negative() {
                        return Err(ReverseSearchError::InfeasibleSeed);
                    }
                    step = Some(step.map_or(distance.clone(), |x| x.min(distance)));
                }
            }
            Ok(step)
        }

        fn step_point(
            base: &[BigRational],
            direction: Vec<BigRational>,
            step: &BigRational,
            fuel: &mut RationalBudget,
        ) -> Result<Vec<BigRational>, ReverseSearchError> {
            let mut point = Vec::with_capacity(base.len());
            for (x, dx) in base.iter().zip(direction) {
                let change = fuel.mul(step, &dx)?;
                point.push(fuel.add(x, &change)?);
            }
            Ok(point)
        }

        fn solve_leaving_direction(
            &self,
            v: &Vertex,
            leaving: usize,
            fuel: &mut RationalBudget,
        ) -> Result<Vec<BigRational>, ReverseSearchError> {
            let basis = self.basis(v, fuel)?;
            let mut rhs = vec![BigRational::zero(); self.a.cols()];
            rhs[self.independent_equalities.len() + leaving] = -BigRational::one();
            let direction = exact::solve(&basis, &rhs, fuel)?;
            if direction.pivot_columns.len() != self.a.cols() {
                return Err(ReverseSearchError::NotVertex);
            }
            Ok(direction.particular)
        }

        fn neighbor(
            &mut self,
            v: &Vertex,
            leaving: usize,
            fuel: &mut RationalBudget,
        ) -> Result<Option<Vertex>, ReverseSearchError> {
            fuel.charge(1)?;
            self.probes = self
                .probes
                .checked_add(1)
                .ok_or(RationalError::FuelExhausted)?;
            let direction = self.solve_leaving_direction(v, leaving, fuel)?;
            let rates = exact::multiply_vector(self.a, &direction, fuel)?;
            let values = exact::multiply_vector(self.a, &v.point, fuel)?;
            let Some(step) = self.min_positive_step(&rates, &values, fuel)? else {
                return Ok(None); // an unbounded ray
            };
            let point = Self::step_point(&v.point, direction, &step, fuel)?;
            let next = self.vertex(point, fuel)?;
            if next.active == v.active {
                return Err(ReverseSearchError::InvalidParent);
            }
            Ok(Some(next))
        }
        fn parent(
            &mut self,
            v: &Vertex,
            fuel: &mut RationalBudget,
        ) -> Result<Option<Vertex>, ReverseSearchError> {
            if v.active == self.root {
                return Ok(None);
            }
            let current = exact::dot(&self.objective, &v.point, fuel)?;
            for leaving in 0..v.active.len() {
                if let Some(next) = self.neighbor(v, leaving, fuel)? {
                    if exact::dot(&self.objective, &next.point, fuel)? > current {
                        return Ok(Some(next));
                    }
                }
            }
            Err(ReverseSearchError::InvalidParent)
        }
    }

    fn check_reverse_search_shapes(
        e: &BasicMatrix<BigRational>,
        erhs: &[BigRational],
        a: &BasicMatrix<BigRational>,
        bounds: &[BigRational],
        seed: &[BigRational],
    ) -> Result<(), ReverseSearchError> {
        let d = a.cols();
        let shapes_match = [
            e.cols() == d,
            e.rows() == erhs.len(),
            a.rows() == bounds.len(),
            seed.len() == d,
            d <= MAX_GEOMETRY_DIMENSION,
            a.rows() <= MAX_GEOMETRY_ROWS,
            e.rows() <= MAX_GEOMETRY_ROWS,
        ]
        .into_iter()
        .all(|ok| ok);
        if !shapes_match {
            return Err(ReverseSearchError::Shape);
        }
        Ok(())
    }

    fn validate_reverse_search_inputs(
        e: &BasicMatrix<BigRational>,
        erhs: &[BigRational],
        a: &BasicMatrix<BigRational>,
        bounds: &[BigRational],
        seed: &[BigRational],
        fuel: &mut RationalBudget,
    ) -> Result<(), ReverseSearchError> {
        check_reverse_search_shapes(e, erhs, a, bounds, seed)?;
        let d = a.cols();
        for (rows, cols) in [(d, 1), (e.rows(), 1), (a.rows(), 1), (e.rows(), d), (a.rows(), d)] {
            fuel.elements(rows, cols)?;
        }
        for q in e
            .as_slice()
            .iter()
            .chain(erhs)
            .chain(a.as_slice())
            .chain(bounds)
            .chain(seed)
        {
            fuel.rational(q)?;
        }
        Ok(())
    }

    fn accumulate_root_objective(
        a: &BasicMatrix<BigRational>,
        active: &[usize],
        objective: &mut [BigRational],
        fuel: &mut RationalBudget,
    ) -> Result<(), ReverseSearchError> {
        let d = a.cols();
        for &i in active {
            for j in 0..d {
                let entry = a.get_ref(i, j).map_err(RationalError::from)?;
                objective[j] = fuel.add(&objective[j], entry)?;
            }
        }
        Ok(())
    }

    fn init_reverse_search<'a>(
        e: &'a BasicMatrix<BigRational>,
        erhs: &'a [BigRational],
        a: &'a BasicMatrix<BigRational>,
        bounds: &'a [BigRational],
        seed: &[BigRational],
        fuel: &mut RationalBudget,
    ) -> Result<(Oracle<'a>, Vertex), ReverseSearchError> {
        let d = a.cols();
        let transpose = e.try_transpose().map_err(RationalError::from)?;
        let independent_equalities =
            exact::solve(&transpose, &vec![BigRational::zero(); d], fuel)?.pivot_columns;
        let mut oracle = Oracle {
            e,
            erhs,
            a,
            bounds,
            independent_equalities,
            objective: vec![BigRational::zero(); d],
            root: vec![],
            probes: 0,
        };
        let v = oracle.vertex(seed.to_vec(), fuel)?;
        let basis = oracle.basis(&v, fuel)?;
        if exact::solve(&basis, &vec![BigRational::zero(); d], fuel)?
            .pivot_columns
            .len()
            != d
        {
            return Err(ReverseSearchError::NotVertex);
        }
        accumulate_root_objective(a, &v.active, &mut oracle.objective, fuel)?;
        oracle.root = v.active.clone();
        Ok((oracle, v))
    }

    fn try_advance_neighbor(
        oracle: &mut Oracle<'_>,
        v: &mut Vertex,
        next_edge: &mut usize,
        vertices: &mut usize,
        fuel: &mut RationalBudget,
        emit: &mut impl FnMut(&[BigRational]),
    ) -> Result<(), ReverseSearchError> {
        let neighbor = oracle.neighbor(v, *next_edge, fuel)?;
        *next_edge += 1;
        if let Some(child) = neighbor {
            if oracle
                .parent(&child, fuel)?
                .is_some_and(|parent| parent.active == v.active)
            {
                *v = child;
                *next_edge = 0;
                *vertices = vertices
                    .checked_add(1)
                    .ok_or(RationalError::FuelExhausted)?;
                emit(&v.point);
            }
        }
        Ok(())
    }

    pub fn reverse_search_vertices(
        e: &BasicMatrix<BigRational>,
        erhs: &[BigRational],
        a: &BasicMatrix<BigRational>,
        bounds: &[BigRational],
        seed: &[BigRational],
        fuel: &mut RationalBudget,
        mut emit: impl FnMut(&[BigRational]),
    ) -> Result<ReverseSearchReport, ReverseSearchError> {
        let start = fuel.used();
        validate_reverse_search_inputs(e, erhs, a, bounds, seed, fuel)?;
        let (mut oracle, mut v) = init_reverse_search(e, erhs, a, bounds, seed, fuel)?;
        let mut vertices = 1usize;
        let mut next_edge = 0;
        emit(&v.point);
        loop {
            fuel.charge(1)?;
            if next_edge < v.active.len() {
                try_advance_neighbor(&mut oracle, &mut v, &mut next_edge, &mut vertices, fuel, &mut emit)?;
            } else {
                let Some(parent) = oracle.parent(&v, fuel)? else {
                    break;
                };
                let leaving = parent
                    .active
                    .iter()
                    .position(|i| v.active.binary_search(i).is_err())
                    .ok_or(ReverseSearchError::InvalidParent)?;
                v = parent;
                next_edge = leaving + 1;
            }
        }
        Ok(ReverseSearchReport {
            vertices,
            edge_probes: oracle.probes,
            scalar_ops: fuel.used() - start,
        })
    }
}
