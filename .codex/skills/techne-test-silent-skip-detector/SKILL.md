---
name: techne-test-silent-skip-detector
description: "Flag tests that pass while checking nothing. Bare returns, skips on repo fixtures, tautological asserts."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [code, testing, quality, falsification]
---

# Test Silent Skip Detector

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Inspection tool; emits test quality audit receipts)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

The **Test Silent Skip Detector** audits test suites to eliminate false-green illusions, tautological assertions, and silent skip patterns where test execution reports success without executing actual behavioral verification.

---

## 2. Invariants & Rules

1. **Anti-Silent-Skip Discipline:**
   - Flags tests that contain early bare `return` statements upon encountering missing fixtures.
   - Flags `pytest.skip` or `#[ignore]` directives placed on fixtures or assets that ship with the canonical repository.
   - Flags existence checks (`assert path.exists()`) used as the sole assertion without validating content, schema, or invariants.
2. **Cross-Package Dependency Isolation:**
   - Flags package-local unit tests that depend on undeclared, live sibling fixtures across workspace boundaries without hermetic isolation.
3. **Fixture-Only Aim (the misaimed suite):**
   - Flags a suite that validates a **generator** against `tmp_path` fixtures while **no test opens the artifact the repository actually ships**. Such a suite is not silently skipping; it asserts rigorously, and it is aimed at the wrong subject.
   - Rule of thumb: a package that ships a generated or content-addressed file needs at least one test resolving the **real repository root** for it. Hermetic tests prove the mechanism; only a test pointed at the shipped artifact proves the artifact.
   - This does **not** contradict invariant 2. Hermetic isolation governs tests of *behaviour*; artifact-custody tests are the declared exception, and they read the shipped file rather than a live sibling's scratch state.
   - Any such test that mutates the real tree must restore it in `finally` and re-assert the clean state afterwards, so a failing probe cannot poison the tests that follow.
   - Witness: sprint 028 found 48 green manifest tests, every one built under `tmp_path`, while a real drift (`manifest=8140, observed=9513`) sat in `origin/main`. The audit was correct; nothing had aimed it at the repository.
4. **The Vacuous Quantifier (decide the empty case deliberately):**
   - `all(...)` over an empty collection is `True`. Any claim of the form "every X satisfies P" reads as evidence when there were no X, and the reader cannot tell the difference from the result alone.
   - Every universal quantifier over a collection that **can** be empty needs its empty case decided on purpose: refused, reported separately, or deliberately admitted as vacuously true. All three are legitimate; leaving it undecided is not.
   - Vacuous truth is sometimes exactly right. Ground inertia depends on it -- an empty observer context family *must* make every pair equivalent. So this is a question for a reviewer, never an automatic defect, and a tool that claimed to tell the difference would be an unfalsifiable instrument.
   - Tool: `python operations/domain/cicd/vacuous_quantifier_scan.py` reports guarded and unguarded quantifier sites. A diagnostic; it blocks nothing.
   - Witnesses, four consecutive sprints and four mechanisms: 48 tests all aimed at `tmp_path` fixtures (028); six epic gates nothing could turn red (029); soundness certified against an empty witness set (030); a universal quantifier over an empty edge set (031).
5. **Degenerate Cases Belong Inside Exhaustive Loops:**
   - When a rule is asserted over a set of cases, include the **degenerate** one -- the identity, the empty input, the self-comparison -- even when it looks like padding. It looks like padding precisely because it is the case an implementation is most likely to special-case without anyone noticing.
   - A loop over "the interesting cases" passes against an implementation with an opening in the boring one, and that opening is where a later contributor widens the condition.
   - Witness (sprint 032): `bridge()` refuses every cross-layer promotion. Making it return `Ok` when source and target layers *agree* is the most innocuous edit imaginable -- it is the identity, semantically a no-op, and any reviewer would wave it through. It failed only because the exhaustive loop included `Parity -> Parity`.
   - Prefer asserting a **specific expected value** over asserting a type or property. Sprint 031: `assert_eq!(curvature, 1)` caught a malformed test fixture; `assert!(curvature.is_integer())` would have passed on it indefinitely.
6. **Detectors Must Be Shown Able to Fire -- in Both Polarities:**
   - A check that reports a clean result proves nothing until something demonstrates it can report a dirty one. An absence check that could never report presence, or a divergence detector that could never come back clean, is a constant with a function signature.
   - **Both polarities matter, and the second is the one that gets skipped.** Sprint 033 tested that an absence detector can find something. Sprint 034 needed the opposite: a divergence detector shown able to report **no** divergence -- otherwise its finding is an artefact of the detector rather than a property of the data.
   - Applies to presence checks, absence checks, drift detectors, and any predicate whose interesting result is one-sided in practice.
   - Witnesses: `a_directory_holding_a_corpus_root_reports_present` (033, absence check can find); `a_manifest_whose_dispositions_match_the_epic_reports_no_divergence` (034, divergence check can come back clean); `a_verifier_pointing_nowhere_is_reported` (034, presence check can fail).
7. **Falsification & Negative Controls:**
   - Enforces that all test suites include negative controls capable of failing when invariants are violated.
   - Emits structured `Audit` receipts categorizing false-green patterns and proposing concrete assertion assertions.

---

## 2b. The Tool

```powershell
python -m operations.use_cases.verification.fail_closed_audit `
  governance operations --max 64
```

Exit `0` when the count is at or under the ceiling, `1` above it. Without
`--max` it reports and always exits `0`, which is useful for reading and
useless as a gate.

This skill was a specification with no executable for its whole life, and the
cost was paid in 2026-09: a session enumerated seven instances of exactly the
pattern described above, named the archetype three times, and then wrote a
*fresh* detector implementing a strictly smaller subset of the rules already
written here. The skill is the specification; the module is its implementation,
and it is still missing invariants 2, 3, and 4 (undeclared sibling
dependencies, the misaimed suite, and the vacuous quantifier).

Measured 2026-09-04: **64 fail-open shapes, 20 of them inside 11 modules whose
own names say they audit, gate, census, or verify.** The detection layer is the
softest layer.

The tool caught itself on its first run. Its exclusion list contained
`worktrees`; this repository is checked out under `.claude/worktrees/<branch>/`,
so every path matched, zero files were read, and it printed "no fail-open shapes
found". It now raises `EmptyScan` instead of reporting clean on an empty read.

Run it through the stopping-point battery rather than on its own:

```powershell
python -m operations.use_cases.verification.stopping_point
```

---

## 3. The Family: Evidence That Cannot Fail

Three skills, three faces of one failure mode:

| Skill | Failure it names |
| --- | --- |
| **this skill** | The test asserts nothing |
| `techne-generated-artifact-custody-auditor` | The test asserts rigorously, against the wrong subject |
| `techne-unfalsifiable-gate-auditor` | The criterion names no falsifier at all |

A suite can be green because it skipped, because it was aimed at a fixture, or because the bar it was measured against was never a bar.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.
