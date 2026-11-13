//! Print the obstruction-transfer table, write its receipt, or replay a receipt.
//!
//! AuthorityEffect: None.
//!
//! ```text
//! obstruction_transfer_table [--max-n N] [--out DIR] [--inject-flip-chord-sign | --inject-flip-tree-edge-sign]
//! obstruction_transfer_table --check DIR
//! ```
//!
//! `--out DIR` writes `DIR/table.md` and `DIR/receipt.json`. `--check DIR` reruns
//! the family named by `DIR/receipt.json` and exits 1 unless the receipt and the
//! table are reproduced byte for byte.

use std::path::PathBuf;
use std::process::ExitCode;
use std::time::Instant;

use core_obstruction_transfer::{receipt_json, run, Injection, RunConfig, RunOutput};

fn document(out: &RunOutput) -> String {
    format!("## Census\n\n{}\n## Table\n\n{}", out.census, out.table)
}

fn max_n_from_receipt(text: &str) -> Option<usize> {
    let line = text
        .lines()
        .find(|l| l.trim_start().starts_with("\"max_n\""))?;
    line.split(':')
        .nth(1)?
        .trim()
        .trim_end_matches(',')
        .parse()
        .ok()
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut max_n = 5usize;
    let mut out_dir: Option<PathBuf> = None;
    let mut check_dir: Option<PathBuf> = None;
    let mut injection = Injection::None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--max-n" => {
                i += 1;
                match args.get(i).and_then(|s| s.parse().ok()) {
                    Some(n) => max_n = n,
                    None => {
                        eprintln!("obstruction_transfer_table: --max-n needs an integer");
                        return ExitCode::from(2);
                    }
                }
            }
            "--out" => {
                i += 1;
                out_dir = args.get(i).map(PathBuf::from);
            }
            "--check" => {
                i += 1;
                check_dir = args.get(i).map(PathBuf::from);
            }
            "--inject-flip-chord-sign" => injection = Injection::FlipFirstChordSign,
            "--inject-flip-tree-edge-sign" => injection = Injection::FlipFirstTreeEdgeSign,
            other => {
                eprintln!("obstruction_transfer_table: unknown argument {other}");
                return ExitCode::from(2);
            }
        }
        i += 1;
    }
    if let Some(dir) = &check_dir {
        let (Ok(receipt), Ok(table)) = (
            std::fs::read_to_string(dir.join("receipt.json")),
            std::fs::read_to_string(dir.join("table.md")),
        ) else {
            eprintln!(
                "obstruction_transfer_table: cannot read receipt.json and table.md in {}",
                dir.display()
            );
            return ExitCode::from(2);
        };
        let Some(n) = max_n_from_receipt(&receipt) else {
            eprintln!("obstruction_transfer_table: receipt has no max_n");
            return ExitCode::from(2);
        };
        max_n = n;
        let cfg = RunConfig {
            max_n,
            injection: Injection::None,
        };
        return match run(cfg) {
            Ok(out) if receipt_json(&cfg, &out) == receipt && document(&out) == table => {
                println!("receipt reproduced: output_digest {}", out.output_digest);
                ExitCode::SUCCESS
            }
            Ok(out) => {
                eprintln!(
                    "receipt NOT reproduced: output_digest {}",
                    out.output_digest
                );
                ExitCode::from(1)
            }
            Err(e) => {
                eprintln!("obstruction_transfer_table: {e}");
                ExitCode::from(1)
            }
        };
    }
    let cfg = RunConfig { max_n, injection };
    let started = Instant::now();
    let out = match run(cfg) {
        Ok(out) => out,
        Err(e) => {
            eprintln!("obstruction_transfer_table: {e}");
            return ExitCode::from(1);
        }
    };
    eprintln!(
        "instances {} pairs {} elapsed_ms {}",
        out.instance_count,
        out.pair_count,
        started.elapsed().as_millis()
    );
    for f in out.gauge_failures.iter().take(20) {
        eprintln!("GAUGE_FAILURE {f}");
    }
    eprintln!("gauge_failures {}", out.gauge_failures.len());
    for d in &out.defects {
        eprintln!("DEFECT {d}");
    }
    let doc = document(&out);
    match &out_dir {
        Some(dir) => {
            let written = std::fs::create_dir_all(dir)
                .and_then(|_| std::fs::write(dir.join("table.md"), &doc))
                .and_then(|_| std::fs::write(dir.join("receipt.json"), receipt_json(&cfg, &out)));
            if let Err(e) = written {
                eprintln!("obstruction_transfer_table: {e}");
                return ExitCode::from(2);
            }
        }
        None => print!("{doc}"),
    }
    if out.defects.is_empty() {
        ExitCode::SUCCESS
    } else {
        ExitCode::from(1)
    }
}
