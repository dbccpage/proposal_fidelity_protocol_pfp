---
kind: template
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Workflow Skill Template

Template for creating workflow-based skills. Workflow skills orchestrate multi-step processes with agent delegation, BLOB tracking, and handoffs.

## Common Sections

All workflow skills share 85% structural similarity. Use this template for consistency.

---

## Front Matter

```yaml
name: {workflow-name}
description: {Brief description}. Use after {prerequisite}. Triggers on "{triggers}"
```

---

## 1. Title & Introduction

```markdown

# {Workflow Name} Workflow

This skill initiates the **{workflow_id}** workflow with {lead_agent} as {role}.

```

---

## 2. Usage

```markdown

## Usage

\`\`\`
/{skill-name}           # Auto-detect context
/{skill-name} 014       # Explicitly specify sprint 014
\`\`\`

```

---

## 3. Prerequisites

```markdown

## Prerequisites

- {Previous workflow completed}
- {Required artifacts exist}
- {Required state}

```

---

## 4. Workflow Overview

Use a table to summarize steps:

```markdown

## Workflow Overview

| Step | Duration | Agent | Deliverable |
|------|----------|-------|-------------|
| 1 | X min | agent_name | Output 1 |
| 2 | X min | agent_name | Output 2 |
| 3 | X min | agent_name | Output 3 |

```

For event-driven workflows:

```markdown

## Workflow Overview

{Workflow name} is **event-driven**, not step-based:

| Event | Handler | Action |
|-------|---------|--------|
| event_1 | agent_1 | Action description |
| event_2 | agent_2 | Action description |

```

---

## 5. Instructions

### Step-by-Step Pattern

```markdown

## Instructions

### Step 1: {Action Name}

{Description of what to do}

\`\`\`python

# Code example if applicable
Load agent prompt: {lead_agent}
\`\`\`

### Step 2: {Main Work}

{Description of core workflow activity}

### Step N: Handoff

\`\`\`
{WORKFLOW_NAME} COMPLETE

{Summary of what was accomplished}

NEXT WORKFLOW: {next_workflow}
REQUEST: Run /{next-skill} to continue
\`\`\`

```

---

## 6. Reference Tables (Optional)

Include any reference tables needed for the workflow:

```markdown

## {Reference Type}

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value | Value | Value |

```

---

## 7. Next Workflow

Always end with navigation to the next workflow:

```markdown

## Next Workflow

After `/{skill-name}` completes, run `/{next-skill}` to {purpose}.

```

---

## Placeholder Patterns

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{workflow-name}` | Kebab-case skill name | `sprint-planning` |
| `{workflow_id}` | Snake_case workflow ID | `sprint_planning` |
| `{lead_agent}` | Primary orchestrating agent | `blackrod`, `scrum` |
| `{WORKFLOW}` | Uppercase for task codes | `PLANNING`, `EXECUTION` |
| `{next-skill}` | Skill to run after this one | `sprint-review` |

---

## Sprint Workflow Sequence

The standard sprint workflow follows this sequence:

```
/sprint-planning -> /sprint-review -> /sprint-execution -> /sprint-retrospective
       |                                                            |
       +<-----------------------------------------------------------+

```

Each workflow skill should clearly indicate its position in this cycle.

---

## Checklist for New Workflow Skills

- [ ] Front matter has name and description
- [ ] Usage section shows invocation patterns
- [ ] Prerequisites list what must be done first
- [ ] Workflow Overview summarizes steps or events
- [ ] Handoff message indicates next workflow
- [ ] Next Workflow section provides navigation
