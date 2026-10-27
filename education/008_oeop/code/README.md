# Workflows, Agents, Skills (WAS), Multicategories & Operads Computational Tools

**AuthorityEffect:** None.

This package contains diagnostic, verification, and simulation engines for WAS, Multicategories, and Coloured Operads across Levels 00–09.

## Modules

- `was_operad_core.py`: Core dataclasses and operadic tools:
  - `ColouredOperad`, `OperadOp`, `Colour` (Level 00)
  - `SkillPackage` (Level 01)
  - `PlanarTree` (Level 02)
  - `SwarmWing` (Level 03)
  - `AntiSkillRegistry` (Level 04)
  - `OperadTregSupervisor` (Level 05)
  - `DDCContractivityEngine` (Level 06)
  - `DialecticWorkflow` (Level 07)
  - `FourHostParityManager` (Level 08)
  - `DeliberationReceiptEmitter` (Level 09)

## Running Tests

Execute targeted tests using Python 3.12:

```bash
py -3.12 -m pytest education/documentation/008_oeop/code/tests/test_was_operad_levels.py -v
```
