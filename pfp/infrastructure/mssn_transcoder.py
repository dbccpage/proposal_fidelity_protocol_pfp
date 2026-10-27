"""Bidirectional Transcoder between MSS-N Terse Wire AST (*.mssn)
and Canonical Four-Object JSON Packet Suite (*.json).

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


def canonical_json_bytes(value: Any) -> bytes:
    """PFP demo encoding: UTF-8, sorted keys, compact separators (not general JCS)."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


class MssnTranscoderError(Exception):
    """Raised when parsing or transcoding between MSS-N wire AST and JSON packets fails."""

    pass


@dataclass
class FourObjectPacketSuite:
    problem: Dict[str, Any]
    candidate: Dict[str, Any]
    verifier: Dict[str, Any]
    receipt: Dict[str, Any]

    def compute_digests(self) -> Tuple[str, str, str, str]:
        """Computes canonical SHA-256 digests for all four objects."""
        receipt_body = dict(self.receipt, receipt_digest="")
        return (
            digest(self.problem),
            digest(self.candidate),
            digest(self.verifier),
            digest(receipt_body),
        )


class MssnCycleRepairTranscoder:
    """Bidirectional transcoder for Genesis Cycle Balance Repair."""

    @staticmethod
    def strip_comments_and_normalize(text: str) -> str:
        """Strips line comments and normalizes whitespace."""
        clean_lines = []
        for line in text.splitlines():
            line = re.sub(r"#.*$", "", line).strip()
            if line:
                clean_lines.append(line)
        return " ".join(clean_lines)

    @classmethod
    def _parse_bracket_array(cls, text: str) -> List[int]:
        """Parses [a,b,c] into a list of integers."""
        m = re.search(r"\[([\s0-9,\-]+)\]", text)
        if not m:
            raise MssnTranscoderError(f"Failed to parse bracket array from: {text}")
        raw = m.group(1).strip()
        if not raw:
            return []
        return [int(x.strip()) for x in raw.split(",") if x.strip()]

    @classmethod
    def _parse_matrix_rows(cls, text: str) -> List[List[int]]:
        """Parses <[r0],[r1],...> into a matrix of integers."""
        # Find all [...] inside the tag
        row_matches = re.findall(r"\[([0-9,\-\s]+)\]", text)
        if not row_matches:
            raise MssnTranscoderError(f"No matrix rows found in: {text}")
        matrix = []
        for rm in row_matches:
            row = [int(x.strip()) for x in rm.split(",") if x.strip()]
            matrix.append(row)
        return matrix

    @classmethod
    def wire_to_four_object(cls, wire_text: str) -> FourObjectPacketSuite:
        """Parses a terse MSS-N wire AST string into the canonical 4-object JSON packet suite."""
        normalized = cls.strip_comments_and_normalize(wire_text)

        if not normalized.startswith("cycle_repair<") or not normalized.endswith(">"):
            raise MssnTranscoderError("Wire text must be enclosed in cycle_repair< ... >")

        body = normalized[len("cycle_repair<") : -1].strip()

        # 1. Parse carrier: carrier<K0_CHORD_SQUARE; V<4>; E<5>; B<1>>
        carrier_m = re.search(r"carrier<([^;>]+);\s*V<(\d+)>;\s*E<(\d+)>;\s*B<(\d+)>", body)
        if not carrier_m:
            raise MssnTranscoderError("Failed to parse carrier<...> clause")
        carrier_name = carrier_m.group(1).strip()
        num_v = int(carrier_m.group(2))
        num_e = int(carrier_m.group(3))
        num_b = int(carrier_m.group(4))

        # 2. Parse d1 matrix: d1<[...],[...],...>
        d1_m = re.search(r"d1<([^>]+)>", body)
        if not d1_m:
            raise MssnTranscoderError("Failed to parse d1<...> clause")
        d1 = cls._parse_matrix_rows(d1_m.group(1))

        # 3. Parse d2 matrix: d2<[...],[...],...>
        d2_m = re.search(r"d2<([^>]+)>", body)
        if not d2_m:
            raise MssnTranscoderError("Failed to parse d2<...> clause")
        d2 = cls._parse_matrix_rows(d2_m.group(1))

        # 4. Parse obstruction: obstruct<z<[...]|0,0,1,1,1>>
        obstruct_m = re.search(r"obstruct<z<([0-9,\-\s]+)>>", body)
        if not obstruct_m:
            raise MssnTranscoderError("Failed to parse obstruct<z<...>> clause")
        cycle_z = [int(x.strip()) for x in obstruct_m.group(1).split(",") if x.strip()]

        # 5. Parse attach: attach<f1; edges<e2,e3,e4>; boundary<0,0,1,1,1>>
        attach_m = re.search(r"attach<([^;>]+);\s*edges<([^>]+)>;\s*boundary<([0-9,\-\s]+)>", body)
        if not attach_m:
            raise MssnTranscoderError("Failed to parse attach<...> clause")
        face_name = attach_m.group(1).strip()
        raw_edges = [x.strip() for x in attach_m.group(2).split(",") if x.strip()]
        repair_boundary_col = [int(x.strip()) for x in attach_m.group(3).split(",") if x.strip()]

        # 6. Parse nilpotent: nilpotent<d1*b=0>
        has_nilpotent = "nilpotent<d1*b=0>" in body

        # 7. Parse preimage: preimage<c<0,1>; d2_ext*c=z>
        preimage_m = re.search(r"preimage<c<([0-9,\-\s]+)>;", body)
        if not preimage_m:
            raise MssnTranscoderError("Failed to parse preimage<c<...>> clause")
        preimage_c = [int(x.strip()) for x in preimage_m.group(1).split(",") if x.strip()]

        # 8. Parse terminal: terminal<qed<exact>>
        terminal_m = re.search(r"terminal<qed<([a-z]+)>>", body)
        if not terminal_m:
            raise MssnTranscoderError("Failed to parse terminal<qed<...>> clause")
        terminal_status = terminal_m.group(1).upper()

        # This profile describes only K0's fixed oriented chorded square.
        # Unsupported carriers must be refused rather than relabeled as K0.
        expected_d1 = [[-1, 0, 0, 1, -1], [1, -1, 0, 0, 0], [0, 1, -1, 0, 1], [0, 0, 1, -1, 0]]
        expected_d2 = [[1], [1], [0], [0], [-1]]
        if (num_v, num_e, num_b) != (4, 5, 1) or d1 != expected_d1 or d2 != expected_d2:
            raise MssnTranscoderError(
                "Unsupported carrier: this wire profile requires the declared K0 incidence matrices"
            )
        if (
            len(cycle_z) != num_e
            or len(repair_boundary_col) != num_e
            or len(preimage_c) != num_b + 1
        ):
            raise MssnTranscoderError("Witness dimensions disagree with the carrier")
        if any(
            not -(2**63) <= value < 2**63 for value in (*cycle_z, *repair_boundary_col, *preimage_c)
        ):
            raise MssnTranscoderError("Wire integers must fit the shared signed 64-bit profile")
        if not re.fullmatch(r"[A-Za-z0-9_]+", carrier_name) or not re.fullmatch(
            r"[A-Za-z0-9_]+", face_name
        ):
            raise MssnTranscoderError("Unsupported identifier")
        if (
            not raw_edges
            or len(set(raw_edges)) != len(raw_edges)
            or any(e not in {"e0", "e1", "e2", "e3", "e4"} for e in raw_edges)
        ):
            raise MssnTranscoderError("Unknown or duplicate candidate edge")
        if not has_nilpotent or terminal_status not in {"EXACT", "REFUSED", "OPEN", "SURVIVOR"}:
            raise MssnTranscoderError("Unsupported or missing wire claim")

        # Construct standard vertices and edges for chordal square
        vertices = list(range(num_v))
        edges = [
            {"id": "e0", "source": 0, "target": 1},
            {"id": "e1", "source": 1, "target": 2},
            {"id": "e2", "source": 2, "target": 3},
            {"id": "e3", "source": 3, "target": 0},
            {"id": "e4", "source": 0, "target": 2},
        ]
        faces = [{"id": "f0", "boundary_edges": ["e0", "e1", "-e4"]}]

        # Compute d1 * z to verify cycle property
        d1_z = [0] * num_v
        for r_idx, row in enumerate(d1):
            s = 0
            for coefficient, value in zip(row, cycle_z):
                term = coefficient * value
                s += term
                if not -(2**63) <= term < 2**63 or not -(2**63) <= s < 2**63:
                    raise MssnTranscoderError("Integer diagnostic overflow")
            d1_z[r_idx] = s

        # Build Object 1: Problem Carrier Contract
        problem = {
            "schema_version": "core.symbol_game.cycle_balance.problem.v1",
            "problem_id": "SG-PROB-GENESIS-CYCLE-003",
            "case_id": "case_day3_cycle_balance_repair",
            "authority_effect": "None",
            "arithmetic_domain": "EXACT_INTEGER",
            "carrier": {
                "name": carrier_name,
                "vertices": vertices,
                "edges": edges,
                "faces": faces,
                "static_cell_bounds": {
                    "max_vertices": 64,
                    "max_edges": 128,
                    "max_faces": 64,
                },
            },
            "boundary_matrices": {
                "d1": d1,
                "d2": d2,
            },
            "active_obstruction": {
                "cycle_z": cycle_z,
                "cycle_edges": raw_edges,
                "d1_z": d1_z,
                "homology_status": "UNVERIFIED",
            },
        }
        prob_digest = digest(problem)

        # Build Object 2: Candidate Proposal Packet
        candidate = {
            "schema_version": "core.symbol_game.cycle_balance.candidate.v1",
            "candidate_id": "SG-CAND-CYCLE-REPAIR-001",
            "problem_digest": prob_digest,
            "authority_effect": "None",
            "claimed_move": "ATTACH_2CELL",
            "repair_face_name": face_name,
            "constituent_edges": [
                f"{e}:{edges[int(e[1:])]['source']}->{edges[int(e[1:])]['target']}"
                for e in raw_edges
            ],
            "repair_boundary_column": repair_boundary_col,
            "preserves_chain_law": has_nilpotent,
            "claimed_integer_preimage_c": preimage_c,
            "claimed_h1_status": terminal_status,
        }
        cand_digest = digest(candidate)

        # Build Object 3: Host Verifier Contract
        verifier = {
            "schema_version": "core.symbol_game.cycle_balance.verifier.v1",
            "verifier_id": "PFP-V02-EXACT-INTEGER-SNF-SOLVER",
            "arithmetic_domain": "EXACT_INTEGER",
            "problem_digest": prob_digest,
            "verification_rules": [
                "STATIC_CELL_BOUNDS_CHECK",
                "CHAIN_COMPLEX_NILPOTENCY_CHECK",
                "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE",
            ],
            "static_bounds": {
                "max_vertices": 64,
                "max_edges": 128,
                "max_faces": 64,
            },
        }
        ver_digest = digest(verifier)

        # Build Object 4: Verifier Receipt Envelope
        receipt = {
            "schema_version": "core.symbol_game.cycle_balance.receipt.v1",
            "receipt_id": "RCPT-GENESIS-CYCLE-003",
            "authority_effect": "None",
            "problem_digest": prob_digest,
            "candidate_digest": cand_digest,
            "verifier_digest": ver_digest,
            "verification_status": "UNVERIFIED",
            "terminal_status": None,
            "residuals": None,
            "exact_witness": None,
            "claim_hygiene": {
                "what_it_supports": "Parsing and content binding of an untrusted candidate only.",
                "what_it_does_not_support": "No mathematical verification, SNF computation, or terminal authority.",
                "next_test_needed": "Independently check chain laws and replay the submitted integer preimage.",
            },
            "receipt_digest": "",
        }
        receipt["receipt_digest"] = digest(receipt)

        suite = FourObjectPacketSuite(
            problem=problem,
            candidate=candidate,
            verifier=verifier,
            receipt=receipt,
        )
        reconstructed = cls.strip_comments_and_normalize(cls.four_object_to_wire(suite))
        if re.sub(r"\s+", "", reconstructed) != re.sub(r"\s+", "", normalized):
            raise MssnTranscoderError(
                "Non-canonical, duplicate, missing, or unsupported wire clauses"
            )
        return suite

    @classmethod
    def four_object_to_wire(cls, suite: FourObjectPacketSuite) -> str:
        """Renders a 4-object JSON packet suite into canonical terse MSS-N wire AST format."""
        prob = suite.problem
        cand = suite.candidate

        carrier = prob["carrier"]
        carrier_name = carrier["name"]
        num_v = len(carrier["vertices"])
        num_e = len(carrier["edges"])
        num_b = len(carrier["faces"])

        d1 = prob["boundary_matrices"]["d1"]
        d2 = prob["boundary_matrices"]["d2"]
        cycle_z = prob["active_obstruction"]["cycle_z"]

        d1_str = ",".join(f"[{','.join(str(x) for x in row)}]" for row in d1)
        d2_str = ",".join(f"[{','.join(str(x) for x in row)}]" for row in d2)
        cycle_str = ",".join(str(x) for x in cycle_z)

        if cand["preserves_chain_law"] is not True:
            raise MssnTranscoderError("This wire profile cannot encode an absent nilpotency claim")
        # Candidate repair
        face_name = cand["repair_face_name"]
        raw_edges = [e.split(":")[0] for e in cand["constituent_edges"]]
        edges_str = ",".join(raw_edges)
        b_col_str = ",".join(str(x) for x in cand["repair_boundary_column"])

        # Preimage and terminal
        preimage = cand["claimed_integer_preimage_c"]
        preimage_str = ",".join(str(x) for x in preimage)
        terminal_status = cand["claimed_h1_status"].lower()

        lines = [
            "# MSS-N Terse Wire AST Representation: Genesis Cycle Balance Repair",
            "# Language: MSS-N Symbol Game Wire Grammar (PKT-00)",
            "# AuthorityEffect: None",
            "",
            "cycle_repair<",
            f"  carrier<{carrier_name}; V<{num_v}>; E<{num_e}>; B<{num_b}>>;",
            f"  d1<{d1_str}>;",
            f"  d2<{d2_str}>;",
            f"  obstruct<z<{cycle_str}>>;",
            f"  attach<{face_name}; edges<{edges_str}>; boundary<{b_col_str}>>;",
            "  nilpotent<d1*b=0>;",
            f"  preimage<c<{preimage_str}>; d2_ext*c=z>;",
            f"  terminal<qed<{terminal_status}>>",
            ">",
            "",
        ]
        return "\n".join(lines)
