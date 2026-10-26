---
name: declared-vs-actual-gate
description: "Preflight that declared stage binaries and host mirrors exist on disk and cross-host files are byte-identical."
status: canonical
council: L3_logos_sadc
invocation: discipline
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [meta]
---

# declared-vs-actual-gate

**AuthorityEffect:** None. This gate refuses. It does not repair, admit, promote, archive, or delete.  
**Council:** `L3_logos_sadc` (Software Architecture and Development Council: Craft — software architecture and development) / Metronomos Team (`L4_logos_sadc_metronomos`: Precision & Measurement).

## The executable

```bash
python omega_engine_operads/skills/declared-vs-actual-gate/scripts/check_declared_programs.py
```

Exit 0 all checks pass, 1 at least one `BLOCKED`, 2 the gate could not run -- which is a refusal, not a pass. `--json` emits the receipt.

The gate enforces that prose declarations fail closed: a gate that nothing runs fails open exactly as reliably as no gate at all.

## The single rule

> A pipeline that mandates a gate it does not ship fails open every time it runs.

Every check below compares a **declaration** (prose, frontmatter, a stage list) against the **filesystem**, and returns `BLOCKED` on mismatch. Mirrored documentation is never evidence that a stage executed.

## Check 1 — stage prerequisites

Before executing any declared multi-stage pipeline, resolve every mandatory script and interpreter named by its stages. For each: record absolute path and SHA-256, or mark it `BLOCKED`.

* A stage whose binary is absent is `BLOCKED`, never `PASS` and never silently skipped.
* The run report must state per stage: `RAN` / `BLOCKED (<missing path>)` / `VACUOUS (no input)`.
* `VACUOUS` is distinct from `PASS`. A stage with nothing to process did not pass.

Check 1 resolves 23 declared paths rather than reporting six absent, and `--json` records a SHA-256 for each. The check stays fail-closed: a path that disappears again is `BLOCKED`, never skipped, and `VACUOUS` is still distinct from `PASS`. Path resolution does not claim that every pipeline stage ran.

## Check 2 — host-mirror set completeness

Derive the host root set from the filesystem; never read it from prose.

```bash
ls -d .*/skills            # the authoritative host set
```

Refuse any skill whose declared mirror list is a **strict subset** of that set. At last audit six roots carried skills — `.agents`, `.antigravity`, `.claude`, `.codex`, `.gemini`, `.grok` — while doctrine named four.

## Check 3 — cross-host content parity

Compare trees by hash, not by file count. Equal cardinality is not parity.

```bash
git rev-parse HEAD:.agents/skills HEAD:.claude/skills   # must be equal
git rev-parse HEAD:.agents/agents HEAD:.claude/agents
```

For agent packages, additionally compare the declared sub-operad licence as a **set of colours**, so reordering passes and membership change fails. An agent present in one host and absent in another is a refusal.

## What this gate does not decide

Which side of a parity break is authoritative. That is a human decision, and this gate reports the divergence rather than resolving it. Reporting a divergence is not repairing it, and a green run of this gate means only that declaration and filesystem agree — not that either is correct.

## Consolidated Governance

This canonical gate is consolidated under [governance-git-release](../governance-git-release/SKILL.md) and governed by `L3_logos_sadc` (`metronomos`).
