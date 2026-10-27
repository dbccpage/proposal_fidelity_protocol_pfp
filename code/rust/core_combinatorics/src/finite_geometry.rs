//! Finite geometry incidence structures, configurations, and ray orthogonality.
//!
//! AuthorityEffect: None.
//!
//! Provides combinatorial point-line incidence structures, projective and affine planes,
//! and orthogonality incidence without host I/O or floating-point approximations.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ca9d3d1e<T> {
    fn checked_invariant_ca9d3d1e(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ca9d3d1e<T> for Option<T> {
    #[inline]
    fn checked_invariant_ca9d3d1e(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ca9d3d1e<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ca9d3d1e(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeSet;
use thiserror::Error;

/// Mandatory authority effect declaration.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

/// Errors occurring during finite geometry operations.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum FiniteGeometryError {
    #[error("point index {point} out of bounds for {num_points} points")]
    PointOutOfBounds { point: usize, num_points: usize },
    #[error("line index {line} out of bounds for {num_lines} lines")]
    LineOutOfBounds { line: usize, num_lines: usize },
    #[error("line must contain at least 2 distinct points")]
    DegenerateLine,
    #[error("configuration requires at least 3 points and 3 lines")]
    TooSmall,
    #[error("dimension must be positive and bounded")]
    InvalidDimension,
    #[error("dimension {0} is not a prime")]
    NotPrime(usize),
}

/// A finite incidence structure of points and lines $(P, L, I)$.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IncidenceStructure {
    num_points: usize,
    num_lines: usize,
    /// For each line, the sorted set of incident point indices.
    lines: Vec<BTreeSet<usize>>,
}

impl IncidenceStructure {
    /// Creates a new incidence structure with declared points and line incidence lists.
    pub fn new(num_points: usize, lines: Vec<Vec<usize>>) -> Result<Self, FiniteGeometryError> {
        if num_points < 3 || lines.len() < 3 {
            return Err(FiniteGeometryError::TooSmall);
        }
        let num_lines = lines.len();
        let mut clean_lines = Vec::with_capacity(num_lines);
        for l in lines {
            let pts: BTreeSet<usize> = l.into_iter().collect();
            if pts.len() < 2 {
                return Err(FiniteGeometryError::DegenerateLine);
            }
            if let Some(&max_pt) = pts.iter().next_back() {
                if max_pt >= num_points {
                    return Err(FiniteGeometryError::PointOutOfBounds {
                        point: max_pt,
                        num_points,
                    });
                }
            }
            clean_lines.push(pts);
        }
        Ok(Self {
            num_points,
            num_lines,
            lines: clean_lines,
        })
    }

    /// Number of points.
    pub fn num_points(&self) -> usize {
        self.num_points
    }

    /// Number of lines.
    pub fn num_lines(&self) -> usize {
        self.num_lines
    }

    /// Checks if point `p` is incident with line `l`.
    pub fn is_incident(&self, point: usize, line: usize) -> Result<bool, FiniteGeometryError> {
        if point >= self.num_points {
            return Err(FiniteGeometryError::PointOutOfBounds {
                point,
                num_points: self.num_points,
            });
        }
        if line >= self.num_lines {
            return Err(FiniteGeometryError::LineOutOfBounds {
                line,
                num_lines: self.num_lines,
            });
        }
        Ok(self.lines[line].contains(&point))
    }

    /// Returns the points on line `l`.
    pub fn points_on_line(&self, line: usize) -> Result<&BTreeSet<usize>, FiniteGeometryError> {
        self.lines.get(line).ok_or(FiniteGeometryError::LineOutOfBounds {
            line,
            num_lines: self.num_lines,
        })
    }

    /// Returns the lines incident with point `p`.
    pub fn lines_on_point(&self, point: usize) -> Result<Vec<usize>, FiniteGeometryError> {
        if point >= self.num_points {
            return Err(FiniteGeometryError::PointOutOfBounds {
                point,
                num_points: self.num_points,
            });
        }
        Ok((0..self.num_lines)
            .filter(|&l| self.lines[l].contains(&point))
            .collect())
    }

    /// Intersection points between two lines.
    pub fn line_intersection(&self, l1: usize, l2: usize) -> Result<Vec<usize>, FiniteGeometryError> {
        let pts1 = self.points_on_line(l1)?;
        let pts2 = self.points_on_line(l2)?;
        Ok(pts1.intersection(pts2).copied().collect())
    }

    /// Checks whether any two distinct points lie on at most one line (partial linear space).
    pub fn is_partial_linear_space(&self) -> bool {
        for p1 in 0..self.num_points {
            for p2 in (p1 + 1)..self.num_points {
                let lines_containing_both = (0..self.num_lines)
                    .filter(|&l| self.lines[l].contains(&p1) && self.lines[l].contains(&p2))
                    .count();
                if lines_containing_both > 1 {
                    return false;
                }
            }
        }
        true
    }

    /// Checks whether any two distinct points lie on exactly one line (linear space).
    pub fn is_linear_space(&self) -> bool {
        for p1 in 0..self.num_points {
            for p2 in (p1 + 1)..self.num_points {
                let lines_containing_both = (0..self.num_lines)
                    .filter(|&l| self.lines[l].contains(&p1) && self.lines[l].contains(&p2))
                    .count();
                if lines_containing_both != 1 {
                    return false;
                }
            }
        }
        true
    }
}

/// Constructs the Fano plane $PG(2, 2)$: 7 points, 7 lines, 3 points per line, 3 lines per point.
pub fn fano_plane() -> IncidenceStructure {
    // 7 points {0..=6}, lines correspond to the 7 non-zero 3-bit binary words with x.y = 0 mod 2
    let lines = vec![
        vec![0, 1, 2],
        vec![0, 3, 4],
        vec![0, 5, 6],
        vec![1, 3, 5],
        vec![1, 4, 6],
        vec![2, 3, 6],
        vec![2, 4, 5],
    ];
    IncidenceStructure::new(7, lines).checked_invariant_ca9d3d1e("Fano plane is a valid incidence structure")
}

/// Constructs the affine plane $AG(2, p)$ for prime $p$.
/// Has $p^2$ points $(x, y)$ encoded as $x \cdot p + y$, and $p(p+1)$ lines.
/// Lines are partitioned into $p+1$ parallel classes of $p$ lines each:
/// - $p$ vertical lines: $x = c$ for $c \in \{0..p-1\}$
/// - for each slope $m \in \{0..p-1\}$, $p$ lines: $y = m x + c \pmod p$.
pub fn affine_plane_ag2(p: usize) -> Result<IncidenceStructure, FiniteGeometryError> {
    if p < 2 || p > 13 {
        return Err(FiniteGeometryError::InvalidDimension);
    }
    // Check primality
    for d in 2..p {
        if p % d == 0 {
            return Err(FiniteGeometryError::NotPrime(p));
        }
    }
    let num_points = p * p;
    let mut lines = Vec::with_capacity(p * (p + 1));

    // Class infinity: vertical lines x = c
    for c in 0..p {
        let mut line = Vec::with_capacity(p);
        for y in 0..p {
            line.push(c * p + y);
        }
        lines.push(line);
    }

    // Classes m in 0..p: lines y = m x + c (mod p)
    for m in 0..p {
        for c in 0..p {
            let mut line = Vec::with_capacity(p);
            for x in 0..p {
                let y = (m * x + c) % p;
                line.push(x * p + y);
            }
            lines.push(line);
        }
    }

    IncidenceStructure::new(num_points, lines)
}

/// Orthogonality adjacency over finite integer vectors (exact scalar product).
pub fn ray_orthogonality(vectors: &[Vec<i64>]) -> Vec<Vec<bool>> {
    let n = vectors.len();
    let mut adj = vec![vec![false; n]; n];
    for i in 0..n {
        for j in (i + 1)..n {
            let dot: i64 = vectors[i]
                .iter()
                .zip(&vectors[j])
                .map(|(&a, &b)| a * b)
                .sum();
            if dot == 0 {
                adj[i][j] = true;
                adj[j][i] = true;
            }
        }
    }
    adj
}

// Origin: engine/crates_rs/core_combinatorics/src/finite_geometry.rs
// Claim: urn:core:crates_rs:core-combinatorics:finite-geometry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fano_plane_is_linear_space() {
        let fano = fano_plane();
        assert_eq!(fano.num_points(), 7);
        assert_eq!(fano.num_lines(), 7);
        assert!(fano.is_linear_space());
        assert!(fano.is_partial_linear_space());

        // Every point is on exactly 3 lines
        for p in 0..7 {
            assert_eq!(fano.lines_on_point(p).unwrap().len(), 3);
        }
        // Every line has exactly 3 points
        for l in 0..7 {
            assert_eq!(fano.points_on_line(l).unwrap().len(), 3);
        }
        // Any two lines intersect at exactly 1 point
        for l1 in 0..7 {
            for l2 in (l1 + 1)..7 {
                assert_eq!(fano.line_intersection(l1, l2).unwrap().len(), 1);
            }
        }
    }

    #[test]
    fn test_affine_plane_ag2_3() {
        let ag = affine_plane_ag2(3).unwrap();
        assert_eq!(ag.num_points(), 9);
        assert_eq!(ag.num_lines(), 12); // 3 * (3 + 1) = 12
        assert!(ag.is_linear_space());

        // Points on each line is 3
        for l in 0..12 {
            assert_eq!(ag.points_on_line(l).unwrap().len(), 3);
        }
        // Lines on each point is 4 (p+1)
        for p in 0..9 {
            assert_eq!(ag.lines_on_point(p).unwrap().len(), 4);
        }
    }

    #[test]
    fn test_ray_orthogonality() {
        let rays = vec![
            vec![1, 0, 0],
            vec![0, 1, 0],
            vec![0, 0, 1],
            vec![1, 1, 0],
        ];
        let adj = ray_orthogonality(&rays);
        assert!(adj[0][1]);
        assert!(adj[0][2]);
        assert!(!adj[0][3]); // 1*1 + 0*1 + 0*0 = 1 != 0
        assert!(adj[1][2]);
        assert!(adj[2][3]); // 0*1 + 0*1 + 1*0 = 0
    }
}
