# Claude Code Git Guardrails & Safety Hooks (`git-guardrails-claude-code`)

**AuthorityEffect:** None

Sets up a `PreToolUse` hook for Claude Code that intercepts and blocks dangerous git commands before execution.

## What Gets Blocked

- `git push` (all variants including `--force`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`
- `push --force`
- `reset --hard`

When blocked, Claude Code receives a message indicating that the command matches a dangerous pattern and is denied authority.

## Hook Script Location

The bundled interception script is located at:
`scripts/block-dangerous-git.sh`

## Installation Steps

### 1. Scope Selection

Determine installation scope:
- **Project Scope**: `.claude/hooks/block-dangerous-git.sh` configured in `.claude/settings.json`
- **Global Scope**: `~/.claude/hooks/block-dangerous-git.sh` configured in `~/.claude/settings.json`

### 2. Copy Hook Script & Make Executable

Copy `scripts/block-dangerous-git.sh` to the target hooks directory and make executable (`chmod +x`).

### 3. Configure Settings JSON

Merge the PreToolUse hook into the relevant settings file:

**Project** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

### 4. Verification

Test the hook:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

Expect exit code `2` with a `BLOCKED` message on stderr.
