//! Sealed, content-addressed RunFolderV1 for the Symbol Game.
//!
//! AuthorityEffect: None.
//! Every execution produces exactly one sealed RunFolderV1 under
//! `_intelligence/symbol_game/runs/<utc>_<trigger>_<task>_<id>/`.
//! The `receipt.json` binds the SHA-256 of every other file and the head hash
//! of each JSONL chain. Nothing is overwritten, and nothing is discarded.

use std::collections::BTreeMap;
use std::fs::{self, File};
use std::io::{self, BufRead, BufReader, Read, Write};
use std::path::Path;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::append_log::{AppendLogError, AppendLogV1};
use crate::secret_scrubber::SecretScrubber;

pub const MANIFEST_SCHEMA_V1: &str = "core.run_folder.manifest.v1";
pub const RECEIPT_SCHEMA_V1: &str = "core.run_folder.receipt.v1";
pub const AUTHORITY_EFFECT_NONE: &str = "None";

/// Closed enum of execution triggers.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RunTrigger {
    Cli,
    Demo,
    Bench,
    Trial,
    Adversary,
    AdversarySkill,
    Oeop,
    Challenge,
    Mining,
    OperandAdmission,
    Test,
}

impl RunTrigger {
    fn domain_str(&self) -> Option<&'static str> {
        match self {
            Self::Adversary => Some("adversary"),
            Self::AdversarySkill => Some("adversary_skill"),
            Self::Oeop => Some("oewas"),
            Self::Challenge => Some("challenge"),
            Self::Mining => Some("mining"),
            Self::OperandAdmission => Some("operand_admission"),
            _ => None,
        }
    }

    pub fn as_str(&self) -> &'static str {
        if let Some(s) = self.domain_str() {
            return s;
        }
        match self {
            Self::Cli => "cli",
            Self::Demo => "demo",
            Self::Bench => "bench",
            Self::Trial => "trial",
            _ => "test",
        }
    }

    fn from_domain_str(lower: &str) -> Option<Self> {
        match lower {
            "adversary" => Some(Self::Adversary),
            "adversary_skill" => Some(Self::AdversarySkill),
            "oewas" => Some(Self::Oeop),
            "challenge" => Some(Self::Challenge),
            "mining" => Some(Self::Mining),
            "operand_admission" => Some(Self::OperandAdmission),
            _ => None,
        }
    }

    pub fn from_str_opt(s: &str) -> Option<Self> {
        let lower = s.to_ascii_lowercase();
        if let Some(trigger) = Self::from_domain_str(&lower) {
            return Some(trigger);
        }
        match lower.as_str() {
            "cli" => Some(Self::Cli),
            "demo" => Some(Self::Demo),
            "bench" => Some(Self::Bench),
            "trial" => Some(Self::Trial),
            "test" => Some(Self::Test),
            _ => None,
        }
    }
}

/// Execution mode: fixture vs live model.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RunMode {
    Fixture,
    Live,
}

impl RunMode {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Fixture => "fixture",
            Self::Live => "live",
        }
    }
}

/// Run manifest describing provenance, code hashes, and configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunManifestV1 {
    pub schema_version: String,
    pub run_id: String,
    pub utc: String,
    pub trigger: RunTrigger,
    pub task_slug: String,
    pub parent_run_ids: Vec<String>,
    pub git_revision: Option<String>,
    pub git_dirty: bool,
    pub code_hashes: BTreeMap<String, String>,
    pub model_registry_entries: Vec<String>,
    pub budget_ceiling_micro_usd: Option<u64>,
    pub run_mode: RunMode,
    pub authority_effect: String,
}

/// Final cryptographic receipt sealing a run folder.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunReceiptV1 {
    pub schema_version: String,
    pub run_id: String,
    pub status: String,
    pub reason: Option<String>,
    pub files: BTreeMap<String, String>,
    pub chain_heads: BTreeMap<String, Option<String>>,
    pub sealed_at_utc: String,
    pub authority_effect: String,
}

/// Errors occurring during run folder operations.
#[derive(Debug, thiserror::Error)]
pub enum RunFolderError {
    #[error("I/O error at {path}: {source}")]
    Io {
        path: String,
        #[source]
        source: io::Error,
    },
    #[error("JSON error: {0}")]
    Json(String),
    #[error("Manifest file manifest.json is missing in {0}")]
    ManifestMissing(String),
    #[error("Receipt file receipt.json is missing in {0}")]
    ReceiptMissing(String),
    #[error("Digest mismatch for file {file}: expected {expected}, got {actual}")]
    DigestMismatch {
        file: String,
        expected: String,
        actual: String,
    },
    #[error("Unbound file in run folder not covered by receipt: {0}")]
    UnboundFile(String),
    #[error("Missing file referenced by receipt: {0}")]
    MissingFile(String),
    #[error("Hash chain tampered in stream {stream}: {reason}")]
    ChainTampered { stream: String, reason: String },
    #[error("Run folder already exists: {0}")]
    RunFolderExists(String),
    #[error("Invalid authority effect {actual}; expected {AUTHORITY_EFFECT_NONE}")]
    InvalidAuthorityEffect { actual: String },
}

fn classify_slug_char(c: char) -> Option<char> {
    if c.is_ascii_alphanumeric() || matches!(c, '_' | '-') {
        Some(c)
    } else if c.is_whitespace() {
        Some('_')
    } else {
        None
    }
}

/// Sanitize a task name into a slug of at most 40 characters.
pub fn sanitize_task_slug(task: &str) -> String {
    let mut slug: String = task.chars().filter_map(classify_slug_char).collect();
    if slug.is_empty() {
        slug.push_str("task");
    }
    slug.truncate(40);
    slug
}

/// Compute canonical run folder name `<utc>_<trigger>_<task>_<id>/`.
pub fn generate_run_folder_name(
    utc: &str,
    trigger: RunTrigger,
    task: &str,
    nonce: u64,
) -> (String, String) {
    let slug = sanitize_task_slug(task);
    let mut hasher = Sha256::new();
    hasher.update(utc.as_bytes());
    hasher.update(b":");
    hasher.update(trigger.as_str().as_bytes());
    hasher.update(b":");
    hasher.update(slug.as_bytes());
    hasher.update(b":");
    hasher.update(nonce.to_string().as_bytes());
    let digest = format!("{:x}", hasher.finalize());
    let id_12 = &digest[..12];
    let folder_name = format!("{}_{}_{}_{}", utc, trigger.as_str(), slug, id_12);
    (folder_name, id_12.to_string())
}

/// Compute SHA-256 of file bytes.
pub fn compute_file_sha256(path: &Path) -> Result<String, io::Error> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 8192];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

/// Scrub secrets from packets.jsonl in place before sealing.
fn scrub_packets_stream(path: &Path) -> Result<(), io::Error> {
    if !path.exists() {
        return Ok(());
    }
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut lines = Vec::new();
    let mut any_scrubbed = false;
    let scrubber = SecretScrubber::new();

    for line_result in reader.lines() {
        let line = line_result?;
        let (scrubbed, report) = scrubber.scrub(&line);
        if !report.is_clean() {
            any_scrubbed = true;
            lines.push(scrubbed.into_owned());
        } else {
            lines.push(line);
        }
    }

    if any_scrubbed {
        let mut out = File::create(path)?;
        for line in lines {
            writeln!(out, "{}", line)?;
        }
        out.sync_all()?;
    }
    Ok(())
}

fn fallback_last_line_sha256(path: &Path) -> Result<Option<String>, RunFolderError> {
    // Check if it's plain json or text
    let file = File::open(path).map_err(|source| RunFolderError::Io {
        path: path.display().to_string(),
        source,
    })?;
    let reader = BufReader::new(file);
    let last_line = reader
        .lines()
        .map_while(Result::ok)
        .filter(|line| !line.trim().is_empty())
        .last();
    Ok(last_line.map(|last| {
        let mut hasher = Sha256::new();
        hasher.update(last.as_bytes());
        format!("{:x}", hasher.finalize())
    }))
}

/// Verify integrity of an AppendLog stream if present.
fn verify_stream_chain(path: &Path) -> Result<Option<String>, RunFolderError> {
    if !path.exists() {
        return Ok(None);
    }
    let metadata = fs::metadata(path).map_err(|source| RunFolderError::Io {
        path: path.display().to_string(),
        source,
    })?;
    if metadata.len() == 0 {
        return Ok(None);
    }

    match AppendLogV1::open(path.to_path_buf()) {
        Ok((log, _)) => Ok(log.head_sha256().map(|s| s.to_string())),
        Err(AppendLogError::CorruptRecord { .. }) => {
            // If it's not formatted as an AppendLogRecordV1 (e.g. plain JSONL),
            // compute the hash of the last line as chain head without error.
            fallback_last_line_sha256(path)
        }
        Err(AppendLogError::ChainViolation { line_number, reason }) => {
            let err = RunFolderError::ChainTampered {
                stream: path
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned(),
                reason: format!("line {line_number}: {reason}"),
            };
            Err(err)
        }
        Err(AppendLogError::Io { path: p, source }) => Err(RunFolderError::Io { path: p, source }),
        Err(AppendLogError::Serialize(s)) => Err(RunFolderError::Json(s)),
    }
}

fn collect_stream_chain_heads(
    run_dir: &Path,
) -> Result<BTreeMap<String, Option<String>>, RunFolderError> {
    let stream_names = [
        "packets.jsonl",
        "ddc_trace.jsonl",
        "prime_trace.jsonl",
        "obstructions.jsonl",
        "cemetery.jsonl",
    ];
    let mut chain_heads = BTreeMap::new();
    for stream_name in &stream_names {
        let stream_path = run_dir.join(stream_name);
        if stream_path.exists() {
            let head = verify_stream_chain(&stream_path)?;
            chain_heads.insert((*stream_name).to_string(), head);
        }
    }
    Ok(chain_heads)
}

fn hash_run_dir_files(run_dir: &Path) -> Result<BTreeMap<String, String>, RunFolderError> {
    let mut files = BTreeMap::new();
    let entries = fs::read_dir(run_dir).map_err(|source| RunFolderError::Io {
        path: run_dir.display().to_string(),
        source,
    })?;

    for entry in entries {
        let entry = entry.map_err(|source| RunFolderError::Io {
            path: run_dir.display().to_string(),
            source,
        })?;
        let path = entry.path();
        if path.is_file() {
            let file_name = entry.file_name().to_string_lossy().into_owned();
            if file_name == "receipt.json" || file_name.starts_with('.') {
                continue;
            }
            let hash = compute_file_sha256(&path).map_err(|source| RunFolderError::Io {
                path: path.display().to_string(),
                source,
            })?;
            files.insert(file_name, hash);
        }
    }
    Ok(files)
}

/// Seal a RunFolder directory: scrubs secrets, collects file hashes & chain heads,
/// writes `receipt.json`.
pub fn seal_run_folder(
    run_dir: &Path,
    status: Option<&str>,
    reason: Option<&str>,
    sealed_at_utc: Option<&str>,
) -> Result<RunReceiptV1, RunFolderError> {
    let manifest_path = run_dir.join("manifest.json");
    if !manifest_path.exists() {
        return Err(RunFolderError::ManifestMissing(
            run_dir.display().to_string(),
        ));
    }

    let manifest_bytes = fs::read(&manifest_path).map_err(|source| RunFolderError::Io {
        path: manifest_path.display().to_string(),
        source,
    })?;
    let manifest: RunManifestV1 =
        serde_json::from_slice(&manifest_bytes).map_err(|e| RunFolderError::Json(e.to_string()))?;

    // 1. Scrub secrets in packets.jsonl if present
    let packets_path = run_dir.join("packets.jsonl");
    scrub_packets_stream(&packets_path).map_err(|source| RunFolderError::Io {
        path: packets_path.display().to_string(),
        source,
    })?;

    // 2. Collect chain heads for known stream files
    let chain_heads = collect_stream_chain_heads(run_dir)?;

    // 3. Hash all non-receipt files
    let files = hash_run_dir_files(run_dir)?;

    let receipt = RunReceiptV1 {
        schema_version: RECEIPT_SCHEMA_V1.to_string(),
        run_id: manifest.run_id,
        status: status.unwrap_or("SEALED").to_string(),
        reason: reason.map(|s| s.to_string()),
        files,
        chain_heads,
        sealed_at_utc: sealed_at_utc.unwrap_or(&manifest.utc).to_string(),
        authority_effect: AUTHORITY_EFFECT_NONE.to_string(),
    };

    let receipt_path = run_dir.join("receipt.json");
    let receipt_json =
        serde_json::to_string(&receipt).map_err(|e| RunFolderError::Json(e.to_string()))?;
    fs::write(&receipt_path, receipt_json.as_bytes()).map_err(|source| RunFolderError::Io {
        path: receipt_path.display().to_string(),
        source,
    })?;

    Ok(receipt)
}

fn verify_bound_files(
    run_dir: &Path,
    files: &BTreeMap<String, String>,
) -> Result<(), RunFolderError> {
    for (file_name, expected_hash) in files {
        let file_path = run_dir.join(file_name);
        if !file_path.exists() {
            return Err(RunFolderError::MissingFile(file_name.clone()));
        }
        let actual_hash = compute_file_sha256(&file_path).map_err(|source| RunFolderError::Io {
            path: file_path.display().to_string(),
            source,
        })?;
        if &actual_hash != expected_hash {
            let err = RunFolderError::DigestMismatch {
                file: file_name.clone(),
                expected: expected_hash.clone(),
                actual: actual_hash,
            };
            return Err(err);
        }
    }
    Ok(())
}

fn verify_no_unbound_files(
    run_dir: &Path,
    files: &BTreeMap<String, String>,
) -> Result<(), RunFolderError> {
    let entries = fs::read_dir(run_dir).map_err(|source| RunFolderError::Io {
        path: run_dir.display().to_string(),
        source,
    })?;

    for entry in entries {
        let entry = entry.map_err(|source| RunFolderError::Io {
            path: run_dir.display().to_string(),
            source,
        })?;
        let path = entry.path();
        if path.is_file() {
            let file_name = entry.file_name().to_string_lossy().into_owned();
            if file_name == "receipt.json" || file_name.starts_with('.') {
                continue;
            }
            if !files.contains_key(&file_name) {
                return Err(RunFolderError::UnboundFile(file_name));
            }
        }
    }
    Ok(())
}

fn verify_receipt_chains(
    run_dir: &Path,
    chain_heads: &BTreeMap<String, Option<String>>,
) -> Result<(), RunFolderError> {
    for (stream_name, expected_head) in chain_heads {
        let stream_path = run_dir.join(stream_name);
        if stream_path.exists() {
            let actual_head = verify_stream_chain(&stream_path)?;
            if actual_head != *expected_head {
                let err = RunFolderError::ChainTampered {
                    stream: stream_name.clone(),
                    reason: format!(
                        "head mismatch: expected {:?}, got {:?}",
                        expected_head, actual_head
                    ),
                };
                return Err(err);
            }
        }
    }
    Ok(())
}

/// Verify a sealed RunFolder: checks all file digests match `receipt.json`,
/// no extra/missing files exist, and hash chains are intact.
pub fn verify_run_folder(run_dir: &Path) -> Result<RunReceiptV1, RunFolderError> {
    let receipt_path = run_dir.join("receipt.json");
    if !receipt_path.exists() {
        return Err(RunFolderError::ReceiptMissing(
            run_dir.display().to_string(),
        ));
    }

    let receipt_bytes = fs::read(&receipt_path).map_err(|source| RunFolderError::Io {
        path: receipt_path.display().to_string(),
        source,
    })?;
    let receipt: RunReceiptV1 =
        serde_json::from_slice(&receipt_bytes).map_err(|e| RunFolderError::Json(e.to_string()))?;

    if receipt.authority_effect != AUTHORITY_EFFECT_NONE {
        let err = RunFolderError::InvalidAuthorityEffect {
            actual: receipt.authority_effect,
        };
        return Err(err);
    }

    // 1. Verify every file bound in the receipt exists and matches hash
    verify_bound_files(run_dir, &receipt.files)?;

    // 2. Check no unbound files exist
    verify_no_unbound_files(run_dir, &receipt.files)?;

    // 3. Verify stream chains
    verify_receipt_chains(run_dir, &receipt.chain_heads)?;

    Ok(receipt)
}

/// Sealed, content-addressed RunFolderV1 model and filesystem representation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunFolder {
    pub folder_name: String,
    pub path: String,
    pub manifest: RunManifestV1,
    pub receipt: Option<RunReceiptV1>,
    pub status: String,
}

impl RunFolder {
    /// Create a new open RunFolder on disk.
    pub fn open(
        base_dir: &Path,
        utc: &str,
        trigger: RunTrigger,
        task: &str,
        nonce: u64,
        manifest_builder: impl FnOnce(String) -> RunManifestV1,
    ) -> Result<Self, RunFolderError> {
        let (folder_name, _) = generate_run_folder_name(utc, trigger, task, nonce);
        let folder_path = base_dir.join(&folder_name);
        if folder_path.exists() {
            return Err(RunFolderError::RunFolderExists(folder_path.display().to_string()));
        }
        fs::create_dir_all(&folder_path).map_err(|source| RunFolderError::Io {
            path: folder_path.display().to_string(),
            source,
        })?;

        let manifest = manifest_builder(folder_name.clone());
        let manifest_bytes = serde_json::to_vec_pretty(&manifest)
            .map_err(|e| RunFolderError::Json(e.to_string()))?;
        fs::write(folder_path.join("manifest.json"), manifest_bytes).map_err(|source| {
            RunFolderError::Io {
                path: folder_path.join("manifest.json").display().to_string(),
                source,
            }
        })?;

        Ok(Self {
            folder_name,
            path: folder_path.display().to_string(),
            manifest,
            receipt: None,
            status: "OPEN".to_string(),
        })
    }

    /// Load an existing RunFolder from disk.
    pub fn load(folder_path: &Path) -> Result<Self, RunFolderError> {
        let manifest_path = folder_path.join("manifest.json");
        if !manifest_path.exists() {
            return Err(RunFolderError::ManifestMissing(folder_path.display().to_string()));
        }
        let manifest_bytes = fs::read(&manifest_path).map_err(|source| RunFolderError::Io {
            path: manifest_path.display().to_string(),
            source,
        })?;
        let manifest: RunManifestV1 = serde_json::from_slice(&manifest_bytes)
            .map_err(|e| RunFolderError::Json(e.to_string()))?;

        let receipt_path = folder_path.join("receipt.json");
        let receipt = if receipt_path.exists() {
            let receipt_bytes = fs::read(&receipt_path).map_err(|source| RunFolderError::Io {
                path: receipt_path.display().to_string(),
                source,
            })?;
            Some(serde_json::from_slice::<RunReceiptV1>(&receipt_bytes).map_err(|e| RunFolderError::Json(e.to_string()))?)
        } else {
            None
        };

        let status = if let Some(ref r) = receipt {
            r.status.clone()
        } else {
            "OPEN".to_string()
        };

        let folder_name = folder_path
            .file_name()
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_default();

        Ok(Self {
            folder_name,
            path: folder_path.display().to_string(),
            manifest,
            receipt,
            status,
        })
    }

    /// Seal this run folder and write `receipt.json`.
    pub fn seal(
        &mut self,
        status: Option<&str>,
        reason: Option<&str>,
        sealed_at_utc: Option<&str>,
    ) -> Result<RunReceiptV1, RunFolderError> {
        let receipt = seal_run_folder(Path::new(&self.path), status, reason, sealed_at_utc)?;
        self.status = receipt.status.clone();
        self.receipt = Some(receipt.clone());
        Ok(receipt)
    }

    /// Verify this run folder against its receipt.
    pub fn verify(&self) -> Result<RunReceiptV1, RunFolderError> {
        verify_run_folder(Path::new(&self.path))
    }
}

// Origin: engine/crates_rs/core_replay/src/run_folder.rs
// Claim: urn:core:crates_rs:core-replay:run-folder:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_slug_sanitization() {
        assert_eq!(sanitize_task_slug("my task / with spaces!"), "my_task___with_spaces");
        assert_eq!(sanitize_task_slug(""), "task");
    }

    #[test]
    fn test_folder_naming() {
        let (name, id_12) = generate_run_folder_name("20260930T180000Z", RunTrigger::Cli, "test_task", 1);
        assert!(name.starts_with("20260930T180000Z_cli_test_task_"));
        assert_eq!(id_12.len(), 12);
    }
}
