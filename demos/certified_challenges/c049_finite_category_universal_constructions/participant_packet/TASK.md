# C049: Universal Constructions in Finite Categories

**Domain:** e_formal_math
**Tier:** T2
**Protocol:** SG-CP v1

## Problem Description

Given a finite category $C$ ($\le 12$ objects, $\le 60$ morphisms) with objects, named morphisms, and composition table, compute:
1. **Limits / Colimits**: Product, equalizer, pullback, terminal object, and their duals (coproduct, coequalizer, pushout, initial object). Output `EXISTS` with apex and legs, or `DOES_NOT_EXIST`.
2. **Adjunctions**: Given functors $F: C \to D$ and $G: D \to C$, output `ADJOINT` with unit $\eta$ and counit $\varepsilon$, or `NOT_ADJOINT` with a hom-set cardinality or universal arrow witness.

## Output Schema

Your solution must implement `solve(case: dict) -> dict`.

### Limit / Colimit Exists
```json
{
  "case_id": "cat_ex_01",
  "status": "SOLVED",
  "kind": "EXISTS",
  "apex": "0",
  "legs": {
    "1": "p",
    "2": "q"
  }
}
```

### Limit / Colimit Does Not Exist
```json
{
  "case_id": "cat_ex_04",
  "status": "SOLVED",
  "kind": "DOES_NOT_EXIST"
}
```

### Adjunction Certified
```json
{
  "case_id": "cat_ex_10",
  "status": "SOLVED",
  "kind": "ADJOINT",
  "unit": {"0": "id0"},
  "counit": {"0": "id0"}
}
```

### Refusal (Not Adjoint with Witness)
```json
{
  "case_id": "cat_ex_09",
  "status": "SOLVED",
  "kind": "NOT_ADJOINT",
  "witness": {
    "type": "HOM_CARDINALITY",
    "c": "0",
    "d": "1",
    "lhs": 2,
    "rhs": 1
  }
}
```
