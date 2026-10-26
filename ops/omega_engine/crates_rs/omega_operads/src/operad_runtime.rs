//! Bounded planar inventory terms, normalized by the existing sovereign kernel.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_776740b9<T> {
    fn checked_invariant_776740b9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_776740b9<T> for Option<T> {
    #[inline]
    fn checked_invariant_776740b9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_776740b9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_776740b9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::Refusal;
use omega_operad_theory::kernel::{
    model::{AuthorityEffect, InvocationGrade, OperationSpec, OperationSpecInput, PortSpec},
    terms::{normalize_term, OperationTerm},
};
use omega_operad_theory::kernel::{InputPermutation, ReindexedTerm};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    command: String,
    inventory_json: String,
    wire: Value,
    #[serde(default)]
    values: Option<Vec<Value>>,
    #[serde(default)]
    input_order: Option<Vec<usize>>,
}
#[derive(Deserialize)]
struct Inventory {
    schema_version: String,
    skills: Vec<Skill>,
}
#[derive(Deserialize)]
struct Skill {
    ops: Vec<Op>,
    #[serde(default)]
    anti_ops: Vec<Guard>,
}
#[derive(Clone, Deserialize)]
struct Op {
    op_id: String,
    inputs: Vec<String>,
    output: String,
    binding: Option<Value>,
}
#[derive(Deserialize, serde::Serialize)]
struct Guard {
    op_id: String,
    guards: String,
    slot: usize,
    inspects: String,
    refusal: String,
}
fn bad(code: &str, message: impl Into<String>) -> Refusal {
    Refusal::new(code, message)
}
fn sha(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn port(index: usize, colour: &str) -> Result<PortSpec, Refusal> {
    PortSpec::new(
        &format!("slot{index}"),
        colour,
        &format!("inventory:{colour}:v1"),
    )
    .map_err(|e| bad("PORT_INVALID", e.to_string()))
}
fn primitive(op: &Op) -> Result<OperationTerm, Refusal> {
    let binding =
        serde_json::to_vec(&op.binding).map_err(|e| bad("BINDING_INVALID", e.to_string()))?;
    let spec = OperationSpec::new(OperationSpecInput {
        operation_id: &op.op_id,
        version: "v3",
        input_ports: op
            .inputs
            .iter()
            .enumerate()
            .map(|(i, c)| port(i, c))
            .collect::<Result<_, _>>()?,
        output_port: port(0, &op.output)?,
        executor_ref: "inventory-binding",
        executor_digest: &format!("sha256:{}", sha(&binding)),
        tool_refs: vec![],
        effects: vec![],
        invocation_grade: InvocationGrade::Discipline,
        authority_effect: AuthorityEffect::None,
        authority_ceiling: AuthorityEffect::None,
    })
    .map_err(|e| bad("OPERATION_INVALID", e.to_string()))?;
    Ok(OperationTerm::Primitive(spec))
}
fn parse_wire_pair(w: &Value) -> Result<(&str, &[Value]), Refusal> {
    let obj = w
        .as_object()
        .ok_or_else(|| bad("WIRE_INVALID", "wire must be input or op/args"))?;
    if obj.len() != 2 {
        return Err(bad("WIRE_INVALID", "only op/args allowed"));
    }
    let id = w["op"]
        .as_str()
        .ok_or_else(|| bad("WIRE_INVALID", "missing op"))?;
    let args = w["args"]
        .as_array()
        .ok_or_else(|| bad("WIRE_INVALID", "missing args"))?;
    Ok((id, args.as_slice()))
}
fn extract_wire_op<'a>(
    w: &'a Value,
    ops: &'a BTreeMap<String, Op>,
) -> Result<(&'a str, &'a Op, &'a [Value]), Refusal> {
    let (id, args) = parse_wire_pair(w)?;
    let op = ops.get(id).ok_or_else(|| bad("UNKNOWN_OPERATION", id))?;
    if args.len() != op.inputs.len() {
        return Err(bad("ARITY_MISMATCH", id));
    }
    Ok((id, op, args))
}
fn substitute_children(
    mut result: OperationTerm,
    args: &[Value],
    ops: &BTreeMap<String, Op>,
    leaves: &mut Vec<String>,
    used: &mut Vec<String>,
    depth: usize,
) -> Result<OperationTerm, Refusal> {
    let mut slot = 0;
    for child in args {
        let child_term = term(child, ops, leaves, used, depth + 1)?;
        let child_norm = normalize_term(&child_term).map_err(|e| bad(&e.code, e.message))?;
        let arity = child_norm.boundary().inputs.len();
        result = OperationTerm::Substitute {
            outer: Box::new(result),
            slot,
            inner: Box::new(child_term),
        };
        normalize_term(&result).map_err(|e| bad(&e.code, e.message))?;
        slot += arity;
    }
    Ok(result)
}
fn term(
    w: &Value,
    ops: &BTreeMap<String, Op>,
    leaves: &mut Vec<String>,
    used: &mut Vec<String>,
    depth: usize,
) -> Result<OperationTerm, Refusal> {
    if depth > 32 || used.len() > 128 || leaves.len() > 128 {
        return Err(bad("TERM_LIMIT", "maximum depth32 and128 occurrences"));
    }
    if let Some(colour) = w.as_str() {
        leaves.push(colour.into());
        let p = port(leaves.len() - 1, colour)?;
        return Ok(OperationTerm::Identity(p));
    }
    let (id, op, args) = extract_wire_op(w, ops)?;
    used.push(id.into());
    let base = primitive(op)?;
    substitute_children(base, args, ops, leaves, used, depth)
}
fn eval_native_sum(args: Vec<Value>) -> Result<Value, Refusal> {
    let mut total = 0i64;
    for arg in args {
        let val = arg
            .as_i64()
            .ok_or_else(|| bad("VALUE_INVALID", "exact i64 expected"))?;
        total = total
            .checked_add(val)
            .ok_or_else(|| bad("VALUE_OVERFLOW", "sum"))?;
    }
    Ok(json!(total))
}
fn eval_target(id: &str, target: &str, args: Vec<Value>) -> Result<Value, Refusal> {
    match target {
        "native:identity" if args.len() == 1 => Ok(args[0].clone()),
        "native:pair" if args.len() == 2 => Ok(json!(args)),
        "native:sum" => eval_native_sum(args),
        _ => Err(bad(
            "NOT_EXECUTABLE",
            format!("{id}: external host/PFP binding needs its registered executor"),
        )),
    }
}
fn eval(
    w: &Value,
    ops: &BTreeMap<String, Op>,
    values: &[Value],
    cursor: &mut usize,
) -> Result<Value, Refusal> {
    if w.is_string() {
        let result = values
            .get(*cursor)
            .cloned()
            .ok_or_else(|| bad("MISSING_INPUT", "input occurrence"))?;
        *cursor += 1;
        return Ok(result);
    }
    let id = w["op"].as_str().ok_or_else(|| bad("WIRE_INVALID", "op"))?;
    let op = &ops[id];
    let raw_args = w["args"]
        .as_array()
        .ok_or_else(|| bad("WIRE_INVALID", "args"))?;
    let args = raw_args
        .iter()
        .map(|a| eval(a, ops, values, cursor))
        .collect::<Result<Vec<_>, _>>()?;
    let target = op
        .binding
        .as_ref()
        .and_then(|v| v.get("target"))
        .and_then(Value::as_str)
        .unwrap_or("");
    eval_target(id, target, args)
}
fn execution_plan(
    w: &Value,
    leaves: &mut usize,
    steps: &mut Vec<Value>,
    guards: &[Guard],
) -> Value {
    if w.is_string() {
        let index = *leaves;
        *leaves += 1;
        return json!({"input":index});
    }
    let args = w["args"]
        .as_array()
        .into_iter()
        .flatten()
        .map(|a| execution_plan(a, leaves, steps, guards))
        .collect::<Vec<_>>();
    let id = w["op"].as_str().unwrap_or("");
    let index = steps.len();
    steps.push(json!({"op_id":id,"args":args,"guards":guards.iter().filter(|g|g.guards==id).collect::<Vec<_>>()}));
    json!({"step":index})
}
fn reindex_reference(reference: &mut Value, planar_to_external: &[usize]) {
    if let Some(index) = reference.get("input").and_then(Value::as_u64) {
        reference["input"] = json!(planar_to_external[index as usize]);
    }
}
fn load_inventory(req: &Request) -> Result<(BTreeMap<String, Op>, Vec<Guard>), Refusal> {
    if req.command != "operad" || req.inventory_json.len() > 49152 {
        return Err(bad("INVENTORY_INVALID", "command or inventory limit"));
    }
    let inv: Inventory = serde_json::from_str(&req.inventory_json)
        .map_err(|e| bad("INVENTORY_INVALID", e.to_string()))?;
    if !["omega.oewas.op_inventory.v2", "omega.oewas.op_inventory.v3"]
        .contains(&inv.schema_version.as_str())
    {
        return Err(bad("INVENTORY_VERSION", inv.schema_version));
    }
    let mut ops = BTreeMap::new();
    let mut guards = vec![];
    for skill in inv.skills {
        for op in skill.ops {
            if ops.insert(op.op_id.clone(), op).is_some() {
                return Err(bad("DUPLICATE_OPERATION", "inventory"));
            }
        }
        guards.extend(skill.anti_ops);
    }
    verify_guards(&ops, &guards)?;
    Ok((ops, guards))
}
fn verify_guards(ops: &BTreeMap<String, Op>, guards: &[Guard]) -> Result<(), Refusal> {
    for g in guards {
        let op = ops
            .get(&g.guards)
            .ok_or_else(|| bad("GUARD_SLOT_INVALID", &g.op_id))?;
        if op.inputs.get(g.slot) != Some(&g.inspects) {
            return Err(bad("GUARD_SLOT_INVALID", &g.op_id));
        }
    }
    Ok(())
}
fn build_reindexed_term(
    parsed: &OperationTerm,
    input_order: Option<Vec<usize>>,
) -> Result<Option<ReindexedTerm>, Refusal> {
    input_order
        .map(|order| {
            let permutation = InputPermutation::new(order).map_err(|e| bad(&e.code, e.message))?;
            ReindexedTerm::new(parsed, permutation).map_err(|e| bad(&e.code, e.message))
        })
        .transpose()
}
fn evaluate_if_requested(
    wire: &Value,
    values: Option<Vec<Value>>,
    ops: &BTreeMap<String, Op>,
    leaves: &[String],
    selected: &[Guard],
    reindexed: &Option<ReindexedTerm>,
) -> Result<Option<Value>, Refusal> {
    let Some(values) = values else {
        return Ok(None);
    };
    if values.len() != leaves.len() {
        return Err(bad("MISSING_INPUT", "ordered leaf count"));
    }
    if !selected.is_empty() {
        return Err(bad("NOT_EXECUTABLE", "host detectors are required"));
    }
    let planar_values = match reindexed {
        Some(term) => term
            .route_inputs(&values)
            .map_err(|e| bad(&e.code, e.message))?,
        None => values,
    };
    let evaluated = eval(wire, ops, &planar_values, &mut 0)?;
    Ok(Some(evaluated))
}
fn apply_reindexing(
    term: &ReindexedTerm,
    plan: &mut [Value],
    output_ref: &mut Value,
    leaves: &mut Vec<String>,
) {
    let inverse = term.permutation().inverse();
    for step in plan {
        for reference in step["args"]
            .as_array_mut()
            .checked_invariant_776740b9("constructed plan arguments")
        {
            reindex_reference(reference, inverse.as_slice());
        }
    }
    reindex_reference(output_ref, inverse.as_slice());
    *leaves = term
        .permutation()
        .as_slice()
        .iter()
        .map(|&index| leaves[index].clone())
        .collect();
}
fn resolve_canonical_term(
    normalized: &omega_operad_theory::kernel::terms::NormalizedTerm,
    reindexed: &Option<ReindexedTerm>,
) -> Result<(String, Value), Refusal> {
    let (term_id, normal_form) = match reindexed {
        Some(term) => (term.canonical_id(), term.to_canonical()),
        None => (normalized.canonical_id(), normalized.to_canonical()),
    };
    let id = term_id.map_err(|e| bad("TERM_INVALID", e.to_string()))?;
    Ok((id, normal_form))
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let req: Request =
        serde_json::from_value(payload.clone()).map_err(|e| bad("BAD_INPUT", e.to_string()))?;
    let (ops, guards) = load_inventory(&req)?;
    let mut leaves = vec![];
    let mut used = vec![];
    let parsed = term(&req.wire, &ops, &mut leaves, &mut used, 0)?;
    let normalized = normalize_term(&parsed).map_err(|e| bad(&e.code, e.message))?;
    let reindexed = build_reindexed_term(&parsed, req.input_order)?;
    let selected: Vec<_> = guards
        .into_iter()
        .filter(|g| used.contains(&g.guards))
        .collect();
    let request_binding = reindexed.as_ref().map(|term| {
        json!({
            "wire":req.wire, "input_order":term.permutation().as_slice(), "values":req.values
        })
    });
    let output =
        evaluate_if_requested(&req.wire, req.values, &ops, &leaves, &selected, &reindexed)?;
    let mut plan = vec![];
    let mut output_ref = execution_plan(&req.wire, &mut 0, &mut plan, &selected);
    if let Some(term) = &reindexed {
        apply_reindexing(term, &mut plan, &mut output_ref, &mut leaves);
    }
    let (canonical_term_id, normal_form) = resolve_canonical_term(&normalized, &reindexed)?;
    let mut result = json!({"execution_plan":plan,"output_ref":output_ref,"status":"VALID","term_id":canonical_term_id,"inventory_sha256":sha(req.inventory_json.as_bytes()),"operation_ids":used,"leaves":leaves,"guards":selected,"normal_form":normal_form,"output":output,"authority_effect":"None"});
    if let Some(term) = reindexed {
        result["input_order"] = json!(term.permutation().as_slice());
        result["request_binding"] =
            request_binding.checked_invariant_776740b9("explicit action binding");
    }
    Ok(result)
}

// Origin: omega_engine/crates_rs/omega_operads/src/operad_runtime.rs
// Claim: urn:omega:crates_rs:omega-operads:operad-runtime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord776740b9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord776740b9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError776740b9 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError776740b9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError776740b9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError776740b9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord776740b9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError776740b9> {
        if capacity_bound == 0 {
            return Err(BoundaryError776740b9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError776740b9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError776740b9::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn request() -> Value {
        json!({"command":"operad", "inventory_json":json!({
            "schema_version":"omega.oewas.op_inventory.v3", "skills":[{"ops":[{
                "op_id":"pair", "inputs":["Code","Code"], "output":"Code",
                "binding":{"kind":"host","target":"native:pair"}}]}]}).to_string(),
            "wire":{"op":"pair","args":["Code",{"op":"pair","args":["Code","Code"]}]},
            "values":[10,20,30]})
    }
    #[test]
    fn explicit_order_routes_values_and_plan_references() {
        let mut req = request();
        let legacy = execute(&req).unwrap();
        assert_eq!(legacy["output"], json!([10, [20, 30]]));
        assert!(legacy.get("input_order").is_none());
        req["input_order"] = json!([2, 0, 1]);
        let checked = execute(&req).unwrap();
        assert_eq!(checked["output"], json!([20, [30, 10]]));
        assert_eq!(
            checked["execution_plan"][0]["args"],
            json!([{"input":2},{"input":0}])
        );
        assert_eq!(
            checked["execution_plan"][1]["args"],
            json!([{"input":1},{"step":0}])
        );
        assert_ne!(checked["term_id"], legacy["term_id"]);
        assert_eq!(checked["normal_form"]["planar"], legacy["normal_form"]);
    }
    #[test]
    fn malformed_input_orders_refuse_before_native_evaluation() {
        for order in [
            json!([0, 0, 2]),
            json!([0, 1]),
            json!([0, 1, 3]),
            json!([-1, 0, 1]),
            json!([false, 1, 2]),
        ] {
            let mut req = request();
            req["input_order"] = order;
            assert!(execute(&req).is_err());
        }
    }
    fn pair(id: &str) -> OperationTerm {
        primitive(&Op {
            op_id: id.into(),
            inputs: vec!["Code".into(), "Code".into()],
            output: "Code".into(),
            binding: Some(json!({"kind":"host","target":"native:pair"})),
        })
        .unwrap()
    }
    fn sub(a: OperationTerm, i: usize, b: OperationTerm) -> OperationTerm {
        OperationTerm::Substitute {
            outer: Box::new(a),
            slot: i,
            inner: Box::new(b),
        }
    }
    fn key(a: &OperationTerm) -> String {
        normalize_term(a).unwrap().canonical_id().unwrap()
    }
    #[test]
    fn nested_reindexing_disjoint_interchange_and_units() {
        let (a, b, c) = (pair("a"), pair("b"), pair("c"));
        for i in 0..2 {
            for j in 0..2 {
                let lhs = sub(sub(a.clone(), i, b.clone()), i + j, c.clone());
                let rhs = sub(a.clone(), i, sub(b.clone(), j, c.clone()));
                assert_eq!(key(&lhs), key(&rhs));
            }
        }
        assert_eq!(
            key(&sub(sub(a.clone(), 0, b.clone()), 2, c.clone())),
            key(&sub(sub(a.clone(), 1, c.clone()), 0, b.clone()))
        );
        assert_ne!(
            key(&sub(sub(a.clone(), 1, b.clone()), 0, c.clone())),
            key(&sub(a.clone(), 1, sub(b, 0, c)))
        );
        for i in 0..2 {
            assert_eq!(
                key(&a),
                key(&sub(
                    a.clone(),
                    i,
                    OperationTerm::Identity(port(i, "Code").unwrap())
                ))
            );
        }
        assert_eq!(
            key(&a),
            key(&sub(
                OperationTerm::Identity(port(0, "Code").unwrap()),
                0,
                a.clone()
            ))
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_776740b9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord776740b9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord776740b9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord776740b9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord776740b9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord776740b9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError776740b9::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError776740b9::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
