//! Original dossier integer homology and Smith-certificate replay.
//! Mathematics delegates to existing owners. AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::determinant::bareiss_determinant;
use linear_algebra::smith_normal_form::{smith_normal_form_checked, SmithDiagonal};
use num_bigint::BigInt;
use omega_homology::integral_chain_complex::{IntegralChainComplex, SparseIntegerMatrix};
use serde_json::{json, Value};
use std::io::{self, Read};

fn matrix(value: &Value) -> Result<BasicMatrix<BigInt>, String> {
    let rows = value.as_array().ok_or("MATRIX_ARRAY")?;
    let cols = rows
        .first()
        .and_then(Value::as_array)
        .ok_or("EMPTY_MATRIX")?
        .len();
    if rows.is_empty() || cols == 0 || rows.len() > 128 || cols > 128 {
        return Err("MATRIX_BOUND".into());
    }
    let mut data = Vec::new();
    for row in rows {
        let items = row.as_array().ok_or("ROW_ARRAY")?;
        if items.len() != cols {
            return Err("RAGGED_MATRIX".into());
        }
        for item in items {
            let wire = item.as_str().ok_or("INTEGER_STRING_REQUIRED")?;
            let integer: BigInt = wire.parse().map_err(|_| "NONINTEGER")?;
            if integer.to_string() != wire {
                return Err("NONCANONICAL_INTEGER".into());
            }
            data.push(integer);
        }
    }
    BasicMatrix::from_row_major(rows.len(), cols, data).map_err(|e| e.to_string())
}

fn rows(m: &BasicMatrix<BigInt>) -> Vec<Vec<String>> {
    (0..m.rows())
        .map(|r| {
            (0..m.cols())
                .map(|c| m.get(r, c).unwrap().to_string())
                .collect()
        })
        .collect()
}

fn determinant(m: &BasicMatrix<BigInt>) -> Result<BigInt, String> {
    let data = (0..m.rows())
        .map(|r| {
            (0..m.cols())
                .map(|c| m.get(r, c).unwrap().clone())
                .collect()
        })
        .collect::<Vec<_>>();
    bareiss_determinant(&data).map_err(|e| e.to_string())
}

fn verify(a: &BasicMatrix<BigInt>, certificate: &Value) -> Result<Value, String> {
    let u = matrix(&certificate["u"])?;
    let v = matrix(&certificate["v"])?;
    let d = matrix(&certificate["d"])?;
    if u.rows() != a.rows()
        || u.cols() != a.rows()
        || v.rows() != a.cols()
        || v.cols() != a.cols()
        || d.rows() != a.rows()
        || d.cols() != a.cols()
    {
        return Err("CERTIFICATE_SHAPE".into());
    }
    let du = determinant(&u)?;
    let dv = determinant(&v)?;
    if !["1", "-1"].contains(&du.to_string().as_str())
        || !["1", "-1"].contains(&dv.to_string().as_str())
    {
        return Err("NONUNIMODULAR_BASIS".into());
    }
    let product = u
        .mul(a)
        .and_then(|ua| ua.mul(&v))
        .map_err(|e| e.to_string())?;
    if product.as_slice() != d.as_slice() {
        return Err("UAV_NE_D".into());
    }
    let mut factors = Vec::new();
    let mut zero_seen = false;
    for r in 0..d.rows() {
        for c in 0..d.cols() {
            let entry = d.get(r, c).unwrap();
            if r != c && entry != BigInt::from(0) {
                return Err("NONDIAGONAL_SMITH".into());
            }
            if r == c {
                if entry == BigInt::from(0) {
                    zero_seen = true;
                } else {
                    if zero_seen {
                        return Err("SMITH_ZERO_ORDER".into());
                    }
                    factors.push(entry.clone());
                }
            }
        }
    }
    let diagonal = SmithDiagonal::new_checked(factors).map_err(|e| e.to_string())?;
    Ok(
        json!({"verified": true, "det_u": du.to_string(), "det_v": dv.to_string(),
        "invariants": diagonal.invariants().iter().map(ToString::to_string).collect::<Vec<_>>()}),
    )
}

fn audit(case: &Value) -> Result<Value, String> {
    let wire = case["matrices"].as_array().ok_or("MISSING_MAPS")?;
    if wire.is_empty() || wire.len() > 8 {
        return Err("MAP_COUNT".into());
    }
    let cochain_maps = wire.iter().map(matrix).collect::<Result<Vec<_>, _>>()?;
    let mut dims = vec![cochain_maps[0].cols()];
    dims.extend(cochain_maps.iter().map(|m| m.rows()));
    // A cochain row becomes a chain-boundary column, preserving every signed coefficient.
    let boundaries = cochain_maps
        .iter()
        .map(|m| {
            let columns = (0..m.rows())
                .map(|r| {
                    (0..m.cols())
                        .filter_map(|c| {
                            let entry = m.get(r, c).unwrap();
                            if entry == BigInt::from(0) {
                                None
                            } else {
                                Some(
                                    entry
                                        .to_string()
                                        .parse::<i64>()
                                        .map(|x| (c, x))
                                        .map_err(|_| "COEFFICIENT_I64_BOUND".to_string()),
                                )
                            }
                        })
                        .collect::<Result<Vec<_>, _>>()
                })
                .collect::<Result<Vec<_>, _>>()?;
            SparseIntegerMatrix::new(m.cols(), columns).map_err(|e| e.to_string())
        })
        .collect::<Result<Vec<_>, String>>()?;
    let declared_dims = case["carrier_dimensions"]
        .as_array()
        .ok_or("MISSING_CARRIER_DIMENSIONS")?
        .iter()
        .map(|x| {
            x.as_u64()
                .and_then(|x| usize::try_from(x).ok())
                .ok_or("CARRIER_DIMENSION_TYPE")
        })
        .collect::<Result<Vec<_>, _>>()?;
    if declared_dims != dims {
        return Err("DECLARED_CARRIER_MISMATCH".into());
    }
    let complex = IntegralChainComplex::new(dims.clone(), boundaries).map_err(|e| e.to_string())?;
    if let Some(certificates) = case.get("certificates") {
        let certificates = certificates.as_array().ok_or("CERTIFICATE_ARRAY")?;
        if certificates.len() != cochain_maps.len() {
            return Err("CERTIFICATE_COMPLETENESS".into());
        }
        let reports = (1..dims.len())
            .map(|k| {
                if certificates[k - 1]["degree"].as_u64() != Some(k as u64) {
                    return Err("CERTIFICATE_DEGREE_BINDING".into());
                }
                let a = complex
                    .boundary(k)
                    .and_then(SparseIntegerMatrix::to_dense)
                    .map_err(|e| e.to_string())?;
                verify(&a, &certificates[k - 1])
            })
            .collect::<Result<Vec<_>, _>>()?;
        return Ok(json!({"certificates_verified": true, "reports": reports}));
    }
    let mut certificates = Vec::new();
    for k in 1..dims.len() {
        let a = complex
            .boundary(k)
            .and_then(SparseIntegerMatrix::to_dense)
            .map_err(|e| e.to_string())?;
        let snf = smith_normal_form_checked(&a).map_err(|e| e.to_string())?;
        let certificate = json!({"degree": k, "u": rows(snf.u()), "v": rows(snf.v()), "d": rows(snf.diagonal_matrix())});
        let replay = verify(&a, &certificate)?;
        certificates.push(json!({"certificate": certificate, "replay": replay}));
    }
    let f2 = complex.reduce_mod_2().map_err(|e| e.to_string())?;
    let mut homology = Vec::new();
    let mut previous_even = 0;
    for k in 0..dims.len() {
        let h = complex.integral_homology(k).map_err(|e| e.to_string())?;
        let even = h.even_torsion_summands();
        let mod2 = f2.homology_dimension(k).map_err(|e| e.to_string())?;
        let uct = h.free_rank + even + previous_even;
        if mod2 != uct {
            return Err("UCT_MOD2_MISMATCH".into());
        }
        homology.push(json!({"degree": k, "free_rank": h.free_rank,
            "torsion": h.torsion.iter().map(ToString::to_string).collect::<Vec<_>>(),
            "mod2_dimension": mod2, "uct_dimension": uct}));
        previous_even = even;
    }
    Ok(json!({"dimensions": dims, "boundary_law_verified": true,
        "integral_homology": homology, "certificates": certificates,
        "euler_characteristic": complex.euler_characteristic().to_string(), "uct_verified": true}))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut input = Vec::new();
    io::stdin().take(2_097_153).read_to_end(&mut input)?;
    if input.len() > 2_097_152 {
        return Err("REQUEST_LIMIT".into());
    }
    let request: Value = serde_json::from_slice(&input)?;
    let cases = request["cases"].as_array().ok_or("CASE_ARRAY")?;
    if cases.is_empty() || cases.len() > 64 {
        return Err("CASE_COUNT".into());
    }
    let outcomes = cases
        .iter()
        .map(|c| match audit(c) {
            Ok(result) => json!({"case_id":c["case_id"],"success":true,"result":result}),
            Err(error) => json!({"case_id":c["case_id"],"success":false,"error":error}),
        })
        .collect::<Vec<_>>();
    serde_json::to_writer(
        io::stdout().lock(),
        &json!({"schema":"paper011.dossier-integral-native.v1","cases":outcomes,"AuthorityEffect":"None"}),
    )?;
    println!();
    Ok(())
}
