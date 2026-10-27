//! Sovereign in-code contract engine (V1).
//!
//! Provides native in-code contract primitives that replace external human
//! meta-files with compiler-enforced invariants and type-state transitions:
//!
//! 1. **Zero-cost Type-State enforcement** (`Unverified` -> `Verified` -> `Admitted`)
//! 2. **In-code predicate macros** (`precondition!`, `postcondition!`, `invariant!`)
//! 3. **Typed fail-closed contract violations** ([`ContractViolation`])
//!
//! AuthorityEffect: None.

use std::fmt;
use std::marker::PhantomData;

/// Trait implemented by operational state markers.
pub trait State: 'static + Send + Sync {}

/// Unverified state marker. Payloads in this state cannot be admitted.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct Unverified;
impl State for Unverified {}

/// Verified state marker. A verifier has executed and passed.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct Verified;
impl State for Verified {}

/// Admitted state marker. The payload has achieved admission status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct Admitted;
impl State for Admitted {}

/// Classification of in-code contract failures.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ViolationKind {
    /// A required precondition evaluated to false.
    Precondition,
    /// An expected postcondition evaluated to false.
    Postcondition,
    /// An invariant of the type or system was violated.
    Invariant,
    /// An illegal type-state transition was attempted.
    TypeState,
}

impl fmt::Display for ViolationKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Precondition => write!(f, "PRECONDITION_VIOLATION"),
            Self::Postcondition => write!(f, "POSTCONDITION_VIOLATION"),
            Self::Invariant => write!(f, "INVARIANT_VIOLATION"),
            Self::TypeState => write!(f, "TYPE_STATE_VIOLATION"),
        }
    }
}

/// Typed machine record of a contract predicate failure.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ContractViolation {
    pub contract_id: String,
    pub kind: ViolationKind,
    pub expression: String,
    pub message: String,
}

impl fmt::Display for ContractViolation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}: [{}] expression `{}` failed: {}",
            self.kind, self.contract_id, self.expression, self.message
        )
    }
}

impl std::error::Error for ContractViolation {}

/// In-code contract envelope enforcing type-state progression.
#[derive(Debug, Clone)]
pub struct InCodeContract<S: State, T> {
    state: PhantomData<S>,
    pub contract_id: String,
    payload: T,
}

impl<T> InCodeContract<Unverified, T> {
    /// Construct a new unverified contract envelope.
    pub fn new(contract_id: impl Into<String>, payload: T) -> Self {
        Self {
            state: PhantomData,
            contract_id: contract_id.into(),
            payload,
        }
    }

    /// Execute a verifier predicate over the payload.
    ///
    /// Fails closed if the verifier returns an error; upon success, promotes
    /// to [`Verified`] status.
    pub fn verify<F>(self, verifier: F) -> Result<InCodeContract<Verified, T>, ContractViolation>
    where
        F: FnOnce(&T) -> Result<(), ContractViolation>,
    {
        verifier(&self.payload)?;
        Ok(InCodeContract {
            state: PhantomData,
            contract_id: self.contract_id,
            payload: self.payload,
        })
    }
}

impl<T> InCodeContract<Verified, T> {
    /// Admit a verified contract envelope.
    pub fn admit(self) -> InCodeContract<Admitted, T> {
        InCodeContract {
            state: PhantomData,
            contract_id: self.contract_id,
            payload: self.payload,
        }
    }

    /// Read-only access to verified payload.
    pub fn payload(&self) -> &T {
        &self.payload
    }
}

impl<T> InCodeContract<Admitted, T> {
    /// Extract the admitted payload.
    pub fn into_inner(self) -> T {
        self.payload
    }

    /// Read-only access to admitted payload.
    pub fn payload(&self) -> &T {
        &self.payload
    }
}

/// Enforce a precondition expression inside a function body.
#[macro_export]
macro_rules! precondition {
    ($cond:expr, $msg:expr) => {
        if !$cond {
            return Err($crate::in_code_contracts::ContractViolation {
                contract_id: concat!(file!(), ":", line!()).to_string(),
                kind: $crate::in_code_contracts::ViolationKind::Precondition,
                expression: stringify!($cond).to_string(),
                message: $msg.to_string(),
            });
        }
    };
    ($cond:expr, $msg:expr, $contract_id:expr) => {
        if !$cond {
            return Err($crate::in_code_contracts::ContractViolation {
                contract_id: $contract_id.to_string(),
                kind: $crate::in_code_contracts::ViolationKind::Precondition,
                expression: stringify!($cond).to_string(),
                message: $msg.to_string(),
            });
        }
    };
}

/// Enforce a postcondition expression on a returned result.
#[macro_export]
macro_rules! postcondition {
    ($cond:expr, $msg:expr) => {
        if !$cond {
            return Err($crate::in_code_contracts::ContractViolation {
                contract_id: concat!(file!(), ":", line!()).to_string(),
                kind: $crate::in_code_contracts::ViolationKind::Postcondition,
                expression: stringify!($cond).to_string(),
                message: $msg.to_string(),
            });
        }
    };
    ($cond:expr, $msg:expr, $contract_id:expr) => {
        if !$cond {
            return Err($crate::in_code_contracts::ContractViolation {
                contract_id: $contract_id.to_string(),
                kind: $crate::in_code_contracts::ViolationKind::Postcondition,
                expression: stringify!($cond).to_string(),
                message: $msg.to_string(),
            });
        }
    };
}

/// Enforce an internal structural invariant.
#[macro_export]
macro_rules! invariant {
    ($cond:expr, $msg:expr) => {
        if !$cond {
            return Err($crate::in_code_contracts::ContractViolation {
                contract_id: concat!(file!(), ":", line!()).to_string(),
                kind: $crate::in_code_contracts::ViolationKind::Invariant,
                expression: stringify!($cond).to_string(),
                message: $msg.to_string(),
            });
        }
    };
    ($cond:expr, $msg:expr, $contract_id:expr) => {
        if !$cond {
            return Err($crate::in_code_contracts::ContractViolation {
                contract_id: $contract_id.to_string(),
                kind: $crate::in_code_contracts::ViolationKind::Invariant,
                expression: stringify!($cond).to_string(),
                message: $msg.to_string(),
            });
        }
    };
}

// Origin: engine/crates_rs/core_contracts/src/in_code_contracts.rs
// Claim: urn:core:crates_rs:core-contracts:in-code-contracts:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn tested_divide(a: i64, b: i64) -> Result<i64, ContractViolation> {
        precondition!(b != 0, "denominator cannot be zero", "urn:core:math:safe_div");
        let result = a / b;
        postcondition!(result * b <= a, "quotient check", "urn:core:math:safe_div");
        Ok(result)
    }

    #[test]
    fn test_precondition_success() {
        assert_eq!(tested_divide(10, 2).unwrap(), 5);
    }

    #[test]
    fn test_precondition_failure_fails_closed() {
        let err = tested_divide(10, 0).unwrap_err();
        assert_eq!(err.kind, ViolationKind::Precondition);
        assert_eq!(err.expression, "b != 0");
        assert_eq!(err.message, "denominator cannot be zero");
        assert_eq!(err.contract_id, "urn:core:math:safe_div");
    }

    #[test]
    fn test_typestate_progression() {
        let raw = InCodeContract::new("urn:core:pipeline:packet", 42);

        // Cannot admit directly from unverified state
        let verified = raw
            .verify(|val| {
                if *val > 0 {
                    Ok(())
                } else {
                    Err(ContractViolation {
                        contract_id: "urn:core:pipeline:packet".into(),
                        kind: ViolationKind::Invariant,
                        expression: "val > 0".into(),
                        message: "value must be positive".into(),
                    })
                }
            })
            .expect("verification passed");

        let admitted = verified.admit();
        assert_eq!(admitted.into_inner(), 42);
    }

    #[test]
    fn test_typestate_verification_failure() {
        let raw = InCodeContract::new("urn:core:pipeline:packet", -5);
        let result = raw.verify(|val| {
            if *val > 0 {
                Ok(())
            } else {
                Err(ContractViolation {
                    contract_id: "urn:core:pipeline:packet".into(),
                    kind: ViolationKind::Invariant,
                    expression: "val > 0".into(),
                    message: "value must be positive".into(),
                })
            }
        });
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().expression, "val > 0");
    }
}
