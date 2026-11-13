---
pattern_id: HP_MD_058
name: hyphen_list_bullet_syntax
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_058_markdown_asterisk_list_syntax
language: markdown
authority_effect: None
---

# Healthy Pattern: Hyphen List Bullet Syntax (`HP_MD_058`)

## Description

Markdown documents mandate consistent hyphen list markers (`- list item`) adhering to Markdownlint rule MD004 and passing republication gate check Channel C (`C03`).

## Implementation Pattern

```markdown
<!-- GOOD -->
- Item one
- Item two
```

## Resolution

Always use hyphens (`-`) for unordered list items across all Markdown documentation, change logs, and monographs.
