---
name: thanatos-aegidion-network-security
description: "Audit containment and network security; check no ambient network sockets in perception bureaus."
operad_source_colours: ["State"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [security, containment, thanatos]
---

# Aegidion Network Security

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Security & containment scanner; emits audit receipts)
**Governance Council:** `L4_logos_thanatos_nemesis` / `L3_logos_techne`

---

## 1. Prime Directive

The **Aegidion Network Security** skill enforces strict network isolation, zero ambient socket policies, sandbox boundaries, and cognitive containment invariants across all distributed agents and perception bureaus, operating as a constituent enforcement module within the `rip-thanatos` workflow.

---

## 2. Invariants & Rules

1. **Zero Ambient Network Sockets:**
   - Perception bureaus, model evaluators, and reasoning engines must operate without uncontracted ambient network sockets or raw internet access.
2. **Thanatos-Nemesis Sandbox Enclosure:**
   - All untrusted execution environments, external parsers, and prompt runs must be quarantined in sandbox containers under the Thanatos-Nemesis kill-chain.
3. **Orthogonal Governance Audit:**
   - Works in coordination with Blackrod to audit agent process trees, ensuring zero privilege escalation and verified fail-closed execution.
4. **Integration with `rip-thanatos` Workflow:**
   - Directly executed during Stage 2 (OEATS Security Audit Sweep) of `/rip-thanatos` to verify cognitive containment and network isolation before downstream execution.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.
