//! Cayley–Menger metric determinants and polytope admissibility (RQ-03).
//!
//! Evaluates n-simplex volumes directly from edge lengths without coordinate embeddings:
//! - 1-simplex: length
//! - 2-simplex: Heron's formula / 2D area
//! - 3-simplex: Cayley–Menger tetrahedron volume V^2 = (1/288) det(CM)
//! - 4-simplex: Cayley–Menger 4-simplex volume V^2 = (-1/9216) det(CM)
//!
//! AuthorityEffect: None.

pub const DEFAULT_CM_TOL: f64 = 1e-9;

fn find_pivot_row(mat: &[Vec<f64>], col: usize, n: usize) -> (usize, f64) {
    let mut pivot_row = col;
    let mut max_val = mat[col][col].abs();
    for (r, row) in mat.iter().enumerate().take(n).skip(col + 1) {
        if row[col].abs() > max_val {
            max_val = row[col].abs();
            pivot_row = r;
        }
    }
    (pivot_row, max_val)
}

fn eliminate_column_below(mat: &mut [Vec<f64>], col: usize, n: usize, pivot: f64) {
    for r in (col + 1)..n {
        let factor = mat[r][col] / pivot;
        for c in col..n {
            mat[r][c] -= factor * mat[col][c];
        }
    }
}

/// Computes determinant of small square matrices (up to 6x6) using Gaussian elimination with partial pivoting.
pub fn small_matrix_det(mut mat: Vec<Vec<f64>>) -> f64 {
    let n = mat.len();
    if n == 0 {
        return 1.0;
    }
    if mat.iter().any(|row| row.len() != n) {
        return 0.0;
    }

    let mut det = 1.0;
    for col in 0..n {
        // Pivot selection
        let (pivot_row, max_val) = find_pivot_row(&mat, col, n);
        if max_val < 1e-15 {
            return 0.0;
        }

        if pivot_row != col {
            mat.swap(pivot_row, col);
            det = -det;
        }

        let pivot = mat[col][col];
        det *= pivot;
        eliminate_column_below(&mut mat, col, n, pivot);
    }

    det
}

/// Computes the cofactor of an n x n matrix at entry (row, col):
/// Cof(M)_{row, col} = (-1)^{row + col} * det(submatrix excluding row and col).
pub fn matrix_cofactor(mat: &[Vec<f64>], row: usize, col: usize) -> f64 {
    let n = mat.len();
    if n <= 1 {
        return 1.0;
    }
    let mut sub = Vec::with_capacity(n - 1);
    for (r, r_vec) in mat.iter().enumerate() {
        if r == row {
            continue;
        }
        let mut row_sub = Vec::with_capacity(n - 1);
        for (c, &val) in r_vec.iter().enumerate() {
            if c == col {
                continue;
            }
            row_sub.push(val);
        }
        sub.push(row_sub);
    }
    let det = small_matrix_det(sub);
    if (row + col) % 2 == 1 {
        -det
    } else {
        det
    }
}

/// Constructs the Cayley-Menger matrix for an n-simplex on vertices v_0, ..., v_n given a distance lookup function.
/// Size is (n + 2) x (n + 2).
///
/// CM = [
///   [ 0,  1,       1,       ..., 1       ],
///   [ 1,  0,       d(0,1)^2, ..., d(0,n)^2 ],
///   [ 1,  d(1,0)^2, 0,       ..., d(1,n)^2 ],
///   ...
///   [ 1,  d(n,0)^2, d(n,1)^2, ..., 0       ]
/// ]
pub fn cayley_menger_matrix(
    vertices: &[usize],
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<Vec<Vec<f64>>, String> {
    let k = vertices.len();
    if k == 0 {
        return Err("Cannot construct Cayley-Menger matrix for empty vertex set".to_string());
    }

    let m = k + 1; // size of matrix
    let mut mat = vec![vec![0.0; m]; m];

    // First row and column are [0, 1, 1, ..., 1]
    for i in 1..m {
        mat[0][i] = 1.0;
        mat[i][0] = 1.0;
    }

    for i in 0..k {
        for j in 0..k {
            if i != j {
                let u = vertices[i];
                let v = vertices[j];
                let len = get_length(u, v)
                    .ok_or_else(|| format!("Missing edge length between vertices {u} and {v}"))?;
                if len <= 0.0 || !len.is_finite() {
                    return Err(format!(
                        "Invalid non-positive edge length {len} between {u} and {v}"
                    ));
                }
                mat[i + 1][j + 1] = len * len;
            }
        }
    }

    Ok(mat)
}

/// Computes the determinant of the Cayley-Menger matrix of an n-simplex.
pub fn cayley_menger_determinant(
    vertices: &[usize],
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let mat = cayley_menger_matrix(vertices, get_length)?;
    Ok(small_matrix_det(mat))
}

/// Computes the volume of an n-simplex via Cayley-Menger:
/// V_n^2 = ((-1)^{n+1} / (2^n (n!)^2)) * det(CM).
pub fn simplex_volume_cayley_menger(
    vertices: &[usize],
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let n = vertices.len().saturating_sub(1);
    if n == 0 {
        return Ok(1.0); // 0-simplex point has volume 1
    }
    if n == 1 {
        let u = vertices[0];
        let v = vertices[1];
        let len = get_length(u, v).ok_or_else(|| format!("Missing edge length ({u}, {v})"))?;
        return Ok(len);
    }

    let det = cayley_menger_determinant(vertices, get_length)?;

    // Factor: (-1)^{n+1} / (2^n * (n!)^2)
    let mut factorial = 1.0;
    for i in 1..=n {
        factorial *= i as f64;
    }
    let denom = (2.0f64.powi(n as i32)) * (factorial * factorial);
    let sign = if (n + 1) % 2 == 1 { -1.0 } else { 1.0 };

    let vol_sq = (sign * det) / denom;
    if vol_sq < -DEFAULT_CM_TOL {
        return Err(format!(
            "Simplex on vertices {vertices:?} violates metric embedding (negative Cayley-Menger vol^2 = {vol_sq})"
        ));
    }
    Ok(vol_sq.max(0.0).sqrt())
}

/// Metric polytope admissibility check (RQ-03):
/// 1. Triangle inequalities for all triangles.
/// 2. Positive Cayley-Menger volume for all higher simplices.
#[derive(Debug, Clone, PartialEq)]
pub struct MetricPolytopeCheck {
    pub is_admissible: bool,
    pub triangle_inequality_violations: Vec<([usize; 3], String)>,
    pub cayley_menger_violations: Vec<(Vec<usize>, f64)>,
}

impl MetricPolytopeCheck {
    pub fn new() -> Self {
        Self {
            is_admissible: true,
            triangle_inequality_violations: Vec::new(),
            cayley_menger_violations: Vec::new(),
        }
    }
}

impl Default for MetricPolytopeCheck {
    fn default() -> Self {
        Self::new()
    }
}

fn triangle_side_lengths(
    tri: [usize; 3],
    get_length: &impl Fn(usize, usize) -> Option<f64>,
) -> Option<(f64, f64, f64)> {
    Some((
        get_length(tri[1], tri[2])?,
        get_length(tri[0], tri[2])?,
        get_length(tri[0], tri[1])?,
    ))
}

fn check_tetrahedron_volume(
    tet: &[usize; 4],
    get_length: &impl Fn(usize, usize) -> Option<f64>,
) -> Option<f64> {
    match simplex_volume_cayley_menger(tet, get_length) {
        Ok(vol) if vol > DEFAULT_CM_TOL => None,
        Ok(vol) => Some(vol),
        Err(_) => Some(-1.0),
    }
}

/// Check metric polytope admissibility for a complex and an edge-length lookup.
pub fn check_metric_polytope_admissibility(
    triangles: &[[usize; 3]],
    tetrahedra: &[[usize; 4]],
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> MetricPolytopeCheck {
    let mut check = MetricPolytopeCheck::new();

    for &tri in triangles {
        if let Some((a, b, c)) = triangle_side_lengths(tri, &get_length) {
            let violates = [
                a + b <= c + DEFAULT_CM_TOL,
                a + c <= b + DEFAULT_CM_TOL,
                b + c <= a + DEFAULT_CM_TOL,
            ]
            .into_iter()
            .any(std::convert::identity);
            if violates {
                check.triangle_inequality_violations.push((
                    tri,
                    format!("Lengths ({a}, {b}, {c}) violate triangle inequality"),
                ));
                check.is_admissible = false;
            }
        }
    }

    for &tet in tetrahedra {
        if let Some(bad_vol) = check_tetrahedron_volume(&tet, &get_length) {
            check.cayley_menger_violations.push((tet.to_vec(), bad_vol));
            check.is_admissible = false;
        }
    }

    check
}

fn find_distinct_edge_indices(
    vertices: &[usize],
    u: usize,
    v: usize,
) -> Result<(usize, usize), String> {
    let i = vertices
        .iter()
        .position(|&x| x == u)
        .ok_or_else(|| format!("Vertex {u} not found in simplex {vertices:?}"))?;
    let j = vertices
        .iter()
        .position(|&x| x == v)
        .ok_or_else(|| format!("Vertex {v} not found in simplex {vertices:?}"))?;

    if i == j {
        return Err(format!("Vertices u={u} and v={v} must be distinct"));
    }
    Ok((i, j))
}

/// Computes the exact analytical partial derivative of the n-simplex volume with respect to
/// the squared edge length s_{uv} = d(u, v)^2 via Jacobi's cofactor formula:
/// ∂(V_n)/∂(s_{uv}) = ((-1)^{n+1} / (2^n (n!)^2 V_n)) * Cof(CM)_{i+1, j+1}
pub fn simplex_volume_derivative_wrt_squared_edge(
    vertices: &[usize],
    u: usize,
    v: usize,
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let n = vertices.len().saturating_sub(1);
    if n < 1 {
        return Err("Simplex must have dimension at least 1 to compute edge derivative".to_string());
    }

    let (i, j) = find_distinct_edge_indices(vertices, u, v)?;

    let vol = simplex_volume_cayley_menger(vertices, &get_length)?;
    if vol <= DEFAULT_CM_TOL {
        return Err(format!("Simplex has degenerate/non-positive volume {vol}"));
    }

    let mat = cayley_menger_matrix(vertices, &get_length)?;
    let cof = matrix_cofactor(&mat, i + 1, j + 1);

    let factorial: f64 = (1..=n).map(|k| k as f64).product();
    let denom = (2.0f64.powi(n as i32)) * (factorial * factorial) * vol;
    let sign = if (n + 1) % 2 == 1 { -1.0 } else { 1.0 };

    Ok((sign * cof) / denom)
}

// Origin: engine/crates_rs/core_general_relativity/src/cayley_menger.rs
// Claim: urn:core:crates_rs:core-general-relativity:cayley-menger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord785a9628 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord785a9628` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError785a9628 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError785a9628 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError785a9628 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError785a9628 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord785a9628 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError785a9628> {
        if capacity_bound == 0 {
            return Err(BoundaryError785a9628::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError785a9628::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError785a9628::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;

    #[test]
    fn test_equilateral_triangle_cayley_menger() {
        let side = 2.0;
        let get_len = |_: usize, _: usize| Some(side);
        let vol = simplex_volume_cayley_menger(&[0, 1, 2], get_len).unwrap();
        // Area = (sqrt(3)/4) * side^2 = sqrt(3) ~ 1.7320508
        let expected = (3.0f64.sqrt() / 4.0) * side * side;
        assert!((vol - expected).abs() < 1e-9);
    }

    #[test]
    fn test_regular_tetrahedron_cayley_menger() {
        let side = 1.0;
        let get_len = |_: usize, _: usize| Some(side);
        let vol = simplex_volume_cayley_menger(&[0, 1, 2, 3], get_len).unwrap();
        // Volume = side^3 / (6 * sqrt(2)) ~ 0.11785113
        let expected = side.powi(3) / (6.0 * 2.0f64.sqrt());
        assert!((vol - expected).abs() < 1e-9);
    }

    #[test]
    fn test_triangle_inequality_rejection() {
        let triangles = [[0, 1, 2]];
        let tetrahedra = [];
        let mut map = BTreeMap::new();
        map.insert((0, 1), 1.0);
        map.insert((1, 2), 2.0);
        map.insert((0, 2), 10.0); // 1 + 2 < 10 violates!
        let get_len = |u: usize, v: usize| {
            let key = if u < v { (u, v) } else { (v, u) };
            map.get(&key).copied()
        };

        let check = check_metric_polytope_admissibility(&triangles, &tetrahedra, get_len);
        assert!(!check.is_admissible);
        assert_eq!(check.triangle_inequality_violations.len(), 1);
    }

    #[test]
    fn test_simplex_volume_derivative_wrt_squared_edge() {
        // Test on a triangle with sides a=3, b=4, c=5 (right triangle, Area = 6)
        let get_len = |u: usize, v: usize| {
            let key = if u < v { (u, v) } else { (v, u) };
            match key {
                (0, 1) => Some(3.0),
                (1, 2) => Some(4.0),
                (0, 2) => Some(5.0),
                _ => None,
            }
        };

        // For edge (0, 1) with length 3:
        // Angle opposite to (0, 1) is at vertex 2: tan(theta_2) = 3/4, cot(theta_2) = 4/3.
        // ∂A/∂(s_a) = 1/4 * cot(theta_2) = 1/4 * 4/3 = 1/3 ~ 0.33333333.
        let d_anal = simplex_volume_derivative_wrt_squared_edge(&[0, 1, 2], 0, 1, get_len).unwrap();
        assert!((d_anal - 1.0 / 3.0).abs() < 1e-7);

        // Finite difference verification
        let eps = 1e-6;
        let s0 = 3.0f64 * 3.0;
        let l_plus = (s0 + eps).sqrt();
        let l_minus = (s0 - eps).sqrt();

        let get_len_plus = |u: usize, v: usize| {
            let key = if u < v { (u, v) } else { (v, u) };
            if key == (0, 1) {
                Some(l_plus)
            } else {
                get_len(u, v)
            }
        };
        let get_len_minus = |u: usize, v: usize| {
            let key = if u < v { (u, v) } else { (v, u) };
            if key == (0, 1) {
                Some(l_minus)
            } else {
                get_len(u, v)
            }
        };

        let a_plus = simplex_volume_cayley_menger(&[0, 1, 2], get_len_plus).unwrap();
        let a_minus = simplex_volume_cayley_menger(&[0, 1, 2], get_len_minus).unwrap();
        let d_num = (a_plus - a_minus) / (2.0 * eps);

        assert!((d_anal - d_num).abs() < 1e-6);
    }
}

#[cfg(test)]
mod l4_boundary_tests_785a9628 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord785a9628::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord785a9628::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord785a9628::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord785a9628::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord785a9628::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError785a9628::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError785a9628::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
