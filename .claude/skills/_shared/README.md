---
kind: note
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Shared Components for Skills

This directory contains reusable components that skills can reference.

## Usage

In your `SKILL.md` frontmatter, reference shared components:

```yaml
name: my-skill
description: ...
shared_refs:
  - _shared/constraints.md
  - _shared/faculty_base.md
---
```

## Available Components

### [constraints.md](constraints.md)
Reusable constraint definitions (`APPROVAL_REQUIRED`, `NO_DELETE`, etc.)

### [council_hierarchy.md](council_hierarchy.md)
Council hierarchy and governance topology across executive and domain councils.

### [sprint_gates.md](sprint_gates.md)
Shared sprint gate definitions, discovery witness criteria, and test coverage standards.

### [checklists/pre_commit_checklist.md](checklists/pre_commit_checklist.md)
Shared pre-commit and pre-push verification gates.

### [architecture.md](architecture.md)
Architecture guide covering faculty skill design, progressive disclosure, and operadic composition.

### [categorical_architecture.md](categorical_architecture.md)
Operadic multicategory foundation, 10-colour boundary carrier algebra, and planar tree substitution workflows.

### [faculty_base.md](faculty_base.md)
Base template for faculty/consolidated agents with specialties.

### [output_formats.md](output_formats.md)
Standard output format templates.

### [windows_cli.md](windows_cli.md)
Command-line syntax and terminal execution guidance for Windows environments.

## Section Naming Conventions

- **`## Quick Commands`** — Use for project slash commands (e.g. `/skill-name`, `/teach-me`).
- **`## Commands`** — Use for CLI/subcommand reference (e.g. `playwright-cli open`, `playwright-cli click`). Keeps CLI docs distinct from slash-command docs.

## Design Philosophy

Following Engine's paradigm:

- `_shared/` = Reusable components (constraints, base templates, checklists, laws)
- `_templates/` = Scaffolding templates for creating new skills, operad operations, agent slices, and workflows
- Individual skills reference shared components via `shared_refs`
