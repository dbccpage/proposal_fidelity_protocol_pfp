//! Exact general linear sensing and its checked repair-quotient strengthening.
//! AuthorityEffect: None. Coefficients are exact unbounded rationals. No memory,
//! policy, idempotence or physical interpretation is supplied by this map.
use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::semiring_lumpability::semiring_product;
use num_rational::BigRational;
use num_traits::Zero;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LinearObserverError {
    #[error("matrix shape refusal: {0}")]
    Matrix(#[from] MatrixError),
    #[error("report sees admissible repairs at ({row},{column})")]
    SeesRepair { row: usize, column: usize },
    #[error("invalid exact rational: zero denominator")]
    InvalidRational,
    #[error("blindspot witness differs from independently recomputed values")]
    WitnessMismatch,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinearObserverPresentation {
    reports: BasicMatrix<BigRational>,
    repairs: BasicMatrix<BigRational>,
}
impl LinearObserverPresentation {
    pub fn try_new(
        reports: BasicMatrix<BigRational>,
        repairs: BasicMatrix<BigRational>,
    ) -> Result<Self, LinearObserverError> {
        let reports = checked_matrix(&reports)?;
        let repairs = checked_matrix(&repairs)?;
        let product = semiring_product(&reports, &repairs)?;
        for row in 0..product.rows() {
            for column in 0..product.cols() {
                if !product.get_ref(row, column)?.is_zero() {
                    return Err(LinearObserverError::SeesRepair { row, column });
                }
            }
        }
        Ok(Self { reports, repairs })
    }
    pub fn report_map(&self) -> &BasicMatrix<BigRational> {
        &self.reports
    }
    pub fn repair_map(&self) -> &BasicMatrix<BigRational> {
        &self.repairs
    }
    pub fn report(&self, defect: &[BigRational]) -> Result<Vec<BigRational>, LinearObserverError> {
        let column = checked_column(defect)?;
        let result = semiring_product(&self.reports, &column)?;
        (0..result.rows())
            .map(|i| result.get(i, 0).map_err(LinearObserverError::Matrix))
            .collect()
    }
}

fn checked_matrix(
    matrix: &BasicMatrix<BigRational>,
) -> Result<BasicMatrix<BigRational>, LinearObserverError> {
    let mut entries = Vec::new();
    for i in 0..matrix.rows() {
        for j in 0..matrix.cols() {
            let q = matrix.get_ref(i, j)?;
            if q.denom().is_zero() {
                return Err(LinearObserverError::InvalidRational);
            }
            entries.push(q.reduced());
        }
    }
    Ok(BasicMatrix::from_row_major(
        matrix.rows(),
        matrix.cols(),
        entries,
    )?)
}
fn checked_column(values: &[BigRational]) -> Result<BasicMatrix<BigRational>, LinearObserverError> {
    checked_matrix(&BasicMatrix::from_row_major(
        values.len(),
        1,
        values.to_vec(),
    )?)
}
fn column_values(
    matrix: &BasicMatrix<BigRational>,
) -> Result<Vec<BigRational>, LinearObserverError> {
    (0..matrix.rows())
        .map(|i| matrix.get(i, 0).map_err(LinearObserverError::Matrix))
        .collect()
}
/// General sensing on the full exact rational defect space. Repairs need not be
/// invisible. Finite matrix dimensions do not restrict carriers to finite sets.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinearSensingPresentation {
    reports: BasicMatrix<BigRational>,
    repairs: BasicMatrix<BigRational>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairBlindspotWitness {
    pub parameters: Vec<BigRational>,
    pub repair_defect: Vec<BigRational>,
    pub sensed_report: Vec<BigRational>,
    /// Membership in im(d0) intersect ker(R), including the zero vector.
    pub is_blindspot: bool,
    pub is_nontrivial: bool,
}
impl LinearSensingPresentation {
    pub fn try_new(
        reports: BasicMatrix<BigRational>,
        repairs: BasicMatrix<BigRational>,
    ) -> Result<Self, LinearObserverError> {
        let reports = checked_matrix(&reports)?;
        let repairs = checked_matrix(&repairs)?;
        // Shape check only; nonzero entries in this product are permitted.
        semiring_product(&reports, &repairs)?;
        Ok(Self { reports, repairs })
    }
    pub fn report_map(&self) -> &BasicMatrix<BigRational> {
        &self.reports
    }
    pub fn repair_map(&self) -> &BasicMatrix<BigRational> {
        &self.repairs
    }
    pub fn report(&self, defect: &[BigRational]) -> Result<Vec<BigRational>, LinearObserverError> {
        column_values(&semiring_product(&self.reports, &checked_column(defect)?)?)
    }
    /// Strengthen to a quotient report exactly when R d0 = 0.
    pub fn try_quotient(&self) -> Result<LinearObserverPresentation, LinearObserverError> {
        LinearObserverPresentation::try_new(self.reports.clone(), self.repairs.clone())
    }
    /// Check the actual supplied repair, rather than infer visibility from a tag.
    pub fn check_repair_blindspot(
        &self,
        parameters: &[BigRational],
    ) -> Result<RepairBlindspotWitness, LinearObserverError> {
        let column = checked_column(parameters)?;
        let repair_defect = column_values(&semiring_product(&self.repairs, &column)?)?;
        let sensed_report = self.report(&repair_defect)?;
        Ok(RepairBlindspotWitness {
            parameters: column_values(&column)?,
            is_blindspot: sensed_report.iter().all(Zero::is_zero),
            is_nontrivial: repair_defect.iter().any(|q| !q.is_zero()),
            repair_defect,
            sensed_report,
        })
    }
    pub fn verify_blindspot_witness(
        &self,
        witness: &RepairBlindspotWitness,
    ) -> Result<(), LinearObserverError> {
        if self.check_repair_blindspot(&witness.parameters)? != *witness {
            return Err(LinearObserverError::WitnessMismatch);
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_observer_presentation.rs
// Claim: urn:core:crates_rs:core-linear-algebra:linear-observer-presentation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod sensing_tests {
    use super::*;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }
    fn mat(rows: usize, cols: usize, data: &[i64]) -> BasicMatrix<BigRational> {
        BasicMatrix::from_row_major(rows, cols, data.iter().map(|&n| q(n)).collect()).unwrap()
    }
    #[test]
    fn general_sensing_is_not_a_quotient_and_nonzero_blindspots_can_coexist() {
        let sensing =
            LinearSensingPresentation::try_new(mat(1, 2, &[1, 0]), mat(2, 2, &[1, 0, 0, 1]))
                .unwrap();
        assert_eq!(sensing.report(&[q(3), q(7)]).unwrap(), vec![q(3)]);
        assert!(matches!(
            sensing.try_quotient(),
            Err(LinearObserverError::SeesRepair { .. })
        ));
        let hidden = sensing.check_repair_blindspot(&[q(0), q(7)]).unwrap();
        assert!(hidden.is_blindspot && hidden.is_nontrivial);
        sensing.verify_blindspot_witness(&hidden).unwrap();
        let visible = sensing.check_repair_blindspot(&[q(3), q(0)]).unwrap();
        assert!(!visible.is_blindspot && visible.is_nontrivial);
        let zero = sensing.check_repair_blindspot(&[q(0), q(0)]).unwrap();
        assert!(zero.is_blindspot && !zero.is_nontrivial);
        let mut forged = hidden;
        forged.repair_defect[1] = q(8);
        assert_eq!(
            sensing.verify_blindspot_witness(&forged),
            Err(LinearObserverError::WitnessMismatch)
        );
    }
    #[test]
    fn invisible_repairs_allow_exact_quotient_strengthening() {
        let s =
            LinearSensingPresentation::try_new(mat(1, 2, &[1, -1]), mat(2, 1, &[1, 1])).unwrap();
        let quotient = s.try_quotient().unwrap();
        assert_eq!(
            quotient.report(&[q(5), q(2)]).unwrap(),
            s.report(&[q(5), q(2)]).unwrap()
        );
        assert!(s.check_repair_blindspot(&[q(4)]).unwrap().is_blindspot);
    }
    #[test]
    fn malformed_shapes_rationals_and_actual_repair_inputs_refuse() {
        assert!(LinearSensingPresentation::try_new(mat(1, 2, &[1, 0]), mat(1, 1, &[1])).is_err());
        let bad = BasicMatrix::from_row_major(1, 1, vec![BigRational::new_raw(1.into(), 0.into())])
            .unwrap();
        assert_eq!(
            LinearSensingPresentation::try_new(bad, mat(1, 1, &[1])),
            Err(LinearObserverError::InvalidRational)
        );
        let s = LinearSensingPresentation::try_new(mat(1, 1, &[1]), mat(1, 1, &[1])).unwrap();
        assert!(s.check_repair_blindspot(&[]).is_err());
        assert!(s.report(&[]).is_err());
    }
}
