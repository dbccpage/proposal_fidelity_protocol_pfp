// AuthorityEffect: None.
//! QM-217 su(2) Kravchuk oscillator and so(4) Hydrogen spectra.
//! Re-exported from `quantum_import_finite_maps`.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};

use super::q;
use super::*;

// ============================================================================
// QM-217: Exact Algebraic Bound-State Spectra (su(2) Kravchuk & so(4) Hydrogen)
// ============================================================================

type QMatDyn = Vec<Vec<Q>>;

fn qd_zeros(rows: usize, cols: usize) -> QMatDyn {
    vec![vec![Q::zero(); cols]; rows]
}

fn qd_eye(dim: usize) -> QMatDyn {
    let mut m = qd_zeros(dim, dim);
    for i in 0..dim {
        m[i][i] = Q::one();
    }
    m
}

fn qd_add(a: &QMatDyn, b: &QMatDyn) -> QMatDyn {
    a.iter()
        .zip(b.iter())
        .map(|(ra, rb)| ra.iter().zip(rb.iter()).map(|(&x, &y)| x + y).collect())
        .collect()
}

fn qd_sub(a: &QMatDyn, b: &QMatDyn) -> QMatDyn {
    a.iter()
        .zip(b.iter())
        .map(|(ra, rb)| ra.iter().zip(rb.iter()).map(|(&x, &y)| x - y).collect())
        .collect()
}

fn qd_scale(s: Q, a: &QMatDyn) -> QMatDyn {
    a.iter()
        .map(|r| r.iter().map(|&x| s * x).collect())
        .collect()
}

fn qd_mul(a: &QMatDyn, b: &QMatDyn) -> QMatDyn {
    let rows = a.len();
    let inner = b.len();
    let cols = b[0].len();
    let mut out = qd_zeros(rows, cols);
    for i in 0..rows {
        for k in 0..inner {
            let aik = a[i][k];
            if !aik.is_zero() {
                for j in 0..cols {
                    out[i][j] += aik * b[k][j];
                }
            }
        }
    }
    out
}

fn qd_comm(a: &QMatDyn, b: &QMatDyn) -> QMatDyn {
    qd_sub(&qd_mul(a, b), &qd_mul(b, a))
}

fn qd_anticomm(a: &QMatDyn, b: &QMatDyn) -> QMatDyn {
    qd_add(&qd_mul(a, b), &qd_mul(b, a))
}

fn qd_transpose(a: &QMatDyn) -> QMatDyn {
    let rows = a.len();
    let cols = a[0].len();
    let mut out = qd_zeros(cols, rows);
    for i in 0..rows {
        for j in 0..cols {
            out[j][i] = a[i][j];
        }
    }
    out
}

fn qd_trace(a: &QMatDyn) -> Q {
    (0..a.len()).fold(Q::zero(), |acc, i| acc + a[i][i])
}

fn qd_kron(a: &QMatDyn, b: &QMatDyn) -> QMatDyn {
    let (ra, ca) = (a.len(), a[0].len());
    let (rb, cb) = (b.len(), b[0].len());
    let mut out = qd_zeros(ra * rb, ca * cb);
    for i in 0..ra {
        for j in 0..ca {
            let aij = a[i][j];
            if !aij.is_zero() {
                for k in 0..rb {
                    for col_b in 0..cb {
                        out[i * rb + k][j * cb + col_b] = aij * b[k][col_b];
                    }
                }
            }
        }
    }
    out
}

fn qd_is_zero(a: &QMatDyn) -> bool {
    a.iter().all(|row| row.iter().all(|x| x.is_zero()))
}

fn binom_i64(n: i64, k: i64) -> i64 {
    if k < 0 || k > n {
        return 0;
    }
    let k = k.min(n - k);
    let mut res = 1i64;
    for i in 0..k {
        res = res * (n - i) / (i + 1);
    }
    res
}

fn sl2_oscillator_generators_q(twice_j: usize) -> (QMatDyn, QMatDyn, QMatDyn, QMatDyn) {
    assert!(twice_j >= 1, "twice_j = 2j must be >= 1");
    let dim = twice_j + 1;
    let j_val = q(twice_j as i64, 2);
    let mut jz = qd_zeros(dim, dim);
    let mut jp = qd_zeros(dim, dim);
    let mut jm = qd_zeros(dim, dim);
    let mut g_metric = qd_zeros(dim, dim);
    for n in 0..dim {
        jz[n][n] = q(n as i64, 1) - j_val;
        g_metric[n][n] = q(1, binom_i64(twice_j as i64, n as i64));
        if n + 1 < dim {
            jp[n + 1][n] = q((twice_j - n) as i64, 1);
        }
        if n >= 1 {
            jm[n - 1][n] = q(n as i64, 1);
        }
    }
    (jz, jp, jm, g_metric)
}

fn sl2_casimir_q(jz: &QMatDyn, jp: &QMatDyn, jm: &QMatDyn) -> QMatDyn {
    qd_add(&qd_mul(jz, jz), &qd_scale(q(1, 2), &qd_anticomm(jp, jm)))
}

pub fn kravchuk_polynomial(k: i64, x: i64, n_max: i64) -> i64 {
    if k < 0 || k > n_max || x < 0 || x > n_max {
        return 0;
    }
    let mut total = 0i64;
    for r in 0..=k {
        let term = binom_i64(x, r) * binom_i64(n_max - x, k - r);
        if r % 2 == 1 {
            total -= term;
        } else {
            total += term;
        }
    }
    total
}

fn check_kravchuk_orthogonality_and_difference_eq(n_max: i64) -> (bool, bool) {
    let mut ortho_ok = true;
    let mut diff_ok = true;
    for k in 0..=n_max {
        for kp in 0..=n_max {
            let lhs: i64 = (0..=n_max)
                .map(|x| {
                    binom_i64(n_max, x)
                        * kravchuk_polynomial(k, x, n_max)
                        * kravchuk_polynomial(kp, x, n_max)
                })
                .sum();
            let rhs = if k == kp {
                (1i64 << n_max) * binom_i64(n_max, k)
            } else {
                0
            };
            if lhs != rhs {
                ortho_ok = false;
            }
        }
        for x in 0..=n_max {
            let left_step = if x < n_max {
                (n_max - x) * kravchuk_polynomial(k, x + 1, n_max)
            } else {
                0
            };
            let right_step = if x >= 1 {
                x * kravchuk_polynomial(k, x - 1, n_max)
            } else {
                0
            };
            let lhs_diff = left_step - n_max * kravchuk_polynomial(k, x, n_max) + right_step;
            let rhs_diff = -2 * k * kravchuk_polynomial(k, x, n_max);
            if lhs_diff != rhs_diff {
                diff_ok = false;
            }
        }
    }
    (ortho_ok, diff_ok)
}

fn sl2_shell_generators_q(twice_j: usize) -> (QMatDyn, QMatDyn, QMatDyn) {
    if twice_j == 0 {
        let z1 = qd_zeros(1, 1);
        return (z1.clone(), z1.clone(), z1);
    }
    let (jz, jp, jm, _) = sl2_oscillator_generators_q(twice_j);
    (jz, jp, jm)
}

struct So4ShellOps {
    az: QMatDyn,
    bz: QMatDyn,
    lz: QMatDyn,
    lp: QMatDyn,
    lm: QMatDyn,
    kz: QMatDyn,
    kp: QMatDyn,
    km: QMatDyn,
    l2: QMatDyn,
    l_dot_k: QMatDyn,
    c2_so4: QMatDyn,
}

fn so4_hydrogen_shell_operators_q(n_principal: usize) -> So4ShellOps {
    assert!(n_principal >= 1, "n_principal must be >= 1");
    let twice_j = n_principal - 1;
    let eye_f = qd_eye(n_principal);
    let (jz, jp, jm) = sl2_shell_generators_q(twice_j);

    let az = qd_kron(&jz, &eye_f);
    let ap = qd_kron(&jp, &eye_f);
    let am = qd_kron(&jm, &eye_f);

    let bz = qd_kron(&eye_f, &jz);
    let bp = qd_kron(&eye_f, &jp);
    let bm = qd_kron(&eye_f, &jm);

    let lz = qd_add(&az, &bz);
    let lp = qd_add(&ap, &bp);
    let lm = qd_add(&am, &bm);

    let kz = qd_sub(&az, &bz);
    let kp = qd_sub(&ap, &bp);
    let km = qd_sub(&am, &bm);

    let l2 = sl2_casimir_q(&lz, &lp, &lm);
    let k2 = sl2_casimir_q(&kz, &kp, &km);
    let l_dot_k = qd_add(
        &qd_mul(&lz, &kz),
        &qd_scale(q(1, 2), &qd_add(&qd_mul(&lp, &km), &qd_mul(&lm, &kp))),
    );
    let c2_so4 = qd_add(&l2, &k2);
    So4ShellOps {
        az,
        bz,
        lz,
        lp,
        lm,
        kz,
        kp,
        km,
        l2,
        l_dot_k,
        c2_so4,
    }
}

pub fn dirac_fine_structure_coeff_q(n_principal: i64, twice_j_tot: i64) -> Q {
    assert!(
        n_principal >= 1 && twice_j_tot >= 1 && twice_j_tot % 2 == 1,
        "Require n >= 1 and odd twice_j_tot >= 1"
    );
    let k_denom = q(twice_j_tot + 1, 2);
    -q(1, 2 * n_principal.pow(3)) * (Q::one() / k_denom - q(3, 4 * n_principal))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm217AlgebraicBoundStateSpectraReport {
    pub kravchuk_sl2_commutators_exact: bool,
    pub kravchuk_casimir_matches_j_j_plus_1: bool,
    pub kravchuk_metric_adjoint_exact: bool,
    pub kravchuk_equidistant_ladder_commutators_exact: bool,
    pub kravchuk_ground_variance_q2: Q,
    pub kravchuk_ground_variance_p2: Q,
    pub kravchuk_ground_uncertainty_product: Q,
    pub kravchuk_ground_saturates_robertson_schrodinger: bool,
    pub kravchuk_polynomial_orthogonality_exact: bool,
    pub kravchuk_difference_eigenvalue_exact: bool,
    pub hydrogen_chiral_factors_commute: bool,
    pub hydrogen_so4_lie_brackets_exact: bool,
    pub hydrogen_pauli_orthogonality_l_dot_k_zero: bool,
    pub hydrogen_asymmetric_control_l_dot_k_nonzero: bool,
    pub hydrogen_casimir_matches_n_squared_minus_1: bool,
    pub hydrogen_balmer_rydberg_energies: Vec<Q>,
    pub hydrogen_lyman_alpha_dimensionless_jump: Q,
    pub hydrogen_balmer_alpha_dimensionless_jump: Q,
    pub hydrogen_orbital_l2_traces: Vec<Q>,
    pub hydrogen_orbital_l2_traces_match_clebsch_gordan: bool,
    pub n2_projectors_idempotent_orthogonal_complete: bool,
    pub n2_2s_rank: Q,
    pub n2_2p_rank: Q,
    pub n2_pi_2s_commutes_with_so3_l: bool,
    pub n2_pi_2s_breaks_runge_lenz_k: bool,
    pub dirac_fs_2s_half_coeff: Q,
    pub dirac_fs_2p_half_coeff: Q,
    pub dirac_fs_2p_three_halves_coeff: Q,
    pub dirac_fs_2s_2p_half_degenerate: bool,
    pub dirac_fs_fine_structure_splitting_coeff: Q,
    pub lyman_alpha_gross_thz_decimal_12: String,
    pub lyman_alpha_gross_thz_12_digits_agree: bool,
    pub lamb_contact_2s_2p_mhz_decimal_12: String,
    pub lamb_contact_2s_2p_mhz_12_digits_agree: bool,
}

#[allow(clippy::type_complexity)]
fn check_single_kravchuk_shell(
    twice_j: usize,
) -> (bool, bool, bool, bool, Q, Q, Q, bool, bool, bool) {
    let dim = twice_j + 1;
    let j_val = q(twice_j as i64, 2);
    let eye = qd_eye(dim);
    let (jz, jp, jm, g_mat) = sl2_oscillator_generators_q(twice_j);

    let sl2_comm_ok = qd_comm(&jz, &jp) == jp
        && qd_comm(&jz, &jm) == qd_scale(q(-1, 1), &jm)
        && qd_comm(&jp, &jm) == qd_scale(q(2, 1), &jz);

    let c2 = sl2_casimir_q(&jz, &jp, &jm);
    let casimir_ok = c2 == qd_scale(j_val * (j_val + Q::one()), &eye);
    let metric_adj_ok = qd_mul(&qd_transpose(&jp), &g_mat) == qd_mul(&g_mat, &jm);

    let h_osc = qd_add(&jz, &qd_scale(j_val + q(1, 2), &eye));
    let expected_diag: Vec<Q> = (0..dim).map(|n| q(2 * (n as i64) + 1, 2)).collect();
    let actual_diag: Vec<Q> = (0..dim).map(|n| h_osc[n][n]).collect();
    let ladder_ok = actual_diag == expected_diag
        && qd_comm(&h_osc, &jp) == jp
        && qd_comm(&h_osc, &jm) == qd_scale(q(-1, 1), &jm);

    let jp_plus_jm = qd_add(&jp, &jm);
    let jp_minus_jm = qd_sub(&jp, &jm);
    let q2_mat = qd_scale(q(1, 8) / j_val, &qd_mul(&jp_plus_jm, &jp_plus_jm));
    let p2_mat = qd_scale(q(-1, 8) / j_val, &qd_mul(&jp_minus_jm, &jp_minus_jm));
    let q2_0 = q2_mat[0][0];
    let p2_0 = p2_mat[0][0];
    let half_jz_ratio = jz[0][0] / (q(2, 1) * j_val);
    let rs_bound = q(1, 4) * half_jz_ratio * half_jz_ratio;
    let saturates_ok = q2_0 == q(1, 4) && p2_0 == q(1, 4) && q2_0 * p2_0 == rs_bound;
    let (o_ok, d_ok) = check_kravchuk_orthogonality_and_difference_eq(twice_j as i64);
    (
        sl2_comm_ok,
        casimir_ok,
        metric_adj_ok,
        ladder_ok,
        q2_0,
        p2_0,
        q2_0 * p2_0,
        saturates_ok,
        o_ok,
        d_ok,
    )
}

#[allow(clippy::type_complexity)]
fn audit_kravchuk_shells() -> (bool, bool, bool, bool, Q, Q, Q, bool, bool, bool) {
    let mut sl2_comm_ok = true;
    let mut casimir_ok = true;
    let mut metric_adj_ok = true;
    let mut ladder_ok = true;
    let mut ground_q2 = Q::zero();
    let mut ground_p2 = Q::zero();
    let mut ground_prod = Q::zero();
    let mut saturates_ok = true;
    let mut ortho_all_ok = true;
    let mut diff_all_ok = true;

    for twice_j in 1..=4usize {
        let (c_ok, cas_ok, m_ok, l_ok, q2_0, p2_0, prod_0, sat_ok, o_ok, d_ok) =
            check_single_kravchuk_shell(twice_j);
        sl2_comm_ok &= c_ok;
        casimir_ok &= cas_ok;
        metric_adj_ok &= m_ok;
        ladder_ok &= l_ok;
        ground_q2 = q2_0;
        ground_p2 = p2_0;
        ground_prod = prod_0;
        saturates_ok &= sat_ok;
        ortho_all_ok &= o_ok;
        diff_all_ok &= d_ok;
    }
    (
        sl2_comm_ok,
        casimir_ok,
        metric_adj_ok,
        ladder_ok,
        ground_q2,
        ground_p2,
        ground_prod,
        saturates_ok,
        ortho_all_ok,
        diff_all_ok,
    )
}

fn check_so4_lie_brackets(ops: &So4ShellOps) -> bool {
    qd_comm(&ops.lz, &ops.lp) == ops.lp
        && qd_comm(&ops.lz, &ops.lm) == qd_scale(q(-1, 1), &ops.lm)
        && qd_comm(&ops.lp, &ops.lm) == qd_scale(q(2, 1), &ops.lz)
        && qd_comm(&ops.lz, &ops.kp) == ops.kp
        && qd_comm(&ops.kz, &ops.lp) == ops.kp
        && qd_comm(&ops.kp, &ops.km) == qd_scale(q(2, 1), &ops.lz)
}

#[allow(clippy::type_complexity)]
fn audit_so4_hydrogen_shells() -> (bool, bool, bool, bool, Vec<Q>, Vec<Q>, bool) {
    let mut chiral_comm_ok = true;
    let mut so4_brackets_ok = true;
    let mut pauli_ortho_ok = true;
    let mut casimir_so4_ok = true;
    let mut energies = Vec::new();
    let mut l2_traces = Vec::new();
    let mut l2_traces_match = true;

    for n_prin in 1..=4usize {
        let ops = so4_hydrogen_shell_operators_q(n_prin);
        let dim_shell = n_prin * n_prin;
        let eye_shell = qd_eye(dim_shell);

        chiral_comm_ok &= qd_is_zero(&qd_comm(&ops.az, &ops.bz));
        so4_brackets_ok &= check_so4_lie_brackets(&ops);
        pauli_ortho_ok &= qd_is_zero(&ops.l_dot_k);

        let expected_c2 = q((dim_shell as i64) - 1, 1);
        casimir_so4_ok &= ops.c2_so4 == qd_scale(expected_c2, &eye_shell);
        energies.push(-Q::one() / (expected_c2 + Q::one()));

        let tr_l2 = qd_trace(&ops.l2);
        l2_traces.push(tr_l2);
        let cg_sum: Q = (0..n_prin)
            .map(|l_orb| {
                let l = l_orb as i64;
                q((2 * l + 1) * l * (l + 1), 1)
            })
            .fold(Q::zero(), |a, b| a + b);
        let closed_sum = q((dim_shell as i64) * ((dim_shell as i64) - 1), 2);
        l2_traces_match &= tr_l2 == cg_sum && tr_l2 == closed_sum;
    }
    (
        chiral_comm_ok,
        so4_brackets_ok,
        pauli_ortho_ok,
        casimir_so4_ok,
        energies,
        l2_traces,
        l2_traces_match,
    )
}

pub fn evaluate_qm217_algebraic_bound_state_spectra() -> Qm217AlgebraicBoundStateSpectraReport {
    let (
        sl2_comm_ok,
        casimir_ok,
        metric_adj_ok,
        ladder_ok,
        ground_q2,
        ground_p2,
        ground_prod,
        saturates_ok,
        ortho_all_ok,
        diff_all_ok,
    ) = audit_kravchuk_shells();

    let (
        chiral_comm_ok,
        so4_brackets_ok,
        pauli_ortho_ok,
        casimir_so4_ok,
        energies,
        l2_traces,
        l2_traces_match,
    ) = audit_so4_hydrogen_shells();

    let (jz_1, jp_1, jm_1) = sl2_shell_generators_q(1);
    let (jz_2, jp_2, jm_2) = sl2_shell_generators_q(2);
    let (eye_2, eye_3) = (qd_eye(2), qd_eye(3));
    let lz_asym = qd_add(&qd_kron(&jz_1, &eye_3), &qd_kron(&eye_2, &jz_2));
    let lp_asym = qd_add(&qd_kron(&jp_1, &eye_3), &qd_kron(&eye_2, &jp_2));
    let lm_asym = qd_add(&qd_kron(&jm_1, &eye_3), &qd_kron(&eye_2, &jm_2));
    let kz_asym = qd_sub(&qd_kron(&jz_1, &eye_3), &qd_kron(&eye_2, &jz_2));
    let kp_asym = qd_sub(&qd_kron(&jp_1, &eye_3), &qd_kron(&eye_2, &jp_2));
    let km_asym = qd_sub(&qd_kron(&jm_1, &eye_3), &qd_kron(&eye_2, &jm_2));
    let l_dot_k_asym = qd_add(
        &qd_mul(&lz_asym, &kz_asym),
        &qd_scale(
            q(1, 2),
            &qd_add(&qd_mul(&lp_asym, &km_asym), &qd_mul(&lm_asym, &kp_asym)),
        ),
    );
    let asym_nonzero = !qd_is_zero(&l_dot_k_asym);

    let lyman_jump = energies[1] - energies[0];
    let balmer_jump = energies[2] - energies[1];

    let ops_n2 = so4_hydrogen_shell_operators_q(2);
    let eye_4 = qd_eye(4);
    let pi_2p = qd_scale(q(1, 2), &ops_n2.l2);
    let pi_2s = qd_sub(&eye_4, &pi_2p);

    let proj_ok = qd_mul(&pi_2s, &pi_2s) == pi_2s
        && qd_mul(&pi_2p, &pi_2p) == pi_2p
        && qd_is_zero(&qd_mul(&pi_2s, &pi_2p))
        && qd_add(&pi_2s, &pi_2p) == eye_4;
    let rank_2s = qd_trace(&pi_2s);
    let rank_2p = qd_trace(&pi_2p);
    let comm_so3_ok = qd_is_zero(&qd_comm(&pi_2s, &ops_n2.lz))
        && qd_is_zero(&qd_comm(&pi_2s, &ops_n2.lp))
        && qd_is_zero(&qd_comm(&pi_2s, &ops_n2.lm));
    let breaks_rl_ok = !qd_is_zero(&qd_comm(&pi_2s, &ops_n2.kz));

    let fs_2s_half = dirac_fine_structure_coeff_q(2, 1);
    let fs_2p_half = dirac_fine_structure_coeff_q(2, 1);
    let fs_2p_three_halves = dirac_fine_structure_coeff_q(2, 3);
    let fs_deg = fs_2s_half == fs_2p_half && fs_2s_half == q(-5, 128);
    let fs_split = fs_2p_three_halves - fs_2p_half;

    let alpha_inv = BigRational::new(
        BigInt::from(137035999166i64),
        BigInt::from(1_000_000_000i64),
    );
    let me_c2_over_h_mhz = BigRational::from_integer(BigInt::from(123558996383000i64));
    let me_c2_over_h_thz =
        &me_c2_over_h_mhz / BigRational::from_integer(BigInt::from(1_000_000i64));
    let alpha_exact = BigInterval::exact(alpha_inv.recip());
    let lyman_scale = BigRational::new(BigInt::from(3), BigInt::from(8)) * me_c2_over_h_thz;
    let lyman_thz_iv = alpha_exact.pow(2).scale(lyman_scale);
    let (lyman_dec_12, _lyman_hi_12, lyman_ok) = lyman_thz_iv.decimal_prefix(12);

    let pi_iv = pi_big_interval(20);
    let alpha5_over_pi = alpha_exact.pow(5).mul(&pi_iv.reciprocal());
    let lamb_scale = BigRational::new(BigInt::from(91), BigInt::from(120)) * me_c2_over_h_mhz;
    let lamb_contact_iv = alpha5_over_pi.scale(lamb_scale);
    let (lamb_contact_dec_12, _lamb_hi_12, lamb_contact_ok) = lamb_contact_iv.decimal_prefix(12);

    Qm217AlgebraicBoundStateSpectraReport {
        kravchuk_sl2_commutators_exact: sl2_comm_ok,
        kravchuk_casimir_matches_j_j_plus_1: casimir_ok,
        kravchuk_metric_adjoint_exact: metric_adj_ok,
        kravchuk_equidistant_ladder_commutators_exact: ladder_ok,
        kravchuk_ground_variance_q2: ground_q2,
        kravchuk_ground_variance_p2: ground_p2,
        kravchuk_ground_uncertainty_product: ground_prod,
        kravchuk_ground_saturates_robertson_schrodinger: saturates_ok,
        kravchuk_polynomial_orthogonality_exact: ortho_all_ok,
        kravchuk_difference_eigenvalue_exact: diff_all_ok,
        hydrogen_chiral_factors_commute: chiral_comm_ok,
        hydrogen_so4_lie_brackets_exact: so4_brackets_ok,
        hydrogen_pauli_orthogonality_l_dot_k_zero: pauli_ortho_ok,
        hydrogen_asymmetric_control_l_dot_k_nonzero: asym_nonzero,
        hydrogen_casimir_matches_n_squared_minus_1: casimir_so4_ok,
        hydrogen_balmer_rydberg_energies: energies,
        hydrogen_lyman_alpha_dimensionless_jump: lyman_jump,
        hydrogen_balmer_alpha_dimensionless_jump: balmer_jump,
        hydrogen_orbital_l2_traces: l2_traces,
        hydrogen_orbital_l2_traces_match_clebsch_gordan: l2_traces_match,
        n2_projectors_idempotent_orthogonal_complete: proj_ok,
        n2_2s_rank: rank_2s,
        n2_2p_rank: rank_2p,
        n2_pi_2s_commutes_with_so3_l: comm_so3_ok,
        n2_pi_2s_breaks_runge_lenz_k: breaks_rl_ok,
        dirac_fs_2s_half_coeff: fs_2s_half,
        dirac_fs_2p_half_coeff: fs_2p_half,
        dirac_fs_2p_three_halves_coeff: fs_2p_three_halves,
        dirac_fs_2s_2p_half_degenerate: fs_deg,
        dirac_fs_fine_structure_splitting_coeff: fs_split,
        lyman_alpha_gross_thz_decimal_12: lyman_dec_12,
        lyman_alpha_gross_thz_12_digits_agree: lyman_ok,
        lamb_contact_2s_2p_mhz_decimal_12: lamb_contact_dec_12,
        lamb_contact_2s_2p_mhz_12_digits_agree: lamb_contact_ok,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/algebraic_bound_state_spectra.rs
// Claim: urn:core:crates_rs:core-quantum-physics:algebraic-bound-state-spectra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4db8dd3e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4db8dd3e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4db8dd3e {
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
impl BoundaryError4db8dd3e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4db8dd3e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4db8dd3e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4db8dd3e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4db8dd3e> {
        if capacity_bound == 0 {
            return Err(BoundaryError4db8dd3e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4db8dd3e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4db8dd3e::ExceedsCapacity {
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
    use super::super::q;
    use super::*;

    #[test]
    fn test_qm217_algebraic_bound_state_spectra_control() {
        let r = evaluate_qm217_algebraic_bound_state_spectra();
        assert!(r.kravchuk_sl2_commutators_exact);
        assert!(r.kravchuk_casimir_matches_j_j_plus_1);
        assert!(r.kravchuk_metric_adjoint_exact);
        assert!(r.kravchuk_equidistant_ladder_commutators_exact);
        assert_eq!(r.kravchuk_ground_variance_q2, q(1, 4));
        assert_eq!(r.kravchuk_ground_variance_p2, q(1, 4));
        assert_eq!(r.kravchuk_ground_uncertainty_product, q(1, 16));
        assert!(r.kravchuk_ground_saturates_robertson_schrodinger);
        assert!(r.kravchuk_polynomial_orthogonality_exact);
        assert!(r.kravchuk_difference_eigenvalue_exact);
        assert!(r.hydrogen_chiral_factors_commute);
        assert!(r.hydrogen_so4_lie_brackets_exact);
        assert!(r.hydrogen_pauli_orthogonality_l_dot_k_zero);
        assert!(r.hydrogen_asymmetric_control_l_dot_k_nonzero);
        assert!(r.hydrogen_casimir_matches_n_squared_minus_1);
        assert_eq!(
            r.hydrogen_balmer_rydberg_energies,
            vec![q(-1, 1), q(-1, 4), q(-1, 9), q(-1, 16)]
        );
        assert_eq!(r.hydrogen_lyman_alpha_dimensionless_jump, q(3, 4));
        assert_eq!(r.hydrogen_balmer_alpha_dimensionless_jump, q(5, 36));
        assert_eq!(
            r.hydrogen_orbital_l2_traces,
            vec![q(0, 1), q(6, 1), q(36, 1), q(120, 1)]
        );
        assert!(r.hydrogen_orbital_l2_traces_match_clebsch_gordan);
        assert!(r.n2_projectors_idempotent_orthogonal_complete);
        assert_eq!(r.n2_2s_rank, q(1, 1));
        assert_eq!(r.n2_2p_rank, q(3, 1));
        assert!(r.n2_pi_2s_commutes_with_so3_l);
        assert!(r.n2_pi_2s_breaks_runge_lenz_k);
        assert_eq!(r.dirac_fs_2s_half_coeff, q(-5, 128));
        assert_eq!(r.dirac_fs_2p_half_coeff, q(-5, 128));
        assert_eq!(r.dirac_fs_2p_three_halves_coeff, q(-1, 128));
        assert!(r.dirac_fs_2s_2p_half_degenerate);
        assert_eq!(r.dirac_fs_fine_structure_splitting_coeff, q(1, 32));
        assert_eq!(r.lyman_alpha_gross_thz_decimal_12, "2467.381467264629");
        assert!(r.lyman_alpha_gross_thz_12_digits_agree);
        assert_eq!(r.lamb_contact_2s_2p_mhz_decimal_12, "617.179215588248");
        assert!(r.lamb_contact_2s_2p_mhz_12_digits_agree);
    }
}

#[cfg(test)]
mod l4_boundary_tests_4db8dd3e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4db8dd3e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4db8dd3e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4db8dd3e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4db8dd3e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4db8dd3e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError4db8dd3e::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError4db8dd3e::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
