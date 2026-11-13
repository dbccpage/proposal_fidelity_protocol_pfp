# Root cause analysis

`AuthorityEffect: None.` Reference material for [`sprint-vp-briefing`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Phase 7 — Root Cause Analysis

For each major issue, classify root cause:

```text
unclear acceptance criteria
missing test plan
weak implementation
bad dependency ordering
missing harness
mock-only validation
wrong abstraction
unrouted solver
overclaim
time pressure
review failure

``` ext

Then recommend:

```text
fix now
quarantine
rollback
follow-up sprint
Blackrod enforcement
SVP escalation

``` ext

---

# Severity Levels

| Severity | Meaning                                                                         | Action                 |
| -------- | ------------------------------------------------------------------------------- | ---------------------- |
| CRITICAL | Safety/firewall breach, self-certification, false DONE, data loss, broken build | Blackrod immediately   |
| HIGH     | Sprint goal at risk, major tests missing, kill-gate mishandled                  | Fix before next sprint |
| MEDIUM   | Architecture drift, weak module boundary, insufficient coverage                 | Schedule cleanup       |
| LOW      | Naming/docs friction, minor cleanup                                             | Backlog                |
| INFO     | Observation only                                                                | Record                 |

---

# Automatic Blackrod Escalation

Escalate to Blackrod if any of these occur:

```text
false DONE status
missing evidence for completed story
trivial tests accepted
self-certification accepted
HMAC/signature called proof
kill-gate bypassed
same-boundary oracle accepted
external API used in CI without permission
sandbox overclaim
revocation/rollback claim not tested
build broken
test suite broken

``` ext

---

# Automatic SVP Escalation

Prepare SVP report if:

```text
sprint failed
critical blocker exists
delivery date at risk
architecture direction changed
quality system failed
Blackrod intervention required
cross-team or council-level decision needed

``` ext

SVP report must be short.

No philosophy unless directly relevant to engineering risk.

---

# Output Format 1 — VP Engineering Sprint Delivery Report

Always produce this first.

```markdown

# VP Engineering Sprint Delivery Report

## Sprint

- Sprint ID:
- Sprint goal:
- Review date:
- Reviewed artifacts:
- Evidence root:

## Engineering Decision

APPROVED_FOR_BLACKROD_REVIEW / NEEDS_FIXES / BLOCKED / FAILED / QUARANTINE_REQUIRED

## One-Paragraph Truth

Plain statement of what happened.

## Story Status Table

| Story | Claimed Status | Verified Status | Evidence | Finding |
|---|---|---|---|---|
| STORY-X | DONE | DONE_WITH_EVIDENCE | path | OK |
| STORY-Y | DONE | DONE_BUT_EVIDENCE_MISSING | missing | No credit |

## Quality Gate Results

| Gate | Status | Evidence |
|---|---|---|
| Build | PASS/FAIL/NOT PROVIDED | path/output |
| Test build | PASS/FAIL/NOT PROVIDED | path/output |
| Unit tests | PASS/FAIL/NOT PROVIDED | path/output |
| Integration tests | PASS/FAIL/NOT PROVIDED | path/output |
| Coverage | PASS/FAIL/NOT PROVIDED | path/output |
| Clippy/lint | PASS/FAIL/NOT PROVIDED | path/output |
| Techne Code Inspector | PASS/FAIL/NOT RUN | path/output |
| Evidence paths | PASS/FAIL | paths |

If build, test, coverage, clippy, or evidence output is unavailable,
the status must be `NOT PROVIDED`, never PASS.

## Major Findings

### Critical

- ...

### High

- ...

### Medium

- ...

### Low

- ...

## Test Quality Findings

List missing, weak, fake, or insufficient tests.

## Architecture / Organization Findings

List drift, duplicated concepts, bad boundaries, or misplaced files.

## Kill-Gate Findings

State whether kill-gates ran, fired, or were bypassed.

## Root Causes

| Issue | Root Cause | Recommended Action |
|---|---|---|

## Required Fixes Before Blackrod Approval

1. ...
2. ...

## Recommended Follow-Up Sprint Items

1. ...
2. ...

## VP Engineering Verdict

One blunt paragraph.

``` ext

---

# Output Format 2 — Blackrod Action Report

Produce this after the VP report.

This is the report Blackrod uses to act.

```markdown

# Report to Blackrod

## Required Action

NO_ACTION / BLOCK_APPROVAL / FORCE_FIXES / QUARANTINE / ROLLBACK / ESCALATE_TO_SVP

## Summary

One paragraph. No fluff.

## Enforcement Items

Use the following priority buckets:
- P0: block/revoke/quarantine immediately
- P1: fix before next sprint
- P2: schedule cleanup
- P3: backlog

| Priority | Item | Evidence | Required Action |
|---|---|---|---|
| P0 (CRITICAL) | Missing evidence on DONE story | path/missing | Revoke DONE |
| P1 (HIGH) | Weak test accepted | file/test | Require replacement |

## Stories to Strip of DONE Credit

- STORY-X — reason
- STORY-Y — reason

## Stories to Block

- STORY-Z — reason

## Stories Safe to Accept

- STORY-A — evidence path

## Cleanup Orders Recommended

1. ...
2. ...

## Escalation Needed?

YES / NO

If YES:

Reason:
Recommended recipient:
Required decision:

``` ext

Tone: direct. Blackrod does not need a novel.

---

# Output Format 3 — SVP Software Development Council Report

Produce this only if escalation is needed or requested.

```markdown

# SVP Software Development Council Report

## Executive Summary

One paragraph. What happened and why it matters.

## Current State

GREEN / YELLOW / RED

## What Is Working

- ...

## What Is Broken

- ...

## What Is Blocked

- ...

## Risk to Delivery

LOW / MEDIUM / HIGH / CRITICAL

Reason:

## Required Decisions

1. ...
2. ...

## Immediate Actions Underway

- ...

## Help Needed From SVP

- ...

## Expected Next Update

- after fixes complete
- after Blackrod enforcement
- after rerun of tests
- after kill-gate resolution

## Plain Truth

One blunt sentence.

``` ext

SVP report rule:

```text
No jargon unless necessary.
No metaphysics.
No “operator ecology” unless architecture direction itself is the issue.

``` ext

---

# Review Logic
