//! The `pfp` command line: argument parsing, file reading and printing.
//!
//! AuthorityEffect: None. Safety contract, enforced by tests:
//! - reads only regular files you name, plus stdin once; for replay, only the
//!   regular files a packet names that resolve inside `--root`;
//! - writes only with `pfp seal --out PATH`, and never over an existing file;
//! - no network, no subprocesses, no environment changes;
//! - escapes control characters in anything it echoes from a file or a packet.
//!
//! Exit codes: 0 nothing found, 1 findings or mismatches, 2 could not run.

use pfp_cli::skills::{self, Licence};
use pfp_cli::{catalog, check, clean, count, packet, Input, Text};
use std::ffi::OsString;
use std::fs::{self, File, OpenOptions};
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
      Use - to read one input from stdin.
  pfp seal FILE ... [--out PACKET]
      Print a packet: the SHA-256 of each file. --out writes it to a new file.
  pfp replay PACKET [--root DIR]
      Check that the files on disk still match the packet.
  pfp explain [CODE]
      What a code means and what to do. No CODE lists them all.
  pfp demo
      Run check on a bundled prompt and reply.
  pfp skills --catalog FILE [--json]
      Count bound and unbound skills in a compiled skill catalogue.
  pfp licence ROLE SKILL --catalog FILE
      Whether the catalogue licenses ROLE to use SKILL (exit 1 if not).
  pfp export --mcp --catalog FILE
      Print the bound skills as MCP tool definitions.

EXIT CODES
  0 nothing found   1 findings or mismatches   2 could not run
";

/// A failure to run, printed as `pfp: ...` with exit code 2.
struct Fail(String);

fn fail<T>(message: impl Into<String>) -> Result<T, Fail> {
    Err(Fail(message.into()))
}

type Run = Result<ExitCode, Fail>;

fn main() -> ExitCode {
    let args: Option<Vec<String>> = std::env::args_os()
        .skip(1)
        .map(|a: OsString| a.into_string().ok())
        .collect();
    let result = match args {
        Some(args) => dispatch(&args),
        None => fail("arguments must be valid Unicode"),
    };
    match result {
        Ok(code) => code,
        Err(Fail(message)) => {
            eprintln!("pfp: {}", clean(&message));
            ExitCode::from(2)
        }
    }
}

fn dispatch(args: &[String]) -> Run {
    if args
        .iter()
        .take_while(|a| *a != "--")
        .any(|a| a == "-h" || a == "--help")
    {
        return print(HELP, ExitCode::SUCCESS);
    }
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
        "skills" => cmd_skills(rest),
        "licence" | "license" => cmd_licence(rest),
        "export" => cmd_export(rest),
        "help" => print(HELP, ExitCode::SUCCESS),
        "-V" | "--version" => print(&format!("{}\n", pfp_cli::TOOL), ExitCode::SUCCESS),
        other => fail(format!("unknown command {other:?}; try `pfp help`")),
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
/// After `--`, everything is a positional (for a file named `--json`).
fn parse(args: &[String], options: &[&str], flags: &[&str]) -> Result<Args, Fail> {
    let mut parsed = Args {
        positional: Vec::new(),
        options: Vec::new(),
        flags: Vec::new(),
    };
    let mut iter = args.iter();
    while let Some(arg) = iter.next() {
        let name = arg.as_str();
        if name == "--" {
            parsed.positional.extend(iter.by_ref().cloned());
        } else if options.contains(&name) {
            let Some(value) = iter.next() else {
                return fail(format!("{name} needs a value"));
            };
            if parsed.option(name).is_some() {
                return fail(format!("{name} given twice"));
            }
            parsed.options.push((name.to_owned(), value.clone()));
        } else if flags.contains(&name) {
            parsed.flags.push(name.to_owned());
        } else if name.starts_with('-') && name != "-" {
            return fail(format!("unknown option {name:?}; try `pfp help`"));
        } else {
            parsed.positional.push(arg.clone());
        }
    }
    Ok(parsed)
}

/// Write to stdout. A closed pipe (`pfp check x | head`) is fine; any other
/// write error (a full disk) means the output was lost, so it fails the run.
fn print(text: &str, code: ExitCode) -> Run {
    let mut out = io::stdout().lock();
    match out.write_all(text.as_bytes()).and_then(|()| out.flush()) {
        Err(e) if e.kind() != io::ErrorKind::BrokenPipe => {
            fail(format!("cannot write output: {e}"))
        }
        _ => Ok(code),
    }
}

fn read_limited(reader: impl Read, name: &str) -> Result<Vec<u8>, Fail> {
    let mut bytes = Vec::new();
    reader
        .take(MAX_INPUT_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| Fail(format!("cannot read {name}: {e}")))?;
    if bytes.len() as u64 > MAX_INPUT_BYTES {
        return fail(format!("{name} is larger than {MAX_INPUT_BYTES} bytes"));
    }
    Ok(bytes)
}

/// Read a regular file. Directories, FIFOs and devices are refused, so a
/// read can neither hang nor stream forever.
fn read_file(path: &Path) -> Result<Vec<u8>, Fail> {
    let name = path.display().to_string();
    match fs::metadata(path) {
        Ok(meta) if meta.is_file() => {}
        Ok(_) => return fail(format!("{name} is not a regular file")),
        Err(e) => return fail(format!("cannot read {name}: {e}")),
    }
    let file = File::open(path).map_err(|e| Fail(format!("cannot read {name}: {e}")))?;
    read_limited(file, &name)
}

/// Read a file (or stdin for `-`) as UTF-8 text.
fn read_text(name: &str) -> Result<Text, Fail> {
    let bytes = if name == "-" {
        read_limited(io::stdin().lock(), "stdin")?
    } else {
        read_file(Path::new(name))?
    };
    let body = String::from_utf8(bytes).map_err(|_| Fail(format!("{name} is not UTF-8 text")))?;
    Ok(Text {
        name: name.to_owned(),
        body,
    })
}

fn read_doc(text: &Text) -> Result<pfp_cli::Doc, Fail> {
    pfp_cli::read_doc(text).map_err(|e| {
        Fail(format!(
            "{} has {} JSON values; the limit is {}",
            e.name,
            e.values,
            check::MAX_JSON_VALUES
        ))
    })
}

fn use_color() -> bool {
    io::stdout().is_terminal() && std::env::var_os("NO_COLOR").is_none()
}

fn run_and_render(input: &Input, json: bool) -> Result<(String, ExitCode), Fail> {
    let report = check::run_checks(&check::builtin_checks(), input);
    let code = if report.findings.is_empty() {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(1)
    };
    let text = if json {
        serde_json::to_string_pretty(&report).map_err(|e| Fail(e.to_string()))? + "\n"
    } else {
        pfp_cli::render_report(&report, use_color())
    };
    Ok((text, code))
}

fn cmd_check(args: &[String]) -> Run {
    let args = parse(args, &["--prompt"], &["--json"])?;
    let prompt = args.option("--prompt");
    let stdin_uses = args
        .positional
        .iter()
        .map(String::as_str)
        .chain(prompt)
        .filter(|p| *p == "-")
        .count();
    if stdin_uses > 1 {
        return fail("stdin (-) can be read once");
    }
    if prompt.is_none() && args.positional.is_empty() {
        return fail("name a file to check, or --prompt FILE; try `pfp demo`");
    }
    let mut outputs = Vec::new();
    for name in &args.positional {
        outputs.push(read_doc(&read_text(name)?)?);
    }
    let input = Input {
        prompt: prompt.map(read_text).transpose()?,
        outputs,
    };
    let (text, code) = run_and_render(&input, args.flag("--json"))?;
    print(&text, code)
}

fn cmd_demo(args: &[String]) -> Run {
    parse(args, &[], &[])?;
    let reply = Text {
        name: "demo/reply.json".to_owned(),
        body: pfp_cli::DEMO_REPLY.to_owned(),
    };
    let input = Input {
        prompt: Some(Text {
            name: "demo/prompt.md".to_owned(),
            body: pfp_cli::DEMO_PROMPT.to_owned(),
        }),
        outputs: vec![read_doc(&reply)?],
    };
    let (report, _) = run_and_render(&input, false)?;
    let intro = format!(
        "--- demo/prompt.md ---\n{}\n--- demo/reply.json ---\n{}\n$ pfp check --prompt demo/prompt.md demo/reply.json\n",
        pfp_cli::DEMO_PROMPT,
        pfp_cli::DEMO_REPLY
    );
    // The demo succeeding is the point, so it exits 0 even with findings.
    print(&(intro + &report), ExitCode::SUCCESS)
}

/// Where a relative path really leads, following links.
enum Resolved {
    Inside(PathBuf),
    Outside,
    Missing,
}

/// `root` must already be canonical.
fn resolve(root: &Path, relative: &str) -> Resolved {
    match root.join(relative).canonicalize() {
        Ok(real) if real.starts_with(root) => Resolved::Inside(real),
        Ok(_) => Resolved::Outside,
        Err(_) => Resolved::Missing,
    }
}

fn canonical_dir(dir: &str) -> Result<PathBuf, Fail> {
    match Path::new(dir).canonicalize() {
        Ok(path) if path.is_dir() => Ok(path),
        _ => fail(format!("{dir} is not a folder")),
    }
}

fn cmd_seal(args: &[String]) -> Run {
    let args = parse(args, &["--out"], &[])?;
    let out = args.option("--out");
    if out == Some("-") {
        return fail("without --out the packet is printed; --out takes a file name");
    }
    let root = canonical_dir(".")?;
    let mut files = Vec::new();
    for name in &args.positional {
        let path = packet::normalize_path(name)
            .map_err(|p| Fail(format!("{}: {} ({name})", p.code, p.message)))?;
        let real = match resolve(&root, &path) {
            Resolved::Inside(real) => real,
            Resolved::Outside => {
                return fail(format!(
                    "PATH_OUTSIDE_ROOT: {name} leads outside the current folder"
                ))
            }
            Resolved::Missing => return fail(format!("cannot read {name}: no such file")),
        };
        files.push((path, read_file(&real)?));
    }
    let envelope = packet::seal(&files, pfp_cli::TOOL)
        .map_err(|p| Fail(format!("{}: {}", p.code, p.message)))?;
    let json = serde_json::to_string_pretty(&envelope).map_err(|e| Fail(e.to_string()))? + "\n";
    let Some(out) = out else {
        return print(&json, ExitCode::SUCCESS);
    };
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(out)
        .map_err(|e| Fail(format!("will not write {out}: {e} (pfp never overwrites)")))?;
    file.write_all(json.as_bytes())
        .map_err(|e| Fail(format!("cannot write {out}: {e}")))?;
    print(
        &format!(
            "Sealed {} into {out}\n",
            count(envelope.files.len(), "file")
        ),
        ExitCode::SUCCESS,
    )
}

fn cmd_replay(args: &[String]) -> Run {
    let args = parse(args, &["--root"], &[])?;
    let [packet_path] = args.positional.as_slice() else {
        return fail("name exactly one packet file");
    };
    let root = canonical_dir(args.option("--root").unwrap_or("."))?;
    let bytes = read_file(Path::new(packet_path))?;
    let envelope = match packet::parse_envelope(&bytes) {
        Ok(envelope) => envelope,
        Err(p) if p.code == "ENVELOPE_TAMPERED" => {
            return print(
                &format!("  REFUSE   {}  {}\n", p.code, p.message),
                ExitCode::from(1),
            );
        }
        Err(p) => return fail(format!("{}: {} {}", p.code, p.path, p.message)),
    };
    let problems = packet::replay(&envelope, |path| match resolve(&root, path) {
        Resolved::Inside(real) => {
            read_file(&real).map_or(packet::OnDisk::Missing, packet::OnDisk::Bytes)
        }
        Resolved::Outside => packet::OnDisk::Outside,
        Resolved::Missing => packet::OnDisk::Missing,
    });
    let mut out = String::new();
    for p in &problems {
        out.push_str(&format!(
            "  REFUSE   {}  {}  {}\n",
            p.code,
            clean(&p.path),
            p.message
        ));
    }
    let n = envelope.files.len();
    if problems.is_empty() {
        let verb = if n == 1 { "matches" } else { "match" };
        out.push_str(&format!(
            "{} {verb} the packet byte for byte.\n",
            count(n, "file")
        ));
        print(&out, ExitCode::SUCCESS)
    } else {
        let verb = if problems.len() == 1 { "does" } else { "do" };
        out.push_str(&format!(
            "{} of {} {verb} not match. Nothing was changed.\n",
            problems.len(),
            count(n, "file")
        ));
        print(&out, ExitCode::from(1))
    }
}

fn read_catalog(args: &Args) -> Result<skills::Catalog, Fail> {
    let Some(name) = args.option("--catalog") else {
        return fail(
            "name the catalogue with --catalog, e.g. operads/skill_operad/json/capability_catalog.v1.json",
        );
    };
    let text = read_text(name)?;
    skills::parse_catalog(text.body.as_bytes()).map_err(|e| Fail(format!("{name}: {e}")))
}

fn to_json(value: &serde_json::Value) -> Result<String, Fail> {
    Ok(serde_json::to_string_pretty(value).map_err(|e| Fail(e.to_string()))? + "\n")
}

fn cmd_skills(args: &[String]) -> Run {
    let args = parse(args, &["--catalog"], &["--json"])?;
    if !args.positional.is_empty() {
        return fail("skills takes no file names; use --catalog FILE");
    }
    let catalog = read_catalog(&args)?;
    if !args.flag("--json") {
        return print(&skills::render_summary(&catalog), ExitCode::SUCCESS);
    }
    let bound = catalog.skills.iter().filter(|s| s.is_bound()).count();
    let summary = serde_json::json!({
        "skills": catalog.skills.len(),
        "bound": bound,
        "unbound": catalog.skills.len() - bound,
        "agents": catalog.agents.len(),
        "authority_effect": "None",
    });
    print(&to_json(&summary)?, ExitCode::SUCCESS)
}

fn cmd_licence(args: &[String]) -> Run {
    let args = parse(args, &["--catalog"], &[])?;
    let [role, skill] = args.positional.as_slice() else {
        return fail("licence takes a ROLE and a SKILL");
    };
    let catalog = read_catalog(&args)?;
    let (role_shown, skill_shown) = (clean(role), clean(skill));
    match skills::licence(&catalog, role, skill) {
        Licence::Licensed => print(
            &format!("{role_shown} is licensed to use {skill_shown}.\n"),
            ExitCode::SUCCESS,
        ),
        Licence::NotLicensed { outside } => print(
            &format!(
                "  REFUSE   UNLICENSED_SKILL  {role_shown} may not use {skill_shown}: {} outside its licence.\n",
                outside.join(", ")
            ),
            ExitCode::from(1),
        ),
        Licence::UnknownAgent => fail(format!("no role {role_shown:?} in the catalogue")),
        Licence::UnknownSkill => fail(format!("no skill {skill_shown:?} in the catalogue")),
    }
}

fn cmd_export(args: &[String]) -> Run {
    let args = parse(args, &["--catalog"], &["--mcp"])?;
    if !args.flag("--mcp") || !args.positional.is_empty() {
        return fail("export needs --mcp (the only format) and --catalog FILE");
    }
    let catalog = read_catalog(&args)?;
    print(&to_json(&skills::mcp_tools(&catalog))?, ExitCode::SUCCESS)
}

fn cmd_explain(args: &[String]) -> Run {
    let args = parse(args, &[], &[])?;
    match args.positional.as_slice() {
        [] => {
            let mut out = String::from("Codes (pfp explain CODE for details):\n");
            for e in catalog::ENTRIES {
                out.push_str(&format!("  {:<28} {}\n", e.code, e.short));
            }
            print(&out, ExitCode::SUCCESS)
        }
        [code] => match catalog::find(code) {
            Some(entry) => print(&pfp_cli::render_explain(entry), ExitCode::SUCCESS),
            None => fail(format!("no code {code:?}; `pfp explain` lists them")),
        },
        _ => fail("explain takes one code"),
    }
}
