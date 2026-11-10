//! Bounded offline adapter for source-extracted production char_poly methods.
//! This is not the full PFP host, nor OPERADS/EIS/PCIV integration.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::Deserialize;
use serde_json::json;
use std::io::{self, Read};
use std::str::FromStr;

type Exact = BigRational;
const MAX_REQUEST: usize = 262_144;
const MAX_MATRICES: usize = 125;

#[derive(Debug)]
enum RationalError {
    NotSquare { rows: usize, cols: usize },
}

// Minimal private carrier; all production arithmetic methods are included below.
struct RationalMatrix {
    rows: usize,
    cols: usize,
    data: Vec<Exact>,
}
impl RationalMatrix {
    fn get(&self, row: usize, col: usize) -> &Exact {
        &self.data[row * self.cols + col]
    }
    fn is_square(&self) -> bool { self.rows == self.cols }
}
include!("production_charpoly.rs");

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    schema: String,
    matrices: Vec<Vec<Vec<String>>>,
}

fn admit_matrix(rows: Vec<Vec<String>>) -> Result<RationalMatrix, String> {
    let n = rows.len();
    if !(1..=4).contains(&n) || rows.iter().any(|row| row.len() != n) {
        return Err("MATRIX_DIMENSION: nonempty square dimension 1..4 required".into());
    }
    let mut data = Vec::with_capacity(n * n);
    for text in rows.into_iter().flatten() {
        if text.len() > 82 {
            return Err("RATIONAL_LIMIT".into());
        }
        let q = BigRational::from_str(&text).map_err(|_| "RATIONAL_INVALID")?;
        if q.to_string() != text || q.numer().bits() > 128 || q.denom().bits() > 128 {
            return Err("RATIONAL_CANONICAL_OR_BIT_LIMIT".into());
        }
        data.push(q);
    }
    Ok(RationalMatrix { rows: n, cols: n, data })
}

fn run() -> Result<serde_json::Value, String> {
    let mut raw = Vec::new();
    io::stdin().take((MAX_REQUEST + 1) as u64).read_to_end(&mut raw)
        .map_err(|_| "INPUT_IO")?;
    if raw.len() > MAX_REQUEST { return Err("REQUEST_LIMIT".into()); }
    let request: Request = serde_json::from_slice(&raw).map_err(|_| "REQUEST_INVALID")?;
    if request.schema != "pfp.native-sidecar.charpoly-batch.v1" {
        return Err("SCHEMA_MISMATCH".into());
    }
    if request.matrices.is_empty() || request.matrices.len() > MAX_MATRICES {
        return Err("BATCH_LIMIT".into());
    }
    // Admit the complete request before any calculation.
    let matrices = request.matrices.into_iter().map(admit_matrix)
        .collect::<Result<Vec<_>, _>>()?;
    let coefficients = matrices.iter().map(|matrix| {
        matrix.char_poly().map(|p| p.iter().map(ToString::to_string).collect::<Vec<_>>())
            .map_err(|error| format!("CHARPOLY_REFUSAL:{error:?}"))
    }).collect::<Result<Vec<_>, _>>()?;
    Ok(json!({"schema":"pfp.native-sidecar.charpoly-result.v1",
        "status":"COMPUTED", "coefficients":coefficients,
        "mechanism":"source-extracted-pfp-runtime-rational-char-poly",
        "authority_effect":"None"}))
}

fn main() {
    let output = match run() {
        Ok(value) => value,
        Err(reason) => json!({"schema":"pfp.native-sidecar.charpoly-result.v1",
            "status":"REFUSED", "reason":reason, "authority_effect":"None"}),
    };
    println!("{}", output);
}
