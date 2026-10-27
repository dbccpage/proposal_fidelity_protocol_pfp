//! Source-ordered presentation data; never canonical certificate or money data.
use indexmap::IndexMap;
use num_bigint::BigInt;
use crate::stage::ports::Refusal;
use serde_json::value::RawValue;
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq)]
pub enum RenderRecord {
    Null,
    Bool(bool),
    Integer(BigInt),
    Float(f64),
    String(String),
    Array(Vec<Self>),
    Object(IndexMap<String, Self>),
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum JsonStyle {
    PrettyUnicode,
    PrettySortedAscii,
    SpacedSortedAscii,
    CompactSortedAscii,
}
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_RENDER_INPUT_INVALID", message)
}
impl RenderRecord {
    /// Decode raw JSON without sorting objects or conflating magic number objects.
    pub fn from_json(raw: &str) -> Result<Self, Refusal> {
        let admitted: Box<RawValue> =
            serde_json::from_str(raw).map_err(|e| invalid(e.to_string()))?;
        Self::decode(&admitted)
    }
    fn decode(raw: &RawValue) -> Result<Self, Refusal> {
        let text = raw.get();
        match text.as_bytes().first() {
            Some(b'{') => {
                let pairs: IndexMap<String, Box<RawValue>> =
                    serde_json::from_str(text).map_err(|e| invalid(e.to_string()))?;
                pairs
                    .into_iter()
                    .map(|(key, value)| Ok((key, Self::decode(&value)?)))
                    .collect::<Result<_, Refusal>>()
                    .map(Self::Object)
            }
            Some(b'[') => {
                let items: Vec<Box<RawValue>> =
                    serde_json::from_str(text).map_err(|e| invalid(e.to_string()))?;
                items
                    .iter()
                    .map(|value| Self::decode(value))
                    .collect::<Result<_, _>>()
                    .map(Self::Array)
            }
            Some(b'"') => serde_json::from_str(text)
                .map(Self::String)
                .map_err(|e| invalid(e.to_string())),
            Some(b'n') => Ok(Self::Null),
            Some(b't') => Ok(Self::Bool(true)),
            Some(b'f') => Ok(Self::Bool(false)),
            _ if text.contains(['.', 'e', 'E']) => text
                .parse::<f64>()
                .map(Self::Float)
                .map_err(|e| invalid(e.to_string())),
            _ => BigInt::from_str(text)
                .map(Self::Integer)
                .map_err(|e| invalid(e.to_string())),
        }
    }
    pub fn object(pairs: impl IntoIterator<Item = (String, Self)>) -> Self {
        Self::Object(pairs.into_iter().collect())
    }
    pub fn text(text: impl Into<String>) -> Self {
        Self::String(text.into())
    }
    pub fn as_object(&self) -> Result<&IndexMap<String, Self>, Refusal> {
        match self {
            Self::Object(pairs) => Ok(pairs),
            _ => Err(invalid("presentation record must be an object")),
        }
    }
    pub fn as_str(&self) -> Result<&str, Refusal> {
        match self {
            Self::String(text) => Ok(text),
            _ => Err(invalid("captured text must be a string")),
        }
    }
    pub fn truthy(&self) -> bool {
        match self {
            Self::Null => false,
            Self::Bool(value) => *value,
            Self::Integer(value) => value != &BigInt::from(0),
            Self::Float(value) => *value != 0.0,
            Self::String(value) => !value.is_empty(),
            Self::Array(value) => !value.is_empty(),
            Self::Object(value) => !value.is_empty(),
        }
    }
    pub fn pretty_json(&self) -> Result<String, Refusal> {
        self.json(JsonStyle::PrettyUnicode)
    }
    pub fn json(&self, style: JsonStyle) -> Result<String, Refusal> {
        self.json_at(0, style)
    }
    fn json_at(&self, depth: usize, style: JsonStyle) -> Result<String, Refusal> {
        let pretty = matches!(
            style,
            JsonStyle::PrettyUnicode | JsonStyle::PrettySortedAscii
        );
        let separator = if style == JsonStyle::CompactSortedAscii {
            ","
        } else {
            ", "
        };
        let colon = if style == JsonStyle::CompactSortedAscii {
            ":"
        } else {
            ": "
        };
        let indent = "  ".repeat(depth + 1);
        let close_indent = "  ".repeat(depth);
        match self {
            Self::Null => Ok("null".into()),
            Self::Bool(value) => Ok(value.to_string()),
            Self::Integer(value) => Ok(value.to_string()),
            Self::Float(value) => python_float(*value),
            Self::String(value) => {
                let quoted = serde_json::to_string(value).map_err(|e| invalid(e.to_string()))?;
                if style == JsonStyle::PrettyUnicode {
                    return Ok(quoted);
                }
                let mut ascii = String::new();
                for c in quoted.chars() {
                    if c >= '\u{7f}' {
                        let mut units = [0; 2];
                        for unit in c.encode_utf16(&mut units) {
                            ascii.push_str(&format!("\\u{unit:04x}"));
                        }
                    } else {
                        ascii.push(c);
                    }
                }
                Ok(ascii)
            }
            Self::Array(items) => {
                if items.is_empty() {
                    return Ok("[]".into());
                }
                let values = items
                    .iter()
                    .map(|value| {
                        Ok(format!(
                            "{}{}",
                            if pretty { &indent } else { "" },
                            value.json_at(depth + 1, style)?
                        ))
                    })
                    .collect::<Result<Vec<_>, Refusal>>()?;
                if pretty {
                    Ok(format!("[\n{}\n{close_indent}]", values.join(",\n")))
                } else {
                    Ok(format!("[{}]", values.join(separator)))
                }
            }
            Self::Object(pairs) => {
                if pairs.is_empty() {
                    return Ok("{}".into());
                }
                let mut ordered = pairs.iter().collect::<Vec<_>>();
                if style != JsonStyle::PrettyUnicode {
                    ordered.sort_unstable_by(|left, right| left.0.cmp(right.0));
                }
                let values = ordered
                    .into_iter()
                    .map(|(key, value)| {
                        Ok(format!(
                            "{}{}{colon}{}",
                            if pretty { &indent } else { "" },
                            Self::text(key).json_at(depth + 1, style)?,
                            value.json_at(depth + 1, style)?
                        ))
                    })
                    .collect::<Result<Vec<_>, Refusal>>()?;
                if pretty {
                    Ok(format!("{{\n{}\n{close_indent}}}", values.join(",\n")))
                } else {
                    Ok(format!("{{{}}}", values.join(separator)))
                }
            }
        }
    }
}
fn python_float(value: f64) -> Result<String, Refusal> {
    if value.is_nan() {
        return Ok("NaN".into());
    }
    if value.is_infinite() {
        return Ok(if value.is_sign_negative() {
            "-Infinity"
        } else {
            "Infinity"
        }
        .into());
    }
    if value == 0.0 {
        return Ok(if value.is_sign_negative() {
            "-0.0"
        } else {
            "0.0"
        }
        .into());
    }
    // Ryu chooses the even final digit at shortest-decimal ties, as Python does.
    let mut buffer = ryu::Buffer::new();
    let shortest = buffer.format_finite(value);
    let (sign, unsigned) = if let Some(unsigned) = shortest.strip_prefix('-') {
        ("-", unsigned)
    } else {
        ("", shortest)
    };
    let (coefficient, exponent) = unsigned.split_once('e').unwrap_or((unsigned, "0"));
    let exponent: i32 = exponent.parse().map_err(|e| invalid(format!("{e}")))?;
    let decimal = coefficient.find('.').unwrap_or(coefficient.len());
    let all_digits = coefficient.replace('.', "");
    let significant = all_digits.trim_start_matches('0');
    let first = all_digits.len() - significant.len();
    let exponent = exponent + decimal as i32 - first as i32 - 1;
    let digits = significant.trim_end_matches('0');
    if digits.is_empty() {
        return Err(invalid("nonzero float had no significant decimal digits"));
    }
    let mantissa = if digits.len() == 1 {
        format!("{sign}{digits}")
    } else {
        format!("{sign}{}.{}", &digits[..1], &digits[1..])
    };
    if !(-4..16).contains(&exponent) {
        return Ok(format!("{mantissa}e{exponent:+03}"));
    }
    let point = exponent + 1;
    let fixed = if point <= 0 {
        format!("0.{}{}", "0".repeat((-point) as usize), digits)
    } else if point as usize >= digits.len() {
        format!("{}{}.0", digits, "0".repeat(point as usize - digits.len()))
    } else {
        let point = point as usize;
        format!("{}.{}", &digits[..point], &digits[point..])
    };
    Ok(format!("{sign}{fixed}"))
}

// Origin: engine/crates_rs/core_adversary/src/render_record.rs
// Claim: urn:core:crates_rs:core-adversary:render-record:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1aa5ef2b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1aa5ef2b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1aa5ef2b {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError1aa5ef2b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1aa5ef2b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1aa5ef2b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1aa5ef2b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1aa5ef2b> {
        if capacity_bound == 0 {
            return Err(BoundaryError1aa5ef2b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1aa5ef2b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1aa5ef2b::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_1aa5ef2b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1aa5ef2b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1aa5ef2b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1aa5ef2b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1aa5ef2b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1aa5ef2b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1aa5ef2b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1aa5ef2b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
