//! `operad_canon write` regenerates the Python and JSON consumers of the operad table;
//! `operad_canon check` fails if the committed files differ from what the table renders.

use std::path::{Path, PathBuf};
use std::process::ExitCode;

use core_operad_canon::render::{to_json, to_python, JSON_PATH, PYTHON_PATH};

fn repo_root() -> PathBuf {
    // code/rust/core_operad_canon -> repository root
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../../..")
}

fn main() -> ExitCode {
    let mode = std::env::args().nth(1).unwrap_or_default();
    let root = repo_root();
    let outputs = [(JSON_PATH, to_json()), (PYTHON_PATH, to_python())];
    match mode.as_str() {
        "write" => {
            for (relative, text) in &outputs {
                let path = root.join(relative);
                if let Some(parent) = path.parent() {
                    std::fs::create_dir_all(parent).expect("create output directory");
                }
                std::fs::write(&path, text).expect("write generated file");
                println!("wrote {relative}");
            }
            ExitCode::SUCCESS
        }
        "check" => {
            let mut stale = 0;
            for (relative, text) in &outputs {
                let committed = std::fs::read_to_string(root.join(relative)).unwrap_or_default();
                if committed.replace("\r\n", "\n") != *text {
                    eprintln!("STALE {relative}: run `cargo run -p core_operad_canon -- write`");
                    stale += 1;
                }
            }
            if stale == 0 {
                println!("operad canon: generated files are current");
                ExitCode::SUCCESS
            } else {
                ExitCode::FAILURE
            }
        }
        _ => {
            eprintln!("usage: operad_canon write|check");
            ExitCode::from(2)
        }
    }
}
