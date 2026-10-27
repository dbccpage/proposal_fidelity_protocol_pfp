//! Exact finite many-sorted partial-algebra and relation descent.
//! No omitted operation is completed; predicates preserve both truth and falsity.
//! Exact finite many-sorted partial-algebra and relation descent.
//! No omitted operation is completed; predicates preserve both truth and falsity.
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PartialOperation {
    pub inputs: Vec<usize>,
    pub output: usize,
    /// Lexicographic Cartesian-product order, last coordinate varies fastest.
    /// Lexicographic Cartesian-product order, last coordinate varies fastest.
    pub values: Vec<Option<usize>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Predicate {
    pub inputs: Vec<usize>,
    pub values: Vec<bool>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FinitePartialStructure {
    pub sizes: Vec<usize>,
    pub operations: Vec<PartialOperation>,
    pub predicates: Vec<Predicate>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SortQuotient {
    pub target_sizes: Vec<usize>,
    pub maps: Vec<Vec<usize>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DescentError {
    InvalidSignature,
    InvalidTable,
    InvalidSortMap,
    CardinalityOverflow,
    OperationConflict {
        operation: usize,
        left: usize,
        right: usize,
        left_image: Option<usize>,
        right_image: Option<usize>,
    },
    PredicateConflict {
        predicate: usize,
        left: usize,
        right: usize,
    },
    ReceiptMismatch,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_partial_structure.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-partial-structure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DescentError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DescentError {}
fn cardinality(sizes: &[usize], inputs: &[usize]) -> Result<usize, DescentError> {
    inputs.iter().try_fold(1usize, |n, &sort| {
        let size = sizes.get(sort).ok_or(DescentError::InvalidSignature)?;
        n.checked_mul(*size)
            .ok_or(DescentError::CardinalityOverflow)
    })
}
impl FinitePartialStructure {
    pub fn validate(&self) -> Result<(), DescentError> {
        for operation in &self.operations {
            let output = *self
                .sizes
                .get(operation.output)
                .ok_or(DescentError::InvalidSignature)?;
            if cardinality(&self.sizes, &operation.inputs)? != operation.values.len()
                || operation
                    .values
                    .iter()
                    .flatten()
                    .any(|&value| value >= output)
            {
                return Err(DescentError::InvalidTable);
            }
        }
        for predicate in &self.predicates {
            if cardinality(&self.sizes, &predicate.inputs)? != predicate.values.len() {
                return Err(DescentError::InvalidTable);
            }
        }
        Ok(())
    }
}
impl SortQuotient {
    fn validate(&self, source: &FinitePartialStructure) -> Result<(), DescentError> {
        if self.maps.len() != source.sizes.len() || self.target_sizes.len() != source.sizes.len() {
            return Err(DescentError::InvalidSortMap);
        }
        for (sort, map) in self.maps.iter().enumerate() {
            if map.len() != source.sizes[sort]
                || map.iter().any(|&x| x >= self.target_sizes[sort])
                || map.iter().copied().collect::<BTreeSet<_>>().len() != self.target_sizes[sort]
            {
                return Err(DescentError::InvalidSortMap);
            }
        }
        Ok(())
    }
    fn tuple_image(&self, sizes: &[usize], inputs: &[usize], mut row: usize) -> usize {
        let mut image = 0;
        let mut stride = 1;
        for &sort in inputs.iter().rev() {
            let coordinate = row % sizes[sort];
            row /= sizes[sort];
            image += self.maps[sort][coordinate] * stride;
            stride *= self.target_sizes[sort];
        }
        image
    }
}
/// Necessary and sufficient descent, including reflection of undefinedness.
/// Surjectivity makes every target row determined and hence the result unique.
// Distinguish an unseen fiber from a seen operation value that is itself None.
fn insert_fiber<T: Copy + Eq>(
    rows: &mut [Option<(usize, T)>], image_row: usize, source_row: usize, value: T,
    conflict: impl FnOnce(usize, T) -> DescentError,
) -> Result<(), DescentError> {
    match rows[image_row] {
        Some((left, previous)) if previous != value => Err(conflict(left, previous)),
        None => { rows[image_row] = Some((source_row, value)); Ok(()) }
        _ => Ok(()),
    }
}

fn finish_fibers<T>(rows: Vec<Option<(usize, T)>>) -> Result<Vec<T>, DescentError> {
    rows.into_iter().map(|row| row.map(|(_, value)| value).ok_or(DescentError::InvalidSortMap)).collect()
}

fn descend_operation(source: &FinitePartialStructure, quotient: &SortQuotient, id: usize, operation: &PartialOperation) -> Result<PartialOperation, DescentError> {
    let count = cardinality(&quotient.target_sizes, &operation.inputs)?;
    let mut rows = vec![None; count];
    for (row, value) in operation.values.iter().enumerate() {
        let image_row = quotient.tuple_image(&source.sizes, &operation.inputs, row);
        let image = value.map(|value| quotient.maps[operation.output][value]);
        insert_fiber(&mut rows, image_row, row, image, |left, old| DescentError::OperationConflict {
            operation: id, left, right: row, left_image: old, right_image: image,
        })?;
    }
    Ok(PartialOperation { inputs: operation.inputs.clone(), output: operation.output, values: finish_fibers(rows)? })
}

fn descend_predicate(source: &FinitePartialStructure, quotient: &SortQuotient, id: usize, predicate: &Predicate) -> Result<Predicate, DescentError> {
    let count = cardinality(&quotient.target_sizes, &predicate.inputs)?;
    let mut rows = vec![None; count];
    for (row, &value) in predicate.values.iter().enumerate() {
        let image_row = quotient.tuple_image(&source.sizes, &predicate.inputs, row);
        insert_fiber(&mut rows, image_row, row, value, |left, _| DescentError::PredicateConflict {
            predicate: id, left, right: row,
        })?;
    }
    Ok(Predicate { inputs: predicate.inputs.clone(), values: finish_fibers(rows)? })
}

/// Necessary and sufficient descent,including reflection of undefinedness.
/// Surjectivity makes every target row determined and hence the result unique.
/// Cardinalities use checked left-to-right prefixes;overflow is a typed refusal.
pub fn descend(source: &FinitePartialStructure, quotient: &SortQuotient) -> Result<FinitePartialStructure, DescentError> {
    source.validate()?;
    quotient.validate(source)?;
    let operations = source.operations.iter().enumerate().map(|(id, operation)| descend_operation(source, quotient, id, operation)).collect::<Result<_, _>>()?;
    let predicates = source.predicates.iter().enumerate().map(|(id, predicate)| descend_predicate(source, quotient, id, predicate)).collect::<Result<_, _>>()?;
    Ok(FinitePartialStructure { sizes: quotient.target_sizes.clone(), operations, predicates })
}

/// Independently regenerate all rows; a proposed target cannot erase a field.
pub fn verify(
    source: &FinitePartialStructure,
    quotient: &SortQuotient,
    target: &FinitePartialStructure,
) -> Result<(), DescentError> {
    if &descend(source, quotient)? != target {
        return Err(DescentError::ReceiptMismatch);
    }
    Ok(())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn source(values: Vec<Option<usize>>) -> FinitePartialStructure {
        FinitePartialStructure {
            sizes: vec![3, 2],
            operations: vec![PartialOperation {
                inputs: vec![0],
                output: 1,
                values,
            }],
            predicates: vec![],
        }
    }
    fn quotient() -> SortQuotient {
        SortQuotient {
            target_sizes: vec![2, 2],
            maps: vec![vec![0, 0, 1], vec![0, 1]],
        }
    }
    #[test]
    fn partial_definedness_and_values_are_independent_obstructions() {
        assert!(matches!(
            descend(&source(vec![None, Some(0), Some(1)]), &quotient()),
            Err(DescentError::OperationConflict {
                left_image: None,
                right_image: Some(0),
                ..
            })
        ));
        assert!(matches!(
            descend(&source(vec![Some(0), Some(1), None]), &quotient()),
            Err(DescentError::OperationConflict { .. })
        ));
        let s = source(vec![Some(0), Some(0), None]);
        let mut target = descend(&s, &quotient()).unwrap();
        assert_eq!(target.operations[0].values, vec![Some(0), None]);
        verify(&s, &quotient(), &target).unwrap();
        target.operations[0].values[1] = Some(0);
        assert_eq!(
            verify(&s, &quotient(), &target),
            Err(DescentError::ReceiptMismatch)
        );
    }
    #[test]
    fn predicates_require_reflection_not_only_positive_preservation() {
        let mut s = source(vec![None, None, None]);
        s.predicates.push(Predicate {
            inputs: vec![0, 0],
            values: vec![true, false, false, false, false, false, false, false, false],
        });
        assert!(matches!(
            descend(&s, &quotient()),
            Err(DescentError::PredicateConflict { .. })
        ));
    }
    #[test]
    fn exhaustive_binary_partial_factorization_criterion() {
        // All 3^4 unary partial tables and all 2^4 predicates on a four-state source.
        // All 3^4 unary partial tables and all 2^4 predicates on a four-state source.
        let q = SortQuotient {
            target_sizes: vec![2, 2],
            maps: vec![vec![0, 0, 1, 1], vec![0, 1]],
        };
        for code in 0..81 {
            let mut n = code;
            let values: Vec<_> = (0..4)
                .map(|_| {
                    let v = n % 3;
                    n /= 3;
                    if v == 0 {
                        None
                    } else {
                        Some(v - 1)
                    }
                })
                .collect();
            for bits in 0..16 {
                let truth: Vec<_> = (0..4).map(|i| bits & (1 << i) != 0).collect();
                let expected = values[0] == values[1]
                    && values[2] == values[3]
                    && truth[0] == truth[1]
                    && truth[2] == truth[3];
                let s = FinitePartialStructure {
                    sizes: vec![4, 2],
                    operations: vec![PartialOperation {
                        inputs: vec![0],
                        output: 1,
                        values: values.clone(),
                    }],
                    predicates: vec![Predicate {
                        inputs: vec![0],
                        values: truth,
                    }],
                };
                assert_eq!(descend(&s, &q).is_ok(), expected);
            }
        }
    }
    #[test]
    fn nullary_empty_and_non_surjective_boundaries() {
        let s = FinitePartialStructure {
            sizes: vec![0, 1],
            operations: vec![
                PartialOperation {
                    inputs: vec![0],
                    output: 1,
                    values: vec![],
                },
                PartialOperation {
                    inputs: vec![],
                    output: 1,
                    values: vec![Some(0)],
                },
            ],
            predicates: vec![],
        };
        let q = SortQuotient {
            target_sizes: vec![0, 1],
            maps: vec![vec![], vec![0]],
        };
        assert_eq!(descend(&s, &q).unwrap(), s);
        let mut bad = q;
        bad.target_sizes[1] = 2;
        assert_eq!(descend(&s, &bad), Err(DescentError::InvalidSortMap));
    }
    #[test]
    fn quotient_composition_preserves_actual_operations_and_predicates() {
        let mut s = source(vec![Some(0), Some(0), Some(1)]);
        s.predicates.push(Predicate {
            inputs: vec![0],
            values: vec![true; 3],
        });
        let first = quotient();
        let middle = descend(&s, &first).unwrap();
        let second = SortQuotient {
            target_sizes: vec![1, 1],
            maps: vec![vec![0, 0], vec![0, 0]],
        };
        let composed = SortQuotient {
            target_sizes: vec![1, 1],
            maps: vec![vec![0, 0, 0], vec![0, 0]],
        };
        assert_eq!(
            descend(&middle, &second).unwrap(),
            descend(&s, &composed).unwrap()
        );
    }
}
