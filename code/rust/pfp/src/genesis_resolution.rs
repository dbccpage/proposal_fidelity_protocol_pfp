//! Bounded, input-bound Genesis potential certificates from the existing exact solver.
//!
//! The native simplex proposes one optimum, not every tied basic solution. Its
//! arbitrary-precision arithmetic allocates. These limitations are explicit in
//! the result; neither a realization nor a certificate creates authority.

use std::collections::{BTreeMap, BTreeSet};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::elimination::inverse;
use linear_algebra::smith_normal_form::smith_normal_form_checked;
use num_bigint::BigInt;
use num_traits::{One, Signed, ToPrimitive, Zero};
use core_functional::{ExactPhi1Certificate, Phi1Functional};
use core_kernel::bounded_rational::StackRational;
use core_kernel::{exact_wire_vec, parse_exact, Exact};
use core_solvers::solver_lp_bounded_candidate::{self as stack, CandidateError};
use core_solvers::solver_lp_exact_simplex::{solve_weighted_l1_projection, L1LpError};
use pfp_runtime::framed_sha256;
use serde::Deserialize;
use serde_json::{json, Value};

pub const INPUT_DOMAIN: &str = "core.genesis.resolve-input.v1";
const MAX_CELLS_PER_DEGREE: usize = 64;
const MAX_TOTAL_CELLS: usize = 256;
const MAX_BOUNDARY_ENTRIES: usize = 4096;
const MAX_PIVOTS: usize = 100_000;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Complex {
    cells: BTreeMap<i32, Vec<String>>,
    boundary: BTreeMap<i32, Vec<Vec<Value>>>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    #[serde(default = "none_authority")]
    authority_effect: String,
    complex: Complex,
    degree: i32,
    reading_id: String,
    #[serde(with = "exact_wire_vec")]
    reading: Vec<Exact>,
    #[serde(with = "exact_wire_vec")]
    weights: Vec<Exact>,
    budget: usize,
    #[serde(default = "yes")]
    include_integer: bool,
}

fn yes() -> bool {
    true
}

fn none_authority() -> String {
    "None".into()
}

fn refuse(code: &str, detail: impl std::fmt::Display) -> String {
    format!("{code}: {detail}")
}

fn document_q(q: &Exact) -> String {
    format!("{}/{}", q.numer(), q.denom())
}

fn document_vec(q: &[Exact]) -> Vec<String> {
    q.iter().map(document_q).collect()
}

fn proposal_scalar(q: &Exact) -> Result<StackRational, CandidateError> {
    StackRational::new(
        q.numer().to_i128().ok_or(CandidateError::Overflow)?,
        q.denom().to_i128().ok_or(CandidateError::Overflow)?,
    )
    .map_err(Into::into)
}

fn reinject(q: StackRational) -> Exact {
    Exact::new(q.numerator.into(), q.denominator.into())
}

/// Narrowing occurs only in an untrusted proposal generator. Every proposal is
/// reinjected and replayed by the canonical arbitrary-precision certificate gate.
fn exhaustive_ties(
    m: &BasicMatrix<BigInt>,
    reading: &[Exact],
    weights: &[Exact],
) -> Result<stack::Candidates, CandidateError> {
    if m.rows() > stack::MAX_ROWS || m.cols() > stack::MAX_COLS {
        return Err(CandidateError::Capacity);
    }
    let mut matrix = [[StackRational::ZERO; stack::MAX_COLS]; stack::MAX_ROWS];
    let mut r = [StackRational::ZERO; stack::MAX_ROWS];
    let mut w = [StackRational::ZERO; stack::MAX_ROWS];
    for row in 0..m.rows() {
        r[row] = proposal_scalar(&reading[row])?;
        w[row] = proposal_scalar(&weights[row])?;
        for (col, entry) in matrix[row].iter_mut().enumerate().take(m.cols()) {
            *entry = StackRational::new(
                m.as_slice()[row * m.cols() + col]
                    .to_i128()
                    .ok_or(CandidateError::Overflow)?,
                1,
            )?;
        }
    }
    stack::propose(&matrix, m.rows(), m.cols(), &r, &w, 256)
}

fn count(cx: &Complex, k: i32) -> usize {
    cx.cells.get(&k).map_or(0, Vec::len)
}

fn reject_floats(value: &Value) -> Result<(), String> {
    match value {
        Value::Number(n) if n.to_string().contains(['.', 'e', 'E']) => {
            Err(refuse("REFUSED_FLOAT", "numeric boundary contains a float"))
        }
        Value::Array(xs) => xs.iter().try_for_each(reject_floats),
        Value::Object(xs) => xs.values().try_for_each(reject_floats),
        _ => Ok(()),
    }
}

fn integer(value: &Value) -> Result<BigInt, String> {
    let text = match value {
        Value::Number(n) => n.to_string(),
        Value::String(s) => s.strip_suffix("/1").unwrap_or(s).to_owned(),
        _ => return Err(refuse("REFUSED_SHAPE", "boundary entry is not an integer")),
    };
    if text.contains(['.', 'e', 'E']) {
        return Err(refuse("REFUSED_FLOAT", "boundary entry is decimal"));
    }
    let q = parse_exact(&text).map_err(|e| refuse("REFUSED_SHAPE", e))?;
    if !q.denom().is_one() {
        return Err(refuse("REFUSED_SHAPE", "boundary entry is not integral"));
    }
    Ok(q.numer().clone())
}

fn matrices(cx: &Complex) -> Result<BTreeMap<i32, BasicMatrix<BigInt>>, String> {
    let total: usize = cx.cells.values().map(Vec::len).sum();
    if total > MAX_TOTAL_CELLS || cx.cells.values().any(|c| c.len() > MAX_CELLS_PER_DEGREE) {
        return Err(refuse("REFUSED_CAPACITY", "declared cell ceiling exceeded"));
    }
    for (&k, names) in &cx.cells {
        if !(-1..=32).contains(&k)
            || names.iter().any(String::is_empty)
            || names.iter().collect::<BTreeSet<_>>().len() != names.len()
            || (k >= 0 && !names.is_empty() && !cx.boundary.contains_key(&k))
        {
            return Err(refuse(
                "REFUSED_SHAPE",
                "invalid cell labels or missing boundary",
            ));
        }
    }
    let mut out = BTreeMap::new();
    let mut entries = 0usize;
    for (&k, rows) in &cx.boundary {
        if k < 0 || !cx.cells.contains_key(&k) || !cx.cells.contains_key(&(k - 1)) {
            return Err(refuse(
                "REFUSED_SHAPE",
                "boundary degree has no source or target",
            ));
        }
        let (m, n) = (count(cx, k), count(cx, k - 1));
        if rows.len() != m || rows.iter().any(|r| r.len() != n) {
            return Err(refuse(
                "REFUSED_SHAPE",
                "boundary dimensions disagree with cells",
            ));
        }
        entries += m * n;
        if entries > MAX_BOUNDARY_ENTRIES {
            return Err(refuse(
                "REFUSED_CAPACITY",
                "boundary entry ceiling exceeded",
            ));
        }
        let data = rows
            .iter()
            .flatten()
            .map(integer)
            .collect::<Result<Vec<_>, _>>()?;
        out.insert(
            k,
            BasicMatrix::from_row_major(m, n, data).map_err(|e| refuse("REFUSED_SHAPE", e))?,
        );
    }
    for (&k, a) in &out {
        if let Some(b) = out.get(&(k - 1)) {
            if !a
                .mul(b)
                .map_err(|e| refuse("REFUSED_SHAPE", e))?
                .as_slice()
                .iter()
                .all(Zero::is_zero)
            {
                return Err(refuse(
                    "REFUSED_CHAIN_CONDITION",
                    "successive boundaries do not compose to zero",
                ));
            }
        }
    }
    Ok(out)
}

fn integer_rows(m: &BasicMatrix<BigInt>) -> Vec<Vec<String>> {
    (0..m.rows())
        .map(|r| {
            (0..m.cols())
                .map(|c| m.as_slice()[r * m.cols() + c].to_string())
                .collect()
        })
        .collect()
}

fn inverse_integral(m: &BasicMatrix<BigInt>) -> Result<BasicMatrix<BigInt>, String> {
    let q = m.map(|x| Exact::from_integer(x.clone()));
    let inv = inverse(&q).map_err(|e| refuse("REFUSED_SNF_NOT_UNIMODULAR", e))?;
    if inv.as_slice().iter().any(|x| !x.denom().is_one()) {
        return Err(refuse(
            "REFUSED_SNF_NOT_UNIMODULAR",
            "inverse is not integral",
        ));
    }
    Ok(inv.map(|x| x.numer().clone()))
}

fn integer_certificate(
    raw_complex: &Value,
    request: &Request,
    m: &BasicMatrix<BigInt>,
) -> Result<(String, Value), String> {
    if request.reading.iter().any(|x| !x.denom().is_one()) {
        return Ok(("NOT_INTEGRAL".into(), Value::Null));
    }
    let snf = smith_normal_form_checked(m).map_err(|e| refuse("UNKNOWN_SNF", e))?;
    let reading: Vec<BigInt> = request.reading.iter().map(|x| x.numer().clone()).collect();
    let ur = snf
        .u()
        .mul_vec(&reading)
        .map_err(|e| refuse("REFUSED_SHAPE", e))?;
    let mut y = vec![BigInt::zero(); m.cols()];
    let mut obstruction = None;
    for (i, transformed) in ur.iter().enumerate() {
        let d = if i < m.cols() {
            snf.diagonal_matrix().as_slice()[i * m.cols() + i].clone()
        } else {
            BigInt::zero()
        };
        if d.is_zero() {
            if !transformed.is_zero() {
                obstruction = Some((i, "RATIONAL"));
                break;
            }
        } else if !(transformed % &d).is_zero() {
            obstruction = Some((i, "TORSION"));
            break;
        } else {
            y[i] = transformed / d;
        }
    }
    let mut cert = json!({
        "schema": "recurring_genesis/integer-certificate/v1", "authority_effect": "None",
        "complex": raw_complex, "degree": request.degree, "reading": document_vec(&request.reading)
    });
    if let Some((i, kind)) = obstruction {
        let u_inv = inverse_integral(snf.u())?;
        let v_inv = inverse_integral(snf.v())?;
        cert["verdict"] = json!("Z_OBSTRUCTED");
        cert["index"] = json!(i);
        cert["kind"] = json!(kind);
        cert["smith"] = json!({"u": integer_rows(snf.u()), "u_inv": integer_rows(&u_inv),
            "v": integer_rows(snf.v()), "v_inv": integer_rows(&v_inv), "d": integer_rows(snf.diagonal_matrix())});
        Ok(("Z_OBSTRUCTED".into(), cert))
    } else {
        let g = snf
            .v()
            .mul_vec(&y)
            .map_err(|e| refuse("REFUSED_SHAPE", e))?;
        if m.mul_vec(&g).map_err(|e| refuse("REFUSED_SHAPE", e))? != reading {
            return Err(refuse(
                "REFUSED_INTEGRAL_POTENTIAL_INVALID",
                "SNF potential does not replay",
            ));
        }
        cert["verdict"] = json!("Z_EXACT");
        cert["integral_potential"] = json!(g.iter().map(|x| format!("{x}/1")).collect::<Vec<_>>());
        Ok(("Z_EXACT".into(), cert))
    }
}

pub fn resolve(payload: &Value) -> Result<Value, String> {
    if !payload.is_object() {
        return Err(refuse("REFUSED_SHAPE", "request must be an object"));
    }
    reject_floats(payload)?;
    for field in ["reading", "weights"] {
        if let Some(values) = payload[field].as_array() {
            if values
                .iter()
                .any(|v| v.as_str().is_some_and(|s| s.contains(['.', 'e', 'E'])))
            {
                return Err(refuse("REFUSED_FLOAT", "reading or weight is decimal"));
            }
        }
    }
    let request: Request =
        serde_json::from_value(payload.clone()).map_err(|e| refuse("REFUSED_SHAPE", e))?;
    if request.authority_effect != "None" {
        return Err(refuse(
            "REFUSED_AUTHORITY_EFFECT",
            "a realization has no authority effect",
        ));
    }
    if !request.complex.cells.contains_key(&request.degree)
        || request.degree < 0
        || request.reading_id.is_empty()
    {
        return Err(refuse(
            "REFUSED_SHAPE",
            "degree or reading identity is invalid",
        ));
    }
    if request.budget > MAX_PIVOTS {
        return Err(refuse("REFUSED_CAPACITY", "pivot ceiling exceeded"));
    }
    let mats = matrices(&request.complex)?;
    let (m, n) = (
        count(&request.complex, request.degree),
        count(&request.complex, request.degree - 1),
    );
    if request.reading.len() != m || request.weights.len() != m {
        return Err(refuse(
            "REFUSED_SHAPE",
            "reading or weight dimension disagrees",
        ));
    }
    if request.weights.iter().any(|x| !x.is_positive()) {
        return Err(refuse(
            "REFUSED_WEIGHT_NOT_POSITIVE",
            "all weights must be positive",
        ));
    }
    let selected = match mats.get(&request.degree) {
        Some(a) => a.clone(),
        None => BasicMatrix::<BigInt>::zero(m, n).map_err(|e| refuse("REFUSED_SHAPE", e))?,
    };
    let map: Vec<Vec<Exact>> = (0..m)
        .map(|r| {
            (0..n)
                .map(|c| Exact::from_integer(selected.as_slice()[r * n + c].clone()))
                .collect()
        })
        .collect();
    let mut solution =
        solve_weighted_l1_projection(&request.reading, &request.weights, &map, request.budget)
            .map_err(|e| match e {
                L1LpError::IterationBudgetExceeded { .. } => refuse("UNKNOWN_BUDGET", e),
                _ => refuse("REFUSED_NATIVE_SOLVER", e),
            })?;
    // A zero-row map loses its column dimension at the old solver's row seam.
    if m == 0 {
        solution.coefficients = vec![Exact::zero(); n];
    }
    Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: request.reading.clone(),
        d0: map.clone(),
        weights: request.weights.clone(),
        alpha: solution.coefficients.clone(),
        primal_residual: solution.residual.clone(),
        dual_witness: solution.dual.clone(),
        reported_value: solution.value.clone(),
    })
    .map_err(|e| refuse("REFUSED_NATIVE_CERTIFICATE", e))?;
    let mut algorithm_status = "certified_optimum_not_exhaustive_ties";
    let mut enumeration_status = "NOT_APPLICABLE_CAPACITY";
    let mut basic_subsets = None;
    let mut ties = vec![(
        solution.coefficients.clone(),
        request
            .reading
            .iter()
            .zip(&solution.residual)
            .map(|(a, b)| a - b)
            .collect::<Vec<Exact>>(),
    )];
    match exhaustive_ties(&selected, &request.reading, &request.weights) {
        Ok(candidates) => {
            if reinject(candidates.value) != solution.value {
                return Err(refuse(
                    "REFUSED_NATIVE_CERTIFICATE",
                    "bounded primal and arbitrary-precision dual disagree",
                ));
            }
            ties.clear();
            for candidate in candidates.ties.iter().take(candidates.tie_count) {
                let g: Vec<Exact> = candidate.potential[..n]
                    .iter()
                    .copied()
                    .map(reinject)
                    .collect();
                let e: Vec<Exact> = candidate.exact_part[..m]
                    .iter()
                    .copied()
                    .map(reinject)
                    .collect();
                Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
                    omega: request.reading.clone(),
                    d0: map.clone(),
                    weights: request.weights.clone(),
                    alpha: g.clone(),
                    primal_residual: request.reading.iter().zip(&e).map(|(a, b)| a - b).collect(),
                    dual_witness: solution.dual.clone(),
                    reported_value: solution.value.clone(),
                })
                .map_err(|error| refuse("REFUSED_NATIVE_CERTIFICATE", error))?;
                ties.push((g, e));
            }
            ties.sort_by(|a, b| a.1.cmp(&b.1));
            solution.coefficients = ties[0].0.clone();
            algorithm_status = "certified_optimum_exhaustive_basic_ties_bounded_profile";
            enumeration_status = "STACK_ONLY_CHECKED_I128_CANDIDATES";
            basic_subsets = Some(candidates.subsets);
        }
        Err(CandidateError::Capacity) => {}
        Err(CandidateError::Overflow) => {
            enumeration_status = "NOT_APPLICABLE_OVERFLOW";
        }
        Err(error) => return Err(refuse("REFUSED_BOUNDED_ENUMERATION", format!("{error:?}"))),
    }
    let next_rows: Vec<Vec<Exact>> = match mats.get(&(request.degree + 1)) {
        Some(next) => (0..next.rows())
            .map(|i| {
                (0..next.cols())
                    .map(|j| {
                        next.get(i, j)
                            .map(Exact::from_integer)
                            .map_err(|e| refuse("REFUSED_SHAPE", e))
                    })
                    .collect::<Result<Vec<_>, _>>()
            })
            .collect::<Result<Vec<_>, _>>()?,
        None => vec![],
    };
    let gamma =
        core_functional::gamma2::Gamma2Functional::try_compute_raw(&request.reading, &next_rows)
            .map_err(|e| refuse("REFUSED_SHAPE", e.to_string()))?
            .value()
            .clone();
    let class = if solution.value.is_zero() {
        "EXACT"
    } else if gamma.is_zero() {
        "SURVIVOR"
    } else {
        "OPEN"
    };
    let raw_complex = &payload["complex"];
    let (integer_status, integer_cert) = if request.include_integer {
        integer_certificate(raw_complex, &request, &selected)?
    } else {
        ("NOT_REQUESTED".into(), Value::Null)
    };
    Ok(json!({
        "schema_version": "core.genesis.resolve-result.v1", "authority_effect": "None",
        "input_digest": framed_sha256(INPUT_DOMAIN, &crate::protocol::canonical_json(payload)),
        "certificate": {
            "schema": "recurring_genesis/potential-certificate/v1", "authority_effect": "None",
            "layer": "DECLARED_REALIZATION", "complex": raw_complex, "degree": request.degree,
            "reading_id": request.reading_id, "reading": document_vec(&request.reading), "weights": document_vec(&request.weights),
            "primal": {"potential": document_vec(&solution.coefficients), "value": document_q(&solution.value)},
            "dual": {"cycle": document_vec(&solution.dual)}, "gamma": document_q(&gamma), "class": class,
            "ties": ties.iter().map(|(g,e)| json!({"potential": document_vec(g), "exact_part": document_vec(e)})).collect::<Vec<_>>()
        },
        "integer_certificate": integer_cert, "integer_status": integer_status,
        "duality_gap": "0/1", "iterations": solution.iterations,
        "algorithm_status": algorithm_status,
        "allocation_status": "heap_allocating_existing_exact_simplex",
        "basic_enumeration_status": enumeration_status, "basic_subsets": basic_subsets,
        "basic_enumeration_bounds": {"max_rows": stack::MAX_ROWS,"max_cols": stack::MAX_COLS,"subset_budget":256}
    }))
}

// Origin: engine/crates_rs/pfp/src/genesis_resolution.rs
// Claim: urn:core:crates_rs:pfp:genesis-resolution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn triangle() -> Value {
        json!({"complex": {"cells": {"-1": [], "0": ["a", "b", "c"], "1": ["ab", "bc", "ca"]},
            "boundary": {"0": [[], [], []], "1": [[-1, 1, 0], [0, -1, 1], [1, 0, -1]]}},
            "degree": 1, "reading_id": "triangle", "reading": ["1", "1", "1"],
            "weights": ["1", "2", "2"], "budget": 1024})
    }

    #[test]
    fn weighted_survivor_and_integer_obstruction_have_exact_certificates() {
        let result = resolve(&triangle()).unwrap();
        assert_eq!(result["certificate"]["primal"]["value"], "3/1");
        assert_eq!(result["certificate"]["class"], "SURVIVOR");
        assert_eq!(result["integer_status"], "Z_OBSTRUCTED");
        assert_eq!(result["integer_certificate"]["kind"], "RATIONAL");
    }

    #[test]
    fn boundary_chain_float_weight_shape_and_budget_fail_closed() {
        let mut bad = triangle();
        bad["weights"][0] = json!("0");
        assert!(resolve(&bad)
            .unwrap_err()
            .starts_with("REFUSED_WEIGHT_NOT_POSITIVE"));
        bad = triangle();
        bad["reading"][0] = json!(0.5);
        assert!(resolve(&bad).unwrap_err().starts_with("REFUSED_FLOAT"));
        bad = triangle();
        bad["reading"][0] = json!("0.5");
        assert!(resolve(&bad).unwrap_err().starts_with("REFUSED_FLOAT"));
        bad = triangle();
        bad["complex"]["boundary"]["1"][0] = json!([1]);
        assert!(resolve(&bad).unwrap_err().starts_with("REFUSED_SHAPE"));
        bad = triangle();
        bad["budget"] = json!(0);
        assert!(resolve(&bad).unwrap_err().starts_with("UNKNOWN_BUDGET"));
        bad = triangle();
        bad["budget"] = json!(100_001);
        assert!(resolve(&bad).unwrap_err().starts_with("REFUSED_CAPACITY"));
        bad = triangle();
        bad["complex"]["cells"]["2"] = json!(["f"]);
        bad["complex"]["boundary"]["2"] = json!([[1, 0, 0]]);
        assert!(resolve(&bad)
            .unwrap_err()
            .starts_with("REFUSED_CHAIN_CONDITION"));
    }
}
