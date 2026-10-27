---
name: auto-review-agents
description: "Use when cleaning up agents. Reviews agents for relevance, quality and use; flags unused ones."
invocation: discipline
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: neutral
families: [meta]
---

# Agents Review Algorithm

Systematically audit the **agent panel across all declared roots**. Never bypass
this stage because a single path is missing.

**Canonical roots (run all; empty inventory is valid PASS data):**

| Root | Role |
| --- | --- |
| `.agents/agents` | Provider-neutral canon (primary today) |
| `.claude/agents` | Claude host projection (often empty) |
| `.codex/agents` | Codex host projection |
| `engine/agents` | Legacy/optional; may be absent |

```bash
python operads/skills/auto-review-agents/scripts/agents_audit.py
```

The script parses the canonical manifests and validates required fields,
name/path identity, authority, tool-list shape, capability-slice presence,
registered skill references, and color closure. It does not call an agent useful
merely because frontmatter begins with `---`.

Do **not** conclude "no agents" from `engine/agents` alone when
`.agents/agents` has inventory. Mirror roots are packaging projections; the
canonical capability verdict comes from `.agents/agents` plus the operad registry.

## Agent Design Principles

- **No bloat**: Agents should NOT duplicate functionality of other agents
- **Project-specific only**: Include agents that serve the SDLC workflow and Sentinel-specific needs
- **Consolidate related agents**: Prefer one comprehensive agent over many fragmented ones
- **Archive, don't delete**: Move unused agents to `_archived/` for reference

## Model Tier Assignment Policy

When reviewing or creating agents, assign model tiers based on reasoning complexity:

| Tier | Use For | Examples |
| ------ | --------- | --------- |
| **opus** | Complex reasoning, research, domain expertise, adversarial analysis, strategic synthesis, multi-step planning | physics-prof, math-prof, thanatos, panepistimion, sentinel, pedagogy, blackrod, orchestrator, database_dev, are |
| **sonnet** | Structured/formulaic work, pattern matching, code review, process execution, build fixing | code-review, debug, autoskill, build-error-resolver, e2e-runner, dianoia, erc, student |
| **haiku** | Administrative tasks, fast validation, lightweight orchestration | build-validator, secretary_cc, secretary_sadc, secretary_uc |

**Default bias:** When uncertain, lean toward the higher tier. Opus adaptive thinking manages cost automatically by scaling reasoning effort to task complexity.

**Audit steps:** See [`audit-steps.md`](references/audit-steps.md).

## Authority Safety Check

Flag agents that:

- claim final enforcement when not Blackrod
- claim final council decision when not SVP/SADC
- claim human override
- waive evidence
- self-certify
- approve their own output
- use unsafe enforcement language
- blur review vs execution vs enforcement

Classify:
`AUTHORITY_OK` | `AUTHORITY_AMBIGUOUS` | `AUTHORITY_COLLISION` | `AUTHORITY_UNSAFE`

### Symmetry-Hunter Handoff

If the audit finds agents with inconsistent evidence, test, build, authority, or self-certification rules:

Do not patch manually inside auto-review-agents.

Create a `/auto-symmetry-hunter` finding:

- family
- expected invariant
- files diverging
- recommended propagation

## Step 3: Generate Report

Create an agents audit report:

```markdown
# Agents Audit Report - {date}

## Summary
- Total agents: {count}
- Keep (core): {count}
- Keep (sprint): {count}
- Evaluate: {count}
- Archive candidates: {count}

## Actions Required

### High Priority
- [ ] {action 1}
- [ ] {action 2}

### Archive These Agents
- {agent-1}: {reason}
- {agent-2}: {reason}

### Improve These Agents
- {agent-1}: {what to fix}
```

## Step 4: Execute Cleanup

After review approval:

1. **Archive unused agents**:

   ```bash
   mkdir -p operads/agents/_archived
   mv .agents/agents/{agent-name}.md operads/agents/_archived/
   ```

2. **Document decisions** in sprint retrospective

## Quick Commands

```bash
# Preferred: four-root inventory (implements AGENT_ROOTS in agents_audit.py)
python operads/skills/auto-review-agents/scripts/agents_audit.py

# Canon listing
ls .agents/agents/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md$//' | sort

# Optional legacy root (may not exist)
ls engine/agents/*.md 2>/dev/null | wc -l
```

## Faculty Discovery Plan

**DANGER**: candidate discovery only, not automatic archive.
Review each candidate for council ownership and memory value first. Do not provide a bulk `mv` loop unless the user explicitly approves a reviewed archive list.

```bash
for pattern in "math-" "phil-" "hist-" "anthro-" "neuro-" "psych-" "socio-" \
               "cs-" "ir-" "rel-" "epist-" "mind-" "phys-" "rhet-" "stem-" \
               "*-router" "*-faculty"; do
  ls .agents/agents/${pattern}*.md 2>/dev/null
done
```

## Mathematical Document Review

When reviewing mathematical documents (spines, proofs, theory files) with
multi-agent orchestration:

- Assign each agent ONE mathematical perspective (e.g., higher category
  theory, HoTT, homological algebra, Langlands functoriality, cross-document
  synthesis)
- Each agent reads the primary document + 2-3 relevant subsidiary files
- Require concrete rewrites (drop-in LaTeX + prose), not vague suggestions
- For analogies/transfers: require graduated honesty assessment
  (substantively genuine / algebraically genuine / partially genuine /
  largely metaphorical)
- When reviewing another model's mathematical output, verify: (a) definitions
  satisfy their stated axioms, (b) "automatic" coherence claims are actually
  automatic, (c) analogies preserve categorical structure

## Integration with auto-review-skills

Run both reviews together for comprehensive cleanup:

```bash
/auto-review-agents  # Audit agents
/auto-review-skills  # Audit skills
```

Ensure agent-skill alignment:

- Each SDLC agent should have corresponding skills assigned
- Archived agents should not have active skill assignments

## Related Skills (The Meta-Family)

autoskill:
  learns from sessions

auto-improve-autoskill:
  improves the learner

auto-symmetry-hunter:
  finds cross-file invariants and drift

auto-review-skills:
  audits the skill garden

auto-review-agents:
  audits the agent panel

**Family:** meta (see [family_registry.md](../_shared/family_registry.md))

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: APPROVAL_REQUIRED, EVIDENCE_BASED

Summary:

- All archive/delete decisions require explicit approval (APPROVAL_REQUIRED)
- Recommendations must cite specific evidence (relevance score, usage data) (EVIDENCE_BASED)

**Example session:** See [`example-session.md`](references/example-session.md).

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
