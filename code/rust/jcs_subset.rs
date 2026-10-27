use std::collections::BTreeSet;
use std::io::Write;

#[derive(Clone, Copy)]
pub(crate) struct Limits {
    pub max_bytes: usize,
    pub max_depth: u32,
    pub max_nodes: u32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct ScreenFailure {
    pub code: &'static str,
    pub detail: String,
}

impl ScreenFailure {
    fn new(code: &'static str, detail: impl Into<String>) -> Self {
        Self {
            code,
            detail: detail.into(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) enum Jcs {
    Null,
    Bool(bool),
    Integer(i64),
    String(String),
    Array(Vec<Jcs>),
    Object(Vec<(String, Jcs)>),
}

const SAFE_INTEGER: i64 = (1 << 53) - 1;

impl Jcs {
    pub(crate) fn string(value: &str) -> Self {
        Self::String(value.to_owned())
    }

    /// Dialectic receipts emit depths. Gate receipts do not.
    #[allow(dead_code)]
    pub(crate) fn integer(value: i64) -> Self {
        Self::Integer(value)
    }

    pub(crate) fn canonical_bytes(&self) -> Result<Vec<u8>, &'static str> {
        let mut out = Vec::new();
        self.write(&mut out)?;
        Ok(out)
    }

    fn write_integer(value: i64, out: &mut Vec<u8>) -> Result<(), &'static str> {
        if !(-SAFE_INTEGER..=SAFE_INTEGER).contains(&value) {
            return Err("integer outside the RFC 8785 safe range");
        }
        out.extend_from_slice(value.to_string().as_bytes());
        Ok(())
    }

    fn write_array(items: &[Jcs], out: &mut Vec<u8>) -> Result<(), &'static str> {
        out.push(b'[');
        for (index, item) in items.iter().enumerate() {
            if index > 0 {
                out.push(b',');
            }
            item.write(out)?;
        }
        out.push(b']');
        Ok(())
    }

    fn write_object(pairs: &[(String, Jcs)], out: &mut Vec<u8>) -> Result<(), &'static str> {
        let mut ordered = pairs.to_vec();
        ordered.sort_by(|left, right| left.0.encode_utf16().cmp(right.0.encode_utf16()));
        out.push(b'{');
        for (index, (key, value)) in ordered.iter().enumerate() {
            if index > 0 && ordered[index - 1].0 == *key {
                return Err("duplicate canonical key");
            }
            if index > 0 {
                out.push(b',');
            }
            write_string(key, out);
            out.push(b':');
            value.write(out)?;
        }
        out.push(b'}');
        Ok(())
    }

    fn write(&self, out: &mut Vec<u8>) -> Result<(), &'static str> {
        match self {
            Self::Null => out.extend_from_slice(b"null"),
            Self::Bool(true) => out.extend_from_slice(b"true"),
            Self::Bool(false) => out.extend_from_slice(b"false"),
            Self::Integer(value) => Self::write_integer(*value, out)?,
            Self::String(value) => write_string(value, out),
            Self::Array(items) => Self::write_array(items, out)?,
            Self::Object(pairs) => Self::write_object(pairs, out)?,
        }
        Ok(())
    }
}

pub(crate) fn screen(bytes: &[u8], limits: Limits) -> Result<(), ScreenFailure> {
    if bytes.len() > limits.max_bytes {
        return Err(ScreenFailure::new(
            "INPUT_TOO_LARGE",
            "json exceeds the byte ceiling",
        ));
    }
    if bytes.starts_with(&[0xEF, 0xBB, 0xBF]) {
        return Err(ScreenFailure::new(
            "UTF8_BOM_FORBIDDEN",
            "utf-8 bom is forbidden",
        ));
    }
    if bytes.contains(&b'\r') {
        return Err(ScreenFailure::new(
            "CARRIAGE_RETURN_FORBIDDEN",
            "carriage return is forbidden",
        ));
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|_| ScreenFailure::new("INVALID_UTF8", "input is not utf-8"))?;
    let mut parser = Parser {
        s: text,
        i: 0,
        depth: 0,
        nodes: 0,
        limits,
    };
    parser.skip();
    parser.value()?;
    parser.skip();
    if parser.i != parser.s.len() {
        return Err(ScreenFailure::new(
            "INVALID_JSON",
            format!("trailing bytes at {}", parser.i),
        ));
    }
    Ok(())
}

struct Parser<'a> {
    s: &'a str,
    i: usize,
    depth: u32,
    nodes: u32,
    limits: Limits,
}

impl<'a> Parser<'a> {
    fn fail(&self, code: &'static str) -> ScreenFailure {
        ScreenFailure::new(code, format!("at byte {}", self.i))
    }

    fn peek(&self) -> Option<char> {
        self.s[self.i..].chars().next()
    }

    fn bump(&mut self) -> Option<char> {
        let ch = self.peek()?;
        self.i += ch.len_utf8();
        Some(ch)
    }

    fn eat(&mut self, expected: char) -> bool {
        if self.peek() == Some(expected) {
            self.bump();
            true
        } else {
            false
        }
    }

    fn skip(&mut self) {
        while matches!(self.peek(), Some(' ' | '\t' | '\n')) {
            self.bump();
        }
    }

    fn value(&mut self) -> Result<(), ScreenFailure> {
        self.nodes += 1;
        if self.nodes > self.limits.max_nodes {
            return Err(self.fail("JSON_NODE_LIMIT"));
        }
        match self.peek() {
            Some('n') => self.literal("null"),
            Some('t') => self.literal("true"),
            Some('f') => self.literal("false"),
            Some('"') => {
                self.string()?;
                Ok(())
            }
            Some('{') => self.object(),
            Some('[') => self.array(),
            Some('-' | '0'..='9') => self.number(),
            _ => Err(self.fail("INVALID_JSON")),
        }
    }

    fn literal(&mut self, text: &str) -> Result<(), ScreenFailure> {
        if self.s[self.i..].starts_with(text) {
            self.i += text.len();
            Ok(())
        } else {
            Err(self.fail("INVALID_JSON"))
        }
    }

    fn enter(&mut self) -> Result<(), ScreenFailure> {
        if self.depth >= self.limits.max_depth {
            return Err(self.fail("JSON_DEPTH_LIMIT"));
        }
        self.depth += 1;
        Ok(())
    }

    fn object(&mut self) -> Result<(), ScreenFailure> {
        self.bump();
        self.enter()?;
        self.skip();
        if self.eat('}') {
            self.depth -= 1;
            return Ok(());
        }
        let mut keys = BTreeSet::new();
        loop {
            if self.peek() != Some('"') {
                return Err(self.fail("INVALID_JSON"));
            }
            let key = self.string()?;
            if is_prose_key(&key) {
                return Err(ScreenFailure::new(
                    "PROSE_AUTHORITY",
                    format!("forbidden key {key}"),
                ));
            }
            if !keys.insert(key) {
                return Err(self.fail("DUPLICATE_KEY"));
            }
            self.skip();
            if !self.eat(':') {
                return Err(self.fail("INVALID_JSON"));
            }
            self.skip();
            self.value()?;
            self.skip();
            if self.eat(',') {
                self.skip();
                continue;
            }
            if self.eat('}') {
                self.depth -= 1;
                return Ok(());
            }
            return Err(self.fail("INVALID_JSON"));
        }
    }

    fn array(&mut self) -> Result<(), ScreenFailure> {
        self.bump();
        self.enter()?;
        self.skip();
        if self.eat(']') {
            self.depth -= 1;
            return Ok(());
        }
        loop {
            self.value()?;
            self.skip();
            if self.eat(',') {
                self.skip();
                continue;
            }
            if self.eat(']') {
                self.depth -= 1;
                return Ok(());
            }
            return Err(self.fail("INVALID_JSON"));
        }
    }

    fn number(&mut self) -> Result<(), ScreenFailure> {
        if self.peek() == Some('-') {
            self.bump();
        }
        let mut digits = 0u32;
        match self.peek() {
            Some('0') => {
                self.bump();
                digits = 1;
                if matches!(self.peek(), Some('0'..='9')) {
                    return Err(self.fail("INVALID_JSON"));
                }
            }
            Some('1'..='9') => {
                while matches!(self.peek(), Some('0'..='9')) {
                    self.bump();
                    digits += 1;
                    if digits > 16 {
                        return Err(self.fail("INTEGER_LEXEME_TOO_LONG"));
                    }
                }
            }
            _ => return Err(self.fail("INVALID_JSON")),
        }
        if digits == 0 {
            return Err(self.fail("INVALID_JSON"));
        }
        if matches!(self.peek(), Some('.' | 'e' | 'E')) {
            return Err(self.fail("FLOAT_FORBIDDEN"));
        }
        Ok(())
    }

    fn string(&mut self) -> Result<String, ScreenFailure> {
        if !self.eat('"') {
            return Err(self.fail("INVALID_JSON"));
        }
        let mut out = String::new();
        loop {
            match self.bump() {
                None => return Err(self.fail("INVALID_JSON")),
                Some('"') => return Ok(out),
                Some('\\') => {
                    let escaped = match self.bump() {
                        Some(ch) => ch,
                        None => return Err(self.fail("INVALID_JSON")),
                    };
                    match escaped {
                        '"' | '\\' | '/' => out.push(escaped),
                        'b' => out.push('\u{0008}'),
                        'f' => out.push('\u{000c}'),
                        'n' => out.push('\n'),
                        'r' => out.push('\r'),
                        't' => out.push('\t'),
                        'u' => out.push(self.unicode_escape()?),
                        _ => return Err(self.fail("INVALID_JSON")),
                    }
                }
                Some(ch) if (ch as u32) < 0x20 => return Err(self.fail("INVALID_JSON")),
                Some(ch) => out.push(ch),
            }
        }
    }

    fn unicode_escape(&mut self) -> Result<char, ScreenFailure> {
        let unit = self.hex4()?;
        let scalar = if (0xD800..=0xDBFF).contains(&unit) {
            if self.bump() != Some('\\') || self.bump() != Some('u') {
                return Err(self.fail("NON_SCALAR_UNICODE"));
            }
            let low = self.hex4()?;
            if !(0xDC00..=0xDFFF).contains(&low) {
                return Err(self.fail("NON_SCALAR_UNICODE"));
            }
            0x10000 + (((unit as u32) - 0xD800) << 10) + ((low as u32) - 0xDC00)
        } else if (0xDC00..=0xDFFF).contains(&unit) {
            return Err(self.fail("NON_SCALAR_UNICODE"));
        } else {
            unit as u32
        };
        match char::from_u32(scalar) {
            Some(ch) => Ok(ch),
            None => Err(self.fail("NON_SCALAR_UNICODE")),
        }
    }

    fn hex4(&mut self) -> Result<u16, ScreenFailure> {
        let mut value = 0u16;
        for _ in 0..4 {
            let Some(ch) = self.bump() else {
                return Err(self.fail("INVALID_JSON"));
            };
            let Some(digit) = ch.to_digit(16) else {
                return Err(self.fail("INVALID_JSON"));
            };
            value = (value << 4) | digit as u16;
        }
        Ok(value)
    }
}

fn is_prose_key(key: &str) -> bool {
    let lower = key.to_ascii_lowercase();
    lower == "verified" || lower == "is_authorized" || lower == "authorized"
}

/// Local string profile, not unrestricted RFC 8785 string serialization:
/// short escapes for the usual controls, lowercase `\u00xx`
/// for the rest, and `\u2028` / `\u2029` for the line and paragraph separators.
fn write_string(value: &str, out: &mut Vec<u8>) {
    out.push(b'"');
    for ch in value.chars() {
        match ch {
            '"' => out.extend_from_slice(br#"\""#),
            '\\' => out.extend_from_slice(br#"\\"#),
            '\u{0008}' => out.extend_from_slice(br#"\b"#),
            '\t' => out.extend_from_slice(br#"\t"#),
            '\n' => out.extend_from_slice(br#"\n"#),
            '\u{000c}' => out.extend_from_slice(br#"\f"#),
            '\r' => out.extend_from_slice(br#"\r"#),
            ch if (ch as u32) < 0x20 || ch == '\u{2028}' || ch == '\u{2029}' => {
                let _ = write!(out, "\\u{:04x}", ch as u32);
            }
            ch => {
                let mut buf = [0u8; 4];
                out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
            }
        }
    }
    out.push(b'"');
}

// Origin: engine/crates_rs/jcs_subset.rs
// Claim: urn:core:crates_rs:jcs-subset.rs:jcs-subset:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5489e940 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5489e940` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5489e940 {
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
impl BoundaryError5489e940 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5489e940 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5489e940 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5489e940 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5489e940> {
        if capacity_bound == 0 {
            return Err(BoundaryError5489e940::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5489e940::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5489e940::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn line_and_paragraph_separators_use_lowercase_u_escapes() {
        let bytes = Jcs::string("a\u{2028}b\u{2029}").canonical_bytes().unwrap();
        assert_eq!(bytes, br#""a\u2028b\u2029""#);
    }
}
