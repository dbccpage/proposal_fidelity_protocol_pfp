"""A workflow with two nodes sharing an id must not validate.

`ValidateWorkflowsHandler` builds its node map as
`{node.node_id: node for node in query.nodes}`. A duplicate id silently
overwrites its predecessor, so only the LAST node with that id was ever
checked -- the earlier node's ports and colours went unexamined while
`node_count` still counted it.

The handler then validated a smaller graph than the one supplied and emitted a
topological plan naming each id once, with no way for the caller to say which
node a stage meant. `is_valid` was True throughout.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest

from operads.application.dtos.query_dtos import (
    ValidateWorkflowsQuery,
    WorkflowEdgeDTO,
    WorkflowNodeDTO,
)
from operads.application.queries.validate_workflows import (
    ValidateWorkflowsHandler,
)


def _node(node_id: str, *, inputs=("Prompt",), outputs=("Code",)) -> WorkflowNodeDTO:
    return WorkflowNodeDTO(
        node_id=node_id,
        operation_id=f"op:{node_id}",
        inputs=inputs,
        outputs=outputs,
    )


class DuplicateNodeIdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = ValidateWorkflowsHandler()

    def _run(self, nodes, edges=()):
        return self.handler.handle(
            ValidateWorkflowsQuery(nodes=tuple(nodes), edges=tuple(edges))
        ).unwrap()

    def test_a_duplicate_node_id_is_reported(self) -> None:
        """Mutation: drop the duplicate scan and this graph validates."""
        result = self._run([_node("step_a"), _node("step_b"), _node("step_a")])

        self.assertEqual(result.duplicate_node_ids, ("step_a",))

    def test_a_duplicate_node_id_makes_the_workflow_invalid(self) -> None:
        """Mutation: remove `duplicate_node_ids` from the is_valid conjunction
        and this reports a certified graph the handler silently collapsed."""
        result = self._run([_node("step_a"), _node("step_b"), _node("step_a")])

        self.assertFalse(result.is_valid)

    def test_no_execution_plan_is_emitted_over_ambiguous_ids(self) -> None:
        """A stage naming `step_a` cannot say which `step_a` it means.

        Mutation: drop `duplicate_node_ids` from the plan gate and a plan is
        produced over ids that do not identify a node.
        """
        result = self._run([_node("step_a"), _node("step_b"), _node("step_a")])

        self.assertEqual(result.topological_order, ())
        self.assertEqual(result.execution_stages, ())

    def test_node_count_still_reports_what_was_supplied(self) -> None:
        """The count was never the bug and must not be quietly 'fixed'.

        Reporting 2 here would hide the duplicate instead of naming it, which
        is the same failure in the opposite direction.
        """
        result = self._run([_node("step_a"), _node("step_b"), _node("step_a")])

        self.assertEqual(result.node_count, 3)

    def test_a_duplicate_is_named_once_however_many_times_it_repeats(self) -> None:
        result = self._run([_node("dup"), _node("dup"), _node("dup"), _node("other")])

        self.assertEqual(result.duplicate_node_ids, ("dup",))

    def test_several_distinct_duplicates_are_all_named(self) -> None:
        result = self._run([_node("a"), _node("b"), _node("a"), _node("b"), _node("c")])

        self.assertEqual(sorted(result.duplicate_node_ids), ["a", "b"])

    def test_a_unique_graph_still_validates_and_still_plans(self) -> None:
        """Negative control.

        Without it, a handler that rejected every graph would pass all of the
        above and look like a working check.
        """
        result = self._run(
            [
                _node("step_a", inputs=("Prompt",), outputs=("Code",)),
                _node("step_b", inputs=("Code",), outputs=("Receipt",)),
            ],
            [
                WorkflowEdgeDTO(
                    source_node_id="step_a",
                    target_node_id="step_b",
                    source_output="Code",
                    target_input="Code",
                )
            ],
        )

        self.assertTrue(result.is_valid, result)
        self.assertEqual(result.duplicate_node_ids, ())
        self.assertEqual(result.topological_order, ("step_a", "step_b"))
        self.assertEqual(result.execution_stages, (("step_a",), ("step_b",)))

    def test_an_empty_workflow_reports_no_duplicates(self) -> None:
        result = self._run([])

        self.assertEqual(result.duplicate_node_ids, ())
        self.assertTrue(result.is_valid)


class EdgeAndCycleValidationTests(unittest.TestCase):
    """The rest of what makes a typed workflow graph valid.

    Duplicate ids are covered above. These are the other four ways a graph can
    be wrong and still produce a topological plan: an edge to a node that is
    not there, an edge leaving or arriving at a port the node does not declare,
    two endpoints whose colours disagree, and a cycle -- which makes the
    "acyclic step execution DAG" the epic names not a DAG at all.

    AuthorityEffect: None.
    """

    def setUp(self) -> None:
        self.handler = ValidateWorkflowsHandler()

    def _run(self, nodes, edges=()):
        return self.handler.handle(
            ValidateWorkflowsQuery(nodes=tuple(nodes), edges=tuple(edges))
        ).unwrap()

    # -- edges pointing nowhere ---------------------------------------------

    def test_an_edge_to_a_node_that_does_not_exist_is_reported(self) -> None:
        """Mutation: drop the `src_exists or tgt_exists` guard and the handler
        raises a KeyError on `node_map[...]` instead of reporting."""
        result = self._run(
            [_node("a")],
            [WorkflowEdgeDTO("a", "Code", "ghost", "Prompt")],
        )

        self.assertEqual(len(result.orphaned_edges), 1)
        self.assertIn("ghost", result.orphaned_edges[0])
        self.assertFalse(result.is_valid)

    def test_an_edge_from_a_node_that_does_not_exist_is_reported(self) -> None:
        """Both endpoints are checked, not just the target."""
        result = self._run(
            [_node("a")],
            [WorkflowEdgeDTO("ghost", "Code", "a", "Prompt")],
        )

        self.assertEqual(len(result.orphaned_edges), 1)
        self.assertFalse(result.is_valid)

    def test_an_orphaned_edge_is_not_also_a_colour_mismatch(self) -> None:
        """The `continue` matters: an edge whose endpoints are missing has no
        colours to compare, and reporting both would blame the node twice.

        Mutation: drop the `continue` and this edge is reported again.
        """
        result = self._run(
            [_node("a")],
            [WorkflowEdgeDTO("a", "Code", "ghost", "Prompt")],
        )

        self.assertEqual(result.colour_mismatches, ())

    # -- ports ---------------------------------------------------------------

    def test_an_edge_leaving_an_undeclared_output_is_reported(self) -> None:
        """Mutation: drop the `source_output not in src_node.outputs` check and
        a graph wired to a port that does not exist validates."""
        result = self._run(
            [_node("a"), _node("b")],
            [WorkflowEdgeDTO("a", "NotAnOutput", "b", "Prompt")],
        )

        self.assertTrue(
            any("does not output" in m for m in result.colour_mismatches),
            result.colour_mismatches,
        )
        self.assertFalse(result.is_valid)

    def test_an_edge_arriving_at_an_undeclared_input_is_reported(self) -> None:
        result = self._run(
            [_node("a"), _node("b")],
            [WorkflowEdgeDTO("a", "Code", "b", "NotAnInput")],
        )

        self.assertTrue(
            any("does not accept input" in m for m in result.colour_mismatches),
            result.colour_mismatches,
        )
        self.assertFalse(result.is_valid)

    def test_a_correctly_wired_edge_reports_nothing(self) -> None:
        """The negative control for both port checks.

        A validator that flagged every edge would pass the two tests above
        while making every workflow invalid.
        """
        result = self._run(
            [_node("a"), _node("b")],
            [WorkflowEdgeDTO("a", "Code", "b", "Prompt")],
        )

        self.assertEqual(result.colour_mismatches, ())
        self.assertEqual(result.orphaned_edges, ())
        self.assertTrue(result.is_valid)

    # -- colours -------------------------------------------------------------

    def test_disagreeing_endpoint_colours_are_reported(self) -> None:
        """The typing half of "typed workflow graph".

        Mutation: drop the `source_colour != target_colour` comparison and a
        Code output feeding a Prose input validates.
        """
        producer = WorkflowNodeDTO(
            node_id="a", operation_id="op:a", inputs=("Prompt",), outputs=("Code",),
            output_colours=(("Code", "python"),),
        )
        consumer = WorkflowNodeDTO(
            node_id="b", operation_id="op:b", inputs=("Prompt",), outputs=("Code",),
            input_colours=(("Prompt", "prose"),),
        )

        result = self._run(
            [producer, consumer], [WorkflowEdgeDTO("a", "Code", "b", "Prompt")]
        )

        self.assertTrue(
            any("Colour mismatch" in m for m in result.colour_mismatches),
            result.colour_mismatches,
        )
        self.assertFalse(result.is_valid)

    def test_matching_endpoint_colours_are_accepted(self) -> None:
        """The paired control for the mismatch above."""
        producer = WorkflowNodeDTO(
            node_id="a", operation_id="op:a", inputs=("Prompt",), outputs=("Code",),
            output_colours=(("Code", "python"),),
        )
        consumer = WorkflowNodeDTO(
            node_id="b", operation_id="op:b", inputs=("Prompt",), outputs=("Code",),
            input_colours=(("Prompt", "python"),),
        )

        result = self._run(
            [producer, consumer], [WorkflowEdgeDTO("a", "Code", "b", "Prompt")]
        )

        self.assertEqual(result.colour_mismatches, ())
        self.assertTrue(result.is_valid)

    def test_an_unstated_colour_is_not_a_mismatch(self) -> None:
        """A colour is knowable only when BOTH endpoints declare one.

        Mutation: treat a missing colour as a distinct value and every
        untyped edge in the estate becomes a mismatch.
        """
        producer = WorkflowNodeDTO(
            node_id="a", operation_id="op:a", inputs=("Prompt",), outputs=("Code",),
            output_colours=(("Code", "python"),),
        )
        consumer = _node("b")  # declares no input colours at all

        result = self._run(
            [producer, consumer], [WorkflowEdgeDTO("a", "Code", "b", "Prompt")]
        )

        self.assertEqual(result.colour_mismatches, ())
        self.assertTrue(result.is_valid)

    # -- cycles --------------------------------------------------------------

    def test_a_two_node_cycle_is_detected(self) -> None:
        """"Acyclic step execution DAG" is the epic's own phrase.

        A cycle admitted here becomes an execution plan that cannot terminate.

        Mutation: drop the `elif neighbor in rec_stack` branch and this graph
        validates with an empty cycle list.
        """
        result = self._run(
            [_node("a"), _node("b")],
            [
                WorkflowEdgeDTO("a", "Code", "b", "Prompt"),
                WorkflowEdgeDTO("b", "Code", "a", "Prompt"),
            ],
        )

        self.assertTrue(result.cycles, "a two-node cycle was not detected")
        self.assertFalse(result.is_valid)

    def test_a_self_loop_is_a_cycle(self) -> None:
        """The smallest cycle there is."""
        result = self._run(
            [_node("a")], [WorkflowEdgeDTO("a", "Code", "a", "Prompt")]
        )

        self.assertTrue(result.cycles)
        self.assertFalse(result.is_valid)

    def test_a_diamond_is_not_a_cycle(self) -> None:
        """The negative control, and the one that matters most here.

        A node reachable by two distinct paths is visited twice. A detector
        keying on "already visited" rather than "on the current stack" would
        report this perfectly ordinary fan-out/fan-in as a cycle, which is why
        `rec_stack` exists alongside `visited`.

        Kept as a negative control rather than a mutation target: re-entering
        an already-visited node does not by itself manufacture a cycle here,
        so no single-line edit turns this red. Its job is to fail if the cycle
        rule is ever widened.
        """
        result = self._run(
            [_node("a"), _node("b"), _node("c"), _node("d")],
            [
                WorkflowEdgeDTO("a", "Code", "b", "Prompt"),
                WorkflowEdgeDTO("a", "Code", "c", "Prompt"),
                WorkflowEdgeDTO("b", "Code", "d", "Prompt"),
                WorkflowEdgeDTO("c", "Code", "d", "Prompt"),
            ],
        )

        self.assertEqual(result.cycles, ())
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()
