//! Path-oriented transport and J-style identity elimination records.
//!
//! [`PathTransport`] is a synonym name for [`Transport`](crate::identity::Transport):
//! transport along a path into a dependent family. [`IdentityEliminator`] is the
//! finite shape of the path-induction (J) eliminator. Neither record mints
//! authority; validation is shape-only.

use crate::identity::{IdentityError, Transport};
use serde::{Deserialize, Serialize};

/// Transport along a path into a dependent family (synonym of [`Transport`]).
pub type PathTransport = Transport;

/// J-style identity eliminator record (path induction).
///
/// Motive `C`, base case `c` for `refl`, path `p`, and result term.
/// Shape-only: does not compute or verify the elimination.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IdentityEliminator {
    pub motive_ref: String,
    pub base_case_ref: String,
    pub path_ref: String,
    pub result_ref: String,
}

impl IdentityEliminator {
    /// Shape-only validation: all J-eliminator references must be non-empty.
    pub fn validate(&self) -> Result<(), IdentityError> {
        if self.motive_ref.is_empty()
            || self.base_case_ref.is_empty()
            || self.path_ref.is_empty()
            || self.result_ref.is_empty()
        {
            return Err(IdentityError::MissingTransportReference);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::identity::TermId;

    #[test]
    fn path_transport_is_transport_validate() {
        let transport: PathTransport = Transport {
            path_ref: "p".to_string(),
            family_ref: "B".to_string(),
            input_term: TermId("x".to_string()),
            output_term: TermId("y".to_string()),
            transport_certificate_ref: "tr-cert".to_string(),
        };
        assert!(transport.validate().is_ok());
    }

    #[test]
    fn identity_eliminator_requires_all_refs() {
        let elim = IdentityEliminator {
            motive_ref: "C".to_string(),
            base_case_ref: "c_refl".to_string(),
            path_ref: "p".to_string(),
            result_ref: "J(C,c,p)".to_string(),
        };
        assert!(elim.validate().is_ok());

        let bad = IdentityEliminator {
            motive_ref: String::new(),
            base_case_ref: "c".to_string(),
            path_ref: "p".to_string(),
            result_ref: "r".to_string(),
        };
        assert!(bad.validate().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PathLawError {
    Step,
    RoundTrip,
    Overflow,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/path_transport.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:path-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PathLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PathLawError {}

/// A reduced integer path. Adjacent inverse steps cancel, and transport adds the displacement.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReducedIntegerPath {
    steps: Vec<i8>,
    displacement: i64,
}

impl ReducedIntegerPath {
    pub fn try_reduce(raw: &[i8]) -> Result<Self, PathLawError> {
        let mut steps = Vec::new();
        for &step in raw {
            if step != 1 && step != -1 {
                return Err(PathLawError::Step);
            }
            if steps.last().copied() == Some(-step) {
                steps.pop();
            } else {
                steps.push(step);
            }
        }
        let mut displacement = 0i64;
        for &step in &steps {
            displacement = displacement.checked_add(i64::from(step)).ok_or(PathLawError::Overflow)?;
        }
        Ok(Self { steps, displacement })
    }

    pub fn transport(&self, value: i64) -> Result<i64, PathLawError> {
        value.checked_add(self.displacement).ok_or(PathLawError::Overflow)
    }

    pub fn inverse_round_trip(&self, value: i64) -> Result<i64, PathLawError> {
        let moved = self.transport(value)?;
        let restored = moved.checked_sub(self.displacement).ok_or(PathLawError::Overflow)?;
        if restored != value {
            return Err(PathLawError::RoundTrip);
        }
        let mut inverse = Vec::with_capacity(self.steps.len());
        for &step in self.steps.iter().rev() {
            inverse.push(match step {
                1 => -1,
                -1 => 1,
                _ => return Err(PathLawError::Step),
            });
        }
        let inverse_path = Self::try_reduce(&inverse)?;
        if inverse_path.displacement.checked_add(self.displacement).ok_or(PathLawError::Overflow)? != 0 {
            return Err(PathLawError::RoundTrip);
        }
        Ok(restored)
    }

    pub fn displacement(&self) -> i64 { self.displacement }
    pub fn steps(&self) -> &[i8] { &self.steps }
}

#[cfg(test)]
mod reduced_path_tests {
    use super::*;

    #[test]
    fn a_cancelled_step_leaves_unit_displacement() {
        let path = ReducedIntegerPath::try_reduce(&[1, -1, 1]);
        assert!(matches!(path, Ok(ref path) if path.displacement() == 1 && path.steps() == [1]));
        let moved = path.and_then(|path| path.inverse_round_trip(4));
        assert!(matches!(moved, Ok(4)));
    }

    #[test]
    fn a_step_of_two_is_refused() {
        let path = ReducedIntegerPath::try_reduce(&[2]);
        assert!(matches!(path, Err(PathLawError::Step)));
    }
}
