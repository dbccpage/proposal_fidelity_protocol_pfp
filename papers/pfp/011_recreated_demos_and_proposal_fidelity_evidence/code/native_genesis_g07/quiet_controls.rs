//! Supplemental quiet-state replay using the already-built unchanged primitives.
use std::collections::BTreeSet;
use std::io::{self, Read};
use core_ooutwire_primitives::closure::closure_challenge_orbits;
use core_ooutwire_primitives::event::Event;
use core_ooutwire_primitives::mark::{Mark, Pair};
use core_ooutwire_primitives::replay::replay;
use core_ooutwire_primitives::token::Token;
use serde_json::{json, Value};

fn n(value: &Value, key: &str) -> Result<usize, String> {
    value[key].as_u64().map(|n| n as usize).ok_or_else(|| format!("INVALID_INTEGER:{key}"))
}
fn s<'a>(value: &'a Value, key: &str) -> Result<&'a str, String> {
    value[key].as_str().ok_or_else(|| format!("INVALID_STRING:{key}"))
}
fn execute(input: Value) -> Result<Value, String> {
    if s(&input, "schema")? != "paper011.g07-quiet-request.v1" { return Err("SCHEMA_REFUSED".into()); }
    let cases = input["cases"].as_array().ok_or("CASES_NOT_ARRAY")?;
    if cases.is_empty() || cases.len() > 128 { return Err("CASE_CEILING".into()); }
    let mut ids = BTreeSet::new();
    let mut rows = Vec::new();
    for case in cases {
        let id = s(case, "id")?;
        if !ids.insert(id.to_owned()) { return Err("DUPLICATE_CASE".into()); }
        let depth = n(case, "depth")?;
        if depth > 60 { return Err("DEPTH_CEILING".into()); }
        let history = case["history"].as_array().ok_or("HISTORY_NOT_ARRAY")?;
        if history.is_empty() || history.len() > 400 { return Err("HISTORY_CEILING".into()); }
        let events = history.iter().map(|event| Ok(match s(event, "kind")? {
            "Supply" => Event::Supply(Token::new(s(event, "token")?)),
            "AdmitDatum" => Event::AdmitDatum(Token::new(s(event, "token")?)),
            "AdmitForm" => Event::AdmitForm(n(event, "arity")?),
            "AdmitRuleAll" => Event::AdmitRuleAll(n(event, "form")?),
            "AdmitInst" => Event::AdmitInst(n(event, "form")?, event["args"].as_array().ok_or("INVALID_ARGS")?.iter()
                .map(|arg| arg.as_u64().map(|i| Mark(i as usize)).ok_or("INVALID_MARK".to_string())).collect::<Result<Vec<_>, _>>()?),
            "Impose" => {
                let i = n(event, "i")?; let j = n(event, "j")?;
                if i >= j { return Err("INVALID_PAIR".to_string()); }
                Event::Impose(Pair::of(i, j))
            }
            _ => return Err("UNKNOWN_EVENT".to_string()),
        })).collect::<Result<Vec<_>, String>>()?;
        let regime = replay(&events).map_err(|err| format!("HISTORY_REFUSED:{err}"))?;
        if regime.n_data() > 32 { return Err("CARRIER_CEILING".into()); }
        let targets = closure_challenge_orbits(&regime).map_err(|err| format!("ISO_BUDGET:{err}"))?;
        if !targets.is_empty() { return Err(format!("NONQUIET_STATE:{id}")); }
        rows.push(json!({"id": id, "depth": depth, "width": null, "offered_challenges": [],
            "state": {"data": regime.data().iter().map(Token::text).collect::<Vec<_>>(), "forms": regime.forms(),
                "insts": regime.insts().iter().map(|inst| json!([inst.form, inst.args.iter().map(|m| m.0).collect::<Vec<_>>()])).collect::<Vec<_>>(),
                "rules": regime.rules().iter().copied().collect::<Vec<_>>(),
                "reqs": regime.reqs().iter().map(|p| vec![p.i.0, p.j.0]).collect::<Vec<_>>()}}));
    }
    Ok(json!({"schema": "paper011.g07-quiet-response.v1", "cases": rows}))
}
fn main() {
    let mut raw = Vec::new(); io::stdin().take(2 * 1024 * 1024 + 1).read_to_end(&mut raw).unwrap();
    if raw.len() > 2 * 1024 * 1024 { eprintln!("REQUEST_CEILING"); std::process::exit(2); }
    match serde_json::from_slice(&raw).map_err(|err| err.to_string()).and_then(execute) {
        Ok(result) => println!("{}", result),
        Err(reason) => { eprintln!("{reason}"); std::process::exit(2); }
    }
}
