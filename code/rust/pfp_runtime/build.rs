//! Compile-time enforcement of the governance packet contracts.
//!
//! Every packet type and every user-defined type inside a packet is declared in
//! `governance/contracts/contracts_pfp/`. The
//! engine that reads those contracts and generates the checks lives in
//! `../contract_shapes_build.rs`, shared with every other crate whose packets
//! are contracted so the drift detector itself has one copy.
//!
//! It generates, per contract:
//!
//! * an **exhaustive destructure** of the Rust type, compiled in every build,
//!   so a field added, removed or renamed without amending the contract is a
//!   compile error rather than a review finding; and
//! * a **serde conformance probe**, under `cfg(test)`, asserting an undeclared
//!   field is rejected where the contract says `deny_unknown_fields: true`.
//!
//! AuthorityEffect: None.

include!("../contract_shapes_build.rs");

fn main() {
    if let Err(error) = census_runtime_contracts("pfp_runtime") {
        println!("cargo::error=contract shape census refused: {error}");
        std::process::exit(1);
    }
    enforce_packet_contracts("pfp_runtime");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/pfp_runtime/build.rs
// Claim: urn:core:runtime:contract-shape-census:v1
// AuthorityEffect: None

struct ShapeRow {
    form: String,
    fields: u64,
    variants: u64,
    contract_id: String,
    rust_type: String,
}

struct ShapeCensus {
    shapes: u64,
    fields: u64,
    variants: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ShapeCensusError {
    MissingDir,
    Read { detail: String },
    Parse { detail: String },
    Empty,
    Nameless { index: usize },
    DuplicateId { index: usize },
    DuplicateType { index: usize },
    Struct { index: usize },
    Enum { index: usize },
    Form { index: usize },
    Overflow,
    Unenforced,
}

impl ShapeCensusError {
    fn fmt_row_error(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Nameless { index } => write!(f, "contract row {index} has an empty identity"),
            Self::DuplicateId { index } => write!(f, "duplicate contract id at row {index}"),
            Self::DuplicateType { index } => write!(f, "duplicate rust type at row {index}"),
            Self::Struct { index } => write!(f, "struct row {index} declares no fields"),
            Self::Enum { index } => write!(f, "enum row {index} declares no variants"),
            Self::Form { index } => write!(f, "row {index} declares an unknown form"),
            _ => Ok(()),
        }
    }
}

impl std::fmt::Display for ShapeCensusError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::MissingDir => write!(f, "governance packet contracts not found"),
            Self::Read { detail } | Self::Parse { detail } => write!(f, "{detail}"),
            Self::Empty => write!(f, "contract shape census is empty"),
            Self::Overflow => write!(f, "contract shape census overflow"),
            Self::Unenforced => write!(f, "no structure was declared for this crate"),
            _ => self.fmt_row_error(f),
        }
    }
}

fn validate_row_uniqueness<'a>(
    index: usize,
    row: &'a ShapeRow,
    ids: &mut Vec<&'a str>,
    types: &mut Vec<&'a str>,
) -> Result<(), ShapeCensusError> {
    if row.contract_id.is_empty() || row.rust_type.is_empty() {
        return Err(ShapeCensusError::Nameless { index });
    }
    if ids.iter().any(|seen| *seen == row.contract_id) {
        return Err(ShapeCensusError::DuplicateId { index });
    }
    if types.iter().any(|seen| *seen == row.rust_type) {
        return Err(ShapeCensusError::DuplicateType { index });
    }
    ids.push(&row.contract_id);
    types.push(&row.rust_type);
    Ok(())
}

fn accumulate_row_counts(
    index: usize,
    row: &ShapeRow,
    counts: &mut (u64, u64, u64, u64),
) -> Result<(), ShapeCensusError> {
    match row.form.as_str() {
        "struct" => {
            if row.fields == 0 {
                return Err(ShapeCensusError::Struct { index });
            }
            counts.2 = counts.2.checked_add(row.fields).ok_or(ShapeCensusError::Overflow)?;
            counts.0 = counts.0.checked_add(1).ok_or(ShapeCensusError::Overflow)?;
        }
        "enum" => {
            if row.variants == 0 {
                return Err(ShapeCensusError::Enum { index });
            }
            counts.3 = counts.3.checked_add(row.variants).ok_or(ShapeCensusError::Overflow)?;
            counts.1 = counts.1.checked_add(1).ok_or(ShapeCensusError::Overflow)?;
        }
        _ => return Err(ShapeCensusError::Form { index }),
    }
    Ok(())
}

fn finalize_shape_census(
    counts: (u64, u64, u64, u64),
    row_count: usize,
) -> Result<ShapeCensus, ShapeCensusError> {
    let (structs, enums, fields, variants) = counts;
    let shapes = structs.checked_add(enums).ok_or(ShapeCensusError::Overflow)?;
    let stored = u64::try_from(row_count).map_err(|_| ShapeCensusError::Overflow)?;
    let accounted = fields.checked_add(variants).ok_or(ShapeCensusError::Overflow)?;
    if shapes == 0 || shapes != stored || accounted == 0 {
        return Err(ShapeCensusError::Unenforced);
    }
    Ok(ShapeCensus {
        shapes,
        fields,
        variants,
    })
}

fn try_shape_census(rows: &[ShapeRow]) -> Result<ShapeCensus, ShapeCensusError> {
    if rows.is_empty() {
        return Err(ShapeCensusError::Empty);
    }
    let mut counts = (0u64, 0u64, 0u64, 0u64);
    let mut ids: Vec<&str> = Vec::new();
    let mut types: Vec<&str> = Vec::new();
    for (index, row) in rows.iter().enumerate() {
        validate_row_uniqueness(index, row, &mut ids, &mut types)?;
        accumulate_row_counts(index, row, &mut counts)?;
    }
    finalize_shape_census(counts, rows.len())
}

fn collect_contract_entries(dir: &std::path::Path) -> Result<Vec<std::path::PathBuf>, ShapeCensusError> {
    let mut entries: Vec<std::path::PathBuf> = fs::read_dir(dir)
        .map_err(|error| ShapeCensusError::Read {
            detail: format!("cannot read {}: {error}", dir.display()),
        })?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.to_string_lossy().ends_with(".contract.yaml"))
        .collect();
    entries.sort();
    if entries.is_empty() {
        return Err(ShapeCensusError::Empty);
    }
    Ok(entries)
}

fn validate_contract_structure_counts(
    form: &str,
    field_count: u64,
    variant_count: u64,
    index: usize,
) -> Result<(), ShapeCensusError> {
    match form {
        "struct" if field_count == 0 => Err(ShapeCensusError::Struct { index }),
        "enum" if variant_count == 0 => Err(ShapeCensusError::Enum { index }),
        "struct" | "enum" => Ok(()),
        _ => Err(ShapeCensusError::Form { index }),
    }
}

fn record_seen_identity(
    path: &std::path::Path,
    contract_id: &str,
    rust_type: &str,
    index: usize,
    seen_ids: &mut BTreeMap<String, String>,
    seen_types: &mut BTreeMap<String, String>,
) -> Result<(), ShapeCensusError> {
    if rust_type.is_empty() || contract_id.is_empty() {
        return Err(ShapeCensusError::Nameless { index });
    }
    let display = format!("{}", path.display());
    if seen_ids.insert(contract_id.to_owned(), display.clone()).is_some() {
        return Err(ShapeCensusError::DuplicateId { index });
    }
    if seen_types.insert(rust_type.to_owned(), display).is_some() {
        return Err(ShapeCensusError::DuplicateType { index });
    }
    Ok(())
}

fn parse_contract_row(
    path: &std::path::Path,
    crate_name: &str,
    index: usize,
    seen_ids: &mut BTreeMap<String, String>,
    seen_types: &mut BTreeMap<String, String>,
) -> Result<Option<ShapeRow>, ShapeCensusError> {
    let text = fs::read_to_string(path).map_err(|error| ShapeCensusError::Read {
        detail: format!("cannot read {}: {error}", path.display()),
    })?;
    let contract: Contract = serde_yaml::from_str(&text).map_err(|error| ShapeCensusError::Parse {
        detail: format!("{} is not a valid contract: {error}", path.display()),
    })?;
    let Some(structure) = contract.structure else {
        return Ok(None);
    };
    if structure.language != "rust" || structure.rust_crate != crate_name {
        return Ok(None);
    }
    record_seen_identity(
        path,
        &contract.contract_id,
        &structure.rust_type,
        index,
        seen_ids,
        seen_types,
    )?;
    let field_count = u64::try_from(structure.fields.len()).map_err(|_| ShapeCensusError::Overflow)?;
    let variant_count = u64::try_from(structure.variants.len()).map_err(|_| ShapeCensusError::Overflow)?;
    validate_contract_structure_counts(&structure.form, field_count, variant_count, index)?;
    Ok(Some(ShapeRow {
        form: structure.form,
        fields: field_count,
        variants: variant_count,
        contract_id: contract.contract_id,
        rust_type: structure.rust_type,
    }))
}

fn verify_nonempty_census(rows: &[ShapeRow]) -> Result<ShapeCensus, ShapeCensusError> {
    if rows.is_empty() {
        return Err(ShapeCensusError::Unenforced);
    }
    let census = try_shape_census(rows)?;
    let slots = census
        .fields
        .checked_add(census.variants)
        .ok_or(ShapeCensusError::Overflow)?;
    if census.shapes == 0 || slots == 0 {
        return Err(ShapeCensusError::Unenforced);
    }
    Ok(census)
}

fn census_runtime_contracts(crate_name: &str) -> Result<ShapeCensus, ShapeCensusError> {
    let dir = contracts_dir().ok_or(ShapeCensusError::MissingDir)?;
    let entries = collect_contract_entries(&dir)?;
    let mut rows = Vec::new();
    let mut seen_ids: BTreeMap<String, String> = BTreeMap::new();
    let mut seen_types: BTreeMap<String, String> = BTreeMap::new();
    for path in &entries {
        if let Some(row) = parse_contract_row(path, crate_name, rows.len(), &mut seen_ids, &mut seen_types)? {
            rows.push(row);
        }
    }
    verify_nonempty_census(&rows)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod shape_census_tests {
    use super::{try_shape_census, ShapeCensus, ShapeCensusError, ShapeRow};

    fn row(form: &str, fields: u64, variants: u64, id: &str, ty: &str) -> ShapeRow {
        ShapeRow {
            form: form.to_string(),
            fields,
            variants,
            contract_id: id.to_string(),
            rust_type: ty.to_string(),
        }
    }

    #[test]
    fn a_struct_and_an_enum_sum_their_declared_slots() {
        let census = try_shape_census(&[
            row("struct", 3, 0, "alpha", "Alpha"),
            row("enum", 0, 2, "beta", "Beta"),
        ]);
        assert!(matches!(
            census,
            Ok(ShapeCensus {
                shapes: 2,
                fields: 3,
                variants: 2,
            })
        ));
    }

    #[test]
    fn unknown_empty_and_duplicate_shapes_are_refused() {
        assert!(matches!(
            try_shape_census(&[row("mixed", 1, 0, "alpha", "Alpha")]),
            Err(ShapeCensusError::Form { index: 0 })
        ));
        assert!(matches!(
            try_shape_census(&[row("struct", 0, 0, "alpha", "Alpha")]),
            Err(ShapeCensusError::Struct { index: 0 })
        ));
        assert!(matches!(
            try_shape_census(&[row("enum", 0, 0, "alpha", "Alpha")]),
            Err(ShapeCensusError::Enum { index: 0 })
        ));
        assert!(matches!(
            try_shape_census(&[
                row("struct", 1, 0, "alpha", "Alpha"),
                row("struct", 1, 0, "alpha", "Beta"),
            ]),
            Err(ShapeCensusError::DuplicateId { index: 1 })
        ));
    }
}
