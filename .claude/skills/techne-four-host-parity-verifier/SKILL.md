---
name: techne-four-host-parity-verifier
description: "Historical check that .agents, .claude, .codex and .grok skill trees are byte-identical by SHA-256."
operad_source_colours: ["State"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [governance, hosts, symmetry, packaging]
---

# Techne Four-Host Parity Verifier (Historical)

**Status:** `HISTORICAL` (Former four-host doctrine superseded by governance-host-parity)
**AuthorityEffect:** `None` (Multi-host packaging auditor; verifies estate symmetry)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

The **Techne Four-Host Parity Verifier** (former historical rule superseded by governance-host-parity) evaluates multi-host synchronization across `.agents/`, `.claude/`, `.codex/`, and `.grok/`, preventing configuration drift, partial skill deployments, and unregistered host deviations.

---

## 2. Core Invariants

1. **Former Four Active Host Roots (historical `RULE_FOUR_HOST_ROSTER_001`, superseded):**
   - The repository formerly maintained four canonical agent host directories:
     - `.agents/` (Canonical primary source)
     - `.claude/` (Claude Code mirror)
     - `.codex/` (Codex mirror)
     - `.grok/` (Grok mirror)
   - `.gemini` is exclusively an IDE local configuration root and is never on the estate roster.

2. **Atomic Skill & Rule Replication (historical `RULE_FOUR_HOST_SYNC_001`, superseded):**
   - Whenever any skill package is added, updated, or admitted under `.agents/skills/`, or when `AGENTS.md` is modified, the exact same contents were historically replicated across host directories.

3. **Text & Binary Parity Invariant:**
   - Text files (`.md`, `.yaml`, `.json`, `.py`) are compared modulo platform newline materialization (`CRLF` vs `LF`).
   - Binary assets must match exact SHA-256 digests.

4. **Zero Untracked / Stray Host Files:**
   - Destination-only stray files in `.claude/`, `.codex/`, or `.grok/` are strictly rejected.

---

## 3. Verification Commands

```powershell
python -m pytest operations/tests/packaging/test_sync_cross_host_skills.py --basetemp=.pytest_temp -v
```

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
