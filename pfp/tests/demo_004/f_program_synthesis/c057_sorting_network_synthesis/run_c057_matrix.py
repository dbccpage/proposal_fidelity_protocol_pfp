"""Model matrix for C057: Sorting Network Synthesis.

Sends ten sorting-network cases to each declared model and scores the replies
with both judge checkers. This script makes live provider calls; run it only
with an explicit authorization of provider, budget and data handling, and
with ``--output-dir`` naming a new directory. Shared behaviour (explicit
configuration, opaque case tokens, full raw responses, INFRA_ERROR and
CHECKER_DEFECT outcomes) lives in ``omega_engine_pfp/infrastructure/synthesis_matrix.py``.

Run from the repository root as a module, for example
``py -3.12 -m omega_engine_pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.run_c057_matrix --output-dir <new directory> --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-provider-calls 1 --max-estimated-cost-microusd 10000 --max-output-tokens 2048``.

Correction, 2026-09-29: the earlier prompt gave the optimal n = 4 network as
its worked example, stated the proven bounds used by the infeasible cases
(k < 25 for n = 9, k < 29 for n = 10), sent descriptive case IDs, and read a
``.env`` file.
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir() and (p / "omega_engine_woland").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet.exact_checker import (
    check,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from omega_engine_pfp.infrastructure.synthesis_matrix import (
    MatrixSpec,
    main,
)

MODELS = [
    {"id": "stealth/space-bunny-alpha", "name": "Space Bunny Alpha (undisclosed stealth model)"},
    {"id": "meta-llama/llama-3.3-70b-instruct", "name": "LLaMA 3.3 70B Instruct"},
    {"id": "meta-llama/llama-3.1-8b-instruct", "name": "LLaMA 3.1 8B Instruct"},
]

SYSTEM_PROMPT = """You are taking part in Challenge C057: Sorting Network Synthesis.

A case has these fields:
- "n": integer channel count, 4 <= n <= 12
- "k": integer comparator bound, k >= 0
- "prefix": list of mandatory comparators [i, j] with 0 <= i < j < n that must open the network, in order
- "forbidden": list of comparators [i, j] with 0 <= i < j < n that must not appear in the network

Reply with one JSON object and nothing else, in one of three forms.

1. SOLVED, when you give a sorting network of length <= k:
{"case_id": "<the case_id you were given>", "status": "SOLVED", "network": [[i1, j1], [i2, j2], ...]}
Requirements: len(network) <= k; every comparator is [i, j] with 0 <= i < j < n; the network starts
with the prefix; no comparator is forbidden; the network sorts all 2^n binary inputs (0-1 principle).

2. UNKNOWN, only when no admissible network exists and you can name the proof:
{"case_id": "<the case_id you were given>", "status": "UNKNOWN", "code": "<proof code>"}
The proof code must be one of these, and its condition must hold on the case:
- BOUND_BELOW_PREFIX_LENGTH: k is smaller than the number of prefix comparators;
- BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND: k is below the information-theoretic lower bound for sorting n items;
- BOUND_BELOW_PROVEN_OPTIMAL_SIZE: k is below the proven minimum number of comparators for n channels;
- FORBIDDEN_ADJACENT_COMPARATOR: a comparator [i, i+1] is forbidden.
UNKNOWN with any other code, or on a case where an admissible network exists, is scored as a failure.

3. OUT_OF_SCOPE, when the input violates the preconditions above:
{"case_id": "<the case_id you were given>", "status": "OUT_OF_SCOPE", "witness": {"reason": "<REASON>"}}"""

INSTRUCTION = "Case input:"

TEST_CASES = [
    # 1. n=4 unconstrained, optimal k=5
    {
        "case_id": "c057_m01_n4_unconstrained",
        "n": 4,
        "k": 5,
        "prefix": [],
        "forbidden": [],
    },
    # 2. n=4 constrained: prefix [[0, 3]], forbidden [[0, 2]], k=5
    {
        "case_id": "c057_m02_n4_constrained",
        "n": 4,
        "k": 5,
        "prefix": [[0, 3]],
        "forbidden": [[0, 2]],
    },
    # 3. n=5 unconstrained, optimal k=9
    {
        "case_id": "c057_m03_n5_unconstrained",
        "n": 5,
        "k": 9,
        "prefix": [],
        "forbidden": [],
    },
    # 4. n=5 constrained: prefix [[0, 1], [2, 3]], forbidden [[0, 4]], k=10
    {
        "case_id": "c057_m04_n5_constrained",
        "n": 5,
        "k": 10,
        "prefix": [[0, 1], [2, 3]],
        "forbidden": [[0, 4]],
    },
    # 5. n=6 unconstrained, optimal k=12
    {
        "case_id": "c057_m05_n6_unconstrained",
        "n": 6,
        "k": 12,
        "prefix": [],
        "forbidden": [],
    },
    # 6. n=6 constrained: prefix [[0, 5], [1, 3], [2, 4]], k=12
    {
        "case_id": "c057_m06_n6_constrained",
        "n": 6,
        "k": 12,
        "prefix": [[0, 5], [1, 3], [2, 4]],
        "forbidden": [],
    },
    # 7. n=8 unconstrained, optimal k=19
    {
        "case_id": "c057_m07_n8_unconstrained",
        "n": 8,
        "k": 19,
        "prefix": [],
        "forbidden": [],
    },
    # 8. n=4 infeasible bound: k=4 < ceil(log2(4!))=5 -> UNKNOWN
    {
        "case_id": "c057_m08_infeasible_n4_k4",
        "n": 4,
        "k": 4,
        "prefix": [],
        "forbidden": [],
    },
    # 9. n=9 infeasible bound: k=24 < proven optimal 25 -> UNKNOWN
    {
        "case_id": "c057_m09_infeasible_n9_k24",
        "n": 9,
        "k": 24,
        "prefix": [],
        "forbidden": [],
    },
    # 10. Out of scope: reversed prefix comparator [3, 0] -> OUT_OF_SCOPE
    {
        "case_id": "c057_m10_poison_reversed_prefix",
        "n": 4,
        "k": 5,
        "prefix": [[3, 0]],
        "forbidden": [],
    },
]


SPEC = MatrixSpec(
    challenge="C057",
    system_prompt=SYSTEM_PROMPT,
    instruction=INSTRUCTION,
    cases=TEST_CASES,
    checkers=(("exact", check), ("independent", independent_check)),
    models=MODELS,
    max_tokens=8192,
)


if __name__ == "__main__":
    sys.exit(main(SPEC))
