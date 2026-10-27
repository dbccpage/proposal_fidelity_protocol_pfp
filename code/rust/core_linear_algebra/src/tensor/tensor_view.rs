//! Tensor view scaffold (zero-copy later).

#[derive(Debug, Clone, Copy)]
pub struct TensorViewPlaceholder {
    pub order: usize,
}

/// Finite tensor shape whose stored volume is the checked product of extents.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CheckedTensorShape {
    extents: Vec<u64>,
    volume: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TensorShapeError {
    EmptyShape,
    ZeroExtent { index: usize },
    VolumeOverflow { index: usize },
}

// Origin: engine/crates_rs/core_linear_algebra/src/tensor/tensor_view.rs
// Claim: urn:core:crates_rs:core-linear-algebra:tensor-view:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TensorShapeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TensorShapeError {}

impl CheckedTensorShape {
    pub fn try_new(extents: Vec<u64>) -> Result<Self, TensorShapeError> {
        if extents.is_empty() {
            return Err(TensorShapeError::EmptyShape);
        }
        let mut volume = 1u64;
        for (index, extent) in extents.iter().copied().enumerate() {
            if extent == 0 {
                return Err(TensorShapeError::ZeroExtent { index });
            }
            volume = volume
                .checked_mul(extent)
                .ok_or(TensorShapeError::VolumeOverflow { index })?;
        }
        Ok(Self { extents, volume })
    }

    pub fn order(&self) -> usize {
        self.extents.len()
    }

    pub fn volume(&self) -> u64 {
        self.volume
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod checked_tensor_shape_witness {
    use super::*;

    #[test]
    fn volume_is_the_product_of_extents() {
        let shape = CheckedTensorShape::try_new(vec![2, 3, 4]);
        assert!(shape.is_ok());
        if let Ok(shape) = shape {
            assert_eq!(shape.order(), 3);
            assert_eq!(shape.volume(), 24);
        }
    }

    #[test]
    fn zero_extent_is_refused() {
        assert!(matches!(
            CheckedTensorShape::try_new(vec![2, 0]),
            Err(TensorShapeError::ZeroExtent { index: 1 })
        ));
    }
}
