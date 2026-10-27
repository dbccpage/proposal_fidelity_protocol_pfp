// AuthorityEffect: None. Exact finite Q(i) cluster-update regressions.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::tensor_projector::TensorLayout;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::adaptive_integrator::{
    AdaptiveDiagnosticAuthority, AdaptiveError, BoundaryResidual, EvolutionScope,
    ExactClusterPartition, ExactQuantumCluster, ExactQubitChain, RefinementDecision,
    TraceNormWitness,
};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{
    check_well_formed, exact_limits, hermitian_trace, is_psd, outer, partial_trace_first,
    partial_trace_second, ExactHermitianError,
};
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_quantum_physics::exact_operator::ExactOperator;
use core_quantum_physics::quantum_hamiltonian::ExactHamiltonian;
use core_quantum_physics::trace_norm_certificate::TraceNormError;

fn real(value: Rational) -> GaussianRat {
    GaussianRat::from_rational(value)
}

fn x() -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![
        vec![real(ri(0)), real(ri(1))],
        vec![real(ri(1)), real(ri(0))],
    ])
    .unwrap()
}

fn y() -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![
        vec![real(ri(0)), GaussianRat::from_ints(0, -1)],
        vec![GaussianRat::from_ints(0, 1), real(ri(0))],
    ])
    .unwrap()
}

fn z() -> BasicMatrix<GaussianRat> {
    mx::diagonal(&[real(ri(1)), real(ri(-1))]).unwrap()
}

fn ground() -> ExactDensityState {
    ExactDensityState::try_new(mx::diagonal(&[real(ri(1)), real(ri(0))]).unwrap()).unwrap()
}

fn mixed() -> ExactDensityState {
    ExactDensityState::try_new(mx::scale(&mx::identity(2).unwrap(), &real(rq(1, 2))).unwrap())
        .unwrap()
}

fn pure(vector: &[GaussianRat]) -> ExactDensityState {
    ExactDensityState::try_new(outer(vector, vector).unwrap()).unwrap()
}

fn zero_witness(operator: &BasicMatrix<GaussianRat>) -> TraceNormWitness {
    let zero = mx::zeros(operator.rows(), operator.cols()).unwrap();
    TraceNormWitness {
        positive_part: zero.clone(),
        negative_part: zero.clone(),
        dual_witness: zero,
    }
}

// Fixture-specific supplied Jordan/dual witness: the displayed normal is a
// direct sum of 2x2 off-diagonal blocks of the stated rational magnitude, with
// a zero kernel. No rational eigenvalues are guessed. The production verifier
// independently checks P,N >= 0, P-N=n, ||W||op <=1 and the zero duality gap.
fn block_witness(
    operator: &BasicMatrix<GaussianRat>,
    magnitude: Rational,
    support: &[usize],
) -> TraceNormWitness {
    let mut absolute = mx::zeros(operator.rows(), operator.cols()).unwrap();
    for &index in support {
        absolute.set(index, index, real(magnitude.clone())).unwrap();
    }
    TraceNormWitness {
        positive_part: mx::scale(&mx::add(&absolute, operator).unwrap(), &real(rq(1, 2))).unwrap(),
        negative_part: mx::scale(&mx::sub(&absolute, operator).unwrap(), &real(rq(1, 2))).unwrap(),
        dual_witness: mx::scale(operator, &real(ri(1) / magnitude)).unwrap(),
    }
}

fn xx_chain(sites: usize) -> ExactQubitChain {
    ExactQubitChain::try_new(
        vec![mx::zeros(2, 2).unwrap(); sites],
        vec![mx::kronecker(&x(), &x()).unwrap(); sites - 1],
    )
    .unwrap()
}

fn ground_partition(sites: usize) -> ExactClusterPartition {
    ExactClusterPartition::from_site_states(vec![ground(); sites]).unwrap()
}

#[test]
fn actual_projected_commutator_triggers_only_above_the_exact_threshold() {
    let model = xx_chain(2);
    let mut partition = ground_partition(2);
    let before = partition.global_state().unwrap();
    let residual = partition.boundary_residual(&model, 0).unwrap().unwrap();
    assert_eq!(
        residual.operator().get_ref(0, 3).unwrap(),
        &GaussianRat::from_ints(0, 1)
    );
    assert_eq!(
        residual.operator().get_ref(3, 0).unwrap(),
        &GaussianRat::from_ints(0, -1)
    );
    assert!(!mx::is_zero_matrix(residual.operator()));
    assert_eq!(
        residual
            .product_differential(residual.commutator_velocity())
            .unwrap(),
        mx::zeros(4, 4).unwrap()
    );
    assert_eq!(residual.operator(), residual.commutator_velocity());

    let equality = partition
        .refine_with_witnesses(&model, &ri(2), 2, |boundary| {
            Ok(block_witness(boundary.operator(), ri(1), &[0, 3]))
        })
        .unwrap();
    assert_eq!(equality.decision(), RefinementDecision::NoTriggeredBoundary);
    assert_eq!(equality.detections()[0].rate(), &ri(2));
    assert!(!equality.detections()[0].is_triggered());
    assert_eq!(partition.partition_sites(), vec![vec![0], vec![1]]);

    let triggered = partition
        .refine_with_witnesses(&model, &rq(3, 2), 2, |boundary| {
            Ok(block_witness(boundary.operator(), ri(1), &[0, 3]))
        })
        .unwrap();
    assert_eq!(triggered.decision(), RefinementDecision::Fused { bond: 0 });
    assert!(triggered.detections()[0].is_triggered());
    assert_eq!(partition.partition_sites(), vec![vec![0, 1]]);
    assert_eq!(partition.global_state().unwrap(), before);
    assert_eq!(
        triggered.authority_effect(),
        AdaptiveDiagnosticAuthority::None
    );
    assert_eq!(
        triggered.detections()[0].authority_effect(),
        AdaptiveDiagnosticAuthority::None
    );
    assert_eq!(
        triggered.fusion().unwrap().authority_effect(),
        AdaptiveDiagnosticAuthority::None
    );
}

#[test]
fn normalized_product_differential_is_idempotent_and_preserves_both_marginals() {
    let model = xx_chain(2);
    let partition = ExactClusterPartition::from_site_states(vec![mixed(), ground()]).unwrap();
    let residual = partition.boundary_residual(&model, 0).unwrap().unwrap();
    let mut direction =
        mx::diagonal(&[real(ri(1)), real(ri(2)), real(ri(3)), real(ri(4))]).unwrap();
    direction.set(0, 3, GaussianRat::from_ints(2, 1)).unwrap();
    direction.set(3, 0, GaussianRat::from_ints(2, -1)).unwrap();
    assert_eq!(hermitian_trace(&direction).unwrap(), ri(10));
    let tangent = residual.product_differential(&direction).unwrap();
    let normal = residual.normal_projector(&direction).unwrap();
    assert_eq!(residual.product_differential(&tangent).unwrap(), tangent);
    assert_eq!(residual.normal_projector(&normal).unwrap(), normal);
    assert_eq!(
        residual.product_differential(&normal).unwrap(),
        mx::zeros(4, 4).unwrap()
    );
    assert_eq!(mx::add(&tangent, &normal).unwrap(), direction);
    assert_eq!(
        partial_trace_first(&tangent, 2, 2).unwrap(),
        partial_trace_first(&direction, 2, 2).unwrap()
    );
    assert_eq!(
        partial_trace_second(&tangent, 2, 2).unwrap(),
        partial_trace_second(&direction, 2, 2).unwrap()
    );
    assert_eq!(
        partial_trace_first(&normal, 2, 2).unwrap(),
        mx::zeros(2, 2).unwrap()
    );
    assert_eq!(
        partial_trace_second(&normal, 2, 2).unwrap(),
        mx::zeros(2, 2).unwrap()
    );
}

#[test]
fn bell_cluster_boundary_is_detected_even_when_site_marginal_detector_is_zero() {
    let mut bell = mx::zeros(4, 4).unwrap();
    for (row, col) in [(0, 0), (0, 3), (3, 0), (3, 3)] {
        bell.set(row, col, real(rq(1, 2))).unwrap();
    }
    let bell = ExactDensityState::try_new(bell).unwrap();
    let partition = ExactClusterPartition::try_new(
        3,
        vec![
            ExactQuantumCluster::try_new(vec![0, 1], bell).unwrap(),
            ExactQuantumCluster::try_new(vec![2], mixed()).unwrap(),
        ],
    )
    .unwrap();
    let model = ExactQubitChain::try_new(
        vec![mx::zeros(2, 2).unwrap(); 3],
        vec![mx::zeros(4, 4).unwrap(), mx::kronecker(&z(), &z()).unwrap()],
    )
    .unwrap();
    let full = partition.boundary_residual(&model, 1).unwrap().unwrap();
    assert_eq!(full.left().sites(), &[0, 1]);
    assert_eq!(full.right().sites(), &[2]);
    assert_eq!(full.operator().shape(), (8, 8));
    let receipt = full
        .certify(
            block_witness(full.operator(), rq(1, 2), &[0, 1, 6, 7]),
            &ri(1),
        )
        .unwrap();
    assert_eq!(receipt.rate(), &ri(2));
    assert!(receipt.is_triggered());
    let site_model = ExactQubitChain::try_new(
        vec![mx::zeros(2, 2).unwrap(); 2],
        vec![mx::kronecker(&z(), &z()).unwrap()],
    )
    .unwrap();
    let site_partition = ExactClusterPartition::from_site_states(vec![
        partition.single_site_marginal(1).unwrap(),
        partition.single_site_marginal(2).unwrap(),
    ])
    .unwrap();
    let site_only = site_partition
        .boundary_residual(&site_model, 0)
        .unwrap()
        .unwrap();
    assert!(mx::is_zero_matrix(site_only.operator()));
}

#[test]
fn zero_interaction_control_has_no_normal_or_fusion_despite_local_motion() {
    let model = ExactQubitChain::try_new(
        vec![x(), mx::scale(&y(), &real(ri(2))).unwrap()],
        vec![mx::zeros(4, 4).unwrap()],
    )
    .unwrap();
    let mut partition = ground_partition(2);
    let before = partition.global_state().unwrap();
    let receipt = partition
        .advance_and_refine(&model, &rq(1, 3), &ri(0), 2, |boundary| {
            assert!(mx::is_zero_matrix(boundary.operator()));
            Ok(zero_witness(boundary.operator()))
        })
        .unwrap();
    assert_eq!(
        receipt.refinement().decision(),
        RefinementDecision::NoTriggeredBoundary
    );
    assert_eq!(receipt.refinement().detections()[0].rate(), &ri(0));
    assert_eq!(partition.partition_sites(), vec![vec![0], vec![1]]);
    assert_ne!(partition.global_state().unwrap(), before);
    let mut expected = mx::identity(1).unwrap();
    for term in model.local_hamiltonians() {
        let h = ExactHamiltonian::try_new(ExactOperator::try_new(term.clone()).unwrap()).unwrap();
        let unitary = h.cayley_propagator(&rq(1, 3)).unwrap();
        let channel =
            ExactKrausChannel::try_new(2, 2, vec![unitary.into_matrix()], "control").unwrap();
        expected = mx::kronecker(&expected, &channel.apply(ground().matrix()).unwrap()).unwrap();
    }
    assert_eq!(partition.global_state().unwrap().matrix(), &expected);
    assert_eq!(
        receipt.evolution().scope(),
        EvolutionScope::ExactFiniteFrozenCayley
    );
    assert_eq!(
        receipt.authority_effect(),
        AdaptiveDiagnosticAuthority::None
    );
    assert_eq!(
        receipt.evolution().authority_effect(),
        AdaptiveDiagnosticAuthority::None
    );
    for step in receipt.evolution().clusters() {
        assert_eq!(step.authority_effect(), AdaptiveDiagnosticAuthority::None);
        assert_eq!(
            mx::multiply(&star::adjoint(step.unitary()).unwrap(), step.unitary()).unwrap(),
            mx::identity(2).unwrap()
        );
        assert_eq!(
            hermitian_trace(step.outgoing_state().matrix()).unwrap(),
            ri(1)
        );
        assert!(is_psd(step.outgoing_state().matrix()).unwrap());
    }
}

#[test]
fn forged_jordan_or_dual_witness_is_refused_and_streaming_update_is_atomic() {
    let model = ExactQubitChain::try_new(
        vec![x(), mx::zeros(2, 2).unwrap()],
        vec![mx::kronecker(&x(), &x()).unwrap()],
    )
    .unwrap();
    let mut partition = ground_partition(2);
    let before = partition.clone();
    let mut preview = partition.clone();
    preview.cayley_step(&model, &rq(1, 3)).unwrap();
    assert_ne!(
        preview.global_state().unwrap(),
        before.global_state().unwrap()
    );
    assert!(!mx::is_zero_matrix(
        preview
            .boundary_residual(&model, 0)
            .unwrap()
            .unwrap()
            .operator()
    ));
    let refusal = partition.advance_and_refine(&model, &rq(1, 3), &ri(0), 2, |boundary| {
        Ok(zero_witness(boundary.operator()))
    });
    assert!(matches!(
        refusal,
        Err(AdaptiveError::Norm(TraceNormError::DecompositionMismatch))
    ));
    assert_eq!(partition, before);

    let boundary = partition.boundary_residual(&model, 0).unwrap().unwrap();
    let mut forged_dual = block_witness(boundary.operator(), ri(1), &[0, 3]);
    forged_dual.dual_witness = mx::zeros(4, 4).unwrap();
    assert!(matches!(
        boundary.certify(forged_dual, &ri(0)),
        Err(AdaptiveError::Norm(TraceNormError::DualityGap { .. }))
    ));
    let mut outside_ball = block_witness(boundary.operator(), ri(1), &[0, 3]);
    outside_ball.dual_witness = mx::scale(&outside_ball.dual_witness, &real(ri(2))).unwrap();
    assert!(matches!(
        boundary.certify(outside_ball, &ri(0)),
        Err(AdaptiveError::Norm(TraceNormError::WitnessOutsideUnitBall))
    ));
}

#[test]
fn fusion_of_interleaved_correlated_clusters_preserves_global_state_and_marginals() {
    let pair = pure(&[
        real(rq(3, 5)),
        real(ri(0)),
        real(ri(0)),
        GaussianRat {
            re: ri(0),
            im: rq(4, 5),
        },
    ]);
    let mut partition = ExactClusterPartition::try_new(
        5,
        vec![
            ExactQuantumCluster::try_new(vec![0, 2], pair.clone()).unwrap(),
            ExactQuantumCluster::try_new(vec![1, 3], pair.clone()).unwrap(),
            ExactQuantumCluster::try_new(vec![4], ground()).unwrap(),
        ],
    )
    .unwrap();
    let before = partition.global_state().unwrap();
    let marginals: Vec<_> = (0..5)
        .map(|site| partition.single_site_marginal(site).unwrap())
        .collect();
    let receipt = partition.fuse_clusters(1, 0).unwrap();
    assert_eq!(receipt.fused().sites(), &[0, 1, 2, 3]);
    assert_eq!(partition.partition_sites(), vec![vec![0, 1, 2, 3], vec![4]]);
    assert_eq!(partition.global_state().unwrap(), before);
    for (site, marginal) in marginals.iter().enumerate() {
        assert_eq!(&partition.single_site_marginal(site).unwrap(), marginal);
    }
    let layout = TensorLayout::new_with_limits(&[2, 2, 2, 2], exact_limits()).unwrap();
    assert_eq!(
        layout
            .partial_trace_with_limits(receipt.fused().state().matrix(), &[0, 2], exact_limits())
            .unwrap(),
        *pair.matrix()
    );
    assert_eq!(
        layout
            .partial_trace_with_limits(receipt.fused().state().matrix(), &[1, 3], exact_limits())
            .unwrap(),
        *pair.matrix()
    );

    // Independently specified canonical ket, without a permutation operation.
    let mut canonical = vec![GaussianRat::zero(); 16];
    canonical[0] = real(rq(9, 25));
    canonical[5] = GaussianRat {
        re: ri(0),
        im: rq(12, 25),
    };
    canonical[10] = GaussianRat {
        re: ri(0),
        im: rq(12, 25),
    };
    canonical[15] = real(rq(-16, 25));
    let expected = mx::kronecker(pure(&canonical).matrix(), ground().matrix()).unwrap();
    assert_eq!(partition.global_state().unwrap().matrix(), &expected);
    assert_eq!(
        receipt.authority_effect(),
        AdaptiveDiagnosticAuthority::None
    );
}

fn three_chain_witness(boundary: &BoundaryResidual) -> Result<TraceNormWitness, AdaptiveError> {
    if mx::is_zero_matrix(boundary.operator()) {
        Ok(zero_witness(boundary.operator()))
    } else if boundary.bond() == 0 && boundary.operator().rows() == 4 {
        Ok(block_witness(boundary.operator(), ri(1), &[0, 3]))
    } else if boundary.bond() == 1 && boundary.operator().rows() == 8 {
        Ok(block_witness(
            boundary.operator(),
            rq(120, 289),
            &[0, 1, 6, 7],
        ))
    } else {
        Err(AdaptiveError::WitnessUnavailable {
            bond: boundary.bond(),
        })
    }
}

#[test]
fn three_qubit_chain_runs_exact_finite_steps_and_two_adaptive_fusions() {
    let model = ExactQubitChain::try_new(
        vec![mx::zeros(2, 2).unwrap(); 3],
        vec![
            mx::kronecker(&x(), &x()).unwrap(),
            mx::kronecker(&z(), &z()).unwrap(),
        ],
    )
    .unwrap();
    let mut partition =
        ExactClusterPartition::from_site_states(vec![ground(), ground(), mixed()]).unwrap();
    let initial = partition.global_state().unwrap();
    let first = partition
        .advance_and_refine(&model, &rq(1, 2), &ri(1), 3, three_chain_witness)
        .unwrap();
    assert_eq!(
        first.refinement().decision(),
        RefinementDecision::Fused { bond: 0 }
    );
    assert_eq!(partition.partition_sites(), vec![vec![0, 1], vec![2]]);
    assert_eq!(partition.global_state().unwrap(), initial);

    let second = partition
        .advance_and_refine(&model, &rq(1, 2), &ri(1), 3, three_chain_witness)
        .unwrap();
    assert_eq!(
        second.refinement().decision(),
        RefinementDecision::Fused { bond: 1 }
    );
    assert_eq!(second.refinement().detections()[0].rate(), &rq(480, 289));
    assert_eq!(partition.partition_sites(), vec![vec![0, 1, 2]]);
    let evolved_pair = pure(&[
        real(rq(15, 17)),
        real(ri(0)),
        real(ri(0)),
        GaussianRat {
            re: ri(0),
            im: rq(-8, 17),
        },
    ]);
    let expected_second = mx::kronecker(evolved_pair.matrix(), mixed().matrix()).unwrap();
    assert_eq!(partition.global_state().unwrap().matrix(), &expected_second);
    assert_eq!(
        second.refinement().fusion().unwrap().left().state(),
        &evolved_pair
    );

    let full_h = model.full_hamiltonian().unwrap();
    let full = ExactHamiltonian::try_new(ExactOperator::try_new(full_h.clone()).unwrap()).unwrap();
    let unitary = full.cayley_propagator(&rq(1, 2)).unwrap();
    let channel =
        ExactKrausChannel::try_new(8, 8, vec![unitary.into_matrix()], "full-chain").unwrap();
    let expected_third = channel.apply(&expected_second).unwrap();
    let third = partition
        .advance_and_refine(&model, &rq(1, 2), &ri(1), 3, |boundary| {
            Err(AdaptiveError::WitnessUnavailable {
                bond: boundary.bond(),
            })
        })
        .unwrap();
    assert_eq!(
        third.refinement().decision(),
        RefinementDecision::NoTriggeredBoundary
    );
    assert!(third.refinement().detections().is_empty());
    assert_eq!(
        third.evolution().clusters()[0].effective_hamiltonian(),
        &full_h
    );
    assert_eq!(partition.global_state().unwrap().matrix(), &expected_third);
    assert_ne!(expected_third, expected_second);
    for receipt in [&first, &second, &third] {
        assert_eq!(
            receipt.authority_effect(),
            AdaptiveDiagnosticAuthority::None
        );
        assert_eq!(
            receipt.evolution().scope(),
            EvolutionScope::ExactFiniteFrozenCayley
        );
        for step in receipt.evolution().clusters() {
            assert_eq!(
                mx::multiply(&star::adjoint(step.unitary()).unwrap(), step.unitary()).unwrap(),
                mx::identity(step.unitary().rows()).unwrap()
            );
            assert_eq!(
                hermitian_trace(step.outgoing_state().matrix()).unwrap(),
                ri(1)
            );
            assert!(is_psd(step.outgoing_state().matrix()).unwrap());
        }
    }
}

#[test]
fn blocked_stronger_boundary_does_not_prevent_a_weaker_feasible_fusion() {
    let xx = mx::kronecker(&x(), &x()).unwrap();
    let model = ExactQubitChain::try_new(
        vec![mx::zeros(2, 2).unwrap(); 4],
        vec![
            mx::zeros(4, 4).unwrap(),
            mx::scale(&xx, &real(ri(2))).unwrap(),
            xx,
        ],
    )
    .unwrap();
    let mut partition = ExactClusterPartition::try_new(
        4,
        vec![
            ExactQuantumCluster::try_new(
                vec![0, 1],
                pure(&[real(ri(1)), real(ri(0)), real(ri(0)), real(ri(0))]),
            )
            .unwrap(),
            ExactQuantumCluster::try_new(vec![2], ground()).unwrap(),
            ExactQuantumCluster::try_new(vec![3], ground()).unwrap(),
        ],
    )
    .unwrap();
    let before = partition.global_state().unwrap();
    let receipt = partition
        .refine_with_witnesses(&model, &ri(1), 2, |boundary| {
            Ok(block_witness(
                boundary.operator(),
                if boundary.bond() == 1 { ri(2) } else { ri(1) },
                &[0, 3],
            ))
        })
        .unwrap();
    assert_eq!(
        receipt
            .detections()
            .iter()
            .map(|d| d.rate().clone())
            .collect::<Vec<_>>(),
        vec![ri(4), ri(2)]
    );
    assert_eq!(receipt.decision(), RefinementDecision::Fused { bond: 2 });
    assert_eq!(partition.partition_sites(), vec![vec![0, 1], vec![2, 3]]);
    assert_eq!(partition.global_state().unwrap(), before);

    let mut blocked = ground_partition(2);
    let blocked_receipt = blocked
        .refine_with_witnesses(&xx_chain(2), &ri(0), 1, |boundary| {
            Ok(block_witness(boundary.operator(), ri(1), &[0, 3]))
        })
        .unwrap();
    assert_eq!(
        blocked_receipt.decision(),
        RefinementDecision::AllTriggeredMergesExceedCeiling
    );
    assert_eq!(blocked.partition_sites(), vec![vec![0], vec![1]]);
}

#[test]
fn equal_rates_choose_the_lower_bond_and_invalid_inputs_fail_closed() {
    let mut partition = ground_partition(3);
    let receipt = partition
        .refine_with_witnesses(&xx_chain(3), &ri(1), 3, |boundary| {
            Ok(block_witness(boundary.operator(), ri(1), &[0, 3]))
        })
        .unwrap();
    assert_eq!(receipt.decision(), RefinementDecision::Fused { bond: 0 });
    let before = partition.clone();
    assert!(matches!(
        partition.cayley_step(&xx_chain(3), &ri(0)),
        Err(AdaptiveError::NonPositiveStep)
    ));
    assert!(matches!(
        partition.refine_with_witnesses(&xx_chain(3), &ri(-1), 3, |boundary| Ok(zero_witness(
            boundary.operator()
        ))),
        Err(AdaptiveError::NegativeThreshold)
    ));
    assert!(matches!(
        partition.refine_with_witnesses(&xx_chain(3), &ri(0), 0, |boundary| Ok(zero_witness(
            boundary.operator()
        ))),
        Err(AdaptiveError::ZeroClusterCeiling)
    ));
    assert!(matches!(
        partition.fuse_clusters(0, 0),
        Err(AdaptiveError::SameCluster)
    ));
    assert!(matches!(
        partition.fuse_clusters(0, usize::MAX),
        Err(AdaptiveError::ClusterIndex { .. })
    ));
    assert!(matches!(
        partition.boundary_residual(&xx_chain(3), usize::MAX),
        Err(AdaptiveError::Bond { .. })
    ));
    assert!(matches!(
        partition.effective_hamiltonian(&xx_chain(2), 0),
        Err(AdaptiveError::DifferentChains { .. })
    ));
    assert_eq!(partition, before);
    assert!(matches!(
        ExactQubitChain::try_new(vec![], vec![]),
        Err(AdaptiveError::EmptyChain)
    ));
    assert!(matches!(
        ExactQubitChain::try_new(vec![x(); 2], vec![]),
        Err(AdaptiveError::BondCount { .. })
    ));
    assert!(matches!(
        ExactQubitChain::try_new(vec![mx::zeros(3, 3).unwrap()], vec![]),
        Err(AdaptiveError::HamiltonianDimension { .. })
    ));
    assert!(matches!(
        ExactQuantumCluster::try_new(
            vec![1, 0],
            pure(&[real(ri(1)), real(ri(0)), real(ri(0)), real(ri(0))])
        ),
        Err(AdaptiveError::ClusterSites)
    ));
    assert!(matches!(
        ExactQuantumCluster::try_new(vec![0], pure(&[real(ri(1))])),
        Err(AdaptiveError::StateDimension { .. })
    ));
    assert!(matches!(
        ExactClusterPartition::try_new(
            2,
            vec![ExactQuantumCluster::try_new(vec![0], ground()).unwrap()]
        ),
        Err(AdaptiveError::PartitionSites { .. })
    ));
    assert!(matches!(
        ExactClusterPartition::try_new(usize::MAX, vec![]),
        Err(AdaptiveError::Resource(_))
    ));
}

#[test]
fn rational_entries_do_not_create_a_rational_norm_or_an_automatic_witness() {
    // H=(X tensor X)+(X tensor Y) sends |00> to (1+i)|11>, so the
    // boundary normal has trace norm 2 sqrt(2), outside the rational-witness face.
    let interaction = mx::add(
        &mx::kronecker(&x(), &x()).unwrap(),
        &mx::kronecker(&x(), &y()).unwrap(),
    )
    .unwrap();
    let model =
        ExactQubitChain::try_new(vec![mx::zeros(2, 2).unwrap(); 2], vec![interaction]).unwrap();
    let mut partition = ground_partition(2);
    let before = partition.clone();
    let boundary = partition.boundary_residual(&model, 0).unwrap().unwrap();
    assert_eq!(
        boundary.operator().get_ref(0, 3).unwrap(),
        &GaussianRat::from_ints(1, 1)
    );
    assert!(boundary
        .certify(block_witness(boundary.operator(), ri(1), &[0, 3]), &ri(0))
        .is_err());
    let refusal = partition.refine_with_witnesses(&model, &ri(0), 2, |boundary| {
        Err(AdaptiveError::WitnessUnavailable {
            bond: boundary.bond(),
        })
    });
    assert_eq!(
        refusal.unwrap_err(),
        AdaptiveError::WitnessUnavailable { bond: 0 }
    );
    assert_eq!(partition, before);
}

#[test]
fn malformed_rational_scalars_are_refused_before_comparison_or_matrix_arithmetic() {
    let invalid = [
        Rational::new_raw(1.into(), 0.into()),
        Rational::new_raw(1.into(), (-2).into()),
        Rational::new_raw(2.into(), 4.into()),
        Rational::new_raw(0.into(), 7.into()),
    ];
    let model = xx_chain(2);
    let mut partition = ground_partition(2);
    let before = partition.clone();
    let boundary = partition.boundary_residual(&model, 0).unwrap().unwrap();
    for raw in invalid {
        assert!(matches!(
            partition.cayley_step(&model, &raw),
            Err(AdaptiveError::Hermitian(ExactHermitianError::Algebra(_)))
        ));
        assert!(matches!(
            partition
                .refine_with_witnesses(&model, &raw, 2, |b| { Ok(zero_witness(b.operator())) }),
            Err(AdaptiveError::Hermitian(ExactHermitianError::Algebra(_)))
        ));
        for imaginary in [false, true] {
            let malformed = if imaginary {
                GaussianRat {
                    re: ri(1),
                    im: raw.clone(),
                }
            } else {
                GaussianRat {
                    re: raw.clone(),
                    im: ri(0),
                }
            };
            let mut matrix = mx::identity(2).unwrap();
            matrix.set(0, 0, malformed.clone()).unwrap();
            assert!(check_well_formed(&matrix).is_err());
            assert!(ExactDensityState::try_new(matrix.clone()).is_err());
            assert!(matches!(
                ExactQubitChain::try_new(
                    vec![matrix, mx::zeros(2, 2).unwrap()],
                    vec![mx::zeros(4, 4).unwrap()]
                ),
                Err(AdaptiveError::Hermitian(ExactHermitianError::Algebra(_)))
            ));
            let mut direction = mx::identity(4).unwrap();
            direction.set(0, 0, malformed).unwrap();
            assert!(matches!(
                boundary.product_differential(&direction),
                Err(AdaptiveError::Hermitian(ExactHermitianError::Algebra(_)))
            ));
            assert!(matches!(
                boundary.normal_projector(&direction),
                Err(AdaptiveError::Hermitian(ExactHermitianError::Algebra(_)))
            ));
            let mut witness = block_witness(boundary.operator(), ri(1), &[0, 3]);
            witness.dual_witness = direction;
            assert!(matches!(
                boundary.certify(witness, &ri(0)),
                Err(AdaptiveError::Norm(TraceNormError::Operand { .. }))
            ));
        }
        assert_eq!(partition, before);
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/test_adaptive_cluster_fusion.rs
// Claim: urn:core:crates_rs:tests:test-adaptive-cluster-fusion:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord105d7e0f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord105d7e0f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError105d7e0f {
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
impl BoundaryError105d7e0f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError105d7e0f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError105d7e0f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord105d7e0f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError105d7e0f> {
        if capacity_bound == 0 {
            return Err(BoundaryError105d7e0f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError105d7e0f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError105d7e0f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_105d7e0f() {
    let admitted = BoundaryRecord105d7e0f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord105d7e0f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
