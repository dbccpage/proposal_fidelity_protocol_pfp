//! Exact JSON: the values a workflow host reads and writes, with nothing rounded.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:datum:v1
//!
//! A [`Datum`] is read from JSON text. An integer is read from its digits, so it is unbounded. A
//! number written with a fraction or an exponent is kept as written and is never an integer here,
//! whatever its value. An object with the same key twice is refused, and so is nesting deeper
//! than [`MAX_DEPTH`].
//!
//! [`Datum::canonical`] writes the one text a value has: keys in code point order, no spaces,
//! text as it is except the characters JSON must escape.

use std::collections::BTreeMap;
use std::fmt;

use num_bigint::BigInt;
use serde::de::{Deserializer, MapAccess, Visitor};
use serde::Deserialize;
use serde_json::value::RawValue;
use serde_json::Value as Json;

use crate::Refusal;

/// The deepest nesting of lists and objects that is read.
pub const MAX_DEPTH: usize = 64;

/// One exact JSON value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Datum {
    Null,
    Bool(bool),
    Int(BigInt),
    /// A number with a fraction or an exponent, kept as written. No arithmetic reads it.
    Decimal(String),
    Text(String),
    List(Vec<Datum>),
    Map(BTreeMap<String, Datum>),
}

/// The entries of one JSON object in document order, each value still as text.
struct Entries<'a>(Vec<(String, &'a RawValue)>);

struct EntriesVisitor;

impl<'de> Visitor<'de> for EntriesVisitor {
    type Value = Entries<'de>;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("a JSON object")
    }

    fn visit_map<A: MapAccess<'de>>(self, mut entries: A) -> Result<Entries<'de>, A::Error> {
        let mut list = Vec::new();
        while let Some(entry) = entries.next_entry::<String, &'de RawValue>()? {
            list.push(entry);
        }
        Ok(Entries(list))
    }
}

impl<'de> Deserialize<'de> for Entries<'de> {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        deserializer.deserialize_map(EntriesVisitor)
    }
}

fn bad(message: impl Into<String>) -> Refusal {
    Refusal::new("BAD_JSON", message)
}

fn decode<'a, T: Deserialize<'a>>(text: &'a str) -> Result<T, Refusal> {
    serde_json::from_str(text).map_err(|error| bad(error.to_string()))
}

/// The integer a JSON number denotes, if it is written as one: an optional minus, then digits.
fn integer(text: &str) -> Option<BigInt> {
    let digits = text.strip_prefix('-').unwrap_or(text);
    if !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

fn read_map(text: &str, depth: usize) -> Result<Datum, Refusal> {
    let mut map = BTreeMap::new();
    for (key, value) in decode::<Entries>(text)?.0 {
        let value = read(value.get(), depth)?;
        if map.insert(key.clone(), value).is_some() {
            return Err(bad(format!("the key {key} appears twice in one object")));
        }
    }
    Ok(Datum::Map(map))
}

fn read(text: &str, depth: usize) -> Result<Datum, Refusal> {
    if depth > MAX_DEPTH {
        return Err(bad(format!("nesting deeper than {MAX_DEPTH}")));
    }
    match text.as_bytes().first() {
        Some(b'n') => Ok(Datum::Null),
        Some(b't') => Ok(Datum::Bool(true)),
        Some(b'f') => Ok(Datum::Bool(false)),
        Some(b'"') => Ok(Datum::Text(decode(text)?)),
        Some(b'[') => decode::<Vec<&RawValue>>(text)?
            .into_iter()
            .map(|item| read(item.get(), depth + 1))
            .collect::<Result<_, _>>()
            .map(Datum::List),
        Some(b'{') => read_map(text, depth + 1),
        _ => Ok(integer(text).map_or_else(|| Datum::Decimal(text.to_owned()), Datum::Int)),
    }
}

fn write_text(text: &str, out: &mut String) {
    out.push('"');
    for letter in text.chars() {
        match letter {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            control if u32::from(control) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", u32::from(control)));
            }
            other => out.push(other),
        }
    }
    out.push('"');
}

impl Datum {
    /// Read one JSON value from text.
    pub fn parse(text: &str) -> Result<Self, Refusal> {
        read(decode::<&RawValue>(text)?.get(), 0)
    }

    /// An object from its entries; a later entry replaces an earlier one with the same key.
    pub fn map<const N: usize>(entries: [(&str, Datum); N]) -> Self {
        Datum::Map(
            entries
                .into_iter()
                .map(|(key, value)| (key.to_owned(), value))
                .collect(),
        )
    }

    pub fn text(text: impl Into<String>) -> Self {
        Datum::Text(text.into())
    }

    /// The value under `key` when this is an object that has it.
    pub fn get(&self, key: &str) -> Option<&Datum> {
        match self {
            Datum::Map(map) => map.get(key),
            _ => None,
        }
    }

    pub fn as_list(&self) -> Option<&[Datum]> {
        match self {
            Datum::List(items) => Some(items),
            _ => None,
        }
    }

    pub fn as_int(&self) -> Option<&BigInt> {
        match self {
            Datum::Int(number) => Some(number),
            _ => None,
        }
    }

    pub fn as_text(&self) -> Option<&str> {
        match self {
            Datum::Text(text) => Some(text),
            _ => None,
        }
    }

    pub fn is_map(&self) -> bool {
        matches!(self, Datum::Map(_))
    }

    /// The count or position this value denotes: an integer from zero up to the machine's limit.
    pub fn as_count(&self) -> Option<usize> {
        self.as_int()
            .and_then(|number| usize::try_from(number).ok())
    }

    fn write(&self, out: &mut String) {
        match self {
            Datum::Null => out.push_str("null"),
            Datum::Bool(flag) => out.push_str(if *flag { "true" } else { "false" }),
            Datum::Int(number) => out.push_str(&number.to_string()),
            Datum::Decimal(written) => out.push_str(written),
            Datum::Text(text) => write_text(text, out),
            Datum::List(items) => {
                out.push('[');
                for (index, item) in items.iter().enumerate() {
                    if index > 0 {
                        out.push(',');
                    }
                    item.write(out);
                }
                out.push(']');
            }
            Datum::Map(map) => {
                out.push('{');
                for (index, (key, value)) in map.iter().enumerate() {
                    if index > 0 {
                        out.push(',');
                    }
                    write_text(key, out);
                    out.push(':');
                    value.write(out);
                }
                out.push('}');
            }
        }
    }

    /// The one text of this value: sorted keys, no spaces, only the escapes JSON requires.
    pub fn canonical(&self) -> String {
        let mut out = String::new();
        self.write(&mut out);
        out
    }

    /// This value for a host outcome. An integer outside 64 bits and a decimal go out as text,
    /// so no reader rounds them.
    pub fn to_json(&self) -> Json {
        match self {
            Datum::Null => Json::Null,
            Datum::Bool(flag) => Json::Bool(*flag),
            Datum::Int(number) => i64::try_from(number)
                .map(Json::from)
                .or_else(|_| u64::try_from(number).map(Json::from))
                .unwrap_or_else(|_| Json::String(number.to_string())),
            Datum::Decimal(written) => Json::String(written.clone()),
            Datum::Text(text) => Json::String(text.clone()),
            Datum::List(items) => Json::Array(items.iter().map(Datum::to_json).collect()),
            Datum::Map(map) => Json::Object(
                map.iter()
                    .map(|(key, value)| (key.clone(), value.to_json()))
                    .collect(),
            ),
        }
    }
}

impl From<BigInt> for Datum {
    fn from(number: BigInt) -> Self {
        Datum::Int(number)
    }
}

impl From<usize> for Datum {
    fn from(number: usize) -> Self {
        Datum::Int(BigInt::from(number))
    }
}

impl From<i64> for Datum {
    fn from(number: i64) -> Self {
        Datum::Int(BigInt::from(number))
    }
}

impl From<&str> for Datum {
    fn from(text: &str) -> Self {
        Datum::Text(text.to_owned())
    }
}

impl<T: Into<Datum>> From<Vec<T>> for Datum {
    fn from(items: Vec<T>) -> Self {
        Datum::List(items.into_iter().map(Into::into).collect())
    }
}
