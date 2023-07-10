"""Tests for run.py
"""

from copy import deepcopy
from typing import Iterable

from test_event_generator.graph import Graph
from test_event_generator.solutions import GraphSolution
from test_event_generator.io.run import (
    get_categorised_valid_test_sequences,
    get_categorised_invalid_test_sequences,
    get_graph_def_test_events,
    puml_to_test_events
)


def test_get_categorised_valid_test_sequences_options_false(
    graph_simple: GraphSolution
) -> None:
    """Tests the method `get_categorised_valid_test_sequences` when the
    options have "is_template" set to False

    :param graph_simple: Fixture providing a simple sequence
    :class:`GraphSolution`
    :type graph_simple: :class:`GraphSolution`
    """
    graph_sols = [graph_simple, deepcopy(graph_simple)]
    options = {
        "return_plots": False,
        "is_template": False
    }
    categorised_valid_audit_event_sequences = (
        get_categorised_valid_test_sequences(
            graph_sols=graph_sols,
            job_name="A job",
            **options
        )
    )
    check_valid_categorised_sols(
        categorised_valid_audit_event_sequences,
        False
    )


def check_valid_categorised_sols(
    categorised_valid_audit_event_sequences: dict,
    is_template: bool
) -> None:
    """Method to check all valid categorised test event sequences

    :param categorised_valid_audit_event_sequences: Dictionary containing
    categorised test event sequences
    :type categorised_valid_audit_event_sequences: `dict`
    :param is_template: Boolean indicating that whether the events should be
    template events or not
    :type is_template: `bool`
    """
    assert len(categorised_valid_audit_event_sequences) == 1
    assert "ValidSols" in categorised_valid_audit_event_sequences
    generated_sequence_tuple = categorised_valid_audit_event_sequences[
        "ValidSols"
    ]
    assert generated_sequence_tuple[1]
    check_output_event_sequences(generated_sequence_tuple[0], is_template)


def check_output_event_sequences(
    audit_event_sequence_tuples: Iterable[tuple],
    is_template: bool
) -> None:
    """Method to audit event sequence tuples have the correct structure

    :param audit_event_sequence_tuples: Iterable of tuples containing:
    * categorised test event sequences
    * list of event ids
    * figure/None
    * job id string
    :type audit_event_sequence_tuples: :class:`Iterable`[`tuple`]
    :param is_template: Boolean indicating that whether the events should be
    template events or not
    :type is_template: `bool`
    """
    for audit_event_sequence_tuple in audit_event_sequence_tuples:
        (
            audit_event_sequence,
            audit_event_event_ids,
            figure,
            job_id
        ) = audit_event_sequence_tuple
        assert isinstance(audit_event_sequence, list)
        assert isinstance(audit_event_event_ids, list)
        assert figure is None
        if is_template:
            assert job_id == "jobID"
        else:
            assert job_id != "jobID"


def test_get_categorised_valid_test_sequences_options_true(
    graph_simple: GraphSolution
) -> None:
    """Tests the method `get_categorised_valid_test_sequences` when the
    options have "is_template" set to True

    :param graph_simple: Fixture providing a simple sequence
    :class:`GraphSolution`
    :type graph_simple: :class:`GraphSolution`
    """
    graph_sols = [graph_simple, deepcopy(graph_simple)]
    options = {
        "return_plots": False,
        "is_template": True
    }
    categorised_valid_audit_event_sequences = (
        get_categorised_valid_test_sequences(
            graph_sols=graph_sols,
            job_name="A job",
            **options
        )
    )
    check_valid_categorised_sols(
        categorised_valid_audit_event_sequences,
        True
    )


def test_get_categorised_invalid_test_sequences_false(
    parsed_graph: Graph
) -> None:
    """Tests the method `get_categorised_invalid_test_sequences` when the
    options have "is_template" set to False

    :param parsed_graph: Fixture providing a :class:`Graph` with a parsed
    graph def
    :type parsed_graph: :class:`Graph`
    """
    options = {
        "return_plots": False,
        "is_template": False
    }
    parsed_graph.solve()
    graph_sols = parsed_graph.get_all_combined_graph_solutions(
        num_branches=2,
        num_loops=2
    )
    categorised_invalid_audit_event_sequences = (
        get_categorised_invalid_test_sequences(
            graph_sols=graph_sols,
            graph=parsed_graph,
            job_name="A job",
            **options
        )
    )
    check_invalid_categorised_sols(
        categorised_invalid_audit_event_sequences,
        False
    )


def check_invalid_categorised_sols(
    categorised_invalid_audit_event_sequences: dict,
    is_template: bool
) -> None:
    """Method to check all invalid categorised test event sequences

    :param categorised_invalid_test_event_sequences: Dictionary containing
    categorised test event sequences
    :type categorised_invalid_test_event_sequences: `dict`
    :param is_template: Boolean indicating that whether the events should be
    template events or not
    :type is_template: `bool`
    """
    assert len(categorised_invalid_audit_event_sequences) == 7
    invalid_categories = [
        "MissingEvents", "MissingEdges",
        "GhostEvents", "SpyEvents",
        "StackedSolutions", "XORConstraintBreaks",
        "ANDConstraintBreaks"
    ]
    for invalid_category, generated_sequence_tuple in (
        categorised_invalid_audit_event_sequences.items()
    ):
        assert invalid_category in invalid_categories
        assert not generated_sequence_tuple[1]
        check_output_event_sequences(generated_sequence_tuple[0], is_template)


def test_get_categorised_invalid_test_sequences_true(
    parsed_graph: Graph
) -> None:
    """Tests the method `get_categorised_invalid_test_sequences` when the
    options have "is_template" set to True

    :param parsed_graph: Fixture providing a :class:`Graph` with a parsed
    graph def
    :type parsed_graph: :class:`Graph`
    """
    options = {
        "return_plots": False,
        "is_template": True
    }
    parsed_graph.solve()
    graph_sols = parsed_graph.get_all_combined_graph_solutions(
        num_branches=2,
        num_loops=2
    )
    categorised_invalid_audit_event_sequences = (
        get_categorised_invalid_test_sequences(
            graph_sols=graph_sols,
            graph=parsed_graph,
            job_name="A job",
            **options
        )
    )
    check_invalid_categorised_sols(
        categorised_invalid_audit_event_sequences,
        True
    )


def tests_get_graph_def_test_events(
    graph_def: dict[str, dict]
) -> None:
    """Tests the method `get_graph_def_test_events`

    :param graph_def: Standardised graph definition
    :type graph_def: `dict`[`str`, `dict`]
    """
    options = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2
    }
    categorised_test_event_sequences = get_graph_def_test_events(
        graph_def=graph_def,
        job_name="A job",
        **options
    )
    check_all_categorised_sols(
        categorised_test_event_sequences,
        False
    )


def check_all_categorised_sols(
    categorised_test_event_sequences: dict,
    is_template: bool
) -> None:
    """Method to check all categorised test event sequences

    :param categorised_test_event_sequences: Dictionary containing categorised
    test event sequences
    :type categorised_test_event_sequences: `dict`
    :param is_template: Boolean indicating that whether the events should be
    template events or not
    :type is_template: `bool`
    """
    assert len(categorised_test_event_sequences) == 8
    categorised_valid_test_event_sequences = {
        key: value
        for key, value in categorised_test_event_sequences.items()
        if key == "ValidSols"
    }
    categorised_invalid_test_event_sequences = {
        key: value
        for key, value in categorised_test_event_sequences.items()
        if key != "ValidSols"
    }
    check_valid_categorised_sols(
        categorised_valid_test_event_sequences,
        is_template
    )
    check_invalid_categorised_sols(
        categorised_invalid_test_event_sequences,
        is_template
    )


def test_puml_to_test_events(
    ANDFork_loop_puml: str
) -> None:
    """Tests the method `puml_to_test_events`

    :param ANDFork_loop_puml: Fixture providing a str representation of a puml
    file
    :type ANDFork_loop_puml: `str`
    """
    options = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2
    }
    jobs_categorised_test_event_sequences = puml_to_test_events(
        ANDFork_loop_puml,
        **options
    )
    assert len(jobs_categorised_test_event_sequences) == 1
    assert "ANDFork_loop_a" in jobs_categorised_test_event_sequences
    categorised_test_event_sequences = jobs_categorised_test_event_sequences[
        "ANDFork_loop_a"
    ]
    check_all_categorised_sols(
        categorised_test_event_sequences,
        False
    )


def test_puml_to_test_events_solution_limit(
    bunched_xor_puml: str
) -> None:
    """Tests the method `puml_to_test_events` when there is a solution limit

    :param ANDFork_loop_puml: Fixture providing a str representation of a puml
    file
    :type ANDFork_loop_puml: `str`
    """
    options = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2,
        "solution_limit": 1
    }
    jobs_categorised_test_event_sequences = puml_to_test_events(
        bunched_xor_puml,
        **options
    )
    assert len(jobs_categorised_test_event_sequences) == 1
    assert "bunched_XOR_switch" in jobs_categorised_test_event_sequences
    categorised_test_event_sequences = jobs_categorised_test_event_sequences[
        "bunched_XOR_switch"
    ]
    # make sure valid only provides 1 solution
    counter = 0
    for _ in categorised_test_event_sequences["ValidSols"][0]:
        counter += 1
    assert counter == 1
    # as we have only looked for one solution it is possible that the invalid
    # constraint break has found that solutions and it was filtered out
    counter = 0
    for _ in categorised_test_event_sequences["XORConstraintBreaks"][0]:
        counter += 1
    assert counter == 1


def test_puml_to_test_events_solution_limit_invalid_check(
    ANDFork_loop_puml: str
) -> None:
    """Tests the method `puml_to_test_events` with a solution limit for
    invalid solutions

    :param ANDFork_loop_puml: Fixture providing a str representation of a puml
    file
    :type ANDFork_loop_puml: `str`
    """
    options = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2,
        "solution_limit": 1
    }
    jobs_categorised_test_event_sequences = puml_to_test_events(
        ANDFork_loop_puml,
        **options
    )
    categorised_test_event_sequences = jobs_categorised_test_event_sequences[
        "ANDFork_loop_a"
    ]
    counter = 0
    for _ in categorised_test_event_sequences["ANDConstraintBreaks"][0]:
        counter += 1
    assert counter == 1


def test_puml_to_test_events_solution_max_sol_time(
    ANDFork_loop_puml: str
) -> None:
    """Tests the method `puml_to_test_events` with a max solution time provided

    :param ANDFork_loop_puml: Fixture providing a str representation of a puml
    file
    :type ANDFork_loop_puml: `str`
    """
    options = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2,
        "solution_limit": 1,
        "max_sol_time": 10
    }
    puml_to_test_events(
        ANDFork_loop_puml,
        **options
    )


def test_puml_to_test_events_filter_invalid_solutions(
    ANDFork_loop_puml: str
) -> None:
    """Tests the method `puml_to_test_events` with a subset of invalid types
    requested

    :param ANDFork_loop_puml: Fixture providing a str representation of a puml
    file
    :type ANDFork_loop_puml: `str`
    """
    options = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2,
        "invalid_types": [
            "StackedSolutions"
        ]
    }
    test_events = puml_to_test_events(
        ANDFork_loop_puml,
        **options
    )
    assert len(test_events["ANDFork_loop_a"]) == 2
    assert "StackedSolutions" in test_events["ANDFork_loop_a"]
    assert "ValidSols" in test_events["ANDFork_loop_a"]
