# Track 400: Professional Researchers (Physics, Swarms & Logic)

AuthorityEffect: None.

## 25-Lesson Syllabus

| Lesson ID | Title | Core Concept | Existing Anchor |
| :--- | :--- | :--- | :--- |
| **400.01** | [Inspecting the Decode Simplex](concepts/lesson_400_01_inspecting_the_decode_simplex.md) | Analyzing unnormalized logits, softmax simplices, and logprobs | `mechanism` |
| **400.02** | [Carrier Projection at Decode Time](concepts/lesson_400_02_carrier_projection_at_decode_time.md) | Forcing 0.04% -> 100% on-carrier mass via negative infinity masking | `CarrierProjection` |
| **400.03** | [Reading Attention Heads](concepts/lesson_400_03_reading_attention_heads.md) | Distinguishing invariant carrier heads from unconstrained fluff heads | `09_attention_entropy` |
| **400.04** | [4D Additive Attention Masking](concepts/lesson_400_04_4d_additive_attention_masking.md) | Steering last-layer attention from 0.058 -> 1.0 on key tokens | `local_attention_steering.py` |
| **400.05** | [KV-Norm Dynamics and Compression](concepts/lesson_400_05_kv_norm_dynamics_and_compression.md) | Frobenius norm invariance and 71% context memory compression | `KV-Norm Mechanics` |
| **400.06** | [Density Matrices from Distributions](concepts/lesson_400_06_density_matrices_from_distributions.md) | Translating discrete probabilities into density matrices rho | `QUANTUM_ENGINES.md` |
| **400.07** | [Purity, von Neumann Entropy, Coherence](concepts/lesson_400_07_purity_von_neumann_entropy_coherence.md) | Trace-diagnostics of quantum coherence on reasoning paths | `density_matrix.rs` |
| **400.08** | [The H^1 to Density Bridge](concepts/lesson_400_08_the_h_1_to_density_bridge.md) | The Phi_1 residual as a density carrier rho(h) = |h><h| / <h, h> | `density_from_h1.rs` |
| **400.09** | [Harmonic Density and Betti Numbers](concepts/lesson_400_09_harmonic_density_and_betti_numbers.md) | Hodge Laplacian Delta_1 nullspace dimension equals Betti number b_1 | `harmonic_density.rs` |
| **400.10** | [Quantum Channels as Noise Models](concepts/lesson_400_10_quantum_channels_as_noise_models.md) | Depolarizing and amplitude-damping models of model hallucination | `quantum_channel.rs` |
| **400.11** | [Physics of the Fermion Sign Problem](concepts/lesson_400_11_physics_of_the_fermion_sign_problem.md) | Exponential signal-to-noise collapse <sign> -> 0 in volume and beta | `MERON_COLLAPSE.md` |
| **400.12** | [Merons as Cohomological Obstructions](concepts/lesson_400_12_merons_as_cohomological_obstructions.md) | Identifying sign-flipping clusters as non-trivial cocycles | `meron_collapse.py` |
| **400.13** | [Exact Parity Cancellation](concepts/lesson_400_13_exact_parity_cancellation.md) | Proving every meron configuration evaluates to exactly zero | `meron_flip_sum` |
| **400.14** | [The Positive Sector Manifold](concepts/lesson_400_14_the_positive_sector_manifold.md) | Restricting search to zero-meron subspaces as a LAND operation | `Positive Sector` |
| **400.15** | [The NP-Hardness Boundary](concepts/lesson_400_15_the_np_hardness_boundary.md) | Troyer-Wiese theorem: why general sign problems remain NP-hard | `Troyer-Wiese 2005` |
| **400.16** | [Bounded Quantifier Alternation](concepts/lesson_400_16_bounded_quantifier_alternation.md) | Delta_0^0 classification and finite game geography | `bounded_alternation.md` |
| **400.17** | [Non-Turing Completeness as Safety](concepts/lesson_400_17_non_turing_completeness_as_safety.md) | Why bounded alternation prevents infinite divergence in governors | `N10_non_turing` |
| **400.18** | [Autopoietic Cohomology Self-Repair](concepts/lesson_400_18_autopoietic_cohomology_self_repair.md) | Axioms G1, G2, G3, G4 governing self-healing complexes | `N11_godel_capable` |
| **400.19** | [The Gödel Point](concepts/lesson_400_19_the_g_del_point.md) | Self-application probes and divergence boundaries in formal systems | `N12_the_godel_point` |
| **400.20** | [The R-B-G Proof Program](concepts/lesson_400_20_the_r_b_g_proof_program.md) | Unifying Relational Grammar, Boundary Cohomology, and Geometry | `N15_the_rbg_proof` |
| **400.21** | [The LGGR Paradox](concepts/lesson_400_21_the_lggr_paradox.md) | Local Green does not certify Global Red: failure of local certificates | `lggr_prime_seam` |
| **400.22** | [Detector Adequacy and Asymmetric Verdict](concepts/lesson_400_22_detector_adequacy_and_asymmetric_verdict.md) | Why RED is sound but GREEN is unsound without detector adequacy | `verdict.rs` |
| **400.23** | [The Adversary Swarm Axiom](concepts/lesson_400_23_the_adversary_swarm_axiom.md) | Enforcing zero unpriced rewrite density across multi-agent swarms | `Adversary Swarm Axiom` |
| **400.24** | [Dialectical 9-Dot Gauge Breaks](concepts/lesson_400_24_dialectical_9_dot_gauge_breaks.md) | Shattering locked carrier framings via orthogonal surprise injections | `ow-bureau-gauge-breaks` |
| **400.25** | [Professional Capstone](concepts/lesson_400_25_professional_capstone.md) | Orchestrating a 10-agent adversarial swarm with local CI receipts | `AutoP Architecture` |
