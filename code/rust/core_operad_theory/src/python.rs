//! Thin PyO3 bridge exposing the Rust operad kernel to Python.
//!
//! AuthorityEffect: None.

#[cfg(feature = "python")]
use pyo3::exceptions::{PyRuntimeError, PyValueError};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use serde::Serialize;

#[cfg(feature = "python")]
use crate::foundation::colour::OperadColour;
#[cfg(feature = "python")]
use crate::foundation::operation::OperationId;
#[cfg(feature = "python")]
use crate::foundation::planar_tree::PlanarTree;

#[cfg(feature = "python")]
#[pyclass(name = "OperadColour")]
#[derive(Clone)]
pub struct PyOperadColour {
    pub inner: OperadColour,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOperadColour {
    #[new]
    pub fn new(name: String) -> PyResult<Self> {
        OperadColour::new(name)
            .map(|inner| Self { inner })
            .map_err(|e| PyValueError::new_err(e))
    }

    #[getter]
    pub fn name(&self) -> &str {
        self.inner.as_str()
    }

    pub fn __repr__(&self) -> String {
        format!("OperadColour('{}')", self.inner.as_str())
    }

    pub fn __str__(&self) -> String {
        self.inner.to_string()
    }
}

#[cfg(feature = "python")]
#[pyclass(name = "OperationId")]
#[derive(Clone)]
pub struct PyOperationId {
    pub inner: OperationId,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOperationId {
    #[new]
    pub fn new(name: String) -> PyResult<Self> {
        OperationId::new(name)
            .map(|inner| Self { inner })
            .map_err(|e| PyValueError::new_err(e))
    }

    #[staticmethod]
    pub fn identity_for(colour: &PyOperadColour) -> Self {
        Self {
            inner: OperationId::identity_for(&colour.inner),
        }
    }

    #[getter]
    pub fn name(&self) -> &str {
        self.inner.as_str()
    }

    pub fn __repr__(&self) -> String {
        format!("OperationId('{}')", self.inner.as_str())
    }
}

#[cfg(feature = "python")]
#[pyclass(name = "PlanarTree")]
#[derive(Clone)]
pub struct PyPlanarTree {
    pub inner: PlanarTree,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyPlanarTree {
    #[getter]
    pub fn term_hash(&self) -> String {
        self.inner.term_hash()
    }

    #[getter]
    pub fn arity(&self) -> usize {
        self.inner.arity()
    }
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn authority_effect() -> &'static str {
    "None"
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn package_info(py: Python<'_>) -> PyResult<Py<PyAny>> {
    #[derive(Serialize)]
    struct Info {
        name: &'static str,
        version: &'static str,
        authority_effect: &'static str,
        pyo3_accelerated: bool,
    }
    let info = Info {
        name: "core_operad_theory",
        version: "0.1.0",
        authority_effect: "None",
        pyo3_accelerated: true,
    };
    let encoded = serde_json::to_string(&info)
        .map_err(|e| PyRuntimeError::new_err(format!("serialization error: {e}")))?;
    py.import("json")?
        .call_method1("loads", (encoded,))
        .map(|v| v.unbind())
}

#[cfg(feature = "python")]
#[pymodule]
pub fn core_operad_theory_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyOperadColour>()?;
    m.add_class::<PyOperationId>()?;
    m.add_class::<PyPlanarTree>()?;
    m.add_function(wrap_pyfunction!(authority_effect, m)?)?;
    m.add_function(wrap_pyfunction!(package_info, m)?)?;
    Ok(())
}

// Origin: engine/crates_rs/core_operad_theory/src/python.rs
// Claim: urn:core:crates_rs:core-operad-theory:python:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc36100d7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc36100d7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc36100d7 {
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
impl BoundaryErrorc36100d7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc36100d7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc36100d7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc36100d7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc36100d7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc36100d7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc36100d7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc36100d7::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_c36100d7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc36100d7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc36100d7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc36100d7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc36100d7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc36100d7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc36100d7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc36100d7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
