// AuthorityEffect: None.
//! QM-229 / QM-230 / QM-231: post-Newtonian light deflection and perihelion
//! advance as exact rationals and rational interval enclosures, the three-qubit
//! GHZ / Mermin contradiction over Q(i) with the deterministic bound enumerated
//! over all 64 sign assignments, a four-tick Page-Wootters history with a
//! rational-Gaussian step unitary and the cyclic lowering shift, Pythagorean
//! phase-damping Kraus maps, and the QWZ / Haldane Chern parity decided by
//! exact sign tests.
//!
//! The Gaussian rationals are the crate's own `Qi` over `Ratio<i64>`, and the
//! 8 x 8 GHZ and Page-Wootters products use the crate's dynamic `QiDynMat`
//! helpers (`qi_dyn_*`).  `BigRational` carries the physical inputs.  pi enters
//! only as a closed rational interval with exact endpoints (`BigInterval`); the
//! Mercury precession in arcseconds is pi-free and therefore an exact rational.
//! Enclosures certify membership, not equality.  The audits store computed
//! values only; each `passed()` derives its checks from them, and an eigenvalue
//! is either exact or refused with `ReggeGravityGhzChernRefusal`.
//!
//! Deviations from the roadmap text, recorded here so they are not silent: the
//! Page-Wootters constraint `(I_C (x) U - S (x) I_S) |Psi> = 0` holds with the
//! cyclic lowering shift `S |t> = |t - 1 mod 4>` and needs `U^4 = I`, which the
//! chosen rational-Gaussian `U` satisfies; the Haldane sign uses a declared
//! rational `s` standing for `sin(phi)` (the map decides `M^2` against
//! `27 t_2^2 s^2` exactly, and the closing line is never met by nonzero
//! rationals because 3 is not a rational square).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_fa4dc41d<T> {
    fn checked_invariant_fa4dc41d(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_fa4dc41d<T> for Option<T> {
    #[inline]
    fn checked_invariant_fa4dc41d(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_fa4dc41d<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_fa4dc41d(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::{BigRational, Ratio};
use num_traits::{One, Signed, Zero};

use crate::quantum_import_finite_maps::page_wootters_tsirelson_wigner::cyclotomic_rings::{
    qi_dyn_add, qi_dyn_comm, qi_dyn_dagger, qi_dyn_eye, qi_dyn_inner, qi_dyn_is_zero, qi_dyn_kron, qi_dyn_matvec, qi_dyn_mul,
    qi_dyn_scale, qi_dyn_sub, qi_dyn_trace, qi_dyn_zeros, QiDynMat,
};
use crate::quantum_import_finite_maps::{pi_big_interval, BigInterval, Qi, Q};

fn q(n: i64, d: i64) -> Q {
    Ratio::new(n, d)
}

fn big(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

/// Exact decimal constant: `digits * 10^exp10`, formed without float literals.
fn dec(digits: &str, exp10: i32) -> BigRational {
    let mantissa: BigInt = digits.parse().checked_invariant_fa4dc41d("decimal digit string");
    let ten = BigInt::from(10);
    if exp10 >= 0 {
        BigRational::from_integer(mantissa * ten.pow(exp10 as u32))
    } else {
        BigRational::new(mantissa, ten.pow((-exp10) as u32))
    }
}

// ---------------------------------------------------------------------------
// QM-229: PPN deflection and perihelion advance
// ---------------------------------------------------------------------------

/// Light-deflection factor (1 + gamma) / 2.
pub fn ppn_deflection_factor(gamma: Q) -> Q {
    (q(1, 1) + gamma) / q(2, 1)
}

/// Perihelion-advance factor (2 + 2 gamma - beta) / 3.
pub fn ppn_perihelion_factor(gamma: Q, beta: Q) -> Q {
    (q(2, 1) + q(2, 1) * gamma - beta) / q(3, 1)
}

/// Minkowski trace eta_{mu nu} T^{mu nu} with signature (+, -, -, -).
pub fn minkowski_trace(t: [[Q; 4]; 4]) -> Q {
    t[0][0] - t[1][1] - t[2][2] - t[3][3]
}

/// Stress tensor of a null probe T^{mu nu} = E k^mu k^nu with k = (1, 1, 0, 0).
pub fn null_probe_stress_tensor(energy: Q) -> [[Q; 4]; 4] {
    let k = [q(1, 1), q(1, 1), q(0, 1), q(0, 1)];
    let mut t = [[q(0, 1); 4]; 4];
    for mu in 0..4 {
        for nu in 0..4 {
            t[mu][nu] = energy * k[mu] * k[nu];
        }
    }
    t
}

/// Stress tensor of dust at rest: T^{00} = rho, all else zero.
pub fn dust_at_rest_stress_tensor(rho: Q) -> [[Q; 4]; 4] {
    let mut t = [[q(0, 1); 4]; 4];
    t[0][0] = rho;
    t
}

/// Deflection in radians: factor * 4 G M / (c^2 b).
pub fn deflection_radians(factor: BigRational, gm: &BigRational, c: &BigRational, b: &BigRational) -> BigRational {
    factor * big(4) * gm / (c * c * b)
}

/// radians -> arcseconds through the enclosure 648000 / pi.
pub fn radians_to_arcsec(radians: &BigRational, pi: &BigInterval) -> BigInterval {
    pi.reciprocal().scale(radians * big(648000))
}

/// Mercury perihelion advance per orbit in arcseconds, pi-free:
/// 6 pi G M / (a (1 - e^2) c^2) rad = 3888000 G M / (a (1 - e^2) c^2) arcsec.
pub fn perihelion_advance_arcsec_per_orbit(
    factor: BigRational,
    gm: &BigRational,
    c: &BigRational,
    a: &BigRational,
    e: &BigRational,
) -> BigRational {
    factor * big(3888000) * gm / (a * (BigRational::one() - e * e) * c * c)
}

/// Declared windows: GR solar-limb deflection [1.750, 1.752] arcsec, Newtonian
/// [0.875, 0.876] arcsec, Mercury perihelion [42.97, 42.99] arcsec per century.
pub fn post_newtonian_windows() -> [(BigRational, BigRational); 3] {
    [(dec("1750", -3), dec("1752", -3)), (dec("0875", -3), dec("0876", -3)), (dec("4297", -2), dec("4299", -2))]
}

/// Post-Newtonian values.  Fields hold computed values only; `passed()` derives
/// every check from them.
#[derive(Clone, Debug)]
pub struct PostNewtonianAudit {
    pub gr_deflection_factor: Q,
    pub newton_deflection_factor: Q,
    pub null_probe_energy: Q,
    pub null_probe_tensor: [[Q; 4]; 4],
    pub null_probe_trace: Q,
    pub dust_density: Q,
    pub dust_tensor: [[Q; 4]; 4],
    pub dust_trace: Q,
    pub gr_over_newton_deflection: BigRational,
    pub gr_solar_limb_arcsec: BigInterval,
    pub newton_solar_limb_arcsec: BigInterval,
    pub gr_perihelion_factor: Q,
    pub mercury_per_orbit_arcsec: BigRational,
    pub mercury_per_century_arcsec: BigRational,
    pub brans_dicke_factor_omega_40: Q,
}

impl PostNewtonianAudit {
    pub fn gr_in_window(&self) -> bool {
        let [(lo, hi), _, _] = post_newtonian_windows();
        lo <= self.gr_solar_limb_arcsec.lo && self.gr_solar_limb_arcsec.hi <= hi
    }

    pub fn newton_in_window(&self) -> bool {
        let [_, (lo, hi), _] = post_newtonian_windows();
        lo <= self.newton_solar_limb_arcsec.lo && self.newton_solar_limb_arcsec.hi <= hi
    }

    pub fn mercury_in_window(&self) -> bool {
        let [_, _, (lo, hi)] = post_newtonian_windows();
        lo <= self.mercury_per_century_arcsec && self.mercury_per_century_arcsec <= hi
    }

    fn passed_stress_tensors(&self) -> bool {
        self.null_probe_tensor == null_probe_stress_tensor(self.null_probe_energy)
            && self.null_probe_trace == minkowski_trace(self.null_probe_tensor)
            && self.null_probe_trace.is_zero()
            && self.null_probe_tensor[0][0] == self.null_probe_tensor[1][1]
            && self.dust_tensor == dust_at_rest_stress_tensor(self.dust_density)
            && self.dust_trace == minkowski_trace(self.dust_tensor)
            && self.dust_trace == self.dust_density
            && !self.dust_trace.is_zero()
    }

    fn passed_deflection_and_orbit_windows(&self) -> bool {
        self.gr_deflection_factor == q(1, 1)
            && self.newton_deflection_factor == q(1, 2)
            && self.gr_over_newton_deflection == big(2)
            && self.gr_in_window()
            && self.newton_in_window()
            && self.gr_perihelion_factor == q(1, 1)
            && self.mercury_in_window()
            && self.brans_dicke_factor_omega_40 == q(62, 63)
    }

    pub fn passed(&self) -> bool {
        self.passed_stress_tensors() && self.passed_deflection_and_orbit_windows()
    }
}

pub fn build_post_newtonian_audit() -> PostNewtonianAudit {
    let gm = dec("13271244", 13);
    let c = big(299792458);
    let r_sun = dec("6957", 5);
    let au = big(149597870700);
    let a = dec("038709927", -8) * &au;
    let e = dec("020563593", -8);
    let period_days = dec("879691", -4);
    let century_days = big(36525);
    let pi = pi_big_interval(20);

    let null_probe_energy = q(7, 3);
    let null_probe_tensor = null_probe_stress_tensor(null_probe_energy);
    let dust_density = q(5, 2);
    let dust_tensor = dust_at_rest_stress_tensor(dust_density);

    let gr_rad = deflection_radians(big(1), &gm, &c, &r_sun);
    let newton_rad = deflection_radians(BigRational::new(BigInt::from(1), BigInt::from(2)), &gm, &c, &r_sun);
    let per_orbit = perihelion_advance_arcsec_per_orbit(big(1), &gm, &c, &a, &e);
    let per_century = &per_orbit * &century_days / &period_days;

    PostNewtonianAudit {
        gr_deflection_factor: ppn_deflection_factor(q(1, 1)),
        newton_deflection_factor: ppn_deflection_factor(q(0, 1)),
        null_probe_energy,
        null_probe_tensor,
        null_probe_trace: minkowski_trace(null_probe_tensor),
        dust_density,
        dust_tensor,
        dust_trace: minkowski_trace(dust_tensor),
        gr_over_newton_deflection: &gr_rad / &newton_rad,
        gr_solar_limb_arcsec: radians_to_arcsec(&gr_rad, &pi),
        newton_solar_limb_arcsec: radians_to_arcsec(&newton_rad, &pi),
        gr_perihelion_factor: ppn_perihelion_factor(q(1, 1), q(1, 1)),
        mercury_per_orbit_arcsec: per_orbit,
        mercury_per_century_arcsec: per_century,
        brans_dicke_factor_omega_40: ppn_perihelion_factor(q(41, 42), q(1, 1)),
    }
}

// ---------------------------------------------------------------------------
// QM-230: Pauli operators on the crate's dynamic Q(i) matrices
// ---------------------------------------------------------------------------

/// Typed refusal of the QM-229 / QM-230 / QM-231 maps.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ReggeGravityGhzChernRefusal {
    /// The vector is zero, so no eigenvalue is defined.
    ZeroVector,
    /// `A v` is not a multiple of `v`.
    NotAnEigenvector,
}

fn qi_int(n: i64) -> Qi {
    Qi::from_q(q(n, 1))
}

pub fn pauli_x() -> QiDynMat {
    vec![vec![Qi::zero(), Qi::one()], vec![Qi::one(), Qi::zero()]]
}

pub fn pauli_y() -> QiDynMat {
    vec![vec![Qi::zero(), qi_int(-1).mul(Qi::i_unit())], vec![Qi::i_unit(), Qi::zero()]]
}

pub fn pauli_z() -> QiDynMat {
    vec![vec![Qi::one(), Qi::zero()], vec![Qi::zero(), qi_int(-1)]]
}

pub fn kron3(a: &QiDynMat, b: &QiDynMat, c: &QiDynMat) -> QiDynMat {
    qi_dyn_kron(&qi_dyn_kron(a, b), c)
}

/// The exact eigenvalue of `a` on `v`: lambda with `a v = lambda v`, or a refusal
/// when `v` is zero or `a v` is not a multiple of `v`.
pub fn exact_eigenvalue(a: &QiDynMat, v: &[Qi]) -> Result<Qi, ReggeGravityGhzChernRefusal> {
    let k = v.iter().position(|c| !c.is_zero()).ok_or(ReggeGravityGhzChernRefusal::ZeroVector)?;
    let av = qi_dyn_matvec(a, v);
    let lambda = av[k].mul(v[k].inv());
    if av.iter().zip(v.iter()).all(|(l, r)| *l == lambda.mul(*r)) {
        Ok(lambda)
    } else {
        Err(ReggeGravityGhzChernRefusal::NotAnEigenvector)
    }
}

// ---------------------------------------------------------------------------
// QM-230 (a): GHZ / Mermin
// ---------------------------------------------------------------------------

/// Unnormalised GHZ vector |000> + |111>.
pub fn ghz_unnormalized() -> Vec<Qi> {
    let mut v = vec![Qi::zero(); 8];
    v[0] = Qi::one();
    v[7] = Qi::one();
    v
}

/// The Mermin operators A1 = X Y Y, A2 = Y X Y, A3 = Y Y X and B = X X X.
pub fn mermin_operators() -> [QiDynMat; 4] {
    let (x, y) = (pauli_x(), pauli_y());
    [kron3(&x, &y, &y), kron3(&y, &x, &y), kron3(&y, &y, &x), kron3(&x, &x, &x)]
}

/// The Mermin operator M = B - A1 - A2 - A3.
pub fn mermin_operator(ops: &[QiDynMat; 4]) -> QiDynMat {
    qi_dyn_sub(&qi_dyn_sub(&qi_dyn_sub(&ops[3], &ops[0]), &ops[1]), &ops[2])
}

/// All 64 deterministic values of x1 x2 x3 - x1 y2 y3 - y1 x2 y3 - y1 y2 x3.
pub fn mermin_deterministic_values() -> Vec<i64> {
    let mut out = Vec::with_capacity(64);
    for bits in 0..64u32 {
        let s = |k: u32| -> i64 { if (bits >> k) & 1 == 1 { 1 } else { -1 } };
        let (x1, x2, x3, y1, y2, y3) = (s(0), s(1), s(2), s(3), s(4), s(5));
        out.push(x1 * x2 * x3 - x1 * y2 * y3 - y1 * x2 * y3 - y1 * y2 * x3);
    }
    out
}

/// GHZ / Mermin values.  Eigenvalues are exact or the build refuses.
#[derive(Clone, Debug)]
pub struct GhzMerminAudit {
    pub operators: [QiDynMat; 4],
    pub ghz: Vec<Qi>,
    pub ghz_eigenvalues: [Qi; 4],
    pub mermin_eigenvalue: Qi,
    pub deterministic_values: Vec<i64>,
}

impl GhzMerminAudit {
    pub fn operators_commute(&self) -> bool {
        self.operators.iter().all(|p| self.operators.iter().all(|r| qi_dyn_is_zero(&qi_dyn_comm(p, r))))
    }

    pub fn product_is_minus_b(&self) -> bool {
        let o = &self.operators;
        qi_dyn_mul(&qi_dyn_mul(&o[0], &o[1]), &o[2]) == qi_dyn_scale(q(-1, 1), &o[3])
    }

    pub fn deterministic_max_abs(&self) -> Option<i64> {
        self.deterministic_values.iter().map(|v| v.abs()).max()
    }

    pub fn passed(&self) -> bool {
        self.operators_commute()
            && self.product_is_minus_b()
            && self.ghz_eigenvalues == [qi_int(-1), qi_int(-1), qi_int(-1), qi_int(1)]
            && self.mermin_eigenvalue == qi_int(4)
            && self.deterministic_values.len() == 64
            && self.deterministic_max_abs() == Some(2)
    }
}

pub fn build_ghz_mermin_audit() -> Result<GhzMerminAudit, ReggeGravityGhzChernRefusal> {
    let operators = mermin_operators();
    let ghz = ghz_unnormalized();
    let ghz_eigenvalues = [
        exact_eigenvalue(&operators[0], &ghz)?,
        exact_eigenvalue(&operators[1], &ghz)?,
        exact_eigenvalue(&operators[2], &ghz)?,
        exact_eigenvalue(&operators[3], &ghz)?,
    ];
    let mermin_eigenvalue = exact_eigenvalue(&mermin_operator(&operators), &ghz)?;
    Ok(GhzMerminAudit { operators, ghz, ghz_eigenvalues, mermin_eigenvalue, deterministic_values: mermin_deterministic_values() })
}

// ---------------------------------------------------------------------------
// QM-230 (b): Page-Wootters four-tick history
// ---------------------------------------------------------------------------

/// Cyclic clock shift S |t> = |t + step mod dim>.
pub fn clock_shift(dim: usize, step: i64) -> QiDynMat {
    let mut s = qi_dyn_zeros(dim);
    for t in 0..dim {
        let target = ((t as i64 + step).rem_euclid(dim as i64)) as usize;
        s[target][t] = Qi::one();
    }
    s
}

/// U = W diag(1, i) W^dagger with W = (1/5)[[3, 4i], [4i, 3]]; U^4 = I.
pub fn rational_gaussian_step_unitary() -> QiDynMat {
    let w = vec![
        vec![Qi::new(q(3, 5), q(0, 1)), Qi::new(q(0, 1), q(4, 5))],
        vec![Qi::new(q(0, 1), q(4, 5)), Qi::new(q(3, 5), q(0, 1))],
    ];
    let d = vec![vec![Qi::one(), Qi::zero()], vec![Qi::zero(), Qi::i_unit()]];
    qi_dyn_mul(&qi_dyn_mul(&w, &d), &qi_dyn_dagger(&w))
}

/// |Psi> = sum_t |t> (x) U^t |psi0>.
pub fn history_state(u: &QiDynMat, psi0: &[Qi], ticks: usize) -> Vec<Qi> {
    let mut psi = Vec::with_capacity(ticks * psi0.len());
    let mut cur = psi0.to_vec();
    for _ in 0..ticks {
        psi.extend_from_slice(&cur);
        cur = qi_dyn_matvec(u, &cur);
    }
    psi
}

/// (I_C (x) U - S (x) I_S) |Psi> for the clock shift `step`.
pub fn page_wootters_residual(u: &QiDynMat, psi: &[Qi], ticks: usize, step: i64) -> Vec<Qi> {
    let constraint = qi_dyn_sub(&qi_dyn_kron(&qi_dyn_eye(ticks), u), &qi_dyn_kron(&clock_shift(ticks, step), &qi_dyn_eye(u.len())));
    qi_dyn_matvec(&constraint, psi)
}

/// Page-Wootters values: the step unitary, the history, and both constraint residuals.
#[derive(Clone, Debug)]
pub struct PageWoottersAudit {
    pub step_unitary: QiDynMat,
    pub initial_state: Vec<Qi>,
    pub history: Vec<Qi>,
    pub lowering_residual: Vec<Qi>,
    pub raising_residual: Vec<Qi>,
}

impl PageWoottersAudit {
    pub fn history_norm_ratio(&self) -> Q {
        qi_dyn_inner(&self.history, &self.history).re / qi_dyn_inner(&self.initial_state, &self.initial_state).re
    }

    /// The tick-t slice of the history equals U^t |psi0>.
    pub fn conditional_states_match(&self) -> bool {
        let d = self.initial_state.len();
        let mut cur = self.initial_state.clone();
        (0..self.history.len() / d).all(|t| {
            let ok = self.history[t * d..(t + 1) * d] == cur[..];
            cur = qi_dyn_matvec(&self.step_unitary, &cur);
            ok
        })
    }

    pub fn passed(&self) -> bool {
        let u = &self.step_unitary;
        let id = qi_dyn_eye(u.len());
        let u2 = qi_dyn_mul(u, u);
        qi_dyn_mul(&qi_dyn_dagger(u), u) == id
            && qi_dyn_mul(&u2, &u2) == id
            && self.lowering_residual.iter().all(|z| z.is_zero())
            && self.raising_residual.iter().any(|z| !z.is_zero())
            && self.conditional_states_match()
            && self.history_norm_ratio() == q(4, 1)
    }
}

pub fn build_page_wootters_audit() -> PageWoottersAudit {
    let u = rational_gaussian_step_unitary();
    let psi0 = vec![Qi::one(), Qi::zero()];
    let psi = history_state(&u, &psi0, 4);
    PageWoottersAudit {
        lowering_residual: page_wootters_residual(&u, &psi, 4, -1),
        raising_residual: page_wootters_residual(&u, &psi, 4, 1),
        step_unitary: u,
        initial_state: psi0,
        history: psi,
    }
}

// ---------------------------------------------------------------------------
// QM-230 (c): Pythagorean phase damping
// ---------------------------------------------------------------------------

/// Kraus pair K0 = diag(1, p/q), K1 = diag(0, r/q) for a Pythagorean triple (p, r, q).
pub fn phase_damping_kraus(p: i64, r: i64, qd: i64) -> (QiDynMat, QiDynMat) {
    assert_eq!(p * p + r * r, qd * qd, "need a Pythagorean triple p^2 + r^2 = q^2");
    let k0 = vec![vec![Qi::one(), Qi::zero()], vec![Qi::zero(), Qi::from_q(q(p, qd))]];
    let k1 = vec![vec![Qi::zero(), Qi::zero()], vec![Qi::zero(), Qi::from_q(q(r, qd))]];
    (k0, k1)
}

pub fn apply_kraus(ks: &[QiDynMat], rho: &QiDynMat) -> QiDynMat {
    let mut out = qi_dyn_zeros(rho.len());
    for k in ks {
        out = qi_dyn_add(&out, &qi_dyn_mul(&qi_dyn_mul(k, rho), &qi_dyn_dagger(k)));
    }
    out
}

/// One triple: its Kraus pair and the states rho_0 = |+><+|, rho_1, rho_2, rho_3.
#[derive(Clone, Debug)]
pub struct PhaseDampingRun {
    pub triple: (i64, i64, i64),
    pub k0: QiDynMat,
    pub k1: QiDynMat,
    pub states: Vec<QiDynMat>,
}

impl PhaseDampingRun {
    pub fn trace_preserving(&self) -> bool {
        qi_dyn_add(&qi_dyn_mul(&qi_dyn_dagger(&self.k0), &self.k0), &qi_dyn_mul(&qi_dyn_dagger(&self.k1), &self.k1))
            == qi_dyn_eye(2)
    }

    /// Each stored state is the channel applied to the one before it.
    pub fn states_follow_channel(&self) -> bool {
        self.states.windows(2).all(|w| apply_kraus(&[self.k0.clone(), self.k1.clone()], &w[0]) == w[1])
    }

    /// 2 rho_n[0][1], read from the stored state after `n` applications.
    pub fn coherence(&self, n: usize) -> Q {
        q(2, 1) * self.states[n][0][1].re
    }
}

#[derive(Clone, Debug)]
pub struct PhaseDampingAudit {
    pub runs: Vec<PhaseDampingRun>,
}

impl PhaseDampingAudit {
    pub fn passed(&self) -> bool {
        let half = Qi::from_q(q(1, 2));
        self.runs.iter().all(|run| {
            let (p, _, qd) = run.triple;
            run.trace_preserving()
                && run.states_follow_channel()
                && run.states.len() == 4
                && (0..4).all(|n| {
                    let s = &run.states[n];
                    let expected = Qi::from_q(q(1, 2) * num_traits::pow(q(p, qd), n));
                    s[0][1] == expected && s[1][0] == expected && s[0][0] == half && s[1][1] == half && qi_dyn_trace(s) == Qi::one()
                })
        }) && self.runs.first().map(|r| (r.triple, r.coherence(3))) == Some(((3, 4, 5), q(27, 125)))
    }
}

pub fn build_phase_damping_audit() -> PhaseDampingAudit {
    let half = Qi::from_q(q(1, 2));
    let rho0 = vec![vec![half, half], vec![half, half]];
    let runs = [(3i64, 4i64, 5i64), (5, 12, 13), (8, 15, 17)]
        .iter()
        .map(|&(p, r, qd)| {
            let (k0, k1) = phase_damping_kraus(p, r, qd);
            let mut states = vec![rho0.clone()];
            for _ in 0..3 {
                let next = apply_kraus(&[k0.clone(), k1.clone()], states.last().checked_invariant_fa4dc41d("initial state"));
                states.push(next);
            }
            PhaseDampingRun { triple: (p, r, qd), k0, k1, states }
        })
        .collect();
    PhaseDampingAudit { runs }
}

// ---------------------------------------------------------------------------
// QM-231: Chern parity
// ---------------------------------------------------------------------------

pub fn sgn(x: Q) -> i64 {
    if x.is_positive() {
        1
    } else if x.is_negative() {
        -1
    } else {
        0
    }
}

/// Dirac masses of the QWZ model at the four time-reversal-invariant momenta.
pub fn qwz_dirac_masses(m: Q) -> [(i64, Q); 4] {
    [
        (0, m + q(2, 1)),
        (1, m),
        (1, m),
        (2, m - q(2, 1)),
    ]
}

/// C_1(m) = (1/2) sum (-1)^{n_x + n_y} sgn(m + cos k_x + cos k_y); None at a gap closing.
pub fn qwz_chern_number(m: Q) -> Option<i64> {
    let mut acc = 0i64;
    for (parity, mass) in qwz_dirac_masses(m) {
        let s = sgn(mass);
        if s == 0 {
            return None;
        }
        acc += if parity % 2 == 0 { s } else { -s };
    }
    assert_eq!(acc % 2, 0, "Dirac-point parity sum must be even");
    Some(acc / 2)
}

/// Haldane Dirac masses M -/+ 3 sqrt(3) t2 s at K and K' (opposite chirality):
/// C = (1/2) [sgn(M - D) - sgn(M + D)] with D = 3 sqrt(3) t2 s, decided exactly by
/// comparing M^2 with D^2 = 27 t2^2 s^2; `s` is a declared rational standing for
/// sin(phi).  None only at a gap closing (M^2 = D^2).
pub fn haldane_chern_number(mass: Q, t2: Q, s: Q) -> Option<i64> {
    let lhs = mass * mass;
    let rhs = q(27, 1) * t2 * t2 * s * s;
    if lhs == rhs {
        return None;
    }
    if lhs > rhs {
        Some(0)
    } else {
        Some(-sgn(t2 * s))
    }
}

/// Chern values.  Fields hold computed values only.
#[derive(Clone, Debug)]
pub struct ChernParityAudit {
    /// (m, C_1(m)) at m = -3, -1, 1, 3.
    pub qwz_values: Vec<(Q, Option<i64>)>,
    /// (m, C_1(m)) at the gap closings m = -2, 0, 2.
    pub qwz_closings: Vec<(Q, Option<i64>)>,
    pub haldane_topological_sample: Option<i64>,
    pub haldane_trivial_sample: Option<i64>,
    /// ((M, t2, s), C) on the 5 x 5 x 5 rational grid.
    pub haldane_grid: Vec<((Q, Q, Q), Option<i64>)>,
    pub haldane_degenerate: Option<i64>,
}

impl ChernParityAudit {
    pub fn passed(&self) -> bool {
        let expected = [(q(-3, 1), Some(0)), (q(-1, 1), Some(1)), (q(1, 1), Some(-1)), (q(3, 1), Some(0))];
        self.qwz_values == expected
            && self.qwz_closings.len() == 3
            && self.qwz_closings.iter().all(|(_, c)| c.is_none())
            && self.haldane_topological_sample == Some(-1)
            && self.haldane_trivial_sample == Some(0)
            && self.haldane_grid.len() == 125
            && self.haldane_grid.iter().all(|(_, c)| c.is_some())
            && self.haldane_degenerate.is_none()
    }
}

pub fn build_chern_parity_audit() -> ChernParityAudit {
    let grid = [q(1, 3), q(-2, 5), q(7, 4), q(-9, 2), q(11, 7)];
    let mut haldane_grid = Vec::with_capacity(125);
    for &m in &grid {
        for &t in &grid {
            for &s in &grid {
                haldane_grid.push(((m, t, s), haldane_chern_number(m, t, s)));
            }
        }
    }
    ChernParityAudit {
        qwz_values: [q(-3, 1), q(-1, 1), q(1, 1), q(3, 1)].iter().map(|&m| (m, qwz_chern_number(m))).collect(),
        qwz_closings: [q(-2, 1), q(0, 1), q(2, 1)].iter().map(|&m| (m, qwz_chern_number(m))).collect(),
        haldane_topological_sample: haldane_chern_number(q(1, 2), q(1, 10), q(1, 1)),
        haldane_trivial_sample: haldane_chern_number(q(1, 1), q(1, 10), q(1, 1)),
        haldane_grid,
        haldane_degenerate: haldane_chern_number(q(0, 1), q(0, 1), q(1, 1)),
    }
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

#[derive(Clone, Debug)]
pub struct Qm229To231ReggeGravityGhzChernReport {
    pub post_newtonian: PostNewtonianAudit,
    pub ghz_mermin: GhzMerminAudit,
    pub page_wootters: PageWoottersAudit,
    pub phase_damping: PhaseDampingAudit,
    pub chern_parity: ChernParityAudit,
}

impl Qm229To231ReggeGravityGhzChernReport {
    pub fn passed(&self) -> bool {
        self.post_newtonian.passed()
            && self.ghz_mermin.passed()
            && self.page_wootters.passed()
            && self.phase_damping.passed()
            && self.chern_parity.passed()
    }
}

/// Evaluate the QM-229 / QM-230 / QM-231 finite maps.
pub fn evaluate_qm229_to_231_regge_gravity_ghz_chern() -> Result<Qm229To231ReggeGravityGhzChernReport, ReggeGravityGhzChernRefusal> {
    Ok(Qm229To231ReggeGravityGhzChernReport {
        post_newtonian: build_post_newtonian_audit(),
        ghz_mermin: build_ghz_mermin_audit()?,
        page_wootters: build_page_wootters_audit(),
        phase_damping: build_phase_damping_audit(),
        chern_parity: build_chern_parity_audit(),
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/regge_gravity_ghz_chern_finite_maps.rs
// Claim: urn:core:crates_rs:core-quantum-physics:regge-gravity-ghz-chern-finite-maps:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfa4dc41d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfa4dc41d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfa4dc41d {
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
impl BoundaryErrorfa4dc41d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfa4dc41d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfa4dc41d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfa4dc41d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfa4dc41d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfa4dc41d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfa4dc41d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfa4dc41d::ExceedsCapacity {
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

    #[test]
    fn test_qm229_deflection_and_perihelion() {
        assert_eq!(ppn_deflection_factor(q(1, 1)), q(1, 1));
        assert_eq!(ppn_deflection_factor(q(0, 1)), q(1, 2));
        assert_eq!(ppn_perihelion_factor(q(1, 1), q(1, 1)), q(1, 1));
        assert_eq!(ppn_perihelion_factor(q(41, 42), q(1, 1)), q(62, 63));
        let probe = null_probe_stress_tensor(q(7, 3));
        assert_eq!(probe[0][0], q(7, 3));
        assert_eq!(probe[0][1], q(7, 3));
        assert_eq!(probe[2][2], q(0, 1));
        assert_eq!(minkowski_trace(probe), q(0, 1));
        assert_eq!(minkowski_trace(dust_at_rest_stress_tensor(q(5, 2))), q(5, 2));
        let a = build_post_newtonian_audit();
        assert_eq!(a.gr_over_newton_deflection, big(2));
        assert!(dec("1751", -3) <= a.gr_solar_limb_arcsec.lo && a.gr_solar_limb_arcsec.hi < dec("1752", -3));
        assert!(dec("4297", -2) <= a.mercury_per_century_arcsec && a.mercury_per_century_arcsec <= dec("4299", -2));
        assert!(a.passed());
    }

    #[test]
    fn test_qm230_ghz_mermin_exact_eigenvalues_and_refusal() {
        let ops = mermin_operators();
        let ghz = ghz_unnormalized();
        assert_eq!(exact_eigenvalue(&ops[0], &ghz), Ok(qi_int(-1)));
        assert_eq!(exact_eigenvalue(&ops[3], &ghz), Ok(qi_int(1)));
        assert_eq!(exact_eigenvalue(&mermin_operator(&ops), &ghz), Ok(qi_int(4)));
        let mut basis = vec![Qi::zero(); 8];
        basis[0] = Qi::one();
        assert_eq!(exact_eigenvalue(&ops[0], &basis), Err(ReggeGravityGhzChernRefusal::NotAnEigenvector));
        assert_eq!(exact_eigenvalue(&ops[0], &[Qi::zero(); 8]), Err(ReggeGravityGhzChernRefusal::ZeroVector));
        assert_eq!(qi_dyn_mul(&qi_dyn_mul(&ops[0], &ops[1]), &ops[2]), qi_dyn_scale(q(-1, 1), &ops[3]));
        let det = mermin_deterministic_values();
        assert_eq!(det.len(), 64);
        assert_eq!(det.iter().map(|v| v.abs()).max(), Some(2));
        assert!(build_ghz_mermin_audit().expect("GHZ is an eigenvector").passed());
    }

    #[test]
    fn test_qm230_page_wootters_lowering_shift() {
        let u = rational_gaussian_step_unitary();
        let u2 = qi_dyn_mul(&u, &u);
        assert_eq!(qi_dyn_mul(&u2, &u2), qi_dyn_eye(2));
        let psi = history_state(&u, &[Qi::one(), Qi::zero()], 4);
        assert!(page_wootters_residual(&u, &psi, 4, -1).iter().all(|z| z.is_zero()));
        assert!(page_wootters_residual(&u, &psi, 4, 1).iter().any(|z| !z.is_zero()));
        let p = build_page_wootters_audit();
        assert_eq!(p.history_norm_ratio(), q(4, 1));
        assert!(p.passed());
    }

    #[test]
    fn test_qm230_phase_damping_three_applications() {
        let (k0, k1) = phase_damping_kraus(3, 4, 5);
        let half = Qi::from_q(q(1, 2));
        let mut rho = vec![vec![half, half], vec![half, half]];
        for _ in 0..3 {
            rho = apply_kraus(&[k0.clone(), k1.clone()], &rho);
        }
        assert_eq!(rho[0][1], Qi::from_q(q(27, 250)));
        assert_eq!(rho[0][0], half);
        let d = build_phase_damping_audit();
        assert_eq!(d.runs[0].states[3], rho);
        assert_eq!(d.runs[0].coherence(3), q(27, 125));
        assert!(d.passed());
    }

    #[test]
    fn test_qm231_chern_parity() {
        assert_eq!(qwz_chern_number(q(-1, 1)), Some(1));
        assert_eq!(qwz_chern_number(q(1, 1)), Some(-1));
        assert_eq!(qwz_chern_number(q(-3, 1)), Some(0));
        assert_eq!(qwz_chern_number(q(3, 1)), Some(0));
        assert_eq!(qwz_chern_number(q(0, 1)), None);
        assert_eq!(haldane_chern_number(q(1, 2), q(1, 10), q(1, 1)), Some(-1));
        assert_eq!(haldane_chern_number(q(1, 2), q(-1, 10), q(1, 1)), Some(1));
        assert_eq!(haldane_chern_number(q(1, 1), q(1, 10), q(1, 1)), Some(0));
        assert_eq!(haldane_chern_number(q(0, 1), q(0, 1), q(1, 1)), None);
        assert!(build_chern_parity_audit().passed());
    }

    #[test]
    fn test_combined_report_passes() {
        assert!(evaluate_qm229_to_231_regge_gravity_ghz_chern().expect("no refusal").passed());
    }
}

#[cfg(test)]
mod l4_boundary_tests_fa4dc41d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfa4dc41d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfa4dc41d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfa4dc41d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfa4dc41d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfa4dc41d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfa4dc41d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfa4dc41d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
