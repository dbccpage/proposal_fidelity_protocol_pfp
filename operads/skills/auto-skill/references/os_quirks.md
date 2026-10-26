# Autoskill OS quirks

**Cold reference.** Open only after an operating-system or encoding failure.

## Windows and PowerShell

- PowerShell expands `$name` and backticks inside double-quoted strings. Never
  interpolate model-generated prose, Markdown, LaTeX, or code into a command.
  Write UTF-8 JSON and pass its path to a deterministic parser.
- `$Host` is a protected PowerShell automatic variable. Use a task-specific name
  such as `$hostName`.
- Configure subprocess streams explicitly as UTF-8 when output may contain
  mathematical symbols. Encoding failure is infrastructure evidence, not a
  mathematical obstruction.

## Newlines

Parity should compare canonical text content while preserving binary bytes.
CRLF-versus-LF alone is not semantic skill drift.

## Scope

These facts are localized recovery guidance. Do not copy them into unrelated
skills or load them into ordinary autoskill sessions.
