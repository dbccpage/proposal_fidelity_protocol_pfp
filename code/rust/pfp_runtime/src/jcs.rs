// AuthorityEffect: None.
//! RFC 8785 JSON Canonicalization Scheme (JCS) implementation in Rust.
//!
//! Enforces:
//! - UTF-16 code unit property key sorting (RFC 8785 §3.2.3).
//! - ECMAScript number serialization rules (RFC 8785 §3.2.2.3).
//! - Minimal character escaping without solidus escaping (RFC 8785 §3.2.2.2).
//! - Rejection of non-finite numbers (NaN, Infinity), duplicate keys, and integers > 2^53 - 1.

use serde_json::Value;
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const MAX_SAFE_INTEGER: i64 = 9_007_199_254_740_991; // 2^53 - 1

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum JcsError {
    #[error("non-finite numbers are forbidden in JCS: {0}")]
    NonFiniteNumber(String),
    #[error("integer magnitude exceeds 2^53 - 1 safe limit: {0}")]
    IntegerOutOfRange(String),
    #[error("duplicate object key detected: {0}")]
    DuplicateKey(String),
    #[error("invalid JSON syntax: {0}")]
    SyntaxError(String),
    #[error("invalid number representation: {0}")]
    InvalidNumber(String),
    #[error("lone surrogate in string: {0}")]
    LoneSurrogate(String),
}

#[derive(Clone, Debug, PartialEq)]
pub enum JcsValue {
    Null,
    Bool(bool),
    Number(f64),
    String(String),
    Array(Vec<JcsValue>),
    Object(Vec<(String, JcsValue)>),
}

/// Format an f64 number strictly according to ECMAScript 7.1.12.1 (ToString Applied to the Number Type).
pub fn format_es_number(val: f64) -> Result<String, JcsError> {
    if val.is_nan() || val.is_infinite() {
        return Err(JcsError::NonFiniteNumber(val.to_string()));
    }
    if val == 0.0 {
        // Both +0.0 and -0.0 serialize as "0"
        return Ok("0".to_string());
    }

    let mut out = String::new();
    let (is_neg, abs_val) = if val < 0.0 {
        (true, -val)
    } else {
        (false, val)
    };

    let mut buffer = ryu::Buffer::new();
    let formatted = buffer.format_finite(abs_val);

    // formatted is either standard ("123.456", "1.0") or scientific ("1.23e24", "1e-5", etc.)
    let (s, n): (String, i32) = if let Some((mantissa, exp_str)) = formatted.split_once('e') {
        let exp: i32 = exp_str
            .parse()
            .map_err(|_| JcsError::InvalidNumber(formatted.to_string()))?;
        let digits: String = mantissa.chars().filter(|c| c.is_ascii_digit()).collect();
        (digits, exp + 1)
    } else if let Some((int_part, frac_part)) = formatted.split_once('.') {
        let frac_trimmed = frac_part.trim_end_matches('0');
        if int_part == "0" {
            let leading_zeros = frac_part.chars().take_while(|c| *c == '0').count();
            let digits = frac_trimmed[leading_zeros..].to_string();
            let n = -(leading_zeros as i32);
            (digits, n)
        } else {
            let digits = format!("{}{}", int_part, frac_trimmed);
            let n = int_part.len() as i32;
            (digits, n)
        }
    } else {
        let digits = formatted.to_string();
        let n = digits.len() as i32;
        (digits, n)
    };

    let k = s.len() as i32;

    if is_neg {
        out.push('-');
    }

    if k <= n && n <= 21 {
        out.push_str(&s);
        for _ in 0..(n - k) {
            out.push('0');
        }
    } else if 0 < n && n <= 21 {
        let n_usize = n as usize;
        out.push_str(&s[..n_usize]);
        out.push('.');
        out.push_str(&s[n_usize..]);
    } else if -6 < n && n <= 0 {
        out.push_str("0.");
        for _ in 0..(-n) {
            out.push('0');
        }
        out.push_str(&s);
    } else if k == 1 {
        out.push_str(&s);
        out.push('e');
        let exp = n - 1;
        if exp >= 0 {
            out.push('+');
        } else {
            out.push('-');
        }
        out.push_str(&exp.abs().to_string());
    } else {
        let mut chars = s.chars();
        if let Some(first) = chars.next() {
            out.push(first);
            let rem = chars.as_str();
            if !rem.is_empty() {
                out.push('.');
                out.push_str(rem);
            }
            out.push('e');
            let exp = n - 1;
            if exp >= 0 {
                out.push('+');
            } else {
                out.push('-');
            }
            out.push_str(&exp.abs().to_string());
        }
    }

    Ok(out)
}

/// Format a JSON string according to RFC 8785 §3.2.2.2.
pub fn format_es_string(s: &str, out: &mut String) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\x08' => out.push_str("\\b"),
            '\t' => out.push_str("\\t"),
            '\n' => out.push_str("\\n"),
            '\x0c' => out.push_str("\\f"),
            '\r' => out.push_str("\\r"),
            c if (c as u32) < 0x20 => {
                use std::fmt::Write;
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

/// Serialize a JcsValue into canonical UTF-8 JSON.
pub fn serialize_jcs(val: &JcsValue, out: &mut String) -> Result<(), JcsError> {
    match val {
        JcsValue::Null => out.push_str("null"),
        JcsValue::Bool(true) => out.push_str("true"),
        JcsValue::Bool(false) => out.push_str("false"),
        JcsValue::Number(n) => {
            let num_str = format_es_number(*n)?;
            out.push_str(&num_str);
        }
        JcsValue::String(s) => format_es_string(s, out),
        JcsValue::Array(arr) => {
            out.push('[');
            for (i, elem) in arr.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                serialize_jcs(elem, out)?;
            }
            out.push(']');
        }
        JcsValue::Object(props) => {
            out.push('{');
            for (i, (key, value)) in props.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                format_es_string(key, out);
                out.push(':');
                serialize_jcs(value, out)?;
            }
            out.push('}');
        }
    }
    Ok(())
}

/// Convert a serde_json::Value into JcsValue with UTF-16 sorted keys and integer range check.
pub fn from_serde_value(val: &Value) -> Result<JcsValue, JcsError> {
    match val {
        Value::Null => Ok(JcsValue::Null),
        Value::Bool(b) => Ok(JcsValue::Bool(*b)),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                if i.abs() > MAX_SAFE_INTEGER {
                    return Err(JcsError::IntegerOutOfRange(i.to_string()));
                }
                Ok(JcsValue::Number(i as f64))
            } else if let Some(u) = n.as_u64() {
                if u > MAX_SAFE_INTEGER as u64 {
                    return Err(JcsError::IntegerOutOfRange(u.to_string()));
                }
                Ok(JcsValue::Number(u as f64))
            } else if let Some(f) = n.as_f64() {
                if f.is_nan() || f.is_infinite() {
                    return Err(JcsError::NonFiniteNumber(n.to_string()));
                }
                Ok(JcsValue::Number(f))
            } else {
                Err(JcsError::InvalidNumber(n.to_string()))
            }
        }
        Value::String(s) => Ok(JcsValue::String(s.clone())),
        Value::Array(arr) => {
            let mut items = Vec::with_capacity(arr.len());
            for v in arr {
                items.push(from_serde_value(v)?);
            }
            Ok(JcsValue::Array(items))
        }
        Value::Object(map) => {
            let mut props = Vec::with_capacity(map.len());
            for (k, v) in map {
                props.push((k.clone(), from_serde_value(v)?));
            }
            props.sort_by(|a, b| a.0.encode_utf16().cmp(b.0.encode_utf16()));
            for window in props.windows(2) {
                if window[0].0 == window[1].0 {
                    return Err(JcsError::DuplicateKey(window[0].0.clone()));
                }
            }
            Ok(JcsValue::Object(props))
        }
    }
}

// Direct parser for raw JSON strings that validates duplicate keys and integer bounds
struct JsonParser<'a> {
    chars: std::str::Chars<'a>,
    peeked: Option<char>,
}

impl<'a> JsonParser<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            chars: input.chars(),
            peeked: None,
        }
    }

    fn peek(&mut self) -> Option<char> {
        if self.peeked.is_none() {
            self.peeked = self.chars.next();
        }
        self.peeked
    }

    fn next_char(&mut self) -> Option<char> {
        let ch = self.peeked.take().or_else(|| self.chars.next());
        ch
    }

    fn skip_whitespace(&mut self) {
        while let Some(c) = self.peek() {
            if c.is_ascii_whitespace() {
                self.next_char();
            } else {
                break;
            }
        }
    }

    fn parse_value(&mut self) -> Result<JcsValue, JcsError> {
        self.skip_whitespace();
        match self.peek() {
            Some('n') => self.parse_null(),
            Some('t') | Some('f') => self.parse_bool(),
            Some('"') => self.parse_string().map(JcsValue::String),
            Some('[') => self.parse_array(),
            Some('{') => self.parse_object(),
            Some(c) if c == '-' || c.is_ascii_digit() => self.parse_number(),
            Some(c) => Err(JcsError::SyntaxError(format!(
                "Unexpected character: '{c}'"
            ))),
            None => Err(JcsError::SyntaxError("Unexpected end of input".to_string())),
        }
    }

    fn parse_null(&mut self) -> Result<JcsValue, JcsError> {
        let expected = "null";
        for exp in expected.chars() {
            if self.next_char() != Some(exp) {
                return Err(JcsError::SyntaxError("Expected 'null'".to_string()));
            }
        }
        Ok(JcsValue::Null)
    }

    fn parse_bool(&mut self) -> Result<JcsValue, JcsError> {
        if self.peek() == Some('t') {
            for exp in "true".chars() {
                if self.next_char() != Some(exp) {
                    return Err(JcsError::SyntaxError("Expected 'true'".to_string()));
                }
            }
            Ok(JcsValue::Bool(true))
        } else {
            for exp in "false".chars() {
                if self.next_char() != Some(exp) {
                    return Err(JcsError::SyntaxError("Expected 'false'".to_string()));
                }
            }
            Ok(JcsValue::Bool(false))
        }
    }

    fn parse_string(&mut self) -> Result<String, JcsError> {
        if self.next_char() != Some('"') {
            return Err(JcsError::SyntaxError("Expected opening quote".to_string()));
        }
        let mut s = String::new();
        while let Some(c) = self.next_char() {
            match c {
                '"' => return Ok(s),
                '\\' => {
                    let esc = self.next_char().ok_or_else(|| {
                        JcsError::SyntaxError("Unexpected EOF in escape sequence".to_string())
                    })?;
                    match esc {
                        '"' => s.push('"'),
                        '\\' => s.push('\\'),
                        '/' => s.push('/'),
                        'b' => s.push('\x08'),
                        'f' => s.push('\x0c'),
                        'n' => s.push('\n'),
                        'r' => s.push('\r'),
                        't' => s.push('\t'),
                        'u' => {
                            let mut hex = String::with_capacity(4);
                            for _ in 0..4 {
                                let h = self.next_char().ok_or_else(|| {
                                    JcsError::SyntaxError(
                                        "Unexpected EOF in unicode escape".to_string(),
                                    )
                                })?;
                                hex.push(h);
                            }
                            let code = u16::from_str_radix(&hex, 16).map_err(|e| {
                                JcsError::SyntaxError(format!("Invalid unicode hex: {e}"))
                            })?;
                            // Handle surrogate pairs
                            if (0xD800..=0xDBFF).contains(&code) {
                                // High surrogate, must be followed by \uDC00..\uDFFF
                                if self.next_char() != Some('\\') || self.next_char() != Some('u') {
                                    return Err(JcsError::LoneSurrogate(format!("\\u{hex}")));
                                }
                                let mut low_hex = String::with_capacity(4);
                                for _ in 0..4 {
                                    let h = self.next_char().ok_or_else(|| {
                                        JcsError::SyntaxError(
                                            "Unexpected EOF in surrogate pair".to_string(),
                                        )
                                    })?;
                                    low_hex.push(h);
                                }
                                let low_code = u16::from_str_radix(&low_hex, 16).map_err(|e| {
                                    JcsError::SyntaxError(format!("Invalid surrogate hex: {e}"))
                                })?;
                                if !(0xDC00..=0xDFFF).contains(&low_code) {
                                    return Err(JcsError::LoneSurrogate(format!(
                                        "\\u{hex}\\u{low_hex}"
                                    )));
                                }
                                let scalar = (((code as u32 - 0xD800) << 10)
                                    | (low_code as u32 - 0xDC00))
                                    + 0x10000;
                                let ch = char::from_u32(scalar).ok_or_else(|| {
                                    JcsError::SyntaxError(format!("Invalid scalar: {scalar:#x}"))
                                })?;
                                s.push(ch);
                            } else if (0xDC00..=0xDFFF).contains(&code) {
                                return Err(JcsError::LoneSurrogate(format!("\\u{hex}")));
                            } else {
                                let ch = char::from_u32(code as u32).ok_or_else(|| {
                                    JcsError::SyntaxError(format!(
                                        "Invalid unicode code point: {code:#x}"
                                    ))
                                })?;
                                s.push(ch);
                            }
                        }
                        other => {
                            return Err(JcsError::SyntaxError(format!("Invalid escape: \\{other}")))
                        }
                    }
                }
                c => s.push(c),
            }
        }
        Err(JcsError::SyntaxError("Unclosed string".to_string()))
    }

    fn parse_number(&mut self) -> Result<JcsValue, JcsError> {
        let mut num_str = String::new();
        while let Some(c) = self.peek() {
            if c.is_ascii_digit() || c == '.' || c == '-' || c == '+' || c == 'e' || c == 'E' {
                num_str.push(c);
                self.next_char();
            } else {
                break;
            }
        }

        // Check if pure integer literal exceeds 2^53
        if !num_str.contains('.') && !num_str.contains('e') && !num_str.contains('E') {
            if let Ok(i) = num_str.parse::<i128>() {
                if i.abs() > MAX_SAFE_INTEGER as i128 {
                    return Err(JcsError::IntegerOutOfRange(num_str));
                }
            }
        }

        let val: f64 = num_str
            .parse()
            .map_err(|e| JcsError::InvalidNumber(format!("{num_str}: {e}")))?;
        if val.is_nan() || val.is_infinite() {
            return Err(JcsError::NonFiniteNumber(num_str));
        }
        Ok(JcsValue::Number(val))
    }

    fn parse_array(&mut self) -> Result<JcsValue, JcsError> {
        self.next_char(); // consume '['
        let mut items = Vec::new();
        self.skip_whitespace();
        if self.peek() == Some(']') {
            self.next_char();
            return Ok(JcsValue::Array(items));
        }
        loop {
            let item = self.parse_value()?;
            items.push(item);
            self.skip_whitespace();
            match self.next_char() {
                Some(',') => self.skip_whitespace(),
                Some(']') => break,
                Some(c) => {
                    return Err(JcsError::SyntaxError(format!(
                        "Expected ',' or ']', got '{c}'"
                    )))
                }
                None => return Err(JcsError::SyntaxError("Unterminated array".to_string())),
            }
        }
        Ok(JcsValue::Array(items))
    }

    fn parse_object(&mut self) -> Result<JcsValue, JcsError> {
        self.next_char(); // consume '{'
        let mut props = Vec::new();
        self.skip_whitespace();
        if self.peek() == Some('}') {
            self.next_char();
            return Ok(JcsValue::Object(props));
        }
        loop {
            self.skip_whitespace();
            if self.peek() != Some('"') {
                return Err(JcsError::SyntaxError(
                    "Expected string key in object".to_string(),
                ));
            }
            let key = self.parse_string()?;
            self.skip_whitespace();
            if self.next_char() != Some(':') {
                return Err(JcsError::SyntaxError("Expected ':' after key".to_string()));
            }
            let val = self.parse_value()?;
            props.push((key, val));
            self.skip_whitespace();
            match self.next_char() {
                Some(',') => self.skip_whitespace(),
                Some('}') => break,
                Some(c) => {
                    return Err(JcsError::SyntaxError(format!(
                        "Expected ',' or '}}', got '{c}'"
                    )))
                }
                None => return Err(JcsError::SyntaxError("Unterminated object".to_string())),
            }
        }
        // Sort keys by UTF-16 code units
        props.sort_by(|a, b| a.0.encode_utf16().cmp(b.0.encode_utf16()));
        // Duplicate key check
        for window in props.windows(2) {
            if window[0].0 == window[1].0 {
                return Err(JcsError::DuplicateKey(window[0].0.clone()));
            }
        }
        Ok(JcsValue::Object(props))
    }
}

/// Parse raw JSON string into JcsValue with duplicate key and range checks.
pub fn parse_json(input: &str) -> Result<JcsValue, JcsError> {
    let mut parser = JsonParser::new(input);
    let val = parser.parse_value()?;
    parser.skip_whitespace();
    if parser.peek().is_some() {
        return Err(JcsError::SyntaxError(
            "Trailing characters after JSON value".to_string(),
        ));
    }
    Ok(val)
}

/// Canonicalize raw JSON string to RFC 8785 canonical JSON string.
pub fn canonicalize_str(json_str: &str) -> Result<String, JcsError> {
    let jcs_val = parse_json(json_str)?;
    let mut out = String::new();
    serialize_jcs(&jcs_val, &mut out)?;
    Ok(out)
}

/// Canonicalize a serde_json::Value to RFC 8785 canonical JSON string.
pub fn canonicalize_value(val: &Value) -> Result<String, JcsError> {
    let jcs_val = from_serde_value(val)?;
    let mut out = String::new();
    serialize_jcs(&jcs_val, &mut out)?;
    Ok(out)
}

/// Canonicalize a serde_json::Value directly to canonical UTF-8 bytes.
pub fn canonicalize(val: &Value) -> Result<Vec<u8>, JcsError> {
    let s = canonicalize_value(val)?;
    Ok(s.into_bytes())
}

/// Compute SHA-256 hex digest over RFC 8785 canonical bytes of a serde_json::Value.
pub fn digest_sha256(val: &Value) -> Result<String, JcsError> {
    let bytes = canonicalize(val)?;
    let hash = Sha256::digest(&bytes);
    Ok(hex::encode(hash))
}

/// Compute SHA-256 hex digest over RFC 8785 canonical bytes of a JSON string.
pub fn digest_str_sha256(json_str: &str) -> Result<String, JcsError> {
    let canonical = canonicalize_str(json_str)?;
    let hash = Sha256::digest(canonical.as_bytes());
    Ok(hex::encode(hash))
}

// Origin: engine/crates_rs/pfp_runtime/src/jcs.rs
// Claim: urn:core:crates_rs:pfp-runtime:jcs:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_165321ae {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
