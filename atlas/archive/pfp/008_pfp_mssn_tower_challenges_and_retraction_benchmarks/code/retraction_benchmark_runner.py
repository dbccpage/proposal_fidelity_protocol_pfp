"""Single-shot graph-consistency runner for Paper 008.

Each benchmark instance is a small directed graph with an integer claim on
every edge. The question is whether a potential pi: V -> Z exists with
pi(v) - pi(u) = claim for every edge. The host answers it exactly by
spanning-tree propagation and attaches a checkable certificate to its verdict:
a potential that satisfies every edge, or a dual witness, namely a closed walk
whose signed claim sum is nonzero. A model (or the offline stub) is asked the
same question under one of four prompt conditions:

  baseline      the graph only;
  hinted        the graph plus the host's own residuals, which determine the
                answer (an assisted, answer-bearing condition);
  scratchpad    the graph plus a step-by-step propagation instruction;
  exact_oracle  no model call; the host verdict is copied (a control).

Offline mode (the default) never opens a network connection. It replaces the
model with a deterministic stub that reads the prompt text, so it checks the
plumbing and the scoring, not any model. Live mode is opt-in with ``--live``
and reads ``OPENROUTER_API_KEY`` from the process environment only; this
module never reads a ``.env`` file.

Every run writes ``receipts.jsonl`` and ``summary.json`` to an explicit
``--output-dir`` or, by default, to a new temporary directory. Output inside
this package directory is refused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, replace
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
CONDITIONS = ("baseline", "hinted", "scratchpad", "exact_oracle")


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


# Six fixed instances: a tree, a consistent and an inconsistent triangle,
# a consistent and an inconsistent diamond, and an inconsistent K4.
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


class BudgetController:
    """Refuses a call before it is made when the ceiling would be exceeded."""

    def __init__(self, ceiling_usd: float = 0.10) -> None:
        self.ceiling_usd = ceiling_usd
        self.cumulative_cost_usd = 0.0
        self.call_count = 0

    def check_pre_call(self, estimated_cost_usd: float = 0.001) -> None:
        if self.cumulative_cost_usd + estimated_cost_usd > self.ceiling_usd:
            raise RuntimeError(
                f"BudgetGate: cumulative cost ${self.cumulative_cost_usd:.5f} + estimated "
                f"${estimated_cost_usd:.5f} exceeds ceiling ${self.ceiling_usd:.5f}; call refused."
            )

    def record_cost(self, actual_cost_usd: float) -> None:
        self.cumulative_cost_usd += actual_cost_usd
        self.call_count += 1


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
    tokens: int
    cost_usd: float
    latency_sec: float
    digest_sha256: str
    raw_content: str
    host_certificate: dict[str, object]
    instance: dict[str, object]
    prompt: str
    source_sha256: str


def receipt_digest(receipt: ExecutionReceipt | dict[str, object]) -> str:
    """Bind every recorded field except the digest itself, including the raw reply.

    This unkeyed content hash does not authenticate a provider or author.
    A JSON-loaded receipt can be checked with the same function.
    """
    payload = asdict(receipt) if isinstance(receipt, ExecutionReceipt) else dict(receipt)
    payload.pop("digest_sha256", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class OfflineStubClient:
    """Deterministic stand-in for a model. It opens no network connection.

    The stub answers CONTRADICTION when the prompt text itself reports a
    nonzero residual (as the hinted prompt does) and CONSISTENT otherwise. It
    therefore exercises parsing, scoring and receipts; it measures no model.
    """

    provider = "offline-stub"

    def __init__(self, budget_controller: BudgetController | None = None) -> None:
        self.budget_controller = budget_controller or BudgetController()

    def complete(self, prompt: str, max_tokens: int = 128) -> tuple[str, int, float, float]:
        self.budget_controller.check_pre_call(estimated_cost_usd=0.0)
        self.budget_controller.record_cost(0.0)
        if "gap=" in prompt:
            content = "VERDICT: CONTRADICTION\nThe host reports a nonzero residual."
        else:
            content = "VERDICT: CONSISTENT"
        return content, len(prompt) // 4 + 8, 0.0, 0.0


class OpenRouterClient:
    """Live client; used only when the caller passes ``--live``."""

    provider = "openrouter"

    def __init__(self, model: str, api_key: str, budget_controller: BudgetController | None = None) -> None:
        if not api_key:
            raise ValueError("live mode requires a nonempty API key")
        self.model = model
        self.api_key = api_key
        self.budget_controller = budget_controller or BudgetController()

    def complete(self, prompt: str, max_tokens: int = 128) -> tuple[str, int, float, float]:
        self.budget_controller.check_pre_call()
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Answer with VERDICT: CONSISTENT or VERDICT: CONTRADICTION, then a short reason.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.0,
        }
        request = urllib.request.Request(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload).encode("utf-8"),
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"provider HTTP error {error.code}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"provider call failed: {error.reason}") from error
        latency = time.monotonic() - started
        content = data["choices"][0]["message"].get("content", "")
        usage = data.get("usage", {})
        tokens = int(usage.get("total_tokens", 0))
        cost = float(usage.get("cost", 0.0))
        self.budget_controller.record_cost(cost)
        return content, tokens, cost, latency


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


def run_benchmark(
    condition: str = "hinted",
    model: str = "meta-llama/llama-3.1-8b-instruct",
    client: OfflineStubClient | OpenRouterClient | None = None,
) -> list[ExecutionReceipt]:
    """Run every instance under one condition. Without a client the offline stub is used."""
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    active = client if client is not None else OfflineStubClient()
    receipts: list[ExecutionReceipt] = []
    source_path = Path(__file__)
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    for instance in BENCHMARK_INSTANCES:
        instance_record = asdict(instance)
        certificate = host_certificate(instance)
        host_verdict = str(certificate["verdict"])
        expected_verdict = instance.expected_verdict
        if expected_verdict != host_verdict:
            raise ValueError(f"{instance.task_id}: declared label disagrees with its checked host certificate")
        prompt = format_prompt(instance, condition)
        if condition == "exact_oracle":
            content, tokens, cost, latency = f"Host verdict copied: {host_verdict}", 0, 0.0, 0.0
            verdict = host_verdict
        else:
            content, tokens, cost, latency = active.complete(prompt)
            verdict = parse_verdict(content)
        matched = verdict == expected_verdict
        receipt = ExecutionReceipt(
            schema="pfp008.graph-consistency-receipt.v2",
            task_id=instance.task_id,
            condition=condition,
            model=model,
            provider=active.provider if condition != "exact_oracle" else "host",
            verdict_emitted=verdict,
            host_verdict=host_verdict,
            expected_verdict=expected_verdict,
            matched_ground_truth=matched,
            tokens=tokens,
            cost_usd=cost,
            latency_sec=latency,
            digest_sha256="",
            raw_content=content,
            host_certificate=certificate,
            instance=instance_record,
            prompt=prompt,
            source_sha256=source_sha256,
        )
        receipts.append(replace(receipt, digest_sha256=receipt_digest(receipt)))
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_sha256:
        raise RuntimeError("runner source changed during the run; receipts refused")
    return receipts


def resolve_output_dir(requested: str | None) -> Path:
    """Return an output directory outside this package, creating it if needed."""
    if requested is None:
        return Path(tempfile.mkdtemp(prefix="pfp008_runner_"))
    path = Path(requested).resolve()
    if path == PACKAGE_ROOT or path.is_relative_to(PACKAGE_ROOT):
        raise ValueError(f"refusing to write inside the package directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_outputs(output_dir: Path, receipts: list[ExecutionReceipt], mode: str) -> Path:
    with (output_dir / "receipts.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for receipt in receipts:
            handle.write(json.dumps(asdict(receipt), sort_keys=True) + "\n")
    summary = {
        "mode": mode,
        "condition": receipts[0].condition if receipts else None,
        "model": receipts[0].model if receipts else None,
        "instances": len(receipts),
        "matched": sum(r.matched_ground_truth for r in receipts),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Paper 008 single-shot graph-consistency runner")
    parser.add_argument("--condition", choices=CONDITIONS, default="hinted")
    parser.add_argument("--model", default="meta-llama/llama-3.1-8b-instruct")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--mock", action="store_true", help="offline stub; the default")
    mode.add_argument("--live", action="store_true", help="call OpenRouter with OPENROUTER_API_KEY")
    parser.add_argument("--ceiling", type=float, default=0.10, help="spend ceiling in USD (live mode)")
    parser.add_argument("--output-dir", default=None, help="directory for receipts (default: new temp dir)")
    args = parser.parse_args(argv)

    try:
        output_dir = resolve_output_dir(args.output_dir)
    except ValueError as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2

    budget = BudgetController(ceiling_usd=args.ceiling)
    client: OfflineStubClient | OpenRouterClient
    if args.live:
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            print("REFUSED: --live needs OPENROUTER_API_KEY in the process environment.", file=sys.stderr)
            return 2
        client = OpenRouterClient(model=args.model, api_key=api_key, budget_controller=budget)
        mode_name = "live"
    else:
        client = OfflineStubClient(budget_controller=budget)
        mode_name = "offline-stub"

    receipts = run_benchmark(condition=args.condition, model=args.model, client=client)
    summary_path = write_outputs(output_dir, receipts, mode_name)
    matched = sum(r.matched_ground_truth for r in receipts)
    print(f"Paper 008 runner | mode={mode_name} | condition={args.condition} | model={args.model}")
    for receipt in receipts:
        status = "MATCH" if receipt.matched_ground_truth else "MISS"
        print(f"  [{status}] {receipt.task_id}: emitted={receipt.verdict_emitted} host={receipt.host_verdict}")
    print(f"{matched}/{len(receipts)} verdicts match the host. Receipts: {summary_path.parent}")
    return 0 if matched == len(receipts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
