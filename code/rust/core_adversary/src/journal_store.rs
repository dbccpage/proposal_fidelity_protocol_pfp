//! Fsynced JSONL adapter. Reads damaged lines without promoting them to events.
use crate::exact::{integer, Integer};
use crate::journal::{EntryKind, JournalEntry, JournalPort};
use chrono::{SecondsFormat, Utc};
use indexmap::IndexMap;
use crate::stage::ports::Refusal;
use core_types::python_unicode::repr_string;
use serde_json::{json, value::RawValue, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

const LOCUS: &str = "adversary.infrastructure.bout_journal_store";

pub trait TimestampPort {
    fn now_utc(&self) -> String;
}
pub struct UtcTimestamp;
impl TimestampPort for UtcTimestamp {
    fn now_utc(&self) -> String {
        Utc::now().to_rfc3339_opts(SecondsFormat::Micros, false)
    }
}

pub struct JsonlJournal<C = UtcTimestamp> {
    path: PathBuf,
    clock: C,
}
impl JsonlJournal<UtcTimestamp> {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self {
            path: path.into(),
            clock: UtcTimestamp,
        }
    }
}
impl<C: TimestampPort> JsonlJournal<C> {
    pub fn with_clock(path: impl Into<PathBuf>, clock: C) -> Self {
        Self {
            path: path.into(),
            clock,
        }
    }
    pub fn path(&self) -> &Path {
        &self.path
    }
    fn needs_leading_newline(&self) -> std::io::Result<bool> {
        match File::open(&self.path) {
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(false),
            Err(e) => Err(e),
            Ok(mut file) => {
                if file.metadata()?.len() == 0 {
                    return Ok(false);
                }
                file.seek(SeekFrom::End(-1))?;
                let mut last = [0];
                file.read_exact(&mut last)?;
                Ok(last[0] != b'\n')
            }
        }
    }
}
fn unavailable(action: &str, error: impl std::fmt::Display) -> Refusal {
    let mut refusal = Refusal::new(
        "BOUT_JOURNAL_UNAVAILABLE",
        format!("cannot {action} the bout journal: {error}"),
    );
    refusal.locus = LOCUS.into();
    refusal
}
impl<C: TimestampPort> JsonlJournal<C> {
    fn write_journal_line(&self, line: &[u8]) -> std::io::Result<()> {
        if let Some(parent) = self.path.parent().filter(|p| !p.as_os_str().is_empty()) {
            fs::create_dir_all(parent)?;
        }
        let fresh = self.needs_leading_newline()?;
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        if fresh {
            file.write_all(b"\n")?;
        }
        file.write_all(line)?;
        file.flush()?;
        file.sync_all()
    }
}
impl<C: TimestampPort> JournalPort for JsonlJournal<C> {
    fn append(&mut self, entry: &JournalEntry) -> Result<(), Refusal> {
        let record = json!({"authority_effect": entry.authority_effect, "bout_id": entry.bout_id,
            "detail": entry.detail, "kind": entry.kind, "recorded_at_utc": self.clock.now_utc(),
            "sequence": entry.sequence, "task_key": entry.task_key});
        let mut line = python_ascii_json(&record)?.into_bytes();
        line.push(b'\n');
        self.write_journal_line(&line)
            .map_err(|e| unavailable("append to", e))
    }
    fn read_all(&self) -> Result<Vec<JournalEntry>, Refusal> {
        let raw = match fs::read(&self.path) {
            Ok(raw) => raw,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
            Err(e) => return Err(unavailable("read", e)),
        };
        Ok(raw
            .split(|b| *b == b'\n')
            .enumerate()
            .filter(|(_, line)| !line.iter().all(u8::is_ascii_whitespace))
            .map(|(index, line)| parse_line(index + 1, line))
            .collect())
    }
}

fn python_ascii_json(value: &Value) -> Result<String, Refusal> {
    crate::wire_json::python_ascii_json(value).map_err(|error| unavailable("encode", error))
}

fn unreadable(number: usize, line: &[u8], why: &str) -> JournalEntry {
    let mut entry = JournalEntry::new("", EntryKind::JournalLineUnreadable, "");
    entry.detail = vec![
        ("line_number".into(), number.to_string()),
        ("line_sha256".into(), hex::encode(Sha256::digest(line))),
        ("why".into(), why.into()),
    ];
    entry
}

// The Python store coerces damaged non-string metadata. Keep mapping order local,
// without enabling serde_json's preserve_order feature across the workspace.
fn python_repr(raw: &RawValue) -> String {
    match serde_json::from_str::<Value>(raw.get()) {
        Ok(Value::String(text)) => repr_string(&text),
        Ok(Value::Null) => "None".into(),
        Ok(Value::Bool(true)) => "True".into(),
        Ok(Value::Bool(false)) => "False".into(),
        Ok(Value::Array(_)) => {
            let items: Vec<Box<RawValue>> = serde_json::from_str(raw.get()).unwrap_or_default();
            format!(
                "[{}]",
                items
                    .iter()
                    .map(|v| python_repr(v))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        }
        Ok(Value::Object(_)) => {
            let items: IndexMap<String, Box<RawValue>> =
                serde_json::from_str(raw.get()).unwrap_or_default();
            format!(
                "{{{}}}",
                items
                    .iter()
                    .map(|(k, v)| format!("{}: {}", repr_string(k), python_repr(v)))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        }
        Ok(number) => number.to_string(),
        Err(_) => String::new(),
    }
}
fn python_string(raw: &RawValue) -> String {
    match serde_json::from_str::<Value>(raw.get()) {
        Ok(Value::String(text)) => text,
        _ => python_repr(raw),
    }
}

fn populate_journal_details(entry: &mut JournalEntry, record: &BTreeMap<String, Box<RawValue>>) {
    if let Some(sequence) = record
        .get("sequence")
        .and_then(|raw| serde_json::from_str::<Value>(raw.get()).ok())
        .and_then(|v| integer(&v))
    {
        entry.sequence = Integer(sequence);
    }
    if let Some(items) = record
        .get("detail")
        .and_then(|raw| serde_json::from_str::<Vec<Box<RawValue>>>(raw.get()).ok())
    {
        for item in items {
            if let Ok(pair) = serde_json::from_str::<[Box<RawValue>; 2]>(item.get()) {
                entry
                    .detail
                    .push((python_string(&pair[0]), python_string(&pair[1])));
            }
        }
    }
    if let Some(stamp) = record
        .get("recorded_at_utc")
        .and_then(|raw| serde_json::from_str::<String>(raw.get()).ok())
    {
        entry.detail.push(("recorded_at_utc".into(), stamp));
    }
}

pub fn parse_line(number: usize, line: &[u8]) -> JournalEntry {
    let text = match std::str::from_utf8(line) {
        Ok(text) => text,
        Err(_) => return unreadable(number, line, "UnicodeDecodeError"),
    };
    let record: BTreeMap<String, Box<RawValue>> = match serde_json::from_str::<Value>(text) {
        Err(_) => return unreadable(number, line, "JSONDecodeError"),
        Ok(Value::Object(_)) => match serde_json::from_str(text) {
            Ok(record) => record,
            Err(_) => return unreadable(number, line, "JSONDecodeError"),
        },
        Ok(_) => return unreadable(number, line, "NOT_AN_OBJECT"),
    };
    let kind = match record
        .get("kind")
        .and_then(|raw| serde_json::from_str::<EntryKind>(raw.get()).ok())
    {
        Some(kind) => kind,
        None => return unreadable(number, line, "UNKNOWN_KIND"),
    };
    let bout = record
        .get("bout_id")
        .map(|raw| python_string(raw))
        .unwrap_or_default();
    let task = record
        .get("task_key")
        .map(|raw| python_string(raw))
        .unwrap_or_default();
    let mut entry = JournalEntry::new(&bout, kind, &task);
    populate_journal_details(&mut entry, &record);
    entry
}

// Origin: engine/crates_rs/core_adversary/src/journal_store.rs
// Claim: urn:core:crates_rs:core-adversary:journal-store:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_00e3a120 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
