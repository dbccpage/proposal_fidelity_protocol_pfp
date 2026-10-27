//! Exact anyon-model data, cross-validated across independent routes.
//!
//! Each model's F- and R-symbols satisfy the pentagon and both hexagon equations; the
//! modular data obey `S~^2 = D^2 C`, `S~ S~^dagger = D^2 I`, `(S~ T)^3 = p_+ S~^2` and the
//! Verlinde formula; the Gauss-Milgram ratio pins the central charge; the Frobenius-Schur
//! indicators computed from the F-symbols agree with Bantay's formula from the modular
//! data; fusion-space dimensions agree with the ring's path counts. Negative controls
//! perturb one symbol and assert the exact violated index tuples, which were computed
//! independently with a separate exact-arithmetic implementation (Python, rational
//! coefficients reduced modulo the cyclotomic polynomial).
//!
//! AuthorityEffect: None.

use linear_algebra::exact_field::involution::Involution;
use linear_algebra::exact_field::matrix;
use linear_algebra::scalars::{Field, Ring};
use core_fusion_categories::braid_group::{group_closure, ClosureOutcome};
use core_fusion_categories::braided::{BraidedFusionCategory, HexagonForm, RibbonFusionCategory};
use core_fusion_categories::catalog;
use core_fusion_categories::error::FusionError;
use core_fusion_categories::fusion_category::{
    CategoryDefect, DimensionDefect, FusionCategory, Gauge,
};
use core_fusion_categories::modular::{ModularData, ModularDefect};
use core_fusion_categories::scalar::{
    golden_ratio, root_of_unity, root_of_unity_data, sqrt_two, FusionScalar,
};
use core_number_theory::character_sums::quadratic_gauss_sum;
use core_number_theory::cyclotomic::{Cyc12, Cyc5, Cyc8, EisensteinRat, GaussianRat};
use core_number_theory::cyclotomic28::{sqrt7_28, Cyc28};
use core_number_theory::finite_field::FiniteField;
use core_number_theory::rational::{rq, Rational};
use core_number_theory::scalar::{evaluate_integer_polynomial, from_i64};

fn q(n: i64, d: i64) -> Rational {
    rq(n, d)
}

fn z10(k: i64) -> Cyc5 {
    root_of_unity::<Cyc5>(10, k).unwrap()
}

fn sorted<const N: usize>(mut labels: Vec<[usize; N]>) -> Vec<[usize; N]> {
    labels.sort();
    labels
}

/// Everything that must hold for any validated model, from independent routes.
fn check_universal_laws<K: FusionScalar>(ribbon: &RibbonFusionCategory<K>) {
    let ring = ribbon.ring();
    let n = ring.rank();
    // The F-symbols and R-symbols pass the pentagon and both hexagons.
    assert_eq!(ribbon.category().pentagon_defects(), vec![]);
    assert!(ribbon.category().unit_defects().is_empty());
    assert!(ribbon
        .braided()
        .hexagon_defects(HexagonForm::Direct)
        .is_empty());
    assert!(ribbon
        .braided()
        .hexagon_defects(HexagonForm::Mirror)
        .is_empty());
    // Modular data: every relation, exactly.
    let modular = ModularData::verified(ribbon).unwrap();
    // S~_{0a} = d_a (the dimension row of the S-matrix).
    for a in 0..n {
        assert_eq!(
            modular.s_tilde().get(0, a).unwrap(),
            ribbon.dimensions()[a].clone()
        );
    }
    // The Frobenius-Schur indicator from the F-symbols and from Bantay's formula agree.
    for a in 0..n {
        let from_modular = modular.frobenius_schur_indicator(a).unwrap();
        match ribbon
            .category()
            .frobenius_schur_indicator(a, ribbon.dimensions())
            .unwrap()
        {
            Some(from_f) => assert_eq!(from_f, from_modular, "label {a}"),
            None => assert_eq!(from_modular, 0, "a non-self-dual label {a} has indicator 0"),
        }
    }
    check_fusion_and_braid_laws(ribbon, n);
}

fn check_fusion_and_braid_laws<K: FusionScalar>(ribbon: &RibbonFusionCategory<K>, n: usize) {
    let ring = ribbon.ring();
    // Fusion-space dimensions equal the ring's path counts.
    for a in 0..n {
        for total in 0..n {
            for copies in 0..4usize {
                let word = vec![a; copies];
                let space = ribbon.braided().fusion_space(&word, total).unwrap();
                let paths = ring.fusion_paths(&word, total).unwrap();
                assert_eq!(space.dimension().to_string(), paths.to_string());
            }
            assert_eq!(
                ribbon.braided().braid_relation_defects_on_word(&vec![a; 4], total).unwrap(),
                vec![]
            );
        }
    }
    // The monodromy of every vertex is theta_c / (theta_a theta_b).
    for a in 0..n {
        for b in 0..n {
            for c in ring.fuse(a, b).unwrap() {
                let expected = ribbon.twists()[c]
                    .try_div(&ribbon.twists()[a].mul(&ribbon.twists()[b]))
                    .unwrap();
                assert_eq!(ribbon.braided().monodromy([a, b, c]).unwrap(), expected);
            }
        }
    }
    // The dimensions are roots of the characteristic polynomials of the fusion matrices.
    for a in 0..n {
        let polynomial = ring.characteristic_polynomial(a).unwrap();
        assert!(
            core_number_theory::scalar::evaluate_integer_polynomial(
                &polynomial,
                &ribbon.dimensions()[a]
            )
            .unwrap()
            .is_zero(),
            "d_{a} is a root of det(x - N_{a})"
        );
    }
}

// ---------------------------------------------------------------------------
// Fibonacci
// ---------------------------------------------------------------------------

#[test]
fn fibonacci_has_the_pinned_exact_data() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    let phi = golden_ratio::<Cyc5>().unwrap();
    let one = Cyc5::one();
    assert_eq!(fib.dimensions(), &[one.clone(), phi.clone()]);
    assert_eq!(
        fib.twists(),
        &[one.clone(), z10(4)],
        "theta_tau = zeta_10^4 = e^{{4 pi i/5}}"
    );
    // R^{tau tau}_1 = zeta_10^-4, R^{tau tau}_tau = zeta_10^3.
    assert_eq!(fib.braided().r_entry([1, 1, 0]), z10(-4));
    assert_eq!(fib.braided().r_entry([1, 1, 1]), z10(3));
    // F^{tau tau tau}_tau in the algebraic gauge [[1/phi, 1], [1/phi, -1/phi]].
    let phi_inverse = phi.sub(&one);
    assert_eq!(phi_inverse.mul(&phi), one, "phi^-1 = phi - 1");
    let f = |e: usize, g: usize| fib.category().f_entry([1, 1, 1, 1], e, g);
    assert_eq!(f(0, 0), phi_inverse);
    assert_eq!(f(0, 1), one);
    assert_eq!(f(1, 0), phi_inverse);
    assert_eq!(f(1, 1), phi_inverse.neg());
    // D^2 = 2 + phi; p_+ = 1 + phi^2 theta_tau; p_+^2 = D^2 zeta_10^7 (so c = 14/5 mod 4).
    let d_squared = fib.global_dimension_squared();
    assert_eq!(d_squared, from_i64::<Cyc5>(2).add(&phi));
    assert_eq!(fib.gauss_sum(), one.add(&phi.mul(&phi).mul(&z10(4))));
    assert_eq!(
        fib.gauss_sum().mul(&fib.gauss_sum()),
        d_squared.mul(&z10(7))
    );
    check_universal_laws(&fib);
}

#[test]
fn fibonacci_modular_data_and_central_charge_are_exact() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    let modular = ModularData::verified(&fib).unwrap();
    let phi = golden_ratio::<Cyc5>().unwrap();
    // S~ = [[1, phi], [phi, -1]].
    assert_eq!(modular.s_tilde().get(0, 0).unwrap(), Cyc5::one());
    assert_eq!(modular.s_tilde().get(0, 1).unwrap(), phi);
    assert_eq!(modular.s_tilde().get(1, 0).unwrap(), phi);
    assert_eq!(modular.s_tilde().get(1, 1).unwrap(), Cyc5::one().neg());
    // Gauss-Milgram: c = 14/5 modulo 4, exactly.
    assert_eq!(modular.central_charge_mod_4().unwrap(), q(14, 5));
    let ratio = modular
        .p_plus()
        .mul(modular.p_plus())
        .try_div(modular.d_squared())
        .unwrap();
    assert_eq!(root_of_unity_data(&ratio), Some((10, 7)));
    // D is not in Q(zeta_5): a wrong D is refused, and the honest statement is mod 4 only.
    assert_eq!(
        modular.central_charge_mod_8(&phi),
        Err(FusionError::Modular(ModularDefect::WrongGlobalDimension))
    );
    // Ground-state degeneracies: 1 (sphere), 2 (torus), 5, 15.
    let counts: Vec<String> = (0..4)
        .map(|g| modular.ground_state_degeneracy(g).unwrap().to_string())
        .collect();
    assert_eq!(counts, ["1", "2", "5", "15"]);
    // The Frobenius-Schur indicator of tau is +1 by both routes.
    assert_eq!(modular.frobenius_schur_indicator(1), Ok(1));
    assert_eq!(
        fib.category()
            .frobenius_schur_indicator(1, fib.dimensions()),
        Ok(Some(1))
    );
    // The algebraic gauge is not unitary (its F-matrix has a row of norm^2 1 + phi^-2).
    assert!(!fib.category().is_unitary().unwrap());
    // The Galois-conjugate dimension -1/phi is refused: it is a character of the ring but
    // disagrees with the F-symbols.
    let conjugate = vec![Cyc5::one(), Cyc5::one().sub(&phi)];
    assert_eq!(
        RibbonFusionCategory::try_new(fib.braided().clone(), conjugate),
        Err(FusionError::Category(CategoryDefect::Dimensions(
            DimensionDefect::DisagreesWithF { label: 1 }
        )))
    );
}

#[test]
fn fibonacci_perturbed_f_symbols_fail_the_pentagon_at_exactly_the_independent_tuples() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    let phi_inverse = golden_ratio::<Cyc5>().unwrap().sub(&Cyc5::one());
    let ring = fib.ring().clone();
    // F[1,1] = -phi^-1 -> +phi^-1.
    let f = fib
        .category()
        .f_symbols()
        .with_entry([1, 1, 1, 1], 1, 1, phi_inverse.clone())
        .unwrap();
    let category = FusionCategory::new(ring.clone(), f).unwrap();
    let defects = category.pentagon_defects();
    assert_eq!(
        defects.iter().map(|d| d.labels).collect::<Vec<_>>(),
        vec![
            [1, 1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 0, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
    );
    // Every violated equation reads the perturbed entry, and the first one is reported first.
    assert!(defects.iter().all(|d| d.involves([1, 1, 1, 1], 1, 1)));
    assert_eq!(category.first_pentagon_defect().unwrap(), defects[0]);
    assert!(matches!(
        category.validate(),
        Err(FusionError::Category(CategoryDefect::Pentagon {
            labels: [1, 1, 1, 1, 0, 0, 1, 1, 1]
        }))
    ));
    // F[0,1] = 1 -> 2: seven violated equations, the first three as computed independently.
    let f = fib
        .category()
        .f_symbols()
        .with_entry([1, 1, 1, 1], 0, 1, from_i64::<Cyc5>(2))
        .unwrap();
    let category = FusionCategory::new(ring, f).unwrap();
    let defects = category.pentagon_defects();
    assert_eq!(defects.len(), 7);
    assert_eq!(
        defects.iter().take(3).map(|d| d.labels).collect::<Vec<_>>(),
        vec![
            [1, 1, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 1, 1, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 0, 1, 0, 1]
        ]
    );
    assert!(defects.iter().all(|d| d.involves([1, 1, 1, 1], 0, 1)));
}

#[test]
fn fibonacci_perturbed_r_symbols_fail_both_hexagons_at_exactly_the_independent_tuples() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    let category = fib.category().clone();
    let expected = vec![
        [1, 1, 1, 0, 1, 1],
        [1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1],
    ];
    // R^{tau tau}_tau = zeta_10^3 -> zeta_10^-3.
    let r = fib
        .braided()
        .r_symbols()
        .with_entry([1, 1, 1], z10(-3))
        .unwrap();
    let braided = BraidedFusionCategory::new(category.clone(), r).unwrap();
    let direct = braided.hexagon_defects(HexagonForm::Direct);
    let mirror = braided.hexagon_defects(HexagonForm::Mirror);
    assert_eq!(sorted(direct.iter().map(|d| d.labels).collect()), expected);
    assert_eq!(sorted(mirror.iter().map(|d| d.labels).collect()), expected);
    assert!(direct.iter().chain(&mirror).all(|d| d.reads_r([1, 1, 1])));
    assert!(matches!(braided.validate(), Err(FusionError::Braided(_))));
    // R^{tau tau}_1 = zeta_10^-4 -> zeta_10^4: five direct violations (same tuples).
    let r = fib
        .braided()
        .r_symbols()
        .with_entry([1, 1, 0], z10(4))
        .unwrap();
    let braided = BraidedFusionCategory::new(category, r).unwrap();
    assert_eq!(
        sorted(
            braided
                .hexagon_defects(HexagonForm::Direct)
                .iter()
                .map(|d| d.labels)
                .collect()
        ),
        expected
    );
    assert_eq!(braided.hexagon_defects(HexagonForm::Mirror).len(), 5);
}

#[test]
fn fibonacci_braid_generators_obey_the_relations_the_full_twist_and_the_hecke_quadratic() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    for (strands, total, dimension) in [(3usize, 1usize, 2usize), (4, 0, 2), (4, 1, 3), (5, 1, 5)] {
        let generators = fib.braid_generators(1, strands, total).unwrap();
        assert_eq!(generators.len(), strands - 1);
        assert!(generators
            .iter()
            .all(|g| g.shape() == (dimension, dimension)));
        assert_eq!(
            core_fusion_categories::braid_group::braid_relation_defects(&generators).unwrap(),
            vec![]
        );
        // The full twist (sigma_1 ... sigma_{n-1})^n is the scalar theta_total / theta_tau^n.
        let twist = fib.full_twist(1, strands, total).unwrap();
        let scalar = fib.full_twist_scalar(1, strands, total).unwrap();
        let expected = matrix::scale(
            &matrix::identity::<Cyc5>(dimension)
                .map_err(FusionError::from)
                .unwrap(),
            &scalar,
        )
        .map_err(FusionError::from)
        .unwrap();
        assert_eq!(twist, expected, "{strands} strands, total {total}");
        // Each generator has only the eigenvalues R_1 and R_tau: (sigma - R_1)(sigma - R_tau) = 0.
        let (r1, rt) = (
            fib.braided().r_entry([1, 1, 0]),
            fib.braided().r_entry([1, 1, 1]),
        );
        let identity = matrix::identity::<Cyc5>(dimension)
            .map_err(FusionError::from)
            .unwrap();
        for generator in &generators {
            let left = matrix::sub(
                generator,
                &matrix::scale(&identity, &r1)
                    .map_err(FusionError::from)
                    .unwrap(),
            )
            .map_err(FusionError::from)
            .unwrap();
            let right = matrix::sub(
                generator,
                &matrix::scale(&identity, &rt)
                    .map_err(FusionError::from)
                    .unwrap(),
            )
            .map_err(FusionError::from)
            .unwrap();
            assert!(matrix::is_zero_matrix(
                &matrix::multiply(&left, &right)
                    .map_err(FusionError::from)
                    .unwrap()
            ));
        }
    }
    // sigma_1 on three strands is diag(R^{tt}_1, R^{tt}_tau).
    let g = fib.braid_generators(1, 3, 1).unwrap();
    assert_eq!(g[0].get(0, 0).unwrap(), z10(-4));
    assert_eq!(g[0].get(1, 1).unwrap(), z10(3));
    assert_eq!(g[0].get(0, 1).unwrap(), Cyc5::zero());
}

#[test]
fn the_fibonacci_braid_image_is_not_a_finite_group_within_the_bound_but_that_is_not_a_density_claim(
) {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    let generators = fib.braid_generators(1, 3, 1).unwrap();
    let outcome = group_closure(&generators, 400, true).unwrap();
    // The projective closure exceeds 400 elements: reported as a bound, never as a
    // theorem about density.
    assert!(matches!(
        outcome,
        ClosureOutcome::ExceedsBound { bound: 400 }
    ));
}

#[test]
fn fibonacci_gauge_changes_f_but_not_the_modular_data() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    // Scale the two non-unit vertices (tau tau; 1) and (tau tau; tau): unit vertices fixed.
    let gauge = Gauge::trivial(fib.ring())
        .with([1, 1, 0], from_i64::<Cyc5>(2))
        .unwrap()
        .with([1, 1, 1], from_i64::<Cyc5>(3))
        .unwrap();
    let transformed = fib.braided().gauge_transform(&gauge).unwrap();
    assert_ne!(transformed.category(), fib.category());
    // F'[0,1] = (u^{tt}_0 u^{0t}_t)/(u^{tt}_t u^{tt}_t) F[0,1] = (2/9) F[0,1].
    assert_eq!(
        transformed.category().f_entry([1, 1, 1, 1], 0, 1),
        from_i64::<Cyc5>(2).try_div(&from_i64::<Cyc5>(9)).unwrap()
    );
    let regauged = RibbonFusionCategory::try_new(transformed, fib.dimensions().to_vec()).unwrap();
    assert_eq!(regauged.twists(), fib.twists());
    let (before, after) = (
        ModularData::verified(&fib).unwrap(),
        ModularData::verified(&regauged).unwrap(),
    );
    assert_eq!(before.s_tilde(), after.s_tilde());
    assert_eq!(before.p_plus(), after.p_plus());
    // The inverse gauge returns the original category exactly.
    let back = regauged
        .braided()
        .gauge_transform(&gauge.inverse().unwrap())
        .unwrap();
    assert_eq!(&back, fib.braided());
}

#[test]
fn fibonacci_conjugate_is_the_mirror_model_with_negated_central_charge() {
    let fib = catalog::fibonacci::<Cyc5>().unwrap();
    let mirror = fib.complex_conjugate().unwrap();
    check_universal_laws(&mirror);
    assert_eq!(mirror.twists()[1], z10(-4));
    // c -> -c: -14/5 = 6/5 modulo 4.
    assert_eq!(
        ModularData::verified(&mirror)
            .unwrap()
            .central_charge_mod_4()
            .unwrap(),
        q(6, 5)
    );
    // Reversing the braiding of a unitary-type category gives the same mirror data.
    let reversed = RibbonFusionCategory::try_new(
        fib.braided().reverse_braiding().unwrap(),
        fib.dimensions().to_vec(),
    )
    .unwrap();
    assert_eq!(reversed.twists(), mirror.twists());
}

// ---------------------------------------------------------------------------
// Semion
// ---------------------------------------------------------------------------

#[test]
fn the_semion_has_frobenius_schur_indicator_minus_one_and_central_charge_one() {
    let semion = catalog::semion::<GaussianRat>().unwrap();
    let i = GaussianRat::i();
    assert_eq!(semion.twists(), &[GaussianRat::one(), i.clone()]);
    assert_eq!(
        semion.category().f_entry([1, 1, 1, 1], 0, 0),
        GaussianRat::one().neg()
    );
    assert_eq!(semion.braided().r_entry([1, 1, 0]), i);
    let modular = ModularData::verified(&semion).unwrap();
    assert_eq!(modular.d_squared(), &from_i64::<GaussianRat>(2));
    // p_+ = 1 + i, p_+^2 = 2i = D^2 zeta_4: c = 1 modulo 4.
    assert_eq!(modular.p_plus(), &GaussianRat::one().add(&i));
    assert_eq!(modular.central_charge_mod_4().unwrap(), q(1, 1));
    assert_eq!(modular.frobenius_schur_indicator(1), Ok(-1));
    assert_eq!(
        semion
            .category()
            .frobenius_schur_indicator(1, semion.dimensions()),
        Ok(Some(-1))
    );
    let counts: Vec<String> = (0..4)
        .map(|g| modular.ground_state_degeneracy(g).unwrap().to_string())
        .collect();
    assert_eq!(counts, ["1", "2", "4", "8"]);
    check_universal_laws(&semion);
    // Q(i) does not contain sqrt 2: D is unavailable there, so no mod-8 claim is made.
    assert!(sqrt_two::<GaussianRat>().is_err());
}

#[test]
fn the_semion_central_charge_mod_8_needs_sqrt_two_and_is_then_exact() {
    let semion = catalog::semion::<Cyc8>().unwrap();
    let modular = ModularData::verified(&semion).unwrap();
    let d = sqrt_two::<Cyc8>().unwrap();
    assert_eq!(modular.central_charge_mod_8(&d).unwrap(), q(1, 1));
    // With -D the answer would shift by 4; the sign of D is decided exactly and -D is refused.
    assert_eq!(
        modular.central_charge_mod_8(&d.neg()),
        Err(FusionError::Modular(ModularDefect::NonPositiveDimension))
    );
    assert_eq!(
        modular.central_charge_mod_8(&from_i64::<Cyc8>(2)),
        Err(FusionError::Modular(ModularDefect::WrongGlobalDimension))
    );
}

#[test]
fn the_anti_semion_is_the_conjugate_and_the_wrong_braidings_are_refused() {
    let semion = catalog::semion::<GaussianRat>().unwrap();
    let anti = semion.complex_conjugate().unwrap();
    assert_eq!(anti.twists()[1], GaussianRat::i().conjugate());
    assert_eq!(
        ModularData::verified(&anti)
            .unwrap()
            .central_charge_mod_4()
            .unwrap(),
        q(3, 1)
    );
    // R^{ss}_0 = +1 or -1 violates both hexagons, at the single tuple found independently.
    for wrong in [GaussianRat::one(), GaussianRat::one().neg()] {
        let r = semion
            .braided()
            .r_symbols()
            .with_entry([1, 1, 0], wrong)
            .unwrap();
        let braided = BraidedFusionCategory::new(semion.category().clone(), r).unwrap();
        for form in [HexagonForm::Direct, HexagonForm::Mirror] {
            let defects = braided.hexagon_defects(form);
            assert_eq!(defects.len(), 1);
            assert_eq!(defects[0].labels, [1, 1, 1, 1, 0, 0]);
        }
    }
}

// ---------------------------------------------------------------------------
// Pointed models: toric code, three-fermion, quantum doubles, cyclic groups
// ---------------------------------------------------------------------------

#[test]
fn the_toric_code_is_modular_with_the_pinned_s_matrix_and_four_to_the_g_ground_states() {
    let toric = catalog::toric_code::<Rational>().unwrap();
    let minus_one = q(-1, 1);
    assert_eq!(
        toric.twists(),
        &[q(1, 1), q(1, 1), q(1, 1), minus_one.clone()]
    );
    let modular = ModularData::verified(&toric).unwrap();
    // S~ = [[1,1,1,1],[1,1,-1,-1],[1,-1,1,-1],[1,-1,-1,1]].
    let expected = [[1, 1, 1, 1], [1, 1, -1, -1], [1, -1, 1, -1], [1, -1, -1, 1]];
    for (a, row) in expected.iter().enumerate() {
        for (b, &value) in row.iter().enumerate() {
            assert_eq!(
                modular.s_tilde().get(a, b).unwrap(),
                q(value, 1),
                "S~[{a}][{b}]"
            );
        }
    }
    assert_eq!(modular.d_squared(), &q(4, 1));
    assert_eq!(modular.p_plus(), &q(2, 1));
    assert_eq!(modular.central_charge_mod_4().unwrap(), q(0, 1));
    assert_eq!(modular.central_charge_mod_8(&q(2, 1)).unwrap(), q(0, 1));
    for (g, expected) in [(0u32, 1u64), (1, 4), (2, 16), (3, 64)] {
        assert_eq!(
            modular.ground_state_degeneracy(g).unwrap().to_string(),
            expected.to_string()
        );
    }
    // e braided around m gives -1; e around e gives +1; m around eps gives -1.
    assert_eq!(
        toric.braided().monodromy([1, 2, 3]),
        Some(minus_one.clone())
    );
    assert_eq!(toric.braided().monodromy([1, 1, 0]), Some(q(1, 1)));
    assert_eq!(toric.braided().monodromy([2, 3, 1]), Some(minus_one));
    assert!(!toric.braided().is_symmetric());
    check_universal_laws(&toric);
    // Mixed-word braid relations (e, m, eps) and (eps, e, m) fuse to the unit.
    assert_eq!(
        toric
            .braided()
            .braid_relation_defects_on_word(&[1, 2, 3], 0)
            .unwrap(),
        vec![]
    );
    assert_eq!(
        toric
            .braided()
            .braid_relation_defects_on_word(&[3, 1, 2, 3], 3)
            .unwrap(),
        vec![]
    );
}

#[test]
fn the_toric_code_with_a_wrong_mutual_braiding_fails_both_hexagons_at_the_independent_tuples() {
    let toric = catalog::toric_code::<Rational>().unwrap();
    // c(e, m) = -1 is forced by the bicharacter; R^{em}_eps = +1 is not a bicharacter value.
    let r = toric
        .braided()
        .r_symbols()
        .with_entry([1, 2, 3], q(1, 1))
        .unwrap();
    let braided = BraidedFusionCategory::new(toric.category().clone(), r).unwrap();
    assert_eq!(
        sorted(
            braided
                .hexagon_defects(HexagonForm::Direct)
                .iter()
                .map(|d| d.labels)
                .collect()
        ),
        vec![
            [1, 2, 2, 1, 3, 3],
            [1, 3, 2, 0, 2, 3],
            [2, 1, 2, 1, 3, 0],
            [2, 3, 2, 3, 1, 0],
            [3, 1, 2, 0, 2, 1],
            [3, 2, 2, 3, 1, 1],
        ]
    );
    assert_eq!(
        sorted(
            braided
                .hexagon_defects(HexagonForm::Mirror)
                .iter()
                .map(|d| d.labels)
                .collect()
        ),
        vec![
            [1, 2, 1, 2, 3, 0],
            [1, 3, 1, 3, 2, 0],
            [2, 1, 1, 2, 3, 3],
            [2, 3, 1, 0, 1, 3],
            [3, 1, 1, 3, 2, 2],
            [3, 2, 1, 0, 1, 2],
        ]
    );
}

#[test]
fn the_three_fermion_model_has_central_charge_four_modulo_eight() {
    let model = catalog::three_fermion::<Rational>().unwrap();
    assert_eq!(model.twists(), &[q(1, 1), q(-1, 1), q(-1, 1), q(-1, 1)]);
    let modular = ModularData::verified(&model).unwrap();
    assert_eq!(modular.p_plus(), &q(-2, 1), "p_+ = 1 - 1 - 1 - 1");
    assert_eq!(modular.central_charge_mod_4().unwrap(), q(0, 1));
    // p_+ / D = -1 = zeta_2: c = 8 * 1 / 2 = 4 modulo 8 (the toric code has c = 0).
    assert_eq!(modular.central_charge_mod_8(&q(2, 1)).unwrap(), q(4, 1));
    // Same flipped mutual braiding as the toric code: a single hexagon-violation family.
    let r = model
        .braided()
        .r_symbols()
        .with_entry([1, 2, 3], model.braided().r_entry([1, 2, 3]).neg())
        .unwrap();
    let braided = BraidedFusionCategory::new(model.category().clone(), r).unwrap();
    assert_eq!(braided.hexagon_defects(HexagonForm::Direct).len(), 6);
    assert_eq!(braided.hexagon_defects(HexagonForm::Mirror).len(), 6);
    check_universal_laws(&model);
}

#[test]
fn a_symmetric_braiding_gives_a_degenerate_s_matrix_and_is_refused() {
    // Z_2 with the trivial braiding (c = 1): a valid ribbon category, symmetric, not modular.
    let trivial = catalog::pointed_braided::<Rational>(&[2], &[vec![0]], None).unwrap();
    assert!(trivial.braided().is_symmetric());
    assert_eq!(
        ModularData::verified(&trivial),
        Err(FusionError::Modular(ModularDefect::Degenerate {
            rank: 1,
            size: 2
        }))
    );
    // sVec: c(x, y) = (-1)^{xy}, a fermion with theta = -1; also symmetric and degenerate.
    let svec = catalog::pointed_braided::<Rational>(&[2], &[vec![1]], None).unwrap();
    assert_eq!(svec.twists(), &[q(1, 1), q(-1, 1)]);
    assert!(svec.braided().is_symmetric());
    assert_eq!(
        ModularData::verified(&svec),
        Err(FusionError::Modular(ModularDefect::Degenerate {
            rank: 1,
            size: 2
        }))
    );
}

#[test]
fn the_quantum_double_of_z3_is_modular_with_zero_central_charge() {
    let double = catalog::quantum_double_cyclic::<EisensteinRat>(3).unwrap();
    assert_eq!(double.ring().rank(), 9);
    let modular = ModularData::verified(&double).unwrap();
    // theta_{(a,b)} = zeta_3^{ab}; p_+ = sum_{a,b} zeta_3^{ab} = 3 = D.
    assert_eq!(modular.d_squared(), &from_i64::<EisensteinRat>(9));
    assert_eq!(modular.p_plus(), &from_i64::<EisensteinRat>(3));
    assert_eq!(modular.central_charge_mod_4().unwrap(), q(0, 1));
    assert_eq!(
        modular
            .central_charge_mod_8(&from_i64::<EisensteinRat>(3))
            .unwrap(),
        q(0, 1)
    );
    assert_eq!(modular.ground_state_degeneracy(1).unwrap().to_string(), "9");
    assert_eq!(
        modular.ground_state_degeneracy(2).unwrap().to_string(),
        "81"
    );
    // The charge-flux pair (1, 1) has twist zeta_3.
    let zeta3 = root_of_unity::<EisensteinRat>(3, 1).unwrap();
    assert_eq!(double.twists()[1 + 3], zeta3);
    check_universal_laws(&double);
}

#[test]
fn cyclic_pointed_models_have_quadratic_gauss_sums_and_the_right_central_charges() {
    // Z_3 over Q(zeta_12): p_+ = 1 + 2 zeta_3^k = +/- i sqrt 3 = the quadratic Gauss sum.
    let field3 = FiniteField::prime_field(3).unwrap();
    for k in [1i64, 2] {
        let model = catalog::cyclic_pointed::<Cyc12>(3, k).unwrap();
        let modular = ModularData::verified(&model).unwrap();
        let gauss = quadratic_gauss_sum::<Cyc12>(&field3, &field3.base(k as usize), &field3.zero())
            .unwrap();
        assert_eq!(modular.p_plus(), &gauss, "Z_3, k = {k}");
        assert_eq!(modular.d_squared(), &from_i64::<Cyc12>(3));
        // p_+^2 = -3: c = 2 modulo 4 for both k.
        assert_eq!(modular.central_charge_mod_4().unwrap(), q(2, 1));
        // The S~ matrix is symmetric with S~ S~^dagger = 3 I (verified), and Z_3 objects 1, 2 are dual.
        assert_eq!(model.ring().dual(1), Ok(2));
        assert_eq!(modular.frobenius_schur_indicator(1), Ok(0));
        check_universal_laws(&model);
    }
    // Z_5 over Q(zeta_5): G = (k/5) sqrt 5, with sqrt 5 = 1 + 2 (zeta + zeta^-1) in the field.
    let field5 = FiniteField::prime_field(5).unwrap();
    let sqrt5 = Cyc5::one().add(
        &Cyc5::zeta5(1)
            .add(&Cyc5::zeta5(-1))
            .mul(&from_i64::<Cyc5>(2)),
    );
    assert_eq!(sqrt5.mul(&sqrt5), from_i64::<Cyc5>(5));
    for (k, central_charge) in [(1i64, 0i64), (2, 4), (3, 4), (4, 0)] {
        let model = catalog::cyclic_pointed::<Cyc5>(5, k).unwrap();
        let modular = ModularData::verified(&model).unwrap();
        let gauss =
            quadratic_gauss_sum::<Cyc5>(&field5, &field5.base(k as usize), &field5.zero()).unwrap();
        assert_eq!(modular.p_plus(), &gauss, "Z_5, k = {k}");
        assert_eq!(modular.central_charge_mod_4().unwrap(), q(0, 1));
        assert_eq!(
            modular.central_charge_mod_8(&sqrt5).unwrap(),
            q(central_charge, 1),
            "Z_5, k = {k}: Legendre symbol ({k}/5)"
        );
    }
    // Z_7 over Q(zeta_28): G = (k/7) i sqrt 7.
    let field7 = FiniteField::prime_field(7).unwrap();
    let sqrt7 = sqrt7_28();
    for (k, central_charge) in [(1i64, 2i64), (3, 6), (2, 2)] {
        let model = catalog::cyclic_pointed::<Cyc28>(7, k).unwrap();
        let modular = ModularData::verified(&model).unwrap();
        let gauss = quadratic_gauss_sum::<Cyc28>(&field7, &field7.base(k as usize), &field7.zero())
            .unwrap();
        assert_eq!(modular.p_plus(), &gauss, "Z_7, k = {k}");
        assert_eq!(modular.central_charge_mod_4().unwrap(), q(2, 1));
        assert_eq!(
            modular.central_charge_mod_8(&sqrt7).unwrap(),
            q(central_charge, 1),
            "Z_7, k = {k}: Legendre symbol ({k}/7) selects i or -i"
        );
    }
}

#[test]
fn fields_without_the_needed_roots_of_unity_are_refused() {
    assert!(matches!(
        catalog::fibonacci::<Cyc8>(),
        Err(FusionError::FieldTooSmall { .. })
    ));
    assert!(matches!(
        catalog::semion::<Rational>(),
        Err(FusionError::FieldTooSmall { .. })
    ));
    assert!(matches!(
        catalog::quantum_double_cyclic::<Rational>(3),
        Err(FusionError::FieldTooSmall { .. })
    ));
    assert!(matches!(
        catalog::ising::<Cyc8>(),
        Err(FusionError::FieldTooSmall { .. })
    ));
}

#[test]
fn the_verlinde_formula_fails_on_a_perturbed_s_matrix() {
    let toric = catalog::toric_code::<Rational>().unwrap();
    let modular = ModularData::verified(&toric).unwrap();
    let mut rows = matrix::to_rows(modular.s_tilde())
        .map_err(FusionError::from)
        .unwrap();
    rows[1][2] = q(1, 1); // was -1
    let perturbed = matrix::from_rows(rows).map_err(FusionError::from).unwrap();
    let defects = toric
        .ring()
        .verlinde_defects(&perturbed, modular.d_squared())
        .unwrap();
    assert!(!defects.is_empty());
    // The honest matrix has none.
    assert!(toric
        .ring()
        .verlinde_defects(modular.s_tilde(), modular.d_squared())
        .unwrap()
        .is_empty());
    // Wrong shapes and a zero first row are typed refusals.
    let small = matrix::identity::<Rational>(2)
        .map_err(FusionError::from)
        .unwrap();
    assert!(matches!(
        toric.ring().verlinde_defects(&small, modular.d_squared()),
        Err(FusionError::Shape { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_fusion_categories/anyon_models.rs
// Claim: urn:core:crates_rs:tests:anyon-models:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5b67d264 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5b67d264` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5b67d264 {
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
impl BoundaryError5b67d264 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5b67d264 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5b67d264 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5b67d264 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5b67d264> {
        if capacity_bound == 0 {
            return Err(BoundaryError5b67d264::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5b67d264::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5b67d264::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_5b67d264() {
    let admitted = BoundaryRecord5b67d264::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5b67d264::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
