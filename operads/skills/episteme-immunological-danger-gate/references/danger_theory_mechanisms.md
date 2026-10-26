# Danger Theory Mechanisms & Software Translation

## Biological Foundation
In 1994, Polly Matzinger proposed the Danger Theory of immunology, challenging the
classical Self vs. Non-Self discrimination model. The immune system does not primarily
care about foreignness; it cares about damage.
- **Signal 1:** Antigen recognition via T-cell receptor (TCR) binding peptide-MHC.
- **Signal 2:** Co-stimulatory signals (CD80/CD86 binding CD28) released by antigen-presenting
  cells (APCs) only when tissue damage releases endogenous alarmins/DAMPs (e.g. heat shock proteins, ATP, HMGB1).
- **Outcome:** Signal 1 without Signal 2 leads to T-cell anergy (tolerance). Signal 1 with Signal 2 triggers activation.

## Software Analogy in Reasoning Swarms
- **Signal 1:** A string or AST contains a pattern matching a known red-team prompt,
  a forbidden opcode, or a bug pattern (e.g. `assert False`, `TODO`).
- **Signal 2:** The candidate turn actually causes structural failure:
  - Authority escalation beyond declared envelope.
  - Defect count non-descent ($\Phi_1 > 0$, $\Gamma_2 > 0$).
  - Cryptographic hash chain corruption or byte-level encoding violation.
- **Tolerance:** When a developer or agent discusses bugs or writes a negative test containing
  "attack" strings without triggering Signal 2, the system tolerates the prompt without halting.
