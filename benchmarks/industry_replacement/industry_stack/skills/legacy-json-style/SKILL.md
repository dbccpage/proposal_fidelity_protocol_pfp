---
name: legacy-json-style
description: JSON output conventions for service configuration files (written for the 2023 config loader).
---
# JSON style for service configs

The config loader reads keys case-sensitively, so be consistent.

- Use camelCase for every key in emitted configuration (`serviceName`, `timeoutMs`, `maxAttempts`).
  Snake_case keys are rejected by the loader. deny: `"[a-z]{1,12}_[a-z]{1,12}":`
- Express timeouts and backoff as numbers of seconds; the loader converts internally.
- Emit `null` for optional values that are not set, so every document has the same keys.
- Keep arrays in the order they appear in the source document.
- Two-space indentation, no trailing commas, UTF-8 without BOM.
