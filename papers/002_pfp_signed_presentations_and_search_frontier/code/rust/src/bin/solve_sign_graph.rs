use num_rational::Rational64;
use pfp_sign_graph::{
    classify_sign_graph, matrix_sign_graph, verify_gauge, verify_odd_cycle,
    GaugeWitness, OddCycleWitness, SignResult, SignedRewrite,
};
use serde::{Deserialize, Serialize};
use std::io::{self, Read};

#[derive(Deserialize)]
struct InputPayload {
    mode: Option<String>,
    vertices: Option<Vec<String>>,
    edges: Option<Vec<SignedRewrite>>,
    witness_gauge: Option<GaugeWitness>,
    witness_odd_cycle: Option<OddCycleWitness>,
    matrix: Option<Vec<Vec<String>>>,
    matrix_ints: Option<Vec<Vec<i64>>>,
}

#[derive(Serialize)]
struct OutputPayload {
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    result_type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    witness: Option<SignResult>,
    #[serde(skip_serializing_if = "Option::is_none")]
    valid: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
}

fn parse_rational(s: &str) -> Result<Rational64, String> {
    if let Some((num_str, den_str)) = s.split_once('/') {
        let num: i64 = num_str.trim().parse().map_err(|e| format!("invalid numerator: {}", e))?;
        let den: i64 = den_str.trim().parse().map_err(|e| format!("invalid denominator: {}", e))?;
        if den == 0 {
            return Err("denominator cannot be zero".to_string());
        }
        Ok(Rational64::new(num, den))
    } else {
        let val: i64 = s.trim().parse().map_err(|e| format!("invalid integer: {}", e))?;
        Ok(Rational64::from_integer(val))
    }
}

fn emit_error(msg: &str) {
    let out = OutputPayload {
        status: "ERROR".to_string(),
        result_type: None,
        witness: None,
        valid: None,
        message: Some(msg.to_string()),
    };
    println!("{}", serde_json::to_string(&out).unwrap());
}

fn main() {
    let mut buffer = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut buffer) {
        emit_error(&format!("Failed to read stdin: {}", e));
        return;
    }

    let payload: InputPayload = match serde_json::from_str(&buffer) {
        Ok(p) => p,
        Err(e) => {
            emit_error(&format!("JSON parse error: {}", e));
            return;
        }
    };

    let mode = match payload.mode.as_deref() {
        Some("classify") => "classify",
        Some("verify_gauge") => "verify_gauge",
        Some("verify_odd_cycle") => "verify_odd_cycle",
        Some(unknown) => {
            emit_error(&format!("Unknown or unsupported mode '{}'", unknown));
            return;
        }
        None => {
            emit_error("Missing required field 'mode' (must be 'classify', 'verify_gauge', or 'verify_odd_cycle')");
            return;
        }
    };

    if mode == "verify_gauge" {
        if payload.matrix.is_some() || payload.matrix_ints.is_some() || payload.witness_odd_cycle.is_some() {
            emit_error("Extraneous fields supplied for verify_gauge mode");
            return;
        }
        let vertices = match payload.vertices {
            Some(v) => v,
            None => {
                emit_error("Missing required field 'vertices' for verify_gauge mode");
                return;
            }
        };
        let edges = match payload.edges {
            Some(e) => e,
            None => {
                emit_error("Missing required field 'edges' for verify_gauge mode");
                return;
            }
        };
        let witness = match payload.witness_gauge {
            Some(w) => w,
            None => {
                emit_error("witness_gauge is required for verify_gauge mode");
                return;
            }
        };
        let valid = verify_gauge(&vertices, &edges, &witness);
        let out = OutputPayload {
            status: "PASS".to_string(),
            result_type: None,
            witness: None,
            valid: Some(valid),
            message: None,
        };
        println!("{}", serde_json::to_string(&out).unwrap());
        return;
    }

    if mode == "verify_odd_cycle" {
        if payload.matrix.is_some() || payload.matrix_ints.is_some() || payload.witness_gauge.is_some() {
            emit_error("Extraneous fields supplied for verify_odd_cycle mode");
            return;
        }
        let vertices = match payload.vertices {
            Some(v) => v,
            None => {
                emit_error("Missing required field 'vertices' for verify_odd_cycle mode");
                return;
            }
        };
        let edges = match payload.edges {
            Some(e) => e,
            None => {
                emit_error("Missing required field 'edges' for verify_odd_cycle mode");
                return;
            }
        };
        let witness = match payload.witness_odd_cycle {
            Some(w) => w,
            None => {
                emit_error("witness_odd_cycle is required for verify_odd_cycle mode");
                return;
            }
        };
        let valid = verify_odd_cycle(&vertices, &edges, &witness);
        let out = OutputPayload {
            status: "PASS".to_string(),
            result_type: None,
            witness: None,
            valid: Some(valid),
            message: None,
        };
        println!("{}", serde_json::to_string(&out).unwrap());
        return;
    }

    // mode == "classify"
    if payload.witness_gauge.is_some() || payload.witness_odd_cycle.is_some() {
        emit_error("Witness fields ('witness_gauge', 'witness_odd_cycle') are not accepted in classify mode");
        return;
    }

    let has_mat_ints = payload.matrix_ints.is_some();
    let has_mat = payload.matrix.is_some();
    let has_vert = payload.vertices.is_some();
    let has_edge = payload.edges.is_some();

    if has_vert != has_edge {
        emit_error("Both 'vertices' and 'edges' must be supplied together for explicit graph classification");
        return;
    }
    let has_graph = has_vert && has_edge;

    let rep_count = (if has_mat_ints { 1 } else { 0 })
        + (if has_mat { 1 } else { 0 })
        + (if has_graph { 1 } else { 0 });

    if rep_count == 0 {
        emit_error("No graph input representation supplied; expected exactly one of ('matrix_ints', 'matrix', or 'vertices'+'edges')");
        return;
    }
    if rep_count > 1 {
        emit_error("Ambiguous input: multiple graph representations supplied; expected exactly one of ('matrix_ints', 'matrix', or 'vertices'+'edges')");
        return;
    }

    let (vertices, edges) = if let Some(mat_ints) = payload.matrix_ints {
        let mat_rats: Vec<Vec<Rational64>> = mat_ints
            .into_iter()
            .map(|row| row.into_iter().map(Rational64::from_integer).collect())
            .collect();
        match matrix_sign_graph(&mat_rats) {
            Ok(pair) => pair,
            Err(e) => {
                emit_error(&format!("{}", e));
                return;
            }
        }
    } else if let Some(mat_str) = payload.matrix {
        let mut mat_rats = Vec::new();
        for row in mat_str {
            let mut rat_row = Vec::new();
            for s in row {
                match parse_rational(&s) {
                    Ok(r) => rat_row.push(r),
                    Err(e) => {
                        emit_error(&format!("matrix rational parse error: {}", e));
                        return;
                    }
                }
            }
            mat_rats.push(rat_row);
        }
        match matrix_sign_graph(&mat_rats) {
            Ok(pair) => pair,
            Err(e) => {
                emit_error(&format!("{}", e));
                return;
            }
        }
    } else if let (Some(v), Some(e)) = (payload.vertices, payload.edges) {
        (v, e)
    } else {
        unreachable!();
    };

    match classify_sign_graph(&vertices, &edges) {
        Ok(result) => {
            let result_type = match &result {
                SignResult::Gauge(_) => "gauge".to_string(),
                SignResult::OddCycle(_) => "odd_cycle".to_string(),
            };
            let out = OutputPayload {
                status: "PASS".to_string(),
                result_type: Some(result_type),
                witness: Some(result),
                valid: None,
                message: None,
            };
            println!("{}", serde_json::to_string(&out).unwrap());
        }
        Err(e) => {
            emit_error(&format!("{}", e));
        }
    }
}
