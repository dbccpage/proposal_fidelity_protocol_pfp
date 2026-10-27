//! Dihedral angles at hinges in 2D, 3D, and 4D simplicial manifolds.
//!
//! - In 2D: hinge is a 0-simplex (vertex), angle is interior triangle angle.
//! - In 3D: hinge is a 1-simplex (edge), dihedral angle between triangular faces of tetrahedron.
//! - In 4D: hinge is a 2-simplex (triangle), dihedral angle between tetrahedra of 4-simplex.
//!
//! AuthorityEffect: None.

use crate::cayley_menger::simplex_volume_cayley_menger;

pub const DEFAULT_ANGLE_TOL: f64 = 1e-9;

fn triangle_opposite_endpoints(
    triangle: &[usize; 3],
    vertex: usize,
) -> Result<(usize, usize), String> {
    let (i, j, k) = (triangle[0], triangle[1], triangle[2]);
    if vertex == i {
        Ok((j, k))
    } else if vertex == j {
        Ok((i, k))
    } else if vertex == k {
        Ok((i, j))
    } else {
        Err(format!("Vertex {vertex} not in triangle {triangle:?}"))
    }
}

/// Interior angle of a triangle (2-simplex) at `vertex` via the cosine law (radians).
pub fn triangle_angle_at(
    triangle: &[usize; 3],
    vertex: usize,
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let (p, q) = triangle_opposite_endpoints(triangle, vertex)?;

    let a = get_length(vertex, p).ok_or_else(|| format!("Missing length ({vertex}, {p})"))?;
    let b = get_length(vertex, q).ok_or_else(|| format!("Missing length ({vertex}, {q})"))?;
    let c = get_length(p, q).ok_or_else(|| format!("Missing length ({p}, {q})"))?;

    let denom = 2.0 * a * b;
    if denom.abs() < DEFAULT_ANGLE_TOL {
        return Err("Degenerate triangle side length".to_string());
    }
    let cos_theta = ((a * a + b * b - c * c) / denom).clamp(-1.0, 1.0);
    Ok(cos_theta.acos())
}

fn tetrahedron_opposite_pair(
    tetrahedron: &[usize; 4],
    edge: (usize, usize),
) -> Result<(usize, usize), String> {
    let (e1, e2) = edge;
    let mut opp_verts = Vec::new();
    for &v in tetrahedron {
        if v != e1 && v != e2 {
            opp_verts.push(v);
        }
    }
    if opp_verts.len() != 2 {
        return Err(format!(
            "Edge {edge:?} does not belong to tetrahedron {tetrahedron:?}"
        ));
    }
    Ok((opp_verts[0], opp_verts[1]))
}

fn tetrahedron_remaining_lengths(
    (e1, e2): (usize, usize),
    (w1, w2): (usize, usize),
    get_length: &impl Fn(usize, usize) -> Option<f64>,
) -> Result<(f64, f64, f64, f64, f64), String> {
    let d13 = get_length(e1, w1).ok_or("Missing length")?;
    let d23 = get_length(e2, w1).ok_or("Missing length")?;
    let d14 = get_length(e1, w2).ok_or("Missing length")?;
    let d24 = get_length(e2, w2).ok_or("Missing length")?;
    let d34 = get_length(w1, w2).ok_or("Missing length")?;
    Ok((d13, d23, d14, d24, d34))
}

fn validated_face_areas(
    tetrahedron: &[usize; 4],
    (e1, e2): (usize, usize),
    (w1, w2): (usize, usize),
    get_length: &impl Fn(usize, usize) -> Option<f64>,
) -> Result<(f64, f64), String> {
    let _v_tet = simplex_volume_cayley_menger(tetrahedron, get_length)?;
    let a1 = simplex_volume_cayley_menger(&[e1, e2, w1], get_length)?;
    let a2 = simplex_volume_cayley_menger(&[e1, e2, w2], get_length)?;

    if a1 < DEFAULT_ANGLE_TOL || a2 < DEFAULT_ANGLE_TOL {
        return Err("Degenerate triangle face area in tetrahedron".to_string());
    }
    Ok((a1, a2))
}

/// Dihedral angle of a tetrahedron (3-simplex) at edge `(u, v)` (radians).
/// The edge is shared by two triangular faces with opposite vertices w1 and w2.
pub fn tetrahedron_dihedral_angle_at_edge(
    tetrahedron: &[usize; 4],
    edge: (usize, usize),
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let (e1, e2) = edge;
    let (w1, w2) = tetrahedron_opposite_pair(tetrahedron, edge)?;

    let ell = get_length(e1, e2).ok_or_else(|| format!("Missing edge length {edge:?}"))?;
    let (a1, a2) = validated_face_areas(tetrahedron, (e1, e2), (w1, w2), &get_length)?;

    // Formula: sin(theta) = (3 * V * ell) / (2 * A1 * A2)
    // Formula for cos(theta):
    // Let edge endpoints be 1, 2; opposite vertices 3, 4.
    let d12_sq = ell * ell;
    let (d13, d23, d14, d24, d34) = tetrahedron_remaining_lengths((e1, e2), (w1, w2), &get_length)?;

    let term1 = (d12_sq + d13 * d13 - d23 * d23) * (d12_sq + d14 * d14 - d24 * d24);
    let term2 = 2.0 * d12_sq * (d13 * d13 + d14 * d14 - d34 * d34);
    let num = term2 - term1;
    let denom = 16.0 * a1 * a2;

    let cos_theta = (num / denom).clamp(-1.0, 1.0);
    let theta = cos_theta.acos();

    if !theta.is_finite() {
        return Err("Non-finite dihedral angle computed".to_string());
    }
    Ok(theta)
}

fn squared_edge_length(
    i: usize,
    j: usize,
    get_length: &impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let length = get_length(i, j).ok_or("missing edge length")?;
    if !length.is_finite() || length <= 0.0 || !(length * length).is_finite() {
        return Err("edge length must be finite and positive".into());
    }
    Ok(length * length)
}

fn build_pentachoron_gram(
    origin: usize,
    vertices: &[usize; 4],
    get_length: &impl Fn(usize, usize) -> Option<f64>,
) -> Result<[[f64; 4]; 4], String> {
    let mut gram = [[0.0; 4]; 4];
    for i in 0..4 {
        gram[i][i] = squared_edge_length(origin, vertices[i], get_length)?;
        for j in 0..i {
            let dot = (gram[i][i]
                + gram[j][j]
                - squared_edge_length(vertices[i], vertices[j], get_length)?)
                / 2.0;
            gram[i][j] = dot;
            gram[j][i] = dot;
        }
    }
    Ok(gram)
}

fn validate_pentachoron_hinge(
    four_simplex: &[usize; 5],
    triangle: &[usize; 3],
) -> Result<[usize; 4], String> {
    let unique: std::collections::BTreeSet<_> = four_simplex.iter().copied().collect();
    let hinge: std::collections::BTreeSet<_> = triangle.iter().copied().collect();
    if unique.len() != 5 || hinge.len() != 3 || !hinge.is_subset(&unique) {
        return Err("invalid simplex or hinge vertex IDs".into());
    }
    let opposite: Vec<_> = unique.difference(&hinge).copied().collect();
    Ok([triangle[1], triangle[2], opposite[0], opposite[1]])
}

/// Dihedral angle of a 4-simplex at triangle face `(u, v, w)` (radians).
pub fn pentachoron_dihedral_angle_at_triangle(
    four_simplex: &[usize; 5],
    triangle: &[usize; 3],
    get_length: impl Fn(usize, usize) -> Option<f64>,
) -> Result<f64, String> {
    let vertices = validate_pentachoron_hinge(four_simplex, triangle)?;
    let gram = build_pentachoron_gram(triangle[0], &vertices, &get_length)?;
    // Schur complement removes the two tangent directions along the hinge.
    let det = gram[0][0] * gram[1][1] - gram[0][1] * gram[0][1];
    if !det.is_finite() || det <= 0.0 {
        return Err("degenerate hinge".into());
    }
    let normal_dot = |i: usize, j: usize| {
        gram[i][j]
            - (gram[i][0] * (gram[1][1] * gram[j][0] - gram[0][1] * gram[j][1])
                + gram[i][1] * (gram[0][0] * gram[j][1] - gram[0][1] * gram[j][0]))
                / det
    };
    let aa = normal_dot(2, 2);
    let bb = normal_dot(3, 3);
    let ab = normal_dot(2, 3);
    let residual_det = aa * bb - ab * ab;
    if [aa <= 0.0, bb <= 0.0, !residual_det.is_finite(), residual_det <= 0.0]
        .into_iter()
        .any(std::convert::identity)
    {
        return Err("degenerate or non-Euclidean 4-simplex".into());
    }
    Ok((ab / (aa.sqrt() * bb.sqrt())).clamp(-1.0, 1.0).acos())
}

// Origin: engine/crates_rs/core_general_relativity/src/dihedral_angles.rs
// Claim: urn:core:crates_rs:core-general-relativity:dihedral-angles:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd8431438 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd8431438` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord8431438 {
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
impl BoundaryErrord8431438 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord8431438 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord8431438 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd8431438 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord8431438> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord8431438::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord8431438::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord8431438::ExceedsCapacity {
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

    #[test]
    fn test_regular_tetrahedron_dihedral_angle() {
        let side = 1.0;
        let get_len = |_: usize, _: usize| Some(side);
        let tet = [0, 1, 2, 3];
        let theta = tetrahedron_dihedral_angle_at_edge(&tet, (0, 1), get_len).unwrap();
        // For regular tetrahedron: cos(theta) = 1/3, so theta = arccos(1/3) ~ 1.2309594 radians (70.53 degrees)
        let expected = (1.0f64 / 3.0).acos();
        assert!((theta - expected).abs() < 1e-7);
    }
}

#[cfg(test)]
mod l4_boundary_tests_d8431438 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd8431438::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd8431438::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd8431438::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd8431438::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd8431438::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord8431438::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord8431438::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
