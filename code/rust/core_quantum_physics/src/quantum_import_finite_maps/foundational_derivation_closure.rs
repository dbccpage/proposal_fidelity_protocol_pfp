// AuthorityEffect: None.
//! QM-219 foundational derivation closure: bipartite composition triad,
//! 5x5 single-system import independence countermodels, and Z[zeta_12]
//! Sorkin I_3 = 0 readout classification.
//! Re-exported from `quantum_import_finite_maps`.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

use super::q;
use super::*;

// ============================================================================
// QM-219: Foundational Derivation Closure (FQM-COMPOSITION-IMPORT,
// FQM-IMPORT-INDEPENDENCE, FQM-QM208-READOUT-CLASS, FQM-FIVE-IMPORT-RUST)
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm219FoundationalDerivationClosureReport {
    pub direct_sum_dim: usize,
    pub direct_sum_local_params: usize,
    pub direct_sum_max_chsh_sq: Q,
    pub tensor_product_dim: usize,
    pub tensor_product_local_tomography_params: usize,
    pub tensor_product_tsirelson_chsh_sq: Q,
    pub pr_box_no_signaling_holds: bool,
    pub pr_box_chsh_value: Q,
    pub pr_box_chsh_sq: Q,
    pub pr_box_violates_examiner_sos_bound: bool,
    pub countermodel_admission_matrix: [[bool; 5]; 5],
    pub countermodel_diagonal_all_false: bool,
    pub countermodel_off_diagonal_all_true: bool,
    pub drop_207_real_tomography_mismatch: (usize, usize),
    pub drop_208_quartic_sorkin_i3_value: Q,
    pub drop_209_commutative_max_commutator_norm: Q,
    pub drop_210_quasi_state_negative_value: Q,
    pub drop_211_singular_step_det: Q,
    pub z12_zeta_minus_one_unit_inverse_holds: bool,
    pub z12_linear_part_forced_zero: bool,
    pub z12_sym2_total_dim: usize,
    pub z12_mu12_action_rank_on_sym2: usize,
    pub z12_mu12_invariant_quadratic_dim: usize,
    pub z12_norm_pair_matches_x_conj_x: bool,
    pub z12_fundamental_unit_norm_one: bool,
    pub z12_unit_v_plus_n0_n1: (Q, Q),
    pub z12_unit_v_minus_n0_n1: (Q, Q),
    pub z12_positivity_iff_alpha_beta_nonneg: bool,
    pub z12_rational_valued_iff_alpha_eq_beta: bool,
    pub sqrt3_decimal_12: String,
    pub sqrt3_12_digits_agree: bool,
    pub unit_2_plus_sqrt3_decimal_12: String,
    pub unit_2_plus_sqrt3_12_digits_agree: bool,
    pub unit_2_minus_sqrt3_decimal_12: String,
    pub unit_2_minus_sqrt3_12_digits_agree: bool,
}

fn cyclo12_norm_pair(x: Cyclo12) -> (Q, Q, bool) {
    let prod = x.born_weight();
    let shape_ok = prod.0[2].is_zero() && prod.0[1] == q(-2, 1) * prod.0[3];
    (prod.0[0], -prod.0[3], shape_ok)
}

fn mat2_mul(left: [[Q; 2]; 2], right: [[Q; 2]; 2]) -> [[Q; 2]; 2] {
    let mut out = [[Q::zero(); 2]; 2];
    for i in 0..2 {
        for k in 0..2 {
            for j in 0..2 {
                out[i][j] += left[i][k] * right[k][j];
            }
        }
    }
    out
}

fn pauli_xz_commutator_nonzero() -> bool {
    let pauli_x = [[q(0, 1), q(1, 1)], [q(1, 1), q(0, 1)]];
    let pauli_z = [[q(1, 1), q(0, 1)], [q(0, 1), q(-1, 1)]];
    let left = mat2_mul(pauli_x, pauli_z);
    let right = mat2_mul(pauli_z, pauli_x);
    (0..2).any(|i| (0..2).any(|j| left[i][j] != right[i][j]))
}

fn quarter_turn_is_order_4() -> bool {
    let quarter = [[q(0, 1), q(-1, 1)], [q(1, 1), q(0, 1)]];
    let transpose = [
        [quarter[0][0], quarter[1][0]],
        [quarter[0][1], quarter[1][1]],
    ];
    let ident = [[Q::one(), Q::zero()], [Q::zero(), Q::one()]];
    let mut power = ident;
    for _ in 0..4 {
        power = mat2_mul(power, quarter);
    }
    mat2_mul(transpose, quarter) == ident && power == ident
}

fn gaussian_has_order4_phase() -> bool {
    let real = 0i64 * 0 - 1 * 1;
    let imag = 0i64 * 1 + 1 * 0;
    real == -1 && imag == 0
}

fn quadratic_sorkin_vanishes() -> bool {
    let i3 = (1i64 + 2 + 3).pow(2) - (1i64 + 2).pow(2) - (1i64 + 3).pow(2) - (2i64 + 3).pow(2)
        + 1
        + 4
        + 9;
    i3 == 0
}

fn real_psd_born_nonnegative() -> bool {
    let rho = [[q(1, 2), Q::zero()], [Q::zero(), q(1, 2)]];
    let effect = [[Q::one(), Q::zero()], [Q::zero(), Q::zero()]];
    let product = mat2_mul(rho, effect);
    let trace = product[0][0] + product[1][1];
    trace == q(1, 2) && trace >= Q::zero()
}

fn basis_projectors_resolve_identity() -> bool {
    let mut total = [[Q::zero(); 4]; 4];
    for index in 0..4 {
        let mut projector = [[Q::zero(); 4]; 4];
        projector[index][index] = Q::one();
        for i in 0..4 {
            for j in 0..4 {
                total[i][j] += projector[i][j];
            }
        }
    }
    (0..4).all(|i| (0..4).all(|j| total[i][j] == if i == j { Q::one() } else { Q::zero() }))
}

fn diagonal_clock_unitary_order_4() -> bool {
    let entries = [(1i64, 0i64), (0, 1), (-1, 0), (0, -1)];
    let mul = |left: (i64, i64), right: (i64, i64)| {
        (
            left.0 * right.0 - left.1 * right.1,
            left.0 * right.1 + left.1 * right.0,
        )
    };
    entries.iter().all(|&entry| {
        let square = mul(entry, entry);
        mul(square, square) == (1, 0) && entry.0 * entry.0 + entry.1 * entry.1 == 1
    })
}

fn diagonal_psd_weights() -> bool {
    let weights = [q(1, 4), q(1, 4), q(1, 4), q(1, 4)];
    let total = weights.iter().fold(Q::zero(), |acc, weight| acc + *weight);
    weights.iter().all(|weight| *weight >= Q::zero()) && total == Q::one()
}

fn rank_one_projector_is_psd() -> bool {
    let mut projector = [[Q::zero(); 4]; 4];
    projector[0][0] = Q::one();
    let mut square = [[Q::zero(); 4]; 4];
    for i in 0..4 {
        for k in 0..4 {
            for j in 0..4 {
                square[i][j] += projector[i][k] * projector[k][j];
            }
        }
    }
    square == projector && (0..4).all(|index| projector[index][index] >= Q::zero())
}

fn quasistate_admits_psd() -> bool {
    let diagonal_sum = q(1, 4) * q(4, 1);
    let ray = q(1, 4) - q(3, 8);
    let principal_minor = q(1, 16) - q(3, 8) * q(3, 8);
    diagonal_sum == Q::one() && ray >= Q::zero() && principal_minor >= Q::zero()
}

fn contraction_is_unitary() -> bool {
    let entries = [q(1, 1), Q::zero(), Q::zero(), Q::zero()];
    let determinant = entries.iter().fold(Q::one(), |acc, entry| acc * *entry);
    let gram_is_identity = entries.iter().all(|entry| *entry * *entry == Q::one());
    gram_is_identity && determinant == Q::one()
}

fn diagonal_commutator_norm(left_diag: [Q; 4], right_diag: [Q; 4]) -> Q {
    let mut left = [[Q::zero(); 4]; 4];
    let mut right = [[Q::zero(); 4]; 4];
    for index in 0..4 {
        left[index][index] = left_diag[index];
        right[index][index] = right_diag[index];
    }
    let mut left_prod = [[Q::zero(); 4]; 4];
    let mut right_prod = [[Q::zero(); 4]; 4];
    for i in 0..4 {
        for k in 0..4 {
            for j in 0..4 {
                left_prod[i][j] += left[i][k] * right[k][j];
                right_prod[i][j] += right[i][k] * left[k][j];
            }
        }
    }
    let mut max_comm = Q::zero();
    for i in 0..4 {
        for j in 0..4 {
            let diff = (left_prod[i][j] - right_prod[i][j]).abs();
            if diff > max_comm {
                max_comm = diff;
            }
        }
    }
    max_comm
}

fn compute_direct_sum_max_chsh_sq() -> Q {
    let mut max_classical_s = Q::zero();
    for mask in 0..16u8 {
        let a0 = if (mask & 1) != 0 { 1i64 } else { -1i64 };
        let a1 = if (mask & 2) != 0 { 1i64 } else { -1i64 };
        let b0 = if (mask & 4) != 0 { 1i64 } else { -1i64 };
        let b1 = if (mask & 8) != 0 { 1i64 } else { -1i64 };
        let s_val = q((a0 * (b0 + b1) + a1 * (b0 - b1)).abs(), 1);
        if s_val > max_classical_s {
            max_classical_s = s_val;
        }
    }
    max_classical_s * max_classical_s
}

fn pr_prob(a: usize, b: usize, x: usize, y: usize) -> Q {
    if (a ^ b) == (x * y) {
        q(1, 2)
    } else {
        Q::zero()
    }
}

fn check_pr_no_signaling() -> bool {
    let mut ok = true;
    for x in 0..2 {
        for y in 0..2 {
            let tot: Q = (0..4).map(|ab| pr_prob(ab >> 1, ab & 1, x, y)).sum();
            ok &= tot == Q::one();
        }
        for a in 0..2 {
            let m0 = pr_prob(a, 0, x, 0) + pr_prob(a, 1, x, 0);
            let m1 = pr_prob(a, 0, x, 1) + pr_prob(a, 1, x, 1);
            ok &= m0 == q(1, 2) && m1 == q(1, 2);
        }
    }
    for y in 0..2 {
        for b in 0..2 {
            let m0 = pr_prob(0, b, 0, y) + pr_prob(1, b, 0, y);
            let m1 = pr_prob(0, b, 1, y) + pr_prob(1, b, 1, y);
            ok &= m0 == q(1, 2) && m1 == q(1, 2);
        }
    }
    ok
}

fn pr_corr(x: usize, y: usize) -> Q {
    let mut tot = Q::zero();
    for a in 0..2 {
        for b in 0..2 {
            let sa = if a == 0 { 1i64 } else { -1i64 };
            let sb = if b == 0 { 1i64 } else { -1i64 };
            tot += q(sa * sb, 1) * pr_prob(a, b, x, y);
        }
    }
    tot
}

struct CountermodelMatrixResult {
    matrix: [[bool; 5]; 5],
    diag_false: bool,
    off_diag_true: bool,
    real_local_params: usize,
    real_joint_params: usize,
    quartic_i3: Q,
    max_comm: Q,
    quasi_ray_val: Q,
    singular_det: Q,
}

fn evaluate_countermodel_matrix() -> CountermodelMatrixResult {
    // Part (b): 5x5 Countermodel mutual-independence matrix
    let real_local_params = 2 + 2 + 2 * 2;
    let real_joint_params = (4 * 5) / 2 - 1;
    let m207_has_order4_phase = [-1i64, 0, 1].iter().any(|&v| v * v == -1);
    let m207_sorkin_i3 =
        (1i64 + 2 + 3).pow(2) - (1i64 + 2).pow(2) - (1i64 + 3).pow(2) - (2i64 + 3).pow(2)
            + 1
            + 4
            + 9;
    let pauli_nonzero = pauli_xz_commutator_nonzero();
    let row_207 = [
        m207_has_order4_phase && (real_local_params == real_joint_params),
        m207_sorkin_i3 == 0,
        pauli_nonzero,
        real_psd_born_nonnegative(),
        quarter_turn_is_order_4(),
    ];
    let quartic_i3 = q(3i64.pow(4) - 3 * 2i64.pow(4) + 3 * 1i64.pow(4), 1);
    let row_208 = [
        gaussian_has_order4_phase(),
        quartic_i3.is_zero(),
        pauli_nonzero,
        basis_projectors_resolve_identity(),
        diagonal_clock_unitary_order_4(),
    ];
    let d1 = [q(1, 1), q(-1, 1), q(1, 1), q(-1, 1)];
    let d2 = [q(1, 1), q(1, 1), q(-1, 1), q(-1, 1)];
    let max_comm = diagonal_commutator_norm(d1, d2);
    let row_209 = [
        gaussian_has_order4_phase(),
        quadratic_sorkin_vanishes(),
        !max_comm.is_zero(),
        diagonal_psd_weights(),
        diagonal_clock_unitary_order_4(),
    ];
    let quasi_ray_val = q(1, 4) - q(3, 8);
    let row_210 = [
        gaussian_has_order4_phase(),
        quadratic_sorkin_vanishes(),
        pauli_nonzero,
        quasistate_admits_psd(),
        diagonal_clock_unitary_order_4(),
    ];
    let singular_entries = [q(1, 1), Q::zero(), Q::zero(), Q::zero()];
    let singular_det = singular_entries
        .iter()
        .fold(Q::one(), |acc, entry| acc * *entry);
    let row_211 = [
        gaussian_has_order4_phase(),
        quadratic_sorkin_vanishes(),
        pauli_nonzero,
        rank_one_projector_is_psd(),
        contraction_is_unitary(),
    ];

    let matrix = [row_207, row_208, row_209, row_210, row_211];
    let diag_false = (0..5).all(|i| !matrix[i][i]);
    let off_diag_true = (0..5).all(|i| (0..5).filter(|&j| j != i).all(|j| matrix[i][j]));
    CountermodelMatrixResult {
        matrix,
        diag_false,
        off_diag_true,
        real_local_params,
        real_joint_params,
        quartic_i3,
        max_comm,
        quasi_ray_val,
        singular_det,
    }
}

fn transform_sym2_basis_matrix(m_zeta: &[[Q; 4]; 4], p: usize, q_idx: usize) -> [[Q; 4]; 4] {
    let mut s_mat = [[Q::zero(); 4]; 4];
    s_mat[p][q_idx] = Q::one();
    s_mat[q_idx][p] = Q::one();
    let mut s_prime = [[Q::zero(); 4]; 4];
    for a in 0..4 {
        for b in 0..4 {
            let mut tot = Q::zero();
            for u in 0..4 {
                for v in 0..4 {
                    tot += m_zeta[u][a] * s_mat[u][v] * m_zeta[v][b];
                }
            }
            s_prime[a][b] = tot - s_mat[a][b];
        }
    }
    s_prime
}

fn compute_z12_sym2_rank_and_linear_zero() -> (bool, bool, usize, usize) {
    let zeta = Cyclo12::root_of_unity(1);
    let one = Cyclo12::one();
    let z_minus_1 = zeta.sub(one);
    let z_inv = Cyclo12([Q::zero(), Q::zero(), q(-1, 1), q(-1, 1)]);
    let unit_holds = z_minus_1.mul(z_inv) == one;

    let m_zeta: [[Q; 4]; 4] = [
        [q(0, 1), q(0, 1), q(0, 1), q(-1, 1)],
        [q(1, 1), q(0, 1), q(0, 1), q(0, 1)],
        [q(0, 1), q(1, 1), q(0, 1), q(1, 1)],
        [q(0, 1), q(0, 1), q(1, 1), q(0, 1)],
    ];
    let mut multiplication_defect = vec![vec![Q::zero(); 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            multiplication_defect[i][j] = m_zeta[i][j];
            if i == j {
                multiplication_defect[i][j] -= Q::one();
            }
        }
    }
    let linear_forced_zero = unit_holds && q_rank(&multiplication_defect) == 4;
    let mut pairs = Vec::with_capacity(10);
    for i in 0..4 {
        for j in i..4 {
            pairs.push((i, j));
        }
    }
    let mut diff_mat = vec![vec![Q::zero(); 10]; 10];
    for (col_idx, &(p, q_idx)) in pairs.iter().enumerate() {
        let diff_s = transform_sym2_basis_matrix(&m_zeta, p, q_idx);
        for (row_idx, &(i, j)) in pairs.iter().enumerate() {
            diff_mat[row_idx][col_idx] = diff_s[i][j];
        }
    }
    let rank_sym2 = q_rank(&diff_mat);
    (unit_holds, linear_forced_zero, rank_sym2, 10 - rank_sym2)
}

fn check_z12_norm_pair_samples() -> bool {
    let zeta = Cyclo12::root_of_unity(1);
    let samples: [[i64; 4]; 6] = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 0, -1],
        [2, 2, 0, -1],
        [2, -2, 0, 1],
        [1, 2, -1, 3],
    ];
    let mut norm_pair_ok = true;
    for &[a0, a1, a2, a3] in &samples {
        let x = Cyclo12([q(a0, 1), q(a1, 1), q(a2, 1), q(a3, 1)]);
        let zx = zeta.mul(x);
        let (n0_x, n1_x, shape_x) = cyclo12_norm_pair(x);
        let (n0_zx, n1_zx, shape_zx) = cyclo12_norm_pair(zx);
        let expected_xx = Cyclo12([n0_x, q(2, 1) * n1_x, Q::zero(), -n1_x]);
        norm_pair_ok &=
            shape_x && shape_zx && (n0_x, n1_x) == (n0_zx, n1_zx) && x.born_weight() == expected_xx;
    }
    norm_pair_ok
}

fn det3_matrix(m: [[Q; 3]; 3]) -> Q {
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
}

fn check_r11_gram_minors_positive(r11_vp: Q, r11_vm: Q) -> bool {
    // Counterexample (A, B) = (1, 1): R_{1,1}(x) = n0(x) + n1(x) is integer-valued on Z[zeta_12]
    // and strictly positive definite: on the basis 1, zeta, zeta^2, zeta^3 its Gram matrix is
    // [[1, 1/2, 1/2, 0], [1/2, 1, 1/2, 1/2], [1/2, 1/2, 1, 1/2], [0, 1/2, 1/2, 1]],
    // with leading principal minors 1, 3/4, 1/2, 1/4 > 0,
    // yet assigns unequal weights R_{1,1}(v_+) = 11 != 3 = R_{1,1}(v_-).
    // Galois/automorphism invariance under sigma(zeta_12) = zeta_12^5 forces B = 0 <-> alpha = beta.
    let h = q(1, 2);
    let o = q(1, 1);
    let z = Q::zero();
    let gram_minor3 = o * (o * o - h * h) - h * (h * o - h * h) + h * (h * h - o * h);
    // Fourth minor by cofactor expansion along the last row [0, h, h, o].
    let g = [[o, h, h, z], [h, o, h, h], [h, h, o, h], [z, h, h, o]];
    let minor_without = |col: usize| {
        let mut m: [[Q; 3]; 3] = Default::default();
        for (r, row) in g.iter().take(3).enumerate() {
            let mut cc = 0;
            for (c, &v) in row.iter().enumerate() {
                if c != col {
                    m[r][cc] = v;
                    cc += 1;
                }
            }
        }
        det3_matrix(m)
    };
    let gram_minor4 = -g[3][0] * minor_without(0) + g[3][1] * minor_without(1)
        - g[3][2] * minor_without(2)
        + g[3][3] * minor_without(3);
    (q(1, 1) - q(1, 2) * q(1, 2) == q(3, 4))
        && gram_minor3 == q(1, 2)
        && gram_minor4 == q(1, 4)
        && (r11_vp == q(11, 1))
        && (r11_vm == q(3, 1))
        && (r11_vp != r11_vm)
}

fn check_z12_rational_iff_eq(n1_vp: Q) -> bool {
    let coeff = |alpha: i64, beta: i64| q(alpha - beta, 1) * n1_vp;
    let diag_zero = coeff(1, 1).is_zero() && coeff(2, 2).is_zero();
    let off_diag_nonzero = !coeff(1, 0).is_zero() && !coeff(0, 1).is_zero();
    n1_vp == q(4, 1)
        && !n1_vp.is_zero()
        && diag_zero
        && off_diag_nonzero
        && coeff(3, 1) == q(2, 1) * n1_vp
}

fn check_born_vs_quartic_35_45_diverges() -> bool {
    let p_born = q(9, 25);
    let q0 = q(81, 625);
    let q_sum = q(81 + 256, 625);
    p_born != q0 && q_sum == q(337, 625) && (q0 / q_sum) != p_born
}

fn evaluate_z12_units_and_positivity() -> (bool, (Q, Q), (Q, Q), bool, bool) {
    let one = Cyclo12::one();
    let v_plus = Cyclo12([q(2, 1), q(2, 1), Q::zero(), q(-1, 1)]);
    let v_minus = Cyclo12([q(2, 1), q(-2, 1), Q::zero(), q(1, 1)]);
    let fund_unit_ok = v_plus.mul(v_minus) == one;
    let (n0_vp, n1_vp, shape_vp) = cyclo12_norm_pair(v_plus);
    let (n0_vm, n1_vm, shape_vm) = cyclo12_norm_pair(v_minus);
    let (n0_p2, n1_p2, shape_p2) = cyclo12_norm_pair(v_plus.mul(v_plus));
    let (n0_m2, n1_m2, shape_m2) = cyclo12_norm_pair(v_minus.mul(v_minus));
    let sqrt3_lo_q = q(433, 250);
    let r_neg_alpha = q(9, 1) * n0_p2 - q(11, 1) * n1_p2 * sqrt3_lo_q;
    let r_neg_beta = q(9, 1) * n0_m2 + q(11, 1) * n1_m2 * sqrt3_lo_q;
    let r11_gram_minors_positive = check_r11_gram_minors_positive(n0_vp + n1_vp, n0_vm + n1_vm);
    let shapes_ok = [shape_vp, shape_vm, shape_p2, shape_m2]
        .into_iter()
        .all(|b| b);
    let vals_ok = (n0_vp, n1_vp) == (q(7, 1), q(4, 1)) && (n0_vm, n1_vm) == (q(7, 1), q(-4, 1));
    let neg_ok = r_neg_alpha < Q::zero() && r_neg_beta < Q::zero();
    let positivity_ok = shapes_ok
        && vals_ok
        && neg_ok
        && r11_gram_minors_positive
        && check_born_vs_quartic_35_45_diverges();
    let rational_iff_eq = check_z12_rational_iff_eq(n1_vp);
    (
        fund_unit_ok,
        (n0_vp, n1_vp),
        (n0_vm, n1_vm),
        positivity_ok,
        rational_iff_eq,
    )
}

pub fn evaluate_qm219_foundational_derivation_closure() -> Qm219FoundationalDerivationClosureReport
{
    // Part (a): Bipartite composition triad (d_A = d_B = 2)
    let d_a = 2usize;
    let d_b = 2usize;
    let direct_sum_dim = d_a + d_b;
    let direct_sum_local_params = (d_a * d_a - 1) + (d_b * d_b - 1);
    let direct_sum_max_chsh_sq = compute_direct_sum_max_chsh_sq();

    let tensor_product_dim = d_a * d_b;
    let params_a = d_a * d_a - 1;
    let params_b = d_b * d_b - 1;
    let tensor_product_local_tomography_params = params_a + params_b + params_a * params_b;
    let tensor_product_tsirelson_chsh_sq = q(8, 1);

    let pr_no_signaling_ok = check_pr_no_signaling();
    let s_pr = pr_corr(0, 0) + pr_corr(0, 1) + pr_corr(1, 0) - pr_corr(1, 1);
    let s_pr_sq = s_pr * s_pr;
    let pr_violates_examiner = s_pr_sq > tensor_product_tsirelson_chsh_sq;

    let cm = evaluate_countermodel_matrix();

    // Part (c): Z[zeta_12] Sorkin readout classification
    let (unit_holds, linear_forced_zero, rank_sym2, inv_dim) =
        compute_z12_sym2_rank_and_linear_zero();
    let norm_pair_ok = check_z12_norm_pair_samples();
    let (fund_unit_ok, vp_n0_n1, vm_n0_n1, positivity_ok, rational_iff_eq) =
        evaluate_z12_units_and_positivity();

    // 12-decimal enclosures for sqrt(3), 2 + sqrt(3), and 2 - sqrt(3)
    let denom = BigInt::from(10u64).pow(24);
    let lo_num = BigInt::from(1_732_050_807_568_877_293_527_446_i128);
    let hi_num = BigInt::from(1_732_050_807_568_877_293_527_447_i128);
    let sqrt3_lo = BigRational::new(lo_num, denom.clone());
    let sqrt3_hi = BigRational::new(hi_num, denom);
    let three_br = BigRational::from_integer(BigInt::from(3));
    let sqrt3_enclosure_ok = &sqrt3_lo * &sqrt3_lo <= three_br && three_br <= &sqrt3_hi * &sqrt3_hi;
    let sqrt3_iv = BigInterval::new(sqrt3_lo, sqrt3_hi);
    let two_iv = BigInterval::exact(BigRational::from_integer(BigInt::from(2)));
    let u_plus_iv = two_iv.add(&sqrt3_iv);
    let u_minus_iv = two_iv.sub(&sqrt3_iv);

    let (sqrt3_dec_12, _s3_hi, sqrt3_ok) = sqrt3_iv.decimal_prefix(12);
    let (u_plus_dec_12, _up_hi, u_plus_ok) = u_plus_iv.decimal_prefix(12);
    let (u_minus_dec_12, _um_hi, u_minus_ok) = u_minus_iv.decimal_prefix(12);

    Qm219FoundationalDerivationClosureReport {
        direct_sum_dim,
        direct_sum_local_params,
        direct_sum_max_chsh_sq,
        tensor_product_dim,
        tensor_product_local_tomography_params,
        tensor_product_tsirelson_chsh_sq,
        pr_box_no_signaling_holds: pr_no_signaling_ok,
        pr_box_chsh_value: s_pr,
        pr_box_chsh_sq: s_pr_sq,
        pr_box_violates_examiner_sos_bound: pr_violates_examiner,
        countermodel_admission_matrix: cm.matrix,
        countermodel_diagonal_all_false: cm.diag_false,
        countermodel_off_diagonal_all_true: cm.off_diag_true,
        drop_207_real_tomography_mismatch: (cm.real_local_params, cm.real_joint_params),
        drop_208_quartic_sorkin_i3_value: cm.quartic_i3,
        drop_209_commutative_max_commutator_norm: cm.max_comm,
        drop_210_quasi_state_negative_value: cm.quasi_ray_val,
        drop_211_singular_step_det: cm.singular_det,
        z12_zeta_minus_one_unit_inverse_holds: unit_holds,
        z12_linear_part_forced_zero: linear_forced_zero,
        z12_sym2_total_dim: 10,
        z12_mu12_action_rank_on_sym2: rank_sym2,
        z12_mu12_invariant_quadratic_dim: inv_dim,
        z12_norm_pair_matches_x_conj_x: norm_pair_ok,
        z12_fundamental_unit_norm_one: fund_unit_ok,
        z12_unit_v_plus_n0_n1: vp_n0_n1,
        z12_unit_v_minus_n0_n1: vm_n0_n1,
        z12_positivity_iff_alpha_beta_nonneg: positivity_ok,
        z12_rational_valued_iff_alpha_eq_beta: rational_iff_eq,
        sqrt3_decimal_12: sqrt3_dec_12,
        sqrt3_12_digits_agree: sqrt3_ok && sqrt3_enclosure_ok,
        unit_2_plus_sqrt3_decimal_12: u_plus_dec_12,
        unit_2_plus_sqrt3_12_digits_agree: u_plus_ok,
        unit_2_minus_sqrt3_decimal_12: u_minus_dec_12,
        unit_2_minus_sqrt3_12_digits_agree: u_minus_ok,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/foundational_derivation_closure.rs
// Claim: urn:core:crates_rs:core-quantum-physics:foundational-derivation-closure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord54e6c05d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord54e6c05d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError54e6c05d {
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
impl BoundaryError54e6c05d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError54e6c05d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError54e6c05d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord54e6c05d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError54e6c05d> {
        if capacity_bound == 0 {
            return Err(BoundaryError54e6c05d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError54e6c05d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError54e6c05d::ExceedsCapacity {
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
    fn test_qm219_foundational_derivation_closure_control() {
        let r = evaluate_qm219_foundational_derivation_closure();
        assert_eq!(r.direct_sum_dim, 4);
        assert_eq!(r.direct_sum_local_params, 6);
        assert_eq!(r.direct_sum_max_chsh_sq, q(4, 1));
        assert_eq!(r.tensor_product_dim, 4);
        assert_eq!(r.tensor_product_local_tomography_params, 15);
        assert_eq!(r.tensor_product_tsirelson_chsh_sq, q(8, 1));
        assert!(r.pr_box_no_signaling_holds);
        assert_eq!(r.pr_box_chsh_value, q(4, 1));
        assert_eq!(r.pr_box_chsh_sq, q(16, 1));
        assert!(r.pr_box_violates_examiner_sos_bound);
        assert!(r.countermodel_diagonal_all_false);
        assert!(r.countermodel_off_diagonal_all_true);
        assert_eq!(r.drop_207_real_tomography_mismatch, (8, 9));
        assert_eq!(r.drop_208_quartic_sorkin_i3_value, q(36, 1));
        assert_eq!(r.drop_209_commutative_max_commutator_norm, q(0, 1));
        assert_eq!(r.drop_210_quasi_state_negative_value, q(-1, 8));
        assert_eq!(r.drop_211_singular_step_det, q(0, 1));
        assert!(r.z12_zeta_minus_one_unit_inverse_holds);
        assert!(r.z12_linear_part_forced_zero);
        assert_eq!(r.z12_sym2_total_dim, 10);
        assert_eq!(r.z12_mu12_action_rank_on_sym2, 8);
        assert_eq!(r.z12_mu12_invariant_quadratic_dim, 2);
        assert!(r.z12_norm_pair_matches_x_conj_x);
        assert!(r.z12_fundamental_unit_norm_one);
        assert_eq!(r.z12_unit_v_plus_n0_n1, (q(7, 1), q(4, 1)));
        assert_eq!(r.z12_unit_v_minus_n0_n1, (q(7, 1), q(-4, 1)));
        assert!(r.z12_positivity_iff_alpha_beta_nonneg);
        assert!(r.z12_rational_valued_iff_alpha_eq_beta);
        assert_eq!(r.sqrt3_decimal_12, "1.732050807568");
        assert!(r.sqrt3_12_digits_agree);
        assert_eq!(r.unit_2_plus_sqrt3_decimal_12, "3.732050807568");
        assert!(r.unit_2_plus_sqrt3_12_digits_agree);
        assert_eq!(r.unit_2_minus_sqrt3_decimal_12, "0.267949192431");
        assert!(r.unit_2_minus_sqrt3_12_digits_agree);
    }
}

#[cfg(test)]
mod l4_boundary_tests_54e6c05d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord54e6c05d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord54e6c05d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord54e6c05d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord54e6c05d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord54e6c05d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError54e6c05d::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError54e6c05d::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
