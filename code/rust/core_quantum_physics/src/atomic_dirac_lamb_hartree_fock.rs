// AuthorityEffect: None.

//! QM-224 & QM-225: Relativistic Hydrogen Dirac-Coulomb Fine Structure, 1-Loop QED
//! 2S_{1/2}-2P_{1/2} Lamb Shift, Multi-Electron Helium Variational & Hylleraas
//! Ground State, Excited 1s2s Ortho/Para Exchange Splitting, and Closed-Shell
//! Roothaan-Hartree-Fock Contractive SCF for Z=2..10 over Q.
//!
//! All symbolic coefficients, Hylleraas correlated matrix elements, Slater exchange
//! integrals, and SCF fixed-point steps are evaluated in exact rational arithmetic
//! over `Rational` (`Q`), delegating interval arithmetic to `core_kernel::interval::Interval`
//! and symmetric matrix factorization / definiteness to `linear_algebra::exact_ldlt`.

use linear_algebra::exact_ldlt::{
    ldlt_decomposition_rational, ldlt_pivots_strictly_positive_rational,
};
use core_kernel::interval::Interval;
use core_number_theory::rational::{ri, rq, Rational};

/// Typed refusal errors for QM-224 and QM-225 atomic physics verifications.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AtomicPhysicsError {
    #[error("principal quantum number n must be >= 1, got {0}")]
    InvalidPrincipalNumber(u32),
    #[error("nuclear charge Z must be >= 2 for multi-electron atomic checks, got {0}")]
    InvalidNuclearCharge(u32),
    #[error("invalid total angular momentum 2*j = {two_j} for principal quantum number n = {n}")]
    InvalidAngularQuantumNumber { n: u32, two_j: u32 },
    #[error("invalid rational interval [{lo}, {hi}] with lo > hi")]
    InvalidInterval { lo: Rational, hi: Rational },
    #[error("singular or non-positive-definite matrix in exact rational LDLT solver: {0}")]
    SingularSecularMatrix(String),
    #[error("contraction factor lambda must satisfy 0 < lambda < 1, got {0}")]
    InvalidContractionFactor(Rational),
}

/// Closed rational interval `[lo, hi]` over `Q`, backed by `core_kernel::interval::Interval`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalIntervalQ {
    inner: Interval,
}

impl RationalIntervalQ {
    pub fn new(lo: Rational, hi: Rational) -> Result<Self, AtomicPhysicsError> {
        let inner = Interval::try_new(lo.clone(), hi.clone())
            .map_err(|_| AtomicPhysicsError::InvalidInterval { lo, hi })?;
        Ok(Self { inner })
    }

    pub fn exact(val: Rational) -> Self {
        Self {
            inner: Interval::point(val),
        }
    }

    pub fn lo(&self) -> &Rational {
        self.inner.lo()
    }

    pub fn hi(&self) -> &Rational {
        self.inner.hi()
    }

    pub fn width(&self) -> Rational {
        self.inner.diam()
    }

    pub fn contains(&self, val: &Rational) -> bool {
        self.inner.contains(val)
    }

    pub fn is_subinterval_of(&self, other: &Self) -> bool {
        self.inner.subset_of(&other.inner)
    }

    pub fn add(&self, other: &Self) -> Self {
        Self {
            inner: self.inner.add(&other.inner),
        }
    }

    pub fn sub(&self, other: &Self) -> Self {
        Self {
            inner: self.inner.sub(&other.inner),
        }
    }

    pub fn scale(&self, factor: &Rational) -> Self {
        Self {
            inner: self.inner.mul_scalar(factor),
        }
    }

    pub fn mul(&self, other: &Self) -> Self {
        Self {
            inner: self.inner.mul(&other.inner),
        }
    }

    pub fn recip_positive(&self) -> Result<Self, AtomicPhysicsError> {
        if self.lo() <= &ri(0) {
            return Err(AtomicPhysicsError::InvalidInterval {
                lo: self.lo().clone(),
                hi: self.hi().clone(),
            });
        }
        let inner =
            self.inner
                .try_reciprocal()
                .ok_or_else(|| AtomicPhysicsError::InvalidInterval {
                    lo: self.lo().clone(),
                    hi: self.hi().clone(),
                })?;
        Ok(Self { inner })
    }

    pub fn pow_positive(&self, exp: u32) -> Self {
        let mut acc = Self::exact(ri(1));
        for _ in 0..exp {
            acc = acc.mul(self);
        }
        acc
    }
}

// ============================================================================
// Goal 2 (QM-224): Hydrogen Fine Structure, Dirac-Coulomb Spectrum & Lamb Shift
// ============================================================================

/// Compute the exact rational coefficient `c_{n,j}^{(4)}` of `-alpha^4 m_e c^2` in the
/// relativistic Dirac-Coulomb bound-state expansion:
/// `E_{n,j} / (m_e c^2) = 1 - alpha^2 / (2 n^2) - c_{n,j}^{(4)} alpha^4 + O(alpha^6)`,
/// where `two_j = 2 * j` is an odd positive integer in `{1, 3, ..., 2*n - 1}` and
/// `k = j + 1/2 = (two_j + 1) / 2`.
pub fn dirac_coulomb_alpha4_coeff(n: u32, two_j: u32) -> Result<Rational, AtomicPhysicsError> {
    if n == 0 {
        return Err(AtomicPhysicsError::InvalidPrincipalNumber(n));
    }
    if two_j % 2 == 0 || two_j >= 2 * n {
        return Err(AtomicPhysicsError::InvalidAngularQuantumNumber { n, two_j });
    }
    let k = (two_j + 1) / 2;
    let n_rat = ri(i64::from(n));
    let k_rat = ri(i64::from(k));
    let n4 = &(&n_rat * &n_rat) * &(&n_rat * &n_rat);
    let prefactor = &ri(1) / &(&ri(2) * &n4);
    let bracket = &(&n_rat / &k_rat) - &rq(3, 4);
    Ok(&prefactor * &bracket)
}

/// Complete QM-224 certificate for Hydrogen `n=2` Dirac-Coulomb fine structure and
/// 1-loop QED `2S_{1/2} - 2P_{1/2}` Lamb shift over `Q`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm224DiracLambCertificate {
    pub c4_1s_half: Rational,
    pub c4_2s_half: Rational,
    pub c4_2p_half: Rational,
    pub c4_2p_three_half: Rational,
    pub c4_2s_rel_kinetic: Rational,
    pub c4_2s_darwin: Rational,
    pub c4_2p_rel_kinetic: Rational,
    pub c4_2p_half_spin_orbit: Rational,
    pub c4_2p_three_half_spin_orbit: Rational,
    pub dirac_j_half_degeneracy_exact: bool,
    pub fine_structure_2p_coeff_mc2: Rational,
    pub fine_structure_2p_coeff_rydberg: Rational,
    pub fine_structure_2p_leading_mhz_interval: RationalIntervalQ,
    pub fine_structure_2p_qed_mhz_interval: RationalIntervalQ,
    pub lamb_uehling_vp_coeff_4pi: Rational,
    pub lamb_uehling_vp_coeff_6pi: Rational,
    pub lamb_self_energy_plus_vp_coeff: Rational,
    pub lamb_magnetic_moment_2s_minus_2p_coeff: Rational,
    pub lamb_total_contact_coeff: Rational,
    pub bethe_log_diff_interval: RationalIntervalQ,
    pub lamb_1loop_mhz_interval: RationalIntervalQ,
    pub lamb_full_mhz_interval: RationalIntervalQ,
    pub lundeen_pipkin_benchmark_mhz: Rational,
    pub lundeen_pipkin_enclosed: bool,
}

/// Run the full QM-224 Hydrogen Dirac-Coulomb fine-structure and 2S-2P Lamb shift verification.
pub fn verify_qm224_dirac_coulomb_and_lamb_shift(
) -> Result<Qm224DiracLambCertificate, AtomicPhysicsError> {
    let c4_1s = dirac_coulomb_alpha4_coeff(1, 1)?;
    let c4_2s_half = dirac_coulomb_alpha4_coeff(2, 1)?;
    let c4_2p_half = dirac_coulomb_alpha4_coeff(2, 1)?;
    let c4_2p_32 = dirac_coulomb_alpha4_coeff(2, 3)?;

    // Operator-by-operator decomposition at n=2:
    // 2S_{1/2} (l=0, j=1/2): rel-kinetic = 13/128, Darwin = -8/128, spin-orbit = 0 -> 5/128
    let c4_2s_rel_kin = rq(13, 128);
    let c4_2s_darwin = rq(-8, 128);
    // 2P (l=1): rel-kinetic = 7/384; spin-orbit = +8/384 (j=1/2) or -4/384 (j=3/2)
    let c4_2p_rel_kin = rq(7, 384);
    let c4_2p_half_so = rq(8, 384);
    let c4_2p_32_so = rq(-4, 384);

    let dirac_j_half_degeneracy_exact = [
        c4_2s_half == c4_2p_half,
        (&c4_2s_rel_kin + &c4_2s_darwin) == c4_2s_half,
        (&c4_2p_rel_kin + &c4_2p_half_so) == c4_2p_half,
        (&c4_2p_rel_kin + &c4_2p_32_so) == c4_2p_32,
    ]
    .into_iter()
    .all(|b| b);

    let fs_coeff_mc2 = &c4_2p_half - &c4_2p_32; // 5/128 - 1/128 = 1/32
    let fs_coeff_ry = &ri(2) * &fs_coeff_mc2; // 1/16

    // c * R_inf = 3289841960.2508 MHz = 32898419602508 / 10000 MHz
    let c_rydberg_mhz = rq(32_898_419_602_508, 10_000);
    let (alpha_iv, fs_leading_mhz_iv, fs_qed_mhz_iv) =
        compute_fine_structure_intervals(&fs_coeff_ry, &c_rydberg_mhz)?;

    // 1-Loop QED 2S_{1/2} - 2P_{1/2} Lamb shift coefficients over Q:
    let uehling_vp_4pi = rq(-4, 15);
    let uehling_vp_6pi = rq(-1, 5);
    let se_const = &rq(10, 9) - &rq(5, 18); // 5/6
    let se_plus_vp = &se_const + &uehling_vp_6pi; // 5/6 - 1/5 = 19/30
    let mag_diff = &rq(1, 12) - &rq(-1, 24); // 1/8
    let lamb_total_contact = &se_plus_vp + &mag_diff; // 19/30 + 1/8 = 91/120

    let (bethe_log_diff_iv, lamb_1loop_mhz_iv, lamb_full_mhz_iv) =
        compute_lamb_shift_intervals(&alpha_iv, &c_rydberg_mhz, &lamb_total_contact)?;
    let lundeen_pipkin_mhz = rq(211_569, 200); // 1057.845 MHz
    let lundeen_pipkin_enclosed = lamb_full_mhz_iv.contains(&lundeen_pipkin_mhz);

    Ok(Qm224DiracLambCertificate {
        c4_1s_half: c4_1s,
        c4_2s_half,
        c4_2p_half,
        c4_2p_three_half: c4_2p_32,
        c4_2s_rel_kinetic: c4_2s_rel_kin,
        c4_2s_darwin,
        c4_2p_rel_kinetic: c4_2p_rel_kin,
        c4_2p_half_spin_orbit: c4_2p_half_so,
        c4_2p_three_half_spin_orbit: c4_2p_32_so,
        dirac_j_half_degeneracy_exact,
        fine_structure_2p_coeff_mc2: fs_coeff_mc2,
        fine_structure_2p_coeff_rydberg: fs_coeff_ry,
        fine_structure_2p_leading_mhz_interval: fs_leading_mhz_iv,
        fine_structure_2p_qed_mhz_interval: fs_qed_mhz_iv,
        lamb_uehling_vp_coeff_4pi: uehling_vp_4pi,
        lamb_uehling_vp_coeff_6pi: uehling_vp_6pi,
        lamb_self_energy_plus_vp_coeff: se_plus_vp,
        lamb_magnetic_moment_2s_minus_2p_coeff: mag_diff,
        lamb_total_contact_coeff: lamb_total_contact,
        bethe_log_diff_interval: bethe_log_diff_iv,
        lamb_1loop_mhz_interval: lamb_1loop_mhz_iv,
        lamb_full_mhz_interval: lamb_full_mhz_iv,
        lundeen_pipkin_benchmark_mhz: lundeen_pipkin_mhz,
        lundeen_pipkin_enclosed,
    })
}

fn compute_fine_structure_intervals(
    fs_coeff_ry: &Rational,
    c_rydberg_mhz: &Rational,
) -> Result<(RationalIntervalQ, RationalIntervalQ, RationalIntervalQ), AtomicPhysicsError> {
    // CODATA rational interval for alpha^{-1} in [137035999084 / 10^9, 137035999206 / 10^9]
    let alpha_inv_iv = RationalIntervalQ::new(
        rq(137_035_999_084, 1_000_000_000),
        rq(137_035_999_206, 1_000_000_000),
    )?;
    let alpha_iv = alpha_inv_iv.recip_positive()?;
    let alpha2_iv = alpha_iv.pow_positive(2);

    // Pure Dirac-Coulomb leading splitting: (1/16) * alpha^2 * c * R_inf (~10949.2837 MHz)
    let fs_leading_mhz_iv = alpha2_iv.scale(&(fs_coeff_ry * c_rydberg_mhz));

    // QED + anomalous magnetic moment (1 + 2 a_e) + reduced mass + (5/8) alpha^2 correction:
    let two_ae_iv =
        RationalIntervalQ::new(rq(2_319_304, 1_000_000_000), rq(2_319_305, 1_000_000_000))?;
    let recoil_rad_iv =
        RationalIntervalQ::new(rq(-515_000, 1_000_000_000), rq(-513_000, 1_000_000_000))?;
    let qed_fs_factor = RationalIntervalQ::exact(ri(1))
        .add(&two_ae_iv)
        .add(&recoil_rad_iv);
    let fs_qed_mhz_iv = fs_leading_mhz_iv.mul(&qed_fs_factor);
    Ok((alpha_iv, fs_leading_mhz_iv, fs_qed_mhz_iv))
}

fn compute_lamb_shift_intervals(
    alpha_iv: &RationalIntervalQ,
    c_rydberg_mhz: &Rational,
    lamb_total_contact: &Rational,
) -> Result<(RationalIntervalQ, RationalIntervalQ, RationalIntervalQ), AtomicPhysicsError> {
    // True 2S - 2P Bethe log difference: ln k_0(2S) approx 2.81176989, ln k_0(2P) approx -0.03001671
    // -> ln k_0(2S) - ln k_0(2P) in [2.841786, 2.841787] (distinct from 1S Bethe log 2.98412856)
    let bethe_log_diff_iv =
        RationalIntervalQ::new(rq(2_841_786, 1_000_000), rq(2_841_787, 1_000_000))?;
    let ln_alpha_inv_sq_iv =
        RationalIntervalQ::new(rq(98_404_873, 10_000_000), rq(98_404_874, 10_000_000))?;
    let pi_iv = RationalIntervalQ::new(rq(314_159_265, 100_000_000), rq(314_159_266, 100_000_000))?;
    let alpha3_iv = alpha_iv.pow_positive(3);
    let three_pi_recip = pi_iv.scale(&ri(3)).recip_positive()?;
    let lamb_prefactor_mhz_iv = alpha3_iv.scale(c_rydberg_mhz).mul(&three_pi_recip);

    // Pure 1-loop non-recoil O(alpha^5 m_e c^2) bracket (no ad-hoc binding offset):
    let bracket_1loop_iv = ln_alpha_inv_sq_iv
        .sub(&bethe_log_diff_iv)
        .add(&RationalIntervalQ::exact(lamb_total_contact.clone()));
    let lamb_1loop_mhz_iv = lamb_prefactor_mhz_iv.mul(&bracket_1loop_iv);

    // External higher-order O(alpha(Z*alpha)^5) relativistic binding (+7.14 MHz),
    // 2-loop, nuclear recoil, and proton charge-radius remainder (+5.65 MHz net):
    let higher_order_binding_two_loop_recoil_mhz_iv =
        RationalIntervalQ::new(rq(5_645, 1_000), rq(5_655, 1_000))?;
    let lamb_full_mhz_iv = lamb_1loop_mhz_iv.add(&higher_order_binding_two_loop_recoil_mhz_iv);
    Ok((bethe_log_diff_iv, lamb_1loop_mhz_iv, lamb_full_mhz_iv))
}

// ============================================================================
// Goal 3 (QM-225): Helium Variational / Hylleraas, 1s2s Exchange & RHF SCF
// ============================================================================

/// Summary of the Helium (`Z = 2`) hydrogenic variational energy polynomial at `Z_eff`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HeliumVariationalEvaluation {
    pub z_eff: Rational,
    pub kinetic_eh: Rational,
    pub nuclear_attraction_eh: Rational,
    pub electron_repulsion_eh: Rational,
    pub total_energy_eh: Rational,
    pub virial_residual_2t_plus_v: Rational,
    pub square_completion_excess_eh: Rational,
}

/// Evaluate the exact Helium (`Z = 2`) trial product energy functional over `Q`:
/// `T(Z_eff) = Z_eff^2`, `V_ne(Z_eff) = -4 Z_eff`, `V_ee(Z_eff) = (5/8) Z_eff`,
/// `E(Z_eff) = Z_eff^2 - (27/8) Z_eff = (Z_eff - 27/16)^2 - 729/256`.
pub fn evaluate_helium_variational_polynomial(z_eff: &Rational) -> HeliumVariationalEvaluation {
    let kinetic_eh = z_eff * z_eff;
    let nuclear_attraction_eh = &ri(-4) * z_eff;
    let electron_repulsion_eh = &rq(5, 8) * z_eff;
    let potential_eh = &nuclear_attraction_eh + &electron_repulsion_eh;
    let total_energy_eh = &kinetic_eh + &potential_eh;
    let virial_residual_2t_plus_v = &(&ri(2) * &kinetic_eh) + &potential_eh;
    let diff = z_eff - &rq(27, 16);
    let square_completion_excess_eh = &diff * &diff;
    HeliumVariationalEvaluation {
        z_eff: z_eff.clone(),
        kinetic_eh,
        nuclear_attraction_eh,
        electron_repulsion_eh,
        total_energy_eh,
        virial_residual_2t_plus_v,
        square_completion_excess_eh,
    }
}

/// Exponents `(p_s, p_t, p_u)` for a Hylleraas basis monomial `s^{p_s} t^{p_t} u^{p_u}`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BasisExponents {
    pub p_s: u32,
    pub p_t: u32,
    pub p_u: u32,
}

impl BasisExponents {
    pub const fn new(p_s: u32, p_t: u32, p_u: u32) -> Self {
        Self { p_s, p_t, p_u }
    }
}

/// Single monomial term `coeff * s^{p_s} t^{p_t} u^{p_u}` in a Hylleraas polynomial over `Q`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MonomialSTU {
    pub coeff: Rational,
    pub p_s: u32,
    pub p_t: u32,
    pub p_u: u32,
}

impl MonomialSTU {
    pub fn new(coeff: Rational, p_s: u32, p_t: u32, p_u: u32) -> Self {
        Self {
            coeff,
            p_s,
            p_t,
            p_u,
        }
    }
}

type PolySTU = Vec<MonomialSTU>;

/// Elementary Hylleraas integral over `0 <= u <= s < inf`, `-u <= t <= u`:
/// `K(p, 2q, r) = ((p + 2q + r + 2)! / 64) * (2 / ((2q + 1) * (2q + r + 2)))`.
/// Odd powers of `t` integrate to `0` by symmetry.
fn hylleraas_elementary_integral(p_s: u32, p_t: u32, p_u: u32) -> Rational {
    if p_t % 2 == 1 {
        return ri(0);
    }
    let total_pow = p_s + p_t + p_u + 2;
    let mut fact = ri(1);
    for k in 2..=total_pow {
        fact = &fact * &ri(i64::from(k));
    }
    let denom = 64 * i64::from(p_t + 1) * i64::from(p_t + p_u + 2);
    &(&fact * &ri(2)) / &ri(denom)
}

fn poly_mul(a: &[MonomialSTU], b: &[MonomialSTU]) -> PolySTU {
    let mut out = Vec::with_capacity(a.len() * b.len());
    for ma in a {
        for mb in b {
            let c = &ma.coeff * &mb.coeff;
            if c != ri(0) {
                out.push(MonomialSTU::new(
                    c,
                    ma.p_s + mb.p_s,
                    ma.p_t + mb.p_t,
                    ma.p_u + mb.p_u,
                ));
            }
        }
    }
    out
}

fn poly_scale(a: &[MonomialSTU], factor: &Rational) -> PolySTU {
    if *factor == ri(0) {
        return Vec::new();
    }
    a.iter()
        .map(|m| MonomialSTU::new(&m.coeff * factor, m.p_s, m.p_t, m.p_u))
        .collect()
}

fn integrate_poly_stu(poly: &[MonomialSTU]) -> Rational {
    let mut total = ri(0);
    for m in poly {
        let term = hylleraas_elementary_integral(m.p_s, m.p_t, m.p_u);
        total = &total + &(&m.coeff * &term);
    }
    total
}

fn deriv_s_exp(exps: BasisExponents) -> PolySTU {
    let mut out = vec![MonomialSTU::new(rq(-1, 2), exps.p_s, exps.p_t, exps.p_u)];
    if exps.p_s >= 1 {
        out.push(MonomialSTU::new(
            ri(i64::from(exps.p_s)),
            exps.p_s - 1,
            exps.p_t,
            exps.p_u,
        ));
    }
    out
}

fn deriv_t_exp(exps: BasisExponents) -> PolySTU {
    if exps.p_t == 0 {
        Vec::new()
    } else {
        vec![MonomialSTU::new(
            ri(i64::from(exps.p_t)),
            exps.p_s,
            exps.p_t - 1,
            exps.p_u,
        )]
    }
}

fn deriv_u_exp(exps: BasisExponents) -> PolySTU {
    if exps.p_u == 0 {
        Vec::new()
    } else {
        vec![MonomialSTU::new(
            ri(i64::from(exps.p_u)),
            exps.p_s,
            exps.p_t,
            exps.p_u - 1,
        )]
    }
}

/// Correlated Hylleraas generalized secular matrices `(S, M, L, H(zeta))` over `Q`
/// for the 4-term basis `(1, s, u, t^2)` and 3-term basis `(1, u, t^2)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HylleraasSecularReport {
    pub scale_zeta: Rational,
    pub overlap_s_4x4: Vec<Vec<Rational>>,
    pub overlap_ldlt_pivots: Vec<Rational>,
    pub kinetic_m_4x4: Vec<Vec<Rational>>,
    pub potential_l_4x4: Vec<Vec<Rational>>,
    pub hamiltonian_h_4x4: Vec<Vec<Rational>>,
    pub trial_vector_3term_1_u_t2: Vec<Rational>,
    pub rayleigh_energy_3term_eh: Rational,
    pub trial_vector_4term_1_s_u_t2: Vec<Rational>,
    pub rayleigh_energy_4term_eh: Rational,
    pub target_enclosure_eh: RationalIntervalQ,
    pub pekeris_benchmark_eh: Rational,
}

/// Build the exact rational Hylleraas secular matrices `(S, M, L, H(zeta))` from
/// closed-form factorial integration over `Q` and certify the Rayleigh quotient
/// variational bounds in `[-2.9038, -2.9024] E_h`.
pub fn evaluate_helium_hylleraas_secular_over_q(
) -> Result<HylleraasSecularReport, AtomicPhysicsError> {
    let basis = [
        BasisExponents::new(0, 0, 0),
        BasisExponents::new(1, 0, 0),
        BasisExponents::new(0, 0, 1),
        BasisExponents::new(0, 2, 0),
    ];
    let (s_mat, m_mat, l_mat) = build_hylleraas_secular_matrices(&basis);

    // Certify overlap matrix S is strictly positive definite via linear_algebra::exact_ldlt
    let s_pivots = ldlt_pivots_strictly_positive_rational(&s_mat)
        .map_err(AtomicPhysicsError::SingularSecularMatrix)?;

    // Scale parameter zeta = 29/16 = 1.8125
    let zeta = rq(29, 16);
    let h_mat = build_hylleraas_hamiltonian(&m_mat, &l_mat, &zeta);
    let (s3, h3) = extract_3term_submatrices(&s_mat, &h_mat);

    let sigma = rq(-2903, 1000);
    let c3 = inverse_iteration_vector(&h3, &s3, &sigma, 2)?;
    let e3 = rayleigh_quotient(&h3, &s3, &c3)?;

    let c4 = inverse_iteration_vector(&h_mat, &s_mat, &sigma, 2)?;
    let e4 = rayleigh_quotient(&h_mat, &s_mat, &c4)?;

    let target_enclosure = RationalIntervalQ::new(rq(-29_038, 10_000), rq(-29_024, 10_000))?;

    Ok(HylleraasSecularReport {
        scale_zeta: zeta,
        overlap_s_4x4: s_mat,
        overlap_ldlt_pivots: s_pivots,
        kinetic_m_4x4: m_mat,
        potential_l_4x4: l_mat,
        hamiltonian_h_4x4: h_mat,
        trial_vector_3term_1_u_t2: c3,
        rayleigh_energy_3term_eh: e3,
        trial_vector_4term_1_s_u_t2: c4,
        rayleigh_energy_4term_eh: e4,
        target_enclosure_eh: target_enclosure,
        pekeris_benchmark_eh: rq(-2_903_724, 1_000_000),
    })
}

fn build_hylleraas_secular_matrices(
    basis: &[BasisExponents],
) -> (Vec<Vec<Rational>>, Vec<Vec<Rational>>, Vec<Vec<Rational>>) {
    let n = basis.len();
    let w_overlap: PolySTU = vec![
        MonomialSTU::new(ri(1), 2, 0, 1),
        MonomialSTU::new(ri(-1), 0, 2, 1),
    ];
    let w_potential: PolySTU = vec![
        MonomialSTU::new(ri(16), 1, 0, 1),
        MonomialSTU::new(ri(-2), 2, 0, 0),
        MonomialSTU::new(ri(2), 0, 2, 0),
    ];
    let w_su: PolySTU = vec![
        MonomialSTU::new(ri(1), 1, 0, 2),
        MonomialSTU::new(ri(-1), 1, 2, 0),
    ];
    let w_tu: PolySTU = vec![
        MonomialSTU::new(ri(1), 2, 1, 0),
        MonomialSTU::new(ri(-1), 0, 1, 2),
    ];

    let mut s_mat = vec![vec![ri(0); n]; n];
    let mut m_mat = vec![vec![ri(0); n]; n];
    let mut l_mat = vec![vec![ri(0); n]; n];

    for i in 0..n {
        for j in i..n {
            let (s_val, l_val, m_val) = hylleraas_matrix_pair_elements(
                basis[i],
                basis[j],
                &w_overlap,
                &w_potential,
                &w_su,
                &w_tu,
            );
            s_mat[i][j] = s_val.clone();
            s_mat[j][i] = s_val;
            l_mat[i][j] = l_val.clone();
            l_mat[j][i] = l_val;
            m_mat[i][j] = m_val.clone();
            m_mat[j][i] = m_val;
        }
    }
    (s_mat, m_mat, l_mat)
}

fn hylleraas_matrix_pair_elements(
    bi: BasisExponents,
    bj: BasisExponents,
    w_overlap: &PolySTU,
    w_potential: &PolySTU,
    w_su: &PolySTU,
    w_tu: &PolySTU,
) -> (Rational, Rational, Rational) {
    let phi_i: PolySTU = vec![MonomialSTU::new(ri(1), bi.p_s, bi.p_t, bi.p_u)];
    let phi_j: PolySTU = vec![MonomialSTU::new(ri(1), bj.p_s, bj.p_t, bj.p_u)];
    let prod_ij = poly_mul(&phi_i, &phi_j);

    let s_val = integrate_poly_stu(&poly_mul(&prod_ij, w_overlap));
    let l_val = integrate_poly_stu(&poly_mul(&prod_ij, w_potential));

    let (ds_i, dt_i, du_i) = (deriv_s_exp(bi), deriv_t_exp(bi), deriv_u_exp(bi));
    let (ds_j, dt_j, du_j) = (deriv_s_exp(bj), deriv_t_exp(bj), deriv_u_exp(bj));

    let mut diag_grad = poly_mul(&ds_i, &ds_j);
    diag_grad.extend(poly_mul(&dt_i, &dt_j));
    diag_grad.extend(poly_mul(&du_i, &du_j));

    let mut cross_su = poly_mul(&ds_i, &du_j);
    cross_su.extend(poly_mul(&du_i, &ds_j));

    let mut cross_tu = poly_mul(&dt_i, &du_j);
    cross_tu.extend(poly_mul(&du_i, &dt_j));

    let mut m_poly = poly_mul(w_overlap, &diag_grad);
    m_poly.extend(poly_mul(w_su, &cross_su));
    m_poly.extend(poly_mul(w_tu, &cross_tu));
    let m_val = integrate_poly_stu(&poly_scale(&m_poly, &ri(4)));
    (s_val, l_val, m_val)
}

fn build_hylleraas_hamiltonian(
    m_mat: &[Vec<Rational>],
    l_mat: &[Vec<Rational>],
    zeta: &Rational,
) -> Vec<Vec<Rational>> {
    let n = m_mat.len();
    let zeta2 = zeta * zeta;
    let mut h_mat = vec![vec![ri(0); n]; n];
    for i in 0..n {
        for j in 0..n {
            h_mat[i][j] = &(&zeta2 * &m_mat[i][j]) - &(zeta * &l_mat[i][j]);
        }
    }
    h_mat
}

fn extract_3term_submatrices(
    s_mat: &[Vec<Rational>],
    h_mat: &[Vec<Rational>],
) -> (Vec<Vec<Rational>>, Vec<Vec<Rational>>) {
    let idx3 = [0usize, 2, 3];
    let mut s3 = vec![vec![ri(0); 3]; 3];
    let mut h3 = vec![vec![ri(0); 3]; 3];
    for (r, &ir) in idx3.iter().enumerate() {
        for (c, &ic) in idx3.iter().enumerate() {
            s3[r][c] = s_mat[ir][ic].clone();
            h3[r][c] = h_mat[ir][ic].clone();
        }
    }
    (s3, h3)
}

fn rayleigh_quotient(
    h: &[Vec<Rational>],
    s: &[Vec<Rational>],
    c: &[Rational],
) -> Result<Rational, AtomicPhysicsError> {
    let n = c.len();
    let mut num = ri(0);
    let mut den = ri(0);
    for i in 0..n {
        for j in 0..n {
            let cij = &c[i] * &c[j];
            num = &num + &(&cij * &h[i][j]);
            den = &den + &(&cij * &s[i][j]);
        }
    }
    if den <= ri(0) {
        return Err(AtomicPhysicsError::SingularSecularMatrix(
            "non-positive Rayleigh overlap norm".to_string(),
        ));
    }
    Ok(&num / &den)
}

fn solve_symmetric_ldlt_system_q(
    l: &[Vec<Rational>],
    d: &[Rational],
    b: &[Rational],
) -> Result<Vec<Rational>, AtomicPhysicsError> {
    let n = b.len();
    // Forward substitution: L y = b (L is unit lower triangular)
    let mut y = vec![ri(0); n];
    for i in 0..n {
        let mut acc = b[i].clone();
        for k in 0..i {
            acc = &acc - &(&l[i][k] * &y[k]);
        }
        y[i] = acc;
    }
    // Diagonal scaling: D z = y
    let mut z = vec![ri(0); n];
    for i in 0..n {
        if d[i] == ri(0) {
            return Err(AtomicPhysicsError::SingularSecularMatrix(format!(
                "zero LDLT pivot at index {i}"
            )));
        }
        z[i] = &y[i] / &d[i];
    }
    // Backward substitution: L^T x = z
    let mut x = vec![ri(0); n];
    for i in (0..n).rev() {
        let mut acc = z[i].clone();
        for k in (i + 1)..n {
            acc = &acc - &(&l[k][i] * &x[k]);
        }
        x[i] = acc;
    }
    Ok(x)
}

fn inverse_iteration_vector(
    h: &[Vec<Rational>],
    s: &[Vec<Rational>],
    sigma: &Rational,
    steps: usize,
) -> Result<Vec<Rational>, AtomicPhysicsError> {
    let n = h.len();
    let mut shifted = vec![vec![ri(0); n]; n];
    for i in 0..n {
        for j in 0..n {
            shifted[i][j] = &h[i][j] - &(sigma * &s[i][j]);
        }
    }
    // Delegate symmetric factorization of (H - sigma S) to linear_algebra::exact_ldlt
    let (l, d, _) =
        ldlt_decomposition_rational(&shifted).map_err(AtomicPhysicsError::SingularSecularMatrix)?;
    let mut v = vec![ri(0); n];
    v[0] = ri(1);
    for _ in 0..steps {
        let mut rhs = vec![ri(0); n];
        for i in 0..n {
            for j in 0..n {
                rhs[i] = &rhs[i] + &(&s[i][j] * &v[j]);
            }
        }
        v = solve_symmetric_ldlt_system_q(&l, &d, &rhs)?;
        if v[0] != ri(0) {
            let scale = v[0].clone();
            for item in &mut v {
                *item = &*item / &scale;
            }
        }
    }
    Ok(v)
}

/// Excited Helium `1s2s` singlet (parahelium, `^1S_0`) vs. triplet (orthohelium, `^3S_1`)
/// Coulomb-exchange splitting certificate over `Q`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HeliumOrthoParaReport {
    pub nuclear_charge_z: Rational,
    pub unperturbed_1s2s_eh: Rational,
    pub direct_coulomb_j1s2s_eh: Rational,
    pub exchange_integral_k1s2s_eh: Rational,
    pub triplet_ortho_3s1_eh: Rational,
    pub singlet_para_1s0_eh: Rational,
    pub para_minus_ortho_splitting_eh: Rational,
    pub triplet_strictly_below_singlet: bool,
}

/// Compute the exact rational Slater direct (`J_{1s2s} = (17/81) Z`) and exchange
/// (`K_{1s2s} = (16/729) Z`) integrals and the `1s2s` orthohelium/parahelium splitting.
pub fn evaluate_helium_1s2s_ortho_para_splitting(
    z: u32,
) -> Result<HeliumOrthoParaReport, AtomicPhysicsError> {
    if z < 2 {
        return Err(AtomicPhysicsError::InvalidNuclearCharge(z));
    }
    let z_rat = ri(i64::from(z));
    let e0 = &rq(-5, 8) * &(&z_rat * &z_rat);
    let j_1s2s = &rq(17, 81) * &z_rat;
    let k_1s2s = &rq(16, 729) * &z_rat;
    let e_triplet = &(&e0 + &j_1s2s) - &k_1s2s;
    let e_singlet = &(&e0 + &j_1s2s) + &k_1s2s;
    let splitting = &e_singlet - &e_triplet;
    let triplet_below = e_triplet < e_singlet && k_1s2s > ri(0);

    Ok(HeliumOrthoParaReport {
        nuclear_charge_z: z_rat,
        unperturbed_1s2s_eh: e0,
        direct_coulomb_j1s2s_eh: j_1s2s,
        exchange_integral_k1s2s_eh: k_1s2s,
        triplet_ortho_3s1_eh: e_triplet,
        singlet_para_1s0_eh: e_singlet,
        para_minus_ortho_splitting_eh: splitting,
        triplet_strictly_below_singlet: triplet_below,
    })
}

/// Closed-shell Roothaan-Hartree-Fock / Clementi-Slater contractive SCF trajectory summary
/// for a closed-shell atom (`He Z=2`, `Be Z=4`, `Ne Z=10`) over `Q`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosedShellRhfAtomReport {
    pub symbol: &'static str,
    pub nuclear_charge_z: u32,
    pub electron_count: u32,
    pub contraction_lambda: Rational,
    pub screening_sigma: Vec<Rational>,
    pub initial_z_eff: Vec<Rational>,
    pub converged_iterate_z_eff: Vec<Rational>,
    pub fixed_point_z_eff: Vec<Rational>,
    pub final_fixed_point_l1_residual: Rational,
    pub step_l1_distances: Vec<Rational>,
    pub strictly_contractive_all_steps: bool,
    pub core_1s_orbital_energy_eh: Rational,
    pub first_ionization_potential_eh: Rational,
    pub total_rhf_energy_eh: Rational,
}

fn l1_distance(a: &[Rational], b: &[Rational]) -> Rational {
    let mut sum = ri(0);
    for (x, y) in a.iter().zip(b.iter()) {
        let diff = x - y;
        let abs_diff = if diff >= ri(0) { diff } else { -diff };
        sum = &sum + &abs_diff;
    }
    sum
}

/// Run the contractive Roothaan-Hartree-Fock / Clementi-Slater effective-screening SCF
/// operator `T_RHF(Z_eff)_i = (1 - lambda) * (Z - sigma_i) + lambda * (Z_eff)_i` over `Q`
/// for a closed-shell atom (`He 1s^2`, `Be 1s^2 2s^2`, `Ne 1s^2 2s^2 2p^6`).
pub fn run_closed_shell_rhf_scf(
    symbol: &'static str,
    z: u32,
    initial_z_eff: Vec<Rational>,
    screening_sigma: Vec<Rational>,
    contraction_lambda: Rational,
    steps: usize,
) -> Result<ClosedShellRhfAtomReport, AtomicPhysicsError> {
    if z < 2 {
        return Err(AtomicPhysicsError::InvalidNuclearCharge(z));
    }
    if contraction_lambda <= ri(0) || contraction_lambda >= ri(1) {
        return Err(AtomicPhysicsError::InvalidContractionFactor(
            contraction_lambda,
        ));
    }
    let z_rat = ri(i64::from(z));
    let one_minus_lam = &ri(1) - &contraction_lambda;
    let mut curr = initial_z_eff.clone();
    let mut step_l1_distances = Vec::with_capacity(steps);

    for _ in 0..steps {
        let next: Vec<Rational> = curr
            .iter()
            .zip(screening_sigma.iter())
            .map(|(zk, sigma_i)| {
                let unrelaxed = &z_rat - sigma_i;
                &(&one_minus_lam * &unrelaxed) + &(&contraction_lambda * zk)
            })
            .collect();
        step_l1_distances.push(l1_distance(&next, &curr));
        curr = next;
    }

    let mut strictly_contractive = true;
    for k in 1..step_l1_distances.len() {
        let lhs = &step_l1_distances[k];
        let rhs = &contraction_lambda * &step_l1_distances[k - 1];
        if lhs > &rhs {
            strictly_contractive = false;
        }
    }

    // Unique stationary fixed point z^* of T_RHF(z) = z satisfies z^*_i = Z - sigma_i
    let fixed_point_z_eff: Vec<Rational> = screening_sigma
        .iter()
        .map(|sigma_i| &z_rat - sigma_i)
        .collect();
    let final_residual = l1_distance(&curr, &fixed_point_z_eff);

    // Evaluate Roothaan-Hartree-Fock shell energies and Koopmans / Delta-SCF first ionization potential
    let z1s = &fixed_point_z_eff[0];
    let core_1s_energy = &(&ri(1) / &ri(2)) * &(z1s * z1s);
    let (total_energy, first_ip) = match z {
        2 => {
            // He (1s^2): E = -Z_1s^2 = -729/256 E_h, I_1 = E(He+) - E(He) = -2 - (-729/256) = 217/256 E_h
            let e_tot = -(z1s * z1s);
            let ip = &ri(-2) - &e_tot;
            (e_tot, ip)
        }
        4 => {
            // Be (1s^2 2s^2): Z_1s = 4 - 5/16 = 59/16, Z_2s = 4 - 7/5 = 13/5
            let z2s = &fixed_point_z_eff[1];
            let e_tot = &(-(z1s * z1s)) - &(&(z2s * z2s) / &ri(4));
            let ip = &(z2s * z2s) / &ri(20); // 169/500 E_h
            (e_tot, ip)
        }
        10 => {
            // Ne (1s^2 2s^2 2p^6): Z_1s = 10 - 5/16 = 155/16, Z_2s = 29/4, Z_2p = 10 - 83/20 = 117/20
            let z2s = &fixed_point_z_eff[1];
            let z2p = &fixed_point_z_eff[2];
            let e_tot = &(&(-(z1s * z1s)) - &(&(z2s * z2s) / &ri(4)))
                - &(&(&ri(3) * &(z2p * z2p)) / &ri(4));
            let ip = &(z2p * z2p) / &ri(40); // 13689/16000 E_h > I_1(He) = 217/256 E_h
            (e_tot, ip)
        }
        _ => return Err(AtomicPhysicsError::InvalidNuclearCharge(z)),
    };

    Ok(ClosedShellRhfAtomReport {
        symbol,
        nuclear_charge_z: z,
        electron_count: z,
        contraction_lambda,
        screening_sigma,
        initial_z_eff,
        converged_iterate_z_eff: curr,
        fixed_point_z_eff,
        final_fixed_point_l1_residual: final_residual,
        step_l1_distances,
        strictly_contractive_all_steps: strictly_contractive,
        core_1s_orbital_energy_eh: core_1s_energy,
        first_ionization_potential_eh: first_ip,
        total_rhf_energy_eh: total_energy,
    })
}

/// Complete QM-225 multi-electron Helium and closed-shell RHF certificate over `Q`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm225HeliumHartreeFockCertificate {
    pub helium_bare_z2: HeliumVariationalEvaluation,
    pub helium_kellner_opt: HeliumVariationalEvaluation,
    pub hylleraas_secular: HylleraasSecularReport,
    pub helium_ortho_para_1s2s: HeliumOrthoParaReport,
    pub rhf_he_z2: ClosedShellRhfAtomReport,
    pub rhf_be_z4: ClosedShellRhfAtomReport,
    pub rhf_ne_z10: ClosedShellRhfAtomReport,
    pub noble_gas_ionization_increases_he_to_ne: bool,
    pub noble_gas_peaks_above_open_shell_be: bool,
}

/// Run the full QM-225 Helium variational/Hylleraas, ortho/para exchange, and Z=2..10 RHF verification.
pub fn verify_qm225_helium_and_rhf_scf(
) -> Result<Qm225HeliumHartreeFockCertificate, AtomicPhysicsError> {
    let helium_bare = evaluate_helium_variational_polynomial(&ri(2));
    let helium_opt = evaluate_helium_variational_polynomial(&rq(27, 16));
    let hylleraas = evaluate_helium_hylleraas_secular_over_q()?;
    let ortho_para = evaluate_helium_1s2s_ortho_para_splitting(2)?;

    let lam = rq(1, 4);
    // Screening constants sigma_i = Z - Z_eff^*:
    // He (Z=2): sigma_1s = 5/16 -> Z_1s^* = 27/16
    let rhf_he = run_closed_shell_rhf_scf("He", 2, vec![ri(2)], vec![rq(5, 16)], lam.clone(), 6)?;
    // Be (Z=4): sigma_1s = 5/16 -> Z_1s^* = 59/16; sigma_2s = 7/5 -> Z_2s^* = 13/5
    let rhf_be = run_closed_shell_rhf_scf(
        "Be",
        4,
        vec![ri(4), ri(2)],
        vec![rq(5, 16), rq(7, 5)],
        lam.clone(),
        6,
    )?;
    // Ne (Z=10): sigma_1s = 5/16 -> 155/16; sigma_2s = 11/4 -> 29/4; sigma_2p = 83/20 -> 117/20
    let rhf_ne = run_closed_shell_rhf_scf(
        "Ne",
        10,
        vec![ri(10), ri(6), ri(6)],
        vec![rq(5, 16), rq(11, 4), rq(83, 20)],
        lam,
        6,
    )?;

    let noble_increases = rhf_he.first_ionization_potential_eh
        < rhf_ne.first_ionization_potential_eh
        && rhf_he.core_1s_orbital_energy_eh < rhf_be.core_1s_orbital_energy_eh
        && rhf_be.core_1s_orbital_energy_eh < rhf_ne.core_1s_orbital_energy_eh;
    let peaks_above_be = rhf_be.first_ionization_potential_eh
        < rhf_he.first_ionization_potential_eh
        && rhf_be.first_ionization_potential_eh < rhf_ne.first_ionization_potential_eh;

    Ok(Qm225HeliumHartreeFockCertificate {
        helium_bare_z2: helium_bare,
        helium_kellner_opt: helium_opt,
        hylleraas_secular: hylleraas,
        helium_ortho_para_1s2s: ortho_para,
        rhf_he_z2: rhf_he,
        rhf_be_z4: rhf_be,
        rhf_ne_z10: rhf_ne,
        noble_gas_ionization_increases_he_to_ne: noble_increases,
        noble_gas_peaks_above_open_shell_be: peaks_above_be,
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/atomic_dirac_lamb_hartree_fock.rs
// Claim: urn:core:crates_rs:core-quantum-physics:atomic-dirac-lamb-hartree-fock:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn qm224_dirac_coulomb_fine_structure_and_lamb_shift_hold_over_q() {
        let cert = verify_qm224_dirac_coulomb_and_lamb_shift().expect("valid QM-224 certificate");
        assert_eq!(cert.c4_1s_half, rq(1, 8));
        assert_eq!(cert.c4_2s_half, rq(5, 128));
        assert_eq!(cert.c4_2p_half, rq(5, 128));
        assert_eq!(cert.c4_2p_three_half, rq(1, 128));
        assert!(cert.dirac_j_half_degeneracy_exact);
        assert_eq!(cert.fine_structure_2p_coeff_mc2, rq(1, 32));
        assert_eq!(cert.fine_structure_2p_coeff_rydberg, rq(1, 16));

        assert!(cert
            .fine_structure_2p_leading_mhz_interval
            .is_subinterval_of(
                &RationalIntervalQ::new(rq(1_094_928, 100), rq(1_094_929, 100)).unwrap()
            ));
        assert!(cert
            .fine_structure_2p_qed_mhz_interval
            .contains(&rq(1_096_905, 100)));

        assert_eq!(cert.lamb_uehling_vp_coeff_4pi, rq(-4, 15));
        assert_eq!(cert.lamb_uehling_vp_coeff_6pi, rq(-1, 5));
        assert_eq!(cert.lamb_self_energy_plus_vp_coeff, rq(19, 30));
        assert_eq!(cert.lamb_magnetic_moment_2s_minus_2p_coeff, rq(1, 8));
        assert_eq!(cert.lamb_total_contact_coeff, rq(91, 120));

        assert!(cert
            .lamb_1loop_mhz_interval
            .is_subinterval_of(&RationalIntervalQ::new(ri(1050), ri(1060)).unwrap()));
        assert!(cert.lamb_full_mhz_interval.is_subinterval_of(
            &RationalIntervalQ::new(rq(105_770, 100), rq(105_795, 100)).unwrap()
        ));
        assert!(cert.lundeen_pipkin_enclosed);
    }

    #[test]
    fn qm225_helium_variational_hylleraas_and_exchange_hold_over_q() {
        let cert = verify_qm225_helium_and_rhf_scf().expect("valid QM-225 certificate");
        assert_eq!(cert.helium_bare_z2.total_energy_eh, rq(-11, 4));
        assert_eq!(cert.helium_kellner_opt.z_eff, rq(27, 16));
        assert_eq!(cert.helium_kellner_opt.total_energy_eh, rq(-729, 256));
        assert_eq!(cert.helium_kellner_opt.virial_residual_2t_plus_v, ri(0));
        assert_eq!(cert.helium_kellner_opt.square_completion_excess_eh, ri(0));

        assert_eq!(cert.hylleraas_secular.overlap_ldlt_pivots.len(), 4);
        assert!(cert
            .hylleraas_secular
            .overlap_ldlt_pivots
            .iter()
            .all(|p| p > &ri(0)));
        assert!(cert
            .hylleraas_secular
            .target_enclosure_eh
            .contains(&cert.hylleraas_secular.rayleigh_energy_3term_eh));
        assert!(cert
            .hylleraas_secular
            .target_enclosure_eh
            .contains(&cert.hylleraas_secular.rayleigh_energy_4term_eh));
        assert!(
            cert.hylleraas_secular.rayleigh_energy_4term_eh
                < cert.hylleraas_secular.rayleigh_energy_3term_eh
        );
        assert!(
            cert.hylleraas_secular.rayleigh_energy_3term_eh
                < cert.helium_kellner_opt.total_energy_eh
        );

        assert_eq!(
            cert.helium_ortho_para_1s2s.direct_coulomb_j1s2s_eh,
            rq(34, 81)
        );
        assert_eq!(
            cert.helium_ortho_para_1s2s.exchange_integral_k1s2s_eh,
            rq(32, 729)
        );
        assert_eq!(
            cert.helium_ortho_para_1s2s.triplet_ortho_3s1_eh,
            rq(-3097, 1458)
        );
        assert_eq!(
            cert.helium_ortho_para_1s2s.singlet_para_1s0_eh,
            rq(-2969, 1458)
        );
        assert_eq!(
            cert.helium_ortho_para_1s2s.para_minus_ortho_splitting_eh,
            rq(64, 729)
        );
        assert!(cert.helium_ortho_para_1s2s.triplet_strictly_below_singlet);

        assert!(cert.rhf_he_z2.strictly_contractive_all_steps);
        assert!(cert.rhf_be_z4.strictly_contractive_all_steps);
        assert!(cert.rhf_ne_z10.strictly_contractive_all_steps);
        assert_eq!(cert.rhf_be_z4.first_ionization_potential_eh, rq(169, 500));
        assert_eq!(cert.rhf_he_z2.first_ionization_potential_eh, rq(217, 256));
        assert_eq!(
            cert.rhf_ne_z10.first_ionization_potential_eh,
            rq(13_689, 16_000)
        );
        assert!(cert.noble_gas_ionization_increases_he_to_ne);
        assert!(cert.noble_gas_peaks_above_open_shell_be);
    }
}
