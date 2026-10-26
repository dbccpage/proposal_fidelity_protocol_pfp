---
pattern_id: AP_PY_003
name: dual_catalog_path_asymmetry
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_003_single_canonical_catalog_path
language: python
authority_effect: None
---

# Anti-Pattern: Dual Catalog Path Asymmetry (`AP_PY_003`)

## Description

Hardcoding disjoint directory targets for the same semantic asset across producer and consumer services (e.g., seeding candidates into `.agents/antibodies/` while the digestion service searches only `_intelligence/antibodies/`).

## Detection Signature

- AST Pattern: Direct string concatenation of `_intelligence/antibodies` without querying `PharmacyCatalogRepository.catalog_path()`.
- Regex: `(Path\(.*\)\s*/\s*["']_intelligence["']\s*/\s*["']antibodies["'])(?!.*catalog_path)` in lifecycle consumption logic.

## Hazard & Failure Mode

- Mined candidate antibodies cannot be located by digestion services.
- Causes `FINDING_DESTINATION_MISSING` warnings and traps runs in `EXTRACTED` (`FINDINGS_PENDING_TRANSFER`).
- Prevents runs from transitioning to `ABSORBED` and achieving terminal archival.

## Dual Healthy Pattern

See [HP_PY_003_single_canonical_catalog_path](../../helpful/python/HP_PY_003_single_canonical_catalog_path.md).
