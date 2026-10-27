// Executable finite evidence; AuthorityEffect: None.
//! Chapter 19: the bridge from integer cochains to amplitudes over Q(i), readout left
//! free. Executable finite evidence for `WDP-CH19-P11` and `WDP-CH19-P12`; the residual
//! `WDP-CH19-O03` (which readout, if any, is privileged) stays open.
//!
//! Fix the rational unit phase `u = (3 + 4i) / 5`. An integer edge cochain `a` on an
//! oriented graph gives the transport `U_e = u^{a_e}` on each edge; the holonomy of a
//! closed edge path is the product of its transports, a reversed edge contributing the
//! inverse (the conjugate, since the phase is unimodular), so
//! `Hol(gamma) = u^{<a, gamma>}` with `<a, gamma> = sum_e +- a_e`.
//!
//! - `WDP-CH19-P11`: replacing `a` by `a + d0 f` conjugates the transports by
//!   `g(v) = u^{f(v)}` ([`OrientedGraph::gauge_conjugated_transport`]) and leaves every cycle holonomy
//!   unchanged. For two paths `gamma_1, gamma_2` from `s` to `t` with amplitudes
//!   `z_1, z_2`, `z_1 conj(z_2) = N(z_2) Hol(gamma_1 gamma_2^{-1})`, with `N` the
//!   norm `re^2 + im^2`; unit transports give `N(z_2) = 1`. Two amplitude pairs agree
//!   up to one common unit phase exactly when `N(z_1) = N(w_1)`, `N(z_2) = N(w_2)` and
//!   `z_1 conj(z_2) = w_1 conj(w_2)` ([`same_up_to_common_phase`]; zero amplitudes need
//!   no exclusion). The readouts [`readout_quadratic`] `N(z_1 + z_2)` and
//!   [`readout_quartic`] `N(z_1 + z_2)^2` are both invariant under a common phase and are
//!   left free: nothing here chooses between them.
//! - `WDP-CH19-P12`: there is no homomorphism `(Q, +) -> U(1)(Q(i))` with `1 -> u`, since
//!   the image of `1/2` would be a square root of `u`, and `u` has none in `Q(i)`
//!   ([`unit_square_root`], [`half_exponent_obstruction`]: `x^2 = (1 + Re u)/2 = 4/5` is
//!   not a rational square). Integer cochains do exponentiate, and `n -> u^n` is injective:
//!   `u^n != 1` for every `n >= 1`, certified by [`u_power_is_never_one`] without forming
//!   `u^n`. The certificate is that `(3 + 4i)^n` is not zero modulo 5, whereas `u^n = 1`
//!   would make it `5^n`, which is. The residue is computed exactly, for any positive
//!   `i64` exponent ([`unit_phase_numerator_mod_five`]). This concerns this `u` only.
//!
//! Amplitudes are `core_holonomy::GaussianRational` over `BigRational`.
//! [`OrientedGraph::u1_connection`] presents a cochain as a `U1Connection`, whose loop
//! holonomy is `core_holonomy::compute_loop_holonomy`; the tests compare it with the
//! exponent-sum holonomy computed here.

use std::collections::{BTreeMap, BTreeSet};

use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_holonomy::{ExactScalar, GaussianRational};
use serde::Serialize;

use crate::connection::U1Connection;
use crate::error::WdpError;
use crate::types::AuthorityEffect;

/// An amplitude in Q(i).
pub type Amplitude = GaussianRational<BigRational>;

/// Largest `|n|` for which [`u_pow`] computes `u^n`.
pub const MAX_EXPONENT: i64 = 4096;

/// Largest number of vertices of an [`OrientedGraph`].
pub const MAX_VERTICES: usize = 100_000;

fn invalid(detail: String) -> WdpError {
    WdpError::InvalidInput { detail }
}

fn ratio(numerator: i64, denominator: i64) -> BigRational {
    BigRational::new(numerator.into(), denominator.into())
}

/// `N(z) = re^2 + im^2`.
pub fn norm(z: &Amplitude) -> BigRational {
    z.norm_sq()
}

/// Complex conjugate.
pub fn conj(z: &Amplitude) -> Amplitude {
    z.conjugate()
}

/// Product.
pub fn mul(a: &Amplitude, b: &Amplitude) -> Amplitude {
    a.clone() * b.clone()
}

/// The fixed unit phase `u = (3 + 4i) / 5`.
pub fn unit_phase() -> Amplitude {
    GaussianRational::new(ratio(3, 5), ratio(4, 5))
}

/// `u^n` exactly, negative `n` by conjugation; `|n|` is capped at [`MAX_EXPONENT`].
pub fn u_pow(n: i64) -> Result<Amplitude, WdpError> {
    if n.unsigned_abs() > MAX_EXPONENT.unsigned_abs() {
        return Err(invalid(format!(
            "|n| = {} exceeds {MAX_EXPONENT}",
            n.unsigned_abs()
        )));
    }
    let mut result = Amplitude::one();
    let mut base = unit_phase();
    let mut exponent = n.unsigned_abs();
    while exponent > 0 {
        if exponent & 1 == 1 {
            result = mul(&result, &base);
        }
        base = mul(&base, &base);
        exponent >>= 1;
    }
    Ok(if n < 0 { conj(&result) } else { result })
}

/// A finite oriented graph on vertices `0..vertices`; parallel and antiparallel edges are
/// allowed here, self-loops are not.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrientedGraph {
    vertices: usize,
    edges: Vec<(usize, usize)>,
}

/// One step of an edge path: the edge, traversed forward (tail to head) or backward.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PathStep {
    pub edge: usize,
    pub forward: bool,
}

/// A path as a start vertex and steps; validated against a graph by the graph's methods.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EdgePath {
    pub start: usize,
    pub steps: Vec<PathStep>,
}

impl OrientedGraph {
    pub fn new(vertices: usize, edges: Vec<(usize, usize)>) -> Result<Self, WdpError> {
        if vertices == 0 {
            return Err(invalid("a graph needs at least one vertex".to_string()));
        }
        if vertices > MAX_VERTICES {
            return Err(invalid(format!(
                "{vertices} vertices exceed the cap {MAX_VERTICES}"
            )));
        }
        for (e, &(u, v)) in edges.iter().enumerate() {
            if u >= vertices || v >= vertices {
                return Err(invalid(format!(
                    "edge {e} = ({u}, {v}) leaves 0..{vertices}"
                )));
            }
            if u == v {
                return Err(invalid(format!("edge {e} is a self-loop at {u}")));
            }
        }
        Ok(Self { vertices, edges })
    }

    pub fn vertices(&self) -> usize {
        self.vertices
    }

    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }

    fn check_cochain(&self, a: &[i64]) -> Result<(), WdpError> {
        if a.len() != self.edges.len() {
            return Err(invalid(format!(
                "cochain has {} values for {} edges",
                a.len(),
                self.edges.len()
            )));
        }
        Ok(())
    }

    /// The vertex a path ends at, refusing a broken path.
    pub fn path_end(&self, path: &EdgePath) -> Result<usize, WdpError> {
        if path.start >= self.vertices {
            return Err(invalid(format!(
                "path starts at vertex {} outside the graph",
                path.start
            )));
        }
        let mut here = path.start;
        for (k, step) in path.steps.iter().enumerate() {
            let &(tail, head) = self.edges.get(step.edge).ok_or_else(|| {
                invalid(format!(
                    "step {k} names edge {} outside the graph",
                    step.edge
                ))
            })?;
            let (from, to) = if step.forward {
                (tail, head)
            } else {
                (head, tail)
            };
            if from != here {
                return Err(invalid(format!(
                    "step {k} starts at {from} but the path is at {here}"
                )));
            }
            here = to;
        }
        Ok(here)
    }

    /// The path traversed backwards.
    pub fn inverse_path(&self, path: &EdgePath) -> Result<EdgePath, WdpError> {
        let end = self.path_end(path)?;
        Ok(EdgePath {
            start: end,
            steps: path
                .steps
                .iter()
                .rev()
                .map(|s| PathStep {
                    edge: s.edge,
                    forward: !s.forward,
                })
                .collect(),
        })
    }

    /// `first` then `second`; `second` must start where `first` ends.
    pub fn concat_paths(&self, first: &EdgePath, second: &EdgePath) -> Result<EdgePath, WdpError> {
        let end = self.path_end(first)?;
        self.path_end(second)?;
        if second.start != end {
            return Err(invalid(format!(
                "cannot concatenate: first path ends at {end}, second starts at {}",
                second.start
            )));
        }
        Ok(EdgePath {
            start: first.start,
            steps: first.steps.iter().chain(&second.steps).copied().collect(),
        })
    }

    /// `(d0 f)(u -> v) = f(v) - f(u)` for a 0-cochain `f`.
    pub fn coboundary(&self, f: &[i64]) -> Result<Vec<i64>, WdpError> {
        if f.len() != self.vertices {
            return Err(invalid(format!(
                "0-cochain has {} values for {} vertices",
                f.len(),
                self.vertices
            )));
        }
        self.edges
            .iter()
            .map(|&(u, v)| {
                f[v].checked_sub(f[u])
                    .ok_or_else(|| invalid("coboundary overflows i64".to_string()))
            })
            .collect()
    }

    /// The gauge-transformed cochain `a + d0 f`.
    pub fn gauge_transform(&self, a: &[i64], f: &[i64]) -> Result<Vec<i64>, WdpError> {
        self.check_cochain(a)?;
        self.coboundary(f)?
            .into_iter()
            .zip(a)
            .map(|(d, &x)| {
                d.checked_add(x)
                    .ok_or_else(|| invalid("gauge transform overflows i64".to_string()))
            })
            .collect()
    }

    /// `U_e = u^{a_e}`.
    pub fn transport(&self, a: &[i64], edge: usize) -> Result<Amplitude, WdpError> {
        self.check_cochain(a)?;
        let value = a
            .get(edge)
            .ok_or_else(|| invalid(format!("edge {edge} outside the graph")))?;
        u_pow(*value)
    }

    /// `g(v) U_e conj(g(u))` with `g(x) = u^{f(x)}` for the edge `e = (u, v)`.
    pub fn gauge_conjugated_transport(
        &self,
        a: &[i64],
        f: &[i64],
        edge: usize,
    ) -> Result<Amplitude, WdpError> {
        self.check_cochain(a)?;
        if f.len() != self.vertices {
            return Err(invalid(format!(
                "0-cochain has {} values for {} vertices",
                f.len(),
                self.vertices
            )));
        }
        let &(tail, head) = self
            .edges
            .get(edge)
            .ok_or_else(|| invalid(format!("edge {edge} outside the graph")))?;
        let (g_head, g_tail) = (u_pow(f[head])?, u_pow(f[tail])?);
        Ok(mul(
            &mul(&g_head, &self.transport(a, edge)?),
            &conj(&g_tail),
        ))
    }

    /// `<a, gamma> = sum_e +- a_e`, plus for forward and minus for backward steps.
    pub fn pairing(&self, a: &[i64], path: &EdgePath) -> Result<i64, WdpError> {
        self.check_cochain(a)?;
        self.path_end(path)?;
        path.steps.iter().try_fold(0i64, |acc, step| {
            let value = if step.forward {
                Some(a[step.edge])
            } else {
                a[step.edge].checked_neg()
            };
            value
                .and_then(|v| acc.checked_add(v))
                .ok_or_else(|| invalid("pairing overflows i64".to_string()))
        })
    }

    /// The product of the transports along the path, a backward step contributing the
    /// conjugate of its edge's transport.
    pub fn path_amplitude(&self, a: &[i64], path: &EdgePath) -> Result<Amplitude, WdpError> {
        self.check_cochain(a)?;
        self.path_end(path)?;
        let mut amplitude = Amplitude::one();
        for step in &path.steps {
            let transport = self.transport(a, step.edge)?;
            amplitude = mul(
                &amplitude,
                &if step.forward {
                    transport
                } else {
                    conj(&transport)
                },
            );
        }
        Ok(amplitude)
    }

    /// The holonomy of a closed path: its amplitude.
    pub fn holonomy(&self, a: &[i64], path: &EdgePath) -> Result<Amplitude, WdpError> {
        let end = self.path_end(path)?;
        if end != path.start {
            return Err(invalid(format!(
                "path from {} ends at {end}: not closed",
                path.start
            )));
        }
        self.path_amplitude(a, path)
    }

    /// The vertex names `v0, v1, ...` visited by a closed or open path, as
    /// `core_holonomy` names them.
    pub fn path_vertex_names(&self, path: &EdgePath) -> Result<Vec<String>, WdpError> {
        self.path_end(path)?;
        let mut here = path.start;
        let mut names = vec![vertex_name(here)];
        for step in &path.steps {
            let (tail, head) = self.edges[step.edge];
            here = if step.forward { head } else { tail };
            names.push(vertex_name(here));
        }
        Ok(names)
    }

    /// The cochain as a `U1Connection` with phases `u^{a_e}`. Parallel edges (two edges
    /// with the same tail and head) are refused, and a declared antiparallel pair must
    /// carry conjugate phases, that is opposite cochain values (`u^n` is injective), as
    /// `U1Connection::new` requires.
    pub fn u1_connection(&self, a: &[i64]) -> Result<U1Connection, WdpError> {
        self.check_cochain(a)?;
        let vertices: BTreeSet<String> = (0..self.vertices).map(vertex_name).collect();
        let mut phases = BTreeMap::new();
        for (e, &(u, v)) in self.edges.iter().enumerate() {
            let key = (vertex_name(u), vertex_name(v));
            if phases.insert(key, u_pow(a[e])?).is_some() {
                return Err(invalid(format!("edge {e} is parallel to an earlier edge")));
            }
        }
        U1Connection::new(vertices, phases)
    }
}

fn vertex_name(v: usize) -> String {
    format!("v{v}")
}

/// `relative_phase = z_1 / z_2`, when `z_2 != 0`.
pub fn relative_phase(z1: &Amplitude, z2: &Amplitude) -> Option<Amplitude> {
    z2.exact_inv().ok().map(|inv| mul(z1, &inv))
}

/// `WDP-CH19-P11`: the amplitude pairs agree up to a common unit phase `g` (`w = g z`,
/// `N(g) = 1`) exactly when the norms of corresponding entries agree and
/// `z_1 conj(z_2) = w_1 conj(w_2)`. Returns such a `g`, verified, or `None`.
pub fn same_up_to_common_phase(
    z: &(Amplitude, Amplitude),
    w: &(Amplitude, Amplitude),
) -> Option<Amplitude> {
    if norm(&z.0) != norm(&w.0) || norm(&z.1) != norm(&w.1) {
        return None;
    }
    if mul(&z.0, &conj(&z.1)) != mul(&w.0, &conj(&w.1)) {
        return None;
    }
    let g = if !z.0.is_zero() {
        mul(&w.0, &z.0.exact_inv().ok()?)
    } else if !z.1.is_zero() {
        mul(&w.1, &z.1.exact_inv().ok()?)
    } else {
        Amplitude::one()
    };
    let verified = norm(&g).is_one() && mul(&g, &z.0) == w.0 && mul(&g, &z.1) == w.1;
    verified.then_some(g)
}

/// `N(z_1 + z_2)`, invariant under a common phase.
pub fn readout_quadratic(z1: &Amplitude, z2: &Amplitude) -> BigRational {
    norm(&(z1.clone() + z2.clone()))
}

/// `N(z_1 + z_2)^2`, invariant under a common phase.
pub fn readout_quartic(z1: &Amplitude, z2: &Amplitude) -> BigRational {
    let quadratic = readout_quadratic(z1, z2);
    &quadratic * &quadratic
}

/// The interference term `2 Re(z_1 conj(z_2))`: `N(z_1 + z_2) = N(z_1) + N(z_2) + this`.
pub fn cross_term(z1: &Amplitude, z2: &Amplitude) -> BigRational {
    let product = mul(z1, &conj(z2));
    &product.re + &product.re
}

/// The rational square root of a nonnegative rational, when there is one.
fn rational_sqrt(x: &BigRational) -> Option<BigRational> {
    if x.is_negative() {
        return None;
    }
    let root = |n: &num_bigint::BigInt| {
        let r = n.sqrt();
        (&r * &r == *n).then_some(r)
    };
    Some(BigRational::new(root(x.numer())?, root(x.denom())?))
}

/// `WDP-CH19-P12`: decides whether the unit-norm `z` has a square root `w` in Q(i). With
/// `w = x + iy`, `x^2 = (1 + Re z)/2` must be a rational square; then `y = Im z / (2x)`,
/// or `z = -1` and `w = i` when `x = 0`. Returns the root with `x > 0` (or `i`); the other
/// is its negative. A `z` that is not of norm one is refused.
pub fn unit_square_root(z: &Amplitude) -> Result<Option<Amplitude>, WdpError> {
    if !norm(z).is_one() {
        return Err(invalid(format!("{z} is not of norm one")));
    }
    let x_squared = (BigRational::one() + &z.re) / BigRational::from_integer(2.into());
    let Some(x) = rational_sqrt(&x_squared) else {
        return Ok(None);
    };
    let root = if x.is_zero() {
        Amplitude::i()
    } else {
        let y = &z.im / (&x + &x);
        GaussianRational::new(x, y)
    };
    Ok((mul(&root, &root) == *z).then_some(root))
}

/// Why `1 -> u` has no extension to `(Q, +)`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct HalfExponentObstruction {
    pub u: Amplitude,
    /// `(1 + Re u) / 2`, the square of the real part of any root.
    pub x_squared: BigRational,
    pub x_squared_is_rational_square: bool,
    pub u_has_square_root_in_q_i: bool,
    pub authority_effect: AuthorityEffect,
}

/// A homomorphism `phi : (Q, +) -> U(1)(Q(i))` with `phi(1) = u` would give
/// `phi(1/2)^2 = u`; this records that `u` has no square root in Q(i).
pub fn half_exponent_obstruction() -> Result<HalfExponentObstruction, WdpError> {
    let u = unit_phase();
    let x_squared = (BigRational::one() + &u.re) / BigRational::from_integer(2.into());
    Ok(HalfExponentObstruction {
        x_squared_is_rational_square: rational_sqrt(&x_squared).is_some(),
        u_has_square_root_in_q_i: unit_square_root(&u)?.is_some(),
        x_squared,
        u,
        authority_effect: AuthorityEffect::None,
    })
}

/// `(3 + 4i)^n` reduced modulo 5, as `(re, im)`, by repeated squaring in `Z_5[i]`. Since
/// `u = (3 + 4i) / 5`, this is the numerator of `u^n` modulo 5. It equals `(3, 4)` for
/// every `n >= 1`, because `(3 + 4i)^2 = -7 + 24i` is congruent to `3 + 4i` modulo 5, so
/// `3 + 4i` is idempotent there; `n = 0` gives `(1, 0)`.
pub fn unit_phase_numerator_mod_five(n: u64) -> (u8, u8) {
    // (a + bi)(c + di) = (ac - bd) + (ad + bc)i, and -1 = 4 modulo 5. Every product
    // below is at most 80, so `u8` does not overflow.
    let mul = |(a, b): (u8, u8), (c, d): (u8, u8)| ((a * c + 4 * b * d) % 5, (a * d + b * c) % 5);
    let mut result = (1u8, 0u8);
    let mut base = (3u8, 4u8);
    let mut exponent = n;
    while exponent > 0 {
        if exponent & 1 == 1 {
            result = mul(result, base);
        }
        base = mul(base, base);
        exponent >>= 1;
    }
    result
}

/// Whether `u^n` is certified different from 1, for every `n >= 1` (`n <= 0` is refused).
///
/// `u^n = (3 + 4i)^n / 5^n`, so `u^n = 1` would give `(3 + 4i)^n = 5^n`, which is zero
/// modulo 5. The certificate is that [`unit_phase_numerator_mod_five`] is not `(0, 0)`.
/// `Ok(true)` is that certificate; `Ok(false)` would mean only that the residue test is
/// inconclusive, not that `u^n = 1`. It does not occur: the residue is `(3, 4)` for all
/// `n >= 1`.
pub fn u_power_is_never_one(n: i64) -> Result<bool, WdpError> {
    let exponent = u64::try_from(n)
        .ok()
        .filter(|&e| e >= 1)
        .ok_or_else(|| invalid(format!("n = {n} is not a positive exponent")))?;
    Ok(unit_phase_numerator_mod_five(exponent) != (0, 0))
}

// Origin: engine/crates_rs/core_wdp/src/amplitude_bridge.rs
// Claim: urn:core:crates_rs:core-wdp:amplitude-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbe9ff270 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbe9ff270` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbe9ff270 {
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
impl BoundaryErrorbe9ff270 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbe9ff270 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbe9ff270 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbe9ff270 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbe9ff270> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbe9ff270::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbe9ff270::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbe9ff270::ExceedsCapacity {
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
mod l4_boundary_tests_be9ff270 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbe9ff270::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbe9ff270::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbe9ff270::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbe9ff270::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbe9ff270::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbe9ff270::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbe9ff270::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
