//! Sparse exact open Kitaev wire in the Majorana paper's coefficient convention.
//!
//! `H = -N mu/2 I + sum_(a<b) h_ab i gamma_a gamma_b`, with
//! `h_(2j-1,2j) = -mu/2`, `h_(2j,2j+1) = -(t+delta)/2`, and
//! `h_(2j-1,2j+2) = (t-delta)/2`. These are precisely the coefficients of
//! `kitaev_chain_exact.py`. Relative to the existing Fock carrier this is
//! `FockCarrier::kitaev_chain(-t, -delta, mu) - N mu/2 I`.
//!
//! No Fock matrix is allocated. Isolated coordinate Majoranas are reported;
//! arbitrary linear combinations in the quadratic kernel and a bulk
//! topological phase require separate checks. AuthorityEffect: None.

use num_traits::{Signed, Zero};
use core_number_theory::rational::Rational;
use std::collections::{BTreeMap, BTreeSet};

/// Bound on a declared sparse wire's number of fermionic sites.
pub const MAX_WIRE_SITES: usize = 65_536;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum KitaevWireError {
    #[error("the sparse wire requires 2..={MAX_WIRE_SITES} sites, not {sites}")]
    Sites { sites: usize },
    #[error("a bilinear requires positive ordered indices a < b, not ({a}, {b})")]
    Bilinear { a: usize, b: usize },
    #[error("Majorana mode {mode} is outside 1..={count}")]
    Mode { mode: usize, count: usize },
}

/// An admitted Hermitian basis term `i gamma_a gamma_b` with one-indexed `a<b`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct MajoranaBilinear {
    a: usize,
    b: usize,
}

impl MajoranaBilinear {
    pub fn new(a: usize, b: usize) -> Result<Self, KitaevWireError> {
        if a == 0 || a >= b {
            return Err(KitaevWireError::Bilinear { a, b });
        }
        Ok(Self { a, b })
    }

    pub fn mode_a(&self) -> usize {
        self.a
    }

    pub fn mode_b(&self) -> usize {
        self.b
    }

    /// The real coefficient and target in `i[i gamma_a gamma_b, gamma_mode]`.
    /// The explicit outer `i` matters: the commutator itself is imaginary.
    pub fn generator_on_mode(&self, mode: usize) -> Option<(i8, usize)> {
        if mode == self.a {
            Some((2, self.b))
        } else if mode == self.b {
            Some((-2, self.a))
        } else {
            None
        }
    }
}

/// Exact sparse coefficients of a declared open wire, with no zero terms.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KitaevWire {
    sites: usize,
    t: Rational,
    mu: Rational,
    delta: Rational,
    constant_energy: Rational,
    terms: BTreeMap<MajoranaBilinear, Rational>,
}

/// Boundary isolation is a finite algebraic property of the declared wire.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryIsolation {
    pub boundary_modes: (usize, usize),
    pub isolated_modes: BTreeSet<usize>,
    pub left_generator: BTreeMap<usize, Rational>,
    pub right_generator: BTreeMap<usize, Rational>,
    pub is_sweet_spot: bool,
}

impl BoundaryIsolation {
    pub fn left_isolated(&self) -> bool {
        self.left_generator.is_empty()
    }

    pub fn right_isolated(&self) -> bool {
        self.right_generator.is_empty()
    }
}

impl KitaevWire {
    pub fn new(
        sites: usize,
        t: Rational,
        mu: Rational,
        delta: Rational,
    ) -> Result<Self, KitaevWireError> {
        if !(2..=MAX_WIRE_SITES).contains(&sites) {
            return Err(KitaevWireError::Sites { sites });
        }
        let two = Rational::from_integer(2.into());
        let onsite = -&mu / &two;
        let bulk = -(&t + &delta) / &two;
        let cross = (&t - &delta) / &two;
        let mut terms = BTreeMap::new();
        for j in 1..=sites {
            if !onsite.is_zero() {
                terms.insert(
                    MajoranaBilinear {
                        a: 2 * j - 1,
                        b: 2 * j,
                    },
                    onsite.clone(),
                );
            }
            if j < sites {
                if !bulk.is_zero() {
                    terms.insert(
                        MajoranaBilinear {
                            a: 2 * j,
                            b: 2 * j + 1,
                        },
                        bulk.clone(),
                    );
                }
                if !cross.is_zero() {
                    terms.insert(
                        MajoranaBilinear {
                            a: 2 * j - 1,
                            b: 2 * j + 2,
                        },
                        cross.clone(),
                    );
                }
            }
        }
        let constant_energy = -Rational::from_integer(sites.into()) * &mu / two;
        Ok(Self {
            sites,
            t,
            mu,
            delta,
            constant_energy,
            terms,
        })
    }

    pub fn sites(&self) -> usize {
        self.sites
    }

    pub fn mode_count(&self) -> usize {
        2 * self.sites
    }

    pub fn hopping(&self) -> &Rational {
        &self.t
    }

    pub fn chemical_potential(&self) -> &Rational {
        &self.mu
    }

    pub fn pairing(&self) -> &Rational {
        &self.delta
    }

    pub fn constant_energy(&self) -> &Rational {
        &self.constant_energy
    }

    pub fn terms(&self) -> &BTreeMap<MajoranaBilinear, Rational> {
        &self.terms
    }

    pub fn is_sweet_spot(&self) -> bool {
        self.mu.is_zero() && self.t == self.delta && self.t.is_positive()
    }

    pub fn boundary_modes(&self) -> (usize, usize) {
        (1, self.mode_count())
    }

    pub fn active_modes(&self) -> BTreeSet<usize> {
        self.terms
            .keys()
            .flat_map(|term| [term.a, term.b])
            .collect()
    }

    /// Coordinate Majoranas absent from every term. This is distinct from
    /// computing the full nullspace of the quadratic coefficient matrix.
    pub fn isolated_modes(&self) -> BTreeSet<usize> {
        let active = self.active_modes();
        (1..=self.mode_count())
            .filter(|mode| !active.contains(mode))
            .collect()
    }

    /// Compute `i[H, gamma_mode]` exactly in the Majorana basis. This is the
    /// real generator represented by the paper's `commutator_with_mode` API.
    pub fn generator_on_mode(
        &self,
        mode: usize,
    ) -> Result<BTreeMap<usize, Rational>, KitaevWireError> {
        if mode == 0 || mode > self.mode_count() {
            return Err(KitaevWireError::Mode {
                mode,
                count: self.mode_count(),
            });
        }
        let mut result = BTreeMap::new();
        for (term, coefficient) in &self.terms {
            if let Some((factor, target)) = term.generator_on_mode(mode) {
                *result.entry(target).or_insert_with(Rational::zero) +=
                    coefficient * Rational::from_integer(factor.into());
            }
        }
        result.retain(|_, value| !value.is_zero());
        Ok(result)
    }

    pub fn boundary_isolation(&self) -> Result<BoundaryIsolation, KitaevWireError> {
        let boundary_modes = self.boundary_modes();
        Ok(BoundaryIsolation {
            boundary_modes,
            isolated_modes: self.isolated_modes(),
            left_generator: self.generator_on_mode(boundary_modes.0)?,
            right_generator: self.generator_on_mode(boundary_modes.1)?,
            is_sweet_spot: self.is_sweet_spot(),
        })
    }
}

// Origin: engine/crates_rs/core_majorana/src/sparse_kitaev.rs
// Claim: urn:core:crates_rs:core-majorana:sparse-kitaev:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::majorana_fock_algebra::{gi, FockCarrier};
    use linear_algebra::exact_field::matrix;
    use core_number_theory::{
        cyclotomic::GaussianRat,
        rational::{ri, rq},
    };

    #[test]
    fn sparse_coefficients_and_generator_match_independent_fock_operator() {
        for sites in 2..=3 {
            for (t, mu, delta) in [
                (ri(1), ri(0), ri(1)),
                (rq(2, 3), rq(3, 5), rq(-4, 7)),
                (ri(1), ri(-2), ri(-1)),
            ] {
                let wire = KitaevWire::new(sites, t.clone(), mu.clone(), delta.clone()).unwrap();
                let fock = FockCarrier::new(sites).unwrap();
                let h = matrix::add(
                    &fock.kitaev_chain(&(-t), &(-delta), &mu),
                    &matrix::scale(
                        &matrix::identity(fock.dimension()).unwrap(),
                        &GaussianRat {
                            re: wire.constant_energy().clone(),
                            im: ri(0),
                        },
                    )
                    .unwrap(),
                )
                .unwrap();
                let mut reconstructed = matrix::scale(
                    &matrix::identity(fock.dimension()).unwrap(),
                    &GaussianRat {
                        re: wire.constant_energy().clone(),
                        im: ri(0),
                    },
                )
                .unwrap();
                for (term, coefficient) in wire.terms() {
                    reconstructed = matrix::add(
                        &reconstructed,
                        &matrix::scale(
                            &matrix::multiply(
                                &fock.majorana(term.mode_a()).unwrap(),
                                &fock.majorana(term.mode_b()).unwrap(),
                            )
                            .unwrap(),
                            &GaussianRat {
                                re: ri(0),
                                im: coefficient.clone(),
                            },
                        )
                        .unwrap(),
                    )
                    .unwrap();
                }
                assert_eq!(reconstructed, h);
                for mode in 1..=wire.mode_count() {
                    let gamma = fock.majorana(mode).unwrap();
                    let actual = matrix::scale(
                        &matrix::sub(
                            &matrix::multiply(&h, &gamma).unwrap(),
                            &matrix::multiply(&gamma, &h).unwrap(),
                        )
                        .unwrap(),
                        &gi(0, 1),
                    )
                    .unwrap();
                    let mut expected = matrix::zeros(fock.dimension(), fock.dimension()).unwrap();
                    for (target, coefficient) in wire.generator_on_mode(mode).unwrap() {
                        expected = matrix::add(
                            &expected,
                            &matrix::scale(
                                &fock.majorana(target).unwrap(),
                                &GaussianRat {
                                    re: coefficient,
                                    im: ri(0),
                                },
                            )
                            .unwrap(),
                        )
                        .unwrap();
                    }
                    assert_eq!(actual, expected);
                }
            }
        }
    }

    #[test]
    fn sweet_spot_detuning_and_zero_wire_have_distinct_diagnostics() {
        let sweet = KitaevWire::new(8, rq(2, 3), ri(0), rq(2, 3)).unwrap();
        let report = sweet.boundary_isolation().unwrap();
        assert!(report.is_sweet_spot && report.left_isolated() && report.right_isolated());
        assert_eq!(report.isolated_modes, BTreeSet::from([1, 16]));
        assert_eq!(sweet.terms().len(), 7);
        for wire in [
            KitaevWire::new(8, ri(1), rq(1, 5), ri(1)).unwrap(),
            KitaevWire::new(8, ri(1), ri(0), rq(4, 5)).unwrap(),
        ] {
            let report = wire.boundary_isolation().unwrap();
            assert!(!report.is_sweet_spot && !report.left_isolated() && !report.right_isolated());
            assert!(report.isolated_modes.is_empty());
        }
        let zero = KitaevWire::new(3, ri(0), ri(0), ri(0)).unwrap();
        assert!(!zero.is_sweet_spot());
        assert_eq!(zero.isolated_modes(), (1..=6).collect());
        assert!(zero.terms().is_empty());
    }

    #[test]
    fn invalid_wire_and_bilinear_declarations_fail_closed() {
        for sites in [0, 1, usize::MAX] {
            assert_eq!(
                KitaevWire::new(sites, ri(1), ri(0), ri(1)),
                Err(KitaevWireError::Sites { sites })
            );
        }
        for (a, b) in [(0, 1), (1, 1), (3, 2)] {
            assert_eq!(
                MajoranaBilinear::new(a, b),
                Err(KitaevWireError::Bilinear { a, b })
            );
        }
        let wire = KitaevWire::new(2, ri(1), ri(0), ri(1)).unwrap();
        // Kills: returning an empty generator for a mode outside 1..=4.
        assert_eq!(
            wire.generator_on_mode(0),
            Err(KitaevWireError::Mode { mode: 0, count: 4 })
        );
        assert_eq!(
            wire.generator_on_mode(5),
            Err(KitaevWireError::Mode { mode: 5, count: 4 })
        );
    }

    #[test]
    fn long_wire_is_not_limited_by_fock_dimension() {
        let wire = KitaevWire::new(10_000, ri(1), ri(0), ri(1)).unwrap();
        assert_eq!(wire.terms().len(), 9_999);
        assert_eq!(wire.isolated_modes(), BTreeSet::from([1, 20_000]));
    }
}
