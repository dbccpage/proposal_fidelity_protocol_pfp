# Epistemic Immune System (EIS)

[`eis/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/eis)
screens proposals for known failure patterns and keeps the evidence of past
failures. It borrows its vocabulary from immunology, but every mechanism is a
small, exact rule, and none of them grants authority.

## The idea in one picture

```text
 past failure ──▶ farmed antibody (CANDIDATE)
                        │  negative selection (thymus), bounded pattern
                        │  distinct observations, bound fixtures
                        ▼
                 human admission decision (signed, scoped)
                        │
                        ▼
 new proposal ──▶ Signal 1: an admitted detector matches
              ──▶ Signal 2: an independent host check observes damage
                        │
                        ▼
             two-signal gate: TOLERATED / DIAGNOSTIC_ONLY /
                              DEFENSIVE_LOCKDOWN / QUARANTINED
                        │
                        ▼
          regulation: a detector that blocks valid answers is downgraded
```

## Pages in this section

| Page | Read it to... |
| --- | --- |
| [Two-signal gate](eis_two_signal_gate.md) | See why a detector match alone never blocks, how the second signal is kept independent, and how a quorum of sensors is counted |
| [Antibody lifecycle](eis_antibody_lifecycle.md) | Follow an antibody from farming to admission or retirement: negative selection, safe patterns, distinct observations and the retirement register |
| [Regulation and custody](eis_regulation_and_custody.md) | See how detectors that suppress valid answers are downgraded, and how admission decisions are signed and checked |
| [Exclusion hypotheses](eis_exclusion_hypotheses.md) | See why every exclusion carries its cheapest falsifier, how agreement is counted by model family, and which dead branches are still tested |

## Rules that hold throughout

1. **Candidate by default.** Anything farmed starts as `CANDIDATE`, and there is
   no parameter to start it otherwise.
2. **Repetition is not evidence.** Replaying one observation ten times counts
   once.
3. **Two independent signals.** A detector match acts only together with a
   separate host observation of damage, and that observation may not be
   derived from the match.
4. **Missing is not clear.** A detector that was not run, or a service that was
   unavailable, is recorded as not measured. It is never read as "no problem".
5. **Named, not deleted.** A detector that was wrong is retired by name, so the
   same mistake cannot be farmed again unnoticed.
6. **Exclusions are hypotheses.** Every exclusion names the cheapest test that
   would refute it, and agreement among seats of one model family counts once.
7. **AuthorityEffect: None.** Screening, promotion and retirement compute
   eligibility or remove a guard. They never admit or promote anything by
   themselves.

## Layout

| Folder | Role |
| --- | --- |
| `domain/` | The rules: danger gate, thymus, regulation, safe patterns, admission criteria, retirement, failure classes |
| `use_cases/` | Admission assessment, guard activation, regulation, screening, the admitted-antibody query and the transferable guard library |
| `antibodies/` | Definitions, templates, candidates and admission records |
| `antiskills/` | Admitted anti-skills, mined proposals and fixtures |
| `infrastructure/` | Pharmacy adapters (the native pharmacy is reached through the host), custody, the immune bench |
| `receipts/` | Recorded custody and repair receipts |
| `documentation/` | [Authenticated custody](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/eis/documentation/authenticated_custody.md) |

## How the EIS connects to the rest

- **Operads.** Antibodies and anti-ops are bound to individual prompts through
  the prompt hierarchy, and anti-skills attach at vertex, edge or tree sites of
  a prompt tree. See [Prompts as operad trees](operads_prompt_trees.md) and
  [Rewriting and packetization](operads_rewriting_and_packetization.md).
- **Prompt Civilization.** Immunity propagates along prompt lineages, with
  attenuation and scope limits. See [Mutation and inheritance](pciv_mutation_and_inheritance.md).
- **Bounded repair.** The repair workflow submits its observations to the EIS
  and records `NOT_MEASURED` honestly. See [Bounded repair](operads_bounded_repair.md).

Related papers: [003](paper_003.md) (admitting detectors and testing their
effects) and [006](paper_006.md) (retained failure evidence and controlled reuse).
