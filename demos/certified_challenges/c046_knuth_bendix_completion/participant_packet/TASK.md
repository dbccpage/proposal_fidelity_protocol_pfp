# C046: Knuth-Bendix Equational Completion with Joinability Certificates

**Domain:** `e_formal_math`  
**Tier:** `T3`  
**Protocol:** `SG-CP v1`  
**AuthorityEffect:** None  

## Problem Specification

Transform equational specifications $(E, >)$ over first-order terms into canonical, confluent, and terminating term rewrite systems (TRS) $R = \{l_1 \to r_1, \dots, l_k \to r_k\}$ using Knuth-Bendix completion.

### Tasks
1. **`COMPLETE`**:
   Given a set of equational axioms $E$ and a precedence ordering on function symbols:
   - Orient equations using Lexicographic Path Order (LPO) with symbol precedence.
   - Saturate critical pairs: for every overlap between rewrite rules, generate the critical pair $(c_1, c_2)$.
   - Reduce both sides to normal form.
   - If irreducible and different, orient and add to rule set; inter-reduce existing rules.
   - Emit joinability certificates for all resolved critical pairs.
   ```json
   {
     "case_id": "...",
     "status": "SOLVED",
     "task": "COMPLETE",
     "converged": true,
     "rules_count": 10,
     "rules": [
       {"lhs": "mul(e, x)", "rhs": "x"},
       {"lhs": "mul(inv(x), x)", "rhs": "e"},
       ...
     ],
     "joinability_certificates_count": 84
   }
   ```

2. **`CHECK_CONFLUENCE`**:
   Given an existing term rewrite system $R$:
   - Generate all critical pairs.
   - Check if all critical pairs are joinable under $R$.
   - Return `{"is_confluent": true/false, ...}`.

3. **`REDUCE`**:
   Given a TRS $R$ and a target term $t$:
   - Compute the unique canonical normal form $\hat{t}$.

### Refusals & Out of Scope
The solver must refuse with `status: "REFUSED"` and an explicit witness:
- `ORDER_FAILURE`: an unorientable equation where neither $s >_{\mathrm{lpo}} t$ nor $t >_{\mathrm{lpo}} s$.
- `MALFORMED_TERM`: syntax error or unmatched parentheses in term expression.
- `MAX_STEPS_EXCEEDED`: completion loop exceeds step budget (non-terminating completion).
