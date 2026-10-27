//! Typed finite retention data form a Cartesian product of update, readout,
//! and comparison choices. Forward compatibility is an *additional* law.
//! Arbitrary comparison refinement produces a relation, not a partition.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RetentionChoiceError {
    EmptyCarrier,
    CardinalityOverflow,
    ChoiceOutsideRange,
    InvalidShape,
    OutsideCarrier,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_retention_choices.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-retention-choices:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RetentionChoiceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RetentionChoiceError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RetentionSignature {
    pub state_count: usize,
    pub label_count: usize,
    pub report_count: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RetentionChoiceCounts {
    pub updates: u128,
    pub readouts: u128,
    pub comparisons: u128,
    pub reflexive_symmetric_comparisons: u128,
    pub packets: u128,
}

fn checked_power(mut base: u128, mut exponent: usize) -> Result<u128, RetentionChoiceError> {
    let mut result = 1u128;
    while exponent > 0 {
        if exponent & 1 == 1 {
            result = result
                .checked_mul(base)
                .ok_or(RetentionChoiceError::CardinalityOverflow)?;
        }
        exponent >>= 1;
        if exponent > 0 {
            base = base
                .checked_mul(base)
                .ok_or(RetentionChoiceError::CardinalityOverflow)?;
        }
    }
    Ok(result)
}

impl RetentionSignature {
    pub fn counts(&self) -> Result<RetentionChoiceCounts, RetentionChoiceError> {
        if self.state_count == 0 {
            return Err(RetentionChoiceError::EmptyCarrier);
        }
        let n = self.state_count;
        let k = self.label_count;
        let m = self.report_count;
        let update_entries = n
            .checked_mul(k)
            .ok_or(RetentionChoiceError::CardinalityOverflow)?;
        let comparison_entries = m
            .checked_mul(m)
            .ok_or(RetentionChoiceError::CardinalityOverflow)?;
        let unordered_pairs = m
            .checked_mul(m.saturating_sub(1))
            .ok_or(RetentionChoiceError::CardinalityOverflow)?
            / 2;
        let updates = checked_power(n as u128, update_entries)?;
        let readouts = checked_power(m as u128, n)?;
        let comparisons = checked_power(2, comparison_entries)?;
        let reflexive_symmetric_comparisons = checked_power(2, unordered_pairs)?;
        let packets = updates
            .checked_mul(readouts)
            .and_then(|v| v.checked_mul(comparisons))
            .ok_or(RetentionChoiceError::CardinalityOverflow)?;
        Ok(RetentionChoiceCounts {
            updates,
            readouts,
            comparisons,
            reflexive_symmetric_comparisons,
            packets,
        })
    }

    /// Every code triple in its independent ranges constructs one typed
    /// packet. Mixed-radix digits enumerate all choices without selection.
    pub fn from_codes(
        &self,
        mut update: u128,
        mut report: u128,
        comparison: u128,
    ) -> Result<FiniteRetentionData, RetentionChoiceError> {
        let counts = self.counts()?;
        if update >= counts.updates || report >= counts.readouts || comparison >= counts.comparisons
        {
            return Err(RetentionChoiceError::ChoiceOutsideRange);
        }
        let mut updates = vec![vec![0; self.label_count]; self.state_count];
        for row in &mut updates {
            for value in row {
                *value = (update % self.state_count as u128) as usize;
                update /= self.state_count as u128;
            }
        }
        let mut reports = vec![0; self.state_count];
        for value in &mut reports {
            *value = (report % self.report_count as u128) as usize;
            report /= self.report_count as u128;
        }
        let comparison = (0..self.report_count)
            .map(|x| {
                (0..self.report_count)
                    .map(|y| comparison & (1 << (x * self.report_count + y)) != 0)
                    .collect()
            })
            .collect();
        FiniteRetentionData::new(updates, reports, comparison, self.label_count)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteRetentionData {
    updates: Vec<Vec<usize>>,
    reports: Vec<usize>,
    comparison: Vec<Vec<bool>>,
    label_count: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ForwardRelationReceipt {
    pub relations: Vec<Vec<Vec<bool>>>,
    pub relation: Vec<Vec<bool>>,
}

impl FiniteRetentionData {
    pub fn new(
        updates: Vec<Vec<usize>>,
        reports: Vec<usize>,
        comparison: Vec<Vec<bool>>,
        label_count: usize,
    ) -> Result<Self, RetentionChoiceError> {
        let n = reports.len();
        let m = comparison.len();
        if n == 0 {
            return Err(RetentionChoiceError::EmptyCarrier);
        }
        if updates.len() != n
            || updates.iter().any(|row| row.len() != label_count)
            || comparison.iter().any(|row| row.len() != m)
        {
            return Err(RetentionChoiceError::InvalidShape);
        }
        if updates.iter().flatten().any(|&state| state >= n) || reports.iter().any(|&r| r >= m) {
            return Err(RetentionChoiceError::OutsideCarrier);
        }
        Ok(Self {
            updates,
            reports,
            comparison,
            label_count,
        })
    }
    pub fn updates(&self) -> &[Vec<usize>] {
        &self.updates
    }
    pub fn reports(&self) -> &[usize] {
        &self.reports
    }
    pub fn comparison(&self) -> &[Vec<bool>] {
        &self.comparison
    }
    pub fn is_reflexive_symmetric_comparison(&self) -> bool {
        let m = self.comparison.len();
        (0..m).all(|x| {
            self.comparison[x][x] && (0..m).all(|y| self.comparison[x][y] == self.comparison[y][x])
        })
    }
    pub fn greatest_forward_relation(&self) -> ForwardRelationReceipt {
        let n = self.reports.len();
        let mut relation: Vec<Vec<bool>> = (0..n)
            .map(|x| {
                (0..n)
                    .map(|y| self.comparison[self.reports[x]][self.reports[y]])
                    .collect()
            })
            .collect();
        let mut relations = vec![relation.clone()];
        loop {
            let next: Vec<Vec<bool>> = (0..n)
                .map(|x| {
                    (0..n)
                        .map(|y| {
                            relation[x][y]
                                && (0..self.label_count).all(|label| {
                                    relation[self.updates[x][label]][self.updates[y][label]]
                                })
                        })
                        .collect()
                })
                .collect();
            if next == relation {
                break;
            }
            relation = next;
            relations.push(relation.clone());
        }
        ForwardRelationReceipt {
            relations,
            relation,
        }
    }
    pub fn verify_forward_receipt(&self, receipt: &ForwardRelationReceipt) -> bool {
        &self.greatest_forward_relation() == receipt
    }
    pub fn is_forward_compatible(&self, relation: &[Vec<bool>]) -> bool {
        let n = self.reports.len();
        relation.len() == n
            && relation.iter().all(|row| row.len() == n)
            && (0..n).all(|x| {
                (0..n).all(|y| {
                    !relation[x][y]
                        || (self.comparison[self.reports[x]][self.reports[y]]
                            && (0..self.label_count).all(|label| {
                                relation[self.updates[x][label]][self.updates[y][label]]
                            }))
                })
            })
    }
    pub fn relation_is_equivalence(&self, receipt: &ForwardRelationReceipt) -> bool {
        if !self.verify_forward_receipt(receipt) {
            return false;
        }
        let r = &receipt.relation;
        let n = self.reports.len();
        (0..n).all(|x| {
            r[x][x]
                && (0..n)
                    .all(|y| r[x][y] == r[y][x] && (0..n).all(|z| !r[x][y] || !r[y][z] || r[x][z]))
        })
    }
    /// A state quotient is admissible iff its actual relation is an
    /// equivalence. A literal report map descends iff reports are additionally
    /// constant on its classes. Tolerance alone supplies no such equality.
    pub fn raw_report_quotient_admissible(&self, receipt: &ForwardRelationReceipt) -> bool {
        self.relation_is_equivalence(receipt)
            && (0..self.reports.len()).all(|x| {
                (0..self.reports.len())
                    .all(|y| !receipt.relation[x][y] || self.reports[x] == self.reports[y])
            })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_independent_code_triple_constructs_a_packet() {
        let signature = RetentionSignature {
            state_count: 2,
            label_count: 1,
            report_count: 2,
        };
        let counts = signature.counts().unwrap();
        assert_eq!(
            counts,
            RetentionChoiceCounts {
                updates: 4,
                readouts: 4,
                comparisons: 16,
                reflexive_symmetric_comparisons: 2,
                packets: 256
            }
        );
        let mut packets = Vec::new();
        for u in 0..counts.updates {
            for r in 0..counts.readouts {
                for c in 0..counts.comparisons {
                    let packet = signature.from_codes(u, r, c).unwrap();
                    let receipt = packet.greatest_forward_relation();
                    assert!(packet.is_forward_compatible(&receipt.relation));
                    assert!(receipt.relations.len() <= 5);
                    let mut union = vec![vec![false; 2]; 2];
                    for pair_bits in 0..16 {
                        let candidate: Vec<Vec<bool>> = (0..2)
                            .map(|x| {
                                (0..2)
                                    .map(|y| pair_bits & (1 << (2 * x + y)) != 0)
                                    .collect()
                            })
                            .collect();
                        if packet.is_forward_compatible(&candidate) {
                            for x in 0..2 {
                                for y in 0..2 {
                                    union[x][y] |= candidate[x][y];
                                }
                            }
                        }
                    }
                    assert_eq!(union, receipt.relation);
                    assert!(!packets.contains(&packet));
                    packets.push(packet);
                }
            }
        }
        assert_eq!(packets.len(), 256);
        assert!(signature.from_codes(4, 0, 0).is_err());
    }

    #[test]
    fn tolerance_is_not_an_equivalence_or_a_literal_report_quotient() {
        let tolerance = vec![
            vec![true, true, false],
            vec![true, true, true],
            vec![false, true, true],
        ];
        let packet =
            FiniteRetentionData::new(vec![vec![0], vec![1], vec![2]], vec![0, 1, 2], tolerance, 1)
                .unwrap();
        assert!(packet.is_reflexive_symmetric_comparison());
        let receipt = packet.greatest_forward_relation();
        assert!(!packet.relation_is_equivalence(&receipt));
        assert!(!packet.raw_report_quotient_admissible(&receipt));
        let universal = FiniteRetentionData::new(
            vec![vec![0], vec![1]],
            vec![0, 1],
            vec![vec![true; 2]; 2],
            1,
        )
        .unwrap();
        let receipt = universal.greatest_forward_relation();
        assert!(universal.relation_is_equivalence(&receipt));
        assert!(!universal.raw_report_quotient_admissible(&receipt));
    }

    #[test]
    fn regularity_couples_otherwise_independent_factors() {
        let comparison = vec![vec![true, false], vec![false, true]];
        let keep = FiniteRetentionData::new(
            vec![vec![0], vec![1], vec![2]],
            vec![0, 0, 1],
            comparison.clone(),
            1,
        )
        .unwrap();
        let break_fiber = FiniteRetentionData::new(
            vec![vec![0], vec![2], vec![2]],
            vec![0, 0, 1],
            comparison,
            1,
        )
        .unwrap();
        assert!(keep.greatest_forward_relation().relation[0][1]);
        assert!(!break_fiber.greatest_forward_relation().relation[0][1]);
    }

    #[test]
    fn cardinality_and_regular_degenerate_boundaries() {
        let empty_outputs = RetentionSignature {
            state_count: 2,
            label_count: 0,
            report_count: 0,
        };
        assert_eq!(empty_outputs.counts().unwrap().packets, 0);
        assert!(empty_outputs.from_codes(0, 0, 0).is_err());
        let static_packet = RetentionSignature {
            state_count: 2,
            label_count: 0,
            report_count: 1,
        };
        assert_eq!(static_packet.counts().unwrap().updates, 1);
        assert!(RetentionSignature {
            state_count: 0,
            label_count: 1,
            report_count: 1
        }
        .counts()
        .is_err());
        assert!(RetentionSignature {
            state_count: 2,
            label_count: 1,
            report_count: 12
        }
        .counts()
        .is_err());
    }
}
