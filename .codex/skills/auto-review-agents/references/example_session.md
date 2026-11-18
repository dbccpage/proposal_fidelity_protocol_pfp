# Example session

`AuthorityEffect: None.` Reference material for [`auto-review-agents`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Example Session

```text
User: Can you audit our Engine agents and tell me which ones we should keep vs. archive?

Core: I'll run a full agents audit across the four agent roots (`.agents/agents` primary). Let me inventory
everything first...

# Agents Audit Report - 2026-02-13

## Summary
- Total agents: 47
- Keep (core): 8
- Keep (sprint): 7
- Evaluate: 26
- Archive candidates: 6

## Core Agents (KEEP)
- blackrod: Relevance 5, Memory 5 - used every sprint for enforcement
- developers-dev: Relevance 5, Memory 3 - consolidated developer agent
- database-dev: Relevance 5, Memory 4 - database development
- scrum: Relevance 5, Memory 3 - sprint facilitation

## Faculty to Evaluate (DO NOT ARCHIVE YET)
- math-topology: Relevance 1, Memory 5 - check with ERC if needed for domain verification
- phil-ethics: Relevance 1, Memory 5 - check with Nous/Dianoia

## Archive Candidates
- duplicate-tester: Relevance 1, Memory 1 - duplicate of qa-dev

## Actions Required

### High Priority
- [ ] Evaluate 26 faculty agents for council ownership
- [ ] Archive 6 duplicate agents to engine/agents/_archived/
- [ ] Update database records for archived agents

### Improve These Agents
- devops-dev: Missing YAML frontmatter model field, Authority Ambiguous

Shall I proceed with archiving the 6 duplicate agents and begin council ownership evaluation for the faculty?

```text

---
Do not archive the professors just because they are not holding the hammer today. First ask which council still needs their eyes.
