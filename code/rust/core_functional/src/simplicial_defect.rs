//! Exact successive closure measurements on an explicitly oriented finite carrier.
//! Cell labels are supplied as indices. Missing faces refuse; no partial boundary
//! is silently interpreted as a zero defect. Results confer no authorization.

use crate::gamma2::{ExactGamma2Error, Gamma2Functional};
use num_rational::BigRational;
use num_traits::{One, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SimplicialDefectError {
    #[error("a cell repeats a vertex")]
    RepeatedVertex,
    #[error("a boundary face is missing or ambiguous")]
    MissingOrAmbiguousFace,
    #[error(transparent)]
    Evaluation(#[from] ExactGamma2Error),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SimplicialDefects {
    pub gamma2: BigRational,
    pub degree_three_closure: BigRational,
    pub degree_four_closure: BigRational,
    pub face_values: Vec<BigRational>,
    pub tetrahedron_values: Vec<BigRational>,
    pub simplex_values: Vec<BigRational>,
}

fn coboundary<const LOWER: usize, const UPPER: usize>(
    lower: &[[usize; LOWER]],
    upper: &[[usize; UPPER]],
) -> Result<Vec<Vec<BigRational>>, SimplicialDefectError> {
    if lower
        .iter()
        .any(|cell| cell.iter().enumerate().any(|(i, v)| cell[..i].contains(v)))
    {
        return Err(SimplicialDefectError::RepeatedVertex);
    }
    let mut rows = Vec::with_capacity(upper.len());
    for cell in upper {
        if cell.iter().enumerate().any(|(i, v)| cell[..i].contains(v)) {
            return Err(SimplicialDefectError::RepeatedVertex);
        }
        let mut row = vec![BigRational::zero(); lower.len()];
        for omitted in 0..UPPER {
            let face: Vec<_> = cell
                .iter()
                .enumerate()
                .filter(|(i, _)| *i != omitted)
                .map(|(_, v)| *v)
                .collect();
            let matches: Vec<_> = lower
                .iter()
                .enumerate()
                .filter(|(_, candidate)| candidate.iter().all(|v| face.contains(v)))
                .collect();
            if matches.len() != 1 {
                return Err(SimplicialDefectError::MissingOrAmbiguousFace);
            }
            let (index, original) = matches[0];
            let permutation: Vec<_> = face
                .iter()
                .map(|v| {
                    original
                        .iter()
                        .position(|x| x == v)
                        .ok_or(SimplicialDefectError::MissingOrAmbiguousFace)
                })
                .collect::<Result<_, _>>()?;
            let inversions: usize = permutation
                .iter()
                .enumerate()
                .map(|(i, p)| permutation[i + 1..].iter().filter(|q| *q < p).count())
                .sum();
            row[index] = if (omitted + inversions) % 2 == 0 {
                BigRational::one()
            } else {
                -BigRational::one()
            };
        }
        rows.push(row);
    }
    Ok(rows)
}

pub fn evaluate_simplicial_defects(
    edges: &[[usize; 2]],
    faces: &[[usize; 3]],
    tetrahedra: &[[usize; 4]],
    four_simplices: &[[usize; 5]],
    cochain: &[BigRational],
) -> Result<SimplicialDefects, SimplicialDefectError> {
    if edges.len() != cochain.len() {
        return Err(ExactGamma2Error::D1ColumnMismatch {
            row: 0,
            expected: edges.len(),
            actual: cochain.len(),
        }
        .into());
    }
    let face_measurement = Gamma2Functional::try_compute_raw(cochain, &coboundary(edges, faces)?)?;
    let tetrahedron_measurement = Gamma2Functional::try_compute_raw(
        face_measurement.coboundary(),
        &coboundary(faces, tetrahedra)?,
    )?;
    let simplex_measurement = Gamma2Functional::try_compute_raw(
        tetrahedron_measurement.coboundary(),
        &coboundary(tetrahedra, four_simplices)?,
    )?;
    Ok(SimplicialDefects {
        gamma2: face_measurement.value().clone(),
        degree_three_closure: tetrahedron_measurement.value().clone(),
        degree_four_closure: simplex_measurement.value().clone(),
        face_values: face_measurement.coboundary().to_vec(),
        tetrahedron_values: tetrahedron_measurement.coboundary().to_vec(),
        simplex_values: simplex_measurement.coboundary().to_vec(),
    })
}

// Origin: engine/crates_rs/core_functional/src/simplicial_defect.rs
// Claim: urn:core:crates_rs:core-functional:simplicial-defect:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }

    #[test]
    fn oriented_triangle_has_one_closure_value_and_orientation_invariant_mass() {
        let edges = [[0, 1], [1, 2], [2, 0]];
        let first =
            evaluate_simplicial_defects(&edges, &[[0, 1, 2]], &[], &[], &[q(2), q(3), q(-1)])
                .unwrap();
        let reversed =
            evaluate_simplicial_defects(&edges, &[[0, 2, 1]], &[], &[], &[q(2), q(3), q(-1)])
                .unwrap();
        assert_eq!(first.gamma2, q(4));
        assert_eq!(first.face_values, vec![q(4)]);
        assert_eq!(reversed.face_values, vec![q(-4)]);
        assert_eq!(first.gamma2, reversed.gamma2);
    }

    #[test]
    fn missing_faces_and_repeated_vertices_are_refusals() {
        assert_eq!(
            evaluate_simplicial_defects(&[[0, 0]], &[], &[], &[], &[q(1)]),
            Err(SimplicialDefectError::RepeatedVertex)
        );
        assert_eq!(
            evaluate_simplicial_defects(&[[0, 1]], &[[0, 1, 2]], &[], &[], &[q(1)]),
            Err(SimplicialDefectError::MissingOrAmbiguousFace)
        );
        assert_eq!(
            evaluate_simplicial_defects(&[], &[[0, 0, 1]], &[], &[], &[]),
            Err(SimplicialDefectError::RepeatedVertex)
        );
    }
}
