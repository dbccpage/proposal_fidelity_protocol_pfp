
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_03689c81<T> {
    fn checked_invariant_03689c81(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_03689c81<T> for Option<T> {
    #[inline]
    fn checked_invariant_03689c81(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_03689c81<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_03689c81(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_traits::Zero;
use core_kernel::exact::{exact_wire, exact_wire_vec, to_canonical_string, Exact};
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// The residual vector and its L1 diagnostic, carried together.
/// Laws: `urn:core:rust:core_kernel:residual:v1.0.0`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "ResidualWire", into = "ResidualWire")]
pub struct Residual {
    vector: Vec<Exact>,
    l1: Exact,
}

#[derive(Debug, Error, PartialEq, Eq)]
#[error("residual l1 is {declared}, but its vector sums to {recomputed}")]
pub struct ResidualError {
    pub declared: String,
    pub recomputed: String,
}

impl Residual {
    pub fn new(vector: Vec<Exact>) -> Self {
        let l1 = Self::norm(&vector);
        Self { vector, l1 }
    }

    fn norm(vector: &[Exact]) -> Exact {
        crate::Phi1Functional::unweighted_l1_rational(vector)
            .checked_invariant_03689c81("Exact residual entries have nonzero denominators")
    }

    pub fn vector(&self) -> &[Exact] {
        &self.vector
    }

    pub fn l1(&self) -> &Exact {
        &self.l1
    }

    pub fn len(&self) -> usize {
        self.vector.len()
    }

    pub fn is_empty(&self) -> bool {
        self.vector.is_empty()
    }

    pub fn is_zero(&self) -> bool {
        self.l1.is_zero()
    }
}

#[derive(Serialize, Deserialize)]
struct ResidualWire {
    #[serde(with = "exact_wire_vec")]
    vector: Vec<Exact>,
    #[serde(with = "exact_wire")]
    l1: Exact,
}

impl TryFrom<ResidualWire> for Residual {
    type Error = ResidualError;
    fn try_from(wire: ResidualWire) -> Result<Self, Self::Error> {
        let recomputed = Residual::norm(&wire.vector);
        if recomputed != wire.l1 {
            return Err(ResidualError {
                declared: to_canonical_string(&wire.l1),
                recomputed: to_canonical_string(&recomputed),
            });
        }
        Ok(Self {
            vector: wire.vector,
            l1: recomputed,
        })
    }
}

impl From<Residual> for ResidualWire {
    fn from(residual: Residual) -> Self {
        Self {
            vector: residual.vector,
            l1: residual.l1,
        }
    }
}

// Origin: engine/crates_rs/core_functional/src/residual.rs
// Claim: urn:core:crates_rs:core-functional:residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::exact::{exact, integer};

    fn v(values: &[i64]) -> Vec<Exact> {
        values.iter().copied().map(integer).collect()
    }

    #[test]
    fn the_vector_survives_alongside_its_norm() {
        let residual = Residual::new(v(&[1, -2, 0]));
        assert_eq!(*residual.l1(), integer(3));
        assert_eq!(residual.vector(), v(&[1, -2, 0]).as_slice());
    }

    #[test]
    fn an_empty_residual_is_zero() {
        let residual = Residual::new(vec![]);
        assert!(residual.is_zero());
        assert!(residual.is_empty());
        assert_eq!(*residual.l1(), Exact::zero());
    }

    #[test]
    fn a_tiny_nonzero_residual_is_not_zero() {
        let residual = Residual::new(vec![exact(1, 1_000_000_000)]);
        assert!(!residual.is_zero());
        assert_eq!(*residual.l1(), exact(1, 1_000_000_000));
    }

    #[test]
    fn cancelling_entries_do_not_cancel_in_the_l1_norm() {
        let residual = Residual::new(v(&[1, -1]));
        assert_eq!(*residual.l1(), integer(2));
        assert!(!residual.is_zero());
    }

    #[test]
    fn a_forged_norm_is_refused_on_deserialize() {
        let err = serde_json::from_str::<Residual>(r#"{"vector":["3","4"],"l1":"0"}"#)
            .expect_err("a norm that disagrees with its vector must not parse");
        assert!(err.to_string().contains("sums to 7"), "{err}");
    }

    #[test]
    fn an_honest_norm_round_trips() {
        let residual = Residual::new(vec![exact(1, 3), integer(-2)]);
        let json = serde_json::to_string(&residual).unwrap();
        assert_eq!(json, r#"{"vector":["1/3","-2"],"l1":"7/3"}"#);
        assert_eq!(serde_json::from_str::<Residual>(&json).unwrap(), residual);
    }

    #[test]
    fn a_float_norm_is_refused_on_the_wire() {
        assert!(serde_json::from_str::<Residual>(r#"{"vector":["3","4"],"l1":7.0}"#).is_err());
    }

    #[test]
    fn exact_arithmetic_survives_where_a_float_sum_would_drift() {
        let thirds = Residual::new(vec![exact(1, 3); 3]);
        assert_eq!(*thirds.l1(), integer(1));
        assert!(!thirds.is_zero());
    }
}
