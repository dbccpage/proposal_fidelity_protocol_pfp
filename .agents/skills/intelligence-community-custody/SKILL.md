---
name: intelligence-community-custody
description: "Validate intelligence agency boundaries, directory structure, and custody manifests."
operad_source_colours: ["Audit", "Receipt"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
authority_effect: None
---

# Intelligence Community Custody (`intelligence-community-custody`)

## Intent

Enforces the canonical 23-agency partition under `_ic/` declared by `AgencyCode` in `governance/domain/intelligence_community.py`, verifying that no unauthorized silos exist and that telemetry outputs route strictly through typed agency bindings.

## Verification Checklist

1. **Agency Completeness:** Ensure every `AgencyCode` value exists as a top-level folder under `_ic/` and that the enum matches `governance/domain/intelligence_community.py`.
2. **Silo Prohibition:** Verify that zero ad-hoc top-level folders exist under `_ic/`.
3. **Archive Integrity:** Verify that historical archives reside at `_ic/nara/_archive` and convenience aliases match canonical manifests.
4. **Receipt Validation:** Audit outputs of producers (`Adversary`, `SymbolGame`, `DurableIntelligenceCollector`) for valid agency targets.
