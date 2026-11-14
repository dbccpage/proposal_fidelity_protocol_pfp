//! The bench a repair run uses on a real machine: a source tree, a run folder and local commands.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:workshop:v1
//!
//! The source tree is only read. Everything written goes under a run folder that must not exist
//! yet and must lie outside the source tree: a `workspace` with a copy of the declared sources,
//! and the kept files beside it. A check runs in the working copy as the program and arguments
//! the request gives, without a shell, with a deadline and a fixed environment profile.
//!
//! This separates a working copy from the source. It is not a sandbox: a check is a trusted
//! command chosen by the host's operator and can do whatever the operator's account can.

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, ExitStatus, Stdio};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use sha2::{Digest, Sha256};

use crate::host::Outcome;
use crate::repair::{self, relative_file, Bench, Check, Exit, Stream};
use crate::Refusal;

/// The name of the working copy inside the run folder.
pub const WORKSPACE: &str = "workspace";
/// A source file larger than this is refused.
pub const MAX_SOURCE_BYTES: u64 = 2 * 1024 * 1024;
/// How much of each output stream a record keeps as text. The hash covers the whole stream.
pub const HEAD_BYTES: usize = 4096;
/// Inherited variables a check must not see: they redirect Git or Python's bytecode cache.
pub const SCRUBBED: [&str; 12] = [
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "PYTHONPYCACHEPREFIX",
    "PYTHONOPTIMIZE",
];
/// Variables every check gets. A same-size edit must not be hidden by stale bytecode.
pub const PINNED: [(&str, &str); 2] = [
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("GIT_CONFIG_NOSYSTEM", "1"),
];

const POLL: Duration = Duration::from_millis(10);
const UNAVAILABLE: &str = "CHECK_UNAVAILABLE";

fn refuse<T>(code: &'static str, message: impl Into<String>) -> Result<T, Refusal> {
    Err(Refusal::new(code, message))
}

fn failed<'a>(code: &'static str, path: &'a Path) -> impl Fn(std::io::Error) -> Refusal + 'a {
    move |error| Refusal::new(code, format!("{}: {error}", path.display()))
}

/// Read a stream to its end: the hash of every byte and the first [`HEAD_BYTES`] as text.
pub fn stream(mut reader: impl Read) -> Stream {
    let mut hasher = Sha256::new();
    let mut head = Vec::new();
    let mut total = 0;
    let mut chunk = [0; 8192];
    while let Ok(count @ 1..) = reader.read(&mut chunk) {
        let bytes = chunk.get(..count).unwrap_or_default();
        hasher.update(bytes);
        let room = HEAD_BYTES.saturating_sub(head.len());
        head.extend(bytes.iter().take(room));
        total += count;
    }
    Stream {
        sha256: hex::encode(hasher.finalize()),
        head: String::from_utf8_lossy(&head).into_owned(),
        truncated: total > HEAD_BYTES,
    }
}

/// A source tree to read and a run folder to write.
#[derive(Debug)]
pub struct Workshop {
    source: PathBuf,
    run: PathBuf,
    opened: bool,
}

impl Workshop {
    /// Bind a source tree and a run folder. Nothing is created yet.
    pub fn new(source: &Path, run: &Path) -> Result<Self, Refusal> {
        let source = fs::canonicalize(source).map_err(failed("SOURCE_ROOT_REFUSED", source))?;
        if !source.is_dir() {
            return refuse(
                "SOURCE_ROOT_REFUSED",
                format!("{} is not a folder", source.display()),
            );
        }
        let (Some(parent), Some(name)) = (run.parent(), run.file_name()) else {
            return refuse("OUTPUT_SCOPE_REFUSED", "the run folder needs a name");
        };
        let parent = if parent.as_os_str().is_empty() {
            Path::new(".")
        } else {
            parent
        };
        let run = fs::canonicalize(parent)
            .map_err(failed("OUTPUT_SCOPE_REFUSED", parent))?
            .join(name);
        if run.starts_with(&source) || source.starts_with(&run) {
            return refuse(
                "OUTPUT_SCOPE_REFUSED",
                "the run folder must be outside the source tree",
            );
        }
        Ok(Self {
            source,
            run,
            opened: false,
        })
    }

    fn workspace(&self) -> PathBuf {
        self.run.join(WORKSPACE)
    }

    /// Create the run folder. It must not exist: a run never writes into another run.
    fn ensure_run(&mut self) -> Result<(), Refusal> {
        if !self.opened {
            fs::create_dir(&self.run).map_err(failed("OUTPUT_CONFLICT", &self.run))?;
            self.opened = true;
        }
        Ok(())
    }

    fn keep_new(&self, name: &str, bytes: &[u8]) -> Result<(), Refusal> {
        relative_file(name)?;
        let path = self.run.join(name);
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .and_then(|mut file| file.write_all(bytes))
            .map_err(failed("OUTPUT_CONFLICT", &path))
    }
}

/// The path of a declared file under `root`, refused when a link or a non-file is on the way.
fn plain(root: &Path, relative: &str) -> Result<PathBuf, Refusal> {
    relative_file(relative)?;
    let mut path = root.to_path_buf();
    let mut kind = None;
    for part in relative.split('/') {
        path.push(part);
        let found = fs::symlink_metadata(&path).map_err(failed("SOURCE_FILE_REFUSED", &path))?;
        if found.file_type().is_symlink() {
            return refuse(
                "SOURCE_LINK_REFUSED",
                format!("{relative} goes through a link"),
            );
        }
        kind = Some(found);
    }
    match kind {
        Some(found) if found.is_file() && found.len() <= MAX_SOURCE_BYTES => Ok(path),
        _ => refuse(
            "SOURCE_FILE_REFUSED",
            format!("{relative} is not a regular file of at most {MAX_SOURCE_BYTES} bytes"),
        ),
    }
}

fn read_plain(root: &Path, relative: &str) -> Result<Vec<u8>, Refusal> {
    let path = plain(root, relative)?;
    fs::read(&path).map_err(failed("SOURCE_FILE_REFUSED", &path))
}

fn reader(pipe: Option<impl Read + Send + 'static>) -> JoinHandle<Stream> {
    thread::spawn(move || pipe.map(stream).unwrap_or_default())
}

/// Wait for the child until the deadline; a child still running then is stopped.
fn waited(child: &mut Child, deadline: Instant) -> Option<ExitStatus> {
    loop {
        match child.try_wait() {
            Ok(Some(status)) => return Some(status),
            Ok(None) if Instant::now() < deadline => thread::sleep(POLL),
            _ => {
                let _ = child.kill();
                let _ = child.wait();
                return None;
            }
        }
    }
}

impl Bench for Workshop {
    fn source(&mut self, path: &str) -> Result<Vec<u8>, Refusal> {
        read_plain(&self.source, path)
    }

    fn open(
        &mut self,
        files: &BTreeMap<String, Vec<u8>>,
        kept: &[(&str, Vec<u8>)],
    ) -> Result<(), Refusal> {
        self.ensure_run()?;
        let workspace = self.workspace();
        for (name, bytes) in files {
            relative_file(name)?;
            let target = workspace.join(name);
            let folder = target.parent().unwrap_or(&workspace);
            fs::create_dir_all(folder)
                .and_then(|()| fs::write(&target, bytes))
                .map_err(failed("IO_UNAVAILABLE", &target))?;
        }
        kept.iter()
            .try_for_each(|(name, bytes)| self.keep_new(name, bytes))
    }

    fn copy(&mut self, path: &str) -> Result<Vec<u8>, Refusal> {
        read_plain(&self.workspace(), path)
    }

    fn write(&mut self, path: &str, bytes: &[u8]) -> Result<(), Refusal> {
        let target = plain(&self.workspace(), path)?;
        fs::write(&target, bytes).map_err(failed("IO_UNAVAILABLE", &target))
    }

    fn run(&mut self, check: &Check) -> Result<Exit, Refusal> {
        let unavailable =
            |why: String| Refusal::new(UNAVAILABLE, format!("{}: {why}", check.check_id));
        let Some((program, arguments)) = check.argv.split_first() else {
            return Err(unavailable("no program".to_owned()));
        };
        let mut command = Command::new(program);
        command
            .args(arguments)
            .current_dir(self.workspace())
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .envs(PINNED)
            .env(
                "GIT_CONFIG_GLOBAL",
                if cfg!(windows) { "NUL" } else { "/dev/null" },
            );
        for name in SCRUBBED {
            command.env_remove(name);
        }
        let mut child = command
            .spawn()
            .map_err(|error| unavailable(error.to_string()))?;
        let (stdout, stderr) = (reader(child.stdout.take()), reader(child.stderr.take()));
        let limit = Duration::from_secs(u64::from(check.timeout_seconds));
        let Some(status) = waited(&mut child, Instant::now() + limit) else {
            return Err(unavailable(format!(
                "no exit within {} s",
                check.timeout_seconds
            )));
        };
        let Some(code) = status.code() else {
            return Err(unavailable("ended without an exit code".to_owned()));
        };
        match (stdout.join(), stderr.join()) {
            (Ok(stdout), Ok(stderr)) => Ok(Exit {
                code,
                stdout,
                stderr,
            }),
            _ => Err(unavailable("its output could not be read".to_owned())),
        }
    }

    fn keep(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal> {
        self.ensure_run()?;
        self.keep_new(name, bytes)
    }
}

/// Run one repair request on a source tree, with everything kept under a new run folder.
pub fn repair_in(request: &str, source: &Path, run: &Path) -> Outcome {
    match Workshop::new(source, run) {
        Ok(mut bench) => repair::respond(request, &mut bench),
        Err(refusal) => Outcome::Refused { refusal },
    }
}
