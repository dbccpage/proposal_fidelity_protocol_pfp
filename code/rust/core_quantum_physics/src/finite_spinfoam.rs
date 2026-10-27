// AuthorityEffect: None.

//! Finite polynomial and parity models of QM_122's H023-H027 over `Z[zeta_12]`,
//! in the two versions the repository holds.
//!
//! - [`ModelVersion::Published`] follows the paper's Lean, retained in
//!   `projects/finite_qm/sources/122_finite_hilbert_boundary_from_primitive_difference/lean4/`
//!   (`H025_spinfoam_boundary_unitarity.lean`, `H027_pachner_master_constraint_finiteness.lean`).
//!   Every pair of admissible boundaries has transition `a(W)`, the 10j amplitude
//!   of the bulk, and the Pachner partition multiplies an amplitude by itself.
//!   The ledger rows QM-122-C57 to C64 describe this version.
//! - [`ModelVersion::Corrected`] follows `lean4/quantum_mechanics/H025SpinfoamBoundaryUnitarity.lean`
//!   and `H027PachnerMasterConstraintFiniteness.lean`: the transition is `a(W)`
//!   only from an admissible boundary to itself (the identity channel for the
//!   vacuum bulk), and the partition is `conj(a) (P a)`.
//!
//! On the eight admissible binary boundaries ([`ADMISSIBLE_BASIS`]) the published
//! transition matrix is `a(W)` times the all-ones matrix and is never unitary; the
//! corrected one is `a(W) I`, unitary exactly when `a(W)` is a unit.
//! [`adjoint_bulk`] is the Lean's orientation reversal, which realizes the
//! adjoint matrix. The corrected partition is a Hermitian norm: [`real_value`]
//! reads a real element of `Q(zeta_12)` as `x + y sqrt(3)`, so its sign is decided
//! exactly. These are finite models, not general spin-foam unitarity theorems.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c3ee6ebe<T> {
    fn checked_invariant_c3ee6ebe(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c3ee6ebe<T> for Option<T> {
    #[inline]
    fn checked_invariant_c3ee6ebe(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c3ee6ebe<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c3ee6ebe(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as iv, matrix as mx, ExactFieldError};
use num_traits::Zero;
use core_number_theory::cyclotomic::Cyc12;
use core_number_theory::cyclotomic_integer::{CyclotomicInteger as C, CyclotomicIntegerError};
use core_number_theory::quadratic::Quadratic;
use core_number_theory::rational::{ri, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpinFoamModelError {
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    Ring(#[from] CyclotomicIntegerError),
    #[error("invalid declared model input: {0}")]
    Input(String),
}
impl From<String> for SpinFoamModelError {
    fn from(s: String) -> Self {
        Self::Input(s)
    }
}
impl From<&str> for SpinFoamModelError {
    fn from(s: &str) -> Self {
        Self::Input(s.into())
    }
}
const TET: [[usize; 3]; 4] = [[0, 3, 1], [1, 4, 2], [2, 5, 0], [3, 4, 5]];
const SIMPLEX: [[usize; 4]; 5] = [
    [6, 7, 8, 9],
    [3, 4, 5, 9],
    [1, 2, 5, 8],
    [0, 2, 4, 7],
    [0, 1, 3, 6],
];

/// Which version of the H025 and H027 definitions a computation follows.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ModelVersion {
    /// The paper's Lean as published; the version the ledger rows describe.
    Published,
    /// The corrected Lean in `lean4/quantum_mechanics/`.
    Corrected,
}

/// The eight admissible binary four-spin boundaries, in the order of the
/// corrected Lean's `admissibleBasis8`.
pub const ADMISSIBLE_BASIS: [[u32; 4]; 8] = [
    [0, 0, 0, 0],
    [1, 1, 0, 0],
    [1, 0, 1, 0],
    [1, 0, 0, 1],
    [0, 1, 1, 0],
    [0, 1, 0, 1],
    [0, 0, 1, 1],
    [1, 1, 1, 1],
];

pub fn quantum_integer(n: usize) -> C {
    let value = core_number_theory::cyclotomic_field::quantum_integer(12, n as i64)
        .checked_invariant_c3ee6ebe("fixed q-number budget");
    C::new(12, value.coefficients().to_vec())
        .checked_invariant_c3ee6ebe("q-integer has integral cyclotomic coordinates")
}
fn amplitude<const N: usize>(s: &[u32], faces: &[[usize; N]]) -> C {
    let mut a = C::scalar(12, 1).checked_invariant_c3ee6ebe("fixed valid conductor");
    let z = C::zeta(12).checked_invariant_c3ee6ebe("checked invariant");
    for f in faces {
        let sum: u64 = f.iter().map(|&i| u64::from(s[i])).sum();
        if sum % 2 != 0 {
            return C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor");
        }
        a = a.mul(&z.pow(((sum * 3) % 12) as usize)).checked_invariant_c3ee6ebe("checked invariant");
    }
    a
}
pub fn tetrahedron(s: &[u32; 6]) -> C {
    amplitude(s, &TET)
}
/// The 10j vertex amplitude `a(W)` of a bulk 4-simplex, the Lean's `amplitude10j`.
pub fn simplex4(s: &[u32; 10]) -> C {
    amplitude(s, &SIMPLEX)
}
pub fn admissible(s: &[u32]) -> bool {
    s.iter().fold(0u32, |parity, s| parity ^ (s & 1)) == 0
}

/// The orientation-reversed bulk, the Lean's `orientReverse4`: faces `012, 013,
/// 014` and `234` stay, and `023, 024, 034` trade places with `123, 124, 134`.
pub fn adjoint_bulk(bulk: &[u32; 10]) -> [u32; 10] {
    [
        bulk[0], bulk[1], bulk[2], bulk[6], bulk[7], bulk[8], bulk[3], bulk[4], bulk[5], bulk[9],
    ]
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryState {
    pub spins: [u32; 4],
    pub amplitude: C,
}
impl BoundaryState {
    pub fn inner_product(&self, b: &Self) -> Result<C, SpinFoamModelError> {
        if self.spins == b.spins && admissible(&self.spins) {
            Ok(self.amplitude.conj().mul(&b.amplitude)?)
        } else {
            Ok(C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor"))
        }
    }
    pub fn master(&self) -> Self {
        Self {
            spins: self.spins,
            amplitude: if admissible(&self.spins) {
                C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor")
            } else {
                self.amplitude.clone()
            },
        }
    }
    pub fn projector(&self) -> Self {
        Self {
            spins: self.spins,
            amplitude: if admissible(&self.spins) {
                self.amplitude.clone()
            } else {
                C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor")
            },
        }
    }
    /// The diagonal evolution `<s| W |s> a` of the Lean's `evolveState`. The
    /// diagonal is the same in both versions.
    pub fn evolve(&self, bulk: &[u32; 10]) -> Result<Self, SpinFoamModelError> {
        Ok(Self {
            spins: self.spins,
            amplitude: transition(ModelVersion::Published, &self.spins, &self.spins, bulk)
                .mul(&self.amplitude)?,
        })
    }
}

/// Whether a version lets `input` reach `output`: published, whenever both are
/// admissible; corrected, only an admissible boundary to itself.
fn connected(version: ModelVersion, input: &[u32; 4], output: &[u32; 4]) -> bool {
    match version {
        ModelVersion::Published => admissible(input) && admissible(output),
        ModelVersion::Corrected => input == output && admissible(input),
    }
}

/// `<output| W |input>` for the bulk `W`: `a(W)` when the version connects the
/// two boundaries, and zero otherwise.
pub fn transition(
    version: ModelVersion,
    input: &[u32; 4],
    output: &[u32; 4],
    bulk: &[u32; 10],
) -> C {
    if connected(version, input, output) {
        simplex4(bulk)
    } else {
        C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor")
    }
}

/// The fixed admissible boundary matrix, on the canonical static Q(zeta_12)
/// field. Runtime integral amplitudes cross the model boundary by coefficient
/// conversion only; matrix arithmetic belongs to linear algebra.
pub fn transition_matrix(version: ModelVersion, bulk: &[u32; 10]) -> BasicMatrix<Cyc12> {
    let amplitude = simplex4(bulk);
    let a = Cyc12 {
        a: std::array::from_fn(|i| {
            amplitude
                .coefficient_values()
                .get(i)
                .cloned()
                .unwrap_or_else(Rational::zero)
        }),
    };
    mx::from_fn(8, 8, |r, c| {
        if connected(version, &ADMISSIBLE_BASIS[c], &ADMISSIBLE_BASIS[r]) {
            a.clone()
        } else {
            Cyc12::zero()
        }
    })
    .checked_invariant_c3ee6ebe("fixed eight-boundary carrier")
}

/// and `c1 = -2 c3`, and then it is `c0 + (c1/2) sqrt(3)`.
pub fn real_value(z: &C) -> Result<Option<Quadratic<3>>, SpinFoamModelError> {
    if z.conductor() != 12 {
        return Err("CONDUCTOR_12_REQUIRED".into());
    }
    let mut c = z.coefficient_values().to_vec();
    c.resize(4, Rational::zero());
    if !c[2].is_zero() || c[1] != -(&c[3] * ri(2)) {
        return Ok(None);
    }
    Ok(Some(Quadratic::<3>::new(c[0].clone(), &c[1] / ri(2))))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PachnerState {
    pub external: [u32; 6],
    pub internal: Vec<u32>,
    pub amplitude: C,
}
impl PachnerState {
    pub fn projector(&self) -> Self {
        let mut r = self.clone();
        if !admissible(&r.external) {
            r.amplitude = C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor")
        }
        r
    }
    pub fn two_to_three(&self) -> Result<Self, SpinFoamModelError> {
        if self.internal.len() != 1 {
            return Err("PACHNER_REQUIRES_TWO_TETRAHEDRA".into());
        }
        Ok(Self {
            external: self.external,
            internal: vec![self.internal[0], 0, 0],
            amplitude: self.amplitude.clone(),
        })
    }
    /// The H027 partition `Z(psi)`. Published: `a (P a)`, a bilinear product
    /// without conjugation, so amplitude `i` gives `-1` and it is not a norm.
    /// Corrected: `conj(a) (P a)`, the Hermitian norm of the projected state.
    pub fn partition(&self, version: ModelVersion) -> Result<C, SpinFoamModelError> {
        let projected = self.projector().amplitude;
        Ok(match version {
            ModelVersion::Published => self.amplitude.mul(&projected)?,
            ModelVersion::Corrected => self.amplitude.conj().mul(&projected)?,
        })
    }
}
fn combinations(n: usize, k: usize) -> Vec<Vec<usize>> {
    core_combinatorics::enumeration::combinations(n, k, 64).checked_invariant_c3ee6ebe("fixed simplex face budget")
}
pub fn sphere_partition(spins: &[u32; 20]) -> C {
    let faces = combinations(6, 3);
    let cells = combinations(6, 5);
    cells.iter().fold(
        C::scalar(12, 1).checked_invariant_c3ee6ebe("fixed valid conductor"),
        |a, cell| {
            let triples = combinations(5, 3);
            let mut s = [0; 10];
            for (i, t) in triples.iter().enumerate() {
                let f: Vec<_> = t.iter().map(|&j| cell[j]).collect();
                s[i] = spins[faces.iter().position(|v| *v == f).checked_invariant_c3ee6ebe("checked invariant")];
            }
            a.mul(&simplex4(&s)).checked_invariant_c3ee6ebe("checked invariant")
        },
    )
}

/// Alternating face count of the boundary of a 5-simplex, the declared sphere.
pub fn sphere_euler() -> i64 {
    (1..=5)
        .map(|k| {
            let count = combinations(6, k).len() as i64;
            if k % 2 == 1 {
                count
            } else {
                -count
            }
        })
        .sum()
}

/// Exact census of the declared binary spin-foam model at `level` in `2..=3`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SpinFoamCensus {
    pub level: usize,
    pub tetrahedra_checked: usize,
    pub simplices_checked: usize,
    pub admissible_tetrahedra: usize,
    pub admissible_simplices: usize,
    pub sphere_euler: i64,
    pub q2_square_three: bool,
    pub q6_zero: bool,
    pub tetra_orientation: bool,
    pub simplex_symmetries: bool,
    pub boundary_projector: bool,
    pub master_self_adjoint_on_basis: bool,
    pub diagonal_evolution_projector: bool,
    pub pachner_intertwining: bool,
    pub sphere_euler_two: bool,
    pub sphere_vacuum_partition: bool,
    pub corrected_vacuum_transition_unitary: bool,
    pub corrected_partition_unit_norm_and_pachner_invariance: bool,
}

impl SpinFoamCensus {
    pub fn checks_hold(&self) -> bool {
        [
            self.q2_square_three,
            self.q6_zero,
            self.tetra_orientation,
            self.simplex_symmetries,
            self.boundary_projector,
            self.master_self_adjoint_on_basis,
            self.diagonal_evolution_projector,
            self.pachner_intertwining,
            self.sphere_euler_two,
            self.sphere_vacuum_partition,
            self.corrected_vacuum_transition_unitary,
            self.corrected_partition_unit_norm_and_pachner_invariance,
        ]
        .into_iter()
        .all(|b| b)
    }
}

fn census_tetrahedra(level: usize) -> (bool, usize) {
    let mut tetra_sym = true;
    let mut admissible_tets = 0;
    let zero = C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor");
    for code in 0..level.pow(6) {
        let mut m = code;
        let mut s = [0; 6];
        for x in &mut s {
            *x = (m % level) as u32;
            m /= level
        }
        let a = tetrahedron(&s);
        let r = [s[1], s[0], s[2], s[3], s[5], s[4]];
        tetra_sym &= tetrahedron(&r) == a.conj();
        admissible_tets += usize::from(a != zero);
    }
    (tetra_sym, admissible_tets)
}

fn census_simplices(level: usize) -> (bool, usize) {
    let mut simplex_sym = true;
    let mut admissible_cells = 0;
    let zero = C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor");
    for code in 0..level.pow(10) {
        let mut m = code;
        let mut s = [0; 10];
        for x in &mut s {
            *x = (m % level) as u32;
            m /= level
        }
        let a = simplex4(&s);
        let c = [s[6], s[7], s[0], s[8], s[1], s[2], s[9], s[3], s[4], s[5]];
        simplex_sym &= simplex4(&adjoint_bulk(&s)) == a.conj() && simplex4(&c) == a;
        admissible_cells += usize::from(a != zero);
    }
    (simplex_sym, admissible_cells)
}

fn census_boundary_states(z: &C) -> Result<(bool, bool, bool), SpinFoamModelError> {
    let mut projector = true;
    let mut adjoint = true;
    let mut duality = true;
    for code in 0..16 {
        let spins = std::array::from_fn(|i| ((code >> i) & 1) as u32);
        let b = BoundaryState {
            spins,
            amplitude: z.pow(code),
        };
        projector &= b.projector().projector() == b.projector();
        duality &= b.evolve(&[0; 10])? == b.projector();
        adjoint &= b.inner_product(&b.master())? == b.master().inner_product(&b)?;
    }
    Ok((projector, adjoint, duality))
}

fn census_pachner_states(z: &C) -> Result<(bool, bool), SpinFoamModelError> {
    let mut pachner = true;
    let mut corrected_pachner = true;
    for code in 0..64 {
        let b = PachnerState {
            external: std::array::from_fn(|i| ((code >> i) & 1) as u32),
            internal: vec![1],
            amplitude: z.pow(code),
        };
        let t23 = b.two_to_three()?;
        pachner &= t23.projector() == b.projector().two_to_three()?
            && b.partition(ModelVersion::Published)? == t23.partition(ModelVersion::Published)?;
        // A unit amplitude has norm one on an admissible state and none otherwise.
        let norm = b.partition(ModelVersion::Corrected)?;
        let expected = C::scalar(12, i64::from(admissible(&b.external)))
            .checked_invariant_c3ee6ebe("fixed valid conductor");
        corrected_pachner &= norm == expected && t23.partition(ModelVersion::Corrected)? == norm;
    }
    Ok((pachner, corrected_pachner))
}

pub fn census(level: usize) -> Result<SpinFoamCensus, SpinFoamModelError> {
    if level == 0 || level > 3 {
        return Err("INVALID_SPIN_LEVEL".into());
    }
    let (tetra_sym, admissible_tets) = census_tetrahedra(level);
    let (simplex_sym, admissible_cells) = census_simplices(level);
    let z = C::zeta(12)?;
    let (projector, adjoint, duality) = census_boundary_states(&z)?;
    let (pachner, corrected_pachner) = census_pachner_states(&z)?;
    let vacuum_unitary = iv::is_unitary(&transition_matrix(ModelVersion::Corrected, &[0; 10]))?;
    let euler = sphere_euler();
    Ok(SpinFoamCensus {
        level,
        tetrahedra_checked: level.pow(6),
        simplices_checked: level.pow(10),
        admissible_tetrahedra: admissible_tets,
        admissible_simplices: admissible_cells,
        sphere_euler: euler,
        q2_square_three: quantum_integer(2).mul(&quantum_integer(2))?
            == C::scalar(12, 3).checked_invariant_c3ee6ebe("fixed valid conductor"),
        q6_zero: quantum_integer(6)
            == C::scalar(12, 0).checked_invariant_c3ee6ebe("fixed valid conductor"),
        tetra_orientation: tetra_sym,
        simplex_symmetries: simplex_sym,
        boundary_projector: projector,
        master_self_adjoint_on_basis: adjoint,
        diagonal_evolution_projector: duality,
        pachner_intertwining: pachner,
        sphere_euler_two: euler == 2,
        sphere_vacuum_partition: sphere_partition(&[0; 20])
            == C::scalar(12, 1).checked_invariant_c3ee6ebe("fixed valid conductor"),
        corrected_vacuum_transition_unitary: vacuum_unitary,
        corrected_partition_unit_norm_and_pachner_invariance: corrected_pachner,
    })
}
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finite_lean_models() {
        let r = census(2).unwrap();
        assert!(r.checks_hold());
        assert_eq!(r.admissible_tetrahedra, 8);
        assert_eq!(r.admissible_simplices, 64);
        assert!(census(0).is_err());
    }
    #[test]
    fn nonclaims_have_counterexamples() {
        let off_diagonal = |version| transition(version, &[0; 4], &[1, 1, 0, 0], &[0; 10]);
        assert_eq!(
            off_diagonal(ModelVersion::Published),
            C::scalar(12, 1).expect("fixed valid conductor")
        );
        assert_eq!(
            off_diagonal(ModelVersion::Corrected),
            C::scalar(12, 0).expect("fixed valid conductor")
        );
        let s = PachnerState {
            external: [0; 6],
            internal: vec![0],
            amplitude: C::zeta(12).unwrap().pow(3),
        };
        assert_eq!(
            s.partition(ModelVersion::Published).unwrap(),
            C::scalar(12, -1).expect("fixed valid conductor")
        );
        assert_eq!(
            s.partition(ModelVersion::Corrected).unwrap(),
            C::scalar(12, 1).expect("fixed valid conductor")
        );
    }
    #[test]
    fn real_values_of_q_zeta_12_are_read_exactly() {
        let z = C::zeta(12).unwrap();
        // |1 + zeta|^2 = 2 + sqrt(3).
        let one_plus = C::scalar(12, 1)
            .expect("fixed valid conductor")
            .add(&z)
            .unwrap();
        let norm = one_plus.conj().mul(&one_plus).unwrap();
        assert_eq!(
            real_value(&norm).unwrap(),
            Some(Quadratic::<3>::new(ri(2), ri(1)))
        );
        // zeta itself is not real; 2 - sqrt(3) > 0 > 1 - sqrt(3).
        assert_eq!(real_value(&z).unwrap(), None);
        assert!(Quadratic::<3>::new(ri(2), ri(-1)).is_nonnegative());
        assert!(!Quadratic::<3>::new(ri(1), ri(-1)).is_nonnegative());
        assert!(Quadratic::<3>::new(ri(-1), ri(1)).is_nonnegative());
        assert!(!Quadratic::<3>::new(ri(-2), ri(1)).is_nonnegative());
        assert_eq!(
            real_value(&C::scalar(8, 1).expect("fixed valid conductor")),
            Err("CONDUCTOR_12_REQUIRED".into())
        );
    }
}
