# Cross-reference validation report

`AuthorityEffect: None.` Reference material for [`lib-pedagogy-improvement`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Cross-Reference Validation Report

When validating cross-references across lessons, generate a structured report:

### Report Template

```markdown

# Cross-Reference Validation Report

**Date:** YYYY-MM-DD
**Scope:** [lesson(s) validated]
**Validator:** [agent type]

## Summary

| Metric | Count |
|--------|-------|
| Files checked | N |
| Internal links validated | N |
| External references validated | N |
| Issues found | N |

## Files Checked

| File | Sections | Links | Status |
|------|----------|-------|--------|
| lesson_000/000.01_void.md | 12 | 5 | OK |
| lesson_000/000.02_distinction.md | 15 | 8 | OK |
| ... | ... | ... | ... |

## Links Validated

### Internal Cross-References

| Source | Target | Status |
|--------|--------|--------|
| 000.03 → 000.01 (void) | 000.01_void.md | OK |
| 000.05 → 000.02 (distinction) | 000.02_distinction.md | OK |
| ... | ... | ... |

### External References

| Source | Reference | Verified |
|--------|-----------|----------|
| 000.01 | Casimir (1948) | Yes |
| 000.02 | Spencer-Brown (1969) | Yes |
| ... | ... | ... |

## Issues Found

| # | Severity | File | Issue | Recommendation |
|---|----------|------|-------|----------------|
| 1 | HIGH | 000.05 | Broken link to 000.99 | Remove or update reference |
| 2 | MEDIUM | 000.03 | Missing section anchor | Add anchor #eigenvalue |
| ... | ... | ... | ... | ... |

## Prerequisite Chain Validation

| Section | Prerequisites Used | All Defined? |
|---------|-------------------|--------------|
| 000.03 | void, distinction | Yes |
| 000.05 | recursion, eigenvalue | No (eigenvalue) |
| ... | ... | ... |

---

*Report generated YYYY-MM-DD*

``` ext

### Usage Pattern

When invoking cross-reference validation via Explore agent:

```python
Task(
    description="Cross-reference validation",
    prompt="""Validate cross-references in [lesson path]:
    1. List all files checked
    2. Validate all internal section links
    3. Check prerequisite term usage
    4. Report any broken or missing references
    5. Output structured report in markdown table format
    6. Save report to sprint folder""",
    subagent_type="Explore"
)

``` ext

**Source:** Sprint 073-0 STORY-073-0-003 (Cross-reference validation reporting)
