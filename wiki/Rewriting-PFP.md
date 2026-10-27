# PFP rewriting: overview

Part of [Rewriting](Rewriting.md). Next: [Residual repair](Rewriting-PFP-Residual-Repair.md) · [Dialects and pilot](Rewriting-PFP-Dialects.md)

PFP is where all the earlier layers meet a real task. A proposal arrives, is
rewritten into some representation, is checked by the host, and may be
repaired. The question at every step is **which kind of rewrite is this?**

## The five layers in one picture

```text
Level 4  PFP          envelopes, lineage, schema contracts, fail-closed host gates
Level 3  MSS-N        strict wire trees, polygraphs, confluence, matrix form
Level 2  S(n)         directed cuts, retractions r_n, refusal propagation
Level 1  Genesis      regime state, candidate delta streams, Reading L vs F
Level 0  Pre-Genesis  quiescent baseline, observational separation, raw marks
```

These five layers are separate from the six research stages P0–P5, the eleven
public runtime stages and the 101 numbered teaching specifications. Matching
numbers do not mean matching meanings.

## What kind of rewrite is it?

| Kind | Ask | What a pass can establish |
| --- | --- | --- |
| Representation | Can the decoder recover the original carrier and orientation? | A round trip on the stated domain; no gain in reasoning |
| Witness replacement | Does a complete replacement satisfy the original task under a fresh binding? | The predicates checked on that certificate |
| Cochain repair | Is the change exactly `d0*a` on the fixed maps? | The same quotient class; the optimum is unchanged |
| Problem change | Were carrier, observations, norms, maps or assumptions changed? | A different problem, needing its own provenance |
| Prompt heuristic | Does a controlled comparison improve a declared outcome? | Bounded evidence for those tasks, that model and that budget |

## Five transformation laws

1. **No smuggled containers in Tier S.** No whitespace or separators inside
   strict packets; siblings sit side by side.
2. **Presentation is not admission.** Showing a string does not put it in the
   state.
3. **Retractions are partial inverses.** `r_n(u_n(x)) = inl(x)`, and anything off
   the image is refused as `NON_DESCENT`.
4. **Operators need a licence.** Digits have no arithmetic meaning until the
   prompt grants permission to add, subtract, multiply or contract.
5. **Intermediate witnesses.** A composite answer such as `x + y = 3` is refused
   unless the reasoning establishes each part (`x = 1`, `y = 2`).

## The one-line test

Change the direct edge of a square from 7 to 4 and the face sum becomes 0. Does
that show the original optimum was 0? **No.** It changed the observed data,
which is a new problem. The original optimum is still 3. See
[Residual repair](Rewriting-PFP-Residual-Repair.md) for the full example.

## Sources

- [`education/004_oepfp/rewriting/README.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/education/004_oepfp/rewriting/README.md)
- [`finite_qm_residual_repair.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/education/004_oepfp/rewriting/finite_qm_residual_repair.md)
- [`pfp_master_rewriting.md`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/education/004_oepfp/rewriting/pfp_master_rewriting.md)
