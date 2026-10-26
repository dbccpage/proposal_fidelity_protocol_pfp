# Epistemic Immune System (EIS)

[`eis/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/eis)
screens proposals for known failure patterns and keeps the evidence of past
failures. It borrows its vocabulary from immunology, but every mechanism is a
small, exact rule.

## Main ideas

**Antibodies.** Detector rules for recurring failures, such as an unsupported
claim or a silently skipped check. A harvested antibody is only a candidate;
only human-admitted antibodies may be used (`admitted_antibody_query.py`).
Retired antibodies are recorded so they are never harvested again.

**Two signals.** A detector match alone does not act. A learned guard activates
only on two independent signals: a detector hit and a separate danger
observation from the host (`danger_gate.py`, `guard_activation.py`).

**Negative selection.** Before admission, a detector rule is screened against a
panel of known-good examples, so it does not block valid answers (`thymus.py`).
Blocking a valid answer is called false suppression, and Paper 003 shows how a
reasonable-looking detector can do it.

**Regulation.** A learned detector can be suspended in a stated scope when an
independent check shows it blocked something benign (`treg.py`,
`regulate_guard.py`). Detectors that never fire are counted (`clonal_selection.py`).

**Repetition is not evidence.** External proposals are candidates by default,
and seeing the same one many times does not make it true
(`external_admission.py`).

**Safe patterns.** Detector rules use a bounded subset of regular expressions so
a rule cannot run away (`safe_pattern.py`).

## Layout

| Folder | Role |
| --- | --- |
| `domain/` | The rules above, failure classes and canonical receipt ids |
| `use_cases/` | Admission, guard activation, regulation, screening and the transferable guard library |
| `antibodies/` | Definitions, templates, candidates and admission records |
| `antiskills/` | Admitted anti-skills and fixtures |
| `receipts/` | Recorded custody and repair receipts |
| `documentation/` | [Authenticated custody](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/eis/documentation/authenticated_custody.md): signed admission decisions under an explicit trust policy |

## Custody

Admission decisions and observations can be signed and checked against an
operator-supplied trust policy. A verified signature identifies a configured
key, not a person or a correct measurement. There is no built-in production key
and no automatic admission.

Related papers: [003](Paper-003.md), [006](Paper-006.md).
