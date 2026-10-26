# Detailed definition: Publication Review Remediation & Package Re-certification (1)

**AuthorityEffect:** None.

Parent: [Publication Review Remediation & Package Re-certification](../../../../../rules/papers/rl_publication_review_remediation_and_recertification_discipline.md). Load for the matching predicate, not every task.

# Rule: Publication Review Remediation & Package Re-certification Discipline

**AuthorityEffect:** None.

This rule codifies the XeLaTeX compilation log synchronization and package re-certification protocol, atomic cross-layer review remediation, mechanization-manuscript scope parity, diagnostic model parameter strictness, and hermetic verification runtime requirements.

---

## XeLaTeX Build Log Synchronization & Package Re-certification Protocol

> **Full-Stack Paper Re-certification Invariant:**
>
> 1. **XeLaTeX Compilation Log & TOC Preservation:**
>    When compiling paper PDFs, XeLaTeX `.log`, `.toc`, and `.aux` compilation outputs must be preserved at the root of the deposit package alongside the `.pdf`. The `.toc` file must be verified to ensure section page numbers match actual rendered PDF pages (preventing page-off-by-one errors), and the `.log` file must report zero missing characters/glyphs and zero overfull horizontal boxes > 10pt.
> 2. **Mandatory 5-Step Re-certification Sequence:**
>    Whenever any packaged file (manuscript text, claim ledger, python script, or metadata document) is modified, the author/agent MUST execute the full 5-step re-certification sequence prior to release:
>    a. Regenerate checksum manifests (`regen_sha256sums.py`).
>    b. Replay computational verifications (`replay.py`).
>    c. Re-verify deposit certificates (`verify_certificate.py` -> `verdict: pass`).
>    d. Verify byte-identical reproducible ZIP build (`build_release_zip.py --check`).
>    e. Execute targeted unit test sweeps (`py -3.12 -m pytest code/tests/`).

---
