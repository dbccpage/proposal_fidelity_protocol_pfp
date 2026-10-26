"""Expand one retained tree node through the existing PFP preparation boundary."""

from omega_engine_pfp.domain.prompts.compression import CompressedPromptTree, expand_prompt_tree
from omega_engine_pfp.infrastructure.task_turn import PreparedTaskTurn, prepare_task_turn


def prepare_compressed_turn(tree: CompressedPromptTree | dict, node_id: str) -> PreparedTaskTurn:
    for node in expand_prompt_tree(tree):
        if node["node_id"] == node_id:
            return prepare_task_turn(**{key: value for key, value in node.items()
                if key not in {"node_id", "parent_id", "slot"}})
    raise ValueError("UNKNOWN_PROMPT_NODE")
