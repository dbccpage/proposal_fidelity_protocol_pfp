---
name: python-style
description: House Python style for all modules in this repository.
---
# Python style

- Follow PEP 8 naming: `snake_case` functions and variables, `PascalCase` classes, `UPPER_CASE` constants.
- Annotate public functions; keep private helpers prefixed with `_`.
- Prefer small pure helpers over long functions with nested branches.
- Prefer early returns over deep nesting.
- Use `pathlib` for paths and context managers for resources.
- Use f-strings for human-readable messages, never for code or queries.
- Keep line length under 110 characters.
- Write docstrings for public functions: one summary line, then details if needed.
- Do not leave commented-out code.
- Avoid global mutable state; pass state explicitly.
