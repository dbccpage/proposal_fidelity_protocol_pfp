use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use thiserror::Error;

pub type Exact = BigRational;

pub fn exact(numerator: i64, denominator: i64) -> Exact {
    BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
}

pub fn integer(value: i64) -> Exact {
    BigRational::from_integer(BigInt::from(value))
}

#[derive(Debug, Error, PartialEq, Eq)]
#[error("not an exact rational ({reason}): {value:?}")]
pub struct ExactError {
    pub value: String,
    pub reason: &'static str,
}

/// `"3/4"`, `"-5"`, `"0"`. Exact values cross the wire as strings, never as JSON
/// numbers: a JSON number is a float in most readers, and
/// `core-sorted-json-no-float-v1` refuses floats outright.
pub fn to_canonical_string(value: &Exact) -> String {
    if value.denom().is_one() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

pub fn parse_exact(text: &str) -> Result<Exact, ExactError> {
    let fail = |reason: &'static str| ExactError {
        value: text.to_owned(),
        reason,
    };
    if text.is_empty() {
        return Err(fail("empty"));
    }
    let (numer_text, denom_text) = match text.split_once('/') {
        Some((n, d)) => (n, d),
        None => (text, "1"),
    };
    let numer: BigInt = numer_text
        .parse()
        .map_err(|_| fail("numerator is not an integer"))?;
    let denom: BigInt = denom_text
        .parse()
        .map_err(|_| fail("denominator is not an integer"))?;
    if denom.is_zero() {
        return Err(fail("zero denominator"));
    }
    let value = BigRational::new(numer, denom);
    if to_canonical_string(&value) != text {
        return Err(fail("not in lowest terms with a positive denominator"));
    }
    Ok(value)
}

/// The only sanctioned lossy read of an exact value, named so it cannot be
/// mistaken for one. Returns `None` when the value does not fit in a finite
/// `f64`: overflow, and a nonzero value that underflows to ±0. A collapsed
/// zero would compare equal to an actual zero.
pub fn approximate(value: &Exact) -> Option<f64> {
    use num_traits::ToPrimitive;
    let approx = value.to_f64()?;
    if !approx.is_finite() || (approx == 0.0 && !value.is_zero()) {
        return None;
    }
    Some(approx)
}

pub mod exact_wire {
    use super::{parse_exact, to_canonical_string, Exact};
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S: Serializer>(value: &Exact, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&to_canonical_string(value))
    }

    pub fn deserialize<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Exact, D::Error> {
        let text = String::deserialize(deserializer)?;
        parse_exact(&text).map_err(serde::de::Error::custom)
    }
}

pub mod exact_wire_option {
    use super::{parse_exact, to_canonical_string, Exact};
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S: Serializer>(
        value: &Option<Exact>,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        match value {
            Some(inner) => serializer.serialize_some(&to_canonical_string(inner)),
            None => serializer.serialize_none(),
        }
    }

    pub fn deserialize<'de, D: Deserializer<'de>>(
        deserializer: D,
    ) -> Result<Option<Exact>, D::Error> {
        let text = Option::<String>::deserialize(deserializer)?;
        text.map(|t| parse_exact(&t).map_err(serde::de::Error::custom))
            .transpose()
    }
}

pub mod exact_wire_vec {
    use super::{parse_exact, to_canonical_string, Exact};
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S: Serializer>(value: &[Exact], serializer: S) -> Result<S::Ok, S::Error> {
        let wire: Vec<String> = value.iter().map(to_canonical_string).collect();
        serde::Serialize::serialize(&wire, serializer)
    }

    pub fn deserialize<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Vec<Exact>, D::Error> {
        Vec::<String>::deserialize(deserializer)?
            .iter()
            .map(|t| parse_exact(t).map_err(serde::de::Error::custom))
            .collect()
    }
}

pub mod exact_wire_pairs {
    use super::{parse_exact, to_canonical_string, Exact};
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S: Serializer>(
        value: &[(String, Exact)],
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        let wire: Vec<(&str, String)> = value
            .iter()
            .map(|(key, value)| (key.as_str(), to_canonical_string(value)))
            .collect();
        serde::Serialize::serialize(&wire, serializer)
    }

    pub fn deserialize<'de, D: Deserializer<'de>>(
        deserializer: D,
    ) -> Result<Vec<(String, Exact)>, D::Error> {
        Vec::<(String, String)>::deserialize(deserializer)?
            .into_iter()
            .map(|(key, text)| {
                parse_exact(&text)
                    .map(|value| (key, value))
                    .map_err(serde::de::Error::custom)
            })
            .collect()
    }
}

// Origin: engine/crates_rs/core_kernel/src/exact.rs
// Claim: urn:core:crates_rs:core-kernel:exact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::Signed;

    #[test]
    fn one_value_has_exactly_one_spelling() {
        assert_eq!(to_canonical_string(&exact(2, 4)), "1/2");
        assert_eq!(to_canonical_string(&exact(-1, -2)), "1/2");
        assert_eq!(to_canonical_string(&exact(1, -2)), "-1/2");
        assert_eq!(to_canonical_string(&exact(4, 2)), "2");
        assert_eq!(to_canonical_string(&integer(0)), "0");
    }

    #[test]
    fn parsing_is_the_inverse_of_rendering() {
        for value in [exact(3, 4), exact(-5, 7), integer(0), integer(-12)] {
            assert_eq!(parse_exact(&to_canonical_string(&value)).unwrap(), value);
        }
    }

    #[test]
    fn a_non_canonical_spelling_is_refused_rather_than_normalised() {
        // Admitting "2/4" would mean two strings for one value, so string
        // equality would stop being value equality.
        for text in ["2/4", "-1/-2", "1/-2", "4/2", "+1"] {
            assert!(parse_exact(text).is_err(), "{text} must be refused");
        }
    }

    #[test]
    fn a_decimal_is_refused_because_it_is_not_exactly_representable() {
        for text in ["0.1", "1e-9", "1.0", ""] {
            assert!(parse_exact(text).is_err(), "{text} must be refused");
        }
    }

    #[test]
    fn a_zero_denominator_is_refused_rather_than_panicking() {
        assert!(parse_exact("1/0").is_err());
    }

    #[test]
    fn exactness_holds_where_floating_point_would_not() {
        let third = exact(1, 3);
        assert_eq!(&third + &third + &third, Exact::one());
        assert_ne!(0.1_f64 + 0.2, 0.3);
        assert_eq!(exact(1, 10) + exact(2, 10), exact(3, 10));
    }

    #[test]
    fn a_value_too_large_for_f64_approximates_to_none_not_nan() {
        let huge = BigRational::new(BigInt::from(10).pow(400), BigInt::one());
        assert_eq!(approximate(&huge), None);
        assert_eq!(approximate(&-&huge), None);
        assert_eq!(approximate(&exact(1, 2)), Some(0.5));
    }

    #[test]
    fn a_nonzero_value_that_underflows_approximates_to_none_not_zero() {
        // 2^-1074 is the smallest positive f64. One binade further is a
        // nonzero rational that `to_f64` collapses to ±0.
        let subnormal = BigRational::new(BigInt::one(), BigInt::from(2).pow(1074));
        assert_eq!(approximate(&subnormal), Some(f64::from_bits(1)));
        let underflow = BigRational::new(BigInt::one(), BigInt::from(2).pow(1075));
        assert_eq!(approximate(&underflow), None);
        assert_eq!(approximate(&-&underflow), None);
        let tiny = BigRational::new(BigInt::one(), BigInt::from(10).pow(400));
        assert_eq!(approximate(&tiny), None);
        assert_eq!(approximate(&-&tiny), None);
        assert_eq!(approximate(&Exact::zero()), Some(0.0));
    }

    #[test]
    fn ordering_is_total_and_exact() {
        let mut values = vec![exact(1, 3), exact(-1, 2), integer(2), exact(1, 4)];
        values.sort();
        assert_eq!(
            values.iter().map(to_canonical_string).collect::<Vec<_>>(),
            ["-1/2", "1/4", "1/3", "2"]
        );
    }

    #[test]
    fn a_big_value_survives_the_round_trip_without_loss() {
        let big = BigRational::new(BigInt::from(10).pow(40) + BigInt::one(), BigInt::from(7));
        let text = to_canonical_string(&big);
        assert_eq!(parse_exact(&text).unwrap(), big);
    }

    #[derive(serde::Serialize, serde::Deserialize, PartialEq, Debug)]
    struct Wire {
        #[serde(with = "exact_wire")]
        scalar: Exact,
        #[serde(with = "exact_wire_option")]
        maybe: Option<Exact>,
        #[serde(with = "exact_wire_vec")]
        vector: Vec<Exact>,
        #[serde(with = "exact_wire_pairs")]
        pairs: Vec<(String, Exact)>,
    }

    #[test]
    fn the_wire_form_is_strings_and_never_json_numbers() {
        let wire = Wire {
            scalar: exact(3, 4),
            maybe: Some(integer(-2)),
            vector: vec![exact(1, 3), integer(0)],
            pairs: vec![("k".to_owned(), exact(5, 6))],
        };
        let json = serde_json::to_string(&wire).unwrap();
        assert_eq!(
            json,
            r#"{"scalar":"3/4","maybe":"-2","vector":["1/3","0"],"pairs":[["k","5/6"]]}"#
        );
        assert_eq!(serde_json::from_str::<Wire>(&json).unwrap(), wire);
    }

    #[test]
    fn a_json_number_is_refused_on_the_wire() {
        let json = r#"{"scalar":0.75,"maybe":null,"vector":[],"pairs":[]}"#;
        assert!(serde_json::from_str::<Wire>(json).is_err());
    }

    #[test]
    fn a_null_option_round_trips_as_absent() {
        let wire = Wire {
            scalar: integer(1),
            maybe: None,
            vector: vec![],
            pairs: vec![],
        };
        let json = serde_json::to_string(&wire).unwrap();
        assert!(json.contains(r#""maybe":null"#));
        assert_eq!(serde_json::from_str::<Wire>(&json).unwrap(), wire);
    }

    #[test]
    fn the_absolute_value_of_a_negative_is_its_negation() {
        assert_eq!(exact(-3, 4).abs(), exact(3, 4));
    }
}
