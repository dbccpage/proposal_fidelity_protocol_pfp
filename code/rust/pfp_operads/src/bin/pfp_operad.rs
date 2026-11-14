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
//! pfp_operad ledger load LEDGER.jsonl REQUEST.json    write the seed a run loads: seed plus rules
//! pfp_operad ledger loaded LEDGER.jsonl REQUEST.json  check a seed is what the ledger loaded
//! pfp_operad ledger trial LEDGER.jsonl REQUEST.json   judge paired stored turns, write the trial
//! pfp_operad envelope REQUEST.json         check a full-slot reply: slots, candidates, DDC moves
//! pfp_operad judge REQUEST.json            compare a reply's task result with the host's own
//! pfp_operad mining REQUEST.json           screen a mining reply: digits, candidates, guidance
//! pfp_operad typing REQUEST.json           type candidates and bind the licensed ones
//! pfp_operad grounding REQUEST.json        recheck a solver reply's grounded slots
//! pfp_operad reuse REQUEST.json            list emitted candidates that reuse a mined signature
//! pfp_operad witness REQUEST.json          judge an answer and write its failure record
//! pfp_operad trial REQUEST.json            judge a rule's held-out trial and write its record
//! pfp_operad witness-turn REQUEST.json     judge a stored turn and write its failure record
//! pfp_operad run REQUEST.json              run candidates on the task's input against the judge
//! pfp_operad version                       name, version and canon of this host
//! ```
//!
//! Exit 0: the check held. Exit 1: it ran and did not hold, or the input was refused.
//! Exit 2: the command line was wrong or a file could not be read or written.

use std::fs;
use std::io::Write;
use std::process::ExitCode;

use pfp_operads::host::{respond, Command, Outcome};

const USAGE: &str = "usage: pfp_operad laws FILE | check FILE | envelope FILE | judge FILE | mining FILE | typing FILE | grounding FILE | reuse FILE | witness FILE | trial FILE | witness-turn FILE | run FILE | version | ledger verify FILE | ledger admitted FILE | ledger append FILE RECORD | ledger load FILE REQUEST | ledger loaded FILE REQUEST | ledger trial FILE REQUEST";

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
        ["mining", file] => Ok(Command::Mining(read(file)?)),
        ["typing", file] => Ok(Command::Typing(read(file)?)),
        ["grounding", file] => Ok(Command::Grounding(read(file)?)),
        ["reuse", file] => Ok(Command::Reuse(read(file)?)),
        ["witness", file] => Ok(Command::Witness(read(file)?)),
        ["trial", file] => Ok(Command::Trial(read(file)?)),
        ["witness-turn", file] => Ok(Command::WitnessTurn(read(file)?)),
        ["run", file] => Ok(Command::Run(read(file)?)),
        ["version"] => Ok(Command::Version),
        ["ledger", "verify", file] => Ok(Command::LedgerVerify(read(file)?)),
        ["ledger", "admitted", file] => Ok(Command::LedgerAdmitted(read(file)?)),
        ["ledger", "append", file, record] => Ok(Command::LedgerAppend {
            ledger: read_ledger(file)?,
            record: read(record)?,
        }),
        ["ledger", "load", file, request] => Ok(Command::LedgerLoad {
            ledger: read_ledger(file)?,
            request: read(request)?,
        }),
        ["ledger", "loaded", file, request] => Ok(Command::LedgerLoaded {
            ledger: read_ledger(file)?,
            request: read(request)?,
        }),
        ["ledger", "trial", file, request] => Ok(Command::LedgerTrial {
            ledger: read_ledger(file)?,
            request: read(request)?,
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
