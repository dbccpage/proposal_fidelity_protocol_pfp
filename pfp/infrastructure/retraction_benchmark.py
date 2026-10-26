"""Current PFP route for Paper 008's original six finite graph tasks.

Original graph data, exact certificate helpers, prompts and verdict parser are
copied unchanged from the sealed source. Hinted prompts contain host answers;
offline stubs and exact-oracle controls are not model evidence. AuthorityEffect: None.
"""
from __future__ import annotations

import base64
import hashlib
import json
import stat
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from uuid import uuid4

from omega_engine_pfp.infrastructure.pilot_matrix import (
    _scope,
    complete_pilot_turn,
    make_pilot_gateways,
    validate_pilot_gateways,
)
from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1, Provider
from omega_engine_woland.infrastructure.providers.openai_compat import (
    build_openai_compat_body,
    parse_openai_compat_response,
)

CONDITIONS = ("baseline", "hinted", "scratchpad", "exact_oracle")
DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"
SYSTEM = "Answer with VERDICT: CONSISTENT or VERDICT: CONTRADICTION, then a short reason."
ANSWER_SCHEMA = {"anyOf": [{"type": "object"}, {"type": "array"},
                           {"type": "string", "minLength": 1}]}
SCHEMA = "pfp008.graph-consistency-receipt.v3"
SUMMARY_SCHEMA = "pfp008.graph-consistency-summary.v3"
HISTORICAL_SOURCE_SHA256 = 'b11a59a64f6d0bd3d8c80b6ea46cc6466ff5967cd31f851e4d77de17497103bb'


def compute_opcode_base(level: int) -> int:
    """Reserved opcode base for stage N >= 22: base(N) = 128 + 8 * (N - 22); 0 below 22."""
    if level < 22:
        return 0
    return 128 + 8 * (level - 22)


@dataclass(frozen=True)
class GraphInstance:
    """A directed graph potential-consistency task."""

    task_id: str
    vertices: list[str]
    edges: list[tuple[str, str, int]]  # (u, v, claimed difference pi(v) - pi(u))
    expected_verdict: str  # "CONSISTENT" or "CONTRADICTION"
    description: str


BENCHMARK_INSTANCES: list[GraphInstance] = [
    GraphInstance(
        task_id="retract_01_tree_clean",
        vertices=["A", "B", "C"],
        edges=[("A", "B", 2), ("B", "C", 3)],
        expected_verdict="CONSISTENT",
        description="Spanning tree with potential pi(A)=0, pi(B)=2, pi(C)=5",
    ),
    GraphInstance(
        task_id="retract_02_triangle_clean",
        vertices=["A", "B", "C"],
        edges=[("A", "B", 2), ("B", "C", 3), ("A", "C", 5)],
        expected_verdict="CONSISTENT",
        description="Triangle whose claims sum to zero around the cycle: 2 + 3 - 5 = 0",
    ),
    GraphInstance(
        task_id="retract_03_triangle_poisoned",
        vertices=["A", "B", "C"],
        edges=[("A", "B", 2), ("B", "C", 3), ("A", "C", 6)],
        expected_verdict="CONTRADICTION",
        description="Triangle with cycle sum 2 + 3 - 6 = -1",
    ),
    GraphInstance(
        task_id="retract_04_diamond_clean",
        vertices=["A", "B", "C", "D"],
        edges=[("A", "B", 1), ("B", "D", 4), ("A", "C", 2), ("C", "D", 3)],
        expected_verdict="CONSISTENT",
        description="Diamond: path ABD = 1 + 4 = 5 and path ACD = 2 + 3 = 5",
    ),
    GraphInstance(
        task_id="retract_05_diamond_entangled_poisoned",
        vertices=["A", "B", "C", "D"],
        edges=[("A", "B", 1), ("B", "D", 4), ("A", "C", 2), ("C", "D", 4)],
        expected_verdict="CONTRADICTION",
        description="Diamond: path ABD = 5 but path ACD = 6",
    ),
    GraphInstance(
        task_id="retract_06_k4_rank3_poisoned",
        vertices=["A", "B", "C", "D"],
        edges=[
            ("A", "B", 1),
            ("B", "C", 2),
            ("C", "A", -3),
            ("B", "D", 3),
            ("D", "C", -2),
            ("A", "D", 4),
        ],
        expected_verdict="CONTRADICTION",
        description="K4 (cycle rank 3) whose cycle B->D->C->B sums to 3 - 2 - 2 = -1",
    ),
]


def exact_host_evaluate(instance: GraphInstance) -> tuple[str, dict[str, int], int, list[str]]:
    """Decide consistency exactly by breadth-first spanning-tree propagation.

    Returns (verdict, potentials, residual_sum, residual_edges). ``residual_sum``
    is the sum over edges of |pi(v) - pi(u) - claim| for the tree potential. It
    is zero exactly when the claims are consistent; it is not the minimal L1
    repair distance. Every vertex must be reachable from the first vertex.
    """
    adjacency: dict[str, list[tuple[str, int]]] = {v: [] for v in instance.vertices}
    for u, v, diff in instance.edges:
        adjacency[u].append((v, diff))
        adjacency[v].append((u, -diff))

    root = instance.vertices[0]
    potentials: dict[str, int] = {root: 0}
    queue = [root]
    while queue:
        current = queue.pop(0)
        for neighbor, diff in adjacency[current]:
            if neighbor not in potentials:
                potentials[neighbor] = potentials[current] + diff
                queue.append(neighbor)
    missing = [v for v in instance.vertices if v not in potentials]
    if missing:
        raise ValueError(f"{instance.task_id}: vertices unreachable from {root}: {missing}")

    residual_sum = 0
    residual_edges: list[str] = []
    for u, v, diff in instance.edges:
        actual = potentials[v] - potentials[u]
        residual = abs(actual - diff)
        if residual:
            residual_sum += residual
            residual_edges.append(f"edge({u}->{v}, claimed={diff}, actual={actual}, gap={residual})")

    verdict = "CONSISTENT" if residual_sum == 0 else "CONTRADICTION"
    return verdict, potentials, residual_sum, residual_edges


def _tree_parents(instance: GraphInstance) -> dict[str, tuple[str, int, int] | None]:
    """Breadth-first tree from the first vertex: vertex -> (parent, edge index, orientation)."""
    adjacency: dict[str, list[tuple[str, int, int]]] = {v: [] for v in instance.vertices}
    for index, (u, v, _) in enumerate(instance.edges):
        adjacency[u].append((v, index, 1))
        adjacency[v].append((u, index, -1))
    root = instance.vertices[0]
    parents: dict[str, tuple[str, int, int] | None] = {root: None}
    queue = [root]
    while queue:
        current = queue.pop(0)
        for neighbor, index, orientation in adjacency[current]:
            if neighbor not in parents:
                parents[neighbor] = (current, index, orientation)
                queue.append(neighbor)
    return parents


def _root_path(parents: dict[str, tuple[str, int, int] | None], vertex: str) -> list[tuple[int, int]]:
    """Tree steps (edge index, orientation) leading from the root to ``vertex``."""
    steps: list[tuple[int, int]] = []
    link = parents[vertex]
    while link is not None:
        parent, index, orientation = link
        steps.append((index, orientation))
        link = parents[parent]
    return list(reversed(steps))


def inconsistency_witness(instance: GraphInstance) -> list[tuple[int, int]] | None:
    """Dual witness for CONTRADICTION: a closed walk with a nonzero signed claim sum.

    A step (i, +1) traverses edge i forward and adds its claim; (i, -1) traverses it
    backward and subtracts it. For every potential pi the signed sum of
    pi(v) - pi(u) around a closed walk is zero, so a closed walk whose signed claim
    sum is nonzero rules out every potential. Conversely, when no potential exists
    some tree-plus-chord cycle has a nonzero sum; this function returns that walk, or
    None when the claims are consistent.
    """
    _, potentials, _, _ = exact_host_evaluate(instance)
    parents = _tree_parents(instance)
    for index, (u, v, claim) in enumerate(instance.edges):
        if potentials[v] - potentials[u] != claim:
            back = [(i, -orientation) for i, orientation in reversed(_root_path(parents, v))]
            return _root_path(parents, u) + [(index, 1)] + back
    return None


def verify_inconsistency_witness(instance: GraphInstance, steps: object) -> bool:
    """Check that ``steps`` is a closed walk over declared edges with a nonzero signed claim sum."""
    if not isinstance(steps, list) or not steps:
        return False
    position: str | None = None
    start: str | None = None
    total = 0
    for step in steps:
        if not (isinstance(step, (tuple, list)) and len(step) == 2):
            return False
        index, orientation = step
        if type(index) is not int or type(orientation) is not int or orientation not in (1, -1):
            return False
        if not 0 <= index < len(instance.edges):
            return False
        u, v, claim = instance.edges[index]
        tail, head = (u, v) if orientation == 1 else (v, u)
        if position is None:
            start = tail
        elif position != tail:
            return False
        position = head
        total += orientation * claim
    return position == start and total != 0


def verify_potential(instance: GraphInstance, potentials: object) -> bool:
    """Check that ``potentials`` assigns an integer to every vertex and satisfies every edge."""
    if not isinstance(potentials, dict) or set(potentials) != set(instance.vertices):
        return False
    if any(type(value) is not int for value in potentials.values()):
        return False
    return all(potentials[v] - potentials[u] == claim for u, v, claim in instance.edges)


def host_certificate(instance: GraphInstance) -> dict[str, object]:
    """The host verdict with its checkable certificate: a potential, or a dual witness walk."""
    verdict, potentials, _, _ = exact_host_evaluate(instance)
    if verdict == "CONSISTENT":
        if not verify_potential(instance, potentials):
            raise AssertionError(f"{instance.task_id}: host potential failed its own check")
        return {"verdict": verdict, "potential": dict(potentials)}
    walk = inconsistency_witness(instance)
    if walk is None or not verify_inconsistency_witness(instance, walk):
        raise AssertionError(f"{instance.task_id}: no valid dual witness for CONTRADICTION")
    signed_sum = sum(orientation * instance.edges[index][2] for index, orientation in walk)
    return {"verdict": verdict, "dual_witness_walk": [list(step) for step in walk], "signed_claim_sum": signed_sum}


def detect_stationary_loops(proposals: list[str], threshold: int = 3) -> tuple[bool, int]:
    """Return whether the longest consecutive repeat count reaches ``threshold``.

    Four identical proposals have three consecutive repeats. Separate runs
    do not add to the count.

    This helper is for multi-turn traces. The single-shot runner below never
    produces more than one proposal per instance, so it records no loop count.
    """
    if type(threshold) is not int or threshold < 1:
        raise ValueError("repeat threshold must be a positive integer")
    current = longest = 0
    for previous, proposal in zip(proposals, proposals[1:]):
        current = current + 1 if proposal.strip() == previous.strip() else 0
        longest = max(longest, current)
    return longest >= threshold, longest


def receipt_digest(receipt: ExecutionReceipt | dict[str, object]) -> str:
    """Bind every recorded field except the digest itself, including the raw reply.

    This unkeyed content hash does not authenticate a provider or author.
    A JSON-loaded receipt can be checked with the same function.
    """
    payload = asdict(receipt) if isinstance(receipt, ExecutionReceipt) else dict(receipt)
    payload.pop("digest_sha256", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def format_prompt(instance: GraphInstance, condition: str) -> str:
    """Render the prompt for one instance under one condition."""
    relations = ", ".join(f"{u}->{v} difference is {d}" for u, v, d in instance.edges)
    base = (
        "Analyze this directed graph potential problem:\n"
        f"Vertices: {instance.vertices}\n"
        f"Relations: {relations}\n"
        "Determine whether there exists an integer potential pi: V -> Z with "
        "pi(v) - pi(u) = difference for every edge.\n"
    )
    if condition == "baseline":
        return base + "Output 'VERDICT: CONSISTENT' or 'VERDICT: CONTRADICTION' with brief reasoning."
    if condition == "hinted":
        _, _, residual_sum, residual_edges = exact_host_evaluate(instance)
        hint = (
            "\n[HOST RESIDUALS]\n"
            f"Sum of edge residuals under a spanning-tree potential = {residual_sum}.\n"
            f"Edges with nonzero residual: {residual_edges if residual_edges else 'none'}.\n"
        )
        return base + hint + "Use the host residuals. Output 'VERDICT: CONSISTENT' or 'VERDICT: CONTRADICTION'."
    if condition == "scratchpad":
        steps = (
            "\n[SCRATCHPAD]\n"
            f"Step 1: Set pi({instance.vertices[0]}) = 0.\n"
            "Step 2: Propagate potentials along spanning-tree edges.\n"
            "Step 3: For every remaining edge compute gap = |pi(v) - pi(u) - difference|.\n"
            "Step 4: Answer VERDICT: CONSISTENT if every gap is 0, else VERDICT: CONTRADICTION.\n"
        )
        return base + steps
    if condition == "exact_oracle":
        return "ORACLE_INTERNAL"
    raise ValueError(f"Unknown condition: {condition}")


def parse_verdict(response: str) -> str:
    """Read exact verdict labels; refuse malformed or conflicting explicit labels."""
    labels: list[str] = []
    for line in response.splitlines():
        cleaned = line.strip().upper()
        if cleaned.startswith("VERDICT:"):
            label = cleaned.removeprefix("VERDICT:").strip()
            if label not in ("CONSISTENT", "CONTRADICTION"):
                return "UNKNOWN"
            labels.append(label)
    if labels:
        return labels[0] if len(set(labels)) == 1 else "UNKNOWN"
    bare = response.strip().upper()
    return bare if bare in ("CONSISTENT", "CONTRADICTION") else "UNKNOWN"


@dataclass(frozen=True)
class ExecutionReceipt:
    schema: str
    task_id: str
    condition: str
    model: str
    provider: str
    verdict_emitted: str
    host_verdict: str
    expected_verdict: str
    matched_ground_truth: bool
    tokens: int | None
    cost_usd: float | None
    latency_sec: float
    digest_sha256: str
    raw_content: str
    host_certificate: dict[str, object]
    instance: dict[str, object]
    prompt: str
    source_sha256: str
    status: str = "REFUSED"
    evidence_grade: str = "UNVERIFIED"
    attempt_id: str | None = None
    provider_attempted: bool = False
    turn: dict | None = None


class OfflineStubClient:
    """Original deterministic prompt-reading rule; no model or provider budget."""

    provider = "offline-stub"

    def complete(self, prompt: str, max_tokens: int = 128) -> tuple[str, int, float, float]:
        content = ("VERDICT: CONTRADICTION\nThe host reports a nonzero residual."
                   if "gap=" in prompt else "VERDICT: CONSISTENT")
        return content, len(prompt) // 4 + 8, 0.0, 0.0


def _pins():
    from omega_engine_pfp.domain import pfp_ingress
    from omega_engine_pfp.infrastructure import pilot_matrix, task_turn
    from omega_engine_pfp.use_cases import pfp_prompt, pfp_proposal
    from omega_engine_woland.infrastructure.providers import openai_compat

    modules = (pilot_matrix, task_turn, pfp_prompt, pfp_proposal, pfp_ingress, openai_compat)
    return {"runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **{module.__name__: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
           for module in modules}}


def _request(prompt):
    return CandidateRequest(SYSTEM, prompt, decoding=DecodingParamsV1(
        temperature=0.0, allow_fallbacks=False, require_parameters=True))


def _selected(conditions, task_ids):
    conditions = tuple(conditions)
    if (not conditions or len(conditions) > 4 or len(set(conditions)) != len(conditions)
            or any(condition not in CONDITIONS for condition in conditions)):
        raise ValueError("INVALID_CONDITIONS")
    by_id = {item.task_id: item for item in BENCHMARK_INSTANCES}
    ids = tuple(by_id) if task_ids is None else tuple(task_ids)
    if not ids or len(set(ids)) != len(ids) or any(task_id not in by_id for task_id in ids):
        raise ValueError("INVALID_TASK_SELECTION")
    return [(condition, by_id[task_id]) for condition in conditions for task_id in ids]


def _new_output(output_dir):
    if output_dir is None:
        return None
    output = Path(output_dir).absolute()
    for path in (output, *output.parents):
        try:
            attributes = path.lstat()
        except FileNotFoundError:
            attributes = None
        if (attributes is not None and (stat.S_ISLNK(attributes.st_mode)
                or getattr(attributes, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
                or path.name.rstrip(" .") != path.name):
            raise ValueError("OUTPUT_ALIAS_REFUSED")
    historical = Path(__file__).resolve().parents[2] / (
        "omega_engine_education/documentation/004_oepfp/papers/omega_engine_symbol_game/"
        "008_pfp_mssn_tower_challenges_and_retraction_benchmarks")
    if output.resolve().is_relative_to(historical):
        raise ValueError("HISTORICAL_OUTPUT_REFUSED")
    if output.exists():
        raise ValueError("OUTPUT_DIR_EXISTS")
    return output


def _grade(condition, provider):
    if provider == "host":
        return "EXACT_ORACLE_CONTROL_NO_MODEL"
    if provider == "offline-stub":
        return "DETERMINISTIC_STUB_NO_MODEL"
    return "ASSISTED_ANSWER_BEARING_MODEL" if condition == "hinted" else "BOUND_MODEL_ORIGINAL_JUDGE"


def _known_no_dispatch(turn):
    """Only retained pre-send refusals establish zero additional provider cost."""
    if (turn["provider_wire"] is not None or turn["raw_body"] is not None
            or turn["usage"] or turn["pfp"] is not None or turn["attempt_state"] is not None
            or turn["ok"] or not turn["stop"]):
        return False
    claim = turn["action_record"]
    if claim is None:
        return turn["error"] in {
            "CALL_ALLOWANCE_EXHAUSTED", "RUN_RECONCILIATION_REQUIRED", "UNRECONCILED_ATTEMPT",
            "ESTIMATED_BUDGET_EXCEEDED", "FUZZY_BUDGET_MILESTONE_REACHED"}
    return (claim.get("state") == "refused_before_dispatch"
        and bool(turn["error"]) and claim.get("failure_code") == turn["error"]
        and not any(claim.get(key) for key in (
            "provider_attempt_id", "wire_file", "wire_sha256", "wire_bytes", "generation_id",
            "actual", "charged", "reported_cost_usd")))


def run_benchmark(condition="hinted", model=DEFAULT_MODEL, client=None, **options):
    """Original one-condition/list API; live clients must be accounted gateways.

    No client means the original offline stub. Live execution requires a fresh
    explicit output directory. Custom raw completion clients are refused.
    """
    return run_conditions((condition,), model=model, client=client, **options)


def run_conditions(conditions=("hinted",), *, model=DEFAULT_MODEL, client=None,
        output_dir=None, task_ids=None, live=False, max_output_tokens=128,
        max_provider_calls=24, max_estimated_cost_microusd=None, env_file=None):
    """One bounded serial run, one existing gateway, no fallback or retries."""
    selected = _selected(conditions, task_ids)
    output = _new_output(output_dir)  # Before credentials, gateway factory or dispatch.
    if type(live) is not bool or type(model) is not str or not model.strip():
        raise ValueError("INVALID_EXECUTION_SELECTION")
    for name, value, ceiling in (("OUTPUT_TOKENS", max_output_tokens, 3000),
                                 ("PROVIDER_CALLS", max_provider_calls, 24)):
        if type(value) is not int or not 0 < value <= ceiling:
            raise ValueError("INVALID_" + name)
    cap = max_estimated_cost_microusd
    if cap is not None and (type(cap) is not int or not 0 < cap <= 50000):
        raise ValueError("INVALID_ESTIMATED_POLICY")
    active = client if client is not None else OfflineStubClient()
    requested_live = live or type(active) is not OfflineStubClient
    has_provider = requested_live and any(condition != "exact_oracle" for condition, _ in selected)
    if live and type(client) is OfflineStubClient:
        raise ValueError("LIVE_CANNOT_USE_OFFLINE_STUB")
    if has_provider and output is None:
        raise ValueError("LIVE_OUTPUT_REQUIRED")
    if has_provider and client is None and cap is None:
        raise ValueError("EXPLICIT_ACCOUNTED_POLICY_REQUIRED")
    if has_provider and client is not None:
        validate_pilot_gateways({model: client}, (model,), max_tokens=max_output_tokens)
        scope = _scope(client, model, max_output_tokens)
        if scope[3] > max_provider_calls or (cap is not None and scope[2] > cap):
            raise ValueError("PFP_INJECTED_ALLOWANCE_EXCEEDS_REQUESTED_CAP")
    pins, run_id = _pins(), uuid4().hex
    if output is not None:
        try:
            output.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise ValueError("OUTPUT_DIR_EXISTS") from exc
    if has_provider and client is None:
        active = make_pilot_gateways((model,), max_output_tokens=max_output_tokens,
            max_estimated_cost_microusd=cap, max_calls=max_provider_calls,
            accounting_path=output / "accounting.sqlite3", env_file=env_file,
            run_id=run_id, objective_sha256=hashlib.sha256(json.dumps(
                [(condition, asdict(instance)) for condition, instance in selected],
                sort_keys=True).encode()).hexdigest())[model]
    receipts, stop_reason = [], None
    for index, (condition, instance) in enumerate(selected):
        certificate = host_certificate(instance)
        host_verdict = str(certificate["verdict"])
        if instance.expected_verdict != host_verdict:
            raise ValueError("DECLARED_LABEL_HOST_MISMATCH")
        prompt = format_prompt(instance, condition)
        turn, attempt, attempted = None, None, False
        if condition == "exact_oracle":
            content, tokens, cost, latency = f"Host verdict copied: {host_verdict}", 0, 0.0, 0.0
            verdict, provider, status = host_verdict, "host", "HOST_ACCEPTED"
        elif not has_provider:
            content, tokens, cost, latency = active.complete(prompt, max_output_tokens)
            verdict, provider, status = parse_verdict(content), "offline-stub", "HOST_REJECTED"
        else:
            attempt = f"retraction:{run_id}:{condition}:{instance.task_id}"
            turn = complete_pilot_turn(active, _request(prompt), model=model,
                task_id=instance.task_id, attempt_id=attempt, max_tokens=max_output_tokens)
            try:
                claim = active.action(attempt)
            except KeyError:
                claim = None
            turn["action_record"] = claim
            attempted = bool(turn["provider_wire"] or
                claim is not None and claim["state"] != "refused_before_dispatch")
            counts = [turn["usage"].get(key) for key in ("prompt_tokens", "completion_tokens")]
            tokens = sum(counts) if all(type(value) is int for value in counts) else None
            cost = 0.0 if _known_no_dispatch(turn) else turn["usage"].get("cost")
            latency = turn["elapsed"]
            provider = "openrouter"
            if (not turn["ok"] or turn["stop"]
                    or type(turn["pfp"].get("answer")) is not str):
                content, verdict, status = "", "UNKNOWN", "REFUSED"
                stop_reason = turn["error"] or "NON_STRING_PFP_ANSWER"
            else:
                content, status = turn["content"], "HOST_REJECTED"
                verdict = parse_verdict(content)
        matched = status != "REFUSED" and verdict == instance.expected_verdict
        if status != "REFUSED":
            status = "HOST_ACCEPTED" if matched else "HOST_REJECTED"
        receipt = ExecutionReceipt(SCHEMA, instance.task_id, condition, model, provider,
            verdict, host_verdict, instance.expected_verdict, matched, tokens, cost, latency,
            "", content, certificate, asdict(instance), prompt, pins["runner"], status,
            _grade(condition, provider) if status != "REFUSED" else "UNVERIFIED_REFUSAL",
            attempt, attempted, turn)
        receipt = replace(receipt, digest_sha256=receipt_digest(receipt))
        receipts.append(receipt)
        if output is not None:
            with (output / "receipts.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(asdict(receipt), sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
        if stop_reason:
            break
    if _pins() != pins:
        stop_reason = "SOURCE_CHANGED_DURING_RUN"
    summary = dict(schema=SUMMARY_SCHEMA, mode="accounted-pfp" if has_provider else "offline-controls",
        model=model, conditions=list(dict.fromkeys(condition for condition, _ in selected)),
        task_ids=list(dict.fromkeys(instance.task_id for _, instance in selected)), run_id=run_id,
        instances=len(receipts), planned=len(selected), matched=sum(row.matched_ground_truth for row in receipts),
        completed=stop_reason is None, stop_reason=stop_reason,
        unattempted=[dict(condition=condition, task_id=instance.task_id)
            for condition, instance in selected[len(receipts):]],
        provider_calls=sum(row.provider_attempted for row in receipts),
        observed_models=([model] if any(row.provider == "openrouter" and row.status != "REFUSED"
                                       for row in receipts) else []),
        blind_model_results=sum(row.evidence_grade == "BOUND_MODEL_ORIGINAL_JUDGE" for row in receipts),
        assisted_model_results=sum(row.evidence_grade == "ASSISTED_ANSWER_BEARING_MODEL" for row in receipts),
        total_cost_usd=(None if any(row.cost_usd is None for row in receipts)
                        else sum(row.cost_usd for row in receipts)),
        known_cost_usd=sum(row.cost_usd for row in receipts if row.cost_usd is not None),
        unknown_cost_count=sum(row.cost_usd is None for row in receipts),
        max_output_tokens=max_output_tokens, max_provider_calls=max_provider_calls,
        financial_policy=("no_provider" if not has_provider else "injected_accounted" if client is not None
                          else "explicitly_estimated_not_vendor_liability_cap"),
        source_pins=pins, historical_source_sha256=HISTORICAL_SOURCE_SHA256,
        authority_effect="None", controls_honored="UNVERIFIED" if has_provider else "NOT_APPLICABLE")
    if output is not None:
        summary["receipts_sha256"] = hashlib.sha256((output / "receipts.jsonl").read_bytes()).hexdigest()
        (output / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2,
            ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
    return receipts


def replay_outputs(output_dir):
    """Recheck current captured bytes and the original judge without any gateway.

    Unkeyed digests detect drift; they do not authenticate provider billing or
    authors. Historical v2 remains the sealed paper's distinct record format.
    """
    try:
        return _replay_outputs(Path(output_dir))
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("REPLAY_CAPTURE_INVALID:" + type(exc).__name__) from exc


def _replay_outputs(output):
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    if summary.get("schema") != SUMMARY_SCHEMA:
        raise ValueError("CURRENT_V3_REPLAY_REQUIRED")
    if summary["source_pins"] != _pins():
        raise ValueError("REPLAY_SOURCE_DRIFT")
    raw = (output / "receipts.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest() != summary["receipts_sha256"]:
        raise ValueError("REPLAY_RECEIPTS_DIGEST_MISMATCH")
    rows = [json.loads(line) for line in raw.splitlines()]
    selected = _selected(summary["conditions"], summary["task_ids"])
    if len(rows) != summary["instances"] or len(rows) > len(selected):
        raise ValueError("REPLAY_COVERAGE_MISMATCH")
    for index, row in enumerate(rows):
        condition, instance = selected[index]
        if row["schema"] != SCHEMA or receipt_digest(row) != row["digest_sha256"]:
            raise ValueError("REPLAY_RECEIPT_MISMATCH")
        prompt = format_prompt(instance, condition)
        if (row["task_id"] != instance.task_id or row["condition"] != condition
                or row["instance"] != json.loads(json.dumps(asdict(instance)))
                or row["host_certificate"] != host_certificate(instance)
                or row["prompt"] != prompt or row["source_sha256"] != summary["source_pins"]["runner"]
                or row["model"] != summary["model"]):
            raise ValueError("REPLAY_TASK_OR_CHECKER_MISMATCH")
        if row["provider"] == "openrouter":
            if condition == "exact_oracle":
                raise ValueError("REPLAY_ORACLE_CANNOT_BE_MODEL")
            attempt = f"retraction:{summary['run_id']}:{condition}:{instance.task_id}"
            if row["attempt_id"] != attempt:
                raise ValueError("REPLAY_BINDING_MISMATCH")
            prepared = prepare_task_turn(system=SYSTEM, user=prompt, task_id=instance.task_id,
                attempt_id=attempt, answer_schema=ANSWER_SCHEMA, checker_id="pilot-original-judge-pending-v1")
            request = _request(prompt)
            expected = build_openai_compat_body(replace(request, system=prepared.prompt.system,
                user=prepared.prompt.user),
                model=row["model"], max_tokens=summary["max_output_tokens"], provider=Provider.OPENROUTER)
            turn = row["turn"]
            if turn["request"] != expected:
                raise ValueError("REPLAY_REQUEST_MISMATCH")
            wire = turn["provider_wire"]
            claim = turn["action_record"]
            attempted = bool(wire or claim is not None and claim["state"] != "refused_before_dispatch")
            cost = 0.0 if _known_no_dispatch(turn) else None
            if wire is not None:
                actual = base64.b64decode(wire["raw_reply_base64"], validate=True)
                if (hashlib.sha256(actual).hexdigest() != wire["raw_reply_sha256"]
                        or len(actual) != wire["raw_reply_bytes"]):
                    raise ValueError("REPLAY_RAW_MISMATCH")
                if turn["pfp"] is not None:
                    candidate = parse_openai_compat_response(json.loads(actual),
                        provider=Provider.OPENROUTER, fallback_model=row["model"])
                    checked = prepared.check_completion(candidate.content)
                    if json.loads(json.dumps(checked)) != turn["pfp"] or candidate.model != row["model"]:
                        raise ValueError("REPLAY_PFP_MISMATCH")
                    cost = candidate.cost_usd
            elif turn["ok"]:
                raise ValueError("REPLAY_RAW_MISSING")
            if row["cost_usd"] != cost or row["provider_attempted"] != attempted:
                raise ValueError("REPLAY_COST_OR_DISPATCH_MISMATCH")
            eligible = (turn["ok"] and not turn["stop"] and wire is not None
                and turn["pfp"] is not None and checked["schema_valid"]
                and checked["failure_class"] == "NONE"
                and type(checked["answer"]) is str and candidate.cost_usd is not None
                and turn["attempt_state"] in {"CompletedSettled", "CompletedPendingSettlement"})
            if eligible:
                if checked["answer"] != row["raw_content"] or turn["content"] != row["raw_content"]:
                    raise ValueError("REPLAY_ANSWER_MISMATCH")
                verdict = parse_verdict(row["raw_content"])
            else:
                if row["status"] != "REFUSED" or row["raw_content"] != "":
                    raise ValueError("REPLAY_REFUSAL_PROMOTED")
                verdict = "UNKNOWN"
        elif row["provider"] == "host" and condition == "exact_oracle":
            eligible = True
            if row["cost_usd"] != 0 or row["provider_attempted"] is not False:
                raise ValueError("REPLAY_COST_OR_DISPATCH_MISMATCH")
            verdict = str(host_certificate(instance)["verdict"])
            if row["raw_content"] != f"Host verdict copied: {verdict}" or row["turn"] is not None:
                raise ValueError("REPLAY_ORACLE_MISMATCH")
        elif row["provider"] == "offline-stub" and condition != "exact_oracle":
            eligible = True
            if row["cost_usd"] != 0 or row["provider_attempted"] is not False:
                raise ValueError("REPLAY_COST_OR_DISPATCH_MISMATCH")
            content, _, _, _ = OfflineStubClient().complete(prompt)
            if row["raw_content"] != content or row["turn"] is not None:
                raise ValueError("REPLAY_STUB_MISMATCH")
            verdict = parse_verdict(content)
        else:
            raise ValueError("REPLAY_EXECUTION_MODE_MISMATCH")
        matched = eligible and verdict == instance.expected_verdict
        status = "REFUSED" if not eligible else "HOST_ACCEPTED" if matched else "HOST_REJECTED"
        grade = _grade(condition, row["provider"]) if eligible else "UNVERIFIED_REFUSAL"
        if (row["verdict_emitted"] != verdict or row["matched_ground_truth"] != matched
                or row["status"] != status or row["evidence_grade"] != grade
                or row["host_verdict"] != instance.expected_verdict
                or row["expected_verdict"] != instance.expected_verdict):
            raise ValueError("REPLAY_JUDGE_MISMATCH")
    refused = [row for row in rows if row["status"] == "REFUSED"]
    unattempted = [dict(condition=condition, task_id=instance.task_id)
                   for condition, instance in selected[len(rows):]]
    total_cost = (None if any(row["cost_usd"] is None for row in rows)
                  else sum(row["cost_usd"] for row in rows))
    if (summary["planned"] != len(selected) or summary["unattempted"] != unattempted
            or summary["completed"] != (not refused and not unattempted)
            or summary["matched"] != sum(row["matched_ground_truth"] for row in rows)
            or summary["known_cost_usd"] != sum(row["cost_usd"] for row in rows if row["cost_usd"] is not None)
            or summary["unknown_cost_count"] != sum(row["cost_usd"] is None for row in rows)
            or summary["total_cost_usd"] != total_cost
            or summary["provider_calls"] != sum(row["provider_attempted"] for row in rows)
            or (refused and rows[-1] is not refused[0])):
        raise ValueError("REPLAY_SUMMARY_MISMATCH")
    return dict(status="REPLAYED", replayed=len(rows), original_completed=summary["completed"],
        provider_calls=0, authority_effect="None")
