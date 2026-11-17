---
name: integration-audit-workflow
description: "Use an audit document as a roadmap. Verify each finding before acting, track stale items, degrade gracefully."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# integration-audit-workflow

## Constraints

**Family:** workflow (see [family_registry.md](../_shared/family_registry.md))

## Related Skills

## Source

## Graceful Degradation for Experimental Features

## Multi-Component Verification

## Stale Finding Protocol

## Execution Order

**Critical rule:** Never trust a finding without verifying the source. This applies to both:

## The Verify-Then-Act Loop

## Overview

## description: Use audit documents as executable roadmaps. Verify each finding before acting, track stale/resolved items, wire results into the codebase

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
