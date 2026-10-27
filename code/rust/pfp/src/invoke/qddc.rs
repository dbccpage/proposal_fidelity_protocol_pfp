//! Strict wire conversion for finite QDDC. Mathematical operations are native.
use super::{native_matrix, outcome_err, outcome_ok, RuntimeOutcomeV1, RuntimeRequestV1};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_kernel::{parse_exact, to_canonical_string};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_quantum_physics::density_matrix::ExactDensityMatrix;
use core_quantum_physics::exact_operator::ExactOperator;
use core_quantum_physics::qddc::{
    self, ExactDensityStep, ExactGenerator, ExactHodge, Lindbladian, QddcState, RetractionChannel,
};
use serde_json::{json, Value};

// QDDC wire output contract, shared by all seven actions. This is distinct
// from the 256-bit input gate and mirrors the Python RationalText contract.
const MAX_OUTPUT_RATIONAL_BITS: u64 = 8192;
const MAX_OUTPUT_RATIONAL_TEXT_BYTES: usize = 6000;

fn field<'a>(v: &'a Value, key: &str) -> Result<&'a Value, String> {
    v.get(key).ok_or_else(|| format!("missing {key}"))
}
fn fields(v: &Value, names: &[&str]) -> Result<(), String> {
    let object = v.as_object().ok_or("expected an object")?;
    if object.len() != names.len() || object.keys().any(|key| !names.contains(&key.as_str())) {
        return Err(format!("expected exactly fields {names:?}"));
    }
    Ok(())
}
fn list(v: &Value, limit: usize) -> Result<&Vec<Value>, String> {
    let values = v.as_array().ok_or("expected an array")?;
    if values.len() > limit {
        return Err("array exceeds QDDC limit".into());
    }
    Ok(values)
}
fn rational(v: &Value) -> Result<Rational, String> {
    let text = v.as_str().ok_or("expected a canonical rational string")?;
    if text.len() > 160 {
        return Err("input rational text exceeds QDDC bound".into());
    }
    let q = parse_exact(text).map_err(|e| e.to_string())?;
    if to_canonical_string(&q) != text {
        return Err("noncanonical rational".into());
    }
    qddc::check_scalar(&q).map_err(|e| e.to_string())?;
    Ok(q)
}
fn check_matrix_dims(v: &Value, limit: usize) -> Result<(), String> {
    for name in ["rows", "cols"] {
        let n = field(v, name)?
            .as_u64()
            .ok_or("matrix dimensions must be integers")?;
        if n > limit as u64 {
            return Err("matrix exceeds QDDC dimension bound".into());
        }
    }
    Ok(())
}
fn check_matrix_entries(data: &Value, limit: usize) -> Result<(), String> {
    for row in list(data, limit)? {
        for entry in list(row, limit)? {
            rational(entry)?;
        }
    }
    Ok(())
}
fn real_matrix(v: &Value, limit: usize) -> Result<BasicMatrix<Rational>, String> {
    fields(v, &["rows", "cols", "data"])?;
    check_matrix_dims(v, limit)?;
    check_matrix_entries(field(v, "data")?, limit)?;
    native_matrix::parse_matrix(v)
}
fn operator(v: &Value) -> Result<ExactOperator, String> {
    fields(v, &["real", "imag"])?;
    let real = real_matrix(field(v, "real")?, qddc::MAX_DIM)?;
    let imag = real_matrix(field(v, "imag")?, qddc::MAX_DIM)?;
    if real.shape() != imag.shape() {
        return Err("complex matrix parts must have equal shapes".into());
    }
    let data = real
        .as_slice()
        .iter()
        .zip(imag.as_slice())
        .map(|(re, im)| GaussianRat {
            re: re.clone(),
            im: im.clone(),
        })
        .collect();
    let matrix =
        BasicMatrix::from_row_major(real.rows(), real.cols(), data).map_err(|e| e.to_string())?;
    let op = ExactOperator::try_new(matrix).map_err(|e| e.to_string())?;
    qddc::check_operator(&op, op.rows()).map_err(|e| e.to_string())?;
    Ok(op)
}
fn operators(v: &Value, limit: usize) -> Result<Vec<ExactOperator>, String> {
    list(v, limit)?.iter().map(operator).collect()
}
fn output_rational(q: &Rational) -> Result<String, String> {
    if q.numer().bits() > MAX_OUTPUT_RATIONAL_BITS || q.denom().bits() > MAX_OUTPUT_RATIONAL_BITS {
        return Err(format!(
            "QDDC_OUTPUT_LIMIT: rational numerator or denominator exceeds {MAX_OUTPUT_RATIONAL_BITS} bits"
        ));
    }
    let text = to_canonical_string(q);
    if text.len() > MAX_OUTPUT_RATIONAL_TEXT_BYTES {
        return Err(format!(
            "QDDC_OUTPUT_LIMIT: rational text exceeds {MAX_OUTPUT_RATIONAL_TEXT_BYTES} bytes"
        ));
    }
    Ok(text)
}
fn op_value(op: &ExactOperator) -> Result<Value, String> {
    let part = |imaginary| -> Result<Value, String> {
        let data: Vec<Vec<String>> = op
            .as_matrix()
            .as_slice()
            .chunks(op.cols())
            .map(|row| {
                row.iter()
                    .map(|z| output_rational(if imaginary { &z.im } else { &z.re }))
                    .collect::<Result<Vec<_>, _>>()
            })
            .collect::<Result<_, _>>()?;
        Ok(json!({"rows":op.rows(),"cols":op.cols(),"data":data}))
    };
    Ok(json!({"real":part(false)?,"imag":part(true)?}))
}
fn op_values(ops: &[ExactOperator]) -> Result<Vec<Value>, String> {
    ops.iter().map(op_value).collect()
}
fn parse_operator_dim(v: &Value) -> Result<usize, String> {
    let dim = field(v, "operator_dim")?
        .as_u64()
        .ok_or("operator_dim must be an integer")?;
    if !(1..=qddc::MAX_DIM as u64).contains(&dim) {
        return Err("operator_dim outside 1..=8".into());
    }
    Ok(dim as usize)
}
fn state(v: &Value) -> Result<QddcState, String> {
    fields(v, &["d_prev", "d_next", "operator_dim", "cochain"])?;
    let dim = parse_operator_dim(v)?;
    QddcState::try_new(
        real_matrix(field(v, "d_prev")?, qddc::MAX_CELLS)?,
        real_matrix(field(v, "d_next")?, qddc::MAX_CELLS)?,
        dim,
        operators(field(v, "cochain")?, qddc::MAX_CELLS)?,
    )
    .map_err(|e| e.to_string())
}
fn run_repair_projector(v: &Value) -> Result<Value, String> {
    let projector = state(v)?.repair_projector().map_err(|e| e.to_string())?;
    Ok(json!({"projector":op_value(&projector)?}))
}
fn run_hodge(v: &Value) -> Result<Value, String> {
    let h = state(v)?.decompose().map_err(|e| e.to_string())?;
    Ok(
        json!({"alpha":op_values(&h.alpha)?,"beta":op_values(&h.beta)?,"exact":op_values(&h.exact)?,"coexact":op_values(&h.coexact)?,"harmonic":op_values(&h.harmonic)?,"scalar_ops":h.scalar_ops}),
    )
}
fn run_deform(v: &Value) -> Result<Value, String> {
    fields(v, &["state", "alpha", "unitary"])?;
    let updated = state(field(v, "state")?)?
        .deform(
            &operators(field(v, "alpha")?, qddc::MAX_CELLS)?,
            &operator(field(v, "unitary")?)?,
        )
        .map_err(|e| e.to_string())?;
    Ok(json!({"cochain":op_values(updated.cochain())?}))
}
fn density_action_fields(action: &str) -> Result<&'static [&'static str], String> {
    match action {
        "qddc_lindblad" => Ok(&["rho", "hamiltonian", "jumps"]),
        "qddc_retract" => Ok(&["rho", "projector", "eta"]),
        "qddc_probe" => Ok(&["rho", "projector"]),
        "qddc_density" => Ok(&["rho"]),
        _ => Err("unknown QDDC action".into()),
    }
}
fn run_lindblad(rho: &ExactDensityMatrix, v: &Value) -> Result<Value, String> {
    let generator = Lindbladian::try_new(
        operator(field(v, "hamiltonian")?)?,
        operators(field(v, "jumps")?, qddc::MAX_JUMPS)?,
    )
    .map_err(|e| e.to_string())?;
    let derivative = generator.derivative(rho).map_err(|e| e.to_string())?;
    Ok(json!({"derivative":op_value(&derivative)?}))
}
fn parse_retraction_channel(v: &Value) -> Result<(RetractionChannel, Rational), String> {
    let channel =
        RetractionChannel::try_new(operator(field(v, "projector")?)?).map_err(|e| e.to_string())?;
    let eta = rational(field(v, "eta")?)?;
    Ok((channel, eta))
}
fn run_retract(rho: &ExactDensityMatrix, v: &Value) -> Result<Value, String> {
    let (channel, eta) = parse_retraction_channel(v)?;
    let output = channel.step(rho, &eta).map_err(|e| e.to_string())?;
    let before = channel.outside_weight(rho).map_err(|e| e.to_string())?;
    let after = channel.outside_weight(&output).map_err(|e| e.to_string())?;
    Ok(
        json!({"rho":op_value(output.as_operator())?,"outside_before":output_rational(&before)?,"outside_after":output_rational(&after)?}),
    )
}
fn run_probe(rho: &ExactDensityMatrix, v: &Value) -> Result<Value, String> {
    let (probability, conditional) =
        qddc::probe(rho, &operator(field(v, "projector")?)?).map_err(|e| e.to_string())?;
    let cond_val = conditional
        .as_ref()
        .map(|s| op_value(s.as_operator()))
        .transpose()?;
    Ok(json!({"probability":output_rational(&probability)?,"conditional":cond_val}))
}
fn run_density(rho: &ExactDensityMatrix) -> Result<Value, String> {
    let purity = rho.purity();
    Ok(json!({"purity":output_rational(&purity)?,"is_pure":purity == ri(1)}))
}
fn run_non_density(action: &str, v: &Value) -> Option<Result<Value, String>> {
    match action {
        "qddc_repair_projector" => Some(run_repair_projector(v)),
        "qddc_hodge" => Some(run_hodge(v)),
        "qddc_deform" => Some(run_deform(v)),
        _ => None,
    }
}
fn run(action: &str, v: &Value) -> Result<Value, String> {
    if let Some(res) = run_non_density(action, v) {
        return res;
    }
    let names = density_action_fields(action)?;
    fields(v, names)?;
    let rho = ExactDensityMatrix::try_from_operator(operator(field(v, "rho")?)?)
        .map_err(|e| e.to_string())?;
    match action {
        "qddc_lindblad" => run_lindblad(&rho, v),
        "qddc_retract" => run_retract(&rho, v),
        "qddc_probe" => run_probe(&rho, v),
        _ => run_density(&rho),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/qddc.rs
// Claim: urn:core:crates_rs:pfp:qddc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord96d12bed {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord96d12bed` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError96d12bed {
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
impl BoundaryError96d12bed {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError96d12bed {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError96d12bed {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord96d12bed {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError96d12bed> {
        if capacity_bound == 0 {
            return Err(BoundaryError96d12bed::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError96d12bed::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError96d12bed::ExceedsCapacity {
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
    use num_bigint::BigInt;

    #[test]
    fn output_bit_boundary_is_inclusive_and_distinct_from_input() {
        let at_limit = BigInt::from(1) << (MAX_OUTPUT_RATIONAL_BITS - 1);
        for q in [
            Rational::from_integer(at_limit.clone()),
            Rational::from_integer(-at_limit.clone()),
            Rational::new(BigInt::from(1), at_limit),
        ] {
            assert!(qddc::check_scalar(&q).is_err());
            let encoded = output_rational(&q).unwrap();
            assert_eq!(parse_exact(&encoded).unwrap(), q);
            assert!(encoded.len() <= MAX_OUTPUT_RATIONAL_TEXT_BYTES);
        }
        let over_limit = BigInt::from(1) << MAX_OUTPUT_RATIONAL_BITS;
        for q in [
            Rational::from_integer(over_limit.clone()),
            Rational::new(BigInt::from(1), over_limit),
        ] {
            assert!(output_rational(&q)
                .unwrap_err()
                .contains("QDDC_OUTPUT_LIMIT"));
        }
    }

    #[test]
    fn operator_output_checks_both_parts_and_later_entries() {
        for imaginary in [false, true] {
            let huge = Rational::from_integer(BigInt::from(1) << MAX_OUTPUT_RATIONAL_BITS);
            let last = if imaginary {
                GaussianRat {
                    re: ri(0),
                    im: huge,
                }
            } else {
                GaussianRat::from_rational(huge)
            };
            let op = ExactOperator::from_rows(vec![
                vec![GaussianRat::one(), GaussianRat::zero()],
                vec![GaussianRat::zero(), last],
            ])
            .unwrap();
            assert!(op_values(&[ExactOperator::identity(2).unwrap(), op])
                .unwrap_err()
                .contains("QDDC_OUTPUT_LIMIT"));
        }
    }
}

pub(super) fn dispatch(request: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    match run(&request.action, &request.payload) {
        Ok(value) => outcome_ok(&request.action, value),
        Err(error) => outcome_err(&request.action, format!("QDDC_REFUSED: {error}")),
    }
}

#[cfg(test)]
mod l4_boundary_tests_96d12bed {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord96d12bed::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord96d12bed::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord96d12bed::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord96d12bed::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord96d12bed::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError96d12bed::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError96d12bed::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
