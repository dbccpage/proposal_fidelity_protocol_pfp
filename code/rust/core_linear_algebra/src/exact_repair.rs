//! § 3 Definition 16.1: Exact Repair Directions
//!
//! The space of **exact repairs** is $B^1 := \operatorname{im}(d_0) \subseteq C^1$.
//! Elements of $B^1$ are declared *admissible repairs*.
//!
//! An exact-repair certificate is a cochain $\alpha \in C^0$ together with $d_0$
//! and $\omega$ so that $h' = \omega - d_0\alpha$ is well-typed in $C^1$.
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

/// The space $B^1 = \operatorname{im}(d_0)$ of exact repairs.
///
/// An exact repair is a vector $d_0 \alpha$ for some $\alpha \in C^0$.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExactRepairSpace {
    /// Dimension of $B^1 = \operatorname{rank}(d_0)$.
    pub rank: usize,
    /// Dimension of $C^1$.
    pub ambient_dim: usize,
    /// Basis vectors for im(d₀)
    pub basis: Vec<Vec<BigRational>>,
}

impl ExactRepairSpace {
    pub fn new(rank: usize, ambient_dim: usize) -> Self {
        Self {
            rank,
            ambient_dim,
            basis: Vec::new(),
        }
    }

    pub fn with_basis(basis: Vec<Vec<BigRational>>) -> Self {
        let ambient_dim = if basis.is_empty() { 0 } else { basis[0].len() };
        let rank = basis.len();
        Self {
            rank,
            ambient_dim,
            basis,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactRepairError {
    #[error("alpha is not in C^0: expected {expected} coordinates, got {got}")]
    AlphaNotInC0 { expected: usize, got: usize },
    #[error(
        "repair map d0 has shape {got_rows}x{got_cols}, expected {expected_rows}x{expected_cols}"
    )]
    RepairMapShapeMismatch {
        expected_rows: usize,
        expected_cols: usize,
        got_rows: usize,
        got_cols: usize,
    },
    #[error("repair does not zero the residual; exact class cannot be claimed")]
    NonzeroResidualClaimedExact,
}

/// A cochain $\alpha \in C^0$ that repairs a representative $\omega$ by $d_0\alpha$.
#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct ExactRepair {
    alpha: Vec<BigRational>,
    d0: Vec<Vec<BigRational>>,
    omega: Vec<BigRational>,
}

impl<'de> Deserialize<'de> for ExactRepair {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        #[derive(Deserialize)]
        struct Fields {
            alpha: Vec<BigRational>,
            d0: Vec<Vec<BigRational>>,
            omega: Vec<BigRational>,
        }

        let fields = Fields::deserialize(deserializer)?;
        Self::try_new(fields.alpha, fields.d0, fields.omega).map_err(serde::de::Error::custom)
    }
}

impl ExactRepair {
    pub fn try_new(
        alpha: Vec<BigRational>,
        d0: Vec<Vec<BigRational>>,
        omega: Vec<BigRational>,
    ) -> Result<Self, ExactRepairError> {
        let c0 = alpha.len();
        let c1 = omega.len();
        let got_rows = d0.len();
        let got_cols = d0.first().map(Vec::len).unwrap_or(c0);
        if got_rows != c1 || d0.iter().any(|row| row.len() != got_cols) {
            return Err(ExactRepairError::RepairMapShapeMismatch {
                expected_rows: c1,
                expected_cols: c0,
                got_rows,
                got_cols,
            });
        }
        if got_cols != c0 {
            return Err(ExactRepairError::AlphaNotInC0 {
                expected: got_cols,
                got: c0,
            });
        }
        Ok(Self { alpha, d0, omega })
    }

    pub fn residual_after(&self) -> Vec<BigRational> {
        self.d0
            .iter()
            .zip(&self.omega)
            .map(|(row, core_i)| {
                let repair = row
                    .iter()
                    .zip(&self.alpha)
                    .map(|(a, x)| a * x)
                    .sum::<BigRational>();
                core_i - repair
            })
            .collect()
    }

    pub fn try_exact_class(self) -> Result<Self, ExactRepairError> {
        if self.residual_after().iter().any(|x| !x.is_zero()) {
            Err(ExactRepairError::NonzeroResidualClaimedExact)
        } else {
            Ok(self)
        }
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_repair.rs
// Claim: urn:core:crates_rs:core-linear-algebra:exact-repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    #[test]
    fn malformed_wire_shapes_cannot_erase_residuals() {
        let malformed = [
            ExactRepair {
                alpha: vec![],
                d0: vec![],
                omega: vec![r(1)],
            },
            ExactRepair {
                alpha: vec![r(1)],
                d0: vec![vec![r(1)]],
                omega: vec![],
            },
            ExactRepair {
                alpha: vec![r(1)],
                d0: vec![vec![r(1)], vec![]],
                omega: vec![r(1), r(1)],
            },
            ExactRepair {
                alpha: vec![r(1), r(1)],
                d0: vec![vec![r(1)]],
                omega: vec![r(1)],
            },
        ];
        for repair in malformed {
            let wire = serde_json::to_value(&repair).expect("serialize malformed fixture");
            assert!(serde_json::from_value::<ExactRepair>(wire).is_err());
        }
    }

    #[test]
    fn validated_wire_roundtrips_preserve_exact_and_nonexact_residuals() {
        let half = BigRational::new(BigInt::from(1), BigInt::from(2));
        for omega in [r(1), r(2)] {
            let repair = ExactRepair::try_new(vec![half.clone()], vec![vec![r(2)]], vec![omega])
                .expect("well-typed repair");
            let expected = repair.residual_after();
            let wire = serde_json::to_vec(&repair).expect("serialize repair");
            let decoded: ExactRepair = serde_json::from_slice(&wire).expect("validated decode");
            assert_eq!(decoded, repair);
            assert_eq!(decoded.residual_after(), expected);
            assert_eq!(
                decoded.try_exact_class().is_ok(),
                expected.iter().all(Zero::is_zero)
            );
        }
        let empty = ExactRepair::try_new(vec![], vec![], vec![]).expect("zero-dimensional repair");
        let wire = serde_json::to_vec(&empty).expect("serialize empty repair");
        let decoded: ExactRepair = serde_json::from_slice(&wire).expect("empty decode");
        assert!(decoded.try_exact_class().is_ok());
    }

    #[test]
    fn empty_edge_space_preserves_nonempty_vertex_potentials() {
        let repair = ExactRepair::try_new(vec![r(1), r(2)], vec![], vec![])
            .expect("map from two vertex coordinates to the zero edge space");
        assert!(repair.residual_after().is_empty());
        let wire = serde_json::to_vec(&repair).expect("serialize zero-edge repair");
        let decoded: ExactRepair = serde_json::from_slice(&wire).expect("zero-edge decode");
        assert_eq!(decoded, repair);
        assert!(decoded.try_exact_class().is_ok());
    }

    #[test]
    fn alpha_not_in_c0_must_be_rejected() {
        let d0 = vec![vec![r(1)]];
        let omega = vec![r(2)];
        let alpha = vec![r(1), r(0)];
        assert_eq!(
            ExactRepair::try_new(alpha, d0, omega).unwrap_err(),
            ExactRepairError::AlphaNotInC0 {
                expected: 1,
                got: 2
            }
        );
    }

    #[test]
    fn repair_map_shape_mismatch_must_be_rejected() {
        let d0 = vec![vec![r(1)]];
        let omega = vec![r(2), r(0)];
        let alpha = vec![r(2)];
        assert_eq!(
            ExactRepair::try_new(alpha, d0, omega).unwrap_err(),
            ExactRepairError::RepairMapShapeMismatch {
                expected_rows: 2,
                expected_cols: 1,
                got_rows: 1,
                got_cols: 1,
            }
        );
    }

    #[test]
    fn nonzero_residual_cannot_claim_exact_class() {
        let repair = ExactRepair::try_new(vec![r(0)], vec![vec![r(1)]], vec![r(2)])
            .expect("well-typed repair");
        assert_eq!(repair.residual_after(), vec![r(2)]);
        assert_eq!(
            repair.try_exact_class().unwrap_err(),
            ExactRepairError::NonzeroResidualClaimedExact
        );

        let exact = ExactRepair::try_new(vec![r(2)], vec![vec![r(1)]], vec![r(2)])
            .expect("well-typed repair")
            .try_exact_class()
            .expect("h' = 0");
        assert_eq!(exact.residual_after(), vec![r(0)]);
    }
}
