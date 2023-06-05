"""Tests for the generation of invalid solutions from graph solutions
"""
from copy import deepcopy
from math import comb

from test_event_generator.solutions import (
    GraphSolution,
    EventSolution,
    create_invalid_missing_event_sols_from_valid_graph_sol,
    create_invalid_missing_event_sols_from_valid_graph_sols,
    create_invalid_missing_edge_sols_from_event,
    create_invalid_missing_edge_sols_from_valid_graph_sol,
    create_invalid_missing_edge_sols_from_valid_graph_sols,
    create_invalid_stacked_valid_solutions_from_valid_graph_sols,
    merge_stacked_graph_sols_audit_events,
    create_invalid_linked_ghost_event_sols_from_valid_sol,
    create_invalid_linked_ghost_event_sols_from_valid_sols,
    create_invalid_linked_spy_event_sols_from_valid_sol,
    create_invalid_linked_spy_event_sols_from_valid_sols,
    create_invalid_graph_solutions_from_valid_graph_solutions
)


class TestInvalidMissingEvent:
    @staticmethod
    def test_create_invalid_missing_event_sols_from_valid_graph_sol(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method `create_invalid_event_sols_from_valid_graph_sol`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        invalid_missing_event_sols = list(
            create_invalid_missing_event_sols_from_valid_graph_sol(
                graph_simple
            )
        )
        TestInvalidMissingEvent.check_invalid_missing_event_sols(
            invalid_missing_event_sols=invalid_missing_event_sols,
            graph_simple=graph_simple
        )

    @staticmethod
    def check_invalid_missing_event_sols(
        invalid_missing_event_sols: list[GraphSolution],
        graph_simple: GraphSolution
    ) -> None:
        """Helper functions check invalid missing event solutions

        :param invalid_missing_event_sols: List of :class:`GraphSolution`'s
        for invalid solutions with missing events
        :type invalid_missing_event_sols: `list`[:class:`GraphSolution`]
        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        assert len(invalid_missing_event_sols) == 3
        for i, graph_sol in enumerate(invalid_missing_event_sols):
            assert graph_sol.events[i + 1] == graph_sol.missing_events[0]

    @staticmethod
    def test_create_invalid_missing_event_sols_from_valid_graph_sols(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        `create_invalid_missing_event_sols_from_valid_graph_sols`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        invalid_missing_event_sols = list(
            create_invalid_missing_event_sols_from_valid_graph_sols(
                [graph_simple, graph_simple]
            )
        )
        TestInvalidMissingEvent.check_invalid_missing_event_sols(
            invalid_missing_event_sols[:3],
            graph_simple
        )
        TestInvalidMissingEvent.check_invalid_missing_event_sols(
            invalid_missing_event_sols[3:],
            graph_simple
        )


class TestInvalidMissingEdge:
    """Tests for Invalid solutions with missing edges
    """
    @staticmethod
    def test_create_invalid_missing_edge_sols_from_event_no_prev_event(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method `create_invalid_missing_edge_sols_from_event`
        for an event with no prev event

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        assert len(list(
            create_invalid_missing_edge_sols_from_event(
                graph_simple,
                1
            )
        )) == 0

    @staticmethod
    def test_create_invalid_missing_edge_sols_from_event_prev_event(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method `create_invalid_missing_edge_sols_from_event`
        for an event with a prev event

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        invalid_missing_edge_sols = list(
            create_invalid_missing_edge_sols_from_event(
                graph_simple,
                2
            )
        )
        assert len(invalid_missing_edge_sols) == 1
        graph_sol = invalid_missing_edge_sols[0]
        assert graph_sol.events[1] not in graph_sol.events[2].previous_events

    @staticmethod
    def test_create_invalid_missing_edge_sols_from_valid_graph_sol(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        `create_invalid_missing_edge_sols_from_valid_graph_sol`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        invalid_missing_edge_sols = list(
            create_invalid_missing_edge_sols_from_valid_graph_sol(
                graph_simple
            )
        )
        TestInvalidMissingEdge.check_invalid_missing_edge_sols(
            invalid_missing_edge_sols
        )

    @staticmethod
    def check_invalid_missing_edge_sols(
        invalid_missing_edge_sols: list[GraphSolution]
    ) -> None:
        """Helper function

        :param invalid_missing_edge_sols: List of :class:`GraphSolution`'s of
        the expected missing edeg :class:`GraphSolution`'s
        :type invalid_missing_edge_sols: `list`[:class:`GraphSolution`]
        """
        assert len(invalid_missing_edge_sols) == 2
        for i, graph_sol in enumerate(invalid_missing_edge_sols):
            assert (
                graph_sol.events[i + 1]
                not in graph_sol.events[i + 2].previous_events
            )

    @staticmethod
    def test_create_invalid_missing_edge_sols_from_valid_graph_sols(
        graph_simple: GraphSolution
    ) -> None:
        """Tests the method
        `create_invalid_missing_edge_sols_from_valid_graph_sols`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        invalid_missing_edge_sols = list(
            create_invalid_missing_edge_sols_from_valid_graph_sols(
                [graph_simple, deepcopy(graph_simple)]
            )
        )
        assert len(invalid_missing_edge_sols) == 4
        TestInvalidMissingEdge.check_invalid_missing_edge_sols(
            invalid_missing_edge_sols[:2]
        )
        TestInvalidMissingEdge.check_invalid_missing_edge_sols(
            invalid_missing_edge_sols[2:]
        )


class TestInvalidStackedSolutions:
    """Tests for method to create invalid stacked solutions
    """
    @staticmethod
    def test_create_invalid_stacked_valid_solutions_from_valid_graph_sols(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method
        `create_invalid_stacked_valid_solutions_from_valid_graph_sols`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        graphs = [
            deepcopy(graph_simple)
            for _ in range(3)
        ]
        stacked_graph_solutions = list(
            create_invalid_stacked_valid_solutions_from_valid_graph_sols(
                graphs
            )
        )
        assert len(stacked_graph_solutions) == comb(3 + 2 - 1, 2)

    @staticmethod
    def test_merge_stacked_graph_sols_audit_events(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method `merge_stacked_graph_sols_audit_events`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        graph_copy = deepcopy(graph_simple)
        # update event types
        for event in graph_copy.events.values():
            event.meta_data = deepcopy(event.meta_data)
            event.meta_data["EventType"] += "_copy"
        audit_event_sequence = merge_stacked_graph_sols_audit_events(
            graph_sols=[graph_simple, graph_copy]
        )
        assert len(audit_event_sequence[0]) == 6
        # check following events are correctly placed
        for i in range(3):
            assert (
                audit_event_sequence[0][2 * i]["eventType"]
            ) == (
                audit_event_sequence[0][2 * i + 1]["eventType"].replace(
                    "_copy",
                    ""
                )
            )
        # check all job ids are the same
        for i in range(5):
            assert (
                audit_event_sequence[0][i]["jobId"]
            ) == (
                audit_event_sequence[0][i]["jobId"]
            )
        # check event ids are all different
        assert len(set(
            audit_event["eventId"]
            for audit_event in audit_event_sequence[0]
        )) == 6


class TestInvalidGhostEvents:
    """Tests for creating invalid ghost events graph solutions
    """
    @staticmethod
    def test_create_invalid_linked_ghost_event_sols_from_valid_sol(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method `create_invalid_linked_ghost_event_sols_from_valid_sol`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        ghost_event = EventSolution(
            meta_data={
                "EventType": "Ghost"
            }
        )
        invalid_graph_sols = list(
            create_invalid_linked_ghost_event_sols_from_valid_sol(
                graph_sol=graph_simple,
                ghost_event=ghost_event
            )
        )
        # should be 3 graph solutions
        assert len(invalid_graph_sols) == 3
        # ghost event should appear in previous events the specific event
        for i, invalid_graph_sol in enumerate(invalid_graph_sols):
            assert len([
                prev_event
                for prev_event
                in invalid_graph_sol.events[i + 1].previous_events
                if (
                    prev_event.meta_data["EventType"]
                ) == (
                    ghost_event.meta_data["EventType"]
                )
            ]) == 1
        # no previous or post events for ghost event
        assert ghost_event.is_start and ghost_event.is_end

    @staticmethod
    def test_create_invalid_linked_ghost_event_sols_from_valid_sols(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method
        `create_invalid_linked_ghost_event_sols_from_valid_sols`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        graph_copy = deepcopy(graph_simple)
        invalid_graph_sols = list(
            create_invalid_linked_ghost_event_sols_from_valid_sols(
                [graph_simple, graph_copy]
            )
        )
        # should be 6 graph solutions
        assert len(invalid_graph_sols) == 6


class TestInvalidSpyEvents:
    """Tests for creating invalid spy events graph solutions
    """
    @staticmethod
    def test_create_invalid_linked_spy_event_sols_from_valid_sol(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method
        `create_invalid_linked_spy_event_sols_from_valid_sol`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        spy_event = EventSolution(
            meta_data={
                "EventType": "Spy"
            },
        )
        invalid_graph_sols = list(
            create_invalid_linked_spy_event_sols_from_valid_sol(
                graph_sol=graph_simple,
                spy_event=spy_event
            )
        )
        # should be 3 graph solutions
        assert len(invalid_graph_sols) == 3
        # ghost event should appear in previous events the specific event
        for i, invalid_graph_sol in enumerate(invalid_graph_sols):
            assert invalid_graph_sol.events[4] in (
                invalid_graph_sol.events[i + 1].previous_events
            )
            assert invalid_graph_sol.events[i + 1] in (
                invalid_graph_sol.events[4].post_events
            )

    @staticmethod
    def test_create_invalid_linked_spy_event_sols_from_valid_sols(
        graph_simple: GraphSolution
    ) -> None:
        """Tests method
        `create_invalid_linked_spy_event_sols_from_valid_sols`

        :param graph_simple: Fixture providing 3 event sequence
        :class:`GraphSolution`
        :type graph_simple: :class:`GraphSolution`
        """
        graph_copy = deepcopy(graph_simple)
        invalid_graph_sols = list(
            create_invalid_linked_spy_event_sols_from_valid_sols(
                [graph_simple, graph_copy]
            )
        )
        # should be 6 graph solutions
        assert len(invalid_graph_sols) == 6


def test_create_invalid_audit_event_graph_solutions_from_valid_graph_solutions(
    graph_simple: GraphSolution
) -> None:
    """Tests
    `create_invalid_audit_event_graph_solutions_from_valid_graph_solutions`

    :param graph_simple: Fixture providing a simple three sequence
    :class:`GraphSolution`
    :type graph_simple: :class:`GraphSolution`
    """
    graph_copy = deepcopy(graph_simple)
    categorised_invalid_solutions = (
        create_invalid_graph_solutions_from_valid_graph_solutions(
            [graph_simple, graph_copy]
        )
    )
    assert len(categorised_invalid_solutions) == 4
    # check keys are correct
    keys_to_check = [
        "MissingEvents", "MissingEdges",
        "GhostEvents", "SpyEvents"
    ]
    for key in keys_to_check:
        assert key in categorised_invalid_solutions
    # check that the last entry of the tuple for each entry is False
    for invalid_graph_sols_tuple in categorised_invalid_solutions.values():
        assert not invalid_graph_sols_tuple[1]
