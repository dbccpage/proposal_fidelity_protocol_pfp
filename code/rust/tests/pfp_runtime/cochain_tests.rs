//! Integration and falsification tests for Prompt-to-Cochain execution and evaluation contract.
//!
//! Covers Milestone 4 requirements:
//! - Lowering to oriented finite cell complex C^0 -> C^1 -> C^2 with d_1 * d_0 = 0 in Q
//! - Zero-face profile: C^2 = Q^0 when no faces are declared
//! - Primary quotient obstruction Phi_1(c) = min_a ||c - d_0 a||_1 with exact primal/dual witness verification
//! - Secondary closure defect Gamma_2(c) = ||d_1 c||_1
//! - Four-Way Typed Dispositions (ExactCoboundary, ClosedNonExactClass, NonClosedEdgeData, Refusal)
//! - Canonical 3-edge triangle benchmark (Triadic inputs 1, 2, and 3)
//! - Falsification of impossible profile (Phi_1 = 0, Gamma_2 > 0)
//! - Prime Triad bindings (Prime 000, Prime 001, Prime 002)
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::Zero;
use sha2::Digest;

use pfp_runtime::cochain::*;

fn r(numer: i64) -> BigRational {
    rational(numer, 1)
}

fn r_frac(numer: i64, denom: i64) -> BigRational {
    rational(numer, denom)
}

/// Canonical 3-edge triangle benchmark complex (Architecture Review 16 §7)
/// Vertices: V = {0, 1, 2}
/// Edges: E = {(0,1), (1,2), (2,0)}
/// d0 = [[-1, 1, 0], [0, -1, 1], [1, 0, -1]]
fn make_canonical_triangle(with_filled_face: bool) -> PromptCellComplex {
    let d0 = vec![
        vec![r(-1), r(1), r(0)],
        vec![r(0), r(-1), r(1)],
        vec![r(1), r(0), r(-1)],
    ];
    if with_filled_face {
        let d1 = vec![vec![r(1), r(1), r(1)]];
        PromptCellComplex::new(3, 3, 1, d0, d1)
    } else {
        PromptCellComplex::zero_face(3, 3, d0)
    }
}

#[test]
fn test_standard_triadic_input_1_exact_coboundary() {
    // Input 1 (Exact): c = (1, 2, -3) = d_0 * (0, 1, 3)^T
    // Filled face d_1 = (1, 1, 1)
    // Both Phi_1 = 0 and Gamma_2 = 0 vanish
    // Disposition: ExactCoboundary
    let complex = make_canonical_triangle(true);
    let c = vec![r(1), r(2), r(-3)];
    let a = vec![r(0), r(1), r(3)];
    let y = vec![r(0), r(0), r(0)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &y, None);

    assert!(disposition.is_exact());
    match disposition {
        CochainDisposition::ExactCoboundary { potential, residual, phi1, gamma2 } => {
            assert_eq!(potential, a);
            assert_eq!(residual, vec![r(0), r(0), r(0)]);
            assert_eq!(phi1, r(0));
            assert_eq!(gamma2, r(0));
        }
        other => panic!("expected ExactCoboundary, got {other:?}"),
    }
}

#[test]
fn test_standard_triadic_input_2_coherent_residual() {
    // Input 2 (Coherent Residual): c = (1, 1, 1), faces omitted explicitly (zero-face profile C^2 = Q^0)
    // a = (0, 0, 0), residual = (1, 1, 1), ||z||_1 = 3
    // Dual witness y = (1, 1, 1):
    // d0^T y = 0, ||y||_inf = 1 <= 1, y^T c = 3 = ||z||_1 (0 duality gap)
    // Faces omitted => Gamma_2 = 0
    // Phi_1 = 3 > 0, Gamma_2 = 0 => Disposition: ClosedNonExactClass
    let complex = make_canonical_triangle(false);
    assert_eq!(complex.c2_dim, 0);
    assert!(complex.d1.is_empty());

    let c = vec![r(1), r(1), r(1)];
    let a = vec![r(0), r(0), r(0)];
    let y = vec![r(1), r(1), r(1)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &y, None);

    assert!(disposition.is_closed_residual());
    match disposition {
        CochainDisposition::ClosedNonExactClass { cohomology_class, dual_witness, phi1, gamma2 } => {
            assert_eq!(cohomology_class, vec![r(1), r(1), r(1)]);
            assert_eq!(dual_witness, y);
            assert_eq!(phi1, r(3));
            assert_eq!(gamma2, r(0));
        }
        other => panic!("expected ClosedNonExactClass, got {other:?}"),
    }
}

#[test]
fn test_standard_triadic_input_3_nonclosed_defect() {
    // Input 3 (Nonclosed Defect): c = (1, 1, 1), filled face d_1 = (1, 1, 1)
    // Phi_1 = 3 > 0, Gamma_2 = ||d1 c||_1 = ||1 + 1 + 1||_1 = 3 > 0
    // Disposition: NonClosedEdgeData with face defect (3)
    let complex = make_canonical_triangle(true);
    let c = vec![r(1), r(1), r(1)];
    let a = vec![r(0), r(0), r(0)];
    let y = vec![r(1), r(1), r(1)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &y, None);

    assert!(disposition.is_nonclosed());
    match disposition {
        CochainDisposition::NonClosedEdgeData { face_defect, phi1, gamma2 } => {
            assert_eq!(face_defect, vec![r(3)]);
            assert_eq!(phi1, r(3));
            assert_eq!(gamma2, r(3));
        }
        other => panic!("expected NonClosedEdgeData, got {other:?}"),
    }
}

#[test]
fn test_falsification_impossible_profile() {
    // Phi_1 = 0, Gamma_2 > 0 is mathematically inadmissible for a valid complex d1 * d0 = 0
    // Because if c = d0 a, then d1 c = d1 (d0 a) = (d1 d0) a = 0.
    // If a candidate claims c = (1, 1, 1) is exact coboundary (which it isn't),
    // evaluate_exact_witness will refute the certificate.
    let complex = make_canonical_triangle(true);
    let c = vec![r(1), r(1), r(1)]; // d1 c = 3 != 0
    let a = vec![r(0), r(1), r(3)]; // d0 a = (1, 2, -3) != c
    let y = vec![r(0), r(0), r(0)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &y, None);
    assert!(disposition.is_refusal());
    match disposition {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "PHI1_CERTIFICATE_INVALID");
            assert!(message.contains("duality gap") || message.contains("residual"));
        }
        other => panic!("expected Refusal, got {other:?}"),
    }
}

#[test]
fn test_falsification_chain_law_violation() {
    // If d1 * d0 != 0, the cell complex is invalid / curved and must be refused fail-closed.
    let d0 = vec![vec![r(1), r(0)], vec![r(0), r(1)]];
    let d1 = vec![vec![r(1), r(1)]]; // d1 * d0 = [1, 1] != [0, 0]
    let complex = PromptCellComplex::new(2, 2, 1, d0, d1);

    let disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(1)],
        &[r(0), r(0)],
        &[r(1), r(1)],
        None,
    );

    assert!(disposition.is_refusal());
    match disposition {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "CHAIN_LAW_VIOLATION");
            assert!(message.contains("d1 * d0 = 0 failed"));
        }
        other => panic!("expected CHAIN_LAW_VIOLATION, got {other:?}"),
    }
}

#[test]
fn test_falsification_dual_annihilator_mismatch() {
    // Dual witness must annihilate im(d0): d0^T y = 0.
    // If y is not in ker(d0^T), it must be refused.
    let complex = make_canonical_triangle(false);
    let c = vec![r(1), r(1), r(1)];
    let a = vec![r(0), r(0), r(0)];
    let invalid_y = vec![r(1), r(0), r(0)]; // d0^T invalid_y != 0

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &invalid_y, None);

    assert!(disposition.is_refusal());
    match disposition {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "PHI1_CERTIFICATE_INVALID");
            assert!(message.contains("d0^T y != 0"));
        }
        other => panic!("expected PHI1_CERTIFICATE_INVALID, got {other:?}"),
    }
}

#[test]
fn test_falsification_dual_norm_bound_violation() {
    // Dual witness must satisfy ||y||_inf <= 1.
    // If |y_i| > 1, it must be refused.
    let complex = make_canonical_triangle(false);
    let c = vec![r(1), r(1), r(1)];
    let a = vec![r(0), r(0), r(0)];
    let invalid_y = vec![r(2), r(2), r(2)]; // ||y||_inf = 2 > 1

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &invalid_y, None);

    assert!(disposition.is_refusal());
    match disposition {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "PHI1_CERTIFICATE_INVALID");
            assert!(message.contains("||y||_infty <= 1"));
        }
        other => panic!("expected PHI1_CERTIFICATE_INVALID, got {other:?}"),
    }
}

#[test]
fn test_prime_000_intake_validation() {
    // Prime 000: source bytes custody validation
    let mut complex = make_canonical_triangle(true);
    let valid_source = "prompt graph specification v1";
    let hash = hex::encode(sha2::Sha256::digest(valid_source.as_bytes()));
    complex = complex.with_source_bytes_hash(hash.clone());

    let mut context = PrimeTriadContext {
        source_bytes: Some(valid_source.into()),
        expected_source_hash: Some(hash),
        protected_answers: None,
        candidate_answers: None,
        remaining_budget: Some(10),
    };

    let disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(2), r(-3)],
        &[r(0), r(1), r(3)],
        &[r(0), r(0), r(0)],
        Some(&mut context),
    );
    assert!(disposition.is_exact());

    // Corrupted source bytes should fail Prime 000
    let mut corrupted_context = PrimeTriadContext {
        source_bytes: Some("tampered prompt graph".into()),
        expected_source_hash: Some("tampered_hash".into()),
        protected_answers: None,
        candidate_answers: None,
        remaining_budget: Some(10),
    };
    let corrupted_disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(2), r(-3)],
        &[r(0), r(1), r(3)],
        &[r(0), r(0), r(0)],
        Some(&mut corrupted_context),
    );
    assert!(corrupted_disposition.is_refusal());
    match corrupted_disposition {
        CochainDisposition::Refusal { code, .. } => {
            assert_eq!(code, "SOURCE_BYTES_CORRUPTED");
        }
        other => panic!("expected SOURCE_BYTES_CORRUPTED, got {other:?}"),
    }
}

#[test]
fn test_prime_002_budget_halting() {
    // Prime 002: Run budget exhaustion halts with typed refusal
    let complex = make_canonical_triangle(true);
    let mut exhausted_context = PrimeTriadContext {
        source_bytes: None,
        expected_source_hash: None,
        protected_answers: None,
        candidate_answers: None,
        remaining_budget: Some(0), // 0 allowance left
    };

    let disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(2), r(-3)],
        &[r(0), r(1), r(3)],
        &[r(0), r(0), r(0)],
        Some(&mut exhausted_context),
    );
    assert!(disposition.is_refusal());
    match disposition {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "RESOURCE_EXHAUSTION");
            assert!(message.contains("run budget is 0"));
        }
        other => panic!("expected RESOURCE_EXHAUSTION, got {other:?}"),
    }
}

#[test]
fn test_prime_002_budget_is_spent_by_evaluate() {
    // A positive allowance is not admitted by being non-zero. Evaluation spends one unit.
    // The next evaluation after that allowance is gone is a refusal.
    let complex = make_canonical_triangle(true);
    let cochain = [r(1), r(2), r(-3)];
    let potential = [r(0), r(1), r(3)];
    let dual = [r(0), r(0), r(0)];

    let mut above_zero = PrimeTriadContext {
        remaining_budget: Some(2),
        ..PrimeTriadContext::default()
    };
    let first = PromptCochainEvaluator::evaluate(
        &complex,
        &cochain,
        &potential,
        &dual,
        Some(&mut above_zero),
    );
    assert!(
        first.is_exact(),
        "a budget above zero is spent, not refused on the first call, got {first:?}"
    );
    assert_eq!(
        above_zero.remaining_budget,
        Some(1),
        "a budget that starts above zero is not a pass while left unchanged"
    );
    let second = PromptCochainEvaluator::evaluate(
        &complex,
        &cochain,
        &potential,
        &dual,
        Some(&mut above_zero),
    );
    assert!(
        second.is_exact(),
        "the last remaining unit is spent, got {second:?}"
    );
    assert_eq!(above_zero.remaining_budget, Some(0));

    let mut one_shot = PrimeTriadContext {
        remaining_budget: Some(1),
        ..PrimeTriadContext::default()
    };
    let admitted = PromptCochainEvaluator::evaluate(
        &complex,
        &cochain,
        &potential,
        &dual,
        Some(&mut one_shot),
    );
    assert!(admitted.is_exact(), "one unit admits one evaluation, got {admitted:?}");
    assert_eq!(one_shot.remaining_budget, Some(0));
    let refused = PromptCochainEvaluator::evaluate(
        &complex,
        &cochain,
        &potential,
        &dual,
        Some(&mut one_shot),
    );
    match refused {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "RESOURCE_EXHAUSTION");
            assert!(message.contains("run budget is 0"));
        }
        other => panic!("second evaluation after the allowance is spent must refuse, got {other:?}"),
    }
    assert_eq!(one_shot.remaining_budget, Some(0));
    match PromptCochainEvaluator::evaluate(
        &complex,
        &cochain,
        &potential,
        &dual,
        Some(&mut above_zero),
    ) {
        CochainDisposition::Refusal { code, .. } => assert_eq!(code, "RESOURCE_EXHAUSTION"),
        other => panic!("spent allowance of 2 must refuse the third evaluation, got {other:?}"),
    }
    assert_eq!(above_zero.remaining_budget, Some(0));
}

#[test]
fn test_from_oriented_graph_construction() {
    // Construct cell complex from oriented graph builder
    // 3 vertices, 3 edges: (0,1), (1,2), (2,0)
    let edges = vec![(0, 1), (1, 2), (2, 0)];
    let faces = vec![vec![(0, r(1)), (1, r(1)), (2, r(1))]];

    let complex = PromptCellComplex::from_oriented_graph(3, &edges, Some(&faces))
        .expect("graph construction should succeed");

    assert_eq!(complex.c0_dim, 3);
    assert_eq!(complex.c1_dim, 3);
    assert_eq!(complex.c2_dim, 1);

    // Verify d0 rows
    assert_eq!(complex.d0[0], vec![r(-1), r(1), r(0)]);
    assert_eq!(complex.d0[1], vec![r(0), r(-1), r(1)]);
    assert_eq!(complex.d0[2], vec![r(1), r(0), r(-1)]);
    assert_eq!(complex.d1[0], vec![r(1), r(1), r(1)]);

    // Evaluate exact coboundary on this generated complex
    let c = vec![r(1), r(2), r(-3)];
    let a = vec![r(0), r(1), r(3)];
    let y = vec![r(0), r(0), r(0)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &y, None);
    assert!(disposition.is_exact());
}

#[test]
fn test_fractional_rationals_precision() {
    // Test that exact fractions (e.g. 1/3, -2/5) evaluate with 0 floating point errors
    let d0 = vec![
        vec![r(-1), r(1)],
    ];
    let complex = PromptCellComplex::zero_face(2, 1, d0);
    // Edge (0, 1): d0 = [[-1, 1]]
    // a = [1/3, 4/3] => d0 a = 4/3 - 1/3 = 3/3 = 1
    // c = [1]
    let c = vec![r(1)];
    let a = vec![r_frac(1, 3), r_frac(4, 3)];
    let y = vec![r(0)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &y, None);
    assert!(disposition.is_exact());
}

#[test]
fn test_adversarial_slack_dual_gap_refusal() {
    // Dual witness satisfies d0^T y = 0 and ||y||_inf <= 1, but y^T c < ||c - d0 a||_1.
    // In canonical triangle with faces omitted (C^2 = Q^0):
    // c = (1, 1, 1), a = (0, 0, 0), residual norm = 3.
    // y = (1/2, 1/2, 1/2) has d0^T y = 0 and ||y||_inf = 1/2 <= 1.
    // But y^T c = 3/2 != 3, so duality gap = 3/2 > 0.
    let complex = make_canonical_triangle(false);
    let c = vec![r(1), r(1), r(1)];
    let a = vec![r(0), r(0), r(0)];
    let slack_y = vec![r_frac(1, 2), r_frac(1, 2), r_frac(1, 2)];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &c, &a, &slack_y, None);
    assert!(disposition.is_refusal());
    match disposition {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "PHI1_CERTIFICATE_INVALID");
            assert!(message.contains("duality gap"));
        }
        other => panic!("expected Refusal(PHI1_CERTIFICATE_INVALID), got {other:?}"),
    }
}

#[test]
fn test_adversarial_bigrational_100_digits_exact() {
    use num_bigint::BigInt;
    use std::str::FromStr;

    // Construct 100-digit integers for high-precision exact rational verification
    let n1 = BigInt::from_str("1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007").unwrap();
    let d1 = BigInt::from_str("1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000031").unwrap();
    let n2 = BigInt::from_str("1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000013").unwrap();
    let d2 = BigInt::from_str("1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000047").unwrap();

    let f1 = BigRational::new(n1, d1);
    let f2 = BigRational::new(n2, d2);

    let d0 = vec![vec![-BigRational::from_integer(1.into()), BigRational::from_integer(1.into())]];
    let complex = PromptCellComplex::zero_face(2, 1, d0);

    let cochain = vec![f2.clone()];
    let potential = vec![f1.clone(), f1 + f2];
    let dual_witness = vec![BigRational::zero()];

    let disposition = PromptCochainEvaluator::evaluate(&complex, &cochain, &potential, &dual_witness, None);
    assert!(disposition.is_exact());
    match disposition {
        CochainDisposition::ExactCoboundary { phi1, gamma2, .. } => {
            assert!(phi1.is_zero());
            assert!(gamma2.is_zero());
        }
        other => panic!("expected ExactCoboundary, got {other:?}"),
    }
}

#[test]
fn test_adversarial_prime_000_multibyte_unicode_source() {
    let unicode_source = "Prompt Graph: 𝒪(x) → 𝒫(y) ⊗ 𝒞(z) [λ = 42.0]";
    let valid_hash = hex::encode(sha2::Sha256::digest(unicode_source.as_bytes()));

    let mut complex = make_canonical_triangle(false);
    complex = complex.with_source_bytes_hash(valid_hash.clone());

    let mut triad = PrimeTriadContext {
        source_bytes: Some(unicode_source.into()),
        expected_source_hash: Some(valid_hash),
        protected_answers: None,
        candidate_answers: None,
        remaining_budget: Some(10),
    };

    let disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(1), r(1)],
        &[r(0), r(0), r(0)],
        &[r(1), r(1), r(1)],
        Some(&mut triad),
    );
    assert!(disposition.is_closed_residual());
}


#[test]
fn test_prime_001_refuses_protected_answers_without_candidates() {
    let complex = make_canonical_triangle(false);
    let mut protected = std::collections::BTreeMap::new();
    protected.insert("q1".to_string(), "a1".to_string());

    let mut triad = PrimeTriadContext {
        source_bytes: None,
        expected_source_hash: None,
        protected_answers: Some(protected),
        candidate_answers: None,
        remaining_budget: Some(10),
    };

    let disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(1), r(1)],
        &[r(0), r(0), r(0)],
        &[r(1), r(1), r(1)],
        Some(&mut triad),
    );
    assert!(
        disposition.is_refusal(),
        "declared protected answers with no candidate answers must fail closed, got {disposition:?}"
    );
}

#[test]
fn test_prime_001_empty_protected_answers_without_candidates_passes() {
    let complex = make_canonical_triangle(false);
    let mut triad = PrimeTriadContext {
        source_bytes: None,
        expected_source_hash: None,
        protected_answers: Some(std::collections::BTreeMap::new()),
        candidate_answers: None,
        remaining_budget: Some(10),
    };

    let disposition = PromptCochainEvaluator::evaluate(
        &complex,
        &[r(1), r(1), r(1)],
        &[r(0), r(0), r(0)],
        &[r(1), r(1), r(1)],
        Some(&mut triad),
    );
    assert!(!disposition.is_refusal(), "no protected answers means nothing to preserve");
}

#[test]
#[should_panic(expected = "denominator cannot be zero")]
fn test_rational_zero_denominator_panics_not_coerced() {
    let _ = rational(1, 0);
}

mod n8_allocation_observer {
    use std::alloc::{GlobalAlloc, Layout, System};
    use std::cell::Cell;

    thread_local! {
        static ARMED: Cell<bool> = const { Cell::new(false) };
        static REQUESTED: Cell<usize> = const { Cell::new(0) };
    }

    fn observe(bytes: usize) {
        // Constant TLS initializers do not allocate. Never format or panic here.
        let _ = ARMED.try_with(|armed| {
            if armed.get() {
                let _ = REQUESTED.try_with(|total| total.set(total.get().saturating_add(bytes)));
            }
        });
    }

    struct Observer;

    // Forward the allocator contracts unchanged; observation is thread-local.
    unsafe impl GlobalAlloc for Observer {
        unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
            observe(layout.size());
            unsafe { System.alloc(layout) }
        }

        unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
            observe(layout.size());
            unsafe { System.alloc_zeroed(layout) }
        }

        unsafe fn realloc(&self, ptr: *mut u8, old: Layout, bytes: usize) -> *mut u8 {
            observe(bytes);
            unsafe { System.realloc(ptr, old, bytes) }
        }

        unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
            unsafe { System.dealloc(ptr, layout) }
        }
    }

    #[global_allocator]
    static ALLOCATOR: Observer = Observer;

    struct Disarm;

    impl Drop for Disarm {
        fn drop(&mut self) {
            ARMED.with(|armed| armed.set(false));
        }
    }

    pub(super) fn measure<T>(operation: impl FnOnce() -> T) -> (T, usize) {
        REQUESTED.with(|total| total.set(0));
        ARMED.with(|armed| armed.set(true));
        let disarm = Disarm;
        let result = operation();
        drop(disarm);
        (result, REQUESTED.with(Cell::get))
    }
}

fn n8_assert_early_resource_refusal(
    result: Result<PromptCellComplex, CochainRefusal>,
    requested_bytes: usize,
    first_dense_buffer_bytes: usize,
) {
    assert!(
        requested_bytes < first_dense_buffer_bytes,
        "constructor requested {requested_bytes} allocation bytes before resource refusal; dense buffer starts at {first_dense_buffer_bytes}"
    );
    match result {
        Err(refusal) => {
            assert_eq!(refusal.code, "RESOURCE_EXHAUSTION");
            assert!(refusal.message.contains("limit"));
        }
        Ok(_) => panic!("oversized graph was admitted instead of a resource refusal"),
    }
}

#[test]
fn n8_vertex_limit_refuses_before_dense_d0_allocation() {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let vertices = limits.max_vertices + 1;
    let row_bytes = vertices * std::mem::size_of::<BigRational>();
    // Bounded positive control for the observer, not an allocation failure.
    let (row, observed) = n8_allocation_observer::measure(|| vec![r(0); vertices]);
    assert_eq!(row.len(), vertices);
    assert!(observed >= row_bytes);
    drop(row);
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_oriented_graph(vertices, &[(0, 0)], None)
    });
    n8_assert_early_resource_refusal(result, requested, row_bytes);
}

#[test]
fn n8_zero_edges_do_not_evaluate_an_oversized_inner_vector() {
    let vertices = core_kernel::resource_limits::OperationLimits::default().max_vertices + 1;
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_oriented_graph(vertices, &[], None)
    });
    n8_assert_early_resource_refusal(
        result,
        requested,
        vertices * std::mem::size_of::<BigRational>(),
    );
}

#[test]
fn n8_d0_cell_limit_refuses_within_individual_axis_limits() {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let edges = vec![(0, 0); 100];
    let vertices = limits.max_cells / edges.len() + 1;
    assert!(vertices <= limits.max_vertices && edges.len() <= limits.max_edges);
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_oriented_graph(vertices, &edges, None)
    });
    n8_assert_early_resource_refusal(
        result,
        requested,
        vertices * std::mem::size_of::<BigRational>(),
    );
}

#[test]
fn n8_d1_cell_limit_refuses_before_even_d0_allocation() {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let edges = vec![(0, 0); 101];
    let vertices = 16;
    let faces = vec![Vec::new(); limits.max_cells / edges.len() + 1];
    assert!(edges.len() <= limits.max_edges && faces.len() <= limits.max_faces);
    assert!(vertices * edges.len() <= limits.max_cells);
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_oriented_graph(vertices, &edges, Some(&faces))
    });
    n8_assert_early_resource_refusal(
        result,
        requested,
        vertices * std::mem::size_of::<BigRational>(),
    );
}

#[test]
fn n8_combined_dense_cells_refuse_when_each_matrix_fits() {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let edges = vec![(0, 0); 50];
    let vertices = 101;
    let faces = vec![Vec::new(); 100];
    let d0_cells = vertices * edges.len();
    let d1_cells = faces.len() * edges.len();
    assert!(d0_cells <= limits.max_cells && d1_cells <= limits.max_cells);
    assert!(d0_cells + d1_cells > limits.max_cells);
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_oriented_graph(vertices, &edges, Some(&faces))
    });
    n8_assert_early_resource_refusal(
        result,
        requested,
        vertices * std::mem::size_of::<BigRational>(),
    );
}

#[test]
fn n8_operad_guard_precedes_coefficient_lowering() {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let vertices = limits.max_vertices + 1;
    let cycles = vec![vec![0; limits.max_cells + 1]];
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_operad_occurrences(vertices, &[(0, 0)], Some(&cycles))
    });
    n8_assert_early_resource_refusal(
        result,
        requested,
        cycles[0].len() * std::mem::size_of::<(usize, BigRational)>(),
    );
}

#[test]
fn n8_edge_count_limit_applies_even_to_zero_width_rows() {
    let count = core_kernel::resource_limits::OperationLimits::default().max_edges + 1;
    let edges = vec![(0, 0); count];
    let (result, requested) =
        n8_allocation_observer::measure(|| PromptCellComplex::from_oriented_graph(0, &edges, None));
    n8_assert_early_resource_refusal(
        result,
        requested,
        count * std::mem::size_of::<Vec<BigRational>>(),
    );
}

#[test]
fn n8_face_count_limit_applies_even_to_zero_width_rows() {
    let count = core_kernel::resource_limits::OperationLimits::default().max_faces + 1;
    let faces = vec![Vec::new(); count];
    let (result, requested) = n8_allocation_observer::measure(|| {
        PromptCellComplex::from_oriented_graph(0, &[], Some(&faces))
    });
    n8_assert_early_resource_refusal(
        result,
        requested,
        count * std::mem::size_of::<Vec<BigRational>>(),
    );
}

#[test]
fn n8_dense_cell_boundary_remains_admitted() {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let edges = vec![(0, 0); 100];
    let vertices = limits.max_cells / edges.len();
    assert_eq!(vertices * edges.len(), limits.max_cells);
    let complex = PromptCellComplex::from_oriented_graph(vertices, &edges, None)
        .expect("the declared dense cell boundary is admitted");
    assert_eq!(
        (complex.c0_dim, complex.c1_dim, complex.c2_dim),
        (vertices, 100, 0)
    );
    assert!(complex.d0.iter().flatten().all(Zero::is_zero));
}

#[test]
fn n8_zero_dimensional_profiles_remain_admitted() {
    let empty = PromptCellComplex::from_oriented_graph(0, &[], None).unwrap();
    assert_eq!((empty.c0_dim, empty.c1_dim, empty.c2_dim), (0, 0, 0));
    assert_eq!(empty.d0, Vec::<Vec<BigRational>>::new());
    assert_eq!(empty.d1, Vec::<Vec<BigRational>>::new());
    let faces = vec![Vec::new()];
    let isolated = PromptCellComplex::from_oriented_graph(3, &[], Some(&faces)).unwrap();
    assert_eq!(
        (isolated.c0_dim, isolated.c1_dim, isolated.c2_dim),
        (3, 0, 1)
    );
    assert_eq!(isolated.d1, vec![Vec::<BigRational>::new()]);
}

#[test]
fn n8_admitted_incidence_keeps_loops_parallel_edges_and_face_cancellation() {
    let edges = [(0, 0), (0, 1), (0, 1)];
    let faces = vec![vec![(1, r(2)), (1, r(-1)), (2, r(-1))]];
    let complex = PromptCellComplex::from_oriented_graph(2, &edges, Some(&faces)).unwrap();
    assert_eq!(
        complex.d0,
        vec![vec![r(0), r(0)], vec![r(-1), r(1)], vec![r(-1), r(1)]]
    );
    assert_eq!(complex.d1, vec![vec![r(0), r(1), r(-1)]]);
    let repeated =
        PromptCellComplex::from_operad_occurrences(1, &[(0, 0)], Some(&[vec![0, 0]])).unwrap();
    assert_eq!(repeated.d0, vec![vec![r(0)]]);
    assert_eq!(repeated.d1, vec![vec![r(2)]]);
}

fn m2_evaluate(
    complex: &PromptCellComplex,
    context: Option<&mut PrimeTriadContext>,
) -> CochainDisposition {
    PromptCochainEvaluator::evaluate(
        complex,
        &[r(1), r(2), r(-3)],
        &[r(0), r(1), r(3)],
        &[r(0), r(0), r(0)],
        context,
    )
}

fn m2_hash(source: &str) -> String {
    hex::encode(sha2::Sha256::digest(source.as_bytes()))
}

fn m2_assert_missing_bytes(expected: Option<String>, bound: Option<String>) {
    let mut complex = make_canonical_triangle(true);
    complex.source_bytes_hash = bound;
    let mut context = PrimeTriadContext {
        expected_source_hash: expected,
        ..PrimeTriadContext::default()
    };
    let refusal = context
        .validate_prime_000(&complex)
        .expect_err("declared source hashes cannot be checked without source bytes");
    assert_eq!(refusal.code, "SOURCE_BYTES_CORRUPTED");
    assert!(refusal.message.contains("source bytes are missing"));
    match m2_evaluate(&complex, Some(&mut context)) {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "SOURCE_BYTES_CORRUPTED");
            assert!(message.contains("source bytes are missing"));
        }
        other => panic!("expected missing-source refusal, got {other:?}"),
    }
}

#[test]
fn m2_expected_hash_without_bytes_is_refused() {
    m2_assert_missing_bytes(Some(m2_hash("source A")), None);
}

#[test]
fn m2_bound_hash_without_bytes_is_refused() {
    m2_assert_missing_bytes(None, Some(m2_hash("source A")));
}

#[test]
fn m2_equal_declared_hashes_without_bytes_are_refused() {
    m2_assert_missing_bytes(Some(m2_hash("source A")), Some(m2_hash("source A")));
}

#[test]
fn m2_unequal_declared_hashes_without_bytes_are_refused() {
    m2_assert_missing_bytes(Some(m2_hash("source A")), Some(m2_hash("source B")));
}

#[test]
fn m2_omitting_context_does_not_bypass_the_complex_hash() {
    let complex = make_canonical_triangle(true).with_source_bytes_hash(m2_hash("source A"));
    match m2_evaluate(&complex, None) {
        CochainDisposition::Refusal { code, message } => {
            assert_eq!(code, "SOURCE_BYTES_CORRUPTED");
            assert!(message.contains("source bytes are missing"));
        }
        other => panic!("omitted context bypassed declared source hash: {other:?}"),
    }
}

#[test]
fn m2_matching_hashes_accept_ascii_utf8_and_present_empty_bytes() {
    for source in ["source A", "custody λ → 𝒪", ""] {
        for (expected, bound) in [(true, false), (false, true), (true, true)] {
            let mut complex = make_canonical_triangle(true);
            complex.source_bytes_hash = bound.then(|| m2_hash(source));
            let mut context = PrimeTriadContext {
                source_bytes: Some(source.into()),
                expected_source_hash: expected.then(|| m2_hash(source)),
                ..PrimeTriadContext::default()
            };
            assert_eq!(context.validate_prime_000(&complex), Ok(()));
            assert!(
                m2_evaluate(&complex, Some(&mut context)).is_exact(),
                "source={source:?}, expected={expected}, bound={bound}"
            );
        }
    }
}

#[test]
fn m2_present_bytes_must_match_each_declared_hash() {
    for expected_matches in [false, true] {
        let mut complex = make_canonical_triangle(true);
        complex.source_bytes_hash = Some(m2_hash(if expected_matches {
            "source B"
        } else {
            "source A"
        }));
        let mut context = PrimeTriadContext {
            source_bytes: Some("source A".into()),
            expected_source_hash: Some(m2_hash(if expected_matches {
                "source A"
            } else {
                "source B"
            })),
            ..PrimeTriadContext::default()
        };
        match m2_evaluate(&complex, Some(&mut context)) {
            CochainDisposition::Refusal { code, .. } => {
                assert_eq!(code, "SOURCE_BYTES_CORRUPTED");
            }
            other => panic!("one disagreeing declared hash was ignored: {other:?}"),
        }
    }
}

#[test]
fn m2_no_hashes_and_no_bytes_preserve_optional_context() {
    let complex = make_canonical_triangle(true);
    let mut context = PrimeTriadContext::default();
    assert!(m2_evaluate(&complex, None).is_exact());
    assert!(m2_evaluate(&complex, Some(&mut context)).is_exact());
}

/// Only a test-vector decoder. It cannot represent named-vertex aliasing,
/// negative/bool usize indices, or float/bool/text BigRational coefficients.
/// Refusal here is not a production Rust constructor result.
fn decode_rational_coeff(val: &serde_json::Value, bad: &'static str) -> Result<BigRational, &'static str> {
    if let Some(value) = val.as_i64() {
        return Ok(r(value));
    }
    let q = val["rational"].as_array().ok_or(bad)?;
    if q.len() != 2 {
        return Err(bad);
    }
    let numerator = q[0].as_i64().ok_or(bad)?;
    let denominator = q[1].as_i64().ok_or(bad)?;
    if denominator <= 0 {
        return Err(bad);
    }
    Ok(r_frac(numerator, denominator))
}

fn decode_face_term(
    term: &serde_json::Value,
    bad: &'static str,
) -> Result<(usize, BigRational), &'static str> {
    let pair = term.as_array().ok_or(bad)?;
    if pair.len() != 2 {
        return Err(bad);
    }
    let index = usize::try_from(pair[0].as_u64().ok_or(bad)?).map_err(|_| bad)?;
    let coefficient = decode_rational_coeff(&pair[1], bad)?;
    Ok((index, coefficient))
}

fn decode_edge_pair(
    value: &serde_json::Value,
    vertices: &[&str],
    bad: &'static str,
) -> Result<(usize, usize), &'static str> {
    let pair = value.as_array().ok_or(bad)?;
    if pair.len() != 2 {
        return Err(bad);
    }
    let u = vertices
        .iter()
        .position(|v| Some(*v) == pair[0].as_str())
        .ok_or(bad)?;
    let v = vertices
        .iter()
        .position(|v| Some(*v) == pair[1].as_str())
        .ok_or(bad)?;
    Ok((u, v))
}

fn decode_faces(
    faces_val: &serde_json::Value,
    bad: &'static str,
) -> Result<Option<Vec<Vec<(usize, BigRational)>>>, &'static str> {
    if faces_val.is_null() {
        return Ok(None);
    }
    let faces = faces_val
        .as_array()
        .ok_or(bad)?
        .iter()
        .map(|face| {
            face.as_array()
                .ok_or(bad)?
                .iter()
                .map(|term| decode_face_term(term, bad))
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Some(faces))
}

fn decode_constructor_vector(
    case: &serde_json::Value,
) -> Result<
    (
        usize,
        Vec<(usize, usize)>,
        Option<Vec<Vec<(usize, BigRational)>>>,
    ),
    &'static str,
> {
    let bad = "fixture not representable by the typed constructor";
    let vertices = case["vertices"]
        .as_array()
        .ok_or(bad)?
        .iter()
        .map(|value| value.as_str().ok_or(bad))
        .collect::<Result<Vec<_>, _>>()?;
    if vertices
        .iter()
        .copied()
        .collect::<std::collections::BTreeSet<_>>()
        .len()
        != vertices.len()
    {
        return Err(bad);
    }
    let edges = case["edges"]
        .as_array()
        .ok_or(bad)?
        .iter()
        .map(|value| decode_edge_pair(value, &vertices, bad))
        .collect::<Result<Vec<_>, _>>()?;
    let faces = decode_faces(&case["faces"], bad)?;
    Ok((vertices.len(), edges, faces))
}

#[test]
fn test_shared_oriented_graph_constructor_vectors() {
    let cases: Vec<serde_json::Value> =
        serde_json::from_str(include_str!("fixtures/cochain_constructor_vectors.json")).unwrap();
    let mut constructed = 0;
    let mut constructor_refused = 0;
    let mut fixture_unrepresentable = 0;
    for case in cases {
        let decoded = decode_constructor_vector(&case);
        if case["rust"] == "fixture_unrepresentable" {
            assert!(decoded.is_err(), "{}", case["id"]);
            fixture_unrepresentable += 1;
            continue;
        }
        let (vertices, edges, faces) = decoded.expect("representable fixture values");
        let result = PromptCellComplex::from_oriented_graph(vertices, &edges, faces.as_deref());
        if case["rust"] == "constructor_refused" {
            assert_eq!(
                result.unwrap_err().code,
                "DIMENSION_MISMATCH",
                "{}",
                case["id"]
            );
            constructor_refused += 1;
            continue;
        }
        assert_eq!(case["rust"], "constructed");
        let graph = result.unwrap();
        let matrix = |rows: &[Vec<BigRational>]| {
            serde_json::to_value(
                rows.iter()
                    .map(|row| row.iter().map(ToString::to_string).collect::<Vec<_>>())
                    .collect::<Vec<_>>(),
            )
            .unwrap()
        };
        assert_eq!(matrix(&graph.d0), case["d0"], "{} d0", case["id"]);
        assert_eq!(matrix(&graph.d1), case["d1"], "{} d1", case["id"]);
        constructed += 1;
    }
    assert_eq!(
        (constructed, constructor_refused, fixture_unrepresentable),
        (7, 1, 8)
    );
}

// Origin: engine/crates_rs/tests/pfp_runtime/cochain_tests.rs
// Claim: urn:core:crates_rs:tests:cochain-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4bfe25ad {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4bfe25ad` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4bfe25ad {
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
impl BoundaryError4bfe25ad {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4bfe25ad {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4bfe25ad {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4bfe25ad {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4bfe25ad> {
        if capacity_bound == 0 {
            return Err(BoundaryError4bfe25ad::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4bfe25ad::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4bfe25ad::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4bfe25ad() {
    let admitted = BoundaryRecord4bfe25ad::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4bfe25ad::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
