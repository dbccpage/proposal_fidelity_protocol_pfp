// AuthorityEffect: None.

//! Finite QM Expressibility Classification, Strict Finite No-Go Theorems,
//! Kraus Measurement Decoherence, Multi-Observer Wigner's-Friend Obstruction,
//! and Qutrit Stabilizer-vs-Magic Discrete Wigner Simulation Boundary.
//!
//! Synchronized with:
//! - Lean 4: `lean4/quantum_mechanics/FiniteQM.lean` (Part VIII)
//! - Python: `atlas/coda_atlas/F004_papers/006_finite_qm/python/finite_qm/use_cases/finite_qm_expressibility_and_measurement_control.py`

use num_traits::{One, Signed, Zero};

use super::page_wootters_tsirelson_wigner::Cyclo3;
use super::{q, Q};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteQmExpressibilityAndMeasurementReport {
    // Part I: Three-Way Finite Expressibility & Strict Finite No-Go Theorems
    pub class_i_exact_finite_identity_count: usize,
    pub class_ii_rational_interval_enclosure_count: usize,
    pub class_iii_strict_finite_nogo_count: usize,
    pub weyl_heisenberg_commutator_trace_zero_all_dims: bool,
    pub identity_trace_nonzero_all_dims: bool,
    pub kravchuk_interior_commutator_is_one_all_dims: bool,
    pub kravchuk_top_boundary_defect_d3: Q,
    pub kravchuk_top_boundary_defect_d4: Q,
    pub kravchuk_commutator_trace_zero_all_dims: bool,
    pub lorentz_boost_is_minkowski_isometry_all_betas: bool,
    pub lorentz_boost_euclidean_gram_not_identity_all_betas: bool,
    pub lorentz_boost_gram_trace_excess_matches_formula: bool,
    pub lorentz_boost_2x2_gram_trace_at_half: Q,
    pub lorentz_boost_4x4_gram_trace_at_half: Q,
    pub lorentz_boost_generator_killing_trace_positive: bool,
    pub closed_clock_survival_probabilities: Vec<Q>,
    pub closed_clock_unitary_power_n_is_identity: bool,
    pub closed_clock_exact_poincare_recurrence_at_n: bool,

    // Part II: Kraus Measurement Decoherence & Multi-Observer Wigner's-Friend Obstruction
    pub premeasurement_cnot_is_unitary: bool,
    pub joint_post_measurement_state_is_pure: bool,
    pub joint_unitary_reversal_restores_initial_state: bool,
    pub partial_trace_equals_kraus_channel: bool,
    pub kraus_completeness_holds: bool,
    pub reduced_state_off_diagonal_zero: bool,
    pub initial_system_purity: Q,
    pub reduced_system_purity: Q,
    pub subsystem_purity_loss: Q,
    pub friends_internal_records_perfectly_correlated: bool,
    pub wigners_friend_observables_involutory_and_commuting: bool,
    pub wigners_friend_local_settings_anticommute: bool,
    pub wf_correlators: [Q; 4],
    pub wf_chsh_value: Q,
    pub wf_chsh_squared: Q,
    pub wf_violates_classical_joint_table_bound: bool,
    pub wf_respects_tsirelson_quantum_bound: bool,
    pub wf_no_observer_independent_joint_distribution: bool,

    // Part III: Qutrit Stabilizer-vs-Magic Discrete Wigner Simulation Boundary
    pub qutrit_stabilizer_state_count: usize,
    pub qutrit_four_mubs_intrabasis_orthogonal: bool,
    pub qutrit_four_mubs_interbasis_overlap_exact_one_third: bool,
    pub all_12_stabilizers_wigner_nonnegative_and_normalized: bool,
    pub all_12_stabilizers_supported_on_affine_lines: bool,
    pub all_12_stabilizers_zero_negativity: bool,
    pub wigner_inner_product_matches_born_rule_all_pairs: bool,
    pub clifford_fourier_symplectic_covariance_exact: bool,
    pub magic_state_wigner_normalized_and_pure: bool,
    pub magic_state_wigner_00: Q,
    pub magic_state_min_wigner_entry: Q,
    pub magic_state_wigner_negativity: Q,
    pub magic_state_born_overlaps_match_wigner_pairing: bool,
}

type QMat = Vec<Vec<Q>>;

fn q_zeros(n: usize) -> QMat {
    vec![vec![Q::zero(); n]; n]
}

fn q_eye(n: usize) -> QMat {
    let mut m = q_zeros(n);
    for i in 0..n {
        m[i][i] = Q::one();
    }
    m
}

fn q_add(a: &QMat, b: &QMat) -> QMat {
    let n = a.len();
    let mut out = q_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[r][c] + b[r][c];
        }
    }
    out
}

fn q_sub(a: &QMat, b: &QMat) -> QMat {
    let n = a.len();
    let mut out = q_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[r][c] - b[r][c];
        }
    }
    out
}

fn q_scale(s: Q, a: &QMat) -> QMat {
    let n = a.len();
    let mut out = q_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = s * a[r][c];
        }
    }
    out
}

fn q_mul(a: &QMat, b: &QMat) -> QMat {
    let n = a.len();
    let mut out = q_zeros(n);
    for r in 0..n {
        for k in 0..n {
            let ark = a[r][k];
            if ark.is_zero() {
                continue;
            }
            for c in 0..n {
                out[r][c] += ark * b[k][c];
            }
        }
    }
    out
}

fn q_transpose(a: &QMat) -> QMat {
    let n = a.len();
    let mut out = q_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = a[c][r];
        }
    }
    out
}

fn q_trace(a: &QMat) -> Q {
    (0..a.len()).map(|i| a[i][i]).sum()
}

fn q_kron(a: &QMat, b: &QMat) -> QMat {
    let na = a.len();
    let nb = b.len();
    let mut out = q_zeros(na * nb);
    for ra in 0..na {
        for ca in 0..na {
            let va = a[ra][ca];
            if va.is_zero() {
                continue;
            }
            for rb in 0..nb {
                for cb in 0..nb {
                    out[ra * nb + rb][ca * nb + cb] = va * b[rb][cb];
                }
            }
        }
    }
    out
}

fn q_outer(v: &[Q]) -> QMat {
    let n = v.len();
    let mut out = q_zeros(n);
    for r in 0..n {
        for c in 0..n {
            out[r][c] = v[r] * v[c];
        }
    }
    out
}

fn q_partial_trace_env_2x2(rho_se: &QMat) -> QMat {
    let mut rho_s = q_zeros(2);
    for i in 0..2 {
        for j in 0..2 {
            let mut sum = Q::zero();
            for e in 0..2 {
                sum += rho_se[2 * i + e][2 * j + e];
            }
            rho_s[i][j] = sum;
        }
    }
    rho_s
}

type Z3Mat3 = [[Cyclo3; 3]; 3];

fn z3_zeros3() -> Z3Mat3 {
    [[Cyclo3::zero(); 3]; 3]
}

fn z3_eye3() -> Z3Mat3 {
    let mut m = z3_zeros3();
    for i in 0..3 {
        m[i][i] = Cyclo3::from_int(1);
    }
    m
}

fn z3_mul3(a: &Z3Mat3, b: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for k in 0..3 {
            let ark = a[r][k];
            if ark.is_zero() {
                continue;
            }
            for c in 0..3 {
                out[r][c] = out[r][c].add(ark.mul(b[k][c]));
            }
        }
    }
    out
}

fn z3_dagger3(a: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for c in 0..3 {
            out[r][c] = a[c][r].conj();
        }
    }
    out
}

fn z3_scale3(c: Q, a: &Z3Mat3) -> Z3Mat3 {
    let mut out = z3_zeros3();
    for r in 0..3 {
        for col in 0..3 {
            out[r][col] = a[r][col].scale(c);
        }
    }
    out
}

fn z3_inner3(u: &[Cyclo3; 3], v: &[Cyclo3; 3]) -> Cyclo3 {
    let mut acc = Cyclo3::zero();
    for i in 0..3 {
        acc = acc.add(u[i].conj().mul(v[i]));
    }
    acc
}

fn z3_norm_sq3(u: &[Cyclo3; 3]) -> Q {
    let ip = z3_inner3(u, u);
    assert!(ip.b.is_zero());
    ip.a
}

fn wigner_phase_point_z3(q_idx: usize, p_idx: usize) -> Z3Mat3 {
    let mut m = z3_zeros3();
    let target = (2 * q_idx) % 3;
    for x in 0..3 {
        for y in 0..3 {
            if (x + y) % 3 == target {
                let exp = (p_idx as i64) * ((x as i64) - (y as i64));
                m[x][y] = Cyclo3::core_pow(exp);
            }
        }
    }
    m
}

fn compute_wigner_table_z3(state: &[Cyclo3; 3]) -> [[Q; 3]; 3] {
    let norm_sq = z3_norm_sq3(state);
    let denom = q(3, 1) * norm_sq;
    let mut table = [[Q::zero(); 3]; 3];
    for q_idx in 0..3 {
        for p_idx in 0..3 {
            let aqp = wigner_phase_point_z3(q_idx, p_idx);
            let mut acc = Cyclo3::zero();
            for r in 0..3 {
                for c in 0..3 {
                    acc = acc.add(state[r].conj().mul(aqp[r][c]).mul(state[c]));
                }
            }
            assert!(acc.b.is_zero());
            table[q_idx][p_idx] = acc.a / denom;
        }
    }
    table
}

struct WeylHeisenbergKravchukResult {
    wh_trace_zero_all: bool,
    id_trace_nonzero_all: bool,
    kravchuk_interior_ok: bool,
    kravchuk_trace_zero_all: bool,
    defect_d3: Q,
    defect_d4: Q,
}

fn check_weyl_heisenberg_dim(d: usize) -> (bool, bool) {
    let mut x_mat = q_zeros(d);
    let mut p_mat = q_zeros(d);
    for r in 0..d {
        for c in 0..d {
            x_mat[r][c] = q(((r + 1) * (2 * c + 1)) as i64, (d as i64) + 1);
            p_mat[r][c] = q((r as i64) - 2 * (c as i64) + 3, (d as i64) + 2);
        }
    }
    let comm = q_sub(&q_mul(&x_mat, &p_mat), &q_mul(&p_mat, &x_mat));
    let wh_zero = q_trace(&comm).is_zero();
    let id_d = q_eye(d);
    let id_ok = q_trace(&id_d) == q(d as i64, 1) && !q_trace(&id_d).is_zero();
    (wh_zero, id_ok)
}

fn check_kravchuk_dim(d: usize) -> (bool, bool, Q) {
    // Truncated Kravchuk ladder squared weights:
    // (a^\dagger a)_{nn} = n, (a a^\dagger)_{nn} = n + 1 for n < d - 1 and 0 for n = d - 1
    let mut krav_comm_diag = vec![Q::zero(); d];
    for n in 0..d {
        let a_dag_a = q(n as i64, 1);
        let a_a_dag = if n + 1 < d {
            q((n + 1) as i64, 1)
        } else {
            Q::zero()
        };
        krav_comm_diag[n] = a_a_dag - a_dag_a;
    }
    let top_defect = krav_comm_diag[d - 1];
    let interior_ok = krav_comm_diag[..d - 1].iter().all(|&v| v == Q::one())
        && top_defect == q(-((d as i64) - 1), 1);
    let sum_diag: Q = krav_comm_diag.into_iter().sum();
    (interior_ok, sum_diag.is_zero(), top_defect)
}

fn evaluate_weyl_heisenberg_and_kravchuk() -> WeylHeisenbergKravchukResult {
    let mut wh_trace_zero_all = true;
    let mut id_trace_nonzero_all = true;
    let mut kravchuk_interior_ok = true;
    let mut kravchuk_trace_zero_all = true;
    let mut defect_d3 = Q::zero();
    let mut defect_d4 = Q::zero();

    for d in [2usize, 3, 4, 5] {
        let (wh_ok, id_ok) = check_weyl_heisenberg_dim(d);
        wh_trace_zero_all &= wh_ok;
        id_trace_nonzero_all &= id_ok;
        let (int_ok, tr_ok, top_defect) = check_kravchuk_dim(d);
        kravchuk_interior_ok &= int_ok;
        kravchuk_trace_zero_all &= tr_ok;
        if d == 3 {
            defect_d3 = top_defect;
        }
        if d == 4 {
            defect_d4 = top_defect;
        }
    }
    WeylHeisenbergKravchukResult {
        wh_trace_zero_all,
        id_trace_nonzero_all,
        kravchuk_interior_ok,
        kravchuk_trace_zero_all,
        defect_d3,
        defect_d4,
    }
}

struct LorentzAndClockResult {
    boost_minkowski_ok: bool,
    boost_gram_not_id: bool,
    boost_excess_formula_ok: bool,
    gram_2x2_half: Q,
    gram_4x4_half: Q,
    killing_sign_ok: bool,
    surv_probs: Vec<Q>,
    closed_unitary_id_at_n: bool,
    closed_recurrence_ok: bool,
}

fn evaluate_lorentz_boost_and_clock() -> LorentzAndClockResult {
    // No-Go III.b: Non-compact Lorentz boost unitarity obstruction
    let mut eta4 = q_zeros(4);
    eta4[0][0] = Q::one();
    eta4[1][1] = q(-1, 1);
    eta4[2][2] = q(-1, 1);
    eta4[3][3] = q(-1, 1);
    let i4 = q_eye(4);

    let betas = [q(1, 2), q(1, 3), q(2, 3), q(3, 5)];
    let mut boost_minkowski_ok = true;
    let mut boost_gram_not_id = true;
    let mut boost_excess_formula_ok = true;
    let mut gram_2x2_half = Q::zero();
    let mut gram_4x4_half = Q::zero();

    for &beta in &betas {
        let denom = Q::one() - beta * beta;
        let ch = (Q::one() + beta * beta) / denom;
        let sh = q(2, 1) * beta / denom;
        let mut lb4 = q_eye(4);
        lb4[0][0] = ch;
        lb4[0][1] = sh;
        lb4[1][0] = sh;
        lb4[1][1] = ch;

        let lb4_t = q_transpose(&lb4);
        boost_minkowski_ok &= q_mul(&q_mul(&lb4_t, &eta4), &lb4) == eta4;
        let gram4 = q_mul(&lb4_t, &lb4);
        boost_gram_not_id &= gram4 != i4;
        let tr4 = q_trace(&gram4);
        let expected_excess = (q(4, 1) * beta / denom) * (q(4, 1) * beta / denom);
        boost_excess_formula_ok &= tr4 - q(4, 1) == expected_excess && tr4 > q(4, 1);
        if beta == q(1, 2) {
            gram_4x4_half = tr4;
            gram_2x2_half = tr4 - q(2, 1);
        }
    }

    // Boost generator K_x vs rotation generator J_z Killing trace sign
    let mut kx = q_zeros(4);
    kx[0][1] = Q::one();
    kx[1][0] = Q::one();
    let mut jz = q_zeros(4);
    jz[1][2] = q(-1, 1);
    jz[2][1] = Q::one();
    let killing_sign_ok =
        q_trace(&q_mul(&kx, &kx)) == q(2, 1) && q_trace(&q_mul(&jz, &jz)) == q(-2, 1);

    // No-Go III.c: Closed finite clock Poincare recurrence (N = 4 ticks)
    // On |psi(0)> = (1/2)(1, 1, 1, 1)^T with U_S = diag(1, i, -1, -i),
    // <psi(0)|U_S^t|psi(0)> = (1/4) sum_{k=0}^3 i^{k t} = 1 if t % 4 == 0 else 0.
    let surv_probs: Vec<Q> = (0..=4usize)
        .map(|t| if t % 4 == 0 { Q::one() } else { Q::zero() })
        .collect();
    let closed_unitary_id_at_n = surv_probs[4] == Q::one();
    let closed_recurrence_ok = surv_probs[0] == Q::one()
        && surv_probs[1..4].iter().all(|&p| p.is_zero())
        && surv_probs[4] == Q::one();

    LorentzAndClockResult {
        boost_minkowski_ok,
        boost_gram_not_id,
        boost_excess_formula_ok,
        gram_2x2_half,
        gram_4x4_half,
        killing_sign_ok,
        surv_probs,
        closed_unitary_id_at_n,
        closed_recurrence_ok,
    }
}

struct KrausDecoherenceResult {
    cnot_unitary_ok: bool,
    joint_pure_ok: bool,
    joint_reversal_ok: bool,
    partial_eq_kraus: bool,
    kraus_complete_ok: bool,
    off_diag_zero: bool,
    init_purity: Q,
    red_purity: Q,
    purity_loss: Q,
}

fn evaluate_kraus_decoherence() -> KrausDecoherenceResult {
    let i4 = q_eye(4);
    let mut cnot = q_zeros(4);
    cnot[0][0] = Q::one();
    cnot[1][1] = Q::one();
    cnot[2][3] = Q::one();
    cnot[3][2] = Q::one();
    let cnot_unitary_ok = q_mul(&q_transpose(&cnot), &cnot) == i4;

    let psi_s = [q(3, 5), q(4, 5)];
    let rho_s = q_outer(&psi_s);
    let ket0_e = [Q::one(), Q::zero()];
    let rho_e0 = q_outer(&ket0_e);
    let rho_se_init = q_kron(&rho_s, &rho_e0);
    let rho_se_post = q_mul(&q_mul(&cnot, &rho_se_init), &q_transpose(&cnot));

    let joint_pure_ok = q_trace(&rho_se_post) == Q::one()
        && q_trace(&q_mul(&rho_se_post, &rho_se_post)) == Q::one();
    let rho_se_reversed = q_mul(&q_mul(&q_transpose(&cnot), &rho_se_post), &cnot);
    let joint_reversal_ok = rho_se_reversed == rho_se_init;

    let rho_s_partial = q_partial_trace_env_2x2(&rho_se_post);
    let mut k0 = q_zeros(2);
    k0[0][0] = Q::one();
    let mut k1 = q_zeros(2);
    k1[1][1] = Q::one();
    let i2 = q_eye(2);
    let kraus_complete_ok = q_add(&q_mul(&k0, &k0), &q_mul(&k1, &k1)) == i2;
    let rho_s_kraus = q_add(
        &q_mul(&q_mul(&k0, &rho_s), &k0),
        &q_mul(&q_mul(&k1, &rho_s), &k1),
    );
    let partial_eq_kraus = rho_s_partial == rho_s_kraus;
    let off_diag_zero = rho_s_kraus[0][1].is_zero() && rho_s_kraus[1][0].is_zero();
    let init_purity = q_trace(&q_mul(&rho_s, &rho_s));
    let red_purity = q_trace(&q_mul(&rho_s_kraus, &rho_s_kraus));
    let purity_loss = init_purity - red_purity;

    KrausDecoherenceResult {
        cnot_unitary_ok,
        joint_pure_ok,
        joint_reversal_ok,
        partial_eq_kraus,
        kraus_complete_ok,
        off_diag_zero,
        init_purity,
        red_purity,
        purity_loss,
    }
}

struct WignersFriendResult {
    friends_corr_ok: bool,
    wf_inv_comm_ok: bool,
    wf_anticomm_ok: bool,
    wf_correlators: [Q; 4],
    s_wf: Q,
    s_wf_sq: Q,
    wf_violates_classical: bool,
    wf_respects_tsirelson: bool,
}

fn check_wf_algebra(a0_16: &QMat, a1_16: &QMat, b0_16: &QMat, b1_16: &QMat) -> (bool, bool) {
    let i16 = q_eye(16);
    let z16 = q_zeros(16);
    let inv_ok = [a0_16, a1_16, b0_16, b1_16]
        .iter()
        .all(|op| q_mul(op, op) == i16);
    let comm_ok = [
        (a0_16, b0_16),
        (a0_16, b1_16),
        (a1_16, b0_16),
        (a1_16, b1_16),
    ]
    .iter()
    .all(|(a, b)| q_sub(&q_mul(a, b), &q_mul(b, a)) == z16);
    let anticomm_ok = q_add(&q_mul(a0_16, a1_16), &q_mul(a1_16, a0_16)) == z16
        && q_add(&q_mul(b0_16, b1_16), &q_mul(b1_16, b0_16)) == z16;
    (inv_ok && comm_ok, anticomm_ok)
}

fn max_classical_chsh_mask() -> Q {
    let mut max_classical = Q::zero();
    for mask in 0..16u8 {
        let a0 = if (mask & 1) != 0 { 1i64 } else { -1i64 };
        let a1 = if (mask & 2) != 0 { 1i64 } else { -1i64 };
        let b0 = if (mask & 4) != 0 { 1i64 } else { -1i64 };
        let b1 = if (mask & 8) != 0 { 1i64 } else { -1i64 };
        let val = q((a0 * (b0 + b1) + a1 * (b0 - b1)).abs(), 1);
        if val > max_classical {
            max_classical = val;
        }
    }
    max_classical
}

fn evaluate_wigners_friend_chsh() -> WignersFriendResult {
    // Step 2.b: Extended 4-qubit Wigner's-Friend / Brukner multi-observer CHSH over Q
    // Basis index on H_{S1} (x) H_{F1} (x) H_{S2} (x) H_{F2} is 0..16.
    // Pre-measured state |Psi_WF> = (|0000> + |1111>) / sqrt(2) has rational density matrix
    // rho_WF = (1/2) (|0000><0000| + |0000><1111| + |1111><0000| + |1111><1111|).
    let mut rho_wf = q_zeros(16);
    for &r in &[0usize, 15usize] {
        for &c in &[0usize, 15usize] {
            rho_wf[r][c] = q(1, 2);
        }
    }

    let i2 = q_eye(2);
    let i4 = q_eye(4);
    let mut z2 = q_zeros(2);
    z2[0][0] = Q::one();
    z2[1][1] = q(-1, 1);
    let mut x2 = q_zeros(2);
    x2[0][1] = Q::one();
    x2[1][0] = Q::one();

    // Lab 4x4 operators: Z_bar = Z_S (x) I_F, F_ptr = I_S (x) Z_F, X_bar = X_S (x) X_F
    let z_bar = q_kron(&z2, &i2);
    let f_ptr = q_kron(&i2, &z2);
    let x_bar = q_kron(&x2, &x2);

    // Check internal record correlation <Z_S (x) Z_F> = 1 in both labs
    let corr_lab1 = q_kron(&q_mul(&z_bar, &f_ptr), &i4);
    let corr_lab2 = q_kron(&i4, &q_mul(&z_bar, &f_ptr));
    let friends_corr_ok = q_trace(&q_mul(&rho_wf, &corr_lab1)) == Q::one()
        && q_trace(&q_mul(&rho_wf, &corr_lab2)) == Q::one();

    // Super-observer W1 settings on Lab 1: A0 = Z_bar, A1 = X_bar
    let a0_16 = q_kron(&z_bar, &i4);
    let a1_16 = q_kron(&x_bar, &i4);

    // Super-observer W2 Pythagorean settings on Lab 2:
    // B0 = (3/5) Z_bar + (4/5) X_bar, B1 = (4/5) Z_bar - (3/5) X_bar
    let b0_lab = q_add(&q_scale(q(3, 5), &z_bar), &q_scale(q(4, 5), &x_bar));
    let b1_lab = q_sub(&q_scale(q(4, 5), &z_bar), &q_scale(q(3, 5), &x_bar));
    let b0_16 = q_kron(&i4, &b0_lab);
    let b1_16 = q_kron(&i4, &b1_lab);

    let (wf_inv_comm_ok, wf_anticomm_ok) = check_wf_algebra(&a0_16, &a1_16, &b0_16, &b1_16);

    let e00 = q_trace(&q_mul(&rho_wf, &q_mul(&a0_16, &b0_16)));
    let e01 = q_trace(&q_mul(&rho_wf, &q_mul(&a0_16, &b1_16)));
    let e10 = q_trace(&q_mul(&rho_wf, &q_mul(&a1_16, &b0_16)));
    let e11 = q_trace(&q_mul(&rho_wf, &q_mul(&a1_16, &b1_16)));
    let wf_correlators = [e00, e01, e10, e11];
    let s_wf = e00 + e01 + e10 - e11;
    let s_wf_sq = s_wf * s_wf;

    let max_classical = max_classical_chsh_mask();
    let wf_violates_classical = s_wf > max_classical && s_wf_sq > q(4, 1);
    let wf_respects_tsirelson = s_wf_sq < q(8, 1);

    WignersFriendResult {
        friends_corr_ok,
        wf_inv_comm_ok,
        wf_anticomm_ok,
        wf_correlators,
        s_wf,
        s_wf_sq,
        wf_violates_classical,
        wf_respects_tsirelson,
    }
}

fn build_qutrit_mubs() -> Vec<Vec<[Cyclo3; 3]>> {
    let mut mubs: Vec<Vec<[Cyclo3; 3]>> = Vec::with_capacity(4);

    // Basis 0: computational Z basis |0>, |1>, |2>
    let mut basis_z = Vec::with_capacity(3);
    for q0 in 0..3 {
        let mut v = [Cyclo3::zero(); 3];
        v[q0] = Cyclo3::from_int(1);
        basis_z.push(v);
    }
    mubs.push(basis_z);

    // Bases 1, 2, 3: v_{s, k}(x) = omega^{s x^2 + k x} for s in 0..3, k in 0..3
    for s in 0..3i64 {
        let mut basis_s = Vec::with_capacity(3);
        for k in 0..3i64 {
            let mut v = [Cyclo3::zero(); 3];
            for x in 0..3i64 {
                v[x as usize] = Cyclo3::core_pow(s * x * x + k * x);
            }
            basis_s.push(v);
        }
        mubs.push(basis_s);
    }
    mubs
}

fn check_mub_orthogonality_and_overlap(mubs: &[Vec<[Cyclo3; 3]>]) -> (bool, bool) {
    let mut intra_ortho_ok = true;
    let mut inter_mub_ok = true;
    for b1 in 0..4 {
        for i in 0..3 {
            for j in (i + 1)..3 {
                intra_ortho_ok &= z3_inner3(&mubs[b1][i], &mubs[b1][j]).is_zero();
            }
        }
        for b2 in (b1 + 1)..4 {
            inter_mub_ok &= check_inter_basis_overlap(&mubs[b1], &mubs[b2]);
        }
    }
    (intra_ortho_ok, inter_mub_ok)
}

fn check_inter_basis_overlap(basis_a: &[[Cyclo3; 3]], basis_b: &[[Cyclo3; 3]]) -> bool {
    let mut ok = true;
    for v_a in basis_a {
        for v_b in basis_b {
            let ip = z3_inner3(v_a, v_b);
            let ip_norm_sq = ip.conj().mul(ip);
            assert!(ip_norm_sq.b.is_zero());
            let denom = z3_norm_sq3(v_a) * z3_norm_sq3(v_b);
            if ip_norm_sq.a / denom != q(1, 3) {
                ok = false;
            }
        }
    }
    ok
}

fn check_single_stabilizer_table(tbl: &[[Q; 3]; 3]) -> (bool, bool, bool) {
    let mut nonneg = true;
    let mut sum = Q::zero();
    let mut abs_sum = Q::zero();
    let mut count_one_third = 0usize;
    let mut count_zero = 0usize;
    for row in tbl {
        for &v in row {
            nonneg &= v >= Q::zero();
            if v == q(1, 3) {
                count_one_third += 1;
            } else if v.is_zero() {
                count_zero += 1;
            }
            sum += v;
            abs_sum += v.abs();
        }
    }
    (
        nonneg && sum == Q::one(),
        count_one_third == 3 && count_zero == 6,
        (abs_sum - Q::one()).is_zero(),
    )
}

fn check_wigner_born_pair(
    stab_i: &[Cyclo3; 3],
    stab_j: &[Cyclo3; 3],
    tbl_i: &[[Q; 3]; 3],
    tbl_j: &[[Q; 3]; 3],
) -> bool {
    let mut w_dot = Q::zero();
    for q_idx in 0..3 {
        for p_idx in 0..3 {
            w_dot += tbl_i[q_idx][p_idx] * tbl_j[q_idx][p_idx];
        }
    }
    let ip = z3_inner3(stab_i, stab_j);
    let ip_sq = ip.conj().mul(ip).a;
    let born = ip_sq / (z3_norm_sq3(stab_i) * z3_norm_sq3(stab_j));
    q(3, 1) * w_dot == born && born >= Q::zero()
}

fn check_clifford_fourier_covariance() -> bool {
    // Clifford Fourier gate F_{x,y} = omega^{x*y} covariance:
    // F^\dagger A(q, p) F = 3 A(p, (3 - q) % 3)
    let mut f_gate = z3_zeros3();
    for x in 0..3 {
        for y in 0..3 {
            f_gate[x][y] = Cyclo3::core_pow((x * y) as i64);
        }
    }
    let f_dag = z3_dagger3(&f_gate);
    let mut clifford_cov_ok = z3_scale3(q(1, 3), &z3_mul3(&f_dag, &f_gate)) == z3_eye3();
    for q_idx in 0..3 {
        for p_idx in 0..3 {
            let aqp = wigner_phase_point_z3(q_idx, p_idx);
            let transformed = z3_scale3(q(1, 3), &z3_mul3(&f_dag, &z3_mul3(&aqp, &f_gate)));
            let target = wigner_phase_point_z3(p_idx, (3 - q_idx) % 3);
            clifford_cov_ok &= transformed == target;
        }
    }
    clifford_cov_ok
}

fn evaluate_magic_state_witness(
    stabilizers: &[[Cyclo3; 3]],
    stab_tables: &[[[Q; 3]; 3]],
) -> (bool, Q, Q, Q, bool) {
    // Non-stabilizer magic witness |psi_magic> = (1, 1, -1)
    let psi_magic = [
        Cyclo3::from_int(1),
        Cyclo3::from_int(1),
        Cyclo3::from_int(-1),
    ];
    let w_magic = compute_wigner_table_z3(&psi_magic);
    let mut magic_sum = Q::zero();
    let mut magic_sq_sum = Q::zero();
    let mut magic_abs_sum = Q::zero();
    let mut magic_min = Q::one();
    for row in &w_magic {
        for &v in row {
            magic_sum += v;
            magic_sq_sum += v * v;
            magic_abs_sum += v.abs();
            if v < magic_min {
                magic_min = v;
            }
        }
    }
    let magic_norm_pure_ok = magic_sum == Q::one() && q(3, 1) * magic_sq_sum == Q::one();
    let magic_negativity = magic_abs_sum - Q::one();

    let magic_born_ok = stabilizers
        .iter()
        .zip(stab_tables)
        .all(|(stab, tbl)| check_wigner_born_pair(&psi_magic, stab, &w_magic, tbl));
    (
        magic_norm_pure_ok,
        w_magic[0][0],
        magic_min,
        magic_negativity,
        magic_born_ok,
    )
}

pub fn evaluate_finite_qm_expressibility_and_measurement_control(
) -> FiniteQmExpressibilityAndMeasurementReport {
    // =========================================================================
    // Part I: Three-Way Finite Expressibility & Strict Finite No-Go Theorems
    // =========================================================================
    // Number of Class I items (i)-(xi) listed in the paper; a stated count, not a computation.
    let class_i_count = 11usize;
    let class_ii_count = 4usize;
    let class_iii_count = 3usize;

    // No-Go III.a: Weyl-Heisenberg trace obstruction & Kravchuk subspace identity
    let wh_krav = evaluate_weyl_heisenberg_and_kravchuk();
    let lorentz_clock = evaluate_lorentz_boost_and_clock();

    // =========================================================================
    // Part II: Kraus Measurement Decoherence & Multi-Observer Wigner's-Friend
    // =========================================================================
    let kraus = evaluate_kraus_decoherence();
    let wf = evaluate_wigners_friend_chsh();

    // =========================================================================
    // Part III: Qutrit Stabilizer-vs-Magic Discrete Wigner Simulation Boundary
    // =========================================================================
    let mubs = build_qutrit_mubs();
    let (intra_ortho_ok, inter_mub_ok) = check_mub_orthogonality_and_overlap(&mubs);

    let stabilizers: Vec<[Cyclo3; 3]> = mubs.into_iter().flatten().collect();
    let stab_tables: Vec<[[Q; 3]; 3]> = stabilizers.iter().map(compute_wigner_table_z3).collect();

    let mut stab_nonneg_norm_ok = true;
    let mut stab_affine_line_ok = true;
    let mut stab_zero_neg_ok = true;
    for tbl in &stab_tables {
        let (nn_ok, aff_ok, zn_ok) = check_single_stabilizer_table(tbl);
        stab_nonneg_norm_ok &= nn_ok;
        stab_affine_line_ok &= aff_ok;
        stab_zero_neg_ok &= zn_ok;
    }

    let mut wigner_born_all_pairs_ok = true;
    for i in 0..stabilizers.len() {
        for j in 0..stabilizers.len() {
            wigner_born_all_pairs_ok &= check_wigner_born_pair(
                &stabilizers[i],
                &stabilizers[j],
                &stab_tables[i],
                &stab_tables[j],
            );
        }
    }

    let clifford_cov_ok = check_clifford_fourier_covariance();
    let (magic_norm_pure_ok, magic_w00, magic_min, magic_negativity, magic_born_ok) =
        evaluate_magic_state_witness(&stabilizers, &stab_tables);

    FiniteQmExpressibilityAndMeasurementReport {
        class_i_exact_finite_identity_count: class_i_count,
        class_ii_rational_interval_enclosure_count: class_ii_count,
        class_iii_strict_finite_nogo_count: class_iii_count,
        weyl_heisenberg_commutator_trace_zero_all_dims: wh_krav.wh_trace_zero_all,
        identity_trace_nonzero_all_dims: wh_krav.id_trace_nonzero_all,
        kravchuk_interior_commutator_is_one_all_dims: wh_krav.kravchuk_interior_ok,
        kravchuk_top_boundary_defect_d3: wh_krav.defect_d3,
        kravchuk_top_boundary_defect_d4: wh_krav.defect_d4,
        kravchuk_commutator_trace_zero_all_dims: wh_krav.kravchuk_trace_zero_all,
        lorentz_boost_is_minkowski_isometry_all_betas: lorentz_clock.boost_minkowski_ok,
        lorentz_boost_euclidean_gram_not_identity_all_betas: lorentz_clock.boost_gram_not_id,
        lorentz_boost_gram_trace_excess_matches_formula: lorentz_clock.boost_excess_formula_ok,
        lorentz_boost_2x2_gram_trace_at_half: lorentz_clock.gram_2x2_half,
        lorentz_boost_4x4_gram_trace_at_half: lorentz_clock.gram_4x4_half,
        lorentz_boost_generator_killing_trace_positive: lorentz_clock.killing_sign_ok,
        closed_clock_survival_probabilities: lorentz_clock.surv_probs,
        closed_clock_unitary_power_n_is_identity: lorentz_clock.closed_unitary_id_at_n,
        closed_clock_exact_poincare_recurrence_at_n: lorentz_clock.closed_recurrence_ok,
        premeasurement_cnot_is_unitary: kraus.cnot_unitary_ok,
        joint_post_measurement_state_is_pure: kraus.joint_pure_ok,
        joint_unitary_reversal_restores_initial_state: kraus.joint_reversal_ok,
        partial_trace_equals_kraus_channel: kraus.partial_eq_kraus,
        kraus_completeness_holds: kraus.kraus_complete_ok,
        reduced_state_off_diagonal_zero: kraus.off_diag_zero,
        initial_system_purity: kraus.init_purity,
        reduced_system_purity: kraus.red_purity,
        subsystem_purity_loss: kraus.purity_loss,
        friends_internal_records_perfectly_correlated: wf.friends_corr_ok,
        wigners_friend_observables_involutory_and_commuting: wf.wf_inv_comm_ok,
        wigners_friend_local_settings_anticommute: wf.wf_anticomm_ok,
        wf_correlators: wf.wf_correlators,
        wf_chsh_value: wf.s_wf,
        wf_chsh_squared: wf.s_wf_sq,
        wf_violates_classical_joint_table_bound: wf.wf_violates_classical,
        wf_respects_tsirelson_quantum_bound: wf.wf_respects_tsirelson,
        wf_no_observer_independent_joint_distribution: wf.wf_violates_classical,
        qutrit_stabilizer_state_count: stabilizers.len(),
        qutrit_four_mubs_intrabasis_orthogonal: intra_ortho_ok,
        qutrit_four_mubs_interbasis_overlap_exact_one_third: inter_mub_ok,
        all_12_stabilizers_wigner_nonnegative_and_normalized: stab_nonneg_norm_ok,
        all_12_stabilizers_supported_on_affine_lines: stab_affine_line_ok,
        all_12_stabilizers_zero_negativity: stab_zero_neg_ok,
        wigner_inner_product_matches_born_rule_all_pairs: wigner_born_all_pairs_ok,
        clifford_fourier_symplectic_covariance_exact: clifford_cov_ok,
        magic_state_wigner_normalized_and_pure: magic_norm_pure_ok,
        magic_state_wigner_00: magic_w00,
        magic_state_min_wigner_entry: magic_min,
        magic_state_wigner_negativity: magic_negativity,
        magic_state_born_overlaps_match_wigner_pairing: magic_born_ok,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/finite_qm_expressibility_and_measurement.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-qm-expressibility-and-measurement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5db621e5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5db621e5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5db621e5 {
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
impl BoundaryError5db621e5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5db621e5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5db621e5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5db621e5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5db621e5> {
        if capacity_bound == 0 {
            return Err(BoundaryError5db621e5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5db621e5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5db621e5::ExceedsCapacity {
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
    fn test_finite_qm_expressibility_and_measurement_control() {
        let r = evaluate_finite_qm_expressibility_and_measurement_control();
        assert_eq!(r.class_i_exact_finite_identity_count, 11);
        assert_eq!(r.class_ii_rational_interval_enclosure_count, 4);
        assert_eq!(r.class_iii_strict_finite_nogo_count, 3);
        assert!(r.weyl_heisenberg_commutator_trace_zero_all_dims);
        assert!(r.identity_trace_nonzero_all_dims);
        assert!(r.kravchuk_interior_commutator_is_one_all_dims);
        assert_eq!(r.kravchuk_top_boundary_defect_d3, q(-2, 1));
        assert_eq!(r.kravchuk_top_boundary_defect_d4, q(-3, 1));
        assert!(r.kravchuk_commutator_trace_zero_all_dims);
        assert!(r.lorentz_boost_is_minkowski_isometry_all_betas);
        assert!(r.lorentz_boost_euclidean_gram_not_identity_all_betas);
        assert!(r.lorentz_boost_gram_trace_excess_matches_formula);
        assert_eq!(r.lorentz_boost_2x2_gram_trace_at_half, q(82, 9));
        assert_eq!(r.lorentz_boost_4x4_gram_trace_at_half, q(100, 9));
        assert!(r.lorentz_boost_generator_killing_trace_positive);
        assert_eq!(
            r.closed_clock_survival_probabilities,
            vec![q(1, 1), q(0, 1), q(0, 1), q(0, 1), q(1, 1)]
        );
        assert!(r.closed_clock_unitary_power_n_is_identity);
        assert!(r.closed_clock_exact_poincare_recurrence_at_n);

        assert!(r.premeasurement_cnot_is_unitary);
        assert!(r.joint_post_measurement_state_is_pure);
        assert!(r.joint_unitary_reversal_restores_initial_state);
        assert!(r.partial_trace_equals_kraus_channel);
        assert!(r.kraus_completeness_holds);
        assert!(r.reduced_state_off_diagonal_zero);
        assert_eq!(r.initial_system_purity, q(1, 1));
        assert_eq!(r.reduced_system_purity, q(337, 625));
        assert_eq!(r.subsystem_purity_loss, q(288, 625));

        assert!(r.friends_internal_records_perfectly_correlated);
        assert!(r.wigners_friend_observables_involutory_and_commuting);
        assert!(r.wigners_friend_local_settings_anticommute);
        assert_eq!(r.wf_correlators, [q(3, 5), q(4, 5), q(4, 5), q(-3, 5)]);
        assert_eq!(r.wf_chsh_value, q(14, 5));
        assert_eq!(r.wf_chsh_squared, q(196, 25));
        assert!(r.wf_violates_classical_joint_table_bound);
        assert!(r.wf_respects_tsirelson_quantum_bound);
        assert!(r.wf_no_observer_independent_joint_distribution);

        assert_eq!(r.qutrit_stabilizer_state_count, 12);
        assert!(r.qutrit_four_mubs_intrabasis_orthogonal);
        assert!(r.qutrit_four_mubs_interbasis_overlap_exact_one_third);
        assert!(r.all_12_stabilizers_wigner_nonnegative_and_normalized);
        assert!(r.all_12_stabilizers_supported_on_affine_lines);
        assert!(r.all_12_stabilizers_zero_negativity);
        assert!(r.wigner_inner_product_matches_born_rule_all_pairs);
        assert!(r.clifford_fourier_symplectic_covariance_exact);
        assert!(r.magic_state_wigner_normalized_and_pure);
        assert_eq!(r.magic_state_wigner_00, q(-1, 9));
        assert_eq!(r.magic_state_min_wigner_entry, q(-1, 9));
        assert_eq!(r.magic_state_wigner_negativity, q(4, 9));
        assert!(r.magic_state_born_overlaps_match_wigner_pairing);
    }
}

#[cfg(test)]
mod l4_boundary_tests_5db621e5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5db621e5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5db621e5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5db621e5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5db621e5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5db621e5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError5db621e5::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError5db621e5::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
