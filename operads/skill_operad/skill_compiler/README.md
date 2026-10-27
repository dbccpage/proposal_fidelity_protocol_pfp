# Skill Compiler (thin, operadic)

**AuthorityEffect: None.** Deterministic helpers for compiling experience into smaller procedural representations. Not an ∞-operad runtime and not a new meta-skill in the auto-oe-autop chain.

## Pipeline

```text
episode → resolve → representation → eval bank → admit/promote receipt → compact

```

Representation preference:

```text
CODE_GATE > SHARED_CONTRACT > references/ > SKILL.md prose > NEW_SKILL (ooutwire)

```

## Phase 0 tools

| Script | Role |
| --- | --- |
| `budget_gate.py` | Fail if governed SKILL.md exceeds line/byte budget without approved exception |
| `knowledge_parity.py` | Fail if live skill prose teaches a four- or five-host roster instead of CODA's six tracked roots |
| `budget_exceptions.yaml` | Temporary approved oversize (expiry required) |

```bash
python .agents/operad/skill_compiler/budget_gate.py
python .agents/operad/skill_compiler/knowledge_parity.py

```

## Phase 1 tools (landed)

| Module | Role |
| --- | --- |
| `episode.py` | Validate inert JSON input; append JSONL under `runs/skill_compiler/episodes/` |
| `resolve.py` | Disposition: `NOISE \| EXISTING_OP \| SHARED_CONTRACT \| CODE_GATE \| NEW_SKILL \| SKILL_PROSE` |
| `routes.yaml` | Keyword routes for contracts/gates (edit here, not in SKILL prose) |
| `promote.py` | Episode + resolve + ooutwire entry for NEW_SKILL only; receipt JSON |

```text

# Candidate prose is stored in an core.skill_compiler.episode.input.v1 JSON file

<configured-python> .agents/operad/skill_compiler/episode.py append --file <episode.json>
<configured-python> .agents/operad/skill_compiler/resolve.py --file <episode.json>
<configured-python> .agents/operad/skill_compiler/promote.py --file <episode.json>

# Deterministic metrics from core.autoskill.run.v1 rows

<configured-python> .agents/operad/skill_compiler/metrics.py --file <run.json>

# Tests (from .agents/operad so skill_compiler is importable)

cd .agents/operad && python -m unittest skill_compiler.tests.test_skill_compiler -v
cd .agents/operad && python -m unittest skill_compiler.tests.test_eval_bank -v

```

## Phase 2 tools (eval bank)

| Module / path | Role |
| --- | --- |
| `.agents/evals/skills/cases.json` | ≥10 known-failure / routing cases |
| `.agents/evals/skills/fixtures/` | Synthetic SKILL prose for parity/structure |
| `eval_runner.py` | Non-regression runner (exit 1 on fail) |

```bash
python .agents/operad/skill_compiler/eval_runner.py

```

**Rule:** changes to resolve/routes/parity/budget **must not** regress the bank.

**Retirement:** `check_skill_usage.py` is a **weak hint only**; never sole archive signal.

### Autoskill contract (Stage 1)

1. Detect signals (see autoskill progressive disclosure).
2. **Write episode first** via `episode.py append --file`. Never interpolate
   candidate prose into command flags.
3. **Resolve** disposition; do not edit SKILL.md until disposition is not `NOISE`.
4. Apply only:
   - `CODE_GATE` / `SHARED_CONTRACT` → patch gate/contract (prefer) or propose cite-only skill change
   - `EXISTING_OP` / `SKILL_PROSE` → compressive skill edit after approval
   - `NEW_SKILL` → ooutwire only (`promote.py`)

### Auto-oe-autop Stages 1-3

| Stage | Compiler duty |
| --- | --- |
| 1 autoskill | Episodes first; resolve before procedural edits |
| 2 symmetry-hunter | Packaging **and** knowledge_parity (semantic) |
| 3 improve-autoskill | Run `budget_gate.py` (mechanized compression law) |

## Phase 3 (operad honesty -- adjacent)

| Surface | Role |
| --- | --- |
| `../residual_honesty.py` | Scalar observations cannot mint `contractive` (recursive admitted packages) |
| `../bulk_operad_ingest.py` | DEF-OP-01 quarantine (dry-run; `CORE_BULK_OPERAD_INGEST=1` to write) |
| `../operad_signature.json` | High-traffic meta SPOEs typed with residual `unknown` |
| `../_docs/SEMANTICS_MAP.md` | PROPOSED_DESIGN fence for ∞-operad / HoTT minting |

```bash
python .agents/operad/residual_honesty.py
python .agents/operad/bulk_operad_ingest.py          # dry-run

python .agents/operad/validate_operad.py             # includes residual honesty

```

## Phase 4 (skill compaction)

| Skill | Hot root | Factored to |
| --- | --- | --- |
| `auto-symmetry-hunter` | Detection algorithm + severity | `references/drift_catalog.md` |
| `blackrod` | Identity, triggers, boundary, actions, schema | Doctrine: `_shared/test_quality_law.md` |
| `auto-improve-autoskill` | HIGH bar + budget_gate + report | `references/failure_modes.md` |

Budget exceptions for these three cleared after Phase 4 (all under 300 lines / 20KB).

## Non-goals

- LangGraph memory ontology as primary spine
- HoTT univalent skill minting (`PROPOSED_DESIGN` only -- see SEMANTICS_MAP)
- Auto-admit new skills from HIGH confidence alone
- Full operad re-typing of the skill garden
