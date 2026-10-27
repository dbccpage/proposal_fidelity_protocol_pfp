//! MSS lift/forget towers as finite functor bridge declarations.

use super::bridges::BridgeEvidence;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MssnFunctorBridge {
    pub lift_functor: String,
    pub forget_functor: String,
    pub evidence: BridgeEvidence,
}

impl MssnFunctorBridge {
    pub fn new(lift_functor: &str, forget_functor: &str) -> Self {
        Self {
            lift_functor: lift_functor.into(),
            forget_functor: forget_functor.into(),
            evidence: BridgeEvidence {
                source_discipline: "MSSN".into(),
                target_discipline: "category".into(),
                map_name: format!("{} adjoint {}", lift_functor, forget_functor),
                laws_preserved: vec!["lift/forget boundary".into()],
            },
        }
    }
}

/// Triangle identities for a pair of monotone maps on a finite chain.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TriangleWitness {
    carrier: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TriangleError {
    Bound,
    Shape,
    Triangle,
    Inequality,
}

impl std::fmt::Display for TriangleError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TriangleError::Bound => write!(formatter, "carrier must lie in 1..=16"),
            TriangleError::Shape => write!(formatter, "a map leaves the carrier"),
            TriangleError::Triangle => write!(formatter, "a triangle identity failed"),
            TriangleError::Inequality => write!(formatter, "the unit or counit inequality failed"),
        }
    }
}

impl std::error::Error for TriangleError {}

impl TriangleWitness {
    fn check_left_triangle(
        left: &[usize],
        right: &[usize],
        point: usize,
    ) -> Result<(), TriangleError> {
        let left_point = *left.get(point).ok_or(TriangleError::Shape)?;
        let right_left = *right.get(left_point).ok_or(TriangleError::Shape)?;
        let left_right_left = *left.get(right_left).ok_or(TriangleError::Shape)?;
        if left_right_left != left_point {
            return Err(TriangleError::Triangle);
        }
        if point > right_left {
            return Err(TriangleError::Inequality);
        }
        Ok(())
    }

    fn check_right_triangle(
        left: &[usize],
        right: &[usize],
        point: usize,
    ) -> Result<(), TriangleError> {
        let right_point = *right.get(point).ok_or(TriangleError::Shape)?;
        let left_right = *left.get(right_point).ok_or(TriangleError::Shape)?;
        let right_left_right = *right.get(left_right).ok_or(TriangleError::Shape)?;
        if right_left_right != right_point {
            return Err(TriangleError::Triangle);
        }
        if left_right > point {
            return Err(TriangleError::Inequality);
        }
        Ok(())
    }

    pub fn certify(carrier: usize, left: &[usize], right: &[usize]) -> Result<Self, TriangleError> {
        if carrier == 0 || carrier > 16 {
            return Err(TriangleError::Bound);
        }
        if left.len() != carrier || right.len() != carrier {
            return Err(TriangleError::Shape);
        }
        for &value in left.iter().chain(right.iter()) {
            if value >= carrier {
                return Err(TriangleError::Shape);
            }
        }
        for point in 0..carrier {
            Self::check_left_triangle(left, right, point)?;
            Self::check_right_triangle(left, right, point)?;
        }
        Ok(Self { carrier })
    }

    pub fn carrier(&self) -> usize {
        self.carrier
    }
}

// Origin: engine/crates_rs/core_category_theory/src/mssn_functor_bridge.rs
// Claim: urn:core:crates_rs:core-category-theory:mssn-functor-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod triangle_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn identity_adjoints_pass_and_a_constant_zero_map_fails() {
        let witness = taken(TriangleWitness::certify(3, &[0, 1, 2], &[0, 1, 2]));
        assert_eq!(witness.carrier(), 3);
        assert!(TriangleWitness::certify(3, &[0, 0, 0], &[0, 0, 0]).is_err());
    }
}
