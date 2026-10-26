//! `po000` — recompute the PO-000 replication and print its receipt.
//!
//! ```text
//! cargo run --release --bin po000            # print the receipt
//! cargo run --release --bin po000 -- --write # also rewrite RECEIPT.txt
//! ```
//!
//! `AuthorityEffect: None.`

use omega_ooutwire_primitives::alpha_projection_obstruction::run;

fn main() {
    let write = std::env::args().any(|a| a == "--write");
    let run = match run() {
        Ok(r) => r,
        Err(e) => {
            eprintln!("replication did not complete: {e}");
            std::process::exit(2);
        }
    };
    let text = run.to_text();
    print!("{text}");
    if write {
        let path = omega_ooutwire_primitives::alpha_projection_obstruction::receipt_path();
        std::fs::write(&path, text.as_bytes()).expect("write RECEIPT.txt");
        eprintln!("wrote {}", path.display());
    }
    if !run.executable_checks_passed {
        std::process::exit(1);
    }
}
