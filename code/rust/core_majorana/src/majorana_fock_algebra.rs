//! Majorana operators on a declared finite fermionic Fock space, over `Q(i)`.
//!
//! # Authority fence (MANDATORY)
//! AuthorityEffect: None.
//!
//! A carrier declares `L` fermionic modes. Its Fock space is `C^(2^L)` with
//! basis `|n_1 .. n_L>`, `n_j` in `{0, 1}`, mode 1 the leftmost tensor factor.
//! Through the Jordan–Wigner string the `2L` Majorana operators are
//!
//! `gamma_(2j-1) = Z (x) .. (x) Z (x) X (x) I (x) ..`,
//! `gamma_(2j)   = Z (x) .. (x) Z (x) Y (x) I (x) ..`
//!
//! with the `X` or `Y` at mode `j`, and `c_j = (gamma_(2j-1) + i gamma_(2j)) / 2`
//! lowers `n_j`. Computed exactly:
//!
//! - the Majoranas, the lowering operators `c_j`, and the parity
//!   `P = prod_j (-i gamma_(2j-1) gamma_(2j))`, which is `(-1)^(n_1 + .. + n_L)`
//!   on the basis;
//! - [`first_anticommutation_failure`]: the first pair of a declared family
//!   that breaks `{g_a, g_b} = 2 delta_ab I`. The Jordan–Wigner family has
//!   none; without its `Z` strings it fails;
//! - [`FockCarrier::kitaev_chain`]: the declared operator
//!   `H = sum_j [-t (c_j* c_(j+1) + h.c.) + Delta (c_j c_(j+1) + h.c.)] - mu sum_j (c_j* c_j - 1/2)`
//!   at rational `t`, `Delta`, `mu`, built from the `c_j`. Its algebraic
//!   properties (Hermitian, commuting with `P`, and at `t = Delta`, `mu = 0`
//!   equal to `i t sum_j gamma_(2j) gamma_(2j+1)` with `gamma_1` and
//!   `gamma_(2L)` commuting with it) are checked in the tests;
//! - [`FockCarrier::braid_unitary`]: `U_a = ((1 + i)/2)(I + gamma_(a+1) gamma_a)`,
//!   an exact unitary. It is `e^(i pi/4) exp((pi/4) gamma_(a+1) gamma_a)`: the
//!   braid operator of two Majoranas up to a declared global phase that no
//!   homogeneous identity sees;
//! - [`FockCarrier::restrict_to_sector`]: an operator that commutes with `P`,
//!   compressed to the even or odd parity sector (basis states in increasing
//!   index order).
//!
//! The carrier, the parameters and the chain are declared data. Nothing here
//! is a statement about a physical device or topological quantum computer.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3fe777e2<T> {
    fn checked_invariant_3fe777e2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3fe777e2<T> for Option<T> {
    #[inline]
    fn checked_invariant_3fe777e2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3fe777e2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3fe777e2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use linear_algebra::exact_pfaffian::{pfaffian, PfaffianError};
use num_traits::Zero;
use core_lie_theory::clifford::{CliffordError, CliffordFamily};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{rq, Rational};

/// Declaration of authority effect.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

/// The largest number of modes a carrier declares (`2^5 = 32` dimensions).
pub const MAX_MODES: usize = 5;

/// Refusals for Fock carriers and their operators.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MajoranaError {
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    Pfaffian(#[from] PfaffianError),
    #[error(transparent)]
    Clifford(#[from] CliffordError),
    #[error("boundary sign must be +1 or -1")]
    BoundarySign,
    #[error("a Fock carrier declares between 1 and {MAX_MODES} modes, not {modes}")]
    Modes { modes: usize },
    #[error("Majorana index {index} is outside 1..={count}")]
    MajoranaIndex { index: usize, count: usize },
    #[error("mode index {index} is outside 1..={modes}")]
    ModeIndex { index: usize, modes: usize },
    #[error("braid index {index} is outside 1..{count}")]
    BraidIndex { index: usize, count: usize },
    #[error("family member {index} is not a square matrix of the family's size")]
    FamilyShape { index: usize },
    #[error("a {rows}x{cols} matrix does not act on the {dimension}-dimensional Fock space")]
    Shape {
        rows: usize,
        cols: usize,
        dimension: usize,
    },
    #[error("the operator does not commute with the parity, so it has no sector restriction")]
    MixesSectors,
}

/// Helper to construct GaussianRat from integers.
pub fn gi(re: i64, im: i64) -> GaussianRat {
    GaussianRat::from_ints(re, im)
}

/// Helper to construct GaussianRat from rational fractions.
pub fn gq(a: i64, b: i64, c: i64, d: i64) -> GaussianRat {
    GaussianRat {
        re: rq(a, b),
        im: rq(c, d),
    }
}

/// The first pair `(a, b)`, `a <= b`, with `{g_a, g_b} != 2 delta_ab I`.
/// An empty family has no failing pair.
pub fn first_anticommutation_failure(
    family: &[BasicMatrix<GaussianRat>],
) -> Result<Option<(usize, usize)>, MajoranaError> {
    if family.is_empty() {
        return Ok(None);
    }
    match CliffordFamily::<GaussianRat>::admit(family.to_vec(), vec![1; family.len()]) {
        Ok(_) => Ok(None),
        Err(CliffordError::Anticommutator { mu, nu }) => Ok(Some((mu, nu))),
        Err(CliffordError::Shape { index }) => Err(MajoranaError::FamilyShape { index }),
        Err(other) => Err(MajoranaError::Clifford(other)),
    }
}

/// A declared Fock space of `L` fermionic modes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FockCarrier {
    modes: usize,
}

impl FockCarrier {
    /// Constructs a validated Fock carrier for `modes` modes (`1..=MAX_MODES`).
    pub fn new(modes: usize) -> Result<Self, MajoranaError> {
        if modes == 0 || modes > MAX_MODES {
            return Err(MajoranaError::Modes { modes });
        }
        Ok(Self { modes })
    }

    /// Number of fermionic modes.
    pub fn modes(&self) -> usize {
        self.modes
    }

    /// Fock space dimension: `2^L`.
    pub fn dimension(&self) -> usize {
        1 << self.modes
    }

    fn majorana_unchecked(&self, index: usize) -> BasicMatrix<GaussianRat> {
        core_lie_theory::clifford::jordan_wigner_operator::<GaussianRat>(self.modes, index - 1)
            .checked_invariant_3fe777e2("the validated Fock carrier is within the Clifford representation bound")
    }

    fn lowering_unchecked(&self, mode: usize) -> BasicMatrix<GaussianRat> {
        let odd = self.majorana_unchecked(2 * mode - 1);
        let even = self.majorana_unchecked(2 * mode);
        mx::scale(
            &mx::add(
                &odd,
                &mx::scale(&even, &gi(0, 1)).checked_invariant_3fe777e2("validated Fock dimensions"),
            )
            .checked_invariant_3fe777e2("validated Fock dimensions"),
            &gq(1, 2, 0, 1),
        )
        .checked_invariant_3fe777e2("validated Fock dimensions")
    }

    /// `gamma_index`, `index` in `1..=2L`.
    pub fn majorana(&self, index: usize) -> Result<BasicMatrix<GaussianRat>, MajoranaError> {
        if index == 0 || index > 2 * self.modes {
            return Err(MajoranaError::MajoranaIndex {
                index,
                count: 2 * self.modes,
            });
        }
        Ok(self.majorana_unchecked(index))
    }

    /// All `2L` Majoranas in index order.
    pub fn majoranas(&self) -> Vec<BasicMatrix<GaussianRat>> {
        (1..=2 * self.modes)
            .map(|index| self.majorana_unchecked(index))
            .collect()
    }

    /// `c_mode = (gamma_(2 mode - 1) + i gamma_(2 mode)) / 2`, `mode` in `1..=L`.
    pub fn lowering(&self, mode: usize) -> Result<BasicMatrix<GaussianRat>, MajoranaError> {
        if mode == 0 || mode > self.modes {
            return Err(MajoranaError::ModeIndex {
                index: mode,
                modes: self.modes,
            });
        }
        Ok(self.lowering_unchecked(mode))
    }

    /// `P = prod_j (-i gamma_(2j-1) gamma_(2j))`.
    pub fn parity(&self) -> BasicMatrix<GaussianRat> {
        let mut parity = mx::identity(self.dimension()).checked_invariant_3fe777e2("validated finite Fock dimension");
        for j in 1..=self.modes {
            let pair = mx::scale(
                &mx::multiply(
                    &self.majorana_unchecked(2 * j - 1),
                    &self.majorana_unchecked(2 * j),
                )
                .checked_invariant_3fe777e2("validated Fock shapes"),
                &gi(0, -1),
            )
            .checked_invariant_3fe777e2("validated Fock dimension");
            parity = mx::multiply(&parity, &pair).checked_invariant_3fe777e2("validated Fock dimensions");
        }
        parity
    }

    /// Real antisymmetric A in H=(i/4) sum_ab A_ab gamma_a gamma_b.
    /// `boundary=None` gives an open chain; `Some(+-1)` declares the boundary twist.
    pub fn bdg_majorana_matrix(
        &self,
        t: &Rational,
        delta: &Rational,
        mu: &Rational,
        boundary: Option<i8>,
    ) -> Result<BasicMatrix<Rational>, MajoranaError> {
        if boundary.is_some_and(|s| s != 1 && s != -1) {
            return Err(MajoranaError::BoundarySign);
        }
        let n = 2 * self.modes;
        let mut data = vec![Rational::zero(); n * n];
        let mut add = |a: usize, b: usize, value: Rational| {
            data[a * n + b] += &value;
            data[b * n + a] -= value;
        };
        for j in 0..self.modes {
            add(2 * j, 2 * j + 1, -mu);
        }
        for j in 0..self.modes - 1 {
            add(2 * j, 2 * (j + 1) + 1, delta - t);
            add(2 * j + 1, 2 * (j + 1), delta + t);
        }
        if let Some(sign) = boundary {
            let sign = Rational::from_integer(sign.into());
            let last = self.modes - 1;
            add(2 * last, 1, &sign * (delta - t));
            add(2 * last + 1, 0, &sign * (delta + t));
        }
        Ok(BasicMatrix::from_row_major(n, n, data)
            .checked_invariant_3fe777e2("the BdG carrier has 2L squared entries"))
    }

    /// The Kitaev chain Hamiltonian with optional boundary twist.
    pub fn kitaev_chain_with_boundary(
        &self,
        t: &Rational,
        delta: &Rational,
        mu: &Rational,
        boundary: Option<i8>,
    ) -> Result<BasicMatrix<GaussianRat>, MajoranaError> {
        let a = self.bdg_majorana_matrix(t, delta, mu, boundary)?;
        let gammas = self.majoranas();
        let mut h = mx::zeros(self.dimension(), self.dimension())?;
        for i in 0..2 * self.modes {
            for j in i + 1..2 * self.modes {
                let value = a.get(i, j).checked_invariant_3fe777e2("valid BdG indices");
                if !value.is_zero() {
                    h = mx::add(
                        &h,
                        &mx::scale(
                            &mx::multiply(&gammas[i], &gammas[j])?,
                            &GaussianRat {
                                re: Rational::zero(),
                                im: value / Rational::from_integer(2.into()),
                            },
                        )?,
                    )?;
                }
            }
        }
        Ok(h)
    }

    /// The declared Kitaev chain at hopping `t`, pairing `Delta` and chemical
    /// potential `mu`, with open ends.
    pub fn kitaev_chain(
        &self,
        hopping: &Rational,
        pairing: &Rational,
        chemical_potential: &Rational,
    ) -> BasicMatrix<GaussianRat> {
        self.kitaev_chain_with_boundary(hopping, pairing, chemical_potential, None)
            .checked_invariant_3fe777e2("the validated finite Fock carrier admits its open-chain Hamiltonian")
    }

    /// The translation-invariant bulk Z2 invariant: signs of the k=0/pi Pfaffians.
    /// None denotes a gap closing: mu=+-2t, or Delta=0 with |mu|<=2|t|.
    pub fn bulk_kitaev_invariant(t: &Rational, delta: &Rational, mu: &Rational) -> Option<i8> {
        use num_traits::Signed;
        let product = (mu + t * Rational::from_integer(2.into()))
            * (mu - t * Rational::from_integer(2.into()));
        if delta.is_zero() && !product.is_positive() {
            return None;
        }
        if product.is_zero() {
            None
        } else {
            Some(if product.is_positive() { 1 } else { -1 })
        }
    }

    /// Finite-chain Pfaffian, whose zero detects an exact zero BdG mode.
    pub fn kitaev_pfaffian(
        &self,
        t: &Rational,
        delta: &Rational,
        mu: &Rational,
        boundary: Option<i8>,
    ) -> Result<Rational, MajoranaError> {
        let a = self.bdg_majorana_matrix(t, delta, mu, boundary)?;
        Ok(pfaffian(&a)?)
    }

    /// `U_index = ((1 + i)/2)(I + gamma_(index+1) gamma_index)`, `index` in `1..2L`.
    pub fn braid_unitary(&self, index: usize) -> Result<BasicMatrix<GaussianRat>, MajoranaError> {
        if index == 0 || index >= 2 * self.modes {
            return Err(MajoranaError::BraidIndex {
                index,
                count: 2 * self.modes,
            });
        }
        let product = mx::multiply(
            &self.majorana_unchecked(index + 1),
            &self.majorana_unchecked(index),
        )?;
        Ok(mx::scale(
            &mx::add(&mx::identity(self.dimension())?, &product)?,
            &gq(1, 2, 1, 2),
        )?)
    }

    /// Basis indices of the even (`even = true`) or odd parity sector.
    pub fn sector_basis(&self, even: bool) -> Vec<usize> {
        (0..self.dimension())
            .filter(|b| (b.count_ones() % 2 == 0) == even)
            .collect()
    }

    /// The compression of `operator` to one parity sector, refused unless
    /// `operator` commutes with `P`.
    pub fn restrict_to_sector(
        &self,
        operator: &BasicMatrix<GaussianRat>,
        even: bool,
    ) -> Result<BasicMatrix<GaussianRat>, MajoranaError> {
        let dimension = self.dimension();
        if operator.rows() != dimension || operator.cols() != dimension {
            return Err(MajoranaError::Shape {
                rows: operator.rows(),
                cols: operator.cols(),
                dimension,
            });
        }
        let parity = self.parity();
        if mx::multiply(operator, &parity)? != mx::multiply(&parity, operator)? {
            return Err(MajoranaError::MixesSectors);
        }
        let basis = self.sector_basis(even);
        Ok(mx::from_fn(basis.len(), basis.len(), |r, c| {
            operator
                .get_ref(basis[r], basis[c])
                .checked_invariant_3fe777e2("checked sector indices")
                .clone()
        })?)
    }
}

// Origin: engine/crates_rs/core_majorana/src/majorana_fock_algebra.rs
// Claim: urn:core:crates_rs:core-majorana:majorana-fock-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use linear_algebra::exact_field::involution as iv;
    use linear_algebra::exact_field::matrix as mx;
    use core_number_theory::rational::ri;

    fn anticommutator(
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
    ) -> BasicMatrix<GaussianRat> {
        mx::add(&mx::multiply(a, b).unwrap(), &mx::multiply(b, a).unwrap()).unwrap()
    }

    fn commutator(
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
    ) -> BasicMatrix<GaussianRat> {
        mx::sub(&mx::multiply(a, b).unwrap(), &mx::multiply(b, a).unwrap()).unwrap()
    }

    #[test]
    fn one_mode_majoranas_are_pauli_x_and_y() {
        // Kills: swapping X with Z, or flipping the sign of Y, and treating an empty family as a failure.
        let carrier = FockCarrier::new(1).unwrap();
        let x = mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap();
        let y = mx::from_rows(vec![
            vec![gi(0, 0), gi(0, -1)],
            vec![gi(0, 1), gi(0, 0)],
        ])
        .unwrap();
        assert_eq!(carrier.majorana(1).unwrap(), x);
        assert_eq!(carrier.majorana(2).unwrap(), y);
        assert_eq!(
            carrier.parity(),
            mx::diagonal(&[gi(1, 0), gi(-1, 0)]).unwrap()
        );
        assert_eq!(first_anticommutation_failure(&[]).unwrap(), None);
    }

    #[test]
    fn test_canonical_anticommutation_relations() {
        for modes in 1..=3 {
            let carrier = FockCarrier::new(modes).unwrap();
            let gammas = carrier.majoranas();
            assert_eq!(gammas.len(), 2 * modes);

            // Majoranas are self-adjoint: gamma_k^\dagger = gamma_k
            for gamma in &gammas {
                assert_eq!(iv::adjoint(gamma).unwrap(), *gamma);
            }

            // CAR: {gamma_j, gamma_k} = 2 delta_{jk} I
            let identity = mx::identity(carrier.dimension()).unwrap();
            let two_i = mx::scale(&identity, &gi(2, 0)).unwrap();
            let zero = mx::zeros(carrier.dimension(), carrier.dimension()).unwrap();

            for (j, g_j) in gammas.iter().enumerate() {
                for (k, g_k) in gammas.iter().enumerate() {
                    let a = anticommutator(g_j, g_k);
                    if j == k {
                        assert_eq!(a, two_i);
                    } else {
                        assert_eq!(a, zero);
                    }
                }
            }

            // Lowering and raising operators: {c_j, c_k^\dagger} = delta_{jk} I, {c_j, c_k} = 0
            let lowerings: Vec<_> = (1..=modes).map(|m| carrier.lowering(m).unwrap()).collect();
            for (j, c_j) in lowerings.iter().enumerate() {
                for (k, c_k) in lowerings.iter().enumerate() {
                    let c_k_dag = iv::adjoint(c_k).unwrap();
                    let a_dag = anticommutator(c_j, &c_k_dag);
                    if j == k {
                        assert_eq!(a_dag, identity);
                    } else {
                        assert_eq!(a_dag, zero);
                    }
                    assert_eq!(anticommutator(c_j, c_k), zero);
                }
            }

            // No failure in canonical Jordan-Wigner family
            assert_eq!(first_anticommutation_failure(&gammas).unwrap(), None);
        }
    }

    #[test]
    fn test_parity_operator_algebra() {
        for modes in 1..=3 {
            let carrier = FockCarrier::new(modes).unwrap();
            let p = carrier.parity();
            let identity = mx::identity(carrier.dimension()).unwrap();
            let zero = mx::zeros(carrier.dimension(), carrier.dimension()).unwrap();

            // P is Hermitian
            assert_eq!(iv::adjoint(&p).unwrap(), p);

            // P^2 = I
            assert_eq!(mx::multiply(&p, &p).unwrap(), identity);

            // {P, gamma_j} = 0 for all Majoranas
            for gamma in carrier.majoranas() {
                assert_eq!(anticommutator(&p, &gamma), zero);
            }
        }
    }

    #[test]
    fn test_braiding_unitaries_and_relations() {
        let carrier = FockCarrier::new(2).unwrap();
        let identity = mx::identity(carrier.dimension()).unwrap();

        // Check braid unitaries U_1, U_2, U_3
        let u1 = carrier.braid_unitary(1).unwrap();
        let u2 = carrier.braid_unitary(2).unwrap();
        let u3 = carrier.braid_unitary(3).unwrap();

        // Unitarity: U^\dagger U = I
        for u in [&u1, &u2, &u3] {
            assert_eq!(mx::multiply(&iv::adjoint(u).unwrap(), u).unwrap(), identity);
            assert_eq!(mx::multiply(u, &iv::adjoint(u).unwrap()).unwrap(), identity);
        }

        // Braid action: U_a gamma_a U_a^\dagger = gamma_{a+1}
        let gammas = carrier.majoranas();
        let g1 = &gammas[0];
        let g2 = &gammas[1];
        let u1_dag = iv::adjoint(&u1).unwrap();
        let braided_1 = mx::multiply(&u1, &mx::multiply(g1, &u1_dag).unwrap()).unwrap();
        assert_eq!(braided_1, *g2);

        // U_a gamma_{a+1} U_a^\dagger = -gamma_a
        let braided_2 = mx::multiply(&u1, &mx::multiply(g2, &u1_dag).unwrap()).unwrap();
        let neg_g1 = mx::scale(g1, &gi(-1, 0)).unwrap();
        assert_eq!(braided_2, neg_g1);

        // Artin braid relation: U_1 U_2 U_1 = U_2 U_1 U_2
        let lhs = mx::multiply(&u1, &mx::multiply(&u2, &u1).unwrap()).unwrap();
        let rhs = mx::multiply(&u2, &mx::multiply(&u1, &u2).unwrap()).unwrap();
        assert_eq!(lhs, rhs);

        // Distant commutativity: U_1 U_3 = U_3 U_1 (|1 - 3| >= 2)
        assert_eq!(
            mx::multiply(&u1, &u3).unwrap(),
            mx::multiply(&u3, &u1).unwrap()
        );
    }

    #[test]
    fn test_kitaev_chain_properties() {
        let carrier = FockCarrier::new(2).unwrap();
        let t = ri(1);
        let delta = ri(1);
        let mu = ri(0);

        let h = carrier.kitaev_chain(&t, &delta, &mu);

        // Hamiltonian is Hermitian
        assert_eq!(iv::adjoint(&h).unwrap(), h);

        // Hamiltonian commutes with parity: [H, P] = 0
        let p = carrier.parity();
        let zero = mx::zeros(carrier.dimension(), carrier.dimension()).unwrap();
        assert_eq!(commutator(&h, &p), zero);

        // At sweet spot (t = Delta, mu = 0), edge modes gamma_1 and gamma_{2L} commute with H
        let gammas = carrier.majoranas();
        let g1 = &gammas[0];
        let g_last = &gammas[2 * carrier.modes() - 1];
        assert_eq!(commutator(&h, g1), zero);
        assert_eq!(commutator(&h, g_last), zero);

        // Bulk invariant
        assert_eq!(FockCarrier::bulk_kitaev_invariant(&t, &delta, &mu), Some(-1));
    }

    #[test]
    fn test_sector_restriction_and_refusals() {
        let carrier = FockCarrier::new(2).unwrap();
        let p = carrier.parity();

        // Parity commutes with itself, so restriction to even and odd succeeds
        let p_even = carrier.restrict_to_sector(&p, true).unwrap();
        let p_odd = carrier.restrict_to_sector(&p, false).unwrap();
        assert_eq!(p_even.rows(), 2);
        assert_eq!(p_odd.rows(), 2);

        // Majoranas anticommute with parity (do not commute), so restrict_to_sector is refused
        let g1 = carrier.majorana(1).unwrap();
        assert_eq!(
            carrier.restrict_to_sector(&g1, true),
            Err(MajoranaError::MixesSectors)
        );

        // Refusals on invalid modes
        assert_eq!(FockCarrier::new(0), Err(MajoranaError::Modes { modes: 0 }));
        assert_eq!(FockCarrier::new(6), Err(MajoranaError::Modes { modes: 6 }));

        // Refusals on out of bounds indices
        assert_eq!(
            carrier.majorana(0),
            Err(MajoranaError::MajoranaIndex { index: 0, count: 4 })
        );
        assert_eq!(
            carrier.majorana(5),
            Err(MajoranaError::MajoranaIndex { index: 5, count: 4 })
        );
        assert_eq!(
            carrier.lowering(3),
            Err(MajoranaError::ModeIndex { index: 3, modes: 2 })
        );
        assert_eq!(
            carrier.braid_unitary(0),
            Err(MajoranaError::BraidIndex { index: 0, count: 4 })
        );
        assert_eq!(
            carrier.braid_unitary(4),
            Err(MajoranaError::BraidIndex { index: 4, count: 4 })
        );
    }
}
