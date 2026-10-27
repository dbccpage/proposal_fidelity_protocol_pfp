# Epistemic Immune System (EIS) Computational Tools

**AuthorityEffect:** None.

This package contains diagnostic, verification, and simulation engines for the Epistemic Immune System across Levels 00–10.

## Modules

- `eis_core.py`: Core dataclasses and immune components:
  - `InnateBarrier` (Level 00)
  - `RolePartition` (Level 01)
  - `FixtureGate` (Level 02)
  - `ThymusGate` (Level 03)
  - `TwoSignalGuard` (Level 04)
  - `SupportPolicy` (Level 05)
  - `ProvisionalCustody` (Level 06)
  - `ClonalSelectionEngine` (Level 07)
  - `TregSupervisor` (Level 08)
  - `ExternalAdmissionBoundary` (Level 09)
  - `AntimorphismEmitter` (Level 10)

## Running Tests

Execute targeted tests using Python 3.12:

```bash
py -3.12 -m pytest education/documentation/009_oeeis/code/tests/test_eis_levels.py -v
```
