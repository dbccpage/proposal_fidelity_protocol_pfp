---
name: human-promotion-firewall
description: "Block agent promotion to PROMOTED. Agents emit review packets only; promotion needs explicit human author consent."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# human-promotion-firewall

## Awaiting

## Review packet

## Reason

## Output when blocked

## Explicit nonclaims

## FinL1 freeze operator ack (Wave-0 enabler)

## PL-7 / human_close_token delivery (Paper 036 / ORT)

## QM / campaign special case

## Coupling to other skills

## Recommendation labels (not promotion)

## How the human authorizes

## Recommendation to human

## Wave-map / freeze collisions (if any)

## Residual notes / OPEN rows

## Does not support

## Supports (narrow)

## Governance

## Object under review

## What you must emit instead

**Exception:** The **user message** is explicitly the human performing the act, e.g. the user alone writes `Authorized` or `Promoted`. Then you may **acknowledge** and proceed with post-authorization steps (e.g. pathspec commit) **without** re-issuing the authorization in the author’s voice.

## Hard refusals (always)

## When to use

**AuthorityEffect: None.** This skill never promotes.

## register_entry: "0012"

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
