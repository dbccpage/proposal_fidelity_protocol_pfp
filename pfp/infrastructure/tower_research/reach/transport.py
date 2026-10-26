"""``mssn.transport-certificate.v2``: one certificate, six criteria, one loss ledger.

AuthorityEffect: None. A certificate is issued ``PROPOSED`` with disposition
``TARGET_REPLAY_REQUIRED``; only the receiving side's replay moves the
disposition, and no disposition means admitted.

This reconciles the two V1 types (W2-C05 section 5). The runtime type
``omega.symgam.transport-certificate.v1`` is unchanged and is called the
*simplicial transport measure* in prose; submitting it where V2 is required is
refused (``TC-V1-PRESENTED-AS-V2``). The atlas 05.1 draft is retired by this
schema.

Criteria:

1. identity and custody (``c1_identity_custody``);
2. a typed map (``c2_typed_map``); this version implements ``SORT_MAP`` with an
   explicit finite element table, checked for being a function and injective by
   enumeration. ``SIMPLICIAL`` and ``MATRIX_BY_GRADE`` are refused as
   unsupported until implemented;
3. compatibility squares, or a stated N/A reason, refused when the level names a
   structure map (``c3_compatibility``);
4. goal and move correspondence, with the cost conversion (``c4_goal_and_moves``);
5. target verification: the witness digest the receiving side replays
   (``c5_target_verification``);
6. loss and authority: the sealed loss ledger (``c6_loss_and_authority``).

The loss ledger ``mssn.loss-ledger.v2`` books what the map drops. A carrier's
standing entries (for 19L57G1: ``mu1`` ties, readings L and F, declared bounds,
claim class, and name-blindness) must each be booked, or stated not applicable
with a reason. An empty ledger is a positive claim that nothing was lost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .canonical import digest_obj, domain_digest
from .schema import Enum, ListOf, Nullable, Obj, SchemaError, validate

SCHEMA_ID = "mssn.transport-certificate.v2"
LEDGER_SCHEMA_ID = "mssn.loss-ledger.v2"
PAYLOAD_DOMAIN_TAG = "mssn.transport-certificate"
LEDGER_DOMAIN_TAG = "mssn.loss-ledger"
PROFILE = "omega-sorted-json-no-float-v1"
V1_SCHEMA_IDS = frozenset({"omega.symgam.transport-certificate.v1", "omega.transport-certificate.v1"})
V1_MARKER_FIELDS = frozenset({"schema_version", "source_vertices", "target_vertices", "dimensional_dilation"})

CLASSIFICATIONS = frozenset({"PRESERVED", "WEAKENED", "DROPPED", "UNKNOWN"})
MAP_KINDS = frozenset({"SORT_MAP", "SIMPLICIAL", "MATRIX_BY_GRADE"})
IMPLEMENTED_KINDS = frozenset({"SORT_MAP"})
BLINDNESS_ENTRY = "source.name_blindness"
COEFFICIENT_ENTRY = "source.coefficient_domain"

LOSS_FIELD_ROW = Obj(
    {
        "classification": Enum(CLASSIFICATIONS),
        "field_or_law": "str",
        "not_applicable_reason": Nullable("str"),
        "source_value": "str",
        "target_value": "str",
    }
)

LOSS_LEDGER = Obj(
    {
        "authority_effect": Enum(frozenset({"None"})),
        "changed_assumptions": ListOf("str"),
        "commitment_sha256": "digest",
        "count": "any",
        "fields": ListOf(LOSS_FIELD_ROW),
        "measure": Nullable("any"),
        "open_obligations": ListOf("str"),
        "reframe_decision": Enum(frozenset({"NONE", "CHILD_REFRAME"})),
        "schema": Enum(frozenset({LEDGER_SCHEMA_ID})),
        "status_ceiling": "str",
    }
)

CERTIFICATE = Obj(
    {
        "authority_effect": Enum(frozenset({"None"})),
        "c1_identity_custody": Obj(
            {
                "adapter": Nullable(Obj({"path": "str", "sha256": "digest"})),
                "coefficient_domain": Obj({"source": "str", "target": "str"}),
                "same_carrier": "bool",
                "source_manifest_sha256": "digest",
            }
        ),
        "c2_typed_map": Obj(
            {
                "kind": Enum(MAP_KINDS),
                "pairs": ListOf(ListOf("str")),
                "sorts": ListOf(Obj({"source": "str", "target": "str"})),
                "unmapped_sorts": ListOf("str"),
            }
        ),
        "c3_compatibility": Obj(
            {
                "not_applicable_reason": Nullable("str"),
                "squares": ListOf(
                    Obj({"lhs_sha256": "digest", "rhs_sha256": "digest", "structure_map": "str"})
                ),
            }
        ),
        "c4_goal_and_moves": Obj(
            {
                "cost": Obj({"source_measure": "str", "target_convention": "str", "value": "rational"}),
                "source_goal_sha256": "digest",
                "target_goal_sha256": "digest",
            }
        ),
        "c5_target_verification": Obj(
            {"source_admission_is_provenance_only": "bool", "witness_sha256": "digest"}
        ),
        "c6_loss_and_authority": Obj(
            {
                "loss_ledger": "any",
                "reframe": Obj({"child": Nullable("digest"), "decision": Enum(frozenset({"NONE", "CHILD_REFRAME"}))}),
            }
        ),
        "carrier": Obj({"commit": "commit", "part": "str", "repo": "str"}),
        "disposition": "str",
        "envelope": Obj(
            {
                "canonicalization_profile": Enum(frozenset({PROFILE})),
                "payload_digest": "digest",
                "payload_domain_tag": Enum(frozenset({PAYLOAD_DOMAIN_TAG})),
            }
        ),
        "schema": "str",
        "status": "str",
        "target": Obj(
            {"checker_id": "str", "level": "int", "registry_version": "int", "repo": "str", "row_sha256": "digest"}
        ),
    }
)

_SCHEMA_CODES = {
    "unknown": "TC-UNKNOWN-FIELD",
    "schema": "TC-CRITERION-MISSING",
    "pin": "TC-DIGEST-MISMATCH",
}


@dataclass(frozen=True)
class Expectation:
    """What the receiving side knows independently of the certificate."""

    carrier: Mapping[str, str]
    target_repo: str
    level: int
    registry_version: int
    row_sha256: str
    checker_id: str
    source_manifest_sha256: str
    witness_sha256: str
    standing_entries: tuple[str, ...]
    blind_framing: bool
    structure_maps: tuple[str, ...]
    adapter_sha256: str | None = None


@dataclass(frozen=True)
class TransportFinding:
    code: str
    detail: str


def ledger_commitment(ledger: Mapping[str, Any]) -> str:
    body = {key: value for key, value in ledger.items() if key != "commitment_sha256"}
    return domain_digest(LEDGER_DOMAIN_TAG, body)


def seal_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(ledger)
    sealed["commitment_sha256"] = ledger_commitment(ledger)
    return sealed


def payload_digest(certificate: Mapping[str, Any]) -> str:
    body = {key: value for key, value in certificate.items() if key != "envelope"}
    return domain_digest(PAYLOAD_DOMAIN_TAG, body)


def seal_certificate(certificate: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(certificate)
    sealed["envelope"] = {
        "canonicalization_profile": PROFILE,
        "payload_digest": payload_digest(certificate),
        "payload_domain_tag": PAYLOAD_DOMAIN_TAG,
    }
    return sealed


def manifest_digest(sources: list[Mapping[str, str]]) -> str:
    """The carrier identity: the digest of its canonical source manifest."""
    return digest_obj(sorted(({"path": s["path"], "sha256": s["sha256"]} for s in sources), key=lambda s: s["path"]))


def validate_certificate(certificate: Any, expect: Expectation) -> list[TransportFinding]:
    """Every finding, in a fixed order. An empty list means the certificate holds."""
    if isinstance(certificate, dict) and (
        certificate.get("schema") in V1_SCHEMA_IDS or V1_MARKER_FIELDS & set(certificate)
    ):
        return [TransportFinding("TC-V1-PRESENTED-AS-V2", "a V1 certificate where V2 is required")]
    try:
        validate(certificate, CERTIFICATE, "$.transport", _SCHEMA_CODES)
    except SchemaError as exc:
        return [TransportFinding(exc.code, exc.detail)]
    if certificate["schema"] != SCHEMA_ID:
        return [TransportFinding("TC-V1-PRESENTED-AS-V2", f"schema {certificate['schema']!r}")]

    findings: list[TransportFinding] = []

    def add(code: str, detail: str) -> None:
        findings.append(TransportFinding(code, detail))

    ledger = certificate["c6_loss_and_authority"]["loss_ledger"]
    try:
        validate(ledger, LOSS_LEDGER, "$.transport.c6_loss_and_authority.loss_ledger", _SCHEMA_CODES)
    except SchemaError as exc:
        return [TransportFinding(exc.code, exc.detail)]

    # Status: issued PROPOSED, awaiting the receiving side's replay.
    if certificate["status"] != "PROPOSED":
        add("TC-STATUS", f"status {certificate['status']!r}")
    if certificate["disposition"] != "TARGET_REPLAY_REQUIRED":
        add("TC-STATUS", f"disposition {certificate['disposition']!r} at issue")
    if ledger["status_ceiling"] != "PROPOSED":
        add("TC-STATUS", f"loss-ledger ceiling {ledger['status_ceiling']!r}")

    # Envelope and pins: recomputed here, never taken from the producer.
    if certificate["envelope"]["payload_digest"] != payload_digest(certificate):
        add("TC-DIGEST-MISMATCH", "envelope payload digest does not recompute")
    c1 = certificate["c1_identity_custody"]
    if c1["source_manifest_sha256"] != expect.source_manifest_sha256:
        add("TC-DIGEST-MISMATCH", "source manifest digest does not match the record's pinned sources")
    if c1["adapter"] is not None and c1["adapter"]["sha256"] != expect.adapter_sha256:
        add("TC-DIGEST-MISMATCH", "adapter digest does not recompute")
    if certificate["c5_target_verification"]["witness_sha256"] != expect.witness_sha256:
        add("TC-DIGEST-MISMATCH", "witness digest is not the replayed positive payload")
    target = certificate["target"]
    if (
        target["row_sha256"] != expect.row_sha256
        or target["level"] != expect.level
        or target["registry_version"] != expect.registry_version
        or target["checker_id"] != expect.checker_id
        or target["repo"] != expect.target_repo
    ):
        add("TC-DIGEST-MISMATCH", "target block does not match the record's level, row and checker")
    if not certificate["c5_target_verification"]["source_admission_is_provenance_only"]:
        add("TC-STATUS", "source admission presented as more than provenance")

    # Carrier identity.
    carrier = certificate["carrier"]
    if dict(carrier) != dict(expect.carrier):
        add("TC-REFRAME-REQUIRED", "certificate carrier differs from the record's carrier")
    if c1["same_carrier"] or carrier["repo"] == expect.target_repo:
        add("TC-SAME-CARRIER", "source and target are the same carrier")

    # Criterion 2: a typed map that is a function and injective on its image.
    c2 = certificate["c2_typed_map"]
    if c2["kind"] not in IMPLEMENTED_KINDS:
        add("TC-UNSUPPORTED-KIND", f"typed-map kind {c2['kind']} is not implemented in this version")
    elif not c2["pairs"] or not c2["sorts"]:
        add("TC-CRITERION-MISSING", "criterion 2 declares no typed map")
    else:
        images: dict[str, str] = {}
        preimages: dict[str, str] = {}
        for pair in c2["pairs"]:
            if len(pair) != 2:
                add("TC-CRITERION-MISSING", f"map pair {pair!r} is not a pair")
                continue
            source, image = pair
            if source in images and images[source] != image:
                add("TC-COLLAPSE", f"{source!r} has two images; the map is not a function")
            images[source] = image
            if image in preimages and preimages[image] != source:
                add("TC-COLLAPSE", f"{preimages[image]!r} and {source!r} both map to {image!r}")
            preimages.setdefault(image, source)

    booked = {row["field_or_law"]: row for row in ledger["fields"]}
    for sort in c2["unmapped_sorts"]:
        row = booked.get(f"sort:{sort}")
        if row is None or row["classification"] != "DROPPED":
            add("TC-UNBOOKED-UNMAPPED-SORT", f"unmapped sort {sort!r} is not booked as DROPPED")

    # Criterion 3.
    c3 = certificate["c3_compatibility"]
    if not c3["squares"]:
        if c3["not_applicable_reason"] is None or not c3["not_applicable_reason"].strip():
            add("TC-CRITERION-MISSING", "criterion 3 has no squares and no N/A reason")
        elif expect.structure_maps:
            add("TC-C3-NOT-APPLICABLE-REFUSED", f"the level names structure maps {list(expect.structure_maps)}")
    else:
        named = {square["structure_map"] for square in c3["squares"]}
        for structure_map in expect.structure_maps:
            if structure_map not in named:
                add("TC-CRITERION-MISSING", f"no compatibility square for {structure_map!r}")
        for square in c3["squares"]:
            if square["lhs_sha256"] != square["rhs_sha256"]:
                add("TC-CRITERION-MISSING", f"square {square['structure_map']!r} does not commute")

    # Coefficient domain: a change must be booked, never silent.
    domain = c1["coefficient_domain"]
    if domain["source"] != domain["target"] and COEFFICIENT_ENTRY not in booked:
        add("TC-REFRAME-REQUIRED", f"coefficient domain {domain['source']} -> {domain['target']} is not booked")

    # The loss ledger.
    count = ledger["count"]
    if not isinstance(count, dict):
        add("TC-UNSOUND-LEDGER", "count is not an object")
    else:
        for key in sorted(count):
            value = count[key]
            if not key.strip():
                add("TC-UNSOUND-LEDGER", "blank loss key")
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                add("TC-UNSOUND-LEDGER", f"loss count for {key!r} is not a positive integer")
    if ledger["commitment_sha256"] != ledger_commitment(ledger):
        add("TC-LEDGER-COMMITMENT", "the loss ledger was edited after its commitment")
    for row in ledger["fields"]:
        if row["not_applicable_reason"] is not None and not row["not_applicable_reason"].strip():
            add("TC-UNBOOKED-STANDING-ENTRY", f"{row['field_or_law']} has a blank N/A reason")
    for entry in expect.standing_entries:
        if entry not in booked:
            add("TC-UNBOOKED-STANDING-ENTRY", f"standing entry {entry!r} is not booked")
    if expect.blind_framing:
        row = booked.get(BLINDNESS_ENTRY)
        if row is not None and row["classification"] != "DROPPED":
            add("TC-BLINDNESS-NOT-DROPPED", f"{BLINDNESS_ENTRY} is {row['classification']}, not DROPPED")
        if row is None and BLINDNESS_ENTRY not in expect.standing_entries:
            add("TC-UNBOOKED-STANDING-ENTRY", f"standing entry {BLINDNESS_ENTRY!r} is not booked")
    return findings
