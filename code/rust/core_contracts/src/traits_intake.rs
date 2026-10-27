use super::identity::{ContractBound, NamedComponent};
use crate::kinds::BaseType;

/// Parses or intakes raw material into typed structure.
///
/// A constructor may reject malformed input, but it does not certify semantic
/// correctness or evaluate admissibility. Validation belongs to a Validator boundary.
pub trait Constructor<Raw, T: BaseType>: NamedComponent + ContractBound {
    type Error;

    fn construct(&self, raw: Raw) -> Result<T, Self::Error>;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConstructorError {
    ParseError(String),
    SchemaMismatch,
    MissingRequiredField(&'static str),
    InvalidInvariant(String),
    NonFiniteNumericInput,
    UnsupportedRepresentation,
}

// Origin: engine/crates_rs/core_contracts/src/traits_intake.rs
// Claim: urn:core:crates_rs:core-contracts:traits-intake:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConstructorError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConstructorError {}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactIntakeRatio { numer: i64, denom: i64 }

fn intake_gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

fn parse_intake_integer(text: &str) -> Result<i64, ConstructorError> {
    if text.is_empty() {
        return Err(ConstructorError::InvalidInvariant("empty integer".into()));
    }
    let (negative, digits) = if let Some(rest) = text.strip_prefix('-') {
        (true, rest)
    } else {
        (false, text)
    };
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ConstructorError::ParseError(text.into()));
    }
    let mut value = 0i128;
    for byte in digits.bytes() {
        value = value.checked_mul(10).ok_or_else(|| ConstructorError::ParseError(text.into()))?
            .checked_add(i128::from(byte - b'0')).ok_or_else(|| ConstructorError::ParseError(text.into()))?;
    }
    if negative {
        value = value.checked_neg().ok_or_else(|| ConstructorError::ParseError(text.into()))?;
    }
    i64::try_from(value).map_err(|_| ConstructorError::ParseError(text.into()))
}

impl ExactIntakeRatio {
    fn split_raw_token(raw: &str) -> Result<(&str, &str), ConstructorError> {
        if raw.is_empty() {
            return Err(ConstructorError::MissingRequiredField("raw"));
        }
        if matches!(raw, "true" | "false" | "True" | "False") || raw.contains('.') || raw.contains('e') || raw.contains('E') {
            return Err(ConstructorError::NonFiniteNumericInput);
        }
        if raw.bytes().filter(|byte| *byte == b'/').count() > 1 {
            return Err(ConstructorError::InvalidInvariant("more than one slash".into()));
        }
        Ok(match raw.split_once('/') {
            Some((numer_text, denom_text)) => (numer_text, denom_text),
            None => (raw, "1"),
        })
    }

    fn normalize_sign(mut numer: i64, mut denom: i64) -> Result<(i64, i64), ConstructorError> {
        if denom == 0 {
            return Err(ConstructorError::InvalidInvariant("zero denominator".into()));
        }
        if denom < 0 {
            numer = numer.checked_neg().ok_or_else(|| ConstructorError::InvalidInvariant("sign".into()))?;
            denom = denom.checked_neg().ok_or_else(|| ConstructorError::InvalidInvariant("sign".into()))?;
        }
        Ok((numer, denom))
    }

    /// Parse an integer or `numer/denom` token. Scientific text and booleans are refused.
    pub fn parse(raw: &str) -> Result<Self, ConstructorError> {
        let (numer_text, denom_text) = Self::split_raw_token(raw)?;
        let (numer, denom) = Self::normalize_sign(
            parse_intake_integer(numer_text)?,
            parse_intake_integer(denom_text)?,
        )?;
        let g = i64::try_from(intake_gcd(numer.unsigned_abs(), denom.unsigned_abs()))
            .map_err(|_| ConstructorError::InvalidInvariant("gcd".into()))?;
        let numer = numer.checked_div(g).ok_or_else(|| ConstructorError::InvalidInvariant("reduce".into()))?;
        let denom = denom.checked_div(g).ok_or_else(|| ConstructorError::InvalidInvariant("reduce".into()))?;
        let out = Self { numer, denom };
        Ok(out)
    }

    pub fn ratio(&self) -> (i64, i64) { (self.numer, self.denom) }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod intake_ratio_checks {
    use super::*;

    #[test]
    fn two_over_four_reduces_and_a_bare_zero_is_zero_over_one() {
        assert!(matches!(ExactIntakeRatio::parse("2/4"), Ok(r) if r.ratio() == (1, 2)));
        assert!(matches!(ExactIntakeRatio::parse("0"), Ok(r) if r.ratio() == (0, 1)));
        assert!(matches!(ExactIntakeRatio::parse("-4/6"), Ok(r) if r.ratio() == (-2, 3)));
    }

    #[test]
    fn nonfinite_text_and_a_zero_denominator_are_refused() {
        assert!(matches!(ExactIntakeRatio::parse(""), Err(ConstructorError::MissingRequiredField("raw"))));
        assert!(matches!(ExactIntakeRatio::parse("1.5"), Err(ConstructorError::NonFiniteNumericInput)));
        assert!(matches!(ExactIntakeRatio::parse("true"), Err(ConstructorError::NonFiniteNumericInput)));
        assert!(matches!(ExactIntakeRatio::parse("1/0"), Err(ConstructorError::InvalidInvariant(_))));
    }
}
