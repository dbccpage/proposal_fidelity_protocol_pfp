//! Thin transport over the already-built exact native matrix owner.
//! Input maps are original cochain matrices d_k: C^k -> C^{k+1}.
//! No elimination algorithm is implemented here. AuthorityEffect: None.
use omega_symbol_game_runtime::rational::RationalMatrix;
use serde_json::{json, Value};
use std::io::{self, Read};

fn audit(case: &Value) -> Result<Value, String> {
    let id = case["case_id"].as_str().ok_or("MISSING_CASE_ID")?;
    let wire = case["matrices"].as_array().ok_or("MISSING_MAPS")?;
    if wire.is_empty() || wire.len() > 8 {
        return Err("MAP_COUNT".into());
    }
    let maps: Vec<RationalMatrix> = wire
        .iter()
        .map(|m| serde_json::from_value(json!({"rows": m})).map_err(|e| format!("EXACT_MAP:{e}")))
        .collect::<Result<_, _>>()?;
    if maps
        .iter()
        .any(|m| m.rows() == 0 || m.cols() == 0 || m.rows() > 128 || m.cols() > 128)
    {
        return Err("CARRIER_BOUND".into());
    }
    let ranks: Vec<usize> = maps
        .iter()
        .map(|m| m.rank().map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    let mut dimensions = vec![maps[0].cols()];
    dimensions.extend(maps.iter().map(|m| m.rows()));
    let mut products = Vec::new();
    let mut closed = true;
    for k in 1..maps.len() {
        let previous = &maps[k - 1];
        let current = &maps[k];
        if current.cols() != previous.rows() {
            return Err("MAP_SHAPE_CHAIN".into());
        }
        let columns = (0..previous.cols())
            .map(|c| {
                let column = (0..previous.rows())
                    .map(|r| previous.get(r, c).clone())
                    .collect::<Vec<_>>();
                current.apply(&column).map_err(|e| e.to_string())
            })
            .collect::<Result<Vec<_>, _>>()?;
        let product = (0..current.rows())
            .map(|r| columns.iter().map(|c| c[r].to_string()).collect::<Vec<_>>())
            .collect::<Vec<_>>();
        let zero = product.iter().flatten().all(|x| x == "0");
        closed &= zero;
        products.push(json!({"degree": k, "product": product, "zero": zero}));
    }
    let betti: Option<Vec<usize>> = if closed {
        Some(
            (0..dimensions.len())
                .map(|k| {
                    let incoming = if k == 0 { 0 } else { ranks[k - 1] };
                    let outgoing = ranks.get(k).copied().unwrap_or(0);
                    dimensions[k]
                        .checked_sub(incoming + outgoing)
                        .ok_or("RANK_NULLITY_FAILURE".to_string())
                })
                .collect::<Result<_, _>>()?,
        )
    } else {
        None
    };
    let mut comparisons = Vec::new();
    if let Some(values) = &betti {
        for (k, actual) in values.iter().enumerate() {
            let key = format!("b{k}");
            if let Some(claim) = case["homology"].get(&key) {
                let declared = claim.as_u64().ok_or("BETTI_CLAIM_TYPE")?;
                comparisons.push(json!({"degree": k, "declared": declared, "actual": actual,
                    "matches": declared == *actual as u64}));
            }
        }
    }
    Ok(
        json!({"case_id": id, "dimensions": dimensions, "ranks": ranks,
        "boundary_products": products, "boundary_law_verified": closed,
        "betti_over_q": betti, "declared_betti_comparisons": comparisons,
        "integer_torsion_verified": false}),
    )
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut bytes = Vec::new();
    io::stdin().take(1_048_577).read_to_end(&mut bytes)?;
    if bytes.len() > 1_048_576 {
        return Err("REQUEST_LIMIT".into());
    }
    let request: Value = serde_json::from_slice(&bytes)?;
    let cases = request["cases"].as_array().ok_or("MISSING_CASES")?;
    if cases.is_empty() || cases.len() > 64 {
        return Err("CASE_COUNT".into());
    }
    let outcomes = cases
        .iter()
        .map(|c| match audit(c) {
            Ok(result) => json!({"case_id": c["case_id"], "success": true, "result": result}),
            Err(error) => json!({"case_id": c["case_id"], "success": false, "error": error}),
        })
        .collect::<Vec<_>>();
    serde_json::to_writer(
        io::stdout().lock(),
        &json!({
            "schema": "paper011.dossier-homology-native.v1", "AuthorityEffect": "None", "cases": outcomes
        }),
    )?;
    println!();
    Ok(())
}
