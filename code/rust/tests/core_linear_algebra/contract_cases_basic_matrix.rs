use linear_algebra::backend::basic_matrix::{
    ArithmeticError, BasicMatrix, CheckedMatrixError, CheckedNumeric, MatrixError, OperationLimits,
};
use num_bigint::BigInt;
use num_rational::Ratio;
#[test]
fn bounded_rational_overflow_must_return_error() {
    let a = Ratio::from_integer(i64::MAX);
    let b = Ratio::from_integer(1);
    assert_eq!(
        CheckedNumeric::checked_add(&a, &b),
        Err(ArithmeticError::Overflow)
    );
    assert_eq!(
        CheckedNumeric::checked_mul(&a, &Ratio::from_integer(2)),
        Err(ArithmeticError::Overflow)
    );
    assert_eq!(
        CheckedNumeric::checked_sub(&Ratio::from_integer(i64::MIN), &b),
        Err(ArithmeticError::Overflow)
    );
}

#[test]
fn capacity_overflow_must_return_error() {
    let mut called = false;
    let result = BasicMatrix::<u8>::try_from_fn(usize::MAX, 1, |_, _| {
        called = true;
        0
    });
    assert_eq!(
        result,
        Err(MatrixError::AllocationFailed {
            requested: usize::MAX
        })
    );
    assert!(!called);
    // Fits usize in element count but not the isize byte-capacity bound.
    let n = isize::MAX as usize / 8 + 1;
    assert!(matches!(
        BasicMatrix::<u64>::zero(n, 1),
        Err(MatrixError::AllocationFailed { .. })
    ));
}

#[test]
fn malformed_rational_must_return_error() {
    for bad in [Ratio::new_raw(1_i64, 0), Ratio::new_raw(0, 0)] {
        let good = Ratio::from_integer(1);
        for (a, b) in [(&bad, &good), (&good, &bad)] {
            assert_eq!(
                CheckedNumeric::checked_add(a, b),
                Err(ArithmeticError::ZeroDenominator)
            );
            assert_eq!(
                CheckedNumeric::checked_sub(a, b),
                Err(ArithmeticError::ZeroDenominator)
            );
            assert_eq!(
                CheckedNumeric::checked_mul(a, b),
                Err(ArithmeticError::ZeroDenominator)
            );
        }
    }
    let bad = Ratio::new_raw(BigInt::from(1), BigInt::from(0));
    let one = Ratio::from_integer(BigInt::from(1));
    for (a, b) in [(&bad, &one), (&one, &bad)] {
        assert_eq!(
            CheckedNumeric::checked_add(a, b),
            Err(ArithmeticError::ZeroDenominator)
        );
        assert_eq!(
            CheckedNumeric::checked_sub(a, b),
            Err(ArithmeticError::ZeroDenominator)
        );
        assert_eq!(
            CheckedNumeric::checked_mul(a, b),
            Err(ArithmeticError::ZeroDenominator)
        );
    }
}

#[test]
fn huge_empty_shapes_finish_without_callbacks() {
    for (rows, cols) in [(usize::MAX, 0), (0, usize::MAX), (0, 0)] {
        let a =
            BasicMatrix::<i64>::try_from_fn(rows, cols, |_, _| panic!("empty callback")).unwrap();
        assert_eq!(a.shape(), (rows, cols));
        assert!(a.as_slice().is_empty());
        assert_eq!(a.try_transpose().unwrap().shape(), (cols, rows));
        assert_eq!(a.checked_add(&a).unwrap(), a);
        let n = a.try_to_nalgebra().unwrap();
        assert_eq!(BasicMatrix::try_from_nalgebra(&n).unwrap(), a);
    }
    let left = BasicMatrix::<i64>::from_row_major(0, usize::MAX, vec![]).unwrap();
    let right = BasicMatrix::from_row_major(usize::MAX, 0, vec![]).unwrap();
    assert_eq!(left.checked_mul(&right).unwrap().shape(), (0, 0));
}

#[test]
fn validation_precedes_callbacks_and_scalar_operations() {
    let r =
        BasicMatrix::<u8>::try_from_fn_with_limit(usize::MAX, 2, 0, |_, _| panic!("must not run"));
    assert!(matches!(r, Err(MatrixError::DimensionOverflow { .. })));
    assert_eq!(
        BasicMatrix::<u8>::try_from_fn_with_limit(2, 3, 5, |_, _| panic!("must not run")),
        Err(MatrixError::AllocationLimitExceeded {
            requested: 6,
            limit: 5
        })
    );
    let bad = BasicMatrix::from_row_major(1, 1, vec![Ratio::new_raw(1_i64, 0)]).unwrap();
    let other = BasicMatrix::from_row_major(1, 2, vec![Ratio::from_integer(1); 2]).unwrap();
    assert!(matches!(
        bad.checked_add_with_limit(&other, 0),
        Err(CheckedMatrixError::Matrix(
            MatrixError::DimensionMismatch { .. }
        ))
    ));
    assert!(matches!(
        bad.checked_mul_with_limit(&bad, 0),
        Err(CheckedMatrixError::Matrix(
            MatrixError::AllocationLimitExceeded { .. }
        ))
    ));
    assert!(matches!(
        bad.checked_mul_with_limits(
            &bad,
            OperationLimits {
                max_elements: 1,
                max_scalar_ops: 1
            }
        ),
        Err(CheckedMatrixError::Matrix(
            MatrixError::OperationLimitExceeded {
                requested: 2,
                limit: 1
            }
        ))
    ));
}

#[test]
fn callback_order_and_first_error() {
    let mut visited = Vec::new();
    let result: Result<BasicMatrix<i64>, MatrixError> =
        BasicMatrix::try_from_fn_result(2, 3, |r, c| {
            visited.push((r, c));
            if (r, c) == (1, 1) {
                Err(MatrixError::InvalidOperation("stop".into()))
            } else {
                Ok(0)
            }
        });
    assert!(result.is_err());
    assert_eq!(visited, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]);
    let a = BasicMatrix::from_row_major(2, 2, vec![1, 2, 3, 4]).unwrap();
    let mut seen = Vec::new();
    let r: Result<BasicMatrix<i64>, MatrixError> = a.try_map(|x| {
        seen.push(*x);
        if *x == 3 {
            Err(MatrixError::InvalidOperation("stop".into()))
        } else {
            Ok(x * 2)
        }
    });
    assert!(r.is_err());
    assert_eq!(seen, [1, 2, 3]);
    assert_eq!(a.as_slice(), &[1, 2, 3, 4]);
}

#[test]
fn indexing_and_failed_set_preserve_storage() {
    let mut a = BasicMatrix::from_row_major(2, 3, vec![0, 1, 2, 3, 4, 5]).unwrap();
    for r in 0..2 {
        for c in 0..3 {
            assert_eq!(*a.get_ref(r, c).unwrap(), (r * 3 + c) as i32);
        }
    }
    let before = a.clone();
    for (r, c) in [(2, 0), (0, 3), (usize::MAX, usize::MAX)] {
        assert!(a.set(r, c, 99).is_err());
        assert_eq!(a, before);
    }
    a.set(1, 2, 9).unwrap();
    assert_eq!(a.as_slice(), &[0, 1, 2, 3, 4, 9]);
}

fn canonical_i128(mut n: i128, mut d: i128) -> Result<(i64, i64), ArithmeticError> {
    assert!(d > 0);
    let (mut a, mut b) = (n.abs(), d);
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    n /= a;
    d /= a;
    Ok((
        i64::try_from(n).map_err(|_| ArithmeticError::Overflow)?,
        i64::try_from(d).map_err(|_| ArithmeticError::Overflow)?,
    ))
}

#[test]
fn rational_boundary_grid_matches_independent_i128_oracle() {
    let nums = [
        i64::MIN,
        i64::MIN + 1,
        -7,
        -1,
        0,
        1,
        7,
        i64::MAX - 1,
        i64::MAX,
    ];
    let dens = [1_i64, 2, 3, i64::MAX];
    for n in nums {
        for d in dens {
            for m in nums {
                for e in dens {
                    let a = Ratio::new_raw(n, d);
                    let b = Ratio::new_raw(m, e);
                    let (nn, dd, mm, ee) =
                        (i128::from(n), i128::from(d), i128::from(m), i128::from(e));
                    let cases = [
                        (
                            CheckedNumeric::checked_add(&a, &b),
                            nn * ee + mm * dd,
                            dd * ee,
                        ),
                        (
                            CheckedNumeric::checked_sub(&a, &b),
                            nn * ee - mm * dd,
                            dd * ee,
                        ),
                        (CheckedNumeric::checked_mul(&a, &b), nn * mm, dd * ee),
                    ];
                    for (got, num, den) in cases {
                        assert_eq!(
                            got.map(|r| r.into_raw()),
                            canonical_i128(num, den),
                            "{n}/{d}, {m}/{e}"
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn raw_signs_minimum_and_cancellation_are_handled_exactly() {
    let zero = Ratio::from_integer(0);
    for (raw, expected) in [
        (Ratio::new_raw(2_i64, -4), Ratio::new_raw(-1, 2)),
        (Ratio::new_raw(i64::MIN, i64::MIN), Ratio::from_integer(1)),
        (
            Ratio::new_raw(i64::MIN, 2),
            Ratio::from_integer(i64::MIN / 2),
        ),
    ] {
        assert_eq!(
            CheckedNumeric::checked_add(&raw, &zero).unwrap().into_raw(),
            expected.into_raw()
        );
    }
    assert_eq!(
        CheckedNumeric::checked_add(&Ratio::new_raw(1, i64::MIN), &zero),
        Err(ArithmeticError::Overflow)
    );
    let a = Ratio::new_raw(i64::MAX, 2);
    assert_eq!(
        CheckedNumeric::checked_add(&a, &a).unwrap().into_raw(),
        (i64::MAX, 1)
    );
    let raw = Ratio::new_raw(BigInt::from(2), BigInt::from(-4));
    let sum = CheckedNumeric::checked_add(&raw, &raw).unwrap();
    assert_eq!(sum.into_raw(), (BigInt::from(-1), BigInt::from(1)));
}

#[test]
fn native_i64_edges_match_i128() {
    let values = [i64::MIN, i64::MIN + 1, -1, 0, 1, 2, i64::MAX - 1, i64::MAX];
    for a in values {
        for b in values {
            for (got, exact) in [
                (
                    CheckedNumeric::checked_add(&a, &b),
                    i128::from(a) + i128::from(b),
                ),
                (
                    CheckedNumeric::checked_sub(&a, &b),
                    i128::from(a) - i128::from(b),
                ),
                (
                    CheckedNumeric::checked_mul(&a, &b),
                    i128::from(a) * i128::from(b),
                ),
            ] {
                assert_eq!(
                    got,
                    i64::try_from(exact).map_err(|_| ArithmeticError::Overflow)
                );
            }
        }
    }
}

#[test]
fn intermediate_overflow_is_reported_even_if_final_sum_would_fit() {
    let a = BasicMatrix::from_row_major(1, 3, vec![i64::MAX, 1, -1]).unwrap();
    assert_eq!(
        a.checked_mul_vec(&[1, 1, 1]),
        Err(CheckedMatrixError::Scalar(ArithmeticError::Overflow))
    );
    let b = BasicMatrix::from_row_major(1, 1, vec![i64::MAX]).unwrap();
    assert!(b.checked_mul_vec(&[2]).is_err());
}

#[test]
fn work_budget_exact_boundary_and_empty_inner_dimension() {
    let a = BasicMatrix::from_row_major(2, 3, vec![1_i64; 6]).unwrap();
    let b = BasicMatrix::from_row_major(3, 2, vec![1_i64; 6]).unwrap();
    let limits = OperationLimits {
        max_elements: 4,
        max_scalar_ops: 24,
    };
    assert_eq!(
        a.checked_mul_with_limits(&b, limits).unwrap().as_slice(),
        &[3, 3, 3, 3]
    );
    assert!(matches!(
        a.checked_mul_with_limits(
            &b,
            OperationLimits {
                max_scalar_ops: 23,
                ..limits
            }
        ),
        Err(CheckedMatrixError::Matrix(
            MatrixError::OperationLimitExceeded {
                requested: 24,
                limit: 23
            }
        ))
    ));
    assert_eq!(
        a.checked_mul_vec_with_limits(
            &[1, 1, 1],
            OperationLimits {
                max_elements: 2,
                max_scalar_ops: 12
            }
        )
        .unwrap(),
        [3, 3]
    );
    assert!(a
        .checked_mul_vec_with_limits(
            &[1, 1, 1],
            OperationLimits {
                max_elements: 2,
                max_scalar_ops: 11
            }
        )
        .is_err());
    let left = BasicMatrix::<i64>::from_row_major(2, 0, vec![]).unwrap();
    let right = BasicMatrix::from_row_major(0, 3, vec![]).unwrap();
    assert_eq!(
        left.checked_mul_with_limits(
            &right,
            OperationLimits {
                max_elements: 6,
                max_scalar_ops: 0
            }
        )
        .unwrap()
        .as_slice(),
        &[0; 6]
    );
    assert_eq!(left.checked_mul_vec(&[]).unwrap(), [0, 0]);
}

#[test]
fn matrix_grid_matches_i128_and_nalgebra_and_algebraic_laws() {
    // Deterministic bounded property grid: all shapes 0..=5, 9 independent values.
    for rows in 0..=5 {
        for inner in 0..=5 {
            for cols in 0..=5 {
                for seed in -4..=4 {
                    let a = BasicMatrix::try_from_fn(rows, inner, |r, c| {
                        ((r * 7 + c * 3) as i64 + seed) % 11 - 5
                    })
                    .unwrap();
                    let b = BasicMatrix::try_from_fn(inner, cols, |r, c| {
                        ((r * 2 + c * 5) as i64 - seed) % 7 - 3
                    })
                    .unwrap();
                    let got = a.checked_mul(&b).unwrap();
                    assert_eq!(got.shape(), (rows, cols));
                    for r in 0..rows {
                        for c in 0..cols {
                            let exact: i128 = (0..inner)
                                .map(|k| {
                                    i128::from(a.get(r, k).unwrap())
                                        * i128::from(b.get(k, c).unwrap())
                                })
                                .sum();
                            assert_eq!(i128::from(got.get(r, c).unwrap()), exact);
                        }
                    }
                    let oracle = a.try_to_nalgebra().unwrap() * b.try_to_nalgebra().unwrap();
                    assert_eq!(got, BasicMatrix::try_from_nalgebra(&oracle).unwrap());
                    assert_eq!(got, a.mul(&b).unwrap());
                    assert_eq!(a.try_transpose().unwrap().try_transpose().unwrap(), a);
                    assert_eq!(a.checked_add(&a).unwrap().checked_sub(&a).unwrap(), a);
                    assert_eq!(a.map(|x| *x), a);
                    let mapped: Result<BasicMatrix<i64>, MatrixError> = a.try_map(|x| Ok(*x));
                    assert_eq!(mapped.unwrap(), a);
                    assert_eq!(
                        got.try_transpose().unwrap(),
                        b.try_transpose()
                            .unwrap()
                            .checked_mul(&a.try_transpose().unwrap())
                            .unwrap()
                    );
                }
            }
        }
    }
}

#[test]
fn error_sources_are_retained() {
    use std::error::Error;
    let error = CheckedMatrixError::Scalar(ArithmeticError::Overflow);
    assert_eq!(
        error.source().unwrap().to_string(),
        ArithmeticError::Overflow.to_string()
    );
    let error: CheckedMatrixError<ArithmeticError> = MatrixError::OperationCountOverflow.into();
    assert_eq!(
        error.source().unwrap().to_string(),
        MatrixError::OperationCountOverflow.to_string()
    );
}

#[test]
fn rational_matrix_operations_match_exact_small_examples() {
    let a = BasicMatrix::from_row_major(1, 2, vec![Ratio::new_raw(1_i64, 2), Ratio::new_raw(1, 3)])
        .unwrap();
    let b = BasicMatrix::from_row_major(2, 1, vec![Ratio::new_raw(2_i64, 3), Ratio::new_raw(3, 4)])
        .unwrap();
    assert_eq!(
        a.checked_mul(&b).unwrap().as_slice(),
        &[Ratio::new_raw(7, 12)]
    );
    let huge = Ratio::from_integer(BigInt::from(1) << 512);
    let a = BasicMatrix::from_row_major(1, 2, vec![huge.clone(), -huge.clone()]).unwrap();
    let one = Ratio::from_integer(BigInt::from(1));
    assert_eq!(
        a.checked_mul_vec(&[one.clone(), one]).unwrap(),
        [Ratio::from_integer(BigInt::from(0))]
    );
}

#[test]
fn zst_storage_and_allocation_are_valid() {
    let a = BasicMatrix::try_from_fn(3, 4, |_, _| ()).unwrap();
    assert_eq!(a.as_slice().len(), 12);
    assert_eq!(a.try_transpose().unwrap().shape(), (4, 3));
    let b = a.try_map::<(), MatrixError, _>(|_| Ok(())).unwrap();
    assert_eq!(a, b);
}

// Origin: engine/crates_rs/tests/core_linear_algebra/contract_cases_basic_matrix.rs
// Claim: urn:core:crates_rs:tests:contract-cases-basic-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
