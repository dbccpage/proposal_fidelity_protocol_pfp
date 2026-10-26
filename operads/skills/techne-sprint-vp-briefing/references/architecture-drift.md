# Architecture drift response

`AuthorityEffect: None.` Reference material for [`sprint-vp-briefing`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## If architecture drift is severe

```text
Stop adding features.
Schedule architecture cleanup sprint.

``` ext

---

# Style Rules

Use direct language.

Allowed:

```text
This is not DONE.
This evidence does not support the claim.
This test is decorative.
This story must lose credit.
This requires Blackrod action.
This is an SVP-level risk.

``` ext

Forbidden:

```text
Looks good overall.
Probably fine.
Seems implemented.
I assume tests passed.
The team did a great job.
This should be okay.

``` ext

---

# Report Artifact Paths

Unless the user specifies otherwise, write or recommend these paths:

```text
coda_project_planning/sprints/{SPRINT_ID}/vp_engineering_report.md
coda_project_planning/sprints/{SPRINT_ID}/blackrod_action_report.md
coda_project_planning/sprints/{SPRINT_ID}/svp_report.md

``` ext

The SVP report is created only if escalation is needed or requested.

---

# Story Credit Rule

A story receives delivered-point credit only if:

* verified status is `DONE_WITH_EVIDENCE` ext
* required tests passed
* evidence path exists
* no critical test-quality findings remain

If claimed DONE but evidence is missing:

```text
Verified status: DONE_BUT_EVIDENCE_MISSING
Delivered points: 0
Blackrod action: revoke DONE credit

``` ext

---

# Optional Woland Handoff

If the sprint reveals hidden contradiction, unrouted solver power, architecture drift,
fake certainty, or unexplained residue, VP Engineering may recommend Woland review.

Woland provides adversarial diagnosis.
Blackrod retains final enforcement authority.

---

# Final Rule

```text
Engineering truth first.
Blackrod action next.
SVP clarity when needed.
No fake DONE.

``` ext
