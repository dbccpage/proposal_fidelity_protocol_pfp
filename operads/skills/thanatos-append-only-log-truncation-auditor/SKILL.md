---
name: thanatos-append-only-log-truncation-auditor
description: "Check append-only ledgers record head entries (count and last digest) and tests reject tail truncation."
operad_source_colours: ["Code", "Ledger"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [governance, receipts, security, forensics]
---

# Append Only Log Truncation Auditor

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Inspection tool; emits forensic integrity audit receipts)
**Governance Council:** `L3_logos_techne` / `L4_logos_thanatos_nemesis`

---

## 1. Prime Directive

The **Append Only Log Truncation Auditor** audits append-only ledgers, receipt tapes, and hash-chain data structures to guarantee that prefix truncation and tail deletion attacks are cryptographically and structurally detectable.

---

## 2. Invariants & Rules

1. **Explicit Head Record Binding:**
   - Verifies that every append-only log, DDA trace, or receipt tape maintains a signed or attested head record binding total entry count, latest entry digest, and monotonic revision checkpoint.
   - Ensures hash chains cannot validate truncated prefixes as complete logs.
2. **Tail Truncation Falsification Testing:**
   - Audits log verification test suites to ensure integrity tests explicitly remove the *last* (tail) entry and verify rejection, rather than only testing interior record mutation.
3. **Causal Head Token Verification:**
   - Enforces that state machines compare the complete 4-tuple causal head token $H_n = (n, h(s_n), r_n, c_n)$ prior to state promotion, preventing ABA replay and rollback attacks.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.
