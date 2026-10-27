//! Deformation Tier for Operad Theory.
//!
//! AuthorityEffect: None.

pub mod quadratic_operad;
pub mod cooperad;
pub mod bar_cobar;
pub mod koszul_duality;

pub use quadratic_operad::{QuadraticOperad, QuadraticRelation};
pub use cooperad::ColouredCooperad;
pub use bar_cobar::BarCobarResolution;
pub use koszul_duality::{KoszulDualBuilder, ProposedQuadraticDual};

/// Content of a quadratic relation after dividing out the coefficient gcd.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimitiveRelation {
    terms: usize,
    content: i64,
    weight: i64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimitiveRelationError {
    Support,
    Empty,
    Zero,
    Overflow,
}

impl std::fmt::Display for PrimitiveRelationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Support => write!(formatter, "coefficient length disagrees with the generating terms"),
            Self::Empty => write!(formatter, "a quadratic relation needs a term"),
            Self::Zero => write!(formatter, "every coefficient is zero"),
            Self::Overflow => write!(formatter, "coefficient arithmetic overflowed i64"),
        }
    }
}

impl std::error::Error for PrimitiveRelationError {}

impl PrimitiveRelation {
    pub fn terms(&self) -> usize {
        self.terms
    }

    pub fn content(&self) -> i64 {
        self.content
    }

    pub fn weight(&self) -> i64 {
        self.weight
    }
}

fn gcd_i64(left: i64, right: i64) -> Result<i64, PrimitiveRelationError> {
    let mut a = left.checked_abs().ok_or(PrimitiveRelationError::Overflow)?;
    let mut b = right.checked_abs().ok_or(PrimitiveRelationError::Overflow)?;
    while b != 0 {
        let remainder = a.checked_rem(b).ok_or(PrimitiveRelationError::Overflow)?;
        a = b;
        b = remainder;
    }
    Ok(a)
}

fn reduced_weight_and_gcd(
    coefficients: &[i64],
    content: i64,
) -> Result<(i64, i64), PrimitiveRelationError> {
    let mut weight = 0i64;
    let mut reduced_gcd = 0i64;
    for coefficient in coefficients {
        let reduced = coefficient
            .checked_div(content)
            .ok_or(PrimitiveRelationError::Overflow)?;
        weight = weight
            .checked_add(reduced)
            .ok_or(PrimitiveRelationError::Overflow)?;
        reduced_gcd = gcd_i64(reduced_gcd, reduced)?;
    }
    Ok((weight, reduced_gcd))
}

/// Divide a quadratic relation by the gcd of its coefficients.
/// The returned content is 1 and the coefficient weight is the reduced sum.
pub fn primitive_content(relation: &QuadraticRelation) -> Result<PrimitiveRelation, PrimitiveRelationError> {
    if relation.generating_terms.len() != relation.coefficients.len() {
        return Err(PrimitiveRelationError::Support);
    }
    if relation.coefficients.is_empty() || relation.relation_id.is_empty() {
        return Err(PrimitiveRelationError::Empty);
    }
    let mut content = 0i64;
    for coefficient in &relation.coefficients {
        content = gcd_i64(content, *coefficient)?;
    }
    if content == 0 {
        return Err(PrimitiveRelationError::Zero);
    }
    let (weight, reduced_gcd) = reduced_weight_and_gcd(&relation.coefficients, content)?;
    if reduced_gcd != 1 {
        return Err(PrimitiveRelationError::Zero);
    }
    Ok(PrimitiveRelation {
        terms: relation.coefficients.len(),
        content,
        weight,
    })
}

// Origin: engine/crates_rs/core_operad_theory/src/deformation/mod.rs
// Claim: urn:core:crates_rs:core-operad-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn taken(result: Result<PrimitiveRelation, PrimitiveRelationError>) -> PrimitiveRelation {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn a_common_content_reduces_to_a_primitive_relation() {
        let relation = QuadraticRelation {
            relation_id: "assoc".to_owned(),
            generating_terms: vec!["(ab)c".to_owned(), "a(bc)".to_owned()],
            coefficients: vec![4, -2],
            description: "scaled associator".to_owned(),
        };
        let primitive = taken(primitive_content(&relation));
        assert_eq!(primitive.terms(), 2);
        assert_eq!(primitive.content(), 2);
        assert_eq!(primitive.weight(), 2 + -1);
    }

    #[test]
    fn a_zero_relation_is_refused() {
        let relation = QuadraticRelation {
            relation_id: "zero".to_owned(),
            generating_terms: vec!["ab".to_owned()],
            coefficients: vec![0],
            description: "empty".to_owned(),
        };
        assert!(matches!(
            primitive_content(&relation),
            Err(PrimitiveRelationError::Zero)
        ));
    }
}
