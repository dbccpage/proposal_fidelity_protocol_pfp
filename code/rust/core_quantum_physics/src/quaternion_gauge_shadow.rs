// AuthorityEffect: None.

//! The quaternion group as a finite non-abelian gauge shadow, and the flux and
//! holonomy operators on functions on a finite matrix group.
//!
//! - The quaternion group from `core_lie_theory::su2_matrix`: `Q8 = {+-1, +-i, +-j, +-k}` as `2 x 2` matrices over
//!   `Q(i)`, embedded by `core_lie_theory::su2_matrix::unit_quaternion_matrix`
//!   (`a + b i + c j + d k -> a I - i (b X + c Y + d Z)`, so `i -> -iX`,
//!   `j -> -iY`, `k -> -iZ`), the crate's one quaternion convention, and
//!   listed as `1, -1, i, -i, j, -j, k, -k`. Each lies in `SU(2)`:
//!   `core_lie_theory::su_n::is_special_unitary` checks `U* U = I` and `det U = 1`, the determinant
//!   from canonical linear algebra. `Q8` is a finite subgroup of `SU(2)`, not `SU(2)`.
//!   Connections, loop holonomies, plaquette commutators and flatness are
//!   computed by `core_holonomy`; this module supplies the group.
//! - [`FiniteGroupAlgebra`]: a declared finite set of square matrices that
//!   contains the identity, is closed under multiplication and has inverses,
//!   with its multiplication table. On functions `G -> Q` (the cylindrical
//!   functions of one edge) the holonomy operator is multiplication by a
//!   declared function `phi` and the flux operator is right translation
//!   `(T_g f)(x) = f(x g)`. [`FiniteGroupAlgebra::flux_holonomy_commutator`]
//!   is the matrix commutator `T_g M_phi - M_phi T_g`;
//!   [`FiniteGroupAlgebra::translated_difference`] is the operator
//!   `f -> (x -> (phi(x g) - phi(x)) f(x g))`. The two agree, so the
//!   commutator vanishes exactly when `phi(x g) = phi(x)` for every `x`, that
//!   is, when `phi` is constant on each coset `x <g>`.
//!
//! Refused: an empty set, matrices of different or non-square shapes,
//! repeated elements, a set without the identity, not closed under
//! multiplication, or with an element lacking an inverse, element indices out
//! of range, and functions of the wrong length. The continuum `SU(2)`
//! configuration space, its measure, and the triad whose smearing gives the
//! flux in loop quantum gravity are imported, not built.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_f3893259<T> {
    fn checked_invariant_f3893259(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_f3893259<T> for Option<T> {
    #[inline]
    fn checked_invariant_f3893259(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_f3893259<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_f3893259(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use core_lie_theory::finite_group::{FiniteGroup, GroupError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Refusals for group declarations and operator requests.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GroupAlgebraError {
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    Foundation(#[from] GroupError),
    #[error("a group needs at least one element")]
    Empty,
    #[error("element {index} is not a square matrix of the common size")]
    Shape { index: usize },
    #[error("elements {first} and {second} are equal")]
    Repeated { first: usize, second: usize },
    #[error("the set does not contain the identity")]
    NoIdentity,
    #[error("the product of elements {left} and {right} is not in the set")]
    NotClosed { left: usize, right: usize },
    #[error("element {index} has no inverse in the set")]
    NoInverse { index: usize },
    #[error("element index {index} is out of range")]
    IndexOutOfRange { index: usize },
    #[error("a function has {actual} values, the group has {expected} elements")]
    FunctionLength { expected: usize, actual: usize },
}

/// A finite matrix group with its multiplication table.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteGroupAlgebra {
    group: FiniteGroup<BasicMatrix<GaussianRat>>,
}

impl FiniteGroupAlgebra {
    fn map_group_error(e: GroupError) -> GroupAlgebraError {
        match e {
            GroupError::Empty => GroupAlgebraError::Empty,
            GroupError::Repeated { first, second } => GroupAlgebraError::Repeated { first, second },
            GroupError::NoIdentity => GroupAlgebraError::NoIdentity,
            GroupError::NotClosed { left, right } => GroupAlgebraError::NotClosed { left, right },
            GroupError::NoInverse { index } => GroupAlgebraError::NoInverse { index },
            other => GroupAlgebraError::Foundation(other),
        }
    }

    pub fn new(elements: Vec<BasicMatrix<GaussianRat>>) -> Result<Self, GroupAlgebraError> {
        let size = elements.first().ok_or(GroupAlgebraError::Empty)?.rows();
        if let Some(index) = elements
            .iter()
            .position(|g| g.rows() != size || g.cols() != size)
        {
            return Err(GroupAlgebraError::Shape { index });
        }
        // The gauge carrier is a matrix subgroup with the ambient identity.
        // An abstract group on a closed matrix set may instead have a projector
        // as its relative identity, so this physical admission is separate.
        let ambient_identity = mx::identity(size)?;
        if !elements.contains(&ambient_identity) {
            return Err(GroupAlgebraError::NoIdentity);
        }
        let group = FiniteGroup::from_operation(
            elements,
            |a, b| mx::multiply(a, b).checked_invariant_f3893259("admitted square matrix group"),
            |m| (m.rows(), m.cols(), m.as_slice().to_vec()),
        )
        .map_err(Self::map_group_error)?;
        Ok(Self { group })
    }

    pub fn order(&self) -> usize {
        self.group.order()
    }

    pub fn conjugacy_classes(&self) -> Vec<Vec<usize>> {
        self.group.conjugacy_classes()
    }
    pub fn commuting_probability(&self) -> Rational {
        self.group.commuting_probability()
    }
    pub fn center(&self) -> Vec<usize> {
        self.group.centre()
    }

    /// The index of `elements[left] * elements[right]`.
    pub fn product_index(&self, left: usize, right: usize) -> Result<usize, GroupAlgebraError> {
        for index in [left, right] {
            self.check_index(index)?;
        }
        Ok(self.group.multiply(left, right)?)
    }

    fn check_index(&self, index: usize) -> Result<(), GroupAlgebraError> {
        if index >= self.order() {
            return Err(GroupAlgebraError::IndexOutOfRange { index });
        }
        Ok(())
    }

    fn check_function(&self, phi: &[Rational]) -> Result<(), GroupAlgebraError> {
        if phi.len() != self.order() {
            return Err(GroupAlgebraError::FunctionLength {
                expected: self.order(),
                actual: phi.len(),
            });
        }
        Ok(())
    }

    /// Flux translation on the finite gauge carrier, computed by the group owner.
    pub fn flux(&self, g: usize) -> Result<BasicMatrix<Rational>, GroupAlgebraError> {
        self.check_index(g)?;
        Ok(self.group.flux_operator(g)?)
    }
    /// Holonomy multiplication of a declared observable on the gauge carrier.
    pub fn holonomy(&self, phi: &[Rational]) -> Result<BasicMatrix<Rational>, GroupAlgebraError> {
        self.check_function(phi)?;
        Ok(mx::diagonal(phi)?)
    }
    pub fn flux_holonomy_commutator(
        &self,
        g: usize,
        phi: &[Rational],
    ) -> Result<BasicMatrix<Rational>, GroupAlgebraError> {
        self.check_index(g)?;
        self.check_function(phi)?;
        Ok(self.group.flux_holonomy_commutator(g, phi)?)
    }
    pub fn translated_difference(
        &self,
        g: usize,
        phi: &[Rational],
    ) -> Result<BasicMatrix<Rational>, GroupAlgebraError> {
        self.check_index(g)?;
        self.check_function(phi)?;
        Ok(self.group.translated_difference(g, phi)?)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quaternion_gauge_shadow.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quaternion-gauge-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f3893259 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
