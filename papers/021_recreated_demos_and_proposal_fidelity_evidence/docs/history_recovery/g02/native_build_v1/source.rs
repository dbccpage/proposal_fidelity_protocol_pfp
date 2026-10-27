//! G02's declared bounded second checker, independent of recursive sublists.
use core_kernel::exact::{integer, to_canonical_string};
use serde_json::{json, Value};
use std::io::{self, Read};

fn census(case: &Value) -> Result<Value, &'static str> {
    let n = case["n"].as_u64().ok_or("NATURAL_N_REQUIRED")?;
    let a = case["a"].as_u64().ok_or("NATURAL_A_REQUIRED")?;
    let b = case["b"].as_u64().ok_or("NATURAL_B_REQUIRED")?;
    if n > 12 {
        return Err("CARRIER_LIMIT_12");
    }
    let mut count: i64 = 0;
    for mask in 0..(1u64 << n) {
        if a < n && (mask & (1u64 << a)) != 0 && (b >= n || (mask & (1u64 << b)) == 0) {
            count += 1;
        }
    }
    Ok(json!({"count":to_canonical_string(&integer(count)), "visited_bitmasks":1u64 << n}))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut raw = Vec::new();
    io::stdin().take(2_097_153).read_to_end(&mut raw)?;
    if raw.len() > 2_097_152 {
        return Err("REQUEST_LIMIT".into());
    }
    let request: Value = serde_json::from_slice(&raw)?;
    let cases = request["cases"].as_array().ok_or("CASE_ARRAY_REQUIRED")?;
    if cases.is_empty() || cases.len() > 2000 {
        return Err("CASE_COUNT_LIMIT".into());
    }
    let outcomes: Vec<_> = cases
        .iter()
        .map(|case| match census(case) {
            Ok(result) => json!({"case_id":case["case_id"],"success":true,"result":result}),
            Err(error) => json!({"case_id":case["case_id"],"success":false,"error":error}),
        })
        .collect();
    serde_json::to_writer(
        io::stdout().lock(),
        &json!({"schema":"paper011.g02-bitmask.v1",
        "AuthorityEffect":"None", "cases":outcomes}),
    )?;
    println!();
    Ok(())
}
