---
name: thanatos-human-promotion-firewall
description: "Block agent promotion to PROMOTED. Agents emit review packets only; promotion needs explicit human author consent."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Human Promotion Firewall

## Awaiting

## Review packet

## Reason

## Output when blocked

## Explicit nonclaims

## Scope of an authorization: enumerate, never bundle

An authorization grants the permissions it names and no others. When one action
would plausibly grant several, enumerate them and grant only the intended ones.

The failure is silent and it compounds. Each widening looks reasonable on its
own, nobody records the moment the scope grew, and the eventual breadth is
defensible at every individual step.

**Worked case (sprint 032).** A formal certificate on a quarantined speculative
adapter grants exactly one thing: the right to author a receipt. It is very
natural to let it also make the adapter's hypothesis count as evidence -- after
all, a human signed for it. That would be wrong. A certificate says *this
proposal has been reviewed*; it does not say *this proposal is now an exact
result*. Had the two been bundled, a signature would have become a laundering
path: sign the adapter, and its hypothesis begins admitting parity claims it was
quarantined from.

The two permissions are held apart in the type, and
`certifying_an_adapter_does_not_promote_its_evidence` pins the separation.

**Questions to ask of any authorization:**

1. What exactly does this permit, listed?
2. What would a reader reasonably assume it also permits?
3. Is the difference between 1 and 2 enforced, or merely intended?
4. Does the grant let its holder do anything to *other* claims, or only to its
   own?

A `VerifiedPromotion` certificate is the same shape and the same discipline: it
promotes the artifact it names, at the grade it names, and nothing adjacent.

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

**Exception:** The **user message** is explicitly the human performing the act, e.g. the user alone writes `Authorized` or `Promoted`. Then you may **acknowledge** and proceed with post-authorization steps (e.g. pathspec commit) **without** re-issuing the authorization in the author's voice.

## Hard refusals (always)

## When to use

**AuthorityEffect: None.** This skill never promotes.

## register_entry: "0012"

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
