"""Extra tests for the graph solution.
"""

from test_event_generator.solutions import (
    GraphSolution,
    get_audit_event_jsons_and_templates_all_topological_permutations,
)


class TestGraphSolution:
    """Test the graph solution methods"""

    @staticmethod
    def test_update_events_from_job_event_list(
        output_job_list: list[dict],
    ) -> None:
        """Test the update_events_from_job_event_list method."""
        graph_solution = GraphSolution()
        graph_solution.update_events_from_job_event_list(output_job_list)
        assert len(graph_solution.events) == 4
        assert len(graph_solution.start_events) == 1
        start_key = list(graph_solution.start_events.keys())[0]
        start_event = graph_solution.start_events[start_key]
        assert start_event.meta_data["EventType"] == "Event_A"
        assert len(start_event.post_events) == 2
        post_events = start_event.post_events
        end_event_set = set()
        for post_event, event_type in zip(post_events, ["Event_C", "Event_D"]):
            assert post_event.meta_data["EventType"] == event_type
            assert len(post_event.post_events) == 1
            end_event_set.add(post_event.post_events[0])
            assert len(post_event.previous_events) == 1
            assert start_event in post_event.previous_events
        assert len(graph_solution.end_events) == 1
        assert len(end_event_set) == 1
        end_key = list(graph_solution.end_events.keys())[0]
        end_event = graph_solution.end_events[end_key]
        assert end_event in end_event_set
        assert end_event.meta_data["EventType"] == "Event_E"
        assert len(end_event.post_events) == 0
        assert len(end_event.previous_events) == 2
        for end_event_previous_event in end_event.previous_events:
            assert end_event_previous_event in post_events

    @staticmethod
    def test_get_topologically_sorted_event_sequence_all_permutations(
        output_job_list: list[dict],
    ) -> None:
        """Test the get_topologically_sorted_event_sequence method."""
        graph_solution = GraphSolution()
        graph_solution.update_events_from_job_event_list(output_job_list)
        event_sequences = list(
            graph_solution.
            get_topologically_sorted_event_sequence_all_permutations(
                graph_solution.events.values()
            )
        )
        assert len(event_sequences) == 2
        event_sequence_1 = event_sequences[0]
        event_sequence_2 = event_sequences[1]
        assert event_sequence_1[1] == event_sequence_2[2]
        assert event_sequence_1[2] == event_sequence_2[1]

    @staticmethod
    def test_get_audit_event_jsons_and_templates_all_topological_permutations(
        output_job_list: list[dict],
    ) -> None:
        """Test the
        get_audit_event_jsons_and_templates_all_topological_permutations
        method.
        """
        graph_solution = GraphSolution()
        graph_solution.update_events_from_job_event_list(output_job_list)
        audit_event_jsons_and_templates = list(
            graph_solution.
            get_audit_event_jsons_and_templates_all_topological_permutations()
        )
        assert len(audit_event_jsons_and_templates) == 2
        audit_event_jsons_and_templates_1 = audit_event_jsons_and_templates[0]
        audit_event_jsons_and_templates_2 = audit_event_jsons_and_templates[1]
        assert (
            audit_event_jsons_and_templates_1[0][1]["eventType"]
            == audit_event_jsons_and_templates_2[0][2]["eventType"]
        )
        assert (
            audit_event_jsons_and_templates_1[0][2]["eventType"]
            == audit_event_jsons_and_templates_2[0][1]["eventType"]
        )


def test_get_audit_event_jsons_and_templates_all_topological_permutations(
    output_job_list: list[dict],
) -> None:
    """Test the
    get_audit_event_jsons_and_templates_all_topological_permutations function.
    """
    graph_solution = GraphSolution()
    graph_solution.update_events_from_job_event_list(output_job_list)
    audit_event_jsons_and_templates = list(
        get_audit_event_jsons_and_templates_all_topological_permutations(
            [graph_solution, graph_solution]
        )
    )
    assert len(audit_event_jsons_and_templates) == 4
    for i in range(2):
        audit_event_jsons_and_templates_1 = audit_event_jsons_and_templates[
            i * 2
        ]
        audit_event_jsons_and_templates_2 = audit_event_jsons_and_templates[
            i * 2 + 1
        ]
        assert (
            audit_event_jsons_and_templates_1[0][1]["eventType"]
            == audit_event_jsons_and_templates_2[0][2]["eventType"]
        )
        assert (
            audit_event_jsons_and_templates_1[0][2]["eventType"]
            == audit_event_jsons_and_templates_2[0][1]["eventType"]
        )
