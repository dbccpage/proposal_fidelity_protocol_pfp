---
name: techne-oeops-evidence-receipt-harness
description: "Generate live receipts only at caller-selected paths and keep committed historical outputs under explicit receipt custody."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Oeops Evidence Receipt Harness

## Authority & Compliance

- **AuthorityEffect**: `None`
- **Governance**: Techne / Blackrod
- **Scope**: Caller-selected live receipt generation and historical receipt custody under `omega_engine_operations/receipts/`.

---

## 🏛️ Evidence Architecture

```text
[Operational Tool Run] ──► [caller-selected output directory]
                                  │
                                  ├─► <run_id>.json
                                  └─► <run_id>.md

[Historical output] ──────► omega_engine_operations/receipts/<custody-id>/
                                  └─► source-commit and source-tree manifest

```

---

## 📋 Evidence Protocol & Invariants

1. **Caller-Selected Live Output**: A live command MUST require or receive its output path from the caller. It MUST NOT default to a repository-owned receipt directory.
2. **Historical Custody Is Not Live Input**: Committed historical outputs live under `omega_engine_operations/receipts/<custody-id>/`, retain a source-commit/tree manifest, and are never selected automatically as runtime evidence.
3. **Deterministic Metadata**: Every live receipt MUST record:
   - `timestamp_utc`: ISO-8601 UTC timestamp
   - `command_line`: Full command line string invoked
   - `git_commit`: Current SHA-1 commit hash
   - `status`: `PASS`, `FAIL`, or `DEFER`
4. **Scoped Freshness**: A freshness check MUST receive the receipt directory it evaluates. It does not infer current validity from a retained historical corpus.

---

## 🛠️ Execution Commands

```powershell

# Run local CI with evidence receipt generation

python -m omega_engine_operations.entrypoints.local_ci --repository <candidate-repository> --trusted-head <trusted-commit> --expected-head <candidate-commit> --expected-main <main-commit> --nonce <64-hex> --report-file <absolute-report.json>

# Write a census only where the caller asks it to go

python -m omega_engine_operations.use_cases.packaging.multi_host_skill_census --json <report.json> --md <report.md>

```
