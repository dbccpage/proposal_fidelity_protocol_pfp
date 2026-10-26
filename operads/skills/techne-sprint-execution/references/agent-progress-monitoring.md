# Agent progress monitoring

`AuthorityEffect: None.` Reference material for [`sprint-execution`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Agent Progress Monitoring

When using background agents (`run_in_background: true`) for long-running tasks:

### Checking Agent Status

```bash

# Use /tasks command to list all background tasks
/tasks

# Press Ctrl+T to toggle full task list view

# Press 't' to teleport into a running task

``` ext

### Reading Agent Output

```python

# When agent runs in background, tool result includes output_file path

# Use Read tool to check progress:
Read(file_path=output_file_path)

# Or use Bash with tail for recent output:
tail -50 {output_file_path}

``` ext

### Best Practices for Parallel Agents

1. **Launch agents in parallel** - Use single message with multiple Task tool calls
2. **Check status periodically** - Use TaskOutput with `block=false` for non-blocking check
3. **Wait for completion** - Use TaskOutput with `block=true` when ready to collect results
4. **Resume if needed** - Use `resume` parameter with agent ID from previous invocation

### Structured Progress Patterns

For complex multi-agent workflows:

- Agents write intermediate results to sprint scratchpad
- Use structured output format for status tracking
- Aggregate results from parallel agents using SubagentStop patterns

**Source:** Sprint 073-0 STORY-073-0-002 (Agent progress visibility improvement)
