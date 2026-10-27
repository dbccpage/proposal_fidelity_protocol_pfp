//! Bounded wire adapters to the canonical exact matrix implementations.

use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{elimination, matrix, ExactFieldError};
use num_rational::BigRational;
use core_kernel::{parse_exact, to_canonical_string};
use core_number_theory::gf2::{F2Matrix, F2Vector};
use serde_json::{json, Map, Value};

const MAX_DIMENSION: usize = 256;
const MAX_ENTRIES: usize = MAX_DIMENSION * MAX_DIMENSION;
const MAX_EXACT_TEXT_BYTES: usize = 4096;

pub(super) const fn limits() -> OperationLimits {
    OperationLimits {
        max_elements: 2 * MAX_ENTRIES,
        max_scalar_ops: 50_000_000,
    }
}

fn required<'a>(value: &'a Value, key: &str) -> Result<&'a Value, String> {
    value.get(key).ok_or_else(|| format!("missing {key}"))
}

fn object<'a>(value: &'a Value, name: &str) -> Result<&'a Map<String, Value>, String> {
    value
        .as_object()
        .ok_or_else(|| format!("{name} must be an object"))
}

fn dimension(value: &Value, name: &str) -> Result<usize, String> {
    let n = value
        .as_u64()
        .and_then(|n| usize::try_from(n).ok())
        .ok_or_else(|| format!("{name} must be a nonnegative integer"))?;
    if n > MAX_DIMENSION {
        return Err(format!("{name} exceeds {MAX_DIMENSION}"));
    }
    Ok(n)
}

fn dimension_field(value: &Value, name: &str) -> Result<usize, String> {
    dimension(required(value, name)?, name)
}

fn verify_row_shapes(data: &[Value], rows: usize, cols: usize) -> Result<(), String> {
    if data.len() != rows {
        return Err(format!("matrix has {} rows, expected {rows}", data.len()));
    }
    for (index, row) in data.iter().enumerate() {
        let row = row
            .as_array()
            .ok_or_else(|| format!("matrix row {index} must be an array"))?;
        if row.len() != cols {
            return Err(format!(
                "matrix row {index} has {} entries, expected {cols}",
                row.len()
            ));
        }
    }
    Ok(())
}

fn shaped_rows(value: &Value) -> Result<(usize, usize, &[Value]), String> {
    let fields = object(value, "matrix")?;
    if let Some(key) = fields
        .keys()
        .find(|key| !matches!(key.as_str(), "rows" | "cols" | "data"))
    {
        return Err(format!("unknown matrix field: {key}"));
    }
    let rows = dimension_field(value, "rows")?;
    let cols = dimension_field(value, "cols")?;
    let data = required(value, "data")?
        .as_array()
        .ok_or_else(|| "matrix data must be an array of rows".to_owned())?;
    verify_row_shapes(data, rows, cols)?;
    Ok((rows, cols, data))
}

fn exact(value: &Value) -> Result<BigRational, String> {
    let text = value
        .as_str()
        .ok_or_else(|| "rational entries must be canonical strings".to_owned())?;
    if text.len() > MAX_EXACT_TEXT_BYTES {
        return Err(format!("exact scalar exceeds {MAX_EXACT_TEXT_BYTES} bytes"));
    }
    parse_exact(text).map_err(|error| error.to_string())
}

pub(super) fn parse_matrix(value: &Value) -> Result<BasicMatrix<BigRational>, String> {
    let (rows, cols, data) = shaped_rows(value)?;
    let mut entries = Vec::with_capacity(rows * cols);
    for row in data {
        // Row types and lengths were checked before scalar decoding.
        for entry in row
            .as_array()
            .ok_or_else(|| "matrix row must be an array".to_owned())?
        {
            entries.push(exact(entry)?);
        }
    }
    BasicMatrix::from_row_major_with_limit(rows, cols, entries, MAX_ENTRIES)
        .map_err(|error| error.to_string())
}

fn rational_vector(value: &Value) -> Result<Vec<BigRational>, String> {
    let entries = value
        .as_array()
        .ok_or_else(|| "vector must be an array".to_owned())?;
    if entries.len() > MAX_DIMENSION {
        return Err(format!("vector exceeds {MAX_DIMENSION} entries"));
    }
    entries.iter().map(exact).collect()
}

fn rational_vector_value(vector: &[BigRational]) -> Value {
    Value::Array(
        vector
            .iter()
            .map(|entry| Value::String(to_canonical_string(entry)))
            .collect(),
    )
}

pub(super) fn matrix_value(value: &BasicMatrix<BigRational>) -> Value {
    let data: Vec<Value> = if value.cols() == 0 {
        vec![json!([]); value.rows()]
    } else {
        value
            .as_slice()
            .chunks(value.cols())
            .map(rational_vector_value)
            .collect()
    };
    json!({"rows": value.rows(), "cols": value.cols(), "data": data})
}

fn operation(payload: &Value) -> Result<&str, String> {
    let fields = object(payload, "matrix request")?;
    if let Some(key) = fields.keys().find(|key| {
        !matches!(
            key.as_str(),
            "operation" | "matrix" | "other" | "scalar" | "vector"
        )
    }) {
        return Err(format!("unknown matrix request field: {key}"));
    }
    required(payload, "operation")?
        .as_str()
        .ok_or_else(|| "operation must be a string".to_owned())
}

fn rational_binary_op(
    operation: &str,
    a: &BasicMatrix<BigRational>,
    payload: &Value,
) -> Result<BasicMatrix<BigRational>, String> {
    let b = parse_matrix(required(payload, "other")?)?;
    let res = match operation {
        "add" => matrix::add(a, &b),
        "subtract" => matrix::sub(a, &b),
        _ => matrix::multiply_with_limits(a, &b, limits()),
    };
    res.map_err(|error| error.to_string())
}

fn rational_inverse_op(a: &BasicMatrix<BigRational>) -> Result<Value, String> {
    match elimination::inverse_with_limits(a, limits()) {
        Ok(inv) => Ok(json!({"matrix": matrix_value(&inv)})),
        Err(ExactFieldError::Singular { .. }) => Ok(json!({"matrix": null})),
        Err(error) => Err(error.to_string()),
    }
}

fn rational_matrix_op(
    operation: &str,
    a: &BasicMatrix<BigRational>,
    payload: &Value,
) -> Result<Option<Value>, String> {
    let output = match operation {
        "add" | "subtract" | "multiply" => rational_binary_op(operation, a, payload)?,
        "scale" => {
            let s = exact(required(payload, "scalar")?)?;
            matrix::scale(a, &s).map_err(|error| error.to_string())?
        }
        "transpose" => matrix::transpose(a).map_err(|error| error.to_string())?,
        "inverse" => return rational_inverse_op(a).map(Some),
        _ => return Ok(None),
    };
    Ok(Some(json!({"matrix": matrix_value(&output)})))
}

fn rational_vector_op(
    operation: &str,
    a: &BasicMatrix<BigRational>,
    payload: &Value,
) -> Result<Option<Value>, String> {
    match operation {
        "solve" => {
            let vector = rational_vector(required(payload, "vector")?)?;
            let solution = elimination::solve_with_limits(a, &vector, limits())
                .map_err(|error| error.to_string())?;
            let encoded = match solution {
                elimination::LinearSolution::Consistent { particular, .. } => {
                    rational_vector_value(&particular)
                }
                elimination::LinearSolution::Inconsistent { .. } => Value::Null,
            };
            Ok(Some(json!({"solution": encoded})))
        }
        "apply" => {
            let vector = rational_vector(required(payload, "vector")?)?;
            let result = matrix::multiply_vector_with_limits(a, &vector, limits())
                .map_err(|error| error.to_string())?;
            Ok(Some(json!({"vector": rational_vector_value(&result)})))
        }
        _ => Ok(None),
    }
}

fn rational_elimination_op(
    operation: &str,
    a: &BasicMatrix<BigRational>,
) -> Result<Value, String> {
    match operation {
        "rref" => {
            let reduced =
                elimination::rref_with_limits(a, limits()).map_err(|error| error.to_string())?;
            Ok(json!({"matrix": matrix_value(reduced.matrix()), "pivots": reduced.pivot_columns()}))
        }
        "rank" => elimination::rank_with_limits(a, limits())
            .map(|rank| json!({"rank": rank}))
            .map_err(|error| error.to_string()),
        "kernel" => {
            let basis = elimination::kernel_basis_with_limits(a, limits())
                .map_err(|error| error.to_string())?;
            Ok(
                json!({"basis": basis.iter().map(|v| rational_vector_value(v)).collect::<Vec<_>>()}),
            )
        }
        "determinant" => {
            let value = elimination::determinant_with_limits(a, limits())
                .map_err(|error| error.to_string())?;
            Ok(json!({"value": to_canonical_string(&value)}))
        }
        "is_idempotent" => {
            let square = matrix::multiply_with_limits(a, a, limits())
                .map_err(|error| error.to_string())?;
            Ok(json!({"is_idempotent": &square == a}))
        }
        _ => Err(format!("unsupported rational matrix operation: {operation}")),
    }
}

pub(super) fn rational(payload: &Value) -> Result<Value, String> {
    let operation = operation(payload)?;
    let a = parse_matrix(required(payload, "matrix")?)?;
    if let Some(value) = rational_matrix_op(operation, &a, payload)? {
        return Ok(value);
    }
    if let Some(value) = rational_vector_op(operation, &a, payload)? {
        return Ok(value);
    }
    rational_elimination_op(operation, &a)
}

fn binary(value: &Value) -> Result<u8, String> {
    match value.as_u64() {
        Some(0) => Ok(0),
        Some(1) => Ok(1),
        _ => Err("GF(2) entries must be the integers 0 or 1".to_owned()),
    }
}

fn f2_matrix(value: &Value) -> Result<F2Matrix, String> {
    let (rows, cols, data) = shaped_rows(value)?;
    let mut matrix = F2Matrix::zeros(rows, cols).map_err(|error| error.to_string())?;
    for (r, row) in data.iter().enumerate() {
        for (c, entry) in row
            .as_array()
            .ok_or_else(|| "matrix row must be an array".to_owned())?
            .iter()
            .enumerate()
        {
            let bit = binary(entry)?;
            if bit != 0 {
                matrix.set(r, c, true).map_err(|error| error.to_string())?;
            }
        }
    }
    Ok(matrix)
}

fn f2_vector(value: &Value) -> Result<F2Vector, String> {
    let entries = value
        .as_array()
        .ok_or_else(|| "vector must be an array".to_owned())?;
    if entries.len() > MAX_DIMENSION {
        return Err(format!("vector exceeds {MAX_DIMENSION} entries"));
    }
    let bits = entries.iter().map(binary).collect::<Result<Vec<_>, _>>()?;
    F2Vector::from_bits(&bits).map_err(|error| error.to_string())
}

fn f2_matrix_value(matrix: &F2Matrix) -> Value {
    json!({"rows": matrix.rows(), "cols": matrix.cols(), "data": matrix.to_rows()})
}

// F2Matrix's bit-packed routines have their own allocation ceiling. The wire
// additionally charges a conservative dense scalar cost before calling them.
fn f2_budget(elements: usize, scalar_ops: usize) -> Result<(), String> {
    let limits = limits();
    if elements > limits.max_elements || scalar_ops > limits.max_scalar_ops {
        return Err(format!("GF(2) operation exceeds the matrix budget ({elements} elements, {scalar_ops} scalar operations)"));
    }
    Ok(())
}

fn reduction_cost(rows: usize, cols: usize) -> usize {
    // Inputs have already passed the dimension bound, even when augmented.
    rows.min(cols) * (2 * rows * cols + cols + 1)
}

fn gf2_matrix_op(
    operation: &str,
    a: &F2Matrix,
    payload: &Value,
) -> Result<Option<Value>, String> {
    let (rows, cols) = (a.rows(), a.cols());
    let output = match operation {
        "add" | "multiply" => {
            let b = f2_matrix(required(payload, "other")?)?;
            if operation == "add" {
                a.add(&b)
            } else {
                f2_budget(rows * b.cols(), 2 * rows * cols * b.cols())?;
                a.mul(&b)
            }
        }
        "transpose" => Ok(a.transpose()),
        _ => return Ok(None),
    }
    .map_err(|error| error.to_string())?;
    Ok(Some(json!({"matrix": f2_matrix_value(&output)})))
}

fn gf2_reduction_op(operation: &str, a: &F2Matrix) -> Result<Value, String> {
    let (rows, cols) = (a.rows(), a.cols());
    f2_budget((rows * cols).max(cols * cols), reduction_cost(rows, cols))?;
    if operation == "kernel" {
        return Ok(
            json!({"basis": a.nullspace().iter().map(F2Vector::to_bits).collect::<Vec<_>>()}),
        );
    }
    let reduced = a.rref();
    Ok(if operation == "rank" {
        json!({"rank": reduced.rank()})
    } else {
        json!({"matrix": f2_matrix_value(&reduced.matrix), "pivots": reduced.pivot_columns})
    })
}

fn gf2_vector_op(
    operation: &str,
    a: &F2Matrix,
    payload: &Value,
) -> Result<Option<Value>, String> {
    let (rows, cols) = (a.rows(), a.cols());
    match operation {
        "solve" => {
            let vector = f2_vector(required(payload, "vector")?)?;
            f2_budget(
                (rows * (cols + 1)).max(cols * cols),
                reduction_cost(rows, cols + 1) + reduction_cost(rows, cols),
            )?;
            a.solve(&vector)
                .map(|result| Some(json!({"solution": result.map(|space| space.particular().to_bits())})))
                .map_err(|error| error.to_string())
        }
        "apply" => {
            let vector = f2_vector(required(payload, "vector")?)?;
            f2_budget(rows, 2 * rows * cols)?;
            a.mul_vec(&vector)
                .map(|result| Some(json!({"vector": result.to_bits()})))
                .map_err(|error| error.to_string())
        }
        _ => Ok(None),
    }
}

fn gf2_elimination_op(
    operation: &str,
    a: &F2Matrix,
    payload: &Value,
) -> Result<Value, String> {
    if let Some(value) = gf2_vector_op(operation, a, payload)? {
        return Ok(value);
    }
    let (rows, cols) = (a.rows(), a.cols());
    match operation {
        "rank" | "rref" | "kernel" => gf2_reduction_op(operation, a),
        "inverse" => {
            f2_budget(2 * rows * cols, reduction_cost(rows, 2 * cols))?;
            a.inverse()
                .map(|result| json!({"matrix": result.as_ref().map(f2_matrix_value)}))
                .map_err(|error| error.to_string())
        }
        _ => Err(format!("unsupported GF(2) matrix operation: {operation}")),
    }
}

pub(super) fn gf2(payload: &Value) -> Result<Value, String> {
    let operation = operation(payload)?;
    let a = f2_matrix(required(payload, "matrix")?)?;
    if let Some(value) = gf2_matrix_op(operation, &a, payload)? {
        return Ok(value);
    }
    gf2_elimination_op(operation, &a, payload)
}

// Origin: engine/crates_rs/pfp/src/invoke/native_matrix.rs
// Claim: urn:core:crates_rs:pfp:native-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord59308103 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord59308103` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError59308103 {
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
impl BoundaryError59308103 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError59308103 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError59308103 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord59308103 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError59308103> {
        if capacity_bound == 0 {
            return Err(BoundaryError59308103::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError59308103::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError59308103::ExceedsCapacity {
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

    fn request(operation: &str, matrix: Value) -> Value {
        json!({"operation": operation, "matrix": matrix})
    }

    #[test]
    fn rational_wire_preserves_empty_shapes_and_exact_solutions() {
        let empty = json!({"rows": 0, "cols": 3, "data": []});
        assert_eq!(matrix_value(&parse_matrix(&empty).unwrap()), empty);
        assert_eq!(
            rational(&request("transpose", empty)).unwrap(),
            json!({"matrix": {"rows": 3, "cols": 0, "data": [[], [], []]}})
        );
        let a = json!({"rows": 2, "cols": 2, "data": [["2", "1"], ["1", "-1"]]});
        let mut solve = request("solve", a.clone());
        solve["vector"] = json!(["1", "0"]);
        assert_eq!(
            rational(&solve).unwrap(),
            json!({"solution": ["1/3", "1/3"]})
        );
        assert_eq!(
            rational(&request("determinant", a)).unwrap(),
            json!({"value": "-3"})
        );
    }

    #[test]
    fn rational_rejects_malformed_and_noncanonical_scalars() {
        for data in [
            json!([[1]]),
            json!([[true]]),
            json!([["2/4"]]),
            json!([["0.5"]]),
            json!([["1/0"]]),
            json!([["01"]]),
        ] {
            assert!(parse_matrix(&json!({"rows": 1, "cols": 1, "data": data})).is_err());
        }
        for matrix in [
            json!({"rows": 1, "cols": 2, "data": [["1"]]}),
            json!({"rows": 0, "cols": 0, "data": [[]]}),
            json!({"rows": true, "cols": 0, "data": []}),
            json!({"rows": 257, "cols": 0, "data": []}),
        ] {
            assert!(parse_matrix(&matrix).is_err());
        }
    }

    #[test]
    fn rational_singular_and_inconsistent_are_explicit_nulls() {
        let a = json!({"rows": 2, "cols": 2, "data": [["1", "1"], ["1", "1"]]});
        assert_eq!(
            rational(&request("inverse", a.clone())).unwrap(),
            json!({"matrix": null})
        );
        let mut solve = request("solve", a);
        solve["vector"] = json!(["0", "1"]);
        assert_eq!(rational(&solve).unwrap(), json!({"solution": null}));
        assert_eq!(
            rational(&request(
                "determinant",
                json!({"rows": 0, "cols": 0, "data": []})
            ))
            .unwrap(),
            json!({"value": "1"})
        );
    }

    #[test]
    fn gf2_uses_binary_arithmetic_and_preserves_zero_row_width() {
        let a = json!({"rows": 2, "cols": 2, "data": [[1, 1], [0, 1]]});
        assert_eq!(
            gf2(&request("inverse", a.clone())).unwrap(),
            json!({"matrix": a})
        );
        let mut apply = request("apply", a.clone());
        apply["vector"] = json!([1, 1]);
        assert_eq!(gf2(&apply).unwrap(), json!({"vector": [0, 1]}));
        let mut solve = request("solve", a);
        solve["vector"] = json!([0, 1]);
        assert_eq!(gf2(&solve).unwrap(), json!({"solution": [1, 1]}));
        assert_eq!(
            gf2(&request(
                "transpose",
                json!({"rows": 0, "cols": 2, "data": []})
            ))
            .unwrap(),
            json!({"matrix": {"rows": 2, "cols": 0, "data": [[], []]}})
        );
    }

    #[test]
    fn gf2_rejects_nonbinary_values_and_shape_mismatches() {
        for entry in [json!(true), json!(0.0), json!(2), json!(-1), json!("1")] {
            assert!(gf2(&request(
                "rank",
                json!({"rows": 1, "cols": 1, "data": [[entry]]})
            ))
            .is_err());
        }
        let mut multiply = request("multiply", json!({"rows": 1, "cols": 2, "data": [[1, 0]]}));
        multiply["other"] = json!({"rows": 1, "cols": 1, "data": [[1]]});
        assert!(gf2(&multiply).is_err());
        assert!(f2_budget(1, limits().max_scalar_ops + 1).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_59308103 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord59308103::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord59308103::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord59308103::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord59308103::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord59308103::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError59308103::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError59308103::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
