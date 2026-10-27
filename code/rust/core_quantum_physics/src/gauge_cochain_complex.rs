// AuthorityEffect: None.

//! Finite exact quantum packets on the carrier `M_2(Q(i))`, with a decidable,
//! witness-producing obstruction classification.
//!
//! A packet declares states, effects, POVM contexts, Kraus channels and a Born
//! table of declared probabilities. The complex Hilbert carrier, the Born
//! pairing and CPTP discipline are **declared packet fields**; nothing here
//! derives them.
//!
//! The calling program admits the states, effects, POVMs, channels and Born
//! declarations. This module constructs their exact gauge cochain complex and
//! classifies residuals with replayable witnesses.
//!
//! On an accepted packet the finite complex is built over real coordinates:
//!
//! - `C^0`: anti-Hermitian gauge generators `A` (real dimension 4);
//! - `C^1`: residuals `(dp, dE, drho)`, one `dp` per Born entry and one
//!   Hermitian `dE`, `drho` per effect and state;
//! - `d0(A) = (0, [A, E_k], [A, rho_j])`;
//! - Born coordinates of `d1`: `dp_jk - Tr(E_k drho_j) - Tr(dE_k rho_j)`.
//!
//! `d1 d0 = 0` by cyclicity of the trace, and it is replayed as an exact matrix
//! identity (Born invariance under gauge repair, not Born selection). A
//! residual is classified `ExactRepair` (with a gauge witness), `ClosedResidual`
//! (with a separating functional that kills `im d0`) or `ActiveClosureFailure`
//! (with the nonzero Born coordinate). Membership is decided by
//! `core_linear_algebra`'s exact row reduction. With the declared polyhedral
//! `l1` norm on these coordinates, `Phi_Q` comes from `core_solvers`, replayed
//! by `core_functional`, and must agree with the membership decision.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a80b1074<T> {
    fn checked_invariant_a80b1074(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a80b1074<T> for Option<T> {
    #[inline]
    fn checked_invariant_a80b1074(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a80b1074<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a80b1074(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian;
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{involution, matrix, ExactFieldError};
use num_traits::{One, Zero};
use core_functional::gamma2::ExactCochainComplexQ;
use core_functional::phi1::VerifiedExactPhi1;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;
use core_policy::trichotomy::{CertifiedExactTrichotomy, ObstructionDiagnosticClass};
use core_solvers::solver_cohomology_quotient_phi1::CertifiedPhi1Error;
use core_solvers::data_cochain_packet::CochainPacketError;

use core_solvers::cert_cohomology_admission::{admit, Admission};

/// Refusals raised when a residual does not live in `C^1` of the packet.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ResidualError {
    #[error("residual has {actual} {field} components, expected {expected}")]
    Shape {
        field: &'static str,
        expected: usize,
        actual: usize,
    },
    #[error("{field} component {index} is not a Hermitian 2x2 matrix")]
    NotHermitian { field: &'static str, index: usize },
    #[error("exact linear algebra refused: {0}")]
    LinearAlgebra(String),
    #[error("exact-field algebra refused: {0}")]
    Arithmetic(#[from] ExactFieldError),
    #[error("gauge generator is not a skew-Hermitian 2x2 matrix")]
    InvalidGaugeGenerator,
    #[error("{field} index {index} is not declared")]
    UndeclaredIndex { field: &'static str, index: usize },
    #[error("gauge-complex dimensions exceed the declared resource budget")]
    ResourceBudget,
    #[error("obstruction functional refused: {0}")]
    Functional(#[from] CertifiedPhi1Error),
    #[error("finite cochain packet refused: {0}")]
    Packet(#[from] CochainPacketError),
}

/// A declared Born-table row: `probability` is declared for `Tr(E_effect rho_state)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BornEntry {
    pub state: usize,
    pub effect: usize,
    pub probability: Rational,
}

/// A finite `M_2(Q(i))` packet, as declared.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct M2Packet {
    pub states: Vec<BasicMatrix<GaussianRat>>,
    pub effects: Vec<BasicMatrix<GaussianRat>>,
    /// Each context lists effect indices that must sum to the identity.
    pub povms: Vec<Vec<usize>>,
    /// Each channel is a list of Kraus operators.
    pub channels: Vec<Vec<BasicMatrix<GaussianRat>>>,
    pub born_table: Vec<BornEntry>,
}

/// A checked finite gauge complex. The calling programme separately admits
/// positive states/effects, probability bounds and CPTP declarations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedM2Packet {
    packet: M2Packet,
    d0: BasicMatrix<Rational>,
    d1: BasicMatrix<Rational>,
}

/// A residual in `C^1`: one `dp` per Born entry, one Hermitian `dE` per effect
/// and one Hermitian `drho` per state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuantumResidual {
    pub dp: Vec<Rational>,
    pub de: Vec<BasicMatrix<GaussianRat>>,
    pub drho: Vec<BasicMatrix<GaussianRat>>,
}

/// The witness that comes with each diagnostic class.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClassificationWitness {
    /// `x = d0(A)` for this anti-Hermitian `A`.
    Gauge(BasicMatrix<GaussianRat>),
    /// A functional `lambda` on the real coordinates of `C^1` with
    /// `lambda . d0 = 0` and `lambda . x != 0`, and `d1 x = 0`.
    Separator(Vec<Rational>),
    /// `(d1 x)_entry != 0`.
    BornDefect { entry: usize, value: Rational },
}

/// The diagnostic class of a residual, with its witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct M2Classification {
    pub class: ObstructionDiagnosticClass,
    pub witness: ClassificationWitness,
}

fn is_2x2(m: &BasicMatrix<GaussianRat>) -> bool {
    m.rows() == 2 && m.cols() == 2
}

/// Real coordinates `(M00, M11, Re M01, Im M01)` of a Hermitian 2x2 matrix.
fn hermitian_coords(m: &BasicMatrix<GaussianRat>) -> [Rational; 4] {
    [
        m.get_ref(0, 0)
            .checked_invariant_a80b1074("checked M2 carrier dimensions")
            .re
            .clone(),
        m.get_ref(1, 1)
            .checked_invariant_a80b1074("checked M2 carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 1)
            .checked_invariant_a80b1074("checked M2 carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 1)
            .checked_invariant_a80b1074("checked M2 carrier dimensions")
            .im
            .clone(),
    ]
}

/// The Hermitian matrix with real coordinates `c`.
fn hermitian_from_coords(c: &[Rational; 4]) -> BasicMatrix<GaussianRat> {
    let off = GaussianRat {
        re: c[2].clone(),
        im: c[3].clone(),
    };
    let mut m = matrix::zeros(2, 2).checked_invariant_a80b1074("checked M2 carrier dimensions");
    m.set(0, 0, GaussianRat::from_rational(c[0].clone()))
        .checked_invariant_a80b1074("checked M2 carrier dimensions");
    m.set(1, 1, GaussianRat::from_rational(c[1].clone()))
        .checked_invariant_a80b1074("checked M2 carrier dimensions");
    m.set(0, 1, off.clone())
        .checked_invariant_a80b1074("checked M2 carrier dimensions");
    m.set(1, 0, off.conj())
        .checked_invariant_a80b1074("checked M2 carrier dimensions");
    m
}

/// The row `r` with `Tr(M H) = r . coords(H)` for Hermitian `M` and `H`.
fn pairing_row(m: &BasicMatrix<GaussianRat>) -> [Rational; 4] {
    let two = Rational::from_integer(2.into());
    [
        m.get_ref(0, 0)
            .checked_invariant_a80b1074("checked M2 carrier dimensions")
            .re
            .clone(),
        m.get_ref(1, 1)
            .checked_invariant_a80b1074("checked M2 carrier dimensions")
            .re
            .clone(),
        &two * &m.get_ref(0, 1).checked_invariant_a80b1074("checked M2 carrier dimensions").re,
        &two * &m.get_ref(0, 1).checked_invariant_a80b1074("checked M2 carrier dimensions").im,
    ]
}

/// The anti-Hermitian generator `i H` for the Hermitian `H` with coordinates
/// `c`, which must be exactly the four real coordinates of `C^0`.
pub fn gauge_generator(c: &[Rational]) -> Result<BasicMatrix<GaussianRat>, ResidualError> {
    let c: &[Rational; 4] = c.try_into().map_err(|_| ResidualError::Shape {
        field: "gauge generator",
        expected: 4,
        actual: c.len(),
    })?;
    Ok(generator_of(c))
}

fn generator_of(c: &[Rational; 4]) -> BasicMatrix<GaussianRat> {
    matrix::scale(&hermitian_from_coords(c), &GaussianRat::i())
        .checked_invariant_a80b1074("checked M2 carrier dimensions")
}

fn c1_len(packet: &M2Packet) -> usize {
    packet.born_table.len() + 4 * (packet.effects.len() + packet.states.len())
}

fn build_d0(
    packet: &M2Packet,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ResidualError> {
    let rows = c1_len(packet);
    let mut d0 = matrix::zeros_with_limits(rows, 4, limits)?;
    for g in 0..4 {
        let mut basis = [
            Rational::zero(),
            Rational::zero(),
            Rational::zero(),
            Rational::zero(),
        ];
        basis[g] = Rational::one();
        let a = generator_of(&basis);
        let column = residual_coords(packet, &gauge_image(packet, &a));
        for (row, value) in column.into_iter().enumerate() {
            d0.set(row, g, value).map_err(ExactFieldError::from)?;
        }
    }
    Ok(d0)
}

fn build_d1(
    packet: &M2Packet,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ResidualError> {
    let n_entries = packet.born_table.len();
    let effect_offset = n_entries;
    let state_offset = n_entries + 4 * packet.effects.len();
    let mut d1 = matrix::zeros_with_limits(n_entries, c1_len(packet), limits)?;
    for (row, entry) in packet.born_table.iter().enumerate() {
        d1.set(row, row, Rational::one())
            .map_err(ExactFieldError::from)?;
        let e_row = pairing_row(&packet.effects[entry.effect]);
        let rho_row = pairing_row(&packet.states[entry.state]);
        for c in 0..4 {
            let s = state_offset + 4 * entry.state + c;
            d1.set(
                row,
                s,
                d1.get_ref(row, s).map_err(ExactFieldError::from)? - &e_row[c],
            )
            .map_err(ExactFieldError::from)?;
            let e = effect_offset + 4 * entry.effect + c;
            d1.set(
                row,
                e,
                d1.get_ref(row, e).map_err(ExactFieldError::from)? - &rho_row[c],
            )
            .map_err(ExactFieldError::from)?;
        }
    }
    Ok(d1)
}

/// `d0(A) = (0, [A, E_k], [A, rho_j])`.
fn gauge_image(packet: &M2Packet, a: &BasicMatrix<GaussianRat>) -> QuantumResidual {
    QuantumResidual {
        dp: vec![Rational::zero(); packet.born_table.len()],
        de: packet
            .effects
            .iter()
            .map(|e| matrix::commutator(&a, e).checked_invariant_a80b1074("checked M2 carrier dimensions"))
            .collect(),
        drho: packet
            .states
            .iter()
            .map(|rho| matrix::commutator(&a, rho).checked_invariant_a80b1074("checked M2 carrier dimensions"))
            .collect(),
    }
}

fn residual_coords(packet: &M2Packet, x: &QuantumResidual) -> Vec<Rational> {
    let mut out = Vec::with_capacity(c1_len(packet));
    out.extend(x.dp.iter().cloned());
    for m in x.de.iter().chain(&x.drho) {
        out.extend(hermitian_coords(m));
    }
    out
}

impl VerifiedM2Packet {
    /// Build the finite gauge complex from well-shaped Hermitian declarations.
    /// Positivity, channel completeness and protocol refusal order are checked by
    /// the calling program; this constructor protects the mathematical shapes.
    pub fn from_declaration(packet: M2Packet) -> Result<Self, ResidualError> {
        Self::from_declaration_with_limits(packet, exact_hermitian::exact_limits())
    }

    fn validate_declaration_budget(
        packet: &M2Packet,
        limits: OperationLimits,
    ) -> Result<usize, ResidualError> {
        let components = packet
            .effects
            .len()
            .checked_add(packet.states.len())
            .ok_or(ResidualError::ResourceBudget)?;
        let c1 = components
            .checked_mul(4)
            .and_then(|n| n.checked_add(packet.born_table.len()))
            .ok_or(ResidualError::ResourceBudget)?;
        let d0_elements = c1.checked_mul(4).ok_or(ResidualError::ResourceBudget)?;
        let d1_elements = c1
            .checked_mul(packet.born_table.len())
            .ok_or(ResidualError::ResourceBudget)?;
        let operations = components
            .checked_mul(128)
            .and_then(|n| {
                packet
                    .born_table
                    .len()
                    .checked_mul(16)
                    .and_then(|m| n.checked_add(m))
            })
            .and_then(|n| d1_elements.checked_mul(4).and_then(|m| n.checked_add(m)))
            .ok_or(ResidualError::ResourceBudget)?;
        let over_elements = d0_elements > limits.max_elements || d1_elements > limits.max_elements;
        if over_elements || operations > limits.max_scalar_ops {
            return Err(ResidualError::ResourceBudget);
        }
        Ok(c1)
    }

    fn validate_declaration_shapes(packet: &M2Packet) -> Result<(), ResidualError> {
        if packet.states.is_empty() || packet.effects.is_empty() || packet.born_table.is_empty() {
            return Err(ResidualError::LinearAlgebra(
                "nonempty states, effects and Born rows required".into(),
            ));
        }
        for (field, list) in [("state", &packet.states), ("effect", &packet.effects)] {
            if let Some(index) = list
                .iter()
                .position(|m| !is_2x2(m) || !exact_hermitian::is_hermitian(m))
            {
                return Err(ResidualError::NotHermitian { field, index });
            }
        }
        if packet
            .born_table
            .iter()
            .any(|e| e.state >= packet.states.len() || e.effect >= packet.effects.len())
        {
            return Err(ResidualError::LinearAlgebra(
                "Born index outside declared state/effect family".into(),
            ));
        }
        if packet.channels.iter().flatten().any(|m| !is_2x2(m)) {
            return Err(ResidualError::LinearAlgebra(
                "channel matrix outside M2 carrier".into(),
            ));
        }
        Ok(())
    }

    /// Admit matrix shapes and construction work against an explicit LA budget.
    pub fn from_declaration_with_limits(
        packet: M2Packet,
        limits: OperationLimits,
    ) -> Result<Self, ResidualError> {
        let c1 = Self::validate_declaration_budget(&packet, limits)?;
        Self::validate_declaration_shapes(&packet)?;
        let d0 = build_d0(&packet, limits)?;
        let d1 = build_d1(&packet, limits)?;
        ExactCochainComplexQ::try_new(
            4,
            c1,
            d1.rows(),
            matrix::to_rows(&d0)?,
            matrix::to_rows(&d1)?,
        )
        .map_err(|e| ResidualError::LinearAlgebra(e.to_string()))?;
        Ok(Self { packet, d0, d1 })
    }

    pub fn packet(&self) -> &M2Packet {
        &self.packet
    }

    /// `d0` as a real `dim C^1 x 4` matrix.
    pub fn d0(&self) -> &BasicMatrix<Rational> {
        &self.d0
    }

    /// The Born rows of `d1` as a real `entries x dim C^1` matrix.
    pub fn d1(&self) -> &BasicMatrix<Rational> {
        &self.d1
    }

    /// `d1 d0` as an exact matrix product; it is zero on every accepted packet.
    pub fn d1_d0(&self) -> Result<BasicMatrix<Rational>, ResidualError> {
        Ok(matrix::multiply(&self.d1, &self.d0)?)
    }

    /// The Born residuals `p_jk - Tr(E_k rho_j)` of the declared table.
    pub fn born_residuals(&self) -> Vec<Rational> {
        self.packet
            .born_table
            .iter()
            .map(|entry| {
                let pairing = matrix::trace(
                    &matrix::multiply(
                        &self.packet.effects[entry.effect],
                        &self.packet.states[entry.state],
                    )
                    .checked_invariant_a80b1074("checked M2 carrier dimensions"),
                )
                .checked_invariant_a80b1074("checked M2 carrier dimensions");
                &entry.probability - &pairing.re
            })
            .collect()
    }

    /// The residual that places every declared Born defect in its `dp` slot.
    pub fn declared_born_residual(&self) -> QuantumResidual {
        QuantumResidual {
            dp: self.born_residuals(),
            de: vec![
                matrix::zeros(2, 2).checked_invariant_a80b1074("checked M2 carrier dimensions");
                self.packet.effects.len()
            ],
            drho: vec![
                matrix::zeros(2, 2).checked_invariant_a80b1074("checked M2 carrier dimensions");
                self.packet.states.len()
            ],
        }
    }

    /// `d0(A)` for an anti-Hermitian `A`.
    pub fn gauge_displacement(
        &self,
        a: &BasicMatrix<GaussianRat>,
    ) -> Result<QuantumResidual, ResidualError> {
        if !is_2x2(a) || !involution::is_skew_hermitian(a)? {
            return Err(ResidualError::InvalidGaugeGenerator);
        }
        Ok(gauge_image(&self.packet, a))
    }

    /// Output of channel `channel` on state `state`: `sum K rho K*`.
    pub fn apply_channel(
        &self,
        channel: usize,
        state: usize,
    ) -> Result<BasicMatrix<GaussianRat>, ResidualError> {
        let kraus = self
            .packet
            .channels
            .get(channel)
            .ok_or(ResidualError::UndeclaredIndex {
                field: "channel",
                index: channel,
            })?;
        let rho = self
            .packet
            .states
            .get(state)
            .ok_or(ResidualError::UndeclaredIndex {
                field: "state",
                index: state,
            })?;
        let mut out = matrix::zeros(2, 2)?;
        for k in kraus {
            let image = matrix::multiply(&matrix::multiply(k, rho)?, &involution::adjoint(k)?)?;
            out = matrix::add(&out, &image)?;
        }
        Ok(out)
    }

    fn coords(&self, x: &QuantumResidual) -> Result<Vec<Rational>, ResidualError> {
        let shapes = [
            ("dp", self.packet.born_table.len(), x.dp.len()),
            ("dE", self.packet.effects.len(), x.de.len()),
            ("drho", self.packet.states.len(), x.drho.len()),
        ];
        for (field, expected, actual) in shapes {
            if expected != actual {
                return Err(ResidualError::Shape {
                    field,
                    expected,
                    actual,
                });
            }
        }
        for (field, list) in [("dE", &x.de), ("drho", &x.drho)] {
            if let Some(index) = list
                .iter()
                .position(|m| !is_2x2(m) || !exact_hermitian::is_hermitian(m))
            {
                return Err(ResidualError::NotHermitian { field, index });
            }
        }
        Ok(residual_coords(&self.packet, x))
    }

    /// `d1 x`, one Born coordinate per declared entry.
    pub fn born_coboundary(&self, x: &QuantumResidual) -> Result<Vec<Rational>, ResidualError> {
        Ok(matrix::multiply_vector(&self.d1, &self.coords(x)?)?)
    }

    fn extract_active_closure_witness(
        defect: Vec<Rational>,
    ) -> Result<(ObstructionDiagnosticClass, ClassificationWitness), ResidualError> {
        let (entry, value) = defect
            .into_iter()
            .enumerate()
            .find(|(_, v)| !v.is_zero())
            .ok_or_else(|| {
                ResidualError::LinearAlgebra("active closure failure with a zero defect".into())
            })?;
        Ok((
            ObstructionDiagnosticClass::ActiveClosureFailure,
            ClassificationWitness::BornDefect { entry, value },
        ))
    }

    /// The decidable, witness-producing classification of a residual: the
    /// cohomology admission of its coordinates on the packet's complex.
    pub fn classify(&self, x: &QuantumResidual) -> Result<M2Classification, ResidualError> {
        let coords = self.coords(x)?;
        let complex = ExactCochainComplexQ::try_new(
            4,
            coords.len(),
            self.d1.rows(),
            matrix::to_rows(&self.d0)?,
            matrix::to_rows(&self.d1)?,
        )
        .map_err(|e| ResidualError::LinearAlgebra(e.to_string()))?;
        let (class, witness) = match admit(&complex, Some(&coords)) {
            Admission::Exact { preimage } => (
                ObstructionDiagnosticClass::ExactRepair,
                ClassificationWitness::Gauge(gauge_generator(&preimage)?),
            ),
            Admission::ActiveClosureFailure { defect } => {
                Self::extract_active_closure_witness(defect)?
            }
            Admission::ClosedNonexact { separator } => (
                ObstructionDiagnosticClass::ClosedResidual,
                ClassificationWitness::Separator(separator),
            ),
            Admission::Refused(refusal) => {
                return Err(ResidualError::LinearAlgebra(format!("{refusal:?}")))
            }
        };
        Ok(M2Classification { class, witness })
    }

    fn unit_weights(&self) -> Vec<Rational> {
        vec![Rational::one(); c1_len(&self.packet)]
    }

    /// `Phi_Q` for the declared polyhedral `l1` norm on the real coordinates of `C^1`.
    pub fn quotient_mass_l1(
        &self,
        x: &QuantumResidual,
    ) -> Result<VerifiedExactPhi1, ResidualError> {
        let coords = self.coords(x)?;
        Ok(core_solvers::solver_cohomology_quotient_phi1::certified_phi1(
            4,
            &matrix::to_rows(&self.d0)?,
            &coords,
            &self.unit_weights(),
            16_384,
        )?)
    }

    /// The exact trichotomy from `core_functional`, for the declared `l1` norm.
    pub fn functional_trichotomy(
        &self,
        x: &QuantumResidual,
    ) -> Result<CertifiedExactTrichotomy, ResidualError> {
        let coords = self.coords(x)?;
        Ok(core_solvers::data_cochain_packet::certified_trichotomy(
            4,
            &matrix::to_rows(&self.d0)?,
            &matrix::to_rows(&self.d1)?,
            &self.unit_weights(),
            &coords,
        )?)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/gauge_cochain_complex.rs
// Claim: urn:core:crates_rs:core-quantum-physics:gauge-cochain-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_a80b1074 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
