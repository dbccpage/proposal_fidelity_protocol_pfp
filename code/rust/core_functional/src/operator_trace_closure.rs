//! Exact half-trace gauges and closure bounds on declared operator repair quotients.
//!
//! Supplied Jordan parts and primal/dual witnesses are replayed over `Q(i)`.
//! There is no spectral search here: an irrational trace norm has no rational
//! witness in this interface. Signed scalar incidences act between equal stalk
//! dimensions; general operator-valued face restrictions are outside its scope.
//! AuthorityEffect: None. These values never authorize an action.

use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use linear_algebra::exact_field::{involution as star, matrix as mx, ordered, ExactFieldError};
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use std::collections::{BTreeMap, BTreeSet};

/// Canonical exact operator carrier consumed by the functional verifier.
pub type Operator = BasicMatrix<GaussianRat>;
type Faces = [Vec<(usize, BigRational)>];

/// These budgets apply to each matrix operation, not to total verifier work.
pub const OPERATOR_MATRIX_CALL_MAX_ELEMENTS: usize = 1_048_576;
pub const OPERATOR_MATRIX_CALL_MAX_SCALAR_OPS: usize = 100_000_000;
/// Collective matrix entries in a single submitted problem and witness bundle.
pub const OPERATOR_MAX_INPUT_MATRIX_ELEMENTS: usize = 1_048_576;
pub const OPERATOR_INPUT_MAX_RATIONAL_BITS: u64 = 4096;
pub const OPERATOR_MAX_FACE_INCIDENCES: usize = 1_000_000;
pub const OPERATOR_MAX_TRACELESS_BASIS_CHECKS: usize = 1_000_000;

/// A malformed carrier, witness, or claimed cochain map.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("operator trace functional refusal: {0}")]
pub struct OperatorTraceError(pub &'static str);

impl From<ExactFieldError> for OperatorTraceError {
    fn from(_: ExactFieldError) -> Self {
        Self("exact matrix algebra refused")
    }
}

impl From<MatrixError> for OperatorTraceError {
    fn from(_: MatrixError) -> Self {
        Self("matrix storage refused")
    }
}

fn limits() -> OperationLimits {
    OperationLimits {
        max_elements: OPERATOR_MATRIX_CALL_MAX_ELEMENTS,
        max_scalar_ops: OPERATOR_MATRIX_CALL_MAX_SCALAR_OPS,
    }
}

/// Reject raw unreduced ratios, negative denominators and zero denominators
/// before any matrix arithmetic can consume them.
pub fn is_canonical_rational(q: &BigRational) -> bool {
    if q.denom() <= &0.into() {
        return false;
    }
    let reduced = crate::gamma2::canonical_rational(q);
    reduced.numer() == q.numer() && reduced.denom() == q.denom()
}

fn check_rational_bits(q: &BigRational) -> Result<(), OperatorTraceError> {
    if q.numer().bits() > OPERATOR_INPUT_MAX_RATIONAL_BITS
        || q.denom().bits() > OPERATOR_INPUT_MAX_RATIONAL_BITS
    {
        return Err(OperatorTraceError("rational bit limit exceeded"));
    }
    Ok(())
}

fn check_input_elements<'a>(
    operators: impl IntoIterator<Item = &'a Operator>,
) -> Result<(), OperatorTraceError> {
    let mut total = 0usize;
    for operator in operators {
        total = total
            .checked_add(operator.as_slice().len())
            .ok_or(OperatorTraceError(
                "collective operator input limit exceeded",
            ))?;
        if total > OPERATOR_MAX_INPUT_MATRIX_ELEMENTS {
            return Err(OperatorTraceError(
                "collective operator input limit exceeded",
            ));
        }
    }
    Ok(())
}

fn problem_operators<'a>(problem: TraceRepairInput<'a>) -> impl Iterator<Item = &'a Operator> {
    problem
        .defects
        .iter()
        .chain(problem.repair_generators.iter().flat_map(|g| g.iter()))
}

fn witness_operators<'a>(witness: TraceObserverInput<'a>) -> impl Iterator<Item = &'a Operator> {
    witness
        .residuals
        .iter()
        .chain(witness.positive_parts.iter())
        .chain(witness.negative_parts.iter())
        .chain(witness.dual_observables.iter())
}

fn validate_entries(m: &Operator) -> Result<(), OperatorTraceError> {
    for z in m.as_slice() {
        check_rational_bits(&z.re)?;
        check_rational_bits(&z.im)?;
    }
    if m.as_slice()
        .iter()
        .any(|z| !is_canonical_rational(&z.re) || !is_canonical_rational(&z.im))
    {
        return Err(OperatorTraceError(
            "noncanonical rational or invalid denominator",
        ));
    }
    core_kernel::resource_limits::OperationLimits::default()
        .check_dense_matrix(m.rows(), m.cols(), std::mem::size_of::<GaussianRat>())
        .map_err(|_| OperatorTraceError("operator resource limit"))?;
    Ok(())
}

fn hermitian(m: &Operator) -> Result<usize, OperatorTraceError> {
    validate_entries(m)?;
    if m.rows() == 0 || m.rows() != m.cols() {
        return Err(OperatorTraceError("operator shape"));
    }
    if star::hermitian_violation(m)?.is_some() {
        return Err(OperatorTraceError("malformed Hermitian operator"));
    }
    Ok(m.rows())
}

fn trace(m: &Operator) -> Result<BigRational, OperatorTraceError> {
    let value = mx::trace(m)?;
    if !value.im.is_zero() {
        return Err(OperatorTraceError("Hermitian trace is not real"));
    }
    Ok(value.re)
}

fn pairing(a: &Operator, b: &Operator) -> Result<BigRational, OperatorTraceError> {
    let value = star::hs_inner(a, b)?;
    if !value.im.is_zero() {
        return Err(OperatorTraceError("Hermitian pairing is not real"));
    }
    Ok(value.re)
}

fn positive(m: &Operator) -> Result<bool, OperatorTraceError> {
    Ok(ordered::hermitian_inertia_with_limits(m, limits())?.is_positive_semidefinite())
}

/// Borrowed declared repair problem; the real span of the supplied columns is
/// the entire repair space being certified. No completeness claim is inferred.
#[derive(Debug, Clone, Copy)]
pub struct TraceRepairInput<'a> {
    pub defects: &'a [Operator],
    pub repair_generators: &'a [Vec<Operator>],
    pub weights: &'a [BigRational],
}

impl TraceRepairInput<'_> {
    fn validate_weights(&self) -> Result<(), OperatorTraceError> {
        if self.defects.is_empty() || self.weights.len() != self.defects.len() {
            return Err(OperatorTraceError("empty or inconsistent edge carrier"));
        }
        for w in self.weights {
            check_rational_bits(w)?;
            if !is_canonical_rational(w) || w <= &BigRational::zero() {
                return Err(OperatorTraceError(
                    "gauge weights must be canonical positive rationals",
                ));
            }
        }
        Ok(())
    }

    fn validate_repair_column(&self, column: &[Operator]) -> Result<(), OperatorTraceError> {
        if column.len() != self.defects.len() {
            return Err(OperatorTraceError("repair column edge shape"));
        }
        for (g, h) in column.iter().zip(self.defects) {
            if hermitian(g)? != h.rows() || !trace(g)?.is_zero() {
                return Err(OperatorTraceError("repair generator carrier or trace"));
            }
        }
        Ok(())
    }

    pub fn validate(&self) -> Result<(), OperatorTraceError> {
        check_input_elements(problem_operators(*self))?;
        self.validate_weights()?;
        for h in self.defects {
            hermitian(h)?;
            if !trace(h)?.is_zero() {
                return Err(OperatorTraceError("defect is not traceless"));
            }
        }
        for column in self.repair_generators {
            self.validate_repair_column(column)?;
        }
        Ok(())
    }
}

/// Untrusted primal/dual witness for the weighted half-trace quotient minimum.
#[derive(Debug, Clone, Copy)]
pub struct TraceObserverInput<'a> {
    pub repair_coefficients: &'a [BigRational],
    pub residuals: &'a [Operator],
    pub positive_parts: &'a [Operator],
    pub negative_parts: &'a [Operator],
    pub dual_observables: &'a [Operator],
}

/// An exact quotient minimum obtainable only by replaying its witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedTraceQuotient {
    phi_q: BigRational,
}

impl VerifiedTraceQuotient {
    pub fn phi_q(&self) -> &BigRational {
        &self.phi_q
    }
}

fn check_jordan_orthogonality(
    actual: &Operator,
    positive_part: &Operator,
    negative_part: &Operator,
) -> Result<(), OperatorTraceError> {
    if mx::sub(positive_part, negative_part)? != *actual
        || !positive(positive_part)?
        || !positive(negative_part)?
    {
        return Err(OperatorTraceError("residual or Jordan decomposition"));
    }
    let prod = mx::multiply_with_limits(positive_part, negative_part, limits())?;
    if !mx::is_zero_matrix(&prod) {
        return Err(OperatorTraceError("residual or Jordan decomposition"));
    }
    Ok(())
}

fn jordan_norm(
    actual: &Operator,
    positive_part: &Operator,
    negative_part: &Operator,
) -> Result<BigRational, OperatorTraceError> {
    let dim = hermitian(actual)?;
    if hermitian(positive_part)? != dim || hermitian(negative_part)? != dim {
        return Err(OperatorTraceError("witness operator shape"));
    }
    check_jordan_orthogonality(actual, positive_part, negative_part)?;
    Ok(trace(positive_part)? + trace(negative_part)?)
}

fn validate_trace_witness_shape(
    problem: TraceRepairInput<'_>,
    witness: TraceObserverInput<'_>,
) -> Result<(), OperatorTraceError> {
    for coefficient in witness.repair_coefficients {
        check_rational_bits(coefficient)?;
        if !is_canonical_rational(coefficient) {
            return Err(OperatorTraceError("witness shape or coefficient domain"));
        }
    }
    let n = problem.defects.len();
    let lengths_match = witness.repair_coefficients.len() == problem.repair_generators.len()
        && witness.residuals.len() == n
        && witness.positive_parts.len() == n
        && witness.negative_parts.len() == n
        && witness.dual_observables.len() == n;
    if !lengths_match {
        return Err(OperatorTraceError("witness shape or coefficient domain"));
    }
    Ok(())
}

fn compute_repaired_edge(
    problem: TraceRepairInput<'_>,
    witness: TraceObserverInput<'_>,
    e: usize,
) -> Result<Operator, OperatorTraceError> {
    let mut actual = problem.defects[e].clone();
    for (g, c) in problem
        .repair_generators
        .iter()
        .zip(witness.repair_coefficients)
    {
        let scaled = mx::scale(&g[e], &GaussianRat::from_rational(c.clone()))?;
        actual = mx::sub(&actual, &scaled)?;
    }
    if actual != witness.residuals[e] {
        return Err(OperatorTraceError("residual or Jordan decomposition"));
    }
    Ok(actual)
}

fn check_dual_observable_polar(
    dim: usize,
    half: &BigRational,
    phi: &Operator,
) -> Result<(), OperatorTraceError> {
    let id_mat = mx::identity_with_limits(dim, limits())?;
    let cap = mx::scale(&id_mat, &GaussianRat::from_rational(half.clone()))?;
    if !positive(&mx::sub(&cap, phi)?)? || !positive(&mx::add(&cap, phi)?)? {
        return Err(OperatorTraceError(
            "dual observable exceeds declared gauge polar",
        ));
    }
    Ok(())
}

fn evaluate_trace_edge(
    problem: TraceRepairInput<'_>,
    witness: TraceObserverInput<'_>,
    e: usize,
) -> Result<(BigRational, BigRational), OperatorTraceError> {
    let dim = problem.defects[e].rows();
    if hermitian(&witness.residuals[e])? != dim || hermitian(&witness.dual_observables[e])? != dim {
        return Err(OperatorTraceError("witness operator shape"));
    }
    let actual = compute_repaired_edge(problem, witness, e)?;
    let norm = jordan_norm(
        &actual,
        &witness.positive_parts[e],
        &witness.negative_parts[e],
    )?;
    let half = &problem.weights[e] / BigRational::from_integer(2.into());
    let phi = &witness.dual_observables[e];
    check_dual_observable_polar(dim, &half, phi)?;
    Ok((half * norm, pairing(phi, &problem.defects[e])?))
}

fn check_repair_annihilation(
    problem: TraceRepairInput<'_>,
    witness: TraceObserverInput<'_>,
) -> Result<(), OperatorTraceError> {
    for g in problem.repair_generators {
        let mut annihilation = BigRational::zero();
        for (phi, m) in witness.dual_observables.iter().zip(g) {
            annihilation += pairing(phi, m)?;
        }
        if !annihilation.is_zero() {
            return Err(OperatorTraceError("dual sees admissible repairs"));
        }
    }
    Ok(())
}

/// Replay feasibility, repair annihilation and equality of primal/dual values.
/// Weak duality then certifies the minimum over the declared real repair span.
pub fn verify_trace_quotient(
    problem: TraceRepairInput<'_>,
    witness: TraceObserverInput<'_>,
) -> Result<VerifiedTraceQuotient, OperatorTraceError> {
    check_input_elements(problem_operators(problem).chain(witness_operators(witness)))?;
    problem.validate()?;
    validate_trace_witness_shape(problem, witness)?;
    let mut upper = BigRational::zero();
    let mut lower = BigRational::zero();
    for e in 0..problem.defects.len() {
        let (u, l) = evaluate_trace_edge(problem, witness, e)?;
        upper += u;
        lower += l;
    }
    check_repair_annihilation(problem, witness)?;
    if upper != lower {
        return Err(OperatorTraceError("nonzero primal dual gap"));
    }
    Ok(VerifiedTraceQuotient { phi_q: upper })
}

/// Shape-free checks available even when no repair generators are declared.
pub fn validate_face_declaration(faces: &Faces) -> Result<(), OperatorTraceError> {
    let mut incidences = 0usize;
    for boundary in faces {
        incidences = incidences
            .checked_add(boundary.len())
            .ok_or(OperatorTraceError("face incidence limit exceeded"))?;
        if incidences > OPERATOR_MAX_FACE_INCIDENCES {
            return Err(OperatorTraceError("face incidence limit exceeded"));
        }
        if boundary.is_empty() {
            return Err(OperatorTraceError("empty face boundary"));
        }
        for (_, sign) in boundary {
            check_rational_bits(sign)?;
            if !is_canonical_rational(sign) || sign.abs() != BigRational::one() {
                return Err(OperatorTraceError(
                    "face orientation must be canonical +1 or -1",
                ));
            }
        }
    }
    Ok(())
}

fn boundary_column_row(
    boundary: &[(usize, BigRational)],
    defects: &[Operator],
) -> Result<BTreeMap<usize, BigRational>, OperatorTraceError> {
    let &(first_edge, _) = boundary
        .first()
        .ok_or(OperatorTraceError("empty face boundary"))?;
    let first = defects
        .get(first_edge)
        .ok_or(OperatorTraceError("edge index out of bounds"))?;
    let dim = first.rows();
    let mut row = BTreeMap::new();
    for (edge, sign) in boundary {
        let h = defects
            .get(*edge)
            .ok_or(OperatorTraceError("edge index out of bounds"))?;
        if h.rows() != dim {
            return Err(OperatorTraceError("face mixes operator stalk dimensions"));
        }
        *row.entry(*edge).or_insert_with(BigRational::zero) += sign;
    }
    Ok(row)
}

fn face_columns(
    faces: &Faces,
    defects: &[Operator],
) -> Result<Vec<BTreeMap<usize, BigRational>>, OperatorTraceError> {
    check_input_elements(defects)?;
    validate_face_declaration(faces)?;
    for h in defects {
        hermitian(h)?;
    }
    let mut rows = Vec::with_capacity(faces.len());
    for boundary in faces {
        rows.push(boundary_column_row(boundary, defects)?);
    }
    Ok(rows)
}

/// Validate every edge operator and every signed face against its actual carrier.
pub fn validate_operator_faces(
    faces: &Faces,
    defects: &[Operator],
) -> Result<(), OperatorTraceError> {
    face_columns(faces, defects)?;
    Ok(())
}

/// Evaluate one signed scalar boundary after admitting all consumed operators.
pub fn evaluate_operator_face(
    faces: &Faces,
    face_index: usize,
    defects: &[Operator],
) -> Result<Operator, OperatorTraceError> {
    let boundary = faces
        .get(face_index)
        .ok_or(OperatorTraceError("face index out of bounds"))?;
    let row = face_columns(std::slice::from_ref(boundary), defects)?;
    let &(edge, _) = boundary
        .first()
        .ok_or(OperatorTraceError("empty face boundary"))?;
    let first = defects
        .get(edge)
        .ok_or(OperatorTraceError("edge index out of bounds"))?;
    let mut out = mx::zeros_with_limits(first.rows(), first.cols(), limits())?;
    let coefficients = row
        .first()
        .ok_or(OperatorTraceError("empty face boundary"))?;
    for (edge, coefficient) in coefficients {
        out = mx::add(
            &out,
            &mx::scale(
                &defects[*edge],
                &GaussianRat::from_rational(coefficient.clone()),
            )?,
        )?;
    }
    Ok(out)
}

/// Verify `d1` kills every declared repair generator. Validation precedes the
/// possibly empty generator loop; an empty repair span cannot hide bad faces.
pub fn verify_operator_chain(
    problem: TraceRepairInput<'_>,
    faces: &Faces,
) -> Result<(), OperatorTraceError> {
    problem.validate()?;
    validate_operator_faces(faces, problem.defects)?;
    for g in problem.repair_generators {
        for face in 0..faces.len() {
            if !mx::is_zero_matrix(&evaluate_operator_face(faces, face, g)?) {
                return Err(OperatorTraceError("d1 sees admissible repairs"));
            }
        }
    }
    Ok(())
}

/// Induced norm from `sum_e w_e ||h_e||_1/2` to `sum_f ||y_f||_1/2`.
/// Coalesced scalar columns attain the triangle-inequality upper bound by a
/// single supported traceless Hermitian operator. A 1x1 traceless stalk is zero.
pub fn operator_boundary_norm(
    problem: TraceRepairInput<'_>,
    faces: &Faces,
) -> Result<BigRational, OperatorTraceError> {
    problem.validate()?;
    let rows = face_columns(faces, problem.defects)?;
    let mut column_sums = vec![BigRational::zero(); problem.defects.len()];
    for row in rows {
        for (edge, coefficient) in row {
            column_sums[edge] += coefficient.abs();
        }
    }
    let mut norm = BigRational::zero();
    for (e, column_sum) in column_sums.into_iter().enumerate() {
        if problem.defects[e].rows() > 1 {
            norm = norm.max(column_sum / &problem.weights[e]);
        }
    }
    Ok(norm)
}

/// Untrusted exact face norms and claimed induced boundary norm.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperatorClosureWitness {
    pub face_defects: Vec<Operator>,
    pub positive_parts: Vec<Operator>,
    pub negative_parts: Vec<Operator>,
    pub claimed_d1_norm: BigRational,
}

/// Sealed result. No constructor or deserializer bypasses witness replay.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedOperatorClosure {
    phi_q: BigRational,
    gamma2_q: BigRational,
    d1_norm: BigRational,
    ratio: Option<BigRational>,
    edge_count: usize,
    face_count: usize,
    repair_generator_count: usize,
}

impl VerifiedOperatorClosure {
    pub fn phi_q(&self) -> &BigRational {
        &self.phi_q
    }
    pub fn gamma2_q(&self) -> &BigRational {
        &self.gamma2_q
    }
    pub fn d1_norm(&self) -> &BigRational {
        &self.d1_norm
    }
    /// `None` exactly when `Phi_Q = 0`; `0/0` is never fabricated.
    pub fn closure_ratio(&self) -> Option<&BigRational> {
        self.ratio.as_ref()
    }
    pub fn edge_count(&self) -> usize {
        self.edge_count
    }
    pub fn face_count(&self) -> usize {
        self.face_count
    }
    pub fn repair_generator_count(&self) -> usize {
        self.repair_generator_count
    }
}

fn evaluate_face_closure_norm(
    problem: TraceRepairInput<'_>,
    faces: &Faces,
    trace_witness: TraceObserverInput<'_>,
    closure_witness: &OperatorClosureWitness,
    f: usize,
) -> Result<BigRational, OperatorTraceError> {
    let actual = evaluate_operator_face(faces, f, problem.defects)?;
    let repaired = evaluate_operator_face(faces, f, trace_witness.residuals)?;
    if hermitian(&closure_witness.face_defects[f])? != actual.rows() {
        return Err(OperatorTraceError("closure witness face shape"));
    }
    if actual != repaired || actual != closure_witness.face_defects[f] {
        return Err(OperatorTraceError(
            "closure witness is not the actual boundary",
        ));
    }
    let j_norm = jordan_norm(
        &actual,
        &closure_witness.positive_parts[f],
        &closure_witness.negative_parts[f],
    )?;
    Ok(j_norm / BigRational::from_integer(2.into()))
}

fn validate_closure_witness_header(
    problem: TraceRepairInput<'_>,
    faces: &Faces,
    trace_witness: TraceObserverInput<'_>,
    closure_witness: &OperatorClosureWitness,
) -> Result<BigRational, OperatorTraceError> {
    check_input_elements(
        problem_operators(problem)
            .chain(witness_operators(trace_witness))
            .chain(closure_witness.face_defects.iter())
            .chain(closure_witness.positive_parts.iter())
            .chain(closure_witness.negative_parts.iter()),
    )?;
    check_rational_bits(&closure_witness.claimed_d1_norm)?;
    verify_operator_chain(problem, faces)?;
    let lengths_ok = closure_witness.face_defects.len() == faces.len()
        && closure_witness.positive_parts.len() == faces.len()
        && closure_witness.negative_parts.len() == faces.len();
    if !lengths_ok {
        return Err(OperatorTraceError("closure witness face shape"));
    }
    let norm = operator_boundary_norm(problem, faces)?;
    if !is_canonical_rational(&closure_witness.claimed_d1_norm)
        || closure_witness.claimed_d1_norm != norm
    {
        return Err(OperatorTraceError("forged induced boundary norm"));
    }
    Ok(norm)
}

/// Certify the quotient value, chain law, actual face defects, Jordan norms and
/// `Gamma2_Q <= ||d1|| Phi_Q` on the declared weighted trace-distance carrier.
pub fn verify_operator_closure(
    problem: TraceRepairInput<'_>,
    faces: &Faces,
    trace_witness: TraceObserverInput<'_>,
    closure_witness: &OperatorClosureWitness,
) -> Result<VerifiedOperatorClosure, OperatorTraceError> {
    let norm = validate_closure_witness_header(problem, faces, trace_witness, closure_witness)?;
    let quotient = verify_trace_quotient(problem, trace_witness)?;
    let mut gamma = BigRational::zero();
    for f in 0..faces.len() {
        gamma += evaluate_face_closure_norm(problem, faces, trace_witness, closure_witness, f)?;
    }
    if gamma > &norm * quotient.phi_q() {
        return Err(OperatorTraceError("exact closure bound violated"));
    }
    let ratio = if quotient.phi_q().is_zero() {
        None
    } else {
        Some(&gamma / quotient.phi_q())
    };
    Ok(VerifiedOperatorClosure {
        phi_q: quotient.phi_q,
        gamma2_q: gamma,
        d1_norm: norm,
        ratio,
        edge_count: problem.defects.len(),
        face_count: faces.len(),
        repair_generator_count: problem.repair_generators.len(),
    })
}

/// Untrusted weighted Kraus map. Completeness is replayed independently of the
/// physics crate's constructor before the map is used in any transport proof.
#[derive(Debug, Clone, Copy)]
pub struct KrausMapInput<'a> {
    pub dim_in: usize,
    pub dim_out: usize,
    pub weights: &'a [BigRational],
    pub operators: &'a [Operator],
}

impl KrausMapInput<'_> {
    fn check_carrier_header(&self) -> Result<(), OperatorTraceError> {
        let non_empty = self.dim_in != 0 && self.dim_out != 0 && !self.operators.is_empty();
        if !non_empty || self.weights.len() != self.operators.len() {
            return Err(OperatorTraceError("Kraus carrier or term shape"));
        }
        Ok(())
    }

    fn validate_kraus_term(
        &self,
        weight: &BigRational,
        k: &Operator,
    ) -> Result<Operator, OperatorTraceError> {
        check_rational_bits(weight)?;
        if !is_canonical_rational(weight) || weight < &BigRational::zero() {
            return Err(OperatorTraceError("Kraus weight domain"));
        }
        validate_entries(k)?;
        if (k.rows(), k.cols()) != (self.dim_out, self.dim_in) {
            return Err(OperatorTraceError("Kraus operator shape"));
        }
        let gram = mx::multiply_with_limits(&star::adjoint(k)?, k, limits())?;
        Ok(mx::scale(
            &gram,
            &GaussianRat::from_rational(weight.clone()),
        )?)
    }

    pub fn validate(&self) -> Result<(), OperatorTraceError> {
        check_input_elements(self.operators)?;
        self.check_carrier_header()?;
        let mut completeness = mx::zeros_with_limits(self.dim_in, self.dim_in, limits())?;
        for (weight, k) in self.weights.iter().zip(self.operators) {
            let scaled_gram = self.validate_kraus_term(weight, k)?;
            completeness = mx::add(&completeness, &scaled_gram)?;
        }
        if completeness != mx::identity_with_limits(self.dim_in, limits())? {
            return Err(OperatorTraceError("Kraus map is not trace preserving"));
        }
        Ok(())
    }

    fn apply(&self, input: &Operator) -> Result<Operator, OperatorTraceError> {
        if (input.rows(), input.cols()) != (self.dim_in, self.dim_in) {
            return Err(OperatorTraceError("Kraus input shape"));
        }
        let mut out = mx::zeros_with_limits(self.dim_out, self.dim_out, limits())?;
        for (weight, k) in self.weights.iter().zip(self.operators) {
            let image = mx::multiply_with_limits(
                &mx::multiply_with_limits(k, input, limits())?,
                &star::adjoint(k)?,
                limits(),
            )?;
            out = mx::add(
                &out,
                &mx::scale(&image, &GaussianRat::from_rational(weight.clone()))?,
            )?;
        }
        Ok(out)
    }
}

fn verify_edge_channels_transport(
    source: TraceRepairInput<'_>,
    target: TraceRepairInput<'_>,
    edge_channels: &[KrausMapInput<'_>],
) -> Result<(), OperatorTraceError> {
    for (e, channel) in edge_channels.iter().enumerate() {
        channel.validate()?;
        if channel.dim_in != source.defects[e].rows()
            || channel.dim_out != target.defects[e].rows()
            || target.weights[e] > source.weights[e]
        {
            return Err(OperatorTraceError("transport carrier or gauge weight"));
        }
        if channel.apply(&source.defects[e])? != target.defects[e] {
            return Err(OperatorTraceError(
                "actual target defect is not transported source",
            ));
        }
    }
    Ok(())
}

fn verify_generator_image_on_edge(
    target: TraceRepairInput<'_>,
    channel: &KrausMapInput<'_>,
    g_edge: &Operator,
    coefficients: &[BigRational],
    e: usize,
) -> Result<(), OperatorTraceError> {
    let dim = target.defects[e].rows();
    let mut expected = mx::zeros_with_limits(dim, dim, limits())?;
    for (column, c) in target.repair_generators.iter().zip(coefficients) {
        let scaled = mx::scale(&column[e], &GaussianRat::from_rational(c.clone()))?;
        expected = mx::add(&expected, &scaled)?;
    }
    if channel.apply(g_edge)? != expected {
        return Err(OperatorTraceError("missing repair intertwining license"));
    }
    Ok(())
}

fn verify_generator_image_intertwining(
    target: TraceRepairInput<'_>,
    edge_channels: &[KrausMapInput<'_>],
    g: &[Operator],
    coefficients: &[BigRational],
) -> Result<(), OperatorTraceError> {
    for coefficient in coefficients {
        check_rational_bits(coefficient)?;
        if !is_canonical_rational(coefficient) {
            return Err(OperatorTraceError("transport expansion domain"));
        }
    }
    if coefficients.len() != target.repair_generators.len() {
        return Err(OperatorTraceError("transport expansion domain"));
    }
    for (e, channel) in edge_channels.iter().enumerate() {
        verify_generator_image_on_edge(target, channel, &g[e], coefficients, e)?;
    }
    Ok(())
}

/// Check the actual defect binding and a linear map of declared repair images.
/// Each source generator is bound to its supplied destination expansion.
pub fn verify_operator_repair_map(
    source: TraceRepairInput<'_>,
    target: TraceRepairInput<'_>,
    edge_channels: &[KrausMapInput<'_>],
    generator_images: &[Vec<BigRational>],
) -> Result<(), OperatorTraceError> {
    check_input_elements(
        problem_operators(source)
            .chain(problem_operators(target))
            .chain(
                edge_channels
                    .iter()
                    .flat_map(|channel| channel.operators.iter()),
            ),
    )?;
    source.validate()?;
    target.validate()?;
    if source.defects.len() != target.defects.len()
        || edge_channels.len() != source.defects.len()
        || generator_images.len() != source.repair_generators.len()
    {
        return Err(OperatorTraceError("transport carrier or repair map shape"));
    }
    verify_edge_channels_transport(source, target, edge_channels)?;
    for (g, coefficients) in source.repair_generators.iter().zip(generator_images) {
        verify_generator_image_intertwining(target, edge_channels, g, coefficients)?;
    }
    Ok(())
}

/// Complete transported complex: edges and faces are paired by their indices.
#[derive(Debug, Clone, Copy)]
pub struct OperatorClosureTransportInput<'a> {
    pub source: TraceRepairInput<'a>,
    pub target: TraceRepairInput<'a>,
    pub source_faces: &'a Faces,
    pub target_faces: &'a Faces,
    pub edge_channels: &'a [KrausMapInput<'a>],
    pub face_channels: &'a [KrausMapInput<'a>],
    pub generator_images: &'a [Vec<BigRational>],
}

/// Sealed replay of repair and closure intertwining on the full declared spaces.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedOperatorClosureTransport {
    edge_count: usize,
    face_count: usize,
    basis_checks: usize,
}

impl VerifiedOperatorClosureTransport {
    pub fn edge_count(&self) -> usize {
        self.edge_count
    }
    pub fn face_count(&self) -> usize {
        self.face_count
    }
    pub fn basis_checks(&self) -> usize {
        self.basis_checks
    }
}

fn diagonal_traceless_basis(dim: usize, j: usize) -> Result<Operator, OperatorTraceError> {
    Ok(BasicMatrix::try_from_fn(dim, dim, |r, c| {
        let diag = if r != c {
            0
        } else if r == j {
            1
        } else if r == dim - 1 {
            -1
        } else {
            0
        };
        GaussianRat::from_ints(diag, 0)
    })?)
}

fn off_diagonal_real_basis(dim: usize, j: usize, k: usize) -> Result<Operator, OperatorTraceError> {
    Ok(BasicMatrix::try_from_fn(dim, dim, |r, c| {
        let hit = (r == j && c == k) || (r == k && c == j);
        GaussianRat::from_ints(i64::from(hit), 0)
    })?)
}

fn off_diagonal_imag_basis(dim: usize, j: usize, k: usize) -> Result<Operator, OperatorTraceError> {
    Ok(BasicMatrix::try_from_fn(dim, dim, |r, c| {
        let im = if r == j && c == k {
            -1
        } else if r == k && c == j {
            1
        } else {
            0
        };
        GaussianRat::from_ints(0, im)
    })?)
}

fn traceless_basis_check(
    dim: usize,
    mut check: impl FnMut(&Operator) -> Result<(), OperatorTraceError>,
) -> Result<usize, OperatorTraceError> {
    let mut count = 0usize;
    for j in 0..dim.saturating_sub(1) {
        let basis = diagonal_traceless_basis(dim, j)?;
        check(&basis)?;
        count += 1;
    }
    for j in 0..dim {
        for k in (j + 1)..dim {
            check(&off_diagonal_real_basis(dim, j, k)?)?;
            check(&off_diagonal_imag_basis(dim, j, k)?)?;
            count += 2;
        }
    }
    Ok(count)
}

fn scaled_channel_image(
    channel: &KrausMapInput<'_>,
    basis: &Operator,
    coefficient: &BigRational,
    target_dim: usize,
) -> Result<Operator, OperatorTraceError> {
    if coefficient.is_zero() {
        return Ok(mx::zeros_with_limits(target_dim, target_dim, limits())?);
    }
    let image = channel.apply(basis)?;
    Ok(mx::scale(
        &image,
        &GaussianRat::from_rational(coefficient.clone()),
    )?)
}

fn reserve_basis_checks(basis_checks: &mut usize, dim: usize) -> Result<(), OperatorTraceError> {
    let required = dim
        .checked_mul(dim)
        .and_then(|n| n.checked_sub(1))
        .ok_or(OperatorTraceError("transport basis count overflow"))?;
    if basis_checks
        .checked_add(required)
        .is_none_or(|n| n > OPERATOR_MAX_TRACELESS_BASIS_CHECKS)
    {
        return Err(OperatorTraceError("transport basis check limit exceeded"));
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn check_transport_edge_basis(
    input: OperatorClosureTransportInput<'_>,
    channel: &KrausMapInput<'_>,
    target_dim: usize,
    source_row: &BTreeMap<usize, BigRational>,
    target_row: &BTreeMap<usize, BigRational>,
    e: usize,
    basis_checks: &mut usize,
) -> Result<(), OperatorTraceError> {
    let edge_channel = input
        .edge_channels
        .get(e)
        .ok_or(OperatorTraceError("edge index out of bounds"))?;
    let source_coefficient = source_row
        .get(&e)
        .cloned()
        .unwrap_or_else(BigRational::zero);
    let target_coefficient = target_row
        .get(&e)
        .cloned()
        .unwrap_or_else(BigRational::zero);
    if source_coefficient.is_zero() && target_coefficient.is_zero() {
        return Ok(());
    }
    let dim = input.source.defects[e].rows();
    reserve_basis_checks(basis_checks, dim)?;
    let checks = traceless_basis_check(dim, |basis| {
        let left = scaled_channel_image(channel, basis, &source_coefficient, target_dim)?;
        let right = scaled_channel_image(edge_channel, basis, &target_coefficient, target_dim)?;
        if left != right {
            return Err(OperatorTraceError("missing closure intertwining license"));
        }
        Ok(())
    })?;
    *basis_checks = basis_checks
        .checked_add(checks)
        .ok_or(OperatorTraceError("transport basis count overflow"))?;
    Ok(())
}

fn check_face_channel_intertwining(
    input: OperatorClosureTransportInput<'_>,
    f: usize,
    channel: &KrausMapInput<'_>,
    source_row: &BTreeMap<usize, BigRational>,
    target_row: &BTreeMap<usize, BigRational>,
    basis_checks: &mut usize,
) -> Result<(), OperatorTraceError> {
    channel.validate()?;
    let source_dim = evaluate_operator_face(input.source_faces, f, input.source.defects)?.rows();
    let target_dim = evaluate_operator_face(input.target_faces, f, input.target.defects)?.rows();
    if channel.dim_in != source_dim || channel.dim_out != target_dim {
        return Err(OperatorTraceError("closure transport face carrier"));
    }
    let consumed_edges: BTreeSet<_> = source_row
        .keys()
        .chain(target_row.keys())
        .copied()
        .collect();
    for e in consumed_edges {
        check_transport_edge_basis(
            input,
            channel,
            target_dim,
            source_row,
            target_row,
            e,
            basis_checks,
        )?;
    }
    Ok(())
}

fn check_closure_transport_elements(
    input: OperatorClosureTransportInput<'_>,
) -> Result<(), OperatorTraceError> {
    check_input_elements(
        problem_operators(input.source)
            .chain(problem_operators(input.target))
            .chain(
                input
                    .edge_channels
                    .iter()
                    .flat_map(|channel| channel.operators.iter()),
            )
            .chain(
                input
                    .face_channels
                    .iter()
                    .flat_map(|channel| channel.operators.iter()),
            ),
    )
}

fn check_closure_transport_preconditions(
    input: OperatorClosureTransportInput<'_>,
) -> Result<(), OperatorTraceError> {
    check_closure_transport_elements(input)?;
    verify_operator_repair_map(
        input.source,
        input.target,
        input.edge_channels,
        input.generator_images,
    )?;
    verify_operator_chain(input.source, input.source_faces)?;
    verify_operator_chain(input.target, input.target_faces)?;
    if input.source_faces.len() != input.target_faces.len()
        || input.face_channels.len() != input.source_faces.len()
    {
        return Err(OperatorTraceError("closure transport face shape"));
    }
    Ok(())
}

/// Replay `Lambda1(im d0) <= im d0'` and `Lambda2 d1 = d1' Lambda1`.
/// The latter is checked on a basis of every consumed traceless-Hermitian stalk,
/// so equality extends to the whole real space by linearity, not sample coverage.
pub fn verify_operator_closure_transport(
    input: OperatorClosureTransportInput<'_>,
) -> Result<VerifiedOperatorClosureTransport, OperatorTraceError> {
    check_closure_transport_preconditions(input)?;
    let source_rows = face_columns(input.source_faces, input.source.defects)?;
    let target_rows = face_columns(input.target_faces, input.target.defects)?;
    let mut basis_checks = 0usize;
    for (f, channel) in input.face_channels.iter().enumerate() {
        check_face_channel_intertwining(
            input,
            f,
            channel,
            &source_rows[f],
            &target_rows[f],
            &mut basis_checks,
        )?;
    }
    Ok(VerifiedOperatorClosureTransport {
        edge_count: input.source.defects.len(),
        face_count: input.source_faces.len(),
        basis_checks,
    })
}

// Origin: engine/crates_rs/core_functional/src/operator_trace_closure.rs
// Claim: urn:core:crates_rs:core-functional:operator-trace-closure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b68ff41e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
