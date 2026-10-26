# Hill Cooperativity Curves & Allosteric Thresholding

## Mathematical Formulation
The Hill equation was originally introduced by Archibald Hill (1910) to describe the
sigmoidal binding of oxygen to hemoglobin:
$$\theta = \frac{[L]^n}{K_d + [L]^n} = \frac{[L]^n}{K^n + [L]^n}$$
Where:
- $[L]$: Ligand concentration (in our setting: aggregate signal strength $\sum c_i$).
- $n$: Hill coefficient.
  - $n = 1$: Hyperbolic non-cooperative Michaelis-Menten curve.
  - $n > 1$: Positive cooperativity (sigmoidal switch).
  - $n < 1$: Negative cooperativity.
- $K$: Apparent dissociation constant / half-maximal binding threshold ($H(K) = 0.5$).

## Application to Multi-Agent Consensus
When $n = 2.5$ and $K = 2.0$:
- Single agent report with $c_1 = 0.8$: $\theta = 0.8 \implies H(0.8) = \frac{0.8^{2.5}}{2^{2.5} + 0.8^{2.5}} \approx \frac{0.572}{5.657 + 0.572} \approx 0.092$ (Gate ignores isolated noise!).
- Two agreeing agents with $c_1 = 1.0, c_2 = 1.0$: $\theta = 2.0 \implies H(2.0) = 0.50$ (Threshold reached).
- Three agreeing agents with $\theta = 2.5 \implies H(2.5) \approx 0.66$ (Full confirmation).
This provides noise immunity against isolated agent hallucination or malicious injection.
