---
kind: checklist
authority_effect: None
status: live
owner: techne-council
---
# Pre-Commit Checklist

Shared checklist for all skills that involve committing code.

## Required Checks

| Check | Command | Blocking |
| ------- | --------- | ---------- |
| Git status | `git status` | No |
| Review staged | `git diff --staged` | No |
| Local CI | `python scripts/local_ci.py` | **Yes** |
| Tests pass | `pytest` | **Yes** |

## Conditional Checks

| Condition | Check | Command | Blocking |
| ----------- | ------- | --------- | ---------- |
| Test files staged | Techne Code Inspector | `/techne-code-inspector <staged test paths>` | Yes |
| Frontend changes | React tests | `npm run test:react:run` | Yes |
| Skill files staged | Autoskill suggestion | `/autoskill` | No |
| **Skill files staged** | **Skill `name:` == directory name** | `python .agents/skills/_shared/verify_skill_names.py` | **Yes** |
| **Skill files staged** | **Four-host byte parity** | `python scripts/sync_cross_host_skills.py --skills <pkgs> --check` | **Yes** |
| **Skill families changed** | **Family registry regen (exit 0 = no drift)** | `python .agents/skills/_shared/regen_family_registry.py` | **Yes** |
| Migration files | Alembic history | `.venv\Scripts\alembic.exe -c X.ini history` | No |

### Why the three skill gates are blocking

A frontmatter `name:` that disagrees with its directory registers a slash-command
unreachable at the path it lives in. Twelve skills shipped that way undetected
(2026-07-28): four `auto-auto-*`, seven `lib-lib-*`, one tripled, plus two truncated.
Partial host mirrors are the sibling failure -- a new package landing in `.agents` +
`.claude` only leaves `.codex`/`.grok` silently short, which is `DANGEROUS_DRIFT`, not
benign. Neither class is caught by review; both are caught by a loop. Run the loop.

### Renames and deletions: the sync script does NOT prune

`sync_cross_host_skills.py` mirrors the packages you **name**. It never removes a
package that no longer exists at the source. So renaming or deleting a skill leaves the
old directory alive on the other three hosts, and the slash command resolves to the
stale copy -- while `--check` still reports OK, because it only compares the packages you
asked about.

```bash

# after ANY skill rename/delete, remove the old package on the three mirrors

for h in .claude .codex .grok; do rm -rf "$h/skills/<old-name>"; done

```

Then re-run all three gates. Confirm the removal, do not assume it:
`ls -d .{claude,codex,grok}/skills/<old-name>` must return three "No such file" errors.
(Observed 2026-07-28 during the `inspector` → `techne-code-inspector`
rename.)

## A blocking row must name a runner that exists

Before adding or trusting any **Blocking = Yes** row, confirm its command resolves.
A gate naming a nonexistent script is worse than no gate: everyone believes it ran and
nobody executed it, and the belief is what stops anyone from looking.

```bash
ls scripts/<name>.py    # or Test-Path in PowerShell

```

This row carried `python scripts/test_quality_inspector.py` as **blocking** until
2026-07-28. That file has never existed on this branch -- `sentinel_councils/src/test_quality.rs`
says so in its own header comment, which is how it was finally caught. The row now
invokes the skill, which is what actually runs.

## Techne Code Inspector Gate

There is **no standalone Python runner.** `scripts/test_quality_inspector.py` does not
exist on this branch, and a checklist row that names it produces a gate everyone
believes ran and nobody executed. The doctrine lives in the skill; the
mechanically-checkable subset is ported to Rust in
`engine/sentinel_councils/src/test_quality.rs`.

```text
staged_test_files = staged paths matching **/tests/**.py, **/tests/**.rs,
                    and inline #[cfg(test)] changes in **/src/**.rs

if staged_test_files:
    invoke /techne-code-inspector <staged_test_files>

    VETO or BLOCKED   -> commit is blocked; fix the defect or report the refusal
    PASS_WITH_PATCHES -> apply the named patches, then re-run
    PASS              -> proceed

```

Missing tests are the Builder's job, not the committer's improvisation: route a VETO
through `/rip-testing`, which runs Inspector → `/techne-code-builder` → Inspector
under a finite budget. Never reach green by deleting or `#[ignore]`-ing the failing test.

## Windows-Specific

See: [windows_cli.md](../windows_cli.md) for Windows command patterns.

---

**Used by:** `commit`, `lint`, `run-tests`, `code-review`, `github`

**Source:** Sprint 050-0 (protected branch), Sprint 058 (Techne Code Inspector)
