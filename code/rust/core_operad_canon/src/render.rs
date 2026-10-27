//! Render the operad table into the files other languages read.
//!
//! Both renderings are deterministic, so `check` can compare the committed files byte for byte.

use crate::{Family, OperadColour, OperadType, OPERAD_TYPES, PYTHON_ENUMS, SUBCOLOUR_SCHEMAS};

/// Where each generated file lives, relative to the repository root.
pub const JSON_PATH: &str = "operads/canon/operad_canon.json";
pub const PYTHON_PATH: &str = "operads/canon/_generated.py";

pub const SCHEMA_VERSION: &str = "core.operad-canon.v1";
const REGENERATE: &str = "cargo run -p core_operad_canon -- write";

fn quote(text: &str) -> String {
    let mut out = String::with_capacity(text.len() + 2);
    out.push('"');
    for c in text.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn list(values: &[&str]) -> String {
    let items: Vec<String> = values.iter().map(|v| quote(v)).collect();
    format!("[{}]", items.join(", "))
}

/// The JSON rendering read by data consumers and by the YAML registry checker.
pub fn to_json() -> String {
    let mut out = String::new();
    out.push_str("{\n");
    out.push_str(&format!(
        "  \"schema_version\": {},\n",
        quote(SCHEMA_VERSION)
    ));
    out.push_str(&format!(
        "  \"generated_by\": {},\n",
        quote(&format!("code/rust/core_operad_canon ({REGENERATE})"))
    ));
    out.push_str("  \"authority_effect\": \"None\",\n");
    let families: Vec<&str> = Family::ALL.iter().map(|f| f.as_str()).collect();
    out.push_str(&format!("  \"families\": {},\n", list(&families)));
    out.push_str("  \"colour_meanings\": {\n");
    let meanings: Vec<String> = OperadColour::ALL
        .iter()
        .map(|c| format!("    {}: {}", quote(c.as_str()), quote(c.meaning())))
        .collect();
    out.push_str(&meanings.join(",\n"));
    out.push_str("\n  },\n");
    out.push_str("  \"subcolour_schemas\": {\n");
    let schemas: Vec<String> = SUBCOLOUR_SCHEMAS
        .iter()
        .map(|(name, schema)| format!("    {}: {}", quote(name), schema))
        .collect();
    out.push_str(&schemas.join(",\n"));
    out.push_str("\n  },\n");
    out.push_str("  \"types\": [\n");
    let entries: Vec<String> = OPERAD_TYPES.iter().map(json_entry).collect();
    out.push_str(&entries.join(",\n"));
    out.push_str("\n  ]\n}\n");
    out
}

fn json_entry(entry: &OperadType) -> String {
    let mut fields = vec![
        format!("\"id\": {}", quote(entry.id)),
        format!("\"family\": {}", quote(entry.family.as_str())),
        format!("\"description\": {}", quote(entry.description)),
        format!("\"status\": {}", quote(entry.status.as_str())),
        format!("\"closed\": {}", entry.closed),
        format!("\"values\": {}", list(entry.values)),
    ];
    if let Some(decision) = entry.decision {
        fields.push(format!("\"decision\": {}", quote(decision)));
    }
    if let Some(note) = entry.note {
        fields.push(format!("\"note\": {}", quote(note)));
    }
    if let Some(letters_of) = entry.letters_of {
        fields.push(format!("\"letters_of\": {}", quote(letters_of)));
    }
    if !entry.legacy_map.is_empty() {
        let pairs: Vec<String> = entry
            .legacy_map
            .iter()
            .map(|(old, new)| format!("{}: {}", quote(old), quote(new)))
            .collect();
        fields.push(format!("\"legacy_map\": {{{}}}", pairs.join(", ")));
    }
    format!("    {{\n      {}\n    }}", fields.join(",\n      "))
}

fn constant_name(id: &str) -> String {
    id.to_ascii_uppercase()
}

/// An enum member name for a value: `Λ` is `LAMBDA`, anything else upper snake case.
pub fn member_name(value: &str) -> String {
    if value == "Λ" {
        return "LAMBDA".to_string();
    }
    let name: String = value
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() {
                c.to_ascii_uppercase()
            } else {
                '_'
            }
        })
        .collect();
    if name.starts_with(|c: char| c.is_ascii_digit()) {
        format!("_{name}")
    } else {
        name
    }
}

fn py_optional(value: Option<&str>) -> String {
    value.map(quote).unwrap_or_else(|| "None".to_string())
}

/// The Python rendering, imported through `operads.canon`.
pub fn to_python() -> String {
    let mut out = String::new();
    out.push_str(&format!(
        "\"\"\"Operad canon, generated from code/rust/core_operad_canon. Do not edit.\n\n\
         Regenerate with ``{REGENERATE}`` from ``code/rust``; import it as ``operads.canon``.\n\n\
         AuthorityEffect: None.\n\"\"\"\n\n"
    ));
    out.push_str("# fmt: off\n# ruff: noqa: E501\nfrom __future__ import annotations\n\nfrom enum import Enum\n\n");
    out.push_str(&format!("SCHEMA_VERSION = {}\n\n", quote(SCHEMA_VERSION)));
    for entry in OPERAD_TYPES {
        let items: Vec<String> = entry.values.iter().map(|v| quote(v)).collect();
        let trailing = if items.len() == 1 { "," } else { "" };
        out.push_str(&format!(
            "{}: tuple[str, ...] = ({}{})\n",
            constant_name(entry.id),
            items.join(", "),
            trailing
        ));
    }
    out.push_str("\nCOLOUR_MEANINGS: dict[str, str] = {\n");
    for colour in OperadColour::ALL {
        out.push_str(&format!(
            "    {}: {},\n",
            quote(colour.as_str()),
            quote(colour.meaning())
        ));
    }
    out.push_str("}\n\n# JSON Schema text for each sub-colour's payload; json.loads before use.\n");
    out.push_str("SUBCOLOUR_SCHEMAS: dict[str, str] = {\n");
    for (name, schema) in SUBCOLOUR_SCHEMAS {
        out.push_str(&format!("    {}: {},\n", quote(name), quote(schema)));
    }
    out.push_str("}\n\nTYPES: dict[str, dict[str, object]] = {\n");
    for entry in OPERAD_TYPES {
        let legacy: Vec<String> = entry
            .legacy_map
            .iter()
            .map(|(old, new)| format!("{}: {}", quote(old), quote(new)))
            .collect();
        out.push_str(&format!("    {}: {{\n", quote(entry.id)));
        out.push_str(&format!(
            "        \"family\": {},\n",
            quote(entry.family.as_str())
        ));
        out.push_str(&format!(
            "        \"description\": {},\n",
            quote(entry.description)
        ));
        out.push_str(&format!(
            "        \"status\": {},\n",
            quote(entry.status.as_str())
        ));
        out.push_str(&format!(
            "        \"closed\": {},\n",
            if entry.closed { "True" } else { "False" }
        ));
        out.push_str(&format!(
            "        \"values\": {},\n",
            constant_name(entry.id)
        ));
        out.push_str(&format!(
            "        \"decision\": {},\n",
            py_optional(entry.decision)
        ));
        out.push_str(&format!("        \"note\": {},\n", py_optional(entry.note)));
        out.push_str(&format!(
            "        \"letters_of\": {},\n",
            py_optional(entry.letters_of)
        ));
        out.push_str(&format!(
            "        \"legacy_map\": {{{}}},\n",
            legacy.join(", ")
        ));
        out.push_str("    },\n");
    }
    out.push_str("}\n");
    for (type_id, class_name) in PYTHON_ENUMS {
        let entry = crate::type_by_id(type_id).expect("PYTHON_ENUMS names a registered type");
        out.push_str(&format!(
            "\n\nclass {class_name}(str, Enum):\n    \"\"\"{}\"\"\"\n\n",
            entry.description
        ));
        for value in entry.values {
            out.push_str(&format!("    {} = {}\n", member_name(value), quote(value)));
        }
    }
    out
}
