//! Permutations in one-line notation: reading, products in reading order, inverses, and the
//! same products over permutation matrices.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:perm-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::perm::{
    compose, identity, inverse, is_permutation, matrix, of_matrix, product, read,
};

fn datum(text: &str) -> Datum {
    Datum::parse(text).expect("JSON")
}

#[test]
fn a_list_with_each_point_once_is_a_permutation() {
    assert_eq!(read(&datum("[2, 0, 1]"), 3), Some(vec![2, 0, 1]));
    assert_eq!(read(&datum("[0]"), 1), Some(vec![0]));
    assert_eq!(read(&datum("[]"), 0), Some(vec![]));
    assert!(is_permutation(&[1, 0]));
    assert!(is_permutation(&[]));
    assert!(is_permutation(&[3, 2, 1, 0]));
}

#[test]
fn a_repeated_missing_or_outside_point_is_not_a_permutation() {
    assert_eq!(read(&datum("[0, 0, 1]"), 3), None);
    assert_eq!(read(&datum("[1, 1]"), 2), None);
    assert_eq!(read(&datum("[0, 1, 3]"), 3), None);
    assert_eq!(read(&datum("[1, 2]"), 2), None);
    assert_eq!(read(&datum("[0, -1]"), 2), None);
    assert!(!is_permutation(&[0, 0]));
    assert!(!is_permutation(&[1]));
    assert!(!is_permutation(&[0, 2]));
    assert!(!is_permutation(&[2, 2, 0]));
}

#[test]
fn a_permutation_is_read_for_exactly_the_number_of_points_asked() {
    assert_eq!(read(&datum("[1, 0]"), 3), None);
    assert_eq!(read(&datum("[1, 0, 2]"), 2), None);
    assert_eq!(read(&datum("[1, 0]"), 2), Some(vec![1, 0]));
}

#[test]
fn only_a_list_of_exact_integers_is_read() {
    assert_eq!(read(&datum("[0, 1.0]"), 2), None);
    assert_eq!(read(&datum(r#"[0, "1"]"#), 2), None);
    // Leaving the unreadable entry out would leave a permutation of two points.
    assert_eq!(read(&datum("[0, 1.0, 1]"), 2), None);
    assert_eq!(read(&datum(r#"[1, "x", 0]"#), 2), None);
    assert_eq!(read(&datum("[null, 0]"), 1), None);
    assert_eq!(read(&datum(r#"{"0": 0}"#), 1), None);
    assert_eq!(read(&datum("0"), 1), None);
    assert_eq!(read(&datum("null"), 0), None);
    assert_eq!(read(&datum("[0, 99999999999999999999999]"), 2), None);
}

#[test]
fn the_identity_fixes_every_point() {
    assert_eq!(identity(0), Vec::<usize>::new());
    assert_eq!(identity(4), vec![0, 1, 2, 3]);
}

#[test]
fn a_product_applies_the_left_permutation_first() {
    let p = [1, 0, 2];
    let q = [0, 2, 1];
    assert_eq!(compose(&p, &q), vec![2, 0, 1]);
    assert_eq!(compose(&q, &p), vec![1, 2, 0]);
    assert_eq!(compose(&p, &identity(3)), p.to_vec());
    assert_eq!(compose(&identity(3), &q), q.to_vec());
}

#[test]
fn a_product_leaves_a_point_the_right_side_lacks_where_it_was_put() {
    assert_eq!(compose(&[2, 0, 1], &[1, 0]), vec![2, 1, 0]);
    assert_eq!(compose(&[1, 0], &[]), vec![1, 0]);
    assert_eq!(compose(&[], &[1, 0]), Vec::<usize>::new());
}

#[test]
fn an_inverse_undoes_its_permutation_on_both_sides() {
    let p = [2, 0, 3, 1];
    assert_eq!(inverse(&p), vec![1, 3, 0, 2]);
    assert_eq!(compose(&p, &inverse(&p)), identity(4));
    assert_eq!(compose(&inverse(&p), &p), identity(4));
    assert_eq!(inverse(&[]), Vec::<usize>::new());
    assert_eq!(inverse(&identity(3)), identity(3));
}

#[test]
fn an_inverse_of_a_list_that_is_no_permutation_keeps_its_length() {
    assert_eq!(inverse(&[5, 0]), vec![1, 1]);
}

#[test]
fn the_matrix_of_a_permutation_has_its_one_in_the_image_column() {
    assert_eq!(
        matrix(&[2, 0, 1]),
        vec![vec![0, 0, 1], vec![1, 0, 0], vec![0, 1, 0]]
    );
    assert_eq!(matrix(&[]), Vec::<Vec<u64>>::new());
    assert_eq!(matrix(&[0]), vec![vec![1]]);
}

#[test]
fn a_matrix_product_is_rows_times_columns() {
    let a = vec![vec![1, 2], vec![3, 4]];
    let b = vec![vec![5, 6], vec![7, 8]];
    assert_eq!(product(&a, &b), vec![vec![19, 22], vec![43, 50]]);
    assert_eq!(product(&b, &a), vec![vec![23, 34], vec![31, 46]]);
    let wide = vec![vec![1, 0, 2]];
    let tall = vec![vec![1], vec![5], vec![3]];
    assert_eq!(product(&wide, &tall), vec![vec![7]]);
    assert_eq!(
        product(&tall, &wide),
        vec![vec![1, 0, 2], vec![5, 0, 10], vec![3, 0, 6]]
    );
}

#[test]
fn a_matrix_product_reads_what_one_side_lacks_as_zeros() {
    let ragged = vec![vec![1, 1], vec![1]];
    assert_eq!(product(&[vec![2, 3]], &ragged), vec![vec![5, 2]]);
    assert_eq!(product(&[vec![2, 3, 4]], &ragged), vec![vec![5, 2]]);
    assert_eq!(product(&[vec![2]], &ragged), vec![vec![2, 2]]);
    assert_eq!(product(&[], &ragged), Vec::<Vec<u64>>::new());
    assert_eq!(product(&[vec![2, 3]], &[]), vec![Vec::<u64>::new()]);
}

#[test]
fn a_matrix_product_too_large_for_64_bits_stays_at_the_largest_value() {
    let big = vec![vec![u64::MAX, u64::MAX]];
    assert_eq!(product(&big, &[vec![2], vec![0]]), vec![vec![u64::MAX]]);
    assert_eq!(product(&big, &[vec![1], vec![1]]), vec![vec![u64::MAX]]);
    assert_eq!(
        product(&[vec![u64::MAX, 0]], &[vec![1], vec![7]]),
        vec![vec![u64::MAX]]
    );
}

#[test]
fn the_matrix_of_a_product_is_the_product_of_the_matrices() {
    let p = [1, 2, 0, 3];
    let q = [3, 0, 2, 1];
    assert_eq!(product(&matrix(&p), &matrix(&q)), matrix(&compose(&p, &q)));
    assert_eq!(
        of_matrix(&product(&matrix(&p), &matrix(&q))),
        Some(compose(&p, &q))
    );
    assert_ne!(compose(&p, &q), compose(&q, &p));
}

#[test]
fn a_permutation_is_read_back_from_its_matrix() {
    assert_eq!(of_matrix(&matrix(&[2, 0, 1])), Some(vec![2, 0, 1]));
    assert_eq!(of_matrix(&[]), Some(vec![]));
    assert_eq!(of_matrix(&[vec![1]]), Some(vec![0]));
}

#[test]
fn a_matrix_that_is_not_a_permutation_matrix_gives_nothing() {
    assert_eq!(of_matrix(&[vec![1, 1], vec![0, 1]]), None);
    assert_eq!(of_matrix(&[vec![0, 0], vec![0, 1]]), None);
    assert_eq!(of_matrix(&[vec![1, 0], vec![1, 0]]), None);
    assert_eq!(of_matrix(&[vec![2, 0], vec![0, 1]]), None);
    assert_eq!(of_matrix(&[vec![1, 2], vec![0, 1]]), None);
    assert_eq!(of_matrix(&[vec![1, 0, 0], vec![0, 1, 0]]), None);
    assert_eq!(of_matrix(&[vec![1], vec![1]]), None);
    assert_eq!(of_matrix(&[vec![1, 0], vec![1]]), None);
    assert_eq!(of_matrix(&[vec![0]]), None);
}
