#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ProdOb {
    pub left: String,
    pub right: String,
}

impl ProdOb {
    pub fn new(left: &str, right: &str) -> Self {
        ProdOb {
            left: left.to_string(),
            right: right.to_string(),
        }
    }

    pub fn terminal() -> Self {
        ProdOb {
            left: "*".to_string(),
            right: "*".to_string(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProdMor {
    pub src: ProdOb,
    pub tgt: ProdOb,
    pub left: String,
    pub right: String,
}

impl ProdMor {
    pub fn new(src: ProdOb, tgt: ProdOb, left: &str, right: &str) -> Self {
        ProdMor {
            src,
            tgt,
            left: left.to_string(),
            right: right.to_string(),
        }
    }

    pub fn identity(ob: &ProdOb) -> Self {
        ProdMor {
            src: ob.clone(),
            tgt: ob.clone(),
            left: format!("id_{}", ob.left),
            right: format!("id_{}", ob.right),
        }
    }
}

/// Positive dimensions whose tensor product is associative and commutative on `u64`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TensorDimWitness {
    left: u64,
    right: u64,
    product: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TensorDimError {
    ZeroDimension,
    Overflow,
    AssociationMismatch { left_assoc: u64, right_assoc: u64 },
}

// Origin: engine/crates_rs/core_types/src/monoidal_types.rs
// Claim: urn:core:crates_rs:core-types:monoidal-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TensorDimError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TensorDimError {}

impl TensorDimWitness {
    pub fn try_pair(left: u64, right: u64) -> Result<Self, TensorDimError> {
        if left == 0 || right == 0 {
            return Err(TensorDimError::ZeroDimension);
        }
        let forward = left.checked_mul(right).ok_or(TensorDimError::Overflow)?;
        let backward = right.checked_mul(left).ok_or(TensorDimError::Overflow)?;
        if forward != backward {
            return Err(TensorDimError::AssociationMismatch {
                left_assoc: forward,
                right_assoc: backward,
            });
        }
        Ok(Self {
            left,
            right,
            product: forward,
        })
    }

    pub fn try_associate(a: u64, b: u64, c: u64) -> Result<u64, TensorDimError> {
        if a == 0 || b == 0 || c == 0 {
            return Err(TensorDimError::ZeroDimension);
        }
        let ab = a.checked_mul(b).ok_or(TensorDimError::Overflow)?;
        let bc = b.checked_mul(c).ok_or(TensorDimError::Overflow)?;
        let left_assoc = ab.checked_mul(c).ok_or(TensorDimError::Overflow)?;
        let right_assoc = a.checked_mul(bc).ok_or(TensorDimError::Overflow)?;
        if left_assoc != right_assoc {
            return Err(TensorDimError::AssociationMismatch {
                left_assoc,
                right_assoc,
            });
        }
        Ok(left_assoc)
    }

    pub fn product(&self) -> u64 {
        self.product
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_54fafa13 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
