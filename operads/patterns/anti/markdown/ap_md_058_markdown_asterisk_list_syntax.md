---
pattern_id: AP_MD_058
name: markdown_asterisk_list_syntax
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_058_hyphen_list_bullet_syntax
language: markdown
authority_effect: None
---

# Anti-Pattern: Markdown Asterisk List Syntax (`AP_MD_058`)

## Description

Using asterisk list bullets (`* list item`) in Markdown documents violates repository Markdownlint rule MD004 (which mandates consistent hyphen markers `- list item`) and triggers failures in republication gate check `C03`.

## Detection Signature

- Regex Pattern: `^\s*\*\s+[^\*]` matching lines beginning with an asterisk bullet marker.
- Republication gate check `C03` failure on asterisk bullet styles.

## Hazard & Failure Mode

- Inconsistent list rendering across pandoc, markdownlint, and XeLaTeX compilers.
- Republication gate Channel C check `C03` failure (`asterisk list style violating MD004`).

## Prevention & Resolution

Always use hyphens (`-`) for unordered list items across all Markdown documentation, change logs, and monographs:
```markdown
<!-- BAD -->
* Item one
* Item two

<!-- GOOD -->
- Item one
- Item two
```
