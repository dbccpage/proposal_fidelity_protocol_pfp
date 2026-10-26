"""Prompt Rewriting Use Case for PFP.

Zero infrastructure imports; depends strictly on domain aggregates, value objects, and entities.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from typing import Union

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.aggregates.rewriting_aggregate import SpanPartitionAggregate
from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.rewriting.rewrites import Boundary, RewriteReceipt, RewriteRequest, Segment, parse_boundary
from ..domain.value_objects.identifiers import PilotId, RequestId, Sha256Digest


class RewritePromptUseCase:
    """Executes prompt boundary isolation and rewriting transformations.

    Accepts RewriteRequest, SpanPartitionAggregate, or PilotAggregate directly.
    """

    def rewrite(
        self, request: Union[RewriteRequest, SpanPartitionAggregate, PilotAggregate]
    ) -> Result[RewriteReceipt, DomainError]:
        try:
            if isinstance(request, PilotAggregate):
                req_id = request.pilot_id.value
                raw_prompt = request.seed_prompt
                rendered_segments = [f"<task>{raw_prompt}</task>"]
                boundary_format = "boundary_tree_v1"
                segments_count = 1

            elif isinstance(request, SpanPartitionAggregate):
                req_id = f"partition_{request.total_length}"
                raw_prompt = f"length_{request.total_length}"
                rendered_segments = []
                for s, r in request.partitions:
                    rendered_segments.append(f"[{r.value.upper()}]: span({s.start}..{s.end}) <atom>")
                boundary_format = "partition_boundary_v1"
                segments_count = len(request.partitions)

            elif isinstance(request, RewriteRequest):
                req_id = request.request_id
                raw_prompt = request.raw_prompt
                rendered_segments = []
                for seg in request.segments:
                    tree = parse_boundary(seg.boundary)
                    rendered_segments.append(f"[{seg.role.upper()}]: {seg.text} {tree.render()}")
                boundary_format = request.boundary_format
                segments_count = len(request.segments)

            else:
                return Result.err(
                    DomainError(
                        code=RefusalCode.TYPING_VIOLATION,
                        message=f"Unsupported rewrite request type: {type(request).__name__}",
                    )
                )

            rewritten_text = "\n".join(rendered_segments) if rendered_segments else f"<task>{raw_prompt}</task>"
            root_boundary = f"<root>{boundary_format}</root>"
            r_hash = Sha256Digest.compute(rewritten_text.encode("utf-8")).value

            return Result.ok(
                RewriteReceipt(
                    request_id=req_id,
                    rewritten_prompt=rewritten_text,
                    root_boundary=root_boundary,
                    segments_count=segments_count,
                    receipt_sha256=r_hash,
                    authority_effect="None",
                )
            )
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.PARSER_ERROR,
                    message=f"Prompt rewrite failed: {str(exc)}",
                )
            )
