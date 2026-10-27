"""Use the existing protected-span engine to separate immutable host context from edits."""

from operads.domain.autopoiesis.learning import canonical
from pciv.domain.models import ProtectedSpanV1, PromptGenomeV1
from pciv.use_cases.forge import PromptMutationEngineV1


def bind_mutation(experiment, parent, candidate):
    protected = (
        canonical(
            {"experiment": experiment.to_dict(), "editable_files": sorted(dict(parent.files))}
        )
        + b"\n"
    )
    old = protected + canonical(parent.to_dict())
    span = ProtectedSpanV1("host-experiment-contract", 0, len(protected))
    rewritten = PromptMutationEngineV1().apply_mutation(
        original_bytes=old,
        protected_spans=(span,),
        edit_start_byte=len(protected),
        edit_end_byte=len(old),
        replacement_bytes=canonical(candidate.to_dict()),
    )
    if not rewritten.startswith(protected) or candidate.parent != parent.candidate_id:
        raise ValueError("PROTECTED_HOST_OR_PARENT_CHANGED")
    return PromptGenomeV1(
        source_packet_refs=({"source": experiment.source, "candidate": candidate.candidate_id},),
        domain_model=candidate.to_dict(),
        parents=({"candidate": parent.candidate_id},),
        protected_spans=(span,),
    )
