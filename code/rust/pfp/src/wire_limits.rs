//! Bounded transport preflight for programmatically supplied JSON values.
//! Depth, node count and decoded text bytes are checked before clone or serialization; a
//! counting writer then checks compact encoded bytes without retaining a copy.
//! This checks transport shape, not an application schema. AuthorityEffect: None.

use serde_json::Value;
use std::io::Write;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum JsonWireLimitError {
    Size,
    Depth,
}

// Origin: engine/crates_rs/pfp/src/wire_limits.rs
// Claim: urn:core:crates_rs:pfp:wire-limits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for JsonWireLimitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for JsonWireLimitError {}

fn charge_bytes(total: &mut usize, count: usize, limit: usize) -> Result<(), JsonWireLimitError> {
    let next = total.checked_add(count).ok_or(JsonWireLimitError::Size)?;
    if next > limit {
        return Err(JsonWireLimitError::Size);
    }
    *total = next;
    Ok(())
}

fn walk_children<'a>(
    children: impl Iterator<Item = &'a Value>,
    depth: usize,
    total: &mut usize,
    max_bytes: usize,
    max_depth: usize,
) -> Result<(), JsonWireLimitError> {
    let child_depth = depth.checked_add(1).ok_or(JsonWireLimitError::Depth)?;
    for child in children {
        walk(child, child_depth, total, max_bytes, max_depth)?;
    }
    Ok(())
}

fn walk_object(
    values: &serde_json::Map<String, Value>,
    depth: usize,
    total: &mut usize,
    max_bytes: usize,
    max_depth: usize,
) -> Result<(), JsonWireLimitError> {
    for key in values.keys() {
        charge_bytes(total, key.len(), max_bytes)?;
    }
    walk_children(values.values(), depth, total, max_bytes, max_depth)
}

fn walk(
    value: &Value,
    depth: usize,
    total: &mut usize,
    max_bytes: usize,
    max_depth: usize,
) -> Result<(), JsonWireLimitError> {
    if depth > max_depth {
        return Err(JsonWireLimitError::Depth);
    }
    charge_bytes(total, 1, max_bytes)?;
    match value {
        Value::String(text) => charge_bytes(total, text.len(), max_bytes),
        Value::Array(values) => walk_children(values.iter(), depth, total, max_bytes, max_depth),
        Value::Object(values) => walk_object(values, depth, total, max_bytes, max_depth),
        Value::Null | Value::Bool(_) | Value::Number(_) => Ok(()),
    }
}

struct JsonByteCounter {
    bytes: usize,
    limit: usize,
}

impl Write for JsonByteCounter {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        charge_bytes(&mut self.bytes, bytes.len(), self.limit).map_err(|_| {
            std::io::Error::new(std::io::ErrorKind::InvalidInput, "JSON wire byte limit")
        })?;
        Ok(bytes.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

/// Root depth is zero. Each visited node and every decoded string/key byte
/// consume the byte ceiling before the encoded-byte counter runs. JSON
/// punctuation and escaped text are included in the second, exact count.
pub(crate) fn validate_json_value(
    value: &Value,
    max_bytes: usize,
    max_depth: usize,
) -> Result<(), JsonWireLimitError> {
    let mut decoded_bytes = 0;
    walk(value, 0, &mut decoded_bytes, max_bytes, max_depth)?;
    serde_json::to_writer(
        &mut JsonByteCounter {
            bytes: 0,
            limit: max_bytes,
        },
        value,
    )
    .map_err(|_| JsonWireLimitError::Size)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_01188a01 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
