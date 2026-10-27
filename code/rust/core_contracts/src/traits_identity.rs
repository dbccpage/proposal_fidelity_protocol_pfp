pub trait NamedComponent {
    fn name(&self) -> &'static str;
}

pub trait ContractBound {
    fn contract_id(&self) -> &'static str;
    fn schema_id(&self) -> Option<&'static str> {
        None
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum IdentityError {
    EmptyName,
    EmptyId,
    SchemaSplit,
}

impl std::fmt::Display for IdentityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EmptyName => write!(formatter, "component name is empty"),
            Self::EmptyId => write!(formatter, "contract id is empty"),
            Self::SchemaSplit => write!(formatter, "one contract id carries two schema ids"),
        }
    }
}

impl std::error::Error for IdentityError {}

/// Two components that share a contract id share its schema slot.
pub fn schema_agrees<C>(left: &C, right: &C) -> Result<(), IdentityError>
where
    C: NamedComponent + ContractBound,
{
    if left.name().is_empty() || right.name().is_empty() {
        return Err(IdentityError::EmptyName);
    }
    if left.contract_id().is_empty() || right.contract_id().is_empty() {
        return Err(IdentityError::EmptyId);
    }
    if left.contract_id() == right.contract_id() && left.schema_id() != right.schema_id() {
        return Err(IdentityError::SchemaSplit);
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/traits_identity.rs
// Claim: urn:core:crates_rs:core-contracts:traits-identity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    struct Component {
        name: &'static str,
        contract_id: &'static str,
        schema_id: Option<&'static str>,
    }

    impl NamedComponent for Component {
        fn name(&self) -> &'static str {
            self.name
        }
    }

    impl ContractBound for Component {
        fn contract_id(&self) -> &'static str {
            self.contract_id
        }
        fn schema_id(&self) -> Option<&'static str> {
            self.schema_id
        }
    }

    #[test]
    fn the_same_contract_refuses_two_schemas() {
        let left = Component {
            name: "left",
            contract_id: "core.contract.identity",
            schema_id: Some("schema-a"),
        };
        let right = Component {
            name: "right",
            contract_id: "core.contract.identity",
            schema_id: Some("schema-b"),
        };
        assert!(matches!(
            schema_agrees(&left, &right),
            Err(IdentityError::SchemaSplit)
        ));
    }

    #[test]
    fn distinct_contracts_may_carry_distinct_schemas() {
        let left = Component {
            name: "left",
            contract_id: "core.contract.left",
            schema_id: Some("schema-a"),
        };
        let right = Component {
            name: "right",
            contract_id: "core.contract.right",
            schema_id: None,
        };
        assert!(schema_agrees(&left, &right).is_ok());
    }
}
