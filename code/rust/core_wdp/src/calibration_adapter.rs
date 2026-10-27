//! Named WDP calibration packets and problem-bound exact replay receipts.
//!
//! Numerical composition/enclosure mathematics is delegated to
//! `core_measurement::affine_calibration`. Packet identity, ordered stages and
//! actual input are bound explicitly; physical traceability and confidence
//! claims remain separate requirements rather than consequences of arithmetic.

use num_rational::BigRational;
use core_measurement::affine_calibration::{
    compose_nominal, nominal_chain_update_bound, propagate_chain, AffineCalibration, BoundedReading,
};
use thiserror::Error;

use crate::types::AuthorityEffect;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum CalibrationPacketError {
    #[error("calibration packet identity must be nonempty")]
    EmptyPacketIdentity,
    #[error("calibration stage identity must be nonempty")]
    EmptyStageIdentity,
    #[error("calibration update packets must declare the same bounded input")]
    UpdateInputMismatch,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NamedCalibrationStage {
    pub stage_id: String,
    pub calibration: AffineCalibration,
}

impl NamedCalibrationStage {
    pub fn new(
        stage_id: String,
        calibration: AffineCalibration,
    ) -> Result<Self, CalibrationPacketError> {
        if stage_id.is_empty() {
            return Err(CalibrationPacketError::EmptyStageIdentity);
        }
        Ok(Self {
            stage_id,
            calibration,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalibrationPacket {
    pub packet_id: String,
    pub input: BoundedReading,
    pub stages: Vec<NamedCalibrationStage>,
}

impl CalibrationPacket {
    pub fn new(
        packet_id: String,
        input: BoundedReading,
        stages: Vec<NamedCalibrationStage>,
    ) -> Result<Self, CalibrationPacketError> {
        let packet = Self {
            packet_id,
            input,
            stages,
        };
        packet.validate()?;
        Ok(packet)
    }

    fn validate(&self) -> Result<(), CalibrationPacketError> {
        if self.packet_id.is_empty() {
            return Err(CalibrationPacketError::EmptyPacketIdentity);
        }
        if self.stages.iter().any(|stage| stage.stage_id.is_empty()) {
            return Err(CalibrationPacketError::EmptyStageIdentity);
        }
        Ok(())
    }

    fn calibrations(&self) -> Vec<AffineCalibration> {
        self.stages
            .iter()
            .map(|stage| stage.calibration.clone())
            .collect()
    }
}

/// Input and every intermediate output appear in declared order. A stage ID
/// may repeat when a calibration is applied twice: position remains binding.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalibrationReceipt {
    pub packet: CalibrationPacket,
    pub readings: Vec<BoundedReading>,
    pub nominal_gain: BigRational,
    pub nominal_offset: BigRational,
    pub authority_effect: AuthorityEffect,
}

pub fn evaluate_calibration_packet(
    packet: &CalibrationPacket,
) -> Result<CalibrationReceipt, CalibrationPacketError> {
    packet.validate()?;
    let stages = packet.calibrations();
    let (nominal_gain, nominal_offset) = compose_nominal(&stages);
    Ok(CalibrationReceipt {
        packet: packet.clone(),
        readings: propagate_chain(&packet.input, &stages),
        nominal_gain,
        nominal_offset,
        authority_effect: AuthorityEffect::None,
    })
}

/// Replay against the externally supplied actual problem, never merely the
/// candidate's self-declared packet. This checks input, stage count/order/IDs,
/// exact coefficients and bounds, all intermediate enclosures and final output.
pub fn verify_calibration_receipt(
    actual_packet: &CalibrationPacket,
    candidate: &CalibrationReceipt,
) -> Result<bool, CalibrationPacketError> {
    let checked = evaluate_calibration_packet(actual_packet)?;
    Ok(candidate == &checked)
}

/// A nominal chain-update supremum plus old and new uncertainty propagation.
/// It does not collapse uncertain realizations into the nominal update bound.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalibrationUpdateReceipt {
    pub old: CalibrationReceipt,
    pub new: CalibrationReceipt,
    pub nominal_update_supremum: BigRational,
    pub authority_effect: AuthorityEffect,
}

pub fn evaluate_calibration_update(
    old: &CalibrationPacket,
    new: &CalibrationPacket,
) -> Result<CalibrationUpdateReceipt, CalibrationPacketError> {
    old.validate()?;
    new.validate()?;
    if old.input != new.input {
        return Err(CalibrationPacketError::UpdateInputMismatch);
    }
    Ok(CalibrationUpdateReceipt {
        old: evaluate_calibration_packet(old)?,
        new: evaluate_calibration_packet(new)?,
        nominal_update_supremum: nominal_chain_update_bound(
            &old.calibrations(),
            &new.calibrations(),
            &old.input,
        ),
        authority_effect: AuthorityEffect::None,
    })
}

pub fn verify_calibration_update(
    actual_old: &CalibrationPacket,
    actual_new: &CalibrationPacket,
    candidate: &CalibrationUpdateReceipt,
) -> Result<bool, CalibrationPacketError> {
    Ok(candidate == &evaluate_calibration_update(actual_old, actual_new)?)
}

// Origin: engine/crates_rs/core_wdp/src/calibration_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:calibration-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(n))
    }
    fn packet() -> CalibrationPacket {
        let calibration = AffineCalibration::new(q(-2), q(3), q(1), q(2), q(1)).unwrap();
        CalibrationPacket::new(
            "packet-0".into(),
            BoundedReading::new(q(4), q(1)).unwrap(),
            vec![NamedCalibrationStage::new("stage-0".into(), calibration).unwrap()],
        )
        .unwrap()
    }

    #[test]
    fn replay_binds_input_named_stages_and_all_outputs() {
        let actual = packet();
        let receipt = evaluate_calibration_packet(&actual).unwrap();
        assert!(verify_calibration_receipt(&actual, &receipt).unwrap());
        assert_eq!(receipt.readings.len(), 2);
        assert_eq!(receipt.readings[1].center(), &q(-5));
        assert_eq!(receipt.readings[1].radius(), &q(10));
        let mut forged = receipt.clone();
        forged.packet.input = BoundedReading::new(q(5), q(1)).unwrap();
        assert!(!verify_calibration_receipt(&actual, &forged).unwrap());
        let mut forged = receipt.clone();
        forged.packet.stages[0].stage_id = "unrelated".into();
        assert!(!verify_calibration_receipt(&actual, &forged).unwrap());
        let mut forged = receipt.clone();
        forged.readings.pop();
        assert!(!verify_calibration_receipt(&actual, &forged).unwrap());
        let mut forged = receipt;
        forged.nominal_gain = q(99);
        assert!(!verify_calibration_receipt(&actual, &forged).unwrap());
    }

    #[test]
    fn update_replay_binds_actual_old_new_problems() {
        let old = packet();
        let mut new = old.clone();
        new.packet_id = "packet-1".into();
        new.stages[0].calibration = AffineCalibration::new(q(1), q(-1), q(0), q(0), q(0)).unwrap();
        let receipt = evaluate_calibration_update(&old, &new).unwrap();
        // Delta(t)=3t-4 on [3,5], exact supremum 11.
        assert_eq!(receipt.nominal_update_supremum, q(11));
        assert!(verify_calibration_update(&old, &new, &receipt).unwrap());
        assert!(!verify_calibration_update(&new, &old, &receipt).unwrap());
        let mut forged = receipt.clone();
        forged.nominal_update_supremum = q(0);
        assert!(!verify_calibration_update(&old, &new, &forged).unwrap());
        new.input = BoundedReading::new(q(0), q(1)).unwrap();
        assert_eq!(
            evaluate_calibration_update(&old, &new),
            Err(CalibrationPacketError::UpdateInputMismatch)
        );
    }

    #[test]
    fn stage_order_and_repeated_applications_are_preserved() {
        let mut actual = packet();
        let second = AffineCalibration::new(q(3), q(1), q(0), q(0), q(0)).unwrap();
        actual
            .stages
            .push(NamedCalibrationStage::new("stage-1".into(), second).unwrap());
        let receipt = evaluate_calibration_packet(&actual).unwrap();
        let mut reordered = actual.clone();
        reordered.stages.reverse();
        assert!(!verify_calibration_receipt(&reordered, &receipt).unwrap());
        assert_eq!(receipt.nominal_gain, q(-6));
        assert_eq!(receipt.nominal_offset, q(10));
        let repeated = actual.stages[0].clone();
        actual.stages.push(repeated);
        assert_eq!(
            evaluate_calibration_packet(&actual).unwrap().readings.len(),
            4
        );
    }

    #[test]
    fn empty_chain_and_invalid_public_identity() {
        let mut actual = packet();
        actual.stages.clear();
        let receipt = evaluate_calibration_packet(&actual).unwrap();
        assert_eq!(receipt.readings, vec![actual.input.clone()]);
        assert_eq!((receipt.nominal_gain, receipt.nominal_offset), (q(1), q(0)));
        actual.packet_id.clear();
        assert!(matches!(
            evaluate_calibration_packet(&actual),
            Err(CalibrationPacketError::EmptyPacketIdentity)
        ));
        let mut actual = packet();
        actual.stages[0].stage_id.clear();
        assert!(matches!(
            evaluate_calibration_packet(&actual),
            Err(CalibrationPacketError::EmptyStageIdentity)
        ));
    }
}
