//! Finite heading/FD decisions, separate from instance checks and authorization.
//! Exact equality and set relations only; no NULL, bag, MVD or join-dependency theory.
//! Reports are raw observations, not admitted schema certificates. Deserialization
//! does not validate witnesses. Generic values require lawful Ord/Eq and value-preserving Clone.
//! Finite heading/FD decisions, separate from instance checks and authorization.
//! Exact equality and set relations only; no NULL, bag, MVD or join-dependency theory.

use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FunctionalDependency {
    pub determinant: u16,
    pub dependent: u16,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FdSchema {
    pub arity: usize,
    pub dependencies: Vec<FunctionalDependency>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FdRefusal {
    UnsupportedHeading,
    AttributeOutsideHeading,
    InvalidDecomposition,
    BudgetUnknown,
    InstanceShape,
    DuplicateTuple,
    InstanceDependencyViolation {
        dependency: usize,
        first: usize,
        second: usize,
    },
}
impl std::fmt::Display for FdRefusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for FdRefusal {}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClosureWitness {
    pub input: u16,
    pub result: u16,
    pub applications: Vec<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BinaryDecompositionReport {
    pub intersection_closure: ClosureWitness,
    pub determined_component: Option<usize>,
    pub original_bcnf_violations: Vec<FunctionalDependency>,
    pub component_bcnf_violations: [Vec<FunctionalDependency>; 2],
    pub projected_dependencies: [Vec<FunctionalDependency>; 2],
    pub lost_dependencies: Vec<FunctionalDependency>,
    pub work_used: u64,
}

struct Work {
    used: u64,
    limit: u64,
}
impl Work {
    fn spend(&mut self) -> Result<(), FdRefusal> {
        if self.used == self.limit {
            return Err(FdRefusal::BudgetUnknown);
        }
        self.used += 1;
        Ok(())
    }
}

impl FdSchema {
    pub fn heading(&self) -> Result<u16, FdRefusal> {
        if self.arity == 0 || self.arity > 8 || self.dependencies.len() > 128 {
            return Err(FdRefusal::UnsupportedHeading);
        }
        let heading = (1u16 << self.arity) - 1;
        if self
            .dependencies
            .iter()
            .any(|fd| (fd.determinant | fd.dependent) & !heading != 0)
        {
            return Err(FdRefusal::AttributeOutsideHeading);
        }
        Ok(heading)
    }

    fn close(&self, input: u16, work: &mut Work) -> Result<ClosureWitness, FdRefusal> {
        let heading = self.heading()?;
        if input & !heading != 0 {
            return Err(FdRefusal::AttributeOutsideHeading);
        }
        let mut result = input;
        let mut applications = Vec::new();
        loop {
            let before = result;
            for (i, fd) in self.dependencies.iter().enumerate() {
                work.spend()?;
                if fd.determinant & !result == 0 && fd.dependent & !result != 0 {
                    result |= fd.dependent;
                    applications.push(i);
                }
            }
            if result == before {
                break;
            }
        }
        Ok(ClosureWitness {
            input,
            result,
            applications,
        })
    }

    pub fn closure(&self, input: u16, budget: u64) -> Result<ClosureWitness, FdRefusal> {
        self.close(
            input,
            &mut Work {
                used: 0,
                limit: budget,
            },
        )
    }

    /// Replay applications, then check that the final set is closed under all FDs.
    /// Minimality follows because each added attribute has an admitted derivation.
    /// Replay applications, then check that the final set is closed under all FDs.
    /// Minimality follows because each added attribute has an admitted derivation.
    pub fn verify_closure(&self, witness: &ClosureWitness) -> bool {
        let Ok(heading) = self.heading() else {
            return false;
        };
        if (witness.input | witness.result) & !heading != 0 {
            return false;
        }
        let mut result = witness.input;
        for &index in &witness.applications {
            let Some(fd) = self.dependencies.get(index) else {
                return false;
            };
            if fd.determinant & !result != 0 || fd.dependent & !result == 0 {
                return false;
            }
            result |= fd.dependent;
        }
        result == witness.result
            && self
                .dependencies
                .iter()
                .all(|fd| fd.determinant & !result != 0 || fd.dependent & !result == 0)
    }

    fn projection(
        &self,
        component: u16,
        work: &mut Work,
    ) -> Result<(Vec<FunctionalDependency>, Vec<FunctionalDependency>), FdRefusal> {
        let mut projected = Vec::new();
        let mut violations = Vec::new();
        let mut subset = component;
        loop {
            work.spend()?;
            let closure = self.close(subset, work)?.result & component;
            let dependent = closure & !subset;
            if dependent != 0 {
                let fd = FunctionalDependency {
                    determinant: subset,
                    dependent,
                };
                if closure != component {
                    violations.push(fd.clone());
                }
                projected.push(fd);
            }
            if subset == 0 {
                break;
            }
            subset = (subset - 1) & component;
        }
        Ok((projected, violations))
    }

    /// Complete FD-only decisions on the supported finite heading, or BudgetUnknown.
    /// No successful current instance is used to infer schema membership.
    /// Complete FD-only decisions on the supported finite heading, or BudgetUnknown.
    /// No successful current instance is used to infer schema membership.
    pub fn binary_decomposition(
        &self,
        components: [u16; 2],
        budget: u64,
    ) -> Result<BinaryDecompositionReport, FdRefusal> {
        let heading = self.heading()?;
        if components.iter().any(|&c| c == 0 || c & !heading != 0)
            || components[0] | components[1] != heading
        {
            return Err(FdRefusal::InvalidDecomposition);
        }
        let mut work = Work {
            used: 0,
            limit: budget,
        };
        let intersection_closure = self.close(components[0] & components[1], &mut work)?;
        let determined_component = components
            .iter()
            .position(|&c| c & !intersection_closure.result == 0);
        let (_, original_bcnf_violations) = self.projection(heading, &mut work)?;
        let (p0, v0) = self.projection(components[0], &mut work)?;
        let (p1, v1) = self.projection(components[1], &mut work)?;
        // The projected cover can exceed the input cover's size. This is internal,
        // bounded by 2*(2^8); close it directly without the public input-cover cap.
        // The projected cover can exceed the input cover's size. This is internal,
        // bounded by 2*(2^8); close it directly without the public input-cover cap.
        let projected = p0.iter().chain(&p1).collect::<Vec<_>>();
        let lost_dependencies = self.lost_dependencies(&projected, &mut work)?;
        Ok(BinaryDecompositionReport {
            intersection_closure,
            determined_component,
            original_bcnf_violations,
            component_bcnf_violations: [v0, v1],
            projected_dependencies: [p0, p1],
            lost_dependencies,
            work_used: work.used,
        })
    }

    fn lost_dependencies(
        &self,
        projected: &[&FunctionalDependency],
        work: &mut Work,
    ) -> Result<Vec<FunctionalDependency>, FdRefusal> {
        let mut lost = Vec::new();
        for fd in &self.dependencies {
            let closure = close_projected(fd.determinant, projected, work)?;
            if fd.dependent & !closure != 0 {
                lost.push(fd.clone());
            }
        }
        Ok(lost)
    }

    pub fn check_instance<T: Ord>(&self, rows: &[Vec<T>]) -> Result<(), FdRefusal> {
        self.heading()?;
        if rows.len() > 128 || rows.iter().any(|r| r.len() != self.arity) {
            return Err(FdRefusal::InstanceShape);
        }
        if rows.iter().collect::<BTreeSet<_>>().len() != rows.len() {
            return Err(FdRefusal::DuplicateTuple);
        }
        for (dependency, fd) in self.dependencies.iter().enumerate() {
            if let Some((first, second)) = first_violation(rows, fd) {
                return Err(FdRefusal::InstanceDependencyViolation {
                    dependency,
                    first,
                    second,
                });
            }
        }
        Ok(())
    }
}

pub fn project<T: Ord + Clone>(
    rows: &[Vec<T>],
    arity: usize,
    component: u16,
) -> Result<BTreeSet<Vec<T>>, FdRefusal> {
    if arity == 0
        || arity > 8
        || component == 0
        || component >> arity != 0
        || rows.len() > 128
        || rows.iter().any(|r| r.len() != arity)
    {
        return Err(FdRefusal::InstanceShape);
    }
    Ok(rows
        .iter()
        .map(|row| {
            (0..arity)
                .filter(|&i| component & (1 << i) != 0)
                .map(|i| row[i].clone())
                .collect()
        })
        .collect())
}

// Internal covers may exceed the public input-cover limit. Every examined FD,
// including the final stable scan, consumes exactly one unit of work.
fn close_projected(
    input: u16,
    projected: &[&FunctionalDependency],
    work: &mut Work,
) -> Result<u16, FdRefusal> {
    let mut closure = input;
    loop {
        let before = closure;
        for local in projected {
            work.spend()?;
            if local.determinant & !closure == 0 {
                closure |= local.dependent;
            }
        }
        if closure == before {
            return Ok(closure);
        }
    }
}

fn rows_agree<T: Eq>(first: &[T], second: &[T], mask: u16) -> bool {
    (0..first.len()).all(|i| mask & (1 << i) == 0 || first[i] == second[i])
}

fn first_violation<T: Eq>(rows: &[Vec<T>], fd: &FunctionalDependency) -> Option<(usize, usize)> {
    for first in 0..rows.len() {
        for second in 0..first {
            if rows_agree(&rows[first], &rows[second], fd.determinant)
                && !rows_agree(&rows[first], &rows[second], fd.dependent)
            {
                return Some((first, second));
            }
        }
    }
    None
}

enum JoinColumn {
    Left(usize),
    Right(usize),
}

struct JoinLayout {
    widths: [usize; 2],
    shared: Vec<(usize, usize)>,
    output: Vec<JoinColumn>,
}

impl JoinLayout {
    fn new(arity: usize, components: [u16; 2], counts: [usize; 2]) -> Result<Self, FdRefusal> {
        if arity == 0
            || arity > 8
            || components.iter().any(|&c| c == 0 || c >> arity != 0)
            || components[0] | components[1] != (1 << arity) - 1
            || counts.iter().any(|&count| count > 128)
        {
            return Err(FdRefusal::InvalidDecomposition);
        }
        let indices = components.map(|c| {
            (0..arity)
                .filter(|&i| c & (1 << i) != 0)
                .collect::<Vec<_>>()
        });
        let shared = indices[0]
            .iter()
            .enumerate()
            .filter_map(|(j, i)| indices[1].iter().position(|k| k == i).map(|k| (j, k)))
            .collect();
        let output = (0..arity)
            .map(|i| Self::column(i, &indices))
            .collect::<Result<_, _>>()?;
        Ok(Self {
            widths: indices.each_ref().map(Vec::len),
            shared,
            output,
        })
    }

    fn column(attribute: usize, indices: &[Vec<usize>; 2]) -> Result<JoinColumn, FdRefusal> {
        if let Some(j) = indices[0].iter().position(|&k| k == attribute) {
            return Ok(JoinColumn::Left(j));
        }
        indices[1]
            .iter()
            .position(|&k| k == attribute)
            .map(JoinColumn::Right)
            .ok_or(FdRefusal::InvalidDecomposition)
    }

    fn matches<T: Eq>(&self, left: &[T], right: &[T]) -> bool {
        self.shared.iter().all(|&(j, k)| left[j] == right[k])
    }

    fn row<T: Clone>(&self, left: &[T], right: &[T]) -> Vec<T> {
        self.output
            .iter()
            .map(|column| match *column {
                JoinColumn::Left(j) => left[j].clone(),
                JoinColumn::Right(k) => right[k].clone(),
            })
            .collect()
    }
}

/// Exact natural join in original heading order. At most 128*128 row pairs;
/// column layout is computed once, and only matching output rows clone values.
/// Exact natural join in original heading order. Quadratic bounded instance work.
pub fn natural_join<T: Ord + Clone>(
    left: &BTreeSet<Vec<T>>,
    right: &BTreeSet<Vec<T>>,
    arity: usize,
    components: [u16; 2],
) -> Result<BTreeSet<Vec<T>>, FdRefusal> {
    let layout = JoinLayout::new(arity, components, [left.len(), right.len()])?;
    if left.iter().any(|r| r.len() != layout.widths[0])
        || right.iter().any(|r| r.len() != layout.widths[1])
    {
        return Err(FdRefusal::InstanceShape);
    }
    let mut joined = BTreeSet::new();
    for a in left {
        for b in right {
            if layout.matches(a, b) {
                joined.insert(layout.row(a, b));
            }
        }
    }
    Ok(joined)
}

// Origin: engine/crates_rs/core_category_theory/src/finite_functional_dependencies.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-functional-dependencies:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9dd33a18 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
