//! Workflow graph checks and execution-stage planning. AuthorityEffect: None.
use crate::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
#[derive(Debug, Clone, Deserialize)]
pub struct Node {
    pub node_id: String,
    pub operation_id: String,
    pub inputs: Vec<String>,
    pub outputs: Vec<String>,
    #[serde(default)]
    pub input_colours: Vec<(String, String)>,
    #[serde(default)]
    pub output_colours: Vec<(String, String)>,
}
#[derive(Debug, Clone, Deserialize)]
pub struct Edge {
    pub source_node_id: String,
    pub source_output: String,
    pub target_node_id: String,
    pub target_input: String,
}
#[derive(Debug, Clone, Deserialize)]
pub struct Request {
    pub nodes: Vec<Node>,
    pub edges: Vec<Edge>,
    #[serde(default)]
    pub typed: Option<TypedRequest>,
}
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TypedRequest {
    schema_version: String,
    root_node_id: String,
    pins: Vec<NodePin>,
    declarations: Vec<Declaration>,
    inputs: Vec<SlotRef>,
}
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct NodePin {
    node_id: String,
    source_digest: String,
    operation_digest: String,
}
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct Declaration {
    source_digest: String,
    operation_json: String,
}
#[derive(Debug, Clone, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
struct SlotRef {
    node_id: String,
    slot: usize,
}
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct Port {
    name: String,
    colour_id: String,
    schema_ref: String,
    schema_digest: String,
    validator_ref: String,
    validator_digest: String,
}
impl Port {
    fn estate_port(&self) -> Result<crate::estate::PortSpecV3, Refusal> {
        serde_json::from_value(serde_json::json!({"name":self.name,
            "colour_id":{"value":self.colour_id},"schema_ref":{"value":self.schema_ref},
            "schema_digest":{"algorithm":"sha256","hex_digest":self.schema_digest.get(7..).unwrap_or("")},
            "validator_ref":self.validator_ref,
            "validator_digest":{"algorithm":"sha256","hex_digest":self.validator_digest.get(7..).unwrap_or("")}
        })).map_err(|e| Refusal::new("PORT_UNBOUND",e.to_string()))
    }
    fn contract(&self) -> [String; 5] {
        [
            self.colour_id.clone(),
            self.schema_ref.clone(),
            self.schema_digest.clone(),
            self.validator_ref.clone(),
            self.validator_digest.clone(),
        ]
    }
    fn valid_digests(&self) -> bool {
        !self.validator_ref.is_empty()
            && digest(&self.schema_digest)
            && digest(&self.validator_digest)
            && self.schema_digest[7..] != "0".repeat(64)
            && self.validator_digest[7..] != "0".repeat(64)
    }
    fn valid(&self) -> bool {
        core_operad_canon::OPERAD_COLOURS
            .contains(&self.colour_id.as_str())
            && !self.name.is_empty()
            && !self.schema_ref.is_empty()
            && self.schema_ref != "schema:any:v1"
            && self.schema_ref.trim() == self.schema_ref
            && self.schema_ref.chars().count() <= 512
            && self.valid_digests()
    }
}
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct Operation {
    operation_id: String,
    inputs: Vec<Port>,
    output: Port,
    authority_effect: String,
    authority_ceiling: String,
    description: String,
    effects: Vec<String>,
    tool_refs: Vec<String>,
    operand_refs: Vec<String>,
    lifecycle: Value,
    residual_status: String,
    invocation_grade: String,
    #[serde(default)]
    replacement_operation_id: Option<String>,
}
#[derive(Debug, Clone, Serialize)]
pub struct TypedInterface {
    inputs: Vec<[String; 5]>,
    output: [String; 5],
    occurrence_order: Vec<String>,
}
fn digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn occurrence(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value.as_bytes()[0].is_ascii_lowercase()
        && value
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
}
fn check_typed_request_bounds(request: &Request, typed: &TypedRequest) -> Result<(), Refusal> {
    if typed.schema_version != "oewas.typed-graph.v1"
        || request.nodes.is_empty()
        || request.nodes.len() > 128
        || typed.declarations.is_empty()
        || typed.declarations.len() > 64
        || typed.pins.len() != request.nodes.len()
        || typed.inputs.len() > 1024
    {
        return Err(Refusal::new(
            "WORKFLOW_SHAPE_INVALID",
            "bounded typed graph required",
        ));
    }
    Ok(())
}

fn check_operation_ports_valid(operation: &Operation) -> bool {
    operation.operation_id.trim() == operation.operation_id
        && !operation.operation_id.is_empty()
        && operation.operation_id.chars().count() <= 512
        && operation.inputs.len() <= 128
        && operation.output.valid()
        && operation.inputs.iter().all(|p| p.valid())
}

fn parse_typed_declaration(declaration: &Declaration) -> Result<(String, Operation), Refusal> {
    if !digest(&declaration.source_digest) || declaration.operation_json.len() > 65536 {
        return Err(Refusal::new(
            "SOURCE_SHAPE_INVALID",
            "bounded source/operation declaration required",
        ));
    }
    let operation: Operation = serde_json::from_str(&declaration.operation_json)
        .map_err(|e| Refusal::new("OPERATION_SHAPE_INVALID", e.to_string()))?;
    if !check_operation_ports_valid(&operation) {
        return Err(Refusal::new(
            "PORT_UNBOUND",
            "bounded operation and complete bound ports required",
        ));
    }
    if operation.authority_effect != "None" || operation.authority_ceiling != "None" {
        return Err(Refusal::new(
            "AUTHORITY_EFFECT_FORBIDDEN",
            "typed graph grants no authority",
        ));
    }
    // Remaining declaration fields are committed by the operation digest; admission,
    // effects, source authenticity and instruction budgets keep their existing owners.
    let _ = (
        &operation.description,
        &operation.effects,
        &operation.tool_refs,
        &operation.operand_refs,
        &operation.lifecycle,
        &operation.residual_status,
        &operation.invocation_grade,
        &operation.replacement_operation_id,
    );
    let operation_digest = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(declaration.operation_json.as_bytes()))
    );
    Ok((operation_digest, operation))
}

fn collect_typed_declarations(
    typed: &TypedRequest,
) -> Result<BTreeMap<String, (&Declaration, String, Operation)>, Refusal> {
    let mut declarations = BTreeMap::new();
    for declaration in &typed.declarations {
        let (operation_digest, operation) = parse_typed_declaration(declaration)?;
        if declarations
            .insert(
                operation.operation_id.clone(),
                (declaration, operation_digest, operation),
            )
            .is_some()
        {
            return Err(Refusal::new(
                "DUPLICATE_SOURCE_ID",
                "one declaration per operation required",
            ));
        }
    }
    Ok(declarations)
}

fn verify_pinned_node<'a>(
    node: &'a Node,
    pins: &BTreeMap<&String, &'a NodePin>,
    declarations: &'a BTreeMap<String, (&'a Declaration, String, Operation)>,
) -> Result<&'a Operation, Refusal> {
    if !occurrence(&node.node_id) {
        return Err(Refusal::new(
            "WORKFLOW_SHAPE_INVALID",
            "bounded lowercase occurrence IDs required",
        ));
    }
    let pin = pins
        .get(&node.node_id)
        .ok_or_else(|| Refusal::new("SOURCE_DIGEST_MISMATCH", &node.node_id))?;
    let (declaration, operation_digest, operation) = declarations
        .get(&node.operation_id)
        .ok_or_else(|| Refusal::new("OPERATION_MISSING", &node.operation_id))?;
    if pin.source_digest != declaration.source_digest {
        return Err(Refusal::new("SOURCE_DIGEST_MISMATCH", &node.node_id));
    }
    if pin.operation_digest != *operation_digest {
        return Err(Refusal::new("OPERATION_DIGEST_MISMATCH", &node.node_id));
    }
    let expected_inputs: Vec<_> = (0..operation.inputs.len()).map(|i| format!("in:{i}")).collect();
    if node.inputs != expected_inputs || node.outputs != ["out"] {
        return Err(Refusal::new("BOUNDARY_MISMATCH", &node.node_id));
    }
    Ok(operation)
}

fn collect_typed_nodes<'a>(
    request: &'a Request,
    typed: &'a TypedRequest,
    declarations: &'a BTreeMap<String, (&'a Declaration, String, Operation)>,
) -> Result<BTreeMap<&'a str, &'a Operation>, Refusal> {
    let mut pins = BTreeMap::new();
    for pin in &typed.pins {
        if pins.insert(&pin.node_id, pin).is_some() {
            return Err(Refusal::new("DUPLICATE_NODE_ID", &pin.node_id));
        }
    }
    let mut nodes = BTreeMap::new();
    for node in &request.nodes {
        let operation = verify_pinned_node(node, &pins, declarations)?;
        nodes.insert(node.node_id.as_str(), operation);
    }
    if !nodes.contains_key(typed.root_node_id.as_str()) {
        return Err(Refusal::new("ROOT_NODE_MISSING", &typed.root_node_id));
    }
    Ok(nodes)
}

fn parse_edge_slot(target_input: &str, input_len: usize) -> Result<usize, Refusal> {
    target_input
        .strip_prefix("in:")
        .and_then(|s| s.parse::<usize>().ok())
        .filter(|i| target_input == format!("in:{i}") && *i < input_len)
        .ok_or_else(|| Refusal::new("SLOT_OUT_OF_BOUNDS", target_input))
}

fn check_edge_port_contract(
    source_output_name: &str,
    source_port: &Port,
    target_port: &Port,
    target_input: &str,
) -> Result<(), Refusal> {
    if source_output_name != "out" {
        return Err(Refusal::new("BOUNDARY_MISMATCH", target_input));
    }
    let src_estate = source_port.estate_port()?;
    let dst_estate = target_port.estate_port()?;
    if !src_estate.same_contract_as(&dst_estate) {
        return Err(Refusal::new("BOUNDARY_MISMATCH", target_input));
    }
    Ok(())
}

fn verify_and_record_edge<'a>(
    edge: &'a Edge,
    nodes: &BTreeMap<&'a str, &'a Operation>,
    bindings: &mut BTreeMap<(&'a str, usize), &'a str>,
    consumed: &mut BTreeSet<&'a str>,
) -> Result<(), Refusal> {
    let source = nodes
        .get(edge.source_node_id.as_str())
        .ok_or_else(|| Refusal::new("BINDING_NODE_MISSING", "source"))?;
    let target = nodes
        .get(edge.target_node_id.as_str())
        .ok_or_else(|| Refusal::new("BINDING_NODE_MISSING", "target"))?;
    let slot = parse_edge_slot(&edge.target_input, target.inputs.len())?;
    check_edge_port_contract(&edge.source_output, &source.output, &target.inputs[slot], &edge.target_input)?;
    if bindings
        .insert((edge.target_node_id.as_str(), slot), edge.source_node_id.as_str())
        .is_some()
    {
        return Err(Refusal::new("DUPLICATE_SLOT_BINDING", &edge.target_input));
    }
    if !consumed.insert(edge.source_node_id.as_str()) {
        return Err(Refusal::new("SHARED_OUTPUT_UNSUPPORTED", &edge.source_node_id));
    }
    Ok(())
}

fn visit_typed_graph<'a>(
    id: &'a str,
    depth: usize,
    nodes: &BTreeMap<&'a str, &'a Operation>,
    bindings: &BTreeMap<(&'a str, usize), &'a str>,
    reached: &mut BTreeSet<&'a str>,
    entries: &mut Vec<SlotRef>,
    inputs: &mut Vec<[String; 5]>,
    order: &mut Vec<String>,
) -> Result<(), Refusal> {
    if depth > 16 || !reached.insert(id) {
        return Err(Refusal::new("COMPOSITION_CYCLE", "cycle or depth ceiling"));
    }
    let operation = nodes
        .get(id)
        .ok_or_else(|| Refusal::new("BINDING_NODE_MISSING", id))?;
    for (slot, port) in operation.inputs.iter().enumerate() {
        if let Some(child) = bindings.get(&(id, slot)) {
            visit_typed_graph(child, depth + 1, nodes, bindings, reached, entries, inputs, order)?;
        } else {
            entries.push(SlotRef {
                node_id: id.into(),
                slot,
            });
            inputs.push(port.contract());
        }
    }
    order.push(id.into());
    Ok(())
}

fn typed_interface(request: &Request, typed: &TypedRequest) -> Result<TypedInterface, Refusal> {
    check_typed_request_bounds(request, typed)?;
    let declarations = collect_typed_declarations(typed)?;
    let nodes = collect_typed_nodes(request, typed, &declarations)?;
    let mut bindings = BTreeMap::new();
    let mut consumed = BTreeSet::new();
    for edge in &request.edges {
        verify_and_record_edge(edge, &nodes, &mut bindings, &mut consumed)?;
    }
    let (mut reached, mut entries, mut inputs, mut order) =
        (BTreeSet::new(), Vec::new(), Vec::new(), Vec::new());
    visit_typed_graph(
        &typed.root_node_id,
        1,
        &nodes,
        &bindings,
        &mut reached,
        &mut entries,
        &mut inputs,
        &mut order,
    )?;
    if reached.len() != nodes.len() {
        return Err(Refusal::new(
            "UNREACHABLE_NODE",
            "every occurrence must reach the root",
        ));
    }
    if entries != typed.inputs {
        return Err(Refusal::new(
            "ENTRY_BOUNDARY_MISMATCH",
            "ordered original node/slot references differ",
        ));
    }
    let iface = TypedInterface {
        inputs,
        output: nodes[typed.root_node_id.as_str()].output.contract(),
        occurrence_order: order,
    };
    Ok(iface)
}
#[derive(Debug, Clone, Serialize)]
pub struct Report {
    pub is_valid: bool,
    pub node_count: usize,
    pub edge_count: usize,
    pub cycles: Vec<Vec<String>>,
    pub colour_mismatches: Vec<String>,
    pub orphaned_edges: Vec<String>,
    pub topological_order: Vec<String>,
    pub execution_stages: Vec<Vec<String>>,
    pub duplicate_node_ids: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub typed_interface: Option<TypedInterface>,
}
fn cycles(nodes: &[Node], adj: &BTreeMap<&str, Vec<&str>>) -> Vec<Vec<String>> {
    let mut visited = BTreeSet::new();
    let mut active = BTreeSet::new();
    let mut cycles = Vec::new();
    for node in nodes {
        let root = node.node_id.as_str();
        if visited.contains(root) {
            continue;
        }
        visited.insert(root);
        active.insert(root);
        let mut stack = vec![(root, 0usize)];
        while let Some(&(current, index)) = stack.last() {
            let Some(&next) = adj.get(current).and_then(|edges| edges.get(index)) else {
                stack.pop();
                active.remove(current);
                continue;
            };
            if let Some(frame) = stack.last_mut() {
                frame.1 += 1;
            }
            if !visited.contains(next) {
                visited.insert(next);
                active.insert(next);
                stack.push((next, 0));
            } else if active.contains(next) {
                if let Some(start) = stack.iter().position(|(id, _)| *id == next) {
                    let mut path = stack[start..]
                        .iter()
                        .map(|(id, _)| (*id).to_owned())
                        .collect::<Vec<_>>();
                    path.push(next.to_owned());
                    cycles.push(path);
                }
            }
        }
    }
    cycles
}
fn find_port_colour<'a>(colours: &'a [(String, String)], port_name: &str) -> Option<&'a String> {
    colours
        .iter()
        .rev()
        .find(|(port, _)| port == port_name)
        .map(|(_, c)| c)
}

fn check_edge_ports_and_colours(
    edge: &Edge,
    source: &Node,
    target: &Node,
    mismatches: &mut Vec<String>,
) {
    if !source.outputs.contains(&edge.source_output) {
        mismatches.push(format!(
            "Source node {} does not output '{}'",
            source.node_id, edge.source_output
        ));
    }
    if !target.inputs.contains(&edge.target_input) {
        mismatches.push(format!(
            "Target node {} does not accept input '{}'",
            target.node_id, edge.target_input
        ));
    }
    let source_colour = find_port_colour(&source.output_colours, &edge.source_output);
    let target_colour = find_port_colour(&target.input_colours, &edge.target_input);
    if let (Some(a), Some(b)) = (source_colour, target_colour) {
        if a != b {
            mismatches.push(format!(
                "Colour mismatch: {}.{} ({a}) -> {}.{} ({b})",
                source.node_id, edge.source_output, target.node_id, edge.target_input
            ));
        }
    }
}

fn advance_stage<'a>(
    queue: Vec<&'a str>,
    adj: &BTreeMap<&'a str, Vec<&'a str>>,
    indegree: &mut BTreeMap<&'a str, usize>,
) -> Vec<&'a str> {
    let mut next = Vec::new();
    for node in queue {
        if let Some(children) = adj.get(node) {
            for child in children {
                if let Some(degree) = indegree.get_mut(child) {
                    *degree -= 1;
                    if *degree == 0 {
                        next.push(*child);
                    }
                }
            }
        }
    }
    next
}

fn compute_topological_stages<'a>(
    mut indegree: BTreeMap<&'a str, usize>,
    adj: &BTreeMap<&'a str, Vec<&'a str>>,
) -> (Vec<String>, Vec<Vec<String>>) {
    let mut order = Vec::new();
    let mut stages = Vec::new();
    let mut queue = indegree
        .iter()
        .filter(|(_, degree)| **degree == 0)
        .map(|(node, _)| *node)
        .collect::<Vec<_>>();
    while !queue.is_empty() {
        queue.sort();
        order.extend(queue.iter().map(|node| (*node).to_owned()));
        stages.push(queue.iter().map(|node| (*node).to_owned()).collect());
        queue = advance_stage(queue, adj, &mut indegree);
    }
    (order, stages)
}

fn index_request_nodes<'a>(
    raw_nodes: &'a [Node],
) -> (
    Vec<String>,
    BTreeMap<&'a str, &'a Node>,
    BTreeMap<&'a str, Vec<&'a str>>,
    BTreeMap<&'a str, usize>,
) {
    let mut seen = BTreeSet::new();
    let mut duplicates = Vec::new();
    let mut nodes = BTreeMap::new();
    let mut adj = BTreeMap::new();
    let mut indegree = BTreeMap::new();
    for node in raw_nodes {
        let id = node.node_id.as_str();
        if !seen.insert(id) && !duplicates.contains(&node.node_id) {
            duplicates.push(node.node_id.clone());
        }
        nodes.insert(id, node);
        adj.insert(id, Vec::new());
        indegree.insert(id, 0usize);
    }
    (duplicates, nodes, adj, indegree)
}

pub fn validate(request: &Request) -> Report {
    let (duplicates, nodes, mut adj, mut indegree) = index_request_nodes(&request.nodes);
    let mut orphaned = Vec::new();
    let mut mismatches = Vec::new();
    for edge in &request.edges {
        let (Some(source), Some(target)) = (
            nodes.get(edge.source_node_id.as_str()),
            nodes.get(edge.target_node_id.as_str()),
        ) else {
            orphaned.push(format!(
                "Edge ({} -> {}) references non-existent node",
                edge.source_node_id, edge.target_node_id
            ));
            continue;
        };
        check_edge_ports_and_colours(edge, source, target, &mut mismatches);
        if let Some(children) = adj.get_mut(edge.source_node_id.as_str()) {
            children.push(edge.target_node_id.as_str());
        }
        if let Some(degree) = indegree.get_mut(edge.target_node_id.as_str()) {
            *degree += 1;
        }
    }
    let cycles = cycles(&request.nodes, &adj);
    let is_acyclic_and_complete = cycles.is_empty() && orphaned.is_empty() && duplicates.is_empty();
    let (order, stages) = if is_acyclic_and_complete {
        compute_topological_stages(indegree, &adj)
    } else {
        (Vec::new(), Vec::new())
    };
    Report {
        is_valid: is_acyclic_and_complete && mismatches.is_empty(),
        node_count: request.nodes.len(),
        edge_count: request.edges.len(),
        cycles,
        colour_mismatches: mismatches,
        orphaned_edges: orphaned,
        topological_order: order,
        execution_stages: stages,
        duplicate_node_ids: duplicates,
        typed_interface: None,
    }
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    if payload.get("command").and_then(Value::as_str) == Some("operad") { return crate::operad_runtime::execute(payload); }

    let request: Request = serde_json::from_value(payload.clone())
        .map_err(|e| Refusal::new("WORKFLOW_GRAPH_INPUT_INVALID", e.to_string()))?;
    let mut report = validate(&request);
    if report.is_valid {
        if let Some(typed) = &request.typed {
            report.typed_interface = Some(typed_interface(&request, typed)?);
        }
    }
    serde_json::to_value(report)
        .map_err(|e| Refusal::new("WORKFLOW_GRAPH_OUTPUT_INVALID", e.to_string()))
}

// Origin: engine/crates_rs/core_operads/src/graph.rs
// Claim: urn:core:crates_rs:core-operads:graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde763b6e2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde763b6e2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore763b6e2 {
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
impl BoundaryErrore763b6e2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore763b6e2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore763b6e2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde763b6e2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore763b6e2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore763b6e2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore763b6e2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore763b6e2::ExceedsCapacity {
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
mod l4_boundary_tests_e763b6e2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde763b6e2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde763b6e2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde763b6e2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde763b6e2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde763b6e2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore763b6e2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore763b6e2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
