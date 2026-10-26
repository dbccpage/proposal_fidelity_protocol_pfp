"""The reach ledger and its computed numbers.

AuthorityEffect: None. A row is evidence, never authorization.

The ledger is regenerated from the stored receipts under
``reach/receipts/<carrier>/<level>/<sha256>.json``. Each receipt is verified
again (K3: its ``computed`` block is deleted and recomputed), so a hand-edited
grade cannot enter. There is at most one live row per (carrier, level).

Outputs, both byte-identical on regeneration (sorted keys, no timestamps):

- ``ledger.jsonl``: one canonical line per (carrier, level) row;
- ``derived/numbers.json``: T(N), and per carrier C(N), C by band, D,
  D_native and A. No number is typed; each is counted from rows.

Definitions (W2-C05 section 4.5):

- T(N): levels n <= N with a checker of record whose gated step is in the
  reach runner's step list;
- C_X(N): levels n <= N with a row for carrier X at R1, apparatus excluded;
  for the target's own rows (TO), C is T less the apparatus levels;
- D_X: the largest k >= 1 with R1 at every level 0..k and an accepted lift
  certificate for every step j -> j+1 below k; otherwise 0;
- D_native: accepted lifts on the carrier's own ladder;
- A_X(N): apparatus rows at R1, never in C or D. For the target, A counts the
  gated checkers of record registered with ``"provenance": "apparatus"``
  (ruling D4 of 2026-09-25: levels 012, 017 and 082-100). Such a checker
  still counts in T, which counts checkers; its level counts in A, never in C.

No lift certificate is accepted by this version (lift acceptance is round P2
work), so every D is 0 by construction until one is.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import canonical_bytes, compact_line, digest, digest_obj
from .receipt import Context, verify_receipt

BANDS = (("000-021", 0, 21), ("022-046", 22, 46), ("047-073", 47, 73), ("074-100", 74, 100))
TOP_LEVEL = 100
TARGET_CARRIER = "the_symbol_game"
# A checker of record's registry entry may carry "provenance": "apparatus";
# absent means an object-language checker. No other value is accepted.
PROVENANCES = frozenset({"apparatus"})


class LedgerError(ValueError):
    pass


@dataclass(frozen=True)
class StoredReceipt:
    carrier_dir: str
    level_dir: str
    name: str
    data: bytes


def carrier_keys(carriers: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    for repo in sorted(carriers):
        for part in carriers[repo]["parts"]:
            keys.append(repo if part == "repo_content" else f"{repo}+harness")
    return sorted(keys)


def carrier_key(repo: str, part: str) -> str:
    return repo if part == "repo_content" else f"{repo}+harness"


def row_from_receipt(receipt: Mapping[str, Any], receipt_sha: str) -> dict[str, Any]:
    computed = receipt["computed"]
    by_kind: dict[str, list[str]] = {"decisive_mutation": [], "near_miss": [], "own_negative": [], "positive": []}
    for fixture in computed["fixtures"]:
        by_kind[fixture["kind"]].append(fixture["payload_sha256"])
    transport = computed["transport"] or {}
    return {
        "authority_effect": "None",
        "carrier": carrier_key(receipt["carrier"]["repo"], receipt["carrier"]["part"]),
        "carrier_commit": receipt["carrier"]["commit"],
        "carrier_manifest_sha256": digest_obj(
            sorted(receipt["carrier"]["sources"], key=lambda source: source["path"])
        ),
        "checker": {"id": receipt["checker"]["id"], "sha256": receipt["checker"]["sha256"]},
        "comparison_row": None,
        "fixtures": {kind: sorted(values) for kind, values in by_kind.items()},
        "framing": receipt["framing"],
        "grades": computed["grades"],
        "level": receipt["ladder"]["level"],
        "loss_ledger_sha256": transport.get("loss_ledger_sha256"),
        "promotion": None,
        "receipt_sha256": receipt_sha,
        "row_sha256": receipt["ladder"]["row_sha256"],
        "status_ceiling": computed["status_ceiling"],
        "terminal": computed["terminal"],
        "transport_certificate_sha256": transport.get("certificate_sha256"),
    }


def build_rows(stored: Iterable[StoredReceipt], ctx: Context) -> list[dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for item in sorted(stored, key=lambda s: (s.carrier_dir, s.level_dir, s.name)):
        sha = digest(item.data)
        if item.name != sha.split(":", 1)[1] + ".json":
            raise LedgerError(f"receipt file {item.name} is not named by its digest")
        result = verify_receipt(item.data, ctx)
        if result.codes:
            raise LedgerError(f"stored receipt {item.name} does not verify: {', '.join(result.codes)}")
        receipt = result.receipt
        row = row_from_receipt(receipt, sha)
        if row["carrier"] != item.carrier_dir or f"{row['level']:03d}" != item.level_dir:
            raise LedgerError(f"receipt {item.name} is filed under the wrong carrier or level")
        key = (row["carrier"], row["level"])
        if key in rows:
            raise LedgerError(f"two live rows for carrier {key[0]} at level {key[1]}")
        rows[key] = row
    return [rows[key] for key in sorted(rows)]


def depth(levels_at_r1: set[int], lifts: set[tuple[int, int]]) -> int:
    """D: the largest k >= 1 with R1 at 0..k and a lift for every step below k."""
    best = 0
    k = 1
    while k <= TOP_LEVEL and all(level in levels_at_r1 for level in range(k + 1)) and all(
        (j, j + 1) in lifts for j in range(k)
    ):
        best = k
        k += 1
    return best


def _by_band(levels: set[int]) -> dict[str, int]:
    return {name: sum(1 for level in levels if low <= level <= high) for name, low, high in BANDS}


def apparatus_levels(checkers: Mapping[str, Any]) -> set[int]:
    """Levels whose checker of record is registered as apparatus (ruling D4)."""
    out: set[int] = set()
    for checker_id, entry in sorted(checkers.items()):
        if "provenance" not in entry:
            continue
        if entry["provenance"] not in PROVENANCES:
            raise LedgerError(f"checker {checker_id} declares unknown provenance {entry['provenance']!r}")
        out.add(entry["level"])
    return out


def numbers(
    rows: list[dict[str, Any]],
    ctx: Context,
    ledger_sha256: str,
    lifts: Mapping[str, set[tuple[int, int]]] | None = None,
) -> dict[str, Any]:
    lifts = lifts or {}
    gated_levels = {
        entry["level"] for entry in ctx.checkers.values() if entry.get("gated_step") in ctx.gated_steps
    }
    gated_apparatus = gated_levels & apparatus_levels(ctx.checkers)
    per_carrier: dict[str, Any] = {}
    for key in carrier_keys(ctx.carriers):
        mine = [row for row in rows if row["carrier"] == key]
        coverage = {row["level"] for row in mine if row["grades"]["R"] == "R1" and row["framing"] != "AP"}
        apparatus = {row["level"] for row in mine if row["grades"]["R"] == "R1" and row["framing"] == "AP"}
        if key == TARGET_CARRIER:
            coverage = gated_levels - gated_apparatus
            apparatus |= gated_apparatus
        per_carrier[key] = {
            "A": len(apparatus),
            "C": len(coverage),
            "C_by_band": _by_band(coverage),
            "D": depth(coverage, lifts.get(key, set())),
            "D_native": 0,
            "rows": len(mine),
        }
    return {
        "authority_effect": "None",
        "carriers": per_carrier,
        "ledger_sha256": ledger_sha256,
        "N": TOP_LEVEL,
        "non_claims": [
            "every number is counted from ledger rows by code; none is typed",
            "an absent row means NONE; no row is generated for a level without evidence",
            "D counts accepted lift certificates; this version accepts none, so D is 0 by construction",
            "D_native is 0: no lift record on any carrier's own ladder has been accepted",
            "apparatus counts in A, never in C or D; the target's apparatus levels are its checkers of record "
            "registered with provenance apparatus (ruling D4: 012, 017, 082-100)",
            "coverage and depth are separate numbers and are never joined into one word",
        ],
        "registry": {
            "levels": len(ctx.stage_registry["levels"]),
            "registry_version": ctx.stage_registry["registry_version"],
            "table_sha256": ctx.stage_registry["table"]["sha256"],
        },
        "rows": len(rows),
        "schema": "mssn.reach-numbers.v1",
        "T": {"by_band": _by_band(gated_levels), "value": len(gated_levels)},
    }


def ledger_bytes(rows: list[dict[str, Any]]) -> bytes:
    return b"".join(compact_line(row) for row in rows)


def read_stored(receipts_dir: Path) -> list[StoredReceipt]:
    if not receipts_dir.exists():
        return []
    out: list[StoredReceipt] = []
    for path in sorted(receipts_dir.rglob("*.json")):
        rel = path.relative_to(receipts_dir).parts
        if len(rel) != 3:
            raise LedgerError(f"receipt {path} is not at <carrier>/<level>/<sha256>.json")
        out.append(StoredReceipt(rel[0], rel[1], rel[2], path.read_bytes()))
    return out


def build(receipts_dir: Path, ctx: Context) -> tuple[bytes, bytes]:
    rows = build_rows(read_stored(receipts_dir), ctx)
    ledger = ledger_bytes(rows)
    return ledger, canonical_bytes(numbers(rows, ctx, digest(ledger)))
