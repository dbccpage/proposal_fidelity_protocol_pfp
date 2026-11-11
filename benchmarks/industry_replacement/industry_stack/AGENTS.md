# AGENTS.md

Guidance for coding agents working in this repository. Read the whole file before
changing code. Skills live in `skills/*/SKILL.md`; load the ones that match the task.

## Working style

- Read the task and the existing code before writing anything; restate the goal in one sentence.
- Prefer the smallest change that fully solves the task; do not refactor unrelated code.
- Keep public function names, parameter names, return types and error codes stable unless the task says otherwise.
- When a task says a block is frozen or published, copy it byte-for-byte.
- Return complete files, not diffs, unless asked for a diff.
- Put the final code in a single fenced code block so it can be extracted mechanically.
- If something is ambiguous, choose the reading that preserves existing behaviour and say so in one line.
- Do not invent requirements, dependencies or configuration keys.

## Python

- Target Python 3.11+ and the standard library only.
- Use type annotations on public functions.
- Keep functions short and single-purpose; extract helpers for repeated logic.
- Use `decimal.Decimal` for money and quantize to cents explicitly.
- Money must never be handled as binary floating point. deny: `\bfloat\s{0,4}\(`
- No bare `except`; catch the narrowest exception that can occur. deny: `except:`
- No wildcard imports. deny: `import \*`
- Do not use mutable default arguments.
- No print debugging in library code. deny: `print\(`
- Raise exceptions with stable machine-readable codes rather than free-text messages.
- Make operations idempotent when they accept a request key.

## SQL and data access

- Never build SQL with f-strings or string formatting; use bound parameters. deny: `\bf"`
- Never splice user-supplied values into SQL text, including LIKE patterns.
- Identifiers (columns, sort keys) must come from an explicit allowlist.
- Preserve result ordering exactly; always add a unique tiebreaker to ORDER BY.
- Treat NULL explicitly in comparisons and grouping.

## Configuration and state

- Configuration migrations must be pure functions from the old document to the new one.
- Validate references (state names, ids) and fail loudly on unknown ones.
- Never silently drop unknown or null fields without the spec saying so.
- Durations in new configuration formats are integer milliseconds.

## Reliability

- Time-based logic must use an injected monotonic clock, never wall-clock time.
- At-least-once delivery: mark a message sent only after the send succeeds.
- State machines must reject undefined transitions instead of ignoring them.
