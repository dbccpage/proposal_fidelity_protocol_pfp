# Prompt Civilization & Lamarckian Evolution Computational Tools

**AuthorityEffect:** None.

This package contains diagnostic, verification, and simulation engines for Prompt Civilization and Lamarckian Evolution across Levels 00–10.

## Modules

- `prompt_civilization_core.py`: Core dataclasses and state machines:
  - `Genotype`, `Phenotype`, `Individual` (Level 00)
  - `LineageDAG` (Level 01)
  - `MutationForge` (Level 02)
  - `LamarckianEngine` (Level 03)
  - `ParetoSelector` (Level 04)
  - `LineagePageRank` (Level 05)
  - `PrecedentMemory` (Level 06)
  - `EcologicalReserve` (Level 07)
  - `LineageTaintTracker` (Level 08)
  - `PromptCivilizationEventLog` (Level 09)
  - `IslandEcology` (Level 10)

## Running Tests

Execute targeted tests using Python 3.12:

```bash
py -3.12 -m pytest education/documentation/010_oepciv/code/tests/test_prompt_civilization_levels.py -v
```
