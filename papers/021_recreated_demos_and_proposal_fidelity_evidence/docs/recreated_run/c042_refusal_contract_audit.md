# C042 retained refusal-contract mismatch

The closed `final_bindings_v4/C042/evaluations.jsonl` retains the literal solver outputs and authoritative branch-gate verdicts. These three cases are not new adapter exceptions. The solver emits the retained case metadata's expected `OUT_OF_SCOPE`, while the current gate rejects it under the correction notice's narrower rule: refusal is warranted only when canonical CNF construction fails.

| Case | Retained input | Original solver guard | Current judge behavior |
|---|---|---|---|
| `c042_poison_02` | `pigeons=-1`, `holes=2` | Rejects nonpositive dimension. | Unchecked PHP encoder iterates empty pigeon ranges and produces `p cnf 0 0`; construction succeeds. |
| `c042_poison_08` | `pigeons=0`, `holes=0` | Rejects nonpositive dimension. | Unchecked PHP encoder produces `p cnf 0 0`; construction succeeds. |
| `c042_poison_04` | `p cnf 2 5` followed by one clause, `1 2 0` | Rejects five declared clauses versus one actual clause. | `get_canonical_cnf` returns and hashes the supplied text without validating the header count. |

Negative PHP population is outside the solver's explicit family boundary. A zero-dimensional PHP can describe a trivial empty instance mathematically, but it is outside that same retained positive-dimension guard. The third input has a malformed DIMACS clause count. The DRAT parser also explicitly ignores header/count mismatch. Thus the gate's literal phrase “well-formed case” does not establish input validity: its actual test is constructibility, including unchecked encodings and raw supplied text. The 2026-09-29 participant-task correction binds refusals to that test, so the observed three rejections are faithful execution of the current contract while exposing inconsistent boundary definitions in the retained package.

This audit changes no mathematical algorithm, input, witness, gate or pass count. The replay's 61 accepted cases, three residuals and 48 rejected mutations remain literal. The evaluator has SAT and DRAT branches; it is one declared evaluator and establishes no separate checker provenance or fresh model result.
