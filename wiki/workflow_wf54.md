# WF54: Five-seam mechanism showcase

**Status:** runnable offline. The open-weight seam needs `torch`; there is no live campaign.

**Folder:** [`workflows/wf54_five_seam_mechanism_showcase/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf54_five_seam_mechanism_showcase)

**What it is for:** showing the five places a host can intervene in a model call, and what each can and cannot certify:

1. Sampling: temperature, seed and sample count. Majority vote can pick a frequent wrong answer; certificate-first picks only a checked draw or refuses.
2. Logits and grammar: a token grammar removes format errors, but an on-grammar wrong answer still needs the host check.
3. Scratchpad: a host-held working memory with a stationary-loop detector.
4. Attention and residual stream: head masking, patching and steering, each paired with a null control.
5. Weights: training pairs taken only from receipts the host certified, with hold-out and lineage guards.

**Run it offline:**

```powershell
python workflows/wf54_five_seam_mechanism_showcase/run_five_seam_showcase.py
python -m pytest pfp_core/tests/test_llm_mechanisms.py workflows/wf54_five_seam_mechanism_showcase/tests -q
```

Builds on [WF12](workflow_wf12.md), [WF24](workflow_wf24.md) and [WF27](workflow_wf27.md). Formerly `benchmarks/llm_mechanisms/`.
