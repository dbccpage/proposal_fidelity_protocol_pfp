---
name: techne-cicd-gate-catalog-dual-home-auditor
description: "Check gate_catalog_v3.yaml matches GATE_CATALOG_V3 in code, entrypoints exist, and flag bad git argv patterns."
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [techne-code, cicd, governance, gate-catalog]
---

# Techne CI/CD Gate Catalog Dual-Home Auditor

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Verification auditor; emits verification receipts without release authority)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

The **Techne CI/CD Gate Catalog Dual-Home Auditor** enforces 1-to-1 parity between the domain YAML gate catalog (`gate_catalog_v3.yaml`) and its canonical loader (`catalog.py`), preventing gate catalog drift, verifying valid Python entrypoint paths, and enforcing safe 4-element git addressing arguments.

---

## 2. Core Invariants

1. **Gate Catalog Dual-Home Parity Invariant (`RULE_GATE_CATALOG_DUAL_HOME_001`):**
   - Any modification to gate routes, module entrypoints, timeout budgets, or failure codes must be applied simultaneously to both:
     - `omega_engine_operations/domain/cicd/gate_catalog_v3.yaml`
     - `omega_engine_operations/domain/cicd/catalog.py` (`GATE_CATALOG_V3`)
   - Both catalogs must match byte-for-byte in gate IDs, entrypoints, timeouts, and route ordering.

2. **Committed-Byte Git Reader Purity Invariant (`RULE_GIT_CAT_FILE_ARGV_001`):**
   - Git object reading across CI/CD and governance harnesses must strictly use 4-element argv arrays:
     $$\text{argv} = [\text{"git"}, \text{"cat-file"}, \text{"-p"}, \text{f"\{rev\}:\{path\}"}]$$
   - Reject unparsed colon strings with typed `UnsafeGitAddress` residuals.
   - Prevent 5-element argv structures containing `--` path delimiters which trigger git error 129.

3. **Typed Refusal Envelope Normalization (`RULE_LOCAL_CI_REFUSAL_NORMALIZATION_001`):**
   - Controllers mediating CI/CD and verification actions must catch typed domain errors (`LocalCiReceiptError`) and serialize them into standard refused response payloads:

     ```json
     {
       "status": "REFUSED",
       "error": {
         "code": "REFUSED_RECEIPT_ERROR",
         "message": "Detailed refusal description"
       }
     }
     ```

   - Catch typed domain errors before falling back to generic HTTP/RPC error wrappers.

---

## 3. Verification Commands

```powershell
python -m pytest omega_engine_operations/tests/cicd/test_local_ci_protocol.py --basetemp=.pytest_temp -v
```

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
