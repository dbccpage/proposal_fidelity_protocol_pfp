---
name: techne-stale-census-detector
description: "Find tests asserting a live corpus count equals a hard-coded integer, which fail as the estate grows."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [quality, falsification, testing, measurement]
---

# Stale Census Detector

**Status:** `CANDIDATE`
**AuthorityEffect:** `None` (inspection tool; emits an audit, promotes nothing)

## The defect

A **census literal** is an assertion comparing something measured from the
repository against an integer somebody typed in:

```python
assert len(load_garden()) == 110
assert len(all_host_markdown()) == 692
assert result.total_skills == 142
```

It is not a weak assertion. It is a very strong assertion about a number that
stops being true. When the corpus grows, the estate's growth is reported as the
estate's defect, and the failure message points at the wrong thing.

## Why it is not the unfalsifiable-gate auditor

The two detectors look adjacent and find opposite failures:

| | can it go red? | why that is wrong |
| --- | --- | --- |
| unfalsifiable gate | **never** | it certifies nothing |
| census literal | **for the wrong reason** | it certifies the corpus never changed |

Neither finds the other. `/techne-unfalsifiable-gate-auditor` scans criteria and
gates for claims nothing could break; this scans test bodies for claims that
break on benign change.

## The evidence this was built from

Seven assertions across three suites were red on `origin/main` for
twenty-five sprints. Two skills were added in sprints 028 and 029, and every
file that had written the garden's size into a literal began failing:

```text
test_the_garden_loads_every_skill                      assert 112 == 110
test_the_garden_admits_the_substitutions_it_admits     assert 3607 == 3497
test_the_estate_has_skills_to_test_against             assert 112 == 110
test_every_frontmatter_bearing_document...round_trips  assert 496 == 488
test_the_corpus_and_the_skill_set_are_both_non_empty   assert 112 == 110
```

There is no CI in this repository, so nothing noticed. The sprint that wrote one
of those literals had, in the same briefing, reported catching its own miscount
and called it *"precisely the class of defect `ESC-002-001` has escalated eleven
times -- a quantitative claim produced by an unchecked reader."* The corrected
figure became the stale one. The literal was not wrong because someone
miscounted; it was wrong because it was a literal.

## Running it

```powershell
python omega_engine_operations/domain/cicd/stale_census_audit.py
python omega_engine_operations/domain/cicd/stale_census_audit.py --path omega_engine/_tests_unit
```

Exit `0` clean, `1` findings, `2` refusal. The report always states its
denominator -- findings against comparisons examined against files read -- because
a finding count nobody can size is the same shape as a budget gate printing
`PASS` over five skills of 112.

## Reading a finding

A finding is **not** an instruction to update the number. Re-pinning re-arms the
trap for the next skill added. Replace the literal with the property it was
standing in for:

- **An independent oracle.** `load_garden()` must return one operation per
  `SKILL.md` on disk. The directory is a separate enumeration, self-maintaining,
  and strictly stronger -- a literal cannot tell a dropped skill from an added
  one; the oracle can.
- **A partition.** Every document lands in exactly one of round-tripped or
  refused, and the buckets sum to the corpus. A document silently skipped is in
  neither, which `exact == 488` could never detect.
- **A pair, where the exact value genuinely matters.** The garden/substitution
  count stays pinned as `(112, 3607)` because a colour drifting is a defect and a
  skill being added is not, and a bare total cannot say which happened. Asserted
  as a pair, the failure names its own cause: both numbers moved means the garden
  changed size; the second alone means a declared colour drifted.

## What is deliberately not a finding

- **Fixture literals.** `assert len(parsed) == 3` over a three-line fixture is a
  correct exact assertion and the test-quality law asks for exactly that. The
  separator is the *source of the measured operand*, not the size of the literal.
- **Inequalities.** `>= 110` is the weak-bound defect, a different law and a
  different repair.
- **Anything below `CENSUS_FLOOR`** (20). Stated rather than tuned: the census
  literals this estate has shipped were 110, 142, 204, 317, 488, 692 and 3497;
  its fixture literals are single digits.

## Known limits, stated

`CORPUS_READERS` is a name vocabulary, so the scan is conservative by
construction: a corpus reader it has never heard of is missed. That is why the
report prints its denominator rather than a verdict. Widening the vocabulary is
a deliberate edit -- every name added turns some correct exact assertion
elsewhere into a false positive, and a detector that cries wolf stops being read.

## Provenance

Built from the sprint 001-039 Blackrod enforcement audit. Held by
`omega_engine_operations/tests/unit/test_stale_census_audit.py` (15 tests),
including a positive control for every absence assertion, a refusal matrix, and
a mutation-verified floor. First run against the estate rather than fixtures, per
sprint 035: it found four literals, one already red and three latent.

`AuthorityEffect: None`.
