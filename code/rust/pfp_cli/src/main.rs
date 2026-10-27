//! The `pfp` command line: argument parsing, file reading and printing.
//!
//! AuthorityEffect: None. Safety contract, enforced by tests:
//! - reads only the files you name (and, for replay, the files the packet names
//!   below `--root`); never follows a `..` or an absolute path from a packet;
//! - writes only with `pfp seal --out PATH`, and never over an existing file;
//! - no network, no subprocesses, no environment changes.
//!
//! Exit codes: 0 nothing found, 1 findings or mismatches, 2 could not run.

use pfp_cli::{catalog, check, packet, Input, Text};
use std::fs::{File, OpenOptions};
use std::io::{self, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;

/// Larger inputs are refused rather than read into memory.
const MAX_INPUT_BYTES: u64 = 10 * 1024 * 1024;

const HELP: &str = "\
pfp: find what your prompt and your model's reply leave to chance.
Offline. Read-only unless you pass --out. AuthorityEffect: None.

USAGE
  pfp check [FILE ...] [--prompt FILE] [--json]
      Check model outputs (text or JSON) and, with --prompt, the prompt.
      Use - to read one output from stdin.
  pfp seal FILE ... [--out PACKET]
      Print a packet: the SHA-256 of each file. --out writes it to a new file.
  pfp replay PACKET [--root DIR]
      Check that the files on disk still match the packet.
  pfp explain [CODE]
      What a code means and what to do. No CODE lists them all.
  pfp demo
      Run check on a bundled prompt and reply.

EXIT CODES
  0 nothing found   1 findings or mismatches   2 could not run
";

/// A failure to run, printed as `pfp: ...` with exit code 2.
struct Fail(String);

impl<E: std::fmt::Display> From<E> for Fail {
    fn from(e: E) -> Self {
        Self(e.to_string())
    }
}

type Run = Result<ExitCode, Fail>;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match dispatch(&args) {
        Ok(code) => code,
        Err(Fail(message)) => {
            eprintln!("pfp: {message}");
            ExitCode::from(2)
        }
    }
}

fn dispatch(args: &[String]) -> Run {
    let (command, rest) = match args.split_first() {
        Some((c, rest)) => (c.as_str(), rest),
        None => ("help", &[][..]),
    };
    match command {
        "check" => cmd_check(rest),
        "seal" => cmd_seal(rest),
        "replay" => cmd_replay(rest),
        "explain" => cmd_explain(rest),
        "demo" => cmd_demo(rest),
        "help" | "-h" | "--help" => print(HELP, ExitCode::SUCCESS),
        "-V" | "--version" => print(&format!("{}\n", pfp_cli::TOOL), ExitCode::SUCCESS),
        other => Err(Fail(format!("unknown command {other:?}; try `pfp help`"))),
    }
}

/// Parsed arguments: positionals plus the named options a command allows.
struct Args {
    positional: Vec<String>,
    options: Vec<(String, String)>,
    flags: Vec<String>,
}

impl Args {
    fn option(&self, name: &str) -> Option<&str> {
        self.options
            .iter()
            .find(|(k, _)| k == name)
            .map(|(_, v)| v.as_str())
    }

    fn flag(&self, name: &str) -> bool {
        self.flags.iter().any(|f| f == name)
    }
}

/// Split `args` into positionals, `--name VALUE` options and `--flag` flags.
/// Anything not listed is refused, so a typo never silently changes behavior.
fn parse(args: &[String], options: &[&str], flags: &[&str]) -> Result<Args, Fail> {
    let mut parsed = Args {
        positional: Vec::new(),
        options: Vec::new(),
        flags: Vec::new(),
    };
    let mut iter = args.iter();
    while let Some(arg) = iter.next() {
        let name = arg.as_str();
        if options.contains(&name) {
            let value = iter
                .next()
                .ok_or_else(|| Fail(format!("{name} needs a value")))?;
            if parsed.option(name).is_some() {
                return Err(Fail(format!("{name} given twice")));
            }
            parsed.options.push((name.to_owned(), value.clone()));
        } else if flags.contains(&name) {
            parsed.flags.push(name.to_owned());
        } else if name.starts_with("--") || (name.starts_with('-') && name != "-") {
            return Err(Fail(format!("unknown option {name:?}; try `pfp help`")));
        } else {
            parsed.positional.push(arg.clone());
        }
    }
    Ok(parsed)
}

fn print(text: &str, code: ExitCode) -> Run {
    let mut out = io::stdout().lock();
    // A closed pipe (`pfp check x | head`) is not an error worth a message.
    let _ = out.write_all(text.as_bytes());
    let _ = out.flush();
    Ok(code)
}

fn read_limited(mut reader: impl Read, name: &str) -> Result<Vec<u8>, Fail> {
    let mut bytes = Vec::new();
    reader
        .by_ref()
        .take(MAX_INPUT_BYTES + 1)
        .read_to_end(&mut bytes)?;
    if bytes.len() as u64 > MAX_INPUT_BYTES {
        return Err(Fail(format!(
            "{name} is larger than {MAX_INPUT_BYTES} bytes"
        )));
    }
    Ok(bytes)
}

fn read_file(path: &Path) -> Result<Vec<u8>, Fail> {
    let name = path.display().to_string();
    let file = File::open(path).map_err(|e| Fail(format!("cannot read {name}: {e}")))?;
    read_limited(file, &name)
}

/// Read a file (or stdin for `-`) as UTF-8 text. A UTF-8 byte order mark is dropped.
fn read_text(name: &str) -> Result<Text, Fail> {
    let bytes = if name == "-" {
        read_limited(io::stdin().lock(), "stdin")?
    } else {
        read_file(Path::new(name))?
    };
    let body = String::from_utf8(bytes).map_err(|_| Fail(format!("{name} is not UTF-8 text")))?;
    let body = body
        .strip_prefix('\u{feff}')
        .map(str::to_owned)
        .unwrap_or(body);
    Ok(Text {
        name: name.to_owned(),
        body,
    })
}

fn use_color() -> bool {
    io::stdout().is_terminal() && std::env::var_os("NO_COLOR").is_none()
}

fn report_exit(report: &pfp_cli::Report) -> ExitCode {
    if report.findings.is_empty() {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(1)
    }
}

fn cmd_check(args: &[String]) -> Run {
    let args = parse(args, &["--prompt"], &["--json"])?;
    if args.positional.iter().filter(|p| *p == "-").count() > 1 {
        return Err(Fail("stdin (-) can be read once".to_owned()));
    }
    let input = Input {
        prompt: args.option("--prompt").map(read_text).transpose()?,
        outputs: args
            .positional
            .iter()
            .map(|p| read_text(p))
            .collect::<Result<_, _>>()?,
    };
    if input.prompt.is_none() && input.outputs.is_empty() {
        return Err(Fail(
            "name a file to check, or --prompt FILE; try `pfp demo`".to_owned(),
        ));
    }
    let report = check::run_checks(&check::builtin_checks(), &input);
    let text = if args.flag("--json") {
        serde_json::to_string_pretty(&report)? + "\n"
    } else {
        pfp_cli::render_report(&report, use_color())
    };
    print(&text, report_exit(&report))
}

fn cmd_demo(args: &[String]) -> Run {
    parse(args, &[], &[])?;
    let input = Input {
        prompt: Some(Text {
            name: "demo/prompt.md".to_owned(),
            body: pfp_cli::DEMO_PROMPT.to_owned(),
        }),
        outputs: vec![Text {
            name: "demo/reply.json".to_owned(),
            body: pfp_cli::DEMO_REPLY.to_owned(),
        }],
    };
    let report = check::run_checks(&check::builtin_checks(), &input);
    let intro = format!(
        "$ pfp check --prompt demo/prompt.md demo/reply.json\n\n--- demo/prompt.md ---\n{}\n--- demo/reply.json ---\n{}\n",
        pfp_cli::DEMO_PROMPT,
        pfp_cli::DEMO_REPLY
    );
    // The demo succeeding is the point, so it exits 0 even with findings.
    print(
        &(intro + &pfp_cli::render_report(&report, use_color())),
        ExitCode::SUCCESS,
    )
}

fn cmd_seal(args: &[String]) -> Run {
    let args = parse(args, &["--out"], &[])?;
    let mut files = Vec::new();
    for name in &args.positional {
        packet::normalize_path(name)
            .map_err(|p| Fail(format!("{}: {} ({})", p.code, p.message, name)))?;
        files.push((name.clone(), read_file(Path::new(name))?));
    }
    let envelope = packet::seal(&files, pfp_cli::TOOL)
        .map_err(|p| Fail(format!("{}: {}", p.code, p.message)))?;
    let json = serde_json::to_string_pretty(&envelope)? + "\n";
    let Some(out) = args.option("--out") else {
        return print(&json, ExitCode::SUCCESS);
    };
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(out)
        .map_err(|e| Fail(format!("will not write {out}: {e} (pfp never overwrites)")))?;
    file.write_all(json.as_bytes())?;
    print(
        &format!(
            "Sealed {} into {out}\n",
            pfp_cli::count(envelope.files.len(), "file")
        ),
        ExitCode::SUCCESS,
    )
}

fn cmd_replay(args: &[String]) -> Run {
    let args = parse(args, &["--root"], &[])?;
    let [packet_path] = args.positional.as_slice() else {
        return Err(Fail("name exactly one packet file".to_owned()));
    };
    let root = PathBuf::from(args.option("--root").unwrap_or("."));
    let bytes = read_file(Path::new(packet_path))?;
    let envelope = match packet::parse_envelope(&bytes) {
        Ok(envelope) => envelope,
        Err(p) => {
            return print(
                &format!("  REFUSE   {}  {}\n", p.code, p.message),
                ExitCode::from(1),
            )
        }
    };
    let problems = packet::replay(&envelope, |path| match read_file(&root.join(path)) {
        Ok(bytes) => packet::OnDisk::Bytes(bytes),
        Err(_) => packet::OnDisk::Missing,
    });
    let mut out = String::new();
    for p in &problems {
        out.push_str(&format!(
            "  REFUSE   {}  {}  {}\n",
            p.code, p.path, p.message
        ));
    }
    let n = envelope.files.len();
    if problems.is_empty() {
        out.push_str(&format!(
            "{} match the packet byte for byte.\n",
            pfp_cli::count(n, "file")
        ));
        print(&out, ExitCode::SUCCESS)
    } else {
        out.push_str(&format!(
            "{} of {} do not match. Nothing was changed.\n",
            problems.len(),
            pfp_cli::count(n, "file")
        ));
        print(&out, ExitCode::from(1))
    }
}

fn cmd_explain(args: &[String]) -> Run {
    let args = parse(args, &[], &[])?;
    match args.positional.as_slice() {
        [] => {
            let mut out = String::from("Codes (pfp explain CODE for details):\n");
            for e in &catalog::ENTRIES {
                out.push_str(&format!("  {:<28} {}\n", e.code, e.what));
            }
            print(&out, ExitCode::SUCCESS)
        }
        [code] => match catalog::find(code) {
            Some(entry) => print(&pfp_cli::render_explain(entry), ExitCode::SUCCESS),
            None => Err(Fail(format!("no code {code:?}; `pfp explain` lists them"))),
        },
        _ => Err(Fail("explain takes one code".to_owned())),
    }
}
