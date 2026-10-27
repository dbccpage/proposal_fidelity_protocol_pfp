# Skill compiler eval bank

**AuthorityEffect: None.** These cases are non-authority regression fixtures for
the skill compiler (resolve, knowledge parity, structure). They do not admit
skills or mint promotion.

## Location

| Path | Role |
| --- | --- |
| `cases.json` | Case catalog (≥10 known-failure / routing cases) |
| `fixtures/` | Synthetic SKILL.md snippets for parity scans |
| Runner | `operads/skill_operad/skill_compiler/eval_runner.py` |

## Run

```bash
python operads/skill_operad/skill_compiler/eval_runner.py

# or

python -m pytest operads/skill_operad/skill_compiler/tests/test_eval_bank.py
```

## Rule

A candidate procedural change to the skill compiler (routes, resolve, parity,
budget) **must not regress this bank**. Exit code 1 = fail.

## Retirement signal (policy)

`check_skill_usage.py` fixed-list substring hits are a **weak hint only**.
Do **not** treat zero external references as primary evidence for archive/delete.
Prefer: eval bank + human retirement evidence + ooutwire disposition.

## Case kinds

| kind | What it checks |
| --- | --- |
| `resolve` | `resolve_text` disposition / rule / skill_id |
| `knowledge_parity_fixture` | `scan_file` on fixture prose (stale vs fenced) |
| `skill_structure` | Live package not hollow (min lines + required substrings) |
| `budget_exception_shape` | Exceptions file has expiry fields for oversize entries |
