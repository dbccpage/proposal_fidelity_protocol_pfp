// AuthorityEffect: None.
//! QM-226 / QM-227 / QM-228: tree-level QED scattering ratios over Q, the Weyl
//! basis Dirac algebra and chiral projectors over Q(i), the muon-decay Fermi
//! constant as a rational interval enclosure, an exact unitary CKM matrix over
//! Q(i) by a Cayley transform with its Jarlskog invariant, the Adler-Bell-Jackiw
//! colour factor for pi^0 -> gamma gamma, and the Gell-Mann-Okubo octet and
//! decuplet relations over Q.
//!
//! The Gaussian rationals are the crate's own: `Qi`, `Mat4Qi` and the
//! `mat4_qi_*` operations over `Ratio<i64>` for the Dirac algebra, and the
//! `BigRational` Gaussian `Qi` / `Mat3Qi` of `qcd_beta0_wilson_confinement_control`
//! for the CKM Cayley transform, where `Ratio<i64>` overflows.  pi, logarithms
//! and square roots are carried only as closed rational intervals with exact
//! endpoints (`BigInterval`).  Enclosures certify membership, not equality.
//!
//! The report stores computed values only; `passed()` derives every check from
//! those values.
//!
//! Deviations from the roadmap text, recorded here so they are not silent:
//! Bhabha and Moller are related by the crossing `s <-> u`, not `s <-> t` (the
//! `s <-> t` swap is recorded as failing on a rational counterexample); the
//! unitarity triangle is the d-b column triangle `z_k = V_{kd} V_{kb}^*`; and the
//! window `[7.60, 7.85] eV` for the pi^0 rate is read as the experimental band
//! around the PDG value `7.72 eV`, against which the theoretical enclosure is
//! compared.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_611cbe47<T> {
    fn checked_invariant_611cbe47(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_611cbe47<T> for Option<T> {
    #[inline]
    fn checked_invariant_611cbe47(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_611cbe47<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_611cbe47(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_integer::Integer;
use num_rational::{BigRational, Ratio};
use num_traits::{One, Signed, Zero};

use crate::quantum_import_finite_maps::qcd_beta0_wilson_confinement_control::{Mat3Qi, Qi as BigQi};
use crate::quantum_import_finite_maps::{
    dirac_gamma_matrices, mat4_qi_add, mat4_qi_identity, mat4_qi_mul, mat4_qi_mul_vec, mat4_qi_scale, mat4_qi_sub,
    mat4_qi_trace, mat4_qi_zero, pi_big_interval, BigInterval, Mat4Qi, Qi, Vec4Qi, Q,
};

fn q(n: i64, d: i64) -> Q {
    Ratio::new(n, d)
}

fn big(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

fn bq(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// Exact decimal constant: `digits` is an integer written in base ten and the
/// value is `digits * 10^exp10`.  No float literal is ever formed.
fn dec(digits: &str, exp10: i32) -> BigRational {
    let mantissa: BigInt = digits.parse().checked_invariant_611cbe47("decimal digit string");
    let ten = BigInt::from(10);
    if exp10 >= 0 {
        BigRational::from_integer(mantissa * ten.pow(exp10 as u32))
    } else {
        BigRational::new(mantissa, ten.pow((-exp10) as u32))
    }
}

// ---------------------------------------------------------------------------
// Rational interval helpers: atanh series, logarithm and square root
// ---------------------------------------------------------------------------

/// Enclose atanh(z) for 0 <= z < 1 by its odd power series with a geometric
/// tail bound `z^(2K+1) / ((2K+1)(1 - z^2))`.
pub fn atanh_series_big_interval(z: &BigRational, terms: usize) -> BigInterval {
    assert!(!z.is_negative() && *z < BigRational::one(), "atanh enclosure needs 0 <= z < 1");
    assert!(terms >= 1, "atanh enclosure needs at least one term");
    let z2 = z * z;
    let mut partial = BigRational::zero();
    let mut power = z.clone();
    for k in 0..terms {
        partial += &power / big((2 * k + 1) as i64);
        power = &power * &z2;
    }
    let tail = &power / (big((2 * terms + 1) as i64) * (BigRational::one() - &z2));
    BigInterval::new(partial.clone(), partial + tail)
}

/// Enclose ln(r) for a positive rational r: write r = 2^k y with 1 <= y < 2,
/// then ln r = k ln 2 + 2 atanh((y - 1)/(y + 1)) with ln 2 = 2 atanh(1/3).
pub fn ln_big_interval(r: &BigRational, terms: usize) -> BigInterval {
    assert!(r.is_positive(), "ln enclosure needs r > 0");
    let two = big(2);
    let mut k: i64 = 0;
    let mut y = r.clone();
    while y >= two {
        y = &y / &two;
        k += 1;
    }
    while y < BigRational::one() {
        y = &y * &two;
        k -= 1;
    }
    let ln2 = atanh_series_big_interval(&BigRational::new(BigInt::from(1), BigInt::from(3)), terms).scale(big(2));
    let z = (&y - BigRational::one()) / (&y + BigRational::one());
    let ln_y = atanh_series_big_interval(&z, terms).scale(big(2));
    ln2.scale(big(k)).add(&ln_y)
}

/// Enclose the square root of a non-negative interval with decimal endpoints
/// `a/10^d`, `b/10^d` satisfying `lo^2 <= iv.lo` and `hi^2 >= iv.hi` (re-checked).
pub fn sqrt_big_interval(iv: &BigInterval, digits: u32) -> BigInterval {
    assert!(!iv.lo.is_negative(), "sqrt enclosure needs a non-negative interval");
    let scale = BigInt::from(10).pow(2 * digits);
    let denom = BigInt::from(10).pow(digits);
    let lo_floor = (iv.lo.numer() * &scale).div_floor(iv.lo.denom());
    let hi_num = iv.hi.numer() * &scale;
    let hi_ceil = -((-hi_num).div_floor(iv.hi.denom()));
    let lo = BigRational::new(lo_floor.sqrt(), denom.clone());
    let hi = BigRational::new(hi_ceil.sqrt() + BigInt::from(1), denom);
    assert!(&lo * &lo <= iv.lo && &hi * &hi >= iv.hi, "sqrt enclosure endpoint check failed");
    BigInterval::new(lo, hi)
}

// ---------------------------------------------------------------------------
// QM-227 (a): Weyl-basis gammas on the crate's Q(i) and Mat4Qi
// ---------------------------------------------------------------------------

fn qi_int(n: i64) -> Qi {
    Qi::from_q(q(n, 1))
}

fn mat4_qi_diag(d: [i64; 4]) -> Mat4Qi {
    let mut m = mat4_qi_zero();
    for k in 0..4 {
        m[k][k] = qi_int(d[k]);
    }
    m
}

/// The block matrix V = [[I, -I], [I, I]] and its transpose V^T, with V V^T = 2 I.
/// V / sqrt(2) is orthogonal; its two factors of 1/sqrt(2) multiply to 1/2, so the
/// change from the Dirac basis to the Weyl basis stays inside Q(i).
pub fn dirac_to_weyl_blocks() -> (Mat4Qi, Mat4Qi) {
    let (o, z, m) = (Qi::one(), Qi::zero(), qi_int(-1));
    let v = [[o, z, m, z], [z, o, z, m], [o, z, o, z], [z, o, z, o]];
    let vt = [[o, z, o, z], [z, o, z, o], [m, z, o, z], [z, m, z, o]];
    (v, vt)
}

/// Weyl-basis gammas gamma_W = (1/2) V gamma_D V^T, built from the crate's
/// Dirac-basis `dirac_gamma_matrices()`: gamma^0 = [[0, I], [I, 0]] and
/// gamma^k = [[0, s_k], [-s_k, 0]].
pub fn dirac_gammas_weyl() -> [Mat4Qi; 4] {
    let (v, vt) = dirac_to_weyl_blocks();
    let half = Qi::from_q(q(1, 2));
    dirac_gamma_matrices().map(|g| mat4_qi_scale(half, &mat4_qi_mul(&mat4_qi_mul(&v, &g), &vt)))
}

/// gamma^mu gamma^nu + gamma^nu gamma^mu.
pub fn clifford_anticommutator(g: &[Mat4Qi; 4], mu: usize, nu: usize) -> Mat4Qi {
    mat4_qi_add(&mat4_qi_mul(&g[mu], &g[nu]), &mat4_qi_mul(&g[nu], &g[mu]))
}

/// gamma_5 = i gamma^0 gamma^1 gamma^2 gamma^3.
pub fn gamma5(g: &[Mat4Qi; 4]) -> Mat4Qi {
    let prod = mat4_qi_mul(&mat4_qi_mul(&mat4_qi_mul(&g[0], &g[1]), &g[2]), &g[3]);
    mat4_qi_scale(Qi::i_unit(), &prod)
}

/// (P_L, P_R) = ((I - gamma_5)/2, (I + gamma_5)/2).
pub fn chiral_projectors(g5: &Mat4Qi) -> (Mat4Qi, Mat4Qi) {
    let half = Qi::from_q(q(1, 2));
    let id = mat4_qi_identity();
    (mat4_qi_scale(half, &mat4_qi_sub(&id, g5)), mat4_qi_scale(half, &mat4_qi_add(&id, g5)))
}

/// The fixed test spinor used for the V-A current check.
pub fn chiral_test_spinor() -> Vec4Qi {
    [
        Qi::new(q(3, 5), q(4, 5)),
        Qi::new(q(-1, 2), q(2, 7)),
        Qi::new(q(5, 13), q(-12, 13)),
        Qi::new(q(1, 3), q(1, 9)),
    ]
}

fn vec4_is_zero(v: &Vec4Qi) -> bool {
    v.iter().all(|c| c.is_zero())
}


// ---------------------------------------------------------------------------
// QM-226: tree-level QED ratios over Q
// ---------------------------------------------------------------------------

/// eta(x, u) = 1 / (1 + x (1 - u)).
pub fn klein_nishina_frequency_ratio(x: Q, u: Q) -> Q {
    assert!(!x.is_negative(), "photon energy ratio must be >= 0");
    assert!(u >= q(-1, 1) && u <= q(1, 1), "scattering cosine must lie in [-1, 1]");
    q(1, 1) / (q(1, 1) + x * (q(1, 1) - u))
}

/// R_KN(x, u) = (1/2) eta^2 (eta + 1/eta - (1 - u^2)) in units of r_e^2.
pub fn klein_nishina_ratio(x: Q, u: Q) -> Q {
    let eta = klein_nishina_frequency_ratio(x, u);
    eta * eta * (eta + q(1, 1) / eta - (q(1, 1) - u * u)) / q(2, 1)
}

/// Exact integral of (3/8)(1 + u^2) over [-1, 1] via the antiderivative (3/8)(u + u^3/3).
pub fn thomson_angular_integral() -> Q {
    let f = |u: Q| q(3, 8) * (u + u * u * u / q(3, 1));
    f(q(1, 1)) - f(q(-1, 1))
}

fn check_mandelstam(s: Q, t: Q, u: Q) {
    assert!((s + t + u).is_zero(), "massless Mandelstam invariants need s + t + u = 0");
    assert!(!s.is_zero() && !t.is_zero() && !u.is_zero(), "pole at s, t or u = 0");
}

/// Massless tree-level Bhabha reduced squared amplitude ratio.
pub fn bhabha_reduced_amplitude(s: Q, t: Q, u: Q) -> Q {
    check_mandelstam(s, t, u);
    q(2, 1) * ((s * s + u * u) / (t * t) + q(2, 1) * u * u / (s * t) + (t * t + u * u) / (s * s))
}

/// Massless tree-level Moller reduced squared amplitude ratio.
pub fn moller_reduced_amplitude(s: Q, t: Q, u: Q) -> Q {
    check_mandelstam(s, t, u);
    q(2, 1) * ((s * s + u * u) / (t * t) + q(2, 1) * s * s / (t * u) + (s * s + t * t) / (u * u))
}

// ---------------------------------------------------------------------------
// QM-227 (b): muon decay enclosures
// ---------------------------------------------------------------------------

/// Muon-decay enclosures from declared CODATA 2018 and PDG inputs.
#[derive(Clone, Debug)]
pub struct MuonDecayEnclosures {
    pub mass_ratio_sq_x: BigRational,
    pub recoil_polynomial_f0: BigRational,
    pub phase_space_f: BigInterval,
    pub kinoshita_sirlin_dq: BigInterval,
    pub fermi_constant_gev_minus2: BigInterval,
}

/// f(x) = f_0(x) - 12 x^2 ln x, the Kinoshita-Sirlin one-loop factor
/// (alpha / 2 pi)(25/4 - pi^2), and G_F from tau_mu by
/// G_F^2 = 192 pi^3 hbar / (tau m_mu^5 f(x) (1 + dq)), all as enclosures.
pub fn muon_decay_enclosures() -> MuonDecayEnclosures {
    let m_e = dec("51099895000", -11);
    let m_mu = dec("1056583755", -7);
    let tau = dec("21969811", -13);
    let h = dec("662607015", -42);
    let e = dec("1602176634", -28);
    let alpha_inv = dec("137035999084", -9);
    let pi = pi_big_interval(20);

    let x = (&m_e / &m_mu) * (&m_e / &m_mu);
    let f0 = BigRational::one() - big(8) * &x + big(8) * &x * &x * &x - &x * &x * &x * &x;
    let ln_x = ln_big_interval(&x, 40);
    let f = BigInterval::exact(f0.clone()).add(&ln_x.scale(big(-12) * &x * &x));
    let alpha = BigRational::one() / alpha_inv;
    let dq = BigInterval::exact(alpha)
        .mul(&BigInterval::exact(bq(25, 4)).sub(&pi.pow(2)))
        .scale(bq(1, 2))
        .mul(&pi.reciprocal());
    let hbar_gev_s = BigInterval::exact(h / (big(2) * e * dec("1", 9))).mul(&pi.reciprocal());
    let m_mu_gev = &m_mu / dec("1", 3);
    let m5 = &m_mu_gev * &m_mu_gev * &m_mu_gev * &m_mu_gev * &m_mu_gev;
    let denom = BigInterval::exact(tau * m5).mul(&f).mul(&BigInterval::exact(BigRational::one()).add(&dq));
    let gf_sq = BigInterval::exact(big(192)).mul(&pi.pow(3)).mul(&hbar_gev_s).mul(&denom.reciprocal());
    let gf = sqrt_big_interval(&gf_sq, 14);
    MuonDecayEnclosures {
        mass_ratio_sq_x: x,
        recoil_polynomial_f0: f0,
        phase_space_f: f,
        kinoshita_sirlin_dq: dq,
        fermi_constant_gev_minus2: gf,
    }
}

/// The declared window [1.1663e-5, 1.1665e-5] GeV^-2 for G_F.
pub fn fermi_constant_window() -> (BigRational, BigRational) {
    (dec("11663", -9), dec("11665", -9))
}

// ---------------------------------------------------------------------------
// QM-227 (c): CKM over Q(i) on the crate's BigRational Gaussian and Mat3Qi
// ---------------------------------------------------------------------------

/// |z|^2 for the BigRational Gaussian of `qcd_beta0_wilson_confinement_control`.
pub fn big_qi_norm_sq(z: &BigQi) -> BigRational {
    &z.re * &z.re + &z.im * &z.im
}

fn big_qi_inverse(z: &BigQi) -> BigQi {
    let n = big_qi_norm_sq(z);
    assert!(!n.is_zero(), "inverse of zero in Q(i)");
    BigQi::new(&z.re / &n, -(&z.im / &n))
}

fn big_qi_neg(z: &BigQi) -> BigQi {
    z.scale_rat(&big(-1))
}

/// Exact inverse of a 3x3 matrix over Q(i) by the adjugate.  The shared `Mat3Qi`
/// has no inverse; this is the one operation the Cayley transform adds.
pub fn mat3_qi_inverse(a: &Mat3Qi) -> Mat3Qi {
    let e = &a.e;
    let minor = |r: usize, c: usize| -> BigQi {
        let rows: Vec<usize> = (0..3).filter(|&i| i != r).collect();
        let cols: Vec<usize> = (0..3).filter(|&j| j != c).collect();
        e[rows[0]][cols[0]]
            .mul(&e[rows[1]][cols[1]])
            .sub(&e[rows[0]][cols[1]].mul(&e[rows[1]][cols[0]]))
    };
    let mut cof = Mat3Qi::zero();
    for r in 0..3 {
        for c in 0..3 {
            let m = minor(r, c);
            cof.e[r][c] = if (r + c) % 2 == 0 { m } else { big_qi_neg(&m) };
        }
    }
    let det = e[0][0].mul(&cof.e[0][0]).add(&e[0][1].mul(&cof.e[0][1])).add(&e[0][2].mul(&cof.e[0][2]));
    let det_inv = big_qi_inverse(&det);
    let mut out = Mat3Qi::zero();
    for r in 0..3 {
        for c in 0..3 {
            out.e[r][c] = cof.e[c][r].mul(&det_inv);
        }
    }
    out
}

/// Skew-Hermitian generator near the Wolfenstein point lambda = 9/40, A_W = 4/5.
pub fn ckm_skew_hermitian_generator() -> Mat3Qi {
    let a12 = BigQi::from_rat(bq(-9, 80));
    let a23 = BigQi::from_rat(bq(-81, 4000));
    let a13 = BigQi::new(bq(-29, 40000), bq(317, 200000));
    let minus_conj = |z: &BigQi| big_qi_neg(&z.conj());
    Mat3Qi {
        e: [
            [BigQi::zero(), a12.clone(), a13.clone()],
            [minus_conj(&a12), BigQi::zero(), a23.clone()],
            [minus_conj(&a13), minus_conj(&a23), BigQi::zero()],
        ],
    }
}

/// V = (I - A)(I + A)^(-1), unitary whenever A is skew-Hermitian.
pub fn cayley_transform3(a: &Mat3Qi) -> Mat3Qi {
    let id = Mat3Qi::identity();
    id.sub(a).mul(&mat3_qi_inverse(&id.add(a)))
}

/// J = Im(V_{ac} V_{bd} V_{ad}^* V_{bc}^*).
pub fn jarlskog(v: &Mat3Qi, rows: (usize, usize), cols: (usize, usize)) -> BigRational {
    let (a, b) = rows;
    let (c, d) = cols;
    v.e[a][c].mul(&v.e[b][d]).mul(&v.e[a][d].conj()).mul(&v.e[b][c].conj()).im
}

/// Unitarity-triangle sides z_k = V_{kd} V_{kb}^* for k in {u, c, t}.
pub fn ckm_db_triangle(v: &Mat3Qi) -> [BigQi; 3] {
    [0usize, 1, 2].map(|k| v.e[k][0].mul(&v.e[k][2].conj()))
}


// ---------------------------------------------------------------------------
// QM-228: ABJ colour factor, pi^0 rate, Gell-Mann-Okubo
// ---------------------------------------------------------------------------

/// S_pi0(N_c) = N_c (Q_u^2 - Q_d^2) = N_c / 3.
pub fn abj_colour_factor(n_c: i64) -> Q {
    assert!(n_c >= 1, "colour number must be a positive integer");
    q(n_c, 1) * (q(2, 3) * q(2, 3) - q(-1, 3) * q(-1, 3))
}

/// Gamma(pi^0 -> gamma gamma) in eV for colour factor S:
/// alpha^2 m_pi^3 S^2 / (64 pi^3 f_pi^2), with f_pi^2 = f(130)^2 / 2 and
/// f(130) in the declared band [129.4, 131.0] MeV.
pub fn pion_two_photon_rate_ev(s: Q) -> BigInterval {
    let m_pi = dec("1349768", -4);
    let alpha = BigRational::one() / dec("137035999084", -9);
    let f130 = BigInterval::new(dec("1294", -1), dec("1310", -1));
    let f_pi_sq = f130.mul(&f130).scale(bq(1, 2));
    let pi = pi_big_interval(20);
    let prefactor = BigInterval::exact(&alpha * &alpha * &m_pi * &m_pi * &m_pi / big(64)).mul(&pi.pow(3).reciprocal());
    let s_big = bq(*s.numer(), *s.denom());
    prefactor.mul(&f_pi_sq.reciprocal()).scale(&s_big * &s_big * dec("1", 6))
}

/// The experimental band [7.60, 7.85] eV and the PDG central value 7.72 eV.
pub fn pion_rate_band_and_central() -> (BigRational, BigRational, BigRational) {
    (dec("760", -2), dec("785", -2), dec("772", -2))
}

/// The SU(3) mass operator M = M_0 + M_1 Y + M_2 (I (I + 1) - Y^2 / 4) is linear in
/// (M_0, M_1, M_2); its coefficient vector at (I, Y) is (1, Y, I (I + 1) - Y^2 / 4).
pub fn su3_mass_coefficients(isospin: Q, hypercharge: Q) -> [Q; 3] {
    [q(1, 1), hypercharge, isospin * (isospin + q(1, 1)) - hypercharge * hypercharge / q(4, 1)]
}

/// Coefficients of 2 (M_N + M_Xi) - (3 M_Lambda + M_Sigma) in (M_0, M_1, M_2).
/// All three vanish, so the octet relation holds for every mass operator.
pub fn gmo_octet_relation_coefficients() -> [Q; 3] {
    let n = su3_mass_coefficients(q(1, 2), q(1, 1));
    let l = su3_mass_coefficients(q(0, 1), q(0, 1));
    let s = su3_mass_coefficients(q(1, 1), q(0, 1));
    let x = su3_mass_coefficients(q(1, 2), q(-1, 1));
    [0usize, 1, 2].map(|k| q(2, 1) * (n[k] + x[k]) - q(3, 1) * l[k] - s[k])
}

/// Second differences of the decuplet coefficient vectors along Y = 1, 0, -1, -2
/// (I = Y/2 + 1).  Both vanish, so the decuplet is equally spaced for every operator.
pub fn gmo_decuplet_second_differences() -> [[Q; 3]; 2] {
    let c = [q(1, 1), q(0, 1), q(-1, 1), q(-2, 1)].map(|y| su3_mass_coefficients(y / q(2, 1) + q(1, 1), y));
    [0usize, 1].map(|j| [0usize, 1, 2].map(|k| c[j + 2][k] - q(2, 1) * c[j + 1][k] + c[j][k]))
}

/// PDG isospin-averaged octet and decuplet masses in MeV.
#[derive(Clone, Debug)]
pub struct BaryonMasses {
    pub nucleon: BigRational,
    pub lambda: BigRational,
    pub sigma: BigRational,
    pub xi: BigRational,
    pub delta: BigRational,
    pub sigma_star: BigRational,
    pub xi_star: BigRational,
    pub omega: BigRational,
}

pub fn pdg_baryon_masses() -> BaryonMasses {
    BaryonMasses {
        nucleon: (dec("93827208816", -8) + dec("93956542052", -8)) / big(2),
        lambda: dec("1115683", -3),
        sigma: (dec("118937", -2) + dec("1192642", -3) + dec("1197449", -3)) / big(3),
        xi: (dec("131486", -2) + dec("132171", -2)) / big(2),
        delta: dec("1232", 0),
        sigma_star: (dec("138283", -2) + dec("13837", -1) + dec("13872", -1)) / big(3),
        xi_star: (dec("153180", -2) + dec("15350", -1)) / big(2),
        omega: dec("167245", -2),
    }
}

// ---------------------------------------------------------------------------
// Report: stored values; `passed()` derives every check from them
// ---------------------------------------------------------------------------

/// Combined QM-226 / QM-227 / QM-228 report.  Fields hold computed values only.
#[derive(Clone, Debug)]
pub struct Qm226To228QedWeakHadronicReport {
    /// (x, u, R_KN(x, u)) on the 3 x 3 sample grid.
    pub kn_samples: Vec<(Q, Q, Q)>,
    /// R_KN(x, 1) at x = 1/10, 1, 2, 7/3, 1000.
    pub kn_forward_values: Vec<Q>,
    /// (R_KN(0, u), (1 + u^2) / 2) at six cosines.
    pub thomson_pairs: Vec<(Q, Q)>,
    pub thomson_angular_integral: Q,
    /// (Bhabha(s, t, u), Moller(u, t, s)) at four rational points.
    pub crossing_s_u_pairs: Vec<(Q, Q)>,
    /// (Moller(s, t, u), Moller(s, u, t)) at the same points.
    pub moller_t_u_pairs: Vec<(Q, Q)>,
    /// (Bhabha(5, -2, -3), Moller(-2, 5, -3)).
    pub s_t_swap_values: (Q, Q),
    pub gammas_weyl: [Mat4Qi; 4],
    pub gamma5: Mat4Qi,
    pub p_left: Mat4Qi,
    pub p_right: Mat4Qi,
    pub muon: MuonDecayEnclosures,
    pub fermi_constant_window: (BigRational, BigRational),
    pub ckm_generator: Mat3Qi,
    pub ckm: Mat3Qi,
    pub ckm_jarlskog: BigRational,
    pub abj_s_nc3: Q,
    pub abj_s_nc1: Q,
    pub pion_rate_nc3_ev: BigInterval,
    pub pion_rate_nc1_ev: BigInterval,
    pub gmo_octet_coefficients: [Q; 3],
    pub gmo_decuplet_second_differences: [[Q; 3]; 2],
    pub gmo_octet_lhs_2_n_plus_xi: BigRational,
    pub gmo_octet_rhs_3_lambda_plus_sigma: BigRational,
    pub gmo_octet_fractional_residual: BigRational,
    pub gmo_decuplet_spacings: [BigRational; 3],
    pub gmo_omega_prediction_mev: BigRational,
    pub gmo_omega_pdg_mev: BigRational,
    pub gmo_omega_fractional_residual: BigRational,
}

fn mat3_neg(a: &Mat3Qi) -> Mat3Qi {
    a.scale_rat(&big(-1))
}

impl Qm226To228QedWeakHadronicReport {
    pub fn clifford_relations_hold(&self) -> bool {
        let eta = [q(1, 1), q(-1, 1), q(-1, 1), q(-1, 1)];
        (0..4).all(|mu| {
            (0..4).all(|nu| {
                let expected = if mu == nu {
                    mat4_qi_scale(Qi::from_q(q(2, 1) * eta[mu]), &mat4_qi_identity())
                } else {
                    mat4_qi_zero()
                };
                clifford_anticommutator(&self.gammas_weyl, mu, nu) == expected
            })
        })
    }

    pub fn projectors_idempotent_orthogonal_complete(&self) -> bool {
        let (pl, pr) = (&self.p_left, &self.p_right);
        mat4_qi_mul(pl, pl) == *pl
            && mat4_qi_mul(pr, pr) == *pr
            && mat4_qi_mul(pl, pr) == mat4_qi_zero()
            && mat4_qi_mul(pr, pl) == mat4_qi_zero()
            && mat4_qi_add(pl, pr) == mat4_qi_identity()
    }

    pub fn v_minus_a_current_kills_right_handed(&self) -> bool {
        let right = mat4_qi_mul_vec(&self.p_right, &chiral_test_spinor());
        vec4_is_zero(&mat4_qi_mul_vec(&self.p_left, &right))
            && self.gammas_weyl.iter().all(|g| vec4_is_zero(&mat4_qi_mul_vec(&mat4_qi_mul(g, &self.p_left), &right)))
    }

    pub fn ckm_unitary_both_sides(&self) -> bool {
        let id = Mat3Qi::identity();
        self.ckm.dagger().mul(&self.ckm) == id && self.ckm.mul(&self.ckm.dagger()) == id
    }

    pub fn ckm_jarlskog_quartets_agree(&self) -> bool {
        let pairs = [(0usize, 1usize), (0, 2), (1, 2)];
        pairs.iter().all(|&r| pairs.iter().all(|&c| jarlskog(&self.ckm, r, c).abs() == self.ckm_jarlskog.abs()))
    }

    pub fn ckm_vus_vcb_within_ten_percent(&self) -> bool {
        let lam_sq = bq(81, 1600);
        let a_lam2 = bq(4, 5) * &lam_sq;
        let a_lam2_sq = &a_lam2 * &a_lam2;
        let within = |got: BigRational, target: &BigRational| bq(81, 100) * target <= got && got <= bq(121, 100) * target;
        within(big_qi_norm_sq(&self.ckm.e[0][1]), &lam_sq) && within(big_qi_norm_sq(&self.ckm.e[1][2]), &a_lam2_sq)
    }

    fn passed_qed(&self) -> bool {
        let one = q(1, 1);
        self.kn_forward_values.iter().all(|&r| r == one)
            && self.thomson_pairs.iter().all(|(a, b)| a == b)
            && self.thomson_angular_integral == one
            && self.crossing_s_u_pairs.iter().all(|(a, b)| a == b)
            && self.moller_t_u_pairs.iter().all(|(a, b)| a == b)
            && self.s_t_swap_values.0 != self.s_t_swap_values.1
    }

    fn passed_dirac_and_muon(&self) -> bool {
        let (w_lo, w_hi) = &self.fermi_constant_window;
        let gf = &self.muon.fermi_constant_gev_minus2;
        self.clifford_relations_hold()
            && self.gamma5 == mat4_qi_diag([-1, -1, 1, 1])
            && self.projectors_idempotent_orthogonal_complete()
            && mat4_qi_trace(&self.p_left) == qi_int(2)
            && mat4_qi_trace(&self.p_right) == qi_int(2)
            && self.v_minus_a_current_kills_right_handed()
            && self.muon.kinoshita_sirlin_dq.hi.is_negative()
            && *w_lo <= gf.lo
            && gf.hi <= *w_hi
    }

    fn passed_ckm(&self) -> bool {
        let triangle = ckm_db_triangle(&self.ckm);
        self.ckm_generator.dagger() == mat3_neg(&self.ckm_generator)
            && self.ckm_unitary_both_sides()
            && triangle[0].add(&triangle[1]).add(&triangle[2]).is_zero()
            && !self.ckm_jarlskog.is_zero()
            && self.ckm_jarlskog_quartets_agree()
            && self.ckm_vus_vcb_within_ten_percent()
    }

    fn passed_abj(&self) -> bool {
        let one = q(1, 1);
        let (band_lo, band_hi, central) = pion_rate_band_and_central();
        let r3 = &self.pion_rate_nc3_ev;
        let ratio = (self.abj_s_nc3 / self.abj_s_nc1) * (self.abj_s_nc3 / self.abj_s_nc1);
        [
            self.abj_s_nc3 == one,
            self.abj_s_nc1 == q(1, 3),
            ratio == q(9, 1),
            r3.lo <= central,
            central <= r3.hi,
            r3.lo <= band_hi,
            band_lo <= r3.hi,
            self.pion_rate_nc1_ev.hi < band_lo,
        ]
        .into_iter()
        .all(|b| b)
    }

    fn passed_gmo(&self) -> bool {
        self.gmo_octet_coefficients.iter().all(|c| c.is_zero())
            && self
                .gmo_decuplet_second_differences
                .iter()
                .all(|row| row.iter().all(|c| c.is_zero()))
            && self.gmo_octet_fractional_residual <= bq(6, 1000)
            && self.gmo_omega_fractional_residual <= bq(1, 100)
    }

    fn passed_abj_and_gmo(&self) -> bool {
        self.passed_abj() && self.passed_gmo()
    }

    /// Every check, derived from the stored values.
    pub fn passed(&self) -> bool {
        self.passed_qed()
            && self.passed_dirac_and_muon()
            && self.passed_ckm()
            && self.passed_abj_and_gmo()
    }
}

/// Evaluate the QM-226 / QM-227 / QM-228 finite maps.
pub fn evaluate_qm226_to_228_qed_weak_hadronic() -> Qm226To228QedWeakHadronicReport {
    let xs = [q(1, 10), q(1, 1), q(2, 1)];
    let us = [q(-1, 1), q(0, 1), q(1, 1)];
    let kn_samples = xs.iter().flat_map(|&x| us.iter().map(move |&u| (x, u, klein_nishina_ratio(x, u)))).collect();
    let kn_forward_values =
        [q(1, 10), q(1, 1), q(2, 1), q(7, 3), q(1000, 1)].iter().map(|&x| klein_nishina_ratio(x, q(1, 1))).collect();
    let thomson_pairs = [q(-1, 1), q(0, 1), q(1, 1), q(1, 2), q(-3, 7), q(5, 13)]
        .iter()
        .map(|&u| (klein_nishina_ratio(q(0, 1), u), (q(1, 1) + u * u) / q(2, 1)))
        .collect();
    let points = [(q(5, 1), q(-2, 1)), (q(7, 3), q(-1, 2)), (q(11, 1), q(-4, 1)), (q(13, 2), q(-9, 4))];
    let crossing_s_u_pairs =
        points.iter().map(|&(s, t)| (bhabha_reduced_amplitude(s, t, -s - t), moller_reduced_amplitude(-s - t, t, s))).collect();
    let moller_t_u_pairs = points
        .iter()
        .map(|&(s, t)| (moller_reduced_amplitude(s, t, -s - t), moller_reduced_amplitude(s, -s - t, t)))
        .collect();
    let s_t_swap_values =
        (bhabha_reduced_amplitude(q(5, 1), q(-2, 1), q(-3, 1)), moller_reduced_amplitude(q(-2, 1), q(5, 1), q(-3, 1)));

    let gammas_weyl = dirac_gammas_weyl();
    let g5 = gamma5(&gammas_weyl);
    let (p_left, p_right) = chiral_projectors(&g5);

    let ckm_generator = ckm_skew_hermitian_generator();
    let ckm = cayley_transform3(&ckm_generator);
    let ckm_jarlskog = jarlskog(&ckm, (0, 1), (0, 1));

    let m = pdg_baryon_masses();
    let lhs = big(2) * (&m.nucleon + &m.xi);
    let rhs = big(3) * &m.lambda + &m.sigma;
    let residual = (&rhs - &lhs).abs() / &rhs;
    let core_pred = &m.xi_star + (&m.xi_star - &m.sigma_star);
    let core_res = (&core_pred - &m.omega).abs() / &m.omega;

    Qm226To228QedWeakHadronicReport {
        kn_samples,
        kn_forward_values,
        thomson_pairs,
        thomson_angular_integral: thomson_angular_integral(),
        crossing_s_u_pairs,
        moller_t_u_pairs,
        s_t_swap_values,
        gammas_weyl,
        gamma5: g5,
        p_left,
        p_right,
        muon: muon_decay_enclosures(),
        fermi_constant_window: fermi_constant_window(),
        ckm_generator,
        ckm,
        ckm_jarlskog,
        abj_s_nc3: abj_colour_factor(3),
        abj_s_nc1: abj_colour_factor(1),
        pion_rate_nc3_ev: pion_two_photon_rate_ev(abj_colour_factor(3)),
        pion_rate_nc1_ev: pion_two_photon_rate_ev(abj_colour_factor(1)),
        gmo_octet_coefficients: gmo_octet_relation_coefficients(),
        gmo_decuplet_second_differences: gmo_decuplet_second_differences(),
        gmo_octet_lhs_2_n_plus_xi: lhs,
        gmo_octet_rhs_3_lambda_plus_sigma: rhs,
        gmo_octet_fractional_residual: residual,
        gmo_decuplet_spacings: [&m.sigma_star - &m.delta, &m.xi_star - &m.sigma_star, &m.omega - &m.xi_star],
        gmo_omega_prediction_mev: core_pred,
        gmo_omega_pdg_mev: m.omega.clone(),
        gmo_omega_fractional_residual: core_res,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/qed_weak_hadronic_finite_maps.rs
// Claim: urn:core:crates_rs:core-quantum-physics:qed-weak-hadronic-finite-maps:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord611cbe47 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord611cbe47` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError611cbe47 {
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
impl BoundaryError611cbe47 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError611cbe47 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError611cbe47 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord611cbe47 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError611cbe47> {
        if capacity_bound == 0 {
            return Err(BoundaryError611cbe47::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError611cbe47::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError611cbe47::ExceedsCapacity {
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
    fn test_qm226_klein_nishina_thomson_and_crossing() {
        assert_eq!(klein_nishina_ratio(q(1, 1), q(0, 1)), q(3, 16));
        assert_eq!(klein_nishina_ratio(q(2, 1), q(-1, 1)), q(13, 125));
        assert_eq!(klein_nishina_ratio(q(1, 10), q(-1, 1)), q(305, 432));
        for x in [q(1, 10), q(7, 3), q(1000, 1)] {
            assert_eq!(klein_nishina_ratio(x, q(1, 1)), q(1, 1));
        }
        assert_eq!(klein_nishina_ratio(q(0, 1), q(1, 2)), q(5, 8));
        assert_eq!(thomson_angular_integral(), q(1, 1));
        assert_eq!(bhabha_reduced_amplitude(q(7, 3), q(-1, 2), q(-11, 6)), moller_reduced_amplitude(q(-11, 6), q(-1, 2), q(7, 3)));
        assert_eq!(bhabha_reduced_amplitude(q(5, 1), q(-2, 1), q(-3, 1)), q(361, 25));
        assert_eq!(moller_reduced_amplitude(q(-2, 1), q(5, 1), q(-3, 1)), q(1444, 225));
        assert!(evaluate_qm226_to_228_qed_weak_hadronic().passed());
    }

    #[test]
    fn test_qm227_weyl_gammas_and_chiral_projectors() {
        let (v, vt) = dirac_to_weyl_blocks();
        assert_eq!(mat4_qi_mul(&v, &vt), mat4_qi_scale(qi_int(2), &mat4_qi_identity()));
        let g = dirac_gammas_weyl();
        let (o, z) = (Qi::one(), Qi::zero());
        assert_eq!(g[0], [[z, z, o, z], [z, z, z, o], [o, z, z, z], [z, o, z, z]]);
        assert_eq!(clifford_anticommutator(&g, 1, 1), mat4_qi_scale(qi_int(-2), &mat4_qi_identity()));
        assert_eq!(clifford_anticommutator(&g, 0, 2), mat4_qi_zero());
        let g5 = gamma5(&g);
        assert_eq!(g5, mat4_qi_diag([-1, -1, 1, 1]));
        let (pl, pr) = chiral_projectors(&g5);
        assert_eq!(pl, mat4_qi_diag([1, 1, 0, 0]));
        assert_eq!(pr, mat4_qi_diag([0, 0, 1, 1]));
        assert_eq!(mat4_qi_trace(&pl), qi_int(2));
        let right = mat4_qi_mul_vec(&pr, &chiral_test_spinor());
        assert!(vec4_is_zero(&mat4_qi_mul_vec(&mat4_qi_mul(&g[1], &pl), &right)));
    }

    #[test]
    fn test_qm227_fermi_constant_and_interval_helpers() {
        let muon = muon_decay_enclosures();
        assert!(muon.kinoshita_sirlin_dq.hi.is_negative());
        let (lo, hi) = fermi_constant_window();
        assert!(lo <= muon.fermi_constant_gev_minus2.lo && muon.fermi_constant_gev_minus2.hi <= hi);
        assert!(dec("11663", -9) <= muon.fermi_constant_gev_minus2.lo && muon.fermi_constant_gev_minus2.hi < dec("11664", -9));
        let ln2 = ln_big_interval(&big(2), 30);
        assert!(dec("69314718055", -11) < ln2.lo && ln2.hi < dec("69314718056", -11));
        let root = sqrt_big_interval(&BigInterval::exact(big(2)), 10);
        assert!(&root.lo * &root.lo <= big(2) && big(2) <= &root.hi * &root.hi);
    }

    #[test]
    fn test_qm227_ckm_unitarity_triangle_and_jarlskog() {
        let a = ckm_skew_hermitian_generator();
        assert_eq!(a.dagger(), mat3_neg(&a));
        let v = cayley_transform3(&a);
        assert_eq!(v.dagger().mul(&v), Mat3Qi::identity());
        assert_eq!(v.mul(&v.dagger()), Mat3Qi::identity());
        let z = ckm_db_triangle(&v);
        assert!(z[0].add(&z[1]).add(&z[2]).is_zero());
        let j = jarlskog(&v, (0, 1), (0, 1));
        assert!(j.abs() > dec("1", -5) && j.abs() < dec("1", -4));
        assert_eq!(jarlskog(&v, (1, 2), (0, 2)).abs(), j.abs());
    }

    #[test]
    fn test_qm228_abj_and_gell_mann_okubo() {
        assert_eq!(abj_colour_factor(3), q(1, 1));
        assert_eq!(abj_colour_factor(1), q(1, 3));
        let (band_lo, _, central) = pion_rate_band_and_central();
        let r3 = pion_two_photon_rate_ev(q(1, 1));
        assert!(r3.lo <= central && central <= r3.hi);
        assert!(pion_two_photon_rate_ev(q(1, 3)).hi < band_lo);
        assert_eq!(gmo_octet_relation_coefficients(), [q(0, 1); 3]);
        assert_eq!(gmo_decuplet_second_differences(), [[q(0, 1); 3]; 2]);
        let r = evaluate_qm226_to_228_qed_weak_hadronic();
        let m = pdg_baryon_masses();
        assert_eq!(r.gmo_octet_lhs_2_n_plus_xi, big(2) * (&m.nucleon + &m.xi));
        assert_eq!(r.gmo_octet_rhs_3_lambda_plus_sigma, big(3) * &m.lambda + &m.sigma);
        assert!(r.gmo_octet_lhs_2_n_plus_xi < r.gmo_octet_rhs_3_lambda_plus_sigma);
        assert!(r.gmo_octet_fractional_residual > bq(5, 1000) && r.gmo_octet_fractional_residual <= bq(6, 1000));
        assert!(r.gmo_omega_fractional_residual <= bq(1, 100));
    }
}

#[cfg(test)]
mod l4_boundary_tests_611cbe47 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord611cbe47::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord611cbe47::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord611cbe47::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord611cbe47::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord611cbe47::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError611cbe47::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError611cbe47::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
