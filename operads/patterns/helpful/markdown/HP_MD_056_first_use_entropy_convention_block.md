# HP_MD_056: First-Use Entropy Convention Block

**AuthorityEffect:** None.
**Category:** Markdown / Mathematical Prose
**Status:** ENFORCED

## Context
When stating entropic inequalities, total correlation bounds, or information-theoretic limits in mathematical manuscripts.

## Pattern
Before an entropic inequality is stated or proved:
1. Define the entropy definition and logarithm base explicitly: $S_b(\sigma) := -\operatorname{Tr}(\sigma \log_b \sigma)$.
2. Define derived entropic functionals:
   - Total correlation: $\operatorname{TC}_b(\rho) := \sum_{i \in V} S_b(\rho_i) - S_b(\rho)$.
   - Mutual information: $I_b(u:v) := S_b(\rho_u) + S_b(\rho_v) - S_b(\rho_{uv})$.
3. Explicitly state the counted population and parameter ranges:
   - $N = |V|$, $a \ge 0$, $\eta \in [0, 1]$.
4. Disambiguate variable symbols from the logarithm base (e.g., use vertex labels $u, v$ rather than $a, b$ when $b$ is the logarithm base).
5. Ensure Pinsker constants match the chosen logarithm base and trace-norm convention (e.g., $D_e(t)^2 / (2 \ln b)$ for base $b$).
