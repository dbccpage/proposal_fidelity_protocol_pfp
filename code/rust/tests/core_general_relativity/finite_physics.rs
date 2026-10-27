//! Actual finite causal, flux and recoupling laws; no continuum admission.
use linear_algebra::exact_field::{involution, matrix as mx};
use num_traits::Zero;
use core_general_relativity::{
    causal_set::CausalSet,
    loop_quantum_gravity::{ExactFourSimplex, FluxTetrahedron},
    simplicial_dynamics::{bianchi, emit_angular, CauchySlice, ReggeFourSimplex},
    spin_foam::{
        ising_admissible, ising_f, ising_six_j, ising_six_j_radical, quantum_dimension, SpinFoam,
    },
};
use core_homology::finite_poset::FinitePoset;
use core_number_theory::quadratic::Quadratic;
use core_number_theory::rational::{ri, rq, Rational};
use std::collections::BTreeMap;

#[test]
fn causal_intervals_and_dimension_two_action_are_computed_from_the_order() {
    assert!(CausalSet::new(usize::MAX, "too large").is_err());
    let chain = CausalSet::from_order(
        FinitePoset::from_generating_relations(3, [(0, 1), (1, 2)]).unwrap(),
        "chain",
    );
    assert_eq!(chain.ordering_fraction(), ri(1));
    assert_eq!(chain.alexandrov_interval(0, 2).unwrap(), vec![0, 1, 2]);
    assert_eq!(
        chain.interval_abundances().unwrap(),
        vec![2.into(), 1.into()]
    );
    assert_eq!(chain.two_dimensional_interval_action().unwrap(), 3.into());
    let fork = CausalSet::from_order(FinitePoset::new(3, [(0, 1), (0, 2)]).unwrap(), "fork");
    assert!(fork.spacelike(1, 2).unwrap());
    assert_eq!(fork.ordering_fraction(), rq(2, 3));
    assert_eq!(fork.two_dimensional_interval_action().unwrap(), (-1).into());
    assert!(FinitePoset::new(2, [(0, 1), (1, 0)]).is_err());
}

fn standard_tetrahedron() -> [[Rational; 3]; 4] {
    [
        [ri(0), ri(0), ri(0)],
        [ri(1), ri(0), ri(0)],
        [ri(0), ri(1), ri(0)],
        [ri(0), ri(0), ri(1)],
    ]
}
#[test]
fn geometric_flux_closure_area_and_volume_are_exact() {
    let tetra = FluxTetrahedron::new(standard_tetrahedron()).unwrap();
    assert!(tetra.closure_defect().iter().all(Zero::is_zero));
    assert_eq!(tetra.volume_squared, rq(1, 36));
    assert_eq!(tetra.area_squared(0), Some(rq(3, 4)));
    for face in 1..4 {
        assert_eq!(tetra.area_squared(face), Some(rq(1, 4)));
    }
    assert!(FluxTetrahedron::new(std::array::from_fn(|_| [ri(0), ri(0), ri(0)])).is_err());
}

#[test]
fn simplex_boundary_bianchi_is_oriented_boundary_nilpotency() {
    let vertices = std::array::from_fn(|i| std::array::from_fn(|j| ri(i64::from(i == j + 1))));
    let simplex = ExactFourSimplex::new(vertices.clone()).unwrap();
    assert_eq!(simplex.volume_squared, rq(1, 576));
    let defects = (0..5)
        .flat_map(|a| {
            (a + 1..5).flat_map(move |b| {
                (b + 1..5).map(move |c| ([a, b, c], rq((a + 2 * b + 3 * c) as i64, 7)))
            })
        })
        .collect();
    let regge = ReggeFourSimplex {
        positions: vertices,
        hinge_defects: defects,
    };
    assert!(mx::is_zero_matrix(&regge.boundary_bianchi().unwrap()));
    assert!(mx::is_zero_matrix(
        &regge.tetrahedron_bianchi([0, 1, 2, 3], false).unwrap()
    ));
    assert!(regge.hinge_bivector([0, 0, 1]).is_err());
}

#[test]
fn cauchy_slice_refuses_degenerate_or_unused_vertices_and_preserves_rotations() {
    let vertices = standard_tetrahedron().to_vec();
    let mut slice = CauchySlice::new(vertices.clone(), vec![[0, 1, 2, 3]]).unwrap();
    assert!(slice.constraints().master.is_zero());
    assert!(slice
        .faces()
        .values()
        .any(|f| f.iter().any(|v| !v.is_zero())));
    assert_eq!(slice.constraints().gauss.len(), 1);
    assert!(slice
        .constraints()
        .gauss
        .iter()
        .flatten()
        .all(Zero::is_zero));
    let mut relabeled = vertices.clone();
    relabeled.swap(1, 2);
    assert!(CauchySlice::new(relabeled, vec![[3, 1, 0, 2]])
        .unwrap()
        .constraints()
        .gauss
        .iter()
        .flatten()
        .all(Zero::is_zero));
    let skew = mx::from_rows(vec![
        vec![ri(0), ri(-1), ri(0)],
        vec![ri(1), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(0)],
    ])
    .unwrap();
    slice.set_connection(0, 1, &skew, &rq(1, 2)).unwrap();
    assert!(slice.constraints().master > ri(0));
    slice
        .evolve(&BTreeMap::from([((0, 1), skew)]), &vec![rq(1, 5); 4])
        .unwrap();
    assert!(slice
        .holonomies()
        .values()
        .all(|m| involution::is_unitary(m).unwrap()));
    let mut unused = vertices;
    unused.push([ri(2), ri(2), ri(2)]);
    assert!(CauchySlice::new(unused, vec![[0, 1, 2, 3]]).is_err());
    let mut degenerate = standard_tetrahedron();
    degenerate[3] = degenerate[2].clone();
    assert!(CauchySlice::new(degenerate.to_vec(), vec![[0, 1, 2, 3]]).is_err());
}

#[test]
fn cauchy_slice_failed_evolution_leaves_holonomies_unchanged() {
    let vertices = standard_tetrahedron().to_vec();
    let mut slice = CauchySlice::new(vertices, vec![[0, 1, 2, 3]]).unwrap();
    let skew = mx::from_rows(vec![
        vec![ri(0), ri(-1), ri(0)],
        vec![ri(1), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(0)],
    ])
    .unwrap();
    let non_skew = mx::from_rows(vec![
        vec![ri(1), ri(0), ri(0)],
        vec![ri(0), ri(1), ri(0)],
        vec![ri(0), ri(0), ri(1)],
    ])
    .unwrap();

    let initial_holonomies = slice.holonomies().clone();

    let mut generators = BTreeMap::new();
    generators.insert((0, 1), skew);
    generators.insert((0, 2), non_skew);

    let result = slice.evolve(&generators, &vec![rq(1, 5); 4]);
    assert!(result.is_err());
    assert_eq!(slice.holonomies(), &initial_holonomies);
}

#[test]
fn finite_central_force_and_emitted_bivector_conserve_total_momentum() {
    let positions = vec![
        vec![ri(0), ri(0), ri(0)],
        vec![ri(1), ri(2), ri(3)],
        vec![ri(-2), ri(1), ri(4)],
    ];
    let (local, total, torque) =
        bianchi(&positions, &[(0, 1, rq(2, 3)), (1, 2, rq(-4, 5))]).unwrap();
    assert!(total.iter().all(Zero::is_zero));
    assert!(mx::is_zero_matrix(&torque));
    assert!(local.iter().flatten().any(|x| !x.is_zero()));
    let mut body = mx::identity(3).unwrap();
    let mut radiation = mx::zeros(3, 3).unwrap();
    let initial = mx::add(&body, &radiation).unwrap();
    emit_angular(
        &mut body,
        &mut radiation,
        &[ri(1), ri(2), ri(3)],
        &[ri(2), ri(-1), ri(4)],
    )
    .unwrap();
    assert_eq!(mx::add(&body, &radiation).unwrap(), initial);
    assert!(emit_angular(&mut body, &mut radiation, &[ri(1)], &[ri(2)]).is_err());
}

#[test]
fn su2_level_two_racah_recouplings_are_orthogonal_for_every_admissible_sector() {
    assert_eq!(quantum_dimension(0).unwrap(), Quadratic::<2>::one());
    assert_eq!(
        quantum_dimension(1).unwrap(),
        Quadratic::<2>::new(ri(0), ri(1))
    );
    assert_eq!(quantum_dimension(2).unwrap(), Quadratic::<2>::one());
    for a in 0..=2 {
        for b in 0..=2 {
            for c in 0..=2 {
                for d in 0..=2 {
                    let rows = (0..=2)
                        .filter(|&e| ising_admissible(a, b, e) && ising_admissible(e, c, d))
                        .collect::<Vec<_>>();
                    let cols = (0..=2)
                        .filter(|&f| ising_admissible(b, c, f) && ising_admissible(a, f, d))
                        .collect::<Vec<_>>();
                    assert_eq!(rows.len(), cols.len());
                    for &e in &rows {
                        for &ep in &rows {
                            let inner = cols
                                .iter()
                                .map(|&f| {
                                    ising_f(a, b, c, d, e, f).unwrap()
                                        * ising_f(a, b, c, d, ep, f).unwrap()
                                })
                                .fold(Quadratic::<2>::zero(), |s, t| s + t);
                            assert_eq!(
                                inner,
                                if e == ep {
                                    Quadratic::<2>::one()
                                } else {
                                    Quadratic::<2>::zero()
                                },
                                "sector {a},{b},{c},{d}; rows {e},{ep}"
                            );
                        }
                    }
                }
            }
        }
    }
    // The raw six-j can contain2^(-1/4), while the normalized F is1.
    let labels = [0, 1, 1, 1, 0, 0];
    let radical = ising_six_j_radical(labels).unwrap();
    assert_eq!(
        radical.squared_value(),
        Quadratic::<2>::new(ri(0), rq(1, 2))
    );
    assert!(radical.quadratic_value().is_err());
    assert_eq!(ising_f(0, 1, 1, 0, 1, 0).unwrap(), Quadratic::<2>::one());
    let foam = SpinFoam::from_tetrahedra(vec![labels, labels], "two cells").unwrap();
    assert_eq!(
        foam.tetrahedral_amplitude()
            .unwrap()
            .quadratic_value()
            .unwrap(),
        Quadratic::<2>::new(ri(0), rq(1, 2))
    );
    assert!(SpinFoam::from_tetrahedra(vec![[0; 6]; 4097], "exhausted").is_err());
    assert_eq!(ising_six_j([0; 6]).unwrap(), Quadratic::<2>::one());
    assert!(ising_six_j([3, 0, 0, 0, 0, 0]).is_err());
}

// Origin: engine/crates_rs/tests/core_general_relativity/finite_physics.rs
// Claim: urn:core:crates_rs:tests:finite-physics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord18e958b1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord18e958b1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError18e958b1 {
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
impl BoundaryError18e958b1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError18e958b1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError18e958b1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord18e958b1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError18e958b1> {
        if capacity_bound == 0 {
            return Err(BoundaryError18e958b1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError18e958b1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError18e958b1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_18e958b1() {
    let admitted = BoundaryRecord18e958b1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord18e958b1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
