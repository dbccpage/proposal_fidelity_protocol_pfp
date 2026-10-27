//! Payload schemas for the sub-colours: what a value on a `Colour.subcolour` wire looks like.
//!
//! A colour says only that a wire carries an Audit; a sub-colour schema says which shape of
//! Audit, in the JSON Schema subset the resolver checks at run time (`type`, `properties`,
//! `required`, `additionalProperties`, `items`, `enum`, `const`, `pattern`). Every
//! `operad_subcolour` value has exactly one schema here; a crate test enforces it.

/// `(sub-colour, JSON Schema)` in the order of the `operad_subcolour` values.
pub const SUBCOLOUR_SCHEMAS: &[(&str, &str)] = &[
    (
        "Audit.hype_hits",
        r#"{"type":"array","items":{"type":"object","required":["gate","severity","path","line","message"],"additionalProperties":false,"properties":{"gate":{"type":"string"},"severity":{"enum":["BLOCK","WARN"]},"path":{"type":"string"},"line":{"type":"integer"},"message":{"type":"string"}}}}"#,
    ),
    (
        "Audit.lint_diff",
        r#"{"type":"array","items":{"type":"object","required":["finding","suggestion","applied"],"additionalProperties":false,"properties":{"finding":{"type":"object"},"suggestion":{"type":"string"},"applied":{"const":false}}}}"#,
    ),
    (
        "Audit.sfh_findings",
        r#"{"type":"array","items":{"type":"object","required":["rule_id","file_path","line_number","column_number","message","snippet","severity","authority_effect"],"additionalProperties":false,"properties":{"rule_id":{"type":"string","pattern":"^SFH-"},"file_path":{"type":"string"},"line_number":{"type":"integer"},"column_number":{"type":"integer"},"message":{"type":"string"},"snippet":{"type":"string"},"severity":{"type":"string"},"authority_effect":{"const":"None"}}}}"#,
    ),
    (
        "Audit.shadow_violations",
        r#"{"type":"array","items":{"type":"object","required":["code","path"],"additionalProperties":false,"properties":{"code":{"const":"STDLIB_SHADOW"},"path":{"type":"string"}}}}"#,
    ),
    (
        "Audit.layout_findings",
        r#"{"type":"array","items":{"type":"object","required":["code","path"],"additionalProperties":false,"properties":{"code":{"const":"UNSCOPED_TEST"},"path":{"type":"string"}}}}"#,
    ),
    (
        "Audit.verdict",
        r#"{"type":"object","required":["status","ledger","claim","scope"],"additionalProperties":false,"properties":{"status":{"enum":["SOURCE_BINDINGS_MATCH","REFUTED"]},"ledger":{"type":"object"},"claim":{},"scope":{"type":"string"}}}"#,
    ),
    (
        "Code.purged",
        r#"{"type":"object","required":["sources","input_digest","output_digest"],"additionalProperties":false,"properties":{"sources":{"type":"object","additionalProperties":{"type":"string"}},"input_digest":{"type":"string"},"output_digest":{"type":"string"}}}"#,
    ),
    (
        "Ledger.source_hashes",
        r#"{"type":"object","required":["sources","omitted_variables"],"additionalProperties":false,"properties":{"sources":{"type":"object","additionalProperties":{"type":"string","pattern":"^[0-9a-f]{64}$"}},"omitted_variables":{"type":"array"}}}"#,
    ),
];

/// The schema for one sub-colour, if it has one.
pub fn schema_of(subcolour: &str) -> Option<&'static str> {
    SUBCOLOUR_SCHEMAS
        .iter()
        .find(|(name, _)| *name == subcolour)
        .map(|(_, schema)| *schema)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::type_by_id;

    #[test]
    fn every_subcolour_has_exactly_one_schema() {
        let values = type_by_id("operad_subcolour").expect("registered").values;
        let names: Vec<&str> = SUBCOLOUR_SCHEMAS.iter().map(|(name, _)| *name).collect();
        assert_eq!(names, values.to_vec());
    }

    #[test]
    fn every_schema_is_a_json_object() {
        for (name, schema) in SUBCOLOUR_SCHEMAS {
            assert!(schema.starts_with('{') && schema.ends_with('}'), "{name}");
            assert_eq!(
                schema.matches('{').count(),
                schema.matches('}').count(),
                "{name}"
            );
        }
    }

    #[test]
    fn a_plain_colour_has_no_schema() {
        assert_eq!(schema_of("Audit"), None);
        assert!(schema_of("Audit.verdict").is_some());
    }
}
