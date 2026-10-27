---
pattern_id: HP_PY_003
name: single_canonical_catalog_path
category: healthy_pattern
operad_type: IdentityMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "exact"
dual_pattern: AP_PY_003_dual_catalog_path_asymmetry
language: python
authority_effect: None
---

# Healthy Pattern: Single Canonical Catalog Path (`HP_PY_003`)

## Description

Resolving shared repository catalogs through a single authoritative domain repository class method (`PharmacyCatalogRepository.catalog_path(repo_root)`) with fallback detection across declared candidate roots.

## Implementation Pattern

```python
from eis.domain.pharmacy_catalog import PharmacyCatalogRepository

catalog_file = PharmacyCatalogRepository.catalog_path(self.repo_root)
self.antibodies_dir = catalog_file.parent
```

## Benefits

- Guarantees byte-level agreement between producer and consumer services.
- Eliminates `FINDING_DESTINATION_MISSING` transfer failures.
- Satisfies `RULE_IMMUNE_ANTIBODY_HYGIENE_001` catalog atomicity.
