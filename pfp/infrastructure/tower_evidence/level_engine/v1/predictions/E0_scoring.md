# Round E0: predictions scored

AuthorityEffect: None.

The plaintext `E0_predictions.md` is byte-identical to the digest frozen in
`FROZEN.json` (commit `ea9b40a`), which precedes every spec and record commit.
It is scored here without editing it. PRE-OBSERVED parts were seen while the
engine core was built and do not count.

| id | verdict | evidence |
| --- | --- | --- |
| P0 | HIT | `bare_inscription`: type A; `repo_content`; census `bytes_exact: apparatus`; `supply_is_inert: true`; the refused cases are booked in the loss ledger (`source.refused_cases`, DROPPED) and in the evidence's `anti_aligned` block. |
| P1 | HIT | Lineages L.mu1 3, F.mu1 5, L.mu2 1, F.mu2 1 (`unique_class`, 2 literal minima each). All 10 classes map to 1 packet; the loss ledger books the mu1 rows WEAKENED and the mu2 rows PRESERVED. Census: `shape` derivability, `source_kept` and `pairing` apparatus. |
| P2 | HIT | `edge_endpoints`: own negative `NON_ADMISSIBLE` (sealed `step` refused an out-of-range argument); `near_source` and `near_target` each fail exactly their closure; `near_protect` fails exactly `protect`, grade none over a CLOSED class of size 1. |
| P3 | HIT | `cell_faces`: own negative `NON_ADMISSIBLE` (arity); the repeated-point cell fails `side_distinct`, grade none by `denied_terminal` (CLOSED_BY_THEOREM); the missing-side fixture's refutation names exactly that side. |
| P4 | PARTIAL: one MISS | Positive `unique_class`, 2 literal witnesses, cost 2: hit. Own negative fails the claim-only part: hit. Three cells on one side: none over CLOSED, 42 of 42, bound 3: hit. **Miss:** naming one sign does not give a tie. Exchanging the two cells, with their outer points, is still an automorphism, so the two witnesses stay isomorphic (`unique_class`). An extra fixture that also breaks the cell symmetry (`named_sign_uneven`) gives the tie of two classes. It was added after this result was seen, and is labelled as such in its note. |
| P5 | HIT | `distance_form`: `complete`, `symmetric` and `one_value` are derivability clauses (so is `typed`, which was not predicted); `diagonal_zero` and `form_positive` are decoded (`CAP-SUPPLIED`). The own negative fails at leading minor 2, the degenerate fixture at minor 3. Status `UNRESOLVED`, missing `lean.exact.qn`. |
| P6 | HIT | Every relational clause of `edge_endpoints`, `cell_faces` and `cell_orientation` is derivability (22 of 22); at `distance_form` exactly the two decoded clauses survive the stub. |
| P7 | HIT (unit test only) | A proposal whose capability acts trivially fails condition 10 with `RR-TRIVIAL-LIFT` (`tests/test_stage.py`). The rest of P7 was pre-observed. |
| P8 | PARTIAL: one MISS | On the first run, the four-item bound fired `GUARD_EMBARGO` and the float fired `RR-FLOAT`: hits. **Miss:** on the first run the claim overwrite was caught by the count guard (`RR-EXHAUSTION`), not by `CLAIM_FROZEN`. The engine was then strengthened, and it now fires `CLAIM_FROZEN`; see `INJECTIONS.md`. The first run's recoveries were masked by stale bytecode in the injector, not by the gates. |

Tally: 7 hits, 2 partial (one miss each). No prediction was edited.
