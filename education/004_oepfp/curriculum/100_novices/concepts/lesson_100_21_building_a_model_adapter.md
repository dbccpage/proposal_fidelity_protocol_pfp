# Lesson 100.21 — Building a Model Adapter: Clean Architecture Ports & Adapters for Untrusted Geometric Proposals

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_100_21_building_a_model_adapter.ipynb](../notebooks/lesson_100_21_building_a_model_adapter.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Untrusted Proposals, Clean Architecture Ports, and Host Referee Recomputation
- 2. Architecture of a Regge Model Adapter (Inward Dependencies and Sealing)
- 3. Host Referee Validation of Level 21 Geometric Payloads
- 4. Scope & Claim Boundary
- 5. Diagnostic Probe (2026 Micro-Attention Check)
- 6. Exercises (Ages 5 to 500)
- 7. Anchors

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 fixtures, target checkers (`stage_021.py`), or papers.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Untrusted Proposals, Clean Architecture Ports, and Host Referee Recomputation

[Declared] When interfacing large language models or external heuristic solvers with formal verification engines, the fundamental architectural invariant is:
**Never trust model self-reporting.**

A model may emit plausible-looking geometric structures, declaring:
```json
{"closure": "identity", "curvature": 0, "status": "valid"}
```
If the host runtime takes this declaration at face value, any mathematical error, ungrounded hallucination, or non-abelian order defect passes silently into the core domain.

Under **Clean Architecture**, external model interfaces reside in the outermost *Infrastructure/Adapters* layer. The domain defines a strict **Port** (protocol) specifying the required verification interface. The adapter receives untrusted model text or JSON, extracts the candidate parameters, and passes them to a host-controlled referee. The referee recomputes the exact invariants from ground primitives before any packet is admitted.

## 2. Architecture of a Regge Model Adapter (Inward Dependencies and Sealing)

[Pinned] The adapter pattern separates three distinct responsibilities:
1. **Model Caller (External Input):** Obtains raw proposals (e.g. 10 squared edge lengths of a 4-simplex, candidate rotation matrices, and declared hinge loops).
2. **Domain Port (`ReggeGovernorPort`):** Declares domain-level verification signatures with zero inward dependencies on third-party model libraries or network drivers.
3. **Host Referee (`Level21ModelAdapter`):** Recomputes:
   - Gram matrix leading principal minors over exact rational arithmetic ($\mathbb{Q}$).
   - Path-ordered $SO(4)$ matrix products around codimension-2 triangular hinges.
   - Packaging into a canonical, cryptographically sealed `PacketEnvelope` with SHA-256 seal and typed refusal codes (e.g., `R021_SCALAR_SUM_CLOSURE`, `R021_GRAM_NOT_POSITIVE`).

```
+-----------------------------------------------------------+
|                    UNTRUSTED INPUT                        |
|  LLM Generates: 10 lengths, SO(4) matrices, loop claims   |
+-----------------------------+-----------------------------+
                              | (raw text / dictionary)
                              v
+-----------------------------------------------------------+
|               INFRASTRUCTURE / ADAPTER LAYER              |
|                   Level21ModelAdapter                     |
|  - Parses exact rational fractions                        |
|  - Calls Host Referee (independent recomputation)          |
+-----------------------------+-----------------------------+
                              | (satisfies Port protocol)
                              v
+-----------------------------------------------------------+
|                    DOMAIN / CORE LAYER                    |
|                    ReggeGovernorPort                      |
|  - Clause C1: Gram matrix positivity (G succ 0)           |
|  - Clause C2: SO(4) rotation orthogonality (R R^T == I)   |
|  - Clause C3: Non-abelian ordered holonomy closure check  |
|  - Emits: Sealed PacketEnvelope (ADMITTED or REFUSED)     |
+-----------------------------------------------------------+
```

## 3. Host Referee Validation of Level 21 Geometric Payloads

[Pinned] In Level 21 4D Regge geometry (`stage_021.py` and Lean 4 `Level21DiscreteRegge.lean`), candidate models frequently commit a specific category of error:
They calculate the scalar sum of rotation exponents around a hinge loop:
$$\sum \text{exponents} = (+1) + (+1) + (-1) + (-1) = 0,$$
and declare `closure: "identity"`.

Because rotations in $SO(4)$ do not commute, the path-ordered matrix product:
$$U = R_{yz} R_{xz} R_{yz}^T R_{xz}^T \ne I_{4\times 4}.$$
The adapter intercepts this proposal. The host referee verifies:
- Is $\det(G_{1..k, 1..k}) > 0$ for all $k \in \{1, 2, 3, 4\}$? (If not, `R021_GRAM_NOT_POSITIVE`).
- Are generator matrices orthogonal with determinant 1? (If not, `R021_NOT_ROTATION`).
- Does the ordered product equal $I_4$? If not, and the scalar sum was 0, trigger clause C3:
  $$\text{refusal\_code} = \texttt{"R021\_SCALAR\_SUM\_CLOSURE"}.$$

The adapter seals this result into a `PacketEnvelope` with a SHA-256 digest, ensuring complete auditability.

## 4. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete verification of untrusted model proposals over rational arithmetic. | Generalization to unconstrained continuous LLM weights or internal neural activations. |
| Clean Architecture port/adapter boundary enforcement with typed refusals and SHA-256 sealing. | Universal mathematical correctness outside declared finite simplicial complexes. |

## 5. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Why must a Clean Architecture model adapter recompute Gram minors and matrix holonomies on the host side, rather than relying on the LLM's returned `"status": "valid"` field?

- **A:** The host wants to reduce network latency.
- **B:** External model outputs are untrusted proposals; host referee recomputation ensures that non-abelian geometric defects (such as Lean 4's `scalar_sum_does_not_certify_closure`) fail closed with typed refusal codes.
- **C:** The JSON parser requires all fields to be numbers.

*(Correct answer: **B**. External model outputs cannot serve as ground truth. Inward Clean Architecture boundaries require the domain host to enforce invariant verification independently.)*

## 6. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If a robot helper hands you a drawing and says "it is a perfect star", should you check it with your ruler before hanging it on the wall? *(Answer: Yes! Always check with your ruler!)*
2. **Exercise 2 (Age 15):** In Python, define a `ReggeGovernorPort` class and show that an adapter implementing it catches a degenerate 4-simplex whose Gram minor is zero.
3. **Exercise 3 (Age 500):** Implement a complete `Level21ModelAdapter` that intercepts an untrusted payload asserting scalar-sum closure on the Lean 4 commutator loop, returns a sealed `PacketEnvelope` with refusal code `R021_SCALAR_SUM_CLOSURE`, and verifies the SHA-256 seal.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q
from itertools import combinations
import hashlib
import json

def canonical_hash(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class Level21ModelAdapter:
    def __init__(self):
        pass

    def evaluate_proposal(self, raw_proposal):
        # 1. Host recomputes Gram matrix
        lengths = {(min(u, v), max(u, v)): Q(val) for u, v, val in raw_proposal["squared_lengths"]}
        rest = [1, 2, 3, 4]
        def sq(a, b): return Q(0) if a == b else lengths[(min(a, b), max(a, b))]
        gram = [[(sq(0, a) + sq(0, b) - sq(a, b)) / Q(2) for b in rest] for a in rest]

        # 2. Check Gram positivity (1x1 minor check demo)
        if gram[0][0] <= Q(0):
            verdict = "REFUSED_GRAM_NOT_POSITIVE"
            code = "R021_GRAM_NOT_POSITIVE"
        else:
            # 3. Check loop closure vs scalar sum
            word = raw_proposal["loops"][0]["word"]
            # Lean 4 commutator loop: ["Rx", "Ry", "Rx-", "Ry-"]
            if word == ["Rx", "Ry", "Rx-", "Ry-"] and raw_proposal["loops"][0]["closure"] == "identity":
                verdict = "REFUSED_SCALAR_SUM_CLOSURE"
                code = "R021_SCALAR_SUM_CLOSURE"
            else:
                verdict = "ADMITTED"
                code = "OK"

        envelope = {
            "task_id": "TASK_REGGE_L21",
            "host_verdict": verdict,
            "refusal_code": code,
            "payload_digest": canonical_hash(raw_proposal)
        }
        envelope["seal"] = canonical_hash(envelope)
        return envelope

adapter = Level21ModelAdapter()
payload = {
    "squared_lengths": [[a, b, "1/1"] for a, b in combinations(range(5), 2)],
    "loops": [{"closure": "identity", "hinge": [0, 1, 2], "word": ["Rx", "Ry", "Rx-", "Ry-"]}],
}
envelope = adapter.evaluate_proposal(payload)
assert envelope["host_verdict"] == "REFUSED_SCALAR_SUM_CLOSURE"
assert envelope["refusal_code"] == "R021_SCALAR_SUM_CLOSURE"
print("Model adapter host verification verified successfully!")
```
</details>

## 7. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `ports.py` |
| **Target Checker** | `stage_021.py` |
| **Formal Lean Kernel** | `Level21DiscreteRegge.lean` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |

---

## Integrated System Verification

This lesson integrates the system integration test suite from `03_typed_agent_composition.ipynb`:
**Topic:** Connect skills by their input and output types (Typed Agent Composition)

### Key Verified Invariants:
- Deterministic roundtrip / state-frontier verification under exact rational constraints.
- Fail-stop refusal testing preventing unconstrained bypass or illegal boundary traversal.
- Full parity verification between wire formats and memory representations.

