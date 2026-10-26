# Getting started

## The idea in one example

Suppose three people each claim the price difference between two of three
currencies. Each claim on its own may look reasonable, but if the differences
around the loop do not add up to zero, the claims cannot all be true at once.
PFP treats each claim as a **proposal**, computes how far the set of claims is
from being consistent (the **obstruction**), and only admits a change if an
independent check shows it does not make things worse. Every step, admitted or
refused, is written to a **receipt** so the session can be replayed.

The point is not that the checker is clever. The point is that the proposer
never grades its own work, and that a pass only licenses what was actually
checked.

## Three reading routes

**New to the topic.** Read
[Paper 000](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/000_pfp_introduction),
an introductory preprint that needs only marks, relations, S(n), MSS-N and
packets. It ships a standard-library teaching checker and a workbook with eight
gradual examples.

**Want to run a session.** Read the
[practitioner's guide (Paper 005)](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/005_pfp_practitioners_field_manual).
It follows one triangle through declaration, proposal, refusal, repair,
verification and restoring a saved snapshot. Its examples run with plain
Python:

```powershell
cd papers/005_pfp_practitioners_field_manual
python code/play_demo.py
python code/study_capstone.py
```

**Want a worked finite example.** Read
[Paper 001](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/001_pfp_discrete_cochain_retraction_and_toy_involutions),
which separates residual improvement, obstruction, safety and termination on a
small graph.

## Requirements

Most paper packages need Python 3.10 or later (Paper 000 asks for 3.12) and no
third-party runtime packages. Test extras, where present, install with
`python -m pip install ".[dev]"` from the package folder. On Windows, `py -3.12`
can replace `python`.

## Next

- [Core concepts](Core-Concepts.md) for the vocabulary.
- [Papers](Papers.md) for the full reading list.
- [PFP Lab](PFP-Lab.md) to try small scenarios.
