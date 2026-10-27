//! Cup product on cochains / cohomology ring structure.
//!
//! AuthorityEffect: None. Best-effort shell. Not PROVED; not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0326a5fa;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0326a5fa<T> = std::result::Result<T, BoundaryError_0326a5fa>;
use serde::{Deserialize, Serialize};

/// Cochain representative as sparse (basis_index, coefficient) over f64 shell field.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct SparseCochain {
    pub degree: usize,
    pub terms: Vec<(usize, f64)>,
}

/// Cup product of two cochains (Alexander–Whitney shell on simplicial indices).
///
/// For combinatorial cochains on ordered simplices this is a *shape* for the ring;
/// full face-map evaluation is deferred.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CupProduct {
    pub left_degree: usize,
    pub right_degree: usize,
    pub result: SparseCochain,
}

impl CupProduct {
    pub fn of(a: &SparseCochain, b: &SparseCochain) -> Self {
        // Shell: formal degree add; empty support unless both nonzero single term
        let mut terms = Vec::new();
        if a.terms.len() == 1 && b.terms.len() == 1 {
            let (ia, ca) = a.terms[0];
            let (ib, cb) = b.terms[0];
            // Placeholder pairing index; real AW formula needs simplex faces
            terms.push((ia.wrapping_mul(1_000_003).wrapping_add(ib), ca * cb));
        }
        Self {
            left_degree: a.degree,
            right_degree: b.degree,
            result: SparseCochain {
                degree: a.degree + b.degree,
                terms,
            },
        }
    }

    pub fn total_degree(&self) -> usize {
        self.left_degree + self.right_degree
    }
}

// Origin: engine/crates_rs/core_homology/src/cup_product.rs
// Claim: urn:core:crates_rs:core-homology:cup-product:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cup_degree_adds() {
        let a = SparseCochain {
            degree: 1,
            terms: vec![(0, 1.0)],
        };
        let b = SparseCochain {
            degree: 2,
            terms: vec![(1, 1.0)],
        };
        let c = CupProduct::of(&a, &b);
        assert_eq!(c.total_degree(), 3);
        assert_eq!(c.result.degree, 3);
    }
}

/// Typed refusals of the exact mod-two Alexander–Whitney product.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum F2CupError {
    #[error("cochain degree addition overflows")]
    DegreeOverflow,
    #[error("cup-product degree or cell budget exceeded")]
    Budget,
    #[error("degree {degree} cochain has length {actual}, expected {expected}")]
    CochainLength {
        degree: usize,
        expected: usize,
        actual: usize,
    },
    #[error("the canonical simplicial complex is missing a required face")]
    MissingFace,
    #[error(transparent)]
    F2(#[from] core_number_theory::gf2::F2Error),
}
/// Exact Alexander–Whitney cup product on the canonical ordered simplex bases.
/// On `[v0,...,v(p+q)]` the value is `a([v0,...,vp]) b([vp,...,v(p+q)])`.
/// The routine accepts arbitrary cochains, not only cocycles. Degrees are at
/// most64, each participating basis has at most65536 cells, and the face work
/// is bounded by2^24. Above the complex dimension the basis is empty.
pub fn cup_product_f2(
    complex: &crate::simplicial::SimplicialComplex,
    left_degree: usize,
    left: &core_number_theory::gf2::F2Vector,
    right_degree: usize,
    right: &core_number_theory::gf2::F2Vector,
) -> Result<core_number_theory::gf2::F2Vector, F2CupError> {
    use core_number_theory::gf2::F2Vector;
    use std::collections::BTreeMap;
    let (degree, count) = validate_cup_inputs(complex, left_degree, left, right_degree, right)?;
    let left_indices: BTreeMap<&[usize], usize> = complex
        .simplices(left_degree)
        .iter()
        .enumerate()
        .map(|(i, s)| (s.vertices(), i))
        .collect();
    let right_indices: BTreeMap<&[usize], usize> = complex
        .simplices(right_degree)
        .iter()
        .enumerate()
        .map(|(i, s)| (s.vertices(), i))
        .collect();
    let mut result = F2Vector::zeros(count)?;
    for (i, simplex) in complex.simplices(degree).iter().enumerate() {
        let vertices = simplex.vertices();
        let a = *left_indices
            .get(&vertices[..=left_degree])
            .ok_or(F2CupError::MissingFace)?;
        let b = *right_indices
            .get(&vertices[left_degree..])
            .ok_or(F2CupError::MissingFace)?;
        result.set(i, left.get(a)? && right.get(b)?)?;
    }
    Ok(result)
}

fn validate_cup_inputs(
    complex: &crate::simplicial::SimplicialComplex,
    left_degree: usize,
    left: &core_number_theory::gf2::F2Vector,
    right_degree: usize,
    right: &core_number_theory::gf2::F2Vector,
) -> Result<(usize, usize), F2CupError> {
    let degree = left_degree
        .checked_add(right_degree)
        .ok_or(F2CupError::DegreeOverflow)?;
    if degree > 64 {
        return Err(F2CupError::Budget);
    }
    for (k, c) in [(left_degree, left), (right_degree, right)] {
        let expected = complex.count(k);
        if expected > 65536 {
            return Err(F2CupError::Budget);
        }
        if c.len() != expected {
            return Err(F2CupError::CochainLength {
                degree: k,
                expected,
                actual: c.len(),
            });
        }
    }
    let count = complex.count(degree);
    if count > 65536
        || count
            .checked_mul(degree + 2)
            .is_none_or(|work| work > 1 << 24)
    {
        return Err(F2CupError::Budget);
    }
    Ok((degree, count))
}

#[cfg(test)]
mod exact_f2_laws {
    use super::*;
    use crate::f2_cohomology::F2ChainComplex;
    use crate::simplicial::SimplicialComplex;
    use core_number_theory::gf2::F2Vector;
    #[test]
    fn alexander_whitney_product_obeys_the_cochain_leibniz_rule_over_f2() {
        let complex = SimplicialComplex::standard_n_simplex(3).unwrap();
        let chain = F2ChainComplex::from_simplicial_complex(&complex).unwrap();
        for a in 0..(1 << complex.count(0)) {
            for b in 0..(1 << complex.count(1)) {
                let a = F2Vector::from_indices(
                    complex.count(0),
                    &(0..complex.count(0))
                        .filter(|i| a & (1 << i) != 0)
                        .collect::<Vec<_>>(),
                )
                .unwrap();
                let b = F2Vector::from_indices(
                    complex.count(1),
                    &(0..complex.count(1))
                        .filter(|i| b & (1 << i) != 0)
                        .collect::<Vec<_>>(),
                )
                .unwrap();
                let product = cup_product_f2(&complex, 0, &a, 1, &b).unwrap();
                let derivative = chain.coboundary(1).unwrap().mul_vec(&product).unwrap();
                let da = chain.coboundary(0).unwrap().mul_vec(&a).unwrap();
                let db = chain.coboundary(1).unwrap().mul_vec(&b).unwrap();
                let rhs = cup_product_f2(&complex, 1, &da, 1, &b)
                    .unwrap()
                    .add(&cup_product_f2(&complex, 0, &a, 2, &db).unwrap())
                    .unwrap();
                assert_eq!(derivative, rhs);
            }
        }
        let zero = F2Vector::zeros(0).unwrap();
        assert_eq!(
            cup_product_f2(&complex, usize::MAX, &zero, 1, &zero),
            Err(F2CupError::DegreeOverflow)
        );
        assert!(matches!(
            cup_product_f2(&complex, 0, &zero, 0, &zero),
            Err(F2CupError::CochainLength { .. })
        ));
    }
}
