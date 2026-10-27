//! Exact certificates for the original finite Hermitian trace-gauge observer.
//! AuthorityEffect: None. Repairs are real linear perturbations, not states.
//! This checks supplied Q(i) primal/dual witnesses; it is not a spectral solver.
use crate::exact_channel::ExactKrausChannel;
use crate::exact_hermitian::{check_hermitian, hermitian_trace, square_dim};
use crate::exact_instrument::ExactDensityState;
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_rational::BigRational;
use num_traits::Zero;
use core_certifiers::operator_closure_certifier::{
    OperatorClosureCertificate, OperatorClosureTransportCertificate,
    OperatorClosureTransportVerifier, OperatorClosureVerifier,
};
use core_functional::operator_trace_closure::{
    self, is_canonical_rational as canonical, KrausMapInput, OperatorClosureTransportInput,
    OperatorClosureWitness, OperatorTraceError, TraceObserverInput, TraceRepairInput,
    OPERATOR_INPUT_MAX_RATIONAL_BITS,
};
use core_number_theory::cyclotomic::GaussianRat;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("operator observer refusal: {0}")]
pub struct OperatorObserverError(pub &'static str);
impl From<ExactFieldError> for OperatorObserverError {
    fn from(_: ExactFieldError) -> Self {
        Self("exact matrix algebra refused")
    }
}
impl From<MatrixError> for OperatorObserverError {
    fn from(_: MatrixError) -> Self {
        Self("matrix storage refused")
    }
}
impl From<OperatorTraceError> for OperatorObserverError {
    fn from(error: OperatorTraceError) -> Self {
        Self(error.0)
    }
}
fn hermitian(m: &BasicMatrix<GaussianRat>) -> Result<usize, OperatorObserverError> {
    if m.as_slice().iter().any(|z| {
        z.re.numer().bits() > OPERATOR_INPUT_MAX_RATIONAL_BITS
            || z.re.denom().bits() > OPERATOR_INPUT_MAX_RATIONAL_BITS
            || z.im.numer().bits() > OPERATOR_INPUT_MAX_RATIONAL_BITS
            || z.im.denom().bits() > OPERATOR_INPUT_MAX_RATIONAL_BITS
    }) {
        return Err(OperatorObserverError("rational bit limit exceeded"));
    }
    if m.as_slice()
        .iter()
        .any(|z| !canonical(&z.re) || !canonical(&z.im))
    {
        return Err(OperatorObserverError(
            "noncanonical rational or invalid denominator",
        ));
    }
    check_hermitian(m).map_err(|_| OperatorObserverError("malformed Hermitian operator"))?;
    square_dim(m).map_err(|_| OperatorObserverError("operator shape"))
}
fn trace(m: &BasicMatrix<GaussianRat>) -> Result<BigRational, OperatorObserverError> {
    hermitian_trace(m).map_err(|_| OperatorObserverError("Hermitian trace refused"))
}

/// The real span of the supplied generator columns is precisely the declared
/// repair image. Heterogeneous nonzero edge dimensions are supported.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperatorRepairProblem {
    pub defects: Vec<BasicMatrix<GaussianRat>>,
    pub repair_generators: Vec<Vec<BasicMatrix<GaussianRat>>>,
    /// J(h) = sum_e weights[e] * ||h_e||_1 / 2.
    pub weights: Vec<BigRational>,
}
impl OperatorRepairProblem {
    /// Borrow the canonical functional input without copying the operator data.
    pub fn as_functional_input(&self) -> TraceRepairInput<'_> {
        TraceRepairInput {
            defects: &self.defects,
            repair_generators: &self.repair_generators,
            weights: &self.weights,
        }
    }

    pub fn validate(&self) -> Result<(), OperatorObserverError> {
        self.as_functional_input().validate().map_err(Into::into)
    }
}

/// Untrusted payload. Verification replays every algebraic assertion.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceObserverWitness {
    pub repair_coefficients: Vec<BigRational>,
    pub residuals: Vec<BasicMatrix<GaussianRat>>,
    pub positive_parts: Vec<BasicMatrix<GaussianRat>>,
    pub negative_parts: Vec<BasicMatrix<GaussianRat>>,
    pub dual_observables: Vec<BasicMatrix<GaussianRat>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceObserverCertificate {
    pub obstruction: BigRational,
}

impl TraceObserverWitness {
    pub fn as_functional_input(&self) -> TraceObserverInput<'_> {
        TraceObserverInput {
            repair_coefficients: &self.repair_coefficients,
            residuals: &self.residuals,
            positive_parts: &self.positive_parts,
            negative_parts: &self.negative_parts,
            dual_observables: &self.dual_observables,
        }
    }

    pub fn verify(
        &self,
        problem: &OperatorRepairProblem,
    ) -> Result<TraceObserverCertificate, OperatorObserverError> {
        let value = operator_trace_closure::verify_trace_quotient(
            problem.as_functional_input(),
            self.as_functional_input(),
        )?;
        Ok(TraceObserverCertificate {
            obstruction: value.phi_q().clone(),
        })
    }
}

/// Original comparison r_{b,a}: operators at `to` map to operators at `from`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperatorComparison {
    pub from: usize,
    pub to: usize,
    pub channel: ExactKrausChannel,
}

fn validate_single_comparison_edge(
    states: &[ExactDensityState],
    edge: &OperatorComparison,
) -> Result<(), OperatorObserverError> {
    channel_input(&edge.channel).validate()?;
    if edge.from >= states.len()
        || edge.to >= states.len()
        || edge.channel.dim_in() != states[edge.to].dimension()
        || edge.channel.dim_out() != states[edge.from].dimension()
    {
        return Err(OperatorObserverError(
            "comparison incidence or channel carrier",
        ));
    }
    Ok(())
}

fn validate_states_and_comparisons(
    states: &[ExactDensityState],
    comparisons: &[OperatorComparison],
) -> Result<(), OperatorObserverError> {
    if states.is_empty() {
        return Err(OperatorObserverError("empty vertex carrier"));
    }
    for state in states {
        hermitian(state.matrix())?;
    }
    for edge in comparisons {
        validate_single_comparison_edge(states, edge)?;
    }
    Ok(())
}

fn transport_comparison_image(
    comparisons: &[OperatorComparison],
    fields: &[BasicMatrix<GaussianRat>],
) -> Result<Vec<BasicMatrix<GaussianRat>>, OperatorObserverError> {
    comparisons
        .iter()
        .map(|e| {
            let transported = e
                .channel
                .apply(&fields[e.to])
                .map_err(|_| OperatorObserverError("comparison transport"))?;
            Ok(mx::sub(&transported, &fields[e.from])?)
        })
        .collect()
}

fn validate_vertex_repair_field(
    states: &[ExactDensityState],
    fields: &[BasicMatrix<GaussianRat>],
) -> Result<(), OperatorObserverError> {
    if fields.len() != states.len() {
        return Err(OperatorObserverError("vertex repair shape"));
    }
    for (field, state) in fields.iter().zip(states) {
        if hermitian(field)? != state.dimension() || !trace(field)?.is_zero() {
            return Err(OperatorObserverError(
                "vertex repair must be traceless Hermitian; positivity is not required",
            ));
        }
    }
    Ok(())
}

/// Assemble actual delta(rho) and d0(Adm) from the original source fields.
/// A supplied vertex repair basis declares Adm; completeness is not invented.
pub fn operator_section_problem(
    states: &[ExactDensityState],
    comparisons: &[OperatorComparison],
    vertex_repair_basis: &[Vec<BasicMatrix<GaussianRat>>],
    weights: Vec<BigRational>,
) -> Result<OperatorRepairProblem, OperatorObserverError> {
    validate_states_and_comparisons(states, comparisons)?;
    let state_fields: Vec<_> = states.iter().map(|s| s.matrix().clone()).collect();
    let mut generators = Vec::new();
    for fields in vertex_repair_basis {
        validate_vertex_repair_field(states, fields)?;
        generators.push(transport_comparison_image(comparisons, fields)?);
    }
    let problem = OperatorRepairProblem {
        defects: transport_comparison_image(comparisons, &state_fields)?,
        repair_generators: generators,
        weights,
    };
    problem.validate()?;
    Ok(problem)
}

/// Paid comparison-channel transport: checks Lambda(im d0) subset im d0'.
/// Each source generator has an explicit destination-generator expansion.
/// With target weights <= source weights this supports quotient contraction under the declared assumptions.
pub fn verify_operator_repair_transport(
    source: &OperatorRepairProblem,
    target: &OperatorRepairProblem,
    edge_channels: &[ExactKrausChannel],
    generator_images: &[Vec<BigRational>],
) -> Result<(), OperatorObserverError> {
    let channels: Vec<_> = edge_channels.iter().map(channel_input).collect();
    operator_trace_closure::verify_operator_repair_map(
        source.as_functional_input(),
        target.as_functional_input(),
        &channels,
        generator_images,
    )
    .map_err(Into::into)
}

fn channel_input(channel: &ExactKrausChannel) -> KrausMapInput<'_> {
    KrausMapInput {
        dim_in: channel.dim_in(),
        dim_out: channel.dim_out(),
        weights: channel.weights(),
        operators: channel.operators(),
    }
}

/// A 2-cell complex with operator-valued defects and boundary operator d_1: C¹ → C².
///
/// Implements the signed-scalar, equal-face-stalk fragment of Paper 006
/// (GS-003) §7 and Technical Appendix:
/// Ω_2^Q([h]) := d_1 h,
/// Γ_2^Q([h]) := sum_f 1/2 ||(d_1 h)_f||_1,
/// R_cl^Q := Γ_2^Q / Φ_Q,
/// [`Self::certify_closure`] verifies the weighted closure bound
/// Γ_2^Q <= ||d_1|| Φ_Q; construction alone does not verify it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Operator2CellComplex {
    /// Each face is declared by its signed boundary edges: (edge_index, orientation_sign).
    pub faces: Vec<Vec<(usize, BigRational)>>,
}

impl Operator2CellComplex {
    pub fn new(faces: Vec<Vec<(usize, BigRational)>>) -> Self {
        Self { faces }
    }

    /// Validate actual edge carriers even when the repair family is empty.
    pub fn validate_for(
        &self,
        problem: &OperatorRepairProblem,
    ) -> Result<(), OperatorObserverError> {
        problem.validate()?;
        operator_trace_closure::validate_operator_faces(&self.faces, &problem.defects)
            .map_err(Into::into)
    }

    pub fn verify_chain_for(
        &self,
        problem: &OperatorRepairProblem,
    ) -> Result<(), OperatorObserverError> {
        operator_trace_closure::verify_operator_chain(problem.as_functional_input(), &self.faces)
            .map_err(Into::into)
    }

    pub fn boundary_norm(
        &self,
        problem: &OperatorRepairProblem,
    ) -> Result<BigRational, OperatorObserverError> {
        operator_trace_closure::operator_boundary_norm(problem.as_functional_input(), &self.faces)
            .map_err(Into::into)
    }

    /// Replay exact quotient optimality, the chain law, supplied face Jordan
    /// norms and the induced norm in sovereign owners. The sealed receipt is
    /// bound to these inputs and carries `AuthorityEffect::None`.
    pub fn certify_closure(
        &self,
        problem: &OperatorRepairProblem,
        trace_witness: &TraceObserverWitness,
        closure_witness: &OperatorClosureWitness,
    ) -> Result<OperatorClosureCertificate, OperatorObserverError> {
        OperatorClosureVerifier::verify(
            problem.as_functional_input(),
            &self.faces,
            trace_witness.as_functional_input(),
            closure_witness,
        )
        .map_err(Into::into)
    }

    /// Evaluates face boundary d_1(h) on face f.
    pub fn evaluate_face(
        &self,
        face_idx: usize,
        defects: &[BasicMatrix<GaussianRat>],
    ) -> Result<BasicMatrix<GaussianRat>, OperatorObserverError> {
        operator_trace_closure::evaluate_operator_face(&self.faces, face_idx, defects)
            .map_err(Into::into)
    }

    /// Verifies the d_1 d_0 = 0 condition against repair generators.
    pub fn verify_chain_complex_condition(
        &self,
        repair_generators: &[Vec<BasicMatrix<GaussianRat>>],
    ) -> Result<bool, OperatorObserverError> {
        operator_trace_closure::validate_face_declaration(&self.faces)?;
        for gen in repair_generators {
            for face_idx in 0..self.faces.len() {
                let face_val = self.evaluate_face(face_idx, gen)?;
                if face_val
                    .as_slice()
                    .iter()
                    .any(|z| !z.re.is_zero() || !z.im.is_zero())
                {
                    return Ok(false);
                }
            }
        }
        Ok(true)
    }
}

/// Verify both repair-image transport and the additional closure license
/// `Lambda2 d1 = d1' Lambda1` on complete traceless-Hermitian bases. Matching
/// the transported defect alone is insufficient. Edge and face indices pair
/// the two declared presentations; arbitrary reindexings require another map.
pub fn verify_operator_2cell_transport(
    source: &OperatorRepairProblem,
    source_complex: &Operator2CellComplex,
    target: &OperatorRepairProblem,
    target_complex: &Operator2CellComplex,
    edge_channels: &[ExactKrausChannel],
    face_channels: &[ExactKrausChannel],
    generator_images: &[Vec<BigRational>],
) -> Result<OperatorClosureTransportCertificate, OperatorObserverError> {
    let edges: Vec<_> = edge_channels.iter().map(channel_input).collect();
    let faces: Vec<_> = face_channels.iter().map(channel_input).collect();
    OperatorClosureTransportVerifier::verify(OperatorClosureTransportInput {
        source: source.as_functional_input(),
        target: target.as_functional_input(),
        source_faces: &source_complex.faces,
        target_faces: &target_complex.faces,
        edge_channels: &edges,
        face_channels: &faces,
        generator_images,
    })
    .map_err(Into::into)
}

// Origin: engine/crates_rs/core_quantum_physics/src/trace_observer_certificate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:trace-observer-certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::One;

    #[test]
    fn test_operator_2cell_boundary_evaluation() {
        let faces = vec![vec![
            (0, BigRational::one()),
            (1, BigRational::one()),
            (2, BigRational::one()),
        ]];
        let complex = Operator2CellComplex::new(faces);

        // 3 edges with 2x2 traceless Hermitian operators:
        // sigma_z, -sigma_z, 0
        let sz = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                GaussianRat::from_ints(1, 0),
                GaussianRat::from_ints(0, 0),
                GaussianRat::from_ints(0, 0),
                GaussianRat::from_ints(-1, 0),
            ],
        )
        .unwrap();

        let neg_sz = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                GaussianRat::from_ints(-1, 0),
                GaussianRat::from_ints(0, 0),
                GaussianRat::from_ints(0, 0),
                GaussianRat::from_ints(1, 0),
            ],
        )
        .unwrap();

        let zero = mx::zeros(2, 2).unwrap();

        let defects = vec![sz, neg_sz, zero];
        let face_val = complex
            .evaluate_face(0, &defects)
            .expect("face evaluation succeeds");

        assert!(face_val
            .as_slice()
            .iter()
            .all(|z| z.re.is_zero() && z.im.is_zero()));
    }
}
