"""Functionality to create invalid event sequences
"""
from __future__ import annotations
from copy import copy, deepcopy
from typing import Iterable, Generator, Any, TYPE_CHECKING
from itertools import combinations_with_replacement
import uuid
import datetime

from test_event_generator.solutions import EventSolution
if TYPE_CHECKING:
    from test_event_generator.solutions import GraphSolution


def create_invalid_missing_event_sols_from_valid_graph_sols(
    valid_graph_solutions: Iterable[GraphSolution]
) -> Generator[GraphSolution, Any, None]:
    """Method to create invalid sequences with missing events

    :param valid_graph_solutions: An :class:`Iterable` of valid
    :class:`GraphSolution`'s
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    for valid_sol in valid_graph_solutions:
        yield from create_invalid_missing_event_sols_from_valid_graph_sol(
            valid_sol
        )


def create_invalid_missing_event_sols_from_valid_graph_sol(
    valid_graph_sol: GraphSolution
) -> Generator[GraphSolution, Any, None]:
    """Method to loop over the keys in the events dictionary of a
    :class:`GraphSolution` and remove the event at that key for a copy of the
    :class:`GraphSolution`

    :param valid_graph_sol: A valid :class:`GraphSolution`
    :type valid_graph_sol: :class:`GraphSolution`
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    for key in valid_graph_sol.events.keys():
        missing_event_graph_sol = deepcopy(valid_graph_sol)
        missing_event_graph_sol.add_to_missing_events(key)
        yield missing_event_graph_sol


def create_invalid_missing_edge_sols_from_valid_graph_sols(
    valid_graph_solutions: Iterable[GraphSolution]
) -> Generator[GraphSolution, Any, None]:
    """Method to create invalid sequences with missing edges

    :param valid_graph_solutions: An :class:`Iterable` of valid
    :class:`GraphSolution`'s
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """

    for valid_sol in valid_graph_solutions:
        yield from create_invalid_missing_edge_sols_from_valid_graph_sol(
            valid_sol
        )


def create_invalid_missing_edge_sols_from_valid_graph_sol(
    valid_graph_sol: GraphSolution
) -> Generator[GraphSolution, Any, None]:
    """Method to create invalid solutions with missing edges from a valid
    :class:`GraphSolution`

    :param valid_graph_sol: A valid :class:`GraphSolution`
    :type valid_graph_sol: :class:`GraphSolution`
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    for key in valid_graph_sol.events.keys():
        yield from create_invalid_missing_edge_sols_from_event(
            valid_graph_sol=valid_graph_sol,
            key=key
        )


def create_invalid_missing_edge_sols_from_event(
    valid_graph_sol: GraphSolution,
    key: int
) -> Generator[GraphSolution, Any, None]:
    """Method to create invalid solutions with missing edges from a valid
    :class:`GraphSolution` and event key

    :param valid_graph_sol: A valid :class:`GraphSolution`
    :type valid_graph_sol: :class:`GraphSolution`
    :param key: The key in the events attribute dictionary of the
    :class:`EventSolution` to remove previous event edges from
    :type key: `int`
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    event = valid_graph_sol.events[key]
    for i in range(len(event.previous_events)):
        missing_edge_graph_sol = deepcopy(valid_graph_sol)
        event = missing_edge_graph_sol.events[key]
        event.previous_events.pop(i)
        yield missing_edge_graph_sol


def create_merge_invalid_stacked_solutions_from_valid_graph_sols(
    valid_graph_solutions: Iterable[GraphSolution],
    job_name: str = "default_job_name",
    is_template: bool = False
) -> Generator[tuple[list[dict], list[str], None, str], Any, None]:
    """Method to create and merge stacked invalid solutions

    :param valid_graph_solutions: Iterable of valid :class:`GraphSolution`'s
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :param job_name: The name of the job, defaults to "default_job_name"
    :type job_name: `str`, optional
    :param is_template: Boolean indicating if job is a template
    job or unique ids should be provided for events and the job,
    defaults to `False`
    :type is_template: `bool`, optional
    :yield: Yields a tuple with
    * list of audit event jsons
    * list of event ids
    * `None` place-holder for figure object
    * job id
    :rtype: :class:`Generator`[`tuple`[`list`[`dict`], `list`[`str`], `None`,
    `str`], `Any`, `None`, `str`]
    """
    for stacked_combination in (
        create_invalid_stacked_valid_solutions_from_valid_graph_sols(
            valid_graph_solutions
        )
    ):
        yield merge_stacked_graph_sols_audit_events(
            graph_sols=stacked_combination,
            job_name=job_name,
            is_template=is_template
        )


def create_invalid_stacked_valid_solutions_from_valid_graph_sols(
    valid_graph_solutions: Iterable[GraphSolution]
) -> Generator[tuple[GraphSolution, ...], Any, None]:
    """Generator to get combinations of two valid graph solutions from an
    :class:`Iterable` of valid graph solutions.

    :param valid_graph_solutions: :class:`Iterable of :class:`GraphSolution`'s.
    The :class:`GraphSolution`'s should be from the same job definition.
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :yield: Yields two :class:`GraphSolution`'s as a combination of the
    :class:`Iterable` of :class:`GraphSolution`'s
    :rtype: :class:`Generator`[`tuple`[:class:`GraphSolution`, ...], `Any`,
    `None`]
    """
    yield from combinations_with_replacement(
        valid_graph_solutions, r=2
    )


def merge_stacked_graph_sols_audit_events(
    graph_sols: Iterable[GraphSolution],
    job_name: str = "default_job_name",
    is_template: bool = False
) -> tuple[list[dict], list[str], None, str]:
    """Method to merge stacked :class:`GraphSolution`'s audit events. Flattens
    by row major order.

    :param graph_sols: An :class:`Iterable` of :class:`GraphSolution` to be
    merged
    :type graph_sols: :class:`Iterable`[:class:`GraphSolution`]
    :param is_template: Boolean indicating if job is a template
    job or unique ids should be provided for events and the job,
    defaults to `False`
    :type is_template: `bool`, optional
    :param job_name: The job definition name, defaults to
    "default_job_name"
    :type job_name: `str`, optional
    :return: Returns the merged list of jsons along with template ids and
    `None`
    :rtype: `tuple`[`list`[`dict`], `list`[`str`], `None`, `str`]
    """
    start_time = datetime.datetime.now()
    audit_jsons_to_be_stacked = []
    event_template_ids_to_be_stacked = []
    lengths = []
    max_len = 0
    # get audit event jsons for each graph solution and save lengths and
    # update maximum length of all audit json lists
    if is_template:
        job_id = "jobID"
    else:
        job_id = str(uuid.uuid4())
    for graph_sol in graph_sols:
        audit_event_jsons, event_template_ids, _, _ = (
            graph_sol.create_audit_event_jsons(
                is_template=is_template,
                job_name=job_name,
                start_time=start_time,
                job_id=job_id
            )
        )
        audit_jsons_to_be_stacked.append(audit_event_jsons)
        event_template_ids_to_be_stacked.extend(event_template_ids)
        length = len(audit_event_jsons)
        max_len = max(max_len, length)
        lengths.append(length)
    # stack jsons in order of time stamp
    audit_jsons_stacked = [
        audit_jsons[i]
        for i in range(max_len)
        for j, audit_jsons in enumerate(audit_jsons_to_be_stacked)
        if i < lengths[j]
    ]
    return audit_jsons_stacked, event_template_ids, None, job_id


def create_invalid_linked_ghost_event_sols_from_valid_sols(
    valid_graph_solutions: Iterable[GraphSolution]
) -> Generator[GraphSolution, Any, None]:
    """Method to generate :class:`GraphSolution`'s with a single
    :class:`EventSolution`'s within the :class:`GraphSolution` linked to a
    :class:`EventSolution` that exists outside of the :class:`Graphsolution`.
    Generated from an iterable of :class:`GraphSolution`'s.

    :param valid_graph_solutions: An :class:`Iterable` of valid
    :class:`GraphSolution`'s
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    ghost_event = EventSolution(
        meta_data={
            "EventType": "GhostEvent"
        }
    )
    for graph_sol in valid_graph_solutions:
        yield from create_invalid_linked_ghost_event_sols_from_valid_sol(
            graph_sol=graph_sol,
            ghost_event=ghost_event
        )


def create_invalid_linked_ghost_event_sols_from_valid_sol(
    graph_sol: GraphSolution,
    ghost_event: EventSolution
) -> Generator[GraphSolution, Any, None]:
    """Method to generate :class:`GraphSolution`'s with a single
    :class:`EventSolution`'s within the :class:`GraphSolution` linked to a
    :class:`EventSolution` that exists outside of the :class:`Graphsolution`

    :param graph_sol: A valid :class:`GraphSolution`
    :type graph_sol: :class:`GraphSolution`
    :param ghost_event: The :class:`EventSolution` that will not be part of
    the yielded :class:`GraphSolution`
    :type ghost_event: :class:`EventSolution`
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    for key in graph_sol.events.keys():
        copied_ghost_event = copy(ghost_event)
        copied_ghost_event.event_template_id = str(uuid.uuid4())
        copied_graph_sol = deepcopy(graph_sol)
        copied_event = copied_graph_sol.events[key]
        copied_event.add_prev_event(copied_ghost_event)
        copied_graph_sol.events[key] = copied_event
        yield copied_graph_sol


def create_invalid_linked_spy_event_sols_from_valid_sols(
    valid_graph_solutions: Iterable[GraphSolution]
) -> Generator[GraphSolution, Any, None]:
    """Method to generate :class:`GraphSolution`'s with a single
    :class:`EventSolution`'s within the :class:`GraphSolution` linked to a
    :class:`EventSolution` that exists inside of the :class:`Graphsolution`
    but should not. Generated from an iterable of :class:`GraphSolution`'s

    :param valid_graph_solutions: An :class:`Iterable` of valid
    :class:`GraphSolution`'s
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    spy_event = EventSolution(
        meta_data={
            "EventType": "SpyEvent"
        }
    )
    for graph_sol in valid_graph_solutions:
        yield from create_invalid_linked_spy_event_sols_from_valid_sol(
            graph_sol=graph_sol,
            spy_event=spy_event
        )


def create_invalid_linked_spy_event_sols_from_valid_sol(
    graph_sol: GraphSolution,
    spy_event: EventSolution
) -> Generator[GraphSolution, Any, None]:
    """Method to generate :class:`GraphSolution`'s with a single
    :class:`EventSolution`'s within the :class:`GraphSolution` linked to a
    :class:`EventSolution` that exists inside of the :class:`Graphsolution`
    but should not

    :param graph_sol: A valid :class:`GraphSolution`
    :type graph_sol: :class:`GraphSolution`
    :param ghost_event: The :class:`EventSolution` that will not be part of
    the yielded :class:`GraphSolution`
    :type ghost_event: :class:`EventSolution`
    :yield: Yields a :class:`GraphSolution`
    :rtype: :class:`Generator`[:class:`GraphSolution`, `Any`, `None`]
    """
    for key in graph_sol.events.keys():
        copied_spy_event = copy(spy_event)
        copied_graph_sol = deepcopy(graph_sol)
        copied_event = copied_graph_sol.events[key]
        copied_event.add_prev_event(copied_spy_event)
        copied_spy_event.add_post_event(copied_event)
        copied_graph_sol.add_event(copied_spy_event)
        yield copied_graph_sol


def create_invalid_graph_solutions_from_valid_graph_solutions(
    valid_graph_solutions: Iterable[GraphSolution]
) -> dict[str, tuple[Generator[GraphSolution], bool]]:
    """Method to get a dictionary of categorised audit event graph solutions
    from an iterable of :class:`GraphSolution`'s

    :param valid_graph_solutions: Iterable of valid :class:`GraphSolution`'s
    :type valid_graph_solutions: :class:`Iterable`[:class:`GraphSolution`]
    :return: Returns a dictionary of categorised generated
    :class:`GraphSolution`'s
    :rtype: `dict`[`str`, `tuple`[:class:`Generator`[:class:`GraphSolution`],
    `bool`]]
    """
    # create dictionary for categorised invalid solutions
    categorised_invalid_solutions = {}
    # add invalid missing event solutions
    categorised_invalid_solutions["MissingEvents"] = (
        create_invalid_missing_event_sols_from_valid_graph_sols(
            valid_graph_solutions
        ),
        False
    )
    # add invalid missing edge solutions
    categorised_invalid_solutions["MissingEdges"] = (
        create_invalid_missing_edge_sols_from_valid_graph_sols(
            valid_graph_solutions
        ),
        False
    )
    # add invalid ghost event solutions
    categorised_invalid_solutions["GhostEvents"] = (
        create_invalid_linked_ghost_event_sols_from_valid_sols(
            valid_graph_solutions
        ),
        False
    )
    # add invalid spy event solutions
    categorised_invalid_solutions["SpyEvents"] = (
        create_invalid_linked_spy_event_sols_from_valid_sols(
            valid_graph_solutions
        ),
        False
    )
    return categorised_invalid_solutions
