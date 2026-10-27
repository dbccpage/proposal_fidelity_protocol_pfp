//! Append-only hash-chained JSONL decision log (`AppendLogV1`).
//!
//! One record per line; each record seals `{sequence, parent_sha256, payload}`
//! under SHA-256 (the same digest discipline as
//! [`crate::dual_trace_memory::TraceEventV1`]). [`AppendLogV1::open`] replays
//! and verifies the FULL chain before returning, so a tampered, truncated,
//! reordered, or blank-padded file is a typed refusal — never silently
//! accepted state. Unlike [`crate::trace_writer`] (whole-file-immutable
//! artifacts), an `AppendLogV1` file GROWS: records are appended, existing
//! bytes are never rewritten, and every append is fsynced before it is
//! acknowledged.
//!
//! Diagnostic machinery only — appending a record mints no authority.

use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Write as _};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Failure opening or appending to an append-only log.
#[derive(Debug, thiserror::Error)]
pub enum AppendLogError {
    /// Filesystem failure reading, creating, or syncing the log.
    #[error("append log io at {path}: {source}")]
    Io {
        path: String,
        #[source]
        source: io::Error,
    },
    /// A payload or record could not be serialized to canonical JSON.
    #[error("append log serialize: {0}")]
    Serialize(String),
    /// A line failed to parse as a sealed record (includes torn tails).
    #[error("append log corrupt record at line {line_number}: {reason}")]
    CorruptRecord { line_number: usize, reason: String },
    /// A parsed record does not extend the chain (sequence, parent, or digest).
    #[error("append log chain violation at line {line_number}: {reason}")]
    ChainViolation { line_number: usize, reason: String },
}

/// One sealed record: position, parent digest, opaque JSON payload, and the
/// SHA-256 over the first three (hex, lowercase).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AppendLogRecordV1 {
    pub sequence: u64,
    pub parent_sha256: Option<String>,
    pub payload: serde_json::Value,
    pub record_sha256: String,
}

/// Digest material — the record minus its own digest.
#[derive(Serialize)]
struct RecordMaterialV1<'a> {
    sequence: u64,
    parent_sha256: &'a Option<String>,
    payload: &'a serde_json::Value,
}

impl AppendLogRecordV1 {
    fn seal(
        sequence: u64,
        parent_sha256: Option<String>,
        payload: serde_json::Value,
    ) -> Result<Self, AppendLogError> {
        let record_sha256 = hash_material(&RecordMaterialV1 {
            sequence,
            parent_sha256: &parent_sha256,
            payload: &payload,
        })?;
        Ok(Self {
            sequence,
            parent_sha256,
            payload,
            record_sha256,
        })
    }

    fn expected_sha256(&self) -> Result<String, AppendLogError> {
        hash_material(&RecordMaterialV1 {
            sequence: self.sequence,
            parent_sha256: &self.parent_sha256,
            payload: &self.payload,
        })
    }
}

fn hash_material(material: &RecordMaterialV1<'_>) -> Result<String, AppendLogError> {
    let bytes = serde_json::to_vec(material)
        .map_err(|error| AppendLogError::Serialize(error.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let digest = hasher.finalize();
    let mut out = String::with_capacity(64);
    use std::fmt::Write as _;
    for byte in digest {
        let _ = write!(out, "{byte:02x}");
    }
    Ok(out)
}

/// An open, chain-verified, append-only JSONL log.
#[derive(Debug)]
pub struct AppendLogV1 {
    path: PathBuf,
    file: File,
    head_sha256: Option<String>,
    next_sequence: u64,
}

impl AppendLogV1 {
    /// Open (creating parents and the file if absent), verify the ENTIRE
    /// chain, and return the log plus every previously persisted record in
    /// order. Any corruption is a typed refusal and nothing is returned.
    fn parse_and_verify_line(
        line_number: usize,
        line: &str,
        next_sequence: u64,
        head_sha256: &Option<String>,
    ) -> Result<AppendLogRecordV1, AppendLogError> {
        if line.trim().is_empty() {
            // Appends never write blank lines; one here means the file
            // was edited or torn. Refuse rather than resynchronize.
            return Err(AppendLogError::CorruptRecord {
                line_number,
                reason: "blank line in append-only log".to_string(),
            });
        }
        let record: AppendLogRecordV1 =
            serde_json::from_str(line).map_err(|error| AppendLogError::CorruptRecord {
                line_number,
                reason: format!("unparseable record (torn tail?): {error}"),
            })?;
        if record.sequence != next_sequence {
            return Err(AppendLogError::ChainViolation {
                line_number,
                reason: format!(
                    "sequence {} where {} was required",
                    record.sequence, next_sequence
                ),
            });
        }
        if &record.parent_sha256 != head_sha256 {
            return Err(AppendLogError::ChainViolation {
                line_number,
                reason: "parent digest does not match prior record".to_string(),
            });
        }
        let expected = record.expected_sha256()?;
        if expected != record.record_sha256 {
            return Err(AppendLogError::ChainViolation {
                line_number,
                reason: "record digest does not match sealed material".to_string(),
            });
        }
        Ok(record)
    }

    pub fn open(path: PathBuf) -> Result<(Self, Vec<AppendLogRecordV1>), AppendLogError> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent).map_err(|source| io_error(parent, source))?;
            }
        }

        let mut records: Vec<AppendLogRecordV1> = Vec::new();
        let mut head_sha256: Option<String> = None;
        let mut next_sequence: u64 = 0;

        if path.exists() {
            let reader =
                BufReader::new(File::open(&path).map_err(|source| io_error(&path, source))?);
            for (index, line) in reader.lines().enumerate() {
                let line_number = index + 1;
                let line = line.map_err(|source| io_error(&path, source))?;
                let record = Self::parse_and_verify_line(line_number, &line, next_sequence, &head_sha256)?;
                head_sha256 = Some(record.record_sha256.clone());
                next_sequence += 1;
                records.push(record);
            }
        }

        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .map_err(|source| io_error(&path, source))?;

        let log = Self {
            path,
            file,
            head_sha256,
            next_sequence,
        };
        Ok((log, records))
    }

    /// Seal `payload` onto the chain, append one line, and fsync BEFORE
    /// acknowledging. On error the in-memory cursor is unchanged.
    pub fn append(
        &mut self,
        payload: serde_json::Value,
    ) -> Result<AppendLogRecordV1, AppendLogError> {
        let record =
            AppendLogRecordV1::seal(self.next_sequence, self.head_sha256.clone(), payload)?;
        let mut line = serde_json::to_string(&record)
            .map_err(|error| AppendLogError::Serialize(error.to_string()))?;
        line.push('\n');
        self.file
            .write_all(line.as_bytes())
            .map_err(|source| io_error(&self.path, source))?;
        self.file
            .sync_all()
            .map_err(|source| io_error(&self.path, source))?;
        self.head_sha256 = Some(record.record_sha256.clone());
        self.next_sequence += 1;
        Ok(record)
    }

    /// Digest of the most recent record (`None` on an empty log).
    pub fn head_sha256(&self) -> Option<&str> {
        self.head_sha256.as_deref()
    }

    /// Count of persisted records.
    pub fn len(&self) -> u64 {
        self.next_sequence
    }

    /// True when no record has ever been appended.
    pub fn is_empty(&self) -> bool {
        self.next_sequence == 0
    }

    /// The backing file path.
    pub fn path(&self) -> &Path {
        &self.path
    }
}

fn io_error(path: &Path, source: io::Error) -> AppendLogError {
    AppendLogError::Io {
        path: path.display().to_string(),
        source,
    }
}

// Origin: engine/crates_rs/core_replay/src/append_log.rs
// Claim: urn:core:crates_rs:core-replay:append-log:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn temp_log_path(dir: &Path) -> PathBuf {
        dir.join(".intelligence").join("test_log_v1.jsonl")
    }

    #[test]
    fn open_empty_then_append_then_reopen_round_trips_payloads() {
        let dir = std::env::temp_dir().join(format!("append_log_rt_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let path = temp_log_path(&dir);

        let (mut log, existing) = AppendLogV1::open(path.clone()).expect("open fresh log");
        assert!(existing.is_empty());
        assert!(log.is_empty());
        assert_eq!(log.head_sha256(), None);

        let first = log.append(json!({"kind": "a", "n": 1})).expect("append 1");
        let second = log.append(json!({"kind": "b", "n": 2})).expect("append 2");
        assert_eq!(first.sequence, 0);
        assert_eq!(first.parent_sha256, None);
        assert_eq!(second.sequence, 1);
        assert_eq!(
            second.parent_sha256.as_deref(),
            Some(first.record_sha256.as_str())
        );
        assert_eq!(log.len(), 2);
        assert_eq!(log.head_sha256(), Some(second.record_sha256.as_str()));

        drop(log);
        let (reopened, records) = AppendLogV1::open(path.clone()).expect("reopen verified log");
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].payload, json!({"kind": "a", "n": 1}));
        assert_eq!(records[1].payload, json!({"kind": "b", "n": 2}));
        assert_eq!(
            reopened.head_sha256(),
            Some(second.record_sha256.as_str()),
            "reopen must restore the chain head"
        );
        assert_eq!(reopened.len(), 2);

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn append_after_reopen_extends_the_same_chain() {
        let dir = std::env::temp_dir().join(format!("append_log_ext_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let path = temp_log_path(&dir);

        let (mut log, _) = AppendLogV1::open(path.clone()).expect("open");
        let first = log.append(json!({"n": 1})).expect("append");
        drop(log);

        let (mut log, _) = AppendLogV1::open(path.clone()).expect("reopen");
        let second = log.append(json!({"n": 2})).expect("append after reopen");
        assert_eq!(second.sequence, 1);
        assert_eq!(
            second.parent_sha256.as_deref(),
            Some(first.record_sha256.as_str())
        );

        let (_, records) = AppendLogV1::open(path).expect("final verify");
        assert_eq!(records.len(), 2);

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn tampered_payload_byte_is_a_typed_chain_violation() {
        let dir = std::env::temp_dir().join(format!("append_log_tamper_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let path = temp_log_path(&dir);

        let (mut log, _) = AppendLogV1::open(path.clone()).expect("open");
        log.append(json!({"amount": 1})).expect("append");
        drop(log);

        let contents = fs::read_to_string(&path).expect("read log");
        let tampered = contents.replace("\"amount\":1", "\"amount\":9");
        assert_ne!(contents, tampered, "tamper fixture must change bytes");
        fs::write(&path, tampered).expect("write tampered log");

        let error = AppendLogV1::open(path).expect_err("tampered log must refuse to open");
        assert!(
            matches!(error, AppendLogError::ChainViolation { line_number: 1, .. }),
            "expected ChainViolation at line 1, got {error:?}"
        );

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn torn_tail_is_a_typed_corrupt_record() {
        let dir = std::env::temp_dir().join(format!("append_log_torn_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let path = temp_log_path(&dir);

        let (mut log, _) = AppendLogV1::open(path.clone()).expect("open");
        log.append(json!({"n": 1})).expect("append 1");
        log.append(json!({"n": 2})).expect("append 2");
        drop(log);

        let contents = fs::read_to_string(&path).expect("read log");
        let torn = &contents[..contents.len() - 10];
        fs::write(&path, torn).expect("write torn log");

        let error = AppendLogV1::open(path).expect_err("torn tail must refuse to open");
        assert!(
            matches!(error, AppendLogError::CorruptRecord { line_number: 2, .. }),
            "expected CorruptRecord at line 2, got {error:?}"
        );

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn reordered_records_are_a_typed_chain_violation() {
        let dir = std::env::temp_dir().join(format!("append_log_reorder_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let path = temp_log_path(&dir);

        let (mut log, _) = AppendLogV1::open(path.clone()).expect("open");
        log.append(json!({"n": 1})).expect("append 1");
        log.append(json!({"n": 2})).expect("append 2");
        drop(log);

        let contents = fs::read_to_string(&path).expect("read log");
        let mut lines: Vec<&str> = contents.lines().collect();
        lines.swap(0, 1);
        fs::write(&path, format!("{}\n{}\n", lines[0], lines[1])).expect("write reordered");

        let error = AppendLogV1::open(path).expect_err("reordered log must refuse to open");
        assert!(
            matches!(error, AppendLogError::ChainViolation { line_number: 1, .. }),
            "expected ChainViolation at line 1, got {error:?}"
        );

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn blank_interior_line_is_a_typed_corrupt_record() {
        let dir = std::env::temp_dir().join(format!("append_log_blank_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let path = temp_log_path(&dir);

        let (mut log, _) = AppendLogV1::open(path.clone()).expect("open");
        log.append(json!({"n": 1})).expect("append 1");
        drop(log);

        let mut contents = fs::read_to_string(&path).expect("read log");
        contents.push('\n');
        contents.push('\n');
        fs::write(&path, contents).expect("write blank-padded log");

        let error = AppendLogV1::open(path).expect_err("blank-padded log must refuse to open");
        assert!(
            matches!(error, AppendLogError::CorruptRecord { line_number: 2, .. }),
            "expected CorruptRecord at line 2, got {error:?}"
        );

        let _ = fs::remove_dir_all(&dir);
    }
}
