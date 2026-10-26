# Mode 12: Carrier Spaces & Simplicial Triangulation Specification

**Mode ID:** 12  
**Cluster:** Cluster III: Group & Cochain Structure  
**AuthorityEffect:** None  

## Overview

Mode 12 governs the formal declaration, representation, and topological typing of carriers—including simplicial complexes $K = (V, E, F)$, continuous manifolds $\mathbb{R}^n$, and discrete lattices $\mathbb{Z}$.

## Integration with Demo 001 & ADR

Drawing from `demo_001/round_1/p_star_02_r1_carrier.yaml`, `domain/carrier.py`, and `demo_001/ideas.md`:

### 1. The Carrier Trilemma

Every computational or differential difference expression $d_0(f)(e) = f(\text{tgt } e) - f(\text{src } e)$ requires a declared carrier with vertices, edges, source, and target:
1. Either difference is not primitive,
2. Or carrier is itself a represented difference causing regress,
3. Or the loop is cut by a typed boundary because the two uses of "Structure" are distinct objects.

### 2. Carrier Type Taxonomy

When auditing prompts or mathematical models, Mode 12 categorizes carriers into three disjoint types:

| Carrier Type | Domain Structure | Measure / Differential | Admissible Operator |
|---|---|---|---|
| **Continuous Manifold** | Interval $[a, b] \subset \mathbb{R}$ | Lebesgue measure $dx$, differential 1-forms | Continuous integration $\int_a^b f(x)\,dx$ |
| **Discrete Lattice** | Integer sequence $\{a, \dots, b\} \subset \mathbb{Z}$ | Counting measure $\mu_{\text{count}}$, step $\Delta x$ | Discrete summation $\sum_{x=a}^b f(x)$ |
| **Finite Simplicial Complex** | Cell complex $K = (V, E, F)$ over $\mathbb{Q}$ | Discrete cell weights | Cochain coboundary $d_0, d_1$ |

### 3. ProtoSupport Pre-Carrier Obligations

As defined in `domain/carrier.py`, difference requires seven foundational ProtoSupport obligations before a carrier can become typeable:
- `has_support`: Non-empty ontological backing.
- `has_addressability`: Capacity to index distinct sites.
- `has_distinguishability`: Ability to separate sites ($u \ne v$).
- `has_orientation`: Directional asymmetry ($\text{src } e \ne \text{tgt } e$).
- `has_boundary_capacity`: Delimitation between inside and outside.
- `has_witnessability`: Generation of verifiable trace records.
- `has_markability`: Capacity to write or alter local state.
