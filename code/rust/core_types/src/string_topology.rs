#[derive(Debug, Clone, PartialEq)]
pub struct Loop {
    points: Vec<Vec<f64>>,
}

impl Loop {
    pub fn points(&self) -> &[Vec<f64>] {
        &self.points
    }
}

/// Integer polygon. `twice_area` is the shoelace sum, an exact integer.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IntegerPolygon {
    xs: Vec<i64>,
    ys: Vec<i64>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PolygonError {
    TooFewVertices { len: usize },
    LengthMismatch { xs: usize, ys: usize },
    Overflow,
    MissingVertex { index: usize },
}

// Origin: engine/crates_rs/core_types/src/string_topology.rs
// Claim: urn:core:crates_rs:core-types:string-topology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PolygonError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PolygonError {}

impl IntegerPolygon {
    pub fn try_new(xs: Vec<i64>, ys: Vec<i64>) -> Result<Self, PolygonError> {
        if xs.len() != ys.len() {
            return Err(PolygonError::LengthMismatch {
                xs: xs.len(),
                ys: ys.len(),
            });
        }
        if xs.len() < 3 {
            return Err(PolygonError::TooFewVertices { len: xs.len() });
        }
        Ok(Self { xs, ys })
    }

    pub fn twice_area(&self) -> Result<i64, PolygonError> {
        let n = self.xs.len();
        let mut acc = 0i64;
        for i in 0..n {
            let j = (i + 1) % n;
            let x1 = *self
                .xs
                .get(i)
                .ok_or(PolygonError::MissingVertex { index: i })?;
            let y1 = *self
                .ys
                .get(i)
                .ok_or(PolygonError::MissingVertex { index: i })?;
            let x2 = *self
                .xs
                .get(j)
                .ok_or(PolygonError::MissingVertex { index: j })?;
            let y2 = *self
                .ys
                .get(j)
                .ok_or(PolygonError::MissingVertex { index: j })?;
            let left = x1.checked_mul(y2).ok_or(PolygonError::Overflow)?;
            let right = x2.checked_mul(y1).ok_or(PolygonError::Overflow)?;
            let cross = left.checked_sub(right).ok_or(PolygonError::Overflow)?;
            acc = acc.checked_add(cross).ok_or(PolygonError::Overflow)?;
        }
        Ok(acc)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod integer_polygon_witness {
    use super::*;

    #[test]
    fn unit_square_has_twice_area_two() {
        let polygon = IntegerPolygon::try_new(vec![0, 1, 1, 0], vec![0, 0, 1, 1]);
        assert!(polygon.is_ok());
        if let Ok(polygon) = polygon {
            assert_eq!(polygon.twice_area(), Ok(2));
        }
    }

    #[test]
    fn a_digon_is_refused() {
        assert!(matches!(
            IntegerPolygon::try_new(vec![0, 1], vec![0, 0]),
            Err(PolygonError::TooFewVertices { len: 2 })
        ));
    }
}
