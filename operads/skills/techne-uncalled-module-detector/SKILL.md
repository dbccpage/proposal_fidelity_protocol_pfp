---
name: techne-uncalled-module-detector
description: "Find modules whose only importer is their own test, so they have no production caller."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [architecture, quality, wiring, testing]
---

# Uncalled Module Detector

**Status:** `CANDIDATE`
**AuthorityEffect:** `None` (inspection tool; reports, deletes nothing)

## The defect

A module is **unwired** when every file that imports it is a test. The code is
correct. The tests are real and often excellent. The invariants hold -- and hold
of nothing, because no production path reaches them.

This is not dead code, and the distinction matters. Dead code is unreferenced;
an unwired module is *thoroughly* referenced, by a suite that proves it works.
That is why review never catches it: a reviewer sees the function and its test,
both good.

> **A diff shows you the function. Nothing in a diff shows you the absence of its
> importers.**

## Why this skill exists

Four consecutive sprints found this shape and named it precisely:

| Sprint | What was found |
| --- | --- |
| 028 | 48 rigorous tests aimed at `tmp_path` instead of the shipped artifact |
| 035 | a Lossless Roundtrip Law, correctly implemented, with **no caller at all** |
| 036 | a correct evaluator **and** a declaration about it, with no path between them |
| 037 | a workflow validator with no importer -- which would have caught 036's drift |

Sprint 037 wrote the remedy in one line: *"before accepting that a stated law is
enforced, grep for who calls the thing that enforces it."* No sprint built the
grep. This is the grep, with a denominator.

## Running it

```powershell
python omega_engine_operations/domain/cicd/uncalled_module_audit.py
python omega_engine_operations/domain/cicd/uncalled_module_audit.py --path omega_engine_pfp
```

Exit `0` when every scanned module has a caller, `1` when any does not, `2` on
refusal. First run against the estate reported **17 of 429** importable modules
unwired, across 736 files read.

## Reading a finding

**A finding is a scheduling question, not a defect.** The module may be correct,
valuable, and waiting on a caller that is genuinely next. Three dispositions, and
only a human picks among them:

1. **Wire it.** The consumer exists or is scheduled; the import was forgotten.
   This is the common case and usually a one-line fix.
2. **Record the sequencing.** The consumer is a later epic. Say so where a reader
   will find it, so the next audit does not rediscover it as news.
3. **Retire it.** The consumer is never coming. This needs the authority to
   delete, which this tool does not have and will not claim.

What must not happen is the fourth option: reading the green suite as evidence
that the law it tests is enforced in production. It is evidence that the law
holds of the test's inputs.

## What is deliberately not a finding

- **Entrypoints.** A module with a `main()` and a `__main__` guard is called by a
  person or a gate rather than by an import. Flagging those trains the reader to
  ignore the report, which is how a detector stops being read.
- **`__init__.py`.** Package markers are imported by path, not by stem.
- **Modules nobody imports at all.** That is a different question -- possibly dead
  code, possibly a plugin loaded by name -- and conflating the two makes the
  report unreadable. This skill's subject is *tested but unwired*.

## Known limits, stated

Import detection is by module **stem**, so two modules sharing a basename in
different packages are indistinguishable to the scan, and a dynamic import by
string is invisible to it. Both failure modes are toward silence: the tool
under-reports rather than over-reports. The denominator is printed so the
finding count can be sized against what was actually examined.

## Provenance

Built from the sprint 001-039 Blackrod enforcement audit, which found the shape
in `dda`, `transport`, `debate`, `guard`, `probing`, `coda`, `bytecode`,
`grammar`, `structurebench`, `colour_vocabulary_ledger`, `release_gate`,
`architecture_fitness` and `skill_budget_census`. Held by
`omega_engine_operations/tests/unit/test_uncalled_module_audit.py` (9 tests),
each finding case paired with a control proving the scan returns clean on the
wired case.

`AuthorityEffect: None`.
