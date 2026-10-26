# C058: Straight-Line Superoptimization — Participant Task Specification

## 1. Objective

Synthesize an exact, verified straight-line superoptimizer that shortens straight-line bit-vector programs to equivalent programs of length at most `target_len`.

## 2. IR Grammar and Semantics

Programs operate over declared inputs (e.g. `["x"]` or `["x", "y"]`) and temporaries at bit width `w ∈ {8, 16, 32, 64}`.

All arithmetic is modulo $2^w$.
Shift amounts are taken modulo $w$ (i.e. `shift % w`).

Supported instructions `[target_var, op, ...]` in topological execution order:
- `["t", "const", c]`: immediate constant `c & ((1 << w) - 1)`
- `["t", "not", a]`: bitwise NOT `(~a) & ((1 << w) - 1)`
- `["t", "neg", a]`: two's complement negation `(-a) & ((1 << w) - 1)`
- `["t", "add", a, b]`: `(a + b) & ((1 << w) - 1)`
- `["t", "sub", a, b]`: `(a - b) & ((1 << w) - 1)`
- `["t", "mul", a, b]`: `(a * b) & ((1 << w) - 1)`
- `["t", "and", a, b]`: `(a & b) & ((1 << w) - 1)`
- `["t", "or", a, b]`: `(a | b) & ((1 << w) - 1)`
- `["t", "xor", a, b]`: `(a ^ b) & ((1 << w) - 1)`
- `["t", "shl", a, b]`: `(a << (b % w)) & ((1 << w) - 1)`
- `["t", "lshr", a, b]`: logical right shift `(a >> (b % w)) & ((1 << w) - 1)`
- `["t", "ashr", a, b]`: arithmetic right shift preserving sign bit at width `w`

## 3. Input Case Format

```json
{
  "case_id": "so_ex_01",
  "width": 8,
  "inputs": ["x", "y"],
  "ops": [
    ["t1", "or", "x", "y"],
    ["t2", "and", "x", "y"],
    ["t3", "sub", "t1", "t2"]
  ],
  "out": "t3",
  "target_len": 1
}
```

## 4. Expected Response Format

### A. Solved Case
```json
{
  "case_id": "so_ex_01",
  "status": "SOLVED",
  "ops": [
    ["r0", "xor", "x", "y"]
  ],
  "out": "r0"
}
```

### B. Provably Infeasible / Unsat Target Length
```json
{
  "case_id": "so_ex_09",
  "status": "UNKNOWN",
  "code": "NO_SHORTER_FOUND"
}
```

### C. Out of Scope / Malformed Case
```json
{
  "case_id": "so_ex_12",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "UNDEFINED_OPERAND",
    "op_index": 2,
    "name": "undefined_temp"
  }
}
```

## 5. Verification Rules

1. Every instruction in `ops` must use only variables defined earlier in the sequence or declared inputs.
2. The total count of instructions in `ops` must satisfy `len(ops) <= target_len`.
3. The candidate program must be semantically equivalent to the original program across all inputs (exhaustive at $w=8$, extensive corner-case and randomized stress test at $w \ge 16$).
