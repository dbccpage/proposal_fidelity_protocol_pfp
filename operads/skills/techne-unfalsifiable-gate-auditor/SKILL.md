---
name: techne-unfalsifiable-gate-auditor
description: "Find acceptance criteria and gates no mutation could turn red, and report which epics name a falsifier."
operad_source_colours: ["Contract", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [governance, quality, falsification, planning]
---

# Unfalsifiable Gate Auditor

**Status:** `CANDIDATE`
**AuthorityEffect:** `None` (Inspection tool; emits gate-quality audit receipts)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

An acceptance criterion is a promise about **what would count as failure**. A
criterion naming no falsifier is not a weak criterion; it is not a criterion,
because every implementation satisfies it and nothing can turn it red.

This skill finds them.

---

## 2. The Witness

Sprint 029 opened `EPIC-OE-SYMGAM-011` and found its acceptance gate stated as:

> **Rust Test Suite:** All genesis, observer regime, and Examiner quiz tests pass.

A suite containing one trivial assertion satisfies that exactly. The sprint had
to derive criteria from the spec and rewrite its own gate before it could use it.

Measured across the estate:

| Scope | Result |
| --- | --- |
| `SYMGAM-001` .. `SYMGAM-010` | 5 decisive mutations each, without exception |
| `SYMGAM-011` .. `SYMGAM-016` | 0 |
| **Whole epic estate** | **15 of 31 name a falsifier; 16 name none** |

The `SYMGAM` break is clean rather than a gradient, which is the signature of a
hardening pass that stopped partway.

---

## 3. The Tool

```powershell
python operations/domain/product_planning/epic_criteria_audit.py
python operations/domain/product_planning/epic_criteria_audit.py --family symgam
```

Exit `0` when every audited epic names a falsifier, `1` when any does not, `2` on
a refusal. It is a **diagnostic** and is wired nowhere that could block a merge
on its own; promoting it to a required gate is a governance decision.

---

## 4. What It Detects

Phrases that describe a gate without saying what would fail it. Each is a real
formulation found in this estate, not an invented strawman:

- `all <x> tests pass` / `test suite passes`
- `builds successfully` / `builds cleanly`
- `no errors` / `no warnings`

And the structural signal: an **Acceptance Criteria** section containing no
`Decisive mutation:` declaration.

---

## 5. Invariants & Rules

1. **Count, do not flag.** Findings carry the number of falsifiers, so an epic
   with one stays distinguishable from an epic with five. A boolean makes a
   barely-hardened epic look finished.
2. **The tool does not judge quality.** It counts declarations and finds sections
   with none. Deciding a named mutation is genuinely decisive is a reviewer's
   job; pretending otherwise would make this the same kind of unfalsifiable
   instrument it exists to find.
3. **An empty inventory is refused.** Zero epics audited must never read as zero
   epics failing.
4. **Report, do not repair.** Rewriting an epic's criteria silently destroys the
   evidence that nobody was watching. Propose the falsifiers; let a human land
   them.
5. **A missing criteria section is a different defect** from a criteria section
   with no falsifier, and is reported separately.

---

## 6. Remediation Shape

A hardened criterion names its evidence and its falsifier:

```markdown
1. **Every historical episode replays byte-identically.**
   *Decisive mutation:* alter one byte of one episode -- replay fails and names
   the episode and offset.
```

Five per epic is the estate's established standard (`SYMGAM-001..010`).

---

## 7. The Family: Evidence That Cannot Fail

Three skills, three faces of one failure mode. Consult them together:

| Skill | Failure it names |
| --- | --- |
| `techne-test-silent-skip-detector` | The test asserts nothing |
| `techne-generated-artifact-custody-auditor` | The test asserts rigorously, against the wrong subject |
| **this skill** | The criterion names no falsifier at all |

The progression is worth internalising: a suite can be green because it skipped,
because it was aimed at a fixture, or because the bar it was measured against was
never a bar.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.

**AuthorityEffect:** `None`. Counting falsifiers is not certifying an epic.
