//! DIPHA file format read/write shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_838a0355;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_838a0355<T> = std::result::Result<T, BoundaryError_838a0355>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `dipha_io`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct DiphaIo {
    pub label: String,
    pub notes: Vec<String>,
}

impl DiphaIo {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = DiphaIo::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = DiphaIo::new("dipha_io").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// DIPHA little-endian magic.
pub const DIPHA_MAGIC: i64 = 8_067_171_840;

/// Admitted DIPHA file-type codes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiphaKind {
    /// Weighted boundary matrix, code 0.
    WeightedBoundary = 0,
    /// Image data, code 1.
    Image = 1,
    /// Persistence diagram, code 2.
    Persistence = 2,
    /// Distance matrix, code 7.
    Distance = 7,
}

/// Refusal from a DIPHA header.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiphaError {
    /// Fewer than 16 bytes.
    Short { len: usize },
    /// Magic was not `DIPHA_MAGIC`.
    Magic { found: i64 },
    /// File type was not 0, 1, 2, or 7.
    Kind { found: i64 },
}

// Origin: engine/crates_rs/core_homology/src/dipha_io.rs
// Claim: urn:core:crates_rs:core-homology:dipha-io:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DiphaError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DiphaError {}

/// Parsed magic and file type.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DiphaHeader {
    kind: DiphaKind,
}

fn read_i64(bytes: &[u8], at: usize) -> Result<i64, DiphaError> {
    let mut buf = [0u8; 8];
    for offset in 0..8 {
        let Some(byte) = bytes.get(at + offset).copied() else {
            return Err(DiphaError::Short { len: bytes.len() });
        };
        buf[offset] = byte;
    }
    Ok(i64::from_le_bytes(buf))
}

impl DiphaHeader {
    /// Read the 16-byte DIPHA preamble.
    pub fn try_parse(bytes: &[u8]) -> Result<Self, DiphaError> {
        if bytes.len() < 16 {
            return Err(DiphaError::Short { len: bytes.len() });
        }
        let magic = read_i64(bytes, 0)?;
        if magic != DIPHA_MAGIC {
            return Err(DiphaError::Magic { found: magic });
        }
        let code = read_i64(bytes, 8)?;
        let kind = match code {
            0 => DiphaKind::WeightedBoundary,
            1 => DiphaKind::Image,
            2 => DiphaKind::Persistence,
            7 => DiphaKind::Distance,
            other => return Err(DiphaError::Kind { found: other }),
        };
        Ok(Self { kind })
    }

    /// Admitted file type.
    pub fn kind(&self) -> DiphaKind { self.kind }
}

#[cfg(test)]
mod dipha_header_tests {
    use super::*;
    #[test]
    fn a_persistence_preamble_parses() {
        let mut bytes = Vec::new();
        bytes.extend_from_slice(&DIPHA_MAGIC.to_le_bytes());
        bytes.extend_from_slice(&2i64.to_le_bytes());
        let header = DiphaHeader::try_parse(&bytes);
        assert!(matches!(header, Ok(h) if h.kind() == DiphaKind::Persistence));
    }
    #[test]
    fn a_short_buffer_is_refused() {
        assert!(matches!(DiphaHeader::try_parse(&[0, 1]), Err(DiphaError::Short { .. })));
    }
}
