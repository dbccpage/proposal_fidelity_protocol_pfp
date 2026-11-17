# Clonal Selection & Half-Life Decay Dynamics

## Biological Background
Frank Macfarlane Burnet proposed the Clonal Selection Theory (1957):
1. Diverse lymphocytes pre-exist with distinct antigen receptors.
2. An encountered antigen binds selectively to lymphocytes having complementary receptors.
3. Activated lymphocytes proliferate and form clones.
4. In germinal centers, activation-induced cytidine deaminase (AID) introduces point mutations
   at rates a million times higher than normal genes (somatic hypermutation).
5. Clones with improved affinity are selected; low-affinity clones die by apoptosis.
6. Once the infection is cleared, effector cells undergo apoptosis, while a small memory pool
   persists. Circulating antibody titers decay with an exponential half-life ($t_{1/2}$).

## Prompt Engineering & Context Management
LLM prompt context windows have finite token capacity. Loading hundreds of anti-skills
exhausts the context budget and slows inference:
$$N(t) = N_0 e^{-\lambda t}$$
By tracking `runs_idle` and assigning each rule a half-life $t_{1/2}$, idle rules naturally
evaporate from active prompt context while remaining archived in the append-only ledger.
Active threats continually refresh their antibodies.
