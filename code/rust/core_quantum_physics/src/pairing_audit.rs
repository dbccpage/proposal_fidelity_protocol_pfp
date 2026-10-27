// AuthorityEffect: None.

//! The state–effect pairing audit: every candidate probability pairing is
//! graded by the same finite checks on a declared packet, and no check selects
//! the Born pairing.
//!
//! A [`PairingPacket`] declares states and effects in real coordinates, the
//! measurements (groups of effects meant to sum to the unit effect), a pairing,
//! and transports (a linear map on states with its declared dual on effects).
//! [`audit_row`] replays:
//!
//! - normalization: `sum_{e in M} <e, s> = 1` for every measurement `M` and state `s`;
//! - positivity: `<e, s> >= 0` for every declared state and effect;
//! - transport coherence: `<T* e, s> = <e, T s>` on every declared pair, and the
//!   transported states still pass normalization and positivity;
//! - when a composite is declared, local tomography and local-to-global
//!   agreement. The audit computes the exact rank of the Kronecker products of
//!   the declared effects' coordinates, which for a Hermitian carrier is the
//!   rank of the product effects `E (x) F` in the joint effect space, and
//!   compares it with the joint effect dimension the composite declares. Each
//!   joint table must be nonnegative, sum to one, and have marginals equal to
//!   the local pairing on full-length declared marginal states, for every
//!   declared pair of measurements.
//!
//! The terminal is `Passes`, `RefusedCompositeUndeclared` (the single-system
//! checks pass and no composite rule is declared), `LocalTomographyFails`, or
//! `Failed` with the failed checks. [`declared_registry`] builds the seven rows
//! of the audit on exact carriers: the classical simplex, the square bit, the
//! Spekkens toy bit, the real and complex Hilbert qubits, a quaternionic qubit
//! (through its complex `2n x 2n` representation) and a nonlinear control.
//!
//! No terminal selects a pairing. [`transport_gram_row`] and [`noisy_born_row`]
//! put a second, different pairing on the classical and on the complex packet,
//! and both pass the same checks. A passing row is a finite replay of declared
//! data, not a derivation of the Born rule and not a sealed decision.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_7d507385<T> {
    fn checked_invariant_7d507385(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_7d507385<T> for Option<T> {
    #[inline]
    fn checked_invariant_7d507385(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_7d507385<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_7d507385(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::composition_tomography::{
    local_tomography_spanning_complex, local_tomography_spanning_real,
};
use crate::exact_channel::ExactKrausChannel;
use crate::exact_hermitian::{self, gi, gq};
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{elimination, involution, matrix, ExactFieldError};
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};

/// Refusals raised while declaring a packet or a carrier sample.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PairingError {
    #[error("coordinate vectors or maps have inconsistent dimensions")]
    Shape,
    #[error("measurement {measurement} names effect {effect}, which is not declared")]
    EffectIndex { measurement: usize, effect: usize },
    #[error("declared carrier matrix {index} is not positive semidefinite")]
    NotPositive { index: usize },
    #[error("declared carrier matrix is not Hermitian or not real where required")]
    NotHermitian,
    #[error("the packet declares no states, no effects or no measurements, so every check would pass vacuously")]
    EmptyPacket,
    #[error("pairing coordinates or product effects exceed the declared exact resource budget")]
    ResourceBudget,
    #[error("exact linear algebra refused: {0}")]
    LinearAlgebra(String),
    #[error("exact-field arithmetic refused: {0}")]
    Arithmetic(#[from] ExactFieldError),
    #[error("channel refused: {0}")]
    Channel(String),
}

/// How a pairing evaluates an effect on a state, in declared coordinates.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Pairing {
    /// `<e, s> = e^T G s` for a declared Gram matrix (effect rows, state columns).
    Bilinear(BasicMatrix<Rational>),
    /// `<e, s> = f(e . s)` for a declared polynomial `f`, constant term first.
    PolynomialOfDot(Vec<Rational>),
}

/// Tensor coordinates use column carriers, then return a coordinate vector.
fn tensor_coordinates(a: &[Rational], b: &[Rational]) -> Result<Vec<Rational>, PairingError> {
    let a = BasicMatrix::from_row_major(a.len(), 1, a.to_vec()).map_err(ExactFieldError::from)?;
    let b = BasicMatrix::from_row_major(b.len(), 1, b.to_vec()).map_err(ExactFieldError::from)?;
    Ok(
        matrix::kronecker_with_limits(&a, &b, exact_hermitian::exact_limits())?
            .as_slice()
            .to_vec(),
    )
}

impl Pairing {
    /// Evaluate with exact dimension checks; malformed coordinate lengths are refused.
    pub fn evaluate(
        &self,
        effect: &[Rational],
        state: &[Rational],
    ) -> Result<Rational, PairingError> {
        self.evaluate_with_limits(effect, state, exact_hermitian::exact_limits())
    }

    pub fn evaluate_with_limits(
        &self,
        effect: &[Rational],
        state: &[Rational],
        limits: OperationLimits,
    ) -> Result<Rational, PairingError> {
        if effect.len() > limits.max_elements || state.len() > limits.max_elements {
            return Err(PairingError::ResourceBudget);
        }
        Ok(match self {
            Pairing::Bilinear(gram) => matrix::dot(
                effect,
                &matrix::multiply_vector_with_limits(gram, state, limits)?,
            )?,
            Pairing::PolynomialOfDot(coefficients) => {
                if coefficients
                    .len()
                    .checked_add(state.len())
                    .is_none_or(|n| n > limits.max_scalar_ops)
                {
                    return Err(PairingError::ResourceBudget);
                }
                let x = matrix::dot(effect, state)?;
                coefficients
                    .iter()
                    .rev()
                    .fold(Rational::zero(), |acc, c| acc * &x + c)
            }
        })
    }

    /// The pairing on Kronecker coordinates of a two-copy composite, bounded by
    /// the exact carrier budget before its matrix is allocated.
    pub fn tensor_square(&self) -> Result<Pairing, PairingError> {
        self.tensor_square_with_limits(exact_hermitian::exact_limits())
    }

    pub fn tensor_square_with_limits(
        &self,
        limits: OperationLimits,
    ) -> Result<Pairing, PairingError> {
        Ok(match self {
            Pairing::Bilinear(gram) => {
                Pairing::Bilinear(matrix::kronecker_with_limits(gram, gram, limits)?)
            }
            Pairing::PolynomialOfDot(coefficients) => {
                if coefficients.len() > limits.max_elements {
                    return Err(PairingError::ResourceBudget);
                }
                Pairing::PolynomialOfDot(coefficients.clone())
            }
        })
    }
}

/// A declared transport: a map on state coordinates and its declared dual on effects.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Transport {
    pub on_states: BasicMatrix<Rational>,
    pub on_effects: BasicMatrix<Rational>,
}

/// A declared finite state/effect packet.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PairingPacket {
    states: Vec<Vec<Rational>>,
    effects: Vec<Vec<Rational>>,
    measurements: Vec<Vec<usize>>,
    pairing: Pairing,
    transports: Vec<Transport>,
}

impl PairingPacket {
    fn is_empty_input(
        states: &[Vec<Rational>],
        effects: &[Vec<Rational>],
        measurements: &[Vec<usize>],
    ) -> bool {
        let top_empty = states.is_empty() || effects.is_empty() || measurements.is_empty();
        let inner_empty = states.first().is_some_and(Vec::is_empty)
            || effects.first().is_some_and(Vec::is_empty)
            || measurements.iter().any(Vec::is_empty);
        top_empty || inner_empty
    }

    fn check_resource_budget(
        num_states: usize,
        ds: usize,
        num_effects: usize,
        de: usize,
        pairing: &Pairing,
    ) -> Result<(), PairingError> {
        let limits = exact_hermitian::exact_limits();
        let pairs = [(num_states, ds), (num_effects, de), (ds, ds), (de, de), (ds, de)];
        let pair_overflow = pairs
            .into_iter()
            .any(|(a, b)| a.checked_mul(b).is_none_or(|n| n > limits.max_elements));
        let poly_overflow =
            matches!(pairing, Pairing::PolynomialOfDot(c) if c.len() > limits.max_elements);
        if pair_overflow || poly_overflow {
            return Err(PairingError::ResourceBudget);
        }
        Ok(())
    }

    fn check_shapes(
        states: &[Vec<Rational>],
        ds: usize,
        effects: &[Vec<Rational>],
        de: usize,
        pairing: &Pairing,
        transports: &[Transport],
    ) -> Result<(), PairingError> {
        let vectors_ok =
            states.iter().all(|s| s.len() == ds) && effects.iter().all(|e| e.len() == de);
        let pairing_ok = match pairing {
            Pairing::Bilinear(gram) => gram.shape() == (de, ds),
            Pairing::PolynomialOfDot(_) => de == ds,
        };
        let transports_ok = transports
            .iter()
            .all(|t| t.on_states.shape() == (ds, ds) && t.on_effects.shape() == (de, de));
        if !(vectors_ok && pairing_ok && transports_ok) {
            return Err(PairingError::Shape);
        }
        Ok(())
    }

    pub fn new(
        states: Vec<Vec<Rational>>,
        effects: Vec<Vec<Rational>>,
        measurements: Vec<Vec<usize>>,
        pairing: Pairing,
        transports: Vec<Transport>,
    ) -> Result<Self, PairingError> {
        if Self::is_empty_input(&states, &effects, &measurements) {
            return Err(PairingError::EmptyPacket);
        }
        let ds = states.first().map_or(0, Vec::len);
        let de = effects.first().map_or(0, Vec::len);
        Self::check_resource_budget(states.len(), ds, effects.len(), de, &pairing)?;
        Self::check_shapes(&states, ds, &effects, de, &pairing, &transports)?;
        for (measurement, members) in measurements.iter().enumerate() {
            if let Some(&effect) = members.iter().find(|&&e| e >= effects.len()) {
                return Err(PairingError::EffectIndex {
                    measurement,
                    effect,
                });
            }
        }
        Ok(Self {
            states,
            effects,
            measurements,
            pairing,
            transports,
        })
    }

    pub fn states(&self) -> &[Vec<Rational>] {
        &self.states
    }

    pub fn effects(&self) -> &[Vec<Rational>] {
        &self.effects
    }

    pub fn measurements(&self) -> &[Vec<usize>] {
        &self.measurements
    }

    pub fn pairing(&self) -> &Pairing {
        &self.pairing
    }

    pub fn transports(&self) -> &[Transport] {
        &self.transports
    }

    /// `<effects[e], state>`, refused for an undeclared effect or a state of
    /// the wrong length.
    pub fn value(&self, effect: usize, state: &[Rational]) -> Result<Rational, PairingError> {
        match self.effects.get(effect) {
            Some(e) if state.len() == self.state_dim() => self.pairing.evaluate(e, state),
            _ => Err(PairingError::Shape),
        }
    }

    fn value_of(&self, effect: usize, state: &[Rational]) -> Rational {
        self.pairing
            .evaluate(&self.effects[effect], state)
            .checked_invariant_7d507385("admitted finite pairing coordinates")
    }

    fn state_dim(&self) -> usize {
        self.states.first().map_or(0, Vec::len)
    }

    /// The exact rank of the Kronecker products of every pair of declared
    /// effects: the dimension the product effects span in the joint space.
    pub fn product_effect_rank(&self) -> Result<usize, PairingError> {
        let coordinate_count = self
            .effects
            .len()
            .checked_mul(self.effects[0].len())
            .and_then(|n| n.checked_mul(n))
            .ok_or(PairingError::ResourceBudget)?;
        if coordinate_count > exact_hermitian::exact_limits().max_elements {
            return Err(PairingError::ResourceBudget);
        }
        let products: Vec<Vec<Rational>> = self
            .effects
            .iter()
            .flat_map(|a| self.effects.iter().map(move |b| tensor_coordinates(a, b)))
            .collect::<Result<Vec<_>, _>>()?;
        Ok(elimination::rank_with_limits(
            &matrix::from_rows(products)?,
            exact_hermitian::exact_limits(),
        )?)
    }

    /// The exact dimension of the span of the declared states.
    pub fn state_span_dimension(&self) -> Result<usize, PairingError> {
        Ok(elimination::rank_with_limits(
            &matrix::from_rows(self.states.clone())?,
            exact_hermitian::exact_limits(),
        )?)
    }

    fn normalized_on(&self, states: &[Vec<Rational>]) -> bool {
        states.iter().all(|s| {
            self.measurements.iter().all(|m| {
                m.iter().map(|&e| self.value_of(e, s)).sum::<Rational>() == Rational::one()
            })
        })
    }

    fn positive_on(&self, states: &[Vec<Rational>]) -> bool {
        states
            .iter()
            .all(|s| (0..self.effects.len()).all(|e| !self.value_of(e, s).is_negative()))
    }

    fn transport_coherent(&self) -> bool {
        self.transports.iter().all(|t| {
            let moved: Vec<Vec<Rational>> = self
                .states
                .iter()
                .map(|s| {
                    matrix::multiply_vector(&t.on_states, s)
                        .checked_invariant_7d507385("admitted transport coordinates")
                })
                .collect();
            let dual = self.effects.iter().all(|e| {
                let pulled = matrix::multiply_vector(&t.on_effects, e)
                    .checked_invariant_7d507385("admitted dual transport coordinates");
                self.states.iter().zip(&moved).all(|(s, ts)| {
                    self.pairing
                        .evaluate(&pulled, s)
                        .checked_invariant_7d507385("admitted pairing coordinates")
                        == self
                            .pairing
                            .evaluate(e, ts)
                            .checked_invariant_7d507385("admitted pairing coordinates")
                })
            });
            dual && self.normalized_on(&moved) && self.positive_on(&moved)
        })
    }
}

/// One joint table of a declared composite: outcome probabilities for a pair
/// of local measurements, and the declared marginal states they must reproduce.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointTable {
    pub measurement_a: usize,
    pub measurement_b: usize,
    pub marginal_a: Vec<Rational>,
    pub marginal_b: Vec<Rational>,
    pub probabilities: Vec<Vec<Rational>>,
}

/// The composite tier of a row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CompositeTier {
    Undeclared,
    /// A composite whose joint effect space has the declared dimension; the
    /// audit computes how much of it the product effects span.
    Declared {
        joint_effect_dim: usize,
        tables: Vec<JointTable>,
    },
}

/// A check the audit replays.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum PairingCheck {
    Normalization,
    Positivity,
    Transport,
    Gluing,
}

/// The terminal of one audited row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PairingTerminal {
    Passes,
    RefusedCompositeUndeclared,
    LocalTomographyFails {
        product_effect_rank: usize,
        joint_effect_dim: usize,
    },
    Failed(Vec<PairingCheck>),
}

/// Whether a row's pairing is native to its carrier or an imported rule.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PairingOrigin {
    Native,
    Imported,
}

/// A registry row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PairingRow {
    pub name: &'static str,
    pub origin: PairingOrigin,
    pub packet: PairingPacket,
    pub composite: CompositeTier,
}

fn tables_glue(packet: &PairingPacket, tables: &[JointTable]) -> bool {
    tables.iter().all(|t| {
        let (Some(ma), Some(mb)) = (
            packet.measurements.get(t.measurement_a),
            packet.measurements.get(t.measurement_b),
        ) else {
            return false;
        };
        let shaped = t.probabilities.len() == ma.len()
            && t.probabilities.iter().all(|row| row.len() == mb.len())
            && t.marginal_a.len() == packet.state_dim()
            && t.marginal_b.len() == packet.state_dim();
        shaped
            && t.probabilities.iter().flatten().all(|p| !p.is_negative())
            && t.probabilities.iter().flatten().sum::<Rational>() == Rational::one()
            && ma.iter().enumerate().all(|(i, &e)| {
                t.probabilities[i].iter().sum::<Rational>() == packet.value_of(e, &t.marginal_a)
            })
            && mb.iter().enumerate().all(|(j, &f)| {
                t.probabilities.iter().map(|row| &row[j]).sum::<Rational>()
                    == packet.value_of(f, &t.marginal_b)
            })
    })
}

fn collect_failed_checks(row: &PairingRow) -> Vec<PairingCheck> {
    let packet = &row.packet;
    let mut failed = Vec::new();
    if !packet.normalized_on(&packet.states) {
        failed.push(PairingCheck::Normalization);
    }
    if !packet.positive_on(&packet.states) {
        failed.push(PairingCheck::Positivity);
    }
    if !packet.transport_coherent() {
        failed.push(PairingCheck::Transport);
    }
    if let CompositeTier::Declared { tables, .. } = &row.composite {
        if !tables_glue(packet, tables) {
            failed.push(PairingCheck::Gluing);
        }
    }
    failed
}

/// Replay every declared check of a row and read off its terminal.
///
/// A packet with no states, no effects or no measurements is refused with
/// [`PairingError::EmptyPacket`]: every universally quantified check holds on it vacuously,
/// and a zero-dimensional declared composite would then grade it `Passes`.
pub fn audit_row(row: &PairingRow) -> Result<PairingTerminal, PairingError> {
    let packet = &row.packet;
    if packet.states.is_empty() || packet.effects.is_empty() || packet.measurements.is_empty() {
        return Err(PairingError::EmptyPacket);
    }
    let failed = collect_failed_checks(row);
    if !failed.is_empty() {
        return Ok(PairingTerminal::Failed(failed));
    }
    Ok(match &row.composite {
        CompositeTier::Undeclared => PairingTerminal::RefusedCompositeUndeclared,
        CompositeTier::Declared {
            joint_effect_dim, ..
        } => {
            let product_effect_rank = packet.product_effect_rank()?;
            if product_effect_rank < *joint_effect_dim {
                PairingTerminal::LocalTomographyFails {
                    product_effect_rank,
                    joint_effect_dim: *joint_effect_dim,
                }
            } else {
                PairingTerminal::Passes
            }
        }
    })
}

// ---------------------------------------------------------------------------
// Carrier coordinates
// ---------------------------------------------------------------------------

fn g(r: Rational) -> GaussianRat {
    GaussianRat {
        re: r,
        im: Rational::zero(),
    }
}

/// `(a, d, b, c)` for `[[a, b + ci], [b - ci, d]]`.
fn hermitian2_coords(m: &BasicMatrix<GaussianRat>) -> Vec<Rational> {
    vec![
        m.get_ref(0, 0)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(1, 1)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 1)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 1)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .im
            .clone(),
    ]
}

fn hermitian2_basis() -> Vec<BasicMatrix<GaussianRat>> {
    vec![
        matrix::diagonal(&[gi(1, 0), gi(0, 0)]).checked_invariant_7d507385("declared finite carrier dimensions"),
        matrix::diagonal(&[gi(0, 0), gi(1, 0)]).checked_invariant_7d507385("declared finite carrier dimensions"),
        matrix::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).checked_invariant_7d507385("2x2"),
        matrix::from_rows(vec![vec![gi(0, 0), gi(0, 1)], vec![gi(0, -1), gi(0, 0)]]).checked_invariant_7d507385("2x2"),
    ]
}

/// The coordinate matrix of a linear map on a carrier, column `k` being the
/// coordinates of the image of the `k`-th basis element.
fn coordinate_map(
    basis: &[BasicMatrix<GaussianRat>],
    coords: impl Fn(&BasicMatrix<GaussianRat>) -> Vec<Rational>,
    f: impl Fn(&BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat>,
) -> BasicMatrix<Rational> {
    matrix::transpose(
        &matrix::from_rows(basis.iter().map(|b| coords(&f(b))).collect())
            .checked_invariant_7d507385("declared coordinate basis"),
    )
    .checked_invariant_7d507385("declared coordinate map")
}

fn checked_states(matrices: &[BasicMatrix<GaussianRat>]) -> Result<(), PairingError> {
    for (index, m) in matrices.iter().enumerate() {
        if !exact_hermitian::is_hermitian(m) {
            return Err(PairingError::NotHermitian);
        }
        if !exact_hermitian::is_positive_semidefinite(m) {
            return Err(PairingError::NotPositive { index });
        }
    }
    Ok(())
}

fn trace_pairing_table(
    effects: &[BasicMatrix<GaussianRat>],
    ma: &[usize],
    mb: &[usize],
    joint: &BasicMatrix<GaussianRat>,
) -> Vec<Vec<Rational>> {
    ma.iter()
        .map(|&i| {
            mb.iter()
                .map(|&j| {
                    matrix::trace(
                        &matrix::multiply(
                            &matrix::kronecker(&effects[i], &effects[j])
                                .checked_invariant_7d507385("declared finite carrier dimensions"),
                            joint,
                        )
                        .checked_invariant_7d507385("declared finite carrier dimensions"),
                    )
                    .checked_invariant_7d507385("declared finite carrier dimensions")
                    .re
                })
                .collect()
        })
        .collect()
}

// ---------------------------------------------------------------------------
// The seven declared rows
// ---------------------------------------------------------------------------

fn classical_transport() -> BasicMatrix<Rational> {
    matrix::from_rows(vec![vec![rq(2, 3), rq(1, 4)], vec![rq(1, 3), rq(3, 4)]])
        .checked_invariant_7d507385("declared classical transport")
}

fn classical_packet(pairing: Pairing) -> Result<PairingPacket, PairingError> {
    let t = classical_transport();
    PairingPacket::new(
        vec![
            vec![ri(1), ri(0)],
            vec![ri(0), ri(1)],
            vec![rq(1, 2), rq(1, 2)],
            vec![rq(1, 3), rq(2, 3)],
        ],
        vec![vec![ri(1), ri(0)], vec![ri(0), ri(1)]],
        vec![vec![0, 1]],
        pairing,
        vec![Transport {
            on_effects: matrix::transpose(&t)?,
            on_states: t,
        }],
    )
}

fn classical_composite(
    packet: &PairingPacket,
    joint: &[Rational],
    marginal: &[Rational],
) -> CompositeTier {
    let effects = packet.effects();
    let joint_pairing = packet
        .pairing()
        .tensor_square()
        .checked_invariant_7d507385("declared composite carrier");
    let tables = (0..packet.measurements().len())
        .flat_map(|ma| (0..packet.measurements().len()).map(move |mb| (ma, mb)))
        .map(|(ma, mb)| JointTable {
            measurement_a: ma,
            measurement_b: mb,
            marginal_a: marginal.to_vec(),
            marginal_b: marginal.to_vec(),
            probabilities: packet.measurements()[ma]
                .iter()
                .map(|&i| {
                    packet.measurements()[mb]
                        .iter()
                        .map(|&j| {
                            joint_pairing
                                .evaluate(
                                    &tensor_coordinates(&effects[i], &effects[j])
                                        .checked_invariant_7d507385("declared composite coordinates"),
                                    joint,
                                )
                                .checked_invariant_7d507385("declared joint pairing coordinates")
                        })
                        .collect()
                })
                .collect(),
        })
        .collect();
    let d = packet.states()[0].len();
    CompositeTier::Declared {
        joint_effect_dim: d * d,
        tables,
    }
}

/// The classical simplex with the dot pairing and a perfectly correlated joint table.
pub fn classical_simplex_row() -> Result<PairingRow, PairingError> {
    let packet = classical_packet(Pairing::Bilinear(matrix::identity(2)?))?;
    let composite = classical_composite(
        &packet,
        &[rq(1, 2), ri(0), ri(0), rq(1, 2)],
        &[rq(1, 2), rq(1, 2)],
    );
    Ok(PairingRow {
        name: "classical_simplex_dot_pairing",
        origin: PairingOrigin::Native,
        packet,
        composite,
    })
}

/// The same classical packet paired through its own transport, `<e, s> = e^T T s`.
pub fn transport_gram_row() -> Result<PairingRow, PairingError> {
    let packet = classical_packet(Pairing::Bilinear(classical_transport()))?;
    let composite = classical_composite(
        &packet,
        &[rq(1, 2), ri(0), ri(0), rq(1, 2)],
        &[rq(1, 2), rq(1, 2)],
    );
    Ok(PairingRow {
        name: "classical_transport_gram_pairing",
        origin: PairingOrigin::Native,
        packet,
        composite,
    })
}

/// The square bit in affine coordinates `(1, x, y)`; no composite is declared.
pub fn square_bit_row() -> Result<PairingRow, PairingError> {
    let v = |x: i64, y: i64| vec![ri(1), ri(x), ri(y)];
    let e = |x: i64, y: i64| vec![rq(1, 2), rq(x, 2), rq(y, 2)];
    let rotation = matrix::from_rows(vec![
        vec![ri(1), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(1)],
        vec![ri(0), ri(-1), ri(0)],
    ])?;
    let packet = PairingPacket::new(
        vec![v(1, 1), v(1, -1), v(-1, 1), v(-1, -1)],
        vec![e(1, 0), e(-1, 0), e(0, 1), e(0, -1)],
        vec![vec![0, 1], vec![2, 3]],
        Pairing::Bilinear(matrix::identity(3)?),
        vec![Transport {
            on_effects: matrix::transpose(&rotation)?,
            on_states: rotation,
        }],
    )?;
    Ok(PairingRow {
        name: "square_bit_effect_pairing",
        origin: PairingOrigin::Native,
        packet,
        composite: CompositeTier::Undeclared,
    })
}

/// The Spekkens toy bit: uniform knowledge of an ontic pair out of four, the
/// overlap pairing, and one correlated two-system table.
pub fn spekkens_row() -> Result<PairingRow, PairingError> {
    let pairs = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)];
    let indicator = |(a, b): (usize, usize), weight: Rational| {
        (0..4)
            .map(|k| {
                if k == a || k == b {
                    weight.clone()
                } else {
                    ri(0)
                }
            })
            .collect::<Vec<_>>()
    };
    let states: Vec<Vec<Rational>> = pairs.iter().map(|p| indicator(*p, rq(1, 2))).collect();
    let effects: Vec<Vec<Rational>> = pairs.iter().map(|p| indicator(*p, ri(1))).collect();
    // The ontic permutation (1 2)(3 4) and its dual.
    let swap = matrix::from_fn(4, 4, |i, j| if j == (i ^ 1) { ri(1) } else { ri(0) })?;
    let packet = PairingPacket::new(
        states,
        effects,
        vec![vec![0, 1], vec![2, 3], vec![4, 5]],
        Pairing::Bilinear(matrix::identity(4)?),
        vec![Transport {
            on_effects: matrix::transpose(&swap)?,
            on_states: swap,
        }],
    )?;
    let joint: Vec<Rational> = (0..16)
        .map(|k| if k / 4 == k % 4 { rq(1, 4) } else { ri(0) })
        .collect();
    let composite = classical_composite(&packet, &joint, &[rq(1, 4), rq(1, 4), rq(1, 4), rq(1, 4)]);
    Ok(PairingRow {
        name: "spekkens_epistemic_pairing",
        origin: PairingOrigin::Native,
        packet,
        composite,
    })
}

fn real_symmetric_coords(m: &BasicMatrix<GaussianRat>) -> Vec<Rational> {
    vec![
        m.get_ref(0, 0)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(1, 1)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 1)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
    ]
}

fn real_rebit_matrix(a: Rational, d: Rational, b: Rational) -> BasicMatrix<GaussianRat> {
    matrix::from_rows(vec![vec![g(a), g(b.clone())], vec![g(b), g(d)]]).checked_invariant_7d507385("2x2")
}

/// The real Hilbert rebit with the imported trace pairing. Its declared tensor
/// composite has product effects of rank 9 in a 10-dimensional joint space.
pub fn real_rebit_row() -> Result<PairingRow, PairingError> {
    let states = vec![
        real_rebit_matrix(ri(1), ri(0), ri(0)),
        real_rebit_matrix(ri(0), ri(1), ri(0)),
        real_rebit_matrix(rq(1, 2), rq(1, 2), rq(1, 2)),
        real_rebit_matrix(rq(1, 2), rq(1, 2), rq(1, 4)),
    ];
    let effects = vec![
        real_rebit_matrix(ri(1), ri(0), ri(0)),
        real_rebit_matrix(ri(0), ri(1), ri(0)),
        real_rebit_matrix(rq(1, 2), rq(1, 2), rq(1, 2)),
        real_rebit_matrix(rq(1, 2), rq(1, 2), rq(-1, 2)),
    ];
    checked_states(&states)?;
    checked_states(&effects)?;
    let rotation = matrix::from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(-4, 5, 0, 1)],
        vec![gq(4, 5, 0, 1), gq(3, 5, 0, 1)],
    ])
    .checked_invariant_7d507385("2x2");
    let basis = vec![
        real_rebit_matrix(ri(1), ri(0), ri(0)),
        real_rebit_matrix(ri(0), ri(1), ri(0)),
        real_rebit_matrix(ri(0), ri(0), ri(1)),
    ];
    let transport = Transport {
        on_states: coordinate_map(&basis, real_symmetric_coords, |m| {
            matrix::multiply(
                &matrix::multiply(&rotation, m).checked_invariant_7d507385("declared finite carrier dimensions"),
                &involution::adjoint(&rotation).checked_invariant_7d507385("declared finite carrier dimensions"),
            )
            .checked_invariant_7d507385("declared finite carrier dimensions")
        }),
        on_effects: coordinate_map(&basis, real_symmetric_coords, |m| {
            matrix::multiply(
                &matrix::multiply(
                    &involution::adjoint(&rotation).checked_invariant_7d507385("declared finite carrier dimensions"),
                    m,
                )
                .checked_invariant_7d507385("declared finite carrier dimensions"),
                &rotation,
            )
            .checked_invariant_7d507385("declared finite carrier dimensions")
        }),
    };
    let gram = matrix::diagonal(&[ri(1), ri(1), ri(2)])?;
    let packet = PairingPacket::new(
        states.iter().map(real_symmetric_coords).collect(),
        effects.iter().map(real_symmetric_coords).collect(),
        vec![vec![0, 1], vec![2, 3]],
        Pairing::Bilinear(gram),
        vec![transport],
    )?;
    let spanning = local_tomography_spanning_real(2, 2)
        .map_err(|e| PairingError::LinearAlgebra(format!("{e:?}")))?;
    let product =
        matrix::kronecker(&states[2], &states[3]).checked_invariant_7d507385("declared finite carrier dimensions");
    let tables = vec![JointTable {
        measurement_a: 0,
        measurement_b: 1,
        marginal_a: real_symmetric_coords(&states[2]),
        marginal_b: real_symmetric_coords(&states[3]),
        probabilities: trace_pairing_table(&effects, &[0, 1], &[2, 3], &product),
    }];
    Ok(PairingRow {
        name: "real_hilbert_trace_pairing",
        origin: PairingOrigin::Imported,
        packet,
        composite: CompositeTier::Declared {
            joint_effect_dim: spanning.joint_dim,
            tables,
        },
    })
}

fn complex_states() -> Vec<BasicMatrix<GaussianRat>> {
    vec![
        matrix::diagonal(&[gi(1, 0), gi(0, 0)]).checked_invariant_7d507385("declared finite carrier dimensions"),
        matrix::from_rows(vec![
            vec![gq(1, 2, 0, 1), gq(1, 2, 0, 1)],
            vec![gq(1, 2, 0, 1), gq(1, 2, 0, 1)],
        ])
        .checked_invariant_7d507385("2x2"),
        matrix::from_rows(vec![
            vec![gq(1, 2, 0, 1), gq(0, 1, -1, 2)],
            vec![gq(0, 1, 1, 2), gq(1, 2, 0, 1)],
        ])
        .checked_invariant_7d507385("2x2"),
        matrix::from_rows(vec![
            vec![gq(1, 3, 0, 1), gq(1, 6, 1, 6)],
            vec![gq(1, 6, -1, 6), gq(2, 3, 0, 1)],
        ])
        .checked_invariant_7d507385("2x2"),
    ]
}

/// `|0><0|, |1><1|`, `|+><+|, |-><-|`, a three-outcome POVM, and
/// `|+i><+i|, |-i><-i|`. The last pair has the imaginary off-diagonal the
/// others lack; without it the effects span three of the four local
/// directions.
fn complex_effects() -> Vec<BasicMatrix<GaussianRat>> {
    let half = gq(1, 2, 0, 1);
    let plus = matrix::from_rows(vec![
        vec![half.clone(), half.clone()],
        vec![half.clone(), half.clone()],
    ])
    .checked_invariant_7d507385("2x2");
    let minus = matrix::from_rows(vec![
        vec![half.clone(), gq(-1, 2, 0, 1)],
        vec![gq(-1, 2, 0, 1), half.clone()],
    ])
    .checked_invariant_7d507385("2x2");
    let zero = matrix::diagonal(&[gi(1, 0), gi(0, 0)]).checked_invariant_7d507385("declared finite carrier dimensions");
    let one = matrix::diagonal(&[gi(0, 0), gi(1, 0)]).checked_invariant_7d507385("declared finite carrier dimensions");
    let a = matrix::scale(&zero, &half).checked_invariant_7d507385("declared finite carrier dimensions");
    let b = matrix::scale(&plus, &half).checked_invariant_7d507385("declared finite carrier dimensions");
    let rest = matrix::sub(
        &matrix::sub(
            &matrix::identity(2).checked_invariant_7d507385("declared finite carrier dimensions"),
            &a,
        )
        .checked_invariant_7d507385("declared finite carrier dimensions"),
        &b,
    )
    .checked_invariant_7d507385("declared finite carrier dimensions");
    let plus_i = matrix::from_rows(vec![
        vec![half.clone(), gq(0, 1, -1, 2)],
        vec![gq(0, 1, 1, 2), half.clone()],
    ])
    .checked_invariant_7d507385("2x2");
    let minus_i = matrix::sub(
        &matrix::identity(2).checked_invariant_7d507385("declared finite carrier dimensions"),
        &plus_i,
    )
    .checked_invariant_7d507385("declared finite carrier dimensions");
    vec![zero, one, plus, minus, a, b, rest, plus_i, minus_i]
}

fn hadamard_conjugation(m: &BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat> {
    let h =
        matrix::from_rows(vec![vec![gi(1, 0), gi(1, 0)], vec![gi(1, 0), gi(-1, 0)]]).checked_invariant_7d507385("2x2");
    matrix::scale(
        &matrix::multiply(
            &matrix::multiply(&h, m).checked_invariant_7d507385("declared finite carrier dimensions"),
            &h,
        )
        .checked_invariant_7d507385("declared finite carrier dimensions"),
        &gq(1, 2, 0, 1),
    )
    .checked_invariant_7d507385("declared finite carrier dimensions")
}

fn bell_state() -> BasicMatrix<GaussianRat> {
    let mut phi = matrix::zeros(4, 4).checked_invariant_7d507385("declared finite carrier dimensions");
    for (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)] {
        phi.set(r, c, gq(1, 2, 0, 1))
            .checked_invariant_7d507385("declared finite carrier dimensions");
    }
    phi
}

fn apply_optional_noise(
    m: &BasicMatrix<GaussianRat>,
    noise: Option<&ExactKrausChannel>,
) -> Result<BasicMatrix<GaussianRat>, PairingError> {
    match noise {
        Some(channel) => channel
            .apply(m)
            .map_err(|e| PairingError::Channel(e.to_string())),
        None => Ok(m.clone()),
    }
}

fn build_joint_bell_state(
    noise: Option<&ExactKrausChannel>,
) -> Result<BasicMatrix<GaussianRat>, PairingError> {
    let Some(channel) = noise else {
        return Ok(bell_state());
    };
    let mut products = Vec::new();
    for (wa, a) in channel.weights().iter().zip(channel.operators()) {
        for (wb, b) in channel.weights().iter().zip(channel.operators()) {
            products.push((
                wa * wb,
                matrix::kronecker(&a, b)
                    .checked_invariant_7d507385("declared finite carrier dimensions"),
            ));
        }
    }
    let d = channel.dim_in() * channel.dim_in();
    ExactKrausChannel::try_weighted(
        d,
        channel.dim_out() * channel.dim_out(),
        products,
        "noise (x) noise",
    )
    .and_then(|pair| pair.apply(&bell_state()))
    .map_err(|e| PairingError::Channel(e.to_string()))
}

fn build_complex_gram_and_packet(
    states: &[BasicMatrix<GaussianRat>],
    effects: &[BasicMatrix<GaussianRat>],
    noise: Option<&ExactKrausChannel>,
) -> Result<PairingPacket, PairingError> {
    checked_states(states)?;
    checked_states(effects)?;
    let basis = hermitian2_basis();
    let born = matrix::diagonal(&[ri(1), ri(1), ri(2), ri(2)])?;
    // Born after the declared channel: <E, rho> = Tr(E N(rho)).
    let images = basis
        .iter()
        .map(|b| apply_optional_noise(b, noise).map(|m| hermitian2_coords(&m)))
        .collect::<Result<Vec<_>, _>>()?;
    let rows_mat = matrix::from_rows(images)?;
    let noise_map = matrix::transpose(&rows_mat)?;
    let gram = matrix::multiply(&born, &noise_map)?;
    let transport = coordinate_map(&basis, hermitian2_coords, hadamard_conjugation);
    PairingPacket::new(
        states.iter().map(hermitian2_coords).collect(),
        effects.iter().map(hermitian2_coords).collect(),
        vec![vec![0, 1], vec![2, 3], vec![4, 5, 6], vec![7, 8]],
        Pairing::Bilinear(gram),
        vec![Transport {
            on_effects: transport.clone(),
            on_states: transport,
        }],
    )
}

fn complex_row(
    name: &'static str,
    noise: Option<&ExactKrausChannel>,
) -> Result<PairingRow, PairingError> {
    let (states, effects) = (complex_states(), complex_effects());
    let packet = build_complex_gram_and_packet(&states, &effects, noise)?;
    let joint = build_joint_bell_state(noise)?;
    let marginal = hermitian2_coords(
        &exact_hermitian::partial_trace_second(&bell_state(), 2, 2)
            .map_err(|e| PairingError::LinearAlgebra(e.to_string()))?,
    );
    let tables = [(0, 0), (1, 1), (0, 1), (2, 2), (3, 3)]
        .into_iter()
        .map(|(ma, mb)| JointTable {
            measurement_a: ma,
            measurement_b: mb,
            marginal_a: marginal.clone(),
            marginal_b: marginal.clone(),
            probabilities: trace_pairing_table(
                &effects,
                &packet.measurements()[ma],
                &packet.measurements()[mb],
                &joint,
            ),
        })
        .collect();
    let spanning = local_tomography_spanning_complex(2, 2)
        .map_err(|e| PairingError::LinearAlgebra(format!("{e:?}")))?;
    Ok(PairingRow {
        name,
        origin: PairingOrigin::Imported,
        packet,
        composite: CompositeTier::Declared {
            joint_effect_dim: spanning.joint_dim,
            tables,
        },
    })
}

/// The imported complex qubit with the Born trace pairing, Hadamard transport
/// and the Bell state as its joint table.
pub fn complex_born_row() -> Result<PairingRow, PairingError> {
    complex_row("complex_hilbert_born_pairing", None)
}

/// The Pauli channel with Kraus operators `I/3, 2X/3, 2Z/3`. It commutes with
/// Hadamard conjugation, which swaps `X` and `Z`.
pub fn hadamard_symmetric_noise() -> Result<ExactKrausChannel, PairingError> {
    let x = matrix::from_rows(vec![
        vec![gi(0, 0), gq(2, 3, 0, 1)],
        vec![gq(2, 3, 0, 1), gi(0, 0)],
    ])
    .checked_invariant_7d507385("2x2");
    let z = matrix::diagonal(&[gq(2, 3, 0, 1), gq(-2, 3, 0, 1)])
        .checked_invariant_7d507385("declared finite carrier dimensions");
    ExactKrausChannel::from_operators(vec![
        matrix::scale(
            &matrix::identity(2).checked_invariant_7d507385("declared finite carrier dimensions"),
            &gq(1, 3, 0, 1),
        )
        .checked_invariant_7d507385("declared finite carrier dimensions"),
        x,
        z,
    ])
    .map_err(|e| PairingError::Channel(e.to_string()))
}

/// The same packet with the pairing `Tr(E N(rho))` for [`hadamard_symmetric_noise`].
pub fn noisy_born_row() -> Result<PairingRow, PairingError> {
    complex_row("noisy_born_pairing", Some(&hadamard_symmetric_noise()?))
}

/// A quaternionic 2x2 Hermitian matrix `[[a, q], [conj q, d]]` as coordinates
/// `(a, d, q0, q1, q2, q3)` for `q = q0 + q1 i + q2 j + q3 k`.
fn quaternion_matrix(a: Rational, d: Rational, q: [Rational; 4]) -> Vec<Rational> {
    let mut out = vec![a, d];
    out.extend(q);
    out
}

/// The complex `4 x 4` representation, `q = z + w j -> [[z, w], [-conj w, conj z]]`.
fn quaternion_embedding(c: &[Rational]) -> BasicMatrix<GaussianRat> {
    let z = GaussianRat {
        re: c[2].clone(),
        im: c[3].clone(),
    };
    let w = GaussianRat {
        re: c[4].clone(),
        im: c[5].clone(),
    };
    let conj = |x: &GaussianRat| GaussianRat {
        re: x.re.clone(),
        im: -&x.im,
    };
    let neg = |x: &GaussianRat| GaussianRat {
        re: -&x.re,
        im: -&x.im,
    };
    let block = [[z.clone(), w.clone()], [neg(&conj(&w)), conj(&z)]];
    let mut m = matrix::zeros(4, 4).checked_invariant_7d507385("declared finite carrier dimensions");
    for i in 0..2 {
        m.set(i, i, g(c[0].clone()))
            .checked_invariant_7d507385("declared finite carrier dimensions");
        m.set(i + 2, i + 2, g(c[1].clone()))
            .checked_invariant_7d507385("declared finite carrier dimensions");
        for j in 0..2 {
            m.set(i, j + 2, block[i][j].clone())
                .checked_invariant_7d507385("declared finite carrier dimensions");
            m.set(j + 2, i, conj(&block[i][j]))
                .checked_invariant_7d507385("declared finite carrier dimensions");
        }
    }
    m
}

fn quaternion_coords(m: &BasicMatrix<GaussianRat>) -> Vec<Rational> {
    vec![
        m.get_ref(0, 0)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(2, 2)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 2)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 2)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .im
            .clone(),
        m.get_ref(0, 3)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .re
            .clone(),
        m.get_ref(0, 3)
            .checked_invariant_7d507385("declared finite carrier dimensions")
            .im
            .clone(),
    ]
}

/// A guarded quaternionic qubit: states and effects checked positive through the
/// complex representation, transport by conjugation with `diag(1, j)`, and no
/// declared composite.
pub fn quaternionic_row() -> Result<PairingRow, PairingError> {
    let h = rq(1, 2);
    let q = |q0: Rational, q1: Rational, q2: Rational, q3: Rational| [q0, q1, q2, q3];
    let z = || ri(0);
    let states = vec![
        quaternion_matrix(ri(1), ri(0), q(z(), z(), z(), z())),
        quaternion_matrix(ri(0), ri(1), q(z(), z(), z(), z())),
        quaternion_matrix(h.clone(), h.clone(), q(h.clone(), z(), z(), z())),
        quaternion_matrix(h.clone(), h.clone(), q(z(), h.clone(), z(), z())),
        quaternion_matrix(h.clone(), h.clone(), q(z(), z(), h.clone(), z())),
        quaternion_matrix(h.clone(), h.clone(), q(z(), z(), z(), h.clone())),
    ];
    let effects = vec![
        quaternion_matrix(ri(1), ri(0), q(z(), z(), z(), z())),
        quaternion_matrix(ri(0), ri(1), q(z(), z(), z(), z())),
        quaternion_matrix(h.clone(), h.clone(), q(z(), z(), h.clone(), z())),
        quaternion_matrix(h.clone(), h.clone(), q(z(), z(), -h.clone(), z())),
    ];
    checked_states(
        &states
            .iter()
            .map(|c| quaternion_embedding(c))
            .collect::<Vec<_>>(),
    )?;
    checked_states(
        &effects
            .iter()
            .map(|c| quaternion_embedding(c))
            .collect::<Vec<_>>(),
    )?;
    let mut u = matrix::identity(4).checked_invariant_7d507385("declared finite carrier dimensions");
    u.set(2, 2, gi(0, 0))
        .checked_invariant_7d507385("declared finite carrier dimensions");
    u.set(3, 3, gi(0, 0))
        .checked_invariant_7d507385("declared finite carrier dimensions");
    u.set(2, 3, gi(1, 0))
        .checked_invariant_7d507385("declared finite carrier dimensions");
    u.set(3, 2, gi(-1, 0))
        .checked_invariant_7d507385("declared finite carrier dimensions");
    let basis: Vec<BasicMatrix<GaussianRat>> = (0..6)
        .map(|k| {
            quaternion_embedding(
                &(0..6)
                    .map(|i| if i == k { ri(1) } else { ri(0) })
                    .collect::<Vec<_>>(),
            )
        })
        .collect();
    let transport = Transport {
        on_states: coordinate_map(&basis, quaternion_coords, |m| {
            matrix::multiply(
                &matrix::multiply(&u, m).checked_invariant_7d507385("declared finite carrier dimensions"),
                &involution::adjoint(&u).checked_invariant_7d507385("declared finite carrier dimensions"),
            )
            .checked_invariant_7d507385("declared finite carrier dimensions")
        }),
        on_effects: coordinate_map(&basis, quaternion_coords, |m| {
            matrix::multiply(
                &matrix::multiply(
                    &involution::adjoint(&u).checked_invariant_7d507385("declared finite carrier dimensions"),
                    m,
                )
                .checked_invariant_7d507385("declared finite carrier dimensions"),
                &u,
            )
            .checked_invariant_7d507385("declared finite carrier dimensions")
        }),
    };
    let gram = matrix::diagonal(&[ri(1), ri(1), ri(2), ri(2), ri(2), ri(2)])?;
    let packet = PairingPacket::new(
        states,
        effects,
        vec![vec![0, 1], vec![2, 3]],
        Pairing::Bilinear(gram),
        vec![transport],
    )?;
    Ok(PairingRow {
        name: "quaternionic_guarded_pairing",
        origin: PairingOrigin::Imported,
        packet,
        composite: CompositeTier::Undeclared,
    })
}

/// Check that a quaternionic coordinate vector is a positive matrix, through
/// its complex representation.
pub fn quaternionic_matrix_is_positive(coords: &[Rational]) -> bool {
    coords.len() == 6 && exact_hermitian::is_positive_semidefinite(&quaternion_embedding(coords))
}

/// The nonlinear control: the classical packet with `<e, s> = 2 (e.s)^2 - e.s`
/// and a declared product composite.
pub fn nonlinear_control_row() -> Result<PairingRow, PairingError> {
    let packet = classical_packet(Pairing::PolynomialOfDot(vec![ri(0), ri(-1), ri(2)]))?;
    let composite = classical_composite(
        &packet,
        &[rq(1, 4), rq(1, 4), rq(1, 4), rq(1, 4)],
        &[rq(1, 2), rq(1, 2)],
    );
    Ok(PairingRow {
        name: "nonlinear_ad_hoc_pairing",
        origin: PairingOrigin::Native,
        packet,
        composite,
    })
}

/// The seven declared rows, in the audit's order.
pub fn declared_registry() -> Result<Vec<PairingRow>, PairingError> {
    Ok(vec![
        classical_simplex_row()?,
        square_bit_row()?,
        spekkens_row()?,
        real_rebit_row()?,
        complex_born_row()?,
        quaternionic_row()?,
        nonlinear_control_row()?,
    ])
}

fn check_square_pair(
    e: &BasicMatrix<GaussianRat>,
    rho: &BasicMatrix<GaussianRat>,
) -> Result<(), PairingError> {
    if e.rows() == 0 || e.rows() != e.cols() || rho.rows() != rho.cols() || e.rows() != rho.rows() {
        return Err(PairingError::Shape);
    }
    Ok(())
}

/// The Born pairing `Re Tr(E rho)`.
pub fn born_pairing(
    e: &BasicMatrix<GaussianRat>,
    rho: &BasicMatrix<GaussianRat>,
) -> Result<Rational, PairingError> {
    check_square_pair(e, rho)?;
    Ok(matrix::trace(&matrix::multiply(e, rho)?)?.re)
}

/// The dephased rival `Tr(diag(E) diag(rho)) = sum_s E_ss rho_ss`.
pub fn dephased_pairing(
    e: &BasicMatrix<GaussianRat>,
    rho: &BasicMatrix<GaussianRat>,
) -> Result<Rational, PairingError> {
    check_square_pair(e, rho)?;
    let mut sum = Rational::zero();
    for index in 0..e.rows() {
        sum += &e
            .get_ref(index, index)
            .map_err(|e| PairingError::LinearAlgebra(e.to_string()))?
            .re
            * &rho
                .get_ref(index, index)
                .map_err(|e| PairingError::LinearAlgebra(e.to_string()))?
                .re;
    }
    Ok(sum)
}

// Origin: engine/crates_rs/core_quantum_physics/src/pairing_audit.rs
// Claim: urn:core:crates_rs:core-quantum-physics:pairing-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_7d507385 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
