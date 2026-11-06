"""MCTS-style checkpointed state graph recovery for long-horizon critique loops.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class StateNode:
    """A checkpoint node in the candidate state search tree."""

    checkpoint_id: str
    round_index: int
    code_content: str
    code_sha256: str
    oracle_score: float
    verdict: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    failure_count: int = 0


class MctsStateGraph:
    """Manages checkpointed candidate exploration tree and state recovery backtracking."""

    def __init__(self, root_code: str, root_sha256: str) -> None:
        self.nodes: Dict[str, StateNode] = {}
        root_node = StateNode(
            checkpoint_id="root",
            round_index=0,
            code_content=root_code,
            code_sha256=root_sha256,
            oracle_score=0.0,
            verdict="ROOT",
            parent_id=None,
        )
        self.nodes["root"] = root_node
        self.current_tip_id: str = "root"

    def record_candidate(
        self,
        checkpoint_id: str,
        round_index: int,
        code: str,
        code_sha256: str,
        oracle_score: float,
        verdict: str,
        parent_id: Optional[str] = None,
    ) -> StateNode:
        """Register a new candidate state into the exploration tree."""
        actual_parent = parent_id or self.current_tip_id
        node = StateNode(
            checkpoint_id=checkpoint_id,
            round_index=round_index,
            code_content=code,
            code_sha256=code_sha256,
            oracle_score=oracle_score,
            verdict=verdict,
            parent_id=actual_parent,
        )
        self.nodes[checkpoint_id] = node
        if actual_parent in self.nodes:
            self.nodes[actual_parent].children_ids.append(checkpoint_id)
        self.current_tip_id = checkpoint_id
        return node

    def check_need_backtrack(self, threshold_failures: int = 2) -> Tuple[bool, Optional[str]]:
        """Evaluate if the current branch has accumulated consecutive failures and needs backtracking.

        Returns:
            (needs_backtrack, recommended_ancestor_checkpoint_id)
        """
        current = self.nodes.get(self.current_tip_id)
        if current is None or current.checkpoint_id == "root":
            return False, None

        # Count consecutive non-PASS verdicts along current branch
        consecutive_failures = 0
        cursor: Optional[StateNode] = current
        while cursor and cursor.checkpoint_id != "root":
            if cursor.verdict != "ACCEPTED":
                consecutive_failures += 1
            else:
                break
            cursor = self.nodes.get(cursor.parent_id or "")

        if consecutive_failures >= threshold_failures:
            # Find best healthy ancestor (highest oracle score)
            best_ancestor = "root"
            best_score = -1.0
            ancestor_cursor = self.nodes.get(current.parent_id or "")
            while ancestor_cursor:
                if ancestor_cursor.oracle_score >= best_score:
                    best_score = ancestor_cursor.oracle_score
                    best_ancestor = ancestor_cursor.checkpoint_id
                ancestor_cursor = self.nodes.get(ancestor_cursor.parent_id or "")
            return True, best_ancestor

        return False, None

    def backtrack_to(self, checkpoint_id: str) -> Optional[StateNode]:
        """Backtrack exploration tip to a specified checkpoint ancestor."""
        if checkpoint_id in self.nodes:
            self.current_tip_id = checkpoint_id
            return self.nodes[checkpoint_id]
        return None
