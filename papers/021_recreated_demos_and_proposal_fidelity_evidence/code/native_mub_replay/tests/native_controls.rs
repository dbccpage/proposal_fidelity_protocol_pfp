//! Source-bound discriminating controls for the exact native mathematical owner.
//! Inputs follow mub6_matolcsi_weiner_conj2.rs tests at source head 526ffd17.
use omega_mub::omega_native::mub6_matolcsi_weiner_conj2::{
    gamma1_permutations, gamma2_permutations, verify_gamma1,
};
use omega_number_theory::cyclotomic::Cyc24;

#[test]
fn declared_sign_pattern_counts() {
    assert_eq!(gamma1_permutations().len(), 20);
    assert_eq!(gamma2_permutations().len(), 20);
}

#[test]
fn fourier_positive_and_tao_negative_are_distinguished() {
    let fourier = std::array::from_fn(|row| {
        std::array::from_fn(|col| Cyc24::zeta24(4 * (row * col) as i32))
    });
    assert_eq!(verify_gamma1(&fourier), 0);
    // Exact Tao S6 exponents from the original retained native unit test.
    let exponents = [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 2, 2],
        [0, 1, 0, 2, 2, 1],
        [0, 1, 2, 0, 1, 2],
        [0, 2, 2, 1, 0, 1],
        [0, 2, 1, 2, 1, 0],
    ];
    let tao = std::array::from_fn(|row| {
        std::array::from_fn(|col| Cyc24::zeta24(8 * exponents[row][col]))
    });
    assert_eq!(verify_gamma1(&tao), 20);
}
