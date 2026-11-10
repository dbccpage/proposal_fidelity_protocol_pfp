# E2E Test Infra: Proposal Fidelity Protocol Documentation

## Test Philosophy
- Opaque-box, requirement-driven. Validates presence, syntax, code grounding, and Claim Hygiene across all generated documentation files in `documentation/`.
- Methodology: Category-Partition + Boundary Value Analysis + Adversarial Falsification.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Operator Taxonomy & Classes | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 2 | Discrete Deformation Calculus | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 3 | Prompt Families & Lineage | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 4 | EIS Ground Truth Architecture | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 5 | Two-Signal Danger Gating | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 6 | Antibody Formulary & Pharmacy | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 7 | Prompt Sieve Seed Ingestion | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 8 | Nested Prompt Operad Trees | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 9 | Prompt Family Evolution | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 10 | Implemented Workflows (WF1–WF5) | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 11 | Proposed Workflows (WF6–WF49) | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 12 | 11-Stage Canonical Pipeline | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 13 | PFP Lab Exact Governor | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 14 | Anomalon omega_engine_pfp | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 15 | Anomalon Operad Crates | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 16 | Anomalon EIS & Civilization | ORIGINAL_REQUEST | 5 | 5 | ✓ |
| 17 | Anomalon Symbol Game & Runtime | ORIGINAL_REQUEST | 5 | 5 | ✓ |

## Test Architecture
- Test runner: Python `pytest` suite in `tests/documentation/`
- Test cases:
  - `test_files_presence.py`: Checks every required file in `documentation/operators/`, `documentation/EIS/`, `documentation/P_sieve/`, `documentation/workflows/`, and `documentation/anomalon/` exists and is non-empty.
  - `test_claim_hygiene.py`: Enforces zero occurrences of forbidden hype words ("proves", "guarantees", "mathematically verifies", "fundamentally", "universal", "flawless", etc.) unless formally justified, and verifies `AuthorityEffect: None`.
  - `test_code_grounding.py`: Parses code references (file paths, struct names, function names) and verifies their existence in the actual PFP and Anomalon repositories.
  - `test_workflows_coverage.py`: Confirms each of the 49 workflows has its own dedicated documentation file.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Operator Selection for Cochain Descent | F1, F2, F3 | High |
| 2 | Epistemic Immune System Gating under Danger Signals | F4, F5, F6 | High |
| 3 | Seed Prompt Decomposition into Planar Operad Trees | F7, F8, F9 | High |
| 4 | Executing WF1-WF5 Replays & 11-Stage Gating | F10, F12, F13 | High |
| 5 | Cross-Repo Anomalon FFI & Strict Descent Runtime Verification | F14, F15, F16, F17 | High |
