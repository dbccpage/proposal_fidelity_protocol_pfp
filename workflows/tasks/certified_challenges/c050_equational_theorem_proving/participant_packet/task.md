# Challenge C050: Equational Theorem Proving with Checkable Rewrite Proofs

## Problem Description
Participants must prove equational goals from a given set of equational axioms via explicit, step-by-step term rewrite sequences, or refute non-theorems with finite algebraic countermodels.

### Term Representation
Terms are encoded in prefix JSON format:
- Variables: strings such as `"x"`, `"y"`, `"z"`.
- Ground constants: strings such as `"a"`, `"b"`, `"e"`.
- Compound terms: lists `[function_name, arg0, arg1, ...]`.
  Example: `f(f(x))` is represented as `["f", ["f", "x"]]`.
  Example: `x * y` is represented as `["m", "x", "y"]`.

### Subterm Positions
A position `pos` is a list of 0-based indices navigating into the argument subterms:
- `[]`: the root term itself.
- `[0]`: the first argument of the root term.
- `[1, 0]`: the first argument of the second argument.

### Output Contract
For a given input `{"case_id": "...", "axioms": [[l1, r1], ...], "goal": [s, t]}`:

1. **PROOF (for theorems):**
   ```json
   {
     "case_id": "...",
     "status": "SOLVED",
     "kind": "PROOF",
     "lemmas": [],
     "steps": [
       {
         "axiom": 0,
         "dir": "lr",
         "pos": [0],
         "subst": {"x": ["f", "a"]},
         "result": ["f", "a"]
       }
     ]
   }
   ```
   Every step replaces `subterm(curr, pos) = subst(l)` with `subst(r)` (for `"lr"`), resulting in `result`. The chain starts at `s` and ends at `t`.

2. **COUNTERMODEL (for non-theorems):**
   ```json
   {
     "case_id": "...",
     "status": "SOLVED",
     "kind": "COUNTERMODEL",
     "size": 2,
     "tables": {
       "m": [[0, 0], [1, 1]]
     },
     "assignment": {
       "a": 0,
       "b": 1
     }
   }
   ```
   Every axiom holds for all assignments in `{0, ..., size-1}`, and the goal evaluates to unequal values under `assignment`.

3. **OUT_OF_SCOPE (for malformed inputs):**
   ```json
   {
     "case_id": "...",
     "status": "OUT_OF_SCOPE",
     "witness": "<reason>"
   }
   ```
