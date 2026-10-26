# Workflow: Sprint DevOps Review

**Version:** 2.0
**Roles:** `techne-sprint-devops-review`, `lint`, `run-tests`

---

## Pre-Retrospective CI Gate Protocol

1. **Local CI Run (`python scripts/local_ci.py`):**
   - Format check (`rustfmt --check`)
   - V1 Contract Gate (`v1_contract_gate.ps1`)
   - Packet Registry Integrity check
   - Claim ID Bijection check (`claim_id_bijection.py`)
2. **Lean 4 Sorry-Scan:**
   - Execute `lean_gate_audit` across Lean 4 research programs.
3. **Clippy Clean Gate:**
   - Confirm zero warnings under `clippy -D warnings` on touched crates.
4. **Handoff:** If clean PASS, proceed to `/techne-sprint-retrospective`.
