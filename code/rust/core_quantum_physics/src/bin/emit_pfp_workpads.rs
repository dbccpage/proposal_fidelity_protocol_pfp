//! emit_pfp_workpads.rs — sovereign CLI to emit canonical PFP workpad JSON payloads.
//!
//! AuthorityEffect: None.

use core_quantum_physics::cptp_trajectory_verifier::workpad::*;
use std::env;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let out_dir = classify_emission_request(&args)?;

    println!("Emitting canonical PFP calculation workpads to: {}", out_dir.display());
    let written = emit_canonical_workpads_to_dir(&out_dir)?;
    let _count = census_emitted(&written)?;
    for p in written {
        println!("EMITTED: {}", p.display());
    }
    Ok(())
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_quantum_physics/src/bin/emit_pfp_workpads.rs
// Claim: urn:core:quantum:pfp-workpad-emission:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum EmissionError {
    EmptyDir,
    Nameless,
    Duplicate { name: String },
    EmptyEmission,
    Range,
}

impl std::fmt::Display for EmissionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EmptyDir => write!(f, "emission directory is empty"),
            Self::Nameless => write!(f, "emitted path has no file name"),
            Self::Duplicate { name } => write!(f, "duplicate emitted file {name}"),
            Self::EmptyEmission => write!(f, "emission wrote no workpads"),
            Self::Range => write!(f, "emission count is not a u64"),
        }
    }
}

impl std::error::Error for EmissionError {}

fn classify_emission_request(args: &[String]) -> Result<PathBuf, EmissionError> {
    if args.len() > 2 && args.get(1).map(String::as_str) == Some("--out-dir") {
        if args[2].is_empty() {
            return Err(EmissionError::EmptyDir);
        }
        return Ok(PathBuf::from(&args[2]));
    }
    Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_quantum_physics/fixtures/pfp_workpads"))
}

fn census_emitted(written: &[PathBuf]) -> Result<u64, EmissionError> {
    if written.is_empty() {
        return Err(EmissionError::EmptyEmission);
    }
    let mut names = Vec::<String>::new();
    for path in written {
        let name = match path.file_name().and_then(|value| value.to_str()) {
            Some(value) if !value.is_empty() => value,
            _ => return Err(EmissionError::Nameless),
        };
        if names.iter().any(|seen| seen == name) {
            return Err(EmissionError::Duplicate {
                name: name.to_string(),
            });
        }
        names.push(name.to_string());
    }
    let count = u64::try_from(names.len()).map_err(|_| EmissionError::Range)?;
    if count == 0 {
        return Err(EmissionError::EmptyEmission);
    }
    Ok(count)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod emission_census_tests {
    use super::{census_emitted, classify_emission_request, EmissionError};
    use std::path::PathBuf;

    #[test]
    fn an_empty_out_dir_is_refused_and_the_default_keeps_its_name() {
        let empty = vec![
            "emit".to_string(),
            "--out-dir".to_string(),
            String::new(),
        ];
        assert!(matches!(
            classify_emission_request(&empty),
            Err(EmissionError::EmptyDir)
        ));
        let plain = vec!["emit".to_string()];
        let dir = classify_emission_request(&plain);
        assert!(dir.is_ok());
        if let Ok(dir) = dir {
            assert_eq!(
                dir.file_name().and_then(|value| value.to_str()),
                Some("pfp_workpads")
            );
        }
    }

    #[test]
    fn duplicate_or_nameless_emissions_are_refused() {
        let duplicated = vec![PathBuf::from("alpha.json"), PathBuf::from("nest/alpha.json")];
        assert!(matches!(
            census_emitted(&duplicated),
            Err(EmissionError::Duplicate { .. })
        ));
        assert!(matches!(
            census_emitted(&[PathBuf::from("")]),
            Err(EmissionError::Nameless)
        ));
        assert!(matches!(
            census_emitted(&[]),
            Err(EmissionError::EmptyEmission)
        ));
    }
}
