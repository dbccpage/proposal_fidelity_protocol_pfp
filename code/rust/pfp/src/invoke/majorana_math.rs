//! Bounded wire adapters for the paper's native math owners. No local solvers.

use super::{native_functional, native_homology, native_matrix};
use super::{outcome_err, outcome_ok, RuntimeOutcomeV1, RuntimeRequestV1};
use core_kernel::{parse_exact, to_canonical_string, Exact};
use core_majorana::braid_action::MajoranaBraidAction;
use core_majorana::multiqubit_braid::{compile_multiqubit_braid_with_limit, MultiQubitOperation};
use core_majorana::pauli_noise::{
    correlated_cluster_couplings, evaluate_noise_matrix, DeterministicRationalNoiseGenerator,
    LocalMajoranaNoise,
};
use core_majorana::sparse_kitaev::{KitaevWire, MajoranaBilinear};
use core_majorana::{
    build_tetron_array, classify, classify_with_diagnostics, detect_lggr, min_weight_nontrivial,
    repair_capacity_from_distance, ClassifiedReceipt, GF2Matrix, GF2ScheduleStatus, Topology,
};
use serde_json::{json, Value};

const MAX_DIM: usize = 256;
const MAX_STEPS: usize = 4096;
/// Same ceiling as the dense exact-matrix wire. A 6×6 torus has 72 channels.
/// `GF2_DIAGNOSTIC_MAX_ENTRIES` still refuses a payload whose product exceeds 4096.
const GF2_DIAGNOSTIC_MAX_DIM: usize = MAX_DIM;
const GF2_DIAGNOSTIC_MAX_ENTRIES: usize = 4096;
const GF2_DIAGNOSTIC_MAX_BUDGET: usize = 1_000_000;
const TETRON_MAX_CELLS: usize = 64;
const REPAIR_MAX_CYCLES: usize = 256;
const REPAIR_MAX_CYCLE_LEN: usize = 4096;

fn field<'a>(value: &'a Value, name: &str) -> Result<&'a Value, String> {
    value
        .get(name)
        .ok_or_else(|| format!("missing field: {name}"))
}

fn allowed(value: &Value, fields: &[&str]) -> Result<(), String> {
    let object = value.as_object().ok_or("payload must be an object")?;
    if let Some(key) = object.keys().find(|k| !fields.contains(&k.as_str())) {
        return Err(format!("unknown field: {key}"));
    }
    Ok(())
}

fn count(value: &Value, maximum: usize) -> Result<usize, String> {
    let n = value.as_u64().ok_or("expected an unsigned integer")?;
    let n = usize::try_from(n).map_err(|_| "integer exceeds address range")?;
    if n > maximum {
        return Err(format!("dimension or count {n} exceeds limit {maximum}"));
    }
    Ok(n)
}

fn integer(value: &Value) -> Result<i64, String> {
    value.as_i64().ok_or_else(|| "expected an integer".into())
}

fn boolean(value: &Value) -> Result<bool, String> {
    value.as_bool().ok_or_else(|| "expected a boolean".into())
}

fn rational(value: &Value) -> Result<Exact, String> {
    let text = value
        .as_str()
        .ok_or("exact coefficient must be a rational string")?;
    if text.len() > 4096 {
        return Err("coefficient exceeds length limit".into());
    }
    let number = parse_exact(text).map_err(|e| e.to_string())?;
    if to_canonical_string(&number) != text {
        return Err("coefficient must be a canonical rational string".into());
    }
    Ok(number)
}

fn list(value: &Value, maximum: usize) -> Result<&Vec<Value>, String> {
    let items = value.as_array().ok_or("expected an array")?;
    if items.len() > maximum {
        return Err("array exceeds operation limit".into());
    }
    Ok(items)
}

fn pair(value: &Value) -> Result<&Vec<Value>, String> {
    let row = list(value, 2)?;
    if row.len() != 2 {
        return Err("expected a two-element pair".into());
    }
    Ok(row)
}

fn action_value(action: &MajoranaBraidAction) -> Value {
    let n = action.mode_count();
    let rows: Vec<Vec<String>> = action
        .images()
        .iter()
        .map(|image| {
            (1..=n)
                .map(|column| {
                    if column == image.mode {
                        image.sign.to_string()
                    } else {
                        "0".into()
                    }
                })
                .collect()
        })
        .collect();
    json!({"images": action.images().iter().map(|image| json!([image.mode,image.sign])).collect::<Vec<_>>(),
        "determinant":action.determinant_sign(),
        "matrix":{"rows":n,"cols":n,"data":rows}})
}

fn parse_braid_step(step: &Value) -> Result<(usize, bool), String> {
    let step = pair(step)?;
    Ok((count(&step[0], MAX_DIM)?, boolean(&step[1])?))
}

fn braid(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["num_modes", "steps"])?;
    let n = count(field(payload, "num_modes")?, MAX_DIM)?;
    let steps = list(field(payload, "steps")?, MAX_STEPS)?
        .iter()
        .map(parse_braid_step)
        .collect::<Result<Vec<_>, String>>()?;
    let action = MajoranaBraidAction::from_word(n, &steps).map_err(|e| e.to_string())?;
    Ok(action_value(&action))
}

fn parse_single_qubit_op(name: &str, first: usize, arg1: &Value) -> Result<Option<MultiQubitOperation>, String> {
    match name {
        "elementary" => Ok(Some(MultiQubitOperation::Elementary {
            index: first,
            inverse: boolean(arg1)?,
        })),
        "phase" => Ok(Some(MultiQubitOperation::Phase {
            qubit: first,
            inverse: boolean(arg1)?,
        })),
        "hadamard" => Ok(Some(MultiQubitOperation::Hadamard {
            qubit: first,
            inverse: boolean(arg1)?,
        })),
        _ => Ok(None),
    }
}

fn build_multiqubit_op(name: &str, first: usize, arg1: &Value) -> Result<MultiQubitOperation, String> {
    if let Some(op) = parse_single_qubit_op(name, first, arg1)? {
        return Ok(op);
    }
    match name {
        "cnot" => Ok(MultiQubitOperation::Cnot {
            control: first,
            target: count(arg1, MAX_DIM)?,
        }),
        "swap" => Ok(MultiQubitOperation::Swap {
            first,
            second: count(arg1, MAX_DIM)?,
        }),
        _ => Err(format!("unknown multiqubit operation: {name}")),
    }
}

fn parse_multiqubit_op(operation: &Value) -> Result<MultiQubitOperation, String> {
    let row = pair(operation)?;
    let name = row[0].as_str().ok_or("operation name must be a string")?;
    let args = pair(&row[1])?;
    let first = count(&args[0], MAX_DIM)?;
    build_multiqubit_op(name, first, &args[1])
}

fn multiqubit(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["num_qubits", "operations"])?;
    let qubits = count(field(payload, "num_qubits")?, MAX_DIM / 4)?;
    let operations = list(field(payload, "operations")?, MAX_STEPS)?
        .iter()
        .map(parse_multiqubit_op)
        .collect::<Result<Vec<_>, String>>()?;
    let compiled = compile_multiqubit_braid_with_limit(qubits, &operations, MAX_STEPS)
        .map_err(|e| e.to_string())?;
    let mut result = action_value(&compiled.action);
    result["steps"] = json!(compiled.steps);
    Ok(result)
}

fn wire_bilinear(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "a", "b", "mode"])?;
    let a = count(field(payload, "a")?, usize::MAX)?;
    let b = count(field(payload, "b")?, usize::MAX)?;
    let k = count(field(payload, "mode")?, usize::MAX)?;
    if k == 0 {
        return Err("Majorana mode index must be positive".into());
    }
    let term = MajoranaBilinear::new(a, b).map_err(|e| e.to_string())?;
    Ok(
        json!({"commutator":term.generator_on_mode(k).map(|(coefficient,mode)| json!([coefficient.to_string(),mode]))}),
    )
}

fn build_kitaev_wire(payload: &Value) -> Result<(usize, KitaevWire), String> {
    let sites = count(field(payload, "num_sites")?, 2048)?;
    let model = KitaevWire::new(
        sites,
        rational(field(payload, "t")?)?,
        rational(field(payload, "mu")?)?,
        rational(field(payload, "delta")?)?,
    )
    .map_err(|e| e.to_string())?;
    Ok((sites, model))
}

fn format_commutator(v: &std::collections::BTreeMap<usize, Exact>) -> Vec<Value> {
    v.iter()
        .map(|(k, q)| json!([k, to_canonical_string(q)]))
        .collect()
}

fn wire(payload: &Value) -> Result<Value, String> {
    if payload.get("operation").and_then(Value::as_str) == Some("bilinear") {
        return wire_bilinear(payload);
    }
    allowed(payload, &["num_sites", "t", "mu", "delta", "mode"])?;
    let (sites, model) = build_kitaev_wire(payload)?;
    let isolation = model.boundary_isolation().map_err(|e| e.to_string())?;
    let protected = isolation.left_isolated() && isolation.right_isolated();
    let diagnostics = json!({"num_sites":sites,"t":to_canonical_string(model.hopping()),
        "mu":to_canonical_string(model.chemical_potential()),"delta":to_canonical_string(model.pairing()),
        "is_sweet_spot":model.is_sweet_spot(),"boundary_modes":[isolation.boundary_modes.0,isolation.boundary_modes.1],
        "unpaired_modes":isolation.isolated_modes,"left_commutator_zero":isolation.left_isolated(),
        "right_commutator_zero":isolation.right_isolated(),
        "mzm_topologically_protected":protected,"authority_effect":"None"});
    let mut result = json!({"terms":model.terms().iter().map(|(term,q)|json!([term.mode_a(),term.mode_b(),to_canonical_string(q)])).collect::<Vec<_>>(),
        "constant_energy":to_canonical_string(model.constant_energy()),"is_sweet_spot":model.is_sweet_spot(),
        "boundary_modes":[isolation.boundary_modes.0,isolation.boundary_modes.1],"unpaired_modes":isolation.isolated_modes,
        "left_commutator":format_commutator(&isolation.left_generator),"right_commutator":format_commutator(&isolation.right_generator),"diagnostics":diagnostics});
    if let Some(mode) = payload.get("mode") {
        let values = model
            .generator_on_mode(count(mode, 4096)?)
            .map_err(|e| e.to_string())?;
        result["mode_commutator"] = json!(format_commutator(&values));
    }
    Ok(result)
}

fn noise_value(noise: &LocalMajoranaNoise) -> Value {
    json!({"dim":noise.dim(),"data":noise.rows().iter().map(|row|row.iter().map(to_canonical_string).collect::<Vec<_>>()).collect::<Vec<_>>()})
}

fn read_noise(value: &Value) -> Result<LocalMajoranaNoise, String> {
    allowed(value, &["dim", "data"])?;
    let dim = count(field(value, "dim")?, MAX_DIM)?;
    let matrix =
        native_matrix::parse_matrix(&json!({"rows":dim,"cols":dim,"data":field(value,"data")?}))?;
    let rows = (0..dim)
        .map(|r| {
            (0..dim)
                .map(|c| matrix.get_ref(r, c).cloned().map_err(|e| e.to_string()))
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?;
    LocalMajoranaNoise::from_rows(rows).map_err(|e| e.to_string())
}

fn read_noise_operator(
    value: &Value,
) -> Result<linear_algebra::backend::basic_matrix::BasicMatrix<Exact>, String> {
    allowed(value, &["dim", "data"])?;
    let dim = count(field(value, "dim")?, MAX_DIM)?;
    native_matrix::parse_matrix(&json!({"rows":dim,"cols":dim,"data":field(value,"data")?}))
}

fn parse_coupling_entry(v: &Value) -> Result<(usize, usize, Exact), String> {
    let row = list(v, 3)?;
    if row.len() != 3 {
        return Err("couplings must have three entries".to_string());
    }
    Ok((
        count(&row[0], MAX_DIM)?,
        count(&row[1], MAX_DIM)?,
        rational(&row[2])?,
    ))
}

fn noise_from_rows(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "dim", "data"])?;
    Ok(noise_value(&read_noise(
        &json!({"dim":field(payload,"dim")?,"data":field(payload,"data")?}),
    )?))
}

fn noise_zero(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "dim"])?;
    Ok(noise_value(
        &LocalMajoranaNoise::zero(count(field(payload, "dim")?, MAX_DIM)?)
            .map_err(|e| e.to_string())?,
    ))
}

fn noise_stray_couplings(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "dim", "couplings"])?;
    let dim = count(field(payload, "dim")?, MAX_DIM)?;
    let couplings = list(field(payload, "couplings")?, MAX_DIM * MAX_DIM)?
        .iter()
        .map(parse_coupling_entry)
        .collect::<Result<Vec<_>, String>>()?;
    Ok(noise_value(
        &LocalMajoranaNoise::stray_couplings(dim, &couplings).map_err(|e| e.to_string())?,
    ))
}

fn noise_transform(payload: &Value) -> Result<Value, String> {
    allowed(
        payload,
        &["operation", "noise", "matrix", "tolerance_epsilon"],
    )?;
    let noise = read_noise(field(payload, "noise")?)?;
    let matrix = read_noise_operator(field(payload, "matrix")?)?;
    Ok(noise_value(
        &noise
            .transform_matrix(&matrix, native_matrix::limits())
            .map_err(|e| e.to_string())?,
    ))
}

fn noise_evaluate(payload: &Value) -> Result<Value, String> {
    allowed(
        payload,
        &["operation", "noise", "matrix", "tolerance_epsilon"],
    )?;
    let noise = read_noise(field(payload, "noise")?)?;
    let matrix = read_noise_operator(field(payload, "matrix")?)?;
    let tolerance = rational(field(payload, "tolerance_epsilon")?)?;
    let result = evaluate_noise_matrix(&noise, &matrix, &tolerance, native_matrix::limits())
        .map_err(|e| e.to_string())?;
    Ok(
        json!({"max_noise_leakage":to_canonical_string(&result.max_noise_leakage),
        "circuit_noise_defect":to_canonical_string(&result.circuit_noise_defect),
        "tolerance_epsilon":to_canonical_string(&result.tolerance_epsilon),
        "is_accepted":result.is_accepted,"status_reason":result.status_reason()}),
    )
}

fn noise_leakage(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "noise", "mode"])?;
    let noise = read_noise(field(payload, "noise")?)?;
    let mut result = json!({"max_leakage":to_canonical_string(&noise.max_leakage())});
    if let Some(mode) = payload.get("mode") {
        let mode_leak = noise
            .leakage_on_mode(count(mode, MAX_DIM)?)
            .map_err(|e| e.to_string())?;
        result["leakage_on_mode"] = json!(to_canonical_string(&mode_leak));
    }
    Ok(result)
}

fn parse_correlated_grid(payload: &Value) -> Result<(usize, usize), String> {
    let q = count(field(payload, "num_qubits")?, MAX_DIM / 4)?;
    let lattice = count(field(payload, "lattice_l")?, 4096)?;
    Ok((q, lattice))
}

fn noise_correlated(payload: &Value) -> Result<Value, String> {
    allowed(
        payload,
        &["operation", "num_qubits", "lattice_l", "budget", "seed"],
    )?;
    let (q, lattice) = parse_correlated_grid(payload)?;
    let budget = rational(field(payload, "budget")?)?;
    let seed = integer(field(payload, "seed")?)?;
    let result =
        correlated_cluster_couplings(q, lattice, &budget, seed).map_err(|e| e.to_string())?;
    Ok(
        json!({"couplings":result.iter().map(|(a,b,q)|json!([a,b,to_canonical_string(q)])).collect::<Vec<_>>()}),
    )
}

fn noise(payload: &Value) -> Result<Value, String> {
    let operation = field(payload, "operation")?
        .as_str()
        .ok_or("operation must be a string")?;
    match operation {
        "from_rows" => noise_from_rows(payload),
        "zero" => noise_zero(payload),
        "stray_couplings" => noise_stray_couplings(payload),
        "transform" => noise_transform(payload),
        "evaluate" => noise_evaluate(payload),
        "leakage" => noise_leakage(payload),
        "correlated" => noise_correlated(payload),
        _ => Err(format!("unknown noise operation: {operation}")),
    }
}

fn generate_integer(
    generator: &mut DeterministicRationalNoiseGenerator,
    payload: &Value,
) -> Result<Value, String> {
    let min_val = integer(field(payload, "min_val")?)?;
    let max_val = integer(field(payload, "max_val")?)?;
    let val = generator
        .next_int_in_range(min_val, max_val)
        .map_err(|e| e.to_string())?;
    Ok(json!({"value": val}))
}

fn generate_fraction(
    generator: &mut DeterministicRationalNoiseGenerator,
    payload: &Value,
) -> Result<Value, String> {
    let scale = rational(field(payload, "scale_bound")?)?;
    let denominator = count(field(payload, "max_denom")?, u32::MAX as usize)? as u32;
    let frac = generator
        .next_fraction(denominator, &scale)
        .map_err(|e| e.to_string())?;
    Ok(json!({"value": to_canonical_string(&frac)}))
}

fn generate_matrix(
    generator: &mut DeterministicRationalNoiseGenerator,
    payload: &Value,
) -> Result<Value, String> {
    let dim = count(field(payload, "dim")?, MAX_DIM)?;
    let scale = rational(field(payload, "scale_bound")?)?;
    let density = rational(field(payload, "density")?)?;
    let denominator = count(field(payload, "max_denom")?, u32::MAX as usize)? as u32;
    let mat = generator
        .generate_skew_symmetric_matrix(dim, &scale, &density, denominator)
        .map_err(|e| e.to_string())?;
    Ok(json!({"matrix": noise_value(&mat)}))
}

fn dispatch_generator_op(
    operation: &str,
    generator: &mut DeterministicRationalNoiseGenerator,
    payload: &Value,
) -> Result<Value, String> {
    match operation {
        "integer" => generate_integer(generator, payload),
        "fraction" => generate_fraction(generator, payload),
        "matrix" => generate_matrix(generator, payload),
        _ => Err(format!("unknown generator operation: {operation}")),
    }
}

fn generate(payload: &Value) -> Result<Value, String> {
    allowed(
        payload,
        &[
            "operation",
            "state",
            "dim",
            "scale_bound",
            "density",
            "max_denom",
            "min_val",
            "max_val",
        ],
    )?;
    let state = count(field(payload, "state")?, u32::MAX as usize)? as u32;
    let mut generator = DeterministicRationalNoiseGenerator::new(state);
    let operation = field(payload, "operation")?
        .as_str()
        .ok_or("operation must be a string")?;
    let mut result = dispatch_generator_op(operation, &mut generator, payload)?;
    result["state"] = json!(generator.state());
    Ok(result)
}

/// Same 0/1 refusal as `native_matrix`'s private GF(2) entry parser.
/// That parser is not visible here and its dimension cap is 256.
fn gf2_entry(value: &Value) -> Result<u8, String> {
    match value.as_u64() {
        Some(0) => Ok(0),
        Some(1) => Ok(1),
        _ => Err("GF(2) entries must be the integers 0 or 1".into()),
    }
}

fn parse_gf2_row(index: usize, row: &Value, cols: usize) -> Result<Vec<u8>, String> {
    let entries = list(row, cols)?;
    if entries.len() != cols {
        return Err(format!(
            "matrix row {index} has {} entries, expected {cols}",
            entries.len()
        ));
    }
    entries.iter().map(gf2_entry).collect()
}

fn parse_gf2_dims(value: &Value) -> Result<(usize, usize), String> {
    let rows = count(field(value, "rows")?, GF2_DIAGNOSTIC_MAX_DIM)?;
    let cols = count(field(value, "cols")?, GF2_DIAGNOSTIC_MAX_DIM)?;
    if rows.saturating_mul(cols) > GF2_DIAGNOSTIC_MAX_ENTRIES {
        return Err(format!(
            "matrix has {} entries, above {GF2_DIAGNOSTIC_MAX_ENTRIES}",
            rows.saturating_mul(cols)
        ));
    }
    Ok((rows, cols))
}

fn gf2_matrix(value: &Value) -> Result<GF2Matrix, String> {
    allowed(value, &["rows", "cols", "data"])?;
    let (rows, cols) = parse_gf2_dims(value)?;
    let data = list(field(value, "data")?, rows)?;
    if data.len() != rows {
        return Err(format!("matrix has {} rows, expected {rows}", data.len()));
    }
    let bits = data
        .iter()
        .enumerate()
        .map(|(index, row)| parse_gf2_row(index, row, cols))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(GF2Matrix { rows, cols, data: bits })
}

fn gf2_vector(value: &Value) -> Result<Vec<u8>, String> {
    list(value, GF2_DIAGNOSTIC_MAX_DIM)?
        .iter()
        .map(gf2_entry)
        .collect()
}

fn matrix_value(matrix: &GF2Matrix) -> Value {
    json!({"rows": matrix.rows, "cols": matrix.cols, "data": matrix.data})
}

fn schedule_status(status: GF2ScheduleStatus) -> &'static str {
    match status {
        GF2ScheduleStatus::Exact => "Exact",
        GF2ScheduleStatus::ClosedResidual => "ClosedResidual",
        GF2ScheduleStatus::OpenObstruction => "OpenObstruction",
    }
}

fn parse_classify_matrices(payload: &Value) -> Result<(GF2Matrix, GF2Matrix), String> {
    let d0 = gf2_matrix(field(payload, "d0")?)?;
    let d1 = gf2_matrix(field(payload, "d1")?)?;
    Ok((d0, d1))
}

fn classify_diagnostic(payload: &Value) -> Result<Value, String> {
    allowed(
        payload,
        &["operation", "d0", "d1", "residual", "budget", "diagnostics"],
    )?;
    let (d0, d1) = parse_classify_matrices(payload)?;
    let residual = gf2_vector(field(payload, "residual")?)?;
    let budget = count(field(payload, "budget")?, GF2_DIAGNOSTIC_MAX_BUDGET)? as u64;
    let receipt: ClassifiedReceipt = if boolean(field(payload, "diagnostics")?)? {
        classify_with_diagnostics(&d0, &d1, &residual, budget)
    } else {
        classify(&d0, &d1, &residual, budget)
    };
    serde_json::to_value(receipt).map_err(|error| error.to_string())
}

fn parse_topology(value: &Value) -> Result<Topology, String> {
    match value.as_str() {
        Some("Disk") => Ok(Topology::Disk),
        Some("Cylinder") => Ok(Topology::Cylinder),
        Some("Torus") => Ok(Topology::Torus),
        _ => Err("topology must be Disk, Cylinder, or Torus".into()),
    }
}

fn topology_name(topology: Topology) -> &'static str {
    match topology {
        Topology::Disk => "Disk",
        Topology::Cylinder => "Cylinder",
        Topology::Torus => "Torus",
    }
}

fn tetron_diagnostic(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "rows", "cols", "topology"])?;
    let rows = count(field(payload, "rows")?, usize::MAX)?;
    let cols = count(field(payload, "cols")?, usize::MAX)?;
    if rows.saturating_mul(cols) > TETRON_MAX_CELLS {
        return Err(format!(
            "tetron array has {} cells, above {TETRON_MAX_CELLS}",
            rows.saturating_mul(cols)
        ));
    }
    let topology = parse_topology(field(payload, "topology")?)?;
    let (complex, report) = build_tetron_array(rows, cols, topology)?;
    let homology_matches_prediction = report.homology_matches_prediction();
    Ok(json!({
        "topology": topology_name(report.topology),
        "rows": report.rows,
        "cols": report.cols,
        "num_mzm": report.num_mzm,
        "num_channels": report.num_channels,
        "num_islands": report.num_islands,
        "euler_characteristic": report.euler_characteristic,
        "rank_d0": report.rank_d0,
        "rank_d1": report.rank_d1,
        "graph_b1": report.graph_b1,
        "dim_h1": report.dim_h1,
        "expected_dim_h1": report.expected_dim_h1,
        "horizontal": report.horizontal,
        "vertical": report.vertical,
        "authority_effect": report.authority_effect,
        "homology_matches_prediction": homology_matches_prediction,
        "d0": matrix_value(&complex.d0),
        "d1": matrix_value(&complex.d1),
    }))
}

fn lggr_diagnostic(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "d0", "d1", "omega"])?;
    let d0 = gf2_matrix(field(payload, "d0")?)?;
    let d1 = gf2_matrix(field(payload, "d1")?)?;
    let omega = gf2_vector(field(payload, "omega")?)?;
    let witness = detect_lggr(&d0, &d1, &omega)?;
    Ok(json!({
        "local_green": witness.local_green,
        "global_red": witness.global_red,
        "is_lggr": witness.is_lggr,
        "d1_omega": witness.d1_omega,
        "certificate": {"status": schedule_status(witness.certificate.status)},
        "authority_effect": "None",
    }))
}

fn parse_gf2_cycle(cycle: &Value) -> Result<Vec<u8>, String> {
    list(cycle, REPAIR_MAX_CYCLE_LEN)?
        .iter()
        .map(gf2_entry)
        .collect()
}

fn repair_by_distance(payload: &Value) -> Result<Value, String> {
    allowed(payload, &["operation", "distance"])?;
    let distance = count(field(payload, "distance")?, u32::MAX as usize)? as u32;
    let t = repair_capacity_from_distance(distance)?;
    Ok(json!({"t": t}))
}

fn repair_diagnostic(payload: &Value) -> Result<Value, String> {
    let object = payload.as_object().ok_or("payload must be an object")?;
    let has_distance = object.contains_key("distance");
    let has_cycles = object.contains_key("cycles");
    if has_distance == has_cycles {
        return Err("repair_capacity requires exactly one of distance or cycles".into());
    }
    if has_distance {
        return repair_by_distance(payload);
    }
    allowed(payload, &["operation", "cycles"])?;
    let cycles = list(field(payload, "cycles")?, REPAIR_MAX_CYCLES)?
        .iter()
        .map(parse_gf2_cycle)
        .collect::<Result<Vec<_>, _>>()?;
    Ok(json!({"min_weight": min_weight_nontrivial(&cycles)}))
}

fn gf2_diagnostic(payload: &Value) -> Result<Value, String> {
    let operation = field(payload, "operation")?
        .as_str()
        .ok_or("operation must be a string")?;
    match operation {
        "classify" => classify_diagnostic(payload),
        "tetron" => tetron_diagnostic(payload),
        "lggr" => lggr_diagnostic(payload),
        "repair_capacity" => repair_diagnostic(payload),
        _ => Err(format!("unknown gf2 diagnostic operation: {operation}")),
    }
}

fn dispatch_majorana(action: &str, payload: &Value) -> Option<Result<Value, String>> {
    match action {
        "majorana_braid_action" => Some(braid(payload)),
        "majorana_gf2_diagnostic" => Some(gf2_diagnostic(payload)),
        "majorana_multiqubit_braid" => Some(multiqubit(payload)),
        "majorana_kitaev_wire" => Some(wire(payload)),
        "majorana_noise" => Some(noise(payload)),
        "majorana_noise_generate" => Some(generate(payload)),
        _ => None,
    }
}

fn dispatch_action(action: &str, payload: &Value) -> Result<Value, String> {
    if let Some(res) = dispatch_majorana(action, payload) {
        return res;
    }
    match action {
        "math_rational_matrix" => native_matrix::rational(payload),
        "math_gf2_matrix" => native_matrix::gf2(payload),
        "homology_contraction" => native_homology::dispatch(payload, false),
        "homology_perturbation" => native_homology::dispatch(payload, true),
        name @ ("functional_projection_transfer"
        | "functional_family_bound"
        | "functional_family_member") => native_functional::dispatch(name, payload),
        _ => Err("unknown exact math action".into()),
    }
}

pub(super) fn dispatch(request: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    match dispatch_action(request.action.as_str(), &request.payload) {
        Ok(value) => outcome_ok(&request.action, value),
        Err(error) => outcome_err(&request.action, error),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/majorana_math.rs
// Claim: urn:core:crates_rs:pfp:majorana-math:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda28b79b1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda28b79b1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora28b79b1 {
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
impl BoundaryErrora28b79b1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora28b79b1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora28b79b1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda28b79b1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora28b79b1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora28b79b1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora28b79b1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora28b79b1::ExceedsCapacity {
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

    #[test]
    fn braid_wire_preserves_the_row_action_and_checks_inverse_types() {
        let result = braid(&json!({"num_modes":4,"steps":[[1,false]]})).unwrap();
        assert_eq!(result["images"], json!([[2, 1], [1, -1], [3, 1], [4, 1]]));
        assert_eq!(result["determinant"], 1);
        assert_eq!(result["matrix"]["data"][0], json!(["0", "1", "0", "0"]));
        assert!(braid(&json!({"num_modes":true,"steps":[]})).is_err());
        assert!(braid(&json!({"num_modes":4,"steps":[[1,1]]})).is_err());
        assert!(braid(&json!({"num_modes":257,"steps":[]})).is_err());
        assert!(braid(&json!({"num_modes":4,"steps":[],"extra":0})).is_err());
    }

    #[test]
    fn noise_wire_uses_exact_equality_at_the_acceptance_boundary() {
        let noise = json!({"dim":4,"data":[["0","0","1/3","0"],
            ["0","0","0","0"],["-1/3","0","0","0"],["0","0","0","0"]]});
        let matrix = json!({"dim":4,"data":[["0","1","0","0"],
            ["-1","0","0","0"],["0","0","1","0"],["0","0","0","1"]]});
        let request = json!({"operation":"evaluate","noise":noise,"matrix":matrix,
            "tolerance_epsilon":"1/3"});
        let accepted = super::noise(&request).unwrap();
        assert_eq!(accepted["is_accepted"], true);
        assert_eq!(accepted["circuit_noise_defect"], "1/3");
        assert_eq!(accepted["max_noise_leakage"], "2/3");
        let mut rejected = request;
        rejected["tolerance_epsilon"] = json!("1/4");
        assert_eq!(super::noise(&rejected).unwrap()["is_accepted"], false);
        rejected["noise"]["data"][0][0] = json!(0.0);
        assert!(super::noise(&rejected).is_err());
    }

    #[test]
    fn kitaev_wire_keeps_the_sparse_generator_and_positive_index_contract() {
        let result = wire(&json!({"num_sites":4,"t":"1","mu":"0","delta":"1","mode":1})).unwrap();
        assert_eq!(result["unpaired_modes"], json!([1, 8]));
        assert_eq!(result["mode_commutator"], json!([]));
        assert_eq!(result["diagnostics"]["left_commutator_zero"], true);
        assert_eq!(
            wire(&json!({"operation":"bilinear","a":1,"b":2,"mode":1})).unwrap()["commutator"],
            json!(["2", 2])
        );
        assert!(wire(&json!({"operation":"bilinear","a":1,"b":2,"mode":0})).is_err());
        assert!(wire(&json!({"num_sites":4,"t":1.0,"mu":"0","delta":"1"})).is_err());
    }

    #[test]
    fn seeded_generator_is_replayable_and_refuses_an_inexact_density() {
        let request = json!({"operation":"matrix","state":42,"dim":4,
            "scale_bound":"1/10","density":"1","max_denom":50});
        let first = generate(&request).unwrap();
        assert_eq!(first, generate(&request).unwrap());
        assert_ne!(first["state"], 42);
        assert_eq!(first["matrix"]["dim"], 4);
        let mut bad = request;
        bad["density"] = json!(true);
        assert!(generate(&bad).is_err());
    }

    #[test]
    fn registered_actions_return_the_standard_native_outcome() {
        let request = RuntimeRequestV1 {
            schema_version: super::super::RUNTIME_REQUEST_SCHEMA.into(),
            action: "majorana_braid_action".into(),
            payload: json!({"num_modes":2,"steps":[]}),
        };
        let result = super::super::dispatch_runtime_request(&request);
        assert!(result.success);
        assert_eq!(result.authority_effect, "None");
        assert_eq!(result.action, request.action);
    }

    fn gf2_json(matrix: &core_majorana::GF2Matrix) -> Value {
        json!({"rows": matrix.rows, "cols": matrix.cols, "data": matrix.data})
    }

    fn classify_payload(
        complex: &core_majorana::ChainComplexGf2,
        residual: &[u8],
        diagnostics: bool,
    ) -> Value {
        json!({
            "operation": "classify",
            "d0": gf2_json(&complex.d0),
            "d1": gf2_json(&complex.d1),
            "residual": residual,
            "budget": 64,
            "diagnostics": diagnostics,
        })
    }

    // mutation: publish OpenObstruction and a null certificate_alpha for an im(d0) residual
    #[test]
    fn majorana_gf2_diagnostic_classifies_exact_and_open_obstruction() {
        let complex = core_majorana::triangle();
        let exact = gf2_diagnostic(&classify_payload(
            &complex,
            &core_majorana::exact_syndrome_example(),
            false,
        ))
        .unwrap();
        assert_eq!(exact["terminal"], "Exact");
        assert_eq!(exact["authority_effect"], "None");
        assert_eq!(exact["certificate_alpha"], json!([0, 1, 0]));
        assert_eq!(exact["certificate_verified"], true);
        assert_eq!(exact["phi1_searched"], Value::Null);
        let diagnosed = gf2_diagnostic(&classify_payload(
            &complex,
            &core_majorana::exact_syndrome_example(),
            true,
        ))
        .unwrap();
        assert_eq!(diagnosed["terminal"], "Exact");
        assert!(diagnosed["phi1_searched"].as_u64().is_some());

        let open = gf2_diagnostic(&classify_payload(
            &complex,
            &core_majorana::open_syndrome_example(),
            false,
        ))
        .unwrap();
        assert_eq!(open["terminal"], "OpenObstruction");
        assert_eq!(open["coherence_witness"], json!([1]));
        assert_eq!(open["certificate_alpha"], Value::Null);
        assert_eq!(open["authority_effect"], "None");

        let request = RuntimeRequestV1 {
            schema_version: super::super::RUNTIME_REQUEST_SCHEMA.into(),
            action: "majorana_gf2_diagnostic".into(),
            payload: classify_payload(&complex, &core_majorana::exact_syndrome_example(), false),
        };
        let outcome = super::super::dispatch_runtime_request(&request);
        assert!(outcome.success, "{:?}", outcome.error);
        assert_eq!(outcome.authority_effect, "None");
        assert_eq!(outcome.result.unwrap()["certificate_alpha"], json!([0, 1, 0]));
    }

    // mutation: parse GF(2) entries with as_f64 truncation and JSON bools as 0/1
    #[test]
    fn majorana_gf2_diagnostic_refuses_float_entries_and_bool_integers() {
        let complex = core_majorana::triangle();
        let mut floated = classify_payload(&complex, &core_majorana::exact_syndrome_example(), false);
        floated["d0"]["data"][0][0] = json!(1.0);
        assert!(gf2_diagnostic(&floated).is_err());
        let mut boolean = classify_payload(&complex, &core_majorana::exact_syndrome_example(), false);
        boolean["budget"] = json!(true);
        assert!(gf2_diagnostic(&boolean).is_err());
        boolean = classify_payload(&complex, &core_majorana::exact_syndrome_example(), false);
        boolean["residual"][0] = json!(false);
        assert!(gf2_diagnostic(&boolean).is_err());
        let mut unknown = classify_payload(&complex, &core_majorana::exact_syndrome_example(), false);
        unknown["note"] = json!(1);
        assert!(gf2_diagnostic(&unknown).is_err());
        let mut over_budget = classify_payload(&complex, &[1, 1, 0], false);
        over_budget["budget"] = json!(1_000_001);
        assert!(gf2_diagnostic(&over_budget).is_err());
    }

    // mutation: serialize dim_h1 as 0 and accept a periodic column extent of 1
    #[test]
    fn majorana_gf2_diagnostic_tetron_reports_measured_dim_h1() {
        let disk = gf2_diagnostic(&json!({
            "operation": "tetron", "rows": 1, "cols": 1, "topology": "Disk"
        }))
        .unwrap();
        assert_eq!(disk["dim_h1"], 0);
        assert_eq!(disk["expected_dim_h1"], 0);
        assert_eq!(disk["homology_matches_prediction"], true);
        assert_eq!(disk["authority_effect"], "None");
        assert_eq!(disk["rank_d0"], 3);
        assert_eq!(
            disk["d0"],
            json!({"rows": 4, "cols": 4, "data": [
                [1, 1, 0, 0],
                [0, 0, 1, 1],
                [1, 0, 1, 0],
                [0, 1, 0, 1]
            ]})
        );

        let torus = gf2_diagnostic(&json!({
            "operation": "tetron", "rows": 2, "cols": 2, "topology": "Torus"
        }))
        .unwrap();
        assert_eq!(torus["dim_h1"], 2);
        assert_eq!(torus["num_channels"], 8);
        assert_eq!(torus["num_mzm"], 4);
        assert_eq!(torus["rank_d0"], 3);
        assert_eq!(torus["rank_d1"], 3);
        assert_eq!(torus["homology_matches_prediction"], true);
        assert_eq!(torus["d0"]["data"][0], json!([1, 1, 0, 0]));

        let cylinder = gf2_diagnostic(&json!({
            "operation": "tetron", "rows": 2, "cols": 1, "topology": "Cylinder"
        }));
        let error = cylinder.unwrap_err();
        assert!(
            error.contains("cols must be >= 2"),
            "crate periodic-extent error, got {error}"
        );
        let cells = gf2_diagnostic(&json!({
            "operation": "tetron", "rows": 65, "cols": 1, "topology": "Disk"
        }))
        .unwrap_err();
        assert!(
            cells.contains("tetron array has 65 cells"),
            "cell cap, got {cells}"
        );
    }

    // mutation: keep GF2_DIAGNOSTIC_MAX_DIM at 64, which refuses this torus
    #[test]
    fn majorana_gf2_diagnostic_admits_six_by_six_torus_and_refuses_past_the_ceiling() {
        let built = gf2_diagnostic(&json!({
            "operation": "tetron", "rows": 6, "cols": 6, "topology": "Torus"
        }))
        .unwrap();
        assert_eq!(built["num_channels"], 72);
        assert_eq!(built["num_mzm"], 36);
        assert_eq!(built["dim_h1"], 2);
        assert_eq!(built["d0"]["rows"], 72);
        assert_eq!(built["d0"]["cols"], 36);
        let mut residual = vec![0u8; 72];
        residual[0] = 1;
        let classified = gf2_diagnostic(&json!({
            "operation": "classify",
            "d0": built["d0"],
            "d1": built["d1"],
            "residual": residual,
            "budget": 64,
            "diagnostics": false,
        }))
        .unwrap();
        assert_eq!(classified["terminal"], "OpenObstruction");
        assert_eq!(classified["dim_h1"], 2);
        assert_eq!(classified["certificate_alpha"], Value::Null);
        assert_eq!(classified["phi1_searched"], Value::Null);
        assert_eq!(classified["authority_effect"], "None");
        let witness = classified["coherence_witness"].as_array().unwrap();
        assert!(witness.iter().any(|bit| bit.as_u64() == Some(1)));

        let over_dim = gf2_diagnostic(&json!({
            "operation": "classify",
            "d0": {"rows": 257, "cols": 1, "data": []},
            "d1": {"rows": 1, "cols": 1, "data": [[0]]},
            "residual": [0],
            "budget": 1,
            "diagnostics": false,
        }))
        .unwrap_err();
        assert!(
            over_dim.contains("dimension or count 257 exceeds limit 256"),
            "{over_dim}"
        );
        let over_entries = gf2_diagnostic(&json!({
            "operation": "classify",
            "d0": {"rows": 80, "cols": 52, "data": []},
            "d1": {"rows": 1, "cols": 1, "data": [[0]]},
            "residual": [0],
            "budget": 1,
            "diagnostics": false,
        }))
        .unwrap_err();
        assert!(
            over_entries.contains("matrix has 4160 entries, above 4096"),
            "{over_entries}"
        );
    }

    // mutation: set is_lggr from local_green alone
    #[test]
    fn majorana_gf2_diagnostic_lggr_separates_logical_x_from_exact() {
        let complex = core_majorana::surface_grid_2x2_torus();
        let logical = gf2_diagnostic(&json!({
            "operation": "lggr",
            "d0": gf2_json(&complex.d0),
            "d1": gf2_json(&complex.d1),
            "omega": core_majorana::torus_logical_x_example(),
        }))
        .unwrap();
        assert_eq!(logical["is_lggr"], true);
        assert_eq!(logical["local_green"], true);
        assert_eq!(logical["global_red"], true);
        assert_eq!(logical["d1_omega"], json!([0, 0, 0, 0]));
        assert_eq!(logical["certificate"]["status"], "ClosedResidual");
        assert_eq!(logical["authority_effect"], "None");

        let exact_syndrome = core_majorana::surface_exact_from_vertex0(&complex.d0);
        let exact = gf2_diagnostic(&json!({
            "operation": "lggr",
            "d0": gf2_json(&complex.d0),
            "d1": gf2_json(&complex.d1),
            "omega": exact_syndrome,
        }))
        .unwrap();
        assert_eq!(exact["is_lggr"], false);
        assert_eq!(exact["local_green"], true);
        assert_eq!(exact["certificate"]["status"], "Exact");
    }

    // mutation: return {"t": 0} for distance 0 instead of the crate error
    #[test]
    fn majorana_gf2_diagnostic_repair_capacity_uses_the_crate_radius() {
        assert_eq!(
            gf2_diagnostic(&json!({"operation": "repair_capacity", "distance": 5})).unwrap(),
            json!({"t": 2})
        );
        let refused = gf2_diagnostic(&json!({"operation": "repair_capacity", "distance": 0}));
        let error = refused.unwrap_err();
        assert!(
            error.contains("must be positive"),
            "crate distance refusal, got {error}"
        );
        assert_eq!(
            gf2_diagnostic(&json!({
                "operation": "repair_capacity",
                "cycles": [[0, 0], [1, 0, 1], [1]]
            }))
            .unwrap(),
            json!({"min_weight": 1})
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_a28b79b1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda28b79b1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda28b79b1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda28b79b1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda28b79b1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda28b79b1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora28b79b1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora28b79b1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
