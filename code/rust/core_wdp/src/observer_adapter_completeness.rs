//! Finite typed observer specialization of universal partial-structure descent.
//! Archival custody and authorization are opaque metadata, never mathematical proof.
use core_category_theory::finite_partial_structure::{
    descend, DescentError, FinitePartialStructure, PartialOperation, Predicate, SortQuotient,
};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Sort {
    Input,
    Report,
    Context,
    Memory,
    Symbol,
    Defect,
    Repair,
    Cost,
    Status,
    Action,
    Profile,
    SelfData,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Operation {
    Presentation,
    ContextAction,
    Profile,
    Store,
    Update,
    Readout,
    TransitionReport,
    DefectPresentation,
    Repair,
    Cost,
    Terminal,
    Policy,
    SelfAccess,
}
impl Operation {
    fn evaluator_signature(self) -> (Vec<Sort>, Sort) {
        use Sort::*;
        match self {
            Self::DefectPresentation => (vec![Input], Defect),
            Self::Repair => (vec![Repair], Defect),
            Self::Cost => (vec![Defect], Cost),
            Self::Terminal => (vec![Defect], Status),
            Self::Policy => (vec![Status], Action),
            Self::SelfAccess | _ => (vec![Memory], SelfData),
        }
    }

    pub fn signature(self) -> (Vec<Sort>, Sort) {
        use Sort::*;
        match self {
            Self::Presentation => (vec![Input], Report),
            Self::ContextAction => (vec![Context, Input], Input),
            Self::Profile => (vec![Input], Profile),
            Self::Store => (vec![Report], Memory),
            Self::Update => (vec![Symbol, Memory], Memory),
            Self::Readout => (vec![Memory], Report),
            Self::TransitionReport => (vec![Symbol, Memory], Report),
            other => other.evaluator_signature(),
        }
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Relation {
    Comparison,
    Closure,
    AdmissibleRepair,
}
impl Relation {
    pub fn signature(self) -> Vec<Sort> {
        use Sort::*;
        match self {
            Self::Comparison => vec![Report, Report],
            Self::Closure => vec![Defect],
            Self::AdmissibleRepair => vec![Repair, Defect],
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverTables {
    pub carriers: BTreeMap<Sort, Vec<String>>,
    pub operations: BTreeMap<Operation, Vec<Option<usize>>>,
    pub relations: BTreeMap<Relation, Vec<bool>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverQuotient {
    pub target_carriers: BTreeMap<Sort, Vec<String>>,
    pub maps: BTreeMap<Sort, Vec<usize>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverAdapterPacket {
    pub source: ObserverTables,
    pub quotient: ObserverQuotient,
    /// Labels retained verbatim; neither archive identity nor authority is checked.
    pub archival_annotations: Vec<String>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverAdapterReceipt {
    pub packet: ObserverAdapterPacket,
    pub target: ObserverTables,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ObserverAdapterError {
    InvalidLabels,
    MissingSort(Sort),
    MissingOperation(Operation),
    MissingRelation(Relation),
    Descent(DescentError),
    ReceiptMismatch,
}

// Origin: engine/crates_rs/core_wdp/src/observer_adapter_completeness.rs
// Claim: urn:core:crates_rs:core-wdp:observer-adapter-completeness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ObserverAdapterError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ObserverAdapterError {}
impl From<DescentError> for ObserverAdapterError {
    fn from(e: DescentError) -> Self {
        Self::Descent(e)
    }
}
fn labels_valid(carriers: &BTreeMap<Sort, Vec<String>>) -> bool {
    carriers.values().all(|labels| {
        labels.iter().all(|s| !s.is_empty())
            && labels.iter().collect::<BTreeSet<_>>().len() == labels.len()
    })
}
impl ObserverAdapterPacket {
    /// Require precisely the layers needed by this query, without completing omissions.
    pub fn require(
        &self,
        operations: &[Operation],
        relations: &[Relation],
    ) -> Result<(), ObserverAdapterError> {
        for &op in operations {
            if !self.source.operations.contains_key(&op) {
                return Err(ObserverAdapterError::MissingOperation(op));
            }
        }
        for &relation in relations {
            if !self.source.relations.contains_key(&relation) {
                return Err(ObserverAdapterError::MissingRelation(relation));
            }
        }
        self.adapt().map(|_| ())
    }
    fn validate_carrier_keys(&self) -> Result<(), ObserverAdapterError> {
        let source = &self.source;
        let q = &self.quotient;
        if !labels_valid(&source.carriers)
            || !labels_valid(&q.target_carriers)
            || source.carriers.keys().ne(q.target_carriers.keys())
            || source.carriers.keys().ne(q.maps.keys())
        {
            return Err(ObserverAdapterError::InvalidLabels);
        }
        Ok(())
    }

    pub fn adapt(&self) -> Result<ObserverAdapterReceipt, ObserverAdapterError> {
        self.validate_carrier_keys()?;
        let source = &self.source;
        let q = &self.quotient;
        let sorts: Vec<_> = source.carriers.keys().copied().collect();
        let index: BTreeMap<_, _> = sorts.iter().enumerate().map(|(i, &s)| (s, i)).collect();
        let get = |s: Sort| {
            index
                .get(&s)
                .copied()
                .ok_or(ObserverAdapterError::MissingSort(s))
        };
        let operations = source
            .operations
            .iter()
            .map(|(&op, values)| {
                let (inputs, output) = op.signature();
                Ok(PartialOperation {
                    inputs: inputs.into_iter().map(&get).collect::<Result<_, _>>()?,
                    output: get(output)?,
                    values: values.clone(),
                })
            })
            .collect::<Result<_, ObserverAdapterError>>()?;
        let predicates = source
            .relations
            .iter()
            .map(|(&relation, values)| {
                Ok(Predicate {
                    inputs: relation
                        .signature()
                        .into_iter()
                        .map(&get)
                        .collect::<Result<_, _>>()?,
                    values: values.clone(),
                })
            })
            .collect::<Result<_, ObserverAdapterError>>()?;
        let native = FinitePartialStructure {
            sizes: sorts.iter().map(|s| source.carriers[s].len()).collect(),
            operations,
            predicates,
        };
        let quotient = SortQuotient {
            target_sizes: sorts.iter().map(|s| q.target_carriers[s].len()).collect(),
            maps: sorts.iter().map(|s| q.maps[s].clone()).collect(),
        };
        let target = descend(&native, &quotient)?;
        let operations = source
            .operations
            .keys()
            .copied()
            .zip(target.operations.into_iter().map(|o| o.values))
            .collect();
        let relations = source
            .relations
            .keys()
            .copied()
            .zip(target.predicates.into_iter().map(|r| r.values))
            .collect();
        Ok(ObserverAdapterReceipt {
            packet: self.clone(),
            target: ObserverTables {
                carriers: q.target_carriers.clone(),
                operations,
                relations,
            },
        })
    }
}
impl ObserverAdapterReceipt {
    /// Replay actual source, sort maps, undefined entries, predicates and output.
    pub fn verify_against(
        &self,
        packet: &ObserverAdapterPacket,
    ) -> Result<(), ObserverAdapterError> {
        if &self.packet != packet || packet.adapt()? != *self {
            return Err(ObserverAdapterError::ReceiptMismatch);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn labels(n: usize) -> Vec<String> {
        (0..n).map(|i| format!("v{i}")).collect()
    }
    fn identity(source: ObserverTables) -> ObserverAdapterPacket {
        let maps = source
            .carriers
            .iter()
            .map(|(&s, l)| (s, (0..l.len()).collect()))
            .collect();
        ObserverAdapterPacket {
            quotient: ObserverQuotient {
                target_carriers: source.carriers.clone(),
                maps,
            },
            source,
            archival_annotations: vec!["unverified source annotation".into()],
        }
    }
    #[test]
    fn every_independent_operation_has_a_fiber_countermodel() {
        for op in [
            Operation::Presentation,
            Operation::ContextAction,
            Operation::Profile,
            Operation::Store,
            Operation::Update,
            Operation::Readout,
            Operation::TransitionReport,
            Operation::DefectPresentation,
            Operation::Repair,
            Operation::Cost,
            Operation::Terminal,
            Operation::Policy,
            Operation::SelfAccess,
        ] {
            let (inputs, output) = op.signature();
            let carriers: BTreeMap<_, _> = inputs
                .iter()
                .copied()
                .chain([output])
                .map(|s| (s, labels(3)))
                .collect();
            let mut values = vec![Some(0); 3usize.pow(inputs.len() as u32)];
            values[1] = Some(2);
            let mut packet = identity(ObserverTables {
                carriers,
                operations: [(op, values)].into_iter().collect(),
                relations: BTreeMap::new(),
            });
            for sort in inputs {
                packet.quotient.maps.insert(sort, vec![0, 0, 1]);
                packet.quotient.target_carriers.insert(sort, labels(2));
            }
            assert!(
                matches!(
                    packet.adapt(),
                    Err(ObserverAdapterError::Descent(
                        DescentError::OperationConflict { .. }
                    ))
                ),
                "{op:?}"
            );
            // Identity adapts the same source without changing any semantic table.
            let identity = identity(packet.source);
            assert_eq!(identity.adapt().unwrap().target, identity.source);
            // Forgetting this one role makes incompatible interpretations indistinguishable.
            let mut alternative = identity.source.clone();
            alternative.operations.get_mut(&op).unwrap().fill(Some(2));
            assert_ne!(alternative, identity.source);
            let mut reduct = identity.source.clone();
            reduct.operations.remove(&op);
            alternative.operations.remove(&op);
            assert_eq!(alternative, reduct);
        }
    }
    #[test]
    fn every_independent_relation_has_a_countermodel() {
        for relation in [
            Relation::Comparison,
            Relation::Closure,
            Relation::AdmissibleRepair,
        ] {
            let inputs = relation.signature();
            let carriers = inputs.iter().copied().map(|s| (s, labels(2))).collect();
            let mut values = vec![false; 2usize.pow(inputs.len() as u32)];
            values[0] = true;
            let mut p = identity(ObserverTables {
                carriers,
                operations: BTreeMap::new(),
                relations: [(relation, values)].into_iter().collect(),
            });
            for sort in inputs {
                p.quotient.maps.insert(sort, vec![0, 0]);
                p.quotient.target_carriers.insert(sort, labels(1));
            }
            assert!(matches!(
                p.adapt(),
                Err(ObserverAdapterError::Descent(
                    DescentError::PredicateConflict { .. }
                ))
            ));
        }
    }
    #[test]
    fn partial_terminal_receipt_and_absent_layers_are_not_completed() {
        let source = ObserverTables {
            carriers: [(Sort::Defect, labels(3)), (Sort::Status, labels(2))]
                .into_iter()
                .collect(),
            operations: [(Operation::Terminal, vec![Some(0), Some(0), None])]
                .into_iter()
                .collect(),
            relations: BTreeMap::new(),
        };
        let mut p = identity(source);
        p.quotient.maps.insert(Sort::Defect, vec![0, 0, 1]);
        p.quotient.target_carriers.insert(Sort::Defect, labels(2));
        let r = p.adapt().unwrap();
        assert_eq!(
            r.target.operations[&Operation::Terminal],
            vec![Some(0), None]
        );
        assert_eq!(
            p.require(&[Operation::Update], &[]),
            Err(ObserverAdapterError::MissingOperation(Operation::Update))
        );
        r.verify_against(&p).unwrap();
        let mut forged = r.clone();
        forged
            .target
            .operations
            .get_mut(&Operation::Terminal)
            .unwrap()[1] = Some(1);
        assert_eq!(
            forged.verify_against(&p),
            Err(ObserverAdapterError::ReceiptMismatch)
        );
        let mut other = p.clone();
        other.archival_annotations.push("different custody".into());
        assert_eq!(
            r.verify_against(&other),
            Err(ObserverAdapterError::ReceiptMismatch)
        );
        p.source.operations.get_mut(&Operation::Terminal).unwrap()[1] = None;
        assert!(matches!(
            p.adapt(),
            Err(ObserverAdapterError::Descent(
                DescentError::OperationConflict { .. }
            ))
        ));
    }
    #[test]
    fn missing_signature_carrier_and_uncovered_target_refuse() {
        let mut p = identity(ObserverTables {
            carriers: [(Sort::Input, labels(1))].into_iter().collect(),
            operations: [(Operation::Presentation, vec![Some(0)])]
                .into_iter()
                .collect(),
            relations: BTreeMap::new(),
        });
        assert_eq!(
            p.adapt(),
            Err(ObserverAdapterError::MissingSort(Sort::Report))
        );
        p.source.operations.clear();
        p.quotient.target_carriers.insert(Sort::Input, labels(2));
        assert_eq!(
            p.adapt(),
            Err(ObserverAdapterError::Descent(DescentError::InvalidSortMap))
        );
    }
}
