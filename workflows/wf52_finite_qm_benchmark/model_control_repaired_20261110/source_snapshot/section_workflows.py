"""Exploratory allocation across the public task's five numbered parts.

Five independent solver contexts receive the same unchanged seed. Output caps
sum to 16000 tokens; repeated input, reasoning usage, elapsed time and money
still require the runtime's aggregate accounting. No provider is called here.
Raw assembly is not a mathematical consistency check or certified PFP/EIS step.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PLAN_ID = "section_allocated_v1"
OUTPUT_TOKENS_PER_PART = 3200
PART_NUMBERS = (1, 2, 3, 4, 5)
STAGE_IDS = tuple(f"part_{part}" for part in PART_NUMBERS)
SOURCE_FILES = (
    "section_workflows.py", "reference_runner.py", "budget_ledger.py",
    "campaign_ledger.py", "openrouter_provider.py", "live_campaign.py",
)

# These descriptions copy only the numbered requests in the public seed.
PUBLIC_PARTS = (
    "The full spectrum and spectral projectors of H, including degeneracies and the limit J=Delta=0.",
    "The exact state at time t and the transition probability P_01_to_10(t). Determine its supremum over "
    "t>=0 and the earliest time attaining it, including the constant-probability case.",
    "The reduced density matrix of the first spin, its von Neumann entropy in bits, the pure-state concurrence, "
    "and the maximal CHSH expectation over local dichotomic projective spin measurements. Determine exactly "
    "when a maximally entangled state is reachable and the earliest time reaching one.",
    "For inverse temperature beta>=0, the Gibbs density matrix exp(-beta H)/Z_beta, its partition function, "
    "all four eigenvalues of its partial transpose with respect to the second spin, and a necessary and "
    "sufficient condition for thermal entanglement. Explain the beta=0 and J=Delta=0 limits.",
    "Provide independent consistency checks (normalization, initial conditions, the decoupled limit, and "
    "one nontrivial numerical example). Distinguish algebraic identities from numerical checks. Do not "
    "assume a formula remains defined when its denominator vanishes.",
)


def _instruction(part_number: int, public_request: str) -> str:
    return (
        f"Answer ONLY numbered part {part_number} of the unchanged complete task in the user message. "
        f"That public part requests: {public_request} "
        "Derive any prerequisites you need directly from the stated Hamiltonian and assumptions within "
        "this answer; do not rely on another section or an earlier response. Keep the original basis, "
        "parameter meanings and conventions. Give the requested results, essential derivations and "
        "exceptional cases within 3200 output tokens. Use concise ordinary mathematical text, not JSON. "
        "Do not repeat the question or expand unrelated parts. State unresolved issues explicitly. "
        "This is an independent section: it will be concatenated with other independently produced sections "
        "without a consistency review or editorial merge."
    )


SECTION_PLANS = {
    PLAN_ID: {
        "version": "1.0",
        "source_idea": "exploratory_public_task_output_allocation",
        "stages": [
            {
                "id": stage_id,
                "instruction": _instruction(part, request),
                "max_output_tokens": OUTPUT_TOKENS_PER_PART,
                "visible_artifacts": [],
            }
            for stage_id, part, request in zip(STAGE_IDS, PART_NUMBERS, PUBLIC_PARTS, strict=True)
        ],
        "part_by_stage": dict(zip(STAGE_IDS, PART_NUMBERS, strict=True)),
        "allocation": {"solver_calls": 5, "output_tokens_per_call": 3200, "sum_output_token_caps": 16000},
        "input_policy": {
            "seed": "Exact unchanged UTF8 seed as a separate user message in every call.",
            "previous_answers": False,
            "checker_feedback": False,
            "evaluator_context": False,
            "tools": [],
        },
        "assembly": {
            "function": "section_workflows.assemble_sections",
            "kind": "ordered_raw_sections",
            "order": list(STAGE_IDS),
            "llm_merge": False,
            "consistency_certified": False,
            "missing_output": "Retain an explicit missing/unavailable slot; never silently drop a part.",
            "truncation": "Preserve raw text; runtime retains provider finish reasons separately.",
        },
        "source_pins": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in SOURCE_FILES
        },
        "execution": "Independent contexts; runtime owns dispatch, one aggregate budget ledger and stopping rules.",
        "scope": "Exploratory output allocation/decomposition control, not certified PFP/EIS integration. "
                 "Delivery of all five sections does not certify completeness, correctness or consistency.",
    }
}


def section_messages(stage_id: str, seed_bytes: bytes) -> list[dict[str, str]]:
    """Build an isolated context; there is no prior-answer/artifact input channel."""
    if stage_id not in STAGE_IDS:
        raise ValueError("unknown section stage")
    if type(seed_bytes) is not bytes:
        raise TypeError("seed_bytes must contain the unchanged UTF8 bytes")
    seed_text = seed_bytes.decode("utf8", errors="strict")
    stage = SECTION_PLANS[PLAN_ID]["stages"][STAGE_IDS.index(stage_id)]
    return [{"role": "system", "content": stage["instruction"]}, {"role": "user", "content": seed_text}]


def assemble_sections(responses: Mapping[str, str | None]) -> dict[str, Any]:
    """Frame and concatenate raw sections in public part order, without synthesis.

    Missing keys and explicit None are distinguished from returned empty text.
    Character spans locate the original unmodified text; SHA256 binds its UTF8
    bytes. Incomplete or contradictory prose is retained without an inferred
    verdict. With no nonempty raw text, answer_text and its hash are None; framing
    and placeholders never count as delivered output. Character spans are then
    None as well. The caller must keep transport and finish-reason metadata.
    """
    if not isinstance(responses, Mapping):
        raise TypeError("responses must map section stage IDs to text or None")
    if set(responses) - set(STAGE_IDS):
        raise ValueError("responses contains an unknown section stage")
    chunks = [
        "Independent section assembly. The following sections are raw solver outputs in public task order. "
        "No cross-section consistency, completeness or correctness certificate is implied.\n\n"
    ]
    records = []
    offset = len(chunks[0])
    for part, stage_id in zip(PART_NUMBERS, STAGE_IDS, strict=True):
        text = responses.get(stage_id)
        if text is not None and type(text) is not str:
            raise TypeError("section output must be text or None")
        header = f"## Part {part} — independent raw section\n\n"
        chunks.append(header)
        offset += len(header)
        status = "missing" if stage_id not in responses else "unavailable" if text is None else "returned"
        body = text if text is not None else f"[No section text: {status}.]"
        raw_span = [offset, offset + len(text)] if text is not None else None
        digest = hashlib.sha256(text.encode("utf8")).hexdigest() if text is not None else None
        chunks.extend([body, "\n\n"])
        offset += len(body) + 2
        records.append({"stage_id": stage_id, "part_number": part, "status": status,
                        "raw_text_sha256": digest, "raw_text_character_span": raw_span,
                        "empty_text": text == "" if text is not None else False})
    has_nonempty_text = any(r["status"] == "returned" and not r["empty_text"] for r in records)
    answer = "".join(chunks) if has_nonempty_text else None
    if answer is None:
        for record in records:
            record["raw_text_character_span"] = None
    return {
        "schema_version": "1.0", "plan": PLAN_ID, "assembly_kind": "ordered_raw_sections",
        "answer_text": answer,
        "answer_sha256": hashlib.sha256(answer.encode("utf8")).hexdigest() if answer is not None else None,
        "sections": records,
        "missing_stage_ids": [r["stage_id"] for r in records if r["status"] != "returned"],
        "empty_stage_ids": [r["stage_id"] for r in records if r["empty_text"]],
        "all_sections_present": all(r["status"] == "returned" for r in records),
        "all_sections_nonempty": all(r["status"] == "returned" and not r["empty_text"] for r in records),
        "llm_merge": False, "consistency_certified": False, "mathematical_correctness_assessed": False,
        "scope": SECTION_PLANS[PLAN_ID]["scope"],
    }
