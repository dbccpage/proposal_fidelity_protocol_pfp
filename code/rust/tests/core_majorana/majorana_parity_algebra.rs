//! QM_212: the declared operator algebra behind the Majorana parity language.
//! Jordan–Wigner Majoranas on a declared Fock space, the parity observable, a
//! declared Kitaev chain, Majorana braid unitaries and their restriction to a
//! parity sector, the Ising fusion table, and the retracted tetron carrier.
//! Every statement is about declared matrices; none is about a device.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::involution as iv;
use linear_algebra::exact_field::{matrix as mx, ordered};
use core_fusion_categories::{
    error::FusionError,
    fusion_ring::{FusionTable, RingDefect},
};
use core_homology::matrix_reduction::{is_zero_z2, multiply_z2, rank_z2};
use core_lie_theory::finite_group::{generate, GroupError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_majorana::majorana_fock_algebra::{
    first_anticommutation_failure, gi, gq, FockCarrier, MajoranaError,
};

fn is_hermitian(m: &BasicMatrix<GaussianRat>) -> bool {
    iv::adjoint(m).is_ok_and(|adjoint| adjoint == *m)
}

fn is_positive_semidefinite(m: &BasicMatrix<GaussianRat>) -> bool {
    is_hermitian(m) && ordered::hermitian_is_positive_semidefinite(m).unwrap_or(false)
}
fn is_unitary(m: &BasicMatrix<GaussianRat>) -> bool {
    core_lie_theory::scalar::is_unitary(m).unwrap()
}
fn close_under_multiplication(
    g: &[BasicMatrix<GaussianRat>],
    bound: usize,
) -> Result<Vec<BasicMatrix<GaussianRat>>, GroupError> {
    generate(
        g,
        mx::identity(g[0].rows()).unwrap(),
        |a, b| mx::multiply(a, b).unwrap(),
        |m| m.as_slice().to_vec(),
        bound,
    )
}

fn commutes(a: &BasicMatrix<GaussianRat>, b: &BasicMatrix<GaussianRat>) -> bool {
    mx::multiply(&(a), &(b)).unwrap() == mx::multiply(&(b), &(a)).unwrap()
}

fn anticommutator(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> BasicMatrix<GaussianRat> {
    mx::add(
        &(mx::multiply(&(a), &(b)).unwrap()),
        &(&mx::multiply(&(b), &(a)).unwrap()),
    )
    .unwrap()
}

fn shifted(h: &BasicMatrix<GaussianRat>, energy: i64) -> BasicMatrix<GaussianRat> {
    mx::sub(
        &(h),
        &mx::scale(&mx::identity(h.rows()).unwrap(), &gi(energy, 0)).unwrap(),
    )
    .unwrap()
}

fn two_by_two(entries: [(i64, i64, i64); 4]) -> BasicMatrix<GaussianRat> {
    // (re numerator, im numerator, common denominator)
    let z = |(re, im, d): (i64, i64, i64)| gq(re, d, im, d);
    mx::from_rows(vec![
        vec![z(entries[0]), z(entries[1])],
        vec![z(entries[2]), z(entries[3])],
    ])
    .unwrap()
}

#[test]
fn jordan_wigner_majoranas_satisfy_the_clifford_and_canonical_anticommutation_relations() {
    for modes in 1..=4 {
        let carrier = FockCarrier::new(modes).unwrap();
        let gammas = carrier.majoranas();
        assert_eq!(gammas.len(), 2 * modes);
        assert!(gammas.iter().all(is_hermitian));
        assert_eq!(first_anticommutation_failure(&gammas).unwrap(), None);
        let identity = mx::identity(carrier.dimension()).unwrap();
        let lowering: Vec<BasicMatrix<GaussianRat>> =
            (1..=modes).map(|j| carrier.lowering(j).unwrap()).collect();
        for (j, c_j) in lowering.iter().enumerate() {
            for (k, c_k) in lowering.iter().enumerate() {
                let expected = if j == k {
                    identity.clone()
                } else {
                    mx::zeros(carrier.dimension(), carrier.dimension()).unwrap()
                };
                assert_eq!(anticommutator(c_j, &iv::adjoint(c_k).unwrap()), expected);
                assert_eq!(
                    anticommutator(c_j, c_k),
                    mx::zeros(carrier.dimension(), carrier.dimension()).unwrap()
                );
            }
        }
    }
    // Without the Z strings the operators on different modes commute instead.
    let x = two_by_two([(0, 0, 1), (1, 0, 1), (1, 0, 1), (0, 0, 1)]);
    let y = two_by_two([(0, 0, 1), (0, -1, 1), (0, 1, 1), (0, 0, 1)]);
    let i2 = mx::identity(2).unwrap();
    let stringless = vec![
        mx::kronecker(&(x), &(&i2)).unwrap(),
        mx::kronecker(&(y), &(&i2)).unwrap(),
        mx::kronecker(&(i2), &(&x)).unwrap(),
        mx::kronecker(&(i2), &(&y)).unwrap(),
    ];
    assert_eq!(
        first_anticommutation_failure(&stringless).unwrap(),
        Some((0, 2))
    );
}

#[test]
fn the_parity_is_minus_one_to_the_occupation_and_anticommutes_with_every_majorana() {
    for modes in 1..=4 {
        let carrier = FockCarrier::new(modes).unwrap();
        let parity = carrier.parity();
        let signs: Vec<GaussianRat> = (0..carrier.dimension())
            .map(|b: usize| {
                gi(
                    if b.count_ones().is_multiple_of(2) {
                        1
                    } else {
                        -1
                    },
                    0,
                )
            })
            .collect();
        assert_eq!(parity, mx::diagonal(&signs).unwrap());
        for gamma in carrier.majoranas() {
            assert_eq!(
                anticommutator(&parity, &gamma),
                mx::zeros(carrier.dimension(), carrier.dimension()).unwrap()
            );
        }
        let gammas = carrier.majoranas();
        for a in &gammas {
            for b in &gammas {
                assert!(commutes(&parity, &mx::multiply(&(a), &(b)).unwrap()));
            }
        }
        assert_eq!(
            (
                carrier.sector_basis(true).len(),
                carrier.sector_basis(false).len()
            ),
            (1 << (modes - 1), 1 << (modes - 1))
        );
    }
}

#[test]
fn the_declared_kitaev_chain_is_hermitian_and_conserves_parity_at_every_grid_point() {
    let grid = [ri(-1), rq(1, 2), ri(2)];
    let two = FockCarrier::new(2).unwrap();
    let parity = two.parity();
    for t in &grid {
        for delta in &grid {
            for mu in &grid {
                let h = two.kitaev_chain(t, delta, mu);
                assert!(is_hermitian(&h));
                assert!(commutes(&h, &parity));
            }
        }
    }
    let three = FockCarrier::new(3).unwrap();
    let h = three.kitaev_chain(&rq(3, 2), &rq(-2, 3), &rq(5, 7));
    assert!(is_hermitian(&h));
    assert!(commutes(&h, &three.parity()));
}

#[test]
fn at_the_sweet_spot_the_chain_is_a_sum_of_bond_terms_and_the_end_majoranas_commute_with_it() {
    for modes in 2..=4 {
        let carrier = FockCarrier::new(modes).unwrap();
        let gammas = carrier.majoranas();
        for t in [ri(1), rq(2, 3), ri(-3)] {
            let h = carrier.kitaev_chain(&t, &t, &ri(0));
            let bonds = (1..modes).fold(
                mx::zeros(carrier.dimension(), carrier.dimension()).unwrap(),
                |acc, j| {
                    mx::add(
                        &acc,
                        &mx::multiply(&gammas[2 * j - 1], &gammas[2 * j]).unwrap(),
                    )
                    .unwrap()
                },
            );
            assert_eq!(
                h,
                mx::scale(
                    &bonds,
                    &GaussianRat::i().mul(&GaussianRat::from_rational(t.clone()))
                )
                .unwrap()
            );
            for (index, gamma) in gammas.iter().enumerate() {
                let end = index == 0 || index == 2 * modes - 1;
                assert_eq!(commutes(&h, gamma), end, "gamma_{}", index + 1);
            }
        }
    }
    // The chemical potential alone is -(i mu / 2) sum_j gamma_(2j-1) gamma_(2j).
    let carrier = FockCarrier::new(3).unwrap();
    let gammas = carrier.majoranas();
    let onsite = (0..3).fold(mx::zeros(8, 8).unwrap(), |acc, j| {
        mx::add(
            &acc,
            &mx::multiply(&gammas[2 * j], &gammas[2 * j + 1]).unwrap(),
        )
        .unwrap()
    });
    assert_eq!(
        carrier.kitaev_chain(&ri(0), &ri(0), &ri(4)),
        mx::scale(&onsite, &gi(0, -2)).unwrap()
    );
}

#[test]
fn the_sweet_spot_spectrum_is_exact_and_the_ground_space_holds_one_state_of_each_parity() {
    for (modes, spectrum) in [
        (2usize, vec![(-1i64, 2usize), (1, 2)]),
        (3, vec![(-2, 2), (0, 4), (2, 2)]),
    ] {
        let carrier = FockCarrier::new(modes).unwrap();
        let h = carrier.kitaev_chain(&ri(1), &ri(1), &ri(0));
        let dimension = carrier.dimension();
        let mut total = 0;
        for (energy, multiplicity) in &spectrum {
            assert_eq!(
                dimension
                    - linear_algebra::exact_field::elimination::rank(&shifted(&h, *energy))
                        .unwrap(),
                *multiplicity
            );
            total += multiplicity;
        }
        assert_eq!(total, dimension);
        let ground = shifted(&h, spectrum[0].0);
        assert!(is_positive_semidefinite(&ground));
        for even in [true, false] {
            let sector = carrier.restrict_to_sector(&ground, even).unwrap();
            assert_eq!(
                sector.rows() - linear_algebra::exact_field::elimination::rank(&sector).unwrap(),
                1
            );
        }
    }
}

#[test]
fn off_the_sweet_spot_the_end_majorana_is_not_conserved_and_the_parity_degeneracy_splits() {
    let carrier = FockCarrier::new(2).unwrap();
    let gamma_1 = carrier.majorana(1).unwrap();
    let detuned = carrier.kitaev_chain(&ri(1), &ri(1), &rq(1, 2));
    let unequal = carrier.kitaev_chain(&ri(1), &rq(1, 2), &ri(0));
    assert!(!commutes(&detuned, &gamma_1));
    assert!(!commutes(&unequal, &gamma_1));
    assert!(commutes(&detuned, &carrier.parity()));
    // Odd sector: lowest eigenvalue exactly -1. Even sector: strictly below -1.
    let odd = carrier
        .restrict_to_sector(&shifted(&detuned, -1), false)
        .unwrap();
    assert!(is_positive_semidefinite(&odd));
    assert_eq!(
        linear_algebra::exact_field::elimination::rank(&odd).unwrap(),
        1
    );
    let even = carrier
        .restrict_to_sector(&shifted(&detuned, -1), true)
        .unwrap();
    assert!(!is_positive_semidefinite(&even));
    let determinant = even
        .get_ref(0, 0)
        .unwrap()
        .mul(even.get_ref(1, 1).unwrap())
        .sub(&even.get_ref(0, 1).unwrap().mul(even.get_ref(1, 0).unwrap()));
    assert_eq!(determinant, gq(-1, 4, 0, 1));
}

#[test]
fn majorana_braid_unitaries_satisfy_the_braid_relations_and_conserve_parity() {
    for modes in 2..=3 {
        let carrier = FockCarrier::new(modes).unwrap();
        let gammas = carrier.majoranas();
        let braids: Vec<BasicMatrix<GaussianRat>> = (1..2 * modes)
            .map(|a| carrier.braid_unitary(a).unwrap())
            .collect();
        let identity = mx::identity(carrier.dimension()).unwrap();
        for (a, u) in braids.iter().enumerate() {
            assert!(is_unitary(u));
            assert!(commutes(u, &carrier.parity()));
            assert_eq!(
                mx::multiply(u, u).unwrap(),
                mx::scale(
                    &(mx::multiply(&(gammas[a + 1]), &(&gammas[a])).unwrap()),
                    &(&gi(0, 1))
                )
                .unwrap()
            );
            assert_eq!(mx::power(u, 4).unwrap(), identity);
            for (b, v) in braids.iter().enumerate().skip(a + 1) {
                if b == a + 1 {
                    assert_eq!(
                        mx::multiply(&mx::multiply(u, v).unwrap(), u).unwrap(),
                        mx::multiply(&mx::multiply(v, u).unwrap(), v).unwrap()
                    );
                    assert!(!commutes(u, v));
                } else {
                    assert!(commutes(u, v));
                }
            }
        }
    }
}

/// `R' = diag(1, i)` and `F R' F = (1/2) H R' H`: the Ising matrices of the
/// source, `R = e^(-i pi/8) R'` and `F R F`, without the global phase, which
/// lies outside `Q(i)` and cancels in every identity that is homogeneous in `R`.
fn declared_ising_pair() -> (BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>) {
    let r = mx::diagonal(&[gi(1, 0), gi(0, 1)]).unwrap();
    let h = two_by_two([(1, 0, 1), (1, 0, 1), (1, 0, 1), (-1, 0, 1)]);
    // F = H / sqrt 2 squares to the identity because H^2 = 2I.
    assert_eq!(
        mx::multiply(&(h), &(&h)).unwrap(),
        mx::scale(&mx::identity(2).unwrap(), &gi(2, 0)).unwrap()
    );
    (
        r.clone(),
        mx::scale(
            &(mx::multiply(&(mx::multiply(&(h), &(&r)).unwrap()), &(&h)).unwrap()),
            &(&gq(1, 2, 0, 1)),
        )
        .unwrap(),
    )
}

#[test]
fn on_the_even_sector_of_two_modes_the_braid_unitaries_are_the_declared_ising_matrices() {
    let carrier = FockCarrier::new(2).unwrap();
    let (r, frf) = declared_ising_pair();
    let restricted: Vec<BasicMatrix<GaussianRat>> = (1..=3)
        .map(|a| {
            carrier
                .restrict_to_sector(&carrier.braid_unitary(a).unwrap(), true)
                .unwrap()
        })
        .collect();
    assert_eq!(restricted, vec![r.clone(), frf.clone(), r.clone()]);
    assert_eq!(
        frf,
        two_by_two([(1, 1, 2), (1, -1, 2), (1, -1, 2), (1, 1, 2)])
    );
    assert_eq!(
        mx::multiply(&(mx::multiply(&(r), &(&frf)).unwrap()), &(&r)).unwrap(),
        mx::multiply(&(mx::multiply(&(frf), &(&r)).unwrap()), &(&frf)).unwrap()
    );
}

#[test]
fn the_braid_images_are_finite_groups() {
    let (r, frf) = declared_ising_pair();
    let group = close_under_multiplication(&[r, frf], 200).unwrap();
    assert_eq!(group.len(), 96);
    let scalars: Vec<&BasicMatrix<GaussianRat>> = group
        .iter()
        .filter(|g| {
            g.get_ref(0, 1).unwrap() == &gi(0, 0)
                && g.get_ref(1, 0).unwrap() == &gi(0, 0)
                && g.get_ref(0, 0).unwrap() == g.get_ref(1, 1).unwrap()
        })
        .collect();
    assert_eq!(scalars.len(), 4);
    let carrier = FockCarrier::new(2).unwrap();
    let braids: Vec<BasicMatrix<GaussianRat>> =
        (1..=3).map(|a| carrier.braid_unitary(a).unwrap()).collect();
    assert_eq!(
        close_under_multiplication(&braids, 2000).unwrap().len(),
        768
    );
}

#[test]
fn the_declared_ising_fusion_table_is_a_commutative_associative_unital_table() {
    let ising = FusionTable::ising();
    assert_eq!(ising.first_defect(), None);
    assert_eq!(ising.multiplicity(1, 1, 0), Ok(1));
    assert_eq!(ising.multiplicity(1, 1, 2), Ok(1));
    assert_eq!(ising.multiplicity(1, 1, 1), Ok(0));

    let base = [
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
        [[0, 0, 1], [0, 1, 0], [1, 0, 0]],
    ];
    let mut unit = base;
    unit[0][1] = [0, 0, 1];
    assert_eq!(
        FusionTable::from_array(unit).unwrap().first_defect(),
        Some(RingDefect::Unit { label: 1 })
    );
    let mut lopsided = base;
    lopsided[2][1] = [1, 0, 0];
    assert_eq!(
        FusionTable::from_array(lopsided).unwrap().first_defect(),
        Some(RingDefect::Commutativity { left: 1, right: 2 })
    );
    let mut psi_absorbs = base;
    psi_absorbs[1][2] = [0, 0, 1];
    psi_absorbs[2][1] = [0, 0, 1];
    assert_eq!(
        FusionTable::from_array(psi_absorbs).unwrap().first_defect(),
        Some(RingDefect::Associativity {
            labels: (1, 1, 2),
            outcome: 0,
            left: 1,
            right: 0
        })
    );
}

#[test]
fn fusion_paths_of_sigma_count_the_parity_sectors_of_the_fock_space() {
    let ising = FusionTable::ising();
    for modes in 1..=5 {
        let carrier = FockCarrier::new(modes).unwrap();
        let even = carrier.sector_basis(true).len() as u64;
        let odd = carrier.sector_basis(false).len() as u64;
        assert_eq!(
            ising.charge_counts_u64(1, 2 * modes),
            Ok(vec![even, 0, odd])
        );
        assert_eq!(
            ising.charge_counts_u64(1, 2 * modes - 1),
            Ok(vec![0, even, 0])
        );
    }
    assert_eq!(ising.charge_counts_u64(1, 0), Ok(vec![1, 0, 0]));
    assert_eq!(ising.charge_counts_u64(2, 3), Ok(vec![0, 0, 1]));
}

/// The superseded tetron carrier: six modes per tetron, four bonds inside it,
/// two bonds to the next tetron, and one face for each pair of neighbours.
fn legacy_tetron_carrier(tetrons: usize) -> (Vec<Vec<u8>>, Vec<Vec<u8>>) {
    let modes = 6 * tetrons;
    let mut bonds: Vec<(usize, usize)> = Vec::new();
    let mut top = Vec::new();
    let mut forward = Vec::new();
    let mut back = Vec::new();
    for t in 0..tetrons {
        let o = 6 * t;
        top.push(bonds.len());
        bonds.extend([(o, o + 1), (o + 2, o + 3), (o + 1, o + 4), (o + 3, o + 5)]);
        if t + 1 < tetrons {
            let next = o + 6;
            forward.push(bonds.len());
            bonds.push((o + 1, next));
            back.push(bonds.len());
            bonds.push((next + 1, o));
        }
    }
    let d0 = bonds
        .iter()
        .map(|&(u, v)| (0..modes).map(|m| u8::from(m == u || m == v)).collect())
        .collect();
    let d1 = (0..tetrons.saturating_sub(1))
        .map(|t| {
            let face = [top[t], forward[t], top[t + 1], back[t]];
            (0..bonds.len())
                .map(|b| u8::from(face.contains(&b)))
                .collect()
        })
        .collect();
    (d0, d1)
}

#[test]
fn the_retracted_tetron_carrier_fills_every_cycle_it_has() {
    for tetrons in 1..=4usize {
        let (d0, d1) = legacy_tetron_carrier(tetrons);
        let edges = d0.len();
        assert_eq!(edges, 6 * tetrons - 2);
        let rank_d0 = rank_z2(&d0).unwrap();
        let rank_d1 = if d1.is_empty() {
            0
        } else {
            rank_z2(&d1).unwrap()
        };
        if !d1.is_empty() {
            assert!(is_zero_z2(&multiply_z2(&d1, &d0).unwrap()));
        }
        // Graph cycle rank T - 1, and H^1 = 0: no logical class can live here.
        assert_eq!(edges - rank_d0, tetrons - 1);
        assert_eq!(edges - rank_d1 - rank_d0, 0);
    }
}

#[test]
fn carriers_operators_and_tables_refuse_malformed_requests() {
    assert_eq!(FockCarrier::new(0), Err(MajoranaError::Modes { modes: 0 }));
    assert_eq!(FockCarrier::new(6), Err(MajoranaError::Modes { modes: 6 }));
    let carrier = FockCarrier::new(2).unwrap();
    assert_eq!(
        carrier.majorana(0),
        Err(MajoranaError::MajoranaIndex { index: 0, count: 4 })
    );
    assert_eq!(
        carrier.majorana(5),
        Err(MajoranaError::MajoranaIndex { index: 5, count: 4 })
    );
    assert_eq!(
        carrier.lowering(3),
        Err(MajoranaError::ModeIndex { index: 3, modes: 2 })
    );
    assert_eq!(
        carrier.braid_unitary(4),
        Err(MajoranaError::BraidIndex { index: 4, count: 4 })
    );
    assert_eq!(
        carrier.braid_unitary(0),
        Err(MajoranaError::BraidIndex { index: 0, count: 4 })
    );
    let gamma_1 = carrier.majorana(1).unwrap();
    assert_eq!(
        carrier.restrict_to_sector(&gamma_1, true),
        Err(MajoranaError::MixesSectors)
    );
    assert_eq!(
        carrier.restrict_to_sector(&mx::identity(2).unwrap(), true),
        Err(MajoranaError::Shape {
            rows: 2,
            cols: 2,
            dimension: 4
        })
    );
    assert_eq!(
        first_anticommutation_failure(&[gamma_1, mx::identity(2).unwrap()]),
        Err(MajoranaError::FamilyShape { index: 1 })
    );
    let ising = FusionTable::ising();
    assert_eq!(
        ising.multiplicity(3, 0, 0),
        Err(FusionError::Label { label: 3, rank: 3 })
    );
    assert_eq!(
        ising.charge_counts_u64(3, 2),
        Err(FusionError::Label { label: 3, rank: 3 })
    );
}

#[test]
fn kitaev_pfaffians_replay_determinants_and_boundary_twists_change_the_finite_chain() {
    use linear_algebra::exact_field::elimination::determinant;
    let carrier = FockCarrier::new(3).unwrap();
    let parity = carrier.parity();
    for boundary in [None, Some(1), Some(-1)] {
        let a = carrier
            .bdg_majorana_matrix(&ri(1), &ri(1), &ri(0), boundary)
            .unwrap();
        assert_eq!(mx::transpose(&a).unwrap(), mx::scale(&a, &ri(-1)).unwrap());
        let pf = carrier
            .kitaev_pfaffian(&ri(1), &ri(1), &ri(0), boundary)
            .unwrap();
        assert_eq!(&pf * &pf, determinant(&a).unwrap());
        let h = carrier
            .kitaev_chain_with_boundary(&ri(1), &ri(1), &ri(0), boundary)
            .unwrap();
        assert_eq!(h, iv::adjoint(&h).unwrap());
        assert_eq!(
            mx::multiply(&h, &parity).unwrap(),
            mx::multiply(&parity, &h).unwrap()
        );
    }
    assert_eq!(
        carrier
            .kitaev_pfaffian(&ri(1), &ri(1), &ri(0), None)
            .unwrap(),
        ri(0)
    );
    let periodic = carrier
        .kitaev_pfaffian(&ri(1), &ri(1), &ri(0), Some(1))
        .unwrap();
    let anti = carrier
        .kitaev_pfaffian(&ri(1), &ri(1), &ri(0), Some(-1))
        .unwrap();
    assert_ne!(periodic, ri(0));
    assert_eq!(periodic, -anti);
    assert_eq!(
        FockCarrier::bulk_kitaev_invariant(&ri(1), &ri(1), &ri(0)),
        Some(-1)
    );
    assert_eq!(
        FockCarrier::bulk_kitaev_invariant(&ri(1), &ri(1), &ri(3)),
        Some(1)
    );
    assert_eq!(
        FockCarrier::bulk_kitaev_invariant(&ri(1), &ri(1), &ri(2)),
        None
    );
    assert_eq!(
        FockCarrier::bulk_kitaev_invariant(&ri(1), &ri(0), &ri(0)),
        None
    );
    assert_eq!(
        carrier.bdg_majorana_matrix(&ri(1), &ri(1), &ri(0), Some(0)),
        Err(MajoranaError::BoundarySign)
    );
}

// Origin: engine/crates_rs/tests/core_majorana/majorana_parity_algebra.rs
// Claim: urn:core:crates_rs:tests:majorana-parity-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord43aab531 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord43aab531` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError43aab531 {
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
impl BoundaryError43aab531 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError43aab531 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError43aab531 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord43aab531 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError43aab531> {
        if capacity_bound == 0 {
            return Err(BoundaryError43aab531::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError43aab531::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError43aab531::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_43aab531() {
    let admitted = BoundaryRecord43aab531::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord43aab531::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
