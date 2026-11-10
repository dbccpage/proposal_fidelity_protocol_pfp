"""Independent exact C029 coset optimality check over the supplied GF(2) matrix.

The original matching-certificate judge remains a separate required check. This
Python implementation does not establish the original Rust/protocol obligations.
AuthorityEffect: None.
"""

from __future__ import annotations

CHECKER_ID = "c029:gf2_coset_optimality.v1"
MAX_QUBITS = 50
MAX_KERNEL_DIMENSION = 26


def _kernel(rows: list[int], n: int) -> list[int]:
    """Row reduction: each free coordinate supplies exactly one kernel vector."""
    reduced = rows.copy()
    pivots = []
    for column in range(n):
        pivot = next((i for i in range(len(pivots), len(rows))
                      if reduced[i] & (1 << column)), None)
        if pivot is None:
            continue
        rank = len(pivots)
        reduced[rank], reduced[pivot] = reduced[pivot], reduced[rank]
        for i in range(len(rows)):
            if i != rank and reduced[i] & (1 << column):
                reduced[i] ^= reduced[rank]
        pivots.append(column)
    basis = []
    for free in range(n):
        if free not in pivots:
            vector = 1 << free
            for row, pivot in zip(reduced, pivots):
                if row & (1 << free):
                    vector |= 1 << pivot
            basis.append(vector)
    return basis


def _minimum_weight(candidate: int, basis: list[int], weights: list[int]) -> int:
    """Enumerate the full coset, pruning only with a rigorous lower bound.

    At depth i, remaining vectors can change only coordinates in suffix[i].
    The cost of set bits outside that union is therefore unavoidable. Positive
    weights make it a lower bound for every descendant; equal-bound branches
    cannot improve the incumbent. Every other branch is explored, including
    every logical class and tied minimizer's class.
    """
    masks = [sum(1 << q for q, weight in enumerate(weights) if weight == w)
             for w in range(1, 6)]

    def cost(bits):
        return sum(w * (bits & mask).bit_count() for w, mask in enumerate(masks, 1))

    suffix = [0] * (len(basis) + 1)
    for i in range(len(basis) - 1, -1, -1):
        suffix[i] = suffix[i + 1] | basis[i]
    best = cost(candidate)

    def search(i, bits):
        nonlocal best
        if cost(bits & ~suffix[i]) >= best:
            return
        if i == len(basis):
            best = cost(bits)
            return
        unchanged, changed = bits, bits ^ basis[i]
        if cost(changed & ~suffix[i + 1]) < cost(unchanged & ~suffix[i + 1]):
            unchanged, changed = changed, unchanged
        search(i + 1, unchanged)
        search(i + 1, changed)

    search(0, candidate)
    return best


def _json_value(value):
    if value is None or type(value) in (int, str):
        return True
    if type(value) is list:
        return all(_json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_value(item) for key, item in value.items())
    return False


def verify_independent_coset(case, result):
    """Return the retained judge tuple shape, without consulting matching code.

    Refusal witnesses are checked directly. Malformed/unsupported finite inputs
    are rejected, never turned into an accepted UNKNOWN or a guessed optimum.
    The certificate field is retained but its mathematics belongs to the primary
    judge; this checker independently establishes correction optimality only.
    """
    def reject(reason):
        return False, reason, {}

    if type(case) is not dict or type(result) is not dict:
        return reject("Case and answer must be JSON objects")
    if type(case.get("case_id")) is not str or not case["case_id"]:
        return reject("Missing case_id")
    if type(result.get("id")) is not str or result["id"] != case["case_id"]:
        return reject("Answer id must exactly match case_id")
    schemas = {
        "SOLVED": {"id", "status", "correction", "weight", "certificate"},
        "UNKNOWN": {"id", "status", "refusal_code"},
        "OUT_OF_SCOPE": {"id", "status", "witness"},
    }
    status = result.get("status")
    if type(status) is not str or status not in schemas:
        return reject("Unsupported status")
    if set(result) != schemas[status] or not _json_value(result):
        return reject("Answer does not match the original JSON envelope")
    code, distance = case.get("code"), case.get("distance")
    if type(code) is not str or type(distance) is not int:
        return reject("Code and distance must be an explicit string and integer")
    if code not in ("rotated", "toric"):
        witness = {"kind": "unknown_code_type", "code": code}
        valid = status == "OUT_OF_SCOPE" and result["witness"] == witness
        return valid, "Unknown code type witness checked", {"witness": witness}
    distances = (3, 5, 7) if code == "rotated" else (3, 4, 5)
    if distance not in distances:
        valid = status == "UNKNOWN" and result["refusal_code"] == "DISTANCE_OUT_OF_BOUNDS"
        return valid, "Distance bound refusal checked", {"distance": distance}

    n = distance * distance * (2 if code == "toric" else 1)
    m = distance * distance if code == "toric" else (n - 1) // 2
    hz, weights, syndrome = case.get("hz"), case.get("weights"), case.get("syndrome")
    if n > MAX_QUBITS or type(hz) is not list or len(hz) != m:
        return reject("Invalid parity-check matrix dimensions")
    if any(type(row) is not list or len(row) != n or
           any(type(bit) is not int or bit not in (0, 1) for bit in row) for row in hz):
        return reject("Parity-check matrix must have exact binary entries and dimensions")
    if type(weights) is not list or len(weights) != n or any(
        type(w) is not int or not 1 <= w <= 5 for w in weights
    ):
        return reject("Weights must be one integer in 1..5 per qubit")
    if type(syndrome) is not list or len(syndrome) != m or any(
        type(bit) is not int or bit not in (0, 1) for bit in syndrome
    ):
        return reject("Syndrome must have one exact binary entry per check")
    rows = [sum(bit << q for q, bit in enumerate(row)) for row in hz]
    if code == "toric" and sum(syndrome) % 2:
        dependency = 0
        for row in rows:
            dependency ^= row
        witness = {"kind": "odd_parity_on_torus", "rows": "all"}
        valid = (dependency == 0 and status == "OUT_OF_SCOPE"
                 and result["witness"] == witness)
        return valid, "Odd parity and actual all-row dependency checked", {"dependency": dependency}
    if status != "SOLVED":
        return reject("No declared refusal predicate holds; expected SOLVED")
    correction, stated = result["correction"], result["weight"]
    if type(correction) is not list or any(
        type(q) is not int or not 0 <= q < n for q in correction
    ) or len(correction) != len(set(correction)):
        return reject("Correction must contain distinct in-bounds integer qubit indices")
    if type(stated) is not int or stated < 0 or type(result["certificate"]) is not dict:
        return reject("Invalid stated weight or certificate object")
    candidate = sum(1 << q for q in correction)
    if [(row & candidate).bit_count() % 2 for row in rows] != syndrome:
        return reject("Correction syndrome mismatch")
    actual = sum(weights[q] for q in correction)
    if actual != stated:
        return reject("Stated weight mismatch")
    basis = _kernel(rows, n)
    if len(basis) > MAX_KERNEL_DIMENSION:
        return reject("Kernel dimension exceeds the original finite bound of 26")
    minimum = _minimum_weight(candidate, basis, weights)
    return (
        actual == minimum,
        "Independent coset optimum verified" if actual == minimum else "Correction is suboptimal",
        {"actual_weight": actual, "min_weight": minimum, "kernel_dimension": len(basis)},
    )
