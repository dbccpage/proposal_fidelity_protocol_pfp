//! How the families read a reply: a list of exact integers, an object, an integer per name.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-reading:v1
//!
//! A reading either gives the value or says what was wrong, so a walk can stop the run as a
//! malformed candidate with the reason.

use num_bigint::BigInt;

use crate::datum::Datum;

use super::{require, Stop};

/// A list of exact integers. A decimal, a boolean and text are not integers.
pub fn integers(listed: &Datum) -> Option<Vec<BigInt>> {
    listed
        .as_list()?
        .iter()
        .map(|entry| entry.as_int().cloned())
        .collect()
}

/// This reply, when it is an object; else the run stops as malformed.
pub fn object<'d>(reply: &'d Datum, stage: &str) -> Result<&'d Datum, Stop> {
    require(reply.is_map(), &format!("{stage} reply must be an object"))?;
    Ok(reply)
}

/// The list of exact integers under `key` in a reply; else the run stops as malformed.
pub fn integers_under(reply: &Datum, key: &str) -> Result<Vec<BigInt>, Stop> {
    reply
        .get(key)
        .and_then(integers)
        .ok_or_else(|| Stop::Malformed(format!("{key} must be a list of exact integers")))
}

/// The sum of the squares of a list.
pub fn squared_norm(values: &[BigInt]) -> BigInt {
    values.iter().map(|value| value * value).sum()
}
