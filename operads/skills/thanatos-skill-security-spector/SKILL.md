---
name: thanatos-skill-security-spector
description: "Scan external skills, tool definitions and commands for prompt injection, remote exec, sockets and credential leaks."
families: [oecog, security_audit]
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# thanatos-skill-security-spector

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_logos_thanatos`

## When to use

Use before admitting any external skill package, third-party tool definition, or command
wrapper into the repository skill garden across host roots.

## Inputs

- Candidate `SKILL.md` packaging, scripts, and configuration manifests.
- Security threat pattern matrix:
  - Arbitrary remote download and execution pipelines (e.g. download pipes into shell interpreter).
  - Ambient network socket instantiation within isolated reasoning contexts.
  - Credential, environment variable, or key material harvesting patterns.
  - Unquoted variable expansions in shell commands susceptible to argument injection.
  - Latent prompt-injection triggers embedded in markdown instructions.

## Protocol

1. Parse candidate skill directories, inspecting all markdown instructions, yaml metadata, and executable scripts.
2. Check file permissions, byte encodings (UTF-8 without BOM), and authority effect declarations (`AuthorityEffect: None`).
3. Evaluate static AST patterns for prohibited socket bindings or subprocess command splats.
4. Scan natural language instructions for boundary-override directives attempting to subvert agent safety policies.
5. Emit a typed `SkillSecurityReceiptV1` recording verification hashes and admission decision (`PERMITTED` or `BLOCKED`).

## Terminals

`ADMISSION_PERMITTED`, `ADMISSION_BLOCKED`, `QUARANTINE_REQUIRED`.

## Nonclaims

Static security scanning detects recognized hostile signatures and configuration anomalies;
it does not establish the total absence of novel zero-day exploits or runtime logic vulnerabilities.
