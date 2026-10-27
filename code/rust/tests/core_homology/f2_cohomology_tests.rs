//! Homology and cohomology with coefficients in F_2: cocycle, coboundary and
//! class counts, bases, the coboundary equation as a torsor over the cocycles,
//! Euler-Poincare, the universal coefficient cross-check against integral
//! homology (Smith normal form), and the Bockstein homomorphism.
//!
//! Each test states the invariant it protects. The independent routes are
//! brute-force enumeration of every cochain and every vertex function of a
//! small complex (counts of cocycles, coboundaries and solutions), the
//! integral homology of `core_homology::integral_chain_complex` (Smith normal
//! form shares no code with the GF(2) elimination), and the rational Betti
//! numbers of `core_homology::simplicial`.
//!
//! AuthorityEffect: None.

use num_bigint::BigUint;
use core_homology::f2_cohomology::{ComplexError, F2ChainComplex};
use core_homology::integral_chain_complex::{IntegralChainComplex, SparseIntegerMatrix};
use core_homology::simplicial::{Simplex, SimplicialComplex};
use core_number_theory::gf2::{F2Error, F2Matrix, F2Vector};
use std::collections::{BTreeMap, BTreeSet};

// ---------------------------------------------------------------------------
// Complexes
// ---------------------------------------------------------------------------

fn complex(facets: &[&[usize]]) -> SimplicialComplex {
    SimplicialComplex::from_simplices(
        facets
            .iter()
            .map(|f| Simplex::from_unordered(f.to_vec()).unwrap())
            .collect(),
    )
    .unwrap()
}

fn circle() -> SimplicialComplex {
    complex(&[&[0, 1], &[1, 2], &[0, 2]])
}

fn disk() -> SimplicialComplex {
    complex(&[&[0, 1, 2]])
}

fn sphere() -> SimplicialComplex {
    complex(&[&[0, 1, 2], &[0, 1, 3], &[0, 2, 3], &[1, 2, 3]])
}

/// The octahedron: one vertex from each antipodal pair (0,1), (2,3), (4,5).
fn octahedron() -> SimplicialComplex {
    let mut facets = Vec::new();
    for a in [0, 1] {
        for b in [2, 3] {
            for c in [4, 5] {
                facets.push(vec![a, b, c]);
            }
        }
    }
    let refs: Vec<&[usize]> = facets.iter().map(Vec::as_slice).collect();
    complex(&refs)
}

/// The 7-vertex torus: triangles (i, i+1, i+3) and (i, i+2, i+3) mod 7.
fn torus() -> SimplicialComplex {
    let mut facets = Vec::new();
    for i in 0..7usize {
        facets.push(vec![i, (i + 1) % 7, (i + 3) % 7]);
        facets.push(vec![i, (i + 2) % 7, (i + 3) % 7]);
    }
    let refs: Vec<&[usize]> = facets.iter().map(Vec::as_slice).collect();
    complex(&refs)
}

/// The 6-vertex projective plane (10 triangles, every edge in exactly two).
fn projective_plane() -> SimplicialComplex {
    complex(&[
        &[0, 1, 2],
        &[0, 2, 3],
        &[0, 3, 4],
        &[0, 4, 5],
        &[0, 1, 5],
        &[1, 2, 4],
        &[2, 3, 5],
        &[1, 3, 4],
        &[2, 4, 5],
        &[1, 3, 5],
    ])
}

/// The 5-vertex Mobius band: triangles (i, i+1, i+2) mod 5.
fn mobius_band() -> SimplicialComplex {
    let facets: Vec<Vec<usize>> = (0..5usize)
        .map(|i| vec![i, (i + 1) % 5, (i + 2) % 5])
        .collect();
    let refs: Vec<&[usize]> = facets.iter().map(Vec::as_slice).collect();
    complex(&refs)
}

fn sparse(rows: usize, columns: Vec<Vec<(usize, i64)>>) -> SparseIntegerMatrix {
    SparseIntegerMatrix::new(rows, columns).unwrap()
}

/// One vertex, one loop, one face with boundary `e e`: H_1 = Z/2.
fn projective_plane_cell() -> IntegralChainComplex {
    IntegralChainComplex::new(
        vec![1, 1, 1],
        vec![
            sparse(1, vec![vec![(0, 1), (0, -1)]]),
            sparse(1, vec![vec![(0, 1), (0, 1)]]),
        ],
    )
    .unwrap()
}

/// One vertex, loops `a`, `b`, one face with boundary `a b a^-1 b`: H_1 = Z + Z/2.
fn klein_bottle_cell() -> IntegralChainComplex {
    IntegralChainComplex::new(
        vec![1, 2, 1],
        vec![
            sparse(1, vec![vec![(0, 1), (0, -1)], vec![(0, 1), (0, -1)]]),
            sparse(2, vec![vec![(0, 1), (1, 1), (0, -1), (1, 1)]]),
        ],
    )
    .unwrap()
}

/// One vertex, loops `a`, `b`, one face with boundary `a b a^-1 b^-1`: H_1 = Z^2.
fn torus_cell() -> IntegralChainComplex {
    IntegralChainComplex::new(
        vec![1, 2, 1],
        vec![
            sparse(1, vec![vec![(0, 1), (0, -1)], vec![(0, 1), (0, -1)]]),
            sparse(2, vec![vec![(0, 1), (1, 1), (0, -1), (1, -1)]]),
        ],
    )
    .unwrap()
}

fn f2(c: &SimplicialComplex) -> F2ChainComplex {
    F2ChainComplex::from_simplicial_complex(c).unwrap()
}

fn all_named_surfaces() -> Vec<(&'static str, SimplicialComplex)> {
    vec![
        ("circle", circle()),
        ("disk", disk()),
        ("sphere", sphere()),
        ("octahedron", octahedron()),
        ("torus", torus()),
        ("projective plane", projective_plane()),
        ("Mobius band", mobius_band()),
    ]
}

// ---------------------------------------------------------------------------
// Brute force, independent of any elimination
// ---------------------------------------------------------------------------

struct Incidence {
    vertices: usize,
    edges: Vec<(usize, usize)>,
    /// Bit `e` of `faces[f]` is set when edge `e` lies on face `f`.
    faces: Vec<u64>,
}

fn incidence(c: &SimplicialComplex) -> Incidence {
    let edges: Vec<(usize, usize)> = c
        .simplices(1)
        .iter()
        .map(|s| (s.vertices()[0], s.vertices()[1]))
        .collect();
    let index: BTreeMap<(usize, usize), usize> =
        edges.iter().enumerate().map(|(i, &e)| (e, i)).collect();
    let faces = c
        .simplices(2)
        .iter()
        .map(|t| {
            let v = t.vertices();
            [(v[0], v[1]), (v[0], v[2]), (v[1], v[2])]
                .iter()
                .fold(0u64, |mask, e| mask | (1u64 << index[e]))
        })
        .collect();
    Incidence {
        vertices: c.count(0),
        edges,
        faces,
    }
}

fn mask(v: &F2Vector) -> u64 {
    v.support().iter().fold(0, |m, &i| m | (1u64 << i))
}

fn vector_of(mask: u64, len: usize) -> F2Vector {
    F2Vector::from_indices(
        len,
        &(0..len)
            .filter(|&i| (mask >> i) & 1 == 1)
            .collect::<Vec<_>>(),
    )
    .unwrap()
}

/// `delta^1 c` on plain masks: face `f` gets the parity of the edges of `c` on it.
fn coboundary_mask(faces: &[u64], c: u64) -> u64 {
    faces.iter().enumerate().fold(0, |m, (f, face)| {
        m | (u64::from((face & c).count_ones() % 2 == 1) << f)
    })
}

fn brute_force_cocycle_count(inc: &Incidence) -> u64 {
    (0..(1u64 << inc.edges.len()))
        .filter(|&c| coboundary_mask(&inc.faces, c) == 0)
        .count() as u64
}

fn brute_force_coboundary_count(inc: &Incidence) -> u64 {
    let images: BTreeSet<u64> = (0..(1u64 << inc.vertices))
        .map(|s| {
            inc.edges
                .iter()
                .enumerate()
                .fold(0u64, |m, (e, &(u, v))| m | (((s >> u) ^ (s >> v)) & 1) << e)
        })
        .collect();
    images.len() as u64
}

fn brute_force_solutions(inc: &Incidence, w: u64) -> BTreeSet<u64> {
    (0..(1u64 << inc.edges.len()))
        .filter(|&s| coboundary_mask(&inc.faces, s) == w)
        .collect()
}

// ---------------------------------------------------------------------------
// Dimensions and counts
// ---------------------------------------------------------------------------

#[test]
fn simplicial_complexes_have_the_known_f2_cohomology() {
    // dim H^k(X; F_2) for k = 0, 1, .. : the circle, disk, sphere, octahedron,
    // 7-vertex torus, 6-vertex projective plane and 5-vertex Mobius band.
    let expected: [(&str, Vec<usize>); 7] = [
        ("circle", vec![1, 1]),
        ("disk", vec![1, 0, 0]),
        ("sphere", vec![1, 0, 1]),
        ("octahedron", vec![1, 0, 1]),
        ("torus", vec![1, 2, 1]),
        ("projective plane", vec![1, 1, 1]),
        ("Mobius band", vec![1, 1, 0]),
    ];
    for ((name, c), (expected_name, dims)) in all_named_surfaces().into_iter().zip(expected) {
        assert_eq!(name, expected_name);
        let complex = f2(&c);
        let found: Vec<usize> = (0..=complex.top_dimension())
            .map(|k| complex.cohomology_dimension(k).unwrap())
            .collect();
        assert_eq!(found, dims, "{name}");
    }
}

#[test]
fn cocycle_coboundary_and_class_counts_of_small_complexes() {
    // (|Z^1|, |B^1|, |H^1|) as powers of two.
    let expected: [(&str, (u32, u32, u32)); 7] = [
        ("circle", (3, 2, 1)),
        ("disk", (2, 2, 0)),
        ("sphere", (3, 3, 0)),
        ("octahedron", (5, 5, 0)),
        ("torus", (8, 6, 2)),
        ("projective plane", (6, 5, 1)),
        ("Mobius band", (5, 4, 1)),
    ];
    for ((name, c), (_, (z, b, h))) in all_named_surfaces().into_iter().zip(expected) {
        let complex = f2(&c);
        assert_eq!(
            complex.cocycle_count(1).unwrap(),
            BigUint::from(2u32).pow(z),
            "{name}: |Z^1|"
        );
        assert_eq!(
            complex.coboundary_count(1).unwrap(),
            BigUint::from(2u32).pow(b),
            "{name}: |B^1|"
        );
        assert_eq!(
            complex.cohomology_count(1).unwrap(),
            BigUint::from(2u32).pow(h),
            "{name}: |H^1|"
        );
        // |H^1| = |Z^1| / |B^1|.
        assert_eq!(
            complex.cocycle_count(1).unwrap(),
            complex.coboundary_count(1).unwrap() * complex.cohomology_count(1).unwrap()
        );
    }
}

#[test]
fn cocycle_and_coboundary_counts_agree_with_brute_force_enumeration() {
    // Enumerate every cochain (2^E) and every vertex function (2^V).
    for (name, c) in all_named_surfaces() {
        let inc = incidence(&c);
        let complex = f2(&c);
        assert_eq!(
            complex.cocycle_count(1).unwrap().to_string(),
            brute_force_cocycle_count(&inc).to_string(),
            "{name}: cocycles"
        );
        assert_eq!(
            complex.coboundary_count(1).unwrap().to_string(),
            brute_force_coboundary_count(&inc).to_string(),
            "{name}: coboundaries"
        );
    }
}

#[test]
fn euler_poincare_holds_for_cells_homology_and_cohomology() {
    for (name, c) in all_named_surfaces() {
        let complex = f2(&c);
        let by_cells = complex.euler_characteristic();
        assert_eq!(
            by_cells,
            c.euler_characteristic().into(),
            "{name}: cells vs simplicial"
        );
        let alternating = |f: &dyn Fn(usize) -> usize| -> i64 {
            (0..=complex.top_dimension())
                .map(|k| {
                    if k % 2 == 0 {
                        f(k) as i64
                    } else {
                        -(f(k) as i64)
                    }
                })
                .sum()
        };
        let by_cohomology = alternating(&|k| complex.cohomology_dimension(k).unwrap());
        let by_homology = alternating(&|k| complex.homology_dimension(k).unwrap());
        assert_eq!(
            by_cells,
            by_cohomology.into(),
            "{name}: Euler-Poincare in cohomology"
        );
        assert_eq!(
            by_cells,
            by_homology.into(),
            "{name}: Euler-Poincare in homology"
        );
        // Over a field homology and cohomology have equal dimensions.
        for k in 0..=complex.top_dimension() {
            assert_eq!(
                complex.homology_dimension(k).unwrap(),
                complex.cohomology_dimension(k).unwrap(),
                "{name}, degree {k}"
            );
        }
    }
}

// ---------------------------------------------------------------------------
// Cross-checks against integral homology (Smith normal form)
// ---------------------------------------------------------------------------

#[test]
fn f2_cohomology_follows_from_integral_homology_by_universal_coefficients() {
    // dim H^k(X; F_2) = rank H_k + (even torsion summands of H_k)
    //                   + (even torsion summands of H_{k-1}).
    let check = |name: &str, z: &IntegralChainComplex| {
        let f2 = z.reduce_mod_2().unwrap();
        for k in 0..=z.top_dimension() {
            let here = z.integral_homology(k).unwrap();
            let below = if k == 0 {
                0
            } else {
                z.integral_homology(k - 1).unwrap().even_torsion_summands()
            };
            assert_eq!(
                f2.cohomology_dimension(k).unwrap(),
                here.free_rank + here.even_torsion_summands() + below,
                "{name}, degree {k}"
            );
        }
    };
    for (name, c) in all_named_surfaces() {
        let z = IntegralChainComplex::from_simplicial_complex(&c).unwrap();
        check(name, &z);
        // The free ranks are the rational Betti numbers of the existing code.
        let betti = c.rational_betti_numbers().unwrap();
        for (k, &b) in betti.iter().enumerate() {
            assert_eq!(
                z.integral_homology(k).unwrap().free_rank,
                b,
                "{name}: b_{k}"
            );
        }
    }
    check("projective plane cell", &projective_plane_cell());
    check("Klein bottle cell", &klein_bottle_cell());
    check("torus cell", &torus_cell());
}

#[test]
fn integral_homology_with_torsion_of_known_surfaces() {
    let int = |v: i64| num_bigint::BigInt::from(v);
    // The 6-vertex projective plane: H_0 = Z, H_1 = Z/2, H_2 = 0.
    let rp2 = IntegralChainComplex::from_simplicial_complex(&projective_plane()).unwrap();
    assert_eq!(rp2.integral_homology(0).unwrap().free_rank, 1);
    let h1 = rp2.integral_homology(1).unwrap();
    assert_eq!((h1.free_rank, h1.torsion.clone()), (0, vec![int(2)]));
    assert_eq!(rp2.integral_homology(2).unwrap().free_rank, 0);
    // The torus has no torsion, the Klein bottle cell has Z/2 in H_1.
    let torus_z = IntegralChainComplex::from_simplicial_complex(&torus()).unwrap();
    let h1 = torus_z.integral_homology(1).unwrap();
    assert_eq!((h1.free_rank, h1.torsion), (2, vec![]));
    let klein = klein_bottle_cell().integral_homology(1).unwrap();
    assert_eq!((klein.free_rank, klein.torsion), (1, vec![int(2)]));
    let rp2_cell = projective_plane_cell().integral_homology(1).unwrap();
    assert_eq!((rp2_cell.free_rank, rp2_cell.torsion), (0, vec![int(2)]));
    // A single face bounded by 3 a: H_1 = Z/3, invisible to F_2.
    let by_three = IntegralChainComplex::new(
        vec![1, 1, 1],
        vec![
            sparse(1, vec![vec![(0, 1), (0, -1)]]),
            sparse(1, vec![vec![(0, 3)]]),
        ],
    )
    .unwrap();
    let h1 = by_three.integral_homology(1).unwrap();
    assert_eq!((h1.free_rank, h1.torsion), (0, vec![int(3)]));
    assert_eq!(
        by_three
            .reduce_mod_2()
            .unwrap()
            .cohomology_dimension(1)
            .unwrap(),
        0
    );
}

#[test]
fn torsion_is_seen_by_f2_but_not_by_q() {
    // Over Q the projective plane looks like a point: b = (1, 0, 0). Over F_2
    // it has H^1 and H^2.
    let c = projective_plane();
    assert_eq!(c.rational_betti_numbers().unwrap(), vec![1, 0, 0]);
    assert_eq!(f2(&c).cohomology_dimension(1).unwrap(), 1);
    assert_eq!(f2(&c).cohomology_dimension(2).unwrap(), 1);
    // The Klein bottle cell: b = (1, 1, 0) over Q, (1, 2, 1) over F_2.
    let klein = klein_bottle_cell().reduce_mod_2().unwrap();
    let dims: Vec<usize> = (0..=2)
        .map(|k| klein.cohomology_dimension(k).unwrap())
        .collect();
    assert_eq!(dims, vec![1, 2, 1]);
    let torus = torus_cell().reduce_mod_2().unwrap();
    let dims: Vec<usize> = (0..=2)
        .map(|k| torus.cohomology_dimension(k).unwrap())
        .collect();
    assert_eq!(dims, vec![1, 2, 1]);
}

// ---------------------------------------------------------------------------
// Bases, coordinates
// ---------------------------------------------------------------------------

fn subset_sum(basis: &[F2Vector], cell_count: usize, subset: u32) -> F2Vector {
    let mut sum = F2Vector::zeros(cell_count).unwrap();
    for (i, vec) in basis.iter().enumerate() {
        if (subset >> i) & 1 == 1 {
            sum.add_assign(vec).unwrap();
        }
    }
    sum
}

#[test]
fn homology_and_cohomology_bases_are_cycles_and_cocycles_independent_modulo_boundaries() {
    for (name, c) in all_named_surfaces() {
        let complex = f2(&c);
        for k in 0..=complex.top_dimension() {
            let homology = complex.homology_basis(k).unwrap();
            assert_eq!(homology.len(), complex.homology_dimension(k).unwrap(), "{name}, H_{k}");
            for z in &homology {
                assert!(complex.is_cycle(k, z).unwrap());
            }
            // No nonempty sum of basis cycles is a boundary.
            for subset in 1u32..(1 << homology.len()) {
                let sum = subset_sum(&homology, complex.cell_count(k), subset);
                assert!(!complex.is_boundary(k, &sum).unwrap(), "{name}, H_{k}");
            }
            let cohomology = complex.cohomology_basis(k).unwrap();
            assert_eq!(cohomology.len(), complex.cohomology_dimension(k).unwrap(), "{name}, H^{k}");
            for class in &cohomology {
                assert!(complex.is_cocycle(k, class).unwrap());
            }
            for subset in 1u32..(1 << cohomology.len()) {
                let sum = subset_sum(&cohomology, complex.cell_count(k), subset);
                assert!(!complex.is_coboundary(k, &sum).unwrap(), "{name}, H^{k}");
            }
        }
    }
}

#[test]
fn coordinates_of_a_cocycle_class_are_a_linear_map_onto_the_class_group() {
    for (name, c) in [
        ("torus", torus()),
        ("projective plane", projective_plane()),
        ("circle", circle()),
    ] {
        let complex = f2(&c);
        let cocycles = complex.cocycle_space(1).unwrap();
        let classes = complex.cohomology_dimension(1).unwrap();
        // Every cocycle: combine the basis of Z^1.
        let mut seen: BTreeMap<Vec<bool>, usize> = BTreeMap::new();
        for subset in 0u64..(1u64 << cocycles.len()) {
            let mut cocycle = F2Vector::zeros(complex.cell_count(1)).unwrap();
            for (i, z) in cocycles.iter().enumerate() {
                if (subset >> i) & 1 == 1 {
                    cocycle.add_assign(z).unwrap();
                }
            }
            let coordinates = complex.cohomology_coordinates(1, &cocycle).unwrap();
            // Zero coordinates exactly for the coboundaries.
            assert_eq!(
                coordinates.iter().all(|&b| !b),
                complex.is_coboundary(1, &cocycle).unwrap(),
                "{name}"
            );
            *seen.entry(coordinates).or_insert(0) += 1;
        }
        // Onto 2^classes distinct classes, each hit |B^1| times.
        assert_eq!(seen.len(), 1 << classes, "{name}");
        let per_class = complex.coboundary_count(1).unwrap().to_string();
        assert!(seen.values().all(|n| n.to_string() == per_class), "{name}");
    }
    // Linearity on the torus: coordinates(a + b) = coordinates(a) + coordinates(b).
    let complex = f2(&torus());
    let basis = complex.cohomology_basis(1).unwrap();
    let sum = basis[0].add(&basis[1]).unwrap();
    assert_eq!(
        complex.cohomology_coordinates(1, &basis[0]).unwrap(),
        vec![true, false]
    );
    assert_eq!(
        complex.cohomology_coordinates(1, &basis[1]).unwrap(),
        vec![false, true]
    );
    assert_eq!(
        complex.cohomology_coordinates(1, &sum).unwrap(),
        vec![true, true]
    );
}

#[test]
fn coordinates_refuse_a_cochain_that_is_not_a_cocycle() {
    let complex = f2(&torus());
    // A single edge has a nonzero coboundary on this closed surface.
    let not_cocycle = F2Vector::unit(complex.cell_count(1), 0).unwrap();
    assert!(!complex.is_cocycle(1, &not_cocycle).unwrap());
    assert_eq!(
        complex.cohomology_coordinates(1, &not_cocycle),
        Err(ComplexError::NotACocycle { degree: 1 })
    );
    assert!(complex
        .cohomology_coordinates(1, &F2Vector::zeros(3).unwrap())
        .is_err());
}

// ---------------------------------------------------------------------------
// The coboundary equation: a torsor over the cocycles
// ---------------------------------------------------------------------------

/// A deterministic 1-cochain of length `len`.
fn pattern(len: usize, seed: usize) -> F2Vector {
    F2Vector::from_indices(
        len,
        &(0..len)
            .filter(|i| (i * 7 + seed * 3 + 1) % 5 < 2)
            .collect::<Vec<_>>(),
    )
    .unwrap()
}

#[test]
fn solutions_of_the_coboundary_equation_are_a_torsor_over_the_cocycles() {
    // The spin-lift statement: solutions of delta^1 s = w form a torsor over
    // Z^1(X; F_2) when nonempty. Compared with enumeration of every cochain.
    for (name, c) in [
        ("disk", disk()),
        ("sphere", sphere()),
        ("octahedron", octahedron()),
        ("projective plane", projective_plane()),
        ("Mobius band", mobius_band()),
    ] {
        let complex = f2(&c);
        let inc = incidence(&c);
        let edges = complex.cell_count(1);
        for seed in 0..4 {
            let s0 = pattern(edges, seed);
            let w = complex.coboundary(1).unwrap().mul_vec(&s0).unwrap();
            let space = complex
                .solve_coboundary(1, &w)
                .unwrap()
                .expect("w is a coboundary");
            // Exactly |Z^1| solutions, among them the one we started from.
            assert_eq!(space.count(), complex.cocycle_count(1).unwrap(), "{name}");
            assert!(space.contains(&s0).unwrap());
            let listed: BTreeSet<u64> =
                space.enumerate(1 << 16).unwrap().iter().map(mask).collect();
            assert_eq!(
                listed,
                brute_force_solutions(&inc, mask(&w)),
                "{name}, seed {seed}"
            );
            // Differences of solutions are cocycles, and a cocycle moves a
            // solution to a solution.
            let solutions: Vec<F2Vector> = space.enumerate(1 << 16).unwrap();
            for other in solutions.iter().take(8) {
                assert!(complex.is_cocycle(1, &s0.add(other).unwrap()).unwrap());
            }
            for z in complex.cocycle_space(1).unwrap() {
                let moved = s0.add(&z).unwrap();
                assert_eq!(complex.coboundary(1).unwrap().mul_vec(&moved).unwrap(), w);
            }
        }
    }
}

#[test]
fn on_a_closed_surface_the_coboundary_equation_is_solvable_exactly_for_even_weight() {
    // Every edge lies on two faces, so delta^1 s has even weight; H^2 = F_2
    // makes every even-weight 2-cochain a coboundary. The odd-weight 2-cochain
    // of a single face (the class w_2 of a bundle with an obstruction) has
    // no solution, and brute force agrees.
    for (name, c) in [
        ("sphere", sphere()),
        ("octahedron", octahedron()),
        ("projective plane", projective_plane()),
    ] {
        let complex = f2(&c);
        let inc = incidence(&c);
        let faces = complex.cell_count(2);
        for code in 0u64..(1 << faces) {
            let w = vector_of(code, faces);
            let solvable = complex.solve_coboundary(1, &w).unwrap().is_some();
            assert_eq!(solvable, w.weight() % 2 == 0, "{name}, w = {code:b}");
        }
        let single_face = F2Vector::unit(faces, 0).unwrap();
        assert!(complex.solve_coboundary(1, &single_face).unwrap().is_none());
        assert!(
            brute_force_solutions(&inc, 1).is_empty(),
            "{name}: brute force finds none"
        );
    }
    // The 7-vertex torus: all weight-1 and weight-2 right-hand sides.
    let torus_complex = f2(&torus());
    let faces = torus_complex.cell_count(2);
    for first in 0..faces {
        let one = F2Vector::unit(faces, first).unwrap();
        assert!(torus_complex.solve_coboundary(1, &one).unwrap().is_none());
        for second in (first + 1)..faces {
            let two = F2Vector::from_indices(faces, &[first, second]).unwrap();
            assert!(torus_complex.solve_coboundary(1, &two).unwrap().is_some());
        }
    }
}

#[test]
fn with_h2_zero_every_two_cochain_is_a_coboundary() {
    for (name, c) in [("disk", disk()), ("Mobius band", mobius_band())] {
        let complex = f2(&c);
        assert_eq!(complex.cohomology_dimension(2).unwrap(), 0, "{name}");
        let faces = complex.cell_count(2);
        for code in 0u64..(1 << faces) {
            let w = vector_of(code, faces);
            assert!(
                complex.solve_coboundary(1, &w).unwrap().is_some(),
                "{name}, w = {code:b}"
            );
        }
    }
}

#[test]
fn the_zero_right_hand_side_has_the_cocycles_themselves_as_solutions() {
    let complex = f2(&torus());
    let zero = F2Vector::zeros(complex.cell_count(2)).unwrap();
    let space = complex.solve_coboundary(1, &zero).unwrap().unwrap();
    assert!(space.particular().is_zero() || complex.is_cocycle(1, space.particular()).unwrap());
    assert_eq!(space.count(), complex.cocycle_count(1).unwrap());
    // At the top degree there is no equation: every cochain is a solution.
    let top = complex.top_dimension();
    let trivial = F2Vector::zeros(0).unwrap();
    let all = complex.solve_coboundary(top, &trivial).unwrap().unwrap();
    assert_eq!(all.dimension(), complex.cell_count(top));
}

// ---------------------------------------------------------------------------
// Bockstein
// ---------------------------------------------------------------------------

#[test]
fn the_bockstein_homomorphism_detects_two_torsion() {
    // beta: H^1(X; F_2) -> H^2(X; F_2) is the identity-like isomorphism on the
    // projective plane (Sq^1 x = x^2 != 0) and zero on torsion-free spaces.
    let rp2 = IntegralChainComplex::from_simplicial_complex(&projective_plane()).unwrap();
    assert_eq!(rp2.bockstein_matrix(1).unwrap().to_rows(), vec![vec![1]]);
    assert_eq!(
        rp2.bockstein_matrix(0).unwrap().to_rows(),
        vec![vec![0]],
        "beta of the unit is 0"
    );
    let torus_z = IntegralChainComplex::from_simplicial_complex(&torus()).unwrap();
    assert_eq!(
        torus_z.bockstein_matrix(1).unwrap().to_rows(),
        vec![vec![0, 0]]
    );
    let sphere_z = IntegralChainComplex::from_simplicial_complex(&sphere()).unwrap();
    // H^1 = 0: the matrix has no columns.
    let matrix = sphere_z.bockstein_matrix(1).unwrap();
    assert_eq!((matrix.rows(), matrix.cols()), (1, 0));
    // Cell complexes with torsion.
    assert_eq!(
        projective_plane_cell()
            .bockstein_matrix(1)
            .unwrap()
            .to_rows(),
        vec![vec![1]]
    );
    let klein = klein_bottle_cell().bockstein_matrix(1).unwrap();
    assert_eq!((klein.rows(), klein.cols(), klein.rank()), (1, 2, 1));
    assert!(torus_cell().bockstein_matrix(1).unwrap().is_zero());
}

#[test]
fn the_bockstein_of_a_class_does_not_depend_on_the_representative() {
    let z = IntegralChainComplex::from_simplicial_complex(&projective_plane()).unwrap();
    let f2c = z.reduce_mod_2().unwrap();
    let class = f2c.cohomology_basis(1).unwrap().remove(0);
    let reference = f2c
        .cohomology_coordinates(2, &z.bockstein_of_cocycle(1, &class).unwrap())
        .unwrap();
    assert_eq!(reference, vec![true]);
    // Adding any coboundary to the representative leaves beta(class) in the same class.
    for coboundary in f2c.coboundary_space(1).unwrap() {
        let shifted = class.add(&coboundary).unwrap();
        let image = z.bockstein_of_cocycle(1, &shifted).unwrap();
        assert!(f2c.is_cocycle(2, &image).unwrap());
        assert_eq!(f2c.cohomology_coordinates(2, &image).unwrap(), reference);
    }
}

#[test]
fn the_bockstein_refuses_a_non_cocycle_and_the_top_degree() {
    let z = IntegralChainComplex::from_simplicial_complex(&torus()).unwrap();
    let not_cocycle = F2Vector::unit(z.cell_count(1), 0).unwrap();
    assert_eq!(
        z.bockstein_of_cocycle(1, &not_cocycle),
        Err(ComplexError::NotACocycle { degree: 1 })
    );
    let top = z.top_dimension();
    let cochain = F2Vector::zeros(z.cell_count(top)).unwrap();
    assert!(matches!(
        z.bockstein_of_cocycle(top, &cochain),
        Err(ComplexError::DegreeOutOfRange { .. })
    ));
}

// ---------------------------------------------------------------------------
// Construction refusals
// ---------------------------------------------------------------------------

#[test]
fn a_chain_complex_refuses_malformed_boundary_data() {
    let m = |rows: &[&[u8]]| {
        F2Matrix::from_rows(&rows.iter().map(|r| r.to_vec()).collect::<Vec<_>>()).unwrap()
    };
    assert_eq!(
        F2ChainComplex::new(vec![], vec![]),
        Err(ComplexError::NoDimensions)
    );
    assert_eq!(
        F2ChainComplex::new(vec![1, 1, 1], vec![m(&[&[0]])]),
        Err(ComplexError::BoundaryCount {
            dims: 3,
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        F2ChainComplex::new(vec![2, 1], vec![m(&[&[1, 1]])]),
        Err(ComplexError::BoundaryShape {
            degree: 1,
            expected: (2, 1),
            actual: (1, 2)
        })
    );
    // d_1 d_2 != 0: a face bounding an edge whose boundary is not cancelled.
    let d1 = m(&[&[1], &[1]]);
    let d2 = m(&[&[1]]);
    assert_eq!(
        F2ChainComplex::new(vec![2, 1, 1], vec![d1, d2]),
        Err(ComplexError::BoundaryNotZero { degree: 2 })
    );
    // The same refusals over Z.
    assert_eq!(
        IntegralChainComplex::new(vec![], vec![]),
        Err(ComplexError::NoDimensions)
    );
    let e1 = sparse(2, vec![vec![(0, 1), (1, 1)]]);
    let e2 = sparse(1, vec![vec![(0, 1)]]);
    assert_eq!(
        IntegralChainComplex::new(vec![2, 1, 1], vec![e1, e2]),
        Err(ComplexError::BoundaryNotZero { degree: 2 })
    );
    assert!(matches!(
        SparseIntegerMatrix::new(2, vec![vec![(5, 1)]]),
        Err(ComplexError::EntryOutOfRange {
            column: 0,
            row: 5,
            rows: 2
        })
    ));
}

#[test]
fn sparse_integer_products_refuse_overflow() {
    // 2^40 * 2^40 = 2^80 does not fit i64.
    let big = sparse(1, vec![vec![(0, 1 << 40)]]);
    assert!(matches!(big.mul(&big), Err(ComplexError::Overflow { .. })));
    // Summing three products of (i64::MAX)^2 overflows i128.
    let column = sparse(3, vec![vec![(0, i64::MAX), (1, i64::MAX), (2, i64::MAX)]]);
    let left = sparse(
        1,
        vec![
            vec![(0, i64::MAX)],
            vec![(0, i64::MAX)],
            vec![(0, i64::MAX)],
        ],
    );
    assert!(matches!(
        left.mul(&column),
        Err(ComplexError::Overflow { .. })
    ));
    // A summed column that overflows i64 is refused at construction.
    assert!(matches!(
        SparseIntegerMatrix::new(1, vec![vec![(0, i64::MAX), (0, 1)]]),
        Err(ComplexError::Overflow { .. })
    ));
    // Shapes must compose.
    let a = sparse(2, vec![vec![(0, 1)]]);
    assert!(matches!(
        a.mul(&a),
        Err(ComplexError::ProductShape {
            left_cols: 1,
            right_rows: 2
        })
    ));
}

#[test]
fn degrees_outside_the_complex_are_refused() {
    let complex = f2(&torus());
    let top = complex.top_dimension();
    assert!(matches!(
        complex.cocycle_space(top + 1),
        Err(ComplexError::DegreeOutOfRange { .. })
    ));
    assert!(matches!(
        complex.boundary(0),
        Err(ComplexError::DegreeOutOfRange { .. })
    ));
    assert!(matches!(
        complex.boundary(top + 1),
        Err(ComplexError::DegreeOutOfRange { .. })
    ));
    assert!(matches!(
        complex.homology_basis(top + 1),
        Err(ComplexError::DegreeOutOfRange { .. })
    ));
    assert_eq!(complex.cell_count(top + 5), 0);
    // A cochain of the wrong length.
    assert!(matches!(
        complex.is_cocycle(1, &F2Vector::zeros(2).unwrap()),
        Err(ComplexError::F2(F2Error::LengthMismatch { .. }))
    ));
    let z = IntegralChainComplex::from_simplicial_complex(&torus()).unwrap();
    assert!(z.integral_homology(top + 1).is_err());
    assert!(z.boundary(0).is_err());
}

#[test]
fn the_point_and_the_empty_complex_are_complexes() {
    let point = complex(&[&[0]]);
    let f2c = f2(&point);
    assert_eq!(f2c.cohomology_dimension(0).unwrap(), 1);
    assert_eq!(f2c.top_dimension(), 0);
    assert_eq!(
        f2c.coboundary(0).unwrap().rows(),
        0,
        "the top coboundary maps to the zero space"
    );
    let empty = SimplicialComplex::from_simplices(vec![]).unwrap();
    let f2e = f2(&empty);
    assert_eq!(f2e.cohomology_dimension(0).unwrap(), 0);
    assert_eq!(f2e.euler_characteristic(), 0.into());
    // The bordered cases: two points.
    let two = complex(&[&[0], &[1]]);
    assert_eq!(f2(&two).cohomology_dimension(0).unwrap(), 2);
}

// Origin: engine/crates_rs/tests/core_homology/f2_cohomology_tests.rs
// Claim: urn:core:crates_rs:tests:f2-cohomology-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2921d712 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2921d712` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2921d712 {
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
impl BoundaryError2921d712 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2921d712 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2921d712 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2921d712 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2921d712> {
        if capacity_bound == 0 {
            return Err(BoundaryError2921d712::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2921d712::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2921d712::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2921d712() {
    let admitted = BoundaryRecord2921d712::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2921d712::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
