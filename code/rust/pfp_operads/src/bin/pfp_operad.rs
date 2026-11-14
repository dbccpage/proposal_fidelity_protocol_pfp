//! `pfp_operad`: the operad host as a command. Reads files, prints one JSON outcome, exits 0, 1 or 2.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:bin:v1
//!
//! ```text
//! pfp_operad laws REQUEST.json              check the operad laws on a panel
//! pfp_operad check REQUEST.json             type a model's operad candidates and run host checks
//! pfp_operad ledger verify LEDGER.jsonl     replay every rule and hash of a failure ledger
//! pfp_operad ledger admitted LEDGER.jsonl   list the rules a run may load
//! pfp_operad ledger append LEDGER.jsonl RECORD.json   check a record and add it to the ledger
//! pfp_operad envelope REQUEST.json         check a full-slot reply: slots, candidates, DDC moves
//! pfp_operad judge REQUEST.json            compare a reply's task result with the host's own
//! pfp_operad version                       name, version and canon of this host
//! ```
//!
//! Exit 0: the check held. Exit 1: it ran and did not hold, or the input was refused.
//! Exit 2: the command line was wrong or a file could not be read or written.

use std::fs;
use std::io::Write;
use std::process::ExitCode;

use pfp_operads::host::{respond, Command, Outcome};

const USAGE: &str = "usage: pfp_operad laws FILE | check FILE | envelope FILE | judge FILE | version | ledger verify FILE | ledger admitted FILE | ledger append FILE RECORD";

fn read(path: &str) -> Result<String, String> {
    fs::read_to_string(path).map_err(|error| format!("cannot read {path}: {error}"))
}

/// A ledger that does not exist yet is an empty ledger.
fn read_ledger(path: &str) -> Result<String, String> {
    match fs::read_to_string(path) {
        Ok(text) => Ok(text),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(String::new()),
        Err(error) => Err(format!("cannot read {path}: {error}")),
    }
}

fn command(args: &[&str]) -> Result<Command, String> {
    match args {
        ["laws", file] => Ok(Command::Laws(read(file)?)),
        ["check", file] => Ok(Command::Check(read(file)?)),
        ["envelope", file] => Ok(Command::Envelope(read(file)?)),
        ["judge", file] => Ok(Command::Judge(read(file)?)),
        ["version"] => Ok(Command::Version),
        ["ledger", "verify", file] => Ok(Command::LedgerVerify(read(file)?)),
        ["ledger", "admitted", file] => Ok(Command::LedgerAdmitted(read(file)?)),
        ["ledger", "append", file, record] => Ok(Command::LedgerAppend {
            ledger: read_ledger(file)?,
            record: read(record)?,
        }),
        _ => Err(USAGE.to_owned()),
    }
}

fn append_line(path: &str, outcome: &Outcome) -> Result<(), String> {
    let Outcome::Pass { result } = outcome else {
        return Ok(());
    };
    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|error| format!("cannot open {path}: {error}"))?;
    writeln!(file, "{result}").map_err(|error| format!("cannot write {path}: {error}"))
}

fn run(args: &[&str]) -> Result<Outcome, String> {
    let outcome = respond(&command(args)?);
    if let ["ledger", "append", file, _] = args {
        append_line(file, &outcome)?;
    }
    Ok(outcome)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let args: Vec<&str> = args.iter().map(String::as_str).collect();
    match run(&args) {
        Ok(outcome) => {
            println!(
                "{}",
                serde_json::to_string(&outcome)
                    .unwrap_or_else(|_| "{\"status\":\"REFUSED\"}".to_owned())
            );
            ExitCode::from(u8::from(!matches!(outcome, Outcome::Pass { .. })))
        }
        Err(message) => {
            eprintln!("pfp_operad: {message}");
            ExitCode::from(2)
        }
    }
}
