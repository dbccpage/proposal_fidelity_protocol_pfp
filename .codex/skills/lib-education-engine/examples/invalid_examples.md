# Invalid Frontmatter Examples

These examples demonstrate validation errors caught by `section_schema.json`.

---

## Example 1: Missing Required Fields

## ```yaml

type: section
lesson: 1

## # MISSING: section, title

``` ext

**Error:** `required property 'section' not found` ext

---

## Example 2: Invalid Type Value

## ```yaml
type: chapter  # INVALID - must be one of: section, master_outline, handout, reference, social_hooks
lesson: 1
section: 6

## title: Some Title

``` ext

**Error:** `'chapter' is not one of ['section', 'master_outline', 'handout', 'reference', 'social_hooks']` ext

---

## Example 3: Wrong Data Type

## ```yaml
type: section
lesson: "one"  # INVALID - must be integer
section: 6

## title: Some Title

``` ext

**Error:** `'one' is not of type 'integer'` ext

---

## Example 4: Out of Range Value

## ```yaml
type: section
lesson: 1000  # INVALID - maximum is 999
section: 6

## title: Some Title

``` ext

**Error:** `1000 is greater than the maximum of 999` ext

---

## Example 5: Invalid Prerequisite Format

## ```yaml
type: section
lesson: 1
section: 6
title: Some Title
prerequisites:
  - "1.05"  # INVALID - must be NNN.XX format (001.05)
---
``` ext

**Error:** `'1.05' does not match pattern '^\\d{3}\\.\\d{2}$'` ext

---

## Example 6: Invalid Tag Format

## ```yaml
type: section
lesson: 1
section: 6
title: Some Title
tags:
  - "Triangle Rigidity"  # INVALID - must be lowercase, hyphenated
---
``` ext

**Error:** `'Triangle Rigidity' does not match pattern '^[a-z0-9-]+$'` ext

---

## Example 7: Title Too Long

## ```yaml
type: section
lesson: 1
section: 6

## title: "This is an extremely long title that exceeds the maximum allowed length of 255 characters and therefore will fail validation because we want to enforce reasonable limits on field lengths to ensure consistent display and storage in the database system..."

``` ext

**Error:** `'...' is longer than maximum length 255` ext

---

## Example 8: Master Outline with Non-Zero Section

## ```yaml
type: master_outline
lesson: 1
section: 5  # INVALID - master_outline must have section: 0

## title: Lesson 1 Master Outline

``` ext

**Error:** `section must be 0 for master_outline type` ext

---

## Validation Usage

```python
import jsonschema
import yaml
from pathlib import Path

# Load schema
schema = json.loads(Path("section_schema.json").read_text())

# Parse frontmatter
with open("section.md") as f:
    content = f.read()
    if content.startswith("---"):
        _, fm, _ = content.split("---", 2)
        frontmatter = yaml.safe_load(fm)

# Validate
try:
    jsonschema.validate(frontmatter, schema)
    print("✓ Valid frontmatter")
except jsonschema.ValidationError as e:
    print(f"✗ Invalid: {e.message}")

``` ext
