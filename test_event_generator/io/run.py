""" Functionality to run end to end file input to output of test events
"""
from typing import Iterable, Generator, Any

import matplotlib.pyplot as plt

from test_event_generator.graph import Graph
from test_event_generator.solutions import (
    GraphSolution,
    get_categorised_audit_event_jsons,
    create_invalid_graph_solutions_from_valid_graph_solutions,
    create_merge_invalid_stacked_solutions_from_valid_graph_sols
)
from test_event_generator.io.io import load_puml_file_from_path
from test_event_generator.io.parse_puml import get_graph_defs_from_puml


def puml_file_to_test_events(
    file_path: str,
    **options
):
    """Method to get test events given options and a puml file path.
    Returns a dictionary with job name as keys to distinguish
    between two jobs

    :param file_path: Path to the puml file
    :type file_path: `str`
    :return: Returns a dictionary of job name and a dictionary of valid and
    invalid generated events
    :rtype: `dict`[ `str`, `dict`[ `str`, `tuple`[
    :class:`Generator`[`tuple`[`list`[`dict`], `list`[`str`],
    :class:`plt.Figure` | `None`, `str`]], `bool` ] ] ]
    """
    puml_file = load_puml_file_from_path(file_path=file_path)
    return puml_to_test_events(
        puml_file,
        **options
    )


def puml_to_test_events(
    puml_file: str,
    **options
) -> dict[
    str,
    dict[
        str,
        tuple[
            Generator[
                tuple[list[dict], list[str], plt.Figure | None, str],
                Any,
                None
            ],
            bool
        ]
    ]
]:
    """Method to get test events given options and a puml file string.
    Returns a dictionary with job name as keys to distinguish
    between two jobs

    :param puml_file: puml file as string
    :type file_path: `str`
    :return: Returns a dictionary of job name and a dictionary of valid and
    invalid generated events
    :rtype: `dict`[ `str`, `dict`[ `str`, `tuple`[
    :class:`Generator`[`tuple`[`list`[`dict`], `list`[`str`],
    :class:`plt.Figure` | `None`, `str`]], `bool` ] ] ]
    """
    # convert puml file to graph defs
    graph_defs = get_graph_defs_from_puml(puml_file=puml_file)
    # handle options
    options = handle_options(options)
    # get event sequences
    jobs_and_test_events = {
        job_name: get_graph_def_test_events(
            graph_def=graph_def,
            job_name=job_name,
            **options
        )
        for job_name, graph_def in graph_defs.items()
    }
    return jobs_and_test_events


def get_graph_def_test_events(
    graph_def: dict[str, dict],
    job_name: str,
    **options
) -> dict[
    str,
    tuple[
        Generator[
            tuple[list[dict], list[str], plt.Figure | None, str],
            Any,
            None
        ],
        bool
    ]
]:
    """Method to obtain a categorised dictionary of valid and invalid
    generated solutions

    :param graph_def: Standardised graph definition
    :type graph_def: `dict`[`str`, `dict`]
    :param job_name: The name of the job
    :type job_name: `str`
    :return: Returns a dictionary containing a tuple of a generator of audit
    event sequences and other outputs as well as a boolean indicating that the
    sequences are valid or invalid
    :rtype: `dict`[ `str`, `tuple`[ :class:`Generator`[`tuple`[`list`[`dict`],
    `list`[`str`], :class:`plt.Figure` | `None`, `str`]], `bool` ] ]
    """
    graph = Graph()
    graph.parse_graph_def(graph_def)
    # get the valid graph solutions
    graph_sols = get_graph_sols_for_graph_def(
        graph=graph,
        **options
    )

    # get valid event sequences
    categorised_valid_test_sequences = get_categorised_valid_test_sequences(
        graph_sols=graph_sols,
        job_name=job_name,
        **options
    )
    if options["invalid"]:
        # get invalid event sequences
        categorised_invalid_test_sequences = (
            get_categorised_invalid_test_sequences(
                graph_sols=graph_sols,
                graph=graph,
                job_name=job_name,
                **options
            )
        )
    else:
        categorised_invalid_test_sequences = {}
    # all categorised event sequencs
    categorised_event_sequences = {
        **categorised_valid_test_sequences,
        **categorised_invalid_test_sequences
    }
    return categorised_event_sequences


def get_categorised_valid_test_sequences(
    graph_sols: Iterable[GraphSolution],
    job_name: str,
    **options
) -> dict[
    str,
    tuple[
        Generator[
            tuple[list[dict], list[str], plt.Figure | None, str],
            Any,
            None
        ],
        bool
    ]
]:
    """Method to get categorised valid test sequences from an
    :class:`Iterable` of :class:`GraphSolution`'s for a given job name
    and for given options

    :param graph_sols: Iterable of valid :class:`GraphSolution`'s
    :type graph_sols: :class:`Iterable`[:class:`GraphSolution`]
    :param job_name: The name of the job to apply
    :type job_name: `str`
    :return: Returns a dictionary containing a tuple of a generator of audit
    event sequences and other outputs as well as a boolean indicating that the
    sequences are valid
    :rtype: `dict`[ `str`, `tuple`[ :class:`Generator`[`tuple`[`list`[`dict`],
    `list`[`str`], :class:`plt.Figure` | `None`, `str`]], `bool` ] ]
    """
    # get categorised test event sequences
    valid_categorised = get_categorised_audit_event_jsons(
        categorised_graph_solutions={
            "ValidSols": (graph_sols, True)
        },
        job_name=job_name,
        return_plots=options["return_plots"],
        is_template=options["is_template"]
    )
    return valid_categorised


def get_graph_sols_for_graph_def(
    graph: Graph,
    num_loops: int,
    num_branches: int,
    **solve_options
) -> list[GraphSolution]:
    """Function to get list of :class:`GraphSolution` from an input graph_def

    :param graph_def: Standardised graph definition
    :type graph_def: `dict`
    :param num_loops: Number of loops in expansion
    :type num_loops: `int`
    :param num_branches: Number of branches in expansion
    :type num_branches: `int`
    :return: Returns a list of the
    :class:`GraphSolution` combinations
    instance that generated them
    :rtype: `list`[:class:`GraphSolution`]
    """
    graph.solve(**solve_options)
    graph_sols = graph.get_all_combined_graph_solutions(
        num_loops=num_loops,
        num_branches=num_branches
    )
    return graph_sols


def get_categorised_invalid_test_sequences(
    graph_sols: Iterable[GraphSolution],
    graph: Graph,
    job_name: str,
    **options,
) -> dict[
    str,
    tuple[
        Generator[
            tuple[list[dict], list[str], plt.Figure | None, str],
            Any,
            None
        ],
        bool
    ]
]:
    """Method to handle generating invalid audit event sequences

    :param graph_sols: Iterable of :class:`GraphSolution`'s from which to make
    invalid sequences
    :type graph_sols: :class:`Iterable`[:class:`GraphSolution`]
    :param graph: The pre-solved :class:`Graph` from which to generate invalid
    constraint violation solutions
    :type graph: :class:`Graph`
    :param job_name: The name of the job
    :type job_name: `str`
    :return: Returns a dictionary containing a tuple of a generator of audit
    event sequences and other outputs as well as a boolean indicating that the
    sequences are invalid
    :rtype: `dict`[ `str`, `tuple`[ :class:`Generator`[`tuple`[`list`[`dict`],
    `list`[`str`], :class:`plt.Figure` | `None`, `str`]], `bool` ] ]
    """
    categorised_invalid_graph_sols_from_graph_sols = (
        create_invalid_graph_solutions_from_valid_graph_solutions(
            graph_sols
        )
    )
    # get invalid sols from graph
    categorised_invalid_graph_sols_from_graph = (
        graph.get_all_invalid_constraint_breaks(**options)
    )
    categorised_invalid_graph_sols = {
        **categorised_invalid_graph_sols_from_graph_sols,
        **categorised_invalid_graph_sols_from_graph
    }
    # get dict of generated invalid audit event sequences
    categorised_invalid_audit_event_sequences = (
        get_categorised_audit_event_jsons(
            categorised_invalid_graph_sols,
            job_name=job_name,
            is_template=options["is_template"],
            return_plots=options["return_plots"]
        )
    )
    # add stacked solutions separately
    categorised_invalid_audit_event_sequences["StackedSolutions"] = (
        create_merge_invalid_stacked_solutions_from_valid_graph_sols(
            graph_sols,
            job_name=job_name,
            is_template=options["is_template"]
        ),
        False
    )
    return categorised_invalid_audit_event_sequences


def handle_options(
    options: dict[str, int | bool]
) -> dict[str, int | bool]:
    """Method to check a dictionary of options and
    update with default values if an option is not found.

    :param options: Dictionary providing the options
    :type options: `dict`[`str`, `int`  |  `bool`]
    :raises RuntimeError: Raises a :class:`RuntimeError` is a given option is
    of the incorrect type
    :return: Returns adictionary of the updated options
    :rtype: `dict`[`str`, `int` | `bool`]
    """
    defaults = {
        "is_template": False,
        "return_plots": False,
        "invalid": True,
        "num_branches": 2,
        "num_loops": 2
    }
    for option, default_val in defaults.items():
        if option not in options:
            options[option] = default_val
        else:
            if not isinstance(options[option], type(default_val)):
                raise RuntimeError(
                    f"The provided option value for {option} is of type"
                    f" {type(options[option])} and not of expected"
                    f" {type(default_val)}"
                )
    return options
