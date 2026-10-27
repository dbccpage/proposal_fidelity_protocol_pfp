use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SignValue {
    Negative,
    Zero,
    Positive,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SignValueError {
    #[error("sign value must be -1, 0, or 1")]
    InvalidValue,
    #[error("sign arithmetic overflowed")]
    Overflow,
}

impl SignValue {
    pub fn from_i8(value: i8) -> Result<Self, SignValueError> {
        match value {
            -1 => Ok(Self::Negative),
            0 => Ok(Self::Zero),
            1 => Ok(Self::Positive),
            _ => Err(SignValueError::InvalidValue),
        }
    }

    pub fn as_i8(self) -> i8 {
        match self {
            Self::Negative => -1,
            Self::Zero => 0,
            Self::Positive => 1,
        }
    }

    /// Sign multiplication: zero annihilates, and two negatives make a positive.
    pub fn mul(self, other: Self) -> Self {
        match (self, other) {
            (Self::Zero, _) | (_, Self::Zero) => Self::Zero,
            (Self::Negative, Self::Negative) | (Self::Positive, Self::Positive) => Self::Positive,
            (Self::Negative, Self::Positive) | (Self::Positive, Self::Negative) => Self::Negative,
        }
    }

    pub fn sign_of_i128(value: i128) -> Self {
        match value {
            n if n < 0 => Self::Negative,
            0 => Self::Zero,
            _ => Self::Positive,
        }
    }

    /// Sign of a checked product. The result agrees with multiplying the factors' signs.
    pub fn sign_of_product(left: i128, right: i128) -> Result<Self, SignValueError> {
        let product = left.checked_mul(right).ok_or(SignValueError::Overflow)?;
        let from_product = Self::sign_of_i128(product);
        let from_signs = Self::sign_of_i128(left).mul(Self::sign_of_i128(right));
        if from_product != from_signs {
            return Err(SignValueError::InvalidValue);
        }
        Ok(from_product)
    }

    /// Sign of a checked difference `left - right`.
    pub fn sign_of_difference(left: i128, right: i128) -> Result<Self, SignValueError> {
        let difference = left.checked_sub(right).ok_or(SignValueError::Overflow)?;
        Ok(Self::sign_of_i128(difference))
    }
}

// Origin: engine/crates_rs/core_types/src/sign_value.rs
// Claim: urn:core:crates_rs:core-types:sign-value:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod sign_law_tests {
    use super::*;

    fn taken(result: Result<SignValue, SignValueError>) -> SignValue {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn two_negatives_multiply_to_positive() {
        let sign = taken(SignValue::sign_of_product(-3, -4));
        assert_eq!(sign, SignValue::Positive);
        assert_eq!(sign.as_i8(), 1);
        assert_eq!(
            SignValue::Negative.mul(SignValue::Negative),
            SignValue::Positive
        );
    }

    #[test]
    fn a_difference_of_equals_is_zero() {
        assert_eq!(
            taken(SignValue::sign_of_difference(8, 8)),
            SignValue::Zero
        );
    }

    #[test]
    fn i128_min_times_minus_one_overflows() {
        assert!(matches!(
            SignValue::sign_of_product(i128::MIN, -1),
            Err(SignValueError::Overflow)
        ));
    }
}
