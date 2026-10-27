//! Packets: seal named bytes into an envelope, and replay an envelope against
//! the bytes on disk.
//!
//! AuthorityEffect: None. An envelope records which bytes were proposed. Its
//! hashes catch accidental or naive edits; they are not a signature, and anyone
//! can recompute them, so a matching replay proves the bytes are unchanged and
//! nothing about who sealed them or whether they are right.
//!
//! Pure: callers do all file reading, so this module also runs in the browser.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const FORMAT: &str = "pfp.packet.v1";

/// One sealed file.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Entry {
    /// Relative path with `/` separators, as given at seal time.
    pub path: String,
    pub bytes: u64,
    pub sha256: String,
}

/// The sealed envelope. Field order is fixed, so its JSON bytes are canonical.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Envelope {
    pub format: String,
    pub authority_effect: String,
    pub tool: String,
    pub files: Vec<Entry>,
    /// SHA-256 over `"<sha256>  <path>\n"` for every entry, in path order.
    pub payload_sha256: String,
    /// SHA-256 over the compact JSON of this envelope with this field empty.
    pub envelope_sha256: String,
}

/// Why a seal or replay could not go ahead, or what a replay found.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Problem {
    pub code: &'static str,
    pub path: String,
    pub message: String,
}

impl Problem {
    fn new(code: &'static str, path: &str, message: impl Into<String>) -> Self {
        Self {
            code,
            path: path.to_owned(),
            message: message.into(),
        }
    }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

/// Windows device names: opening one reads a device, not a file.
const RESERVED: [&str; 22] = [
    "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8",
    "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
];

fn bad_part(part: &str) -> bool {
    let stem = part.split('.').next().unwrap_or(part).to_ascii_uppercase();
    part.is_empty() || part == "." || part == ".." || RESERVED.contains(&stem.as_str())
}

/// Accept only plain relative paths: no root, no drive, no `.` or `..` parts,
/// no empty parts, no control characters, no Windows device names. A leading
/// `./` is dropped and backslashes become `/`, so a packet sealed on Windows
/// replays elsewhere.
pub fn normalize_path(raw: &str) -> Result<String, Problem> {
    let slashed = raw.replace('\\', "/");
    let path = slashed.strip_prefix("./").unwrap_or(&slashed);
    let drive = path.as_bytes().get(1) == Some(&b':');
    let bad = path.starts_with('/')
        || drive
        || path.chars().any(char::is_control)
        || path.split('/').any(bad_part);
    if bad {
        return Err(Problem::new(
            "PATH_OUTSIDE_ROOT",
            raw,
            "use a plain relative path below the current folder (no `..`, no absolute path, no device name)",
        ));
    }
    Ok(path.to_owned())
}

fn payload_digest(files: &[Entry]) -> String {
    let mut listing = String::new();
    for entry in files {
        listing.push_str(&entry.sha256);
        listing.push_str("  ");
        listing.push_str(&entry.path);
        listing.push('\n');
    }
    sha256_hex(listing.as_bytes())
}

fn envelope_digest(envelope: &Envelope) -> String {
    let mut blank = envelope.clone();
    blank.envelope_sha256 = String::new();
    // Serializing a struct of strings and integers cannot fail.
    sha256_hex(&serde_json::to_vec(&blank).unwrap_or_default())
}

/// Seal `(path, bytes)` pairs. Paths must be relative and distinct.
pub fn seal(files: &[(String, Vec<u8>)], tool: &str) -> Result<Envelope, Problem> {
    let mut entries = Vec::with_capacity(files.len());
    for (raw, bytes) in files {
        entries.push(Entry {
            path: normalize_path(raw)?,
            bytes: bytes.len() as u64,
            sha256: sha256_hex(bytes),
        });
    }
    entries.sort_by(|a, b| a.path.cmp(&b.path));
    if let Some(pair) = entries.windows(2).find(|w| w[0].path == w[1].path) {
        return Err(Problem::new(
            "DUPLICATE_PATH",
            &pair[0].path,
            "each file may be sealed once",
        ));
    }
    if entries.is_empty() {
        return Err(Problem::new(
            "NOTHING_TO_SEAL",
            "",
            "name at least one file",
        ));
    }
    let mut envelope = Envelope {
        format: FORMAT.to_owned(),
        authority_effect: "None".to_owned(),
        tool: tool.to_owned(),
        payload_sha256: payload_digest(&entries),
        files: entries,
        envelope_sha256: String::new(),
    };
    envelope.envelope_sha256 = envelope_digest(&envelope);
    Ok(envelope)
}

/// Parse envelope JSON and check its own hashes. Unknown fields are refused.
pub fn parse_envelope(json: &[u8]) -> Result<Envelope, Problem> {
    let json = json.strip_prefix(b"\xef\xbb\xbf").unwrap_or(json);
    let envelope: Envelope = serde_json::from_slice(json).map_err(|e| {
        Problem::new(
            "UNSUPPORTED_FORMAT",
            "",
            format!("not a {FORMAT} envelope: {e}"),
        )
    })?;
    if envelope.format != FORMAT {
        return Err(Problem::new(
            "UNSUPPORTED_FORMAT",
            "",
            format!("format is {:?}, expected {FORMAT:?}", envelope.format),
        ));
    }
    if envelope_digest(&envelope) != envelope.envelope_sha256
        || payload_digest(&envelope.files) != envelope.payload_sha256
    {
        return Err(Problem::new(
            "ENVELOPE_TAMPERED",
            "",
            "the envelope does not match its own hashes",
        ));
    }
    for entry in &envelope.files {
        if normalize_path(&entry.path)? != entry.path {
            return Err(Problem::new(
                "PATH_OUTSIDE_ROOT",
                &entry.path,
                "path is not in normal form",
            ));
        }
    }
    // `seal` always writes at least one file, sorted by path, each once.
    if envelope.files.is_empty() || envelope.files.windows(2).any(|w| w[0].path >= w[1].path) {
        return Err(Problem::new(
            "UNSUPPORTED_FORMAT",
            "",
            "files must be non-empty, sorted and distinct",
        ));
    }
    Ok(envelope)
}

/// What the caller found on disk for one entry.
pub enum OnDisk {
    Bytes(Vec<u8>),
    Missing,
    /// The path resolves (through a link) to somewhere outside the root.
    Outside,
}

/// Compare an envelope with the bytes on disk. An empty result means every
/// file matches byte for byte.
pub fn replay(envelope: &Envelope, read: impl Fn(&str) -> OnDisk) -> Vec<Problem> {
    let mut problems = Vec::new();
    for entry in &envelope.files {
        match read(&entry.path) {
            OnDisk::Missing => {
                problems.push(Problem::new(
                    "FILE_MISSING",
                    &entry.path,
                    "the sealed file is missing or cannot be read",
                ));
            }
            OnDisk::Outside => {
                problems.push(Problem::new(
                    "PATH_OUTSIDE_ROOT",
                    &entry.path,
                    "the path leads outside the folder; it was not read",
                ));
            }
            OnDisk::Bytes(bytes) if sha256_hex(&bytes) != entry.sha256 => {
                problems.push(Problem::new(
                    "DIGEST_MISMATCH",
                    &entry.path,
                    format!(
                        "the file changed since it was sealed ({} bytes now, {} sealed)",
                        bytes.len(),
                        entry.bytes
                    ),
                ));
            }
            OnDisk::Bytes(_) => {}
        }
    }
    problems
}
