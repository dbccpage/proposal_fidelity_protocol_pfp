# Lesson 100.12 — RFC 8785 Canonical JSON

## How to use this lesson

AuthorityEffect: None.

Read this page, then try one finite byte example. The retained lesson title names
the standard topic; it is not a certification of the repository's serializers.

Open [the companion notebook](../notebooks/lesson_100_12_rfc_8785_canonical_json.ipynb)
from a repository-root Python environment with the local packages available.
Run its four code cells in order. A passing example is not a learner assessment,
a general proof or a production packet verification.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea
- 2. Scope & Claim Boundary
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Student Exercise
- 5. Anchors

> **Claim-typing legend**
> - **[Pinned]**: an explicitly identified immutable source or contract; none is newly admitted here.
> - **[Proved]**: here, only deterministic finite Python checks when actually run, not a general theorem.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea

**[Declared] Core concept:** An explicitly selected encoder determines the bytes
that are compared or hashed. Key sorting alone does not identify a wire standard.

This lesson calls `omega_engine_pfp.domain.prompts.packets.canonical_json_bytes`.
Its implementation uses Python `json.dumps` with sorted keys, compact separators
and `ensure_ascii=False`, then UTF-8 encoding. It is not the tagged production
packet sealer. Passing this lesson does not establish that these formats agree.

For the worked example, both `{"b": 2, "a": 1}` and `{"a": 1, "b": 2}`
produce the literal bytes `b'{"a":1,"b":2}'` under this selected function.
Compact layout does not remove spaces inside strings: `"two words"` keeps its space.

### The Four-Tier Perspective
- **Tangible:** Put the same two labeled cards in a fixed order.
- **Algorithmic (Age 11–17):** Predict the bytes before running the worked example.
- **Discrete Math (Undergrad):** Distinguish equality of values from equality of bytes.
- **Foundational (Age 50–500):** Ask which input domain and encoder the claim covers.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact bytes for the shown finite dictionary fixtures. | Full standards conformance or universal cross-language parity. |
| Reordered keys agree and a changed integer differs in these examples. | Authentication, hash collision resistance or production packet admission. |

**[Open] Format boundary:** This function retains Python's default number behavior;
the notebook demonstrates that it emits `NaN`. It has no zero-float validation
policy. An unsupported Python object raises `TypeError`, but that one refusal is
not a strict JSON-ingress or complete input-validation certificate.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Under the selected function, will reordering the two worked-example
keys change the encoded bytes? Commit `prediction = "same_bytes"` or
`prediction = "different_bytes"` before evaluating the comparison cell.

The supplied prediction is an author-filled worked example, not a recorded learner
answer. A wrong prediction must fail the assertion. Explain afterward why a changed
value is a different question from reordered keys.

## 4. Student Exercise

**Task:** Complete this comparison with a different insertion order but the same
two key/value pairs. Then change `a` to `3` and check that the bytes differ.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from omega_engine_pfp.domain.prompts.packets import canonical_json_bytes

first = {"b": 2, "a": 1}
second = {"a": 1, "b": 2}
assert canonical_json_bytes(first) == canonical_json_bytes(second)
assert canonical_json_bytes({"a": 3, "b": 2}) != canonical_json_bytes(first)
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `RFC 8785` |
| **Authority Effect** | `None` |
| **Encoding owner** | `omega_engine_pfp.domain.prompts.packets.canonical_json_bytes` |
| **Number policy** | Python defaults; no zero-float enforcement is claimed. |

**[Open] Next check:** Independently test the specific encoder and declared input
domain needed by a real consumer. This lesson records no native, Jupyter-kernel,
video-recording or human-learning result.
