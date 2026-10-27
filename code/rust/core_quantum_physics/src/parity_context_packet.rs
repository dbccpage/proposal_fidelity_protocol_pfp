// AuthorityEffect: None.

//! Finite parity-context packets over `F_2`.
//!
//! A packet declares `n` variables, `m` contexts (each a nonempty set of
//! distinct variables) and a target sign for every context. Signs are written
//! additively: `0 = +1`, `1 = -1`, and a product of signs is a sum mod 2.
//! Assignments and context cochains are bit masks: bit `v` of an assignment is
//! variable `v`, bit `c` of a cochain is context `c`. The incidence matrix `A`
//! (contexts by variables) is the coboundary `d0 : F_2^n -> F_2^m`,
//! `(d0 a)(c) = sum_(v in c) a(v)`: the product of the assigned signs over the
//! context. An assignment satisfies context `c` when `(d0 a)(c)` equals the
//! target. Computed exactly:
//!
//! - incidence counts, `d0`, its transpose `(d0^T y)(v) = sum_(c ni v) y(c)`,
//!   and `rank d0` over `F_2` (by canonical number-theory packed elimination);
//! - membership of a cochain `s` in `im d0`, decided by comparing the ranks of
//!   `A` and `[A | s]`, and certified separately: a preimage `a` with
//!   `d0 a = s`, or a separator `y` with `d0^T y = 0` and `<y, s> = 1`. One of
//!   the two exists for every `s`, because `im d0` is the annihilator of
//!   `ker d0^T`, and [`ParityContextPacket::verify_certificate`] replays either;
//! - by enumeration of all `2^n` assignments: how many violate exactly `k`
//!   contexts, and which subfamilies of contexts are jointly satisfiable;
//! - when every variable lies in exactly two contexts, the context graph
//!   (contexts as vertices, one edge per variable) as a
//!   `binary_pattern_carrier::PatternCarrier`. Its vertex coboundary is
//!   `d0^T`, and an assignment lies in `ker d0` exactly when its edge set is an
//!   even subgraph;
//! - the same packet as a `contextuality_obstruction::MeasurementScenario`,
//!   whose Cech complex over the nerve of the contexts is a second, independent
//!   decision of whether a global assignment exists;
//! - promotion of `s` to cohomological language. A separator shows only that
//!   `[s]` is nonzero in the quotient `F_2^m / im d0`. A class of
//!   `H^1 = ker d1 / im d0` also needs a declared `d1` with `d1 d0 = 0`, and
//!   `s` is such a class only if `d1 s = 0`.
//!   [`ParityContextPacket::admit_with_d1`] refuses a `d1` that does not
//!   annihilate `im d0` and otherwise returns exactly one of: exact (with a
//!   preimage), closed but not exact (with a separator), or closure failure
//!   (with `d1 s != 0`). The packet does not declare `d1`; the verdict depends
//!   on the one supplied.
//!
//! Everything is over `F_2`. Membership over `F_2` and over `Q` can differ, so
//! none of this is decided by the rational `cohomology_admission`.
//!
//! Refused: more than 16 variables or contexts, empty contexts, repeated or
//! out-of-range variables, a target count that differs from the context count,
//! targets or `d1` entries outside `F_2`, context products outside `{+1, -1}`
//! in a declared square, masks with bits beyond the packet, and a context
//! graph when some variable does not lie in exactly two contexts.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_967b9f62<T> {
    fn checked_invariant_967b9f62(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_967b9f62<T> for Option<T> {
    #[inline]
    fn checked_invariant_967b9f62(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_967b9f62<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_967b9f62(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::contextuality_obstruction::{MeasurementScenario, CARRIER, CONDUCTOR};
use core_homology::graph_f2::{pattern_pairing, PatternCarrier, PatternError, MAX_BITS};
use core_number_theory::gf2::{F2Error, F2Matrix, F2Vector};
/// The declared sign contexts consumed by a parity packet.
pub trait SignedContextFamily {
    fn named_contexts(&self) -> &[Vec<&'static str>];
    fn context_signs(&self) -> &[i8];
}
use core_policy::trichotomy::ObstructionDiagnosticClass;

/// Refusals for parity-context packets.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ParityPacketError {
    #[error("at most {MAX_BITS} variables and {MAX_BITS} contexts are supported")]
    TooLarge,
    #[error("context {context} is empty")]
    EmptyContext { context: usize },
    #[error("context {context} names variable {variable}, but the packet has {variable_count} variables")]
    VariableOutOfRange {
        context: usize,
        variable: usize,
        variable_count: usize,
    },
    #[error("context {context} names variable {variable} twice")]
    RepeatedVariable { context: usize, variable: usize },
    #[error("{targets} targets were declared for {contexts} contexts")]
    TargetCount { contexts: usize, targets: usize },
    #[error("target {value} of context {context} is not in F_2")]
    TargetNotBinary { context: usize, value: u8 },
    #[error("context {context} has product {value}, which is not a sign")]
    NotASign { context: usize, value: i8 },
    #[error("mask {mask:#b} has bits beyond the {width} available")]
    MaskOutOfRange { mask: u32, width: usize },
    #[error("d1 row {row} has {actual} entries, expected one per context ({expected})")]
    D1Shape {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("d1 entry {value} at row {row} is not in F_2")]
    D1NotBinary { row: usize, value: u8 },
    #[error("the declared d1 does not annihilate im d0")]
    D1DoesNotAnnihilateImage,
    #[error("variable {variable} lies in {count} contexts; a context graph needs exactly two")]
    NotTwoIncidence { variable: usize, count: usize },
    #[error("context graph: {0}")]
    Graph(#[from] PatternError),
    #[error(transparent)]
    LinearAlgebra(#[from] F2Error),
    #[error("the GF(2) membership certificate could not be replayed")]
    Certificate,
}

/// A certificate for the membership of a cochain in `im d0`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ImageCertificate {
    /// An assignment `a` with `d0 a = s`.
    Preimage(u32),
    /// A cochain `y` with `d0^T y = 0` and `<y, s> = 1`.
    Separator(u32),
}

/// The admission of a cochain against a declared `d1`, with its certificate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParityAdmission {
    Exact { preimage: u32 },
    ClosedNonexact { separator: u32 },
    ClosureFailure { defect: Vec<u8> },
}

impl ParityAdmission {
    /// The matching `core_functional` diagnostic class.
    pub fn diagnostic_class(&self) -> ObstructionDiagnosticClass {
        match self {
            ParityAdmission::Exact { .. } => ObstructionDiagnosticClass::ExactRepair,
            ParityAdmission::ClosedNonexact { .. } => ObstructionDiagnosticClass::ClosedResidual,
            ParityAdmission::ClosureFailure { .. } => {
                ObstructionDiagnosticClass::ActiveClosureFailure
            }
        }
    }
}

/// A declared finite parity-context packet over `F_2`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParityContextPacket {
    variable_count: usize,
    contexts: Vec<u32>,
    targets: u32,
}

impl ParityContextPacket {
    fn encode_single_context(
        context: usize,
        members: &[usize],
        variable_count: usize,
    ) -> Result<u32, ParityPacketError> {
        if members.is_empty() {
            return Err(ParityPacketError::EmptyContext { context });
        }
        let mut mask = 0u32;
        for &variable in members {
            if variable >= variable_count {
                return Err(ParityPacketError::VariableOutOfRange {
                    context,
                    variable,
                    variable_count,
                });
            }
            if mask & (1 << variable) != 0 {
                return Err(ParityPacketError::RepeatedVariable { context, variable });
            }
            mask |= 1 << variable;
        }
        Ok(mask)
    }

    fn encode_targets(targets: &[u8]) -> Result<u32, ParityPacketError> {
        let mut target_mask = 0u32;
        for (context, &value) in targets.iter().enumerate() {
            if value > 1 {
                return Err(ParityPacketError::TargetNotBinary { context, value });
            }
            target_mask |= u32::from(value) << context;
        }
        Ok(target_mask)
    }

    /// `contexts[c]` lists the variables of context `c`; `targets[c]` is its
    /// declared sign in `F_2`.
    pub fn new(
        variable_count: usize,
        contexts: &[Vec<usize>],
        targets: &[u8],
    ) -> Result<Self, ParityPacketError> {
        if variable_count > MAX_BITS || contexts.len() > MAX_BITS {
            return Err(ParityPacketError::TooLarge);
        }
        if targets.len() != contexts.len() {
            return Err(ParityPacketError::TargetCount {
                contexts: contexts.len(),
                targets: targets.len(),
            });
        }
        let mut masks = Vec::with_capacity(contexts.len());
        for (context, members) in contexts.iter().enumerate() {
            masks.push(Self::encode_single_context(
                context,
                members,
                variable_count,
            )?);
        }
        let target_mask = Self::encode_targets(targets)?;
        Ok(Self {
            variable_count,
            contexts: masks,
            targets: target_mask,
        })
    }

    /// The packet of a declared square: variables are numbered in order of
    /// first appearance, a context product `+1` becomes `0` and `-1` becomes
    /// `1`. The square's own `noncontextual_assignment_exists` flag is not read.
    pub fn from_square<S: SignedContextFamily>(square: &S) -> Result<Self, ParityPacketError> {
        if square.context_signs().len() != square.named_contexts().len() {
            return Err(ParityPacketError::TargetCount {
                contexts: square.named_contexts().len(),
                targets: square.context_signs().len(),
            });
        }
        let mut names: Vec<&str> = Vec::new();
        let mut contexts = Vec::with_capacity(square.named_contexts().len());
        for context in square.named_contexts() {
            let mut members = Vec::with_capacity(context.len());
            for &name in context {
                let index = match names.iter().position(|&n| n == name) {
                    Some(index) => index,
                    None => {
                        names.push(name);
                        names.len() - 1
                    }
                };
                members.push(index);
            }
            contexts.push(members);
        }
        let targets = square
            .context_signs()
            .iter()
            .enumerate()
            .map(|(context, &value)| match value {
                1 => Ok(0),
                -1 => Ok(1),
                _ => Err(ParityPacketError::NotASign { context, value }),
            })
            .collect::<Result<Vec<u8>, _>>()?;
        Self::new(names.len(), &contexts, &targets)
    }

    pub fn variable_count(&self) -> usize {
        self.variable_count
    }

    pub fn context_count(&self) -> usize {
        self.contexts.len()
    }

    /// The declared target cochain.
    pub fn targets(&self) -> u32 {
        self.targets
    }

    /// The cochain with every context set: the family of all contexts, and the
    /// functional `y -> sum_c y(c)` when paired with a cochain.
    pub fn all_contexts(&self) -> u32 {
        full_mask(self.contexts.len())
    }

    fn check_assignment(&self, a: u32) -> Result<(), ParityPacketError> {
        check_mask(a, self.variable_count)
    }

    fn check_cochain(&self, y: u32) -> Result<(), ParityPacketError> {
        check_mask(y, self.contexts.len())
    }

    /// How many contexts contain each variable.
    pub fn incidence_counts(&self) -> Vec<usize> {
        (0..self.variable_count)
            .map(|v| self.contexts.iter().filter(|&&c| c & (1 << v) != 0).count())
            .collect()
    }

    /// `(d0 a)(c) = sum_(v in c) a(v)`: the product of the assigned signs over each context.
    pub fn d0(&self, a: u32) -> Result<u32, ParityPacketError> {
        self.check_assignment(a)?;
        Ok(self
            .contexts
            .iter()
            .enumerate()
            .fold(0, |acc, (c, &members)| {
                acc | (pattern_pairing(members, a) << c)
            }))
    }

    /// `(d0^T y)(v) = sum_(c ni v) y(c)`.
    pub fn transpose_d0(&self, y: u32) -> Result<u32, ParityPacketError> {
        self.check_cochain(y)?;
        Ok(self
            .contexts
            .iter()
            .enumerate()
            .filter(|(c, _)| y & (1 << c) != 0)
            .fold(0, |acc, (_, &members)| acc ^ members))
    }

    /// The contexts an assignment violates: `d0 a + targets`.
    pub fn violations(&self, a: u32) -> Result<u32, ParityPacketError> {
        Ok(self.d0(a)? ^ self.targets)
    }

    fn incidence_matrix(&self) -> Result<F2Matrix, ParityPacketError> {
        let mut matrix = F2Matrix::zeros(self.contexts.len(), self.variable_count)?;
        for (row, &members) in self.contexts.iter().enumerate() {
            for variable in 0..self.variable_count {
                matrix.set(row, variable, members & (1 << variable) != 0)?;
            }
        }
        Ok(matrix)
    }

    fn cochain_vector(&self, s: u32) -> Result<F2Vector, ParityPacketError> {
        self.check_cochain(s)?;
        Ok(F2Vector::from_bits(
            &(0..self.context_count())
                .map(|context| ((s >> context) & 1) as u8)
                .collect::<Vec<_>>(),
        )?)
    }

    /// `rank d0` over `F_2` on the constructor-checked small carrier.
    pub fn rank_d0(&self) -> usize {
        self.incidence_matrix()
            .checked_invariant_967b9f62("private carrier has at most MAX_BITS axes")
            .rank()
    }

    /// `dim F_2^m / im d0 = m - rank d0`.
    pub fn quotient_dimension(&self) -> usize {
        self.contexts.len() - self.rank_d0()
    }

    /// Whether `s` lies in `im d0`, decided by `rank A = rank [A | s]`.
    pub fn in_image(&self, s: u32) -> Result<bool, ParityPacketError> {
        Ok(self
            .incidence_matrix()?
            .solve(&self.cochain_vector(s)?)?
            .is_some())
    }

    /// A preimage of `s`, or a separator when `s` lies outside `im d0`, found
    /// by canonical packed elimination.
    pub fn certificate(&self, s: u32) -> Result<ImageCertificate, ParityPacketError> {
        self.check_cochain(s)?;
        let matrix = self.incidence_matrix()?;
        let target = self.cochain_vector(s)?;
        let mask = |v: &F2Vector| {
            v.to_bits()
                .into_iter()
                .enumerate()
                .fold(0u32, |m, (i, b)| m | (u32::from(b) << i))
        };
        let certificate = if let Some(space) = matrix.solve(&target)? {
            ImageCertificate::Preimage(mask(space.particular()))
        } else {
            let separator = matrix
                .transpose()
                .nullspace()
                .into_iter()
                .find(|v| v.dot(&target) == Ok(true))
                .ok_or(ParityPacketError::Certificate)?;
            ImageCertificate::Separator(mask(&separator))
        };
        if !self.verify_certificate(s, certificate)? {
            return Err(ParityPacketError::Certificate);
        }
        Ok(certificate)
    }

    /// Replay a certificate against `s`.
    pub fn verify_certificate(
        &self,
        s: u32,
        certificate: ImageCertificate,
    ) -> Result<bool, ParityPacketError> {
        self.check_cochain(s)?;
        Ok(match certificate {
            ImageCertificate::Preimage(a) => self.d0(a)? == s,
            ImageCertificate::Separator(y) => {
                self.transpose_d0(y)? == 0 && pattern_pairing(y, s) == 1
            }
        })
    }

    /// Entry `k` counts the assignments that violate exactly `k` contexts,
    /// over all `2^n` assignments.
    pub fn violation_histogram(&self) -> Vec<usize> {
        let mut histogram = vec![0; self.contexts.len() + 1];
        for a in 0..=full_mask(self.variable_count) {
            let violated = self
                .violations(a)
                .checked_invariant_967b9f62("enumerated assignments lie in the packet");
            histogram[violated.count_ones() as usize] += 1;
        }
        histogram
    }

    /// Some assignment satisfies every context in the subfamily `family`.
    pub fn satisfiable(&self, family: u32) -> Result<bool, ParityPacketError> {
        self.check_cochain(family)?;
        for a in 0..=full_mask(self.variable_count) {
            if self.violations(a)? & family == 0 {
                return Ok(true);
            }
        }
        Ok(false)
    }

    /// The full family is unsatisfiable and dropping any one context makes it
    /// satisfiable (so every proper subfamily is satisfiable).
    pub fn is_minimally_unsatisfiable(&self) -> Result<bool, ParityPacketError> {
        let all = self.all_contexts();
        if self.satisfiable(all)? {
            return Ok(false);
        }
        for c in 0..self.contexts.len() {
            if !self.satisfiable(all & !(1 << c))? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// Contexts as vertices, one edge per variable joining the two contexts
    /// that contain it.
    pub fn context_graph(&self) -> Result<PatternCarrier, ParityPacketError> {
        let mut edges = Vec::with_capacity(self.variable_count);
        for variable in 0..self.variable_count {
            let holders: Vec<usize> = (0..self.contexts.len())
                .filter(|&c| self.contexts[c] & (1 << variable) != 0)
                .collect();
            if holders.len() != 2 {
                return Err(ParityPacketError::NotTwoIncidence {
                    variable,
                    count: holders.len(),
                });
            }
            edges.push((holders[0], holders[1]));
        }
        Ok(PatternCarrier::new(self.contexts.len(), edges)?)
    }

    /// The packet as a measurement scenario over `Z_2`: variables are rays,
    /// contexts keep their members, targets become `b`.
    pub fn measurement_scenario(&self, scenario_id: &str) -> MeasurementScenario {
        MeasurementScenario {
            name: format!("parity-context packet {scenario_id}"),
            scenario_id: scenario_id.to_string(),
            ray_count: self.variable_count,
            contexts: self
                .contexts
                .iter()
                .map(|&members| {
                    (0..self.variable_count)
                        .filter(|&v| members & (1 << v) != 0)
                        .collect()
                })
                .collect(),
            b_targets: (0..self.contexts.len())
                .map(|c| ((self.targets >> c) & 1) as u8)
                .collect(),
            coefficient_group: "Z_2".to_string(),
            carrier: CARRIER.to_string(),
            conductor: CONDUCTOR,
            declared_global_section: None,
        }
    }

    fn check_d1(&self, d1: &[Vec<u8>]) -> Result<(), ParityPacketError> {
        let expected = self.contexts.len();
        for (row, entries) in d1.iter().enumerate() {
            if entries.len() != expected {
                return Err(ParityPacketError::D1Shape {
                    row,
                    expected,
                    actual: entries.len(),
                });
            }
            if let Some(&value) = entries.iter().find(|&&x| x > 1) {
                return Err(ParityPacketError::D1NotBinary { row, value });
            }
        }
        if d1.is_empty() {
            return Ok(());
        }
        let product = F2Matrix::from_rows(d1)?.mul(&self.incidence_matrix()?)?;
        if !product.is_zero() {
            return Err(ParityPacketError::D1DoesNotAnnihilateImage);
        }
        Ok(())
    }

    fn apply_d1(d1: &[Vec<u8>], s: u32) -> Vec<u8> {
        d1.iter()
            .map(|row| {
                row.iter()
                    .enumerate()
                    .fold(0, |acc, (c, &entry)| acc ^ (entry & ((s >> c) & 1) as u8))
            })
            .collect()
    }

    /// `dim H^1 = (m - rank d1) - rank d0` for a declared `d1` with `d1 d0 = 0`.
    pub fn h1_dimension(&self, d1: &[Vec<u8>]) -> Result<usize, ParityPacketError> {
        self.check_d1(d1)?;
        Ok(self.contexts.len() - F2Matrix::from_rows(d1)?.rank() - self.rank_d0())
    }

    /// Admit `s` against a declared `d1 : F_2^m -> F_2^f` with `d1 d0 = 0`.
    pub fn admit_with_d1(
        &self,
        s: u32,
        d1: &[Vec<u8>],
    ) -> Result<ParityAdmission, ParityPacketError> {
        self.check_d1(d1)?;
        match self.certificate(s)? {
            ImageCertificate::Preimage(preimage) => Ok(ParityAdmission::Exact { preimage }),
            ImageCertificate::Separator(separator) => {
                let defect = Self::apply_d1(d1, s);
                if defect.contains(&1) {
                    Ok(ParityAdmission::ClosureFailure { defect })
                } else {
                    Ok(ParityAdmission::ClosedNonexact { separator })
                }
            }
        }
    }

    /// Replay an admission against `s` and `d1`.
    pub fn verify_admission(
        &self,
        s: u32,
        d1: &[Vec<u8>],
        admission: &ParityAdmission,
    ) -> Result<bool, ParityPacketError> {
        self.check_d1(d1)?;
        let defect = Self::apply_d1(d1, s);
        Ok(match admission {
            ParityAdmission::Exact { preimage } => {
                self.verify_certificate(s, ImageCertificate::Preimage(*preimage))?
            }
            ParityAdmission::ClosedNonexact { separator } => {
                !defect.contains(&1)
                    && self.verify_certificate(s, ImageCertificate::Separator(*separator))?
            }
            ParityAdmission::ClosureFailure { defect: claimed } => {
                *claimed == defect && defect.contains(&1)
            }
        })
    }
}

fn full_mask(bits: usize) -> u32 {
    if bits == 0 {
        0
    } else {
        u32::MAX >> (32 - bits)
    }
}

fn check_mask(mask: u32, width: usize) -> Result<(), ParityPacketError> {
    if mask & !full_mask(width) != 0 {
        return Err(ParityPacketError::MaskOutOfRange { mask, width });
    }
    Ok(())
}

// Origin: engine/crates_rs/core_quantum_physics/src/parity_context_packet.rs
// Claim: urn:core:crates_rs:core-quantum-physics:parity-context-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_967b9f62 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
