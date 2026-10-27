//! Exact adjoint braid action on a declared list of Majorana generators.
//!
//! This is the sparse signed-permutation representation from the Majorana
//! paper's `majorana_braid_exact.py`. Row `a` represents the image of
//! `gamma_a`: the positive elementary braid sends `gamma_j` to
//! `gamma_(j+1)` and `gamma_(j+1)` to `-gamma_j`. A word is evaluated in
//! written matrix order, `R_j1 R_j2 ...`; its spin representation and global
//! phase are separate data, supplied by `FockCarrier::braid_unitary`.
//!
//! AuthorityEffect: None.

/// Explicit resource bound for the sparse representation, independent of the
/// much smaller exponentially sized Fock carrier bound.
pub const MAX_BRAID_MODES: usize = 1_048_576;

/// A signed, one-indexed image of one Majorana generator.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SignedMajorana {
    pub mode: usize,
    pub sign: i8,
}

/// Invalid declarations are refused before an action can be constructed.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BraidActionError {
    #[error("the braid action requires 2..={MAX_BRAID_MODES} modes, not {count}")]
    ModeCount { count: usize },
    #[error("mode {mode} is outside 1..={count}")]
    Mode { mode: usize, count: usize },
    #[error("braid index {index} is outside 1..{count}")]
    BraidIndex { index: usize, count: usize },
    #[error("the image sign at row {row} is {sign}, rather than +1 or -1")]
    Sign { row: usize, sign: i8 },
    #[error("mode {mode} occurs more than once in the image")]
    DuplicateImage { mode: usize },
    #[error("the actions have different mode counts: {left} and {right}")]
    Dimension { left: usize, right: usize },
    #[error("the declared braid action exceeds available allocation capacity")]
    Allocation,
}

/// An admitted signed permutation. Its representation has linear storage and
/// every admitted action is exactly orthogonal.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MajoranaBraidAction {
    images: Vec<SignedMajorana>,
    positions: Vec<usize>,
    determinant: i8,
}

fn validate_count(count: usize) -> Result<(), BraidActionError> {
    if !(2..=MAX_BRAID_MODES).contains(&count) {
        return Err(BraidActionError::ModeCount { count });
    }
    Ok(())
}

fn reserve<T>(count: usize) -> Result<Vec<T>, BraidActionError> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(count)
        .map_err(|_| BraidActionError::Allocation)?;
    Ok(result)
}

fn validate_and_record_image(
    row: usize,
    image: SignedMajorana,
    count: usize,
    visited: &mut [bool],
    positions: &mut [usize],
) -> Result<i8, BraidActionError> {
    if image.sign != 1 && image.sign != -1 {
        return Err(BraidActionError::Sign {
            row: row + 1,
            sign: image.sign,
        });
    }
    if image.mode == 0 || image.mode > count {
        return Err(BraidActionError::Mode {
            mode: image.mode,
            count,
        });
    }
    if visited[image.mode - 1] {
        return Err(BraidActionError::DuplicateImage { mode: image.mode });
    }
    visited[image.mode - 1] = true;
    positions[image.mode - 1] = row;
    Ok(image.sign)
}

fn trace_cycle_length(
    start: usize,
    images: &[SignedMajorana],
    visited: &mut [bool],
) -> usize {
    let mut position = start;
    let mut length = 0;
    while !visited[position] {
        visited[position] = true;
        position = images[position].mode - 1;
        length += 1;
    }
    length
}

impl MajoranaBraidAction {
    /// Admit an externally supplied signed permutation. Arbitrary rational
    /// orthogonal matrices are not part of this representation.
    pub fn try_from_images(images: Vec<SignedMajorana>) -> Result<Self, BraidActionError> {
        let count = images.len();
        validate_count(count)?;
        let mut visited = reserve(count)?;
        visited.resize(count, false);
        let mut positions = reserve(count)?;
        positions.resize(count, 0);
        let mut determinant = 1;
        for (row, &image) in images.iter().enumerate() {
            determinant *=
                validate_and_record_image(row, image, count, &mut visited, &mut positions)?;
        }
        visited.fill(false);
        // A cycle of length l contributes (-1)^(l-1) to the permutation sign.
        for start in 0..count {
            if !visited[start] && trace_cycle_length(start, &images, &mut visited) % 2 == 0 {
                determinant = -determinant;
            }
        }
        Ok(Self {
            images,
            positions,
            determinant,
        })
    }

    pub fn identity(count: usize) -> Result<Self, BraidActionError> {
        validate_count(count)?;
        let mut images = reserve(count)?;
        images.extend((1..=count).map(|mode| SignedMajorana { mode, sign: 1 }));
        let mut positions = reserve(count)?;
        positions.extend(0..count);
        Ok(Self {
            images,
            positions,
            determinant: 1,
        })
    }

    pub fn elementary(count: usize, index: usize, inverse: bool) -> Result<Self, BraidActionError> {
        let mut result = Self::identity(count)?;
        result.append(index, inverse)?;
        Ok(result)
    }

    /// Evaluate a braid word in written matrix order using O(count) memory and
    /// O(count + word length) work.
    pub fn from_word(count: usize, word: &[(usize, bool)]) -> Result<Self, BraidActionError> {
        let mut result = Self::identity(count)?;
        for &(index, inverse) in word {
            result.append(index, inverse)?;
        }
        Ok(result)
    }

    /// Right multiply the current row-action matrix by one elementary braid.
    /// Invalid indices leave the action unchanged.
    pub fn append(&mut self, index: usize, inverse: bool) -> Result<(), BraidActionError> {
        if index == 0 || index >= self.images.len() {
            return Err(BraidActionError::BraidIndex {
                index,
                count: self.images.len(),
            });
        }
        let left = self.positions[index - 1];
        let right = self.positions[index];
        self.images[left].mode = index + 1;
        self.images[right].mode = index;
        if inverse {
            self.images[left].sign = -self.images[left].sign;
        } else {
            self.images[right].sign = -self.images[right].sign;
        }
        self.positions.swap(index - 1, index);
        Ok(())
    }

    pub fn mode_count(&self) -> usize {
        self.images.len()
    }

    pub fn images(&self) -> &[SignedMajorana] {
        &self.images
    }

    pub fn image(&self, mode: usize) -> Result<SignedMajorana, BraidActionError> {
        if mode == 0 || mode > self.mode_count() {
            return Err(BraidActionError::Mode {
                mode,
                count: self.mode_count(),
            });
        }
        Ok(self.images[mode - 1])
    }

    /// Exact determinant of the row-action matrix. The sign equals the action
    /// on the product of all Majoranas; elementary braids preserve this parity.
    pub fn determinant_sign(&self) -> i8 {
        self.determinant
    }

    /// Matrix product `self * other` in the declared row-image convention.
    pub fn compose(&self, other: &Self) -> Result<Self, BraidActionError> {
        if self.mode_count() != other.mode_count() {
            return Err(BraidActionError::Dimension {
                left: self.mode_count(),
                right: other.mode_count(),
            });
        }
        let mut images = reserve(self.mode_count())?;
        let mut positions = reserve(self.mode_count())?;
        positions.resize(self.mode_count(), 0);
        for image in &self.images {
            let next = other.images[image.mode - 1];
            positions[next.mode - 1] = images.len();
            images.push(SignedMajorana {
                mode: next.mode,
                sign: image.sign * next.sign,
            });
        }
        Ok(Self {
            images,
            positions,
            determinant: self.determinant * other.determinant,
        })
    }

    pub fn inverse(&self) -> Result<Self, BraidActionError> {
        let mut result = Self::identity(self.mode_count())?;
        for (row, image) in self.images.iter().enumerate() {
            result.images[image.mode - 1] = SignedMajorana {
                mode: row + 1,
                sign: image.sign,
            };
            result.positions[row] = image.mode - 1;
        }
        result.determinant = self.determinant;
        Ok(result)
    }
}

// Origin: engine/crates_rs/core_majorana/src/braid_action.rs
// Claim: urn:core:crates_rs:core-majorana:braid-action:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::majorana_fock_algebra::{gi, FockCarrier};
    use linear_algebra::exact_field::{involution, matrix};

    #[test]
    fn sparse_action_matches_fock_adjoint_for_each_generator_and_inverse() {
        for sites in 1..=3 {
            let fock = FockCarrier::new(sites).unwrap();
            for index in 1..2 * sites {
                for inverse in [false, true] {
                    let mut u = fock.braid_unitary(index).unwrap();
                    if inverse {
                        u = involution::adjoint(&u).unwrap();
                    }
                    let adjoint = involution::adjoint(&u).unwrap();
                    let action =
                        MajoranaBraidAction::elementary(2 * sites, index, inverse).unwrap();
                    for mode in 1..=2 * sites {
                        let image = action.image(mode).unwrap();
                        let actual = matrix::multiply(
                            &matrix::multiply(&u, &fock.majorana(mode).unwrap()).unwrap(),
                            &adjoint,
                        )
                        .unwrap();
                        let expected = matrix::scale(
                            &fock.majorana(image.mode).unwrap(),
                            &gi(image.sign.into(), 0),
                        )
                        .unwrap();
                        assert_eq!(actual, expected);
                    }
                }
            }
        }
    }

    #[test]
    fn yang_baxter_far_commutativity_inverse_and_parity() {
        for count in 3..=10 {
            for index in 1..count - 1 {
                assert_eq!(
                    MajoranaBraidAction::from_word(
                        count,
                        &[(index, false), (index + 1, false), (index, false)]
                    )
                    .unwrap(),
                    MajoranaBraidAction::from_word(
                        count,
                        &[(index + 1, false), (index, false), (index + 1, false)]
                    )
                    .unwrap(),
                );
            }
            for i in 1..count {
                for j in i + 2..count {
                    assert_eq!(
                        MajoranaBraidAction::from_word(count, &[(i, false), (j, false)]).unwrap(),
                        MajoranaBraidAction::from_word(count, &[(j, false), (i, false)]).unwrap(),
                    );
                }
            }
            let word = [(1, false), (count - 1, true), (2, false), (1, true)];
            let action = MajoranaBraidAction::from_word(count, &word).unwrap();
            assert_eq!(action.determinant_sign(), 1);
            assert_eq!(
                action.compose(&action.inverse().unwrap()).unwrap(),
                MajoranaBraidAction::identity(count).unwrap()
            );
            let parsed = MajoranaBraidAction::try_from_images(action.images().to_vec()).unwrap();
            assert_eq!(parsed, action);
        }
    }

    #[test]
    fn matrix_order_and_non_braid_permutation_determinants() {
        let r1 = MajoranaBraidAction::elementary(4, 1, false).unwrap();
        let r2 = MajoranaBraidAction::elementary(4, 2, false).unwrap();
        assert_eq!(
            r1.compose(&r2).unwrap(),
            MajoranaBraidAction::from_word(4, &[(1, false), (2, false)]).unwrap()
        );
        assert_ne!(r1.compose(&r2).unwrap(), r2.compose(&r1).unwrap());
        let reflection = MajoranaBraidAction::try_from_images(vec![
            SignedMajorana { mode: 2, sign: 1 },
            SignedMajorana { mode: 1, sign: 1 },
        ])
        .unwrap();
        assert_eq!(reflection.determinant_sign(), -1);
        assert_eq!(reflection.inverse().unwrap().determinant_sign(), -1);
    }

    #[test]
    fn invalid_candidates_are_refused_and_append_does_not_mutate() {
        assert!(matches!(
            MajoranaBraidAction::identity(1),
            Err(BraidActionError::ModeCount { .. })
        ));
        assert!(matches!(
            MajoranaBraidAction::identity(usize::MAX),
            Err(BraidActionError::ModeCount { .. })
        ));
        assert!(matches!(
            MajoranaBraidAction::try_from_images(vec![SignedMajorana { mode: 1, sign: 1 }; 2]),
            Err(BraidActionError::DuplicateImage { .. })
        ));
        assert!(matches!(
            MajoranaBraidAction::try_from_images(vec![
                SignedMajorana { mode: 1, sign: 0 },
                SignedMajorana { mode: 2, sign: 1 }
            ]),
            Err(BraidActionError::Sign { .. })
        ));
        assert!(matches!(
            MajoranaBraidAction::try_from_images(vec![
                SignedMajorana { mode: 1, sign: 1 },
                SignedMajorana { mode: 3, sign: 1 }
            ]),
            Err(BraidActionError::Mode { .. })
        ));
        let mut action = MajoranaBraidAction::identity(4).unwrap();
        let before = action.clone();
        // Kills: appending an out-of-range braid and still mutating the images.
        assert_eq!(
            action.append(4, false),
            Err(BraidActionError::BraidIndex { index: 4, count: 4 })
        );
        assert_eq!(action, before);
        assert_eq!(
            action.image(0),
            Err(BraidActionError::Mode { mode: 0, count: 4 })
        );
        assert_eq!(
            action.compose(&MajoranaBraidAction::identity(2).unwrap()),
            Err(BraidActionError::Dimension { left: 4, right: 2 })
        );
    }

    #[test]
    fn thousands_of_modes_need_only_sparse_storage() {
        let action =
            MajoranaBraidAction::from_word(4096, &[(1, false), (4095, false), (1, true)]).unwrap();
        assert_eq!(action.mode_count(), 4096);
        assert_eq!(
            action.image(1).unwrap(),
            SignedMajorana { mode: 1, sign: 1 }
        );
        assert_eq!(
            action.image(4095).unwrap(),
            SignedMajorana {
                mode: 4096,
                sign: 1
            }
        );
    }
}
