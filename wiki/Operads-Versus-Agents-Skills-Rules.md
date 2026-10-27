# Operads versus agents, skills and rules

Part of [Operads](Operads.md). Next: [Operad primer](Operads-Primer.md)

Most coding-agent tools today are configured with three kinds of file: **rules**
(standing instructions), **skills** (task instructions loaded on demand) and
**agents** (a persona with its own prompt and tool list), plus **tools** reached
through the Model Context Protocol (MCP) and **hooks** that run code around tool
calls. This page outlines those formats, says what the operads package adds on
top of them, and is honest about where it does not yet do better.

The industry descriptions were checked against public documentation in October
2026; links are at the end.

## The industry-standard formats

| Kind | Common formats | What it is | How it is enforced |
| --- | --- | --- | --- |
| Rules | `AGENTS.md`, `CLAUDE.md`, Cursor `.cursor/rules/*.mdc`, `.github/copilot-instructions.md` | Markdown instructions loaded into the model's context, always or when a file glob or description matches | Not enforced. The model reads them and may or may not follow them |
| Skills | Agent Skills: a folder with `SKILL.md` (frontmatter `name`, `description`) and optional `scripts/`, `references/`, `assets/` | A task playbook. Only name and description are loaded at start; the body and files are read when the task matches | Not enforced. Selection is by the model reading the description |
| Agents (subagents) | Markdown with frontmatter such as `name`, `description`, `tools`, `model` (for example `.claude/agents/*.md`) | A separate context with its own system prompt and an allow-list of tools | The tool allow-list is enforced by the host; the behaviour is not |
| Tools | MCP tools with a JSON Schema `inputSchema` and optional `outputSchema` | A callable function the model can invoke | Inputs and outputs are schema-checked by the client or server |
| Hooks | Host hook config (for example `PreToolUse`, `PostToolUse`) | Code the host runs before or after a tool call | Enforced: a hook can block the call |

`AGENTS.md` and the Model Context Protocol are now projects of the Agentic AI
Foundation under the Linux Foundation, and Agent Skills was published as an open
specification, so these formats are converging across vendors.

What they have in common: **rules, skills and agents are untyped prose.**
Nothing says what a skill consumes or produces, so nothing can check that the
output of one skill is a valid input to the next, or that a chain of skills makes
sense. Only tools (by schema) and hooks (by code) are mechanically enforced.

## What operads add

An operad treats each capability as an **operation with a typed signature**,
`(input colours) -> output colour`, over a closed set of ten colours (State,
Proof, Paper, Code, Contract, Receipt, Ledger, Diagram, Audit, Post). See the
[primer](Operads-Primer.md). That one change gives several things the plain
formats cannot:

1. **Composition is checked before anything runs.** Plugging skill A's output
   into skill B's input is allowed only when the colours match, and the
   associativity and unit laws make the result independent of how the chain is
   grouped. A mismatched chain is refused with a typed code instead of being
   tried and failing at run time.
2. **Refusal instead of silent repair.** An unknown colour, a malformed
   frontmatter block or a duplicate name fails the compile with a named code.
   The industry formats generally ignore a bad field or let the model guess.
3. **Negative capabilities are first-class.** Every positive kind has a
   negative twin with the same machinery: skill and anti-skill, op and anti-op,
   helpful pattern (HP) and anti-pattern (AP), and antibodies from the
   [Epistemic Immune System](EIS.md). The industry formats express "don't do X"
   only as more prose in a rule file.
4. **No authority from composition.** Every composite is an *unadmitted
   candidate* with `AuthorityEffect: None`. Admission is a separate, recorded
   decision. In the plain formats, loading a skill or rule is the same as
   trusting it.
5. **Receipts.** Compiles, refusals and gate runs produce hashed receipts that a
   second party can recompute, so a claim that "the skill passed" can be
   checked.

## How each operad kind maps to the industry formats

| Operad kind | Closest industry format | Relationship |
| --- | --- | --- |
| Skill (237 in `operads/skills/`) | Agent Skills `SKILL.md` | **Extends, does not replace.** Each skill is a valid `SKILL.md` with extra frontmatter: `operad_source_colours`, `operad_target_colour`, `operad_arity`, `operad_residual`. Any host that reads Agent Skills can still load it |
| Op and anti-op (`op_inventory.yaml`) | MCP tool | **Refines a skill into tool-like pieces.** An op has typed inputs and one output, and is bound to host code; an anti-op guards one input slot. This is the part that behaves most like an MCP tool with a schema |
| Rule (50 rule documents, 144 invariants) | `AGENTS.md`, `CLAUDE.md`, Cursor rules | **Same idea, with status.** Rules are still Markdown, but each invariant has an id and a status (ENFORCED, PARTIAL or CANDIDATE), and a rule counts as enforced only when tested code backs it |
| Helpful pattern / anti-pattern | Examples inside rule files | **Split out and paired.** Each `HP_*` file has a matching `AP_*` file, so the good and bad version of a practice are kept together |
| Antibody | No equivalent | A typed detector for a known failure (pattern, severity, constraint type, action). The nearest industry tool is a lint rule or hook |
| Agent role (12 in `roles.yaml`) | Subagent definition | **Licence by colour, not just by tool.** A role lists the colours it may produce, as a subagent lists the tools it may call |
| Colour signature check | MCP JSON Schema | **Coarser but cross-cutting.** MCP checks one tool's arguments in detail; colours check whether a whole chain of skills fits |
| Host hooks (`operads/hooks/hooks.json`) | Host hooks | **The same mechanism.** The operads hooks use the standard `PreToolUse` and `PostToolUse` events, and this is where enforcement actually happens |
| DDC letters (E, R, C, I, Λ, D, M, T) | No equivalent | An alphabet for how a repair step changes a residual. See [Bounded repair](Operads-Bounded-Repair.md) |

So operads **do not replace** the industry formats. They sit on top of them:
the files stay in formats any agent host can read, and the operad layer adds
types, composition checks, negative twins and receipts that a host without the
operad compiler simply ignores.

## Where operads do not yet do better

Measured against the code on `main` (see the
[type inventory](Operads-Type-Inventory.md)):

- **Most skills have no executor.** All 237 catalogued skills have executor state
  `UNBOUND`. Typed signatures on prose skills are still prose underneath: the
  colour check says two skills fit, not that either does its job. Only 15 ops in
  5 skills are bound to host code.
- **Residual effects are mostly unknown.** 229 of 237 skills declare
  `operad_residual: unknown`, so the contraction claims the theory relies on are
  not yet stated for most skills.
- **Ten colours are coarse.** An MCP schema can say "a string matching this
  pattern"; a colour only says "an Audit". Sub-colours exist for 8 wires only.
- **The negative side is thin.** The anti-skill type exists but no anti-skill
  records are stored here; only 2 skills have a declared constructive and
  adversarial partner.
- **Agents are not compiled.** The 12 roles exist, but the compiled capability
  catalogue lists no agents, so role licences are not yet checked by the
  compiler.
- **Rules are mostly candidates.** 104 of 144 rule invariants are CANDIDATE, so
  most rules are still the same unenforced prose as an `AGENTS.md`.
- **Hooks still do the real enforcement.** As in the industry setup, the checks
  that actually block an action at run time are hook scripts.
- **No other host understands the operad fields.** The extra frontmatter is
  portable but inert outside this repository's compiler.

## Why it is still worth it

The industry formats answer "what should the model read?". Operads also answer
"which capabilities may be chained, what does the chain produce, what must it
refuse, and what evidence says it ran?". Those questions matter once skills are
composed automatically rather than picked one at a time by a model, which is
the case PFP is built for. The gaps above are mostly missing data (bindings,
residuals, anti-skill records), not missing machinery.

## Sources

- Agent Skills specification: [agentskills.io](https://agentskills.io/)
- AGENTS.md and the Agentic AI Foundation: [OpenAI announcement](https://openai.com/index/agentic-ai-foundation/)
- Model Context Protocol, tools: [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- Claude Code subagents and hooks: [code.claude.com/docs](https://code.claude.com/docs/en/sub-agents), [hooks](https://code.claude.com/docs/en/hooks)
- Cursor project rules: [Cursor forum deep dive](https://forum.cursor.com/t/a-deep-dive-into-cursor-rules-0-45/60721)
